"""Upper floor (Z_UP): family/media room, three bedrooms, guest suite + kitchenette, gallery hall, the lounge
inside the wood-slat box, and the furniture on the two roof terraces (front turf terrace, rear dining terrace).

Ownership: the exterior module builds the envelope (outer walls, glass, slabs, terrace turf / rails / parapets).
This module builds floor + ceiling finishes, interior partitions + doors, wall finish panels, furniture, decor, lights.
Detail level: shadow-gap skirtings and ceiling reveals, slot diffusers, speakers, trimmed downlights, aimed track
heads, floater-framed art, pulls / hinges / switch plates, plump upholstery from parts, styling clutter on every surface.
"""
import math, random
from .plan import *
from archviz.mesh import *
from archviz.lights import *
from archviz.parts import *
from archviz import materials as _mat

WT_IN = 0.15            # interior partition thickness
DOOR_H = 2.45
HT = WT_IN / 2          # partitions are centred on the ROOMS boundary: usable faces sit HT inside each room
PX_W = -5.6 - HT        # west-wing rooms' east face
PX_H0 = -5.6 + HT       # hall's west face
PX_H1 = 0.6 - HT        # hall's east face
PX_E = 0.6 + HT         # east rooms' (family / bed1) west face
PX_B2B = 1.0 - HT       # bed 2 en-suite's east face
PX_B2 = 1.0 + HT        # bed 2's west face (headboard wall)
Z_TERR_FRONT = Z_SOF + 0.64      # turf terrace over the living/family pavilions
Z_TERR_REAR = Z_UP + 0.04        # turf terrace on the north-arm roof
GAP = 0.006                      # shadow-gap width (ceiling reveal / skirting)


_LOCAL = {}
def _local(M):
    """Materials specific to this module (never added to the shared library)."""
    if not _LOCAL:
        _LOCAL['rug_camel_deep'] = _mat.rug("RugCamelDeep", (0.46, 0.32, 0.20, 1), (0.60, 0.44, 0.28, 1))       # photo 33
        _LOCAL['rug_plum_deep'] = _mat.rug("RugPlumDeep", (0.20, 0.09, 0.11, 1), (0.30, 0.15, 0.17, 1), pattern=True)   # photo 27
        # photo 21: honey teak (darker than the library teak under the dusk sky) and a mid-tan woven cane
        _LOCAL['teak_warm'] = _mat.wood("TeakWarm", light=(0.56, 0.36, 0.19, 1), dark=(0.40, 0.24, 0.11, 1), grain_axis='X', rough=0.5, coat=0.12)
        _LOCAL['cane_tan'] = _mat.fabric("CaneTan", (0.68, 0.50, 0.29, 1), weave=140, bump=0.7, rough=0.7)
        _LOCAL['boucle_oat'] = _mat.fabric("BoucleOat", (0.80, 0.74, 0.64, 1))
        _LOCAL['knit_oat'] = _mat.fabric("KnitOat", (0.78, 0.70, 0.56, 1), weave=30, bump=0.5, rough=0.95)
    return _LOCAL


# ------------------------------------------------------------------ helpers: room shell details
def _finish(M, name, floor_mat, faces='', wall_mat=None, ceil_mat=None, holes=(), z_ceil=None, bounds=None, gaps='WESN'):
    """Floor + ceiling finish of a room, 2 cm wall finish panels on `faces`, plus a 6 mm dark ceiling reveal and a
    12 mm shadow-gap skirting on the faces listed in `gaps` (the photos' walls float off the floor / ceiling)."""
    x0, x1, y0, y1, z0, z1 = bounds or ROOMS[name]
    z1 = z_ceil or z1
    wall_mat = wall_mat or M['white_int']
    ceil_mat = ceil_mat or M['ceiling']
    f = MB(); f.plate(x0, x1, y0, y1, z0, z0 + 0.02, holes=holes); f.build(f"{name}_floor", floor_mat)
    c = MB(); c.plate(x0, x1, y0, y1, z1 - 0.02, z1, holes=holes); c.build(f"{name}_ceiling", ceil_mat)
    if faces:
        w = MB()
        if 'W' in faces: w.box(x0, x0 + 0.02, y0, y1, z0, z1)
        if 'E' in faces: w.box(x1 - 0.02, x1, y0, y1, z0, z1)
        if 'S' in faces: w.box(x0, x1, y0, y0 + 0.02, z0, z1)
        if 'N' in faces: w.box(x0, x1, y1 - 0.02, y1, z0, z1)
        w.build(f"{name}_walls", wall_mat)
    g = MB()
    zc0, zc1 = z1 - 0.02 - GAP, z1 - 0.02          # ceiling reveal
    zs0, zs1 = z0 + 0.02, z0 + 0.032               # skirting shadow gap
    d = 0.012
    for face in gaps:
        if face == 'W':
            g.box(x0, x0 + d, y0, y1, zc0, zc1); g.box(x0, x0 + d, y0, y1, zs0, zs1)
        if face == 'E':
            g.box(x1 - d, x1, y0, y1, zc0, zc1); g.box(x1 - d, x1, y0, y1, zs0, zs1)
        if face == 'S':
            g.box(x0, x1, y0, y0 + d, zc0, zc1); g.box(x0, x1, y0, y0 + d, zs0, zs1)
        if face == 'N':
            g.box(x0, x1, y1 - d, y1, zc0, zc1); g.box(x0, x1, y1 - d, y1, zs0, zs1)
    if g.v:
        g.build(f"{name}_gaps", M['black'])


def _ceiling_gear(M, name, z, speakers=(), diffusers=(), detector=None):
    """Recessed ceiling services: 150 mm speaker grilles (slightly domed white discs), 60 x 600 mm black linear slot
    diffusers (along='X' or 'Y'), an optional smoke detector puck."""
    mb = MB()
    for (x, y) in speakers:
        mb.lathe(x, y, z - 0.02, [(0.075, 0), (0.075, -0.003), (0.05, -0.006), (0, -0.007)], seg=24, mi=0)
        mb.lathe(x, y, z - 0.02, [(0.078, 0), (0.078, -0.002), (0.075, -0.002)], seg=24, mi=1)
    for (x, y, along) in diffusers:
        if along == 'X':
            mb.box(x - 0.3, x + 0.3, y - 0.03, y + 0.03, z - 0.02 - 0.012, z - 0.02, 2)
            mb.box(x - 0.31, x + 0.31, y - 0.04, y + 0.04, z - 0.02 - 0.002, z - 0.02, 1)
        else:
            mb.box(x - 0.03, x + 0.03, y - 0.3, y + 0.3, z - 0.02 - 0.012, z - 0.02, 2)
            mb.box(x - 0.04, x + 0.04, y - 0.31, y + 0.31, z - 0.02 - 0.002, z - 0.02, 1)
    if detector:
        mb.lathe(detector[0], detector[1], z - 0.02, [(0.06, 0), (0.06, -0.02), (0.045, -0.028), (0, -0.03)], seg=20, mi=0)
    if mb.v:
        mb.build(f"{name}_ceilgear", [M['ceramic'], M['white_gloss'], M['black']], smooth=True)


def _door(mb_frame, mb_leaf, along, a0, a1, b, z0, mi_frame=0, mi_leaf=0, mi_pull=1):
    """Door in a partition: `along` 'X' -> opening spans x a0..a1 at y=b; 'Y' -> spans y a0..a1 at x=b.
    Black frame with a 20 mm reveal, oak leaf, black edge pull + two hinge lines."""
    door_frame(mb_frame, a0, a1, b, z0, z0 + DOOR_H, mi=mi_frame, w=0.05, d=WT_IN + 0.02, along=along)
    # 20 mm reveal step inside the frame
    door_frame(mb_frame, a0 + 0.02, a1 - 0.02, b, z0, z0 + DOOR_H - 0.02, mi=mi_frame, w=0.02, d=WT_IN - 0.04, along=along)
    door_leaf(mb_leaf, a0 + 0.03, a1 - 0.03, b, z0 + 0.012, z0 + DOOR_H - 0.03, mi=mi_leaf, thick=0.045, along=along)
    # edge pull (vertical black bar, 300 mm) on the latch side + hinge knuckles on the other
    zp0, zp1 = z0 + 0.95, z0 + 1.25
    if along == 'X':
        mb_leaf.box(a1 - 0.06, a1 - 0.03, b - 0.03, b + 0.03, zp0, zp1, mi_pull)
        for zh in (z0 + 0.3, z0 + 1.25, z0 + DOOR_H - 0.35):
            mb_leaf.box(a0 + 0.026, a0 + 0.034, b - 0.024, b + 0.024, zh, zh + 0.1, mi_pull)
    else:
        mb_leaf.box(b - 0.03, b + 0.03, a1 - 0.06, a1 - 0.03, zp0, zp1, mi_pull)
        for zh in (z0 + 0.3, z0 + 1.25, z0 + DOOR_H - 0.35):
            mb_leaf.box(b - 0.024, b + 0.024, a0 + 0.026, a0 + 0.034, zh, zh + 0.1, mi_pull)


def _switch(mb, x, y, z, along='X', mi=0, face=1):
    """86 x 86 mm switch plate on a wall (along='X': wall runs along X at y; face = side it projects to)."""
    if along == 'X':
        mb.rbox(x - 0.043, x + 0.043, min(y, y + face * 0.008), max(y, y + face * 0.008), z - 0.043, z + 0.043, r=0.004, mi=mi, seg=2)
    else:
        mb.rbox(min(y, y + face * 0.008), max(y, y + face * 0.008), x - 0.043, x + 0.043, z - 0.043, z + 0.043, r=0.004, mi=mi, seg=2)


def _floater(mb, a0, a1, b, z0, z1, along='X', face=-1, mi_frame=0, mi_canvas=1, deep=0.04):
    """Floater-framed canvas: 30 mm frame bars standing `deep` off the wall, the 4 mm-deep canvas set 8 mm inside them."""
    fw = 0.03
    if along == 'X':
        y0, y1 = (b, b + face * deep) if face > 0 else (b + face * deep, b)
        mb.box(a0, a1, y0, y1, z0, z0 + fw, mi_frame); mb.box(a0, a1, y0, y1, z1 - fw, z1, mi_frame)
        mb.box(a0, a0 + fw, y0, y1, z0, z1, mi_frame); mb.box(a1 - fw, a1, y0, y1, z0, z1, mi_frame)
        cy0, cy1 = (b + face * (deep - 0.012), b + face * (deep - 0.008))
        mb.box(a0 + fw + 0.008, a1 - fw - 0.008, min(cy0, cy1), max(cy0, cy1), z0 + fw + 0.008, z1 - fw - 0.008, mi_canvas)
    else:
        x0, x1 = (b, b + face * deep) if face > 0 else (b + face * deep, b)
        mb.box(x0, x1, a0, a1, z0, z0 + fw, mi_frame); mb.box(x0, x1, a0, a1, z1 - fw, z1, mi_frame)
        mb.box(x0, x1, a0, a0 + fw, z0, z1, mi_frame); mb.box(x0, x1, a1 - fw, a1, z0, z1, mi_frame)
        cx0, cx1 = (b + face * (deep - 0.012), b + face * (deep - 0.008))
        mb.box(min(cx0, cx1), max(cx0, cx1), a0 + fw + 0.008, a1 - fw - 0.008, z0 + fw + 0.008, z1 - fw - 0.008, mi_canvas)


def _downlights(M, name, pts, z):
    d = MB(); downlights(d, pts, z - 0.02); d.build(f"{name}_downlights", [M['emit_down'], M['black']])


def _track(mb, a0, a1, b, z, targets, along='X', mi_track=0, mi_head=0, mi_lens=1):
    """Recessed black track with cylindrical heads that swivel toward `targets` (list of (x,y,z))."""
    if along == 'X':
        mb.box(a0, a1, b - 0.03, b + 0.03, z - 0.012, z + 0.02, mi_track)
    else:
        mb.box(b - 0.03, b + 0.03, a0, a1, z - 0.012, z + 0.02, mi_track)
    n = len(targets)
    for i, tgt in enumerate(targets):
        t = a0 + (a1 - a0) * (i + 0.5) / n
        p0 = Vector((t, b, z - 0.012)) if along == 'X' else Vector((b, t, z - 0.012))
        d = (Vector(tgt) - p0).normalized()
        p1 = p0 + d * 0.11
        mb.tube(tuple(p0), tuple(p1), 0.028, 0.03, seg=12, mi=mi_head)
        mb.tube(tuple(p1), tuple(p1 + d * 0.004), 0.024, 0.024, seg=12, mi=mi_lens)


def _spot(name, loc, target, energy=40, spot=70):
    add_light(name, 'SPOT', loc, energy, WARM_SOFT, size=0.06, spot=math.radians(spot), blend=0.6, target=target)


def _rug(M, name, x0, x1, y0, y1, z, mat):
    r = MB(); r.rbox(x0, x1, y0, y1, z, z + 0.012, r=0.006, seg=2)
    return r.build(f"Rug_{name}", mat, smooth=True)


# ------------------------------------------------------------------ helpers: props
def _mushroom_lamp(mb, x, y, z, mi=0, h=0.5, r=0.17, mi_bulb=None):
    mb.lathe(x, y, z, [(0, 0), (0.06, 0), (0.05, 0.02), (0.022, 0.05), (0.022, h * 0.62), (r * 0.7, h * 0.66),
                       (r, h * 0.78), (r * 0.8, h * 0.92), (r * 0.35, h), (0, h)], seg=24, mi=mi)
    if mi_bulb is not None:
        mb.sphere((x, y, z + h * 0.7), 0.03, seg=12, rings=8, mi=mi_bulb)


def _lamp(mb, x, y, z, mi_base, mi_shade, mi_bulb, mi_cord, cord_to=None, **kw):
    """Table lamp from parts + a visible bulb inside the shade + a cord trailing to `cord_to` (x,y,z)."""
    lamp(mb, x, y, z, mi_base=mi_base, mi_shade=mi_shade, **kw)
    bh = kw.get('base_h', 0.32); sh = kw.get('shade_h', 0.25)
    mb.sphere((x, y, z + bh + 0.08 + sh * 0.45), 0.028, seg=12, rings=8, mi=mi_bulb)
    if cord_to is not None:
        mb.path_tube([(x + 0.05, y, z + 0.01), ((x + cord_to[0]) / 2, (y + cord_to[1]) / 2, z + 0.005), cord_to], 0.003, seg=6, mi=mi_cord)


def _carafe(mb, x, y, z, mi_glass, mi_water=None):
    mb.lathe(x, y, z, [(0, 0), (0.045, 0), (0.05, 0.02), (0.05, 0.14), (0.03, 0.2), (0.024, 0.24), (0.026, 0.25), (0, 0.25)], seg=18, mi=mi_glass)
    mb.lathe(x + 0.11, y + 0.02, z, [(0, 0), (0.03, 0), (0.033, 0.005), (0.036, 0.09), (0, 0.09)], seg=16, mi=mi_glass)   # tumbler
    if mi_water is not None:
        mb.lathe(x, y, z + 0.004, [(0, 0), (0.046, 0), (0.046, 0.09), (0, 0.09)], seg=18, mi=mi_water)


