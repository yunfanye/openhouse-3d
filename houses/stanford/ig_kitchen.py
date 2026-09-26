"""The kitchen (photos 12, 13, 14; also 08, 11 in the background): honey-glazed maple cabinets with cathedral-arch
uppers and square raised-panel bases, a tan speckled laminate perimeter top with a rolled edge and a 4" splash, a dark
'granite' laminate island with a bevel edge, stainless appliances (slide-in gas range, dishwasher, top-freezer
refrigerator with black sides, countertop microwave), a black under-cabinet hood over a brushed-steel splash panel,
the sink window blind, cans and accessories.

House-local helper of interior_main (prefix ig_).  The layout is data (K below); each run lists its modules in the
order they stand, with the widths read from the photos through the solved cameras (see REFERENCES.md and cams/int_great.json).
"""
import math
import random
from .plan import *
from archviz.mesh import MB
from archviz.cladding import Face
from archviz import furnish as fu
from . import interior_main as im

XR = im.XR
FY = im.FRIDGE_Y
YR = YB1 - EWT                       # 11.65 rear wall face

# Layout (world metres) measured through the joint 12/13/14 solve (inputs in cams/int_great.json, 1.8-2.8 px rms)
# with standard appliance widths as checks: DW 0.62 (measured 9.47..10.09), range 0.76 (9.86..10.62), fridge 0.92 x 1.69.
X0 = im.PIER['x1']                   # 8.92: west end of the rear run and of the refrigerator-wall run (12: counter end 8.81-8.91)
K = dict(
    zt=0.915, slab=0.035, tk=0.10, tk_in=0.075, base_d=0.61, splash=0.10,
    up_z0=1.36, up_z1=2.14, up_d=0.31,
    # rear (sink) wall, x from the west end: (x0, x1, kind)
    rear_base=[(X0, 9.47, 'door1'), (9.47, 10.09, 'dw'), (10.09, 10.99, 'sink'), (10.99, XR - 0.61, 'door1'), (XR - 0.61, XR, 'blind')],
    rear_up=[(X0, 9.94, 2), (11.18, XR, 2)],
    sink=(10.17, 10.91),
    # right (range) wall, y from the south end (the counter-run stub) north to the corner: (y0, y1, kind)
    right_base=[(im.PANTRY[1][1] + 0.03, 9.86, 'door1'), (9.86, 10.62, 'range'), (10.62, YR - 0.61, 'door1')],
    right_up=[(im.PANTRY[1][1] + 0.07, 9.86, 1, None), (9.86, 10.62, 2, 1.84), (10.64, YR - 0.31, 2, None)],
    rng=(9.86, 10.62), hood=(1.68, 1.84),
    # refrigerator wall (y = FRIDGE_Y), x from the west end: counter run, then the fridge against the return
    fridge=(9.90, 10.81), fridge_h=1.69,
    fridge_base=[(X0, 9.40, 'door1'), (9.40, 9.88, 'door1')],
    fridge_up=[(X0, 9.88, 2, None)], fridge_top=(9.88, 10.83, 1.80),
    island=(9.05, 9.88, 9.00, 10.17),      # the base; the top overhangs 0.03 (solve: top 9.02..9.91 x 8.97..10.20)
    cans=[(9.58, 10.73), (10.43, 10.71), (11.35, 10.74), (10.87, 9.67), (9.53, 9.49), (9.56, 8.31)],
    spots=[(10.33, 11.40), (10.93, 11.40)],
)


def _mats(M):
    g = M.setdefault
    g('steel_face', M['steel_brushed_z'])
    return M


