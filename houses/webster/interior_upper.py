"""Upper level of 1836 Webster: finishes (carpet / tile floors, ceilings, crown + base), the primary suite (photo 21),
its walk-in closet (17) and bath (23/24), the hall bath (19), the middle bedroom with the deck slider (16/26), the
rear bedroom (18/20), the upper hall, and the deck furniture.  Walls, window / door units (with their casings on
both faces), the slab and the deck floor + parapets are exterior.py's; this module builds everything inside the
rooms plus the upper CEILINGS.

Detail pass (2026-09-04): real beds (archviz.parts.bed: box base, mattress, folded duvet, sewn pillows / shams,
folded throw, channel headboard), nightstands with drawers, harp lamps with bulbs, sconces with back-plates / arms /
hollow glass drums, flush drum ceiling fixtures, framed + matted prints, bordered rugs, curtain rings + brackets,
floor registers, switch plates; the primary bath rebuilt to photo 23 (raised-panel vanity, granite, two oval
drop-in sinks with 3-hole brass sets, mirror wall around the window, brass light bar, brass-framed shower with a
corner shelf + drain, granite floor accents, towels); the hall bath to photo 19; leaf-quad plants (archviz.plants)
on the deck; a lantern + folded blanket on the deck furniture.

Staged for the film: the camera comes in through the slider's open half (y 9.5..10.4), crosses bed2 (y ~9.9..10.8),
the hall (y 11.1) and the primary suite diagonally (1.9, 10.2) -> (2.95, 8.0) -> (3.6, 6.5) -> out the french
windows; nothing stands in that corridor (the bed2 bed now has its headboard on the +X wall, y 8.2..9.55, so the
closet door on the -Y wall is free and the corridor y > 9.6 stays clear).
"""
import math, random
from .plan import *
from archviz.mesh import *
from archviz.lights import *
from archviz.parts import *
from archviz import materials as _mat
from archviz import plants as _pl

K30 = (1.0, 0.84, 0.66)
FLOOR_T = 0.015
DECK_Z = Z_UP + 0.09                       # deck floor top (exterior.py)
CLOSE_HALL_BED3 = False   # the up_hall | bed3 strip wall is now in plan.WALLS (exterior builds it)

_L = {}


def _local(M):
    if _L:
        return _L
    _L['glow'] = _mat.new_mat("UpFixtureGlass", (1.0, 0.92, 0.80, 1), rough=0.6, emit=(1.0, 0.80, 0.55, 1), emit_str=3.0)
    _L['glow_soft'] = _mat.new_mat("UpDrumGlass", (0.98, 0.95, 0.88, 1), rough=0.75, emit=(1.0, 0.86, 0.66, 1), emit_str=2.6)
    _L['bulb'] = _mat.new_mat("UpBulb", (1.0, 0.95, 0.85, 1), rough=0.3, emit=(1.0, 0.85, 0.60, 1), emit_str=7.0)
    _L['candle'] = _mat.new_mat("UpCandleFlame", (1.0, 0.8, 0.4, 1), emit=(1.0, 0.62, 0.25, 1), emit_str=14.0)
    _L['wax'] = _mat.new_mat("UpCandleWax", (0.95, 0.92, 0.85, 1), rough=0.5, subsurface=0.3)
    _L['tile_peach_y'] = _mat.tiles("TilePeachY", (0.86, 0.52, 0.36, 1), grout=(0.70, 0.66, 0.60, 1), size=(0.15, 0.15), gap=0.004,
                                    rough=0.2, variation=0.06, mottle=0.2, bump=0.2, coat=0.6, plane='YZ')
    _L['tile_teal_y'] = _mat.tiles("TileTealY", (0.20, 0.36, 0.38, 1), grout=(0.70, 0.66, 0.60, 1), size=(0.15, 0.15), gap=0.004,
                                   rough=0.2, variation=0.06, mottle=0.2, bump=0.2, coat=0.6, plane='YZ')
    _L['tile_floor_bath'] = _mat.tiles("HallBathFloor", (0.90, 0.90, 0.88, 1), grout=(0.72, 0.72, 0.70, 1), size=(0.15, 0.15), gap=0.004,
                                       rough=0.25, variation=0.03, mottle=0.1, bump=0.2, coat=0.4)
    # primary bath: 4" cream tile (photo 23/24), cream 12" floor
    for k, pl in (('cream', 'XZ'), ('cream_y', 'YZ')):
        _L[k] = _mat.tiles("PBathCream" + pl, (0.90, 0.85, 0.78, 1), grout=(0.80, 0.76, 0.70, 1), size=(0.108, 0.108), gap=0.003,
                           rough=0.18, variation=0.03, mottle=0.15, bump=0.2, coat=0.55, plane=pl)
    _L['cream_floor'] = _mat.tiles("PBathCreamFloor", (0.88, 0.82, 0.74, 1), grout=(0.74, 0.70, 0.64, 1), size=(0.30, 0.30), gap=0.004,
                                   rough=0.3, variation=0.04, mottle=0.25, bump=0.2, coat=0.35)
    _L['garment_a'] = _mat.fabric("GarmentNavy", (0.08, 0.10, 0.20, 1), weave=80)
    _L['garment_b'] = _mat.fabric("GarmentCamel", (0.55, 0.40, 0.24, 1), weave=80)
    _L['garment_c'] = _mat.fabric("GarmentSage", (0.40, 0.46, 0.34, 1), weave=80)
    _L['sheer'] = _mat.new_mat("SheerLinen", (0.92, 0.91, 0.88, 1), rough=0.9, alpha=0.55)
    _L['walnut_dark'] = _mat.wood("UpWalnut", light=(0.30, 0.18, 0.10, 1), dark=(0.16, 0.09, 0.05, 1), grain_axis='X', rough=0.4, coat=0.3)
    # bedding (weave + wrinkle so the linen reads at 1 m)
    _L['sheet'] = _mat.linen("UpSheet", base=(0.96, 0.95, 0.93, 1), wrinkle=0.25)
    _L['duvet'] = _mat.linen("UpDuvet", base=(0.93, 0.92, 0.89, 1), wrinkle=0.6)
    _L['duvet_grey'] = _mat.linen("UpDuvetGrey", base=(0.80, 0.79, 0.76, 1), wrinkle=0.6)
    _L['pillow'] = _mat.linen("UpPillow", base=(0.95, 0.94, 0.92, 1), wrinkle=0.4)
    _L['knit_rust'] = _mat.fabric("UpKnitRust", (0.55, 0.30, 0.20, 1), weave=28, bump=0.6)
    _L['knit_grey'] = _mat.fabric("UpKnitGrey", (0.42, 0.40, 0.37, 1), weave=28, bump=0.6)
    _L['knit_sage'] = _mat.fabric("UpKnitSage", (0.44, 0.50, 0.40, 1), weave=28, bump=0.6)
    _L['knit_oat'] = _mat.fabric("UpKnitOat", (0.78, 0.70, 0.56, 1), weave=28, bump=0.6)
    _L['towel'] = _mat.fabric("UpTowel", (0.93, 0.91, 0.87, 1), weave=22, bump=0.7)
    _L['towel_sage'] = _mat.fabric("UpTowelSage", (0.60, 0.66, 0.56, 1), weave=22, bump=0.7)
    _L['rug_border'] = _mat.fabric("UpRugBorder", (0.50, 0.46, 0.40, 1), weave=50, bump=0.3)
    _L['rug_border_blue'] = _mat.fabric("UpRugBorderBlue", (0.22, 0.28, 0.40, 1), weave=50, bump=0.3)
    _L['plate'] = _mat.new_mat("UpSwitchPlate", (0.93, 0.93, 0.91, 1), rough=0.35, coat=0.3)
    _L['grille'] = _mat.new_mat("UpRegister", (0.84, 0.84, 0.82, 1), rough=0.45, metal=0.15)
    _L['dark'] = _mat.new_mat("UpDarkSlot", (0.03, 0.03, 0.03, 1), rough=0.8)
    _L['vanity'] = _mat.wood("PBathVanity", light=(0.86, 0.76, 0.58, 1), dark=(0.76, 0.64, 0.46, 1), grain_axis='Z', scale=1.4, rough=0.35, coat=0.3)
    _L['granite_pink'] = _mat.noise_mat("PBathGranitePink", (0.52, 0.40, 0.36, 1), (0.82, 0.72, 0.66, 1), scale=220, bump=0.05, detail=6, rough=0.12, spec=0.6)
    _L['granite_floor'] = _mat.noise_mat("PBathGraniteFloor", (0.52, 0.40, 0.36, 1), (0.82, 0.72, 0.66, 1), scale=220, bump=0.05, detail=6, rough=0.4, spec=0.3)
    _L['shower_glass'] = _mat.new_mat("PBathShowerGlass", (1.0, 1.0, 1.0, 1), rough=0.0, transmission=1.0, ior=1.5, spec=0.5)
    _L['mat'] = _mat.new_mat("UpArtMat", (0.96, 0.95, 0.92, 1), rough=0.85, spec=0.2)
    _L['drape_linen'] = _mat.fabric("UpDrapeLinen", (0.86, 0.83, 0.76, 1), weave=45, bump=0.3)
    _L['blanket'] = _mat.fabric("UpDeckBlanket", (0.70, 0.62, 0.50, 1), weave=24, bump=0.7)
    _L['leather'] = _mat.leather("UpLeatherCognac", (0.50, 0.28, 0.14, 1), rough=0.4)
    _L['laptop'] = _mat.new_mat("UpLaptop", (0.72, 0.72, 0.74, 1), rough=0.35, metal=0.8)
    _L['screen'] = _mat.new_mat("UpLaptopScreen", (0.05, 0.05, 0.06, 1), rough=0.2, emit=(0.7, 0.78, 0.95, 1), emit_str=1.2)
    return _L


# ================================================================== helpers
def _plate(name, M, x0, x1, y0, y1, z0, z1, mat, coll='House'):
    mb = MB(); mb.box(x0, x1, y0, y1, z0, z1)
    return mb.build(name, [mat], coll)


def _segments(x0, x1, y0, y1):
    """The 4 wall faces of a rectangular room as (along, a0, a1, b, sign): sign = +1 when the room lies on the +b side."""
    return [('Y', y0, y1, x0, +1), ('Y', y0, y1, x1, -1), ('X', x0, x1, y0, +1), ('X', x0, x1, y1, -1)]


def _openings_on(seg, floor_only=False):
    """a-ranges of plan openings lying in this wall face (used to skip the baseboard)."""
    along, a0, a1, b, sign = seg
    out = []
    for o in OPENINGS:
        if o['along'] != along:
            continue
        ob = o['b']
        inside = (b - 0.42 < ob < b - 0.05) if sign > 0 else (b - 0.05 < ob < b + 0.05)
        if not inside:
            continue
        if o['a1'] <= a0 + 1e-4 or o['a0'] >= a1 - 1e-4:
            continue
        if floor_only and o['z0'] > Z_UP + 0.05:
            continue
        out.append((max(a0, o['a0']), min(a1, o['a1'])))
    return sorted(out)


def _run(mb, seg, z, prof, mi):
    """Extrude a closed (u, v) profile (u = into the room from the wall face, v = up from z) along a wall face."""
    along, a0, a1, b, sign = seg
    secs = []
    for a in (a0, a1):
        sec = []
        for (u, v) in prof:
            if along == 'X':
                sec.append((a, b + sign * u, z + v))
            else:
                sec.append((b + sign * u, a, z + v))
        secs.append(sec)
    mb.sweep(secs, mi)


CROWN = [(0.0, 0.0), (0.085, 0.0), (0.085, -0.014), (0.06, -0.026), (0.045, -0.045), (0.03, -0.07), (0.012, -0.09), (0.0, -0.09)]
BASE = [(0.0, 0.0), (0.016, 0.0), (0.016, 0.10), (0.012, 0.115), (0.0, 0.125)]


def _trims(mb, segs, zf, zc, mi=0):
    """Crown along every face; baseboard along every face minus the floor-level openings (doors / french / sliders)."""
    for seg in segs:
        along, a0, a1, b, sign = seg
        _run(mb, seg, zc, CROWN, mi)
        cur = a0
        for (h0, h1) in _openings_on(seg, floor_only=True):
            if h0 - cur > 0.02:
                _run(mb, (along, cur, h0, b, sign), zf, BASE, mi)
            cur = max(cur, h1)
        if a1 - cur > 0.02:
            _run(mb, (along, cur, a1, b, sign), zf, BASE, mi)


