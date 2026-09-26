"""The neighbours on Stanford Dr (photos 01, 02, 25, 26, 28, 30, 31, 32): the two adjacent houses as measured massing
(walls, roofs, front gables, porches, garages, windows and doors where the photos show them) and simpler houses
further along the street row.  World coordinates, fronts facing -Y (the street).

Evidence (SITE_NEAR, back-projected through the aerial camera of cams_site.py and the facade cameras; the aerial's
ground reads ~+0.6 m in y at the facade line and was corrected; garage doors from SITE_FAR's joint aerial solve):
  left  (x < 0)   cream lap-siding two-storey, side-gabled, grey-brown shingles, walls x -18.7 .. -5.6, front wall y 5.0,
                  ridge y ~10.5 (31); a one-storey front-gabled garage bump in tan brick with an oculus and a white
                  16-ft door (x -11.25 .. -6.43, 31/32), its face flush with our garage; a small entry roof at its right;
                  a satellite dish on the east wall (30, 31)
  right (x > 12)  a mirror of our Ryland plan: garage on its left (brick front with a small window, sage door 17.95 ..
                  22.89), a shed roof over the garage + porch, two overlapping front gables at the left, a recessed
                  centre window, a right front gable (31), sage lap siding, grey shingles, a porch with white columns
                  and railing (30), basketball hoop at the drive, bins (31)
  further houses: massing at the lot pitch (~18 m), colours from 30/31/32 (inferred details)
"""
import math
from .plan import Z_GRADE
from archviz.mesh import MB
from archviz.cladding import Face, lap_siding
from archviz import fenestration as fen
from archviz import roofing as rf

ZG = Z_GRADE


