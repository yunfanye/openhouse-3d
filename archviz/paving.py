"""Hardscape and garden-bed helpers: smooth outlines, concrete pavers laid in European fans with inset circle kits,
river-rock beds made of real pebbles, landscape edging strips (plastic or brick) along a polyline.

All functions are house-independent.  Materials use Object coordinates, so build the meshes in world coordinates
with the object at the origin (what archviz.mesh.MB does).
"""
import math
import random

import bpy

from .materials import _new, _math, _set, _noise, _bump, _mixrgb
from .mesh import MB


# ------------------------------------------------------------------ outlines
def catmull_loop(pts, n=6, closed=True):
    """Catmull-Rom spline through pts (n samples per span).  Open curves keep their end points."""
    m = len(pts)
    out = []
    spans = m if closed else m - 1
    for i in range(spans):
        p0 = pts[(i - 1) % m] if closed or i > 0 else pts[0]
        p1 = pts[i % m]
        p2 = pts[(i + 1) % m]
        p3 = pts[(i + 2) % m] if closed or i + 2 < m else pts[-1]
        for k in range(n):
            t = k / n
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t * t
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t ** 3) for j in range(2)))
    if not closed:
        out.append(tuple(pts[-1]))
    return out


def point_in_poly(x, y, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        (ax, ay), (bx, by) = poly[i], poly[(i + 1) % n]
        if (ay > y) != (by > y) and x < (bx - ax) * (y - ay) / (by - ay + 1e-12) + ax:
            inside = not inside
    return inside


def dist_to_polyline(x, y, pts, closed=True):
    best = 1e9
    n = len(pts)
    for i in range(n if closed else n - 1):
        (ax, ay), (bx, by) = pts[i], pts[(i + 1) % n]
        vx, vy = bx - ax, by - ay
        t = max(0.0, min(1.0, ((x - ax) * vx + (y - ay) * vy) / (vx * vx + vy * vy + 1e-12)))
        best = min(best, math.hypot(x - ax - vx * t, y - ay - vy * t))
    return best


def signed_area(pts):
    return 0.5 * sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))


def ccw(pts):
    return list(pts) if signed_area(pts) > 0 else list(reversed(pts))


# ------------------------------------------------------------------ pavers
def _sock(nt, v):
    return v


def _fan_cell(nt, X, Y, W, H, R):
    """European fan: fan centres on a staggered lattice (row pitch H, spacing W), each fan the upper part of a disk
    of radius R; a point belongs to the LOWEST row whose disk contains it.  Returns (d, dx, dy) sockets relative to
    the chosen fan centre."""
    r1 = _math(nt, 'FLOOR', _math(nt, 'DIVIDE', Y, H))
    D = DX = DY = None
    found = None
    for k in (-1.0, 0.0, 1.0):
        r = _math(nt, 'ADD', r1, k)
        off = _math(nt, 'MULTIPLY', _math(nt, 'FLOORED_MODULO', r, 2.0), W / 2)
        xc = _math(nt, 'ADD', _math(nt, 'MULTIPLY', _math(nt, 'ROUND', _math(nt, 'DIVIDE', _math(nt, 'SUBTRACT', X, off), W)), W), off)
        dx = _math(nt, 'SUBTRACT', X, xc)
        dy = _math(nt, 'SUBTRACT', Y, _math(nt, 'MULTIPLY', r, H))
        d = _math(nt, 'SQRT', _math(nt, 'ADD', _math(nt, 'MULTIPLY', dx, dx), _math(nt, 'MULTIPLY', dy, dy)))
        hit = _math(nt, 'LESS_THAN', d, R)
        take = hit if found is None else _math(nt, 'MULTIPLY', hit, _math(nt, 'SUBTRACT', 1.0, found))
        if D is None:
            D, DX, DY, found = _math(nt, 'MULTIPLY', take, d), _math(nt, 'MULTIPLY', take, dx), _math(nt, 'MULTIPLY', take, dy), take
        else:
            D = _math(nt, 'ADD', D, _math(nt, 'MULTIPLY', take, d))
            DX = _math(nt, 'ADD', DX, _math(nt, 'MULTIPLY', take, dx))
            DY = _math(nt, 'ADD', DY, _math(nt, 'MULTIPLY', take, dy))
            found = _math(nt, 'ADD', found, take)
    return D, DX, DY


