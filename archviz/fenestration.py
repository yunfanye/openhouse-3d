"""Window and door units for framed / veneered houses (vinyl single-hung windows with grilles, shutters, raised-panel
entry and interior doors, sectional garage doors, sliding patio doors, horizontal blinds).  House-agnostic.

All builders take an `archviz.cladding.Face` for the wall's OUTER face plane and local coordinates:
a (along the wall), d (outward from that face; negative = into the wall), z.  `depth` is the wall thickness
measured inward from the face, so the room-side face is at d = -depth.

Material slots are passed explicitly (mi_*); the caller builds with the matching material list.
"""
import math


def _frame(face, mb, a0, a1, z0, z1, w, d0, d1, mi, bottom=True):
    face.box(mb, a0, a0 + w, d0, d1, z0, z1, mi)
    face.box(mb, a1 - w, a1, d0, d1, z0, z1, mi)
    face.box(mb, a0 + w, a1 - w, d0, d1, z1 - w, z1, mi)
    if bottom:
        face.box(mb, a0 + w, a1 - w, d0, d1, z0, z0 + w, mi)


def grille(face, mb, a0, a1, z0, z1, nx, ny, d, w=0.016, t=0.010, mi=0):
    """Flat colonial grid between the panes: nx columns x ny rows of lites."""
    for i in range(1, nx):
        a = a0 + (a1 - a0) * i / nx
        face.box(mb, a - w / 2, a + w / 2, d - t / 2, d + t / 2, z0, z1, mi)
    for j in range(1, ny):
        z = z0 + (z1 - z0) * j / ny
        face.box(mb, a0, a1, d - t / 2, d + t / 2, z - w / 2, z + w / 2, mi)