def _curtain(mb, along, a0, a1, b, z0, z1, mi, depth=0.055, folds=None, t=0.012, seed=0):
    """Hanging curtain panel: a vertical wavy ribbon (folds deepen toward the hem) spanning a0..a1 at plane b."""
    L = a1 - a0
    n = max(8, int(L / 0.035))
    folds = folds or max(2, int(L / 0.11))
    rng = random.Random(seed)
    ph = rng.uniform(0, 6.28)
    secs = []
    for (z, amp) in ((z0, 1.0), ((z0 + z1) / 2, 0.85), (z1, 0.45)):
        front, back = [], []
        for i in range(n + 1):
            a = a0 + L * i / n
            off = depth * amp * math.sin(folds * 2 * math.pi * i / n + ph)
            if along == 'X':
                front.append((a, b + off + t / 2, z)); back.append((a, b + off - t / 2, z))
            else:
                front.append((b + off + t / 2, a, z)); back.append((b + off - t / 2, a, z))
        secs.append(front + back[::-1])
    mb.sweep(secs, mi)


def _rod(mb, p0, p1, mi, r=0.012, rings=0, finial=True):
    """Curtain rod with ball finials and `rings` evenly spaced rings (short fat sleeves round the rod)."""
    mb.tube(p0, p1, r, r, seg=10, mi=mi)
    if finial:
        for p in (p0, p1):
            mb.sphere(p, r * 2.2, seg=10, rings=6, mi=mi)
    if rings > 0:
        p0v, p1v = Vector(p0), Vector(p1)
        for i in range(rings):
            t = (i + 0.5) / rings
            c = p0v.lerp(p1v, t)
            d = (p1v - p0v).normalized() * 0.005
            mb.tube(tuple(c - d), tuple(c + d), r * 1.9, r * 1.9, seg=12, mi=mi)


def _bracket(mb, wall_pt, rod_pt, mi, r=0.007):
    """L bracket: a stub out of the wall + a short riser up to the rod."""
    mb.tube(wall_pt, rod_pt, r, r, seg=6, mi=mi)
    wp = Vector(wall_pt)
    mb.cbox(wp.x, wp.y, wp.z, 0.03, 0.03, 0.05, mi)                                          # wall plate


def _face_box(mb, x, y, nx, ny, cz, w, t, h, mi, proud=0.0, rot=0.0):
    """A box centred on a wall/face point (x, y) with outward normal (nx, ny): w along the face, t out of it, h tall."""
    if abs(nx) > 0.5:
        mb.cbox(x + nx * (proud + t / 2), y, cz, t, w, h, mi)
    else:
        mb.cbox(x, y + ny * (proud + t / 2), cz, w, t, h, mi)


def _nightstand(mb, x, y, z, w, d, h, mi_body, mi_pull, nx=-1, ny=0, drawers=1):
    """Nightstand: a rounded box body on four tapered legs, drawer front(s) with reveals + a bar pull, facing (nx, ny)."""
    leg = 0.12
    mb.rbox(x - w / 2, x + w / 2, y - d / 2, y + d / 2, z + leg, z + h, 0.008, mi_body, seg=2)
    for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        mb.cylinder(x + sx * (w / 2 - 0.04), y + sy * (d / 2 - 0.04), z, z + leg + 0.01, 0.018, 0.014, seg=8, mi=mi_body)
    fx, fy = x + nx * d / 2, y + ny * d / 2
    fh = h - leg - 0.05
    for i in range(drawers):
        z0 = z + leg + 0.025 + fh * i / drawers
        z1 = z + leg + 0.025 + fh * (i + 1) / drawers
        _face_box(mb, fx, fy, nx, ny, (z0 + z1) / 2, w - 0.05, 0.004, z1 - z0 - 0.012, mi_body, proud=0.0)   # drawer front proud
        _face_box(mb, fx, fy, nx, ny, z1 - 0.004, w - 0.04, 0.002, 0.004, mi_pull)                            # shadow line
        _face_box(mb, fx, fy, nx, ny, (z0 + z1) / 2, 0.12, 0.02, 0.012, mi_pull, proud=0.006)                 # bar pull
        if abs(nx) > 0.5:
            for sy in (-1, 1):
                mb.cbox(fx + nx * 0.013, fy + sy * 0.05, (z0 + z1) / 2, 0.02, 0.008, 0.008, mi_pull)
        else:
            for sx in (-1, 1):
                mb.cbox(fx + sx * 0.05, fy + ny * 0.013, (z0 + z1) / 2, 0.008, 0.02, 0.008, mi_pull)


def _lamp(mb, x, y, z, mi_base, mi_shade, mi_metal, mi_bulb, base_r=0.11, base_h=0.30, shade_r=0.17, shade_h=0.22):
    """Table lamp: turned ceramic base, brass stem + harp + finial, a bulb, a hollow drum shade (closed top)."""
    mb.lathe(x, y, z, [(0.0, 0), (base_r * 0.8, 0), (base_r, base_h * 0.4), (base_r * 0.85, base_h * 0.8), (base_r * 0.3, base_h), (0.0, base_h)], seg=22, mi=mi_base)
    zs = z + base_h
    zb = zs + 0.16                                                     # bulb centre
    mb.cylinder(x, y, zs, zs + 0.08, 0.012, 0.010, seg=8, mi=mi_metal)
    mb.cylinder(x, y, zs + 0.08, zs + 0.11, 0.018, 0.018, seg=10, mi=mi_metal)   # socket
    mb.sphere((x, y, zb), 0.03, seg=12, rings=8, mi=mi_bulb)
    zt = zs + 0.08 + shade_h + 0.02                                      # harp top / shade top
    for sx in (-1, 1):                                                  # harp: two thin arms up to the finial
        mb.tube((x, y, zs + 0.09), (x + sx * 0.05, y, zs + 0.16), 0.003, 0.003, seg=6, mi=mi_metal)
        mb.tube((x + sx * 0.05, y, zs + 0.16), (x + sx * 0.05, y, zt - 0.03), 0.003, 0.003, seg=6, mi=mi_metal)
        mb.tube((x + sx * 0.05, y, zt - 0.03), (x, y, zt), 0.003, 0.003, seg=6, mi=mi_metal)
    mb.lathe(x, y, zt, [(0, 0), (0.012, 0), (0.012, 0.02), (0.006, 0.03), (0, 0.03)], seg=10, mi=mi_metal)    # finial
    zsh = zt - shade_h
    mb.lathe(x, y, zsh, [(0, shade_h), (shade_r * 0.98, shade_h), (shade_r, shade_h * 0.9), (shade_r, 0), (shade_r - 0.004, 0),
                         (shade_r - 0.004, shade_h * 0.9), (shade_r * 0.98 - 0.004, shade_h - 0.004), (0, shade_h - 0.004)], seg=26, mi=mi_shade)


def _sconce(mb, x, y, z, nx, ny, mi_metal, mi_glass):
    """Wall sconce: stepped back-plate, short arm, hollow frosted drum (closed top, diffuser below), metal cap."""
    _face_box(mb, x, y, nx, ny, z, 0.12, 0.012, 0.16, mi_metal)
    _face_box(mb, x, y, nx, ny, z, 0.09, 0.006, 0.13, mi_metal, proud=0.012)
    mb.tube((x + nx * 0.016, y + ny * 0.016, z), (x + nx * 0.105, y + ny * 0.105, z), 0.008, 0.008, seg=8, mi=mi_metal)
    cx, cy = x + nx * 0.105, y + ny * 0.105
    mb.lathe(cx, cy, z - 0.055, [(0, 0.16), (0.058, 0.16), (0.058, 0), (0.054, 0), (0.054, 0.156), (0, 0.156)], seg=22, mi=mi_glass)
    mb.lathe(cx, cy, z + 0.105, [(0, 0), (0.061, 0), (0.061, 0.01), (0.03, 0.012), (0, 0.012)], seg=22, mi=mi_metal)   # cap
    mb.lathe(cx, cy, z - 0.056, [(0, 0), (0.055, 0), (0.055, 0.004), (0, 0.004)], seg=22, mi=mi_glass)                 # diffuser


def _flush(mb, x, y, zc, mi_metal, mi_glass, style='dome', r=0.19):
    """Ceiling fixture: 'dome' = brass ring + frosted glass bowl (semi-flush), 'drum' = flush drum with a rounded diffuser."""
    if style == 'dome':
        mb.lathe(x, y, zc, [(0, 0), (r + 0.03, 0), (r + 0.03, -0.03), (r, -0.03), (0, -0.03)], seg=24, mi=mi_metal)
        mb.lathe(x, y, zc - 0.03, [(r, 0), (r * 0.96, -0.06), (r * 0.8, -0.12), (r * 0.5, -0.16), (0, -0.175)], seg=24, mi=mi_glass)
    else:
        h = 0.11
        mb.lathe(x, y, zc, [(0, 0), (r + 0.025, 0), (r + 0.025, -0.02), (r + 0.006, -0.02), (0, -0.02)], seg=28, mi=mi_metal)
        mb.lathe(x, y, zc - 0.02, [(r + 0.004, 0), (r + 0.004, -h + 0.04), (r * 0.96, -h + 0.015), (r * 0.82, -h), (0, -h)], seg=28, mi=mi_glass)
        mb.lathe(x, y, zc - 0.02 - h, [(0, 0), (0.02, 0), (0.02, -0.008), (0, -0.008)], seg=12, mi=mi_metal)        # finial


def _framed(mb, along, a0, a1, b, sign, z0, z1, mi_frame, mi_mat, mi_art, d=0.035, fw=0.03, mat_w=0.06):
    """Framed print with a mat: frame slab, mat face, the print inset 2 mm proud of the mat."""
    picture(mb, a0, a1, b, z0, z1, mi_frame=mi_frame, mi_canvas=mi_mat, along=along, face=sign, d=d, frame_w=fw)
    if along == 'X':
        mb.box(a0 + fw + mat_w, a1 - fw - mat_w, b + sign * (d + 0.002), b + sign * (d + 0.004), z0 + fw + mat_w, z1 - fw - mat_w, mi_art)
    else:
        mb.box(b + sign * (d + 0.002), b + sign * (d + 0.004), a0 + fw + mat_w, a1 - fw - mat_w, z0 + fw + mat_w, z1 - fw - mat_w, mi_art)


def _rug(mb, x0, x1, y0, y1, z, mi_field, mi_border, bw=0.10):
    mb.rbox(x0, x1, y0, y1, z, z + 0.012, 0.01, mi_field, seg=2)
    mb.frame(x0 + 0.01, x1 - 0.01, y0 + 0.01, y1 - 0.01, z + 0.012, z + 0.0135, bw, mi_border, axis='Z')


def _register(mb, x, y, z, mi_grille, mi_dark, along='X', w=0.30, d=0.10):
    """Floor register: a metal frame plate with dark slots."""
    if along == 'X':
        mb.cbox(x, y, z + 0.004, w, d, 0.008, mi_grille)
        n = 9
        for i in range(n):
            mb.cbox(x + (i - (n - 1) / 2) * (w * 0.82 / n), y, z + 0.0085, w * 0.82 / n * 0.45, d * 0.68, 0.002, mi_dark)
    else:
        mb.cbox(x, y, z + 0.004, d, w, 0.008, mi_grille)
        n = 9
        for i in range(n):
            mb.cbox(x, y + (i - (n - 1) / 2) * (w * 0.82 / n), z + 0.0085, d * 0.68, w * 0.82 / n * 0.45, 0.002, mi_dark)


def _switch(mb, x, y, z, nx, ny, mi_plate, mi_dark, kind='switch'):
    _face_box(mb, x, y, nx, ny, z, 0.07, 0.006, 0.115, mi_plate)
    if kind == 'switch':
        _face_box(mb, x, y, nx, ny, z + 0.004, 0.014, 0.012, 0.028, mi_plate, proud=0.006)
    else:
        for dz in (-0.02, 0.02):
            _face_box(mb, x, y, nx, ny, z + dz, 0.03, 0.002, 0.03, mi_dark, proud=0.006)


