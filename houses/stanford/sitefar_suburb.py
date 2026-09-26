"""The subdivision around the pond out to the horizon (photos 30-32; imported by context.py only).

Layout (plan metres, the house's frame):
  * the streets around the pond block, traced from photo 32 orthophotos (tools/orthophoto.py with the solved p32):
    our street continuing west and curving north at the east end into the street behind the east row, the street
    behind the far row (y ~197) and the street behind the west row (x ~ -140);
  * beyond them a network of gently curving east-west residential streets every ~88 m with north-south collectors
    every ~330 m (inferred: the photo resolves rows of houses facing streets, not the plat);
  * a woodland block north-east of the pond and open fairways with a small pond to the north-west (photo 32);
  * houses on both sides of every residential street (lots ~21 m), 1-2 trees per lot, street trees;
  * gently undulating ground beyond ~250 m (a few metres over ~0.5-1 km), a hazed plain to 25 km.
Houses and trees beyond the pond block are geometry-node instances of a few prototypes (archviz.scatter); the
nearer rows are merged low-poly meshes (sitefar_houses).  Aerial perspective: every backdrop material is hazed by
camera distance (archviz.trees.add_haze)."""
import math
import random
from archviz.mesh import MB
from archviz import scatter
from archviz import trees as _tr
from archviz import materials as _m
from . import sitefar_houses as sh

HAZE = dict(color=(0.50, 0.49, 0.43, 1), dist=2600.0, strength=0.5, max_fac=0.5)     # warm, light (32: 1-2 km rows keep colour)
SETBACK = 21.0               # street centreline -> main block front wall (our lot: garage face 15.2 m + 6.4 m bump)
R_SUBURB = 2600.0            # instanced houses / trees out to this radius around the pond
CENTRE = (0.0, 90.0)


# ---------------------------------------------------------------- terrain
def undulation(x, y):
    """Gentle rolling ground beyond the pond block: 0 inside r 250 m, up to ~ +/- 2.5 m beyond 700 m (inferred;
    photo 32's far rows rise and dip slightly)."""
    r = math.hypot(x - CENTRE[0], y - CENTRE[1])
    a = min(1.0, max(0.0, (r - 250.0) / 450.0))
    if a <= 0:
        return 0.0
    u = (math.sin(x / 173.0 + 1.3) * math.cos(y / 211.0 - 0.7) + 0.6 * math.sin((x + y) / 97.0 + 2.1)
         + 0.35 * math.cos((x - 2 * y) / 61.0) + 0.8 * math.sin(x / 520.0 - 0.4) * math.sin(y / 610.0 + 0.9))
    return 1.1 * a * a * (3 - 2 * a) * u


# ---------------------------------------------------------------- polylines
def _resample(pts, step):
    out = [pts[0]]
    for a, b in zip(pts[:-1], pts[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(L / step))
        for k in range(1, n + 1):
            t = k / n
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return out


def _smooth(pts, n=4):
    """Open Catmull-Rom through pts."""
    if len(pts) < 3:
        return list(pts)
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t * t
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t ** 3) for j in (0, 1)))
    out.append(pts[-1])
    return out


def _normal(pts, i):
    a = pts[max(0, i - 1)]
    b = pts[min(len(pts) - 1, i + 1)]
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1.0
    return (-dy / L, dx / L), (dx / L, dy / L)


def strip(mb, pts, w, zf, off=0.0, lift=0.04, mi=0):
    """A ribbon of width w along pts (offset `off` to the left), draped on zf(x, y)."""
    L, R = [], []
    for i, p in enumerate(pts):
        (nx, ny), _ = _normal(pts, i)
        a = (p[0] + nx * (off + w / 2), p[1] + ny * (off + w / 2))
        b = (p[0] + nx * (off - w / 2), p[1] + ny * (off - w / 2))
        L.append((a[0], a[1], zf(*a) + lift))
        R.append((b[0], b[1], zf(*b) + lift))
    base = len(mb.v)
    mb.v.extend(L + R)
    n = len(pts)
    for i in range(n - 1):
        mb.f.append((base + n + i, base + n + i + 1, base + i + 1, base + i)); mb.fm.append(mi)


