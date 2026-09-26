"""13695 Stanford Dr, Carmel IN — house configuration read by run.py and the tools (bpy-free at import).

Geometry modules (MODULES) each expose build(M) and are built in order.  Ownership:
  exterior        every exterior wall in plan.WALLS (+ openings), cladding (lap siding, brick veneer), trim, window /
                  door units, shutters, porch, all roofs with fascia / soffit / gutters / downspouts, exterior lights
  interior_main   main-floor partitions, skins, doors, kitchen, fireplace, great room + dining staging, their lights
  interior_front  foyer, living room, hall, stair, powder room and garage: floors, staging, fixtures, lights
  interior_upper  upper-floor partitions, finishes, fixtures, furniture and lamps
  site            the lot and the street: lawns, driveway, walks, beds, patio, fence, adjacent neighbour houses
  context         the common lawn, path, pond + fountain, common-area trees, houses across the pond, the suburb
  landscape       lot vegetation: trees, shrubs, grasses, beds (tree() is also used by context)
Photo cameras: exterior views here (CAMS), site / aerial views in cams_site.py, interiors in cams_main / cams_upper.
"""
from .plan import *
from .shots import SHOTS, TAKE, BY_NAME, TITLES

NAME = "stanford"
TITLE = "13695 Stanford Dr, Carmel IN"
BLEND = "stanford.blend"
MODULES = ["exterior", "interior_main", "interior_front", "interior_upper", "site", "context", "landscape"]