def _folded_towel(mb, x, y, z, nx, ny, mi, w=0.4, drop=0.45, t=0.025):
    """Towel folded over a bar at (x, y, z): a saddle over the bar + two hanging halves (the wall is toward -(nx, ny))."""
    if abs(nx) > 0.5:
        mb.rcbox(x, y, z + 0.012, 0.11, w, t + 0.01, 0.012, mi, puff=0.3)
        mb.rcbox(x + nx * 0.03, y, z - drop / 2, t, w, drop, 0.008, mi, puff=0.3)
        mb.rcbox(x - nx * 0.03, y, z - drop / 2 + 0.03, t, w, drop - 0.06, 0.008, mi, puff=0.3)
    else:
        mb.rcbox(x, y, z + 0.012, w, 0.11, t + 0.01, 0.012, mi, puff=0.3)
        mb.rcbox(x, y + ny * 0.03, z - drop / 2, w, t, drop, 0.008, mi, puff=0.3)
        mb.rcbox(x, y - ny * 0.03, z - drop / 2 + 0.03, w, t, drop - 0.06, 0.008, mi, puff=0.3)


def _towel_bar(mb, x, y, z, nx, ny, L, mi_metal, mi_towel=None, along='Y', towel_w=0.4):
    """Chrome / brass towel bar 8 cm off the wall with two posts, optionally with a folded towel over it."""
    off = 0.08
    if along == 'Y':
        p0, p1 = (x + nx * off, y - L / 2, z), (x + nx * off, y + L / 2, z)
    else:
        p0, p1 = (x - L / 2, y + ny * off, z), (x + L / 2, y + ny * off, z)
    mb.tube(p0, p1, 0.009, 0.009, seg=10, mi=mi_metal)
    for p in (p0, p1):
        mb.tube((p[0] - nx * off, p[1] - ny * off, z), p, 0.008, 0.008, seg=8, mi=mi_metal)
        _face_box(mb, p[0] - nx * off, p[1] - ny * off, nx, ny, z, 0.035, 0.008, 0.035, mi_metal)
    if mi_towel is not None:
        _folded_towel(mb, x + nx * off, y + ny * off, z, nx, ny, mi_towel, w=towel_w) if along == 'Y' else \
            _folded_towel(mb, x + nx * off, y + ny * off, z, nx, ny, mi_towel, w=towel_w)


def _toilet(mb, x, y, z, rot, mi, mi_metal=None):
    """Tank at its own +Y (against the wall), bowl + seat toward -Y; lid, seat ring, flush lever."""
    def B(cx, cy, cz, sx, sy, sz, r=0.02, m=None):
        px, py = rot2(x + cx, y + cy, x, y, rot)
        mb.rcbox(px, py, z + cz, sx, sy, sz, r, mi if m is None else m, rot)
    B(0, 0.20, 0.55, 0.46, 0.18, 0.36, r=0.02)                       # tank
    B(0, 0.20, 0.745, 0.48, 0.20, 0.03, r=0.01)                       # lid
    if mi_metal is not None:
        B(-0.19, 0.10, 0.70, 0.05, 0.02, 0.015, r=0.004, m=mi_metal)   # flush lever
    bx, by = rot2(x, y - 0.08, x, y, rot)
    el = 1.35                                                          # the bowl is longer along its own Y
    fx, ry = (el, 1.0 / el) if abs(math.sin(rot)) > 0.5 else (1.0, el)
    mb.lathe(bx, by, z, [(0.12 * fx, 0), (0.17 * fx, 0.10), (0.19 * fx, 0.28), (0.20 * fx, 0.38), (0.19 * fx, 0.40), (0, 0.40)], seg=20, mi=mi, ry=ry)
    mb.lathe(bx, by, z + 0.40, [(0, 0), (0.21 * fx, 0), (0.21 * fx, 0.02), (0.15 * fx, 0.02), (0.15 * fx, 0.005), (0, 0.005)], seg=20, mi=mi, ry=ry)   # seat ring
    B(0, -0.02, 0.435, 0.40, 0.50, 0.018, r=0.008)                    # seat lid (closed)


def _pedestal_sink(mb,x,y,z,mi_porcelain,mi_metal,r=.25,h=.82,dir=(-1,0)):
    mb.lathe(x,y,z,[(0,0),(.13,0),(.10,.10),(.09,h-.20),(.14,h-.08),(.20,h-.06),(0,h-.06)],seg=48,mi=mi_porcelain)
    _oval_sink(mb,x,y,z+h+.06,r*.82,r,mi_porcelain)
    _widespread(mb,x-dir[0]*r*.62,y-dir[1]*r*.62,z+h+.06,mi_metal,dir=dir)


def _garments(mb, x_wall, y0, y1, z_rod, sign, mi_rod, mis, n=7, seed=1, off=0.30, wid=0.42):
    """Chrome rod parallel to a wall (x = x_wall) with `n` hanging garments (flat rounded panels perpendicular to it)."""
    xr = x_wall + sign * off
    _rod(mb, (xr, y0, z_rod), (xr, y1, z_rod), mi_rod, r=0.012, finial=False)
    for yy in (y0 + 0.04, y1 - 0.04):
        mb.tube((x_wall, yy, z_rod), (xr, yy, z_rod), 0.008, 0.008, seg=6, mi=mi_rod)
    rng = random.Random(seed)
    for i in range(n):
        yy = y0 + 0.12 + (y1 - y0 - 0.24) * i / max(1, n - 1) + rng.uniform(-0.02, 0.02)
        mi = mis[i % len(mis)]
        hgt = rng.uniform(0.75, 1.05)
        w = wid * rng.uniform(0.9, 1.1)
        mb.rbox(xr - w / 2 - 0.02, xr + w / 2 + 0.02, yy - 0.014, yy + 0.014, z_rod - 0.09 - hgt, z_rod - 0.09, 0.012, mi, seg=2)
        mb.tube((xr, yy, z_rod - 0.09), (xr, yy, z_rod + 0.012), 0.004, 0.004, seg=5, mi=mi_rod)   # hanger hook


def _shelf(mb, x0, x1, y0, y1, z, mi, t=0.022):
    mb.box(x0, x1, y0, y1, z, z + t, mi)


def _dresser(mb, x0, x1, y0, y1, z, h, mi_body, mi_pull, drawers=4, front='+Y'):
    mb.rbox(x0, x1, y0, y1, z + 0.06, z + h, 0.01, mi_body, seg=2)
    for sx, sy in ((x0 + 0.04, y0 + 0.04), (x1 - 0.04, y0 + 0.04), (x0 + 0.04, y1 - 0.04), (x1 - 0.04, y1 - 0.04)):
        mb.cbox(sx, sy, z + 0.03, 0.04, 0.04, 0.06, mi_body)
    for i in range(drawers):
        zz = z + 0.10 + (h - 0.14) * (i + 0.5) / drawers
        zp = zz + (h - 0.14) / drawers / 2
        if front == '+Y':
            mb.box(x0 + 0.01, x1 - 0.01, y1, y1 + 0.003, zz - 0.002, zz + 0.002, mi_pull)                # reveal line
            mb.cbox((x0 + x1) / 2, y1 + 0.016, zp, 0.14, 0.012, 0.012, mi_pull)                          # bar pull
            for sx in (-1, 1):
                mb.cbox((x0 + x1) / 2 + sx * 0.06, y1 + 0.008, zp, 0.008, 0.016, 0.008, mi_pull)
        elif front == '-Y':
            mb.box(x0 + 0.01, x1 - 0.01, y0 - 0.003, y0, zz - 0.002, zz + 0.002, mi_pull)
            mb.cbox((x0 + x1) / 2, y0 - 0.016, zp, 0.14, 0.012, 0.012, mi_pull)
            for sx in (-1, 1):
                mb.cbox((x0 + x1) / 2 + sx * 0.06, y0 - 0.008, zp, 0.008, 0.016, 0.008, mi_pull)
        elif front == '+X':
            mb.box(x1, x1 + 0.003, y0 + 0.01, y1 - 0.01, zz - 0.002, zz + 0.002, mi_pull)
            mb.cbox(x1 + 0.016, (y0 + y1) / 2, zp, 0.012, 0.14, 0.012, mi_pull)
            for sy in (-1, 1):
                mb.cbox(x1 + 0.008, (y0 + y1) / 2 + sy * 0.06, zp, 0.016, 0.008, 0.008, mi_pull)
        else:  # '-X'
            mb.box(x0 - 0.003, x0, y0 + 0.01, y1 - 0.01, zz - 0.002, zz + 0.002, mi_pull)
            mb.cbox(x0 - 0.016, (y0 + y1) / 2, zp, 0.012, 0.14, 0.012, mi_pull)
            for sy in (-1, 1):
                mb.cbox(x0 - 0.008, (y0 + y1) / 2 + sy * 0.06, zp, 0.016, 0.008, 0.008, mi_pull)


def _books(mb, x, y, z, mi, rot=0.0, n=3):
    books(mb, x, y, z, n=n, mi=mi, rot=rot, w=0.24, d=0.18)


def _lantern(mb, x, y, z, mi_metal, mi_glass, mi_wax, mi_flame, s=0.13, h=0.24):
    """Black-framed glass lantern with a pillar candle inside (a small flame emitter)."""
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.cbox(x + sx * (s / 2 - 0.006), y + sy * (s / 2 - 0.006), z + h / 2, 0.012, 0.012, h, mi_metal)
    mb.cbox(x, y, z + 0.006, s, s, 0.012, mi_metal)
    mb.cbox(x, y, z + h - 0.008, s + 0.01, s + 0.01, 0.016, mi_metal)
    mb.lathe(x, y, z + h + 0.008, [(0, 0), (0.03, 0), (0.02, 0.03), (0.008, 0.05), (0, 0.05)], seg=12, mi=mi_metal)   # top knob
    for (dx, dy, sx, sy) in ((s / 2, 0, 0.003, s - 0.012), (-s / 2, 0, 0.003, s - 0.012), (0, s / 2, s - 0.012, 0.003), (0, -s / 2, s - 0.012, 0.003)):
        mb.cbox(x + dx, y + dy, z + h / 2, sx, sy, h - 0.03, mi_glass)
    mb.cylinder(x, y, z + 0.012, z + 0.10, 0.03, 0.03, seg=14, mi=mi_wax)
    mb.lathe(x, y, z + 0.10, [(0, 0), (0.004, 0), (0.007, 0.012), (0.004, 0.028), (0, 0.032)], seg=8, mi=mi_flame)


def _cabinet_door(mb, a0, a1, xf, z0, z1, mi, mi_knob, sign=-1, stile=0.05, raised=True, knob_a=None):
    """Raised-panel cabinet door in the plane x = xf (face normal sign*X), spanning y a0..a1, z z0..z1."""
    t = 0.019
    xa, xb = (xf - t, xf) if sign > 0 else (xf, xf + t)
    mb.box(xa, xb, a0, a1, z0, z1, mi)                                                   # slab
    fx0, fx1 = (xf, xf + 0.006) if sign > 0 else (xf - 0.006, xf)
    mb.box(fx0, fx1, a0, a0 + stile, z0, z1, mi); mb.box(fx0, fx1, a1 - stile, a1, z0, z1, mi)   # stiles
    mb.box(fx0, fx1, a0 + stile, a1 - stile, z0, z0 + stile, mi); mb.box(fx0, fx1, a0 + stile, a1 - stile, z1 - stile, z1, mi)
    if raised and (a1 - a0) > 2 * stile + 0.08 and (z1 - z0) > 2 * stile + 0.08:
        i = 0.025
        px0, px1 = (xf, xf + 0.003) if sign > 0 else (xf - 0.003, xf)
        mb.box(px0, px1, a0 + stile + i, a1 - stile - i, z0 + stile + i, z1 - stile - i, mi)
        px0, px1 = (xf, xf + 0.005) if sign > 0 else (xf - 0.005, xf)
        mb.box(px0, px1, a0 + stile + i + 0.02, a1 - stile - i - 0.02, z0 + stile + i + 0.02, z1 - stile - i - 0.02, mi)
    ka = knob_a if knob_a is not None else (a1 - 0.05 if sign * 0 == 0 and knob_a is None else a0 + 0.05)
    kx = xf + sign * 0.006
    mb.tube((kx, ka, (z0 + z1) / 2), (kx + sign * 0.02, ka, (z0 + z1) / 2), 0.005, 0.005, seg=8, mi=mi_knob)
    mb.sphere((kx + sign * 0.028, ka, (z0 + z1) / 2), 0.013, seg=10, rings=6, mi=mi_knob)


