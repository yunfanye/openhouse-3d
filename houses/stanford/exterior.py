"""Exterior envelope: walls with openings, lap siding / brick veneer, trim, window + door units, shutters, porch,
the roof system (main side gable, left front gable, right cross gable, brick-bay gable, first-floor shed with its
left wrap and hip) with fascia, soffits, rakes, gutters and downspouts, roof vents, exterior lights and small wall
fixtures.  Positions: plan.py; evidence: EXT's joint facade solve (photos 01, 02, 03, 25, 30, 31) and REFERENCES.md.

Per-photo sun: `before_render(scene, cam)` aims the sun lamp of each exterior photograph (shadow directions read in
01, 02, 03, 25, 27, 28, 30) and restores the default day sun for every other camera."""
import math
import os
from .plan import *
from archviz.mesh import MB, collection
from archviz.lights import add_light
from archviz.cladding import Face, lap_siding, corner_board, band, holed_wall, j_channel
from archviz import fenestration as fen
from archviz import roofing as rf

EXPOSURE = 0.19            # lap siding exposure (photo 25: ~12 px per course at 62.6 px/m)
Z_SIDING0 = Z_GRADE + 0.15
RTH = 0.10                 # roof slab thickness
ZT = Z_ROOF_WALL           # roof top surface at the upper wall lines (5.59; joint solve 5.59 +/- 0.03)
KE, KR = OVH, OVH_RAKE     # eave / rake overhangs
YU = globals().get('YB0_UP', YB0)   # the UPPER front wall faces (plan.YB0_UP when defined; the porch door wall stays at YB0)
Y_RIDGE = (CEN[2] + YB1) / 2
Z_RIDGE = ZT + (Y_RIDGE - CEN[2]) * P_MAIN            # 8.27 (aerials 31 + 32 alone: 8.26 +/- 0.08)
HALF_X = (XB1 - RGABLE[0]) / 2                        # right cross gable half-span
P_CROSS = (Z_RIDGE - ZT) / HALF_X                     # its ridge = the main ridge (junction on the ridge line, 30 / 31)
HALF_L = (LGABLE[1] - LGABLE[0]) / 2
ZF_MAIN = ZT - KE * P_MAIN                            # fascia top at the main eaves
SOFFIT_MAIN = ZF_MAIN - 0.19
Z_GTRI = Z_SIDING0 + math.floor((Z_PLATE - Z_SIDING0) / EXPOSURE + 1e-6) * EXPOSURE   # course line where gable triangles start
J_W = 0.022                # J-channel width around openings in siding (narrow white vinyl frames, photos 25 / 27 / 28)
UPPER_PAINT = 'paint_beige'
# soffit heights over the eave walls (siding stops under a narrow frieze there); other siding walls run to their top
SOFFIT = {'rear': SOFFIT_MAIN, 'centre': SOFFIT_MAIN, 'cen_lret': ZT - KE * P_GABLE - 0.19,
          'cen_rret': ZT - KE * P_CROSS - 0.19, 'garage_left': Z_EAVE1, 'garage_rear': Z_EAVE1, 'porch_left': Z_PORCH_CEIL}


def _face(w):
    b = w['b0'] if w['out'] < 0 else w['b1']
    return Face(w['along'], b, w['out'])


def _depth(w):
    return w['b1'] - w['b0']


def _openings_in(w):
    return [o for o in OPENINGS if o['along'] == w['along'] and w['b0'] - 1e-4 <= o['b'] <= w['b1'] + 1e-4
            and o['a0'] < w['a1'] and o['a1'] > w['a0'] and o['z0'] < w['z1'] and o['z1'] > w['z0']]


def _header_h(o):
    return 0.30 if o.get('header') else 0.0


# ================================================================ walls + cladding
def walls(M):
    shell = MB()          # structure: slot 0 siding backing, 1 brick X, 2 brick Y, 3 interior white
    sid = MB()            # lap siding courses
    trim = MB()           # white trim
    brick_x, brick_y = MB(), MB()
    for w in WALLS:
        holes = holes_for(w)
        mi = {'siding': 0, 'brick': 1 if w['along'] == 'X' else 2, 'int': 3}[w['kind']]
        holed_wall(shell, w["along"], w["a0"], w["a1"], w["b0"], w["b1"], w["z0"], w["z1"], holes=holes, mi=mi)
        if w['kind'] != 'siding':
            continue
        f = _face(w)
        cut = []
        for o in _openings_in(w):
            cut.append((o['a0'] - J_W - 0.004, o['a1'] + J_W + 0.004, o['z0'] - J_W - 0.004,
                        o['z1'] + J_W + 0.004 + _header_h(o)))
        z0 = max(w['z0'], Z_SIDING0)
        if w['name'] == 'left_upper':
            z0 = Z_UP                               # below: left_main (rear part) or the garage wrap roof (front part)
        if w['name'] in SOFFIT:
            top = SOFFIT[w['name']] - 0.085
            band(trim, f, w['a0'], w['a1'], top, SOFFIT[w['name']] + 0.005)          # narrow frieze under the soffit
        elif w["z1"] >= Z_PLATE - 1e-6:
            top = Z_GTRI                            # the gable triangle's courses continue from here
        else:
            top = w['z1']
        lap_siding(sid, f, w['a0'], w['a1'], z0, top, holes=cut, exposure=EXPOSURE, start=Z_SIDING0, fit_holes=True)
    shell.build("Shell", [M['siding_back'], M['brick'], M['brick_y'], M['paint_white']])
    sid.build("Siding", [M['siding']])
    # outside corner boards (siding walls only; the brick bay has returns)
    zcr = ZT - 0.20                                 # top of a gable-end corner board (under the rake soffit)
    corners = [  # (along, b, out, a, side, z0, z1)
        ('Y', GAR[0], -1, 0.0, +1, Z_SIDING0, Z_EAVE1 - 0.01),           # garage front-left, left face
        ('Y', GAR[0], -1, GAR[3], -1, Z_SIDING0, Z_EAVE1 - 0.01),        # garage rear-left, left face
        ('X', GAR[3] + EWT, +1, GAR[0], +1, Z_SIDING0, Z_EAVE1 - 0.01),  # garage rear-left, rear face
        ('Y', XB0, -1, YB1, -1, Z_SIDING0, zcr),                         # block rear-left, left face
        ('X', YB1, +1, XB0, +1, Z_SIDING0, SOFFIT_MAIN),                 # block rear-left, rear face
        ('X', YB1, +1, XB1, -1, Z_SIDING0, SOFFIT_MAIN),                 # block rear-right, rear face
        ('Y', XB1, +1, YB1, -1, Z_SIDING0, zcr),                         # block rear-right, right face
        ('Y', XB0, -1, YU, +1, Z_UP - 0.2, zcr),                        # upper front-left, left face
        ('X', YU, -1, XB0, +1, Z_UP - 0.2, ZT - 0.24),                  # upper front-left, front face
        ('X', YU, -1, LGABLE[1], -1, Z_UP - 0.2, ZT - 0.24),            # left gable right corner
        ('X', YU, -1, RGABLE[0], +1, Z_UP - 0.2, ZT - 0.24),            # right gable left corner
        ('Y', CEN[0] + EWT, +1, YU, +1, Z_UP - 0.2, SOFFIT['cen_lret']),  # recess returns at the gable corners
        ('Y', CEN[1] - EWT, -1, YU, +1, Z_UP - 0.2, SOFFIT['cen_rret']),
        ('Y', XB1, +1, YB0, +1, Z_SIDING0, zcr),                         # right wall front corner (behind the bay return)
    ]
    for (al, b, out, a, side, z0, z1) in corners:
        corner_board(trim, Face(al, b, out), a, z0, z1, side=side, w=0.09)
    trim.build("Trim", [M['trim']])
    brick_details(M, brick_x, brick_y)


