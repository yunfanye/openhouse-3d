"""Prepare, preview, inspect and proof the Stanford cinematic take headlessly (run inside Blender).

  blender -b houses/stanford/output/stanford.blend --python-exit-code 1 --python houses/stanford/film_scene.py -- prepare
  blender -b houses/stanford/output/stanford_cinematic.blend --python-exit-code 1 --python houses/stanford/film_scene.py -- preview 4
  blender -b houses/stanford/output/stanford_cinematic.blend --python-exit-code 1 --python houses/stanford/film_scene.py -- storyboard 1,200,400
  blender -b houses/stanford/output/stanford_cinematic.blend --python-exit-code 1 --python houses/stanford/film_scene.py -- audit

prepare: golden-hour sun + sky, the baked camera take, the entry door and the sliding patio door animated, the
fountain and pond ripples animated, film render settings; packs and saves STAN_FILM_BLEND (default
output/stanford_cinematic.blend).  Never run prepare on an accepted production scene just to inspect it.

STAN_TAKE=matched selects matched_take.TAKE instead: the other reconstruction's 80-second route and door / slider
schedule in the listing-photo daylight of the saved scene (no golden-hour sky, fire or practical boost), with that
film's .30-frame shutter.  `storyboard --rebake` / `preview --rebake` re-bake the selected take on a scratch scene.
"""
import math
import os
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from archviz import film, filmkit                      # noqa: E402
from houses.stanford import house as H                # noqa: E402

OUT = ROOT / 'houses/stanford/output'
FOLDER = Path(os.environ.get('STAN_FILM_DIR', str(OUT / 'film')))
FOLDER.mkdir(parents=True, exist_ok=True)
BLEND = Path(os.environ.get('STAN_FILM_BLEND', str(OUT / 'stanford_cinematic.blend')))
filmkit.configure(str(FOLDER))
S = bpy.context.scene
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
mode = argv[0] if argv else 'prepare'
FPS = filmkit.FPS
MATCHED = os.environ.get('STAN_TAKE', 'cinematic') == 'matched'


def _take():
    import importlib
    mod = importlib.import_module('houses.stanford.matched_take' if MATCHED else 'houses.stanford.shots')
    importlib.reload(mod)
    return mod.TAKE


def _fcurves(idb):
    act = idb.animation_data.action if idb.animation_data else None
    fcs = getattr(act, "fcurves", None)
    if fcs is None and act is not None:
        try:
            fcs = act.layers[0].strips[0].channelbag(act.slots[0]).fcurves
        except Exception:
            fcs = []
    return fcs or []


def _ease(idb):
    for fc in _fcurves(idb):
        for kp in fc.keyframe_points:
            kp.interpolation = 'BEZIER'
            kp.easing = 'EASE_IN_OUT'


def slider(take):
    """Split the operable panel of the patio slider into its own object and slide it open.  fen.slider(fixed_side=+1):
    the operable panel is the inner-track one on the -X half (x a0+frame .. mid+0.02, y YB1-0.135 .. YB1-0.095); it
    slides +X behind the fixed panel."""
    src = bpy.data.objects.get('Win_slider')
    if src is None or bpy.data.objects.get('Slider_Panel'):
        return
    o = next(o for o in H.OPENINGS if o['name'] == 'slider')
    a0, a1, y1 = o['a0'], o['a1'], H.YB1
    am = (a0 + a1) / 2
    part = film._split_faces(src, (a0 + 0.01, am + 0.035, y1 - 0.14, y1 - 0.09, o['z0'] - 0.05, o['z1'] + 0.05), 'Slider_Panel')
    if part is None:
        raise RuntimeError('[film] slider panel not found')
    travel = (am + 0.02) - (a0 + 0.045) - 0.03
    sched = take.get('slider') or ((take['slider_t'], 0.0), (take['slider_t'] + take['slider_secs'], 1.0))
    for when, frac in sched:                              # (seconds, open fraction)
        part.location = (frac * travel, 0, 0)
        part.keyframe_insert('location', frame=round(when * FPS) + 1)
    _ease(part)


