"""The rear paver patio and its river-rock border (photos 25-28), with the staging seen in the listing photos.

Evidence (SITE_NEAR fix pass, 2026-09-24).  Outline points were read in photo 27 (drone, nearly top-down) and
back-projected onto the patio plane with a 3x4 projective camera fitted in a joint bundle adjustment of photos 25
(rear camera, fixed), 26, 27 and 28 on the rear-wall openings plus shared ground features (4 solar lights, the
shepherd's hook, a terracotta saucer, 4 stepping stones, the table, 4 stools, the grill); residuals 6-7 px.  The
front edge seen from the ground in 26 and 28 lies ~0.1-0.3 m further out than the drone trace; the outline below
takes the drone shape with the depth stretched 3.5 % toward the ground views (uncertainty ~0.2 m).  Where the corner
shrubs hide the edge (both ends at the wall) the outline is inferred.
    patio      x 1.9 .. 10.7 along the rear wall, up to 5.5 m deep; a broad lobe at the grill (+X, left in 25/27), a
               concave waist at x ~6.1 (4.7 m from the wall), a rounded lobe at the table (-X)
    pavers     tumbled concrete cobbles in a European fan with two circle kits (27): one around the table, one in the
               grill lobe
    border     river-rock bed 0.5-0.85 m wide, black plastic edging on the patio side, red-brown brick edging on the lawn
    staging    covered grill, glass-top table + 4 blue-and-white porcelain drum stools, 4 solar path lights, a green
               lantern on a shepherd's hook, a terracotta saucer, 2 wire plant cages, the hose (all as photographed)
"""
import math
import random
from .plan import *
from archviz.mesh import MB
from archviz import materials as _m
from archviz import paving as _pv

# ---------------------------------------------------------------- measured outlines (plan metres; see docstring)
PATIO_EDGE = [                      # from the wall at the +X end, round the front, back to the wall at the -X end
    (10.66, 11.80), (10.47, 12.66), (10.26, 13.29), (10.04, 13.88), (9.90, 14.40), (9.92, 14.80), (9.90, 15.15), (9.83, 15.45),
    (9.68, 15.86), (9.44, 16.27), (9.13, 16.63), (8.72, 16.92), (8.28, 17.08), (7.88, 17.14), (7.47, 17.04), (7.10, 16.82),
    (6.80, 16.63), (6.47, 16.52), (6.09, 16.48), (5.74, 16.57), (5.45, 16.71), (5.15, 16.91), (4.86, 17.11), (4.44, 17.28),
    (4.05, 17.34), (3.68, 17.33), (3.36, 17.22), (3.07, 17.02), (2.79, 16.75), (2.52, 16.42), (2.31, 16.11), (2.05, 15.58),
    (1.93, 15.17), (1.90, 14.73), (1.95, 14.26), (2.01, 13.90), (2.04, 13.20), (2.03, 12.40), (2.00, 11.80)]
BED_OUTER = [                       # lawn side of the river-rock bed (drone trace through the solar-light bases)
    (11.35, 11.80), (11.25, 12.50), (11.00, 13.20), (10.77, 13.68), (10.69, 14.18), (10.68, 14.78), (10.64, 15.27), (10.42, 16.02),
    (10.15, 16.58), (9.60, 17.19), (8.94, 17.65), (8.29, 17.83), (7.62, 17.84), (7.26, 17.81), (6.62, 17.57), (5.99, 17.32),
    (5.49, 17.56), (5.03, 17.76), (4.58, 17.95), (3.98, 18.07), (3.19, 17.82), (2.59, 17.53), (2.02, 17.12), (1.68, 16.54),
    (1.33, 15.90), (1.17, 15.44), (1.16, 14.93), (1.32, 14.49), (1.45, 13.60), (1.40, 12.60), (1.30, 11.80)]
