"""Staging kit for photo-matched bedrooms, closets and baths (bpy through archviz.mesh.MB).

Soft goods: a comforter / coverlet draped over a mattress (quarter-round wrap at the edges, hanging drops with folds
and flared, drooping corners, lumps where pillows lie underneath), a box-pleat bed skirt, hanging garments, folded
stacks, a gathered shower curtain on rings, a sheer panel drawn into a tie-back.  Case goods and fixtures modelled on
builder-grade / big-box pieces: platform and cube-panel beds, drawer chests (bail, knob or bar pulls, bun or square
feet), a nightstand with an open shelf, a crystal-column lamp, a porcelain lantern lamp, a track-arm sofa with a
button-tufted back, a power recliner, a recumbent exercise bike, an office chair, a desk, bookcases, wire closet
shelving, a bath vanity, a two-piece toilet, a globe light bar.

Every builder draws into caller-supplied MB accumulators in a local frame: origin (x, y) on the floor at z, rotated
by `rot` about Z; local +Y is the piece's BACK (the wall / headboard side), local -Y its FRONT, local X its width.
Builders that need modifiers (solidify, subsurf) build and return their own objects.
"""
import math
import random

from .mesh import MB


class F:
    """Local frame: (lx, ly, lz) -> world, drawing into an MB."""

    def __init__(self, mb, x, y, rot=0.0, z=0.0):
        self.mb, self.x, self.y, self.z, self.rot = mb, x, y, z, rot
        self.c, self.s = math.cos(rot), math.sin(rot)

    def P(self, lx, ly, lz=0.0):
        return (self.x + lx * self.c - ly * self.s, self.y + lx * self.s + ly * self.c, self.z + lz)

    def box(self, x0, x1, y0, y1, z0, z1, mi=0, mb=None):
        P = self.P
        (mb or self.mb).hexa([P(x0, y0, z0), P(x1, y0, z0), P(x1, y1, z0), P(x0, y1, z0),
                              P(x0, y0, z1), P(x1, y0, z1), P(x1, y1, z1), P(x0, y1, z1)], mi)

    def rbox(self, x0, x1, y0, y1, z0, z1, r=0.02, mi=0, puff=0.0, seg=3, mb=None):
        cx, cy, cz = self.P((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
        (mb or self.mb).rcbox(cx, cy, cz, abs(x1 - x0), abs(y1 - y0), abs(z1 - z0), r, mi, self.rot, seg=seg, puff=puff)

    def lathe(self, lx, ly, lz, profile, seg=16, mi=0, mb=None, ry=1.0):
        x, y, z = self.P(lx, ly, lz)
        (mb or self.mb).lathe(x, y, z, profile, seg=seg, mi=mi, ry=ry)

    def cyl(self, lx, ly, z0, z1, r0, r1=None, seg=12, mi=0, mb=None):
        x, y, _ = self.P(lx, ly, 0)
        (mb or self.mb).cylinder(x, y, self.z + z0, self.z + z1, r0, r1, seg=seg, mi=mi, rot=self.rot)

    def tube(self, p0, p1, r0, r1=None, seg=8, mi=0, mb=None):
        (mb or self.mb).tube(self.P(*p0), self.P(*p1), r0, r0 if r1 is None else r1, seg=seg, mi=mi)

    def path(self, pts, r, seg=8, mi=0, mb=None):
        (mb or self.mb).path_tube([self.P(*p) for p in pts], r, seg=seg, mi=mi)

    def sphere(self, lx, ly, lz, r, seg=12, rings=8, mi=0, squash=1.0, mb=None):
        (mb or self.mb).sphere(self.P(lx, ly, lz), r, seg=seg, rings=rings, mi=mi, squash=squash)

    def hexa(self, pts, mi=0, mb=None):
        (mb or self.mb).hexa([self.P(*p) for p in pts], mi)

    def sweep(self, secs, mi=0, mb=None, close=False, caps=True):
        (mb or self.mb).sweep([[self.P(*p) for p in sec] for sec in secs], mi, close=close, caps=caps)

    def pillow(self, lx, ly, lz, w, d, t, mi=0, lrot=0.0, pitch=0.0, seed=0, mb=None, **kw):
        wx, wy, wz = self.P(lx, ly, lz)
        (mb or self.mb).pillow_sq(wx, wy, wz, w, d, t, mi, rot=self.rot + lrot, pitch=pitch, seed=seed, **kw)

    def grid(self, pts, nu, nv, mi=0, mb=None, flip=False):
        """Quad grid from a row-major list of (nu+1) x (nv+1) local points."""
        m = mb or self.mb
        base = len(m.v)
        m.v.extend(self.P(*p) for p in pts)
        for i in range(nu):
            for j in range(nv):
                a = base + i * (nv + 1) + j
                q = (a, a + nv + 1, a + nv + 2, a + 1)
                m.f.append(tuple(reversed(q)) if flip else q)
                m.fm.append(mi)


def _smooth_min(a, b, k):
    h = max(0.0, min(1.0, 0.5 + 0.5 * (b - a) / k))
    return b * (1 - h) + a * h - k * h * (1 - h)


# ============================================================ soft goods
def drape_points(w, l, z_top, drop_side, drop_foot, r=0.06, z_floor=0.0, head_gap=0.0, folds=5, fold_amp=0.02,
                 flare=0.05, lumps=(), crown=0.012, seed=0, nu=64, nv=56, corner_droop=1.0, head_tuck=0.0,
                 top_wave=0.006):
    """Vertices of a cover draped over a w x l mattress top at z_top (local frame: head at +Y = +l/2, foot at -Y).
    The unfolded sheet spans s in [-(w/2 + drop_side), +] and t from the head (0) to l + drop_foot; beyond the
    mattress edge the cloth wraps a quarter-round of radius r and hangs, flaring out by `flare` at the hem, with
    `folds` soft vertical folds per metre of hem.  Corners hang radially (a cone), so they droop lower.  `lumps` =
    [(lx, ly, rx, ry, h)] bumps on the top (pillows under the cover).  Returns (points, nu, nv)."""
    rng = random.Random(seed)
    ph = [rng.uniform(0, 6.3) for _ in range(6)]
    S = w / 2 + drop_side
    T = l - head_gap + drop_foot
    pts = []

    def wrap(d, hang_max):
        """distance d past the edge -> (outward offset, dz)."""
        if d <= 0:
            return 0.0, 0.0
        arc = math.pi * r / 2
        if d <= arc:
            th = d / r
            return r * math.sin(th), -r * (1 - math.cos(th))
        hang = d - arc
        return r, -r - hang

    for i in range(nu + 1):
        s = -S + 2 * S * i / nu
        for j in range(nv + 1):
            t = T * j / nv
            ds = abs(s) - w / 2                       # past the side edge
            ly_top = l / 2 - head_gap - t              # local y if on top
            dt = -(ly_top + l / 2)                     # past the foot edge (positive beyond)
            sx = 1.0 if s >= 0 else -1.0
            if ds <= 0 and dt <= 0:
                x, y, dz = s, ly_top, 0.0
                # mattress crown, gentle waves, lumps
                u = (s + w / 2) / w
                dz += crown * math.sin(math.pi * u) * min(1.0, (l / 2 - head_gap - ly_top + 0.3) / 0.6)
                dz += top_wave * math.sin(3.1 * s + ph[0]) * math.sin(2.3 * ly_top + ph[1])
                for (lx, lyy, rx, ry, h) in lumps:
                    e = ((s - lx) / rx) ** 2 + ((ly_top - lyy) / ry) ** 2
                    if e < 4:
                        dz += h * math.exp(-e * 1.6)
                if head_tuck > 0 and ly_top > l / 2 - head_gap - 0.05:
                    dz -= head_tuck
                pts.append((x, y, z_top + dz))
                continue
            if ds > 0 and dt <= 0:                      # side drop
                off, dz = wrap(ds, drop_side)
                hang = max(0.0, -dz - r)
                k = min(1.0, hang / max(drop_side, 1e-3))
                fold = fold_amp * k * math.sin(2 * math.pi * folds * ly_top + ph[2] + sx)
                x = sx * (w / 2 + off + flare * k * k + fold)
                y = ly_top + 0.4 * fold_amp * k * math.cos(2 * math.pi * folds * ly_top + ph[3])
                z = z_top + dz
            elif dt > 0 and ds <= 0:                    # foot drop
                off, dz = wrap(dt, drop_foot)
                hang = max(0.0, -dz - r)
                k = min(1.0, hang / max(drop_foot, 1e-3))
                fold = fold_amp * k * math.sin(2 * math.pi * folds * s + ph[4])
                x = s + 0.4 * fold_amp * k * math.cos(2 * math.pi * folds * s + ph[5])
                y = -l / 2 - (off + flare * k * k + fold)
                z = z_top + dz
            else:                                       # corner: hang radially from the mattress corner
                rho = math.hypot(ds, dt) * corner_droop
                ux, uy = ds / math.hypot(ds, dt), dt / math.hypot(ds, dt)
                off, dz = wrap(rho, max(drop_side, drop_foot))
                hang = max(0.0, -dz - r)
                k = min(1.0, hang / max(drop_side, 1e-3))
                ang = math.atan2(uy, ux)
                fold = fold_amp * 1.5 * k * math.sin(6 * ang + ph[2])
                o = off + flare * 1.4 * k * k + fold
                x = sx * (w / 2 + o * ux)
                y = -l / 2 - o * uy
                z = z_top + dz
            if z < z_floor + 0.012:                     # pool on the floor
                extra = z_floor + 0.012 - z
                z = z_floor + 0.012
                if ds > 0 and dt <= 0:
                    x += sx * extra * 0.6
                elif dt > 0 and ds <= 0:
                    y -= extra * 0.6
            pts.append((x, y, z))
    return pts, nu, nv


def draped_cover(name, mats, x, y, rot, z_top, w, l, drop_side, drop_foot, coll, thickness=0.03, subsurf=1, **kw):
    """Build the draped cover as its own object (solidified, subdivided, smooth-shaded)."""
    import bpy
    mb = MB()
    L = F(mb, x, y, rot)
    pts, nu, nv = drape_points(w, l, z_top, drop_side, drop_foot, **kw)
    L.grid(pts, nu, nv, mi=0, flip=True)
    ob = mb.build(name, mats, coll=coll, smooth=True, auto_smooth=False)
    so = ob.modifiers.new("solidify", 'SOLIDIFY')
    so.thickness = thickness
    so.offset = 1.0
    so.use_even_offset = True
    if subsurf:
        ss = ob.modifiers.new("subsurf", 'SUBSURF'); ss.levels = subsurf; ss.render_levels = subsurf
    for p in ob.data.polygons:
        p.use_smooth = True
    # UVs in metres of the unfolded sheet (for printed / quilted textures)
    uvl = ob.data.uv_layers.new(name="UVMap")
    S = w / 2 + drop_side
    T = l - kw.get('head_gap', 0.0) + drop_foot
    for poly in ob.data.polygons:
        for li in poly.loop_indices:
            vi = ob.data.loops[li].vertex_index
            i, j = divmod(vi, nv + 1)
            uvl.data[li].uv = (2 * S * i / nu, T * (1 - j / nv))
    bpy.context.view_layer.update()
    return ob


def bed_skirt(mb, x, y, rot, w, l, z0, z1, mi=0, pleat=0.25, depth=0.02, head=False, seed=0, z=0.0):
    """A tailored skirt around a box spring (sides + foot, split at the corners), z0 floor .. z1 top: shallow
    vertical flutes and a box pleat at each foot corner."""
    L = F(mb, x, y, rot, z)
    rng = random.Random(seed)
    sides = [((-w / 2, l / 2), (-w / 2, -l / 2), (-1, 0)), ((-w / 2, -l / 2), (w / 2, -l / 2), (0, -1)), ((w / 2, -l / 2), (w / 2, l / 2), (1, 0))]
    for (p0, p1, nrm) in sides:
        L_ = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
        n = max(8, int(L_ / 0.02))
        rows = []
        ph = rng.uniform(0, 6)
        for k in range(n + 1):
            u = k / n
            px, py = p0[0] + (p1[0] - p0[0]) * u, p0[1] + (p1[1] - p0[1]) * u
            a = L_ * u
            corner = math.exp(-(a / 0.06) ** 2) + math.exp(-((L_ - a) / 0.06) ** 2)
            off = depth * (0.5 + 0.5 * math.sin(2 * math.pi * a / pleat + ph)) + 0.012 * corner
            rows.append((px + nrm[0] * off, py + nrm[1] * off))
        pts = []
        for (px, py) in rows:
            for zz in (z1, (z0 + z1) / 2, z0 + 0.008):
                pts.append((px, py, zz))
        L.grid(pts, n, 2, mi=mi, flip=nrm[0] > 0 or nrm[1] > 0)


def garment(mb, x, y, z_rod, rot=0.0, kind='coat', length=0.95, width=0.52, thick=0.07, mi=0, mi_hanger=None, seed=0, sway=0.0,
            sleeves=True):
    """A garment hanging from a rod running along local X: its breadth is along local Y (perpendicular to the rod), so
    neighbours overlap like coats on a real rail.  Shoulders slope from the hanger, the body widens a little and
    drapes to the hem, sleeves hang at the sides; `kind` 'coat' | 'jacket' | 'quilted' | 'bag' (garment bag) | 'suit'
    changes the fullness.  The garment's front faces local -X."""
    L = F(mb, x, y, rot, z_rod)
    rng = random.Random(seed)
    if mi_hanger is not None:
        L.path([(0, 0.0, 0.0), (0.012, 0.0, 0.015), (0.0, 0.0, 0.03), (-0.012, 0.0, 0.015), (0, 0.0, -0.03)], 0.003, seg=5, mi=mi_hanger)
    full = {'coat': 1.0, 'jacket': 0.85, 'quilted': 1.25, 'bag': 1.1, 'suit': 0.8}.get(kind, 1.0)
    n = 12
    secs = []
    ph = rng.uniform(0, 6)
    for k in range(n + 1):
        t = k / n
        z = -0.04 - length * t
        if t < 0.12:                                               # shoulders: from the hook out to full breadth
            hw = width * (0.18 + 0.32 * (t / 0.12) ** 0.6)
            th = thick * full * (0.5 + 0.5 * t / 0.12)
        else:
            hw = width * (0.50 + 0.04 * (t - 0.12))
            th = thick * full * (1.0 - 0.25 * t) if kind != 'bag' else thick * full
        ox = sway * t * t + 0.01 * math.sin(3 * t + ph)
        sec = []
        for m_ in range(16):
            a = 2 * math.pi * m_ / 16
            ca, sa = math.cos(a), math.sin(a)
            px = th / 2 * math.copysign(abs(ca) ** 0.8, ca)
            py = hw * math.copysign(abs(sa) ** 0.45, sa)
            if kind != 'bag':                                      # soft vertical folds
                px += 0.006 * math.sin(7 * py / max(width, 0.1) * math.pi + ph) * t
            sec.append((ox + px, py, z))
        secs.append(sec)
    L.sweep(secs, mi)
    if sleeves and kind not in ('bag',):
        sl = length * (0.62 if kind != 'jacket' else 0.55)
        for sgn in (-1, 1):
            p0 = (-thick * 0.1, sgn * width * 0.46, -0.08)
            p1 = (-thick * 0.25, sgn * width * 0.44, -0.08 - sl * 0.55)
            p2 = (-thick * 0.35, sgn * width * 0.40, -0.08 - sl)
            L.path([p0, p1, p2], 0.045 * full, seg=10, mi=mi)


def folded_stack(mb, x, y, z, rot, w, d, layers, mi=0, seed=0, t=0.035):
    """A stack of folded towels / blankets: rounded, slightly offset slabs; `layers` = list of material indices."""
    L = F(mb, x, y, rot, z)
    rng = random.Random(seed)
    zz = 0.0
    for i, m in enumerate(layers):
        dx, dy = rng.uniform(-0.02, 0.02), rng.uniform(-0.02, 0.02)
        tt = t * rng.uniform(0.8, 1.3)
        L.rbox(-w / 2 + dx, w / 2 + dx, -d / 2 + dy, d / 2 + dy, zz, zz + tt, r=min(tt / 2 - 0.001, 0.02), mi=m, puff=0.3)
        zz += tt * 0.95
    return zz


def shower_curtain(mb, along, a0, a1, b, z_rod, z_hem, gathered=0.0, folds=12, amp=0.03, mi=0, mi_ring=None, rings=12,
                   seed=0, bulge=0.0):
    """A fabric shower curtain hanging from rings on a rod along `along` at plane b; `gathered` = the fraction of
    the length bunched at the a1 end (0 = drawn across).  Soft sinusoidal folds deepen toward the hem."""
    rng = random.Random(seed)
    ph = rng.uniform(0, 6)
    nz, nu = 14, folds * 6
    span = a1 - a0
    pts = []
    for i in range(nu + 1):
        u = i / nu
        if gathered > 0:
            ua = u * (1 - gathered) if u < 1 - gathered else (1 - gathered) + (u - (1 - gathered)) * 0.25
            ua = min(1.0, ua / (1 - gathered * 0.75))
        else:
            ua = u
        a = a0 + span * ua
        for k in range(nz + 1):
            t = k / nz
            z = z_rod - 0.03 - (z_rod - 0.03 - z_hem) * t
            d = amp * (0.55 + 0.45 * t) * math.sin(2 * math.pi * folds * u + ph) + bulge * math.sin(math.pi * u) * t
            pts.append((a, b + d, z) if along == 'X' else (b + d, a, z))
    base = len(mb.v)
    mb.v.extend(pts)
    for i in range(nu):
        for k in range(nz):
            p = base + i * (nz + 1) + k
            mb.f.append((p, p + 1, p + nz + 2, p + nz + 1)); mb.fm.append(mi)
    if mi_ring is not None:
        for r in range(rings):
            u = (r + 0.5) / rings
            if gathered > 0 and u > 1 - gathered:
                continue
            a = a0 + span * u
            c = (a, b, z_rod - 0.01) if along == 'X' else (b, a, z_rod - 0.01)
            mb.sphere(c, 0.012, seg=8, rings=5, mi=mi_ring, squash=0.6)


def sheer_tieback(mb, along, a_center, b, s, z_top, z_bot, w=0.62, gather_z=None, lean=0.0, folds=8, mi=0, amp=0.028, seed=0,
                  pinch=0.24, flare=0.64):
    """A sheer panel gathered on a rod at z_top, drawn into a tie-back at gather_z (pinched to ~25 %) and released
    below; wall plane b, room side s; the panel leans toward `lean` (+/-1 along `along`) where it is tied."""
    rng = random.Random(seed)
    ph = rng.uniform(0, 6)
    gz = gather_z if gather_z is not None else z_bot + (z_top - z_bot) * 0.42
    nz, nu = 24, folds * 6
    pts = []
    for i in range(nu + 1):
        u = i / nu - 0.5
        for k in range(nz + 1):
            z = z_top - (z_top - z_bot) * k / nz
            if z >= gz:
                q = (z - gz) / (z_top - gz)
                pw = pinch + (1 - pinch) * q ** 0.8
                shift = lean * w * 0.38 * (1 - q) ** 1.5
            else:
                q = (gz - z) / (gz - z_bot)
                pw = pinch + (flare - pinch) * q ** 0.9
                shift = lean * w * 0.38 * (1 - q) ** 1.2
            aa = a_center + shift + u * w * pw
            d = s * (0.10 + amp * (0.6 + 0.6 * (1 - pw)) * math.sin(2 * math.pi * folds * (u + 0.5) + ph))
            pts.append((aa, b + d, z) if along == 'X' else (b + d, aa, z))
    base = len(mb.v)
    mb.v.extend(pts)
    for i in range(nu):
        for k in range(nz):
            p = base + i * (nz + 1) + k
            mb.f.append((p, p + 1, p + nz + 2, p + nz + 1)); mb.fm.append(mi)


# ============================================================ beds
def platform_bed(mb, x, y, rot, w, l, mi=0, head_h=1.08, head_t=0.06, rail_z=(0.14, 0.34), leg=0.07, leg_h=0.16,
                 head_frame=0.04, groove=True, z=0.0):
    """Low platform bed (photos 16/17): plain panel headboard with a framed top rail, side / foot rails, square legs.
    Mattress sizes: queen 1.52 x 2.03, king 1.93 x 2.03 (w x l, local +Y = head)."""
    L = F(mb, x, y, rot, z)
    hw, hl = w / 2, l / 2
    L.box(-hw - 0.035, hw + 0.035, -hl - 0.035, hl, rail_z[0], rail_z[1], mi)                # rails
    for sx in (-1, 1):
        L.box(sx * hw - leg / 2 - sx * 0.0, sx * hw + leg / 2, -hl - 0.035, -hl - 0.035 + leg, 0.0, leg_h + 0.02, mi)
    yb = hl + 0.005
    L.box(-hw - 0.06, hw + 0.06, yb, yb + head_t, 0.0, head_h, mi)                             # headboard panel
    for sx in (-1, 1):                                                                         # posts
        L.box(sx * (hw + 0.06) - (0.07 if sx > 0 else 0), sx * (hw + 0.06) + (0.0 if sx > 0 else 0.07),
              yb - 0.01, yb + head_t + 0.01, 0.0, head_h + 0.005, mi)
    if groove:
        L.box(-hw - 0.0, hw + 0.0, yb - 0.004, yb, head_h - 0.12, head_h - 0.105, mi)          # routed line under the top rail
    L.box(-hw - 0.07, hw + 0.07, yb - 0.012, yb + head_t + 0.012, head_h - 0.035, head_h + 0.01, mi)   # top cap


def cube_panel_bed(mb, x, y, rot, w, l, mi=0, head_h=1.32, foot_h=0.72, cols=4, z=0.0):
    """Espresso bed with a headboard and footboard of square raised panels (photo 21): two rows of cubes in the
    headboard, two in the footboard, the panels proud of the frame by 18 mm."""
    L = F(mb, x, y, rot, z)
    hw, hl = w / 2, l / 2
    L.box(-hw - 0.02, hw + 0.02, -hl, hl, 0.16, 0.36, mi)                                     # side rails
    for (yb, zt, t) in ((hl + 0.01, head_h, 0.07), (-hl - 0.09, foot_h, 0.07)):
        L.box(-hw - 0.08, hw + 0.08, yb, yb + t, 0.0, zt, mi)                                  # board
        for sx in (-1, 1):
            L.box(sx * (hw + 0.08) - (0.075 if sx > 0 else 0), sx * (hw + 0.08) + (0 if sx > 0 else 0.075), yb - 0.01, yb + t + 0.01, 0.0, zt + 0.01, mi)
        rows = 2
        z0 = zt - 0.52 if yb > 0 else 0.12
        pw = (w + 0.10) / cols
        face = yb - 0.018 if yb > 0 else yb - 0.018
        for i in range(cols):
            for j in range(rows):
                a0 = -hw - 0.05 + i * pw + 0.012
                a1 = a0 + pw - 0.024
                zz0 = z0 + j * 0.26 + 0.012
                zz1 = zz0 + 0.236
                if yb < 0:
                    zz0, zz1 = 0.10 + j * 0.30 + 0.015, 0.10 + j * 0.30 + 0.285
                L.box(a0, a1, face, face + 0.02 if yb > 0 else face + 0.02, zz0, zz1, mi)


def box_spring(mb, x, y, rot, w, l, z0, z1, mi=0):
    L = F(mb, x, y, rot)
    L.rbox(-w / 2, w / 2, -l / 2, l / 2, z0, z1, r=0.015, mi=mi)


def mattress(mb, x, y, rot, w, l, z0, z1, mi=0):
    L = F(mb, x, y, rot)
    L.rbox(-w / 2, w / 2, -l / 2, l / 2, z0, z1, r=0.05, mi=mi, puff=0.15)


# ============================================================ case goods
def chest(mb, x, y, rot, w, d, h, mi=0, mi_pull=1, drawers=4, feet='bun', pulls='bail', top_over=0.015, split=False,
          plinth=0.08, bevel_top=True, cols=None, knob_r=0.016, drawer_heights=None, shelf=False, mi_dark=None, z=0.0):
    """Drawer chest / dresser / nightstand.  feet: 'bun' | 'square' | 'plinth' | 'none'; pulls: 'bail' (Louis-Philippe
    drop bails), 'knob', 'bar', 'cup'.  split=True puts two drawers side by side in the top row.  shelf=True leaves an
    open shelf in the lowest bay (a nightstand).  Front = local -Y."""
    L = F(mb, x, y, rot, z)
    hw, hd = w / 2, d / 2
    fz = plinth if feet != 'none' else 0.0
    L.box(-hw, hw, -hd, hd, fz, h - 0.025, mi)                                               # carcass
    L.box(-hw - top_over, hw + top_over, -hd - top_over, hd + 0.005, h - 0.025, h, mi)       # top
    if bevel_top:
        L.box(-hw - top_over + 0.006, hw + top_over - 0.006, -hd - top_over + 0.006, hd, h, h + 0.006, mi)
    if feet == 'bun':
        for sx in (-1, 1):
            for sy in (-1, 1):
                L.lathe(sx * (hw - 0.05), sy * (hd - 0.05), 0.0, [(0, 0), (0.028, 0), (0.042, 0.03), (0.036, fz * 0.8), (0.03, fz), (0, fz)], seg=12, mi=mi)
    elif feet == 'square':
        for sx in (-1, 1):
            for sy in (-1, 1):
                L.box(sx * hw - (0.045 if sx > 0 else 0) , sx * hw + (0 if sx > 0 else 0.045), sy * hd - (0.045 if sy > 0 else 0),
                      sy * hd + (0 if sy > 0 else 0.045), 0.0, fz + 0.01, mi)
    elif feet == 'plinth':
        L.box(-hw + 0.01, hw - 0.01, -hd + 0.03, hd - 0.01, 0.0, fz, mi_dark if mi_dark is not None else mi)
    # drawers
    zb, zt = fz + 0.02, h - 0.045
    rows = drawer_heights or [1.0] * drawers
    tot = sum(rows)
    if shelf:
        zb = zb + (zt - zb) * 0.42
        L.box(-hw + 0.02, hw - 0.02, -hd + 0.02, hd - 0.02, fz + 0.012, fz + 0.03, mi)           # shelf board
    z = zt
    for k, fr in enumerate(rows):
        dh = (zt - zb) * fr / tot
        z0, z1 = z - dh + 0.006, z - 0.006
        z -= dh
        nc = 2 if (split and k == 0) or (cols and cols > 1) else 1
        for c in range(nc):
            a0 = -hw + 0.018 + c * (w - 0.036) / nc + (0.004 if c else 0)
            a1 = -hw + 0.018 + (c + 1) * (w - 0.036) / nc - (0.004 if c < nc - 1 else 0)
            L.box(a0, a1, -hd - 0.018, -hd, z0, z1, mi)                                        # drawer front
            L.box(a0 + 0.012, a1 - 0.012, -hd - 0.024, -hd - 0.018, z0 + 0.012, z1 - 0.012, mi)   # raised panel
            zc = (z0 + z1) / 2
            ac = (a0 + a1) / 2
            spots = (ac - (a1 - a0) * 0.25, ac + (a1 - a0) * 0.25) if (a1 - a0) > 0.55 and pulls != 'bar' else (ac,)
            for s_ in spots:
                if pulls == 'bail':
                    L.box(s_ - 0.035, s_ + 0.035, -hd - 0.030, -hd - 0.024, zc - 0.005, zc + 0.035, mi_pull)     # back plate
                    L.path([(s_ - 0.03, -hd - 0.032, zc + 0.02), (s_ - 0.03, -hd - 0.045, zc - 0.012), (s_ + 0.03, -hd - 0.045, zc - 0.012),
                            (s_ + 0.03, -hd - 0.032, zc + 0.02)], 0.004, seg=6, mi=mi_pull)
                elif pulls == 'knob':
                    L.sphere(s_, -hd - 0.024 - knob_r, zc, knob_r, seg=12, rings=8, mi=mi_pull)
                    L.tube((s_, -hd - 0.024, zc), (s_, -hd - 0.024 - knob_r, zc), 0.005, 0.005, seg=6, mi=mi_pull)
                elif pulls == 'bar':
                    L.tube((s_ - 0.06, -hd - 0.04, zc), (s_ + 0.06, -hd - 0.04, zc), 0.006, 0.006, seg=6, mi=mi_pull)
                    for e in (-0.06, 0.06):
                        L.tube((s_ + e, -hd - 0.024, zc), (s_ + e, -hd - 0.042, zc), 0.005, 0.005, seg=6, mi=mi_pull)
                elif pulls == 'cup':
                    L.box(s_ - 0.045, s_ + 0.045, -hd - 0.034, -hd - 0.024, zc - 0.012, zc + 0.012, mi_pull)


def bookcase(mb, x, y, rot, w, d, h, shelves=2, mi=0, t=0.018, back=True, z=0.0):
    """Laminate bookcase: sides, top, base kick, fixed shelves (returns the shelf surface heights)."""
    L = F(mb, x, y, rot, z)
    hw, hd = w / 2, d / 2
    for sx in (-1, 1):
        L.box(sx * hw - (t if sx > 0 else 0), sx * hw + (0 if sx > 0 else t), -hd, hd, 0.0, h, mi)
    L.box(-hw, hw, -hd, hd, h - t, h, mi)
    L.box(-hw + t, hw - t, -hd + 0.01, hd, 0.0, 0.06, mi)
    L.box(-hw + t, hw - t, -hd, hd, 0.06, 0.06 + t, mi)
    if back:
        L.box(-hw + t, hw - t, hd - 0.006, hd, 0.06, h - t, mi)
    zs = [0.06 + t]
    for k in range(1, shelves + 1):
        z = 0.06 + t + (h - t - 0.06 - t) * k / (shelves + 1)
        L.box(-hw + t, hw - t, -hd, hd - 0.006, z, z + t, mi)
        zs.append(z + t)
    return zs


def book_row(mb, x, y, z, rot, w, d, h, mis, seed=0, lean_end=True, fill=0.92, stacks=0, mi_page=None):
    """A row of books standing on a shelf (spines toward local -Y), random heights / thickness / colours from `mis`;
    `stacks` > 0 lays that many flat piles instead of part of the row."""
    L = F(mb, x, y, rot, z)
    rng = random.Random(seed)
    a = -w / 2
    end = -w / 2 + w * fill
    while a < end:
        if stacks and rng.random() < 0.18:
            pw = rng.uniform(0.16, 0.26)
            if a + pw > w / 2:
                break
            zz = 0.0
            for _ in range(rng.randint(2, 6)):
                tt = rng.uniform(0.012, 0.035)
                bw = rng.uniform(0.13, pw)
                L.box(a, a + bw, -d / 2 + rng.uniform(0, 0.02), d / 2 - 0.02, zz, zz + tt, rng.choice(mis))
                zz += tt
            a += pw + 0.01
            continue
        tt = rng.uniform(0.015, 0.045)
        hh = h * rng.uniform(0.62, 0.98)
        dd = d * rng.uniform(0.7, 1.0)
        L.box(a, a + tt, -d / 2, -d / 2 + dd, 0.0, hh, rng.choice(mis))
        if mi_page is not None:                           # page block: inset behind the spine, visible at the top
            L.box(a + 0.002, a + tt - 0.002, -d / 2 + 0.004, -d / 2 + dd - 0.004, 0.004, hh + 0.0005, mi_page)
        a += tt + rng.uniform(0.0, 0.004)


def desk(mb, x, y, rot, w, d, h=0.76, mi=0, drawer_side=None, modesty=True, t=0.03, z=0.0):
    """Simple computer desk: top, two panel ends, a modesty panel; optional drawer pedestal side ('L'/'R')."""
    L = F(mb, x, y, rot, z)
    hw, hd = w / 2, d / 2
    L.box(-hw, hw, -hd, hd, h - t, h, mi)
    for sx in (-1, 1):
        L.box(sx * hw - (0.025 if sx > 0 else 0), sx * hw + (0 if sx > 0 else 0.025), -hd + 0.02, hd, 0.0, h - t, mi)
    if modesty:
        L.box(-hw + 0.025, hw - 0.025, hd - 0.03, hd - 0.012, 0.25, h - t, mi)
    if drawer_side:
        sx = 1 if drawer_side == 'R' else -1
        L.box(sx * hw - (0.40 if sx > 0 else 0), sx * hw + (0 if sx > 0 else 0.40), -hd + 0.01, hd - 0.03, 0.02, h - t, mi)


# ============================================================ upholstery
def track_sofa(mb, pil, x, y, rot, w=2.05, d=0.88, mi=0, mi_leg=1, mi_button=None, seat_h=0.46, back_h=0.86, arm_h=0.62,
               arm_w=0.16, seats=3, tufts=True, flare=0.05, leg_h=0.13, z=0.0):
    """Mid-century track-arm sofa (photo 16/17): flared arms, a tight button-tufted back, loose box seat cushions
    with welts, tapered splayed wood legs.  Front = local -Y."""
    L = F(mb, x, y, rot, z)
    hw, hd = w / 2, d / 2
    z0 = leg_h
    L.rbox(-hw + arm_w * 0.6, hw - arm_w * 0.6, -hd + 0.05, hd - 0.02, z0, seat_h - 0.12, 0.03, mi)          # deck / base
    L.rbox(-hw + arm_w * 0.7, hw - arm_w * 0.7, hd - 0.22, hd, z0 + 0.05, back_h, 0.06, mi, puff=0.15)       # tight back
    for sx in (-1, 1):                                                                                       # flared arms
        secs = []
        for k in range(5):
            zz = z0 + (arm_h - z0) * k / 4
            out = flare * (k / 4) ** 1.5
            a_in = sx * (hw - arm_w)
            a_out = sx * (hw + out)
            ya, yb = -hd - out * 0.3, hd
            sec = [(min(a_in, a_out), ya, zz), (max(a_in, a_out), ya, zz), (max(a_in, a_out), yb, zz), (min(a_in, a_out), yb, zz)]
            secs.append(sec)
        L.rbox(min(sx * (hw - arm_w), sx * (hw + flare)), max(sx * (hw - arm_w), sx * (hw + flare)), -hd - 0.01, hd,
               arm_h - 0.06, arm_h, 0.03, mi, puff=0.3)
        L.rbox(min(sx * (hw - arm_w), sx * (hw + flare * 0.6)), max(sx * (hw - arm_w), sx * (hw + flare * 0.6)), -hd + 0.0, hd,
               z0, arm_h - 0.04, 0.03, mi)
    sw = (w - 2 * arm_w) / seats
    for i in range(seats):
        a0 = -hw + arm_w + i * sw + 0.004
        L.rbox(a0, a0 + sw - 0.008, -hd - 0.01, hd - 0.20, seat_h - 0.14, seat_h, 0.05, mi, puff=0.35)   # seat cushion
        if tufts and mi_button is not None:
            for r_ in range(2):
                for c_ in range(3):
                    bx = a0 + sw * (c_ + 0.5) / 3
                    bz = seat_h + 0.12 + r_ * 0.14
                    L.sphere(bx, hd - 0.225, bz, 0.01, seg=6, rings=4, mi=mi_button)
    # tapered splayed legs
    for sx in (-1, 1):
        for sy in (-1, 1):
            lx, ly = sx * (hw - 0.07), sy * (hd - 0.07)
            L.tube((lx, ly, z0 + 0.01), (lx + sx * 0.035, ly + sy * 0.03, 0.0), 0.022, 0.012, seg=10, mi=mi_leg)


def recliner(mb, x, y, rot, w=0.92, d=0.95, mi=0, seat_h=0.50, back_h=1.04, arm_h=0.62, z=0.0):
    """Power / rocker recliner (photo 17): pillow arms, a thick back with three horizontal channels and a head pad,
    a plump seat, a chaise pad folded under; everything in rounded, puffed forms.  Front = local -Y."""
    L = F(mb, x, y, rot, z)
    hw, hd = w / 2, d / 2
    L.rbox(-hw + 0.10, hw - 0.10, -hd + 0.08, hd - 0.10, 0.04, seat_h - 0.12, 0.05, mi)                      # base
    L.rbox(-hw + 0.13, hw - 0.13, -hd - 0.02, hd - 0.26, seat_h - 0.17, seat_h, 0.07, mi, puff=0.4)          # seat
    L.rbox(-hw + 0.08, hw - 0.08, -hd + 0.02, -hd + 0.14, 0.06, seat_h - 0.10, 0.05, mi, puff=0.2)           # footrest pad (folded)
    for sx in (-1, 1):
        L.rbox(sx * hw - (0.17 if sx > 0 else 0), sx * hw + (0 if sx > 0 else 0.17), -hd + 0.06, hd - 0.02, 0.02, arm_h, 0.08, mi, puff=0.35)
    for k, (z0, z1, t) in enumerate(((seat_h - 0.05, seat_h + 0.20, 0.26), (seat_h + 0.18, seat_h + 0.40, 0.24), (seat_h + 0.38, back_h, 0.22))):
        yb = hd - 0.02 - t
        L.rbox(-hw + 0.14, hw - 0.14, yb, hd - 0.02 + (0.02 * k), z0, z1, 0.08, mi, puff=0.45)                # back channels
    L.rbox(-hw + 0.10, hw - 0.10, hd - 0.14, hd + 0.02, seat_h - 0.1, back_h - 0.02, 0.07, mi)                # back shell


def pad_loft(L, path, half_w, half_t, mi=0, n=16, p=3.0, cap_round=True):
    """A padded cushion lofted along a path in the local YZ plane (x centred): `path` = [(y, z), ...], `half_w` /
    `half_t` = per-point half width (local X) and half thickness (perpendicular to the path, in YZ); sections are
    superellipses of exponent p (flat faces, rounded edges).  The ends are rounded off by shrinking sections."""
    secs = []
    m = len(path)
    for k, (y, z) in enumerate(path):
        y0, z0 = path[max(0, k - 1)]
        y1, z1 = path[min(m - 1, k + 1)]
        ty, tz = y1 - y0, z1 - z0
        ln = math.hypot(ty, tz) or 1.0
        ny, nz = -tz / ln, ty / ln                                                     # normal in YZ
        w, t = half_w[k], half_t[k]
        sec = []
        for i in range(n):
            a = 2 * math.pi * i / n
            ca, sa = math.cos(a), math.sin(a)
            px = w * math.copysign(abs(ca) ** (2 / p), ca)
            pt = t * math.copysign(abs(sa) ** (2 / p), sa)
            sec.append((px, y + ny * pt, z + nz * pt))
        secs.append(sec)
    L.sweep(secs, mi)


def office_chair(mb, x, y, rot, mi=0, mi_metal=1, seat_h=0.50, back_top=1.14, arms=True, z=0.0):
    """Executive task chair (photo 20): five-star base on twin-wheel casters, a gas lift, a padded seat with a
    waterfall front, a tall reclined back with a lumbar roll and a stitched head pad, loop arms with pads.
    Front = local -Y."""
    L = F(mb, x, y, rot, z)
    for i in range(5):
        a = 2 * math.pi * i / 5 + 0.3
        ex, ey = 0.31 * math.cos(a), 0.31 * math.sin(a)
        L.path([(0.04 * math.cos(a), 0.04 * math.sin(a), 0.12), (ex * 0.9, ey * 0.9, 0.09), (ex, ey, 0.065)], 0.02, seg=8, mi=mi_metal)
        for s_ in (-1, 1):
            L.sphere(ex + s_ * 0.015 * math.sin(a), ey - s_ * 0.015 * math.cos(a), 0.028, 0.026, seg=10, rings=6, mi=mi_metal)
    L.cyl(0, 0, 0.08, 0.16, 0.042, 0.038, seg=14, mi=mi_metal)
    L.cyl(0, 0, 0.16, seat_h - 0.09, 0.024, 0.024, seg=10, mi=mi_metal)
    L.cyl(0, 0, 0.22, 0.36, 0.034, 0.034, seg=12, mi=mi_metal)                           # lift shroud
    L.box(-0.10, 0.10, -0.12, 0.10, seat_h - 0.11, seat_h - 0.08, mi_metal)
    L.tube((0.10, 0.02, seat_h - 0.10), (0.20, 0.05, seat_h - 0.16), 0.006, seg=5, mi=mi_metal)       # height lever
    pad_loft(L, [(0.22, seat_h - 0.03), (0.0, seat_h), (-0.20, seat_h), (-0.27, seat_h - 0.05)], [0.20, 0.25, 0.25, 0.22],
             [0.04, 0.06, 0.06, 0.035], mi=mi)                                                      # seat, waterfall front
    back = [(0.25, seat_h + 0.05), (0.28, seat_h + 0.20), (0.26, seat_h + 0.32), (0.29, seat_h + 0.45), (0.33, back_top - 0.12),
            (0.35, back_top)]
    pad_loft(L, back, [0.19, 0.22, 0.23, 0.22, 0.21, 0.17], [0.05, 0.075, 0.08, 0.07, 0.07, 0.05], mi=mi)
    L.box(-0.05, 0.05, 0.14, 0.30, seat_h - 0.09, seat_h + 0.04, mi_metal)                        # back upright
    if arms:
        for sx in (-1, 1):
            L.path([(sx * 0.22, 0.12, seat_h - 0.08), (sx * 0.27, 0.10, seat_h + 0.05), (sx * 0.27, 0.0, seat_h + 0.17)], 0.018, seg=8, mi=mi_metal)
            L.rbox(sx * 0.27 - 0.035, sx * 0.27 + 0.035, -0.20, 0.08, seat_h + 0.17, seat_h + 0.21, 0.015, mi)


def recumbent_bike(mb, x, y, rot, mi_frame=0, mi_pad=1, mi_shroud=2, z=0.0):
    """Folding recumbent exercise bike (photo 17): an X frame, a flywheel shroud at the front with pedals, a padded
    seat and backrest at the rear.  Front (the pedals) = local -Y."""
    L = F(mb, x, y, rot, z)
    L.tube((-0.22, -0.40, 0.03), (0.22, -0.40, 0.03), 0.025, seg=8, mi=mi_frame)                           # front stabiliser
    L.tube((-0.20, 0.42, 0.03), (0.20, 0.42, 0.03), 0.025, seg=8, mi=mi_frame)                             # rear stabiliser
    L.tube((0, -0.40, 0.04), (0, 0.10, 0.62), 0.028, seg=8, mi=mi_frame)                                   # main tube
    L.tube((0, 0.42, 0.04), (0, -0.02, 0.45), 0.025, seg=8, mi=mi_frame)                                   # rear strut
    L.tube((0, 0.10, 0.62), (0, 0.30, 0.95), 0.022, seg=8, mi=mi_frame)                                    # back post
    L.rbox(-0.09, 0.09, -0.48, -0.16, 0.10, 0.44, 0.08, mi_shroud, puff=0.2)                                # flywheel shroud
    for sx in (-1, 1):
        L.tube((sx * 0.10, -0.32, 0.27), (sx * 0.12, -0.42 - 0.03 * sx, 0.27 - 0.10 * sx), 0.01, seg=6, mi=mi_frame)
        L.box(sx * 0.12 - 0.04, sx * 0.12 + 0.04, -0.46 - 0.03 * sx, -0.40 - 0.03 * sx, 0.14 - 0.10 * sx + 0.1, 0.16 - 0.10 * sx + 0.1, mi_frame)
    L.rbox(-0.17, 0.17, -0.02, 0.26, 0.50, 0.56, 0.03, mi_pad, puff=0.3)                                   # seat
    L.rbox(-0.14, 0.14, 0.28, 0.36, 0.62, 1.00, 0.04, mi_pad, puff=0.2)                                    # backrest
    for sx in (-1, 1):
        L.path([(sx * 0.18, 0.05, 0.52), (sx * 0.22, 0.02, 0.48), (sx * 0.22, 0.20, 0.48)], 0.012, seg=6, mi=mi_frame)
    L.tube((0, -0.16, 0.40), (0, -0.30, 0.72), 0.015, seg=6, mi=mi_frame)                                  # console post


# ============================================================ lamps and small things
def crystal_lamp(mb, x, y, z, mi_metal=0, mi_crystal=1, mi_shade=2, h=0.74, shade_r=0.19, shade_h=0.26):
    """Table lamp (photo 16): square silver foot, a column of faceted crystal, a white drum shade."""
    L = F(mb, x, y, 0.0, z)
    L.box(-0.07, 0.07, -0.07, 0.07, 0.0, 0.025, mi_metal)
    L.cyl(0, 0, 0.025, 0.045, 0.035, 0.03, seg=12, mi=mi_metal)
    zz = 0.045
    for r, hh in ((0.045, 0.05), (0.055, 0.07), (0.04, 0.05), (0.06, 0.09), (0.035, 0.04), (0.045, 0.06)):
        L.lathe(0, 0, zz, [(0.0, 0.0), (r * 0.7, 0.0), (r, hh * 0.35), (r, hh * 0.65), (r * 0.7, hh), (0.0, hh)], seg=8, mi=mi_crystal)
        zz += hh
    L.cyl(0, 0, zz, h - shade_h + 0.02, 0.012, 0.012, seg=8, mi=mi_metal)
    zs = h - shade_h
    L.lathe(0, 0, zs, [(shade_r, 0.0), (shade_r + 0.003, 0.0), (shade_r + 0.003, shade_h), (shade_r, shade_h)], seg=40, mi=mi_shade)
    L.cyl(0, 0, h - 0.02, h + 0.04, 0.008, 0.008, seg=6, mi=mi_metal)
    L.sphere(0, 0, h + 0.05, 0.014, seg=8, rings=6, mi=mi_metal)
    return (x, y, z + zs + shade_h * 0.45)


def lantern_lamp(mb, x, y, z, mi_wood=0, mi_porcelain=1, mi_metal=2):
    """Chinese lantern lamp (photo 19): a dark wood base and gallows arm, a blue-and-white porcelain lantern hanging
    from the arm.  Local +X = the arm's direction."""
    L = F(mb, x, y, 0.0, z)
    L.box(-0.10, 0.10, -0.07, 0.07, 0.0, 0.03, mi_wood)
    L.box(-0.09, -0.06, -0.015, 0.015, 0.03, 0.50, mi_wood)
    L.box(-0.10, 0.10, -0.015, 0.015, 0.50, 0.53, mi_wood)
    L.path([(-0.06, 0, 0.44), (-0.02, 0, 0.48), (0.0, 0, 0.50)], 0.006, seg=5, mi=mi_wood)
    L.tube((0.05, 0, 0.50), (0.05, 0, 0.44), 0.003, seg=4, mi=mi_metal)
    L.lathe(0.05, 0, 0.14, [(0.0, 0.0), (0.05, 0.0), (0.07, 0.04), (0.08, 0.12), (0.075, 0.22), (0.055, 0.28), (0.02, 0.30), (0, 0.30)],
            seg=24, mi=mi_porcelain)
    L.cyl(0.05, 0, 0.44 - 0.012, 0.44, 0.022, seg=12, mi=mi_metal)
    return (x + 0.05, y, z + 0.29)


def drum_pendant(mb, x, y, z_ceiling, drop, mi_metal=0, mi_crystal=1, r=0.085, h=0.10, seed=0):
    """Crystal-bead drum pendant on a rigid downrod (photo 15)."""
    rng = random.Random(seed)
    zb = z_ceiling - drop
    mb.cylinder(x, y, z_ceiling - 0.025, z_ceiling, 0.055, 0.052, seg=20, mi=mi_metal)
    mb.cylinder(x, y, zb + h, z_ceiling - 0.02, 0.006, 0.006, seg=8, mi=mi_metal)
    mb.cylinder(x, y, zb + h - 0.005, zb + h + 0.01, r * 0.95, r * 0.95, seg=20, mi=mi_metal)
    rows = 7
    for k in range(rows):
        zz = zb + h * (k + 0.5) / rows
        rr = r * (0.82 + 0.18 * math.sin(math.pi * (k + 0.5) / rows))
        n = int(2 * math.pi * rr / 0.018)
        off = rng.uniform(0, 1)
        for i in range(n):
            a = 2 * math.pi * (i + 0.5 * (k % 2) + off) / n
            mb.sphere((x + rr * math.cos(a), y + rr * math.sin(a), zz), 0.0085, seg=6, rings=4, mi=mi_crystal)
    for ring_r in (0.25, 0.5, 0.75):
        n = int(2 * math.pi * r * ring_r / 0.018) + 1
        for i in range(n):
            a = 2 * math.pi * i / n
            mb.sphere((x + r * ring_r * math.cos(a), y + r * ring_r * math.sin(a), zb + 0.004), 0.0085, seg=6, rings=4, mi=mi_crystal)
    return (x, y, zb + h * 0.5)
