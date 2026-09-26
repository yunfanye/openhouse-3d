"""Promo-film machinery: baked camera moves, per-shot / long-take rendering, motion-vector pass, VSE assembly,
clearance ray-casts, passability probes and door animation.  House-agnostic: the shots, take, titles, doors and
probe walls come from houses/<name>/shots.py + house.py.

Each SHOT is a short, eased camera move (dolly / push / crane / orbit) described by waypoints at fractions 0..1 of
the shot; position and look-at target are interpolated with a cardinal Hermite spline (ease = end-tangent scale).
A TAKE is one continuous move through timed keys (position, look direction as a unit vector, lens, f-stop, exposure).
Frames go to <film>/<set>/<shot>/f_####.png (resumable: existing frames are skipped) and are cut together in
Blender's sequencer with dissolves, title cards and a fade from/to black - no external ffmpeg needed.

  blender -b --python run.py -- --house walsh --film all                       # render every shot (Cycles)
  blender -b --python run.py -- --house walsh --film take --film-preview       # Workbench path check + clearance
  blender -b --python run.py -- --house walsh --film-encode --film take        # titles + dissolves -> mp4
"""
import os, math
import bpy
from mathutils import Vector
from .mesh import collection
from . import filmkit
from .filmkit import FPS, DISSOLVE, FADE_IN, FADE_OUT, W, H, frames_of, shot_dir


def _hermite(pts, ease=(0.0, 0.0)):
    """f(s in 0..1) -> Vector; cardinal Hermite through pts. `ease` scales the end tangents: 0 = come to rest
    (ease in / out), 1 = full one-sided velocity (the move is already going at the cut / keeps going through it)."""
    P = [Vector(p) for p in pts]
    n = len(P)
    if n == 1:
        return lambda s: P[0].copy()
    times = [i / (n - 1) for i in range(n)]
    m = []
    for i in range(n):
        if i == 0:
            m.append(ease[0] * (P[1] - P[0]) / (times[1] - times[0]))
        elif i == n - 1:
            m.append(ease[1] * (P[-1] - P[-2]) / (times[-1] - times[-2]))
        else:
            m.append((P[i + 1] - P[i - 1]) / (times[i + 1] - times[i - 1]))

    def f(s):
        s = max(0.0, min(1.0, s))
        for i in range(n - 1):
            if s <= times[i + 1]:
                h = times[i + 1] - times[i]
                t = (s - times[i]) / h
                h00 = 2 * t ** 3 - 3 * t ** 2 + 1
                h10 = t ** 3 - 2 * t ** 2 + t
                h01 = -2 * t ** 3 + 3 * t ** 2
                h11 = t ** 3 - t ** 2
                return h00 * P[i] + h10 * h * m[i] + h01 * P[i + 1] + h11 * h * m[i + 1]
        return P[-1].copy()
    return f


def _smooth(t):
    return t * t * (3 - 2 * t)


_DIRS = [Vector(v).normalized() for v in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1),
                                          (1, 1, 0), (1, -1, 0), (-1, 1, 0), (-1, -1, 0), (1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1))]


def clearance(scene, shot, radius=0.6):
    """Ray-cast around the baked camera path: report the closest geometry per shot (and anything hit in front of
    the lens within 0.5 m — the camera looking through a wall). Used by --film-preview."""
    dg = bpy.context.evaluated_depsgraph_get()
    ease = shot.get('ease', (0.0, 0.0))
    pos_f = _hermite([w[0] for w in shot['wp']], ease)
    tgt_f = _hermite([w[1] for w in shot['wp']], ease)
    n = frames_of(shot)
    worst = (9.9, 0, "")
    front = []

    def cast(o, d, dist):
        hit, p, nrm, idx, ob, mat = scene.ray_cast(dg, o, d, distance=dist)
        if hit and ob.type != 'LIGHT' and not ob.name.startswith(("Cam_", "L_")):
            return (p - o).length, ob.name
        return None

    for fr in range(1, n + 1, 2):
        s = (fr - 1) / max(1, n - 1)
        loc, tgt = pos_f(s), tgt_f(s)
        for d in _DIRS:
            h = cast(loc, d, radius)
            if h and h[0] < worst[0]:
                worst = (h[0], fr, h[1])
        h = cast(loc, (tgt - loc).normalized(), 0.5)
        if h:
            front.append((fr, h[0], h[1]))
    flag = "" if worst[0] > 0.45 else "  <-- TIGHT"
    print(f"[clear] {shot['name']:9s} closest {worst[0]:.2f} m at frame {worst[1]} ({worst[2]}){flag}"
          + (f"  LENS BLOCKED at frames {[f for f, _, _ in front][:6]} by {front[0][2]}" if front else ""))


