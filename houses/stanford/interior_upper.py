"""Upper floor of 13695 Stanford Dr (photos 15-23): floor structure with the stairwell opening, partitions painted per
room on each face, paint skins on the exterior walls' inner faces, ceilings (the primary bedroom's tray), 7 ft doors,
the stair-top guard, the stairwell dressing, window treatments, bath fixtures, closets and the staging of every
photographed room after its photograph (up_staging.py builds the rooms' contents; this module owns the layout).

LAYOUT (interior faces; Z_UP .. Z1), parametric in the plan constants (XB1, BAY, Y_BAY, CEN, RGABLE, ST_*; values below for
the plan of 2026-09-24).  Photographed rooms follow point solves of their photos (cams/int_p15.json … int_p23.json, REFERENCES.md):
  wic      0.15..2.60 x 1.65..3.20      walk-in closet under the left-gable window (22)
  vest     2.72..CEN0 x 1.65..3.20      dressing vestibule WIC <-> primary bath (inferred)
  mbath    0.15..2.84 x 3.32..5.80      primary bath (18: camera in the doorway 2.58 m from the far wall; vanity on the x 0.15
                                        wall, toilet on the far wall, 60" tub along the x 2.84 wall behind a curtain at x 2.08)
  lin      2.96..4.95 x 3.32..5.80      linen / storage closet off the primary bath (inferred)
  clo20    2.96..5.29 x 2.25..4.65      bedroom 20's walk-in closet (22) behind the recessed centre window; door from 20
  bed20    5.41..8.50 x 2.25..5.70      + the right-gable bump from CEN1 (20: 3.26 x 3.98 m solved, listing 13 x 11; the photo
                                        shows no jog at the recess corner - unresolved conflict with the facade, see notes)
  bed21    8.74..XR x 1.11..ST_Y0-T     bedroom 21 in the brick bay (21: 3.6 m deep, camera in the doorway at the back-left)
  landing  8.74..ST_X0 x ST_Y0..ST_Y1   stair-top hall: bed21's door at its south end, bed19's at its north end
  hall     5.07..8.74 x ST_YM-0.05..ST_Y1  upper hall north of bed20; the primary suite's door at its west end
  lpass    5.07..5.87 x ST_Y1+T..10.02  passage (cased opening) to the laundry (inferred)
  hbath    5.99..8.48 x ST_Y1+T..9.50   hall bath (23: vanity on the x 8.48 wall ending at the pier face y 9.50; the toilet in
  hnook    5.99..7.50 x 9.50..9.90      a nook beside the pier (edge x 7.50); 60" tub along the x 5.99 wall)
  laundry  5.07..7.50 x 10.14..11.65    laundry (listing: upper level; windowless, inferred)
  clo19    7.62..8.48 x 9.62..11.65     bedroom 19's closet, door in its left wall (the open door at photo 19's left edge)
  bed19    8.60..XR x ST_Y1+T..11.65    bedroom 19 (19: x 8.58..8.69 .. XR, fan at (10.50, 9.33))
  master   0.15..4.95 x 5.92..11.65     primary bedroom (16, 17), tray ceiling
Stair flights, their balustrades and everything below the main ceiling are interior_front's.
"""
import math
import random
from .plan import *
from archviz.mesh import MB, collection
from archviz.lights import add_light, area_light
from archviz.cladding import Face, holed_wall
from archviz import fenestration as fen
from archviz import materials as _m
from archviz import plants as _pl

Z0 = Z_UP
Z1 = Z_C2                              # upper ceilings 5.20 (INT_CAM's level solves on exterior anchors: 21 5.20, 16+17 5.18)
ZF0 = Z_UP - 0.012                     # top of the structural floor (finish layer 12 mm)
T = 0.12                               # partition thickness
DOOR_H = 2.03                          # 6'8" doors (17 with the 5.20 ceiling: casing top 2.05 above the floor)
TRAY = 0.29                            # primary bedroom tray: raised 0.29 m ...
TRAY_IN = 0.51                         # ... inside a 0.51 m perimeter soffit (16+17 joint level solve)
Z_SOFFIT = 5.183                       # the primary's soffit underside (= its wall top), 16+17: 5.18 +/- 0.02
COLL = 'Interior_Upper'
LCOLL = 'Lights_Upper'

# ---------------------------------------------------------------- stair-derived lines
Y21 = ST_Y0 - T                        # bed21 back wall (its room face)
HY0 = ST_YM - 0.05                     # upper hall south face (bed20's back wall north face)
HY1 = ST_Y1                            # upper hall north face (stairwell back wall south face)
Y19 = ST_Y1 + T                        # bed19 front face
Y20B = HY0 - T                         # bed20 back face
YCEN = CEN[2] + EWT                    # 2.25: the recessed centre wall's inner face
XREC = CEN[1]                          # 5.90: the right gable face's left edge (recess right return, inner face)
XR = XB1 - EWT                         # right exterior wall, inner face (12.30)
YR = YB1 - EWT                         # rear exterior wall, inner face (11.65)
YU = globals().get('YB0_UP', YB0)      # upper-storey front gable faces (plan.YB0_UP when EXT defines it, else the block face)
YF = YU + EWT                          # front gable walls' inner face
DYF = YF - 1.65                        # shift of the front walls since the photo 20 / 22 solves (their staging follows it)
XBL, XBR = BAY[0] + BWT, BAY[1] - BWT  # brick bay returns, inner faces (8.95, 12.20)
YBF, YBB = Y_BAY + BWT, YB0 + BWT      # bay front inner face (1.11) and the end of its left return (1.75)
XP = 8.50                              # bed20 | bed21 partition west face (photo 20 level solve with the 5.20 ceiling: 8.50)
XB20 = 5.30                            # bed20's -X wall inner face (INT_CAM p20 with YB0_UP: 5.30); wall XB20 - T .. XB20
XB19 = 8.60                            # bed19's -X wall inner face (photo 19: 8.58 .. 8.69); wall XB19 - T .. XB19 = hall bath's +X face