class Kit:
    """Accumulates one neighbour house: siding faces (geometry lap siding), brick, trim, windows, roofs."""

    def __init__(self, name, M, siding, roof, brick=None, coll='Neighbours'):
        self.name, self.M, self.coll = name, M, coll
        self.siding_mat, self.roof_mat, self.brick_mat = siding, roof, brick or M['brick']
        self.core, self.sid, self.brk, self.trim, self.win, self.dark = MB(), MB(), MB(), MB(), MB(), MB()
        self.n_roof = 0

    # -- walls
    def box(self, x0, x1, y0, y1, z0, z1, inset=0.15):
        """Dark core volume, inset behind the face planes so recessed window units have room in front of it."""
        self.core.box(x0 + inset, x1 - inset, y0 + inset, y1 - inset, z0, z1)

    def siding(self, face, a0, a1, z0, z1, holes=(), top_clip=None):
        lap_siding(self.sid, face, a0, a1, z0, z1, holes=holes, exposure=0.19, top_clip=top_clip)

    def brick(self, face, a0, a1, z0, z1, t=0.10):
        face.box(self.brk, a0, a1, 0.0, t, z0, z1)

    def gable_tri(self, face, a0, a1, z0, z_apex, mat='siding', d=0.0):
        """Gable-end triangle (a thin prism) on a face."""
        am = (a0 + a1) / 2
        mb = self.sid if mat == 'siding' else self.brk
        pts = [(a0, d, z0), (a1, d, z0), (am, d, z_apex)]
        (P0, P1, P2) = [face.p(*q) for q in pts]
        Q = [face.p(a, d + 0.06, z) for (a, _, z) in pts]
        mb._add([P0, P1, P2, Q[0], Q[1], Q[2]], [(0, 1, 2), (3, 5, 4), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)], 0)

    # -- openings
    def window(self, face, a0, a1, z0, z1, shutters=False, grid=(3, 2), units=1, d=0.0):
        fen.single_hung(face, self.win, a0, a1, z0, z1, 0.12, grid=grid, units=units, mi_frame=0, mi_glass=1, mi_grille=0,
                        mi_return=0, mi_casing=0, interior=False)
        face.box(self.dark, a0 + 0.02, a1 - 0.02, -0.14, -0.10, z0 + 0.02, z1 - 0.02)          # dark room behind the glass
        if shutters:
            w = min(0.42, (a1 - a0) / (2 * units) * 0.95)
            fen.shutter(face, self.win, a0 - 0.08 - w, a0 - 0.08, z0, z1, d=0.02, mi=2)
            fen.shutter(face, self.win, a1 + 0.08, a1 + 0.08 + w, z0, z1, d=0.02, mi=2)

    def door(self, face, a0, a1, z0, z1, mi=3):
        fen.panel_leaf(face, self.win, a0, a1, z0, z1, -0.05, 0.0, layout='six', mi_out=mi, mi_in=mi)
        for (b0, b1, c0, c1) in ((a0 - 0.09, a0, z0, z1 + 0.09), (a1, a1 + 0.09, z0, z1 + 0.09), (a0, a1, z1, z1 + 0.09)):
            face.box(self.trim, b0, b1, 0.0, 0.03, c0, c1)

    def garage_door(self, face, a0, a1, z0, z1, mat_key):
        mb = MB()
        fen.garage_door(face, mb, a0, a1, z0, z1, d=0.02, sections=4, cols=8, style='bevel')
        for (b0, b1, c0, c1) in ((a0 - 0.1, a0, z0, z1 + 0.1), (a1, a1 + 0.1, z0, z1 + 0.1), (a0, a1, z1, z1 + 0.1)):
            face.box(self.trim, b0, b1, 0.0, 0.035, c0, c1)
        mb.build(f"{self.name}_GarageDoor{self.n_roof}", [self.M[mat_key]], coll=self.coll)
        self.n_roof += 1

    # -- roofs
    def slope(self, eave_pt, eave_dir, up_dir, pitch, plan_pts):
        rf.slope(f"{self.name}_Roof{self.n_roof}", [self.roof_mat], eave_pt, eave_dir, up_dir, pitch, plan_pts, 0.1, self.coll)
        self.n_roof += 1

    def side_gable_roof(self, x0, x1, y0, y1, z_eave, pitch, ov=0.35, rake=0.40, gable_ends=True):
        """Ridge along X at the middle of y0..y1; eaves at z_eave (roof surface at the wall line)."""
        ym = (y0 + y1) / 2
        zr = z_eave + (ym - y0) * pitch
        ze = z_eave - ov * pitch
        self.slope((x0 - rake, y0 - ov, ze), (1, 0), (0, 1), pitch, [(x0 - rake, y0 - ov), (x1 + rake, y0 - ov), (x1 + rake, ym), (x0 - rake, ym)])
        self.slope((x0 - rake, y1 + ov, ze), (1, 0), (0, -1), pitch, [(x0 - rake, y1 + ov), (x1 + rake, y1 + ov), (x1 + rake, ym), (x0 - rake, ym)])
        for (x, s) in ((x0, -1), (x1, 1)):
            if gable_ends:
                self.gable_tri(Face('Y', x, s), y0, y1, z_eave, zr - 0.12)
            rf.rake_board(self.trim, (x + s * rake, y0 - ov), (x + s * rake, ym), ze, zr, (s, 0))
            rf.rake_board(self.trim, (x + s * rake, y1 + ov), (x + s * rake, ym), ze, zr, (s, 0))
        for (y, s) in ((y0, -1), (y1, 1)):
            rf.fascia_run(self.trim, (x0 - rake, y + s * ov), (x1 + rake, y + s * ov), ze, (0, s))
            rf.gutter(self.trim, (x0 - rake, y + s * ov), (x1 + rake, y + s * ov), ze - 0.03, (0, s))
            rf.soffit_run(self.trim, (x0, y), (x1, y), (0, s), ov, z_eave - 0.22)
        return zr

    def front_gable_roof(self, x0, x1, y_face, y_back, z_eave, pitch, ov=0.30, tri_mat='siding'):
        """Ridge along Y from the gable face (y_face) back to y_back; the gable triangle on the face."""
        xm = (x0 + x1) / 2
        zr = z_eave + (xm - x0) * pitch
        ze = z_eave - ov * pitch
        yf = y_face - ov
        self.slope((x0 - ov, yf, ze), (0, 1), (1, 0), pitch, [(x0 - ov, yf), (xm, yf), (xm, y_back), (x0 - ov, y_back)])
        self.slope((x1 + ov, yf, ze), (0, 1), (-1, 0), pitch, [(x1 + ov, yf), (xm, yf), (xm, y_back), (x1 + ov, y_back)])
        self.gable_tri(Face('X', y_face, -1), x0, x1, z_eave, zr - 0.12, mat=tri_mat)
        rf.rake_board(self.trim, (x0 - ov, yf), (xm, yf), ze, zr, (0, -1))
        rf.rake_board(self.trim, (x1 + ov, yf), (xm, yf), ze, zr, (0, -1))
        for (x, s) in ((x0, -1), (x1, 1)):
            rf.fascia_run(self.trim, (x + s * ov, yf), (x + s * ov, y_back), ze, (s, 0))
            rf.gutter(self.trim, (x + s * ov, yf), (x + s * ov, y_back), ze - 0.03, (s, 0))
        return zr

    def shed_roof(self, x0, x1, y_front, y_back, z_eave, pitch, ov=0.35):
        ze = z_eave - ov * pitch
        self.slope((x0, y_front - ov, ze), (1, 0), (0, 1), pitch, [(x0, y_front - ov), (x1, y_front - ov), (x1, y_back), (x0, y_back)])
        rf.fascia_run(self.trim, (x0, y_front - ov), (x1, y_front - ov), ze, (0, -1))
        rf.gutter(self.trim, (x0, y_front - ov), (x1, y_front - ov), ze - 0.03, (0, -1))
        rf.soffit_run(self.trim, (x0, y_front), (x1, y_front), (0, -1), ov, z_eave - 0.2)

    def build(self):
        M, c = self.M, self.coll
        self.core.build(f"{self.name}_Core", [M['siding_back']], coll=c)
        if self.sid.v:
            self.sid.build(f"{self.name}_Siding", [self.siding_mat], coll=c)
        if self.brk.v:
            self.brk.build(f"{self.name}_Brick", [self.brick_mat], coll=c)
        self.trim.build(f"{self.name}_Trim", [M['trim']], coll=c)
        self.win.build(f"{self.name}_Windows", [M['trim'], M['neighbour_glass'], M.get('nb_shutter', M['shutter']), M.get('nb_door', M['navy'])],
                       coll=c)
        self.dark.build(f"{self.name}_Rooms", [M['neighbour_room']], coll=c)