def single_hung(face, mb, a0, a1, z0, z1, depth, grid=(3, 2), lower_grid=True, units=1, mullion=0.06,
                mi_frame=0, mi_glass=1, mi_grille=2, mi_return=3, mi_casing=4, interior=True, recess=0.035,
                casing_w=0.066, stool=True, frame=0.05, sash=0.042, fixed=False, grille_w=0.016, lower_grid_rows=None):
    """Vinyl single-hung window(s) filling the rough opening a0..a1 x z0..z1.  `units` side-by-side sashes share a
    mullion.  Grilles in the upper sash (grid = (cols, rows)); the lower sash gets the same grid unless lower_grid is
    False (`lower_grid_rows` overrides its row count).  Interior: drywall returns to the room face (mi_return), a flat
    casing and a stool.  `frame` / `sash` are the vinyl frame and sash-stile widths; `fixed` = one lite per unit (a
    picture / garage window) with the whole `grid` over it."""
    fw = frame
    d_out, d_in = -recess, -recess - 0.10
    _frame(face, mb, a0, a1, z0, z1, fw, d_in, d_out, mi_frame)
    uw = (a1 - a0 - 2 * fw - (units - 1) * mullion) / units
    for u in range(units):
        ua0 = a0 + fw + u * (uw + mullion)
        ua1 = ua0 + uw
        if u:
            face.box(mb, ua0 - mullion, ua0, d_in, d_out, z0, z1, mi_frame)
        zi0, zi1 = z0 + fw, z1 - fw
        zm = (zi0 + zi1) / 2
        sw = sash
        if fixed:
            dd0, dd1 = d_out - 0.030, d_out - 0.005
            _frame(face, mb, ua0, ua1, zi0, zi1, sw, dd0, dd1, mi_frame)
            dm = (dd0 + dd1) / 2
            face.box(mb, ua0 + sw, ua1 - sw, dm - 0.003, dm + 0.003, zi0 + sw, zi1 - sw, mi_glass)
            if grid:
                grille(face, mb, ua0 + sw, ua1 - sw, zi0 + sw, zi1 - sw, grid[0], grid[1], dm, w=grille_w, mi=mi_grille)
            continue
        # upper sash (outer track) and lower sash (inner track), meeting rails overlap at zm
        for (s0, s1, dd0, dd1, gz, rows) in ((zm - 0.015, zi1, d_out - 0.030, d_out - 0.005, True, None),
                                               (zi0, zm + 0.015, d_out - 0.060, d_out - 0.035, lower_grid, lower_grid_rows)):
            _frame(face, mb, ua0, ua1, s0, s1, sw, dd0, dd1, mi_frame)
            dm = (dd0 + dd1) / 2
            face.box(mb, ua0 + sw, ua1 - sw, dm - 0.003, dm + 0.003, s0 + sw, s1 - sw, mi_glass)
            if gz and grid:
                grille(face, mb, ua0 + sw, ua1 - sw, s0 + sw, s1 - sw, grid[0], rows or grid[1], dm, w=grille_w, mi=mi_grille)
        face.box(mb, ua0 + 0.02, ua0 + 0.07, d_out - 0.066, d_out - 0.058, zm + 0.02, zm + 0.035, mi_frame)   # sash lift
    if interior and depth > recess + 0.1:
        dr0, dr1 = -depth, d_in
        face.box(mb, a0 - 0.012, a0, dr0, dr1, z0, z1, mi_return)
        face.box(mb, a1, a1 + 0.012, dr0, dr1, z0, z1, mi_return)
        face.box(mb, a0 - 0.012, a1 + 0.012, dr0, dr1, z1, z1 + 0.012, mi_return)
        face.box(mb, a0 - 0.012, a1 + 0.012, dr0, dr1, z0 - 0.012, z0, mi_return)
        cw = casing_w
        face.box(mb, a0 - cw, a0, -depth - 0.016, -depth, z0 - (cw if not stool else 0.0), z1 + cw, mi_casing)
        face.box(mb, a1, a1 + cw, -depth - 0.016, -depth, z0 - (cw if not stool else 0.0), z1 + cw, mi_casing)
        face.box(mb, a0 - cw, a1 + cw, -depth - 0.016, -depth, z1, z1 + cw, mi_casing)
        if stool:
            face.box(mb, a0 - cw - 0.03, a1 + cw + 0.03, -depth - 0.045, -depth + 0.02, z0 - 0.022, z0, mi_casing)
            face.box(mb, a0 - cw, a1 + cw, -depth - 0.016, -depth, z0 - 0.022 - cw, z0 - 0.022, mi_casing)   # apron
        else:
            face.box(mb, a0 - cw, a1 + cw, -depth - 0.016, -depth, z0 - cw, z0, mi_casing)


def blinds(face, mb, a0, a1, z0, z1, depth, drop=1.0, tilt=0.35, slat=0.025, pitch=0.022, mi=0, mi_rail=None, inset=0.02):
    """Horizontal slat blind hung inside the window's room-side return; `drop` = lowered fraction (1 = closed down),
    `tilt` = slat angle (radians)."""
    mi_rail = mi if mi_rail is None else mi_rail
    d = -depth + inset + slat / 2 + 0.01
    face.box(mb, a0 + 0.01, a1 - 0.01, d - 0.03, d + 0.03, z1 - 0.06, z1 - 0.005, mi_rail)            # head rail
    zb = z1 - 0.06 - (z1 - 0.06 - z0) * drop
    n = max(1, int((z1 - 0.06 - zb) / pitch))
    c, s = math.cos(tilt), math.sin(tilt)
    for i in range(n):
        z = z1 - 0.07 - i * pitch
        h = slat / 2
        # a thin tilted slat: a hexahedron with the cross-section rotated by `tilt`
        q = [(-h * c, -h * s - 0.0006), (h * c, h * s - 0.0006), (h * c, h * s + 0.0006), (-h * c, -h * s + 0.0006)]
        verts = [(a0 + 0.012, d + dd, z + dz) for dd, dz in q] + [(a1 - 0.012, d + dd, z + dz) for dd, dz in q]
        face.quad8(mb, [verts[0], verts[1], verts[2], verts[3], verts[4], verts[5], verts[6], verts[7]], mi)
    face.box(mb, a0 + 0.012, a1 - 0.012, d - 0.014, d + 0.014, zb - 0.02, zb, mi_rail)                  # bottom rail


