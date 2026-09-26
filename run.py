"""Headless build + render driver for any house under houses/ (Blender 5.x, Cycles / Metal).

  blender -b --python run.py -- --house walsh --cam hero,entry --samples 32 --scale 50     # quick preview
  blender -b --python run.py -- --house walsh --cam all --samples 160 --res 2560x1440      # every view, promo quality
  blender -b --python run.py -- --house walsh --norender --save                           # -> output/<BLEND>
  blender -b --python run.py -- --house walsh --only exterior,site --cam hero --suffix _t # build a subset of modules
  blender -b --python run.py -- --house walsh --film take --film-preview                  # Workbench path check + clearance
  blender -b --python run.py -- --house walsh --film-encode --film take                   # cut + titles -> output/film/<name>_promo.mp4

A house package (houses/<name>/) supplies
  plan.py    levels / plan constants / ROOMS (bpy-free)
  house.py   config: MODULES, CAMS, EXT, EXPOSURE, DOF, SKY, GRASS, DOORS, PROBE_WALLS, PHOTO_PAIRS, materials() (bpy-free)
  shots.py   film SHOTS / TAKE / BY_NAME / TITLES (bpy-free)
  <module>.py for every MODULES entry, each exposing build(M) - the geometry, built in order
Everything else (mesh builder, materials, parts, trees, sky, polish, cameras, render settings, film) is archviz/.
Output: houses/<name>/output/{renders,film,flicker,<BLEND>}.  HOUSE_HIDE="Name1,Name2" hides objects by name prefix.
"""
import sys, os, math, argparse, time, importlib
import bpy

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
for m in list(sys.modules):                    # Blender keeps modules alive between runs in one process
    if m.startswith(("archviz", "houses")):
        del sys.modules[m]

# ---------------------------------------------------------------- args
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--house", default=os.environ.get("HOUSE", ""), help="houses/<name> (or env HOUSE)")
ap.add_argument("--cam", default="hero", help="camera name(s), 'all', 'ext' or 'int'")
ap.add_argument("--samples", type=int, default=256)
ap.add_argument("--device", default=os.environ.get("ARCHVIZ_DEVICE", "AUTO"),
                choices=["AUTO", "CPU", "OPTIX", "CUDA", "HIP", "ONEAPI", "METAL"])
ap.add_argument("--scale", type=int, default=100)
ap.add_argument("--res", default="1920x1080")
ap.add_argument("--save", action="store_true", help="write output/<BLEND>")
ap.add_argument("--out", default="", help="render directory (default output/renders)")
ap.add_argument("--norender", action="store_true")
ap.add_argument("--only", default="", help="comma list of modules to build (default all)")
ap.add_argument("--skip", default="", help="comma list of modules to skip")
ap.add_argument("--threshold", type=float, default=0.02)
ap.add_argument("--time-limit", type=float, default=0.0)
ap.add_argument("--list-cams", action="store_true")
ap.add_argument("--suffix", default="")
ap.add_argument("--no-polish", action="store_true", help="skip grass / leaf particles / bloom / DoF (faster previews)")
ap.add_argument("--no-dof", action="store_true")
# promo film (archviz/film.py): --film all|shot,shot [--film-frames a-b] [--film-step N] [--film-preview] ; --film-encode
ap.add_argument("--film", default="", help="render film shots: 'all' or a comma list of shot names")
ap.add_argument("--film-frames", default="", help="frame range within the shot, e.g. 1-48")
ap.add_argument("--film-step", type=int, default=1)
ap.add_argument("--film-preview", action="store_true", help="Workbench 640x360 path check instead of Cycles")
ap.add_argument("--film-draft", action="store_true", help="quick Cycles cut: 960x540, 24 spp, every 2nd frame -> film/draft/")
ap.add_argument("--film-raw", action="store_true", help="with --film-encode: use the raw frames even if temporally filtered ones exist")
ap.add_argument("--film-vectors", action="store_true", help="render the motion-vector pass (v_####.exr) for the shots instead of the picture")
ap.add_argument("--film-encode", action="store_true", help="assemble film frames + titles into an mp4 (no build)")
ap.add_argument("--film-out", default="", help="mp4 path for --film-encode (default output/film/<name>_promo.mp4)")
ap.add_argument("--film-stills", default="", help="with --film-encode: comma list of sequence frames to write as PNG instead of the mp4")
ap.add_argument("--film-music", default="", help="with --film-encode: audio file to lay under the cut")
ap.add_argument("--no-mblur", action="store_true")
ap.add_argument("--min-samples", type=int, default=0)
ap.add_argument("--clamp-indirect", type=float, default=10.0)
ap.add_argument("--filter-glossy", type=float, default=1.0)
ap.add_argument("--light-floor", type=float, default=0.0, help="minimum shadow_soft_size for point/spot lights (softer, more stable)")
ap.add_argument("--flicker", default="", help="temporal-noise test: render N identical frames (animated seed) of this camera to output/flicker/<tag>/")
ap.add_argument("--flicker-frames", type=int, default=10)
ap.add_argument("--probe", action="store_true", help="print passability maps of the interior walls (house.PROBE_WALLS) and exit")
args = ap.parse_args(argv)
if not args.house:
    sys.exit("run.py: --house <name> is required (a directory under houses/)")

