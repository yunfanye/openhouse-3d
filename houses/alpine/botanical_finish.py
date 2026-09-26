"""Hero palm crowns, layered contextual planting and modeled rose petals."""
import bpy,math,random
from mathutils import Vector
from archviz import plants,trees,materials
from archviz.mesh import MB

def apply(scene):
    if scene.get('Alpine botanical finish'):return
    scene['Alpine botanical finish']=True
    # Rebuild the palm fronds with correct downward curvature and a shared trunk anchor.
    for ob in list(bpy.data.objects):
        if ob.name.startswith('Skyline | palm crown'):bpy.data.objects.remove(ob,do_unlink=True)
    MM=plants.mats();rng=random.Random(805)
    for j in range(10):
        trunk=bpy.data.objects.get(f'Skyline | palm trunk {j}')
        if not trunk:continue
        top=max(v.co.z for v in trunk.data.vertices)
        ring=[v.co for v in trunk.data.vertices if v.co.z>top-.02]
        center=sum(ring,Vector())/len(ring)
        F=plants.Foliage(290+j)
        for k in range(19):
            a=k*2*math.pi/19+rng.uniform(-.12,.12);el=rng.uniform(.18,.8)
            out=Vector((math.cos(a),math.sin(a),0));direction=out*math.cos(el)+Vector((0,0,1))*math.sin(el)
            side=out.cross(Vector((0,0,1)))
            F.leaf('palm',center,direction,side,rng.uniform(3.1,4.3),rng.uniform(.82,1.2),n=8,droop=-rng.uniform(1.05,1.45),twist=rng.uniform(-.08,.08))
        F.build(f'Alpine botanical palm {j}',[MM['stem'],MM['soil'],MM['stem']],coll='Landscape')
    # Dense vegetation beyond the photographed parcel avoids distracting bare context.
    context=bpy.data.objects.get('Context | neighbouring Beverly Hills rooflines')
    if context:context.hide_render=True
    bark=bpy.data.materials['Alpine | polished walnut']
    for side in (-1,1):
        for j in range(11):
            trees.oak(f'Alpine context understory {side} {j}',(side*(22+rng.uniform(-1,2)),-13+j*10.1,-.10),height=rng.uniform(7.2,9.2),spread=12,trunk_r=.21,trunk_f=.22,seed=2200+j+(side+1)*20,detail=.17,min_z=1.2,mats={'bark':bark})
    for j in range(12):
        trees.oak(f'Alpine distant understory {j}',(-52+j*9.5,-30-rng.uniform(0,8),-.1),height=rng.uniform(8,10),spread=12,trunk_r=.24,trunk_f=.2,seed=2300+j,detail=.16,min_z=1.5,mats={'bark':bark})
    # Lavender infill under the taller roses creates a dense, layered formal garden.
    for side in (-1,1):
        for row,y in enumerate((44.7,49.7,54.7)):
            for j in range(5):
                plants.shrub(f'Alpine lavender infill {side} {row} {j}',(side*(2.5+j*1.45),y+1.35,.065),r=.43,h=.48,kind='lavender',seed=2400+row*30+j+(side+1)*100)
    # Replace the flat rose flower cards with small sculpted corollas for the close garden pass.
    pink=materials.new_mat('Alpine | rose silk pink',(.66,.24,.30,1),rough=.65,subsurface=.10)
    pink_inner=materials.new_mat('Alpine | rose pink heart',(.32,.045,.075,1),rough=.72)
    ivory=materials.new_mat('Alpine | rose ivory petals',(.78,.71,.56,1),rough=.66,subsurface=.08)
    gold=materials.new_mat('Alpine | rose ivory heart',(.58,.38,.15,1),rough=.70)
    red=materials.new_mat('Alpine | rose carmine petals',(.46,.035,.065,1),rough=.67,subsurface=.09)
    trans=bpy.data.materials.new('Alpine | replaced rose card');trans.use_nodes=True;nt=trans.node_tree;nt.nodes.clear();o=nt.nodes.new('ShaderNodeOutputMaterial');n=nt.nodes.new('ShaderNodeBsdfTransparent');nt.links.new(o.inputs[0],n.outputs[0])
    blossoms=MB();mats=[pink,pink_inner,ivory,gold,red]
    objects=[ob for ob in list(bpy.data.objects) if ob.type=='MESH' and ob.name.startswith(('Rose collection','Climbing roses','Front white roses')) and ob.name.endswith('_Leaves')]
    flowers=0
    for ob in objects:
        idxs={j:m.name for j,m in enumerate(ob.data.materials) if m and ('FlowerRose' in m.name or 'Alpine rose carmine' in m.name)}
        for p in ob.data.polygons:
            if p.material_index not in idxs:continue
            center=ob.matrix_world@p.center
            name=idxs[p.material_index];white='White' in name;car='carmine' in name
            mi=2 if white else 4 if car else 0;heart=3 if white else 1
            normal=p.normal.copy()
            if normal.z<0:normal=-normal
            normal=(normal+Vector((0,0,1))*.55).normalized();q=normal.to_track_quat('Z','Y')
            petal_radius=rng.uniform(.052,.085)
            for layer in range(3):
                petals=7 if layer==0 else 6
                radius=petal_radius*(1-layer*.23)
                for k in range(petals):
                    a=k*2*math.pi/petals+layer*.45+rng.uniform(-.12,.12)
                    verts=[];faces=[];nu,nv=6,5
                    for vj in range(nv+1):
                        v=vj/nv;r=radius*(.14+.86*v)
                        for uj in range(nu+1):
                            u=(uj/nu-.5)*2
                            ang=a+u*.46*math.sin(math.pi*v*.90)
                            z=petal_radius*(.16+layer*.18)+radius*(.48*(1-v)**2-.14*v+.12*math.sin(u*math.pi+v*2))
                            pt=Vector((r*math.cos(ang),r*math.sin(ang),z))
                            verts.append(center+q@pt)
                    for vj in range(nv):
                        for uj in range(nu):
                            a0=vj*(nu+1)+uj;faces.append((a0,a0+1,a0+nu+2,a0+nu+1))
                    blossoms._add(verts,faces,mi if layer<2 else heart)
            flowers+=1
        for idx in idxs:ob.data.materials[idx]=trans
    blossoms.build('Alpine | sculpted garden roses',mats,coll='Landscape',smooth=True,auto_smooth=False,recalc=False)
    print('[alpine] Sculpted rose blooms:',flowers,flush=True)
