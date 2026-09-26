# 13695 Stanford Drive, Carmel IN

A photo-derived reconstruction of a 2005 Ryland two-storey on a pond lot in Stanford Park (listing:
[Zillow](https://www.zillow.com/homedetails/13695-Stanford-Dr-Carmel-IN-46074/99144200_zpid/); 4 bed, 2.5 bath,
2,345 sq ft). It includes every exterior and interior room seen in the 32 listing photographs, the street, the
neighbouring houses, the common path and the pond, a photo/render comparison gallery for all 32 photographs and a
continuous ~66-second golden-hour cinematic. Dimensions are solved from the photographs where they are visible and
inferred elsewhere; see [REFERENCES.md](REFERENCES.md). The interiors and landscaping are virtually staged.

The 32 reference photos are `photos/01.jpg` … `photos/32.jpg` (original numeric prefixes preserved). They are
included for reference only; see the [photo removal policy](../../PHOTO_REMOVAL.md).

The side-by-side walkthrough in the [project README](../../README.md) and the
[v0.1.0 release](https://github.com/yunfanye/openhouse-3d/releases/tag/v0.1.0) was made from this package.

## Package

| File | Contents |
| --- | --- |
| `plan.py` | levels, footprint, walls + openings (validated), rooms; `python -m houses.stanford.plan` |
| `house.py` | palette, lighting, `before_render` dispatch (per-photo state in each module), exterior photo cameras (`CAMS`, `CAM_SHIFT`, `CAM_ROLL`, `CAM_RES`, `CAM_ASPECT`, `CAM_SHEAR`, `CAM_OVERSCAN`) |
| `exterior.py`, `ext_skies.py` | walls, lap siding / brick veneer as geometry, J-channel trim, windows, doors, porch, roofs, gutters, fixtures; each exterior photo's sun and sky |
| `interior_main.py`, `ig_kitchen.py`, `ig_staging.py` | main-floor partitions, skins, doors, fireplace; the kitchen; great room + dining staging |
| `interior_front.py`, `front_staging.py` | foyer, living room, hall, U-stair, powder room, garage |
| `interior_upper.py`, `up_staging.py` | upper floor layout and finishes; its staging, blinds and per-photo lighting |
| `cams_main.py`, `cams_upper.py`, `cams_site.py` | solved cameras of photos 04–14 / 24, 15–23, and 26, 29, 31, 32 |
| `site.py`, `site_front.py`, `site_patio.py`, `site_nbrs.py`, `landscape.py` | the lot and the street: lawns, drive, walks, beds, patio + staging, fence, neighbours; lot vegetation |
| `context.py`, `sitefar_houses.py`, `sitefar_suburb.py`, `sitefar_trees.py` | common lawn, path, traced pond + fountain, common-area trees, houses across the pond, the subdivision |
| `shots.py` | the one-take golden-hour camera route (timed keys, re-routed for the corrected model; see REFERENCES.md) |
| `film_scene.py` | prepare / preview / storyboard / audit the cinematic scene |
| `promo.py` | titles, lower thirds, the music edit and the final encode |
| `compose_comparison_video.py`, `comparison_video_timeline.json` | the cinematic above synchronized photo/render pairs |
| `matched_take.py`, `matched_film.py`, `matched_comparison_timeline.json` | an independent reconstruction's 80-second route re-authored key-for-key in this model; its titles and fades; the synchronized photo comparison and a side-by-side of both films |
| `cams/` | camera / plan solve inputs: `ext_facade_solve.py` etc. (`tools/joint_solve_lines.py`), `int_*.json` (`tools/intcam_solve.py`), `aerials.json`, `p26.json` (`tools/solve_scene.py`) |
| `gallery.json`, `make_photo_comparisons.py` | photo/render comparison gallery (`--renders/--model/--out/--archive` for a review round) |
| `assets/sources.json`, `assets/music.json` | the CC0 sky (fetchable) and the Pixabay music provenance |

Shared helpers added for this house live in `archviz/`: `cladding.py` (lap siding, J-channel, trim, grid-decomposed
walls), `fenestration.py` (single-hung windows, shutters, panel doors, garage door, slider, blinds), `roofing.py`
(roof slopes in their own frame, fascia, soffits, gutters, downspouts), `finishes.py` (speckled laminate, cut-pile
carpet, cabinet wood, tile, Persian rug, voile and other interior materials), `furnish.py` and `stagekit.py`
(furniture, soft goods, garments, fixtures), `paving.py` (fan / circle pavers, pebble beds, edging), `phototex.py`
(textures rectified from a photograph's quadrilateral), `scatter.py` (geometry-nodes instancing), `trees.upright()`
and new materials (`brick_veneer`, `shingles`, `painted_board`, `knockdown`, `fan_pavers`) plus `sky.setup_day`.

Photo tools: `tools/photo_grid.py` (read pixel coordinates), `tools/overlay.py` (render edges over the photo),
`tools/intcam_solve.py` and `tools/joint_solve_lines.py` (point + line camera / plan solves), `tools/backproject.py`
and `tools/orthophoto.py` (pixels to ground / water plans).

## Build and check

```sh
python tools/fetch_assets.py houses/stanford/assets/sources.json      # CC0 sky for the film (17 MB)
python -m houses.stanford.plan
blender -b --python-exit-code 1 --python run.py -- --house stanford --cam hero --samples 32 --scale 50 --no-polish
blender -b --python-exit-code 1 --python run.py -- --house stanford --norender --save    # output/stanford.blend
```

Photo cameras: `--cam photos` renders every mapped photograph at its own size (use `--no-dof`). A review round
renders into its own directory and builds its gallery there, leaving `output/final` untouched:

```sh
blender -b --python-exit-code 1 --python run.py -- --house stanford --cam photos --samples 160 --no-dof \
  --out houses/stanford/output/renders/review2
python houses/stanford/make_photo_comparisons.py --renders output/renders/review2 \
  --model output/stanford.blend --out output/review2/gallery --archive output/review2/gallery.zip
```

`python tools/joint_solve_lines.py houses/stanford/cams/ext_facade_solve.py` reproduces the exterior cameras,
`python tools/intcam_solve.py houses/stanford/cams/int_great.json` the great room / kitchen ones.

## Cinematic

Download the music from its Pixabay page (see `assets/music.json`) to `output/music/`. The second-round film was
built into its own folders so the accepted first delivery (`output/final/`) stays untouched:

```sh
HOUSE_BLEND=houses/stanford/output/film_v2/stanford.blend \
  blender -b --python-exit-code 1 --python run.py -- --house stanford --norender --save
export STAN_FILM_DIR=houses/stanford/output/film_v2 STAN_FILM_BLEND=houses/stanford/output/film_v2/stanford_cinematic.blend
blender -b houses/stanford/output/film_v2/stanford.blend --python-exit-code 1 --python houses/stanford/film_scene.py -- prepare
blender -b $STAN_FILM_BLEND --python-exit-code 1 --python houses/stanford/film_scene.py -- audit
blender -b $STAN_FILM_BLEND --python-exit-code 1 --python houses/stanford/film_scene.py -- preview 12       # Workbench path check
python -m archviz.production --scene $STAN_FILM_BLEND --out houses/stanford/output/runs/cinematic_v2 --shot cinematic --device METAL
python -m houses.stanford.promo encode --frames houses/stanford/output/runs/cinematic_v2/frames/cinematic \
  --out houses/stanford/output/final_v2/stanford_cinematic.mp4
python -m houses.stanford.promo verify --out houses/stanford/output/final_v2/stanford_cinematic.mp4 --expected 1585
python houses/stanford/compose_comparison_video.py --work houses/stanford/output/comparison_work_v2 \
  --output houses/stanford/output/final_v2/stanford_cinematic_comparison.mp4
```

A changed scene needs a fresh `--out` run directory. See [production](../../docs/production.md).

## Matched walkthrough (comparison with an independent reconstruction)

`matched_take.py` re-authors the September 8 route of an independent Stanford reconstruction (its
`houses/stanford/cinematic.py`) in this model: the same 44 key times, labels, lenses, f-stop, interpolation
(`position_tension`, `angular_aim`), entry-door, powder-door and slider schedules, 1,921 frames at 24 fps. The two
plans use different origins and room sizes, so each key is placed by what it frames in the same room rather than by
one transform (see the module docstring). `matched_film.py` copies that film's opening/closing titles and fades, so
the two movies can be played frame-locked. The film is lit by the saved scene's listing-photo daylight at this
model's still exposure; no golden-hour sky, fire or practical boost. Film-only staging: the bedroom 19 / 20 doors are
shut (they swing across the upper hall) in addition to the existing dining-chair and corn-plant moves.

The other reconstruction's film and score are not part of this repository; pass your own score with `--music` and
the film to compare with `--theirs`. Rendered outputs stay in the ignored `output/` folder; published videos are
release assets.

```sh
W=houses/stanford/output/matched
STAN_TAKE=matched STAN_FILM_DIR=$W STAN_FILM_BLEND=$W/take.blend \
  blender -b houses/stanford/output/film_v2/stanford.blend --python-exit-code 1 --python houses/stanford/film_scene.py -- prepare
STAN_TAKE=matched STAN_FILM_DIR=$W blender -b $W/take.blend --python-exit-code 1 --python houses/stanford/film_scene.py -- audit
python -m archviz.production --scene $W/take.blend --out $W/production --shot cinematic
python -m houses.stanford.matched_film encode --frames $W/production/frames/cinematic \
  --music score.wav --out $W/delivery/stanford_matched_1080p.mp4
python -m archviz.comparison --timeline houses/stanford/matched_comparison_timeline.json \
  --work $W/comparison --output $W/delivery/stanford_matched_comparison.mp4
python -m houses.stanford.matched_film side-by-side --ours $W/delivery/stanford_matched_1080p.mp4 \
  --theirs other_reconstruction_1080p.mp4 --out $W/delivery/stanford_side_by_side.mp4 \
  --label-ours "This reconstruction" --label-theirs "Other reconstruction"
```