def bake_shot(scene, shot):
    """Create/refresh Cam_Film with per-frame keys for one shot (frames 1..n); returns (camera, n)."""
    n = frames_of(shot)
    cam = bpy.data.objects.get("Cam_Film")
    if cam is None:
        cd = bpy.data.cameras.new("Cam_Film")
        cd.sensor_width = 36
        cd.clip_start = 0.05
        cd.clip_end = 800
        cam = bpy.data.objects.new("Cam_Film", cd)
        collection('Cameras').objects.link(cam)
        cam.rotation_mode = 'QUATERNION'
    cd = cam.data
    cam.animation_data_clear()
    cd.animation_data_clear()
    cd.dof.use_dof = True
    cd.dof.aperture_fstop = shot['fstop']
    cd.dof.aperture_blades = 7
    pos_f = _hermite([w[0] for w in shot['wp']], shot.get('ease', (0.0, 0.0)))
    tgt_f = _hermite([w[1] for w in shot['wp']], shot.get('ease', (0.0, 0.0)))
    l0, l1 = shot['lens']
    for fr in range(1, n + 1):
        s = (fr - 1) / max(1, n - 1)
        loc, tgt = pos_f(s), tgt_f(s)
        cam.location = loc
        cam.rotation_quaternion = (tgt - loc).to_track_quat('-Z', 'Y')
        cd.lens = l0 + (l1 - l0) * _smooth(s)
        cd.dof.focus_distance = (tgt - loc).length
        cam.keyframe_insert("location", frame=fr)
        cam.keyframe_insert("rotation_quaternion", frame=fr)
        cd.keyframe_insert("lens", frame=fr)
        cd.keyframe_insert("dof.focus_distance", frame=fr)
    for idb in (cam, cd):
        act = idb.animation_data.action if idb.animation_data else None
        fcs = getattr(act, "fcurves", None)
        if fcs is None and act is not None:                     # Blender 5 layered actions
            try:
                fcs = act.layers[0].strips[0].channelbag(act.slots[0]).fcurves
            except Exception:
                fcs = []
        for fc in fcs or []:
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'
    scene.camera = cam
    scene.frame_start, scene.frame_end = 1, n
    scene.render.fps = FPS
    return cam, n


def enable_vectors(scene, out_dir):
    """Write the Cycles Vector pass (per-pixel screen motion to the previous / next frame) as v_####.exr next to
    the colour frames, for tools/temporal.py.  Needs motion blur OFF (Cycles has no vector pass with blur)."""
    scene.view_layers[0].use_pass_vector = True
    scene.render.use_motion_blur = False
    nt = scene.compositing_node_group if hasattr(scene, "compositing_node_group") else scene.node_tree
    if nt is None:
        from . import polish
        nt = polish.setup_compositor(scene)
    rl = next(n for n in nt.nodes if n.type == 'R_LAYERS')
    fo = nt.nodes.get("VectorOut")
    if fo is None:                                            # Blender 5.2 File Output: directory + items
        fo = nt.nodes.new("CompositorNodeOutputFile")
        fo.name = "VectorOut"
        fo.file_name = ""
        fo.format.media_type = 'IMAGE'
        fo.format.file_format = 'OPEN_EXR'
        fo.format.color_depth = '32'
        fo.format.color_mode = 'RGBA'
        fo.file_output_items.new('RGBA', "v_")
        nt.links.new(fo.inputs[0], rl.outputs["Vector"])
    fo.directory = out_dir + os.sep


