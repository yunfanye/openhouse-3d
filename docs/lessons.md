# Lessons (Blender 5.2, bpy, Cycles/Metal on an M5 Pro) — read before the next house

## Blender 5.x API differences that bit

* Compositor: the scene's compositing tree is a node **group** (`bpy.data.node_groups.new(name, 'CompositorNodeTree')`,
  `scene.compositing_node_group = nt`) whose `NodeGroupOutput` is the result — there is no Composite node. Glare
  settings are sockets (`inputs["Type"].default_value = 'Bloom'`). See `archviz/polish.py: setup_compositor`.
* File Output node: `directory`, `file_name = ""`, `format.media_type = 'IMAGE'`, `file_output_items.new('RGBA', 'v_')`.
* Video output: set `image_settings.media_type = 'VIDEO'` **before** `file_format = 'FFMPEG'`.
* VSE: `strips.new_effect(..., length=)` not `frame_end`; image strips added through the API are NOT scaled to fit —
  set `transform.scale_x/y`; dissolves = keyframed `blend_alpha` with `blend_type = 'ALPHA_OVER'`.
* Actions are layered: fcurves live at `action.layers[0].strips[0].channelbag(action.slots[0]).fcurves` (with a
  fallback to `action.fcurves`). `archviz/film.py` handles both.
* Light ray visibility flags live on the **Object** (`ob.visible_glossy / visible_transmission / visible_camera`),
  not on the Light data. Unset them on fill lights or they show as glowing spheres through water and in glass.
* `bpy.ops.object.shade_auto_smooth` needs an active object (MB.build wraps it in try/except).
* Cycles Vector pass: channels (0, 1) = motion from the previous frame, (2, 3) = motion to the next, same sign;
  needs motion blur OFF. `tools/temporal.py` auto-calibrates the convention.
* Blender's python has no PIL: anything PIL-based runs under system `python3` (`tools/film_tools.py`,
  `archviz/filmkit.py`); keep those modules bpy-free.

## Materials

* Noise banding needs a **Map Range stretch** (0.35..0.65 → 0..1) or colour ramps barely register (`_stretch`).
* Backlit onyx: emission > ~0.6 blows out to white under AgX; 0.5 with stratified layers (24/m) reads as stone.
* Big emissive "light box" panels (emit 25 over m²) flood a room — use ≤ 3, prefer slot lights / coves / downlights,
  and keep `room_light` fill at ≤ 30 % of the fixtures.
* Flat-shaded moss / green walls read as camouflage; dense clump geometry (leaf cards per species in diagonal
  swaths) is what sells them.
* Tile swatch faces that sit exactly on a joint line render as all-mortar — test tiles on a real floor, not a unit box.
* Rug hair fibres read as grey fur at room-camera distance — the boucle shader on a rounded box wins.
* Travertine that looks like wood grain: vein-cut banding needs 1.2 × 0.6 m panel joints chosen per wall from the
  surface normal, and low-contrast veins.
* Pool water: absorb + faint scatter, ripple bump masked to the top face, pale plaster shell; a "caustic web" texture
  on the plaster looked fake and was removed.

## Geometry / realism

* Soft goods: rounded lofts (`MB.rbox/rcbox` with `puff`), real pillows (`MB.pillow`), draped throws (`MB.drape`),
  bevel modifiers. Boxes with sharp edges are the #1 tell.
* Trees: blob canopies never look right. Branching skeletons + thousands of alpha-cut leaf-cluster cards
  (`archviz/trees.py`), LOD by distance, camera-distance haze on the far rings (keep haze ≤ 0.2 or the treeline
  becomes a grey slab at dusk).
* Perforated fascias: round holes (3 rows of 58 mm), not square; slat boxes need solid fins over a dark backing.
* Fire: volumetric gas flame, not cut-out flame cards.
* Sunken rooms: a 3 m ceiling at Z 0 collided with the level above; drop the floor (Walsh lounge −0.9) and cut the
  ground plane under it.

## Rendering / performance (measured)

* GPU OpenImageDenoise (`cycles.denoising_use_gpu = True`) saves ~2 s/frame. Always on.
* Stills: 160–192 spp / 0.02 at 1440p = 30–110 s/frame with particles. Previews: 16–32 spp / 0.05 at 25–50 %.
* Animation: 48 spp / 0.05 + `--light-floor 0.08` + the temporal filter (flicker 0.26) beats 256 spp raw (0.47).
  Clamp indirect 3 darkened cove-lit rooms 11 % — keep 10.
* EEVEE is not a win for glass-heavy scenes with ~60 lights (loses glass → water refraction chains); Workbench for
  path checks only. Details and the full table: `docs/render-performance.md`.
