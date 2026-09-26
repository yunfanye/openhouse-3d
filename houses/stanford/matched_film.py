"""Editorial layer for the matched take (system Python): the other reconstruction's titles, fades and score, the clean
encode, and a side-by-side movie of both reconstructions for comparison.

  python -m houses.stanford.matched_film encode --frames DIR --music SCORE.wav --out stanford_matched_1080p.mp4
  python -m houses.stanford.matched_film side-by-side --ours stanford_matched_1080p.mp4 \
      --theirs other_reconstruction_1080p.mp4 --out stanford_side_by_side.mp4 \
      [--label-ours "This reconstruction" --label-theirs "Other reconstruction"]

The transitions copy the other reconstruction's finishing pass (its 2026-09-08 delivery): a 0.65 s fade from
black, the lower-left opening title (in 0.8 s over 1.2 s, out 5.5 s over 1 s), the closing title from 5.04 s before the
end over 1.3 s, and a 1.14 s fade to black.  The picture is one continuous rendered take; there are no cuts.
"""
import argparse
import json
from pathlib import Path
import subprocess

from PIL import Image, ImageDraw, ImageFilter

from archviz.media import digest, ffmpeg, font, metadata

FPS, FRAMES = 24, 1921
W, H = 1920, 1080


def title_image(path, main, sub, footer=False):
    """The other film's title card: a soft lower-left scrim, a gold rule, a serif line and a light subline."""
    im = Image.new('RGBA', (W, H))
    mask = Image.new('L', im.size)
    ImageDraw.Draw(mask).ellipse((-350, 610, 1760, 1400), fill=120)
    mask = mask.filter(ImageFilter.GaussianBlur(100))
    bg = Image.new('RGBA', im.size, (8, 17, 23, 255))
    bg.putalpha(mask)
    im.alpha_composite(bg)
    d = ImageDraw.Draw(im)
    y = 820 if footer else 810
    d.line((114, y - 45, 174, y - 45), fill=(224, 198, 153, 240), width=3)
    d.text((112, y), main, font=font(63, serif=True), fill=(255, 251, 240, 255))
    d.text((116, y + 88), sub, font=font(24, face='light'), fill=(244, 238, 225, 255))
    im.save(path)