def _tray(mb, x, y, z, w, d, mi, rot=0.0):
    mb.rcbox(x, y, z + 0.006, w, d, 0.012, r=0.005, mi=mi, rot=rot, seg=2)
    px, py = rot2(x, y - d / 2 + 0.01, x, y, rot); mb.cbox(px, py, z + 0.025, w, 0.02, 0.05, mi, rot)
    px, py = rot2(x, y + d / 2 - 0.01, x, y, rot); mb.cbox(px, py, z + 0.025, w, 0.02, 0.05, mi, rot)
    px, py = rot2(x - w / 2 + 0.01, y, x, y, rot); mb.cbox(px, py, z + 0.025, 0.02, d, 0.05, mi, rot)
    px, py = rot2(x + w / 2 - 0.01, y, x, y, rot); mb.cbox(px, py, z + 0.025, 0.02, d, 0.05, mi, rot)


def _candle(mb, x, y, z, mi_wax, mi_flame, r=0.035, h=0.08):
    mb.cylinder(x, y, z, z + h, r, seg=16, mi=mi_wax)
    mb.cylinder(x, y, z + h, z + h + 0.03, 0.006, 0.001, seg=8, mi=mi_flame)


def _laptop(mb, x, y, z, mi_body, mi_screen, rot=0.0):
    mb.rcbox(x, y, z + 0.008, 0.31, 0.22, 0.016, r=0.006, mi=mi_body, rot=rot, seg=2)
    # lid open ~105 deg: a thin hexa hinged at the back edge
    c, s = math.cos(rot), math.sin(rot)
    def P(px, py, pz):
        return (x + px * c - py * s, y + px * s + py * c, z + pz)
    a = math.radians(105)
    dy, dz = 0.21 * math.cos(a), 0.21 * math.sin(a)
    mb.hexa([P(-0.155, 0.11, 0.016), P(0.155, 0.11, 0.016), P(0.155, 0.11 + dy, 0.016 + dz), P(-0.155, 0.11 + dy, 0.016 + dz),
             P(-0.155, 0.118, 0.016), P(0.155, 0.118, 0.016), P(0.155, 0.118 + dy, 0.016 + dz), P(-0.155, 0.118 + dy, 0.016 + dz)], mi_body)
    mb.hexa([P(-0.145, 0.111, 0.024), P(0.145, 0.111, 0.024), P(0.145, 0.111 + dy * 0.95, 0.024 + dz * 0.95), P(-0.145, 0.111 + dy * 0.95, 0.024 + dz * 0.95),
             P(-0.145, 0.1105, 0.024), P(0.145, 0.1105, 0.024), P(0.145, 0.1105 + dy * 0.95, 0.024 + dz * 0.95), P(-0.145, 0.1105 + dy * 0.95, 0.024 + dz * 0.95)], mi_screen)


def _pen_cup(mb, x, y, z, mi_cup, mi_pen):
    mb.lathe(x, y, z, [(0, 0), (0.04, 0), (0.042, 0.1), (0.036, 0.1), (0.036, 0.01), (0, 0.01)], seg=16, mi=mi_cup)
    rng = random.Random(int(x * 10 + y))
    for i in range(4):
        a = rng.uniform(0, 6.28); r = rng.uniform(0.0, 0.025)
        mb.tube((x + r * math.cos(a), y + r * math.sin(a), z + 0.02), (x + r * math.cos(a) * 1.8, y + r * math.sin(a) * 1.8, z + 0.16), 0.004, 0.004, seg=6, mi=mi_pen)


def _lantern(mb, x, y, z, mi_frame, mi_glass, mi_candle, mi_flame, w=0.22, h=0.42):
    mb.frame(x - w / 2, x + w / 2, y - w / 2, y + w / 2, z, z + h, 0.012, mi=mi_frame, axis='Z')
    mb.box(x - w / 2, x + w / 2, y - w / 2, y + w / 2, z, z + 0.012, mi_frame)
    mb.box(x - w / 2, x + w / 2, y - w / 2, y + w / 2, z + h - 0.012, z + h, mi_frame)
    for (sx, sy) in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        if sx:
            mb.box(x + sx * (w / 2 - 0.008), x + sx * (w / 2 - 0.004), y - w / 2 + 0.012, y + w / 2 - 0.012, z + 0.012, z + h - 0.012, mi_glass)
        else:
            mb.box(x - w / 2 + 0.012, x + w / 2 - 0.012, y + sy * (w / 2 - 0.008), y + sy * (w / 2 - 0.004), z + 0.012, z + h - 0.012, mi_glass)
    mb.cylinder(x, y, z + h, z + h + 0.03, 0.02, seg=10, mi=mi_frame)                       # top ring
    _candle(mb, x, y, z + 0.012, mi_candle, mi_flame, r=0.04, h=h * 0.4)


def _agave(mb, x, y, z, mi_pot, mi_leaf, n=18, seed=1, size=0.55):
    mb.lathe(x, y, z, [(0, 0), (0.24, 0), (0.28, 0.5), (0.25, 0.5), (0.25, 0.47), (0, 0.47)], seg=24, mi=mi_pot)
    rng = random.Random(seed)
    for i in range(n):
        a = 2 * math.pi * i / n + rng.uniform(-0.2, 0.2)
        tilt = rng.uniform(0.35, 1.1)
        L = size * rng.uniform(0.7, 1.0)
        tip = (x + L * math.cos(a) * math.sin(tilt), y + L * math.sin(a) * math.sin(tilt), z + 0.47 + L * math.cos(tilt))
        mid = ((x + tip[0]) / 2, (y + tip[1]) / 2, z + 0.47 + L * 0.6)
        secs = []
        for k, p in enumerate(((x, y, z + 0.45), mid, tip)):
            w = (0.045, 0.03, 0.003)[k]
            secs.append([(p[0] + w * math.cos(a + math.pi / 2) * math.cos(t), p[1] + w * math.sin(a + math.pi / 2) * math.cos(t), p[2] + 0.008 * math.sin(t)) for t in [2 * math.pi * j / 8 for j in range(8)]])
        mb.sweep(secs, mi_leaf)


def _towel(mb, x, y, z, mi, w=0.3, d=0.2, rot=0.0, folded=2):
    for i in range(folded):
        mb.rcbox(x, y, z + 0.02 + i * 0.04, w - i * 0.01, d, 0.04, r=0.015, mi=mi, rot=rot + i * 0.02, seg=2)


def _bottles(mb, x, y, z, mi_a, mi_b, n=3):
    rng = random.Random(int(x * 7 + y * 3))
    for i in range(n):
        bx, by = x + i * 0.07, y + rng.uniform(-0.02, 0.02)
        h = rng.uniform(0.14, 0.2)
        mb.lathe(bx, by, z, [(0, 0), (0.025, 0), (0.027, h - 0.03), (0.012, h - 0.02), (0.012, h), (0, h)], seg=12, mi=mi_a if i % 2 else mi_b)


def _bulb_floor_lamp(mb, x, y, z, mi_metal, mi_shade, mi_bulb, h=1.55, shade_r=0.2):
    mb.cylinder(x, y, z, z + 0.012, 0.15, seg=20, mi=mi_metal)
    mb.cylinder(x, y, z, z + h, 0.012, seg=10, mi=mi_metal)
    mb.lathe(x, y, z + h - 0.1, [(shade_r * 0.9, 0), (shade_r, 0.02), (shade_r, 0.28), (shade_r * 0.9, 0.3), (shade_r * 0.88, 0.3), (shade_r * 0.88, 0.02)], seg=24, mi=mi_shade)
    mb.sphere((x, y, z + h + 0.03), 0.032, seg=12, rings=8, mi=mi_bulb)


def _round_mirror(mb, x, y, z, r, axis='X', mi_frame=0, mi_mirror=1, seg=48):
    """Round mirror on a wall whose normal is +axis: 20 mm deep black frame, 6 mm glass set into it."""
    def circle(rr, off):
        pts = []
        for i in range(seg):
            a = 2 * math.pi * i / seg
            if axis == 'X':
                pts.append((x + off, y + rr * math.cos(a), z + rr * math.sin(a)))
            else:
                pts.append((x + rr * math.cos(a), y + off, z + rr * math.sin(a)))
        return pts
    mb.sweep([circle(r + 0.02, 0.0), circle(r + 0.02, 0.02)], mi_frame)
    mb.sweep([circle(r + 0.02, 0.02), circle(r, 0.02)], mi_frame, caps=False)
    mb.sweep([circle(r, 0.012), circle(r, 0.018)], mi_mirror)


def _fluted_nightstand(mb, x, y, z, w=0.62, d=0.45, h=0.55, mi=0, mi_top=None, rot=0.0):
    """Box with vertical grooves on the front face (photo 27)."""
    mi_top = mi if mi_top is None else mi_top
    mb.cbox(x, y, z + h / 2, w, d, h, mi, rot)
    mb.cbox(x, y, z + h + 0.01, w + 0.02, d + 0.02, 0.02, mi_top, rot)
    n = int(w / 0.04)
    for i in range(n):
        lx = -w / 2 + 0.02 + i * 0.04
        px, py = rot2(x + lx, y - d / 2 - 0.008, x, y, rot)
        mb.cbox(px, py, z + h / 2 - 0.01, 0.018, 0.016, h - 0.06, mi, rot)


def _nightstand(mb, x, y, z, w=0.55, d=0.5, h=0.5, mi=0, mi_gap=1, rot=0.0, drawers=2, floating=False):
    """Nightstand with 3 mm drawer reveals on its front (front = its own -Y)."""
    if floating:
        mb.cbox(x, y, z + h - 0.12, w, d, 0.24, mi, rot)
        zs = [z + h - 0.12]
    else:
        mb.cbox(x, y, z + h / 2, w, d, h, mi, rot)
        zs = [z + 0.03 + (h - 0.06) * (i + 1) / drawers for i in range(drawers - 1)]
        for zz in zs:
            px, py = rot2(x, y - d / 2 - 0.001, x, y, rot)
            mb.cbox(px, py, zz, w - 0.02, 0.004, 0.003, mi_gap, rot)
    px, py = rot2(x, y - d / 2 - 0.001, x, y, rot)
    mb.cbox(px, py, z + h - 0.03, w - 0.02, 0.004, 0.003, mi_gap, rot)          # top reveal
    for sx in (-1, 1):
        px, py = rot2(x + sx * (w / 2 - 0.01), y - d / 2 - 0.001, x, y, rot)
        mb.cbox(px, py, z + h / 2, 0.003, 0.004, h - 0.02, mi_gap, rot)


def _books_row(mb, x, y, z, n, mi_list, rot=0.0, along='X'):
    """A row of upright books with varied heights / thicknesses."""
    rng = random.Random(int(abs(x * 13 + y * 7)))
    off = 0.0
    for i in range(n):
        t = rng.uniform(0.018, 0.045); h = rng.uniform(0.2, 0.3); d = rng.uniform(0.15, 0.22)
        mi = mi_list[i % len(mi_list)]
        if along == 'X':
            px, py = rot2(x + off + t / 2, y, x, y, rot); mb.cbox(px, py, z + h / 2, t, d, h, mi, rot)
        else:
            px, py = rot2(x, y + off + t / 2, x, y, rot); mb.cbox(px, py, z + h / 2, d, t, h, mi, rot)
        off += t + 0.002


# ------------------------------------------------------------------ helpers: angled timber, Jeanneret chairs, tufting, slot lights
def _plank(mb, p0, p1, w, t, mi=0, up=(0, 0, 1)):
    """Straight timber member between two 3-D points: `w` across (horizontal-ish), `t` thick (along the local up)."""
    p0, p1 = Vector(p0), Vector(p1)
    d = (p1 - p0).normalized()
    side = d.cross(Vector(up))
    if side.length < 1e-6:
        side = d.cross(Vector((1, 0, 0)))
    side.normalize()
    n = side.cross(d).normalized()
    a, b = side * (w / 2), n * (t / 2)
    mb.hexa([tuple(p0 - a - b), tuple(p0 + a - b), tuple(p0 + a + b), tuple(p0 - a + b),
             tuple(p1 - a - b), tuple(p1 + a - b), tuple(p1 + a + b), tuple(p1 - a + b)], mi)


def _jeanneret_chair(mb, x, y, rot=0.0, z=0.0, mi_wood=0, mi_cane=1, w=0.52, d=0.52, arms=True, seat_h=0.43):
    """Pierre Jeanneret 'Committee' / compass chair (photos 21 / 26 / 30): on each side a front leg that runs from the
    floor up to the armrest and a rear leg that meets it at seat level (the inverted-V 'compass'), a raked back post
    from the rear of the seat rail, flat teak arms, a teak-framed woven-cane seat and a raked cane back.
    Faces its own -Y; `rot` about (x, y)."""
    def P(cx, cy, cz):
        px, py = rot2(x + cx, y + cy, x, y, rot)
        return (px, py, z + cz)
    def plank(a, b, ww, tt, mi_):
        _plank(mb, P(*a), P(*b), ww, tt, mi_)
    hw, hd = w / 2 - 0.02, d / 2
    lt = 0.032                                   # leg thickness (across the chair)
    arm_z = 0.64 if arms else seat_h + 0.02
    back_top = 0.86
    for sx in (-1, 1):
        X = sx * hw
        # front leg: floor -> armrest, raked back a little
        plank((X, -hd + 0.10, 0.0), (X, -hd + 0.17, arm_z), lt, 0.055, mi_wood)
        # rear leg: floor (behind the seat) -> meets the front leg at seat level = the compass apex
        plank((X, hd + 0.04, 0.0), (X, -hd + 0.15, seat_h - 0.05), lt, 0.05, mi_wood)
        # seat side rail
        plank((X, -hd + 0.06, seat_h - 0.03), (X, hd - 0.08, seat_h - 0.03), lt, 0.05, mi_wood)
        # raked back post from the rear of the side rail
        plank((X, hd - 0.10, seat_h - 0.05), (X, hd + 0.01, back_top), lt, 0.05, mi_wood)
        if arms:
            plank((X, -hd + 0.10, arm_z), (X, hd - 0.02, arm_z + 0.005), 0.06, 0.028, mi_wood)
    # front + rear seat rails and the cane seat inside them
    plank((-hw, -hd + 0.06, seat_h - 0.03), (hw, -hd + 0.06, seat_h - 0.03), 0.05, lt, mi_wood)
    plank((-hw, hd - 0.08, seat_h - 0.03), (hw, hd - 0.08, seat_h - 0.03), 0.05, lt, mi_wood)
    mb.hexa([P(-hw + 0.01, -hd + 0.08, seat_h - 0.02), P(hw - 0.01, -hd + 0.08, seat_h - 0.02), P(hw - 0.01, hd - 0.10, seat_h - 0.02), P(-hw + 0.01, hd - 0.10, seat_h - 0.02),
             P(-hw + 0.01, -hd + 0.08, seat_h - 0.005), P(hw - 0.01, -hd + 0.08, seat_h - 0.005), P(hw - 0.01, hd - 0.10, seat_h - 0.005), P(-hw + 0.01, hd - 0.10, seat_h - 0.005)], mi_cane)
    # back: two rails between the posts + a cane panel, following the posts' rake
    def on_post(t):                                # point on the back-post line (t 0..1)
        y0_, z0_ = hd - 0.10, seat_h - 0.05
        y1_, z1_ = hd + 0.01, back_top
        return y0_ + (y1_ - y0_) * t, z0_ + (z1_ - z0_) * t
    yb0, zb0 = on_post(0.42); yb1, zb1 = on_post(0.97)
    plank((-hw, yb0, zb0), (hw, yb0, zb0), 0.045, lt, mi_wood)
    plank((-hw, yb1, zb1), (hw, yb1, zb1), 0.045, lt, mi_wood)
    # cane back panel as a thin plank spanning the two rails
    mb.hexa([P(-hw + 0.01, yb0 - 0.006, zb0), P(hw - 0.01, yb0 - 0.006, zb0), P(hw - 0.01, yb0 + 0.006, zb0), P(-hw + 0.01, yb0 + 0.006, zb0),
             P(-hw + 0.01, yb1 - 0.006, zb1), P(hw - 0.01, yb1 - 0.006, zb1), P(hw - 0.01, yb1 + 0.006, zb1), P(-hw + 0.01, yb1 + 0.006, zb1)], mi_cane)


