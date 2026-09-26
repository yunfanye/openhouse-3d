"""Procedural material library (Cycles, no image textures): stone, wood, glass, metals, fabrics, water, foliage cards,
emitters, art.  Every material is a function `name(...)` returning a bpy Material; `build_materials()` assembles the
default modern-villa palette (a dict of ~140 keyed materials) that the house modules index as M['trav'], M['oak'] ...

A house can extend the palette (add keys / override entries) in its house.py `materials()` hook.
Helpers `_new/_math/_ramp/_mixrgb/_stretch/_coords/_noise/_voronoi/_bump` are used by trees.py and polish.py too.
"""
import bpy, math

# ------------------------------------------------------------------ node helpers
def _bsdf(m):
    return m.node_tree.nodes["Principled BSDF"]

def _set(node, name, val):
    s = node.inputs.get(name)
    if s is not None:
        s.default_value = val

def _new(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    return m, m.node_tree, _bsdf(m)

def _node(nt, kind, **kw):
    n = nt.nodes.new(kind)
    for k, v in kw.items():
        if k == 'inputs':
            for ik, iv in v.items():
                n.inputs[ik].default_value = iv
        else:
            setattr(n, k, v)
    return n

def _math(nt, op, a, b=None, clamp=False):
    n = nt.nodes.new("ShaderNodeMath"); n.operation = op; n.use_clamp = clamp
    if hasattr(a, 'is_output'):
        nt.links.new(n.inputs[0], a)
    else:
        n.inputs[0].default_value = a
    if b is not None:
        if hasattr(b, 'is_output'):
            nt.links.new(n.inputs[1], b)
        else:
            n.inputs[1].default_value = b
    return n.outputs[0]

def _ramp(nt, fac, stops):
    """stops: list of (pos, (r,g,b,a))"""
    r = nt.nodes.new("ShaderNodeValToRGB")
    cr = r.color_ramp
    while len(cr.elements) < len(stops):
        cr.elements.new(0.5)
    for e, (p, c) in zip(cr.elements, stops):
        e.position = p; e.color = c
    nt.links.new(r.inputs["Fac"], fac)
    return r.outputs["Color"]

def _mixrgb(nt, fac, a, b, blend='MIX'):
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = blend
    for sock, val in (("Factor", fac), ("A", a), ("B", b)):
        if hasattr(val, 'is_output'):
            nt.links.new(mx.inputs[sock], val)
        else:
            mx.inputs[sock].default_value = val
    return mx.outputs["Result"]

def _stretch(nt, fac, lo=0.35, hi=0.65):
    """Map-range a noise factor so its typical lo..hi band spans 0..1 (clamped)."""
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.clamp = True
    mr.inputs["From Min"].default_value = lo; mr.inputs["From Max"].default_value = hi
    nt.links.new(mr.inputs["Value"], fac)
    return mr.outputs["Result"]


def _coords(nt, scale=(1, 1, 1), rot=(0, 0, 0), loc=(0, 0, 0), src='Object'):
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = scale
    mp.inputs["Rotation"].default_value = rot
    mp.inputs["Location"].default_value = loc
    nt.links.new(mp.inputs["Vector"], tc.outputs[src])
    return mp.outputs["Vector"]

def _noise(nt, vec, scale=5.0, detail=4.0, rough=0.5, distortion=0.0, dim='3D'):
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.noise_dimensions = dim
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = detail
    n.inputs["Roughness"].default_value = rough
    n.inputs["Distortion"].default_value = distortion
    nt.links.new(n.inputs["Vector"], vec)
    return n.outputs["Fac"]

def _voronoi(nt, vec, scale=10.0, feature='F1', rand=1.0):
    v = nt.nodes.new("ShaderNodeTexVoronoi")
    v.feature = feature
    v.inputs["Scale"].default_value = scale
    v.inputs["Randomness"].default_value = rand
    nt.links.new(v.inputs["Vector"], vec)
    return v

def _bump(nt, b, height, strength, distance=0.02, normal_in=None):
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = strength
    bp.inputs["Distance"].default_value = distance
    nt.links.new(bp.inputs["Height"], height)
    if normal_in is not None:
        nt.links.new(bp.inputs["Normal"], normal_in)
    nt.links.new(b.inputs["Normal"], bp.outputs["Normal"])
    return bp


def new_mat(name, base=(0.8, 0.8, 0.8, 1), rough=0.5, metal=0.0, spec=0.5, transmission=0.0, ior=1.45,
            emit=None, emit_str=0.0, coat=0.0, sheen=0.0, subsurface=0.0, alpha=1.0):
    m, nt, b = _new(name)
    _set(b, "Base Color", base); _set(b, "Roughness", rough); _set(b, "Metallic", metal)
    _set(b, "Specular IOR Level", spec); _set(b, "Transmission Weight", transmission); _set(b, "IOR", ior)
    _set(b, "Coat Weight", coat); _set(b, "Sheen Weight", sheen); _set(b, "Subsurface Weight", subsurface)
    _set(b, "Alpha", alpha)
    if emit is not None:
        _set(b, "Emission Color", emit); _set(b, "Emission Strength", emit_str)
    return m


# ------------------------------------------------------------------ stone
def travertine(name, light=(0.90, 0.83, 0.70, 1), mid=(0.82, 0.73, 0.59, 1), dark=(0.70, 0.59, 0.45, 1),
               band_scale=2.2, pit=0.22, rough=0.42, bump=0.08, emit=0.0, band_axis='Z', panels=(1.2, 0.6)):
    """Vein-cut travertine (photos 02/23): a creamy ground with many fine, closely spaced horizontal layers of
    slightly darker sediment, a few thin dark streaks, small pits, and 1.2 x 0.6 m cladding panels whose tint varies
    a little from panel to panel.  Contrast is deliberately low - the real stone reads as beige, not as wood grain."""
    m, nt, b = _new(name)
    sc = (1.0, 1.0, 7.0) if band_axis == 'Z' else ((7.0, 1.0, 1.0) if band_axis == 'X' else (1.0, 7.0, 1.0))
    vec_b = _coords(nt, scale=(band_scale * sc[0], band_scale * sc[1], band_scale * sc[2]))
    vec_f = _coords(nt, scale=(band_scale * sc[0] * 0.5, band_scale * sc[1] * 0.5, band_scale * sc[2] * 4.0))
    vec_s = _coords(nt, scale=(band_scale * sc[0] * 0.25, band_scale * sc[1] * 0.25, band_scale * sc[2] * 9.0))
    bands = _stretch(nt, _noise(nt, vec_b, scale=1.0, detail=4.0, rough=0.55, distortion=0.5), 0.30, 0.70)
    fine = _stretch(nt, _noise(nt, vec_f, scale=1.0, detail=3.0, rough=0.6, distortion=0.3), 0.32, 0.68)
    # thin dark streaks: where a strongly flattened noise crosses 0.5 (a few per 10 cm, broken up by a mask)
    sn = _noise(nt, vec_s, scale=1.0, detail=2.0, rough=0.5)
    streak = _math(nt, 'SUBTRACT', 1.0, _math(nt, 'MULTIPLY', _math(nt, 'ABSOLUTE', _math(nt, 'SUBTRACT', sn, 0.5)), 22.0, clamp=True))
    streak = _math(nt, 'MULTIPLY', streak, _math(nt, 'GREATER_THAN', _noise(nt, vec_b, scale=2.5, detail=2.0), 0.48))
    layers = _math(nt, 'ADD', _math(nt, 'MULTIPLY', bands, 0.55), _math(nt, 'MULTIPLY', fine, 0.45))
    vec = _coords(nt)
    grain = _noise(nt, vec, scale=45.0, detail=3.0, rough=0.6)
    vor = _voronoi(nt, vec, scale=38.0, feature='F1')
    pits_raw = _math(nt, 'LESS_THAN', vor.outputs["Distance"], 0.14)
    pit_mask = _math(nt, 'GREATER_THAN', _noise(nt, vec, scale=6.0, detail=2.0), 0.58)
    pits = _math(nt, 'MULTIPLY', _math(nt, 'MULTIPLY', pits_raw, pit_mask), pit)
    lighter = (min(1, light[0] * 1.04), min(1, light[1] * 1.04), min(1, light[2] * 1.04), 1)
    base = _ramp(nt, layers, [(0.0, dark), (0.30, mid), (0.62, light), (1.0, lighter)])
    base = _mixrgb(nt, _math(nt, 'MULTIPLY', streak, 0.45), base, (dark[0] * 0.85, dark[1] * 0.85, dark[2] * 0.85, 1))
    base = _mixrgb(nt, _math(nt, 'MULTIPLY', grain, 0.12), base, (0.98, 0.95, 0.9, 1), 'MULTIPLY')
    base = _mixrgb(nt, pits, base, (dark[0] * 0.6, dark[1] * 0.6, dark[2] * 0.6, 1))
    # cladding panels: 1.2 x 0.6 m running bond with 6 mm joints; the wall axis is picked from the surface normal
    if panels:
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        nsep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(nsep.inputs["Vector"], geo.outputs["True Normal"])
        tcp = nt.nodes.new("ShaderNodeTexCoord")
        psep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(psep.inputs["Vector"], tcp.outputs["Object"])
        facing_x = _math(nt, 'GREATER_THAN', _math(nt, 'ABSOLUTE', nsep.outputs["X"]), 0.5)
        horiz = _math(nt, 'GREATER_THAN', _math(nt, 'ABSOLUTE', nsep.outputs["Z"]), 0.7)
        # u = along-wall coordinate (y for x-facing walls, x otherwise); v = z (or y on horizontal faces)
        u = nt.nodes.new("ShaderNodeMix"); u.data_type = 'FLOAT'
        nt.links.new(u.inputs["Factor"], facing_x); nt.links.new(u.inputs["A"], psep.outputs["X"]); nt.links.new(u.inputs["B"], psep.outputs["Y"])
        v = nt.nodes.new("ShaderNodeMix"); v.data_type = 'FLOAT'
        nt.links.new(v.inputs["Factor"], horiz); nt.links.new(v.inputs["A"], psep.outputs["Z"]); nt.links.new(v.inputs["B"], psep.outputs["Y"])
        comb = nt.nodes.new("ShaderNodeCombineXYZ")
        nt.links.new(comb.inputs["X"], u.outputs["Result"]); nt.links.new(comb.inputs["Y"], v.outputs["Result"])
        brick = nt.nodes.new("ShaderNodeTexBrick")
        brick.offset = 0.5; brick.offset_frequency = 2
        brick.inputs["Scale"].default_value = 1.0
        brick.inputs["Mortar Size"].default_value = 0.004
        brick.inputs["Mortar Smooth"].default_value = 0.6
        brick.inputs["Brick Width"].default_value = panels[0]
        brick.inputs["Row Height"].default_value = panels[1]
        brick.inputs["Color1"].default_value = (1.0, 1.0, 1.0, 1)
        brick.inputs["Color2"].default_value = (0.955, 0.945, 0.93, 1)
        brick.inputs["Bias"].default_value = 0.0
        brick.inputs["Mortar"].default_value = (0.80, 0.76, 0.70, 1)
        nt.links.new(brick.inputs["Vector"], comb.outputs["Vector"])
        base = _mixrgb(nt, 1.0, base, brick.outputs["Color"], 'MULTIPLY')
    nt.links.new(b.inputs["Base Color"], base)
    _set(b, "Roughness", rough); _set(b, "Specular IOR Level", 0.45)
    h = _math(nt, 'SUBTRACT', _math(nt, 'MULTIPLY', layers, 0.3), pits)
    h = _math(nt, 'SUBTRACT', h, _math(nt, 'MULTIPLY', streak, 0.25))
    h = _math(nt, 'ADD', h, _math(nt, 'MULTIPLY', grain, 0.15))
    if panels:
        h = _math(nt, 'SUBTRACT', h, _math(nt, 'MULTIPLY', brick.outputs["Fac"], 1.5))
    _bump(nt, b, h, bump, 0.02)
    if emit > 0:
        nt.links.new(b.inputs["Emission Color"], base); _set(b, "Emission Strength", emit)
    return m


def onyx(name, c1=(1.0, 0.86, 0.58, 1), c2=(0.94, 0.64, 0.26, 1), c3=(0.50, 0.26, 0.08, 1), emit=0.5,
         band_scale=1.0, axis='Z', rough=0.18, vein=0.35, freq=24.0, wobble=0.15):
    """Backlit stratified onyx (photo 10 fireplace pier): many thin sedimentary layers stacked along `axis`, of
    varying thickness, each a slightly different cream / honey / amber tone with a thin dark parting line at its base
    and a soft gradient across it; the boundaries wander (low-frequency warp) and carry fine within-layer streaks.
    `freq` = mean layers per metre, `wobble` = how far (m) the boundaries wander."""
    m, nt, b = _new(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(sep.inputs["Vector"], tc.outputs["Object"])
    along = sep.outputs[axis]
    # boundary warp: a smooth noise (so layers stay continuous) plus a smaller sharper one for the ripples
    warp = _noise(nt, _coords(nt, scale=(0.45 * band_scale,) * 3), scale=1.0, detail=2.0, rough=0.5)
    warp2 = _noise(nt, _coords(nt, scale=(2.2 * band_scale,) * 3), scale=1.0, detail=3.0, rough=0.6)
    # thickness variation: a noise that varies mainly along the stacking axis compresses / expands the layer count
    tsc = {'Z': (0.2, 0.2, 2.2), 'X': (2.2, 0.2, 0.2), 'Y': (0.2, 2.2, 0.2)}[axis]
    thick = _noise(nt, _coords(nt, scale=tuple(band_scale * s for s in tsc)), scale=1.0, detail=2.0, rough=0.5)
    L = _math(nt, 'MULTIPLY', along, freq / band_scale)
    L = _math(nt, 'ADD', L, _math(nt, 'MULTIPLY', _math(nt, 'SUBTRACT', warp, 0.5), wobble * freq))
    L = _math(nt, 'ADD', L, _math(nt, 'MULTIPLY', _math(nt, 'SUBTRACT', thick, 0.5), 0.45 * freq))
    L = _math(nt, 'ADD', L, _math(nt, 'MULTIPLY', _math(nt, 'SUBTRACT', warp2, 0.5), 0.35))
    f = _math(nt, 'FRACT', L)
    lid = _math(nt, 'FLOOR', L)
    wn = nt.nodes.new("ShaderNodeTexWhiteNoise"); wn.noise_dimensions = '1D'
    nt.links.new(wn.inputs["W"], lid)
    wn2 = nt.nodes.new("ShaderNodeTexWhiteNoise"); wn2.noise_dimensions = '1D'
    nt.links.new(wn2.inputs["W"], _math(nt, 'ADD', lid, 37.0))
    # per-layer tone: cream / honey / amber, a few dark brown layers
    tone = _ramp(nt, wn.outputs["Value"], [(0.0, c1), (0.25, (c1[0] * 0.98, c1[1] * 0.92, c1[2] * 0.80, 1)), (0.45, c2), (0.72, c2),
                                            (0.82, (c2[0] * 0.8, c2[1] * 0.7, c2[2] * 0.6, 1)), (0.92, c3), (1.0, c3)])
    # within-layer gradient: brightest just above the parting line, darkening toward the next one
    grad = _ramp(nt, f, [(0.0, (0.70, 0.70, 0.70, 1)), (0.12, (1.06, 1.06, 1.06, 1)), (0.7, (0.96, 0.96, 0.96, 1)), (1.0, (0.78, 0.78, 0.78, 1))])
    base = _mixrgb(nt, 1.0, tone, grad, 'MULTIPLY')
    # thin dark parting line at every boundary (strength varies per layer) + fine streaks inside the layers
    line = _math(nt, 'SUBTRACT', 1.0, _math(nt, 'MULTIPLY', f, 14.0, clamp=True))
    line = _math(nt, 'MULTIPLY', line, _math(nt, 'ADD', 0.3, _math(nt, 'MULTIPLY', wn2.outputs["Value"], 0.7)))
    base = _mixrgb(nt, _math(nt, 'MULTIPLY', line, vein * 2.4, clamp=True), base, (0.28, 0.12, 0.03, 1))
    sc = {'Z': (1, 1, 40), 'X': (40, 1, 1), 'Y': (1, 40, 1)}[axis]
    streak = _noise(nt, _coords(nt, scale=tuple(band_scale * s for s in sc)), scale=1.0, detail=2.0)
    base = _mixrgb(nt, _math(nt, 'MULTIPLY', streak, 0.4), base, (0.78, 0.72, 0.64, 1), 'MULTIPLY')
    nt.links.new(b.inputs["Base Color"], base)
    _set(b, "Roughness", rough); _set(b, "Specular IOR Level", 0.6); _set(b, "Coat Weight", 0.4)
    nt.links.new(b.inputs["Emission Color"], base)
    _set(b, "Emission Strength", emit)
    _bump(nt, b, _math(nt, 'MULTIPLY', line, 0.4), 0.03, 0.005)
    return m


def onyx_crackle(name, ground=(0.96, 0.87, 0.66, 1), honey=(0.90, 0.62, 0.26, 1), vein=(0.45, 0.22, 0.04, 1),
                 river=(0.74, 0.40, 0.09, 1), emit=0.6, scale=1.0, rough=0.10):
    """Backlit crackle onyx (photo 18 bathroom): cream ground with big soft honey clouds, a net of thin dark-amber
    veins (voronoi cell edges on warped coordinates), wide golden 'rivers' wandering through, and darker amber
    pooling along the rivers."""
    m, nt, b = _new(name)
    vec = _coords(nt, scale=(scale,) * 3)
    dn = nt.nodes.new("ShaderNodeTexNoise"); dn.inputs["Scale"].default_value = 1.1; dn.inputs["Detail"].default_value = 3.0
    nt.links.new(dn.inputs["Vector"], vec)
    dv = nt.nodes.new("ShaderNodeVectorMath"); dv.operation = 'MULTIPLY_ADD'; dv.inputs[1].default_value = (0.7, 0.7, 0.7)
    nt.links.new(dv.inputs[0], dn.outputs["Color"]); nt.links.new(dv.inputs[2], vec)
    warped = dv.outputs["Vector"]
    cloud = _stretch(nt, _noise(nt, vec, scale=0.7, detail=3.0, rough=0.5), 0.36, 0.64)
    base = _ramp(nt, cloud, [(0.0, ground), (0.4, (ground[0] * 0.99, ground[1] * 0.93, ground[2] * 0.80, 1)), (0.75, honey), (1.0, (honey[0] * 0.92, honey[1] * 0.82, honey[2] * 0.7, 1))])
    vor = _voronoi(nt, warped, scale=1.15, feature='DISTANCE_TO_EDGE')
    net = _math(nt, 'SUBTRACT', 1.0, _math(nt, 'MULTIPLY', vor.outputs["Distance"], 26.0, clamp=True))
    net = _math(nt, 'MULTIPLY', net, _math(nt, 'ADD', 0.5, _math(nt, 'MULTIPLY', _noise(nt, vec, scale=3.0, detail=2.0), 0.9)), clamp=True)
    vor2 = _voronoi(nt, warped, scale=4.5, feature='DISTANCE_TO_EDGE')
    net2 = _math(nt, 'SUBTRACT', 1.0, _math(nt, 'MULTIPLY', vor2.outputs["Distance"], 45.0, clamp=True))
    net2 = _math(nt, 'MULTIPLY', net2, _math(nt, 'GREATER_THAN', _noise(nt, vec, scale=1.5, detail=2.0), 0.48))
    rn = _noise(nt, vec, scale=0.9, detail=4.0, rough=0.55, distortion=1.6)
    rd = _math(nt, 'ABSOLUTE', _math(nt, 'SUBTRACT', rn, 0.5))
    riv = _math(nt, 'POWER', _math(nt, 'SUBTRACT', 1.0, _math(nt, 'MULTIPLY', rd, 4.5, clamp=True)), 1.6)
    pool = _math(nt, 'POWER', _math(nt, 'SUBTRACT', 1.0, _math(nt, 'MULTIPLY', rd, 2.0, clamp=True)), 1.2)   # broad amber halo
    base = _mixrgb(nt, _math(nt, 'MULTIPLY', pool, 0.5), base, honey)
    base = _mixrgb(nt, _math(nt, 'MULTIPLY', riv, 0.9), base, river)
    base = _mixrgb(nt, _math(nt, 'MULTIPLY', net, 0.7), base, vein)
    base = _mixrgb(nt, _math(nt, 'MULTIPLY', net2, 0.35), base, vein)
    nt.links.new(b.inputs["Base Color"], base)
    _set(b, "Roughness", rough); _set(b, "Specular IOR Level", 0.6); _set(b, "Coat Weight", 0.5); _set(b, "Coat Roughness", 0.04)
    nt.links.new(b.inputs["Emission Color"], base)
    _set(b, "Emission Strength", emit)
    _bump(nt, b, _math(nt, 'ADD', _math(nt, 'MULTIPLY', net, 0.3), _math(nt, 'MULTIPLY', riv, 0.2)), 0.02, 0.004)
    return m


def marble(name, base=(0.93, 0.92, 0.90, 1), vein=(0.55, 0.52, 0.50, 1), vein2=(0.72, 0.66, 0.58, 1),
           scale=0.8, rough=0.12, emit=0.0):
    """Calacatta-style: white ground with wandering grey/gold veins."""
    m, nt, b = _new(name)
    vec = _coords(nt, scale=(scale, scale, scale))
    # primary veins: wide, soft-edged, wandering (photo 12: bold grey rivers with feathered edges)
    n1 = _noise(nt, vec, scale=1.1, detail=5.0, rough=0.55, distortion=2.4)
    v1 = _math(nt, 'ABSOLUTE', _math(nt, 'SUBTRACT', n1, 0.5))
    v1 = _math(nt, 'MULTIPLY', v1, 6.0, clamp=True)
    v1 = _math(nt, 'POWER', v1, 0.45)
    # secondary veins: thin, sharper, branching off at a different scale
    n2 = _noise(nt, vec, scale=3.0, detail=4.0, rough=0.5, distortion=1.4)
    v2 = _math(nt, 'ABSOLUTE', _math(nt, 'SUBTRACT', n2, 0.5))
    v2 = _math(nt, 'MULTIPLY', v2, 20.0, clamp=True)
    v2 = _math(nt, 'MULTIPLY', _math(nt, 'SUBTRACT', 1.0, v2), _math(nt, 'GREATER_THAN', _noise(nt, vec, scale=1.6, detail=2.0), 0.45))
    cloud = _noise(nt, vec, scale=2.0, detail=3.0)
    col = _mixrgb(nt, v1, vein, base)
    col = _mixrgb(nt, _math(nt, 'MULTIPLY', v2, 0.7), col, vein2)
    col = _mixrgb(nt, _math(nt, 'MULTIPLY', cloud, 0.2), col, (0.86, 0.85, 0.83, 1))
    nt.links.new(b.inputs["Base Color"], col)
    _set(b, "Roughness", rough); _set(b, "Specular IOR Level", 0.6); _set(b, "Coat Weight", 0.5); _set(b, "Coat Roughness", 0.05)
    if emit > 0:
        nt.links.new(b.inputs["Emission Color"], col); _set(b, "Emission Strength", emit)
    return m


def plaster(name, base=(0.90, 0.89, 0.86, 1), rough=0.7, grain=0.06):
    m, nt, b = _new(name)
    vec = _coords(nt)
    n = _noise(nt, vec, scale=30.0, detail=3.0)
    col = _mixrgb(nt, grain, base, (base[0] * 0.85, base[1] * 0.85, base[2] * 0.85, 1))
    col2 = _mixrgb(nt, n, col, base)
    nt.links.new(b.inputs["Base Color"], col2)
    _set(b, "Roughness", rough); _set(b, "Specular IOR Level", 0.3)
    _bump(nt, b, n, 0.04, 0.01)
    return m


# ------------------------------------------------------------------ wood
def wood(name, light=(0.74, 0.58, 0.40, 1), dark=(0.52, 0.36, 0.22, 1), grain_axis='Z', scale=1.0, rough=0.45,
         coat=0.15, ring=18.0):
    """Straight-grained timber; grain runs along grain_axis."""
    m, nt, b = _new(name)
    sc = {'Z': (ring, ring, 0.35), 'X': (0.35, ring, ring), 'Y': (ring, 0.35, ring)}[grain_axis]
    vec = _coords(nt, scale=tuple(s * scale for s in sc))
    g = _noise(nt, vec, scale=1.0, detail=4.0, rough=0.6, distortion=0.4)
    fine = _noise(nt, _coords(nt, scale=(80, 80, 80)), scale=1.0, detail=2.0)
    col = _ramp(nt, g, [(0.3, dark), (0.5, light), (0.7, dark), (0.9, light)])
    col = _mixrgb(nt, _math(nt, 'MULTIPLY', fine, 0.15), col, (0.9, 0.86, 0.8, 1), 'MULTIPLY')
    nt.links.new(b.inputs["Base Color"], col)
    _set(b, "Roughness", rough); _set(b, "Specular IOR Level", 0.4); _set(b, "Coat Weight", coat); _set(b, "Coat Roughness", 0.25)
    _bump(nt, b, g, 0.05, 0.005)
    return m


def wood_planks(name, light=(0.88, 0.79, 0.64, 1), dark=(0.74, 0.62, 0.46, 1), plank=(2.4, 0.22), along='X',
                gap=0.003, rough=0.35, coat=0.25):
    """Wide-plank white-oak floor (brick texture for boards + grain noise + per-board tint)."""
    m, nt, b = _new(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(sep.inputs["Vector"], tc.outputs["Object"])
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    a, bb = ('X', 'Y') if along == 'X' else ('Y', 'X')
    nt.links.new(comb.inputs["X"], sep.outputs[a]); nt.links.new(comb.inputs["Y"], sep.outputs[bb])
    brick = nt.nodes.new("ShaderNodeTexBrick")
    brick.offset = 0.5; brick.offset_frequency = 2
    brick.inputs["Scale"].default_value = 1.0
    brick.inputs["Mortar Size"].default_value = gap
    brick.inputs["Mortar Smooth"].default_value = 0.2
    brick.inputs["Brick Width"].default_value = plank[0]
    brick.inputs["Row Height"].default_value = plank[1]
    brick.inputs["Color1"].default_value = (1, 1, 1, 1)
    brick.inputs["Color2"].default_value = (0.95, 0.94, 0.92, 1)
    brick.inputs["Mortar"].default_value = (0.60, 0.53, 0.44, 1)
    nt.links.new(brick.inputs["Vector"], comb.outputs["Vector"])
    sc = (0.5, 40, 40) if along == 'X' else (40, 0.5, 40)
    g = _stretch(nt, _noise(nt, _coords(nt, scale=sc), scale=1.0, detail=4.0, rough=0.6, distortion=0.3), 0.35, 0.65)
    col = _ramp(nt, g, [(0.1, dark), (0.4, light), (0.6, light), (0.9, dark)])
    col = _mixrgb(nt, 1.0, col, brick.outputs["Color"], 'MULTIPLY')
    nt.links.new(b.inputs["Base Color"], col)
    _set(b, "Roughness", rough); _set(b, "Specular IOR Level", 0.45); _set(b, "Coat Weight", coat); _set(b, "Coat Roughness", 0.2)
    _bump(nt, b, brick.outputs["Fac"], 0.15, 0.004)
    return m


def wave_wood(name):
    """The entry door (photos 02/05): vertical staves of blonde maple and dark walnut whose edges are cut as tall,
    tapering flames - each stave a flame that narrows toward the top or bottom - plus the stave joints and grain."""
    m, nt, b = _new(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(sep.inputs["Vector"], tc.outputs["Object"])
    # a horizontal coordinate that bends with height: x + a(z) where a is a smooth, very low-frequency noise of z.
    # Thresholding the fract of the bent coordinate gives light/dark strips whose width changes with height (flames).
    bend = _noise(nt, _coords(nt, scale=(0.15, 0.15, 0.55)), scale=1.0, detail=2.0, rough=0.5)
    bend2 = _noise(nt, _coords(nt, scale=(0.4, 0.4, 1.1), loc=(3.0, 1.0, 0.0)), scale=1.0, detail=2.0, rough=0.5)
    u = _math(nt, 'ADD', _math(nt, 'MULTIPLY', sep.outputs["X"], 3.6), _math(nt, 'MULTIPLY', _math(nt, 'SUBTRACT', bend, 0.5), 2.4))
    u = _math(nt, 'ADD', u, _math(nt, 'MULTIPLY', _math(nt, 'SUBTRACT', bend2, 0.5), 0.6))
    f = _math(nt, 'FRACT', u)
    sid = _math(nt, 'FLOOR', u)
    # flame taper: each strip's light part is wide at some heights and pinches to a point at others; the pattern is
    # a strongly contrast-stretched noise of (strip id, z) so neighbouring strips taper at different heights
    wc = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(wc.inputs["X"], _math(nt, 'MULTIPLY', sid, 0.37)); nt.links.new(wc.inputs["Z"], _math(nt, 'MULTIPLY', sep.outputs["Z"], 0.55))
    wvar = _stretch(nt, _noise(nt, wc.outputs["Vector"], scale=1.0, detail=1.0), 0.36, 0.64)
    width = _math(nt, 'ADD', 0.04, _math(nt, 'MULTIPLY', wvar, 0.92))
    dark = _math(nt, 'GREATER_THAN', f, width)
    grain = _noise(nt, _coords(nt, scale=(25.0, 25.0, 0.6)), scale=1.0, detail=3.0, rough=0.6)
    light_col = _ramp(nt, grain, [(0.3, (0.86, 0.70, 0.46, 1)), (0.7, (0.93, 0.80, 0.56, 1))])
    dark_col = _ramp(nt, grain, [(0.3, (0.36, 0.20, 0.10, 1)), (0.7, (0.50, 0.30, 0.15, 1))])
    col = _mixrgb(nt, dark, light_col, dark_col)
    # 110 mm stave joints (thin dark lines) - the flames are cut across several staves
    jx = _math(nt, 'FRACT', _math(nt, 'DIVIDE', sep.outputs["X"], 0.11))
    joint = _math(nt, 'LESS_THAN', _math(nt, 'ABSOLUTE', _math(nt, 'SUBTRACT', jx, 0.5)), 0.012)
    col = _mixrgb(nt, _math(nt, 'MULTIPLY', joint, 0.6), col, (0.25, 0.15, 0.08, 1))
    nt.links.new(b.inputs["Base Color"], col)
    _set(b, "Roughness", 0.38); _set(b, "Coat Weight", 0.35); _set(b, "Coat Roughness", 0.2)
    _bump(nt, b, _math(nt, 'ADD', _math(nt, 'MULTIPLY', grain, 0.3), _math(nt, 'MULTIPLY', joint, 0.8)), 0.05, 0.004)
    return m


# ------------------------------------------------------------------ tiles / paving
def tiles(name, base, grout=(0.4, 0.38, 0.35, 1), size=(0.9, 0.9), gap=0.006, rough=0.5, plane='XY',
          variation=0.08, mottle=0.3, bump=0.3, offset=0.0, coat=0.0):
    m, nt, b = _new(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(sep.inputs["Vector"], tc.outputs["Object"])
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    a, bb = {'XY': ('X', 'Y'), 'XZ': ('X', 'Z'), 'YZ': ('Y', 'Z')}[plane]
    nt.links.new(comb.inputs["X"], sep.outputs[a]); nt.links.new(comb.inputs["Y"], sep.outputs[bb])
    brick = nt.nodes.new("ShaderNodeTexBrick")
    brick.offset = offset
    brick.inputs["Scale"].default_value = 1.0
    brick.inputs["Mortar Size"].default_value = gap
    brick.inputs["Mortar Smooth"].default_value = 0.3
    brick.inputs["Brick Width"].default_value = size[0]
    brick.inputs["Row Height"].default_value = size[1]
    brick.inputs["Color1"].default_value = base
    brick.inputs["Color2"].default_value = tuple(min(1, c * (1 - variation)) for c in base[:3]) + (1,)
    brick.inputs["Mortar"].default_value = grout
    nt.links.new(brick.inputs["Vector"], comb.outputs["Vector"])
    n = _noise(nt, tc.outputs["Object"], scale=5.0, detail=5.0)
    col = _mixrgb(nt, mottle, brick.outputs["Color"], _ramp(nt, n, [(0, (0.72, 0.72, 0.72, 1)), (1, (1, 1, 1, 1))]), 'MULTIPLY')
    nt.links.new(b.inputs["Base Color"], col)
    _set(b, "Roughness", rough); _set(b, "Specular IOR Level", 0.4); _set(b, "Coat Weight", coat)
    _bump(nt, b, brick.outputs["Fac"], bump, 0.01)
    return m


def noise_mat(name, c1, c2, scale=8.0, rough=0.9, bump=0.3, detail=8.0, spec=0.3, bump_dist=0.05):
    m, nt, b = _new(name)
    vec = _coords(nt)
    n = _noise(nt, vec, scale=scale, detail=detail, rough=0.7)
    col = _ramp(nt, n, [(0.3, c1), (0.7, c2)])
    nt.links.new(b.inputs["Base Color"], col)
    _set(b, "Roughness", rough); _set(b, "Specular IOR Level", spec)
    if bump:
        _bump(nt, b, n, bump, bump_dist)
    return m


def turf(name, c_dark=(0.10, 0.27, 0.06, 1), c_light=(0.24, 0.44, 0.12, 1), stripes=False, stripe_axis='X', stripe_w=0.42):
    """Synthetic-lawn look: fine fibre noise + broad mottling (+ optional mowing stripes)."""
    m, nt, b = _new(name)
    vec = _coords(nt)
    fine = _noise(nt, vec, scale=120.0, detail=2.0, rough=0.5)
    broad = _noise(nt, vec, scale=1.2, detail=4.0)
    col = _ramp(nt, fine, [(0.3, c_dark), (0.7, c_light)])
    col = _mixrgb(nt, _math(nt, 'MULTIPLY', broad, 0.35), col, (0.8, 0.82, 0.7, 1), 'MULTIPLY')
    if stripes:
        wave = nt.nodes.new("ShaderNodeTexWave"); wave.wave_type = 'BANDS'; wave.bands_direction = stripe_axis
        wave.wave_profile = 'SAW'; wave.inputs["Scale"].default_value = stripe_w
        wave.inputs["Distortion"].default_value = 0.0; wave.inputs["Detail"].default_value = 0.0
        nt.links.new(wave.inputs["Vector"], vec)
        st = _ramp(nt, wave.outputs["Fac"], [(0, (0.82, 0.82, 0.82, 1)), (1, (1.08, 1.08, 1.08, 1))])
        col = _mixrgb(nt, 1.0, col, st, 'MULTIPLY')
    nt.links.new(b.inputs["Base Color"], col)
    _set(b, "Roughness", 0.95); _set(b, "Specular IOR Level", 0.1); _set(b, "Sheen Weight", 0.08)
    _bump(nt, b, fine, 0.5, 0.01)
    return m


def moss(name):
    """Preserved-moss art wall: patchwork of lime / olive / deep-green clumps, very matte, strong relief."""
    m, nt, b = _new(name)
    vec = _coords(nt)
    # distort the cell lookup with low-frequency noise so patches get organic edges
    dn = nt.nodes.new("ShaderNodeTexNoise"); dn.inputs["Scale"].default_value = 1.5; dn.inputs["Detail"].default_value = 3.0
    nt.links.new(dn.inputs["Vector"], vec)
    dv = nt.nodes.new("ShaderNodeVectorMath"); dv.operation = 'MULTIPLY_ADD'
    dv.inputs[1].default_value = (0.9, 0.9, 0.9)
    nt.links.new(dv.inputs[0], dn.outputs["Color"]); nt.links.new(dv.inputs[2], vec)
    vor = _voronoi(nt, dv.outputs["Vector"], scale=2.2, feature='F1', rand=1.0)
    cellcol = vor.outputs["Color"]
    sepc = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(sepc.inputs["Color"], cellcol)
    patch = sepc.outputs["Red"]
    n1 = _noise(nt, vec, scale=7.0, detail=6.0, rough=0.7)
    n2 = _noise(nt, vec, scale=45.0, detail=3.0)
    f = _math(nt, 'ADD', _math(nt, 'MULTIPLY', patch, 0.7), _math(nt, 'MULTIPLY', n1, 0.45))
    col = _ramp(nt, f, [(0.15, (0.04, 0.14, 0.03, 1)), (0.38, (0.16, 0.36, 0.05, 1)), (0.55, (0.38, 0.55, 0.08, 1)), (0.72, (0.62, 0.74, 0.14, 1)), (0.9, (0.82, 0.86, 0.30, 1))])
    col = _mixrgb(nt, _math(nt, 'MULTIPLY', n2, 0.35), col, (0.65, 0.7, 0.55, 1), 'MULTIPLY')
    nt.links.new(b.inputs["Base Color"], col)
    _set(b, "Roughness", 1.0); _set(b, "Specular IOR Level", 0.05); _set(b, "Subsurface Weight", 0.2)
    _bump(nt, b, _math(nt, 'ADD', _math(nt, 'MULTIPLY', n1, 0.7), _math(nt, 'MULTIPLY', n2, 0.5)), 1.0, 0.05)
    return m


def foliage(name, c1, c2, translucent=0.35, rough=0.8, c3=None):
    m, nt, b = _new(name)
    vec = _coords(nt)
    n = _noise(nt, vec, scale=3.0, detail=4.0)
    n2 = _noise(nt, vec, scale=25.0, detail=2.0)
    stops = [(0.3, c1), (0.7, c2)] if c3 is None else [(0.25, c1), (0.55, c2), (0.85, c3)]
    col = _ramp(nt, n, stops)
    col = _mixrgb(nt, _math(nt, 'MULTIPLY', n2, 0.35), col, (0.75, 0.8, 0.6, 1), 'MULTIPLY')
    nt.links.new(b.inputs["Base Color"], col)
    _set(b, "Roughness", rough); _set(b, "Specular IOR Level", 0.25)
    tr = nt.nodes.new("ShaderNodeBsdfTranslucent"); nt.links.new(tr.inputs["Color"], col)
    mix = nt.nodes.new("ShaderNodeMixShader"); mix.inputs["Fac"].default_value = translucent
    out = nt.nodes["Material Output"]
    nt.links.new(mix.inputs[1], b.outputs["BSDF"]); nt.links.new(mix.inputs[2], tr.outputs["BSDF"])
    nt.links.new(out.inputs["Surface"], mix.outputs["Shader"])
    _bump(nt, b, n2, 0.3, 0.02)
    return m


def fabric(name, base, rough=0.95, sheen=0.6, weave=60.0, bump=0.25, sheen_tint=(1, 1, 1, 1)):
    """Boucle / linen upholstery: fine weave bump + sheen."""
    m, nt, b = _new(name)
    vec = _coords(nt)
    w = _noise(nt, vec, scale=weave, detail=2.0, rough=0.5)
    n = _noise(nt, vec, scale=4.0, detail=3.0)
    col = _mixrgb(nt, _math(nt, 'MULTIPLY', n, 0.12), base, (0.85, 0.85, 0.85, 1), 'MULTIPLY')
    nt.links.new(b.inputs["Base Color"], col)
    _set(b, "Roughness", rough); _set(b, "Specular IOR Level", 0.2); _set(b, "Sheen Weight", sheen); _set(b, "Sheen Tint", sheen_tint)
    _bump(nt, b, w, bump, 0.003)
    return m


def water(name, tint=(0.62, 0.90, 0.96, 1), density=0.20, ripple=0.06, scatter=0.0, scatter_col=(0.55, 0.85, 1.0, 1)):
    """Pool water: a glass-like refractive surface (ripples on the top face only) over a coloured absorbing volume,
    optionally with a little scattering so underwater lights make the water glow milky-blue (photo 24)."""
    m = new_mat(name, base=(0.9, 0.97, 0.98, 1), rough=0.0, transmission=1.0, ior=1.333, spec=0.5)
    nt, b = m.node_tree, _bsdf(m)
    vec = _coords(nt)
    # gentle wind ripples: two crossed low-frequency wave trains + a little noise (not a boiling noise field)
    w1 = nt.nodes.new("ShaderNodeTexWave"); w1.wave_type = 'BANDS'; w1.bands_direction = 'DIAGONAL'; w1.wave_profile = 'SIN'
    w1.inputs["Scale"].default_value = 3.0; w1.inputs["Distortion"].default_value = 2.5; w1.inputs["Detail"].default_value = 3.0
    w1.inputs["Detail Scale"].default_value = 2.0
    nt.links.new(w1.inputs["Vector"], vec)
    w2 = nt.nodes.new("ShaderNodeTexWave"); w2.wave_type = 'BANDS'; w2.bands_direction = 'X'; w2.wave_profile = 'SIN'
    w2.inputs["Scale"].default_value = 5.0; w2.inputs["Distortion"].default_value = 3.0; w2.inputs["Detail"].default_value = 2.0
    nt.links.new(w2.inputs["Vector"], _coords(nt, rot=(0, 0, 0.6)))
    n2 = _noise(nt, vec, scale=7.0, detail=3.0, rough=0.5)
    h = _math(nt, 'ADD', _math(nt, 'MULTIPLY', w1.outputs["Fac"], 0.6), _math(nt, 'MULTIPLY', w2.outputs["Fac"], 0.3))
    h = _math(nt, 'ADD', h, _math(nt, 'MULTIPLY', n2, 0.25))
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    nsep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(nsep.inputs["Vector"], geo.outputs["True Normal"])
    top = _math(nt, 'GREATER_THAN', _math(nt, 'ABSOLUTE', nsep.outputs["Z"]), 0.7)
    bp = _bump(nt, b, h, ripple, 0.05)
    nt.links.new(bp.inputs["Strength"], _math(nt, 'MULTIPLY', top, ripple))
    _set(b, "Roughness", 0.01)
    vol = nt.nodes.new("ShaderNodeVolumeAbsorption")
    vol.inputs["Color"].default_value = tint
    vol.inputs["Density"].default_value = density
    vout = vol.outputs["Volume"]
    if scatter > 0:
        sc = nt.nodes.new("ShaderNodeVolumeScatter")
        sc.inputs["Color"].default_value = scatter_col
        sc.inputs["Density"].default_value = scatter
        sc.inputs["Anisotropy"].default_value = 0.35
        add = nt.nodes.new("ShaderNodeAddShader")
        nt.links.new(add.inputs[0], vout); nt.links.new(add.inputs[1], sc.outputs["Volume"])
        vout = add.outputs["Shader"]
    nt.links.new(nt.nodes["Material Output"].inputs["Volume"], vout)
    return m


def perforated(name, axis='X', pitch=0.115, hole=0.058, z0=6.01, rows=3, base=(0.93, 0.92, 0.89, 1), stagger=True):
    """White powder-coated fascia panel with `rows` rows of small round perforations (photos 01/22: a fine dot
    pattern, not big squares) along `axis`; alternate rows are staggered by half a pitch."""
    m, nt, b = _new(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(sep.inputs["Vector"], tc.outputs["Object"])
    zc = _math(nt, 'DIVIDE', _math(nt, 'SUBTRACT', sep.outputs['Z'], z0), pitch)
    row = _math(nt, 'FLOOR', zc)
    fz = _math(nt, 'SUBTRACT', _math(nt, 'FRACT', zc), 0.5)
    uc = _math(nt, 'DIVIDE', sep.outputs[axis], pitch)
    if stagger:
        uc = _math(nt, 'ADD', uc, _math(nt, 'MULTIPLY', _math(nt, 'FRACT', _math(nt, 'MULTIPLY', row, 0.5)), 1.0))
    fu = _math(nt, 'SUBTRACT', _math(nt, 'FRACT', uc), 0.5)
    r2 = _math(nt, 'ADD', _math(nt, 'MULTIPLY', fu, fu), _math(nt, 'MULTIPLY', fz, fz))
    rr = (hole / pitch / 2) ** 2
    g = _math(nt, 'LESS_THAN', r2, rr)
    g = _math(nt, 'MULTIPLY', g, _math(nt, 'LESS_THAN', sep.outputs['Z'], z0 + rows * pitch))
    g = _math(nt, 'MULTIPLY', g, _math(nt, 'GREATER_THAN', sep.outputs['Z'], z0))
    col = _mixrgb(nt, g, base, (0.03, 0.03, 0.03, 1))
    nt.links.new(b.inputs["Base Color"], col)
    _set(b, "Roughness", 0.4); _set(b, "Metallic", 0.0); _set(b, "Specular IOR Level", 0.5)
    _bump(nt, b, _math(nt, 'SUBTRACT', 1.0, g), 0.8, 0.008)
    return m


def fire(name):
    m, nt, b = _new(name)
    nt.nodes.remove(b)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(sep.inputs["Vector"], tc.outputs["Generated"])
    col = _ramp(nt, sep.outputs["Z"], [(0.0, (1.0, 0.50, 0.10, 1)), (0.45, (1.0, 0.30, 0.03, 1)), (1.0, (0.85, 0.10, 0.02, 1))])
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Strength"].default_value = 1.4
    nt.links.new(em.inputs["Color"], col)
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    fade = _math(nt, 'POWER', sep.outputs["Z"], 1.5)
    nt.links.new(mix.inputs["Fac"], fade)
    nt.links.new(mix.inputs[1], em.outputs["Emission"]); nt.links.new(mix.inputs[2], tr.outputs["BSDF"])
    nt.links.new(nt.nodes["Material Output"].inputs["Surface"], mix.outputs["Shader"])
    m.blend_method = 'BLEND'
    return m


def leather(name, base=(0.93, 0.92, 0.88, 1), rough=0.45):
    m, nt, b = _new(name)
    vec = _coords(nt)
    n = _noise(nt, vec, scale=90.0, detail=2.0)
    nt.links.new(b.inputs["Base Color"], _mixrgb(nt, _math(nt, 'MULTIPLY', n, 0.08), base, (0.8, 0.8, 0.8, 1), 'MULTIPLY'))
    _set(b, "Roughness", rough); _set(b, "Specular IOR Level", 0.5); _set(b, "Coat Weight", 0.2); _set(b, "Coat Roughness", 0.35)
    _bump(nt, b, n, 0.12, 0.002)
    return m


def rug(name, c1, c2, scale=25.0, pattern=False):
    m, nt, b = _new(name)
    vec = _coords(nt)
    n = _noise(nt, vec, scale=scale, detail=4.0)
    col = _ramp(nt, n, [(0.3, c1), (0.7, c2)])
    if pattern:
        p = _noise(nt, vec, scale=0.9, detail=2.0, distortion=1.0)
        col = _mixrgb(nt, _math(nt, 'MULTIPLY', _math(nt, 'GREATER_THAN', p, 0.52), 0.35), col, (1.15, 1.15, 1.15, 1), 'MULTIPLY')
    nt.links.new(b.inputs["Base Color"], col)
    _set(b, "Roughness", 1.0); _set(b, "Specular IOR Level", 0.1); _set(b, "Sheen Weight", 0.8)
    _bump(nt, b, n, 0.6, 0.01)
    return m


def art_stripes(name):
    m, nt, b = _new(name)
    vec = _coords(nt)
    wave = nt.nodes.new("ShaderNodeTexWave"); wave.wave_type = 'BANDS'; wave.bands_direction = 'Z'
    wave.inputs["Scale"].default_value = 18.0; wave.inputs["Distortion"].default_value = 1.2; wave.inputs["Detail"].default_value = 1.0
    nt.links.new(wave.inputs["Vector"], vec)
    col = _ramp(nt, wave.outputs["Fac"], [(0.0, (0.05, 0.35, 0.6, 1)), (0.3, (0.95, 0.6, 0.1, 1)), (0.55, (0.85, 0.15, 0.2, 1)), (0.8, (0.2, 0.6, 0.3, 1)), (1.0, (0.95, 0.9, 0.3, 1))])
    nt.links.new(b.inputs["Base Color"], col)
    _set(b, "Roughness", 0.7)
    return m


def art_abstract(name, bg=(0.92, 0.88, 0.80, 1), fg=(0.12, 0.10, 0.09, 1), scale=3.0, thresh=0.58):
    m, nt, b = _new(name)
    vec = _coords(nt)
    n = _noise(nt, vec, scale=scale, detail=3.0, distortion=1.6)
    f = _math(nt, 'GREATER_THAN', n, thresh)
    col = _mixrgb(nt, f, bg, fg)
    nt.links.new(b.inputs["Base Color"], col)
    _set(b, "Roughness", 0.8)
    return m


def art_dots(name, bg=(0.93, 0.92, 0.88, 1), fg=(0.55, 0.52, 0.22, 1)):
    """Olive rounded-square print (guest room)."""
    m, nt, b = _new(name)
    vec = _coords(nt, scale=(9, 9, 9))
    vor = _voronoi(nt, vec, scale=1.0, feature='F1', rand=0.0)
    vor.distance = 'CHEBYCHEV'
    f = _math(nt, 'LESS_THAN', vor.outputs["Distance"], 0.36)
    col = _mixrgb(nt, f, bg, fg)
    nt.links.new(b.inputs["Base Color"], col)
    _set(b, "Roughness", 0.85)
    return m


def screen_image(name):
    """Cinema screen: warm cloud-sky gradient (an actual movie frame, stylised)."""
    m, nt, b = _new(name)
    vec = _coords(nt)
    n = _noise(nt, vec, scale=2.5, detail=6.0)
    col = _ramp(nt, n, [(0.3, (0.25, 0.22, 0.30, 1)), (0.5, (0.85, 0.65, 0.40, 1)), (0.7, (1.0, 0.92, 0.75, 1))])
    nt.links.new(b.inputs["Base Color"], col)
    nt.links.new(b.inputs["Emission Color"], col)
    _set(b, "Emission Strength", 1.8); _set(b, "Roughness", 0.9)
    return m


def grass_blade(name, root=(0.06, 0.18, 0.03, 1), tip=(0.42, 0.62, 0.16, 1), dry=(0.55, 0.52, 0.22, 1), stripes=True, stripe_axis='X', stripe_w=0.42):
    """Hair-strand grass: dark at the root, lighter at the tip, a few dry blades, mowing stripes from the root position."""
    m, nt, b = _new(name)
    hi = nt.nodes.new("ShaderNodeHairInfo")
    col = _ramp(nt, hi.outputs["Intercept"], [(0.0, root), (0.55, (tip[0] * 0.7, tip[1] * 0.8, tip[2] * 0.6, 1)), (1.0, tip)])
    dryf = _math(nt, 'GREATER_THAN', hi.outputs["Random"], 0.88)
    col = _mixrgb(nt, dryf, col, dry)
    vec = _coords(nt)
    patch = _noise(nt, vec, scale=0.7, detail=3.0)
    col = _mixrgb(nt, _math(nt, 'MULTIPLY', patch, 0.35), col, (0.78, 0.85, 0.65, 1), 'MULTIPLY')
    if stripes:
        wave = nt.nodes.new("ShaderNodeTexWave"); wave.wave_type = 'BANDS'; wave.bands_direction = stripe_axis
        wave.wave_profile = 'SAW'; wave.inputs["Scale"].default_value = stripe_w
        wave.inputs["Distortion"].default_value = 0.0; wave.inputs["Detail"].default_value = 0.0
        nt.links.new(wave.inputs["Vector"], vec)
        st = _ramp(nt, wave.outputs["Fac"], [(0, (0.84, 0.84, 0.84, 1)), (1, (1.08, 1.08, 1.08, 1))])
        col = _mixrgb(nt, 1.0, col, st, 'MULTIPLY')
    nt.links.new(b.inputs["Base Color"], col)
    _set(b, "Roughness", 0.55); _set(b, "Specular IOR Level", 0.35); _set(b, "Coat Weight", 0.15)
    tr = nt.nodes.new("ShaderNodeBsdfTranslucent"); nt.links.new(tr.inputs["Color"], col)
    mix = nt.nodes.new("ShaderNodeMixShader"); mix.inputs["Fac"].default_value = 0.3
    nt.links.new(mix.inputs[1], b.outputs["BSDF"]); nt.links.new(mix.inputs[2], tr.outputs["BSDF"])
    nt.links.new(nt.nodes["Material Output"].inputs["Surface"], mix.outputs["Shader"])
    return m


def leaf_card(name, c1=(0.06, 0.16, 0.04, 1), c2=(0.16, 0.32, 0.08, 1), c3=(0.30, 0.44, 0.12, 1), translucent=0.4, shape='oval', rough=0.5):
    """Alpha-cut leaf on a unit quad (UV 0..1): an oval / lanceolate outline, mid-rib, per-instance colour variation."""
    m, nt, b = _new(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(sep.inputs["Vector"], tc.outputs["UV"])
    u = _math(nt, 'SUBTRACT', sep.outputs["X"], 0.5)
    v = _math(nt, 'SUBTRACT', sep.outputs["Y"], 0.5)
    if shape == 'oval':
        r2 = _math(nt, 'ADD', _math(nt, 'MULTIPLY', _math(nt, 'MULTIPLY', u, u), 4.0), _math(nt, 'MULTIPLY', _math(nt, 'MULTIPLY', v, v), 4.0))
    elif shape == 'needle':   # a spray of needles: a fan of thin radial strokes inside the disc
        ang = nt.nodes.new("ShaderNodeMath"); ang.operation = 'ARCTAN2'
        nt.links.new(ang.inputs[0], v); nt.links.new(ang.inputs[1], u)
        spokes = _math(nt, 'FRACT', _math(nt, 'MULTIPLY', ang.outputs[0], 14.0 / (2 * math.pi)))
        spoke_mask = _math(nt, 'LESS_THAN', _math(nt, 'ABSOLUTE', _math(nt, 'SUBTRACT', spokes, 0.5)), 0.16)
        r2 = _math(nt, 'ADD', _math(nt, 'MULTIPLY', _math(nt, 'MULTIPLY', u, u), 4.0), _math(nt, 'MULTIPLY', _math(nt, 'MULTIPLY', v, v), 4.0))
        r2 = _math(nt, 'ADD', r2, _math(nt, 'MULTIPLY', _math(nt, 'SUBTRACT', 1.0, spoke_mask), 3.0))
    elif shape == 'cluster':   # a loose cluster of ~12-20 small overlapping leaves with sky showing between them
        r2 = _math(nt, 'ADD', _math(nt, 'MULTIPLY', _math(nt, 'MULTIPLY', u, u), 4.0), _math(nt, 'MULTIPLY', _math(nt, 'MULTIPLY', v, v), 4.0))
    else:   # lanceolate: narrow ellipse pinched toward the tip
        r2 = _math(nt, 'ADD', _math(nt, 'MULTIPLY', _math(nt, 'MULTIPLY', u, u), 9.0), _math(nt, 'MULTIPLY', _math(nt, 'MULTIPLY', v, v), 4.0))
    # ragged edge: modulate the outline with UV noise (reads as a small cluster of leaves rather than one disc)
    uvn = nt.nodes.new("ShaderNodeTexNoise"); uvn.inputs["Scale"].default_value = 7.0; uvn.inputs["Detail"].default_value = 2.0
    nt.links.new(uvn.inputs["Vector"], tc.outputs["UV"])
    r2 = _math(nt, 'ADD', r2, _math(nt, 'MULTIPLY', _math(nt, 'SUBTRACT', uvn.outputs["Fac"], 0.5), 1.4 if shape != 'needle' else 0.4))
    alpha = _math(nt, 'LESS_THAN', r2, 1.0)
    oi = nt.nodes.new("ShaderNodeObjectInfo")
    rnd = oi.outputs["Random"]
    col = _ramp(nt, rnd, [(0.0, c1), (0.5, c2), (1.0, c3)])
    rib = _math(nt, 'LESS_THAN', _math(nt, 'ABSOLUTE', u), 0.03)
    col = _mixrgb(nt, _math(nt, 'MULTIPLY', rib, 0.5), col, (0.55, 0.6, 0.3, 1))
    if shape == 'cluster':
        # individual leaves = discs around voronoi cell centres in UV space (each cell its own tint), only inside
        # the cluster outline; leaves get a slightly darker rim + a paler mid-rib so they read as leaves, not dots
        uvm = nt.nodes.new("ShaderNodeMapping"); uvm.inputs["Scale"].default_value = (4.2, 4.2, 1.0)
        nt.links.new(uvm.inputs["Vector"], tc.outputs["UV"])
        cv = nt.nodes.new("ShaderNodeTexVoronoi"); cv.voronoi_dimensions = '2D'; cv.feature = 'F1'
        cv.inputs["Scale"].default_value = 1.0; cv.inputs["Randomness"].default_value = 1.0
        nt.links.new(cv.inputs["Vector"], uvm.outputs["Vector"])
        leaf = _math(nt, 'LESS_THAN', cv.outputs["Distance"], 0.46)
        alpha = _math(nt, 'MULTIPLY', alpha, leaf)
        csep = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(csep.inputs["Color"], cv.outputs["Color"])
        tint = _ramp(nt, csep.outputs["Red"], [(0.0, (0.80, 0.85, 0.75, 1)), (0.5, (1.0, 1.0, 1.0, 1)), (1.0, (1.15, 1.12, 0.95, 1))])
        col = _mixrgb(nt, 1.0, col, tint, 'MULTIPLY')
        rim = _ramp(nt, cv.outputs["Distance"], [(0.30, (1.0, 1.0, 1.0, 1)), (0.46, (0.70, 0.72, 0.65, 1))])
        col = _mixrgb(nt, 1.0, col, rim, 'MULTIPLY')
    nt.links.new(b.inputs["Base Color"], col)
    nt.links.new(b.inputs["Alpha"], alpha)
    _set(b, "Roughness", rough); _set(b, "Specular IOR Level", 0.4); _set(b, "Coat Weight", 0.1)
    tr = nt.nodes.new("ShaderNodeBsdfTranslucent"); nt.links.new(tr.inputs["Color"], col)
    mixs = nt.nodes.new("ShaderNodeMixShader"); mixs.inputs["Fac"].default_value = translucent
    nt.links.new(mixs.inputs[1], b.outputs["BSDF"]); nt.links.new(mixs.inputs[2], tr.outputs["BSDF"])
    trans = nt.nodes.new("ShaderNodeBsdfTransparent")
    mixa = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(mixa.inputs["Fac"], alpha)
    nt.links.new(mixa.inputs[1], trans.outputs["BSDF"]); nt.links.new(mixa.inputs[2], mixs.outputs["Shader"])
    nt.links.new(nt.nodes["Material Output"].inputs["Surface"], mixa.outputs["Shader"])
    return m


def linen(name, base=(0.95, 0.94, 0.91, 1), rough=0.9, wrinkle=0.35):
    """Bed linen: fine weave + soft large-scale wrinkles in the normal."""
    m, nt, b = _new(name)
    vec = _coords(nt)
    w = _noise(nt, vec, scale=140.0, detail=2.0)
    wr = _noise(nt, vec, scale=6.0, detail=4.0, rough=0.6, distortion=0.8)
    n = _noise(nt, vec, scale=3.0, detail=3.0)
    col = _mixrgb(nt, _math(nt, 'MULTIPLY', n, 0.08), base, (0.85, 0.85, 0.85, 1), 'MULTIPLY')
    nt.links.new(b.inputs["Base Color"], col)
    _set(b, "Roughness", rough); _set(b, "Specular IOR Level", 0.2); _set(b, "Sheen Weight", 0.4)
    h = _math(nt, 'ADD', _math(nt, 'MULTIPLY', w, 0.15), _math(nt, 'MULTIPLY', wr, wrinkle))
    _bump(nt, b, h, 0.35, 0.02)
    return m


# ------------------------------------------------------------------ the library
def build_materials(perf_z0=6.01):
    """The default palette.  perf_z0: z of the first hole row of the perforated fascia materials (soffit + 0.11)."""
    M = {}
    # stone
    M['trav'] = travertine("Travertine")
    M['trav_warm'] = travertine("TravertineWarm", light=(0.80, 0.70, 0.55, 1), mid=(0.68, 0.57, 0.43, 1), dark=(0.50, 0.40, 0.29, 1))
    M['trav_grey'] = travertine("TravertineGrey", light=(0.78, 0.74, 0.68, 1), mid=(0.64, 0.60, 0.54, 1), dark=(0.46, 0.42, 0.37, 1), pit=0.3)
    M['trav_int'] = travertine("TravertineInt", light=(0.84, 0.78, 0.68, 1), mid=(0.72, 0.65, 0.54, 1), dark=(0.55, 0.48, 0.38, 1), pit=0.3, rough=0.35)
    M['onyx'] = onyx("OnyxAmber")
    M['onyx_dim'] = onyx("OnyxAmberDim", emit=0.25)
    M['onyx_wine'] = onyx("OnyxWine", c1=(1.0, 0.84, 0.54, 1), c2=(0.92, 0.58, 0.22, 1), c3=(0.55, 0.28, 0.08, 1), emit=1.0, freq=6.0)
    M['onyx_bath'] = onyx_crackle("OnyxBath")
    M['onyx_bath_floor'] = onyx_crackle("OnyxBathFloor", emit=0.45, scale=0.8, rough=0.08)
    M['salt'] = onyx("HimalayanSalt", c1=(1.0, 0.62, 0.42, 1), c2=(0.96, 0.40, 0.22, 1), c3=(0.70, 0.20, 0.08, 1), emit=1.6, axis='Y', vein=0.2, freq=9.0, wobble=0.5)
    M['marble'] = marble("Calacatta")
    M['marble_dark'] = marble("CalacattaViola", base=(0.90, 0.88, 0.86, 1), vein=(0.42, 0.30, 0.32, 1), vein2=(0.65, 0.55, 0.5, 1), scale=1.4)
    M['white'] = plaster("WhitePlaster")
    M['white_int'] = plaster("WhiteInterior", base=(0.93, 0.92, 0.89, 1), rough=0.75, grain=0.03)
    M['white_gloss'] = new_mat("WhiteGloss", (0.94, 0.94, 0.92, 1), rough=0.25, spec=0.5, coat=0.6)
    M['ceiling'] = new_mat("Ceiling", (0.95, 0.94, 0.92, 1), rough=0.85, spec=0.2)
    M['gravel'] = noise_mat("GravelRoof", (0.62, 0.61, 0.58, 1), (0.85, 0.84, 0.80, 1), scale=60, bump=0.6, detail=4, bump_dist=0.02)
    M['concrete'] = noise_mat("Concrete", (0.52, 0.51, 0.49, 1), (0.66, 0.65, 0.62, 1), scale=8, bump=0.1, rough=0.8)
    # glass + metal
    M['glass'] = new_mat("Glass", (0.95, 0.98, 0.97, 1), rough=0.0, transmission=1.0, ior=1.5, spec=0.5)
    M['glass_tint'] = new_mat("GlassTint", (0.78, 0.88, 0.87, 1), rough=0.02, transmission=1.0, ior=1.5, spec=0.5)
    M['glass_frost'] = new_mat("GlassFrost", (0.85, 0.95, 0.92, 1), rough=0.35, transmission=1.0, ior=1.45, spec=0.5)
    M['glass_green'] = new_mat("GlassSeaGreen", (0.55, 0.85, 0.75, 1), rough=0.3, transmission=0.9, ior=1.45)
    M['mirror'] = new_mat("Mirror", (0.98, 0.98, 0.98, 1), rough=0.0, metal=1.0)
    M['frame'] = new_mat("DarkFrame", (0.03, 0.03, 0.035, 1), rough=0.35, metal=0.5)
    M['steel'] = new_mat("Stainless", (0.80, 0.80, 0.79, 1), rough=0.25, metal=1.0)
    M['chrome'] = new_mat("Chrome", (0.9, 0.9, 0.9, 1), rough=0.08, metal=1.0)
    M['brass'] = new_mat("Brass", (0.85, 0.65, 0.35, 1), rough=0.3, metal=1.0)
    M['bronze'] = new_mat("Bronze", (0.45, 0.32, 0.22, 1), rough=0.4, metal=1.0)
    M['black_metal'] = new_mat("BlackMetal", (0.05, 0.05, 0.05, 1), rough=0.4, metal=0.8)
    # wood
    M['wood_slat'] = wood("WoodSlat", light=(0.74, 0.52, 0.28, 1), dark=(0.56, 0.36, 0.17, 1), grain_axis='Z', rough=0.5, coat=0.1)
    M['teak'] = wood("Teak", light=(0.62, 0.42, 0.24, 1), dark=(0.45, 0.28, 0.14, 1), grain_axis='X', rough=0.5, coat=0.1)
    M['oak'] = wood("Oak", light=(0.80, 0.68, 0.50, 1), dark=(0.68, 0.55, 0.38, 1), grain_axis='Z', rough=0.45, coat=0.2)
    M['oak_h'] = wood("OakH", light=(0.80, 0.68, 0.50, 1), dark=(0.68, 0.55, 0.38, 1), grain_axis='X', rough=0.45, coat=0.2)
    M['oak_pale'] = wood("OakPale", light=(0.86, 0.78, 0.64, 1), dark=(0.76, 0.66, 0.50, 1), grain_axis='Z', rough=0.45, coat=0.15)
    M['walnut'] = wood("Walnut", light=(0.40, 0.25, 0.14, 1), dark=(0.22, 0.12, 0.06, 1), grain_axis='X', rough=0.4, coat=0.3)
    M['walnut_v'] = wood("WalnutV", light=(0.40, 0.25, 0.14, 1), dark=(0.22, 0.12, 0.06, 1), grain_axis='Z', rough=0.4, coat=0.3)
    M['ebony'] = wood("Ebony", light=(0.10, 0.08, 0.07, 1), dark=(0.04, 0.03, 0.03, 1), grain_axis='X', rough=0.35, coat=0.3)
    M['door'] = wave_wood("DoorWaveWood")
    # wide-plank white oak (photos 12/17): 260 mm boards, very low tone contrast between boards, pale grain
    M['oak_floor'] = wood_planks("OakFloor", light=(0.86, 0.78, 0.65, 1), dark=(0.79, 0.70, 0.57, 1), plank=(2.6, 0.26))
    M['oak_floor_y'] = wood_planks("OakFloorY", light=(0.86, 0.78, 0.65, 1), dark=(0.79, 0.70, 0.57, 1), plank=(2.6, 0.26), along='Y')
    M['cedar_ceiling'] = wood_planks("CedarCeiling", light=(0.78, 0.62, 0.42, 1), dark=(0.66, 0.50, 0.32, 1), plank=(3.0, 0.14), along='Y', rough=0.5, coat=0.1)
    M['oak_ceiling'] = wood_planks("OakCeiling", light=(0.84, 0.72, 0.52, 1), dark=(0.72, 0.60, 0.42, 1), plank=(3.0, 0.16), along='Y', rough=0.5, coat=0.1)
    # floors / paving
    M['floor_stone'] = tiles("InteriorLimestone", (0.88, 0.83, 0.73, 1), grout=(0.70, 0.66, 0.58, 1), size=(1.2, 1.2), gap=0.003, rough=0.28, variation=0.04, mottle=0.25, bump=0.05, coat=0.3)
    M['pavers'] = tiles("TerracePavers", (0.78, 0.74, 0.66, 1), grout=(0.50, 0.47, 0.42, 1), size=(1.2, 0.6), gap=0.01, rough=0.6, variation=0.08, mottle=0.35, bump=0.3, offset=0.5)
    M['pavers_big'] = tiles("TerracePaversBig", (0.80, 0.76, 0.68, 1), grout=(0.50, 0.47, 0.42, 1), size=(1.2, 1.2), gap=0.01, rough=0.55, variation=0.06, mottle=0.3, bump=0.25)
    # motor court: large-format 1.2 x 0.6 m pale concrete pavers between the grass strips (photos 02/23), not cobbles
    M['court'] = tiles("MotorCourt", (0.66, 0.64, 0.60, 1), grout=(0.42, 0.40, 0.37, 1), size=(0.6, 1.2), gap=0.006, rough=0.7, variation=0.07, mottle=0.35, bump=0.25, offset=0.5, plane='XY')
    M['tile_spa'] = tiles("SpaMosaic", (0.55, 0.72, 0.74, 1), grout=(0.80, 0.82, 0.80, 1), size=(0.05, 0.05), gap=0.004, rough=0.2, variation=0.25, mottle=0.2, bump=0.4, coat=0.5)
    M['tile_pool_edge'] = tiles("PoolEdgeMosaic", (0.35, 0.45, 0.55, 1), grout=(0.7, 0.72, 0.7, 1), size=(0.05, 0.05), gap=0.004, rough=0.2, variation=0.35, mottle=0.2, bump=0.4, coat=0.5)
    M['tile_dark'] = tiles("DarkPorcelain", (0.22, 0.21, 0.20, 1), grout=(0.15, 0.15, 0.14, 1), size=(0.6, 0.6), gap=0.003, rough=0.35, variation=0.05, mottle=0.2, bump=0.1)
    # ground
    # lawns / turf: muted, slightly blue-green at dusk (the photos' grass is far less saturated than a daylight lawn)
    M['turf'] = turf("Turf", c_dark=(0.09, 0.20, 0.06, 1), c_light=(0.19, 0.33, 0.11, 1))
    M['lawn'] = turf("Lawn", c_dark=(0.08, 0.19, 0.05, 1), c_light=(0.17, 0.31, 0.09, 1), stripes=True)
    M['lawn_rear'] = turf("LawnRear", c_dark=(0.09, 0.21, 0.06, 1), c_light=(0.19, 0.34, 0.11, 1), stripes=True, stripe_axis='Y', stripe_w=0.5)
    M['ground'] = noise_mat("Ground", (0.14, 0.17, 0.07, 1), (0.24, 0.26, 0.11, 1), scale=4, bump=0.2)
    M['hill'] = noise_mat("Hillside", (0.20, 0.24, 0.10, 1), (0.36, 0.38, 0.18, 1), scale=3, bump=0.5, detail=10)
    M['asphalt'] = noise_mat("Asphalt", (0.10, 0.10, 0.10, 1), (0.16, 0.16, 0.15, 1), scale=30, bump=0.2)
    M['mulch'] = noise_mat("Mulch", (0.10, 0.06, 0.03, 1), (0.20, 0.12, 0.07, 1), scale=30, bump=0.6)
    M['pebble'] = noise_mat("PebbleGrey", (0.45, 0.44, 0.42, 1), (0.70, 0.69, 0.66, 1), scale=80, bump=0.8, detail=3, rough=0.6)
    M['fire_glass'] = new_mat("FireGlassBlack", (0.02, 0.02, 0.02, 1), rough=0.1, coat=1.0)
    # water
    # pool: clear water with a faint blue absorption and a little scatter so the underwater lights make it glow
    # (photo 24); very gentle ripples.  The reflecting pool is near-still.
    M['water'] = water("PoolWater", tint=(0.60, 0.90, 1.0, 1), density=0.05, ripple=0.10, scatter=0.035, scatter_col=(0.60, 0.88, 1.0, 1))
    M['water_still'] = water("ReflectingWater", tint=(0.75, 0.90, 0.92, 1), density=0.15, ripple=0.015)
    M['pool_shell'] = noise_mat("PoolPlaster", (0.80, 0.90, 0.92, 1), (0.88, 0.95, 0.96, 1), scale=12, bump=0.05, rough=0.5)
    # very subtle caustic shimmer on the plaster (the photos show only a soft dappling, never a bold cell web)
    ntp, bp_ = M['pool_shell'].node_tree, _bsdf(M['pool_shell'])
    cv0 = _coords(ntp, scale=(1.0, 1.0, 1.0))
    dn = ntp.nodes.new("ShaderNodeTexNoise"); dn.inputs["Scale"].default_value = 0.8; dn.inputs["Detail"].default_value = 2.0
    ntp.links.new(dn.inputs["Vector"], cv0)
    dv = ntp.nodes.new("ShaderNodeVectorMath"); dv.operation = 'MULTIPLY_ADD'; dv.inputs[1].default_value = (0.5, 0.5, 0.5)
    ntp.links.new(dv.inputs[0], dn.outputs["Color"]); ntp.links.new(dv.inputs[2], cv0)
    cv = dv.outputs["Vector"]
    vor = _voronoi(ntp, cv, scale=3.2, feature='DISTANCE_TO_EDGE')
    web = _math(ntp, 'POWER', _math(ntp, 'SUBTRACT', 1.0, _math(ntp, 'MULTIPLY', vor.outputs["Distance"], 7.0, clamp=True)), 2.0)
    vor2 = _voronoi(ntp, _coords(ntp, scale=(1.4, 1.4, 1.4), loc=(3.1, 1.7, 0.4)), scale=3.2, feature='DISTANCE_TO_EDGE')
    web2 = _math(ntp, 'POWER', _math(ntp, 'SUBTRACT', 1.0, _math(ntp, 'MULTIPLY', vor2.outputs["Distance"], 8.0, clamp=True)), 2.0)
    web = _math(ntp, 'MULTIPLY', _math(ntp, 'ADD', web, web2), 0.5)
    ecol = _mixrgb(ntp, web, (0.55, 0.82, 0.95, 1), (0.85, 0.97, 1.0, 1))
    ntp.links.new(bp_.inputs["Emission Color"], ecol)
    estr = _math(ntp, 'ADD', 0.05, _math(ntp, 'MULTIPLY', web, 0.07))
    ntp.links.new(bp_.inputs["Emission Strength"], estr)
    # vegetation
    M['moss'] = moss("MossWall")
    M['green'] = foliage("GreenWall", (0.06, 0.20, 0.05, 1), (0.28, 0.48, 0.12, 1), 0.3, c3=(0.55, 0.62, 0.20, 1))
    M['green2'] = foliage("GreenWallB", (0.10, 0.28, 0.08, 1), (0.40, 0.55, 0.16, 1), 0.3, c3=(0.70, 0.60, 0.25, 1))
    M['green3'] = foliage("GreenWallC", (0.05, 0.16, 0.06, 1), (0.18, 0.38, 0.14, 1), 0.3, c3=(0.36, 0.52, 0.18, 1))
    M['foliage'] = foliage("Foliage", (0.06, 0.17, 0.05, 1), (0.15, 0.32, 0.08, 1), c3=(0.30, 0.42, 0.14, 1))
    M['foliage_dark'] = foliage("FoliageDark", (0.03, 0.10, 0.04, 1), (0.08, 0.19, 0.06, 1), 0.25)
    M['foliage_oak'] = foliage("FoliageOak", (0.05, 0.13, 0.04, 1), (0.13, 0.26, 0.08, 1), 0.3, c3=(0.25, 0.36, 0.12, 1))
    M['olive'] = foliage("Olive", (0.32, 0.38, 0.26, 1), (0.50, 0.54, 0.40, 1), 0.4, c3=(0.66, 0.68, 0.52, 1))
    M['grass_tuft'] = foliage("GrassTuft", (0.30, 0.36, 0.14, 1), (0.55, 0.58, 0.28, 1), 0.5)
    M['shrub'] = foliage("Shrub", (0.08, 0.20, 0.06, 1), (0.22, 0.40, 0.12, 1), 0.3)
    M['bark'] = noise_mat("Bark", (0.20, 0.16, 0.12, 1), (0.34, 0.29, 0.23, 1), scale=20, bump=0.6)
    M['bark_red'] = noise_mat("BarkRedwood", (0.28, 0.14, 0.08, 1), (0.42, 0.24, 0.14, 1), scale=25, bump=0.7)
    M['leaf_plant'] = foliage("HousePlant", (0.08, 0.26, 0.08, 1), (0.22, 0.48, 0.16, 1), 0.4)
    # lighting
    M['emit_warm'] = new_mat("EmitWarm", (1, 0.75, 0.5, 1), emit=(1.0, 0.72, 0.45, 1), emit_str=8.0)
    M['emit_ceiling'] = new_mat("EmitCeiling", (1, 0.8, 0.6, 1), emit=(1.0, 0.75, 0.50, 1), emit_str=1.2)
    M['emit_down'] = new_mat("EmitDownlight", (1, 0.8, 0.6, 1), emit=(1.0, 0.75, 0.48, 1), emit_str=60.0)
    M['emit_bar'] = new_mat("EmitBar", (1, 0.85, 0.65, 1), emit=(1.0, 0.80, 0.55, 1), emit_str=25.0)
    M['emit_cove'] = new_mat("EmitCove", (1, 0.85, 0.65, 1), emit=(1.0, 0.78, 0.50, 1), emit_str=12.0)
    M['emit_white'] = new_mat("EmitWhite", (1, 1, 1, 1), emit=(1.0, 0.95, 0.85, 1), emit_str=15.0)
    M['emit_pool'] = new_mat("EmitPoolLight", (0.8, 0.95, 1, 1), emit=(0.7, 0.92, 1.0, 1), emit_str=40.0)
    M['fire'] = fire("Fire")
    M['screen'] = screen_image("CinemaScreen")
    M['tv'] = new_mat("TVBlack", (0.01, 0.01, 0.012, 1), rough=0.05, coat=1.0)
    # soft goods
    M['fabric'] = fabric("BoucleCream", (0.86, 0.82, 0.74, 1))
    M['fabric_white'] = fabric("BoucleWhite", (0.92, 0.90, 0.85, 1))
    M['fabric_grey'] = fabric("BoucleGrey", (0.58, 0.56, 0.53, 1))
    M['fabric_taupe'] = fabric("BoucleTaupe", (0.62, 0.55, 0.47, 1))
    M['fabric_sand'] = fabric("LinenSand", (0.74, 0.66, 0.54, 1), weave=90, bump=0.15)
    M['fabric_brown'] = fabric("VelvetBrown", (0.30, 0.20, 0.14, 1), rough=0.8, sheen=1.0, weave=120, bump=0.1)
    M['fabric_rust'] = fabric("BoucleRust", (0.62, 0.32, 0.18, 1))
    M['fabric_dark'] = fabric("BoucleCharcoal", (0.22, 0.20, 0.19, 1))
    M['linen_white'] = linen("LinenWhite")
    M['grass'] = grass_blade("GrassBlade")
    M['grass_rear'] = grass_blade("GrassBladeRear", stripe_axis='Y', stripe_w=0.5)
    M['turf_fibre'] = grass_blade("TurfFibre", root=(0.08, 0.24, 0.05, 1), tip=(0.20, 0.42, 0.10, 1), dry=(0.24, 0.40, 0.12, 1), stripes=False)   # artificial turf (polish hair)
    M['leaf_oak'] = leaf_card("LeafOak", (0.05, 0.13, 0.04, 1), (0.12, 0.26, 0.07, 1), (0.22, 0.36, 0.11, 1), 0.35)
    M['leaf_olive'] = leaf_card("LeafOlive", (0.30, 0.38, 0.24, 1), (0.48, 0.54, 0.38, 1), (0.66, 0.70, 0.54, 1), 0.45, shape='lance')
    M['leaf_shrub'] = leaf_card("LeafShrub", (0.08, 0.22, 0.06, 1), (0.20, 0.40, 0.12, 1), (0.34, 0.52, 0.18, 1), 0.4)
    M['leaf_needle'] = leaf_card("LeafNeedle", (0.04, 0.11, 0.04, 1), (0.08, 0.18, 0.06, 1), (0.14, 0.26, 0.09, 1), 0.25, shape='needle')
    M['leaf_cluster_oak'] = leaf_card("LeafClusterOak", (0.04, 0.11, 0.035, 1), (0.10, 0.22, 0.06, 1), (0.20, 0.32, 0.10, 1), 0.3, shape='cluster')
    M['leaf_cluster_olive'] = leaf_card("LeafClusterOlive", (0.28, 0.36, 0.22, 1), (0.46, 0.52, 0.36, 1), (0.64, 0.68, 0.52, 1), 0.45, shape='cluster')
    M['leaf_cluster_shrub'] = leaf_card("LeafClusterShrub", (0.07, 0.20, 0.05, 1), (0.18, 0.36, 0.10, 1), (0.32, 0.48, 0.16, 1), 0.4, shape='cluster')
    M['throw'] = fabric("ThrowOat", (0.80, 0.72, 0.58, 1), weave=40, bump=0.35)
    M['throw_brown'] = fabric("ThrowBrown", (0.42, 0.30, 0.22, 1), weave=40, bump=0.35)
    M['leather_white'] = leather("LeatherWhite")
    M['leather_tan'] = leather("LeatherTan", (0.62, 0.42, 0.26, 1), rough=0.5)
    M['cane'] = fabric("Cane", (0.82, 0.68, 0.45, 1), weave=200, bump=0.6, rough=0.7)
    M['felt'] = fabric("PoolFelt", (0.02, 0.02, 0.025, 1), rough=1.0, sheen=0.2, weave=200, bump=0.2)
    M['rug'] = rug("RugGreige", (0.62, 0.58, 0.52, 1), (0.74, 0.70, 0.64, 1))
    M['rug_pale'] = rug("RugPale", (0.72, 0.68, 0.62, 1), (0.84, 0.80, 0.74, 1), pattern=True)
    M['rug_plum'] = rug("RugPlum", (0.24, 0.13, 0.15, 1), (0.34, 0.20, 0.22, 1), pattern=True)
    M['rug_camel'] = rug("RugCamel", (0.62, 0.48, 0.32, 1), (0.72, 0.58, 0.40, 1))
    M['rug_blue'] = rug("RugBlueGrey", (0.50, 0.54, 0.58, 1), (0.66, 0.68, 0.70, 1))
    M['carpet'] = rug("CarpetTheatre", (0.62, 0.58, 0.50, 1), (0.70, 0.66, 0.58, 1), scale=60)
    # misc
    M['black'] = new_mat("BlackMatte", (0.03, 0.03, 0.03, 1), rough=0.6)
    M['black_gloss'] = new_mat("BlackGloss", (0.02, 0.02, 0.02, 1), rough=0.15, coat=0.8)
    M['dark_slats'] = wood("DarkSlats", light=(0.18, 0.12, 0.08, 1), dark=(0.10, 0.06, 0.04, 1), grain_axis='Z', rough=0.6, coat=0.0)
    M['ceramic'] = new_mat("CeramicWhite", (0.95, 0.94, 0.90, 1), rough=0.3, coat=0.5)
    M['ceramic_cream'] = new_mat("CeramicCream", (0.88, 0.82, 0.70, 1), rough=0.35, coat=0.4)
    M['ceramic_black'] = new_mat("CeramicBlack", (0.06, 0.05, 0.05, 1), rough=0.3, coat=0.5)
    M['clay'] = noise_mat("Clay", (0.55, 0.42, 0.30, 1), (0.66, 0.52, 0.38, 1), scale=30, bump=0.3, rough=0.85)
    M['acrylic_white'] = new_mat("AcrylicWhite", (0.96, 0.96, 0.95, 1), rough=0.15, coat=0.6)
    M['paper'] = new_mat("Paper", (0.95, 0.94, 0.90, 1), rough=0.9, spec=0.2)
    M['lampshade'] = new_mat("Lampshade", (0.95, 0.88, 0.72, 1), rough=0.8, emit=(1.0, 0.80, 0.55, 1), emit_str=3.0)
    M['book'] = new_mat("Book", (0.85, 0.83, 0.78, 1), rough=0.8)
    M['plant_pot'] = new_mat("PlantPot", (0.85, 0.83, 0.78, 1), rough=0.6)
    M['soil'] = noise_mat("Soil", (0.12, 0.08, 0.05, 1), (0.20, 0.14, 0.09, 1), scale=40, bump=0.5)
    M['perf_x'] = perforated("PerfX", axis='X', z0=perf_z0)
    M['perf_y'] = perforated("PerfY", axis='Y', z0=perf_z0)
    M['art_stripes'] = art_stripes("ArtStripes")
    M['art_abstract'] = art_abstract("ArtAbstract")
    M['art_bw'] = art_abstract("ArtBW", bg=(0.95, 0.94, 0.92, 1), fg=(0.06, 0.06, 0.06, 1), scale=1.6, thresh=0.55)
    M['art_teal'] = art_abstract("ArtTeal", bg=(0.35, 0.62, 0.62, 1), fg=(0.92, 0.90, 0.85, 1), scale=2.5, thresh=0.6)
    M['art_dots'] = art_dots("ArtDots")
    M['art_lines'] = art_abstract("ArtLines", bg=(0.88, 0.84, 0.76, 1), fg=(0.15, 0.12, 0.10, 1), scale=5.0, thresh=0.62)
    M['art_patch'] = art_abstract("ArtPatch", bg=(0.90, 0.86, 0.78, 1), fg=(0.72, 0.55, 0.35, 1), scale=6.0, thresh=0.5)
    M['art_relief'] = plaster("ArtRelief", base=(0.92, 0.90, 0.86, 1), rough=0.8, grain=0.2)
    M['balls'] = new_mat("BilliardBalls", (0.9, 0.2, 0.1, 1), rough=0.1, coat=1.0)
    M['ball_white'] = new_mat("CueBall", (0.95, 0.94, 0.9, 1), rough=0.1, coat=1.0)
    return M


# Photographic PBR inputs: color maps are sRGB; data maps are Non-Color.
def image_texture(nt, path, vector, data=False, box=False):
    n = nt.nodes.new('ShaderNodeTexImage')
    n.image = bpy.data.images.load(str(path), check_existing=True)
    if data:
        n.image.colorspace_settings.name = 'Non-Color'
    if box:
        n.projection = 'BOX'
        n.projection_blend = 0.25
    nt.links.new(vector, n.inputs['Vector'])
    return n


def mapped(nt, scale, rotation=0):
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = scale
    mp.inputs['Rotation'].default_value[2] = rotation
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    return mp.outputs['Vector']


# ------------------------------------------------------------------ suburban cladding / roofing (object-space patterns)
def _plane_vec(nt, plane):
    """Object coordinates re-packed so that (X, Y) of the result lie in the given plane ('XY', 'XZ', 'YZ')."""
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(sep.inputs["Vector"], tc.outputs["Object"])
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    a, bb, c = {'XY': ('X', 'Y', 'Z'), 'XZ': ('X', 'Z', 'Y'), 'YZ': ('Y', 'Z', 'X')}[plane]
    nt.links.new(comb.inputs["X"], sep.outputs[a]); nt.links.new(comb.inputs["Y"], sep.outputs[bb])
    nt.links.new(comb.inputs["Z"], sep.outputs[c])
    return comb.outputs["Vector"], tc


def brick_veneer(name, plane='XZ', base=(0.30, 0.075, 0.045, 1), alt=(0.40, 0.12, 0.07, 1), dark=(0.17, 0.05, 0.035, 1),
                 mortar=(0.50, 0.48, 0.44, 1), size=(0.213, 0.0677), mortar_w=0.010, soldier=False, rough=0.85,
                 dark_frac=0.20, accent=None, accent_frac=0.0, tone_var=0.0, relief=0.55, blot=0.18):
    """Modular brick in running bond on a wall plane (object space, metres): per-brick tone between two reds, a
    scattering of darker flashed bricks, a light recessed mortar joint and a fine sandy face.  `soldier` stands the
    bricks on end (window heads, the course over the garage door).  Optional (defaults = the original look):
    `dark_frac` share of flashed bricks, `accent` colour for an odd orange / tan brick (`accent_frac` share),
    `tone_var` per-brick brightness jitter (0.2 = +/- 20 %), `relief` bump strength of the joints, `blot` large-scale
    weathering blotches."""
    m, nt, b = _new(name)
    vec, tc = _plane_vec(nt, plane)
    br = nt.nodes.new("ShaderNodeTexBrick")
    br.offset = 0.0 if soldier else 0.5; br.offset_frequency = 2
    br.squash = 1.0; br.squash_frequency = 1
    w, h = (size[1], size[0]) if soldier else size
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Mortar Size"].default_value = mortar_w
    br.inputs["Mortar Smooth"].default_value = 0.15
    br.inputs["Bias"].default_value = 0.0
    br.inputs["Brick Width"].default_value = w
    br.inputs["Row Height"].default_value = h
    br.inputs["Color1"].default_value = base
    br.inputs["Color2"].default_value = alt
    br.inputs["Mortar"].default_value = mortar
    nt.links.new(br.inputs["Vector"], vec)
    # darker "flashed" bricks: a second brick lattice with the same joints, thresholded per-brick random value
    br2 = nt.nodes.new("ShaderNodeTexBrick")
    br2.offset = br.offset; br2.offset_frequency = 2
    for k in ("Scale", "Mortar Size", "Brick Width", "Row Height"):
        br2.inputs[k].default_value = br.inputs[k].default_value
    br2.inputs["Color1"].default_value = (0, 0, 0, 1); br2.inputs["Color2"].default_value = (1, 1, 1, 1)
    br2.inputs["Bias"].default_value = 0.0
    shifted = nt.nodes.new("ShaderNodeVectorMath"); shifted.operation = 'ADD'
    shifted.inputs[1].default_value = (0.0, 0.0, 7.31)
    nt.links.new(shifted.inputs[0], vec); nt.links.new(br2.inputs["Vector"], shifted.outputs["Vector"])
    sepd = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(sepd.inputs["Color"], br2.outputs["Color"])
    darkf = _math(nt, 'GREATER_THAN', sepd.outputs["Red"], 1.0 - dark_frac)
    brickf = _math(nt, 'SUBTRACT', 1.0, br.outputs["Fac"])           # 1 on the brick faces, 0 in the joints
    col = _mixrgb(nt, _math(nt, 'MULTIPLY', darkf, brickf), br.outputs["Color"], dark)
    if accent is not None and accent_frac > 0:                        # the odd orange / tan brick
        accf = _math(nt, 'LESS_THAN', sepd.outputs["Red"], accent_frac)
        col = _mixrgb(nt, _math(nt, 'MULTIPLY', accf, brickf), col, accent)
    if tone_var > 0:                                                  # per-brick brightness from a third, shifted lattice
        br3 = nt.nodes.new("ShaderNodeTexBrick")
        br3.offset = br.offset; br3.offset_frequency = 2
        for k in ("Scale", "Mortar Size", "Brick Width", "Row Height"):
            br3.inputs[k].default_value = br.inputs[k].default_value
        br3.inputs["Color1"].default_value = (0, 0, 0, 1); br3.inputs["Color2"].default_value = (1, 1, 1, 1)
        sh3 = nt.nodes.new("ShaderNodeVectorMath"); sh3.operation = 'ADD'
        sh3.inputs[1].default_value = (0.0, 0.0, 3.77)
        nt.links.new(sh3.inputs[0], vec); nt.links.new(br3.inputs["Vector"], sh3.outputs["Vector"])
        sep3 = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(sep3.inputs["Color"], br3.outputs["Color"])
        jit = _math(nt, 'ADD', 1.0 - tone_var, _math(nt, 'MULTIPLY', sep3.outputs["Red"], 2.0 * tone_var))
        jc = nt.nodes.new("ShaderNodeCombineColor")
        for k in ("Red", "Green", "Blue"):
            nt.links.new(jc.inputs[k], jit)
        col = _mixrgb(nt, brickf, col, _mixrgb(nt, 1.0, col, jc.outputs["Color"], 'MULTIPLY'))
    sand = _noise(nt, tc.outputs["Object"], scale=180.0, detail=3.0)
    blotn = _noise(nt, tc.outputs["Object"], scale=6.0, detail=3.0)
    col = _mixrgb(nt, _math(nt, 'MULTIPLY', sand, 0.25), col, (0.72, 0.70, 0.68, 1), 'MULTIPLY')
    col = _mixrgb(nt, _math(nt, 'MULTIPLY', blotn, blot), col, (1.2, 1.12, 1.05, 1), 'MULTIPLY')
    nt.links.new(b.inputs["Base Color"], col)
    _set(b, "Roughness", rough); _set(b, "Specular IOR Level", 0.25)
    height = _math(nt, 'ADD', _math(nt, 'MULTIPLY', brickf, 1.0), _math(nt, 'MULTIPLY', sand, 0.15))
    _bump(nt, b, height, relief, 0.006)
    return m


def shingles(name, c1=(0.075, 0.078, 0.085, 1), c2=(0.12, 0.123, 0.13, 1), c3=(0.045, 0.047, 0.052, 1),
             exposure=0.143, tab=0.33, rough=0.92, granule=(1.6, 1.6, 1.6, 1), granule_amt=0.35, tint=None, tint_amt=0.0,
             butt_dark=0.55, spec=0.3, grazing=0.0, diffuse_rough=None):
    """Architectural (laminated) asphalt shingles in the object's XY plane: X along the eave, Y up the slope.
    Two offset tab lattices give the irregular dimensional pattern; each course casts a shadow line at its butt edge;
    granule speckle + gentle streaking.  Optional (defaults = the original look): `granule` multiply colour and
    `granule_amt` of the fine speckle, `tint` a second (e.g. brown) blend colour mixed into random tabs by `tint_amt`,
    `butt_dark` strength of the course shadow line, `spec` the specular level, `grazing` > 0 darkens the shingles seen
    at a grazing angle (the course steps and granules hide their lit faces there) by up to that fraction,
    `diffuse_rough` sets the Principled diffuse (Oren-Nayar) roughness of the granular surface."""
    m, nt, b = _new(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    obj = tc.outputs["Object"]
    def lattice(width, off, loc):
        br = nt.nodes.new("ShaderNodeTexBrick")
        br.offset = off; br.offset_frequency = 1
        br.inputs["Scale"].default_value = 1.0
        br.inputs["Mortar Size"].default_value = 0.0
        br.inputs["Brick Width"].default_value = width
        br.inputs["Row Height"].default_value = exposure
        br.inputs["Color1"].default_value = (0, 0, 0, 1); br.inputs["Color2"].default_value = (1, 1, 1, 1)
        v = nt.nodes.new("ShaderNodeVectorMath"); v.operation = 'ADD'; v.inputs[1].default_value = loc
        nt.links.new(v.inputs[0], obj); nt.links.new(br.inputs["Vector"], v.outputs["Vector"])
        s = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(s.inputs["Color"], br.outputs["Color"])
        return s.outputs["Red"]
    r1 = lattice(tab, 0.37, (0.0, 0.0, 0.0))
    r2 = lattice(tab * 0.55, 0.71, (0.13, 0.0, 3.0))
    tone = _math(nt, 'ADD', _math(nt, 'MULTIPLY', r1, 0.6), _math(nt, 'MULTIPLY', r2, 0.4))
    col = _ramp(nt, tone, [(0.15, c3), (0.45, c1), (0.85, c2)])
    # shadow line at the butt of each course: fract(y / exposure) near 0 = the exposed lower edge of the course above
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(sep.inputs["Vector"], obj)
    fy = _math(nt, 'FRACT', _math(nt, 'DIVIDE', sep.outputs["Y"], exposure))
    butt = _math(nt, 'LESS_THAN', fy, 0.09)
    if tint is not None and tint_amt > 0:
        r3 = lattice(tab * 0.8, 0.23, (0.41, 0.0, 7.0))
        col = _mixrgb(nt, _math(nt, 'MULTIPLY', _math(nt, 'GREATER_THAN', r3, 0.55), tint_amt), col, tint)
    col = _mixrgb(nt, _math(nt, 'MULTIPLY', butt, butt_dark), col, (0.02, 0.02, 0.022, 1))
    gran = _noise(nt, obj, scale=260.0, detail=2.0)
    col = _mixrgb(nt, _math(nt, 'MULTIPLY', gran, granule_amt), col, granule, 'MULTIPLY')
    streak = _noise(nt, _coords(nt, scale=(0.4, 3.0, 1.0)), scale=1.5, detail=3.0)
    col = _mixrgb(nt, _math(nt, 'MULTIPLY', streak, 0.25), col, (1.25, 1.25, 1.25, 1), 'MULTIPLY')
    if grazing > 0:
        lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.5
        g = _math(nt, 'POWER', lw.outputs["Facing"], 2.0)
        col = _mixrgb(nt, _math(nt, 'MULTIPLY', g, grazing), col, (0.0, 0.0, 0.0, 1))
    nt.links.new(b.inputs["Base Color"], col)
    _set(b, "Roughness", rough); _set(b, "Specular IOR Level", spec)
    if diffuse_rough is not None:
        _set(b, "Diffuse Roughness", diffuse_rough)
    h = _math(nt, 'ADD', fy, _math(nt, 'MULTIPLY', gran, 0.05))
    _bump(nt, b, h, 0.35, 0.01)
    return m


def painted_board(name, base=(0.17, 0.235, 0.32, 1), rough=0.55, grain=0.18):
    """Painted fibre-cement lap siding / trim: a faint embossed cedar grain running along X / Y, satin paint."""
    m, nt, b = _new(name)
    g = _noise(nt, _coords(nt, scale=(1.2, 1.2, 40.0)), scale=1.0, detail=4.0, rough=0.6, distortion=0.4)
    speck = _noise(nt, _coords(nt), scale=90.0, detail=2.0)
    col = _mixrgb(nt, _math(nt, 'MULTIPLY', g, grain * 0.3), base, (0.86, 0.86, 0.86, 1), 'MULTIPLY')
    col = _mixrgb(nt, _math(nt, 'MULTIPLY', speck, 0.06), col, (0.8, 0.8, 0.8, 1), 'MULTIPLY')
    nt.links.new(b.inputs["Base Color"], col)
    _set(b, "Roughness", rough); _set(b, "Specular IOR Level", 0.4)
    _bump(nt, b, g, grain, 0.004)
    return m


def knockdown(name, base=(0.90, 0.90, 0.88, 1), strength=0.45, scale=9.0):
    """Knock-down / splatter drywall texture (US ceilings, photos of 2000s builder homes): flat-topped islands."""
    m, nt, b = _new(name)
    vec = _coords(nt)
    n = _noise(nt, vec, scale=scale, detail=6.0, rough=0.62, distortion=0.6)
    isl = _stretch(nt, n, 0.46, 0.56)
    fine = _noise(nt, vec, scale=120.0, detail=2.0)
    col = _mixrgb(nt, _math(nt, 'MULTIPLY', isl, 0.05), base, (0.9, 0.9, 0.9, 1), 'MULTIPLY')
    nt.links.new(b.inputs["Base Color"], col)
    _set(b, "Roughness", 0.95); _set(b, "Specular IOR Level", 0.2)
    _bump(nt, b, _math(nt, 'ADD', isl, _math(nt, 'MULTIPLY', fine, 0.2)), strength, 0.004)
    return m


def fan_pavers(name, centre=(0.0, 0.0), base=(0.28, 0.24, 0.21, 1), alt=(0.36, 0.31, 0.27, 1), joint=(0.18, 0.17, 0.15, 1),
               ring=0.16, length=0.20, rough=0.85):
    """Concrete cobble pavers laid in concentric rings (European fan / circle kit) around `centre` (object XY)."""
    m, nt, b = _new(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(sep.inputs["Vector"], tc.outputs["Object"])
    dx = _math(nt, 'SUBTRACT', sep.outputs["X"], centre[0]); dy = _math(nt, 'SUBTRACT', sep.outputs["Y"], centre[1])
    r = nt.nodes.new("ShaderNodeVectorMath"); r.operation = 'LENGTH'
    cxy = nt.nodes.new("ShaderNodeCombineXYZ"); nt.links.new(cxy.inputs["X"], dx); nt.links.new(cxy.inputs["Y"], dy)
    nt.links.new(r.inputs[0], cxy.outputs["Vector"])
    ang = _math(nt, 'ARCTAN2', dy, dx)
    arc = _math(nt, 'MULTIPLY', ang, r.outputs["Value"])                      # arc length along the ring
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(comb.inputs["X"], arc); nt.links.new(comb.inputs["Y"], r.outputs["Value"])
    br = nt.nodes.new("ShaderNodeTexBrick")
    br.offset = 0.5; br.offset_frequency = 2
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Mortar Size"].default_value = 0.008
    br.inputs["Mortar Smooth"].default_value = 0.4
    br.inputs["Brick Width"].default_value = length
    br.inputs["Row Height"].default_value = ring
    br.inputs["Color1"].default_value = base; br.inputs["Color2"].default_value = alt
    br.inputs["Mortar"].default_value = joint
    nt.links.new(br.inputs["Vector"], comb.outputs["Vector"])
    n = _noise(nt, tc.outputs["Object"], scale=40.0, detail=3.0)
    col = _mixrgb(nt, _math(nt, 'MULTIPLY', n, 0.3), br.outputs["Color"], (0.75, 0.75, 0.75, 1), 'MULTIPLY')
    nt.links.new(b.inputs["Base Color"], col)
    _set(b, "Roughness", rough); _set(b, "Specular IOR Level", 0.25)
    _bump(nt, b, _math(nt, 'ADD', _math(nt, 'SUBTRACT', 1.0, br.outputs["Fac"]), _math(nt, 'MULTIPLY', n, 0.2)), 0.5, 0.006)
    return m
