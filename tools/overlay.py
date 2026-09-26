"""Check a camera match: overlay a render on its reference photograph (system Python + NumPy + PIL).

  python tools/overlay.py houses/stanford/photos/08.jpg output/renders/p08.png --out /tmp/p08_overlay.png

Writes one image with three panels stacked vertically: the render's edges (red) drawn over the desaturated
photo, the photo's edges (cyan) over the desaturated render, and a 50 % blend. The render is resized to the
photo's size first, so a preview at --scale 50 works. Edge lines that run parallel with a constant offset mean a
camera error; lines that agree in one area and diverge in another usually mean a plan dimension is wrong.
--mode edges|blend|all (default all); --crop x0,y0,x1,y1 (photo pixels) and --scale enlarge a detail.
"""
import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter


def edges(im, thresh=0.10):
    g = np.asarray(im.convert("L").filter(ImageFilter.GaussianBlur(1.0)), dtype=np.float32) / 255.0
    gx = np.zeros_like(g)
    gy = np.zeros_like(g)
    gx[:, 1:-1] = g[:, 2:] - g[:, :-2]
    gy[1:-1, :] = g[2:, :] - g[:-2, :]
    mag = np.hypot(gx, gy)
    ref = max(np.percentile(mag, 99.0), 1e-4)
    return mag / ref > thresh * 4.0


def paint(base, mask, colour):
    a = np.asarray(base.convert("L").convert("RGB"), dtype=np.float32) * 0.65 + 60
    a[mask] = colour
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def overlay(photo, render, mode="all", crop=None, scale=1.0):
    p = Image.open(photo).convert("RGB")
    r = Image.open(render).convert("RGB").resize(p.size, Image.LANCZOS)
    if crop:
        p, r = p.crop(crop), r.crop(crop)
    if scale != 1.0:
        size = (round(p.width * scale), round(p.height * scale))
        p, r = p.resize(size, Image.LANCZOS), r.resize(size, Image.LANCZOS)
    panels = []
    if mode in ("edges", "all"):
        panels.append(paint(p, edges(r), (255, 40, 40)))
        panels.append(paint(r, edges(p), (40, 230, 255)))
    if mode in ("blend", "all"):
        panels.append(Image.blend(p, r, 0.5))
    out = Image.new("RGB", (p.width, p.height * len(panels)))
    for i, im in enumerate(panels):
        out.paste(im, (0, i * p.height))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("photo", type=Path)
    ap.add_argument("render", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--mode", default="all", choices=("all", "edges", "blend"))
    ap.add_argument("--crop", default="")
    ap.add_argument("--scale", type=float, default=1.0)
    a = ap.parse_args(argv)
    crop = tuple(int(float(v)) for v in a.crop.split(",")) if a.crop else None
    overlay(a.photo, a.render, a.mode, crop, a.scale).save(a.out)
    print(a.out)


if __name__ == "__main__":
    main()