def materials():
    """The default library plus this house's palette (keys used by every module)."""
    from archviz import materials as _m
    M = _m.build_materials()
    # ---- exterior (photos 01-03, 25-31)
    M['siding'] = _m.painted_board("SidingBlueGrey", base=(0.385, 0.41, 0.45, 1), rough=0.55, grain=0.2)   # patch-calibrated (EXT)
    M['siding_back'] = _m.new_mat("SidingShadow", (0.06, 0.08, 0.11, 1), rough=0.8)
    M['trim'] = _m.painted_board("TrimWhite", base=(0.80, 0.80, 0.78, 1), rough=0.45, grain=0.05)
    M['vinyl'] = _m.new_mat("VinylWhite", (0.82, 0.82, 0.80, 1), rough=0.32, spec=0.5)
    M['soffit'] = _m.new_mat("SoffitWhite", (0.78, 0.78, 0.76, 1), rough=0.55)
    M['gutter'] = _m.new_mat("GutterWhite", (0.84, 0.84, 0.82, 1), rough=0.28, spec=0.6, coat=0.3)
    BR = dict(base=(0.40, 0.050, 0.030, 1), alt=(0.52, 0.075, 0.042, 1), dark=(0.17, 0.035, 0.025, 1), mortar=(0.46, 0.44, 0.41, 1),
              mortar_w=0.008, dark_frac=0.15, accent=(0.58, 0.16, 0.07, 1), accent_frac=0.07, tone_var=0.18, relief=0.8)
    M['brick'] = _m.brick_veneer("BrickRedX", 'XZ', **BR)
    M['brick_y'] = _m.brick_veneer("BrickRedY", 'YZ', **BR)
    M['brick_sol'] = _m.brick_veneer("BrickSoldierX", 'XZ', soldier=True, **BR)
    M['brick_sol_y'] = _m.brick_veneer("BrickSoldierY", 'YZ', soldier=True, **BR)
    M['shingle'] = _m.shingles("ShinglesWeatheredGrey", c1=(0.160, 0.142, 0.124, 1), c2=(0.185, 0.166, 0.147, 1), c3=(0.118, 0.103, 0.090, 1),
                               tint=(0.185, 0.150, 0.115, 1), tint_amt=0.15, granule=(1.5, 1.45, 1.4, 1), butt_dark=0.45, spec=0.15, grazing=0.25)
    M['brick_row'] = M['brick_sol']                    # rowlock sills / door step: header ends on edge (same scale as soldiers)
    M['precast'] = _m.noise_mat("PrecastKeystone", (0.62, 0.58, 0.50, 1), (0.74, 0.70, 0.62, 1), scale=30, bump=0.25, rough=0.8)
    M['galvanised'] = _m.new_mat("GalvanisedVent", (0.55, 0.56, 0.56, 1), rough=0.35, metal=0.9)
    M['garage_navy'] = _m.new_mat("GarageDoorSlate", (0.13, 0.145, 0.215, 1), rough=0.6, spec=0.15)
    M['navy'] = _m.new_mat("NavyDoor", (0.065, 0.082, 0.14, 1), rough=0.42, spec=0.5, coat=0.25)   # 03 patch (shaded porch)
    M['shutter'] = _m.new_mat("ShutterNavy", (0.026, 0.031, 0.052, 1), rough=0.55, spec=0.4)
    M['win_glass'] = _m.new_mat("WindowGlass", (0.92, 0.95, 0.95, 1), rough=0.0, transmission=1.0, ior=1.5, spec=0.5)   # exterior photos: tinted in exterior.before_render
    M['nickel'] = _m.new_mat("SatinNickel", (0.72, 0.71, 0.69, 1), rough=0.28, metal=1.0)
    M['iron_black'] = _m.new_mat("LanternBlack", (0.02, 0.02, 0.022, 1), rough=0.45, metal=0.6)
    M['lantern_glass'] = _m.new_mat("LanternGlass", (0.55, 0.55, 0.50, 1), rough=0.25, transmission=0.8, ior=1.45)   # seeded glass (03)
    M['concrete'] = _m.tiles("DriveConcrete", (0.40, 0.385, 0.36, 1), grout=(0.22, 0.21, 0.20, 1), size=(3.0, 3.0), gap=0.008,
                             rough=0.85, variation=0.04, mottle=0.45, bump=0.15)
    M['walk'] = _m.tiles("WalkConcrete", (0.42, 0.40, 0.37, 1), grout=(0.22, 0.21, 0.20, 1), size=(1.5, 1.5), gap=0.008,
                         rough=0.85, variation=0.04, mottle=0.4, bump=0.15)
    M['porch_slab'] = _m.noise_mat("PorchConcrete", (0.50, 0.48, 0.44, 1), (0.60, 0.58, 0.54, 1), scale=6, bump=0.1, rough=0.85)
    M['foundation'] = _m.noise_mat("Foundation", (0.40, 0.39, 0.36, 1), (0.52, 0.51, 0.48, 1), scale=10, bump=0.2, rough=0.9)
    M['house_number'] = _m.new_mat("PlaqueCream", (0.80, 0.76, 0.66, 1), rough=0.5)
    # ---- interior finishes (photos 04-23)
    # main-floor walls: a light grey-blue (photos 08-14 read it at V 0.65-0.75, S < 0.04 against warm-white trim and
    # ceiling; the former (0.56, 0.66, 0.74) rendered too saturated and too bright) - INT_GREAT
    M['paint_blue'] = _m.plaster("PaintSkyBlue", base=(0.465, 0.535, 0.60, 1), rough=0.85, grain=0.03)
    M['paint_beige'] = _m.plaster("PaintBeige", base=(0.62, 0.50, 0.38, 1), rough=0.85, grain=0.03)
    M['paint_cream'] = _m.plaster("PaintCream", base=(0.68, 0.58, 0.45, 1), rough=0.85, grain=0.03)
    M['paint_bath'] = _m.plaster("PaintBathBlue", base=(0.60, 0.66, 0.74, 1), rough=0.8, grain=0.03)
    M['paint_white'] = _m.plaster("PaintWhite", base=(0.80, 0.80, 0.78, 1), rough=0.85, grain=0.03)
    # warm off-white knock-down (photos 05/08/09/12/14 ceiling patches ~ sRGB 205/200/192, s 0.04; INT_GREAT, archviz.finishes)
    from archviz import finishes as _fz
    M['ceiling'] = _fz.knockdown_ceiling("KnockdownCeiling", base=(0.74, 0.715, 0.655, 1))
    M['trim_int'] = _m.new_mat("TrimSemiGloss", (0.81, 0.80, 0.77, 1), rough=0.3, spec=0.5, coat=0.2)
    # ---- site (photos 01, 25-32)
    M['lawn'] = _m.turf("LawnKentucky", c_dark=(0.10, 0.16, 0.010, 1), c_light=(0.28, 0.36, 0.022, 1))
    M['lawn_rear'] = _m.turf("LawnCommon", c_dark=(0.11, 0.17, 0.012, 1), c_light=(0.29, 0.37, 0.025, 1))
    M['grass'] = _m.grass_blade("GrassBladeKY", root=(0.07, 0.13, 0.010, 1), tip=(0.46, 0.58, 0.05, 1), dry=(0.52, 0.50, 0.18, 1), stripes=False)
    M['ground'] = _m.noise_mat("GroundGrass", (0.06, 0.14, 0.035, 1), (0.14, 0.24, 0.06, 1), scale=3, bump=0.2)
    M['concrete_curb'] = _m.noise_mat("CurbConcrete", (0.48, 0.47, 0.44, 1), (0.60, 0.59, 0.56, 1), scale=12, bump=0.1, rough=0.85)
    M['asphalt'] = _m.noise_mat("StreetAsphalt", (0.10, 0.10, 0.10, 1), (0.20, 0.20, 0.19, 1), scale=40, bump=0.25, rough=0.9)
    M['asphalt_path'] = _m.noise_mat("PathAsphalt", (0.06, 0.06, 0.065, 1), (0.13, 0.13, 0.135, 1), scale=40, bump=0.25, rough=0.9)
    M['river_rock'] = _m.noise_mat("RiverRock", (0.46, 0.43, 0.39, 1), (0.78, 0.75, 0.70, 1), scale=55, bump=1.0, detail=3, rough=0.7)
    M['pavers_fan'] = _m.fan_pavers("PatioFanPavers", centre=(6.2, 14.2))
    M['black_rubber'] = _m.new_mat("EdgingBlack", (0.02, 0.02, 0.02, 1), rough=0.6)
    M['siding_beige'] = _m.painted_board("SidingBeige", base=(0.62, 0.58, 0.50, 1))
    M['brick_tan'] = _m.brick_veneer("BrickTanX", 'XZ', base=(0.42, 0.33, 0.24, 1), alt=(0.50, 0.40, 0.30, 1), dark=(0.30, 0.23, 0.17, 1), mortar=(0.55, 0.52, 0.47, 1))
    M['siding_sage'] = _m.painted_board("SidingSage", base=(0.30, 0.34, 0.26, 1))
    M['siding_grey'] = _m.painted_board("SidingGrey", base=(0.38, 0.38, 0.36, 1))
    M['siding_white'] = _m.painted_board("SidingWhite", base=(0.55, 0.54, 0.50, 1))
    M['siding_bluegrey'] = _m.painted_board("SidingBlueGrey", base=(0.22, 0.27, 0.32, 1))
    M['siding_mocha'] = _m.painted_board("SidingMocha", base=(0.30, 0.25, 0.20, 1))
    M['siding_tan'] = _m.painted_board("SidingTan", base=(0.46, 0.36, 0.25, 1))
    M['shingle_brown'] = _m.shingles("ShinglesWeatheredWood", c1=(0.27, 0.22, 0.18, 1), c2=(0.33, 0.28, 0.23, 1), c3=(0.21, 0.17, 0.14, 1))
    M['garage_white'] = _m.new_mat("GarageDoorWhite", (0.78, 0.78, 0.76, 1), rough=0.4)
    M['garage_sage'] = _m.new_mat("GarageDoorSage", (0.28, 0.32, 0.26, 1), rough=0.4)
    M['neighbour_glass'] = _m.new_mat("NeighbourGlass", (0.05, 0.06, 0.07, 1), rough=0.05, spec=0.6, coat=0.5)
    M['pond'] = _pond_water(_m)
    M['spray'] = _spray(_m)
    M['foam'] = _foam(_m)
    M['mist'] = _mist(_m)
    return M


