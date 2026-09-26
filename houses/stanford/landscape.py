"""Vegetation for 13695 Stanford Dr (photos 01-03, 25-32): the dense oval front-yard tree (a Callery pear / linden
form) in its white-rock ring, the neighbours' front trees, maiden-grass clumps at the right front corner, foundation
perennials and porch pots, the two big arching shrubs at the rear corners, iris clumps + hydrangea in the patio's
rock border and the blue spruce at the neighbour's fence corner.  The common-area / pond-shore trees, the trees
across the pond and the drone-horizon ring are context.py (they use tree() from here).

Trees: archviz.trees skeletons + leaf cards with midsummer (daylight) leaf colours.  Object names start with Land_.
"""
import math
import random
from .plan import *
from archviz.mesh import MB
from archviz import materials as _m
from archviz import trees as _tr
from archviz import plants as _pl

ZG = Z_GRADE
_LM = {}


def local_mats():
    if _LM:
        return _LM
    _LM['bark'] = _m.noise_mat("BarkGreyBrown", (0.10, 0.085, 0.07, 1), (0.24, 0.21, 0.17, 1), scale=14, bump=1.0, spec=0.06, bump_dist=0.03)
    _LM['bark_birch'] = _m.noise_mat("BarkBirch", (0.55, 0.53, 0.48, 1), (0.85, 0.84, 0.80, 1), scale=9, bump=0.4, spec=0.1)
    _LM['leaf_pear'] = _tr._oak_spray_card("LeafPearGloss", (0.030, 0.085, 0.020, 1), (0.065, 0.16, 0.040, 1), (0.13, 0.25, 0.065, 1),
                                           translucent=0.35, n=6, a=0.20, b=0.12, rough=0.45)
    # the front Callery pear (01 canopy mean sRGB (53-76, 61-87, 36-51), p90 (135-175, 143-188, 103-137): glossy leaves that
    # catch the sky) - calibrated with polish renders of 01 / 30
    _LM['leaf_pear_fine'] = _tr._oak_spray_card("LeafPearFine", (0.15, 0.23, 0.055, 1), (0.23, 0.33, 0.085, 1), (0.34, 0.43, 0.13, 1),
                                                translucent=0.5, n=11, a=0.085, b=0.052, rough=0.28)
    _LM['core_pear'] = _tr._holey(_m.noise_mat("CanopyCorePear", (0.06, 0.10, 0.03, 1), (0.10, 0.16, 0.045, 1), scale=3, rough=1.0, spec=0.02,
                                               bump=0.0), "CanopyCorePearHoley", 0.45, 4.0)
    _LM['leaf_locust'] = _tr._oak_spray_card("LeafHoneyLocust", (0.16, 0.24, 0.04, 1), (0.26, 0.36, 0.07, 1), (0.38, 0.46, 0.12, 1),
                                             translucent=0.45, n=9, a=0.12, b=0.06, rough=0.55)
    _LM['leaf_maple'] = _tr._oak_spray_card("LeafMaple", (0.04, 0.11, 0.03, 1), (0.10, 0.21, 0.05, 1), (0.20, 0.32, 0.09, 1),
                                            translucent=0.4, n=5, a=0.26, b=0.18, rough=0.55)
    _LM['leaf_far'] = _tr._attr_random(_m.leaf_card("LeafFarSummer", (0.04, 0.10, 0.03, 1), (0.09, 0.19, 0.05, 1), (0.17, 0.29, 0.08, 1),
                                                    0.3, shape='cluster', rough=0.7))
    _LM['leaf_shrub'] = _tr._oak_spray_card("LeafSpirea", (0.10, 0.20, 0.04, 1), (0.20, 0.34, 0.08, 1), (0.34, 0.46, 0.14, 1),
                                            translucent=0.5, n=10, a=0.10, b=0.05, rough=0.6)
    _LM['core'] = _m.noise_mat("CanopyCoreSummer", (0.015, 0.04, 0.012, 1), (0.04, 0.08, 0.025, 1), scale=3, rough=1.0, spec=0.02, bump=0.0)
    _LM['core_holey'] = _tr._holey(_LM['core'], "CanopyCoreSummerHoley", 0.55, 4.0)
    _LM['grass_blade'] = _m.foliage("MaidenGrass", (0.20, 0.26, 0.10, 1), (0.42, 0.46, 0.24, 1), 0.45, c3=(0.62, 0.60, 0.40, 1), rough=0.6)
    _LM['iris'] = _m.foliage("IrisLeaves", (0.12, 0.26, 0.06, 1), (0.30, 0.46, 0.14, 1), 0.45, c3=(0.48, 0.58, 0.22, 1), rough=0.5)
    _LM['hosta'] = _m.foliage("HostaLeaves", (0.08, 0.20, 0.05, 1), (0.22, 0.40, 0.10, 1), 0.35, rough=0.5)
    # rear corner shrubs (25-28): small narrow alternate leaves on long arching canes; the +X one sunlit yellow-green,
    # the -X one a darker, denser green (explicit leaves, archviz.plants.leaf_shader)
    _LM['leaf_arch_light'] = _pl.leaf_shader("LeafArchingLight", 'elliptic', (0.34, 0.42, 0.09, 1), (0.46, 0.53, 0.13, 1), (0.58, 0.62, 0.20, 1),
                                             under=(0.52, 0.56, 0.28, 1), translucent=0.45, rough=0.5, coat=0.1, p=0.95, q=0.9, rib=0.012)
    _LM['leaf_arch_dark'] = _pl.leaf_shader("LeafArchingDark", 'elliptic', (0.13, 0.22, 0.055, 1), (0.19, 0.29, 0.075, 1), (0.27, 0.37, 0.11, 1),
                                            under=(0.34, 0.42, 0.20, 1), translucent=0.4, rough=0.5, coat=0.1, p=0.95, q=0.9, rib=0.012)
    _LM['spray_arch_light'] = _tr._oak_spray_card("SprayArchingLight", (0.33, 0.41, 0.085, 1), (0.45, 0.52, 0.12, 1), (0.57, 0.61, 0.19, 1),
                                                  translucent=0.45, n=7, a=0.13, b=0.045, rough=0.55)
    _LM['spray_arch_dark'] = _tr._oak_spray_card("SprayArchingDark", (0.12, 0.21, 0.05, 1), (0.18, 0.28, 0.07, 1), (0.26, 0.36, 0.10, 1),
                                                 translucent=0.4, n=7, a=0.13, b=0.045, rough=0.55)
    _LM['cane'] = _m.noise_mat("ShrubCane", (0.12, 0.09, 0.06, 1), (0.22, 0.17, 0.11, 1), scale=30, bump=0.4, rough=0.85)
    _LM['core_shrub'] = _tr._holey(_m.noise_mat("ShrubCoreDark", (0.025, 0.055, 0.015, 1), (0.05, 0.10, 0.03, 1), scale=4, rough=1.0,
                                                spec=0.02, bump=0.0), "ShrubCoreDarkHoley", 0.6, 5.0)
    return _LM