import houses
H = houses.load(args.house)
P = importlib.import_module(f"houses.{args.house}.plan")
HOUSE_DIR = houses.path(args.house)
OUT = houses.path(args.house, "output")
FILM_DIR = os.environ.get("HOUSE_FILM_DIR", os.path.join(OUT, "film"))
args.out = args.out or os.path.join(OUT, "renders")
from archviz import filmkit, lights, materials
filmkit.configure(FILM_DIR)
lights.set_rooms(getattr(P, "ROOMS", {}))
SHOTS = list(getattr(H, "SHOTS", []))
BY_NAME = dict(getattr(H, "BY_NAME", {s['name']: s for s in SHOTS}))
DOORS = getattr(H, "DOORS", None)


def titles():
    """PIL lives in system python, not Blender's: regenerate the title overlays through tools/film_tools.py."""
    import subprocess
    subprocess.run([os.environ.get("ARCHVIZ_PYTHON", "python3"), os.path.join(ROOT, "tools", "film_tools.py"), "--house", args.house, "titles"], check=True)


if args.film_encode:
    from archviz import film
    if args.film_preview:
        filmkit.FRAMES = "preview"
    if args.film_draft:
        filmkit.FRAMES = "draft"
        args.film_out = args.film_out or os.path.join(FILM_DIR, f"{args.house}_promo_draft.mp4")
    shots = SHOTS if args.film in ("", "all") else [BY_NAME[n] for n in args.film.split(",")]
    stills = [int(v) for v in args.film_stills.split(",") if v]
    titles()
    mp4 = args.film_out or os.path.join(FILM_DIR, f"{args.house}_promo.mp4")
    print("[film] mp4 ->", film.assemble(mp4, shots, filmkit.titles_dir(), stills=stills, music=args.film_music or None, tf=not args.film_raw))
    sys.exit(0)

# ---------------------------------------------------------------- reset
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
for blk in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras,
            bpy.data.textures, bpy.data.worlds, bpy.data.collections, bpy.data.curves):
    for x in list(blk):
        blk.remove(x)
S = bpy.context.scene
S.unit_settings.system = 'METRIC'

# ---------------------------------------------------------------- geometry
t0 = time.time()
M = H.materials() if hasattr(H, "materials") else materials.build_materials()
only = [m for m in args.only.split(",") if m]
skip = [m for m in args.skip.split(",") if m]
for name in H.MODULES:
    if (only and name not in only) or name in skip:
        continue
    t1 = time.time()
    mod = importlib.import_module(f"houses.{args.house}.{name}")
    mod.build(M)
    print(f"[build] {name:15s} {time.time() - t1:5.1f}s  objects={len(bpy.data.objects)}")
