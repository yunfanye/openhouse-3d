"""805 N Alpine Drive — procedural reconstruction and cinematic presentation."""
from .plan import *
from .shots import *
NAME='alpine'
TITLE='805 North Alpine Drive, Beverly Hills'
BLEND='alpine.blend'
MODULES=['exterior','interior','site','landscape']

def materials():
    from .palette import build
    return build()
SKY=dict(sun_dir=(-.75,.45,.19),sun_energy=1.75,sun_color=(1,.80,.57),strength=.40,sun_elevation=4.0)
EXPOSURE_DEFAULT={'ext':.55,'int':.35}
DOF_DEFAULT={'ext':11,'int':8}
CAMS={
 'hero':((-12,-25,6.7),(0,2,3.7),31),
 'front':((-.2,-20,2.7),(0,0,3.5),26),
 'hall':((0,.65,2.1),(0,9.5,2.65),20),
 'stair':((0,10.2,5.65),(0,1,2.0),23),
 'living':((-4.25,7.7,2.05),(-8.3,3.7,1.6),22),
 'library':((-6,9.8,2.05),(-8,15,1.8),23),
 'dining':((4.6,1.9,2.05),(8.0,5.8,1.7),23),
 'kitchen':((5.1,15.6,2.05),(9.5,12.4,1.55),23),
 'salon':((-2.5,12.8,2.0),(1,16.6,1.6),22),
 'veranda':((10.6,19.3,1.95),(-8,20.1,2.0),25),
 'pool':((0,40.5,1.6),(0,18.5,3.4),25),
 'garden':((-5.4,76,20),(0,37,1.5),29),
 'gallery':((7.8,56,2.6),(0,66,2.5),28),
 'primary':((-4.7,9.6,UP+1.65),(-8.4,13.8,UP+1.2),23),
}
EXT=['hero','front','veranda','pool','garden','gallery']
PHOTO_PAIRS=[('front',2),('hall',3),('stair',13),('living',4),('library',6),('dining',5),('kitchen',11),('salon',8),('veranda',12),('pool',1),('garden',0),('gallery',28),('primary',14)]
DOORS=dict(static=[],entry=('Entry_Door',(-.72,0),105))
GRASS=[dict(name='Grass front island',rect=(-7.5,7.5,-13.4,-9.3),z=.028,cell=.3,padding=.04,mat='grass',count=18000,length=.029,children=7,seed=8),
 dict(name='Grass main lawn',rect=(-12.45,12.45,21.6,42.2),z=-.021,holes=[(-9.4,9.4,27.25,36.75)],cell=.27,padding=.05,mat='grass',count=62000,length=.036,children=7,seed=9),
 dict(name='Grass beyond parterre',rect=(-12.3,12.3,59.6,62.2),z=-.021,cell=.3,padding=.05,mat='grass',count=12000,length=.032,children=6,seed=11)]
PROBE_WALLS=[]

def setup_scene(scene):
    """Soft blue-hour environment with thin cloud bands; warm practical illumination."""
    import bpy
    nt=scene.world.node_tree;nt.nodes.clear()
    output=nt.nodes.new('ShaderNodeOutputWorld');bg=nt.nodes.new('ShaderNodeBackground');bg.inputs['Strength'].default_value=.62
    tc=nt.nodes.new('ShaderNodeTexCoord');sep=nt.nodes.new('ShaderNodeSeparateXYZ');nt.links.new(sep.inputs[0],tc.outputs['Generated'])
    ramp=nt.nodes.new('ShaderNodeValToRGB');els=ramp.color_ramp.elements
    stops=[(0,(.39,.48,.59,1)),(.15,(.20,.33,.53,1)),(.55,(.075,.18,.38,1)),(1,(.035,.09,.24,1))]
    els[0].position=stops[0][0];els[0].color=stops[0][1];els[1].position=stops[-1][0];els[1].color=stops[-1][1]
    for pos,color in stops[1:-1]:els.new(pos).color=color
    nt.links.new(ramp.inputs[0],sep.outputs['Z'])
    mapping=nt.nodes.new('ShaderNodeVectorMath');mapping.operation='MULTIPLY';mapping.inputs[1].default_value=(3,3,18);nt.links.new(mapping.inputs[0],tc.outputs['Generated'])
    noise=nt.nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=1;noise.inputs['Detail'].default_value=5;noise.inputs['Roughness'].default_value=.7;nt.links.new(noise.inputs['Vector'],mapping.outputs[0])
    cloud=nt.nodes.new('ShaderNodeMapRange');cloud.inputs['From Min'].default_value=.53;cloud.inputs['From Max'].default_value=.70;cloud.inputs['To Max'].default_value=.32;nt.links.new(cloud.inputs['Value'],noise.outputs['Fac'])
    mix=nt.nodes.new('ShaderNodeMixRGB');nt.links.new(mix.inputs[0],cloud.outputs[0]);nt.links.new(mix.inputs[1],ramp.outputs[0]);mix.inputs[2].default_value=(.41,.43,.47,1)
    nt.links.new(bg.inputs['Color'],mix.outputs[0]);nt.links.new(output.inputs[0],bg.outputs[0])
    sun=bpy.data.objects.get('Sun');sun.data.energy=1.65;sun.data.angle=.06