YWI = YF + 2.05                        # primary walk-in closet (photo 22, left gable, honey blinds seen in 01): 2.05 +/- 0.04 deep
YBF0 = YWI + T                         # 3.96: primary bath far wall (photo 18 with 12" tiles, toilet / vanity depths: 3.80 +/- 0.28)
YPS = 6.57                             # primary bedroom's south wall, bath side face; bedroom face YPS + T = 6.69 (INT_CAM 16+17 6.69)
XMT = 2.84                             # primary bath tub-side (east) wall west face (photo 18: curtain plane x 2.0, 60" tub)
XV0, XV1 = XMT + T, XMT + T + 0.80     # dressing hall from the primary bedroom to the WIC along the bath's east wall (inferred)
XC0 = XV1 + T                          # bedroom 20's closet (behind the recessed centre window) / linen west face
CH22 = (0.15, 0.44, YF, YF + 0.29)     # photo 22: a chase in the WIC's front-left corner (INT_CAM: face x 0.45; corner y 1.66)
XHB = 5.99                             # hall bath -X wall (photo 23: the 60" tub 5.99..6.75, toilet centred 7.12 by the pier)
YHP, YHN = 9.50, 9.90                  # hall bath: vanity-alcove back (pier face) and the toilet / tub nook's back wall (photo 23)
XPE = 7.50                             # hall bath pier edge (photo 23 level solve 7.50 +/- 0.06)
R = {
    'wic':     (0.15, XMT, YF, YWI),
    'vest':    (XV0, XV1, YF, YPS),
    'mbath':   (0.15, XMT, YBF0, YPS),
    'clo20':   (XC0, XB20 - T, YCEN, YWI),
    'lin':     (XC0, 4.95, YBF0, YPS),
    'bed20':   (XB20, XP, YCEN, Y20B),
    'bed21':   (XP + T, XR, YBF, Y21),
    'landing': (XP + T, ST_X0, ST_Y0, HY1),
    'hall':    (5.07, XP + T, HY0, HY1),
    'lpass':   (5.07, XHB - T, Y19, YHN + T),
    'hbath':   (XHB, XB19 - T, Y19, YHP),
    'hnook':   (XHB, XPE, YHP, YHN),
    'laundry': (5.07, XPE, YHN + 2 * T, YR),
    'clo19':   (XPE + T, XB19 - T, YHP + T, YR),
    'bed19':   (XB19, XR, Y19, YR),
    'master':  (0.15, 4.95, YPS + T, YR),
}



def rects(name):
    """Floor / ceiling rectangles of a room (bed20 adds the right-gable bump, bed21 the bay)."""
    x0, x1, y0, y1 = R[name]
    if name == 'bed20':
        return [(x0, x1, y0, y1), (XREC, x1, YF, y0)]
    if name == 'vest':                                  # its front end steps with the recessed centre wall
        return [(x0, CEN[0], YF, YCEN), (x0, x1, YCEN, y1)]
    if name == 'bed21':
        return [(x0, x1, YBB, y1), (XBL, XBR, YBF, YBB), (XBR, x1, YB0, YBB)]
    return [(x0, x1, y0, y1)]


# ---------------------------------------------------------------- paints / finishes (colours matched to the photos, local_mats)
SLOTS = ['up_core', 'up_white', 'up_master', 'up_b19', 'up_b20', 'up_b21', 'up_hall', 'up_bath', 'up_stair']


