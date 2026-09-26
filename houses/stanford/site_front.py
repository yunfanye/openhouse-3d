"""The front of the lot and the street row (photos 01, 02, 03, 30, 31): graded lawn, driveway with its control joints and
the pale ring stain, the curved walk, the river-rock beds with red-brick edging, the tree's white-rock ring, the
sidewalk / parkway / curb / street / far side, the neighbours' drives, the utility pedestals and hair-grass emitters.

Evidence (SITE_NEAR fix pass, 2026-09-24; back-projection with the solved cameras, see REFERENCES.md):
  street     sidewalk back edge -8.12 (aerial 31 joint solve, SITE_FAR; photo 01 with EXT's camera -8.10), front edge -9.60,
             gutter / curb line -10.90, far curb -19.57, far parkway to -20.93, far sidewalk to -22.37 (31 + 32)
  driveway   x 0.55 .. 5.52 from the garage door to the sidewalk (31 and 30 agree: straight, as wide as the door + 0.1 m),
             apron flaring to 0.10 .. 6.05 at the curb (31); centre joint x 3.0 (31, 30), transverse joints at y -1.7,
             -4.2, -6.65 (30: 2.5 m panels, 01 -6.0); a paler ring ~2 m across centred (3.9, -6.7) (31 lighter 237 vs 225,
             01 lighter 237 vs 210 with a darker rim) - it reads as a clean spot, not a dark stain
  walk       porch step (slab front y -0.40, EXT) -> curving to the drive, front edge y ~ -1.55 (03: -1.3 .. -1.4,
             30: -1.8), convex toward the lawn; joins the drive's right edge between y -0.85 and -1.65
  beds       river rock + red-brick edging: in front of the porch's left half (x 5.55 .. 7.0, 03 / 30) and along the bay,
             deepest at the porch column (y -1.0, 03) and ~0.5 m deep at the bay's right corner; mulch + brick at the
             garage's left pier (01, 30, 31)
  pedestals  two light-grey telecom pedestals at the right lot line by the sidewalk, beside a spreading juniper (30)
Levels: the front lawn is at -0.32 at the house (the garage-door slab solves at -0.25, the porch slab is -0.17 and one
step above the walk) falling to the sidewalk (-0.50); inferred between.
"""
import math
import random
from .plan import *
from archviz.mesh import MB
from archviz import materials as _m
from archviz import paving as _pv

SW = (-8.12, -9.60)                  # sidewalk y (back edge, front edge)
CURB_Y = -10.90                      # gutter line / curb face
STREET = (-10.90, -19.57)            # curb to curb
FAR_PARK = (-19.57, -20.93)
FAR_SW = (-20.93, -22.37)
Z_SW = -0.50
Z_ST = -0.66                         # asphalt at the gutter; curb reveal 0.15
Z_HOUSE = -0.32                      # front lawn at the house (inferred between the solved slabs)
Z_DOOR = globals().get('Z_GAR_DOOR', Z_GAR)
DRIVE = (0.55, 5.52)
DRIVE_JX = 3.03
DRIVE_JY = (-1.70, -4.20, -6.65)
APRON = (0.10, 6.05)                 # at the curb
STAIN = (3.90, -6.70, 1.00)          # the paler ring on the drive (31, 01)
SW_JOINT0, SW_PITCH = 7.17, 1.87     # sidewalk joints (31: 7.17, 9.06, 10.82, 12.50; 01: 1.8 m)
# neighbours' drives (garage doors from SITE_FAR's aerial solve, +0.15 m each side); ours first
DRIVES = [DRIVE, (-11.40, -6.28), (17.80, 23.05), (-27.70, -22.60)]
WALK_EDGE = [(7.95, -0.40), (7.93, -0.62), (7.82, -0.95), (7.52, -1.25), (7.02, -1.47), (6.40, -1.57), (5.90, -1.62), (5.52, -1.66)]
BED_PORCH = [(5.56, -0.41), (7.00, -0.41), (7.00, -0.86), (5.56, -0.86)]
SLAB_X1 = PORCH_ROOF_X1 - 0.06       # the porch slab's right end (exterior.porch), in front of the bay's corner
BED_BAY_FRONT = [(7.95, -0.42), (8.05, -0.78), (8.35, -0.98), (8.95, -0.98), (9.60, -0.78), (10.50, -0.60), (11.50, -0.52),
                 (XB1, -0.52), (XB1 + 0.42, -0.22), (XB1 + 0.50, 0.30), (XB1 + 0.50, 1.50)]
