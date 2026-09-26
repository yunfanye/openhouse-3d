"""Main-floor front rooms (photos 04-07, 24): the foyer, living room, hall, powder room and finished garage, and the
U-shaped stair (both flights, landing, skirts, balustrades) - floors, staging, fixtures and fill lights.

Split out of interior_main.py (partitions, skins, doors and paint stay there).  The furniture / textile / art kit is
front_staging.py.  Staging follows the listing photos (the real pieces' shapes, sizes and materials); positions are
read from photos 04-06 relative to the walls and are labelled 'staging' in REFERENCES.md.

Photo evidence used here (details and pixel measurements: REFERENCES.md):
  04  foyer + living front wall: entry rug, swag valances (two scarf swags with lace hems, three jabots) over
      embroidered floor-length sheers on a fleur-de-lis rod, two framed parchment prints flanking the window, slipper
      chairs + octagonal repousse table + hammered vase, the sofa's south arm, the oval cocktail table, a ceiling
      register over the bay, the carpet / hardwood line at the end of the door wall.
  05  the hall end (dracaena, runner), peace lily on a blackwood stand, demilune console + embossed mirror, the flush
      dome light, the bar cart under the lower flight, the red abstract on the landing-enclosure wall, the lamp.
  06  the stair (carpeted treads AND risers with bullnoses, white skirts, turned oak balusters two per tread, a turned
      newel with a ball cap), the diagonal carpet edge from the newel base toward the foyer, the sofa under 'Irises'.
  07  powder room: maple vanity (two false drawers, two square raised-panel doors), cultured-marble top with splashes,
      frameless mirror, a four-light bar (two shades up, two down), towel bar, switch plate, towel ring.
  24  garage: open sectional door on its tracks, opener + rail, wall shelf with boxes, carts, freezer, mower, fans ...
"""
import math
import os
import random

from .plan import *
from archviz.mesh import MB
from archviz.lights import add_light, area_light
from archviz.cladding import Face
from . import interior_main as _im
from .interior_main import LC, ZC, WARM, HALL_X, PW, FRUIT_X0, XR, frame_art
from . import front_staging as fs
from archviz import phototex as ptx

PHOTOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'photos')

# ---------------------------------------------------------------- flat art rectified from the listing photos
# key -> (photo, quad TL, TR, BR, BL in photo pixels = the picture inside its frame, output size w x h, opts).
# Each painting is taken from the photo where it is largest and most front-on; the frames stay geometry (sizes and
# positions below come from back-projecting the same corners through INT_CAM's solved cameras onto the wall planes).
# gain / sat: the photo already carries its lighting; matched so the re-lit canvas reads like the photo (04-06 patches).
PHOTO_TEX = {
    'abstract_05': ('05', [(1220, 341), (1394, 326), (1393, 440), (1221, 446)], (360, 290), {'gain': 0.95, 'sat': 1.12}),     # red/orange 'fruit' abstract
    'irises_06':   ('06', [(910.6, 371), (990, 368), (990.6, 434), (911, 438)], (240, 200), {'gain': 0.78, 'sat': 1.2}),       # 'Irises' over the sofa
    'print_e_04':  ('04', [(96.3, 338.8), (160.8, 338.3), (162.8, 414.5), (98.7, 415)], (180, 205), {'gain': 0.9}),   # left of the window
    'print_w_04':  ('04', [(711, 342), (776.6, 341), (777.4, 442), (712, 443)], (160, 245), {'gain': 0.97, 'sat': 1.05}),     # right of the window
}


def photo_tex(key, rough=0.6, coat=0.0):
    ph, quad, size, opt = PHOTO_TEX[key]
    img = ptx.rectify(os.path.join(PHOTOS, f"{ph}.jpg"), quad, size, f"PhotoTex_{key}", gain=opt.get('gain', 1.0),
                      flatten=opt.get('flatten', 0.0), saturation=opt.get('sat', 1.0))
    return ptx.photo_material(f"Photo_{key}", img, rough=rough, coat=coat)


def photo_art(M, name, key, along, a0, a1, b, s, z0, z1, frame_mat, fw, rough=0.6, coat=0.0):
    """Framed flat art: frame_art's moulded frame (geometry) + the rectified photo texture on a UV quad filling the frame
    opening, set 1.45 cm off the wall (behind the frame's face, in front of its backing)."""
    mb = MB()
    frame_art(mb, along, a0, a1, b, s, z0, z1, mi_frame=0, mi_art=0, fw=fw)
    mb.build(f"{name}_Frame", [M[frame_mat]])
    corners = ptx.rect_corners(along, a0 + fw, a1 - fw, b + s * 0.0145, z0 + fw, z1 - fw, s)
    return ptx.uv_quad_mesh(f"{name}_Picture", corners, photo_tex(key, rough=rough, coat=coat), coll='House')

# ---------------------------------------------------------------- front-room lines (see the docstring / notes)
FOYER_WX = getattr(_im, 'FOYER_WX', 7.15)     # foyer west wall face (photo 04: the casing is 3 cm from that corner)
DOOR_Y = PORCH[3] + BWT                        # 1.75: inner face of the entry-door wall
WALL_END_X = BAY[0] + BWT                     # end of the door wall = the bay's west return (photo 04: x 8.945; 04-06 joint 8.92)
CARPET_CORNER = (WALL_END_X + 0.15, ST_Y0 - 0.50)   # the carpet edge turns here toward the newel base (06: (9.06, yf - 0.67))
KNEE = 0.12                                    # knee wall between the flights: y ST_YM .. ST_YM + KNEE
LIV_Y0 = BAY[2] + BWT                          # living-room front (window) wall face (1.11 with Y_BAY 0.86)
HALL_END = GAR[3] + IWT                        # the hall opens into the great room here (6.47)
SOFA = (XR - 0.50, ST_Y0 - 1.77)               # the sofa's centre (05/06 through INT_CAM's cameras: centred under 'Irises',
                                               # 1.77 m in front of the landing-enclosure wall, the lamp table in that corner)
COAT_Y1_ = ROOMS['foyer'][3] if 'foyer' in ROOMS else getattr(_im, 'COAT_Y1', 3.85)   # foyer's N end = the closet's north wall
                                               # (the convex corner in photo 05; 04-06 joint 4.38)
COAT_ = getattr(_im, 'COAT', dict(y0=2.15, y1=2.91))


def _mat(M, key, fallback):
    return M[key] if key in M else M[fallback]


# ================================================================ floors
def floors_front(M):
    """Foyer / stair foot / hall / powder: the laminate of the hall and kitchen; the living room: cut-pile carpet
    whose edge runs along the door wall's end and then diagonally to the newel base (photos 04, 05, 06), with a
    flush wood reducer along the edge."""
    lam, car, red = MB(), MB(), MB()
    zt = Z_MAIN
    cx, cy = CARPET_CORNER
    # laminate: everything west of the carpet line (a polygon), the stair foot, the hall, the powder room
    lam.prism([(HALL_X[0], DOOR_Y), (WALL_END_X, DOOR_Y), (cx, cy), (ST_X0 + 0.02, ST_Y0), (ST_X0 + 0.02, ST_YM), (HALL_X[0], ST_YM)], zt - 0.02, zt)
    lam.box(HALL_X[0], HALL_X[1], ST_YM, 6.47, zt - 0.02, zt)
    lam.box(PW['x0'], PW['x1'], PW['y0'], PW['y1'], zt - 0.02, zt)
    lam.build("Floor_Laminate_Front", [M['laminate']])
    # carpet: the bay + the living room east of the line
    car.prism([(WALL_END_X, LIV_Y0), (XR, LIV_Y0), (XR, ST_Y0), (ST_X0 + 0.02, ST_Y0), (cx, cy), (WALL_END_X, DOOR_Y)], zt - 0.02, zt + 0.012)
    car.build("Floor_Carpet_Living", [_mat(M, 'fs_carpet', 'carpet')])
    # reducer strip along the edge (6 cm, rounded top)
    for (a, b) in (((WALL_END_X, DOOR_Y), (cx, cy)), ((cx, cy), (ST_X0 + 0.02, ST_Y0))):
        (ax, ay), (bx, by) = a, b
        L = math.hypot(bx - ax, by - ay); nx, ny = -(by - ay) / L, (bx - ax) / L
        w = 0.03
        red.hexa([(ax - nx * w, ay - ny * w, zt), (bx - nx * w, by - ny * w, zt), (bx + nx * w, by + ny * w, zt), (ax + nx * w, ay + ny * w, zt),
                  (ax - nx * w, ay - ny * w, zt + 0.006), (bx - nx * w, by - ny * w, zt + 0.006), (bx + nx * w, by + ny * w, zt + 0.012),
                  (ax + nx * w, ay + ny * w, zt + 0.012)])
    red.build("Floor_Reducer_Front", [M['laminate']])


