"""Prepare or render any house's packed scene, inside Blender.

blender -b house.blend --python-exit-code 1 --python tools/render_scene.py -- --help
"""
import argparse
import json
from pathlib import Path
import sys

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from archviz import film, filmkit
from archviz.media import write_json
from archviz.rendering import configure_device, linked_data, pack_scene
import houses


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'info', 'frames', 'vectors'])
    parser.add_argument('--house')
    parser.add_argument('--shot')
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--start', type=int)
    parser.add_argument('--end', type=int)
    parser.add_argument('--device', default='AUTO')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    scene = bpy.context.scene
    if args.action == 'prepare':
        if not args.house or not args.shot:
            parser.error('prepare requires --house and --shot')
        house = houses.load(args.house)
        shot = house.BY_NAME[args.shot]
        if 'keys' in shot:
            film.bake_take(scene, shot)
        else:
            film.bake_shot(scene, shot)
        if getattr(house, 'DOORS', None):
            film.open_doors(scene, house.DOORS,
                            frame_open=round(shot.get('door_t', 0) * filmkit.FPS) + 1,
                            seconds=shot.get('door_secs', 1))
        scene.frame_start, scene.frame_end = 1, filmkit.frames_of(shot)
        scene.render.fps, scene.render.fps_base = filmkit.FPS, 1
        scene.render.use_motion_blur = True
        scene.render.motion_blur_shutter = .45
        scene.cycles.use_animated_seed = True
        scene['archviz_house'], scene['archviz_shot'] = args.house, shot['name']
        scene.frame_set(1)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        pack_scene()
        bpy.ops.wm.save_as_mainfile(filepath=str(args.out.resolve()))
        return
    if args.action == 'info':
        if not scene.camera:
            raise ValueError('Scene has no active camera')
        size = [int(scene.render.resolution_x * scene.render.resolution_percentage / 100),
                int(scene.render.resolution_y * scene.render.resolution_percentage / 100)]
        missing = [image.filepath for image in bpy.data.images
                   if image.source == 'FILE' and not image.packed_file
                   and not Path(bpy.path.abspath(image.filepath)).is_file()]
        if missing:
            raise ValueError(f'Scene has missing external textures: {missing}')
        unpacked = [image.filepath for image in bpy.data.images if image.source == 'FILE' and not image.packed_file]
        if unpacked:
            raise ValueError('Pack textures before production; external files are outside the scene fingerprint: ' + str(unpacked))
        linked = linked_data()
        if linked:
            raise ValueError(f'Make linked library data local before freezing production: {linked}')
        device = configure_device(scene, args.device)
        devices = [item.name for item in bpy.context.preferences.addons['cycles'].preferences.devices if item.use]
        write_json(args.out, {'start': scene.frame_start, 'end': scene.frame_end,
                             'fps': scene.render.fps / scene.render.fps_base, 'size': size,
                             'blender_version': bpy.app.version_string, 'camera': scene.camera.name,
                             'device': device, 'devices': devices if device != 'CPU' else ['CPU']})
        return
    if args.start is None or args.end is None or args.start < 1 or args.end < args.start:
        parser.error('frames/vectors require a positive inclusive --start / --end range')
    configure_device(scene, args.device)
    args.out.mkdir(parents=True, exist_ok=True)
    folder = args.out.resolve()
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.image_settings.color_depth = '8'
    scene.render.use_overwrite = False
    scene.render.use_persistent_data = True
    if args.action == 'frames':
        scene.frame_start, scene.frame_end, scene.frame_step = args.start, args.end, 1
        scene.render.filepath = str(folder / 'f_')
        bpy.ops.render.render(animation=True)
    else:
        film.enable_vectors(scene, str(folder))
        scene.render.use_motion_blur = False
        scene.camera.data.dof.use_dof = False
        scene.cycles.samples = 1
        scene.cycles.use_adaptive_sampling = False
        scene.cycles.use_denoising = False
        scene.cycles.max_bounces = 0
        scene.cycles.pixel_filter_type, scene.cycles.filter_width = 'BOX', .01
        for frame in range(args.start, args.end + 1):
            if (folder / f'v_{frame:04d}.exr').exists():
                continue
            scene.frame_set(frame)
            scene.frame_start = scene.frame_end = frame
            scene.render.filepath = str(folder / '_vector_scratch_')
            bpy.ops.render.render(animation=True)
        for path in folder.glob('_vector_scratch_*.png'):
            path.unlink()


if __name__ == '__main__':
    main()
