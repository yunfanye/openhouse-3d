"""Procedural interior finishes (Cycles, no image textures): speckled laminate / granite counters, laminate plank
floors with per-board tint, cut-pile carpet, glazed cabinet wood, stone-look tile with grout, hand-knotted Persian rugs
with a medallion + floral field + guard borders, woven rush, carved dark wood, voile sheers.

Every function returns a bpy Material.  Colours are linear base colours; calibrate them against a photo by rendering
and comparing patch means (the listing photos are HDR-processed).  House-agnostic: object-space coordinates, metres.
"""
import math
from . import materials as _m


def _tc(nt, src='Object'):
    tc = nt.nodes.new("ShaderNodeTexCoord")
    return tc.outputs[src]


def _sep(nt, vec):
    s = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(s.inputs["Vector"], vec)
    return s.outputs["X"], s.outputs["Y"], s.outputs["Z"]


def _comb(nt, x=None, y=None, z=None):
    c = nt.nodes.new("ShaderNodeCombineXYZ")
    for k, v in (("X", x), ("Y", y), ("Z", z)):
        if v is None:
            continue
        if hasattr(v, 'is_output'):
            nt.links.new(c.inputs[k], v)
        else:
            c.inputs[k].default_value = v
    return c.outputs["Vector"]


def _scale_vec(nt, vec, s):
    vm = nt.nodes.new("ShaderNodeVectorMath"); vm.operation = 'SCALE'
    nt.links.new(vm.inputs[0], vec); vm.inputs["Scale"].default_value = s
    return vm.outputs["Vector"]


def _fleck(nt, vec, scale, density, radius, seed=0.0):
    """Mask of small round flecks: Voronoi cells (scale per metre) of which a random fraction `density` shows a dot
    of `radius` (fraction of the cell)."""
    v = nt.nodes.new("ShaderNodeTexVoronoi"); v.feature = 'F1'
    v.inputs["Scale"].default_value = scale; v.inputs["Randomness"].default_value = 1.0
    if seed:
        vm = nt.nodes.new("ShaderNodeVectorMath"); vm.operation = 'ADD'
        nt.links.new(vm.inputs[0], vec); vm.inputs[1].default_value = (seed, seed * 1.7, seed * 0.6)
        nt.links.new(v.inputs["Vector"], vm.outputs["Vector"])
    else:
        nt.links.new(v.inputs["Vector"], vec)
    r = _sep(nt, v.outputs["Color"])[0]
    pick = _m._math(nt, 'GREATER_THAN', r, 1.0 - density)
    dot = _m._math(nt, 'LESS_THAN', v.outputs["Distance"], radius)
    return _m._math(nt, 'MULTIPLY', pick, dot)


def speckle(name, base, flecks, mottle=(0.9, 1.08), mottle_scale=6.0, rough=0.35, spec=0.5, coat=0.0, bump=0.15,
            warp=0.25):
    """Speckled laminate / granite: a mottled ground plus layers of flecks.
    flecks: [(colour, cells per metre, density 0..1, radius 0..0.5), ...] laid over each other in order."""
    m, nt, b = _m._new(name)
    vec = _tc(nt)
    if warp:
        wn = nt.nodes.new("ShaderNodeTexNoise"); wn.inputs["Scale"].default_value = 30.0; wn.inputs["Detail"].default_value = 2.0
        nt.links.new(wn.inputs["Vector"], vec)
        wv = nt.nodes.new("ShaderNodeVectorMath"); wv.operation = 'MULTIPLY_ADD'
        nt.links.new(wv.inputs[0], wn.outputs["Color"]); wv.inputs[1].default_value = (warp * 0.004,) * 3
        nt.links.new(wv.inputs[2], vec)
        vec = wv.outputs["Vector"]
    mot = _m._stretch(nt, _m._noise(nt, _tc(nt), scale=mottle_scale, detail=4.0, rough=0.6), 0.3, 0.7)
    lo = tuple(c * mottle[0] for c in base[:3]) + (1,)
    hi = tuple(min(1.0, c * mottle[1]) for c in base[:3]) + (1,)
    col = _m._mixrgb(nt, mot, lo, hi)
    hsum = None
    for i, (fc, sc, dens, rad) in enumerate(flecks):
        f = _fleck(nt, vec, sc, dens, rad, seed=3.1 * (i + 1))
        col = _m._mixrgb(nt, f, col, fc)
        hsum = f if hsum is None else _m._math(nt, 'ADD', hsum, f)
    nt.links.new(b.inputs["Base Color"], col)
    _m._set(b, "Roughness", rough); _m._set(b, "Specular IOR Level", spec); _m._set(b, "Coat Weight", coat)
    _m._set(b, "Coat Roughness", 0.15)
    if bump and hsum is not None:
        _m._bump(nt, b, hsum, bump, 0.0006)
    return m


