"""Joint photo-camera + plan solve with LINE constraints and edited-photo camera models (NumPy only; see tools/solve_scene.py
for the JSON variant without lines).

Config = a Python file defining
  UNK    = {name: init}                     plan unknowns
  PRIORS = {name: (mean, sigma)}            optional soft priors (3 px per sigma)
  FIX    = [names]                          unknowns held
  PHOTOS = {key: dict(size=(W, H), model='level'|'aspect'|'free'|'roll'|'general'|'aspect_roll'|'level_roll',
                      init=dict(loc=(x,y,z), yaw=.., pitch=.., roll=.., lens=.., shift_x=.., shift_y=.., aspect=..),
                      weight=1.0, points=[(u, v, xexpr, yexpr, zexpr, label[, w]), ...])}
Expressions are python strings over the unknowns (or numbers).
Line constraint: ('L', u, v, P0, P1, label[, w]) = the pixel (u, v) lies on the projection of the 3D segment P0-P1 (rakes,
ridges, corner boards, skylines; a ground line with an unknown x pins a vanishing point without absolute coordinates).
Model 'general_skew' adds a post-render horizontal shear (keystone-edited photos: house CAM_SHEAR).
  python tools/joint_solve_lines.py houses/stanford/cams/ext_facade_solve.py [--json out.json] [--only 01,02] [--free y_up,y_cen]
"""
import math
import runpy
import sys
import json
import numpy as np

SENSOR = 36.0
PN = ['x', 'y', 'z', 'yaw', 'pitch', 'roll', 'lens', 'shift_x', 'shift_y', 'aspect', 'skew']
MODELS = {
    'level': ['x', 'y', 'z', 'yaw', 'lens', 'shift_x', 'shift_y'],
    'aspect': ['x', 'y', 'z', 'yaw', 'lens', 'shift_x', 'shift_y', 'aspect'],
    'level_roll': ['x', 'y', 'z', 'yaw', 'roll', 'lens', 'shift_x', 'shift_y'],
    'aspect_roll': ['x', 'y', 'z', 'yaw', 'roll', 'lens', 'shift_x', 'shift_y', 'aspect'],
    'free': ['x', 'y', 'z', 'yaw', 'pitch', 'lens'],
    'roll': ['x', 'y', 'z', 'yaw', 'pitch', 'roll', 'lens'],
    'general': ['x', 'y', 'z', 'yaw', 'pitch', 'roll', 'lens', 'shift_x', 'shift_y'],
    'general_aspect': ['x', 'y', 'z', 'yaw', 'pitch', 'roll', 'lens', 'shift_x', 'shift_y', 'aspect'],
    'free_roll_aspect': ['x', 'y', 'z', 'yaw', 'pitch', 'roll', 'lens', 'aspect'],
    'general_skew': ['x', 'y', 'z', 'yaw', 'pitch', 'roll', 'lens', 'shift_x', 'shift_y', 'aspect', 'skew'],
}


def basis(yaw, pitch, roll=0.0):
    y, p = math.radians(yaw), math.radians(pitch)
    fwd = np.array([math.sin(y) * math.cos(p), math.cos(y) * math.cos(p), math.sin(p)])
    right = np.array([math.cos(y), -math.sin(y), 0.0])
    up = np.cross(right, fwd)
    if roll:
        r = math.radians(roll)
        right, up = right * math.cos(r) - up * math.sin(r), up * math.cos(r) + right * math.sin(r)
    return fwd, right, up


def project(c, pts, size):
    """c = dict of the 10 camera params."""
    W, H = size
    S = max(W, H)
    fwd, right, up = basis(c['yaw'], c['pitch'], c['roll'])
    d = pts - np.array([c['x'], c['y'], c['z']])
    depth = d @ fwd
    xn = (d @ right) / depth
    yn = (d @ up) / depth
    k = c['lens'] / SENSOR
    u = W / 2 + (xn * k - c['shift_x']) * S
    v = H / 2 - (yn * k - c['shift_y']) * S * c['aspect']
    u = u + c.get('skew', 0.0) * (v - H / 2)           # post-render shear (keystone-edited photos)
    return np.stack([u, v], axis=1), depth


def _compile(expr, names):
    if isinstance(expr, (int, float)):
        return lambda u: float(expr)
    code = compile(expr, '<expr>', 'eval')
    return lambda u: float(eval(code, {'__builtins__': {}, 'math': math}, dict(zip(names, u))))


