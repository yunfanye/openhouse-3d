import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import ImageFont

from archviz.media import digest, font, local_path, write_json


def test_hash_and_atomic_report(tmp_path):
    path = tmp_path / 'data'
    path.write_bytes(b'house')
    assert digest(path) == hashlib.sha256(b'house').hexdigest()
    write_json(tmp_path / 'run.json', {'count': 42})
    assert not list(tmp_path.glob('*.tmp'))


def test_paths_cannot_escape_manifest_root(tmp_path):
    assert local_path(tmp_path, 'renders/a.png') == tmp_path / 'renders/a.png'
    for path in ['../private.jpg', str(tmp_path.parent / 'secret')]:
        with pytest.raises(ValueError, match='escapes'):
            local_path(tmp_path, path)
    (tmp_path / 'link').symlink_to(tmp_path.parent, target_is_directory=True)
    with pytest.raises(ValueError, match='escapes'):
        local_path(tmp_path, 'link/private.jpg')


def test_explicit_font_fails_on_typo(monkeypatch):
    monkeypatch.setenv('ARCHVIZ_FONT', '/missing/font.ttf')
    with pytest.raises(OSError):
        font(18)


def test_discovered_font_and_bundled_font(monkeypatch):
    monkeypatch.delenv('ARCHVIZ_FONT', raising=False)
    actual = font(18)
    assert actual.getlength('House') > 0
    bundled = ImageFont.load_default(size=18)
    with patch.object(ImageFont, 'truetype', side_effect=OSError('missing')), patch.object(ImageFont, 'load_default', return_value=bundled):
        assert font(18) is bundled