def _teak_table(mb, x, y, z, L=3.0, W=1.1, h=0.74, top_t=0.06, mi=0, rot=0.0, planks=4):
    """Thick teak dining table (photo 21): a 60 mm top of `planks` boards with 5 mm gaps and breadboard ends on two
    A-frame ends of angled planks with a stretcher."""
    def P(cx, cy, cz):
        px, py = rot2(x + cx, y + cy, x, y, rot)
        return (px, py, z + cz)
    pw = (W - (planks - 1) * 0.005) / planks
    for i in range(planks):
        cy = -W / 2 + pw / 2 + i * (pw + 0.005)
        px, py = rot2(x, y + cy, x, y, rot)
        mb.cbox(px, py, z + h - top_t / 2, L - 0.24, pw, top_t, mi, rot)
    for sx in (-1, 1):
        px, py = rot2(x + sx * (L / 2 - 0.06), y, x, y, rot)
        mb.cbox(px, py, z + h - top_t / 2, 0.12, W, top_t, mi, rot)                       # breadboard ends
        ex = sx * (L / 2 - 0.42)
        for sy in (-1, 1):                                                                # A-frame legs
            _plank(mb, P(ex, sy * (W / 2 - 0.12), 0.0), P(ex, sy * 0.10, h - top_t), 0.09, 0.05, mi)
        _plank(mb, P(ex, -W / 2 + 0.14, 0.06), P(ex, W / 2 - 0.14, 0.06), 0.07, 0.05, mi)  # foot bar
        _plank(mb, P(ex - sx * 0.02, -0.14, h - top_t - 0.05), P(ex - sx * 0.02, 0.14, h - top_t - 0.05), 0.07, 0.05, mi)
    _plank(mb, P(-(L / 2 - 0.42), 0, 0.30), P((L / 2 - 0.42), 0, 0.30), 0.06, 0.06, mi)   # stretcher


def _tufted_sofa(mb, x, y, w, d, rot=0.0, z=0.0, mi=0, mi_pillow=None, seat_h=0.43, back_h=0.72, biscuit=0.30,
                 arm_end=None, pillows=()):
    """Biscuit-tufted low sectional piece (photo 30): a plinth base, the seat a grid of plump square tufts, the back a
    row of standing tufts along its +Y edge; optional arm ('L' = at -X end, 'R' = at +X end) as a tufted bolster.
    `pillows` = list of (local x, size, mi) loose pillows leaning on the back."""
    mi_pillow = mi if mi_pillow is None else mi_pillow
    def R(cx, cy, cz, sx, sy, sz, mi_, r=0.05, puff=0.0):
        px, py = rot2(x + cx, y + cy, x, y, rot)
        mb.rcbox(px, py, z + cz, sx, sy, sz, r, mi_, rot, puff=puff)
    hw, hd = w / 2, d / 2
    base_h = seat_h - 0.17
    R(0, 0, 0.03 + (base_h - 0.03) / 2, w, d, base_h - 0.03, mi, r=0.03)                  # base
    R(0, 0, 0.015, w - 0.12, d - 0.12, 0.03, mi, r=0.01)                                  # plinth shadow
    back_d = 0.24
    seat_d = d - back_d
    # one continuous seat slab with the tufts as shallow pillows on top: the photo's biscuits are soft squares
    # separated by a seam, not a heap of balloons
    R(0, -back_d / 2, base_h + 0.06, w - 0.01, seat_d - 0.01, 0.12, mi, r=0.03)
    nx = max(1, round(w / biscuit)); ny = max(1, round(seat_d / biscuit))
    bx = (w - 0.012 * (nx - 1)) / nx; by = (seat_d - 0.012 * (ny - 1)) / ny
    for i in range(nx):
        for j in range(ny):
            cx = -hw + bx / 2 + i * (bx + 0.012)
            cy = -hd + by / 2 + j * (by + 0.012)
            R(cx, cy, base_h + 0.135, bx - 0.006, by - 0.006, 0.07, mi, r=0.03, puff=0.16)
    nb = max(1, round(w / biscuit))
    bw = (w - 0.012 * (nb - 1)) / nb
    R(0, hd - back_d / 2 + 0.02, seat_h + (back_h - seat_h) / 2, w - 0.01, back_d - 0.06, back_h - seat_h + 0.02, mi, r=0.04)
    for i in range(nb):
        cx = -hw + bw / 2 + i * (bw + 0.012)
        R(cx, hd - back_d / 2 - 0.035, seat_h + (back_h - seat_h) / 2, bw - 0.006, 0.09, back_h - seat_h - 0.02, mi, r=0.03, puff=0.16)
    if arm_end in ('L', 'R'):
        sx = -1 if arm_end == 'L' else 1
        R(sx * (hw + 0.13), 0.0, (seat_h + 0.17) / 2, 0.26, d, seat_h + 0.17, mi, r=0.07, puff=0.12)
    for (lx, size, mip) in pillows:
        px, py = rot2(x + lx, y + hd - back_d - 0.10, x, y, rot)
        mb.pillow(px, py, z + seat_h + 0.20, size, size, 0.15, mip, rot=rot + 0.05 * (1 if lx > 0 else -1), pitch=math.pi / 2 - 0.35)


def _slot_lights(mb, pts, z, mi_black=0, mi_lens=1, along='X', L=0.9):
    """Recessed black linear slot lights (photos 30 / 33): a 40 x L mm black trough 30 mm deep with a warm lens at
    its bottom; the actual illumination comes from the spot lights placed by _down_spots."""
    for (x, y) in pts:
        if along == 'X':
            mb.box(x - L / 2, x + L / 2, y - 0.02, y + 0.02, z - 0.03, z + 0.001, mi_black)
            mb.box(x - L / 2 + 0.01, x + L / 2 - 0.01, y - 0.012, y + 0.012, z - 0.03, z - 0.028, mi_lens)
        else:
            mb.box(x - 0.02, x + 0.02, y - L / 2, y + L / 2, z - 0.03, z + 0.001, mi_black)
            mb.box(x - 0.012, x + 0.012, y - L / 2 + 0.01, y + L / 2 - 0.01, z - 0.03, z - 0.028, mi_lens)


def _down_spots(name, pts, z, energy=28.0, spot=85, blend=0.7):
    """A downward spot at every fixture position: this is what draws the light pools + wall scallops."""
    for i, (x, y) in enumerate(pts):
        add_light(f"{name}_{i}", 'SPOT', (x, y, z - 0.04), energy, WARM_SOFT, size=0.05, spot=math.radians(spot), blend=blend)


def _cove(M, name, x0, x1, y0, y1, z, mi_emit, sides='WESN', w=0.07, strength=None):
    """Perimeter ceiling cove: a thin emissive strip along the listed sides just below the ceiling (soft wash)."""
    mb = MB()
    if 'W' in sides: mb.box(x0, x0 + w, y0, y1, z - 0.012, z - 0.006)
    if 'E' in sides: mb.box(x1 - w, x1, y0, y1, z - 0.012, z - 0.006)
    if 'S' in sides: mb.box(x0, x1, y0, y0 + w, z - 0.012, z - 0.006)
    if 'N' in sides: mb.box(x0, x1, y1 - w, y1, z - 0.012, z - 0.006)
    mb.build(f"{name}_cove", mi_emit)


# ------------------------------------------------------------------ partitions + doors
def build_partitions(M):
    """Interior walls of the upper floor with door openings; doors get black frames + reveals, pale-oak leaves with
    edge pulls + hinges; switch plates beside every door."""
    z0, z1 = Z_UP, Z_UPC
    p = MB()
    doors = []          # (along, a0, a1, b)
    p.wall('Y', UP_Y0 + 0.4, MY1 - 0.4, -5.6 - HT, -5.6 + HT, z0, z1,
           holes=[(6.6, 7.55, z0, z0 + DOOR_H), (11.2, 12.15, z0, z0 + DOOR_H), (15.2, 16.15, z0, z0 + DOOR_H)])
    doors += [('Y', 6.6, 7.55, -5.6), ('Y', 11.2, 12.15, -5.6), ('Y', 15.2, 16.15, -5.6)]
    p.wall('X', MX0 + 0.4, -5.6, 9.0 - HT, 9.0 + HT, z0, z1)
    p.wall('X', MX0 + 0.4, -5.6, 14.0 - HT, 14.0 + HT, z0, z1)
    p.wall('Y', 4.0, 17.8, 0.6 - HT, 0.6 + HT, z0, z1,
           holes=[(7.4, 8.35, z0, z0 + DOOR_H), (16.4, 17.35, z0, z0 + DOOR_H)])
    doors += [('Y', 7.4, 8.35, 0.6), ('Y', 16.4, 17.35, 0.6)]
    p.wall('X', 0.6, MX1 - 0.4, 11.0, 11.2, z0, z1)
    p.wall('X', -5.6, MX1 - 0.4, 17.8, 18.0, z0, z1, holes=[(-1.2, -0.25, z0, z0 + DOOR_H)])
    doors += [('X', -1.2, -0.25, 17.9)]
    p.wall('Y', 18.0, MY1 - 0.4, 1.0 - HT, 1.0 + HT, z0, z1, holes=[(22.4, 23.35, z0, z0 + DOOR_H)])
    doors += [('Y', 22.4, 23.35, 1.0)]
    p.wall('X', BOX_X0, BOX_X1, 4.0 - HT, 4.0 + HT, z0, z1, holes=[(-0.6, 1.6, z0, z0 + 2.6)])
    p.build("Up_Partitions", M['white_int'])
    fr, lf, sw = MB(), MB(), MB()
    for (along, a0, a1, b) in doors:
        _door(fr, lf, along, a0, a1, b, z0)
        # switch plates 1.1 m up, 150 mm past the latch side, on both faces of the partition
        if along == 'Y':
            _switch(sw, a1 + 0.2, b - HT, z0 + 1.1, along='Y', mi=0, face=-1)
            _switch(sw, a1 + 0.2, b + HT, z0 + 1.1, along='Y', mi=0, face=1)
        else:
            _switch(sw, a1 + 0.2, b - HT, z0 + 1.1, along='X', mi=0, face=-1)
            _switch(sw, a1 + 0.2, b + HT, z0 + 1.1, along='X', mi=0, face=1)
    fr.build("Up_DoorFrames", M['frame'])
    lf.build("Up_DoorLeaves", [M['oak_pale'], M['black_metal']])
    sw.build("Up_Switches", M['white_gloss'], smooth=True)
    # black reveal around the wide opening into the wood box
    rv = MB(); rv.frame(-0.62, 1.62, 4.0 - HT - 0.01, 4.0 + HT + 0.01, z0, z0 + 2.62, 0.02, mi=0, axis='Y')
    rv.build("Up_BoxReveal", M['frame'])


