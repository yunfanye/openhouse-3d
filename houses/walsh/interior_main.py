"""Living level (Z_LIV): living pavilion with the onyx fireplace pier, dining under the oak-plank ceiling band,
kitchen with twin Calacatta islands, family room with the grey-travertine TV wall.  Photos 10, 11, 12, 13, 14.

Lighting follows the photos: pools of light from recessed downlights / linear slot lights, perimeter coves,
lit niches and the backlit onyx; the big per-room ceiling area light is only a weak fill now, so ceilings stay
darker than the lit walls."""
import math, random
from .plan import *
from archviz.mesh import *
from archviz.lights import *
from archviz.parts import *
from .interior_lower import (wall_trims, face_strips, door_set, floater_art, fireplace_insert,
                             fig_plant, rug, candle, tray, glassware, ceramics_row, basket, sq_pillow)
from archviz import materials as _mat

K30 = (1.0, 0.84, 0.66)          # 3000 K warm-white lamps (the photos are warm, not orange)

LIV = ROOMS['living']
DIN = ROOMS['dining']
KIT = ROOMS['kitchen']
FAM = ROOMS['family']

_L = {}


def _local(M):
    """Materials specific to this module (never added to materials.py)."""
    if _L:
        return _L
    _L['oak_hx'] = _mat.wood("KitchenOakHX", light=(0.85, 0.75, 0.59, 1), dark=(0.77, 0.66, 0.50, 1), grain_axis='X', rough=0.42, coat=0.12, ring=22.0)
    _L['oak_hy'] = _mat.wood("KitchenOakHY", light=(0.85, 0.75, 0.59, 1), dark=(0.77, 0.66, 0.50, 1), grain_axis='Y', rough=0.42, coat=0.12, ring=22.0)
    _L['oak_ceiling'] = _mat.wood_planks("DiningOakCeiling", light=(0.84, 0.72, 0.53, 1), dark=(0.77, 0.64, 0.45, 1), plank=(3.2, 0.24), along='Y', gap=0.002, rough=0.5, coat=0.06)
    _L['walnut_table'] = _mat.wood("WalnutTable", light=(0.36, 0.22, 0.12, 1), dark=(0.20, 0.11, 0.06, 1), grain_axis='Y', rough=0.35, coat=0.35, ring=14.0)
    _L['lemon'] = _mat.new_mat("Lemon", (0.95, 0.80, 0.10, 1), rough=0.45, coat=0.3)
    _L['ember'] = _mat.new_mat("EmberBed", (0.15, 0.05, 0.02, 1), rough=0.6, emit=(1.0, 0.35, 0.08, 1), emit_str=2.5)
    _L['cove_white'] = _mat.plaster("CoveWhite", base=(0.95, 0.94, 0.91, 1), rough=0.8, grain=0.02)
    # the library flame (emission 1.4) is too dim behind a glass face at room exposure: a brighter, yellower copy
    _L['fire_bright'] = _mat.fire("FireBright")
    for n in _L['fire_bright'].node_tree.nodes:
        if n.type == 'EMISSION':
            n.inputs["Strength"].default_value = 5.0
        if n.type == 'VALTORGB':
            n.color_ramp.elements[0].color = (1.0, 0.72, 0.28, 1)
    # dark walnut for the counter stools (photo 12) - the library walnut washes out to oak under the kitchen light
    _L['stool_walnut'] = _mat.wood("StoolWalnut", light=(0.28, 0.15, 0.08, 1), dark=(0.14, 0.07, 0.035, 1), grain_axis='Z', rough=0.38, coat=0.3)
    # bolder Calacatta for the islands / backsplash (photo 12: grey rivers you can see from across the room)
    _L['calacatta'] = _mat.marble("KitchenCalacatta", vein=(0.42, 0.40, 0.39, 1), vein2=(0.62, 0.58, 0.52, 1), scale=0.7, rough=0.1)
    return _L


# ---------------------------------------------------------------- geometry helpers
def _plate_holes(mb, x0, x1, y0, y1, z0, z1, holes, mi=0):
    """Horizontal slab minus arbitrary axis-aligned rectangles (they may share x ranges, unlike MB.plate)."""
    xs = sorted({x0, x1} | {h[0] for h in holes} | {h[1] for h in holes})
    xs = [x for x in xs if x0 <= x <= x1]
    for xa, xb in zip(xs, xs[1:]):
        if xb - xa < 1e-6:
            continue
        xm = (xa + xb) / 2
        cuts = sorted((h[2], h[3]) for h in holes if h[0] <= xm <= h[1])
        cur = y0
        for (hy0, hy1) in cuts:
            if hy0 > cur:
                mb.box(xa, xb, cur, hy0, z0, z1, mi)
            cur = max(cur, hy1)
        if y1 > cur:
            mb.box(xa, xb, cur, y1, z0, z1, mi)


def _ceiling(name, M, x0, x1, y0, y1, zc, slots=(), diffusers=(), speakers=(), detector=None, downlight_pts=(),
             dl_r=0.055, thick=0.02, mat=None, holes=(), coll='House'):
    """Ceiling slab with recessed linear slot lights (photo 12: black 600 x 45 mm slots, three lenses each), recessed
    linear diffusers, speaker discs, a detector and trimmed downlights.  slots: (cx, cy, along 'X'|'Y')."""
    SL, SW = 0.6, 0.045
    rects = list(holes)
    slot_r = []
    for (cx, cy, al) in slots:
        hw, hd = (SL / 2, SW / 2) if al == 'X' else (SW / 2, SL / 2)
        slot_r.append((cx - hw, cx + hw, cy - hd, cy + hd))
    diff_r = []
    for (cx, cy, rot) in diffusers:
        hw, hd = (0.3, 0.03) if rot == 0 else (0.03, 0.3)
        diff_r.append((cx - hw, cx + hw, cy - hd, cy + hd))
    mb = MB()
    zb = zc - thick
    _plate_holes(mb, x0, x1, y0, y1, zb, zc, rects + slot_r + diff_r, mi=0)
    for (hx0, hx1, hy0, hy1) in slot_r:
        mb.frame(hx0 - 0.006, hx1 + 0.006, hy0 - 0.006, hy1 + 0.006, zb, zb + 0.07, 0.006, mi=1, axis='Z')     # recess walls
        mb.box(hx0 - 0.006, hx1 + 0.006, hy0 - 0.006, hy1 + 0.006, zb + 0.065, zb + 0.07, 1)                    # recess top
        mb.frame(hx0 - 0.010, hx1 + 0.010, hy0 - 0.010, hy1 + 0.010, zb - 0.0015, zb, 0.004, mi=3, axis='Z')   # flush black rim
        along_x = (hx1 - hx0) > (hy1 - hy0)
        for k in range(3):                                                                                     # three lenses
            if along_x:
                px, py = hx0 + (hx1 - hx0) * (k + 0.5) / 3, (hy0 + hy1) / 2
            else:
                px, py = (hx0 + hx1) / 2, hy0 + (hy1 - hy0) * (k + 0.5) / 3
            mb.cylinder(px, py, zb + 0.03, zb + 0.062, 0.016, seg=12, mi=3)
            mb.cylinder(px, py, zb + 0.028, zb + 0.03, 0.013, seg=12, mi=4)
    for (hx0, hx1, hy0, hy1) in diff_r:
        mb.box(hx0 - 0.01, hx1 + 0.01, hy0 - 0.01, hy1 + 0.01, zb + 0.04, zc + 0.01, 1)
        along_x = (hx1 - hx0) > (hy1 - hy0)
        for k in range(3):
            if along_x:
                yy = hy0 + (hy1 - hy0) * (k + 1) / 4
                mb.box(hx0, hx1, yy - 0.003, yy + 0.003, zb + 0.015, zb + 0.022, 0)
            else:
                xx = hx0 + (hx1 - hx0) * (k + 1) / 4
                mb.box(xx - 0.003, xx + 0.003, hy0, hy1, zb + 0.015, zb + 0.022, 0)
    for (sx, sy) in speakers:
        mb.lathe(sx, sy, zb, [(0, -0.012), (0.05, -0.010), (0.070, -0.004), (0.076, 0.0), (0, 0.0)], seg=24, mi=0)
        mb.lathe(sx, sy, zb - 0.012, [(0, -0.001), (0.012, -0.001), (0.012, 0), (0, 0)], seg=12, mi=1)
    if detector is not None:
        dx, dy = detector
        mb.lathe(dx, dy, zb, [(0, -0.022), (0.04, -0.022), (0.052, -0.012), (0.054, 0), (0, 0)], seg=20, mi=0)
        mb.lathe(dx, dy, zb - 0.022, [(0, -0.002), (0.008, -0.002), (0.008, 0), (0, 0)], seg=8, mi=4)
    if downlight_pts:
        downlights(mb, downlight_pts, zb, r=dl_r, mi=2, mi_trim=3)
    return mb.build(name, [mat or M['ceiling'], M['black'], M['emit_down'], M['black_metal'], M['emit_white']], coll=coll, smooth=False)


