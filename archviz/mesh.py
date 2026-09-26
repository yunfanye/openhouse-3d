"""Mesh builder + scene helpers shared by every house (Blender 5.x bpy, no GUI).

`MB` accumulates boxes / walls-with-holes / plates / prisms / lathes / sweeps / rounded boxes / pillows / blobs into
ONE mesh with per-face material indices and turns it into an object with `build()` (optional smooth shading, bevel,
subsurf, auto-smooth).  `collection()` links objects into named collections, `look_at()` aims cameras and lights.

Everything here is house-agnostic: coordinates are whatever the house's plan.py says they are (metres, Z up).
"""
import bpy, bmesh, math, random
from mathutils import Vector, noise

COLL = {}


def collection(name):
    if name in COLL:
        return COLL[name]
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(c)
    COLL[name] = c
    return c


# ------------------------------------------------------------------ mesh builder
class MB:
    """Accumulates boxes / prisms / sweeps into one mesh with per-face material indices."""

    def __init__(self):
        self.v, self.f, self.fm = [], [], []

    def _add(self, verts, faces, mi):
        b = len(self.v)
        self.v.extend(tuple(v) for v in verts)
        self.f.extend([tuple(b + i for i in fc) for fc in faces])
        self.fm.extend([mi] * len(faces))

    # -- boxes -------------------------------------------------------------
    def box(self, x0, x1, y0, y1, z0, z1, mi=0):
        if x1 < x0: x0, x1 = x1, x0
        if y1 < y0: y0, y1 = y1, y0
        if z1 < z0: z0, z1 = z1, z0
        if x1 - x0 < 1e-7 or y1 - y0 < 1e-7 or z1 - z0 < 1e-7:
            return
        vs = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
              (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        fs = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        self._add(vs, fs, mi)

    def cbox(self, cx, cy, cz, sx, sy, sz, mi=0, rot=0.0):
        """Box centred at (cx,cy,cz) with size (sx,sy,sz), optionally rotated about Z (radians)."""
        hx, hy, hz = sx / 2, sy / 2, sz / 2
        c, s = math.cos(rot), math.sin(rot)
        vs = []
        for dz in (-hz, hz):
            for dx, dy in ((-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)):
                vs.append((cx + dx * c - dy * s, cy + dx * s + dy * c, cz + dz))
        fs = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        self._add(vs, fs, mi)

    def hexa(self, vs, mi=0):
        """Arbitrary hexahedron; vs = 8 verts (4 bottom CCW, then 4 top)."""
        fs = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        self._add(vs, fs, mi)

    def wall(self, along, a0, a1, b0, b1, z0, z1, holes=(), mi=0):
        """Wall along 'X' (a=x, b=y) or 'Y' (a=y, b=x) with rectangular holes
        (ha0, ha1, hz0, hz1), non-overlapping in `a`."""
        def bx(aa0, aa1, zz0, zz1):
            if aa1 - aa0 < 1e-6 or zz1 - zz0 < 1e-6:
                return
            if along == 'X':
                self.box(aa0, aa1, b0, b1, zz0, zz1, mi)
            else:
                self.box(b0, b1, aa0, aa1, zz0, zz1, mi)
        cur = a0
        for (ha0, ha1, hz0, hz1) in sorted(holes):
            bx(cur, ha0, z0, z1)
            bx(ha0, ha1, z0, hz0)
            bx(ha0, ha1, hz1, z1)
            cur = ha1
        bx(cur, a1, z0, z1)

    def plate(self, x0, x1, y0, y1, z0, z1, holes=(), mi=0):
        """Horizontal slab with rectangular holes (hx0, hx1, hy0, hy1), non-overlapping in x."""
        cur = x0
        for (hx0, hx1, hy0, hy1) in sorted(holes):
            if hx0 > cur:
                self.box(cur, hx0, y0, y1, z0, z1, mi)
            if hy0 > y0:
                self.box(hx0, hx1, y0, hy0, z0, z1, mi)
            if y1 > hy1:
                self.box(hx0, hx1, hy1, y1, z0, z1, mi)
            cur = hx1
        if x1 > cur:
            self.box(cur, x1, y0, y1, z0, z1, mi)

    def frame(self, x0, x1, y0, y1, z0, z1, w, mi=0, axis='Y'):
        """Rectangular picture frame of bar width w in the plane normal to `axis`."""
        if axis == 'Y':
            self.box(x0, x1, y0, y1, z0, z0 + w, mi); self.box(x0, x1, y0, y1, z1 - w, z1, mi)
            self.box(x0, x0 + w, y0, y1, z0 + w, z1 - w, mi); self.box(x1 - w, x1, y0, y1, z0 + w, z1 - w, mi)
        elif axis == 'X':
            self.box(x0, x1, y0, y1, z0, z0 + w, mi); self.box(x0, x1, y0, y1, z1 - w, z1, mi)
            self.box(x0, x1, y0, y0 + w, z0 + w, z1 - w, mi); self.box(x0, x1, y1 - w, y1, z0 + w, z1 - w, mi)
        else:  # Z: horizontal frame
            self.box(x0, x1, y0, y0 + w, z0, z1, mi); self.box(x0, x1, y1 - w, y1, z0, z1, mi)
            self.box(x0, x0 + w, y0 + w, y1 - w, z0, z1, mi); self.box(x1 - w, x1, y0 + w, y1 - w, z0, z1, mi)

    # -- prisms / revolves / sweeps -----------------------------------------
    def prism(self, pts, z0, z1, mi=0):
        """Extrude a CCW 2D polygon from z0 to z1."""
        n = len(pts)
        vs = [(x, y, z0) for x, y in pts] + [(x, y, z1) for x, y in pts]
        fs = [tuple(reversed(range(n))), tuple(range(n, 2 * n))]
        for i in range(n):
            j = (i + 1) % n
            fs.append((i, j, n + j, n + i))
        self._add(vs, fs, mi)

    def quad(self, a, b, c, d, mi=0):
        self._add([a, b, c, d], [(0, 1, 2, 3)], mi)

    def arc_prism(self, cx, cy, r0, r1, a0, a1, z0, z1, seg=12, mi=0):
        """Ring sector (curved sofa / stair landing) between radii r0<r1, angles a0->a1."""
        pts = []
        for i in range(seg + 1):
            a = a0 + (a1 - a0) * i / seg
            pts.append((cx + r1 * math.cos(a), cy + r1 * math.sin(a)))
        for i in range(seg, -1, -1):
            a = a0 + (a1 - a0) * i / seg
            pts.append((cx + r0 * math.cos(a), cy + r0 * math.sin(a)))
        if a1 < a0:
            pts.reverse()
        self.prism(pts, z0, z1, mi)

    def cylinder(self, cx, cy, z0, z1, r0, r1=None, seg=16, mi=0, ry=None, rot=0.0):
        """Tapered (elliptical if ry) cylinder along Z."""
        r1 = r0 if r1 is None else r1
        vs, fs = [], []
        for (z, r) in ((z0, r0), (z1, r1)):
            rr_y = r if ry is None else ry * (r / r0 if r0 else 1)
            for i in range(seg):
                a = 2 * math.pi * i / seg + rot
                vs.append((cx + r * math.cos(a), cy + rr_y * math.sin(a), z))
        for i in range(seg):
            j = (i + 1) % seg
            fs.append((i, j, seg + j, seg + i))
        fs.append(tuple(reversed(range(seg))))
        fs.append(tuple(range(seg, 2 * seg)))
        self._add(vs, fs, mi)

    def lathe(self, cx, cy, cz, profile, seg=24, mi=0, ry=1.0):
        """Revolve a profile [(r, z), ...] (z relative to cz, r>=0, first/last may be r=0) about a vertical axis."""
        n = len(profile)
        vs, fs = [], []
        for (r, z) in profile:
            for i in range(seg):
                a = 2 * math.pi * i / seg
                vs.append((cx + r * math.cos(a), cy + r * ry * math.sin(a), cz + z))
        for k in range(n - 1):
            for i in range(seg):
                j = (i + 1) % seg
                a, b, c, d = k * seg + i, k * seg + j, (k + 1) * seg + j, (k + 1) * seg + i
                if profile[k][0] < 1e-6:
                    fs.append((a, c, d))
                elif profile[k + 1][0] < 1e-6:
                    fs.append((a, b, c))
                else:
                    fs.append((a, b, c, d))
        if profile[0][0] > 1e-6:
            fs.append(tuple(reversed(range(seg))))
        if profile[-1][0] > 1e-6:
            fs.append(tuple(range((n - 1) * seg, n * seg)))
        self._add(vs, fs, mi)

    def sweep(self, sections, mi=0, close=False, caps=True):
        """Loft a list of sections (each a list of N 3D points, same N) into a tube. Shared vertices -> subsurf friendly."""
        n = len(sections[0])
        vs = [p for sec in sections for p in sec]
        fs = []
        m = len(sections)
        for k in range(m - 1 if not close else m):
            k2 = (k + 1) % m
            for i in range(n):
                j = (i + 1) % n
                fs.append((k * n + i, k * n + j, k2 * n + j, k2 * n + i))
        if caps and not close:
            fs.append(tuple(reversed(range(n))))
            fs.append(tuple(range((m - 1) * n, m * n)))
        self._add(vs, fs, mi)

    def tube(self, p0, p1, r0, r1, seg=8, mi=0):
        p0, p1 = Vector(p0), Vector(p1)
        d = p1 - p0
        if d.length < 1e-6:
            return
        q = d.normalized().to_track_quat('Z', 'Y')
        secs = []
        for (p, r) in ((p0, r0), (p1, r1)):
            secs.append([tuple(p + q @ Vector((r * math.cos(2 * math.pi * i / seg), r * math.sin(2 * math.pi * i / seg), 0))) for i in range(seg)])
        self.sweep(secs, mi)

    def path_tube(self, pts, r, seg=8, mi=0):
        """Round tube along a polyline (shared sections -> smooth with subsurf)."""
        pts = [Vector(p) for p in pts]
        secs = []
        for k, p in enumerate(pts):
            if k == 0:
                t = pts[1] - pts[0]
            elif k == len(pts) - 1:
                t = pts[-1] - pts[-2]
            else:
                t = (pts[k + 1] - pts[k - 1])
            q = t.normalized().to_track_quat('Z', 'Y')
            secs.append([tuple(p + q @ Vector((r * math.cos(2 * math.pi * i / seg), r * math.sin(2 * math.pi * i / seg), 0))) for i in range(seg)])
        self.sweep(secs, mi)

    def sphere(self, c, r, seg=16, rings=10, mi=0, squash=1.0):
        self.blob(c, r, seg, rings, 0.0, 0, mi, squash)

    def blob(self, c, r, seg=12, rings=8, jitter=0.0, seed=0, mi=0, squash=1.0, rx=1.0, ry=1.0):
        """UV-sphere with optional noise jitter (foliage clumps); squash scales Z."""
        cx, cy, cz = c
        vs, fs = [], []
        rng = random.Random(seed)
        off = Vector((rng.uniform(0, 100), rng.uniform(0, 100), rng.uniform(0, 100)))
        for j in range(rings + 1):
            th = math.pi * j / rings
            for i in range(seg):
                ph = 2 * math.pi * i / seg
                n = Vector((math.sin(th) * math.cos(ph), math.sin(th) * math.sin(ph), math.cos(th)))
                rr = r
                if jitter:
                    rr = r * (1 + jitter * noise.noise(off + n * 2.2) + 0.45 * jitter * noise.noise(off + n * 5.5))
                vs.append((cx + rr * n.x * rx, cy + rr * n.y * ry, cz + rr * n.z * squash))
        for j in range(rings):
            for i in range(seg):
                a = j * seg + i
                b = j * seg + (i + 1) % seg
                c2 = (j + 1) * seg + (i + 1) % seg
                d = (j + 1) * seg + i
                if j == 0:
                    fs.append((a, c2, d))
                elif j == rings - 1:
                    fs.append((a, b, d))
                else:
                    fs.append((a, b, c2, d))
        self._add(vs, fs, mi)

    def cone_blob(self, c, r_base, h, seg=12, rings=10, jitter=0.3, seed=0, mi=0):
        cx, cy, cz = c
        rng = random.Random(seed)
        off = Vector((rng.uniform(0, 100), rng.uniform(0, 100), rng.uniform(0, 100)))
        vs, fs = [], []
        for j in range(rings + 1):
            t = j / rings
            rr0 = r_base * (1 - t) ** 0.8 + 0.05
            for i in range(seg):
                ph = 2 * math.pi * i / seg
                n = Vector((math.cos(ph), math.sin(ph), 0))
                rr = rr0 * (1 + jitter * noise.noise(off + Vector((n.x * 1.5, n.y * 1.5, t * 6))))
                vs.append((cx + rr * n.x, cy + rr * n.y, cz + h * t))
        for j in range(rings):
            for i in range(seg):
                a = j * seg + i; b = j * seg + (i + 1) % seg
                c2 = (j + 1) * seg + (i + 1) % seg; d = (j + 1) * seg + i
                fs.append((a, b, c2, d))
        fs.append(tuple(reversed(range(seg))))
        self._add(vs, fs, mi)

    def rbox(self, x0, x1, y0, y1, z0, z1, r=0.05, mi=0, seg=3, rot=0.0, puff=0.0):
        """Rounded box (all 12 edges filleted) built as a loft — for cushions, tubs, pads.
        `rot` rotates it about its own vertical centre line; `puff` (0..1) bulges the top/bottom faces like a stuffed cushion."""
        r = min(r, (x1 - x0) / 2 - 1e-4, (y1 - y0) / 2 - 1e-4, (z1 - z0) / 2 - 1e-4)
        if r <= 0:
            self.box(x0, x1, y0, y1, z0, z1, mi); return
        cx0, cy0 = (x0 + x1) / 2, (y0 + y1) / 2
        levels = []
        for k in range(seg + 1):          # bottom fillet
            a = math.pi / 2 * k / seg
            levels.append((z0 + r - r * math.cos(a), r * math.sin(a), -1.0 + k / seg))
        for k in range(seg + 1):          # top fillet
            a = math.pi / 2 * k / seg
            levels.append((z1 - r + r * math.sin(a), r * math.cos(a), k / seg))
        secs = []
        c, s = math.cos(rot), math.sin(rot)
        for (z, rr, t) in levels:
            sec = []
            for (cx, cy, a0) in ((x1 - r, y0 + r, -math.pi / 2), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, math.pi / 2), (x0 + r, y0 + r, math.pi)):
                for k in range(seg + 1):
                    a = a0 + math.pi / 2 * k / seg
                    px, py = cx + rr * math.cos(a), cy + rr * math.sin(a)
                    dx, dy = px - cx0, py - cy0
                    sec.append((cx0 + dx * c - dy * s, cy0 + dx * s + dy * c, z))
            secs.append(sec)
        if puff > 0:                     # add a centre point ring so the caps dome outward
            top = [(cx0, cy0, z1 + puff * r)]
            bot = [(cx0, cy0, z0 - puff * r)]
            # approximate by scaling the last/first ring inward and lifting it
            def ring(sec, z, k):
                return [(cx0 + (px - cx0) * k, cy0 + (py - cy0) * k, z) for (px, py, _) in sec]
            secs = [ring(secs[0], z0 - puff * r * 0.7, 0.35)] + secs + [ring(secs[-1], z1 + puff * r * 0.7, 0.35)]
        self.sweep(secs, mi)

    def rcbox(self, cx, cy, cz, sx, sy, sz, r=0.05, mi=0, rot=0.0, seg=3, puff=0.0):
        """Rounded box centred at (cx,cy,cz), size (sx,sy,sz), rotated about Z by rot."""
        self.rbox(cx - sx / 2, cx + sx / 2, cy - sy / 2, cy + sy / 2, cz - sz / 2, cz + sz / 2, r, mi, seg, rot, puff)

    def pillow(self, cx, cy, cz, w=0.6, d=0.42, t=0.16, mi=0, rot=0.0, tilt=0.0, pitch=0.0):
        """Plump pillow: a squashed superellipsoid with single pole vertices (clean under subsurf).
        `pitch` rotates it about its own X axis (pitch ~1.3 = standing up against a backrest)."""
        seg, rings = 16, 8
        c, s = math.cos(rot), math.sin(rot)
        cp, sp = math.cos(pitch), math.sin(pitch)
        def P(nx, ny, nz):
            k = 1.0 / (abs(nx) ** 3 + abs(ny) ** 3 + 1e-6) ** (1 / 3) if (abs(nx) + abs(ny)) > 1e-4 else 1.0
            k = min(k, 1.35)
            px, py, pz = nx * k * w / 2, ny * k * d / 2, nz * t / 2 * (1.0 - 0.35 * (k - 1.0))
            pz += tilt * py
            py, pz = py * cp - pz * sp, py * sp + pz * cp
            return (cx + px * c - py * s, cy + px * s + py * c, cz + pz)
        vs = [P(0, 0, 1)]
        for j in range(1, rings):
            th = math.pi * j / rings
            for i in range(seg):
                ph = 2 * math.pi * i / seg
                vs.append(P(math.sin(th) * math.cos(ph), math.sin(th) * math.sin(ph), math.cos(th)))
        vs.append(P(0, 0, -1))
        fs = []
        top, bot = 0, len(vs) - 1
        def R(j, i):
            return 1 + (j - 1) * seg + (i % seg)
        for i in range(seg):
            fs.append((top, R(1, i + 1), R(1, i)))
        for j in range(1, rings - 1):
            for i in range(seg):
                fs.append((R(j, i), R(j, i + 1), R(j + 1, i + 1), R(j + 1, i)))
        for i in range(seg):
            fs.append((R(rings - 1, i), R(rings - 1, i + 1), bot))
        self._add(vs, fs, mi)

    def pillow_sq(self, cx, cy, cz, w=0.7, d=0.5, t=0.15, mi=0, rot=0.0, pitch=0.0, nx=20, ny=18, flange=0.008, p=2.6, dome=1.5, seed=0):
        """Sewn pillow: a rectangle whose thickness follows a superellipse (flat plump centre, rounded edges, a
        piped seam flange at the rim), lightly crumpled.  `pitch` rotates it about its own X axis (~1.3 = standing
        against a headboard), `rot` yaws it about Z; cz = the centre height."""
        rng = random.Random(seed)
        c, s = math.cos(rot), math.sin(rot)
        cp, sp = math.cos(pitch), math.sin(pitch)
        ph1, ph2 = rng.uniform(0, 6), rng.uniform(0, 6)
        def edge(u):
            return max(0.0, 1.0 - abs(2 * u - 1) ** p) ** (1.0 / p)
        def P(u, v, sgn):
            e = edge(u) * edge(v)
            h = (t / 2) * (e ** dome) * sgn
            h += t * 0.06 * math.sin(3.1 * u + ph1) * math.sin(2.3 * v + ph2) * e
            # Short creases converge into the seam and fade before the filled centre.
            seam_dist = min(u, 1-u, v, 1-v)
            h += t * .035 * math.sin(39*u+13*v+ph1) * math.exp(-seam_dist*18) * e
            px, py = (u - 0.5) * w, (v - 0.5) * d
            if e < 1e-6:                                    # rim: push the seam out a little
                px += flange * (1 if u > 0.5 else -1) * (abs(2 * u - 1) > 0.999)
                py += flange * (1 if v > 0.5 else -1) * (abs(2 * v - 1) > 0.999)
            py, pz = py * cp - h * sp, py * sp + h * cp
            return (cx + px * c - py * s, cy + px * s + py * c, cz + pz)
        for sgn in (1, -1):
            b = len(self.v)
            vs = [P(i / nx, j / ny, sgn) for i in range(nx + 1) for j in range(ny + 1)]
            fs = []
            for i in range(nx):
                for j in range(ny):
                    a, bb, cc, dd = i * (ny + 1) + j, (i + 1) * (ny + 1) + j, (i + 1) * (ny + 1) + j + 1, i * (ny + 1) + j + 1
                    fs.append((a, bb, cc, dd) if sgn > 0 else (a, dd, cc, bb))
            self._add(vs, fs, mi)

    def drape(self, x0, x1, y0, y1, z, t=0.03, mi=0, sag=0.06, rot=0.0, folds=2, seed=0):
        """A throw / folded blanket lying on a surface: a wavy slab with soft edges (subsurf it)."""
        nx, ny = 10, 6
        rng = random.Random(seed)
        ph = rng.uniform(0, 6)
        cx0, cy0 = (x0 + x1) / 2, (y0 + y1) / 2
        c, s = math.cos(rot), math.sin(rot)
        def P(u, v, dz):
            px, py = x0 + (x1 - x0) * u, y0 + (y1 - y0) * v
            h = z + dz + sag * (0.5 * math.sin(folds * math.pi * u + ph) * math.sin(math.pi * v) + 0.3 * math.sin(2.7 * math.pi * v + ph))
            dx, dy = px - cx0, py - cy0
            return (cx0 + dx * c - dy * s, cy0 + dx * s + dy * c, h)
        secs = []
        for i in range(nx + 1):
            u = i / nx
            sec = [P(u, j / ny, t) for j in range(ny + 1)] + [P(u, j / ny, 0.0) for j in range(ny, -1, -1)]
            secs.append(sec)
        self.sweep(secs, mi)

    # -- output --------------------------------------------------------------
    def build(self, name, mats, coll='House', smooth=False, recalc=True, subsurf=0, bevel=0.0, bevel_seg=3, auto_smooth=None):
        me = bpy.data.meshes.new(name)
        me.from_pydata(self.v, [], self.f)
        me.validate()
        if isinstance(mats, bpy.types.Material):
            mats = [mats]
        for m in mats:
            me.materials.append(m)
        if len(mats) > 1:
            for p, mi in zip(me.polygons, self.fm):
                p.material_index = min(mi, len(mats) - 1)
        if recalc:
            bm = bmesh.new(); bm.from_mesh(me)
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            bm.to_mesh(me); bm.free()
        if smooth:
            for p in me.polygons:
                p.use_smooth = True
        ob = bpy.data.objects.new(name, me)
        collection(coll).objects.link(ob)
        if smooth and auto_smooth is None:
            auto_smooth = True                 # smooth shading on meshes that also contain flat boxes needs the angle split
        if bevel > 0:
            bv = ob.modifiers.new("bevel", 'BEVEL')
            bv.width = bevel; bv.segments = bevel_seg; bv.limit_method = 'ANGLE'; bv.angle_limit = math.radians(40)
            bv.harden_normals = False
            for p in me.polygons:
                p.use_smooth = True
            if auto_smooth is None:
                auto_smooth = True
        if subsurf > 0:
            ss = ob.modifiers.new("subsurf", 'SUBSURF'); ss.levels = subsurf; ss.render_levels = subsurf
        if auto_smooth:
            try:
                bpy.ops.object.select_all(action='DESELECT')
                ob.select_set(True); bpy.context.view_layer.objects.active = ob
                bpy.ops.object.shade_auto_smooth(angle=math.radians(35))
            except Exception:
                pass
        return ob


def box(name, x0, x1, y0, y1, z0, z1, mat, coll='House'):
    mb = MB(); mb.box(x0, x1, y0, y1, z0, z1)
    return mb.build(name, mat, coll)


def look_at(ob, target):
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def rot2(px, py, cx, cy, rot):
    """Rotate (px,py) about (cx,cy) by rot radians."""
    c, s = math.cos(rot), math.sin(rot)
    dx, dy = px - cx, py - cy
    return (cx + dx * c - dy * s, cy + dx * s + dy * c)
