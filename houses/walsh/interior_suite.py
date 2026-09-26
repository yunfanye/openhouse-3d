"""Suite interiors at Z_LIV: master bedroom / bath / closet, office, gym + sauna, guest rooms, and the
vestibule that links them to the dining.  Envelope walls + exterior glass come from exterior.py; this
module builds floors, ceilings, partitions, wall finishes, furniture, decor and lights for its rooms."""
import math, random
from .plan import *
from archviz.mesh import *
from archviz.lights import *
from archviz.parts import *

PT = 0.15                      # interior partition thickness
Z0 = Z_LIV
ZC = Z_SOF - 0.4               # 5.5 dropped ceiling of the suite rooms
CEIL_T = 0.05

# inner (finish) volumes after the partitions have been placed
MASTER = (-12.05, -4.675, 17.8, 23.55)
VEST = (-4.525, 3.325, 17.95, 19.525)
BATH = (-4.525, -0.675, 19.675, 23.55)
CLOSET = (-0.525, 3.325, 19.675, 23.55)
OFFICE = (3.475, 7.05, 17.95, 23.55)
GYM = (7.9, 14.2, 18.25, 23.55)
GUEST2 = (14.6, 18.4, 18.25, 23.55)       # queen guest room (photo 27)
GUEST = (18.6, 24.0, 18.25, 23.55)        # twin guest room (photo 25)


# ------------------------------------------------------------------ small local helpers
def rrect_pts(cx, cz, w, h, r, seg=6):
    pts = []
    for (ox, oz, a0) in ((w / 2 - r, -h / 2 + r, -math.pi / 2), (w / 2 - r, h / 2 - r, 0.0),
                         (-w / 2 + r, h / 2 - r, math.pi / 2), (-w / 2 + r, -h / 2 + r, math.pi)):
        for k in range(seg + 1):
            a = a0 + math.pi / 2 * k / seg
            pts.append((cx + ox + r * math.cos(a), cz + oz + r * math.sin(a)))
    return pts


def rrect_xz(mb, cx, cz, y0, y1, w, h, r, mi=0):
    """Rounded-rectangle plate in the XZ plane (hung on a wall running along X)."""
    pts = rrect_pts(cx, cz, w, h, r)
    mb.sweep([[(x, y0, z) for (x, z) in pts], [(x, y1, z) for (x, z) in pts]], mi)


def rrect_yz(mb, cy, cz, x0, x1, w, h, r, mi=0):
    pts = rrect_pts(cy, cz, w, h, r)
    mb.sweep([[(x0, y, z) for (y, z) in pts], [(x1, y, z) for (y, z) in pts]], mi)


def arch_yz(mb, cy, z0, x0, x1, w, h, mi=0, seg=12):
    """Arched (round-top) plate in the YZ plane."""
    r = w / 2
    pts = [(cy - r, z0), (cy + r, z0)]
    for k in range(seg + 1):
        a = -math.pi / 2 + math.pi * k / seg
        pts.append((cy + r * math.sin(a) * -1, z0 + h - r + r * math.cos(a)))
    pts = [(cy - r, z0), (cy + r, z0)] + [(cy + r * math.cos(math.pi * k / seg), z0 + h - r + r * math.sin(math.pi * k / seg)) for k in range(seg + 1)]
    mb.sweep([[(x0, y, z) for (y, z) in pts], [(x1, y, z) for (y, z) in pts]], mi)


def part_x(mb, x, y0, y1, z0, z1, holes=(), mi=0, t=PT):
    mb.wall('Y', y0, y1, x - t / 2, x + t / 2, z0, z1, holes=holes, mi=mi)


def part_y(mb, y, x0, x1, z0, z1, holes=(), mi=0, t=PT):
    mb.wall('X', x0, x1, y - t / 2, y + t / 2, z0, z1, holes=holes, mi=mi)


def track_y(mb, y0, y1, x, z, mi_track=0, mi_lamp=1, n=4):
    mb.box(x - 0.03, x + 0.03, y0, y1, z - 0.01, z + 0.02, mi_track)
    for i in range(n):
        y = y0 + (y1 - y0) * (i + 0.5) / n
        mb.cylinder(x, y, z - 0.02, z - 0.005, 0.02, seg=8, mi=mi_lamp)


def spin_bike(mb, x, y, z, rot=0.0, mi=0, mi_red=1, mi_screen=2, mi_bottle=3):
    """Peloton-style spin bike (photo 20): matt-black frame - front mast, sloping top tube, seat post - a small
    (Ø 0.46 m) black flywheel low at the front with a red belt guard, bullhorn bars with a tablet screen, saddle,
    cranks + pedals, bottle.  Faces its own -Y (screen end)."""
    def P(cx, cy, cz):
        px, py = rot2(x + cx, y + cy, x, y, rot)
        return (px, py, z + cz)
    def B(cx, cy, cz, sx, sy, sz, mi_):
        px, py = rot2(x + cx, y + cy, x, y, rot)
        mb.cbox(px, py, z + cz, sx, sy, sz, mi_, rot)
    def R(cx, cy, cz, sx, sy, sz, mi_, r=0.02):
        px, py = rot2(x + cx, y + cy, x, y, rot)
        mb.rcbox(px, py, z + cz, sx, sy, sz, r, mi_, rot)
    def disc(cy, cz, r, t, mi_, seg=32):
        """Solid disc whose axis is the bike's local X (across the bike)."""
        secs = []
        for lx in (-t / 2, t / 2):
            secs.append([P(lx, cy + r * math.cos(2 * math.pi * i / seg), cz + r * math.sin(2 * math.pi * i / seg)) for i in range(seg)])
        mb.sweep(secs, mi_)
    def ring(cy, cz, R_, r_, mi_, seg=32, rings=10):
        secs = []
        for i in range(seg):
            a_ = 2 * math.pi * i / seg
            sec = []
            for j in range(rings):
                b_ = 2 * math.pi * j / rings
                rr = R_ + r_ * math.cos(b_)
                sec.append(P(r_ * math.sin(b_), cy + rr * math.cos(a_), cz + rr * math.sin(a_)))
            secs.append(sec)
        mb.sweep(secs, mi_, close=True, caps=False)
    # stabilisers with rubber feet + the base rail (with a transport roller at the front)
    R(0, -0.56, 0.035, 0.60, 0.075, 0.07, mi, r=0.02); R(0, 0.50, 0.035, 0.60, 0.075, 0.07, mi, r=0.02)
    for sx in (-1, 1):
        mb.cylinder(*P(sx * 0.27, -0.56, 0.0)[:2], z, z + 0.012, 0.03, seg=12, mi=mi)
        mb.cylinder(*P(sx * 0.27, 0.50, 0.0)[:2], z, z + 0.012, 0.03, seg=12, mi=mi)
    R(0, -0.03, 0.08, 0.10, 1.10, 0.08, mi, r=0.025)
    # flywheel low at the front: black disc, red belt-guard ring, hub, belt housing up to the bottom bracket
    fy, fz = -0.36, 0.26
    disc(fy, fz, 0.225, 0.045, mi)
    ring(fy, fz, 0.235, 0.014, mi_red)
    disc(fy, fz, 0.06, 0.07, mi)
    B(0, (fy - 0.05) / 2, 0.30, 0.07, 0.36, 0.09, mi)                                        # belt guard body
    # bottom bracket, crank arms, pedals
    bb = (0, -0.02, 0.32)
    mb.tube(P(-0.07, bb[1], bb[2]), P(0.07, bb[1], bb[2]), 0.035, 0.035, seg=14, mi=mi)
    for sgn in (-1, 1):
        ca = P(sgn * 0.085, bb[1], bb[2]); cb = P(sgn * 0.085, bb[1] + sgn * 0.17, bb[2] - sgn * 0.02)
        mb.tube(ca, cb, 0.012, 0.010, seg=8, mi=mi)
        R(sgn * 0.13, bb[1] + sgn * 0.17, bb[2] - sgn * 0.02, 0.09, 0.10, 0.02, mi, r=0.008)
    # frame: front mast, sloping top tube, seat tube + post
    mb.tube(P(0, -0.40, 0.10), P(0, -0.42, 1.00), 0.034, 0.030, seg=12, mi=mi)                # front mast
    mb.tube(P(0, -0.40, 0.88), P(0, 0.30, 0.60), 0.032, 0.030, seg=12, mi=mi)                 # top tube
    mb.tube(P(0, 0.30, 0.10), P(0, 0.30, 0.62), 0.030, 0.030, seg=12, mi=mi)                  # seat tube
    mb.tube(P(0, -0.02, 0.10), P(0, -0.02, 0.32), 0.026, 0.026, seg=10, mi=mi)                # bb strut
    mb.tube(P(0, 0.30, 0.62), P(0, 0.34, 0.96), 0.018, 0.018, seg=10, mi=mi)                  # seat post
    B(0, 0.30, 0.62, 0.06, 0.08, 0.05, mi)                                                    # seat clamp
    R(0, 0.36, 0.99, 0.15, 0.27, 0.045, mi, r=0.02)                                            # saddle
    R(0, 0.44, 1.00, 0.10, 0.10, 0.06, mi, r=0.02)
    # handlebar stem + bullhorn bars + tablet screen
    mb.tube(P(0, -0.42, 1.00), P(0, -0.50, 1.10), 0.018, 0.018, seg=10, mi=mi)
    mb.path_tube([P(-0.24, -0.30, 1.10), P(-0.24, -0.62, 1.10), P(-0.16, -0.66, 1.10), P(0.16, -0.66, 1.10), P(0.24, -0.62, 1.10), P(0.24, -0.30, 1.10)], 0.016, seg=10, mi=mi)
    mb.tube(P(-0.24, -0.50, 1.10), P(0.24, -0.50, 1.10), 0.014, 0.014, seg=10, mi=mi)         # cross bar
    mb.tube(P(0, -0.50, 1.10), P(0, -0.70, 1.22), 0.014, 0.014, seg=8, mi=mi)                  # screen arm
    R(0, -0.735, 1.32, 0.52, 0.025, 0.32, mi, r=0.012)                                         # tablet body
    B(0, -0.7495, 1.32, 0.48, 0.002, 0.28, mi_screen)                                           # screen glass (faces forward)
    # bottle cage on the mast + bottle
    bt = P(0, -0.46, 0.55)
    mb.lathe(bt[0], bt[1], bt[2], [(0, 0), (0.032, 0), (0.032, 0.16), (0.02, 0.19), (0.012, 0.22), (0, 0.22)], seg=12, mi=mi_bottle)
    mb.tube(P(0, -0.46, 0.58), P(0, -0.42, 0.58), 0.006, 0.006, seg=6, mi=mi)


def flames(mb, x0, x1, y0, y1, z, n=26, seed=3, mi=0, h=(0.12, 0.26)):
    rng = random.Random(seed)
    for i in range(n):
        x = rng.uniform(x0, x1); y = rng.uniform(y0, y1)
        mb.cylinder(x, y, z, z + rng.uniform(*h), rng.uniform(0.02, 0.04), 0.004, seg=6, mi=mi)


def towel_stack(mb, x, y, z, n=3, w=0.45, d=0.32, mi=0, rot=0.0):
    for i in range(n):
        mb.cbox(x, y, z + 0.035 + i * 0.07, w - i * 0.01, d, 0.07, mi, rot)


def garment(mb, x, y, z_rail, mi, along='Y', w=0.42, h=0.9):
    """A hanging shirt: thin slab under a hanger hook."""
    if along == 'Y':
        mb.box(x - 0.02, x + 0.02, y - w / 2, y + w / 2, z_rail - 0.06 - h, z_rail - 0.06, mi)
    else:
        mb.box(x - w / 2, x + w / 2, y - 0.02, y + 0.02, z_rail - 0.06 - h, z_rail - 0.06, mi)
    mb.cylinder(x, y, z_rail - 0.06, z_rail + 0.01, 0.006, seg=6, mi=mi)


def floor_ceiling(mb, room, mi_floor, mi_ceil, z0=Z0, z1=ZC):
    x0, x1, y0, y1 = room
    mb.box(x0, x1, y0, y1, z0, z0 + 0.02, mi_floor)
    mb.box(x0, x1, y0, y1, z1 - CEIL_T, z1, mi_ceil)


def finish(mb, room, faces, mi, t=0.02, z0=Z0, z1=ZC, holes=None):
    """Thin finish panels on the given faces ('N','S','E','W') of a room volume."""
    x0, x1, y0, y1 = room
    holes = holes or {}
    if 'W' in faces: mb.wall('Y', y0, y1, x0, x0 + t, z0, z1, holes=holes.get('W', ()), mi=mi)
    if 'E' in faces: mb.wall('Y', y0, y1, x1 - t, x1, z0, z1, holes=holes.get('E', ()), mi=mi)
    if 'S' in faces: mb.wall('X', x0, x1, y0, y0 + t, z0, z1, holes=holes.get('S', ()), mi=mi)
    if 'N' in faces: mb.wall('X', x0, x1, y1 - t, y1, z0, z1, holes=holes.get('N', ()), mi=mi)


# ------------------------------------------------------------------ hyper-detail helpers
def room_details(mb, room, z0=Z0, z1=ZC, mi_gap=0, mi_speaker=1, mi_diffuser=2, diffusers=(), speakers=(), skirt=True, faces='WESN'):
    """Shadow-gap detailing: 6 mm dark reveal where walls meet the ceiling, 12 mm shadow-gap skirting at the floor,
    recessed linear slot diffusers (black 60 x 600) and 150 mm speaker discs in the ceiling."""
    x0, x1, y0, y1 = room
    zc = z1 - CEIL_T
    g, sk = 0.006, 0.012
    for f in faces:
        if f == 'W':
            mb.box(x0 - 0.001, x0 + 0.03, y0, y1, zc - g, zc + 0.001, mi_gap)
            if skirt: mb.box(x0 - 0.001, x0 + 0.012, y0, y1, z0 + 0.02, z0 + 0.02 + sk * 5, mi_gap)
        if f == 'E':
            mb.box(x1 - 0.03, x1 + 0.001, y0, y1, zc - g, zc + 0.001, mi_gap)
            if skirt: mb.box(x1 - 0.012, x1 + 0.001, y0, y1, z0 + 0.02, z0 + 0.02 + sk * 5, mi_gap)
        if f == 'S':
            mb.box(x0, x1, y0 - 0.001, y0 + 0.03, zc - g, zc + 0.001, mi_gap)
            if skirt: mb.box(x0, x1, y0 - 0.001, y0 + 0.012, z0 + 0.02, z0 + 0.02 + sk * 5, mi_gap)
        if f == 'N':
            mb.box(x0, x1, y1 - 0.03, y1 + 0.001, zc - g, zc + 0.001, mi_gap)
            if skirt: mb.box(x0, x1, y1 - 0.012, y1 + 0.001, z0 + 0.02, z0 + 0.02 + sk * 5, mi_gap)
    for (dx, dy, along) in diffusers:
        if along == 'X':
            mb.box(dx - 0.30, dx + 0.30, dy - 0.03, dy + 0.03, zc - 0.004, zc + 0.03, mi_diffuser)
            for k in range(6):
                mb.box(dx - 0.28 + k * 0.095, dx - 0.28 + k * 0.095 + 0.07, dy - 0.02, dy + 0.02, zc - 0.006, zc - 0.004, mi_gap)
        else:
            mb.box(dx - 0.03, dx + 0.03, dy - 0.30, dy + 0.30, zc - 0.004, zc + 0.03, mi_diffuser)
            for k in range(6):
                mb.box(dx - 0.02, dx + 0.02, dy - 0.28 + k * 0.095, dy - 0.28 + k * 0.095 + 0.07, zc - 0.006, zc - 0.004, mi_gap)
    for (sx, sy) in speakers:
        mb.lathe(sx, sy, zc - 0.006, [(0, 0), (0.07, 0), (0.075, 0.003), (0.075, 0.006), (0, 0.006)], seg=24, mi=mi_speaker)