def local_mats(M):
    """Upper-floor finishes.  Wall colours are tuned so the photo-camera renders match the photos' mean wall colours
    (sRGB patches sampled from the photos): the primary suite / hall are a warm greige, bedroom 20 a yellower tan, 21 the
    palest pinkish beige, 19 a beige, the baths a very pale lilac-grey-blue, the closets white."""
    S = M.setdefault
    S('up_core', _m.new_mat("UpWallCore", (0.7, 0.7, 0.68, 1), rough=0.9))
    S('up_white', _m.plaster("UpPaintWhite", base=(0.74, 0.735, 0.72, 1), rough=0.85, grain=0.02))
    S('up_master', _m.plaster("UpPaintGreige", base=(0.50, 0.39, 0.26, 1), rough=0.85, grain=0.02))
    S('up_b19', _m.plaster("UpPaintBeige19", base=(0.54, 0.45, 0.34, 1), rough=0.85, grain=0.02))
    S('up_b20', _m.plaster("UpPaintTan20", base=(0.60, 0.48, 0.29, 1), rough=0.85, grain=0.02))
    S('up_b21', _m.plaster("UpPaintBlush21", base=(0.63, 0.56, 0.47, 1), rough=0.85, grain=0.02))
    S('up_hall', _m.plaster("UpPaintHall", base=(0.52, 0.43, 0.32, 1), rough=0.85, grain=0.02))
    S('up_stair', _m.plaster("UpPaintStairwell", base=(0.62, 0.55, 0.46, 1), rough=0.85, grain=0.02))   # photo 15: lighter, greyer
    S('up_bath', _m.plaster("UpPaintBathBlueGrey", base=(0.50, 0.52, 0.59, 1), rough=0.6, grain=0.015))
    S('up_carpet', _m.rug("CarpetUpper", (0.31, 0.22, 0.15, 1), (0.38, 0.28, 0.20, 1), scale=180))
    S('up_carpet_master', _m.rug("CarpetPrimaryGrey", (0.19, 0.18, 0.18, 1), (0.25, 0.24, 0.24, 1), scale=180))
    S('up_tile', _m.tiles("BathTileBeige", (0.33, 0.27, 0.21, 1), grout=(0.25, 0.22, 0.19, 1), size=(0.305, 0.305), gap=0.004,
                          rough=0.35, variation=0.06, mottle=0.45, bump=0.2, coat=0.2))
    S('up_vinyl_floor', _m.tiles("LaundryVinyl", (0.52, 0.48, 0.42, 1), grout=(0.45, 0.42, 0.37, 1), size=(0.305, 0.305), gap=0.002,
                                 rough=0.4, variation=0.04, mottle=0.3, bump=0.05))
    S('up_trim', _m.new_mat("UpTrimWhite", (0.80, 0.80, 0.78, 1), rough=0.32, spec=0.5, coat=0.2))
    S('up_door', _m.new_mat("UpDoorWhite", (0.80, 0.80, 0.78, 1), rough=0.3, spec=0.5, coat=0.25))
    S('ceiling_up', _m.knockdown("KnockdownCeilingUp", base=(0.88, 0.875, 0.86, 1), strength=0.55, scale=7.0))
    S('brushed', _m.new_mat("BrushedNickelUp", (0.62, 0.61, 0.58, 1), rough=0.3, metal=1.0))
    S('chrome', _m.new_mat("UpChrome", (0.9, 0.9, 0.9, 1), rough=0.06, metal=1.0))
    S('crystal', _m.new_mat("CrystalGlass", (0.95, 0.96, 0.98, 1), rough=0.02, transmission=1.0, ior=1.55))
    S('bulb', _m.new_mat("VanityGlobe", (0.95, 0.94, 0.90, 1), rough=0.3, transmission=0.4, emit=(1.0, 0.92, 0.80, 1), emit_str=6.0))
    S('stair_oak', _m.wood("StairRedOak", light=(0.60, 0.33, 0.14, 1), dark=(0.46, 0.22, 0.08, 1), grain_axis='Z', rough=0.4, coat=0.4))
    S('blind_white', _m.new_mat("BlindWhite", (0.86, 0.86, 0.84, 1), rough=0.45, spec=0.35))
    S('blind_wood', _m.wood("BlindHoneyWood", light=(0.62, 0.36, 0.17, 1), dark=(0.50, 0.27, 0.11, 1), grain_axis='X', rough=0.45, coat=0.25))
    S('cord_white', _m.new_mat("BlindCord", (0.85, 0.85, 0.83, 1), rough=0.8))
    return M


# ================================================================ geometry helpers
def box6(mb, x0, x1, y0, y1, z0, z1, mneg, mpos, axis):
    """Axis-aligned box: the face toward -axis gets slot mneg, toward +axis mpos, all others mneg."""
    if x1 - x0 < 1e-6 or y1 - y0 < 1e-6 or z1 - z0 < 1e-6:
        return
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    faces = {'-z': (0, 3, 2, 1), '+z': (4, 5, 6, 7), '-y': (0, 1, 5, 4), '+x': (1, 2, 6, 5), '+y': (2, 3, 7, 6), '-x': (3, 0, 4, 7)}
    for k, f in faces.items():
        mi = mpos if k == '+' + axis.lower() else mneg
        mb._add([v[i] for i in f], [(0, 1, 2, 3)], mi)


def two_tone_wall(mb, along, a0, a1, b0, b1, z0, z1, holes, mneg, mpos):
    """Partition with holes painted mneg on its b0 face and mpos on its b1 face."""
    hs = [(max(h0, a0), min(h1, a1), max(hz0, z0), min(hz1, z1)) for (h0, h1, hz0, hz1) in holes
          if h1 > a0 and h0 < a1 and hz1 > z0 and hz0 < z1]
    av = sorted({a0, a1, *[h[0] for h in hs], *[h[1] for h in hs]})
    zv = sorted({z0, z1, *[h[2] for h in hs], *[h[3] for h in hs]})
    ax = 'y' if along == 'X' else 'x'
    for i in range(len(av) - 1):
        ca, cb = av[i], av[i + 1]
        am = (ca + cb) / 2
        run = None
        cells = []
        for j in range(len(zv) - 1):
            za, zb = zv[j], zv[j + 1]
            solid = not any(h[0] < am < h[1] and h[2] < (za + zb) / 2 < h[3] for h in hs)
            if solid:
                run = (run[0], zb) if run else (za, zb)
            elif run:
                cells.append(run); run = None
        if run:
            cells.append(run)
        for (za, zb) in cells:
            if along == 'X':
                box6(mb, ca, cb, b0, b1, za, zb, mneg, mpos, ax)
            else:
                box6(mb, b0, b1, ca, cb, za, zb, mneg, mpos, ax)


