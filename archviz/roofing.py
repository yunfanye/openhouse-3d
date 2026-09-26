"""Pitched roofs from planar shingle slabs, with fascia, soffits, rake boards, gutters and downspouts.

Each roof plane is its own object whose LOCAL frame is aligned with the plane (local X along the eave, local Y up the
slope, local Z = the outward normal), so object-space shingle materials (`materials.shingles`) course correctly on
every slope without UVs.  Intersecting planes (cross gables, valleys) are simply allowed to overlap: the visible
surface is their union, which is exactly a valley.  Hips (convex corners) need clipped polygons: pass `poly`.

House-agnostic: coordinates, pitches and extents come from the caller.
"""
import math
from mathutils import Matrix, Vector
from .mesh import MB


def plane(name, mats, origin, u, v, poly, thick=0.10, coll='House'):
    """Slab under the surface through `origin` spanned by unit vectors u (horizontal, along the eave) and v (up the
    slope).  `poly` = CCW 2D polygon in (u, v) metres measured on the slope."""
    u, v = Vector(u).normalized(), Vector(v).normalized()
    n = u.cross(v).normalized()
    mb = MB()
    mb.prism(poly, -thick, 0.0)
    ob = mb.build(name, mats, coll)
    M = Matrix.Identity(4)
    for i in range(3):
        M[i][0], M[i][1], M[i][2], M[i][3] = u[i], v[i], n[i], origin[i]
    ob.matrix_world = M
    return ob


def slope_frame(eave_dir, up_dir, pitch):
    """(u, v) for a slope whose eave runs along `eave_dir` (2D, horizontal) and which rises toward `up_dir` (2D)."""
    k = math.hypot(1.0, pitch)
    u = Vector((eave_dir[0], eave_dir[1], 0.0)).normalized()
    v = Vector((up_dir[0] / k, up_dir[1] / k, pitch / k))
    if u.cross(v).z < 0:
        u = -u
    return u, v


def slope(name, mats, eave_pt, eave_dir, up_dir, pitch, plan_pts, thick=0.10, coll='House'):
    """A roof slope whose top surface contains the eave line through `eave_pt` = (x, y, z) running along `eave_dir`
    and rising toward `up_dir` at `pitch`.  `plan_pts` = CCW-or-CW plan polygon (x, y) of the slope's outline."""
    u, v = slope_frame(eave_dir, up_dir, pitch)
    k = math.hypot(1.0, pitch)
    uh = Vector((u[0], u[1]))
    vh = Vector((up_dir[0], up_dir[1])).normalized()
    poly = []
    for (x, y) in plan_pts:
        d = Vector((x - eave_pt[0], y - eave_pt[1]))
        poly.append((d.dot(uh), d.dot(vh) * k))
    # CCW in (u, v)
    area = sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly)))
    if area < 0:
        poly.reverse()
    return plane(name, mats, eave_pt, u, v, poly, thick, coll)


def height(eave_pt, up_dir, pitch, x, y):
    """Top-surface height of a slope at plan point (x, y)."""
    vh = Vector((up_dir[0], up_dir[1])).normalized()
    return eave_pt[2] + Vector((x - eave_pt[0], y - eave_pt[1])).dot(vh) * pitch


# ---------------------------------------------------------------- trims (added to an MB, caller builds)
def fascia_run(mb, p0, p1, z_top, out, depth=0.19, t=0.028, mi=0):
    """Vertical fascia board along the plan segment p0 -> p1 (horizontal eave), outer face offset toward `out`
    (a 2D unit vector), top at z_top."""
    _slab_along(mb, p0, p1, out, 0.0, t, z_top - depth, z_top, mi)


def soffit_run(mb, p0, p1, out, width, z, t=0.015, mi=0):
    """Horizontal soffit panel from the wall line (p0 -> p1) outward by `width`, underside at z."""
    _slab_along(mb, p0, p1, out, -width, 0.0, z, z + t, mi, from_outer=True)


def _slab_along(mb, p0, p1, out, d0, d1, z0, z1, mi, from_outer=False):
    p0, p1 = Vector(p0), Vector(p1)
    o = Vector(out).normalized()
    if from_outer:
        a0, a1 = p0 + o * (-d0), p1 + o * (-d0)
        b0, b1 = p0, p1
    else:
        a0, a1 = p0 + o * d0, p1 + o * d0
        b0, b1 = p0 + o * d1, p1 + o * d1
    mb.hexa([(a0.x, a0.y, z0), (a1.x, a1.y, z0), (b1.x, b1.y, z0), (b0.x, b0.y, z0),
             (a0.x, a0.y, z1), (a1.x, a1.y, z1), (b1.x, b1.y, z1), (b0.x, b0.y, z1)], mi)


