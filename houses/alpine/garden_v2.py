"""Review revision 2: cupped roses, detailed white-flower borders and garden light."""
import bpy,math,random,re
from mathutils import Vector
from archviz import materials,plants
from archviz.mesh import MB
from archviz.lights import area_light

def petal_material(name,light,dark):
    mat,nt,b=materials._new(name)
    n=materials._noise(nt,materials._coords(nt),scale=85,detail=3,rough=.6)
    col=materials._mixrgb(nt,n,(*dark,1),(*light,1))
    nt.links.new(b.inputs['Base Color'],col)
    b.inputs['Roughness'].default_value=.60
    b.inputs['Subsurface Weight'].default_value=.075
    b.inputs['Subsurface Scale'].default_value=.008
    fine=materials._noise(nt,materials._coords(nt),scale=850,detail=2)
    materials._bump(nt,b,fine,.13,.0003)
    return mat


def rose(mb,center,normal,rng,palette,radius=.075,hero=False):
    """Overlapping broad petals: shallow outer bowl, erect inner whorl, curled rims."""
    q=normal.to_track_quat('Z','Y')
    nu,nv=(8,7) if hero else (5,5)
    # (petals, length, width, lift, base-height) scaled by outer radius.
    rings=[(8,.87,.51,.35,-.32),(8,.69,.40,.64,-.25),(7,.48,.30,.78,-.13),(5,.26,.17,.64,.02)]
    if not hero:rings=[rings[0],rings[1],rings[3]]
    for layer,(count,length,width,lift,base_z) in enumerate(rings):
        phase=rng.uniform(-.2,.2)
        for k in range(count):
            angle=k*2*math.pi/count+layer*.49+rng.uniform(-.095,.095)
            ca,sa=math.cos(angle),math.sin(angle)
            verts=[];faces=[]
            for j in range(nv+1):
                v=j/nv
                for i in range(nu+1):
                    u=2*i/nu-1
                    w=width*(.48+.52*math.sin(math.pi*(.07+.55*v)))
                    radial=.11+length*v*(1-.18*u*u)
                    tang=u*w
                    # The outside petals gently curl down; inner petals cup around the heart.
                    z=base_z+lift*math.sin(v*math.pi*.74)+.15*u*u*(.15+.85*v)-.12*v**7
                    z+=.025*math.sin(7*u+phase)*v*v
                    local=Vector((radius*(radial*ca-tang*sa),radius*(radial*sa+tang*ca),radius*z))
                    verts.append(center+q@local)
            for j in range(nv):
                for i in range(nu):
                    a=j*(nu+1)+i;faces.append((a,a+nu+1,a+nu+2,a+1))
            mb._add(verts,faces,palette+(1 if layer==len(rings)-1 else 0))