def door_hardware(mb, x0, x1, y, z1, mi_black, along='X', side=1, z0=Z0):
    """Black 20 mm reveal around a door, an edge pull bar and two hinge lines, plus a switch plate beside it."""
    if along == 'X':
        mb.box(x0 - 0.02, x0, y - PT / 2 - 0.01, y + PT / 2 + 0.01, z0, z1 + 0.02, mi_black)
        mb.box(x1, x1 + 0.02, y - PT / 2 - 0.01, y + PT / 2 + 0.01, z0, z1 + 0.02, mi_black)
        mb.box(x0 - 0.02, x1 + 0.02, y - PT / 2 - 0.01, y + PT / 2 + 0.01, z1, z1 + 0.02, mi_black)
        px = x1 - 0.06 if side > 0 else x0 + 0.06
        mb.box(px - 0.012, px + 0.012, y - 0.05, y + 0.05, z0 + 0.85, z0 + 1.25, mi_black)          # edge pull
        hx = x0 + 0.005 if side > 0 else x1 - 0.005
        for hz in (z0 + 0.25, z1 - 0.3):
            mb.box(hx - 0.004, hx + 0.004, y - 0.03, y + 0.03, hz, hz + 0.1, mi_black)
        sx = x1 + 0.18 if side > 0 else x0 - 0.18
        mb.box(sx - 0.04, sx + 0.04, y - PT / 2 - 0.006, y - PT / 2, z0 + 1.05, z0 + 1.13, mi_black + 1)
    else:
        mb.box(y - PT / 2 - 0.01, y + PT / 2 + 0.01, x0 - 0.02, x0, z0, z1 + 0.02, mi_black)
        mb.box(y - PT / 2 - 0.01, y + PT / 2 + 0.01, x1, x1 + 0.02, z0, z1 + 0.02, mi_black)
        mb.box(y - PT / 2 - 0.01, y + PT / 2 + 0.01, x0 - 0.02, x1 + 0.02, z1, z1 + 0.02, mi_black)
        py = x1 - 0.06 if side > 0 else x0 + 0.06
        mb.box(y - 0.05, y + 0.05, py - 0.012, py + 0.012, z0 + 0.85, z0 + 1.25, mi_black)
        hy = x0 + 0.005 if side > 0 else x1 - 0.005
        for hz in (z0 + 0.25, z1 - 0.3):
            mb.box(y - 0.03, y + 0.03, hy - 0.004, hy + 0.004, hz, hz + 0.1, mi_black)
        sy = x1 + 0.18 if side > 0 else x0 - 0.18
        mb.box(y - PT / 2 - 0.006, y - PT / 2, sy - 0.04, sy + 0.04, z0 + 1.05, z0 + 1.13, mi_black + 1)


def floater_canvas(mb, a0, a1, b, z0, z1, mi_frame, mi_canvas, along='X', face=1):
    """Canvas on a 4 mm stretcher floating inside a 30 mm-deep frame with a 8 mm shadow gap."""
    d = 0.03
    if along == 'X':
        mb.frame(a0, a1, b, b + face * d, z0, z1, 0.012, mi_frame, axis='Y')
        mb.box(a0 + 0.02, a1 - 0.02, b + face * 0.008, b + face * (d - 0.004), z0 + 0.02, z1 - 0.02, mi_canvas)
    else:
        mb.frame(b, b + face * d, a0, a1, z0, z1, 0.012, mi_frame, axis='X')
        mb.box(b + face * 0.008, b + face * (d - 0.004), a0 + 0.02, a1 - 0.02, z0 + 0.02, z1 - 0.02, mi_canvas)


def carafe(mb, x, y, z, mi_glass, mi_water=None, h=0.22):
    mb.lathe(x, y, z, [(0, 0), (0.045, 0), (0.05, h * 0.55), (0.035, h * 0.72), (0.03, h), (0.026, h), (0.026, 0.01), (0, 0.01)], seg=20, mi=mi_glass)
    mb.lathe(x + 0.09, y, z, [(0, 0), (0.03, 0), (0.035, 0.09), (0.03, 0.09), (0.028, 0.008), (0, 0.008)], seg=16, mi=mi_glass)


def bulb_lamp(mb, x, y, z, mi_base, mi_shade, mi_bulb, mi_cord, base_r=0.13, base_h=0.36, shade_r=0.22, shade_h=0.22, cord_to=None):
    lamp(mb, x, y, z, mi_base=mi_base, mi_shade=mi_shade, base_r=base_r, base_h=base_h, shade_r=shade_r, shade_h=shade_h)
    mb.sphere((x, y, z + base_h + 0.08 + shade_h * 0.45), 0.028, seg=12, rings=8, mi=mi_bulb)
    if cord_to is not None:
        mb.path_tube([(x + base_r * 0.6, y, z + 0.003), cord_to], 0.003, seg=6, mi=mi_cord)


def pebble_bed(mb, x0, x1, y0, y1, z, n=80, mi=0, seed=1):
    rng = random.Random(seed)
    for i in range(n):
        r = rng.uniform(0.014, 0.026)
        mb.blob((rng.uniform(x0 + r, x1 - r), rng.uniform(y0 + r, y1 - r), z + r * 0.6), r, seg=8, rings=5, jitter=0.25, seed=seed * 50 + i, mi=mi, squash=0.65, rx=rng.uniform(0.8, 1.3))


def flame_tongues(mb, x0, x1, y0, y1, z, n=30, seed=3, mi=0, h=(0.10, 0.26)):
    """Slender tapered tongues with a slight lean, in two staggered rows."""
    rng = random.Random(seed)
    for i in range(n):
        x = rng.uniform(x0, x1); y = rng.uniform(y0, y1)
        hh = rng.uniform(*h) * (1.0 if rng.random() < 0.7 else 0.55)
        r = rng.uniform(0.012, 0.024)
        mb.blob((x, y, z + hh * 0.45), r, seg=7, rings=7, jitter=0.6, seed=seed * 100 + i, mi=mi, squash=hh / (2 * r), ry=rng.uniform(0.6, 1.0))


def candle(mb, x, y, z, mi_glass, mi_wax, mi_flame, r=0.035, h=0.09):
    mb.lathe(x, y, z, [(0, 0), (r, 0), (r, h), (r - 0.003, h), (r - 0.003, 0.004), (0, 0.004)], seg=16, mi=mi_glass)
    mb.cylinder(x, y, z + 0.004, z + h * 0.7, r - 0.004, seg=16, mi=mi_wax)
    mb.blob((x, y, z + h * 0.7 + 0.014), 0.006, seg=6, rings=5, mi=mi_flame, squash=2.2)


def bottle(mb, x, y, z, mi_body, mi_cap, h=0.2, r=0.028, cap=0.03):
    mb.lathe(x, y, z, [(0, 0), (r * 0.9, 0), (r, 0.01), (r, h * 0.7), (r * 0.55, h * 0.8), (r * 0.5, h), (0, h)], seg=16, mi=mi_body)
    mb.cylinder(x, y, z + h, z + h + cap, r * 0.52, seg=16, mi=mi_cap)


def hanger_garment(mb, x, y, z_rail, mi_cloth, mi_wire, along='Y', w=0.44, h=0.72, seed=0):
    """Wire hanger (hook + shoulders) with an rcbox torso hanging from it."""
    rng = random.Random(seed)
    hk = 0.045
    if along == 'Y':
        mb.path_tube([(x, y, z_rail + 0.012), (x + 0.01, y, z_rail + 0.03), (x - 0.006, y, z_rail + 0.032), (x - 0.012, y, z_rail + 0.01), (x, y, z_rail - hk)], 0.0025, seg=6, mi=mi_wire)
        mb.path_tube([(x, y - w / 2 + 0.02, z_rail - hk - 0.11), (x, y, z_rail - hk), (x, y + w / 2 - 0.02, z_rail - hk - 0.11)], 0.0025, seg=6, mi=mi_wire)
        mb.rcbox(x, y, z_rail - hk - 0.10 - h / 2, 0.07 + rng.uniform(0, 0.03), w, h, r=0.025, mi=mi_cloth, rot=rng.uniform(-0.06, 0.06))
    else:
        mb.path_tube([(x, y, z_rail + 0.012), (x, y + 0.01, z_rail + 0.03), (x, y - 0.006, z_rail + 0.032), (x, y - 0.012, z_rail + 0.01), (x, y, z_rail - hk)], 0.0025, seg=6, mi=mi_wire)
        mb.path_tube([(x - w / 2 + 0.02, y, z_rail - hk - 0.11), (x, y, z_rail - hk), (x + w / 2 - 0.02, y, z_rail - hk - 0.11)], 0.0025, seg=6, mi=mi_wire)
        mb.rcbox(x, y, z_rail - hk - 0.10 - h / 2, w, 0.07 + rng.uniform(0, 0.03), h, r=0.025, mi=mi_cloth, rot=rng.uniform(-0.06, 0.06))


def shoe_pair(mb, x, y, z, mi, rot=0.0, l=0.28):
    for k in (-1, 1):
        px, py = rot2(x + k * 0.055, y, x, y, rot)
        mb.rcbox(px, py, z + 0.035, 0.09, l, 0.07, r=0.03, mi=mi, rot=rot, puff=0.2)
        px, py = rot2(x + k * 0.055, y + l * 0.15, x, y, rot)
        mb.rcbox(px, py, z + 0.075, 0.08, l * 0.5, 0.05, r=0.024, mi=mi, rot=rot)


def sweater_stack(mb, x, y, z, mis, w=0.34, d=0.28, n=3, rot=0.0):
    for i in range(n):
        mb.rcbox(x + (i % 2) * 0.01, y - (i % 2) * 0.008, z + 0.03 + i * 0.06, w - i * 0.01, d, 0.06, r=0.02, mi=mis[i % len(mis)], rot=rot, puff=0.3)


def laptop(mb, x, y, z, mi_body, mi_screen, rot=0.0):
    mb.rcbox(x, y, z + 0.008, 0.32, 0.22, 0.016, r=0.006, mi=mi_body, rot=rot)
    px, py = rot2(x, y + 0.105, x, y, rot)
    # lid tilted back ~100 deg
    c, s_ = math.cos(rot), math.sin(rot)
    top = (px - s_ * 0.06, py + c * 0.06, z + 0.21)
    mb.hexa([(px - c * 0.16, py - s_ * 0.16, z + 0.016), (px + c * 0.16, py + s_ * 0.16, z + 0.016), (px + c * 0.16 + s_ * 0.004, py + s_ * 0.16 - c * 0.004, z + 0.016), (px - c * 0.16 + s_ * 0.004, py - s_ * 0.16 - c * 0.004, z + 0.016),
             (top[0] - c * 0.16, top[1] - s_ * 0.16, top[2]), (top[0] + c * 0.16, top[1] + s_ * 0.16, top[2]), (top[0] + c * 0.16 + s_ * 0.004, top[1] + s_ * 0.16 - c * 0.004, top[2]), (top[0] - c * 0.16 + s_ * 0.004, top[1] - s_ * 0.16 - c * 0.004, top[2])], mi_body)
    mb.hexa([(px - c * 0.15 - s_ * 0.001, py - s_ * 0.15 + c * 0.001, z + 0.03), (px + c * 0.15 - s_ * 0.001, py + s_ * 0.15 + c * 0.001, z + 0.03), (px + c * 0.15, py + s_ * 0.15, z + 0.03), (px - c * 0.15, py - s_ * 0.15, z + 0.03),
             (top[0] - c * 0.15 - s_ * 0.001, top[1] - s_ * 0.15 + c * 0.001, top[2] - 0.012), (top[0] + c * 0.15 - s_ * 0.001, top[1] + s_ * 0.15 + c * 0.001, top[2] - 0.012), (top[0] + c * 0.15, top[1] + s_ * 0.15, top[2] - 0.012), (top[0] - c * 0.15, top[1] - s_ * 0.15, top[2] - 0.012)], mi_screen)


def desk_lamp(mb, x, y, z, mi_metal, mi_bulb, rot=0.0):
    mb.cylinder(x, y, z, z + 0.015, 0.07, seg=20, mi=mi_metal)
    px, py = rot2(x + 0.12, y, x, y, rot)
    qx, qy = rot2(x + 0.28, y, x, y, rot)
    mb.path_tube([(x, y, z + 0.015), (x, y, z + 0.32), (px, py, z + 0.45), (qx, qy, z + 0.40)], 0.006, seg=8, mi=mi_metal)
    mb.lathe(qx, qy, z + 0.33, [(0, 0.07), (0.05, 0.065), (0.07, 0.03), (0.065, 0), (0, 0)], seg=20, mi=mi_metal)
    mb.sphere((qx, qy, z + 0.35), 0.02, seg=10, rings=6, mi=mi_bulb)


def dumbbell(mb, x, y, z, mi, l=0.32, r=0.045, rot=0.0):
    a = rot2(x - l / 2, y, x, y, rot); b = rot2(x + l / 2, y, x, y, rot)
    mb.tube((a[0], a[1], z + r), (b[0], b[1], z + r), 0.014, 0.014, seg=10, mi=mi)
    for (px, py) in (rot2(x - l / 2 + 0.04, y, x, y, rot), rot2(x + l / 2 - 0.04, y, x, y, rot)):
        d0 = rot2(px - 0.035, py, px, py, rot); d1 = rot2(px + 0.035, py, px, py, rot)
        mb.tube((d0[0], d0[1], z + r), (d1[0], d1[1], z + r), r, r, seg=16, mi=mi)


def torus(mb, cx, cy, cz, R, r, mi, seg=28, rings=10, axis='X'):
    """Torus in the plane normal to `axis` (a flywheel rim when axis='X')."""
    secs = []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        sec = []
        for j in range(rings):
            b = 2 * math.pi * j / rings
            rr = R + r * math.cos(b)
            if axis == 'X':
                sec.append((cx + r * math.sin(b), cy + rr * math.cos(a), cz + rr * math.sin(a)))
            else:
                sec.append((cx + rr * math.cos(a), cy + rr * math.sin(a), cz + r * math.sin(b)))
        secs.append(sec)
    mb.sweep(secs, mi, close=True, caps=False)


def _salt_material(MT, name):
    """Backlit Himalayan-salt bricks (photo 20): 200 x 100 mm blocks with thin dark joints, mottled pink / orange /
    apricot, glowing from behind."""
    m, nt, b = MT._new(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(sep.inputs["Vector"], tc.outputs["Object"])
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(comb.inputs["X"], sep.outputs["X"]); nt.links.new(comb.inputs["Y"], sep.outputs["Z"])
    brick = nt.nodes.new("ShaderNodeTexBrick")
    brick.offset = 0.5; brick.offset_frequency = 2
    brick.inputs["Scale"].default_value = 1.0
    brick.inputs["Mortar Size"].default_value = 0.004
    brick.inputs["Mortar Smooth"].default_value = 0.3
    brick.inputs["Brick Width"].default_value = 0.20
    brick.inputs["Row Height"].default_value = 0.10
    brick.inputs["Color1"].default_value = (1.0, 1.0, 1.0, 1)
    brick.inputs["Color2"].default_value = (0.82, 0.72, 0.68, 1)
    brick.inputs["Mortar"].default_value = (0.25, 0.10, 0.06, 1)
    nt.links.new(brick.inputs["Vector"], comb.outputs["Vector"])
    vec = MT._coords(nt)
    n1 = MT._noise(nt, vec, scale=6.0, detail=4.0, rough=0.6)
    n2 = MT._noise(nt, vec, scale=40.0, detail=2.0)
    col = MT._ramp(nt, n1, [(0.25, (0.90, 0.36, 0.20, 1)), (0.5, (1.0, 0.58, 0.32, 1)), (0.75, (1.0, 0.76, 0.52, 1))])
    col = MT._mixrgb(nt, MT._math(nt, 'MULTIPLY', n2, 0.3), col, (0.8, 0.7, 0.65, 1), 'MULTIPLY')
    col = MT._mixrgb(nt, 1.0, col, brick.outputs["Color"], 'MULTIPLY')
    nt.links.new(b.inputs["Base Color"], col)
    nt.links.new(b.inputs["Emission Color"], col)
    MT._set(b, "Emission Strength", 2.6); MT._set(b, "Roughness", 0.35); MT._set(b, "Coat Weight", 0.3)
    MT._bump(nt, b, MT._math(nt, 'ADD', MT._math(nt, 'MULTIPLY', brick.outputs["Fac"], 1.0), MT._math(nt, 'MULTIPLY', n2, 0.3)), 0.4, 0.01)
    return m


def rug_slab(name, x0, x1, y0, y1, z, mat):
    r = MB(); r.rbox(x0, x1, y0, y1, z, z + 0.012, r=0.006, mi=0)
    return r.build(name, mat, smooth=True)


# ------------------------------------------------------------------ lighting (photos 16-20: black recessed slots, coves)
def slot_x(mb, x0, x1, y, z, mi_slot=0, mi_lens=1, heads=3):
    """Recessed 40 mm black linear slot in the ceiling (underside at z) with `heads` flush lens discs.
    Returns the head positions so real spot lights can be placed under them."""
    mb.box(x0, x1, y - 0.02, y + 0.02, z - 0.002, z + 0.035, mi_slot)
    pts = []
    for i in range(heads):
        x = x0 + (x1 - x0) * (i + 0.5) / heads
        mb.cylinder(x, y, z - 0.001, z + 0.004, 0.015, seg=10, mi=mi_lens)
        pts.append((x, y))
    return pts


def slot_y(mb, x, y0, y1, z, mi_slot=0, mi_lens=1, heads=3):
    mb.box(x - 0.02, x + 0.02, y0, y1, z - 0.002, z + 0.035, mi_slot)
    pts = []
    for i in range(heads):
        y = y0 + (y1 - y0) * (i + 0.5) / heads
        mb.cylinder(x, y, z - 0.001, z + 0.004, 0.015, seg=10, mi=mi_lens)
        pts.append((x, y))
    return pts


def head_spots(prefix, pts, z, energy=22.0, spot=50.0, blend=0.55, color=WARM, targets=None, size=0.03):
    """One narrow SPOT per slot head (pools of light, like the photos); `targets` = optional aim points per head."""
    for i, (x, y) in enumerate(pts):
        tgt = None if not targets else targets[i % len(targets)]
        add_light(f"{prefix}_{i}", 'SPOT', (x, y, z - 0.03), energy, color, size=size, spot=math.radians(spot), blend=blend, target=tgt)


def cove_x(mb, x0, x1, y, z, mi, w=0.03, face=1):
    """Thin emissive LED line along X at (y, z), `w` deep toward +face y."""
    mb.box(x0, x1, min(y, y + face * w), max(y, y + face * w), z, z + 0.008, mi)


def cove_y(mb, y0, y1, x, z, mi, w=0.03, face=1):
    mb.box(min(x, x + face * w), max(x, x + face * w), y0, y1, z, z + 0.008, mi)


def ceiling_cove(mb, room, z, mi_step, mi_led, band=0.35, drop=0.10, inset=0.0):
    """Perimeter ceiling tray: a dropped band around the room with a continuous LED line on its inner edge shining
    up onto the recessed centre (the cove wash in photos 17/19/20)."""
    x0, x1, y0, y1 = room
    x0 += inset; x1 -= inset; y0 += inset; y1 -= inset
    mb.box(x0, x1, y0, y0 + band, z - drop, z, mi_step); mb.box(x0, x1, y1 - band, y1, z - drop, z, mi_step)
    mb.box(x0, x0 + band, y0, y1, z - drop, z, mi_step); mb.box(x1 - band, x1, y0, y1, z - drop, z, mi_step)
    zl = z - drop + 0.012
    cove_x(mb, x0 + band, x1 - band, y0 + band - 0.03, zl, mi_led, w=0.03, face=1)
    cove_x(mb, x0 + band, x1 - band, y1 - band, zl, mi_led, w=0.03, face=1)
    cove_y(mb, y0 + band, y1 - band, x0 + band - 0.03, zl, mi_led, w=0.03, face=1)
    cove_y(mb, y0 + band, y1 - band, x1 - band, zl, mi_led, w=0.03, face=1)


def wash_light(name, p0, p1, z, energy, color=WARM_SOFT, width=0.06, up=False):
    """Slim area light along a line (LED strip substitute) - upward for coves, downward for shelf strips."""
    L = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    ld = bpy.data.lights.new(name, 'AREA')
    ld.shape = 'RECTANGLE'; ld.size = L; ld.size_y = width; ld.energy = energy; ld.color = color
    ld.spread = math.radians(160)
    ob = bpy.data.objects.new(name, ld)
    ob.location = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, z)
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    ob.rotation_euler = (math.pi if up else 0.0, 0.0, ang)
    collection('Lights').objects.link(ob)
    return ob


