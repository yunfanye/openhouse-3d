"""Procedural trees (oaks, conifers, olives, shrubs) for any house's landscape module.

A tree = a recursive branching skeleton (trunk -> limbs -> secondaries -> twigs; tapered, gently curving tubes
with tropism) plus EXPLICIT leaf geometry: thousands of small quads ("leaf-cluster cards", alpha-cut materials)
hung around the twig ends, each with its own UV square and a per-face random value the card shader reads for
colour variation.  Near oaks use twig-spray cards (small alternate oval leaves); near olives skip cards entirely
and carry every leaf as its own quad on hundreds of thin drooping twigs (Tree.leafy_twig).  No smooth blob
cores on olives: the silhouette is made of leaves and the limbs stay visible through the crown.

Level of detail: `detail` in (0, 1] scales card counts, tube segment counts and branching depth; low-detail
trees use fewer, larger cards so the canopy still closes at 60-200 m.

Public: oak(), conifer(), olive(), shrub_cards(), leaf_materials(), add_haze().
"""
import math, random
import bpy
from mathutils import Vector
from .mesh import MB, collection
from . import materials as _mat

# ------------------------------------------------------------------ materials (local copies; materials.py is read-only)
_LEAF = {}


def _attr_random(m, name="leaf_rnd"):
    """Replace the Object Info -> Random driver in a copied leaf_card material by a per-face attribute so every card
    in one mesh gets its own tint."""
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type == 'OBJECT_INFO':
            at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_name = name
            for l in list(n.outputs["Random"].links):
                nt.links.new(l.to_socket, at.outputs["Fac"])
            nt.nodes.remove(n)
    return m


