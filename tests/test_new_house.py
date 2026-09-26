from pathlib import Path
import shutil

import pytest

from tools.new_house import create


def test_scaffold_omits_generated_and_private_inputs(tmp_path):
    source = Path(__file__).resolve().parents[1] / 'houses/_template'
    shutil.copytree(source, tmp_path / 'houses/_template',
                    ignore=shutil.ignore_patterns('output', '__pycache__'))
    (tmp_path / 'houses/_template/output').mkdir()
    (tmp_path / 'houses/_template/output/private.png').touch()
    destination = create('my_house', 'My "quoted" house', tmp_path)
    assert not (destination / 'output').exists()
    config = (destination / 'house.py').read_text()
    compile(config, 'house.py', 'exec')
    assert "NAME = 'my_house'" in config
    assert (destination / 'REFERENCES.md').is_file()
    with pytest.raises(FileExistsError):
        create('my_house', 'duplicate', tmp_path)


@pytest.mark.parametrize('name', ['../outside', 'class', '_internal', 'two-houses'])
def test_scaffold_rejects_invalid_package_names(tmp_path, name):
    with pytest.raises(ValueError):
        create(name, 'house', tmp_path)
