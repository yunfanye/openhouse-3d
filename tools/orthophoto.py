"""Rectify a solved photograph onto a horizontal plane: an "orthophoto" in plan coordinates with a labelled metre grid
(system Python + NumPy + PIL, no bpy).  Every output pixel is a ground point (x, y, z); it is projected into the photo
with the solved camera (tools/solve_camera.project) and sampled.  Things that lie on the plane (shorelines, paths,
lawns, trunk bases, shadows, lot lines) land at their true plan position; raised things (canopies, roofs) lean away
from the camera, so read trees at their trunks or shadows.

  python tools/orthophoto.py houses/stanford/photos/32.jpg scratch/site_solution.json 32 --z -0.6 \
      --extent -120,120,-30,260 --res 0.25 --grid 10 --out scratch/ortho32.png

The solution JSON comes from `tools/solve_scene.py <photos.json> --json <out>` (see tools/backproject.py).

--extent x0,x1,y0,y1 in metres, --res metres per output pixel, --grid spacing of the grid lines (labels every 5th),
--mark x,y draws a numbered cross at a plan point (repeatable) to check a reading.  Areas outside the photo are grey.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from solve_camera import project          # noqa: E402

KEYS = {'level': ['x', 'y', 'z', 'yaw', 'lens', 'shift_x', 'shift_y'], 'roll': ['x', 'y', 'z', 'yaw', 'pitch', 'lens', 'roll'],
        'aspect': ['x', 'y', 'z', 'yaw', 'lens', 'shift_x', 'shift_y', 'aspect'], 'free': ['x', 'y', 'z', 'yaw', 'pitch', 'lens']}


def params(sol):
    for model in ('aspect', 'level', 'roll', 'free'):
        if all(k in sol for k in KEYS[model]) and (model != 'free' or 'roll' not in sol):
            return model, [sol[k] for k in KEYS[model]]
    raise ValueError(f'unrecognised camera solution {sorted(sol)}')


def ortho(photo, sol, extent, res, z=0.0, zfun=None):
    im = np.asarray(Image.open(photo).convert('RGB'))
    H, W = im.shape[:2]
    model, p = params(sol)
    x0, x1, y0, y1 = extent
    nx, ny = int(round((x1 - x0) / res)), int(round((y1 - y0) / res))
    xs = x0 + (np.arange(nx) + 0.5) * res
    ys = y1 - (np.arange(ny) + 0.5) * res                    # image row 0 = the far (+Y) edge
    X, Y = np.meshgrid(xs, ys)
    Z = np.full_like(X, z) if zfun is None else zfun(X, Y)
    pts = np.stack([X.ravel(), Y.ravel(), Z.ravel()], axis=1)
    uv, depth = project(np.array(p, float), pts, (W, H), model)
    u, v = uv[:, 0], uv[:, 1]
    ok = (depth > 0) & (u >= 0) & (u < W - 1) & (v >= 0) & (v < H - 1)
    out = np.full((len(u), 3), 110, np.uint8)
    ui, vi = np.clip(u, 0, W - 2), np.clip(v, 0, H - 2)
    u0, v0 = np.floor(ui).astype(int), np.floor(vi).astype(int)
    fu, fv = (ui - u0)[:, None], (vi - v0)[:, None]
    c = (im[v0, u0] * (1 - fu) * (1 - fv) + im[v0, u0 + 1] * fu * (1 - fv) + im[v0 + 1, u0] * (1 - fu) * fv
         + im[v0 + 1, u0 + 1] * fu * fv)
    out[ok] = c[ok].astype(np.uint8)
    return Image.fromarray(out.reshape(ny, nx, 3)), (x0, x1, y0, y1, res)


def draw_grid(img, frame, step=10.0, marks=()):
    x0, x1, y0, y1, res = frame
    d = ImageDraw.Draw(img, 'RGBA')
    try:
        font = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', 11)
    except OSError:
        font = ImageFont.load_default()

    def P(x, y):
        return ((x - x0) / res, (y1 - y) / res)
    k0 = int(np.ceil(x0 / step))
    for k in range(k0, int(np.floor(x1 / step)) + 1):
        x = k * step
        major = k % 5 == 0
        d.line([P(x, y0), P(x, y1)], fill=(255, 255, 0, 170 if major else 60), width=1)
        if major:
            d.text((P(x, y1)[0] + 2, 2), f'{x:g}', fill=(255, 255, 0, 255), font=font, stroke_width=2, stroke_fill=(0, 0, 0, 255))
    for k in range(int(np.ceil(y0 / step)), int(np.floor(y1 / step)) + 1):
        y = k * step
        major = k % 5 == 0
        d.line([P(x0, y), P(x1, y)], fill=(0, 255, 255, 170 if major else 60), width=1)
        if major:
            d.text((2, P(x0, y)[1] + 1), f'{y:g}', fill=(0, 255, 255, 255), font=font, stroke_width=2, stroke_fill=(0, 0, 0, 255))
    for i, (x, y) in enumerate(marks):
        u, v = P(x, y)
        d.line([(u - 7, v), (u + 7, v)], fill=(255, 0, 60, 255), width=2)
        d.line([(u, v - 7), (u, v + 7)], fill=(255, 0, 60, 255), width=2)
        d.text((u + 5, v + 3), str(i + 1), fill=(255, 0, 60, 255), font=font, stroke_width=2, stroke_fill=(255, 255, 255, 255))
    return img


def load_solution(path, key=None):
    data = json.loads(Path(path).read_text())
    if 'cameras' in data:
        return data['cameras'][key]['sol']
    return data.get('sol', data)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('photo', type=Path)
    ap.add_argument('solution', type=Path)
    ap.add_argument('key', nargs='?', default=None)
    ap.add_argument('--z', type=float, default=0.0)
    ap.add_argument('--extent', required=True)
    ap.add_argument('--res', type=float, default=0.25)
    ap.add_argument('--grid', type=float, default=10.0)
    ap.add_argument('--mark', action='append', default=[])
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args(argv)
    ext = [float(s) for s in a.extent.split(',')]
    img, frame = ortho(a.photo, load_solution(a.solution, a.key), ext, a.res, a.z)
    marks = [tuple(float(s) for s in m.split(',')) for m in a.mark]
    draw_grid(img, frame, a.grid, marks).save(a.out)
    print(a.out, img.size)


if __name__ == '__main__':
    main(sys.argv[1:])
