"""Reusable architectural + furniture parts (glass walls / rails, slats, stairs, downlights, doors, shelves, sofas,
chairs, tables, beds, lamps, plants, pendants, TVs, art, tub, basin, bike, cabinets ...).

All functions take an MB and add geometry to it using material-slot indices documented per function; the caller
does mb.build(name, [mat_for_slot0, mat_for_slot1, ...]).  Coordinates are metres in the house's plan frame.
"""
import math, random
from .mesh import *
from .lights import *

GLASS_T = 0.012                     # glass pane thickness (frameless rails / sloped rails)


# ================================================================== architecture
def glass_wall(mb, x0, x1, y0, y1, z0, z1, mi_glass=0, mi_frame=1, mullions=(), frame_w=0.05, sill=True):
    """Glazed plane (thin box) + slim dark frame + optional mullions (positions along the long axis)."""
    mb.box(x0, x1, y0, y1, z0, z1, mi_glass)
    d = frame_w
    if abs(x1 - x0) > abs(y1 - y0):
        yc0, yc1 = min(y0, y1) - 0.02, max(y0, y1) + 0.02
        if sill: mb.box(x0, x1, yc0, yc1, z0, z0 + d, mi_frame)
        mb.box(x0, x1, yc0, yc1, z1 - d, z1, mi_frame)
        mb.box(x0, x0 + d, yc0, yc1, z0, z1, mi_frame); mb.box(x1 - d, x1, yc0, yc1, z0, z1, mi_frame)
        for mx in mullions:
            mb.box(mx - d / 2, mx + d / 2, yc0, yc1, z0, z1, mi_frame)
    else:
        xc0, xc1 = min(x0, x1) - 0.02, max(x0, x1) + 0.02
        if sill: mb.box(xc0, xc1, y0, y1, z0, z0 + d, mi_frame)
        mb.box(xc0, xc1, y0, y1, z1 - d, z1, mi_frame)
        mb.box(xc0, xc1, y0, y0 + d, z0, z1, mi_frame); mb.box(xc0, xc1, y1 - d, y1, z0, z1, mi_frame)
        for my in mullions:
            mb.box(xc0, xc1, my - d / 2, my + d / 2, z0, z1, mi_frame)


def glass_rail(mb, pts, z0, h=1.05, mi_glass=0, mi_shoe=1, shoe=0.06, cap=True):
    """Frameless glass balustrade along a polyline of (x, y) points, stainless shoe + slim top cap."""
    for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
        if abs(ax - bx) > abs(ay - by):
            x0, x1 = min(ax, bx), max(ax, bx)
            mb.box(x0, x1, ay - GLASS_T / 2, ay + GLASS_T / 2, z0, z0 + h, mi_glass)
            mb.box(x0, x1, ay - shoe / 2, ay + shoe / 2, z0 - 0.02, z0 + 0.08, mi_shoe)
            if cap: mb.box(x0, x1, ay - 0.02, ay + 0.02, z0 + h - 0.015, z0 + h + 0.015, mi_shoe)
        else:
            y0, y1 = min(ay, by), max(ay, by)
            mb.box(ax - GLASS_T / 2, ax + GLASS_T / 2, y0, y1, z0, z0 + h, mi_glass)
            mb.box(ax - shoe / 2, ax + shoe / 2, y0, y1, z0 - 0.02, z0 + 0.08, mi_shoe)
            if cap: mb.box(ax - 0.02, ax + 0.02, y0, y1, z0 + h - 0.015, z0 + h + 0.015, mi_shoe)


def sloped_rail(mb, x, y0, y1, z0, z1, h=1.05, mi_glass=0, mi_shoe=1):
    """Glass panel following a stair that runs along Y at constant x."""
    mb.hexa([(x - GLASS_T / 2, y0, z0), (x + GLASS_T / 2, y0, z0), (x + GLASS_T / 2, y1, z1), (x - GLASS_T / 2, y1, z1),
             (x - GLASS_T / 2, y0, z0 + h), (x + GLASS_T / 2, y0, z0 + h), (x + GLASS_T / 2, y1, z1 + h), (x - GLASS_T / 2, y1, z1 + h)], mi_glass)
    mb.hexa([(x - 0.02, y0, z0 + h - 0.015), (x + 0.02, y0, z0 + h - 0.015), (x + 0.02, y1, z1 + h - 0.015), (x - 0.02, y1, z1 + h - 0.015),
             (x - 0.02, y0, z0 + h + 0.015), (x + 0.02, y0, z0 + h + 0.015), (x + 0.02, y1, z1 + h + 0.015), (x - 0.02, y1, z1 + h + 0.015)], mi_shoe)


def sloped_rail_x(mb, y, x0, x1, z0, z1, h=1.05, mi_glass=0, mi_shoe=1):
    """Glass panel following a stair that runs along X at constant y."""
    mb.hexa([(x0, y - GLASS_T / 2, z0), (x1, y - GLASS_T / 2, z1), (x1, y + GLASS_T / 2, z1), (x0, y + GLASS_T / 2, z0),
             (x0, y - GLASS_T / 2, z0 + h), (x1, y - GLASS_T / 2, z1 + h), (x1, y + GLASS_T / 2, z1 + h), (x0, y + GLASS_T / 2, z0 + h)], mi_glass)
    mb.hexa([(x0, y - 0.02, z0 + h - 0.015), (x1, y - 0.02, z1 + h - 0.015), (x1, y + 0.02, z1 + h - 0.015), (x0, y + 0.02, z0 + h - 0.015),
             (x0, y - 0.02, z0 + h + 0.015), (x1, y - 0.02, z1 + h + 0.015), (x1, y + 0.02, z1 + h + 0.015), (x0, y + 0.02, z0 + h + 0.015)], mi_shoe)


