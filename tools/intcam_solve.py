"""Solve photo cameras from point AND line correspondences, optionally several photos together with named plan
unknowns (a small bundle adjustment).  System Python + NumPy, no bpy.

A superset of tools/solve_camera.py / solve_scene.py for interiors, where room corners are often hidden but wall /
ceiling / floor junctions, jambs and casing edges are long visible lines.  Same projection and camera conventions
(36 mm sensor across the larger image side, Blender lens shift in units of that side, yaw measured from +Y toward
+X, positive roll = image rotated clockwise as in the house CAM_ROLL), so a result drops straight into a CAMS /
CAM_SHIFT / CAM_ROLL entry.

Single photo (the solve_camera.py format plus optional keys):
  {"size": [1536, 1024], "model": "level", "photo": "../photos/08.jpg",
   "init": {"loc": [x, y, z], "yaw": 90, "pitch": 0, "roll": 0, "lens": 18, "shift_x": 0, "shift_y": 0},
   "fix": "lens",                                  comma list of camera parameters held at init
   "priors": {"z": [1.45, 0.1]},                   soft constraints (mean, sigma) on camera parameters (1 px / sigma)
   "points": [[u, v, x, y, z, "label"(, weight)], ...],         image point <-> 3D point
   "lines":  [[u, v, [x0, y0, z0], [x1, y1, z1], "label"(, weight)], ...]}
                                                   the image point lies on the projection of the 3D line x0 -> x1
Several photos: {"unknowns": {"fp_y0": 8.1, ...}, "priors": {"fp_y0": [8.1, 0.3]}, "photos": {"09": {...}, ...}};
any 3D coordinate may then be a number or an expression of the unknowns ("fp_y0+1.88").
Models: level (x y z yaw lens shift_x shift_y), level_roll (+ roll), free (x y z yaw pitch lens), free_roll (+ roll),
free_shift (free + shift_x shift_y), level_aspect (level + a vertical stretch `aspect` of the photo: render at
(W, H / aspect) and stretch to (W, H), as house CAM_ASPECT).  Labels starting with "#" are reported (read vs predicted) but not fitted.

  python tools/intcam_solve.py houses/stanford/cams/int_p07.json [--draw out.png] [--wire wire.json]
"""
import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