# ================================================================ the stair
def stair(M):
    """U stair, 14 risers: 6 treads + the half landing (7R) against the right wall + 6 treads back toward -X.  Photo 06:
    treads AND risers are carpeted, bullnosed; a white skirt on both sides of the lower flight; oak shoe rail, turned
    colonial balusters (two per tread), a rounded oak handrail; a turned oak newel with a ball cap at the foot; the
    lower rail dies into the landing-enclosure wall with a rosette; the upper flight's balustrade stands on the white
    fascia of the knee wall."""
    R, T = RISE, TREAD
    car, oak, white, oakh = MB(), MB(), MB(), MB()
    yl0, yl1 = ST_Y0 + 0.05, ST_YM - 0.03            # lower flight (between the open-side stringer and the wall skirt)
    yu0, yu1 = ST_YM + KNEE, ST_Y1                    # upper flight
    for i in range(1, 7):                             # lower flight rises toward +X
        x0 = ST_X0 + (i - 1) * T
        car.box(x0, ST_LAND, yl0, yl1, (i - 1) * R, i * R - 0.004)
        car.rbox(x0 - 0.032, x0 + 0.04, yl0, yl1, i * R - 0.042, i * R, r=0.018, seg=3)            # bullnose
    car.box(ST_LAND, XR, ST_Y0 + 0.12, ST_Y1, 0.0, Z_LAND - 0.004)                              # landing
    car.rbox(ST_LAND - 0.032, ST_LAND + 0.04, ST_Y0 + 0.12, ST_Y1, Z_LAND - 0.042, Z_LAND, r=0.018, seg=3)
    for j in range(8, 14):                            # upper flight rises toward -X from the landing
        k = j - 7
        x1 = ST_LAND - (k - 1) * T
        car.box(ST_X0, x1, yu0, yu1, Z_LAND, j * R - 0.004)
        car.rbox(x1 - 0.04, x1 + 0.032, yu0, yu1, j * R - 0.042, j * R, r=0.018, seg=3)
    car.build("Stair_Treads", [_mat(M, 'fs_carpet', 'carpet')], smooth=True)

    def sloped(mb, xa, xb, y0, y1, za, zb, h, mi=0):
        mb.hexa([(xa, y0, za), (xb, y0, zb), (xb, y1, zb), (xa, y1, za),
                 (xa, y0, za + h), (xb, y0, zb + h), (xb, y1, zb + h), (xa, y1, za + h)], mi)
    xa, xb = ST_X0 + 0.085, FRUIT_X0                  # the open-side stringer starts behind the newel (photo 06)
    zb = (xb - ST_X0) / T * R
    # open-side stringer (white fascia over the pony wall) + the wall-side skirt of the lower flight
    za = (xa - ST_X0) / T * R
    sloped(white, xa, xb, ST_Y0 - 0.025, ST_Y0 + 0.05, za + R - 0.06, zb + R - 0.06, 0.28)
    sloped(white, ST_X0 - 0.02, ST_LAND, ST_YM - 0.03, ST_YM - 0.005, R + 0.04, (ST_LAND - ST_X0) / T * R + R + 0.04, 0.24)
    white.box(ST_X0 - 0.02, ST_X0 + 0.05, ST_YM - 0.03, ST_YM - 0.005, 0.0, R + 0.28)              # skirt's plumb end at the floor
    pony = MB()
    pony.hexa([(ST_X0, ST_Y0, 0.0), (FRUIT_X0, ST_Y0, 0.0), (FRUIT_X0, ST_Y0 + 0.05, 0.0), (ST_X0, ST_Y0 + 0.05, 0.0),
               (ST_X0, ST_Y0, R - 0.06), (FRUIT_X0, ST_Y0, zb + R - 0.06), (FRUIT_X0, ST_Y0 + 0.05, zb + R - 0.06), (ST_X0, ST_Y0 + 0.05, R - 0.06)])
    pony.build("Stair_PonyWall", [M['paint_blue']])
    base = MB()
    base.box(ST_X0 + 0.05, FRUIT_X0, ST_Y0 - 0.014, ST_Y0, 0.0, 0.095)
    base.build("Stair_PonyBase", [M['trim_int']])
    # shoe rail, balusters, rounded handrail, newel
    rail_h = 0.88
    sloped(oakh, xa, xb, ST_Y0 - 0.02, ST_Y0 + 0.045, za + R + 0.22, zb + R + 0.22, 0.035)
    n_bal = int((xb - ST_X0) / (T / 2))
    for i in range(n_bal):
        x = ST_X0 + 0.16 + i * T / 2
        if x > xb - 0.06:
            break
        z0 = (x - ST_X0) / T * R + R + 0.255
        z1 = (x - ST_X0) / T * R + R + rail_h - 0.035
        _baluster(oak, x, ST_Y0 + 0.012, z0, z1)
    _rail(oakh, (ST_X0 + 0.07, ST_Y0 + 0.012, R + rail_h + 0.07 / T * R), (xb, ST_Y0 + 0.012, zb + R + rail_h))
    _rosette(oakh, xb, ST_Y0 + 0.012, zb + R + rail_h - 0.02)
    _newel(oak, ST_X0 + 0.04, ST_Y0 + 0.012, 0.0, 1.22)
    # knee wall under the upper flight + its fascia; the upper balustrade on it
    kz = lambda x: Z_LAND + (ST_LAND - x) / T * R
    knee = MB()
    # (its top rises to the upper flight's skirt so no gap opens under the fascia)
    kt = lambda x: kz(x) + R - 0.03
    ya_, yb_ = ST_YM, ST_YM + KNEE
    knee.hexa([(ST_X0, ya_, 0.0), (ST_LAND, ya_, 0.0), (ST_LAND, yb_, 0.0), (ST_X0, yb_, 0.0),
               (ST_X0, ya_, kt(ST_X0)), (ST_LAND, ya_, kt(ST_LAND)), (ST_LAND, yb_, kt(ST_LAND)), (ST_X0, yb_, kt(ST_X0))])
    knee.build("Stair_KneeWall", [M['paint_blue']])
    # photo 06 (through INT_CAM's p06, on the balustrade plane y 5.88): the white fascia's top - where the upper balusters
    # start - is 0.18 above the nosing line (z 2.44 at x 10.40, 2.05 at 10.92). (INT_CAM's newer p15 would put the shoe AT
    # the nosing line; that camera is 0.37 m off in y for this near field - see notes - so 06 rules here.) The rail enters
    # the landing newel's square block (06: block centre z 2.26, ball top 2.53) -> ~0.78 above the nosings (15: ~0.81).
    rail_u = 0.78
    sk2 = MB()
    sloped(sk2, ST_LAND + 0.03, ST_X0, ST_YM - 0.03, ST_YM + 0.05, kz(ST_LAND) - 0.05 + R, kz(ST_X0) - 0.05 + R, 0.24)
    sk2.build("Stair_UpperSkirt", [M['trim_int']])
    sloped(oakh, ST_LAND, ST_X0, ST_YM - 0.02, ST_YM + 0.045, kz(ST_LAND) + R + 0.19, kz(ST_X0) + R + 0.19, 0.035)
    for i in range(int((ST_LAND - ST_X0) / (T / 2))):
        x = ST_LAND - 0.13 - i * T / 2
        if x < ST_X0 + 0.05:
            break
        _baluster(oak, x, ST_YM + 0.012, kz(x) + R + 0.225, kz(x) + R + rail_u - 0.035)
    _rail(oakh, (ST_LAND - 0.07, ST_YM + 0.012, kz(ST_LAND - 0.07) + R + rail_u), (ST_X0, ST_YM + 0.012, kz(ST_X0) + R + rail_u))
    _newel(oak, ST_LAND - 0.04, ST_YM + 0.012, Z_LAND - 0.25, Z_LAND + 1.20)                        # landing newel (06: ball top z 2.53, 15: ~2.45)
    # (no rail across the landing edge: that edge is the lower flight's top riser - photo 06 shows the plant there)
    oak.build("Stair_Balusters", [M['oak_stair']], smooth=True)
    oakh.build("Stair_Rails", [M['oak_stair_h']], smooth=True)
    white.build("Stair_Skirt", [M['trim_int']])


def _baluster(mb, x, y, z0, z1):
    """Turned colonial baluster: square blocks at top and bottom, a vase + ring + tapered stem between."""
    h = z1 - z0
    s = 0.034
    mb.box(x - s / 2, x + s / 2, y - s / 2, y + s / 2, z0, z0 + 0.13)
    mb.box(x - s / 2, x + s / 2, y - s / 2, y + s / 2, z1 - 0.09, z1)
    L = h - 0.22
    prof = [(0.0155, 0.0), (0.011, 0.012), (0.017, 0.03), (0.019, 0.07), (0.016, 0.12), (0.011, 0.17), (0.013, 0.19), (0.009, 0.21),
            (0.0085, L * 0.75), (0.011, L * 0.86), (0.009, L * 0.92), (0.013, L * 0.97), (0.0155, L)]
    mb.lathe(x, y, z0 + 0.13, prof, seg=12)


def _newel(mb, x, y, z0, z1):
    """Turned oak newel (photo 06): square base block, a turned vase shaft, a square upper block where the rail
    enters, a collar and a ball cap."""
    s = 0.082
    mb.box(x - s / 2, x + s / 2, y - s / 2, y + s / 2, z0, z0 + 0.30)
    mb.box(x - s / 2 - 0.006, x + s / 2 + 0.006, y - s / 2 - 0.006, y + s / 2 + 0.006, z0, z0 + 0.06)
    zs = z0 + 0.30
    L = (z1 - 0.34) - zs
    mb.lathe(x, y, zs, [(0.036, 0.0), (0.026, 0.02), (0.034, 0.05), (0.030, 0.08), (0.025, L * 0.35), (0.030, L * 0.55), (0.034, L * 0.62),
                        (0.026, L * 0.75), (0.022, L * 0.9), (0.032, L * 0.96), (0.036, L)], seg=16)
    zu = z1 - 0.34
    mb.box(x - s / 2, x + s / 2, y - s / 2, y + s / 2, zu, zu + 0.17)
    mb.box(x - s / 2 - 0.008, x + s / 2 + 0.008, y - s / 2 - 0.008, y + s / 2 + 0.008, zu + 0.17, zu + 0.19)
    mb.lathe(x, y, zu + 0.19, [(0.0, 0.0), (0.03, 0.0), (0.022, 0.025), (0.027, 0.04), (0.045, 0.075), (0.047, 0.10), (0.04, 0.13), (0.02, 0.148),
                               (0.0, 0.152)], seg=20)


def _rail(mb, p0, p1, w=0.058, h=0.052):
    """Colonial handrail between two centre-top points: a rounded mushroom profile swept along the segment."""
    from mathutils import Vector
    a, b = Vector(p0), Vector(p1)
    d = (b - a).normalized()
    side = d.cross(Vector((0, 0, 1))).normalized()
    up = side.cross(d).normalized()
    prof = [(-w / 2, -h), (-w / 2, -h * 0.55), (-w * 0.46, -h * 0.35), (-w * 0.36, -h * 0.12), (-w * 0.2, 0.0), (w * 0.2, 0.0), (w * 0.36, -h * 0.12),
            (w * 0.46, -h * 0.35), (w / 2, -h * 0.55), (w / 2, -h)]
    secs = []
    for c in (a, b):
        secs.append([tuple(c + side * px + up * pz) for (px, pz) in prof])
    mb.sweep(secs, 0)


def _rosette(mb, x, y, z):
    """The oval wall plate where the lower rail dies into the landing-enclosure wall (photo 06)."""
    mb.box(x - 0.018, x, y - 0.045, y + 0.045, z - 0.075, z + 0.03)


