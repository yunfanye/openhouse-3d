# OpenHouse 3D — turn listing photos into 3D walkthrough videos

[![Tests](https://github.com/yunfanye/openhouse-3d/actions/workflows/tests.yml/badge.svg)](https://github.com/yunfanye/openhouse-3d/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Blender 5.2](https://img.shields.io/badge/Blender-5.2-orange.svg)](https://www.blender.org/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-3776ab.svg)](pyproject.toml)

**OpenHouse 3D rebuilds a house as a 3D model from its real-estate listing photos,
then renders a cinematic walkthrough video of it with headless Blender.** You get
photo-matched stills and a continuous fly-through/walk-through film. A comparison
video plays the film above the original listing photos.

<!-- demo-video -->
https://github.com/user-attachments/assets/7713c3fe-af4e-4139-ac58-e73f6894c496
<!-- /demo-video -->

<p align="center">
  <b>▶ <a href="https://github.com/yunfanye/openhouse-3d/releases/download/v0.1.0/stanford_side_by_side_opus5.5_vs_astra.mp4">Watch the side-by-side walkthrough</a></b>
  (65 s, 3856 × 1980, 184 MB) ·
  <a href="https://github.com/yunfanye/openhouse-3d/releases/download/v0.1.0/stanford_side_by_side_1080p.mp4">1080p version</a> (27 MB) ·
  <a href="https://yunfanye.github.io/openhouse-3d/">Project page</a>
</p>

*13695 Stanford Drive, Carmel, Indiana, rebuilt from its 32 listing photos.
**Left, Opus 5.5:** the Stanford reconstruction in this repository, built with Claude
Opus 5.5 using this toolkit. **Right, Astra:** an independent reconstruction of the
same listing. Below each film are the original listing photo and the matching
virtually staged render. The films are rendered from the 3D models; listing photos
appear only in the comparison panels.*

## What it does

| Input | Output |
| --- | --- |
| The photos from a real-estate listing (exterior, aerial, rooms) | A procedural 3D model of the house, lot and street in Blender (`.blend`) |
| A few measured or published dimensions (optional) | Renders from each listing photo's own camera, for a photo-vs-render gallery |
| Your interpretation of rooms, levels and openings | A continuous cinematic walkthrough video (1080p24, Cycles, titles and music) |
| | A synchronized comparison movie: the film above matching photo/render pairs |

Under the hood:

- **Camera solving from photos.** Point and line solvers recover each listing photo's
  camera. They handle perspective-corrected (shifted-lens) photos and drone aerials,
  and solve plan dimensions jointly across photos.
- **Procedural architecture in `bpy`.** Walls with validated openings, lap siding
  and brick as real geometry, windows, doors, stairs, roofs with gutters, kitchens,
  baths and fixtures.
- **Virtual staging and landscape.** Furniture, soft goods, rugs, art rectified from
  the photos, trees, shrubs, grass, pavers, water and the neighbouring context.
- **Production rendering.** Headless Cycles on CPU, Metal, OptiX, CUDA, HIP or oneAPI;
  packed and fingerprinted scenes; resumable chunked rendering; motion-compensated
  temporal denoising; camera-route audits for clearance and whip pans.
- **Delivery tools.** Title cards, music edit, an offline photo/render gallery,
  frame-accurate comparison videos, and checksum inventories of the final files.

This is a **modeling toolkit, not a one-click photo-to-3D service** and not
photogrammetry. A person or an AI coding agent reads the photos, sets out the plan
and writes a small house package. The library does the geometry, rendering and
video. Hidden geometry is inferred; a reconstruction is not a measured survey.

## Examples

| House | Photos | What's included |
| --- | --- | --- |
| [Stanford](houses/stanford/README.md), Carmel IN | 32 | Every photographed room, the street, neighbours and pond. Photo-solved cameras, 32 photo/render pairs, a ~66 s golden-hour cinematic and an 80 s route-matched walkthrough (the video above) |
| [Webster](houses/webster/README.md), Palo Alto CA | 31 + plan | The most documented delivery: a 64 s continuous walkthrough, 31 photo comparisons and a synchronized comparison movie |
| [Walsh](houses/walsh/README.md), Atherton CA | 34 | Modern travertine villa: 29 photo-matched stills and a 78 s long-take film |
| [Alpine](houses/alpine/README.md), Beverly Hills CA | 33 | Experimental Georgian estate; production paused |
| [`_template`](houses/_template/README.md) | none | Synthetic starter that renders with no downloads |

## Start with a small render

Requirements: Blender **5.2.x** (tested with 5.2.1), Python **3.9+**, and Git.
Blender includes `bpy`; install the Python dependencies into a separate virtual
environment. `imageio-ffmpeg` supplies FFmpeg for media tools. No API key is needed.

```sh
git clone https://github.com/yunfanye/openhouse-3d.git
cd openhouse-3d
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
export ARCHVIZ_PYTHON="$PWD/.venv/bin/python"

python tools/new_house.py my_house --title "My house"
blender -b --python-exit-code 1 --python run.py -- \
  --house my_house --cam hero --samples 16 --scale 25 --no-polish --device CPU
```

Open `houses/my_house/output/renders/hero.png`. The starter is a synthetic house
that needs no photos, downloaded textures, or saved `.blend` file. Replace its
plan, geometry, cameras, and materials with your house. The environment commands
above use a POSIX shell; see [setup](docs/setup.md) for Windows and GPU selection.

## From listing photos to a walkthrough video

1. Inventory your photos and their rights; write measured dimensions and uncertain
   assumptions in `houses/my_house/REFERENCES.md`.
2. Define one coordinate system, room volumes, levels, walls, and openings in
   `plan.py`. Solve photo cameras (`tools/photo_grid.py`, `solve_camera.py`,
   `solve_scene.py`, `intcam_solve.py`) before refining finishes.
3. Build architecture and permanent fixtures. Compare silhouettes, apertures,
   roof coverage, room connections, and fixtures against every available view
   (`tools/overlay.py`).
4. Add physically scaled materials, furnishing, vegetation, and lighting. Keep
   staging choices distinct from observed architecture.
5. Audit the baked camera route, inspect representative final-quality stills,
   freeze and pack the scene, then render into a fresh fingerprinted run.
6. Build the gallery and comparison video, decode the entire movie, inspect native
   frames and transitions, and record checksums before removing intermediates.

The detailed instructions are in [the workflow](docs/workflow.md),
[the realism checklist](docs/realism.md), and [the production guide](docs/production.md).
[Comparison manifests](docs/comparisons.md) explain the gallery and video tools.
[Lessons](docs/lessons.md) record what went wrong on each house and how it was fixed.

## Repository map

| Path | Responsibility |
| --- | --- |
| `run.py` | Build a house, configure Cycles, render stills, prepare film shots |
| `archviz/mesh.py`, `parts.py` | Mesh construction, openings, furniture, fittings |
| `archviz/cladding.py`, `fenestration.py`, `roofing.py` | Lap siding and trim, windows / doors / blinds, pitched roofs with gutters |
| `archviz/finishes.py`, `furnish.py`, `stagekit.py`, `paving.py` | Interior finishes, furniture and soft goods, pavers and landscape beds |
| `archviz/phototex.py`, `scatter.py` | Textures rectified from reference photos, geometry-nodes instancing for large context |
| `archviz/materials.py`, `sky.py`, `lights.py` | Procedural materials, photographic texture helpers, sun/sky and lighting |
| `archviz/plants.py`, `trees.py`, `polish.py` | Vegetation, grass, cloth-friendly primitives, finish passes |
| `archviz/plan.py` | Shared wall/opening validation and hole clipping, without Blender |
| `archviz/film.py`, `filmkit.py`, `camera_audit.py` | Camera motion, doors, film assembly, title helpers, route checks |
| `archviz/rendering.py`, `production.py` | Device selection, packed-scene rendering, safe resume |
| `archviz/media.py`, `gallery.py`, `comparison.py` | Portable media I/O, offline gallery, synchronized video |
| `archviz/delivery.py` | Final inventory, checksum verification, explicit pruning |
| `tools/` | Camera and plan solving from photos, house creation, asset fetching, scene preparation, audits, look-dev renders |
| `houses/_template/` | Minimal runnable starting point |
| `houses/stanford/`, `webster/`, `walsh/`, `alpine/` | Photo-derived example houses (see the table above) |

Keep transferable algorithms in `archviz/`; keep dimensions, photo mappings,
art direction, and architectural decisions in `houses/<name>/`. The library does
not import a specific house. See [architecture](docs/architecture.md).

## Outputs and verification

The listing photos for [Alpine](houses/alpine/photos/), [Stanford](houses/stanford/photos/),
[Walsh](houses/walsh/photos/) and [Webster](houses/webster/photos/) are included
so the examples can be reproduced: 131 reference images, including Webster's floor
plan, and the existing source manifests. Image bytes are preserved; Stanford's
filenames are normalized to `01.jpg` through `32.jpg`.
See [photo removal requests](PHOTO_REMOVAL.md) if an image should be removed.

Generated frames, models, movies and local environments are ignored. New house
photo folders stay local by default. Final media are published as
[release downloads](https://github.com/yunfanye/openhouse-3d/releases).

```sh
python -m pytest -q
python -m ruff check .
python -m archviz.delivery houses/my_house/output --record
python -m archviz.delivery houses/my_house/output           # verify + list cleanup candidates
python -m archviz.delivery houses/my_house/output --prune   # keep only verified final/
```

Put accepted artifacts in `output/final/` before recording the inventory. The
checksum file is a record of accepted bytes, not proof that a model is accurate.
Never replace visual review with a green test suite.

## License and contributions

Project code and documentation are [MIT licensed](LICENSE). Reference photographs,
listing floor plans, third-party assets, and media incorporating them retain their
own rights; the code license does not relicense those files. See
[asset provenance](ASSET_LICENSES.md) and [publishing](docs/publishing.md).

Contributions should include a small reproducible example and evidence appropriate
to the change. Start with [CONTRIBUTING.md](CONTRIBUTING.md).