def skin(mb, along, b, side, a0, a1, z0, z1, holes=(), mi=0, t=0.006):
    """Paint skin just inside a wall face at plane b: `side` = +1 if the room is toward +b."""
    c0, c1 = (b + 0.001, b + 0.001 + t) if side > 0 else (b - 0.001 - t, b - 0.001)
    holed_wall(mb, along, a0, a1, c0, c1, z0, z1, holes, mi)


def win_holes(along, b0, b1, a0, a1, grow=0.0):
    """Openings (from plan.OPENINGS) in the plane band b0..b1 overlapping a0..a1, as (a0, a1, z0, z1) holes."""
    out = []
    for o in OPENINGS:
        if o['along'] == along and b0 - 0.3 <= o['b'] <= b1 + 0.3 and o['a1'] > a0 and o['a0'] < a1:
            out.append((o['a0'] - grow, o['a1'] + grow, o['z0'] - grow, o['z1'] + grow))
    return out


def baseboard(mb, along, b, side, a0, a1, z=Z0, h=0.10, t=0.014, gaps=(), mi=0):
    """Painted baseboard on a wall face, interrupted at door `gaps` (a0, a1)."""
    spans, cur = [], a0
    for g0, g1 in sorted(gaps):
        if g0 > cur:
            spans.append((cur, g0))
        cur = max(cur, g1)
    if cur < a1:
        spans.append((cur, a1))
    for s0, s1 in spans:
        if s1 - s0 < 0.02:
            continue
        c0, c1 = (b, b + side * t) if side > 0 else (b + side * t, b)
        if along == 'X':
            mb.box(s0, s1, min(c0, c1), max(c0, c1), z, z + h, mi)
            mb.box(s0, s1, min(c0, c1) - (0.004 if side < 0 else -0.004) * 0, max(c0, c1), z + h, z + h + 0.008, mi)
        else:
            mb.box(min(c0, c1), max(c0, c1), s0, s1, z, z + h, mi)