def _spots(prefix, pts, z, energy=28.0, spot=62.0, blend=0.55, color=K30, size=0.04, aim=None):
    """One SPOT per recessed fixture, straight down (or toward `aim`)."""
    for i, (x, y) in enumerate(pts):
        add_light(f"{prefix}_{i}", 'SPOT', (x, y, z), energy, color, size=size, spot=math.radians(spot), blend=blend,
                  target=aim(x, y) if aim else None)


def _rr(uc, vc, w, h, r, n=3):
    """Closed rounded-rectangle loop of (u, v) points, CCW, centred on (uc, vc)."""
    r = min(r, w / 2 - 1e-4, h / 2 - 1e-4)
    pts = []
    for (cx, cy, a0) in ((uc + w / 2 - r, vc - h / 2 + r, -math.pi / 2), (uc + w / 2 - r, vc + h / 2 - r, 0.0),
                         (uc - w / 2 + r, vc + h / 2 - r, math.pi / 2), (uc - w / 2 + r, vc - h / 2 + r, math.pi)):
        for k in range(n + 1):
            a = a0 + math.pi / 2 * k / n
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def _arc_loft(mb, cx, cy, r, a0, a1, prof, z, mi, seg=24, ends=0.5, vscale=None):
    """Loft a closed (u, v) profile along the arc of radius r from a0 to a1 (u = radial offset from r, v = height
    above z).  The profile shrinks toward both ends so they read as rounded upholstery, not cut tubes.
    vscale(t) optionally scales the profile height (measured from its lowest point) along the arc."""
    uc = sum(p[0] for p in prof) / len(prof)
    vc = sum(p[1] for p in prof) / len(prof)
    vmin = min(p[1] for p in prof)
    ts = sorted({0.0, 0.02, 0.05} | {k / seg for k in range(1, seg) if 0.05 < k / seg < 0.95} | {0.95, 0.98, 1.0})

    def sc(t):
        e = min(t, 1 - t)
        if e >= 0.05:
            return 1.0
        if e >= 0.02:
            return 0.85 + 0.15 * (e - 0.02) / 0.03
        return ends + (0.85 - ends) * e / 0.02
    secs = []
    for t in ts:
        a = a0 + (a1 - a0) * t
        s = sc(t)
        hs = vscale(t) if vscale else 1.0
        sec = []
        for (u, v) in prof:
            uu = uc + (u - uc) * s
            vv = vc + (v - vc) * s
            vv = vmin + (vv - vmin) * hs
            rr = r + uu
            sec.append((cx + rr * math.cos(a), cy + rr * math.sin(a), z + vv))
        secs.append(sec)
    mb.sweep(secs, mi)


def _stadium(cx, cy, L, W, rot=0.0, n=10):
    """Stadium (rounded-end rectangle) outline in plan, length L along local X, width W, CCW."""
    r = W / 2
    pts = []
    for k in range(n + 1):
        a = -math.pi / 2 + math.pi * k / n
        pts.append((L / 2 - r + r * math.cos(a), r * math.sin(a)))
    for k in range(n + 1):
        a = math.pi / 2 + math.pi * k / n
        pts.append((-L / 2 + r + r * math.cos(a), r * math.sin(a)))
    c, s = math.cos(rot), math.sin(rot)
    return [(cx + px * c - py * s, cy + px * s + py * c) for (px, py) in pts]


def _round_tube(mb, pts, r, seg=10, mi=0):
    """Smooth tube along a polyline (path_tube) - a thin wrapper so the intent reads in the callers."""
    mb.path_tube(pts, r, seg=seg, mi=mi)


# ---------------------------------------------------------------- furniture
def curved_sofa2(mb, cx, cy, r, a0, a1, z, depth=0.95, seat_h=0.42, back_h=0.76, mi=0, mi_plinth=1, seg=26, bolsters=4, mi_bolster=None):
    """Kidney sofa (photo 10): a plump seat and a rolled back lofted along an arc with rounded ends, a recessed
    dark plinth and a row of round bolster cushions along the back."""
    mi_bolster = mi if mi_bolster is None else mi_bolster
    seat = _rr(-depth / 2 + 0.02, (0.12 + seat_h) / 2, depth - 0.04, seat_h - 0.12, 0.10, n=3)
    _arc_loft(mb, cx, cy, r, a0, a1, seat, z, mi, seg, ends=0.55)
    back = _rr(-0.17, (seat_h - 0.05 + back_h) / 2, 0.32, back_h - seat_h + 0.05, 0.11, n=3)
    _arc_loft(mb, cx, cy, r + 0.015, a0 + 0.015, a1 - 0.015, back, z, mi, seg, ends=0.45)
    mb.arc_prism(cx, cy, r - depth + 0.10, r - 0.10, a0 + 0.05, a1 - 0.05, z + 0.015, z + 0.13, seg, mi_plinth)
    rb = r - 0.40
    for i in range(bolsters):
        a = a0 + (a1 - a0) * (i + 0.5) / bolsters
        half = 0.20 / rb
        p0 = (cx + rb * math.cos(a - half), cy + rb * math.sin(a - half), z + seat_h + 0.14)
        p1 = (cx + rb * math.cos(a + half), cy + rb * math.sin(a + half), z + seat_h + 0.14)
        mb.tube(p0, p1, 0.15, 0.15, seg=16, mi=mi_bolster)


def tub_chair(mb, x, y, rot=0.0, z=0.0, mi=0, mi_leg=1, w=0.58, d=0.58):
    """Fully upholstered boucle dining chair (photo 11): a plump round-cornered seat inside a curved wrap-around
    back that is tallest behind the sitter and drops to arm height at the sides; four turned oak legs.
    Faces its own -Y."""
    seat_h = 0.46
    mb.rcbox(x, y, z + seat_h - 0.07, w, d, 0.14, r=0.06, mi=mi, rot=rot, seg=3, puff=0.35)
    # back ring: semicircle around the rear half, profile 90 mm thick; height 0.40 at the rear, 0.22 at the arms
    prof = _rr(0.0, 0.0, 0.09, 0.40, 0.04, n=2)
    prof = [(u, v + 0.20) for (u, v) in prof]                     # v measured from the seat top
    _arc_loft(mb, x, y, w / 2 - 0.02, rot + 0.0, rot + math.pi, prof, z + seat_h - 0.02, mi, seg=18, ends=0.6,
              vscale=lambda t: 0.55 + 0.45 * math.sin(math.pi * t))
    for sx in (-1, 1):
        for sy in (-1, 1):
            px, py = rot2(x + sx * (w / 2 - 0.08), y + sy * (d / 2 - 0.08), x, y, rot)
            qx, qy = rot2(x + sx * (w / 2 - 0.05), y + sy * (d / 2 - 0.05), x, y, rot)
            mb.tube((qx, qy, z), (px, py, z + seat_h - 0.1), 0.014, 0.019, seg=10, mi=mi_leg)


def walnut_stool(mb, x, y, z, h=0.66, r=0.19, mi_wood=0, mi_seat=1, rot=0.0):
    """Counter stool (photo 12): dark walnut - four splayed turned legs, a foot ring, a low curved back rail on two
    posts - with a round white leather cushion."""
    zt = z + h
    mb.lathe(x, y, zt - 0.03, [(0, 0), (r * 0.9, 0), (r, 0.006), (r, 0.03), (r * 0.96, 0.03)], seg=24, mi=mi_wood)       # seat frame disc
    mb.lathe(x, y, zt, [(0, 0), (r * 0.94, 0), (r * 0.98, 0.02), (r * 0.94, 0.045), (r * 0.6, 0.06), (0, 0.065)], seg=24, mi=mi_seat)  # cushion
    for sx in (-1, 1):
        for sy in (-1, 1):
            px, py = rot2(x + sx * (r - 0.06), y + sy * (r - 0.06), x, y, rot)
            qx, qy = rot2(x + sx * (r + 0.01), y + sy * (r + 0.01), x, y, rot)
            mb.tube((qx, qy, z), (px, py, zt - 0.03), 0.014, 0.018, seg=10, mi=mi_wood)
    ring = []
    for k in range(17):                                                                     # foot ring
        a = 2 * math.pi * k / 16
        f = (z + 0.24 - z) / (zt - 0.03 - z)
        rr = (r + 0.01) + ((r - 0.06) - (r + 0.01)) * f
        ring.append((x + rr * 0.98 * math.cos(a), y + rr * 0.98 * math.sin(a), z + 0.24))
    mb.path_tube(ring, 0.009, seg=8, mi=mi_wood)
    # low back: two posts at the rear + a curved rail
    for sx in (-1, 1):
        px, py = rot2(x + sx * 0.10, y + r - 0.03, x, y, rot)
        mb.tube((px, py, zt - 0.03), (px, py, zt + 0.22), 0.011, 0.010, seg=8, mi=mi_wood)
    rail = []
    for k in range(9):
        a = rot + math.pi * 0.25 + math.pi * 0.5 * k / 8
        rail.append((x + (r - 0.01) * math.cos(a), y + (r - 0.01) * math.sin(a), zt + 0.23))
    mb.path_tube(rail, 0.012, seg=10, mi=mi_wood)


