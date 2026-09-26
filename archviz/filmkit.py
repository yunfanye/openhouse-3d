"""bpy-free film helpers: timing constants, frame folders, PIL title overlays, contact sheets, the timeline table.

Imported both inside Blender (archviz/film.py) and by system python3 (tools/film_tools.py),
because Blender's bundled python has no PIL.  Call `configure(film_dir, frames)` first; run.py does it for the house.

A SHOT is a dict: name, sec, wp=[(cam_xyz, target_xyz), ...] (evenly spaced in time), lens=(start, end),
fstop, exp (EV), caption (lower-third text or None), ease=(in, out) (0 = come to rest, 1 = keep moving).
A TAKE is a dict with `keys` = [dict(t, cam, tgt, lens, fstop, exp, label), ...] (see houses/walsh/shots.py).
"""
import os

FPS = 24
DISSOLVE = 10            # frames of cross-dissolve between shots (0.42 s)
FADE_IN, FADE_OUT = 30, 40
W, H = 1920, 1080
FRAME_W = {"frames": 1920, "draft": 960, "preview": 640}

FILM_DIR = None          # <house>/output/film   (configure())
FRAMES = "frames"        # frame set: "frames" (final 1080p) | "draft" (960x540 quick cut) | "preview" (Workbench 640x360)


def configure(film_dir, frames=None):
    global FILM_DIR, FRAMES
    FILM_DIR = film_dir
    FRAMES = frames or 'frames'
    return FILM_DIR


def frames_of(shot):
    return int(round(shot['sec'] * FPS)) + (1 if 'keys' in shot else 0)


def shot_dir(shot):
    assert FILM_DIR, "filmkit.configure(film_dir) first"
    return os.path.join(FILM_DIR, FRAMES, shot['name'])


def titles_dir():
    return os.path.join(FILM_DIR, "titles")


def timeline(shots):
    """Print the cut: in/out times of every shot after the dissolves."""
    t = 0.0
    print(f"{'#':>2} {'shot':9} {'in':>6} {'out':>6} {'len':>5}  caption")
    for i, sh in enumerate(shots):
        if i:
            t -= DISSOLVE / FPS
        n = frames_of(sh) / FPS
        print(f"{i + 1:>2} {sh['name']:9} {t:6.1f} {t + n:6.1f} {n:5.1f}  {sh.get('caption') or ''}")
        t += n
    print(f"total {t:.1f} s")


# ------------------------------------------------------------------ titles (PIL, RGBA overlays)
def _font(face, size):
    from .media import font
    return font(size, face=face)


def _spaced(draw, xy, text, font, spacing, fill, anchor='c', shadow=None):
    """Draw letter-spaced text; anchor 'c' centres on xy, 'l' starts at xy. Returns width."""
    widths = [font.getlength(ch) for ch in text]
    total = sum(widths) + spacing * (len(text) - 1)
    x, y = xy
    x0 = x - total / 2 if anchor == 'c' else x
    if shadow is not None:
        for ch, w in zip(text, widths):
            draw.text((x0 + 2, y + 2), ch, font=font, fill=shadow, anchor='ls')
            x0 += w + spacing
        x0 = x - total / 2 if anchor == 'c' else x
    for ch, w in zip(text, widths):
        draw.text((x0, y), ch, font=font, fill=fill, anchor='ls')
        x0 += w + spacing
    return total