def brick_details(M, brick_x, brick_y):
    """Soldier courses, rowlock sills and steps, precast keystones, the bay's gable triangle (photos 01, 02, 03, 30)."""
    rowlock = MB()
    stone = MB()
    fg = Face('X', 0.0, -1)
    # the garage front: a continuous soldier course along the top of the brick (01, 03: 1.95 .. 2.17)
    fg.box(brick_x, GAR[0] - 0.002, GAR[1], 0.0, 0.012, Z_BRICK_TOP - 0.22, Z_BRICK_TOP)
    for o in OPENINGS:
        if o['kind'] not in ('garage_door', 'window') or o['b'] > 1.2 or o['along'] != 'X':
            continue
        f = Face('X', Y_BAY if o['b'] > Y_BAY - 1e-3 else 0.0, -1)
        if o['name'] not in ('garage_door', 'garage_win'):       # the bay windows: soldier course over the head
            f.box(brick_x, o['a0'] - 0.10, o['a1'] + 0.10, 0.0, 0.012, o['z1'] + 0.035, o['z1'] + 0.245)
            if o.get('keystone'):                                 # precast keystone at its centre (photo 03)
                am = (o['a0'] + o['a1']) / 2
                f.quad8(stone, [(am - 0.085, -0.005, o['z1'] + 0.04), (am + 0.085, -0.005, o['z1'] + 0.04),
                                (am + 0.085, 0.03, o['z1'] + 0.04), (am - 0.085, 0.03, o['z1'] + 0.04),
                                (am - 0.105, -0.005, o['z1'] + 0.29), (am + 0.105, -0.005, o['z1'] + 0.29),
                                (am + 0.105, 0.03, o['z1'] + 0.29), (am - 0.105, 0.03, o['z1'] + 0.29)])
        if o['kind'] == 'window':                                 # rowlock sill: bricks on edge, sloped, proud of the face
            w0, w1 = o['a0'] - 0.07, o['a1'] + 0.07
            f.quad8(rowlock, [(w0, -0.03, o['z0'] - 0.115), (w1, -0.03, o['z0'] - 0.115), (w1, 0.045, o['z0'] - 0.115), (w0, 0.045, o['z0'] - 0.115),
                              (w0, -0.03, o['z0'] + 0.002), (w1, -0.03, o['z0'] + 0.002), (w1, 0.045, o['z0'] - 0.025), (w0, 0.045, o['z0'] - 0.025)])
    # rowlock step under the entry door (photo 03: one course of bricks on edge from the slab to the threshold)
    fd = next(o for o in OPENINGS if o['name'] == 'front_door')
    Face('X', PORCH[3], -1).quad8(rowlock, [(fd['a0'] - 0.08, 0.0, Z_PORCH), (fd['a1'], 0.0, Z_PORCH), (fd['a1'], 0.13, Z_PORCH),
                                        (fd['a0'] - 0.08, 0.13, Z_PORCH), (fd['a0'] - 0.08, 0.0, -0.012), (fd['a1'], 0.0, -0.012),
                                        (fd['a1'], 0.13, -0.004), (fd['a0'] - 0.08, 0.13, -0.004)])
    rowlock.build("Brick_Rowlock", [M['brick_row']])
    stone.build("Keystones", [M['precast']])
    # the brick bay's gable triangle (brick face above the plate, under the bay roof)
    xm = (BAY[0] + BAY[1]) / 2
    top = ZT + (xm - BAY[0]) * P_BAY - 0.14
    zb = Z_PLATE - 0.01
    xs = [(BAY[0], zb), (BAY[1], zb), (BAY[1], ZT - 0.14), (xm, top), (BAY[0], ZT - 0.14)]
    tri = MB()
    n = len(xs)
    tri._add([(x, Y_BAY, z) for x, z in xs] + [(x, Y_BAY + BWT, z) for x, z in xs],
             [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))] + [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)], 0)
    tri.build("Bay_Gable_Brick", [M['brick']])
    brick_x.build("BrickDetails", [M['brick_sol']])
    del brick_y


# ================================================================ gable-end / gable-face siding triangles
def gable_siding(M):
    sid = MB()
    under = 0.16                           # siding stops under the rake soffit
    def tri_clip(x0, x1, p, zt=ZT):
        return lambda a: zt + (min(a - x0, x1 - a)) * p - under
    # left front gable face (y = YU)
    lap_siding(sid, Face('X', YU, -1), LGABLE[0], LGABLE[1], Z_GTRI, ZT + HALF_L * P_GABLE, exposure=EXPOSURE,
               top_clip=tri_clip(LGABLE[0], LGABLE[1], P_GABLE), start=Z_SIDING0)
    # right cross gable face (y = YU), x RGABLE[0] .. XB1 (its right half is behind the bay gable)
    lap_siding(sid, Face('X', YU, -1), RGABLE[0], XB1, Z_GTRI, ZT + HALF_X * P_CROSS, exposure=EXPOSURE,
               top_clip=tri_clip(RGABLE[0], XB1, P_CROSS), start=Z_SIDING0)
    # main gable ends (x = XB0 and x = XB1), y CEN[2] .. YB1 (in front of CEN[2] they are under the front gables)
    def main_clip(a):
        return ZT + (min(a - CEN[2], YB1 - a)) * P_MAIN - under
    for (b, out) in ((XB0, -1), (XB1, +1)):
        lap_siding(sid, Face('Y', b, out), YU, YB1, Z_GTRI, Z_RIDGE, exposure=EXPOSURE,
                   top_clip=lambda a: max(Z_GTRI + 0.02, main_clip(a)), start=Z_SIDING0)
    sid.build("GableSiding", [M['siding']])
    # attic backing behind the triangles (so no light leaks through course gaps)
    back = MB()
    for (al, b, a0, a1, ap, p, zt) in (('X', YU + 0.02, LGABLE[0], LGABLE[1], HALF_L, P_GABLE, ZT),
                                         ('X', YU + 0.02, RGABLE[0], XB1, HALF_X, P_CROSS, ZT)):
        xm = (a0 + a1) / 2
        back._add([(a0, b, Z_PLATE + 0.01), (a1, b, Z_PLATE + 0.01), (xm, b, zt + ap * p - 0.2)], [(0, 1, 2)], 0)
    for x in (XB0 + 0.02, XB1 - 0.02):
        back._add([(x, CEN[2], Z_PLATE + 0.01), (x, YB1, Z_PLATE + 0.01), (x, Y_RIDGE, Z_RIDGE - 0.2)], [(0, 1, 2)], 0)
    back.build("GableBacking", [M['siding_back']])


# ================================================================ windows, doors, shutters, porch
def _paint(o):
    return o.get('paint') or (UPPER_PAINT if o['z0'] > Z_UP - 0.1 else 'paint_blue')


# grille patterns read from the photos (upper sash cols x rows, lower sash rows or None = no grille)
GRILLES = {
    'lg_win': ((3, 2), 2), 'cen_win': ((3, 2), 2), 'rg_win': ((3, 2), 2),        # 6/6 (01, 02, 30 zooms)
    'bay_up_win': ((3, 2), 2), 'living_win': ((3, 2), 2),                        # 6/6 pairs (02, 03)
    'great_win': ((3, 2), 2), 'rear_up_l': ((3, 2), 2), 'rear_up_m': ((3, 2), 2), 'rear_up_r': ((3, 2), 2),   # 25, 27
    'kitchen_win': ((3, 2), 2), 'landing_win': ((2, 2), 2),
}


