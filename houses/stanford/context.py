"""Context behind and around the lot (photos 26, 29-32): the common lawn falling to the retention pond, the narrow
asphalt loop path round the pond, the pond with its riprap swales, boulder groups and aerating fountain, the
common-area trees (the dense honey-locust belt behind the lots, the young trees behind our lot, the far-bank row, the
east-bank belt), the houses across the pond, and the subdivision to the horizon (sitefar_suburb).  The lot itself
(lawns, hardscape, patio, fence, the street row within x +/- 60) is site.py / site_front.py; lot vegetation is
landscape.py.

Evidence (SITE_FAR fix pass; REFERENCES.md, cams/aerials.json, cams/p26.json): cameras 31 / 32 solved jointly on
the house row, the street and the neighbours' garages (2.4 / 1.9 px); 26 on the fence, the far shore, the riprap
and two far-row houses.  Plan positions come from back-projecting photo pixels onto the ground / water plane with
those cameras (tools/backproject.py, tools/orthophoto.py):
  shoreline   north, east and the south shore x -1..29 traced in 31 and 32 (agree to ~1 m); the south shore west of
              x -1 is under the tree belt in both aerials: from 26 (bias-corrected) and 29 at y 48-50 - INFERRED
  fountain    nozzle (-14.0, 94.9) +/- (0.6, 3.6) (31 + 32); plume 4.6-5.0 m, landing ring r ~ 4 m (31: 3.8, 32: 4.7)
  path        31 / 32 traces (y 33.7-33.8 behind our lot, 1.6-1.8 m wide); hidden under the belt for x -56..0
  trees       trunk bases from 26 (T1..T6, the birch clump), far-bank trees from 31's orthophoto (mulch rings, shadows),
              belt / east / west trees from the canopy masses in 31 / 32 and the allee seen in 29 - positions of trees
              hidden in canopy masses and all heights except 26's are INFERRED
  houses      far-row rear walls from 32 (x ranges +/- 0.4 m, y +/- 1 m, 8 houses), colours from 31 / 32; decks, fences,
              the sunroom from 31's top row; houses on the other streets are procedural (sitefar_suburb)
Levels (INFERRED): water -1.85, the lawn -0.42 at the rear lot line falling to a 5 m bank; far row base +0.3 (32)."""
import math
import random
from .plan import *
from archviz.mesh import MB, COLL
from archviz import trees as _tr
from archviz import materials as _m
from . import sitefar_houses as sh
from . import sitefar_suburb as sub

ZG = Z_GRADE
Z_WATER = -1.85
Z_LAWN = Z_GRADE - 0.02          # common lawn at the rear lot line (site_patio.z_lawn meets it there)
PATH_W = 1.8                     # 6 ft asphalt trail (31: 1.55-1.8 m)

# ---------------------------------------------------------------- the pond (water line, clockwise from the SE corner)
POND_PTS = [
    # south shore: x -1..33 traced (31 v 558-564, 32 v 741-742); west of x -1 inferred from 26 / 29 (under the belt)
    (35.5, 47.9), (33.5, 45.7), (29.3, 45.0), (25.8, 44.9), (18.4, 44.7), (13.4, 45.0), (7.1, 44.7), (1.0, 44.6), (-4.0, 45.1),
    (-10.1, 45.8), (-17.1, 46.5), (-24.2, 47.1), (-31.3, 47.6), (-38.3, 48.0), (-45.4, 48.7), (-51.4, 49.7), (-56.0, 51.6),
    (-59.3, 54.8), (-61.3, 59.2), (-61.9, 64.9),
    # west shore (32)
    (-61.6, 68.5), (-61.0, 72.1), (-60.6, 78.4), (-60.3, 85.1), (-59.5, 91.4), (-59.7, 98.1), (-60.7, 105.0), (-61.5, 111.3),
    (-61.9, 117.2), (-60.9, 122.0), (-58.7, 124.5),
    # north (far) shore (31 + 32)
    (-55.5, 125.3), (-49.4, 125.2), (-43.3, 125.3), (-37.7, 125.4), (-31.8, 124.8), (-26.4, 125.2), (-20.0, 126.2), (-12.0, 126.3),
    (-3.9, 126.4), (1.2, 127.7), (9.2, 128.3), (18.3, 128.4), (26.4, 128.5), (35.6, 128.6), (41.8, 128.1), (45.1, 126.2), (47.8, 123.0),
    (49.1, 120.1),
    # east shore with the lobe at y 55-75 (31 + 32)
    (48.2, 117.4), (46.6, 114.2), (45.1, 111.0), (42.9, 106.4), (40.7, 101.0), (38.9, 96.6), (37.9, 93.0), (37.5, 89.1), (37.7, 85.6),
    (38.1, 82.3), (38.7, 78.7), (39.4, 74.5), (40.3, 70.0), (41.1, 65.9), (41.5, 62.0), (41.4, 57.9), (40.2, 54.1), (38.2, 50.6),
]
FOUNTAIN = (-14.1, 92.1)
FOUNTAIN_H = 4.8                 # plume top above the water (31: 4.6, 32: 5.0)
FOUNTAIN_R = 4.0                 # landing ring radius (31: 3.8, 32: ~4.7 incl. the outer splash)


def _catmull_closed(pts, n=3):
    out = []
    m = len(pts)
    for i in range(m):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % m], pts[(i + 2) % m]
        for k in range(n):
            t = k / n
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t * t
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t ** 3) for j in (0, 1)))
    return out


POND_RING = _catmull_closed(POND_PTS, 3)
POND_BOX = (min(p[0] for p in POND_RING), max(p[0] for p in POND_RING), min(p[1] for p in POND_RING), max(p[1] for p in POND_RING))


def pond_dist(x, y):
    """Signed distance to the water line (negative on the water)."""
    best, inside = 1e9, False
    ring = POND_RING
    n = len(ring)
    for i in range(n):
        (ax, ay), (bx, by) = ring[i], ring[(i + 1) % n]
        if (ay > y) != (by > y) and x < (bx - ax) * (y - ay) / (by - ay + 1e-12) + ax:
            inside = not inside
        vx, vy = bx - ax, by - ay
        t = max(0.0, min(1.0, ((x - ax) * vx + (y - ay) * vy) / (vx * vx + vy * vy + 1e-12)))
        d = (x - ax - vx * t) ** 2 + (y - ay - vy * t) ** 2
        if d < best:
            best = d
    best = math.sqrt(best)
    return -best if inside else best


def _pond_dist_np(X, Y):
    import numpy as np
    ring = np.array(POND_RING)
    B = np.roll(ring, -1, axis=0)
    best = np.full(X.shape, np.inf)
    inside = np.zeros(X.shape, bool)
    for (ax, ay), (bx, by) in zip(ring, B):
        cross = ((ay > Y) != (by > Y)) & (X < (bx - ax) * (Y - ay) / (by - ay + 1e-12) + ax)
        inside ^= cross
        vx, vy = bx - ax, by - ay
        t = np.clip(((X - ax) * vx + (Y - ay) * vy) / (vx * vx + vy * vy + 1e-12), 0.0, 1.0)
        best = np.minimum(best, (X - ax - vx * t) ** 2 + (Y - ay - vy * t) ** 2)
    best = np.sqrt(best)
    return np.where(inside, -best, best)


