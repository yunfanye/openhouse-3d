"""Blender runtime configuration. Kept separate from bpy-free workflow modules."""
import os


def pack_scene():
    """Make linked essentials/local libraries self-contained before saving."""
    import bpy
    bpy.ops.object.make_local(type='ALL')
    bpy.ops.file.pack_all()


def linked_data():
    import bpy
    return [item.name for item in bpy.data.user_map() if item.library is not None]


def configure_device(scene, device=None):
    import bpy
    requested = (device or os.environ.get('ARCHVIZ_DEVICE', 'AUTO')).upper()
    allowed = ('AUTO', 'CPU', 'OPTIX', 'CUDA', 'HIP', 'ONEAPI', 'METAL')
    if requested not in allowed:
        raise ValueError(f'Unknown Cycles device {requested}; choose {allowed}')
    scene.render.engine = 'CYCLES'
    prefs = bpy.context.preferences.addons['cycles'].preferences
    # Establish CPU state first: discovery failure must never leave a stale GPU flag.
    scene.cycles.device = 'CPU'
    scene.cycles.denoising_use_gpu = False
    if requested == 'CPU':
        print('[render] device CPU', flush=True)
        return 'CPU'
    candidates = ('OPTIX', 'CUDA', 'HIP', 'ONEAPI', 'METAL') if requested == 'AUTO' else (requested,)
    failures = []
    for backend in candidates:
        try:
            prefs.compute_device_type = backend
            prefs.refresh_devices()
        except (TypeError, RuntimeError) as error:
            failures.append(f'{backend}: {error}')
            continue
        devices = [item for item in prefs.devices if item.type == backend]
        if not devices:
            failures.append(f'{backend}: no available devices')
            continue
        for item in prefs.devices:
            item.use = item.type == backend
        scene.cycles.device = 'GPU'
        scene.cycles.denoising_use_gpu = True
        print(f'[render] device {backend}: {", ".join(item.name for item in devices)}', flush=True)
        return backend
    if requested != 'AUTO':
        raise RuntimeError('Requested GPU is unavailable: ' + '; '.join(failures))
    print('[render] AUTO selected CPU; ' + '; '.join(failures), flush=True)
    return 'CPU'