# ------------------------------------------------------------------ rooms
def build_upfamily(M):
    x0, x1, y0, y1, z0, z1 = ROOMS['upfamily']
    x0 = PX_E
    _finish(M, 'upfamily', M['oak_floor'], faces='', bounds=(x0, x1, y0, y1, z0, z1), gaps='WSN')
    _ceiling_gear(M, 'upfamily', z1, speakers=[(2.2, 5.2), (6.0, 5.2), (2.2, 9.8), (6.0, 9.8)],
                  diffusers=[(4.2, 4.5, 'X'), (4.2, 10.6, 'X')], detector=(1.6, 7.6))
    # free-standing grey travertine TV pier: 15 mm shadow gaps top and bottom, TV with a 5 mm bezel, soundbar
    pier = MB()
    px0, px1, py0, py1 = 2.6, 5.8, 6.35, 6.85
    pier.box(px0, px1, py0, py1, z0 + 0.035, z1 - 0.035, 0)
    pier.box(px0 + 0.015, px1 - 0.015, py0 + 0.015, py1 - 0.015, z0 + 0.02, z0 + 0.035, 2)     # bottom shadow gap
    pier.box(px0 + 0.015, px1 - 0.015, py0 + 0.015, py1 - 0.015, z1 - 0.035, z1 - 0.02, 2)     # top shadow gap
    pier.box(px0 + 0.25, px1 - 0.25, py1, py1 + 0.42, z0 + 0.06, z0 + 0.5, 1)                   # low oak cabinet
    pier.box(px0 + 0.25, px1 - 0.25, py1, py1 + 0.42, z0 + 0.02, z0 + 0.06, 2)                  # toe-kick shadow
    for gx in (px0 + 0.25 + (px1 - px0 - 0.5) / 3, px0 + 0.25 + 2 * (px1 - px0 - 0.5) / 3):
        pier.box(gx - 0.002, gx + 0.002, py1 + 0.42, py1 + 0.424, z0 + 0.07, z0 + 0.49, 2)      # door gaps
    # open display niche (photo 30): oak back + cheeks, an LED strip tucked under the shelf above, a few objects inside
    pier.box(px0 + 0.25, px1 - 0.25, py1, py1 + 0.03, z0 + 0.5, z0 + 0.82, 1)                    # back (against the pier)
    pier.box(px0 + 0.25, px0 + 0.27, py1, py1 + 0.42, z0 + 0.5, z0 + 0.82, 1)                    # cheeks
    pier.box(px1 - 0.27, px1 - 0.25, py1, py1 + 0.42, z0 + 0.5, z0 + 0.82, 1)
    pier.box(px0 + 0.27, px1 - 0.27, py1 + 0.03, py1 + 0.10, z0 + 0.80, z0 + 0.815, 3)           # LED strip under the shelf
    books(pier, px0 + 0.75, py1 + 0.22, z0 + 0.5, n=2, mi=5, rot=0.0, w=0.3, d=0.22)
    vase(pier, px1 - 0.9, py1 + 0.22, z0 + 0.5, h=0.12, r=0.09, mi=6, style='bowl')
    pier.box(px0 + 0.25, px1 - 0.25, py1, py1 + 0.42, z0 + 0.82, z0 + 0.85, 1)                   # niche shelf
    pier.box(px0 + 0.45, px1 - 0.45, py1, py1 + 0.03, z0 + 1.25, z0 + 2.35, 2)                   # TV bezel
    pier.box(px0 + 0.455, px1 - 0.455, py1 + 0.03, py1 + 0.032, z0 + 1.255, z0 + 2.345, 4)       # screen
    pier.rbox(px0 + 0.7, px1 - 0.7, py1 + 0.02, py1 + 0.09, z0 + 1.1, z0 + 1.17, r=0.03, mi=2, seg=2)   # soundbar
    pier.box(px0 + 0.7, px0 + 1.0, py1 + 0.42, py1 + 0.47, z0 + 0.85, z0 + 0.86, 1)
    books(pier, px1 - 0.9, py1 + 0.2, z0 + 0.85, n=2, mi=5, rot=0.1, w=0.28, d=0.2)
    vase(pier, px0 + 0.5, py1 + 0.2, z0 + 0.85, h=0.16, r=0.07, mi=6, style='round')
    niche_glow = _mat.new_mat("NicheGlowSoft", (1, 0.85, 0.65, 1), emit=(1.0, 0.80, 0.55, 1), emit_str=6.0)   # a thin strip now, so it can be brighter
    pier.build("UpFam_Pier", [M['trav_grey'], M['oak'], M['black'], niche_glow, M['tv'], M['book'], M['ceramic_black']])
    # biscuit-tufted L-sectional facing the TV (photo 30: plump square tufts, low back, loose pillows, brown throw)
    sf = MB()
    _tufted_sofa(sf, 4.85, 9.95, 3.6, 1.0, rot=0.0, z=z0 + 0.02, mi=0, arm_end='R',
                 pillows=[(-1.25, 0.5, 2), (-0.55, 0.48, 3), (0.65, 0.5, 2), (1.3, 0.44, 3)])
    _tufted_sofa(sf, 3.55, 8.3, 2.2, 1.0, rot=math.pi / 2, z=z0 + 0.02, mi=0, arm_end='L', pillows=[(0.55, 0.48, 3)])
    sf.pillow(3.35, 7.75, z0 + 0.62, 0.5, 0.5, 0.15, 1, rot=math.pi / 2 + 0.2, pitch=math.pi / 2 - 0.45)
    sf.drape(3.05, 4.1, 8.55, 9.35, z0 + 0.62, t=0.024, mi=4, sag=0.06, rot=0.1, folds=3, seed=4)   # brown throw over the chaise
    sf.build("UpFam_Sectional", [M['fabric_taupe'], M['fabric_dark'], M['fabric_grey'], M['fabric_white'], M['throw_brown']], bevel=0.012)
    ct = MB()
    round_table(ct, 5.1, 8.45, z0 + 0.02, 0.5, h=0.38, top_t=0.04, mi=0, mi_leg=1, legs='drum')
    vase(ct, 4.92, 8.35, z0 + 0.42, h=0.1, r=0.11, mi=2, style='bowl')
    books(ct, 5.3, 8.62, z0 + 0.42, n=3, mi=3, rot=0.25, w=0.28, d=0.22)
    _candle(ct, 5.05, 8.7, z0 + 0.42, 4, 5, r=0.03, h=0.09)
    ct.build("UpFam_Table", [M['marble'], M['brass'], M['ceramic'], M['book'], M['ceramic_cream'], M['emit_warm']])
    _rug(M, 'UpFamily', 2.9, 6.8, 7.1, 10.5, z0 + 0.02, M['rug'])
    # rust leather armchair with a piped rim, walnut side drum
    ac = MB()
    armchair(ac, 1.75, 5.7, rot=math.pi * 0.62, z=z0 + 0.02, w=0.8, d=0.85, mi=0, mi_legs=1)
    px_, py_ = rot2(1.75, 5.7 + 0.32, 1.75, 5.7, math.pi * 0.62)
    ac.rcbox(px_, py_, z0 + 0.02 + 0.83, 0.8, 0.02, 0.02, r=0.009, mi=2, rot=math.pi * 0.62, seg=2)   # piping along the back top
    ac.cylinder(1.4, 6.6, z0 + 0.02, z0 + 0.5, 0.2, seg=20, mi=1)
    _tray(ac, 1.4, 6.6, z0 + 0.5, 0.26, 0.26, 3)
    ac.build("UpFam_Armchair", [M['leather_tan'], M['walnut'], M['leather_tan'], M['ceramic_black']], bevel=0.012)
    pl = MB()
    potted_plant(pl, x1 - 0.5, y0 + 0.5, z0 + 0.02, pot_r=0.26, pot_h=0.5, h=1.4, mi_pot=0, mi_leaf=1, mi_stem=2, seed=3, kind='olive')
    pl.build("UpFam_Plant", [M['ceramic'], M['leaf_plant'], M['bark']], smooth=True)
    # desk zone at the north end: oak built-in desk + lit shelves, laptop, lamp, books, pen cup, ceramics
    dk = MB()
    dx0, dx1 = x0 + 0.1, 2.6
    dk.box(dx0, dx1, y1 - 0.7, y1 - 0.05, z0 + 0.72, z0 + 0.76, 0)
    dk.box(dx0, dx0 + 0.04, y1 - 0.7, y1 - 0.05, z0 + 0.02, z0 + 0.72, 0)
    dk.box(dx1 - 0.04, dx1, y1 - 0.7, y1 - 0.05, z0 + 0.02, z0 + 0.72, 0)
    dk.box(dx1 - 0.65, dx1 - 0.05, y1 - 0.66, y1 - 0.05, z0 + 0.02, z0 + 0.72, 0)              # drawer pedestal
    for zz in (z0 + 0.25, z0 + 0.48):
        dk.box(dx1 - 0.64, dx1 - 0.06, y1 - 0.665, y1 - 0.661, zz, zz + 0.003, 4)              # drawer reveals
    shelves(dk, dx0, dx1, y1 - 0.36, y1 - 0.05, z0 + 1.35, z0 + 2.7, n=3, t=0.03, mi=0, back=True)
    dk.box(dx0 + 0.05, dx1 - 0.05, y1 - 0.08, y1 - 0.05, z0 + 1.36, z0 + 2.69, 1)               # lit back panel
    dk.box(dx0 + 0.05, dx1 - 0.05, y1 - 0.4, y1 - 0.36, z0 + 2.72, z0 + 2.74, 1)                # cove strip
    _books_row(dk, dx0 + 0.15, y1 - 0.2, z0 + 1.365, 7, [2, 5, 6], along='X')
    _books_row(dk, dx0 + 1.3, y1 - 0.2, z0 + 1.815, 5, [5, 2], along='X')
    books(dk, dx0 + 0.3, y1 - 0.22, z0 + 1.815, n=3, mi=2, rot=0.05, w=0.26, d=0.2)
    vase(dk, dx1 - 0.4, y1 - 0.2, z0 + 2.265, h=0.28, r=0.09, mi=3, style='tall')
    vase(dk, dx0 + 0.6, y1 - 0.2, z0 + 2.265, h=0.18, r=0.11, mi=3, style='round')
    vase(dk, dx0 + 1.1, y1 - 0.2, z0 + 2.265, h=0.12, r=0.12, mi=6, style='bowl')
    vase(dk, dx1 - 0.35, y1 - 0.2, z0 + 1.815, h=0.2, r=0.08, mi=6, style='round')
    _laptop(dk, dx0 + 1.05, y1 - 0.42, z0 + 0.76, 4, 7, rot=0.06)
    _lamp(dk, dx1 - 0.3, y1 - 0.35, z0 + 0.76, 3, 8, 9, 4, cord_to=(dx1 - 0.08, y1 - 0.07, z0 + 0.76), base_r=0.1, base_h=0.3, shade_r=0.15, shade_h=0.18)
    books(dk, dx0 + 0.35, y1 - 0.4, z0 + 0.76, n=2, mi=5, rot=0.15, w=0.27, d=0.2)
    _pen_cup(dk, dx1 - 0.75, y1 - 0.5, z0 + 0.76, 6, 4)
    dk.build("UpFam_Desk", [M['oak_pale'], M['emit_bar'], M['book'], M['ceramic'], M['black_gloss'], M['paper'], M['ceramic_black'], M['tv'], M['lampshade'], M['emit_warm']], smooth=False)
    ch = MB()
    _jeanneret_chair(ch, dx0 + 0.6, y1 - 1.2, rot=math.pi, z=z0 + 0.02, mi_wood=0, mi_cane=1)
    _jeanneret_chair(ch, dx0 + 1.6, y1 - 1.2, rot=math.pi + 0.08, z=z0 + 0.02, mi_wood=0, mi_cane=1)
    ch.build("UpFam_Chairs", [_local(M)['teak_warm'], _local(M)['cane_tan']], bevel=0.006)
    # south zone behind the pier: low oak console + floater-framed art
    sc = MB()
    sc.box(2.9, 5.5, py0 - 0.42, py0 - 0.02, z0 + 0.3, z0 + 0.62, 0)
    sc.box(3.1, 5.3, py0 - 0.4, py0 - 0.04, z0 + 0.02, z0 + 0.3, 0)
    sc.box(3.4, 5.0, py0 - 0.42, py0 - 0.418, z0 + 0.32, z0 + 0.6, 4)
    vase(sc, 3.4, py0 - 0.22, z0 + 0.62, h=0.3, r=0.1, mi=1, style='tall')
    books(sc, 4.8, py0 - 0.22, z0 + 0.62, n=2, mi=5, rot=-0.1, w=0.3, d=0.22)
    _floater(sc, 3.3, 5.1, py0 - 0.02, z0 + 1.0, z0 + 2.2, along='X', face=-1, mi_frame=2, mi_canvas=3)
    sc.build("UpFam_SouthConsole", [M['oak'], M['ceramic_black'], M['walnut'], M['art_abstract'], M['black'], M['book']])
    # lighting (photo 30): two runs of recessed black slot lights + a few trimmed downlights; the pools of light on
    # the walls come from spots under each fixture, no flat ceiling wash
    slots = [(2.2, y) for y in (5.0, 7.4, 9.8)] + [(5.6, y) for y in (5.0, 7.4, 9.8)]
    tl = MB()
    _slot_lights(tl, slots, z1 - 0.02, mi_black=0, mi_lens=1, along='Y', L=0.9)
    tl.build("UpFam_Slots", [M['black'], M['emit_down']])
    _down_spots("L_upfam_slot", slots, z1, energy=26, spot=95, blend=0.75)
    dl = [(1.4, 5.0), (6.4, 5.0), (1.4, 10.3), (6.4, 10.3)]
    _downlights(M, 'upfamily', dl, z1)
    _down_spots("L_upfam_dl", dl, z1, energy=22, spot=80)
    room_light("L_upfamily", 'upfamily', energy=16)
    _spot("L_upfam_tv", (4.2, 8.4, z1 - 0.05), (4.2, 6.85, z0 + 1.6), 30, 60)
    _spot("L_upfam_desk", (1.5, 10.2, z1 - 0.05), (1.5, 10.9, z0 + 0.8), 30, 70)
    _spot("L_upfam_art", (4.2, 5.4, z1 - 0.05), (4.2, py0, z0 + 1.6), 25, 60)


def build_upbed1(M):
    x0, x1, y0, y1, z0, z1 = ROOMS['upbed1']
    x0 = PX_E
    _finish(M, 'upbed1', M['oak_floor'], faces='N', bounds=(x0, x1, y0, y1, z0, z1), gaps='WSN')
    _ceiling_gear(M, 'upbed1', z1, speakers=[(2.5, 13.2), (5.5, 15.8)], diffusers=[(4.0, 11.7, 'X'), (4.0, 17.3, 'X')])
    bd = MB()
    bed(bd, x0 + 1.2, 14.3, rot=math.pi / 2, z=z0 + 0.02, w=1.9, l=2.15, mi_frame=0, mi_linen=1, mi_pillow=1, mi_throw=3, head_h=1.05, seed=2)
    cushion(bd, x0 + 0.62, 14.62, z0 + 0.7, 0.55, 0.55, 0.16, 4, rot=math.pi / 2 + 0.1, upright=True)
    cushion(bd, x0 + 0.62, 13.98, z0 + 0.7, 0.55, 0.55, 0.16, 4, rot=math.pi / 2 - 0.08, upright=True)
    cushion(bd, x0 + 0.8, 14.3, z0 + 0.7, 0.45, 0.45, 0.15, 5, rot=math.pi / 2 - 0.15, upright=True)
    bd.rcbox(x0 + 3.4, 14.3, z0 + 0.44, 0.42, 1.5, 0.1, r=0.03, mi=6, seg=2)                  # bench at the foot
    bd.cbox(x0 + 3.4, 14.3, z0 + 0.2, 0.36, 1.4, 0.34, 7)
    bd.drape(x0 + 3.15, x0 + 3.65, 13.55, 14.15, z0 + 0.49, t=0.03, mi=3, sag=0.05, rot=0.1, folds=2, seed=7)   # knit throw on the bench
    bd.build("UpBed1_Bed", [_local(M)['boucle_oat'], M['linen_white'], M['linen_white'], _local(M)['knit_oat'], M['fabric_taupe'], M['fabric_grey'], M['fabric_grey'], M['oak']], bevel=0.012)
    _rug(M, 'UpBed1', x0 + 0.3, x0 + 4.4, 12.5, 16.1, z0 + 0.02, M['rug_pale'])
    ns = MB()
    for ny in (12.95, 15.65):
        _nightstand(ns, x0 + 0.32, ny, z0 + 0.02, w=0.55, d=0.5, h=0.5, mi=0, mi_gap=3, rot=-math.pi / 2)
    _mushroom_lamp(ns, x0 + 0.32, 15.65, z0 + 0.52, mi=1, h=0.45, r=0.15, mi_bulb=4)
    books(ns, x0 + 0.32, 12.95, z0 + 0.52, n=2, mi=2, rot=0.1, w=0.26, d=0.2)
    _carafe(ns, x0 + 0.22, 13.1, z0 + 0.52, 5, 6)
    ns.build("UpBed1_Nightstands", [M['oak'], M['ceramic'], M['book'], M['black'], M['emit_warm'], M['glass'], M['water_still']], smooth=True)
    # walnut wave console: 5 stacked curved boxes with rounded edges + white vase with branches + line-art canvas
    cs = MB()
    cx0, cx1, cy0, cy1 = 3.2, 4.8, y1 - 0.42, y1 - 0.04
    for i in range(5):
        zz = z0 + 0.02 + i * 0.152
        off = 0.06 * math.sin(i * 1.3)
        cs.rbox(cx0 + 0.08 + off, cx1 - 0.08 + off, cy0 + 0.02, cy1, zz, zz + 0.15, r=0.015, mi=0, seg=2)
    cs.rbox(cx0, cx1, cy0, cy1, z0 + 0.78, z0 + 0.82, r=0.012, mi=0, seg=2)
    vase(cs, 3.55, y1 - 0.24, z0 + 0.82, h=0.32, r=0.12, mi=1, style='round')
    branches(cs, 3.55, y1 - 0.24, z0 + 1.12, h=0.7, n=7, seed=5, mi=2, leaves=6, mi_leaf=3, spread=0.4)
    vase(cs, 4.4, y1 - 0.24, z0 + 0.82, h=0.14, r=0.07, mi=1, style='bowl')
    books(cs, 4.05, y1 - 0.26, z0 + 0.82, n=2, mi=4, rot=0.1, w=0.24, d=0.2)
    cs.build("UpBed1_Console", [M['walnut'], M['ceramic'], M['bark'], M['olive'], M['book']], smooth=True)
    pc = MB()
    _floater(pc, 3.2, 4.8, y1 - 0.02, z0 + 1.15, z0 + 2.45, along='X', face=-1, mi_frame=0, mi_canvas=1)
    pc.build("UpBed1_Art", [M['walnut'], M['art_lines']])
    ex = MB()
    armchair(ex, 6.2, 12.4, rot=-math.pi * 0.35, z=z0 + 0.02, w=0.8, d=0.8, mi=0, mi_legs=1)
    ex.cylinder(6.55, 13.3, z0 + 0.02, z0 + 0.45, 0.2, seg=20, mi=1)
    books(ex, 6.55, 13.3, z0 + 0.45, n=2, mi=2, rot=0.3, w=0.22, d=0.17)
    ex.build("UpBed1_Chair", [M['fabric'], M['oak'], M['book']], bevel=0.012)
    pl = MB()
    potted_plant(pl, 6.4, 17.2, z0 + 0.02, pot_r=0.26, pot_h=0.5, h=1.4, mi_pot=0, mi_leaf=1, mi_stem=2, seed=19, kind='olive')
    pl.build("UpBed1_Plant", [M['plant_pot'], M['olive'], M['bark']], smooth=True)
    dl = [(2.0, 12.4), (2.0, 16.6), (5.5, 12.4), (5.5, 16.6)]
    _downlights(M, 'upbed1', dl, z1)
    _down_spots("L_upbed1_dl", dl, z1, energy=24, spot=85)
    sl = [(3.8, 13.0), (3.8, 15.6)]
    tl = MB(); _slot_lights(tl, sl, z1 - 0.02, 0, 1, along='X', L=0.9); tl.build("UpBed1_Slots", [M['black'], M['emit_down']])
    _down_spots("L_upbed1_slot", sl, z1, energy=20, spot=95, blend=0.8)
    add_light("L_upbed1_lamp", 'POINT', (x0 + 0.32, 15.65, z0 + 0.85), 9, (1.0, 0.72, 0.45), size=0.12)
    room_light("L_upbed1", 'upbed1', energy=28)
    _spot("L_upbed1_art", (4.0, 16.6, z1 - 0.05), (4.0, y1, z0 + 1.8), 30, 60)


