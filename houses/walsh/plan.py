"""
349 Walsh Rd, Atherton — THE PLAN: levels, plan constants and interior volumes (bpy-free; every module imports *).

Coordinates (metres): X = left(-)/right(+) as seen from the street, Y = street(-)/rear(+), Z up.

LEVELS
  Z_COURT 0.0   motor court, foyer, garage, billiard room; lounge + theatre are SUNKEN to -0.9 (ceiling = Z_LIV slab underside 2.23)
  Z_LAWN  0.9   front lawn (right of the house), fire trough
  Z_LIV   2.6   living level: living / dining / kitchen / family, pool terrace, courtyard, rear lawn
  Z_SOF   5.9   ground-floor soffit (underside of the L1 slab)
  Z_UP    6.3   upper floor + roof terraces
  Z_UPC   9.3   upper ceiling (underside of the roof slab)
  Z_ROOF  9.85  top of the roof slab

PLAN (all modules must use these — see the ROOMS dict for the interior volumes)
  main block        x -12.5 .. 7.5, y 0 .. 24   (front face y = 0, double-height foyer behind the entry glass)
  living pavilion   x 7.5 .. 12.5, y 3.8 .. 11.2 at Z_LIV (glass S + E, onyx fireplace wall inside, turf roof terrace above)
  family pavilion   x 7.5 .. 12.5, y 11.4 .. 17.8 at Z_LIV (glass E onto the courtyard lawn)
  courtyard         x 12.5 .. 24.5, y 3.2 .. 17.8 at Z_LIV: pool SW (glass S wall over the front lawn), turf NE
  north arm         x 7.5 .. 24.5, y 17.8 .. 24 at Z_LIV (green wall on its S face x 14.6..23.6); roof = upper dining terrace
  front lawn        x 7.5 .. 25, y -13 .. 3.2 at Z_LAWN; fire trough under the pool's glass wall
  motor court       x -18 .. 7.5, y -14.5 .. 0 at Z_COURT; reflecting pool in front of the entry glass
  rear lawn         x -13 .. 7.5, y 24 .. 34 at Z_LIV, white retaining wall + wooded hill behind
  roof              x -13.3 .. 13.6, y -1.6 .. 25, hole (8.6..12.6, 5.2..15.0) over the pool terrace
"""

Z_COURT, Z_LAWN, Z_LIV, Z_SOF, Z_UP, Z_UPC, Z_ROOF = 0.0, 0.9, 2.6, 5.9, 6.3, 9.3, 9.85
Z_WATER = 2.52                      # pool water surface: 80 mm below the coping / glass-wall top (photo 24: nearly brim-full)
T = 0.012                           # glass pane thickness
WT = 0.45                           # exterior wall thickness

# main block
MX0, MX1, MY0, MY1 = -12.5, 7.5, 0.0, 24.0
GLASS_X0, GLASS_X1 = -4.2, 3.6      # entry glass wall (3 panes + portal)
PORTAL_X0, PORTAL_X1, PORTAL_H = -0.2, 2.5, 3.15
DOOR_X0, DOOR_X1 = 0.35, 1.95
GAR_X0, GAR_X1, GAR_H = -10.6, -5.9, 3.0
BOX_X0, BOX_X1, BOX_Y0, BOX_Y1 = -2.4, 3.6, -1.9, 4.0        # vertical-slat wood box (Z_SOF-0.15 .. Z_ROOF)
SKY_X0, SKY_X1 = -5.4, -2.4                                 # glazed stair lantern left of the wood box
UP_Y0 = 1.0                                                 # upper-floor front face
STAIR_C = (-2.9, 5.4)                                       # spiral stair centre
STAIR_RI, STAIR_RO = 1.0, 2.5
STAIR_HOLE = (-5.6, -0.2, 2.7, 8.2)                         # hole in the L1 slab
FOYER_Y1 = 8.4                                              # foyer void ends / dining mezzanine starts
SLAB_Y0 = -0.6                                              # L1 slab front overhang
ROOF_X0, ROOF_X1, ROOF_Y0, ROOF_Y1 = -13.3, 13.6, -1.6, 25.0
ROOF_HOLE = (8.6, 12.6, 5.2, 15.0)