def _drawer_front(mb, a0, a1, xf, z0, z1, mi, mi_pull, sign=-1):
    t = 0.019
    xa, xb = (xf - t, xf) if sign > 0 else (xf, xf + t)
    mb.box(xa, xb, a0, a1, z0, z1, mi)
    fx0, fx1 = (xf, xf + 0.006) if sign > 0 else (xf - 0.006, xf)
    mb.box(fx0, fx1, a0, a0 + 0.035, z0, z1, mi); mb.box(fx0, fx1, a1 - 0.035, a1, z0, z1, mi)
    mb.box(fx0, fx1, a0 + 0.035, a1 - 0.035, z0, z0 + 0.03, mi); mb.box(fx0, fx1, a0 + 0.035, a1 - 0.035, z1 - 0.03, z1, mi)
    ac, zc = (a0 + a1) / 2, (z0 + z1) / 2
    kx = xf + sign * 0.006
    mb.tube((kx + sign * 0.022, ac - 0.05, zc), (kx + sign * 0.022, ac + 0.05, zc), 0.005, 0.005, seg=8, mi=mi_pull)
    for s in (-1, 1):
        mb.tube((kx, ac + s * 0.05, zc), (kx + sign * 0.022, ac + s * 0.05, zc), 0.004, 0.004, seg=6, mi=mi_pull)


def _ring_slab(mb, cx, cy, rx, ry, x0, x1, y0, y1, z0, z1, mi, seg=36):
    """Counter piece around a sink: a slab filling the rectangle x0..x1 / y0..y1 minus the ellipse (rx, ry) at (cx, cy)."""
    inner, outer = [], []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        dx, dy = math.cos(a), math.sin(a)
        tx = ((x1 - cx) / dx) if dx > 1e-9 else (((x0 - cx) / dx) if dx < -1e-9 else 1e9)
        ty = ((y1 - cy) / dy) if dy > 1e-9 else (((y0 - cy) / dy) if dy < -1e-9 else 1e9)
        t = min(tx, ty)
        inner.append((cx + rx * dx, cy + ry * dy)); outer.append((cx + dx * t, cy + dy * t))
    secs = [[(x, y, z1) for (x, y) in outer], [(x, y, z1) for (x, y) in inner], [(x, y, z0) for (x, y) in inner], [(x, y, z0) for (x, y) in outer]]
    mb.sweep(secs, mi, close=True, caps=False)


def _oval_sink(mb, x, y, z, rx, ry, mi):
    """Drop-in oval sink: rolled rim 12 mm above the counter, 15 cm deep bowl (double-walled shell)."""
    k = ry / rx
    mb.lathe(x, y, z, [(0, -0.15), (rx * 0.45, -0.15), (rx * 0.85, -0.09), (rx * 0.97, -0.02), (rx * 1.06, 0.0), (rx * 1.07, 0.012),
                       (rx * 0.99, 0.014), (rx * 0.94, 0.0), (rx * 0.82, -0.065), (rx * 0.42, -0.128), (0, -0.135)], seg=32, mi=mi, ry=k)
    mb.lathe(x, y + ry * 0.75, z - 0.128, [(0, 0), (0.018, 0), (0.018, 0.004), (0, 0.004)], seg=12, mi=mi)   # drain


def _widespread(mb, x, y, z, mi, dir=(-1, 0)):
    """3-hole brass faucet: an arched spout + two cross handles either side of it."""
    mb.lathe(x, y, z, [(0, 0), (0.025, 0), (0.022, 0.01), (0.012, 0.012), (0.012, 0.06), (0, 0.06)], seg=12, mi=mi)
    p0 = Vector((x, y, z + 0.06)); mid = Vector((x + dir[0] * 0.06, y + dir[1] * 0.06, z + 0.13)); p1 = Vector((x + dir[0] * 0.13, y + dir[1] * 0.13, z + 0.11))
    mb.path_tube([tuple(p0), tuple(mid), tuple(p1), tuple(p1 + Vector((0, 0, -0.02)))], 0.01, seg=8, mi=mi)
    for s in (-1, 1):
        hx, hy = x - dir[1] * s * 0.10, y + dir[0] * s * 0.10
        mb.lathe(hx, hy, z, [(0, 0), (0.02, 0), (0.018, 0.008), (0.010, 0.01), (0.010, 0.04), (0, 0.04)], seg=10, mi=mi)
        mb.cbox(hx, hy, z + 0.045, 0.045, 0.008, 0.008, mi); mb.cbox(hx, hy, z + 0.045, 0.008, 0.045, 0.008, mi)


# ================================================================== finishes
def finishes(M):
    L = _local(M)
    carpet = ['prim', 'wic', 'bed2', 'wic2', 'bed3', 'bed3_s', 'closet3', 'up_hall']
    mb_c = MB()
    for r in carpet:
        x0, x1, y0, y1, z0, z1 = ROOMS[r]
        if r=='prim':
            from .exterior import _plate_holes
            _plate_holes(mb_c,x0,x1,y0,y1,Z_UP,Z_UP+FLOOR_T,[ROOMS['wic'][:4]],0)
        else:mb_c.box(x0,x1,y0,y1,Z_UP,Z_UP+FLOOR_T)
    mb_c.build("Up_Floor_Carpet", [M['carpet_up']], 'House')
    for r, mat in (('prim_bath', L['cream_floor']), ('hall_bath', L['tile_floor_bath'])):
        x0, x1, y0, y1, z0, z1 = ROOMS[r]
        mb = MB(); mb.box(x0, x1, y0, y1, Z_UP, Z_UP + FLOOR_T)
        mb.build(f"Up_Floor_{r}", [mat], 'House')
    # ceilings: one plate per room (+ the stair well's top)
    mb = MB()
    for r in UPPER_ROOMS:
        if r == 'deck':
            continue
        x0, x1, y0, y1, z0, z1 = ROOMS[r]
        if r=='prim':
            from .exterior import _plate_holes
            _plate_holes(mb,x0,x1,y0,y1,Z_UPC,Z_UPC+.03,[ROOMS['wic'][:4]],0)
        else:mb.box(x0,x1,y0,y1,Z_UPC,Z_UPC+.03)
    wx0, wx1, wy0, wy1 = STAIR_WELL
    mb.box(wx0, wx1, wy0, wy1, Z_UPC, Z_UPC + 0.03)
    mb.build("Up_Ceilings", [M['ceiling']], 'House')
    # crown + base: rectangular rooms, then the two irregular ones by hand
    mb = MB()
    for r in ('wic', 'wic2', 'prim_bath', 'hall_bath', 'closet3', 'bed2', 'up_hall'):
        x0, x1, y0, y1, z0, z1 = ROOMS[r]
        segs = _segments(x0, x1, y0, y1)
        if r == 'up_hall':                                  # its -Y end is the open stair well: no wall there
            segs = [s for s in segs if not (s[0] == 'X' and abs(s[3] - y0) < 1e-6)]
        _trims(mb, segs, Z_UP + FLOOR_T, Z_UPC)
    # primary suite: rectangle minus the WIC bump (faces x 2.45 for y 6.25..8.2 and y 8.2 for x 1.05..2.45)
    px0, px1, py0, py1 = ROOMS['prim'][:4]
    segs = [('Y', 8.2, py1, px0, +1), ('Y', py0, py1, px1, -1), ('X', 2.45, px1, py0, +1), ('X', px0, px1, py1, -1),
            ('Y', py0, 8.2, 2.45, +1), ('X', px0, 2.45, 8.2, +1)]
    _trims(mb, segs, Z_UP + FLOOR_T, Z_UPC)
    # rear bedroom: the L (bed3 + bed3_s)
    segs = [('Y', 11.6, BED_REAR, -3.15, +1), ('X', -3.15, 0.9, BED_REAR, -1), ('Y', 13.55, BED_REAR, 0.9, -1),
            ('X', -0.15, 0.9, 13.55, +1), ('Y', 11.6, 13.55, -0.15, -1), ('X', -3.15, -0.15, 11.6, +1)]
    _trims(mb, segs, Z_UP + FLOOR_T, Z_UPC)
    mb.build("Up_Trims", [M['trim']], 'House')
    if CLOSE_HALL_BED3:
        _plate("Up_Wall_HallBed3", M, -0.3, -0.15, 11.6, 13.55, Z_UP, Z_UPC, M['wall'])
    # small stuff every room has: floor registers by the exterior walls, switch plates beside the doors, outlets
    zf = Z_UP + FLOOR_T
    sm = MB()          # 0 grille, 1 dark, 2 plate
    for (x, y, along) in ((4.7, 7.5, 'Y'), (1.3, 6.55, 'X'), (-2.8, 10.6, 'Y'), (-2.72, 16.85, 'X'), (0.55, 16.8, 'X'), (0.4, 10.6, 'X')):
        _register(sm, x, y, zf, 0, 1, along=along)
    for (x, y, nx, ny, kind) in ((1.08, 11.8, 1, 0, 'switch'), (1.08, 11.95, 1, 0, 'switch'), (5.29, 7.55, -1, 0, 'outlet'), (5.29, 11.85, -1, 0, 'outlet'),
                                 (-0.53, 10.35, -1, 0, 'switch'), (-3.12, 8.2, 1, 0, 'outlet'), (-0.53, 8.9, -1, 0, 'outlet'),
                                 (-.225, 13.55, 0, 1, 'switch'), (-3.12, 15.8, 1, 0, 'outlet'), (0.87, 15.0, -1, 0, 'outlet'),
                                 (0.87, 10.52, -1, 0, 'switch'), (2.78, 12.58, 0, 1, 'switch'), (1.55, 12.58, 0, 1, 'switch')):
        _switch(sm, x, y, Z_UP + (1.2 if kind == 'switch' else 0.32), nx, ny, 2, 1, kind)
    sm.build("Up_Small_Electrical", [L['grille'], L['dark'], L['plate']], 'House')