SENSOR = 36.0
MODELS = {
    'level': ['x', 'y', 'z', 'yaw', 'lens', 'shift_x', 'shift_y'],
    'level_roll': ['x', 'y', 'z', 'yaw', 'roll', 'lens', 'shift_x', 'shift_y'],
    'free': ['x', 'y', 'z', 'yaw', 'pitch', 'lens'],
    'free_roll': ['x', 'y', 'z', 'yaw', 'pitch', 'roll', 'lens'],
    'free_shift': ['x', 'y', 'z', 'yaw', 'pitch', 'lens', 'shift_x', 'shift_y'],
    'level_aspect': ['x', 'y', 'z', 'yaw', 'lens', 'shift_x', 'shift_y', 'aspect'],
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
    """c: dict of the 9 camera parameters; pts (n, 3) -> (n, 2) pixels, depth."""
    W, H = size
    S = max(W, H)
    fwd, right, up = basis(c['yaw'], c['pitch'], c['roll'])
    d = np.atleast_2d(np.asarray(pts, float)) - np.array([c['x'], c['y'], c['z']])
    depth = d @ fwd
    k = c['lens'] / SENSOR
    with np.errstate(divide='ignore', invalid='ignore'):
        xn = (d @ right) / depth
        yn = (d @ up) / depth
    u = W / 2 + (xn * k - c['shift_x']) * S
    v = H / 2 - (yn * k - c['shift_y']) * S * c.get('aspect', 1.0)
    return np.stack([u, v], axis=1), depth


def line_dist(c, uv, a, b, size):
    """Signed pixel distance of image point uv from the projection of the 3D line a-b (clipped to the front)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    fwd, _, _ = basis(c['yaw'], c['pitch'], c['roll'])
    o = np.array([c['x'], c['y'], c['z']])
    da, db = (a - o) @ fwd, (b - o) @ fwd
    if da <= 0.05 and db <= 0.05:
        return 1e4
    if da <= 0.05 or db <= 0.05:
        m = a + (b - a) * ((0.1 - da) / (db - da))
        a, b = (m, b) if da <= 0.05 else (a, m)
    P, _ = project(c, np.array([a, b]), size)
    d = P[1] - P[0]
    n = np.array([-d[1], d[0]]) / (np.hypot(*d) + 1e-12)
    return float((np.asarray(uv, float) - P[0]) @ n)


def _expr(e, names):
    if isinstance(e, (int, float)):
        return lambda u: float(e)
    code = compile(str(e), '<expr>', 'eval')
    return lambda u: float(eval(code, {'__builtins__': {}, 'math': math}, dict(zip(names, u))))


def _cam0(ini):
    return dict(x=ini['loc'][0], y=ini['loc'][1], z=ini['loc'][2], yaw=ini.get('yaw', 0.0), pitch=ini.get('pitch', 0.0),
                roll=ini.get('roll', 0.0), lens=ini.get('lens', 20.0), shift_x=ini.get('shift_x', 0.0), shift_y=ini.get('shift_y', 0.0),
                aspect=ini.get('aspect', 1.0))


def _photos(cfg):
    return cfg['photos'] if 'photos' in cfg else {'photo': cfg}


def _used(lab):
    return not str(lab).startswith('#')


class Problem:
    def __init__(self, cfg, fixed_extra=()):
        self.cfg = cfg
        self.names = list(cfg.get('unknowns', {})) if 'photos' in cfg else []
        self.u0 = np.array([cfg['unknowns'][n] for n in self.names], float)
        self.upri = {n: v for n, v in cfg.get('priors', {}).items() if n in self.names} if 'photos' in cfg else {}
        self.photos = []
        for key, ph in _photos(cfg).items():
            model = ph.get('model', 'level')
            fixed = set(v for v in (ph.get('fix', '') or '').split(',') if v) | set(fixed_extra)
            free = [n for n in MODELS[model] if n not in fixed]
            pts = [dict(uv=p[0:2], xyz=[_expr(e, self.names) for e in p[2:5]], lab=str(p[5]) if len(p) > 5 else '',
                        w=float(p[6]) if len(p) > 6 else 1.0) for p in ph.get('points', [])]
            lns = [dict(uv=ln[0:2], a=[_expr(e, self.names) for e in ln[2]], b=[_expr(e, self.names) for e in ln[3]],
                        lab=str(ln[4]) if len(ln) > 4 else '', w=float(ln[5]) if len(ln) > 5 else 1.0) for ln in ph.get('lines', [])]
            cpri = ph.get('priors', {}) if 'photos' in cfg else cfg.get('priors', {})
            self.photos.append(dict(key=key, cfg=ph, size=ph['size'], model=model, c0=_cam0(ph['init']), free=free, pts=pts,
                                    lns=lns, cpri={n: v for n, v in cpri.items() if n in free}))
        self.nu = len(self.names)

    def x0(self):
        return np.concatenate([self.u0] + [np.array([ph['c0'][n] for n in ph['free']], float) for ph in self.photos])

    def unpack(self, x):
        u = x[:self.nu]
        cams, k = [], self.nu
        for ph in self.photos:
            c = dict(ph['c0'])
            c.update(zip(ph['free'], x[k:k + len(ph['free'])]))
            k += len(ph['free'])
            cams.append(c)
        return u, cams

    def resid(self, x, all_=False):
        u, cams = self.unpack(x)
        out = []
        for ph, c in zip(self.photos, cams):
            for p in ph['pts']:
                if all_ or _used(p['lab']):
                    pr, dep = project(c, [[f(u) for f in p['xyz']]], ph['size'])
                    r = (pr[0] - np.asarray(p['uv'], float)) * p['w']
                    out.extend(r if dep[0] > 0.05 else [1e4, 1e4])
            for ln in ph['lns']:
                if all_ or _used(ln['lab']):
                    out.append(line_dist(c, ln['uv'], [f(u) for f in ln['a']], [f(u) for f in ln['b']], ph['size']) * ln['w'])
            for n, (m, s) in ph['cpri'].items():
                out.append((c[n] - m) / s)
        for n, (m, s) in self.upri.items():
            out.append((u[self.names.index(n)] - m) / s * 3.0)      # 3 px per sigma, as solve_scene.py
        return np.array(out, float)

    def solve(self, iters=400):
        x = self.x0()
        r = self.resid(x)
        cost = r @ r
        lam = 1e-2
        J = np.zeros((len(r), len(x)))
        for _ in range(iters):
            J = np.zeros((len(r), len(x)))
            for j in range(len(x)):
                h = 1e-5 * max(1.0, abs(x[j]))
                q = x.copy()
                q[j] += h
                J[:, j] = (self.resid(q) - r) / h
            J = np.nan_to_num(J, nan=0.0, posinf=0.0, neginf=0.0)
            with np.errstate(all='ignore'):
                A, g = J.T @ J, J.T @ r
            ok = False
            for _ in range(14):
                step = np.linalg.solve(A + lam * np.diag(np.diag(A) + 1e-9), -g)
                q = x + step
                rq = self.resid(q)
                if rq @ rq < cost:
                    x, r, cost = q, rq, rq @ rq
                    lam = max(lam / 3, 1e-10)
                    ok = True
                    break
                lam *= 4
            if not ok or np.linalg.norm(step) < 1e-10:
                break
        s2 = cost / max(1, len(r) - len(x))
        try:
            with np.errstate(all='ignore'):
                se = np.sqrt(np.clip(np.diag(np.linalg.pinv(J.T @ J) * s2), 0, None))
        except (np.linalg.LinAlgError, ValueError):
            se = np.full(len(x), np.nan)
        return x, se


def report(prob, x, se=None, out=sys.stdout):
    u, cams = prob.unpack(x)
    res = {}
    if prob.nu:
        print('unknowns:', file=out)
        for i, n in enumerate(prob.names):
            e = f"+/- {se[i]:.3f}" if se is not None else ''
            print(f"  {n:14s} {u[i]:8.3f}  {e}   init {prob.u0[i]:.3f}", file=out)
    k = prob.nu
    for ph, c in zip(prob.photos, cams):
        sub = {}
        if se is not None:
            sub = dict(zip(ph['free'], se[k:k + len(ph['free'])]))
        k += len(ph['free'])
        fwd, _, _ = basis(c['yaw'], c['pitch'], c['roll'])
        loc = np.array([c['x'], c['y'], c['z']])
        tgt = loc + fwd * 10.0
        rows, sq = [], []
        for p in ph['pts']:
            pr, _ = project(c, [[f(u) for f in p['xyz']]], ph['size'])
            du, dv = pr[0] - np.asarray(p['uv'], float)
            if _used(p['lab']):
                sq.append(du * du + dv * dv)
            rows.append(f"    pt   {p['lab'][:40]:40s} read ({p['uv'][0]:7.1f},{p['uv'][1]:7.1f})  du {du:7.1f}  dv {dv:7.1f}")
        for ln in ph['lns']:
            d = line_dist(c, ln['uv'], [f(u) for f in ln['a']], [f(u) for f in ln['b']], ph['size'])
            if _used(ln['lab']):
                sq.append(d * d)
            rows.append(f"    line {ln['lab'][:40]:40s} read ({ln['uv'][0]:7.1f},{ln['uv'][1]:7.1f})  dist {d:7.1f}")
        rms = math.sqrt(np.mean(sq)) if sq else 0.0
        print(f"photo {ph['key']}  [{ph['model']}]  rms {rms:.2f} px over {len(sq)} residuals", file=out)
        print("  " + json.dumps({kk: round(float(v), 4) for kk, v in c.items()}), file=out)
        if sub:
            print("  std err: " + ", ".join(f"{kk} {v:.3g}" for kk, v in sub.items()), file=out)
        asp = f"   CAM_ASPECT: {round(c['aspect'], 4)}" if abs(c.get('aspect', 1.0) - 1.0) > 1e-9 else ''
        print(f"  CAMS: ({tuple(round(float(v), 3) for v in loc)}, {tuple(round(float(v), 3) for v in tgt)}, {round(c['lens'], 2)})"
              f"   CAM_SHIFT: ({round(c['shift_x'], 4)}, {round(c['shift_y'], 4)})   CAM_ROLL: {round(c['roll'], 2)}{asp}", file=out)
        for s in rows:
            print(s, file=out)
        res[ph['key']] = dict(cam=c, loc=loc.tolist(), tgt=tgt.tolist(), rms=rms)
    return res


def _segment_px(c, a, b, size, n=40):
    t = np.linspace(0.0, 1.0, n)[:, None]
    P = np.asarray(a, float) + (np.asarray(b, float) - np.asarray(a, float)) * t
    pr, dep = project(c, P, size)
    return [tuple(p) for p, d in zip(pr, dep) if d > 0.05]


def wire_segments(spec):
    """wire JSON: [[x0,y0,z0],[x1,y1,z1]] segments, {"box": [x0,x1,y0,y1,z0,z1]} boxes, {"rect": [along,a0,a1,b,z0,z1]}."""
    segs = []
    for s in spec:
        if isinstance(s, dict) and 'box' in s:
            x0, x1, y0, y1, z0, z1 = s['box']
            cs = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
            for i in range(4):
                (xa, ya), (xb, yb) = cs[i], cs[(i + 1) % 4]
                segs += [([xa, ya, z0], [xb, yb, z0]), ([xa, ya, z1], [xb, yb, z1]), ([xa, ya, z0], [xa, ya, z1])]
        elif isinstance(s, dict) and 'rect' in s:
            al, a0, a1, b, z0, z1 = s['rect']
            q = [(a0, z0), (a1, z0), (a1, z1), (a0, z1)]
            P = [[a, b, z] if al == 'X' else [b, a, z] for a, z in q]
            segs += [(P[i], P[(i + 1) % 4]) for i in range(4)]
        elif isinstance(s, dict):
            continue
        else:
            segs.append((s[0], s[1]))
    return segs


def draw(prob, x, key, photo, out, wire=()):
    """The photo with read points (cyan +), their projections (red o), fitted lines (red) and a wireframe (yellow)."""
    from PIL import Image, ImageDraw
    u, cams = prob.unpack(x)
    i = [ph['key'] for ph in prob.photos].index(key)
    ph, c = prob.photos[i], cams[i]
    im = Image.open(photo).convert('RGB')
    d = ImageDraw.Draw(im)
    for (a, b) in wire:
        poly = _segment_px(c, a, b, ph['size'])
        if len(poly) > 1:
            d.line(poly, fill=(255, 220, 0), width=1)
    for ln in ph['lns']:
        poly = _segment_px(c, [f(u) for f in ln['a']], [f(u) for f in ln['b']], ph['size'])
        if len(poly) > 1:
            d.line(poly, fill=(255, 40, 40), width=1)
        uu, vv = ln['uv']
        d.ellipse([uu - 3, vv - 3, uu + 3, vv + 3], outline=(0, 230, 255), width=2)
    for p in ph['pts']:
        pr, _ = project(c, [[f(u) for f in p['xyz']]], ph['size'])
        uu, vv = p['uv']
        col = (0, 230, 255) if _used(p['lab']) else (255, 0, 255)
        d.line([uu - 5, vv, uu + 5, vv], fill=col, width=2)
        d.line([uu, vv - 5, uu, vv + 5], fill=col, width=2)
        pu, pv = pr[0]
        d.ellipse([pu - 4, pv - 4, pu + 4, pv + 4], outline=(255, 40, 40), width=2)
        d.line([uu, vv, pu, pv], fill=(255, 40, 40), width=1)
    im.save(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('config', type=Path)
    ap.add_argument('--fix', default='', help='extra comma list of camera parameters to hold at init')
    ap.add_argument('--noopt', action='store_true', help='evaluate the initial cameras without solving')
    ap.add_argument('--draw', type=Path, help='write the photo with read / projected points and lines (single photo, '
                                               'or DIR for one image per photo)')
    ap.add_argument('--wire', type=Path, help='JSON list of 3D segments / boxes drawn through the solved camera')
    ap.add_argument('--json', type=Path, help='write the solved cameras / unknowns here')
    ap.add_argument('--photos', type=Path, help='directory holding the photos (overrides the configured paths)')
    a = ap.parse_args(argv)
    cfg = json.loads(a.config.read_text())
    prob = Problem(cfg, fixed_extra=tuple(v for v in a.fix.split(',') if v))
    if a.noopt:
        x, se = prob.x0(), None
    else:
        x, se = prob.solve()
    res = report(prob, x, se)
    if a.json:
        u, _ = prob.unpack(x)
        a.json.write_text(json.dumps(dict(unknowns=dict(zip(prob.names, map(float, u))),
                                          cameras={k: dict(v, cam={kk: float(vv) for kk, vv in v['cam'].items()}) for k, v in res.items()}),
                                     indent=1))
    if a.draw:
        wire = wire_segments(json.loads(a.wire.read_text())) if a.wire else ()
        for ph in prob.photos:
            photo = ph['cfg'].get('photo')
            if photo and a.photos:
                photo = a.photos / Path(photo).name
            elif photo and not Path(photo).is_absolute():
                photo = a.config.parent / photo
            out = a.draw if len(prob.photos) == 1 else a.draw / f"{ph['key']}.png"
            if photo:
                draw(prob, x, ph['key'], photo, out, wire)
                print(out)
    return res


if __name__ == '__main__':
    main(sys.argv[1:])