def laminate_floor(name, light, dark, plank=(1.22, 0.195), along='X', gap=0.0015, tint=0.28, rough=0.22, coat=0.35,
                   bevel=0.25, warm_tint=(1.0, 0.93, 0.88)):
    """Laminate / engineered plank floor: staggered boards, strong board-to-board tint (light / dark boards), a long
    grain with cathedral figure, micro-bevel joints and a satin wear layer."""
    m, nt, b = _m._new(name)
    x, y, z = _sep(nt, _tc(nt))
    a_, b_ = (x, y) if along == 'X' else (y, x)
    uv = _comb(nt, a_, b_, 0.0)
    br = nt.nodes.new("ShaderNodeTexBrick")
    br.offset = 0.37; br.offset_frequency = 1; br.squash = 1.0
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Mortar Size"].default_value = gap
    br.inputs["Mortar Smooth"].default_value = 0.3
    br.inputs["Bias"].default_value = 0.0
    br.inputs["Brick Width"].default_value = plank[0]
    br.inputs["Row Height"].default_value = plank[1]
    br.inputs["Color1"].default_value = (1, 1, 1, 1)
    br.inputs["Color2"].default_value = (0, 0, 0, 1)
    br.inputs["Mortar"].default_value = (0.5, 0.5, 0.5, 1)
    nt.links.new(br.inputs["Vector"], uv)
    board = _sep(nt, br.outputs["Color"])[0]                 # a random 0..1 per board
    # grain: long streaks (stretched noise) + a cathedral figure (bent wave), offset per board
    boff = _comb(nt, _m._math(nt, 'MULTIPLY', board, 13.7), _m._math(nt, 'MULTIPLY', board, 7.3), 0.0)
    vm = nt.nodes.new("ShaderNodeVectorMath"); vm.operation = 'ADD'
    nt.links.new(vm.inputs[0], uv); nt.links.new(vm.inputs[1], boff)
    g_vec = vm.outputs["Vector"]
    mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (0.6, 38.0, 1.0)
    nt.links.new(mp.inputs["Vector"], g_vec)
    streak = _m._stretch(nt, _m._noise(nt, mp.outputs["Vector"], scale=1.0, detail=6.0, rough=0.62, distortion=0.2), 0.32, 0.68)
    wave = nt.nodes.new("ShaderNodeTexWave"); wave.wave_type = 'BANDS'; wave.bands_direction = 'Y'; wave.wave_profile = 'SIN'
    wave.inputs["Scale"].default_value = 9.0; wave.inputs["Distortion"].default_value = 6.0
    wave.inputs["Detail"].default_value = 2.0; wave.inputs["Detail Scale"].default_value = 0.6
    mp2 = nt.nodes.new("ShaderNodeMapping"); mp2.inputs["Scale"].default_value = (0.25, 1.0, 1.0)
    nt.links.new(mp2.inputs["Vector"], g_vec); nt.links.new(wave.inputs["Vector"], mp2.outputs["Vector"])
    fig = _m._math(nt, 'MULTIPLY', wave.outputs["Fac"], 0.35)
    g = _m._math(nt, 'ADD', _m._math(nt, 'MULTIPLY', streak, 0.7), fig, clamp=True)
    col = _m._ramp(nt, g, [(0.0, dark), (0.55, light), (1.0, tuple(min(1, c * 1.12) for c in light[:3]) + (1,))])
    # board tint: some boards darker / redder, some lighter / browner
    t = _m._math(nt, 'ADD', _m._math(nt, 'MULTIPLY', board, 2.0 * tint), 1.0 - tint)
    col = _m._mixrgb(nt, 1.0, col, _comb_col(nt, t, t, t), 'MULTIPLY')
    hue = _m._math(nt, 'GREATER_THAN', _sep(nt, _fleck_rand(nt, uv, plank))[0], 0.6)
    col = _m._mixrgb(nt, _m._math(nt, 'MULTIPLY', hue, 0.5), col, _mul_col(col, nt, warm_tint), 'MIX')
    # joints: darker micro bevel
    joint = _m._math(nt, 'SUBTRACT', 1.0, br.outputs["Fac"])
    col = _m._mixrgb(nt, _m._math(nt, 'MULTIPLY', joint, 0.7), col, tuple(c * 0.35 for c in dark[:3]) + (1,))
    nt.links.new(b.inputs["Base Color"], col)
    _m._set(b, "Roughness", rough); _m._set(b, "Specular IOR Level", 0.5); _m._set(b, "Coat Weight", coat)
    _m._set(b, "Coat Roughness", 0.12)
    _m._bump(nt, b, _m._math(nt, 'ADD', _m._math(nt, 'MULTIPLY', br.outputs["Fac"], bevel), _m._math(nt, 'MULTIPLY', streak, 0.02)),
             0.25, 0.002)
    return m


def _comb_col(nt, r, g, bl):
    c = nt.nodes.new("ShaderNodeCombineColor")
    for k, v in (("Red", r), ("Green", g), ("Blue", bl)):
        nt.links.new(c.inputs[k], v)
    return c.outputs["Color"]


def _mul_col(col, nt, tint):
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
    mx.inputs["Factor"].default_value = 1.0
    nt.links.new(mx.inputs["A"], col); mx.inputs["B"].default_value = tuple(tint) + (1,)
    return mx.outputs["Result"]


