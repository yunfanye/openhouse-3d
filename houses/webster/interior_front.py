"""Front rooms of 1836 Webster: living room (photos 01/02), entry + the enclosed stair (15), dining room (03/04).

Finishes (floors, crown + base mouldings), built-ins (tiled fireplace + mantel, bookcase wall), the carpeted stair
with its white wrought-iron rail, staging furniture, art and the room lights.  Walls / window + door units / arch
heads / slabs / the main ceiling are exterior.py's.  Reads positions from plan.py only.
"""
import math, random
from .plan import *
from archviz.mesh import *
from archviz.lights import *
from archviz.parts import *
from archviz import materials as _mat
from archviz import plants as _pl
from .interior_back import _pillows, _register, _switch, _framed_art, _smoke_detector

K30 = (1.0, 0.84, 0.66)          # 3000 K lamps
_L = {}


def _local(M):
    if _L:
        return _L
    _L['firebrick'] = _mat.noise_mat("Firebrick", (0.06, 0.05, 0.045, 1), (0.14, 0.11, 0.09, 1), scale=30, bump=0.4, rough=0.95)
    _L['lemon'] = _mat.new_mat("Lemon", (0.95, 0.80, 0.10, 1), rough=0.45, coat=0.3)
    _L['book1'] = _mat.new_mat("BookNavy", (0.06, 0.09, 0.20, 1), rough=0.8)
    _L['book2'] = _mat.new_mat("BookRust", (0.45, 0.16, 0.08, 1), rough=0.8)
    _L['book3'] = _mat.new_mat("BookCream", (0.80, 0.74, 0.60, 1), rough=0.85)
    _L['book4'] = _mat.new_mat("BookOlive", (0.20, 0.26, 0.12, 1), rough=0.8)
    _L['book5'] = _mat.new_mat("BookCharcoal", (0.10, 0.10, 0.10, 1), rough=0.8)
    _L['ember'] = _mat.new_mat("EmberBed", (0.15, 0.05, 0.02, 1), rough=0.6, emit=(1.0, 0.35, 0.08, 1), emit_str=4.0)
    _L['fire'] = _mat.fire("FireFront")
    for n in _L['fire'].node_tree.nodes:
        if n.type == 'EMISSION':
            n.inputs["Strength"].default_value = 6.0
    _L['bulb'] = _mat.new_mat("BulbWarm", (1, 0.85, 0.6, 1), emit=(1.0, 0.78, 0.5, 1), emit_str=14.0)
    _L['bowl_glass'] = _mat.new_mat("BowlGlass", (0.9, 0.95, 0.93, 1), rough=0.05, transmission=0.9, ior=1.45)
    _L['mesh'] = _mat.new_mat("FireScreenMesh", (0.03, 0.03, 0.03, 1), rough=0.6, metal=0.4, alpha=0.42)
    _L['coir'] = _mat.fabric("CoirMatF", (0.55, 0.42, 0.25, 1), weave=160, bump=0.7)
    _L['plate'] = _mat.new_mat("SwitchPlateF", (0.92, 0.92, 0.90, 1), rough=0.35, coat=0.2)
    _L['register'] = _mat.new_mat("RegisterBrownF", (0.30, 0.26, 0.22, 1), rough=0.5, metal=0.3)
    _L['candle'] = _mat.new_mat("CandleIvory", (0.93, 0.90, 0.80, 1), rough=0.5, subsurface=0.3)
    _L['clock_face'] = _mat.new_mat("ClockFace", (0.95, 0.94, 0.90, 1), rough=0.6)
    _L['deco_green'] = _mat.tiles("DecoGreenYZ", (0.22, 0.42, 0.34, 1), grout=(0.70, 0.66, 0.58, 1), size=(0.1, 0.1), gap=0.004, rough=0.2,
                                  variation=0.25, mottle=0.8, bump=0.25, coat=0.6, plane='YZ')
    _L['mat_white'] = _mat.new_mat("ArtMatF", (0.95, 0.94, 0.91, 1), rough=0.7)
    _L['rug_border'] = _mat.rug("RugBorder", (0.50, 0.46, 0.40, 1), (0.60, 0.56, 0.50, 1))
    _L['throw_knit'] = _mat.fabric("ThrowKnit", (0.80, 0.72, 0.58, 1), weave=30, bump=0.5)
    return _L


# ---------------------------------------------------------------- trim helpers
def _crown_x(mb, a0, a1, b, s, zc, mi, h=0.075, d=0.07):
    """Cove crown along X on the wall face at plane y=b; s=+1 if the room lies on the +Y side of the face."""
    if a1 - a0 < 0.02:
        return
    P = [(b, zc - h), (b + s * 0.025, zc - h), (b + s * d, zc), (b, zc)]
    mb.hexa([(a0, y, z) for (y, z) in P] + [(a1, y, z) for (y, z) in P], mi)


def _crown_y(mb, a0, a1, b, s, zc, mi, h=0.075, d=0.07):
    """Cove crown along Y on the wall face at plane x=b; s=+1 if the room lies on the +X side."""
    if a1 - a0 < 0.02:
        return
    P = [(b, zc - h), (b + s * 0.025, zc - h), (b + s * d, zc), (b, zc)]
    mb.hexa([(x, a0, z) for (x, z) in P] + [(x, a1, z) for (x, z) in P], mi)


def _gaps(along, b_lo, b_hi, a0, a1):
    """Floor-level openings (doors / arches) in the wall plane range -> (a0, a1) gaps for the baseboard."""
    out = []
    for o in OPENINGS:
        if o['along'] == along and b_lo <= o['b'] <= b_hi and o['z0'] < 0.05 and o['a1'] > a0 and o['a0'] < a1:
            out.append((max(a0, o['a0'] - 0.05), min(a1, o['a1'] + 0.05)))
    return sorted(out)


def _segments(a0, a1, gaps):
    cur = a0
    for (g0, g1) in gaps:
        if g0 > cur:
            yield cur, g0
        cur = max(cur, g1)
    if a1 > cur:
        yield cur, a1


