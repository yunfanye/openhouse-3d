"""Motion-compensated temporal filter for rendered image sequences (kills sampling flicker).

For every frame t the neighbours t±1..t±R are warped onto t with the Cycles Vector pass (per-pixel screen motion,
written as v_####.exr by archviz/film.py) and averaged with the frame; neighbours whose warped colour disagrees with
the frame beyond a noise-scaled tolerance are rejected per pixel (no ghosting at disocclusions, reflections,
refractions, the fire).  With animated seeds the residual noise is independent frame to frame, so a 5-frame window
cuts the temporal std roughly in half - the same stability as ~4x the samples, at no render cost.

  blender -b --python tools/temporal.py -- houses/<name>/output/film/frames/<shot> [...] [--radius 2] [--tol 6] [--out-suffix _tf]

Writes <dir><suffix>/f_####.png (same names) - the assembler (run.py --film-encode) prefers the "_tf" set unless --film-raw.
"""
import os, sys, glob, time, gc
import numpy as np
import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
dirs, radius, tol, suffix, lowpass, frange = [], 2, 6.0, "_tf", 7, None
i = 0
while i < len(argv):
    a = argv[i]
    if a == "--radius":
        radius = int(argv[i + 1]); i += 2
    elif a == "--tol":
        tol = float(argv[i + 1]); i += 2
    elif a == "--out-suffix":
        suffix = argv[i + 1]; i += 2
    elif a == "--lowpass":
        lowpass = int(argv[i + 1]); i += 2          # blend only frequencies below this kernel size (0 = full band)
    elif a == "--range":
        frange = tuple(int(v) for v in argv[i + 1].split("-")); i += 2   # only write frames a..b (chunked runs: bounds memory)
    else:
        dirs.append(a); i += 1


def load_rgb(path):
    """8-bit PNG -> float32 HxWx3 in 0..255 (display-referred; no colour management applied)."""
    img = bpy.data.images.load(path)
    img.colorspace_settings.name = 'Non-Color'
    w, h = img.size
    buf = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(buf)
    bpy.data.images.remove(img)
    a = buf.reshape(h, w, 4)[::-1, :, :3] * 255.0            # Blender stores bottom-up
    return a


def load_vec(path):
    img = bpy.data.images.load(path)
    img.colorspace_settings.name = 'Non-Color'
    w, h = img.size
    buf = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(buf)
    bpy.data.images.remove(img)
    return buf.reshape(h, w, 4)[::-1]                       # (prev_x, prev_y, next_x, next_y), pixels, y up


def save_rgb(path, a):
    h, w, _ = a.shape
    img = bpy.data.images.new("tf_out", w, h, alpha=False, float_buffer=False)
    img.colorspace_settings.name = 'Non-Color'
    rgba = np.ones((h, w, 4), dtype=np.float32)
    rgba[:, :, :3] = np.clip(a[::-1], 0, 255) / 255.0
    img.pixels.foreach_set(rgba.ravel())
    img.filepath_raw = path
    img.file_format = 'PNG'
    img.save()
    bpy.data.images.remove(img)


def warp(src, dx, dy):
    """Bilinear sample of src (HxWxC) at (x+dx, y+dy); dy is in image rows (y down)."""
    h, w = dx.shape
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    x = np.clip(xs + dx, 0, w - 1.001); y = np.clip(ys + dy, 0, h - 1.001)
    x0 = np.floor(x).astype(np.int32); y0 = np.floor(y).astype(np.int32)
    fx = (x - x0)[..., None]; fy = (y - y0)[..., None]
    c00 = src[y0, x0]; c10 = src[y0, x0 + 1]; c01 = src[y0 + 1, x0]; c11 = src[y0 + 1, x0 + 1]
    return (c00 * (1 - fx) + c10 * fx) * (1 - fy) + (c01 * (1 - fx) + c11 * fx) * fy


def boxn(a, n):
    """n x n box blur (separable, edge-padded)."""
    if n <= 1:
        return a
    r = n // 2
    p = np.pad(a, ((r, r), (0, 0), (0, 0)), mode='edge')
    c = np.cumsum(p, axis=0); c = np.concatenate([np.zeros_like(c[:1]), c])
    a = (c[n:] - c[:-n]) / n
    p = np.pad(a, ((0, 0), (r, r), (0, 0)), mode='edge')
    c = np.cumsum(p, axis=1); c = np.concatenate([np.zeros_like(c[:, :1]), c], axis=1)
    return (c[:, n:] - c[:, :-n]) / n


