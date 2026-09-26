"""13695 Stanford Dr, Carmel IN — THE PLAN (bpy-free): levels, footprint, walls, openings, rooms.

A 2005 Ryland two-storey (listing: 4 bed, 2.5 bath, 2,345 sq ft above grade, 2-car 468 sq ft garage) on a pond lot.
Every dimension below is photo-derived or inferred; see REFERENCES.md for the evidence and the uncertain choices.

Coordinates (metres): X = left(-)/right(+) as seen from the street, Y = street(-)/rear(+), Z up.
  X = 0      the upper storey's left (-X) exterior face (= the great room's left wall)
  Y = 0      the front face of the garage, the porch columns and the two-storey brick bay
  Z = 0      the finished main floor

MASSING (photos 01, 02, 25, 27, 28, 30-32)
  two-storey block      x 0 .. 12.5, y 1.5 .. 11.8 (rear width from the 6-ft slider in photo 25)
  garage (one storey)   x -1.25 .. 6.18, y 0 .. 6.35; protrudes 1.25 m left of the block (aerials 30/31), 16-ft door
  porch recess          x 6.18 .. 8.53, y 0 .. 1.5 (door wall at y 1.5; two square white columns)
  brick bay             x 8.53 .. 12.5, y 0 .. 1.5, two storeys (living room below, bedroom 21 above)
  upper front           left gable face x 0 .. 3.2 and right gable face x 5.5 .. 8.53 at y 1.5; centre wall recessed
                        to y 2.1 between them
  roofs                 side-gabled main roof; a small left front gable; a full-height right cross gable (ridge meets the
                        main ridge); a front-sloping roof over the brick bay (its left rake rises toward the back in
                        photos 02/30); a one-storey shed roof across the garage + porch that wraps the garage's left side

LEVELS
  Z_GRADE -0.40  lawn at the house       Z_GAR -0.28  garage slab     Z_PORCH -0.18  porch slab
  Z_MAIN   0.00  main floor              Z_C1   2.44  main ceiling (8 ft; interior solves 2.40-2.46)
  Z_UP     2.84  upper floor             Z_C2   5.20  upper ceilings (Z_PLATE 5.46: exterior wall top / roof bearing)
"""
import math

# ---------------------------------------------------------------- levels
Z_GRADE, Z_GAR, Z_PORCH, Z_WALK = -0.40, -0.10, -0.17, -0.36
Z_MAIN, Z_C1, Z_UP = 0.0, 2.44, 2.84          # floor-to-floor 2.84 (upper window head/sill solved at 5.08/3.55); main
                                              # ceiling 8'0": interior solves 2.46 (08-11), 2.42-2.45 (12-14), 2.40 (04-06)
Z_PLATE = Z_UP + 2.62                    # exterior upper wall top under the roof / soffits (5.46; the roof sits on it)
Z_C2 = Z_UP + 2.36                       # upper CEILING 5.20: level solves on exterior anchors, 21 -> 5.20 +/- 0.03,
                                         # 16+17 soffit 5.18 +/- 0.02 (6'8" doors, window casings agree); was 5.46
Z_PATIO = -0.30
Z_GAR_DOOR = -0.25                        # slab at the garage door: 0.25 below the entry threshold (joint solve 01/02/03/30/31, +/- 0.02)
Z_STREET = -0.58

# ---------------------------------------------------------------- footprint
XB0, XB1 = 0.0, 12.50                     # two-storey block: interior 04/05/06 put the living room's east inner face at
                                          # 12.34-12.37 +/- 0.05; the exterior joint solve wants 12.5 +/- 0.15 (was 12.3)
YB0, YB1 = 1.5, 11.8
YB0_UP = 1.22                             # UPPER front wall faces (joint solve 1.22 +/- 0.03): the upper floor overhangs the
                                          # porch door wall (YB0) by 0.28 m; the lower door wall stays at YB0
