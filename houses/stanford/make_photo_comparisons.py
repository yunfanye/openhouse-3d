"""Stanford photo/render comparisons: render every photo-matched camera at final quality, then build the offline
gallery (pairs, overview sheet, slider viewer) with archviz.gallery.

  blender -b --python-exit-code 1 --python run.py -- --house stanford --cam photos --samples 160 --no-dof \\
      --out houses/stanford/output/renders/final                       # (run.py builds the model from source)
  python houses/stanford/make_photo_comparisons.py                   # gallery.json -> output/final/gallery

A review round that must not touch the accepted delivery renders into its own directory and builds its gallery there:

  python houses/stanford/make_photo_comparisons.py --renders output/renders/review2 --model output/review2/stanford.blend \\
      --out output/review2/gallery --archive output/review2/gallery.zip
(--renders / --model / --out / --archive are relative to houses/stanford/; the render file names are those in gallery.json.)
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from archviz.gallery import main  # noqa: E402

if __name__ == '__main__':
    house = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--renders', default='', help='render directory replacing output/renders/final (relative to the house)')
    ap.add_argument('--model', default='', help='model .blend whose hash the manifest records (relative to the house)')
    ap.add_argument('--out', default='output/final/gallery')
    ap.add_argument('--archive', default='output/final/gallery.zip')
    a = ap.parse_args()
    config = house / 'gallery.json'
    derived = None
    if a.renders or a.model:
        # archviz.gallery keeps every path inside the config's directory, so the derived config sits beside gallery.json
        cfg = json.loads(config.read_text(encoding='utf-8'))
        for row in cfg['pairs']:
            if a.renders:
                row['render'] = (Path(a.renders) / Path(row['render']).name).as_posix()
        if a.model:
            cfg['model'] = a.model
        derived = house / '.gallery_review.json'
        derived.write_text(json.dumps(cfg, indent=2), encoding='utf-8')
        config = derived
    try:
        main(['--config', str(config), '--out', str(house / a.out), '--archive', str(house / a.archive)])
    finally:
        if derived is not None:
            derived.unlink(missing_ok=True)
