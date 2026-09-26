"""Plants with real leaves: potted plants, cut stems for vases, flowering shrubs, hedges (Cycles, no image textures).

Every leaf is an explicit quad strip (1-5 quads along its length so it can arch, twist and droop) carrying its own
UV square (U = base -> tip, V across) and a per-face 'leaf_rnd' attribute; an alpha-cut shader gives it the species'
outline (obovate / heart / strap / pinnate frond ...), mid-rib, side veins, margin, a felted or glossy underside and
per-leaf tint.  Flowers are alpha-cut discs (rose spiral, floret ball, spike, 5-petal).  This replaces the faceted
"blob on a stick" potted plants of archviz.parts and complements archviz.trees (trees keep their own leaf code).

Public
  potted(name, pos, kind, height, pot, ...)   pot + plant; kinds: fiddle, monstera, bird, fern, palm, snake, olive,
                                              boxwood, citrus, lavender, rosemary, hydrangea, agapanthus
  stems(name, pos, kind, height, ...)         cut stems rising from a vase mouth: eucalyptus, olive, magnolia
  shrub(name, pos, r, h, kind, ...)           garden shrub: boxwood, rose, hydrangea, agapanthus, lavender, oleander,
                                              privet (mixed green)
  hedge(name, x0, x1, y0, y1, z, h, kind)     clipped hedge box (leaf shell over a dark core)
  Foliage                                     the accumulator, for custom arrangements
Objects: `<name>` (pot / stems / wood) + `<name>_Leaves` (all quads, one material slot per leaf kind).
"""
import math, random
import bpy
from mathutils import Vector
from .mesh import MB, collection
from . import materials as _mat
from .trees import _sections, leaf_materials as _tree_leaf_mats

_M = {}


# ------------------------------------------------------------------ shaders
def _uv(nt):
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(sep.inputs["Vector"], tc.outputs["UV"])
    return tc, sep.outputs["X"], sep.outputs["Y"]


def _uvnoise(nt, tc, scale=6.0, detail=2.0, stretch=(1, 1)):
    mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (stretch[0], stretch[1], 1.0)
    nt.links.new(mp.inputs["Vector"], tc.outputs["UV"])
    n = nt.nodes.new("ShaderNodeTexNoise"); n.noise_dimensions = '2D'
    n.inputs["Scale"].default_value = scale; n.inputs["Detail"].default_value = detail
    nt.links.new(n.inputs["Vector"], mp.outputs["Vector"])
    return n.outputs["Fac"]


def _finish(nt, b, col, alpha, translucent=0.3, rough=0.45, coat=0.15, spec=0.4):
    nt.links.new(b.inputs["Base Color"], col)
    nt.links.new(b.inputs["Alpha"], alpha)
    _mat._set(b, "Roughness", rough); _mat._set(b, "Specular IOR Level", spec); _mat._set(b, "Coat Weight", coat)
    _mat._set(b, "Coat Roughness", 0.3)
    tr = nt.nodes.new("ShaderNodeBsdfTranslucent"); nt.links.new(tr.inputs["Color"], col)
    mixs = nt.nodes.new("ShaderNodeMixShader"); mixs.inputs["Fac"].default_value = translucent
    nt.links.new(mixs.inputs[1], b.outputs["BSDF"]); nt.links.new(mixs.inputs[2], tr.outputs["BSDF"])
    trans = nt.nodes.new("ShaderNodeBsdfTransparent")
    mixa = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(mixa.inputs["Fac"], alpha)
    nt.links.new(mixa.inputs[1], trans.outputs["BSDF"]); nt.links.new(mixa.inputs[2], mixs.outputs["Shader"])
    nt.links.new(nt.nodes["Material Output"].inputs["Surface"], mixa.outputs["Shader"])


def _rnd(nt):
    at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_name = "leaf_rnd"
    return at.outputs["Fac"]


def leaf_shader(name, shape='obovate', top=(0.06, 0.16, 0.05, 1), mid=(0.10, 0.24, 0.07, 1), top2=(0.16, 0.32, 0.10, 1),
                under=None, translucent=0.3, rough=0.45, coat=0.15, p=1.0, q=0.8, veins=0, vein_k=0.8, margin=0.0,
                margin_col=None, band=0.0, torn=0.0, leaflets=0, duty=0.55, slits=0, holes=0, rib=0.012, rib_col=(0.55, 0.60, 0.42, 1),
                pinch=0.0, pinch_at=0.32, pinch_w=0.13):
    """Alpha-cut leaf on a unit quad: U base -> tip, V across.  Outline half-width w(u) = 0.5 sin(pi u^p)^q
    (p > 1 obovate, p < 1 ovate; q < 1 round shoulders, q > 1 pointed).  Options: side `veins` per leaf,
    darker / coloured `margin`, cross `band`ing (sansevieria), `torn` edges, pinnate `leaflets` (palm / fern),
    monstera `slits` + `holes`."""
    m, nt, b = _mat._new(name)
    M = lambda op, a, c=None: _mat._math(nt, op, a, c)
    tc, u, v = _uv(nt)
    av = M('ABSOLUTE', M('SUBTRACT', v, 0.5))
    if shape == 'strap':
        w = M('MULTIPLY', M('POWER', M('SUBTRACT', 1.0, M('POWER', u, 10.0)), 0.5), M('POWER', _mat._math(nt, 'MULTIPLY', u, 10.0, clamp=True), 0.5))
        w = M('MULTIPLY', w, M('ADD', 0.86, M('MULTIPLY', M('SINE', M('MULTIPLY', M('POWER', u, 0.7), math.pi)), 0.14)))
        w = M('MULTIPLY', w, 0.5)
    else:
        s = M('SINE', M('MULTIPLY', M('POWER', u, p), math.pi))
        w = M('MULTIPLY', M('POWER', M('MAXIMUM', s, 0.0), q), 0.5)
        if shape == 'heart':     # the two basal lobes: widen near the base, notch on the mid-line
            w = M('MAXIMUM', w, M('MULTIPLY', M('SUBTRACT', 0.42, M('MULTIPLY', M('ABSOLUTE', M('SUBTRACT', u, 0.16)), 1.6)), 1.0))
    if pinch > 0:            # a waist (fiddle-leaf fig): w *= 1 - pinch * exp(-((u - at) / width)^2)
        dd = M('SUBTRACT', u, pinch_at)
        g = M('EXPONENT', M('MULTIPLY', M('DIVIDE', M('MULTIPLY', dd, dd), pinch_w * pinch_w), -1.0))
        w = M('MULTIPLY', w, M('SUBTRACT', 1.0, M('MULTIPLY', g, pinch)))
    if torn > 0:
        w = M('ADD', w, M('MULTIPLY', M('SUBTRACT', _uvnoise(nt, tc, 9.0, 3.0), 0.5), torn))
    alpha = M('LESS_THAN', av, w)
    if shape == 'heart':
        notch = M('MULTIPLY', M('LESS_THAN', u, 0.09), M('LESS_THAN', av, M('MULTIPLY', M('SUBTRACT', 0.09, u), 0.9)))
        alpha = M('MULTIPLY', alpha, M('SUBTRACT', 1.0, notch))
    if leaflets > 0:
        rach = M('LESS_THAN', av, M('ADD', 0.006, M('MULTIPLY', M('SUBTRACT', 1.0, u), 0.012)))
        sfrac = M('FRACT', M('SUBTRACT', M('MULTIPLY', u, float(leaflets)), M('MULTIPLY', av, 0.9)))
        wsafe = M('MAXIMUM', w, 0.02)
        dutyu = M('MULTIPLY', duty, M('SUBTRACT', 1.0, M('MULTIPLY', M('DIVIDE', av, wsafe), 0.55)))
        lf = M('LESS_THAN', sfrac, dutyu)
        alpha = M('MAXIMUM', rach, M('MULTIPLY', alpha, lf))
    if slits > 0:
        sl = M('LESS_THAN', M('FRACT', M('ADD', M('MULTIPLY', u, float(slits)), M('MULTIPLY', av, 0.5))), 0.26)
        deep = M('GREATER_THAN', av, M('ADD', 0.06, M('MULTIPLY', _uvnoise(nt, tc, 5.0, 2.0), 0.06)))
        alpha = M('MULTIPLY', alpha, M('SUBTRACT', 1.0, M('MULTIPLY', sl, deep)))
    if holes > 0:
        mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (float(holes), float(holes), 1.0)
        nt.links.new(mp.inputs["Vector"], tc.outputs["UV"])
        vo = nt.nodes.new("ShaderNodeTexVoronoi"); vo.voronoi_dimensions = '2D'; vo.inputs["Randomness"].default_value = 1.0
        nt.links.new(vo.inputs["Vector"], mp.outputs["Vector"])
        hole = M('LESS_THAN', vo.outputs["Distance"], 0.16)
        zone = M('MULTIPLY', M('GREATER_THAN', av, 0.07), M('LESS_THAN', av, 0.32))
        zone = M('MULTIPLY', zone, M('MULTIPLY', M('GREATER_THAN', u, 0.2), M('LESS_THAN', u, 0.85)))
        alpha = M('MULTIPLY', alpha, M('SUBTRACT', 1.0, M('MULTIPLY', hole, zone)))
    # colour
    rnd = _rnd(nt)
    col = _mat._ramp(nt, rnd, [(0.0, top), (0.5, mid), (1.0, top2)])
    if veins > 0:
        vn = M('LESS_THAN', M('FRACT', M('MULTIPLY', M('SUBTRACT', u, M('MULTIPLY', av, vein_k)), float(veins))), 0.05)
        lighter = _mat._mixrgb(nt, 1.0, col, (1.35, 1.32, 1.15, 1), 'MULTIPLY')
        col = _mat._mixrgb(nt, M('MULTIPLY', vn, 0.55), col, lighter)
    if band > 0:
        bn = _mat._stretch(nt, _uvnoise(nt, tc, 3.0, 2.0, stretch=(1.0, 14.0)), 0.4, 0.6)
        pale = _mat._mixrgb(nt, 1.0, col, (1.9, 1.85, 1.4, 1), 'MULTIPLY')
        col = _mat._mixrgb(nt, M('MULTIPLY', bn, band), col, pale)
    if rib > 0:
        rb = M('LESS_THAN', av, M('MULTIPLY', M('SUBTRACT', 1.1, u), rib))
        col = _mat._mixrgb(nt, M('MULTIPLY', rb, 0.7), col, rib_col)
    if margin > 0:
        ed = M('LESS_THAN', M('SUBTRACT', w, av), margin)
        col = _mat._mixrgb(nt, M('MULTIPLY', ed, 0.8), col, margin_col or _mat._mixrgb(nt, 1.0, col, (0.55, 0.55, 0.45, 1), 'MULTIPLY'))
    if under is not None:
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        uc = _mat._mixrgb(nt, 1.0, under, _mat._ramp(nt, rnd, [(0.0, (0.9, 0.9, 0.88, 1)), (1.0, (1.1, 1.1, 1.05, 1))]), 'MULTIPLY')
        col = _mat._mixrgb(nt, geo.outputs["Backfacing"], col, uc)
    _finish(nt, b, col, alpha, translucent, rough, coat)
    return m


