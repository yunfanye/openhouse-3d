"""Photo-review refinement pass: measured texture scale, soft goods and photographic light.

Keep all changes local to Webster. Photographic maps are CC0 from Poly Haven;
assets/sources.json records the exact sources. The architecture remains photo-derived.
"""
import math
from pathlib import Path
import bpy
import bmesh
from mathutils import Vector
from mathutils import noise
from archviz import materials as mat
from archviz.mesh import MB, rot2
from archviz.materials import image_texture, mapped
from archviz.lights import area_light
from .plan import Z_UP, Z_GRADE, CHIMNEY, FIREPLACE_FACE, FIREPLACE_CENTRE, FAMILY_REAR, ROOMS

ASSETS = Path(__file__).parent / 'assets'


def oak_floor(name, rotation=0):
    m = mat.new_mat(name, rough=0.32, coat=0.22)
    nt = m.node_tree
    bs = nt.nodes.get('Principled BSDF')
    vec = mapped(nt, (0.78, 0.40, 1), rotation)
    diff = image_texture(nt, ASSETS / 'wood_floor_diff_2k.jpg', vec)
    # Gentle lift into the original honey-oak palette, retaining photographed grain.
    mix = nt.nodes.new('ShaderNodeMixRGB'); mix.blend_type = 'MULTIPLY'
    mix.inputs[0].default_value = 1
    mix.inputs[2].default_value = (1.6, 1.48, 1.24, 1)
    nt.links.new(diff.outputs['Color'], mix.inputs[1])
    nt.links.new(mix.outputs[0], bs.inputs['Base Color'])
    rough = image_texture(nt, ASSETS / 'wood_floor_rough_2k.jpg', vec, True)
    remap = nt.nodes.new('ShaderNodeMapRange')
    remap.inputs['To Min'].default_value = 0.24
    remap.inputs['To Max'].default_value = 0.43
    nt.links.new(rough.outputs['Color'], remap.inputs['Value'])
    nt.links.new(remap.outputs[0], bs.inputs['Roughness'])
    # Height from grain at submillimetre depth; avoid the old heavy plastic relief.
    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.16
    bump.inputs['Distance'].default_value = 0.001
    nt.links.new(diff.outputs['Color'], bump.inputs['Height'])
    nt.links.new(bump.outputs[0], bs.inputs['Normal'])
    return m


def woven(m, thread=650):
    nt = m.node_tree; bs = nt.nodes.get('Principled BSDF')
    if not bs:
        return
    vec = mapped(nt, (1, 1, 1))
    waves = []
    for axis in ('X', 'Y'):
        n = nt.nodes.new('ShaderNodeTexWave'); n.bands_direction = axis
        n.inputs['Scale'].default_value = thread
        n.inputs['Distortion'].default_value = 2.0
        n.inputs['Detail Scale'].default_value = 3.0
        nt.links.new(vec, n.inputs['Vector']); waves.append(n)
    multiply = nt.nodes.new('ShaderNodeMath'); multiply.operation = 'MULTIPLY'
    for i, n in enumerate(waves): nt.links.new(n.outputs['Color'], multiply.inputs[i])
    b = nt.nodes.new('ShaderNodeBump'); b.inputs['Strength'].default_value = 0.23
    b.inputs['Distance'].default_value = 0.00065
    nt.links.new(multiply.outputs[0], b.inputs['Height'])
    if bs.inputs['Normal'].links:
        nt.links.new(bs.inputs['Normal'].links[0].from_socket, b.inputs['Normal'])
    nt.links.new(b.outputs[0], bs.inputs['Normal'])
    bs.inputs['Sheen Weight'].default_value = 0.45
    bs.inputs['Roughness'].default_value = 0.86