def openings(M):
    wall_of = {}
    for w in WALLS:
        for o in _openings_in(w):
            wall_of[o['name']] = w
    shut = MB()
    trim = MB()
    for o in OPENINGS:
        if o['kind'] not in ('window', 'slider', 'garage_door', 'entry'):      # interior door holes etc. (other modules)
            continue
        w = wall_of[o['name']]
        f = _face(w)
        depth = _depth(w)
        a0, a1, z0, z1 = o['a0'], o['a1'], o['z0'], o['z1']
        if o['kind'] == 'window':
            mb = MB()
            gr, lower_rows = GRILLES.get(o['name'], (o.get('grid', (3, 2)), None if not o.get('lower_grid', True) else o.get('grid', (3, 2))[1]))
            fixed = o['name'] == 'garage_win'
            fen.single_hung(f, mb, a0, a1, z0, z1, depth, grid=o.get('grid', gr) if fixed else gr, lower_grid=lower_rows is not None,
                            lower_grid_rows=lower_rows, units=o.get('units', 1), recess=0.035 if w['kind'] == 'siding' else 0.10,
                            frame=0.038, sash=0.034, fixed=fixed, grille_w=0.014)
            mb.build(f"Win_{o['name']}", [M['vinyl'], M['win_glass'], M['vinyl'], M[_paint(o)], M['trim_int']])
            if w['kind'] == 'siding':
                j_channel(trim, f, a0, a1, z0, z1, w=J_W)
                if o.get('header'):                                   # crosshead with a keystone (front gable windows)
                    zh = z1 + J_W
                    f.box(trim, a0 - 0.06, a1 + 0.06, 0.0, 0.04, zh, zh + 0.20)
                    f.box(trim, a0 - 0.085, a1 + 0.085, 0.0, 0.065, zh + 0.20, zh + 0.235)
                    f.box(trim, a0 - 0.07, a1 + 0.07, 0.0, 0.05, zh + 0.235, zh + 0.25)
                    am = (a0 + a1) / 2
                    # keystone: tapered, standing proud of the crosshead and above its cap (01 / 02 / 30)
                    f.quad8(trim, [(am - 0.055, 0.0, zh - 0.03), (am + 0.055, 0.0, zh - 0.03), (am + 0.055, 0.075, zh - 0.03), (am - 0.055, 0.075, zh - 0.03),
                                   (am - 0.085, 0.0, zh + 0.31), (am + 0.085, 0.0, zh + 0.31), (am + 0.085, 0.09, zh + 0.31), (am - 0.085, 0.09, zh + 0.31)])
            else:
                # brick opening: a narrow white brick-mould frame proud of the veneer (no sill piece: rowlock below)
                bm = 0.035
                for (b0_, b1_, c0_, c1_) in ((a0 - bm, a0, z0, z1 + bm), (a1, a1 + bm, z0, z1 + bm), (a0 - bm, a1 + bm, z1, z1 + bm)):
                    f.box(trim, b0_, b1_, -0.10, 0.014, c0_, c1_)
            if o.get('shutters'):
                # louvre-less raised-panel shutters abutting the frame (02: no gap); 0.38 wide on siding, 0.40 on brick
                sw = 0.37 if w['kind'] == 'siding' else 0.40
                gap = J_W + 0.004 if w['kind'] == 'siding' else 0.045
                zz0, zz1 = z0 - (0.0 if w['kind'] == 'siding' else 0.01), z1 + (J_W if w['kind'] == 'siding' else 0.03)
                fen.shutter(f, shut, a0 - gap - sw, a0 - gap, zz0, zz1, d=0.02)
                fen.shutter(f, shut, a1 + gap, a1 + gap + sw, zz0, zz1, d=0.02)
        elif o['kind'] == 'slider':
            mb = MB()
            # photo 11 / 25 / 28: two panels, a narrow white vinyl frame, thin flat grilles 3 wide x 5 high in both panels;
            # the operable panel is on the -X side (the left one seen from the dining room, the right one in 25)
            fen.slider(f, mb, a0, a1, z0, z1, depth, grid=(3, 5), frame=0.045, stile=0.055, grille_w=0.012, rail_bottom=0.075,
                       fixed_side=+1)
            mb.build(f"Win_{o['name']}", [M['vinyl'], M['win_glass'], M['vinyl'], M['nickel'], M['paint_blue'], M['trim_int']])
            j_channel(trim, f, a0, a1, z0, z1, w=J_W, sill=False)
        elif o['kind'] == 'garage_door':
            mb = MB()
            fen.garage_door(f, mb, a0, a1, z0, z1, d=-0.10, mi=0, mi_hw=1, style='bevel', margin=0.06, panel_gap=0.075,
                            rail=0.075, joint=0.006, lock=False)
            mb.build("Garage_Door", [M['garage_navy'], M['nickel']])
            gt = 0.07
            for (b0_, b1_, c0_, c1_) in ((a0 - gt, a0, z0, z1 + gt), (a1, a1 + gt, z0, z1 + gt), (a0 - gt, a1 + gt, z1, z1 + gt)):
                f.box(trim, b0_, b1_, -0.10, 0.016, c0_, c1_)
            # white jamb / head liner on the opening's inner reveal (behind the door; photo 24 with the door up)
            for (b0_, b1_, c0_, c1_) in ((a0, a0 + 0.02, z0, z1), (a1 - 0.02, a1, z0, z1), (a0, a1, z1 - 0.02, z1)):
                f.box(trim, b0_, b1_, -depth, -0.12, c0_, c1_)
        elif o['kind'] == 'entry':
            entry_door(M, f, o, depth, trim)
    shut.build("Shutters", [M['shutter']])
    trim.build("OpeningTrim", [M['trim']])


def entry_door(M, f, o, depth, trim):
    """Navy six-panel steel entry door (white inside) with a 10" sidelight on its right (textured glass divided into
    five lites by flat white bars, photos 02 / 03), a narrow brick mould and a satin-nickel handleset + keypad."""
    a0, a1, z0, z1 = o['a0'], o['a1'], o['z0'], o['z1']
    dl0, dl1 = a0 + 0.06, a0 + 0.06 + 0.91
    frame = MB()
    fw = 0.05
    # jambs, head, the mullion between door and sidelight, threshold
    for (b0_, b1_) in ((a0, a0 + fw), (dl1, dl1 + fw), (a1 - fw, a1)):
        f.box(frame, b0_, b1_, -depth, -0.02, z0, z1, 0)
    f.box(frame, a0, a1, -depth, -0.02, z1 - fw, z1, 0)
    f.box(frame, a0, a1, -depth + 0.02, -0.03, z0 - 0.02, z0 + 0.015, 1)
    # sidelight: rails, textured glass, flat bars (photo 03: horizontal subdivisions)
    s0, s1 = dl1 + fw, a1 - fw
    f.box(frame, s0, s1, -0.09, -0.06, z0, z0 + 0.22, 0)
    f.box(frame, s0, s1, -0.09, -0.06, z1 - fw - 0.08, z1 - fw, 0)
    g0, g1 = z0 + 0.22, z1 - fw - 0.08
    f.box(frame, s0 + 0.025, s1 - 0.025, -0.078, -0.072, g0, g1, 2)
    for i in range(1, 5):
        zb = g0 + (g1 - g0) * i / 5
        f.box(frame, s0 + 0.025, s1 - 0.025, -0.071, -0.064, zb - 0.006, zb + 0.006, 0)
    f.box(frame, s0, s0 + 0.025, -0.09, -0.06, g0, g1, 0)
    f.box(frame, s1 - 0.025, s1, -0.09, -0.06, g0, g1, 0)
    frame.build("Entry_Frame", [M['vinyl'], M['nickel'], M['win_glass']])
    # brick mould outside + interior casing
    bm = 0.05
    for (b0_, b1_, c0_, c1_) in ((a0 - bm, a0, z0, z1 + bm), (a1, a1 + bm, z0, z1 + bm), (a0 - bm, a1 + bm, z1, z1 + bm)):
        f.box(trim, b0_, b1_, -0.03, 0.02, c0_, c1_)
    for (b0_, b1_, c0_, c1_) in ((a0 - 0.07, a0, z0, z1 + 0.07), (a1, a1 + 0.07, z0, z1 + 0.07), (a0 - 0.07, a1 + 0.07, z1, z1 + 0.07)):
        f.box(trim, b0_, b1_, -depth - 0.016, -depth, c0_, c1_)
    # the leaf: its own object (the film swings it on the hinge at x = dl0)
    leaf = MB()
    d0, d1 = -0.11, -0.065
    fen.panel_leaf(f, leaf, dl0 + 0.003, dl1 - 0.003, z0 + 0.01, z1 - fw - 0.003, d0, d1, layout='six_colonial', mi_out=0, mi_in=1,
                   raise_=0.012, bevel=0.03)
    hx = dl1 - 0.075
    f.box(leaf, hx - 0.022, hx + 0.022, d1, d1 + 0.012, z0 + 0.82, z0 + 1.07, 2)            # handleset escutcheon
    f.box(leaf, hx - 0.008, hx + 0.008, d1 + 0.012, d1 + 0.07, z0 + 0.88, z0 + 1.02, 2)     # grip
    f.box(leaf, hx - 0.03, hx + 0.03, d1, d1 + 0.02, z0 + 1.10, z0 + 1.24, 3)               # keypad deadbolt
    fen.lever(f, leaf, hx, z0 + 0.92, d0, side=-1, mi=2, knob=True)                        # interior knob (photo 04)
    f.box(leaf, hx - 0.025, hx + 0.025, d0 - 0.012, d0, z0 + 1.00, z0 + 1.05, 2)            # thumb-turn rose
    ob = leaf.build("Entry_Door", [M['navy'], M['trim_int'], M['nickel'], M['iron_black']])
    ob["hinge"] = (dl0, f.b + f.out * ((d0 + d1) / 2))


