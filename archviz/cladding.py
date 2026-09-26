"""Suburban wall cladding built as real geometry: lap-siding courses with shadow lines, gable-triangle courses,
trim boards (corner boards, frieze bands, window casings).  House-agnostic; all positions come from the caller.

A wall face is described by `Face(along, b, out)`: the face lies in the plane y = b (along='X') or x = b (along='Y')
and its outward normal points toward `out` (+1 / -1) on the other axis.  Builders take local coordinates
(a = position along the wall, d = distance outward from the face plane, z = height).
"""
from .mesh import MB


class Face:
    def __init__(self, along, b, out):
        self.along, self.b, self.out = along, b, out

    def p(self, a, d, z):
        """Local (along, outward, height) -> world (x, y, z)."""
        if self.along == 'X':
            return (a, self.b + self.out * d, z)
        return (self.b + self.out * d, a, z)

    def box(self, mb, a0, a1, d0, d1, z0, z1, mi=0):
        (x0, y0, _), (x1, y1, _) = self.p(a0, d0, 0), self.p(a1, d1, 0)
        mb.box(min(x0, x1), max(x0, x1), min(y0, y1), max(y0, y1), z0, z1, mi)

    def quad8(self, mb, pts, mi=0):
        """Hexahedron from 8 local points (4 bottom CCW, 4 top)."""
        mb.hexa([self.p(*q) for q in pts], mi)


def _free_spans(a0, a1, blocks):
    """[a0, a1] minus the union of the (b0, b1) blocks."""
    spans, cur = [], a0
    for b0, b1 in sorted(blocks):
        if b1 <= cur or b0 >= a1:
            continue
        if b0 > cur:
            spans.append((cur, b0))
        cur = max(cur, b1)
    if cur < a1:
        spans.append((cur, a1))
    return [(s0, s1) for s0, s1 in spans if s1 - s0 > 0.004]


def lap_siding(mb, face, a0, a1, z0, z1, holes=(), exposure=0.19, butt=0.022, tip=0.006, mi=0, top_clip=None, start=None,
               fit_holes=False):
    """Horizontal lap siding from z0 to z1 between a0 and a1 on `face`.  Each course is a wedge (thick butt edge at
    the bottom, thin under the course above) so raking light draws a shadow line every `exposure`.  `holes` are
    (ha0, ha1, hz0, hz1) rectangles (openings plus their trim) that cut the courses.  `top_clip(a) -> z` optionally
    limits the top (a gable rake); courses are then trapezoids following it.  `fit_holes` = True keeps the parts of a
    cut course above / below a hole (the siding then meets a narrow J-channel instead of leaving a gap up to one
    course high); the default cuts whole courses, as a wide casing would hide."""
    import math as _m
    z = z0 if start is None else start + _m.floor((z0 - start) / exposure + 1e-6) * exposure
    k = 0
    while z < z1 - 1e-4:
        zb, zt = max(z, z0), min(z + exposure, z1)
        if fit_holes and top_clip is None:
            for (h0, h1, hz0, hz1) in holes:
                if not (hz0 < zt - 1e-4 and hz1 > zb + 1e-4):
                    continue
                s0, s1 = max(h0, a0), min(h1, a1)
                if s1 - s0 < 0.004:
                    continue
                if hz1 < zt - 0.004:                 # the part of the course above the hole (thin: the butt is below)
                    t = (hz1 - zb) / (zt - zb)
                    db = butt + (tip - butt) * t
                    face.quad8(mb, [(s0, 0, hz1), (s1, 0, hz1), (s1, db, hz1), (s0, db, hz1),
                                    (s0, 0, zt), (s1, 0, zt), (s1, tip, zt), (s0, tip, zt)], mi)
                if hz0 > zb + 0.004:                 # the part below the hole (keeps the butt edge)
                    t = (hz0 - zb) / (zt - zb)
                    dt = butt + (tip - butt) * t
                    face.quad8(mb, [(s0, 0, zb), (s1, 0, zb), (s1, butt, zb), (s0, butt, zb),
                                    (s0, 0, hz0), (s1, 0, hz0), (s1, dt, hz0), (s0, dt, hz0)], mi)
        blocks = [(h0, h1) for (h0, h1, hz0, hz1) in holes if hz0 < zt - 1e-4 and hz1 > zb + 1e-4]
        for s0, s1 in _free_spans(a0, a1, blocks):
            if top_clip is None:
                face.quad8(mb, [(s0, 0, zb), (s1, 0, zb), (s1, butt, zb), (s0, butt, zb),
                                (s0, 0, zt), (s1, 0, zt), (s1, tip, zt), (s0, tip, zt)], mi)
            else:
                # clip the course to the rake line: the course is cut along the rake in n segments (a course that
                # crosses the apex keeps its flat top between the two rakes; a course the rake enters mid-span starts
                # where the rake crosses its bottom)
                n = 24
                prof = []
                for i in range(n):
                    pa, pb = s0 + (s1 - s0) * i / n, s0 + (s1 - s0) * (i + 1) / n
                    ta, tb = top_clip(pa) - zb, top_clip(pb) - zb
                    if ta <= 0.004 and tb <= 0.004:
                        continue
                    if ta <= 0.004:
                        pa = pa + (pb - pa) * (0.004 - ta) / (tb - ta)
                    if tb <= 0.004:
                        pb = pa + (pb - pa) * (ta - 0.004) / (ta - tb)
                    za, zc = min(zt, top_clip(pa)), min(zt, top_clip(pb))
                    if prof and abs(prof[-1][1] - pa) < 1e-6 and prof[-1][2] >= zt - 1e-6 and za >= zt - 1e-6 and zc >= zt - 1e-6:
                        prof[-1] = (prof[-1][0], pb, zt, zt)          # merge flat runs
                        continue
                    prof.append((pa, pb, za, zc))
                for (c0, c1, zt0, zt1) in prof:
                    face.quad8(mb, [(c0, 0, zb), (c1, 0, zb), (c1, butt, zb), (c0, butt, zb),
                                    (c0, 0, zt0), (c1, 0, zt1), (c1, tip, zt1), (c0, tip, zt0)], mi)
        z += exposure
        k += 1
    return k