def refine_materials(M):
    # The reference is a light grey stucco. Blue-hour saturation had made it violet.
    M['stucco'] = mat.plaster('Webster_SilverGreyStucco', (0.49, 0.52, 0.53, 1), rough=0.87, grain=0.2)
    M['stucco_wing'] = M['stucco']
    M['maple'] = oak_floor('Webster_RefinishedOak_X', math.pi / 2)
    M['maple_y'] = oak_floor('Webster_RefinishedOak_Y')
    M['walnut'] = mat.wood('Webster_QuietWalnut', light=(0.29, 0.19, 0.105, 1), dark=(0.21, 0.13, 0.065, 1), grain_axis='X', ring=48, rough=0.37, coat=0.18)
    for key in ('fabric', 'fabric_sand', 'fabric_taupe', 'fabric_rust'):
        woven(M[key])
    leather = M['leather_tan']; nt = leather.node_tree; bs = nt.nodes.get('Principled BSDF')
    tex = image_texture(nt, ASSETS / 'fabric_leather_01_rough_2k.jpg', mapped(nt, (3, 3, 3)), True, True)
    b = nt.nodes.new('ShaderNodeBump'); b.inputs['Strength'].default_value = 0.22; b.inputs['Distance'].default_value = 0.0007
    nt.links.new(tex.outputs['Color'], b.inputs['Height']); nt.links.new(b.outputs[0], bs.inputs['Normal'])
    bs.inputs['Roughness'].default_value = 0.46
    # Retain the green tile, but give it a restrained glazed reflection.
    for key in ('tile_green', 'tile_green_v', 'tile_green_vy'):
        bs = M[key].node_tree.nodes.get('Principled BSDF')
        bs.inputs['Coat Weight'].default_value = 0.28
        bs.inputs['Coat Roughness'].default_value = 0.21
    for key in ('wall', 'ceiling', 'stucco'):
        for node in M[key].node_tree.nodes:
            if node.type == 'BUMP':
                node.inputs['Distance'].default_value = 0.0015 if key == 'stucco' else 0.0005


def sewn_seat(mb, x, y, z, w, d, rot=0, mi=0):
    points = []
    r = 0.08
    for cx, cy, a0 in ((w/2-r, -d/2+r, -math.pi/2), (w/2-r, d/2-r, 0), (-w/2+r, d/2-r, math.pi/2), (-w/2+r, -d/2+r, math.pi)):
        for i in range(9):
            a = a0 + math.pi/2*i/8
            px, py = rot2(x+cx+r*math.cos(a), y+cy+r*math.sin(a), x, y, rot)
            points.append((px, py, z))
    points.append(points[0])
    mb.path_tube(points, 0.0028, seg=6, mi=mi)


def primary_bedding():
    """Continuous cloth surfaces with rolled hems and gravity-shaped side drops."""
    bed = bpy.data.objects['Up_Bed_Prim']
    bm = bmesh.new(); bm.from_mesh(bed.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index in (2, 4)], context='FACES')
    bm.to_mesh(bed.data); bm.free()
    linen, throw = bed.data.materials[4], bed.data.materials[2]
    cx, cy, floor = ROOMS['prim'][1]-.08-.975, 9.2, Z_UP + .018

    def cloth(name, xa, xb, ya, yb, material, blanket=False):
        mb = MB(); nx, ny = 90, 76
        def point(u, v):
            x, y = xa+(xb-xa)*u, ya+(yb-ya)*v
            side = max(0., abs(x)-.71)
            z = floor+.72 - .85*side
            z -= max(0., -y-.92)*1.9
            z += .009*noise.fractal(Vector((x*6,y*6,3.7)),1.,2.,3)
            z += .014*math.exp(-((y+.12-.13*math.sin(2.5*x))/.065)**2) * math.exp(-((x-.25)/.6)**2)
            if blanket:
                z += .034 + .003*noise.noise(Vector((x*21,y*12,9.1)))
            else:
                z += .055*math.exp(-((y-.21)/.12)**2)
            px, py = rot2(cx+x, cy+y, cx, cy, -math.pi/2)
            return (px, py, z)
        verts = [point(i/nx,j/ny) for j in range(ny+1) for i in range(nx+1)]
        faces=[]
        for j in range(ny):
            for i in range(nx):
                a=j*(nx+1)+i; faces.append((a,a+1,a+nx+2,a+nx+1))
        mb._add(verts,faces,0)
        ob=mb.build(name,[material],smooth=True,subsurf=1,auto_smooth=False)
        sol=ob.modifiers.new('Cloth thickness','SOLIDIFY'); sol.thickness=.009 if blanket else .028; sol.offset=-1
        seam=MB()
        for v in (0.,1.):
            seam.path_tube([point(i/120,v) for i in range(121)],.003,seg=5)
        seam.build(name+'_Hem',[material],smooth=True)
    cloth('Detail_PrimaryDuvet',-1.01,1.01,-1.035,.36,linen)
    cloth('Detail_PrimaryThrow',-1.02,1.03,-.84,-.29,throw,True)
    mb=MB()
    mb.pillow_sq(4.37,9.2,floor+.85,.56,.32,.16,rot=-math.pi/2,pitch=1.03,nx=22,ny=18,seed=91)
    mb.build('Detail_PrimaryLumbar',[throw],smooth=True,subsurf=1,auto_smooth=False)



