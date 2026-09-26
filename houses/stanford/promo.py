"""Stanford editorial layer (system Python): title cards, lower-third captions, the music edit and the final encode.

  python -m houses.stanford.promo titles                       # output/film/titles/*.png (1920x1080 RGBA)
  python -m houses.stanford.promo score                        # output/film/stanford_score.wav (edited Pixabay track)
  python -m houses.stanford.promo encode --frames DIR --out output/film/stanford_cinematic.mp4

The picture is one continuous rendered take; this layer only adds typography (with fades), a fade from / to black
and the licensed music.  Music: "Wonders of the Earth" by Grand_Project (Roman Dudchyk), Pixabay Content License,
https://pixabay.com/music/adventure-wonders-of-the-earth-550792/ (see REFERENCES.md for provenance).
"""
import argparse
import math
import os
import subprocess
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from archviz.media import font

HOUSE = Path(__file__).resolve().parent
FILM = Path(os.environ.get('STAN_FILM_DIR', str(HOUSE / 'output' / 'film')))
MUSIC_SRC = HOUSE / 'output' / 'music' / 'wonders_grandproject_550792.mp3'
W, H, FPS = 1920, 1080, 24
CREAM = (250, 246, 236, 255)
GOLD = (214, 186, 132, 255)

# ---------------------------------------------------------------- timing (seconds of the film)
TITLE_MAIN = (2.4, 8.4)                  # over the fountain
CAPTIONS = [                              # (in, out, kicker, text)
    (9.6, 14.4, 'STANFORD PARK', 'A pond-view lot on the walking path'),
    (22.4, 26.4, '13695 STANFORD DRIVE', '4 bedrooms  ·  2.5 baths  ·  2,345 sq ft'),
    (29.0, 32.6, 'MAIN LEVEL', 'Living room and open staircase'),
    (35.6, 39.8, 'GREAT ROOM', 'Fireplace, open to the kitchen and dining'),
    (44.2, 48.6, 'KITCHEN', 'Island, pantry and dining with patio doors'),
    (53.6, 57.6, 'OUTDOORS', 'Paver patio overlooking the common lawn and pond'),
]
END_CARD = 6.0                            # seconds before the end
# music edit: the track starts MUSIC_DELAY into the film and plays until source JOIN_A (just before the onset at
# 55.624 s), then jumps to the final cadence at JOIN_B (just before its hit at 141.230 s), so the closing hit lands
# on the reveal of the house at sunset (film 57.0 s) and the chord decays under the end card
MUSIC_DELAY = 2.38
JOIN_A = 55.60
JOIN_B = 141.21
XFADE = 0.04


def _canvas():
    return Image.new('RGBA', (W, H), (0, 0, 0, 0))


def _tracked(d, xy, text, size, spacing, fill, face='regular', anchor='l'):
    f = font(size, face=face)
    widths = [f.getlength(c) for c in text]
    total = sum(widths) + spacing * (len(text) - 1)
    x, y = xy
    if anchor == 'c':
        x -= total / 2
    for c, w in zip(text, widths):
        d.text((x, y), c, font=f, fill=fill)
        x += w + spacing
    return total


def _shadowed(img, radius=8, alpha=0.55, scrim=None):
    out = _canvas()
    if scrim is not None:
        out.alpha_composite(scrim)
    a = img.split()[3].point(lambda v: int(v * alpha))
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    sh.putalpha(a)
    sh = sh.filter(ImageFilter.GaussianBlur(radius))
    out.alpha_composite(sh, dest=(0, 3))
    out.alpha_composite(img)
    return out


