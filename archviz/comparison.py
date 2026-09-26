"""Append frame-synchronized photo/render panels to an existing CFR video.

Input must be square-pixel, limited-range BT.709 SDR at an integer CFR rate.
The cinematic keeps its original pixel dimensions. Video is re-encoded once;
audio packets are copied in a separate mux to preserve the complete soundtrack.
All manifest paths are relative to the timeline JSON. Frame numbers are zero-based.
"""
import argparse
import copy
import json
import math
from pathlib import Path
import re
import subprocess

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw

from .media import audio_hash, digest, ffmpeg, fit_image, font, local_path, metadata, read_frame, write_json


def validate_timeline(data):
    data = copy.deepcopy(data)
    if data.get('schema_version') != 1:
        raise ValueError('Timeline requires schema_version 1')
    for key in ('fps', 'frames'):
        if type(data[key]) is not int or data[key] <= 0:
            raise ValueError(f'{key} must be a positive integer (integer CFR rates only)')
    width, height = data['source_size']
    output_width, output_height = data['output_size']
    if any(type(n) is not int or n <= 0 or n % 2 for n in [width, height, output_width, output_height]):
        raise ValueError('Video dimensions must be positive even integers for yuv420p')
    if output_width != width or output_height <= height or width < 320:
        raise ValueError('Output must keep source width (at least 320) and append a panel below it')
    if output_height - height < round(100 * width / 1920):
        raise ValueError('Comparison panel is too short for labels and pictures')
    segments = data['segments']
    starts = [segment['start_frame'] for segment in segments]
    if (not starts or any(type(n) is not int for n in starts) or starts[0] != 0
            or starts != sorted(set(starts)) or starts[-1] >= data['frames']):
        raise ValueError('Segments must start at frame 0 and increase strictly within the film')
    for index, segment in enumerate(segments):
        if type(segment['photo']) is not int or segment['photo'] < 0 or not segment.get('title'):
            raise ValueError(f'Invalid photo ID or title: {segment}')
        end = starts[index + 1] if index + 1 < len(starts) else data['frames']
        review = segment.get('review_time', (segment['start_frame'] + end - 1) / 2 / data['fps'])
        if not math.isfinite(review) or not segment['start_frame'] / data['fps'] <= review < end / data['fps']:
            raise ValueError(f'Review time lies outside segment: {segment}')
        segment.update(end_frame=end, review_time=review)
    return data


def escape_metadata(value):
    return (value.replace('\\', '\\\\').replace('\n', ' ').replace('\r', ' ')
            .replace('=', '\\=').replace(';', '\\;').replace('#', '\\#'))