def _decoded_frames(mp4):
    r = ffmpeg(['-v', 'error', '-i', str(mp4), '-map', '0:v:0', '-f', 'framemd5', '-'],
               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if r.stderr.strip():
        raise ValueError(f'Decode errors in {mp4}: {r.stderr.decode()[:400]}')
    return r.stdout, [x for x in r.stdout.decode().splitlines() if x and not x.startswith('#')]


def encode(frames, out, music, frame_count=FRAMES):
    frames, out = Path(frames).resolve(), Path(out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    expected = [frames / f'f_{i:04d}.png' for i in range(1, frame_count + 1)]
    missing = [p.name for p in expected if not p.is_file()]
    if missing:
        raise ValueError(f'Missing {len(missing)} rendered frames: {missing[:10]}')
    for p in expected:
        with Image.open(p) as im:
            if im.size != (W, H):
                raise ValueError(f'Wrong frame size: {p}')
            im.verify()
    duration = frame_count / FPS
    work = out.parent / 'titles'
    work.mkdir(exist_ok=True)
    title_image(work / 'opening.png', '13695 Stanford Drive', 'CARMEL, INDIANA  /  STANFORD PARK')
    title_image(work / 'closing.png', 'A place by the water.', '13695 STANFORD DRIVE  /  CARMEL, INDIANA', True)
    filt = ('[1:v]format=rgba,fade=t=in:st=0.8:d=1.2:alpha=1,fade=t=out:st=5.5:d=1:alpha=1[o];'
            f'[2:v]format=rgba,fade=t=in:st={duration - 5.04:.4f}:d=1.3:alpha=1[e];'
            '[0:v][o]overlay=0:0:format=auto[v1];'
            f'[v1][e]overlay=0:0:format=auto,fade=t=in:st=0:d=0.65,fade=t=out:st={duration - 1.14:.4f}:d=1.14,'
            'format=gbrpf32le,zscale=matrixin=gbr:transferin=iec61966-2-1:primariesin=bt709:rangein=full:'
            'matrix=bt709:transfer=bt709:primaries=bt709:range=limited,format=yuv420p,'
            'setparams=range=limited:color_primaries=bt709:color_trc=bt709:colorspace=bt709[v]')
    args = ['-y', '-framerate', str(FPS), '-start_number', '1', '-i', str(frames / 'f_%04d.png'),
            '-loop', '1', '-framerate', str(FPS), '-i', str(work / 'opening.png'),
            '-loop', '1', '-framerate', str(FPS), '-i', str(work / 'closing.png'),
            '-i', str(Path(music).resolve()), '-filter_complex', filt, '-map', '[v]', '-map', '3:a:0',
            '-frames:v', str(frame_count), '-t', str(duration), '-r', str(FPS),
            '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p',
            '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', '-color_range', 'tv',
            '-c:a', 'aac', '-b:a', '256k', '-movflags', '+faststart',
            '-metadata', 'title=13695 Stanford Drive | A Place by the Water (matched route)',
            '-metadata', 'comment=Photo-derived 3D reconstruction; dimensions and furnishings approximate.', str(out)]
    r = ffmpeg(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (out.parent / 'encode.log').write_bytes(r.stderr)
    raw, rows = _decoded_frames(out)
    if len(rows) != frame_count:
        raise ValueError(f'Encoded movie has {len(rows)} frames, expected {frame_count}')
    (out.parent / 'decoded_frames.md5').write_bytes(raw)
    meta = metadata(out)
    if 'bt709' not in meta['pix_fmt'] or 'iec61966' in meta['pix_fmt']:
        raise ValueError(f'Unexpected colour metadata: {meta}')
    report = {'metadata': meta, 'frames_decoded': len(rows), 'fps': FPS, 'duration_s': duration,
              'movie_sha256': digest(out), 'audio_source_sha256': digest(music), 'camera_cuts': 0,
              'frame_interpolation': False, 'visual_review': 'pending'}
    (out.parent / 'movie_verification.json').write_text(json.dumps(report, indent=2))
    print('[matched] encoded', out, len(rows), 'frames')
    return out


def _label(path, text, sub):
    im = Image.new('RGBA', (W, H))
    d = ImageDraw.Draw(im)
    f, fs = font(26, face='medium'), font(18, face='light')
    w = max(f.getlength(text), fs.getlength(sub)) + 44
    d.rounded_rectangle((28, 26, 28 + w, 112), radius=10, fill=(8, 17, 23, 170))
    d.text((50, 38), text, font=f, fill=(255, 251, 240, 255))
    d.text((50, 76), sub, font=fs, fill=(224, 198, 153, 255))
    im.save(path)


def side_by_side(ours, theirs, out, frame_count=FRAMES, label_ours='This reconstruction',
                 label_theirs='Other reconstruction'):
    """Both films frame-locked at full resolution: theirs on the left, ours on the right (3840 x 1080, ours' audio)."""
    ours, theirs, out = Path(ours).resolve(), Path(theirs).resolve(), Path(out).resolve()
    for movie in (ours, theirs):
        _, rows = _decoded_frames(movie)
        if len(rows) != frame_count:
            raise ValueError(f'{movie} has {len(rows)} frames, expected {frame_count}')
    work = out.parent / 'titles'
    work.mkdir(parents=True, exist_ok=True)
    _label(work / 'label_theirs.png', label_theirs, 'SEPTEMBER 8 RECONSTRUCTION')
    _label(work / 'label_ours.png', label_ours, 'MATCHED ROUTE · THIS RECONSTRUCTION')
    filt = ('[0:v]setpts=PTS-STARTPTS[a];[1:v]setpts=PTS-STARTPTS[b];'
            '[2:v]format=rgba[la];[3:v]format=rgba[lb];'
            '[a][la]overlay=0:0:shortest=1[a1];[b][lb]overlay=0:0:shortest=1[b1];'
            '[a1][b1]hstack=inputs=2,format=yuv420p,'
            'setparams=range=limited:color_primaries=bt709:color_trc=bt709:colorspace=bt709[v]')
    args = ['-y', '-i', str(theirs), '-i', str(ours),
            '-loop', '1', '-framerate', str(FPS), '-i', str(work / 'label_theirs.png'),
            '-loop', '1', '-framerate', str(FPS), '-i', str(work / 'label_ours.png'),
            '-filter_complex', filt, '-map', '[v]', '-map', '1:a:0', '-frames:v', str(frame_count),
            '-r', str(FPS), '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p',
            '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', '-color_range', 'tv',
            '-c:a', 'copy', '-movflags', '+faststart',
            '-metadata', 'title=13695 Stanford Drive | two reconstructions, one route', str(out)]
    r = ffmpeg(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (out.parent / 'side_by_side.log').write_bytes(r.stderr)
    _, rows = _decoded_frames(out)
    if len(rows) != frame_count:
        raise ValueError(f'Side-by-side has {len(rows)} frames, expected {frame_count}')
    report = {'metadata': metadata(out), 'frames_decoded': len(rows), 'left': str(theirs),
              'left_sha256': digest(theirs), 'right': str(ours), 'right_sha256': digest(ours),
              'movie_sha256': digest(out)}
    (out.parent / 'side_by_side_verification.json').write_text(json.dumps(report, indent=2))
    print('[matched] side-by-side', out, len(rows), 'frames')
    return out


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('cmd', choices=['encode', 'side-by-side'])
    ap.add_argument('--frames', type=Path)
    ap.add_argument('--music', type=Path)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--ours', type=Path)
    ap.add_argument('--theirs', type=Path)
    ap.add_argument('--frame-count', type=int, default=FRAMES)
    ap.add_argument('--label-ours', default='This reconstruction')
    ap.add_argument('--label-theirs', default='Other reconstruction')
    a = ap.parse_args()
    if a.cmd == 'encode':
        encode(a.frames, a.out, a.music, a.frame_count)
    else:
        side_by_side(a.ours, a.theirs, a.out, a.frame_count, a.label_ours, a.label_theirs)