CIRCLES = [(4.30, 14.35, 2.00), (7.55, 14.80, 1.75)]     # paver circle kits: table lobe, grill lobe (27); first wins
TABLE = (4.14, 14.72)                                     # glass-top table (BA of 25/27/28)
STOOLS = [(0.0, 0.62), (65.0, 0.62), (125.0, 0.62), (-115.0, 0.62)]   # (bearing deg from +X, radius) round the table (27)
GRILL = (9.10, 15.35, math.radians(12))                   # covered grill: centre, yaw of its long axis (25/27/28)
LIGHTS = [(7.25, 17.70, 'bronze'), (5.80, 17.30, 'bronze'), (4.02, 17.95, 'silver'), (2.75, 17.52, 'silver')]
HOOK = (4.50, 17.85)                                      # shepherd's hook with the green lantern (26/27/28)
SAUCER = (4.61, 17.36)
CAGES = [(3.40, 17.88), (5.40, 17.72)]                     # wire plant supports (25/26/28)
STONES = [(7.55, 18.27, 0.21), (6.74, 18.03, 0.24), (6.10, 17.75, 0.24), (5.41, 18.12, 0.24), (4.92, 18.26, 0.24)]
HOSE = (9.70, 12.40)                                       # coiled green garden hose by the wall (27/28)
STEP = (6.40, 8.35, 0.40, 0.13)                            # paver step at the slider: x0, x1, depth, rise
# levels: the bundle adjustment puts the rear ground 0.1-0.15 m above the plan's Z_GRADE relative to the wall openings
# (patio ~ -0.24, lawn by the bed ~ -0.25); the yard then falls toward the rear lot line (drainage, inferred)
Z_PAT = -0.27                                              # patio paver surface (2 cm below the first siding course)
Z_BED = Z_PAT - 0.045                                      # rock-bed surface next to the pavers


def z_lawn(x, y):
    """The rear lawn: -0.31 near the house, falling to context's common-lawn level (Z_GRADE - 0.02) at the rear lot
    line and beyond the side lot lines (inferred grading)."""
    z_far = Z_GRADE - 0.02
    t = min(1.0, max(0.0, (y - 18.0) / (29.6 - 18.0)))
    z = -0.31 + (z_far + 0.31) * t
    for edge, inside in ((-3.2, x > -3.2), (15.0, x < 15.0)):
        if not inside:
            k = min(1.0, abs(x - edge) / 2.0)
            z = z + (z_far - z) * k
    return z


Z_LAWN = -0.31                                             # lawn level at the bed (the brick edging sits on it)


def _smooth(pts, n=4):
    """Catmull-Rom through the traced points, keeping the two wall-end points exact."""
    return _pv.catmull_loop(pts, n=n, closed=False)


def patio_poly():
    edge = _smooth(PATIO_EDGE)
    return edge                                          # closes along the wall (y = YB1) from the last point to the first


def bed_outer():
    return _smooth(BED_OUTER)


def in_bed(x, y):
    """Inside the rock bed (between the patio edge and the outer edge, in front of the wall)."""
    return y > YB1 + 0.02 and _pv.point_in_poly(x, y, BED_POLY) and not _pv.point_in_poly(x, y, PATIO_POLY)


PATIO_POLY = None
BED_POLY = None


def _init_polys():
    global PATIO_POLY, BED_POLY
    PATIO_POLY = patio_poly()
    BED_POLY = bed_outer()


_init_polys()


# ---------------------------------------------------------------- materials (site-local, calibrated on 26/27/28)
# paver albedo (EXT, final review): same-surface medians photo / render with each photo's own sun, converted to linear
# through the AgX inverse - shaded pavers 26 (1.43, 0.95, 0.80), 27 (1.45, 1.07, 0.81), 28 (1.50, 1.03, 0.93); the sunlit
# strips (26 / 28) are warmer still (tan-pink ~ (235-240, 210, 185-194) sRGB) -> x (1.48, 1.04, 0.82) on the old tones
PAVER_BASE, PAVER_ALT, PAVER_JOINT = (0.59, 0.364, 0.254, 1), (0.72, 0.452, 0.315, 1), (0.30, 0.205, 0.15, 1)