def prepare(config, out):
    config, out = Path(config).resolve(), Path(out).resolve()
    data = validate_timeline(json.loads(config.read_text(encoding='utf-8')))
    source, gallery = local_path(config.parent, data['source']), local_path(config.parent, data['gallery'])
    meta = metadata(source)
    count, _ = imageio_ffmpeg.count_frames_and_secs(str(source))
    if list(meta['size']) != data['source_size'] or abs(meta['fps'] - data['fps']) > 0.001 or count != data['frames']:
        raise ValueError(f'Source metadata does not match timeline: {meta}, frames={count}')
    color = ffmpeg(['-i', str(source), '-vf', 'showinfo', '-frames:v', '1', '-an', '-f', 'null', '-'],
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).stderr
    if ('color_range:tv color_space:bt709 color_primaries:bt709 color_trc:bt709' not in color
            or not re.search(r'\bsar:1/1\b', color)):
        raise ValueError('Source must be square-pixel limited-range BT.709 SDR; normalize its color metadata before composition')
    timing = ffmpeg(['-i', str(source), '-vf', 'vfrdet', '-an', '-f', 'null', '-'],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).stderr
    rates = re.findall(r'VFR:([0-9.]+)', timing)
    if not rates or float(rates[-1]) != 0:
        raise ValueError('Source frame timestamps must be constant-rate; normalize variable-rate video first')
    pairs = json.loads((gallery / 'manifest.json').read_text(encoding='utf-8'))['pairs']
    records = {record['photo']: record for record in pairs}
    if len(records) != len(pairs):
        raise ValueError('Gallery contains duplicate photo IDs')
    selected = sorted({segment['photo'] for segment in data['segments']})
    for number in selected:
        if number not in records:
            raise ValueError(f'Photo {number} is absent from gallery')
        row = records[number]
        if row['render_kind'] != 'whole_house_model':
            raise ValueError(f'Photo {number} is a separate detail study, not part of this movie')
        for kind in ('original', 'render'):
            if digest(local_path(gallery, row[kind])) != row[f'{kind}_sha256']:
                raise ValueError(f'Gallery image changed: {row[kind]}')
    width, height = data['source_size']
    panel_height = data['output_size'][1] - height
    scale = width / 1920
    margin, gap, top = max(2, round(16 * scale)), max(2, round(16 * scale)), round(80 * scale)
    picture_width = (width - 2 * margin - gap) // 2
    picture_height = panel_height - top - margin
    panel_dir = out / 'panels'
    panel_dir.mkdir(parents=True, exist_ok=True)
    for number in selected:
        row = records[number]
        panel = Image.new('RGB', (width, panel_height), '#121b19')
        draw = ImageDraw.Draw(panel)
        draw.line((0, 0, width - 1, 0), fill='#647760', width=max(1, round(3 * scale)))
        title = next(segment['title'] for segment in data['segments'] if segment['photo'] == number)
        for kind, x, label, color in [('original', margin, 'ORIGINAL PHOTO', '#c0c9c1'),
                                      ('render', margin + picture_width + gap, 'RENDERED VIEW · VIRTUALLY STAGED', '#d0e4b2')]:
            draw.text((x, round(12 * scale)), label, font=font(max(8, round(19 * scale))), fill=color)
            title_font = font(max(9, round(24 * scale)))
            caption = f'{number:02d} / {title}'
            while draw.textlength(caption, font=title_font) > picture_width and len(caption) > 4:
                caption = caption[:-2].rstrip('…') + '…'
            draw.text((x, round(39 * scale)), caption, font=title_font, fill='#f1f3ec')
            panel.paste(fit_image(local_path(gallery, row[kind]), (picture_width, picture_height), '#121b19'), (x, top))
        panel.save(panel_dir / f'{number:02d}.png')
    fps = data['fps']
    concat = ['ffconcat version 1.0']
    chapters = [';FFMETADATA1', 'title=' + escape_metadata(data.get('title', 'Photo and render comparison'))]
    for segment in data['segments']:
        start, end = segment['start_frame'], segment['end_frame']
        concat.extend([f"file 'panels/{segment['photo']:02d}.png'", f'option framerate {fps}', f'duration {(end-start)/fps:.12f}'])
        chapters.extend(['[CHAPTER]', f'TIMEBASE=1/{fps}', f'START={start}', f'END={end}', 'title=' + escape_metadata(segment['title'])])
    concat.extend([f"file 'panels/{data['segments'][-1]['photo']:02d}.png'", f'option framerate {fps}'])
    (out / 'panels.ffconcat').write_text('\n'.join(concat) + '\n', encoding='utf-8')
    (out / 'chapters.ffmetadata').write_text('\n'.join(chapters) + '\n', encoding='utf-8')
    data.update(source_sha256=digest(source), has_audio=bool(meta.get('audio_codec')),
                distinct_pairs=len(selected), source_metadata=meta)
    write_json(out / 'composition.json', data)
    return data


def compose(config, out, data, movie):
    source = local_path(Path(config).resolve().parent, data['source'])
    out, movie = Path(out).resolve(), Path(movie).resolve()
    movie.parent.mkdir(parents=True, exist_ok=True)
    if movie == source:
        raise ValueError('Output movie must not overwrite source')
    silent, muxed = out / '_video.mp4', out / '_muxed.mp4'
    if source in (silent, muxed) or movie in (silent, muxed):
        raise ValueError('Movie paths collide with composition scratch files')
    fps, count = data['fps'], data['frames']
    graph = (f'[0:v]setpts=PTS-STARTPTS[cinematic];[1:v]fps={fps},trim=end_frame={count},'
             'setpts=PTS-STARTPTS,scale=iw:ih:in_range=pc:out_range=tv:out_color_matrix=bt709,'
             'format=yuv420p,setparams=range=limited:color_primaries=bt709:color_trc=bt709:colorspace=bt709'
             '[comparisons];[cinematic][comparisons]vstack=inputs=2:shortest=1,'
             'setparams=range=limited:color_primaries=bt709:color_trc=bt709:colorspace=bt709[video]')
    command = ['-v', 'error', '-i', str(source), '-f', 'concat', '-safe', '0', '-i', str(out / 'panels.ffconcat'),
               '-f', 'ffmetadata', '-i', str(out / 'chapters.ffmetadata'), '-filter_complex_threads', '4',
               '-filter_complex', graph, '-map', '[video]', '-an', '-map_metadata', '2', '-map_chapters', '2',
               '-c:v', 'libx264', '-preset', 'slow', '-crf', '12', '-pix_fmt', 'yuv420p', '-threads', '8',
               '-color_range', 'tv', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
               '-r:v', str(fps), '-fps_mode:v', 'cfr', '-enc_time_base:v', f'1:{fps}',
               '-frames:v', str(count), '-movflags', '+faststart', str(silent)]
    write_json(out / 'ffmpeg_command.json', command)
    ffmpeg(command)
    # Frame-limited encoding can truncate stream-copied AAC. Mux without a frame
    # or duration limit, then compare packet hashes in verify(). Silent films work too.
    if data['has_audio']:
        ffmpeg(['-v', 'error', '-i', str(silent), '-i', str(source), '-map', '0:v:0', '-map', '1:a:0',
                '-map_metadata', '0', '-map_chapters', '0', '-c', 'copy', '-movflags', '+faststart', str(muxed)])
        muxed.replace(movie)
        silent.unlink()
    else:
        silent.replace(movie)