def shutter(face, mb, a0, a1, z0, z1, d=0.03, t=0.03, mi=0, panels=2):
    """Raised-panel exterior shutter (stiles, rails and raised panels proud of the frame)."""
    sw = 0.06
    face.box(mb, a0, a1, d, d + t * 0.6, z0, z1, mi)
    face.box(mb, a0, a0 + sw, d, d + t, z0, z1, mi)
    face.box(mb, a1 - sw, a1, d, d + t, z0, z1, mi)
    gap = 0.07
    h = (z1 - z0 - (panels + 1) * gap) / panels
    for i in range(panels + 1):
        zz = z0 + i * (h + gap)
        face.box(mb, a0 + sw, a1 - sw, d, d + t, zz, zz + gap, mi)
    for i in range(panels):
        zz = z0 + gap + i * (h + gap)
        face.box(mb, a0 + sw + 0.025, a1 - sw - 0.025, d, d + t * 0.95, zz + 0.025, zz + h - 0.025, mi)


def panel_leaf(face, mb, a0, a1, z0, z1, d0, d1, layout='six', mi_out=0, mi_in=None, raise_=0.008, bevel=0.0):
    """Door slab between d0 < d1 (the d1 face is the exterior / mi_out side) with raised panels on both faces.  layout: 'six' (colonial six
    panel), 'six_colonial' (small panels at the top), 'two' (two tall arched-look panels), 'flat'.  mi_in defaults to mi_out.
    `bevel` > 0 draws each raised field as a frustum with sloped edges of that width (catches light like a pressed-steel door)."""
    mi_in = mi_out if mi_in is None else mi_in
    dm = (d0 + d1) / 2
    face.box(mb, a0, a1, dm, d1, z0, z1, mi_out)
    face.box(mb, a0, a1, d0, dm, z0, z1, mi_in)
    W, H = a1 - a0, z1 - z0
    st = 0.12 * W / 0.91
    if layout == 'six':
        rows = [(0.08, 0.36), (0.44, 0.61), (0.69, 0.93)]      # fractions of height, bottom to top
        cols = [(st / W, 0.5 - 0.06), (0.5 + 0.06, 1 - st / W)]
    elif layout == 'six_colonial':                              # the small panels at the top (a colonial six-panel)
        rows = [(0.10, 0.41), (0.49, 0.75), (0.83, 0.93)]
        cols = [(st / W, 0.5 - 0.06), (0.5 + 0.06, 1 - st / W)]
    elif layout == 'two':
        rows = [(0.07, 0.40), (0.48, 0.93)]
        cols = [(st / W, 1 - st / W)]
    else:
        rows, cols = [], []
    for (r0, r1) in rows:
        for (c0, c1) in cols:
            pa0, pa1, pz0, pz1 = a0 + W * c0, a0 + W * c1, z0 + H * r0, z0 + H * r1
            if bevel > 0:
                b = bevel
                for (dd, sgn, mi) in ((d1, 1, mi_out), (d0, -1, mi_in)):
                    dr = dd + sgn * raise_
                    face.quad8(mb, [(pa0, dd, pz0), (pa1, dd, pz0), (pa1 - b, dr, pz0 + b), (pa0 + b, dr, pz0 + b),
                                    (pa0, dd, pz1), (pa1, dd, pz1), (pa1 - b, dr, pz1 - b), (pa0 + b, dr, pz1 - b)] if sgn > 0 else
                               [(pa0 + b, dr, pz0 + b), (pa1 - b, dr, pz0 + b), (pa1, dd, pz0), (pa0, dd, pz0),
                                (pa0 + b, dr, pz1 - b), (pa1 - b, dr, pz1 - b), (pa1, dd, pz1), (pa0, dd, pz1)], mi)
                continue
            for (dd, sgn, mi) in ((d1, 1, mi_out), (d0, -1, mi_in)):
                # bevelled raised field: a slightly smaller box proud of the face + a thin inner step
                face.box(mb, pa0 + 0.018, pa1 - 0.018, dd if sgn > 0 else dd - raise_, dd + raise_ if sgn > 0 else dd, pz0 + 0.018, pz1 - 0.018, mi)
                face.box(mb, pa0, pa1, dd if sgn > 0 else dd - raise_ * 0.35, dd + raise_ * 0.35 if sgn > 0 else dd, pz0, pz0 + 0.006, mi)
                face.box(mb, pa0, pa1, dd if sgn > 0 else dd - raise_ * 0.35, dd + raise_ * 0.35 if sgn > 0 else dd, pz1 - 0.006, pz1, mi)