def mats(M):
    from archviz import materials as _m
    if 'nb_cream' in M:
        return M
    M['nb_cream'] = _m.painted_board("SidingCreamNbr", base=(0.62, 0.60, 0.53, 1))
    M['nb_sage'] = _m.painted_board("SidingSageNbr", base=(0.30, 0.335, 0.27, 1))
    M['nb_tanbrick'] = _m.brick_veneer("BrickTanNbr", 'XZ', base=(0.36, 0.28, 0.20, 1), alt=(0.44, 0.35, 0.26, 1), dark=(0.26, 0.20, 0.15, 1),
                                       mortar=(0.50, 0.47, 0.42, 1))
    M['nb_tanbrick_y'] = _m.brick_veneer("BrickTanNbrY", 'YZ', base=(0.36, 0.28, 0.20, 1), alt=(0.44, 0.35, 0.26, 1), dark=(0.26, 0.20, 0.15, 1),
                                         mortar=(0.50, 0.47, 0.42, 1))
    M['nb_roof_tan'] = _m.shingles("ShinglesTanNbr", c1=(0.17, 0.13, 0.10, 1), c2=(0.22, 0.17, 0.13, 1), c3=(0.13, 0.10, 0.08, 1))
    M['nb_roof_grey'] = _m.shingles("ShinglesGreyNbr", c1=(0.13, 0.135, 0.14, 1), c2=(0.17, 0.175, 0.18, 1), c3=(0.10, 0.10, 0.11, 1))
    M['nb_garage_white'] = _m.new_mat("GarageWhiteNbr", (0.74, 0.74, 0.72, 1), rough=0.45)
    M['nb_garage_sage'] = _m.new_mat("GarageSageNbr", (0.30, 0.34, 0.29, 1), rough=0.45)
    M['nb_shutter'] = _m.new_mat("ShutterDarkNbr", (0.035, 0.04, 0.045, 1), rough=0.5)
    M['nb_door'] = _m.new_mat("DoorWhiteNbr", (0.72, 0.72, 0.70, 1), rough=0.4)
    M['neighbour_room'] = _m.new_mat("NeighbourRoomDark", (0.035, 0.032, 0.03, 1), rough=0.9)
    M['nb_bin_blue'] = _m.new_mat("BinBlue", (0.02, 0.18, 0.40, 1), rough=0.45)
    M['nb_bin_yellow'] = _m.new_mat("BinYellow", (0.60, 0.46, 0.02, 1), rough=0.45)
    M['nb_car_dark'] = _m.new_mat("CarPaintDark", (0.02, 0.022, 0.025, 1), rough=0.18, metal=0.6, coat=1.0)
    M['nb_car_grey'] = _m.new_mat("CarPaintGrey", (0.10, 0.10, 0.10, 1), rough=0.2, metal=0.6, coat=1.0)
    M['nb_car_white'] = _m.new_mat("CarPaintWhite", (0.70, 0.70, 0.69, 1), rough=0.2, metal=0.3, coat=1.0)
    M['nb_car_glass'] = _m.new_mat("CarGlass", (0.02, 0.025, 0.03, 1), rough=0.05, spec=0.8, coat=0.5)
    M['nb_tyre'] = _m.new_mat("CarTyre", (0.02, 0.02, 0.02, 1), rough=0.8)
    M['nb_metal'] = _m.new_mat("PoleMetal", (0.08, 0.08, 0.085, 1), rough=0.4, metal=0.9)
    return M