def slats(mb, axis, a0, a1, b, depth, z0, z1, w=0.06, gap=0.035, mi=0, sign=1):
    """Vertical slats along `axis` from a0..a1 at position b on the other axis, projecting `depth` toward `sign`."""
    a = a0
    while a + w <= a1 + 1e-6:
        if axis == 'X':
            mb.box(a, a + w, b, b + sign * depth, z0, z1, mi)
        else:
            mb.box(b, b + sign * depth, a, a + w, z0, z1, mi)
        a += w + gap


def stairs(mb, x0, x1, y_start, y_end, z0, z1, n=None, mi=0, riser=0.17, base=0.3):
    """Straight solid stair rising from (y_start, z0) to (y_end, z1) along +/-Y."""
    n = n or max(2, round((z1 - z0) / riser))
    dz = (z1 - z0) / n
    dy = (y_end - y_start) / n
    for i in range(n):
        ya = y_start + dy * i
        mb.box(x0, x1, min(ya, y_end), max(ya, y_end), z0 - base, z0 + dz * (i + 1), mi)
    return n


def stairs_x(mb, y0, y1, x_start, x_end, z0, z1, n=None, mi=0, riser=0.17, base=0.3):
    n = n or max(2, round((z1 - z0) / riser))
    dz = (z1 - z0) / n
    dx = (x_end - x_start) / n
    for i in range(n):
        xa = x_start + dx * i
        mb.box(min(xa, x_end), max(xa, x_end), y0, y1, z0 - base, z0 + dz * (i + 1), mi)
    return n


def downlights(mb, pts, z, r=0.055, mi=0, mi_trim=None):
    """Recessed downlights: flush lens disc + a slim dark trim ring (mi_trim defaults to mi+1; clamps to mi if absent)."""
    mi_trim = mi + 1 if mi_trim is None else mi_trim
    for x, y in pts:
        mb.cylinder(x, y, z - 0.004, z + 0.02, r, seg=16, mi=mi)
        mb.lathe(x, y, z - 0.005, [(r, 0), (r + 0.012, 0), (r + 0.012, 0.004), (r, 0.004)], seg=16, mi=mi_trim)


def track_lights(mb, x0, x1, y, z, mi_track=0, mi_lamp=1, n=4):
    """Black recessed linear track with n small spot heads."""
    mb.box(x0, x1, y - 0.03, y + 0.03, z - 0.01, z + 0.02, mi_track)
    for i in range(n):
        x = x0 + (x1 - x0) * (i + 0.5) / n
        mb.cylinder(x, y, z - 0.02, z - 0.005, 0.02, seg=8, mi=mi_lamp)


def cove(mb, x0, x1, y0, y1, z, w=0.08, mi=0):
    """Emissive perimeter cove strip (rectangular ring) at height z."""
    mb.box(x0, x1, y0, y0 + w, z, z + 0.01, mi); mb.box(x0, x1, y1 - w, y1, z, z + 0.01, mi)
    mb.box(x0, x0 + w, y0, y1, z, z + 0.01, mi); mb.box(x1 - w, x1, y0, y1, z, z + 0.01, mi)


def door_leaf(mb, x0, x1, y, z0, z1, mi=0, thick=0.045, along='X'):
    if along == 'X':
        mb.box(x0, x1, y - thick / 2, y + thick / 2, z0, z1, mi)
    else:
        mb.box(y - thick / 2, y + thick / 2, x0, x1, z0, z1, mi)


def door_frame(mb, x0, x1, y, z0, z1, mi=0, w=0.06, d=0.15, along='X'):
    if along == 'X':
        mb.box(x0 - w, x0, y - d / 2, y + d / 2, z0, z1 + w, mi)
        mb.box(x1, x1 + w, y - d / 2, y + d / 2, z0, z1 + w, mi)
        mb.box(x0 - w, x1 + w, y - d / 2, y + d / 2, z1, z1 + w, mi)
    else:
        mb.box(y - d / 2, y + d / 2, x0 - w, x0, z0, z1 + w, mi)
        mb.box(y - d / 2, y + d / 2, x1, x1 + w, z0, z1 + w, mi)
        mb.box(y - d / 2, y + d / 2, x0 - w, x1 + w, z1, z1 + w, mi)


def shelves(mb, x0, x1, y0, y1, z0, z1, n=5, t=0.03, mi=0, back=True):
    """Open shelving unit: sides + n shelves (+ back)."""
    mb.box(x0, x0 + t, y0, y1, z0, z1, mi); mb.box(x1 - t, x1, y0, y1, z0, z1, mi)
    if back:
        mb.box(x0, x1, y1 - t, y1, z0, z1, mi)
    for i in range(n + 1):
        z = z0 + (z1 - z0) * i / n
        mb.box(x0, x1, y0, y1, z - t / 2 if i else z, z + t / 2 if i < n else z, mi)