def onyx_joints(mb, room, faces, mi, z0=Z0, z1=ZC, pitch=1.2, t=0.032):
    """3 mm dark mitre lines every `pitch` m on the onyx cladding (book-matched slab joints), plus one horizontal at 1.2 m."""
    x0, x1, y0, y1 = room
    zc = z1 - CEIL_T
    j = 0.0015
    if 'W' in faces or 'E' in faces:
        for f, xx in (('W', x0 + t), ('E', x1 - t)):
            if f not in faces:
                continue
            yy = y0 + pitch
            while yy < y1 - 0.1:
                mb.box(xx - 0.001, xx + 0.001, yy - j, yy + j, z0 + 0.02, zc, mi); yy += pitch
            mb.box(xx - 0.001, xx + 0.001, y0, y1, z0 + 1.2 - j, z0 + 1.2 + j, mi)
    for f, yy in (('S', y0 + t), ('N', y1 - t)):
        if f not in faces:
            continue
        xx = x0 + pitch
        while xx < x1 - 0.1:
            mb.box(xx - j, xx + j, yy - 0.001, yy + 0.001, z0 + 0.02, zc, mi); xx += pitch
        mb.box(x0, x1, yy - 0.001, yy + 0.001, z0 + 1.2 - j, z0 + 1.2 + j, mi)


# ================================================================== structure shared by the suite
def build_structure(M):
    w = MB()
    white = 0
    # master south wall (kitchen is y<17.6) and office / vestibule south walls (dining is y<17.8)
    w.box(MX0 + WT, -4.6, 17.65, 17.8, Z0, ZC, white)
    part_y(w, 17.875, -4.6, 3.4, Z0, ZC, holes=[(-1.0, 0.8, Z0, Z0 + 2.4)], mi=white)                 # vestibule S (double door)
    part_y(w, 17.875, 3.4, 7.05, Z0, ZC, holes=[(4.6, 5.6, Z0, Z0 + 2.3)], mi=white)                  # office S (door)
    part_y(w, 19.6, -4.6, 3.4, Z0, ZC, holes=[(-3.1, -2.1, Z0, Z0 + 2.3), (0.9, 1.9, Z0, Z0 + 2.3)], mi=white)   # vestibule N
    part_x(w, -4.6, 17.8, 23.55, Z0, ZC, holes=[(18.3, 19.3, Z0, Z0 + 2.3)], mi=white)                # master | vestibule+bath
    part_x(w, -0.6, 19.6, 23.55, Z0, ZC, holes=[(21.3, 22.3, Z0, Z0 + 2.4)], mi=white)                # bath | closet (portal)
    part_x(w, 3.4, 17.8, 23.55, Z0, ZC, holes=[(18.3, 19.3, Z0, Z0 + 2.3)], mi=white)                 # closet+vestibule | office
    w.wall('Y', 18.25, 23.55, 14.2, 14.6, Z0, ZC, holes=[(22.5, 23.4, Z0, Z0 + 2.3)], mi=white)       # gym | guest2
    w.wall('Y', 18.25, 23.55, 18.4, 18.6, Z0, ZC, holes=[(18.5, 19.4, Z0, Z0 + 2.3)], mi=white)       # guest2 | guest
    # fill above the dropped ceilings so nothing peeks through from the upper floor slab gap
    w.build("Suite_Partitions", [M['white_int']])

    # doors (oak leaves + frames)
    d = MB()
    oak, frm = 0, 1
    for (x0, x1, y, z1) in ((-1.0, -0.1, 17.875, Z0 + 2.4), (-0.1, 0.8, 17.875, Z0 + 2.4), (4.6, 5.6, 17.875, Z0 + 2.3),
                            (-3.1, -2.1, 19.6, Z0 + 2.3), (0.9, 1.9, 19.6, Z0 + 2.3)):
        door_leaf(d, x0 + 0.01, x1 - 0.01, y, Z0 + 0.02, z1 - 0.01, oak, along='X')
        door_frame(d, x0, x1, y, Z0, z1, frm, w=0.05, d=PT + 0.02, along='X')
    for (y0, y1, x, z1) in ((18.3, 19.3, -4.6, Z0 + 2.3), (18.3, 19.3, 3.4, Z0 + 2.3), (22.5, 23.4, 14.4, Z0 + 2.3), (18.5, 19.4, 18.5, Z0 + 2.3)):
        door_leaf(d, y0 + 0.01, y1 - 0.01, x, Z0 + 0.02, z1 - 0.01, oak, along='Y')
        door_frame(d, y0, y1, x, Z0, z1, frm, w=0.05, d=PT + 0.02, along='Y')
    # bath -> closet portal lined in oak
    d.box(-0.68, -0.52, 21.3, 21.35, Z0, Z0 + 2.4, oak); d.box(-0.68, -0.52, 22.25, 22.3, Z0, Z0 + 2.4, oak)
    d.box(-0.68, -0.52, 21.3, 22.3, Z0 + 2.35, Z0 + 2.4, oak)
    d.build("Suite_Doors", [M['oak_pale'], M['oak']])
    hw = MB()
    for (x0, x1, y, z1, side) in ((-1.0, -0.1, 17.875, Z0 + 2.4, -1), (-0.1, 0.8, 17.875, Z0 + 2.4, 1), (4.6, 5.6, 17.875, Z0 + 2.3, 1),
                                  (-3.1, -2.1, 19.6, Z0 + 2.3, 1), (0.9, 1.9, 19.6, Z0 + 2.3, 1)):
        door_hardware(hw, x0, x1, y, z1, 0, along='X', side=side)
    for (y0, y1, x, z1) in ((18.3, 19.3, -4.6, Z0 + 2.3), (18.3, 19.3, 3.4, Z0 + 2.3), (22.5, 23.4, 14.4, Z0 + 2.3), (18.5, 19.4, 18.5, Z0 + 2.3)):
        door_hardware(hw, y0, y1, x, z1, 0, along='Y', side=1)
    hw.build("Suite_DoorHardware", [M['black_metal'], M['white_gloss']])

    # vestibule finishes
    v = MB()
    floor_ceiling(v, VEST, 0, 1)
    v.build("Vestibule_Shell", [M['oak_floor'], M['ceiling']])
    dl = MB(); downlights(dl, [(-3.0, 18.75), (-1.0, 18.75), (1.0, 18.75), (2.6, 18.75)], ZC - CEIL_T)
    dl.build("Vestibule_Downlights", [M['emit_down'], M['black']])
    vd = MB(); room_details(vd, VEST, mi_gap=0, mi_speaker=1, mi_diffuser=2, speakers=((0.0, 18.75),), diffusers=((-2.0, 19.2, 'X'),))
    vd.build("Vestibule_Details", [M['black'], M['white_gloss'], M['black_metal']])
    room_light("L_Vestibule", (*VEST, Z0, ZC), energy=12, z_off=0.3)


# ================================================================== master bedroom (photo 17)
def _master_materials(MT):
    """Local finishes that give photo 17 its contrast: ivory rug with soft grey abstract shapes, charcoal / mocha
    velvet, grey-striped lumbar linen, a chunky cream knit, a slightly glossier oak floor and a neutral cove LED."""
    L = {}
    L['cove'] = MT.new_mat("EmitCoveMaster", (1.0, 0.92, 0.80, 1), emit=(1.0, 0.88, 0.70, 1), emit_str=7.0)
    L['charcoal'] = MT.fabric("VelvetCharcoal", (0.13, 0.115, 0.105, 1), rough=0.65, sheen=1.0, weave=120, bump=0.1, sheen_tint=(0.7, 0.62, 0.55, 1))
    L['mocha'] = MT.fabric("VelvetMocha", (0.21, 0.125, 0.08, 1), rough=0.6, sheen=0.5, weave=120, bump=0.1, sheen_tint=(0.9, 0.7, 0.5, 1))
    L['knit'] = MT.fabric("KnitOat", (0.80, 0.73, 0.61, 1), rough=0.95, sheen=0.5, weave=22, bump=0.7)
    L['oak'] = MT.wood_planks("OakFloorMaster", light=(0.80, 0.70, 0.55, 1), dark=(0.63, 0.51, 0.37, 1), plank=(2.6, 0.26), rough=0.26, coat=0.35)
    # striped lumbar: 22 mm grey / white bands along the pillow's long axis (world Y once rotated)
    m, nt, b = MT._new("LinenStripe")
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.wave_type = 'BANDS'; wave.bands_direction = 'Y'; wave.wave_profile = 'SAW'
    wave.inputs["Scale"].default_value = 22.0; wave.inputs["Distortion"].default_value = 0.4; wave.inputs["Detail"].default_value = 1.0
    nt.links.new(wave.inputs["Vector"], MT._coords(nt))
    band = MT._math(nt, 'GREATER_THAN', wave.outputs["Fac"], 0.5)
    col = MT._mixrgb(nt, band, (0.90, 0.88, 0.84, 1), (0.36, 0.34, 0.33, 1))
    n = MT._noise(nt, MT._coords(nt), scale=90.0, detail=2.0)
    nt.links.new(b.inputs["Base Color"], col)
    MT._set(b, "Roughness", 0.92); MT._set(b, "Specular IOR Level", 0.2); MT._set(b, "Sheen Weight", 0.6)
    MT._bump(nt, b, n, 0.25, 0.003)
    L['stripe'] = m
    # rug: ivory ground, large soft-edged grey shapes (warped low-frequency noise), fine looped-pile bump
    m, nt, b = MT._new("RugMasterIvory")
    vec = MT._coords(nt)
    shapes = MT._noise(nt, vec, scale=0.55, detail=2.0, rough=0.45, distortion=1.4)
    fac = MT._stretch(nt, shapes, 0.485, 0.545)
    pile = MT._noise(nt, vec, scale=70.0, detail=3.0)
    col = MT._mixrgb(nt, fac, (0.85, 0.84, 0.81, 1), (0.47, 0.46, 0.44, 1))
    col = MT._mixrgb(nt, MT._math(nt, 'MULTIPLY', pile, 0.18), col, (0.8, 0.8, 0.8, 1), 'MULTIPLY')
    nt.links.new(b.inputs["Base Color"], col)
    MT._set(b, "Roughness", 1.0); MT._set(b, "Specular IOR Level", 0.1); MT._set(b, "Sheen Weight", 0.9)
    MT._bump(nt, b, pile, 0.6, 0.012)
    L['rug'] = m
    return L


