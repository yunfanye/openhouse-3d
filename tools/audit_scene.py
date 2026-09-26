"""Run a camera obstruction audit inside Blender; a blocked lens exits with error."""
import argparse
from pathlib import Path
import sys

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from archviz.camera_audit import audit
from archviz.media import write_json

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--out', required=True, type=Path)
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
report = audit(bpy.context.scene)
write_json(args.out, report)
print(f'Audited {report["frames"]} frames; {len(report["lens_obstructions"])} lens obstructions, '
      f'{len(report["path_crossings"])} path crossings')
if report['lens_obstructions'] or report['path_crossings']:
    raise ValueError(f'Camera route intersects geometry; see {args.out}')