BED_BAY_BACK = [(XB1, 1.50), (XB1, Y_BAY), (SLAB_X1, Y_BAY), (SLAB_X1, -0.40)]
BED_MULCH = [(-1.36, -0.02), (0.50, -0.02), (0.50, -0.62), (-0.20, -0.78), (-1.36, -0.70)]
TREE = (10.16, -4.48)                # front tree trunk: 01 x 02 trunk azimuths with the final EXT cameras (30 ring 10.86, -4.66)
RING_R = 0.82
PEDESTALS = [(13.75, -7.35, 0.12, 0.62), (14.30, -7.45, 0.10, 0.52)]    # (x, y, radius, height) - 30: two small grey posts
FOOT = [(GAR[0], GAR[1], GAR[2], GAR[3]), (XB0, XB1, YB0, YB1), (PORCH[0], SLAB_X1, -0.40, 1.5), (BAY[0], XB1, Y_BAY, 1.5)]   # house + porch


def grade(x, y):
    """Front-yard lawn height: Z_HOUSE at the facades falling to just above the sidewalk; the parkway from the
    sidewalk to the curb top."""
    if y >= -0.6:
        return Z_HOUSE
    if y >= SW[0]:
        t = (-0.6 - y) / (-0.6 - SW[0])
        return Z_HOUSE + (Z_SW + 0.015 - Z_HOUSE) * t
    if y >= CURB_Y:
        return Z_SW + 0.01 + (Z_ST + 0.14 - Z_SW - 0.01) * (SW[1] - y) / (SW[1] - CURB_Y)
    return Z_ST + 0.14


def z_drive(x, y):
    """Driveway: the garage-door slab level at y 0 falling to the sidewalk, then the apron down to the gutter."""
    if y >= SW[0]:
        return Z_DOOR + (Z_SW - Z_DOOR) * min(1.0, max(0.0, -y / -SW[0]))
    if y >= SW[1]:
        return Z_SW
    return Z_SW + (Z_ST + 0.01 - Z_SW) * (SW[1] - y) / (SW[1] - CURB_Y)


def walk_poly():
    edge = _pv.catmull_loop(WALK_EDGE, n=4, closed=False)
    return [(7.95, -0.40)] + edge[1:] + [(DRIVE[1], -0.86), (7.00, -0.86), (7.00, -0.40)]


def bay_bed_poly():
    front = _pv.catmull_loop(BED_BAY_FRONT, n=4, closed=False)
    return front + BED_BAY_BACK


def _in_any(x, y, polys):
    return any(_pv.point_in_poly(x, y, p) for p in polys)