def staging(powder_shut=True):
    """Film-only staging so the one-take walk-through has a clear corridor (the photo stills keep the photographed
    arrangement): the dining table's two end chairs are pulled away (the route passes both ends of the table), the
    corn plant beside the slider stands 0.3 m further from the opening, and the powder-room door is shut."""
    for name in ('Dining_ChairNorth', 'Dining_SeatNorth', 'Dining_ChairSouth', 'Dining_SeatSouth'):
        ob = bpy.data.objects.get(name)
        if ob is not None:
            ob.hide_render = True
            ob.hide_viewport = True
    leaf = bpy.data.objects.get('Door_Powder_Leaf')          # closed, as in photos 05 / 06 (its build rest is open)
    if leaf is not None and powder_shut:
        leaf.rotation_euler.z = 0.0
    for ob in bpy.data.objects:
        if ob.name.startswith('Plant_CornSlider') and not ob.get('film_moved'):
            ob.location.x -= 0.30
            ob['film_moved'] = True


def fountain():
    """Animated aerating fountain: the spray streaks breathe (scale) and churn (a noise displace whose texture
    coordinates rise with time); a slow spin breaks up the pattern."""
    sp = bpy.data.objects.get('Fountain_Spray')
    if sp is None or sp.modifiers.get('Churn'):
        return
    tex = bpy.data.textures.new('Stan_FountainNoise', type='CLOUDS')
    tex.noise_scale = 0.35
    tex.noise_depth = 2
    em = bpy.data.objects.new('Fountain_Flow', None)
    bpy.context.scene.collection.objects.link(em)
    em.driver_add('location', 2).driver.expression = 'frame * 0.09'
    mod = sp.modifiers.new('Churn', 'DISPLACE')
    mod.texture = tex
    mod.texture_coords = 'OBJECT'
    mod.texture_coords_object = em
    mod.strength = 0.22
    mod.mid_level = 0.5
    # breathe about the nozzle
    fx, fy = sp.data.vertices[0].co.x, sp.data.vertices[0].co.y
    for v in sp.data.vertices:
        v.co.x -= fx
        v.co.y -= fy
    sp.location = (fx, fy, 0)
    sp.driver_add('scale', 2).driver.expression = '1 + 0.035*sin(frame*0.43) + 0.02*sin(frame*1.13)'
    sp.driver_add('rotation_euler', 2).driver.expression = 'frame * 0.004'
    # droplets travel: the spray's breakup mask slides along the arcs, the foam churns
    for name, axis, rate in (('FountainSpray', 2, -0.35), ('FountainFoam', 0, 0.02)):
        m = bpy.data.materials.get(name)
        for n in (m.node_tree.nodes if m else []):
            if n.type == 'MAPPING' and not n.inputs['Location'].is_linked:
                n.inputs['Location'].driver_add('default_value', axis).driver.expression = f'frame * {rate}'


def water():
    """Slow drifting ripples on the pond (the bump noise's mapping location follows the frame)."""
    m = bpy.data.materials.get('PondWater')
    if m is None:
        return
    for n in m.node_tree.nodes:
        if n.type == 'MAPPING' and not n.inputs['Location'].is_linked:
            d = n.inputs['Location'].driver_add('default_value', 1)
            d.driver.expression = 'frame * 0.0035'


def wind():
    """A gentle breeze through the near trees and shrubs: a low-frequency displace whose field drifts with time."""
    tex = bpy.data.textures.get('Stan_Wind') or bpy.data.textures.new('Stan_Wind', type='CLOUDS')
    tex.noise_scale = 1.6
    em = bpy.data.objects.get('Wind_Field')
    if em is None:
        em = bpy.data.objects.new('Wind_Field', None)
        bpy.context.scene.collection.objects.link(em)
        em.driver_add('location', 0).driver.expression = 'frame * 0.012'
        em.driver_add('location', 1).driver.expression = 'frame * 0.006'
    for ob in bpy.data.objects:
        if ob.type != 'MESH' or not ob.name.startswith('Land_') or not ob.name.endswith('_Leaves'):
            continue
        if ob.modifiers.get('Wind'):
            continue
        mod = ob.modifiers.new('Wind', 'DISPLACE')
        mod.texture = tex
        mod.texture_coords = 'OBJECT'
        mod.texture_coords_object = em
        mod.strength = 0.05
        mod.mid_level = 0.5


