"""Interiors: floors, ceilings, partitions, furniture and lights for every ROOMS entry.  Split this into
interior_<level>.py files (as houses/walsh does) once it grows."""
from .plan import *
from archviz.mesh import *
from archviz.lights import *
from archviz.parts import *


def build(M):
    for room, (x0, x1, y0, y1, z0, z1) in ROOMS.items():
        f = MB(); f.box(x0, x1, y0, y1, z0 - 0.02, z0 + 0.02); f.build(f"Floor_{room}", [M['oak_floor']])
        c = MB(); c.box(x0, x1, y0, y1, z1 - 0.02, z1 + 0.02); c.build(f"Ceiling_{room}", [M['white_int']])
        room_light(f"L_{room}", room)                                   # soft fill; keep it <= 30 % of the real fixtures
    # partitions with door openings
    w = MB()
    w.wall('X', MX0 + WT, MX1 - WT, PARTITION_Y - 0.06, PARTITION_Y + 0.06, Z_GND, Z_SOF, holes=[(-1.0, 1.5, Z_GND, Z_GND + 2.4)])
    w.wall('Y', MY0 + WT, MY1 - WT, PARTITION_X - 0.06, PARTITION_X + 0.06, Z_UP, Z_UPC, holes=[(3.0, 4.0, Z_UP, Z_UP + 2.2)])
    w.build("Partitions", [M['white_int']])
    # living room
    s = MB(); sofa(s, 0.0, 3.2, 2.8, 1.0, z=Z_GND, mi_seat=0, mi_back=0, mi_base=1)
    s.build("Sofa", [M['fabric_grey'], M['walnut']], smooth=True, bevel=0.02)
    t = MB(); round_table(t, 0.0, 1.6, Z_GND, 0.5, h=0.38, mi=0)
    t.build("CoffeeTable", [M['walnut']])
    r = MB(); r.rbox(-2.0, 2.0, 0.8, 4.4, Z_GND + 0.02, Z_GND + 0.035, r=0.006, mi=0)
    r.build("Rug_Living", [M['rug']])
    pts = [(x, y) for x in (-4.0, 0.0, 4.0) for y in (2.0, 5.0)]
    dl = MB(); downlights(dl, pts, Z_SOF - 0.005, mi=0); dl.build("Living_Downlights", [M['emit_down']])
    for (x, y) in pts:
        add_light(f"L_Down_{x:+.0f}_{y:.0f}", 'SPOT', (x, y, Z_SOF - 0.05), 25, size=0.05)
    # bedroom
    b = MB(); bed(b, -3.0, 6.0, z=Z_UP, mi_frame=0, mi_linen=1, mi_pillow=1, mi_throw=2)
    b.build("Bed", [M['walnut'], M['linen_white'], M['throw']], smooth=True, bevel=0.01)
