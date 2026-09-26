> Measured 2026-09-01 on the v1 Walsh scene with the old `build_villa.py` driver (its `--engine/--denoise-gpu/--eevee-fast`
> flags no longer exist). The conclusions are baked into `run.py` (GPU denoise on, adaptive sampling) and
> `archviz.production` (see production.md for current settings). Kept for the numbers.

# Faster video rendering — measurements on this scene

All numbers: Apple M5 Pro (20-core GPU, Metal), Blender 5.2.1, this villa scene
(~160 objects, ~60 lights, lots of glass + pool water), fly-through frames 400–423
(24 frames, hero/lawn view), seconds per frame **including** per-frame overhead.

| engine / settings | 1080p s/frame | 1177-frame video | look |
|---|---|---|---|
| Cycles 32 spp, thr 0.02, **CPU** OIDN *(what the first video used)* | 6.9 | 2 h 15 m | reference |
| Cycles 32 spp, thr 0.02, **GPU** OIDN | 4.6 | 1 h 30 m | identical |
| Cycles 64 spp cap, 2 s time limit, GPU OIDN | 2.6 | 51 m | identical |
| **Cycles 16 spp, thr 0.05, GPU OIDN** ← new default | **2.55** | **50 m** | identical at 100 % crop |
| …same at 720p | 1.35 | 27 m | softer |
| …same at 1440p | 5.0 | 1 h 38 m | sharper |
| …same, transmission/transparent bounces 8/12 | 2.75 | — | no gain (bounces aren't the bottleneck) |
| EEVEE 64 TAA, raytracing, shadows | 6.6 | 2 h 10 m | flat GI, salmon cast, pool wrong |
| EEVEE 32 TAA, cheap raytrace/shadow | 3.3 | 1 h 05 m | same |
| EEVEE 16 TAA, cheap raytrace/shadow | 1.8 | 35 m | same, slightly softer AA |
| Workbench (solid shading, 8× AA) | 0.2 | 4 m | flat preview |

## What actually mattered

1. **OpenImageDenoise was running on the CPU and cost ~2 s of every frame** — about
   45 % of the original frame time. `scene.cycles.denoising_use_gpu = True` makes it
   essentially free on Apple Silicon. This is the single biggest win and costs nothing.
2. **16 spp with adaptive threshold 0.05 is enough** for a denoised animation of a
   scene lit mostly by area/emissive lights. 32 spp / 0.02 doubled the time for no
   visible gain. (Prefer a fixed sample count over `time_limit` for animation — it
   keeps the noise level, and therefore the denoiser's behaviour, consistent frame to frame.)
3. **Resolution is the next lever** (cost is ~linear in pixels): 720p halves the time again.
4. Bounce limits, persistent data, and the chunked launcher overhead (~10 s per 100
   frames) are all second-order here.

Net: the same 49 s / 1080p video that took **2 h 15 m** renders in **~50 min** with
identical output — a 2.7× speed-up from two settings.

## EEVEE — when it is (and isn't) worth it

EEVEE (the "EEVEE Next" rasteriser in 4.2+/5.x) was **not** the 10× win people
expect on this scene:

- Its per-sample cost is high with screen-space raytracing + virtual shadow maps +
  ~60 lights; at 64 TAA samples it is as slow as Cycles at 32 spp. It only pulls
  ahead at 16 samples (1.8 s/frame, ~1.4× faster than tuned Cycles).
- Fidelity gaps that matter for *this* house: no real GI (soffits/undersides pick up
  un-occluded sky light → the salmon cast), screen-space refraction can't chain
  glass wall → water → pool shell (the signature glass pool becomes a white/aqua slab),
  no volume absorption in thin slabs, translucent foliage shader unsupported,
  and the shadow pool overflowed until shadows were disabled on the accent lights.
- Closing the gap would need baked light probes (irradiance volume + reflection
  cubemaps via `bpy.ops.object.lightprobe_cache_bake`), a faked water material, and
  re-balanced lights — realistically an afternoon of tuning to reach ~80 % of the
  Cycles look, for a 1.4× gain over tuned Cycles. Not worth it for a final.

Where EEVEE/Workbench *do* pay off: designing and checking the camera path.
A Workbench pass rendered the whole 1177-frame path in ~4 min and a fast EEVEE
preview took ~35 min. Today the Workbench path check is
`run.py -- --house <name> --film <shot> --film-preview`.

## Recommendations for future videos

- Cycles with GPU denoising and adaptive sampling (16–48 spp, threshold 0.05) at 1080p
  is the baseline; set samples with `run.py --samples/--threshold` before `--save`.
- Workflow: block the path with Workbench (minutes) → check a 2-second Cycles test clip
  for denoiser flicker (`run.py --flicker`, `tools/flicker_stat.py`) → launch the
  resumable chunked render with `python -m archviz.production`.
- Want it faster still? In order of payoff: 720p (2×), shorter/faster path (fewer
  frames), fewer lights (merge the 40 accent spots into a few emissive strips),
  rendering only every 2nd frame at 12 fps for previews.
- Want it prettier? 1440p costs 2× (~1 h 40 m); 24 spp / thr 0.03 is a cheap safety
  margin if a scene has darker interiors than this one; add Cycles motion blur only
  for fast camera moves (it roughly doubles cost).
- Keep the PNG-frames-then-encode pipeline: it's resumable and re-encodable
  (`run.py --film-encode`, or the house's `promo.py`).
