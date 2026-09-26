"""PIL-side helpers for a house's promo film (system python3; Blender's python has no PIL).

  python3 tools/film_tools.py --house walsh titles                    # output/film/titles/*.png overlays
  python3 tools/film_tools.py --house walsh sheet [frames|draft|preview] [per_shot]   # output/film/_sheet_<set>.jpg
  python3 tools/film_tools.py --house walsh timeline                  # shot table with in/out times in the cut
"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import houses
from archviz import filmkit

argv = sys.argv[1:]
house = os.environ.get("HOUSE", "")
if "--house" in argv:
    i = argv.index("--house"); house = argv[i + 1]; del argv[i:i + 2]
if not house:
    sys.exit("film_tools.py: --house <name> (or env HOUSE) is required")
H = houses.load(house)
filmkit.configure(houses.path(house, "output", "film"))
shots = list(getattr(H, "SHOTS", []))
by_name = dict(getattr(H, "BY_NAME", {s['name']: s for s in shots}))

cmd = argv[0] if argv else "titles"
if cmd == "titles":
    if hasattr(H, 'make_titles'):
        H.make_titles()
    else:
        filmkit.make_titles(getattr(H, "TITLES", {"main": house.upper()}), list(by_name.values()))
elif cmd == "timeline":
    filmkit.timeline(shots)
elif cmd == "sheet":
    filmkit.FRAMES = argv[1] if len(argv) > 1 else "frames"
    per = int(argv[2]) if len(argv) > 2 else 6
    out = filmkit.contact_sheet(os.path.join(filmkit.FILM_DIR, f"_sheet_{filmkit.FRAMES}.jpg"), list(by_name.values()), per_shot=per)
    print("[film] sheet ->", out)
else:
    sys.exit(f"unknown command {cmd}")
