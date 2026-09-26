import copy
import json
from pathlib import Path
import subprocess
import zipfile

import numpy as np
from PIL import Image
import pytest

from archviz.comparison import compose, prepare, validate_timeline, verify
from archviz.gallery import build
from archviz.media import digest, ffmpeg, write_json


def timeline():
    return {'schema_version': 1, 'source': 'source.mp4', 'gallery': 'gallery', 'fps': 12,
            'frames': 24, 'source_size': [320, 180], 'output_size': [320, 300],
            'segments': [{'start_frame': 0, 'photo': 3, 'title': 'Room A'},
                         {'start_frame': 8, 'photo': 10, 'title': 'Room B'},
                         {'start_frame': 16, 'photo': 3, 'title': 'Room A'}]}


@pytest.mark.parametrize('mutate', [
    lambda data: data.update(fps=0),
    lambda data: data.update(frames=True),
    lambda data: data.update(output_size=[322, 300]),
    lambda data: data['segments'][0].update(start_frame=1),
    lambda data: data['segments'][1].update(start_frame=0),
    lambda data: data['segments'][2].update(start_frame=24),
    lambda data: data['segments'][0].update(review_time=1),
])
def test_bad_timeline_rejected(mutate):
    data = timeline()
    mutate(data)
    with pytest.raises(ValueError):
        validate_timeline(data)


def make_gallery(tmp_path):
    y, x = np.mgrid[0:128, 0:192]
    pairs = []
    for number in (3, 10):
        for kind in ('original', 'render'):
            # Distinct, spatially varying colors; photo-like chroma bandwidth.
            # White RGB noise is destroyed by 4:2:0 subsampling independently
            # of the compositor's correctness.
            pixels = np.stack([(x + number * 11) % 256, (y + number * 7) % 256,
                               100 + 60 * np.sin((x + y) / 20)], axis=-1).astype(np.uint8)
            Image.fromarray(pixels).save(tmp_path / f'{kind}{number}.png')
        pairs.append({'photo': number, 'title': f'Room <{number}>', 'camera': f'room{number}',
                      'original': f'original{number}.png', 'render': f'render{number}.png'})
    config = {'schema_version': 1, 'house': 'A & B', 'render_resolution': [192, 128], 'pairs': pairs}
    write_json(tmp_path / 'gallery.json', config)
    return config


def test_gallery_preserves_sources_and_closed_archive(tmp_path):
    config = make_gallery(tmp_path)
    out = tmp_path / 'gallery'
    out.mkdir()
    (out / 'private.log').write_text('do not package')
    manifest = build(tmp_path / 'gallery.json', out, tmp_path / 'gallery.zip')
    assert [row['photo'] for row in manifest['pairs']] == [3, 10]
    for row in manifest['pairs']:
        assert digest(out / row['original']) == digest(tmp_path / f'original{row["photo"]}.png')
        assert digest(out / row['render']) == digest(tmp_path / f'render{row["photo"]}.png')
    page = (out / 'index.html').read_text()
    assert 'Room &lt;3&gt;' in page and 'A &amp; B' in page
    assert '2 / 2' in page and '11 / 2' not in page
    with zipfile.ZipFile(tmp_path / 'gallery.zip') as archive:
        assert not any('private' in name for name in archive.namelist())
    config['pairs'][1]['photo'] = 3
    write_json(tmp_path / 'gallery.json', config)
    with pytest.raises(ValueError, match='unique'):
        build(tmp_path / 'gallery.json', tmp_path / 'bad')
    assert not (tmp_path / 'bad').exists()


@pytest.mark.parametrize('has_audio', [True, False])
def test_actual_encode_exact_switches_full_audio_and_unscaled_video(tmp_path, has_audio):
    make_gallery(tmp_path)
    build(tmp_path / 'gallery.json', tmp_path / 'gallery')
    command = ['-v', 'error', '-f', 'lavfi', '-i', 'testsrc2=size=320x180:rate=12:duration=2']
    if has_audio:
        command += ['-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=48000:duration=2', '-c:a', 'aac']
    command += ['-vf', 'setparams=range=limited:color_primaries=bt709:color_trc=bt709:colorspace=bt709',
                '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-color_range', 'tv',
                '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
                str(tmp_path / 'source.mp4')]
    ffmpeg(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    config, work, movie = tmp_path / 'timeline.json', tmp_path / 'work', tmp_path / 'comparison.mp4'
    write_json(config, timeline())
    data = prepare(config, work)
    compose(config, work, data, movie)
    report = verify(config, work, movie)
    assert report['frames'] == 24 and report['size'] == [320, 300]
    assert bool(report['audio_packet_hash']) == has_audio
    assert {row['frame'] for row in report['frame_checks']} >= {7, 8, 15, 16}
    assert report['top_video_all_frames_ssim'] > .99
    source_hash = digest(tmp_path / 'source.mp4')
    with pytest.raises(ValueError, match='overwrite'):
        compose(config, work, data, tmp_path / 'source.mp4')
    assert digest(tmp_path / 'source.mp4') == source_hash
    changed = tmp_path / 'gallery/renders/03.png'
    changed.write_bytes(b'changed')
    with pytest.raises(ValueError, match='changed'):
        prepare(config, tmp_path / 'bad_work')
    assert not (tmp_path / 'bad_work').exists()
