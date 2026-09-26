"""Prepare, audit and render the self-contained Alpine scene in headless Blender.

blender -b houses/alpine/output/alpine.blend --python houses/alpine/film_scene.py -- prepare
blender -b houses/alpine/output/alpine_cinematic.blend --python houses/alpine/film_scene.py -- audit
blender -b houses/alpine/output/alpine_cinematic.blend --python houses/alpine/film_scene.py -- storyboard
blender -b houses/alpine/output/alpine_cinematic.blend --python houses/alpine/film_scene.py -- frames 1 1536
"""
import sys,math,json,time,os
from pathlib import Path
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from archviz import film,filmkit
from houses.alpine import house as H
S=bpy.context.scene;OUT=ROOT/'houses/alpine/output';FILM=OUT/'film'
REVIEW=Path(os.environ.get('ALPINE_REVIEW_DIR',str(FILM)))
REVIEW.mkdir(parents=True,exist_ok=True)
DRAFT=Path(os.environ.get('ALPINE_DRAFT_DIR',str(FILM/'draft_quarter')))
SAVE_SCENE=Path(os.environ.get('ALPINE_SAVE_SCENE',str(OUT/'alpine_cinematic.blend')))
filmkit.configure(str(FILM))
args=sys.argv[sys.argv.index('--')+1:];mode=args[0]

p=bpy.context.preferences.addons['cycles'].preferences
p.compute_device_type='METAL'
# Use generic Metal kernels for reliable rendering of this scene; image settings are unchanged.
p.kernel_optimization_level=os.environ.get('ALPINE_METAL_OPTIMIZATION','OFF')
p.metalrt=os.environ.get('ALPINE_METAL_RT','OFF')
p.refresh_devices()
for d in p.devices:d.use=d.type=='METAL'
S.cycles.device='GPU';S.cycles.denoising_use_gpu=True

if mode=='prepare':
    H.setup_scene(S)
    from archviz.mesh import look_at
    for name,(loc,tgt,lens) in H.CAMS.items():
        ob=bpy.data.objects.get('Cam_'+name)
        if not ob:
            cd=bpy.data.cameras.new('Cam_'+name);ob=bpy.data.objects.new('Cam_'+name,cd);bpy.context.scene.collection.objects.link(ob)
        ob.location=loc;ob.data.lens=lens;look_at(ob,tgt)
    film.bake_take(S,H.TAKE)
    # Quaternion signs are made continuous for correct subframe motion blur.
    pos_f,tgt_f,*_=film.take_curves(H.TAKE);prev=None;flips=0
    focus_curve=None
    if any(k.get('focus') is not None for k in H.TAKE['keys']):
        focus_curve=film._hermite_t([k['t'] for k in H.TAKE['keys']],[k.get('focus') if k.get('focus') is not None else (Vector(k['tgt'])-Vector(k['cam'])).length for k in H.TAKE['keys']])
    for fr in range(1,1538):
        t=(fr-1)/24;q=(tgt_f(t)-pos_f(t)).to_track_quat('-Z','Y')
        if prev is not None and q.dot(prev)<0:q.negate();flips+=1
        S.camera.rotation_quaternion=q;S.camera.keyframe_insert('rotation_quaternion',frame=fr);prev=q.copy()
        if focus_curve is not None:
            S.camera.data.dof.focus_distance=max(.4,focus_curve(t).x);S.camera.data.keyframe_insert('dof.focus_distance',frame=fr)
    S['quaternion_hemisphere_corrections']=flips
    film.open_doors(S,H.DOORS,frame_open=round(H.TAKE['door_t']*24)+1,seconds=H.TAKE['door_secs'])
    S.render.resolution_x=1920;S.render.resolution_y=1080;S.render.resolution_percentage=100
    S.render.fps=24;S.frame_end=1536
    S.render.use_motion_blur=True;S.render.motion_blur_shutter=.42
    S.cycles.samples=96;S.cycles.adaptive_threshold=.025;S.cycles.adaptive_min_samples=24
    S.cycles.diffuse_bounces=6;S.cycles.max_bounces=14;S.cycles.sample_clamp_indirect=5
    S.cycles.use_animated_seed=True;S.render.use_persistent_data=True
    S.render.image_settings.file_format='PNG';S.render.image_settings.color_mode='RGB';S.render.image_settings.color_depth='8';S.render.image_settings.compression=20
    S.render.use_overwrite=False
    S['revision']=os.environ.get('ALPINE_REVISION','alpine_v4')
    S['source_listing']='https://www.zillow.com/homedetails/805-N-Alpine-Dr-Beverly-Hills-CA-90210/20519812_zpid/'
    S['reconstruction']='Photo-derived architecture with inferred dimensions and room connections; virtual staging. Not a measured survey.'
    S['film']='64 seconds, 24 fps, one continuous camera movement. Native rendered frames, no internal cuts.'
    for marker in list(S.timeline_markers):S.timeline_markers.remove(marker)
    for k in H.TAKE['keys']:S.timeline_markers.new(k['label'],frame=round(k['t']*24)+1)
    for source in ('plan.py','shots.py','house.py'):
        text=bpy.data.texts.get('ALPINE_'+source) or bpy.data.texts.new('ALPINE_'+source)
        text.clear();text.write((ROOT/'houses/alpine'/source).read_text())
    # Quiet water movement and irregular flame motion.
    water=bpy.data.materials.get('Alpine | still rippling water')
    if water:
        for n in water.node_tree.nodes:
            if n.type=='TEX_WAVE':n.inputs['Phase Offset'].driver_add('default_value').driver.expression='frame * .013'
    for ob in bpy.data.objects:
        if ob.type=='MESH' and ob.name.endswith('| flame tongues') and not ob.modifiers.get('Small flame motion'):
            tex=bpy.data.textures.new(ob.name+' noise',type='CLOUDS');tex.noise_scale=.12
            mod=ob.modifiers.new('Small flame motion','DISPLACE');mod.texture=tex;mod.strength=.018
            mod.driver_add('strength').driver.expression='.018+.007*sin(frame*.23)+.004*sin(frame*.57)'
    S.frame_set(1);S.render.filepath=str(FILM/'frames/take/f_')
    bpy.ops.wm.save_as_mainfile(filepath=str(SAVE_SCENE))
    print('[alpine] Cinematic scene prepared',flush=True)
