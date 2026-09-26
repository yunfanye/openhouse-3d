"""Vegetation for 1836 Webster St: kerb-side street trees, the front olive + clipped foundation planting, side-yard
trees and hedges, the rear redwoods / pine behind the fence, the white-flowering oleander behind the garage, rose
shrubs in the patio cut-outs, the -X shrub border, ferns by the shed, ground cover, fallen leaves on the driveway,
landscape uplights and a hazed low-LOD tree ring as the neighbourhood backdrop.  (Photos 02, 16, 27-30.)

Trees come from archviz.trees (branching skeletons + leaf cards); shrubs / hedges are dark cores + card shells on
shared Tree accumulators.  Everything sits on the site grade Z_GRADE.  Surfaces, beds, fences, garage and shed are
site.py's.  Object names start with Land_, collection 'Landscape'.
"""
import math, random
import bpy
from mathutils import Vector
from .plan import *
from archviz.mesh import *
from archviz.lights import *
from archviz import materials
from archviz import trees as _tr
from archviz import plants as _pl

HAZE = (0.62, 0.64, 0.78, 1)
ZG = Z_GRADE

# camera corridors of the film that must stay free of foliage (x0, x1, y0, y1, z_min): nothing below z_min inside
CORRIDORS = [(-3.0, 8.0, -34.0, -4.0, 9.0),      # aerial descent / finale over the front lawn + street
             (-8.0, 3.0, 12.0, 30.0, 3.0)]        # backyard crane and the arc onto the deck

_LM = {}


def _aniso(m, scale):
    for n in m.node_tree.nodes:
        if n.type == 'MAPPING':
            n.inputs["Scale"].default_value = scale
    return m


def _specks(mat, name, color=(0.95, 0.95, 0.9, 1), frac=0.08, scale=35.0):
    """Copy of a leaf material whose base colour is replaced by `color` in sparse noise blobs (flowers)."""
    m = mat.copy(); m.name = name
    nt = m.node_tree
    b = nt.nodes.get("Principled BSDF")
    if b is None:
        return m
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = scale; n.inputs["Detail"].default_value = 2.0
    nt.links.new(n.inputs["Vector"], tc.outputs["Object"])
    gt = nt.nodes.new("ShaderNodeMath"); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = 1.0 - frac * 0.5
    nt.links.new(gt.inputs[0], n.outputs["Fac"])
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = 'RGBA'
    src = b.inputs["Base Color"]
    if src.links:
        nt.links.new(mix.inputs["A"], src.links[0].from_socket)
    else:
        mix.inputs["A"].default_value = src.default_value
    mix.inputs["B"].default_value = color
    nt.links.new(mix.inputs["Factor"], gt.outputs[0])
    nt.links.new(b.inputs["Base Color"], mix.outputs["Result"])
    return m


