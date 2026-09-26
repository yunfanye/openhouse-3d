"""Idempotent final architectural and styling details, also applied to packed scenes."""
import bpy,math
from archviz.mesh import MB
from archviz import materials,parts
from .details import B,path_tube
from .exterior import roof

def apply(scene):
    if bpy.data.objects.get('Alpine | final architectural details'):return
    def mat(n):return bpy.data.materials['Alpine | '+n]
    M=dict(white=mat('warm white plaster'),trim=mat('ivory painted joinery'),counter=mat('champagne granite'),steel=mat('steel'),black=mat('black'),oak=mat('library honey oak'),porcelain=mat('porcelain'),brick=mat('aged red brick'),brick_y=mat('side brick'),slate=mat('slate shingle courses'),walnut=mat('polished walnut'))
    b=B(M);i=b.i
    # Close thin exposed masonry joints on the room corners.
    for x in (-11.80,11.80):
        for y in (.20,17.80):b.box(x-.07,x+.07,y-.045,y+.045,.45,7.85,i['white'])
    b.box(-12,12,-.15,.15,4.03,4.25,i['brick']);b.box(-12,12,17.85,18.15,4.03,4.25,i['brick'])
    for x in (-12,12):b.box(x-.15,x+.15,0,18,4.03,4.25,i['brick_y'])
    # Granite backsplash and a copper-toned board with a stainless cooking vessel.
    b.box(11.715,11.76,8.92,13.62,1.38,2.16,i['counter'])
    b.cylinder(11.37,11.15,1.43,1.64,.18,.18,seg=36,mi=i['steel'])
    b.lathe(11.37,11.15,1.63,[(.19,0),(.14,.025),(0,.045)],seg=36,mi=i['steel'])
    b.cylinder(11.37,11.15,1.67,1.72,.024,seg=16,mi=i['black'])
    for yy in (10.91,11.39):b.cbox(11.37,yy,1.58,.16,.10,.025,i['black'])
    b.rbox(11.42,11.64,16.17,16.53,1.41,1.75,.025,i['oak'])
    # Opening entry consoles and desk decorations.
    for x in (-2.65,2.65):
        # Lacquered sculptural rosette over each entry console.
        for j in range(9):
            a=j*2*math.pi/9
            points=[(x+.28*math.cos(a)+.16*math.cos(t),.435,2.44+.28*math.sin(a)+.16*math.sin(t)) for t in [q*2*math.pi/32 for q in range(33)]]
            path_tube(b,points,.018,i['black'],seg=8)
    b.done('Alpine | final architectural details',bevel=.003)
    # Gallery's exposed wood trusses, ventilation duct and polished slate floor.
    M['gallery_floor']=materials.tiles('Alpine | gallery slate',(.07,.075,.078,1),grout=(.10,.105,.108,1),size=(.8,.8),gap=.003,rough=.22,variation=.1,mottle=.12,bump=.08)
    b=B(M);i=b.i;b.box(-11.06,11.06,65.30,75.69,.201,.215,i['gallery_floor'])
    b.box(-11.10,11.10,75.65,75.70,.215,4.40,i['white'])
    b.box(-11.11,-11.07,65.3,75.7,.215,4.40,i['white']);b.box(11.07,11.11,65.3,75.7,.215,4.40,i['white'])
    for x in (-8,-4,0,4,8):
        b.box(x-.075,x+.075,65.5,75.5,4.10,4.28,i['oak'])
        for yy in (65.5,75.5):b.tube((x,yy,4.24),(x,70.5,5.98),.105,.105,seg=4,mi=i['oak'])
        b.box(x-.06,x+.06,70.44,70.56,4.24,5.96,i['oak'])
        for yy in (67.5,73.5):b.tube((x,yy,4.24),(x,70.5,5.86),.07,.07,seg=4,mi=i['oak'])
    b.tube((-10.5,70.2,5.30),(10.5,70.2,5.30),.16,.16,seg=28,mi=i['steel'])
    # Sculptural gallery display, visible through the three glazed bays.
    for x in (-6,6):
        b.cylinder(x,68,.215,.38,.58,seg=48,mi=i['white'])
        b.cylinder(x,68,.38,1.2,.24,.34,seg=36,mi=i['black'])
        b.blob((x,68,1.66),.64,seg=32,rings=20,squash=.8,mi=i['steel'])
    b.done('Gallery | trusses and sculptural interior',bevel=.004)
    # Discreet neighbouring rooflines establish the Beverly Hills setting from above.
    M['neighbor']=materials.plaster('Alpine | distant ivory stucco',(.48,.435,.35,1),grain=.08)
    M['neighbor_roof']=materials.noise_mat('Alpine | distant roof',(.14,.145,.145,1),(.22,.225,.21,1),scale=32,bump=.08)
    b=B(M);i=b.i
    for x in (-33,33):
        for y in (-1,34,72):
            b.box(x-7.5,x+7.5,y-7.5,y+7.5,-.20,5.2,i['neighbor'])
            old=M['slate'];M['slate']=M['neighbor_roof']
            rb=B(M);roof(rb,x-7.9,x+7.9,y-7.9,y+7.9,5.25,7.5)
            # Keep material slots consistent when merging the distant roof.
            ri=rb.i['slate']
            for idx in range(len(rb.fm)):
                if rb.fm[idx]==ri:rb.fm[idx]=i['neighbor_roof']
            b.merge(rb);M['slate']=old
            for xx in (-4.5,0,4.5):
                for zz in (1.0,3.3):
                    b.box(x+xx-.60,x+xx+.60,y-7.54,y-7.5,zz,zz+1.3,i['black'])
                    b.frame(x+xx-.66,x+xx+.66,y-7.58,y-7.53,zz-.06,zz+1.36,.065,i['trim'])
    b.done('Context | neighbouring Beverly Hills rooflines',bevel=.015)

    from archviz.lights import add_light
    for x in (-1.85,1.85):
        for y in (45.0,50.0,55.0):
            ob=add_light(f'Alpine rose uplight {x} {y}','POINT',(x,y,.24),22,(1,.72,.44),size=.22)
            ob.visible_camera=False;ob.visible_glossy=False;ob.visible_transmission=False
