"""Vegetation: coast live oaks, redwoods/pines, olives, shrubs, background treeline, distant ridge, ground-cover.

Trees come from walsh/trees.py: a recursive branching skeleton down to twig level plus explicit leaf-cluster /
frond cards (thousands of small alpha-cut quads per tree) - no blob canopies.  Level of detail falls with the
distance from the house.  The background rings are low-LOD trees + smooth hazed masses; every distant material
carries aerial perspective (mixes toward the dusk haze colour with camera distance).
"""
import math, random
import bpy
from .plan import *
from archviz.mesh import *
from archviz.lights import *
from archviz import materials
from archviz import trees as _tr

# hillside behind the rear lawn (the site fork builds the wedge): z of the slope at a given y
def hill_z(y):
    return min(12.0, max(0.0, 12.0 * (y - REAR_Y1) / 36.0))


HAZE = (0.60, 0.62, 0.78, 1)

_LM = {}
def local_mats():
    """Bark / ground-cover materials + hazed copies of the leaf cards for the background rings."""
    if not _LM:
        L = _tr.leaf_materials()
        _LM['shrub'] = materials.foliage("ShrubDark", (0.05, 0.14, 0.04, 1), (0.14, 0.28, 0.08, 1), 0.25, rough=0.9)
        _LM['ridge'] = _tr.add_haze(materials.foliage("RidgeForest", (0.02, 0.045, 0.035, 1), (0.04, 0.085, 0.055, 1), 0.0, rough=1.0),
                                    HAZE, dist=170.0, strength=0.20, max_fac=0.5)
        _LM['treeline_mass'] = _tr.add_haze(materials.foliage("TreelineMass", (0.018, 0.045, 0.028, 1), (0.04, 0.09, 0.05, 1), 0.0, rough=1.0),
                                            HAZE, dist=260.0, strength=0.14, max_fac=0.3)
        _LM['bark_red'] = _aniso(materials.noise_mat("BarkRedwoodFibrous", (0.13, 0.07, 0.05, 1), (0.25, 0.14, 0.09, 1), scale=22, bump=1.3, spec=0.06, bump_dist=0.03), (1.0, 1.0, 0.10))
        _LM['bark'] = _aniso(materials.noise_mat("BarkOakFurrowed", (0.08, 0.065, 0.05, 1), (0.19, 0.16, 0.12, 1), scale=14, bump=1.2, spec=0.06, bump_dist=0.03), (1.0, 1.0, 0.28))
        _LM['bark_olive'] = _aniso(materials.noise_mat("BarkOlivePeeling", (0.30, 0.26, 0.21, 1), (0.52, 0.47, 0.39, 1), scale=16, bump=0.9, spec=0.08, bump_dist=0.02), (1.0, 1.0, 0.35))
        _LM['bark_far'] = _tr.add_haze(materials.noise_mat("BarkFar", (0.05, 0.04, 0.032, 1), (0.11, 0.09, 0.07, 1), scale=8, bump=0.3, spec=0.05), HAZE, dist=220.0, strength=0.12, max_fac=0.45)
        _LM['rock'] = materials.noise_mat("BoulderGrey", (0.30, 0.30, 0.28, 1), (0.52, 0.51, 0.47, 1), scale=6, bump=0.9, detail=9, rough=0.85, spec=0.15, bump_dist=0.04)
        _LM['dead_leaf'] = materials.noise_mat("DeadLeaf", (0.30, 0.17, 0.07, 1), (0.52, 0.34, 0.14, 1), scale=40, bump=0.3, rough=0.85)
        _LM['fern'] = materials.foliage("Fern", (0.05, 0.18, 0.05, 1), (0.14, 0.34, 0.10, 1), 0.45, c3=(0.28, 0.46, 0.16, 1), rough=0.8)
        # background-ring leaf cards: hazed copies of the far card materials (holes stay holes: add_haze goes behind the alpha mix)
        _LM['leaf_ring'] = _tr.add_haze(_tr._attr_random(materials.leaf_card("LeafGeoRing", (0.02, 0.05, 0.025, 1), (0.04, 0.095, 0.04, 1), (0.075, 0.14, 0.055, 1), 0.1, shape='cluster', rough=0.9)),
                                        HAZE, dist=220.0, strength=0.14, max_fac=0.45)
        _LM['leaf_ring_warm'] = _tr.add_haze(_tr._attr_random(materials.leaf_card("LeafGeoRingWarm", (0.03, 0.055, 0.02, 1), (0.06, 0.10, 0.035, 1), (0.10, 0.15, 0.05, 1), 0.1, shape='cluster', rough=0.9)),
                                             HAZE, dist=220.0, strength=0.14, max_fac=0.45)
        _LM['frond_ring'] = _tr.add_haze(_tr._frond_card("FrondRing", (0.02, 0.05, 0.03, 1), (0.035, 0.085, 0.04, 1), (0.06, 0.12, 0.05, 1), 0.1),
                                         HAZE, dist=220.0, strength=0.14, max_fac=0.45)
        _LM['core_ring'] = _tr.add_haze(materials.noise_mat("CanopyCoreRing", (0.012, 0.03, 0.014, 1), (0.03, 0.06, 0.03, 1), scale=3, rough=1.0, spec=0.02, bump=0.0),
                                        HAZE, dist=220.0, strength=0.14, max_fac=0.45)
    return _LM


