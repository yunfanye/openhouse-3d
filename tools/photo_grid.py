"""Read pixel coordinates off a photograph: crop a region, enlarge it and draw a labelled pixel grid in the ORIGINAL
image's coordinates, so correspondences for tools/solve_camera.py can be read to ~1-2 px (system Python + PIL).

  python tools/photo_grid.py houses/stanford/photos/08.jpg --crop 0,150,700,650 --step 25 --scale 2 --out /tmp/g.png
  python tools/photo_grid.py photo.jpg --mark 512,300 --mark 640,410      # crosshairs at candidate points

--crop x0,y0,x1,y1 (default the whole image), --step grid pitch in original pixels (major lines every 4 steps are
labelled), --scale enlargement, --mark u,v draws a numbered crosshair (repeatable) to confirm a reading.
"""
import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def grid(path, crop=None, step=25, scale=2.0, marks=(), out=None):
    im = Image.open(path).convert("RGB")
    x0, y0, x1, y1 = crop or (0, 0, im.width, im.height)
    x0, y0, x1, y1 = max(0, x0), max(0, y0), min(im.width, x1), min(im.height, y1)
    c = im.crop((x0, y0, x1, y1))
    c = c.resize((round(c.width * scale), round(c.height * scale)), Image.LANCZOS)
    ov = Image.new("RGBA", c.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", max(10, int(11 * min(scale, 2))))
    except OSError:
        font = ImageFont.load_default()

    def X(u):
        return (u - x0) * scale

    def Y(v):
        return (v - y0) * scale
    u = (x0 // step) * step
    while u <= x1:
        major = (u // step) % 4 == 0
        if u >= x0:
            d.line([(X(u), 0), (X(u), c.height)], fill=(255, 255, 0, 150 if major else 70), width=1)
            if major:
                d.text((X(u) + 2, 2), str(u), fill=(255, 255, 0, 255), font=font, stroke_width=2, stroke_fill=(0, 0, 0, 255))
        u += step
    v = (y0 // step) * step
    while v <= y1:
        major = (v // step) % 4 == 0
        if v >= y0:
            d.line([(0, Y(v)), (c.width, Y(v))], fill=(0, 255, 255, 150 if major else 70), width=1)
            if major:
                d.text((2, Y(v) + 2), str(v), fill=(0, 255, 255, 255), font=font, stroke_width=2, stroke_fill=(0, 0, 0, 255))
        v += step
    for i, (mu, mv) in enumerate(marks):
        r = 10
        d.line([(X(mu) - r, Y(mv)), (X(mu) + r, Y(mv))], fill=(255, 0, 80, 255), width=2)
        d.line([(X(mu), Y(mv) - r), (X(mu), Y(mv) + r)], fill=(255, 0, 80, 255), width=2)
        d.text((X(mu) + 6, Y(mv) + 4), str(i + 1), fill=(255, 0, 80, 255), font=font, stroke_width=2, stroke_fill=(255, 255, 255, 255))
    res = Image.alpha_composite(c.convert("RGBA"), ov).convert("RGB")
    if out:
        res.save(out)
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("image", type=Path)
    ap.add_argument("--crop", default="")
    ap.add_argument("--step", type=int, default=25)
    ap.add_argument("--scale", type=float, default=2.0)
    ap.add_argument("--mark", action="append", default=[])
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    crop = tuple(int(float(v)) for v in a.crop.split(",")) if a.crop else None
    marks = [tuple(float(v) for v in m.split(",")) for m in a.mark]
    grid(a.image, crop, a.step, a.scale, marks, a.out)
    print(a.out)


if __name__ == "__main__":
    main()