# ================================================================ living room (staging after photos 04-06)
def living(M):
    fab, pc = MB(), MB()
    sx, sy = SOFA
    rot = -math.pi / 2 + 0.05                               # faces -X, back to the east wall; north end 5 cm out (05 + 06 fit)
    fs.flare_sofa(fab, sx, sy, rot, w=2.00, mi_body=0, mi_leg=1, back_h=0.90, arm_h=0.70)          # 06: ~2.0 m over the arms
    fab.build("Living_Sofa", [M['fs_sofa'], M['fs_espresso']], smooth=True)
    F = fs.local_frame(sx, sy, rot)                         # sofa frame: local -y = front, +x = south end
    # four plump floral pillows against the back, each spun a little in its own plane so the corners read (photo 06), the
    # middle pair slightly forward; two brown striped pillows in front of them near the arms (photos 05, 06)
    for i, (lxp, yaw, pz, sz, spin) in enumerate(((0.72, -0.20, 0.80, 0.48, 0.10), (0.25, 0.05, 0.83, 0.50, -0.07),
                                                   (-0.23, -0.06, 0.83, 0.50, 0.06), (-0.72, 0.19, 0.80, 0.48, -0.11))):
        px, py, _ = F(lxp, 0.21 - (0.03 if i in (1, 2) else 0.0), 0)
        fs.pillow_obj(f"Living_PillowFloral_{i}", [M['fs_floral_obj']], (px, py, pz), sz, sz * 0.96, 0.22, rot + yaw, 1.20, spin, seed=i + 1)
    for i, (lxp, spin) in enumerate(((0.58, 0.07), (-0.56, -0.08))):
        px, py, _ = F(lxp, 0.05, 0)
        fs.pillow_obj(f"Living_PillowStripe_{i}", [M['fs_stripe_sofa_obj']], (px, py, 0.74), 0.46, 0.44, 0.19,
                      rot + (-0.24 if lxp > 0 else 0.24), 1.28, spin, seed=i + 9)
    # oval glass cocktail table in front of the sofa (photos 04-06: ~0.45 m from the seat front, centred on the sofa)
    t = MB()
    tx, ty = XR - 1.62, sy - 0.02
    fs.oval_cocktail_table(t, tx, ty, math.pi / 2 + 0.05, a=0.60, b=0.33, h=0.47, mi_wood=0, mi_glass=1, mi_foot=2)
    t.build("Living_CocktailTable", [M['fs_cherry'], M['fs_glass'], M['fs_bronze']], smooth=True)
    tray = MB()
    tray.lathe(tx + 0.05, ty - 0.30, 0.47, [(0, 0.0), (0.05, 0.0), (0.07, 0.02), (0.10, 0.035), (0.095, 0.037), (0.06, 0.024), (0, 0.02)], seg=24, ry=0.55)
    tray.lathe(tx - 0.08, ty + 0.10, 0.47, [(0, 0.0), (0.03, 0.0), (0.035, 0.03), (0.08, 0.06), (0.078, 0.063), (0.03, 0.035), (0, 0.032)], seg=24)
    tray.tube((tx - 0.15, ty + 0.10, 0.53), (tx - 0.08, ty + 0.10, 0.60), 0.004, 0.004, seg=5)
    tray.tube((tx - 0.08, ty + 0.10, 0.60), (tx - 0.01, ty + 0.10, 0.53), 0.004, 0.004, seg=5)
    tray.lathe(tx + 0.02, ty + 0.36, 0.47, [(0, 0.0), (0.04, 0.0), (0.07, 0.02), (0.09, 0.03), (0.088, 0.032), (0.05, 0.02), (0, 0.018)], seg=24, ry=0.7)
    tray.build("Living_SilverTrays", [M['fs_hammered']], smooth=True)
    # slipper chairs in front of the window, the octagonal table + hammered vase between them (photo 04, back-projected
    # through INT_CAM's p04: west chair ~(9.70, 1.60), table ~(10.28, 1.50); photo 06: east chair ~(11.3-11.7, 1.7))
    ch = MB()
    chairs = ((XR - 1.33, LIV_Y0 + 0.52, math.pi + 0.30), (XR - 2.60, LIV_Y0 + 0.50, math.pi - 0.22))
    for (cx, cy, r_) in chairs:
        fs.slipper_chair(ch, cx, cy, r_, mi_up=0, mi_leg=1)
    ch.build("Living_SlipperChairs", [M['fs_leaf'], M['fs_espresso']], smooth=True)
    for (cx, cy, r_) in chairs:
        px, py = cx + 0.24 * math.sin(r_ + math.pi), cy - 0.24 * math.cos(r_ + math.pi)
        fs.pillow(pc, px, py, 0.72, 0.46, r_, pitch=1.3, seed=int(cx * 10), h=0.36)
    pc.build("Living_ChairPillows", [M['fs_stripe_chair']], smooth=True)
    ot, vs = MB(), MB()
    ox, oy = XR - 2.02, LIV_Y0 + 0.36
    fs.octagon_table(ot, ox, oy, r=0.19, h=0.47, mi=0, mi_top=0)
    fs.hammered_vase(vs, ox, oy, 0.47, r=0.155, h=0.30)
    ot.build("Living_OctagonTable", [M['fs_embossed']])
    vs.build("Living_HammeredVase", [M['fs_hammered']], smooth=True)
    # the lamp's octagonal table at the sofa's north end + the bronze candlestick lamp (photo 06)
    lt, lb, lsh = MB(), MB(), MB()
    lx, ly = XR - 0.44, ST_Y0 - 0.34                      # 06: (xe - 0.46, yf - 0.33)
    fs.octagon_table(lt, lx, ly, r=0.18, h=0.56, mi=0, mi_top=1)
    lt.build("Living_LampTable", [M['fs_embossed'], M['fs_embossed_top']])
    fs.candlestick_lamp(lb, lsh, lx, ly, 0.56, h=0.64, shade_w=(0.40, 0.25), shade_h=0.28)
    lb.build("Living_LampBase", [M['fs_bronze']], smooth=True)
    lsh.build("Living_LampShade", [M['fs_shade']], smooth=True)
    add_light("L_Living_Lamp", 'POINT', (lx, ly, 0.56 + 0.64 - 0.16), 4, color=WARM, size=0.05, coll=LC)
    # dried branches in a bronze urn in the front-right corner (photos 04, 06)
    uv = MB()
    fs.urn_vase(uv, XR - 0.25, LIV_Y0 + 0.28, 0.0, r=0.13, h=0.36)
    uv.build("Living_BranchUrn", [M['fs_gold']], smooth=True)
    from archviz.parts import branches
    br = MB()
    branches(br, XR - 0.25, LIV_Y0 + 0.28, 0.33, h=0.95, n=16, seed=4, mi=0, spread=0.26)
    br.build("Living_DriedBranches", [M['fs_twig']])
    # art: the parchment prints flanking the window (photo 04), 'Irises' over the sofa (06), the red abstract on the
    # landing-enclosure wall (05, 06)
    # (pictures = photo textures, PHOTO_TEX; frames and positions back-projected from the same photo corners:
    #  04 left print outer x 11.81..12.13 z 1.37..1.73, black frame ~16 mm; right print 9.10..9.50 x 1.22..1.77, 55 mm;
    #  06 Irises y 2.76..3.395 z 1.265..1.81, ornate silver ~80 mm; 05 abstract x 11.52..12.135 z 1.30..1.81, 50 mm)
    photo_art(M, "Living_PrintEast", 'print_e_04', 'X', 11.81, 12.13, LIV_Y0, +1, 1.37, 1.73, 'fs_ebony', 0.016, rough=0.35, coat=0.3)
    photo_art(M, "Living_PrintWest", 'print_w_04', 'X', 9.10, 9.50, LIV_Y0, +1, 1.22, 1.77, 'fs_frame_walnut', 0.055, rough=0.35, coat=0.3)
    photo_art(M, "Living_ArtIrises", 'irises_06', 'Y', 2.76, 3.395, XR, -1, 1.265, 1.81, 'fs_frame_silver', 0.08, rough=0.85)
    photo_art(M, "Living_ArtAbstract", 'abstract_05', 'X', 11.52, 12.135, ST_Y0, -1, 1.30, 1.81, 'fs_frame_bronze', 0.05, rough=0.85)
    windows_living(M)
    # ceiling register over the bay's west side (photo 04, px 700-790 x 142-152)
    register(M, "Living_Register", WALL_END_X + 0.33, LIV_Y0 + 0.35, along='X', w=0.30, d=0.10)          # 04: (9.28, 1.46)


def windows_living(M):
    """Photo 04: a pewter rod with fleur-de-lis finials 0.40 m past the window; two scarf swags (taupe sheer with
    embroidered sprays, scalloped lace hems) and three jabot tails (the middle one covers the meeting point), over
    two floor-length cream sheers embroidered with rows of small flower sprigs; white 2" blinds in the sashes."""
    lw = next(o for o in OPENINGS if o['name'] == 'living_win')
    a0, a1 = lw['a0'], lw['a1']
    y = LIV_Y0 + 0.11
    zr = lw["z1"] + 0.14                                   # 04: rod z 2.18-2.20 (p04 back-projection)
    # 04 through INT_CAM's p04 (planes y 1.22 / 1.28): rod x 9.51..11.76, tails centred 9.745 (0.19 wide), 10.675 (0.27)
    # and 11.525 (0.13) - the side tails hang just inside the opening's edges, clear of the prints beside the window
    rodm, sh, sw, jb, bl = MB(), MB(), MB(), MB(), MB()
    fs.finial_rod(rodm, a0 - 0.31, a1 + 0.20, y, zr, mi=0)
    rodm.build("Living_CurtainRod", [M['fs_pewter']], smooth=True)
    mid = (a0 + a1) / 2
    fs.sheer_panel(sh, a0 - 0.12, mid - 0.01, y - 0.03, 0.01, zr - 0.02, folds=11, depth=0.03)
    fs.sheer_panel(sh, mid + 0.01, a1 + 0.06, y - 0.03, 0.01, zr - 0.02, folds=11, depth=0.03)
    sh.build("Living_Sheers", [M['fs_sheer']])
    for (xa, xb) in ((a0 - 0.14, mid + 0.02), (mid - 0.02, a1 + 0.06)):
        fs.swag_valance(sw, xa, xb, y + 0.02, zr + 0.02, 0.64, depth=0.12, side=+1)      # 04: lace hem low point z 1.53
    sw.build("Living_Swags", [M['fs_swag']], smooth=True)
    for (xc, w) in ((a0 - 0.077, 0.19), (mid, 0.27), (a1 - 0.035, 0.14)):
        fs.jabot(jb, xc - w / 2, xc + w / 2, y + 0.06, zr + 0.01, 0.95, pleats=3, depth=0.035, taper=0.3)
    jb.build("Living_Jabots", [M['fs_tail']], smooth=True)
    f = Face('X', lw['b'] + 0.25 - 0.1, +1)       # the room-side face of the window unit
    from archviz import fenestration as fen
    for (b0, b1) in ((a0 + 0.06, mid - 0.03), (mid + 0.03, a1 - 0.06)):
        fen.blinds(f, bl, b0, b1, lw['z0'] + 0.06, lw['z1'] - 0.05, 0.12, drop=0.55, tilt=0.5, mi=0)
    bl.build("Living_Blinds", [M['blind_white'] if 'blind_white' in M else M['trim_int']])


def register(M, name, x, y, along='X', w=0.30, d=0.10, z=None):
    """Stamped-steel ceiling supply register: a white face with a louvre grid over a dark duct."""
    z = ZC if z is None else z
    mb = MB()
    hx, hy = (w / 2, d / 2) if along == 'X' else (d / 2, w / 2)
    mb.box(x - hx - 0.012, x + hx + 0.012, y - hy - 0.012, y + hy + 0.012, z - 0.006, z - 0.001, 0)
    mb.box(x - hx, x + hx, y - hy, y + hy, z - 0.0005, z, 1)
    n = int((w if along == 'X' else d) / 0.018)
    for i in range(n):
        if along == 'X':
            xx = x - hx + (i + 0.5) * (2 * hx / n)
            mb.box(xx - 0.003, xx + 0.003, y - hy, y + hy, z - 0.02, z - 0.004, 0)
        else:
            yy = y - hy + (i + 0.5) * (2 * hy / n)
            mb.box(x - hx, x + hx, yy - 0.003, yy + 0.003, z - 0.02, z - 0.004, 0)
    # the face frame has an open centre: cut it by leaving the louvre band visible (inner lip)
    mb.build(name, [M['fs_register'], M['fs_slot']])