EWT = 0.15                                # siding exterior wall
BWT = 0.25                                # brick-veneer exterior wall
IWT = 0.12                                # interior partition
GAR = (-1.30, 6.0, 0.0, 6.35)             # garage exterior x0, x1, y0, y1 (solved corner -1.32)
PORCH = (6.0, 8.70, 0.0, 1.5)             # right end = the bay's west face (exterior solve 8.70-8.72 +/- 0.05)
PORCH_COLS = (6.34, 8.86)                 # porch column centres x (01 / 02 / 03 agree to 0.05 with the final cameras), shaft 0.165
PORCH_COL_Y = 0.08                        # column centre y (joint solve 0.02 +/- 0.08; the slab runs in front of the plinths)
PORCH_ROOF_X1 = 9.05                      # the porch roof's right end runs past the bay's left corner (03: beam end 8.99, gutter 9.06)
Y_BAY = 0.86                              # the brick bay's front face: exterior joint solve 0.86 +/- 0.07 (door wall -> bay
                                          # front 0.73 +/- 0.06); interior 04/06 window-wall inner face 1.15 +/- 0.06 (was 0.50)
BAY = (8.70, XB1, Y_BAY, 1.5)             # two-storey brick bay
CEN = (3.245, 5.97, 1.60)                 # recessed upper centre wall x0, x1, face y (joint solve)
LGABLE = (0.0, CEN[0])                    # upper-left front gable face (at y = YB0_UP)
RGABLE = (CEN[1], BAY[0])                 # upper-right cross-gable face (at y = YB0_UP), gable spans CEN[1] .. XB1

# ---------------------------------------------------------------- roofs (pitch = rise / run)
# joint solve of photos 01+02+03+25+30+31 with the upper faces at YB0_UP 1.22 / recess 1.60 (EXT, cams/ext_facade_solve.py):
# main pitch 0.523 +/- 0.006 (6.3/12), roof surface at the wall line 5.525 +/- 0.02, ridge 8.19 (aerials 31+32 alone: 8.26 +/- 0.08),
# eave overhang 0.31, gable-end rake overhang 0.37, left gable 0.824 +/- 0.011; the cross gable's ridge meets the main ridge
# (junction on the ridge line in 30 and 31)
P_MAIN = 0.523
P_GABLE = 0.824                           # the left front gable (01 rake slope 0.84-0.86, joint 0.822)
P_BAY = 0.70                              # the brick bay's small front gable (inferred; mostly hidden by the tree)
P_SHED = 4 / 12                           # first-floor roof across the garage / porch
OVH = 0.31                                # eave overhang (and the front gables' side eaves)
OVH_RAKE = 0.37                           # rake overhang at the main gable ends and the front gables' rakes
Z_ROOF_WALL = Z_PLATE + 0.065             # roof top surface at the upper wall lines (5.525; joint solve)
Z_WALL1 = 2.56                            # structural top of the one-storey walls (inside the shed roof slab; soffit hides it)
Z_EAVE1 = 2.28                            # first-floor shed soffit (01: gutter top 2.46, brick top 2.18; 03 agrees)
Z_SHED = 2.48                             # shed roof top surface at its eave line (gutter top 2.48-2.51 in 01 / 03)
Z_BRICK_TOP = 2.18                        # top of the garage-front brick (soldier course 1.95 .. 2.17 over the door, photo 03)
Z_PORCH_CEIL = 2.17                       # flat porch ceiling = the underside of the porch beam (photo 03: 2.15-2.19, 01: 2.13)

# ---------------------------------------------------------------- stair (U-shaped, 14 risers, half landing at +X)
RISERS = 14
RISE = Z_UP / RISERS                      # 0.196
TREAD = 0.26
ST_X0 = 9.76                              # first riser of the lower flight / last riser of the upper flight (newel
                                          # triangulated from 05 + 06 at (9.80 +/- 0.05, 4.88); was 9.57)
ST_LAND = ST_X0 + 6 * TREAD               # 11.32: landing edge
ST_Y0, ST_YM, ST_Y1 = 4.87, 5.87, 6.82    # lower flight y 4.87..5.82, upper flight 5.87..6.82 (moved back 1.02 m in the
                                          # 2026-09-24 review: 04+05+06 joint solve living depth 3.72 +/- 0.10 from the window
                                          # wall -> 4.87 +/- 0.12; photo 06 alone 4.86; photos 19-21 upper plan 4.75..4.90)
