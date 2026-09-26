"""Still previews and roof-coverage checks; does not render or resume the film.

blender -b <blend> --python houses/webster/roof_review.py -- <output-dir> [--audit]
"""
import json
import math
import sys
from pathlib import Path
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from houses.webster import plan as P
from houses.webster import exterior as E

args=sys.argv[sys.argv.index('--')+1:]
OUT=Path(args[0]);OUT.mkdir(parents=True,exist_ok=True)
S=bpy.context.scene
S.frame_set(1)


def audit():
    from houses.webster import roof_form as R
    dg=bpy.context.evaluated_depsgraph_get()
    front=BVHTree.FromObject(bpy.data.objects['Ext_FrontRoof_Deck'],dg)
    front_tiles=BVHTree.FromObject(bpy.data.objects['Ext_FrontRoof_Tiles'],dg)
    upper=BVHTree.FromObject(bpy.data.objects['Ext_RoofSoffit'],dg)
    upper_tiles=BVHTree.FromObject(bpy.data.objects['Ext_RoofTile'],dg)
    checks={};failures=[]
    def coverage(label,domains,height,deck,tiles):
        count=0;miss=[];tile_miss=[]
        x0=min(x for poly in domains for x,y in poly);x1=max(x for poly in domains for x,y in poly)
        y0=min(y for poly in domains for x,y in poly);y1=max(y for poly in domains for x,y in poly)
        nx=int((x1-x0)/.13);ny=int((y1-y0)/.13)
        for i in range(nx):
            for j in range(ny):
                x=x0+(i+.5)*(x1-x0)/nx;y=y0+(j+.5)*(y1-y0)/ny
                if not any(R.inside(poly,x,y) for poly in domains):continue
                count+=1;expected=height(x,y)
                h=deck.ray_cast(Vector((x,y,8)),Vector((0,0,-1)),8)[0]
                ht=tiles.ray_cast(Vector((x,y,8)),Vector((0,0,-1)),8)[0]
                if h is None or abs(h.z-(expected-.009))>.015:miss.append((round(x,3),round(y,3)))
                if ht is None or ht.z<expected-.03:tile_miss.append((round(x,3),round(y,3)))
        checks[label]={'samples':count,'deck_misses':miss,'tile_misses':tile_miss}
        failures.extend(miss)
    coverage('front_roof',R.FRONT_DOMAINS,R.front_height,front,front_tiles)
    coverage('upper_roof',[R.UPPER_MAIN,R.UPPER_WING],R.upper_height,upper,upper_tiles)
    # Verify every sampled roof can descend to an exterior edge without a local sink.
    def drainage(domains,height,spacing,upper_roof=False):
        result=[];total=0
        x0=min(x for p in domains for x,y in p);x1=max(x for p in domains for x,y in p)
        y0=min(y for p in domains for x,y in p);y1=max(y for p in domains for x,y in p)
        directions=[(math.cos(i*math.tau/16),math.sin(i*math.tau/16)) for i in range(16)]
        for i in range(int((x1-x0)/spacing)):
            for j in range(int((y1-y0)/spacing)):
                x=x0+(i+.5)*spacing;y=y0+(j+.5)*spacing
                if not any(R.inside(p,x,y) for p in domains):continue
                total+=1;start=(x,y);escaped=False
                for k in range(1200):
                    h=height(x,y);candidates=[]
                    if upper_roof:
                        groups=[planes for poly,planes in ((R.UPPER_MAIN,R.UPPER_MAIN_PLANES),(R.UPPER_WING,R.UPPER_WING_PLANES)) if R.inside(poly,x,y)]
                        group=max(groups,key=lambda planes:min(R.value(p,x,y) for p in planes))
                        plane=min(group,key=lambda p:R.value(p,x,y))
                    else:plane=max(R.FRONT_PLANES,key=lambda p:R.value(p,x,y))
                    for dx,dy in directions:
                        xx,yy=x+.055*dx,y+.055*dy
                        inside=any(R.inside(p,xx,yy) for p in domains)
                        hh=height(xx,yy) if inside else h+.055*(plane[0]*dx+plane[1]*dy)
                        if hh<h-1e-6:candidates.append((hh,xx,yy,inside))
                    if not candidates:break
                    hh,x,y,within=min(candidates)
                    if not within:escaped=True;break
                if not escaped:result.append(start)
        return {'traces':total,'internal_sinks':result}
    checks['front_drainage']=drainage(R.FRONT_DOMAINS,R.front_height,.70)
    checks['upper_drainage']=drainage([R.UPPER_MAIN,R.UPPER_WING],R.upper_height,.85,True)
    clearances=[];window_conflicts=[]
    for x in (-1.05,-.5,0,.5,.95):
        for y in (.35,1.,1.80,1.86,2.1,3.,4.5,5.7):
            ceiling=P.ENTRY_VEST_ZC if y<P.ENTRY_VEST_Y1 else P.Z_MC
            bottom=front.ray_cast(Vector((x,y,ceiling)),Vector((0,0,1)),3.)[0]
            if bottom:clearances.append(bottom.z-ceiling)
    for name in ('Wic2WF','StairW1','StairW2','PrimWF'):
        o=P.BY_NAME[name]
        max_roof=max(R.front_height(o['a0']+(o['a1']-o['a0'])*i/20,6)+.075 for i in range(21))
        if max_roof>=o['z0']:window_conflicts.append(name)
    checks['minimum_clearance_above_entry_ceiling_m']=min(clearances)
    checks['front_window_aperture_conflicts']=window_conflicts
    protrusions=[]
    cx0,cx1,cy0,cy1,_=P.CHIMNEY
    for v in bpy.data.objects['Ext_Walls_Stucco'].data.vertices:
        x,y,z=v.co
        if not (-5.751<=x<=5.751 and -.01<=y<5.99 and z>P.Z_ROOF1):continue
        if cx0-.08<=x<=cx1+.08 and cy0-.08<=y<=cy1+.08:continue
        if z>R.front_height(x,y)+.025:protrusions.append((round(x,3),round(y,3),round(z,3)))
    checks['front_wall_vertices_above_roof']=protrusions
    checks['raised_front_parapet_walls']=[w for w in P.WALLS if w['kind']=='par' and w['z0']>=P.Z_ROOF1 and w['a0']<6 and w['along']=='Y']
    checks['remaining_enclosures']='Photographed side terrace and front porch only.'
    (OUT/'roof_audit.json').write_text(json.dumps(checks,indent=2))
    print(json.dumps(checks,indent=2),flush=True)
    assert not failures,'Missing roof deck coverage'
    assert not checks['front_drainage']['internal_sinks'] and not checks['upper_drainage']['internal_sinks']
    assert not window_conflicts and min(clearances)>.02
    assert not checks['raised_front_parapet_walls']
    assert not protrusions,'Front wall geometry protrudes above roofing'