# ---------------------------------------------------------------- materials
def mats(M):
    if 'sn_drive' in M:
        return M
    # 01 sunlit drive sRGB (204-238, 185-222, 163-211): warm tan-grey; the sidewalk slightly greyer (218, 199, 184); saw-cut joints
    # as thin dark lines, the pale ring with a darker rim, faint tyre lanes and darker concrete toward the garage door
    jd = dict(x=[DRIVE_JX], y=list(DRIVE_JY) + [SW[0]], w=0.016)
    M['sn_drive'] = drive_concrete("DriveConcreteWarm", stain=STAIN, base=(0.76, 0.45, 0.22, 1), joints=jd, garage_dark=0.6, mottle=1.4,
                                   dirt=1.0)
    M['sn_apron'] = drive_concrete("ApronConcreteWarm", base=(0.76, 0.46, 0.23, 1), dirt=0.0, mottle=1.2)
    M['sn_walk'] = drive_concrete("WalkConcreteWarm", stain=None, base=(0.76, 0.48, 0.26, 1), dirt=0.0, mottle=1.0,
                                  joints=dict(xp=(SW_JOINT0, SW_PITCH), x=list(DRIVE), w=0.016))
    M['sn_frontwalk'] = drive_concrete("FrontWalkConcrete", stain=None, base=(0.76, 0.48, 0.26, 1), dirt=0.0, mottle=1.0,
                                       joints=dict(x=[7.0], w=0.014))
    # the street is concrete too (31 / 32: sRGB ~ (217, 204, 175), paler than asphalt) with 4.5 m panels
    M['sn_street'] = drive_concrete("StreetConcrete", stain=None, base=(0.64, 0.46, 0.30, 1), dirt=0.0, mottle=1.2,
                                    joints=dict(xp=(-60.0, 4.5), y=[(STREET[0] + STREET[1]) / 2], w=0.02))
    M['sn_joint'] = _m.new_mat("ConcreteJointDark", (0.05, 0.045, 0.04, 1), rough=0.95)
    M['sn_curb'] = _m.noise_mat("CurbConcreteWarm", (0.44, 0.41, 0.37, 1), (0.56, 0.53, 0.49, 1), scale=12, bump=0.1, rough=0.85)
    M['sn_asphalt'] = _asphalt()
    M['sn_rock_white'] = _pv.pebble_material("RiverRockWhite", colours=((0.72, 0.70, 0.66, 1), (0.60, 0.58, 0.55, 1), (0.80, 0.78, 0.74, 1),
                                                                        (0.46, 0.45, 0.44, 1), (0.66, 0.60, 0.52, 1), (0.52, 0.52, 0.53, 1)))
    M['sn_rock_grit'] = _m.noise_mat("RockGritGrey", (0.16, 0.155, 0.15, 1), (0.30, 0.29, 0.28, 1), scale=60, bump=0.5, rough=0.95)
    M['sn_brick_edge'] = _m.brick_veneer("EdgingPaverBrick", 'XY', base=(0.26, 0.075, 0.045, 1), alt=(0.34, 0.11, 0.06, 1),
                                          dark=(0.16, 0.05, 0.035, 1), mortar=(0.30, 0.28, 0.26, 1))
    M['sn_mulch'] = _m.noise_mat("MulchBrown", (0.07, 0.045, 0.028, 1), (0.16, 0.10, 0.06, 1), scale=35, bump=0.7, rough=0.95)
    M['sn_pedestal'] = _m.noise_mat("PedestalGrey", (0.52, 0.53, 0.50, 1), (0.62, 0.63, 0.60, 1), scale=8, bump=0.05, rough=0.55)
    return M


def _joint_lines(nt, sep, joints):
    """0..1 darkening at saw-cut joints: joints = dict(x=[...], y=[...], xp=(x0, pitch), yp=(y0, pitch), w=half width)."""
    M_ = lambda op, a, c=None: _m._math(nt, op, a, c)
    w = joints.get('w', 0.014)
    ds = []
    for key, axis in (('x', "X"), ('y', "Y")):
        for v in joints.get(key, ()):
            ds.append(M_('ABSOLUTE', M_('SUBTRACT', sep.outputs[axis], v)))
    for key, axis in (('xp', "X"), ('yp', "Y")):
        if joints.get(key):
            x0, p = joints[key]
            f = M_('FRACT', M_('DIVIDE', M_('SUBTRACT', sep.outputs[axis], x0), p))
            ds.append(M_('MULTIPLY', M_('ABSOLUTE', M_('SUBTRACT', f, 0.5)), -p))      # (|f - 0.5| - 0.5) * p = -dist
            ds[-1] = M_('ADD', ds[-1], 0.5 * p)
    if not ds:
        return None
    d = ds[0]
    for e in ds[1:]:
        d = M_('MINIMUM', d, e)
    return M_('SUBTRACT', 1.0, _m._math(nt, 'DIVIDE', d, w, clamp=True))


