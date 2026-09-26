"""Ray-cast pixels of a house camera in a saved .blend and report what they hit (object, material, world point).

  blender -b houses/webster/output/webster.blend --python tools/pixel_probe.py -- prim 400,190 900,300  bath_a 1200,250
Pixels are given for the configured render resolution (default 1920x1080).  Use it to identify the object behind an
artefact seen in a render without guessing from names.
"""
import sys, bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
S = bpy.context.scene
W, Hh = S.render.resolution_x, S.render.resolution_y
dg = bpy.context.evaluated_depsgraph_get()
cam = None
for a in argv:
    if "," not in a:
        cam = bpy.data.objects.get("Cam_" + a) or bpy.data.objects.get(a)
        print(f"== camera {a}: {'ok' if cam else 'MISSING'}")
        continue
    px, py = [float(v) for v in a.split(",")]
    fr = cam.data.view_frame(scene=S)              # camera space corners: [top-right, bottom-right, bottom-left, top-left]
    tr, br, bl, tl = fr
    u, v = px / W, 1.0 - py / Hh
    p = bl + (br - bl) * u + (tl - bl) * v
    o = cam.matrix_world.translation
    d = (cam.matrix_world @ p) - o
    d.normalize()
    hit, loc, nrm, idx, ob, mat = S.ray_cast(dg, o, d, distance=500.0)
    if not hit:
        print(f"  ({px:.0f},{py:.0f}) -> nothing"); continue
    m = None
    try:
        ev = ob.evaluated_get(dg)
        poly = ev.data.polygons[idx]
        m = ev.data.materials[poly.material_index].name if ev.data.materials else None
    except Exception as e:
        m = f"? {e}"
    print(f"  ({px:.0f},{py:.0f}) -> {ob.name:32s} mat={m}  at=({loc.x:.2f},{loc.y:.2f},{loc.z:.2f}) n=({nrm.x:.2f},{nrm.y:.2f},{nrm.z:.2f}) dist={(loc-o).length:.2f}")