def local_mats():
    if _LM:
        return _LM
    L = _tr.leaf_materials()
    _LM['bark'] = _aniso(materials.noise_mat("BarkOakFurrowedW", (0.09, 0.07, 0.055, 1), (0.20, 0.17, 0.13, 1), scale=14, bump=1.2, spec=0.06, bump_dist=0.03), (1.0, 1.0, 0.28))
    _LM['bark_plane'] = _aniso(materials.noise_mat("BarkPlaneMottled", (0.36, 0.33, 0.26, 1), (0.62, 0.60, 0.50, 1), scale=5, bump=0.6, spec=0.08, bump_dist=0.02), (1.0, 1.0, 0.5))
    _LM['bark_red'] = _aniso(materials.noise_mat("BarkRedwoodW", (0.14, 0.075, 0.05, 1), (0.26, 0.15, 0.09, 1), scale=22, bump=1.3, spec=0.06, bump_dist=0.03), (1.0, 1.0, 0.10))
    _LM['bark_pine'] = _aniso(materials.noise_mat("BarkPineW", (0.16, 0.11, 0.08, 1), (0.32, 0.24, 0.17, 1), scale=12, bump=1.1, spec=0.06, bump_dist=0.03), (1.0, 1.0, 0.35))
    _LM['bark_olive'] = _aniso(materials.noise_mat("BarkOliveW", (0.30, 0.26, 0.21, 1), (0.52, 0.47, 0.39, 1), scale=16, bump=0.9, spec=0.08, bump_dist=0.02), (1.0, 1.0, 0.35))
    _LM['bark_far'] = _tr.add_haze(materials.noise_mat("BarkFarW", (0.05, 0.04, 0.032, 1), (0.11, 0.09, 0.07, 1), scale=8, bump=0.3, spec=0.05), HAZE, dist=180.0, strength=0.14, max_fac=0.45)
    # a lighter, larger-leaved spray for the London plane at the kerb (photo 02: pale green crowns over the street)
    _LM['leaf_plane'] = _tr._oak_spray_card("LeafPlane", (0.05, 0.12, 0.035, 1), (0.11, 0.24, 0.07, 1), (0.22, 0.36, 0.12, 1), translucent=0.35, n=6, a=0.22, b=0.14, rough=0.6)
    _LM['leaf_hedge'] = _tr._attr_random(materials.leaf_card("LeafHedgeBox", (0.04, 0.11, 0.035, 1), (0.09, 0.20, 0.06, 1), (0.16, 0.30, 0.10, 1), 0.25, shape='cluster', rough=0.6))
    _LM['leaf_oleander'] = _specks(_tr._attr_random(materials.leaf_card("LeafOleander", (0.05, 0.13, 0.05, 1), (0.12, 0.26, 0.10, 1), (0.24, 0.38, 0.16, 1), 0.3, shape='lance', rough=0.55)),
                                   "LeafOleanderFlowers", (0.95, 0.94, 0.88, 1), frac=0.16, scale=28.0)
    _LM['leaf_rose'] = _specks(_tr._attr_random(materials.leaf_card("LeafRose", (0.04, 0.12, 0.04, 1), (0.10, 0.24, 0.08, 1), (0.20, 0.36, 0.13, 1), 0.3, shape='cluster', rough=0.55)),
                               "LeafRoseBlooms", (0.85, 0.35, 0.45, 1), frac=0.09, scale=40.0)
    _LM['shrub_core'] = materials.foliage("ShrubDarkW", (0.05, 0.14, 0.04, 1), (0.14, 0.28, 0.08, 1), 0.25, rough=0.9)
    _LM['hedge_core'] = materials.foliage("HedgeDarkW", (0.03, 0.10, 0.03, 1), (0.09, 0.20, 0.06, 1), 0.2, rough=0.95)
    _LM['fern'] = materials.foliage("FernW", (0.05, 0.18, 0.05, 1), (0.14, 0.34, 0.10, 1), 0.45, c3=(0.28, 0.46, 0.16, 1), rough=0.8)
    _LM['agave'] = materials.foliage("AgaveW", (0.30, 0.40, 0.32, 1), (0.48, 0.58, 0.46, 1), 0.2, c3=(0.62, 0.70, 0.56, 1), rough=0.6)
    _LM['dead_leaf'] = materials.noise_mat("DeadLeafW", (0.32, 0.18, 0.07, 1), (0.55, 0.36, 0.14, 1), scale=40, bump=0.3, rough=0.85)
    _LM['mulch'] = materials.noise_mat("MulchRing", (0.12, 0.07, 0.04, 1), (0.22, 0.13, 0.08, 1), scale=30, bump=0.6)
    _LM['mulch_bed'] = materials.noise_mat("MulchBedW", (0.09, 0.055, 0.03, 1), (0.24, 0.15, 0.09, 1), scale=55, bump=0.9, detail=7, rough=0.95, spec=0.05, bump_dist=0.03)
    # far ring: hazed copies of the leaf cards (the haze goes behind the alpha mix so the holes stay holes)
    _LM['leaf_ring'] = _tr.add_haze(_tr._attr_random(materials.leaf_card("LeafRingW", (0.02, 0.05, 0.025, 1), (0.04, 0.095, 0.04, 1), (0.075, 0.14, 0.055, 1), 0.1, shape='cluster', rough=0.9)),
                                    HAZE, dist=180.0, strength=0.14, max_fac=0.45)
    _LM['frond_ring'] = _tr.add_haze(_tr._frond_card("FrondRingW", (0.02, 0.05, 0.03, 1), (0.035, 0.085, 0.04, 1), (0.06, 0.12, 0.05, 1), 0.1),
                                     HAZE, dist=180.0, strength=0.14, max_fac=0.45)
    _LM['core_ring'] = _tr.add_haze(materials.noise_mat("CanopyCoreRingW", (0.012, 0.03, 0.014, 1), (0.03, 0.06, 0.03, 1), scale=3, rough=1.0, spec=0.02, bump=0.0),
                                    HAZE, dist=180.0, strength=0.14, max_fac=0.45)
    return _LM


def _detail(x, y):
    d = math.hypot(x, y - 8.0)
    return 1.0 if d < 30 else (0.5 if d < 60 else 0.16)


# ================================================================== species wrappers
def oak(M, name, pos, height=12.0, spread=10.0, trunk_r=0.45, seed=0, lean=(0, 0), trunk_f=0.38, limbs=None,
        detail=None, min_z=None, ring=False, plane=False):
    lm = local_mats()
    d = _detail(pos[0], pos[1]) if detail is None else detail
    mats = {'bark': lm['bark_far'] if ring else (lm['bark_plane'] if plane else lm['bark'])}
    if ring:
        mats['leaf'] = lm['leaf_ring']; mats['core'] = lm['core_ring']
    elif plane:
        mats['leaf'] = lm['leaf_plane']
    return _tr.oak("Land_" + name, pos, height, spread, trunk_r, seed, lean, trunk_f, limbs, d, None, 'Landscape', mats, min_z)


def conifer(M, name, pos, height=28.0, r=3.4, seed=0, kind='redwood', detail=None, ring=False):
    lm = local_mats()
    d = _detail(pos[0], pos[1]) if detail is None else detail
    # Match the modest background silhouettes in photo 00; keep rear specimen trees detailed.
    if ring:
        height *= 0.62
        r *= 0.9
    else:
        d = max(d, 0.85)
    mats = {'bark': lm['bark_far'] if ring else (lm['bark_red'] if kind == 'redwood' else lm['bark_pine'])}
    if ring:
        mats['leaf'] = lm['frond_ring']
    return _tr.conifer("Land_" + name, pos, height, r, seed, d, kind, 'Landscape', mats)


def olive(M, name, pos, height=4.5, seed=0, detail=None, stake=False):
    lm = local_mats()
    d = _detail(pos[0], pos[1]) if detail is None else detail
    return _tr.olive("Land_" + name, pos, height, seed, d, 'Landscape', {'bark': lm['bark_olive']}, stake=stake,
                     extra_mats=(lm['mulch'], M['teak']) if stake else ())