def porch(M):
    """Porch (photo 03): slab one step above the walk, running ~0.4 m in front of the columns and past the bay's left
    corner; two square white columns on low plinths with a capital block; a flat ceiling at 2.17 behind the beam."""
    x0, x1 = PORCH[0], PORCH[1]
    xr = PORCH_ROOF_X1 - 0.06
    yf = -0.40
    s = MB()
    s.box(x0, x1, yf, PORCH[3], Z_PORCH - 0.25, Z_PORCH)                      # porch slab
    s.box(x1 - 0.01, xr, yf, Y_BAY, Z_PORCH - 0.25, Z_PORCH)                  # its part in front of the bay's corner
    s.build("Porch_Slab", [M['porch_slab']])
    c = MB()
    yc = PORCH_COL_Y
    for cx in PORCH_COLS:
        c.box(cx - 0.10, cx + 0.10, yc - 0.10, yc + 0.10, Z_PORCH, Z_PORCH + 0.17)                 # plinth
        c.box(cx - 0.108, cx + 0.108, yc - 0.108, yc + 0.108, Z_PORCH + 0.17, Z_PORCH + 0.19)
        c.box(cx - 0.0825, cx + 0.0825, yc - 0.0825, yc + 0.0825, Z_PORCH + 0.19, Z_PORCH_CEIL - 0.15)   # shaft
        c.box(cx - 0.092, cx + 0.092, yc - 0.092, yc + 0.092, Z_PORCH_CEIL - 0.165, Z_PORCH_CEIL - 0.15)
        c.box(cx - 0.10, cx + 0.10, yc - 0.10, yc + 0.10, Z_PORCH_CEIL - 0.15, Z_PORCH_CEIL)       # capital block
    c.box(x0 - 0.02, xr, -0.03, 0.20, Z_PORCH_CEIL, Z_EAVE1 + 0.005)                               # wrapped beam
    c.box(x0, x1, 0.20, PORCH[3], Z_PORCH_CEIL, Z_PORCH_CEIL + 0.02)                               # porch ceiling
    c.box(x1 - 0.01, xr, 0.20, Y_BAY, Z_PORCH_CEIL, Z_PORCH_CEIL + 0.02)
    c.build("Porch_Columns", [M['trim']])
    # frieze board above the garage brick, under the shed soffit
    fz = MB()
    fz.box(GAR[0] - 0.012, x0 - 0.02, -0.03, 0.0, Z_BRICK_TOP, Z_EAVE1 + 0.005)
    fz.build("Frieze_Front", [M['trim']])


# ================================================================ roofs
def _trim_mb():
    return MB(), MB(), MB()     # fascia/rake/soffit (white), gutters+downspouts (white metal), ridge caps (shingle)


def roofs(M):
    sh = [M['shingle']]
    trim, gut, cap = _trim_mb()
    col = 'Roof'
    zf = ZF_MAIN
    # ---------------- main side gable
    #   front slope: full width back from the recess eave; at the gable ends the rake overhangs reach forward to the front
    #   gables (not over the rooms under them)
    front = [(XB0 - KR, YU), (XB0, YU), (XB0, CEN[2]), (CEN[0], CEN[2]), (CEN[0], CEN[2] - KE), (CEN[1], CEN[2] - KE),
             (CEN[1], CEN[2]), (XB1, CEN[2]), (XB1, YU), (XB1 + KR, YU), (XB1 + KR, Y_RIDGE), (XB0 - KR, Y_RIDGE)]
    rf.slope("Roof_Main_Front", sh, (XB0 - KR, CEN[2] - KE, zf), (1, 0), (0, 1), P_MAIN, front, RTH, col)
    rf.slope("Roof_Main_Rear", sh, (XB0 - KR, YB1 + KE, zf), (1, 0), (0, -1), P_MAIN,
             [(XB0 - KR, YB1 + KE), (XB1 + KR, YB1 + KE), (XB1 + KR, Y_RIDGE), (XB0 - KR, Y_RIDGE)], RTH, col)
    rf.ridge_cap(cap, (XB0 - KR, Y_RIDGE), (XB1 + KR, Y_RIDGE), Z_RIDGE, mi=0)
    # rear eave
    rf.fascia_run(trim, (XB0 - KR, YB1 + KE), (XB1 + KR, YB1 + KE), zf, (0, 1))
    rf.soffit_run(trim, (XB0 - KR, YB1), (XB1 + KR, YB1), (0, 1), KE, zf - 0.19)
    rf.gutter(gut, (XB0 - KR, YB1 + KE + 0.028), (XB1 + KR, YB1 + KE + 0.028), zf + 0.01, (0, 1))
    # centre front eave (over the recess)
    rf.fascia_run(trim, (CEN[0], CEN[2] - KE), (CEN[1], CEN[2] - KE), zf, (0, -1))
    rf.soffit_run(trim, (CEN[0], CEN[2]), (CEN[1], CEN[2]), (0, -1), KE, zf - 0.19)
    rf.gutter(gut, (CEN[0], CEN[2] - KE - 0.028), (CEN[1], CEN[2] - KE - 0.028), zf + 0.01, (0, -1))
    # rakes at both gable ends (the front part is exposed beside the front gables, photo 30)
    zfront = ZT - (CEN[2] - YU) * P_MAIN
    for x, out in ((XB0 - KR, -1), (XB1 + KR, 1)):
        rf.rake_board(trim, (x, YB1 + KE), (x, Y_RIDGE), zf, Z_RIDGE, (out, 0))
        rf.rake_board(trim, (x, YU), (x, Y_RIDGE), zfront, Z_RIDGE, (out, 0))
        xs = XB0 if x < 0 else XB1
        _rake_soffit(trim, xs, out, YB1 + KE, Y_RIDGE, zf, Z_RIDGE, KR)
        _rake_soffit(trim, xs, out, CEN[2], Y_RIDGE, ZT, Z_RIDGE, KR)
    # ---------------- left front gable (walls x 0 .. 3.3 at y 1.5; its ridge dies into the main front slope)
    zr_l = ZT + HALF_L * P_GABLE
    y_back_l = CEN[2] + (zr_l - ZT) / P_MAIN + 0.05
    _front_gable("LGable", sh, trim, gut, cap, LGABLE[0], LGABLE[1], YU, P_GABLE, y_back=y_back_l, col=col, clip_r=CEN[2])
    # ---------------- right cross gable (walls x RGABLE[0] .. XB1; ridge = main ridge, runs back to it)
    _front_gable("RGable", sh, trim, gut, cap, RGABLE[0], XB1, YU, P_CROSS, y_back=Y_RIDGE, col=col, clip_l=CEN[2])
    # ---------------- brick bay gable (walls BAY[0] .. BAY[1] at y = Y_BAY; tucks under the cross gable's overhang)
    _front_gable("BayGable", sh, trim, gut, cap, BAY[0], BAY[1], Y_BAY, P_BAY, y_back=YU - 0.1, col=col)
    # ---------------- first-floor shed across the garage + porch, with the left wrap and a hip at the front-left
    shed(sh, trim, gut, col)
    vents(M, col)
    trim.build("Roof_Trim", [M['trim']], coll=col)
    gut.build("Gutters", [M['gutter']], coll=col)
    cap.build("Ridge_Caps", sh, coll=col)


def _rake_soffit(trim, xs, out, ya, yb, za, zb, k):
    """Sloped soffit strip under a rake overhang: from the wall plane x = xs outward by k, following the rake."""
    x1 = xs + out * k
    zo = 0.20
    trim.hexa([(xs, ya, za - zo), (x1, ya, za - zo), (x1, yb, zb - zo), (xs, yb, zb - zo),
               (xs, ya, za - zo + 0.015), (x1, ya, za - zo + 0.015), (x1, yb, zb - zo + 0.015), (xs, yb, zb - zo + 0.015)], 0)


