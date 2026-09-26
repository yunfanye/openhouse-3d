"""Back-project photo pixels onto a horizontal plane with a solved camera (system Python + NumPy, no bpy).

The inverse of tools/solve_camera.project: a pixel (u, v) and a height z give the world point where the pixel's ray
meets the plane Z = z.  Use it to trace things that lie on the ground or the water in a solved photo (a shoreline, a
path's edges, tree trunks and canopy centres, lot corners) and turn them into plan coordinates.

  python tools/solve_scene.py houses/stanford/cams/aerials.json --json scratch/site_solution.json
  python tools/backproject.py scratch/site_solution.json 31 --z -1.85 --px 480,290 --px 1200,160
  python tools/backproject.py scratch/site_solution.json 32 --z -0.9 --file shore32.txt     # "u v [z] [label]" lines

The solution JSON is what `tools/solve_scene.py --json` writes (cameras.<key>.sol with the model's parameters; the
model is inferred from the keys) or a single-camera dict {"size": [W, H], "sol": {...}}.  Photos with a lens shift
(`level` model) and rolled drone frames (`roll`) are supported.  Rays that point above the horizon print `nan`.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from solve_camera import SENSOR, basis          # noqa: E402


def camera(sol, size):
    """(origin, fwd, right, up, focal_px, shift_px) from a solved parameter dict."""
    W, H = size
    S = max(W, H)
    fwd, right, up = basis(sol['yaw'], sol.get('pitch', 0.0), sol.get('roll', 0.0))
    k = sol['lens'] / SENSOR * S
    return np.array([sol['x'], sol['y'], sol['z']]), fwd, right, up, k, (sol.get('shift_x', 0.0) * S, sol.get('shift_y', 0.0) * S), \
        sol.get('aspect', 1.0)


def ray(cam, size, u, v):
    o, fwd, right, up, k, (sx, sy), asp = cam
    W, H = size
    xn = (u - W / 2) / k + sx / k
    yn = -(v - H / 2) / (k * asp) + sy / k
    d = fwd + right * xn + up * yn
    return o, d / np.linalg.norm(d)


def to_plane(cam, size, u, v, z):
    o, d = ray(cam, size, u, v)
    if abs(d[2]) < 1e-9 or (z - o[2]) / d[2] <= 0:
        return np.array([math.nan, math.nan, z])
    t = (z - o[2]) / d[2]
    return o + d * t


def load(path, key=None):
    data = json.loads(Path(path).read_text())
    if 'cameras' in data:
        c = data['cameras'][key]
        size = c.get('size') or data.get('sizes', {}).get(key) or [1536, 1152]
        return c['sol'], size
    return data['sol'], data['size']


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('solution', type=Path)
    ap.add_argument('key', nargs='?', default=None, help='camera key inside a solve_scene solution')
    ap.add_argument('--size', default='', help='W,H (default: from the solution, else 1536,1152)')
    ap.add_argument('--z', type=float, default=0.0, help='plane height for points without their own z')
    ap.add_argument('--px', action='append', default=[], help='u,v[,z] (repeatable)')
    ap.add_argument('--file', type=Path, help='text file of "u v [z] [label]" lines')
    a = ap.parse_args(argv)
    sol, size = load(a.solution, a.key)
    if a.size:
        size = [int(s) for s in a.size.split(',')]
    cam = camera(sol, size)
    rows = []
    for p in a.px:
        f = [float(s) for s in p.split(',')]
        rows.append((f[0], f[1], f[2] if len(f) > 2 else a.z, ''))
    if a.file:
        for line in a.file.read_text().splitlines():
            t = line.split('#')[0].split()
            if len(t) >= 2:
                z = float(t[2]) if len(t) > 2 and t[2].lstrip('-').replace('.', '', 1).isdigit() else a.z
                rows.append((float(t[0]), float(t[1]), z, ' '.join(t[3:] if len(t) > 3 else [])))
    for (u, v, z, lab) in rows:
        P = to_plane(cam, size, u, v, z)
        print(f"{u:8.1f} {v:8.1f}  ->  x {P[0]:9.2f}  y {P[1]:9.2f}  z {P[2]:6.2f}  {lab}")


if __name__ == '__main__':
    main(sys.argv[1:])
