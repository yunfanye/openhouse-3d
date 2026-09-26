"""Parametric furnishings and fixtures modelled after real pieces (Blender 5.x bpy through archviz.mesh.MB).

Every builder draws into caller-supplied MB accumulators (so the caller controls objects / materials) in a local
frame: origin (x, y) on the floor at z, rotated by `rot` about Z; local +Y is the piece's BACK, local -Y its FRONT
(the side a sofa or chair faces), local X its width.  `Loc` does the transform.

  sectional(...)            modular sofa: runs of loose seat / back cushions, track arms, a chaise, welts
  jhula(...)                carved Indian swing: trestle posts with finials, cusped crest beam, chains, carved bench
  carved_chair(...)         low carved chair with turned legs, openwork crest, rush seat
  carved_bench(...)         low carved table / bench with turned legs and a carved apron
  scroll_table(...)         glass-top cocktail / side table on scrolled iron legs
  media_console(...)        TV stand with a smoked-glass door, rounded top
  flat_tv(...)              flat panel on a pedestal
  parquet_table(...)        dining table with a quartered plank top and a block-carved apron
  panel_back_chair(...)     dining chair with a curved 2 x 2 panel back and an upholstered seat
  bell_chandelier(...)      chain-hung chandelier: column, curved arms, downward bell shades
  hugger_fan(...)           flush-mount ceiling fan with a vented motor, blades on irons, a 4-tulip light kit
  wall_clock(...)           round wall clock with a moulded rim, Roman numerals and hands
  register(...)             ceiling / wall HVAC supply register with louvres
  h_blinds(...)             2" horizontal blinds (head rail, slats, bottom rail, cords) in a window recess
  v_blinds(...)             vertical blinds stacked to one side under a head rail
  cornice(...)              upholstered / painted valance box
  grommet_panel(...)        pleated curtain panel hanging from grommets on a rod, optional tie-back sash
  rod(...)                  curtain rod with ball finials and brackets
Kitchen:  gas_range, under_hood, dishwasher, fridge_top_freezer, microwave, raised_panel_door (arched or square)
Fireplace: gas_firebox, fluted_mantel
"""
import math
import random
from .mesh import MB


