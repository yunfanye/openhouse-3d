"""Webster defaults for the shared frozen-scene production renderer.

Prepare output/webster_cinematic.blend using film_scene.py first.
The run directory is fingerprinted; changing the scene requires a new --out.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from archviz.production import main

if __name__ == '__main__':
    house = Path(__file__).resolve().parent
    main(['--scene', str(house / 'output/webster_cinematic.blend'),
          '--out', str(house / 'output/runs/cinematic'), '--shot', 'cinematic', '--temporal'] + sys.argv[1:])