def mats(M):
    if 'sn_pavers' in M:
        return M
    M['sn_pavers'] = _pv.fan_circle_pavers("PatioCobbleFan", circles=CIRCLES, fan_width=1.30, fan_origin=(6.2, YB1 + 0.25),
                                           ring=0.135, length=0.155, base=PAVER_BASE, alt=PAVER_ALT, joint=PAVER_JOINT, mottle=0.3)
    M['sn_step'] = _pv.fan_circle_pavers("PatioStepPavers", circles=(), fan_width=40.0, fan_origin=(7.3, -30.0), ring=0.135, length=0.20,
                                         base=PAVER_BASE, alt=PAVER_ALT, joint=PAVER_JOINT)
    # 26 / 28 rock bed sRGB ~ (192-208, 166-192, 140-171): cream, white, tan and a few rust / grey pebbles
    M['sn_rock'] = _pv.pebble_material("RiverRockPebbles", colours=((0.82, 0.74, 0.62, 1), (0.66, 0.52, 0.38, 1), (0.60, 0.58, 0.55, 1),
                                                                     (0.74, 0.56, 0.46, 1), (0.46, 0.34, 0.24, 1), (0.88, 0.85, 0.78, 1),
                                                                     (0.76, 0.68, 0.56, 1), (0.58, 0.52, 0.46, 1)))
    M['sn_rock_base'] = _m.noise_mat("RockBedGrit", (0.10, 0.085, 0.07, 1), (0.22, 0.19, 0.16, 1), scale=60, bump=0.6, rough=0.95)
    M['sn_edge_black'] = _m.new_mat("EdgingBlackPlastic", (0.018, 0.018, 0.018, 1), rough=0.45, spec=0.5)
    M['sn_edge_brick'] = _m.noise_mat("EdgingBrickBrown", (0.17, 0.075, 0.045, 1), (0.26, 0.12, 0.07, 1), scale=25, bump=0.3, rough=0.85)
    M['sn_stone'] = _m.noise_mat("SteppingStoneConcrete", (0.24, 0.22, 0.19, 1), (0.34, 0.32, 0.28, 1), scale=18, bump=0.35, rough=0.9)
    M['sn_glass_top'] = _m.new_mat("TableGlassTop", (0.55, 0.62, 0.58, 1), rough=0.3, transmission=0.6, ior=1.5, spec=0.6)   # frosted (27)
    M['sn_metal_dark'] = _m.new_mat("PatioMetalBronze", (0.035, 0.035, 0.03, 1), rough=0.4, metal=0.8)
    M['sn_porcelain'] = _porcelain()
    M['sn_cover'] = _cover()
    M['sn_steel'] = _m.new_mat("GrillCartSteel", (0.55, 0.55, 0.54, 1), rough=0.35, metal=0.9)
    M['sn_rubber'] = _m.new_mat("CasterRubber", (0.03, 0.03, 0.03, 1), rough=0.7)
    M['sn_bronze'] = _m.new_mat("SolarBronze", (0.16, 0.10, 0.06, 1), rough=0.45, metal=0.7)
    M['sn_silver'] = _m.new_mat("SolarSilverCap", (0.55, 0.55, 0.56, 1), rough=0.3, metal=0.8)
    M['sn_clear'] = _m.new_mat("SolarClear", (0.9, 0.9, 0.88, 1), rough=0.12, transmission=0.9, ior=1.45)
    M['sn_lantern'] = _m.noise_mat("LanternTeal", (0.14, 0.30, 0.26, 1), (0.22, 0.42, 0.36, 1), scale=40, bump=0.6, rough=0.5)
    M['sn_terracotta'] = _m.noise_mat("SaucerTerracotta", (0.42, 0.17, 0.08, 1), (0.52, 0.24, 0.12, 1), scale=30, bump=0.2, rough=0.8)
    M['sn_wire'] = _m.new_mat("PlantCageWire", (0.20, 0.26, 0.18, 1), rough=0.4, metal=0.5)
    M['sn_hose'] = _m.new_mat("GardenHoseGreen", (0.02, 0.10, 0.05, 1), rough=0.35, spec=0.5, coat=0.3)
    return M


def _porcelain():
    """Blue-and-white porcelain drum stool: celadon-white glaze, cobalt bands near the rims and a stylised flower
    motif (world z bands: every stool stands on the patio)."""
    m, nt, b = _m._new("PorcelainBlueWhite")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(sep.inputs["Vector"], tc.outputs["Object"])
    z = _m._math(nt, 'SUBTRACT', sep.outputs["Z"], Z_PAT)
    blue = (0.035, 0.07, 0.26, 1)
    white = (0.72, 0.78, 0.74, 1)
    band = None
    for (a, c) in ((0.035, 0.05), (0.075, 0.085), (0.375, 0.39), (0.41, 0.425)):
        s = _m._math(nt, 'MULTIPLY', _m._math(nt, 'GREATER_THAN', z, a), _m._math(nt, 'LESS_THAN', z, c))
        band = s if band is None else _m._math(nt, 'ADD', band, s)
    vor = _m._voronoi(nt, _m._coords(nt, scale=(9, 9, 9)), scale=1.0, feature='F1', rand=0.8)
    motif = _m._math(nt, 'LESS_THAN', vor.outputs["Distance"], 0.16)
    zone = _m._math(nt, 'MULTIPLY', _m._math(nt, 'GREATER_THAN', z, 0.12), _m._math(nt, 'LESS_THAN', z, 0.34))
    f = _m._math(nt, 'MINIMUM', _m._math(nt, 'ADD', band, _m._math(nt, 'MULTIPLY', motif, zone)), 1.0)
    col = _m._mixrgb(nt, f, white, blue)
    nt.links.new(b.inputs["Base Color"], col)
    _m._set(b, "Roughness", 0.12); _m._set(b, "Coat Weight", 0.6); _m._set(b, "Specular IOR Level", 0.6)
    return m