* **Never run two full-scene Cycles renders at once**: swap goes to 15 GB and frames go from 17 s to 5 min.
* One long Blender process over thousands of frames (vector pass, temporal filter) dies OOM — image allocations
  accumulate even after `bpy.data.images.remove`. `archviz.production` chunks rendering and filtering into bounded
  processes; `tools/temporal.py --range` is idempotent.
* Long detached jobs: `subprocess.Popen(start_new_session=True)` (no `setsid` on macOS; `scripts/detach.py`). Plain
  background shell jobs die with the session that launched them, which for automated sessions can be soon.

## Process

* Six parallel writers with **strict file ownership** (see `docs/workflow.md`) worked; shared files
  (`plan.py`, `materials.py`, `parts.py`, `polish.py`, the driver) stay with one integrator.
* Photo-by-photo audit against the renders (`tools/compare.py`) is the review that found the real problems
  (trees, water, flames, perforations, flat lighting); "make it more realistic" without a per-photo list did not.
* Flicker in animation is the denoiser, not sample count: measure with `--flicker <cam>` + `tools/flicker_stat.py`
  before spending samples.

## Second house (1836 Webster St, 2026-09-04) — what changed in the recipe

* **Data-driven walls**: `plan.py` carries `WALLS` (boxes with a kind) and `OPENINGS` (windows / doors / arches with
  the wall plane they sit in); `holes_for(wall)` matches them, `python3 -m houses.webster.plan` checks that every
  opening lands in exactly one wall, and a PIL plan drawing (walls + openings + room labels) caught adjacency
  mistakes before any geometry existed. One module (exterior.py) then builds every wall and every unit from that
  spec; interior modules only add finishes, furniture and lights. Six forks with file ownership built the whole
  house in ~30 min of wall-clock time.
* Inferring a facade that has no photo: use the interior shots looking out (window sizes, sills, the porch parapet
  seen through french doors) plus the side/rear photos for the vocabulary (tile hood, vent dots, parapet caps).
* `clearance_take` cannot see the animated entry door (it never frame_sets), so `Entry_Door ... TIGHT` and
  `LENS BLOCKED (Entry_Door)` around door_t are expected; check the Workbench frames instead.
* Pan flags: a 180° turn needs ~5 s (four keys) to stay under ~50°/s peak; give the direction spline intermediate
  keys every ~40-50° and move the camera on an arc while it turns.
* Passing through a door or an arch always reports TIGHT (< 0.42 m to a jamb); the real hazards are full-height
  objects beside an opening (a fridge next to the kitchen arch) — keep those ≥ 0.9 m from the opening.
* `parts.potted_plant(kind='broad')` reads as floating green discs at camera distance; `kind='olive'` is safer.
* Flat emissive quads for neighbours' windows look painted-on above emit ~0.7; keep them dim.

## Detail pass (Webster, 2026-09-04) — what the "physics + detail" review taught

* Two geometry faults were invisible in code and obvious in a render: a roof slab 3 cm below a ceiling (an orange
  band inside the primary suite) and a tile plate covering a window. `tools/pixel_probe.py` (ray-cast a render
  pixel of a saved .blend -> object / material / point) and `tools/line_probe.py` (every surface crossed along a
  segment) find the culprit in seconds; `HOUSE_BLEND=/tmp/x.blend run.py --save` writes scratch blends for them.
* Plants: `archviz/plants.py` builds real leaves (explicit quad strips + alpha-cut species shaders with veins, waist,
  slits, pinnate leaflets, felted undersides) for potted plants, vase stems, flowering shrubs and hedges. Blob
  "potted_plant" / branch-with-disc-leaves parts read as floating discs at every camera distance; never use them.
  `tools/plant_test.py` renders the whole lineup in 3 s.
* Beds: `parts.bed` now stacks a box base, mattress, folded duvet with side drops, sewn pillows (`MB.pillow_sq`:
  superellipse thickness + piped rim), standing shams, lumbar and a folded throw. `MB.pillow` (superellipsoid) reads
  as marshmallows; `MB.drape` with folds > 1 self-intersects and reads as torn cloth.
* Cycles renders two coplanar overlapping boxes as black squares (z-fighting); frame / muntin / gutter / hinge
  helpers must not share faces with the wall or leaf they sit on - offset by 1-2 mm.
* An enclosed shower stall behind plain glass boxes renders black with caustics off: use a local glass material
  that mixes Glass with Transparent on `Is Shadow Ray` (Light Path), and put a small point light inside the stall.
* Parapet / roof walls listed in `plan.WALLS` must be clipped to the footprint of the storey above them: a
  single-storey parapet under a wing runs straight through the room above (found by a line probe, not by eye).
* After any interrupted editing session, check that every module still parses (`python3 -c "import ast..."`) and
  run a `--norender` build before continuing.
* Matching a render to a photo: solve the camera from two known widths (facade edges) and one vertical drop
  (sidewalk edge), render, then blend the two at 50 % and compare gradient-peak rows along a few columns
  (window head / sill / eave). Residual rows convert to metres with the pixel scale at that wall's distance;
  fix the plan constants (sill heights, ridge, wing width), not the camera. The Webster hero landed within ~0.1 m.