# ================================================================ cabinet modules
def _base_module(cab, hw, face, a0, a1, kind, flip=False):
    """Fronts of one base module on `face` (the carcass front plane; d outward): 'door1' = drawer over one door,
    'door2' = two drawers over two doors, 'sink' = two tilt-out false fronts over two doors, 'corner' = a blind
    corner (one drawer + one door at the open end), 'drawers' = three drawers."""
    zt, tk = K['zt'] - K['slab'], K['tk']
    zd = zt - 0.165
    gap = 0.003
    if kind in ('door1', 'corner'):
        fu.drawer_front(face, cab, a0 + gap, a1 - gap, zd + gap, zt - 0.012)
        fu.bar_pull(face, hw, (a0 + a1) / 2, (zd + zt) / 2 - 0.005, length=0.096)
        fu.raised_panel_door(face, cab, a0 + gap, a1 - gap, tk + 0.012, zd - gap, 'square')
        hx = a0 + 0.045 if not flip else a1 - 0.045
        fu.bar_pull(face, hw, hx, zd - 0.12, length=0.096, vertical=True)
    elif kind in ('door2', 'sink'):
        am = (a0 + a1) / 2
        for (b0, b1, side) in ((a0, am, 1), (am, a1, -1)):
            fu.drawer_front(face, cab, b0 + gap, b1 - gap, zd + gap, zt - 0.012)
            if kind == 'door2':
                fu.bar_pull(face, hw, (b0 + b1) / 2, (zd + zt) / 2 - 0.005, length=0.096)
            fu.raised_panel_door(face, cab, b0 + gap, b1 - gap, tk + 0.012, zd - gap, 'square')
            hx = b1 - 0.045 if side > 0 else b0 + 0.045
            fu.bar_pull(face, hw, hx, zd - 0.12, length=0.096, vertical=True)
    elif kind == 'drawers':
        n = 3
        hh = (zt - 0.012 - tk - 0.012) / n
        for i in range(n):
            z0 = tk + 0.012 + i * hh
            fu.drawer_front(face, cab, a0 + gap, a1 - gap, z0 + gap, z0 + hh - gap)
            fu.bar_pull(face, hw, (a0 + a1) / 2, z0 + hh * 0.62, length=0.128)


def _upper_module(cab, hw, face, a0, a1, n, z0, z1):
    W = (a1 - a0) / n
    gap = 0.003
    for i in range(n):
        b0, b1 = a0 + i * W + gap, a0 + (i + 1) * W - gap
        fu.raised_panel_door(face, cab, b0, b1, z0 + 0.012, z1 - 0.004, 'arch')
        hx = b1 - 0.045 if (i % 2 == 0 and n > 1) else b0 + 0.045
        if n == 1:
            hx = b0 + 0.045
        fu.bar_pull(face, hw, hx, z0 + 0.13, length=0.096, vertical=True)


def _crown(cab, face, a0, a1, z, d_back, ends=(True, True), along='X', wall_b=None, sgn=-1):
    """Stepped crown moulding on the uppers' front at z (top of the box), returning along exposed ends."""
    steps = ((0.0, 0.018, 0.012), (0.018, 0.034, 0.024), (0.034, 0.052, 0.038), (0.052, 0.068, 0.05))
    for (z0, z1, out) in steps:
        face.box(cab, a0 - out * ends[0], a1 + out * ends[1], 0.0, out, z + z0, z + z1, 0)