def tree(name, pos, height, spread, seed, kind='pear', detail=1.0, trunk_r=None, trunk_f=0.32, upright=0.9, min_z=None, lean=(0, 0),
         keep_out=None):
    lm = local_mats()
    rng = random.Random(seed)
    nb = 6 if kind != 'locust' else 5
    limbs = [(2 * math.pi * i / nb + rng.uniform(-0.3, 0.3), spread * rng.uniform(0.42, 0.55), upright * rng.uniform(0.8, 1.25))
             for i in range(nb)]
    leaf = {'pear': lm['leaf_pear'], 'locust': lm['leaf_locust'], 'maple': lm['leaf_maple'], 'birch': lm['leaf_maple']}[kind] if detail >= 0.45 else lm['leaf_far']
    bark = lm['bark_birch'] if kind == 'birch' else lm['bark']
    return _tr.oak("Land_" + name, pos, height, spread, trunk_r or height * 0.028, seed, lean, trunk_f, limbs, detail, keep_out,
                   'Landscape', {'bark': bark, 'leaf': leaf, 'core': lm['core_holey'] if detail >= 0.45 else lm['core']}, min_z)


def prune(name, box):
    """Delete the faces of object `name` whose centres lie inside box (x0, x1, y0, y1, z0, z1): leaf cards that a
    crown would otherwise push through a wall or an eave."""
    import bpy
    import bmesh
    ob = bpy.data.objects.get(name)
    if ob is None:
        return 0
    x0, x1, y0, y1, z0, z1 = box
    bm = bmesh.new(); bm.from_mesh(ob.data)
    mw = ob.matrix_world
    dead = []
    for f in bm.faces:
        c = mw @ f.calc_center_median()
        if x0 < c.x < x1 and y0 < c.y < y1 and z0 < c.z < z1:
            dead.append(f)
    bmesh.ops.delete(bm, geom=dead, context='FACES')
    bm.to_mesh(ob.data); bm.free()
    return len(dead)


def grass_clump(mb, x, y, z, h, r, seed, n=70, mi=0, arch=0.45):
    """Ornamental grass / iris fan: tapered strap blades leaning outward and arching over."""
    rng = random.Random(seed)
    for i in range(n):
        a = rng.uniform(0, 2 * math.pi)
        lean = rng.uniform(0.1, 1.0) * arch
        L = h * rng.uniform(0.6, 1.05)
        w = rng.uniform(0.008, 0.016) * (h / 1.0) ** 0.3
        pts = []
        base = (x + math.cos(a) * r * rng.uniform(0, 0.5), y + math.sin(a) * r * rng.uniform(0, 0.5), z)
        for k in range(6):
            t = k / 5
            out = r * 0.6 * t + L * lean * t * t
            pts.append((base[0] + math.cos(a) * out, base[1] + math.sin(a) * out, z + L * (t - 0.35 * lean * t * t)))
        # flat blade: two rows offset sideways
        px, py = -math.sin(a) * w, math.cos(a) * w
        vs = []
        for k, p in enumerate(pts):
            ww = (1 - k / 6)
            vs += [(p[0] - px * ww, p[1] - py * ww, p[2]), (p[0] + px * ww, p[1] + py * ww, p[2])]
        b0 = len(mb.v)
        mb.v.extend(vs)
        for k in range(len(pts) - 1):
            mb.f.append((b0 + 2 * k, b0 + 2 * k + 1, b0 + 2 * k + 3, b0 + 2 * k + 2)); mb.fm.append(mi)