elif mode=='draft':
    folder=DRAFT/'frames';folder.mkdir(parents=True,exist_ok=True)
    S.render.resolution_x=int(os.environ.get('ALPINE_DRAFT_WIDTH','960'));S.render.resolution_y=int(os.environ.get('ALPINE_DRAFT_HEIGHT','540'));S.render.resolution_percentage=100
    S.cycles.samples=24;S.cycles.adaptive_threshold=.075;S.cycles.adaptive_min_samples=8
    S.frame_start=int(args[1]) if len(args)>1 else 1
    S.frame_end=int(args[2]) if len(args)>2 else 1536
    S.frame_step=4;S.render.fps=24
    S.render.filepath=str(folder/'f_');S.render.use_file_extension=True
    S.render.use_overwrite=False;S.render.use_placeholder=False
    if os.environ.get('ALPINE_DRAFT_EXECUTION','INDEPENDENT')=='NATIVE':
        S.render.use_persistent_data=True
        previous=[time.time()]
        def draft_written(sc):
            now=time.time();print(f'[alpine draft] frame {sc.frame_current}/1536 {now-previous[0]:.2f} sec native software intersections',flush=True);previous[0]=now
        bpy.app.handlers.render_write.append(draft_written)
        bpy.ops.render.render(animation=True)
    else:
        # Independent frame renders are the conservative fallback for GPU/session stalls.
        S.render.use_persistent_data=False
        for f in range(S.frame_start,S.frame_end+1,4):
            path=folder/f'f_{f:04d}.png'
            if path.exists():continue
            S.frame_set(f);S.render.filepath=str(path);started=time.time()
            bpy.ops.render.render(write_still=True)
            print(f'[alpine draft] frame {f}/1536 {time.time()-started:.2f} sec independent',flush=True)
