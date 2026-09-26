"""Inspect electrical faceplate components against the actual wall meshes, read-only."""
from pathlib import Path
import bpy,json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
S=bpy.context.scene;S.frame_set(1);dg=bpy.context.evaluated_depsgraph_get()
walls=[(o.name,BVHTree.FromObject(o,dg)) for o in bpy.data.objects if o.name.startswith('Ext_Walls_')]
report=[]
for ob in bpy.data.objects:
 if ob.type!='MESH' or not ob.name.startswith(('Front_','Back_','Up_')):continue
 mids={i for i,m in enumerate(ob.data.materials) if m and ('plate' in m.name.lower() or (ob.name=='Back_FamAccessories' and i==7))}
 if not mids:continue
 adj={}
 for poly in ob.data.polygons:
  if poly.material_index not in mids:continue
  ids=list(poly.vertices)
  for a,b in zip(ids,ids[1:]+ids[:1]):adj.setdefault(a,set()).add(b);adj.setdefault(b,set()).add(a)
 unseen=set(adj)
 while unseen:
  seed=unseen.pop();todo=[seed];ids={seed}
  while todo:
   for k in adj[todo.pop()]:
    if k not in ids:ids.add(k);unseen.discard(k);todo.append(k)
  ps=[ob.matrix_world@ob.data.vertices[i].co for i in ids]
  lo=Vector(tuple(min(p[j] for p in ps) for j in range(3)));hi=Vector(tuple(max(p[j] for p in ps) for j in range(3)));size=hi-lo;center=(lo+hi)/2
  axis=0 if size.x<size.y else 1
  if not (.004<size[axis]<.010 and .06<max(size.x,size.y)<.13 and .105<size.z<.125):continue
  hits=[]
  for sign in (-1,1):
   d=Vector((0,0,0));d[axis]=sign
   for name,tree in walls:
    pt,n,index,dist=tree.ray_cast(center,d,.4)
    if pt is not None:hits.append((dist,name,list(pt),sign))
  best=min(hits) if hits else None
  report.append({'object':ob.name,'center':list(center),'size':list(size),'vertex_count':len(ids),'wall_distance':best[0] if best else None,'nearest_wall':best[1:] if best else None})
import sys
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
output = Path(args[0]) if args else Path(__file__).parent / 'output/audit/electrical.json'
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(report, indent=2))
bad = [row for row in report if row['wall_distance'] is None or row['wall_distance'] > .055]
print(json.dumps({'plates_checked': len(report), 'not_close_to_wall': bad}, indent=2), flush=True)
if bad:
    raise ValueError('Electrical plates need wall backing; see ' + str(output))
