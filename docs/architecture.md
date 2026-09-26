# Architecture and maintenance boundaries

## House contract

A house is a Python package under `houses/<name>/`. Its configuration is importable
in ordinary Python; import Blender modules inside `materials()` / `setup_scene()`
instead of at the top of `house.py`.

| File | Contract |
| --- | --- |
| `plan.py` | Units, coordinates, levels, rooms, wall/opening data, assumptions; no `bpy` |
| `house.py` | `NAME`, `TITLE`, `MODULES`, `CAMS`; optional sky, grass, exposure, DOF, doors, photo pairs, palette and scene hooks |
| `shots.py` | Shot/take timing, waypoints, lens/exposure/DOF, titles; no `bpy` |
| Geometry modules | `build(materials)`; explicit ownership; build in `MODULES` order |
| `gallery.json` | Photo/render inventory, camera IDs, notes and provenance |
| `comparison_video_timeline.json` | Frame-zero-based selection of gallery pairs beneath a finished movie |
| `REFERENCES.md` | Evidence, dimensions, uncertain interpretations and staging choices |

`CAMS[name] = (location_xyz, target_xyz, focal_length_mm)`. The driver uses a 36 mm
sensor, metre units, and `Z` up. Name `EXT` cameras explicitly so the intended
exposure and depth-of-field defaults apply. `PHOTO_PAIRS` is the older contact-sheet
mapping; `gallery.json` is the explicit portable delivery mapping.

For a multi-house helper, accept data or configuration as arguments; never import
`houses.webster` into `archviz`. Python modules must not start renders, encodes,
network calls, or deletion merely by being imported. Blender command scripts live
in `tools/` and are executed deliberately with `--python-exit-code 1`.

## Shared modeling components

- `MB` in `archviz.mesh`: indexed meshes, boxes, holed walls, prisms, lathes, tubes,
  sweeps, rounded boxes, pillows, smooth objects, bevels, material slots.
- `archviz.parts`: windows/rails/slats/stairs, doors, cabinet runs, seating, beds,
  pillows, tables, sinks/faucets/tubs, lamps, twin sconces and staging objects.
- `archviz.materials`: procedural materials plus `mapped(node_tree, scale,
  rotation)` and `image_texture(node_tree, path, vector, data=False, box=False)`.
  Use `data=True` for roughness/normal/height maps. Image paths are explicit;
  material scale and the decision to use box projection remain caller choices.
- `archviz.cladding`: lap siding as real courses (with rake clipping for gables), trim boards, and `holed_wall`
  for walls whose openings stack vertically. `archviz.fenestration`: single-hung windows with grilles, shutters,
  panel doors, sectional garage doors, sliding patio doors and blinds, all placed on a wall `Face`.
  `archviz.roofing`: each roof slope is an object in its own plane frame so object-space shingles course
  correctly; fascia, soffits, rakes, gutters, downspouts and ridge caps.
- `archviz.finishes`: interior finishes (speckled laminate, cut-pile carpet, cabinet wood, tile, rugs, voile).
  `archviz.furnish` and `archviz.stagekit`: furniture, soft goods (draped comforters, bed skirts, curtains),
  garments, case goods and bath fixtures drawn into `MB` accumulators in a local frame. `archviz.paving`: smooth
  outlines, fan/circle pavers, pebble beds and edging. `archviz.phototex`: textures rectified from a photograph's
  quadrilateral (the result carries the photo's rights). `archviz.scatter`: geometry-nodes instancing for large
  context such as distant houses and trees.

The photo tools are system-Python scripts in `tools/`, not library modules:
`photo_grid.py` (read pixel coordinates), `solve_camera.py` / `solve_scene.py` (level-with-shift, free, roll and
aspect camera models; the scene solver fits several photos and named plan dimensions together),
`intcam_solve.py` / `joint_solve_lines.py` (point **and** line constraints for interiors and facades),
`overlay.py` (render edges over a photo), `backproject.py` and `orthophoto.py` (pixels to plan coordinates).
- `archviz.plan`: wall/opening matching, clipped holes, strict validation. A wall
  has `along`, `a0/a1`, `b0/b1`, `z0/z1`; an opening adds `name`, uses a plane `b`,
  and spans `a0/a1`, `z0/z1`. Positive overlap counts; mere edge contact does not.
- Vegetation, sky, lighting and finishing are separate modules because their
  scale, seeds, geometry cost and visual review requirements differ.

Do not generalize a specific house's decorative motif into a configurable system
until there is another real use. Extract a useful primitive with a stable argument
contract; leave its placement and architectural meaning in the house.

## Rendering and media boundaries

`archviz.rendering` configures Cycles. `tools/render_scene.py` prepares a shot in a
packed scene and renders requested ranges. `archviz.production` runs that worker,
locks a run directory, records input fingerprints, validates completed images,
and limits retries. It does not choose a design or declare a render visually approved.

`archviz.media`, `gallery`, `comparison`, `production`, `delivery` and `plan` work
in system Python without Blender. `filmkit` also avoids `bpy`. The compositor reads
a finished cinematic and a gallery manifest, not raw Blender scene internals.
Gallery creation preserves source image bytes. MP4 composition necessarily encodes
video again, while retaining complete original audio packets.

## Refactoring checks

Preserve object names used by cameras, doors, audits, or house refinements. Keep
mesh vertex coordinates, material slots, seeds and normal orientation stable when
moving code. Run the plan/timing tests, build the starter, and compare a Webster
scene before and after a modeling refactor. Counts alone are insufficient: compare
vertex/topology hashes and material assignments, then inspect representative views.

A saved final `.blend` is a frozen production artifact. Source rebuilding recreates
the model from the maintained plan and geometry. It is not guaranteed to recreate
the exact binary file, internal object ordering, stochastic samples, or historic
patch metadata. Preserve the accepted packed scene for exact continuation.