def hearth_fire():
    """A lit gas fire behind the fireplace glass: flame cards just proud of the dark glass, a warm flickering light."""
    if bpy.data.objects.get('Film_Fire'):
        return
    box = bpy.data.objects.get('Fireplace_Firebox')
    if box is None:
        return
    from archviz import materials as _m
    from archviz.mesh import MB
    from archviz.lights import add_light
    import random
    ws = [box.matrix_world @ v.co for v in box.data.vertices]
    xf = max(v.x for v in ws)                              # the glass face
    ym = (min(v.y for v in ws) + max(v.y for v in ws)) / 2
    rng = random.Random(7)
    mb = MB()
    for k in range(9):
        yy = ym + rng.uniform(-0.28, 0.28)
        w = rng.uniform(0.07, 0.13); h = rng.uniform(0.16, 0.30)
        x = xf + 0.004 + 0.001 * k
        mb.quad((x, yy - w / 2, 0.24), (x, yy + w / 2, 0.24), (x, yy + w * 0.2, 0.24 + h), (x, yy - w * 0.2, 0.24 + h))
    fire = mb.build('Film_Fire', [_m.fire('FilmFire')], coll='Lights_Main')
    fire.visible_shadow = False
    tex = bpy.data.textures.new('Film_FireNoise', type='CLOUDS'); tex.noise_scale = 0.06
    mod = fire.modifiers.new('Flicker', 'SUBSURF'); mod.levels = mod.render_levels = 3
    d = fire.modifiers.new('Lick', 'DISPLACE'); d.texture = tex; d.strength = 0.03; d.direction = 'Y'
    d.driver_add('strength').driver.expression = '0.03 + 0.012*sin(frame*0.9) + 0.008*sin(frame*2.3)'
    fire.driver_add('scale', 2).driver.expression = '1 + 0.08*sin(frame*1.1) + 0.05*sin(frame*2.7)'
    li = add_light('L_Film_Fire', 'POINT', (xf + 0.35, ym, 0.42), 45.0, color=(1.0, 0.55, 0.22), size=0.25, coll='Lights_Main')
    li.data.driver_add('energy').driver.expression = '45 + 6*sin(frame*0.9) + 4*sin(frame*2.3)'


def lights_for_film():
    """Warm interior practicals for the golden-hour take (the daylight comparison stills keep plan values)."""
    for ob in bpy.data.objects:
        if ob.type != 'LIGHT' or ob.name == 'Sun':
            continue
        cols = [c.name for c in ob.users_collection]
        if any(c in ('Lights_Main', 'Lights_Upper') for c in cols):
            ob.data.energy *= float(os.environ.get('STAN_INT_GAIN', 1.6))
        if ob.data.type in ('POINT', 'SPOT'):
            ob.data.shadow_soft_size = max(0.08, ob.data.shadow_soft_size)


def powder_door(take):
    """Swing the powder-room door from its open build rest to shut on the take's schedule ((seconds, 'open'|'closed'))."""
    leaf = bpy.data.objects.get('Door_Powder_Leaf')
    if leaf is None:
        raise RuntimeError('[film] Door_Powder_Leaf not found')
    rest = leaf.get('_rest', tuple(leaf.rotation_euler))[2]
    leaf.animation_data_clear()
    for when, state in take['powder']:
        leaf.rotation_euler.z = rest if state == 'open' else 0.0
        leaf.keyframe_insert('rotation_euler', index=2, frame=round(when * FPS) + 1)
    _ease(leaf)