def _fleck_rand(nt, uv, plank):
    """A second per-board random (independent of the brick colour) from a Voronoi of the board grid."""
    x, y, _ = _sep(nt, uv)
    row = _m._math(nt, 'FLOOR', _m._math(nt, 'DIVIDE', y, plank[1]))
    col = _m._math(nt, 'FLOOR', _m._math(nt, 'DIVIDE', x, plank[0] * 0.5))
    wn = nt.nodes.new("ShaderNodeTexWhiteNoise"); wn.noise_dimensions = '3D'
    nt.links.new(wn.inputs["Vector"], _comb(nt, row, col, 0.37))
    return wn.outputs["Color"]


def carpet(name, base, alt=None, rough=1.0, pile=280.0, bump=0.5, sheen=0.9):
    """Cut-pile wall-to-wall carpet: fine tufts (high-frequency noise + a voronoi tuft grain), faint tracking."""
    alt = alt or tuple(c * 0.85 for c in base[:3]) + (1,)
    m, nt, b = _m._new(name)
    vec = _tc(nt)
    tuft = _m._voronoi(nt, vec, scale=pile, feature='F1', rand=1.0)
    tr = _sep(nt, tuft.outputs["Color"])[0]
    n = _m._noise(nt, vec, scale=pile * 0.6, detail=2.0)
    big = _m._stretch(nt, _m._noise(nt, vec, scale=1.5, detail=3.0), 0.35, 0.65)
    col = _m._mixrgb(nt, _m._math(nt, 'MULTIPLY', tr, 0.55), base, alt)
    col = _m._mixrgb(nt, _m._math(nt, 'MULTIPLY', big, 0.25), col, tuple(c * 1.06 for c in base[:3]) + (1,))
    nt.links.new(b.inputs["Base Color"], col)
    _m._set(b, "Roughness", rough); _m._set(b, "Specular IOR Level", 0.15); _m._set(b, "Sheen Weight", sheen)
    _m._set(b, "Sheen Roughness", 0.4)
    _m._bump(nt, b, _m._math(nt, 'ADD', _m._math(nt, 'MULTIPLY', tuft.outputs["Distance"], 1.5), n), bump, 0.0015)
    return m


def cabinet_wood(name, light, dark, grain_axis='Z', rough=0.38, coat=0.3, glaze=0.35, glaze_dist=0.012, ring=22.0,
                 figure=0.3):
    """Stained maple / cherry cabinetry: fine straight grain with a soft figure, a darker glaze that collects in the
    panel recesses (ambient occlusion), satin lacquer."""
    m, nt, b = _m._new(name)
    sc = {'Z': (ring, ring, 0.5), 'X': (0.5, ring, ring), 'Y': (ring, 0.5, ring)}[grain_axis]
    vec = _m._coords(nt, scale=sc)
    g = _m._noise(nt, vec, scale=1.0, detail=5.0, rough=0.62, distortion=0.35)
    fsc = {'Z': (6, 6, 0.4), 'X': (0.4, 6, 6), 'Y': (6, 0.4, 6)}[grain_axis]
    fig = _m._stretch(nt, _m._noise(nt, _m._coords(nt, scale=fsc), scale=1.0, detail=3.0, distortion=1.2), 0.35, 0.65)
    gg = _m._math(nt, 'ADD', _m._math(nt, 'MULTIPLY', _m._stretch(nt, g, 0.3, 0.7), 1.0 - figure), _m._math(nt, 'MULTIPLY', fig, figure))
    col = _m._ramp(nt, gg, [(0.0, dark), (0.45, light), (0.75, light), (1.0, dark)])
    fine = _m._noise(nt, _m._coords(nt, scale=(120, 120, 120)), scale=1.0, detail=2.0)
    col = _m._mixrgb(nt, _m._math(nt, 'MULTIPLY', fine, 0.12), col, (0.88, 0.84, 0.8, 1), 'MULTIPLY')
    if glaze > 0:
        ao = nt.nodes.new("ShaderNodeAmbientOcclusion"); ao.samples = 4; ao.only_local = True
        ao.inputs["Distance"].default_value = glaze_dist
        dk = tuple(c * 0.45 for c in dark[:3]) + (1,)
        f = _m._math(nt, 'MULTIPLY', _m._math(nt, 'SUBTRACT', 1.0, ao.outputs["AO"]), glaze * 2.0, clamp=True)
        col = _m._mixrgb(nt, f, col, dk)
    nt.links.new(b.inputs["Base Color"], col)
    _m._set(b, "Roughness", rough); _m._set(b, "Specular IOR Level", 0.45); _m._set(b, "Coat Weight", coat)
    _m._set(b, "Coat Roughness", 0.3)
    _m._bump(nt, b, g, 0.04, 0.003)
    return m