# ================================================================== primary suite (photo 21)
def primary(M):
    L = _local(M)
    zf = Z_UP + FLOOR_T
    # bordered rug under the bed
    mb = MB(); _rug(mb, 2.5, 4.95, 8.05, 10.35, zf, 0, 1)
    mb.build("Up_Rug_Prim", [M['rug_pale'], L['rug_border']], 'House')
    # queen bed, headboard on the +X wall between the two windows (own +Y -> +X: rot -90 deg); its foot corner
    # (3.02, 8.45) stays 0.45 m from the film key (2.95, 8.0)
    XW = ROOMS['prim'][1]                                              # +X wall face (5.05)
    mb = MB()
    bed(mb, XW - 0.08 - 0.975, 9.2, rot=-math.pi / 2, z=zf, w=1.5, l=1.95, mi_frame=0, mi_linen=1, mi_pillow=3, mi_throw=2, mi_duvet=4, head_h=1.15, seed=3, channels=5)
    mb.build("Up_Bed_Prim", [M['fabric_taupe'], L['sheet'], L['knit_rust'], L['pillow'], L['duvet']], 'House', smooth=True, subsurf=1)
    # nightstands with a drawer + harp lamps (under the window sills, z 0.8)
    NS = ((XW - 0.25, 8.15), (XW - 0.25, 10.25))
    mb = MB()
    for (xx, yy) in NS:
        _nightstand(mb, xx, yy, zf, 0.46, 0.44, 0.56, 0, 1, nx=-1, ny=0, drawers=1)
    mb.build("Up_Nightstands_Prim", [M['walnut'], M['brass']], 'House', bevel=0.004)
    mb = MB()
    for (xx, yy) in NS:
        _lamp(mb, xx, yy, zf + 0.56, 0, 1, 2, 3, base_r=0.10, base_h=0.28, shade_r=0.16, shade_h=0.21)
        add_light(f"Up_L_PrimLamp_{yy * 10:.0f}", 'POINT', (xx, yy, zf + 0.56 + 0.44), 14, K30, size=0.08)
    mb.build("Up_Lamps_Prim", [M['bronze'], M['lampshade'], M['brass'], L['bulb']], 'House', smooth=True)
    mb = MB()
    _books(mb, XW - 0.25, 8.02, zf + 0.56, 0, rot=0.15, n=2)
    mb.lathe(XW - 0.22, 10.38, zf + 0.56, [(0, 0), (0.05, 0), (0.06, 0.02), (0.06, 0.08), (0.055, 0.09), (0, 0.09)], seg=14, mi=1)   # a glass of water
    mb.build("Up_Deco_PrimNS", [M['book'], M['glass']], 'House', smooth=True)
    # dresser on the +Y wall with a framed mirror above, tray + vase with eucalyptus stems
    mb = MB()
    _dresser(mb, 1.45, 2.75, 11.92, 12.38, zf, 0.92, 0, 1, drawers=3, front='-Y')
    mb.build("Up_Dresser_Prim", [M['oak_pale'], M['black_metal']], 'House')
    mb = MB()
    mb.box(1.55, 2.65, 12.351, 12.354, Z_UP + 1.05, Z_UP + 2.0, 0)
    mb.frame(1.52, 2.68, 12.345, 12.395, Z_UP + 1.02, Z_UP + 2.03, 0.03, mi=1, axis='Y')
    mb.build("Up_Mirror_Prim", [M['mirror'], M['oak']], 'House')
    mb = MB()
    mb.rcbox(2.35, 12.14, zf + 0.925, 0.32, 0.22, 0.012, 0.006, 0)                                                # tray
    mb.lathe(2.28, 12.1, zf + 0.93, [(0, 0), (0.03, 0), (0.035, 0.05), (0.03, 0.09), (0.018, 0.10), (0, 0.10)], seg=12, mi=1)  # bottle
    mb.lathe(2.45, 12.18, zf + 0.93, [(0, 0), (0.035, 0), (0.035, 0.03), (0, 0.03)], seg=12, mi=2)            # dish
    vase(mb, 1.8, 12.15, zf + 0.92, h=0.34, r=0.09, mi=2, style='tall')
    mb.build("Up_Vase_Prim", [M['leather_tan'], M['glass'], M['ceramic']], 'House', smooth=True)
    _pl.stems("Up_Stems_Prim", (1.8, 12.15, zf + 0.92 + 0.34), kind='eucalyptus', height=0.55, seed=3)
    mb = MB(); _books(mb, 1.65, 12.12, zf + 0.92, 0, rot=0.2, n=3)
    mb.build("Up_Books_Prim", [M['book']], 'House')
    # tall leaner mirror against the walk-in closet's +Y face (photo 21 shows that face blank)
    mb = MB()
    tilt = 0.07
    def lean_slab(x0, x1, z0, z1, d0, d1, m_):
        secs = []
        for zz in (z0, z1):
            yy = 8.2 + 0.02 + tilt * (1.75 - zz)                      # foot out, top against the wall
            secs.append([(x0, yy + d0, zf + zz), (x1, yy + d0, zf + zz), (x1, yy + d1, zf + zz), (x0, yy + d1, zf + zz)])
        mb.sweep(secs, m_)
    lean_slab(1.35, 1.9, 0.0, 1.75, 0.0, 0.035, 1)                  # oak frame slab
    lean_slab(1.38, 1.87, 0.03, 1.72, 0.035, 0.039, 0)              # mirror pane, proud of the slab, 3 cm margin
    mb.build("Up_Mirror_PrimLean", [M['mirror'], M['oak']], 'House')
    # reading chair in the +X / +Y corner (clear of the bath door swing x <= 3.8) with a knit throw + a small table
    mb = MB()
    armchair(mb, XW - 0.55, 11.85, rot=-math.pi / 4, z=zf, w=0.72, d=0.74, mi=0, mi_legs=1, style='barrel')
    mb.rcbox(XW - 0.53, 11.87, zf + 0.60, 0.40, 0.30, 0.035, 0.012, 2, rot=-math.pi / 4, puff=0.6)                       # folded throw on the seat
    mb.build("Up_Chair_Prim", [M['fabric_sand'], M['walnut'], L['knit_sage']], 'House', smooth=True)
    # the shuttered triple window on the street wall (PrimWF, x 2.95..4.95): stool + apron on the room side,
    # linen drapes on a black rod with rings + brackets, gathered at both ends (the centre pane stays clear:
    # the film ends looking out through it)
    o = BY_NAME['PrimWF']
    yw = WINGY0 + WT                                                    # inner face of the front wall (6.25)
    mb = MB()
    mb.box(o['a0'] - 0.11, o['a1'] + 0.11, yw, yw + 0.06, o['z0'] - 0.035, o['z0'] - 0.005, 0)      # stool
    mb.box(o['a0'] - 0.09, o['a1'] + 0.09, yw, yw + 0.018, o['z0'] - 0.115, o['z0'] - 0.035, 0)     # apron
    mb.build("Up_Stool_PrimWF", [M['trim']], 'House')
    mb = MB()
    zc = o['z1'] + 0.19
    _rod(mb, (o['a0'] - 0.25, yw + 0.09, zc), (min(o['a1'] + 0.09, XW - 0.03), yw + 0.09, zc), 0, rings=18)
    for xx in (o['a0'] - 0.18, (o['a0'] + o['a1']) / 2, min(o['a1'] + 0.02, XW - 0.1)):
        _bracket(mb, (xx, yw, zc), (xx, yw + 0.09, zc), 0)
    mb.build("Up_Rod_Prim", [M['iron_black']], 'House', smooth=True)
    mb = MB()
    _curtain(mb, 'X', o['a0'] - 0.23, o['a0'] + 0.10, yw + 0.075, zf + 0.01, zc - 0.03, 0, depth=0.05, folds=3, seed=1)
    _curtain(mb, 'X', o['a1'] - 0.33, min(o['a1'] + 0.04, XW - 0.05), yw + 0.075, zf + 0.01, zc - 0.03, 0, depth=0.05, folds=3, seed=2)
    for xx in (o['a0'] - 0.07, o['a1'] - 0.15):                                                  # tie-backs
        mb.rcbox(xx, yw + 0.1, Z_UP + 1.0, 0.2, 0.09, 0.05, 0.02, 1, puff=0.3)
    mb.build("Up_Drapes_Prim", [L['drape_linen'], L['knit_grey']], 'House', smooth=True)
    # art over the bed (+X wall): framed + matted, sconces with real fixtures, ceiling dome
    mb = MB()
    _framed(mb, 'Y', 8.5, 9.9, XW, -1, Z_UP + 1.4, Z_UP + 2.2, 0, 1, 2, d=0.035, fw=0.035, mat_w=0.07)
    mb.build("Up_Art_Prim", [M['ebony'], L['mat'], M['art_abstract']], 'House')
    room_light("Up_L_PrimFill", 'prim', energy=24, color=K30)
    # walk-in closet (photo 17): rods on both long walls, shelves above
    mb = MB()
    _garments(mb, 1.05, 6.4, 7.95, Z_UP + 1.7, +1, 0, [1, 2, 3, 1], n=6, seed=4, off=0.24, wid=0.34)
    _garments(mb, 2.3, 6.4, 7.95, Z_UP + 1.7, -1, 0, [2, 3, 1, 2], n=6, seed=5, off=0.24, wid=0.34)
    mb.build("Up_WIC_Rods", [M['chrome'], L['garment_a'], L['garment_b'], L['garment_c']], 'House', smooth=True)
    mb = MB()
    _shelf(mb, 1.05, 1.42, 6.3, 8.0, Z_UP + 1.95, 0)
    _shelf(mb, 1.93, 2.3, 6.3, 8.0, Z_UP + 1.95, 0)
    for xx in (1.15, 2.05):
        mb.rcbox(xx, 6.6, Z_UP + 2.09, 0.28, 0.36, 0.26, 0.02, 1)               # storage boxes
        mb.rcbox(xx, 7.2, Z_UP + 2.09, 0.28, 0.36, 0.26, 0.02, 1)
    mb.build("Up_WIC_Shelves", [M['trim'], M['fabric_sand']], 'House')
    add_light("Up_L_WIC", 'POINT', (1.67, 7.15, Z_UPC - 0.12), 15, K30, size=0.1)