def flower_shader(name, kind='rose', c_in=(0.85, 0.30, 0.42, 1), c_out=(0.98, 0.78, 0.82, 1), c_alt=None, rough=0.7):
    """Flower on a unit quad (centred): 'rose' (spiral petals), 'ball' (many florets, hydrangea / agapanthus),
    'spike' (lavender), 'flat5' (five petals, oleander / citrus)."""
    m, nt, b = _mat._new(name)
    M = lambda op, a, c=None: _mat._math(nt, op, a, c)
    tc, u, v = _uv(nt)
    x = M('SUBTRACT', u, 0.5); y = M('SUBTRACT', v, 0.5)
    r = M('SQRT', M('ADD', M('MULTIPLY', x, x), M('MULTIPLY', y, y)))
    an = nt.nodes.new("ShaderNodeMath"); an.operation = 'ARCTAN2'; nt.links.new(an.inputs[0], y); nt.links.new(an.inputs[1], x)
    a = an.outputs[0]
    rnd = _rnd(nt)
    if kind == 'rose':
        edge = M('MULTIPLY', 0.5, M('ADD', 0.84, M('MULTIPLY', M('SINE', M('ADD', M('MULTIPLY', a, 5.0), M('MULTIPLY', r, 9.0))), 0.16)))
        alpha = M('LESS_THAN', r, edge)
        base = _mat._ramp(nt, M('MULTIPLY', r, 2.0), [(0.0, c_in), (0.55, c_out), (1.0, c_out)])
        sh = M('ADD', 0.85, M('MULTIPLY', M('SINE', M('ADD', M('MULTIPLY', a, 5.0), M('MULTIPLY', r, 28.0))), 0.15))
        col = _mat._mixrgb(nt, 1.0, base, _mat._ramp(nt, sh, [(0.7, (0.7, 0.7, 0.7, 1)), (1.0, (1.05, 1.05, 1.05, 1))]), 'MULTIPLY')
    elif kind == 'ball':
        mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (5.0, 5.0, 1.0)
        nt.links.new(mp.inputs["Vector"], tc.outputs["UV"])
        vo = nt.nodes.new("ShaderNodeTexVoronoi"); vo.voronoi_dimensions = '2D'
        nt.links.new(vo.inputs["Vector"], mp.outputs["Vector"])
        d = vo.outputs["Distance"]
        petal = M('LESS_THAN', d, M('ADD', 0.30, M('MULTIPLY', M('ABSOLUTE', M('SINE', M('MULTIPLY', a, 2.0))), 0.18)))
        alpha = M('MULTIPLY', M('LESS_THAN', r, 0.5), petal)
        csep = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(csep.inputs["Color"], vo.outputs["Color"])
        col = _mat._ramp(nt, csep.outputs["Red"], [(0.0, c_in), (0.5, c_out), (1.0, c_alt or c_out)])
        col = _mat._mixrgb(nt, M('LESS_THAN', d, 0.06), col, (0.9, 0.85, 0.3, 1))
    elif kind == 'spike':
        w = M('MULTIPLY', 0.13, M('POWER', M('SINE', M('MULTIPLY', u, math.pi)), 0.5))
        av = M('ABSOLUTE', y)
        fl = M('GREATER_THAN', _uvnoise(nt, tc, 22.0, 1.0), 0.42)
        stem = M('MULTIPLY', M('LESS_THAN', av, 0.02), M('LESS_THAN', u, 0.35))
        alpha = M('MAXIMUM', stem, M('MULTIPLY', M('MULTIPLY', M('LESS_THAN', av, w), fl), M('GREATER_THAN', u, 0.3)))
        col = _mat._ramp(nt, rnd, [(0.0, c_in), (1.0, c_out)])
        col = _mat._mixrgb(nt, M('LESS_THAN', u, 0.32), col, (0.32, 0.38, 0.26, 1))
    else:   # flat5
        edge = M('MULTIPLY', 0.5, M('ADD', 0.5, M('MULTIPLY', M('POWER', M('ABSOLUTE', M('COSINE', M('MULTIPLY', a, 2.5))), 0.6), 0.5)))
        alpha = M('LESS_THAN', r, edge)
        col = _mat._ramp(nt, M('MULTIPLY', r, 2.0), [(0.0, (0.95, 0.85, 0.35, 1)), (0.18, c_in), (1.0, c_out)])
    col = _mat._mixrgb(nt, 1.0, col, _mat._ramp(nt, rnd, [(0.0, (0.88, 0.88, 0.88, 1)), (1.0, (1.08, 1.08, 1.08, 1))]), 'MULTIPLY')
    _finish(nt, b, col, alpha, 0.35, rough, 0.0, 0.3)
    return m