def _front_gable(name, sh, trim, gut, cap, x0, x1, yface, p, y_back, col, clip_l=None, clip_r=None):
    """A front-facing gable over walls x0..x1 with its face at y = yface: two slopes from the side eaves (overhang KE)
    up to the ridge at the centre, from the front rake (yface - KR) back to y_back; rake boards + soffits at the
    front, gutters on both side eaves (the parts that end up under another roof are hidden)."""
    xm = (x0 + x1) / 2
    zf = ZT - KE * p
    zr = ZT + (xm - x0) * p
    yf = yface - KR
    # an overhang that would run back over a recessed wall (into the rooms behind it) stops at that wall line
    left = [(x0 - KE, yf), (xm, yf), (xm, y_back), (x0 - KE, y_back)] if clip_l is None else \
        [(x0 - KE, yf), (xm, yf), (xm, y_back), (x0, y_back), (x0, clip_l), (x0 - KE, clip_l)]
    right = [(x1 + KE, yf), (xm, yf), (xm, y_back), (x1 + KE, y_back)] if clip_r is None else \
        [(x1 + KE, yf), (xm, yf), (xm, y_back), (x1, y_back), (x1, clip_r), (x1 + KE, clip_r)]
    rf.slope(f"Roof_{name}_L", sh, (x0 - KE, yf, zf), (0, 1), (1, 0), p, left, RTH, col)
    rf.slope(f"Roof_{name}_R", sh, (x1 + KE, yf, zf), (0, 1), (-1, 0), p, right, RTH, col)
    rf.ridge_cap(cap, (xm, yf), (xm, y_back), zr, mi=0)
    # front rakes (boards follow the slope from the eave corners to the apex)
    rf.rake_board(trim, (x0 - KE, yf), (xm, yf), zf, zr, (0, -1))
    rf.rake_board(trim, (x1 + KE, yf), (xm, yf), zf, zr, (0, -1))
    # rake soffit under the front overhang (sloped strips from the face plane out to the rake)
    for (xa, za) in ((x0 - KE, zf), (x1 + KE, zf)):
        trim.hexa([(xa, yface, za - 0.20), (xm, yface, zr - 0.20), (xm, yf, zr - 0.20), (xa, yf, za - 0.20),
                   (xa, yface, za - 0.185), (xm, yface, zr - 0.185), (xm, yf, zr - 0.185), (xa, yf, za - 0.185)], 0)
    # side eaves: fascia, soffit, gutter from the front corner back (visible length only)
    for xe, out in ((x0 - KE, -1), (x1 + KE, 1)):
        clip = clip_l if out < 0 else clip_r
        run = min(y_back, yface + 0.9) if clip is None else clip - KE         # meets the recess eave
        xw = x0 if out < 0 else x1
        rf.fascia_run(trim, (xe, yf), (xe, run), zf, (out, 0))
        rf.soffit_run(trim, (xw, yf), (xw, run), (out, 0), KE, zf - 0.19)
        rf.gutter(gut, (xe + out * 0.028, yf), (xe + out * 0.028, run), zf + 0.01, (out, 0))


def shed(sh, trim, gut, col):
    """First-floor roof: a 4/12 shed across the garage + porch front (eave at y = -KE) that wraps the garage's
    left protrusion (eave at x = GAR[0] - KE), the two meeting in a hip at the front-left corner; its right end runs
    past the brick bay's left corner to x = PORCH_ROOF_X1 (photos 02, 03)."""
    k = KE
    ye, xe = -k, GAR[0] - k
    xr = PORCH_ROOF_X1
    run_front = YU - ye                    # 1.85 m to the upper walls
    xh = xe + run_front                     # the hip reaches the wall line at x = xh (equal runs)
    front = [(xe, ye), (xr, ye), (xr, Y_BAY), (PORCH[1], Y_BAY), (PORCH[1], YU), (CEN[1], YU), (CEN[1], CEN[2]),
             (CEN[0], CEN[2]), (CEN[0], YU), (xh, YU)]
    th = 0.06                               # thin slab: the garage ceiling (2.55) is just under it
    rf.slope("Roof_Shed_Front", sh, (xe, ye, Z_SHED), (1, 0), (0, 1), P_SHED, front, th, col)
    yb = GAR[3] + k
    left = [(xe, ye), (xh, YU), (xh, yb), (xe, yb)]
    rf.slope("Roof_Shed_Left", sh, (xe, ye, Z_SHED), (0, 1), (1, 0), P_SHED, left, th, col)
    zh = Z_SHED + run_front * P_SHED
    cap = MB()
    rf.ridge_cap(cap, (xe, ye), (xh, YU), Z_SHED, mi=0)
    # fascia, soffits, gutters
    rf.fascia_run(trim, (xe, ye), (xr, ye), Z_SHED, (0, -1), depth=0.17)
    rf.fascia_run(trim, (xe, ye), (xe, yb), Z_SHED, (-1, 0), depth=0.17)
    rf.soffit_run(trim, (GAR[0], 0.0), (xr, 0.0), (0, -1), k, Z_EAVE1)
    rf.soffit_run(trim, (GAR[0], 0.0), (GAR[0], yb), (-1, 0), k, Z_EAVE1)
    rf.gutter(gut, (xe, ye - 0.028), (xr - 0.02, ye - 0.028), Z_SHED + 0.01, (0, -1))
    rf.gutter(gut, (xe - 0.028, ye), (xe - 0.028, yb), Z_SHED + 0.01, (-1, 0))
    # right end, exposed in front of the recessed brick bay; its soffit return
    rf.rake_board(trim, (xr, ye), (xr, Y_BAY), Z_SHED, Z_SHED + (Y_BAY - ye) * P_SHED, (1, 0), depth=0.17)
    trim.box(PORCH[1], xr, ye, Y_BAY, Z_EAVE1, Z_EAVE1 + 0.015)
    # rear end of the left wrap: a rake from its eave up to the block wall
    rf.rake_board(trim, (xe, yb), (xh, yb), Z_SHED, zh, (0, 1))
    del cap


def vents(M, col):
    """Roof penetrations, located by intersecting the photo rays with the roof planes (EXT notes): a galvanised can vent
    (static roof louver, ~0.4 m cap) on the main front slope above the cross-gable valley (01: u 797, 02: u 817, 30:
    u 764 -> x 6.6..7.0, y 4.9..5.3), two black exhaust hoods on the rear slope (25: x 8.60 / 8.03, y 8.5)."""
    mb = MB()
    def at(x, y):
        return ZT + (y - CEN[2]) * P_MAIN if y < Y_RIDGE else ZT + (YB1 - y) * P_MAIN
    x, y = 6.66, 5.12
    z = at(x, y)
    mb.hexa([(x - 0.24, y - 0.24, z - 0.02 - 0.24 * P_MAIN), (x + 0.24, y - 0.24, z - 0.02 - 0.24 * P_MAIN),
             (x + 0.24, y + 0.24, z - 0.02 + 0.24 * P_MAIN), (x - 0.24, y + 0.24, z - 0.02 + 0.24 * P_MAIN),
             (x - 0.24, y - 0.24, z + 0.01 - 0.24 * P_MAIN), (x + 0.24, y - 0.24, z + 0.01 - 0.24 * P_MAIN),
             (x + 0.24, y + 0.24, z + 0.01 + 0.24 * P_MAIN), (x - 0.24, y + 0.24, z + 0.01 + 0.24 * P_MAIN)], 0)   # flashing
    mb.cylinder(x, y, z - 0.10, z + 0.12, 0.15, 0.11, seg=16, mi=0)                        # boot / collar
    mb.cylinder(x, y, z + 0.12, z + 0.26, 0.11, 0.11, seg=16, mi=0)                        # throat
    mb.cylinder(x, y, z + 0.26, z + 0.30, 0.13, 0.19, seg=16, mi=0)                        # cap skirt
    mb.cylinder(x, y, z + 0.30, z + 0.46, 0.19, 0.19, seg=16, mi=0)                        # louvred cap
    mb.cylinder(x, y, z + 0.46, z + 0.50, 0.19, 0.12, seg=16, mi=0)                        # top
    for (x, y) in ((8.65, 8.35), (8.07, 8.35)):
        z = at(x, y)
        mb.box(x - 0.13, x + 0.13, y - 0.14, y + 0.16, z - 0.05, z + 0.02, 1)
        mb.box(x - 0.06, x + 0.06, y - 0.06, y + 0.06, z - 0.02, z + 0.22, 1)
        mb.box(x - 0.10, x + 0.10, y - 0.02, y + 0.14, z + 0.10, z + 0.26, 1)             # hood opening down-slope
    mb.build("Roof_Vents", [M['galvanised'], M['iron_black']], coll=col)