def stone_tile(name, colours, grout=(0.36, 0.33, 0.29, 1), size=(0.305, 0.305), gap=0.004, plane='XZ', rough=0.5,
               vein=0.35, pits=0.3, bump=0.25, offset=0.0, per_island=False):
    """Travertine / slate-look porcelain tile: per-tile colour picked from `colours`, cloudy mottling and soft veins
    inside each tile, pits, recessed grout joints.  per_island=True: the tiles are modelled as separate slabs
    (real joints); each mesh island then gets its own colour and stone offset and the shader draws no joints."""
    m, nt, b = _m._new(name)
    x, y, z = _sep(nt, _tc(nt))
    a_, b_ = {'XY': (x, y), 'XZ': (x, z), 'YZ': (y, z)}[plane]
    uv = _comb(nt, a_, b_, 0.0)
    if per_island:
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        t = geo.outputs["Random Per Island"]
        joint = None
    else:
        br = nt.nodes.new("ShaderNodeTexBrick")
        br.offset = offset; br.offset_frequency = 2
        br.inputs["Scale"].default_value = 1.0
        br.inputs["Mortar Size"].default_value = gap
        br.inputs["Mortar Smooth"].default_value = 0.15
        br.inputs["Brick Width"].default_value = size[0]
        br.inputs["Row Height"].default_value = size[1]
        br.inputs["Color1"].default_value = (1, 1, 1, 1); br.inputs["Color2"].default_value = (0, 0, 0, 1)
        nt.links.new(br.inputs["Vector"], uv)
        t = _sep(nt, br.outputs["Color"])[0]                    # per-tile random
        joint = br.outputs["Fac"]
    n = len(colours)
    col = colours[0]
    for i in range(1, n):
        col = _m._mixrgb(nt, _m._math(nt, 'GREATER_THAN', t, i / n), col, colours[i])
    # per-tile offset so neighbouring tiles show different parts of the stone
    off = _comb(nt, _m._math(nt, 'MULTIPLY', t, 17.0), _m._math(nt, 'MULTIPLY', t, 9.0), _m._math(nt, 'MULTIPLY', t, 5.0))
    vm = nt.nodes.new("ShaderNodeVectorMath"); vm.operation = 'ADD'
    nt.links.new(vm.inputs[0], uv); nt.links.new(vm.inputs[1], off)
    cloud = _m._stretch(nt, _m._noise(nt, vm.outputs["Vector"], scale=7.0, detail=6.0, rough=0.62, distortion=0.6), 0.3, 0.7)
    col = _m._mixrgb(nt, 1.0, col, _m._ramp(nt, cloud, [(0.0, (0.78, 0.76, 0.74, 1)), (0.6, (1.0, 1.0, 1.0, 1)), (1.0, (1.14, 1.12, 1.08, 1))]),
                     'MULTIPLY')
    mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1.0, 5.0, 1.0)
    nt.links.new(mp.inputs["Vector"], vm.outputs["Vector"])
    vn = _m._noise(nt, mp.outputs["Vector"], scale=4.0, detail=3.0, distortion=1.5)
    v = _m._math(nt, 'SUBTRACT', 1.0, _m._math(nt, 'MULTIPLY', _m._math(nt, 'ABSOLUTE', _m._math(nt, 'SUBTRACT', vn, 0.5)), 14.0, clamp=True))
    col = _m._mixrgb(nt, _m._math(nt, 'MULTIPLY', v, vein), col, (0.55, 0.50, 0.44, 1), 'MULTIPLY')
    pit = _fleck(nt, _tc(nt), 90.0, pits, 0.25, seed=1.3)
    col = _m._mixrgb(nt, _m._math(nt, 'MULTIPLY', pit, 0.5), col, (0.42, 0.38, 0.33, 1))
    if joint is not None:
        col = _m._mixrgb(nt, _m._math(nt, 'SUBTRACT', 1.0, joint), col, grout)
    nt.links.new(b.inputs["Base Color"], col)
    _m._set(b, "Roughness", rough); _m._set(b, "Specular IOR Level", 0.45)
    h = _m._math(nt, 'SUBTRACT', joint if joint is not None else 1.0, _m._math(nt, 'MULTIPLY', pit, 0.3))
    _m._bump(nt, b, h, bump, 0.002)
    return m