def apply(scene):
    if scene.get('Alpine garden revision 2'):return
    scene['Alpine garden revision 2']=True
    rng=random.Random(80502)
    # Close the front entry for the revised route, which uses the rear French doors.
    door=bpy.data.objects.get('Entry_Door')
    if door:door.animation_data_clear();door.rotation_euler=(0,0,0)
    scene['doors_open']=True
    objects=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(('Rose collection','Climbing roses','Front white roses')) and o.name.endswith('_Leaves')]
    sites=[]
    for ob in objects:
        indices={j for j,m in enumerate(ob.data.materials) if m and m.name.startswith('Alpine | replaced rose card')}
        if not indices:continue
        if ob.name.startswith('Rose collection'):
            side,row,j=map(int,re.findall(r'-?\d+',ob.name)[:3]);color=(row+j//3)%3
        else:color=1
        accepted=[]
        for poly in sorted(ob.data.polygons,key=lambda p:p.area,reverse=True):
            if poly.material_index not in indices:continue
            c=ob.matrix_world@poly.center
            if any((c-other).length<.045 for other in accepted):continue
            accepted.append(c)
            n=poly.normal.copy()
            if n.z<0:n=-n
            n=(n+Vector((0,0,.80))).normalized()
            sites.append((c,n,color,math.sqrt(poly.area)*.52))
    old=bpy.data.objects.get('Alpine | sculpted garden roses')
    if old:
        mesh=old.data;bpy.data.objects.remove(old,do_unlink=True)
        if mesh.users==0:bpy.data.meshes.remove(mesh)
    mats=[
        petal_material('V2 | blush rose outer',(.74,.34,.40),(.45,.12,.21)),
        petal_material('V2 | blush rose heart',(.57,.17,.27),(.30,.055,.11)),
        petal_material('V2 | ivory rose outer',(.89,.82,.68),(.68,.60,.40)),
        petal_material('V2 | ivory rose heart',(.78,.64,.39),(.47,.32,.13)),
        petal_material('V2 | carmine rose outer',(.62,.085,.15),(.32,.022,.055)),
        petal_material('V2 | carmine rose heart',(.40,.034,.080),(.20,.012,.030)),
    ]
    blooms=MB();hero_count=0
    for c,n,color,card_radius in sites:
        hero=41.5<c.y<51 and .9<c.x<5.7
        hero_count+=hero
        rose(blooms,c,n,rng,color*2,radius=max(.024,min(.054,card_radius))*rng.uniform(.97,1.08),hero=hero)
    blooms.build('V2 | layered cupped garden roses',mats,coll='Landscape',smooth=True,recalc=False,auto_smooth=False)
    print(f'[garden v2] {len(sites)} layered roses, {hero_count} close-view blooms',flush=True)
    # Detailed strap leaves and small white umbels sit just beyond the pool flower border.
    F=plants.Foliage(80503);MM=plants.mats();buds=MB()
    white=petal_material('V2 | white border blossom',(.88,.90,.78),(.59,.71,.48))
    stem=bpy.data.materials['Alpine | rose ivory heart']
    centers=[]
    for j in range(42):
        a=2*math.pi*(j+.4)/42;x=9.38*math.cos(a);y=32+4.74*math.sin(a)
        for k in range(9):
            az=k*2*math.pi/9+rng.uniform(-.12,.12);el=rng.uniform(.38,.88)
            out=Vector((math.cos(az),math.sin(az),0));direction=out*math.cos(el)+Vector((0,0,1))*math.sin(el)
            F.leaf('agap_leaf',(x,y,.0),direction,out.cross(Vector((0,0,1))),rng.uniform(.34,.52),rng.uniform(.021,.035),n=6,droop=-rng.uniform(.65,1.0))
        for k in range(3):
            az=rng.uniform(0,2*math.pi);cx=x+.10*math.cos(az);cy=y+.10*math.sin(az);h=rng.uniform(.43,.64)
            F.wood.tube((x,y,0),(cx,cy,h),.004,.0025,seg=7,mi=2)
            for v in range(16):
                ang=v*2*math.pi/16;rr=rng.uniform(.03,.065)
                c=Vector((cx+rr*math.cos(ang),cy+rr*math.sin(ang),h+rng.uniform(-.018,.04)))
                # Six pale rounded petals surround a small green throat.
                for pet in range(6):
                    aa=pet*math.pi/3;vs=[c]
                    for q in range(7):
                        u=q*math.pi/6
                        r=.009+.016*math.sin(u)
                        vs.append(c+Vector((r*math.cos(aa+(u-math.pi/2)*.25),r*math.sin(aa+(u-math.pi/2)*.25),.008*math.sin(u))))
                    buds._add(vs,[tuple(range(len(vs)))],0)
    F.build('V2 | pool border leaves and stems',[MM['stem'],MM['soil'],MM['stem']],coll='Landscape')
    buds.build('V2 | modeled white border florets',[white],coll='Landscape',smooth=True,recalc=False,auto_smooth=False)
    # Small compound-leaf mounds fill the beds beneath the roses, with visible stems and veins.
    ground=plants.Foliage(80509)
    for side in (-1,1):
        for row,ya in enumerate((44.0,49.0,54.0)):
            for j in range(30):
                x=side*rng.uniform(1.58,9.25);y=ya+rng.uniform(.42,3.20)
                for k in range(15):
                    a=k*2*math.pi/15+rng.uniform(-.16,.16)
                    out=Vector((math.cos(a),math.sin(a),0));h=rng.uniform(.10,.22)
                    tip=Vector((x,y,.065))+out*rng.uniform(.08,.20)+Vector((0,0,h))
                    ground.wood.tube((x,y,.065),tuple(tip),.0025,.0015,seg=5,mi=2)
                    d=(out*.85+Vector((0,0,rng.uniform(.15,.6)))).normalized()
                    ground.leaf('rose_leaf',tip,d,out.cross(Vector((0,0,1))),rng.uniform(.08,.13),rng.uniform(.035,.055),n=3,droop=-.35)
    ground.build('V2 | layered rose-bed ground foliage',[MM['stem'],MM['soil'],MM['stem']],coll='Landscape')
    # Soft photographic fill lets petal color and leaf structure read in the evening shade.
    for name,loc,size,power,color,target in [
        ('V2 garden soft light',(-3,47.5,8.5),(15,13),1250,(1,.86,.66),(1,48.5,.5)),
        ('V2 garden rim light',(9,51,6.5),(8,7),520,(1,.79,.53),(1,47.0,1)),
        ('V2 pool edge soft light',(-7,35,5.5),(8,5),280,(.81,.9,1),(0,32,0)),
    ]:
        ob=area_light(name,loc,size,power,color,target=target)
        ob.visible_camera=False;ob.visible_glossy=False;ob.visible_transmission=False
    scene['garden_v2_blooms']=len(sites);scene['garden_v2_hero_blooms']=hero_count