def kitchen(M):
    _mats(M)
    cab, cab_h, hw, top_b, top_d, steel, black, glass, knobs = (MB() for _ in range(9))
    zt, slab, tk, tkin, BD = K['zt'], K['slab'], K['tk'], K['tk_in'], K['base_d']
    zc = zt - slab
    U0, U1, UD = K['up_z0'], K['up_z1'], K['up_d']
    # ---------------- rear run (sink wall): carcasses, toe kick, fronts
    yf = YR - BD
    fr = Face('X', yf, -1)
    for (a0, a1, kind) in K['rear_base']:
        if kind == 'dw':
            fu.dishwasher(steel, black, Face('X', YR, -1), a0, a1, top=zc - 0.005, depth=BD + 0.012, mi=0, mi_black=0)
            continue
        cab.box(a0, a1, yf, YR, tk, zc)
        cab.box(a0 + 0.001, a1 - 0.001, yf + tkin, YR, 0.0, tk)
        if kind != 'blind':                                  # the blind corner is covered by the right run's first cabinet
            _base_module(cab, hw, fr, a0, a1, kind, flip=(kind == 'door1' and a0 < 9.0))
    # finished end panel at the run's west end (photo 12: exposed left side)
    x_end = K['rear_base'][0][0]
    cab.box(x_end - 0.019, x_end, yf - 0.019, YR, 0.0, zc)
    # ---------------- right run (range wall)
    xf = XR - BD
    frr = Face('Y', xf, -1)
    for (a0, a1, kind) in K['right_base']:
        if kind == 'range':
            continue
        cab.box(xf, XR, a0, a1, tk, zc)
        cab.box(xf + tkin, XR, a0 + 0.001, a1 - 0.001, 0.0, tk)
        _base_module(cab, hw, frr, a0, a1, kind, flip=True)
    # ---------------- refrigerator-wall run (faces +Y)
    yff = FY + BD
    ffr = Face('X', yff, +1)
    for (a0, a1, kind) in K['fridge_base']:
        cab.box(a0, a1, FY, yff, tk, zc)
        cab.box(a0 + 0.001, a1 - 0.001, FY, yff - tkin, 0.0, tk)
        _base_module(cab, hw, ffr, a0, a1, kind)
    x_fe = K['fridge_base'][0][0]                                            # the run butts into the pier (photo 14)
    # ---------------- counters: rolled-edge perimeter laminate + 4" splash; the sink cut-out
    sx0, sx1 = K['sink']
    _counter(top_b, x_end - 0.02, XR, yf - 0.03, YR, zc, zt, front='-Y', hole=(sx0, sx1, YR - 0.55, YR - 0.10))
    ry0 = K['right_base'][0][0]
    y_rng0, y_rng1 = K['rng']
    _counter(top_b, xf - 0.03, XR, ry0, y_rng0, zc, zt, front='-X')
    _counter(top_b, xf - 0.03, XR, y_rng1, yf - 0.03, zc, zt, front='-X')
    _counter(top_b, x_fe, K['fridge_base'][-1][1], FY, yff + 0.03, zc, zt, front='+Y')
    sp = K['splash']
    top_b.box(x_end - 0.02, XR, YR - 0.012, YR - 0.001, zt, zt + sp)
    top_b.box(XR - 0.012, XR - 0.001, ry0, y_rng0 - 0.06, zt, zt + sp)
    top_b.box(XR - 0.012, XR - 0.001, y_rng1 + 0.06, YR, zt, zt + sp)
    top_b.box(x_fe, K['fridge_base'][-1][1], FY + 0.001, FY + 0.012, zt, zt + sp)
    # ---------------- sink (double stainless bowl, pull-down faucet, soap pump)
    yb0, yb1 = YR - 0.53, YR - 0.13
    sm = (sx0 + sx1) / 2
    for (a0, a1) in ((sx0 + 0.02, sm - 0.01), (sm + 0.01, sx1 - 0.02)):
        steel.box(a0, a1, yb0, yb1, zt - 0.20, zt - 0.19)
        steel.box(a0, a1, yb0, yb0 + 0.008, zt - 0.20, zt - 0.002)
        steel.box(a0, a1, yb1 - 0.008, yb1, zt - 0.20, zt - 0.002)
        steel.box(a0, a0 + 0.008, yb0, yb1, zt - 0.20, zt - 0.002)
        steel.box(a1 - 0.008, a1, yb0, yb1, zt - 0.20, zt - 0.002)
        steel.cylinder((a0 + a1) / 2, (yb0 + yb1) / 2, zt - 0.195, zt - 0.188, 0.045, seg=16)
    steel.box(sx0, sx1, yb0 - 0.02, yb0, zt - 0.002, zt + 0.004)
    steel.box(sx0, sx1, yb1, yb1 + 0.03, zt - 0.002, zt + 0.004)
    steel.box(sx0, sx0 + 0.02, yb0, yb1, zt - 0.002, zt + 0.004)
    steel.box(sx1 - 0.02, sx1, yb0, yb1, zt - 0.002, zt + 0.004)
    fx = sm + 0.04
    steel.cylinder(fx, YR - 0.07, zt, zt + 0.04, 0.03, seg=16)
    steel.path_tube([(fx, YR - 0.07, zt + 0.03), (fx, YR - 0.07, zt + 0.30), (fx, YR - 0.09, zt + 0.40), (fx, YR - 0.16, zt + 0.43),
                     (fx, YR - 0.23, zt + 0.39), (fx, YR - 0.25, zt + 0.30)], 0.014, seg=12)
    steel.cylinder(fx, YR - 0.25, zt + 0.22, zt + 0.31, 0.017, seg=12)
    steel.path_tube([(fx + 0.035, YR - 0.07, zt + 0.12), (fx + 0.07, YR - 0.07, zt + 0.16)], 0.006, seg=6)
    steel.cylinder(sx1 + 0.06, YR - 0.07, zt, zt + 0.10, 0.02, seg=12)
    steel.path_tube([(sx1 + 0.06, YR - 0.07, zt + 0.10), (sx1 + 0.06, YR - 0.10, zt + 0.12)], 0.005, seg=6)
    # ---------------- uppers: arched raised-panel doors, crown; the right-wall bank over the hood is short
    ufr = Face('X', YR - UD, -1)
    for i, (a0, a1, n) in enumerate(K['rear_up']):
        cab.box(a0, a1, YR - UD, YR, U0, U1)
        _upper_module(cab, hw, ufr, a0, a1 - (UD if a1 >= XR - 0.01 else 0.0), n, U0, U1)
        if a1 >= XR - 0.01:
            ufr.box(cab, a1 - UD, a1, 0.0, 0.019, U0, U1)                           # the corner box's front stile
        _crown(cab, ufr, a0, a1, U1, UD, ends=(True, a1 < XR - 0.01))
        # exposed ends: crown returns
        for (ae, s_) in ((a0, -1), (a1, 1)):
            if ae >= XR - 0.01:
                continue
            for (z0_, z1_, out) in ((0.0, 0.018, 0.012), (0.018, 0.034, 0.024), (0.034, 0.052, 0.038), (0.052, 0.068, 0.05)):
                x_a, x_b = sorted((ae, ae + s_ * out))
                cab.box(x_a, x_b, YR - UD - out, YR, U1 + z0_, U1 + z1_)
    urf = Face('Y', XR - UD, -1)
    for (a0, a1, n, zlow) in K['right_up']:
        z0 = zlow if zlow else U0
        cab.box(XR - UD, XR, a0, a1, z0, U1)
        _upper_module(cab, hw, urf, a0, a1, n, z0, U1)
        _crown(cab, urf, a0, a1, U1, UD, ends=(False, False))
    for (a0, a1, n, zlow) in K['fridge_up']:
        z0 = zlow if zlow else U0
        cab.box(a0, a1, FY, FY + UD, z0, U1)
        _upper_module(cab, hw, Face('X', FY + UD, +1), a0, a1, n, z0, U1)
        _crown(cab, Face('X', FY + UD, +1), a0, a1, U1, UD, ends=(True, False))
    fa0, fa1, fz0 = K['fridge_top']
    cab.box(fa0, fa1, FY, FY + 0.62, fz0, U1)                                          # deep cabinet over the fridge
    _upper_module(cab, hw, Face('X', FY + 0.62, +1), fa0, fa1, 2, fz0, U1)
    _crown(cab, Face('X', FY + 0.62, +1), fa0, fa1, U1, 0.62, ends=(True, True))
    cab.box(fa0 - 0.019, fa0, FY, FY + 0.62, fz0, U1)                                  # its exposed west side
    # ---------------- appliances
    y0r, y1r = K['rng']
    fu.gas_range(steel, black, glass, knobs, Face('Y', XR, -1), y0r + 0.003, y1r - 0.003, 0.0, depth=0.665, top=zt)
    hz0, hz1 = K['hood']
    fu.under_hood(steel, black, Face('Y', XR, -1), y0r, y1r, hz0, hz1, depth=0.50, finish='black')
    steel.box(XR - 0.013, XR - 0.008, y0r - 0.02, y1r + 0.02, zt + sp, hz0)                  # brushed splash panel
    f0, f1 = K['fridge']
    fu.fridge_top_freezer(steel, black, Face('X', FY, +1), f0, f1, h=K['fridge_h'], depth=0.76, split=0.64)
    # ---------------- island: maple base (drawers + doors facing the range; flat panels in a greyer stain on the other
    # three sides: photos 12 / 13 read them grey-brown (128, 93, 68) next to the honey fronts), bevel-edge top
    ix0, ix1, iy0, iy1 = K['island']
    isl = MB()
    isl.box(ix0 + 0.075, ix1 - 0.075, iy0 + 0.075, iy1 - 0.075, 0.0, tk)
    isl.box(ix0, ix1, iy0, iy1, tk, zc)
    fe = Face('Y', ix1, +1)
    _base_module(cab, hw, fe, iy0 + 0.02, iy1 - 0.02, 'door2')
    for (f_, a0, a1) in ((Face('X', iy0, -1), ix0, ix1), (Face('X', iy1, +1), ix0, ix1), (Face('Y', ix0, -1), iy0, iy1)):
        am = (a0 + a1) / 2
        f_.box(isl, a0 + 0.02, a1 - 0.02, 0.0, 0.006, tk, zc - 0.01)                         # flat panels + a centre stile
        f_.box(isl, am - 0.035, am + 0.035, 0.006, 0.012, tk, zc - 0.07)
        f_.box(isl, a0 + 0.02, a1 - 0.02, 0.006, 0.0135, zc - 0.07, zc - 0.01)
    isl.build("Kitchen_IslandBase", [M['maple_island']])
    _bevel_top(top_d, ix0 - 0.035, ix1 + 0.035, iy0 - 0.035, iy1 + 0.035, zc, zt)
    cab.build("Kitchen_Cabinets", [M['maple']])
    top_b.build("Kitchen_Counters", [M['counter_beige']])
    top_d.build("Kitchen_IslandTop", [M['counter_dark']])
    steel.build("Kitchen_Stainless", [M['steel_face']])
    black.build("Kitchen_Black", [M['appliance_black']])
    glass.build("Kitchen_OvenGlass", [M['firebox_glass']])
    knobs.build("Kitchen_Knobs", [M['steel_face']])
    hw.build("Kitchen_Hardware", [M['nickel_brushed']])
    return dict(island=(ix0, ix1, iy0, iy1), zt=zt)