# ================================================================== furniture
def sofa(mb, x, y, w, d, rot=0.0, z=0.0, mi_seat=0, mi_back=None, mi_base=None, arms=True, seat_h=0.42, back_h=0.78,
         arm_w=0.22, back_d=0.22, cushion_gap=0.0, plinth=0.0, mi_plinth=None, soft=0.06, pillows=0, mi_pillow=None):
    """Upholstered sofa centred at (x, y), width w (along its own X), depth d, facing its own -Y (rot=0 -> faces -Y/street).
    Rounded, stuffed cushions (rcbox with puff) so it reads as boucle upholstery, optional loose back pillows."""
    mi_back = mi_seat if mi_back is None else mi_back
    mi_base = mi_seat if mi_base is None else mi_base
    mi_pillow = mi_back if mi_pillow is None else mi_pillow
    def B(cx, cy, cz, sx, sy, sz, mi, r=soft, puff=0.0):
        px, py = rot2(x + cx, y + cy, x, y, rot)
        mb.rcbox(px, py, z + cz, sx, sy, sz, r, mi, rot, puff=puff)
    hw, hd = w / 2, d / 2
    aw = arm_w if arms else 0.0
    if plinth > 0:
        B(0, 0, plinth / 2, w - 0.1, d - 0.1, plinth, mi_plinth if mi_plinth is not None else mi_base, r=0.01)
    base_h = seat_h - 0.16 - plinth
    B(0, 0, plinth + base_h / 2, w, d, base_h, mi_base, r=0.03)                          # base
    seat_w = w - 2 * aw
    n = 1 if (cushion_gap <= 0 or seat_w < 1.2) else (2 if seat_w < 2.4 else 3)
    cw = (seat_w - (n - 1) * cushion_gap) / n
    for i in range(n):
        cx = -seat_w / 2 + cw / 2 + i * (cw + cushion_gap)
        B(cx, -back_d / 2, seat_h - 0.08, cw, d - back_d - 0.02, 0.17, mi_seat, r=0.07, puff=0.5)     # seat cushions
    B(0, hd - back_d / 2, seat_h + (back_h - seat_h) / 2, seat_w, back_d, back_h - seat_h + 0.02, mi_back, r=0.08, puff=0.3)   # back
    if arms:
        for sx in (-1, 1):
            B(sx * (hw - aw / 2), 0, (seat_h + 0.2) / 2, aw, d, seat_h + 0.2, mi_base, r=0.06)
    for i in range(pillows):
        cx = -seat_w / 2 + seat_w * (i + 0.5) / pillows
        px, py = rot2(x + cx, y + hd - back_d - 0.14, x, y, rot)
        mb.pillow(px, py, z + seat_h + 0.22, 0.5, 0.5, 0.16, mi_pillow, rot=rot + (i - (pillows - 1) / 2) * 0.08, pitch=math.pi / 2 - 0.3)


def curved_sofa(mb, cx, cy, r, a0, a1, z=0.0, depth=0.95, seat_h=0.42, back_h=0.75, mi=0, seg=14, cushions=0):
    """Arc sofa: seat ring sector r-depth..r, back on the outer edge."""
    mb.arc_prism(cx, cy, r - depth, r, a0, a1, z + 0.12, z + seat_h, seg, mi)
    mb.arc_prism(cx, cy, r - 0.28, r, a0, a1, z + seat_h, z + back_h, seg, mi)
    mb.arc_prism(cx, cy, r - depth + 0.05, r - 0.05, a0, a1, z + 0.02, z + 0.12, seg, mi)
    for i in range(cushions):
        a = a0 + (a1 - a0) * (i + 0.5) / cushions
        px, py = cx + (r - 0.3) * math.cos(a), cy + (r - 0.3) * math.sin(a)
        mb.blob((px, py, z + back_h - 0.05), 0.24, seg=10, rings=6, mi=mi, squash=0.9)


def armchair(mb, x, y, rot=0.0, z=0.0, w=0.85, d=0.85, mi=0, mi_legs=None, style='barrel'):
    """Rounded lounge chair facing its own -Y."""
    mi_legs = mi if mi_legs is None else mi_legs
    def B(cx, cy, cz, sx, sy, sz, mi_, r=0.05, puff=0.0):
        px, py = rot2(x + cx, y + cy, x, y, rot)
        mb.rcbox(px, py, z + cz, sx, sy, sz, r, mi_, rot, puff=puff)
    if style == 'barrel':
        B(0, 0, 0.30, w - 0.1, d - 0.1, 0.28, mi, r=0.07, puff=0.4)              # seat
        B(0, d / 2 - 0.12, 0.55, w, 0.24, 0.55, mi, r=0.09)                      # back
        B(-w / 2 + 0.11, 0.05, 0.50, 0.22, d - 0.3, 0.45, mi, r=0.08)            # arms
        B(w / 2 - 0.11, 0.05, 0.50, 0.22, d - 0.3, 0.45, mi, r=0.08)
        for sx in (-1, 1):
            for sy in (-1, 1):
                px, py = rot2(x + sx * (w / 2 - 0.1), y + sy * (d / 2 - 0.1), x, y, rot)
                mb.cylinder(px, py, z, z + 0.16, 0.02, seg=10, mi=mi_legs)
    else:  # 'jeanneret' style: wooden frame + cane / cushion
        B(0, 0, 0.42, w, d, 0.07, mi, r=0.03, puff=0.3)                          # seat pad
        B(0, d / 2 - 0.04, 0.72, w, 0.07, 0.55, mi, r=0.03)                      # back pad
        for sx in (-1, 1):
            px, py = rot2(x + sx * (w / 2 - 0.02), y - d / 2 + 0.03, x, y, rot)
            mb.cbox(px, py, z + 0.22, 0.04, 0.04, 0.44, mi_legs, rot)              # front legs
            px, py = rot2(x + sx * (w / 2 - 0.02), y + d / 2 - 0.05, x, y, rot)
            mb.cbox(px, py, z + 0.50, 0.04, 0.05, 1.0, mi_legs, rot)              # back uprights
            px, py = rot2(x + sx * (w / 2 - 0.02), y, x, y, rot)
            mb.cbox(px, py, z + 0.62, 0.035, d - 0.1, 0.035, mi_legs, rot)         # arm rails
            px, py = rot2(x + sx * (w / 2 - 0.02), y + 0.05, x, y, rot)
            mb.cbox(px, py, z + 0.42, 0.04, d - 0.1, 0.04, mi_legs, rot)           # side rails