elif mode=='audit':
    nearest=[];blocked=[];speeds=[];pans=[];last=None
    dirs=[Vector((x,y,z)).normalized() for x in (-1,0,1) for y in (-1,0,1) for z in (-1,0,1) if (x,y,z)!=(0,0,0)]
    dg=bpy.context.evaluated_depsgraph_get()
    for f in range(1,1537,3):
        S.frame_set(f);cam=S.camera;loc=cam.location.copy();d=cam.rotation_quaternion@Vector((0,0,-1))
        if last:
            speeds.append((f,(loc-last[0]).length*8));pans.append((f,math.degrees(d.angle(last[1]))*8))
        last=(loc,d)
        best=(1,None)
        for v in dirs:
            hit,pt,normal,idx,ob,matrix=S.ray_cast(dg,loc,v,distance=.40)
            if hit and ob.type=='MESH' and (pt-loc).length<best[0]:best=((pt-loc).length,ob.name)
        if best[0]<.30:nearest.append(dict(frame=f,distance=round(best[0],3),object=best[1]))
        hit,pt,normal,idx,ob,matrix=S.ray_cast(dg,loc,d,distance=.22)
        if hit and ob.type=='MESH':blocked.append(dict(frame=f,object=ob.name,distance=round((pt-loc).length,3)))
    data=dict(frames=1536,fps=24,duration_seconds=64,peak_speed_mps=max(speeds,key=lambda x:x[1]),peak_pan_degrees_sec=max(pans,key=lambda x:x[1]),lens_obstructions=blocked,clearances_under_30cm=nearest)
    (REVIEW/'camera_audit.json').write_text(json.dumps(data,indent=2));print(json.dumps(data,indent=2),flush=True)
elif mode in ('storyboard','workbench','frames','stills','test'):
    if mode in ('storyboard','workbench'):
        folder=REVIEW/mode;frames=list(range(1,1537,48))+[1536]
        S.render.resolution_percentage=50;S.cycles.samples=48;S.cycles.adaptive_min_samples=16
        if mode=='workbench':
            S.render.engine='BLENDER_WORKBENCH';S.render.use_motion_blur=False;S.display.shading.light='STUDIO';S.display.shading.color_type='MATERIAL'
            S.render.resolution_percentage=33;frames=list(range(1,1537,12))+[1536]
    elif mode=='test':
        folder=REVIEW/'tests';frames=[int(x) for x in args[1:]]
        S.cycles.samples=int(os.environ.get('ALPINE_CHECK_SAMPLES','64'));S.cycles.adaptive_min_samples=min(24,S.cycles.samples)
        S.render.resolution_percentage=int(os.environ.get('ALPINE_CHECK_SCALE','100'))
    elif mode=='stills':
        folder=OUT/'stills';folder.mkdir(exist_ok=True)
        S.animation_data_clear();S.render.use_motion_blur=False;S.cycles.samples=192;S.cycles.adaptive_threshold=.012
        S.render.resolution_x=2560;S.render.resolution_y=1440
        for name in (args[1:] or H.CAMS):
            S.camera=bpy.data.objects['Cam_'+name];S.view_settings.exposure=H.EXPOSURE_DEFAULT['ext' if name in H.EXT else 'int']
            S.render.filepath=str(folder/(name+'.png'));bpy.ops.render.render(write_still=True);print('[alpine] still',name,flush=True)
        sys.exit(0)
    else:
        folder=FILM/'frames/take';folder.mkdir(parents=True,exist_ok=True)
        S.frame_start=int(args[1]);S.frame_end=int(args[2]);S.frame_step=1
        S.render.filepath=str(folder/'f_');S.render.use_file_extension=True
        S.render.use_overwrite=False;S.render.use_placeholder=False
        previous=[time.time()]
        def frame_written(sc):
            now=time.time();print(f'[alpine] frames {sc.frame_current}/1536 {now-previous[0]:.2f} sec native',flush=True);previous[0]=now
        bpy.app.handlers.render_write.append(frame_written)
        bpy.ops.render.render(animation=True)
        sys.exit(0)
    folder.mkdir(parents=True,exist_ok=True)
    for f in frames:
        path=folder/f'f_{f:04d}.png'
        if path.exists() and mode=='frames':continue
        S.frame_set(f);S.render.filepath=str(path);t=time.time()
        bpy.ops.render.render(write_still=True)
        print(f'[alpine] {mode} {f}/1536 {time.time()-t:.2f} sec',flush=True)
else:raise ValueError(mode)