# ---------------------------------------------------------------- the left neighbour (x < 0)
def bump_house(name, M, x0, x1, y0, y1, gx0, gx1, door, siding, roof, brick, gy0=0.12, dish=False, entry_x1=None, oculus_brick=True):
    """Two-storey side-gabled house with a one-storey front-gabled brick garage bump (oculus in the gable, 16-ft door),
    the type of the left neighbour and the house beyond it (31): walls x0..x1 / y0..y1, bump gx0..gx1 from gy0 back to
    y0, garage door = (d0, d1); an optional one-storey entry wing from the bump's right wall to entry_x1."""
    k = Kit(name, M, siding, roof, brick=brick)
    ze = ZG + 5.85
    k.box(x0, x1, y0, y1, ZG - 0.2, ze)
    F, B, L, R = Face('X', y0, -1), Face('X', y1, 1), Face('Y', x0, -1), Face('Y', x1, 1)
    W = x1 - x0
    fw = [(x0 + W * f - 0.45, x0 + W * f + 0.45) for f in (0.2, 0.62, 0.8)]
    bw_up = [(x0 + W * f - 0.45, x0 + W * f + 0.45) for f in (0.1, 0.4, 0.7, 0.88)]
    sl = (x0 + W * 0.33, x0 + W * 0.33 + 1.8)
    kw = (x0 + W * 0.62, x0 + W * 0.62 + 1.6)
    k.siding(F, x0, x1, ZG + 0.1, ze, holes=[(a - 0.1, b + 0.1, ZG + 3.4, ZG + 5.2) for a, b in fw])
    for a, b in fw:
        k.window(F, a, b, ZG + 3.55, ZG + 5.05)
    k.siding(B, x0, x1, ZG + 0.1, ze, holes=[(a - 0.1, b + 0.1, ZG + 3.4, ZG + 5.2) for a, b in bw_up] +
             [(sl[0] - 0.1, sl[1] + 0.1, ZG + 0.2, ZG + 2.5), (kw[0] - 0.1, kw[1] + 0.1, ZG + 0.9, ZG + 2.4)])
    for a, b in bw_up:
        k.window(B, a, b, ZG + 3.55, ZG + 5.05)
    k.window(B, sl[0], sl[1], ZG + 0.3, ZG + 2.4, grid=(3, 3))
    k.window(B, kw[0], kw[1], ZG + 1.0, ZG + 2.3, units=2, grid=(3, 2))
    ym = (y0 + y1) / 2
    k.siding(L, y0, y1, ZG + 0.1, ze, holes=[(ym - 1.3, ym - 0.3, ZG + 3.4, ZG + 5.2)])
    k.window(L, ym - 1.2, ym - 0.4, ZG + 3.55, ZG + 5.05)
    k.siding(R, y0, y1, ZG + 0.1, ze, holes=[(ym + 2.3, ym + 3.3, ZG + 3.4, ZG + 5.2), (ym - 3.5, ym - 2.6, ZG + 0.9, ZG + 2.3)])
    k.window(R, ym + 2.4, ym + 3.2, ZG + 3.55, ZG + 5.05)
    k.window(R, ym - 3.4, ym - 2.7, ZG + 1.0, ZG + 2.2)
    k.side_gable_roof(x0, x1, y0, y1, ze, 0.60, ov=0.35, rake=0.35)
    zb = ZG + 2.95
    k.box(gx0, gx1, gy0, y0, ZG - 0.2, zb)
    GF = Face('X', gy0, -1)
    k.brick(GF, gx0 - 0.1, gx1 + 0.1, ZG - 0.1, zb)
    for (xx, sgn) in ((gx0, -1), (gx1, 1)):
        Face('Y', xx, sgn).box(k.brk, gy0 - 0.1, y0, 0.0, 0.1, ZG - 0.1, zb)
    k.window(Face('Y', gx1 + 0.1, 1), gy0 + 1.5, gy0 + 2.25, ZG + 1.1, ZG + 2.0)
    k.garage_door(Face('X', gy0 - 0.1, -1), door[0], door[1], ZG + 0.15, ZG + 2.28, 'nb_garage_white')
    zr = k.front_gable_roof(gx0, gx1, gy0 - 0.1, y0 + 1.0, zb, 0.72, ov=0.32, tri_mat='brick' if oculus_brick else 'siding')
    xm = (gx0 + gx1) / 2
    k.trim.lathe(xm, gy0 - 0.14, zr - 0.95, [(0.0, 0.0), (0.26, 0.0), (0.26, 0.06), (0.0, 0.06)], seg=24)
    k.trim.cylinder(xm, gy0 - 0.2, zr - 0.95, zr - 0.945, 0.2, seg=24)
    Face('X', gy0 - 0.13, -1).box(k.dark, xm - 0.19, xm + 0.19, 0.0, 0.01, zr - 1.14, zr - 0.76)
    if entry_x1:
        # one-storey entry wing right of the bump under a low roof (31: roof at u 520-575 beside the bump's gable)
        ey0 = gy0 + 1.0
        k.box(gx1, entry_x1, ey0, y0, ZG - 0.2, ZG + 2.7)
        k.siding(Face('X', ey0, -1), gx1 + 0.1, entry_x1, ZG + 0.1, ZG + 2.7, holes=[(gx1 + 0.35, gx1 + 1.35, ZG + 0.2, ZG + 2.5)])
        k.siding(Face('Y', entry_x1, 1), ey0, y0, ZG + 0.1, ZG + 2.7)
        k.door(Face('X', ey0, -1), gx1 + 0.45, gx1 + 1.25, ZG + 0.3, ZG + 2.33)
        k.shed_roof(gx1 + 0.1, entry_x1 + 0.3, ey0, y0, ZG + 2.7, 0.40, ov=0.4)
        k.trim.box(gx1 + 0.1, entry_x1, ey0 - 0.9, ey0, ZG + 0.05, ZG + 0.28)                   # stoop
    k.build()
    if dish:                                     # satellite dish on the east wall (30, 31)
        d = MB()
        d.lathe(x1 + 0.35, 11.0, ZG + 4.1, [(0.0, 0.0), (0.2, 0.04), (0.34, 0.14), (0.35, 0.16), (0.0, 0.05)], seg=20)
        d.box(x1, x1 + 0.3, 10.97, 11.03, ZG + 3.95, ZG + 4.0)
        d.build(f"{name}_Dish", [M['trim']], coll='Neighbours')