def fan_circle_pavers(name, circles=(), fan_width=1.30, fan_origin=(0.0, 0.0), fan_angle=0.0, ring=0.13, length=0.15,
                      base=(0.30, 0.26, 0.23, 1), alt=(0.38, 0.33, 0.29, 1), joint=(0.16, 0.15, 0.13, 1), rough=0.85,
                      mottle=0.35, bump=0.5):
    """Tumbled concrete cobbles laid in a European fan pattern (fans `fan_width` wide, rows W/2 apart, fan radius
    W/sqrt2, opening toward +v of the fan frame rotated by fan_angle about fan_origin) with circle kits inset:
    circles = [(cx, cy, R), ...] (object XY; earlier circles win where they overlap).  Pavers are `ring` wide
    (radially) and ~`length` long along each ring, joints staggered ring to ring."""
    m, nt, b = _new(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(sep.inputs["Vector"], tc.outputs["Object"])
    X0 = _math(nt, 'SUBTRACT', sep.outputs["X"], fan_origin[0])
    Y0 = _math(nt, 'SUBTRACT', sep.outputs["Y"], fan_origin[1])
    ca, sa = math.cos(fan_angle), math.sin(fan_angle)
    U = _math(nt, 'ADD', _math(nt, 'MULTIPLY', X0, ca), _math(nt, 'MULTIPLY', Y0, sa))
    V = _math(nt, 'SUBTRACT', _math(nt, 'MULTIPLY', Y0, ca), _math(nt, 'MULTIPLY', X0, sa))
    W = fan_width
    D, DX, DY = _fan_cell(nt, U, V, W, W / 2, W / math.sqrt(2))
    ARC = _math(nt, 'MULTIPLY', _math(nt, 'ARCTAN2', DX, DY), D)
    for (cx, cy, R) in reversed(list(circles)):            # first circle applied last = wins
        dx = _math(nt, 'SUBTRACT', sep.outputs["X"], cx)
        dy = _math(nt, 'SUBTRACT', sep.outputs["Y"], cy)
        d = _math(nt, 'SQRT', _math(nt, 'ADD', _math(nt, 'MULTIPLY', dx, dx), _math(nt, 'MULTIPLY', dy, dy)))
        arc = _math(nt, 'MULTIPLY', _math(nt, 'ARCTAN2', dy, dx), d)
        inside = _math(nt, 'LESS_THAN', d, R)
        D = _math(nt, 'ADD', _math(nt, 'MULTIPLY', inside, d), _math(nt, 'MULTIPLY', _math(nt, 'SUBTRACT', 1.0, inside), D))
        ARC = _math(nt, 'ADD', _math(nt, 'MULTIPLY', inside, arc), _math(nt, 'MULTIPLY', _math(nt, 'SUBTRACT', 1.0, inside), ARC))
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(comb.inputs["X"], ARC); nt.links.new(comb.inputs["Y"], D)
    br = nt.nodes.new("ShaderNodeTexBrick")
    br.offset = 0.5; br.offset_frequency = 2
    br.squash = 1.0; br.squash_frequency = 2
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Mortar Size"].default_value = 0.009
    br.inputs["Mortar Smooth"].default_value = 0.55
    br.inputs["Bias"].default_value = 0.0
    br.inputs["Brick Width"].default_value = length
    br.inputs["Row Height"].default_value = ring
    br.inputs["Color1"].default_value = base; br.inputs["Color2"].default_value = alt
    br.inputs["Mortar"].default_value = joint
    nt.links.new(br.inputs["Vector"], comb.outputs["Vector"])
    n = _noise(nt, tc.outputs["Object"], scale=9.0, detail=4.0)
    n2 = _noise(nt, tc.outputs["Object"], scale=0.6, detail=2.0)
    col = _mixrgb(nt, _math(nt, 'MULTIPLY', n, mottle), br.outputs["Color"], (0.78, 0.76, 0.74, 1), 'MULTIPLY')
    col = _mixrgb(nt, _math(nt, 'MULTIPLY', n2, 0.35), col, (0.86, 0.84, 0.82, 1), 'MULTIPLY')
    nt.links.new(b.inputs["Base Color"], col)
    _set(b, "Roughness", rough); _set(b, "Specular IOR Level", 0.3)
    _bump(nt, b, _math(nt, 'ADD', _math(nt, 'SUBTRACT', 1.0, br.outputs["Fac"]), _math(nt, 'MULTIPLY', n, 0.25)), bump, 0.008)
    return m


# ------------------------------------------------------------------ river rock
def pebble_material(name, colours=((0.62, 0.58, 0.52, 1), (0.74, 0.71, 0.66, 1), (0.52, 0.44, 0.36, 1), (0.40, 0.38, 0.36, 1),
                                   (0.66, 0.54, 0.46, 1)), rough=0.55, attr="pebble_rnd"):
    """Rounded river pebbles: each pebble picks one of `colours` from its face attribute `attr` (0..1), plus fine
    speckle and a slight sheen."""
    m, nt, b = _new(name)
    at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_type = 'GEOMETRY'; at.attribute_name = attr
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    cr = ramp.color_ramp
    cr.interpolation = 'CONSTANT'
    k = len(colours)
    while len(cr.elements) < k:
        cr.elements.new(0.5)
    for i, (e, c) in enumerate(zip(cr.elements, colours)):
        e.position = i / k; e.color = c
    nt.links.new(ramp.inputs["Fac"], at.outputs["Fac"])
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sp = _noise(nt, tc.outputs["Object"], scale=160.0, detail=2.0)
    col = _mixrgb(nt, _math(nt, 'MULTIPLY', sp, 0.35), ramp.outputs["Color"], (0.8, 0.78, 0.76, 1), 'MULTIPLY')
    nt.links.new(b.inputs["Base Color"], col)
    _set(b, "Roughness", rough); _set(b, "Specular IOR Level", 0.4)
    _bump(nt, b, sp, 0.15, 0.003)
    return m


def pebble_bed(name, inside, bbox, z_fn, mat, spacing=0.055, r=(0.018, 0.040), seed=0, coll='Site', layers=1,
               base_mat=None, base_poly=None, base_holes=()):
    """Scatter low-poly pebbles (squashed, jittered 6x4 spheres) over the region where inside(x, y) is true within
    bbox = (x0, x1, y0, y1), resting on z_fn(x, y).  Each pebble carries a random face attribute `pebble_rnd` for
    pebble_material().  Optionally a flat base slab (base_poly, same material or base_mat) fills the gaps."""
    rng = random.Random(seed)
    mb = MB()
    rnd = []
    x0, x1, y0, y1 = bbox
    for layer in range(layers):
        nx, ny = int((x1 - x0) / spacing) + 1, int((y1 - y0) / spacing) + 1
        for i in range(nx):
            for j in range(ny):
                x = x0 + (i + rng.random()) * spacing
                y = y0 + (j + rng.random()) * spacing
                if not inside(x, y):
                    continue
                rr = rng.uniform(*r)
                rx, ry = rr * rng.uniform(0.75, 1.25), rr * rng.uniform(0.7, 1.1)
                sq = rng.uniform(0.40, 0.65)
                rot = rng.uniform(0, math.pi)
                z = z_fn(x, y) + rr * sq * 0.35 + layer * 0.01
                seg, rings = 6, 4
                c, s = math.cos(rot), math.sin(rot)
                vs, fs = [], []
                for jr in range(rings + 1):
                    th = math.pi * jr / rings
                    for ip in range(seg):
                        ph = 2 * math.pi * ip / seg + (0.5 if jr % 2 else 0.0) * math.pi / seg
                        ex, ey, ez = math.sin(th) * math.cos(ph) * rx, math.sin(th) * math.sin(ph) * ry, math.cos(th) * rr * sq
                        j2 = 1.0 + rng.uniform(-0.12, 0.12)
                        vs.append((x + (ex * c - ey * s) * j2, y + (ex * s + ey * c) * j2, z + ez))
                for jr in range(rings):
                    for ip in range(seg):
                        a = jr * seg + ip
                        bq = jr * seg + (ip + 1) % seg
                        c2 = (jr + 1) * seg + (ip + 1) % seg
                        d = (jr + 1) * seg + ip
                        fs.append((a, bq, c2, d))
                mb._add(vs, fs, 0)
                val = rng.random()
                rnd.extend([val] * len(fs))
    ob = mb.build(name, [mat], coll=coll, smooth=True, recalc=True, auto_smooth=False)
    if rnd:
        at = ob.data.attributes.new("pebble_rnd", 'FLOAT', 'FACE')
        at.data.foreach_set("value", rnd)
    if base_poly:
        bm = MB()
        pts = ccw(base_poly)
        n = len(pts)
        vs = [(x, y, z_fn(x, y)) for (x, y) in pts]
        bm._add(vs, [tuple(range(n))], 0)
        bo = bm.build(name + "_Base", [base_mat or mat], coll=coll)
        at = bo.data.attributes.new("pebble_rnd", 'FLOAT', 'FACE')
        at.data.foreach_set("value", [0.5] * len(bo.data.polygons))
    return ob


# ------------------------------------------------------------------ edging
def edging_strip(mb, pts, width, z_bot, z_top, closed=False, mi=0, block=None, gap=0.006, side=0.0):
    """A strip of `width` centred on the polyline pts (offset sideways by `side`), from z_bot to z_top (numbers or
    functions of (x, y)).  block = segment length for brick / paver edging (small joints), None for a continuous
    plastic or steel strip."""
    zb = z_bot if callable(z_bot) else (lambda x, y, v=z_bot: v)
    zt = z_top if callable(z_top) else (lambda x, y, v=z_top: v)
    P = list(pts) + ([pts[0]] if closed else [])
    # resample
    seq = [P[0]]
    step = block if block else 0.25
    for (a, bq) in zip(P[:-1], P[1:]):
        L = math.hypot(bq[0] - a[0], bq[1] - a[1])
        k = max(1, int(math.ceil(L / step)))
        for i in range(1, k + 1):
            seq.append((a[0] + (bq[0] - a[0]) * i / k, a[1] + (bq[1] - a[1]) * i / k))
    for i in range(len(seq) - 1):
        a, bq = seq[i], seq[i + 1]
        dx, dy = bq[0] - a[0], bq[1] - a[1]
        L = math.hypot(dx, dy) or 1e-6
        nx, ny = -dy / L, dx / L
        ux, uy = dx / L, dy / L
        g = gap / 2 if block else 0.0
        a2 = (a[0] + ux * g + nx * side, a[1] + uy * g + ny * side)
        b2 = (bq[0] - ux * g + nx * side, bq[1] - uy * g + ny * side)
        h = width / 2
        q = [(a2[0] - nx * h, a2[1] - ny * h), (b2[0] - nx * h, b2[1] - ny * h), (b2[0] + nx * h, b2[1] + ny * h), (a2[0] + nx * h, a2[1] + ny * h)]
        mb.hexa([(x, y, zb(x, y)) for x, y in q] + [(x, y, zt(x, y)) for x, y in q], mi)
    return mb