def mats():
    """Shared leaf / flower / pot materials (built once per scene)."""
    if _M:
        return _M
    S = leaf_shader
    _M['fiddle'] = S("LeafFiddle", 'obovate', (0.04, 0.12, 0.035, 1), (0.07, 0.18, 0.05, 1), (0.11, 0.24, 0.08, 1), under=(0.16, 0.26, 0.12, 1),
                     translucent=0.18, rough=0.28, coat=0.45, p=1.45, q=0.5, veins=7, vein_k=0.9, margin=0.03, torn=0.03, rib=0.02,
                     pinch=0.42, pinch_at=0.3, pinch_w=0.12)
    _M['monstera'] = S("LeafMonstera", 'heart', (0.03, 0.10, 0.03, 1), (0.05, 0.15, 0.05, 1), (0.08, 0.20, 0.06, 1), under=(0.12, 0.22, 0.10, 1),
                       translucent=0.12, rough=0.28, coat=0.45, p=0.8, q=0.55, veins=6, vein_k=0.7, slits=6, holes=4, rib=0.018)
    _M['bird'] = S("LeafBird", 'paddle', (0.07, 0.17, 0.05, 1), (0.11, 0.24, 0.07, 1), (0.17, 0.31, 0.10, 1), under=(0.20, 0.32, 0.15, 1),
                   translucent=0.28, rough=0.4, coat=0.2, p=1.15, q=0.45, veins=16, vein_k=0.35, torn=0.05, rib=0.03, rib_col=(0.62, 0.66, 0.42, 1))
    _M['fern'] = S("LeafFern", 'pinnate', (0.10, 0.24, 0.06, 1), (0.16, 0.34, 0.09, 1), (0.24, 0.42, 0.12, 1), translucent=0.45, rough=0.7, coat=0.0,
                   p=0.75, q=0.5, leaflets=22, duty=0.6, torn=0.02, rib=0.0)
    _M['palm'] = S("LeafPalm", 'pinnate', (0.06, 0.17, 0.05, 1), (0.10, 0.25, 0.07, 1), (0.16, 0.32, 0.10, 1), translucent=0.3, rough=0.45, coat=0.2,
                   p=0.9, q=0.45, leaflets=14, duty=0.5, rib=0.0)
    _M['snake'] = S("LeafSnake", 'strap', (0.04, 0.12, 0.04, 1), (0.07, 0.18, 0.06, 1), (0.10, 0.24, 0.08, 1), translucent=0.15, rough=0.4, coat=0.25,
                    band=0.8, margin=0.055, margin_col=(0.78, 0.68, 0.22, 1), rib=0.0)
    _M['citrus'] = S("LeafCitrus", 'elliptic', (0.05, 0.14, 0.04, 1), (0.08, 0.19, 0.06, 1), (0.12, 0.25, 0.08, 1), under=(0.28, 0.38, 0.22, 1),
                     translucent=0.25, rough=0.3, coat=0.4, p=0.9, q=0.9, veins=5, rib=0.02)
    _M['magnolia'] = S("LeafMagnolia", 'elliptic', (0.05, 0.13, 0.04, 1), (0.07, 0.17, 0.05, 1), (0.10, 0.22, 0.07, 1), under=(0.45, 0.30, 0.16, 1),
                       translucent=0.15, rough=0.25, coat=0.5, p=1.1, q=0.8, rib=0.02)
    _M['euc'] = S("LeafEucalyptus", 'elliptic', (0.40, 0.48, 0.40, 1), (0.50, 0.58, 0.48, 1), (0.62, 0.68, 0.56, 1), under=(0.55, 0.62, 0.52, 1),
                  translucent=0.35, rough=0.6, coat=0.05, p=1.0, q=0.45, rib=0.02, rib_col=(0.62, 0.66, 0.55, 1))
    _M['olive_leaf'] = S("LeafOliveStem", 'lanceolate', (0.24, 0.31, 0.20, 1), (0.32, 0.38, 0.26, 1), (0.42, 0.46, 0.34, 1), under=(0.60, 0.64, 0.54, 1),
                         translucent=0.3, rough=0.45, coat=0.15, p=0.85, q=1.2, rib=0.02, rib_col=(0.62, 0.66, 0.52, 1))
    _M['hyd_leaf'] = S("LeafHydrangea", 'ovate', (0.08, 0.20, 0.06, 1), (0.12, 0.27, 0.08, 1), (0.18, 0.34, 0.11, 1), under=(0.30, 0.42, 0.24, 1),
                       translucent=0.4, rough=0.55, coat=0.05, p=0.8, q=0.75, veins=8, torn=0.03, rib=0.016)
    _M['rose_leaf'] = S("LeafRose", 'elliptic', (0.05, 0.14, 0.04, 1), (0.08, 0.20, 0.06, 1), (0.12, 0.26, 0.08, 1), under=(0.26, 0.36, 0.20, 1),
                        translucent=0.3, rough=0.35, coat=0.3, p=0.9, q=0.8, veins=6, torn=0.04, rib=0.016)
    _M['oleander_leaf'] = S("LeafOleander", 'lanceolate', (0.07, 0.17, 0.06, 1), (0.11, 0.23, 0.08, 1), (0.16, 0.30, 0.11, 1), under=(0.30, 0.40, 0.26, 1),
                            translucent=0.25, rough=0.4, coat=0.2, p=0.9, q=1.1, rib=0.016)
    _M['agap_leaf'] = S("LeafAgapanthus", 'strap', (0.08, 0.20, 0.06, 1), (0.12, 0.28, 0.08, 1), (0.18, 0.36, 0.11, 1), translucent=0.35, rough=0.4,
                        coat=0.25, rib=0.0)
    _M['lav_leaf'] = S("LeafLavender", 'lanceolate', (0.36, 0.44, 0.34, 1), (0.44, 0.52, 0.42, 1), (0.54, 0.60, 0.50, 1), translucent=0.3, rough=0.8,
                       coat=0.0, p=0.8, q=1.3, rib=0.0)
    _M['boxwood'] = _M['privet'] = _mat.leaf_card("LeafBoxwoodCl", (0.05, 0.14, 0.04, 1), (0.10, 0.24, 0.07, 1), (0.18, 0.33, 0.10, 1), 0.3, shape='cluster', rough=0.45)
    _M['hedge'] = _mat.leaf_card("LeafHedgeCl", (0.04, 0.12, 0.04, 1), (0.09, 0.22, 0.06, 1), (0.16, 0.30, 0.09, 1), 0.28, shape='cluster', rough=0.5)
    for k in ('boxwood', 'hedge'):
        m = _M[k]; nt = m.node_tree
        for n in list(nt.nodes):
            if n.type == 'OBJECT_INFO':
                at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_name = "leaf_rnd"
                for l in list(n.outputs["Random"].links):
                    nt.links.new(l.to_socket, at.outputs["Fac"])
                nt.nodes.remove(n)
    F = flower_shader
    _M['rose_pink'] = F("FlowerRosePink", 'rose', (0.80, 0.22, 0.36, 1), (0.98, 0.72, 0.78, 1))
    _M['rose_white'] = F("FlowerRoseWhite", 'rose', (0.92, 0.82, 0.55, 1), (0.98, 0.96, 0.92, 1))
    _M['hyd_blue'] = F("FlowerHydBlue", 'ball', (0.40, 0.45, 0.80, 1), (0.62, 0.66, 0.92, 1), (0.80, 0.72, 0.92, 1))
    _M['hyd_white'] = F("FlowerHydWhite", 'ball', (0.86, 0.90, 0.78, 1), (0.96, 0.96, 0.94, 1), (0.98, 0.95, 0.90, 1))
    _M['agap_blue'] = F("FlowerAgapanthus", 'ball', (0.30, 0.36, 0.78, 1), (0.50, 0.56, 0.90, 1), (0.66, 0.70, 0.95, 1))
    _M['lav_spike'] = F("FlowerLavender", 'spike', (0.42, 0.28, 0.66, 1), (0.60, 0.45, 0.82, 1))
    _M['oleander_white'] = F("FlowerOleanderW", 'flat5', (0.96, 0.94, 0.86, 1), (0.99, 0.98, 0.96, 1))
    _M['oleander_pink'] = F("FlowerOleanderP", 'flat5', (0.90, 0.45, 0.60, 1), (0.98, 0.78, 0.84, 1))
    _M['citrus_bloom'] = F("FlowerCitrus", 'flat5', (0.98, 0.96, 0.90, 1), (1.0, 0.99, 0.97, 1))
    # pots, soil, stems, fruit
    _M['terracotta'] = _mat.noise_mat("PotTerracotta", (0.58, 0.32, 0.20, 1), (0.72, 0.44, 0.30, 1), scale=18, bump=0.25, rough=0.85, spec=0.25)
    _M['ceramic'] = _mat.new_mat("PotCeramicWhite", (0.90, 0.89, 0.85, 1), rough=0.25, coat=0.5)
    _M['ceramic_black'] = _mat.new_mat("PotCeramicBlack", (0.05, 0.05, 0.05, 1), rough=0.4, coat=0.3)
    _M['concrete'] = _mat.noise_mat("PotConcrete", (0.52, 0.51, 0.48, 1), (0.66, 0.65, 0.61, 1), scale=30, bump=0.3, rough=0.9, spec=0.2)
    _M['basket'] = _mat.wood("PotBasket", light=(0.72, 0.56, 0.34, 1), dark=(0.50, 0.36, 0.20, 1), grain_axis='Z', scale=12.0, rough=0.9, coat=0.0)
    _M['soil'] = _mat.noise_mat("PotSoil", (0.05, 0.035, 0.025, 1), (0.14, 0.10, 0.07, 1), scale=90, bump=0.6, rough=1.0, spec=0.05)
    _M['stem'] = _mat.noise_mat("PlantStem", (0.16, 0.24, 0.10, 1), (0.28, 0.36, 0.16, 1), scale=40, bump=0.2, rough=0.7, spec=0.2)
    _M['bark'] = _mat.noise_mat("PlantBark", (0.30, 0.25, 0.20, 1), (0.48, 0.42, 0.34, 1), scale=25, bump=0.5, rough=0.9, spec=0.1)
    _M['cane'] = _mat.noise_mat("PlantCane", (0.16, 0.13, 0.09, 1), (0.30, 0.25, 0.17, 1), scale=30, bump=0.4, rough=0.85, spec=0.1)
    _M['lemon'] = _mat.noise_mat("FruitLemon", (0.92, 0.78, 0.12, 1), (0.98, 0.88, 0.25, 1), scale=60, bump=0.35, rough=0.45, spec=0.5)
    return _M