# ================================================================== primary bath (photos 23 / 24)
def primary_bath(M):
    L = _local(M)
    zf = Z_UP + FLOOR_T
    x0, x1, y0, y1 = ROOMS['prim_bath'][:4]
    vx = x1 - 0.55                                                  # vanity front face
    zt = zf + 0.86                                                   # counter top
    # ---- vanity carcass + toe kick, raised-panel doors / drawer stacks (photo 23), brass hardware
    mb = MB()
    mb.box(vx,x1,12.62,14.9,zf+.1,zf+.12,0)
    mb.box(x1-.02,x1,12.62,14.9,zf+.1,zt-.03,0)
    for yy in (12.62,14.88):mb.box(vx,x1,yy,yy+.02,zf+.1,zt-.03,0)                                          # carcass
    mb.box(vx + 0.07, x1, 12.66, 14.86, zf, zf + 0.10, 1)                                          # toe kick (dark)
    ya, yb = 12.63, 14.89
    # layout along y: doors 0.42+0.42 | drawer stack 0.46 | doors 0.42+0.42 (sink base) | drawer stack 0.46 (rest)
    segs_ = [('d', 0.42), ('d', 0.42), ('w', 0.46), ('d', 0.42), ('d', 0.42)]
    total = sum(w for _, w in segs_)
    scale = (yb - ya - 0.02) / total
    yy = ya + 0.01
    top_z = zt - 0.03 - 0.02
    for kind, w in segs_:
        w *= scale
        if kind == 'd':
            _cabinet_door(mb, yy + 0.004, yy + w - 0.004, vx, zf + 0.30, top_z - 0.005, 0, 2, sign=-1, knob_a=yy + w - 0.06 if yy < 13.5 else yy + 0.06)
            _drawer_front(mb, yy + 0.004, yy + w - 0.004, vx, zf + 0.115, zf + 0.29, 0, 2, sign=-1)         # false / top drawer
        else:
            for i in range(4):
                z0 = zf + 0.115 + (top_z - 0.005 - zf - 0.115) * i / 4
                z1 = zf + 0.115 + (top_z - 0.005 - zf - 0.115) * (i + 1) / 4
                _drawer_front(mb, yy + 0.004, yy + w - 0.004, vx, z0 + 0.003, z1 - 0.003, 0, 2, sign=-1)
        yy += w
    mb.build("Up_Vanity_PBath", [L['vanity'], M['black'], M['brass']], 'House', bevel=0.002)
    # ---- granite top with two oval drop-in sinks (holes cut with elliptical ring slabs), backsplash, bullnose lip
    mb = MB()
    sinks = ((x1 - 0.28, 13.02), (x1 - 0.28, 14.45))
    rx, ry = 0.19, 0.245
    zones = [(12.6, 13.45), (14.02, 14.92)]
    mb.box(vx - 0.02, x1, 13.45, 14.02, zt - 0.03, zt, 0)
    for (sx, sy), (za, zb) in zip(sinks, zones):
        _ring_slab(mb, sx, sy, rx * 0.96, ry * 0.96, vx - 0.02, x1, za, zb, zt - 0.03, zt, 0)
    mb.box(vx - 0.03, vx - 0.02, 12.6, 14.92, zt - 0.03, zt + 0.004, 0)                              # bullnose lip (proud)
    mb.box(x1 - 0.02, x1, 12.6, 14.92, zt, zt + 0.10, 0)                                             # backsplash
    mb.build("Up_Top_PBath", [L['granite_pink']], 'House', bevel=0.004)
    mb = MB()
    for (sx, sy) in sinks:
        _oval_sink(mb, sx, sy, zt, rx, ry, 0)
        _widespread(mb, x1 - 0.10, sy, zt, 1, dir=(-1, 0))
    mb.lathe(x1 - 0.13, 13.6, zt, [(0, 0), (0.03, 0), (0.03, 0.14), (0.012, 0.16), (0.012, 0.19), (0, 0.19)], seg=12, mi=1)      # soap pump
    mb.lathe(x1 - 0.13, 13.8, zt, [(0, 0), (0.035, 0), (0.035, 0.09), (0, 0.09)], seg=12, mi=2)                                 # cup
    mb.rcbox(x1 - 0.25, 13.72, zt + 0.02, 0.22, 0.14, 0.04, 0.012, 3, puff=0.4)                                                  # folded hand towel
    mb.build("Up_Basins_PBath", [M['porcelain'], M['brass'], M['ceramic'], L['towel_sage']], 'House', smooth=True)
    # ---- mirror wall around the window (photo 23), brass light bar over the -Y panel, sconce by the window
    mb = MB()
    mb.wall('Y', 12.62, 14.9, x1 - 0.01, x1 - 0.002, Z_UP + 1.0, Z_UP + 2.35, holes=[(13.11, 14.19, Z_UP + 1.0, Z_UP + 2.24)], mi=0)
    mb.build("Up_Mirror_PBath", [M['mirror']], 'House')
    mb = MB()
    from archviz.parts import twin_sconce
    for yy in (12.82,14.65):
        twin_sconce(mb,x1-.01,yy,Z_UP+1.90,-1,0,0,1)
    mb.build("Up_Lights_PBath", [M['brass'], L['glow']], 'House', smooth=True)
    add_light("Up_L_PBathBar", 'POINT', (x1 - 0.15, 12.87, Z_UP + 2.12), 18, K30, size=0.12)
    add_light("Up_L_PBathShower", 'POINT', (3.15, 14.5, Z_UP + 2.1), 14, K30, size=0.1)
    add_light("Up_L_PBathSconce", 'POINT', (x1 - 0.13, 14.55, Z_UP + 1.86), 10, K30, size=0.05)
    # ---- shower (x 2.7..3.6, y 14.0..14.95): 4" cream tile, granite accents, pan + drain, corner shelf, brass frame + glass
    mb = MB()
    mb.box(x0, x0 + 0.01, 13.98, y1, zf, Z_UP + 2.2, 1)                                             # -X wall tiles (YZ)
    mb.box(x0, 3.62, y1 - 0.01, y1, zf, Z_UP + 2.2, 0)                                              # +Y wall tiles (XZ)
    for row in range(3):
        for col in range(3):
            if (row+col)%2==0:
                xx=x0+.055+col*.30;zz=Z_UP+1.10+row*.30
                mb.box(xx,xx+.295,y1-.014,y1-.01,zz,zz+.295,2)
    # recessed toiletry niche, inset stone border and a usable shelf
    mb.box(x0+.10,x0+.48,y1-.018,y1-.013,Z_UP+.90,Z_UP+1.15,2)
    mb.box(x0+.12,x0+.46,y1-.019,y1-.018,Z_UP+.92,Z_UP+1.13,1)
    mb.box(x0+.10,x0+.48,y1-.09,y1-.015,Z_UP+.90,Z_UP+.92,2)
    mb.box(x0, 3.62, 13.98, y1, zf, zf + 0.03, 3)                                                   # pan
    mb.box(x0, 3.62, 13.93, 14.0, zf, zf + 0.10, 3)                                                 # curb
    mb.box(3.56, 3.62, 13.93, y1, zf, zf + 0.10, 3)
    mb.prism([(x0 + 0.01, y1 - 0.01), (x0 + 0.27, y1 - 0.01), (x0 + 0.01, y1 - 0.27)], Z_UP + 1.05, Z_UP + 1.07, 2)   # corner shelf
    mb.v=[(x,y-.018 if y>y1-.035 else y,z) for x,y,z in mb.v]
    mb.build("Up_Shower_Tile", [L['cream'], L['cream_y'], L['granite_pink'], L['cream_floor']], 'House')
    mb = MB()
    mb.cbox(3.15, 14.47, zf + 0.031, 0.10, 0.10, 0.003, 0)                                          # drain
    for i in range(4):
        mb.cbox(3.15, 14.47 - 0.03 + 0.02 * i, zf + 0.0335, 0.08, 0.004, 0.001, 1)
    mb.build("Up_Shower_Drain", [M['brass'], L['dark']], 'House')
    mb = MB()          # 0 brass, 1 glass
    zg0, zg1 = zf + 0.10, Z_UP + 2.05
    mb.box(3.575, 3.595, 14.02, y1 - 0.01, zg0, zg1, 1)                                            # fixed side panel
    mb.box(x0 + 0.03, 3.54, 14.005, 14.015, zg0, zg1, 1)                                             # door (closed)
    mb.box(3.56, 3.61, 13.99, y1, zg1, zg1 + 0.03, 0); mb.box(x0, 3.61, 13.985, 14.035, zg1, zg1 + 0.03, 0)   # header
    mb.box(3.56, 3.61, 13.99, 14.035, zg0 - 0.005, zg1, 0)                                          # corner post
    mb.box(3.56, 3.61, y1 - 0.03, y1, zg0 - 0.005, zg1, 0); mb.box(x0, x0 + 0.03, 13.985, 14.035, zg0 - 0.005, zg1, 0)   # jambs
    mb.box(3.56, 3.61, 14.02, y1, zg0 - 0.005, zg0 + 0.02, 0)                                       # sill channel
    for zz in (zg0 + 0.25, zg1 - 0.25):                                                             # hinges
        mb.box(x0 + 0.02, x0 + 0.06, 13.995, 14.025, zz - 0.04, zz + 0.04, 0)
    mb.build("Up_Shower_Frame", [M['brass'], L['shower_glass']], 'House')
    mb = MB()
    for yy in (14.0, 14.03):                                                                          # D-handle both sides
        mb.tube((3.35, yy - 0.06 * (1 if yy < 14.01 else -1), Z_UP + 0.95), (3.35, yy - 0.06 * (1 if yy < 14.01 else -1), Z_UP + 1.25), 0.008, 0.008, seg=8, mi=0)
        for zz in (Z_UP + 0.95, Z_UP + 1.25):
            mb.tube((3.35, yy, zz), (3.35, yy - 0.06 * (1 if yy < 14.01 else -1), zz), 0.008, 0.008, seg=8, mi=0)
    mb.tube((x0 + 0.01, 14.45, Z_UP + 2.0), (x0 + 0.22, 14.45, Z_UP + 2.05), 0.012, 0.012, seg=8, mi=0)
    mb.lathe(x0 + 0.24, 14.45, Z_UP + 2.0, [(0, 0), (0.05, 0), (0.05, 0.015), (0.012, 0.03), (0, 0.03)], seg=16, mi=0)   # head
    _face_box(mb, x0 + 0.01, 14.45, 1, 0, Z_UP + 1.15, 0.09, 0.02, 0.09, 0)                        # valve plate
    mb.tube((x0 + 0.03, 14.45, Z_UP + 1.15), (x0 + 0.08, 14.45, Z_UP + 1.15), 0.012, 0.012, seg=8, mi=0)   # valve knob
    mb.lathe(x0 + 0.06, y1 - 0.06, Z_UP + 1.07, [(0, 0), (0.025, 0), (0.025, 0.12), (0.012, 0.135), (0.012, 0.16), (0, 0.16)], seg=10, mi=1)   # shampoo bottle
    mb.build("Up_Shower_Brass", [M['brass'], M['ceramic_black']], 'House', smooth=True)
    # ---- toilet against the -X wall with a paper holder, towel bar + towel, bath mat, bin, floor accents
    mb = MB()
    _toilet(mb, 2.98, 13.2, zf, math.pi / 2, 0, mi_metal=1)
    mb.build("Up_Toilet_PBath", [M['porcelain'], M['brass']], 'House', smooth=True)
    mb = MB()
    _towel_bar(mb, x0, 12.9, Z_UP + 1.2, 1, 0, 0.55, 0, mi_towel=1, along='Y', towel_w=0.42)
    mb.tube((x0, 13.75, Z_UP + 0.7), (x0 + 0.08, 13.75, Z_UP + 0.7), 0.006, 0.006, seg=8, mi=0)      # paper holder
    mb.tube((x0 + 0.08, 13.62, Z_UP + 0.7), (x0 + 0.08, 13.88, Z_UP + 0.7), 0.006, 0.006, seg=8, mi=0)
    mb.tube((x0 + 0.08, 13.70, Z_UP + 0.7), (x0 + 0.08, 13.80, Z_UP + 0.7), 0.05, 0.05, seg=16, mi=2)   # paper roll
    mb.build("Up_Towel_PBath", [M['brass'], L['towel'], M['paper']], 'House', smooth=True)
    mb = MB()
    mb.lathe(vx - 0.15, 12.75, zf, [(0, 0), (0.11, 0), (0.12, 0.28), (0.11, 0.28), (0.10, 0.02), (0, 0.02)], seg=18, mi=1)   # bin
    mb.build("Up_Deco_PBath", [L['towel_sage'], M['black_metal']], 'House', smooth=True)
    mb = MB()
    for (cx, cy) in ((3.4, 12.9), (3.8, 13.2), (3.4, 13.5), (4.15, 12.85), (3.95, 13.75)):
        mb.cbox(cx, cy, zf + 0.001, 0.15, 0.15, 0.002, 0, rot=math.pi / 4)                                # granite floor accents (flat shaded)
    mb.build("Up_FloorAccents_PBath", [L['granite_floor']], 'House')
    mb = MB()
    mb.rbox(vx - 0.55, vx - 0.05, 13.35, 14.05, zf + 0.002, zf + 0.02, 0.008, 0, seg=2)                     # bath mat (flat shaded)
    mb.build("Up_Mat_PBath", [L['towel_sage']], 'House')
    mb = MB()
    pts = [(3.95, 13.1), (3.95, 14.3)]
    downlights(mb, pts, Z_UPC, r=0.05, mi=0, mi_trim=1)
    mb.build("Up_Downlights_PBath", [M['emit_down'], M['black_metal']], 'House')
    for i, (px, py) in enumerate(pts):
        add_light(f"Up_L_PBathDown_{i}", 'SPOT', (px, py, Z_UPC - 0.02), 18, K30, size=0.04, spot=math.radians(70), blend=0.6, target=(px, py, zf))
    room_light("Up_L_PBathFill", 'prim_bath', energy=12, color=K30)