# ================================================================ downspouts, lights, small fixtures
def fixtures(M):
    gut = MB()
    zf = ZF_MAIN
    zfs = Z_SHED - 0.13
    def shed_z(y):
        return Z_SHED + (y + KE) * P_SHED
    spouts = [
        # (x, y, z_bottom, z_top, out)
        (GAR[0], 0.02, Z_GRADE, zfs, (0, -1)),                    # garage front-left (photo 02)
        (PORCH_COLS[1] + 0.09, PORCH_COL_Y + 0.03, Z_PORCH, zfs, (1, 0)),   # right end of the shed gutter, down the right column (03)
        (XB0 + 0.05, YU, shed_z(YU) - 0.05, ZT - KE * P_GABLE - 0.02, (0, -1)),   # left gable, left corner -> shed roof
        (CEN[0] + 0.09, CEN[2], shed_z(CEN[2]) - 0.05, zf - 0.02, (0, -1)),        # recess left end (02, 30)
        (RGABLE[0] + 0.05, YU, shed_z(YU) - 0.05, ZT - KE * P_CROSS - 0.02, (0, -1)),  # right gable, left corner
        (BAY[0] + 0.08, Y_BAY, shed_z(Y_BAY) - 0.05, ZT - KE * P_BAY - 0.02, (0, -1)),   # bay gable, left eave (30)
        (XB0 + 0.06, YB1, Z_GRADE, zf - 0.02, (0, 1)),            # rear corners (photo 25)
        (XB1 - 0.06, YB1, Z_GRADE, zf - 0.02, (0, 1)),
        (GAR[0] + 0.05, GAR[3], Z_GRADE, zfs, (0, 1)),            # garage left wrap, rear
    ]
    for (x, y, z0, z1, out) in spouts:
        rf.downspout(gut, x, y, z0, z1, out=out)
    gut.build("Downspouts", [M['gutter']], coll='Roof')
    # coach lanterns: left of the garage door (02), on the pier right of it and on the door wall left of the door (03)
    lan = MB()
    for (x, y, z) in LANTERNS:
        _lantern(lan, x, y, z)
    lan.build("Lanterns", [M['iron_black'], M['lantern_glass']])
    # house-number plaque on the garage pier (photo 03: "13695" on a cream plaque with a raised border)
    pl = MB()
    pl.box(5.61, 6.01, -0.03, 0.0, 1.19, 1.33, 0)
    pl.box(5.625, 5.995, -0.036, -0.03, 1.202, 1.318, 1)
    pl.box(5.635, 5.985, -0.038, -0.036, 1.21, 1.31, 0)
    pl.build("House_Number", [M['trim'], M['house_number']])
    _number_text(M, "13695", (5.81, -0.039, 1.26), 0.075)
    # small front fixtures: video doorbell right of the sidelight, a dome camera under the porch beam's left end, the
    # solar light on the left column's capital, a solar spot on the garage's top-left corner (photos 02, 03)
    fx = MB()
    fx.box(8.63, 8.67, 1.47, 1.50, 1.15, 1.28, 0)                                     # doorbell on the sidelight mould (03)
    fx.cylinder(5.96, -0.10, Z_EAVE1 - 0.12, Z_EAVE1 - 0.005, 0.045, 0.05, seg=12, mi=0)            # camera (03)
    fx.box(PORCH_COLS[0] - 0.06, PORCH_COLS[0] + 0.06, PORCH_COL_Y - 0.106, PORCH_COL_Y - 0.10, Z_PORCH_CEIL - 0.13, Z_PORCH_CEIL - 0.03, 0)
    fx.box(GAR[0] + 0.05, GAR[0] + 0.19, -0.06, 0.0, 2.02, 2.14, 0)
    fx.build("Front_Fixtures", [M['iron_black']])
    rear_fixtures(M)
    for i, (x, y, z) in enumerate(LANTERNS):
        add_light(f"L_Lantern_{i}", 'POINT', (x, y - 0.14, z - 0.02), 2.5, color=(1.0, 0.78, 0.5), size=0.03)


def _number_text(M, text, centre, height):
    """Raised black serif numerals on the plaque (photo 03): a Blender text object facing -Y, 3 mm deep."""
    import bpy
    cu = bpy.data.curves.new("HouseNumberText", 'FONT')
    cu.body = text
    cu.align_x, cu.align_y = 'CENTER', 'CENTER'
    cu.size = height * 1.38                  # cap height ~ 0.72 of the font size
    cu.extrude = 0.0015
    ob = bpy.data.objects.new("House_Number_Text", cu)
    ob.data.materials.append(M['iron_black'])
    ob.location = centre
    ob.rotation_euler = (math.pi / 2, 0.0, 0.0)
    collection('House').objects.link(ob)
    return ob


LANTERNS = ((0.28, 0.0, 1.79), (5.80, 0.0, 1.73), (7.03, 1.5, 1.77))     # back-projected from 02 / 03 (glass centre)


def rear_fixtures(M):
    """Rear wall (photos 25, 27, 28): positions back-projected through the solved 25 and 28 cameras onto the wall
    (the two photos agree to ~5 cm): a white twin-head motion flood light high above the slider, a black camera and a
    black motion light over the slider's right half, a white-based light at the slider head's -X side, solar wall
    lights either side of the slider, outlets low at x 6.2 and a hose bib + outlet at x 10.65."""
    blk, wht, grey = MB(), MB(), MB()
    y = YB1
    def box(mb, x, z, w, h, d):
        mb.box(x - w / 2, x + w / 2, y + 0.005, y + d, z - h / 2, z + h / 2, 0)
    # flood light (25: (6.68, 4.91), 28: (6.68, 4.87)): white base, two heads angled down
    box(wht, 6.68, 4.90, 0.12, 0.12, 0.05)
    for dx in (-0.075, 0.075):
        wht.cylinder(6.68 + dx, y + 0.12, 4.80, 4.87, 0.055, 0.05, seg=10, mi=0)
    # camera (25: 6.64 / 2.89, 28: 6.71 / 2.80) and the black motion light (28: 5.91 / 2.66; 25: 6.64 / 2.57)
    box(blk, 6.68, 2.86, 0.08, 0.09, 0.05)
    blk.cylinder(6.68, y + 0.09, 2.73, 2.82, 0.035, 0.03, seg=10, mi=0)
    box(blk, 5.91, 2.66, 0.10, 0.12, 0.08)
    # solar wall lights either side of the slider (25: 9.32 / 4.93, 28: 9.35 / 5.01 at z 2.10)
    for x in (9.33, 4.97):
        box(blk, x, 2.10, 0.20, 0.09, 0.05)
        blk.box(x - 0.08, x + 0.08, y + 0.05, y + 0.06, 2.08, 2.14, 0)
    # the white-based black light beside the slider head (25: 6.38 / 2.00, 28: 6.42 / 2.01)
    box(wht, 6.40, 2.01, 0.11, 0.13, 0.03)
    blk.cylinder(6.40, y + 0.08, 1.95, 2.04, 0.045, 0.04, seg=10, mi=0)
    # outlets (25: 6.17 / 0.49, 28: 6.22 / 0.53) and the hose bib with an outlet above (25: 10.62, 28: 10.66)
    box(wht, 6.20, 0.50, 0.09, 0.12, 0.035)
    box(wht, 10.64, 0.62, 0.09, 0.12, 0.035)
    grey.box(10.62, 10.66, y, y + 0.08, 0.40, 0.44, 0)
    grey.cylinder(10.64, y + 0.08, 0.37, 0.45, 0.028, 0.028, seg=8, mi=0)
    blk.build("Rear_Fixtures_Black", [M['iron_black']])
    wht.build("Rear_Fixtures_White", [M['vinyl']])
    grey.build("Rear_Fixtures_Metal", [M['nickel']])