# ------------------------------------------------------------------ geometry helpers
def _unit(v):
    v = Vector(v)
    return v.normalized() if v.length > 1e-9 else Vector((0, 0, 1))


def _perp(d, rng=None, az=None):
    """A unit vector perpendicular to d (random azimuth about d unless given)."""
    d = _unit(d)
    ref = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0))
    n1 = d.cross(ref).normalized(); n2 = d.cross(n1).normalized()
    a = rng.uniform(0, 2 * math.pi) if az is None else az
    return n1 * math.cos(a) + n2 * math.sin(a)


def _rot(v, axis, ang):
    axis = _unit(axis)
    return v * math.cos(ang) + axis.cross(v) * math.sin(ang) + axis * axis.dot(v) * (1 - math.cos(ang))


class Foliage:
    """Accumulates stems (MB tubes) and leaf / flower quads keyed by material; build() writes `name` + `name_Leaves`."""

    def __init__(self, seed=0):
        self.rng = random.Random(seed)
        self.wood = MB()
        self.quads = {}
        self.n = 0

    def _q(self, key, a, b, c, d, u0, u1, rnd):
        self.quads.setdefault(key, []).append((tuple(a), tuple(b), tuple(c), tuple(d), u0, u1, rnd))
        self.n += 1

    def leaf(self, key, base, along, side, L, W, n=3, droop=0.0, twist=0.0, rnd=None, up_normal=True):
        """One blade from `base` along `along`, width axis `side` (both unit), n quads; `droop` = angle (rad) the tip
        has bent toward gravity, `twist` = roll (rad) of the blade along its length."""
        rng = self.rng
        rnd = rng.random() if rnd is None else rnd
        d0 = _unit(along); s0 = _unit(side)
        s0 = (s0 - d0 * s0.dot(d0)).normalized()
        nrm = d0.cross(s0)
        # Quad winding below is side.cross(along), the opposite of nrm.
        # Keep the actual face normal upward so leaf tops receive the green shader.
        if up_normal and nrm.z > 0:
            s0 = -s0; nrm = -nrm
        p = Vector(base)
        prev_edge = (p - s0 * (W / 2), p + s0 * (W / 2))
        for i in range(n):
            f1 = ((i + 1) / n) ** 1.4
            d = _rot(d0, s0, droop * f1) if droop else d0
            s = _rot(s0, d, twist * (i + 1) / n) if twist else s0
            q = p + d * (L / n)
            e = (q - s * (W / 2), q + s * (W / 2))
            self._q(key, prev_edge[0], prev_edge[1], e[1], e[0], i / n, (i + 1) / n, rnd)
            p, prev_edge = q, e

    def card(self, key, pos, normal, size, aspect=1.0, rnd=None):
        """A single square card (cluster leaves / flowers) at pos facing `normal` with a random roll."""
        rng = self.rng
        n = _unit(normal)
        u = _perp(n, rng); v = n.cross(u).normalized()
        c = Vector(pos); su, sv = size / 2, size * aspect / 2
        self._q(key, c - u * su - v * sv, c + u * su - v * sv, c + u * su + v * sv, c - u * su + v * sv, 0.0, 1.0, rng.random() if rnd is None else rnd)

    def clump(self, key, c, R, size, cov=1.1, up_bias=0.3, flat=0.2, shell=0.4, cap=600):
        """Shell of cards around c (radius R) - a boxwood ball, a hedge lump, a flower head."""
        rng = self.rng
        n = int(min(cap, max(4, cov * 4 * math.pi * R * R / (size * size * 0.5))))
        for i in range(n):
            v = Vector((rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1) + up_bias)).normalized()
            u = rng.random() ** shell
            pos = Vector(c) + Vector((v.x * R, v.y * R, v.z * R * (1 - flat))) * u
            nrm = (v + Vector((rng.gauss(0, 0.5), rng.gauss(0, 0.5), rng.gauss(0, 0.5)))).normalized()
            self.card(key, pos, nrm, size * rng.uniform(0.7, 1.35))

    def stem(self, pts, r0, r1=None, seg=6, mi=2):
        self.wood.path_tube(pts, r0, seg=seg, mi=mi) if r1 is None else self.wood.tube(pts[0], pts[-1], r0, r1, seg=seg, mi=mi)

    def arc(self, p, d, L, r0, r1, n=4, gravity=0.35, wiggle=0.06, mi=2, seg=6):
        """A gently arching stem; returns its points and the final direction."""
        rng = self.rng
        pts, cur, dir_ = [Vector(p)], Vector(p), _unit(d)
        for i in range(n):
            dir_ = (dir_ + Vector((rng.gauss(0, wiggle), rng.gauss(0, wiggle), -gravity * (i + 1) / n))).normalized()
            cur = cur + dir_ * (L / n)
            pts.append(cur.copy())
        radii = [r0 + (r1 - r0) * k / n for k in range(n + 1)]
        self.wood.sweep(_sections(pts, radii, seg), mi)
        return pts, dir_

    def build(self, name, wood_mats, coll='House', smooth=True):
        MM = mats()
        ob = None
        if self.wood.v:
            ob = self.wood.build(name, wood_mats, coll=coll, smooth=smooth)
        keys = [k for k in self.quads if self.quads[k]]
        if not keys:
            return ob
        mb = MB(); rnds = []; uvs = []
        for mi, k in enumerate(keys):
            for (a, b, c, d, u0, u1, rnd) in self.quads[k]:
                mb.quad(a, b, c, d, mi); rnds.append(rnd); uvs.append((u0, u1))
        lv = mb.build(name + "_Leaves", [MM[k] for k in keys], coll=coll, recalc=False)
        me = lv.data
        uv = me.uv_layers.new(name="UVMap"); uvd = uv.data
        for pi, poly in enumerate(me.polygons):
            u0, u1 = uvs[pi]
            cs = ((u0, 0.0), (u0, 1.0), (u1, 1.0), (u1, 0.0))
            for j, li in enumerate(poly.loop_indices):
                uvd[li].uv = cs[j]
        at = me.attributes.new("leaf_rnd", 'FLOAT', 'FACE')
        at.data.foreach_set("value", rnds)
        if ob is not None:
            lv.parent = ob
            lv.matrix_parent_inverse = ob.matrix_world.inverted()
        return ob or lv