if '--audit' in args:audit()
if '--audit-only' in args:sys.exit(0)

if '--beauty' in args:
    from archviz.rendering import configure_device
    configure_device(S)
    S.render.resolution_x=1600;S.render.resolution_y=1000;S.render.resolution_percentage=100
    S.cycles.samples=80;S.cycles.adaptive_threshold=.025
    S.render.use_motion_blur=False;S.animation_data_clear();S.view_settings.exposure=.6
    for name,loc,tgt,lens in [('hero_beauty',(0,-15.5,1.6),(0,30,1.6),35),
                              ('elevated_beauty',(7.2,-12,9.2),(-.45,2.7,3.),43)]:
        data=bpy.data.cameras.new(name);data.lens=lens;data.sensor_width=36
        cam=bpy.data.objects.new(name,data);S.collection.objects.link(cam);cam.location=loc
        cam.rotation_euler=(Vector(tgt)-cam.location).to_track_quat('-Z','Y').to_euler()
        S.camera=cam;S.render.filepath=str(OUT/(name+'.png'))
        bpy.ops.render.render(write_still=True)
    sys.exit(0)

# Neutral architectural proof: reveal roof structure instead of hiding it behind foliage.
for ob in bpy.data.objects:
    if ob.type=='MESH' and not ob.name.startswith(('Ext_','Entry_Door')):
        ob.hide_render=True
    if ob.type=='LIGHT':ob.hide_render=True