# ================================================================ foyer + hall (staging after photos 04, 05)
def foyer(M):
    # entry rug in front of the door (photo 04: ~1.6 x 0.75 m, grey all-over pattern, pale border)
    rug = MB()
    rug.rbox(FOYER_WX + 0.06, WALL_END_X - 0.12, DOOR_Y + 0.05, DOOR_Y + 0.80, 0.0, 0.009, r=0.004, seg=1)
    rug.build("Rug_Foyer", [M['fs_rug']])
    # demilune console + embossed mirror on the foyer's west wall north of the coat closet (photo 05)
    cy = COAT_Y1_ - 0.62                                   # 05 through p05: console legs y 3.69..4.04, mirror 3.54..3.99
    con = MB()
    fs.demilune(con, FOYER_WX, cy, r=0.40, h=0.78, side=+1, mi=0)
    con.build("Foyer_Console", [M['fs_mahogany']], smooth=True)
    mir = MB()
    x0 = FOYER_WX
    mz0, mz1, mw_ = 1.15, 1.79, 0.23                                                            # 05: 0.46 x 0.64 m
    mir.box(x0 + 0.004, x0 + 0.040, cy - mw_, cy + mw_, mz0, mz1, 0)                           # embossed frame
    mir.box(x0 + 0.040, x0 + 0.046, cy - mw_ + 0.06, cy + mw_ - 0.06, mz0 + 0.06, mz1 - 0.06, 1)   # glass
    for zz in (mz0 + 0.03, mz1 - 0.03):                                                        # copper bands
        mir.box(x0 + 0.040, x0 + 0.048, cy - mw_, cy + mw_, zz - 0.012, zz + 0.012, 2)
    for yy in (cy - mw_ + 0.03, cy + mw_ - 0.03):
        mir.box(x0 + 0.040, x0 + 0.048, yy - 0.012, yy + 0.012, mz0, mz1, 2)
    mir.build("Foyer_Mirror", [M['fs_embossed'], M['mirror'], M['fs_copper']])
    deco = MB()
    deco.lathe(x0 + 0.22, cy + 0.08, 0.78, [(0, 0), (0.04, 0), (0.065, 0.05), (0.06, 0.10), (0.02, 0.16), (0.013, 0.22), (0.02, 0.23), (0.012, 0.28),
                                            (0, 0.29)], seg=20)                                   # blue-white decanter
    deco.lathe(x0 + 0.16, cy - 0.05, 0.125, [(0, 0), (0.045, 0), (0.05, 0.02), (0.042, 0.19), (0.05, 0.21), (0, 0.21)], seg=20)   # cobalt vase
    deco.build("Foyer_BlueGlass", [M['fs_cobalt']], smooth=True)
    # door chime box high on the west wall, a brass wall hanging at the hall corner (photo 05)
    ch = MB()
    ch.rbox(x0 + 0.004, x0 + 0.05, COAT_Y1_ - 0.38, COAT_Y1_ - 0.18, 1.98, 2.10, r=0.01)            # 05: (7.25, 4.10, 2.04)
    ch.build("Foyer_Chime", [M['fs_plastic_white']], smooth=True)
    bh = MB()
    bh.cylinder(x0 + 0.02, COAT_Y1_ - 0.06, 1.55, 1.72, 0.014, seg=10)
    bh.tube((x0 + 0.02, COAT_Y1_ - 0.06, 1.55), (x0 + 0.02, COAT_Y1_ - 0.06, 1.40), 0.004, 0.002, seg=6)
    bh.build("Foyer_BrassHanging", [M['fs_gold']], smooth=True)
    # flush dome light over the foyer (photo 05): frosted bowl in a brushed-nickel band, a nickel finial
    fx, fy = FOYER_WX + 0.45, COAT_Y1_ - 0.23                # 05 back-projected (7.60, 4.15): over the hall mouth
    dm, gl = MB(), MB()
    dm.cylinder(fx, fy, ZC - 0.025, ZC, 0.19, 0.195, seg=32)
    gl.lathe(fx, fy, ZC - 0.14, [(0, 0.0), (0.06, 0.004), (0.12, 0.025), (0.16, 0.06), (0.182, 0.10), (0.188, 0.115), (0, 0.115)], seg=32)
    dm.lathe(fx, fy, ZC - 0.165, [(0, 0.0), (0.012, 0.0), (0.016, 0.012), (0.008, 0.03), (0, 0.032)], seg=12)
    dm.build("Foyer_DomeBand", [M['fs_nickel']], smooth=True)
    gl.build("Foyer_DomeGlass", [M['frosted']], smooth=True)
    add_light("L_Foyer_Dome", 'POINT', (fx, fy, ZC - 0.09), 14, color=WARM, size=0.12, coll=LC)
    # brass bar cart under the lower flight (photos 05, 06) + its tea set and plant
    bc = MB()
    cx_, cy_ = (ST_X0 + FRUIT_X0) / 2 + 0.05, ST_Y0 - 0.26
    fs.bar_cart(bc, cx_, cy_, 0.0, a=0.40, b=0.20, mi_metal=0, mi_shelf=1, mi_wheel=2)
    bc.build("Foyer_BarCart", [M['fs_brass'], M['fs_smoke_glass'], M['fs_bronze']], smooth=True)
    tea = MB()
    tea.lathe(cx_ - 0.22, cy_ - 0.02, 0.792, [(0, 0), (0.05, 0), (0.07, 0.05), (0.06, 0.09), (0.03, 0.11), (0.012, 0.13), (0.02, 0.15), (0, 0.155)], seg=20)
    tea.tube((cx_ - 0.17, cy_ - 0.02, 0.84), (cx_ - 0.10, cy_ - 0.02, 0.88), 0.006, 0.004, seg=6)
    for k, dx in enumerate((0.06, 0.20)):
        tea.lathe(cx_ + dx, cy_ + 0.02 * (-1) ** k, 0.792, [(0, 0), (0.07, 0), (0.07, 0.006), (0.03, 0.008), (0.035, 0.05), (0.04, 0.06), (0, 0.055)], seg=20)
    tea.build("Foyer_TeaSet", [M['fs_glass']], smooth=True)
    pp = MB()
    zs = fs.planter(pp, cx_ + 0.12, cy_ + 0.03, 0.302, r=0.055, h=0.09, mi=0, mi_soil=1)
    pp.build("Foyer_CartPot", [M['fs_plastic_white'], M['fs_ebony']], smooth=True)
    fs.aloe("Plant_CartAloe", cx_ + 0.12, cy_ + 0.03, zs, h=0.16)
    bk = MB()
    bk.box(cx_ - 0.24, cx_ - 0.08, cy_ - 0.08, cy_ + 0.06, 0.302, 0.33)
    bk.build("Foyer_CartBox", [M['fs_cobalt']])
    # switch plates (photo 04: left of the entry door; photo 06: between the powder door and the stair)
    sp = MB()
    sp.box(WALL_END_X - 0.14, WALL_END_X - 0.07, DOOR_Y + 0.002, DOOR_Y + 0.008, 1.16, 1.28)
    sp.box(ST_X0 - 0.14, ST_X0 - 0.07, ST_YM - 0.006, ST_YM, 1.14, 1.26)
    sp.build("Foyer_SwitchPlates", [M['fs_plastic_white']])
    hall(M)


def hall(M):
    # peace lily in a blue-and-white planter on a blackwood stand at the hall entrance (photo 05)
    st = MB()
    lx, ly = HALL_X[1] - 0.45, COAT_Y1_ + 0.45                # 05: just past the wall's corner, in the hall mouth
    fs.plant_stand(st, lx, ly, r=0.17, h=0.13, mi=0)
    zs = fs.planter(st, lx, ly, 0.13, r=0.17, h=0.26, mi=1, mi_soil=2)
    st.build("Hall_LilyStand", [M['fs_ebony'], M['fs_porcelain'], M['fs_ebony']], smooth=True)
    fs.peace_lily("Plant_PeaceLily", lx, ly, zs, h=0.66, seed=11)
    # dracaena at the hall's end by the great-room opening (photo 05)
    dp = MB()
    dx, dy = HALL_X[0] + 0.24, HALL_END - 0.29
    zs2 = fs.planter(dp, dx, dy, 0.0, r=0.19, h=0.30, mi=0, mi_soil=1)
    dp.build("Hall_DracaenaPot", [M['fs_porcelain'], M['fs_ebony']], smooth=True)
    fs.dracaena("Plant_HallDracaena", dx, dy, zs2, h=1.45, seed=12)
    # Persian runner (photo 05)
    run = MB()
    run.rbox(HALL_X[0] + 0.18, HALL_X[1] - 0.18, COAT_Y1_ + 0.22, HALL_END - 0.50, 0.0, 0.008, r=0.003, seg=1)
    if 'fs_runner' not in M:
        M['fs_runner'] = _im._persian("FS_RunnerRed", (0.20, 0.055, 0.035, 1), (0.42, 0.33, 0.24, 1), (0.06, 0.05, 0.06, 1))
    run.build("Rug_HallRunner", [M['fs_runner']])
    # smoke detector + supply register on the hall ceiling (photo 05)
    sd = MB()
    sd.cylinder((HALL_X[0] + HALL_X[1]) / 2, (COAT_Y1_ + HALL_END) / 2 + 0.3, ZC - 0.035, ZC, 0.065, 0.07, seg=24)
    sd.build("Hall_SmokeDetector", [M['fs_plastic_white']], smooth=True)
    register(M, "Hall_Register", HALL_X[0] + 0.30, COAT_Y1_ + 0.35, along='Y', w=0.30, d=0.10)