def slab_table(mb, cx, cy, z, L, W, h=0.75, top_t=0.06, mi=0, rot=0.0):
    """Dining table (photo 11): thick walnut top on two solid slab legs and a low stretcher; length along local X."""
    mb.cbox(cx, cy, z + h - top_t / 2, L, W, top_t, mi, rot)
    for sx in (-1, 1):
        px, py = rot2(cx + sx * (L / 2 - 0.55), cy, cx, cy, rot)
        mb.cbox(px, py, z + (h - top_t) / 2, 0.09, W - 0.26, h - top_t, mi, rot)
    mb.cbox(cx, cy, z + 0.16, L - 1.3, 0.10, 0.09, mi, rot)


def _panels(mb, body, face, cols, rows, mi, mi_gap, gap=0.003):
    """Flat cabinet body + 3 mm reveal lines on one face (face '+X' | '-X' | '+Y' | '-Y'); rows = z values."""
    x0, x1, y0, y1, z0, z1 = body
    mb.box(x0, x1, y0, y1, z0, z1, mi)
    e = 0.0008
    if face in ('+X', '-X'):
        fx0, fx1 = (x1 - 0.002, x1 + e) if face == '+X' else (x0 - e, x0 + 0.002)
        L = y1 - y0
        for i in range(1, cols):
            yy = y0 + L * i / cols
            mb.box(fx0, fx1, yy - gap / 2, yy + gap / 2, z0, z1, mi_gap)
        for zz in rows:
            mb.box(fx0, fx1, y0, y1, zz - gap / 2, zz + gap / 2, mi_gap)
    else:
        fy0, fy1 = (y1 - 0.002, y1 + e) if face == '+Y' else (y0 - e, y0 + 0.002)
        L = x1 - x0
        for i in range(1, cols):
            xx = x0 + L * i / cols
            mb.box(xx - gap / 2, xx + gap / 2, fy0, fy1, z0, z1, mi_gap)
        for zz in rows:
            mb.box(x0, x1, fy0, fy1, zz - gap / 2, zz + gap / 2, mi_gap)


def stadium_sofa(mb, x, y, L, W, rot, z, mi, mi_plinth=None, seat_h=0.42, back_h=0.72, back_d=0.26, pillows=()):
    """Sofa with fully rounded ends in plan (photos 13/14): stadium-shaped seat + a stadium-ring back along the
    rear half; meant to be built with a bevel modifier for the soft edges.  Faces its own -Y."""
    mi_plinth = mi if mi_plinth is None else mi_plinth
    outer = _stadium(x, y, L, W, rot)
    mb.prism(outer, z + 0.02, z + 0.12, mi_plinth)
    mb.prism(_stadium(x, y, L + 0.02, W + 0.02, rot), z + 0.12, z + seat_h, mi)
    # back: a C-shaped ring between the outer stadium and an inset one, along the rear (+Y) half only
    n = 10
    r = W / 2
    ri = r - back_d

    def end_c(a):                                                 # the end-cap centre an arc point at angle a belongs to
        return L / 2 - r if a <= math.pi / 2 else -L / 2 + r
    pts = [(end_c(math.pi * k / n) + r * math.cos(math.pi * k / n), r * math.sin(math.pi * k / n)) for k in range(n + 1)]
    pts += [(end_c(math.pi * k / n) + ri * math.cos(math.pi * k / n), ri * math.sin(math.pi * k / n)) for k in range(n, -1, -1)]
    c, s = math.cos(rot), math.sin(rot)
    ring = [(x + px * c - py * s, y + px * s + py * c) for (px, py) in pts]
    mb.prism(ring, z + seat_h - 0.02, z + back_h, mi)
    for (px, py, mi_, rr, lean) in pillows:
        qx, qy = rot2(x + px, y + py, x, y, rot)
        sq_pillow(mb, qx, qy, z + seat_h, 0.5, 0.15, mi_, rot=rot + rr, lean=lean)


def _flames(mb, x0, x1, y0, y1, z, n=26, seed=3, mi=0):
    rng = random.Random(seed)
    for i in range(n):
        x = rng.uniform(x0, x1); y = rng.uniform(y0, y1)
        mb.cylinder(x, y, z, z + rng.uniform(0.12, 0.27), 0.03, 0.004, seg=5, mi=mi)


# ---------------------------------------------------------------- living room
def living(M):
    L_ = _local(M)
    x0, x1, y0, y1, z0, z1 = LIV
    box("Living_Floor", x0, x1, y0, y1, z0, z0 + 0.02, M['floor_stone'])
    dl_pts = [(x0 + (x1 - x0) * (i + 0.5) / 3, y0 + (y1 - y0) * (j + 0.5) / 4) for i in range(3) for j in range(4)]
    _ceiling("Living_Ceiling", M, x0, x1, y0, y1, z1, diffusers=[(8.3, y0 + 0.35, 0), (11.7, y1 - 0.35, 0)],
             speakers=[(8.1, 10.4), (12.0, 4.5)], detector=(10.0, 10.8), downlight_pts=dl_pts)
    box("Living_WestFinish", x0, x0 + 0.02, y0, y1, z0, z1, M['white_int'])
    # the exterior's travertine pier fills y1..FAM_Y0 between living and family; on the living side its west part
    # is finished in white plaster (photo 10) - a 20 mm layer on the room side, not a second wall in the same volume
    box("Living_NorthFinish", x0, x0 + 2.0, y1 - 0.02, y1, z0, z1, M['white_int'])
    tr_ = MB()
    wall_trims(tr_, [(x0 + 0.02, x0 + 0.028, y0, y1), (x0, x0 + 2.0, y1 - 0.028, y1 - 0.02)], z0 + 0.02, z1 - 0.02)
    tr_.build("Living_Trims", M['black'])
    # onyx fireplace pier: a free-standing backlit monolith with 15 mm shadow gaps top + bottom and a long linear
    # fire set low in its west face (photo 10: the fire runs almost the full length of the pier); see-through to the east
    ox0, ox1, oy0, oy1 = ONYX
    fz0, fz1 = z0 + 0.42, z0 + 0.74
    fy0, fy1 = oy0 + 0.35, oy1 - 0.35
    p = MB()
    p.wall('Y', oy0, oy1, ox0, ox1, z0 + 0.015, z1 - 0.015, holes=[(fy0, fy1, fz0, fz1)], mi=0)
    p.box(ox0 + 0.012, ox1 - 0.012, oy0 + 0.012, oy1 - 0.012, z0, z0 + 0.015, 1)             # recessed plinth (shadow gap)
    p.box(ox0 + 0.012, ox1 - 0.012, oy0 + 0.012, oy1 - 0.012, z1 - 0.015, z1, 1)             # ceiling shadow gap
    p.box(ox0 + 0.04, ox1 - 0.04, fy0, fy1, fz0, fz0 + 0.012, 1)                             # firebox floor
    p.box(ox0 + 0.04, ox1 - 0.04, fy0, fy1, fz1 - 0.012, fz1, 1)                             # firebox ceiling
    p.box(ox0 + 0.04, ox1 - 0.04, fy0, fy1, fz0 + 0.012, fz0 + 0.03, 2)                      # glowing ember bed
    p.build("Living_OnyxPier", [M['onyx'], M['black'], L_['ember']])
    fp = MB()
    fireplace_insert(fp, fy0, fy1, ox0, fz0, fz1, along='Y', faces=(-1,), mi_frame=0, mi_glass=1, mi_pebble=2, mi_flame=3,
                     depth=0.5, seed=1, n_flames=110, bed=True, bed_centre=(ox0 + ox1) / 2)
    fireplace_insert(fp, fy0, fy1, ox1, fz0, fz1, along='Y', faces=(1,), mi_frame=0, mi_glass=1, mi_pebble=2, mi_flame=3, bed=False)
    fp.build("Living_Fireplace", [M['black_metal'], M['glass'], M['pebble'], L_['fire_bright']], smooth=True)
    # two kidney sofas facing each other over a round black table, bolsters + a folded throw, a big wool rug
    cxs, cys = 9.15, 6.5
    sf = MB()
    curved_sofa2(sf, cxs, cys, 1.85, math.radians(108), math.radians(252), z0 + 0.02, depth=0.98, mi=0, mi_plinth=1, seg=26, bolsters=4)
    curved_sofa2(sf, cxs, cys, 1.85, math.radians(-72), math.radians(72), z0 + 0.02, depth=0.98, mi=0, mi_plinth=1, seg=26, bolsters=4)
    sf.build("Living_Sofas", [M['fabric'], M['black']], smooth=True, subsurf=1)
    sp = MB()
    sp.drape(cxs - 1.72, cxs - 1.08, cys - 0.55, cys + 0.05, z0 + 0.02 + 0.44, t=0.025, mi=0, sag=0.05, rot=0.35, folds=2, seed=7)
    sp.build("Living_SofaThrow", M['throw'], smooth=True, subsurf=1)
    ct = MB()
    round_table(ct, cxs, cys, z0 + 0.02, 0.62, h=0.36, top_t=0.05, mi=0, legs='drum')
    ct.build("Living_CoffeeTable", M['black_gloss'], smooth=True, bevel=0.012)
    rug("Rug_Living", cxs - 2.5, cxs + 2.5, cys - 2.7, cys + 2.7, z0 + 0.02, M['rug'])
    dc = MB()
    vase(dc, cxs + 0.2, cys + 0.15, z0 + 0.38, h=0.36, r=0.14, mi=0, style='round')
    branches(dc, cxs + 0.2, cys + 0.15, z0 + 0.72, h=0.7, n=7, seed=4, mi=1, leaves=8, mi_leaf=2, spread=0.55)
    books(dc, cxs - 0.28, cys - 0.22, z0 + 0.38, n=3, mi=3, rot=0.25)
    vase(dc, cxs - 0.1, cys + 0.35, z0 + 0.38, h=0.07, r=0.1, mi=3, style='bowl')
    dc.lathe(cxs + 0.35, cys - 0.3, z0 + 0.38, [(0, 0), (0.03, 0), (0.035, 0.05), (0.06, 0.12), (0.045, 0.2), (0.07, 0.26), (0.02, 0.3), (0, 0.3)], seg=16, mi=4)   # small sculpture
    dc.build("Living_Decor", [M['ceramic'], M['bark'], M['leaf_plant'], M['book'], M['bronze']], smooth=True)
    # a fiddle-leaf fig in the SW corner, a console with a lamp against the west wall
    pl = MB()
    fig_plant(pl, x0 + 0.6, y0 + 0.6, z0 + 0.02, pot_r=0.3, pot_h=0.45, h=1.7, mi_pot=0, mi_leaf=1, mi_stem=2, mi_soil=3, seed=8, n_leaves=15)
    pl.build("Living_Plant", [M['clay'], M['leaf_plant'], M['bark'], M['soil']], smooth=True)
    cs = MB()
    table(cs, x0 + 0.45, y1 - 1.6, z0 + 0.02, 0.4, 1.6, h=0.78, top_t=0.04, mi_top=0, mi_leg=0, legs='four', leg_w=0.03)
    lamp(cs, x0 + 0.45, y1 - 1.2, z0 + 0.8, mi_base=1, mi_shade=2, base_r=0.12, base_h=0.28, shade_r=0.18, shade_h=0.22)
    books(cs, x0 + 0.45, y1 - 2.1, z0 + 0.8, n=2, mi=3, w=0.26, d=0.2)
    tray(cs, x0 + 0.45, y1 - 1.75, z0 + 0.8, w=0.28, d=0.18, mi=4)
    cs.build("Living_Console", [M['walnut'], M['ceramic_black'], M['lampshade'], M['book'], M['brass']], smooth=True)
    # lighting: pools from the 12 downlights, a weak fill, the ember glow; the onyx itself is emissive
    room_light("L_Living", 'living', energy=36, color=K30)
    _spots("L_LivingDL", dl_pts, z1 - 0.05, energy=26, spot=64, blend=0.55)
    for yy in (oy0 + 1.0, (oy0 + oy1) / 2, oy1 - 1.0):                                       # the 2.9 m fire lights the floor + sofas
        add_light(f"L_LivingFire_{yy:.1f}", 'POINT', (ox0 - 0.12, yy, z0 + 0.58), 30, (1.0, 0.55, 0.22), size=0.3)
    add_light("L_LivingLamp", 'POINT', (x0 + 0.45, y1 - 1.2, z0 + 1.15), 8, (1.0, 0.78, 0.55), size=0.12)