def shrub_mass(name, c, r, h, seed, detail=1.0, card=0.22):
    """A loose, arching deciduous shrub (ninebark / forsythia form): a few canes + leaf-cluster cards."""
    lm = local_mats()
    T = _tr.Tree(seed, detail)
    rng = T.rng
    from mathutils import Vector
    x, y, z = c
    for i in range(9):
        a = 2 * math.pi * i / 9 + rng.uniform(-0.3, 0.3)
        tip = Vector((x + math.cos(a) * r * rng.uniform(0.6, 1.0), y + math.sin(a) * r * rng.uniform(0.6, 1.0), z + h * rng.uniform(0.7, 1.0)))
        mid = Vector((x + math.cos(a) * r * 0.35, y + math.sin(a) * r * 0.35, z + h * 0.55))
        T.tube([Vector((x, y, z)), mid, tip], [0.03, 0.02, 0.008])
        T.clump(tip, r * 0.40, card, cov=0.75, up_bias=0.2, flat=0.1, shell=0.8, core=0.35)
        T.clump(mid, r * 0.36, card, cov=0.55, up_bias=0.2, flat=0.1, shell=0.8, core=0.35)
    T.build("Land_" + name, lm['bark'], lm['leaf_shrub'], coll='Landscape', core_mat=lm['core_holey'], core_seg=8)
    return T


def arching_shrub(name, c, height, radius, seed, canes=40, leaf='leaf_arch_light', droop=0.35, bias=(0.0, 0.0), core=0.0,
                  twig=0.40, leaf_size=(0.06, 0.021), pitch=0.030, avoid_y=None, spacing=0.11, flat=0.0, spray=None, spray_every=0.32,
                  spray_r=0.22, spray_size=0.22, spray_cov=0.6):
    """A multi-stemmed arching shrub (forsythia / spirea form, photos 25-28): `canes` long stems rise from a clump at
    c, lean outward (biased toward `bias`) and arch over under `droop`; leafy twigs (explicit leaves) every
    `spacing` m along their outer 75 %, with side twigs of their own.  `core` > 0 adds a dark inner mass (dense
    shrubs).  avoid_y: keep stems at y > it (the house wall).  flat: 0 = tall vase form, 1 = mounded."""
    from mathutils import Vector
    lm = local_mats()
    T = _tr.Tree(seed, 1.0)
    T2 = _tr.Tree(seed + 1000, 1.0) if spray else None
    rng = T.rng
    x, y, z = c
    for i in range(canes):
        a = rng.uniform(0, 2 * math.pi)
        ox, oy = math.cos(a) + bias[0], math.sin(a) + bias[1]
        n = math.hypot(ox, oy) or 1.0
        ox, oy = ox / n, oy / n
        if avoid_y is not None and oy < -0.2:
            oy = -0.2 + rng.uniform(0, 0.3)
        r0 = rng.uniform(0.0, 0.2)
        start = Vector((x + ox * r0, y + oy * r0, z - 0.05))
        inner = rng.random() < 0.35                               # upright inner canes fill the middle
        tilt = rng.uniform(0.05, 0.3) if inner else rng.uniform(0.3, 0.9) * (1.0 + flat)
        d0 = Vector((ox * tilt, oy * tilt, 1.0)).normalized()
        L = height * (rng.uniform(0.75, 1.05) if inner else rng.uniform(0.95, 1.35))
        g = droop * rng.uniform(0.6, 1.3) * (0.4 if inner else 1.0)
        pts, radii, _ = T.curve(start, d0, L, rng.uniform(0.010, 0.017), 0.003, n_sub=8, wiggle=0.06, gravity=g)
        reach = max(math.hypot(p.x - start.x, p.y - start.y) for p in pts)
        target = radius * (rng.uniform(0.35, 0.7) if inner else rng.uniform(0.75, 1.0)) - twig * 0.6
        if reach > target > 0:                                  # keep the crown inside its measured radius
            k_ = target / reach
            pts = [Vector((start.x + (p.x - start.x) * k_, start.y + (p.y - start.y) * k_, p.z)) for p in pts]
        if avoid_y is not None:
            pts = [Vector((p.x, max(p.y, avoid_y), p.z)) for p in pts]
        pts = [Vector((p.x, p.y, max(p.z, z + 0.03))) for p in pts]
        T.tube(pts, radii, 4)
        s_ = L * 0.25
        while s_ < L:
            k = s_ / L
            q, dq, rq = T._at(pts, radii, k)
            az = rng.uniform(0, 2 * math.pi)
            dd = _tr._rotate_away(dq, rng.uniform(0.45, 1.05), az)
            tl = twig * rng.uniform(0.6, 1.2) * (0.6 + 0.6 * k)
            T.leafy_twig(q, dd, tl, r0=0.0025, leaf=leaf_size, pitch=pitch, droop=0.45, drop=0.08)
            if rng.random() < 0.55:                                # a side twig off the twig
                T.leafy_twig(q + dd * tl * 0.5, _tr._rotate_away(dd, 0.7, rng.uniform(0, 6.28)), tl * 0.6, r0=0.002,
                             leaf=leaf_size, pitch=pitch, droop=0.5, drop=0.1)
            s_ += spacing * rng.uniform(0.6, 1.4)
        T.leafy_twig(pts[-1], (pts[-1] - pts[-2]).normalized(), twig * 1.2, r0=0.003, leaf=leaf_size, pitch=pitch, droop=0.6, drop=0.05)
        if T2 is not None:                                          # leaf-spray clumps give the mass its density
            s_ = L * 0.3
            while s_ < L:
                q, dq, rq = T._at(pts, radii, s_ / L)
                if avoid_y is None or q.y > avoid_y + spray_r * 0.6:
                    T2.clump(q, spray_r * rng.uniform(0.7, 1.2), spray_size, cov=spray_cov, up_bias=0.15, flat=0.15, shell=0.7, core=0.0)
                s_ += spray_every * rng.uniform(0.7, 1.3)
    if T2 is not None:
        T2.build("Land_" + name + "Spray", lm["cane"], lm[spray], coll="Landscape")
    if core > 0:
        cx, cy = x + bias[0] * radius * 0.3, y + bias[1] * radius * 0.3
        for (dx, dy, dz, f) in ((0, 0, 0.45, 1.0), (0.35, 0.2, 0.35, 0.8), (-0.35, 0.25, 0.38, 0.8), (0.0, 0.4, 0.3, 0.7)):
            T.core(Vector((cx + radius * dx, cy + radius * dy, z + height * dz)), radius * core * f, 0.75)
    T.build("Land_" + name, lm['cane'], lm[leaf], coll='Landscape', core_mat=lm['core_shrub'], core_seg=10)
    return T