def box3(a):
    return boxn(a, 3)


def calibrate(src, vec, dst, label):
    """Pick the vector convention (channel pair / signs) that maps pixels of `src` onto `dst` with minimum error."""
    best = None
    for pair in ((0, 1), (2, 3)):
        for sgn in (1.0, -1.0):
            for flip_y in (1.0, -1.0):
                dx = sgn * vec[..., pair[0]]; dy = sgn * flip_y * vec[..., pair[1]]
                err = np.abs(warp(dst, dx, dy) - src).mean()
                if best is None or err < best[0]:
                    best = (err, pair, sgn, flip_y)
    still = np.abs(dst - src).mean()
    print(f"[temporal] {label}: pair {best[1]} sign {best[2]:+.0f} flip_y {best[3]:+.0f}: warp err {best[0]:.2f} vs unwarped {still:.2f}")
    return best[1], best[2], best[3]


for d in dirs:
    d = d.rstrip("/")
    out_dir = d + suffix
    os.makedirs(out_dir, exist_ok=True)
    frames = sorted(glob.glob(os.path.join(d, "f_*.png")))
    nums = [int(os.path.basename(f)[2:6]) for f in frames]
    step = min((b-a for a,b in zip(nums,nums[1:])), default=1)
    if frange:
        nums = [n for n in nums if frange[0]-radius*step <= n <= frange[1]+radius*step]
    if not nums:
        continue
    vecs = {n: os.path.join(d, f"v_{n:04d}.exr") for n in nums}
    available = [os.path.exists(v) for v in vecs.values()]
    static = not any(available)
    if not static and not all(available):
        raise RuntimeError(f"Incomplete motion vectors in requested range: {d}")
    if static:
        print(f"[temporal] {d}: no vector EXRs -> treating the camera as static (zero motion)")
    t0 = time.time()
    cache = {}

    def get(n):
        if n not in cache:
            rgb = load_rgb(os.path.join(d, f"f_{n:04d}.png"))
            cache[n] = (rgb, np.zeros(rgb.shape[:2] + (4,), np.float32) if static else load_vec(vecs[n]))
        return cache[n]

    f0, v0 = get(nums[0]); f1, v1 = get(nums[1] if len(nums)>1 else nums[0])
    conv = {1: calibrate(f0, v0 * step, f1, "to next"), -1: calibrate(f1, v1 * step, f0, "to previous")}
    for idx, n in enumerate(nums):
        if frange and not (frange[0] <= n <= frange[1]):
            continue
        if os.path.exists(os.path.join(out_dir, f"f_{n:04d}.png")):     # resumable
            continue
        cur, vec = get(n)
        ref = box3(cur)
        # temporal blend of the low band only: the visible flicker is low-frequency "breathing", and the low band
        # is immune to the slight blur of bilinear resampling (which would otherwise shimmer frame to frame)
        cur_lo = boxn(cur, lowpass) if lowpass > 1 else cur
        acc = cur_lo.copy(); wsum = np.ones(cur.shape[:2], dtype=np.float32)
        for k in range(1, radius + 1):
            for sign in (1, -1):
                j = idx + sign * k
                if j < 0 or j >= len(nums):
                    continue
                if nums[j] != n + sign*k*step:
                    continue
                nb, _ = get(nums[j])
                pair, sgn, fy = conv[sign]
                dx = sgn * vec[..., pair[0]] * k * step; dy = sgn * fy * vec[..., pair[1]] * k * step   # vectors are per scene frame
                w_ = warp(nb, dx, dy)
                diff = np.abs(box3(w_) - ref).max(axis=2)
                wgt = np.exp(-k / radius) * np.clip(1.0 - (diff - tol) / tol, 0.0, 1.0)   # full weight below tol, 0 above 2*tol
                w_lo = boxn(w_, lowpass) if lowpass > 1 else w_
                acc += w_lo * wgt[..., None]; wsum += wgt
        out = cur + (acc / wsum[..., None] - cur_lo)
        save_rgb(os.path.join(out_dir, f"f_{n:04d}.png"), out)
        for old in [m for m in cache if abs(m - n) > radius * step]:
            del cache[old]
        del acc, wsum, out, ref, cur_lo
        gc.collect()
    done = len([f for f in os.listdir(out_dir) if f.startswith("f_")])
    print(f"[temporal] {d}: {done}/{len(nums)} frames in {out_dir} (+{time.time() - t0:.0f}s this run)")