def render_shot(scene, shot, frames=None, step=1, exposure=True, vectors=False, doors=None):
    """Render a shot's frames (skipping ones already on disk).  vectors=True renders the motion-vector pass instead
    of the picture: 1 sample, no DoF / blur / denoise, pinhole-exact v_####.exr for tools/temporal.py.
    doors: house.py DOORS spec (see open_doors); applied for takes that carry door_t / door_secs."""
    import time, shutil
    if 'keys' in shot:
        cam, n = bake_take(scene, shot)
        if doors and 'door_t' in shot:
            open_doors(scene, doors, frame_open=int(round(shot['door_t'] * FPS)) + 1, seconds=shot.get('door_secs', 1.6))
    else:
        cam, n = bake_shot(scene, shot)
    d = shot_dir(shot)
    os.makedirs(d, exist_ok=True)
    scratch = None
    if vectors:
        enable_vectors(scene, d)
        cam.data.dof.use_dof = False
        scene.cycles.samples = 1
        scene.cycles.use_adaptive_sampling = False
        scene.cycles.use_denoising = False
        scene.cycles.max_bounces = 0
        scene.cycles.pixel_filter_type = 'BOX'
        scene.cycles.filter_width = 0.01
        scratch = os.path.join(d, "_vecpng")
        os.makedirs(scratch, exist_ok=True)
    if frames:
        a, b = frames
        scene.frame_start, scene.frame_end = max(1, a), min(n, b)
    scene.frame_step = step
    if exposure and 'keys' not in shot:
        scene.view_settings.exposure = shot['exp']
    scene.render.filepath = os.path.join(scratch or d, "f_")
    scene.render.use_overwrite = False
    scene.render.use_placeholder = False
    scene.render.use_file_extension = True
    done = (lambda f: os.path.exists(os.path.join(d, f"v_{f:04d}.exr"))) if vectors else \
           (lambda f: os.path.exists(os.path.join(d, f"f_{f:04d}.png")))
    todo = [f for f in range(scene.frame_start, scene.frame_end + 1, step) if not done(f)]
    what = "vectors" if vectors else "frames"
    print(f"[film] {shot['name']}: {what} {scene.frame_start}-{scene.frame_end} step {step} ({len(todo)} to render)")
    if not todo:
        return
    if vectors:                      # use_overwrite skips by the PNG name, so render exactly the missing frames
        for f in todo:
            scene.frame_start = scene.frame_end = f
            bpy.ops.render.render(animation=True)
        shutil.rmtree(scratch, ignore_errors=True)
        return
    t1 = time.time()
    bpy.ops.render.render(animation=True)
    print(f"[film] {shot['name']} done in {time.time() - t1:.0f}s ({(time.time() - t1) / max(1, len(todo)):.1f} s/frame)")


# ------------------------------------------------------------------ assembly (VSE -> H.264)
def _strips(ed):
    return ed.strips if hasattr(ed, "strips") else ed.sequences


def _key_alpha(strip, keys):
    for fr, a in keys:
        strip.blend_alpha = a
        strip.keyframe_insert("blend_alpha", frame=fr)


def _frame_step(files):
    """Frame step a shot folder was rendered with (f_0001, f_0003 ... -> 2)."""
    nums = [int(f[2:6]) for f in files[:2]]
    return max(1, nums[1] - nums[0]) if len(nums) == 2 else 1


def _image_strip(ed, name, folder, files, channel, frame_start, hold=1):
    """Image strip of the files; each held `hold` frames (draft sets rendered with --film-step)."""
    st = _strips(ed).new_image(name=name, filepath=os.path.join(folder, files[0]), channel=channel, frame_start=frame_start)
    seq = [f for f in files for _ in range(hold)][1:]
    for f in seq:
        st.elements.append(f)
    return st