def left_house(M):
    """The left neighbour (31: bump roof edges x -11.7 .. -4.1 incl. its entry wing, door -11.25 .. -6.43)."""
    bump_house("NbrL", M, -18.7, -5.6, 5.0, 16.0, -11.45, -5.72, (-11.25, -6.43), M['nb_cream'], M['nb_roof_tan'], M['nb_tanbrick'],
               dish=True, entry_x1=-4.35)


def left_left_house(M):
    """The house beyond the left neighbour (31 left edge): the same type in beige siding with a RED brick bump and a grey
    roof; main block to x -21.9, bump -28.2 .. -22.1, door -27.56 .. -22.75 (SITE_FAR's aerial solve)."""
    bump_house("NbrLL", M, -34.5, -21.9, 5.2, 15.8, -28.2, -22.1, (-27.56, -22.75), M['siding_beige'], M['nb_roof_grey'], M['brick'],
               oculus_brick=True)


# ---------------------------------------------------------------- the right neighbour (x > 12.3)
def right_house(M):
    k = Kit("NbrR", M, M['nb_sage'], M['nb_roof_grey'], brick=M['brick'])
    bx0, bx1, by0, by1 = 17.45, 29.75, 2.0, 12.5
    ze = ZG + 5.85
    k.box(bx0, bx1, by0, by1, ZG - 0.2, ze)
    F, B, L, R = Face('X', by0, -1), Face('X', by1, 1), Face('Y', bx0, -1), Face('Y', bx1, 1)
    # garage (one storey, brick front with a small window, sage door)
    gx0, gx1, gy0, gy1 = 16.15, 23.55, 0.0, 6.35
    zg = ZG + 2.70
    k.box(gx0, gx1, gy0, gy1, ZG - 0.2, zg)
    GF = Face('X', gy0, -1)
    k.brick(GF, gx0, gx1, ZG - 0.1, zg - 0.2)
    k.siding(Face('Y', gx0, -1), gy0, gy1, ZG + 0.1, zg)
    k.garage_door(Face('X', gy0 - 0.1, -1), 18.02, 22.92, ZG + 0.15, ZG + 2.28, 'nb_garage_sage')
    k.window(Face('X', gy0 - 0.1, -1), 16.6, 17.3, ZG + 1.15, ZG + 1.95, grid=(2, 3))
    # porch + the right part of the ground floor (brick below the shed eave)
    k.brick(Face('X', by0 + 0.2, -1), 23.55, bx1, ZG - 0.1, zg - 0.2)
    k.door(Face('X', by0 + 0.2, -1), 24.2, 25.1, ZG + 0.2, ZG + 2.23)
    k.window(Face('X', by0 + 0.2, -1), 26.6, 28.4, ZG + 0.85, ZG + 2.25, units=2, grid=(3, 2), shutters=True)
    k.trim.box(23.55, 26.6, -0.6, by0 + 0.2, ZG - 0.05, ZG + 0.12)                          # porch slab
    for x in (23.75, 26.4):
        k.trim.box(x - 0.09, x + 0.09, -0.5, -0.32, ZG + 0.12, zg - 0.1)                   # columns
    for xa, xb in ((23.84, 24.4), (25.4, 26.31)):                                          # white railing (30)
        k.trim.box(xa, xb, -0.44, -0.40, ZG + 0.95, ZG + 1.0)
        k.trim.box(xa, xb, -0.44, -0.40, ZG + 0.2, ZG + 0.25)
        n = int((xb - xa) / 0.12)
        for i in range(n + 1):
            xx = xa + (xb - xa) * i / n
            k.trim.box(xx - 0.015, xx + 0.015, -0.435, -0.405, ZG + 0.25, ZG + 0.95)
    k.shed_roof(gx0, 26.6, -0.35, by0, zg, 4 / 12, ov=0.30)
    k.shed_roof(26.6, bx1, by0 + 0.2, by0 + 0.8, zg, 4 / 12, ov=0.30)
    # upper storey faces: siding with the three front gables (31)
    k.siding(F, bx0, bx1, zg, ze, holes=[(18.9, 22.8, zg, ze + 3), (24.05, 25.35, ZG + 3.4, ZG + 5.1), (26.3, 29.75, zg, ze + 3)])
    k.window(F, 24.2, 25.2, ZG + 3.6, ZG + 4.9, grid=(3, 2))
    for (a0, a1, yf, zap, wins) in ((18.9, 22.8, by0, ZG + 7.55, [(19.35, 21.15, 2)]), (21.35, 23.55, by0 - 0.75, ZG + 6.75, [(22.05, 22.85, 1)]),
                                     (26.3, 29.75, by0, ZG + 7.55, [(27.55, 28.45, 1)])):
        GFc = Face('X', yf, -1)
        if yf < by0:
            k.box(a0, a1, yf, by0, zg, ze)
            for (xx, s) in ((a0, -1), (a1, 1)):
                k.siding(Face('Y', xx, s), yf, by0, zg, ze)
        holes = [(w0 - 0.1, w1 + 0.1, ZG + 3.4, ZG + 5.1) for (w0, w1, u) in wins]
        k.siding(GFc, a0, a1, zg if yf < by0 else zg, ze, holes=holes)
        for (w0, w1, u) in wins:
            k.window(GFc, w0, w1, ZG + 3.55, ZG + 5.0, units=u, grid=(3, 2), shutters=True)
        pitch = (zap - ze) / ((a1 - a0) / 2)
        k.front_gable_roof(a0, a1, yf, by0 + 2.6, ze, pitch, ov=0.30)
    k.siding(L, by0, by1, zg, ze, holes=[(8.8, 9.7, ZG + 3.4, ZG + 5.2)])
    k.window(L, 8.9, 9.6, ZG + 3.55, ZG + 5.05)
    k.siding(Face('Y', bx0, -1), gy1, by1, ZG + 0.1, zg)
    k.siding(R, by0, by1, ZG + 0.1, ze, holes=[(5.5, 6.4, ZG + 3.4, ZG + 5.2)])
    k.window(R, 5.6, 6.3, ZG + 3.55, ZG + 5.05)
    bw = [(18.2, 19.1), (21.9, 22.8), (27.4, 28.3)]
    k.siding(B, bx0, bx1, ZG + 0.1, ze, holes=[(a - 0.1, b + 0.1, ZG + 3.4, ZG + 5.2) for a, b in bw] + [(23.6, 25.5, ZG + 0.2, ZG + 2.5)])
    for a, b in bw:
        k.window(B, a, b, ZG + 3.55, ZG + 5.05)
    k.window(B, 23.7, 25.4, ZG + 0.3, ZG + 2.4, grid=(3, 3))
    k.side_gable_roof(bx0, bx1, by0, by1, ze, 0.552, ov=0.35, rake=0.43)
    k.build()
    # basketball hoop at the drive's left edge (30, 31) and the bins at the garage (31)
    h = MB()
    px, py = 17.55, -2.9
    h.cylinder(px, py, ZG - 0.3, ZG + 3.0, 0.055, seg=12, mi=0)
    h.box(px - 0.03, px + 0.03, py - 0.03, py + 0.03, ZG + 2.9, ZG + 3.05, 0)
    h.box(px + 0.05, px + 0.62, py - 0.04, py + 0.04, ZG + 3.0, ZG + 3.06, 0)
    h.box(px + 0.62, px + 0.64, py - 0.55, py + 0.55, ZG + 2.95, ZG + 3.72, 1)                     # backboard
    h.cylinder(px + 0.87, py, ZG + 3.03, ZG + 3.05, 0.23, 0.22, seg=20, mi=2)                      # rim
    h.build("NbrR_Hoop", [M['nb_metal'], M['trim'], M['nb_car_dark']], coll='Neighbours')
    bins = MB()
    for i, (bx, mi) in enumerate(((18.55, 0), (19.35, 1))):
        bins.rbox(bx - 0.3, bx + 0.3, -0.45, 0.25, ZG, ZG + 1.05, r=0.04, mi=mi)
    bins.build("NbrR_Bins", [M['nb_bin_yellow'], M['nb_bin_blue']], coll='Neighbours')


