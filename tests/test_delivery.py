from pathlib import Path

import pytest

from archviz.delivery import prune, record


def test_prune_requires_verified_final_and_preserves_it(tmp_path):
    out = tmp_path / 'output'
    final = out / 'final'
    final.mkdir(parents=True)
    (final / 'movie.mp4').write_bytes(b'accepted movie')
    old = out / 'old_frames'
    old.mkdir()
    (old / 'f_0001.png').write_bytes(b'intermediate')
    record(final)
    assert prune(out)['paths'] == ['old_frames']
    assert old.exists()
    (final / 'movie.mp4').write_bytes(b'corrupt movie')
    with pytest.raises(ValueError, match='checksum'):
        prune(out, apply=True)
    assert old.exists()
    (final / 'movie.mp4').write_bytes(b'accepted movie')
    result = prune(out, apply=True)
    assert result['deleted'] and not old.exists()
    assert (final / 'movie.mp4').read_bytes() == b'accepted movie'


def test_unknown_delivery_files_block_cleanup(tmp_path):
    final = tmp_path / 'output/final'
    final.mkdir(parents=True)
    (final / 'model.blend').write_bytes(b'model')
    record(final)
    (final / 'unreviewed.mp4').touch()
    with pytest.raises(ValueError, match='inventory differs'):
        prune(final.parent, apply=True)