def build_upbed2(M):
    x0, x1, y0, y1, z0, z1 = ROOMS['upbed2']
    x0 = PX_B2
    _finish(M, 'upbed2', M['oak_floor'], faces='N', bounds=(x0, x1, y0, y1, z0, z1), gaps='WSN')
    _ceiling_gear(M, 'upbed2', z1, speakers=[(2.6, 19.2), (5.6, 22.4)], diffusers=[(4.0, 18.5, 'X'), (4.0, 23.1, 'X')], detector=(5.8, 19.0))
    bd = MB()
    bed(bd, x0 + 1.3, 20.7, rot=math.pi / 2, z=z0 + 0.02, w=1.95, l=2.15, mi_frame=0, mi_linen=1, mi_pillow=1, mi_throw=2, head_h=1.0, seed=5)
    cushion(bd, x0 + 0.65, 20.7, z0 + 0.7, 0.5, 0.5, 0.15, 3, rot=math.pi / 2 + 0.08, upright=True)
    cushion(bd, x0 + 0.8, 20.7, z0 + 0.7, 0.42, 0.42, 0.14, 4, rot=math.pi / 2 - 0.12, upright=True)
    bd.rcbox(x0 + 2.9, 20.7, z0 + 0.44, 0.45, 1.5, 0.12, r=0.035, mi=3, seg=2)                 # bench at the foot
    bd.cbox(x0 + 2.9, 20.7, z0 + 0.19, 0.4, 1.4, 0.34, 5)
    bd.drape(x0 + 2.65, x0 + 3.15, 21.0, 21.55, z0 + 0.5, t=0.03, mi=2, sag=0.05, rot=-0.08, folds=2, seed=9)    # knit throw
    bd.build("UpBed2_Bed", [M['fabric'], M['linen_white'], _local(M)['knit_oat'], M['fabric_sand'], M['fabric_grey'], M['oak']], bevel=0.012)
    _rug(M, 'UpBed2', x0 + 0.4, x0 + 4.2, 18.9, 22.5, z0 + 0.02, _local(M)['rug_camel_deep'])
    ns = MB()
    _nightstand(ns, x0 + 0.42, 22.2, z0 + 0.02, w=0.7, d=0.5, h=0.52, mi=0, mi_gap=3, rot=-math.pi / 2)
    _mushroom_lamp(ns, x0 + 0.42, 22.2, z0 + 0.54, mi=1, h=0.48, r=0.16, mi_bulb=4)
    ns.box(x0 + 0.2, x0 + 0.45, 21.95, 22.1, z0 + 0.54, z0 + 0.56, 1)                          # small dish
    _nightstand(ns, x0 + 0.42, 19.2, z0 + 0.02, w=0.7, d=0.5, h=0.52, mi=0, mi_gap=3, rot=-math.pi / 2)
    books(ns, x0 + 0.42, 19.2, z0 + 0.54, n=2, mi=2, rot=0.1, w=0.28, d=0.2)
    _carafe(ns, x0 + 0.3, 19.45, z0 + 0.54, 5, 6)
    ns.build("UpBed2_Nightstands", [M['oak'], M['ceramic'], M['book'], M['black'], M['emit_warm'], M['glass'], M['water_still']], smooth=True)
    mr = MB()
    _round_mirror(mr, x0 + 0.005, 22.2, z0 + 1.65, 0.62, axis='X', mi_frame=0, mi_mirror=1)
    mr.build("UpBed2_Mirror", [M['frame'], M['mirror']], smooth=True)
    # travertine waterfall console + white relief canvas on the north wall (east end)
    cs = MB()
    cx0, cx1 = 4.4, 6.4
    cs.box(cx0, cx1, y1 - 0.45, y1 - 0.03, z0 + 0.74, z0 + 0.8, 0)
    cs.box(cx0, cx0 + 0.06, y1 - 0.45, y1 - 0.03, z0 + 0.02, z0 + 0.74, 0)
    cs.box(cx1 - 0.06, cx1, y1 - 0.45, y1 - 0.03, z0 + 0.02, z0 + 0.74, 0)
    vase(cs, 5.0, y1 - 0.25, z0 + 0.8, h=0.28, r=0.11, mi=1, style='round')
    branches(cs, 5.0, y1 - 0.25, z0 + 1.06, h=0.55, n=6, seed=8, mi=2, leaves=5, mi_leaf=3, spread=0.35)
    books(cs, 5.8, y1 - 0.25, z0 + 0.8, n=2, mi=4, rot=0.0, w=0.32, d=0.24)
    _tray(cs, 5.45, y1 - 0.25, z0 + 0.8, 0.3, 0.2, 5, rot=0.05)
    cs.build("UpBed2_Console", [M['trav_int'], M['ceramic'], M['bark'], M['olive'], M['book'], M['brass']])
    pc = MB()
    _floater(pc, 4.7, 6.1, y1 - 0.02, z0 + 1.2, z0 + 2.5, along='X', face=-1, mi_frame=0, mi_canvas=1)
    pc.build("UpBed2_Art", [M['oak_pale'], M['art_relief']])
    dr = MB(); fr = MB()
    _door(fr, dr, 'X', 2.7, 3.65, y1 - 0.08, z0, mi_pull=1)
    dr.build("UpBed2_ClosetDoor", [M['oak_pale'], M['black_metal']]); fr.build("UpBed2_ClosetFrame", M['frame'])
    ex = MB()
    armchair(ex, 6.2, 19.0, rot=math.pi * 0.7, z=z0 + 0.02, w=0.8, d=0.8, mi=0, mi_legs=1)
    ex.drape(5.85, 6.45, 18.75, 19.2, z0 + 0.45, t=0.02, mi=2, sag=0.04, rot=0.3, folds=2, seed=3)
    ex.build("UpBed2_Chair", [M['fabric'], M['oak'], M['throw']], bevel=0.012)
    dl = [(x0 + 1.3, 19.3), (x0 + 1.3, 22.1), (4.5, 19.3), (4.5, 22.1)]
    _downlights(M, 'upbed2', dl, z1)
    _down_spots("L_upbed2_dl", dl, z1, energy=24, spot=85)
    sl = [(3.2, 19.0), (3.2, 22.6), (6.0, 20.7)]
    tl = MB(); _slot_lights(tl, sl, z1 - 0.02, 0, 1, along='X', L=0.9); tl.build("UpBed2_Slots", [M['black'], M['emit_down']])
    _down_spots("L_upbed2_slot", sl, z1, energy=20, spot=95, blend=0.8)
    add_light("L_upbed2_lamp", 'POINT', (x0 + 0.42, 22.2, z0 + 0.88), 9, (1.0, 0.72, 0.45), size=0.12)
    room_light("L_upbed2", 'upbed2', energy=26)
    _spot("L_upbed2_art", (5.4, 22.4, z1 - 0.05), (5.4, y1, z0 + 1.8), 30, 60)
    _spot("L_upbed2_bed", (x0 + 1.0, 20.7, z1 - 0.05), (x0 + 0.2, 20.7, z0 + 1.2), 25, 70)


def build_upbed2b(M):
    """Bed 2's en-suite bath + dressing room: marble floor, floating oak vanity with basin + lit mirror on the north
    wall, glass shower in the NW corner, oak wardrobe run along the south wall (leaving the hall door), bench."""
    x0, x1, y0, y1, z0, z1 = ROOMS['upbed2b']
    x0, x1 = PX_H0, PX_B2B
    _finish(M, 'upbed2b', M['marble'], faces='N', bounds=(x0, x1, y0, y1, z0, z1), gaps='WEN')
    _ceiling_gear(M, 'upbed2b', z1, speakers=[(-2.0, 20.0)], diffusers=[(-2.2, 22.9, 'X')])
    sh = MB()
    sx0, sx1, sy0, sy1 = x0, x0 + 1.3, y1 - 1.6, y1
    sh.box(sx0, sx0 + 0.02, sy0, sy1, z0, z1, 0); sh.box(sx0, sx1, sy1 - 0.02, sy1, z0, z1, 0)
    sh.box(sx0, sx1, sy0, sy1, z0 + 0.02, z0 + 0.04, 0)
    sh.lathe(sx0 + 0.65, sy1 - 0.8, z0 + 0.04, [(0, 0), (0.05, 0), (0.05, 0.003), (0, 0.003)], seg=16, mi=2)     # drain
    gl = MB()                                                                                    # frameless glass: its own flat-shaded object
    gl.box(sx1 - T, sx1, sy0, sy1, z0 + 0.04, z0 + 2.2, 0)                                       # glass side
    gl.box(sx0, sx1 - 0.6, sy0 - T, sy0, z0 + 0.04, z0 + 2.2, 0)                                  # glass front (door gap)
    gl.build("UpBed2b_ShowerGlass", M['glass'])
    sh.box(sx1 - 0.03, sx1 + 0.03, sy0 - 0.03, sy0 + 0.03, z0 + 0.04, z0 + 2.2, 2)                 # corner post
    sh.box(sx1 - 0.02, sx1 + 0.02, sy0 - 0.02, sy1, z0 + 2.2, z0 + 2.23, 2)                        # header bar
    sh.cylinder(sx0 + 0.65, sy1 - 0.4, z0 + 2.3, z0 + 2.32, 0.12, seg=20, mi=2)                   # rain head
    sh.cylinder(sx0 + 0.65, sy1 - 0.4, z0 + 2.32, z0 + 2.6, 0.012, seg=8, mi=2)
    sh.cylinder(sx0 + 0.04, sy1 - 0.9, z0 + 1.1, z0 + 1.12, 0.03, seg=12, mi=2, rot=0)              # mixer plate
    sh.box(sx0 + 0.02, sx0 + 0.05, sy0 + 0.5, sy1 - 0.5, z0 + 1.0, z0 + 1.3, 3)                   # niche glow
    _bottles(sh, sx0 + 0.08, sy0 + 0.7, z0 + 1.0, 4, 5, n=3)
    sh.build("UpBed2b_Shower", [M['marble'], M['glass'], M['chrome'], M['emit_bar'], M['ceramic_black'], M['glass_frost']], bevel=0.004)
    vn = MB()
    vx0, vx1 = x0 + 1.7, x0 + 3.9
    vn.box(vx0, vx1, y1 - 0.55, y1 - 0.03, z0 + 0.55, z0 + 0.85, 0)
    vn.box(vx0 + 0.3, vx1 - 0.3, y1 - 0.552, y1 - 0.548, z0 + 0.6, z0 + 0.8, 7)                   # drawer reveal
    vn.box(vx0 - 0.02, vx1 + 0.02, y1 - 0.57, y1 - 0.03, z0 + 0.85, z0 + 0.89, 1)
    vn.box(vx0 + 0.02, vx1 - 0.02, y1 - 0.54, y1 - 0.04, z0 + 0.52, z0 + 0.55, 2)                 # under-glow
    basin(vn, (vx0 + vx1) / 2, y1 - 0.3, z0 + 0.89, r=0.22, mi=3)
    faucet(vn, (vx0 + vx1) / 2, y1 - 0.08, z0 + 0.89, mi=4, dir=(0, -1))
    vn.box(vx0 + 0.3, vx1 - 0.3, y1 - 0.04, y1 - 0.022, z0 + 1.15, z0 + 2.15, 5)                  # mirror
    vn.frame(vx0 + 0.25, vx1 - 0.25, y1 - 0.045, y1 - 0.02, z0 + 1.1, z0 + 2.2, 0.04, mi=2, axis='Y')  # LED halo
    vase(vn, vx1 - 0.3, y1 - 0.3, z0 + 0.89, h=0.22, r=0.08, mi=3, style='tall')
    _towel(vn, vx0 + 0.35, y1 - 0.3, z0 + 0.89, 6, w=0.3, d=0.2, folded=2)
    _bottles(vn, vx0 + 0.75, y1 - 0.18, z0 + 0.89, 8, 3, n=2)
    _tray(vn, vx1 - 0.7, y1 - 0.3, z0 + 0.89, 0.26, 0.16, 7)
    vn.rcbox((vx0 + vx1) / 2, y1 - 1.0, z0 + 0.03, 0.9, 0.55, 0.02, r=0.008, mi=6, seg=2)          # bath mat
    vn.build("UpBed2b_Vanity", [M['oak'], M['marble'], M['emit_bar'], M['ceramic'], M['chrome'], M['mirror'], M['linen_white'], M['black'], M['ceramic_black']], smooth=False)
    wd = MB()
    cabinet_run(wd, x0 + 0.05, -1.45, y0 + 0.02, y0 + 0.62, z0 + 0.06, z1 - 0.02, mi=0, doors='X', n=6, mi_gap=1)
    cabinet_run(wd, -0.05, x1 - 0.05, y0 + 0.02, y0 + 0.62, z0 + 0.06, z1 - 0.02, mi=0, doors='X', n=2, mi_gap=1)
    wd.box(x0 + 0.05, x1 - 0.05, y0 + 0.02, y0 + 0.62, z0 + 0.02, z0 + 0.06, 1)                    # toe-kick shadow
    wd.box(x0 + 0.05, -1.45, y0 + 0.62, y0 + 0.64, z0 + 2.1, z0 + 2.12, 2)                        # LED line under the top row
    for i in range(1, 6):                                                                        # tiny edge pulls
        gx = x0 + 0.05 + (-1.45 - x0 - 0.05) * i / 6
        wd.box(gx - 0.06, gx - 0.02, y0 + 0.62, y0 + 0.63, z0 + 1.0, z0 + 1.3, 1)
    wd.build("UpBed2b_Wardrobe", [M['oak_pale'], M['black'], M['emit_bar']])
    ex = MB()
    ex.rcbox(-1.6, 21.0, z0 + 0.44, 1.3, 0.45, 0.1, r=0.035, mi=0, seg=2)
    ex.cbox(-1.6, 21.0, z0 + 0.2, 1.2, 0.38, 0.38, 1)
    ex.drape(-2.05, -1.5, 20.8, 21.2, z0 + 0.49, t=0.025, mi=4, sag=0.04, rot=0.15, folds=2, seed=11)
    ex.box(x1 - 0.03, x1 - 0.005, 19.0, 19.8, z0 + 0.1, z0 + 2.0, 2)
    ex.frame(x1 - 0.035, x1, 18.97, 19.83, z0 + 0.07, z0 + 2.03, 0.03, mi=3, axis='X')
    ex.build("UpBed2b_Extras", [M['fabric_sand'], M['oak'], M['mirror'], M['frame'], M['throw']], bevel=0.012)
    _rug(M, 'UpBed2b', -3.4, 0.2, 19.8, 22.4, z0 + 0.02, M['rug_pale'])
    dl = [(-4.7, 22.6), (-2.8, 22.6), (-1.5, 19.3), (-3.8, 19.3), (0.2, 21.0)]
    _downlights(M, 'upbed2b', dl, z1)
    _down_spots("L_upbed2b_dl", dl, z1, energy=22, spot=85)
    room_light("L_upbed2b", 'upbed2b', energy=24)
    _spot("L_upbed2b_vanity", (x0 + 2.8, 22.6, z1 - 0.05), (x0 + 2.8, y1, z0 + 1.4), 30, 70)


