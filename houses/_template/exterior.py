"""Building envelope: walls with openings, slabs, roof, ALL exterior glass, the entry door, soffit downlights.
Ownership rule (keeps parallel work sane): exterior owns the shell + exterior glass; interiors own finishes,
partitions, furniture and room lights; site owns terraces / pools / garden walls; landscape owns trees."""
import math
from .plan import *
from archviz.mesh import *
from archviz.lights import *
from archviz.parts import *


def build(M):
    # ---- shell: walls with holes for the glass, cantilevered first-floor slab, roof slab (one mesh, travertine)
    mb = MB()
    mb.wall('X', MX0, MX1, MY0, MY0 + WT, Z_GND, Z_SOF, holes=[(GLASS_X0, GLASS_X1, Z_GND, Z_SOF - 0.05)])   # south: glass
    mb.wall('X', MX0, MX1, MY0, MY0 + WT, Z_SOF, Z_UPC, holes=[(-5.0, 5.0, Z_UP + 0.9, Z_UP + 2.3)])          # upper strip window
    mb.wall('X', MX0, MX1, MY1 - WT, MY1, Z_GND, Z_UPC, holes=[(-3.0, 3.0, Z_GND + 0.9, Z_GND + 2.4)])       # north: kitchen window
    mb.wall('Y', MY0, MY1, MX0, MX0 + WT, Z_GND, Z_UPC)                                                       # west
    mb.wall('Y', MY0, MY1, MX1 - WT, MX1, Z_GND, Z_UPC, holes=[(3.0, 6.0, Z_GND + 0.5, Z_GND + 2.6)])         # east window
    mb.plate(MX0 - 0.6, MX1 + 0.6, MY0 - 1.2, MY1 + 0.3, Z_SOF, Z_UP)                                        # L1 slab, overhangs the glass
    mb.plate(MX0 - 0.6, MX1 + 0.6, MY0 - 1.2, MY1 + 0.3, Z_UPC, Z_ROOF)                                      # roof slab
    mb.build("Shell", [M['trav']])
    # ---- glass (slot 0) + dark frames (slot 1)
    g = MB()
    yg = MY0 + 0.1
    glass_wall(g, GLASS_X0, DOOR_X0 - 0.05, yg, yg + T, Z_GND, Z_SOF - 0.05, mullions=(-3.0,))
    glass_wall(g, DOOR_X1 + 0.05, GLASS_X1, yg, yg + T, Z_GND, Z_SOF - 0.05, mullions=(3.0,))
    glass_wall(g, -5.0, 5.0, yg, yg + T, Z_UP + 0.9, Z_UP + 2.3)
    glass_wall(g, -3.0, 3.0, MY1 - 0.2, MY1 - 0.2 + T, Z_GND + 0.9, Z_GND + 2.4)
    glass_wall(g, MX1 - 0.2, MX1 - 0.2 + T, 3.0, 6.0, Z_GND + 0.5, Z_GND + 2.6)
    g.build("Glazing", [M['glass'], M['frame']])
    # ---- pivot door: its own object so the film can swing it (house.py DOORS)
    d = MB()
    door_leaf(d, DOOR_X0, DOOR_X1, yg, Z_GND, Z_SOF - 0.05, mi=0)
    d.build("Entry_Door", [M['door']])
    # ---- soffit downlights under the overhang: emissive discs + real spots
    xs = (-4.0, -2.0, 0.0, 2.0, 4.0)
    dl = MB()
    downlights(dl, [(x, MY0 - 0.6) for x in xs], Z_SOF - 0.005, mi=0)
    dl.build("Soffit_Downlights", [M['emit_down']])
    for x in xs:
        add_light(f"L_Soffit_{x:+.0f}", 'SPOT', (x, MY0 - 0.6, Z_SOF - 0.05), 40, size=0.05)