def assemble(mp4_path, shots, titles_dir, crf='PERC_LOSSLESS', stills=(), music=None, tf=True):
    """Cut the rendered shots together: dissolves, titles, fades; encode H.264 1080p24.
    titles_dir: PNG overlays from filmkit.make_titles (run.py regenerates them via tools/film_tools.py first).
    stills: sequence frame numbers to write as PNGs next to the mp4 instead of encoding (layout checks).
    music: optional audio file laid under the cut (AAC, 2 s fade-out at the end)."""
    sc = bpy.data.scenes.new("Film")
    sc.render.resolution_x, sc.render.resolution_y = W, H
    sc.render.resolution_percentage = 100
    sc.render.fps = FPS
    sc.view_settings.view_transform = 'Standard'
    sc.render.image_settings.media_type = 'VIDEO'
    sc.render.image_settings.file_format = 'FFMPEG'
    sc.render.ffmpeg.format = 'MPEG4'
    sc.render.ffmpeg.codec = 'H264'
    sc.render.ffmpeg.constant_rate_factor = crf
    sc.render.ffmpeg.ffmpeg_preset = 'GOOD'
    sc.render.ffmpeg.gopsize = 12
    sc.render.filepath = mp4_path
    ed = sc.sequence_editor_create()
    tdir = titles_dir

    # picture: shot i on channel i+1, alpha-over dissolve into the previous one
    cursor = 1
    ch = 1
    for i, s in enumerate(shots):
        d = shot_dir(s)
        if tf and os.path.isdir(d + "_tf"):                       # temporally filtered set (tools/temporal.py)
            d = d + "_tf"
        files = sorted(f for f in os.listdir(d) if f.startswith("f_") and f.endswith(".png"))
        if not files:
            raise RuntimeError(f"no frames for shot {s['name']} in {d}")
        hold = _frame_step(files)
        n = min(len(files) * hold, frames_of(s))
        start = cursor if i == 0 else cursor - DISSOLVE
        st = _image_strip(ed, s['name'], d, files, ch, start, hold)
        st.frame_final_duration = n
        fw = filmkit.FRAME_W.get(filmkit.FRAMES, W)
        if fw != W:                                              # draft / preview frames: fit the 1080p canvas
            st.transform.scale_x = st.transform.scale_y = W / fw
        st.blend_type = 'ALPHA_OVER'
        if i > 0:
            _key_alpha(st, [(start, 0.0), (start + DISSOLVE, 1.0)])
        else:
            st.blend_alpha = 1.0
        s['_start'], s['_end'] = start, start + n - 1
        cursor = start + n
        ch += 1
    last = cursor - 1
    sc.frame_start, sc.frame_end = 1, last

    # captions + titles
    ch_t = ch + 1
    ovl = _strips(ed)

    def overlay(png, a, b, fade=20, channel=ch_t):
        st = ovl.new_image(name=os.path.basename(png), filepath=png, channel=channel, frame_start=a)
        st.frame_final_duration = b - a + 1
        st.blend_type = 'ALPHA_OVER'
        _key_alpha(st, [(a, 0.0), (a + fade, 1.0), (b - fade, 1.0), (b, 0.0)])
        return st

    s0 = shots[0]
    disclosure = os.path.join(tdir, 'disclosure.png')
    if os.path.isfile(disclosure):
        overlay(disclosure, 1, last, fade=24, channel=ch_t + 1)
    if len(shots) == 1:                                            # the long take: title over the descent, end card over the orbit out
        overlay(os.path.join(tdir, "title_main.png"), s0['_start'] + 30, s0['_start'] + 150, fade=28)
        overlay(os.path.join(tdir, "title_end.png"), last - 150, last - 4, fade=26)
    else:
        overlay(os.path.join(tdir, "title_main.png"), s0['_start'] + 18, s0['_end'] - DISSOLVE - 4, fade=28)   # gone before the dissolve
        for s in shots[1:-1]:
            if s['caption']:
                overlay(os.path.join(tdir, f"cap_{s['name']}.png"), s['_start'] + DISSOLVE + 4, s['_end'] - DISSOLVE - 2, fade=14)
        sl = shots[-1]
        overlay(os.path.join(tdir, "title_end.png"), sl['_start'] + 40, last - 4, fade=26)

    # fade from / to black
    try:
        blk = ovl.new_effect(name="Black", type='COLOR', channel=ch_t + 2, frame_start=1, length=last)
    except TypeError:                                                  # < 5.0 signature
        blk = ovl.new_effect(name="Black", type='COLOR', channel=ch_t + 2, frame_start=1, frame_end=last + 1)
    blk.color = (0, 0, 0)
    blk.blend_type = 'ALPHA_OVER'
    _key_alpha(blk, [(1, 1.0), (1 + FADE_IN, 0.0), (last - FADE_OUT, 0.0), (last, 1.0)])

    if music:
        snd = ovl.new_sound(name="Music", filepath=music, channel=ch_t + 4, frame_start=1)
        snd.frame_final_duration = min(snd.frame_final_duration, last)
        snd.volume = 1.0
        snd.keyframe_insert("volume", frame=last - 2 * FPS)
        snd.volume = 0.0
        snd.keyframe_insert("volume", frame=last)
        sc.render.ffmpeg.audio_codec = 'AAC'
        sc.render.ffmpeg.audio_bitrate = 192

    if bpy.context.window:
        bpy.context.window.scene = sc
    if stills:
        sc.render.image_settings.media_type = 'IMAGE'
        sc.render.image_settings.file_format = 'PNG'
        for fr in stills:
            sc.frame_set(fr)
            sc.render.filepath = os.path.splitext(mp4_path)[0] + f"_f{fr:04d}.png"
            bpy.ops.render.render(write_still=True, scene=sc.name)
            print(f"[film] still {fr} -> {sc.render.filepath}")
        return mp4_path, last
    print(f"[film] encoding {last} frames ({last / FPS:.1f} s) -> {mp4_path}")
    bpy.ops.render.render(animation=True, scene=sc.name)
    return mp4_path, last




