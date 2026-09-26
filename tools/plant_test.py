"""Render a lineup of archviz.plants species in a neutral studio (a quick check of every leaf shader / species).

  blender -b --python tools/plant_test.py -- [--scale 50] [--samples 48] [--out scratch/plants.png] [--kinds fiddle,fern]
"""
import sys, os, math, argparse
import bpy
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
for m in list(sys.modules):
    if m.startswith("archviz"):
        del sys.modules[m]
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--scale", type=int, default=50); ap.add_argument("--samples", type=int, default=48)
ap.add_argument("--out", default=os.path.join(ROOT, "scratch", "plants.png")); ap.add_argument("--kinds", default="")
ap.add_argument("--cam", default="wide", help="wide | close")
args = ap.parse_args(argv)
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
from archviz import plants, materials as _mat, lights
from archviz.rendering import configure_device
from archviz.mesh import MB, collection, look_at
S = bpy.context.scene
POTS = [('fiddle', 1.7, 'ceramic'), ('monstera', 1.1, 'basket'), ('bird', 1.6, 'concrete'), ('fern', 0.5, 'terracotta'), ('palm', 1.8, 'ceramic'),
        ('snake', 0.8, 'black'), ('olive', 1.4, 'terracotta'), ('boxwood', 0.7, 'concrete'), ('citrus', 1.5, 'terracotta'), ('lavender', 0.45, 'terracotta')]
SHR = [('rose', 0.7, 0.9, None), ('hydrangea', 0.8, 0.9, 'hyd_blue'), ('agapanthus', 0.6, 0.8, None), ('oleander', 1.4, 3.0, 'oleander_white'), ('boxwood', 0.6, None, None)]
kinds = [k for k in args.kinds.split(",") if k]
floor = MB(); floor.box(-3, 16, -3, 8, -0.05, 0, 0); floor.box(-3, 16, 7.9, 8, 0, 3, 0)
floor.build("Studio", [_mat.plaster("StudioGrey", base=(0.55, 0.54, 0.52, 1), rough=0.9, grain=0.05)], coll='House')
x = 0.0
for i, (k, h, pot) in enumerate(POTS):
    if kinds and k not in kinds:
        continue
    plants.potted(f"Pot_{k}", (x, 0.0, 0.0), kind=k, height=h, pot=pot, seed=i + 1)
    x += 1.5
x = 0.5
for i, (k, r, h, col) in enumerate(SHR):
    if kinds and k not in kinds:
        continue
    plants.shrub(f"Shrub_{k}", (x, 4.0, 0.0), r=r, h=h, kind=k, seed=i + 11, colour=col)
    x += 2.6 if k != 'oleander' else 3.6
plants.hedge("Hedge", 9.5, 13.5, 3.6, 4.4, 0.0, 1.0, seed=5)
v = MB(); v.lathe(13.5, 0.0, 0.0, [(0, 0), (0.07, 0), (0.09, 0.15), (0.06, 0.3), (0.05, 0.32), (0, 0.32)], seg=20, mi=0)
v.lathe(14.5, 0.0, 0.0, [(0, 0), (0.06, 0), (0.07, 0.2), (0.04, 0.28), (0, 0.28)], seg=20, mi=0)
v.lathe(15.5, 0.0, 0.0, [(0, 0), (0.06, 0), (0.07, 0.2), (0.04, 0.28), (0, 0.28)], seg=20, mi=0)
v.build("Vases", [_mat.new_mat("VaseWhite", (0.9, 0.9, 0.88, 1), rough=0.3, coat=0.4)], coll='House')
plants.stems("Stems_euc", (13.5, 0.0, 0.32), kind='eucalyptus', height=0.7, seed=3)
plants.stems("Stems_olive", (14.5, 0.0, 0.28), kind='olive', height=0.6, seed=4)
plants.stems("Stems_mag", (15.5, 0.0, 0.28), kind='magnolia', height=0.6, seed=5)
# light + camera
sun = bpy.data.lights.new("Sun", 'SUN'); sun.energy = 3.0; sun.angle = math.radians(2)
so = bpy.data.objects.new("Sun", sun); collection('Lights').objects.link(so); so.rotation_euler = (math.radians(50), 0, math.radians(-30))
w = bpy.data.worlds.new("W"); w.use_nodes = True; S.world = w
w.node_tree.nodes["Background"].inputs[0].default_value = (0.6, 0.7, 0.85, 1); w.node_tree.nodes["Background"].inputs[1].default_value = 0.8
cd = bpy.data.cameras.new("Cam"); cd.lens = 28 if args.cam == 'wide' else 50
co = bpy.data.objects.new("Cam", cd); collection('Cameras').objects.link(co)
if args.cam == 'wide':
    co.location = (6.5, -9.5, 3.2); look_at(co, (6.5, 2.0, 0.8))
elif "," in args.cam:
    px, py, pz, tx, ty, tz, lens = [float(v) for v in args.cam.split(",")]
    co.location = (px, py, pz); look_at(co, (tx, ty, tz)); cd.lens = lens
else:
    co.location = (2.0, -4.0, 1.4); look_at(co, (2.2, 0.0, 0.8))
S.camera = co
configure_device(S)  # ARCHVIZ_DEVICE=AUTO|CPU|OPTIX|CUDA|HIP|ONEAPI|METAL
S.cycles.samples = args.samples; S.cycles.use_denoising = True; S.cycles.adaptive_threshold = 0.05
S.cycles.transparent_max_bounces = 32
S.render.resolution_x, S.render.resolution_y = 2560, 1080; S.render.resolution_percentage = args.scale
S.view_settings.view_transform = 'AgX'; S.view_settings.exposure = 0.3
S.render.filepath = args.out
n_tris = sum(len(o.data.polygons) for o in bpy.data.objects if o.type == 'MESH')
print(f"[plants] objects={len(bpy.data.objects)} faces={n_tris}")
bpy.ops.render.render(write_still=True)
print("[plants] wrote", args.out)
