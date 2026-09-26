"""<House name>, <city> — THE PLAN (bpy-free): levels, plan constants and interior volumes.

Every geometry module does `from .plan import *`, so this file is the single source of truth for where things are.
Write the site reading here first (which photo shows what, how the levels stack) before touching geometry.

Coordinates (metres): X = left(-)/right(+) as seen from the street, Y = street(-)/rear(+), Z up.

LEVELS
  Z_GND   0.0   ground floor: living, kitchen, entry
  Z_SOF   3.1   ground-floor soffit (underside of the first-floor slab)
  Z_UP    3.4   upper floor: bedroom, bath
  Z_UPC   6.5   upper ceiling (underside of the roof slab)
  Z_ROOF  6.8   top of the roof slab

PLAN
  main block   x -7 .. 7, y 0 .. 11 (front face y = 0, full-height glass on the south face, pivot door at x 0)
  lawn         x -16 .. 16, y -14 .. -1, hedge along the street
"""
Z_GND, Z_UP, Z_ROOF = 0.0, 3.4, 6.8
Z_SOF, Z_UPC = Z_UP - 0.3, Z_ROOF - 0.3
T = 0.012                           # glass pane thickness
WT = 0.35                           # exterior wall thickness

MX0, MX1, MY0, MY1 = -7.0, 7.0, 0.0, 11.0        # main block
GLASS_X0, GLASS_X1 = -5.5, 5.5                   # south glass wall
DOOR_X0, DOOR_X1 = -0.6, 0.6                     # pivot door inside the glass wall
LAWN = (-16.0, 16.0, -14.0, -1.0)
PARTITION_Y = 7.0                                # living | kitchen
PARTITION_X = 1.0                                # bedroom | bath (upper)

# ---------------------------------------------------------------- interior volumes (x0, x1, y0, y1, z_floor, z_ceiling)
ROOMS = {
    'living':  (MX0 + WT, MX1 - WT, MY0 + WT, PARTITION_Y, Z_GND, Z_SOF),
    'kitchen': (MX0 + WT, MX1 - WT, PARTITION_Y, MY1 - WT, Z_GND, Z_SOF),
    'bedroom': (MX0 + WT, PARTITION_X, MY0 + WT, MY1 - WT, Z_UP, Z_UPC),
    'bath':    (PARTITION_X, MX1 - WT, MY0 + WT, MY1 - WT, Z_UP, Z_UPC),
}