def dining_chair(mb, x, y, rot=0.0, z=0.0, mi_wood=0, mi_seat=1, w=0.48, d=0.5, cane=False):
    """Pierre-Jeanneret style chair: angled compass legs, cane/pad seat + back; faces its own -Y."""
    def B(cx, cy, cz, sx, sy, sz, mi_):
        px, py = rot2(x + cx, y + cy, x, y, rot)
        mb.cbox(px, py, z + cz, sx, sy, sz, mi_, rot)
    def R(cx, cy, cz, sx, sy, sz, mi_, r=0.02, puff=0.0):
        px, py = rot2(x + cx, y + cy, x, y, rot)
        mb.rcbox(px, py, z + cz, sx, sy, sz, r, mi_, rot, puff=puff)
    R(0, 0, 0.44, w, d, 0.045, mi_seat, r=0.02, puff=0.3)
    R(0, d / 2 - 0.03, 0.72, w - 0.06, 0.04, 0.42, mi_seat, r=0.018)
    for sx in (-1, 1):
        B(sx * (w / 2 - 0.02), -d / 2 + 0.03, 0.21, 0.035, 0.035, 0.42, mi_wood)
        B(sx * (w / 2 - 0.02), d / 2 - 0.03, 0.48, 0.035, 0.035, 0.96, mi_wood)
        B(sx * (w / 2 - 0.02), 0, 0.40, 0.03, d - 0.05, 0.03, mi_wood)
    B(0, -d / 2 + 0.03, 0.40, w - 0.04, 0.03, 0.03, mi_wood)
    B(0, d / 2 - 0.03, 0.95, w - 0.06, 0.03, 0.03, mi_wood)
def stool(mb, x, y, z=0.0, h=0.72, mi_wood=0, mi_seat=1, r=0.19, rot=0.0):
    """Counter stool: round padded seat on a square wooden frame with back."""
    mb.lathe(x, y, z + h - 0.06, [(0, 0), (r * 0.9, 0), (r, 0.025), (r * 0.98, 0.05), (r * 0.7, 0.065), (0, 0.07)], seg=24, mi=mi_seat)
    for sx in (-1, 1):
        for sy in (-1, 1):
            px, py = rot2(x + sx * (r - 0.03), y + sy * (r - 0.03), x, y, rot)
            mb.cbox(px, py, z + (h - 0.06) / 2, 0.03, 0.03, h - 0.06, mi_wood, rot)
    px, py = rot2(x, y + r - 0.03, x, y, rot)
    mb.cbox(px, py, z + h + 0.12, 2 * r - 0.06, 0.03, 0.22, mi_wood, rot)
    for sy in (-1, 1):
        px, py = rot2(x, y + sy * (r - 0.03), x, y, rot)
        mb.cbox(px, py, z + 0.25, 2 * r - 0.06, 0.03, 0.03, mi_wood, rot)
def table(mb, x, y, z, w, d, h=0.75, top_t=0.05, mi_top=0, mi_leg=None, legs='four', rot=0.0, leg_w=0.06):
    mi_leg = mi_top if mi_leg is None else mi_leg
    mb.cbox(x, y, z + h - top_t / 2, w, d, top_t, mi_top, rot)
    if legs == 'four':
        for sx in (-1, 1):
            for sy in (-1, 1):
                px, py = rot2(x + sx * (w / 2 - leg_w), y + sy * (d / 2 - leg_w), x, y, rot)
                mb.cbox(px, py, z + (h - top_t) / 2, leg_w, leg_w, h - top_t, mi_leg, rot)
    elif legs == 'pedestal':
        mb.cbox(x, y, z + (h - top_t) / 2, w * 0.45, d * 0.55, h - top_t, mi_leg, rot)
    elif legs == 'trestle':
        for sx in (-1, 1):
            px, py = rot2(x + sx * (w / 2 - 0.35), y, x, y, rot)
            mb.cbox(px, py, z + (h - top_t) / 2, 0.08, d - 0.3, h - top_t, mi_leg, rot)
        mb.cbox(x, y, z + 0.15, w - 0.8, 0.08, 0.08, mi_leg, rot)
    elif legs == 'drum':
        mb.cylinder(x, y, z, z + h - top_t, min(w, d) * 0.32, seg=24, mi=mi_leg)


def round_table(mb, x, y, z, r, h=0.4, top_t=0.04, mi=0, mi_leg=None, legs='drum', seg=32):
    mi_leg = mi if mi_leg is None else mi_leg
    mb.cylinder(x, y, z + h - top_t, z + h, r, seg=seg, mi=mi)
    if legs == 'drum':
        mb.cylinder(x, y, z, z + h - top_t, r * 0.55, seg=seg, mi=mi_leg)
    elif legs == 'three':
        for i in range(3):
            a = 2 * math.pi * i / 3 + math.pi / 2
            mb.cylinder(x + r * 0.6 * math.cos(a), y + r * 0.6 * math.sin(a), z, z + h - top_t, 0.02, seg=8, mi=mi_leg)