# ---------------------------------------------------------------- partitions + doors table
# (name, along, a0, a1, b0, b1, paint on the b0 face, paint on the b1 face, [door/opening (a0, a1)], z0)
WALLS_UP = [
    # primary suite: south wall (bath / dressing hall / upper hall | bedroom), bath, WIC, dressing hall, closets
    ('prim_s_bath', 'X', 0.15, XV0, YPS, YPS + T, 'up_bath', 'up_master', [(0.83, 1.55)], Z0),          # 17: casing 0.77..1.61
    ('prim_s_vest', 'X', XV0, XC0, YPS, YPS + T, 'up_white', 'up_master', [], Z0),                      # 17: plain to x 4.08
    ('prim_s_lin', 'X', XC0, 5.07, YPS, YPS + T, 'up_white', 'up_master', [], Z0),
    ('wic_bath', 'X', 0.15, XV0, YWI, YBF0, 'up_white', 'up_bath', [], Z0),
    ('wic_east', 'Y', YF, YWI, XMT, XV0, 'up_white', 'up_white', [(YF + 0.07, YF + 0.79)], Z0),         # 22: camera in this door
    ('bath_east', 'Y', YBF0, YPS, XMT, XV0, 'up_bath', 'up_white', [(5.72, 6.46)], Z0),                 # 18: door seen in the mirror
    ('vest_e_clo', 'Y', YCEN, YWI, XV1, XC0, 'up_white', 'up_white', [], Z0),
    ('vest_e_lin', 'Y', YWI, YPS, XV1, XC0, 'up_white', 'up_white', [], Z0),
    ('clo20_lin', 'X', XC0, XB20 - T, YWI, YBF0, 'up_white', 'up_white', [], Z0),
    ('chase_20', 'Y', YBF0, HY0, 4.95, XB20 - T, 'up_white', 'up_white', [], Z0),
    ('lin_east', 'Y', HY0, YPS, 4.95, 5.07, 'up_white', 'up_hall', [(5.90, 6.48)], Z0),
    ('master_right', 'Y', YPS, YR, 4.95, 5.07, 'up_master', 'up_hall', [(7.02, 7.78)], Z0),             # entry from the passage
    # bedroom 20
    ('b20_left', 'Y', YCEN, Y20B, XB20 - T, XB20, 'up_white', 'up_b20', [(1.80, 2.30)], Z0),        # 20: casing 1.69..2.36
    ('b20_back', 'X', XB20 - T, XP + T, Y20B, HY0, 'up_b20', 'up_hall', [(7.70, 8.46)], Z0),
    ('b20_b21', 'Y', YBB, Y21, XP, XP + T, 'up_b20', 'up_b21', [], Z0),
    ('b20_land', 'Y', Y21, Y20B, XP, XP + T, 'up_b20', 'up_hall', [], Z0),
    # bedroom 21 back wall (over the stairwell it continues down to the main ceiling)
    ('b21_back_land', 'X', XP + T, ST_X0, Y21, ST_Y0, 'up_b21', 'up_hall', [(8.80, 9.56)], Z0),
    ('b21_back_stair', 'X', ST_X0, XR, Y21, ST_Y0, 'up_b21', 'up_stair', [], Z_C1),
    # hall north wall, bath / passage / laundry / closet block
    ('hall_north', 'X', 5.07, XB19, HY1, Y19, 'up_hall', 'up_bath', [(5.10, 5.82), (7.56, 8.32)], Z0),   # 5.10..5.82 cased
    ('b19_front_land', 'X', XB19, ST_X0, HY1, Y19, 'up_hall', 'up_b19', [(8.70, 9.46)], Z0),
    ('b19_front_stair', 'X', ST_X0, XR, HY1, Y19, 'up_stair', 'up_b19', [], Z_C1),
    ('lpass_hbath', 'Y', Y19, YHN + T, XHB - T, XHB, 'up_hall', 'up_bath', [], Z0),
    ('hbath_b19', 'Y', Y19, YHP + T, XB19 - T, XB19, 'up_bath', 'up_b19', [], Z0),
    ('hbath_pier', 'X', XPE + T, XB19 - T, YHP, YHP + T, 'up_bath', 'up_white', [], Z0),
    ('nook_clo19', 'Y', YHP, YHN, XPE, XPE + T, 'up_bath', 'up_white', [], Z0),
    ('nook_back', 'X', XHB, XPE + T, YHN, YHN + T, 'up_bath', 'up_white', [], Z0),
    ('lpass_laundry', 'X', 5.07, XHB - T, YHN + T, YHN + 2 * T, 'up_hall', 'up_white', [(5.10, 5.82)], Z0),
    ('laundry_nook', 'X', XHB - T, XPE + T, YHN + T, YHN + 2 * T, 'up_white', 'up_white', [], Z0),
    ('laundry_clo19', 'Y', YHN + 2 * T, YR, XPE, XPE + T, 'up_white', 'up_white', [], Z0),
    ('clo19_b19', 'Y', YHP + T, YR, XB19 - T, XB19, 'up_white', 'up_b19', [(9.85, 10.61)], Z0),     # 19: casing edge y 10.88
]
# doors: (name, along, a0, a1, b0, b1, hinge 'a0'|'a1', swing side -1|+1 (toward -b / +b), open angle deg)
DOORS_UP = [
    ('Door_MBath', 'X', 0.83, 1.55, YPS, YPS + T, 'a0', +1, 0),               # photo 17: closed; opens into the bedroom (18)
    ('Door_Master', 'Y', 7.02, 7.78, 4.95, 5.07, 'a0', -1, 80),               # the primary's entry (unphotographed), open
    ('Door_BathVest', 'Y', 5.72, 6.46, XMT, XV0, 'a1', +1, 0),                # 18: closed (in the mirror)
    ('Door_WIC', 'Y', YF + 0.07, YF + 0.79, XMT, XV0, 'a0', +1, 95),          # photo 22 is taken from this doorway
    ('Door_Linen', 'Y', 5.90, 6.48, 4.95, 5.07, 'a1', +1, 0),
    ('Door_Clo20', 'Y', 1.80, 2.30, XB20 - T, XB20, 'a0', -1, 0),             # photo 20: closed
    ('Door_Bed20', 'X', 7.70, 8.46, Y20B, HY0, 'a1', +1, 85),                 # photo 20 is taken from its doorway
    ('Door_Bed21', 'X', 8.80, 9.56, Y21, ST_Y0, 'a0', -1, 88),                # into bed21 along its -X wall (photo 21's right edge)
    ('Door_Bed19', 'X', 8.70, 9.46, HY1, Y19, 'a0', -1, 86),                  # photo 19 is taken from its doorway
    ('Door_HBath', 'X', 7.56, 8.32, HY1, Y19, 'a1', +1, 80),
    ('Door_Laundry', 'X', 5.10, 5.82, YHN + T, YHN + 2 * T, 'a0', +1, 0),
    ('Door_Clo19', 'Y', 9.85, 10.61, XB19 - T, XB19, 'a1', -1, 92),           # photo 19: open away, hinges at the far jamb
]
OPEN_CASED = [('X', 5.10, 5.82, HY1, Y19)]                                    # hall -> laundry passage (cased opening)


