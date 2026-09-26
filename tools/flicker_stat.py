"""Temporal-noise metric for a folder of identical-camera frames: mean per-pixel std over time (8-bit sRGB units).
  python3 tools/flicker_stat.py houses/<name>/output/flicker/<tag> [...]   (frames from run.py --flicker <cam>)"""
import sys, os, numpy as np
from PIL import Image
for d in sys.argv[1:]:
    fs = sorted(f for f in os.listdir(d) if f.endswith(".png"))
    if len(fs) < 2:
        continue
    A = np.stack([np.asarray(Image.open(os.path.join(d, f)).convert("L"), dtype=np.float32) for f in fs])
    sd = A.std(axis=0)
    # flicker = temporal std; report mean, the 95th percentile (worst regions) and a low-frequency version
    # (8x8 block means -> catches the large-scale "breathing" the eye sees, not just grain)
    H, W = sd.shape
    blk = A[:, :H // 8 * 8, :W // 8 * 8].reshape(len(fs), H // 8, 8, W // 8, 8).mean(axis=(2, 4))
    lf = blk.std(axis=0)
    print(f"{os.path.basename(d):48s} n={len(fs):2d}  std mean {sd.mean():5.2f}  p95 {np.percentile(sd, 95):5.2f}   8x8-block std mean {lf.mean():5.2f}  p95 {np.percentile(lf, 95):5.2f}")