def _counter(mb, x0, x1, y0, y1, z0, z1, front='-Y', hole=None):
    """Post-formed laminate top: a slab with a rolled (bullnose) front edge drawn as a half-round along `front`."""
    if hole:
        hx0, hx1, hy0, hy1 = hole
        mb.plate(x0, x1, y0, y1, z0, z1, holes=[(hx0, hx1, hy0, hy1)])
    else:
        mb.box(x0, x1, y0, y1, z0, z1)
    r = (z1 - z0) / 2
    zc = (z0 + z1) / 2
    if front in ('-Y', '+Y'):
        yy = y0 if front == '-Y' else y1
        s = -1 if front == '-Y' else 1
        secs = []
        for k in range(9):
            a = -math.pi / 2 + math.pi * k / 8
            secs.append((yy + s * r * 0.6 * math.cos(a), zc + r * math.sin(a)))
        for i in range(len(secs) - 1):
            (ya, za), (yb, zb) = secs[i], secs[i + 1]
            mb.hexa([(x0, ya, za), (x1, ya, za), (x1, yb, zb), (x0, yb, zb), (x0, yy, za), (x1, yy, za), (x1, yy, zb), (x0, yy, zb)])
    else:
        xx = x0 if front == '-X' else x1
        s = -1 if front == '-X' else 1
        secs = []
        for k in range(9):
            a = -math.pi / 2 + math.pi * k / 8
            secs.append((xx + s * r * 0.6 * math.cos(a), zc + r * math.sin(a)))
        for i in range(len(secs) - 1):
            (xa, za), (xb, zb) = secs[i], secs[i + 1]
            mb.hexa([(xa, y0, za), (xa, y1, za), (xb, y1, zb), (xb, y0, zb), (xx, y0, za), (xx, y1, za), (xx, y1, zb), (xx, y0, zb)])