def build_upbed3(M):
    x0, x1, y0, y1, z0, z1 = ROOMS['upbed3']
    _finish(M, 'upbed3', M['oak_floor'], faces='WN', gaps='WESN')
    _ceiling_gear(M, 'upbed3', z1, speakers=[(x0 + 1.5, y1 - 1.5), (x1 - 1.5, y1 - 1.5)], diffusers=[((x0 + x1) / 2, y0 + 0.6, 'X'), ((x0 + x1) / 2, y1 - 0.5, 'X')])
    cx = (x0 + x1) / 2
    bd = MB()
    bed(bd, cx, y1 - 1.25, rot=0.0, z=z0 + 0.02, w=1.9, l=2.15, mi_frame=0, mi_linen=1, mi_pillow=1, mi_throw=3, head_h=1.0, seed=8)
    cushion(bd, cx - 0.35, y1 - 0.66, z0 + 0.7, 0.5, 0.5, 0.15, 4, rot=0.1, upright=True)
    cushion(bd, cx + 0.35, y1 - 0.66, z0 + 0.7, 0.5, 0.5, 0.15, 4, rot=-0.08, upright=True)
    cushion(bd, cx, y1 - 0.8, z0 + 0.7, 0.55, 0.3, 0.14, 5, rot=0.0, upright=True)
    bd.drape(cx - 0.85, cx + 0.85, y1 - 2.3, y1 - 1.5, z0 + 0.64, t=0.05, mi=3, sag=0.06, rot=0.03, folds=3, seed=6)   # chunky knit throw
    bd.build("UpBed3_Bed", [M['fabric_grey'], M['linen_white'], M['linen_white'], M['throw'], M['fabric_taupe'], M['fabric_sand']], bevel=0.012)
    _rug(M, 'UpBed3', x0 + 0.9, x1 - 0.9, y1 - 3.6, y1 - 0.3, z0 + 0.02, _local(M)['rug_plum_deep'])
    ns = MB()
    for sx in (cx - 1.42, cx + 1.42):
        _fluted_nightstand(ns, sx, y1 - 0.4, z0 + 0.02, w=0.66, d=0.46, h=0.56, mi=0, mi_top=1)
        _lamp(ns, sx, y1 - 0.42, z0 + 0.6, 2, 3, 4, 5, cord_to=(sx + 0.2, y1 - 0.05, z0 + 0.6), base_r=0.17, base_h=0.34, shade_r=0.24, shade_h=0.26)
    _carafe(ns, cx - 1.65, y1 - 0.5, z0 + 0.6, 6, 7)
    books(ns, cx + 1.3, y1 - 0.55, z0 + 0.6, n=2, mi=8, rot=-0.1, w=0.22, d=0.17)
    ns.build("UpBed3_Nightstands", [M['ceramic_cream'], M['brass'], M['bronze'], M['lampshade'], M['emit_warm'], M['black'], M['glass'], M['water_still'], M['book']], smooth=True)
    pc = MB()
    for i, ax in enumerate((cx - 0.55, cx, cx + 0.55)):
        _floater(pc, ax - 0.2, ax + 0.2, y1 - 0.02, z0 + 1.55, z0 + 1.95, along='X', face=-1, mi_frame=0, mi_canvas=1, deep=0.03)
    _floater(pc, y1 - 4.4, y1 - 2.4, PX_W, z0 + 1.15, z0 + 2.65, along='Y', face=-1, mi_frame=0, mi_canvas=1)
    pc.build("UpBed3_Art", [M['brass'], M['art_patch']])
    ex = MB()
    ex.rcbox(cx, y1 - 2.75, z0 + 0.44, 1.4, 0.42, 0.1, r=0.035, mi=0, seg=2)
    ex.cbox(cx, y1 - 2.75, z0 + 0.19, 1.3, 0.36, 0.36, 1)
    armchair(ex, x0 + 1.0, y0 + 1.3, rot=-math.pi / 2 + 0.4, z=z0 + 0.02, w=0.8, d=0.8, mi=2, mi_legs=1)
    ys = 14.0 + HT
    ex.cbox(cx, ys + 0.26, z0 + 0.4, 2.0, 0.5, 0.72, 1)
    ex.cbox(cx, ys + 0.26, z0 + 0.03, 1.9, 0.44, 0.06, 3)                                         # plinth shadow
    for i in range(1, 4):
        ex.cbox(cx - 1.0 + i * 0.5, ys + 0.005, z0 + 0.4, 0.004, 0.012, 0.68, 3)
    ex.box(cx - 0.8, cx + 0.8, ys + 0.005, ys + 0.045, z0 + 1.15, z0 + 2.05, 4)
    ex.box(cx - 0.805, cx + 0.805, ys + 0.045, ys + 0.05, z0 + 1.145, z0 + 2.055, 3)              # TV bezel edge
    vase(ex, cx - 0.8, ys + 0.26, z0 + 0.78, h=0.26, r=0.1, mi=5, style='tall')
    _tray(ex, cx + 0.6, ys + 0.26, z0 + 0.78, 0.32, 0.22, 3, rot=0.1)
    _candle(ex, cx + 0.55, ys + 0.24, z0 + 0.792, 5, 6, r=0.03, h=0.07)
    armchair(ex, x1 - 1.1, y0 + 1.6, rot=math.pi / 2 - 0.5, z=z0 + 0.02, w=0.8, d=0.8, mi=2, mi_legs=1)
    ex.build("UpBed3_Extras", [M['fabric_sand'], M['oak'], M['fabric_taupe'], M['black'], M['tv'], M['ceramic'], M['emit_warm']], bevel=0.012)
    pl = MB()
    potted_plant(pl, x0 + 0.6, y0 + 0.7, z0 + 0.02, pot_r=0.26, pot_h=0.5, h=1.5, mi_pot=0, mi_leaf=1, mi_stem=2, seed=17, kind='olive')
    pl.build("UpBed3_Plant", [M['plant_pot'], M['olive'], M['bark']], smooth=True)
    # middle of the room: reading pair by the west glass with a round table + floor lamp, dresser + mirror on the east partition
    mid = MB()
    armchair(mid, x0 + 1.3, y0 + 4.6, rot=-math.pi / 2 - 0.35, z=z0 + 0.02, w=0.82, d=0.82, mi=0, mi_legs=1)
    armchair(mid, x0 + 1.3, y0 + 6.4, rot=-math.pi / 2 + 0.35, z=z0 + 0.02, w=0.82, d=0.82, mi=0, mi_legs=1)
    round_table(mid, x0 + 1.55, y0 + 5.5, z0 + 0.02, 0.32, h=0.5, mi=2, mi_leg=1, legs='drum')
    books(mid, x0 + 1.5, y0 + 5.5, z0 + 0.52, n=2, mi=3, rot=0.3, w=0.22, d=0.17)
    _carafe(mid, x0 + 1.68, y0 + 5.42, z0 + 0.52, 4, 5)
    _bulb_floor_lamp(mid, x0 + 0.7, y0 + 5.5, z0 + 0.02, 6, 7, 8, h=1.5, shade_r=0.19)
    mid.cbox(x1 - 0.3, y0 + 5.0, z0 + 0.42, 0.48, 1.7, 0.8, 1)                                   # oak dresser
    mid.cbox(x1 - 0.3, y0 + 5.0, z0 + 0.04, 0.42, 1.6, 0.08, 9)                                   # plinth shadow
    for i in range(1, 3):
        mid.cbox(x1 - 0.545, y0 + 5.0 - 0.85 + i * 0.567, z0 + 0.42, 0.004, 0.003, 0.76, 9)     # door gaps
    mid.cbox(x1 - 0.545, y0 + 5.0, z0 + 0.62, 0.004, 1.6, 0.003, 9)                              # drawer gap
    vase(mid, x1 - 0.3, y0 + 4.4, z0 + 0.82, h=0.26, r=0.09, mi=2, style='tall')
    _tray(mid, x1 - 0.3, y0 + 5.3, z0 + 0.82, 0.3, 0.2, 9, rot=0.05)
    _round_mirror(mid, x1 - 0.036, y0 + 5.0, z0 + 1.75, 0.45, axis='X', mi_frame=9, mi_mirror=10)
    mid.build("UpBed3_Middle", [M['fabric_taupe'], M['oak'], M['ceramic_cream'], M['book'], M['glass'], M['water_still'], M['brass'], M['lampshade'], M['emit_warm'], M['frame'], M['mirror']], bevel=0.012)
    dl = [(cx - 1.0, y1 - 1.0), (cx + 1.0, y1 - 1.0), (cx, y1 - 4.0), (cx, y1 - 7.0)]
    _downlights(M, 'upbed3', dl, z1)
    _down_spots("L_upbed3_dl", dl, z1, energy=24, spot=85)
    sl = [(cx - 1.6, y1 - 2.6), (cx + 1.6, y1 - 2.6), (cx, y1 - 5.5)]
    tl = MB(); _slot_lights(tl, sl, z1 - 0.02, 0, 1, along='X', L=0.9); tl.build("UpBed3_Slots", [M['black'], M['emit_down']])
    _down_spots("L_upbed3_slot", sl, z1, energy=20, spot=95, blend=0.8)
    for sx in (cx - 1.42, cx + 1.42):
        add_light(f"L_upbed3_lamp_{sx:.0f}", 'POINT', (sx, y1 - 0.42, z0 + 1.05), 12, (1.0, 0.72, 0.45), size=0.14)
    room_light("L_upbed3", 'upbed3', energy=28)
    _spot("L_upbed3_art", (x1 - 1.2, y1 - 3.4, z1 - 0.05), (x1, y1 - 3.4, z0 + 1.9), 30, 60)


