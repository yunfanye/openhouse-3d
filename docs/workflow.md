# From reference photos to a believable house

## 1. Record evidence before modeling

Create the house with `python tools/new_house.py my_house --title "My house"`.
Put local photos under `houses/my_house/photos/`, assign stable numeric IDs, and
write `REFERENCES.md`. Use photos you own or have permission to use. Preserve the
original image rather than repeatedly saving JPEGs during analysis. Keep a separate
copy if removing EXIF location data for a public release.

For each photo record the room, visible walls, view direction, distinguishing
fixtures, approximate camera height/lens, source, rights, and whether it is cropped
or perspective-corrected. Mark floor plans separately; they are supporting drawings,
not extra photographs that need a fabricated camera match.

Make an evidence table: **observation → constraint → confidence → unresolved question**.
A room can look larger because of a wide lens, not because a wall moved. A mirror
can create an apparent opening. A tree can conceal a roof junction. Reconcile these
across photos before treating them as geometry.

Measure at least one reliable scale reference: an actual wall dimension is better
than a nominal appliance size. Use door and cabinet dimensions only as stated
assumptions when measurements are unavailable. Record the uncertainty; do not
invent exact dimensions from visual impressions.

## 2. Establish one plan

Use metres, `Z` up, `X` left/right as seen from the street, and `Y` street-to-rear.
Put those conventions, floor levels, wall thicknesses and room volumes in `plan.py`.
Every module must share them. Separate the slab surface from the finished floor,
ceiling underside, roof deck and roof finish; confusing these causes penetrations.

Define wall spans and openings once. `archviz.plan.validate(WALLS, OPENINGS)` checks
positive dimensions, names, containment, and exactly one wall per opening. Webster
shows this data model and retains its historical `holes_for()` / `check()` API.
The starter has a simpler explicit glass-wall layout; adopt the wall table when
its architectural complexity warrants it.

Sketch the adjacency graph: which rooms connect, which door swings into which room,
how the stair rises, and where upper floors bear on lower walls. Check upper/lower
alignment with an overhead view before adding furniture. Correct the plan first;
revisit hand-placed furniture and camera paths after a wall moves.

## 3. Solve cameras against simple geometry

Block out the silhouette, floor levels and apertures. Use flat neutral materials
and low-sample, small renders. Match a source photo's framing and aspect ratio.
Set camera height, distance, target, and focal length together; focal length alone
cannot fix perspective. The camera contract uses a 36 mm sensor.

Compare the render with the original at 50% opacity or with the gallery slider.
Track landmarks at the corners of windows, sill/eave lines, door jambs and roof
breaks. Check several vertical and horizontal alignments, not just the center.
A consistent scale error suggests geometry; a divergence toward the edges often
suggests a camera/lens mismatch. Perspective-corrected listing photos may not admit
one perfect pinhole-camera solution. Document residual error.

Solve rather than eyeball once the block-out is close. Read pixel coordinates with
`tools/photo_grid.py`, then fit known points with `tools/solve_camera.py` (one photo)
or `tools/solve_scene.py` (several photos plus named plan unknowns). Interiors, where
corners are often hidden, solve better from lines (wall/ceiling junctions, jambs) with
`tools/intcam_solve.py` or `tools/joint_solve_lines.py`. Check each result with
`tools/overlay.py`. `houses/stanford/cams/` has worked inputs for every solver.

Model the simplest geometry supported by evidence. Webster's front roofline needed
a straight rake, not a smoothed spline. A visually appealing alternate shape is not
a substitute for the photographed silhouette.

## 4. Build architecture and permanent fixtures

Assign ownership: exterior walls/openings/roofs; site; each interior level or zone;
landscape. Every geometry module exposes `build(materials)` and reads the shared
plan. Keep stable names for objects used by doors, film, or audits.

Check all permanent features: sash divisions and operable types; arch springing and
apex; sill depths; chimney/fireplace alignment; rainwater drainage; bathroom fixture
positions; cabinet depth and full appliance envelopes; vents, railings, switch
plates and outlets. Back switches and mirrors with actual wall surfaces. View both
sides of a door and account for its leaf, hinge, handle and swing.

Run structural diagnostics before expensive rendering. Webster includes roof
coverage/runoff and electrical-attachment audits. These test its particular geometry;
they are examples for writing checks appropriate to another house, not universal
building-code checks. Raycast and mesh evidence are stronger than a beauty render
for hidden overlaps, but must be interpreted in scene coordinates.

## 5. Add materials and staging

Use [the realism checklist](realism.md). Establish physically scaled material
features under neutral daylight before grading. Roughness/normal/height textures
are data, not sRGB colors. OpenGL normal maps need the appropriate tangent-space
interpretation; distinguish a normal map from a height/bump map.

Separate architecture from virtual staging. Furniture, renewed paint, healthy grass,
artwork and warm dusk lighting may be intentional, but label them. Do not quietly
replace a real window type or fixture simply because a newer style looks better.

Use deterministic seeds for vegetation and procedural detail. Inspect leaf normals
from above as well as below. Avoid density that hides architectural errors or makes
rendering unmanageable. Check tree trunks against grade and background ground extent.

## 6. Review every reference

Set `CAMS` and an explicit gallery mapping for every photographic view. Keep a note
for each pair identifying residual differences and inferred geometry. Use matched
exposure for diagnostic comparisons; dramatic cinematic lighting can conceal errors.
Review hero, rear, side, all rooms, and details. Inspect native pixels as well as
contact sheets. Contact sheets find global problems; they hide floating switches,
misaligned glazing and temporal ghosts.

If a view cannot be reconciled with the whole-house model, say so. Webster photo
22 is a separate photo-derived closet study with an inferred stair junction. It is
labeled `separate_photo_derived_detail` and the video compositor rejects it as a
whole-house movie comparison. Never use a separate study to imply solved geometry.

## 7. Freeze, render, finish, inspect

Follow [production](production.md). Audit the actual baked camera on every frame,
including animated doors. Review storyboard images and several native-quality
frames before freezing. Pack textures and save the animated scene. Render into a
new directory whose fingerprint records that scene and the rendering code.

Temporal filtering is optional. Inspect both sides of doorways, bright window
frames, reflections, fire, plant edges and disocclusions. For a repair, use a new
run; replacing only visible direct-view frames is insufficient because bounce light,
reflections and filter context can change other frames. The historic Webster patch
required much more evidence than a simple interval replacement.

Build an offline gallery and a synchronized comparison movie using the manifests.
Decode the complete encoded file, verify timing and audio, inspect all segment joins,
and record the accepted hashes. Copy the final model, movie, stills, score and evidence
into `output/final/`. Only then prune intermediates. Keep the input references and
source manifests needed to reproduce the work.
