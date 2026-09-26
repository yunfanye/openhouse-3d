# 349 Walsh Rd, Atherton — headless reconstruction (v2, final)

A from-scratch procedural reconstruction of the modern travertine villa at 349 Walsh Rd, built with `bpy` from the
34 listing photos in `photos/` (MLS ML82027150) and rendered with Cycles (Metal). Final deliverables in `output/`:

* `renders/` — 29 photo-matched stills (2560×1440, 160 spp), `_compare_final.jpg` (photo vs render), `_sheet_final.jpg`
* `film/walsh_promo.mp4` — the 78 s long-take promo film (1080p24, 48 spp + temporal filter), `walsh_promo_contact.jpg`
* `villa_walsh_v2.blend` — the saved scene (1546 objects, ~2.26 M triangles)

```
blender -b --python run.py -- --house walsh --cam all --samples 160 --res 2560x1440       # every view, promo quality
blender -b --python run.py -- --house walsh --cam hero,entry --samples 32 --scale 50       # quick preview
blender -b --python run.py -- --house walsh --norender --save                             # -> output/villa_walsh_v2.blend
blender -b --python run.py -- --house walsh --only exterior,site --cam hero --suffix _t   # build a subset of modules
python3 tools/compare.py --house walsh                                                    # photo-vs-render contact sheet
```

`--cam` accepts a comma list, `all`, `ext` or `int`. `--no-polish` skips the particle / bloom / DoF stage for fast
previews; `HOUSE_HIDE=Name1,Name2` hides objects by name prefix for debugging.

## Cameras (each matched to a listing photo)

| camera | photo | camera | photo |
|---|---|---|---|
| `hero` | 01 front-lawn 3/4 view | `foyer`, `stair` | 05, 09 entry hall + spiral stair |
| `aerial` | 34 | `lounge`, `wine` | 06, 07 sunken lounge, moss + wine wall |
| `front` | 23 street elevation | `theatre` | 08 |
| `entry` | 02 | `living` | 10 onyx fireplace pier |
| `court`, `court_n` | 04, 03 courtyard / pool | `dining`, `kitchen`, `family` | 11, 12, 14 |
| `pool` | 24 through the glass pool wall | `master`, `bath`, `closet` | 17, 18, 19 |
| `drone` | 22 | `office`, `gym`, `guest` | 16, 20, 25 |
| `green`, `terrace` | 15, 21 | `upfamily`, `upbed` | 30, 33 |
| `garden`, `rear` | — | | |

## Files

| path | what |
|---|---|
| `plan.py` | **the plan** (levels, plan constants, `ROOMS` volumes — read its docstring first) |
| `house.py` | cameras + per-camera exposure / f-stop, sky, grass specs, film doors, probe walls, photo pairs |
| `shots.py` | the film: 15-shot cut (`SHOTS`) and the 78 s long take (`TAKE`, ~55 timed keys), title texts |
| `exterior.py` | building envelope: all exterior walls, glass, slabs, roof, wood-slat box, stair lantern, terraces, parapets |
| `site.py` | motor court + reflecting pool, lawns, pool terrace, glass-walled pool + spa, fire trough, courtyard, green wall, outdoor furniture, rear garden + hill |
| `interior_lower.py` | foyer + spiral stair, billiard room + moss wall, sunken lounge (wine wall, TV/fire wall), theatre; shared interior helpers (`wall_trims`, `door_set`, `floater_art`, `fireplace_insert` ...) |
| `interior_main.py` | living (onyx pier), dining, kitchen, family room |
| `interior_suite.py` | master bedroom, onyx bath, closet, office, gym + sauna, guest rooms |
| `interior_upper.py` | upper family room, bedrooms, suite, hall, box room, both roof terraces' furniture |
| `landscape.py` | tree placement (signature oak over the court, lawn oaks, redwood skyline, olives), ground cover, hazed treeline rings + ridge |

## Reading of the site

Coordinates are metres; X = left/right seen from the street, Y = street(−)/rear(+), Z up.