def _pond_water(_m):
    """Retention-pond water (photos 26, 30-32): opaque olive-teal body, mirror-like at grazing angles, fine ripples."""
    m = _m.new_mat("PondWater", (0.018, 0.030, 0.028, 1), rough=0.03, spec=0.5, ior=1.33, coat=0.0)
    nt, b = m.node_tree, _m._bsdf(m)
    n = _m._noise(nt, _m._coords(nt, scale=(1.0, 2.5, 1.0)), scale=2.2, detail=4.0, rough=0.55)
    n2 = _m._noise(nt, _m._coords(nt), scale=18.0, detail=2.0)
    h = _m._math(nt, 'ADD', n, _m._math(nt, 'MULTIPLY', n2, 0.35))
    _m._bump(nt, b, h, 0.06, 0.05)
    return m


def _spray(_m):
    """Fountain water: thin arcs broken into droplets by a stretched noise mask (alpha), bright translucent white
    that glows when back-lit; the mask's mapping is driven by the frame in the film so droplets travel."""
    m = _m.new_mat("FountainSpray", (0.92, 0.95, 0.98, 1), rough=0.15, spec=0.6, ior=1.33)
    nt, b = m.node_tree, _m._bsdf(m)
    vec = _m._coords(nt, scale=(20.0, 20.0, 7.0))
    n = _m._noise(nt, vec, scale=1.0, detail=2.0, rough=0.5)
    drop = _m._math(nt, 'GREATER_THAN', n, 0.53)
    tr = nt.nodes.new("ShaderNodeBsdfTranslucent"); tr.inputs["Color"].default_value = (0.95, 0.97, 1.0, 1)
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.95, 0.96, 1.0, 1); em.inputs["Strength"].default_value = 0.6
    mix1 = nt.nodes.new("ShaderNodeMixShader"); mix1.inputs["Fac"].default_value = 0.45
    nt.links.new(mix1.inputs[1], b.outputs["BSDF"]); nt.links.new(mix1.inputs[2], tr.outputs["BSDF"])
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(add.inputs[0], mix1.outputs["Shader"]); nt.links.new(add.inputs[1], em.outputs["Emission"])
    tp = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix2 = nt.nodes.new("ShaderNodeMixShader")
    alpha = _m._math(nt, 'MULTIPLY', drop, 0.85)
    nt.links.new(mix2.inputs["Fac"], alpha)
    nt.links.new(mix2.inputs[1], tp.outputs["BSDF"]); nt.links.new(mix2.inputs[2], add.outputs["Shader"])
    nt.links.new(nt.nodes["Material Output"].inputs["Surface"], mix2.outputs["Shader"])
    return m