def persian_rug(name, field, border, accent, ivory, dark, medallion=True, fringe=None, rough=0.95, motif=11.0,
                border_w=0.12, seed=0.0):
    """Hand-knotted Persian (Kashan / Tabriz-look) rug on a unit-square Generated mapping (build the rug as ONE box so
    Generated spans it): an ivory `field` densely covered with small palmettes (`accent` / `dark` / `border` tones)
    and thin scrolling vines, a small lobed medallion, a wide `border` band carrying dark floral motifs between ivory
    and dark guard stripes, abrash (dye bands), knot texture and a soft worn sheen.  `motif` = palmettes per metre."""
    m, nt, b = _m._new(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    u, v, _ = _sep(nt, tc.outputs["Generated"])
    ob = tc.outputs["Object"]
    du = _m._math(nt, 'MINIMUM', u, _m._math(nt, 'SUBTRACT', 1.0, u))
    dv = _m._math(nt, 'MINIMUM', v, _m._math(nt, 'SUBTRACT', 1.0, v))
    edge = _m._math(nt, 'MINIMUM', du, dv)

    wv = nt.nodes.new("ShaderNodeVectorMath"); wv.operation = 'ADD'           # a gently warped domain for the motifs
    nt.links.new(wv.inputs[0], ob)
    wn = nt.nodes.new("ShaderNodeTexNoise"); wn.inputs["Scale"].default_value = motif * 0.9
    nt.links.new(wn.inputs["Vector"], ob)
    wsc = nt.nodes.new("ShaderNodeVectorMath"); wsc.operation = 'SCALE'; wsc.inputs["Scale"].default_value = 0.35 / motif
    nt.links.new(wsc.inputs[0], wn.outputs["Color"]); nt.links.new(wv.inputs[1], wsc.outputs["Vector"])
    wob_vec = wv.outputs["Vector"]

    def palmettes(scale, size, seed_, dens=1.0, lobes=5.0, elong=1.4):
        """Lobed, elongated palmette / rosette motifs on a jittered grid: shape, outline ring, core, 2 randoms."""
        sv = _scale_vec(nt, wob_vec, scale)
        vv = _m._voronoi(nt, sv, scale=1.0, feature='F1', rand=0.8)
        dvec = nt.nodes.new("ShaderNodeVectorMath"); dvec.operation = 'SUBTRACT'
        nt.links.new(dvec.inputs[0], sv); nt.links.new(dvec.inputs[1], vv.outputs["Position"])
        qx, qy, _qz = _sep(nt, dvec.outputs["Vector"])
        r, g, bb = _sep(nt, vv.outputs["Color"])
        qy = _m._math(nt, 'DIVIDE', qy, elong)
        dist = _m._math(nt, 'SQRT', _m._math(nt, 'ADD', _m._math(nt, 'MULTIPLY', qx, qx), _m._math(nt, 'MULTIPLY', qy, qy)))
        ang = _m._math(nt, 'ARCTAN2', qy, qx)
        lobe = _m._math(nt, 'COSINE', _m._math(nt, 'ADD', _m._math(nt, 'MULTIPLY', ang, lobes), _m._math(nt, 'MULTIPLY', r, 6.283)))
        d = _m._math(nt, 'MULTIPLY', dist, _m._math(nt, 'ADD', 1.0, _m._math(nt, 'MULTIPLY', lobe, 0.16)))
        on = _m._math(nt, 'LESS_THAN', bb, dens)
        shape = _m._math(nt, 'MULTIPLY', _m._math(nt, 'LESS_THAN', d, size), on)
        ring = _m._math(nt, 'MULTIPLY', shape, _m._math(nt, 'GREATER_THAN', d, size - 0.07))
        core = _m._math(nt, 'MULTIPLY', shape, _m._math(nt, 'LESS_THAN', d, size * 0.40))
        return shape, ring, core, r, g
    # field: ivory ground, scrolling vines, large palmettes (rust / navy / blue-grey), small florets
    col = field
    vine_n = _m._noise(nt, _scale_vec(nt, ob, motif * 0.7), scale=1.0, detail=3.0, distortion=2.4)
    vine = _m._math(nt, 'LESS_THAN', _m._math(nt, 'ABSOLUTE', _m._math(nt, 'SUBTRACT', vine_n, 0.5)), 0.045)
    col = _m._mixrgb(nt, vine, col, _m._mixrgb(nt, 0.6, dark, field))
    vine2_n = _m._noise(nt, _scale_vec(nt, ob, motif * 1.6), scale=1.0, detail=2.0, distortion=2.0)
    vine2 = _m._math(nt, 'LESS_THAN', _m._math(nt, 'ABSOLUTE', _m._math(nt, 'SUBTRACT', vine2_n, 0.5)), 0.03)
    col = _m._mixrgb(nt, vine2, col, _m._mixrgb(nt, 0.4, accent, field))
    shape, ring, core, r, g = palmettes(motif, 0.46, seed, dens=0.9)
    pc = _m._mixrgb(nt, _m._math(nt, 'GREATER_THAN', r, 0.55), accent, border)
    pc = _m._mixrgb(nt, _m._math(nt, 'GREATER_THAN', g, 0.72), pc, _m._mixrgb(nt, 0.5, accent, ivory))
    col = _m._mixrgb(nt, shape, col, pc)
    col = _m._mixrgb(nt, ring, col, dark)
    col = _m._mixrgb(nt, core, col, ivory)
    s2, r2, c2, rr, gg = palmettes(motif * 2.4, 0.30, seed + 5.0, dens=0.6)
    col = _m._mixrgb(nt, s2, col, _m._mixrgb(nt, _m._math(nt, 'GREATER_THAN', gg, 0.5), dark, accent))
    col = _m._mixrgb(nt, c2, col, _m._mixrgb(nt, 0.5, border, ivory))
    s3, r3, c3, rr3, gg3 = palmettes(motif * 4.5, 0.24, seed + 11.0, dens=0.35)            # buds
    col = _m._mixrgb(nt, s3, col, _m._mixrgb(nt, _m._math(nt, 'GREATER_THAN', gg3, 0.6), border, dark))
    if medallion:
        cu = _m._math(nt, 'SUBTRACT', u, 0.5); cv = _m._math(nt, 'MULTIPLY', _m._math(nt, 'SUBTRACT', v, 0.5), 1.4)
        rr_ = _m._math(nt, 'SQRT', _m._math(nt, 'ADD', _m._math(nt, 'MULTIPLY', cu, cu), _m._math(nt, 'MULTIPLY', cv, cv)))
        ang = _m._math(nt, 'ARCTAN2', cv, cu)
        lob = _m._math(nt, 'ADD', rr_, _m._math(nt, 'MULTIPLY', _m._math(nt, 'COSINE', _m._math(nt, 'MULTIPLY', ang, 12.0)), 0.010))
        ringm = _m._math(nt, 'MULTIPLY', _m._math(nt, 'LESS_THAN', lob, 0.105), _m._math(nt, 'GREATER_THAN', lob, 0.095))
        col = _m._mixrgb(nt, ringm, col, dark)
        col = _m._mixrgb(nt, _m._math(nt, 'MULTIPLY', _m._math(nt, 'LESS_THAN', lob, 0.095), 0.35), col, border)
    # border band (rust) with dark / ivory florets, guard stripes
    bw = border_w
    bb, br_, bc_, b_r, b_g = palmettes(motif * 1.5, 0.34, seed + 9.0, dens=0.8)
    bcol = _m._mixrgb(nt, bb, border, _m._mixrgb(nt, _m._math(nt, 'GREATER_THAN', b_r, 0.5), dark, _m._mixrgb(nt, 0.5, accent, ivory)))
    bcol = _m._mixrgb(nt, bc_, bcol, ivory)
    col = _m._mixrgb(nt, _m._math(nt, 'LESS_THAN', edge, bw), col, bcol)
    for (lo, hi, c) in ((bw, bw + 0.010, ivory), (bw + 0.010, bw + 0.016, dark), (bw - 0.008, bw, dark), (0.0, 0.010, dark),
                        (0.010, 0.020, ivory)):
        band = _m._math(nt, 'MULTIPLY', _m._math(nt, 'GREATER_THAN', edge, lo), _m._math(nt, 'LESS_THAN', edge, hi))
        col = _m._mixrgb(nt, band, col, c)
    # abrash and knots
    ab = _m._stretch(nt, _m._noise(nt, _comb(nt, _m._math(nt, 'MULTIPLY', v, 3.0), seed, 0.0), scale=2.0, detail=2.0), 0.3, 0.7)
    col = _m._mixrgb(nt, _m._math(nt, 'MULTIPLY', ab, 0.12), col, (0.8, 0.8, 0.8, 1), 'MULTIPLY')
    knot = _m._noise(nt, _scale_vec(nt, ob, 420.0), scale=1.0, detail=1.0)
    col = _m._mixrgb(nt, _m._math(nt, 'MULTIPLY', knot, 0.2), col, (0.84, 0.84, 0.84, 1), 'MULTIPLY')
    nt.links.new(b.inputs["Base Color"], col)
    _m._set(b, "Roughness", rough); _m._set(b, "Specular IOR Level", 0.08); _m._set(b, "Sheen Weight", 0.12)
    _m._set(b, "Sheen Roughness", 0.5)
    _m._bump(nt, b, knot, 0.25, 0.002)
    return m


def rush(name, base=(0.50, 0.38, 0.18, 1), alt=(0.36, 0.25, 0.10, 1), pitch=0.012, axis='X', rough=0.8):
    """Woven rush / seagrass seat: two crossing sets of twisted cords (wave bands) with shading between them."""
    m, nt, b = _m._new(name)
    x, y, z = _sep(nt, _tc(nt))
    out = []
    for (p, q) in ((x, y), (y, x)):
        w = nt.nodes.new("ShaderNodeTexWave"); w.wave_type = 'BANDS'; w.bands_direction = 'X'; w.wave_profile = 'SIN'
        w.inputs["Scale"].default_value = 1.0 / pitch / 6.283; w.inputs["Distortion"].default_value = 0.0
        nt.links.new(w.inputs["Vector"], _comb(nt, _m._math(nt, 'ADD', p, _m._math(nt, 'MULTIPLY', q, 0.3)), q, 0.0))
        out.append(w.outputs["Fac"])
    h = _m._math(nt, 'MAXIMUM', out[0], out[1])
    col = _m._ramp(nt, h, [(0.0, alt), (0.6, base), (1.0, tuple(min(1, c * 1.2) for c in base[:3]) + (1,))])
    n = _m._noise(nt, _tc(nt), scale=60.0, detail=2.0)
    col = _m._mixrgb(nt, _m._math(nt, 'MULTIPLY', n, 0.3), col, (0.8, 0.78, 0.7, 1), 'MULTIPLY')
    nt.links.new(b.inputs["Base Color"], col)
    _m._set(b, "Roughness", rough); _m._set(b, "Specular IOR Level", 0.3); _m._set(b, "Sheen Weight", 0.4)
    _m._bump(nt, b, h, 0.6, 0.004)
    return m


def carved_wood(name, base=(0.06, 0.035, 0.022, 1), high=(0.16, 0.10, 0.06, 1), scale=60.0, depth=1.0, rough=0.42,
                coat=0.25, lacquer_black=False):
    """Carved / turned dark hardwood (Indian sheesham or teak): fine foliate carving relief (a low bump of smooth
    voronoi + noise), wear that lifts the raised parts slightly toward `high`, satin lacquer; optional black
    lacquer with brown wear on the high points."""
    m, nt, b = _m._new(name)
    vec = _tc(nt)
    vor = _m._voronoi(nt, _scale_vec(nt, vec, scale), scale=1.0, feature='SMOOTH_F1', rand=0.8)
    n = _m._noise(nt, _scale_vec(nt, vec, scale * 1.8), scale=1.0, detail=3.0, distortion=1.4)
    hgt = _m._math(nt, 'ADD', _m._math(nt, 'MULTIPLY', vor.outputs["Distance"], 1.0), _m._math(nt, 'MULTIPLY', n, 0.5))
    hs = _m._stretch(nt, hgt, 0.55, 1.0)
    grain = _m._noise(nt, _m._coords(nt, scale=(30, 30, 0.5)), scale=1.0, detail=3.0)
    col = _m._mixrgb(nt, _m._math(nt, 'MULTIPLY', hs, 0.45), base, high)
    col = _m._mixrgb(nt, _m._math(nt, 'MULTIPLY', grain, 0.3), col, (0.75, 0.70, 0.65, 1), 'MULTIPLY')
    if lacquer_black:
        col = _m._mixrgb(nt, _m._math(nt, 'MULTIPLY', _m._math(nt, 'SUBTRACT', 1.0, hs), 0.85), col, (0.012, 0.011, 0.011, 1))
    nt.links.new(b.inputs["Base Color"], col)
    _m._set(b, "Roughness", rough); _m._set(b, "Specular IOR Level", 0.45); _m._set(b, "Coat Weight", coat)
    _m._set(b, "Coat Roughness", 0.25)
    _m._bump(nt, b, hgt, 0.35 * depth, 0.003)
    return m


def voile(name, color=(0.90, 0.89, 0.86, 1), alpha=0.55, weave=900.0, slub=0.35):
    """Sheer voile / linen-look curtain: translucent + transparent mix whose opacity follows a slubbed weave."""
    m, nt, b = _m._new(name)
    vec = _tc(nt)
    x, y, z = _sep(nt, vec)
    w1 = _m._noise(nt, _comb(nt, _m._math(nt, 'MULTIPLY', x, 2.0), _m._math(nt, 'MULTIPLY', y, 2.0), _m._math(nt, 'MULTIPLY', z, 60.0)), scale=4.0, detail=1.0)
    sl = _m._stretch(nt, w1, 0.35, 0.65)
    _m._set(b, "Base Color", color); _m._set(b, "Roughness", 0.8); _m._set(b, "Sheen Weight", 0.8)
    tr = nt.nodes.new("ShaderNodeBsdfTranslucent"); tr.inputs["Color"].default_value = color
    tp = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix1 = nt.nodes.new("ShaderNodeMixShader"); mix1.inputs["Fac"].default_value = 0.55
    nt.links.new(mix1.inputs[1], b.outputs["BSDF"]); nt.links.new(mix1.inputs[2], tr.outputs["BSDF"])
    mix2 = nt.nodes.new("ShaderNodeMixShader")
    a = _m._math(nt, 'ADD', alpha * (1 - slub), _m._math(nt, 'MULTIPLY', sl, alpha * slub * 2.0), clamp=True)
    nt.links.new(mix2.inputs["Fac"], a)
    nt.links.new(mix2.inputs[1], tp.outputs["BSDF"]); nt.links.new(mix2.inputs[2], mix1.outputs["Shader"])
    nt.links.new(nt.nodes["Material Output"].inputs["Surface"], mix2.outputs["Shader"])
    return m


def brushed_metal(name, base=(0.62, 0.61, 0.59, 1), rough=0.28, axis='X', streak=0.3):
    """Brushed stainless / nickel: fine streaks along `axis` in the colour and the roughness."""
    m, nt, b = _m._new(name)
    sc = {'X': (0.3, 400, 400), 'Y': (400, 0.3, 400), 'Z': (400, 400, 0.3)}[axis]
    n = _m._noise(nt, _m._coords(nt, scale=sc), scale=1.0, detail=2.0)
    col = _m._mixrgb(nt, _m._math(nt, 'MULTIPLY', n, streak), base, tuple(c * 0.85 for c in base[:3]) + (1,))
    nt.links.new(b.inputs["Base Color"], col)
    _m._set(b, "Metallic", 1.0)
    rr = _m._math(nt, 'ADD', rough * (1.0 - streak * 0.5), _m._math(nt, 'MULTIPLY', n, rough * streak))
    nt.links.new(b.inputs["Roughness"], rr)
    return m


def shadow_glass(name, tint=(0.80, 0.80, 0.80, 1), rough=0.02, ior=1.5, reflect=1.0):
    """Clear / tinted glass that lets shadow rays through (Light Path 'Is Shadow Ray' -> Transparent), so objects
    behind it (fireplace logs, a cabinet interior, a shower) are lit without caustics."""
    m, nt, b = _m._new(name)
    _m._set(b, "Base Color", tint); _m._set(b, "Roughness", rough); _m._set(b, "Transmission Weight", 1.0)
    _m._set(b, "IOR", ior); _m._set(b, "Specular IOR Level", 0.5 * reflect)
    lp = nt.nodes.new("ShaderNodeLightPath")
    tp = nt.nodes.new("ShaderNodeBsdfTransparent"); tp.inputs["Color"].default_value = tint
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(mx.inputs["Fac"], lp.outputs["Is Shadow Ray"])
    nt.links.new(mx.inputs[1], b.outputs["BSDF"]); nt.links.new(mx.inputs[2], tp.outputs["BSDF"])
    nt.links.new(nt.nodes["Material Output"].inputs["Surface"], mx.outputs["Shader"])
    return m


def cerused_wood(name, base=(0.032, 0.022, 0.017, 1), pores=(0.20, 0.18, 0.16, 1), grain_axis='X', ring=26.0, rough=0.5,
                 wire=0.55, coat=0.1):
    """Wire-brushed, cerused dark oak (espresso stain with pale grain): a dark ground, long open-grain streaks and
    cathedral figure filled with a light wax (`pores`), a brushed bump."""
    m, nt, b = _m._new(name)
    sc = {'Z': (ring, ring, 0.3), 'X': (0.3, ring, ring), 'Y': (ring, 0.3, ring)}[grain_axis]
    g = _m._noise(nt, _m._coords(nt, scale=sc), scale=1.0, detail=6.0, rough=0.65, distortion=0.6)
    sc2 = {'Z': (ring * 6, ring * 6, 2.0), 'X': (2.0, ring * 6, ring * 6), 'Y': (ring * 6, 2.0, ring * 6)}[grain_axis]
    pore = _m._noise(nt, _m._coords(nt, scale=sc2), scale=1.0, detail=2.0)
    streak = _m._math(nt, 'MULTIPLY', _m._stretch(nt, g, 0.52, 0.66), _m._stretch(nt, pore, 0.45, 0.7))
    col = _m._mixrgb(nt, _m._math(nt, 'MULTIPLY', streak, wire), base, pores)
    nt.links.new(b.inputs["Base Color"], col)
    _m._set(b, "Roughness", rough); _m._set(b, "Specular IOR Level", 0.4); _m._set(b, "Coat Weight", coat)
    _m._bump(nt, b, _m._math(nt, 'SUBTRACT', 1.0, streak), 0.25, 0.002)
    return m


def knockdown_ceiling(name, base=(0.74, 0.715, 0.655, 1), relief=0.9, splat=26.0, shade=0.10, stipple=0.35):
    """Knock-down drywall ceiling that still reads at room-camera distance: flat-topped splats (a thresholded noise at
    `splat` per metre, 2-5 cm islands) with rounded rims, a fine stipple between them, a slightly darker, warmer tone
    in the low areas (joint compound catches less light / dust) and a strong short-range bump."""
    m, nt, b = _m._new(name)
    vec = _tc(nt)
    n = _m._noise(nt, _scale_vec(nt, vec, splat), scale=1.0, detail=5.0, rough=0.6, distortion=0.8)
    isl = _m._stretch(nt, n, 0.47, 0.55)                       # 0 = trough, 1 = flattened splat top
    fine = _m._noise(nt, _scale_vec(nt, vec, splat * 6.0), scale=1.0, detail=2.0)
    low = _m._math(nt, 'SUBTRACT', 1.0, isl)
    dark = tuple(c * (1.0 - shade) for c in base[:3]) + (1,)
    warm = (dark[0], dark[1] * 0.985, dark[2] * 0.955, 1)
    col = _m._mixrgb(nt, low, base, warm)
    # the splats' rims: a thin darker line where the knife lifted the compound (what makes knock-down read in photos; as
    # albedo it also survives the denoiser, which smooths a pure bump away)
    rim = _m._math(nt, 'SUBTRACT', 1.0, _m._math(nt, 'MULTIPLY', _m._math(nt, 'ABSOLUTE', _m._math(nt, 'SUBTRACT', n, 0.505)), 60.0,
                                                     clamp=True))
    rimc = tuple(c * (1.0 - 2.2 * shade) for c in base[:3]) + (1,)
    col = _m._mixrgb(nt, _m._math(nt, 'MULTIPLY', rim, 0.8), col, rimc)
    col = _m._mixrgb(nt, _m._math(nt, 'MULTIPLY', fine, 0.06), col, (0.9, 0.9, 0.9, 1), 'MULTIPLY')
    nt.links.new(b.inputs["Base Color"], col)
    _m._set(b, "Roughness", 0.95); _m._set(b, "Specular IOR Level", 0.2)
    h = _m._math(nt, 'ADD', isl, _m._math(nt, 'MULTIPLY', fine, stipple))
    _m._bump(nt, b, h, relief, 0.0025)
    return m