def _cover():
    """Grey-green polyester grill cover with slack folds."""
    m, nt, b = _m._new("GrillCoverGreyGreen")
    vec = _m._coords(nt)
    n = _m._noise(nt, vec, scale=3.0, detail=3.0, distortion=0.6)
    fine = _m._noise(nt, vec, scale=90.0, detail=2.0)
    col = _m._mixrgb(nt, _m._math(nt, 'MULTIPLY', n, 0.4), (0.17, 0.175, 0.14, 1), (0.24, 0.245, 0.20, 1))
    nt.links.new(b.inputs["Base Color"], col)
    _m._set(b, "Roughness", 0.85); _m._set(b, "Sheen Weight", 0.05); _m._set(b, "Specular IOR Level", 0.2)
    _m._bump(nt, b, _m._math(nt, 'ADD', n, _m._math(nt, 'MULTIPLY', fine, 0.1)), 0.6, 0.03)
    return m


# ---------------------------------------------------------------- geometry
def _z_bed(x, y):
    """The bed surface falls from just below the pavers to the lawn at the outer edge."""
    d_in = _pv.dist_to_polyline(x, y, PATIO_POLY, closed=False)
    d_out = _pv.dist_to_polyline(x, y, BED_POLY, closed=False)
    t = d_in / max(1e-6, d_in + d_out)
    return Z_BED + (z_lawn(x, y) + 0.015 - Z_BED) * t * t


def slab(M):
    mats(M)
    poly = PATIO_POLY
    p = MB()
    pts = _pv.ccw(poly)
    p.prism(pts, Z_PAT - 0.16, Z_PAT)
    p.build("Patio", [M['sn_pavers']], coll='Site')
    x0, x1, dep, rise = STEP
    s = MB()
    s.rbox(x0, x1, YB1 - 0.02, YB1 + dep, Z_PAT - 0.05, Z_PAT + rise, r=0.012, seg=2)
    s.build("Patio_Step", [M['sn_step']], coll='Site')
    # black plastic edging on the patio side (free edge only, not along the wall)
    e = MB()
    _pv.edging_strip(e, poly, 0.012, Z_PAT - 0.10, Z_PAT + 0.018)
    e.build("Patio_Edging", [M['sn_edge_black']], coll='Site')


def rock_bed(M):
    mats(M)
    xs = [p[0] for p in BED_POLY]; ys = [p[1] for p in BED_POLY]
    bbox = (min(xs), max(xs), YB1, max(ys))
    base = MB()
    outer = BED_POLY
    # base: the bed polygon minus the patio (both touch the wall): outer edge forward, patio edge back
    ring = list(outer) + list(reversed(PATIO_POLY))
    pts = _pv.ccw(ring)
    base._add([(x, y, _z_bed(x, y) - 0.012) for (x, y) in pts], [tuple(range(len(pts)))], 0)
    base.build("Patio_RockBase", [M['sn_rock_base']], coll='Site')
    _pv.pebble_bed("Patio_RiverRock", in_bed, bbox, _z_bed, M['sn_rock'], spacing=0.058, r=(0.02, 0.045), seed=17)
    # red-brown brick edging on the lawn side
    e = MB()
    _pv.edging_strip(e, outer, 0.08, lambda x, y: z_lawn(x, y) - 0.06, lambda x, y: z_lawn(x, y) + 0.015, block=0.20, gap=0.008)
    e.build("Patio_BrickEdging", [M['sn_edge_brick']], coll='Site')