# ------------------------------------------------------------------ pots
POT_STYLES = {'terracotta': 'terracotta', 'ceramic': 'ceramic', 'white': 'ceramic', 'black': 'ceramic_black',
              'concrete': 'concrete', 'basket': 'basket'}


def pot(F, x, y, z, r, h, style='terracotta', mi=0, mi_soil=1, saucer=True):
    """Planter at (x, y, z): tapered body, rolled rim, hollow top with soil 4 cm below the rim; returns the soil z."""
    mb = F.wood if isinstance(F, Foliage) else F
    rb = r * (0.74 if style in ('terracotta', 'basket') else 0.86)
    if style == 'basket':
        prof = [(0, 0), (rb, 0), (r * 1.02, h * 0.45), (r, h * 0.92), (r * 1.04, h), (r * 0.9, h), (r * 0.9, h - 0.05), (0, h - 0.05)]
    elif style == 'concrete':
        prof = [(0, 0), (rb, 0), (r, h * 0.12), (r, h), (r * 0.82, h), (r * 0.82, h - 0.05), (0, h - 0.05)]
    else:
        prof = [(0, 0), (rb, 0), (rb * 1.02, 0.02), (r * 0.98, h - 0.07), (r * 1.06, h - 0.07), (r * 1.06, h), (r * 0.9, h), (r * 0.9, h - 0.05), (0, h - 0.05)]
    mb.lathe(x, y, z, prof, seg=28, mi=mi)
    if saucer:
        mb.lathe(x, y, z - 0.004, [(0, 0), (rb * 1.12, 0), (rb * 1.2, 0.022), (rb * 1.1, 0.022), (rb * 1.05, 0.008), (0, 0.008)], seg=28, mi=mi)
    zs = z + h - 0.045
    mb.lathe(x, y, zs - 0.01, [(0, 0), (r * 0.91, 0), (r * 0.88, 0.012), (r * 0.5, 0.02), (0, 0.016)], seg=20, mi=mi_soil)
    return zs


_POT_FN = pot


# ------------------------------------------------------------------ species (all take the Foliage, the soil point and a height)
def _fiddle(F, x, y, z, h, spread=1.0):
    rng = F.rng
    pts = [Vector((x, y, z - 0.03))]
    lean = Vector((rng.uniform(-0.05, 0.05), rng.uniform(-0.05, 0.05), 0))
    for k in range(1, 6):
        t = k / 5
        pts.append(Vector((x + lean.x * t * h + rng.uniform(-0.012, 0.012), y + lean.y * t * h + rng.uniform(-0.012, 0.012), z + h * t)))
    from .trees import _sections
    F.wood.sweep(_sections(pts, [0.02, 0.018, 0.016, 0.013, 0.011, 0.008], 8), 2)
    n = 10 + int(h * 7)
    ga = math.radians(137.5)
    for i in range(n):
        t = 0.32 + 0.66 * i / (n - 1)
        k = min(len(pts) - 2, int(t * 5)); f = t * 5 - k
        p = pts[k].lerp(pts[k + 1], f)
        az = i * ga + rng.uniform(-0.25, 0.25)
        young = t > 0.88
        L = (0.30 if not young else 0.17) * rng.uniform(0.8, 1.15) * (h / 1.6) ** 0.35
        W = L * rng.uniform(0.62, 0.78)
        out = Vector((math.cos(az), math.sin(az), 0))
        el = rng.uniform(0.25, 0.6) if not young else rng.uniform(0.6, 1.1)
        d = (out * math.cos(el) + Vector((0, 0, 1)) * math.sin(el)).normalized()
        pet = p + d * 0.05
        F.wood.tube(tuple(p), tuple(pet), 0.004, 0.003, seg=5, mi=2)
        side = out.cross(Vector((0, 0, 1))).normalized()
        F.leaf('fiddle', pet, d, side, L, W * spread, n=3, droop=rng.uniform(0.55, 0.95))


def _monstera(F, x, y, z, h, spread=1.0):
    rng = F.rng
    F.wood.cylinder(x, y, z - 0.02, z + 0.12, 0.03, 0.025, seg=10, mi=2)
    n = 6 + int(h * 3)
    for i in range(n):
        az = 2 * math.pi * i / n + rng.uniform(-0.35, 0.35)
        out = Vector((math.cos(az), math.sin(az), 0))
        el = rng.uniform(0.7, 1.25) - 0.35 * (i % 3 == 0)
        L_p = h * rng.uniform(0.45, 0.9)
        d = (out * math.cos(el) + Vector((0, 0, 1)) * math.sin(el)).normalized()
        pts, dend = F.arc((x + out.x * 0.02, y + out.y * 0.02, z + 0.08), d, L_p, 0.009, 0.006, n=3, gravity=0.15, wiggle=0.05)
        L = rng.uniform(0.32, 0.48) * (h / 1.2) ** 0.4 * spread
        side = out.cross(Vector((0, 0, 1))).normalized()
        bd = (dend + Vector((0, 0, -0.35))).normalized()
        F.leaf('monstera', pts[-1], bd, side, L, L * 0.92, n=3, droop=rng.uniform(0.25, 0.55))


def _bird(F, x, y, z, h, spread=1.0):
    rng = F.rng
    n = 7 + int(h * 2)
    base_az = rng.uniform(0, math.pi)
    for i in range(n):
        az = base_az + (i % 2) * math.pi + rng.uniform(-0.55, 0.55)          # two ranks (fan)
        out = Vector((math.cos(az), math.sin(az), 0))
        el = rng.uniform(1.05, 1.42)
        d = (out * math.cos(el) + Vector((0, 0, 1)) * math.sin(el)).normalized()
        Lp = h * rng.uniform(0.45, 0.72)
        pts, dend = F.arc((x + out.x * 0.04, y + out.y * 0.04, z - 0.02), d, Lp, 0.014, 0.008, n=3, gravity=0.12, wiggle=0.03)
        L = h * rng.uniform(0.34, 0.5) * spread
        W = L * rng.uniform(0.3, 0.4)
        side = out.cross(Vector((0, 0, 1))).normalized()
        F.leaf('bird', pts[-1], dend, side, L, W, n=4, droop=rng.uniform(0.6, 1.1), twist=rng.uniform(-0.25, 0.25))


def _fern(F, x, y, z, h, spread=1.0):
    rng = F.rng
    n = 26 + int(h * 24)
    for i in range(n):
        az = rng.uniform(0, 2 * math.pi)
        out = Vector((math.cos(az), math.sin(az), 0))
        el = rng.uniform(0.35, 1.35)
        d = (out * math.cos(el) + Vector((0, 0, 1)) * math.sin(el)).normalized()
        L = h * rng.uniform(0.7, 1.25) * spread
        W = L * rng.uniform(0.24, 0.32)
        side = out.cross(Vector((0, 0, 1))).normalized()
        F.leaf('fern', (x + out.x * 0.03, y + out.y * 0.03, z), d, side, L, W, n=4, droop=rng.uniform(1.0, 1.7), twist=rng.uniform(-0.3, 0.3))


def _palm(F, x, y, z, h, spread=1.0):
    rng = F.rng
    n_st = 1 if h < 1.2 else rng.randint(2, 3)
    for s in range(n_st):
        ox, oy = (0.0, 0.0) if n_st == 1 else (rng.uniform(-0.08, 0.08), rng.uniform(-0.08, 0.08))
        hs = h * rng.uniform(0.5, 0.62) * (1.0 if s == 0 else rng.uniform(0.7, 1.0))
        lean = Vector((rng.uniform(-0.12, 0.12), rng.uniform(-0.12, 0.12), 1)).normalized()
        top = Vector((x + ox, y + oy, z - 0.02)) + lean * hs
        F.wood.tube((x + ox, y + oy, z - 0.02), tuple(top), 0.02, 0.012, seg=7, mi=2)
        nf = rng.randint(5, 7)
        for i in range(nf):
            az = 2 * math.pi * i / nf + rng.uniform(-0.3, 0.3)
            out = Vector((math.cos(az), math.sin(az), 0))
            el = rng.uniform(0.35, 1.0)
            d = (out * math.cos(el) + Vector((0, 0, 1)) * math.sin(el)).normalized()
            L = (h - hs) * rng.uniform(1.3, 1.9) * spread
            W = L * rng.uniform(0.3, 0.38)
            side = out.cross(Vector((0, 0, 1))).normalized()
            F.wood.tube(tuple(top), tuple(top + d * 0.08), 0.009, 0.006, seg=5, mi=2)
            F.leaf('palm', top + d * 0.08, d, side, L, W, n=5, droop=rng.uniform(0.9, 1.4), twist=rng.uniform(-0.2, 0.2))


