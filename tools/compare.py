"""Side-by-side contact sheet: listing photo vs render for each camera (house.py PHOTO_PAIRS).

  python3 tools/compare.py --house walsh [renders_dir] [out.jpg]
  defaults: houses/<name>/output/renders  ->  <renders_dir>/_compare.jpg
"""
import os, sys
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import houses

argv = sys.argv[1:]
house = os.environ.get("HOUSE", "")
if "--house" in argv:
    i = argv.index("--house"); house = argv[i + 1]; del argv[i:i + 2]
if not house:
    sys.exit("compare.py: --house <name> (or env HOUSE) is required")
H = houses.load(house)
PHOTOS = houses.path(house, "photos")
REN = argv[0] if len(argv) > 0 else houses.path(house, "output", "renders")
OUT = argv[1] if len(argv) > 1 else os.path.join(REN, "_compare.jpg")
PAIRS = getattr(H, "PHOTO_PAIRS", [])


def photo(idx):
    for f in sorted(os.listdir(PHOTOS)):
        if f.startswith(f"{idx:02d}-") or f.startswith(f"{idx:02d}."):
            return Image.open(os.path.join(PHOTOS, f)).convert("RGB")
    return None


W, H_ = 640, 400
rows = []
for cam, idx in PAIRS:
    rp = os.path.join(REN, f"{cam}.png")
    if not os.path.exists(rp):
        continue
    p = photo(idx)
    r = Image.open(rp).convert("RGB")
    tile = Image.new("RGB", (2 * W + 10, H_ + 24), (20, 20, 20))
    if p is not None:
        p.thumbnail((W, H_)); tile.paste(p, (0, 24))
    r.thumbnail((W, H_)); tile.paste(r, (W + 10, 24))
    d = ImageDraw.Draw(tile)
    d.text((4, 4), f"photo {idx:02d}", fill=(230, 230, 230))
    d.text((W + 14, 4), f"render: {cam}", fill=(230, 230, 230))
    rows.append(tile)

cols = 2
n = len(rows)
sheet = Image.new("RGB", (cols * (2 * W + 20), max(1, (n + cols - 1) // cols) * (H_ + 30)), (10, 10, 10))
for i, t in enumerate(rows):
    sheet.paste(t, ((i % cols) * (2 * W + 20), (i // cols) * (H_ + 30)))
sheet.save(OUT, quality=88)
print("wrote", OUT, f"({n} pairs)")