for m in bpy.data.materials:
    name=m.name.lower()
    if 'claytiles' in name or 'claytile' in name:m.diffuse_color=(.58,.24,.095,1)
    elif 'rooftorch' in name:m.diffuse_color=(.36,.40,.41,1)
    elif 'glass' in name:m.diffuse_color=(.19,.28,.33,1)
    elif 'stucco' in name or 'wallgrey' in name:m.diffuse_color=(.67,.73,.75,1)
    elif 'galvan' in name:m.diffuse_color=(.37,.40,.41,1)
    else:m.diffuse_color=(.84,.85,.83,1)
S.render.engine='BLENDER_WORKBENCH'
S.render.resolution_x=1600;S.render.resolution_y=1000;S.render.resolution_percentage=100
S.render.image_settings.file_format='PNG';S.render.image_settings.color_mode='RGB'
S.render.use_compositing=False;S.render.use_sequencer=False;S.render.use_motion_blur=False
S.view_settings.view_transform='Standard';S.view_settings.look='None';S.view_settings.exposure=0
S.animation_data_clear()
sh=S.display.shading;sh.light='STUDIO';sh.color_type='MATERIAL'
sh.show_shadows=True;sh.show_cavity=True;sh.cavity_type='BOTH'
sh.curvature_ridge_factor=1.15;sh.curvature_valley_factor=1.1
sh.cavity_ridge_factor=1.1;sh.cavity_valley_factor=1.15
sh.background_type='WORLD';S.world.color=(.055,.07,.085)
S.display.render_aa='32'

views={
    'front':((0,-15.5,1.6),(0,30,1.6),35),
    'elevated':((7.2,-12,9.2),(-.45,2.7,3.0),43),
    'roof_close':((4.8,-7.6,8.8),(-.65,1.4,3.0),50),
}
if '--drainage' in args:
    from houses.webster import roof_form as R
    from archviz.mesh import MB
    mat=bpy.data.materials.new('Review_RunoffArrows');mat.diffuse_color=(1.0,.57,.07,1)
    arrows=MB()
    def arrow(points):
        path=[Vector((x,y,R.front_height(x,y)+.13)) for x,y in points]
        arrows.path_tube([tuple(p) for p in path],.028,seg=10)
        direction=(path[-1]-path[-2]).normalized()
        arrows.tube(tuple(path[-1]-direction*.22),tuple(path[-1]+direction*.04),.11,.002,seg=12)
    arrow([(-4.5,4.5),(-3.6,4.448),(-2.7,4.395)])
    arrow([(4.3,5.2),(4.3,3.5),(4.3,1.42)])
    valley=[]
    for y in (5.2,4.2,3.2,2.2,1.2,.45):
        x=(R.value(R.FRONT_PORCH,0,y)-R.FRONT_DIAGONAL[1]*y-R.FRONT_DIAGONAL[2])/R.FRONT_DIAGONAL[0]
        valley.append((x,y))
    arrow(valley)
    arrows.build('Review_RunoffArrows',mat,coll='Review',smooth=True)
    views={'drainage':views['elevated']}
for name,(loc,tgt,lens) in views.items():
    data=bpy.data.cameras.new('RoofReview_'+name);data.lens=lens;data.sensor_width=36;data.clip_start=.05
    cam=bpy.data.objects.new(data.name,data);S.collection.objects.link(cam)
    cam.location=loc;cam.rotation_euler=(Vector(tgt)-cam.location).to_track_quat('-Z','Y').to_euler()
    S.camera=cam;S.render.filepath=str(OUT/(name+'.png'))
    bpy.ops.render.render(write_still=True)
    print('[roof review]',S.render.filepath,flush=True)