def _aniso(m, scale):
    """Stretch a noise material's coordinates (vertical fibres / furrows for bark)."""
    for n in m.node_tree.nodes:
        if n.type == 'MAPPING':
            n.inputs["Scale"].default_value = scale
    return m


def leafify(ob, scale=0.16, strength=0.5, sub=1):
    """Subdivide + noise-displace so masses read as soft canopies (background masses / boulders only)."""
    if sub > 0:
        s = ob.modifiers.new("sub", 'SUBSURF'); s.subdivision_type = 'CATMULL_CLARK'; s.levels = sub; s.render_levels = sub
    name = f"leaf_noise_{scale:.2f}"
    tex = bpy.data.textures.get(name)
    if tex is None:
        tex = bpy.data.textures.new(name, 'CLOUDS')
        tex.noise_scale = scale; tex.noise_depth = 3
    d = ob.modifiers.new("dsp", 'DISPLACE'); d.texture = tex; d.strength = strength; d.mid_level = 0.5
    d.texture_coords = 'GLOBAL'
    return ob


def _detail(x, y):
    """Level of detail from the distance to the house."""
    d = math.hypot(x, y)
    return 1.0 if d < 45 else (0.55 if d < 70 else (0.3 if d < 110 else 0.15))


# ================================================================== species wrappers (names kept for the plan)
def oak(M, name, pos, height=12.0, spread=10.0, trunk_r=0.45, seed=0, lean=(0, 0), trunk_f=0.38, limbs=None,
        detail=None, keep_out=None, min_z=None, coll='Landscape', ring=False):
    lm = local_mats()
    d = _detail(pos[0], pos[1]) if detail is None else detail
    mats = {'bark': lm['bark_far'] if ring else lm['bark']}
    if ring:
        mats['leaf'] = lm['leaf_ring']; mats['core'] = lm['core_ring']
    return _tr.oak(name, pos, height, spread, trunk_r, seed, lean, trunk_f, limbs, d, keep_out, coll, mats, min_z)


def conifer(M, name, pos, height=28.0, r=3.4, seed=0, kind='redwood', detail=None, coll='Landscape', ring=False):
    lm = local_mats()
    d = _detail(pos[0], pos[1]) if detail is None else detail
    mats = {'bark': lm['bark_far'] if ring else (lm['bark_red'] if kind == 'redwood' else lm['bark'])}
    if ring:
        mats['leaf'] = lm['frond_ring']
    return _tr.conifer(name, pos, height, r, seed, d, kind, coll, mats)


def olive(M, name, pos, height=4.5, seed=0, coll='Landscape', stake=False, detail=None):
    lm = local_mats()
    d = _detail(pos[0], pos[1]) if detail is None else detail
    return _tr.olive(name, pos, height, seed, d, coll, {'bark': lm['bark_olive']}, stake=stake, extra_mats=(M['mulch'], M['teak']) if stake else ())