def bed(mb, x, y, rot=0.0, z=0.0, w=1.9, l=2.15, mi_frame=0, mi_linen=1, mi_pillow=None, mi_throw=None, head_h=1.0, platform=True, seed=0,
        mi_duvet=None, channels=4, legs=True):
    """Upholstered bed centred at (x,y), headboard on its own +Y side.  Box base on short legs, mattress with a fitted
    sheet, a plump duvet folded back at the head, two sleeping pillows + two standing euro shams + a lumbar cushion
    (sewn-pillow meshes, not blobs), a folded throw across the foot, a channel-tufted headboard."""
    rng = random.Random(seed)
    mi_pillow = mi_linen if mi_pillow is None else mi_pillow
    mi_throw = mi_linen if mi_throw is None else mi_throw
    mi_duvet = mi_linen if mi_duvet is None else mi_duvet
    def R(cx, cy, cz, sx, sy, sz, mi_, r=0.05, puff=0.0, seg=3):
        px, py = rot2(x + cx, y + cy, x, y, rot)
        mb.rcbox(px, py, z + cz, sx, sy, sz, r, mi_, rot, seg=seg, puff=puff)
    def PIL(cx, cy, cz, pw, pd, pt, mi_, yaw=0.0, pitch=0.0, sd=0):
        px, py = rot2(x + cx, y + cy, x, y, rot)
        mb.pillow_sq(px, py, z + cz, pw, pd, pt, mi_, rot=rot + yaw, pitch=pitch, seed=seed * 10 + sd)
    zb0 = 0.11 if legs else 0.0
    if legs:
        for sx_, sy_ in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            px, py = rot2(x + sx_ * (w / 2 + 0.02), y + sy_ * (l / 2 - 0.08), x, y, rot)
            mb.cylinder(px, py, z, z + zb0 + 0.02, 0.03, 0.025, seg=10, mi=mi_frame)
    R(0, 0, zb0 + 0.14, w + 0.10, l + 0.04, 0.28, mi_frame, r=0.03)                         # upholstered box base
    R(0, 0.0, zb0 + 0.28 + 0.12, w, l - 0.06, 0.24, mi_linen, r=0.07, puff=0.12)             # mattress + fitted sheet
    zm = zb0 + 0.28 + 0.24                                                                    # top of the mattress
    # duvet: covers from 0.62 m below the head end to 0.06 past the foot, overhanging the sides; folded back at the head
    dy0, dy1 = -l / 2 - 0.05, l / 2 - 0.62
    R(0, (dy0 + dy1) / 2, zm + 0.06, w + 0.14, dy1 - dy0, 0.14, mi_duvet, r=0.07, puff=0.7, seg=4)
    R(0, dy1 - 0.17, zm + 0.16, w + 0.10, 0.34, 0.09, mi_duvet, r=0.045, puff=0.6, seg=4)   # the turned-back fold
    for sgn in (-1, 1):                                                                      # side drops of the duvet
        R(sgn * (w / 2 + 0.055), (dy0 + dy1) / 2, zm - 0.08, 0.05, dy1 - dy0 - 0.08, 0.26, mi_duvet, r=0.022, seg=2)
    # pillows: two sleeping pillows flat at the head, two euro shams standing behind, a lumbar in front
    n = 2 if w >= 1.3 else 1
    pw = (w - 0.12) / n
    for i in range(n):
        cx = (i - (n - 1) / 2) * (w / n)
        PIL(cx, l / 2 - 0.40, zm + 0.10, pw - 0.06, 0.52, 0.20, mi_pillow, yaw=rng.uniform(-0.05, 0.05), sd=i)
        PIL(cx * 0.98, l / 2 - 0.20, zm + 0.31, min(0.66, pw - 0.02), 0.66, 0.19, mi_pillow, yaw=rng.uniform(-0.04, 0.04), pitch=1.25 + rng.uniform(-0.05, 0.05), sd=10 + i)
    PIL(0, l / 2 - 0.62, zm + 0.19, 0.55 if n == 2 else 0.45, 0.32, 0.16, mi_throw, yaw=rng.uniform(-0.08, 0.08), pitch=1.1, sd=20)
    # throw folded across the foot, laid at a slight angle
    ty = -l / 2 + 0.42
    R(0.05, ty, zm + 0.13 + 0.016, w * 0.72, 0.55, 0.032, mi_throw, r=0.015, puff=0.7, seg=3)
    R(-0.12, ty + 0.06, zm + 0.13 + 0.046, w * 0.48, 0.42, 0.03, mi_throw, r=0.015, puff=0.7, seg=3)
    # headboard: upholstered panel with vertical channels
    R(0, l / 2 + 0.06, head_h / 2 + 0.05, w + 0.24, 0.09, head_h - 0.1, mi_frame, r=0.03)
    if channels > 0:
        cw = (w + 0.20) / channels
        for i in range(channels):
            cx = (i - (channels - 1) / 2) * cw
            R(cx, l / 2 + 0.035, head_h / 2 + 0.08, cw - 0.03, 0.05, head_h - 0.2, mi_frame, r=0.02, puff=0.35)
def nightstand(mb, x, y, z=0.0, w=0.6, d=0.45, h=0.5, mi=0, rot=0.0, floating=False):
    if floating:
        mb.cbox(x, y, z + h - 0.12, w, d, 0.24, mi, rot)
    else:
        mb.cbox(x, y, z + h / 2, w, d, h, mi, rot)


def lamp(mb, x, y, z, mi_base=0, mi_shade=1, base_r=0.18, base_h=0.32, shade_r=0.25, shade_h=0.25):
    """Table lamp: rounded base + drum shade."""
    mb.lathe(x, y, z, [(0.0, 0), (base_r * 0.8, 0), (base_r, base_h * 0.4), (base_r * 0.85, base_h * 0.8), (base_r * 0.3, base_h), (0.02, base_h), (0.02, base_h + 0.1), (0, base_h + 0.1)], seg=20, mi=mi_base)
    mb.lathe(x, y, z + base_h + 0.08, [(shade_r * 0.75, 0), (shade_r, 0), (shade_r * 0.85, shade_h), (shade_r * 0.6, shade_h)], seg=24, mi=mi_shade)


def vase(mb, x, y, z, h=0.4, r=0.16, mi=0, style='round'):
    if style == 'round':
        prof = [(0, 0), (r * 0.6, 0), (r, h * 0.35), (r * 0.9, h * 0.7), (r * 0.5, h * 0.9), (r * 0.35, h), (0, h)]
    elif style == 'tall':
        prof = [(0, 0), (r * 0.7, 0), (r, h * 0.4), (r * 0.8, h * 0.9), (r * 0.75, h), (0, h)]
    else:  # bowl
        prof = [(0, 0), (r * 0.4, 0), (r * 0.9, h * 0.5), (r, h), (0, h)]
    mb.lathe(x, y, z, prof, seg=20, mi=mi)