# ---------------------------------------------------------------- grades
def _ss(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


BANK_W = 14.0                    # the lawn falls to the water over the last 14 m (26: a gentle slope, steeper at the edge)


def _bank(d, zb):
    """Ground height at distance d from the water line, blending into the lawn level zb at BANK_W; the bed below."""
    if d <= 0:
        return Z_WATER - 0.05 - min(1.4, -d * 0.25)
    t = min(1.0, d / BANK_W)
    return Z_WATER - 0.05 + (zb - Z_WATER + 0.05) * (1.0 - (1.0 - t) ** 2.2)


def _front():
    from . import site_front as sf
    return sf


def z_base(x, y):
    """Lawn level before the pond bank: the street strip follows site_front's grades; behind the houses -0.33 ->
    -0.42 (the common lawn); the north bank rises to +0.30 at the far row (32); gentle undulation far away."""
    r = math.hypot(x - sub.CENTRE[0], y - sub.CENTRE[1])
    fade = 1.0 - _ss((r - 500.0) / 1000.0)
    if y < 12.0:
        sf = _front()
        if y >= sf.CURB_Y:
            z = sf.grade(0.0, y)
        elif y >= sf.STREET[1]:
            z = sf.Z_ST
        elif y >= sf.FAR_SW[1] - 30.0:
            z = sf.Z_SW - 0.01
        else:
            z = sf.Z_SW - 0.01 + (Z_LAWN - sf.Z_SW + 0.01) * _ss((sf.FAR_SW[1] - 30.0 - y) / 20.0)
        if y > 0.0:
            z = z + (-0.33 - z) * _ss(y / 2.0)
    else:
        z = -0.33 + (Z_LAWN + 0.33) * _ss((y - 12.0) / 8.0)
    z += 0.72 * _ss((y - 135.0) / 33.0) * fade
    return z + sub.undulation(x, y)


def z_ground(x, y):
    z = z_base(x, y)
    if POND_BOX[0] - 20 < x < POND_BOX[1] + 20 and POND_BOX[2] - 20 < y < POND_BOX[3] + 20:
        d = pond_dist(x, y)
        if d < BANK_W:
            z = _bank(d, z)
    return z


# ---------------------------------------------------------------- the paths (centrelines; 31 / 32 traces, see notes)
PATHS = {
    # behind the lots: traced x 0.6..41 (31, 32), hidden under the belt for x -56..0 (a slight bow, 29 curves left), the
    # SW curve up the west bank (32)
    'south': [(41.5, 39.0), (33.3, 35.5), (26.1, 33.9), (20.4, 32.9), (14.7, 31.9), (11.4, 32.0), (7.3, 32.4), (0.6, 32.5), (-10.1, 32.4), (-16.0, 31.8),
              (-22.0, 30.7), (-28.0, 30.2), (-35.0, 30.7), (-46.4, 32.3), (-56.7, 33.3), (-61.0, 33.8), (-67.6, 35.8), (-72.9, 42.3), (-75.4, 50.6), (-75.5, 57.1)],
    'west': [(-75.5, 57.1), (-76.3, 66.1), (-77.5, 77.8), (-78.5, 92.4), (-79.0, 109.0), (-78.9, 124.5), (-77.1, 134.3), (-70.5, 139.4),
             (-61.0, 140.2)],
    'north': [(-61.0, 140.2), (-47.7, 139.9), (-34.3, 138.5), (-20.9, 137.9), (-10.0, 139.0), (-3.3, 140.7), (7.9, 143.5), (19.2, 144.0),
              (37.5, 144.2), (55.7, 144.2), (61.9, 143.8), (65.4, 142.8)],
    'east': [(65.4, 142.8), (65.4, 134.5), (65.1, 126.4), (62.4, 118.6), (58.8, 109.8), (56.6, 103.3), (53.5, 92.4), (52.9, 83.5),
             (53.8, 76.6), (55.8, 69.3), (56.2, 63.9), (53.2, 55.2), (47.1, 45.8), (41.5, 38.0)],
    # connectors to the streets (inferred where they leave the photos)
    'se': [(41.5, 38.0), (45.8, 38.3), (48.8, 35.7), (52.5, 30.4), (55.2, 23.1), (56.2, 15.2), (56.4, 11.8)],
    'n': [(65.4, 142.8), (67.4, 157.1), (67.6, 167.5), (67.7, 176.8)],
}


def _smooth(pts, n=4):
    return sub._smooth(pts, n)


# ---------------------------------------------------------------- riprap: rock-lined swales and boulder groups (31 / 32)
SWALES = [   # (polyline from the top of the bank to the water, width)
    ([(-37.9, 142.6), (-35.9, 136.7), (-33.4, 130.4), (-32.0, 125.9), (-31.5, 123.9)], 2.4),      # north swale (31 / 32)
    ([(42.0, 39.2), (40.4, 42.8), (38.8, 46.2), (37.8, 48.6)], 2.0),                               # SE inlet (31 lower right)
    ([(-77.7, 78.2), (-73.1, 75.4), (-67.6, 72.5), (-63.3, 70.2), (-61.7, 69.6)], 2.2),           # SW swale (32 west)
]
BOULDERS = [  # (x, y, radius of the group, count, pipe) at the water's edge
    (-26.5, 125.8, 2.7, 70, True),         # the headwall mound with its outlet pipe (31: rock pile with a dark opening)
    (44.8, 127.4, 2.9, 60, False),         # NE corner groups (31 / 32 'far R boulders')
    (48.3, 122.3, 2.6, 55, False),
    (38.5, 76.2, 1.9, 34, False),          # east shore pile (31 / 32 / 26)
    (-63.1, 97.8, 2.2, 36, False),        # west shore patch (32)
    (-31.5, 123.5, 2.4, 40, False),        # apron of the north swale
    (37.4, 48.9, 1.9, 26, False),          # apron of the SE inlet
    (-61.5, 69.1, 1.8, 24, False),         # apron of the SW swale
]

# ---------------------------------------------------------------- common-area trees
# (name, x, y, kind, height, spread, seed); kinds: locust, gold (Sunburst honey locust), maple, purple, ash, birch,
# columnar, amur, spruce
TREES = [
    # behind our lot (26 trunk bases back-projected at z -0.7 with p26; heights from 26's crowns)
    # sizes from 26 (crown top row and width at the trunk's depth): T2 u 40-560 top v 85; T4 u 590-830 top v 370; T3 / T5
    # ~ 80 px wide, top v 470; T6 u 940-1090 top v 450; the birch clump top v 335
    # T2 on 26's trunk ray (u 300) at the depth that keeps it out of 29's frame (it is behind-left of the 29 camera); crown
    # top v 80 -> 13 m.  T1 = 26's twin-stem trunk (u 115, base v 605) = 29's second right-hand trunk (u 925): the tie
    # that places the 29 camera (see cams_site.py)
    ("T2_Locust", -4.5, 29.3, 'locust', 11.8, 11.0, 11),
    ("T1_Locust", -14.4, 35.9, 'locust', 12.0, 10.0, 12),
    ("T3_Young", -0.5, 35.9, 'maple', 3.9, 2.5, 13),
    ("T4_Maple", 3.2, 33.8, 'maple', 6.3, 6.5, 14),
    ("T5_Young", 5.4, 35.9, 'maple', 3.9, 2.6, 15),
    ("T6_Ash", 12.2, 33.4, 'ash', 4.5, 4.5, 16),                # 26 ray x 31 base: just north of the path
    ("T7_Birch", 16.1, 34.0, 'birch', 8.3, 7.0, 17),             # the white-stemmed clump: 31 base at the path's edge, 26 azimuth
    ("T8_Maple", 20.4, 34.6, 'maple', 6.5, 5.0, 18),             # 31 crown centre at z 3.5
    ("T11_Shore", 26.0, 36.5, 'maple', 7.0, 5.0, 21),            # 31: the tree by the shore with its shadow on the lawn
    # the yellow 'Sunburst' honey locust stands in the second right neighbour's back yard: crown centre triangulated from
    # 30 + 31 + 32 at (29.4, 18.0, 8.7), top (31.3, 21.0, 11.9); crown ~12 m across (31: 260 px)
    ("T9_Sunburst", 29.8, 19.5, 'gold', 12.3, 12.0, 19),
    ("EG2", 45.0, 29.9, 'maple', 10.0, 9.0, 22),                 # 31 lower right: back yard behind the street row (crown at z 5.1)
    ("EG1", 48.2, 48.8, 'maple', 10.0, 9.0, 20),                 # 31: the dense tree by the SE inlet
    # the east bank (31 crown centres back-projected at crown height; the striped east lawn is open but for one young tree)
    ("EF", 44.8, 71.4, 'maple', 5.0, 3.5, 31),                   # young tree in its mulch ring (31, base)
    ("EP", 47.3, 84.4, 'purple', 10.0, 8.0, 41),                 # the purple-leaf maple
    ("EY", 57.3, 85.7, 'locust', 10.0, 9.0, 42),
    ("EA", 51.1, 106.1, 'ash', 13.0, 12.0, 43),                  # the big pale crown between the path and the pond
    ("EB3", 47.6, 96.0, 'maple', 10.0, 8.0, 44), ("EB5", 55.0, 120.0, 'ash', 11.0, 8.0, 45),       # fill of the dense bank (inferred)
    ("EB6", 60.0, 98.0, 'locust', 11.0, 8.5, 46), ("EB9", 64.0, 112.0, 'maple', 12.0, 9.0, 49),
    ("EC", 60.5, 143.6, 'maple', 11.0, 7.0, 47),                 # dark crown beyond the north path (31 top right)
    ("ES1", 65.9, 129.5, 'spruce', 11.0, 4.2, 48), ("ES2", 69.0, 126.7, 'spruce', 10.0, 3.8, 50),   # the two spruces east of the path
    # 31's right edge (crown centres at z 5): the mass by the SE inlet and in the street row's back yards, trees east of the
    # east path and at the NE corner of the north path
    ("EM1", 47.7, 54.1, 'maple', 10.0, 8.5, 51), ("EM2", 49.5, 43.5, 'ash', 11.0, 8.5, 52), ("EM3", 45.5, 33.5, 'maple', 9.0, 7.5, 53),
    ("EM4", 41.9, 25.0, 'maple', 9.5, 8.0, 54), ("EM5", 43.8, 20.2, 'locust', 10.0, 8.5, 55),
    ("EM6", 57.0, 72.0, 'maple', 9.0, 7.5, 56), ("EM7", 58.0, 64.5, 'ash', 10.0, 8.0, 57),
    ("NE1", 45.0, 133.0, 'ash', 8.0, 6.0, 58), ("NE2", 43.3, 136.7, 'maple', 7.0, 5.5, 59), ("NE3", 52.0, 147.5, 'maple', 9.0, 7.0, 60),
    ("NE4", 56.6, 151.6, 'locust', 9.0, 7.5, 83), ("NE5", 50.5, 121.5, 'locust', 9.0, 7.0, 84),
    ("EB10", 42.3, 86.2, 'ash', 9.0, 7.0, 85), ("EB11", 54.2, 101.7, 'maple', 11.0, 8.0, 86),
    # the far bank (31 orthophoto: base = mulch ring / southern tip); young round-headed trees along the far path (31: 3-4 m crowns), two big spruces
    ("F1", -52.1, 134.3, 'young', 6.5, 4.2, 61), ("F2", -39.4, 139.4, 'spruce', 13.0, 4.2, 62), ("F3", -26.7, 139.4, 'spruce', 12.0, 3.8, 63),
    ("F4", -37.5, 132.5, 'young', 7.5, 4.4, 64), ("F5", -30.3, 132.9, 'young', 6.0, 3.8, 65), ("F6", -20.7, 132.3, 'young', 6.0, 3.8, 66),
    ("F7", -18.0, 142.9, 'young', 7.0, 4.0, 67), ("F8", -13.0, 133.9, 'young', 6.0, 3.8, 68), ("F9", -10.3, 142.2, 'young', 6.5, 3.9, 69),
    ("F10", -8.4, 145.5, 'young', 7.0, 4.0, 70), ("F11", -3.8, 132.9, 'young', 6.0, 4.0, 71), ("F12", -1.4, 144.9, 'young', 7.0, 4.0, 72),
    ("F13", 3.2, 137.2, 'young', 8.0, 4.4, 73), ("F14", 9.3, 148.6, 'young', 7.0, 4.0, 74), ("F15", 11.4, 137.4, 'young', 6.5, 4.1, 75),
    ("F16", 17.5, 148.0, 'young', 7.5, 4.2, 76), ("F17", 26.3, 139.1, 'young', 7.0, 4.2, 77), ("F18", 36.6, 138.1, 'young', 6.0, 3.8, 78),
    ("F19", 46.9, 138.1, 'young', 8.0, 4.4, 79), ("F20", 61.0, 146.5, 'young', 7.5, 4.2, 80), ("F21", -56.5, 154.3, 'maple', 5.0, 3.5, 81),
    ("F22", -64.5, 147.9, 'young', 6.5, 4.0, 82),
    # the west bank (32: columnar / conical trees along the west path, a broad mass at the SW curve) - positions inferred
    ("W1", -92.7, 139.2, 'spruce', 11.0, 3.8, 91), ("W2", -83.7, 134.8, 'columnar', 9.0, 3.6, 92), ("W3", -86.2, 109.0, 'columnar', 9.5, 3.8, 93),
    ("W4", -82.2, 102.6, 'spruce', 10.0, 3.6, 94), ("W5", -83.2, 83.6, 'columnar', 9.0, 3.6, 95), ("W6", -90.3, 92.9, 'maple', 11.0, 8.0, 96),
    ("W7", -86.8, 68.5, 'ash', 11.5, 8.5, 97), ("W8", -94.3, 52.5, 'maple', 12.5, 10.0, 98), ("W9", -82.7, 47.1, 'locust', 13.0, 10.5, 99),
    ("W10", -69.6, 40.7, 'maple', 10.0, 8.0, 100), ("W11", -97.8, 120.7, 'columnar', 9.0, 3.6, 101), ("W12", -99.9, 77.8, 'maple', 10.5, 8.0, 102),
    # the back yards of the west row (32: a band of trees between the row and the west path) - INFERRED positions
    ("WY1", -99.0, 58.0, 'maple', 11.0, 9.0, 103), ("WY2", -101.0, 97.0, 'ash', 12.0, 9.0, 104), ("WY3", -98.5, 136.0, 'maple', 10.0, 8.0, 105),
    ("WY4", -100.5, 152.0, 'locust', 11.0, 9.0, 106), ("WY5", -93.0, 160.0, 'maple', 9.0, 7.0, 107), ("WY6", -101.5, 40.0, 'ash', 11.0, 8.5, 108),
    ("WY7", -95.5, 110.0, 'columnar', 9.0, 3.8, 109), ("WY8", -92.0, 66.0, 'young', 6.0, 4.0, 110),
]


def _belt_trees():
    """The belt behind the lots west of our house: an allee of low-forking, small-leaved honey locusts along the path
    (photo 29, trunk bases back-projected with p29: north row 2.4-4.7 m from the path, south row 3.3-5.5 m; they
    agree with 26's T1 / T2), continued west to the SW curve at the same spacing (31 / 32 show one closed canopy
    x -62..0 whose top edge fits ~9 m trees at y 29-39).  Positions west of x -15 are INFERRED."""
    rng = random.Random(404)
    out = []
    # measured in 29 (x, y): north row, south row
    # (29 shows twin / multi-stem trunks: readings closer than ~1.5 m are one tree)
    north = [(-10.9, 37.4, 8.5, 9.5), (-18.7, 35.0, 8.5, 9.0)]
    south = [(-11.4, 26.6, 9.0, 10.0), (-13.2, 29.0, 8.0, 8.5), (-15.6, 27.8, 8.5, 9.0)]
    for i, (x, y, hh, ss) in enumerate(north):
        out.append((f"AN{i}", x, y, 'locust', hh, ss, 500 + i))
    for i, (x, y, hh, ss) in enumerate(south):
        out.append((f"AS{i}", x, y, 'locust', hh, ss, 510 + i))
    x = -22.0
    i = 0
    while x > -60.0:
        py = _path_y(x)
        out.append((f"BN{i}", x + rng.uniform(-0.6, 0.6), py + rng.uniform(3.0, 4.8), 'locust', rng.uniform(8.0, 10.0), rng.uniform(8.0, 9.5),
                    520 + i))
        xs = x - rng.uniform(1.5, 2.5)
        out.append((f"BS{i}", xs, _path_y(xs) - rng.uniform(3.4, 5.2), 'locust', rng.uniform(8.0, 10.0), rng.uniform(8.0, 9.5), 560 + i))
        x -= rng.uniform(3.6, 4.8)
        i += 1
    out.append(("BSamara", -7.3, 35.6, 'samara', 6.0, 6.0, 600))
    # the SW corner: the belt reaches the water (32: canopy over the pond's SW corner, u 400-480 v 640-700)
    for i, (x, y, kind, h, w) in enumerate([(-50.0, 47.5, 'ash', 12.0, 10.0), (-57.5, 50.5, 'maple', 11.0, 9.0),
                                             (-63.5, 47.0, 'locust', 12.0, 10.0), (-44.0, 44.0, 'maple', 11.0, 9.0),
                                             (-66.0, 56.5, 'maple', 10.0, 8.0), (-38.0, 43.0, 'ash', 12.0, 9.5)]):
        out.append((f"SW{i}", x, y, kind, h, w, 610 + i))        # 29 right: the tree hung with red-brown seed clusters
    return out


_PATH_CACHE = {}


def _path_y(x):
    """y of the south path's centreline at x (for the belt)."""
    if 'south' not in _PATH_CACHE:
        _PATH_CACHE['south'] = sub._resample(_smooth(PATHS['south'], 4), 0.5)
    pts = _PATH_CACHE['south']
    best = min(pts, key=lambda p: abs(p[0] - x) + (0 if p[1] < 40 else 100))
    return best[1]


# ---------------------------------------------------------------- the far row across the pond (32: rear-wall x ranges)
# (name, x0, x1, rear wall y, siding, roof, style)
FAR_ROW = [
    ("H0", -95.8, -82.6, 162.6, 'cream', 'weathered', dict(deck='patio')),                        # inferred (west of 32's row)
    ("H1", -79.1, -65.7, 163.2, 'greyblue', 'weathered', dict(deck='patio', garage='R')),
    ("H2", -63.0, -48.1, 161.9, 'white', 'brown', dict(deck='wood', deck_f=0.2, garage='L')),
    ("H3", -45.8, -30.8, 162.8, 'white', 'weathered', dict(sunroom=True, garage='R')),
    ("H4", -20.4, -7.2, 162.4, 'white', 'charcoal', dict(deck='wood', deck_f=0.35, deck_w=5.0, garage='L')),   # dark roof (32: 100/96/81)
    ("H5", -2.9, 10.0, 163.2, 'cream', 'weathered', dict(deck='wood', deck_f=0.5, garage='R')),
    ("H6", 12.8, 25.8, 164.1, 'beige', 'weathered', dict(deck='red', deck_f=0.45, garage='L')),
    ("H7", 31.1, 43.9, 166.1, 'greige', 'weathered', dict(fence='black', yard=14.0, deck='patio', garage='R')),
    ("H8", 47.9, 61.5, 164.7, 'khaki', 'weathered', dict(fence='black', yard=11.0, deck='patio', garage='L')),
    ("H9", 70.9, 84.1, 165.0, 'tan', 'brown', dict(deck='wood')),                                  # inferred
]
FAR_ROW_D = 10.8                 # house depth (inferred)


# ================================================================ materials
def _mats(M):
    if 'sf_lawn' in M:
        return M
    M['sf_lawn'] = _m.turf("SF_LawnCommon", c_dark=(0.075, 0.09, 0.008, 1), c_light=(0.20, 0.23, 0.02, 1), stripes=True, stripe_axis='Y',
                           stripe_w=0.2)                       # mowing stripes (31 east lawn, 26)
    M['sf_bank'] = _m.noise_mat("SF_BankToe", (0.06, 0.07, 0.03, 1), (0.16, 0.15, 0.08, 1), scale=4, bump=0.4, rough=0.9)
    M['sf_grass'] = _m.grass_blade("SF_GrassBlade", root=(0.035, 0.08, 0.012, 1), tip=(0.26, 0.42, 0.06, 1), dry=(0.46, 0.44, 0.16, 1),
                                   stripes=False)
    M['sf_path'] = _m.noise_mat("SF_PathAsphalt", (0.14, 0.135, 0.13, 1), (0.28, 0.27, 0.26, 1), scale=30, bump=0.3, rough=0.85)   # 29: weathered, light grey
    M['sf_rock'] = _m.noise_mat("SF_Limestone", (0.25, 0.235, 0.21, 1), (0.50, 0.48, 0.44, 1), scale=5, bump=0.8, detail=5, rough=0.85)
    M['sf_pipe'] = _m.noise_mat("SF_PipeConcrete", (0.30, 0.29, 0.27, 1), (0.42, 0.41, 0.38, 1), scale=8, bump=0.2, rough=0.9)
    M['sf_hole'] = _m.new_mat("SF_PipeHole", (0.01, 0.01, 0.01, 1), rough=1.0)
    import bpy
    for legacy in ('PondWater', 'FountainFoam', 'FountainMist', 'FountainSpray'):      # house.py's first-pass materials: film_scene.py animates the
        old = bpy.data.materials.get(legacy)                           # materials by these names, so the context's take them over
        if old is not None:
            old.name = legacy + '_Legacy'
    M['sf_water'] = _water()
    M['sf_mist'] = _mist()
    M['sf_foam'] = _foam()
    M['sf_spray'] = _spray()
    M['sf_far'] = _m.noise_mat("SF_FarPlain", (0.045, 0.06, 0.025, 1), (0.17, 0.155, 0.11, 1), scale=0.03, bump=0.0, detail=8, rough=0.95)
    return M


def _mist():
    """A faint spray mist round the fountain (the photos show only a thin haze under the umbrella)."""
    import bpy
    m = bpy.data.materials.new("FountainMist")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_MATERIAL':
            nt.nodes.remove(n)
    out = nt.nodes['Material Output']
    vol = nt.nodes.new("ShaderNodeVolumePrincipled")
    vol.inputs["Density"].default_value = 0.03
    vol.inputs["Color"].default_value = (0.95, 0.97, 1.0, 1)
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    nt.links.new(out.inputs["Surface"], tr.outputs["BSDF"])
    nt.links.new(out.inputs["Volume"], vol.outputs["Volume"])
    return m


def _spray():
    """Fountain water: thin arcs broken into droplets by a stretched noise mask, translucent white with a faint glow;
    only ~40 % of each arc is opaque so the umbrella reads airy from 100 m (31 / 32).  The mask's mapping is driven by
    the frame in the film (film_scene.fountain), so droplets travel."""
    m = _m.new_mat("FountainSpray", (0.90, 0.93, 0.96, 1), rough=0.2, spec=0.5, ior=1.33)
    nt, b = m.node_tree, _m._bsdf(m)
    n = _m._noise(nt, _m._coords(nt, scale=(22.0, 22.0, 6.0)), scale=1.0, detail=2.0, rough=0.5)
    drop = _m._math(nt, 'GREATER_THAN', n, 0.56)
    tr = nt.nodes.new("ShaderNodeBsdfTranslucent"); tr.inputs["Color"].default_value = (0.95, 0.97, 1.0, 1)
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (0.95, 0.96, 1.0, 1); em.inputs["Strength"].default_value = 0.35
    mix1 = nt.nodes.new("ShaderNodeMixShader"); mix1.inputs["Fac"].default_value = 0.5
    nt.links.new(mix1.inputs[1], b.outputs["BSDF"]); nt.links.new(mix1.inputs[2], tr.outputs["BSDF"])
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(add.inputs[0], mix1.outputs["Shader"]); nt.links.new(add.inputs[1], em.outputs["Emission"])
    tp = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix2 = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(mix2.inputs["Fac"], _m._math(nt, 'MULTIPLY', drop, 0.6))
    nt.links.new(mix2.inputs[1], tp.outputs["BSDF"]); nt.links.new(mix2.inputs[2], add.outputs["Shader"])
    nt.links.new(nt.nodes["Material Output"].inputs["Surface"], mix2.outputs["Shader"])
    return m


def _foam():
    """Churned white water round the fountain: alpha-cut noise, dense in a ring at r ~2.5-4.5 m (object coordinates are
    centred on the nozzle), a thinner patch inside."""
    m = _m.new_mat("FountainFoam", (0.86, 0.89, 0.89, 1), rough=0.55)
    nt, b = m.node_tree, _m._bsdf(m)
    n = _m._noise(nt, _m._coords(nt, scale=(1.6, 1.6, 1.6)), scale=2.5, detail=6.0, rough=0.65, distortion=0.9)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(sep.inputs["Vector"], tc.outputs["Object"])
    comb = nt.nodes.new("ShaderNodeCombineXYZ"); nt.links.new(comb.inputs["X"], sep.outputs["X"]); nt.links.new(comb.inputs["Y"], sep.outputs["Y"])
    ln = nt.nodes.new("ShaderNodeVectorMath"); ln.operation = 'LENGTH'; nt.links.new(ln.inputs[0], comb.outputs["Vector"])
    r = ln.outputs["Value"]
    ring = _m._ramp(nt, _m._math(nt, 'DIVIDE', r, FOUNTAIN_R * 1.25, clamp=True),
                    [(0.0, (0.55, 0.55, 0.55, 1)), (0.3, (0.3, 0.3, 0.3, 1)), (0.55, (0.62, 0.62, 0.62, 1)), (0.75, (1.0, 1.0, 1.0, 1)),
                     (0.9, (0.6, 0.6, 0.6, 1)), (1.0, (0.0, 0.0, 0.0, 1))])
    sepc = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(sepc.inputs["Color"], ring)
    a = _m._math(nt, 'GREATER_THAN', _m._math(nt, 'MULTIPLY', _m._stretch(nt, n, 0.3, 0.7), sepc.outputs["Red"]), 0.42)
    tp = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(mix.inputs["Fac"], _m._math(nt, 'MULTIPLY', a, 0.92))
    nt.links.new(mix.inputs[1], tp.outputs["BSDF"]); nt.links.new(mix.inputs[2], b.outputs["BSDF"])
    nt.links.new(nt.nodes["Material Output"].inputs["Surface"], mix.outputs["Shader"])
    return m


def _water():
    """Retention-pond water (26, 30-32): a dark olive-teal body under a rippled surface (the sky and the far bank
    reflect at grazing angles in 26; from the drones it reads teal blue-grey, 31 sRGB ~ (83, 112, 111))."""
    m = _m.new_mat("PondWater", (0.035, 0.058, 0.04, 1), rough=0.2, spec=0.1, ior=1.333, coat=0.0)
    nt, b = m.node_tree, _m._bsdf(m)
    n = _m._noise(nt, _m._coords(nt, scale=(1.0, 2.2, 1.0)), scale=1.6, detail=5.0, rough=0.55)
    n2 = _m._noise(nt, _m._coords(nt), scale=9.0, detail=3.0)
    h = _m._math(nt, 'ADD', n, _m._math(nt, 'MULTIPLY', n2, 0.45))
    _m._bump(nt, b, h, 0.045, 0.04)
    return m


# ================================================================ ground
def _cells(mb, xs, ys, Z, keep, mi_of=None):
    nx, ny = len(xs), len(ys)
    base = len(mb.v)
    idx = {}
    for j in range(ny):
        for i in range(nx):
            idx[(i, j)] = None
    for j in range(ny - 1):
        for i in range(nx - 1):
            if not keep(i, j):
                continue
            q = []
            for (a, b_) in ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)):
                if idx[(a, b_)] is None:
                    idx[(a, b_)] = len(mb.v)
                    mb.v.append((xs[a], ys[b_], Z[b_][a]))
                q.append(idx[(a, b_)])
            mb.f.append(tuple(q)); mb.fm.append(mi_of(i, j) if mi_of else 0)
    return base