def build_upsuite(M):
    """Guest suite living / kitchenette (photo 28) with a small desk by the strip window (photo 26)."""
    x0, x1, y0, y1, z0, z1 = ROOMS['upsuite']
    _finish(M, 'upsuite', M['oak_floor'], faces='', gaps='WES')
    _ceiling_gear(M, 'upsuite', z1, speakers=[(x0 + 1.5, y0 + 2.0), (x0 + 5.0, y0 + 2.0), (x0 + 3.0, y1 - 3.5)],
                  diffusers=[(x0 + 3.0, y0 + 0.5, 'X'), (x0 + 5.5, y1 - 1.2, 'Y')], detector=(x0 + 5.5, y0 + 5.0))
    x1 = PX_W
    # oak cabinet run along the north partition: 20 mm doors on 3 mm gaps, toe-kick shadow, marble niche, hood band
    kc = MB()
    kx0, kx1 = x0 + 0.05, x0 + 4.9
    kc.box(kx0, kx1, y1 - 0.62, y1 - 0.02, z0 + 0.1, z0 + 0.92, 1)                             # carcass (dark)
    kc.box(kx0 + 0.04, kx1 - 0.04, y1 - 0.58, y1 - 0.02, z0 + 0.02, z0 + 0.1, 1)                # toe kick (recessed)
    n = 8
    for i in range(n):
        dx0 = kx0 + (kx1 - kx0) * i / n + 0.0015; dx1 = kx0 + (kx1 - kx0) * (i + 1) / n - 0.0015
        kc.box(dx0, dx1, y1 - 0.64, y1 - 0.62, z0 + 0.105, z0 + 0.915, 0)                       # 20 mm door fronts
    kc.box(kx0, kx1, y1 - 0.66, y1 - 0.02, z0 + 0.92, z0 + 0.95, 2)                             # counter (marble)
    kc.box(kx0, kx1, y1 - 0.62, y1 - 0.02, z0 + 1.5, z1 - 0.02, 1)                              # upper carcass
    for i in range(n):
        dx0 = kx0 + (kx1 - kx0) * i / n + 0.0015; dx1 = kx0 + (kx1 - kx0) * (i + 1) / n - 0.0015
        kc.box(dx0, dx1, y1 - 0.64, y1 - 0.62, z0 + 1.505, z1 - 0.025, 0)                       # upper door fronts
    kc.box(x0 + 1.4, x0 + 3.5, y1 - 0.1, y1 - 0.02, z0 + 0.95, z0 + 1.5, 2)                     # marble backsplash niche
    kc.box(x0 + 1.4, x0 + 3.5, y1 - 0.62, y1 - 0.1, z0 + 1.48, z0 + 1.5, 3)                     # niche light
    kc.box(x0 + 0.05, x0 + 1.4, y1 - 0.62, y1 - 0.02, z0 + 0.95, z0 + 1.5, 0)                   # closed sides
    kc.box(x0 + 3.5, x0 + 4.9, y1 - 0.62, y1 - 0.02, z0 + 0.95, z0 + 1.5, 0)
    kc.box(x0 + 0.3, x0 + 1.0, y1 - 0.6, y1 - 0.05, z0 + 1.55, z0 + 2.05, 4)                    # wall oven
    kc.box(x0 + 0.34, x0 + 0.96, y1 - 0.63, y1 - 0.6, z0 + 1.62, z0 + 1.98, 4)                  # oven glass
    kc.cylinder(x0 + 0.65, y1 - 0.66, z0 + 2.0, z0 + 2.02, 0.008, seg=8, mi=5)                  # handle (bar)
    kc.box(x0 + 0.36, x0 + 0.94, y1 - 0.675, y1 - 0.655, z0 + 1.99, z0 + 2.01, 5)
    kc.box(x0 + 1.9, x0 + 2.9, y1 - 0.6, y1 - 0.08, z0 + 0.95, z0 + 0.96, 4)                    # cooktop glass
    for (bx, by, r) in ((x0 + 2.12, y1 - 0.45, 0.075), (x0 + 2.68, y1 - 0.45, 0.075), (x0 + 2.12, y1 - 0.22, 0.06), (x0 + 2.68, y1 - 0.22, 0.09)):
        kc.lathe(bx, by, z0 + 0.96, [(r, 0), (r, 0.005), (r * 0.7, 0.005), (r * 0.7, 0.002), (r * 0.3, 0.002), (r * 0.3, 0.006), (0, 0.006)], seg=20, mi=5)   # burner rings
    # sink basin + gooseneck faucet on the right of the run
    kc.box(x0 + 3.8, x0 + 4.4, y1 - 0.5, y1 - 0.15, z0 + 0.94, z0 + 0.951, 5)
    kc.box(x0 + 3.82, x0 + 4.38, y1 - 0.48, y1 - 0.17, z0 + 0.78, z0 + 0.95, 1)
    kc.path_tube([(x0 + 4.1, y1 - 0.1, z0 + 0.95), (x0 + 4.1, y1 - 0.1, z0 + 1.25), (x0 + 4.1, y1 - 0.2, z0 + 1.32), (x0 + 4.1, y1 - 0.33, z0 + 1.26), (x0 + 4.1, y1 - 0.34, z0 + 1.18)], 0.011, seg=10, mi=5)
    kc.lathe(x0 + 4.1, y1 - 0.1, z0 + 0.95, [(0.03, 0), (0.03, 0.02), (0.02, 0.025), (0, 0.025)], seg=12, mi=5)
    kc.lathe(x0 + 3.3, y1 - 0.3, z0 + 0.95, [(0, 0), (0.06, 0), (0.07, 0.15), (0.06, 0.16), (0.055, 0.16), (0.05, 0.01), (0, 0.01)], seg=16, mi=6)   # canister
    kc.lathe(x0 + 3.45, y1 - 0.3, z0 + 0.95, [(0, 0), (0.05, 0), (0.06, 0.11), (0.05, 0.12), (0.045, 0.12), (0.04, 0.01), (0, 0.01)], seg=16, mi=6)
    kc.lathe(x0 + 1.2, y1 - 0.3, z0 + 0.95, [(0, 0), (0.1, 0), (0.16, 0.06), (0.17, 0.08), (0.16, 0.08), (0.14, 0.05), (0, 0.04)], seg=20, mi=6)     # fruit bowl
    rng = random.Random(3)
    for i in range(6):
        a = 2 * math.pi * i / 6; kc.sphere((x0 + 1.2 + 0.06 * math.cos(a), y1 - 0.3 + 0.06 * math.sin(a), z0 + 1.03), 0.036, seg=12, rings=8, mi=7)
    kc.sphere((x0 + 1.2, y1 - 0.3, z0 + 1.07), 0.036, seg=12, rings=8, mi=7)
    kc.build("UpSuite_Kitchen", [M['oak'], M['black'], M['marble'], M['emit_bar'], M['black_gloss'], M['steel'], M['ceramic'], M['ceramic_cream']], smooth=False)
    # waterfall marble island + 6 walnut/cane stools on its south side
    isl = MB()
    ix0, ix1, iy0, iy1 = x0 + 0.6, x0 + 4.6, y1 - 2.35, y1 - 1.45
    isl.box(ix0, ix1, iy0, iy1, z0 + 0.88, z0 + 0.94, 0)
    isl.box(ix0, ix0 + 0.06, iy0, iy1, z0 + 0.02, z0 + 0.88, 0)
    isl.box(ix1 - 0.06, ix1, iy0, iy1, z0 + 0.02, z0 + 0.88, 0)
    isl.box(ix0 + 0.06, ix1 - 0.06, iy0 + 0.35, iy1, z0 + 0.1, z0 + 0.88, 1)                    # oak cabinet core
    isl.box(ix0 + 0.1, ix1 - 0.1, iy0 + 0.4, iy1, z0 + 0.02, z0 + 0.1, 5)                       # toe kick
    for gx in (ix0 + 1.06, ix1 - 1.06):
        isl.box(gx - 0.002, gx + 0.002, iy1 - 0.001, iy1 + 0.003, z0 + 0.12, z0 + 0.86, 5)     # door gaps
    vase(isl, x0 + 1.6, y1 - 1.9, z0 + 0.94, h=0.3, r=0.12, mi=2, style='tall')
    branches(isl, x0 + 1.6, y1 - 1.9, z0 + 1.24, h=0.6, n=6, seed=12, mi=3, leaves=8, mi_leaf=4, spread=0.4)
    isl.lathe(x0 + 3.6, y1 - 1.9, z0 + 0.94, [(0, 0), (0.12, 0), (0.17, 0.04), (0.18, 0.05), (0.17, 0.05), (0.15, 0.03), (0, 0.025)], seg=20, mi=2)   # bowl
    books(isl, x0 + 2.7, y1 - 1.75, z0 + 0.94, n=2, mi=6, rot=0.2, w=0.3, d=0.24)
    isl.build("UpSuite_Island", [M['marble'], M['oak'], M['ceramic'], M['bark'], M['leaf_plant'], M['black'], M['book']])
    st = MB()
    for i in range(6):
        stool(st, ix0 + 0.4 + i * 0.64, iy0 - 0.32, z0 + 0.02, h=0.68, mi_wood=0, mi_seat=1, r=0.2, rot=math.pi)
    st.build("UpSuite_Stools", [M['walnut'], M['cane']], smooth=True)
    _rug(M, 'UpSuite', x0 + 0.8, x1 - 0.8, y0 + 1.7, y0 + 5.0, z0 + 0.02, M['rug_blue'])
    lg = MB()
    lg.rbox(x0 + 1.4, x0 + 2.3, y0 + 2.4, y0 + 3.3, z0 + 0.02, z0 + 0.42, r=0.1, mi=0, puff=0.3)
    lg.rbox(x0 + 2.6, x0 + 3.5, y0 + 2.2, y0 + 3.1, z0 + 0.02, z0 + 0.42, r=0.1, mi=0, puff=0.3)
    lg.build("UpSuite_Ottomans", [M['fabric_grey']], bevel=0.012)
    tb = MB()
    table(tb, x0 + 3.2, y0 + 4.1, z0 + 0.02, 1.2, 0.7, h=0.4, top_t=0.03, mi_top=0, mi_leg=1, legs='four', leg_w=0.02)
    books(tb, x0 + 2.9, y0 + 4.1, z0 + 0.42, n=3, mi=2, rot=0.1, w=0.34, d=0.26)
    vase(tb, x0 + 3.6, y0 + 4.0, z0 + 0.42, h=0.16, r=0.1, mi=3, style='round')
    _tray(tb, x0 + 3.55, y0 + 4.28, z0 + 0.42, 0.24, 0.16, 1, rot=-0.15)
    tb.build("UpSuite_CoffeeTable", [M['marble_dark'], M['black_metal'], M['book'], M['ceramic_black']])
    cr = MB()
    cr.box(x1 - 0.5, x1 - 0.06, y0 + 2.6, y0 + 4.4, z0 + 0.18, z0 + 0.72, 0)
    cr.box(x1 - 0.4, x1 - 0.16, y0 + 2.8, y0 + 4.2, z0 + 0.02, z0 + 0.18, 0)
    for gy in (y0 + 3.2, y0 + 3.8):
        cr.box(x1 - 0.502, x1 - 0.499, gy - 0.002, gy + 0.002, z0 + 0.2, z0 + 0.7, 5)          # door gaps
    vase(cr, x1 - 0.28, y0 + 3.0, z0 + 0.72, h=0.3, r=0.1, mi=1, style='tall')
    vase(cr, x1 - 0.28, y0 + 4.0, z0 + 0.72, h=0.22, r=0.12, mi=2, style='round')
    books(cr, x1 - 0.32, y0 + 3.5, z0 + 0.72, n=3, mi=6, rot=0.0, w=0.2, d=0.28)
    _round_mirror(cr, x1 - 0.036, y0 + 3.5, z0 + 1.7, 0.7, axis='X', mi_frame=3, mi_mirror=4)
    cr.build("UpSuite_Credenza", [M['ebony'], M['clay'], M['ceramic'], M['frame'], M['mirror'], M['black'], M['book']], smooth=True)
    dk = MB()
    dk.cylinder(x0 + 3.2, y0 + 0.75, z0 + 0.72, z0 + 0.76, 0.85, seg=32, mi=0, ry=0.5)
    dk.cylinder(x0 + 2.55, y0 + 0.75, z0 + 0.02, z0 + 0.72, 0.16, seg=20, mi=1)
    dk.cylinder(x0 + 3.85, y0 + 0.75, z0 + 0.02, z0 + 0.72, 0.16, seg=20, mi=1)
    books(dk, x0 + 3.0, y0 + 0.7, z0 + 0.76, n=2, mi=2, rot=0.3, w=0.3, d=0.24)
    vase(dk, x0 + 3.7, y0 + 0.75, z0 + 0.76, h=0.3, r=0.1, mi=3, style='tall')
    branches(dk, x0 + 3.7, y0 + 0.75, z0 + 1.06, h=0.5, n=6, seed=21, mi=4, leaves=8, mi_leaf=5, spread=0.45)
    _laptop(dk, x0 + 2.75, y0 + 0.85, z0 + 0.76, 8, 9, rot=-0.2)
    _jeanneret_chair(dk, x0 + 2.7, y0 + 1.55, rot=0.0, z=z0 + 0.02, mi_wood=6, mi_cane=7)
    _jeanneret_chair(dk, x0 + 3.7, y0 + 1.55, rot=0.1, z=z0 + 0.02, mi_wood=6, mi_cane=7)
    dk.build("UpSuite_Desk", [M['oak_pale'], M['trav_int'], M['book'], M['ceramic_cream'], M['bark'], M['leaf_plant'], M['oak'], M['fabric_white'], M['black_gloss'], M['tv']], smooth=True)
    tv_ = MB()
    tv_.box(x1 - 0.05, x1 - 0.005, y0 + 5.2, y0 + 6.6, z0 + 1.3, z0 + 2.1, 0)
    tv_.box(x1 - 0.055, x1 - 0.05, y0 + 5.195, y0 + 6.605, z0 + 1.295, z0 + 2.105, 1)
    tv_.build("UpSuite_TV", [M['tv'], M['black']])
    sl = [(x0 + 1.2, y1 - 1.0), (x0 + 3.2, y1 - 1.0), (x0 + 5.2, y1 - 1.0), (x0 + 1.2, y0 + 3.2), (x0 + 3.2, y0 + 3.2), (x0 + 5.2, y0 + 3.2), (x0 + 3.2, y0 + 0.9)]
    tl = MB(); _slot_lights(tl, sl, z1 - 0.02, 0, 1, along='X', L=0.9); tl.build("UpSuite_Slots", [M['black'], M['emit_down']])
    _down_spots("L_upsuite_slot", sl, z1, energy=24, spot=95, blend=0.8)
    room_light("L_upsuite", 'upsuite', energy=30)
    _spot("L_upsuite_niche", (x0 + 2.4, y1 - 1.0, z1 - 0.05), (x0 + 2.4, y1, z0 + 1.2), 30, 70)


def build_upbath(M):
    """Unassigned west-wing bay between the suite and bed3: a simple guest bathroom."""
    x0, x1, y0, y1, z0, z1 = MX0 + 0.4, -5.6, 9.0, 14.0, Z_UP, Z_UPC
    _finish(M, 'upbath', M['marble'], faces='W', bounds=(x0, x1, y0, y1, z0, z1), gaps='WESN')
    v = MB()
    v.box(x0 + 0.05, x0 + 0.6, y0 + 0.6, y0 + 2.6, z0 + 0.25, z0 + 0.85, 0)
    v.box(x0 + 0.05, x0 + 0.62, y0 + 0.58, y0 + 2.62, z0 + 0.85, z0 + 0.89, 1)
    basin(v, x0 + 0.35, y0 + 1.1, z0 + 0.89, r=0.2, mi=2); basin(v, x0 + 0.35, y0 + 2.1, z0 + 0.89, r=0.2, mi=2)
    faucet(v, x0 + 0.12, y0 + 1.1, z0 + 0.89, mi=3, dir=(1, 0)); faucet(v, x0 + 0.12, y0 + 2.1, z0 + 0.89, mi=3, dir=(1, 0))
    v.box(x0 + 0.02, x0 + 0.03, y0 + 0.7, y0 + 2.5, z0 + 1.1, z0 + 2.2, 4)
    _towel(v, x0 + 0.35, y0 + 1.6, z0 + 0.89, 5, w=0.24, d=0.16, rot=math.pi / 2)
    v.build("UpBath_Vanity", [M['oak'], M['marble'], M['ceramic'], M['chrome'], M['mirror'], M['linen_white']], smooth=True)
    dl = [(x0 + 1.5, y0 + 1.5), (x0 + 1.5, y0 + 3.5)]
    _downlights(M, 'upbath', dl, z1)
    _down_spots("L_upbath_dl", dl, z1, energy=24, spot=85)
    room_light("L_upbath", (x0, x1, y0, y1, z0, z1), energy=18)