# living level pavilions + courtyard
LIV_X0, LIV_X1, LIV_Y0, LIV_Y1 = 7.5, 12.5, 3.8, 11.2
FAM_Y0, FAM_Y1 = 11.4, 17.8
ONYX = (10.9, 11.5, 4.4, 8.0)                               # fireplace onyx wall footprint
TX0, TX1, TY0, TY1 = 7.5, 24.5, 3.2, 17.8                   # pool terrace / courtyard
PX0, PX1, PY0, PY1 = 13.8, 22.0, 3.3, 9.6                   # pool
SPA = (17.4, 19.6, 5.2, 7.4)
ST_X0, ST_X1 = 12.2, 13.6                                   # lawn -> terrace stair
COURT_TURF = (13.2, 24.1, 10.8, 16.4)
NA_Y0, NA_Y1 = 17.8, 24.0                                   # north arm
GREEN_X0, GREEN_X1 = 14.6, 23.6                             # living green wall on the north arm's south face
CAN_X0, CAN_X1, CAN_Y0, CAN_Y1 = 18.6, 24.8, 11.2, 17.8     # low canopy over the NE courtyard corner
CAN_HOLE = (20.2, 23.4, 12.8, 16.0)
LAWN_X0, LAWN_X1, LAWN_Y0, LAWN_Y1 = 7.5, 25.0, -13.0, 3.2
FIRE = (15.3, 20.1, 2.05, 2.85)                             # fire trough footprint (lawn level)
REAR_Y1 = 34.0                                              # rear lawn ends at a white retaining wall

# ---------------------------------------------------------------- interior volumes (x0, x1, y0, y1, z_floor, z_ceiling)
ROOMS = {
    # Z_COURT
    'foyer':    (GLASS_X0 - 0.3, MX1 - WT, MY0 + WT, FOYER_Y1, Z_COURT, Z_SOF),        # double height, spiral stair
    'billiard': (-9.5, GLASS_X0 - 0.3, MY0 + WT, 8.4, Z_COURT, Z_LIV - 0.37),         # pool table, opens to the lounge (ceiling = slab underside)
    'lounge':   (-12.05, -5.0, 8.4, 17.0, -0.9, Z_LIV - 0.37),                        # SUNKEN 0.9 (5 steps down from the billiard); moss W, wine N, TV/fire E
    'theatre':  (-12.05, -5.0, 17.4, 23.55, -0.9, Z_LIV - 0.37),                      # sunken like the lounge
    'garage':   (-12.05, -5.0, MY0 + WT, 8.0, Z_COURT, Z_LIV - 0.37),
    # Z_LIV (main block)
    'kitchen':  (-12.05, -4.6, 8.4, 17.6, Z_LIV, Z_SOF),                              # two marble islands, oak cabinets
    'dining':   (-4.3, MX1 - WT, FOYER_Y1, FAM_Y1, Z_LIV, Z_SOF),                      # mezzanine over the foyer void; glass E onto the lawn
    'master':   (-12.05, -4.6, 17.8, MY1 - WT, Z_LIV, Z_SOF - 0.4),                    # glass N onto the rear lawn
    'bath':     (-4.6, -0.6, 19.6, MY1 - WT, Z_LIV, Z_SOF - 0.4),                      # backlit onyx
    'closet':   (-0.6, 3.4, 19.6, MY1 - WT, Z_LIV, Z_SOF - 0.4),
    'office':   (3.4, MX1 - WT, 17.8, MY1 - WT, Z_LIV, Z_SOF - 0.4),
    # Z_LIV (pavilions)
    'living':   (LIV_X0, LIV_X1, LIV_Y0, LIV_Y1, Z_LIV, Z_SOF),
    'family':   (LIV_X0, LIV_X1, FAM_Y0, FAM_Y1, Z_LIV, Z_SOF),
    'gym':      (7.9, 14.2, NA_Y0 + WT, NA_Y1 - WT, Z_LIV, Z_SOF - 0.4),               # glass S onto the courtyard lawn; sauna at its N side
    'guest':    (14.6, 24.0, NA_Y0 + WT, NA_Y1 - WT, Z_LIV, Z_SOF - 0.4),              # behind the green wall
    # Z_UP
    'upfamily': (0.6, MX1 - 0.4, 4.0, 11.0, Z_UP, Z_UPC),                             # 6.5 m wide; glass E + terrace, TV travertine wall
    'upbed1':   (0.6, MX1 - 0.4, 11.2, 17.8, Z_UP, Z_UPC),                            # glass E
    'upbed2':   (1.0, MX1 - 0.4, 18.0, MY1 - 0.4, Z_UP, Z_UPC),                        # 6.1 m wide; doors E onto the roof dining terrace
    'upbed2b':  (-5.4, 1.0, 18.0, MY1 - 0.4, Z_UP, Z_UPC),                             # bed 2's bath / dressing (west half of the old room)
    'upbed3':   (MX0 + 0.4, -5.6, 14.0, MY1 - 0.4, Z_UP, Z_UPC),
    'upsuite':  (MX0 + 0.4, -5.6, UP_Y0 + 0.4, 9.0, Z_UP, Z_UPC),                      # strip window S, glass W
    'uphall':   (-5.6, 0.6, 4.0, 18.0, Z_UP, Z_UPC),
    'boxroom':  (BOX_X0 + 0.15, BOX_X1 - 0.15, BOX_Y0 + 0.15, 4.0, Z_UP, Z_UPC - 0.15),  # inside the wood box
}