def partitions(M):
    mats = [M[k] for k in SLOTS]
    mb = MB()
    for (name, along, a0, a1, b0, b1, pn, pp, holes, z0) in WALLS_UP:
        hs = [(h0, h1, Z0 - 0.01, Z0 + DOOR_H) for (h0, h1) in holes]
        two_tone_wall(mb, along, a0, a1, b0, b1, z0, Z1, hs, SLOTS.index(pn), SLOTS.index(pp))
    cx0, cx1, cy0, cy1 = CH22                                            # photo 22's shallow chase in the WIC corner
    box6(mb, cx0, cx1, cy0, cy1, Z0, Z1, SLOTS.index('up_white'), SLOTS.index('up_white'), 'y')
    mb.build("Up_Partitions", mats, coll=COLL)
    fr = MB()
    for (name, along, a0, a1, b0, b1, pn, pp, holes, z0) in WALLS_UP:
        for (h0, h1) in holes:
            f = Face(along, b1, +1)
            fen.interior_door_frame(f, fr, h0, h1, Z0, Z0 + DOOR_H, b1 - b0, mi=0)
    fr.build("Up_DoorFrames", [M['up_trim']], coll=COLL)
    for (name, along, a0, a1, b0, b1, hinge, swing, ang) in DOORS_UP:
        door_leaf(M, name, along, a0, a1, b0, b1, hinge, swing, ang)


def door_leaf(M, name, along, a0, a1, b0, b1, hinge, swing, ang, layout='four'):
    """Moulded four-panel door (photos 17, 20: two tall panels over two short), hung on the jamb at `hinge`, swung by
    `ang` degrees toward the `swing` side; satin-nickel knobs and three hinges."""
    mb = MB()
    bm = (b0 + b1) / 2
    f = Face(along, bm, +1)
    a0i, a1i = a0 + 0.02, a1 - 0.02
    z0, z1 = Z0 + 0.012, Z0 + DOOR_H - 0.003
    f.box(mb, a0i, a1i, -0.0175, 0.0175, z0, z1, 0)
    W, H = a1i - a0i, z1 - z0
    st = 0.115
    rows = [(0.06, 0.36), (0.42, 0.95)]                    # bottom pair, tall top pair (fractions of the height)
    for (f0, f1) in rows:
        for c in range(2):
            p0 = a0i + st + c * (W - 2 * st) / 2 + (0.03 if c else 0)
            p1 = a0i + st + (c + 1) * (W - 2 * st) / 2 - (0.03 if c == 0 else 0)
            for side in (1, -1):
                d0, d1 = (0.0175, 0.0215) if side > 0 else (-0.0215, -0.0175)
                f.box(mb, p0, p1, d0, d1, z0 + H * f0, z0 + H * f1, 0)                      # raised field
                e = 0.012
                f.box(mb, p0 - e, p1 + e, d0 - side * 0.0 if side > 0 else d0, d1 - 0.002 if side > 0 else d1 + 0.002,
                      z0 + H * f0 - e, z0 + H * f0, 0)
    kx = a1 - 0.075 if hinge == 'a0' else a0 + 0.075
    for side in (1, -1):
        fen.lever(f, mb, kx, Z0 + 0.92, 0.0175 * side, side=side, mi=1, knob=True)
    hx = a0 + 0.021 if hinge == 'a0' else a1 - 0.021
    for zz in (Z0 + 0.25, Z0 + DOOR_H / 2 + 0.1, Z0 + DOOR_H - 0.25):
        f.box(mb, hx - 0.006, hx + 0.006, -0.019, 0.019, zz - 0.05, zz + 0.05, 1)
    ob = mb.build(name, [M['up_door'], M['brushed']], coll=COLL)
    ha = a0 + 0.02 if hinge == 'a0' else a1 - 0.02
    hb = bm + swing * 0.0175
    px, py = (ha, hb) if along == 'X' else (hb, ha)
    for v in ob.data.vertices:
        v.co.x -= px; v.co.y -= py
    ob.location = (px, py, 0.0)
    free_dir = 1 if hinge == 'a0' else -1
    if along == 'X':
        s = 1 if (free_dir * swing) > 0 else -1
    else:
        s = -1 if (free_dir * swing) > 0 else 1
    ob.rotation_euler = (0, 0, math.radians(ang) * s)
    ob["hinge"] = (px, py)
    ob["open_sign"] = s
    return ob


# ================================================================ floors, ceilings, skins
def floors(M):
    s = MB()
    sw = (ST_X0, XR, ST_Y0, ST_Y1)
    xs = sorted({0.0, CEN[0], CEN[1], RGABLE[1], sw[0], XB1})
    for x0, x1 in zip(xs[:-1], xs[1:]):
        ys = [YU if x1 <= RGABLE[1] + 1e-6 else YB0, YB1]
        if x0 >= CEN[0] - 1e-6 and x1 <= CEN[1] + 1e-6:
            ys = [CEN[2], YB1]
        cuts = [(sw[2], sw[3])] if (x0 >= sw[0] - 1e-6) else []
        cur = ys[0]
        for c0, c1 in cuts:
            s.box(x0, x1, cur, c0, Z_C1 + 0.10, ZF0)
            cur = c1
        s.box(x0, x1, cur, ys[1], Z_C1 + 0.10, ZF0)
    s.box(BAY[0], BAY[1], BAY[2], YB0, Z_C1 + 0.10, ZF0)
    s.build("Up_FloorStructure", [M['up_core']], coll=COLL)
    fin = MB()
    for name in R:
        mi = {'mbath': 1, 'hbath': 1, 'hnook': 1, 'laundry': 2, 'master': 3}.get(name, 0)
        for (x0, x1, y0, y1) in rects(name):
            if x1 - x0 > 1e-3 and y1 - y0 > 1e-3:
                fin.box(x0, x1, y0, y1, ZF0, Z0, mi)
    for (name, along, a0, a1, b0, b1, *_r) in DOORS_UP:
        mi = 1 if name in ('Door_MBath', 'Door_HBath') else 0
        if along == 'X':
            fin.box(a0, a1, b0, b1, ZF0, Z0 - 0.001, mi)
        else:
            fin.box(b0, b1, a0, a1, ZF0, Z0 - 0.001, mi)
    for (along, a0, a1, b0, b1) in OPEN_CASED:
        fin.box(a0, a1, b0, b1, ZF0, Z0 - 0.001, 0)
    fin.build("Up_FloorFinish", [M['up_carpet'], M['up_tile'], M['up_vinyl_floor'], M['up_carpet_master']], coll=COLL)
    fa = MB()                                           # stairwell edge fascia (main ceiling -> upper floor) at the head of the lower flight
    fa.box(ST_X0 - 0.02, ST_X0, ST_Y0, ST_YM, Z_C1, Z0 + 0.001, 0)
    fa.build("Up_StairwellFascia", [M['up_hall']], coll=COLL)