def verify(config, out, movie):
    out, movie = Path(out).resolve(), Path(movie).resolve()
    data = validate_timeline(json.loads((out / 'composition.json').read_text(encoding='utf-8')))
    source = local_path(Path(config).resolve().parent, data['source'])
    if digest(source) != data['source_sha256']:
        raise ValueError('Source movie changed after preparation')
    meta = metadata(movie)
    count, duration = imageio_ffmpeg.count_frames_and_secs(str(movie))
    fps, (width, height) = data['fps'], data['source_size']
    if (list(meta['size']) != data['output_size'] or abs(meta['fps'] - fps) > .001
            or count != data['frames'] or abs(duration - count / fps) > .02):
        raise ValueError(f'Output does not match timeline: {meta}, frames={count}')
    decoded = ffmpeg(['-v', 'error', '-i', str(movie), '-f', 'null', '-'],
                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if decoded.stderr.strip():
        raise ValueError(f'Decode errors: {decoded.stderr}')
    audio = None
    if data['has_audio']:
        audio = audio_hash(source)
        if audio_hash(movie) != audio:
            raise ValueError('Output audio packets differ from original')
    quality = ffmpeg(['-i', str(movie), '-i', str(source), '-filter_complex',
                      f'[0:v]crop={width}:{height}:0:0[top];[top][1:v]ssim', '-an', '-f', 'null', '-'],
                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    matches = re.findall(r'All:([0-9.]+)', quality.stderr)
    if not matches or float(matches[-1]) <= .99:
        raise ValueError(f'Top video SSIM must exceed .99: {quality.stderr[-1500:]}')
    checks, images = [], []
    def check(frame, segment):
        image = read_frame(movie, frame, data['output_size'], fps)
        with Image.open(out / 'panels' / f'{segment["photo"]:02d}.png') as expected:
            error = float(np.abs(np.asarray(image.crop((0, height, width, data['output_size'][1])), dtype=np.float32)
                                 - np.asarray(expected.convert('RGB'), dtype=np.float32)).mean())
        if error >= 5:
            raise ValueError(f'Wrong or damaged panel at frame {frame}: photo {segment["photo"]}, error {error}')
        checks.append({'frame': frame, 'photo': segment['photo'], 'panel_mean_rgb_error': error})
        return image
    for segment in data['segments']:
        frame = min(segment['end_frame'] - 1, max(segment['start_frame'], round(segment['review_time'] * fps)))
        images.append(check(frame, segment))
    for previous, current in zip(data['segments'], data['segments'][1:]):
        check(current['start_frame'] - 1, previous)
        check(current['start_frame'], current)
    thumb_width = 640
    thumb_height = round(data['output_size'][1] * thumb_width / width)
    sheet = Image.new('RGB', (3 * thumb_width, math.ceil(len(images) / 3) * (thumb_height + 42)), '#121b19')
    draw = ImageDraw.Draw(sheet)
    for index, (image, segment) in enumerate(zip(images, data['segments'])):
        x, y = index % 3 * thumb_width, index // 3 * (thumb_height + 42)
        sheet.paste(image.resize((thumb_width, thumb_height), Image.Resampling.LANCZOS), (x, y))
        draw.text((x + 10, y + thumb_height + 8), f'Photo {segment["photo"]:02d} · {segment["title"]}', font=font(20), fill='#edf2e8')
    sheet.save(out / 'contact_sheet.jpg', quality=93)
    images[0].save(out / 'poster.jpg', quality=95)
    report = {'video': movie.name, 'sha256': digest(movie), 'source_sha256': data['source_sha256'],
              'frames': count, 'fps': fps, 'size': data['output_size'], 'duration_seconds': count / fps,
              'audio_packet_hash': audio, 'top_video_all_frames_ssim': float(matches[-1]),
              'full_decode_errors': decoded.stderr, 'frame_checks': checks,
              'visual_review': 'Pending human inspection of contact_sheet.jpg and native-size frames.'}
    write_json(out / 'validation.json', report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--timeline', required=True, type=Path)
    parser.add_argument('--work', required=True, type=Path, help='Generated panels and verification reports')
    parser.add_argument('--output', required=True, type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--prepare-only', action='store_true')
    mode.add_argument('--verify-only', action='store_true')
    args = parser.parse_args(argv)
    if args.verify_only:
        verify(args.timeline, args.work, args.output)
        return
    data = prepare(args.timeline, args.work)
    if not args.prepare_only:
        compose(args.timeline, args.work, data, args.output)
        verify(args.timeline, args.work, args.output)
    print(f'Prepared {data["distinct_pairs"]} photo pairs across {len(data["segments"])} sections')


if __name__ == '__main__':
    main()
