# Webster House

The maintained reference example is a photo-derived reconstruction of 1836 Webster
Street, Palo Alto. It includes a 64-second continuous camera take, virtually staged
interiors and landscape, all 31 source-photo comparisons, and a synchronized
comparison video. Dimensions and concealed geometry are inferred where unmeasured.

## Current accepted delivery

The accepted cinematic is the kitchen-clearance V4 delivery. The cabinet/appliance
run is recessed 0.60 m; original doorway locations and appliance dimensions remain.
The corrected kitchen, roof, rear elevation, fixtures and electrical placements are
already incorporated in `plan.py` and the geometry modules. No historical patch
script is required to build the maintained source.

Final local files are under `output/final/`:

| File | Contents |
| --- | --- |
| `webster_cinematic_comparison.mp4` | 1920 × 1800, 24 fps, 1,537 frames; original cinematic above 11 distinct photo/render pairs across 12 timed sections |
| `webster_cinematic.mp4` | Accepted 1920 × 1080 cinematic, same frame count and original score |
| `models/webster.blend` | Accepted packed inspection model |
| `models/webster_cinematic.blend` | Accepted packed animated V4 scene |
| `models/portable/` | Localized copies for machines without the original Blender asset-library paths |
| `renders/` | Final named whole-house stills |
| `details/` | Separate photo-22 closet study and its scene/metadata |
| `gallery/index.html`, `gallery.zip` | Offline photo comparison viewer and portable archive |
| `webster_original_score.wav` | Original synthesized score |
| `*_poster.jpg`, `*_contact_sheet.jpg` | Accepted movie review images |
| `qa/`, `SHA256SUMS.json` | Acceptance evidence, migration map and complete retained-file checksums |

The comparison movie SHA-256 is
`7381345c2e54f19ff90bc2fa758e695e2b3fc9a3909358b73fe956ac31bea1c4`.
The cinematic SHA-256 is
`c6365c7ed919b060d33959154fa995915e431e4cc92bd07a8b017f2d3eb42d8b`.
These accepted files were not re-encoded during cleanup. The shared verifier checks
all 1,537 frames, exact panel boundaries, unchanged audio packets and cinematic SSIM
of 0.99641. Generated metadata and gallery layout may be regenerated independently.

Large final files are release assets, not part of a normal source clone. Photo-containing
releases require permission for the reference photographs. Historical QA reports
can name old run directories; those are provenance, not active instructions.
`qa/retained_paths.json` maps old paths to retained files. Obsolete frame caches and
revision scenes are removed after checksum validation.

## Build from source

Install the root project's Python dependencies and set `ARCHVIZ_PYTHON`. Then:

```sh
python tools/fetch_assets.py houses/webster/assets/sources.json
python -m houses.webster.plan
blender -b --python-exit-code 1 --python run.py -- \
  --house webster --cam hero --samples 32 --scale 50 --no-polish
blender -b --python-exit-code 1 --python run.py -- \
  --house webster --norender --save --samples 96 --min-samples 24 --threshold 0.025
```

The default save is `output/webster.blend`, separate from the accepted final model.
A fresh build reproduces the maintained geometry, not the binary identity of a
historically patched scene. Keep the accepted model for exact delivery reference.
Use `models/portable/` when moving the saved scenes to another machine.

## Architectural review

```sh
blender -b houses/webster/output/webster.blend --python-exit-code 1 \
  --python houses/webster/roof_review.py -- houses/webster/output/roof_audit --audit --audit-only
blender -b houses/webster/output/webster.blend --python-exit-code 1 \
  --python houses/webster/audit_electrical_attachments.py -- houses/webster/output/electrical.json
blender -b houses/webster/output/webster.blend --python-exit-code 1 \
  --python houses/webster/consistency_review.py -- final
```

The last command produces named 1920 × 1280 stills under
`output/consistency_review/final/`. Inspect them before replacing any accepted stills
under `output/final/renders/`. `gallery.json` documents all 31 photo mappings and
residual architectural notes independently of generated review files.

## Cinematic production

Webster has a small house-specific preparation step for its fire animation and
editorial settings; camera rendering and resume are shared:

```sh
WEBSTER_FILM_BLEND="$PWD/houses/webster/output/webster_cinematic.blend" \
  blender -b houses/webster/output/webster.blend --python-exit-code 1 \
  --python houses/webster/film_scene.py -- prepare
blender -b houses/webster/output/webster_cinematic.blend --python-exit-code 1 \
  --python tools/audit_scene.py -- --out houses/webster/output/camera_audit.json
blender -b houses/webster/output/webster_cinematic.blend --python-exit-code 1 \
  --python houses/webster/film_scene.py -- storyboard 1,228,588,720,960,1344
python houses/webster/finish_film.py --device METAL
```

Choose your actual device. The wrapper renders into `output/runs/cinematic`, with
raw, vector and filtered images under `frames/cinematic*`. A changed scene or code
requires a fresh `--out` directory. See [production](../../docs/production.md).

Generate titles/score and encode a newly rendered run:

```sh
WEBSTER_FILM_DIR="$PWD/houses/webster/output/runs/cinematic" python -m houses.webster.promo score
HOUSE_FILM_DIR="$PWD/houses/webster/output/runs/cinematic" \
WEBSTER_FILM_DIR="$PWD/houses/webster/output/runs/cinematic" \
  blender -b --python-exit-code 1 --python run.py -- --house webster \
  --film cinematic --film-encode \
  --film-music "$PWD/houses/webster/output/runs/cinematic/webster_original_score.wav" \
  --film-out "$PWD/houses/webster/output/runs/cinematic/webster_cinematic.mp4"
```

Never replace the accepted cinematic until the newly encoded file is reviewed.

## Gallery and synchronized video

The original reference photos are included in this repository as `photos/00.jpg`
through `30.jpg`; `31.jpg` is a floor plan. The existing source manifest is preserved.
They are not needed to build the model, but are needed to rebuild a gallery.
See [photo removal requests](../../PHOTO_REMOVAL.md) if an image should be removed.
The separate photo-22 study can be rebuilt with:

```sh
blender -b --python-exit-code 1 --python houses/webster/render_photo_closet.py
python houses/webster/make_photo_comparisons.py
python houses/webster/compose_comparison_video.py --prepare-only
python houses/webster/compose_comparison_video.py --verify-only
```

`make_photo_comparisons.py` and `compose_comparison_video.py` are thin defaults for
`archviz.gallery` and `archviz.comparison`. Their `--help` lists generic options.
Omit `--prepare-only` to encode a new comparison, preferably using `--output` to a
review candidate until accepted. `--verify-only` requires prepared panels in the work
directory. The accepted movie remains the reference, not something to re-encode just
because source was refactored.

Photo 22 is deliberately labeled as a **separate study**: its concealed dimensions
and stair junction are inferred, and it is not inserted into the production model
or selected by the film timeline. Other rooms also contain stated uncertainty and
virtual staging; see each pair's note and `qa/architectural_review.md`.