def _snake(F, x, y, z, h, spread=1.0):
    rng = F.rng
    n = 10 + int(h * 9)
    for i in range(n):
        az = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(0.0, 0.09) * spread
        px, py = x + r * math.cos(az), y + r * math.sin(az)
        L = h * rng.uniform(0.5, 1.0)
        W = rng.uniform(0.055, 0.085)
        lean = rng.uniform(0.04, 0.2)
        out = Vector((math.cos(az), math.sin(az), 0))
        d = (Vector((0, 0, 1)) + out * lean).normalized()
        side = _perp(d, None, az + math.pi / 2)
        F.leaf('snake', (px, py, z - 0.01), d, side, L, W, n=4, droop=rng.uniform(0.0, 0.25), twist=rng.uniform(-0.7, 0.7), up_normal=False)


def _boxwood(F, x, y, z, h, spread=1.0, key='boxwood'):
    R = h * 0.5 * spread
    c = (x, y, z + h * 0.5)
    F.wood.blob(c, R * 0.72, seg=10, rings=7, jitter=0.3, seed=F.rng.randint(0, 999), mi=3, squash=0.95)
    F.clump(key, c, R, 0.07 * (0.8 + h * 0.4), cov=1.3, up_bias=0.2, flat=0.08, shell=0.3, cap=900)
    F.wood.tube((x, y, z - 0.02), (x, y, z + h * 0.3), 0.02, 0.014, seg=6, mi=2)


def _citrus(F, x, y, z, h, spread=1.0):
    rng = F.rng
    ht = h * 0.42
    pts = [Vector((x, y, z - 0.03)), Vector((x + rng.uniform(-0.02, 0.02), y + rng.uniform(-0.02, 0.02), z + ht * 0.5)), Vector((x, y, z + ht))]
    F.wood.sweep(_sections(pts, [0.024, 0.02, 0.016], 8), 2)
    nb = rng.randint(4, 6)
    tips = []
    for i in range(nb):
        az = 2 * math.pi * i / nb + rng.uniform(-0.4, 0.4)
        out = Vector((math.cos(az), math.sin(az), 0))
        d = (out * 0.75 + Vector((0, 0, rng.uniform(0.5, 1.0)))).normalized()
        p2, dend = F.arc(pts[-1], d, (h - ht) * 0.55, 0.012, 0.006, n=3, gravity=0.1, wiggle=0.12)
        tips.append(p2[-1])
        for k in range(rng.randint(2, 3)):
            d2 = (dend + _perp(dend, rng) * rng.uniform(0.6, 1.2)).normalized()
            p3, _ = F.arc(p2[-1], d2, (h - ht) * 0.3, 0.006, 0.003, n=2, gravity=0.15, wiggle=0.15)
            tips.append(p3[-1])
    R = h * 0.36 * spread
    c = Vector((x, y, z + ht + (h - ht) * 0.55))
    n = int(260 + 320 * h)
    for i in range(n):
        v = Vector((rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1) * 0.9)).normalized()
        u = rng.random() ** 0.45
        p = c + Vector((v.x * R, v.y * R, v.z * R * 0.9)) * u
        d = (v + Vector((rng.gauss(0, 0.5), rng.gauss(0, 0.5), rng.gauss(0, 0.5) - 0.25))).normalized()
        side = _perp(d, rng)
        L = rng.uniform(0.06, 0.095)
        F.leaf('citrus', p, d, side, L, L * 0.5, n=1)
    for i in range(rng.randint(5, 9) + int(h * 2)):
        v = Vector((rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1) - 0.3)).normalized()
        p = c + Vector((v.x * R, v.y * R, v.z * R * 0.9)) * rng.uniform(0.55, 0.95)
        F.wood.blob(tuple(p), rng.uniform(0.03, 0.04), seg=10, rings=7, jitter=0.08, seed=i, mi=3, squash=1.15)
    for i in range(rng.randint(4, 8)):
        v = Vector((rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1) + 0.2)).normalized()
        p = c + Vector((v.x * R, v.y * R, v.z * R * 0.9)) * rng.uniform(0.85, 1.05)
        F.card('citrus_bloom', p, v, 0.03)


def _lavender(F, x, y, z, h, spread=1.0, spikes=True):
    rng = F.rng
    n = 26 + int(h * 40)
    for i in range(n):
        az = rng.uniform(0, 2 * math.pi)
        out = Vector((math.cos(az), math.sin(az), 0))
        el = rng.uniform(0.5, 1.3)
        d = (out * math.cos(el) + Vector((0, 0, 1)) * math.sin(el)).normalized()
        L = h * rng.uniform(0.55, 0.85)
        pts, dend = F.arc((x + out.x * 0.03, y + out.y * 0.03, z), d, L, 0.003, 0.0015, n=3, gravity=0.1, wiggle=0.08, seg=4)
        for k in range(6):
            t = 0.25 + 0.75 * k / 6
            kk = min(len(pts) - 2, int(t * 3)); f = t * 3 - kk
            p = pts[kk].lerp(pts[kk + 1], f)
            for sgn in (1, -1):
                dd = (dend * 0.5 + _perp(dend, rng) * sgn * 0.8).normalized()
                F.leaf('lav_leaf', p, dd, _perp(dd, rng), rng.uniform(0.035, 0.055), 0.008, n=1, up_normal=False)
        if spikes and rng.random() < 0.7:
            sp = (dend + Vector((0, 0, 0.6))).normalized()
            F.wood.tube(tuple(pts[-1]), tuple(pts[-1] + sp * 0.12), 0.0015, 0.001, seg=4, mi=2)
            F.card('lav_spike', pts[-1] + sp * 0.16, _perp(sp, rng), 0.09, aspect=0.35)


def _hydrangea(F, x, y, z, h, spread=1.0, colour='hyd_white'):
    rng = F.rng
    n = 7 + int(h * 6)
    R = h * 0.75 * spread
    for i in range(n):
        az = 2 * math.pi * i / n + rng.uniform(-0.3, 0.3)
        out = Vector((math.cos(az), math.sin(az), 0))
        d = (out * rng.uniform(0.3, 0.8) + Vector((0, 0, 1))).normalized()
        L = h * rng.uniform(0.75, 1.0)
        pts, dend = F.arc((x + out.x * 0.06, y + out.y * 0.06, z - 0.03), d, L, 0.006, 0.004, n=3, gravity=0.15, wiggle=0.06, seg=5)
        for k in range(rng.randint(8, 12)):
            t = 0.25 + 0.7 * rng.random()
            kk = min(len(pts) - 2, int(t * 3)); f = t * 3 - kk
            p = pts[kk].lerp(pts[kk + 1], f)
            dd = (_perp(dend, rng) * 0.8 + dend * 0.3 + Vector((0, 0, -0.2))).normalized()
            Ll = rng.uniform(0.10, 0.15)
            F.leaf('hyd_leaf', p, dd, _perp(dd, rng), Ll, Ll * 0.72, n=2, droop=0.4)
        if rng.random() < 0.9:
            c = pts[-1] + dend * 0.05
            F.clump(colour, c, rng.uniform(0.07, 0.10), 0.05, cov=1.8, up_bias=0.1, flat=0.0, shell=0.5, cap=140)