# ------------------------------------------------------------------ passability probes (planning a long take)
# house.py PROBE_WALLS: (name, axis of the wall plane ('X' = plane x=b, along y; 'Y' = plane y=b, along x), b, (a0, a1), (z0, z1))
def probe_stair(scene, centre, radius=1.75, z_from=(5.8, 2.5)):
    """Tread height around a spiral stair (ray-cast down at `radius` from the centre every 15 deg, from each z in z_from)."""
    dg = bpy.context.evaluated_depsgraph_get()
    for z0 in z_from:
        for deg in range(0, 360, 15):
            a = math.radians(deg)
            o = Vector((centre[0] + radius * math.cos(a), centre[1] + radius * math.sin(a), z0))
            hit, p, nrm, idx, ob, mat = scene.ray_cast(dg, o, Vector((0, 0, -1)), distance=7.0)
            print(f"[stair] from z={z0} {deg:3d} deg: {'z=%.2f %s' % (p.z, ob.name) if hit else 'nothing'}")


def probe_openings(scene, walls, step=0.25):
    """ASCII map of every probe wall: '#' = geometry within 0.6 m either side of the plane, '.' = clear."""
    dg = bpy.context.evaluated_depsgraph_get()
    for name, axis, b, (a0, a1), (z0, z1) in walls:
        na = int((a1 - a0) / step) + 1
        nz = int((z1 - z0) / step) + 1
        print(f"[probe] {name}   along {a0}..{a1} (cols, {step} m), z {z0}..{z1} (rows, top first)")
        for iz in range(nz - 1, -1, -1):
            z = z0 + iz * step
            row = ""
            for ia in range(na):
                a = a0 + ia * step
                p = Vector((b, a, z)) if axis == 'X' else Vector((a, b, z))
                d = Vector((1, 0, 0)) if axis == 'X' else Vector((0, 1, 0))
                o = p - d * 0.6
                hit, loc, nrm, idx, ob, mat = scene.ray_cast(dg, o, d, distance=1.2)
                row += "#" if hit and ob.type != 'LIGHT' else "."
            print(f"  z={z:5.2f} {row}")


# ------------------------------------------------------------------ long take: doors + the timed camera path
def _split_faces(ob, bbox, name):
    """Move the faces of `ob` whose vertices all lie inside bbox (x0,x1,y0,y1,z0,z1) into a new object."""
    import bmesh
    x0, x1, y0, y1, z0, z1 = bbox
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    inside = lambda v: x0 <= v.co.x <= x1 and y0 <= v.co.y <= y1 and z0 <= v.co.z <= z1
    faces = [f for f in bm.faces if all(inside(v) for v in f.verts)]
    if not faces:
        bm.free()
        return None
    nb = bmesh.new()
    vmap = {}
    for f in faces:
        vs = []
        for v in f.verts:
            if v not in vmap:
                vmap[v] = nb.verts.new(v.co)
            vs.append(vmap[v])
        nf = nb.faces.new(vs)
        nf.material_index = f.material_index
        nf.smooth = f.smooth
    me = bpy.data.meshes.new(name)
    for m in ob.data.materials:                 # slots first: clearing / appending slots later resets the indices
        me.materials.append(m)
    nb.to_mesh(me); nb.free()
    bmesh.ops.delete(bm, geom=faces, context='FACES')
    bm.to_mesh(ob.data); bm.free()
    new = bpy.data.objects.new(name, me)
    new.matrix_world = ob.matrix_world.copy()
    for c in ob.users_collection:
        c.objects.link(new)
    return new