def _lantern(mb, x, y, z):
    """Wall lantern projecting toward -y from a wall at y: backplate, arm, a tapered glass box and a cap."""
    mb.box(x - 0.045, x + 0.045, y - 0.02, y, z - 0.14, z + 0.14, 0)
    mb.box(x - 0.012, x + 0.012, y - 0.12, y - 0.02, z + 0.02, z + 0.05, 0)
    c = (x, y - 0.14)
    mb.cylinder(c[0], c[1], z - 0.17, z - 0.14, 0.07, 0.05, seg=4, mi=0, rot=math.pi / 4)
    mb.cylinder(c[0], c[1], z - 0.14, z + 0.08, 0.075, 0.09, seg=4, mi=1, rot=math.pi / 4)
    mb.cylinder(c[0], c[1], z + 0.08, z + 0.15, 0.10, 0.02, seg=4, mi=0, rot=math.pi / 4)


def build(M):
    walls(M)
    gable_siding(M)
    openings(M)
    porch(M)
    roofs(M)
    fixtures(M)
    collection('Roof')


# ================================================================ per-photo sun (run.py -> house.before_render -> here)
# unit vector TOWARD the sun, read from the photos' cast shadows (EXT notes): 01 - the lantern's shadow falls left and
# down (sx/sz ~ 0.68) and the shed eave's shadow on the garage brick ends at z 1.97 (v 552, cast by the gutter's lower edge
# at y -0.48, z 2.36 -> profile rise 0.8 per metre); with it the front tree shades the garage door's right half as in 01 and
# 30; 30 - the vent's shadow on the roof, the house's shadow over the left lawn; 31 / 32 were flown with 30.
SUN_PHOTO = (0.394, -0.713, 0.579)
SUN = {k: SUN_PHOTO for k in ('hero', 'front', 'p03', 'p30')}
# the rear photos: the rear eave's shadow is a straight line parallel to the wall on the ground (back-projected through
# the solved cameras): y 17.0 in 26 AND 27 (on the pavers / lawn), y 15.9 in 28 (the lit strip at the patio's outer edge;
# 25's lawn is lit from y 16 on).  Cast by the gutter's outer top edge (y 12.26, z 5.37) -> -sy/sz = 0.84 (26 / 27) and
# 0.645 (25 / 28).  Azimuth: in 27 the edge runs straight to the frame edge at x -2.7 (the eave's shadow end is further
# -X: sx/sz >= 0.40) and the solar lights' shadows on the lawn give sx/sy ~ -0.62 .. -0.75 -> sx/sz 0.54
for _k in ('p26', 'p27'):
    SUN[_k] = (0.383, -0.592, 0.709)
for _k in ('rear', 'p28'):
    SUN[_k] = (0.333, -0.511, 0.792)
# photo 02 was taken on another (partly cloudy) day: the whole facade is in shade (no cast shadows, the garage door reads
# 2.3x darker than in 01) while the lawn in front is sunlit -> the sun is high behind the house
SUN['front'] = (-0.15, 0.50, 0.85)
# (sun energy, sky strength[, sun angle deg]) multipliers per photo; 02 is lit mostly by a bright cloudy sky (the roof
# reads bright, the facade under the eaves dull): a weak, soft sun and an overcast-distributed sky light (OVERCAST)
LIGHT = {'front': (0.35, 1.0, 6.0), 'rear': (1.45, 1.0), 'p27': (1.75, 1.0), 'p28': (1.45, 1.0), 'p26': (1.2, 1.0)}
OVERCAST = {'front': (5.0, 0.85, (0.93, 0.97, 1.0))}      # (zenith luminance, share of the sky light, tint)
if os.environ.get('STAN_EXT_OVC'):                         # test override "k,mix,sun_mult,sky_mult" for 02
    _o = [float(v) for v in os.environ['STAN_EXT_OVC'].split(',')]
    OVERCAST['front'] = (_o[0], _o[1], OVERCAST['front'][2]); LIGHT['front'] = (_o[2], _o[3], 6.0)
EXT_PHOTOS = ('hero', 'front', 'p03', 'p30', 'rear', 'p27', 'p28', 'p26', 'p29', 'aerial', 'p32')     # glass tint, interior dimming, neutral shade tint
# photo 24 (garage, door open): the sun patch on the slab (INT_FRONT's back-projection: eave shadow edge at y 1.25, spill past
# the left jamb) -> a high sun from the front
SUN['p24'] = (0.10, -0.54, 0.84)
# site photos: 31 / 32 were flown with 30 (same shadows: tree / house shadows toward -X / +Y in 31), 26 / 29 fit the same
# high south-east sun (26: the house's shadow reaches the patio edge; 29: the allee's south row shades the path)
for _k in ('p29', 'aerial', 'p32'):
    SUN[_k] = SUN_PHOTO
LIGHT['p24'] = (1.3, 1.0)
_SUN_DEFAULT = {}


def _aim_sun(scene, d):
    import os
    from mathutils import Vector
    import bpy
    sun = bpy.data.objects.get("Sun")
    if sun is None:
        return
    sky = next((n for n in scene.world.node_tree.nodes if n.type == 'TEX_SKY'), None) if scene.world and scene.world.use_nodes else None
    if d is None:
        sun.rotation_euler = _SUN_DEFAULT['rot']
        if sky and _SUN_DEFAULT['sky']:
            sky.sun_elevation, sky.sun_rotation = _SUN_DEFAULT['sky']
        return
    ov = os.environ.get('STAN_EXT_SUN')                      # test override "x,y,z" for the exterior photos
    if ov:
        d = tuple(float(v) for v in ov.split(','))
    sd = Vector(d).normalized()
    sun.rotation_euler = (-sd).to_track_quat('-Z', 'Y').to_euler()
    if sky:
        sky.sun_elevation = math.asin(max(0.02, sd.z))
        sky.sun_rotation = math.atan2(-sd.x, sd.y)


GLASS_EXT = (0.52, 0.57, 0.57, 1)        # double-pane low-E seen from outside: the rooms read darker than the sunlit walls
_GLASS_DEFAULT = {}


def _glass(ext):
    import bpy
    m = bpy.data.materials.get("WindowGlass")
    if m is None or not m.use_nodes:
        return
    b = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if b is None:
        return
    if 'col' not in _GLASS_DEFAULT:
        _GLASS_DEFAULT['col'] = tuple(b.inputs["Base Color"].default_value)
        _GLASS_DEFAULT['spec'] = b.inputs["Specular IOR Level"].default_value
    b.inputs["Base Color"].default_value = GLASS_EXT if ext else _GLASS_DEFAULT['col']
    b.inputs["Specular IOR Level"].default_value = 1.0 if ext else _GLASS_DEFAULT['spec']   # 4 glass faces of a double pane


INTERIOR_DIM = 0.08        # exterior photos: the rooms are lit by daylight only, so the interior fills are dimmed
_LIGHT_DEFAULT = {}


def _interior_lights(ext):
    """Scale every lamp inside the house envelope (not the exterior lanterns) for the exterior photos; restore otherwise."""
    import bpy
    if not _LIGHT_DEFAULT:
        for ob in bpy.data.objects:
            if ob.type != 'LIGHT' or ob.data.type == 'SUN':
                continue
            if ob.name.startswith('L_Lantern'):              # the coach lanterns are off in the daytime photos
                _LIGHT_DEFAULT[ob.name] = ob.data.energy
                continue
            x, y, z = ob.matrix_world.translation
            if GAR[0] + 0.05 < x < XB1 - 0.05 and 0.05 < y < YB1 - 0.05 and Z_GAR < z < Z_RIDGE:
                _LIGHT_DEFAULT[ob.name] = ob.data.energy
    for n, e in _LIGHT_DEFAULT.items():
        ob = bpy.data.objects.get(n)
        if ob is not None:
            k = (0.0 if n.startswith('L_Lantern') else INTERIOR_DIM) if ext else 1.0
            ob.data.energy = e * k


def _light_levels(scene, name):
    import bpy
    sun = bpy.data.objects.get("Sun")
    bg = next((n for n in scene.world.node_tree.nodes if n.type == 'BACKGROUND'), None) if scene.world and scene.world.use_nodes else None
    if sun is None or bg is None:
        return
    lv = LIGHT.get(name, (1.0, 1.0))
    ks, kb = lv[0], lv[1]
    sun.data.energy = _SUN_DEFAULT['energy'] * ks
    sun.data.angle = math.radians(lv[2]) if len(lv) > 2 else _SUN_DEFAULT['angle']
    bg.inputs['Strength'].default_value = _SUN_DEFAULT['sky_strength'] * kb