def load(path, only=None):
    cfg = runpy.run_path(path)
    names = list(cfg['UNK'])
    photos = []
    for key, ph in cfg['PHOTOS'].items():
        if only and key not in only:
            continue
        ini = dict(ph['init'])
        c0 = dict(x=ini['loc'][0], y=ini['loc'][1], z=ini['loc'][2], yaw=ini.get('yaw', 0.0), pitch=ini.get('pitch', 0.0),
                  roll=ini.get('roll', 0.0), lens=ini.get('lens', 24.0), shift_x=ini.get('shift_x', 0.0),
                  shift_y=ini.get('shift_y', 0.0), aspect=ini.get('aspect', 1.0), skew=ini.get('skew', 0.0))
        free = [p for p in MODELS[ph.get('model', 'level')] if p not in ph.get('fix', ())]
        pts, lines = [], []
        for p in ph['points']:
            if p[0] == 'L':
                w = p[6] if len(p) > 6 else 1.0
                lines.append((p[1], p[2], [_compile(e, names) for e in p[3]], [_compile(e, names) for e in p[4]], p[5], w))
                continue
            w = p[6] if len(p) > 6 else 1.0
            pts.append((p[0], p[1], [_compile(e, names) for e in p[2:5]], p[5], w))
        photos.append(dict(key=key, size=ph['size'], model=ph.get('model', 'level'), c0=c0, free=free, pts=pts, lines=lines,
                           w=ph.get('weight', 1.0)))
    return cfg, names, photos


def pack(cfg, names, photos):
    x = [cfg['UNK'][n] for n in names]
    for ph in photos:
        x += [ph['c0'][p] for p in ph['free']]
    return np.array(x, float)


def unpack_cam(x, k, ph):
    c = dict(ph['c0'])
    for i, p in enumerate(ph['free']):
        c[p] = x[k + i]
    return c, k + len(ph['free'])


def residuals(x, names, photos, priors, nu):
    u = x[:nu]
    out = []
    k = nu
    for ph in photos:
        c, k = unpack_cam(x, k, ph)
        P = np.array([[f(u) for f in p[2]] for p in ph['pts']])
        uv = np.array([[p[0], p[1]] for p in ph['pts']], float)
        w = np.array([p[4] for p in ph['pts']])[:, None] * ph['w']
        pr, depth = project(c, P, ph['size'])
        r = ((pr - uv) * w).ravel()
        out.append(np.where(np.repeat(depth, 2) > 0.05, r, 1e4))
        if ph['lines']:
            A = np.array([[f(u) for f in L[2]] for L in ph['lines']])
            B = np.array([[f(u) for f in L[3]] for L in ph['lines']])
            pa, da = project(c, A, ph['size'])
            pb, db = project(c, B, ph['size'])
            q = np.array([[L[0], L[1]] for L in ph['lines']], float)
            t = pb - pa
            nrm = np.stack([-t[:, 1], t[:, 0]], axis=1) / np.maximum(np.linalg.norm(t, axis=1), 1e-9)[:, None]
            dist = ((q - pa) * nrm).sum(axis=1) * np.array([L[5] for L in ph['lines']]) * ph['w']
            out.append(np.where((da > 0.05) & (db > 0.05), dist, 1e4))
    for n, (mean, sig) in priors.items():
        if n in names:
            out.append(np.array([(u[names.index(n)] - mean) / sig * 3.0]))
    return np.concatenate(out)