if not args.no_polish and not only:
    from archviz import polish
    t1 = time.time()
    polish.build(M, grass=getattr(H, "GRASS", ()))
    print(f"[build] polish            {time.time() - t1:5.1f}s  (grass + leaf cards)")
print(f"[build] geometry done in {time.time() - t0:.1f}s, objects={len(bpy.data.objects)}, "
      f"tris~{sum(len(o.data.polygons) for o in bpy.data.objects if o.type == 'MESH')}")

# ---------------------------------------------------------------- sun + sky (archviz/sky.py; tools/sky_test.py renders it alone)
from archviz import sky as _sky
SKY = dict(getattr(H, "SKY", {}))
sun_dir = SKY.get("sun_dir")
sun = _sky.setup_sun(energy=SKY.get("sun_energy", 2.2), color=SKY.get("sun_color", (1.0, 0.80, 0.62)), sun_dir=sun_dir)
_sky.setup_world(S, strength=SKY.get("strength", 0.55), sun_elevation=SKY.get("sun_elevation", 1.2), sun_dir=sun_dir)
if hasattr(H, "setup_scene"):
    H.setup_scene(S)

# ---------------------------------------------------------------- cameras
from archviz.mesh import collection, look_at
CAMS = H.CAMS
EXT = list(getattr(H, "EXT", []))
INT = [c for c in CAMS if c not in EXT]
EXPOSURE = dict(getattr(H, "EXPOSURE", {}))
EXP_DEF = dict({'ext': 0.6, 'int': 0.3}, **getattr(H, "EXPOSURE_DEFAULT", {}))
DOF = dict(getattr(H, "DOF", {}))
DOF_DEF = dict({'ext': 11.0, 'int': 4.5}, **getattr(H, "DOF_DEFAULT", {}))
if args.list_cams:
    print("cameras:", ", ".join(CAMS)); sys.exit(0)


def exposure_of(name):
    return EXPOSURE.get(name, EXP_DEF['ext'] if name in EXT else EXP_DEF['int'])


cam_objs = {}
for name, (loc, tgt, lens) in CAMS.items():
    cd = bpy.data.cameras.new(f"Cam_{name}")
    cd.lens = lens
    cd.sensor_width = 36
    cd.clip_start = 0.05
    cd.clip_end = getattr(H, "CAM_CLIP", {}).get(name, 800)     # optional per-camera far clip (drone views to the horizon)
    co = bpy.data.objects.new(f"Cam_{name}", cd)
    co.location = loc
    collection('Cameras').objects.link(co)
    look_at(co, tgt)
    cam_objs[name] = co
    shift = getattr(H, "CAM_SHIFT", {}).get(name)          # optional lens shift (perspective-corrected photos)
    if shift:
        cd.shift_x, cd.shift_y = shift
    roll = getattr(H, "CAM_ROLL", {}).get(name)            # optional roll in degrees (hand-held / drone photos)
    if roll:
        from mathutils import Matrix
        co.rotation_euler = (co.rotation_euler.to_matrix() @ Matrix.Rotation(math.radians(-roll), 3, 'Z')).to_euler()
    if not args.no_polish and not args.no_dof:
        from archviz import polish
        polish.set_dof(co, tgt, DOF.get(name, DOF_DEF['ext'] if name in EXT else DOF_DEF['int']))