def branches(mb, x, y, z, h=1.0, n=7, seed=0, mi=0, leaves=0, mi_leaf=1, spread=0.35):
    """Bare / leafy branch arrangement rising from (x,y,z)."""
    rng = random.Random(seed)
    for i in range(n):
        a = 2 * math.pi * i / n + rng.uniform(-0.4, 0.4)
        top = (x + spread * h * math.cos(a) * rng.uniform(0.4, 1.0), y + spread * h * math.sin(a) * rng.uniform(0.4, 1.0), z + h * rng.uniform(0.7, 1.0))
        mid = ((x + top[0]) / 2 + rng.uniform(-0.05, 0.05), (y + top[1]) / 2 + rng.uniform(-0.05, 0.05), (z + top[2]) / 2)
        mb.path_tube([(x, y, z), mid, top], 0.006, seg=5, mi=mi)
        for k in range(leaves):
            t = rng.uniform(0.3, 1.0)
            p = (x + (top[0] - x) * t + rng.uniform(-0.08, 0.08), y + (top[1] - y) * t + rng.uniform(-0.08, 0.08), z + (top[2] - z) * t + rng.uniform(-0.05, 0.05))
            mb.blob(p, 0.035, seg=6, rings=4, jitter=0.4, seed=seed * 100 + i * 10 + k, mi=mi_leaf, squash=0.35)


def potted_plant(mb, x, y, z, pot_r=0.3, pot_h=0.45, h=1.6, mi_pot=0, mi_leaf=1, mi_stem=2, seed=0, kind='olive'):
    mb.lathe(x, y, z, [(0, 0), (pot_r * 0.85, 0), (pot_r, pot_h), (pot_r * 0.9, pot_h), (pot_r * 0.9, pot_h - 0.03), (0, pot_h - 0.03)], seg=20, mi=mi_pot)
    rng = random.Random(seed)
    if kind == 'olive':
        mb.tube((x, y, z + pot_h - 0.03), (x + 0.05, y, z + pot_h + h * 0.45), 0.03, 0.02, seg=6, mi=mi_stem)
        for i in range(6):
            a = 2 * math.pi * i / 6 + rng.uniform(-0.3, 0.3)
            p = (x + 0.05 + h * 0.3 * math.cos(a), y + h * 0.3 * math.sin(a), z + pot_h + h * rng.uniform(0.55, 0.95))
            mb.tube((x + 0.05, y, z + pot_h + h * 0.45), p, 0.015, 0.006, seg=5, mi=mi_stem)
            mb.blob(p, h * 0.16, seg=10, rings=6, jitter=0.5, seed=seed * 10 + i, mi=mi_leaf, squash=0.7)
        mb.blob((x + 0.05, y, z + pot_h + h * 0.7), h * 0.2, seg=10, rings=6, jitter=0.5, seed=seed * 10 + 9, mi=mi_leaf)
    else:  # broad-leaf: few big leaves
        for i in range(9):
            a = 2 * math.pi * i / 9 + rng.uniform(-0.2, 0.2)
            tip = (x + h * 0.4 * math.cos(a), y + h * 0.4 * math.sin(a), z + pot_h + h * rng.uniform(0.5, 1.0))
            mb.tube((x, y, z + pot_h), tip, 0.012, 0.006, seg=5, mi=mi_stem)
            mb.blob(tip, h * 0.14, seg=8, rings=5, jitter=0.3, seed=seed * 10 + i, mi=mi_leaf, squash=0.25, rx=1.6)


def pendant(mb, x, y, z_ceiling, drop=1.0, r=0.12, mi_cord=0, mi_shade=1, style='globe'):
    mb.cylinder(x, y, z_ceiling - drop, z_ceiling, 0.004, seg=6, mi=mi_cord)
    if style == 'globe':
        mb.sphere((x, y, z_ceiling - drop - r), r, seg=16, rings=10, mi=mi_shade)
    else:  # dome
        mb.lathe(x, y, z_ceiling - drop - r, [(0, r), (r * 0.5, r * 0.95), (r, r * 0.6), (r, 0), (0, 0)], seg=20, mi=mi_shade)


def tv(mb, x0, x1, y, z0, z1, mi=0, along='X', d=0.04, bezel=0.01):
    if along == 'X':
        mb.box(x0, x1, y - d, y, z0, z1, mi)
    else:
        mb.box(y - d, y, x0, x1, z0, z1, mi)


def picture(mb, x0, x1, y, z0, z1, mi_frame=0, mi_canvas=1, along='X', d=0.04, frame_w=0.03, face=1):
    """Framed canvas on a wall; `face` = +1 if the picture faces +axis (normal), -1 otherwise."""
    if along == 'X':
        mb.box(x0, x1, y, y + face * d, z0, z1, mi_frame)
        mb.box(x0 + frame_w, x1 - frame_w, y + face * d, y + face * (d + 0.002), z0 + frame_w, z1 - frame_w, mi_canvas)
    else:
        mb.box(y, y + face * d, x0, x1, z0, z1, mi_frame)
        mb.box(y + face * d, y + face * (d + 0.002), x0 + frame_w, x1 - frame_w, z0 + frame_w, z1 - frame_w, mi_canvas)