def gutter(mb, p0, p1, z_top, out, w=0.125, h=0.12, mi=0):
    """K-style gutter hung on the fascia: outer face + bottom + a rolled front lip; end caps."""
    p0, p1 = Vector(p0), Vector(p1)
    o = Vector(out).normalized()
    tdir = (p1 - p0).normalized()
    def seg(d0, d1, z0, z1):
        a0, a1 = p0 + o * d0, p1 + o * d0
        b0, b1 = p0 + o * d1, p1 + o * d1
        mb.hexa([(a0.x, a0.y, z0), (a1.x, a1.y, z0), (b1.x, b1.y, z0), (b0.x, b0.y, z0),
                 (a0.x, a0.y, z1), (a1.x, a1.y, z1), (b1.x, b1.y, z1), (b0.x, b0.y, z1)], mi)
    zb = z_top - h
    seg(0.0, w, zb, zb + 0.012)                      # bottom
    seg(w - 0.012, w, zb, z_top - 0.035)             # front face (ogee simplified: a step + lip)
    seg(w - 0.028, w + 0.004, z_top - 0.035, z_top - 0.02)
    seg(w - 0.012, w, z_top - 0.02, z_top)
    for pe, sgn in ((p0, 1), (p1, -1)):              # end caps
        c0 = pe + tdir * (0.0 if sgn > 0 else -0.01)
        c1 = c0 + tdir * 0.01
        mb.hexa([(c0.x, c0.y, zb), (c1.x, c1.y, zb), ((c1 + o * w).x, (c1 + o * w).y, zb), ((c0 + o * w).x, (c0 + o * w).y, zb),
                 (c0.x, c0.y, z_top - 0.01), (c1.x, c1.y, z_top - 0.01), ((c1 + o * w).x, (c1 + o * w).y, z_top - 0.01), ((c0 + o * w).x, (c0 + o * w).y, z_top - 0.01)], mi)


def downspout(mb, x, y, z0, z1, out=(0, -1), mi=0, w=0.075, d=0.055, kick=0.25, elbow=True):
    """Rectangular downspout on a wall at (x, y) from gutter height z1 down to z0, kicking out at the bottom."""
    o = Vector(out).normalized()
    c = Vector((x, y)) + o * (d / 2 + 0.02)
    t = Vector((-o.y, o.x))
    def rect(cc, za, zb, ww, dd):
        p = [cc + t * (-ww / 2) + o * (-dd / 2), cc + t * (ww / 2) + o * (-dd / 2), cc + t * (ww / 2) + o * (dd / 2), cc + t * (-ww / 2) + o * (dd / 2)]
        mb.hexa([(q.x, q.y, za) for q in p] + [(q.x, q.y, zb) for q in p], mi)
    rect(c, z0 + (0.12 if elbow else 0.0), z1, w, d)
    if elbow:
        rect(c + o * (kick / 2), z0 + 0.02, z0 + 0.12, w, kick + d)
    for zz in (z0 + 0.6, (z0 + z1) / 2, z1 - 0.3):                      # straps
        rect(c, zz, zz + 0.025, w + 0.012, d + 0.012)


def rake_board(mb, p_low, p_high, z_low, z_high, out, depth=0.2, t=0.028, mi=0):
    """Sloped fascia along a gable rake from (p_low, z_low) up to (p_high, z_high) (tops of the board)."""
    o = Vector(out).normalized()
    a0, a1 = Vector(p_low), Vector(p_high)
    b0, b1 = a0 + o * t, a1 + o * t
    mb.hexa([(a0.x, a0.y, z_low - depth), (a1.x, a1.y, z_high - depth), (b1.x, b1.y, z_high - depth), (b0.x, b0.y, z_low - depth),
             (a0.x, a0.y, z_low), (a1.x, a1.y, z_high), (b1.x, b1.y, z_high), (b0.x, b0.y, z_low)], mi)


def ridge_cap(mb, p0, p1, z, w=0.16, h=0.035, mi=0):
    """Low ridge-vent / cap shingles along a ridge line at height z."""
    p0, p1 = Vector(p0), Vector(p1)
    tdir = (p1 - p0).normalized()
    o = Vector((-tdir.y, tdir.x))
    q = [p0 - o * w / 2, p1 - o * w / 2, p1 + o * w / 2, p0 + o * w / 2]
    mb.hexa([(v.x, v.y, z - 0.02) for v in q] + [(q[0].x, q[0].y, z + h * 0.4), (q[1].x, q[1].y, z + h * 0.4),
                                                  (q[2].x, q[2].y, z + h * 0.4), (q[3].x, q[3].y, z + h * 0.4)], mi)
    mb.hexa([((p0 - o * w * 0.3).x, (p0 - o * w * 0.3).y, z), ((p1 - o * w * 0.3).x, (p1 - o * w * 0.3).y, z),
             ((p1 + o * w * 0.3).x, (p1 + o * w * 0.3).y, z), ((p0 + o * w * 0.3).x, (p0 + o * w * 0.3).y, z),
             ((p0 - o * w * 0.3).x, (p0 - o * w * 0.3).y, z + h), ((p1 - o * w * 0.3).x, (p1 - o * w * 0.3).y, z + h),
             ((p1 + o * w * 0.3).x, (p1 + o * w * 0.3).y, z + h), ((p0 + o * w * 0.3).x, (p0 + o * w * 0.3).y, z + h)], mi)