def _hinge(ob, pivot):
    """Put the object's origin at the hinge line (pivot x, y) so rotation_euler.z swings the leaf."""
    if tuple(ob.get('film_hinge', ())) == tuple(pivot):
        return
    px, py = pivot
    for v in ob.data.vertices:
        v.co.x -= px; v.co.y -= py
    ob.location = (px, py, 0.0)
    ob['film_hinge'] = tuple(pivot)


def open_doors(scene, doors, frame_open=None, seconds=1.6):
    """Swing doors open for the film.  `doors` (house.py DOORS):

        dict(static=[(name, (source objects...), bbox (x0, x1, y0, y1, z0, z1), hinge (x, y), angle_deg), ...],
             entry=(object_name, hinge (x, y), angle_deg))

    static leaves are cut out of merged meshes (all faces inside bbox) and left open; the entry door is a whole object
    that, if frame_open is given, swings open over `seconds` starting at that frame.  Idempotent."""
    if scene.get("doors_open"):
        return
    scene["doors_open"] = True
    debug = os.environ.get("FILM_DEBUG_DOORS")
    for name, sources, bbox, pivot, ang in doors.get("static", ()):
        for src in sources:
            ob = bpy.data.objects.get(src)
            if ob is None:
                continue
            part = _split_faces(ob, bbox, f"{name}_{src}")
            if part:
                _hinge(part, pivot)
                part.rotation_euler = (0, 0, math.radians(ang))
                if debug:
                    bpy.context.view_layer.update()
                    ws = [part.matrix_world @ v.co for v in part.data.vertices]
                    print(f"[doors] {part.name}: {len(ws)} verts, world bbox x {min(v.x for v in ws):.2f}..{max(v.x for v in ws):.2f} "
                          f"y {min(v.y for v in ws):.2f}..{max(v.y for v in ws):.2f} z {min(v.z for v in ws):.2f}..{max(v.z for v in ws):.2f}")
    entry = doors.get("entry")
    door = bpy.data.objects.get(entry[0]) if entry else None
    if door is not None and frame_open is not None:
        _, pivot, ang = entry
        _hinge(door, pivot)
        door.rotation_mode = 'XYZ'
        door.rotation_euler = (0, 0, 0)
        door.keyframe_insert("rotation_euler", frame=frame_open)
        door.rotation_euler = (0, 0, math.radians(ang))
        door.keyframe_insert("rotation_euler", frame=frame_open + int(seconds * FPS))
        act = door.animation_data.action
        fcs = getattr(act, "fcurves", None)
        if fcs is None:
            try:
                fcs = act.layers[0].strips[0].channelbag(act.slots[0]).fcurves
            except Exception:
                fcs = []
        for fc in fcs or []:
            for kp in fc.keyframe_points:
                kp.interpolation = 'BEZIER'; kp.easing = 'EASE_IN_OUT'
        if debug:
            for fr in (frame_open - 5, frame_open + 20, frame_open + 60):
                scene.frame_set(fr)
                print(f"[doors] entry door frame {fr}: rot z {math.degrees(door.rotation_euler.z):.0f} deg, loc {tuple(round(v, 2) for v in door.location)}")


def _hermite_t(times, pts, ease=(0.0, 0.0), tension=1.0):
    """Cardinal Hermite through pts at explicit times (seconds); end tangents scaled by `ease`; interior
    tangents scaled by `tension` (< 1 = less overshoot, closer to piecewise-linear)."""
    P = [Vector(p) if not isinstance(p, (int, float)) else Vector((p, 0, 0)) for p in pts]
    n = len(P)
    m = []
    for i in range(n):
        if i == 0:
            m.append(ease[0] * (P[1] - P[0]) / (times[1] - times[0]))
        elif i == n - 1:
            m.append(ease[1] * (P[-1] - P[-2]) / (times[-1] - times[-2]))
        else:
            m.append(tension * (P[i + 1] - P[i - 1]) / (times[i + 1] - times[i - 1]))

    def f(t):
        t = max(times[0], min(times[-1], t))
        for i in range(n - 1):
            if t <= times[i + 1]:
                h = times[i + 1] - times[i]
                s = (t - times[i]) / h
                h00 = 2 * s ** 3 - 3 * s ** 2 + 1; h10 = s ** 3 - 2 * s ** 2 + s
                h01 = -2 * s ** 3 + 3 * s ** 2; h11 = s ** 3 - s ** 2
                return h00 * P[i] + h10 * h * m[i] + h01 * P[i + 1] + h11 * h * m[i + 1]
        return P[-1].copy()
    return f