def build_hall(M):
    x0, x1, y0, y1, z0, z1 = ROOMS['uphall']
    hx0, hx1, hy0, hy1 = STAIR_HOLE
    hole = (max(hx0, x0), min(hx1, x1), max(hy0, y0), min(hy1, y1))
    _finish(M, 'uphall', M['oak_floor'], faces='', holes=[hole], gaps='WEN')
    _ceiling_gear(M, 'uphall', z1, speakers=[(-3.5, 10.0), (-3.5, 15.0)], diffusers=[(-1.5, 16.8, 'X')], detector=(-2.0, 9.4))
    pc = MB()
    _floater(pc, 12.4, 14.0, PX_H1, z0 + 1.2, z0 + 2.4, along='Y', face=-1, mi_frame=0, mi_canvas=1)
    _floater(pc, 7.4, 9.0, PX_H1, z0 + 1.2, z0 + 2.4, along='Y', face=-1, mi_frame=0, mi_canvas=2)
    _floater(pc, -4.6, -2.6, 17.8 - 0.02, z0 + 1.3, z0 + 2.4, along='X', face=-1, mi_frame=0, mi_canvas=3)
    pc.build("Hall_Art", [M['walnut'], M['art_abstract'], M['art_bw'], M['art_teal']])
    bn = MB()
    bn.rcbox(-0.2, 13.2, z0 + 0.44, 1.6, 0.42, 0.08, r=0.03, mi=0, seg=2, puff=0.3)
    bn.cbox(-0.2, 13.2, z0 + 0.2, 1.5, 0.36, 0.4, 1)
    bn.drape(-0.9, -0.3, 13.0, 13.4, z0 + 0.48, t=0.025, mi=4, sag=0.045, rot=0.1, folds=2, seed=13)
    bn.cbox(-4.8, 10.0, z0 + 0.42, 0.42, 1.2, 0.04, 2)
    bn.cbox(-4.8, 10.0, z0 + 0.2, 0.36, 1.1, 0.4, 2)
    vase(bn, -4.8, 10.35, z0 + 0.44, h=0.3, r=0.1, mi=3, style='tall')
    branches(bn, -4.8, 10.35, z0 + 0.74, h=0.6, n=6, seed=15, mi=5, leaves=6, mi_leaf=6, spread=0.4)
    bn.lathe(-4.8, 9.7, z0 + 0.44, [(0, 0), (0.09, 0), (0.13, 0.04), (0.14, 0.05), (0.13, 0.05), (0.11, 0.03), (0, 0.025)], seg=20, mi=3)   # bowl
    bn.build("Hall_Bench", [M['fabric_sand'], M['oak'], M['walnut'], M['ceramic_black'], M['throw'], M['bark'], M['olive']], bevel=0.012)
    pl = MB()
    potted_plant(pl, 0.1, 11.4, z0 + 0.02, pot_r=0.28, pot_h=0.5, h=1.7, mi_pot=0, mi_leaf=1, mi_stem=2, seed=7, kind='olive')
    pl.build("Hall_Plant", [M['plant_pot'], M['olive'], M['bark']], smooth=True)
    dl = [(-0.6, y) for y in (9.0, 11.5, 14.0, 16.5)] + [(-4.6, y) for y in (9.5, 12.5, 15.5)]
    _downlights(M, 'uphall', dl, z1)
    _down_spots("L_hall_dl", dl, z1, energy=22, spot=85)
    area_light("L_hall_n", (-2.5, 13.5, z1 - 0.08), (5.0, 6.0), 24, WARM_SOFT)
    area_light("L_hall_s", (-0.2, 6.0, z1 - 0.08), (1.4, 3.5), 12, WARM_SOFT)
    _spot("L_hall_art1", (-0.2, 13.2, z1 - 0.05), (PX_H1, 13.2, z0 + 1.8), 25, 60)
    _spot("L_hall_art2", (-0.2, 8.2, z1 - 0.05), (PX_H1, 8.2, z0 + 1.8), 25, 60)


def build_boxroom(M):
    x0, x1, y0, y1, z0, z1 = ROOMS['boxroom']
    _finish(M, 'boxroom', M['oak_floor'], faces='', ceil_mat=M['ceiling'], gaps='N')
    # lighting: a perimeter cove washing the slatted walls + two slot lights over the seating (no flooding light box)
    _cove(M, 'Box', x0 + 0.05, x1 - 0.05, y0 + 0.05, y1 - 0.05, z1 - 0.02, M['emit_cove'], sides='WES', w=0.05)
    sl = [((x0 + x1) / 2 - 1.0, y0 + 3.0), ((x0 + x1) / 2 + 1.0, y0 + 3.0)]
    tl = MB(); _slot_lights(tl, sl, z1 - 0.02, 0, 1, along='X', L=0.9); tl.build("Box_Slots", [M['black'], M['emit_down']])
    _down_spots("L_box_slot", sl, z1, energy=18, spot=95, blend=0.8)
    sf = MB()
    sofa(sf, (x0 + x1) / 2, y0 + 3.4, 2.4, 0.95, rot=0.0, z=z0 + 0.02, mi_seat=0, arms=True, cushion_gap=0.03, soft=0.065, pillows=2, mi_pillow=1)
    cushion(sf, (x0 + x1) / 2 + 0.85, y0 + 3.65, z0 + 0.46, 0.45, 0.45, 0.14, 2, rot=-0.2, upright=True)
    armchair(sf, x1 - 0.7, y0 + 1.6, rot=-math.pi / 2 + 0.6, z=z0 + 0.02, w=0.8, d=0.8, mi=1, mi_legs=3)
    sf.drape((x0 + x1) / 2 - 1.1, (x0 + x1) / 2 - 0.4, y0 + 3.15, y0 + 3.7, z0 + 0.47, t=0.02, mi=4, sag=0.04, rot=0.1, folds=2, seed=17)
    sf.build("Box_Sofa", [M['fabric'], M['fabric_grey'], M['fabric_white'], M['oak'], M['throw']], bevel=0.012)
    ct = MB()
    round_table(ct, (x0 + x1) / 2, y0 + 1.9, z0 + 0.02, 0.45, h=0.36, mi=0, mi_leg=1, legs='drum')
    vase(ct, (x0 + x1) / 2 + 0.15, y0 + 1.85, z0 + 0.38, h=0.2, r=0.1, mi=2, style='round')
    books(ct, (x0 + x1) / 2 - 0.15, y0 + 1.95, z0 + 0.38, n=3, mi=4, rot=0.2, w=0.26, d=0.2)
    _bulb_floor_lamp(ct, x0 + 0.5, y0 + 3.4, z0 + 0.02, 1, 3, 5, h=1.55, shade_r=0.2)
    ct.cylinder(x1 - 0.55, y0 + 2.6, z0 + 0.02, z0 + 0.5, 0.18, seg=20, mi=0)                    # side table
    books(ct, x1 - 0.55, y0 + 2.6, z0 + 0.5, n=3, mi=4, rot=0.1, w=0.24, d=0.18)
    ct.build("Box_Table", [M['walnut'], M['brass'], M['ceramic'], M['lampshade'], M['book'], M['emit_warm']], smooth=True)
    _rug(M, 'Box', x0 + 0.5, x1 - 0.5, y0 + 1.0, y0 + 4.0, z0 + 0.02, M['rug'])
    room_light("L_boxroom", 'boxroom', energy=12)
    dl = [((x0 + x1) / 2 - 1.2, y0 + 2.4), ((x0 + x1) / 2 + 1.2, y0 + 2.4)]
    _downlights(M, 'boxroom', dl, z1)
    _down_spots("L_box_dl", dl, z1, energy=20, spot=85)


# ------------------------------------------------------------------ roof terraces
def build_front_terrace(M):
    """Turf terrace over the living/family pavilions (photos 22 / 30): long cream sofas along the parapet, teak side
    tables with trays + tumblers, an agave planter, lanterns."""
    z = Z_TERR_FRONT
    fu = MB()
    outdoor_sofa(fu, 12.15, 6.1, 2.4, 0.95, rot=-math.pi / 2, z=z, mi_frame=0, mi_cushion=1, seats=3)
    outdoor_sofa(fu, 12.15, 8.65, 2.4, 0.95, rot=-math.pi / 2, z=z, mi_frame=0, mi_cushion=1, seats=3)
    outdoor_sofa(fu, 9.6, 4.15, 2.0, 0.95, rot=math.pi, z=z, mi_frame=0, mi_cushion=1, seats=2)
    for (tx, ty) in ((10.9, 6.1), (10.9, 8.65)):
        # slatted teak coffee table top
        for i in range(7):
            fu.cbox(tx, ty - 0.36 + i * 0.12, z + 0.35, 0.8, 0.1, 0.03, 0)
        for sx in (-1, 1):
            for sy in (-1, 1):
                fu.cbox(tx + sx * 0.36, ty + sy * 0.36, z + 0.17, 0.05, 0.05, 0.34, 0)
        fu.cbox(tx, ty - 0.36, z + 0.31, 0.8, 0.05, 0.05, 0); fu.cbox(tx, ty + 0.36, z + 0.31, 0.8, 0.05, 0.05, 0)
    _tray(fu, 10.9, 6.1, z + 0.365, 0.36, 0.26, 2, rot=0.1)
    for (gx, gy) in ((10.82, 6.04), (10.98, 6.14)):
        fu.lathe(gx, gy, z + 0.377, [(0, 0), (0.032, 0), (0.034, 0.005), (0.037, 0.1), (0, 0.1)], seg=14, mi=3)     # tumblers
    fu.lathe(10.9, 8.65, z + 0.365, [(0, 0), (0.1, 0), (0.15, 0.04), (0.16, 0.05), (0.15, 0.05), (0.13, 0.03), (0, 0.025)], seg=20, mi=2)   # bowl
    fu.blob((10.9, 8.65, z + 0.41), 0.1, seg=12, rings=7, jitter=0.3, seed=2, mi=4, squash=0.5)                       # moss
    _lantern(fu, 12.25, 4.95, z, 5, 6, 7, 8, w=0.24, h=0.46)
    _lantern(fu, 12.25, 9.95, z, 5, 6, 7, 8, w=0.2, h=0.38)
    fu.build("FrontTerrace_Furniture", [M['teak'], M['fabric_white'], M['ceramic_black'], M['glass'], M['moss'], M['black_metal'], M['glass_frost'], M['ceramic_cream'], M['emit_warm']], bevel=0.012)
    pl = MB()
    potted_plant(pl, 8.4, 10.9, z, pot_r=0.32, pot_h=0.55, h=1.4, mi_pot=0, mi_leaf=1, mi_stem=2, seed=9, kind='olive')
    _agave(pl, 8.4, 4.4, z, 0, 3, n=20, seed=4, size=0.6)
    pl.build("FrontTerrace_Plants", [M['ceramic'], M['olive'], M['bark'], M['olive']], smooth=True)


def build_rear_terrace(M):
    """Roof dining terrace over the north arm (photo 21): 8-seat teak table (3 planks + breadboard ends on a trestle)
    with Jeanneret chairs, a linen runner + moss bowl, lanterns, olives in planters, a bench, loungers by the doors."""
    z = Z_TERR_REAR
    tx, ty = 15.6, 21.0
    fu = MB()
    L, W = 3.0, 1.1
    _teak_table(fu, tx, ty, z, L=L, W=W, h=0.74, top_t=0.06, mi=0, planks=4)
    # 8 Jeanneret compass chairs: 3 a side (chairs face -Y, so the far row is rotated pi) + one at each end
    for i in range(3):
        cx = tx - 0.9 + i * 0.9
        _jeanneret_chair(fu, cx, ty - 0.92, rot=math.pi + (i - 1) * 0.05, z=z, mi_wood=0, mi_cane=1)
        _jeanneret_chair(fu, cx, ty + 0.92, rot=(i - 1) * -0.05, z=z, mi_wood=0, mi_cane=1)
    _jeanneret_chair(fu, tx - 1.9, ty, rot=-math.pi / 2, z=z, mi_wood=0, mi_cane=1)
    _jeanneret_chair(fu, tx + 1.9, ty, rot=math.pi / 2, z=z, mi_wood=0, mi_cane=1)
    # centrepiece: a wide shallow black bowl heaped with moss balls (photo 21)
    fu.lathe(tx, ty, z + 0.74, [(0, 0), (0.16, 0), (0.30, 0.05), (0.36, 0.11), (0.33, 0.115), (0.28, 0.06), (0, 0.03)], seg=28, mi=2)
    rng = random.Random(21)
    for k in range(14):
        a = rng.uniform(0, 2 * math.pi); rr = rng.uniform(0.0, 0.22)
        fu.blob((tx + rr * math.cos(a), ty + rr * math.sin(a), z + 0.80 + rng.uniform(0.0, 0.05)), rng.uniform(0.07, 0.11),
                seg=12, rings=7, jitter=0.35, seed=300 + k, mi=3, squash=0.8)
    _lantern(fu, tx - 1.15, ty + 0.3, z + 0.74, 7, 8, 9, 10, w=0.16, h=0.3)
    _lantern(fu, tx + 1.15, ty - 0.3, z + 0.74, 7, 8, 9, 10, w=0.16, h=0.3)
    armchair(fu, 9.4, 19.7, rot=math.pi / 2 - 0.15, z=z, w=0.85, d=0.9, mi=4, mi_legs=0)
    armchair(fu, 9.4, 22.3, rot=math.pi / 2 + 0.15, z=z, w=0.85, d=0.9, mi=4, mi_legs=0)
    fu.cylinder(9.5, 21.0, z, z + 0.42, 0.24, seg=20, mi=5)
    _tray(fu, 9.5, 21.0, z + 0.42, 0.24, 0.18, 2, rot=0.2)
    fu.lathe(9.46, 20.98, z + 0.432, [(0, 0), (0.03, 0), (0.033, 0.005), (0.036, 0.09), (0, 0.09)], seg=14, mi=8)
    # teak bench along the north parapet
    for i in range(4):
        fu.cbox(19.5, 23.3 - 0.06 * 1.5 + i * 0.105 - 0.1, z + 0.42, 1.6, 0.09, 0.03, 0)
    for sx in (-1, 1):
        fu.cbox(19.5 + sx * 0.7, 23.15, z + 0.2, 0.06, 0.38, 0.4, 0)
    fu.build("RearTerrace_Furniture", [_local(M)['teak_warm'], _local(M)['cane_tan'], M['ceramic_black'], M['moss'], M['fabric_white'], M['ceramic'], M['linen_white'], M['black_metal'], M['glass'], M['ceramic_cream'], M['emit_warm']], bevel=0.008)
    pl = MB()
    potted_plant(pl, 22.8, 22.8, z, pot_r=0.34, pot_h=0.6, h=1.6, mi_pot=0, mi_leaf=1, mi_stem=2, seed=11, kind='olive')
    potted_plant(pl, 22.8, 19.0, z, pot_r=0.34, pot_h=0.6, h=1.5, mi_pot=0, mi_leaf=1, mi_stem=2, seed=13, kind='olive')
    pl.build("RearTerrace_Plants", [M['ceramic'], M['olive'], M['bark']], smooth=True)


# ------------------------------------------------------------------ entry point
def build(M):
    build_partitions(M)
    build_upfamily(M)
    build_upbed1(M)
    build_upbed2(M)
    build_upbed2b(M)
    build_upbed3(M)
    build_upsuite(M)
    build_upbath(M)
    build_hall(M)
    build_boxroom(M)
    build_front_terrace(M)
    build_rear_terrace(M)