# ---------------------------------------------------------------- dining + the open sitting area toward the kitchen
def dining(M):
    L_ = _local(M)
    x0, x1, y0, y1, z0, z1 = DIN
    box("Dining_Floor", x0, x1, y0, y1, z0, z0 + 0.02, M['floor_stone'])
    # ceiling: wide oak planks over the table (photo 11), a plain white field with recessed slots over the sitting area
    bx0, bx1 = -1.7, 3.3
    slots = [(x, y, 'Y') for x in (-3.5, -2.3) for y in (11.0, 12.6, 14.2)]
    _ceiling("Dining_Ceiling", M, x0, x1, y0, y1, z1, slots=slots, diffusers=[(-3.4, y1 - 0.35, 0), (5.8, y0 + 0.35, 0)],
             speakers=[(-3.0, 9.4), (6.4, 16.2)], detector=(0.2, 9.0), holes=[(bx0, bx1, y0, y1)])
    c = MB()
    c.box(bx0, bx1, y0, y1, z1 - 0.06, z1, 0)                                          # oak plank band (planks run N-S)
    c.box(bx0 - 0.012, bx0, y0, y1, z1 - 0.06, z1, 1); c.box(bx1, bx1 + 0.012, y0, y1, z1 - 0.06, z1, 1)   # dark reveals at its edges
    xx = bx0 + 0.24
    while xx < bx1 - 0.05:                                                             # 2 mm plank joints as real grooves
        c.box(xx - 0.001, xx + 0.001, y0, y1, z1 - 0.062, z1 - 0.055, 1)
        xx += 0.24
    c.build("Dining_OakBand", [L_['oak_ceiling'], M['black']])
    band_dl = [(-1.0 + 3.6 * (i + 0.5) / 2, y0 + 0.8 + (y1 - y0 - 1.6) * (j + 0.5) / 5) for i in range(2) for j in range(5)]
    dl = MB(); downlights(dl, band_dl, z1 - 0.06)
    dl.build("Dining_Downlights", [M['emit_down'], M['black_metal']])
    # north partition (to the office/corridor) inside our volume, with a door; east finish
    w = MB()
    w.wall('X', x0, x1, y1 - 0.2, y1, z0, z1, holes=[(4.6, 5.6, z0, z0 + 2.4), (-1.0, 0.8, z0, z0 + 2.4)], mi=0)   # office door + the suite's double doors
    w.build("Dining_NorthWall", M['white_int'])
    d = MB()
    door_set(d, 4.6, 5.6, y1 - 0.1, z0, z0 + 2.4, along='X', mi_leaf=0, mi_black=1, mi_plate=2, pull_side=-1, plate_side=1, face=-1)
    d.build("Dining_Door", [M['oak_pale'], M['black'], M['white_gloss']])
    tr_ = MB()
    wall_trims(tr_, [(x0, -1.02, y1 - 0.208, y1 - 0.2), (0.82, 4.58, y1 - 0.208, y1 - 0.2), (5.62, x1, y1 - 0.208, y1 - 0.2)], z0 + 0.02, z1 - 0.02)
    tr_.build("Dining_Trims", M['black'])
    # walnut slab table 3.4 x 1.1 running N-S along the east glass, 8 boucle tub chairs
    tx, ty = 4.6, 13.2
    t = MB()
    slab_table(t, tx, ty, z0 + 0.02, 3.4, 1.1, h=0.75, top_t=0.06, mi=0, rot=math.pi / 2)
    t.build("Dining_Table", L_['walnut_table'], bevel=0.012, bevel_seg=4)
    ch = MB()
    for i in range(3):
        y = ty - 1.1 + i * 1.1
        tub_chair(ch, tx - 0.95, y, rot=math.pi / 2, z=z0 + 0.02, mi=0, mi_leg=1)     # west side, faces east (+X)
        tub_chair(ch, tx + 0.95, y, rot=-math.pi / 2, z=z0 + 0.02, mi=0, mi_leg=1)    # east side, faces west
    tub_chair(ch, tx, ty - 2.15, rot=math.pi, z=z0 + 0.02, mi=0, mi_leg=1)           # south end, faces north
    tub_chair(ch, tx, ty + 2.15, rot=0.0, z=z0 + 0.02, mi=0, mi_leg=1)               # north end, faces south
    ch.build("Dining_Chairs", [M['fabric_white'], M['oak']], smooth=True, subsurf=1)
    dc = MB()
    dc.rcbox(tx, ty, z0 + 0.782, 0.36, 2.6, 0.004, r=0.002, mi=4, rot=0.0)                                                  # linen runner
    vase(dc, tx, ty + 0.3, z0 + 0.786, h=0.3, r=0.13, mi=0, style='bowl')
    vase(dc, tx, ty - 0.6, z0 + 0.786, h=0.26, r=0.09, mi=1, style='tall')
    vase(dc, tx + 0.12, ty + 0.75, z0 + 0.786, h=0.18, r=0.08, mi=3, style='round')
    branches(dc, tx, ty - 0.6, z0 + 1.04, h=0.55, n=6, seed=5, mi=5, leaves=5, mi_leaf=6, spread=0.45)
    for (cx_, cy_, h_) in ((tx - 0.15, ty - 1.15, 0.28), (tx + 0.1, ty - 1.3, 0.22)):                                        # candlesticks
        dc.lathe(cx_, cy_, z0 + 0.786, [(0, 0), (0.045, 0), (0.02, 0.02), (0.012, h_ - 0.03), (0.02, h_), (0, h_)], seg=14, mi=7)
        candle(dc, cx_, cy_, z0 + 0.786 + h_, r=0.012, h=0.12, mi_wax=2, mi_flame=8)
    books(dc, tx + 0.1, ty - 1.3 - 0.4, z0 + 0.786, n=2, mi=2)
    dc.build("Dining_Decor", [M['ceramic_black'], M['ceramic'], M['book'], M['ceramic_cream'], M['linen_white'], M['bark'], M['leaf_plant'], M['brass'], M['fire']], smooth=True)
    # low white credenza + art (floater frame + picture light) on the north wall
    cr = MB()
    cr.rcbox(2.2, y1 - 0.5, z0 + 0.37, 2.2, 0.5, 0.7, r=0.012, mi=0)
    for k in range(1, 3):                                                                                                    # door reveals
        cr.box(1.1 + k * 0.733 - 0.002, 1.1 + k * 0.733 + 0.002, y1 - 0.76, y1 - 0.75, z0 + 0.06, z0 + 0.7, 1)
    cr.box(1.15, 3.25, y1 - 0.72, y1 - 0.28, z0 + 0.02, z0 + 0.03, 1)                                                          # plinth shadow gap
    ceramics_row(cr, [(1.5, y1 - 0.5), (2.35, y1 - 0.45)], z0 + 0.72, mis=(2, 3), seed=3)
    books(cr, 2.9, y1 - 0.5, z0 + 0.72, n=3, mi=4, rot=-0.2)
    cr.build("Dining_Credenza", [M['white_gloss'], M['black'], M['ceramic_black'], M['ceramic_cream'], M['book']], smooth=True)
    a = MB(); floater_art(a, 1.3, 3.1, y1 - 0.2, z0 + 1.3, z0 + 2.6, along='X', face=-1, mi_frame=0, mi_canvas=1, mi_light=2, mi_lens=3)
    a.build("Dining_Art", [M['oak'], M['art_lines'], M['brass'], M['emit_bar']])
    # grey boucle curved sectional facing the kitchen (photo 13): a long rounded-end sofa + a rounded return,
    # dark taupe pillows, a round bolster, Calacatta Viola drum tables
    sf = MB()
    stadium_sofa(sf, -2.15, 13.4, 3.6, 1.05, -math.pi / 2, z0 + 0.02, 0, mi_plinth=1, back_h=0.70,
                 pillows=[(-1.1, 0.16, 2, 0.15, 0.3), (-0.45, 0.17, 3, -0.1, 0.3), (0.35, 0.16, 2, 0.05, 0.3), (1.05, 0.17, 3, 0.1, 0.3)])
    stadium_sofa(sf, -0.75, 11.45, 1.7, 1.05, math.pi, z0 + 0.02, 0, mi_plinth=1, back_h=0.70,
                 pillows=[(-0.35, 0.17, 3, 0.08, 0.3), (0.35, 0.17, 2, -0.1, 0.3)])
    sf.build("Dining_Sectional", [M['fabric_grey'], M['black'], M['fabric_dark'], M['fabric_taupe']], smooth=True, bevel=0.05, bevel_seg=4)
    bl = MB()
    bl.sphere((-2.05, 12.05, z0 + 0.64), 0.2, seg=18, rings=12, mi=0)                                                        # round bolster
    bl.drape(-2.45, -1.85, 14.35, 14.95, z0 + 0.45, t=0.025, mi=1, sag=0.05, rot=0.2, folds=2, seed=3)
    bl.build("Dining_SectionalSoft", [M['fabric_white'], M['throw_brown']], smooth=True, subsurf=1)
    ct = MB()
    ct.cylinder(-3.45, 13.4, z0 + 0.02, z0 + 0.34, 0.55, seg=36, ry=0.45)
    ct.cylinder(-3.05, 12.7, z0 + 0.02, z0 + 0.42, 0.42, seg=36, ry=0.42)
    ct.build("Dining_CoffeeTables", M['marble_dark'], smooth=True, bevel=0.008)
    ctd = MB()
    tray(ctd, -3.5, 13.5, z0 + 0.34, w=0.3, d=0.2, mi=0, rot=0.3)
    books(ctd, -3.1, 12.7, z0 + 0.42, n=3, mi=1, rot=0.5, w=0.3, d=0.22)
    vase(ctd, -3.55, 13.2, z0 + 0.34, h=0.14, r=0.07, mi=2, style='round')
    ctd.build("Dining_TableDecor", [M['black'], M['book'], M['ceramic']], smooth=True)
    rug("Rug_Dining", -4.2, 0.1, 10.6, 15.6, z0 + 0.02, M['rug_blue'])
    # lighting: downlights in the oak band over the table, slot spots over the sectional, a weak fill
    room_light("L_Dining", 'dining', energy=45, color=K30)
    _spots("L_DiningDL", band_dl, z1 - 0.10, energy=24, spot=60, blend=0.55)
    _spots("L_DiningSlot", [(x, y) for (x, y, _) in slots], z1 - 0.05, energy=30, spot=55, blend=0.5)
    add_light("L_DiningTable", 'SPOT', (tx, ty, z1 - 0.1), 60, K30, size=0.1, spot=math.radians(70), blend=0.7)