# ---------------------------------------------------------------- render settings
S.render.engine = 'CYCLES'
from archviz.rendering import configure_device
configure_device(S, args.device)
cy = S.cycles
cy.samples = args.samples
cy.use_adaptive_sampling = True
cy.adaptive_threshold = args.threshold
cy.time_limit = args.time_limit
cy.use_denoising = True
cy.denoiser = 'OPENIMAGEDENOISE'
cy.max_bounces = 12
cy.diffuse_bounces = 4
cy.glossy_bounces = 6
cy.transmission_bounces = 14
cy.transparent_max_bounces = 32
cy.volume_bounces = 1
cy.caustics_reflective = False
cy.caustics_refractive = False
cy.blur_glossy = args.filter_glossy
cy.sample_clamp_indirect = args.clamp_indirect
cy.adaptive_min_samples = args.min_samples
cy.film_exposure = 1.0
S.render.use_persistent_data = True
w, h = [int(v) for v in args.res.lower().split("x")]
S.render.resolution_x, S.render.resolution_y = w, h
S.render.resolution_percentage = args.scale
S.render.image_settings.file_format = 'PNG'
S.render.image_settings.color_depth = '8'
S.view_settings.view_transform = 'AgX'
S.view_settings.look = 'AgX - Medium High Contrast'
if not args.no_polish:
    from archviz import polish
    polish.setup_compositor(S)
S.view_settings.exposure = 0.6
S.view_settings.gamma = 1.0

# fill lights must never be seen as glowing spheres in glass reflections / through water (emissive fixtures do that job)
for ob in bpy.data.objects:
    if ob.type == 'LIGHT' and ob.data.type in ('POINT', 'SPOT', 'AREA'):
        ob.visible_glossy = False          # ray visibility lives on the object in 4.x/5.x
        ob.visible_transmission = False
        ob.visible_camera = False
if args.light_floor > 0:
    for ld in bpy.data.lights:
        if ld.type in ('POINT', 'SPOT') and ld.shadow_soft_size < args.light_floor:
            ld.shadow_soft_size = args.light_floor
for pref in [x for x in os.environ.get("HOUSE_HIDE", "").split(",") if x]:
    for ob in bpy.data.objects:
        if ob.name.startswith(pref):
            ob.hide_render = True
os.makedirs(args.out, exist_ok=True)
if args.save:
    blend = os.environ.get("HOUSE_BLEND") or os.path.join(OUT, getattr(H, "BLEND", f"{args.house}.blend"))   # HOUSE_BLEND=/tmp/x.blend for scratch saves
    os.makedirs(os.path.dirname(os.path.abspath(blend)), exist_ok=True)
    from archviz.rendering import pack_scene
    pack_scene()
    bpy.ops.wm.save_as_mainfile(filepath=blend)
    print("[save]", blend)

# ---------------------------------------------------------------- modes
if args.probe:
    from archviz import film
    if getattr(H, "STAIR_PROBE", None):
        film.probe_stair(S, **H.STAIR_PROBE)
    film.probe_openings(S, getattr(H, "PROBE_WALLS", []))
    sys.exit(0)
if args.flicker:
    tag = f"{args.flicker}_s{args.samples}_t{args.threshold}_m{args.min_samples}_c{args.clamp_indirect:g}_lf{args.light_floor:g}"
    d = os.path.join(OUT, "flicker", tag)
    os.makedirs(d, exist_ok=True)
    S.camera = cam_objs[args.flicker]
    S.view_settings.exposure = exposure_of(args.flicker)
    cy.use_animated_seed = True
    S.frame_start, S.frame_end = 1, args.flicker_frames
    S.render.filepath = os.path.join(d, "f_")
    t1 = time.time()
    bpy.ops.render.render(animation=True)
    print(f"[flicker] {tag}: {args.flicker_frames} frames in {time.time() - t1:.0f}s ({(time.time() - t1) / args.flicker_frames:.1f} s/frame)")
    sys.exit(0)