def drive_concrete(name, stain=None, base=(0.80, 0.68, 0.54, 1), dirt=0.35, joints=None, garage_dark=0.0, mottle=1.0, joint_dark=0.45):
    """Broom-finished concrete, warm grey-tan (01: sunlit 204-238 / 185-222 / 163-211 sRGB): large-scale mottling, blotches
    and fine speckle (x `mottle`), tyre-track lanes down each bay (dirt), darkening toward the garage door (garage_dark,
    over the last 3 m before y 0), darkened saw-cut joint edges (joints, see _joint_lines), and an optional paler ring
    with a darker rim (stain = (cx, cy, r) in object coordinates)."""
    m, nt, b = _m._new(name)
    M_ = lambda op, a, c=None: _m._math(nt, op, a, c)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(sep.inputs["Vector"], tc.outputs["Object"])
    big = _m._noise(nt, _m._coords(nt, scale=(0.35, 0.35, 0.35)), scale=1.0, detail=4.0, rough=0.6)
    mid = _m._noise(nt, tc.outputs["Object"], scale=2.2, detail=6.0, rough=0.65)
    blot = _m._noise(nt, tc.outputs["Object"], scale=7.0, detail=3.0, rough=0.5)
    fine = _m._noise(nt, tc.outputs["Object"], scale=90.0, detail=2.0)
    dk = lambda f: tuple(c * f for c in base[:3]) + (1,)
    # (the sunlit ground sits in AgX's shoulder: albedo contrasts must be large to survive as visible texture)
    col = _m._mixrgb(nt, M_('MULTIPLY', _m._stretch(nt, big, 0.44, 0.58), 0.9 * mottle), base, dk(0.72))
    col = _m._mixrgb(nt, M_('MULTIPLY', _m._stretch(nt, mid, 0.45, 0.57), 0.8 * mottle), col, dk(0.80))
    col = _m._mixrgb(nt, M_('MULTIPLY', _m._stretch(nt, blot, 0.53, 0.62), 0.7 * mottle), col, dk(0.84))
    col = _m._mixrgb(nt, M_('MULTIPLY', fine, 0.35), col, (0.80, 0.78, 0.76, 1), 'MULTIPLY')
    if dirt:
        # tyre lanes: two bands per garage bay (inferred wear pattern; 01 shows faint darker lanes)
        lane = None
        for xc in (1.25, 2.45, 3.65, 4.85):
            d = M_('ABSOLUTE', M_('SUBTRACT', sep.outputs["X"], xc))
            s_ = M_('SUBTRACT', 1.0, _m._math(nt, 'DIVIDE', d, 0.30, clamp=True))
            lane = s_ if lane is None else M_('MAXIMUM', lane, s_)
        lane = M_('MULTIPLY', lane, M_('ADD', 0.5, M_('MULTIPLY', blot, 0.8)))
        near = _m._math(nt, 'DIVIDE', M_('ADD', sep.outputs["Y"], 7.0), 7.0, clamp=True)        # stronger toward the garage
        f = M_('MULTIPLY', M_('MULTIPLY', lane, M_('ADD', 0.3, near)), dirt * 0.45)
        col = _m._mixrgb(nt, _m._math(nt, 'MINIMUM', f, 0.7), col, dk(0.58))
    if garage_dark:
        g = _m._math(nt, 'DIVIDE', M_('ADD', sep.outputs["Y"], 3.0), 3.0, clamp=True)
        col = _m._mixrgb(nt, M_('MULTIPLY', M_('MULTIPLY', g, g), garage_dark), col, dk(0.62))
    if stain:
        cx, cy, r = stain
        dx = M_('SUBTRACT', sep.outputs["X"], cx); dy = M_('SUBTRACT', sep.outputs["Y"], cy)
        rr = M_('SQRT', M_('ADD', M_('MULTIPLY', dx, dx), M_('MULTIPLY', M_('MULTIPLY', dy, dy), 1.25)))
        wob = M_('MULTIPLY', M_('SUBTRACT', mid, 0.5), 0.3)
        rr = M_('ADD', rr, wob)
        inside = M_('SUBTRACT', 1.0, _m._math(nt, 'DIVIDE', M_('SUBTRACT', rr, r * 0.88), r * 0.12, clamp=True))
        rim = M_('SUBTRACT', 1.0, _m._math(nt, 'DIVIDE', M_('ABSOLUTE', M_('SUBTRACT', rr, r)), 0.09, clamp=True))
        col = _m._mixrgb(nt, M_('MULTIPLY', inside, 0.85), col, tuple(min(1.0, c * 1.14) for c in base[:3]) + (1,))
        col = _m._mixrgb(nt, M_('MULTIPLY', rim, 0.8), col, dk(0.60))
    if joints:
        jl = _joint_lines(nt, sep, joints)
        if jl is not None:
            col = _m._mixrgb(nt, M_('MULTIPLY', jl, joint_dark * 2.0), col, dk(0.35))
    nt.links.new(b.inputs["Base Color"], col)
    _m._set(b, "Roughness", 0.88); _m._set(b, "Specular IOR Level", 0.35)
    broom = _m._noise(nt, _m._coords(nt, scale=(2.0, 60.0, 2.0)), scale=1.0, detail=2.0)
    _m._bump(nt, b, M_('ADD', M_('MULTIPLY', broom, 0.5), M_('MULTIPLY', fine, 0.5)), 0.12, 0.004)
    return m