def magnolia(M, name, pos, height=9.0, crown_r=4.0, limb_up=3.0, seed=1, reach=None):
    """Southern magnolia (photo 00, front-left over the sidewalk): a stout trunk limbed up `limb_up`, six rising limbs
    with secondaries + leafy twigs, a dense shell of big glossy elliptic leaves (rust undersides) on an ovoid crown,
    and an optional long low limb to `reach` = (x, y, z) whose hanging leaves frame a camera's top-left corner."""
    lm = local_mats()
    L = _tr.leaf_materials()
    F = _pl.Foliage(seed)
    rng = F.rng
    x, y, z = pos
    up = Vector((0, 0, 1))
    pts = [Vector((x, y, z - 0.4)), Vector((x + 0.08, y - 0.04, z + limb_up * 0.5)), Vector((x + 0.2, y - 0.1, z + limb_up + 0.2))]
    F.wood.sweep(_tr._sections(pts, [0.36, 0.30, 0.25], 12, bulge=0.15), 2)
    F.wood.cylinder(x, y, z - 0.4, z + 0.3, 0.5, 0.37, seg=12, mi=2)                          # root flare
    top = pts[-1]
    cz = z + limb_up + (height - limb_up) * 0.5
    c_half = (height - limb_up) * 0.5

    def twig_leaves(p, d, Ltw, n_leaves):
        q, dq = F.arc(p, d, Ltw, 0.012, 0.005, n=2, gravity=0.12, wiggle=0.15, seg=4)
        for j in range(n_leaves):
            t = 0.3 + 0.7 * rng.random()
            kk = min(len(q) - 2, int(t * 2)); f = t * 2 - kk
            pl = q[kk].lerp(q[kk + 1], f)
            ld = (dq * 0.4 + _pl._perp(dq, rng) * 0.8 + Vector((0, 0, -rng.uniform(0.1, 0.5)))).normalized()
            Ll = rng.uniform(0.12, 0.18)
            F.leaf('magnolia', pl, ld, _pl._perp(ld, rng), Ll, Ll * 0.5, n=2, droop=rng.uniform(0.25, 0.5))

    n = 6
    for i in range(n):
        a = 2 * math.pi * i / n + rng.uniform(-0.3, 0.3)
        out = Vector((math.cos(a), math.sin(a), 0))
        el = rng.uniform(0.35, 0.8)
        d = (out * math.cos(el) + up * math.sin(el)).normalized()
        Ll = crown_r * rng.uniform(0.8, 1.05)
        p1, d1 = F.arc(top, d, Ll, 0.13, 0.05, n=4, gravity=-0.04, wiggle=0.07, seg=7)
        for k in range(rng.randint(3, 4)):
            t = rng.uniform(0.4, 1.0)
            kk = min(len(p1) - 2, int(t * 4)); f = t * 4 - kk
            q = p1[kk].lerp(p1[kk + 1], f)
            d2 = (d1 * 0.5 + _pl._perp(d1, rng) * 0.8 + Vector((0, 0, rng.uniform(-0.1, 0.4)))).normalized()
            p2, dd2 = F.arc(q, d2, crown_r * rng.uniform(0.35, 0.55), 0.045, 0.015, n=3, gravity=0.06, wiggle=0.12, seg=5)
            for m in range(rng.randint(3, 4)):
                tt = rng.uniform(0.45, 1.0)
                mm = min(len(p2) - 2, int(tt * 3)); ff = tt * 3 - mm
                twig_leaves(p2[mm].lerp(p2[mm + 1], ff), (dd2 * 0.6 + _pl._perp(dd2, rng) * 0.7).normalized(), rng.uniform(0.5, 0.9), rng.randint(6, 9))
    # crown shell: leaves on an ovoid, biased to the outside (glossy tops out / up, rust undersides seen from below)
    for i in range(int(22000 * (crown_r / 4.0) ** 2)):
        v = Vector((rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1) * 0.85)).normalized()
        u = rng.random() ** 0.3
        pl = Vector((x + v.x * crown_r * u, y + v.y * crown_r * u, cz + v.z * c_half * u))
        if pl.z < z + limb_up * 0.85:
            continue
        ld = (v + Vector((rng.gauss(0, 0.5), rng.gauss(0, 0.5), rng.gauss(0, 0.5) - 0.35))).normalized()
        Ll = rng.uniform(0.12, 0.18)
        F.leaf('magnolia', pl, ld, _pl._perp(ld, rng), Ll, Ll * 0.5, n=2, droop=rng.uniform(0.2, 0.5))
    # The canopy is real overlapping foliage. A solid dark core was visibly spherical from above.
    if reach is not None:                                                                       # the long low limb
        rx, ry, rz = reach
        d = (Vector((rx, ry, rz)) - top)
        Lr = d.length; d.normalize()
        pr, dr = F.arc(top, (d + Vector((0, 0, 0.12))).normalized(), Lr, 0.15, 0.05, n=5, gravity=0.05, wiggle=0.04, seg=8)
        for k in range(16):
            t = rng.uniform(0.35, 1.0)
            kk = min(len(pr) - 2, int(t * 5)); f = t * 5 - kk
            q = pr[kk].lerp(pr[kk + 1], f)
            d2 = (dr * 0.4 + _pl._perp(dr, rng) * 0.8 + Vector((0, 0, -0.2))).normalized()
            p2, dd2 = F.arc(q, d2, rng.uniform(0.7, 1.3), 0.04, 0.012, n=3, gravity=0.15, wiggle=0.12, seg=5)
            for m in range(rng.randint(4, 6)):
                tt = rng.uniform(0.3, 1.0)
                mm = min(len(p2) - 2, int(tt * 3)); ff = tt * 3 - mm
                twig_leaves(p2[mm].lerp(p2[mm + 1], ff), (dd2 * 0.5 + _pl._perp(dd2, rng) * 0.7 + Vector((0, 0, -0.3))).normalized(), rng.uniform(0.4, 0.8), rng.randint(8, 12))
        for k in range(140):                                                                   # leaves hanging off the limb itself
            t = rng.uniform(0.3, 1.0)
            kk = min(len(pr) - 2, int(t * 5)); f = t * 5 - kk
            q = pr[kk].lerp(pr[kk + 1], f)
            ld = (_pl._perp(dr, rng) * 0.8 + Vector((0, 0, -rng.uniform(0.3, 0.8)))).normalized()
            Ll = rng.uniform(0.13, 0.18)
            F.leaf('magnolia', q, ld, _pl._perp(ld, rng), Ll, Ll * 0.5, n=2, droop=rng.uniform(0.2, 0.45))
    return F.build("Land_" + name, [lm['bark'], lm['bark'], lm['bark'], L['core'], lm['bark']], coll='Landscape')