# ---------------------------------------------------------------- cars on the drives (31; staging as photographed)
def car(name, M, x, y, yaw, paint, L=4.8, W=1.9, H=1.7, suv=True):
    """A parked car as rounded massing: body, glasshouse, four wheels (yaw = heading of the nose, radians from +X)."""
    c, s = math.cos(yaw), math.sin(yaw)
    mb = MB()
    body_h = 0.62 if suv else 0.5
    z0 = ZG + 0.28

    def pt(u, v, z):
        return (x + u * c - v * s, y + u * s + v * c, z)
    mb.rcbox(x, y, z0 + body_h / 2, L, W, body_h, r=0.14, rot=yaw, mi=0)
    top_l = L * (0.60 if suv else 0.48)
    off = -0.06 * L if suv else -0.02 * L
    gh = H - body_h - 0.28
    mb.rcbox(x + off * c, y + off * s, z0 + body_h + gh / 2 - 0.02, top_l, W * 0.86, gh, r=0.12, rot=yaw, mi=1)
    for (u, v) in ((L * 0.32, W * 0.40), (L * 0.32, -W * 0.40), (-L * 0.32, W * 0.40), (-L * 0.32, -W * 0.40)):
        side = 1 if v > 0 else -1
        mb.tube(pt(u, v - side * 0.1, ZG + 0.36), pt(u, v + side * 0.14, ZG + 0.36), 0.35, 0.35, seg=18, mi=2)
    mb.build(name, [paint, M['nb_car_glass'], M['nb_tyre']], coll='Neighbours', smooth=True)