def _asphalt():
    m, nt, b = _m._new("StreetAsphaltWarm")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    fine = _m._noise(nt, tc.outputs["Object"], scale=70.0, detail=3.0)
    big = _m._noise(nt, _m._coords(nt, scale=(0.3, 0.3, 0.3)), scale=1.0, detail=3.0)
    col = _m._ramp(nt, fine, [(0.3, (0.11, 0.105, 0.10, 1)), (0.7, (0.21, 0.20, 0.19, 1))])
    col = _m._mixrgb(nt, _m._math(nt, 'MULTIPLY', big, 0.4), col, (0.85, 0.85, 0.85, 1), 'MULTIPLY')
    nt.links.new(b.inputs["Base Color"], col)
    _m._set(b, "Roughness", 0.9); _m._set(b, "Specular IOR Level", 0.3)
    _m._bump(nt, b, fine, 0.3, 0.01)
    return m


# ---------------------------------------------------------------- slabs with real joints
def _panels(mb, x0, x1, y0, y1, xs, ys, zf, t=0.12, gap=0.008, mi=0):
    """Concrete panels (a slab cut by joints at the x / y lines) whose tops follow zf(x, y); each panel is a
    separate box so the 8 mm joints are real grooves over a dark bed."""
    xs = [x0] + [x for x in xs if x0 < x < x1] + [x1]
    ys = sorted([y0] + [y for y in ys if y0 < y < y1] + [y1])
    for (a0, a1) in zip(xs[:-1], xs[1:]):
        for (b0, b1) in zip(ys[:-1], ys[1:]):
            ga0 = gap / 2 if a0 > x0 else 0.0
            ga1 = gap / 2 if a1 < x1 else 0.0
            gb0 = gap / 2 if b0 > y0 else 0.0
            gb1 = gap / 2 if b1 < y1 else 0.0
            q = [(a0 + ga0, b0 + gb0), (a1 - ga1, b0 + gb0), (a1 - ga1, b1 - gb1), (a0 + ga0, b1 - gb1)]
            top = [(x, y, zf(x, y)) for x, y in q]
            bot = [(x, y, z - t) for x, y, z in top]
            mb.hexa(bot + top, mi)