def _foam(_m):
    """Churned white water ring under the fountain (alpha-cut noise, fading outward)."""
    m = _m.new_mat("FountainFoam", (0.85, 0.88, 0.88, 1), rough=0.6)
    nt, b = m.node_tree, _m._bsdf(m)
    n = _m._noise(nt, _m._coords(nt, scale=(1.4, 1.4, 1.4)), scale=3.0, detail=6.0, rough=0.65, distortion=0.8)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    ln = nt.nodes.new("ShaderNodeVectorMath"); ln.operation = 'LENGTH'
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(sep.inputs["Vector"], tc.outputs["Object"])
    comb = nt.nodes.new("ShaderNodeCombineXYZ"); nt.links.new(comb.inputs["X"], sep.outputs["X"]); nt.links.new(comb.inputs["Y"], sep.outputs["Y"])
    nt.links.new(ln.inputs[0], comb.outputs["Vector"])
    fall = _m._math(nt, 'SUBTRACT', 1.0, _m._math(nt, 'DIVIDE', ln.outputs["Value"], 5.0, clamp=True))
    a = _m._math(nt, 'MULTIPLY', _m._math(nt, 'GREATER_THAN', _m._math(nt, 'MULTIPLY', n, fall), 0.28), 0.9)
    tp = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(mix.inputs["Fac"], a)
    nt.links.new(mix.inputs[1], tp.outputs["BSDF"]); nt.links.new(mix.inputs[2], b.outputs["BSDF"])
    nt.links.new(nt.nodes["Material Output"].inputs["Surface"], mix.outputs["Shader"])
    return m


