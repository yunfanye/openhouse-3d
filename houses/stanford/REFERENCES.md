# Reference evidence for 13695 Stanford Dr, Carmel IN 46074

Source listing: <https://www.zillow.com/homedetails/13695-Stanford-Dr-Carmel-IN-46074/99144200_zpid/>
(the Zillow page itself refuses automated access; the facts below come from the MLS listing mirror at
chain-realty.com, MLS 22119165). The 32 photographs in `photos/` are the listing photographs (MIBOR BLC
watermark). They are tracked for reference only; see [PHOTO_REMOVAL.md](../../PHOTO_REMOVAL.md).

This file was rewritten for the second review round (2026-09-24). The first review found real geometry errors
(rear patio, front roof, great-room / slider glazing, pond and site) and, above all, photo cameras that did not match
their photographs. Every camera has since been solved from hand-read correspondences; the plan was corrected wherever
two or more photographs agreed. What each number rests on is listed below, as are the open conflicts.

## Listing facts used as constraints

| Fact | Value | Used for |
| --- | --- | --- |
| Beds / baths | 4 bed, 2 full + 1 half bath | upper-floor room program, powder room on the main floor |
| Above-grade area | 2,345 sq ft (218 m²) | plausibility check of the 12.5 × 10.3 m block + garage wrap |
| Year / builder | 2005, Ryland, Stanford Park | builder-grade details (vinyl single-hung windows, colonial six-panel steel door, 6'8" doors) |
| Garage | 2 car, 468 sq ft, finished | garage bay, 16 ft door |
| Rooms (main) | Living 13×11, Dining 17×9, Kitchen 11×12, Great 17×19 | room extents (the 13 ft living room agrees with the solved stair position) |
| Rooms (upper) | Primary 15×19, Bed 14×14, 12×13, 13×11, Laundry 7×9 | upper layout |
| Fireplace | 1, great room | the gas fireplace chase on the great room's west wall |
| Lot | 0.15 acre, pond view, on the walking path | rear yard depth, the common path and the pond |

## Coordinate frame and scale

Metres; X left→right seen from the street, Y street→rear, Z up. X = 0 is the upper storey's left face; Y = 0 is the
garage front; Z = 0 the finished main floor. Scale comes from standard units the photographs show: the 16 ft
garage door, the 36 × 80 in entry leaf, 6'8" interior doors, 30" range / 24" dishwasher / 36" refrigerator, 12" floor
tiles, the neighbours' garage doors in the aerials. These are stated assumptions, not measurements.

## How the cameras were solved

Listing photos are perspective-corrected, so almost every camera is **level with a lens shift**; photo 15 (free
pitch −15.7°, roll −1.1°), the drone views 30–32 (free pitch) and the keystone-edited drone photo 27 (pinhole +
vertical aspect + horizontal shear, rendered through `run.py`'s `CAM_ASPECT` / `CAM_SHEAR` / `CAM_OVERSCAN`) are the
exceptions. Correspondences were read at 1–2 px with `tools/photo_grid.py` or as sub-pixel edge fits; **architecture
only** (walls, ceiling and floor lines, jambs, casings, eaves, rakes, ridges, curbs), never furniture. Line
constraints (a pixel lies on the projection of a known 3D edge) carry most interior solves. Every solve was checked
with `tools/overlay.py` (render edges over the photo) and a 50 % blend.

| Tool | Use |
| --- | --- |
| `tools/joint_solve_lines.py` + `cams/ext_facade_solve.py`, `ext_p27_solve.py`, `ext_p28_solve.py` | exterior joint solve of 01, 02, 03, 25, 30 (+ 31 as a constraint) with plan unknowns and line constraints; 27 and 28 |
| `tools/intcam_solve.py` + `cams/int_*.json` | interior cameras: points + lines, several photos jointly with plan unknowns (`int_great.json` = 08–14, `int_living.json` = 04–06) |
| `tools/solve_scene.py` + `cams/aerials.json`, `cams/p26.json` | 31 + 32 jointly (horizon-pinned), 26 |
| `tools/backproject.py`, `tools/orthophoto.py` | pixel → ground / water plane; rectified aerial with a metre grid (shoreline, path, trees, patio tracing) |

| Photo | Camera | rms (px) | Notes |
| --- | --- | --- | --- |
| 01 hero | level, 24.8 mm | 2.1 | the driveway's joint / edge lines pin the Y vanishing point a facade-only fit cannot (the old hero stood 2 m too far −X) |
| 02 front | level, 28.1 mm | 3.1 | a cloudier day: sun high behind the house |
| 03 porch | level + roll 0.2°, 25.5 mm | 1.6 | old camera had a fixed 22 mm lens and was badly framed |
| 04 / 05 / 06 | level, 23.1 / 15.9 / 17.1 mm | 1.3 / 0.9 / 1.0 | joint; door wall + entry leaf anchor the scale |
| 07 | level, 13.6 mm | 0.8 | in the powder-room doorway |
| 08–14 | level, 17–24 mm (10: 32 mm crop) | 1.4–3.3 | one joint solve (walls, chase, fan, kitchen features); 11 held north of the pier and with the island just off-frame, as the photo shows |
| 15 | free pitch + roll, 17.1 mm | 1.5 far / 5.4 all | the near balustrade is ~0.3 m off; kept on the far-field fit |
| 16 / 17 | level, 16.4 / 16.3 mm | 1.0 / 1.2 | joint on the tray ceiling and rear windows |
| 18–23 | level, 14–16.6 mm | 0.3–1.4 | on the 5.20 m ceiling; 19's scale is weak (fan 42 px off) |
| 24 | level, 16.1 mm | 1.1 | back-left corner, ceiling, door track, slab joints |
| 25 rear | level, 27.9 mm | 0.9 | |
| 26 | level, 17.3 mm | 1–4 far / ~15 near patio | fence posts, far shore, riprap, far-row houses |
| 27 | general + aspect 0.888 + shear 0.085 | ~3 wall / 5.9 incl. ground | keystone + aspect-edited drone photo; its own sun (the house's shadow edge on the lawn at y 17.0) |
| 28 | level, 29.7 mm | 2.1 | the rear wall alone is planar-degenerate; lens from a ground-feature bundle adjustment of 25–28 |
| 29 | level, 17.3 mm (estimated) | – | path vanishing point + width, tied to a trunk also seen in 26; lens assumed = 26's |
| 30 | free (pitch −22.5°), 24.8 mm | 3.9 | |
| 31 / 32 | free, 67.5 / 22.3 mm | 2.3 / 1.9 | joint; the old 32 camera was ~35 % too wide, 31 was 13 m too close with a shorter lens |

All interior cameras now stand 0.85–1.15 m above their floor with 14–24 mm lenses (the old automated fits stood
1.3–1.6 m high with 10.5–14.6 mm lenses, which made correct geometry look wrong and hid real errors).

## Plan corrections (this round)

| Quantity | Evidence | Before | Now |
| --- | --- | --- | --- |
| Main roof pitch / ridge | joint exterior solve 0.523 ± 0.006; ridge 8.19 (aerials alone 8.26 ± 0.08) | 7/12, ridge 8.55 | 6.3/12, ridge 8.19; roof top at the wall line 5.525 |
| Right cross gable | ridge meets the main ridge (30, 31); corner x 5.97 | pitch 0.884, 5.9..12.3 | pitch 0.817 (the reviewer's "too tall right gable") |
| Upper front faces / recess | free-depth solves of 01/02/03/25/30: y 1.22 ± 0.03 / 1.60 ± 0.05 | 1.50 / 2.10 | `YB0_UP` 1.22 (overhangs the porch door wall by 0.28 m), `CEN` (3.245, 5.97, 1.60) |
| First-floor eave | gutter top 2.48–2.51 (01, 03) | soffit 2.66 | soffit 2.28, shed 2.48 |
| Brick bay front | exterior 0.86 ± 0.07 (03 shows its west return); interior 04/06 window wall 1.15 ± 0.06 inner | 0.50 | `Y_BAY` 0.86, bay x 8.70 |
| Right wall | interior 04/05/06 east inner face 12.34–12.37; exterior 12.5 ± 0.15 | 12.30 | `XB1` 12.50 |
| Stair (U) | 04+05+06 joint: living depth 3.72 ± 0.10 → 4.87 ± 0.12; 06 alone 4.86; upper plan from 19–21; newel triangulated from 05+06 (9.80, 4.88) | ST_Y0 3.85, ST_X0 9.57 | ST_Y0 4.87 (+1.02 m), ST_X0 9.76 |
| Main ceiling | every main-floor solve 2.42–2.46 | 2.50 | `Z_C1` 2.44 (8'0") |
| Upper ceiling | level solves on exterior anchors: 21 → 5.20 ± 0.03, 16+17 soffit 5.18 ± 0.02; 6'8" doors then read standard | 5.46 | `Z_C2` 5.20; `Z_PLATE` 5.46 stays the exterior wall top |
| Kitchen | joint 12+13+14 with 16 unknowns (1.8/1.8/2.8 px) | fridge wall 7.85, island 1.18 × 1.28 | fridge wall 7.28–7.36, pier x 8.46–8.94, island top 0.9 × 1.2 m (the reviewer was right: it was too big) |
| Fireplace chase | 09 + 10 + 14 | y 7.91–9.79, 0.45 deep | y 8.09–9.95, 0.545 deep |
| Foyer / core | 04 (same plane as the entry leaf, camera-independent) | foyer west wall on the garage wall x 6.0 | foyer west wall x 7.22 with a coat closet behind the porch brick; powder room 1.07 m wide |
| Openings | outer frames minus J-channel in 01/02/03/25/27/28 | | all re-measured; 6/6 grilles everywhere, 3 × 5 slider grilles, garage door 2.08 tall at slab −0.25, the garage-entry door hole |
| Street | 31+32 joint | sidewalk −5.9..−7.1 | sidewalk −8.12..−9.60, gutter −10.90, far curb −19.57 |

The rear openings were **already right** to within ~5 px in 25 (slider, great-room pair, the three upper windows).
The small window left of the slider that the reviewer read as "extra" is the kitchen sink window: it is clearly
visible in 27 and 28 and hidden behind the shrub in 25 (the model's shrub now hides it too). The perceived rear
mismatch came from the camera, wide flat casings (the house has narrow vinyl frames + J-channel), chunky slider
muntins and the patio.

## Site

- Patio: traced in 27 (36 edge + 25 bed points) through a bundle adjustment of 25–28 (6–7 px per photo); x 1.9..10.7,
  5.5 m deep, broad grill lobe, concave waist, rounded table lobe; fan + circle-kit pavers; 0.5–0.85 m river-rock bed
  with black edging; staging (table, stools, grill, lights, hook, stones) from the same adjustment. The ends hidden by
  the corner shrubs are inferred.
- Front tree: trunk (10.16, −4.48) where the 01 and 02 trunk rays cross (30's rock ring agrees to 0.7 m); the crown is a
  measured envelope fitted to the tree masks of 01/02/30/31 (IoU 0.91 / 0.88 / 0.83 / 0.80).
- Fence 1.2 m on x 14.3 from y 10.85 to the corner at 30.5 (25, 31). The reviewer's "utility pedestal" is two grey
  telecom posts at the front right lot line by the sidewalk (30), modelled there.
- Neighbours rebuilt as measured massing from 30/31 (garage bumps, front gables, porch, dish, hoop, cars on the drives).
- Pond traced in 31 and 32 (they agree to ~1 m): ~110 × 84 m with the east lobe and NE corner, riprap swales, boulder
  groups and an outlet; fountain at (−14.1, 92.1) with a 4.8 m jet. The south shore west of x −1 is under trees in both
  aerials (inferred). ~110 common-area trees placed from their trunk rays / crowns (26, 29, 31); the yellow 'Sunburst'
  locust is in the second right neighbour's back yard (30/31/32). The loop path traced from 31/32. The far row of
  houses from 32's rear walls; streets round the pond block and the woodland traced from 32; the subdivision beyond it
  (~17.6 k instanced houses, gentle terrain) is an inferred grid.

## Materials and light

Colours were calibrated by patch medians, photo vs render through the same camera (most within ±10 %). Siding is a
lighter blue-grey (the old one was 1.4–2× too dark), shingles a warm medium grey, brick varied with lighter mortar,
interior walls light grey-blue downstairs and per-room paints upstairs (the old renders washed walls out by up to
1.8×). Each exterior photo has its own sun read from its shadows (`exterior.before_render`): the rear photos were taken at
two times (26/27: the gutter's shadow edge at y 17.0; 25/28: at 15.9). Each exterior photo also has its own sky
(camera rays only), graded from the photo's own sky pixels. Interior photos have per-room fills without the old strong
ceiling panels; ceilings are a warm knockdown within ~3 % of the photos, and the carpet has a visible pile. Listing photos are HDR-processed and warmer than the renders;
the remaining differences are mostly white balance and tone mapping.

## Staging and presentation choices (not evidence)

- Furniture, rugs, art, plants, linens and window treatments are reconstructed after the listing photos and placed by
  back-projecting their photo pixels through the solved cameras; sizes and hidden shapes are inferred. Where the
  photographer moved furniture between shots the render follows each photo (dining chairs in 12/13, the sectional's
  chaise in 08; `before_render` hooks). Door states follow each photo (powder door, primary bath door, the garage door
  up in 24).
- **Photo-rectified textures.** Flat photographed items are reproduced with textures rectified from the listing photos
  themselves (`archviz/phototex.py`): the paintings and prints (04, 05, 06, 08, 09, 10, 14, 15, 16, 17, 19, 20, 21), the
  crewel embroideries, pillow and comforter fabrics, rugs, curtains, towels and soap labels upstairs. The photo and the
  pixel quad of every texture are listed in `interior_front.PHOTO_TEX`, `ig_staging.PHOTO_TEX` and
  `up_staging.PHOTO_TEX`. Those textures carry the photographs' rights (see ASSET_LICENSES.md).
- Photo comparison stills use per-photo suns and skies; the film is lit at golden hour with the CC0 Poly Haven sky
  `kloppenheim_06_puresky` (`assets/sources.json`).

## Open conflicts (documented, not resolved)

- Upper window heads read 0.1–0.15 m lower from inside (16, 19, 20, 21) than the facade solve puts them. Both fit their
  own photos; a ~10 % vertical stretch of the upper interior photos would explain it as well as a lower ceiling does.
  The levels were frozen; the exterior values are kept.
- Photo 20 shows bed20's front wall as one plane where the facade evidence needs the recess jog; the jog is kept.
- Photo 11 frames correctly only with the camera held north of the pier (3.3 px instead of 2.5); letting the island move 0.13 m east fits 2.7 px but disturbs 12–14, so the island stays as the 12/13/14 solve built it.
- Photo 15's near balustrade renders ~40–65 px high with the far-field camera.
- Upper-floor dimensions not photographed (dressing hall, linen closet, laundry, bed19 closet) are inferred.

## The film

The 66-second golden-hour take was re-routed for the corrected model and re-rendered (`output/final_v2/`; the
previous film in `output/final/` shows the model before the review). `shots.py` now:

- opens at the fountain's triangulated position (-14.1, 92.1) and flies over the re-traced pond to the rear;
- orbits the sunlit left side instead of the right (the refitted front tree fills the right-hand approach) and lands
  at photo 01's viewpoint before walking up the drive;
- turns into the hall north of the foyer's moved west wall (the coat closet), follows the stair 1 m further back,
  and circles the relaid kitchen island (south aisle, east end, north aisle) to the patio slider.

Film-only staging, so that one continuous camera has a clear corridor (`film_scene.staging()`; the photo stills keep
the photographed arrangement): the dining table's two end chairs are pulled away, the corn plant beside the slider
stands 0.3 m further from the opening, and the powder-room door is shut as in photos 05/06. The slider's operable
(-X, inner-track) panel slides open behind the fixed panel. Route audit: no lens obstructions, peak speed 8.5 m/s
(aerial), peak pan 59 deg/s, nearest surfaces 0.24-0.31 m (door jambs). Captions, titles and the music edit keep
their timings. The comparison movie (`comparison_video_timeline.json`) switches photos on the new route's timings and
pairs the film with the review-round gallery (`output/review2/gallery`).

## Music

"Wonders of the Earth" by Grand_Project (composer Roman Dudchyk), Pixabay,
<https://pixabay.com/music/adventure-wonders-of-the-earth-550792/>, free for use under the
[Pixabay Content License](https://pixabay.com/service/license-summary/). The track is registered with Content ID
by its author: an upload to YouTube may show a claim that the uploader can clear with the Pixabay license.
The edit (`promo.py`) keeps 0–55.6 s of the track and joins its final cadence (141.2 s–end) on a downbeat.
The downloaded MP3 is not committed (`output/music/`, ignored); its SHA-256 is recorded in the delivery inventory.