def prepare_matched():
    """The matched take in the saved scene's listing-photo daylight (the stills' world and interior lights)."""
    take = _take()
    film.bake_take(S, take)
    if not bpy.data.objects['Entry_Door'].get('film_hinge'):
        film.open_doors(S, H.DOORS, frame_open=round(take['door_t'] * FPS) + 1, seconds=take['door_secs'])
    slider(take)
    staging(powder_shut=False)
    powder_door(take)
    for name in take.get('shut', ()):                     # leaves that would swing across the route (origin at the hinge)
        bpy.data.objects[name].rotation_euler.z = 0.0
    fountain()
    water()
    wind()
    S.camera.data.clip_end = 6000.0                          # the aerials and the pond view see the far context
    S.render.resolution_x, S.render.resolution_y, S.render.resolution_percentage = 1920, 1080, 100
    S.render.fps, S.render.fps_base = FPS, 1
    S.render.use_motion_blur = True
    S.render.motion_blur_shutter = 0.30
    cy = S.cycles
    cy.samples = int(os.environ.get('STAN_SPP', 40))             # the accepted v2 film's quality: 40 / 64 / 128 spp
    cy.adaptive_threshold = float(os.environ.get('STAN_THRESHOLD', 0.03))   # measured equal at 100% after OIDN
    cy.adaptive_min_samples = 16
    cy.use_animated_seed = True
    cy.seed = 13695
    cy.use_denoising = True
    cy.denoiser = 'OPENIMAGEDENOISE'
    cy.diffuse_bounces = 4
    cy.glossy_bounces = 4
    cy.sample_clamp_indirect = 8.0
    S.render.use_persistent_data = True
    S.render.image_settings.file_format = 'PNG'
    S.render.image_settings.color_mode = 'RGB'
    S.render.image_settings.color_depth = '8'
    for m in S.timeline_markers:
        S.timeline_markers.remove(m)
    for key in take['keys']:
        if key['label']:
            S.timeline_markers.new(key['label'][:60], frame=round(key['t'] * FPS) + 1)
    S['visualization'] = 'Photo-derived reconstruction with virtual staging; inferred dimensions, not a measured survey.'
    S['film_description'] = ('The route, timing and transitions of an independent reconstruction\'s houses/stanford/cinematic.py '
                             're-authored in this model; one continuous 80-second camera, 24 fps, no cuts.')
    S['archviz_house'], S['archviz_shot'] = 'stanford', take['name']
    S.frame_set(1)
    from archviz.rendering import pack_scene
    pack_scene()
    BLEND.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    print('[film] prepared matched take', BLEND, 'frames', S.frame_start, S.frame_end, flush=True)


def prepare():
    if MATCHED:
        return prepare_matched()
    H.setup_film_light(S)
    take = H.TAKE
    film.bake_take(S, take)
    if not bpy.data.objects['Entry_Door'].get('film_hinge'):
        film.open_doors(S, H.DOORS, frame_open=round(take['door_t'] * FPS) + 1, seconds=take['door_secs'])
    slider(take)
    staging()
    fountain()
    water()
    wind()
    hearth_fire()
    lights_for_film()
    S.render.resolution_x, S.render.resolution_y, S.render.resolution_percentage = 1920, 1080, 100
    S.render.fps, S.render.fps_base = FPS, 1
    S.render.use_motion_blur = True
    S.render.motion_blur_shutter = 0.45
    cy = S.cycles
    cy.samples = int(os.environ.get('STAN_SPP', 40))
    cy.adaptive_threshold = 0.03
    cy.adaptive_min_samples = 16
    cy.use_animated_seed = True
    cy.use_denoising = True
    cy.denoiser = 'OPENIMAGEDENOISE'
    cy.diffuse_bounces = 4
    cy.glossy_bounces = 4
    cy.sample_clamp_indirect = 8.0
    S.render.use_persistent_data = True
    S.render.image_settings.file_format = 'PNG'
    S.render.image_settings.color_mode = 'RGB'
    S.render.image_settings.color_depth = '8'
    S.view_settings.view_transform = 'AgX'
    S.view_settings.look = 'AgX - Medium High Contrast'
    for m in S.timeline_markers:
        S.timeline_markers.remove(m)
    for key in take['keys']:
        S.timeline_markers.new(key['label'][:60], frame=round(key['t'] * FPS) + 1)
    S['visualization'] = 'Photo-derived reconstruction with virtual staging; inferred dimensions, not a measured survey.'
    S['source_listing'] = 'https://www.zillow.com/homedetails/13695-Stanford-Dr-Carmel-IN-46074/99144200_zpid/'
    S['film_description'] = f"One continuous {take['keys'][-1]['t']:.0f}-second camera; 24 fps; no internal cuts."
    S['archviz_house'], S['archviz_shot'] = 'stanford', take['name']
    S.frame_set(1)
    from archviz.rendering import pack_scene
    pack_scene()
    BLEND.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    print('[film] prepared', BLEND, 'frames', S.frame_start, S.frame_end, flush=True)