def lever(face, mb, a, z, d, side=1, mi=0, knob=False):
    """Door hardware: a round rose + a lever (or knob) projecting outward by `side` from the face at d."""
    face.box(mb, a - 0.028, a + 0.028, d, d + side * 0.012, z - 0.028, z + 0.028, mi)
    if knob:
        face.box(mb, a - 0.024, a + 0.024, d + side * 0.012, d + side * 0.065, z - 0.024, z + 0.024, mi)
    else:
        face.box(mb, a - 0.01, a + 0.01, d + side * 0.012, d + side * 0.06, z - 0.01, z + 0.01, mi)
        face.box(mb, a - 0.12 if side > 0 else a - 0.01, a + 0.01, d + side * 0.05, d + side * 0.068, z - 0.012, z + 0.012, mi)


def garage_door(face, mb, a0, a1, z0, z1, d=0.0, sections=4, cols=8, mi=0, mi_hw=None, style='flat', margin=0.05,
                panel_gap=0.07, rail=0.07, joint=0.004, lock=True):
    """Sectional steel garage door with short raised panels (cols per section).  style='bevel' draws each panel as a
    raised field with sloped (bevelled) edges and a recessed section joint, so raking light draws the shadow lines of
    a pressed-steel door; 'flat' is the original stepped panel.  `margin` = the flat border at the door's sides,
    `panel_gap` = the flat stile between panels, `rail` = the flat rail above / below the panels in each section."""
    mi_hw = mi if mi_hw is None else mi_hw
    H = (z1 - z0) / sections
    face.box(mb, a0, a1, d - 0.04, d - 0.005, z0, z1, mi)
    for s in range(sections):
        zs = z0 + s * H
        face.box(mb, a0, a1, d - 0.005, d, zs + joint, zs + H - joint, mi)          # section face (joint lines between)
        pw = (a1 - a0 - 2 * margin) / cols
        for c in range(cols):
            pa0 = a0 + margin + c * pw
            if style == 'bevel':
                g = panel_gap / 2
                b = 0.028                                                           # bevel width
                x0_, x1_, y0_, y1_ = pa0 + g, pa0 + pw - g, zs + rail, zs + H - rail
                face.quad8(mb, [(x0_, d, y0_), (x1_, d, y0_), (x1_, d + 0.004, y0_), (x0_, d + 0.004, y0_),
                                (x0_, d, y1_), (x1_, d, y1_), (x1_, d + 0.004, y1_), (x0_, d + 0.004, y1_)], mi)
                # raised field: a frustum from the panel outline (d + 0.004) to the field (d + 0.016)
                face.quad8(mb, [(x0_, d + 0.004, y0_), (x1_, d + 0.004, y0_), (x1_ - b, d + 0.016, y0_ + b), (x0_ + b, d + 0.016, y0_ + b),
                                (x0_, d + 0.004, y1_), (x1_, d + 0.004, y1_), (x1_ - b, d + 0.016, y1_ - b), (x0_ + b, d + 0.016, y1_ - b)], mi)
            else:
                face.box(mb, pa0 + 0.035, pa0 + pw - 0.035, d, d + 0.010, zs + 0.07, zs + H - 0.07, mi)
                face.box(mb, pa0 + 0.06, pa0 + pw - 0.06, d + 0.010, d + 0.016, zs + 0.095, zs + H - 0.095, mi)
    if lock:
        am = (a0 + a1) / 2
        face.box(mb, am - 0.03, am + 0.03, d, d + 0.03, z0 + 0.95, z0 + 1.01, mi_hw)    # lock / handle


