from types import SimpleNamespace
import sys

import pytest

from archviz.rendering import configure_device


def scene_and_devices(monkeypatch, devices):
    prefs = SimpleNamespace(devices=devices, compute_device_type='', refresh_devices=lambda: None)
    bpy = SimpleNamespace(context=SimpleNamespace(preferences=SimpleNamespace(
        addons={'cycles': SimpleNamespace(preferences=prefs)})))
    monkeypatch.setitem(sys.modules, 'bpy', bpy)
    scene = SimpleNamespace(render=SimpleNamespace(), cycles=SimpleNamespace(device='GPU', denoising_use_gpu=True))
    return scene


def test_cpu_clears_old_gpu_flags(monkeypatch):
    scene = scene_and_devices(monkeypatch, [])
    assert configure_device(scene, 'CPU') == 'CPU'
    assert scene.cycles.device == 'CPU'
    assert not scene.cycles.denoising_use_gpu


def test_auto_reports_cpu_when_no_gpus(monkeypatch, capsys):
    scene = scene_and_devices(monkeypatch, [])
    assert configure_device(scene, 'AUTO') == 'CPU'
    assert 'no available devices' in capsys.readouterr().out


def test_explicit_unavailable_gpu_fails(monkeypatch):
    scene = scene_and_devices(monkeypatch, [])
    with pytest.raises(RuntimeError, match='unavailable'):
        configure_device(scene, 'METAL')
    assert scene.cycles.device == 'CPU'


def test_gpu_enables_only_selected_backend(monkeypatch):
    devices = [SimpleNamespace(type=kind, name=kind, use=False) for kind in ('CPU', 'METAL', 'CUDA')]
    scene = scene_and_devices(monkeypatch, devices)
    assert configure_device(scene, 'METAL') == 'METAL'
    assert [d.type for d in devices if d.use] == ['METAL']
    assert scene.cycles.denoising_use_gpu