def build_master(M):
    from archviz import materials as MT
    LM = _master_materials(MT)
    x0, x1, y0, y1 = MASTER
    s = MB()
    floor_ceiling(s, MASTER, 0, 1)
    finish(s, MASTER, 'WS', 2)                                            # W exterior wall + S wall finish (N = glass, E = fireplace wall)
    # perimeter ceiling tray: dropped band with a warm cove on its inner edge
    band = 0.55
    s.box(x0, x1, y0, y0 + band, ZC - 0.2, ZC - CEIL_T, 1); s.box(x0, x1, y1 - band, y1, ZC - 0.2, ZC - CEIL_T, 1)
    s.box(x0, x0 + band, y0, y1, ZC - 0.2, ZC - CEIL_T, 1); s.box(x1 - band, x1, y0, y1, ZC - 0.2, ZC - CEIL_T, 1)
    s.build("Master_Shell", [LM['oak'], M['ceiling'], M['white_int']])
    md = MB()
    room_details(md, MASTER, z1=ZC - 0.15, mi_gap=0, mi_speaker=1, mi_diffuser=2, faces='WSE',
                 speakers=((-9.5, 20.5), (-7.0, 20.5)), diffusers=((-8.5, 18.6, 'X'), (-8.5, 22.7, 'X')))
    md.build("Master_Details", [M['black'], M['white_gloss'], M['black_metal']])
    # LED line on the inner edge of the tray (up-wash onto the recessed centre) + soft up-lights behind it
    c = MB()
    zl = ZC - 0.2 + 0.006
    cove_x(c, x0 + band, x1 - band, y0 + band - 0.03, zl, 0, w=0.03); cove_x(c, x0 + band, x1 - band, y1 - band, zl, 0, w=0.03)
    cove_y(c, y0 + band, y1 - band, x0 + band - 0.03, zl, 0, w=0.03); cove_y(c, y0 + band, y1 - band, x1 - band, zl, 0, w=0.03)
    c.build("Master_Cove", LM['cove'])
    wash_light("L_MasterCoveS", (x0 + band, y0 + band), (x1 - band, y0 + band), zl + 0.03, 8, color=(1.0, 0.88, 0.72), up=True)
    wash_light("L_MasterCoveN", (x0 + band, y1 - band), (x1 - band, y1 - band), zl + 0.03, 8, color=(1.0, 0.88, 0.72), up=True)
    # recessed black slots with narrow spot heads (photo 17: two rows of slots either side of the bed axis)
    tl = MB()
    zc = ZC - CEIL_T
    heads = slot_x(tl, -11.4, -8.9, 19.3, zc, 0, 1, heads=3) + slot_x(tl, -8.3, -5.8, 19.3, zc, 0, 1, heads=3)
    heads += slot_x(tl, -11.4, -8.9, 22.2, zc, 0, 1, heads=3) + slot_x(tl, -8.3, -5.8, 22.2, zc, 0, 1, heads=3)
    tl.build("Master_Slots", [M['black'], M['emit_white']])
    aims = [(-12.0, 19.6, Z0 + 1.2), (-10.6, 19.6, Z0 + 0.6), (-9.2, 19.2, Z0 + 0.4), (-7.5, 19.0, Z0 + 0.4), (-6.2, 19.4, Z0 + 0.5), (-4.9, 20.2, Z0 + 1.4),
            (-12.0, 21.6, Z0 + 1.2), (-10.6, 21.4, Z0 + 0.6), (-9.2, 22.4, Z0 + 0.4), (-7.5, 22.6, Z0 + 0.4), (-6.2, 22.4, Z0 + 0.5), (-4.9, 22.1, Z0 + 0.7)]
    head_spots("L_MasterHead", heads, zc, energy=30, spot=44, blend=0.55, color=(1.0, 0.90, 0.78), targets=aims)

    # headboard: tall cream boucle upholstered panel spanning nightstand to nightstand (photo 17), floating oak
    # nightstands with two drawers each, a slim oak ledge behind the panel
    hb = MB()
    hb.rbox(x0 + 0.03, x0 + 0.11, 18.55, 22.45, Z0 + 0.20, Z0 + 1.32, r=0.03, mi=2, puff=0.15)             # upholstered panel
    hb.box(x0 + 0.02, x0 + 0.04, 18.5, 22.5, Z0 + 0.02, Z0 + 1.36, 0)                                        # oak backing strip
    for ny in (19.05, 21.95):
        nightstand(hb, x0 + 0.37, ny, Z0, w=0.62, d=0.72, h=0.56, mi=0, floating=True)
        hb.box(x0 + 0.06, x0 + 0.685, ny - 0.36, ny + 0.36, Z0 + 0.44 - 0.0015, Z0 + 0.44 + 0.0015, 1)     # drawer reveal
        hb.box(x0 + 0.678, x0 + 0.688, ny - 0.36, ny + 0.36, Z0 + 0.32, Z0 + 0.323, 1)                     # finger pull line
        hb.box(x0 + 0.678, x0 + 0.688, ny - 0.36, ny + 0.36, Z0 + 0.445, Z0 + 0.448, 1)
    hb.build("Master_Headboard", [M['oak_pale'], M['black'], M['fabric']])
    nd = MB()
    carafe(nd, x0 + 0.22, 21.72, Z0 + 0.56, 0)
    books(nd, x0 + 0.44, 19.25, Z0 + 0.56, n=2, mi=1, w=0.2, d=0.15, rot=0.2)
    nd.build("Master_NightstandDecor", [M['glass'], M['book']], smooth=True, auto_smooth=True)
    b = MB()
    # white linen bed with the duvet folded back at the foot (bed() throw = linen), then the photo's stack:
    # two white euros, two charcoal velvet squares, two grey-striped lumbars, one sand bolster in front
    bed(b, x0 + 1.25, 20.5, rot=math.pi / 2, z=Z0 + 0.02, w=1.9, l=2.15, mi_frame=0, mi_linen=1, mi_pillow=1, mi_throw=1, head_h=0.90)
    cushion(b, x0 + 0.66, 19.98, Z0 + 0.62, w=0.48, d=0.48, t=0.15, mi=4, rot=-math.pi / 2 + 0.06, upright=True, tilt=0.6)
    cushion(b, x0 + 0.66, 21.02, Z0 + 0.62, w=0.48, d=0.48, t=0.15, mi=4, rot=-math.pi / 2 - 0.06, upright=True, tilt=0.6)
    cushion(b, x0 + 0.84, 20.12, Z0 + 0.62, w=0.40, d=0.28, t=0.12, mi=2, rot=-math.pi / 2 + 0.04, upright=True, tilt=0.7)
    cushion(b, x0 + 0.84, 20.88, Z0 + 0.62, w=0.40, d=0.28, t=0.12, mi=2, rot=-math.pi / 2 - 0.04, upright=True, tilt=0.7)
    b.pillow(x0 + 1.0, 20.5, Z0 + 0.66, w=0.52, d=0.26, t=0.13, mi=6, rot=math.pi / 2, pitch=0.9)          # sand bolster in front
    # chunky cream knit thrown across the foot corner, one end hanging over the bed's end
    b.drape(x0 + 1.70, x0 + 2.27, 19.68, 20.90, Z0 + 0.635, t=0.035, mi=5, sag=0.05, folds=4, seed=8)
    b.drape(x0 + 1.86, x0 + 2.27, 19.76, 20.52, Z0 + 0.668, t=0.035, mi=5, sag=0.04, folds=3, seed=11)    # folded-back second layer
    # mocha velvet bench at the foot (photo 17): a clean dark block, cushion piped edge
    b.rbox(x0 + 2.48, x0 + 2.98, 19.75, 21.25, Z0 + 0.25, Z0 + 0.48, r=0.06, mi=3, puff=0.3)
    b.build("Master_Bed", [M['fabric_white'], M['linen_white'], LM['stripe'], LM['mocha'], LM['charcoal'], LM['knit'], M['fabric_sand']], smooth=True, subsurf=1)
    lg = MB()
    for ly in (19.9, 21.1):
        lg.box(x0 + 2.58, x0 + 2.88, ly - 0.06, ly + 0.06, Z0, Z0 + 0.25, 0)
    lg.build("Master_BenchLegs", M['walnut'])
    # sculptural white ceramic lamps (a twisted ribbon of clay on a disc) with white linen drum shades
    lm = MB()
    for ny in (19.05, 21.95):
        lx = x0 + 0.37
        lm.lathe(lx, ny, Z0 + 0.56, [(0, 0), (0.12, 0), (0.125, 0.02), (0.11, 0.025), (0, 0.025)], seg=24, mi=0)
        pts_ = [(lx + 0.06 * math.cos(t * 3.1), ny + 0.06 * math.sin(t * 3.1), Z0 + 0.585 + 0.30 * t) for t in [k / 8 for k in range(9)]]
        lm.path_tube(pts_, 0.045, seg=12, mi=0)                                                              # coiled ribbon body
        lm.lathe(lx, ny, Z0 + 0.86, [(0, 0), (0.035, 0), (0.035, 0.06), (0.012, 0.06), (0.012, 0.12), (0, 0.12)], seg=12, mi=3)
        lm.lathe(lx, ny, Z0 + 0.92, [(0.20, 0), (0.205, 0), (0.205, 0.25), (0.20, 0.25)], seg=28, mi=1)      # drum shade
        lm.sphere((lx, ny, Z0 + 1.03), 0.028, seg=12, rings=8, mi=2)
        lm.path_tube([(lx + 0.10, ny, Z0 + 0.563), (lx - 0.25, ny + 0.25, Z0 + 0.56), (x0 + 0.05, ny + 0.32, Z0 + 0.30)], 0.003, seg=6, mi=3)
        add_light(f"L_MasterLamp_{ny:.0f}", 'POINT', (lx, ny, Z0 + 1.04), 16, (1.0, 0.78, 0.55), size=0.06)
    lm.build("Master_Lamps", [M['ceramic'], M['lampshade'], M['emit_warm'], M['black']], smooth=True, auto_smooth=True)
    # mirrors above the headboard (photo 17): a tall narrow one over each nightstand + an asymmetric organic one
    # centred above the bed, 6 mm slabs on a dark 15 mm standoff
    mr = MB()
    for ny in (19.05, 21.95):
        mr.box(x0 + 0.075, x0 + 0.09, ny - 0.16, ny + 0.16, Z0 + 1.45, Z0 + 2.65, 1)
        mr.box(x0 + 0.09, x0 + 0.096, ny - 0.15, ny + 0.15, Z0 + 1.46, Z0 + 2.64, 0)
    mr.blob((x0 + 0.075, 20.5, Z0 + 2.05), 1.0, seg=32, rings=12, jitter=0.25, seed=7, mi=1, squash=0.46, rx=0.012, ry=0.62)
    mr.blob((x0 + 0.093, 20.5, Z0 + 2.05), 1.0, seg=32, rings=12, jitter=0.25, seed=7, mi=0, squash=0.45, rx=0.006, ry=0.61)
    mr.build("Master_Mirrors", [M['mirror'], M['black']], smooth=True, auto_smooth=True)
    # rug (polish adds fibres to Rug_* objects)
    rug_slab("Rug_Master", x0 + 1.0, x0 + 5.2, 18.5, 22.7, Z0 + 0.02, LM['rug'])
    # fireplace wall (east): grey travertine cladding, fire slot, lit oak shelving beside it
    fw = MB()
    fw.wall('Y', 20.6, y1, x1 - 0.28, x1, Z0, ZC - CEIL_T, holes=[(21.4, 22.9, Z0 + 0.4, Z0 + 0.75)], mi=0)
    fw.box(x1 - 0.28, x1 - 0.02, 21.4, 22.9, Z0 + 0.4, Z0 + 0.42, 1)                          # slot floor (black)
    fw.box(x1 - 0.04, x1 - 0.02, 21.4, 22.9, Z0 + 0.42, Z0 + 0.75, 1)                         # slot back
    fw.box(x1 - 0.28, x1 - 0.26, 21.36, 21.4, Z0 + 0.36, Z0 + 0.79, 1); fw.box(x1 - 0.28, x1 - 0.26, 22.9, 22.94, Z0 + 0.36, Z0 + 0.79, 1)   # black steel frame
    fw.box(x1 - 0.28, x1 - 0.26, 21.36, 22.94, Z0 + 0.36, Z0 + 0.40, 1); fw.box(x1 - 0.28, x1 - 0.26, 21.36, 22.94, Z0 + 0.75, Z0 + 0.79, 1)
    fw.box(x1 - 0.275, x1 - 0.265, 21.4, 22.9, Z0 + 0.42, Z0 + 0.75, 3)                       # glass front
    fw.box(x1 - 0.28, x1, 20.6, 20.66, Z0, ZC - CEIL_T, 0)
    for zz in (Z0 + 0.9, Z0 + 1.6, Z0 + 2.3):                                                   # oak shelves in the niche
        fw.box(x1 - 0.28, x1 - 0.02, y0 + 1.85, 20.6, zz, zz + 0.03, 2)
        fw.box(x1 - 0.06, x1 - 0.03, y0 + 1.85, 20.6, zz - 0.012, zz, 4)                        # LED under each shelf
    fw.box(x1 - 0.30, x1 - 0.28, y0 + 1.85, 20.6, Z0, ZC - CEIL_T, 2)                          # niche back (oak)
    fw.box(x1 - 0.28, x1, y0 + 1.80, y0 + 1.85, Z0, ZC - CEIL_T, 2)
    fw.build("Master_Fireplace", [M['trav_grey'], M['black'], M['oak_pale'], M['glass'], M['emit_bar']])
    pb = MB(); pebble_bed(pb, x1 - 0.24, x1 - 0.05, 21.42, 22.88, Z0 + 0.42, n=80, mi=0, seed=2)
    pb.build("Master_FirePebbles", M['pebble'], smooth=True)
    fl = MB(); flame_tongues(fl, x1 - 0.22, x1 - 0.07, 21.5, 22.8, Z0 + 0.44, n=32, seed=5, h=(0.1, 0.26))
    fl.build("Master_Flames", M['fire'], smooth=True)
    add_light("L_MasterFire", 'POINT', (x1 - 0.5, 22.15, Z0 + 0.7), 35, (1.0, 0.5, 0.18), size=0.4)
    # shelf decor: vases + books
    dv = MB()
    vase(dv, x1 - 0.15, 19.95, Z0 + 0.93, h=0.28, r=0.10, mi=0)
    vase(dv, x1 - 0.15, 20.35, Z0 + 1.63, h=0.2, r=0.08, mi=1, style='bowl')
    books(dv, x1 - 0.15, 20.2, Z0 + 2.33, n=3, mi=2, w=0.2, d=0.16)
    dv.build("Master_Decor", [M['ceramic'], M['ceramic_black'], M['book']], smooth=True)
    # a small potted plant on the far nightstand (photo 17: the one splash of green in the room)
    pl = MB()
    potted_plant(pl, x0 + 0.30, 22.25, Z0 + 0.56, pot_r=0.085, pot_h=0.11, h=0.46, mi_pot=0, mi_leaf=1, mi_stem=2, seed=3)
    pl.build("Master_Plant", [M['ceramic'], M['leaf_plant'], M['walnut']], smooth=True)
    # lights: a faint ambient only (the slots, cove, lamps and shelf LEDs do the work), plus a cool dusk fill coming
    # in through the north glass so the warm pools have something to play against
    room_light("L_Master", (*MASTER, Z0, ZC), energy=6, z_off=0.25)
    area_light("L_MasterDusk", ((x0 + x1) / 2, y1 - 0.10, Z0 + 1.7), (6.6, 2.9), 28, color=(0.70, 0.80, 1.0),
               target=((x0 + x1) / 2, y0 + 1.0, Z0 + 0.5))
    wash_light("L_MasterShelf", (x1 - 0.15, y0 + 1.9), (x1 - 0.15, 20.55), Z0 + 2.28, 6, color=(1.0, 0.8, 0.58), width=0.04)