def secondary_bedding():
    """Replace folded rectangular duvet props with continuous soft cloth surfaces."""
    for name,cx,cy,width,length,angle in (
        ('Up_Bed_Bed2',-1.555,9.02,1.4,1.95,-math.pi/2),
        ('Up_Bed_Bed3',-1.65,12.7,1.6,2.1,math.pi)):
        ob=bpy.data.objects[name];bm=bmesh.new();bm.from_mesh(ob.data)
        bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index in (2,4)],context='FACES')
        bm.to_mesh(ob.data);bm.free()
        for blanket,material in ((False,ob.data.materials[4]),(True,ob.data.materials[2])):
            nx,ny=64,56;mb=MB();half=width/2
            ya,yb=(-length*.43,-length*.14) if blanket else (-length/2-.025,.34)
            def point(u,v):
                x=(2*u-1)*(half+.24);y=ya+(yb-ya)*v
                z=Z_UP+.015+.715-.88*max(0.,abs(x)-(half-.04))
                z-=1.5*max(0.,-y-(length/2-.04))
                z+=.010*noise.fractal(Vector((x*7,y*7,7.3)),1.,2.,3)
                z+=.015*math.sin(17*x+4*y)*math.exp(-((y-.12)/.24)**2)
                if blanket:z+=.035+.004*math.sin(22*y+6*x)
                else:z+=.040*math.exp(-((y-.23)/.10)**2)
                xx,yy=rot2(cx+x,cy+y,cx,cy,angle)
                return xx,yy,z
            verts=[point(i/nx,j/ny) for j in range(ny+1) for i in range(nx+1)]
            faces=[]
            for j in range(ny):
                for i in range(nx):
                    a=j*(nx+1)+i;faces.append((a,a+1,a+nx+2,a+nx+1))
            mb._add(verts,faces,0)
            tag='Detail_'+name+('_Throw' if blanket else '_Duvet')
            cloth=mb.build(tag,[material],smooth=True,subsurf=1,auto_smooth=False)
            sol=cloth.modifiers.new('Woven thickness','SOLIDIFY');sol.thickness=.010 if blanket else .035;sol.offset=-1
            hem=MB()
            for vv in (0.,1.):hem.path_tube([point(i/100,vv) for i in range(101)],.0025,seg=5)
            hem.build(tag+'_Hem',[material],smooth=True)