def take_curves(take):
    """(pos_f, tgt_f, lens_f, fstop_f, exp_f, n) for a take.  The look direction is interpolated as a unit vector
    (not as a look-at point), so the view never whips when a target point would pass close to the camera; the
    focus distance follows its own spline.  Optional take keys: `position_tension` (< 1 = less overshoot between
    positions) and `angular_aim` (interpolate unwrapped yaw / pitch, for long authored pans where a blend of
    near-opposite unit vectors would whip)."""
    keys = take['keys']
    times = [k['t'] for k in keys]
    n = int(round(times[-1] * FPS)) + 1
    pos_f = _hermite_t(times, [k['cam'] for k in keys], tension=take.get('position_tension', 1.0))
    dirs = [(Vector(k['tgt']) - Vector(k['cam'])).normalized() for k in keys]
    dist = [(Vector(k['tgt']) - Vector(k['cam'])).length for k in keys]
    dir_f = _hermite_t(times, dirs, tension=0.6)          # softer tangents: no overshoot on the pans
    if take.get('angular_aim'):
        yaws = []
        for d in dirs:
            yaw = math.atan2(d.y, d.x)
            if yaws:
                yaw = yaws[-1] + (yaw - yaws[-1] + math.pi) % (2 * math.pi) - math.pi
            yaws.append(yaw)
        yaw_f = _hermite_t(times, yaws, tension=0.8)
        pitch_f = _hermite_t(times, [math.asin(max(-1.0, min(1.0, d.z))) for d in dirs], tension=0.8)

        def dir_f(t):
            yaw, pitch = yaw_f(t).x, pitch_f(t).x
            return Vector((math.cos(pitch) * math.cos(yaw), math.cos(pitch) * math.sin(yaw), math.sin(pitch)))
    dist_f = _hermite_t(times, dist)

    def tgt_f(t):
        d = dir_f(t)
        if d.length < 1e-6:
            d = Vector((0, 1, 0))
        return pos_f(t) + d.normalized() * max(0.3, dist_f(t).x)
    return (pos_f, tgt_f, _hermite_t(times, [k['lens'] for k in keys]), _hermite_t(times, [k['fstop'] for k in keys]),
            _hermite_t(times, [k['exp'] for k in keys]), n)


def bake_take(scene, take):
    """Bake the long take (shots.TAKE: timed keys) onto Cam_Film: position, look-at, lens, f-stop, and the
    scene exposure, all keyed per frame.  Returns (camera, n_frames)."""
    pos_f, tgt_f, lens_f, fst_f, exp_f, n = take_curves(take)
    cam = bpy.data.objects.get("Cam_Film")
    if cam is None:
        cd = bpy.data.cameras.new("Cam_Film")
        cd.sensor_width = 36; cd.clip_start = 0.05; cd.clip_end = 800
        cam = bpy.data.objects.new("Cam_Film", cd)
        collection('Cameras').objects.link(cam)
        cam.rotation_mode = 'QUATERNION'
    cd = cam.data
    cam.rotation_mode = 'QUATERNION'
    cam.animation_data_clear(); cd.animation_data_clear(); scene.animation_data_clear()
    cd.dof.use_dof = True
    cd.dof.aperture_blades = 7
    prev = None
    for fr in range(1, n + 1):
        t = (fr - 1) / FPS
        loc, tgt = pos_f(t), tgt_f(t)
        cam.location = loc
        q = (tgt - loc).to_track_quat('-Z', 'Y')
        if prev is not None and q.dot(prev) < 0:          # q and -q are one pose; a sign jump spins the motion-blur shutter
            q.negate()
        cam.rotation_quaternion = q
        prev = q.copy()
        cd.lens = lens_f(t).x
        cd.dof.aperture_fstop = fst_f(t).x
        cd.dof.focus_distance = max(0.3, (tgt - loc).length)
        scene.view_settings.exposure = exp_f(t).x
        cam.keyframe_insert("location", frame=fr)
        cam.keyframe_insert("rotation_quaternion", frame=fr)
        cd.keyframe_insert("lens", frame=fr)
        cd.keyframe_insert("dof.aperture_fstop", frame=fr)
        cd.keyframe_insert("dof.focus_distance", frame=fr)
        scene.keyframe_insert("view_settings.exposure", frame=fr)
    for idb in (cam, cd, scene):
        act = idb.animation_data.action if idb.animation_data else None
        fcs = getattr(act, "fcurves", None)
        if fcs is None and act is not None:
            try:
                fcs = act.layers[0].strips[0].channelbag(act.slots[0]).fcurves
            except Exception:
                fcs = []
        for fc in fcs or []:
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'
    scene.camera = cam
    scene.frame_start, scene.frame_end = 1, n
    scene.render.fps = FPS
    return cam, n