# ================================================================== hall bath (photo 19)
def hall_bath(M):
    L = _local(M)
    zf = Z_UP + FLOOR_T
    x0, x1, y0, y1 = ROOMS['hall_bath'][:4]
    # tile skins around the tub alcove (y 14.05..14.8): +Y wall (XZ), both side walls (YZ); accent row at z +1.1
    mb = MB()
    zt = Z_UP + 2.25
    o=BY_NAME['HallBathWN']
    mb.wall('X',x0,x1,y1-.025,y1-.015,zf,zt,holes=[(o['a0'],o['a1'],o['z0'],o['z1'])],mi=0)
    mb.box(x0, x0 + 0.01, 13.95, y1, zf, zt, 1)
    mb.box(x1 - 0.01, x1, 13.95, y1, zf, zt, 1)
    from .interior_back import _checker
    _checker(mb,'X',x0,x1,y1-.025,-1,Z_UP+.60,2,2,3,0,t=.15)
    _checker(mb,'Y',13.95,y1,x0,1,Z_UP+.60,2,2,3,0,t=.15)
    _checker(mb,'Y',13.95,y1,x1,-1,Z_UP+.60,2,2,3,0,t=.15)
    peach=_mat.new_mat('HBathPlainPeach',(.78,.40,.25,1),rough=.23,coat=.6)
    teal=_mat.new_mat('HBathPlainTeal',(.12,.30,.30,1),rough=.23,coat=.6)
    mb.build("Up_HBath_Tile", [M['tile_white'],M['tile_white_y'],peach,teal,peach,teal], 'House')
    # alcove tub: rolled rim, apron, hollow basin
    mb = MB()
    tx0, tx1, ty0, ty1 = x0 + 0.02, x1 - 0.02, 14.05, y1 - 0.02
    mb.box(tx0, tx1, ty0, ty0 + 0.04, zf, zf + 0.55, 0)                                     # apron
    mb.box(tx0, tx1, ty0, ty1, zf, zf + 0.10, 0)                                            # bottom
    mb.box(tx0, tx0 + 0.06, ty0, ty1, zf, zf + 0.55, 0); mb.box(tx1 - 0.06, tx1, ty0, ty1, zf, zf + 0.55, 0)
    mb.box(tx0, tx1, ty1 - 0.06, ty1, zf, zf + 0.55, 0)
    mb.frame(tx0 - 0.01, tx1 + 0.01, ty0 - 0.01, ty1 + 0.01, zf + 0.53, zf + 0.57, 0.08, mi=0, axis='Z')   # rolled rim
    mb.build("Up_HBath_Tub", [M['porcelain']], 'House', bevel=0.012)
    mb = MB()          # 0 chrome, 1 brass
    _rod(mb, (x0 + 0.02, 14.06, Z_UP + 1.95), (x1 - 0.02, 14.06, Z_UP + 1.95), 0, r=0.012, rings=10, finial=False)   # curtain rod + rings
    for xx in (x0 + 0.02, x1 - 0.02):
        _face_box(mb, xx, 14.06, 1 if xx < 2.0 else -1, 0, Z_UP + 1.95, 0.05, 0.008, 0.05, 0)
    mb.tube((x1 - 0.06, y1 - 0.05, Z_UP + 0.9), (x1 - 0.06, y1 - 0.05, Z_UP + 1.75), 0.012, 0.012, seg=8, mi=1)
    mb.tube((x1 - 0.06, y1 - 0.05, Z_UP + 1.75), (x1 - 0.2, y1 - 0.05, Z_UP + 1.72), 0.012, 0.012, seg=8, mi=1)  # shower arm
    mb.lathe(x1 - 0.22, y1 - 0.05, Z_UP + 1.68, [(0, 0), (0.04, 0), (0.04, 0.012), (0.01, 0.03), (0, 0.03)], seg=14, mi=1)
    mb.tube((x1 - 0.013, 14.45, Z_UP + 0.72), (x1 - 0.13, 14.45, Z_UP + 0.70), 0.012, 0.010, seg=8, mi=1)     # tub spout
    for dy in (-0.09, 0.09):                                                                                  # cross handles
        mb.tube((x1 - 0.013, 14.45 + dy, Z_UP + 0.9), (x1 - 0.05, 14.45 + dy, Z_UP + 0.9), 0.012, 0.010, seg=8, mi=1)
        mb.cbox(x1 - 0.055, 14.45 + dy, Z_UP + 0.9, 0.008, 0.045, 0.008, 1); mb.cbox(x1 - 0.055, 14.45 + dy, Z_UP + 0.9, 0.008, 0.008, 0.045, 1)
    _towel_bar(mb, x0, 13.3, Z_UP + 1.15, 1, 0, 0.5, 0, mi_towel=None, along='Y')
    mb.tube((x1, 12.95, Z_UP + 0.75), (x1 - 0.08, 12.95, Z_UP + 0.75), 0.006, 0.006, seg=8, mi=0)              # paper holder
    mb.tube((x1 - 0.08, 12.82, Z_UP + 0.75), (x1 - 0.08, 13.08, Z_UP + 0.75), 0.006, 0.006, seg=8, mi=0)
    mb.build("Up_HBath_Metal", [M['chrome'], M['brass']], 'House', smooth=True)
    mb = MB()
    _folded_towel(mb, x0 + 0.08, 13.3, Z_UP + 1.15, 1, 0, 0, w=0.36)
    mb.tube((x1 - 0.08, 12.9, Z_UP + 0.75), (x1 - 0.08, 13.0, Z_UP + 0.75), 0.05, 0.05, seg=16, mi=1)           # paper roll
    mb.rbox(x0 + 0.3, x1 - 0.3, 13.55, 13.98, zf, zf + 0.016, 0.01, 0, seg=2, puff=0.4)                        # bath mat
    mb.build("Up_HBath_Soft", [L['towel'], M['paper']], 'House', smooth=True)
    # pedestal sink on the +X wall, medicine cabinet, toilet
    mb = MB()
    _pedestal_sink(mb, x1 - 0.30, 13.2, zf, 0, 1, r=0.24)
    mb.lathe(x1 - 0.12, 13.45, zf + 0.82, [(0, 0), (0.03, 0), (0.03, 0.08), (0, 0.08)], seg=10, mi=0)         # cup
    mb.build("Up_HBath_Sink", [M['porcelain'], M['chrome']], 'House', smooth=True)
    mb = MB()
    mb.box(x1 - 0.12, x1 - 0.01, 12.95, 13.45, Z_UP + 1.25, Z_UP + 1.95, 0)
    mb.box(x1 - 0.125, x1 - 0.12, 12.97, 13.43, Z_UP + 1.27, Z_UP + 1.93, 1)
    mb.build("Up_HBath_Cabinet", [M['trim'], M['mirror']], 'House')
    mb = MB()
    _toilet(mb, 1.4, 13.55, zf, math.pi / 2, 0, mi_metal=1)      # tank against the -X wall
    mb.build("Up_HBath_Toilet", [M['porcelain'], M['chrome']], 'House', smooth=True)
    mb = MB()
    from archviz.parts import twin_sconce
    twin_sconce(mb,x1-.13,13.2,Z_UP+2.04,-1,0,0,1)
    mb.build("Up_HBath_Light", [M['chrome'], L['glow']], 'House', smooth=True)
    add_light("Up_L_HBath", 'POINT', ((x0 + x1) / 2, 13.3, Z_UPC - 0.18), 25, K30, size=0.1)
    room_light("Up_L_HBathFill", 'hall_bath', energy=6, color=K30)


# ================================================================== bedroom 2 (photos 16 / 26)
def bed2(M):
    L = _local(M)
    zf = Z_UP + FLOOR_T
    # full bed, headboard on the +X wall (own +Y -> +X: rot -90): y 8.2..9.55, so the closet door (-Y wall) and
    # the slider -> hall-door corridor (y > 9.6) stay clear
    mb = MB()
    bx, by = -1.555, 9.02
    bed(mb, bx, by, rot=-math.pi / 2, z=zf, w=1.4, l=1.95, mi_frame=0, mi_linen=1, mi_pillow=3, mi_throw=2, mi_duvet=4, head_h=1.0, seed=5, channels=3)
    mb.build("Up_Bed_Bed2", [M['fabric'], L['sheet'], L['knit_oat'], L['pillow'], L['duvet_grey']], 'House', smooth=True, subsurf=1)
    mb = MB(); _rug(mb, -2.95, -1.1, 8.2, 9.95, zf, 0, 1)
    mb.build("Up_Rug_Bed2", [M['rug_blue'], L['rug_border_blue']], 'House')
    mb = MB()
    for yy in (10.0,):                                                  # one nightstand: the -Y side is the closet door's swing
        _nightstand(mb, -0.75, yy, zf, 0.46, 0.44, 0.56, 0, 1, nx=-1, ny=0, drawers=1)
    _dresser(mb, -3.1, -2.35, 10.9, 11.43, zf, 0.85, 0, 1, drawers=3, front='-Y')
    mb.build("Up_Case_Bed2", [M['oak_pale'], M['black_metal']], 'House', bevel=0.004)
    mb = MB()
    for yy in (10.0,):
        _lamp(mb, -0.75, yy, zf + 0.56, 0, 1, 2, 3, base_r=0.085, base_h=0.24, shade_r=0.14, shade_h=0.19)
        add_light(f"Up_L_Bed2Lamp_{yy * 10:.0f}", 'POINT', (-0.75, yy, zf + 0.56 + 0.38), 12, K30, size=0.07)
    mb.build("Up_Lamps_Bed2", [M['ceramic'], M['lampshade'], M['brass'], L['bulb']], 'House', smooth=True)
    mb = MB()
    vase(mb, -2.75, 11.15, zf + 0.85, h=0.22, r=0.07, mi=0, style='round')
    _books(mb, -2.95, 11.15, zf + 0.85, 1, rot=-0.2, n=2)
    mb.rcbox(-2.5, 11.15, zf + 0.86, 0.18, 0.12, 0.02, 0.006, 0)                                         # small tray
    mb.build("Up_Deco_Bed2", [M['ceramic_black'], M['book']], 'House', smooth=True)
    _pl.stems("Up_Stems_Bed2", (-2.75, 11.15, zf + 0.85 + 0.22), kind='olive', height=0.4, seed=5, n=4)
    # reading chair in the -X / -Y corner beside the slider, with a knit throw
    mb = MB()
    armchair(mb, -2.62, 8.15, rot=math.pi * 0.75, z=zf, w=0.68, d=0.7, mi=0, mi_legs=1, style='barrel')
    mb.rcbox(-2.6, 8.17, zf + 0.60, 0.36, 0.26, 0.035, 0.012, 2, rot=math.pi * 0.75, puff=0.6)
    mb.build("Up_Chair_Bed2", [M['fabric_sand'], M['walnut'], L['knit_rust']], 'House', smooth=True)
    # grey curtains on the slider (both ends gathered), black rod with rings + 3 brackets
    mb = MB()
    zc = Z_UP + 2.24
    _rod(mb, (-3.09, 8.4, zc), (-3.09, 10.95, zc), 0, rings=16)
    for yy in (8.48, 9.68, 10.87):
        _bracket(mb, (-3.15, yy, zc), (-3.09, yy, zc), 0)
    mb.build("Up_Rod_Bed2", [M['iron_black']], 'House', smooth=True)
    mb = MB()
    _curtain(mb, 'Y', 8.46, 8.9, -3.07, zf + 0.01, zc - 0.03, 0, depth=0.05, folds=4, seed=3)
    _curtain(mb, 'Y', 10.5, 10.88, -3.07, zf + 0.01, zc - 0.03, 0, depth=0.05, folds=3, seed=4)   # clear of the open half (y 9.5..10.4)
    mb.build("Up_Drapes_Bed2", [M['fabric_grey']], 'House', smooth=True)
    # sconces flanking the headboard on the +X wall, flush drum on the ceiling, framed print over the bed
    mb = MB()
    for yy in (8.98,10.0):
        _sconce(mb, -0.5, yy, Z_UP + 1.75, -1, 0, 0, 1)
        add_light(f"Up_L_Bed2Sconce_{yy * 10:.0f}", 'POINT', (-0.61, yy, Z_UP + 1.77), 8, K30, size=0.05)
    # Original wall sconces provide the permanent lighting (photo 26).
    mb.build("Up_Fixtures_Bed2", [M['iron_black'], L['glow_soft']], 'House', smooth=True)
    add_light("Up_L_Bed2Ceiling", 'POINT', (-1.85, 9.7, Z_UPC - 0.09), 40, K30, size=0.14)
    room_light("Up_L_Bed2Fill", 'bed2', energy=18, color=K30)
    mb = MB()
    _framed(mb, 'Y', 9.1, 9.65, -0.5, -1, Z_UP + 1.35, Z_UP + 2.1, 0, 1, 2, d=0.03, fw=0.03, mat_w=0.06)
    mb.build("Up_Art_Bed2", [M['oak'], L['mat'], M['art_bw']], 'House')
    # wic2: one rod along the +Y wall + shelves
    mb = MB()
    xr0, xr1 = -3.05, -0.6
    yr = 7.45 - 0.30
    _rod(mb, (xr0, yr, Z_UP + 1.7), (xr1, yr, Z_UP + 1.7), 0, finial=False)
    _rod(mb,(-3.05,6.49,Z_UP+1.70),(-.6,6.49,Z_UP+1.70),0,finial=False)
    mb.build("Up_WIC2_Rod", [M['chrome'], L['garment_a'], L['garment_b'], L['garment_c']], 'House', smooth=True)
    mb = MB()
    _shelf(mb, -3.1, -0.55, 7.18, 7.44, Z_UP + 1.95, 0)
    _shelf(mb,-3.1,-.55,6.26,6.51,Z_UP+1.95,0)
    mb.build("Up_WIC2_Shelves", [M['trim'], M['fabric_sand']], 'House')
    mb=MB();_flush(mb,-1.8,6.85,Z_UPC,0,1,style='dome',r=.075)
    mb.build('Up_WIC2_OriginalLight',[M['trim'],L['glow_soft']],'House',smooth=True)
    add_light("Up_L_WIC2", 'POINT', (-1.8, 6.85, Z_UPC - 0.12), 12, K30, size=0.1)


