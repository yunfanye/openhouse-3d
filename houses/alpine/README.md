# 805 North Alpine Drive — Beverly Hills (experimental)

**Status: experimental, production paused.** No accepted final-quality film exists
for this house. Use it as a source example for a large formal estate; start new
work from `houses/_template`, `archviz.production` and the root workflow guides.
Do not treat partial local frames or review drafts as a delivery.

This package reconstructs the visible architecture and principal furnished spaces
from the 33 listing photographs in `photos/`. Dimensions and room connections are
inferred. It is a photographic interpretation for architectural visualization, not
a measured survey or a complete construction model.

## Camera route

`shots.py` holds one continuous 64-second take (revision 3): a quick descent from a
centred pool-side aerial, a low skim across the full length of the pool, entry
through the central French doors, then the garden salon, kitchen, dining room,
grand stair hall, formal living room, oak library and back through the salon to
the rose garden, ending with a rising view across the estate. The garden and reveal
keys from 43 s onward are unchanged from revision 2. The main house, rear gallery
and guest-house exterior form one connected scene.

## Build and render

```sh
blender -b --python-exit-code 1 --python run.py -- --house alpine --norender --save
blender -b houses/alpine/output/alpine.blend --python-exit-code 1 \
  --python houses/alpine/film_scene.py -- prepare
blender -b houses/alpine/output/alpine_cinematic.blend --python-exit-code 1 \
  --python houses/alpine/film_scene.py -- audit
blender -b houses/alpine/output/alpine_cinematic.blend --python-exit-code 1 \
  --python houses/alpine/film_scene.py -- storyboard
blender -b houses/alpine/output/alpine_cinematic.blend --python-exit-code 1 \
  --python houses/alpine/film_scene.py -- frames 1 1536
python houses/alpine/promo.py    # title cards and the synthesized score
python houses/alpine/encode.py   # validate frames, encode 1080p24 with titles and score
```

`film_scene.py` is tuned for Apple Metal (generic kernels, MetalRT off). On other
platforms, render the prepared scene with `python -m archviz.production` instead
(see [the production guide](../../docs/production.md)).

The planned delivery is a 1920 × 1080, 24 fps film with titles and an original
instrumental score, a clean title-free version, the packed animated
`alpine_cinematic.blend`, selected 2560 × 1440 stills and a camera audit.

## Reconstruction notes

- Photos 00–02, 12, 18–19 and 32 establish the paired colonnades, five dormers,
  shutters, brick terraces, pool, garden and motor court.
- Photos 03 and 13 establish the tall central hall, turned balusters, flared stair
  and rooflights.
- Photos 04–11 establish the principal room materials, furniture arrangement
  vocabulary and kitchen cabinetry.
- Photos 14–17 inform the furnished upstairs rooms; photos 28–31 inform the rear
  buildings.
- Exact dimensions, interior adjacency, unseen construction, garden lighting and
  surrounding context are interpretive. The camera route uses real openings in the
  reconstruction.
- Artwork, the two rug textures (`assets/rug_*.png`, drawn by `textiles.py` with
  fixed seeds) and the instrumental score (`promo.py`) were created for this project.
  The listing photographs remain unchanged in `photos/`.

Listing reference: https://www.zillow.com/homedetails/805-N-Alpine-Dr-Beverly-Hills-CA-90210/20519812_zpid/