def _mist(_m):
    import bpy
    m = bpy.data.materials.new("FountainMist")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_MATERIAL':
            nt.nodes.remove(n)
    out = nt.nodes['Material Output']
    vol = nt.nodes.new("ShaderNodeVolumePrincipled")
    vol.inputs["Density"].default_value = 0.035
    vol.inputs["Color"].default_value = (0.95, 0.97, 1.0, 1)
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    nt.links.new(out.inputs["Surface"], tr.outputs["BSDF"])
    nt.links.new(out.inputs["Volume"], vol.outputs["Volume"])
    return m


# golden-hour look for the film: low warm sun from the front-left (it rakes the facade, glitters on the pond and
# back-lights the fountain when the camera looks toward the street)
FILM_SKY = dict(sun_dir=(-0.52, -0.83, 0.20), sun_energy=3.2, sun_color=(1.0, 0.68, 0.42), strength=0.35, clouds=0.35,
                hdri_strength=0.55, hdri_rot=86.8)


def setup_film_light(scene):
    """Golden hour: the CC0 Poly Haven sunset sky (assets/sources.json) rotated so its low sun sits behind the sun
    lamp; the procedural sky is the fallback when the HDRI has not been fetched."""
    import math
    from pathlib import Path
    from archviz import sky as _sky
    f = FILM_SKY
    _sky.setup_day(scene, sun_dir=f['sun_dir'], sun_energy=f['sun_energy'], strength=f['strength'], sun_color=f['sun_color'],
                   deepen=1.0, clouds=f['clouds'], sun_angle=0.8)
    hdr = Path(__file__).resolve().parent / 'assets' / 'kloppenheim_06_puresky_4k.hdr'
    if not hdr.is_file():
        print('[stanford] HDRI missing: python tools/fetch_assets.py houses/stanford/assets/sources.json (procedural sky used)')
        return
    import bpy
    nt = scene.world.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputWorld')
    bg = nt.nodes.new('ShaderNodeBackground')
    bg.inputs['Strength'].default_value = f['hdri_strength']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Rotation'].default_value[2] = math.radians(f['hdri_rot'])
    env = nt.nodes.new('ShaderNodeTexEnvironment')
    env.image = bpy.data.images.load(str(hdr), check_existing=True)
    nt.links.new(tc.outputs['Generated'], mp.inputs['Vector'])
    nt.links.new(mp.outputs[0], env.inputs['Vector'])
    nt.links.new(env.outputs['Color'], bg.inputs['Color'])
    nt.links.new(bg.outputs[0], out.inputs['Surface'])


def setup_scene(scene):
    """Daylight (the listing photos): a clear late-summer sky with the sun at the front-right."""
    from archviz import sky as _sky
    _sky.setup_day(scene, sun_dir=SKY['sun_dir'], sun_energy=SKY['day_sun'], strength=SKY['day_strength'], deepen=1.0, clouds=0.25,
                   shade_warm=1.0)