def room_trims(mb, room, zc, mi, sides='WESN', base_h=0.12, base_d=0.015, crown=True):
    """Crown + baseboard on the given sides of an interior room rect (x0, x1, y0, y1), skipping door openings."""
    x0, x1, y0, y1 = room[:4]
    zf = room[4] if len(room) > 4 else 0.0
    if 'W' in sides:
        gaps = _gaps('Y', x0 - 0.36, x0 + 0.05, y0, y1)
        for (g0, g1) in _segments(y0, y1, gaps):
            mb.box(x0, x0 + base_d, g0, g1, zf, zf + base_h, mi)
        if crown: _crown_y(mb, y0, y1, x0, +1, zc, mi)
    if 'E' in sides:
        gaps = _gaps('Y', x1 - 0.05, x1 + 0.36, y0, y1)
        for (g0, g1) in _segments(y0, y1, gaps):
            mb.box(x1 - base_d, x1, g0, g1, zf, zf + base_h, mi)
        if crown: _crown_y(mb, y0, y1, x1, -1, zc, mi)
    if 'S' in sides:
        gaps = _gaps('X', y0 - 0.36, y0 + 0.05, x0, x1)
        for (g0, g1) in _segments(x0, x1, gaps):
            mb.box(g0, g1, y0, y0 + base_d, zf, zf + base_h, mi)
        if crown: _crown_x(mb, x0, x1, y0, +1, zc, mi)
    if 'N' in sides:
        gaps = _gaps('X', y1 - 0.05, y1 + 0.36, x0, x1)
        for (g0, g1) in _segments(x0, x1, gaps):
            mb.box(g0, g1, y1 - base_d, y1, zf, zf + base_h, mi)
        if crown: _crown_x(mb, x0, x1, y1, -1, zc, mi)


def _disc_x(mb, x, cy, cz, r, t, mi, seg=28):
    """Thin disc in the YZ plane (mirror / canopy), thickness t toward -X."""
    ring0 = [(x, cy + r * math.cos(2 * math.pi * i / seg), cz + r * math.sin(2 * math.pi * i / seg)) for i in range(seg)]
    ring1 = [(x - t, y, z) for (_, y, z) in ring0]
    b = len(mb.v)
    mb.v.extend(ring0 + ring1)
    fs = [tuple(b + i for i in range(seg)), tuple(b + seg + i for i in reversed(range(seg)))]
    for i in range(seg):
        j = (i + 1) % seg
        fs.append((b + i, b + j, b + seg + j, b + seg + i))
    mb.f.extend(fs); mb.fm.extend([mi] * len(fs))


def _book_row(mb, x0, x1, y0, y1, z, mis, rng, h_lo=0.18, h_hi=0.30, lean_last=True):
    """A row of upright books between x0..x1 standing on z, spines toward -Y."""
    x = x0
    while x < x1 - 0.02:
        w = rng.uniform(0.018, 0.045)
        if x + w > x1:
            break
        h = rng.uniform(h_lo, h_hi)
        d = rng.uniform(0.14, 0.2)
        mb.box(x, x + w, y1 - d, y1 - 0.01, z, z + h, rng.choice(mis))
        x += w + rng.uniform(0.0, 0.004)


def _glass(mb, x, y, z, kind='decanter', mi=0):
    if kind == 'decanter':
        mb.lathe(x, y, z, [(0, 0), (0.06, 0), (0.08, 0.05), (0.065, 0.14), (0.022, 0.2), (0.02, 0.28), (0.028, 0.3), (0.0, 0.3)], seg=16, mi=mi)
    elif kind == 'wine':
        mb.lathe(x, y, z, [(0, 0), (0.035, 0), (0.035, 0.005), (0.004, 0.006), (0.004, 0.09), (0.03, 0.11), (0.036, 0.16), (0.028, 0.21), (0.0, 0.21)], seg=14, mi=mi)
    else:
        mb.lathe(x, y, z, [(0, 0), (0.036, 0), (0.04, 0.09), (0.0, 0.09)], seg=12, mi=mi)


