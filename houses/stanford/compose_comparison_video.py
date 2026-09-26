"""Stanford defaults for the reusable archviz.comparison command (film above, photo/render pair below)."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from archviz.comparison import main

if __name__ == '__main__':
    house = Path(__file__).resolve().parent
    defaults = ['--timeline', 'comparison_video_timeline.json', '--work', 'output/comparison_work',
                '--output', 'output/final/stanford_cinematic_comparison.mp4']
    main([str(house / value) if not value.startswith('--') else value for value in defaults] + sys.argv[1:])