def iris_clump(name, x, y, z, h, r, seed, fans=7):
    """Bearded-iris clump (photos 25-28): flat fans of 5-7 sword leaves (2.5-3 cm wide), outer leaves splaying and
    a few tips bending over; bright yellow-green in sun."""
    from mathutils import Vector
    MM = _pl.mats()
    if 'iris_leaf' not in MM:
        MM['iris_leaf'] = _pl.leaf_shader("LeafIrisSword", 'strap', (0.36, 0.48, 0.05, 1), (0.46, 0.56, 0.07, 1), (0.56, 0.62, 0.10, 1),
                                          under=(0.40, 0.50, 0.08, 1), translucent=0.5, rough=0.45, coat=0.15, rib=0.0)
    F = _pl.Foliage(seed)
    rng = F.rng
    for f in range(fans):
        a = rng.uniform(0, 2 * math.pi); rr = r * math.sqrt(rng.random())
        fx, fy = x + rr * math.cos(a), y + rr * math.sin(a)
        pa = rng.uniform(0, math.pi)                           # the fan's plane
        pd = Vector((math.cos(pa), math.sin(pa), 0.0))
        out = Vector((fx - x, fy - y, 0.0))
        nl = rng.randint(5, 7)
        for k in range(nl):
            t = (k - (nl - 1) / 2) / max(1, (nl - 1) / 2)       # -1 .. 1 across the fan
            ang = t * rng.uniform(0.25, 0.45)
            along = (Vector((0, 0, 1)) * math.cos(ang) + pd * math.sin(ang) + out * 0.25).normalized()
            L = h * (1.0 - 0.35 * abs(t)) * rng.uniform(0.8, 1.1)
            base = Vector((fx, fy, z)) + pd * (t * 0.02)
            droop = rng.uniform(0.0, 0.25) + (0.6 if rng.random() < 0.18 else 0.0)
            F.leaf('iris_leaf', base, along, pd, L, rng.uniform(0.032, 0.042), n=6, droop=droop, twist=rng.uniform(-0.3, 0.3),
                   up_normal=False)
    return F.build(name, [MM['stem']], coll='Landscape')


def _front_mats():
    MM = _pl.mats()
    if 'hosta_leaf' not in MM:
        S = _pl.leaf_shader
        MM['hosta_leaf'] = S("LeafHosta", 'heart', (0.09, 0.19, 0.07, 1), (0.13, 0.25, 0.09, 1), (0.18, 0.31, 0.12, 1), under=(0.24, 0.34, 0.20, 1),
                             translucent=0.3, rough=0.45, coat=0.15, p=0.85, q=0.7, veins=9, vein_k=0.55, rib=0.02)
        MM['lily_leaf'] = S("LeafDaylily", 'strap', (0.14, 0.26, 0.06, 1), (0.20, 0.33, 0.08, 1), (0.27, 0.40, 0.11, 1), translucent=0.4,
                            rough=0.5, coat=0.1, rib=0.0)
        MM['mgrass_leaf'] = S("LeafMaidenGrass", 'strap', (0.22, 0.30, 0.13, 1), (0.34, 0.40, 0.20, 1), (0.50, 0.52, 0.34, 1),
                              under=(0.55, 0.56, 0.42, 1), translucent=0.45, rough=0.55, coat=0.05, rib=0.0)
        MM['plume'] = _pl.flower_shader("FlowerGrassPlume", 'spike', (0.66, 0.60, 0.48, 1), (0.82, 0.78, 0.68, 1))
        MM['geranium'] = _pl.flower_shader("FlowerGeraniumRed", 'rose', (0.62, 0.03, 0.04, 1), (0.85, 0.12, 0.10, 1))
        MM['mum_white'] = _pl.flower_shader("FlowerMumWhite", 'ball', (0.86, 0.86, 0.80, 1), (0.97, 0.96, 0.92, 1), (0.92, 0.90, 0.70, 1))
        MM['lily_orange'] = _pl.flower_shader("FlowerDaylily", 'flat5', (0.85, 0.40, 0.05, 1), (0.95, 0.62, 0.15, 1))
        MM['juniper'] = _tr._attr_random(_m.leaf_card("LeafJuniper", (0.05, 0.11, 0.07, 1), (0.08, 0.16, 0.10, 1), (0.13, 0.22, 0.14, 1), 0.2,
                                                    shape='cluster', rough=0.7))
    return MM