def finishing_objects(M):
    # A working-looking clock face and printed bindings survive the close fireplace orbit.
    mb=MB();x=FIREPLACE_FACE+.106;y=FIREPLACE_CENTRE;z=1.53
    for i in range(12):
        a=i*math.tau/12;r0=.059 if i%3==0 else .064
        mb.tube((x,y+math.sin(a)*r0,z+math.cos(a)*r0),(x,y+math.sin(a)*.071,z+math.cos(a)*.071),.0013,.0013,seg=6)
    for a,r in ((math.radians(-55),.039),(math.radians(60),.055)):
        mb.tube((x+.001,y,z),(x+.001,y+math.sin(a)*r,z+math.cos(a)*r),.002,.0009,seg=7)
    mb.tube((x,y,z),(x+.004,y,z),.004,.004,seg=12)
    mb.build('Detail_MantelClock',[M['black_metal']],smooth=True)
    mb=MB()
    for i in range(3):
        xx,yy=-3.5+(i%2)*.02,1.62-(i%2)*.015
        for zz in (.422+i*.03,.448+i*.03):
            mb.rcbox(xx,yy,zz,.266-i*.02,.206-i*.01,.004,.001,i%2,rot=.3)
    mb.build('Detail_CoffeeBookBindings',[M['fabric_taupe'],M['fabric_sand']])
    # Emitting gas fills the flame volumes. The old surface shader made solid orange cut-outs.
    fire=bpy.data.objects['Front_Fire']
    m=bpy.data.materials.new('Webster_EmittingFlameVolume');m.use_nodes=True
    nt=m.node_tree;nt.nodes.clear()
    out=nt.nodes.new('ShaderNodeOutputMaterial');vol=nt.nodes.new('ShaderNodeVolumePrincipled')
    vol.inputs['Density'].default_value=0.0
    tc=nt.nodes.new('ShaderNodeTexCoord')
    sep=nt.nodes.new('ShaderNodeSeparateXYZ');nt.links.new(tc.outputs['Generated'],sep.inputs[0])
    n=nt.nodes.new('ShaderNodeTexNoise');n.noise_dimensions='4D';n.inputs['Scale'].default_value=9.;n.inputs['Detail'].default_value=3.
    n.inputs['W'].driver_add('default_value').driver.expression='frame/19'
    nt.links.new(tc.outputs['Generated'],n.inputs['Vector'])
    ramp=nt.nodes.new('ShaderNodeMapRange');ramp.inputs['From Min'].default_value=.30;ramp.inputs['From Max'].default_value=.64
    ramp.inputs['To Min'].default_value=0.;ramp.inputs['To Max'].default_value=85.
    nt.links.new(n.outputs['Fac'],ramp.inputs['Value'])
    fade=nt.nodes.new('ShaderNodeMath');fade.operation='SUBTRACT';fade.inputs[0].default_value=1.
    nt.links.new(sep.outputs['Z'],fade.inputs[1])
    strength=nt.nodes.new('ShaderNodeMath');strength.operation='MULTIPLY'
    nt.links.new(ramp.outputs[0],strength.inputs[0]);nt.links.new(fade.outputs[0],strength.inputs[1])
    nt.links.new(strength.outputs[0],vol.inputs['Emission Strength'])
    temp=nt.nodes.new('ShaderNodeMapRange');temp.inputs['To Min'].default_value=2250.;temp.inputs['To Max'].default_value=1400.
    nt.links.new(sep.outputs['Z'],temp.inputs['Value'])
    blackbody=nt.nodes.new('ShaderNodeBlackbody');nt.links.new(temp.outputs[0],blackbody.inputs['Temperature'])
    nt.links.new(blackbody.outputs[0],vol.inputs['Emission Color']);nt.links.new(vol.outputs[0],out.inputs['Volume'])
    fire.data.materials.clear();fire.data.materials.append(m)