def hardscape(M):
    mats(M)
    d = MB()
    # our driveway: two columns (centre joint) x transverse joints, then across the sidewalk
    x0, x1 = DRIVE
    _panels(d, x0, x1, SW[0], 0.0, [DRIVE_JX], list(DRIVE_JY), z_drive)
    # the neighbours' drives: same construction, joints every ~2.5 m (31)
    for (a, b) in DRIVES[1:]:
        _panels(d, a, b, SW[0], 0.0, [(a + b) / 2], [-1.7, -4.2, -6.65], z_drive)
    d.build("Driveway", [M['sn_drive']], coll='Site')
    ap = MB()
    for (a, b) in DRIVES:
        fl = 0.45
        pts = [(a, SW[1]), (b, SW[1]), (b + fl, CURB_Y + 0.02), (a - fl, CURB_Y + 0.02)]
        top = [(x, y, z_drive(x, y)) for x, y in pts]
        ap.hexa([(x, y, z - 0.15) for x, y, z in top] + top)
    ap.build("Drive_Aprons", [M['sn_apron']], coll='Site')
    j = MB()
    for (a, b) in DRIVES:                                                          # dark joint bed under every slab
        _panels(j, a - 0.01, b + 0.01, SW[0] - 0.01, -0.005, [], [], lambda x, y: z_drive(x, y) - 0.012, t=0.2, gap=0.0)
    j.build("Drive_JointBed", [M['sn_joint']], coll='Site')
    # sidewalks: 1.48 m wide, joints every 1.87 m, continuous across the drives (the drive slabs stop at SW[0])
    s = MB()
    xs = [SW_JOINT0 + k * SW_PITCH for k in range(-40, 40) if -60 < SW_JOINT0 + k * SW_PITCH < 60]
    _panels(s, -60.0, 60.0, SW[1], SW[0], xs, [], lambda x, y: Z_SW, t=0.12)
    _panels(s, -60.0, 60.0, FAR_SW[1], FAR_SW[0], [x + 0.6 for x in xs], [], lambda x, y: Z_SW, t=0.12)
    s.build("Sidewalk", [M['sn_walk']], coll='Site')
    sb = MB()
    sb.box(-60, 60, SW[1] - 0.01, SW[0] + 0.01, Z_SW - 0.2, Z_SW - 0.013)
    sb.box(-60, 60, FAR_SW[1] - 0.01, FAR_SW[0] + 0.01, Z_SW - 0.2, Z_SW - 0.013)
    sb.build("Sidewalk_JointBed", [M['sn_joint']], coll='Site')
    # curb + gutter (rolled / depressed at the aprons), street, far curb
    c = MB()
    cuts = sorted([(a - 0.45, b + 0.45) for (a, b) in DRIVES])
    xa = -60.0
    for (c0, c1) in cuts + [(60.0, 60.0)]:
        if c0 > xa:
            c.box(xa, c0, CURB_Y, CURB_Y + 0.15, Z_ST - 0.1, Z_ST + 0.15)
        if c1 > c0:
            c.box(c0, c1, CURB_Y, CURB_Y + 0.06, Z_ST - 0.1, Z_ST + 0.03)
        xa = max(xa, c1)
    c.box(-60, 60, CURB_Y - 0.45, CURB_Y, Z_ST - 0.1, Z_ST + 0.005)               # concrete gutter pan
    c.box(-60, 60, STREET[1] - 0.15, STREET[1], Z_ST - 0.1, Z_ST + 0.15)
    c.box(-60, 60, STREET[1], STREET[1] + 0.45, Z_ST - 0.1, Z_ST + 0.005)
    c.build("Curbs", [M['sn_curb']], coll='Site')
    st = MB()
    ym = (STREET[0] + STREET[1]) / 2
    _panels(st, -60.0, 60.0, STREET[1] + 0.45, CURB_Y - 0.45, [-60.0 + 4.5 * k for k in range(1, 27)], [ym], lambda x, y: Z_ST - 0.002,
            t=0.2, gap=0.01)
    st.box(-60, 60, STREET[1] + 0.44, CURB_Y - 0.44, Z_ST - 0.24, Z_ST - 0.014, mi=1)            # joint bed
    st.build("Street", [M['sn_street'], M['sn_joint']], coll='Site')     # SITE_FAR continues it beyond |x| 60
    # the front walk (porch step -> the drive), one slab with a joint at x 7.0
    w = MB()
    poly = _pv.ccw(walk_poly())
    w.prism(poly, -0.44, -0.31)
    w.build("Walk", [M['sn_frontwalk']], coll='Site')