def cushion(mb, x, y, z, w=0.5, d=0.5, t=0.14, mi=0, rot=0.0, upright=False, tilt=0.35):
    """Throw pillow: plump; `upright` stands it against a backrest (leaning back by `tilt` radians)."""
    if upright:
        mb.pillow_sq(x, y, z + d / 2 * 0.92, w, d, t, mi, rot=rot, pitch=math.pi / 2 - tilt, seed=int(x * 7 + y * 3))
    else:
        mb.pillow_sq(x, y, z + t / 2, w, d, t, mi, rot=rot, seed=int(x * 7 + y * 3))


def books(mb, x, y, z, n=3, mi=0, rot=0.0, w=0.3, d=0.24):
    for i in range(n):
        mb.cbox(x + (i % 2) * 0.02, y - (i % 2) * 0.015, z + 0.015 + i * 0.03, w - i * 0.02, d - i * 0.01, 0.03, mi, rot)


def lounger(mb, x, y, z, mi=0, rot=0.0):
    """In-pool white chaise: a low bent slab, foot toward its own -Y."""
    def H(pts, mi_):
        mb.hexa([(*rot2(px, py, x, y, rot), pz) for (px, py, pz) in pts], mi_)
    mb.cbox(*rot2(x, y - 0.3, x, y, rot), z + 0.03, 0.7, 1.2, 0.06, mi, rot)
    H([(x - 0.35, y + 0.3, z), (x + 0.35, y + 0.3, z), (x + 0.35, y + 0.95, z + 0.45), (x - 0.35, y + 0.95, z + 0.45),
       (x - 0.35, y + 0.3, z + 0.06), (x + 0.35, y + 0.3, z + 0.06), (x + 0.35, y + 0.95, z + 0.51), (x - 0.35, y + 0.95, z + 0.51)], mi)


def outdoor_sofa(mb, x, y, w, d=0.95, rot=0.0, z=0.0, mi_frame=0, mi_cushion=1, seats=3):
    """Teak-framed outdoor sofa with loose cushions; faces its own -Y. Slatted seat deck + solid teak arm panels."""
    def B(cx, cy, cz, sx, sy, sz, mi_):
        px, py = rot2(x + cx, y + cy, x, y, rot)
        mb.cbox(px, py, z + cz, sx, sy, sz, mi_, rot)
    def R(cx, cy, cz, sx, sy, sz, mi_, r=0.04, puff=0.0):
        px, py = rot2(x + cx, y + cy, x, y, rot)
        mb.rcbox(px, py, z + cz, sx, sy, sz, r, mi_, rot, puff=puff)
    hw, hd = w / 2, d / 2
    ns = max(4, int((d - 0.12) / 0.07))
    for i in range(ns):                                              # slatted seat deck
        cy = -hd + 0.06 + (d - 0.12) * (i + 0.5) / ns
        B(0, cy, 0.32, w - 0.12, (d - 0.12) / ns * 0.75, 0.03, mi_frame)
    B(0, hd - 0.03, 0.62, w, 0.06, 0.66, mi_frame)                    # back frame
    for i in range(1, 4):                                            # back slats
        B(0, hd - 0.03, 0.40 + i * 0.15, w - 0.12, 0.02, 0.06, mi_frame)
    for sx in (-1, 1):
        B(sx * (hw - 0.03), 0, 0.5, 0.06, d, 0.42, mi_frame)          # arms (solid teak panel)
        for sy in (-1, 1):
            B(sx * (hw - 0.05), sy * (hd - 0.05), 0.15, 0.06, 0.06, 0.3, mi_frame)
    R(0, -0.03, 0.42, w - 0.14, d - 0.12, 0.14, mi_cushion, r=0.06, puff=0.5)      # seat cushion
    cw = (w - 0.14) / seats
    for i in range(seats):
        cx = -(w - 0.14) / 2 + cw * (i + 0.5)
        R(cx, hd - 0.16, 0.72, cw - 0.06, 0.16, 0.42, mi_cushion, r=0.07, puff=0.4)   # back cushions
    px, py = rot2(x - hw + 0.45, y + hd - 0.30, x, y, rot)
    mb.pillow(px, py, z + 0.66, 0.45, 0.45, 0.14, mi_cushion, rot=rot, tilt=0.5)
    px, py = rot2(x + hw - 0.45, y + hd - 0.30, x, y, rot)
    mb.pillow(px, py, z + 0.66, 0.45, 0.45, 0.14, mi_cushion, rot=rot + 0.15, tilt=0.5)
def pool_table(mb, x, y, z=0.0, rot=0.0, mi_wood=0, mi_felt=1, mi_ball=2, mi_cue=3):
    L, W, H = 2.54, 1.42, 0.82
    def B(cx, cy, cz, sx, sy, sz, mi_):
        px, py = rot2(x + cx, y + cy, x, y, rot)
        mb.cbox(px, py, z + cz, sx, sy, sz, mi_, rot)
    B(0, 0, H - 0.08, L, W, 0.16, mi_wood)                            # apron
    B(0, 0, H + 0.005, L - 0.28, W - 0.28, 0.01, mi_felt)             # bed
    B(0, W / 2 - 0.075, H + 0.03, L - 0.14, 0.15, 0.06, mi_wood)      # rails
    B(0, -W / 2 + 0.075, H + 0.03, L - 0.14, 0.15, 0.06, mi_wood)
    B(L / 2 - 0.075, 0, H + 0.03, 0.15, W, 0.06, mi_wood)
    B(-L / 2 + 0.075, 0, H + 0.03, 0.15, W, 0.06, mi_wood)
    for sx in (-1, 1):
        for sy in (-1, 1):
            B(sx * (L / 2 - 0.12), sy * (W / 2 - 0.12), (H - 0.16) / 2, 0.16, 0.16, H - 0.16, mi_wood)
    rng = random.Random(4)
    for i in range(10):
        px, py = rot2(x + rng.uniform(-0.6, 0.9), y + rng.uniform(-0.45, 0.45), x, y, rot)
        mb.sphere((px, py, z + H + 0.04), 0.029, seg=10, rings=6, mi=mi_ball)
    p0 = rot2(x - 1.0, y - 0.3, x, y, rot); p1 = rot2(x + 0.4, y + 0.1, x, y, rot)
    mb.tube((p0[0], p0[1], z + H + 0.06), (p1[0], p1[1], z + H + 0.03), 0.015, 0.006, seg=6, mi=mi_cue)