def rebake():
    """Re-bake only the camera from the current take module (path iteration on a prepared scratch scene)."""
    take = _take()
    film.bake_take(S, take)
    film.clearance_take(S, take)


def preview(step, frames=None):
    """Fast path check: Workbench (studio light, material colours) every `step` frames at 640x360."""
    d = FOLDER / 'preview'
    d.mkdir(parents=True, exist_ok=True)
    for f in d.glob('p_*.png'):
        f.unlink()
    S.render.engine = 'BLENDER_WORKBENCH'
    S.display.shading.light = 'STUDIO'
    S.display.shading.color_type = 'MATERIAL'
    S.display.shading.show_shadows = True
    S.render.resolution_x, S.render.resolution_y, S.render.resolution_percentage = 640, 360, 100
    S.render.use_motion_blur = False
    S.render.use_compositing = False
    a, b = frames or (S.frame_start, S.frame_end)
    for fr in range(a, b + 1, step):
        S.frame_set(fr)
        S.render.filepath = str(d / f'p_{fr:04d}.png')
        bpy.ops.render.render(write_still=True)
    print('[film] preview ->', d, flush=True)


def storyboard(frames, pct=50, spp=32):
    d = FOLDER / 'storyboard'
    d.mkdir(parents=True, exist_ok=True)
    from archviz.rendering import configure_device
    configure_device(S, os.environ.get('ARCHVIZ_DEVICE', 'METAL'))
    S.render.resolution_percentage = pct
    S.cycles.samples = spp
    S.cycles.adaptive_min_samples = min(16, spp)
    for fr in frames:
        S.frame_set(fr)
        S.render.filepath = str(d / f's_{fr:04d}.png')
        bpy.ops.render.render(write_still=True)
        print('[film] storyboard', fr, flush=True)


def audit():
    from archviz.camera_audit import audit as inspect
    from archviz.media import write_json
    report = inspect(S)
    write_json(FOLDER / 'camera_audit.json', report)
    print('[film] audit: peak speed', report['peak_speed_mps'], 'peak pan', report['peak_pan_degps'],
          'lens obstructions', len(report['lens_obstructions']), 'path crossings', len(report['path_crossings']), flush=True)
    for o in report['lens_obstructions'][:40]:
        print('   lens', o, flush=True)


if mode == 'prepare':
    prepare()
elif mode == 'preview':
    if '--rebake' in argv:
        rebake()
    rng = next((tuple(int(v) for v in a.split('-')) for a in argv[2:] if '-' in a and not a.startswith('--')), None)
    preview(int(argv[1]) if len(argv) > 1 else 6, rng)
elif mode == 'storyboard':
    if '--rebake' in argv:
        argv.remove('--rebake')
        rebake()
    fr = [int(v) for v in argv[1].split(',')] if len(argv) > 1 else list(range(S.frame_start, S.frame_end + 1, 72))
    storyboard(fr, int(argv[2]) if len(argv) > 2 else 50, int(argv[3]) if len(argv) > 3 else 32)
elif mode == 'audit':
    audit()
else:
    raise ValueError(mode)