def make_titles(titles, shots):
    """Write <film>/titles/*.png (transparent 1920x1080 overlays): title_main, title_end and one cap_<shot> per
    captioned shot.  titles = dict(main="349 WALSH ROAD", sub="ATHERTON, CALIFORNIA", end="A MODERN ESTATE ...")."""
    from PIL import Image, ImageDraw, ImageFilter
    d = titles_dir()
    os.makedirs(d, exist_ok=True)
    white = (255, 255, 255, 255)
    soft = (255, 255, 255, 225)

    def canvas():
        return Image.new("RGBA", (W, H), (0, 0, 0, 0))

    def with_shadow(img, radius=6, alpha=0.55, offset=(0, 3), scrim=None):
        # soft dark halo under the type so it stays legible on pale sky / white walls; optional wide
        # elliptical scrim (cx, cy, rx, ry, strength) darkens the area behind a centred title card
        out = canvas()
        if scrim:
            cx, cy, rx, ry, k = scrim
            sc = Image.new("L", (W, H), 0)
            ImageDraw.Draw(sc).ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=int(255 * k))
            sc = sc.filter(ImageFilter.GaussianBlur(120))
            dark = Image.new("RGBA", (W, H), (0, 0, 0, 255))
            dark.putalpha(sc)
            out.alpha_composite(dark)
        a = img.split()[3]
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sh.putalpha(a.point(lambda v: int(v * alpha)))
        sh = sh.filter(ImageFilter.GaussianBlur(radius))
        out.alpha_composite(sh, dest=offset)
        out.alpha_composite(img)
        return out

    main, sub, end = titles.get("main", ""), titles.get("sub", ""), titles.get("end", "")
    # main title
    img = canvas(); dr = ImageDraw.Draw(img)
    _spaced(dr, (W / 2, 470), main, _font('light', 118), 22, white)
    dr.line([(W / 2 - 150, 512), (W / 2 + 150, 512)], fill=soft, width=1)
    _spaced(dr, (W / 2, 574), sub, _font('light', 34), 12, soft)
    with_shadow(img, radius=10, alpha=0.7, scrim=(W / 2, 500, 900, 260, 0.42)).save(os.path.join(d, "title_main.png"))

    # end card
    img = canvas(); dr = ImageDraw.Draw(img)
    _spaced(dr, (W / 2, 450), end, _font('light', 30), 11, soft)
    _spaced(dr, (W / 2, 560), main, _font('light', 104), 20, white)
    dr.line([(W / 2 - 150, 600), (W / 2 + 150, 600)], fill=soft, width=1)
    _spaced(dr, (W / 2, 658), sub, _font('light', 32), 12, soft)
    with_shadow(img, radius=10, alpha=0.7, scrim=(W / 2, 550, 950, 300, 0.45)).save(os.path.join(d, "title_end.png"))

    # lower-third captions
    for s in shots:
        if not s.get('caption'):
            continue
        img = canvas(); dr = ImageDraw.Draw(img)
        dr.line([(120, 958), (168, 958)], fill=soft, width=1)
        _spaced(dr, (188, 969), s['caption'], _font('light', 28), 9, white, anchor='l')
        with_shadow(img, radius=4, alpha=0.5, offset=(0, 2)).save(os.path.join(d, f"cap_{s['name']}.png"))
    print(f"[film] titles -> {d}")
    return d


def contact_sheet(out_path, shots, per_shot=6, thumb=(320, 180)):
    """A PIL sheet of evenly spaced frames from every shot (path / framing check)."""
    from PIL import Image, ImageDraw
    rows = []
    for s in shots:
        d = shot_dir(s)
        if not os.path.isdir(d):
            continue
        files = sorted(f for f in os.listdir(d) if f.startswith("f_") and f.endswith(".png"))
        if not files:
            continue
        idx = [int(round(i * (len(files) - 1) / max(1, per_shot - 1))) for i in range(per_shot)]
        rows.append((s['name'], [os.path.join(d, files[i]) for i in idx]))
    tw, th = thumb
    sheet = Image.new("RGB", (tw * per_shot, th * max(1, len(rows))), (20, 20, 20))
    dr = ImageDraw.Draw(sheet)
    for r, (name, paths) in enumerate(rows):
        for c, p in enumerate(paths):
            im = Image.open(p).convert("RGB").resize(thumb, Image.LANCZOS)
            sheet.paste(im, (c * tw, r * th))
        dr.text((6, r * th + 4), name, fill=(255, 255, 0))
    sheet.save(out_path, quality=88)
    return out_path