def _agapanthus(F, x, y, z, h, spread=1.0):
    rng = F.rng
    n = 16 + int(h * 14)
    for i in range(n):
        az = rng.uniform(0, 2 * math.pi)
        out = Vector((math.cos(az), math.sin(az), 0))
        el = rng.uniform(0.35, 1.1)
        d = (out * math.cos(el) + Vector((0, 0, 1)) * math.sin(el)).normalized()
        L = h * rng.uniform(0.35, 0.55) * spread
        F.leaf('agap_leaf', (x + out.x * 0.04, y + out.y * 0.04, z - 0.01), d, out.cross(Vector((0, 0, 1))).normalized(), L, rng.uniform(0.03, 0.045), n=4,
               droop=rng.uniform(0.6, 1.3), twist=rng.uniform(-0.3, 0.3))
    for i in range(rng.randint(3, 6)):
        az = rng.uniform(0, 2 * math.pi)
        out = Vector((math.cos(az), math.sin(az), 0))
        d = (Vector((0, 0, 1)) + out * rng.uniform(0.05, 0.25)).normalized()
        top = Vector((x, y, z)) + d * h * rng.uniform(0.85, 1.0)
        F.wood.tube((x, y, z), tuple(top), 0.006, 0.004, seg=5, mi=2)
        F.clump('agap_blue', top, rng.uniform(0.06, 0.09), 0.05, cov=1.4, up_bias=0.0, flat=0.0, shell=0.5, cap=80)