def _frond_card(name, c1=(0.025, 0.075, 0.03, 1), c2=(0.05, 0.13, 0.05, 1), c3=(0.12, 0.22, 0.08, 1), translucent=0.25):
    """Conifer spray on a unit quad: U runs base -> tip, V across.  A rachis with fine forward-angled side needles
    that shorten toward the tip; ragged; per-face random tint (attribute 'leaf_rnd')."""
    m, nt, b = _mat._new(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(sep.inputs["Vector"], tc.outputs["UV"])
    x = sep.outputs["X"]
    y = _mat._math(nt, 'SUBTRACT', sep.outputs["Y"], 0.5)
    ay = _mat._math(nt, 'ABSOLUTE', y)
    # half width: widest ~1/3 along, tapering to a point at the tip
    w = _mat._math(nt, 'MULTIPLY', _mat._math(nt, 'POWER', _mat._math(nt, 'SUBTRACT', 1.0, x, clamp=True), 0.7),
                   _mat._math(nt, 'POWER', _mat._math(nt, 'MULTIPLY', x, 3.0, clamp=True), 0.35))
    w = _mat._math(nt, 'MULTIPLY', w, 0.5)
    inside = _mat._math(nt, 'LESS_THAN', ay, w)
    # side needles: a comb along x, sheared forward by |y| so needles angle toward the tip (narrow gaps)
    comb = _mat._math(nt, 'FRACT', _mat._math(nt, 'ADD', _mat._math(nt, 'MULTIPLY', x, 24.0), _mat._math(nt, 'MULTIPLY', ay, 8.0)))
    needle = _mat._math(nt, 'GREATER_THAN', comb, 0.3)
    rachis = _mat._math(nt, 'LESS_THAN', ay, 0.03)
    shape = _mat._math(nt, 'MULTIPLY', inside, _mat._math(nt, 'ADD', needle, rachis, clamp=True))
    uvn = nt.nodes.new("ShaderNodeTexNoise"); uvn.inputs["Scale"].default_value = 9.0; uvn.inputs["Detail"].default_value = 2.0
    nt.links.new(uvn.inputs["Vector"], tc.outputs["UV"])
    ragged = _mat._math(nt, 'GREATER_THAN', _mat._math(nt, 'ADD', uvn.outputs["Fac"], _mat._math(nt, 'MULTIPLY', _mat._math(nt, 'SUBTRACT', w, ay), 5.0)), 0.36)
    alpha = _mat._math(nt, 'MULTIPLY', shape, ragged)
    at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_name = "leaf_rnd"
    col = _mat._ramp(nt, at.outputs["Fac"], [(0.0, c1), (0.5, c2), (1.0, c3)])
    tipl = _mat._ramp(nt, x, [(0.6, (1.0, 1.0, 1.0, 1)), (1.0, (1.35, 1.3, 1.1, 1))])       # paler new growth at the tips
    col = _mat._mixrgb(nt, 1.0, col, tipl, 'MULTIPLY')
    nt.links.new(b.inputs["Base Color"], col)
    nt.links.new(b.inputs["Alpha"], alpha)
    _mat._set(b, "Roughness", 0.6); _mat._set(b, "Specular IOR Level", 0.3)
    tr = nt.nodes.new("ShaderNodeBsdfTranslucent"); nt.links.new(tr.inputs["Color"], col)
    mixs = nt.nodes.new("ShaderNodeMixShader"); mixs.inputs["Fac"].default_value = translucent
    nt.links.new(mixs.inputs[1], b.outputs["BSDF"]); nt.links.new(mixs.inputs[2], tr.outputs["BSDF"])
    trans = nt.nodes.new("ShaderNodeBsdfTransparent")
    mixa = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(mixa.inputs["Fac"], alpha)
    nt.links.new(mixa.inputs[1], trans.outputs["BSDF"]); nt.links.new(mixa.inputs[2], mixs.outputs["Shader"])
    nt.links.new(nt.nodes["Material Output"].inputs["Surface"], mixa.outputs["Shader"])
    return m


def _olive_leaf(name, top=(0.16, 0.23, 0.12, 1), mid=(0.22, 0.30, 0.17, 1), top2=(0.30, 0.37, 0.24, 1),
                under=(0.46, 0.52, 0.41, 1), translucent=0.3):
    """One olive leaf on a unit quad: U petiole -> tip, V across.  Lanceolate outline (widest just below the
    middle, drawn to a fine point), a pale mid-rib, grey-green top / felted silver underside (Backfacing),
    per-leaf tint from the 'leaf_rnd' face attribute, a faint waxy sheen."""
    m, nt, b = _mat._new(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(sep.inputs["Vector"], tc.outputs["UV"])
    u = sep.outputs["X"]
    av = _mat._math(nt, 'ABSOLUTE', _mat._math(nt, 'SUBTRACT', sep.outputs["Y"], 0.5))
    # half width = 0.5 * sin(pi * u^0.85)^0.7: rounded shoulders, pointed base and (longer) tip
    s = _mat._math(nt, 'SINE', _mat._math(nt, 'MULTIPLY', _mat._math(nt, 'POWER', u, 0.85), math.pi))
    w = _mat._math(nt, 'MULTIPLY', _mat._math(nt, 'POWER', _mat._math(nt, 'MAXIMUM', s, 0.0), 0.7), 0.5)
    alpha = _mat._math(nt, 'LESS_THAN', av, w)
    rib = _mat._math(nt, 'LESS_THAN', av, _mat._math(nt, 'MULTIPLY', _mat._math(nt, 'SUBTRACT', 1.05, u), 0.045))
    at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_name = "leaf_rnd"
    col_top = _mat._ramp(nt, at.outputs["Fac"], [(0.0, top), (0.5, mid), (1.0, top2)])
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    col_under = _mat._mixrgb(nt, 1.0, under, _mat._ramp(nt, at.outputs["Fac"], [(0.0, (0.88, 0.9, 0.86, 1)), (1.0, (1.1, 1.1, 1.05, 1))]), 'MULTIPLY')
    col = _mat._mixrgb(nt, geo.outputs["Backfacing"], col_top, col_under)
    col = _mat._mixrgb(nt, _mat._math(nt, 'MULTIPLY', rib, 0.55), col, (0.60, 0.64, 0.50, 1))
    nt.links.new(b.inputs["Base Color"], col)
    nt.links.new(b.inputs["Alpha"], alpha)
    _mat._set(b, "Roughness", 0.42); _mat._set(b, "Specular IOR Level", 0.45); _mat._set(b, "Coat Weight", 0.25)
    _mat._set(b, "Coat Roughness", 0.35)
    tr = nt.nodes.new("ShaderNodeBsdfTranslucent"); nt.links.new(tr.inputs["Color"], col)
    mixs = nt.nodes.new("ShaderNodeMixShader"); mixs.inputs["Fac"].default_value = translucent
    nt.links.new(mixs.inputs[1], b.outputs["BSDF"]); nt.links.new(mixs.inputs[2], tr.outputs["BSDF"])
    trans = nt.nodes.new("ShaderNodeBsdfTransparent")
    mixa = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(mixa.inputs["Fac"], alpha)
    nt.links.new(mixa.inputs[1], trans.outputs["BSDF"]); nt.links.new(mixa.inputs[2], mixs.outputs["Shader"])
    nt.links.new(nt.nodes["Material Output"].inputs["Surface"], mixa.outputs["Shader"])
    return m


def _oak_spray_card(name, c1=(0.018, 0.05, 0.02, 1), c2=(0.04, 0.10, 0.035, 1), c3=(0.085, 0.16, 0.055, 1), translucent=0.2,
                    n=8, a=0.15, b=0.075, rough=0.65):
    """Coast-live-oak twig on a unit (square) card: a thin rachis along U with `n` nodes; at each node one small
    oval leaf on alternating sides (plus a second, opposite one at ~40 % of the nodes), standing out at 50-80 deg
    with its own size / angle jitter, a darker rim and a pale mid-rib.  Per-leaf tint from a white-noise hash,
    per-card tint from the 'leaf_rnd' attribute.  Replaces the round 'cluster' discs on the near oaks."""
    m, nt, b_ = _mat._new(name)
    M = lambda op, x, y=None, clamp=False: _mat._math(nt, op, x, y, clamp)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(sep.inputs["Vector"], tc.outputs["UV"])
    u = sep.outputs["X"]
    dy = M('SUBTRACT', sep.outputs["Y"], 0.5)
    ci = M('FLOOR', M('MULTIPLY', u, float(n)))
    xc = M('DIVIDE', M('ADD', ci, 0.5), float(n))
    parity = M('FRACT', M('MULTIPLY', ci, 0.5))                                     # 0 / 0.5 alternate
    best_r, best_rnd = None, None
    for s in (1.0, -1.0):
        def hash_(off):
            wn = nt.nodes.new("ShaderNodeTexWhiteNoise"); wn.noise_dimensions = '2D'
            cmb = nt.nodes.new("ShaderNodeCombineXYZ"); nt.links.new(cmb.inputs["X"], ci); cmb.inputs["Y"].default_value = off
            nt.links.new(wn.inputs["Vector"], cmb.outputs["Vector"])
            return wn.outputs["Value"]
        rnd, rnd2 = hash_(3.7 * s + 1.3), hash_(7.1 * s + 0.4)
        own = M('LESS_THAN', parity, 0.25) if s > 0 else M('GREATER_THAN', parity, 0.25)
        present = M('MAXIMUM', own, M('GREATER_THAN', rnd2, 0.6))
        th = M('MULTIPLY', M('ADD', 0.9, M('MULTIPLY', rnd, 0.5)), s)                # 50-80 deg off the twig, sign = side
        jit = M('MULTIPLY', M('SUBTRACT', rnd, 0.5), 0.05)
        k = M('ADD', 0.75, M('MULTIPLY', rnd2, 0.5))                                 # leaf size jitter
        dx = M('SUBTRACT', M('SUBTRACT', u, xc), jit)
        c, sn = M('COSINE', th), M('SINE', th)
        ak = M('MULTIPLY', k, a)
        l = M('SUBTRACT', M('ADD', M('MULTIPLY', dx, c), M('MULTIPLY', dy, sn)), ak)  # along the leaf, centred
        t = M('SUBTRACT', M('MULTIPLY', dy, c), M('MULTIPLY', dx, sn))              # across
        r = M('ADD', M('POWER', M('DIVIDE', l, ak), 2.0), M('POWER', M('DIVIDE', t, M('MULTIPLY', k, b)), 2.0))
        r = M('ADD', r, M('MULTIPLY', M('SUBTRACT', 1.0, present), 10.0))
        if best_r is None:
            best_r, best_rnd = r, rnd
        else:
            pick = M('LESS_THAN', r, best_r)
            best_rnd = _mat._mixrgb(nt, pick, best_rnd, rnd)
            best_r = M('MINIMUM', r, best_r)
    leaf = M('LESS_THAN', best_r, 1.0)
    rachis = M('MULTIPLY', M('LESS_THAN', M('ABSOLUTE', dy), 0.012), M('LESS_THAN', u, 0.97))
    alpha = M('ADD', leaf, rachis, clamp=True)
    at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_name = "leaf_rnd"
    col = _mat._ramp(nt, at.outputs["Fac"], [(0.0, c1), (0.5, c2), (1.0, c3)])
    tint = _mat._ramp(nt, best_rnd, [(0.0, (0.75, 0.8, 0.7, 1)), (0.5, (1.0, 1.0, 1.0, 1)), (1.0, (1.25, 1.2, 1.0, 1))])
    col = _mat._mixrgb(nt, 1.0, col, tint, 'MULTIPLY')
    rim = _mat._ramp(nt, best_r, [(0.55, (1.0, 1.0, 1.0, 1)), (1.0, (0.62, 0.66, 0.6, 1))])
    col = _mat._mixrgb(nt, 1.0, col, rim, 'MULTIPLY')
    col = _mat._mixrgb(nt, M('MULTIPLY', rachis, 0.8), col, (0.16, 0.12, 0.07, 1))
    nt.links.new(b_.inputs["Base Color"], col)
    nt.links.new(b_.inputs["Alpha"], alpha)
    _mat._set(b_, "Roughness", rough); _mat._set(b_, "Specular IOR Level", 0.4); _mat._set(b_, "Coat Weight", 0.15)
    tr = nt.nodes.new("ShaderNodeBsdfTranslucent"); nt.links.new(tr.inputs["Color"], col)
    mixs = nt.nodes.new("ShaderNodeMixShader"); mixs.inputs["Fac"].default_value = translucent
    nt.links.new(mixs.inputs[1], b_.outputs["BSDF"]); nt.links.new(mixs.inputs[2], tr.outputs["BSDF"])
    trans = nt.nodes.new("ShaderNodeBsdfTransparent")
    mixa = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(mixa.inputs["Fac"], alpha)
    nt.links.new(mixa.inputs[1], trans.outputs["BSDF"]); nt.links.new(mixa.inputs[2], mixs.outputs["Shader"])
    nt.links.new(nt.nodes["Material Output"].inputs["Surface"], mixa.outputs["Shader"])
    return m


def leaf_materials():
    """Dusk-toned leaf cards (dark, desaturated - photos 01/34 crowns are near-black green)."""
    if _LEAF:
        return _LEAF
    L = _LEAF
    L['oak'] = _oak_spray_card("LeafGeoOak")                      # near oaks: twig sprays of small oval leaves
    L['oak_far'] = _attr_random(_mat.leaf_card("LeafGeoOakFar", (0.02, 0.05, 0.025, 1), (0.04, 0.10, 0.04, 1), (0.08, 0.15, 0.06, 1), 0.12, shape='cluster', rough=0.8))
    L['olive'] = _olive_leaf("LeafOlive")                       # single leaves (near olives: explicit leaf quads)
    L['olive_far'] = _attr_random(_mat.leaf_card("LeafGeoOlive", (0.24, 0.30, 0.20, 1), (0.40, 0.46, 0.33, 1), (0.58, 0.62, 0.48, 1), 0.4, shape='cluster', rough=0.7))
    L['shrub'] = _attr_random(_mat.leaf_card("LeafGeoShrub", (0.04, 0.12, 0.04, 1), (0.10, 0.24, 0.07, 1), (0.20, 0.34, 0.11, 1), 0.3, shape='cluster', rough=0.6))
    L['frond'] = _frond_card("FrondRedwood")
    L['frond_far'] = _frond_card("FrondRedwoodFar", (0.02, 0.055, 0.03, 1), (0.04, 0.10, 0.045, 1), (0.08, 0.15, 0.06, 1), 0.12)
    L['core'] = _mat.noise_mat("CanopyCore", (0.012, 0.03, 0.012, 1), (0.03, 0.06, 0.025, 1), scale=3, rough=1.0, spec=0.02, bump=0.0)
    L['core_holey'] = _holey(L['core'], "CanopyCoreHoley", 0.55, 4.0)
    return L


def _holey(mat, name, coverage=0.55, scale=6.0):
    m = mat.copy(); m.name = name
    nt = m.node_tree
    b = nt.nodes.get("Principled BSDF")
    out = nt.nodes["Material Output"]
    surf = out.inputs["Surface"].links[0].from_socket if out.inputs["Surface"].links else b.outputs["BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = scale; n.inputs["Detail"].default_value = 3.0
    nt.links.new(n.inputs["Vector"], tc.outputs["Object"])
    gt = nt.nodes.new("ShaderNodeMath"); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = 1.0 - coverage
    nt.links.new(gt.inputs[0], n.outputs["Fac"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(mix.inputs["Fac"], gt.outputs[0])
    nt.links.new(mix.inputs[1], tr.outputs["BSDF"]); nt.links.new(mix.inputs[2], surf)
    nt.links.new(out.inputs["Surface"], mix.outputs["Shader"])
    return m


def add_haze(m, color=(0.60, 0.62, 0.78, 1), dist=220.0, strength=0.55, max_fac=0.85):
    """Aerial perspective: mix the material's surface toward a flat haze colour by camera distance
    (fac = min(max_fac, 1 - exp(-d / dist))).  Alpha-cut card materials keep their transparency: the haze is
    inserted behind the alpha mix so the holes stay holes."""
    nt = m.node_tree
    out = nt.nodes["Material Output"]
    if not out.inputs["Surface"].links:
        return m
    src_link = out.inputs["Surface"].links[0]
    target_socket = out.inputs["Surface"]
    surf = src_link.from_socket
    node = src_link.from_node
    if node.type == 'MIX_SHADER' and node.inputs[1].links and node.inputs[1].links[0].from_node.type == 'BSDF_TRANSPARENT':
        target_socket = node.inputs[2]
        surf = node.inputs[2].links[0].from_socket
    cam = nt.nodes.new("ShaderNodeCameraData")
    d = _mat._math(nt, 'DIVIDE', cam.outputs["View Distance"], dist)
    e = nt.nodes.new("ShaderNodeMath"); e.operation = 'EXPONENT'
    nt.links.new(e.inputs[0], _mat._math(nt, 'MULTIPLY', d, -1.0))
    fac = _mat._math(nt, 'MINIMUM', _mat._math(nt, 'SUBTRACT', 1.0, e.outputs[0]), max_fac)
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = color; em.inputs["Strength"].default_value = strength
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(mix.inputs["Fac"], fac)
    nt.links.new(mix.inputs[1], surf); nt.links.new(mix.inputs[2], em.outputs["Emission"])
    nt.links.new(target_socket, mix.outputs["Shader"])
    return m


# ------------------------------------------------------------------ geometry helpers
def _frame(t, ref=None):
    t = t.normalized()
    if ref is None:
        ref = Vector((0, 1, 0)) if abs(t.z) > 0.8 else Vector((0, 0, 1))
    n = t.cross(ref)
    if n.length < 1e-6:
        n = t.cross(Vector((1, 0, 0)))
    n.normalize()
    return n, t.cross(n).normalized()


def _sections(pts, radii, seg, bulge=0.0):
    """Ring sections along a polyline with per-point radius and a consistent frame (no roll flips)."""
    pts = [Vector(p) for p in pts]
    ref = Vector((0, 1, 0)) if abs((pts[-1] - pts[0]).normalized().z) > 0.8 else Vector((0, 0, 1))
    secs = []
    for k, p in enumerate(pts):
        t = pts[1] - pts[0] if k == 0 else (pts[-1] - pts[-2] if k == len(pts) - 1 else pts[k + 1] - pts[k - 1])
        n, b = _frame(t, ref)
        r = radii[k]
        secs.append([tuple(p + (n * math.cos(a) + b * math.sin(a)) * r * (1 + bulge * math.sin(3 * a)))
                     for a in [2 * math.pi * i / seg for i in range(seg)]])
    return secs


def _rand_unit(rng):
    while True:
        v = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1)))
        if 0.05 < v.length < 1.0:
            return v.normalized()


def _rotate_away(d, ang, az):
    """Direction at angle `ang` from d, azimuth `az` around d."""
    n1, n2 = _frame(d)
    perp = n1 * math.cos(az) + n2 * math.sin(az)
    return (d * math.cos(ang) + perp * math.sin(ang)).normalized()


class Tree:
    """Accumulates wood tubes + leaf cards; build() writes two objects (`name`, `name_Leaves`)."""

    def __init__(self, seed, detail=1.0, keep_out=None):
        self.rng = random.Random(seed)
        self.wood = MB()
        self.cards = []            # (pos, u, v, su, sv, rnd)
        self.cores = []            # (centre, radius, squash)
        self.detail = max(0.05, min(1.0, detail))
        self.keep_out = keep_out   # (x0, x1, y_front, z_low): keep everything south of y_front inside that box
        self.n_tubes = 0

    # -- keep-out (the signature oak must not grow into the house)
    def _blocked(self, p, margin=0.6):
        if self.keep_out is None:
            return False
        kx0, kx1, ky, kz = self.keep_out
        return kx0 - margin < p.x < kx1 + margin and p.y > ky - margin and p.z > kz - margin

    # -- wood
    def tube(self, pts, radii, seg=None):
        if seg is None:
            r = radii[0]
            seg = 10 if r > 0.25 else (8 if r > 0.1 else (6 if r > 0.03 else 4))
            if self.detail < 0.4:
                seg = max(4, seg - 2)
        self.wood.sweep(_sections(pts, radii, seg), 0)
        self.n_tubes += 1

    def curve(self, p, d, L, r0, r1, n_sub=3, wiggle=0.12, tropism=0.0, gravity=0.0):
        """Grow a curved segment from p along d; returns (points, radii, final direction). Tropism pushes the
        direction up (+) / down (-) per sub-segment; gravity bends more the longer the segment."""
        rng = self.rng
        pts, radii = [Vector(p)], [r0]
        cur, dir_ = Vector(p), Vector(d).normalized()
        for i in range(n_sub):
            jit = Vector((rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 0.7))) * wiggle
            dir_ = (dir_ + jit + Vector((0, 0, tropism - gravity * (i + 1) / n_sub))).normalized()
            nxt = cur + dir_ * (L / n_sub)
            if self._blocked(nxt):
                dir_ = Vector((dir_.x, -abs(dir_.y) - 0.4, dir_.z * 0.5)).normalized()
                nxt = cur + dir_ * (L / n_sub)
            cur = nxt
            pts.append(cur); radii.append(r0 + (r1 - r0) * (i + 1) / n_sub)
        return pts, radii, dir_

    @staticmethod
    def _at(pts, radii, t):
        """Point / direction / radius at parameter t (0..1) along a polyline."""
        n = len(pts) - 1
        k = min(n - 1, int(t * n)); f = t * n - k
        p = pts[k].lerp(pts[k + 1], f)
        d = (pts[k + 1] - pts[k]).normalized()
        r = radii[k] + (radii[k + 1] - radii[k]) * f
        return p, d, r

    # -- leaves
    def card(self, pos, normal, size, aspect=1.0, rnd=None):
        rng = self.rng
        n = Vector(normal).normalized()
        u, v = _frame(n, _rand_unit(rng))
        ph = rng.uniform(0, 2 * math.pi)
        uu = u * math.cos(ph) + v * math.sin(ph)
        vv = n.cross(uu).normalized()
        self.cards.append((Vector(pos), uu, vv, size, size * aspect, rng.random() if rnd is None else rnd))

    def frond(self, pos, along, side, length, width, rnd=None):
        """Card lying in the plane of (along, side): a flat spray along a conifer branch."""
        a = Vector(along).normalized()
        s = Vector(side).normalized()
        self.cards.append((Vector(pos), a, s, length, width, self.rng.random() if rnd is None else rnd))

    def leafy_twig(self, p, d, L, r0=0.004, leaf=(0.075, 0.017), pitch=0.03, droop=0.4, wiggle=0.22, drop=0.12):
        """A thin drooping twig with opposite leaf pairs along its outer 85 % (explicit quads).  Successive pairs
        are rotated ~90 deg round the twig (decussate), each leaf leaves the twig at 30-60 deg, sags a little and
        lies roughly blade-up; `drop` = fraction of leaves missing."""
        rng = self.rng
        pts, radii, _ = self.curve(p, d, L, r0, max(0.0015, r0 * 0.35), n_sub=3, wiggle=wiggle, gravity=droop)
        self.tube(pts, radii, 4)
        ll0, lw0 = leaf
        n = max(2, int(L * 0.85 / pitch))
        up = Vector((0, 0, 1))
        for i in range(n):
            f = 0.15 + 0.85 * (i + rng.uniform(0.25, 0.75)) / n
            q, dq, _ = self._at(pts, radii, min(1.0, f))
            n1, n2 = _frame(dq)
            roll = (i % 2) * (math.pi / 2) + rng.uniform(-0.4, 0.4)
            side = n1 * math.cos(roll) + n2 * math.sin(roll)
            for sgn in (1, -1):
                if rng.random() < drop:
                    continue
                ang = rng.uniform(0.55, 1.05)
                along = (dq * math.cos(ang) + side * (sgn * math.sin(ang))).normalized()
                along = (along + Vector((0, 0, -rng.uniform(0.0, 0.35)))).normalized()
                sd = (up + _rand_unit(rng) * 0.55).cross(along)
                if sd.length < 1e-4:
                    sd = n1
                sd.normalize()
                ll = ll0 * rng.uniform(0.65, 1.3)
                lw = lw0 * (ll / ll0) * rng.uniform(0.85, 1.15)
                self.cards.append((q + along * (ll * 0.52), along, sd, ll, lw, rng.random()))

    def clump(self, c, R, size, cov=1.2, up_bias=0.25, flat=0.15, shell=0.45, aspect=1.0, core=0.62, cap=400):
        """Leaf mass of radius R around c: a dark irregular core (core * R) plus enough cards (size grows as the
        detail drops) to cover the shell `cov` times, biased toward the shell, normals ~ radial."""
        rng = self.rng
        size = size * (1.0 + (1.0 - self.detail) * 1.5)
        n = int(min(cap, max(4, cov * 4 * math.pi * R * R / (size * size * 0.5))))
        if core > 0:
            self.cores.append((Vector(c), R * core, 1.0 - flat))
        for i in range(n):
            v = _rand_unit(rng)
            v = Vector((v.x, v.y, v.z + up_bias)).normalized()
            u = rng.random() ** shell
            pos = Vector(c) + Vector((v.x * R, v.y * R, v.z * R * (1 - flat))) * u
            nrm = (v + _rand_unit(rng) * 0.7).normalized()
            self.card(pos, nrm, size * rng.uniform(0.7, 1.35), aspect)

    def core(self, c, r, squash=0.75):
        self.cores.append((Vector(c), r, squash))

    # -- output
    def build(self, name, bark_mat, leaf_mat, coll='Landscape', core_mat=None, core_seg=8):
        # smooth shading needs the (slow, depsgraph-updating) auto-smooth operator: only for trees seen up close
        sm = self.detail >= 0.3
        ob_w = self.wood.build(name, bark_mat, coll=coll, smooth=sm)
        if self.cores and core_mat is not None:
            cm = MB()
            for k, (c, r, sq) in enumerate(self.cores):
                cm.blob(tuple(c), r, seg=core_seg, rings=max(4, core_seg * 2 // 3), jitter=0.6, seed=k * 7 + 3, mi=0, squash=sq)
            ob_c = cm.build(name + "_Core", core_mat, coll=coll, smooth=sm, auto_smooth=False)
            if not sm:
                for p in ob_c.data.polygons:
                    p.use_smooth = True
        if not self.cards:
            return ob_w
        mb = MB()
        rnds = []
        for (p, u, v, su, sv, rnd) in self.cards:
            a = p - u * (su / 2) - v * (sv / 2)
            b = p + u * (su / 2) - v * (sv / 2)
            c = p + u * (su / 2) + v * (sv / 2)
            d = p - u * (su / 2) + v * (sv / 2)
            mb.quad(tuple(a), tuple(b), tuple(c), tuple(d))
            rnds.append(rnd)
        ob_l = mb.build(name + "_Leaves", leaf_mat, coll=coll, recalc=False)
        me = ob_l.data
        uv = me.uv_layers.new(name="UVMap")
        corners = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))
        uvd = uv.data
        for pi, poly in enumerate(me.polygons):
            for j, li in enumerate(poly.loop_indices):
                uvd[li].uv = corners[j]
        attr = me.attributes.new("leaf_rnd", 'FLOAT', 'FACE')
        attr.data.foreach_set("value", rnds)
        ob_l.visible_shadow = True
        return ob_w


# ------------------------------------------------------------------ species
def oak(name, pos, height=12.0, spread=10.0, trunk_r=0.45, seed=0, lean=(0, 0), trunk_f=0.38, limbs=None,
        detail=1.0, keep_out=None, coll='Landscape', mats=None, min_z=None):
    """Coast live oak: short massive trunk, 5-7 heavy limbs spreading wide and low, three more branching levels,
    leaf-cluster cards around every twig end.  `limbs` = optional [(azimuth, length, rise)] for the primary limbs."""
    T = Tree(seed, detail, keep_out)
    rng = T.rng
    L = leaf_materials()
    x, y, z = pos
    h_trunk = height * trunk_f
    top = Vector((x + lean[0], y + lean[1], z + h_trunk))
    base = Vector((x, y, z - 0.4))
    mid = Vector((x + lean[0] * 0.35 + rng.uniform(-0.15, 0.15), y + lean[1] * 0.35 + rng.uniform(-0.15, 0.15), z + h_trunk * 0.5))
    T.wood.sweep(_sections([base, mid, top], [trunk_r * 1.05, trunk_r * 0.9, trunk_r * 0.72], 12 if detail > 0.5 else 8, bulge=0.12), 0)
    T.wood.cylinder(x, y, z - 0.4, z + 0.3, trunk_r * 1.35, trunk_r * 1.02, seg=12 if detail > 0.5 else 8, mi=0)
    if detail > 0.4:                                                   # buttress roots
        for k in range(rng.randint(3, 4)):
            a = 2 * math.pi * k / 4 + rng.uniform(-0.4, 0.4)
            rl = trunk_r * rng.uniform(1.6, 2.6)
            T.tube([Vector((x + 0.3 * trunk_r * math.cos(a), y + 0.3 * trunk_r * math.sin(a), z + 0.25)),
                    Vector((x + 0.6 * rl * math.cos(a), y + 0.6 * rl * math.sin(a), z - 0.05)),
                    Vector((x + rl * math.cos(a), y + rl * math.sin(a), z - 0.45))], [trunk_r * 0.5, trunk_r * 0.32, trunk_r * 0.14], 7)
    if limbs is None:
        nb = rng.randint(5, 7)
        limbs = []
        for i in range(nb):
            a = 2 * math.pi * i / nb + rng.uniform(-0.35, 0.35)
            limbs.append((a, spread * rng.uniform(0.40, 0.58), rng.uniform(0.25, 0.65)))
    depth = 4 if detail > 0.45 else (3 if detail > 0.2 else 2)
    clump_R = spread * (0.10 if depth >= 4 else (0.13 if depth == 3 else 0.17))
    card = (0.34 if detail >= 1.0 else 0.42) * (spread / 10.0) ** 0.5     # finer cards on the hero trees (seen from < 15 m)
    cov = 1.0 if detail > 0.45 else 0.85

    def grow(p, d, Lg, r0, level, azimuth_hint):
        r1 = r0 * (0.55 if level < 2 else 0.45)
        n_sub = 3 if level <= 1 else 2
        pts, radii, dend = T.curve(p, d, Lg, r0, max(0.008, r1), n_sub=n_sub, wiggle=0.10 + 0.06 * level,
                                   tropism=0.06 if level >= 2 else 0.0, gravity=0.05 * level)
        if min_z is not None and pts[-1].z < min_z:
            # limbed-up crown: a branch that would dip below min_z is pruned back to the last point above that
            # level and ends in a clump there - never a bare stick hanging toward the house
            keep = []
            for q, r in zip(pts, radii):
                if q.z < min_z:
                    break
                keep.append((q, r))
            if len(keep) >= 2 and keep[-1][0].z - min_z > 0.3:
                T.tube([q for q, _ in keep], [r for _, r in keep])
                T.clump(keep[-1][0], clump_R * 0.8, card, cov=cov, up_bias=0.3, flat=0.3, shell=0.6)
            return
        T.tube(pts, radii)
        if level >= depth:
            T.clump(pts[-1], clump_R * rng.uniform(0.85, 1.25), card, cov=cov, up_bias=0.3, flat=0.3, shell=0.6)
            return
        nch = {1: rng.randint(3, 4), 2: rng.randint(2, 3), 3: rng.randint(2, 3)}.get(level, 2)
        if detail < 0.45:
            nch = max(2, nch - 1)
        for k in range(nch):
            t = rng.uniform(0.45, 1.0) if k < nch - 1 else 1.0
            q, dq, rq = T._at(pts, radii, t)
            ang = rng.uniform(0.45, 0.95) if t < 1.0 else rng.uniform(0.1, 0.4)
            az = rng.uniform(0, 2 * math.pi)
            cd = _rotate_away(dq, ang, az)
            if cd.z < -0.25:
                cd = Vector((cd.x, cd.y, -0.25)).normalized()
            cL = Lg * rng.uniform(0.5, 0.75)
            grow(q, cd, cL, max(0.008, rq * rng.uniform(0.55, 0.8)), level + 1, az)
        # a clump partway along thick branches too (inner canopy)
        if level >= 2 and rng.random() < 0.75:
            q, dq, rq = T._at(pts, radii, rng.uniform(0.45, 0.9))
            T.clump(q, clump_R * 0.85, card, cov=cov * 0.7, up_bias=0.3, flat=0.3, shell=0.6)

    for (a, Ll, rise) in limbs:
        d0 = Vector((math.cos(a), math.sin(a), rise)).normalized()
        r0 = trunk_r * rng.uniform(0.5, 0.62)
        grow(top, d0, Ll * 0.62, r0, 1, a)
    mats = mats or {}
    T.build(name, mats.get('bark'), mats.get('leaf', L['oak'] if detail >= 0.45 else L['oak_far']), coll=coll,
            core_mat=mats.get('core', L['core_holey'] if detail >= 0.45 else L['core']), core_seg=8 if detail > 0.5 else 6)
    return T


def upright(name, pos, height=11.0, radius=4.0, crown_base=1.8, seed=0, detail=1.0, trunk_r=0.18, lean=(0.0, 0.0),
            scaffolds=18, card=0.26, cov=1.25, fill=1.0, keep_out=None, coll='Landscape', mats=None, squash=1.0, offset=(0.0, 0.0),
            lobes=0.0, core=0.62, envelope=None, centre=None, cull=None, scaffold_z=None):
    """Upright, dense, oval-crowned street tree (Callery pear / linden / hornbeam form): a straight central leader to
    ~0.8 H, ascending scaffold limbs spiralling up it (40-65 deg above horizontal), two more branching levels, and
    leaf-cluster cards on every twig end plus a shell fill that closes the crown to an ellipsoid of `radius`
    (horizontal) between crown_base and `height` (centre shifted by `offset`, depth scaled by `squash`).  A dark
    holey core blocks the see-through inside (`core` = its radius / crown radius); `lobes` (0..0.3) makes the crown
    outline lumpy (a smooth random radius modulation).  Measured crowns: `envelope(p)` (a callable on a world-space Vector,
    > 1 outside, star-shaped around `centre`) replaces the ellipsoid for branch lengths and the shell fill; `cull` drops
    leaf cards whose centre has envelope > cull; `scaffold_z` = (z0, z1) above pos for the scaffold origins.
    Returns the Tree (objects `name`, `name_Leaves`, `name_Core`)."""
    T = Tree(seed, detail, keep_out)
    rng = T.rng
    L = leaf_materials()
    x, y, z = pos
    cx, cy = x + offset[0], y + offset[1]
    zc = (crown_base + height) / 2
    rz = (height - crown_base) / 2

    ph = [rng.uniform(0, 2 * math.pi) for _ in range(6)]

    def lobe(dx, dy, dz):
        """Radius factor of the lumpy crown in direction (dx, dy, dz) (unnormalised)."""
        if lobes <= 0:
            return 1.0
        az = math.atan2(dy, dx)
        el = math.atan2(dz, math.hypot(dx, dy) + 1e-9)
        f = (math.sin(3 * az + ph[0]) * math.cos(2 * el + ph[1]) * 0.55 + math.sin(5 * az + ph[2] + 2 * el) * 0.3
             + math.sin(2 * az + ph[3]) * math.sin(3 * el + ph[4]) * 0.35)
        return 1.0 + lobes * f

    C = Vector(centre) if centre is not None else Vector((cx, cy, z + zc))

    def env(p):
        """> 1 outside the (lumpy) crown ellipsoid / the measured envelope."""
        if envelope is not None:
            d = p - C
            return envelope(p) / lobe(d.x, d.y, d.z)
        dx, dy, dz = (p.x - cx) / radius, (p.y - cy) / (radius * squash), (p.z - z - zc) / rz
        return math.sqrt(dx * dx + dy * dy + dz * dz) / lobe(dx, dy, dz)

    def surface(v):
        """Distance from C to the envelope along the unit vector v (march + bisection)."""
        t0, t1 = 0.0, 0.25
        while t1 < 4.0 * max(radius, rz) and env(C + v * t1) < 1.0:
            t0, t1 = t1, t1 + 0.25
        for _ in range(8):
            tm = (t0 + t1) / 2
            if env(C + v * tm) < 1.0:
                t0 = tm
            else:
                t1 = tm
        return t0
    top = Vector((x + lean[0], y + lean[1], z + height * 0.82))
    base = Vector((x, y, z - 0.3))
    T.wood.sweep(_sections([base, Vector((x + lean[0] * 0.3, y + lean[1] * 0.3, z + height * 0.3)), top],
                           [trunk_r * 1.08, trunk_r * 0.8, trunk_r * 0.28], 12 if detail > 0.5 else 8, bulge=0.06), 0)
    T.wood.cylinder(x, y, z - 0.3, z + 0.25, trunk_r * 1.35, trunk_r * 1.05, seg=12, mi=0)
    card_sz = card * (1.0 + (1.0 - T.detail) * 1.2)
    clump_r = radius * 0.16

    def grow(p, d, Lg, r0, level):
        pts, radii, dend = T.curve(p, d, Lg, r0, max(0.006, r0 * 0.5), n_sub=3, wiggle=0.07, tropism=0.05, gravity=0.02 * level)
        # stay inside the envelope: shorten the branch at the shell
        keep = [pts[0]]
        for q in pts[1:]:
            if env(q) > 1.02:
                break
            keep.append(q)
        if len(keep) < 2:
            keep = pts[:2]
        pts = keep
        radii = radii[:len(pts)]
        T.tube(pts, radii)
        if level >= (3 if detail > 0.45 else 2):
            T.clump(pts[-1], clump_r * rng.uniform(0.8, 1.2), card_sz, cov=cov, up_bias=0.25, flat=0.2, shell=0.55)
            return
        for k in range(rng.randint(2, 3)):
            t = rng.uniform(0.4, 1.0)
            q, dq, rq = T._at(pts, radii, t)
            cd = _rotate_away(dq, rng.uniform(0.35, 0.8), rng.uniform(0, 2 * math.pi))
            if cd.z < 0.1:
                cd = Vector((cd.x, cd.y, 0.1)).normalized()
            grow(q, cd, Lg * rng.uniform(0.5, 0.7), max(0.006, rq * rng.uniform(0.55, 0.75)), level + 1)
        if rng.random() < 0.8:
            q, dq, rq = T._at(pts, radii, rng.uniform(0.5, 0.95))
            T.clump(q, clump_r * 0.9, card_sz, cov=cov * 0.7, up_bias=0.25, flat=0.2, shell=0.55)

    golden = math.pi * (3 - math.sqrt(5))
    az0 = rng.uniform(0, 2 * math.pi)
    for i in range(scaffolds):
        f = i / max(1, scaffolds - 1)
        z0s, z1s = scaffold_z if scaffold_z else (crown_base * 0.85, height * 0.78)
        zb = z + z0s + (z1s - z0s) * f
        p = base.lerp(top, (zb - base.z) / (top.z - base.z))
        az = az0 + golden * i + rng.uniform(-0.25, 0.25)
        elev = math.radians(rng.uniform(38, 55) + 18 * f)
        d0 = Vector((math.cos(az) * math.cos(elev), math.sin(az) * math.cos(elev), math.sin(elev)))
        # length to reach ~0.9 of the envelope along d0
        Lr = 0.5
        while Lr < 2.5 * radius and env(p + d0 * Lr) < 0.92:
            Lr += 0.25
        grow(p, d0, Lr, trunk_r * (0.55 - 0.3 * f), 1)
    # shell fill: close the crown silhouette where the branch clumps left gaps
    cps = [c for (c, r, sq) in T.cores]
    n_fill = int(fill * 4 * math.pi * radius * rz / (clump_r * clump_r * 2.2))
    tips = [Vector(v) for v in list(T.wood.v)[::7]]
    for k in range(n_fill):
        v = _rand_unit(rng)
        if envelope is not None:
            q = C + v * (surface(v) * rng.uniform(0.80, 1.0))
        else:
            s = rng.uniform(0.80, 1.0) * lobe(v.x, v.y, v.z)
            q = Vector((cx + v.x * radius * s, cy + v.y * radius * squash * s, z + zc + v.z * rz * s))
            if q.z < z + crown_base:
                continue
        if keep_out is not None and T._blocked(q, margin=0.3):
            continue
        near = min(tips, key=lambda t: (t - q).length_squared) if tips else None
        if near is not None and (near - q).length > 0.15:
            d = (q - near)
            T.tube([near, near + d * 0.5, q], [0.012, 0.009, 0.005], 4)
        T.clump(q, clump_r * rng.uniform(0.8, 1.15), card_sz, cov=cov, up_bias=0.2, flat=0.15, shell=0.6, core=0.0)
    del cps
    # the dark core (a few overlapping squashed blobs inside the crown)
    for k in range(5):
        v = _rand_unit(rng) * 0.35
        if envelope is not None:
            T.core(C + Vector((v.x * radius, v.y * radius * squash, v.z * rz * 0.6)), radius * core, rz / radius * 0.85)
        else:
            T.core(Vector((cx + v.x * radius, cy + v.y * radius * squash, z + zc + v.z * rz * 0.6)), radius * core, rz / radius * 0.85)
    if cull is not None:
        T.cards = [c for c in T.cards if env(c[0]) <= cull]
    mats = mats or {}
    T.build(name, mats.get('bark'), mats.get('leaf', L['oak']), coll=coll, core_mat=mats.get('core', L['core_holey']),
            core_seg=10 if detail > 0.5 else 6)
    return T


def conifer(name, pos, height=28.0, r=3.4, seed=0, detail=1.0, kind='redwood', coll='Landscape', mats=None):
    """Coast redwood / pine: straight fibrous trunk, whorls of near-horizontal, drooping branches whose length
    follows a conical profile, flat feathery sprays (frond cards) along the outer part of every branch."""
    T = Tree(seed, detail)
    rng = T.rng
    L = leaf_materials()
    x, y, z = pos
    clear = height * (0.12 if kind == 'redwood' else 0.30)
    r_base = min(0.95, height * 0.031)
    r_top = max(0.08, height * 0.004)
    pts = [Vector((x, y, z - 0.5))]
    for k in range(1, 6):
        t = k / 5
        pts.append(Vector((x + rng.uniform(-0.1, 0.1) * height * 0.01 * k, y + rng.uniform(-0.1, 0.1) * height * 0.01 * k, z + height * 0.985 * t)))
    radii = [r_base * 1.3, r_base * 0.85, r_base * 0.62, r_base * 0.42, r_base * 0.22, r_top]
    T.wood.sweep(_sections(pts, radii, 12 if detail > 0.5 else 7, bulge=0.12), 0)

    def trunk_at(zz):
        t = max(0.0, min(1.0, (zz - (z - 0.5)) / (height * 0.985 + 0.5)))
        i = min(4, int(t * 5)); f = t * 5 - i
        return pts[i].lerp(pts[i + 1], f)

    if detail > 0.4:                                                   # dead stubs in the clear zone
        for k in range(rng.randint(3, 6)):
            zz = z + clear * rng.uniform(0.35, 0.95)
            a = rng.uniform(0, 2 * math.pi)
            p0 = trunk_at(zz)
            Ls = r * rng.uniform(0.2, 0.45)
            p1 = p0 + Vector((Ls * math.cos(a), Ls * math.sin(a), -Ls * rng.uniform(0.3, 0.7)))
            T.tube([p0, p0.lerp(p1, 0.5) + Vector((0, 0, Ls * 0.1)), p1], [0.05, 0.03, 0.012], 5)
    spacing = 0.6 if detail > 0.45 else (0.9 if detail > 0.2 else 1.3)
    n_whorl = max(6, int((height * 0.93 - clear) / spacing))
    frond_len = 0.85 * (1.0 + (1.0 - T.detail) * 1.4)
    pitch = 0.22 * (1.0 + (1.0 - T.detail) * 1.6)                    # spray spacing along a branch
    for i in range(n_whorl):
        t = i / max(1, n_whorl - 1)
        if 0.05 < t < 0.9 and rng.random() < 0.07:
            continue
        zt = z + clear + (height * 0.93 - clear) * t + rng.uniform(-0.2, 0.2)
        rt = (r * (1.0 - 0.92 * t ** 1.1) + 0.28 * r / 3.4) * rng.uniform(0.85, 1.12)
        p0 = trunk_at(zt)
        nb = (rng.randint(6, 8) if detail > 0.45 else rng.randint(4, 6))
        a0 = rng.uniform(0, 2 * math.pi)
        for j in range(nb):
            if rng.random() < 0.10:
                continue
            a = a0 + 2 * math.pi * j / nb + rng.uniform(-0.3, 0.3)
            Lb = rt * rng.uniform(0.8, 1.15)
            d = Vector((math.cos(a), math.sin(a), rng.uniform(0.02, 0.14)))
            sag = Lb * rng.uniform(0.15, 0.4)
            b_pts = [p0, p0 + d * (Lb * 0.5) + Vector((0, 0, -sag * 0.2)), p0 + d * Lb + Vector((0, 0, -sag))]
            b_rad = [max(0.012, 0.035 * Lb / 3.0), max(0.009, 0.022 * Lb / 3.0), 0.007]
            if detail > 0.2:
                T.tube(b_pts, b_rad, 5 if detail > 0.45 else 4)
            side = Vector((-d.y, d.x, 0))
            # sprays along the outer 70 % of the branch, every `pitch` m alternating sides, plus a hanging row
            # below: flat, drooping, fanning slightly forward -> a continuous feathery plume per branch
            n_fr = max(2, int(Lb * 0.7 / pitch))
            for m in range(n_fr):
                f = 0.3 + 0.7 * (m + rng.uniform(0.3, 0.7)) / n_fr
                q, dq, _ = T._at(b_pts, b_rad, min(1.0, f))
                for row in (0, 1):
                    if row and rng.random() < 0.45:
                        continue
                    sgn = (1 if m % 2 == 0 else -1) * (1 if row == 0 else -1)
                    along = (dq * 0.7 + side * sgn * rng.uniform(0.45, 1.0) + Vector((0, 0, -rng.uniform(0.1, 0.45) - 0.25 * row))).normalized()
                    sd = along.cross(Vector((0, 0, 1)))
                    if sd.length < 1e-4:
                        sd = side
                    sd = (sd.normalized() + Vector((0, 0, rng.uniform(-0.3, 0.3)))).normalized()
                    fl = frond_len * rng.uniform(0.75, 1.3) * (1.1 if f > 0.8 else 0.95) * max(0.7, min(1.25, Lb / 2.5))
                    T.frond(q + along * (fl * 0.42), along, sd, fl, fl * 0.5)
            # secondary side branchlets with their own sprays (near trees)
            if detail > 0.45 and Lb > 1.2:
                for m in range(rng.randint(1, 2)):
                    f = rng.uniform(0.35, 0.8)
                    q, dq, _ = T._at(b_pts, b_rad, f)
                    sgn = rng.choice((-1, 1))
                    sdir = (dq * 0.6 + side * sgn * 0.8 + Vector((0, 0, -0.15))).normalized()
                    Ls = Lb * rng.uniform(0.25, 0.45)
                    s_pts = [q, q + sdir * Ls * 0.5, q + sdir * Ls + Vector((0, 0, -Ls * 0.2))]
                    T.tube(s_pts, [0.012, 0.009, 0.006], 4)
                    for mm in range(3):
                        ff = 0.4 + 0.6 * (mm + 0.5) / 3
                        qq, dqq, _ = T._at(s_pts, [0.012, 0.009, 0.006], ff)
                        along = (dqq * 0.8 + side * sgn * 0.3 + Vector((0, 0, -0.15))).normalized()
                        sd = along.cross(Vector((0, 0, 1))).normalized()
                        fl = frond_len * rng.uniform(0.6, 1.0)
                        T.frond(qq + along * fl * 0.45, along, sd, fl, fl * 0.42)
    # leader: a slim spire of small sprays + a tip
    for j in range(4):
        zz = z + height * (0.92 + 0.02 * j)
        p0 = trunk_at(zz)
        for k in range(4):
            a = rng.uniform(0, 2 * math.pi)
            along = Vector((math.cos(a) * 0.7, math.sin(a) * 0.7, 0.35)).normalized()
            sd = along.cross(Vector((0, 0, 1))).normalized()
            fl = frond_len * 0.6 * (1 - 0.2 * j)
            T.frond(p0 + along * fl * 0.4, along, sd, fl, fl * 0.42)
    mats = mats or {}
    T.build(name, mats.get('bark'), mats.get('leaf', L['frond'] if detail >= 0.45 else L['frond_far']), coll=coll, core_mat=None)
    return T


def olive(name, pos, height=4.5, seed=0, detail=1.0, coll='Landscape', mats=None, stake=False, extra_mats=()):
    """Olive: gnarled bulging trunk, 3-4 leaders branching four deep, then hundreds of thin drooping twigs carrying
    opposite pairs of small lanceolate leaves (explicit quads, grey-green top / silver underside) - an airy,
    irregular crown the limbs stay visible through.  Low detail (< 0.4) keeps the cheap leaf-cluster cards."""
    T = Tree(seed, detail)
    rng = T.rng
    L = leaf_materials()
    fine = detail >= 0.4
    x, y, z = pos
    h_trunk = height * 0.34
    pts = [Vector((x, y, z - 0.2))]
    for k in range(1, 4):
        t = k / 3
        pts.append(Vector((x + rng.uniform(-0.14, 0.14) * (1 if k < 3 else 0.5), y + rng.uniform(-0.14, 0.14), z + h_trunk * t)))
    top = pts[-1]
    T.wood.sweep(_sections(pts, [height * (0.03 - 0.011 * k / 3) for k in range(4)], 10, bulge=0.25), 0)
    for k in range(3):                                                   # root knuckles
        a = 2 * math.pi * k / 3 + rng.uniform(-0.5, 0.5)
        rl = height * rng.uniform(0.05, 0.08)
        T.tube([Vector((x, y, z + 0.1)), Vector((x + rl * 0.6 * math.cos(a), y + rl * 0.6 * math.sin(a), z - 0.02)),
                Vector((x + rl * math.cos(a), y + rl * math.sin(a), z - 0.25))], [height * 0.022, height * 0.014, height * 0.007], 6)
    if stake:                                                            # mulch ring + nursery stake with a tie (mats 2, 3)
        T.wood.cylinder(x, y, z - 0.02, z + 0.025, 0.75, seg=20, mi=2)
        sx, sy = x + 0.28, y - 0.12
        T.wood.cylinder(sx, sy, z - 0.3, z + 1.6, 0.022, seg=8, mi=3)
        T.wood.tube((sx, sy, z + 1.35), (top.x, top.y, z + 1.35), 0.012, 0.012, seg=6, mi=3)
    card = 0.28 * (height / 4.0) ** 0.5
    R = height * 0.10
    depth = 4 if fine else 2
    sz = (height / 4.0) ** 0.3
    leaf = (0.085 * sz, 0.019 * sz)                                    # 6-11 cm x 1.6-2.2 cm lanceolate leaves
    tw_len = height * 0.09

    def twig_fan(pts_, radii, n, t_lo=0.35):
        """n leafy twigs off a branch: one continues the tip, the rest leave its outer part at 20-60 deg."""
        for k in range(n):
            t = 1.0 if k == 0 else rng.uniform(t_lo, 1.0)
            q, dq, rq = T._at(pts_, radii, t)
            ang = rng.uniform(0.0, 0.35) if t >= 1.0 else rng.uniform(0.35, 1.05)
            cd = _rotate_away(dq, ang, rng.uniform(0, 2 * math.pi))
            T.leafy_twig(q, cd, tw_len * rng.uniform(0.6, 1.4), r0=min(0.006, max(0.003, rq * 0.6)), leaf=leaf,
                         pitch=0.021, droop=rng.uniform(0.25, 0.65))

    def grow(p, d, Lg, r0, level):
        r1 = r0 * 0.5
        pts_, radii, dend = T.curve(p, d, Lg, r0, max(0.006, r1), n_sub=2 if level > 1 else 3, wiggle=0.16,
                                    tropism=0.05 if level < 3 else -0.02, gravity=0.0 if level < 3 else 0.12)
        T.tube(pts_, radii)
        if level >= depth:
            if fine:
                twig_fan(pts_, radii, rng.randint(11, 15))
            else:
                T.clump(pts_[-1], R * 1.5 * rng.uniform(0.85, 1.2), card, cov=1.0, up_bias=0.2, flat=0.25, core=0.55)
            return
        for k in range(rng.randint(2, 3)):
            t = rng.uniform(0.5, 1.0) if k else 1.0
            q, dq, rq = T._at(pts_, radii, t)
            cd = _rotate_away(dq, rng.uniform(0.4, 0.95), rng.uniform(0, 2 * math.pi))
            if cd.z < -0.15:
                cd = Vector((cd.x, cd.y, -0.15)).normalized()
            grow(q, cd, Lg * rng.uniform(0.5, 0.72), max(0.006, rq * 0.7), level + 1)
        if fine and level >= 2:
            twig_fan(pts_, radii, rng.randint(4, 6), t_lo=0.2)         # inner canopy along the thicker branches
        elif not fine and level == 2 and rng.random() < 0.7:
            q, dq, rq = T._at(pts_, radii, rng.uniform(0.5, 0.9))
            T.clump(q, R * 0.8, card, cov=0.7, up_bias=0.2, flat=0.25, core=0.55)

    n = rng.randint(3, 4)
    for i in range(n):
        a = 2 * math.pi * i / n + rng.uniform(-0.4, 0.4)
        d0 = Vector((math.cos(a) * 0.8, math.sin(a) * 0.8, rng.uniform(0.45, 0.95))).normalized()
        grow(top, d0, height * rng.uniform(0.28, 0.38), height * 0.02, 1)
    mats = mats or {}
    bark = mats.get('bark')
    T.build(name, [bark] + list(extra_mats) if extra_mats else bark, mats.get('leaf', L['olive'] if fine else L['olive_far']),
            coll=coll, core_mat=mats.get('core', L['core_holey']), core_seg=8)
    return T


def shrub_cards(T, c, r, size=0.22, seed=0, cov=1.0):
    """Rounded shrub = dark cores + a shell of shrub leaf-cluster cards (call on a shared Tree accumulator)."""
    rng = random.Random(seed)
    for k in range(3):
        q = (c[0] + rng.uniform(-0.3, 0.3) * r, c[1] + rng.uniform(-0.3, 0.3) * r, c[2] + r * 0.5 + rng.uniform(-0.1, 0.2) * r)
        T.clump(q, r * 0.75, size, cov=cov, up_bias=0.35, flat=0.25, shell=0.35, core=0.7)