def ceilings(M):
    c = MB()
    for name in R:
        if name == 'master':
            x0, x1, y0, y1 = R[name]
            tx0, tx1, ty0, ty1 = x0 + TRAY_IN, x1 - TRAY_IN, y0 + TRAY_IN, y1 - TRAY_IN
            e = 0.02                                   # riser ring e thick, standing in the soffit plate's hole (no coplanar faces)
            zs = Z_SOFFIT
            c.plate(x0, x1, y0, y1, zs, zs + 0.04, holes=[(tx0 - e, tx1 + e, ty0 - e, ty1 + e)], mi=0)
            c.box(tx0 - e, tx1 + e, ty0 - e, ty1 + e, zs + TRAY, zs + TRAY + 0.04, 0)
            for (a, b_, cc, d) in ((tx0 - e, tx1 + e, ty0 - e, ty0), (tx0 - e, tx1 + e, ty1, ty1 + e), (tx0 - e, tx0, ty0, ty1), (tx1, tx1 + e, ty0, ty1)):
                c.box(a, b_, cc, d, zs - 0.0005, zs + TRAY + 0.0005, 0)
            continue
        for (a0, a1, b0, b1) in rects(name):
            if a1 - a0 > 1e-3 and b1 - b0 > 1e-3:
                c.box(a0, a1, b0, b1, Z1, Z1 + 0.04, 0)
    c.box(ST_X0, XR, ST_Y0, ST_Y1, Z1, Z1 + 0.04, 0)                      # stairwell
    for (name, along, a0, a1, b0, b1, *_r) in WALLS_UP:                     # cap the partition tops over door heads
        pass
    c.build("Up_Ceilings", [M['ceiling_up']], coll=COLL)


# exterior-wall inner faces: (along, plane b, side toward the room, a0, a1, paint, z0)
EXT_SKINS = [
    ('Y', 0.15, +1, YF, YWI, 'up_white', Z0), ('Y', 0.15, +1, YBF0, YPS, 'up_bath', Z0), ('Y', 0.15, +1, YPS + T, YR, 'up_master', Z0),
    ('X', YF, +1, 0.15, XMT, 'up_white', Z0), ('X', YF, +1, XV0, CEN[0], 'up_white', Z0),
    ('Y', CEN[0], -1, YF, YCEN, 'up_white', Z0),
    ('X', YCEN, +1, CEN[0] + EWT, XV1, 'up_white', Z0), ('X', YCEN, +1, XC0, XB20 - T, 'up_white', Z0),
    ('X', YCEN, +1, XB20, XREC, 'up_b20', Z0),
    ('Y', XREC, +1, YF, YCEN, 'up_b20', Z0), ('X', YF, +1, XREC, XP, 'up_b20', Z0),
    ('X', YBF, +1, XBL, XBR, 'up_b21', Z0), ('Y', XBL, +1, YBF, YBB, 'up_b21', Z0), ('Y', XBR, -1, YBF, YB0, 'up_b21', Z0),
    ('X', YB0, +1, XBR, XR, 'up_b21', Z0), ('X', YBB, +1, XP + T, XBL, 'up_b21', Z0),
    ('Y', XR, -1, YB0, Y21, 'up_b21', Z0), ('Y', XR, -1, ST_Y0, ST_Y1, 'up_hall', Z_C1), ('Y', XR, -1, Y19, YR, 'up_b19', Z0),
    ('X', YR, -1, 0.15, 4.95, 'up_master', Z0), ('X', YR, -1, 5.07, XPE, 'up_white', Z0), ('X', YR, -1, XPE + T, XB19 - T, 'up_white', Z0),
    ('X', YR, -1, XB19, XR, 'up_b19', Z0),
]