# ---------------------------------------------------------------- living room
def living(M):
    """Photo 01: the fireplace is at the FRONT end of the -X wall - an interior chimney breast (plan.CHIMNEY) with a
    cream 8" tile surround + green deco border, a raised tiled hearth and a white mantel on corbels, brass sconces
    flanking; the small window LivW1 right of it; the built-in alcove bay (shelves + chalkboard) behind the cased
    opening LivAlcove.  Staged: a sofa facing the fire, an armchair by the small window, a fiddle-leaf fig in the
    +Y/+X corner, the film sweep corridor (x -4.0..-1.4, y 2.4..3.7) kept clear."""
    L = _local(M)
    R = ROOMS['living']
    x0, x1, y0, y1 = R[:4]
    cx0, cx1, cy0, cy1, _ctop = -5.75, FIREPLACE_FACE, CHIMNEY[2], CHIMNEY[3], CHIMNEY[4]
    # floor (living + the alcove bay, both carpet)
    mb = MB(); mb.plate(x0, x1, y0, y1, 0.0, 0.015, holes=[(-5.5,-4.05,4.45,5.75)])
    mb.build("Front_LivFloor", [M['carpet']])
    # trims: the room, then the crown / base returning round the chimney breast
    mb = MB(); room_trims(mb, R, Z_MC, 0)
    mb.build("Front_LivTrim", [M['trim']])

    # ---- chimney breast: painted mass floor to ceiling; firebox recessed into its +X face
    FX, FY0, FY1, FZ0, FZ1, FD = cx1, (cy0 + cy1) / 2 - 0.375, (cy0 + cy1) / 2 + 0.375, 0.2, 0.9, 0.45     # opening 0.75 x 0.7
    mb = MB()   # 0 wall paint, 1 firebrick, 2 tile cream (YZ), 3 deco green (YZ), 4 hearth tile (H), 5 trim, 6 black metal, 7 bark, 8 ember
    mb.wall('Y', cy0, cy1, cx0, cx1, 0.0, 1.34, holes=[(FY0, FY1, FZ0, FZ1)], mi=0)
    mb.box(FX - FD, FX - FD + 0.015, FY0, FY1, FZ0, FZ1, 1)                                             # firebox back
    mb.box(FX - FD, FX, FY0, FY0 + 0.015, FZ0, FZ1, 1); mb.box(FX - FD, FX, FY1 - 0.015, FY1, FZ0, FZ1, 1)
    mb.box(FX - FD, FX, FY0, FY1, FZ1 - 0.015, FZ1, 1); mb.box(FX - FD, FX, FY0, FY1, FZ0, FZ0 + 0.015, 1)
    # tile surround on the breast face: cream 8" field, green deco border round the opening, up to the mantel
    mb.wall('Y', cy0 + 0.01, cy1 - 0.01, FX, FX + 0.012, FZ0, 1.32, holes=[(FY0 - 0.1, FY1 + 0.1, FZ0, FZ1 + 0.1)], mi=2)
    mb.wall('Y', FY0 - 0.1, FY1 + 0.1, FX + 0.004, FX + 0.016, FZ0, FZ1 + 0.1, holes=[(FY0, FY1, FZ0, FZ1)], mi=3)
    # raised tiled hearth projecting past the breast
    mb.box(FX, FX + 0.45, (cy0 + cy1) / 2 - 0.75, (cy0 + cy1) / 2 + 0.75, 0.0, 0.18, 2)
    mb.box(FX - 0.01, FX + 0.45, (cy0 + cy1) / 2 - 0.75, (cy0 + cy1) / 2 + 0.75, 0.18, 0.2, 4)
    # white mantel shelf on two corbels
    mb.box(FX, FX + 0.2, cy0 - 0.05, cy1 + 0.05, 1.36, 1.43, 5)
    mb.box(FX, FX + 0.04, cy0 - 0.03, cy1 + 0.03, 1.32, 1.36, 5)
    for yy in (cy0 + 0.05, cy1 - 0.15):
        mb.hexa([(FX, yy, 1.2), (FX + 0.02, yy, 1.2), (FX + 0.02, yy + 0.1, 1.2), (FX, yy + 0.1, 1.2),
                 (FX, yy, 1.32), (FX + 0.15, yy, 1.32), (FX + 0.15, yy + 0.1, 1.32), (FX, yy + 0.1, 1.32)], 5)
    # grate, andirons, logs, embers
    for i in range(4):
        yy = FY0 + 0.15 + i * 0.15
        mb.box(FX - 0.38, FX - 0.08, yy - 0.008, yy + 0.008, FZ0 + 0.03, FZ0 + 0.1, 6)
    mb.box(FX - 0.38, FX - 0.08, FY0 + 0.1, FY1 - 0.1, FZ0 + 0.015, FZ0 + 0.035, 6)
    for yy in (FY0 + 0.1, FY1 - 0.1):
        mb.cylinder(FX - 0.1, yy, FZ0, FZ0 + 0.3, 0.012, seg=8, mi=6); mb.sphere((FX - 0.1, yy, FZ0 + 0.32), 0.025, seg=10, rings=6, mi=6)
    mb.tube((FX - 0.32, FY0 + 0.1, FZ0 + 0.14), (FX - 0.32, FY1 - 0.1, FZ0 + 0.14), 0.04, 0.04, seg=10, mi=7)
    mb.tube((FX - 0.18, FY0 + 0.12, FZ0 + 0.14), (FX - 0.18, FY1 - 0.12, FZ0 + 0.14), 0.035, 0.035, seg=10, mi=7)
    mb.tube((FX - 0.25, FY0 + 0.15, FZ0 + 0.21), (FX - 0.25, FY1 - 0.15, FZ0 + 0.21), 0.035, 0.035, seg=10, mi=7)
    rng = random.Random(7)
    for i in range(14):
        mb.blob((FX - rng.uniform(0.1, 0.36), rng.uniform(FY0 + 0.08, FY1 - 0.08), FZ0 + 0.035), rng.uniform(0.012, 0.022), seg=6, rings=4, jitter=0.3, seed=i, mi=8, squash=0.6)
    # fire screen on the hearth, tool set at the hearth's +Y end, mantel objects (clock, candlesticks)
    mb.frame(FX + 0.03, FX + 0.05, FY0 - 0.06, FY1 + 0.06, FZ0, FZ1 + 0.03, 0.02, mi=6, axis='X')
    mb.box(FX + 0.038, FX + 0.042, FY0 - 0.04, FY1 + 0.04, FZ0 + 0.02, FZ1 + 0.01, 9)
    mb.box(FX + 0.03, FX + 0.05, FY0 - 0.06, FY1 + 0.06, (FZ0 + FZ1) / 2, (FZ0 + FZ1) / 2 + 0.015, 6)
    for yy in (FY0 - 0.04, FY1 + 0.04):
        mb.box(FX + 0.0, FX + 0.1, yy - 0.01, yy + 0.01, FZ0, FZ0 + 0.015, 6)
    tx, ty = FX + 0.2, (cy0 + cy1) / 2 + 0.95
    mb.lathe(tx, ty, 0.0, [(0, 0), (0.09, 0), (0.09, 0.012), (0.012, 0.015), (0.012, 0.62), (0.03, 0.64), (0, 0.64)], seg=12, mi=6)
    for k, ang in enumerate((0.0, 2.1, 4.2)):
        px, py = tx + 0.05 * math.cos(ang), ty + 0.05 * math.sin(ang)
        mb.cylinder(px, py, 0.03, 0.6, 0.005, seg=6, mi=6)
        mb.tube((px, py, 0.6), (tx + 0.035 * math.cos(ang), ty + 0.035 * math.sin(ang), 0.625), 0.006, 0.004, seg=6, mi=6)
        if k == 0:
            mb.box(px - 0.03, px + 0.03, py - 0.004, py + 0.004, 0.03, 0.09, 6)
        elif k == 1:
            mb.tube((px, py, 0.03), (px + 0.03, py, 0.06), 0.004, 0.003, seg=6, mi=6)
    mc = (cy0 + cy1) / 2
    mb.tube((FX + 0.06, mc, 1.53), (FX + 0.1, mc, 1.53), 0.085, 0.085, seg=24, mi=6)
    mb.tube((FX + 0.1, mc, 1.53), (FX + 0.104, mc, 1.53), 0.075, 0.075, seg=24, mi=10)
    mb.box(FX + 0.04, FX + 0.13, mc - 0.04, mc + 0.04, 1.43, 1.45, 6)
    for yy in (cy0 + 0.12, cy1 - 0.12):
        mb.lathe(FX + 0.1, yy, 1.43, [(0, 0), (0.035, 0), (0.035, 0.012), (0.012, 0.02), (0.012, 0.2), (0.02, 0.22), (0.018, 0.24), (0, 0.24)], seg=14, mi=11)
        mb.cylinder(FX + 0.1, yy, 1.67, 1.87, 0.012, seg=10, mi=12)
        mb.cylinder(FX + 0.1, yy, 1.87, 1.895, 0.003, 0.001, seg=6, mi=13)
    mb.build("Front_Fireplace", [M['wall'], L['firebrick'], M['tile_fire'], L['deco_green'], M['tile_fire_h'], M['trim'], M['black_metal'], M['bark'], L['ember'],
                                 L['mesh'], L['clock_face'], M['brass'], L['candle'], L['bulb']])
    # flames (own object: the fire shader grades along the object's Generated Z)
    mb = MB()
    rng = random.Random(3)
    for i in range(36):
        px = FX - rng.uniform(0.1, 0.36)
        py = rng.uniform(FY0 + 0.08, FY1 - 0.08)
        h = rng.uniform(0.07, 0.26) * (1.0 if rng.random() < 0.7 else 0.5)
        r0 = rng.uniform(0.018, 0.04)
        mb.cylinder(px, py, FZ0 + 0.05, FZ0 + 0.05 + h * 0.55, r0, r0 * 0.6, seg=7, rot=rng.uniform(0, 1))
        mb.cylinder(px + rng.uniform(-0.01, 0.01), py + rng.uniform(-0.015, 0.015), FZ0 + 0.05 + h * 0.5, FZ0 + 0.05 + h, r0 * 0.6, 0.003, seg=7)
    mb.build("Front_Fire", [L['fire']], smooth=True)
    add_light("L_Front_Fire", 'POINT', (FX - 0.2, mc, FZ0 + 0.28), 25, (1.0, 0.5, 0.2), size=0.1)
    # art over the mantel, brass sconces flanking the breast on the -X wall (photo 01: small capped boxes)
    mb = MB()
    _framed_art(mb, 'Y', mc - 0.42, mc + 0.42, FX, +1, 1.55, 2.25, 0, 1, 2)
    mb.build("Front_LivArtSconces", [M['black'], L['mat_white'], M['art_abstract'], M['brass'], M['emit_warm']], smooth=True)

    from .fixtures import living_board
    living_board(M)

    # ---- furniture: sofa facing the fire (backing onto the front window wall), coffee table, armchair by the small window
    mb = MB()
    sofa(mb, -2.55, 1.45, 2.0, 0.9, rot=-math.pi / 2, mi_seat=0, mi_back=0, mi_base=0, cushion_gap=0.02, pillows=0)
    # Sewn scatter cushions are built separately by refinements.
    mb.rbox(-3.0, -2.1, 0.45, 0.5, 0.62, 0.655, r=0.012, mi=5, puff=0.5, seg=2)                                # knitted throw over the -Y arm
    mb.rbox(-2.9, -2.2, 0.47, 0.485, 0.655, 0.68, r=0.01, mi=5, puff=0.5, seg=2)
    mb.rbox(-2.9, -2.2, 0.42, 0.45, 0.3, 0.63, r=0.008, mi=5, seg=2)
    armchair(mb, -4.6, 4.00, rot=math.pi / 2 + 0.5, mi=2, mi_legs=3, style='barrel')
    mb.pillow_sq(-4.73, 4.10, 0.47, 0.42, 0.42, 0.13, 6, rot=math.pi / 2 + 0.6, pitch=math.pi / 2 - 0.4, seed=4)
    mb.build("Front_LivSeating", [M['fabric'], M['fabric_rust'], M['leather_tan'], M['walnut'], M['fabric_taupe'], L['throw_knit'], M['fabric_sand']], smooth=True, subsurf=1)
    mb = MB()
    round_table(mb, -3.65, 1.4, 0.0, 0.42, h=0.42, top_t=0.04, mi=0, mi_leg=0, legs='drum')
    mb.rcbox(-3.72, 1.32, 0.426, 0.36, 0.26, 0.012, r=0.005, mi=1)
    mb.frame(-3.9, -3.54, 1.19, 1.45, 0.432, 0.46, 0.012, mi=1, axis='Z')
    mb.cylinder(-3.82, 1.27, 0.432, 0.55, 0.035, seg=14, mi=2); mb.cylinder(-3.82, 1.27, 0.55, 0.575, 0.006, 0.001, seg=6, mi=3)
    mb.cylinder(-3.65, 1.39, 0.432, 0.51, 0.03, seg=14, mi=2); mb.cylinder(-3.65, 1.39, 0.51, 0.535, 0.006, 0.001, seg=6, mi=3)
    books(mb, -3.5, 1.62, 0.42, n=3, mi=4, rot=0.3, w=0.26, d=0.2)
    vase(mb, -3.5, 1.15, 0.42, h=0.16, r=0.055, mi=5, style='round')
    mb.build("Front_CoffeeTable", [M['walnut'], M['black_metal'], M['ceramic'], L['bulb'], M['book'], M['clay']], smooth=True)
    # rug under the seating group (woven border + fringe on the short ends)
    rx0, rx1, ry0, ry1 = -4.45, -1.8, 0.55, 2.35
    mb = MB(); mb.rbox(rx0, rx1, ry0, ry1, 0.017, 0.029, r=0.006, seg=2)
    mb.frame(rx0, rx1, ry0, ry1, 0.029, 0.0315, 0.12, mi=1, axis='Z')
    for xx in (rx0, rx1):
        n = int((ry1 - ry0) / 0.04)
        for k in range(n):
            yy = ry0 + 0.02 + 0.04 * k
            mb.box(xx - 0.035 if xx < -3 else xx, xx if xx < -3 else xx + 0.035, yy, yy + 0.012, 0.017, 0.021, 1)
    mb.build("Rug_Living", [M['rug_pale'], L['rug_border']], smooth=True)
    # side table + lamp beside the sofa's +Y end, floor lamp in the +Y/-X corner by the alcove, registers, switches, smoke detector
    mb = MB()
    _register(mb, -1.75, 4.65, 0.015, along='Y', mi=9)
    _register(mb, -4.6, 0.42, 0.015, along='X', mi=9)
    _switch(mb, 'Y', 3.85, -1.4, -1, 1.2, 10, n=2)
    _switch(mb, 'X', -1.6, 0.25, +1, 1.2, 10)
    _smoke_detector(mb, -3.2, 3.6, Z_MC, 10)
    mb.build("Front_Console", [M['walnut'], M['black_metal'], M['ceramic'], M['lampshade'], M['book'], M['clay'], M['plant_pot'], M['leaf_plant'], M['bark'],
                               L['register'], L['plate']], smooth=True)
    _pl.potted("Front_LivOlive", (-1.78, 0.58, 0.0), kind='olive', height=1.7, pot='ceramic', seed=4)
    mb = MB()
    mb.cylinder(-1.78, 4.90, 0.0, 0.03, 0.14, seg=20, mi=0)
    mb.cylinder(-1.78, 4.90, 0.03, 1.45, 0.012, seg=10, mi=0)
    mb.lathe(-1.78, 4.90, 1.42, [(0.16, 0), (0.2, 0.02), (0.2, 0.3), (0.17, 0.32), (0, 0.32)], seg=22, mi=1)
    mb.build("Front_FloorLamp", [M['brass'], M['lampshade']], smooth=True)
    add_light("L_Front_FloorLamp", 'POINT', (-1.78, 4.90, 1.6), 18, K30, size=0.1)
    room_light("L_LivFill", 'living', energy=27, color=K30)