def ground(M):
    """Heightfields: near (1.25 m cells) round the pond block, mid (12 m) to ~1 km, far (60 m) to 3 km, then a flat
    hazed plain to 25 km.  SITE_NEAR's surfaces are left out (x +/- 60 for y < 12 and the rear-lot lawn)."""
    import numpy as np
    from . import site as st
    sf = _front()
    near_x = (-200.0, 170.0)
    near_y = (-80.0, 250.0)
    step = 1.25
    xs = list(np.arange(near_x[0], near_x[1] + 1e-6, step))
    ys = list(np.arange(near_y[0], near_y[1] + 1e-6, step))
    X, Y = np.meshgrid(np.array(xs), np.array(ys))
    Zb = np.vectorize(z_base)(X, Y)
    D = _pond_dist_np(X, Y)
    Z = np.where(D < BANK_W, np.vectorize(_bank)(D, Zb), Zb)
    # SITE_NEAR's front strip + rear lawn (their surfaces), and a margin where their lawn meets ours
    rear = (st.LOT_L - 2.0, 17.0, YB1 + 0.10, st.REAR_LOT)
    front_y0 = sf.FAR_SW[1] - 30.0

    def theirs(cx, cy):
        if -60.0 < cx < 60.0 and front_y0 < cy < 12.0:
            return True
        return rear[0] < cx < rear[1] and rear[2] < cy < rear[3]

    # the lawn seen close up in 29 (dense hair grass) and in 26 (sparser) get hair-grass emitters above the plain lawn
    near_box = (-26.0, 2.0, 25.5, 40.0)
    mid_box = (-45.0, 30.0, 28.5, 48.0)
    Dl = D.tolist()
    under = np.zeros(X.shape, bool)
    under |= (X > -60.0) & (X < 60.0) & (Y > front_y0) & (Y < 12.0)
    under |= (X > rear[0]) & (X < rear[1]) & (Y > rear[2]) & (Y < rear[3])
    lawn = MB()

    def cell_c(i, j):
        return (xs[i] + xs[i + 1]) / 2, (ys[j] + ys[j + 1]) / 2

    def inbox(b, cx, cy):
        return b[0] < cx < b[1] and b[2] < cy < b[3]

    in_boxes = np.zeros(X.shape, bool)
    for bb in (near_box, mid_box):
        in_boxes |= (X > bb[0]) & (X < bb[1]) & (Y > bb[2]) & (Y < bb[3])
    Zl = (Z - 0.05 * under - 0.03 * (in_boxes & ~under)).tolist()

    def mi(i, j):
        return 1 if -0.9 < Dl[j][i] < 0.9 else 0
    _cells(lawn, xs, ys, Zl, lambda i, j: True, mi)
    lawn.build("Lawn_Common", [M['sf_lawn'], M['sf_bank']], coll='Site', recalc=False)
    # hair-grass emitters on a 0.25 m grid that stops at the path edges and the water
    segs = []
    for pts in PATHS.values():
        c = sub._resample(_smooth(pts, 4), 0.8)
        segs += [(a_, b_) for a_, b_ in zip(c[:-1], c[1:])]
    for (name, bb) in (("Lawn_Common_Near", near_box), ("Lawn_Common_Mid", mid_box)):
        g = 0.25
        gx = list(np.arange(bb[0], bb[1] + 1e-6, g))
        gy = list(np.arange(bb[2], bb[3] + 1e-6, g))
        GX, GY = np.meshgrid(np.array(gx), np.array(gy))
        CX, CY = GX[:-1, :-1] + g / 2, GY[:-1, :-1] + g / 2
        PD = np.full(CX.shape, np.inf)
        for (ax, ay), (bx, by) in segs:
            if max(ax, bx) < bb[0] - 3 or min(ax, bx) > bb[1] + 3 or max(ay, by) < bb[2] - 3 or min(ay, by) > bb[3] + 3:
                continue
            vx, vy = bx - ax, by - ay
            t = np.clip(((CX - ax) * vx + (CY - ay) * vy) / (vx * vx + vy * vy + 1e-12), 0.0, 1.0)
            PD = np.minimum(PD, np.hypot(CX - ax - vx * t, CY - ay - vy * t))
        WD = _pond_dist_np(CX, CY)
        GZ = np.vectorize(z_ground)(GX, GY).tolist()
        ok = ((PD > PATH_W / 2 + 0.06) & (WD > 1.2)).tolist()
        other = near_box if bb is mid_box else None
        mb = MB()

        def keep(i, j, ok=ok, CX=CX, CY=CY, other=other):
            cx, cy = float(CX[j][i]), float(CY[j][i])
            if not ok[j][i] or theirs(cx, cy):
                return False
            return other is None or not inbox(other, cx, cy)
        _cells(mb, gx, gy, GZ, keep)
        mb.build(name, [M['sf_lawn']], coll='Site', recalc=False)
    # mid / far rings (drop 5 cm under the finer grid where they overlap)
    hz = dict(color=sub.HAZE['color'], dist=sub.HAZE['dist'], strength=sub.HAZE['strength'], max_fac=sub.HAZE['max_fac'])
    lawn_h = _tr.add_haze(M['sf_lawn'].copy(), hz['color'], dist=hz['dist'], strength=hz['strength'], max_fac=hz['max_fac'])
    lawn_h.name = "SF_LawnCommonHazed"
    for (name, rect, st_, hole) in (("Ground_Mid", (-1000.0, 1000.0, -900.0, 1100.0), 12.0, (near_x[0] + 6, near_x[1] - 6, near_y[0] + 6, near_y[1] - 6)),
                                    ("Ground_Far", (-3000.0, 3000.0, -2900.0, 3100.0), 60.0, (-1000.0 + 30, 1000.0 - 30, -900.0 + 30, 1100.0 - 30))):
        gx = list(np.arange(rect[0], rect[1] + 1e-6, st_))
        gy = list(np.arange(rect[2], rect[3] + 1e-6, st_))
        GZ = [[z_ground(x, y) - 0.05 for x in gx] for y in gy]
        mb = MB()

        def keep(i, j, gx=gx, gy=gy, hole=hole):
            cx, cy = (gx[i] + gx[i + 1]) / 2, (gy[j] + gy[j + 1]) / 2
            return not (hole[0] < cx < hole[1] and hole[2] < cy < hole[3])
        _cells(mb, gx, gy, GZ, keep)
        mb.build(name, [lawn_h], coll='Backdrop', recalc=False)
    # the plain to 25 km (flat; the far grid ends at the base level)
    plain = MB()
    zp = z_base(0.0, 3000.0) - 0.1
    R0x0, R0x1, R0y0, R0y1 = -2990.0, 2990.0, -2890.0, 3090.0
    R1 = 25000.0
    for q in (((-R1, -R1), (R1, -R1), (R1, R0y0), (-R1, R0y0)), ((-R1, R0y1), (R1, R0y1), (R1, R1), (-R1, R1)),
              ((-R1, R0y0), (R0x0, R0y0), (R0x0, R0y1), (-R1, R0y1)), ((R0x1, R0y0), (R1, R0y0), (R1, R0y1), (R0x1, R0y1))):
        plain.quad(*[(x, y, zp) for (x, y) in q])
    far_mat = _tr.add_haze(M['sf_far'], (0.44, 0.49, 0.54, 1), dist=7000.0, strength=0.6, max_fac=0.8)    # 32: horizon band (141, 154, 162)
    plain.build("Ground_Plain", [far_mat], coll='Backdrop')