# ================================================================== master bath (photo 18)
def build_bath(M):
    x0, x1, y0, y1 = BATH
    s = MB()
    s.box(x0, x1, y0, y1, Z0, Z0 + 0.02, 0)
    s.box(x0, x1, y0, y1, ZC - CEIL_T, ZC, 1)
    # onyx wall cladding (3 cm) on all faces, with the door / portal openings and a shower niche
    finish(s, BATH, 'WSEN', 2, t=0.03, holes={'S': [(-3.1, -2.1, Z0, Z0 + 2.3)], 'E': [(21.3, 22.3, Z0, Z0 + 2.4)],
                                             'W': [(22.25, 22.95, Z0 + 1.0, Z0 + 1.4)]})
    s.box(x0 - 0.10, x0, 22.25, 22.95, Z0 + 1.0, Z0 + 1.4, 2)                                    # niche back
    s.box(x0 - 0.10, x0 + 0.03, 22.25, 22.95, Z0 + 0.98, Z0 + 1.0, 2)                           # niche shelf
    # skylight well (1 x 1 m) over the tub
    kx0, kx1, ky0, ky1 = -3.2, -2.2, 21.2, 22.2
    s.box(kx0 - 0.05, kx0, ky0 - 0.05, ky1 + 0.05, ZC - CEIL_T, ZC + 0.35, 1); s.box(kx1, kx1 + 0.05, ky0 - 0.05, ky1 + 0.05, ZC - CEIL_T, ZC + 0.35, 1)
    s.box(kx0, kx1, ky0 - 0.05, ky0, ZC - CEIL_T, ZC + 0.35, 1); s.box(kx0, kx1, ky1, ky1 + 0.05, ZC - CEIL_T, ZC + 0.35, 1)
    # shower bench + curb
    s.box(x0, x0 + 0.65, 22.9, y1, Z0, Z0 + 0.45, 2)
    s.box(x0, -3.2, 21.8, 21.85, Z0, Z0 + 0.04, 2)
    sh = s.build("Bath_Shell", [M['onyx_bath_floor'], M['ceiling'], M['onyx_bath']])
    bj = MB()
    onyx_joints(bj, BATH, 'WSEN', 0)                                                             # book-matched slab joints
    room_details(bj, BATH, mi_gap=0, mi_speaker=1, mi_diffuser=2, skirt=False, speakers=((-1.6, 20.4),), diffusers=((-3.6, 20.2, 'X'),))
    bj.frame(kx0 - 0.006, kx1 + 0.006, ky0 - 0.006, ky1 + 0.006, ZC - CEIL_T - 0.006, ZC - CEIL_T, 0.006, mi=0, axis='Z')   # 6 mm skylight reveal
    bj.build("Bath_Joints", [M['black'], M['white_gloss'], M['black_metal']])
    # the ceiling box needs a hole for the skylight: overlay a white ceiling ring instead (simple: leave the box, cut visually with the well)
    g = MB()
    g.box(kx0, kx1, ky0, ky1, ZC + 0.30, ZC + 0.32, 0)                                           # skylight glass
    g.box(-3.2 - 0.004, -3.2 + 0.004, 21.85, y1 - 0.03, Z0 + 0.02, Z0 + 2.3, 0)                  # 8 mm shower screen
    g.box(-3.2 - 0.02, -3.2 + 0.02, 21.85, y1 - 0.03, Z0 + 0.02, Z0 + 0.03, 1)                   # shoe
    g.box(-3.2 - 0.02, -3.2 + 0.02, y1 - 0.06, y1 - 0.03, Z0 + 0.02, Z0 + 2.3, 1)                # wall channel
    g.box(-3.2 - 0.012, -3.2 + 0.012, 21.85, 21.9, Z0 + 2.28, Z0 + 2.31, 1)                      # top clamp
    g.tube((-3.2, 21.87, Z0 + 2.3), (-3.2, y1 - 0.05, Z0 + 2.3), 0.008, 0.008, seg=8, mi=1)      # stabiliser bar
    g.build("Bath_Glass", [M['glass'], M['chrome']])
    # linear drain grate in the shower floor + WC-side floor drain
    dr = MB()
    dr.box(x0 + 0.08, -3.3, 22.05, 22.11, Z0 + 0.02, Z0 + 0.024, 0)
    for k in range(18):
        xx = x0 + 0.1 + (0.5 - 0.1) * k / 18
        dr.box(xx, xx + 0.008, 22.06, 22.10, Z0 + 0.024, Z0 + 0.026, 1)
    dr.build("Bath_Drain", [M['chrome'], M['black']])
    # bath ceiling hole: rebuild ceiling as a plate with the hole (replace the solid ceiling of the shell)
    sh.data.polygons  # (kept simple; the well walls hide the slab edge)
    pl = MB(); pl.plate(x0, x1, y0, y1, ZC - CEIL_T - 0.001, ZC - CEIL_T, holes=[(kx0, kx1, ky0, ky1)])
    pl.build("Bath_CeilingPlate", M['ceiling'])
    # sea-green frosted WC door on the west wall (south of the shower)
    d = MB()
    d.box(x0 + 0.03, x0 + 0.05, 20.85, 21.75, Z0 + 0.02, Z0 + 2.3, 0)
    d.box(x0 + 0.05, x0 + 0.08, 21.6, 21.63, Z0 + 0.95, Z0 + 1.25, 1)                            # pull
    d.box(x0 + 0.03, x0 + 0.06, 20.82, 20.85, Z0, Z0 + 2.35, 1); d.box(x0 + 0.03, x0 + 0.06, 21.75, 21.78, Z0, Z0 + 2.35, 1)
    d.build("Bath_WCDoor", [M['glass_green'], M['chrome']])
    # tub + floor-standing filler
    tb = MB()
    w_, l_, h_ = 0.82, 1.75, 0.6
    prof = [(0, 0.02), (w_ * 0.35, 0.02), (w_ * 0.5, h_ * 0.35), (w_ * 0.5, h_ * 0.93), (w_ * 0.515, h_ * 0.985), (w_ * 0.5, h_ + 0.012),
            (w_ * 0.47, h_ + 0.012), (w_ * 0.45, h_ * 0.985), (w_ * 0.44, h_ * 0.9), (w_ * 0.42, h_ * 0.3), (0, h_ * 0.28)]       # 10 mm rolled rim
    tb.lathe(-2.5, 21.55, Z0 + 0.02, prof, seg=40, mi=0, ry=l_ / w_)
    tb.build("Bath_Tub", M['acrylic_white'], smooth=True, subsurf=1)
    fx = MB()
    # floor-standing filler with a gooseneck spout + hand shower on a cradle
    fx.cylinder(-2.5, 20.5, Z0 + 0.02, Z0 + 0.05, 0.05, seg=16, mi=0)
    fx.path_tube([(-2.5, 20.5, Z0 + 0.05), (-2.5, 20.5, Z0 + 0.92), (-2.5, 20.56, Z0 + 1.02), (-2.5, 20.7, Z0 + 1.04), (-2.5, 20.82, Z0 + 0.98)], 0.012, seg=10, mi=0)
    fx.cylinder(-2.5, 20.5, Z0 + 0.62, Z0 + 0.69, 0.018, seg=12, mi=0)                             # mixer knob
    fx.tube((-2.5, 20.5, Z0 + 0.66), (-2.44, 20.44, Z0 + 0.66), 0.006, 0.006, seg=8, mi=0)
    fx.path_tube([(-2.5, 20.5, Z0 + 0.55), (-2.4, 20.42, Z0 + 0.5), (-2.36, 20.42, Z0 + 0.75), (-2.38, 20.44, Z0 + 0.88)], 0.005, seg=8, mi=0)   # hose
    fx.cylinder(-2.38, 20.44, Z0 + 0.88, Z0 + 1.0, 0.013, seg=10, mi=0)                             # hand shower
    fx.lathe(-2.5, 21.55 + 0.7, Z0 + 0.02 + 0.28, [(0, 0), (0.028, 0), (0.028, 0.012), (0, 0.012)], seg=16, mi=0)   # overflow
    fx.lathe(-2.5, 21.55, Z0 + 0.03, [(0, 0), (0.03, 0), (0.03, 0.005), (0, 0.005)], seg=16, mi=0)           # drain
    # rain head with a spray-hole face + wand on a slide rail
    fx.lathe(-3.9, 22.7, Z0 + 2.28, [(0, 0), (0.16, 0), (0.165, 0.008), (0.16, 0.03), (0, 0.03)], seg=32, mi=0)
    fx.cylinder(-3.9, 22.7, Z0 + 2.31, ZC - CEIL_T, 0.012, seg=8, mi=0)
    rng_ = random.Random(3)
    for k in range(40):
        a_ = 2 * math.pi * k / 40 * 3.3; rr = 0.03 + 0.12 * ((k % 8) / 8)
        fx.cylinder(-3.9 + rr * math.cos(a_), 22.7 + rr * math.sin(a_), Z0 + 2.276, Z0 + 2.281, 0.004, seg=6, mi=1)
    fx.cylinder(x0 + 0.06, 22.3, Z0 + 1.0, Z0 + 1.9, 0.012, seg=8, mi=0)                          # wand rail
    fx.cylinder(x0 + 0.08, 22.3, Z0 + 1.6, Z0 + 1.8, 0.02, seg=8, mi=0)
    fx.path_tube([(x0 + 0.08, 22.3, Z0 + 1.6), (x0 + 0.12, 22.36, Z0 + 1.3), (x0 + 0.06, 22.4, Z0 + 1.05)], 0.005, seg=8, mi=0)   # hose
    fx.build("Bath_Chrome", [M['chrome'], M['black']], smooth=True, auto_smooth=True)
    # floating walnut vanity along the north wall, onyx top, two basins, halo mirrors
    vn = MB()
    vx0, vx1 = -3.05, x1 - 0.06
    cabinet_run(vn, vx0, vx1, y1 - 0.60, y1 - 0.04, Z0 + 0.62, Z0 + 0.92, mi=0, doors='X', n=4, gap=0.006, mi_gap=1)
    vn.box(vx0, vx1, y1 - 0.62, y1 - 0.03, Z0 + 0.92, Z0 + 0.96, 2)
    vn.build("Bath_Vanity", [M['walnut'], M['black'], M['onyx_bath']])
    bs = MB()
    for bx in (-2.35, -1.15):
        basin(bs, bx, y1 - 0.34, Z0 + 0.96, r=0.21, mi=0)
        bs.lathe(bx, y1 - 0.34, Z0 + 0.975, [(0, 0), (0.022, 0), (0.022, 0.004), (0.012, 0.004), (0, 0.004)], seg=16, mi=1)   # chrome drain
        bs.path_tube([(bx, y1 - 0.10, Z0 + 0.96), (bx, y1 - 0.10, Z0 + 1.18), (bx, y1 - 0.15, Z0 + 1.26), (bx, y1 - 0.25, Z0 + 1.25), (bx, y1 - 0.29, Z0 + 1.19)], 0.011, seg=10, mi=1)   # gooseneck
        bs.cylinder(bx + 0.09, y1 - 0.10, Z0 + 0.96, Z0 + 1.02, 0.014, seg=12, mi=1)             # lever
        bs.tube((bx + 0.09, y1 - 0.10, Z0 + 1.01), (bx + 0.09, y1 - 0.15, Z0 + 1.02), 0.005, 0.005, seg=8, mi=1)
    bs.build("Bath_Basins", [M['ceramic'], M['chrome']], smooth=True)
    mr = MB()
    for bx in (-2.35, -1.15):
        rrect_xz(mr, bx, Z0 + 1.85, y1 - 0.062, y1 - 0.042, 0.72, 0.98, 0.14, mi=0)              # mirror slab (front)
        rrect_xz(mr, bx, Z0 + 1.85, y1 - 0.042, y1 - 0.034, 0.78, 1.04, 0.17, mi=2)              # 30 mm dark frame ring behind it
        rrect_xz(mr, bx, Z0 + 1.85, y1 - 0.035, y1 - 0.031, 0.80, 1.06, 0.18, mi=1)              # halo
    mr.build("Bath_Mirrors", [M['mirror'], M['emit_bar'], M['black_metal']])
    # vanity props: soap dispensers, rolled towels, folded towel on the tub, bath tray with a candle, niche bottles
    pr = MB()
    for (px_, py_) in ((-2.05, y1 - 0.22), (-1.45, y1 - 0.22)):
        bottle(pr, px_, py_, Z0 + 0.96, 0, 1, h=0.14, r=0.03, cap=0.02)
        pr.tube((px_, py_, Z0 + 1.12), (px_ + 0.03, py_ - 0.02, Z0 + 1.11), 0.004, 0.004, seg=6, mi=1)       # pump nozzle
    for k, (tx_, ty_) in enumerate(((-0.72, y1 - 0.40), (-0.72, y1 - 0.24), (-0.72, y1 - 0.32))):
        pr.tube((tx_ - 0.13, ty_, Z0 + 0.96 + 0.05 + (0.09 if k == 2 else 0)), (tx_ + 0.13, ty_, Z0 + 0.96 + 0.05 + (0.09 if k == 2 else 0)), 0.05, 0.05, seg=16, mi=2)   # rolled towels
    pr.drape(-2.9, -2.55, 21.9, 22.35, Z0 + 0.63, t=0.03, mi=2, sag=0.02, folds=2, seed=7)                   # folded towel on the tub rim
    pr.box(-2.9, -2.1, 21.4, 21.62, Z0 + 0.62, Z0 + 0.64, 3)                                                  # walnut bath tray
    pr.box(-2.9, -2.1, 21.4, 21.415, Z0 + 0.64, Z0 + 0.66, 3); pr.box(-2.9, -2.1, 21.605, 21.62, Z0 + 0.64, Z0 + 0.66, 3)
    candle(pr, -2.7, 21.51, Z0 + 0.64, 4, 5, 6, r=0.035, h=0.09)
    books(pr, -2.28, 21.51, Z0 + 0.64, n=1, mi=7, w=0.2, d=0.15, rot=0.1)
    for k, bx_ in enumerate((22.37, 22.55, 22.78)):
        bottle(pr, x0 + 0.06 - 0.05, bx_, Z0 + 1.0, (0, 4, 0)[k], 1, h=(0.16, 0.12, 0.19)[k], r=0.024, cap=0.018)      # niche bottles
    pr.build("Bath_Props", [M['ceramic_black'], M['chrome'], M['linen_white'], M['walnut'], M['glass_tint'], M['ceramic_cream'], M['emit_warm'], M['book']], smooth=True, auto_smooth=True)
    # pendant cluster, vase with a leafy branch, towels
    pd = MB()
    for (px, py, drop) in ((-1.75, 22.85, 1.4), (-1.6, 22.7, 1.65), (-1.9, 22.65, 1.85)):
        pendant(pd, px, py, ZC - CEIL_T, drop=drop, r=0.09, mi_cord=0, mi_shade=1, style='dome')
    pd.build("Bath_Pendants", [M['black'], M['brass']], smooth=True)
    dc = MB()
    vase(dc, -0.95, y1 - 0.30, Z0 + 0.96, h=0.34, r=0.12, mi=0)
    branches(dc, -0.95, y1 - 0.30, Z0 + 1.28, h=0.6, n=6, seed=2, mi=1, leaves=14, mi_leaf=2, spread=0.45)
    towel_stack(dc, -1.55, y1 - 0.32, Z0 + 0.96, n=2, w=0.30, d=0.22, mi=3)
    towel_stack(dc, x0 + 0.33, 23.1, Z0 + 0.45, n=3, w=0.36, d=0.26, mi=3)
    dc.build("Bath_Decor", [M['ceramic'], M['bark'], M['leaf_plant'], M['linen_white']], smooth=True)
    # lights (photo 18): the backlit onyx is the main source; a cool skylight, a few narrow downlights over the tub
    # and basins, the mirror halos, the niche and the pendant bulbs - no big ceiling wash
    room_light("L_Bath", (*BATH, Z0, ZC), energy=6, z_off=0.3, color=(1.0, 0.9, 0.78))
    area_light("L_BathSky", ((kx0 + kx1) / 2, (ky0 + ky1) / 2, ZC + 0.33), (0.9, 0.9), 110, color=(0.80, 0.88, 1.0))
    dl = MB(); downlights(dl, [(-2.35, 22.55), (-1.15, 22.55), (-3.9, 22.7), (-2.5, 20.4), (-1.0, 20.4)], ZC - CEIL_T, r=0.04)
    dl.build("Bath_Downlights", [M['emit_down'], M['black']])
    for (lx, ly) in ((-2.35, 22.55), (-1.15, 22.55), (-3.9, 22.7), (-2.5, 20.4), (-1.0, 20.4)):
        add_light(f"L_BathSpot_{lx}_{ly}", 'SPOT', (lx, ly, ZC - CEIL_T - 0.03), 20, (1.0, 0.85, 0.66), size=0.03, spot=math.radians(52), blend=0.55)
    add_light("L_BathNiche", 'POINT', (x0 + 0.1, 22.6, Z0 + 1.35), 5, WARM, size=0.05)
    for (px, py, drop) in ((-1.75, 22.85, 1.4), (-1.6, 22.7, 1.65), (-1.9, 22.65, 1.85)):
        add_light(f"L_BathPendant_{drop:.2f}", 'POINT', (px, py, ZC - CEIL_T - drop - 0.05), 4, (1.0, 0.75, 0.5), size=0.04)
    for bx in (-2.35, -1.15):                                                                     # mirror halos really glow
        add_light(f"L_BathHalo_{bx:.2f}", 'AREA', (bx, y1 - 0.12, Z0 + 1.85), 4, (1.0, 0.9, 0.8), size=0.6, target=(bx, y1 - 2.0, Z0 + 1.3))