def before_render(scene, name):
    """run.py calls this before each photo still: every geometry module may define before_render(scene, cam_name) to
    set that photo's state (door positions, visibility, the sun of that photo) and must restore its defaults for any
    other camera."""
    import importlib
    import bpy
    # every light starts each photo at its build-time energy (stored on the first call as ob['_e0']): a module's
    # per-photo change (the exterior dimming the interior lamps, a room's fill gain) can then never leak into the next photo
    for ob in bpy.data.objects:
        if ob.type == 'LIGHT':
            if '_e0' not in ob:
                ob['_e0'] = ob.data.energy
            ob.data.energy = ob['_e0']
    for mod in MODULES:
        m = importlib.import_module(f"{__package__}.{mod}")
        if hasattr(m, "before_render"):
            m.before_render(scene, name)


# ---------------------------------------------------------------- sky: sun from the front-right (shadows in photos 01/30/31)
import os as _os                                                                    # noqa: E402
SKY = dict(sun_dir=(0.55, -0.62, 0.56), sun_energy=3.2, sun_color=(1.0, 0.94, 0.86), strength=0.8, sun_elevation=34.0,
           day_sun=float(_os.environ.get('STAN_SUN', 4.5)), day_strength=float(_os.environ.get('STAN_SKY', 0.2)))

# ---------------------------------------------------------------- cameras: name -> (location, target, lens mm)
# photo-matched views (solved with tools/solve_camera.py where noted; shifts in CAM_SHIFT)
CAMS = {
    # joint solve of 01 + 02 + 03 + 25 + 30 + 31 against the final plan (XB1 12.50, Y_BAY 0.86, YB0_UP 1.22, recess 1.60) + 01's drive lines:
    # python tools/joint_solve_lines.py houses/stanford/cams/ext_facade_solve.py  (p27 / p28: cams/ext_p27_solve.py, ext_p28_solve.py)
    'front':  ((-0.57, -14.516, 0.747), (2.617, -5.038, 0.747), 28.11),     # photo 02 (3.1 px rms)
    'hero':   ((5.291, -14.789, 1.018), (5.278, -4.789, 1.018), 24.75),      # photo 01 (2.1 px rms)
    'p03':    ((7.17, -5.497, 0.998), (7.432, 4.5, 0.998), 25.47),       # photo 03 porch (1.6 px rms, roll 0.21)
    'rear':   ((7.387, 30.904, 0.838), (7.411, 20.904, 0.838), 27.87),       # photo 25 (0.9 px rms)
    'p27':    ((-0.583, 29.516, 20.89), (1.36, 21.858, 14.761), 57.677),   # photo 27 drone, keystone-edited: pinhole + aspect + shear (~3 px wall, 6 px incl. ground);
              # lens / shift scaled by W / (W + 2 * overscan) = 1536 / 1656 (solved 62.18 mm, shift (-0.2182, -0.403))
    'p28':    ((-0.572, 19.103, 1.093), (7.489, 13.185, 1.093), 29.7),       # photo 28: rear wall (2.1 px); lens from SITE_NEAR's ground BA
    'p30':    ((-2.477, -18.23, 12.963), (0.949, -9.652, 9.133), 24.82),   # photo 30 drone (joint solve, 3.9 px rms)
}
CAM_SHIFT = {'front': (-0.0048, 0.161), 'hero': (0.0264, 0.0712), 'rear': (0.0469, 0.0503), 'p03': (0.0293, -0.0173),
             'p28': (0.0573, 0.0052), 'p27': (-0.2023, -0.3738)}
CAM_ASPECT = {'p27': 0.8881}     # {name: a}: render at (W, H / a), then stretch to (W, H) (keystone + aspect edits)
CAM_SHEAR = {'p27': 0.0852}      # then shear: out(x, y) = render(x - k (y - H/2), y) (run.py)
CAM_OVERSCAN = {'p27': 60}       # px per side rendered beyond the frame so the shear leaves no empty wedges
CAM_ROLL = {'p27': -10.86, 'p03': 0.21}
CAM_RES = {'front': (1536, 970), 'hero': (1536, 1024), 'p03': (1536, 1024), 'rear': (1536, 1024),
           'p27': (1536, 1152), 'p28': (1536, 1024), 'p30': (1536, 1152)}