def _grass(M):
    """Hair grass on the near common lawn (26 / 29), registered in the house's GRASS list at build time."""
    import sys
    H = sys.modules.get(__name__.rsplit('.', 1)[0] + '.house')
    if H is None or not hasattr(H, 'GRASS'):
        return
    keep = [g for g in H.GRASS if g.get('object') not in ('Lawn_Common_Near', 'Lawn_Common_Mid')]
    # (hair costs ~2 kB per rendered strand in Cycles: ~0.6 M strands dense round the 29 camera, ~0.35 M in 26's view)
    keep.append(dict(object="Lawn_Common_Near", mat=M['sf_grass'], count=52000, length=0.085, children=9, seed=21))
    keep.append(dict(object="Lawn_Common_Mid", mat=M['sf_grass'], count=34000, length=0.09, children=7, seed=22))
    H.GRASS[:] = keep


# ================================================================ pond, riprap, fountain, paths
def pond(M):
    w = MB()
    ring = POND_RING
    cx = sum(p[0] for p in ring) / len(ring)
    cy = sum(p[1] for p in ring) / len(ring)
    # the water plane runs 3 m under the bank; the terrain draws the water line
    big = []
    for (x, y) in ring:
        dx, dy = x - cx, y - cy
        L = math.hypot(dx, dy) or 1.0
        big.append((x + dx / L * 3.0, y + dy / L * 3.0))
    w.v.extend([(x, y, Z_WATER) for x, y in big] + [(cx, cy, Z_WATER)])
    n = len(big)
    for i in range(n):
        w.f.append((i, (i + 1) % n, n)); w.fm.append(0)
    ob = w.build("Pond", [M['sf_water']], coll='Site', recalc=False)
    ob.visible_shadow = False
    M['pond'] = M['sf_water']