def point_in_poly(x, y, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        (ax, ay), (bx, by) = poly[i], poly[(i + 1) % n]
        if (ay > y) != (by > y) and x < (bx - ax) * (y - ay) / (by - ay + 1e-12) + ax:
            inside = not inside
    return inside


# ---------------------------------------------------------------- land use (photo 32; outlines back-projected, see notes)
WOODLAND = [(113.5, 280.7), (202.7, 274.9), (314.2, 282.8), (430.0, 320.0), (620.0, 470.0), (800.0, 780.0), (877.3, 1080.1), (734.6, 1296.1), (428.2, 1303.7),
            (234.5, 1125.4), (163.2, 977.8), (134.5, 781.6), (120.1, 585.7), (113.7, 409.7)]      # 32: east of the NNW street's right-hand row
FAIRWAYS = [
    [(-440, 300), (-300, 286), (-190, 292), (-165, 340), (-215, 410), (-330, 432), (-450, 420)],
    [(-330, 450), (-190, 438), (-105, 442), (-92, 520), (-150, 600), (-260, 612), (-350, 560)],
    [(-700, 640), (-520, 620), (-470, 700), (-560, 800), (-720, 760)],
]
PONDS_FAR = [(-121.0, 501.0, 22.0, 14.0), (-560.0, 700.0, 30.0, 18.0)]     # (x, y, rx, ry) small ponds in the fairways
BLOCK = [(-160, -40), (130, -40), (130, 232), (-160, 232)]                  # the pond block: built explicitly by context.py


def near_streets(yc):
    """The streets round the pond block (photo 32 orthophotos): yc = our street's centreline."""
    # our street curving north into the east street, which bends NNW at the block's NE corner into the long street to the
    # north (32: centreline back-projected (101.7, 115), (93, 187), (81.5, 213), (75, 247), (72, 288), (69, 340), (69, 407),
    # (71, 497), (74.5, 587), (83.5, 757), (93, 952), (110, 1257))
    east = [(60.0, yc), (64.6, yc + 0.3), (70.7, yc + 1.6), (78.8, yc + 5.2), (86.9, yc + 11.4), (93.9, yc + 19.2), (100.0, yc + 28.4),
            (103.6, yc + 38.2), (104.9, yc + 49.9), (105.2, 63.0), (103.7, 111.8), (101.2, 146.0), (96.2, 175.2), (86.1, 201.6),
            (76.4, 240.6), (72.7, 281.1), (70.4, 331.7), (70.0, 397.0), (72.5, 484.6), (76.0, 572.6), (85.3, 739.8), (95.4, 930.3),
            (112.6, 1229.6), (138.7, 1567.0), (164.7, 1961.3), (185.8, 2455.3)]
    north = [(-134.5, 194.8), (0.2, 195.3), (40.6, 194.8), (70.9, 196.7), (89.1, 194.8)]
    branch = [(102.7, 136.2), (117.4, 158.6), (135.7, 171.3), (162.0, 182.1), (202.5, 190.8), (260.0, 200.0)]
    # the street west of the pond (32 orthophoto: the rear walls of its east-side houses stand at x ~ -103, 40 m from the water)
    west = [(-134.5, -120.0), (-134.5, yc), (-134.5, 100.0), (-135.5, 197.0), (-138.0, 300.0)]
    ours_w = [(-60.0, yc), (-134.5, yc)]
    return {'east': _smooth(east, 3), 'north': _smooth(north, 3), 'branch': _smooth(branch, 3), 'west': west, 'ours_w': ours_w}


COLLECTORS = []                  # (x0, phase) of the N-S collectors: x = x0 + 14 sin(y / 160 + phase)


def far_streets():
    """Inferred residential grid beyond the block: E-W streets every ~88 m (gently curving), N-S collectors."""
    rng = random.Random(77)
    ew = []
    for k in range(-26, 27):
        y0 = 197.0 + 88.0 * k if k > 0 else (-15.2 - 88.0 * (-k) if k < 0 else None)
        if y0 is None:
            continue
        ph, ph2 = rng.uniform(0, 6.28), rng.uniform(0, 6.28)
        pts = []
        x = -R_SUBURB
        while x <= R_SUBURB:
            pts.append((x, y0 + 9.0 * math.sin(x / 190.0 + ph) + 4.0 * math.sin(x / 67.0 + ph2)))
            x += 12.0
        ew.append(pts)
    ns = []
    COLLECTORS.clear()
    for j in range(-8, 9):
        x0 = -140.0 + 330.0 * j
        ph = rng.uniform(0, 6.28)
        COLLECTORS.append((x0, ph))
        pts = []
        y = CENTRE[1] - R_SUBURB
        while y <= CENTRE[1] + R_SUBURB:
            pts.append((x0 + 14.0 * math.sin(y / 160.0 + ph), y))
            y += 12.0
        ns.append(pts)
    return ew, ns


def _clip(pts, keep):
    """Split a polyline into the runs where keep(x, y) is True."""
    runs, cur = [], []
    for p in pts:
        if keep(*p):
            cur.append(p)
        elif cur:
            if len(cur) > 1:
                runs.append(cur)
            cur = []
    if len(cur) > 1:
        runs.append(cur)
    return runs


# ---------------------------------------------------------------- prototypes
HOUSE_TYPES = [
    # (W, D, siding, roof, style) - 32's mix: mostly beige / tan / cream with weathered-wood roofs, some white and grey,
    # a few blue-grey, yellow and brick fronts (INFERRED distribution)
    (13.0, 10.5, 'beige', 'weathered', dict(garage='L', roof='side')),
    (12.5, 10.0, 'cream', 'weathered', dict(garage='R', roof='side', brick=True)),
    (14.0, 11.0, 'greyblue', 'charcoal', dict(garage='L', roof='hip', front_gable=False)),
    (12.0, 10.5, 'tan', 'brown', dict(garage='R', roof='side')),
    (13.5, 10.5, 'white', 'weathered', dict(garage='L', roof='front', front_gable=False)),
    (12.5, 11.0, 'beige', 'brown', dict(garage='R', roof='side', shutters=False)),
    (13.0, 10.0, 'sage', 'weathered', dict(garage='L', roof='side', brick=True)),
    (14.5, 11.5, 'cream', 'grey', dict(garage='R', roof='hip', front_gable=True)),
    (12.0, 10.0, 'yellow', 'weathered', dict(garage='L', roof='side')),
    (13.0, 10.5, 'lightgrey', 'weathered', dict(garage='R', roof='front', front_gable=False)),
    (13.5, 11.0, 'tan', 'weathered', dict(garage='L', roof='hip', brick=True)),
    (12.5, 10.5, 'mocha', 'weathered', dict(garage='R', roof='side')),
    (13.0, 10.5, 'white', 'charcoal', dict(garage='L', roof='side', shutters=False)),
    (12.0, 11.0, 'beige', 'weathered', dict(garage='R', roof='side', brick=True)),
    (14.0, 10.5, 'cream', 'brown', dict(garage='L', roof='front', front_gable=False)),
    (13.0, 10.0, 'grey', 'weathered', dict(garage='R', roof='hip')),
]


def house_protos(M):
    """Joined prototype houses at the origin, front wall centre at (0, 0) facing -Y, ground at z 0."""
    P = scatter.prototypes("SF_Proto_Houses")
    for i, (W, D, sid, roof, st) in enumerate(HOUSE_TYPES):
        kit = sh.Kit(M, haze=HAZE)
        style = dict(st)
        style.setdefault('deck', ['wood', 'patio', None, 'red'][i % 4])
        sh.house(kit, 0.0, 0.0, 0.0, 0.3, W=W, D=D, siding=sid, roof=roof, seed=100 + i, style=style)
        ob = kit.build_joined(f"P{i:02d}_SFHouse", coll='SF_Tmp')
        scatter.adopt(ob, P)
    return P


def tree_protos(M):
    """Low-detail broadleaf crowns (leaf cards) + conifers for the nearer instances, blob crowns for the far ones."""
    near = scatter.prototypes("SF_Proto_Trees")
    far = scatter.prototypes("SF_Proto_TreesFar")
    leafs = [
        _tr._attr_random(_m.leaf_card("SF_LeafFar_A", (0.08, 0.11, 0.02, 1), (0.16, 0.21, 0.04, 1), (0.28, 0.33, 0.07, 1), 0.4,
                                      shape='cluster', rough=0.75)),
        _tr._attr_random(_m.leaf_card("SF_LeafFar_B", (0.11, 0.13, 0.025, 1), (0.21, 0.24, 0.05, 1), (0.34, 0.36, 0.09, 1), 0.4,
                                      shape='cluster', rough=0.75)),
        _tr._attr_random(_m.leaf_card("SF_LeafFar_C", (0.05, 0.075, 0.015, 1), (0.11, 0.15, 0.03, 1), (0.20, 0.24, 0.05, 1), 0.4,
                                      shape='cluster', rough=0.8)),
    ]
    for m in leafs:
        _tr.add_haze(m, HAZE['color'], dist=HAZE['dist'], strength=HAZE['strength'], max_fac=HAZE['max_fac'])
    bark = _tr.add_haze(_m.noise_mat("SF_BarkFar", (0.10, 0.085, 0.07, 1), (0.22, 0.19, 0.15, 1), scale=10, bump=0.2),
                        HAZE['color'], dist=HAZE['dist'], strength=HAZE['strength'], max_fac=HAZE['max_fac'])
    core = _tr.add_haze(_m.noise_mat("SF_CoreFar", (0.06, 0.08, 0.016, 1), (0.13, 0.16, 0.035, 1), scale=3, rough=1.0, bump=0.0),
                        HAZE['color'], dist=HAZE['dist'], strength=HAZE['strength'], max_fac=HAZE['max_fac'])
    from . import sitefar_trees as st
    shapes = [(11.0, 9.5, 'round'), (8.0, 7.0, 'round'), (14.0, 12.0, 'dome'), (7.5, 3.6, 'column'), (10.0, 8.5, 'oval'),
              (12.5, 9.0, 'multistem')]
    for i, (h, w, form) in enumerate(shapes):
        st.broadleaf(f"P{i:02d}_SFTree", (0.0, 0.0, 0.0), h, w, 500 + i, {'bark': bark, 'leaf': leafs[i % 3], 'core': core}, detail=0.22, form=form,
                     stems=3 if form == 'multistem' else 1, fork=0.22, cov=1.0, coll='SF_Tmp')
    for i in range(2):
        _tr.conifer(f"P{6 + i:02d}_SFTree", (0.0, 0.0, 0.0), height=9.0 + 4 * i, r=2.4 + 0.6 * i, seed=560 + i, detail=0.2, kind='pine',
                    coll='SF_Tmp', mats={'bark': bark})
    import bpy
    tmp = bpy.data.collections.get('SF_Tmp')
    names = sorted(o.name for o in tmp.objects)
    # join each tree's wood / leaves / core into one prototype object
    groups = {}
    for n in names:
        groups.setdefault(n.split('_SFTree')[0], []).append(bpy.data.objects[n])
    for k, obs in sorted(groups.items()):
        ob = _join(obs, f"{k}_SFTree")
        scatter.adopt(ob, near)
    # far blobs
    fol = [_tr.add_haze(_m.noise_mat(f"SF_BlobFol{i}", c1, c2, scale=1.2, bump=0.6, detail=4, rough=0.9), HAZE['color'],
                        dist=HAZE['dist'], strength=HAZE['strength'], max_fac=HAZE['max_fac'])
           for i, (c1, c2) in enumerate([((0.035, 0.05, 0.012, 1), (0.11, 0.14, 0.03, 1)), ((0.05, 0.065, 0.018, 1), (0.14, 0.16, 0.04, 1)),
                                         ((0.025, 0.04, 0.012, 1), (0.08, 0.10, 0.025, 1))])]
    for i in range(4):
        mb = MB()
        r = [4.5, 3.4, 5.5, 2.4][i]
        mb.blob((0, 0, r * 1.15), r, seg=9, rings=6, jitter=0.4, seed=40 + i, squash=0.85 if i != 3 else 1.6)
        if i != 3:
            mb.blob((r * 0.45, r * 0.2, r * 1.5), r * 0.6, seg=7, rings=5, jitter=0.4, seed=50 + i)
        ob = mb.build(f"P{i:02d}_SFBlob", [fol[i % 3]], coll='SF_Tmp', smooth=True, auto_smooth=False)
        scatter.adopt(ob, far)
    return near, far


def woodland(M, zf, rng, add_tree):
    """The woodland NE of the pond (32): seen from above as a lumpy closed canopy.  A heightfield canopy (crowns of
    ~9 m, 14-20 m tall, noise-shaded olive green with dark gaps) plus a ring of instanced trees along its edge so the
    border reads as individual crowns."""
    from mathutils import noise, Vector
    fol = _tr.add_haze(_m.noise_mat("SF_WoodCanopy", (0.012, 0.016, 0.004, 1), (0.075, 0.075, 0.018, 1), scale=0.18, bump=1.0, detail=6,
                                    rough=0.9), HAZE['color'], dist=HAZE['dist'], strength=HAZE['strength'], max_fac=HAZE['max_fac'])
    xs = [p[0] for p in WOODLAND]; ys = [p[1] for p in WOODLAND]
    step = 3.0
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    nx, ny = int((x1 - x0) / step) + 1, int((y1 - y0) / step) + 1
    mb = MB()
    idx = {}

    def vert(i, j):
        if (i, j) not in idx:
            x, y = x0 + i * step, y0 + j * step
            # lumpy crowns: cellular + fbm; drops to the ground outside the polygon edge
            n = noise.cell(Vector((x / 7.0, y / 7.0, 0.3)))
            f = noise.fractal(Vector((x / 40.0, y / 40.0, 1.7)), 0.6, 2.0, 4)
            h = 15.5 + 3.5 * f + 4.0 * (0.5 - n)
            idx[(i, j)] = len(mb.v)
            mb.v.append((x, y, zf(x, y) + h))
        return idx[(i, j)]
    for i in range(nx - 1):
        for j in range(ny - 1):
            cx, cy = x0 + (i + 0.5) * step, y0 + (j + 0.5) * step
            if not point_in_poly(cx, cy, WOODLAND):
                continue
            mb.f.append((vert(i, j), vert(i + 1, j), vert(i + 1, j + 1), vert(i, j + 1))); mb.fm.append(0)
    mb.build("SF_Woodland_Canopy", [fol], coll='Backdrop', recalc=False)
    # the edge: individual trees just inside the boundary hide the canopy's cut edge
    ring = _resample(WOODLAND + [WOODLAND[0]], 6.5)
    for (x, y) in ring:
        for k in range(2):
            add_tree(x + rng.uniform(-3.5, 3.5), y + rng.uniform(-3.5, 3.5), big=rng.uniform(1.4, 1.9))


def _join(obs, name):
    import bpy
    if len(obs) == 1:
        obs[0].name = name
        return obs[0]
    ctx = bpy.context
    for o in ctx.view_layer.objects:
        o.select_set(False)
    for o in obs:
        o.select_set(True)
    ctx.view_layer.objects.active = obs[0]
    bpy.ops.object.join()
    ob = ctx.view_layer.objects.active
    ob.name = name
    return ob


# ---------------------------------------------------------------- build
def build(M, zf, excluded, yc, ground_mat):
    """zf(x, y): terrain height; excluded(x, y): True where context.py builds the ground/houses itself;
    yc: our street's centreline (site.py).  Builds streets, the explicit rows round the block's outer streets,
    the instanced suburb and the far terrain."""
    import bpy
    rng = random.Random(2024)
    if 'SF_Tmp' not in bpy.data.collections:
        tmp = bpy.data.collections.new('SF_Tmp')
        bpy.context.scene.collection.children.link(tmp)
    street_m = _m.noise_mat("SF_StreetConcrete", (0.22, 0.215, 0.20, 1), (0.30, 0.29, 0.27, 1), scale=3, bump=0.05, rough=0.85)
    walk_m = _m.noise_mat("SF_WalkConcrete", (0.30, 0.29, 0.27, 1), (0.38, 0.37, 0.34, 1), scale=3, bump=0.05, rough=0.85)
    street_h = _tr.add_haze(street_m.copy(), HAZE['color'], dist=HAZE['dist'], strength=HAZE['strength'], max_fac=HAZE['max_fac'])
    street_h.name = "SF_StreetConcreteHazed"
    # ---- streets
    ns_near = near_streets(yc)
    st_near = MB()
    for key, pts in ns_near.items():
        pts = _resample(pts, 4.0)
        strip(st_near, pts, 8.67, zf, lift=0.03, mi=0)                 # site_front: curb to curb 8.67, sidewalks 1.48 at +/- 6.4
        for side in (1, -1):
            strip(st_near, pts, 1.48, zf, off=side * 6.4, lift=0.06, mi=1)
    st_near.build("SF_Streets_Near", [street_m, walk_m], coll='Backdrop', recalc=False)
    ew, ns = far_streets()
    st_far = MB()

    def road_ok(x, y):
        r = math.hypot(x - CENTRE[0], y - CENTRE[1])
        return r < R_SUBURB and not point_in_poly(x, y, BLOCK) and not point_in_poly(x, y, WOODLAND) and \
            not any(point_in_poly(x, y, f) for f in FAIRWAYS[:2])
    for pts in ew + ns:
        for run in _clip(pts, road_ok):
            strip(st_far, run, 7.4, zf, lift=0.05)
    st_far.build("SF_Streets_Far", [street_h], coll='Backdrop', recalc=False)

    # ---- lots along the near outer streets (explicit merged houses) and the far streets (instances)
    near_kit = sh.Kit(M, haze=HAZE)
    placed = []                                     # (x, y) of every house, for spacing tests
    placed_h = []                                   # (x, y, heading)
    G = 25.0
    hgrid, sgrid = {}, {}

    def _key(x, y):
        return (int(math.floor(x / G)), int(math.floor(y / G)))

    def _near(grid, x, y, r):
        kx, ky = _key(x, y)
        for i in (-1, 0, 1):
            for j in (-1, 0, 1):
                for (px, py) in grid.get((kx + i, ky + j), ()):
                    if (x - px) ** 2 + (y - py) ** 2 < r * r:
                        return True
        return False
    # every street centreline point (near + far) -> no house within 11 m of a street centre
    for pts in list(ns_near.values()) + ew + ns:
        for (x, y) in _resample(pts, 3.0):
            sgrid.setdefault(_key(x, y), []).append((x, y))

    def free_lot(x, y, r=9.0):
        return not _near(hgrid, x, y, r) and not _near(sgrid, x, y, 14.0)

    def add_placed(x, y, hd):
        placed.append((x, y)); placed_h.append((x, y, hd))
        hgrid.setdefault(_key(x, y), []).append((x, y))

    def lot_ok(x, y):
        if excluded(x, y) or point_in_poly(x, y, WOODLAND) or any(point_in_poly(x, y, f) for f in FAIRWAYS):
            return False
        return math.hypot(x - CENTRE[0], y - CENTRE[1]) < R_SUBURB - 20

    def lots_along(pts, spacing, setback, sides=(1, -1), skip=None):
        pts = _resample(pts, 1.0)
        out = []
        acc = spacing * 0.5
        for i in range(1, len(pts)):
            acc += math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1])
            if acc < spacing:
                continue
            acc = 0.0
            (nx, ny), (tx, ty) = _normal(pts, i)
            for s in sides:
                x, y = pts[i][0] + nx * setback * s, pts[i][1] + ny * setback * s
                if skip and skip(x, y):
                    continue
                # the front faces the street: direction toward the street = (-nx*s, -ny*s)
                fx, fy = -nx * s, -ny * s
                heading = math.atan2(fx, -fy)
                out.append((x, y, heading))
        return out

    near_types = list(range(len(HOUSE_TYPES)))
    for key in ('east', 'north', 'branch', 'west', 'ours_w'):
        pts = ns_near[key]
        sides = {'east': (1, -1), 'north': (1,), 'branch': (1, -1), 'west': (1, -1), 'ours_w': (1, -1)}[key]
        for (x, y, hd) in lots_along(pts, 20.5, SETBACK, sides):
            if not lot_ok(x, y) or not free_lot(x, y, 12.0):
                continue
            W, D, sid, roof, st = HOUSE_TYPES[rng.choice(near_types)]
            style = dict(st)
            style['deck'] = rng.choice(['wood', 'patio', None, 'red', 'wood'])
            style['fence'] = rng.choice([None, None, 'black', 'wood'])
            sh.house(near_kit, x, y, hd, zf(x, y) + 0.3, W=W, D=D, siding=sid, roof=roof, seed=rng.randrange(9999), style=style)
            add_placed(x, y, hd)
    near_kit.build("SF_RowOuter", 'Backdrop')

    # instanced houses along the far streets
    hp = house_protos(M)
    pts_h, idx_h, rot_h = [], [], []
    for pts in ew:
        for run in _clip(pts, lambda x, y: math.hypot(x - CENTRE[0], y - CENTRE[1]) < R_SUBURB):
            for (x, y, hd) in lots_along(run, rng.uniform(20.0, 22.5), SETBACK):
                if not lot_ok(x, y) or not free_lot(x, y, 12.0):
                    continue
                # keep collector corridors clear
                pts_h.append((x, y, zf(x, y)))
                idx_h.append(rng.randrange(len(HOUSE_TYPES)))
                rot_h.append(hd + rng.uniform(-0.03, 0.03))
                add_placed(x, y, hd)
    scatter.instance_points("SF_Suburb_Houses", pts_h, hp, index=idx_h, rot_z=rot_h, coll='Backdrop')
    print(f"[sitefar] suburb: {len(placed)} houses ({len(pts_h)} instanced)")

    # ---- trees: yard / street trees, woodland, fairway clumps
    tn, tf = tree_protos(M)
    near_pts, near_idx, near_rot, near_sc = [], [], [], []
    far_pts, far_idx, far_rot, far_sc = [], [], [], []

    def add_tree(x, y, big=1.0):
        if excluded(x, y):
            return
        r = math.hypot(x - CENTRE[0], y - CENTRE[1])
        if r > R_SUBURB:
            return
        z = zf(x, y)
        s = big * rng.uniform(0.75, 1.3)
        if r < 900:
            near_pts.append((x, y, z)); near_idx.append(rng.randrange(8) if rng.random() < 0.9 else rng.choice((6, 7)))
            near_rot.append(rng.uniform(0, 6.28)); near_sc.append(s)
        else:
            far_pts.append((x, y, z)); far_idx.append(rng.randrange(4)); far_rot.append(rng.uniform(0, 6.28)); far_sc.append(s)
    for (hx, hy, hd) in placed_h:
        # back-yard trees behind the house, a front-yard / street tree (32: canopy between most houses)
        bx, by = -math.sin(hd), math.cos(hd)          # toward the back
        for _ in range(rng.choice((1, 1, 2, 2))):
            d = rng.uniform(14.0, 26.0); o = rng.uniform(-10.0, 10.0)
            add_tree(hx + bx * d - by * o, hy + by * d + bx * o, big=rng.uniform(0.75, 1.15))
        if rng.random() < 0.4:
            d = rng.uniform(-12.0, -8.0); o = rng.uniform(-9.0, 9.0)
            add_tree(hx + bx * d - by * o, hy + by * d + bx * o, big=0.7)
    # street trees along the far streets (32: most streets are lined) and back-yard canopy between the rows
    for pts in ew:
        for (x, y) in _resample(pts, rng.uniform(16.0, 20.0))[::1]:
            for sd in (-1, 1):
                if rng.random() < 0.25:
                    add_tree(x + rng.uniform(-3, 3), y + sd * rng.uniform(7.5, 9.0), big=rng.uniform(0.6, 0.9))
            if rng.random() < 0.6:                    # back-yard line half-way between rows
                add_tree(x + rng.uniform(-6, 6), y + 44.0 + rng.uniform(-5, 5), big=rng.uniform(0.9, 1.3))
    woodland(M, zf, rng, add_tree)
    for poly in FAIRWAYS:
        cx = sum(p[0] for p in poly) / len(poly); cy = sum(p[1] for p in poly) / len(poly)
        for _ in range(26):
            px, py = cx + rng.uniform(-90, 90), cy + rng.uniform(-70, 70)
            if point_in_poly(px, py, poly):
                for k in range(rng.randint(2, 6)):
                    add_tree(px + rng.uniform(-8, 8), py + rng.uniform(-8, 8))
    scatter.instance_points("SF_Suburb_Trees", near_pts, tn, index=near_idx, rot_z=near_rot, scale=near_sc, coll='Backdrop')
    scatter.instance_points("SF_Suburb_TreesFar", far_pts, tf, index=far_idx, rot_z=far_rot, scale=far_sc, coll='Backdrop')
    print(f"[sitefar] suburb trees: {len(near_pts)} near + {len(far_pts)} far instances")

    # ---- far ponds in the fairways
    wp = MB()
    for (px, py, rx, ry) in PONDS_FAR:
        ring = [(px + rx * math.cos(2 * math.pi * k / 24), py + ry * math.sin(2 * math.pi * k / 24)) for k in range(24)]
        z = zf(px, py) - 0.6
        wp.v.extend([(qx, qy, z) for qx, qy in ring] + [(px, py, z)])
        b = len(wp.v) - 25
        for k in range(24):
            wp.f.append((b + k, b + (k + 1) % 24, b + 24)); wp.fm.append(0)
    wp.build("SF_FarPonds", [M['sf_water']], coll='Backdrop', recalc=False)
    bpy.data.collections.remove(bpy.data.collections['SF_Tmp'])
