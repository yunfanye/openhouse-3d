import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import overlay                                          # noqa: E402
import photo_grid                                       # noqa: E402


def _card(path, box):
    im = Image.new('RGB', (200, 120), (200, 200, 200))
    ImageDraw.Draw(im).rectangle(box, fill=(20, 20, 20))
    im.save(path)
    return path


def test_grid_keeps_original_pixel_coordinates(tmp_path):
    src = _card(tmp_path / 'p.png', (60, 40, 100, 80))
    out = photo_grid.grid(src, crop=(50, 30, 150, 90), step=10, scale=3.0, out=tmp_path / 'g.png')
    assert out.size == (300, 180)
    a = np.asarray(out, dtype=float)
    # the dark square's top-left corner (60, 40) lands at ((60-50)*3, (40-30)*3) in the enlargement
    assert a[33:40, 33:40].mean() < 90
    assert a[5:20, 5:20].mean() > 120
    # a mark's crosshair is centred on the same enlarged position (its label glyphs vary by platform font)
    marked = np.asarray(photo_grid.grid(src, crop=(50, 30, 150, 90), step=10, scale=3.0, marks=[(60, 40)]), dtype=int)
    arm = marked[30, 21:29]
    assert (arm[:, 0] > 200).all() and (arm[:, 1] < 80).all()


def test_overlay_marks_render_edges_on_the_photo(tmp_path):
    photo = _card(tmp_path / 'photo.png', (60, 40, 100, 80))
    render = _card(tmp_path / 'render.png', (64, 40, 104, 80))
    Image.open(render).resize((100, 60)).save(render)          # previews are often smaller than the photo
    out = overlay.overlay(photo, render)
    assert out.size == (200, 360)                              # edges on photo, edges on render, blend
    red = np.asarray(out.crop((0, 0, 200, 120)), dtype=int)
    is_red = (red[..., 0] > 200) & (red[..., 1] < 80)
    cols = np.nonzero(is_red.any(axis=0))[0]
    assert abs(cols.min() - 64) <= 3 and abs(cols.max() - 104) <= 3     # the render's (offset) outline, not the photo's