def _rock(mb, x, y, z, r, rng, flat=0.6):
    mb.blob((x, y, z + r * flat * 0.35), r, seg=7, rings=4, jitter=0.45, seed=rng.randrange(99999), squash=flat,
            rx=rng.uniform(0.8, 1.25), ry=rng.uniform(0.8, 1.25))


def riprap(M):
    rng = random.Random(8)
    mb = MB()
    for (pts, wdt) in SWALES:
        path = sub._resample(_smooth(pts, 4), 0.35)
        for i, (x, y) in enumerate(path):
            (nx, ny), _ = sub._normal(path, i)
            for k in range(int(wdt / 0.32)):
                o = -wdt / 2 + (k + 0.5) * wdt / int(wdt / 0.32) + rng.uniform(-0.12, 0.12)
                px, py = x + nx * o, y + ny * o
                r = rng.uniform(0.16, 0.34) * (1.2 if abs(o) > wdt * 0.35 else 1.0)
                _rock(mb, px, py, max(z_ground(px, py), Z_WATER - 0.1) - 0.1, r, rng)
    pipe = MB()
    for (bx, by, R, cnt, has_pipe) in BOULDERS:
        for k in range(cnt):
            a = rng.uniform(0, 2 * math.pi)
            d = R * math.sqrt(rng.random())
            px, py = bx + d * math.cos(a), by + d * math.sin(a)
            r = rng.uniform(0.22, 0.55) * (1.0 - 0.35 * d / R)
            zc = max(z_ground(px, py), Z_WATER - 0.25)
            _rock(mb, px, py, zc - 0.12 + 0.35 * (1 - d / R) * (0.6 if has_pipe else 0.3), r, rng, flat=rng.uniform(0.5, 0.8))
        if has_pipe:
            # a concrete outlet pipe (r 0.52) poking out of the mound toward the water, its dark mouth
            zc = Z_WATER + 0.55
            ring = [(bx + 0.52 * math.cos(2 * math.pi * i / 18), zc + 0.52 * math.sin(2 * math.pi * i / 18)) for i in range(18)]
            for i in range(18):
                (x0_, z0_), (x1_, z1_) = ring[i], ring[(i + 1) % 18]
                pipe._add([(x0_, by - 1.3, z0_), (x1_, by - 1.3, z1_), (x1_, by + 0.8, z1_), (x0_, by + 0.8, z0_)], [(0, 1, 2, 3)], 0)
            h2 = MB()
            mouth = [(bx + 0.45 * math.cos(2 * math.pi * i / 18), by - 1.28, zc + 0.45 * math.sin(2 * math.pi * i / 18)) for i in range(18)]
            h2._add(mouth + [(bx, by - 1.28, zc)], [(i, (i + 1) % 18, 18) for i in range(18)], 0)
            h2.build("Riprap_PipeHole", [M['sf_hole']], coll='Site', recalc=False)
    mb.build("Riprap", [M['sf_rock']], coll='Site', smooth=True, auto_smooth=False, recalc=False)
    if pipe.f:
        pipe.build("Riprap_Pipe", [M['sf_pipe']], coll='Site', recalc=False)