def hosta(name, x, y, z, r=0.35, seed=0):
    """Hosta clump (03, 01): 12-20 heart-shaped, ribbed leaves on arching petioles radiating from the crown."""
    from mathutils import Vector
    MM = _front_mats()
    F = _pl.Foliage(seed)
    rng = F.rng
    n = int(16 + r * 48)
    for i in range(n):
        az = 2 * math.pi * i / n + rng.uniform(-0.25, 0.25)
        out = Vector((math.cos(az), math.sin(az), 0.0))
        el = rng.uniform(0.35, 0.9)
        pl_ = r * rng.uniform(0.35, 0.6)
        base = Vector((x, y, z))
        tip = base + (out * math.cos(el) + Vector((0, 0, 1)) * math.sin(el)) * pl_
        F.wood.tube(tuple(base), tuple(tip), 0.006, 0.004, seg=4, mi=2)
        L = r * rng.uniform(0.40, 0.62)
        d = (out + Vector((0, 0, rng.uniform(-0.05, 0.25)))).normalized()
        F.leaf('hosta_leaf', tuple(tip), d, out.cross(Vector((0, 0, 1))).normalized(), L, L * 0.72, n=3, droop=rng.uniform(0.3, 0.7))
    return F.build(name, [MM['stem'], MM['soil'], MM['stem']], coll='Landscape')


def strap_clump(name, x, y, z, h, r, seed=0, key='lily_leaf', n=40, flowers=None, n_flowers=0, arch=1.0, plumes=0):
    """Daylily / maiden-grass clump: arching strap leaves from a crown (explicit quads), optional flower scapes or
    grass plumes (flower_shader keys)."""
    from mathutils import Vector
    MM = _front_mats()
    F = _pl.Foliage(seed)
    rng = F.rng
    for i in range(n):
        az = rng.uniform(0, 2 * math.pi)
        out = Vector((math.cos(az), math.sin(az), 0.0))
        el = rng.uniform(0.9, 1.45)
        d = (out * math.cos(el) + Vector((0, 0, 1)) * math.sin(el)).normalized()
        b = Vector((x, y, z)) + out * r * rng.uniform(0.0, 0.35)
        L = h * rng.uniform(0.65, 1.1)
        W = (0.018 if key == 'lily_leaf' else 0.010) * rng.uniform(0.8, 1.2)
        F.leaf(key, tuple(b), d, out.cross(Vector((0, 0, 1))).normalized(), L, W, n=6, droop=arch * rng.uniform(0.6, 1.6), twist=rng.uniform(-0.6, 0.6),
               up_normal=False)
    for i in range(n_flowers):
        az = rng.uniform(0, 2 * math.pi)
        b = (x + math.cos(az) * r * 0.2, y + math.sin(az) * r * 0.2, z)
        top = (b[0] + math.cos(az) * 0.1, b[1] + math.sin(az) * 0.1, z + h * rng.uniform(1.05, 1.3))
        F.wood.tube(b, top, 0.004, 0.003, seg=4, mi=2)
        F.clump(flowers, top, 0.05, 0.05, cov=1.5, up_bias=0.3, flat=0.2, shell=0.5, cap=10)
    for i in range(plumes):
        az = rng.uniform(0, 2 * math.pi)
        lean = rng.uniform(0.05, 0.35)
        b = Vector((x + math.cos(az) * r * 0.3, y + math.sin(az) * r * 0.3, z))
        top = b + Vector((math.cos(az) * lean, math.sin(az) * lean, 1.0)).normalized() * h * rng.uniform(1.05, 1.25)
        F.wood.tube(tuple(b), tuple(top), 0.003, 0.002, seg=3, mi=2)
        for k in range(4):
            q = top + Vector((rng.uniform(-0.04, 0.04), rng.uniform(-0.04, 0.04), -0.05 * k))
            F.leaf('plume', tuple(q), (0, 0, 1), (1, 0, 0), 0.22, 0.03, n=2, droop=0.4)
    return F.build(name, [MM['stem'], MM['soil'], MM['stem']], coll='Landscape')


def juniper(name, x, y, z, r=1.1, h=0.75, seed=0):
    """Spreading juniper (30, 31): a low dense mound of blue-green scale-leaf sprays."""
    from mathutils import Vector
    MM = _front_mats()
    T = _tr.Tree(seed, 1.0)
    rng = T.rng
    for i in range(14):
        a = rng.uniform(0, 2 * math.pi); rr = r * math.sqrt(rng.random()) * 0.75
        c = Vector((x + rr * math.cos(a), y + rr * math.sin(a), z + h * (0.55 - 0.3 * rr / r)))
        T.clump(c, r * 0.42, 0.14, cov=1.4, up_bias=0.35, flat=0.35, shell=0.5, core=0.5)
    T.build(name, local_mats()['bark'], MM['juniper'], coll='Landscape', core_mat=local_mats()['core_shrub'], core_seg=8)
    return T