# ================================================================== small stuff
def grass_tuft(mb, c, r, seed=0, mi=0, blades=None):
    """Clump of 15-25 thin tapered blades (each a curved 3-section sweep) arching outward."""
    rng = random.Random(seed)
    n = blades or rng.randint(15, 25)
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
    """Radial crown of 7-11 arching fronds (thin pillows tilted upward)."""
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


def boulder(mb, c, r, seed=0, mi=0):
    rng = random.Random(seed)
    mb.blob((c[0], c[1], c[2] + r * 0.35), r, seg=14, rings=9, jitter=0.4, seed=seed, mi=mi, squash=rng.uniform(0.55, 0.8),
            rx=rng.uniform(0.9, 1.5), ry=rng.uniform(0.8, 1.2))


def fallen_leaves(mb, rng, n, x0, x1, y0, y1, z, mi=0):
    for i in range(n):
        mb.pillow(rng.uniform(x0, x1), rng.uniform(y0, y1), z + 0.004, w=rng.uniform(0.05, 0.08), d=rng.uniform(0.03, 0.05), t=0.006,
                  mi=mi, rot=rng.uniform(0, math.pi), tilt=rng.uniform(-0.15, 0.15))


# ================================================================== scene
def build(M):
    rng = random.Random(42)
    lm = local_mats()
    L = _tr.leaf_materials()

    # ---- signature coast live oak over the motor court (photos 02/05/23): trunk SW of the court, leaning
    #      hard toward the house, three huge limbs reaching over the court to x≈-6..-4, y≈-6..-2 at z 6.5–9
    A = math.atan2(6.5, 14.5)       # direction from the trunk top toward the entry
    limbs = [(A - 0.30, 14.5, 0.20), (A + 0.02, 15.5, 0.24), (A + 0.36, 13.0, 0.17),   # over the court
             (A + 1.25, 8.5, 0.45), (A - 1.15, 7.5, 0.40), (A + 2.3, 7.0, 0.55), (A - 2.4, 6.0, 0.6), (A + 3.1, 5.5, 0.7)]
    oak(M, "Oak_Signature", (-20.0, -12.0, 0.0), height=16.0, spread=14.0, trunk_r=0.72, seed=1, lean=(3.2, 2.4), trunk_f=0.34,
        limbs=limbs, detail=1.0, min_z=5.6, keep_out=(-14.0, 14.5, -2.3, 4.5))
    # ---- oak at the right of the front lawn + one behind the courtyard's east side
    # (39.5, -7): the aerial camera at (30, -14, 12) sat inside this crown when the trunk was at x=34
    oak(M, "Oak_LawnRight", (39.5, -7.0, 0.9), height=13.5, spread=12.0, trunk_r=0.55, seed=2, lean=(-1.6, 1.2), trunk_f=0.36, detail=1.0)
    oak(M, "Oak_EastCourt", (36.0, 27.5, 1.0), height=14.0, spread=12.5, trunk_r=0.55, seed=3, lean=(-1.2, -0.8), trunk_f=0.38, detail=1.0)
    # ---- more oaks around the property (photo 01/34 dark canopies left of the house, photo 17 hillside)
    oak(M, "Oak_West", (-24.0, 8.0, 0.0), height=13.0, spread=11.0, trunk_r=0.5, seed=10, lean=(1.5, 0.5), detail=1.0)
    oak(M, "Oak_WestRear", (-20.0, 24.0, 1.0), height=12.0, spread=10.0, trunk_r=0.45, seed=11, detail=0.8)
    oak(M, "Oak_NE", (30.0, 38.0, hill_z(38.0)), height=13.0, spread=11.0, trunk_r=0.5, seed=12, detail=0.6)
    oak(M, "Oak_StreetW", (-36.0, -22.0, 0.0), height=12.0, spread=10.0, trunk_r=0.45, seed=13, detail=0.55)
    oak(M, "Oak_StreetE", (42.0, -22.0, 0.5), height=12.0, spread=10.0, trunk_r=0.45, seed=14, detail=0.55)
    # hillside oaks behind the rear lawn (z follows the slope built by the site fork)
    for i, (x, y) in enumerate(((-10.0, 40.0), (4.0, 42.0), (-24.0, 44.0), (16.0, 46.0), (-4.0, 50.0), (8.0, 54.0),
                                (-18.0, 56.0), (22.0, 58.0), (0.0, 62.0), (-12.0, 66.0))):
        oak(M, f"Oak_Hill_{i}", (x, y, hill_z(y)), height=rng.uniform(10, 14), spread=rng.uniform(9, 12), trunk_r=0.45,
            seed=20 + i, detail=0.55 if y < 52 else 0.35)

    # ---- redwoods / pines: the tall dark skyline behind and west of the house (photos 01/34)
    for i, (x, y, h) in enumerate(((10, 40, 32), (24, 42, 27), (-6, 44, 34), (34, 36, 26), (18, 50, 36), (-16, 48, 30),
                                   (30, 52, 30), (2, 54, 33), (40, 46, 28), (-26, 52, 31), (12, 58, 35), (-2, 66, 30),
                                   (-30, -4, 26), (-28, 6, 29), (-26, 14, 24), (-31, 24, 27))):
        zb = hill_z(y) if y > REAR_Y1 else 0.3
        conifer(M, f"Redwood_{i}", (x, y, zb), height=h, r=h * 0.135, seed=30 + i, kind='redwood' if i % 3 else 'pine',
                detail=1.0 if math.hypot(x, y) < 48 else 0.55)

    # ---- olives: entry (photo 02), front lawn, courtyard canopy cut-out
    olive(M, "Olive_EntryL", (-5.6, -3.4, 0.0), height=3.9, seed=4, stake=True)
    olive(M, "Olive_EntryR", (6.3, -3.4, 0.0), height=3.0, seed=5, stake=True)
    olive(M, "Olive_Lawn", (23.5, -10.5, Z_LAWN), height=3.8, seed=6)
    olive(M, "Olive_Lawn2", (11.0, -11.5, Z_LAWN), height=3.2, seed=7)
    cx, cy = (CAN_HOLE[0] + CAN_HOLE[1]) / 2, (CAN_HOLE[2] + CAN_HOLE[3]) / 2
    olive(M, "Olive_Court", (cx, cy, Z_LIV), height=4.6, seed=8)
    olive(M, "Olive_Drive", (-16.5, -9.0, 0.0), height=3.4, seed=9)

    # ---- ground-cover: blade-grass clumps along the drive edges + beds, shrubs under the trees
    gc = MB()
    k = 0
    for i in range(30):                                   # west planting bed (top of the low bed is z -0.05)
        x = rng.uniform(-21.6, -18.4); y = -13.5 + i * 0.52 + rng.uniform(-0.12, 0.12)
        grass_tuft(gc, (x, y, -0.05), rng.uniform(0.2, 0.32), seed=100 + k, mi=0); k += 1
    for i in range(24):                                   # south bed along the court edge (top z 0.05)
        x = -17.5 + i * 1.02 + rng.uniform(-0.25, 0.25); y = rng.uniform(-17.1, -15.4)
        grass_tuft(gc, (x, y, 0.05), rng.uniform(0.2, 0.32), seed=100 + k, mi=0); k += 1
    for i in range(14):                                   # driveway edges toward the street
        for x in (-35.0 + rng.uniform(-0.4, 0.4), -13.0 + rng.uniform(-0.4, 0.4)):
            y = -29.0 + i * 1.6
            grass_tuft(gc, (x, y, -0.05), rng.uniform(0.2, 0.34), seed=100 + k, mi=0, blades=14); k += 1
    for (x, y, z) in ((-23.5, -14.5, 0.0), (-25.5, -9.5, 0.0), (33.0, -12.5, 0.9), (38.5, -6.0, 0.9), (-21.5, 26.0, 1.0), (30.0, 33.0, 1.0)):
        for j in range(4):                                # under the trees
            grass_tuft(gc, (x + rng.uniform(-1.2, 1.2), y + rng.uniform(-1.2, 1.2), z), rng.uniform(0.18, 0.3), seed=100 + k, mi=0, blades=12); k += 1
    gc.build("GroundCover_Grasses", M['grass_tuft'], coll='Landscape', smooth=True)
    # shrubs: dark core + a shell of leaf-cluster cards (no cotton balls)
    sh = _tr.Tree(77, 1.0)
    for i, (x, y, z, r) in enumerate(((-22, -12, 0, 1.0), (-24, -8, 0, 1.2), (-19, -16, 0, 0.9), (-26, 4, 0, 1.3), (-23, 12, 0, 1.1),
                                      (36, -12, 0.9, 1.2), (37, -5, 0.9, 1.0), (31, -14, 0.9, 0.9), (-33, -26, 0, 1.2), (40, -26, 0.4, 1.1),
                                      (-14, 26, 1.0, 1.0), (28, 30, 1.0, 1.2), (36, 30, 1.0, 1.0))):
        _tr.shrub_cards(sh, (x, y, z), r, size=0.24, seed=200 + i)
    sh.build("GroundCover_Shrubs", lm['shrub'], L['shrub'], coll='Landscape', core_mat=L['core'], core_seg=9)
    sh2 = _tr.Tree(78, 0.5)
    for i in range(24):                                   # scrub on the hillside
        y = rng.uniform(36, 68); x = rng.uniform(-28, 28)
        _tr.shrub_cards(sh2, (x, y, hill_z(y)), rng.uniform(0.9, 1.6), size=0.3, seed=300 + i, cov=0.8)
    sh2.build("GroundCover_HillScrub", lm['shrub'], L['shrub'], coll='Landscape', core_mat=L['core'], core_seg=8)
    # ferns in the shade at the foot of the rear hill, boulders at the drive / lawn edges + hillside
    fr = MB()
    for i, (x, y) in enumerate(((-9.0, 35.2), (-3.5, 35.6), (2.5, 35.3), (6.5, 35.8), (-14.0, 36.5), (10.5, 36.2), (-6.0, 37.4), (4.0, 38.0))):
        fern(fr, (x, y, hill_z(y) + 0.02), rng.uniform(0.55, 0.85), seed=400 + i, mi=0)
    leafify(fr.build("GroundCover_Ferns", lm['fern'], coll='Landscape', smooth=True), 0.12, 0.03, sub=1)
    bd = MB()
    for i, (x, y, z, r) in enumerate(((-15.2, -18.6, 0.0, 0.55), (-24.0, -4.0, 0.0, 0.85), (27.5, -13.5, 0.9, 0.6), (-8.0, 42.0, hill_z(42.0), 1.0), (12.0, 44.5, hill_z(44.5), 0.75))):
        boulder(bd, (x, y, z), r, seed=500 + i, mi=0)
    leafify(bd.build("GroundCover_Boulders", lm['rock'], coll='Landscape', smooth=True), 0.45, 0.12, sub=1)
    # fallen oak leaves on the motor-court beds under the signature oak
    fl = MB()
    fallen_leaves(fl, rng, 90, -21.6, -18.3, -13.5, 2.0, -0.05, mi=0)
    fallen_leaves(fl, rng, 60, -17.5, 6.0, -17.2, -15.3, 0.05, mi=0)
    fl.build("GroundCover_Leaves", lm['dead_leaf'], coll='Landscape', smooth=True)

    # ---- background ring 0 (62-80 m): real low-LOD trees with trunks so the skyline reads as trees
    i = 0
    for j in range(96):
        a = 2 * math.pi * j / 96 + rng.uniform(-0.02, 0.02)
        if abs(a - math.pi * 1.5) < 0.75:                 # street side: only the far ring closes the view
            continue
        d = rng.uniform(62, 80)
        x, y = d * math.cos(a), d * math.sin(a)
        zb = hill_z(y) if y > REAR_Y1 else 0.0
        if i % 5 == 2:
            conifer(M, f"Treeline_Conifer_{i}", (x, y, zb), height=rng.uniform(22, 34), r=rng.uniform(2.8, 3.8), seed=600 + i,
                    kind='redwood', detail=0.18, ring=True)
        else:
            oak(M, f"Treeline_Oak_{i}", (x, y, zb), height=rng.uniform(11, 17), spread=rng.uniform(10, 15), trunk_r=rng.uniform(0.4, 0.6),
                seed=600 + i, detail=0.16, ring=True)
        i += 1
    # ---- ring 1 (85-130 m): smooth hazed canopy masses with a few emergent conifers, fronted by very low-LOD
    #      trees so the silhouette is made of crowns and trunks rather than mounds
    bg = MB()
    for j in range(150):
        a = 2 * math.pi * j / 150 + rng.uniform(-0.02, 0.02)
        d = rng.uniform(85, 130)
        x, y = d * math.cos(a), d * math.sin(a)
        zb = hill_z(y) if y > REAR_Y1 else 0.0
        h = rng.uniform(12, 22)
        if j % 2 == 0:
            xt, yt = (d - 6) * math.cos(a), (d - 6) * math.sin(a)
            if j % 6 == 0:
                conifer(M, f"Treeline_FarConifer_{j}", (xt, yt, zb), height=rng.uniform(24, 36), r=rng.uniform(3.0, 4.0), seed=900 + j,
                        kind='redwood', detail=0.12, ring=True)
            else:
                oak(M, f"Treeline_FarOak_{j}", (xt, yt, zb), height=rng.uniform(12, 18), spread=rng.uniform(11, 16), trunk_r=0.5,
                    seed=900 + j, detail=0.12, ring=True)
        bg.blob((x, y, zb + h * 0.5), h * 0.45, seg=24, rings=14, jitter=0.3, seed=400 + j, mi=0, squash=0.9)
        bg.blob((x + rng.uniform(-8, 8), y + rng.uniform(-8, 8), zb + h * 0.38), h * 0.4, seg=20, rings=12, jitter=0.3, seed=600 + j, mi=0, squash=0.85)
        if j % 4 == 0:
            bg.cone_blob((x + rng.uniform(-4, 4), y + rng.uniform(-4, 4), zb + h * 0.3), h * 0.28, h * 0.75, seg=14, rings=10, jitter=0.25, seed=800 + j, mi=0)
    leafify(bg.build("Treeline", lm['treeline_mass'], coll='Landscape', smooth=True), 4.0, 1.6, sub=1)
    # ---- far forested ridge (165-240 m): low smooth hazed masses (Atherton is flat; only the wooded hill behind
    #      the house rises), their front edge broken by a row of very low-LOD tree silhouettes
    rg = MB()
    for j in range(140):
        a = 2 * math.pi * j / 140
        d = rng.uniform(165, 240)
        x, y = d * math.cos(a), d * math.sin(a)
        h = rng.uniform(18, 26) + (16.0 if y > 40 else 0.0)
        rg.blob((x, y, h * 0.2), h * 0.9, seg=28, rings=16, jitter=0.18, seed=1000 + j, squash=0.5)
        rg.blob((x + rng.uniform(-14, 14), y + rng.uniform(-14, 14), h * 0.15), h * 0.8, seg=24, rings=14, jitter=0.18, seed=1200 + j, squash=0.5)
        if j % 3 == 0:
            xt, yt = (d - 10) * math.cos(a), (d - 10) * math.sin(a)
            if j % 9 == 0:
                conifer(M, f"Ridge_Conifer_{j}", (xt, yt, 0.0), height=rng.uniform(26, 38), r=rng.uniform(3.2, 4.2), seed=1300 + j,
                        kind='redwood', detail=0.1, ring=True)
            else:
                oak(M, f"Ridge_Oak_{j}", (xt, yt, 0.0), height=rng.uniform(13, 19), spread=rng.uniform(12, 17), trunk_r=0.5,
                    seed=1300 + j, detail=0.1, ring=True)
    leafify(rg.build("Ridge", lm['ridge'], coll='Landscape', smooth=True), 14.0, 2.0, sub=1)