def kitchen(M):
    L_ = _local(M)
    x0, x1, y0, y1, z0, z1 = KIT
    box("Kitchen_Floor", x0, x1, y0, y1, z0, z0 + 0.02, M['oak_floor'])
    # ceiling: 3 x 4 grid of recessed black slot lights running N-S (photo 12), diffusers, speakers
    slots = [(x, y, 'Y') for x in (-10.6, -8.6, -6.6) for y in (9.6, 11.6, 13.6, 15.6)]
    _ceiling("Kitchen_Ceiling", M, x0, x1, y0, y1, z1, slots=slots, diffusers=[(-11.2, y0 + 0.3, 0), (-5.6, y0 + 0.3, 0)],
             speakers=[(-7.6, 9.0), (-9.6, 16.4)], detector=(-5.4, 12.0))
    box("Kitchen_SouthFinish", x0, x1, y0, y0 + 0.02, z0, z1, M['white_int'])
    tr_ = MB()
    wall_trims(tr_, [(x0, x1, y0 + 0.02, y0 + 0.028)], z0 + 0.02, z1 - 0.02)
    tr_.build("Kitchen_Trims", M['black'])
    TK = 0.10                                                                              # toe-kick height (recessed 60 mm, dark)
    CT = z1 - 0.36                                                                         # top of the tall cabinets; lit cove above
    # ---- west wall: full-height horizontal-grain oak run in wide panels (photo 12 left), integrated ovens, lit niche
    cb = MB()
    _panels(cb, (x0 + 0.02, x0 + 0.62, y0 + 0.3, y1 - 0.62, z0 + TK, CT), '+X', cols=9, rows=[z0 + 0.92, z0 + 1.62, z0 + 2.32], mi=0, mi_gap=1)
    cb.box(x0 + 0.02, x0 + 0.56, y0 + 0.3, y1 - 0.62, z0 + 0.02, z0 + TK, 1)               # toe kick
    cb.build("Kitchen_WestRun", [L_['oak_hy'], M['black']])
    # niche in the west run (marble back, 8 mm LED bar) between y 10.6..13.6 at counter height
    nw = MB()
    nw.box(x0 + 0.62, x0 + 0.64, 10.6, 13.6, z0 + 0.95, z0 + 1.65, 0)
    nw.box(x0 + 0.62, x0 + 0.66, 10.6, 13.6, z0 + 1.65, z0 + 1.658, 1)
    ceramics_row(nw, [(x0 + 0.75, 11.1), (x0 + 0.75, 12.0), (x0 + 0.78, 12.9)], z0 + 0.95, mis=(2, 3, 2), seed=8)
    nw.build("Kitchen_WestNicheMarble", [L_['calacatta'], M['emit_bar'], M['ceramic'], M['ceramic_cream']], smooth=True)
    # ovens: two black/steel stacks at y 15.3..16.3 with handles + a control strip
    ov = MB()
    for (za, zb) in ((z0 + 0.92, z0 + 1.52), (z0 + 1.52, z0 + 2.12)):
        ov.box(x0 + 0.6, x0 + 0.63, 15.35, 16.25, za + 0.02, zb - 0.02, 0)
        ov.box(x0 + 0.6, x0 + 0.66, 15.35, 16.25, za + 0.02, za + 0.05, 1)
        ov.box(x0 + 0.63, x0 + 0.68, 15.42, 16.18, zb - 0.16, zb - 0.135, 1)                 # bar handle
        ov.box(x0 + 0.63, x0 + 0.66, 15.42, 15.44, zb - 0.16, zb - 0.135, 1); ov.box(x0 + 0.63, x0 + 0.66, 16.16, 16.18, zb - 0.16, zb - 0.135, 1)
        ov.box(x0 + 0.6, x0 + 0.632, 15.5, 16.1, zb - 0.09, zb - 0.06, 2)                    # display strip
    ov.build("Kitchen_Ovens", [M['black_gloss'], M['steel'], M['emit_white']])
    # ---- north (cooking) wall: base drawers + counter, tall horizontal-grain cabinets around the marble niche,
    #      the hood integrated in the cabinetry above the niche
    NX0, NX1 = x0 + 2.4, x1 - 1.4                                                          # niche extent in x
    nb = MB()
    _panels(nb, (x0 + 0.62, x1 - 0.02, y1 - 0.62, y1 - 0.02, z0 + TK, z0 + 0.92), '-Y', cols=8, rows=[z0 + 0.52], mi=0, mi_gap=1)   # base drawers
    nb.box(x0 + 0.62, x1 - 0.02, y1 - 0.56, y1 - 0.02, z0 + 0.02, z0 + TK, 1)                                    # toe kick
    nb.box(x0 + 0.62, x1 - 0.02, y1 - 0.66, y1 - 0.02, z0 + 0.92, z0 + 0.95, 2)                                      # 30 mm marble counter
    nb.wall('X', x0 + 0.62, x1 - 0.02, y1 - 0.62, y1 - 0.02, z0 + 0.95, CT, holes=[(NX0, NX1, z0 + 0.95, z0 + 2.15)], mi=0)   # tall cabinets around the niche
    for (xa, xb) in ((x0 + 0.62, NX0), (NX1, x1 - 0.02)):                                                       # panel reveals on the tall parts
        for i in range(1, 3):
            xx = xa + (xb - xa) * i / 3
            nb.box(xx - 0.0015, xx + 0.0015, y1 - 0.623, y1 - 0.62, z0 + 0.95, CT, 1)
        for zz in (z0 + 1.62, z0 + 2.32):
            nb.box(xa, xb, y1 - 0.623, y1 - 0.62, zz - 0.0015, zz + 0.0015, 1)
    nb.box(NX0, NX1, y1 - 0.623, y1 - 0.62, z0 + 2.32 - 0.0015, z0 + 2.32 + 0.0015, 1)
    nb.box(NX0, NX1, y1 - 0.12, y1 - 0.02, z0 + 0.95, z0 + 2.15, 2)                                              # marble backsplash in the niche
    nb.box(NX0, NX1, y1 - 0.62, y1 - 0.12, z0 + 2.15, z0 + 2.2, 0)                                               # niche head
    nb.box(NX0 + 0.02, NX1 - 0.02, y1 - 0.60, y1 - 0.14, z0 + 2.142, z0 + 2.15, 3)                               # LED panel at the niche top
    nb.box(NX0, NX1, y1 - 0.12, y1 - 0.10, z0 + 1.45, z0 + 1.47, 2)                                              # marble display shelf
    nb.build("Kitchen_NorthRun", [L_['oak_hx'], M['black'], L_['calacatta'], M['emit_cove']])
    # lit cove above the tall cabinets: the wall steps back 0.22 m, an LED strip on the cabinet tops washes it
    cv = MB()
    cv.box(x0 + 0.02, x1 - 0.02, y1 - 0.40, y1 - 0.02, CT, z1 - 0.02, 0)                                          # north cove wall (set back)
    cv.box(x0 + 0.02, x0 + 0.40, y0 + 0.3, y1 - 0.40, CT, z1 - 0.02, 0)                                           # west cove wall
    cv.box(x0 + 0.66, x1 - 0.06, y1 - 0.62, y1 - 0.40, CT, CT + 0.012, 1)                                         # LED strips on the cabinet tops
    cv.box(x0 + 0.40, x0 + 0.62, y0 + 0.3, y1 - 0.62, CT, CT + 0.012, 1)
    cv.build("Kitchen_Cove", [L_['cove_white'], M['emit_cove']])
    rg = MB()
    rx = (NX0 + NX1) / 2
    rg.box(rx - 0.6, rx + 0.6, y1 - 0.66, y1 - 0.12, z0 + 0.02, z0 + 0.93, 0)                                       # stainless range
    rg.box(rx - 0.58, rx + 0.58, y1 - 0.67, y1 - 0.66, z0 + 0.35, z0 + 0.86, 2)                                      # oven door glass
    rg.box(rx - 0.55, rx + 0.55, y1 - 0.70, y1 - 0.66, z0 + 0.86, z0 + 0.885, 0)                                     # door handle bar
    for i in range(6):
        rg.cylinder(rx - 0.42 + i * 0.17, y1 - 0.42, z0 + 0.93, z0 + 0.96, 0.05, seg=12, mi=1)                       # burners
        rg.cylinder(rx - 0.42 + i * 0.17, y1 - 0.42, z0 + 0.96, z0 + 0.975, 0.025, seg=12, mi=1)                     # burner caps
        rg.lathe(rx - 0.45 + i * 0.18, y1 - 0.665, z0 + 0.905, [(0, 0), (0.022, 0), (0.022, -0.028), (0.016, -0.03), (0, -0.03)], seg=14, mi=0)   # knobs (front face)
    rg.box(rx - 0.55, rx + 0.55, y1 - 0.62, y1 - 0.14, z0 + 0.97, z0 + 0.99, 2)                                      # dark cooktop plate
    rg.box(rx - 0.55, rx + 0.55, y1 - 0.62, y1 - 0.20, z0 + 2.05, z0 + 2.142, 0)                                     # hood body (stainless, integrated)
    rg.frame(rx - 0.57, rx + 0.57, y1 - 0.64, y1 - 0.18, z0 + 2.03, z0 + 2.05, 0.02, mi=1, axis='Z')                   # 20 mm perimeter reveal
    rg.box(rx - 0.50, rx + 0.50, y1 - 0.58, y1 - 0.24, z0 + 2.04, z0 + 2.05, 3)                                      # hood lamp panel
    faucet(rg, rx, y1 - 0.16, z0 + 1.6, h=0.05, mi=0, reach=0.25, dir=(0, -1))                                        # pot filler
    rg.build("Kitchen_Range", [M['steel'], M['black_metal'], M['black_gloss'], M['emit_white']])
    # ---- two Calacatta islands: 30 mm tops with mitred 30 mm waterfall ends (no thick-slab look)
    H = 0.92
    ST = 0.03

    def island_stone(mb, cx, cy, L, W, mi=0, sink=None, front_face=None):
        if sink is None:
            mb.box(cx - L / 2, cx + L / 2, cy - W / 2, cy + W / 2, z0 + H - ST, z0 + H, mi)
        else:
            mb.plate(cx - L / 2, cx + L / 2, cy - W / 2, cy + W / 2, z0 + H - ST, z0 + H, holes=[sink], mi=mi)
        mb.box(cx - L / 2, cx - L / 2 + ST, cy - W / 2, cy + W / 2, z0 + 0.02, z0 + H - ST, mi)      # waterfall ends
        mb.box(cx + L / 2 - ST, cx + L / 2, cy - W / 2, cy + W / 2, z0 + 0.02, z0 + H - ST, mi)
        if front_face == '-Y':                                                                          # marble seating face
            mb.box(cx - L / 2 + ST, cx + L / 2 - ST, cy - W / 2, cy - W / 2 + 0.02, z0 + 0.02, z0 + H - ST, mi)
    SINK = (-8.62, -7.78, 14.6 - 0.26, 14.6 + 0.2)
    isl = MB()
    island_stone(isl, -8.2, 11.7, 2.9, 1.1, front_face='-Y')
    island_stone(isl, -8.0, 14.6, 3.2, 1.1, sink=SINK)
    isl.build("Kitchen_Islands", L_['calacatta'], bevel=0.002)
    ib = MB()
    # front island: oak body behind the marble face, drawers toward the working aisle (+Y)
    _panels(ib, (-8.2 - 1.45 + ST, -8.2 + 1.45 - ST, 11.7 - 0.55 + 0.02, 11.7 + 0.55 - 0.03, z0 + TK, z0 + H - ST), '+Y', cols=4, rows=[z0 + 0.50], mi=0, mi_gap=1)
    ib.box(-8.2 - 1.4, -8.2 + 1.4, 11.7 - 0.5, 11.7 + 0.47, z0 + 0.02, z0 + TK, 1)                      # toe kick
    # back island: drawers facing the aisle (-Y), a wine fridge at the east end, oak back
    _panels(ib, (-8.0 - 1.6 + ST, -8.0 + 1.6 - ST, 14.6 - 0.55 + 0.03, 14.6 + 0.55 - 0.03, z0 + TK, z0 + H - ST), '-Y', cols=4, rows=[z0 + 0.50], mi=0, mi_gap=1)
    ib.box(-8.0 - 1.55, -8.0 + 1.55, 14.6 - 0.48, 14.6 + 0.48, z0 + 0.02, z0 + TK, 1)
    ib.box(-8.0 + 0.7, -8.0 + 1.5, 14.6 - 0.56, 14.6 - 0.50, z0 + TK + 0.02, z0 + 0.86, 3)                  # wine fridge: dark cabinet behind a tinted glass door
    for row in range(6):                                                                                  # bottle rows behind the glass
        zz = z0 + TK + 0.07 + row * 0.115
        for k in range(4):
            ib.cylinder(-8.0 + 0.78 + k * 0.17, 14.6 - 0.35, zz, zz + 0.075, 0.035, seg=8, mi=4)
            ib.cylinder(-8.0 + 0.78 + k * 0.17, 14.6 - 0.35, zz + 0.075, zz + 0.1, 0.015, seg=8, mi=4)
    ib.box(-8.0 + 0.7, -8.0 + 1.5, 14.6 - 0.525, 14.6 - 0.52, z0 + TK + 0.02, z0 + 0.86, 2)               # tinted glass door
    ib.frame(-8.0 + 0.7, -8.0 + 1.5, 14.6 - 0.535, 14.6 - 0.525, z0 + TK + 0.02, z0 + 0.86, 0.02, mi=1, axis='Y')
    ib.build("Kitchen_IslandBodies", [L_['oak_hx'], M['black'], M['glass_tint'], M['black_gloss'], M['ebony']])
    sk = MB()
    sk.frame(SINK[0] - 0.004, SINK[1] + 0.004, SINK[2] - 0.004, SINK[3] + 0.004, z0 + 0.72, z0 + H - ST - 0.002, 0.012, mi=0, axis='Z')   # undermount basin walls
    sk.box(SINK[0] - 0.004, SINK[1] + 0.004, SINK[2] - 0.004, SINK[3] + 0.004, z0 + 0.708, z0 + 0.72, 0)                        # basin floor
    sk.cylinder(-8.2, 14.6 - 0.03, z0 + 0.72, z0 + 0.724, 0.04, seg=16, mi=1)                                                   # drain
    # gooseneck faucet: a swept arc from the deck to over the basin
    arc = [(-8.2, 14.86, z0 + H + 0.34 * t) for t in (0, 0.5, 0.85)]
    arc += [(-8.2, 14.86 - 0.22 * math.sin(a), z0 + H + 0.34 + 0.09 * math.sin(a)) for a in (0.4, 0.9, 1.4, 1.9, 2.4)]
    arc += [(-8.2, 14.64, z0 + H + 0.30), (-8.2, 14.64, z0 + H + 0.22)]
    sk.path_tube(arc, 0.012, seg=10, mi=2)
    sk.cylinder(-8.2, 14.86, z0 + H, z0 + H + 0.015, 0.03, seg=14, mi=2)                                  # deck flange
    sk.tube((-8.35, 14.86, z0 + H), (-8.35, 14.86, z0 + H + 0.08), 0.008, 0.008, seg=8, mi=2); sk.tube((-8.35, 14.86, z0 + H + 0.08), (-8.42, 14.86, z0 + H + 0.11), 0.006, 0.006, seg=8, mi=2)   # lever
    sk.build("Kitchen_Sink", [M['steel'], M['black_metal'], M['chrome']], smooth=True)
    # stools (5 dark walnut with round white leather cushions) along the front island's seating face
    st = MB()
    for i in range(5):
        walnut_stool(st, -9.3 + i * 0.55, 10.86, z0 + 0.02, h=0.66, mi_wood=0, mi_seat=1, r=0.18, rot=math.pi)
    st.build("Kitchen_Stools", [L_['stool_walnut'], M['leather_white']], smooth=True)
    dc = MB()
    vase(dc, -7.4, 14.6, z0 + H, h=0.42, r=0.17, mi=0, style='round')
    branches(dc, -7.4, 14.6, z0 + H + 0.41, h=1.1, n=9, seed=6, mi=1, leaves=0, spread=0.45)
    vase(dc, -9.0, 11.8, z0 + H, h=0.08, r=0.15, mi=2, style='bowl')
    for k in range(7):                                                                                     # lemons in the bowl
        a = k * 0.9; rr = 0.06 if k < 6 else 0.0
        dc.blob((-9.0 + rr * math.cos(a), 11.8 + rr * math.sin(a), z0 + H + 0.07 + (0.05 if k == 6 else 0)), 0.038, seg=10, rings=6, jitter=0.08, seed=k, mi=5, squash=0.85, rx=1.15)
    dc.cbox(-8.3, 14.35, z0 + H + 0.02, 0.45, 0.3, 0.03, 3, rot=0.12)                                        # cutting board
    dc.cbox(-8.36, 14.3, z0 + H + 0.04, 0.22, 0.03, 0.004, 4, rot=0.12); dc.cbox(-8.16, 14.3, z0 + H + 0.04, 0.12, 0.03, 0.02, 6, rot=0.12)   # knife blade + handle
    for (kx, kh) in ((-9.35, 0.22), (-9.5, 0.16)):                                                          # glass canisters
        dc.lathe(kx, 14.9, z0 + H, [(0, 0), (0.05, 0), (0.055, kh - 0.02), (0.05, kh), (0, kh)], seg=16, mi=7)
        dc.lathe(kx, 14.9, z0 + H + kh, [(0, 0), (0.052, 0), (0.052, 0.015), (0, 0.015)], seg=16, mi=3)
    dc.build("Kitchen_Decor", [M['ceramic'], M['bark'], M['ceramic_cream'], M['walnut'], M['chrome'], L_['lemon'], M['black'], M['glass']], smooth=True)
    # lighting: 12 slot spots (aimed slightly toward the islands / cooking wall), the cove wash, niche + hood
    room_light("L_Kitchen", 'kitchen', energy=22, color=K30)
    _spots("L_KitchenSlot", [(x, y) for (x, y, _) in slots], z1 - 0.05, energy=30, spot=58, blend=0.5)
    area_light("L_KitchenNiche", ((NX0 + NX1) / 2, y1 - 0.4, z0 + 2.05), (NX1 - NX0 - 0.2, 0.2), 14, (1.0, 0.86, 0.68), target=((NX0 + NX1) / 2, y1, z0 + 1.2))
    area_light("L_KitchenCoveN", ((x0 + x1) / 2, y1 - 0.52, CT + 0.03), (x1 - x0 - 0.8, 0.12), 18, (1.0, 0.84, 0.62), down=False)
    area_light("L_KitchenCoveW", (x0 + 0.5, (y0 + y1) / 2, CT + 0.03), (0.12, y1 - y0 - 1.2), 11, (1.0, 0.84, 0.62), down=False)
    add_light("L_KitchenWestNiche", 'AREA', (x0 + 0.9, 12.1, z0 + 1.6), 6, (1.0, 0.86, 0.68), size=0.1)