# ================================================================ powder room (photo 07)
def powder(M):
    """Maple vanity wall to wall on the north wall: face frame, two false drawer fronts with arched bar pulls, two
    square raised-panel doors with bar pulls near the centre stile; cultured-marble top with an integral oval bowl, a
    4" back splash and two side splashes; single-lever faucet; frameless mirror; four-light bar (two ribbed shades
    up, two down); towel bar on the east wall, towel ring + black hand towel beside the door (seen in the mirror),
    double toggle switch + outlet on the west wall.  The toilet is outside the photographed view (not modelled)."""
    x0, x1, y0, y1 = PW['x0'], PW['x1'], PW['y0'], PW['y1']
    cab, hw, top, mir, bar, gl = MB(), MB(), MB(), MB(), MB(), MB()
    dep, zt = 0.56, 0.83                   # INT_CAM's p07 solve: counter depth prior 0.56, top 0.83 (+0.03 slab)
    yf = y1 - dep
    f = Face('X', yf, -1)
    cab.box(x0 + 0.005, x1 - 0.005, yf, y1, 0.09, zt - 0.19)                   # carcass below the bowl
    cab.box(x0 + 0.005, x1 - 0.005, yf, yf + 0.02, zt - 0.19, zt)                # front, back and sides around the bowl
    cab.box(x0 + 0.005, x1 - 0.005, y1 - 0.02, y1, zt - 0.19, zt)
    cab.box(x0 + 0.005, x0 + 0.025, yf, y1, zt - 0.19, zt)
    cab.box(x1 - 0.025, x1 - 0.005, yf, y1, zt - 0.19, zt)
    cab.box(x0 + 0.03, x1 - 0.03, yf + 0.06, y1, 0.0, 0.09)                  # toe kick
    # face frame + fronts
    W = x1 - x0 - 0.01
    xm = (x0 + x1) / 2
    zd0, zd1 = zt - 0.20, zt - 0.03
    for (a, b) in ((x0 + 0.03, xm - 0.02), (xm + 0.02, x1 - 0.03)):
        f.box(cab, a, b, 0.0, 0.02, zd0 + 0.01, zd1, 1)                       # false drawer fronts
        f.box(cab, a + 0.03, b - 0.03, 0.02, 0.026, zd0 + 0.04, zd1 - 0.03, 1)
        pc = (a + b) / 2
        for k in range(7):                                                    # arched bar pull
            u0, u1 = k / 7, (k + 1) / 7
            za = zd0 + 0.095 + 0.008 * math.sin(math.pi * (u0 + u1) / 2)
            f.box(hw, pc - 0.065 + 0.13 * u0, pc - 0.065 + 0.13 * u1, 0.026, 0.04, za - 0.004, za + 0.004, 0)
        for s in (-1, 1):
            f.box(hw, pc + s * 0.065 - 0.004, pc + s * 0.065 + 0.004, 0.02, 0.04, zd0 + 0.085, zd0 + 0.1, 0)
    for (a, b, side) in ((x0 + 0.03, xm - 0.02, 1), (xm + 0.02, x1 - 0.03, -1)):
        zz0, zz1 = 0.12, zd0 - 0.03
        f.box(cab, a, b, 0.0, 0.02, zz0, zz1, 1)                              # door slab
        fw = 0.068                                                            # stile / rail frame (07: ~1/6 of the door)
        f.box(cab, a, a + fw, 0.02, 0.036, zz0, zz1, 1)
        f.box(cab, b - fw, b, 0.02, 0.036, zz0, zz1, 1)
        f.box(cab, a + fw, b - fw, 0.02, 0.036, zz0, zz0 + fw, 1)
        f.box(cab, a + fw, b - fw, 0.02, 0.036, zz1 - fw, zz1, 1)
        f.box(cab, a + fw + 0.012, b - fw - 0.012, 0.02, 0.026, zz0 + fw + 0.012, zz1 - fw - 0.012, 1)   # bevel
        f.box(cab, a + fw + 0.035, b - fw - 0.035, 0.026, 0.031, zz0 + fw + 0.035, zz1 - fw - 0.035, 1)  # raised field
        hx = b - 0.04 if side > 0 else a + 0.04
        f.box(hw, hx - 0.005, hx + 0.005, 0.046, 0.056, zz1 - 0.24, zz1 - 0.08, 0)      # bar pull, standing off the stile
        f.box(hw, hx - 0.006, hx + 0.006, 0.036, 0.05, zz1 - 0.245, zz1 - 0.232, 0)
        f.box(hw, hx - 0.006, hx + 0.006, 0.036, 0.05, zz1 - 0.088, zz1 - 0.075, 0)
    f.box(cab, x0 + 0.005, x1 - 0.005, 0.0, 0.012, 0.09, 0.12, 0)               # face-frame rails / stiles
    f.box(cab, x0 + 0.005, x1 - 0.005, 0.0, 0.012, zd0 - 0.03, zd0 + 0.01, 0)
    f.box(cab, xm - 0.02, xm + 0.02, 0.0, 0.012, 0.09, zt - 0.02, 0)
    del W
    # top with integral bowl, back + side splashes
    bcy, brx, bry = y1 - 0.28, 0.18, 0.13
    fs.slab_oval_hole(top, x0, x1, yf + 0.02, y1, zt, zt + 0.03, xm, bcy, brx, bry)
    top.rbox(x0, x1, yf - 0.03, yf + 0.025, zt, zt + 0.032, r=0.012)
    fs.bowl(top, xm, bcy, zt + 0.03, brx, bry, depth=0.16)
    top.box(x0, x1, y1 - 0.015, y1, zt + 0.03, zt + 0.13)
    top.box(x0, x0 + 0.015, yf - 0.02, y1, zt + 0.03, zt + 0.13)
    top.box(x1 - 0.015, x1, yf - 0.02, y1, zt + 0.03, zt + 0.13)
    hw.cylinder(xm, y1 - 0.075, zt + 0.03, zt + 0.19, 0.016, 0.014, seg=12)
    hw.tube((xm, y1 - 0.075, zt + 0.18), (xm, y1 - 0.18, zt + 0.16), 0.011, 0.009, seg=8)
    hw.box(xm - 0.008, xm + 0.008, y1 - 0.09, y1 - 0.02, zt + 0.19, zt + 0.21)
    # soap pump + a glass with red twigs at the right corner (photo 07)
    acc = MB()
    acc.lathe(xm - 0.20, y1 - 0.09, zt + 0.03, [(0, 0), (0.028, 0), (0.03, 0.12), (0.012, 0.13), (0.008, 0.17), (0, 0.17)], seg=16)
    acc.build("Powder_Soap", [M['fs_plastic_white']], smooth=True)
    gv = MB()
    gv.box(x1 - 0.12, x1 - 0.05, y1 - 0.10, y1 - 0.04, zt + 0.03, zt + 0.21)
    gv.build("Powder_TwigGlass", [M['fs_glass']])
    from archviz.parts import branches
    tw = MB()
    branches(tw, x1 - 0.085, y1 - 0.07, zt + 0.10, h=0.30, n=9, seed=7, mi=0, spread=0.18)
    if 'fs_twig_red' not in M:
        from archviz import materials as _mm
        M['fs_twig_red'] = _mm.new_mat("FS_RedTwig", (0.42, 0.06, 0.05, 1), rough=0.6)
    tw.build("Powder_RedTwigs", [M['fs_twig_red']])
    # frameless mirror, four-light bar
    mw = (x1 - x0) - 0.14                    # 07 through p07: the mirror nearly spans the vanity, z ~1.02 .. 2.09
    mir.box(xm - mw / 2, xm + mw / 2, y1 - 0.010, y1 - 0.004, zt + 0.16, 2.08)
    zb = 2.05
    bar.box(xm - 0.05, xm + 0.05, y1 - 0.02, y1 - 0.004, zb - 0.045, zb + 0.045)
    bar.lathe(xm, y1 - 0.07, zb - 0.02, [(0, 0), (0.028, 0.0), (0.034, 0.02), (0.022, 0.05), (0, 0.055)], seg=16)
    bar.tube((xm, y1 - 0.015, zb), (xm, y1 - 0.07, zb), 0.012, 0.012, seg=8)
    shades = []
    for s in (-1, 1):
        ax, ay = xm + s * 0.10, y1 - 0.10
        bar.path_tube([(xm, y1 - 0.07, zb + 0.01), (xm + s * 0.06, y1 - 0.09, zb + 0.045), (ax, ay, zb + 0.06)], 0.006, seg=6)
        bar.path_tube([(xm, y1 - 0.07, zb - 0.01), (xm + s * 0.05, y1 - 0.085, zb - 0.04), (xm + s * 0.07, ay, zb - 0.05)], 0.006, seg=6)
        shades.append((ax, ay, zb + 0.06, +1))
        shades.append((xm + s * 0.07, ay, zb - 0.05, -1))
    for k, (sx, sy, sz, d) in enumerate(shades):
        # fluted bell (07): a wide flared skirt, thin wall
        prof = [(0.020, 0.0), (0.030, 0.012), (0.045, 0.04), (0.058, 0.075), (0.068, 0.10), (0.064, 0.10), (0.054, 0.075), (0.040, 0.042), (0.024, 0.014)]
        if d > 0:
            gl.lathe(sx, sy, sz, prof, seg=20)
        else:
            gl.lathe(sx, sy, sz - 0.10, [(r, 0.10 - z) for (r, z) in reversed(prof)], seg=20)
        bar.cylinder(sx, sy, sz - 0.012 if d > 0 else sz - 0.004, sz + 0.004 if d > 0 else sz + 0.012, 0.022, seg=12)
        add_light(f"L_Powder_{k}", 'POINT', (sx, sy, sz + d * 0.05), 6.0, color=WARM, size=0.025, coll=LC)
    # short towel bar on the east wall right beside the door (07 through p07: far bracket y ~6.23-6.29, z 1.33); a black hand
    # towel hangs on its near half (it shows in the mirror, out of the direct view)
    tb0, tb1, zb_ = y0 + 0.03, y0 + 0.28, 1.33
    bar.box(x1 - 0.03, x1 - 0.004, tb0 - 0.02, tb0 + 0.02, zb_ - 0.02, zb_ + 0.02)
    bar.box(x1 - 0.03, x1 - 0.004, tb1 - 0.02, tb1 + 0.02, zb_ - 0.02, zb_ + 0.02)
    bar.box(x1 - 0.075, x1 - 0.03, tb0 - 0.01, tb0 + 0.01, zb_ - 0.01, zb_ + 0.01)
    bar.box(x1 - 0.075, x1 - 0.03, tb1 - 0.01, tb1 + 0.01, zb_ - 0.01, zb_ + 0.01)
    bar.box(x1 - 0.085, x1 - 0.065, tb0 - 0.01, tb1 + 0.01, zb_ - 0.01, zb_ + 0.01)
    cab.build("Powder_Vanity", [M['fs_vanity_maple_h'], M['fs_vanity_maple']])
    hw.build("Powder_Hardware", [M['nickel']])
    top.build("Powder_Top", [M['cultured_marble']], smooth=False)
    mir.build("Powder_Mirror", [M['mirror']])
    bar.build("Powder_LightBar", [M['fs_nickel']], smooth=True)
    gl.build("Powder_Shades", [M['frosted']], smooth=True)
    tw_ = MB()
    tw_.rbox(x1 - 0.10, x1 - 0.06, tb0 - 0.02, tb0 + 0.06, zb_ - 0.42, zb_ + 0.01, r=0.012)
    if 'fs_towel_black' not in M:
        from archviz import materials as _mm
        M['fs_towel_black'] = _mm.fabric("FS_TowelBlack", (0.025, 0.025, 0.028, 1), rough=1.0, sheen=0.8, weave=300, bump=0.6)
    tw_.build("Powder_Towel", [M['fs_towel_black']], smooth=True)
    sp = MB()
    sy0 = y1 - 0.60                                                                    # 07: switch centre (8.53, 6.69, 1.22)
    sp.box(x0 + 0.004, x0 + 0.010, sy0, sy0 + 0.13, 1.15, 1.28)                  # double toggle plate (west wall)
    for yy in (sy0 + 0.04, sy0 + 0.09):
        sp.box(x0 + 0.010, x0 + 0.020, yy - 0.004, yy + 0.004, 1.195, 1.215)
    sp.box(x0 + 0.004, x0 + 0.010, y1 - 0.10, y1 - 0.03, 1.18, 1.30)                   # outlet above the side splash (07: z 1.24)
    sp.build("Powder_Switches", [M['fs_plastic_white']])
    register(M, "Powder_Register", xm, y0 + 0.45, along='X', w=0.25, d=0.10)
    ex = MB()
    ex.box(xm - 0.12, xm + 0.12, y0 + 0.85, y0 + 1.09, ZC - 0.01, ZC)
    ex.build("Powder_ExhaustFan", [M['fs_register']])