# ---------------------------------------------------------------- entry + stair
def _tread_z(y):
    """Top of the stair mass at y (flights + landing)."""
    if y < STAIR_F1[0]:
        return 0.0
    if y < STAIR_F1[1]:
        i = int((y - STAIR_F1[0]) / ((STAIR_F1[1] - STAIR_F1[0]) / 8))
        return (min(i, 7) + 1) * RISER
    if y < STAIR_F2[0]:
        return 8 * RISER
    if y < STAIR_F2[1]:
        i = int((y - STAIR_F2[0]) / ((STAIR_F2[1] - STAIR_F2[0]) / 9))
        return 8 * RISER + (min(i, 8) + 1) * RISER
    return Z_UP


def _rail_z(y, h=0.9):
    """Handrail height: a straight line over the nosings of each flight, flat over the landing."""
    if y <= STAIR_F1[1]:
        t = max(0.0, (y - STAIR_F1[0]) / (STAIR_F1[1] - STAIR_F1[0]))
        return RISER + t * 7 * RISER + h
    if y <= STAIR_F2[0]:
        return 8 * RISER + h
    t = (y - STAIR_F2[0]) / (STAIR_F2[1] - STAIR_F2[0])
    return 8 * RISER + t * 9 * RISER + h


def entry_stair(M):
    L = _local(M)
    R = ROOMS['entry']
    x0, x1, y0, y1 = R[:4]
    mb = MB(); mb.plate(x0, x1, y0, y1, 0.0, 0.015, holes=[(-5.5,-4.05,4.45,5.75)])
    mb.build("Front_EntryFloor", [M['tile_entry']])
    # the front part (y0..ENTRY_VEST_Y1) is a low vestibule under the shed roof: dropped ceiling at ENTRY_VEST_ZC with a
    # cove, a cased soffit face at y = ENTRY_VEST_Y1 up to the main ceiling; crown at 2.45 there, at Z_MC behind
    vy, vz = ENTRY_VEST_Y1, ENTRY_VEST_ZC
    mb = MB()
    room_trims(mb, (x0, x1, y0, vy), vz, 0, sides='WES')
    _crown_x(mb, x0, x1, vy - 0.03, -1, vz, 0)                                                       # crown returns along the soffit, vestibule side
    room_trims(mb, (x0, x1, vy, y1), Z_MC, 0, sides='WE')
    _crown_x(mb, x0, x1, vy, +1, Z_MC, 0)                                                            # crown along the step, main-ceiling side
    mb.box(x0 - 0.01, x1 + 0.01, vy - 0.03, vy, vz, Z_MC, 1)                                          # plastered soffit face (the ceiling step)
    # baseboards continue along the stair well walls at the entry's rear (visible from the entry)
    mb.box(STAIR_X0, STAIR_X0 + 0.015, y1 - 0.02, y1, 0.0, 0.12, 0)
    mb.build("Front_EntryTrim", [M['trim'], M['wall']])
    mb = MB()   # 0 ceiling, 1 trim, 2 brass, 3 glow
    mb.box(x0 - 0.01, x1 + 0.01, y0 - 0.01, vy, vz, vz + 0.06, 0)                                    # dropped ceiling (hides the roof wedge above)
    mb.lathe((x0 + x1) / 2, (y0 + vy) / 2, vz, [(0, 0), (0.11, 0), (0.11, -0.03), (0.09, -0.03), (0.09, -0.02), (0, -0.02)], seg=20, mi=2)   # flush canopy
    mb.lathe((x0 + x1) / 2, (y0 + vy) / 2, vz - 0.03, [(0, 0), (0.09, 0), (0.1, -0.05), (0.06, -0.09), (0, -0.1)], seg=20, mi=3)              # glass dome
    mb.build("Front_EntryVestCeiling", [M['ceiling'], M['trim'], M['brass'], M['emit_warm']], smooth=True)
    add_light("L_Front_Vestibule", 'POINT', ((x0 + x1) / 2, (y0 + vy) / 2, vz - 0.2), 25, K30, size=0.08)
    # runner, console + round mirror, semi-flush fixture
    mb = MB(); mb.rbox(-0.45, 0.25, 2.7, 4.5, 0.017, 0.028, r=0.005, seg=2)
    mb.build("Rug_Entry", [M['rug_plum']], smooth=True)
    mb = MB()
    mb.box(0.62, 0.95, 3.9, 4.8, 0.76, 0.8, 0)
    for yy in (3.93, 4.77):
        for xx in (0.65, 0.92):
            mb.cbox(xx, yy, 0.38, 0.025, 0.025, 0.76, 1)
    vase(mb, 0.8, 4.15, 0.8, h=0.26, r=0.08, mi=2, style='tall')
    mb.box(0.605, 0.62, 4.0, 4.7, 0.65, 0.745, 0); mb.box(0.585, 0.605, 4.3, 4.4, 0.69, 0.7, 6)          # drawer front + pull
    mb.rbox(-0.72, 0.17, 0.3, 1.0, 0.015, 0.03, r=0.01, mi=8, seg=2)                                      # coir door mat just inside the front door
    _switch(mb, 'X', 0.5, 0.25, +1, 1.2, 9, n=2)
    _smoke_detector(mb, 0.0, 4.3, Z_MC, 9)
    books(mb, 0.78, 4.55, 0.8, n=2, mi=5, rot=0.0, w=0.22, d=0.18)
    _disc_x(mb, 1.045, 4.35, 1.55, 0.32, 0.02, 6)                                                  # mirror frame (brass ring look)
    _disc_x(mb, 1.02, 4.35, 1.55, 0.3, 0.004, 7)
    mb.build("Front_EntryConsole", [M['walnut'], M['black_metal'], M['ceramic'], M['bark'], M['leaf_plant'], M['book'], M['brass'], M['mirror'], L['coir'], L['plate']], smooth=True)
    _pl.stems("Front_EntryStems", (0.8, 4.15, 1.06), kind='olive', height=0.45, seed=2)
    mb = MB()
    mb.cylinder(0.0, 3.5, Z_MC - 0.02, Z_MC, 0.16, seg=24, mi=0)
    mb.cylinder(0.0, 3.5, Z_MC - 0.12, Z_MC - 0.02, 0.02, seg=10, mi=0)
    mb.lathe(0.0, 3.5, Z_MC - 0.34, [(0.0, 0.0), (0.14, 0.02), (0.19, 0.12), (0.17, 0.22), (0.03, 0.22)], seg=24, mi=1)
    mb.build("Front_EntryLight", [M['brass'], M['emit_warm']], smooth=True)
    add_light("L_Front_Entry", 'POINT', (0.0, 3.5, Z_MC - 0.42), 60, K30, size=0.12)
    room_light("L_EntryFill", 'entry', energy=14, color=K30)

    # ---- the stair (photo 15): flight 1, landing, flight 2 as carpeted solid masses
    sx0, sx1 = STAIR_X0 + 0.02, STAIR_X1 - 0.02
    mb = MB()
    stairs(mb, sx0, sx1, STAIR_F1[0], STAIR_F1[1], 0.0, 8 * RISER, n=8, mi=0, base=0.0)
    mb.box(sx0, sx1, STAIR_LAND[0], STAIR_LAND[1], 0.0, 8 * RISER, 0)
    stairs(mb, sx0, sx1, STAIR_F2[0], STAIR_F2[1], 8 * RISER, Z_UP, n=9, mi=0, base=8 * RISER)
    # carpet bullnose over every nosing
    dy1 = (STAIR_F1[1] - STAIR_F1[0]) / 8
    for i in range(8):
        ya = STAIR_F1[0] + dy1 * i; top = (i + 1) * RISER
        mb.rbox(sx0, sx1, ya - 0.022, ya + 0.03, top - 0.04, top + 0.004, r=0.012, seg=2, mi=0)
    dy2 = (STAIR_F2[1] - STAIR_F2[0]) / 9
    for i in range(9):
        ya = STAIR_F2[0] + dy2 * i; top = 8 * RISER + (i + 1) * RISER
        mb.rbox(sx0, sx1, ya - 0.022, ya + 0.03, top - 0.04, top + 0.004, r=0.012, seg=2, mi=0)
    mb.build("Front_Stair", [M['carpet']], smooth=True)

    # ---- white wrought-iron rail on the -X side of the flights (balusters + handrail + landing scrolls)
    rx = STAIR_X0 + 0.06
    mb = MB()
    pts = []
    for yy in (STAIR_F1[0] + 0.03, STAIR_F1[1], STAIR_LAND[1], STAIR_F2[1] - 0.12):
        pts.append((rx, yy, _rail_z(yy)))
    # subdivide so the tube bends cleanly at the landing
    poly = []
    for (a, b) in zip(pts[:-1], pts[1:]):
        for k in range(6):
            t = k / 6
            poly.append((a[0], a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t))
    poly.append(pts[-1])
    mb.path_tube(poly, 0.02, seg=10, mi=0)
    # newel post + ball at the foot
    mb.cbox(rx, STAIR_F1[0] + 0.05, 0.6, 0.045, 0.045, 1.2, 0)
    mb.sphere((rx, STAIR_F1[0] + 0.05, 1.24), 0.04, seg=12, rings=8, mi=0)
    # balusters: two per tread on the flights, every 0.13 on the landing
    def bal(yy):
        z0 = _tread_z(yy)
        mb.cylinder(rx, yy, z0, _rail_z(yy) - 0.015, 0.007, seg=8, mi=0)
    for i in range(8):
        ya = STAIR_F1[0] + dy1 * i
        bal(ya + 0.08); bal(ya + 0.2)
    for i in range(9):
        ya = STAIR_F2[0] + dy2 * i
        bal(ya + 0.08); bal(ya + 0.2)
    yy = STAIR_LAND[0] + 0.05
    while yy < STAIR_LAND[1]:
        bal(yy); yy += 0.13
    # scroll ornaments on the landing section (photo 15)
    for yc in (STAIR_LAND[0] + 0.22, STAIR_LAND[0] + 0.5, STAIR_LAND[0] + 0.78):
        for (zc, sgn) in ((8 * RISER + 0.30, 1), (8 * RISER + 0.60, -1)):
            sp = []
            for k in range(14):
                a = sgn * (0.3 + 1.9 * math.pi * k / 13)
                r = 0.03 + 0.045 * k / 13
                sp.append((rx, yc + r * math.cos(a), zc + r * math.sin(a)))
            mb.path_tube(sp, 0.0055, seg=6, mi=0)
    # wall-mounted handrail on the +X wall
    wx = STAIR_X1 - 0.055
    poly2 = []
    for (a, b) in zip(pts[:-1], pts[1:]):
        for k in range(6):
            t = k / 6
            poly2.append((wx, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t))
    poly2.append((wx, pts[-1][1], pts[-1][2]))
    mb.path_tube(poly2, 0.018, seg=10, mi=0)
    for yy in (5.5, 6.6, 7.6, 8.6, 9.6):
        mb.box(wx, STAIR_X1, yy - 0.012, yy + 0.012, _rail_z(yy) - 0.06, _rail_z(yy) - 0.02, 0)
        mb.cylinder(wx, yy, _rail_z(yy) - 0.06, _rail_z(yy) - 0.01, 0.01, seg=8, mi=0)
    mb.build("Front_StairRail", [M['iron_white']], smooth=True)
    # landing sconce on the +X wall
    mb = MB()
    sy_ = STAIR_LAND[0] + 0.5
    mb.box(STAIR_X1 - 0.015, STAIR_X1, sy_ - 0.05, sy_ + 0.05, 8 * RISER + 1.5, 8 * RISER + 1.76, 0)
    mb.tube((STAIR_X1, sy_, 8 * RISER + 1.63), (STAIR_X1 - 0.08, sy_, 8 * RISER + 1.63), 0.008, 0.008, seg=6, mi=0)
    mb.lathe(STAIR_X1 - 0.1, sy_, 8 * RISER + 1.54, [(0.04, 0), (0.055, 0.02), (0.07, 0.17), (0.065, 0.18), (0, 0.18)], seg=18, mi=1)
    mb.build("Front_StairSconce", [M['iron_white'], M['emit_warm']], smooth=True)
    add_light("L_Front_StairSconce", 'POINT', (STAIR_X1 - 0.13, sy_, 8 * RISER + 1.66), 12, K30, size=0.05)