def _brick_edge(mb, pts, z_top, closed=False, mi=0):
    _pv.edging_strip(mb, pts, 0.10, lambda x, y: z_top(x, y) - 0.08, lambda x, y: z_top(x, y) + 0.02, closed=closed, mi=mi,
                     block=0.20, gap=0.007)


def beds(M):
    mats(M)
    zf = lambda x, y: grade(x, y) + 0.035
    # river-rock beds: grit base + real pebbles
    polys = [BED_PORCH, bay_bed_poly()]
    ring = [(TREE[0] + RING_R * math.cos(2 * math.pi * i / 28), TREE[1] + RING_R * math.sin(2 * math.pi * i / 28)) for i in range(28)]
    base = MB()
    for p in polys + [ring]:
        pp = _pv.ccw(p)
        base._add([(x, y, zf(x, y) - 0.015) for x, y in pp], [tuple(range(len(pp)))], 0)
    base.build("Beds_Front_Base", [M['sn_rock_grit']], coll='Site')
    for k, p in enumerate(polys):
        xs = [q[0] for q in p]; ys = [q[1] for q in p]
        _pv.pebble_bed(f"Bed_Rock_Front_{k}", lambda x, y, p=p: _pv.point_in_poly(x, y, p), (min(xs), max(xs), min(ys), max(ys)), zf,
                       M['sn_rock_white'], spacing=0.05, r=(0.016, 0.034), seed=31 + k)
    zr = lambda x, y: grade(x, y) + 0.02 + 0.06 * max(0.0, 1.0 - math.hypot(x - TREE[0], y - TREE[1]) / RING_R)
    _pv.pebble_bed("Land_TreeRing", lambda x, y: math.hypot(x - TREE[0], y - TREE[1]) < RING_R - 0.03,
                   (TREE[0] - RING_R, TREE[0] + RING_R, TREE[1] - RING_R, TREE[1] + RING_R), zr, M['sn_rock_white'],
                   spacing=0.055, r=(0.02, 0.04), seed=77)
    # mulch bed at the garage's left pier
    mu = MB()
    pp = _pv.ccw(BED_MULCH)
    mu.prism(pp, Z_HOUSE - 0.05, Z_HOUSE + 0.03)
    mu.build("Bed_Mulch_Garage", [M['sn_mulch']], coll='Site')
    # red-brick paver edging (03): porch bed front + left side, bay bed front
    e = MB()
    _brick_edge(e, [(7.00, -0.86), (5.56, -0.86), (5.56, -0.41)], zf)
    _brick_edge(e, _pv.catmull_loop(BED_BAY_FRONT, n=4, closed=False)[1:-2], zf)
    e.build("Edging_Front", [M['sn_brick_edge']], coll='Site')