def fountain(M):
    """The aerating fountain (31 / 32): a V-shaped central jet to ~4.8 m, an umbrella of thin arcs landing on a ring
    of r ~4 m (the photos' white splash ring), a churned foam ring and a low mist (animated by film_scene.py)."""
    fx, fy = FOUNTAIN
    zw = Z_WATER
    sp = MB()
    rng = random.Random(3)
    Hh, R = FOUNTAIN_H, FOUNTAIN_R
    for i in range(420):
        a = rng.uniform(0, 2 * math.pi)
        h = Hh * rng.uniform(0.62, 1.0)
        rr = R * rng.uniform(0.55, 1.1) * (0.6 + 0.4 * h / Hh)
        tilt = rng.uniform(-0.12, 0.12)
        ptsl = []
        for k2 in range(12):
            t = k2 / 11
            ptsl.append((fx + math.cos(a + tilt * t) * rr * t, fy + math.sin(a + tilt * t) * rr * t, zw + h * (4 * t * (1 - t)) + 0.02))
        sp.path_tube(ptsl, rng.uniform(0.0025, 0.0055), seg=4)
    for i in range(46):                                                       # the central V jet
        a = rng.uniform(0, 2 * math.pi); r0 = rng.uniform(0.0, 0.10)
        hh = Hh * rng.uniform(0.9, 1.08)
        spread = rng.uniform(0.25, 0.7)
        sp.path_tube([(fx + r0 * math.cos(a), fy + r0 * math.sin(a), zw), (fx + spread * 0.4 * math.cos(a), fy + spread * 0.4 * math.sin(a), zw + hh * 0.55),
                      (fx + spread * math.cos(a), fy + spread * math.sin(a), zw + hh)], rng.uniform(0.012, 0.028), seg=5)
    ob = sp.build("Fountain_Spray", [M['sf_spray']], coll='Site')
    ob["fountain"] = True
    # the splash ring (31: a bright ring of churned water r 2.5-4.5 m round the nozzle). Built about the object's own origin
    # at the nozzle: the foam shader fades with the distance from the object origin
    foam = MB()
    foam.lathe(0.0, 0.0, 0.0, [(0.0, 0.08), (1.2, 0.12), (2.6, 0.10), (R * 0.95, 0.07), (R * 1.25, 0.0)], seg=48)
    ob = foam.build("Fountain_Foam", [M['sf_foam']], coll='Site')
    ob.location = (fx, fy, zw - 0.02)
    mist = MB()
    mist.blob((0.0, 0.0, 0.0), R * 0.95, seg=20, rings=10, squash=0.62)
    ob = mist.build("Fountain_Mist", [M['sf_mist']], coll='Site')
    ob.location = (fx, fy, zw + 1.9)