def skins(M):
    mb = MB()
    for (along, b, side, a0, a1, paint, z0) in EXT_SKINS:
        holes = win_holes(along, b - 0.3, b + 0.3, a0, a1)
        skin(mb, along, b, side, a0, a1, z0, Z1, holes, SLOTS.index(paint))
    mb.build("Up_PaintSkins", [M[k] for k in SLOTS], coll=COLL)
    bb = MB()
    for (name, along, a0, a1, b0, b1, pn, pp, holes, z0) in WALLS_UP:
        if abs(z0 - Z0) > 1e-3:                               # walls that continue down the stairwell: no baseboard
            continue
        for side, b in ((-1, b0), (+1, b1)):
            baseboard(bb, along, b, side, a0, a1, gaps=holes)
    for (along, b, side, a0, a1, paint, z0) in EXT_SKINS:
        if abs(z0 - Z0) > 1e-3:
            continue
        baseboard(bb, along, b + side * 0.007, side, a0, a1)
    bb.build("Up_Baseboards", [M['up_trim']], coll=COLL)


def window_returns(M):
    """Drywall returns + a painted stool at every upper window (the photos show no casings: the drywall wraps into
    the opening and a white stool sits ~0.1 m below the exterior sill, photos 16, 19-22)."""
    tr = MB()
    for o in OPENINGS:
        if o['z0'] < Z_UP + 0.3 or o['name'] == 'landing_win':
            continue
        along, b = o['along'], o['b']
        a0, a1, z0, z1 = o['a0'], o['a1'], o['z0'], o['z1']
        # inner face of the wall this window sits in
        if along == 'X':
            if b > 6:
                face = Face('X', YB1 - EWT, +1)          # rear wall: room toward -Y; out = +1 means +Y is outward
            elif o['name'] == 'bay_up_win':
                face = Face('X', Y_BAY + BWT, -1)
            elif o['name'] == 'cen_win':
                face = Face('X', CEN[2] + EWT, -1)
            else:
                face = Face('X', YF, -1)
        else:
            continue
        # the stool: 22 mm board, 60 mm proud of the wall, with horns
        face.box(tr, a0 - 0.05, a1 + 0.05, -0.06, 0.10, z0 - 0.10, z0 - 0.078, 0)
        face.box(tr, a0 - 0.04, a1 + 0.04, -0.012, 0.0, z0 - 0.19, z0 - 0.10, 0)                    # apron
    tr.build("Up_WindowStools", [M['up_trim']], coll=COLL)


# ================================================================ stair top: guard rail, newel
def stair_top(M):
    """Natural red-oak guard at the head of the lower flight (photos 05/06/15): the upper hall edge x = ST_X0 over the
    lower flight (y ST_Y0 .. ST_YM), turned balusters, a box newel with a ball cap where the upper flight's rail ends."""
    oak = M['stair_oak']
    mb = MB()
    x = ST_X0 - 0.06
    ya, yb = ST_Y0 + 0.08, ST_YM - 0.02
    mb.box(x - 0.035, x + 0.035, ya, yb, Z0, Z0 + 0.03, 0)
    mb.rbox(x - 0.035, x + 0.035, ya, yb + 0.05, Z0 + 0.86, Z0 + 0.92, r=0.012, mi=0)
    n = int((yb - ya) / 0.11)
    for i in range(1, n + 1):
        y = ya + i * (yb - ya) / (n + 1)
        baluster(mb, x, y, Z0 + 0.03, Z0 + 0.86, 0)
    for (nx, ny) in ((x, yb + 0.04), (x, ya - 0.03)):
        newel(mb, nx, ny, Z0, Z0 + 1.10, 0)
    mb.build("Up_StairGuard", [oak], coll=COLL)


def baluster(mb, x, y, z0, z1, mi, w=0.034):
    h = z1 - z0
    mb.box(x - w / 2, x + w / 2, y - w / 2, y + w / 2, z0, z0 + 0.14 * h, mi)
    mb.box(x - w / 2, x + w / 2, y - w / 2, y + w / 2, z1 - 0.12 * h, z1, mi)
    mb.lathe(x, y, z0 + 0.14 * h, [(w * 0.46, 0), (w * 0.3, 0.05 * h), (w * 0.42, 0.12 * h), (w * 0.26, 0.2 * h), (w * 0.22, 0.6 * h),
                                  (w * 0.3, 0.66 * h), (w * 0.4, 0.72 * h), (w * 0.4, 0.74 * h)], seg=10, mi=mi)


def newel(mb, x, y, z0, z1, mi, w=0.085):
    mb.box(x - w / 2, x + w / 2, y - w / 2, y + w / 2, z0, z1 - 0.22, mi)
    mb.box(x - w / 2 - 0.01, x + w / 2 + 0.01, y - w / 2 - 0.01, y + w / 2 + 0.01, z1 - 0.22, z1 - 0.19, mi)
    mb.lathe(x, y, z1 - 0.19, [(w * 0.30, 0), (w * 0.22, 0.04), (w * 0.26, 0.06), (w * 0.48, 0.11), (w * 0.44, 0.16), (w * 0.2, 0.19), (0, 0.195)],
             seg=20, mi=mi)


def build(M):
    local_mats(M)
    collection(COLL)
    collection(LCOLL)
    floors(M)
    ceilings(M)
    partitions(M)
    skins(M)
    window_returns(M)
    stair_top(M)
    from . import up_staging
    up_staging.build(M)


def before_render(S, name):
    from . import up_staging
    up_staging.before_render(S, name)
