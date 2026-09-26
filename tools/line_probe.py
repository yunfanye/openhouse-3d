"""Scan a saved .blend along line segments and print every surface crossed (object / material / point / normal).

  blender -b houses/webster/output/webster.blend --python tools/line_probe.py -- 3.0,9.0,5.4 6.0,9.0,5.4  4.6,9.0,8.0 4.6,9.0,5.0
Each pair of points is one segment; hits are found by repeated ray casts (front and back faces both count).
"""
import sys, bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
S = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()
pts = [Vector([float(v) for v in a.split(",")]) for a in argv]
for i in range(0, len(pts) - 1, 2):
    a, b = pts[i], pts[i + 1]
    d = (b - a); L = d.length; d.normalize()
    print(f"== segment {tuple(round(v, 2) for v in a)} -> {tuple(round(v, 2) for v in b)}")
    o = a.copy(); travelled = 0.0; n_hits = 0
    while travelled < L and n_hits < 40:
        hit, loc, nrm, idx, ob, mat = S.ray_cast(dg, o, d, distance=L - travelled)
        if not hit:
            break
        m = None
        try:
            ev = ob.evaluated_get(dg); poly = ev.data.polygons[idx]
            m = ev.data.materials[poly.material_index].name if ev.data.materials else None
        except Exception:
            pass
        print(f"   t={(loc - a).length:6.3f}  {ob.name:28s} {str(m):22s} at=({loc.x:.3f},{loc.y:.3f},{loc.z:.3f}) n=({nrm.x:.2f},{nrm.y:.2f},{nrm.z:.2f})")
        travelled = (loc - a).length + 0.002
        o = a + d * travelled
        n_hits += 1