from .cams_site import CAMS_SITE, CAM_SHIFT_SITE, CAM_RES_SITE, CAM_ROLL_SITE                # noqa: E402
CAMS.update(CAMS_SITE); CAM_SHIFT.update(CAM_SHIFT_SITE); CAM_RES.update(CAM_RES_SITE); CAM_ROLL.update(CAM_ROLL_SITE)
from . import cams_site as _cs                                                               # noqa: E402
CAM_CLIP = dict(getattr(_cs, 'CAM_CLIP_SITE', {}))                  # far clip (m) per camera, default 800 (run.py)
EXT = list(CAMS)
EXPOSURE = {'p28': 0.45, 'front': 0.0}   # exterior: 28 is exposed ~0.45 EV brighter than 25 (same shaded wall); 02 see exterior.LIGHT
EXPOSURE_DEFAULT = {'ext': 0.0, 'int': 0.0}
DOF = {}
DOF_DEFAULT = {'ext': 16.0, 'int': 8.0}
PHOTO_PAIRS = [('hero', 1), ('front', 2), ('p03', 3), ('rear', 25), ('p26', 26), ('p27', 27), ('p28', 28), ('p29', 29),
               ('p30', 30), ('aerial', 31), ('p32', 32)]

from .cams_main import CAMS_MAIN, CAM_SHIFT_MAIN, CAM_RES_MAIN, PAIRS_MAIN          # noqa: E402
from .cams_upper import CAMS_UPPER, CAM_SHIFT_UPPER, CAM_RES_UPPER, PAIRS_UPPER    # noqa: E402
from . import cams_main as _cm, cams_upper as _cu                                   # noqa: E402
CAMS.update(CAMS_MAIN); CAMS.update(CAMS_UPPER)
CAM_SHIFT.update(CAM_SHIFT_MAIN); CAM_SHIFT.update(CAM_SHIFT_UPPER)
CAM_RES.update(CAM_RES_MAIN); CAM_RES.update(CAM_RES_UPPER)
for _mod in (_cm, _cu, _cs):              # optional per-camera roll / exposure (stops) / aspect of the interior and site views
    CAM_ROLL.update(getattr(_mod, 'CAM_ROLL', {}))
    EXPOSURE.update(getattr(_mod, 'EXPOSURE', {}))
    CAM_ASPECT.update(getattr(_mod, 'CAM_ASPECT', {}))
PHOTO_PAIRS = PHOTO_PAIRS + PAIRS_MAIN + PAIRS_UPPER

GRASS = [
    dict(name="Grass_Front", rect=(-3.5, 17.5, -5.85, -0.05), z=Z_GRADE + 0.01, cell=0.5, padding=0.05,
         holes=[(0.3, 5.8, -6.0, 0.0), (5.6, 8.6, -1.7, 0.0), (8.4, 12.7, -1.3, 0.5), (-1.4, 0.4, -0.8, 0.0), (10.4, 12.0, -3.0, -1.4)],
         mat='grass', count=90000, length=0.06, children=10, seed=3),
    dict(name="Grass_Rear", rect=(-3.2, 13.8, 11.9, 28.0), z=Z_GRADE - 0.05, cell=0.5, padding=0.05,
         holes=[(1.4, 13.0, 11.8, 16.3)], mat='grass', count=110000, length=0.07, children=10, seed=5),
]
DOORS = dict(static=[], entry=("Entry_Door", (7.31, 1.5875), 96))       # inswing, hinged on the left (photo 03)
PROBE_WALLS = []