def _bevel_top(mb, x0, x1, y0, y1, z0, z1, bevel=0.012):
    """Island top with a 45-degree bevel on all four top edges (photo 12: a light line above a dark edge band)."""
    b = bevel
    mb.box(x0, x1, y0, y1, z0, z1 - b)
    mb.box(x0 + b, x1 - b, y0 + b, y1 - b, z1 - b, z1)
    # four sloped strips
    zb, ztp = z1 - b, z1
    P = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    Q = [(x0 + b, y0 + b), (x1 - b, y0 + b), (x1 - b, y1 - b), (x0 + b, y1 - b)]
    for i in range(4):
        j = (i + 1) % 4
        mb._add([(P[i][0], P[i][1], zb), (P[j][0], P[j][1], zb), (Q[j][0], Q[j][1], ztp), (Q[i][0], Q[i][1], ztp)], [(0, 1, 2, 3)], 0)


# ================================================================ accessories (photos 12-14)
def accessories(M, kit):
    ix0, ix1, iy0, iy1 = kit['island']
    zt = kit['zt']
    rng = random.Random(8)
    # ruby-glass footed fruit bowl with peaches, apples and a banana on the island (12, 13, 14)
    bx, by = (ix0 + ix1) / 2 - 0.05, (iy0 + iy1) / 2 + 0.05
    bw = MB()
    prof = [(0.0, 0.0), (0.06, 0.0), (0.05, 0.015), (0.035, 0.03), (0.09, 0.05), (0.20, 0.10), (0.235, 0.135), (0.225, 0.137),
            (0.19, 0.105), (0.085, 0.058), (0.0, 0.052)]
    secs = []
    n = 36
    for (r, z) in prof:
        sec = []
        for i in range(n):
            t = 2 * math.pi * i / n
            rr = r * (1.0 + (0.06 * math.cos(12 * t) if z > 0.09 else 0.0))
            sec.append((bx + rr * math.cos(t), by + rr * math.sin(t), zt + z))
        secs.append(sec)
    bw.sweep(secs, 0, close=False, caps=False)
    bw.build("Kitchen_FruitBowl", [M['red_glass']], smooth=True)
    fr, fr2 = MB(), MB()
    for i in range(7):
        a = 2 * math.pi * i / 7 + rng.uniform(-0.2, 0.2)
        rr = rng.uniform(0.03, 0.11)
        p = (bx + rr * math.cos(a), by + rr * math.sin(a), zt + 0.10 + rng.uniform(0.0, 0.04))
        (fr if i % 3 else fr2).sphere(p, rng.uniform(0.038, 0.045), seg=14, rings=10, squash=0.92)
    fr.build("Kitchen_Peaches", [M['peach']], smooth=True)
    fr2.build("Kitchen_Apples", [M['apple_red']], smooth=True)
    # floral kettle + three floral canisters right of the sink (12)
    kk = MB()
    kx, ky = K['sink'][1] + 0.32, YR - 0.20
    kk.lathe(kx, ky, zt, [(0.0, 0.0), (0.075, 0.0), (0.09, 0.05), (0.085, 0.15), (0.06, 0.20), (0.02, 0.215), (0.0, 0.215)], seg=20)
    kk.path_tube([(kx - 0.07, ky, zt + 0.18), (kx - 0.13, ky, zt + 0.17), (kx - 0.13, ky, zt + 0.06), (kx - 0.08, ky, zt + 0.04)], 0.009, seg=6)
    kk.path_tube([(kx + 0.08, ky, zt + 0.10), (kx + 0.14, ky, zt + 0.16), (kx + 0.16, ky, zt + 0.17)], 0.012, seg=6)
    for k, (dx, h) in enumerate(((0.28, 0.21), (0.40, 0.25), (0.53, 0.20))):
        kk.box(kx + dx - 0.055, kx + dx + 0.055, YR - 0.20 - 0.055, YR - 0.20 + 0.055, zt, zt + h)
        kk.box(kx + dx - 0.058, kx + dx + 0.058, YR - 0.20 - 0.058, YR - 0.20 + 0.058, zt + h, zt + h + 0.02)
    kk.build("Kitchen_KettleCanisters", [M['ceramic_floral']], smooth=True)
    # stainless 2-slice toaster at the counter's south end by the pantry (12, 13)
    ts = MB()
    ty = K['right_base'][0][0] + 0.12
    ts.rbox(XR - 0.36, XR - 0.18, ty - 0.14, ty + 0.14, zt, zt + 0.19, 0.02, 0)
    ts.box(XR - 0.33, XR - 0.21, ty - 0.10, ty + 0.10, zt + 0.19, zt + 0.192, 1)
    ts.build("Kitchen_Toaster", [M['steel_face'], M['appliance_black']], smooth=True)
    # countertop microwave on the refrigerator-wall run (13, 14)
    mw_s, mw_b, mw_g = MB(), MB(), MB()
    fb = K['fridge_base']
    fu.microwave(mw_s, mw_b, mw_g, Face('X', FY, +1), fb[-1][1] - 0.60, fb[-1][1] - 0.06, zt, h=0.31, depth=0.43)
    mw_s.build("Kitchen_Microwave", [M['steel_face']])
    mw_b.build("Kitchen_MicrowaveBlack", [M['appliance_black']])
    mw_g.build("Kitchen_MicrowaveGlass", [M['glass_smoke']])
    # salt / pepper mills, a canister and a cutting board on the fridge-wall counter (14)
    sm = MB()
    for k, x in enumerate((fb[0][0] + 0.12, fb[0][0] + 0.20)):
        sm.lathe(x, FY + 0.18, zt, [(0.0, 0.0), (0.025, 0.0), (0.03, 0.05), (0.022, 0.12), (0.028, 0.18), (0.012, 0.20), (0.0, 0.2)], seg=14)
    sm.build("Kitchen_Mills", [M['glass_clear']])
    cb = MB()
    cb.box(fb[0][0] + 0.30, fb[0][0] + 0.52, FY + 0.03, FY + 0.05, zt, zt + 0.30)
    cb.build("Kitchen_Board", [M['espresso_v']])
    # on top of the uppers: a black pot of trailing pothos (12 left), a trailing plant right of the window, a silver
    # pitcher in the corner, a white ginger jar over the hood, a green bottle vase (13)
    from . import ig_staging as st
    zt_up = K['up_z1'] + 0.07
    x0 = K['rear_up'][0][0]
    st.plant("Plant_PothosUpperL", (x0 + 0.20, YR - 0.16, zt_up), 'pothos', 0.3, pot='black', pot_r=0.10, pot_h=0.13, seed=31,
             trails=[[(x0 + 0.12, YR - 0.25, zt_up + 0.10), (x0 + 0.02, YR - 0.33, zt_up - 0.05), (x0 - 0.04, YR - 0.36, 1.95),
                      (x0 - 0.05, YR - 0.38, 1.65), (x0 - 0.02, YR - 0.40, 1.45)],
                     [(x0 + 0.25, YR - 0.28, zt_up + 0.05), (x0 + 0.18, YR - 0.36, zt_up - 0.02), (x0 + 0.05, YR - 0.40, 2.05)]])
    x1 = K['rear_up'][1][0]
    st.plant("Plant_PothosUpperR", (x1 + 0.12, YR - 0.15, zt_up), 'pothos', 0.25, pot='black', pot_r=0.08, pot_h=0.10, seed=32,
             trails=[[(x1 + 0.05, YR - 0.28, zt_up + 0.02), (x1 - 0.02, YR - 0.33, 2.05), (x1 - 0.03, YR - 0.34, 1.90)]])
    orn = MB()
    orn.lathe(XR - 0.18, YR - 0.16, zt_up, [(0.0, 0.0), (0.05, 0.0), (0.07, 0.08), (0.05, 0.16), (0.03, 0.2), (0.045, 0.24), (0.0, 0.24)], seg=16)
    orn.build("Kitchen_Pitcher", [M['pewter']], smooth=True)
    jar = MB()
    jar.lathe(XR - 0.17, (K['rng'][0] + K['rng'][1]) / 2, zt_up, [(0.0, 0.0), (0.06, 0.0), (0.10, 0.06), (0.09, 0.12), (0.05, 0.15),
                                                                (0.03, 0.16), (0.0, 0.17)], seg=20)
    jar.build("Kitchen_GingerJar", [M['ceramic']], smooth=True)
    gb = MB()
    gb.lathe(XR - 0.17, K['rng'][0] - 0.25, zt_up, [(0.0, 0.0), (0.045, 0.0), (0.05, 0.10), (0.02, 0.18), (0.012, 0.26), (0.0, 0.26)], seg=16)
    gb.build("Kitchen_BottleVase", [M['glass_green']], smooth=True)
    # outlets / switch plates on the backsplash walls (12)
    op = MB()
    fwr = Face('X', YR, -1)
    for (x, z, w, h) in ((8.95, 1.15, 0.075, 0.115), (9.45, 1.13, 0.07, 0.115), (10.95, 1.12, 0.07, 0.115)):
        fwr.box(op, x - w / 2, x + w / 2, 0.007, 0.013, z - h / 2, z + h / 2, 0)
    fwl = Face('Y', XR, -1)
    for (y, z) in ((10.85, 1.12), (9.62, 1.12)):
        fwl.box(op, y - 0.035, y + 0.035, 0.007, 0.013, z - 0.057, z + 0.057, 0)
    ix0, ix1, iy0, iy1 = kit['island']
    op.box(ix1 - 0.20, ix1 - 0.13, iy1 + 0.014, iy1 + 0.019, 0.42, 0.53)                            # island outlet (13, 14)
    op.build("Kitchen_Plates", [M['outlet']])
    # recessed cans (photos 12-14: two rows over the counters + one over the island)
    im.recessed(M, "Kitchen_Cans", K['cans'], energy=8)
    im.recessed(M, "Kitchen_Spots", K['spots'], energy=5, spot=math.radians(60))