# ================================================================== small stuff
def grass_tuft(mb, c, r, seed=0, mi=0, blades=None):
    rng = random.Random(seed)
    n = blades or rng.randint(14, 22)
    h = r * 2.6
    for i in range(n):
        a = 2 * math.pi * i / n + rng.uniform(-0.3, 0.3)
        lean = rng.uniform(0.25, 0.75)
        hb = h * rng.uniform(0.6, 1.15)
        base = Vector((c[0] + rng.uniform(-0.25, 0.25) * r, c[1] + rng.uniform(-0.25, 0.25) * r, c[2] - 0.02))
        d = Vector((math.cos(a), math.sin(a), 0))
        mid = base + d * (hb * lean * 0.35) + Vector((0, 0, hb * 0.6))
        tip = base + d * (hb * lean) + Vector((0, 0, hb * (1.0 - lean * 0.45)))
        mb.sweep(_tr._sections([base, mid, tip], [0.011 * r / 0.25, 0.007 * r / 0.25, 0.001], 4), mi)


def fern(mb, c, r, seed=0, mi=0):
    rng = random.Random(seed)
    n = rng.randint(7, 11)
    for i in range(n):
        a = 2 * math.pi * i / n + rng.uniform(-0.25, 0.25)
        L = r * rng.uniform(0.75, 1.2)
        pitch = rng.uniform(0.35, 0.75)
        cx = c[0] + 0.5 * L * math.cos(pitch) * math.cos(a)
        cy = c[1] + 0.5 * L * math.cos(pitch) * math.sin(a)
        cz = c[2] + 0.5 * L * math.sin(pitch) + 0.05
        mb.pillow(cx, cy, cz, w=L * 0.28, d=L, t=0.018, mi=mi, rot=a - math.pi / 2, pitch=pitch)


def agave(mb, c, n=14, L=0.55, seed=0, mi=0):
    """Rosette of stiff pointed leaves (tapered hexahedra) rising from the ground."""
    rng = random.Random(seed)
    for i in range(n):
        a = 2 * math.pi * i / n + rng.uniform(-0.2, 0.2)
        pitch = rng.uniform(0.55, 1.15) if i % 2 else rng.uniform(0.25, 0.6)
        ll = L * rng.uniform(0.7, 1.1)
        d = Vector((math.cos(a) * math.cos(pitch), math.sin(a) * math.cos(pitch), math.sin(pitch)))
        s = Vector((-math.sin(a), math.cos(a), 0))
        base = Vector(c)
        w0, w1 = 0.09 * ll / 0.5, 0.005
        p0 = base + d * 0.05
        p1 = base + d * ll
        mb.hexa([tuple(p0 - s * w0), tuple(p0 + s * w0), tuple(p1 + s * w1), tuple(p1 - s * w1),
                 tuple(p0 - s * w0 + Vector((0, 0, 0.02))), tuple(p0 + s * w0 + Vector((0, 0, 0.02))),
                 tuple(p1 + s * w1 + Vector((0, 0, 0.006))), tuple(p1 - s * w1 + Vector((0, 0, 0.006)))], mi)


def fallen_leaves(mb, rng, n, x0, x1, y0, y1, z, mi=0):
    for i in range(n):
        mb.pillow(rng.uniform(x0, x1), rng.uniform(y0, y1), z + 0.004, w=rng.uniform(0.05, 0.09), d=rng.uniform(0.03, 0.06), t=0.006,
                  mi=mi, rot=rng.uniform(0, math.pi), tilt=rng.uniform(-0.15, 0.15))


def hedge(T, x0, x1, y0, y1, z0, h, size=0.16, seed=0, cov=1.1):
    """Clipped hedge: a rounded dark core box (added by the caller) + a shell of small cards in a grid of clumps."""
    rng = random.Random(seed)
    nx = max(1, int((x1 - x0) / 0.45)); ny = max(1, int((y1 - y0) / 0.45))
    for i in range(nx):
        for j in range(ny):
            cx = x0 + (x1 - x0) * (i + 0.5) / nx + rng.uniform(-0.05, 0.05)
            cy = y0 + (y1 - y0) * (j + 0.5) / ny + rng.uniform(-0.05, 0.05)
            R = min(0.45, max(x1 - x0, y1 - y0) * 0.3, h * 0.55)
            T.clump((cx, cy, z0 + h * 0.55), R, size, cov=cov, up_bias=0.5, flat=0.3, shell=0.3, core=0.0, cap=140)