def _scrim(kind):
    """Soft darkening that protects the type without a visible box."""
    y = np.arange(H)[:, None].astype(np.float32)
    x = np.arange(W)[None, :].astype(np.float32)
    if kind == 'centre':
        a = 150 * np.exp(-(((x - W / 2) / 760) ** 2 + ((y - 520) / 230) ** 2))
    else:  # lower-left
        a = 150 * np.clip((y - 700) / 380, 0, 1) ** 1.3 * np.clip((1500 - x) / 900, 0.1, 1)
    arr = np.zeros((H, W, 4), np.uint8)
    arr[..., :3] = (10, 14, 18)
    arr[..., 3] = np.clip(a, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


def titles():
    out = FILM / 'titles'
    out.mkdir(parents=True, exist_ok=True)
    serif = lambda s: font(s, serif=True)                    # noqa: E731
    # main title
    im = _canvas(); d = ImageDraw.Draw(im)
    _tracked(d, (W / 2, 408), 'CARMEL  ·  INDIANA', 26, 9, GOLD, anchor='c')
    f = serif(112)
    t = '13695 Stanford Drive'
    d.text(((W - f.getlength(t)) / 2, 444), t, font=f, fill=CREAM)
    d.line([(W / 2 - 70, 606), (W / 2 + 70, 606)], fill=GOLD, width=2)
    _tracked(d, (W / 2, 628), 'A LAKESIDE HOME IN STANFORD PARK', 22, 6, CREAM, anchor='c')
    _shadowed(im, 10, 0.6, _scrim('centre')).save(out / 'title_main.png')
    # end card
    im = _canvas(); d = ImageDraw.Draw(im)
    _tracked(d, (W / 2, 356), 'WELCOME HOME', 24, 10, GOLD, anchor='c')
    f = serif(104)
    d.text(((W - f.getlength(t)) / 2, 392), t, font=f, fill=CREAM)
    d.line([(W / 2 - 70, 548), (W / 2 + 70, 548)], fill=GOLD, width=2)
    _tracked(d, (W / 2, 572), '4 BEDROOMS   ·   2.5 BATHS   ·   2,345 SQ FT   ·   POND VIEW', 22, 4, CREAM, anchor='c')
    _tracked(d, (W / 2, 616), 'CARMEL, INDIANA  46074', 20, 6, CREAM, anchor='c')
    _shadowed(im, 10, 0.6, _scrim('centre')).save(out / 'title_end.png')
    # lower thirds
    for i, (_, _, kicker, text) in enumerate(CAPTIONS):
        im = _canvas(); d = ImageDraw.Draw(im)
        d.line([(110, 905), (160, 905)], fill=GOLD, width=2)
        _tracked(d, (178, 891), kicker, 22, 6, GOLD)
        f = serif(46)
        d.text((108, 925), text, font=f, fill=CREAM)
        _shadowed(im, 6, 0.55, _scrim('lower')).save(out / f'cap_{i:02d}.png')
    # disclosure (whole film)
    im = _canvas(); d = ImageDraw.Draw(im)
    label = '3D VISUALIZATION  ·  VIRTUALLY STAGED  ·  DIMENSIONS APPROXIMATE'
    f = font(15)
    x = W - 60 - sum(f.getlength(c) + 2 for c in label)
    _tracked(d, (x, 1036), label, 15, 2, (250, 248, 240, 150))
    im.save(out / 'disclosure.png')
    print('[promo] titles ->', out)


# ---------------------------------------------------------------- music
def _decode(path, sr=48000):
    import imageio_ffmpeg
    raw = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-v', 'error', '-i', str(path), '-ac', '2', '-ar', str(sr),
                          '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy(), sr


def score(length=None, out=None):
    x, sr = _decode(MUSIC_SRC)
    a_end = int(JOIN_A * sr)
    b0 = int(JOIN_B * sr)
    n = int(XFADE * sr)
    A = x[:a_end + n].copy()
    B = x[b0:].copy()
    t = np.linspace(0, math.pi / 2, n)[:, None]
    mix = np.concatenate([np.zeros((int(MUSIC_DELAY * sr), 2), np.float32), A[:a_end],
                          A[a_end:a_end + n] * np.cos(t) + B[:n] * np.sin(t), B[n:]])
    if length:
        L = int(length * sr)
        mix = mix[:L] if len(mix) >= L else np.concatenate([mix, np.zeros((L - len(mix), 2), np.float32)])
    fade = int(1.5 * sr)
    mix[-fade:] *= np.linspace(1, 0, fade)[:, None] ** 2
    mix *= 0.89 / max(1e-6, float(np.abs(mix).max()))           # -1 dBFS peak
    out = Path(out or (FILM / 'stanford_score.wav'))
    out.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out), 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((np.clip(mix, -1, 1) * 32767).astype('<i2').tobytes())
    print('[promo] score ->', out, f'{len(mix) / sr:.2f}s')
    return out