def front_beds(M):
    """Front planting (photos 01, 02, 03, 30, 31); positions back-projected through the solved cameras."""
    from . import site_front as sf
    zb = lambda x, y: sf.grade(x, y) + 0.05
    # maiden grass by the neighbour's garage (01 x 1330-1536 / y 570-720, 02, 31 at x 14.7-16.8)
    for i, (x, y, h) in enumerate([(14.95, 0.75, 1.75), (15.85, 1.35, 1.85), (15.0, 1.9, 1.6)]):
        strap_clump(f"Land_MaidenGrass_{i}", x, y, sf.grade(x, y), h, 0.40, seed=40 + i, key='mgrass_leaf', n=230, arch=0.9, plumes=14)
    # garage-left mulch bed: pink knockout rose + daylilies (01, 02, 30)
    _pl.shrub("Land_KnockoutRose", (-0.75, -0.40, zb(-0.75, -0.4)), r=0.38, h=0.72, kind='rose', seed=5, colour='rose_pink')
    for i, (x, y) in enumerate([(-1.15, -0.45), (0.05, -0.35), (0.30, -0.55)]):
        strap_clump(f"Land_Daylily_{i}", x, y, zb(x, y), 0.55, 0.16, seed=60 + i, key='lily_leaf', n=34, flowers='lily_orange', n_flowers=2)
    # in front of the bay (03): hosta, a daylily clump at the wall, small shrubs, a boxwood by the porch column
    hosta("Land_Hosta_Bay", 8.80, -0.55, zb(8.8, -0.55), r=0.42, seed=71)          # 03: the big-leaf clump at the right column
    hosta("Land_Hosta_Bay2", 9.45, 0.45, zb(9.45, 0.45), r=0.30, seed=70)
    strap_clump("Land_Daylily_Bay", 9.90, 0.60, zb(9.9, 0.6), 0.6, 0.18, seed=72, n=40)
    _pl.shrub("Land_Shrub_Bay", (11.15, 0.55, zb(11.15, 0.55)), r=0.28, h=0.5, kind='boxwood', seed=73)
    _pl.shrub("Land_Boxwood_Porch", (10.35, 0.55, zb(10.35, 0.55)), r=0.22, h=0.36, kind='boxwood', seed=74)
    hosta("Land_Hosta_Porch", 6.30, -0.52, zb(6.3, -0.52), r=0.24, seed=75)
    # porch pots (03): basket with red geraniums, a gold pot with a fern, the black glazed pot of white mums on a stand
    MM = _front_mats()
    _pl.potted("Land_PorchPot_Geranium", (6.62, 1.05, Z_PORCH), kind='rose', height=0.30, pot='basket', seed=80)
    _pl.potted("Land_PorchPot_Fern", (6.95, 1.28, Z_PORCH), kind='fern', height=0.55, pot='ceramic', seed=81)
    st = MB()
    st.cylinder(8.45, 1.15, Z_PORCH, Z_PORCH + 0.12, 0.2, seg=16)
    st.build("Land_PlantStand", [_pl.mats()['ceramic_black']], coll='Landscape')
    _pl.potted("Land_PorchPot_Mums", (8.45, 1.15, Z_PORCH + 0.12), kind='hydrangea', height=0.36, pot='black', seed=82)
    for nm in ("Land_PorchPot_Geranium_Leaves", "Land_PorchPot_Mums_Leaves"):
        ob = __import__('bpy').data.objects.get(nm)
        if ob is not None:
            for i, m in enumerate(ob.data.materials):
                if m.name.startswith("FlowerRose"):
                    ob.data.materials[i] = MM['geranium']
                elif m.name.startswith("FlowerHyd"):
                    ob.data.materials[i] = MM['mum_white']
    # the juniper and shrubs at the right lot line by the sidewalk (30, 31)
    juniper("Land_Juniper", 15.05, -7.35, sf.grade(15.05, -7.35), r=1.15, h=0.8, seed=76)
    _pl.shrub("Land_Shrub_NbrR", (17.35, -1.35, sf.grade(17.35, -1.35)), r=0.55, h=0.9, kind='boxwood', seed=77)
    _pl.shrub("Land_Shrub_NbrR2", (16.7, -0.3, sf.grade(16.7, -0.3)), r=0.45, h=0.8, kind='boxwood', seed=78)
    # solar path lights (03: two in the porch bed, two in the bay bed; 01: one at the bay)
    L = MB()
    for (x, y) in [(5.85, -0.33), (6.75, -0.58), (10.51, -0.25), (10.81, -0.12)]:
        z = zb(x, y)
        L.cylinder(x, y, z - 0.1, z + 0.26, 0.009, seg=6, mi=0)
        L.cylinder(x, y, z + 0.26, z + 0.34, 0.04, seg=8, mi=1)
        L.lathe(x, y, z + 0.335, [(0.0, 0.0), (0.07, 0.0), (0.055, 0.03), (0.0, 0.04)], seg=8, mi=0)
    L.build("Land_SolarLights_Front", [M.get('sn_bronze') or _m.new_mat("SolarBronzeF", (0.16, 0.10, 0.06, 1), rough=0.45, metal=0.7),
                                        M.get('sn_clear') or _m.new_mat("SolarClearF", (0.9, 0.9, 0.88, 1), rough=0.12, transmission=0.9)],
            coll='Landscape')