# ================================================================== closet (photo 19)
def build_closet(M):
    x0, x1, y0, y1 = CLOSET
    s = MB()
    floor_ceiling(s, CLOSET, 0, 1)
    finish(s, CLOSET, 'WSEN', 2, t=0.03, holes={'S': [(0.9, 1.9, Z0, Z0 + 2.3)], 'W': [(21.3, 22.3, Z0, Z0 + 2.4)]})
    s.build("Closet_Shell", [M['oak_floor'], M['ceiling'], M['oak_pale']])
    cd_ = MB(); room_details(cd_, CLOSET, mi_gap=0, mi_speaker=1, mi_diffuser=2, speakers=((1.5, 21.6),), diffusers=((2.0, 20.0, 'Y'),))
    cd_.build("Closet_Details", [M['black'], M['white_gloss'], M['black_metal']])
    oak, led, chrome = 0, 1, 2
    u = MB()
    # west wall unit (y 19.9..21.1 south of the portal): drawers below, open shelves with LED strips above
    wx = x0 + 0.03
    for (ya, yb) in ((19.9, 21.2),):
        u.box(wx, wx + 0.55, ya, yb, Z0 + 0.02, Z0 + 1.0, oak)
        for i in range(1, 3):                                                                    # drawer reveals
            zz = Z0 + 0.02 + 0.98 * i / 3
            u.box(wx + 0.55, wx + 0.553, ya + 0.02, yb - 0.02, zz - 0.003, zz + 0.003, chrome)
        for zz in (Z0 + 1.35, Z0 + 1.85, Z0 + 2.35):
            u.box(wx, wx + 0.42, ya, yb, zz, zz + 0.03, oak)
            u.box(wx + 0.39, wx + 0.42, ya, yb, zz - 0.012, zz, led)
        u.box(wx, wx + 0.03, ya, yb, Z0 + 1.0, Z0 + 2.7, oak)                                   # back panel
        u.box(wx, wx + 0.42, ya - 0.03, ya, Z0 + 0.02, Z0 + 2.7, oak); u.box(wx, wx + 0.42, yb, yb + 0.03, Z0 + 0.02, Z0 + 2.7, oak)
    # north-east: full-height mirror; north-west: vanity desk + lit mirror
    u.box(0.3, 1.5, y1 - 0.58, y1 - 0.03, Z0 + 0.70, Z0 + 0.74, oak)                             # vanity top
    u.box(0.3, 0.34, y1 - 0.55, y1 - 0.03, Z0 + 0.02, Z0 + 0.70, oak); u.box(1.46, 1.5, y1 - 0.55, y1 - 0.03, Z0 + 0.02, Z0 + 0.70, oak)
    u.box(0.34, 1.46, y1 - 0.58, y1 - 0.03, Z0 + 0.60, Z0 + 0.70, oak)                           # drawer
    u.box(0.34, 1.46, y1 - 0.583, y1 - 0.58, Z0 + 0.60, Z0 + 0.603, chrome)                       # drawer reveal
    # island with drawer reveals (3 mm) + horizontal reveals
    cabinet_run(u, 1.0, 2.1, 20.5, 22.4, Z0 + 0.02, Z0 + 0.95, mi=oak, doors='Y', n=3, gap=0.003, mi_gap=chrome)
    for zz in (Z0 + 0.33, Z0 + 0.64):
        u.box(0.997, 1.0, 20.52, 22.38, zz - 0.0015, zz + 0.0015, chrome); u.box(2.1, 2.103, 20.52, 22.38, zz - 0.0015, zz + 0.0015, chrome)
    u.box(0.97, 2.13, 20.47, 22.43, Z0 + 0.95, Z0 + 0.99, oak)
    # east wall: double hanging rails + top shelf + a low shoe shelf, LED bars under each shelf front
    ex = x1 - 0.03
    u.box(ex - 0.55, ex, 21.0, 23.2, Z0 + 2.3, Z0 + 2.33, oak)
    u.box(ex - 0.55, ex - 0.542, 21.0, 23.2, Z0 + 2.292, Z0 + 2.3, led)
    u.box(ex - 0.55, ex, 21.0, 23.2, Z0 + 0.32, Z0 + 0.35, oak)                                    # shoe shelf
    u.box(ex - 0.55, ex - 0.542, 21.0, 23.2, Z0 + 0.312, Z0 + 0.32, led)
    u.box(ex - 0.55, ex, 23.2, 23.23, Z0 + 0.02, Z0 + 2.33, oak)
    u.build("Closet_Units", [M['oak_pale'], M['emit_bar'], M['chrome']])
    r = MB()
    for zr in (Z0 + 1.1, Z0 + 2.15):
        r.tube((ex - 0.3, 21.0, zr), (ex - 0.3, 23.2, zr), 0.012, 0.012, seg=8, mi=0)
    r.tube((wx + 0.2, 19.9, Z0 + 2.6), (wx + 0.2, 21.2, Z0 + 2.6), 0.012, 0.012, seg=8, mi=0)
    r.build("Closet_Rails", M['chrome'], smooth=True)
    gm = MB()
    cloth = (0, 1, 2, 3, 0, 1, 4, 0, 2, 3)
    for i, yy in enumerate((21.75, 21.98, 22.2, 22.44, 22.68, 22.9, 23.1)):        # (starts past the camera's right edge)
        hanger_garment(gm, ex - 0.3, yy, Z0 + 2.15, cloth[i], 5, along='Y', w=0.42, h=0.72, seed=i)
    for i, yy in enumerate((21.8, 22.05, 22.3, 22.55, 22.8, 23.05)):
        hanger_garment(gm, ex - 0.3, yy, Z0 + 1.1, cloth[(i + 3) % 10], 5, along='Y', w=0.42, h=0.62, seed=20 + i)
    for i, yy in enumerate((20.05, 20.5, 20.95)):
        hanger_garment(gm, wx + 0.2, yy, Z0 + 2.6, cloth[(i + 5) % 10], 5, along='Y', w=0.42, h=0.7, seed=40 + i)
    gm.build("Closet_Garments", [M['linen_white'], M['fabric_sand'], M['fabric_grey'], M['fabric_dark'], M['fabric_white'], M['chrome']], smooth=True)
    sh_ = MB()
    for k, yy in enumerate((21.25, 21.6, 21.95, 22.3, 22.65, 23.0)):
        shoe_pair(sh_, ex - 0.28, yy, Z0 + 0.35, (0, 1, 2, 0, 1, 2)[k], rot=math.pi / 2, l=0.27)
    for k, (sx_, sy_) in enumerate(((wx + 0.2, 20.1), (wx + 0.2, 20.5), (wx + 0.2, 20.95), (1.55, 21.0))):
        sweater_stack(sh_, sx_, sy_, Z0 + 1.35 if k < 3 else Z0 + 0.99, (3, 4, 0), w=0.32, d=0.26, n=3 if k < 3 else 2, rot=0.05 * k)
    sh_.rbox(1.3, 1.75, 21.35, 21.65, Z0 + 0.99, Z0 + 1.03, r=0.01, mi=5)                                   # leather tray on the island
    for k in range(3):
        sh_.lathe(1.38 + k * 0.14, 21.5, Z0 + 1.03, [(0, 0), (0.02, 0), (0.02, 0.01), (0.008, 0.01), (0.008, 0.02), (0, 0.02)], seg=12, mi=6)   # watches
    sh_.rbox(1.05, 1.28, 22.0, 22.25, Z0 + 0.99, Z0 + 1.02, r=0.008, mi=5)                                   # second tray
    for k, (px_, py_) in enumerate(((0.62, y1 - 0.45), (0.72, y1 - 0.4), (0.68, y1 - 0.5))):
        bottle(sh_, px_, py_, Z0 + 0.74, (7, 8, 7)[k], 6, h=(0.09, 0.11, 0.07)[k], r=0.02, cap=0.02)         # perfume trio
    sh_.build("Closet_Props", [M['leather_tan'], M['fabric_dark'], M['ceramic_black'], M['fabric_sand'], M['linen_white'], M['leather_tan'], M['chrome'], M['glass_tint'], M['brass']], smooth=True, auto_smooth=True)
    m = MB()
    m.box(2.05, 3.0, y1 - 0.045, y1 - 0.035, Z0 + 0.05, Z0 + 2.4, 0)                             # full-height mirror
    m.box(2.03, 3.02, y1 - 0.05, y1 - 0.045, Z0 + 0.03, Z0 + 2.42, 2)                             # dark backing / edge
    # vanity mirror cabinet (photo 19): a shallow lit niche with three glass shelves, mirror back, LED-lit frame
    nx0, nx1, nz0, nz1 = 0.52, 1.28, Z0 + 0.98, Z0 + 1.95
    m.box(nx0 - 0.03, nx1 + 0.03, y1 - 0.10, y1 - 0.04, nz0 - 0.03, nz0, 3)                       # oak frame
    m.box(nx0 - 0.03, nx1 + 0.03, y1 - 0.10, y1 - 0.04, nz1, nz1 + 0.03, 3)
    m.box(nx0 - 0.03, nx0, y1 - 0.10, y1 - 0.04, nz0, nz1, 3); m.box(nx1, nx1 + 0.03, y1 - 0.10, y1 - 0.04, nz0, nz1, 3)
    m.box(nx0, nx1, y1 - 0.045, y1 - 0.04, nz0, nz1, 0)                                          # mirror back
    for k in range(1, 4):
        zz = nz0 + (nz1 - nz0) * k / 4
        m.box(nx0, nx1, y1 - 0.10, y1 - 0.045, zz, zz + 0.008, 4)                                 # glass shelf
        m.box(nx0, nx1, y1 - 0.10, y1 - 0.092, zz - 0.004, zz, 1)                                 # LED under the front edge
    m.frame(nx0 - 0.03, nx1 + 0.03, y1 - 0.104, y1 - 0.10, nz0 - 0.03, nz1 + 0.03, 0.012, mi=1, axis='Y')   # LED halo on the frame face
    m.build("Closet_Mirrors", [M['mirror'], M['emit_bar'], M['black'], M['oak_pale'], M['glass']])
    st = MB(); st.rbox(0.68, 1.12, 21.9, 22.34, Z0 + 0.22, Z0 + 0.48, r=0.1, mi=0, puff=0.3)
    st.cylinder(0.9, 22.12, Z0 + 0.02, Z0 + 0.22, 0.1, seg=12, mi=1)
    st.build("Closet_Stool", [M['fabric_white'], M['oak_pale']], smooth=True, subsurf=1)
    dc = MB()
    vase(dc, 0.5, y1 - 0.3, Z0 + 0.74, h=0.22, r=0.07, mi=0, style='tall')
    branches(dc, 0.5, y1 - 0.3, Z0 + 0.96, h=0.35, n=5, seed=4, mi=1, leaves=10, mi_leaf=2, spread=0.4)
    books(dc, 1.25, y1 - 0.3, Z0 + 0.74, n=2, mi=3, w=0.22, d=0.16)
    vase(dc, 1.55, 21.45, Z0 + 0.99, h=0.12, r=0.09, mi=0, style='bowl')
    dc.build("Closet_Decor", [M['ceramic_cream'], M['bark'], M['leaf_plant'], M['book']], smooth=True)
    # ceiling (photo 19): black recessed slots down the middle, a lit cove line where the units meet the ceiling,
    # LED lines under every shelf front - and only a faint ambient
    tl = MB()
    zc = ZC - CEIL_T
    heads = slot_y(tl, 1.4, 20.0, 21.4, zc, 0, 1, heads=3) + slot_y(tl, 1.4, 21.9, 23.3, zc, 0, 1, heads=3)
    tl.build("Closet_Slots", [M['black'], M['emit_white']])
    head_spots("L_ClosetHead", heads, zc, energy=24, spot=55, blend=0.6)
    cv = MB()
    cove_y(cv, 19.9, 23.3, x0 + 0.42, zc - 0.012, 0, w=0.03, face=-1)                             # over the west unit
    cove_y(cv, 20.9, 23.3, x1 - 0.55, zc - 0.012, 0, w=0.03, face=1)                              # over the east shelves
    cove_x(cv, 0.3, 1.5, y1 - 0.58, zc - 0.012, 0, w=0.03, face=1)                                # over the vanity
    cv.build("Closet_CoveLines", M['emit_cove'])
    wash_light("L_ClosetCoveW", (x0 + 0.5, 19.9), (x0 + 0.5, 23.3), zc - 0.02, 10, up=True, width=0.05)
    wash_light("L_ClosetCoveE", (x1 - 0.62, 20.9), (x1 - 0.62, 23.3), zc - 0.02, 10, up=True, width=0.05)
    wash_light("L_ClosetShelfE", (x1 - 0.3, 21.0), (x1 - 0.3, 23.2), Z0 + 2.28, 8, color=(1.0, 0.82, 0.6), width=0.04)
    wash_light("L_ClosetShelfW", (x0 + 0.25, 19.9), (x0 + 0.25, 21.2), Z0 + 1.34, 6, color=(1.0, 0.82, 0.6), width=0.04)
    room_light("L_Closet", (*CLOSET, Z0, ZC), energy=8, z_off=0.3)
    add_light("L_ClosetVanity", 'SPOT', (0.9, 22.5, zc - 0.03), 18, WARM, size=0.03, spot=math.radians(55), blend=0.6, target=(0.9, y1 - 0.3, Z0 + 0.8))


