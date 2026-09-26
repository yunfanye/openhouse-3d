"""Prepare, inspect, and render the packed Webster cinematic scene headlessly.

blender -b houses/webster/output/webster_cinematic.blend --python houses/webster/film_scene.py -- prepare
blender -b houses/webster/output/webster_cinematic.blend --python houses/webster/film_scene.py -- storyboard
python houses/webster/finish_film.py --device METAL
"""
import os
import sys
import math
import json
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from archviz import film, filmkit
from houses.webster import house as H

OUT=ROOT/'houses/webster/output'
FOLDER=Path(os.environ.get('WEBSTER_FILM_DIR',str(OUT/'film')))
FOLDER.mkdir(parents=True,exist_ok=True)
BLEND=Path(os.environ.get('WEBSTER_FILM_BLEND',str(OUT/'webster_cinematic.blend')))
filmkit.configure(str(FOLDER))
S=bpy.context.scene
argv=sys.argv[sys.argv.index('--')+1:]
mode=argv[0]


def gpu():
    from archviz.rendering import configure_device
    configure_device(S)


def prepare():
    film.bake_take(S,H.TAKE)
    if not bpy.data.objects['Entry_Door'].get('film_hinge'):
        film.open_doors(S,H.DOORS,frame_open=round(H.TAKE['door_t']*24)+1,seconds=H.TAKE['door_secs'])
    S.render.resolution_x=1920;S.render.resolution_y=1080;S.render.resolution_percentage=100
    S.render.use_motion_blur=True;S.render.motion_blur_shutter=.45
    S.cycles.samples=96;S.cycles.adaptive_threshold=.025;S.cycles.adaptive_min_samples=24
    S.cycles.use_animated_seed=True;S.cycles.diffuse_bounces=6
    S.render.use_persistent_data=True
    S.render.image_settings.file_format='PNG';S.render.image_settings.color_mode='RGB'
    S.render.image_settings.color_depth='8';S.render.image_settings.compression=25
    for ob in bpy.data.objects:
        if ob.type=='LIGHT' and ob.data.type in ('POINT','SPOT'):
            ob.data.shadow_soft_size=max(.08,ob.data.shadow_soft_size)
    # Tiny irregular flame movement and a subdued, correlated warm light variation.
    fire=bpy.data.objects.get('Front_Fire')
    if fire and not fire.modifiers.get('Flame turbulence'):
        tex=bpy.data.textures.new('Webster_FlameNoise',type='CLOUDS');tex.noise_scale=.11;tex.noise_depth=2
        mod=fire.modifiers.new('Flame turbulence','DISPLACE');mod.texture=tex;mod.strength=.025;mod.mid_level=.45
        driver=mod.driver_add('strength').driver
        driver.expression='.026 + .009*sin(frame*.39) + .005*sin(frame*.73)'
        light=bpy.data.objects.get('L_Front_Fire')
        light.data.driver_add('energy').driver.expression='24 + 1.3*sin(frame*.39) + .7*sin(frame*.73)'
    for m in S.timeline_markers: S.timeline_markers.remove(m)
    for key in H.TAKE['keys']:
        S.timeline_markers.new(key['label'],frame=round(key['t']*24)+1)
    S['visualization']='Photo-derived architectural reconstruction with virtual staging; inferred dimensions, not a measured survey.'
    S['source_listing']='https://www.zillow.com/homedetails/1836-Webster-St-Palo-Alto-CA-94301/19496464_zpid/'
    S['film_description']='One continuous 64-second camera; 24 fps; no internal cuts or dissolves.'
    S.frame_set(1)
    S.render.filepath=str(FOLDER/'frames/cinematic/f_')
    S.render.use_overwrite=False
    from archviz.rendering import pack_scene
    pack_scene()
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    print('[cinematic] Prepared packed animated scene.',flush=True)


def audit():
    from archviz.camera_audit import audit as inspect
    from archviz.media import write_json
    report = inspect(S)
    write_json(FOLDER / 'camera_audit.json', report)
    if report['lens_obstructions']:
        raise ValueError('Camera lens intersects geometry; inspect camera_audit.json')


gpu()
if mode=='prepare':
    prepare()
elif mode=='audit':
    audit()
elif mode=='storyboard':
    folder=FOLDER/'storyboard';folder.mkdir(exist_ok=True)
    S.render.resolution_percentage=50;S.cycles.samples=48;S.cycles.adaptive_min_samples=16
    proof_frames=[int(f) for f in argv[1].split(',')] if len(argv)>1 else range(S.frame_start, S.frame_end + 1, 48)
    for fr in proof_frames:
        S.frame_set(fr);S.render.filepath=str(folder/f'f_{fr:04d}.png')
        bpy.ops.render.render(write_still=True)
        print('[cinematic] storyboard',fr,flush=True)
elif mode=='stills':
    S.animation_data_clear();S.frame_set(1)
    S.render.use_motion_blur=False;S.cycles.samples=128;S.cycles.adaptive_threshold=.02
    folder=OUT/'renders_cinematic';folder.mkdir(exist_ok=True)
    for name in H.CAMS:
        S.camera=bpy.data.objects['Cam_'+name]
        S.view_settings.exposure=H.EXPOSURE.get(name,H.EXPOSURE_DEFAULT['ext' if name in H.EXT else 'int'])
        S.render.filepath=str(folder/(name+'.png'))
        bpy.ops.render.render(write_still=True)
        print('[cinematic] still',name,flush=True)

else:
    raise ValueError(mode)