def clearance_take(scene, take, radius=0.5):
    """Closest geometry along the take, reported per key interval, plus frames where the lens is inside/against a wall."""
    dg = bpy.context.evaluated_depsgraph_get()
    keys = take['keys']
    times = [k['t'] for k in keys]
    pos_f, tgt_f, _, _, _, n = take_curves(take)
    seg = 0
    worst = {}
    blocked = []
    for fr in range(1, n + 1, 2):
        t = (fr - 1) / FPS
        while seg < len(times) - 2 and t > times[seg + 1]:
            seg += 1
        loc, tgt = pos_f(t), tgt_f(t)
        best = (9.9, "")
        for d in _DIRS:
            hit, p, nrm, idx, ob, mat = scene.ray_cast(dg, loc, d, distance=radius)
            if hit and ob.type != 'LIGHT' and not ob.name.startswith(("Cam_", "L_")):
                dist = (p - loc).length
                if dist < best[0]:
                    best = (dist, ob.name)
                if dist < 0.06 and os.environ.get("FILM_DEBUG_DOORS"):
                    print(f"[take]   f{fr} cam {tuple(round(v, 2) for v in loc)} hit {ob.name} at {tuple(round(v, 2) for v in p)} dir {tuple(round(v, 1) for v in d)}")
        if best[0] < worst.get(seg, (9.9, "", 0))[0]:
            worst[seg] = (best[0], best[1], fr)
        hit, p, nrm, idx, ob, mat = scene.ray_cast(dg, loc, (tgt - loc).normalized(), distance=0.35)
        if hit and ob.type != 'LIGHT' and not ob.name.startswith(("Cam_", "L_")):
            blocked.append((fr, round(t, 1), ob.name))
            if os.environ.get("FILM_DEBUG_DOORS"):
                print(f"[take]   lens f{fr} cam {tuple(round(v, 2) for v in loc)} -> hit {ob.name} at {tuple(round(v, 2) for v in p)}")
    # pace: peak linear speed and peak angular speed of the view direction per key interval
    import math
    pace = {}
    prev = None
    for fr in range(1, n + 1):
        t = (fr - 1) / FPS
        loc, tgt = pos_f(t), tgt_f(t)
        d = (tgt - loc).normalized()
        if prev is not None:
            v = (loc - prev[0]).length * FPS
            ang = math.degrees(math.acos(max(-1.0, min(1.0, d.dot(prev[1]))))) * FPS
            k = 0
            while k < len(times) - 2 and t > times[k + 1]:
                k += 1
            pv, pa = pace.get(k, (0.0, 0.0))
            pace[k] = (max(pv, v), max(pa, ang))
            if ang > 45 and os.environ.get("FILM_DEBUG_PACE"):
                print(f"[pace] f{fr} t={t:.2f} pan {ang:.0f} deg/s dir {tuple(round(c, 2) for c in d)} cam {tuple(round(c, 1) for c in loc)}")
        prev = (loc, d)
    for i in range(len(times) - 1):
        w = worst.get(i)
        lab = keys[i].get('label', '')
        pv, pa = pace.get(i, (0.0, 0.0))
        fast = "  <-- FAST" if pa > 45 or (pv > 3.0 and keys[i]['fstop'] < 9) else ""
        pc = f"speed {pv:4.1f} m/s  pan {pa:5.1f} deg/s{fast}"
        if w:
            flag = "  <-- TIGHT" if w[0] < 0.3 else ""
            print(f"[take] {times[i]:5.1f}-{times[i + 1]:5.1f}s {lab:28s} {pc}  closest {w[0]:.2f} m f{w[2]} ({w[1]}){flag}")
        else:
            print(f"[take] {times[i]:5.1f}-{times[i + 1]:5.1f}s {lab:28s} {pc}  clear")
    if blocked:
        print(f"[take] LENS BLOCKED at (frame, t, object): {blocked[:12]}{' ...' if len(blocked) > 12 else ''}")
