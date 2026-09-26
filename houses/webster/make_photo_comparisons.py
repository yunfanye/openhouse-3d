"""Webster defaults for the reusable archviz.gallery command; pass CLI options to override."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from archviz.gallery import main

if __name__ == '__main__':
    house = Path(__file__).resolve().parent
    defaults = ['--config', 'gallery.json', '--out', 'output/final/gallery', '--archive', 'output/final/gallery.zip']
    main([str(house / value) if not value.startswith('--') else value for value in defaults] + sys.argv[1:])