def slider(face, mb, a0, a1, z0, z1, depth, grid=(3, 5), mi_frame=0, mi_glass=1, mi_grille=2, mi_hw=3, mi_return=4, mi_casing=5,
           recess=0.035, frame=0.06, stile=0.07, grille_w=0.016, rail_bottom=None, fixed_side=1):
    """Two-panel vinyl sliding patio door (fixed panel outside, operable panel inside) with colonial grilles.
    `frame` = outer frame width, `stile` = panel stile / rail width (`rail_bottom` optionally wider), `grille_w` =
    the flat grille bar width; `fixed_side` = +1 puts the fixed (outer) panel on the +a half (today's layout), -1 on
    the -a half."""
    fw = frame
    d_out, d_in = -recess, -recess - 0.12
    _frame(face, mb, a0, a1, z0, z1, fw, d_in, d_out, mi_frame)
    am = (a0 + a1) / 2
    pw = stile
    pb = pw if rail_bottom is None else rail_bottom
    halves = ((am - 0.02, a1 - fw), (a0 + fw, am + 0.02))
    if fixed_side < 0:
        halves = (halves[1], halves[0])
    for ((p0, p1), (dd0, dd1)) in zip(halves, ((d_out - 0.05, d_out - 0.01), (d_out - 0.10, d_out - 0.06))):
        _frame(face, mb, p0, p1, z0 + fw, z1 - fw, pw, dd0, dd1, mi_frame)
        if pb > pw:
            face.box(mb, p0 + pw, p1 - pw, dd0, dd1, z0 + fw + pw, z0 + fw + pb, mi_frame)
        dm = (dd0 + dd1) / 2
        face.box(mb, p0 + pw, p1 - pw, dm - 0.003, dm + 0.003, z0 + fw + pb, z1 - fw - pw, mi_glass)
        if grid:
            grille(face, mb, p0 + pw, p1 - pw, z0 + fw + pb, z1 - fw - pw, grid[0], grid[1], dm, w=grille_w, mi=mi_grille)
    face.box(mb, am - 0.06, am - 0.045, d_in - 0.02, d_in + 0.005, z0 + 0.85, z0 + 1.15, mi_hw)        # pull (inside)
    face.box(mb, a0, a1, d_in, d_out, z0 - 0.02, z0 + 0.01, mi_frame)                                   # sill track
    if depth > recess + 0.12:
        face.box(mb, a0 - 0.012, a0, -depth, d_in, z0, z1, mi_return)
        face.box(mb, a1, a1 + 0.012, -depth, d_in, z0, z1, mi_return)
        face.box(mb, a0 - 0.012, a1 + 0.012, -depth, d_in, z1, z1 + 0.012, mi_return)
        cw = 0.066
        face.box(mb, a0 - cw, a0, -depth - 0.016, -depth, z0, z1 + cw, mi_casing)
        face.box(mb, a1, a1 + cw, -depth - 0.016, -depth, z0, z1 + cw, mi_casing)
        face.box(mb, a0 - cw, a1 + cw, -depth - 0.016, -depth, z1, z1 + cw, mi_casing)


def interior_door_frame(face, mb, a0, a1, z0, z1, depth, mi=0, cw=0.066, t=0.016):
    """Jambs + head lining the wall opening through its full `depth` and flat casings on both faces."""
    face.box(mb, a0, a0 + 0.018, -depth, 0, z0, z1, mi)
    face.box(mb, a1 - 0.018, a1, -depth, 0, z0, z1, mi)
    face.box(mb, a0, a1, -depth, 0, z1 - 0.018, z1, mi)
    for (d0, d1) in ((0, t), (-depth - t, -depth)):
        face.box(mb, a0 - cw + 0.018, a0 + 0.018, d0, d1, z0, z1 + cw - 0.018, mi)
        face.box(mb, a1 - 0.018, a1 + cw - 0.018, d0, d1, z0, z1 + cw - 0.018, mi)
        face.box(mb, a0 - cw + 0.018, a1 + cw - 0.018, d0, d1, z1 - 0.018, z1 + cw - 0.018, mi)