# ================================================================== office (photo 16)
def build_office(M):
    from archviz import materials as MT
    walnut_dk = MT.wood("WalnutDark", light=(0.24, 0.13, 0.07, 1), dark=(0.10, 0.05, 0.03, 1), grain_axis='X', rough=0.35, coat=0.35)
    rust = MT.fabric("BoucleRustDeep", (0.50, 0.22, 0.11, 1))
    x0, x1, y0, y1 = OFFICE
    s = MB()
    floor_ceiling(s, OFFICE, 0, 1)
    finish(s, OFFICE, 'WEN', 2)
    s.build("Office_Shell", [M['oak_floor'], M['ceiling'], M['white_int']])
    od = MB(); room_details(od, OFFICE, mi_gap=0, mi_speaker=1, mi_diffuser=2, faces='WEN', speakers=((5.25, 20.6),), diffusers=((5.25, 18.5, 'X'),))
    od.build("Office_Details", [M['black'], M['white_gloss'], M['black_metal']])
    rug_slab("Rug_Office", x0 + 0.4, x1 - 0.45, 18.7, 22.5, Z0 + 0.02, M['rug_pale'])
    # oval walnut desk (photo 16: ~2.1 x 1.0 m, 40 mm top with a soft edge, on an elliptical drum pedestal)
    dk = MB()
    dx_, dy_ = 5.15, 20.75
    dk.lathe(dx_, dy_, Z0 + 0.70, [(0, 0), (0.46, 0), (0.495, 0.012), (0.50, 0.025), (0.495, 0.038), (0.46, 0.045), (0, 0.045)], seg=64, mi=0, ry=2.1)
    dk.cylinder(dx_, dy_, Z0 + 0.02, Z0 + 0.70, 0.27, seg=40, mi=0, ry=1.9)
    dk.build("Office_Desk", walnut_dk, smooth=True, auto_smooth=True)
    dp = MB()
    laptop(dp, dx_ - 0.05, dy_ - 0.55, Z0 + 0.745, 0, 1, rot=0.3)
    dp.lathe(dx_ + 0.3, dy_ + 0.3, Z0 + 0.745, [(0, 0), (0.035, 0), (0.035, 0.1), (0.03, 0.1), (0.03, 0.005), (0, 0.005)], seg=14, mi=2)   # pen cup
    for k in range(4):
        dp.cylinder(dx_ + 0.3 + 0.012 * math.cos(k * 1.7), dy_ + 0.3 + 0.012 * math.sin(k * 1.7), Z0 + 0.75, Z0 + 0.9 + k * 0.01, 0.004, seg=6, mi=(3, 4, 3, 4)[k])
    # a contact sheet of prints and a stack of white boxes (photo 16)
    for k in range(6):
        dp.box(dx_ - 0.30 + (k % 3) * 0.13, dx_ - 0.30 + (k % 3) * 0.13 + 0.11, dy_ + 0.05 + (k // 3) * 0.10, dy_ + 0.05 + (k // 3) * 0.10 + 0.085, Z0 + 0.745, Z0 + 0.747, 7)
    dp.rcbox(dx_ + 0.22, dy_ - 0.35, Z0 + 0.745 + 0.03, 0.26, 0.18, 0.06, r=0.006, mi=7)
    dp.rcbox(dx_ + 0.22, dy_ - 0.35, Z0 + 0.745 + 0.085, 0.24, 0.16, 0.05, r=0.006, mi=7)
    dp.build("Office_DeskProps", [M['black_gloss'], M['tv'], M['ceramic_black'], M['black'], M['brass'], M['brass'], M['emit_warm'], M['paper']], smooth=True, auto_smooth=True)
    # chairs: two rust boucle armchairs facing the desk from the east, a black slatted chair on the west
    ch = MB()
    armchair(ch, 6.3, 20.05, rot=-math.pi / 2 + 0.15, z=Z0 + 0.02, w=0.8, d=0.8, mi=0, mi_legs=1)
    armchair(ch, 6.3, 21.55, rot=-math.pi / 2 - 0.35, z=Z0 + 0.02, w=0.8, d=0.8, mi=0, mi_legs=1)
    ch.build("Office_Armchairs", [rust, walnut_dk], bevel=0.03)
    bc = MB()
    dining_chair(bc, 4.05, dy_, rot=math.pi / 2, z=Z0 + 0.02, mi_wood=0, mi_seat=1, w=0.5, d=0.5)
    for k in range(9):                                                                           # slatted back
        zz = Z0 + 0.02 + 0.55 + k * 0.045
        bc.cbox(3.82, dy_, zz, 0.02, 0.44, 0.012, 0, 0.0)
    bc.build("Office_SlatChair", [M['black'], M['linen_white']])
    # black credenza on the EAST wall (photo 16) + ceramics, two B&W canvases above it
    cr = MB()
    cabinet_run(cr, x1 - 0.47, x1 - 0.04, 19.4, 22.4, Z0 + 0.12, Z0 + 0.68, mi=0, doors='Y', n=3, gap=0.003, mi_gap=1)
    cr.box(x1 - 0.473, x1 - 0.47, 19.4, 22.4, Z0 + 0.40 - 0.0015, Z0 + 0.40 + 0.0015, 1)                     # horizontal drawer reveal
    cr.box(x1 - 0.45, x1 - 0.06, 19.45, 22.35, Z0 + 0.02, Z0 + 0.12, 1)
    cr.build("Office_Credenza", [M['ebony'], M['black']])
    dc = MB()
    vase(dc, x1 - 0.26, 19.9, Z0 + 0.68, h=0.34, r=0.12, mi=0, style='tall')
    vase(dc, x1 - 0.26, 20.5, Z0 + 0.68, h=0.14, r=0.11, mi=1, style='bowl')
    vase(dc, x1 - 0.26, 21.9, Z0 + 0.68, h=0.26, r=0.10, mi=2)
    books(dc, dx_ - 0.05, dy_ + 0.45, Z0 + 0.745, n=3, mi=3, w=0.32, d=0.24)
    vase(dc, dx_ + 0.05, dy_ - 0.05, Z0 + 0.745, h=0.14, r=0.07, mi=0)
    branches(dc, dx_ + 0.05, dy_ - 0.05, Z0 + 0.885, h=0.25, n=4, seed=6, mi=4, leaves=8, mi_leaf=5, spread=0.5)
    lamp(dc, dx_ - 0.1, dy_ + 0.75, Z0 + 0.745, mi_base=6, mi_shade=7, base_r=0.09, base_h=0.28, shade_r=0.17, shade_h=0.2)
    add_light("L_OfficeLamp", 'POINT', (dx_ - 0.1, dy_ + 0.75, Z0 + 0.745 + 0.42), 6, (1.0, 0.78, 0.55), size=0.05)
    dc.build("Office_Decor", [M['ceramic'], M['clay'], M['ceramic_cream'], M['book'], M['bark'], M['leaf_plant'], M['ceramic_black'], M['lampshade']], smooth=True)
    ar = MB()
    floater_canvas(ar, 18.6, 21.4, x0 + 0.02, Z0 + 0.85, Z0 + 2.75, 0, 1, along='Y', face=1)                 # big drawing on the west wall
    floater_canvas(ar, 19.75, 20.75, x1 - 0.02, Z0 + 1.05, Z0 + 2.35, 0, 2, along='Y', face=-1)              # two B&W canvases over the credenza
    floater_canvas(ar, 20.85, 21.85, x1 - 0.02, Z0 + 1.05, Z0 + 2.35, 0, 2, along='Y', face=-1)
    ar.build("Office_Art", [M['oak'], M['art_abstract'], M['art_bw']])
    # potted olive: gnarled trunk, branches and ~140 small pillow-leaves
    pl = MB()
    px_, py_ = 4.0, 22.75
    pl.lathe(px_, py_, Z0 + 0.02, [(0, 0), (0.24, 0), (0.28, 0.4), (0.25, 0.4), (0.25, 0.37), (0, 0.37)], seg=24, mi=0)
    pl.cylinder(px_, py_, Z0 + 0.37, Z0 + 0.39, 0.24, seg=20, mi=3)                                            # soil
    rng_ = random.Random(3)
    pl.path_tube([(px_, py_, Z0 + 0.38), (px_ + 0.04, py_ - 0.02, Z0 + 0.9), (px_ - 0.02, py_ + 0.03, Z0 + 1.3)], 0.028, seg=8, mi=2)
    for i in range(7):
        a_ = 2 * math.pi * i / 7 + rng_.uniform(-0.3, 0.3)
        tip = (px_ - 0.02 + 0.45 * math.cos(a_), py_ + 0.03 + 0.45 * math.sin(a_), Z0 + 1.3 + rng_.uniform(0.2, 0.75))
        mid = ((px_ + tip[0]) / 2, (py_ + tip[1]) / 2, Z0 + 1.25 + (tip[2] - Z0 - 1.3) * 0.5)
        pl.path_tube([(px_ - 0.02, py_ + 0.03, Z0 + 1.28), mid, tip], 0.009, seg=6, mi=2)
        for k in range(34):
            t = rng_.uniform(0.3, 1.08)
            lx = px_ + (tip[0] - px_) * t + rng_.uniform(-0.16, 0.16); ly = py_ + (tip[1] - py_) * t + rng_.uniform(-0.16, 0.16)
            lz = Z0 + 1.28 + (tip[2] - Z0 - 1.28) * t + rng_.uniform(-0.14, 0.14)
            pl.pillow(lx, ly, lz, w=0.085, d=0.03, t=0.005, mi=1, rot=rng_.uniform(0, math.pi), pitch=rng_.uniform(-1.2, 1.2))
    pl.build("Office_Olive", [M['plant_pot'], M['olive'], M['bark'], M['soil']], smooth=True, auto_smooth=True)
    # ceiling (photo 16): two long black slots, heads aimed at the art, the desk and the credenza; faint ambient
    tl = MB()
    zc = ZC - CEIL_T
    heads = slot_y(tl, 4.3, 18.6, 22.9, zc, 0, 1, heads=4) + slot_y(tl, 6.2, 18.6, 22.9, zc, 0, 1, heads=4)
    tl.build("Office_Slots", [M['black'], M['emit_white']])
    aims = [(x0, 19.4, Z0 + 1.8), (x0, 20.6, Z0 + 1.8), (dx_, dy_, Z0 + 0.75), (4.2, 22.7, Z0 + 1.2),
            (x1, 20.2, Z0 + 1.7), (x1, 21.4, Z0 + 1.7), (6.3, 20.8, Z0 + 0.5), (x1, 22.0, Z0 + 0.7)]
    head_spots("L_OfficeHead", heads, zc, energy=26, spot=46, blend=0.6, color=(1.0, 0.86, 0.68), targets=aims)
    room_light("L_Office", (*OFFICE, Z0, ZC), energy=10, z_off=0.3, color=(1.0, 0.95, 0.9))


# ================================================================== gym + sauna (photo 20)
def build_gym(M):
    x0, x1, y0, y1 = GYM
    s = MB()
    floor_ceiling(s, GYM, 0, 1)
    finish(s, GYM, 'WNE', 2)
    s.box(x0, x0 + 0.32, y0, y0 + 1.3, Z0, ZC - CEIL_T, 3)                                       # travertine pier by the glass
    s.build("Gym_Shell", [M['oak_floor'], M['ceiling'], M['white_int'], M['trav_int']])
    gd = MB(); room_details(gd, GYM, mi_gap=0, mi_speaker=1, mi_diffuser=2, faces='WNE', speakers=((9.5, 20.3), (12.5, 20.3)), diffusers=((9.0, 22.6, 'X'), (12.8, 19.2, 'X')))
    gd.build("Gym_Details", [M['black'], M['white_gloss'], M['black_metal']])
    # sauna box on the north wall (x 10.0..12.8), travertine inside, glass front
    sx0, sx1, sy0, sy1, sz1 = 11.3, 14.1, 21.65, y1 - 0.02, Z0 + 2.4
    sa = MB()
    sa.box(sx0, sx0 + 0.1, sy0, sy1, Z0, sz1 + 0.1, 0); sa.box(sx1 - 0.1, sx1, sy0, sy1, Z0, sz1 + 0.1, 0)
    sa.box(sx0, sx1, sy1 - 0.1, sy1, Z0, sz1 + 0.1, 0)
    sa.box(sx0, sx1, sy0, sy1, sz1, sz1 + 0.1, 0)
    sa.box(sx0 + 0.1, sx1 - 0.1, sy0 + 0.1, sy1 - 0.1, Z0 + 0.02, Z0 + 0.04, 1)                   # cedar duckboard floor
    # benches: upper along the north wall, lower L along north + west, LED under each front edge
    sa.box(sx0 + 0.1, sx1 - 0.1, sy1 - 0.75, sy1 - 0.1, Z0 + 0.72, Z0 + 0.78, 1)
    sa.box(sx0 + 0.1, sx1 - 0.1, sy1 - 0.75, sy1 - 0.70, Z0 + 0.20, Z0 + 0.72, 1)
    sa.box(sx0 + 0.1, sx1 - 0.1, sy1 - 1.30, sy1 - 0.75, Z0 + 0.38, Z0 + 0.44, 1)
    sa.box(sx0 + 0.1, sx0 + 0.7, sy0 + 0.1, sy1 - 1.30, Z0 + 0.38, Z0 + 0.44, 1)
    sa.box(sx0 + 0.1, sx1 - 0.1, sy1 - 1.30, sy1 - 1.28, Z0 + 0.36, Z0 + 0.38, 2)
    sa.box(sx0 + 0.1, sx1 - 0.1, sy1 - 0.75, sy1 - 0.73, Z0 + 0.70, Z0 + 0.72, 2)
    sa.box(sx0 + 0.68, sx0 + 0.7, sy0 + 0.1, sy1 - 1.30, Z0 + 0.36, Z0 + 0.38, 2)
    sa.box(sx0 + 0.1, sx1 - 0.1, sy1 - 0.20, sy1 - 0.1, Z0 + 1.6, Z0 + 1.62, 2)                   # backrest LED line
    # bench slats (6 mm gaps) laid over the bench tops, bucket + ladle, thermometer
    for (bx0_, bx1_, by0_, by1_, bz_) in ((sx0 + 0.1, sx1 - 0.1, sy1 - 0.75, sy1 - 0.1, Z0 + 0.78), (sx0 + 0.1, sx1 - 0.1, sy1 - 1.30, sy1 - 0.75, Z0 + 0.44), (sx0 + 0.1, sx0 + 0.7, sy0 + 0.1, sy1 - 1.30, Z0 + 0.44)):
        n_ = max(2, int((by1_ - by0_) / 0.066))
        for k in range(n_):
            ya_ = by0_ + (by1_ - by0_) * k / n_
            sa.box(bx0_, bx1_, ya_ + 0.003, ya_ + (by1_ - by0_) / n_ - 0.003, bz_, bz_ + 0.018, 1)
    sa.lathe(sx0 + 0.45, sy1 - 1.0, Z0 + 0.46, [(0, 0), (0.1, 0), (0.12, 0.2), (0.11, 0.2), (0.09, 0.02), (0, 0.02)], seg=18, mi=1)     # bucket
    sa.path_tube([(sx0 + 0.5, sy1 - 1.05, Z0 + 0.5), (sx0 + 0.62, sy1 - 1.15, Z0 + 0.74)], 0.008, seg=6, mi=1)                          # ladle handle
    sa.lathe(sx0 + 0.5, sy1 - 1.05, Z0 + 0.47, [(0, 0), (0.035, 0), (0.035, 0.04), (0, 0.04)], seg=12, mi=1)
    sa.box(sx1 - 0.35, sx1 - 0.15, sy1 - 0.125, sy1 - 0.1, Z0 + 1.7, Z0 + 1.9, 1)                                                     # thermometer
    sa.box(sx1 - 0.33, sx1 - 0.17, sy1 - 0.13, sy1 - 0.125, Z0 + 1.72, Z0 + 1.88, 3)
    sa.build("Gym_Sauna", [M['trav_int'], M['oak'], M['emit_cove'], M['paper']])
    # sauna heater (black cylinder with a stone basket) in the SW corner + wall-mounted light
    ht = MB()
    ht.lathe(sx0 + 0.35, sy0 + 0.35, Z0 + 0.04, [(0, 0), (0.17, 0), (0.17, 0.62), (0.16, 0.62), (0.16, 0.05), (0, 0.05)], seg=24, mi=0)
    rng_h = random.Random(5)
    for k in range(26):
        a_ = rng_h.uniform(0, 2 * math.pi); rr = rng_h.uniform(0, 0.12)
        ht.blob((sx0 + 0.35 + rr * math.cos(a_), sy0 + 0.35 + rr * math.sin(a_), Z0 + 0.62 + rng_h.uniform(0.0, 0.08)), rng_h.uniform(0.03, 0.045), seg=8, rings=5, jitter=0.35, seed=k, mi=1, squash=0.75)
    ht.build("Gym_SaunaHeater", [M['black_metal'], M['pebble']], smooth=True, auto_smooth=True)
    sg = MB()
    glass_wall(sg, sx0 + 0.1, sx1 - 0.1, sy0 + 0.02, sy0 + 0.02 + T, Z0 + 0.02, sz1, mi_glass=0, mi_frame=1, mullions=(sx0 + 1.0,))
    sg.tube((sx0 + 0.92, sy0 - 0.05, Z0 + 0.9), (sx0 + 0.92, sy0 - 0.05, Z0 + 1.4), 0.012, 0.012, seg=10, mi=2)   # glass door pull (vertical bar)
    for zz in (Z0 + 0.95, Z0 + 1.35):
        sg.tube((sx0 + 0.92, sy0 - 0.05, zz), (sx0 + 0.92, sy0 + 0.02, zz), 0.008, 0.008, seg=8, mi=2)
    sg.build("Gym_SaunaGlass", [M['glass'], M['frame'], M['chrome']], smooth=True, auto_smooth=True)
    add_light("L_Sauna", 'POINT', ((sx0 + sx1) / 2, sy1 - 0.6, Z0 + 2.2), 9, (1.0, 0.7, 0.45), size=0.2)
    wash_light("L_SaunaBench", (sx0 + 0.15, sy1 - 1.29), (sx1 - 0.15, sy1 - 1.29), Z0 + 0.36, 5, color=(1.0, 0.75, 0.5), width=0.04)
    wash_light("L_SaunaBench2", (sx0 + 0.15, sy1 - 0.74), (sx1 - 0.15, sy1 - 0.74), Z0 + 0.70, 5, color=(1.0, 0.75, 0.5), width=0.04)
    # backlit Himalayan-salt brick wall (photo 20): a glowing panel of salt bricks inside a cedar-panelled alcove
    # left of the sauna, with a low oak bench in front
    from archviz import materials as MT
    salt = _salt_material(MT, "SaltBricksGlow")
    cedar = MT.wood_planks("CedarPanelling", light=(0.78, 0.58, 0.38, 1), dark=(0.66, 0.46, 0.28, 1), plank=(3.0, 0.12), along='X', rough=0.5, coat=0.05)
    sw = MB()
    sw.wall('X', 8.1, 11.1, y1 - 0.32, y1 - 0.02, Z0 + 0.02, ZC - CEIL_T, holes=[(8.35, 10.55, Z0 + 0.62, Z0 + 2.32)], mi=0)   # cedar alcove wall
    sw.box(8.35, 10.55, y1 - 0.12, y1 - 0.07, Z0 + 0.62, Z0 + 2.32, 1)                             # salt bricks (glowing) recessed in the opening
    sw.frame(8.32, 10.58, y1 - 0.32, y1 - 0.12, Z0 + 0.59, Z0 + 2.35, 0.03, mi=2, axis='Y')          # bronze reveal lining the opening
    sw.box(8.4, 10.5, y1 - 0.62, y1 - 0.32, Z0 + 0.42, Z0 + 0.47, 3)                                # bench
    sw.box(8.45, 8.55, y1 - 0.60, y1 - 0.34, Z0 + 0.02, Z0 + 0.42, 3); sw.box(10.35, 10.45, y1 - 0.60, y1 - 0.34, Z0 + 0.02, Z0 + 0.42, 3)
    sw.build("Gym_SaltWall", [cedar, salt, M['bronze'], M['oak']])
    area_light("L_Salt", (9.45, y1 - 0.45, Z0 + 1.5), (1.9, 1.5), 14, color=(1.0, 0.50, 0.26), target=(9.45, y0, Z0 + 1.0))
    # rolled towels on the sauna's upper bench + a folded one on the salt-wall bench
    tw = MB()
    for k, xx in enumerate((sx1 - 0.55, sx1 - 0.85)):
        tw.tube((xx - 0.12, sy1 - 0.42, Z0 + 0.78 + 0.05), (xx + 0.12, sy1 - 0.42, Z0 + 0.78 + 0.05), 0.05, 0.05, seg=16, mi=0)
    towel_stack(tw, 10.1, y1 - 0.47, Z0 + 0.47, n=2, w=0.34, d=0.24, mi=0)
    tw.build("Gym_Towels", M['linen_white'], smooth=True, auto_smooth=True)
    # west wall: two arched mirrors + TV + black console with a moss bowl
    mr = MB()
    arch_yz(mr, 20.15, Z0 + 0.15, x0 + 0.025, x0 + 0.04, 0.75, 2.05, mi=0)
    arch_yz(mr, 21.05, Z0 + 0.15, x0 + 0.025, x0 + 0.04, 0.75, 2.05, mi=0)
    mr.build("Gym_Mirrors", M['mirror'])
    mf = MB()
    for cy in (20.15, 21.05):
        arch_yz(mf, cy, Z0 + 0.135, x0 + 0.02, x0 + 0.05, 0.78, 2.08, mi=0)                    # 15 mm black frame (arch behind the mirror)
        mf.box(x0 + 0.02, x0 + 0.05, cy - 0.39, cy + 0.39, Z0 + 0.135, Z0 + 0.15, 0)
    mf.build("Gym_MirrorFrames", M['black_metal'])
    tvm = MB()
    tvm.box(x0 + 0.03, x0 + 0.075, 21.68, 23.27, Z0 + 1.33, Z0 + 2.27, 1)                       # bezel body
    tv(tvm, 21.7, 23.25, x0 + 0.08, Z0 + 1.35, Z0 + 2.25, mi=0, along='Y', d=0.004)
    tvm.build("Gym_TV", [M['tv'], M['black_metal']])
    cn = MB()
    cn.box(x0 + 0.05, x0 + 0.45, 21.7, 23.25, Z0 + 0.02, Z0 + 0.72, 0)
    for cy in (22.05, 22.6, 23.0):                                                                # oval cut-outs (dark recesses)
        cn.cylinder(x0 + 0.46, cy, Z0 + 0.18, Z0 + 0.56, 0.02, seg=12, mi=1, ry=0.14)
    cn.build("Gym_Console", [M['black'], M['black_gloss']])
    mb2 = MB()
    mb2.lathe(x0 + 0.25, 22.45, Z0 + 0.72, [(0, 0), (0.18, 0), (0.24, 0.06), (0.25, 0.1), (0, 0.1)], seg=20, mi=0)
    mb2.blob((x0 + 0.25, 22.45, Z0 + 0.86), 0.2, seg=14, rings=8, jitter=0.35, seed=12, mi=1, squash=0.55)
    mb2.build("Gym_MossBowl", [M['black_gloss'], M['moss']], smooth=True)
    # three spin bikes facing the TV / glass corner
    bk = MB()
    for i, (bx, by) in enumerate(((9.6, 19.7), (10.9, 20.15), (12.2, 20.6))):
        spin_bike(bk, bx, by, Z0 + 0.02, rot=-0.75, mi=0, mi_red=1)
    bk.build("Gym_Bikes", [M['black_metal'], M['fabric_rust'], M['tv'], M['acrylic_white']], smooth=True, auto_smooth=True)
    # dumbbell rack on the west wall (3 pairs) + a rolled yoga mat
    dr_ = MB()
    dr_.box(x0 + 0.05, x0 + 0.55, 19.05, 19.95, Z0 + 0.42, Z0 + 0.46, 0)
    dr_.box(x0 + 0.05, x0 + 0.55, 19.05, 19.95, Z0 + 0.72, Z0 + 0.76, 0)
    for yy in (19.07, 19.93):
        dr_.box(x0 + 0.07, x0 + 0.11, yy - 0.02, yy + 0.02, Z0 + 0.02, Z0 + 0.76, 0); dr_.box(x0 + 0.49, x0 + 0.53, yy - 0.02, yy + 0.02, Z0 + 0.02, Z0 + 0.76, 0)
    for k, yy in enumerate((19.2, 19.5, 19.8)):
        dumbbell(dr_, x0 + 0.3, yy, Z0 + 0.46, 1, l=0.3, r=0.03 + 0.008 * k)
        dumbbell(dr_, x0 + 0.3, yy, Z0 + 0.76, 1, l=0.3, r=0.03 + 0.008 * k)
    dr_.tube((x0 + 0.08, 20.25, Z0 + 0.09), (x0 + 0.08 + 0.62, 20.25, Z0 + 0.09), 0.07, 0.07, seg=16, mi=2)      # yoga mat roll
    dr_.build("Gym_Rack", [M['black_metal'], M['chrome'], M['fabric_taupe']], smooth=True, auto_smooth=True)
    # ceiling (photo 20): four recessed black slots running E-W with narrow heads aimed at the bikes, mirrors, TV and
    # the sauna glass; the glowing salt wall and the sauna's LED benches do the rest - only a faint ambient
    tl = MB()
    zc = ZC - CEIL_T
    heads = []
    for yy in (19.3, 20.4, 21.5, 22.6):
        heads += slot_x(tl, 8.6, 13.6, yy, zc, 0, 1, heads=4)
    tl.build("Gym_Slots", [M['black'], M['emit_white']])
    aims = [(x0 + 0.1, 19.4, Z0 + 0.6), (9.8, 19.6, Z0 + 0.9), (11.2, 19.8, Z0 + 0.9), (13.4, 19.6, Z0 + 0.4),
            (x0 + 0.1, 20.6, Z0 + 1.2), (10.3, 20.4, Z0 + 0.9), (12.0, 20.5, Z0 + 0.9), (13.6, 20.8, Z0 + 0.4),
            (x0 + 0.1, 21.6, Z0 + 1.6), (9.5, 22.9, Z0 + 1.4), (11.5, 21.5, Z0 + 0.4), (13.2, 21.6, Z0 + 0.6),
            (x0 + 0.2, 22.6, Z0 + 1.7), (9.5, 23.2, Z0 + 1.4), (12.2, 22.6, Z0 + 0.8), (13.6, 22.8, Z0 + 0.5)]
    head_spots("L_GymHead", heads, zc, energy=28, spot=46, blend=0.6, color=(1.0, 0.86, 0.68), targets=aims)
    room_light("L_Gym", (*GYM, Z0, ZC), energy=14, color=(1.0, 0.93, 0.85), z_off=0.3)
    add_light("L_GymTV", 'SPOT', (8.6, 22.4, zc - 0.03), 14, WARM, size=0.04, spot=math.radians(70), blend=0.6, target=(x0, 22.4, Z0 + 1.8))
    add_light("L_GymMirror", 'SPOT', (8.6, 20.6, zc - 0.03), 14, WARM, size=0.04, spot=math.radians(70), blend=0.6, target=(x0, 20.6, Z0 + 1.2))


# ================================================================== guest rooms (photos 25 + 27)
def build_guest(M):
    # ---- twin room (photo 25)
    x0, x1, y0, y1 = GUEST
    s = MB()
    floor_ceiling(s, GUEST, 0, 1)
    finish(s, GUEST, 'SE', 2)                                            # W = partition, N = glass
    s.build("Guest_Shell", [M['oak_floor'], M['ceiling'], M['white_int']])
    gd = MB(); room_details(gd, GUEST, mi_gap=0, mi_speaker=1, mi_diffuser=2, faces='WSE', speakers=((x0 + 2.7, 20.8),), diffusers=((x0 + 2.7, 18.6, 'X'),))
    gd.build("Guest_Details", [M['black'], M['white_gloss'], M['black_metal']])
    from archviz import materials as MT
    rug_esp = MT.rug("RugEspresso", (0.16, 0.10, 0.08, 1), (0.24, 0.16, 0.13, 1), pattern=True)
    grey_up = MT.fabric("BoucleGreyTaupe", (0.56, 0.52, 0.47, 1), weave=70, bump=0.3)
    rug_slab("Rug_Guest", x0 + 0.6, x0 + 4.3, 19.0, 23.0, Z0 + 0.02, rug_esp)
    # twin beds (photo 25): low grey-taupe upholstered platforms with a squared 0.7 m headboard, white linen with the
    # duvet folded back, one brown + one white euro pillow, a round boucle bolster, and a tan knit throw slung over the
    # outer foot corner and hanging down the side
    b = MB()
    for k, by in enumerate((19.6, 22.0)):
        bed(b, x0 + 1.15, by, rot=math.pi / 2, z=Z0 + 0.02, w=1.1, l=2.1, mi_frame=0, mi_linen=1, mi_pillow=1, mi_throw=1, head_h=0.72, seed=k + 1)
        cushion(b, x0 + 0.62, by + 0.05, Z0 + 0.62, w=0.44, d=0.44, t=0.13, mi=3, rot=-math.pi / 2 + 0.1 * k, upright=True, tilt=0.65)
        cushion(b, x0 + 0.70, by - 0.30, Z0 + 0.60, w=0.36, d=0.36, t=0.12, mi=1, rot=-math.pi / 2 - 0.15, upright=True, tilt=0.7)
        b.pillow(x0 + 0.98, by - 0.22, Z0 + 0.70, w=0.24, d=0.24, t=0.2, mi=4, rot=0.3)                # round bolster cushion
        sgn = -1 if k == 0 else 1
        b.drape(x0 + 1.55, x0 + 2.2, by + sgn * 0.05, by + sgn * 0.62, Z0 + 0.63, t=0.028, mi=2, sag=0.05, folds=3, seed=k + 3)
        b.rcbox(x0 + 1.9, by + sgn * 0.63, Z0 + 0.36, 0.55, 0.03, 0.55, r=0.012, mi=2, puff=0.25)      # throw hanging down the side
    b.build("Guest_Beds", [grey_up, M['linen_white'], M['throw'], M['fabric_brown'], M['fabric_taupe']], smooth=True, subsurf=1)
    ns = MB()
    ns.box(x0 + 0.05, x0 + 0.6, 20.35, 21.25, Z0 + 0.02, Z0 + 0.6, 0)
    for i in range(1, 3):
        ns.box(x0 + 0.6, x0 + 0.603, 20.37, 21.23, Z0 + 0.02 + 0.58 * i / 3 - 0.003, Z0 + 0.02 + 0.58 * i / 3 + 0.003, 1)
    ns.build("Guest_Nightstand", [M['oak_pale'], M['black']])
    lm = MB()
    lm.lathe(x0 + 0.32, 20.8, Z0 + 0.6, [(0, 0), (0.05, 0), (0.05, 0.22), (0.0, 0.22)], seg=16, mi=0)
    lm.lathe(x0 + 0.32, 20.8, Z0 + 0.78, [(0, 0.2), (0.14, 0.14), (0.19, 0.02), (0.19, 0)], seg=24, mi=1)  # dome shade
    lm.sphere((x0 + 0.32, 20.8, Z0 + 0.86), 0.025, seg=10, rings=6, mi=2)                                  # bulb
    lm.path_tube([(x0 + 0.36, 20.8, Z0 + 0.603), (x0 + 0.5, 20.9, Z0 + 0.6), (x0 + 0.6, 21.0, Z0 + 0.3), (x0 + 0.06, 21.1, Z0 + 0.1)], 0.003, seg=6, mi=3)   # cord
    carafe(lm, x0 + 0.2, 21.05, Z0 + 0.6, 4)
    books(lm, x0 + 0.42, 20.5, Z0 + 0.6, n=1, mi=5, w=0.18, d=0.13, rot=0.15)
    lm.lathe(x0 + 0.22, 20.55, Z0 + 0.6, [(0, 0), (0.05, 0), (0.06, 0.09), (0.055, 0.09), (0.05, 0.02), (0, 0.02)], seg=14, mi=6)   # small plant pot
    for k in range(9):
        a_ = 2 * math.pi * k / 9
        lm.pillow(x0 + 0.22 + 0.06 * math.cos(a_), 20.55 + 0.06 * math.sin(a_), Z0 + 0.72 + 0.02 * (k % 3), w=0.07, d=0.035, t=0.004, mi=7, rot=a_, pitch=0.6)
    lm.build("Guest_Lamp", [M['ceramic'], M['lampshade'], M['emit_warm'], M['black'], M['glass'], M['book'], M['clay'], M['leaf_plant']], smooth=True, auto_smooth=True)
    ar = MB()
    floater_canvas(ar, 19.55, 21.85, x0 + 0.02, Z0 + 1.35, Z0 + 2.45, 0, 1, along='Y', face=1)
    floater_canvas(ar, 20.4, 21.9, x1 - 0.02, Z0 + 0.95, Z0 + 2.35, 2, 3, along='Y', face=-1)
    ar.build("Guest_Art", [M['oak'], M['art_dots'], M['oak_pale'], M['art_relief']])
    # curved oak console under the relief canvas (east wall)
    cs = MB()
    pts = [(x1 - 0.06, 20.3)] + [(x1 - 0.06 - 0.5 * math.sin(math.pi * k / 12), 20.3 + 1.7 * (k / 12)) for k in range(13)]   # half-ellipse front
    cs.prism(pts, Z0 + 0.66, Z0 + 0.71, 0)
    cs.box(x1 - 0.5, x1 - 0.06, 21.05, 21.25, Z0 + 0.02, Z0 + 0.66, 0)                            # pedestal
    cs.build("Guest_Console", M['oak_pale'], smooth=True)
    dc = MB()
    vase(dc, x1 - 0.3, 21.5, Z0 + 0.71, h=0.22, r=0.08, mi=0)
    vase(dc, x1 - 0.3, 20.75, Z0 + 0.71, h=0.1, r=0.07, mi=1, style='bowl')
    books(dc, x1 - 0.32, 21.1, Z0 + 0.71, n=2, mi=2, w=0.24, d=0.18)
    dc.build("Guest_Decor", [M['ceramic'], M['ceramic_cream'], M['book']], smooth=True)
    # ceiling (photo 25): two recessed black slots along the room with heads aimed at the beds, the art and the
    # console; a soft cove line above the glass; faint ambient only
    tl = MB()
    zc = ZC - CEIL_T
    heads = slot_x(tl, x0 + 0.6, x0 + 4.6, 19.9, zc, 0, 1, heads=4) + slot_x(tl, x0 + 0.6, x0 + 4.6, 21.9, zc, 0, 1, heads=4)
    tl.build("Guest_Slots", [M['black'], M['emit_white']])
    aims = [(x0 + 0.05, 20.7, Z0 + 1.9), (x0 + 1.3, 19.6, Z0 + 0.6), (x0 + 3.0, 19.4, Z0 + 0.3), (x1 - 0.1, 20.4, Z0 + 1.6),
            (x0 + 0.05, 21.0, Z0 + 1.7), (x0 + 1.3, 22.0, Z0 + 0.6), (x0 + 3.0, 22.3, Z0 + 0.3), (x1 - 0.1, 21.6, Z0 + 1.6)]
    head_spots("L_GuestHead", heads, zc, energy=26, spot=48, blend=0.6, color=(1.0, 0.86, 0.68), targets=aims)
    cv = MB(); cove_x(cv, x0 + 0.3, x1 - 0.3, y1 - 0.06, zc - 0.012, 0, w=0.03, face=-1)
    cv.build("Guest_CoveLine", M['emit_cove'])
    wash_light("L_GuestCove", (x0 + 0.3, y1 - 0.12), (x1 - 0.3, y1 - 0.12), zc - 0.02, 8, up=True, width=0.05)
    room_light("L_Guest", (*GUEST, Z0, ZC), energy=12, color=(1.0, 0.95, 0.9), z_off=0.3)
    add_light("L_GuestLamp", 'POINT', (x0 + 0.32, 20.8, Z0 + 0.86), 7, (1.0, 0.78, 0.55), size=0.05)

    # ---- queen room (photo 27)
    x0, x1, y0, y1 = GUEST2
    s = MB()
    floor_ceiling(s, GUEST2, 0, 1)
    finish(s, GUEST2, 'S', 2)                                            # W/E partitions, N glass
    s.build("Guest2_Shell", [M['oak_floor'], M['ceiling'], M['white_int']])
    g2 = MB(); room_details(g2, GUEST2, mi_gap=0, mi_speaker=1, mi_diffuser=2, faces='S', speakers=((x0 + 1.9, 21.0),), diffusers=((x0 + 1.9, 18.6, 'X'),))
    g2.build("Guest2_Details", [M['black'], M['white_gloss'], M['black_metal']])
    rug_slab("Rug_Guest2", x0 + 0.8, x1 - 0.5, 19.4, 22.6, Z0 + 0.02, rug_esp)
    b = MB()
    bed(b, x0 + 1.3, 21.0, rot=math.pi / 2, z=Z0 + 0.02, w=1.7, l=2.1, mi_frame=0, mi_linen=1, mi_pillow=1, mi_throw=2, head_h=0.95, seed=5)
    cushion(b, x0 + 0.78, 20.6, Z0 + 0.62, w=0.5, d=0.45, t=0.13, mi=3, rot=-math.pi / 2 + 0.08, upright=True, tilt=0.62)
    cushion(b, x0 + 0.78, 21.4, Z0 + 0.62, w=0.5, d=0.45, t=0.13, mi=3, rot=-math.pi / 2 - 0.08, upright=True, tilt=0.62)
    cushion(b, x0 + 0.94, 21.0, Z0 + 0.62, w=0.55, d=0.3, t=0.12, mi=4, rot=-math.pi / 2, upright=True, tilt=0.7)
    b.build("Guest2_Bed", [M['fabric_white'], M['linen_white'], M['throw'], M['fabric_taupe'], M['fabric_sand']], smooth=True, subsurf=1)
    g2p = MB()
    carafe(g2p, x0 + 0.25, 22.6, Z0 + 0.64, 0)
    books(g2p, x0 + 0.5, 19.4, Z0 + 0.64, n=2, mi=1, w=0.2, d=0.14, rot=-0.2)
    g2p.build("Guest2_Props", [M['glass'], M['book']], smooth=True, auto_smooth=True)
    ns = MB()
    for ny in (19.55, 22.45):
        ns.box(x0 + 0.05, x0 + 0.75, ny - 0.4, ny + 0.4, Z0 + 0.02, Z0 + 0.62, 0)
        for k in range(14):                                                                       # fluted front
            yy = ny - 0.38 + 0.8 * k / 14
            ns.cylinder(x0 + 0.75, yy + 0.028, Z0 + 0.04, Z0 + 0.6, 0.022, seg=8, mi=0)
        ns.box(x0 + 0.03, x0 + 0.78, ny - 0.42, ny + 0.42, Z0 + 0.62, Z0 + 0.64, 1)
    ns.build("Guest2_Nightstands", [M['ceramic_cream'], M['brass']], smooth=True)
    lm = MB()
    for ny in (19.55, 22.45):
        bulb_lamp(lm, x0 + 0.4, ny, Z0 + 0.64, 0, 1, 2, 3, base_r=0.16, base_h=0.34, shade_r=0.26, shade_h=0.24, cord_to=(x0 + 0.06, ny + 0.3, Z0 + 0.2))
    lm.build("Guest2_Lamps", [M['ceramic_black'], M['lampshade'], M['emit_warm'], M['black']], smooth=True)
    ar = MB()
    floater_canvas(ar, 19.6, 21.15, x1 - 0.02, Z0 + 1.3, Z0 + 2.6, 0, 1, along='Y', face=-1)      # patchwork on the east partition
    for k, yy in enumerate((20.3, 20.95, 21.6)):
        floater_canvas(ar, yy - 0.2, yy + 0.2, x0 + 0.02, Z0 + 1.65, Z0 + 2.05, 0, 2 + (k % 2), along='Y', face=1)
    ar.build("Guest2_Art", [M['oak'], M['art_patch'], M['art_lines'], M['clay']])
    tl = MB()
    zc = ZC - CEIL_T
    heads = slot_x(tl, x0 + 0.5, x1 - 0.5, 20.0, zc, 0, 1, heads=3) + slot_x(tl, x0 + 0.5, x1 - 0.5, 22.0, zc, 0, 1, heads=3)
    tl.build("Guest2_Slots", [M['black'], M['emit_white']])
    aims = [(x0 + 0.05, 20.4, Z0 + 1.8), (x0 + 1.4, 21.0, Z0 + 0.6), (x1 - 0.1, 20.4, Z0 + 1.9),
            (x0 + 0.05, 21.6, Z0 + 1.8), (x0 + 1.4, 21.0, Z0 + 0.6), (x1 - 0.1, 21.6, Z0 + 1.9)]
    head_spots("L_Guest2Head", heads, zc, energy=26, spot=48, blend=0.6, color=(1.0, 0.86, 0.68), targets=aims)
    room_light("L_Guest2", (*GUEST2, Z0, ZC), energy=12, color=(1.0, 0.95, 0.9), z_off=0.3)
    for ny in (19.55, 22.45):
        add_light(f"L_Guest2Lamp_{ny:.0f}", 'POINT', (x0 + 0.4, ny, Z0 + 0.64 + 0.5), 7, (1.0, 0.78, 0.55), size=0.06)


def build(M):
    build_structure(M)
    build_master(M)
    build_bath(M)
    build_closet(M)
    build_office(M)
    build_gym(M)
    build_guest(M)