# ================================================================== rear bedroom (photos 18 / 20)
def bed3(M):
    L = _local(M)
    zf = Z_UP + FLOOR_T
    # queen bed, headboard on the y 11.6 wall (own +Y -> -Y)
    mb = MB()
    bed(mb, -1.65, 12.7, rot=math.pi, z=zf, w=1.6, l=2.1, mi_frame=0, mi_linen=1, mi_pillow=3, mi_throw=2, mi_duvet=4, head_h=1.1, seed=8, channels=4)
    mb.build("Up_Bed_Bed3", [M['fabric_sand'], L['sheet'], L['knit_sage'], L['pillow'], L['duvet']], 'House', smooth=True, subsurf=1)
    mb = MB(); _rug(mb, -2.85, -0.45, 13.3, 15.1, zf, 0, 1)
    mb.build("Up_Rug_Bed3", [M['rug_camel'], L['rug_border']], 'House')
    mb = MB()
    for xx in (-2.85, -0.45):
        _nightstand(mb, xx, 11.95, zf, 0.5, 0.45, 0.56, 0, 1, nx=0, ny=1, drawers=1)
    _dresser(mb, 0.4, 0.9, 14.4, 15.1, zf, 0.9, 0, 1, drawers=3, front='-X')
    mb.build("Up_Case_Bed3", [M['oak_pale'], M['black_metal']], 'House', bevel=0.004)
    # desk under the -X window: top on two trestle legs, a drawer, a laptop, books, a task lamp
    mb = MB()
    dx, dy = -2.85, 14.9
    mb.rbox(dx - 0.28, dx + 0.28, dy - 0.65, dy + 0.65, zf + 0.72, zf + 0.75, 0.006, 0, seg=2)
    for sy in (-1, 1):
        for sx in (-1, 1):
            mb.cbox(dx + sx * 0.22, dy + sy * 0.58, zf + 0.36, 0.035, 0.035, 0.72, 0)
        mb.cbox(dx, dy + sy * 0.58, zf + 0.10, 0.44, 0.035, 0.035, 0)
    mb.rbox(dx - 0.24, dx + 0.24, dy - 0.25, dy + 0.25, zf + 0.62, zf + 0.715, 0.005, 0, seg=2)              # drawer box
    mb.cbox(dx + 0.255, dy, zf + 0.667, 0.012, 0.12, 0.012, 1)                                                # pull
    mb.build("Up_Desk_Bed3", [M['oak'], M['black_metal']], 'House', bevel=0.003)
    mb = MB()
    dining_chair(mb, -2.35, 14.9, rot=-math.pi / 2, z=zf, mi_wood=0, mi_seat=1)    # faces -X (toward the desk)
    mb.build("Up_Chair_Bed3", [M['oak'], M['fabric_sand']], 'House', bevel=0.004)
    mb = MB()          # laptop: base + screen tilted back, a mug, books, a task lamp
    mb.rcbox(-2.82, 14.75, zf + 0.758, 0.30, 0.21, 0.014, 0.004, 0, rot=-math.pi / 2 + 0.15)
    mb.cbox(-2.945, 14.75, zf + 0.86, 0.008, 0.30, 0.20, 0, rot=0.0)                                            # screen (upright)
    mb.cbox(-2.94, 14.75, zf + 0.86, 0.002, 0.28, 0.18, 1)
    mb.lathe(-2.7, 15.3, zf + 0.75, [(0, 0), (0.035, 0), (0.037, 0.09), (0, 0.09)], seg=12, mi=2)              # mug
    mb.build("Up_Laptop_Bed3", [L['laptop'], L['screen'], M['ceramic']], 'House', smooth=True)
    mb = MB()
    _books(mb, -2.85, 15.35, zf + 0.75, 0, rot=0.1, n=3)
    vase(mb, 0.65, 14.75, zf + 0.9, h=0.26, r=0.08, mi=1, style='bowl')
    mb.build("Up_Deco_Bed3", [M['book'], M['ceramic']], 'House', smooth=True)
    mb = MB()          # task lamp: base, arm, shade (brass) + bulb
    mb.lathe(-2.85, 14.42, zf + 0.75, [(0, 0), (0.06, 0), (0.05, 0.015), (0.008, 0.02), (0, 0.02)], seg=14, mi=0)
    mb.tube((-2.85, 14.42, zf + 0.77), (-2.85, 14.5, zf + 1.05), 0.006, 0.006, seg=8, mi=0)
    mb.tube((-2.85, 14.5, zf + 1.05), (-2.78, 14.62, zf + 1.02), 0.006, 0.006, seg=8, mi=0)
    mb.lathe(-2.76, 14.66, zf + 0.92, [(0, 0.1), (0.02, 0.1), (0.07, 0.0), (0.066, 0.0), (0.018, 0.096), (0, 0.096)], seg=16, mi=0)
    mb.sphere((-2.76, 14.66, zf + 0.95), 0.018, seg=10, rings=6, mi=1)
    mb.build("Up_TaskLamp_Bed3", [M['brass'], L['bulb']], 'House', smooth=True)
    add_light("Up_L_Bed3Task", 'POINT', (-2.76, 14.66, zf + 0.93), 6, K30, size=0.03)
    mb = MB()
    for xx in (-2.85, -0.45):
        _lamp(mb, xx, 11.95, zf + 0.56, 0, 1, 2, 3, base_r=0.09, base_h=0.26, shade_r=0.15, shade_h=0.2)
        add_light(f"Up_L_Bed3Lamp_{abs(xx) * 10:.0f}", 'POINT', (xx, 11.95, zf + 0.56 + 0.4), 12, K30, size=0.07)
    mb.build("Up_Lamps_Bed3", [M['ceramic'], M['lampshade'], M['brass'], L['bulb']], 'House', smooth=True)
    # bench under the 3-window group, sheers on a black rod with rings
    mb = MB()
    mb.rcbox(-1.5, 16.17, zf + 0.42, 1.2, 0.38, 0.09, 0.03, 0, puff=0.4)
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.cylinder(-1.5 + sx * 0.52, 16.17 + sy * 0.14, zf, zf + 0.38, 0.02, 0.016, seg=8, mi=1)
    mb.rcbox(-1.5, 16.17, zf + 0.375, 1.16, 0.34, 0.03, 0.01, 1)
    mb.build("Up_Bench_Bed3", [L['leather'], M['walnut']], 'House', smooth=True)
    mb = MB()
    zc = Z_UP + 2.24
    _rod(mb, (-2.95, 16.21, zc), (-0.05, 16.21, zc), 0, rings=18)
    for xx in (-2.88, -1.5, -0.12):
        _bracket(mb, (xx, BED_REAR, zc), (xx, 16.21, zc), 0)
    mb.build("Up_Rod_Bed3", [M['iron_black']], 'House', smooth=True)
    mb = MB()
    _curtain(mb, 'X', -2.92, -2.55, 16.23, zf + 0.01, zc - 0.03, 0, depth=0.045, folds=3, seed=5)
    _curtain(mb, 'X', -0.45, -0.08, 16.23, zf + 0.01, zc - 0.03, 0, depth=0.045, folds=3, seed=6)
    mb.build("Up_Sheers_Bed3", [L['sheer']], 'House', smooth=True)
    # flush drum on the ceiling (photo 20 has a flat panel; a drum reads better), framed print over the bed
    mb = MB()
    from .interior_back import _flush_mount
    _flush_mount(mb,-1.4,14.4,Z_UPC,1,0,size=.34)
    mb.build("Up_Fixture_Bed3", [M['trim'], L['glow_soft']], 'House', smooth=True)
    add_light("Up_L_Bed3Ceiling", 'POINT', (-1.4, 14.4, Z_UPC - 0.09), 50, K30, size=0.16)
    room_light("Up_L_Bed3Fill", 'bed3', energy=18, color=K30)
    mb = MB()
    _framed(mb, 'X', -2.3, -1.0, 11.6, 1, Z_UP + 1.35, Z_UP + 2.15, 0, 1, 2, d=0.03, fw=0.035, mat_w=0.06)
    mb.build("Up_Art_Bed3", [M['ebony'], L['mat'], M['art_lines']], 'House')
    # closet3: rod + shelf behind the sliding doors
    mb = MB()
    _rod(mb, (1.2, 15.25, Z_UP + 1.7), (1.2, 16.25, Z_UP + 1.7), 0, finial=False)
    rng = random.Random(11)
    for i in range(5):
        yy = 15.2 + 1.4 * i / 4 + rng.uniform(-0.02, 0.02)
        hgt = rng.uniform(0.7, 0.95)
        mb.rbox(1.0, 1.42, yy - 0.014, yy + 0.014, Z_UP + 1.61 - hgt, Z_UP + 1.61, 0.012, 1 + i % 3, seg=2)
    mb.build("Up_Closet3_Rod", [M['chrome'], L['garment_a'], L['garment_b'], L['garment_c']], 'House', smooth=True)
    mb = MB(); _shelf(mb, 1.05, 1.40, 15.25, 16.3, Z_UP + 1.95, 0)
    mb.build("Up_Closet3_Shelf", [M['trim']], 'House')


# ================================================================== upper hall
def up_hall(M):
    L = _local(M)
    zf = Z_UP + FLOOR_T
    mb = MB(); _rug(mb, 0.1, 0.65, 10.7, 13.3, zf, 0, 1, bw=0.06)
    mb.build("Up_Runner_Hall", [M['rug_plum'], L['rug_border']], 'House')
    mb = MB()
    _flush(mb, 0.38, 12.0, Z_UPC, 0, 1, style='dome', r=0.14)
    mb.build("Up_Fixture_Hall", [M['brass'], L['glow']], 'House', smooth=True)
    add_light("Up_L_Hall", 'POINT', (0.38, 12.0, Z_UPC - 0.2), 40, K30, size=0.12)
    mb = MB()
    _framed(mb, 'Y', 11.7, 12.15, 0.9, -1, Z_UP + 1.4, Z_UP + 1.95, 0, 1, 2, d=0.025, fw=0.025, mat_w=0.04)
    _framed(mb, 'Y', 12.25, 12.55, 0.9, -1, Z_UP + 1.45, Z_UP + 1.9, 0, 1, 2, d=0.025, fw=0.025, mat_w=0.035)
    mb.build("Up_Art_Hall", [M['oak'], L['mat'], M['art_bw']], 'House')
    mb = MB()          # round mirror on the -X face (x -0.15) between the bed2 door and the bed3 door
    mb.cbox(-0.147, 12.55, Z_UP + 1.65, 0.006, 0.46, 0.46, 0)
    mb.frame(-0.15, -0.12, 12.30, 12.80, Z_UP + 1.40, Z_UP + 1.90, 0.025, mi=1, axis='X')
    mb.build("Up_Mirror_Hall", [M['mirror'], M['brass']], 'House')


# ================================================================== deck furniture (photo 16 shows the empty deck)
def deck(M):
    L = _local(M)
    mb = MB()          # 0 cushion, 1 teak; chairs with slatted seats / backs (jeanneret) + sewn seat cushions
    for yy in (8.2, 11.0):
        armchair(mb, -4.6, yy, rot=math.pi / 2, z=DECK_Z, w=0.8, d=0.8, mi=1, mi_legs=1, style='jeanneret')
        mb.pillow_sq(-4.6, yy, DECK_Z + 0.50, 0.62, 0.60, 0.07, 0, rot=math.pi / 2, seed=int(yy * 3))
    mb.rcbox(-4.6, 11.0 + 0.05, DECK_Z + 0.56, 0.42, 0.34, 0.05, 0.015, 2, rot=0.2, puff=0.6)             # folded blanket on a seat
    mb.build("Up_Deck_Chairs", [M['fabric_sand'], M['teak'], L['blanket']], 'House', bevel=0.004, smooth=True)
    mb = MB()
    round_table(mb, -4.6, 8.95, DECK_Z, r=0.25, h=0.45, top_t=0.03, mi=0, legs='three')
    mb.build("Up_Deck_Table", [M['teak']], 'House')
    mb = MB()
    _lantern(mb, -4.55, 8.95, DECK_Z + 0.45, 0, 1, 2, 3, s=0.13, h=0.24)
    mb.lathe(-4.72, 9.05, DECK_Z + 0.45, [(0, 0), (0.035, 0), (0.035, 0.09), (0, 0.09)], seg=12, mi=4)          # cup
    mb.build("Up_Deck_Lantern", [M['iron_black'], M['glass'], L['wax'], L['candle'], M['ceramic']], 'House', smooth=True)
    add_light("Up_L_DeckCandle", 'POINT', (-4.55, 8.95, DECK_Z + 0.57), 3, (1.0, 0.7, 0.4), size=0.03)
    # planters: potted olive + boxwood ball at the -Y end, lavender at the +Y end (the slider corridor y 9.3..10.6 stays clear)
    _pl.potted("Up_Deck_Olive", (-5.15, 7.95, DECK_Z), kind='olive', height=1.25, pot='terracotta', pot_r=0.21, pot_h=0.30, seed=3)
    _pl.potted("Up_Deck_Boxwood", (-3.95, 7.85, DECK_Z), kind='boxwood', height=0.55, pot='concrete', seed=4)
    _pl.potted("Up_Deck_Lavender", (-3.95, 11.2, DECK_Z), kind='lavender', height=0.42, pot='terracotta', seed=5)


# ================================================================== entry point
def build(M):
    _local(M)
    finishes(M)
    primary(M)
    primary_bath(M)
    hall_bath(M)
    bed2(M)
    bed3(M)
    up_hall(M)
    deck(M)