def solve(path, only=None, iters=400, extra_fix=(), unfix=()):
    cfg, names, photos = load(path, only)
    priors = cfg.get('PRIORS', {})
    fixed = (set(cfg.get('FIX', ())) | set(extra_fix)) - set(unfix)
    nu = len(names)
    x = pack(cfg, names, photos)
    free = [i for i in range(len(x)) if not (i < nu and names[i] in fixed)]
    lam = 1e-2
    r = residuals(x, names, photos, priors, nu)
    cost = r @ r
    J = None
    for _ in range(iters):
        J = np.zeros((len(r), len(free)))
        for j, i in enumerate(free):
            h = 1e-5 * max(1.0, abs(x[i]))
            q = x.copy(); q[i] += h
            J[:, j] = (residuals(q, names, photos, priors, nu) - r) / h
        J = np.nan_to_num(J)
        with np.errstate(all='ignore'):         # trial steps that cross the camera plane give huge (clipped) derivatives
            A, g = J.T @ J, J.T @ r
        ok = False
        for _ in range(16):
            step = np.linalg.solve(A + lam * np.diag(np.diag(A) + 1e-9), -g)
            q = x.copy(); q[free] += step
            rq = residuals(q, names, photos, priors, nu)
            if rq @ rq < cost:
                x, r, cost = q, rq, rq @ rq
                lam = max(lam / 3, 1e-10); ok = True
                break
            lam *= 4
        if not ok or np.linalg.norm(step) < 1e-10:
            break
    m = len(r) - len(free)
    s2 = cost / max(1, m)
    if J is None:
        J = np.eye(len(r), len(free))
    with np.errstate(all='ignore'):             # an exact fit (s2 = 0) or a clipped depth penalty in J is harmless here
        cov = np.linalg.pinv(J.T @ J) * s2
    se = np.full(len(x), np.nan)
    se[free] = np.sqrt(np.clip(np.diag(cov), 0, None))
    return cfg, names, photos, x, r, se


def cam_entry(c):
    fwd, _, _ = basis(c['yaw'], c['pitch'])
    loc = np.array([c['x'], c['y'], c['z']])
    tgt = loc + fwd * 10.0
    return ([round(float(v), 3) for v in loc], [round(float(v), 3) for v in tgt], round(float(c['lens']), 2),
            (round(c['shift_x'], 4), round(c['shift_y'], 4)), round(c['roll'], 2), round(c['aspect'], 4))


def main(argv):
    path = argv[0]
    only = None
    out = None
    fix = ()
    if '--only' in argv:
        only = argv[argv.index('--only') + 1].split(',')
    if '--json' in argv:
        out = argv[argv.index('--json') + 1]
    if '--fix' in argv:
        fix = argv[argv.index('--fix') + 1].split(',')
    iters = int(argv[argv.index('--iters') + 1]) if '--iters' in argv else 400
    free = argv[argv.index('--free') + 1].split(',') if '--free' in argv else ()
    cfg, names, photos, x, r, se = solve(path, only, iters=iters, extra_fix=fix, unfix=free)
    nu = len(names)
    print('unknowns:')
    for i, n in enumerate(names):
        print(f"  {n:12s} {x[i]:9.4f}  (+/- {se[i]:.3f})   init {cfg['UNK'][n]:.3f}")
    k, pos = nu, 0
    res = {'unknowns': {n: float(x[i]) for i, n in enumerate(names)}, 'cameras': {}}
    for ph in photos:
        c, k = unpack_cam(x, k, ph)
        n = len(ph['pts'])
        w = np.array([p[4] for p in ph['pts']])[:, None] * ph['w']
        rr = r[pos:pos + 2 * n].reshape(-1, 2) / w; pos += 2 * n
        nl = len(ph['lines'])
        wl = np.array([L[5] for L in ph['lines']]) * ph['w'] if nl else np.zeros(0)
        rl = r[pos:pos + nl] / wl if nl else np.zeros(0); pos += nl
        rms = float(np.sqrt(((rr ** 2).sum(axis=1).sum() + (rl ** 2).sum()) / max(1, n + nl)))
        loc, tgt, lens, shift, roll, asp = cam_entry(c)
        print(f"photo {ph['key']} [{ph['model']}]: ({tuple(loc)}, {tuple(tgt)}, {lens})  shift {shift}  pitch {c['pitch']:.2f} "
              f"roll {roll}  aspect {asp}  skew {c.get('skew', 0.0):.4f}  rms {rms:.2f} px")
        for p, e in zip(ph['pts'], rr):
            flag = '  <--' if math.hypot(*e) > 2.5 * max(rms, 1.0) else ''
            print(f"    {p[3]:30s} du {e[0]:7.1f}  dv {e[1]:7.1f}{flag}")
        for L, e in zip(ph['lines'], rl):
            flag = '  <--' if abs(e) > 2.5 * max(rms, 1.0) else ''
            print(f"    {'line: ' + L[4]:30s} d  {e:7.1f}{flag}")
        res['cameras'][ph['key']] = dict(params=c, loc=loc, tgt=tgt, lens=lens, shift=shift, roll=roll, aspect=asp, rms=rms)
    if out:
        with open(out, 'w') as f:
            json.dump(res, f, indent=1)


if __name__ == '__main__':
    main(sys.argv[1:])
