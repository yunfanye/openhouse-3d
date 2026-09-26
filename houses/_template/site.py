"""Site: ground, lawn, path to the door, street hedge.  The hedge opts into polish's leaf cards (ob["leaf_cards"]);
the lawn's hair grass is declared in house.py GRASS."""
from .plan import *
from archviz.mesh import *
from archviz.lights import *
from archviz.parts import *


def build(M):
    g = MB(); g.box(-80, 80, -80, 80, -0.3, 0.0)
    g.build("Ground", [M['ground']], coll='Site')
    x0, x1, y0, y1 = LAWN
    l = MB(); l.box(x0, x1, y0, y1, -0.02, 0.02)
    l.build("Lawn", [M['lawn']], coll='Site')
    p = MB(); p.box(-2.0, 2.0, y0, MY0, 0.0, 0.04)
    p.build("Path", [M['pavers']], coll='Site')
    h = MB(); h.box(x0, x1, y0 - 1.0, y0 - 0.2, 0.0, 1.2)
    hedge = h.build("Hedge", [M['foliage']], coll='Site')
    hedge["leaf_cards"] = {"leaf": "cluster_shrub", "size": 0.14, "density": 120}