def casing(mb, face, a0, a1, z0, z1, w=0.09, t=0.028, mi=0, sill=True, head_extra=0.0):
    """Flat exterior window / door trim around an opening (proud of the siding)."""
    face.box(mb, a0 - w, a0, 0, t, z0 - (w if sill else 0), z1 + w + head_extra, mi)
    face.box(mb, a1, a1 + w, 0, t, z0 - (w if sill else 0), z1 + w + head_extra, mi)
    face.box(mb, a0 - w, a1 + w, 0, t, z1, z1 + w + head_extra, mi)
    if sill:
        face.box(mb, a0 - w - 0.02, a1 + w + 0.02, 0, t + 0.03, z0 - w, z0, mi)


def j_channel(mb, face, a0, a1, z0, z1, w=0.022, t=0.016, lip=0.006, mi=0, sill=True):
    """Vinyl J-channel around an opening in lap siding: a narrow white frame (w wide, t proud of the sheathing) with a
    returned lip, instead of a flat casing.  `sill=False` leaves the bottom open (doors)."""
    face.box(mb, a0 - w, a0, 0, t, z0 - (w if sill else 0), z1 + w, mi)
    face.box(mb, a1, a1 + w, 0, t, z0 - (w if sill else 0), z1 + w, mi)
    face.box(mb, a0 - w, a1 + w, 0, t, z1, z1 + w, mi)
    face.box(mb, a0 - w, a0 - w + lip, t, t + 0.006, z0 - (w if sill else 0), z1 + w, mi)
    face.box(mb, a1 + w - lip, a1 + w, t, t + 0.006, z0 - (w if sill else 0), z1 + w, mi)
    face.box(mb, a0 - w, a1 + w, t, t + 0.006, z1 + w - lip, z1 + w, mi)
    if sill:
        face.box(mb, a0 - w, a1 + w, 0, t, z0 - w, z0, mi)


def corner_board(mb, face, a, z0, z1, w=0.1, t=0.028, side=+1, mi=0):
    """Vertical outside-corner trim at position a (extends toward `side` along the wall)."""
    a0, a1 = (a, a + side * w) if side > 0 else (a + side * w, a)
    face.box(mb, a0, a1, 0, t, z0, z1, mi)


def band(mb, face, a0, a1, z0, z1, t=0.028, mi=0):
    """Horizontal trim band (frieze board under the soffit, water table)."""
    face.box(mb, a0, a1, 0, t, z0, z1, mi)


def holed_wall(mb, along, a0, a1, b0, b1, z0, z1, holes=(), mi=0):
    """Wall slab with any number of rectangular holes (ha0, ha1, hz0, hz1), including holes stacked above one
    another in the same span (MB.wall assumes holes do not overlap along the wall).  The solid is decomposed on the
    grid of hole edges; kept cells are merged vertically per column."""
    hs = [(max(h0, a0), min(h1, a1), max(hz0, z0), min(hz1, z1)) for (h0, h1, hz0, hz1) in holes
          if h1 > a0 and h0 < a1 and hz1 > z0 and hz0 < z1]
    av = sorted({a0, a1, *[h[0] for h in hs], *[h[1] for h in hs]})
    zv = sorted({z0, z1, *[h[2] for h in hs], *[h[3] for h in hs]})
    def solid(ac, zc):
        return not any(h[0] < ac < h[1] and h[2] < zc < h[3] for h in hs)
    for i in range(len(av) - 1):
        ca, cb = av[i], av[i + 1]
        if cb - ca < 1e-6:
            continue
        am = (ca + cb) / 2
        run = None
        for j in range(len(zv) - 1):
            za, zb = zv[j], zv[j + 1]
            if zb - za < 1e-6:
                continue
            if solid(am, (za + zb) / 2):
                run = (run[0], zb) if run else (za, zb)
            elif run:
                _wall_box(mb, along, ca, cb, b0, b1, run[0], run[1], mi)
                run = None
        if run:
            _wall_box(mb, along, ca, cb, b0, b1, run[0], run[1], mi)


def _wall_box(mb, along, a0, a1, b0, b1, z0, z1, mi):
    if along == 'X':
        mb.box(a0, a1, b0, b1, z0, z1, mi)
    else:
        mb.box(b0, b1, a0, a1, z0, z1, mi)