# ---------------------------------------------------------------- final encode (ffmpeg overlay graph)
def encode(frames, out, music=None, crf=16):
    import imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    frames = Path(frames)
    files = sorted(frames.glob('f_*.png'))
    n = len(files)
    dur = n / FPS
    first = int(files[0].stem.split('_')[1])
    tdir = FILM / 'titles'
    overlays = [(tdir / 'title_main.png', *TITLE_MAIN, 1.0)]
    overlays += [(tdir / f'cap_{i:02d}.png', a, b, 0.6) for i, (a, b, _, _) in enumerate(CAPTIONS)]
    overlays += [(tdir / 'title_end.png', dur - END_CARD, dur - 0.4, 1.2)]
    cmd = [ff, '-y', '-v', 'warning', '-framerate', str(FPS), '-start_number', str(first), '-i', str(frames / 'f_%04d.png')]
    for p, *_ in overlays:
        cmd += ['-loop', '1', '-framerate', str(FPS), '-i', str(p)]
    cmd += ['-loop', '1', '-framerate', str(FPS), '-i', str(tdir / 'disclosure.png')]
    music = music or score(length=dur)
    cmd += ['-i', str(music)]
    g = ['[0:v]format=rgba[v0]']
    last = 'v0'
    for i, (p, a, b, fd) in enumerate(overlays, start=1):
        a, b = max(0.0, a), max(0.0, min(b, dur))
        if a >= dur or b - a < 2 * fd:                       # outside a short test clip: keep the input, show nothing
            g.append(f'[{i}:v]format=rgba,trim=duration={dur:.3f},colorchannelmixer=aa=0[o{i}]')
        else:
            g.append(f'[{i}:v]format=rgba,trim=duration={dur:.3f},fade=t=in:st={a:.3f}:d={fd}:alpha=1,'
                     f'fade=t=out:st={b - fd:.3f}:d={fd}:alpha=1[o{i}]')
        g.append(f'[{last}][o{i}]overlay=0:0:shortest=1[v{i}]')
        last = f'v{i}'
    k = len(overlays) + 1
    g.append(f'[{k}:v]format=rgba,trim=duration={dur:.3f},fade=t=in:st=1.0:d=1.0:alpha=1,'
             f'fade=t=out:st={max(2.0, dur - END_CARD - 1.0):.3f}:d=0.8:alpha=1[dsc]')
    g.append(f'[{last}][dsc]overlay=0:0:shortest=1,fade=t=in:st=0:d=0.8,fade=t=out:st={max(0.0, dur - 1.2):.3f}:d=1.2,'
             f'scale=in_range=pc:out_range=tv:out_color_matrix=bt709,format=yuv420p,'
             f'setparams=range=limited:color_primaries=bt709:color_trc=bt709:colorspace=bt709[vout]')
    cmd += ['-filter_complex', ';'.join(g), '-map', '[vout]', '-map', f'{k + 1}:a',
            '-c:v', 'libx264', '-preset', 'slow', '-crf', str(crf), '-profile:v', 'high', '-pix_fmt', 'yuv420p',
            '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv',
            '-r', str(FPS), '-c:a', 'aac', '-b:a', '256k', '-shortest', '-movflags', '+faststart', str(out)]
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(cmd, check=True)
    print('[promo] encoded', out, f'{n} frames, {dur:.2f}s')