def street_row(M, simple_house):
    """Houses further along the street (both directions) and across it: simplified massing (site.simple_house)."""
    import random
    rng = random.Random(11)
    pal = [M['siding_beige'], M['siding_grey'], M['nb_sage'], M['siding_bluegrey'], M['siding_tan'], M['nb_cream'], M['siding_mocha']]
    roofs = [M['nb_roof_grey'], M['nb_roof_tan']]
    left_left_house(M)
    for i, x in enumerate([41.5, -47.0]):                   # (x > 52: SITE_FAR's corner lot inside the street's curve)
        simple_house(f"NbrS{i + 1}", M, x - 6.2, x + 6.2, 1.8 + rng.uniform(-0.3, 0.6), 12.3, 5.85, pal[(i + 2) % 7], roofs[i % 2],
                     gable='side', garage=(x - 7.4, x - 0.3, 1.8, 'garage_white'), brick_front=bool(i % 2),
                     front_gables=[(x - 5.8, x - 2.4)] if i % 2 == 0 else [(x + 1.0, x + 4.6)],
                     wins=[(x + 2.8, 3.5, 0.9, 1.5), (x - 1.5, 3.5, 0.9, 1.5)])
    yb = -22.37 - 7.5
    for i, x in enumerate([-40.0, -22.0, -4.0, 14.0, 32.0, 50.0]):
        simple_house(f"NbrX{i}", M, x - 6.2, x + 6.2, yb - 10.5, yb, 5.85, pal[(i + 2) % 7], roofs[(i + 1) % 2],
                     gable='front' if i % 3 == 0 else 'side', brick_front=(i % 2 == 0), wins=[])