Z_LAND = 7 * RISE

# ---------------------------------------------------------------- rooms: (x0, x1, y0, y1, z_floor, z_ceiling)
ROOMS = {
    'garage':  (-1.15, 5.85, 0.25, 6.35, Z_GAR, Z_C1 + 0.05),
    'foyer':   (7.15, BAY[0], 1.75, 4.38, Z_MAIN, Z_C1),
    'living':  (BAY[0] + BWT, XB1 - EWT, Y_BAY + BWT, ST_Y0, Z_MAIN, Z_C1),
    'hall':    (6.00, 7.20, 3.85, 6.47, Z_MAIN, Z_C1),
    'great':   (0.15, 5.85, 6.47, 11.65, Z_MAIN, Z_C1),
    'dining':  (5.85, 8.75, 6.47, 11.65, Z_MAIN, Z_C1),
    'kitchen': (8.75, XB1 - EWT, 8.05, 11.65, Z_MAIN, Z_C1),
    'powder':  (7.32, 8.75, 4.97, 6.60, Z_MAIN, Z_C1),
    'pantry':  (11.25, XB1 - EWT, 6.60, 8.95, Z_MAIN, Z_C1),
    # upper floor (layout inferred around the photographed rooms 15-23; see REFERENCES.md)
    'master':  (0.15, 4.95, 6.10, 11.65, Z_UP, Z_C2),
    'mbath':   (0.15, 2.95, 3.47, 6.00, Z_UP, Z_C2),
    'wic':     (0.15, 2.95, 1.65, 3.35, Z_UP, Z_C2),
    'mhall':   (3.07, 4.43, 2.37, 6.00, Z_UP, Z_C2),
    'bed20':   (6.02, 8.60, 1.65, 4.78, Z_UP, Z_C2),
    'bed21':   (BAY[0] + BWT, XB1 - EWT, Y_BAY + BWT, ST_Y0 - IWT, Z_UP, Z_C2),
    'bed19':   (8.30, XB1 - EWT, 7.30, 11.65, Z_UP, Z_C2),
    'hbath':   (5.07, 8.18, 8.96, 11.65, Z_UP, Z_C2),
    'laundry': (5.07, 7.20, 6.12, 8.84, Z_UP, Z_C2),
    'uhall':   (4.55, ST_X0, 4.90, 6.00, Z_UP, Z_C2),
    'stairwell': (ST_X0, XB1 - EWT, ST_Y0, ST_Y1, Z_MAIN, Z_C2),
}

# ---------------------------------------------------------------- walls
def W(along, a0, a1, b0, b1, z0, z1, kind, out=0, name=''):
    """out = which side is the exterior face (-1: toward -Y/-X, +1: toward +Y/+X, 0: interior partition)."""
    return dict(along=along, a0=a0, a1=a1, b0=b0, b1=b1, z0=z0, z1=z1, kind=kind, out=out, name=name)