# ---------------------------------------------------------------- dining room
def dining(M):
    L = _local(M)
    R = ROOMS['dining']
    x0, x1, y0, y1 = R[:4]
    mb = MB(); mb.plate(x0, x1, y0, y1, 0.0, 0.015, holes=[(-5.5,-4.05,4.45,5.75)])
    mb.build("Front_DinFloor", [M['maple']])
    mb = MB(); room_trims(mb, R, Z_MC, 0)
    mb.build("Front_DinTrim", [M['trim']])

    # ---- cage pendant (photos 03/04)
    cx, cy = 4.2, 4.4
    zt, zb = Z_MC - 0.75, Z_MC - 0.75 - 0.32
    hw, hd = 0.45, 0.16
    mb = MB()
    r = 0.006
    corners = [(cx - hw, cy - hd), (cx + hw, cy - hd), (cx + hw, cy + hd), (cx - hw, cy + hd)]
    for (px, py) in corners:                                                        # verticals
        mb.box(px - r, px + r, py - r, py + r, zb, zt, 0)
    for zz in (zb, zt):                                                             # horizontals
        mb.box(cx - hw, cx + hw, cy - hd - r, cy - hd + r, zz - r, zz + r, 0)
        mb.box(cx - hw, cx + hw, cy + hd - r, cy + hd + r, zz - r, zz + r, 0)
        mb.box(cx - hw - r, cx - hw + r, cy - hd, cy + hd, zz - r, zz + r, 0)
        mb.box(cx + hw - r, cx + hw + r, cy - hd, cy + hd, zz - r, zz + r, 0)
    for py in (cy - hd, cy + hd):                                                   # X braces on the long faces
        for k in range(3):
            xa = cx - hw + 2 * hw * k / 3; xb = cx - hw + 2 * hw * (k + 1) / 3
            mb.tube((xa, py, zb), (xb, py, zt), r, r, seg=6, mi=0)
            mb.tube((xa, py, zt), (xb, py, zb), r, r, seg=6, mi=0)
    for px in (cx - hw, cx + hw):                                                   # braces on the short faces
        mb.tube((px, cy - hd, zb), (px, cy + hd, zt), r, r, seg=6, mi=0)
        mb.tube((px, cy - hd, zt), (px, cy + hd, zb), r, r, seg=6, mi=0)
    mb.rbox(cx-.38,cx+.38,cy-.055,cy+.055,Z_MC-.025,Z_MC,r=.007,mi=0)                       # canopy
    for px in (cx - 0.3, cx + 0.3):                                                 # rods
        for k in range(max(1,int((Z_MC-.03-zt)/.026))):
            zz=zt+.026*k
            pts=[(px+(.014*math.cos(math.tau*j/16) if k%2==0 else 0),cy+(.014*math.cos(math.tau*j/16) if k%2 else 0),zz+.018*math.sin(math.tau*j/16)) for j in range(17)]
            mb.path_tube(pts,.0025,seg=6,mi=0)
    for i in range(5):                                                              # bulbs on short stems
        px = cx - hw + 2 * hw * (i + 0.5) / 5
        mb.cylinder(px, cy, zt - 0.09, zt, 0.004, seg=6, mi=0)
        mb.cylinder(px, cy, zt - 0.12, zt - 0.09, 0.012, seg=8, mi=0)
        mb.sphere((px, cy, zt - 0.16), 0.03, seg=12, rings=8, mi=1)
    mb.build("Front_DinPendant", [M['iron_black'], L['bulb']], smooth=True)
    add_light("L_Front_Pendant", 'POINT', (cx, cy, zt - 0.14), 80, K30, size=0.15)

    # ---- table, chairs, rug, tabletop dressing
    mb = MB()
    table(mb, cx, cy, 0.0, 2.0, 0.95, h=0.75, top_t=0.045, mi_top=0, mi_leg=0, legs='trestle')
    mb.build("Front_DinTable", [M['oak']])
    mb = MB()
    for px in (3.55, 4.85):
        dining_chair(mb, px, 3.62, rot=math.pi, mi_wood=0, mi_seat=1)
        dining_chair(mb, px, 5.18, rot=0.0, mi_wood=0, mi_seat=1)
    mb.build("Front_DinChairs", [M['walnut'], M['fabric_sand']], smooth=True)
    mb = MB()
    mb.rcbox(cx, cy, 0.753, 1.6, 0.36, 0.006, r=0.003, mi=0)                                        # linen runner
    mb.lathe(cx - 0.32, cy, 0.756, [(0, 0), (0.06, 0), (0.15, 0.05), (0.16, 0.075), (0.15, 0.08), (0.06, 0.02), (0, 0.02)], seg=24, mi=1)  # bowl
    rng = random.Random(5)
    for i in range(9):
        a = 2 * math.pi * i / 9
        rr = 0.075 if i < 6 else 0.03
        mb.sphere((cx - 0.32 + rr * math.cos(a), cy + rr * math.sin(a), 0.79 + (0.03 if i >= 6 else 0.0)), 0.033, seg=12, rings=8, mi=2, squash=0.85)
    vase(mb, cx + 0.42, cy, 0.756, h=0.3, r=0.085, mi=3, style='tall')
    mb.build("Front_DinTabletop", [M['linen_white'], L['bowl_glass'], L['lemon'], M['ceramic'], M['bark'], M['leaf_plant']], smooth=True)
    _pl.stems("Front_DinStems", (cx + 0.42, cy, 1.056), kind='eucalyptus', height=0.55, seed=3)
    mb = MB(); mb.rbox(2.85, 5.45, 3.25, 5.55, 0.017, 0.029, r=0.006, seg=2)
    mb.build("Rug_Dining", [M['rug_camel']], smooth=True)
    # sideboard on the +Y wall + lamp + big framed print
    mb = MB()
    cabinet_run(mb, 3.6, 5.2, y1 - 0.42, y1 - 0.02, 0.1, 0.85, mi=0, doors='X', n=3, mi_gap=1)
    mb.box(3.58, 5.22, y1 - 0.44, y1 - 0.02, 0.85, 0.87, 0)
    for xx in (3.65, 5.15):
        for yy in (y1 - 0.4, y1 - 0.06):
            mb.cbox(xx, yy, 0.05, 0.03, 0.03, 0.1, 1)
    lamp(mb, 3.85, y1 - 0.22, 0.87, mi_base=2, mi_shade=3, base_r=0.1, base_h=0.3, shade_r=0.17, shade_h=0.2)
    books(mb, 4.75, y1 - 0.22, 0.87, n=3, mi=4, rot=0.05, w=0.24, d=0.2)
    vase(mb, 4.4, y1 - 0.22, 0.87, h=0.2, r=0.09, mi=5, style='bowl')
    picture(mb, 3.50, 4.20, y1, 1.15, 2.0, mi_frame=1, mi_canvas=6, along='X', face=-1, d=0.035, frame_w=0.03)
    for (px, py, h) in ((4.12, y1 - 0.16, 0.22), (4.24, y1 - 0.3, 0.16)):
        mb.lathe(px, py, 0.87, [(0, 0), (0.035, 0), (0.035, 0.012), (0.012, 0.02), (0.012, h), (0.02, h + 0.02), (0.018, h + 0.04), (0, h + 0.04)], seg=14, mi=7)
        mb.cylinder(px, py, 0.87 + h + 0.04, 0.87 + h + 0.22, 0.012, seg=10, mi=8)
    _switch(mb, 'Y', 3.85, 1.2, +1, 1.2, 9)
    _smoke_detector(mb, 2.4, 5.6, Z_MC, 9)
    mb.build("Front_Sideboard", [M['walnut'], M['black_metal'], M['ceramic'], M['lampshade'], M['book'], M['clay'], M['art_bw'], M['brass'], L['candle'], L['plate']], smooth=True)
    add_light("L_Front_SideboardLamp", 'POINT', (3.85, y1 - 0.22, 1.35), 12, K30, size=0.08)
    # brass bar cart against the +X wall between the front window and the side window (the corners hold cameras)
    mb = MB()
    cx0, cx1, cy0, cy1 = 5.06, 5.44, 2.9, 3.62
    for zz in (0.35, 0.8):
        mb.box(cx0, cx1, cy0, cy1, zz - 0.012, zz, 1)                                                 # glass shelves
        mb.frame(cx0 - 0.01, cx1 + 0.01, cy0 - 0.01, cy1 + 0.01, zz - 0.02, zz + 0.01, 0.012, mi=0, axis='Z')
    for (px, py) in ((cx0, cy0), (cx1, cy0), (cx0, cy1), (cx1, cy1)):
        mb.cylinder(px, py, 0.06, 0.86, 0.008, seg=8, mi=0)
        mb.sphere((px, py, 0.05), 0.03, seg=10, rings=6, mi=0)                                         # castors
    mb.box(cx0, cx1, cy0, cy0 + 0.01, 0.82, 0.9, 0); mb.box(cx0, cx1, cy1 - 0.01, cy1, 0.82, 0.9, 0)  # top rails
    for i, (px, py, kind) in enumerate(((5.15, 3.05, 'decanter'), (5.3, 3.4, 'wine'), (5.38, 3.5, 'wine'), (5.2, 3.5, 'tumbler'))):
        _glass(mb, px, py, 0.8, kind, mi=1)
    mb.cylinder(5.32, 3.12, 0.8, 0.98, 0.07, seg=14, mi=2)                                             # ice bucket
    mb.build("Front_BarCart", [M['brass'], M['glass'], M['steel']], smooth=True)
    room_light("L_DinFill", 'dining', energy=23, color=K30)


def build(M):
    _local(M)
    living(M)
    entry_stair(M)
    dining(M)