def _rose(F, x, y, z, h, spread=1.0, colour='rose_pink'):
    rng = F.rng
    n = rng.randint(4, 6)
    for i in range(n):
        az = 2 * math.pi * i / n + rng.uniform(-0.4, 0.4)
        out = Vector((math.cos(az), math.sin(az), 0))
        d = (out * rng.uniform(0.45, 0.9) + Vector((0, 0, 1))).normalized()
        pts, dend = F.arc((x + out.x * 0.05, y + out.y * 0.05, z - 0.03), d, h * rng.uniform(0.6, 0.85), 0.008, 0.005, n=3, gravity=0.1, wiggle=0.12, seg=5, mi=4)
        branches = [(pts, dend)]
        for k in range(rng.randint(3, 5)):
            t = rng.uniform(0.35, 0.95)
            kk = min(len(pts) - 2, int(t * 3)); f = t * 3 - kk
            p = pts[kk].lerp(pts[kk + 1], f)
            d2 = (dend * 0.5 + _perp(dend, rng) * 0.7 + Vector((0, 0, 0.5))).normalized()
            p2, dd2 = F.arc(p, d2, h * rng.uniform(0.3, 0.5) * spread, 0.004, 0.0025, n=2, gravity=0.1, wiggle=0.15, seg=4, mi=4)
            branches.append((p2, dd2))
        for (bp, bd) in branches:
            for k in range(rng.randint(5, 8)):
                t = rng.uniform(0.15, 1.0)
                kk = min(len(bp) - 2, int(t * (len(bp) - 1))); f = t * (len(bp) - 1) - kk
                p = bp[kk].lerp(bp[kk + 1], f)
                ld = (_perp(bd, rng) * 0.85 + bd * 0.3 + Vector((0, 0, -0.15))).normalized()
                lside = _perp(ld, rng)
                for j in range(5):                                     # compound leaf: 5 leaflets along a rachis
                    lp = p + ld * (0.025 * (j // 2 + (1 if j == 4 else 0)))
                    sgn = 1 if j % 2 == 0 else -1
                    lj = (ld * 0.6 + lside * sgn * 0.7).normalized() if j < 4 else ld
                    F.leaf('rose_leaf', lp, lj, _perp(lj, rng), rng.uniform(0.035, 0.05), 0.026, n=1)
            if rng.random() < 0.85:
                tip = bp[-1]
                fd = (bd + Vector((0, 0, 0.5))).normalized()
                F.wood.tube(tuple(tip), tuple(tip + fd * 0.03), 0.002, 0.002, seg=4, mi=4)
                F.card(colour, tip + fd * 0.05, fd, rng.uniform(0.07, 0.095))
                if rng.random() < 0.5:                                  # a second bloom / bud beside it
                    fd2 = (fd + _perp(fd, rng) * 0.6).normalized()
                    F.card(colour, tip + fd2 * 0.06, fd2, rng.uniform(0.045, 0.07))


def _oleander(F, x, y, z, h, spread=1.0, colour='oleander_white'):
    rng = F.rng
    n = 12 + int(h * 5)
    for i in range(n):
        az = 2 * math.pi * i / n + rng.uniform(-0.3, 0.3)
        out = Vector((math.cos(az), math.sin(az), 0))
        d = (out * rng.uniform(0.15, 0.6) * spread + Vector((0, 0, 1))).normalized()
        L = h * rng.uniform(0.55, 1.0)
        pts, dend = F.arc((x + out.x * 0.12, y + out.y * 0.12, z - 0.05), d, L, 0.016, 0.006, n=4, gravity=0.08, wiggle=0.08, seg=6, mi=4)
        for k in range(rng.randint(5, 8)):
            t = rng.uniform(0.15, 0.95)
            kk = min(len(pts) - 2, int(t * 4)); f = t * 4 - kk
            p = pts[kk].lerp(pts[kk + 1], f)
            d2 = (dend * 0.45 + _perp(dend, rng) * 0.75 + Vector((0, 0, 0.35))).normalized()
            p2, dd2 = F.arc(p, d2, L * rng.uniform(0.25, 0.45), 0.005, 0.003, n=2, gravity=0.05, wiggle=0.1, seg=4, mi=4)
            for j in range(rng.randint(18, 26)):
                tt = rng.uniform(0.1, 1.0)
                q = p2[0].lerp(p2[-1], tt)
                ld = (dd2 * 0.35 + _perp(dd2, rng) * 0.85 + Vector((0, 0, -0.25))).normalized()
                Ll = rng.uniform(0.09, 0.14)
                F.leaf('oleander_leaf', q, ld, _perp(ld, rng), Ll, Ll * 0.2, n=1)
            if rng.random() < 0.85:
                F.clump(colour, p2[-1] + dd2 * 0.05, rng.uniform(0.07, 0.11), 0.055, cov=1.6, up_bias=0.2, flat=0.1, shell=0.5, cap=70)
        for j in range(rng.randint(16, 24)):
            tt = rng.uniform(0.15, 1.0)
            kk = min(len(pts) - 2, int(tt * 4)); f = tt * 4 - kk
            q = pts[kk].lerp(pts[kk + 1], f)
            ld = (dend * 0.3 + _perp(dend, rng) * 0.85 + Vector((0, 0, -0.2))).normalized()
            Ll = rng.uniform(0.09, 0.14)
            F.leaf('oleander_leaf', q, ld, _perp(ld, rng), Ll, Ll * 0.2, n=1)


def _olive_pot(name, x, y, z, h, seed, coll):
    from . import trees as _tr
    L = _tr.leaf_materials()
    MM = mats()
    return _tr.olive(name + "_Tree", (x, y, z + 0.06), height=h, seed=seed, detail=1.0, coll=coll,
                     mats={'bark': MM['bark'], 'leaf': L['olive'], 'core': L['core_holey']})


SPECIES = {'fiddle': _fiddle, 'monstera': _monstera, 'bird': _bird, 'fern': _fern, 'palm': _palm, 'snake': _snake,
           'boxwood': _boxwood, 'citrus': _citrus, 'lavender': _lavender, 'hydrangea': _hydrangea, 'agapanthus': _agapanthus,
           'rose': _rose, 'oleander': _oleander}
# sensible pot sizes (radius, height) per species at height 1.0 (scaled by height^0.5)
_POT = {'fiddle': (0.20, 0.30), 'monstera': (0.22, 0.30), 'bird': (0.24, 0.34), 'fern': (0.17, 0.20), 'palm': (0.22, 0.32),
        'snake': (0.14, 0.24), 'olive': (0.24, 0.34), 'boxwood': (0.20, 0.26), 'citrus': (0.26, 0.36), 'lavender': (0.19, 0.22),
        'rosemary': (0.19, 0.22), 'hydrangea': (0.22, 0.26), 'agapanthus': (0.20, 0.26), 'rose': (0.22, 0.30)}


def potted(name, pos, kind='fiddle', height=1.5, pot='terracotta', pot_r=None, pot_h=None, seed=0, coll='House', spread=1.0, saucer=True):
    """A potted plant standing on the floor at pos = (x, y, z_floor).  `height` = plant height above the soil.
    Returns the pot object (the leaves are `<name>_Leaves`, parented to it)."""
    MM = mats()
    x, y, z = pos
    F = Foliage(seed)
    pr, ph = _POT.get(kind, (0.2, 0.28))
    sc = max(0.5, height) ** 0.45
    pr = pot_r or pr * sc
    ph = pot_h or ph * sc
    style = POT_STYLES.get(pot, 'terracotta')
    zs = _POT_FN(F, x, y, z, pr, ph, style, 0, 1, saucer)
    green = kind in ('fern', 'snake', 'agapanthus', 'lavender', 'rosemary', 'monstera', 'bird', 'hydrangea')
    slots = [MM[style], MM['soil'], MM['stem'] if green else MM['bark'], MM['lemon'] if kind == 'citrus' else _core_mat(), MM['cane']]
    if kind == 'olive':
        ob = F.build(name, slots, coll=coll)
        _olive_pot(name, x, y, zs, height, seed, coll)
        return ob
    fn = SPECIES.get('lavender' if kind == 'rosemary' else kind)
    if fn is None:
        raise KeyError(f"plants.potted: unknown kind {kind!r} (have {sorted(SPECIES)} + olive / rosemary)")
    if kind == 'rosemary':
        fn(F, x, y, zs, height, spread, spikes=False)
    else:
        fn(F, x, y, zs, height, spread)
    return F.build(name, slots, coll=coll)


def _core_mat():
    return _tree_leaf_mats()['core']


def stems(name, pos, kind='eucalyptus', height=0.8, n=None, seed=0, coll='House', spread=1.0):
    """Cut stems standing in a vase whose mouth is at pos = (x, y, z_mouth): eucalyptus (round silver leaves),
    olive (lanceolate grey-green), magnolia (big glossy leaves, rust underside), or bare 'branches'."""
    MM = mats()
    x, y, z = pos
    F = Foliage(seed)
    rng = F.rng
    n = n or {'eucalyptus': 5, 'olive': 6, 'magnolia': 3, 'branches': 7}.get(kind, 5)
    for i in range(n):
        az = 2 * math.pi * i / n + rng.uniform(-0.5, 0.5)
        out = Vector((math.cos(az), math.sin(az), 0))
        d = (Vector((0, 0, 1)) + out * rng.uniform(0.15, 0.55) * spread).normalized()
        L = height * rng.uniform(0.7, 1.05)
        pts, dend = F.arc((x + out.x * 0.02, y + out.y * 0.02, z - 0.08), d, L, 0.004, 0.0025, n=4, gravity=0.18 if kind != 'branches' else 0.05,
                          wiggle=0.08, seg=5, mi={'magnolia': 4, 'branches': 3}.get(kind, 2))
        if kind == 'branches':
            for k in range(rng.randint(2, 4)):
                t = rng.uniform(0.4, 0.95)
                kk = min(len(pts) - 2, int(t * 4)); f = t * 4 - kk
                p = pts[kk].lerp(pts[kk + 1], f)
                d2 = (dend * 0.6 + _perp(dend, rng) * 0.6 + Vector((0, 0, 0.3))).normalized()
                F.arc(p, d2, L * rng.uniform(0.2, 0.4), 0.002, 0.001, n=2, gravity=0.05, wiggle=0.15, seg=4, mi=2)
            continue
        pitch = {'eucalyptus': 0.05, 'olive': 0.035, 'magnolia': 0.09}[kind]
        key = {'eucalyptus': 'euc', 'olive': 'olive_leaf', 'magnolia': 'magnolia'}[kind]
        m = int(L * 0.8 / pitch)
        for k in range(m):
            t = 0.2 + 0.8 * (k + 0.5) / m
            kk = min(len(pts) - 2, int(t * 4)); f = t * 4 - kk
            p = pts[kk].lerp(pts[kk + 1], f)
            roll = (k % 2) * (math.pi / 2) + rng.uniform(-0.3, 0.3)
            side = _perp(dend, None, roll)
            for sgn in (1, -1):
                if rng.random() < 0.1:
                    continue
                ang = rng.uniform(0.7, 1.2)
                ld = (dend * math.cos(ang) + side * sgn * math.sin(ang) + Vector((0, 0, -rng.uniform(0.0, 0.3)))).normalized()
                if kind == 'eucalyptus':
                    Ll = rng.uniform(0.035, 0.05); F.leaf(key, p, ld, _perp(ld, rng), Ll, Ll * 0.85, n=1)
                elif kind == 'olive':
                    Ll = rng.uniform(0.06, 0.09); F.leaf(key, p, ld, _perp(ld, rng), Ll, Ll * 0.2, n=1)
                else:
                    Ll = rng.uniform(0.12, 0.17); F.leaf(key, p, ld, _perp(ld, rng), Ll, Ll * 0.5, n=2, droop=0.35)
    return F.build(name, [MM['stem'], MM['soil'], MM['stem'], MM['bark'], MM['bark']], coll=coll)


def shrub(name, pos, r=0.6, h=None, kind='boxwood', seed=0, coll='Landscape', colour=None):
    """Garden shrub at pos = (x, y, z_ground).  kinds: boxwood / privet (clipped balls), rose, hydrangea, agapanthus,
    lavender, rosemary, oleander (2.5-4 m, flowering).  `colour` picks the flower material key."""
    MM = mats()
    x, y, z = pos
    h = h or (r * 1.6 if kind in ('boxwood', 'privet') else r * 1.4)
    F = Foliage(seed)
    if kind in ('boxwood', 'privet'):
        _boxwood(F, x, y, z, h, spread=r / (h * 0.5), key=kind)
    elif kind == 'rose':
        _rose(F, x, y, z, h, spread=r / (h * 0.6), colour=colour or 'rose_pink')
    elif kind == 'hydrangea':
        _hydrangea(F, x, y, z, h, spread=r / (h * 0.75), colour=colour or 'hyd_white')
    elif kind == 'agapanthus':
        _agapanthus(F, x, y, z, h, spread=r / (h * 0.5))
    elif kind in ('lavender', 'rosemary'):
        _lavender(F, x, y, z, h, spread=r / (h * 0.7), spikes=(kind == 'lavender'))
    elif kind == 'oleander':
        _oleander(F, x, y, z, h, spread=r / (h * 0.45), colour=colour or 'oleander_white')
    else:
        raise KeyError(f"plants.shrub: unknown kind {kind!r}")
    return F.build(name, [MM['terracotta'], MM['soil'], MM['stem'], _core_mat(), MM['cane']], coll=coll)


def hedge(name, x0, x1, y0, y1, z, h, kind='hedge', seed=0, coll='Landscape', size=0.075, cov=1.4):
    """Clipped hedge box: a dark core slab + leaf-cluster cards over the top and every side."""
    MM = mats()
    F = Foliage(seed); rng = F.rng
    ins = 0.06
    F.wood.box(x0 + ins, x1 - ins, y0 + ins, y1 - ins, z, z + h - ins, 3)
    faces = [((x0, x1), (y0, y0), 'y', -1), ((x0, x1), (y1, y1), 'y', 1), ((x0, x0), (y0, y1), 'x', -1), ((x1, x1), (y0, y1), 'x', 1)]
    area_side = 2 * (x1 - x0 + y1 - y0) * h
    n_side = int(cov * area_side / (size * size * 0.5))
    for i in range(n_side):
        (xa, xb), (ya, yb), ax, sg = faces[rng.randrange(4)]
        px = rng.uniform(xa, xb) if ax == 'y' else xa + sg * rng.uniform(-0.04, 0.03)
        py = rng.uniform(ya, yb) if ax == 'x' else ya + sg * rng.uniform(-0.04, 0.03)
        pz = z + rng.uniform(0.02, h - 0.02)
        nrm = Vector((sg if ax == 'x' else 0, sg if ax == 'y' else 0, 0)) + Vector((rng.gauss(0, 0.45), rng.gauss(0, 0.45), rng.gauss(0, 0.45)))
        F.card(kind, (px, py, pz), nrm, size * rng.uniform(0.7, 1.35))
    n_top = int(cov * (x1 - x0) * (y1 - y0) / (size * size * 0.5))
    for i in range(n_top):
        F.card(kind, (rng.uniform(x0, x1), rng.uniform(y0, y1), z + h + rng.uniform(-0.05, 0.03)),
               Vector((rng.gauss(0, 0.45), rng.gauss(0, 0.45), 1.0)), size * rng.uniform(0.7, 1.35))
    return F.build(name, [MM['terracotta'], MM['soil'], MM['stem'], _core_mat()], coll=coll, smooth=False)