def rear_beds(M):
    """Rear planting (photos 25-28): the two big corner shrubs, iris clumps + a dusty-pink hydrangea in the patio's
    rock border, vegetable pots along the -X side wall.  Positions: the bundle-adjusted views (site_patio.py)."""
    from . import site_patio as sp
    lm = local_mats()
    # +X corner: tall airy arching shrub, ~4 m (25: crown x 9.7-12.75, top at z ~3.8; hides the kitchen window)
    arching_shrub("ShrubRearL", (11.55, 12.95, sp.z_lawn(11.55, 12.95)), 3.75, 1.55, seed=22, canes=60, leaf='leaf_arch_light',
                  droop=0.28, bias=(-0.75, 0.35), twig=0.42, avoid_y=YB1 + 0.25, spacing=0.09, core=0.0, spray='spray_arch_light',
                  spray_cov=0.75)
    # -X corner: large dense rounded shrub (25: crown x -1.0 .. 2.8, top ~3.7)
    arching_shrub("ShrubRearR", (0.95, 13.0, sp.z_lawn(0.95, 13.0)), 3.45, 1.90, seed=21, canes=80, leaf='leaf_arch_dark',
                  droop=0.40, bias=(-0.15, 0.25), core=0.0, twig=0.46, avoid_y=YB1 + 0.25, spacing=0.08, flat=0.3,
                  spray='spray_arch_dark', spray_every=0.26, spray_cov=0.8)
    for nm in ("ShrubRearL", "ShrubRearR"):
        for suf in ("_Leaves", "Spray_Leaves"):
            prune("Land_" + nm + suf, (-0.5, XB1 + 0.6, 1.0, YB1 + 0.12, -1.0, 7.0))
    # iris clumps in the rock border (26/27/28, 25), sword leaves 0.6-0.9 m
    for i, (x, y, h, r, n) in enumerate([(8.13, 17.45, 0.80, 0.30, 12), (2.30, 17.02, 0.95, 0.40, 18), (10.27, 15.62, 0.75, 0.26, 9),
                                         (10.62, 13.25, 0.70, 0.24, 7), (0.55, 13.55, 0.65, 0.24, 7)]):
        iris_clump(f"Land_Iris_{i}", x, y, sp.z_lawn(x, y) + 0.02, h, r, seed=90 + i, fans=n)
    MM = _pl.mats()
    if 'hyd_pink' not in MM:
        MM['hyd_pink'] = _pl.flower_shader("FlowerHydDustyPink", 'ball', (0.40, 0.20, 0.18, 1), (0.56, 0.34, 0.32, 1), (0.36, 0.25, 0.17, 1))
    for k, (dx, dy, rr, hh) in enumerate(((0.0, 0.0, 0.50, 0.75), (0.30, 0.25, 0.42, 0.68), (-0.25, 0.30, 0.40, 0.62))):
        _pl.shrub(f"Land_Hydrangea_Rear{k}", (1.62 + dx, 16.22 + dy, sp.z_lawn(1.62, 16.22) + 0.02), r=rr, h=hh, kind='hydrangea',
                  seed=31 + k, colour='hyd_pink')
    # vegetable pots along the -X side wall (27 right edge, 25 right corner)
    for i, (y, kind, hh) in enumerate([(9.4, 'fern', 0.55), (10.2, 'boxwood', 0.55), (10.95, 'fern', 0.5), (11.55, 'boxwood', 0.5)]):
        _pl.potted(f"Land_SidePot_{i}", (-0.42, y, Z_GRADE + 0.02), kind=kind, height=hh, pot='terracotta', seed=120 + i, coll='Landscape')


# The front Callery pear's crown, measured (SITE_NEAR follow-up): silhouettes of the tree in 01 / 02 (colour mask below a
# hand-read lower boundary) and 30 / 31 (hand-read outlines) with the final house.py cameras; a 6-half-axis egg + a crown
# FLOOR z(dx) (dx = x - trunk x) fitted by maximising the silhouette IoU (01 0.92, 02 0.90, 30 0.85, 31 0.86).
# The floor lifts the canopy to ~2.9 m above the lawn on the house side (01: the bay brick, the living window and the
# porch's right column are clear) and lets it hang to ~1.2 m at the trunk.
TREE_EGG = dict(c=(10.46, -5.21, 4.81), rx=(4.11, 3.23), ry=(4.00, 3.12), rz=(3.51, 5.82))     # photo fit, (-, +) half axes
TREE_FLOOR = ([-4.5, -2.5, -1.2, 0.0, 1.2, 2.5, 4.5], [2.57, 2.55, 1.61, 0.80, 1.08, 0.91, 1.40])   # world z at dx
# the builder's envelope: the leaf clumps and cards overshoot it, so it is shrunk per half axis until the RENDERED silhouette
# matches the photos (tree-only renders, IoU 01 0.91 / 02 0.88 / 30 0.83 / 31 0.80, weighted 0.86)
TREE_BUILD_EGG = dict(c=(10.46, -5.21, 4.81), rx=(4.01, 3.13), ry=(3.90, 3.02), rz=(3.16, 5.12))
TREE_SHRINK = 0.0
TREE_FLOOR_LIFT = 0.0