SHADE_TINT_EXT = (1.12, 1.06, 0.95, 1)   # exterior photos: milder than the interiors' warm sky tint (03 / 25 / 27 shade patches)
_TINT_DEFAULT = {}


def _shade_tint(scene, ext):
    """setup_day(shade_warm=1) multiplies the light the sky casts by a warm tint (good for the interiors); outside, the
    photos' shadows are neutral / bluish, so the tint is neutralised for the exterior cameras."""
    if not scene.world or not scene.world.use_nodes:
        return
    for n in scene.world.node_tree.nodes:
        if n.type == 'MIX' and getattr(n, 'data_type', '') == 'RGBA' and n.blend_type == 'MULTIPLY' and not n.inputs['B'].is_linked:
            key = n.name
            if key in _TINT_DEFAULT:
                n.inputs['B'].default_value = SHADE_TINT_EXT if ext else _TINT_DEFAULT[key]


_WORLDS = {}


def _pix_dir(cam, W, H, u, v):
    """World ray direction of photo pixel (u, v) for a W x H frame (horizontal sensor fit, lens shift)."""
    from mathutils import Vector
    cd = cam.data
    k = cd.sensor_width / cd.lens
    x = ((u + 0.5) / W - 0.5 + cd.shift_x) * k
    y = ((0.5 - (v + 0.5) / H) * (H / W) + cd.shift_y) * k
    return (cam.matrix_world.to_3x3() @ Vector((x, y, -1.0))).normalized()


def _sky_plane(d):
    z = max(d.z, 0.03)
    return (d.x / z, d.y / z)


def _overcast_light(world, k, mix, tint):
    """Replace the light the sky casts (non-camera rays) by an overcast-like distribution: luminance k (1 + 2 z) / 3 above
    the horizon (CIE overcast), a dim ground below, mixed by `mix` with the clear sky - for a cloudy-bright photo."""
    from archviz.sky import _math, _mix
    nt = world.node_tree
    bg = next(n for n in nt.nodes if n.type == 'BACKGROUND')
    lit = bg.inputs["Color"].links[0].from_socket
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nrm = nt.nodes.new("ShaderNodeVectorMath"); nrm.operation = 'NORMALIZE'
    nt.links.new(nrm.inputs[0], tc.outputs["Generated"])
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(sep.inputs["Vector"], nrm.outputs["Vector"])
    z = _math(nt, 'MAXIMUM', sep.outputs["Z"], 0.0)
    lum = _math(nt, 'MULTIPLY', _math(nt, 'ADD', 1.0, _math(nt, 'MULTIPLY', z, 2.0)), k / 3.0)
    lum = _math(nt, 'MULTIPLY', lum, _math(nt, 'ADD', 0.15, _math(nt, 'MULTIPLY', _math(nt, 'GREATER_THAN', sep.outputs["Z"], -0.01), 0.85)))
    grey = nt.nodes.new("ShaderNodeCombineColor")
    for ch, t in zip(("Red", "Green", "Blue"), tint):
        nt.links.new(grey.inputs[ch], _math(nt, 'MULTIPLY', lum, t))
    nt.links.new(bg.inputs["Color"], _mix(nt, mix, lit, grey.outputs["Color"]))


def _photo_world(scene, name):
    """The listing photo's own sky for camera rays (ext_skies.py): a copy of the day world with archviz.sky.camera_sky;
    the light the sky casts is untouched."""
    from . import ext_skies as SK
    from archviz import sky as _sky
    if name not in SK.GRAD or scene.camera is None:
        return None
    if name in _WORLDS:
        return _WORLDS[name]
    W, H = SK.SIZE[name]
    cam = scene.camera
    import bpy
    bpy.context.view_layer.update()          # run.py creates the cameras just before: refresh matrix_world
    lin = SK.LIN
    grad = [(math.sin(math.radians(e)), lin[c]) for e, c in SK.GRAD[name]]
    feats = []
    for f in SK.FEAT.get(name, ()):
        if f[0] == 'blob':
            _, (u, v), (ru, rv), a, col, shade, amt = f[:7]
            soft, nz = (f[7], f[8]) if len(f) > 8 else (0.45, 0.5)
            c = _sky_plane(_pix_dir(cam, W, H, u, v))
            p1 = _sky_plane(_pix_dir(cam, W, H, u + ru, v))
            p2 = _sky_plane(_pix_dir(cam, W, H, u, v - rv))
            a1 = (p1[0] - c[0], p1[1] - c[1]); a2 = (p2[0] - c[0], p2[1] - c[1])
            det = a1[0] * a2[1] - a2[0] * a1[1]
            if abs(det) < 1e-12:
                continue
            b1 = (a2[1] / det, -a2[0] / det); b2 = (-a1[1] / det, a1[0] / det)
            feats.append(dict(kind='blob', c=c, b1=b1, b2=b2, color=lin[col], alpha=a, shade=lin[shade], shade_amt=amt,
                              soft=soft, noise=nz, freq=4.5))
        else:
            _, (u0, v0), (u1, v1), hw, a, col, nz = f
            pa, pb = _sky_plane(_pix_dir(cam, W, H, u0, v0)), _sky_plane(_pix_dir(cam, W, H, u1, v1))
            um, vm = (u0 + u1) / 2, (v0 + v1) / 2
            L = math.hypot(u1 - u0, v1 - v0)
            nu, nv = -(v1 - v0) / L, (u1 - u0) / L
            m0 = _sky_plane(_pix_dir(cam, W, H, um, vm)); m1 = _sky_plane(_pix_dir(cam, W, H, um + nu * hw, vm + nv * hw))
            w = math.hypot(m1[0] - m0[0], m1[1] - m0[1])
            plen = math.hypot(pb[0] - pa[0], pb[1] - pa[1])
            feats.append(dict(kind='streak', a=pa, b=pb, width=w, color=lin[col], alpha=a, noise=nz,
                              along=max(1.5, plen / w * 0.05), across=4.5 if hw >= 12 else 1.2))
    base = _SUN_DEFAULT['pristine'] or _SUN_DEFAULT['world']
    Wd = base.copy()
    Wd.name = f"World_{name}"
    if name in OVERCAST:
        _overcast_light(Wd, *OVERCAST[name])
    gain = _sky.camera_sky(Wd, grad, feats, name="CamSky")
    _WORLDS[name] = (Wd, gain.name)
    return _WORLDS[name]


def _cache_defaults(scene):
    """Record the house defaults ONCE, from the day world and sun as run.py built them, before any camera changes them."""
    import bpy
    if _SUN_DEFAULT:
        return
    w = scene.world
    sun = bpy.data.objects.get("Sun")
    nodes = w.node_tree.nodes if w and w.use_nodes else []
    sky = next((n for n in nodes if n.type == 'TEX_SKY'), None)
    bg = next((n for n in nodes if n.type == 'BACKGROUND'), None)
    _SUN_DEFAULT.update(world=w, rot=tuple(sun.rotation_euler) if sun else None, sky=(sky.sun_elevation, sky.sun_rotation) if sky else None,
                        energy=sun.data.energy if sun else 1.0, angle=sun.data.angle if sun else 0.02,
                        sky_strength=bg.inputs['Strength'].default_value if bg else 1.0,
                        pristine=w.copy() if w else None)
    for n in nodes:                           # the interiors' warm sky tint (setup_day shade_warm)
        if n.type == 'MIX' and getattr(n, 'data_type', '') == 'RGBA' and n.blend_type == 'MULTIPLY' and not n.inputs['B'].is_linked:
            c = tuple(n.inputs['B'].default_value)
            if c[0] > 1.05 and c[2] < 0.97:
                _TINT_DEFAULT[n.name] = c


def before_render(scene, name):
    ext = name in EXT_PHOTOS
    _cache_defaults(scene)
    pw = _photo_world(scene, name)
    scene.world = pw[0] if pw else _SUN_DEFAULT['world']
    _aim_sun(scene, SUN.get(name))
    _light_levels(scene, name)
    _shade_tint(scene, ext)
    if pw:                                   # camera sky: display targets independent of this camera's exposure / strength
        nt = scene.world.node_tree
        bg = next(n for n in nt.nodes if n.type == 'BACKGROUND')
        nt.nodes[pw[1]].inputs[1].default_value = 2.0 ** (-scene.view_settings.exposure) / max(1e-4, bg.inputs['Strength'].default_value)
    _glass(ext)
    _interior_lights(ext)