def pedestals(M):
    mats(M)
    p = MB()
    for (x, y, r, h) in PEDESTALS:
        z = grade(x, y)
        p.cylinder(x, y, z - 0.1, z + h - 0.06, r, r * 0.96, seg=16)
        p.lathe(x, y, z + h - 0.06, [(0.0, 0.0), (r * 0.96, 0.0), (r * 0.8, 0.045), (0.0, 0.06)], seg=16)
    p.build("Utility_Pedestals", [M['sn_pedestal']], coll='Site', smooth=True)


def lawn(M, footprints=()):
    """The front lawns of the street row between x -14 and 27 (our lot and both neighbours, where the hair grass
    grows) as a grade-following surface with holes for every drive, walk, bed, the tree ring and the houses;
    the parkway strips; coarse lawn beyond."""
    mats(M)
    polys = [walk_poly(), BED_PORCH, bay_bed_poly(), BED_MULCH]
    foot = list(FOOT) + list(footprints)
    mb = MB()
    pk = MB()
    cell = 0.20
    X0, X1 = -14.0, 27.0
    for (ya, yb, zfun, tgt) in ((SW[0], 12.0, grade, mb), (CURB_Y + 0.02, SW[1], grade, pk)):
        nx, ny = int(round((X1 - X0) / cell)), int(round((yb - ya) / cell))
        for i in range(nx):
            for jj in range(ny):
                ax, ay = X0 + i * cell, ya + jj * cell
                cx, cy = ax + cell / 2, ay + cell / 2
                if any(a - 0.02 < cx < b + 0.02 for (a, b) in DRIVES) and cy < 0.05:
                    continue
                if cy < SW[1]:
                    t = (SW[1] - cy) / (SW[1] - CURB_Y)
                    if any(a - 0.45 * t - 0.05 < cx < b + 0.45 * t + 0.05 for (a, b) in DRIVES):
                        continue
                if any(fx0 - 0.02 < cx < fx1 + 0.02 and fy0 - 0.02 < cy < fy1 + 0.02 for (fx0, fx1, fy0, fy1) in foot):
                    continue
                if cy > -2.5 and _in_any(cx, cy, polys):
                    continue
                if math.hypot(cx - TREE[0], cy - TREE[1]) < RING_R:
                    continue
                if any(math.hypot(cx - x, cy - y) < r + 0.03 for (x, y, r, h) in PEDESTALS):
                    continue
                tgt.quad((ax, ay, zfun(ax, ay)), (ax + cell, ay, zfun(ax + cell, ay)), (ax + cell, ay + cell, zfun(ax + cell, ay + cell)),
                         (ax, ay + cell, zfun(ax, ay + cell)))
    mb.build("Lawn_Front_Lot", [M['sn_lawn_front']], coll='Site', recalc=False)
    pk.build("Lawn_Parkway", [M['sn_lawn_park']], coll='Site', recalc=False)       # the sun-dried tree lawn (01 / 30)
    # coarse lawn (no hair) beyond the hair-grass strip, both sides, front yards + parkways
    far = MB()
    for (xa, xb) in ((-60.0, X0), (X1, 60.0)):
        for (ya, yb) in ((SW[0], 12.0), (CURB_Y + 0.02, SW[1])):
            ys = [ya + (yb - ya) * k / 8 for k in range(9)]
            for (y0, y1) in zip(ys[:-1], ys[1:]):
                far.quad((xa, y0, grade(0, y0) - 0.01), (xb, y0, grade(0, y0) - 0.01), (xb, y1, grade(0, y1) - 0.01), (xa, y1, grade(0, y1) - 0.01))
    for (ya, yb) in (FAR_PARK, (FAR_SW[1] - 30.0, FAR_SW[1])):
        far.quad((-60, ya, Z_SW - 0.01), (60, ya, Z_SW - 0.01), (60, yb, Z_SW - 0.01), (-60, yb, Z_SW - 0.01))
    far.build("Lawn_Front_Far", [M['lawn']], coll='Site')


def build(M, footprints=()):
    mats(M)
    hardscape(M)
    beds(M)
    pedestals(M)
    lawn(M, footprints)
