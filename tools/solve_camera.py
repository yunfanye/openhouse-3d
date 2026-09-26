"""Solve a Blender camera from 2D photo points and their 3D model coordinates (system Python + NumPy, no bpy).

Listing photographs are usually perspective-corrected: verticals stay vertical, which is a LEVEL camera whose
optical axis is horizontal plus a lens shift.  `--model level` solves (x, y, z, yaw, lens, shift_x, shift_y);
`--model free` solves (x, y, z, yaw, pitch, lens) with no shift (drone photos, uncorrected shots);
`--model roll` adds a roll angle (degrees, positive = image rotated clockwise) for hand-held / drone frames;
`--model aspect` is `level` plus a vertical stretch (keystone-corrected drone photos whose editor also changed the
aspect): render at (W, H / aspect) and stretch the image vertically to (W, H).

Input JSON (paths relative to the file):
  {"size": [1536, 1024], "model": "level",
   "init": {"loc": [3, -16, 1.2], "yaw": 5, "pitch": 0, "lens": 26},
   "points": [[u_px, v_px, x, y, z, "label"], ...]}
yaw is the heading in degrees measured from +Y toward +X (0 = looking along +Y).

  python tools/solve_camera.py houses/stanford/cams/front.json
prints the camera as a house.py CAMS entry (location, level target, lens) + CAM_SHIFT, and per-point residuals.
Residuals are the evidence: a consistent pattern means the model (plan) is wrong, not the camera.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

SENSOR = 36.0


def basis(yaw, pitch, roll=0.0):
    y, p = math.radians(yaw), math.radians(pitch)
    fwd = np.array([math.sin(y) * math.cos(p), math.cos(y) * math.cos(p), math.sin(p)])
    right = np.array([math.cos(y), -math.sin(y), 0.0])
    up = np.cross(right, fwd)
    if roll:
        r = math.radians(roll)
        right, up = right * math.cos(r) - up * math.sin(r), up * math.cos(r) + right * math.sin(r)
    return fwd, right, up


def project(params, pts, size, model):
    W, H = size
    S = max(W, H)
    roll, aspect = 0.0, 1.0
    if model == 'level':
        x, y, z, yaw, lens, sx, sy = params
        pitch = 0.0
    elif model == 'aspect':
        x, y, z, yaw, lens, sx, sy, aspect = params
        pitch = 0.0
    elif model == 'roll':
        x, y, z, yaw, pitch, lens, roll = params
        sx = sy = 0.0
    else:
        x, y, z, yaw, pitch, lens = params
        sx = sy = 0.0
    fwd, right, up = basis(yaw, pitch, roll)
    d = pts - np.array([x, y, z])
    depth = d @ fwd
    xn = (d @ right) / depth
    yn = (d @ up) / depth
    k = lens / SENSOR
    u = W / 2 + (xn * k - sx) * S
    v = H / 2 - (yn * k - sy) * S * aspect
    return np.stack([u, v], axis=1), depth


def solve(size, pts3, uv, init, model='level', iters=200, fixed=()):
    if model == 'level':
        p = np.array([*init['loc'], init.get('yaw', 0.0), init.get('lens', 24.0), init.get('shift_x', 0.0), init.get('shift_y', 0.0)], float)
        names = ['x', 'y', 'z', 'yaw', 'lens', 'shift_x', 'shift_y']
    elif model == 'aspect':
        p = np.array([*init['loc'], init.get('yaw', 0.0), init.get('lens', 24.0), init.get('shift_x', 0.0), init.get('shift_y', 0.0),
                      init.get('aspect', 1.0)], float)
        names = ['x', 'y', 'z', 'yaw', 'lens', 'shift_x', 'shift_y', 'aspect']
    elif model == 'roll':
        p = np.array([*init['loc'], init.get('yaw', 0.0), init.get('pitch', 0.0), init.get('lens', 24.0), init.get('roll', 0.0)], float)
        names = ['x', 'y', 'z', 'yaw', 'pitch', 'lens', 'roll']
    else:
        p = np.array([*init['loc'], init.get('yaw', 0.0), init.get('pitch', 0.0), init.get('lens', 24.0)], float)
        names = ['x', 'y', 'z', 'yaw', 'pitch', 'lens']
    free = [i for i, n in enumerate(names) if n not in fixed]
    lam = 1e-2
    def resid(q):
        pr, depth = project(q, pts3, size, model)
        r = (pr - uv).ravel()
        r = np.where(np.repeat(depth, 2) > 0.05, r, 1e4)
        return r
    r = resid(p)
    cost = r @ r
    for _ in range(iters):
        J = np.zeros((len(r), len(free)))
        for j, i in enumerate(free):
            h = 1e-5 * max(1.0, abs(p[i]))
            q = p.copy(); q[i] += h
            J[:, j] = (resid(q) - r) / h
        A = J.T @ J
        g = J.T @ r
        improved = False
        for _ in range(12):
            step = np.linalg.solve(A + lam * np.diag(np.diag(A) + 1e-9), -g)
            q = p.copy()
            q[free] += step
            rq = resid(q)
            cq = rq @ rq
            if cq < cost:
                p, r, cost = q, rq, cq
                lam = max(lam / 3, 1e-9)
                improved = True
                break
            lam *= 4
        if not improved or np.linalg.norm(step) < 1e-9:
            break
    return dict(zip(names, p.tolist())), r.reshape(-1, 2)


def as_cam(sol, model):
    """(location, look-at target, lens, shift); a solved roll is reported separately (house CAM_ROLL)."""
    fwd, _, _ = basis(sol['yaw'], sol.get('pitch', 0.0))
    loc = np.array([sol['x'], sol['y'], sol['z']])
    tgt = loc + fwd * 10.0
    shift = (round(sol.get('shift_x', 0.0), 4), round(sol.get('shift_y', 0.0), 4))
    return ([round(float(v), 3) for v in loc], [round(float(v), 3) for v in tgt], round(float(sol["lens"]), 2), shift)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('config', type=Path)
    ap.add_argument('--fix', default='', help='comma list of parameters to hold at their initial values')
    a = ap.parse_args(argv)
    cfg = json.loads(a.config.read_text())
    pts = cfg['points']
    uv = np.array([[p[0], p[1]] for p in pts], float)
    xyz = np.array([[p[2], p[3], p[4]] for p in pts], float)
    model = cfg.get('model', 'level')
    fixed = tuple(v for v in (a.fix or cfg.get('fix', '')).split(',') if v)
    sol, res = solve(cfg['size'], xyz, uv, cfg['init'], model, fixed=fixed)
    loc, tgt, lens, shift = as_cam(sol, model)
    rms = float(np.sqrt((res ** 2).sum(axis=1).mean()))
    print(json.dumps({k: round(v, 4) for k, v in sol.items()}))
    print(f"CAMS entry: ({tuple(loc)}, {tuple(tgt)}, {lens})   CAM_SHIFT: {shift}   rms {rms:.1f} px")
    for p, e in zip(pts, res):
        lab = p[5] if len(p) > 5 else ''
        print(f"  {lab:28s} du {e[0]:7.1f}  dv {e[1]:7.1f}")
    return sol, res


if __name__ == '__main__':
    main(sys.argv[1:])