# Elliptical grass boundaries follow the masonry and pool beds.
import math as _math
_front_holes=[]
for j in range(116):
    x=-8.7+j*.15;mid=x+.075;dy=4.49*_math.sqrt(max(0,1-(mid/8.59)**2))
    _front_holes.extend([(x,x+.151,-16.,-11.4-dy),(x,x+.151,-11.4+dy,-6.8)])
_pool_holes=[]
for j in range(122):
    x=-9.15+j*.15;mid=x+.075;dy=4.35*_math.sqrt(max(0,1-(mid/9.05)**2))
    if dy:_pool_holes.append((x,x+.151,32-dy,32+dy))
GRASS[0].update(rect=(-8.7,8.7,-16.,-6.8),holes=_front_holes,cell=.12,padding=0,count=30000)
GRASS[1].update(holes=_pool_holes,cell=.15,padding=.02,count=90000)

# Preserve the world implementation and add the photographic lighting pass.
_world_setup=setup_scene

def setup_scene(scene):
    _world_setup(scene)
    import bpy
    from archviz.lights import area_light
    scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=1.10
    # Broad soft sources match the evening listing photography and hold detail in the colonnades.
    fills=[('Alpine front soft fill',(-2,-13,7.5),(16,8),950,(.79,.86,1),(0,1,3.7)),
           ('Alpine rear soft fill',(0,29,9),(20,8),1050,(.8,.89,1),(0,18,4.2)),
           ('Alpine pool west',(-4.1,32,-.40),(6,3),65,(.35,.75,1),(-4.1,32,-1.7)),
           ('Alpine pool east',(4.1,32,-.40),(6,3),65,(.35,.75,1),(4.1,32,-1.7))]
    for name,loc,size,power,color,target in fills:
        ob=bpy.data.objects.get(name)
        if ob is None:ob=area_light(name,loc,size,power,color,target=target)
        ob.visible_camera=False;ob.visible_glossy=False;ob.visible_transmission=False
    for ob in bpy.data.objects:
        if ob.type=='MESH' and ob.name.startswith('Skyline | palm crown') and not ob.get('crown_flattened'):
            zs=[v.co.z for v in ob.data.vertices]
            if zs:
                z0=(min(zs)+max(zs))/2
                for v in ob.data.vertices:v.co.z=z0+(v.co.z-z0)*.55
            ob['crown_flattened']=True

_lighting_setup=setup_scene

def setup_scene(scene):
    _lighting_setup(scene)
    from .finishing import apply
    apply(scene)

_architecture_setup=setup_scene

def setup_scene(scene):
    _architecture_setup(scene)
    from .botanical_finish import apply
    apply(scene)

_garden_baseline=setup_scene

def setup_scene(scene):
    _garden_baseline(scene)
    from .garden_v2 import apply
    apply(scene)

CAMS.update({
    'pool_aerial':((0,49,11),(0,23,2.8),26),
    'water_skim':((0,32.25,.34),(0,18,2.4),26),
    'garden_detail':((.15,47.7,1.1),(2.8,42.0,1.1),36),
})
EXT.extend(['pool_aerial','water_skim','garden_detail'])

_pool_garden_setup=setup_scene

def setup_scene(scene):
    _pool_garden_setup(scene)
    from .center_entry_finish import apply
    apply(scene)