def bathtub(mb, x, y, z, l=1.7, w=0.8, h=0.6, mi=0, rot=0.0):
    """Free-standing oval tub (shell of revolution, elliptical)."""
    prof = [(0, 0.02), (w * 0.35, 0.02), (w * 0.5, h * 0.35), (w * 0.5, h * 0.95), (w * 0.52, h), (w * 0.44, h), (w * 0.42, h * 0.3), (0, h * 0.28)]
    mb.lathe(x, y, z, prof, seg=32, mi=mi, ry=l / w)


def basin(mb, x, y, z, r=0.2, mi=0):
    mb.lathe(x, y, z, [(0, 0), (r * 0.7, 0), (r, 0.08), (r, 0.12), (r * 0.9, 0.12), (r * 0.6, 0.03), (0, 0.02)], seg=20, mi=mi)


def faucet(mb, x, y, z, h=0.28, mi=0, reach=0.16, dir=(0, 1)):
    mb.cylinder(x, y, z, z + h, 0.012, seg=8, mi=mi)
    mb.tube((x, y, z + h), (x + dir[0] * reach, y + dir[1] * reach, z + h), 0.012, 0.012, seg=8, mi=mi)
    mb.cylinder(x + dir[0] * reach, y + dir[1] * reach, z + h - 0.03, z + h, 0.012, seg=8, mi=mi)


def bike(mb, x, y, z, rot=0.0, mi=0, mi_red=1):
    """Peloton-style spin bike (silhouette)."""
    def B(cx, cy, cz, sx, sy, sz, mi_):
        px, py = rot2(x + cx, y + cy, x, y, rot)
        mb.cbox(px, py, z + cz, sx, sy, sz, mi_, rot)
    B(0, 0, 0.03, 0.55, 1.2, 0.06, mi)                # base rails
    B(0, 0, 0.35, 0.08, 0.9, 0.06, mi)                # frame beam
    B(0, -0.25, 0.4, 0.1, 0.5, 0.5, mi)               # flywheel housing
    B(0, 0.25, 0.55, 0.08, 0.08, 0.5, mi)             # seat post
    B(0, 0.25, 0.85, 0.28, 0.24, 0.06, mi_red)        # saddle
    B(0, -0.3, 0.75, 0.08, 0.08, 0.6, mi)             # handlebar post
    B(0, -0.35, 1.1, 0.55, 0.12, 0.05, mi)            # handlebars
    B(0, -0.45, 1.3, 0.5, 0.03, 0.3, mi)              # screen
    px, py = rot2(x, y - 0.25, x, y, rot)
    mb.cylinder(px, py, z + 0.15, z + 0.45, 0.22, seg=16, mi=mi_red)  # not a real wheel orientation, silhouette only


def sconce(mb, x, y, z, mi=0, h=1.2, along='X', out=0.05):
    """Vertical linear LED sconce projecting from a wall."""
    if along == 'X':
        mb.box(x - 0.02, x + 0.02, y - out, y, z - h / 2, z + h / 2, mi)
    else:
        mb.box(y - out, y, x - 0.02, x + 0.02, z - h / 2, z + h / 2, mi)


def cabinet_run(mb, x0, x1, y0, y1, z0, z1, mi=0, doors='X', n=None, gap=0.004, mi_gap=None):
    """Flat-panel cabinet run with door reveals (gap lines) along the front face."""
    mi_gap = mi if mi_gap is None else mi_gap
    mb.box(x0, x1, y0, y1, z0, z1, mi)
    L = (x1 - x0) if doors == 'X' else (y1 - y0)
    n = n or max(1, round(L / 0.6))
    for i in range(1, n):
        if doors == 'X':
            xx = x0 + L * i / n
            mb.box(xx - gap / 2, xx + gap / 2, y0 - 0.002, y0, z0, z1, mi_gap)
            mb.box(xx - gap / 2, xx + gap / 2, y1, y1 + 0.002, z0, z1, mi_gap)
        else:
            yy = y0 + L * i / n
            mb.box(x0 - 0.002, x0, yy - gap / 2, yy + gap / 2, z0, z1, mi_gap)
            mb.box(x1, x1 + 0.002, yy - gap / 2, yy + gap / 2, z0, z1, mi_gap)


def twin_sconce(mb,x,y,z,nx,ny,metal,glass):
    """Two upward opal shades on curved brass arms, round wall escutcheon."""
    tx,ty=-ny,nx
    mb.tube((x,y,z),(x+nx*.025,y+ny*.025,z),.065,.065,seg=24,mi=metal)
    for side in (-1,1):
        sx,sy=x+nx*.13+side*tx*.13,y+ny*.13+side*ty*.13
        mb.path_tube([(x+nx*.03,y+ny*.03,z),(x+nx*.10,y+ny*.10,z-.06),
                      (sx,sy,z-.02),(sx,sy,z+.075)],.010,seg=10,mi=metal)
        mb.lathe(sx,sy,z+.05,[(0,0),(.032,0),(.040,.018),(.027,.033),(.027,.048),(0,.048)],seg=20,mi=metal)
        mb.lathe(sx,sy,z+.09,[(.024,0),(.031,.01),(.059,.07),(.068,.105),(.063,.112),(.055,.077),(.025,.016)],seg=28,mi=glass)