def verify(mp4, frames_expected, out_dir):
    """Decode the whole movie: frame count, rate, size, colour tags, duration, audio level; write a contact sheet
    (every 2 s), a poster and a JSON report next to it.  Visual acceptance is still a human review."""
    import imageio_ffmpeg
    from archviz.media import digest, write_json
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    info = subprocess.run([ff, '-hide_banner', '-i', str(mp4)], capture_output=True, text=True).stderr
    video = next(line.strip() for line in info.splitlines() if 'Video:' in line)
    audio = next((line.strip() for line in info.splitlines() if 'Audio:' in line), None)
    raw = subprocess.run([ff, '-v', 'error', '-i', str(mp4), '-map', '0:v', '-f', 'rawvideo', '-pix_fmt', 'gray',
                          '-s', '96x54', '-'], capture_output=True, check=True).stdout
    n = len(raw) // (96 * 54)
    luma = np.frombuffer(raw[:n * 96 * 54], np.uint8).reshape(n, -1).mean(1)
    pcm = subprocess.run([ff, '-v', 'error', '-i', str(mp4), '-map', '0:a', '-ac', '1', '-ar', '8000', '-f', 's16le', '-'],
                         capture_output=True).stdout
    a = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768 if pcm else np.zeros(1)
    rms = float(20 * np.log10(np.sqrt(np.mean(a ** 2)) + 1e-9))
    jumps = np.abs(np.diff(luma))
    tiles = []
    for t in np.arange(0, n / FPS, 2.0):
        png = out_dir / '_sheet.png'
        subprocess.run([ff, '-v', 'error', '-y', '-ss', f'{t:.3f}', '-i', str(mp4), '-frames:v', '1', '-s', '384x216', str(png)], check=True)
        im = Image.open(png).convert('RGB'); ImageDraw.Draw(im).text((6, 4), f'{t:04.1f}s', fill=(255, 255, 0)); tiles.append(im)
        png.unlink()
    cols = 6
    sheet = Image.new('RGB', (cols * 384, ((len(tiles) + cols - 1) // cols) * 216))
    for i, im in enumerate(tiles):
        sheet.paste(im, ((i % cols) * 384, (i // cols) * 216))
    sheet.save(out_dir / 'stanford_contact_sheet.jpg', quality=88)
    subprocess.run([ff, '-v', 'error', '-y', '-ss', f'{min(58.5, n / FPS / 2):.2f}', '-i', str(mp4), '-frames:v', '1', str(out_dir / 'stanford_poster.jpg')], check=True)
    report = dict(file=str(mp4), sha256=digest(mp4), decoded_frames=n, expected_frames=frames_expected, fps=FPS,
                  duration_s=n / FPS, video=video, audio=audio, audio_rms_dbfs=round(rms, 1),
                  largest_luma_step=dict(frame=int(np.argmax(jumps)) + 1, value=round(float(jumps.max()), 1)),
                  visual_review='pending')
    write_json(out_dir / 'stanford_cinematic_verification.json', report)
    ok = n == frames_expected and '1920x1080' in video and 'bt709' in video and audio is not None and rms > -40
    print('[promo] verify', 'OK' if ok else 'CHECK', json_line(report))
    return ok


def json_line(d):
    import json
    return json.dumps({k: v for k, v in d.items() if k != 'file'})


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('cmd', choices=['titles', 'score', 'encode', 'verify'])
    ap.add_argument('--expected', type=int)
    ap.add_argument('--frames')
    ap.add_argument('--out')
    ap.add_argument('--length', type=float)
    ap.add_argument('--crf', type=int, default=16)
    a = ap.parse_args()
    if a.cmd == 'titles':
        titles()
    elif a.cmd == 'score':
        score(a.length, a.out)
    elif a.cmd == 'verify':
        verify(Path(a.out), a.expected, Path(a.out).parent / 'qa')
    else:
        titles()
        encode(a.frames, a.out or (FILM / 'stanford_cinematic.mp4'), crf=a.crf)