if args.film:
    from archviz import film
    shots = SHOTS if args.film == 'all' else [BY_NAME[n] for n in args.film.split(",")]
    frames = tuple(int(v) for v in args.film_frames.split("-")) if args.film_frames else None
    if args.film_preview:
        S.render.engine = 'BLENDER_WORKBENCH'
        filmkit.FRAMES = "preview"
        S.display.shading.light = 'STUDIO'
        S.display.shading.color_type = 'MATERIAL'
        S.render.resolution_x, S.render.resolution_y = 640, 360
        S.render.resolution_percentage = 100
        S.render.use_motion_blur = False
    else:
        S.render.use_motion_blur = not args.no_mblur
        S.render.motion_blur_shutter = 0.35            # 126-degree shutter: crisp but not strobing
        cy.use_animated_seed = True
    if args.film_draft:
        filmkit.FRAMES = "draft"
        S.render.resolution_x, S.render.resolution_y = 960, 540
        S.render.resolution_percentage = 100
        cy.samples, cy.adaptive_threshold = 24, 0.05
        args.film_step = max(args.film_step, 2)
    for shot in shots:
        if args.film_preview:
            if 'keys' in shot:
                if DOORS and 'door_t' in shot:
                    film.open_doors(S, DOORS, frame_open=int(round(shot['door_t'] * filmkit.FPS)) + 1, seconds=shot.get('door_secs', 1.6))
                film.clearance_take(S, shot)
            else:
                film.clearance(S, shot)
        film.render_shot(S, shot, frames=frames, step=args.film_step, vectors=args.film_vectors, doors=DOORS)
elif not args.norender:
    names = {'all': list(CAMS), 'ext': EXT, 'int': INT, 'photos': [c for c, _ in getattr(H, "PHOTO_PAIRS", [])]}.get(
        args.cam, args.cam.split(","))
    for name in names:
        S.camera = cam_objs[name]
        S.view_settings.exposure = exposure_of(name)      # interiors: neutral exposure (rooms are lit by their own lights)
        if hasattr(H, "before_render"):                   # optional per-camera setup (e.g. each photo's sun position)
            H.before_render(S, name)
        res = getattr(H, "CAM_RES", {}).get(name)          # optional per-camera resolution (photo aspect ratio)
        S.render.resolution_x, S.render.resolution_y = res if res else (w, h)
        asp = getattr(H, "CAM_ASPECT", {}).get(name)       # keystone-corrected photos with an aspect change: taller render
        shear = getattr(H, "CAM_SHEAR", {}).get(name, 0.0)  # ... and a horizontal shear k: out(x, y) = render(x - k (y - H/2), y)
        ovs = getattr(H, "CAM_OVERSCAN", {}).get(name, 0)  # extra render width per side (px) so the shear leaves no empty wedges
        fw, fh = S.render.resolution_x, S.render.resolution_y
        if asp or shear or ovs:
            S.camera.data.sensor_fit = 'HORIZONTAL'       # (the house scales lens / shift for the overscan width itself)
            S.render.resolution_x = fw + 2 * ovs
            S.render.resolution_y = round(fh / (asp or 1.0))
        S.render.filepath = os.path.join(args.out, f"{name}{args.suffix}.png")
        t1 = time.time()
        bpy.ops.render.render(write_still=True)
        if asp or shear or ovs:                             # back to the photo's frame (system python has PIL)
            import subprocess
            pct = S.render.resolution_percentage / 100.0
            subprocess.run([os.environ.get("ARCHVIZ_PYTHON", "python3"), "-c",
                            "import sys;from PIL import Image;p,fw,fh,m,k=sys.argv[1],*map(float,sys.argv[2:]);im=Image.open(p);"
                            "im=im.resize((im.width,round(fh)),Image.LANCZOS);"
                            "im=im.transform((round(fw),round(fh)),Image.AFFINE,(1,-k,k*fh/2+m,0,1,0),Image.BICUBIC) if (k or m) else im;im.save(p)",
                            S.render.filepath, str(fw * pct), str(fh * pct), str(ovs * pct), str(shear)], check=True)
        print(f"[render] {name} -> {S.render.filepath} ({time.time() - t1:.0f}s)")
