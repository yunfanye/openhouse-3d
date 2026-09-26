"""Trees (archviz/trees.py): a few near trees at full detail and a low-LOD treeline ring that closes the horizon."""
import math
from .plan import *
from archviz.mesh import *
from archviz import trees as _tr


def build(M):
    bark = {'bark': M['bark']}
    _tr.oak("Oak_Front", (-14.0, -8.0, 0.0), height=11.0, spread=9.0, seed=1, mats=bark)
    _tr.olive("Olive_Entry", (4.5, -3.0, 0.0), height=3.5, seed=2, mats=bark)
    _tr.conifer("Redwood_Rear", (10.0, 22.0, 0.0), height=24.0, r=3.0, seed=3, mats=bark)
    for i in range(24):
        a = 2 * math.pi * i / 24
        _tr.oak(f"Treeline_{i}", (60 * math.cos(a), 60 * math.sin(a), 0.0), height=12.0, spread=11.0, seed=10 + i, detail=0.2, mats=bark)