def _uplight(name, x, y, z, target, energy=60.0):
    add_light(name, 'SPOT', (x, y, z + 0.08), energy, (1.0, 0.8, 0.6), size=0.06, spot=math.radians(50), blend=0.7, target=target)


# ================================================================== scene
def build(M):
    rng = random.Random(7)
    lm = local_mats()
    L = _tr.leaf_materials()

    # ---- 1. street: two big kerb-side trees in the parkway (photo 02), limbed up over the sidewalk / lawn corridor
    sx0, sy0 = STREET_TREES[0]
    sx1, sy1 = STREET_TREES[1]
    # the -X oak frames the left of the street views; the +X plane tree is upright and narrow, parked beyond the
    # driveway (x 11.7) so the end-card camera at (5, -24, 12.5) sees the porch side of the house past it
    # southern magnolia over the sidewalk at the front-left (photo 00): trunk where the kerb oak stood, a 4 m crown limbed
    # up 3 m, one long low limb reaching toward the street in front of the hero camera so its hanging leaves frame the
    # top-left corner of that view (the crown itself stays left of the camera -> facade lines)
    magnolia(M, "MagnoliaKerbW", (sx0 - 0.6, sy0, ZG), height=9.0, crown_r=4.0, limb_up=3.0, seed=1, reach=(-1.7, sy0 - 1.0, 2.9))
    oak(M, "PlaneKerbE", (11.7, sy1 - 0.3, ZG), height=12.0, spread=6.5, trunk_r=0.4, seed=2, lean=(0.6, -0.2), trunk_f=0.52, detail=1.0,
        min_z=ZG + 6.5, plane=True)
    # across the street (y -27): a row of hazed mid-LOD oaks / elms, the nearest well clear of the end-card camera (5, -24, 12.5)
    # (varied heights / leans / spreads and a smaller companion tree at three spots, so the row does not read as
    #  identical balls on sticks from the driveway and the aerial descent)
    for i, (x, h, lean, comp) in enumerate(((-24.0, 13.0, (0.8, 0.3), True), (-14.0, 10.5, (-0.6, 0.4), False), (-5.0, 11.5, (0.5, -0.3), True),
                                          (13.0, 9.5, (-0.9, 0.2), True), (22.0, 13.5, (0.4, 0.5), False))):
        y = -27.0 + rng.uniform(-0.8, 0.8)
        oak(M, f"OakAcross_{i}", (x, y, ZG), height=h, spread=h * rng.uniform(0.95, 1.15), trunk_r=0.36 + h * 0.012, seed=10 + i, lean=lean,
            trunk_f=rng.uniform(0.3, 0.4), detail=0.5, min_z=ZG + 3.5, ring=True)
        if comp:
            h2 = h * rng.uniform(0.55, 0.7)
            oak(M, f"OakAcross_{i}b", (x + rng.uniform(4.5, 6.0), y - rng.uniform(2.0, 4.0), ZG), height=h2, spread=h2 * 1.1, trunk_r=0.3, seed=30 + i,
                lean=(-lean[0] * 0.5, 0.3), trunk_f=0.33, detail=0.4, min_z=ZG + 2.5, ring=True)
    for i, (x, y, h) in enumerate(((-30.0, -36.0, 14.0), (-18.0, -38.0, 12.0), (-6.0, -40.0, 15.0), (6.0, -37.0, 11.0), (18.0, -39.0, 13.0), (30.0, -36.0, 12.0))):
        if i % 3 == 1:
            conifer(M, f"ConiferBack_{i}", (x, y, ZG), height=h * 1.9, r=h * 0.25, seed=20 + i, kind="redwood", detail=0.35, ring=True)
        else:
            oak(M, f"OakBack_{i}", (x, y, ZG), height=h, spread=h * 0.85, trunk_r=0.45, seed=20 + i, detail=0.18, ring=True)

    # ---- 2. front yard: ornamental olive with a mulch ring, a mulch bed along the foundation planted with clipped
    #         boxwood balls, white hydrangeas, agapanthus + lavender; hydrangea + boxwood flanking the porch steps
    #         (the lawn's hair particles stop at y -0.45, so the bed runs y -0.52 .. the wall / the porch parapet)
    # photo 00: an open lawn (no front tree); a curved low brick curb (site) bounds a shallow bed along the house, from
    # y -1.0 at the walk (x -0.9..0.35) to -1.8 at the ends.  The bed follows that line 5 cm inside it, leaves the
    # walk + entry steps free, and runs to the living-block wall / the porch parapet.
    def y_curb(x):
        if x < 0:
            t = min(1.0, max(0.0, (-0.95 - x) / (5.75 - 0.95)))
        else:
            t = min(1.0, max(0.0, (x - 0.4) / (5.7 - 0.4)))
        return -1.0 - 0.8 * t ** 1.3
    bed = MB()
    left = [(-5.75, -0.02), (-0.95, -0.02), (-0.95, -1.0 + 0.05)]
    left += [(x, y_curb(x) + 0.05) for x in [-0.95 - (5.75 - 0.95) * k / 14 for k in range(1, 15)]]
    bed.prism(left, ZG - 0.03, ZG + 0.018, 0)
    right = [(0.4, -0.02), (1.25, -0.02), (1.25, 0.2), (5.7, 0.2), (5.7, y_curb(5.7) + 0.05)]
    right += [(x, y_curb(x) + 0.05) for x in [5.7 - (5.7 - 0.4) * k / 14 for k in range(1, 15)]]
    bed.prism(right, ZG - 0.03, ZG + 0.018, 0)
    bed.build("Land_FrontBeds", lm['mulch_bed'], coll='Landscape')
    k = 0
    # two staggered rows: clipped boxwood / lavender against the wall, hydrangea / agapanthus / lavender along the
    # curb; nothing in front of the entry steps (x -1.25..1.2) - the curb-side row sits 0.55 m inside the curb line
    back = ((-5.25, -0.36, 0.36, 'boxwood', None), (-4.35, -0.36, 0.36, 'boxwood', None), (-3.45, -0.36, 0.36, 'boxwood', None),
            (-2.55, -0.36, 0.36, 'boxwood', None), (-1.75, -0.34, 0.30, 'lavender', None),
            (1.6, -0.25, 0.30, 'boxwood', None), (2.35, -0.25, 0.32, 'lavender', None), (3.1, -0.25, 0.32, 'boxwood', None),
            (3.9, -0.25, 0.42, 'agapanthus', None), (4.7, -0.25, 0.32, 'boxwood', None), (5.35, -0.25, 0.30, 'lavender', None))
    front = ((-5.5, 0.42, 'agapanthus', None), (-4.8, 0.42, 'hydrangea', 'hyd_white'), (-3.9, 0.32, 'lavender', None),
             (-3.0, 0.42, 'hydrangea', 'hyd_white'), (-2.1, 0.42, 'agapanthus', None), (-1.7, 0.40, 'hydrangea', 'hyd_white'),
             (1.75, 0.42, 'hydrangea', 'hyd_white'), (2.65, 0.40, 'agapanthus', None), (3.55, 0.42, 'hydrangea', 'hyd_white'),
             (4.4, 0.32, 'lavender', None), (5.2, 0.42, 'hydrangea', 'hyd_white'))
    for (x, y, r, kind, col) in list(back) + [(x, y_curb(x) + 0.55, r, kind, col) for (x, r, kind, col) in front]:
        h = {'boxwood': r * 1.75, 'hydrangea': r * 1.55, 'agapanthus': r * 1.5, 'lavender': r * 1.3}[kind]
        _pl.shrub(f"Land_Front_{kind}_{k}", (x, y, ZG), r=r, h=h, kind=kind, seed=200 + k, coll='Landscape', colour=col); k += 1
    # white oleander by the driveway at the front-right (photo 00 right edge): two 3.5-4 m flowering masses on the
    # +X lot line, over dark cores; the driveway hedge starts behind them
    oc = MB()
    for j, (ox_, oy_, h, r) in enumerate(((9.95, -2.6, 3.6, 1.5), (10.35, 0.5, 3.9, 1.6))):
        _pl.shrub(f"Land_OleanderFront_{j}", (ox_, oy_, ZG), r=r, h=h, kind='oleander', seed=70 + j, coll='Landscape', colour='oleander_white')
        for (cz, R) in ((ZG + h * 0.35, r * 0.5), (ZG + h * 0.62, r * 0.55), (ZG + h * 0.82, r * 0.42)):
            oc.blob((ox_ + rng.uniform(-0.15, 0.15), oy_ + rng.uniform(-0.2, 0.2), cz), R, seg=10, rings=7, jitter=0.5, seed=j * 7 + int(cz * 3), mi=0, squash=1.1)
    oc.build("Land_OleanderFrontCore", lm['hedge_core'], coll='Landscape', smooth=True)
    # clipped hedges: along the -X lot line at the front, and the tall privet along the driveway fence (photo 30)
    _pl.hedge("Land_HedgeW", -6.65, -6.15, -6.0, -0.2, ZG, 0.8, kind='hedge', seed=41, size=0.075, cov=1.4)
    _pl.hedge("Land_HedgeE", 10.15, 10.9, 2.6, 16.0, ZG, 1.6, kind='privet', seed=42, size=0.095, cov=1.25)

    # ---- 3. side yards + the neighbours' trees that frame the side views
    oak(M, "OakSideW", (-13.5, 0.0, ZG), height=11.0, spread=9.0, trunk_r=0.48, seed=5, lean=(-1.0, 0.2), trunk_f=0.42, detail=1.0, min_z=ZG + 5.0)   # the tan neighbour's front yard
    oak(M, "OakNeighbourE", (15.5, 9.0, ZG), height=12.5, spread=10.5, trunk_r=0.5, seed=15, lean=(-0.6, -0.3), trunk_f=0.4, detail=0.6, min_z=ZG + 4.0)  # over the driveway hedge (photo 30)
    oak(M, "OakNeighbourWRear", (-14.5, 21.0, ZG), height=11.0, spread=9.0, trunk_r=0.45, seed=16, lean=(0.4, 0.5), trunk_f=0.42, detail=0.45)
    olive(M, "CitrusW", (-6.3, 13.5, ZG), height=3.4, seed=6, detail=1.0)
    olive(M, "TreeDriveE", (9.8, 5.0, ZG), height=4.0, seed=7, detail=1.0)

    # ---- 4. rear: redwoods + pine beyond the rear-left fence (photos 27/28), a neighbour's oak at +X rear
    conifer(M, "Redwood_0", (-9.0, 50.0, ZG), height=21.0, r=4.0, seed=8, kind='redwood', detail=0.6)
    conifer(M, "Redwood_1", (-3.0, 52.5, ZG), height=23.0, r=4.4, seed=9, kind='redwood', detail=0.6)
    conifer(M, "Redwood_2", (3.5, 55.0, ZG), height=19.0, r=3.8, seed=10, kind='redwood', detail=0.6)
    conifer(M, "PineW", (-11.5, 42.0, ZG), height=18.0, r=4.6, seed=11, kind='pine', detail=0.6)
    oak(M, "OakRearE", (13.5, 40.0, ZG), height=11.0, spread=9.5, trunk_r=0.45, seed=12, detail=0.6)
    for i, (x, y, h) in enumerate(((-16.0, 56.0, 26.0), (10.0, 60.0, 30.0), (20.0, 52.0, 22.0), (-22.0, 48.0, 24.0))):
        conifer(M, f"ConiferFar_{i}", (x, y, ZG), height=h, r=h * 0.13, seed=50 + i, kind='redwood' if i % 2 == 0 else 'pine', detail=0.3, ring=True)
    # oleander: a dense 3-3.5 m white-flowering mass straddling the +X fence behind the garage (photos 27/28):
    # five overlapping flowering shrubs over dark cores so the mass never reads see-through
    ox, oy0, oy1 = OLEANDER
    oc = MB()
    for j, (oy, h, r) in enumerate(((26.3, 3.0, 1.35), (28.0, 3.4, 1.6), (29.9, 3.2, 1.7), (31.7, 3.5, 1.6), (33.3, 3.0, 1.4))):
        cx = ox + rng.uniform(-0.2, 0.2)
        _pl.shrub(f"Land_Oleander_{j}", (cx, oy, ZG), r=r, h=h, kind='oleander', seed=60 + j, coll='Landscape', colour='oleander_white')
        for (cz, R) in ((ZG + h * 0.35, r * 0.55), (ZG + h * 0.62, r * 0.6), (ZG + h * 0.82, r * 0.45)):
            oc.blob((cx + rng.uniform(-0.15, 0.15), oy + rng.uniform(-0.2, 0.2), cz), R, seg=10, rings=7, jitter=0.5, seed=j * 9 + int(cz * 3), mi=0, squash=1.1)
    oc.build("Land_OleanderCore", lm['hedge_core'], coll='Landscape', smooth=True)
    olive(M, "CitrusGarage", (8.0, 27.0, ZG), height=4.0, seed=13, detail=1.0)
    olive(M, "OliveLawnFar", (2.5, 37.0, ZG), height=4.5, seed=14, detail=1.0)
    # rose shrubs in the two patio cut-outs (photo 29): one pink, one white
    for i, (x, y) in enumerate(SHRUB_BEDS):
        _pl.shrub(f"Land_Rose_{i}", (x, y, ZG), r=0.5, h=0.85, kind='rose', seed=230 + i, coll='Landscape', colour='rose_pink' if i == 0 else 'rose_white')
    # mixed shrub border on a mulch strip along the -X fence (the rear lawn's hair starts at x -6.35) + a few
    # along the rear fence between the shed and the garage line
    bed = MB()
    bed.rbox(-6.73, -6.3, 22.3, 39.7, ZG - 0.03, ZG + 0.016, r=0.012, mi=0)
    bed.rbox(-2.3, 9.8, 46.05, 47.3, ZG - 0.03, ZG + 0.016, r=0.012, mi=0)
    bed.build("Land_RearBeds", lm['mulch_bed'], coll='Landscape')
    k = 0
    for (y, r, h, kind, col) in ((23.4, 0.75, 0.95, 'hydrangea', 'hyd_white'), (25.3, 0.55, 0.8, 'agapanthus', None), (27.0, 0.65, 1.1, 'boxwood', None),
                                 (28.9, 0.8, 1.0, 'hydrangea', 'hyd_blue'), (30.8, 0.5, 0.65, 'lavender', None), (32.4, 0.6, 0.85, 'rosemary', None),
                                 (34.3, 0.75, 0.95, 'hydrangea', 'hyd_white'), (36.2, 0.55, 0.8, 'agapanthus', None), (38.0, 0.65, 1.1, 'boxwood', None)):
        _pl.shrub(f"Land_BorderW_{k}", (-6.22, y, ZG), r=r, h=h, kind=kind, seed=240 + k, coll='Landscape', colour=col); k += 1
    for (x, r, h, kind, col) in ((0.3, 0.8, 1.0, 'hydrangea', 'hyd_white'), (2.2, 0.6, 1.05, 'boxwood', None), (4.2, 0.55, 0.8, 'agapanthus', None),
                                 (6.0, 0.75, 1.0, 'hydrangea', 'hyd_blue'), (7.9, 0.6, 0.85, 'rosemary', None), (9.3, 0.55, 0.95, 'boxwood', None)):
        _pl.shrub(f"Land_BorderN_{k}", (x, 46.65, ZG), r=r, h=h, kind=kind, seed=260 + k, coll='Landscape', colour=col); k += 1
    # ferns beside the shed door (real arching fronds) + agaves (the shed's -Y end is y = SHED[2])
    F = _pl.Foliage(300)
    for i, (x, y, h) in enumerate(((SHED[0] + 0.5, SHED[2] - 0.7, 0.5), (SHED[1] - 0.4, SHED[2] - 0.8, 0.55), (SHED[1] + 0.6, SHED[2] + 0.4, 0.45), (SHED[0] - 0.5, SHED[2] + 1.0, 0.5))):
        _pl._fern(F, x, y, ZG + 0.01, h, spread=1.1)
    PM = _pl.mats()
    F.build("Land_Ferns", [PM['terracotta'], PM['soil'], PM['stem'], L['core'], PM['cane']], coll='Landscape')
    ag = MB()
    for i, (x, y) in enumerate(((SHED[1] + 1.4, SHED[2] - 0.3), (SHED[0] - 0.3, SHED[2] - 1.6))):
        agave(ag, (x, y, ZG), n=16, L=0.5, seed=310 + i, mi=0)
    ag.build("Land_Agaves", lm['agave'], coll='Landscape', smooth=True)

    # ---- 5. ground cover: grass tufts along the fences / under the redwoods, fallen leaves on the driveway (photo 30)
    gc = MB()
    k = 0
    for i in range(18):
        grass_tuft(gc, (-6.45 + rng.uniform(-0.1, 0.1), 22.5 + i * 1.35 + rng.uniform(-0.3, 0.3), ZG), rng.uniform(0.16, 0.26), seed=400 + k, mi=0, blades=14); k += 1
    for i in range(14):
        grass_tuft(gc, (-5.0 + i * 1.05 + rng.uniform(-0.3, 0.3), 46.6 + rng.uniform(-0.2, 0.2), ZG), rng.uniform(0.18, 0.3), seed=400 + k, mi=0, blades=14); k += 1
    for (x, y) in ((-9.0, 48.0), (-3.0, 49.5), (3.5, 51.0), (-11.0, 40.5)):
        for j in range(4):
            grass_tuft(gc, (x + rng.uniform(-1.4, 1.4), y + rng.uniform(-1.4, 1.4), ZG), rng.uniform(0.2, 0.32), seed=400 + k, mi=0, blades=12); k += 1
    for i in range(10):                                           # along the +X fence in the front / driveway
        grass_tuft(gc, (10.05 + rng.uniform(-0.1, 0.1), -6.0 + i * 1.3, ZG), rng.uniform(0.15, 0.25), seed=400 + k, mi=0, blades=12); k += 1
    gc.build("Land_GrassTufts", M['grass_tuft'], coll='Landscape', smooth=True)
    fl = MB()
    fallen_leaves(fl, rng, 140, DRIVE_X[0] + 0.1, DRIVE_X[1] - 0.1, -6.5, 16.5, ZG, mi=0)
    fallen_leaves(fl, rng, 40, LOT[0] + 0.2, LOT[0] + 1.6, 22.0, 39.0, ZG, mi=0)
    fl.build("Land_FallenLeaves", lm['dead_leaf'], coll='Landscape', smooth=True)

    # ---- 6. landscape uplights (front olive, both street trees, the -X oak, two on the redwoods)
    _uplight("Land_UpKerbW", sx0 + 0.6, sy0 + 0.8, ZG, (sx0 - 0.6, sy0, ZG + 7.5), energy=90)
    _uplight("Land_UpKerbE", 10.6, sy1 + 0.6, ZG, (11.7, sy1 - 0.3, ZG + 8.5), energy=90)
    _uplight("Land_UpOakW", -9.2, 8.8, ZG, (-10.8, 8.0, ZG + 7.5), energy=80)
    _uplight("Land_UpRedwood0", -7.5, 47.6, ZG, (-9.0, 50.0, ZG + 14.0), energy=120)
    _uplight("Land_UpRedwood1", -1.8, 47.6, ZG, (-3.0, 52.5, ZG + 16.0), energy=120)

    # ---- 7. neighbourhood backdrop ring (62-110 m): hazed low-LOD trees so no view ends on an empty horizon.
    #         Nearer spots carry two overlapping trees of different heights (a leaning big one + a smaller one) at
    #         detail 0.3 so silhouettes stop being single spheres; the far spots one tree at detail 0.22.
    i = 0
    for j in range(64):
        a = 2 * math.pi * j / 64 + rng.uniform(-0.03, 0.03)
        d = rng.uniform(62, 110)
        x, y = d * math.cos(a), 8.0 + d * math.sin(a)
        near = d < 82
        if i % 4 == 2:
            conifer(M, f"Ring_Conifer_{i}", (x, y, ZG), height=rng.uniform(18, 34), r=rng.uniform(2.6, 3.8), seed=600 + i, kind='redwood' if i % 8 == 2 else 'pine',
                    detail=0.3 if near else 0.2, ring=True)
        else:
            h = rng.uniform(9, 17)
            oak(M, f"Ring_Oak_{i}", (x, y, ZG), height=h, spread=h * rng.uniform(0.75, 1.05), trunk_r=rng.uniform(0.4, 0.6),
                seed=600 + i, lean=(rng.uniform(-1.2, 1.2), rng.uniform(-1.2, 1.2)), trunk_f=rng.uniform(0.3, 0.45), detail=0.3 if near else 0.22, ring=True)
            if near or j % 3 == 0:
                h2 = h * rng.uniform(0.5, 0.75)
                dx, dy = rng.uniform(4, 8) * (1 if j % 2 else -1), rng.uniform(-4, 4)
                oak(M, f"Ring_Oak_{i}b", (x + dx, y + dy, ZG), height=h2, spread=h2 * rng.uniform(0.8, 1.1), trunk_r=rng.uniform(0.3, 0.45),
                    seed=700 + i, lean=(rng.uniform(-0.8, 0.8), rng.uniform(-0.8, 0.8)), detail=0.22 if near else 0.16, ring=True)
        i += 1