# ---------------------------------------------------------------- family room (east pavilion, north half)
def family(M):
    L_ = _local(M)
    x0, x1, y0, y1, z0, z1 = FAM
    box("Family_Floor", x0, x1, y0, y1, z0, z0 + 0.02, M['oak_floor'])
    dl_pts = [(x0 + 0.9 + (x1 - x0 - 1.8) * (i + 0.5) / 2, y0 + 0.9 + (y1 - y0 - 1.8) * (j + 0.5) / 3) for i in range(2) for j in range(3)]
    _ceiling("Family_Ceiling", M, x0, x1, y0, y1, z1, speakers=[(x0 + 1.3, y0 + 1.3), (x1 - 1.3, y1 - 1.3)], detector=(x1 - 1.0, y0 + 1.0),
             downlight_pts=dl_pts)
    # cove ceiling (photo 14): perimeter bulkhead with an LED strip on its inner edge + slot diffusers in the bulkhead
    bk = MB()
    bk.frame(x0, x1, y0, y1, z1 - 0.32, z1 - 0.02, 0.7, mi=0, axis='Z')
    for (dx, dy, rot) in ((x0 + 0.35, y0 + 2.0, 1), (x1 - 0.35, y1 - 2.0, 1)):
        hw, hd = (0.03, 0.3) if rot else (0.3, 0.03)
        bk.box(dx - hw - 0.012, dx + hw + 0.012, dy - hd - 0.012, dy + hd + 0.012, z1 - 0.325, z1 - 0.319, 1)     # slot diffuser (dark) in the bulkhead face
        for k in range(3):
            yy = dy - hd + (2 * hd) * (k + 1) / 4
            bk.box(dx - hw, dx + hw, yy - 0.003, yy + 0.003, z1 - 0.326, z1 - 0.318, 0)
    bk.build("Family_Bulkhead", [M['white_int'], M['black']])
    cv = MB(); cove(cv, x0 + 0.68, x1 - 0.68, y0 + 0.68, y1 - 0.68, z1 - 0.31, w=0.03, mi=0)
    cv.build("Family_Cove", M['emit_cove'])
    # the exterior module fills y1-WT..y1 with its travertine wall (Pavilion_Structure), so the room's usable north
    # face is yn; the TV wall, built-ins and fire are layered in front of it
    yn = y1 - WT
    tr_ = MB()
    wall_trims(tr_, [(x0, x0 + 1.05, yn - 0.34, yn - 0.332), (x1 - 1.05, x1, yn - 0.34, yn - 0.332), (x0, x0 + 2.0, y0 + 0.2, y0 + 0.208)], z0 + 0.02, z1 - 0.32, do_gap=False)
    wall_trims(tr_, [(x0, x0 + 2.0, y0 + 0.2, y0 + 0.208)], z0 + 0.02, z1 - 0.32, do_skirt=False)
    tr_.build("Family_Trims", M['black'])
    # north wall: grey travertine TV wall with a steel-framed linear fire, oak built-ins with lit niches either side
    tw = MB()
    FX0, FX1, FZ0, FZ1 = x0 + 1.4, x1 - 1.4, z0 + 0.42, z0 + 0.7
    tw.wall('X', x0 + 1.05, x1 - 1.05, yn - 0.3, yn, z0 + 0.035, z1 - 0.32, holes=[(FX0, FX1, FZ0, FZ1)], mi=0)
    tw.box(x0 + 1.07, x1 - 1.07, yn - 0.28, yn, z0 + 0.02, z0 + 0.035, 1)                                # shadow-gap plinth
    tw.box(FX0, FX1, yn - 0.04, yn - 0.02, FZ0, FZ1, 1)                                                   # firebox: black back plate ...
    tw.box(FX0, FX1, yn - 0.3, yn - 0.02, FZ0, FZ0 + 0.012, 1); tw.box(FX0, FX1, yn - 0.3, yn - 0.02, FZ1 - 0.012, FZ1, 1)   # ... floor + ceiling
    tw.box(FX0, FX0 + 0.012, yn - 0.3, yn - 0.02, FZ0, FZ1, 1); tw.box(FX1 - 0.012, FX1, yn - 0.3, yn - 0.02, FZ0, FZ1, 1)   # ... cheeks
    tw.box(FX0 + 0.02, FX1 - 0.02, yn - 0.28, yn - 0.04, FZ0 + 0.012, FZ0 + 0.03, 2)                      # ember bed
    tw.build("Family_TVWall", [M['trav_grey'], M['black'], L_['ember']])
    fp = MB()
    fireplace_insert(fp, x0 + 1.4, x1 - 1.4, yn - 0.3, z0 + 0.42, z0 + 0.7, along='X', faces=(-1,), mi_frame=0, mi_glass=1, mi_pebble=2, mi_flame=3,
                     depth=0.22, seed=9, n_flames=60, bed_centre=yn - 0.16)
    fp.build("Family_Fireplace", [M['black_metal'], M['glass'], M['pebble'], L_['fire_bright']], smooth=True)
    t = MB()
    tv(t, x0 + 1.55, x1 - 1.55, yn - 0.3, z0 + 1.1, z0 + 2.3, 0, along='X')
    t.box(x0 + 1.555, x1 - 1.555, yn - 0.3425, yn - 0.339, z0 + 1.105, z0 + 2.295, 1)                    # screen panel inside a 5 mm bezel
    t.box(x0 + 1.9, x1 - 1.9, yn - 0.36, yn - 0.3, z0 + 0.98, z0 + 1.04, 2)                              # soundbar
    t.build("Family_TV", [M['black_gloss'], M['tv'], M['black']])
    bi = MB()
    rng = random.Random(14)
    for (xa, xb) in ((x0 + 0.05, x0 + 1.05), (x1 - 1.05, x1 - 0.05)):
        shelves(bi, xa, xb, yn - 0.34, yn, z0 + 0.02, z1 - 0.32, n=6, t=0.03, mi=0, back=True)
        for k in range(6):
            z = z0 + 0.02 + (z1 - 0.34 - z0) * k / 6
            bi.box(xa + 0.04, xb - 0.04, yn - 0.33, yn - 0.32, z + 0.06, z + 0.07, 1)
            kind = k % 3
            if kind == 0:
                ceramics_row(bi, [(xa + 0.3, yn - 0.18), (xa + 0.7, yn - 0.2)], z + 0.03, mis=(2, 4, 5), seed=k + (0 if xa < x0 + 0.5 else 7))
            elif kind == 1:
                vase(bi, (xa + xb) / 2 - 0.2, yn - 0.18, z + 0.03, h=0.12, r=0.12, mi=4, style='bowl')
                books(bi, (xa + xb) / 2 + 0.22, yn - 0.2, z + 0.03, n=3, mi=3, rot=rng.uniform(-0.2, 0.2))
            else:
                basket(bi, (xa + xb) / 2, yn - 0.18, z + 0.03, r=0.16, h=0.22, mi=6)
    bi.build("Family_Builtins", [M['oak'], M['emit_bar'], M['ceramic_cream'], M['book'], M['ceramic'], M['ceramic_black'], M['cane']], smooth=True)
    # seating: cream boucle sofa with rounded ends facing the TV, taupe pillows + a draped throw, side tables, plants, rug
    sf = MB()
    stadium_sofa(sf, 10.0, 14.0, 2.9, 1.05, math.pi, z0 + 0.02, 0, mi_plinth=3, back_h=0.72,
                 pillows=[(-0.65, 0.16, 1, 0.12, 0.3), (0.0, 0.17, 2, -0.08, 0.3), (0.65, 0.16, 1, 0.06, 0.3), (0.45, -0.02, 2, 0.35, 0.45)])
    sf.build("Family_Sofa", [M['fabric'], M['fabric_taupe'], M['fabric_brown'], M['black']], smooth=True, bevel=0.05, bevel_seg=4)
    th = MB()
    th.drape(8.75, 9.35, 13.5, 14.45, z0 + 0.44, t=0.025, mi=0, sag=0.06, rot=-0.15, folds=2, seed=5)                 # throw over the arm
    th.build("Family_Throw", M['throw'], smooth=True, subsurf=1)
    rug("Rug_Family", 8.3, 11.9, 12.3, yn - 0.55, z0 + 0.02, M['rug_pale'])
    st = MB()
    round_table(st, 8.5, 15.4, z0 + 0.02, 0.3, h=0.5, top_t=0.03, mi=0, legs='drum')
    round_table(st, 11.5, 15.4, z0 + 0.02, 0.3, h=0.5, top_t=0.03, mi=0, legs='drum')
    lamp(st, 11.5, 15.4, z0 + 0.52, mi_base=1, mi_shade=2, base_r=0.1, base_h=0.24, shade_r=0.16, shade_h=0.2)
    books(st, 8.5, 15.4, z0 + 0.52, n=2, mi=4, w=0.22, d=0.18, rot=0.3)
    round_table(st, 10.0, 12.9, z0 + 0.02, 0.5, h=0.38, top_t=0.04, mi=3, legs='three', mi_leg=1)
    vase(st, 10.0, 12.9, z0 + 0.4, h=0.1, r=0.14, mi=0, style='bowl')
    tray(st, 10.25, 13.1, z0 + 0.4, w=0.26, d=0.18, mi=1, rot=0.4)
    candle(st, 10.27, 13.1, z0 + 0.412, r=0.03, h=0.07, mi_wax=5, mi_flame=6)
    st.build("Family_Tables", [M['walnut'], M['black_metal'], M['lampshade'], M['marble'], M['book'], M['ceramic_cream'], M['fire']], smooth=True)
    pl = MB()
    fig_plant(pl, 11.85, yn - 0.8, z0 + 0.02, pot_r=0.26, pot_h=0.38, h=1.5, mi_pot=0, mi_leaf=1, mi_stem=2, mi_soil=3, seed=11, n_leaves=13)
    pl.build("Family_Plant", [M['clay'], M['leaf_plant'], M['bark'], M['soil']], smooth=True)
    box("Family_SouthFinish", x0, x0 + 2.0, y0, y0 + 0.02, z0, z1 - 0.32, M['white_int'])                      # plaster face of the exterior's pier
    a = MB(); floater_art(a, x0 + 0.3, x0 + 1.9, y0 + 0.02, z0 + 1.2, z0 + 2.5, along='X', face=1, mi_frame=0, mi_canvas=1, mi_light=2, mi_lens=3)   # on the living/family partition
    a.build("Family_Art", [M['oak'], M['art_abstract'], M['brass'], M['emit_bar']])
    # lighting: the cove glow (strips along the bulkhead's inner edge, pointing up into the recess), 6 downlight
    # pools, lit shelves, the fire; only a weak general fill
    room_light("L_Family", 'family', energy=30, color=K30)
    _spots("L_FamilyDL", dl_pts, z1 - 0.05, energy=24, spot=64, blend=0.55)
    for (cx_, cy_, sx_, sy_) in ((x0 + 0.72, (y0 + y1) / 2, 0.06, y1 - y0 - 1.5), (x1 - 0.72, (y0 + y1) / 2, 0.06, y1 - y0 - 1.5),
                                 ((x0 + x1) / 2, y0 + 0.72, x1 - x0 - 1.5, 0.06), ((x0 + x1) / 2, y1 - 0.72, x1 - x0 - 1.5, 0.06)):
        area_light(f"L_FamilyCove_{cx_:.1f}_{cy_:.1f}", (cx_, cy_, z1 - 0.30), (sx_, sy_), 14, (1.0, 0.82, 0.58), down=False)
    add_light("L_FamilyShelfW", 'AREA', (x0 + 0.55, yn - 0.2, z0 + 1.6), 5, (1.0, 0.85, 0.65), size=0.1)
    add_light("L_FamilyShelfE", 'AREA', (x1 - 0.55, yn - 0.2, z0 + 1.6), 5, (1.0, 0.85, 0.65), size=0.1)
    add_light("L_FamilyFire", 'POINT', (10.0, yn - 0.5, z0 + 0.6), 24, (1.0, 0.5, 0.18), size=0.3)
    add_light("L_FamilyLamp", 'POINT', (11.5, 15.4, z0 + 0.95), 6, (1.0, 0.78, 0.55), size=0.1)


def build(M):
    living(M)
    dining(M)
    kitchen(M)
    family(M)