def tree_envelope(egg=None, floor=None, shrink=None, lift=None):
    """Callable envelope (> 1 outside) for archviz.trees.upright from the measured egg + floor."""
    from mathutils import Vector
    from . import site_front as sf
    egg = egg or TREE_BUILD_EGG
    kx, kz = floor or TREE_FLOOR
    sh = TREE_SHRINK if shrink is None else shrink
    lf = TREE_FLOOR_LIFT if lift is None else lift
    cx, cy, cz = egg['c']
    rx = [max(0.5, r - sh) for r in egg['rx']]; ry = [max(0.5, r - sh) for r in egg['ry']]; rz = [max(0.5, r - sh) for r in egg['rz']]
    tx = sf.TREE[0]

    def floor_z(dx):
        if dx <= kx[0]:
            return kz[0]
        for i in range(len(kx) - 1):
            if dx <= kx[i + 1]:
                t = (dx - kx[i]) / (kx[i + 1] - kx[i])
                return kz[i] + (kz[i + 1] - kz[i]) * t
        return kz[-1]

    def env(p):
        dx, dy, dz = p.x - cx, p.y - cy, p.z - cz
        e = math.sqrt((dx / rx[dx > 0]) ** 2 + (dy / ry[dy > 0]) ** 2 + (dz / rz[dz > 0]) ** 2)
        fz = floor_z(p.x - tx) + lf
        if p.z < fz:
            e = max(e, 1.0 + (fz - p.z) * 2.0)
        return e
    return env, Vector((cx, cy, cz))


def front_tree(**kw):
    """Build the front tree (Land_FrontTree*) inside the measured envelope; kw override envelope parameters (tuning)."""
    from . import site_front as sf
    lm = local_mats()
    tx, ty = sf.TREE
    env, C = tree_envelope(kw.get('egg'), kw.get('floor'), kw.get('shrink'), kw.get('lift'))
    _tr.upright("Land_FrontTree", (tx, ty, sf.grade(tx, ty)), height=11.0, radius=3.9, crown_base=1.0, seed=3, trunk_r=0.17,
                scaffolds=kw.get('scaffolds', 26), card=0.24, cov=kw.get('cov', 1.05), fill=kw.get('fill', 1.0),
                keep_out=(5.6, 13.2, 0.2, -1.0), lobes=kw.get('lobes', 0.08), core=0.42, envelope=env, centre=C,
                cull=kw.get('cull', 1.12), scaffold_z=(0.9, 8.0),
                mats={'bark': lm['bark'], 'leaf': lm['leaf_pear_fine'], 'core': lm['core_pear']})
    prune("Land_FrontTree_Leaves", (5.7, XB1 + 0.6, -0.05, 20.0, -1.0, 6.4))       # nothing inside the bay / porch / eaves


def build(M):
    lm = local_mats()
    # ---- front yard: the big oval tree in its white-rock ring (photos 01, 02, 30, 31)
    from . import site_front as sf
    front_tree()
    # neighbours' front trees (01 left, 31)
    # the left neighbour's big dense front tree (31: crown x -20.9 .. -10.5, a pear form like ours)
    _tr.upright("Land_NbrLTree", (-15.4, -3.0, sf.grade(0, -3.0)), height=10.0, radius=4.2, crown_base=1.0, seed=11, trunk_r=0.18,
                scaffolds=18, card=0.28, cov=1.0, fill=0.9, detail=0.6, lobes=0.08, core=0.45,
                mats={'bark': lm['bark'], 'leaf': lm['leaf_pear_fine'], 'core': lm['core_pear']})
    tree("NbrRTree", (28.2, -2.6, sf.grade(0, -2.6)), 9.0, 8.0, seed=12, kind='locust', detail=0.6, trunk_f=0.32)   # 31: bright locust
    tree("NbrLLTree", (-30.0, -2.0, sf.grade(0, -2.0)), 9.5, 8.0, seed=13, kind='maple', detail=0.45)
    tree("SideYardTree", (-4.3, 1.9, sf.grade(0, 1.9)), 3.4, 2.6, seed=14, kind='maple', detail=0.7, trunk_f=0.2)  # 01/30/31 small tree
    front_beds(M)
    rear_beds(M)
    # blue spruce inside the right neighbour's fenced yard near its rear corner (31: apex u 1000 v 598, base v 690)
    _tr.conifer("Land_BlueSpruce", (17.2, 25.8, ZG - 0.1), height=5.8, r=1.8, seed=150, detail=0.6, kind='pine', coll='Landscape',
                mats={'bark': lm['bark']})
    # the right neighbour's back-yard trees: a broad tree by the fence (25 left edge, 28 top-left: ~(16.2, 16.0), top ~6.5 m)
    # and the bright yellow-green crowns behind their house (31: x 21-29 at y ~18.5)
    tree("NbrRBackTree", (16.4, 16.2, ZG - 0.05), 7.2, 6.4, seed=16, kind='locust', detail=0.6, trunk_f=0.3)
    tree("NbrRBackTree2", (24.5, 18.8, ZG - 0.1), 8.5, 8.5, seed=17, kind='locust', detail=0.45, trunk_f=0.32)
