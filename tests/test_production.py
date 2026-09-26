from pathlib import Path
from unittest.mock import patch
import subprocess

from PIL import Image
import pytest

from archviz.production import bind_run, missing_frames, run_worker


def test_resume_rejects_changed_inputs_and_unknown_frames(tmp_path):
    bind_run(tmp_path, {'scene': 'one'})
    bind_run(tmp_path, {'scene': 'one'})
    with pytest.raises(ValueError, match='changed'):
        bind_run(tmp_path, {'scene': 'two'})
    other = tmp_path / 'unknown'
    (other / 'frames/shot').mkdir(parents=True)
    (other / 'frames/shot/f_0001.png').touch()
    with pytest.raises(ValueError, match='Unidentified'):
        bind_run(other, {'scene': 'one'})


def test_resume_checks_real_image_integrity(tmp_path):
    Image.new('RGB', (32, 32)).save(tmp_path / 'f_0001.png')
    assert missing_frames(tmp_path, 1, 3, [32, 32]) == [2, 3]
    (tmp_path / 'f_0002.png').write_bytes(b'partial PNG')
    with pytest.raises(ValueError, match='Invalid completed frame'):
        missing_frames(tmp_path, 1, 3, [32, 32])


def test_worker_retries_are_bounded(tmp_path):
    with patch('archviz.production.subprocess.Popen') as spawn:
        spawn.return_value.wait.return_value = 1
        with pytest.raises(RuntimeError, match='2 attempts'):
            run_worker(['blender'], tmp_path / 'run.log', 10)
        assert spawn.call_count == 2


def test_timeout_terminates_only_owned_process(tmp_path):
    with patch('archviz.production.subprocess.Popen') as spawn:
        spawn.return_value.wait.side_effect = [subprocess.TimeoutExpired('blender', 1), 0]
        with pytest.raises(RuntimeError):
            run_worker(['blender'], tmp_path / 'run.log', 1, attempts=1)
        spawn.return_value.terminate.assert_called_once()
        spawn.return_value.kill.assert_not_called()