# ================================================================ garage (photo 24)
def garage(M):
    """Finished garage (photo 24): smooth slab with saw-cut joints and tyre marks; the sectional door open overhead on
    its tracks (shown only for photo 24 through before_render); the opener + rail + emergency cord; a steel wall shelf
    with moving boxes on the left wall, the electrical panel near the front, two city recycling carts (one yellow lid),
    a riding mower, a white plastic chair, a mini fridge and an upright freezer in the back-left corner; along the
    rear wall a golf bag, folding chairs, boxes, a storage bin, two pedestal fans, a gas can and a shoe mat."""
    zf = Z_GAR
    gx0, gx1 = GAR[0] + EWT, GAR[1] - EWT
    ybk = GAR[3]
    # slab (photo 24 through INT_CAM's p24): the drywall stops on a ~0.14 m concrete curb (stem wall) along the back wall -
    # the grey band at u 940-1300, v 612-657; its top is plan Z_GAR (-0.10, the line INT_CAM fitted as "rear floor") and
    # the slab meets its foot at v ~645 (u 1067) -> z ~ -0.245 at the back wall; the Y-running saw joint then back-projects
    # to x 3.2 (INT_CAM: ~3.1). At the door the slab is EXT's Z_GAR_DOOR (-0.25). So the slab is almost level; it runs
    # from Z_GAR_DOOR at the door to -0.245 at the back, and a curb closes the gap up to the wall skins (Z_GAR).
    zd = globals().get('Z_GAR_DOOR', zf)
    zb = zf - 0.145                                  # -0.245 at the back wall (photo 24, above)
    s = MB()
    s.hexa([(gx0, BWT, zd - 0.25), (gx1, BWT, zd - 0.25), (gx1, ybk, zd - 0.25), (gx0, ybk, zd - 0.25),
            (gx0, BWT, zd), (gx1, BWT, zd), (gx1, ybk, zb), (gx0, ybk, zb)])
    gd = next(o for o in OPENINGS if o['name'] == 'garage_door')
    s.box(gd['a0'], gd['a1'], 0.0, BWT, zd - 0.10, zd + 0.003)                      # the slab runs out through the opening
    s.build("Garage_Slab", [M['fs_garage_slab']])
    zfl = lambda y: zd + (zb - zd) * max(0.0, min(1.0, (y - BWT) / (ybk - BWT)))      # slab height
    cu = MB()
    cu.box(gx0, gx1, ybk - 0.03, ybk, zb - 0.01, zf + 0.004)                                           # back curb
    cu.box(gx0, gx0 + 0.03, BWT, ybk, zb - 0.01, zf + 0.004)                                           # left
    cu.box(gx1 - 0.03, gx1, BWT, ybk, zb - 0.01, zf + 0.004)                                           # right (house side)
    cu.box(gx0, gd['a0'], BWT, BWT + 0.03, zd - 0.01, zf + 0.004)                                      # front, beside the door
    cu.box(gd['a1'], gx1, BWT, BWT + 0.03, zd - 0.01, zf + 0.004)
    cu.build("Garage_Curb", [M['concrete'] if 'concrete' in M else M['fs_garage_slab']])
    # tracks, torsion spring, opener + rail + emergency cord. Photo 24 through p24: the left horizontal track back-projects
    # onto x 0.62 at z 1.77-1.89 (y 0.5 -> 2.5) and the open door's rear edge (u 540-1100, v 370-230) onto y 2.47-2.61 at
    # z 1.85 - i.e. a low-headroom track just above the opening (z1 1.84), not 0.3 m above it.
    tr, op, dr = MB(), MB(), MB()
    zt_ = Z_C1 + 0.05
    zh = gd['z1'] + 0.06                     # horizontal track height (low headroom, photo 24)
    for x in (gd['a0'] - 0.05, gd['a1'] + 0.05):
        tr.box(x - 0.02, x + 0.02, BWT + 0.02, BWT + 0.07, gd['z0'], gd['z1'] - 0.12)                        # vertical track
        tr.path_tube([(x, BWT + 0.05, gd['z1'] - 0.14), (x, BWT + 0.08, zh - 0.08), (x, BWT + 0.20, zh - 0.01),
                      (x, BWT + 0.34, zh)], 0.02, seg=6)
        tr.box(x - 0.02, x + 0.02, BWT + 0.30, BWT + 3.15, zh - 0.02, zh + 0.02)                            # horizontal track
        tr.box(x - 0.01, x + 0.01, BWT + 3.1, BWT + 3.15, zh + 0.02, zt_)                                   # hanger
    tr.tube((gd['a0'] - 0.05, BWT + 0.10, gd['z1'] + 0.22), (gd['a1'] + 0.05, BWT + 0.10, gd['z1'] + 0.22), 0.012, 0.012, seg=8)   # torsion bar
    for x in (gd['a0'] + 0.2, (gd['a0'] + gd['a1']) / 2, gd['a1'] - 0.2):
        tr.tube((x, BWT + 0.10, gd['z1'] + 0.18), (x, BWT + 0.10, gd['z1'] + 0.26), 0.06, 0.06, seg=12)    # springs / drums
    mx = (gd['a0'] + gd['a1']) / 2
    # photo 24: the opener (white housing, black front) hangs at u 855-945, v 300-345 -> (2.6-3.0, 3.5-3.7) at z ~2.05;
    # the rail runs from the header to it above the door; the red release handle hangs from the trolley at v 472
    ox, oy0, oy1 = 2.85, 3.50, 3.92
    oz0, oz1 = 1.97, 2.15
    tr.box(ox - 0.02, ox + 0.02, BWT + 0.20, oy0, zh + 0.07, zh + 0.11)                                   # opener rail
    tr.box(ox - 0.03, ox + 0.03, BWT + 0.05, BWT + 0.22, zh + 0.05, zh + 0.13)                             # header bracket
    tr.path_tube([(ox, 3.05, zh + 0.07), (ox, 2.85, zh + 0.04), (ox, 2.62, zh - 0.02)], 0.012, seg=6)   # J-arm to the door
    tr.box(ox - 0.03, ox + 0.03, 3.00, 3.12, zh + 0.05, zh + 0.10)                                         # trolley
    for yy in (oy0 + 0.08, oy1 - 0.08):
        tr.box(ox - 0.26, ox + 0.26, yy - 0.015, yy + 0.015, oz1 - 0.01, oz1 + 0.01)                       # angle-iron hanger
        for sx_ in (-1, 1):
            tr.box(ox + sx_ * 0.25 - 0.015, ox + sx_ * 0.25 + 0.015, yy - 0.015, yy + 0.015, oz1, zt_)
    op.rbox(ox - 0.21, ox + 0.21, oy0, oy1, oz0, oz1, r=0.07)
    op.build("Garage_Opener", [M['fs_plastic_white']], smooth=True)
    ob = MB()
    ob.rbox(ox - 0.20, ox + 0.20, oy0 - 0.03, oy0 + 0.10, oz0 + 0.02, oz1 - 0.03, r=0.03)
    ob.box(ox - 0.12, ox + 0.12, oy0 + 0.10, oy1 - 0.06, oz0 - 0.012, oz0 + 0.01)
    ob.build("Garage_OpenerTrim", [M['appliance_black'] if 'appliance_black' in M else M['frame']])
    cord = MB()
    cord.cylinder(ox, 3.06, 1.14, zh + 0.05, 0.002, seg=4)
    cord.sphere((ox, 3.06, 1.11), 0.032, seg=12, rings=8)
    if 'fs_ball_red' not in M:
        from archviz import materials as _mm
        M['fs_ball_red'] = _mm.new_mat("FS_RedPlastic", (0.55, 0.03, 0.03, 1), rough=0.4)
        M['fs_ball_yellow'] = _mm.new_mat("FS_YellowPlastic", (0.78, 0.60, 0.02, 1), rough=0.45)
        M['fs_cardboard'] = _mm.noise_mat("FS_Cardboard", (0.40, 0.27, 0.15, 1), (0.50, 0.36, 0.21, 1), scale=30, bump=0.1, rough=0.85)
        M['fs_grey_plastic'] = _mm.new_mat("FS_GreyTote", (0.32, 0.33, 0.34, 1), rough=0.5)
        M['fs_clear_tote'] = _mm.new_mat("FS_ClearTote", (0.75, 0.78, 0.8, 1), rough=0.2, transmission=0.6)
        M['fs_black_plastic'] = _mm.new_mat("FS_BlackPlastic", (0.03, 0.03, 0.03, 1), rough=0.45)
        M['fs_steel_grey'] = _mm.new_mat("FS_PanelGrey", (0.42, 0.43, 0.43, 1), rough=0.45, metal=0.6)
        M['fs_mower_red'] = _mm.new_mat("FS_MowerRed", (0.50, 0.02, 0.02, 1), rough=0.35, coat=0.4)
        M['fs_wood_chair'] = _mm.wood("FS_BeechChair", light=(0.45, 0.28, 0.14, 1), dark=(0.35, 0.21, 0.10, 1), grain_axis='Z')
        M['fs_mat'] = _mm.noise_mat("FS_ShoeMat", (0.10, 0.08, 0.06, 1), (0.16, 0.13, 0.10, 1), scale=90, bump=0.4)
    cord.build("Garage_Cord", [M['fs_ball_red']], smooth=True)
    tr.build("Garage_Tracks", [M['steel']], smooth=True)
    # the door in the open position: four panels lying on the horizontal tracks, hinges + rollers (photo 24)
    y_a = BWT + 0.25
    ph = (gd['z1'] - gd['z0']) / 4
    for k in range(4):
        ya, yb = y_a + k * ph, y_a + (k + 1) * ph - 0.006
        dr.box(gd['a0'], gd['a1'], ya, yb, zh - 0.06, zh - 0.02, 0)
        for x in (gd['a0'] + 0.25, gd['a0'] + 1.3, mx, gd['a1'] - 1.3, gd['a1'] - 0.25):
            dr.box(x - 0.04, x + 0.04, yb - 0.03, yb + 0.03, zh - 0.07, zh - 0.06, 1)
        for x in (gd['a0'] + 0.03, gd['a1'] - 0.03):
            dr.box(x - 0.03, x + 0.03, yb - 0.04, yb + 0.02, zh - 0.07, zh - 0.058, 1)
    ob_ = dr.build("GarageOpenDoor", [M['garage_white'] if 'garage_white' in M else M['drywall_white'], M['steel']])
    ob_.hide_render = True
    if 'fs_ball_red' not in M:
        from archviz import materials as _mm
        M['fs_ball_red'] = _mm.new_mat("FS_RedPlastic", (0.55, 0.03, 0.03, 1), rough=0.4)
    from archviz import materials as _mm
    for k_, args in (('fs_cart_sky', ("FS_CartSkyBlue", (0.13, 0.33, 0.52, 1))), ('fs_cart_blue', ("FS_CartBlue", (0.035, 0.15, 0.29, 1))),
                     ('fs_cart_lid_b', ("FS_CartLidBlue", (0.05, 0.19, 0.34, 1))), ('fs_panel_grey', ("FS_PanelDark", (0.10, 0.105, 0.11, 1))),
                     ('fs_hose_green', ("FS_HoseGreen", (0.04, 0.22, 0.05, 1))), ('fs_golf_maroon', ("FS_GolfMaroon", (0.20, 0.02, 0.03, 1))),
                     ('fs_stool_blue', ("FS_StoolBlue", (0.05, 0.25, 0.55, 1))), ('fs_bowl_navy', ("FS_BowlNavy", (0.02, 0.03, 0.12, 1))),
                     ('fs_label_green', ("FS_LabelGreen", (0.10, 0.45, 0.12, 1))), ('fs_tote_blue', ("FS_ToteBlue", (0.10, 0.25, 0.45, 1))),
                     ('fs_cloth_maroon', ("FS_ClothMaroon", (0.22, 0.03, 0.06, 1)))):
        if k_ not in M:
            M[k_] = _mm.new_mat(args[0], args[1], rough=0.5)
    wl = gx0
    st, box = MB(), MB()
    # left wall: electrical panel (24: u 138-215, v 357-500 -> y 0.93-1.30, z 0.97-1.88; dark grey, inner door + labels),
    # the steel wall shelf with moving boxes (INT_CAM: front edge x ~-0.85)
    pn = MB()
    pn.box(wl + 0.005, wl + 0.09, 0.93, 1.30, 0.97, 1.88, 0)
    pn.box(wl + 0.09, wl + 0.095, 1.00, 1.22, 1.20, 1.74, 0)                                             # inner door
    pn.box(wl + 0.095, wl + 0.10, 1.13, 1.17, 1.44, 1.50, 1)                                             # latch
    pn.box(wl + 0.095, wl + 0.098, 1.05, 1.12, 1.66, 1.70, 2)                                            # labels
    pn.box(wl + 0.095, wl + 0.098, 1.05, 1.12, 1.60, 1.63, 3)
    pn.build("Garage_Panel", [M['fs_panel_grey'], M['fs_black_plastic'], M['fs_ball_yellow'], M['fs_label_green']])
    st.box(wl + 0.02, wl + 0.30, 1.70, 4.45, zf + 1.66, zf + 1.69, 0)                                    # shelf deck
    for yy in (1.80, 2.70, 3.60, 4.35):
        st.path_tube([(wl + 0.01, yy, zf + 1.40), (wl + 0.27, yy, zf + 1.65)], 0.008, seg=5)             # brackets
        st.box(wl + 0.005, wl + 0.02, yy - 0.015, yy + 0.015, zf + 1.30, zf + 1.70, 0)
    st.cylinder(wl + 0.28, 2.75, zfl(2.75), zf + 1.66, 0.02, seg=8)                                        # a post
    rng = random.Random(24)
    y = 1.75
    while y < 4.35:
        w = rng.uniform(0.42, 0.58)
        h = rng.uniform(0.30, 0.42)
        box.box(wl + 0.03, wl + 0.36, y, y + w, zf + 1.69, zf + 1.69 + h, 0)
        y += w + 0.02
    box.box(wl + 0.05, wl + 0.40, 3.70, 4.10, zf + 1.02, zf + 1.30, 0)
    # the pile left of the carts (24: a white "temperature sensitive" carton at u 240-305, v 440-500 -> (-0.8, 1.36-1.72,
    # z 0.97-1.37) on a black bag on a grey tote; a translucent bag beside it)
    pl = MB()
    pl.rbox(wl + 0.05, wl + 0.60, 1.35, 1.80, zfl(1.6), zfl(1.6) + 0.45, r=0.03, mi=0)
    pl.blob((wl + 0.33, 1.57, 0.60), 0.30, seg=14, rings=10, jitter=0.18, seed=11, mi=1, squash=1.15, rx=1.0, ry=0.8)
    pl.box(wl + 0.15, wl + 0.55, 1.36, 1.72, 0.95, 1.30, 2)
    pl.box(wl + 0.55, wl + 0.552, 1.42, 1.62, 1.08, 1.20, 3)
    pl.blob((wl + 0.55, 1.88, 0.72), 0.20, seg=12, rings=8, jitter=0.2, seed=12, mi=4, squash=1.0, rx=0.9, ry=1.0)
    pl.build("Garage_Pile", [M['fs_grey_plastic'], M['fs_black_plastic'], M['fs_plastic_white'], M['fs_paper_box'] if 'fs_paper_box' in M else M['fs_ball_red'],
                             M['fs_clear_tote']], smooth=True)
    # the two carts (24: the broad faces are almost square to the camera - bottom edges rise 0.085 px/px -> fronts face
    # azimuth -35 deg; bottom front centres (0.735, 1.115) and (0.38, 2.015) on the slab). A: sky blue + yellow lid,
    # B: darker blue + blue lid with a red / black trunk organiser on it.
    # (the bottom-edge slope alone says 55 deg; the narrow right-side strip in the photo, ~0.1 of the face, needs ~68)
    for (nm, fx_, fy_, yaw_, body, lid) in (("A", 0.735, 1.115, math.radians(68.0), 'fs_cart_sky', 'fs_ball_yellow'),
                                            ("B", 0.380, 2.015, math.radians(66.0), 'fs_cart_blue', 'fs_cart_lid_b')):
        cb = MB()
        fs.wheelie_cart(cb, 0, 1, 2, 3, 4, w=0.66, d=0.76, h=1.08)         # 24: 105 px wide x 130 tall at the same depth -> 65 gal
        if nm == "B":
            cb.rbox(-0.25, 0.25, -0.19, 0.17, 1.06, 1.31, r=0.02, mi=5)
            cb.box(-0.255, 0.255, -0.195, 0.175, 1.06, 1.09, 2)
            cb.box(-0.255, 0.255, -0.195, 0.175, 1.29, 1.315, 2)
            cb.path_tube([(-0.08, -0.02, 1.31), (-0.06, -0.02, 1.36), (0.06, -0.02, 1.36), (0.08, -0.02, 1.31)], 0.012, seg=6, mi=2)
        ob_c = cb.build(f"Garage_Cart{nm}", [M[body], M[lid], M['fs_black_plastic'], M['steel'], M['fs_plastic_white'], M['fs_ball_red']], smooth=False)
        n_ = (math.sin(yaw_), -math.cos(yaw_))
        fs.place(ob_c, fx_ - n_[0] * 0.37, fy_ - n_[1] * 0.37, zfl(fy_), yaw_)
    # white resin chair with a shopping bag on the seat (24: front legs (0.20, 2.53) / (0.32, 2.90) -> faces the camera)
    pc = MB()
    fs.plastic_chair(pc, 0)
    pc.blob((0.0, 0.02, 0.44 + 0.19), 0.20, seg=14, rings=10, jitter=0.12, seed=3, mi=1, squash=1.05, rx=1.1, ry=0.8)
    yaw_ch = math.radians(72.0)
    fs.place(pc.build("Garage_PlasticChair", [M['fs_plastic_white'], M['fs_plastic_white']], smooth=True), 0.16, 2.90, zfl(2.9), yaw_ch)
    # riding mower (24: right rear tyre on the slab at (0.09, 3.75); red hood toward the door, behind the chair)
    mw = MB()
    fs.riding_mower(mw, 0, 1, 2)
    fs.place(mw.build("Garage_Mower", [M['fs_mower_red'], M['fs_black_plastic'], M['fs_steel_grey']], smooth=True), -0.36, 3.50, zfl(3.5), 0.0)
    ap = MB()
    zr = zfl(6.0)
    ap.box(wl + 0.02, wl + 0.72, 5.62, 6.30, zr, zr + 1.45, 0)                                           # upright freezer
    ap.box(wl + 0.72, wl + 0.74, 5.64, 6.28, zr + 0.05, zr + 1.43, 0)
    ap.box(wl + 0.74, wl + 0.76, 5.70, 5.73, zr + 0.9, zr + 1.3, 1)
    ap.box(wl + 0.25, wl + 0.73, 4.60, 5.08, zfl(4.8), zfl(4.8) + 0.62, 1)                             # mini fridge
    ap.box(wl + 0.25, wl + 0.73, 4.58, 4.60, zfl(4.8) + 0.02, zfl(4.8) + 0.60, 2)
    ap.build("Garage_Appliances", [M['ceramic'], M['fs_steel_grey'], M['fs_black_plastic']])
    # back of the bay (24, feet on the slab at v 625-680 through p24): a maroon golf bag in front of the freezer, a tall
    # flat box, a yellow bottle, a blue step stool, a wooden step chair, a grey tote with boxes, a maroon throw and paper
    # rolls on it, two pedestal fans, a clear water jug, a red cooler with a navy bowl, a folding chair on the shoe mat
    zr = zfl(5.9)
    rb = MB()
    rb.box(0.08, 0.38, 5.32, 5.46, zr, zr + 1.05)                                                          # tall flat box
    rb.box(1.40, 1.92, 5.86, 6.26, zr + 0.30, zr + 0.62)                                                   # boxes on the tote
    rb.box(1.44, 1.88, 5.90, 6.24, zr + 0.62, zr + 0.86)
    rb.build("Garage_Boxes", [M['fs_cardboard']])
    gb_ = MB()
    gb_.tube((-0.10, 5.22, zr), (-0.18, 5.34, zr + 0.98), 0.13, 0.12, seg=16, mi=0)                      # golf bag
    gb_.tube((-0.18, 5.34, zr + 0.98), (-0.19, 5.36, zr + 1.10), 0.12, 0.10, seg=16, mi=1)                # club heads
    gb_.build("Garage_GolfBag", [M['fs_golf_maroon'], M['fs_black_plastic']], smooth=True)
    tt = MB()
    tt.rbox(1.35, 1.97, 5.82, 6.26, zr, zr + 0.30, r=0.03)
    tt.build("Garage_Tote", [M['fs_grey_plastic']], smooth=True)
    cl = MB()
    cl.drape(1.38, 1.96, 5.86, 6.26, zr + 0.87, t=0.03, sag=0.05, folds=3, seed=4)
    for k in range(5):
        cl.cylinder(1.50 + 0.08 * k, 6.05 + 0.03 * (k % 2), zr + 0.90, zr + 1.05, 0.055, seg=12, mi=1)       # paper rolls
    cl.build("Garage_Throw", [M['fs_cloth_maroon'], M['fs_plastic_white']], smooth=True)
    fan = MB()
    for (x, y) in ((2.15, 5.72), (2.62, 5.74)):
        fan.cylinder(x, y, zr, zr + 0.02, 0.22, seg=20)
        fan.cylinder(x, y, zr + 0.02, zr + 1.05, 0.015, seg=8)
        fan.tube((x, y - 0.07, zr + 1.15), (x, y + 0.07, zr + 1.15), 0.21, 0.21, seg=24)
    fan.build("Garage_Fans", [M['fs_plastic_white']], smooth=True)
    gc = MB()
    gc.rbox(3.55, 3.90, 5.82, 6.12, zr, zr + 0.28, r=0.03, mi=0)                                           # red cooler
    gc.lathe(3.72, 5.97, zr + 0.28, [(0.0, 0.0), (0.09, 0.0), (0.15, 0.08), (0.14, 0.085), (0.0, 0.01)], seg=24, mi=1)
    gc.build("Garage_Cooler", [M['fs_ball_red'], M['fs_bowl_navy']], smooth=True)
    fc = MB()
    fx = 4.66
    for s_ in (-1, 1):
        fc.box(fx + s_ * 0.19 - 0.015, fx + s_ * 0.19 + 0.015, 5.60, 5.63, zr, zr + 0.82)
        fc.box(fx + s_ * 0.19 - 0.015, fx + s_ * 0.19 + 0.015, 5.97, 6.00, zr, zr + 0.82)
    fc.box(fx - 0.21, fx + 0.21, 5.59, 6.00, zr + 0.44, zr + 0.47)
    for zz in (0.60, 0.72):
        fc.box(fx - 0.19, fx + 0.19, 5.96, 6.00, zr + zz, zr + zz + 0.06)
    for zz in (0.12, 0.22):
        fc.box(fx - 0.19, fx + 0.19, 5.60, 5.63, zr + zz, zr + zz + 0.02)
    fc.build("Garage_FoldingChair", [M['fs_wood_chair']])
    mt = MB()
    mt.box(4.10, 5.30, 5.55, 6.27, zr, zr + 0.01)
    mt.build("Garage_ShoeMat", [M['fs_mat']])
    sh_ = MB()
    for k in range(4):
        x_ = 4.95 + 0.14 * k
        sh_.rbox(x_ - 0.05, x_ + 0.05, 5.70, 5.98, zr + 0.01, zr + 0.10, r=0.03, mi=k // 2)
    sh_.build("Garage_Shoes", [M['fs_plastic_white'], M['fs_black_plastic']], smooth=True)
    sm = MB()
    sm.cylinder(0.46, 5.46, zr, zr + 0.30, 0.055, 0.045, seg=14, mi=0)                                     # yellow bottle
    sm.cylinder(0.46, 5.46, zr + 0.30, zr + 0.36, 0.022, seg=10, mi=0)
    sm.rbox(0.52, 0.80, 5.50, 5.72, zr + 0.18, zr + 0.22, r=0.01, mi=3)                                   # blue step stool
    for (dx, dy) in ((0.0, 0.0), (0.24, 0.0), (0.0, 0.18), (0.24, 0.18)):
        sm.box(0.54 + dx, 0.56 + dx, 5.52 + dy, 5.54 + dy, zr, zr + 0.18, 3)
    for (dx, dz) in ((0.0, 0.0), (0.0, 0.26)):                                                             # wooden step chair
        sm.box(0.86 + dx, 1.16 + dx, 5.72, 5.98, zr + dz + 0.24, zr + dz + 0.27, 1)
    for (dx, dy) in ((0.0, 0.0), (0.28, 0.0), (0.0, 0.24), (0.28, 0.24)):
        sm.box(0.87 + dx, 0.89 + dx, 5.73 + dy, 5.75 + dy, zr, zr + 0.52 + (0.40 if dy > 0 else 0.0), 1)
    sm.cylinder(3.10, 6.08, zr, zr + 0.30, 0.10, 0.09, seg=18, mi=2)                                        # water jug
    sm.cylinder(3.10, 6.08, zr + 0.30, zr + 0.36, 0.03, seg=10, mi=2)
    sm.build("Garage_Clutter", [M['fs_ball_yellow'], M['fs_wood_chair'], M['fs_clear_tote'], M['fs_stool_blue']], smooth=True)
    # front-left corner (24): the aluminium extension ladder leaning on the front wall, seen almost edge-on (foot
    # (0.42, 0.67), a rail point (0.35, 0.41, 1.48)), a hose reel with green hose face-on to the camera (centre
    # (-0.25, 0.90, ~0)), a leaf blower and garden tools, the green bin
    ld = MB()
    foot = (0.42, 0.67, zfl(0.67))
    top = (0.32, BWT + 0.05, 2.19)
    rd = (-0.993, 0.116)
    fs.extension_ladder(ld, foot, top, rd, span=0.40, fly=0.10)
    ld.build("Garage_Ladder", [M['steel']])
    hr = MB()
    fs.hose_reel(hr, 0, 1, 2)
    fs.place(hr.build("Garage_HoseReel", [M['fs_plastic_white'], M['fs_hose_green'], M['fs_grey_plastic']], smooth=True), -0.33, 0.92, zfl(0.9), 0.0)
    bl = MB()
    bl.rbox(-0.30, 0.05, 0.40, 0.65, zfl(0.5), zfl(0.5) + 0.32, r=0.05)
    bl.tube((-0.1, 0.5, zfl(0.5) + 0.25), (0.2, 0.3, zfl(0.5) + 0.7), 0.03, 0.02, seg=8)
    bl.build("Garage_Blower", [M['fs_mower_red']], smooth=True)
    gt = MB()
    rng2 = random.Random(7)
    for k in range(6):
        x_ = wl + 0.12 + 0.07 * k
        gt.tube((x_ + 0.05, 0.40 + 0.03 * k, zfl(0.45)), (x_ - 0.02, BWT + 0.04, zfl(0.45) + 1.35 + rng2.uniform(-0.2, 0.2)), 0.012, 0.012, seg=5, mi=k % 2)
    gt.tube((wl + 0.35, 2.30, zf + 0.95), (0.20, 1.40, zf + 1.25), 0.016, 0.016, seg=6, mi=2)             # a rake handle
    gt.build("Garage_Tools", [M['fs_wood_chair'], M['steel'], M['fs_black_plastic']], smooth=True)
    gb = MB()
    gb.rbox(wl + 0.05, wl + 0.55, 0.85, 1.33, zfl(1.1), zfl(1.1) + 0.48, r=0.04)                          # 24: green tub below the panel
    gb.box(wl + 0.555, wl + 0.56, 1.02, 1.14, zfl(1.1) + 0.26, zfl(1.1) + 0.34, 1)
    if 'fs_green_bin' not in M:
        M['fs_green_bin'] = _mm.new_mat("FS_GreenBin", (0.05, 0.16, 0.07, 1), rough=0.5)
    gb.build("Garage_GreenBin", [M['fs_green_bin'], M['fs_cardboard']], smooth=True)
    # right side of the frame (24: copy-paper cases on the slab at (5.2-5.5, 3.55-3.7), a tan box on them, a wire shelf
    # with a blue tote against the house wall behind them)
    wr = gx1
    if 'fs_paper_box' not in M:
        M['fs_paper_box'] = _mm.new_mat("FS_CopyPaperBox", (0.62, 0.10, 0.08, 1), rough=0.6)
    zq = zfl(3.7)
    rb2 = MB()
    rb2.box(5.10, 5.56, 3.52, 3.82, zq, zq + 0.19, 0)                     # (24: the stack is 100 px tall at 2.6 m -> 0.37 m)
    rb2.box(5.11, 5.55, 3.53, 3.81, zq + 0.19, zq + 0.38, 0)
    rb2.box(5.16, 5.46, 3.56, 3.80, zq + 0.38, zq + 0.55, 1)
    rb2.box(5.22, 5.34, 3.555, 3.56, zq + 0.44, zq + 0.50, 2)
    rb2.blob((5.35, 3.70, zq + 0.60), 0.13, seg=12, rings=8, jitter=0.2, seed=8, mi=3, squash=0.6, rx=1.3)
    rb2.build("Garage_RightStack", [M['fs_paper_box'], M['fs_cardboard'], M['fs_plastic_white'], M['fs_clear_tote']], smooth=True)
    rk = MB()
    for (xx, yy) in ((wr - 0.45, 3.90), (wr - 0.05, 3.90), (wr - 0.45, 4.35), (wr - 0.05, 4.35)):
        rk.cylinder(xx, yy, zq, zq + 1.80, 0.012, seg=6)
    for zz in (0.15, 0.60, 1.05, 1.50):
        rk.box(wr - 0.46, wr - 0.04, 3.89, 4.36, zq + zz, zq + zz + 0.02)
    rk.build("Garage_WireShelf", [M['steel']])
    rt = MB()
    rt.rbox(wr - 0.44, wr - 0.06, 3.92, 4.33, zq + 0.62, zq + 0.92, r=0.02, mi=0)
    rt.rbox(wr - 0.44, wr - 0.06, 3.92, 4.33, zq + 1.07, zq + 1.35, r=0.02, mi=1)
    rt.rbox(wr - 0.40, wr - 0.10, 3.95, 4.30, zq + 0.17, zq + 0.45, r=0.02, mi=2)
    rt.build("Garage_ShelfTotes", [M['fs_tote_blue'], M['fs_clear_tote'], M['fs_grey_plastic']], smooth=True)
    tl = MB()
    tl.cylinder(wl + 0.40, 5.95, zr + 1.45, zr + 1.47, 0.12, seg=16)
    tl.cylinder(wl + 0.40, 5.95, zr + 1.47, zr + 1.95, 0.012, seg=8)
    tl.lathe(wl + 0.40, 5.95, zr + 1.95, [(0.02, 0.0), (0.16, 0.10), (0.15, 0.11), (0.018, 0.012)], seg=20)
    tl.build("Garage_Torchiere", [M['fs_plastic_white']], smooth=True)
    sign = MB()
    sign.box(5.62, 5.78, ybk - 0.034, ybk - 0.03, zf + 1.46, zf + 1.56)
    sign.build("Garage_Sign", [M['fs_paper_box']])
    st.build("Garage_Storage", [M['fs_steel_grey']])
    box.build("Garage_ShelfBoxes", [M['fs_cardboard']])
    # porcelain keyless fixtures + the opener lamp; soft fill. Photo 24 is lit by daylight through the open door: EXT's
    # p24 sun (requested: toward-sun (0.10, -0.54, 0.84), energy x1.3 - the eave's shadow edge falls on the slab at y 1.25)
    # makes the sun patch + its bounce; these fills were balanced with it (patches 0.93-1.06 of the photo, back slab 1.18)
    lamp = MB()
    for (x, y) in ((0.6, 2.2), (4.4, 4.6)):
        lamp.cylinder(x, y, zt_ - 0.05, zt_, 0.06, seg=12, mi=0)
        lamp.sphere((x, y, zt_ - 0.10), 0.05, seg=12, rings=8, mi=1)
    lamp.build("Garage_Lamps", [M['ceramic'], M['frosted']])
    add_light("L_Garage_Bulb", 'POINT', (4.4, 4.6, zt_ - 0.14), 25, color=(1.0, 0.92, 0.80), size=0.06, coll=LC)
    area_light("L_Garage_Fill", ((gx0 + gx1) / 2, (BWT + ybk) / 2, zt_ - 0.05), (5.0, 4.4), 70, color=(1.0, 0.97, 0.94), coll=LC)
    area_light("L_Garage_FillUp", ((gx0 + gx1) / 2, (BWT + ybk) / 2, zf + 0.12), (5.5, 4.8), 80, color=(1.0, 0.95, 0.88), down=False, coll=LC)   # warm: the sunlit slab bounce


# ================================================================ fill lights
def lights_front(M):
    """Soft fill standing in for the listing photos' daylight bounce: per room a weak large area light under the ceiling
    pointing down and a stronger one 0.85 m below the ceiling pointing UP with a 90 deg spread - it lights the ceiling,
    whose bounce lights walls and furniture evenly (the HDR listing look) without a hard cut-off line on the walls and
    without over-lighting the furniture tops / fronts (a floor-level up-light did that).  Living / foyer / stair-foot /
    hall re-balanced after INT_GREAT's knockdown ceiling (up x0.70, down x1.15): same-surface patches through the solved
    cameras - ceilings 0.97-1.03 (06 over the stair 1.10), carpet medians 0.98-1.02, walls unchanged (0.81-1.10)."""
    k = float(os.environ.get('FRONT_FILL', '1.0'))
    ku = float(os.environ.get('FRONT_FILL_UP', '1.0'))          # tuning aids: scale only the up / down fills
    kd = float(os.environ.get('FRONT_FILL_DN', '1.0'))
    for (name, rect, e_up, e_dn) in (("Living", (WALL_END_X + 0.05, XR - 0.15, LIV_Y0 + 0.1, ST_Y0 - 0.15), 38, 60),
                                     ("Foyer", (FOYER_WX + 0.1, WALL_END_X - 0.1, DOOR_Y + 0.1, COAT_Y1_), 10.5, 26.5),
                                     ("StairFoot", (HALL_X[1] + 0.1, ST_X0 - 0.05, COAT_Y1_, ST_YM - 0.1), 10, 16),
                                     ("Hall", (6.05, 7.15, 3.9, 6.4), 7, 11.5), ("Powder", (PW['x0'] + 0.1, PW['x1'] - 0.1, PW['y0'] + 0.1, PW['y1'] - 0.1), 8, 11)):
        x0, x1, y0, y1 = rect
        c = ((x0 + x1) / 2, (y0 + y1) / 2)
        area_light(f"L_FillUp_{name}", (c[0], c[1], ZC - 0.85), ((x1 - x0) * 0.9, (y1 - y0) * 0.9), e_up * k * ku, color=(0.97, 0.98, 1.0),
                   down=False, coll=LC, spread=math.radians(90))
        area_light(f"L_Fill_{name}", (c[0], c[1], ZC - 0.06), ((x1 - x0) * 0.85, (y1 - y0) * 0.85), e_dn * k * kd, color=(1.0, 0.97, 0.94), coll=LC)


# ================================================================ per-photo state (house.before_render calls this)
PHOTO_STATE = {
    # powder door: closed in 05 / 06 (the door beside the stair's first riser), open in 07 (taken from the doorway)
    # (a negative angle swings the leaf the other way from its build-time rest: the door swings OUT - its hinges show on
    # the hall side in 05, and 07, shot from the doorway, shows the bare west wall with the switch plate, no leaf)
    'p05': dict(powder=0.0), 'p06': dict(powder=0.0), 'p07': dict(powder=-95.0),
    # garage: the sectional door is up in 24; the closed exterior door is hidden for that view only
    'p24': dict(garage_open=True),
}


def before_render(S, name):
    import bpy
    st = PHOTO_STATE.get(name, {})
    leaf = bpy.data.objects.get("Door_Powder_Leaf")
    if leaf is not None:
        if '_rest' not in leaf:
            leaf['_rest'] = tuple(leaf.rotation_euler)
        rz = leaf['_rest'][2]
        if 'powder' in st:
            ang = math.radians(abs(st['powder']))
            rz = (math.copysign(ang, rz) if abs(rz) > 1e-6 else ang) * (1 if st['powder'] >= 0 else -1)
        leaf.rotation_euler = (leaf['_rest'][0], leaf['_rest'][1], rz)
    op = st.get('garage_open', False)
    for ob in bpy.data.objects:
        if ob.name == "GarageOpenDoor":
            ob.hide_render = not op
        elif ob.name.startswith("Garage_Door") and ob.type == 'MESH':
            ob.hide_render = op


def build(M):
    fs.mats(M)
    floors_front(M)
    stair(M)
    living(M)
    foyer(M)
    powder(M)
    garage(M)
    lights_front(M)