def stepping_stones(M):
    mats(M)
    rng = random.Random(7)
    s = MB()
    for (x, y, r) in STONES:
        n = 9
        rot = rng.uniform(0, math.pi)
        pts = []
        for i in range(n):
            a = rot + 2 * math.pi * i / n
            rr = r * (1.0 + rng.uniform(-0.10, 0.08)) * (1.12 if i % 3 == 0 else 1.0)
            pts.append((x + rr * math.cos(a), y + rr * 0.92 * math.sin(a)))
        s.prism(_pv.ccw(pts), z_lawn(x, y) - 0.05, z_lawn(x, y) + 0.018)
    s.build("Stepping_Stones", [M['sn_stone']], coll='Site')


def table_and_stools(M):
    mats(M)
    tx, ty = TABLE
    z0 = Z_PAT
    t = MB()
    t.cylinder(tx, ty, z0 + 0.715, z0 + 0.725, 0.455, seg=40, mi=0)           # glass
    t.cylinder(tx, ty, z0 + 0.705, z0 + 0.735, 0.47, seg=40, mi=1)            # rim band (hollow look via glass on top)
    for k in range(4):                                                        # 4 splayed legs on a cross base
        a = math.pi / 4 + k * math.pi / 2
        t.path_tube([(tx + 0.36 * math.cos(a), ty + 0.36 * math.sin(a), z0 + 0.70), (tx + 0.22 * math.cos(a), ty + 0.22 * math.sin(a), z0 + 0.45),
                     (tx + 0.20 * math.cos(a), ty + 0.20 * math.sin(a), z0 + 0.20), (tx + 0.30 * math.cos(a), ty + 0.30 * math.sin(a), z0 + 0.012)],
                    0.011, seg=6, mi=1)
        t.cylinder(tx + 0.30 * math.cos(a), ty + 0.30 * math.sin(a), z0, z0 + 0.012, 0.022, seg=8, mi=1)
    t.cylinder(tx, ty, z0 + 0.30, z0 + 0.33, 0.21, seg=24, mi=1)             # ring stretcher
    t.cylinder(tx, ty, z0 + 0.32, z0 + 0.715, 0.022, seg=10, mi=1)           # umbrella hole post
    t.build("Patio_Table", [M['sn_glass_top'], M['sn_metal_dark']], coll='Site')
    st = MB()
    prof = [(0.0, 0.0), (0.125, 0.0), (0.14, 0.03), (0.165, 0.12), (0.172, 0.23), (0.165, 0.34), (0.145, 0.42), (0.13, 0.445),
            (0.10, 0.455), (0.0, 0.458)]
    for (bear, r) in STOOLS:
        a = math.radians(bear)
        st.lathe(tx + r * math.cos(a), ty + r * math.sin(a), z0, prof, seg=28)
    st.build("Patio_Stools", [M['sn_porcelain']], coll='Site', smooth=True)


def grill(M):
    mats(M)
    cx, cy, yaw = GRILL
    z0 = Z_PAT
    c, s = math.cos(yaw), math.sin(yaw)

    def P(u, v, w):
        return (cx + u * c - v * s, cy + u * s + v * c, z0 + w)
    cart = MB()
    cart.rcbox(cx, cy, z0 + 0.17, 1.02, 0.46, 0.10, r=0.02, rot=yaw, mi=0)
    for (u, v) in ((-0.46, -0.19), (0.46, -0.19), (-0.46, 0.19), (0.46, 0.19)):
        x, y, _ = P(u, v, 0)
        cart.cylinder(x, y, z0 + 0.0, z0 + 0.10, 0.045, seg=10, mi=1)
        cart.cylinder(x, y, z0 + 0.10, z0 + 0.13, 0.02, seg=6, mi=0)
    cart.build("Patio_GrillCart", [M['sn_steel'], M['sn_rubber']], coll='Site')
    cov = MB()
    # the cover (25/27/28): a slack grey-green hood over the grill + side shelves: a straight-sided body 1.25 x 0.62 m from
    # 0.24 m (hem) to 0.86 m and a domed lid to 1.19 m (28: the rounded top), slightly bulging
    cov.rcbox(cx, cy, z0 + 0.55, 1.25, 0.62, 0.62, r=0.07, rot=yaw, puff=0.4)
    cov.rcbox(cx, cy, z0 + 0.99, 1.16, 0.58, 0.42, r=0.19, rot=yaw, puff=0.6)
    cov.build("Patio_GrillCover", [M['sn_cover']], coll='Site', smooth=True, bevel=0.02)


