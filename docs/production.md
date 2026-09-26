# Production rendering and final delivery

Run commands from the repository root with the virtual environment activated.
Use `--python-exit-code 1` on Blender scripts: a Python traceback must fail the job.
See Blender's [command-line reference](https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html).

## Build and freeze a shot

For a newly created `my_house` package using the starter's `arrive` shot:

```sh
blender -b --python-exit-code 1 --python run.py -- \
  --house my_house --norender --save --samples 96 --min-samples 24 --threshold 0.025
blender -b houses/my_house/output/my_house.blend --python-exit-code 1 \
  --python tools/render_scene.py -- prepare --house my_house --shot arrive \
  --out houses/my_house/output/arrive.blend
blender -b houses/my_house/output/arrive.blend --python-exit-code 1 \
  --python tools/audit_scene.py -- --out houses/my_house/output/arrive_camera_audit.json
```

Prepare accepts a normal shot or a timed take from `house.BY_NAME`. It bakes the
camera, animates configured doors, sets film frame bounds and packs textures. A
normal shot has `round(seconds × 24)` frames. A timed take includes both endpoints;
Webster's 64-second take therefore has 1,537 frames and lasts 64.0417 seconds when
encoded at 24 fps. Blender's image sequences are **one-based**; comparison timelines
are **zero-based**.

Do not run prepare on an accepted animated scene merely to inspect it. Use
`tools/audit_scene.py` or load the `.blend` read-only. A saved source scene is not
visually approved by being successfully saved; inspect proof frames first.

## Render from the packed scene

```sh
python -m archviz.production \
  --scene houses/my_house/output/arrive.blend \
  --out houses/my_house/output/runs/arrive --shot arrive \
  --device CPU --chunk 96 --timeout 3600
```

Choose a tested GPU backend for long runs; CPU is explicit here for portability.
The default chunk contains 96 frames. Measure a representative batch and set
`--timeout` above its expected duration, including scene load and first-frame kernel
compilation. A timeout is a whole-chunk bound, not a claim about the best GPU stall
threshold. Two failed attempts stop with a log and a resumable directory.

`run.json` fingerprints the packed scene, Blender version, resolved device inventory,
worker/film/filter code and filter settings. A changed fingerprint refuses resume.
The scene must have packed image textures and no linked Blender libraries. Make
external data local before freezing. This workflow is for procedural architectural
scenes; external simulation caches need their own explicit provenance strategy.

The same command resumes an interrupted run. Existing PNGs are opened and checked
for dimensions/corruption before Blender skips them. A corrupt file fails with its
path; remove that specific incomplete frame and rerun. Do not create fake frames
or rename a neighboring frame to satisfy the count.

`production.lock` prevents concurrent controllers in one run. On normal failure
or Ctrl-C it is removed. After a force-kill, inspect the recorded PID and ensure the
owned renderer has exited before removing a stale lock. Never kill Blender by a
broad process-name pattern. Run one complete Cycles scene per GPU until measurements
show concurrency is beneficial; swapping made historic renders dramatically slower.

## Optional temporal filtering

Add `--temporal --radius 3 --tolerance 10` on a **new** run. Raw PNGs render first,
then motion vectors, then the filter; this makes all neighboring frames available
across chunk boundaries. Raw frames live in `frames/<shot>/`, vectors beside them,
and filtered frames in `frames/<shot>_tf/`.

The filter averages compatible, motion-warped neighbors. It cannot reliably infer
all glass/reflection/transparency motion from a first-surface vector pass. Inspect
raw versus filtered frames around narrow arches, shutters, railings, moving foliage,
fire and occlusion boundaries. Reject visible ghosting even if numeric noise falls.
The final Webster film used an additional manual confidence review of selected
patches; its historic thresholds are not a universal guarantee.

## Assemble

For the one prepared starter shot above:

```sh
HOUSE_FILM_DIR="$PWD/houses/my_house/output/runs/arrive" \
  blender -b --python-exit-code 1 --python run.py -- \
  --house my_house --film arrive --film-encode \
  --film-out "$PWD/houses/my_house/output/arrive.mp4"
```

The assembler creates title overlays using `ARCHVIZ_PYTHON`, uses filtered frames
when available, applies the configured film fades, and can add `--film-music path.wav`.
For multiple shots it expects their frame folders under one film root; organize
validated shot folders there explicitly and pass the selected shot names in cut
order. Keep each original render run's fingerprint with its frames.

Long runs can be started with `scripts/detach.py <log> <command...>` so they
survive the terminal that launched them.

## Acceptance and retention

A successful encode still needs these checks:

- Decode the whole MP4 and verify expected frame count, frame rate, pixel dimensions,
  duration, color metadata, audio presence and audible level.
- Inspect a contact sheet plus native frames from every shot, title/fade boundary,
  doorway crossing and photo-panel switch. Watch the actual encoded motion.
- Compare the cinematic portion against its source if compositing. The shared
  comparison verifier requires full-film SSIM above .99, checks representative and
  boundary panels, and verifies identical original audio packets.
- Record visual review honestly. The generated report says “pending” until inspected;
  passing an encode or a checksum test is not visual acceptance.

Put the accepted movies, packed models, score, selected stills, gallery and QA into
`output/final/`. A checksum inventory protects them during housekeeping:

```sh
python -m archviz.delivery houses/my_house/output --record
python -m archviz.delivery houses/my_house/output
python -m archviz.delivery houses/my_house/output --prune
```

The last command deletes everything outside `final/` in that `output` directory,
including intermediate scenes and frame caches. It first checks the entire recorded
final inventory. Keep reusable source and original references outside `output`.
Pruning means you must rerender if you later need discarded raw frames; retain them
elsewhere when future regrading or surgical frame replacement is a requirement.