## Third house (13695 Stanford Dr, 2026-09-23) — photo solving and a suburban kit

* **Solve the facade, don't eyeball it**: `tools/solve_scene.py` fits several listing photos and ~30 named plan
  dimensions at once (level camera + lens shift, because listing photos are perspective-corrected). Two street
  photos plus one aerial pinned window centres to ~5 cm and exposed a wrong assumption (the brick bay is recessed
  0.5 m, the floor-to-floor is 2.84 m). Unknowns with large standard errors are not determined: keep plan values.
* Aerials use the `free` model; a keystone-corrected drone photo of a single wall is planar-degenerate (camera
  distance, lens and the editor's aspect change trade off) — match it by eye and say so in the gallery note.
* Back-projecting a trunk through one grazing ground-level camera is unreliable; overlay renders instead.
* Siding as geometry (wedge courses, `archviz.cladding`) reads correctly in raking golden-hour light where a
  texture does not; roof slopes built in their own plane frame keep object-space shingles coursing on every slope.
* A deepened listing-photo sky must only be seen by camera rays (Light Path), or shaded walls turn blue.
* `film._split_faces` lost material indices when slots were appended after `to_mesh` (a glass slider panel
  rendered as white vinyl); slots are now assigned first.
* Parallel interior workers with strict file ownership (main floor / upper floor / cameras per floor)
  worked again; route constraints for the film (clear corridors, open blinds) should be sent to them early.

## Stanford review round (2026-09-24) — what the reviewer's "the geometry is wrong" actually was

* **Camera first, and never from an automated edge fit.** The first pass fitted interior cameras by chamfer-matching
  rendered edges to photo edges; many landed 0.3–0.6 m too high with 10–14 mm lenses and made correct rooms look wrong
  (and hid real errors). Hand-read points and **lines** (a pixel on the projection of a known edge: wall/ceiling
  junctions, jambs, rakes, curbs) on architecture only, solved jointly across photos with the uncertain plan dimensions
  as unknowns (`tools/intcam_solve.py`, `tools/joint_solve_lines.py`), gave 0.3–3 px and moved the stair 1 m, both
  ceilings, the bay front and the right wall.
* A facade-only fit of a level + shift camera cannot separate camera x from lens shift; one or two ground lines running
  away from the camera (driveway joints) pin the vanishing point without trusting absolute ground coordinates.
* A single photo pins ratios, not heights: a ceiling height and a vertical aspect edit trade off exactly. A door leaf
  (80 in) or an exterior anchor in the same solve is what separates them.
* Check a reviewer's "extra window" against every photo: it was the real kitchen window, hidden by a shrub in one view.
  Several "wrong openings" were trim style (vinyl J-channel vs flat casings) and muntin thickness, not position.
* Per-photo hooks (`before_render`) leak state between stills unless every module restores defaults from build-time
  values: a hook that stored its lamps' "rest" energy after another hook dimmed them rendered every later interior 4×
  too dark. The dispatcher now resets every light to `ob['_e0']` first; test by rendering cameras in two orders and diffing.
* `materials.build_materials()` pre-defines common keys ('carpet', 'fabric_white'): `M.setdefault` in a house module
  silently keeps the library version (white carpet everywhere). Override explicitly.
* Principled sheen ≥ 0.5 on textiles washes rugs and sofas to white at listing-camera grazing angles; ≤ 0.2 reads right.
* Flat photographed decor (paintings, prints, curtains) is most faithful as a texture rectified from the photo itself
  (`archviz/phototex.py`); record every photo quad, and remember the result carries the photo's rights.
* Parallel agents with strict file ownership + an append-only coordination board worked for seven agents; shared plan
  constants need one owner who decides from the pooled evidence, and every module must read them symbolically.

## Matching another reconstruction's camera route (Stanford, 2026-09-24)

* Two reconstructions of one house do not share a coordinate frame or room sizes, so one transform misplaces most
  interior keys. Place each key by what it frames in the same room (the entry door, each stair flight, the bed wall,
  the slider), keep the other take's times, lenses, f-stop and interpolation settings, and compare low-resolution
  storyboards at every key and between keys against frames decoded from the other film.
* Compare per-second peak pan and speed of both takes through the same `film.take_curves`; a matched route should
  follow the other profile closely. A shorter or longer room here shows up as a faster walk or a whip turn.
* Six clearance rays miss plants and door casings. The nearest distance to a BVH of the static scene per key interval
  (animated leaves excluded) found landing plants 0.07 m from the path, a passage casing at 0.02 m and a hall
  dracaena in the lens. `camera_audit` now also reports swept path crossings between consecutive frames.
* Door leaves hung for the photographs (open into halls) block a walk-through; shut them as documented film staging.