def lights(M):
    mats(M)
    L = MB()
    for (x, y, kind) in LIGHTS:
        zg = _z_bed(x, y)
        L.cylinder(x, y, zg - 0.10, zg + (0.26 if kind == 'bronze' else 0.30), 0.009, seg=6, mi=0)      # stake
        if kind == 'bronze':
            L.cylinder(x, y, zg + 0.26, zg + 0.36, 0.045, 0.040, seg=8, mi=2)                             # lens
            L.lathe(x, y, zg + 0.355, [(0.0, 0.0), (0.075, 0.0), (0.06, 0.03), (0.0, 0.045)], seg=8, mi=0)  # roof
        else:
            L.cylinder(x, y, zg + 0.30, zg + 0.40, 0.050, 0.055, seg=16, mi=2)
            L.lathe(x, y, zg + 0.40, [(0.0, 0.0), (0.085, 0.0), (0.08, 0.018), (0.035, 0.04), (0.0, 0.045)], seg=20, mi=1)
    L.build("Patio_SolarLights", [M['sn_bronze'], M['sn_silver'], M['sn_clear']], coll='Site')
    h = MB()
    x, y = HOOK
    zg = _z_bed(x, y)
    pts = [(x, y, zg - 0.15), (x, y, zg + 1.30)]
    for k in range(9):
        a = math.pi * k / 8
        pts.append((x + 0.12 - 0.12 * math.cos(a), y, zg + 1.30 + 0.12 * math.sin(a)))
    h.path_tube(pts, 0.006, seg=6, mi=0)
    lx, lz = x + 0.24, zg + 1.02
    h.path_tube([(lx, y, zg + 1.30), (lx, y, lz + 0.30)], 0.002, seg=4, mi=0)
    h.cylinder(lx, y, lz, lz + 0.26, 0.058, seg=16, mi=1)
    h.lathe(lx, y, lz + 0.26, [(0.0, 0.0), (0.07, 0.0), (0.03, 0.035), (0.0, 0.04)], seg=16, mi=1)
    h.build("Patio_ShepherdHook", [M['sn_metal_dark'], M['sn_lantern']], coll='Site')
    sa = MB()
    x, y = SAUCER
    zg = _z_bed(x, y)
    sa.lathe(x, y, zg, [(0.0, 0.0), (0.12, 0.0), (0.155, 0.035), (0.16, 0.04), (0.14, 0.04), (0.11, 0.012), (0.0, 0.012)], seg=24)
    sa.build("Patio_Saucer", [M['sn_terracotta']], coll='Site', smooth=True)
    w = MB()
    for (x, y) in CAGES:
        zg = _z_bed(x, y)
        for (r, z) in ((0.10, 0.16), (0.14, 0.36), (0.18, 0.58)):
            w.path_tube([(x + r * math.cos(2 * math.pi * i / 16), y + r * math.sin(2 * math.pi * i / 16), zg + z) for i in range(17)], 0.003, seg=4)
        for k in range(3):
            a = 2 * math.pi * k / 3 + 0.4
            w.path_tube([(x + 0.07 * math.cos(a), y + 0.07 * math.sin(a), zg - 0.1), (x + 0.185 * math.cos(a), y + 0.185 * math.sin(a), zg + 0.60)],
                        0.003, seg=4)
    w.build("Patio_PlantCages", [M['sn_wire']], coll='Site')


def hose(M):
    mats(M)
    hx, hy = HOSE
    z = Z_PAT + 0.012
    rng = random.Random(3)
    pts = []
    for k in range(7):                                           # loose loops lying on the pavers
        r = 0.30 + 0.05 * k + rng.uniform(-0.03, 0.03)
        cx, cy = hx + rng.uniform(-0.06, 0.06), hy + rng.uniform(-0.05, 0.05)
        for i in range(18):
            a = 2 * math.pi * i / 18
            pts.append((cx + r * math.cos(a), cy + 0.75 * r * math.sin(a), z + 0.012 * (k % 3)))
    pts += [(hx + 0.55, YB1 + 0.10, z), (10.55, YB1 + 0.05, z), (10.55, YB1 + 0.02, 0.35)]   # up to the hose bib
    hm = MB()
    hm.path_tube(pts, 0.011, seg=6)
    hm.build("Patio_Hose", [M['sn_hose']], coll='Site', smooth=True)


def build(M):
    mats(M)
    slab(M)
    rock_bed(M)
    stepping_stones(M)
    table_and_stools(M)
    grill(M)
    lights(M)
    hose(M)