def build(M):
    primary_bedding()
    secondary_bedding()
    finishing_objects(M)
    # Dense smooth cushions, no auto-smooth seams on soft upholstery.
    for ob in bpy.data.objects:
        if ob.type != 'MESH': continue
        if ob.name in ('Front_LivSeating', 'Up_Bed_Prim', 'Up_Bed_Bed2', 'Up_Bed_Bed3'):
            for modifier in list(ob.modifiers):
                if modifier.type == 'NODES' and 'Smooth' in modifier.name:
                    ob.modifiers.remove(modifier)
                elif modifier.type == 'SUBSURF':
                    modifier.levels = modifier.render_levels = 2
            for poly in ob.data.polygons: poly.use_smooth = True
        # Small real bevels make painted millwork catch window light.
        if any(word in ob.name for word in ('Trims', 'Casings', 'Dresser', 'CoffeeTable')) and not any(m.type == 'BEVEL' for m in ob.modifiers):
            bv = ob.modifiers.new('Hand finished edges', 'BEVEL')
            bv.width = 0.0015; bv.segments = 3; bv.limit_method = 'ANGLE'
    for m in bpy.data.materials:
        if any(s in m.name.lower() for s in ('duvet', 'sheet', 'drape_linen', 'up_pillow')):
            woven(m, 780)
    mb = MB()
    for yy in (1.05, 1.85):
        sewn_seat(mb, -2.66, yy, 0.385, 0.76, 0.66, -math.pi/2)
    mb.build('Detail_SofaPiping', [M['fabric_sand']], smooth=True)
    # Gently crumpled, sewn scatter cushions instead of the upright flat orange slabs.
    mb = MB()
    for i, (yy, w, tilt) in enumerate(((0.90, 0.43, 1.18), (1.98, 0.40, 1.02))):
        mb.pillow_sq(-2.55, yy, 0.62, w, w, 0.18, i, rot=-math.pi/2+(i-.5)*.13, pitch=tilt, nx=24, ny=22, seed=27+i)
    mb.build('Detail_LivingScatterCushions', [M['fabric_rust'], M['fabric_taupe']], smooth=True, subsurf=1, auto_smooth=False)
    # Diffuse window bounce just inside each reveal; avoids lighting exterior casings.
    window_lights = [
        ('Living', (-3.6, 0.35, 1.65), (3.0, 1.5), 125, (-3.4, 3.0, 1.0)),
        ('Dining', (3.5, 2.4, 1.65), (2.6, 1.5), 105, (3.4, 4.7, 1.0)),
        ('Kitchen', (5.35, 9.25, 1.7), (2.0, 1.1), 80, (3.5, 9.0, 1.1)),
        ('Laundry',(5.36,13.08,1.70),(.65,1.0),75,(4.0,12.95,.8)),
        ('Family', (1.25, FAMILY_REAR-.15, 1.9), (2.4, 1.6), 120, (1.0, 14.8, 0.8)),
        ('Suite', (3.9, 6.45, 4.55), (1.8, 1.3), 38, (3.7, 9.0, 3.7)),
        ('DeckBedroom', (-3.05, 9.3, 4.6), (1.7, 1.5), 90, (-1.6, 9.4, 3.7)),
    ]
    for name, loc, size, power, target in window_lights:
        area_light('Detail_Window_'+name, loc, size, power, (1.0, 0.93, 0.83), target=target)
    for ob in bpy.data.objects:
        if ob.type == 'LIGHT' and ob.name.startswith(('L_', 'Up_L_', 'Back_L_')):
            if 'Fill' in ob.name or 'Ceiling' in ob.name:
                ob.data.energy *= 0.65
            ob.data.color = (1.0, 0.88, 0.73)


def setup_scene(scene):
    """Photographic golden-hour sky, packed into the deliverable .blend."""
    nt = scene.world.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputWorld')
    bg = nt.nodes.new('ShaderNodeBackground'); bg.inputs['Strength'].default_value = 0.36
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Rotation'].default_value[2] = math.radians(115)
    nt.links.new(tc.outputs['Generated'], mp.inputs['Vector'])
    env = nt.nodes.new('ShaderNodeTexEnvironment')
    env.image = bpy.data.images.load(str(ASSETS / 'kloppenheim_06_puresky_4k.hdr'), check_existing=True)
    nt.links.new(mp.outputs[0], env.inputs[0]); nt.links.new(env.outputs[0], bg.inputs[0]); nt.links.new(bg.outputs[0], out.inputs[0])
    sun = bpy.data.objects.get('Sun')
    sun.data.energy = 1.5
    sun.data.color = (1.0, 0.84, 0.67)
    sun.data.angle = math.radians(1.2)
    sun.rotation_euler = (-Vector((-0.65, -0.65, 0.28)).normalized()).to_track_quat('-Z', 'Y').to_euler()
    for im in bpy.data.images:
        if im.source == 'FILE': im.pack()