def paths(M):
    p = MB()
    for key, pts in PATHS.items():
        c = sub._resample(_smooth(pts, 4), 0.8)
        L, R_ = [], []
        for i, (x, y) in enumerate(c):
            (nx, ny), _ = sub._normal(c, i)
            for sgn, arr in ((1, L), (-1, R_)):
                px, py = x + nx * PATH_W / 2 * sgn, y + ny * PATH_W / 2 * sgn
                arr.append((px, py, z_ground(px, py) + 0.035))
        base = len(p.v)
        n = len(c)
        p.v.extend(L + R_)
        # a thin slab edge: drop the outer vertices 5 cm (reads as the paving edge in 29)
        p.v.extend([(q[0], q[1], q[2] - 0.08) for q in L + R_])
        for i in range(n - 1):
            p.f.append((base + n + i, base + n + i + 1, base + i + 1, base + i)); p.fm.append(0)
            p.f.append((base + i, base + i + 1, base + 2 * n + i + 1, base + 2 * n + i)); p.fm.append(0)
            p.f.append((base + 3 * n + i + 1, base + n + i + 1, base + n + i, base + 3 * n + i)); p.fm.append(0)
    p.build("Path", [M['sf_path']], coll='Site', recalc=False)


# ================================================================ trees
_TM = {}


def _tree_mats():
    if _TM:
        return _TM
    card = _tr._oak_spray_card
    # leaf colours calibrated on 26 / 29 / 30 / 31 (sunlit foliage in the listing photos is olive-yellow, R ~ G >> B:
    # 29 canopy 158/164/90, 30 Sunburst 148/134/46, 31 belt 94/103/33); the first pass rendered 1.5-2 x too dark and blue
    _TM['locust'] = card("SF_LeafLocust", (0.213, 0.263, 0.037, 1), (0.388, 0.45, 0.075, 1), (0.65, 0.675, 0.15, 1), translucent=0.70, n=12,
                         a=0.075, b=0.032, rough=0.72)
    _TM['gold'] = card("SF_LeafSunburst", (0.45, 0.4, 0.025, 1), (0.725, 0.625, 0.05, 1), (0.95, 0.825, 0.125, 1), translucent=0.65, n=12,
                       a=0.075, b=0.034, rough=0.55)
    _TM['maple'] = card("SF_LeafMaple", (0.125, 0.181, 0.031, 1), (0.25, 0.325, 0.062, 1), (0.425, 0.5, 0.112, 1), translucent=0.60, n=5,
                        a=0.24, b=0.19, rough=0.7)
    _TM['purple'] = card("SF_LeafCrimson", (0.112, 0.027, 0.027, 1), (0.237, 0.062, 0.056, 1), (0.375, 0.112, 0.088, 1), translucent=0.50, n=5,
                         a=0.24, b=0.19, rough=0.55)
    _TM['ash'] = card("SF_LeafAsh", (0.15, 0.206, 0.037, 1), (0.275, 0.362, 0.069, 1), (0.463, 0.537, 0.112, 1), translucent=0.60, n=7,
                      a=0.14, b=0.055, rough=0.7)
    _TM['birch'] = card("SF_LeafBirch", (0.175, 0.237, 0.044, 1), (0.325, 0.413, 0.081, 1), (0.55, 0.6, 0.138, 1), translucent=0.70, n=6,
                        a=0.13, b=0.09, rough=0.65)
    _TM['columnar'] = card("SF_LeafColumnar", (0.1, 0.15, 0.025, 1), (0.2, 0.275, 0.05, 1), (0.35, 0.425, 0.088, 1), translucent=0.55, n=6,
                           a=0.20, b=0.12, rough=0.6)
    _TM['samara'] = card("SF_LeafSamara", (0.175, 0.225, 0.037, 1), (0.338, 0.4, 0.075, 1), (0.575, 0.325, 0.112, 1), translucent=0.65, n=10,
                         a=0.09, b=0.036, rough=0.5)
    _TM['amur'] = card("SF_LeafAmur", (0.125, 0.188, 0.037, 1), (0.25, 0.338, 0.069, 1), (0.525, 0.312, 0.112, 1), translucent=0.60, n=5,
                       a=0.20, b=0.15, rough=0.5)
    _TM['bark'] = _m.noise_mat("SF_Bark", (0.085, 0.07, 0.06, 1), (0.21, 0.18, 0.15, 1), scale=14, bump=1.0, spec=0.06, bump_dist=0.03)
    _TM['bark_birch'] = _m.noise_mat("SF_BarkBirch", (0.52, 0.50, 0.46, 1), (0.84, 0.83, 0.79, 1), scale=9, bump=0.4, spec=0.1)
    _TM['frond_blue'] = _tr._frond_card("SF_FrondBlueSpruce", (0.04, 0.08, 0.075, 1), (0.08, 0.14, 0.13, 1), (0.16, 0.22, 0.20, 1), 0.2)
    _TM['frond_dark'] = _tr._frond_card("SF_FrondSpruce", (0.02, 0.05, 0.03, 1), (0.04, 0.09, 0.05, 1), (0.08, 0.15, 0.08, 1), 0.15)
    _TM['core'] = _m.noise_mat("SF_CanopyCore", (0.07, 0.095, 0.018, 1), (0.16, 0.20, 0.04, 1), scale=3, rough=1.0, spec=0.02, bump=0.0)
    _TM['core_holey'] = _tr._holey(_TM['core'], "SF_CanopyCoreHoley", 0.6, 4.0)
    return _TM


