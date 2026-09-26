"""Render photo-matched stills from a saved candidate; never starts the film."""
from pathlib import Path
import sys,json,time
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from houses.webster import house as H
OUT=ROOT/'houses/webster/output/consistency_review'
S=bpy.context.scene;S.frame_set(1);S.animation_data_clear()
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
action=args[0] if args else 'preview'
for name,(loc,tgt,lens) in H.CAMS.items():
    ob=bpy.data.objects.get('Cam_'+name)
    if ob is None:
        cd=bpy.data.cameras.new('Cam_'+name);ob=bpy.data.objects.new('Cam_'+name,cd);S.collection.objects.link(ob)
    ob.location=loc;ob.rotation_euler=(Vector(tgt)-ob.location).to_track_quat('-Z','Y').to_euler()
    ob.data.lens=lens;ob.data.sensor_width=36;ob.data.dof.use_dof=False;ob.data.clip_start=.035
S.camera=bpy.data.objects['Cam_hero']
if action=='save':
    S.render.engine='CYCLES';S.render.resolution_x=1920;S.render.resolution_y=1280;S.render.resolution_percentage=100
    S.view_settings.exposure=.6;S.cycles.samples=128;S.cycles.adaptive_threshold=.015
    bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath);raise SystemExit
S.render.resolution_x=1280 if action=='preview' else 1920
S.render.resolution_y=853 if action=='preview' else 1280
S.render.resolution_percentage=100;S.render.image_settings.file_format='PNG'
S.render.use_motion_blur=False;S.render.use_compositing=True
from archviz.rendering import configure_device
configure_device(S, 'CPU' if '--cpu' in args else None)
S.cycles.samples=48 if action=='preview' else 128;S.cycles.adaptive_threshold=.035 if action=='preview' else .015
S.cycles.adaptive_min_samples=16 if action=='preview' else 32
S.render.use_persistent_data=True
if '--cpu' in args:
    # Bounded CPU-only stills can run without allocating the occupied Metal device.
    S.cycles.device='CPU';S.cycles.denoising_use_gpu=False
    S.render.threads_mode='FIXED';S.render.threads=8
folder=OUT/action;folder.mkdir(parents=True,exist_ok=True)
keys=args[1].split(',') if len(args)>1 else [k for k,p in H.PHOTO_PAIRS]
for name in keys:
    S.camera=bpy.data.objects['Cam_'+name]
    S.view_settings.exposure=H.EXPOSURE.get(name,H.EXPOSURE_DEFAULT['ext' if name in H.EXT else 'int'])
    S.render.filepath=str(folder/(name+'.png'))
    bpy.ops.render.render(write_still=True)
    (OUT/'render_progress.json').write_text(json.dumps({'stage':action,'last_completed':name,'time':time.time(),'scope':'architectural comparison stills'},indent=2))
    print('[comparison]',name,flush=True)