ZF = Z_GRADE            # foundation / wall bottom outside
WALLS = [
    # ---- garage (one storey): brick front, siding sides / left rear
    W('X', GAR[0], GAR[1], 0.0, BWT, Z_GRADE + 0.1, Z_WALL1, 'brick', -1, 'garage_front'),     # garage front
    W('Y', 0.0, GAR[3], GAR[0], GAR[0] + EWT, ZF, Z_WALL1, 'siding', -1, 'garage_left'),   # garage left side
    W('X', GAR[0], XB0, GAR[3], GAR[3] + EWT, ZF, Z_WALL1, 'siding', 1, 'garage_rear'),    # garage rear, outside the block
    W('Y', BWT, 1.5, GAR[1] - EWT, GAR[1], Z_PORCH, Z_WALL1, 'siding', 1, 'porch_left'),     # porch left return = garage right side
    W('Y', 1.5, GAR[3], GAR[1] - EWT, GAR[1], Z_GAR, Z_C1 + 0.10, 'int', 0, 'garage_hall'),        # garage | foyer + hall
    W('X', XB0, GAR[1], GAR[3], GAR[3] + IWT, Z_GAR, Z_C1 + 0.10, 'int', 0, 'garage_great'),       # garage | great room
    # ---- porch door wall + brick bay (two storeys)
    W('X', PORCH[0], PORCH[1], 1.5, 1.5 + BWT, Z_PORCH, Z_WALL1, 'brick', -1, 'door_wall'),     # door wall
    W('X', BAY[0], BAY[1], Y_BAY, Y_BAY + BWT, ZF, Z_PLATE, 'brick', -1, 'bay_front'),                         # bay front
    W('Y', Y_BAY + BWT, 1.5 + BWT, BAY[0], BAY[0] + BWT, ZF, Z_PLATE, 'brick', -1, 'bay_left'),      # bay left side (porch right return; the corner belongs to bay_front)
    # ---- block exterior
    W('Y', GAR[3] + IWT, YB1, XB0, XB0 + EWT, ZF, Z_UP, 'siding', -1, 'left_main'),              # left, main floor (behind garage)
    W('Y', YB0_UP, YB1, XB0, XB0 + EWT, Z_UP - 0.25, Z_PLATE, 'siding', -1, 'left_upper'),             # left, upper floor
    W('X', XB0, XB1, YB1 - EWT, YB1, ZF, Z_PLATE, 'siding', 1, 'rear'),                                # rear
    W('Y', Y_BAY + BWT, 1.5, XB1 - BWT, XB1, ZF, Z_PLATE, 'brick', 1, 'bay_right'),                         # right, brick bay return
    W('Y', 1.5, YB1 - EWT, XB1 - EWT, XB1, ZF, Z_PLATE, 'siding', 1, 'right'),                        # right
    # ---- upper front walls over the garage / porch
    W('X', LGABLE[0], LGABLE[1], YB0_UP, YB0_UP + EWT, Z_UP - 0.25, Z_PLATE, 'siding', -1, 'lgable'),       # left gable face
    W('X', CEN[0], CEN[1], CEN[2], CEN[2] + EWT, Z_UP - 0.25, Z_PLATE, 'siding', -1, 'centre'),       # recessed centre
    W('Y', YB0_UP, CEN[2] + EWT, CEN[0], CEN[0] + EWT, Z_UP - 0.25, Z_PLATE, 'siding', 1, 'cen_lret'),    # recess left return
    W('Y', YB0_UP, CEN[2] + EWT, CEN[1] - EWT, CEN[1], Z_UP - 0.25, Z_PLATE, 'siding', -1, 'cen_rret'),   # recess right return
    W('X', RGABLE[0], RGABLE[1], YB0_UP, YB0_UP + EWT, Z_WALL1, Z_PLATE, 'siding', -1, 'rgable'),       # right gable face
]

# ---------------------------------------------------------------- openings (windows / doors) in the wall planes
def O(name, along, a0, a1, b, z0, z1, kind, **kw):
    d = dict(name=name, along=along, a0=a0, a1=a1, b=b, z0=z0, z1=z1, kind=kind)
    d.update(kw)
    return d