| level | Z | contents |
|---|---|---|
| motor court / foyer | 0.0 | paver + grass-strip court, full-width reflecting pool, double-height entry glass, billiard room; lounge + theatre sunken to −0.9 |
| front lawn | 0.9 | striped lawn right of the house; fire trough below the pool's glass wall |
| living level | 2.6 | living / dining / kitchen / family, master suite + office (rear), pool terrace, courtyard turf + green wall, gym/sauna + guest wing (north arm), rear lawn |
| L1 slab / soffit | 5.9–6.3 | white slab with downlights, perforated parapets, turf terraces |
| upper floor | 6.3–9.3 | travertine west box, cantilevered wood-slat box over the entry, glass bar over the pavilions, bedrooms opening onto the roof dining terrace |
| roof | 9.3–9.85 | thin white slab, gravel, rectangular frame openings |

The plan is inferred from wide-angle listing photos — proportions are approximate and a few adjacencies
(e.g. which rooms face the courtyard) are one plausible reading among several. The interior volumes are the
single source of truth in `plan.py: ROOMS`; every module places finishes and furniture from them.

## The film (`output/film/walsh_promo.mp4`)

```
blender -b --python run.py -- --house walsh --probe --no-polish                       # passability maps of the interior walls
blender -b --python run.py -- --house walsh --film take --film-preview --film-step 3  # Workbench path check + clearance ray-casts
blender -b --python run.py -- --house walsh --norender --save --samples 48 --threshold 0.05
blender -b houses/walsh/output/villa_walsh_v2.blend --python tools/render_scene.py -- prepare --house walsh --shot take \
  --out houses/walsh/output/take.blend
python -m archviz.production --scene houses/walsh/output/take.blend --out houses/walsh/output/runs/take \
  --shot take --temporal       # resumable, fingerprinted; vectors + temporal filter
HOUSE_FILM_DIR="$PWD/houses/walsh/output/runs/take" \
  blender -b --python run.py -- --house walsh --film-encode --film take [--film-music track.mp3]
```

**The long take** (`shots.TAKE`, 78 s, one unbroken camera move, ~55 timed keys with lens / f-stop / exposure keyed
along the path; the look *direction* is interpolated as a unit vector with soft tangents so the view never whips):
drone descent from the street side onto the motor court → the pivot door swings open as the camera arrives
(`house.DOORS`, keyframed) → foyer → billiard room → down the steps into the lounge to the wine wall and the moss-wall
corner, then the camera pulls back out of the lounge and across the billiard room → climbs alongside the spiral stair
onto the dining mezzanine → dining → kitchen loop → through the suite's double doors and the master door → primary
bedroom → out through the north glass → up over the rear lawn and the roof → the courtyard from the NE, down its east
side, west over the pool facing the living wall and the olive → into the open living pavilion past the onyx pier → out
its south face over the front lawn → a slow clockwise sweep that turns back onto the house as it climbs, end card.
The earlier 15-shot cut (`SHOTS`) can be prepared and rendered the same way, one shot name at a time.

Flicker: measured with `--flicker <cam>` + `tools/flicker_stat.py` (8×8-block temporal std): 16 spp 1.25, 48 spp 0.90,
256 spp 0.47 — samples alone plateau at the denoiser's floor. `tools/temporal.py` (motion-compensated 5–7-frame blend
driven by a 1-spp Vector pass with colour rejection) takes 48 spp to 0.26 at ~1 s/frame.

## Realism notes

* Soft goods are rounded lofts (`MB.rbox/rcbox` with `puff`), real pillows (`MB.pillow`) and draped throws (`MB.drape`).
* Facade travertine carries 1.2 × 0.6 m cladding joints chosen per wall from the surface normal; pool water ripples
  only on its top face; the pool is pale plaster under absorbing, faintly scattering water with a volumetric gas
  flame below the glass wall.
* Lawns are hair particles (70k parents × 9 children on the front lawn); trees are branching skeletons carrying
  thousands of alpha-cut leaf-cluster cards, far rings recede with a camera-distance haze; the living wall is
  per-species leaf-card geometry in diagonal swaths.
* The wood box is solid fins over a dark backing, the entry glass is frameless with glass fins, the fascia
  perforations are 3 rows of 58 mm holes, roofs carry gravel ballast inside a parapet lip; the onyx pier is stratified
  (24 layers/m) and the bath onyx a crackle net; every room is lit by recessed slots / downlights / coves.
* Plan quirks: lounge + theatre are sunken (floor −0.9) because a 3 m ceiling at Z 0 collided with the kitchen slab;
  the site ground plane has a hole under them.