VIEW_CAMS = [(5.74, 13.9), (-3.9, 32.5)]       # p26, p29: trees near these get more detail


def _build_tree(nm, x, y, z, kind, h, s, seed, detail, tm, card=None):
    import functools
    from . import sitefar_trees as st
    bl = functools.partial(st.broadleaf, card=card) if card else st.broadleaf
    rng = random.Random(seed)
    mats = {'bark': tm['bark'], 'leaf': tm.get(kind, tm['maple'] if kind != 'young' else tm['columnar'])}
    if detail < 0.45:
        mats['core'] = tm['core']
    if kind == 'spruce':
        _tr.conifer(nm, (x, y, z), height=h, r=s * 0.5, seed=seed, detail=max(0.3, detail), kind='pine', coll='Landscape',
                    mats={'bark': tm['bark'], 'leaf': tm['frond_dark']})
        return
    if kind == 'birch':
        mats['bark'] = tm['bark_birch']
        bl(nm, (x, y, z), h, s, seed, mats, detail, form='open', stems=4, fork=0.62, trunk_r=0.075)
        return
    if kind == 'columnar':
        bl(nm, (x, y, z), h, s, seed, mats, detail, form='column', fork=0.12, card=0.26)
        return
    if kind in ('locust', 'gold', 'samara'):
        if kind == 'samara':                           # 29 right: a bushy low-crowned tree hung with seed clusters
            bl(nm, (x, y, z), h, s, seed, mats, detail, form='dome', fork=0.15, cov=1.0)
        elif h < 10.5:                                 # the allee trees: low-forking multi-stem (29)
            bl(nm, (x, y, z), h, s, seed, mats, detail, form='multistem', stems=rng.choice((2, 2, 3)), fork=0.26,
                         cov=0.95 if detail >= 0.9 else 0.8)
        else:                                          # the big dome (26)
            bl(nm, (x, y, z), h, s, seed, mats, detail, form='dome', fork=0.2, lean=0.05, cov=1.1)
        return
    form = {'ash': 'oval', 'purple': 'round', 'amur': 'multistem', 'young': 'oval'}.get(kind, 'round')
    bl(nm, (x, y, z), h, s, seed, mats, detail, form=form, fork=0.28 if form != 'multistem' else 0.18,
                 stems=1 if form != 'multistem' else 3)


def _fit(prefix, base, h, s):
    """Scale the objects of one tree about its trunk base so its crown is `h` tall and `s` wide (the generator's
    height / spread are nominal)."""
    import bpy
    obs = [o for o in bpy.data.objects if o.name == prefix or o.name.startswith(prefix + "_")]
    if not obs:
        return
    zs, xs, ys = [], [], []
    for o in obs:
        if o.type != 'MESH' or not len(o.data.vertices):
            continue
        import numpy as np
        co = np.empty(len(o.data.vertices) * 3)
        o.data.vertices.foreach_get('co', co)
        co = co.reshape(-1, 3)
        zs.append(co[:, 2].max())
        if o.name.endswith('_Leaves'):
            xs.append((co[:, 0].min(), co[:, 0].max())); ys.append((co[:, 1].min(), co[:, 1].max()))
    if not zs:
        return
    top = max(zs) - base[2]
    if xs:
        w = 0.5 * ((max(b for _, b in xs) - min(a for a, _ in xs)) + (max(b for _, b in ys) - min(a for a, _ in ys)))
    else:
        w = s
    sz = max(0.5, min(2.0, h / max(0.5, top)))
    sxy = max(0.5, min(2.0, s / max(0.5, w)))
    for o in obs:
        o.scale = (sxy, sxy, sz)
        o.location = (base[0] * (1 - sxy), base[1] * (1 - sxy), base[2] * (1 - sz))


def plant(name, x, y, kind, h, s, seed, detail=None, fit=True):
    """One common-area tree at its trunk base (x, y), `h` tall and `s` wide (fitted after building)."""
    tm = _tree_mats()
    z = z_ground(x, y)
    if detail is None:
        dmin = min(math.hypot(x - cx, y - cy) for cx, cy in VIEW_CAMS)
        detail = 1.0 if dmin < 24 else (0.7 if dmin < 45 else (0.48 if dmin < 90 else 0.3))
    nm = "Land_SF_" + name
    dmin = min(math.hypot(x - cx, y - cy) for cx, cy in VIEW_CAMS)
    card = max(0.17, min(0.34, 0.011 * dmin)) if dmin < 30 else None      # leaf-spray size by distance to the photo cameras
    _build_tree(nm, x, y, z, kind, h, s, seed, detail, tm, card=card)
    if fit and kind != 'spruce':
        _fit(nm, (x, y, z), h, s)


def trees(M):
    for (name, x, y, kind, h, s, seed) in TREES + _belt_trees():
        plant(name, x, y, kind, h, s, seed)


# ================================================================ houses across the pond
def far_row(M):
    kit = sh.Kit(M, haze=sub.HAZE)
    for (name, x0, x1, yr, sid, roof, st) in FAR_ROW:
        W = x1 - x0
        cx = (x0 + x1) / 2
        style = dict(st)
        # the fronts face the street to the north (heading pi); the rear walls face the pond at y = yr
        f = style.pop('deck_f', None)
        if f is not None:
            style['slider_f'] = 1.0 - f
        cy = yr + FAR_ROW_D
        z0 = z_ground(cx, yr) + 0.3
        sh.house(kit, cx, cy, math.pi, z0, W=W, D=FAR_ROW_D, siding=sid, roof=roof, seed=sum(ord(c) for c in name) * 7, style=style)
    kit.build("SF_FarRow", 'Neighbours')


def _excluded(x, y):
    """Where context.py / site.py build explicitly: the pond block interior (common area, the rows round it)."""
    if -60.0 < x < 60.0 and -58.0 < y < 34.0:
        return True                               # SITE_NEAR's street row + our lot / neighbours
    if -104.0 < x < 76.0 and 20.0 < y < 186.0:
        return True                               # the common area, pond and far row
    return False


def build(M):
    _mats(M)
    ground(M)
    _grass(M)
    pond(M)
    riprap(M)
    fountain(M)
    paths(M)
    trees(M)
    far_row(M)
    from . import site_front as sf
    yc = (sf.STREET[0] + sf.STREET[1]) / 2
    sub.build(M, z_ground, _excluded, yc, M['sf_lawn'])
    COLL.pop('SF_Tmp', None)
