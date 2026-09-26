# Starter house

Create a package with `python tools/new_house.py my_house --title "My house"` from
the repository root. It builds a synthetic 14 × 11 m two-storey house with four
rooms, glass front, door, lawn, hedge and trees. No reference images or external
textures are needed for the first render.

```sh
blender -b --python-exit-code 1 --python run.py -- \
  --house my_house --cam hero --samples 16 --scale 25 --no-polish --device CPU
```

Edit `plan.py` first, then `house.py`, `shots.py`, and the geometry modules listed
in `MODULES`. Fill out `REFERENCES.md`. Keep your originals under `photos/` (ignored
by Git). Copy `gallery.example.json` to `gallery.json` when the corresponding source
photos and rendered views exist.

`build(materials)` is the geometry-module contract. Camera entries contain location,
target and lens in millimetres. Modules share metre coordinates and the room/level
constants in `plan.py`. See [the workflow](../../docs/workflow.md),
[architecture](../../docs/architecture.md) and [production](../../docs/production.md).
