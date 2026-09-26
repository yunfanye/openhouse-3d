"""Jointly solve several photo cameras AND a few named plan dimensions (a small bundle adjustment; NumPy only).

When one photograph cannot pin a dimension (how far a gable face is set back, where a window sits), two or three
photographs taken from different places can.  Each point's 3D coordinates may reference named unknowns:
    [u, v, "gd_x0", 0.0, "z_head", "label"]       or expressions: "gd_x0+4.88", "y_up-0.32", "0.5*lg_x1"
Input JSON:
  {"unknowns": {"gd_x0": 0.75, "y_up": 1.5, ...},            initial values
   "priors":   {"gd_x0": [0.75, 0.3], ...},                  optional (mean, sigma in metres) soft constraints
   "photos": {"02": {"size": [1536, 970], "model": "level",
                     "init": {"loc": [..], "yaw": 12, "lens": 24}, "points": [...]}, ...}}
  python tools/solve_scene.py houses/stanford/cams/aerials.json [--json cams_solution.json]
Prints the solved unknowns with an approximate standard error, each camera (CAMS entry + CAM_SHIFT) and the
per-point residuals.  Unknowns with large errors are not determined by the photos: keep their plan values.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from solve_camera import project, as_cam          # noqa: E402


def _compile(expr, names):
    if isinstance(expr, (int, float)):
        return lambda u: float(expr)
    code = compile(expr, '<expr>', 'eval')
    return lambda u: float(eval(code, {'__builtins__': {}, 'math': math}, dict(zip(names, u))))


def build(cfg):
    names = list(cfg['unknowns'])
    u0 = np.array([cfg['unknowns'][n] for n in names], float)
    photos = []
    cam0 = []
    for key, ph in cfg['photos'].items():
        model = ph.get('model', 'level')
        ini = ph['init']
        if model == 'level':
            c = [*ini['loc'], ini.get('yaw', 0.0), ini.get('lens', 24.0), ini.get('shift_x', 0.0), ini.get('shift_y', 0.0)]
        elif model == 'roll':
            c = [*ini['loc'], ini.get('yaw', 0.0), ini.get('pitch', 0.0), ini.get('lens', 24.0), ini.get('roll', 0.0)]
        else:
            c = [*ini['loc'], ini.get('yaw', 0.0), ini.get('pitch', 0.0), ini.get('lens', 24.0)]
        pts = [(p[0], p[1], [_compile(e, names) for e in p[2:5]], p[5] if len(p) > 5 else '') for p in ph['points']]
        photos.append(dict(key=key, model=model, size=ph['size'], n=len(c), pts=pts, w=ph.get('weight', 1.0)))
        cam0.extend(c)
    return names, u0, photos, np.array(cam0, float)


def residuals(x, names, photos, priors, nu):
    u = x[:nu]
    out = []
    k = nu
    for ph in photos:
        cam = x[k:k + ph['n']]; k += ph['n']
        P = np.array([[f(u) for f in p[2]] for p in ph['pts']])
        uv = np.array([[p[0], p[1]] for p in ph['pts']], float)
        pr, depth = project(cam, P, ph['size'], ph['model'])
        r = ((pr - uv) * ph['w']).ravel()
        out.append(np.where(np.repeat(depth, 2) > 0.05, r, 1e4))
    for n, (mean, sig) in priors.items():
        out.append(np.array([(u[names.index(n)] - mean) / sig * 3.0]))     # 3 px per sigma
    return np.concatenate(out)


def solve(cfg, iters=300, fixed=()):
    names, u0, photos, c0 = build(cfg)
    priors = cfg.get('priors', {})
    nu = len(names)
    x = np.concatenate([u0, c0])
    free = [i for i in range(len(x)) if not (i < nu and names[i] in fixed)]
    lam = 1e-2
    r = residuals(x, names, photos, priors, nu)
    cost = r @ r
    for _ in range(iters):
        J = np.zeros((len(r), len(free)))
        for j, i in enumerate(free):
            h = 1e-5 * max(1.0, abs(x[i]))
            q = x.copy(); q[i] += h
            J[:, j] = (residuals(q, names, photos, priors, nu) - r) / h
        J = np.nan_to_num(J, nan=0.0, posinf=0.0, neginf=0.0)
        with np.errstate(all='ignore'):
            A, g = J.T @ J, J.T @ r
        ok = False
        for _ in range(14):
            step = np.linalg.solve(A + lam * np.diag(np.diag(A) + 1e-9), -g)
            q = x.copy(); q[free] += step
            rq = residuals(q, names, photos, priors, nu)
            if rq @ rq < cost:
                x, r, cost = q, rq, rq @ rq
                lam = max(lam / 3, 1e-9); ok = True
                break
            lam *= 4
        if not ok or np.linalg.norm(step) < 1e-10:
            break
    # approximate standard errors of the unknowns (pixel noise ~ rms)
    m = len(r) - len(free)
    s2 = cost / max(1, m)
    try:
        with np.errstate(all='ignore'):
            cov = np.linalg.pinv(J.T @ J) * s2
        se = np.sqrt(np.clip(np.diag(cov), 0, None))
    except (np.linalg.LinAlgError, ValueError):
        se = np.full(len(free), np.nan)
    se_full = np.full(len(x), np.nan); se_full[free] = se
    return names, photos, x, r, se_full


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('config', type=Path)
    ap.add_argument('--fix', default='')
    ap.add_argument('--json', type=Path, help='write the solution here')
    a = ap.parse_args(argv)
    cfg = json.loads(a.config.read_text())
    names, photos, x, r, se = solve(cfg, fixed=tuple(v for v in a.fix.split(',') if v))
    nu = len(names)
    print('unknowns:')
    for i, n in enumerate(names):
        print(f"  {n:14s} {x[i]:8.3f}  (+/- {se[i]:.3f})   init {cfg['unknowns'][n]:.3f}")
    k, pos = nu, 0
    result = {'unknowns': {n: float(x[i]) for i, n in enumerate(names)}, 'cameras': {}}
    for ph in photos:
        cam = x[k:k + ph['n']]; k += ph['n']
        keys = {'level': ['x', 'y', 'z', 'yaw', 'lens', 'shift_x', 'shift_y'], 'roll': ['x', 'y', 'z', 'yaw', 'pitch', 'lens', 'roll']}.get(
            ph['model'], ['x', 'y', 'z', 'yaw', 'pitch', 'lens'])
        sol = dict(zip(keys, cam.tolist()))
        loc, tgt, lens, shift = as_cam(sol, ph['model'])
        n = len(ph['pts'])
        res = r[pos:pos + 2 * n].reshape(-1, 2) / ph['w']; pos += 2 * n
        rms = float(np.sqrt((res ** 2).sum(axis=1).mean()))
        print(f"photo {ph['key']}: ({tuple(float(v) for v in loc)}, {tuple(float(v) for v in tgt)}, {lens})  shift {shift}"
              f"  pitch {sol.get('pitch', 0.0):.2f}  roll {sol.get('roll', 0.0):.2f}  rms {rms:.1f} px")
        for p, e in zip(ph['pts'], res):
            flag = '  <--' if math.hypot(*e) > 3 * max(rms, 1.0) else ''
            print(f"    {p[3]:26s} du {e[0]:7.1f}  dv {e[1]:7.1f}{flag}")
        result['cameras'][ph['key']] = dict(sol=sol, loc=list(map(float, loc)), tgt=list(map(float, tgt)), lens=lens, shift=list(shift), rms=rms)
    if a.json:
        a.json.write_text(json.dumps(result, indent=1))


if __name__ == '__main__':
    main(sys.argv[1:])