UP_SILL, UP_HEAD = 3.55, 5.08                       # upper 3'0" x 5'0" windows (rear photo 25: 3.53 / 5.05)
FUP_SILL, FUP_HEAD = 3.43, 4.932                   # FRONT upper windows (joint solve incl. INT_CAM's interior heads at 1/3 weight)
OPENINGS = [
    # front, ground floor (joint solve of photos 01, 02, 03, 30, 31 against the entry door leaf 0 .. 2.03; EXT notes)
    O('garage_door', 'X', 0.663, 5.519, 0.1, Z_GAR_DOOR, Z_GAR_DOOR + 2.08, 'garage_door'),
    O('garage_win', 'X', -0.579, -0.053, 0.1, 1.041, 1.869, 'window', grid=(2, 3), shutters=False),
    O('front_door', 'X', 7.258, BAY[0], 1.6, Z_MAIN, Z_MAIN + 2.09, 'entry'),     # leaf 7.34..8.25 (joint solve 7.336), sidelight to BAY[0] (03)
    O('living_win', 'X', 9.822, 11.56, Y_BAY + 0.1, 0.536, 2.049, 'window', units=2, grid=(3, 2), lower_grid=False, shutters=True,
      keystone=True),
    # front, upper floor (narrow white frames; the two gable windows have a crosshead + keystone, photos 01 / 02 / 30)
    O('lg_win', 'X', 1.195, 2.075, YB0_UP + 0.05, FUP_SILL, FUP_HEAD, 'window', grid=(3, 2), header=True, shutters=True),
    O('cen_win', 'X', 4.159, 5.038, CEN[2] + 0.05, FUP_SILL, FUP_HEAD, 'window', grid=(3, 2), shutters=True),
    O('rg_win', 'X', 6.971, 7.851, YB0_UP + 0.05, FUP_SILL, FUP_HEAD, 'window', grid=(3, 2), header=True, shutters=True),
    O('bay_up_win', 'X', 9.822, 11.56, Y_BAY + 0.1, 3.431, 4.794, 'window', units=2, grid=(3, 2), shutters=True),
    # rear (joint solve with XB1 12.45: outer white frames in 25 minus the J-channel; kitchen sill from 28 (+ photo 12))
    O('great_win', 'X', 1.973, 3.774, YB1 - 0.07, 0.687, 2.148, 'window', units=2, grid=(3, 2), lower_grid=True),
    O('slider', 'X', 6.587, 8.383, YB1 - 0.07, Z_MAIN, 2.08, 'slider'),
    O('kitchen_win', 'X', 10.154, 11.011, YB1 - 0.07, 1.33, 2.169, 'window', grid=(3, 2), lower_grid=True),
    O('rear_up_r', 'X', 11.191, 12.044, YB1 - 0.07, 3.511, 4.993, 'window', grid=(3, 2)),
    O('rear_up_m', 'X', 3.781, 4.633, YB1 - 0.07, 3.511, 4.993, 'window', grid=(3, 2)),
    O('rear_up_l', 'X', 0.422, 1.274, YB1 - 0.07, 3.511, 4.993, 'window', grid=(3, 2)),
    # right side: stair-landing window (photo 15)
    # interior: the garage -> hall entry door (photos 05, 14, 24); only the hole is cut here, interior_main builds the unit
    O('garage_entry', 'Y', 5.40, 6.21, GAR[1] - EWT / 2, Z_GAR, 2.05, 'door_int'),
    O('landing_win', 'Y', ST_Y0 + 0.58, ST_Y0 + 1.38, XB1 - 0.07, Z_LAND + 0.90, Z_LAND + 2.21, 'window', grid=(2, 2)),   # photo 15 (INT_CAM's p15: casing 5.41..6.32, opening ~2.32..3.63)
]


def holes_for(wall, tol=1e-4):
    from archviz.plan import holes_for as holes
    return holes(wall, OPENINGS, tol)


def check():
    from archviz.plan import validate
    validate(WALLS, OPENINGS)
    return True


# ---------------------------------------------------------------- site (inferred from the aerials 30-32 and photo 01)
LOT = (-4.0, 16.5, -7.6, 36.0)            # x0, x1, y0 (back of sidewalk), y1 (rear lot line / common area)
SIDEWALK = (-7.6, -6.2)                   # y range, 1.4 m wide
PARKWAY = (-6.2, -8.4)                    # grass tree lawn between the sidewalk and the curb
CURB_Y = -8.4
STREET = (-8.4, -17.4)                    # 9 m pavement
DRIVE = (0.55, 5.83)                      # driveway x at the garage door (widens toward the street)
PATH_Y = 44.0                             # the common walking path behind the lots
POND = dict(cx=6.0, cy=92.0, rx=78.0, ry=38.0)
FOUNTAIN = (-10.0, 96.0)


if __name__ == '__main__':
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
    check()
    print(f"plan ok: {len(WALLS)} walls, {len(OPENINGS)} openings, {len(ROOMS)} rooms")
