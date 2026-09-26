"""Render the dusk sky alone (a ground plane + a white box and a travertine box for scale) from three directions.
  blender -b --python tools/sky_test.py -- [--out file.png] [--elev DEG] [--strength S] [--sun x,y,z]
default output: scratch/sky_test_{hero,west,north}.png"""
import sys, os, math
import bpy
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
for m in list(sys.modules):
    if m.startswith("archviz"):
        del sys.modules[m]
from archviz import sky, materials
from archviz.rendering import configure_device
from archviz.mesh import *
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
out = "scratch/sky_test.png"; elev = 1.2; strength = 0.55; sun_dir = None
i = 0
while i < len(argv):
    if argv[i] == "--out": out = argv[i + 1]; i += 2
    elif argv[i] == "--elev": elev = float(argv[i + 1]); i += 2
    elif argv[i] == "--strength": strength = float(argv[i + 1]); i += 2
    elif argv[i] == "--sun": sun_dir = tuple(float(v) for v in argv[i + 1].split(",")); i += 2
    else: i += 1
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
S = bpy.context.scene
M = materials.build_materials()
g = MB(); g.box(-200, 200, -200, 200, -0.2, 0.0); g.build("Ground", M['hill'])
w = MB(); w.box(-6, 6, 10, 12, 0, 6); w.build("Box", M['white'])
t = MB(); t.box(6.5, 8.5, 10, 12, 0, 6); t.build("Box2", M['trav'])
sky.setup_world(S, strength=strength, sun_elevation=elev, sun_dir=sun_dir)
sky.setup_sun(sun_dir=sun_dir)
cams = {'hero': ((18.5, -10.0, 2.6), (4.0, 4.5, 4.6), 21), 'west': ((0, 0, 2), (-30, -10, 8), 24), 'north': ((0, 0, 2), (0, 40, 12), 24)}
configure_device(S)  # ARCHVIZ_DEVICE=AUTO|CPU|OPTIX|CUDA|HIP|ONEAPI|METAL
S.cycles.samples = 32; S.cycles.use_denoising = True
S.render.resolution_x, S.render.resolution_y = 960, 540
S.view_settings.view_transform = 'AgX'; S.view_settings.look = 'AgX - Medium High Contrast'; S.view_settings.exposure = 0.6
out = out if os.path.isabs(out) else os.path.join(ROOT, out)
os.makedirs(os.path.dirname(out), exist_ok=True)
for name, (loc, tgt, lens) in cams.items():
    cd = bpy.data.cameras.new(name); cd.lens = lens
    co = bpy.data.objects.new(name, cd); S.collection.objects.link(co)
    co.location = loc; look_at(co, tgt)
    S.camera = co
    S.render.filepath = out.replace(".png", f"_{name}.png")
    bpy.ops.render.render(write_still=True)
print("saved", out)