class Loc:
    """Local frame helper: (lx, ly, lz) -> world, drawing into an MB."""

    def __init__(self, mb, x, y, rot=0.0, z=0.0):
        self.mb, self.x, self.y, self.z, self.rot = mb, x, y, z, rot
        self.c, self.s = math.cos(rot), math.sin(rot)

    def P(self, lx, ly, lz=0.0):
        return (self.x + lx * self.c - ly * self.s, self.y + lx * self.s + ly * self.c, self.z + lz)

    def box(self, x0, x1, y0, y1, z0, z1, mi=0, mb=None):
        P = self.P
        (mb or self.mb).hexa([P(x0, y0, z0), P(x1, y0, z0), P(x1, y1, z0), P(x0, y1, z0),
                              P(x0, y0, z1), P(x1, y0, z1), P(x1, y1, z1), P(x0, y1, z1)], mi)

    def rbox(self, x0, x1, y0, y1, z0, z1, r=0.04, mi=0, puff=0.0, seg=3, mb=None):
        cx, cy, cz = self.P((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
        (mb or self.mb).rcbox(cx, cy, cz, abs(x1 - x0), abs(y1 - y0), abs(z1 - z0), r, mi, self.rot, seg=seg, puff=puff)

    def lathe(self, lx, ly, lz, profile, seg=16, mi=0, mb=None):
        x, y, z = self.P(lx, ly, lz)
        (mb or self.mb).lathe(x, y, z, profile, seg=seg, mi=mi)

    def cyl(self, lx, ly, z0, z1, r0, r1=None, seg=12, mi=0, mb=None):
        x, y, _ = self.P(lx, ly, 0)
        (mb or self.mb).cylinder(x, y, self.z + z0, self.z + z1, r0, r1, seg=seg, mi=mi, rot=self.rot)

    def tube(self, p0, p1, r0, r1=None, seg=8, mi=0, mb=None):
        (mb or self.mb).tube(self.P(*p0), self.P(*p1), r0, r0 if r1 is None else r1, seg=seg, mi=mi)

    def path(self, pts, r, seg=8, mi=0, mb=None):
        (mb or self.mb).path_tube([self.P(*p) for p in pts], r, seg=seg, mi=mi)

    def sweep(self, secs, mi=0, mb=None, close=False, caps=True):
        (mb or self.mb).sweep([[self.P(*p) for p in sec] for sec in secs], mi, close=close, caps=caps)

    def quad(self, a, b, c, d, mi=0, mb=None):
        (mb or self.mb).quad(self.P(*a), self.P(*b), self.P(*c), self.P(*d), mi)

    def sphere(self, lx, ly, lz, r, seg=12, rings=8, mi=0, squash=1.0, mb=None):
        (mb or self.mb).sphere(self.P(lx, ly, lz), r, seg=seg, rings=rings, mi=mi, squash=squash)

    def prism(self, pts, z0, z1, mi=0, mb=None):
        (mb or self.mb).prism([self.P(px, py)[:2] for px, py in pts], self.z + z0, self.z + z1, mi)


def _profile_slab(L, x0, x1, y0, y1, zlo, zhi, n=24, mi=0, mb=None):
    """A slab in the local XZ plane (thickness y0..y1) whose bottom and top edges follow zlo(u) / zhi(u), u = 0..1
    across x0..x1: contiguous hexahedra, so a scalloped crest or apron has a smooth silhouette (no steps)."""
    P = L.P
    for i in range(n):
        u0, u1 = i / n, (i + 1) / n
        xa, xb = x0 + (x1 - x0) * u0, x0 + (x1 - x0) * u1
        la, lb, ha, hb = zlo(u0), zlo(u1), zhi(u0), zhi(u1)
        (mb or L.mb).hexa([P(xa, y0, la), P(xb, y0, lb), P(xb, y1, lb), P(xa, y1, la),
                           P(xa, y0, ha), P(xb, y0, hb), P(xb, y1, hb), P(xa, y1, ha)], mi)


def _turned(L, lx, ly, z0, h, r, mi=0, beads=3, seg=12, mb=None, foot=True):
    """A turned leg / post: vase + bead profile from z0 up h, max radius r."""
    prof = [(0.0, 0.0)]
    if foot:
        prof += [(r * 0.75, 0.0), (r * 0.95, h * 0.03), (r * 0.7, h * 0.07)]
    else:
        prof += [(r * 0.8, 0.0)]
    n = max(1, beads)
    for k in range(n):
        a = 0.1 + 0.85 * k / n
        bspan = 0.85 / n
        prof += [(r * 0.62, h * a), (r * 1.0, h * (a + bspan * 0.25)), (r * 0.55, h * (a + bspan * 0.5)),
                 (r * 0.85, h * (a + bspan * 0.72)), (r * 0.6, h * (a + bspan * 0.95))]
    prof += [(r * 0.8, h * 0.97), (r * 0.8, h), (0.0, h)]
    L.lathe(lx, ly, z0, prof, seg=seg, mi=mi, mb=mb)


# ============================================================ upholstery
def sectional(mb, pil, x, y, rot, runs, mi=0, mi_leg=1, seat_h=0.46, back_h=0.88, depth=1.0, arm_w=0.2,
              pillows=(), mi_pil=0, seed=0):
    """Modular sectional in its own frame (origin = the back-left corner of the whole piece, seats face -Y ... but
    each run carries its own placement).  runs: list of dicts
        dict(kind='seats'|'corner'|'chaise', x0, y0, x1, y1, face='-Y'|'+X'|'-X'|'+Y', n=2, arm_l=False, arm_r=False,
             back=True)
    in local coordinates; `face` is the direction the seats face.  Cushions are rounded, lightly puffed boxes with
    a welt ring on the seat cushions."""
    L = Loc(mb, x, y, rot)
    base_z = 0.12
    for rn in runs:
        x0, y0, x1, y1 = rn['x0'], rn['y0'], rn['x1'], rn['y1']
        face = rn.get('face', '-Y')
        kind = rn.get('kind', 'seats')
        # frame / base (upholstered plinth) with a small toe recess
        L.rbox(x0 + 0.02, x1 - 0.02, y0 + 0.02, y1 - 0.02, base_z, seat_h - 0.16, 0.035, mi)
        # run axes: 'along' = width direction, 'n' = toward the front
        if face in ('-Y', '+Y'):
            a0, a1, b_back, b_front = x0, x1, (y1 if face == '-Y' else y0), (y0 if face == '-Y' else y1)
        else:
            a0, a1, b_back, b_front = y0, y1, (x0 if face == '+X' else x1), (x1 if face == '+X' else x0)
        sgn = 1 if b_front > b_back else -1

        def R(aa0, aa1, bb0, bb1, z0, z1, r=0.05, puff=0.0, m=mi):
            if face in ('-Y', '+Y'):
                L.rbox(aa0, aa1, bb0, bb1, z0, z1, r, m, puff=puff)
            else:
                L.rbox(bb0, bb1, aa0, aa1, z0, z1, r, m, puff=puff)
        back_t = 0.24 if rn.get('back', True) else 0.0
        al = arm_w if rn.get('arm_l') else 0.0
        ar = arm_w if rn.get('arm_r') else 0.0
        # left/right as seen from the front: for face -Y, 'left' (viewer's left when sitting) is +X ... keep it
        # simple: arm_l at a0, arm_r at a1
        if back_t:
            bb0, bb1 = sorted((b_back, b_back + sgn * 0.20))
            R(a0 + 0.01, a1 - 0.01, bb0, bb1, seat_h - 0.2, back_h - 0.1, 0.06)          # frame back
        if al:
            R(a0, a0 + al, min(b_back, b_front), max(b_back, b_front), base_z, seat_h + 0.16, 0.07, puff=0.2)
        if ar:
            R(a1 - ar, a1, min(b_back, b_front), max(b_back, b_front), base_z, seat_h + 0.16, 0.07, puff=0.2)
        sa0, sa1 = a0 + al, a1 - ar
        n = max(1, rn.get('n', 2))
        sw = (sa1 - sa0) / n
        seat_front = b_front
        seat_back = b_back + sgn * (0.18 if back_t else 0.0)
        for i in range(n):
            c0, c1 = sa0 + i * sw + 0.006, sa0 + (i + 1) * sw - 0.006
            bb0, bb1 = sorted((seat_back, seat_front - sgn * 0.01))
            R(c0, c1, bb0, bb1, seat_h - 0.17, seat_h, 0.07, puff=0.45)                       # seat cushion
            if back_t and kind != 'chaise':
                k0, k1 = sorted((b_back + sgn * 0.12, b_back + sgn * 0.36))
                R(c0 + 0.01, c1 - 0.01, k0, k1, seat_h - 0.03, back_h + 0.04, 0.09, puff=0.55)   # back cushion
        if kind == 'corner' and back_t:
            # the second back along the other side of a corner seat
            side = rn.get('corner_side', 'a1')
            ca = a1 if side == 'a1' else a0
            cb0, cb1 = sorted((ca, ca - 0.20 if side == 'a1' else ca + 0.20))
            R(cb0, cb1, min(b_back, b_front), max(b_back, b_front), seat_h - 0.2, back_h - 0.1, 0.06)
            k0, k1 = sorted((ca - (0.12 if side == 'a1' else -0.12), ca - (0.36 if side == 'a1' else -0.36)))
            R(k0, k1, min(b_back, b_front) + 0.2, max(b_back, b_front) - 0.02, seat_h - 0.03, back_h + 0.04, 0.09, puff=0.55)
        # legs: small dark block feet at the corners
        for (lx, ly) in ((x0 + 0.06, y0 + 0.06), (x1 - 0.06, y0 + 0.06), (x0 + 0.06, y1 - 0.06), (x1 - 0.06, y1 - 0.06)):
            L.box(lx - 0.03, lx + 0.03, ly - 0.03, ly + 0.03, 0.0, base_z, mi_leg)
    for i, (px, py, pz, w, prot, pitch) in enumerate(pillows):
        wx, wy, wz = L.P(px, py, pz)
        pil.pillow_sq(wx, wy, wz, w, w, 0.16, mi_pil, rot=rot + prot, pitch=pitch, seed=seed + i)


# ============================================================ carved Indian furniture
def jhula(mb, bench, cush, x, y, rot=0.0, w=1.95, d=0.78, h=2.30, mi=0, mi_chain=1, mi_cush=0, mi_bolster=0,
          bench_w=1.30, bench_d=0.56, seat_z=0.44):
    """Carved teak Indian swing (photos: a jhula): two trestle frames (a base beam along the depth, two curved
    braces, a turned post with carved blocks and a finial), a cusped crest beam between the posts with a carved
    apron, brass chains, and a carved bench with an openwork back, low turned-baluster arms, a thin mattress and
    two bolsters.  Local frame: +Y = back (toward the wall)."""
    L = Loc(mb, x, y, rot)
    B = Loc(bench, x, y, rot)
    C = Loc(cush, x, y, rot)
    for s in (-1, 1):
        px = s * w / 2
        # base beam (along Y) with scrolled ends
        L.rbox(px - 0.06, px + 0.06, -d / 2, d / 2, 0.0, 0.10, 0.02, mi)
        for e in (-1, 1):
            L.rbox(px - 0.07, px + 0.07, e * d / 2 - 0.07, e * d / 2 + 0.07, 0.0, 0.13, 0.03, mi)
            # curved brace from the base end up to the post
            pts = [(px, e * (d / 2 - 0.06), 0.10), (px, e * (d / 2 - 0.16), 0.30), (px, e * 0.14, 0.52), (px, e * 0.07, 0.62)]
            L.path(pts, 0.035, seg=8, mi=mi)
        # square plinth block, turned post with carved blocks, capital + finial (segment heights scale with h)
        L.box(px - 0.075, px + 0.075, -0.075, 0.075, 0.10, 0.34, mi)
        L.box(px - 0.085, px + 0.085, -0.085, 0.085, 0.30, 0.36, mi)
        z = 0.36
        body = max(0.6, h - 0.36 - 0.30)                  # turned body up to the capital; capital + finial ~0.30
        segs = [(0.22, 'turn'), (0.10, 'block'), (0.22, 'turn'), (0.09, 'block'), (0.22, 'turn'), (0.15, 'block')]
        tot = sum(hh for hh, _ in segs)
        for (hh, kind) in segs:
            hh = hh * body / tot
            if kind == 'turn':
                _turned(L, px, 0.0, z, hh, 0.062, mi, beads=2, foot=False)
            else:
                L.box(px - 0.07, px + 0.07, -0.07, 0.07, z, z + hh, mi)
                L.box(px - 0.078, px + 0.078, -0.078, 0.078, z + hh * 0.4, z + hh * 0.6, mi)
            z += hh
        ztop = z
        L.box(px - 0.09, px + 0.09, -0.09, 0.09, ztop, ztop + 0.05, mi)                      # capital
        L.lathe(px, 0.0, ztop + 0.05, [(0.0, 0.0), (0.06, 0.0), (0.075, 0.04), (0.05, 0.08), (0.062, 0.12), (0.035, 0.17),
                                       (0.042, 0.20), (0.012, 0.24), (0.0, 0.25)], seg=12, mi=mi)
    # crest beam between the posts: a lower rail + a carved cusped cresting + a bracketed, scalloped apron
    zt = h - 0.30 - 0.16
    L.rbox(-w / 2 + 0.05, w / 2 - 0.05, -0.05, 0.05, zt, zt + 0.10, 0.015, mi)
    L.rbox(-w / 2 + 0.04, w / 2 - 0.04, -0.06, 0.06, zt + 0.085, zt + 0.11, 0.01, mi)
    _profile_slab(L, -w / 2 + 0.08, w / 2 - 0.08, -0.03, 0.03, lambda u: zt + 0.10,
                  lambda u: zt + 0.10 + 0.07 + 0.08 * math.sin(math.pi * u) - 0.03 * abs(math.sin(math.pi * u * 9)) ** 0.5, n=72, mi=mi)
    _profile_slab(L, -w / 2 + 0.08, w / 2 - 0.08, -0.025, 0.025,
                  lambda u: zt - 0.02 - 0.06 * abs(math.sin(math.pi * u * 5)) ** 0.6, lambda u: zt, n=60, mi=mi)
    for s_ in (-1, 1):                                                                   # corner brackets
        bx = s_ * (w / 2 - 0.08)
        _profile_slab(L, bx - s_ * 0.0, bx - s_ * 0.22, -0.025, 0.025, lambda u: zt - 0.22 * (1 - u) ** 2, lambda u: zt, n=10, mi=mi)
    # the central bell / ornament
    L.lathe(0.0, 0.0, zt - 0.20, [(0.0, 0.0), (0.03, 0.02), (0.045, 0.08), (0.02, 0.14), (0.01, 0.20), (0.0, 0.2)], seg=10, mi=mi_chain)
    # chains (thin tubes) from the beam to the bench corners
    zb = seat_z + 0.06
    for sx in (-1, 1):
        for sy in (-1, 1):
            p0 = (sx * (bench_w / 2 - 0.05), sy * 0.03, zt)
            p1 = (sx * (bench_w / 2 - 0.05), sy * (bench_d / 2 - 0.06), zb + 0.40 if sy > 0 else zb + 0.02)
            L.tube(p0, p1, 0.006, seg=5, mi=mi_chain)
            L.sphere(p0[0], p0[1], p0[2] - 0.02, 0.018, seg=8, rings=5, mi=mi_chain)
    # bench: plank seat, carved front rail, openwork back with an arched crest, turned-baluster arms
    hw, hd = bench_w / 2, bench_d / 2
    B.rbox(-hw, hw, -hd, hd, seat_z, seat_z + 0.06, 0.01, mi)
    B.box(-hw, hw, -hd - 0.01, -hd + 0.03, seat_z - 0.08, seat_z, mi)                          # front apron
    for i in range(9):
        cx = -hw + 0.07 + i * (bench_w - 0.14) / 8
        B.box(cx - 0.035, cx + 0.035, -hd - 0.02, -hd - 0.005, seat_z - 0.06, seat_z - 0.01, mi)  # carved rosettes
    zb0 = seat_z + 0.06
    back_h = 0.42
    B.box(-hw, hw, hd - 0.05, hd, zb0, zb0 + 0.06, mi)
    for i in range(11):                                                                     # openwork spindles
        cx = -hw + 0.08 + i * (bench_w - 0.16) / 10
        _turned(B, cx, hd - 0.025, zb0 + 0.06, back_h - 0.16, 0.018, mi, beads=2, foot=False)
    B.box(-hw, hw, hd - 0.05, hd, zb0 + back_h - 0.10, zb0 + back_h - 0.04, mi)
    _profile_slab(B, -hw, hw, hd - 0.045, hd - 0.005, lambda u: zb0 + back_h - 0.04,
                  lambda u: zb0 + back_h + 0.03 + 0.10 * math.sin(math.pi * u) ** 1.5 - 0.02 * abs(math.sin(math.pi * u * 7)) ** 0.5,
                  n=56, mi=mi)                                                              # arched crest
    for sx in (-1, 1):
        ax = sx * (hw - 0.03)
        B.box(ax - 0.03, ax + 0.03, -hd, hd, zb0 + 0.20, zb0 + 0.25, mi)                       # arm rail
        for k in range(4):
            yy = -hd + 0.06 + k * (bench_d - 0.12) / 3
            _turned(B, ax, yy, zb0, 0.20, 0.018, mi, beads=1, foot=False)
        B.lathe(ax, -hd + 0.03, zb0 + 0.25, [(0.0, 0.0), (0.03, 0.0), (0.035, 0.03), (0.015, 0.06), (0.0, 0.07)], seg=10, mi=mi)
    # mattress, bolsters, a back cushion or two
    C.rbox(-hw + 0.07, hw - 0.07, -hd + 0.02, hd - 0.06, zb0, zb0 + 0.07, 0.03, mi_cush, puff=0.3)
    for sx in (-1, 1):
        bx = sx * (hw - 0.16)
        C.path([(bx - 0.0, -hd + 0.06, zb0 + 0.14), (bx, hd - 0.10, zb0 + 0.14)], 0.07, seg=14, mi=mi_bolster)
    return zt


def carved_chair(mb, seat, x, y, rot=0.0, w=0.60, d=0.52, seat_z=0.42, back_z=0.95, mi=0, mi_seat=0):
    """Low carved chair (Indian 'rush' chair): turned front legs, square back posts with finials, a carved
    openwork back panel under a cusped crest, a woven rush seat in a frame."""
    L = Loc(mb, x, y, rot)
    S = Loc(seat, x, y, rot)
    hw, hd = w / 2, d / 2
    for sx in (-1, 1):
        _turned(L, sx * (hw - 0.035), -hd + 0.035, 0.0, seat_z - 0.02, 0.034, mi, beads=2)       # front legs
        L.box(sx * (hw - 0.035) - 0.03, sx * (hw - 0.035) + 0.03, hd - 0.065, hd - 0.005, 0.0, back_z, mi)   # back posts
        L.lathe(sx * (hw - 0.035), hd - 0.035, back_z, [(0.0, 0.0), (0.035, 0.0), (0.04, 0.03), (0.02, 0.07), (0.028, 0.10),
                                                         (0.0, 0.13)], seg=10, mi=mi)
        L.box(sx * (hw - 0.035) - 0.025, sx * (hw - 0.035) + 0.025, -hd + 0.01, hd - 0.01, 0.12, 0.16, mi)   # side stretcher
    L.box(-hw + 0.02, hw - 0.02, -hd + 0.01, -hd + 0.06, 0.10, 0.14, mi)                                     # front stretcher
    # seat frame + rush
    L.box(-hw, hw, -hd, -hd + 0.05, seat_z - 0.06, seat_z, mi)
    L.box(-hw, hw, hd - 0.06, hd - 0.01, seat_z - 0.06, seat_z, mi)
    L.box(-hw, -hw + 0.05, -hd, hd, seat_z - 0.06, seat_z, mi)
    L.box(hw - 0.05, hw, -hd, hd, seat_z - 0.06, seat_z, mi)
    S.rbox(-hw + 0.045, hw - 0.045, -hd + 0.045, hd - 0.055, seat_z - 0.04, seat_z + 0.01, 0.015, mi_seat, puff=0.3)
    # back: rails, an openwork carved panel (a lattice of small blocks), a cusped crest
    zb0, zb1 = seat_z + 0.10, back_z - 0.10
    L.box(-hw + 0.06, hw - 0.06, hd - 0.05, hd - 0.02, zb0, zb0 + 0.05, mi)
    rng = random.Random(int(x * 100 + y * 10))
    nx, nz = 7, 5
    for i in range(nx):
        for k in range(nz):
            if (i + k) % 2 and rng.random() < 0.85:
                cx = -hw + 0.08 + (w - 0.16) * (i + 0.5) / nx
                cz = zb0 + 0.05 + (zb1 - zb0 - 0.05) * (k + 0.5) / nz
                L.box(cx - 0.035, cx + 0.035, hd - 0.045, hd - 0.025, cz - 0.03, cz + 0.03, mi)
    for i in range(nx + 1):
        cx = -hw + 0.08 + (w - 0.16) * i / nx
        L.box(cx - 0.008, cx + 0.008, hd - 0.045, hd - 0.025, zb0 + 0.05, zb1, mi)
    _profile_slab(L, -hw + 0.04, hw - 0.04, hd - 0.05, hd - 0.02, lambda u: zb1,
                  lambda u: zb1 + 0.05 + 0.07 * math.sin(math.pi * u) - 0.02 * abs(math.sin(math.pi * u * 5)) ** 0.5, n=40, mi=mi)


def carved_bench(mb, x, y, rot=0.0, w=1.00, d=0.36, h=0.40, mi=0):
    """Low carved table / bench: a thick top with a moulded edge, a carved apron, four turned legs, a low shelf."""
    L = Loc(mb, x, y, rot)
    hw, hd = w / 2, d / 2
    L.rbox(-hw, hw, -hd, hd, h - 0.045, h, 0.01, mi)
    L.box(-hw + 0.04, hw - 0.04, -hd + 0.03, hd - 0.03, h - 0.12, h - 0.045, mi)
    for i in range(10):
        cx = -hw + 0.09 + i * (w - 0.18) / 9
        for sy in (-1, 1):
            L.box(cx - 0.03, cx + 0.03, sy * (hd - 0.025) - 0.006, sy * (hd - 0.025) + 0.006, h - 0.11, h - 0.055, mi)
    for sx in (-1, 1):
        for sy in (-1, 1):
            _turned(L, sx * (hw - 0.06), sy * (hd - 0.05), 0.0, h - 0.12, 0.035, mi, beads=2)
    L.box(-hw + 0.06, hw - 0.06, -hd + 0.05, hd - 0.05, 0.10, 0.125, mi)


# ============================================================ tables / media
def scroll_table(glass, iron, x, y, rot=0.0, w=1.20, d=0.62, h=0.45, clip=0.12, shape='rect', mi_glass=0, mi_iron=0,
                 bevel=0.012):
    """Glass-top table on a scrolled wrought-iron base: a clipped-corner (or round) bevelled glass top on a flat
    iron apron ring, four S-scroll legs with C-scroll feet and a crossed stretcher."""
    G = Loc(glass, x, y, rot)
    I_ = Loc(iron, x, y, rot)
    hw, hd = w / 2, d / 2
    if shape == 'round':
        pts = [(hw * math.cos(2 * math.pi * i / 40), hd * math.sin(2 * math.pi * i / 40)) for i in range(40)]
    else:
        c = clip
        pts = [(-hw + c, -hd), (hw - c, -hd), (hw, -hd + c), (hw, hd - c), (hw - c, hd), (-hw + c, hd), (-hw, hd - c), (-hw, -hd + c)]
    t = 0.012
    G.prism(pts, h - t, h, mi_glass)                      # one closed slab (no coplanar faces: they render black)
    # apron ring under the glass (flat bar)
    ring = [(px * 0.86, py * 0.80) for px, py in pts]
    for i in range(len(ring)):
        a, b = ring[i], ring[(i + 1) % len(ring)]
        I_.path([(a[0], a[1], h - t - 0.012), (b[0], b[1], h - t - 0.012)], 0.008, seg=6, mi=mi_iron)
    lx, ly = hw * 0.72, hd * 0.62
    for sx in (-1, 1):
        for sy in (-1, 1):
            top = (sx * lx, sy * ly, h - t - 0.012)
            pts_l = [top, (sx * lx * 1.02, sy * ly * 1.05, h * 0.78), (sx * lx * 0.88, sy * ly * 0.9, h * 0.55),
                     (sx * lx * 0.95, sy * ly * 0.98, h * 0.30), (sx * lx * 1.12, sy * ly * 1.12, h * 0.10),
                     (sx * lx * 1.22, sy * ly * 1.2, 0.03), (sx * lx * 1.15, sy * ly * 1.13, 0.012)]
            I_.path(pts_l, 0.011, seg=6, mi=mi_iron)
            # C-scroll at the knee (a small spiral)
            cxk, cyk, czk = sx * lx * 0.9, sy * ly * 0.92, h * 0.62
            sp = []
            for k in range(14):
                a = k / 13 * 4.2
                r = 0.05 * (1 - k / 16)
                sp.append((cxk - sx * r * math.cos(a) * 0.7, cyk - sy * r * math.cos(a) * 0.7, czk + r * math.sin(a)))
            I_.path(sp, 0.006, seg=5, mi=mi_iron)
            I_.path([(sx * lx * 0.95, sy * ly * 0.98, h * 0.30), (sx * lx * 0.4, sy * ly * 0.35, h * 0.22), (0.0, 0.0, h * 0.2)], 0.007,
                    seg=5, mi=mi_iron)
    I_.lathe(0.0, 0.0, h * 0.17, [(0.0, 0.0), (0.03, 0.0), (0.04, 0.03), (0.025, 0.06), (0.0, 0.07)], seg=10, mi=mi_iron)


def media_console(mb, glass, x, y, rot=0.0, w=1.02, d=0.46, h=0.56, mi=0, mi_glass=0, mi_dark=1):
    """TV stand (photo: a black console): rounded-edge top overhanging a carcass, a plinth, a large smoked-glass
    door on the left 2/3 (with a player visible behind) and a solid door on the right."""
    L = Loc(mb, x, y, rot)
    G = Loc(glass, x, y, rot)
    hw, hd = w / 2, d / 2
    L.rbox(-hw, hw, -hd, hd, h - 0.035, h, 0.015, mi)                                     # top
    L.rbox(-hw + 0.03, hw - 0.03, -hd + 0.03, hd - 0.02, 0.05, h - 0.035, 0.01, mi)        # carcass
    L.rbox(-hw - 0.005, hw + 0.005, -hd - 0.005, hd - 0.02, 0.0, 0.055, 0.012, mi)        # plinth
    xs = -hw + 0.03 + (w - 0.06) * 0.66
    L.box(-hw + 0.03, xs - 0.01, -hd + 0.02, -hd + 0.03, 0.08, h - 0.06, mi_dark)         # recess behind the glass
    G.box(-hw + 0.045, xs - 0.02, -hd + 0.012, -hd + 0.02, 0.085, h - 0.065, mi_glass)
    L.box(-hw + 0.1, xs - 0.1, -hd + 0.035, -hd + 0.30, 0.25, 0.30, mi)                  # a player on the shelf
    L.rbox(xs + 0.005, hw - 0.045, -hd + 0.01, -hd + 0.035, 0.08, h - 0.06, 0.006, mi)   # solid door
    L.box(xs - 0.012, xs + 0.002, -hd + 0.005, -hd + 0.03, 0.08, h - 0.06, mi)            # centre stile


def flat_tv(mb, x, y, rot=0.0, w=1.23, h=0.72, z=0.62, mi_body=0, mi_screen=1, stand=True, logo=None):
    """Flat panel (bezel + screen) on a small pedestal; local front = -Y."""
    L = Loc(mb, x, y, rot)
    hw = w / 2
    L.box(-hw, hw, -0.02, 0.03, z, z + h, mi_body)
    L.box(-hw + 0.012, hw - 0.012, -0.023, -0.02, z + 0.02, z + h - 0.012, mi_screen)
    L.box(-0.2, 0.2, -0.015, 0.03, z - 0.012, z + 0.03, mi_body)                            # bottom bar / logo strip
    if stand:
        L.box(-0.05, 0.05, 0.0, 0.05, z - 0.07, z, mi_body)
        L.rbox(-0.2, 0.2, -0.12, 0.12, z - 0.085, z - 0.07, 0.01, mi_body)


def parquet_table(top, wood, x, y, rot=0.0, w=1.62, d=0.96, h=0.76, mi_top=0, mi_wood=0, blocks=True, mi_top2=None):
    """Dining table: a thick top of four quartered plank squares (the grain turns 90 deg square to square, drawn as
    separate boards so the shader grain follows each: boards running along local Y use `mi_top2`), a block-carved
    apron, square tapered legs."""
    mi_top2 = mi_top if mi_top2 is None else mi_top2
    T = Loc(top, x, y, rot)
    L = Loc(wood, x, y, rot)
    hw, hd = w / 2, d / 2
    tt = 0.05
    # top: an edge frame + quartered squares of boards
    f = 0.06
    L.box(-hw, hw, -hd, -hd + f, h - tt, h, mi_wood); L.box(-hw, hw, hd - f, hd, h - tt, h, mi_wood)
    L.box(-hw, -hw + f, -hd + f, hd - f, h - tt, h, mi_wood); L.box(hw - f, hw, -hd + f, hd - f, h - tt, h, mi_wood)
    nq = 3 if w / d > 1.5 else 2
    qw = (w - 2 * f) / nq
    qd = (d - 2 * f) / 2
    for i in range(nq):
        for j in range(2):
            x0, y0 = -hw + f + i * qw, -hd + f + j * qd
            nb = 5
            vertical = (i + j) % 2 == 0
            for k in range(nb):
                if vertical:
                    a0, a1 = x0 + k * qw / nb + 0.001, x0 + (k + 1) * qw / nb - 0.001
                    T.box(a0, a1, y0 + 0.001, y0 + qd - 0.001, h - tt + 0.001, h + 0.0015, mi_top2)
                else:
                    b0, b1 = y0 + k * qd / nb + 0.001, y0 + (k + 1) * qd / nb - 0.001
                    T.box(x0 + 0.001, x0 + qw - 0.001, b0, b1, h - tt + 0.001, h + 0.0015, mi_top)
    # apron with carved blocks
    ah = 0.11
    za0 = h - tt - ah
    L.box(-hw + 0.05, hw - 0.05, -hd + 0.05, -hd + 0.075, za0, h - tt, mi_wood)
    L.box(-hw + 0.05, hw - 0.05, hd - 0.075, hd - 0.05, za0, h - tt, mi_wood)
    L.box(-hw + 0.05, -hw + 0.075, -hd + 0.05, hd - 0.05, za0, h - tt, mi_wood)
    L.box(hw - 0.075, hw - 0.05, -hd + 0.05, hd - 0.05, za0, h - tt, mi_wood)
    if blocks:
        nbx = int((w - 0.3) / 0.10)
        for i in range(nbx):
            cx = -hw + 0.15 + (w - 0.3) * (i + 0.5) / nbx
            for sy in (-1, 1):
                yy = sy * (hd - 0.05)
                out = sy * 0.018
                L.box(cx - 0.035, cx + 0.035, min(yy, yy + out), max(yy, yy + out), za0 + 0.02, h - tt - 0.02, mi_wood)
        nby = int((d - 0.3) / 0.10)
        for i in range(nby):
            cy = -hd + 0.15 + (d - 0.3) * (i + 0.5) / nby
            for sx in (-1, 1):
                xx = sx * (hw - 0.05)
                out = sx * 0.018
                L.box(min(xx, xx + out), max(xx, xx + out), cy - 0.035, cy + 0.035, za0 + 0.02, h - tt - 0.02, mi_wood)
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = sx * (hw - 0.10), sy * (hd - 0.10)
            L.box(cx - 0.045, cx + 0.045, cy - 0.045, cy + 0.045, 0.02, h - tt, mi_wood)
            L.box(cx - 0.038, cx + 0.038, cy - 0.038, cy + 0.038, 0.0, 0.02, mi_wood)


def panel_back_chair(mb, seat, x, y, rot=0.0, w=0.46, d=0.54, seat_z=0.48, back_z=1.00, mi=0, mi_seat=0, curve=0.045,
                     leg=0.038):
    """Dining chair (photo: espresso 'panel back' chairs): rear legs that sweep up in one curve into raked back
    posts, a concave back of four wide panels (two over two, split by a centre groove and a rail), square front
    legs tapering to the floor, side and front aprons, and a thick upholstered seat with rounded edges."""
    L = Loc(mb, x, y, rot)
    S = Loc(seat, x, y, rot)
    hw, hd = w / 2, d / 2
    t = leg / 2
    for sx in (-1, 1):
        lx = sx * (hw - t - 0.005)
        # front leg: square, tapering from leg to 0.8 leg at the floor
        L.sweep([[(lx - t * 0.8, -hd + 0.02 - t * 0.8, 0.0), (lx + t * 0.8, -hd + 0.02 - t * 0.8, 0.0),
                  (lx + t * 0.8, -hd + 0.02 + t * 0.8, 0.0), (lx - t * 0.8, -hd + 0.02 + t * 0.8, 0.0)],
                 [(lx - t, -hd + 0.02 - t, seat_z - 0.03), (lx + t, -hd + 0.02 - t, seat_z - 0.03),
                  (lx + t, -hd + 0.02 + t, seat_z - 0.03), (lx - t, -hd + 0.02 + t, seat_z - 0.03)]], mi)
        # rear leg + back post: one swept curve (splayed foot, straight to the seat, then raked back and bowed)
        pts = []
        for i in range(13):
            s_ = i / 12
            z = back_z * s_
            if z < seat_z:
                yy = hd - 0.03 + 0.06 * (1 - z / seat_z) ** 2          # splayed rear foot
            else:
                q = (z - seat_z) / (back_z - seat_z)
                yy = hd - 0.03 + 0.07 * q ** 1.2                        # raked back
            pts.append((lx, yy, z))
        secs = []
        for k, (px, py, pz) in enumerate(pts):
            tt = t * (0.85 if k == 0 else 1.0)
            secs.append([(px - tt, py - tt, pz), (px + tt, py - tt, pz), (px + tt, py + tt, pz), (px - tt, py + tt, pz)])
        L.sweep(secs, mi)
    # aprons
    L.box(-hw + 0.02, hw - 0.02, -hd + 0.005, -hd + 0.028, seat_z - 0.10, seat_z - 0.035, mi)
    L.box(-hw + 0.02, hw - 0.02, hd - 0.05, hd - 0.028, seat_z - 0.10, seat_z - 0.035, mi)
    for sx in (-1, 1):
        ax = sx * (hw - t - 0.005)
        L.box(ax - 0.011, ax + 0.011, -hd + 0.03, hd - 0.04, seat_z - 0.10, seat_z - 0.035, mi)
    # concave back: four panels between the posts, following the posts' rake
    zb0, zmid, zb1 = seat_z + 0.13, seat_z + 0.33, back_z - 0.015
    inner = hw - leg - 0.005
    for (z0, z1) in ((zb0, zmid - 0.008), (zmid + 0.008, zb1)):
        for (a0, a1) in ((-inner, -0.004), (0.004, inner)):
            n = 8
            secs = []
            for i in range(n + 1):
                xx = a0 + (a1 - a0) * i / n
                bow = curve * (1 - (xx / hw) ** 2)
                def yz(z):
                    q = (z - seat_z) / (back_z - seat_z)
                    return hd - 0.03 + 0.07 * q ** 1.2 + bow
                secs.append([(xx, yz(z0) - 0.010, z0), (xx, yz(z0) + 0.010, z0), (xx, yz(z1) + 0.010, z1), (xx, yz(z1) - 0.010, z1)])
            L.sweep(secs, mi)
    # upholstered seat: a rounded pad, slightly domed, over the aprons
    S.rbox(-hw + 0.012, hw - 0.012, -hd + 0.0, hd - 0.035, seat_z - 0.04, seat_z + 0.035, 0.03, mi_seat, puff=0.35)


# ============================================================ light fixtures
def bell_chandelier(body, glass, x, y, zc, drop=0.78, r=0.30, arms=5, mi=0, mi_glass=0, chain=True):
    """Chain-hung chandelier (photo: brushed nickel, 5 arms, clear ribbed bells facing down): canopy, chain,
    a column with a ball, arms that curve out and up, then hook down to downward bell shades.  Returns the
    lamp positions (for point lights).  zc = ceiling height; drop = ceiling to the bottom of the shades."""
    zb = zc - drop                        # bottom of the shades
    body.cylinder(x, y, zc - 0.035, zc, 0.065, 0.06, seg=20, mi=mi)
    body.cylinder(x, y, zc - 0.05, zc - 0.035, 0.012, seg=8, mi=mi)
    zcol = zb + 0.10
    if chain:
        n = int((zc - 0.05 - (zcol + 0.225)) / 0.028) + 1
        for k in range(max(0, n)):
            zz = zc - 0.05 - (k + 0.5) * 0.028
            ang = (k % 2) * math.pi / 2
            ca, sa = math.cos(ang), math.sin(ang)
            pts = []
            for i in range(9):
                t = 2 * math.pi * i / 8
                pts.append((x + 0.009 * math.cos(t) * ca, y + 0.009 * math.cos(t) * sa, zz + 0.016 * math.sin(t)))
            body.path_tube(pts, 0.0028, seg=4, mi=mi)
    # column: loop, cap, ball, stem, bottom finial (photo: the column is ~2x a shade's height)
    body.lathe(x, y, zcol, [(0.0, -0.05), (0.010, -0.047), (0.016, -0.02), (0.015, 0.0), (0.026, 0.015), (0.038, 0.05), (0.026, 0.09),
                            (0.011, 0.11), (0.011, 0.20), (0.017, 0.215), (0.017, 0.225), (0.0, 0.225)], seg=18, mi=mi)
    lamps = []
    for k in range(arms):
        a = 2 * math.pi * k / arms + 0.3
        ca, sa = math.cos(a), math.sin(a)
        pts = []
        for i in range(13):
            t = i / 12
            rr = 0.03 + (r - 0.03) * math.sin(t * math.pi * 0.62) / math.sin(math.pi * 0.62)
            zz = zcol + 0.06 + 0.12 * math.sin(t * math.pi * 0.9)
            pts.append((x + rr * ca, y + rr * sa, zz))
        pts += [(x + (r + 0.015) * ca, y + (r + 0.015) * sa, zcol + 0.14), (x + (r + 0.02) * ca, y + (r + 0.02) * sa, zb + 0.16)]
        body.path_tube(pts, 0.007, seg=6, mi=mi)
        ex, ey = x + (r + 0.02) * ca, y + (r + 0.02) * sa
        body.lathe(ex, ey, zb + 0.13, [(0.0, 0.0), (0.03, 0.0), (0.032, 0.02), (0.018, 0.035), (0.0, 0.035)], seg=12, mi=mi)
        # ribbed bell (prismatic, open bottom, a flared rim): outer + inner wall
        prof = [(0.025, 0.14), (0.045, 0.13), (0.065, 0.10), (0.080, 0.06), (0.088, 0.025), (0.094, 0.004), (0.095, 0.0),
                (0.089, 0.0), (0.087, 0.012), (0.080, 0.04), (0.066, 0.08), (0.048, 0.115), (0.024, 0.132)]
        glass.lathe(ex, ey, zb, prof, seg=28, mi=mi_glass)
        lamps.append((ex, ey, zb + 0.07))
    return lamps


def hugger_fan(body, blades, glass, x, y, zc, blade_r=0.66, n_blades=5, lights=4, mi=0, mi_blade=0, mi_glass=0, rot=0.3):
    """Flush-mount ('hugger') ceiling fan: canopy, a domed motor housing with vent slots and a trim ring, blades on
    curved irons, and a 4-tulip light kit hanging under a switch cup.  Returns the lamp positions."""
    z = zc
    body.cylinder(x, y, z - 0.03, z, 0.085, 0.08, seg=24, mi=mi)
    body.lathe(x, y, z - 0.19, [(0.0, 0.0), (0.06, 0.0), (0.13, 0.015), (0.175, 0.045), (0.19, 0.075), (0.185, 0.10), (0.17, 0.12),
                                (0.12, 0.15), (0.09, 0.16), (0.0, 0.16)], seg=32, mi=mi)
    for k in range(18):                                             # vent slots (raised ribs) around the housing
        a = 2 * math.pi * k / 18
        ca, sa = math.cos(a), math.sin(a)
        body.tube((x + 0.178 * ca, y + 0.178 * sa, z - 0.11), (x + 0.15 * ca, y + 0.15 * sa, z - 0.055), 0.006, 0.006, seg=4, mi=mi)
    zb = z - 0.175
    for k in range(n_blades):
        a = 2 * math.pi * k / n_blades + rot
        ca, sa = math.cos(a), math.sin(a)
        # iron: a curved flat bracket from the motor rim to under the blade
        pts = [(x + 0.15 * ca, y + 0.15 * sa, zb + 0.02), (x + 0.22 * ca - 0.02 * sa, y + 0.22 * sa + 0.02 * ca, zb - 0.005),
               (x + 0.33 * ca - 0.03 * sa, y + 0.33 * sa + 0.03 * ca, zb - 0.01)]
        body.path_tube(pts, 0.011, seg=6, mi=mi)
        # blade: rounded-end plank, slight pitch (10 deg)
        r0, r1, bw = 0.25, blade_r, 0.075
        pitch = math.radians(10)
        secs = []
        m = 12
        for i in range(m + 1):
            t = i / m
            rr = r0 + (r1 - r0) * t
            ww = bw * (1.0 if t < 0.85 else math.sqrt(max(0.0, 1 - ((t - 0.85) / 0.15) ** 2)) * 0.9 + 0.1)
            ww = bw * (0.92 + 0.08 * t) if t < 0.85 else ww
            sec = []
            for (u, v) in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                off = u * ww
                zz = zb - 0.012 + v * 0.005 + off * math.sin(pitch)
                sec.append((x + rr * ca - off * sa, y + rr * sa + off * ca, zz))
            secs.append(sec)
        blades.sweep(secs, mi_blade)
    # light kit
    zs = zb - 0.03
    body.lathe(x, y, zs - 0.08, [(0.0, 0.0), (0.05, 0.0), (0.09, 0.03), (0.10, 0.06), (0.09, 0.08), (0.0, 0.08)], seg=24, mi=mi)
    body.lathe(x, y, zs - 0.13, [(0.0, 0.0), (0.012, 0.0), (0.02, 0.03), (0.012, 0.05), (0.0, 0.05)], seg=10, mi=mi)
    lamps = []
    for k in range(lights):
        a = 2 * math.pi * k / lights + rot + 0.5
        ca, sa = math.cos(a), math.sin(a)
        ax, ay = x + 0.13 * ca, y + 0.13 * sa
        body.path_tube([(x + 0.07 * ca, y + 0.07 * sa, zs - 0.05), (ax, ay, zs - 0.07), (ax + 0.01 * ca, ay + 0.01 * sa, zs - 0.10)], 0.009,
                       seg=6, mi=mi)
        # tulip (open bottom, flared scalloped rim), tilted outward ~25 deg: approximated with an offset lathe stack
        tilt = math.radians(25)
        cx, cy, cz = ax + 0.02 * ca, ay + 0.02 * sa, zs - 0.12
        prof = [(0.025, 0.0), (0.04, -0.02), (0.055, -0.06), (0.06, -0.10), (0.07, -0.13), (0.078, -0.145),
                (0.072, -0.145), (0.064, -0.13), (0.054, -0.10), (0.049, -0.06), (0.035, -0.02), (0.02, -0.004)]
        secs = []
        seg = 24
        for (r, dz) in prof:
            sec = []
            for i in range(seg):
                t = 2 * math.pi * i / seg
                sc = 1.0 + (0.06 * math.cos(6 * t) if dz < -0.12 else 0.0)
                px, py = r * sc * math.cos(t), r * sc * math.sin(t)
                # tilt about the tangential axis: rotate (radial, z) by tilt
                rad = px * ca + py * sa
                tan_ = -px * sa + py * ca
                rad2 = rad * math.cos(tilt) - dz * math.sin(tilt)
                z2 = rad * math.sin(tilt) + dz * math.cos(tilt)
                sec.append((cx + rad2 * ca - tan_ * sa, cy + rad2 * sa + tan_ * ca, cz + z2))
            secs.append(sec)
        glass.sweep(secs, mi_glass, close=False, caps=False)
        lamps.append((cx + 0.03 * ca, cy + 0.03 * sa, cz - 0.07))
    # pull chains
    for (dx, L) in ((0.01, 0.14), (-0.01, 0.10)):
        body.tube((x + dx, y, zs - 0.13), (x + dx, y, zs - 0.13 - L), 0.0015, 0.0015, seg=4, mi=mi)
        body.sphere((x + dx, y, zs - 0.13 - L - 0.008), 0.008, seg=8, rings=5, mi=mi)
    return lamps


def wall_clock(mb, x, b, z, r=0.21, along='X', face=-1, mi_rim=0, mi_face=1, mi_ink=2):
    """Round wall clock on a wall plane (along 'X': wall at y=b; face = the room side sign): a moulded wooden rim,
    a white dial, black Roman numerals, a minute track and hands."""
    def P(u, d, w):
        # u along the wall, d out of the wall (toward the room), w up
        if along == 'X':
            return (x + u, b + face * d, z + w)
        return (b + face * d, x + u, z + w)
    n = 48
    rim = [(r * 0.86, 0.004), (r * 0.86, 0.040), (r * 0.90, 0.050), (r * 0.97, 0.046), (r * 1.0, 0.030), (r * 0.99, 0.004)]
    secs = []
    for i in range(n):
        t = 2 * math.pi * i / n
        secs.append([P(rr * math.cos(t), dd, rr * math.sin(t)) for (rr, dd) in rim])
    mb.sweep(secs, mi_rim, close=True, caps=False)
    # dial
    for i in range(n):
        t0, t1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
        mb._add([P(0, 0.028, 0), P(r * 0.87 * math.cos(t0), 0.028, r * 0.87 * math.sin(t0)), P(r * 0.87 * math.cos(t1), 0.028, r * 0.87 * math.sin(t1))],
                [(0, 1, 2)], mi_face)
    # numerals: I / V / X strokes
    romans = ['XII', 'I', 'II', 'III', 'IIII', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI']
    hh = r * 0.13
    for k, s in enumerate(romans):
        ang = math.pi / 2 - 2 * math.pi * k / 12
        rr = r * 0.70
        cu, cw = rr * math.cos(ang), rr * math.sin(ang)
        # numerals stand upright relative to the rim (rotated so their base faces the centre)
        up = (math.cos(ang), math.sin(ang))
        rt = (math.sin(ang), -math.cos(ang))
        sw = hh * 0.12
        width = 0.0
        glyphs = []
        for ch in s:
            glyphs.append((ch, width))
            width += hh * (0.22 if ch == 'I' else 0.55)
        x0 = -width / 2
        for ch, off in glyphs:
            gx = x0 + off
            strokes = []
            if ch == 'I':
                strokes = [((gx + hh * 0.08, -hh / 2), (gx + hh * 0.08, hh / 2))]
            elif ch == 'V':
                strokes = [((gx, hh / 2), (gx + hh * 0.24, -hh / 2)), ((gx + hh * 0.24, -hh / 2), (gx + hh * 0.48, hh / 2))]
            elif ch == 'X':
                strokes = [((gx, hh / 2), (gx + hh * 0.48, -hh / 2)), ((gx, -hh / 2), (gx + hh * 0.48, hh / 2))]
            for (p0, p1) in strokes:
                def W(p):
                    return (cu + p[0] * rt[0] + p[1] * up[0], cw + p[0] * rt[1] + p[1] * up[1])
                a0, a1 = W(p0), W(p1)
                du, dw = a1[0] - a0[0], a1[1] - a0[1]
                ln = math.hypot(du, dw) or 1.0
                nu, nw = -dw / ln * sw / 2, du / ln * sw / 2
                mb.quad(P(a0[0] + nu, 0.0295, a0[1] + nw), P(a1[0] + nu, 0.0295, a1[1] + nw), P(a1[0] - nu, 0.0295, a1[1] - nw),
                        P(a0[0] - nu, 0.0295, a0[1] - nw), mi_ink)
    # minute track ticks
    for k in range(60):
        ang = 2 * math.pi * k / 60
        r0_, r1_ = r * 0.80, r * (0.84 if k % 5 else 0.85)
        ca, sa = math.cos(ang), math.sin(ang)
        wdt = 0.0015 if k % 5 else 0.003
        mb.quad(P(r0_ * ca - wdt * sa, 0.0295, r0_ * sa + wdt * ca), P(r1_ * ca - wdt * sa, 0.0295, r1_ * sa + wdt * ca),
                P(r1_ * ca + wdt * sa, 0.0295, r1_ * sa - wdt * ca), P(r0_ * ca + wdt * sa, 0.0295, r0_ * sa - wdt * ca), mi_ink)
    # hands (10:10)
    for (ang, L, wdt, dd) in ((math.radians(150), r * 0.45, 0.009, 0.032), (math.radians(30), r * 0.66, 0.006, 0.035),
                              (math.radians(-100), r * 0.72, 0.0015, 0.037)):
        ca, sa = math.cos(ang), math.sin(ang)
        mb.quad(P(-0.02 * ca - wdt * sa, dd, -0.02 * sa + wdt * ca), P(L * ca - wdt * 0.3 * sa, dd, L * sa + wdt * 0.3 * ca),
                P(L * ca + wdt * 0.3 * sa, dd, L * sa - wdt * 0.3 * ca), P(-0.02 * ca + wdt * sa, dd, -0.02 * sa - wdt * ca), mi_ink)
    return P


def register(mb, x, y, z, w=0.36, d=0.15, along='X', ceiling=True, louvres=12, mi=0, mi_dark=1):
    """HVAC supply register (white stamped steel): a flanged frame and angled louvres over a dark duct.  Ceiling
    registers hang at z (the ceiling underside) facing down; `along` = the long axis."""
    hw, hd = w / 2, d / 2
    if along == 'X':
        def B(a0, a1, b0, b1, z0, z1, m):
            mb.box(x + a0, x + a1, y + b0, y + b1, z0, z1, m)
    else:
        def B(a0, a1, b0, b1, z0, z1, m):
            mb.box(x + b0, x + b1, y + a0, y + a1, z0, z1, m)
    zt = z
    B(-hw - 0.025, hw + 0.025, -hd - 0.025, -hd, zt - 0.008, zt, mi)
    B(-hw - 0.025, hw + 0.025, hd, hd + 0.025, zt - 0.008, zt, mi)
    B(-hw - 0.025, -hw, -hd, hd, zt - 0.008, zt, mi)
    B(hw, hw + 0.025, -hd, hd, zt - 0.008, zt, mi)
    B(-hw, hw, -hd, hd, zt + 0.02, zt + 0.021, mi_dark)
    for k in range(louvres):
        c = -hd + d * (k + 0.5) / louvres
        B(-hw, hw, c - 0.004, c + 0.004, zt - 0.016, zt - 0.002, mi)
    B(-0.004, 0.004, -hd, hd, zt - 0.014, zt - 0.001, mi)


def h_blinds(mb, along, a0, a1, b, s, z0, z1, pitch=0.045, slat=0.05, tilt=0.35, mi=0, mi_cord=None, head=0.05):
    """2-inch horizontal blinds in front of a window at plane b (room side s): head rail at z1, slats down to z0,
    a bottom rail, two ladder tapes and a wand."""
    mi_cord = mi if mi_cord is None else mi_cord
    def B(u0, u1, d0, d1, zz0, zz1, m=mi):
        lo, hi = sorted((b + s * d0, b + s * d1))
        if along == 'X':
            mb.box(u0, u1, lo, hi, zz0, zz1, m)
        else:
            mb.box(lo, hi, u0, u1, zz0, zz1, m)
    B(a0, a1, 0.005, 0.005 + head, z1 - head, z1)                                              # head rail
    n = max(1, int((z1 - head - z0 - 0.03) / pitch))
    ct, st = math.cos(tilt), math.sin(tilt)
    for k in range(n):
        zc = z1 - head - 0.02 - k * pitch
        dc = 0.005 + head / 2
        # a tilted slat: cross-section rotated by `tilt`
        hw = slat / 2
        dd0, zz0_ = dc - hw * ct, zc - hw * st
        dd1, zz1_ = dc + hw * ct, zc + hw * st
        t = 0.0025
        for (u0, u1) in ((a0 + 0.004, a1 - 0.004),):
            lo0, lo1 = b + s * dd0, b + s * dd1
            if along == 'X':
                P = lambda u, dpos, zz: (u, dpos, zz)
            else:
                P = lambda u, dpos, zz: (dpos, u, zz)
            mb.hexa([P(u0, lo0, zz0_ - t), P(u1, lo0, zz0_ - t), P(u1, lo1, zz1_ - t), P(u0, lo1, zz1_ - t),
                     P(u0, lo0, zz0_ + t), P(u1, lo0, zz0_ + t), P(u1, lo1, zz1_ + t), P(u0, lo1, zz1_ + t)], mi)
    zb = z1 - head - 0.02 - n * pitch
    B(a0 + 0.002, a1 - 0.002, 0.012, 0.012 + 0.035, zb - 0.012, zb + 0.008)                       # bottom rail
    for f in (0.2, 0.8):                                                                             # ladder cords
        u = a0 + (a1 - a0) * f
        B(u - 0.002, u + 0.002, 0.004, 0.006, zb, z1 - head, mi_cord)
        B(u - 0.002, u + 0.002, 0.004 + head, 0.006 + head, zb, z1 - head, mi_cord)
    uw = a0 + 0.04
    B(uw - 0.004, uw + 0.004, head + 0.012, head + 0.02, z1 - head - 0.55, z1 - head, mi)             # wand


def v_blinds(mb, along, a0, a1, b, s, z0, z1, stack_at='a1', stack_w=0.30, n=None, vane=0.089, mi=0, head=0.05):
    """Vertical blinds drawn open and stacked at one end of a head rail (a0..a1 along the wall plane b, room side
    s): a head rail across the full width, vanes (3.5") turned nearly perpendicular to the glass in the stack."""
    def B(u0, u1, d0, d1, zz0, zz1):
        lo, hi = sorted((b + s * d0, b + s * d1))
        if along == 'X':
            mb.box(u0, u1, lo, hi, zz0, zz1, mi)
        else:
            mb.box(lo, hi, u0, u1, zz0, zz1, mi)
    B(a0, a1, 0.01, 0.01 + head, z1 - head, z1)
    n = n or max(4, int(stack_w / 0.018))
    for k in range(n):
        u = (a1 - 0.01 - k * stack_w / n) if stack_at == 'a1' else (a0 + 0.01 + k * stack_w / n)
        ang = math.radians(70 + 12 * math.sin(k * 1.7))
        du, dd = vane / 2 * math.cos(ang), vane / 2 * math.sin(ang)
        dc = 0.01 + head / 2 + 0.01
        t = 0.0012
        zt, zb = z1 - head - 0.005, z0
        if along == 'X':
            P = lambda uu, d_, zz: (uu, b + s * d_, zz)
        else:
            P = lambda uu, d_, zz: (b + s * d_, uu, zz)
        pa, pb = (u - du, dc - dd), (u + du, dc + dd)
        nx_, ny_ = -(pb[1] - pa[1]), (pb[0] - pa[0])
        ln = math.hypot(nx_, ny_) or 1
        nx_, ny_ = nx_ / ln * t, ny_ / ln * t
        mb.hexa([P(pa[0] - nx_, pa[1] - ny_, zb), P(pb[0] - nx_, pb[1] - ny_, zb), P(pb[0] + nx_, pb[1] + ny_, zb), P(pa[0] + nx_, pa[1] + ny_, zb),
                 P(pa[0] - nx_, pa[1] - ny_, zt), P(pb[0] - nx_, pb[1] - ny_, zt), P(pb[0] + nx_, pb[1] + ny_, zt), P(pa[0] + nx_, pa[1] + ny_, zt)], mi)


def cornice(mb, along, a0, a1, b, s, z0, z1, depth=0.14, mi=0):
    """Valance / cornice box over a door or window: a face board with a rounded top edge, returns to the wall."""
    def B(u0, u1, d0, d1, zz0, zz1):
        lo, hi = sorted((b + s * d0, b + s * d1))
        if along == 'X':
            mb.box(u0, u1, lo, hi, zz0, zz1, mi)
        else:
            mb.box(lo, hi, u0, u1, zz0, zz1, mi)
    B(a0, a1, depth - 0.02, depth, z0, z1 - 0.012)
    B(a0 - 0.004, a1 + 0.004, depth - 0.024, depth + 0.004, z1 - 0.014, z1)
    B(a0, a1, 0.002, depth, z1 - 0.02, z1)
    B(a0, a0 + 0.02, 0.002, depth, z0, z1)
    B(a1 - 0.02, a1, 0.002, depth, z0, z1)


def rod(mb, along, a0, a1, b, s, z, out=0.10, r=0.011, finial=0.028, mi=0, brackets=None):
    """Curtain rod at height z, `out` from the wall plane b (room side s), ball finials and wall brackets."""
    if along == 'X':
        def P(a, d, zz):
            return (a, b + s * d, zz)
    else:
        def P(a, d, zz):
            return (b + s * d, a, zz)
    mb.tube(P(a0, out, z), P(a1, out, z), r, r, seg=10, mi=mi)
    for a in (a0, a1):
        mb.sphere(P(a, out, z), finial, seg=12, rings=8, mi=mi)
    for a in (brackets if brackets is not None else (a0 + 0.08, (a0 + a1) / 2, a1 - 0.08)):
        mb.tube(P(a, 0.004, z + 0.03), P(a, out, z + 0.005), 0.007, 0.007, seg=6, mi=mi)
        bx, by, _ = P(a, 0.004, 0.0)
        if along == 'X':
            mb.box(bx - 0.018, bx + 0.018, min(by, b + s * 0.012), max(by, b + s * 0.012), z - 0.01, z + 0.07, mi)
        else:
            mb.box(min(bx, b + s * 0.012), max(bx, b + s * 0.012), by - 0.018, by + 0.018, z - 0.01, z + 0.07, mi)


def grommet_panel(mb, gm, along, a0, a1, b, s, z_rod, z_floor, out=0.10, folds=None, depth=0.06, mi=0, mi_grommet=0,
                  tie=None, tie_mb=None, mi_tie=0, seed=0, puddle=0.02):
    """Grommet-top curtain panel hanging from a rod at z_rod (out from the wall plane b), rolling in deep regular
    folds from the grommets down to the floor.  tie = (a_tie, z_tie, gather) gathers the lower part toward a_tie
    (a tie-back sash at z_tie, drawn into tie_mb).  Grommets are rings on the rod."""
    rng = random.Random(seed)
    W = a1 - a0
    folds = folds or max(3, int(W / 0.14))
    nu = folds * 8
    nz = 26
    ztop = z_rod + 0.035
    def pos(u, zf):
        """u in 0..1 across the flat panel, zf = height -> (a, d) in the wall frame."""
        a = a0 + W * u
        d = out + depth * 0.5 * math.sin(2 * math.pi * folds * u) * (1.0 + 0.15 * math.sin(3.1 * u + seed))
        if tie is not None:
            ta, tz, gather = tie
            # gathering weight: 0 above the fold-out zone, 1 at the tie height, fading below toward the floor
            if zf > tz + 0.45:
                g = 0.0
            elif zf > tz:
                g = ((tz + 0.45 - zf) / 0.45) ** 1.3
            else:
                g = max(0.25, 1.0 - (tz - zf) / (tz - z_floor + 1e-6) * 0.75)
            a = a + (ta - a) * g * gather
            d = out + (d - out) * (1.0 - 0.6 * g) + 0.03 * g
        return a, d
    def P(a, d, zz):
        return (a, b + s * d, zz) if along == 'X' else (b + s * d, a, zz)
    rows = []
    for k in range(nz + 1):
        t = k / nz
        zz = ztop - (ztop - z_floor) * t
        if k == nz:
            zz = z_floor + 0.002
        row = []
        for i in range(nu + 1):
            u = i / nu
            a, d = pos(u, zz)
            if k == nz and puddle:
                d = d + s * 0.0
            row.append(P(a, d, zz))
        rows.append(row)
    for k in range(nz):
        for i in range(nu):
            mb.quad(rows[k][i], rows[k][i + 1], rows[k + 1][i + 1], rows[k + 1][i], mi)
    # grommets: rings around the rod at every other fold crest
    for f in range(folds + 1):
        u = f / folds
        a, _ = pos(u, ztop)
        if along == 'X':
            pts = [(a, b + s * (out + 0.022 * math.cos(2 * math.pi * i / 10)), z_rod + 0.022 * math.sin(2 * math.pi * i / 10)) for i in range(11)]
        else:
            pts = [(b + s * (out + 0.022 * math.cos(2 * math.pi * i / 10)), a, z_rod + 0.022 * math.sin(2 * math.pi * i / 10)) for i in range(11)]
        gm.path_tube(pts, 0.004, seg=5, mi=mi_grommet)
    if tie is not None and tie_mb is not None:
        ta, tz, gather = tie
        # the sash: a soft band wrapped round the gathered panel at tz, running back to the wall
        w_g = 0.10
        pts = [(ta - w_g * 1.4, out + 0.02, tz), (ta - w_g, out + 0.10, tz + 0.01), (ta + w_g * 0.3, out + 0.12, tz - 0.01),
               (ta + w_g * 1.2, out + 0.04, tz), (ta + w_g * 1.5, 0.01, tz + 0.02)]
        for j in range(len(pts) - 1):
            (pa, pd, pz), (qa, qd, qz) = pts[j], pts[j + 1]
            tie_mb.hexa([P(pa, pd - 0.006, pz - 0.04), P(qa, qd - 0.006, qz - 0.04), P(qa, qd + 0.006, qz - 0.04), P(pa, pd + 0.006, pz - 0.04),
                         P(pa, pd - 0.006, pz + 0.04), P(qa, qd - 0.006, qz + 0.04), P(qa, qd + 0.006, qz + 0.04), P(pa, pd + 0.006, pz + 0.04)], mi_tie)
    return pos


# ============================================================ doors
def panel_leaf_grid(face, mb, a0, a1, z0, z1, d0, d1, rows=((0.06, 0.39), (0.46, 0.90)), cols=2, mi_out=0, mi_in=None,
                    raise_=0.011, stile=0.12, mullion=0.11):
    """Moulded interior door slab (both faces) with a grid of raised panels: `rows` = (bottom, top) fractions of the
    height, `cols` panels across between stiles `stile` wide and mullions `mullion` wide (a 2 x 2 'four panel' by
    default, as in builder-grade hollow-core doors)."""
    mi_in = mi_out if mi_in is None else mi_in
    dm = (d0 + d1) / 2
    face.box(mb, a0, a1, dm, d1, z0, z1, mi_out)
    face.box(mb, a0, a1, d0, dm, z0, z1, mi_in)
    W, H = a1 - a0, z1 - z0
    st = stile * W / 0.91
    pw = (W - 2 * st - (cols - 1) * mullion) / cols
    for (r0, r1) in rows:
        for c in range(cols):
            pa0 = a0 + st + c * (pw + mullion)
            pa1 = pa0 + pw
            pz0, pz1 = z0 + H * r0, z0 + H * r1
            for (dd, sgn, mi) in ((d1, 1, mi_out), (d0, -1, mi_in)):
                lo, hi = (dd, dd + raise_) if sgn > 0 else (dd - raise_, dd)
                face.box(mb, pa0 + 0.02, pa1 - 0.02, lo, hi, pz0 + 0.02, pz1 - 0.02, mi)          # raised field
                lo2, hi2 = (dd, dd + raise_ * 0.4) if sgn > 0 else (dd - raise_ * 0.4, dd)
                for (e0, e1, f0, f1) in ((pa0, pa1, pz0, pz0 + 0.008), (pa0, pa1, pz1 - 0.008, pz1),
                                         (pa0, pa0 + 0.008, pz0, pz1), (pa1 - 0.008, pa1, pz0, pz1)):
                    face.box(mb, e0, e1, lo2, hi2, f0, f1, mi)                                    # sticking bead


def transform_objects(obs, origin, u, n):
    """Map objects drawn in a local frame (x along the wall, y out of it, z up) onto a wall running from `origin`
    along the unit vector `u` with the outward normal `n` (both 2D): world = origin + x u + y n."""
    for ob in obs:
        me = ob.data
        for v in me.vertices:
            x, y = v.co.x + ob.location.x, v.co.y + ob.location.y
            v.co.x = origin[0] + x * u[0] + y * n[0] - ob.location.x
            v.co.y = origin[1] + x * u[1] + y * n[1] - ob.location.y
        if u[0] * n[1] - u[1] * n[0] < 0:
            me.flip_normals()
        me.update()


# ============================================================ kitchen
def raised_panel_door(f, mb, a0, a1, z0, z1, style='arch', mi=0, t=0.019, frame=0.058, rise=None, bead=True):
    """Cabinet door on a cladding.Face (local a along the face, d outward, z up): stiles and rails (the top rail's
    lower edge follows a smooth cathedral arch for style 'arch', straight for 'square'), a recessed panel, a bevel
    step and a raised field.  Every visible face sits at its own depth (frame t, field t - 0.002, step t - 0.006,
    panel t - 0.010), so no two front faces are coplanar (Cycles renders coplanar overlaps as black blotches)."""
    m = frame
    oa0, oa1, oz0 = a0 + m, a1 - m, z0 + m
    w = oa1 - oa0
    if style == 'arch':
        rise = min(0.075, w * 0.22) if rise is None else rise
        n = 16
    else:
        rise, n = 0.0, 1
    zt = z1 - m

    def za(u):                                           # opening top at fraction u across the opening
        return zt - rise + rise * math.sin(math.pi * min(1.0, max(0.0, u))) if rise else zt

    def slab(u0, u1, ins, d0, d1, top_off, lo):
        """Sloped-top hexahedron across u0..u1 (fractions of the opening), inset `ins` from the stiles."""
        b0, b1 = oa0 + w * u0, oa0 + w * u1
        c0, c1 = max(b0, oa0 + ins), min(b1, oa1 - ins)
        if c1 - c0 < 1e-5:
            return
        g0, g1 = (c0 - oa0) / w, (c1 - oa0) / w
        h0, h1 = za(g0) - top_off, za(g1) - top_off
        f.quad8(mb, [(c0, d0, lo), (c1, d0, lo), (c1, d1, lo), (c0, d1, lo), (c0, d0, h0), (c1, d0, h1), (c1, d1, h1), (c0, d1, h0)], mi)
    f.box(mb, a0, oa0, 0.0, t, z0, z1, mi)               # stiles
    f.box(mb, oa1, a1, 0.0, t, z0, z1, mi)
    f.box(mb, oa0, oa1, 0.0, t, z0, oz0, mi)             # bottom rail
    for i in range(n):
        u0, u1 = i / n, (i + 1) / n
        ha, hb = za(u0), za(u1)
        xa, xb = oa0 + w * u0, oa0 + w * u1
        f.quad8(mb, [(xa, 0.0, ha), (xb, 0.0, hb), (xb, t, hb), (xa, t, ha), (xa, 0.0, z1), (xb, 0.0, z1), (xb, t, z1), (xa, t, z1)], mi)
        slab(u0, u1, 0.0, 0.0, t - 0.010, 0.0, oz0)                     # recessed panel
        slab(u0, u1, 0.012, t - 0.010, t - 0.006, 0.012, oz0 + 0.012)   # bevel step
        slab(u0, u1, 0.026, t - 0.006, t - 0.002, 0.026, oz0 + 0.026)   # raised field
    if bead:                                             # a thin proud bead on the stiles' inner edges
        f.box(mb, oa0 - 0.006, oa0, t, t + 0.003, oz0, zt - rise, mi)
        f.box(mb, oa1, oa1 + 0.006, t, t + 0.003, oz0, zt - rise, mi)


def drawer_front(f, mb, a0, a1, z0, z1, mi=0, t=0.019):
    """Slab drawer front with a soft roundover (drawn as a proud slab + a 3 mm chamfer step)."""
    f.box(mb, a0, a1, 0.0, t - 0.003, z0, z1, mi)
    f.box(mb, a0 + 0.004, a1 - 0.004, t - 0.003, t, z0 + 0.004, z1 - 0.004, mi)


def bar_pull(f, mb, a, z, length=0.096, vertical=False, t=0.019, mi=0):
    """Satin-nickel arched bar pull (96 mm centres) on a face at depth t."""
    if vertical:
        f.box(mb, a - 0.005, a + 0.005, t, t + 0.028, z - length / 2 - 0.006, z + length / 2 + 0.006, mi)
        f.box(mb, a - 0.004, a + 0.004, t, t + 0.022, z - length / 2 - 0.004, z - length / 2 + 0.004, mi)
        f.box(mb, a - 0.004, a + 0.004, t, t + 0.022, z + length / 2 - 0.004, z + length / 2 + 0.004, mi)
    else:
        f.box(mb, a - length / 2 - 0.006, a + length / 2 + 0.006, t + 0.016, t + 0.026, z - 0.005, z + 0.005, mi)
        for e in (-1, 1):
            f.box(mb, a + e * length / 2 - 0.004, a + e * length / 2 + 0.004, t, t + 0.022, z - 0.004, z + 0.004, mi)


def gas_range(steel, black, glass, knobs, f, a0, a1, z0=0.0, depth=0.66, top=0.915, mi=0, mi_black=0, mi_glass=0, mi_knob=0,
              display=None):
    """30-inch slide-in gas range on a Face (a across the front, d toward the room from the wall; the face's d=0 is
    the WALL, the front is at d = depth): stainless body and door with a bar handle and a window, front controls
    with 5 knobs and a display, a black cooktop with 4 burners under cast grates."""
    W = a1 - a0
    f.box(steel, a0, a1, 0.03, depth - 0.02, z0 + 0.08, top - 0.02, mi)                       # body
    f.box(black, a0 + 0.01, a1 - 0.01, 0.05, depth - 0.03, z0, z0 + 0.08, mi_black)         # toe kick
    f.box(steel, a0, a1, depth - 0.025, depth, z0 + 0.10, z0 + 0.22, mi)                      # drawer
    f.box(black, a0 + 0.002, a1 - 0.002, depth - 0.026, depth - 0.024, z0 + 0.222, z0 + 0.232, mi_black)
    f.box(steel, a0, a1, depth - 0.03, depth, z0 + 0.232, top - 0.11, mi)                      # oven door
    f.box(black, a0 + 0.06, a1 - 0.06, depth, depth + 0.0012, z0 + 0.33, top - 0.23, mi_black)          # window surround
    f.box(glass, a0 + 0.075, a1 - 0.075, depth + 0.0012, depth + 0.0024, z0 + 0.345, top - 0.245, mi_glass)   # window
    for e in (a0 + 0.06, a1 - 0.06):                                                          # handle posts + bar
        f.box(steel, e - 0.012, e + 0.012, depth, depth + 0.05, top - 0.165, top - 0.14, mi)
    f.box(steel, a0 + 0.05, a1 - 0.05, depth + 0.035, depth + 0.058, top - 0.165, top - 0.14, mi)
    # control panel (angled front) + knobs + display
    f.box(steel, a0, a1, depth - 0.04, depth - 0.005, top - 0.11, top - 0.02, mi)
    for fr in (0.09, 0.2, 0.62, 0.76, 0.9):
        u = a0 + W * fr
        f.box(knobs, u - 0.02, u + 0.02, depth - 0.005, depth + 0.03, top - 0.086, top - 0.044, mi_knob)
        f.box(knobs, u - 0.024, u + 0.024, depth - 0.005, depth + 0.012, top - 0.09, top - 0.04, mi_knob)
    f.box(black, a0 + W * 0.33, a0 + W * 0.52, depth - 0.005, depth - 0.0035, top - 0.09, top - 0.045, mi_black)   # display
    # cooktop: black glass-look base, burners, cast grates (bars)
    f.box(black, a0 + 0.005, a1 - 0.005, 0.04, depth - 0.02, top - 0.02, top, mi_black)
    for (u, dd) in ((0.27, 0.22), (0.73, 0.22), (0.27, 0.48), (0.73, 0.48)):
        bx, by, bz = f.p(a0 + W * u, dd, top)
        black.cylinder(bx, by, bz, bz + 0.018, 0.045, seg=16, mi=mi_black)
        steel.cylinder(bx, by, bz + 0.018, bz + 0.024, 0.03, seg=16, mi=mi)
    zg = top + 0.03
    for k in range(3):                                                                        # grates: bars along d and a
        u = a0 + 0.03 + (W - 0.06) * k / 2
        f.box(black, u - 0.008, u + 0.008, 0.06, depth - 0.04, zg - 0.012, zg, mi_black)
    for dd in (0.08, 0.35, 0.62):
        f.box(black, a0 + 0.03, a1 - 0.03, dd - 0.008, dd + 0.008, zg - 0.012, zg, mi_black)


def under_hood(steel, black, f, a0, a1, z0, z1, depth=0.50, mi=0, mi_black=0, finish='black'):
    """Under-cabinet range hood (photo: black / stainless 30"): a shell with a sloped front, a lower lip, a control
    strip and a filter grille underneath."""
    tgt = black if finish == 'black' else steel
    m = mi_black if finish == 'black' else mi
    f.box(tgt, a0, a1, 0.005, depth - 0.05, z0 + 0.03, z1, m)
    # sloped front: a thin slab from (depth-0.05, z1) to (depth, z0+0.03)
    f.quad8(tgt, [(a0, depth - 0.05, z1), (a1, depth - 0.05, z1), (a1, depth, z0 + 0.035), (a0, depth, z0 + 0.035),
                  (a0, depth - 0.055, z1), (a1, depth - 0.055, z1), (a1, depth - 0.005, z0 + 0.03), (a0, depth - 0.005, z0 + 0.03)], m)
    f.box(tgt, a0 + 0.001, a1 - 0.001, 0.005, depth, z0, z0 + 0.03, m)
    f.box(steel, a0 + (a1 - a0) * 0.72, a0 + (a1 - a0) * 0.9, depth + 0.001, depth + 0.004, z0 + 0.008, z0 + 0.03, mi)   # controls
    f.box(steel, a0 + 0.04, a1 - 0.04, 0.05, depth - 0.06, z0 - 0.002, z0, mi)                                          # filters


def dishwasher(steel, black, f, a0, a1, top=0.87, depth=0.61, mi=0, mi_black=0):
    """Built-in dishwasher (stainless tub door with a pocket handle and a top control strip, black toe kick)."""
    f.box(steel, a0 + 0.004, a1 - 0.004, depth - 0.05, depth - 0.002, 0.10, top - 0.10, mi)
    f.box(black, a0 + 0.01, a1 - 0.01, depth - 0.08, depth - 0.05, 0.0, 0.10, mi_black)
    f.box(steel, a0 + 0.004, a1 - 0.004, depth - 0.06, depth - 0.002, top - 0.098, top - 0.01, mi)
    f.box(black, a0 + 0.004, a1 - 0.004, depth - 0.002, depth, top - 0.102, top - 0.098, mi_black)
    f.box(steel, a0 + 0.06, a1 - 0.06, depth - 0.002, depth + 0.02, top - 0.13, top - 0.115, mi)            # handle bar
    for e in (a0 + 0.07, a1 - 0.07):
        f.box(steel, e - 0.008, e + 0.008, depth - 0.002, depth + 0.02, top - 0.13, top - 0.105, mi)


def fridge_top_freezer(steel, black, f, a0, a1, h=1.70, depth=0.76, split=0.64, mi=0, mi_black=0, side='black'):
    """Top-freezer refrigerator (photo 13: stainless doors, black cabinet sides): freezer door above `split`
    (fraction of the height), fresh-food door below, a dark gap, recessed vertical handles, black sides and top."""
    f.box(black if side == 'black' else steel, a0, a1, 0.02, depth - 0.05, 0.0, h, mi_black if side == 'black' else mi)
    zs = h * split
    f.box(steel, a0, a1, depth - 0.05, depth, 0.05, zs - 0.008, mi)
    f.box(steel, a0, a1, depth - 0.05, depth, zs + 0.008, h - 0.005, mi)
    f.box(black, a0 + 0.003, a1 - 0.003, depth - 0.048, depth - 0.02, zs - 0.008, zs + 0.008, mi_black)
    f.box(black, a0 + 0.01, a1 - 0.01, depth - 0.06, depth - 0.03, 0.0, 0.05, mi_black)                   # grille
    for (z0, z1) in ((zs - 0.45, zs - 0.06), (zs + 0.05, zs + 0.30)):
        hx = a1 - 0.06
        f.box(steel, hx - 0.012, hx + 0.012, depth, depth + 0.045, z0, z1, mi)
        f.box(steel, hx - 0.01, hx + 0.01, depth, depth + 0.03, z0 - 0.03, z0 + 0.02, mi)
        f.box(steel, hx - 0.01, hx + 0.01, depth, depth + 0.03, z1 - 0.02, z1 + 0.03, mi)
    f.box(steel, a0 + 0.3, a0 + 0.36, depth, depth + 0.002, h - 0.06, h - 0.045, mi)                      # badge


def microwave(steel, black, glass, f, a0, a1, z0, h=0.30, depth=0.42, mi=0, mi_black=0, mi_glass=0):
    """Countertop microwave (photo 13: stainless wrap, black glass door on the left 3/4, a keypad on the right)."""
    f.box(steel, a0, a1, 0.02, depth - 0.01, z0 + 0.012, z0 + h, mi)
    f.box(black, a0 + 0.02, a1 - 0.02, depth - 0.02, depth - 0.01, z0, z0 + 0.012, mi_black)
    W = a1 - a0
    f.box(black, a0 + 0.012, a0 + W * 0.74, depth - 0.01, depth, z0 + 0.03, z0 + h - 0.02, mi_black)
    f.box(glass, a0 + 0.04, a0 + W * 0.70, depth, depth + 0.002, z0 + 0.06, z0 + h - 0.05, mi_glass)
    f.box(steel, a0 + W * 0.74, a1 - 0.01, depth - 0.01, depth, z0 + 0.03, z0 + h - 0.02, mi)
    f.box(black, a0 + W * 0.78, a1 - 0.03, depth, depth + 0.002, z0 + 0.08, z0 + h - 0.06, mi_black)
    f.box(steel, a0 + W * 0.70, a0 + W * 0.73, depth, depth + 0.025, z0 + 0.05, z0 + h - 0.04, mi)       # handle


# ============================================================ fireplace
def gas_firebox(black, glass, logs, f, a0, a1, z0, z1, mi=0, mi_glass=0, mi_log=0, louvre=0.075, seed=4, mi_inner=None):
    """Direct-vent gas fireplace front on a Face (d toward the room, d=0 = the surround face): a black surround
    frame with louvred top and bottom grilles, a recessed glass panel, a dark firebox with a scrolled grate bar,
    and a stack of ceramic logs behind the glass."""
    ga0, ga1, gz0, gz1 = a0 + 0.045, a1 - 0.045, z0 + louvre + 0.01, z1 - louvre - 0.01
    f.box(black, a0, a1, 0.0, 0.012, z0, gz0 - 0.012, mi)                           # outer frame (a ring round the glass)
    f.box(black, a0, a1, 0.0, 0.012, gz1 + 0.012, z1, mi)
    f.box(black, a0, ga0 - 0.012, 0.0, 0.012, gz0 - 0.012, gz1 + 0.012, mi)
    f.box(black, ga1 + 0.012, a1, 0.0, 0.012, gz0 - 0.012, gz1 + 0.012, mi)
    for (za, zb) in ((z1 - louvre, z1 - 0.01), (z0 + 0.01, z0 + louvre)):
        n = 6
        for k in range(n):
            zz = za + (zb - za) * (k + 0.5) / n
            f.box(black, a0 + 0.03, a1 - 0.03, 0.012, 0.02, zz - 0.004, zz + 0.004, mi)
    f.box(black, ga0 - 0.012, ga1 + 0.012, 0.012, 0.022, gz0 - 0.012, gz0, mi)
    f.box(black, ga0 - 0.012, ga1 + 0.012, 0.012, 0.022, gz1, gz1 + 0.012, mi)
    f.box(black, ga0 - 0.012, ga0, 0.012, 0.022, gz0, gz1, mi)
    f.box(black, ga1, ga1 + 0.012, 0.012, 0.022, gz0, gz1, mi)
    f.box(glass, ga0, ga1, 0.004, 0.008, gz0, gz1, mi_glass)
    # firebox interior (behind the plate: negative d), a refractory liner (mi_inner)
    mi_in = mi if mi_inner is None else mi_inner
    f.box(black, ga0, ga1, -0.36, -0.34, gz0, gz1, mi_in)                           # back
    f.box(black, ga0, ga0 + 0.02, -0.36, 0.0, gz0, gz1, mi_in)
    f.box(black, ga1 - 0.02, ga1, -0.36, 0.0, gz0, gz1, mi_in)
    f.box(black, ga0, ga1, -0.36, 0.0, gz1 - 0.02, gz1, mi_in)
    f.box(black, ga0, ga1, -0.36, 0.0, gz0, gz0 + 0.03, mi)                          # floor / burner pan
    # scrolled decorative bar across the glass (a ring motif in the middle)
    zb = gz0 + (gz1 - gz0) * 0.62
    f.box(black, ga0 + 0.02, ga1 - 0.02, -0.02, -0.012, zb - 0.006, zb + 0.006, mi)
    cx = (a0 + a1) / 2
    for k in range(3):
        ox = (k - 1) * 0.09
        n = 12
        for i in range(n):
            t0, t1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
            p0 = (cx + ox + 0.035 * math.cos(t0), zb + 0.035 * math.sin(t0))
            p1 = (cx + ox + 0.035 * math.cos(t1), zb + 0.035 * math.sin(t1))
            f.box(black, min(p0[0], p1[0]) - 0.003, max(p0[0], p1[0]) + 0.003, -0.02, -0.012, min(p0[1], p1[1]) - 0.003,
                  max(p0[1], p1[1]) + 0.003, mi)
    # ceramic logs: a grate + 5 logs in a loose pyramid
    rng = random.Random(seed)
    zl = gz0 + 0.035
    for (u0, u1, dd, zz, r) in ((0.18, 0.82, -0.22, zl + 0.05, 0.05), (0.12, 0.55, -0.12, zl + 0.045, 0.045), (0.45, 0.88, -0.12, zl + 0.045, 0.045),
                                (0.25, 0.70, -0.17, zl + 0.13, 0.042), (0.5, 0.78, -0.08, zl + 0.11, 0.035)):
        pa = f.p(ga0 + (ga1 - ga0) * u0, dd + rng.uniform(-0.03, 0.03), zz)
        pb = f.p(ga0 + (ga1 - ga0) * u1, dd + rng.uniform(-0.03, 0.03), zz + rng.uniform(-0.03, 0.03))
        logs.tube(pa, pb, r, r * rng.uniform(0.8, 1.0), seg=12, mi=mi_log)
        for e in (pa, pb):
            logs.sphere(e, r * 0.95, seg=10, rings=6, mi=mi_log)


def fluted_mantel(mb, f, a0, a1, z_shelf, open_a0, open_a1, open_z1, pil_w=0.17, flutes=9, mi=0, shelf_d=0.19,
                  depth=0.06):
    """Painted fluted-pilaster mantel on a Face (a along the wall, d outward, z up): plinth blocks, fluted pilasters
    (`flutes` channels), capitals, a plain frieze with an inner bead around the opening, a bed moulding, a crown
    cove and a thick shelf."""
    for (pa0, pa1) in ((a0, a0 + pil_w), (a1 - pil_w, a1)):
        f.box(mb, pa0 - 0.01, pa1 + 0.01, 0.0, depth + 0.01, 0.0, 0.14, mi)                 # plinth
        f.box(mb, pa0, pa1, 0.0, depth, 0.14, open_z1 + 0.02, mi)                           # pilaster body
        w = pa1 - pa0 - 0.036
        for k in range(flutes):
            u0 = pa0 + 0.018 + w * (k + 0.2) / flutes
            u1 = pa0 + 0.018 + w * (k + 0.8) / flutes
            f.box(mb, u0, u1, depth, depth + 0.006, 0.16, open_z1 - 0.02, mi)                # fillets between flutes
        f.box(mb, pa0 - 0.012, pa1 + 0.012, 0.0, depth + 0.014, open_z1 + 0.02, open_z1 + 0.06, mi)   # capital
    # inner bead around the opening
    f.box(mb, open_a0 - 0.02, open_a0, depth - 0.02, depth + 0.004, 0.0, open_z1, mi)
    f.box(mb, open_a1, open_a1 + 0.02, depth - 0.02, depth + 0.004, 0.0, open_z1, mi)
    f.box(mb, open_a0 - 0.02, open_a1 + 0.02, depth - 0.02, depth + 0.004, open_z1, open_z1 + 0.02, mi)
    # frieze + bands
    f.box(mb, a0 + pil_w, a1 - pil_w, 0.0, depth - 0.01, open_z1, z_shelf - 0.09, mi)
    f.box(mb, a0 - 0.012, a1 + 0.012, 0.0, depth + 0.02, open_z1 + 0.06, open_z1 + 0.085, mi)
    f.box(mb, a0, a1, 0.0, depth, open_z1 + 0.085, z_shelf - 0.09, mi)
    f.box(mb, a0 - 0.02, a1 + 0.02, 0.0, depth + 0.03, z_shelf - 0.09, z_shelf - 0.07, mi)   # bed moulding
    n = 5                                                                                    # crown cove (stepped)
    for k in range(n):
        t = (k + 1) / n
        f.box(mb, a0 - 0.02 - 0.05 * t, a1 + 0.02 + 0.05 * t, 0.0, depth + 0.03 + 0.08 * t ** 1.6, z_shelf - 0.07 + 0.012 * k,
              z_shelf - 0.07 + 0.012 * (k + 1), mi)
    f.box(mb, a0 - 0.085, a1 + 0.085, 0.0, shelf_d, z_shelf - 0.01, z_shelf + 0.035, mi)        # shelf
    f.box(mb, a0 - 0.09, a1 + 0.09, 0.0, shelf_d + 0.005, z_shelf + 0.01, z_shelf + 0.03, mi)
