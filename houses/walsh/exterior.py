"""Building envelope: main block walls + slabs, entry, stair lantern + wood box, living/family pavilions,
upper floor, roof terraces, roof slab, north arm shell, NE canopy, west stair, exterior soffit lights.

Detail pass (hyper-realism): real window / slider frame profiles with glazing beads, 2-track sills, meeting
stiles + pulls; 10 mm shadow gaps at every stone/slab junction; cladding corner returns; portal reveal;
bronze onyx reveals; roof coping + scuppers; turf edge trims; 8 mm perforated fascia with returns; two-tone
slats with end caps + steel outriggers; real light fixtures; tread nosings, rail shoe caps, handrail; door
pull with standoffs + pivot plate; house number, intercom, hose bib.

Interior partitions / finishes / furniture / room lights are NOT built here (interior_* modules)."""
import math
from .plan import *
from archviz.mesh import *
from archviz.lights import *
from archviz.parts import *
from archviz import materials as _mat

DK = 0.010          # shadow-gap size
LOCAL = {}          # exterior-only materials, filled by build()


# ---------------------------------------------------------------- small helpers
def _edge_strip(mb, x0, x1, y0, y1, z0, z1, out=0.015, mi=0):
    """Thin dark drip-edge band wrapped around the outer faces of a rectangular slab outline."""
    mb.box(x0 - out, x1 + out, y0 - out, y0, z0, z1, mi)
    mb.box(x0 - out, x1 + out, y1, y1 + out, z0, z1, mi)
    mb.box(x0 - out, x0, y0, y1, z0, z1, mi)
    mb.box(x1, x1 + out, y0, y1, z0, z1, mi)


def _gravel_plate(mb, x0, x1, y0, y1, z, holes=(), inset=0.12, t=0.02, mi=0):
    mb.plate(x0 + inset, x1 - inset, y0 + inset, y1 - inset, z, z + t,
             holes=[(hx0 - inset, hx1 + inset, hy0 - inset, hy1 + inset) for (hx0, hx1, hy0, hy1) in holes], mi=mi)


def _coping(mb, x0, x1, y0, y1, z, w=0.12, h=0.03, mi=0):
    """Raised roof-edge coping rim (a ring `w` wide, `h` tall) on top of a roof plate outline."""
    mb.frame(x0, x1, y0, y1, z, z + h, w, mi=mi, axis='Z')


def _spots(prefix, pts, z, energy=70, spot=100, blend=0.6, color=WARM):
    for i, (x, y) in enumerate(pts):
        add_light(f"{prefix}_{i}", 'SPOT', (x, y, z - 0.03), energy, color, size=0.05,
                  spot=math.radians(spot), blend=blend, target=(x, y, z - 10))


def _gap_x(mb, x0, x1, y, z, face=-1, mi=0, t=DK):
    """Horizontal 10 mm shadow gap on a wall face running along X at plane y; face=-1 -> the face looks toward -Y."""
    mb.box(x0, x1, y + (face * 0.004 if face < 0 else 0), y + (0 if face < 0 else face * 0.004), z, z + t, mi)


def _gap_y(mb, y0, y1, x, z, face=-1, mi=0, t=DK):
    mb.box(x + (face * 0.004 if face < 0 else 0), x + (0 if face < 0 else face * 0.004), y0, y1, z, z + t, mi)


def _corner_return(mb, x, y, z0, z1, sx, sy, mi=0, w=0.03):
    """Cladding corner return: a 30 mm vertical strip standing 3 mm proud on both faces of an outside corner
    at (x, y); sx, sy = the directions (+/-1) the wall extends from the corner."""
    x0, x1 = (x - 0.003, x + w) if sx > 0 else (x - w, x + 0.003)
    y0, y1 = (y - 0.003, y + w) if sy > 0 else (y - w, y + 0.003)
    mb.box(x0, x1, y0, y1, z0, z1, mi)


def _glazing(mb, along, a0, a1, b, z0, z1, mi_glass=0, mi_frame=1, panels=(), slider=False, fw=0.05, fd=0.06,
             handle=True, mi_edge=None, bead=True, stack=None):
    """Framed glazing in a vertical plane.  along='X': a = x, b = the y plane;  along='Y': a = y, b = the x plane.
    50 mm frame of depth fd, 20 mm glazing beads stepped 8 mm proud of the glass, mullions at `panels`.
    slider=True: alternate panels sit on the outer / inner track (+-18 mm), a 2-rib sill and head track,
    60 mm meeting stiles and a vertical pull on each sliding panel.
    stack='start'|'end': a multi-slide that is OPEN - every panel on its own track (32 mm apart), all parked at
    that end of the opening (photos 04/10: the living pavilion stands open as an air-through loggia)."""
    def B(aa0, aa1, bb0, bb1, zz0, zz1, mi):
        if along == 'X':
            mb.box(aa0, aa1, bb0, bb1, zz0, zz1, mi)
        else:
            mb.box(bb0, bb1, aa0, aa1, zz0, zz1, mi)
    bounds = [a0 + fw] + sorted(panels) + [a1 - fw]
    n = len(bounds) - 1
    if stack:
        offs = [(i - (n - 1) / 2) * 0.032 for i in range(n)]
        fd = max(fd, (n - 1) * 0.032 + 0.05)
    else:
        offs = [(-0.018 if i % 2 == 0 else 0.018) if slider else 0.0 for i in range(n)]
    hb = fd / 2
    B(a0, a1, b - hb, b + hb, z0, z0 + fw, mi_frame)                      # sill
    B(a0, a1, b - hb, b + hb, z1 - fw, z1, mi_frame)                      # head
    B(a0, a0 + fw, b - hb, b + hb, z0, z1, mi_frame)
    B(a1 - fw, a1, b - hb, b + hb, z0, z1, mi_frame)
    if slider:                                                            # one rib per track on the sill / head
        for off in sorted(set(offs)):
            B(a0 + fw, a1 - fw, b + off - 0.004, b + off + 0.004, z0 + fw, z0 + fw + 0.008, mi_frame)
            B(a0 + fw, a1 - fw, b + off - 0.004, b + off + 0.004, z1 - fw - 0.008, z1 - fw, mi_frame)
    for m in panels:
        if not slider:
            B(m - fw / 2, m + fw / 2, b - hb, b + hb, z0 + fw, z1 - fw, mi_frame)
    pw = (a1 - a0 - 2 * fw) / n
    for i in range(n):
        if stack == 'start':
            pa0, pa1 = a0 + fw, a0 + fw + pw
        elif stack == 'end':
            pa0, pa1 = a1 - fw - pw, a1 - fw
        else:
            pa0 = bounds[i] + (0 if i == 0 else (0.0 if slider else fw / 2))
            pa1 = bounds[i + 1] - (0 if i == n - 1 else (0.0 if slider else fw / 2))
        off = offs[i]
        bb = b + off
        gz0, gz1 = z0 + fw, z1 - fw
        if slider:
            # each sliding panel is its own 45 mm frame (stile + rails) around its pane
            sw = 0.045
            B(pa0, pa1, bb - 0.022, bb + 0.022, gz0, gz0 + sw, mi_frame)
            B(pa0, pa1, bb - 0.022, bb + 0.022, gz1 - sw, gz1, mi_frame)
            B(pa0, pa0 + sw, bb - 0.022, bb + 0.022, gz0, gz1, mi_frame)
            B(pa1 - sw, pa1, bb - 0.022, bb + 0.022, gz0, gz1, mi_frame)
            B(pa0 + sw, pa1 - sw, bb - T / 2, bb + T / 2, gz0 + sw, gz1 - sw, mi_glass)
            if handle and n > 1 and (not stack or i == n - 1):
                # meeting stile side: a slim vertical pull 25 mm proud, 600 mm long
                hx = pa1 - sw - 0.05 if i % 2 == 0 else pa0 + sw + 0.05
                side = -1 if i % 2 == 0 else 1
                B(hx - 0.012, hx + 0.012, bb + side * (0.022 + 0.006), bb + side * (0.022 + 0.030), z0 + 0.95, z0 + 1.55, mi_frame)
                for zz in (z0 + 0.98, z0 + 1.52):
                    B(hx - 0.008, hx + 0.008, bb + side * 0.022, bb + side * (0.022 + 0.008), zz, zz + 0.02, mi_frame)
        else:
            B(pa0, pa1, bb - T / 2, bb + T / 2, gz0, gz1, mi_glass)
            if bead:                                                       # 20 mm glazing beads, 8 mm proud, both faces
                for s0, s1 in ((bb + T / 2, bb + T / 2 + 0.008), (bb - T / 2 - 0.008, bb - T / 2)):
                    B(pa0, pa1, s0, s1, gz0, gz0 + 0.02, mi_frame)
                    B(pa0, pa1, s0, s1, gz1 - 0.02, gz1, mi_frame)
                    B(pa0, pa0 + 0.02, s0, s1, gz0 + 0.02, gz1 - 0.02, mi_frame)
                    B(pa1 - 0.02, pa1, s0, s1, gz0 + 0.02, gz1 - 0.02, mi_frame)
        if mi_edge is not None:                                            # 6 mm green glass edge visible in the reveal
            B(pa0 - 0.001, pa0 + 0.006, bb - T / 2, bb + T / 2, gz0, gz1, mi_edge)
            B(pa1 - 0.006, pa1 + 0.001, bb - T / 2, bb + T / 2, gz0, gz1, mi_edge)


def _rail_caps(mb, pts, z0, mi=0, every=0.6):
    """Stainless cover caps on a glass-rail shoe every 0.6 m along a polyline."""
    for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
        L = math.hypot(bx - ax, by - ay)
        k = max(1, int(L / every))
        for i in range(k):
            t = (i + 0.5) / k
            x, y = ax + (bx - ax) * t, ay + (by - ay) * t
            mb.rbox(x - 0.02, x + 0.02, y - 0.02, y + 0.02, z0 + 0.08, z0 + 0.095, 0.006, mi)


def _glass_edges(mb, pts, z0, h, mi=0):
    """6 mm green edge strips at the ends of each glass-rail segment (where the pane's edge is visible)."""
    for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
        for (x, y) in ((ax, ay), (bx, by)):
            mb.box(x - 0.004, x + 0.004, y - 0.004, y + 0.004, z0 + 0.08, z0 + h - 0.02, mi)


def _fixture(mb, x, y, z, h=1.2, along='X', out=0.05, mi_body=0, mi_lens=1):
    """Vertical linear wall light: 40 mm black housing standing `out` proud, lens inset 2 mm."""
    if along == 'X':
        mb.box(x - 0.025, x + 0.025, y - out, y, z - h / 2 - 0.03, z + h / 2 + 0.03, mi_body)
        mb.box(x - 0.016, x + 0.016, y - out - 0.001, y - out + 0.002, z - h / 2, z + h / 2, mi_lens)
    else:
        mb.box(y - out, y, x - 0.025, x + 0.025, z - h / 2 - 0.03, z + h / 2 + 0.03, mi_body)
        mb.box(y - out - 0.001, y - out + 0.002, x - 0.016, x + 0.016, z - h / 2, z + h / 2, mi_lens)


def _slats2(mb, axis, a0, a1, b, depth, z0, z1, w=0.085, gap=0.028, sign=1, mi0=0, mi1=1):
    """Vertical slats alternating between two material slots (two timber tones)."""
    a = a0
    k = 0
    while a + w <= a1 + 1e-6:
        mi = mi0 if k % 2 == 0 else mi1
        if axis == 'X':
            mb.box(a, a + w, b, b + sign * depth, z0, z1, mi)
        else:
            mb.box(b, b + sign * depth, a, a + w, z0, z1, mi)
        a += w + gap
        k += 1


def _perf_panel(mb, along, a0, a1, b, sign, z0, z1, mi=0, t=0.008, proud=0.03):
    """Perforated white parapet panel (photos 01/22): an 8 mm sheet standing `proud` of the fascia face at plane b
    (sign = outward direction), open at the top with a 12 mm folded edge, on stand-off clips every 1.2 m.
    The clips are material slot mi+1."""
    def B(aa0, aa1, bb0, bb1, zz0, zz1, m):
        if along == 'X':
            mb.box(aa0, aa1, bb0, bb1, zz0, zz1, m)
        else:
            mb.box(bb0, bb1, aa0, aa1, zz0, zz1, m)
    f0, f1 = (b + sign * proud, b + sign * (proud + t)) if sign > 0 else (b + sign * (proud + t), b + sign * proud)
    B(a0, a1, f0, f1, z0, z1, mi)
    B(a0, a1, min(f0, f1) - (0.012 if sign < 0 else 0), max(f0, f1) + (0.012 if sign > 0 else 0), z1 - 0.012, z1, mi)   # top fold
    c0, c1 = (b, b + sign * proud) if sign > 0 else (b + sign * proud, b)
    a = a0 + 0.3
    while a < a1 - 0.2:
        for zz in (z0 + 0.08, z1 - 0.12):
            B(a - 0.015, a + 0.015, c0, c1, zz, zz + 0.03, mi + 1)
        a += 1.2


def _local_materials(M):
    """Exterior-only materials (never edit materials.py): golden fins for the box + garage, charcoal fin backing,
    a 4-row perforated panel that fills the taller parapet, and a pebble ballast for the roofs."""
    if 'wood_slat2' not in M:
        M['wood_slat2'] = _mat.wood("WoodSlat2", light=(0.68, 0.46, 0.25, 1), dark=(0.50, 0.31, 0.15, 1), grain_axis='Z', rough=0.52, coat=0.1)
    L = {}
    # light golden oak fins (photo 23): warm blonde, very low red; two close tones so adjacent fins differ a touch
    L['fin_a'] = _mat.wood("WoodFinGoldA", light=(0.80, 0.62, 0.36, 1), dark=(0.66, 0.48, 0.26, 1), grain_axis='Z', rough=0.48, coat=0.12, ring=22.0)
    L['fin_b'] = _mat.wood("WoodFinGoldB", light=(0.74, 0.57, 0.33, 1), dark=(0.61, 0.44, 0.23, 1), grain_axis='Z', rough=0.5, coat=0.12, ring=26.0)
    L['fin_back'] = _mat.new_mat("FinBacking", (0.05, 0.045, 0.04, 1), rough=0.6, metal=0.3)
    L['perf_x'] = _mat.perforated("PerfX4", axis='X', rows=4, z0=Z_SOF + 0.10)
    L['perf_y'] = _mat.perforated("PerfY4", axis='Y', rows=4, z0=Z_SOF + 0.10)
    L['silicone'] = _mat.new_mat("SiliconeJoint", (0.02, 0.02, 0.02, 1), rough=0.55)
    L['ballast'] = _pebble_mat("RoofBallast")
    return L


def _pebble_mat(name):
    """White-grey roof ballast: 15-30 mm rounded pebbles (smooth-F1 voronoi cells, per-cell tint, dark joints
    between stones, strong bump) - reads as gravel at drone distance instead of a flat white plane."""
    m, nt, b = _mat._new(name)
    vec = _mat._coords(nt, scale=(1, 1, 1))
    dn = nt.nodes.new("ShaderNodeTexNoise"); dn.inputs["Scale"].default_value = 30.0; dn.inputs["Detail"].default_value = 2.0
    nt.links.new(dn.inputs["Vector"], vec)
    dv = nt.nodes.new("ShaderNodeVectorMath"); dv.operation = 'MULTIPLY_ADD'; dv.inputs[1].default_value = (0.012, 0.012, 0.012)
    nt.links.new(dv.inputs[0], dn.outputs["Color"]); nt.links.new(dv.inputs[2], vec)
    vor = nt.nodes.new("ShaderNodeTexVoronoi"); vor.feature = 'SMOOTH_F1'
    vor.inputs["Scale"].default_value = 34.0; vor.inputs["Smoothness"].default_value = 0.25; vor.inputs["Randomness"].default_value = 1.0
    nt.links.new(vor.inputs["Vector"], dv.outputs["Vector"])
    csep = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(csep.inputs["Color"], vor.outputs["Color"])
    tint = _mat._ramp(nt, csep.outputs["Red"], [(0.0, (0.58, 0.56, 0.53, 1)), (0.35, (0.78, 0.76, 0.72, 1)), (0.7, (0.90, 0.88, 0.84, 1)), (1.0, (0.97, 0.96, 0.93, 1))])
    d = vor.outputs["Distance"]
    joint = _mat._math(nt, 'GREATER_THAN', d, 0.44)                     # gaps between stones
    col = _mat._mixrgb(nt, joint, tint, (0.25, 0.24, 0.22, 1))
    nt.links.new(b.inputs["Base Color"], col)
    _mat._set(b, "Roughness", 0.8); _mat._set(b, "Specular IOR Level", 0.2)
    h = _mat._math(nt, 'SUBTRACT', 1.0, _mat._math(nt, 'MULTIPLY', d, 2.2, clamp=True))   # domed stones
    _mat._bump(nt, b, h, 1.0, 0.016)
    return m


# ================================================================ ground floor (Z_COURT .. Z_SOF)
def ground_floor(M):
    trav = M['trav']
    g = MB()
    z0, z1 = Z_COURT, Z_SOF
    # front wall: garage, entry glass, onyx slot, small lit window
    g.wall('X', MX0, MX1, MY0, MY0 + WT, z0, z1, holes=[
        (GAR_X0 - 0.15, GAR_X1 + 0.15, z0, GAR_H + 0.15),
        (GLASS_X0, GLASS_X1, z0, z1),
        (4.4, 4.9, 1.4, 4.6),
        (5.6, 7.0, 0.45, 1.35)])
    # west wall with a side door at the top of the west stair (into the kitchen)
    g.wall('Y', MY0, MY1, MX0, MX0 + WT, z0, z1, holes=[(8.6, 9.6, Z_LIV, Z_LIV + 2.4)])
    # east wall: solid beside the foyer, passage into the living room, glass onto the family pavilion
    g.wall('Y', MY0, MY1, MX1 - WT, MX1, z0, z1, holes=[
        (8.4, LIV_Y1, Z_LIV, Z_SOF - 0.4),
        (FAM_Y0, FAM_Y1, Z_LIV, Z_SOF - 0.05)])
    # rear wall: master glass, closet window, office glass
    g.wall('X', MX0, MX1, MY1 - WT, MY1, z0, z1, holes=[
        (-11.8, -5.0, Z_LIV, Z_SOF - 0.5),
        (0.8, 2.6, Z_LIV + 0.9, Z_LIV + 2.5),
        (3.8, 6.9, Z_LIV, Z_SOF - 0.5)])
    # foundation: full under the foyer/garage/billiard, dropped under the sunken lounge + theatre (floor -0.9)
    g.plate(MX0, MX1, MY0, MY1, -0.45, 0.0, holes=[(MX0 + WT, -5.0, 8.4, MY1 - WT)])
    g.box(MX0 + WT, -5.0, 8.4, MY1 - WT, -1.35, -0.9)
    # living-level slab kept inside the wall lines (a full-footprint plate crossed the garage opening and z-fought the facade)
    g.plate(MX0 + WT, MX1 - WT, MY0 + WT, MY1 - WT, Z_LIV - 0.35, Z_LIV, holes=[(GLASS_X0 - 0.3, MX1 - WT, MY0 + WT, FOYER_Y1)])
    g.build("GF_Walls", trav)

    # stone detailing: shadow gaps at ground / soffit, cladding corner returns
    sg = MB()
    _gap_x(sg, MX0, GAR_X0 - 0.15, MY0, z0 + 0.02, -1); _gap_x(sg, GAR_X1 + 0.15, GLASS_X0, MY0, z0 + 0.02, -1)
    _gap_x(sg, GLASS_X1, MX1, MY0, z0 + 0.02, -1)
    _gap_x(sg, MX0, GLASS_X0, MY0, z1 - DK, -1); _gap_x(sg, GLASS_X1, MX1, MY0, z1 - DK, -1)
    _gap_y(sg, MY0, MY1, MX0, z1 - DK, -1); _gap_y(sg, MY0, MY1, MX1, z1 - DK, +1)
    _gap_y(sg, MY0, MY1, MX0, z0 + 0.02, -1); _gap_y(sg, MY0, LIV_Y0, MX1, z0 + 0.02, +1)
    _gap_x(sg, MX0, MX1, MY1, z1 - DK, +1); _gap_x(sg, MX0, MX1, MY1, Z_LIV + 0.02, +1)
    sg.build("GF_ShadowGaps", M['black'])
    cr = MB()
    _corner_return(cr, MX0, MY0, z0 + 0.03, z1 - DK, +1, +1)
    _corner_return(cr, MX1, MY0, z0 + 0.03, z1 - DK, -1, +1)
    _corner_return(cr, MX0, MY1, z0 + 0.03, z1 - DK, +1, -1)
    _corner_return(cr, MX1, MY1, z0 + 0.03, z1 - DK, -1, -1)
    cr.build("GF_CornerReturns", trav)

    # side door + interior glass partition onto the family pavilion (dining east glass)
    d = MB()
    door_leaf(d, 8.6, 9.6, MX0 + WT / 2, Z_LIV, Z_LIV + 2.4, mi=0, along='Y')
    d.box(MX0 + WT / 2 - 0.03, MX0 + WT / 2 - 0.018, 9.45, 9.47, Z_LIV + 0.95, Z_LIV + 1.25, 1)     # edge pull
    d.build("West_SideDoor", [M['oak'], M['black_metal']])
    gl = MB()
    _glazing(gl, 'Y', FAM_Y0, FAM_Y1, MX1 - 0.2, Z_LIV, Z_SOF - 0.05, panels=(13.6, 15.7), slider=True, fd=0.08)
    # rear glazing: master sliders, closet window, office slider
    _glazing(gl, 'X', -11.8, -5.0, MY1 - 0.2, Z_LIV, Z_SOF - 0.5, panels=(-10.1, -8.4, -6.7), slider=True, fd=0.09)
    _glazing(gl, 'X', 0.8, 2.6, MY1 - 0.2, Z_LIV + 0.9, Z_LIV + 2.5, fd=0.06)
    _glazing(gl, 'X', 3.8, 6.9, MY1 - 0.2, Z_LIV, Z_SOF - 0.5, panels=(5.35,), slider=True, fd=0.09)
    gl.build("GF_Glass", [M['glass'], M['frame']])

    # garage: black reveal + recessed vertical-slat door (6 mm gaps on a black backing) + bottom seal + fixtures
    r = MB()
    r.box(GAR_X0 - 0.15, GAR_X1 + 0.15, MY0 + WT - 0.05, MY0 + WT, z0, GAR_H + 0.15, 0)
    r.box(GAR_X0 - 0.15, GAR_X0, MY0, MY0 + WT, z0, GAR_H + 0.15, 0)
    r.box(GAR_X1, GAR_X1 + 0.15, MY0, MY0 + WT, z0, GAR_H + 0.15, 0)
    r.box(GAR_X0 - 0.15, GAR_X1 + 0.15, MY0, MY0 + WT, GAR_H, GAR_H + 0.15, 0)
    r.box(GAR_X0, GAR_X1, MY0 + 0.30, MY0 + 0.36, z0, GAR_H, 0)                        # black backing
    r.box(GAR_X0, GAR_X1, MY0 + 0.24, MY0 + 0.31, z0, z0 + 0.02, 0)                     # bottom seal
    r.build("Garage_Reveal", M['black'])
    dr = MB()                                                                        # fine golden fins matching the box (photo 23)
    _slats2(dr, 'X', GAR_X0 + 0.004, GAR_X1, MY0 + 0.25, 0.05, z0 + 0.025, GAR_H - 0.01, w=0.040, gap=0.008)
    dr.build("Garage_Door", [LOCAL['fin_a'], LOCAL['fin_b']])
    fx = MB()
    for sx in (-11.4, -5.15):
        _fixture(fx, sx, MY0, 1.65, h=1.2, along='X', out=0.05, mi_body=0, mi_lens=1)
    fx.build("Garage_Sconces", [M['black_metal'], M['emit_bar']])
    for sx in (-11.4, -5.15):
        add_light(f"Sconce_{sx}", 'POINT', (sx, MY0 - 0.12, 1.65), 30, WARM, size=0.04)
    # hose bib beside the garage
    hb = MB()
    hb.cylinder(-11.9, MY0 - 0.02, 0.55, 0.55 + 0.001, 0.02, seg=10, mi=0)
    hb.tube((-11.9, MY0, 0.55), (-11.9, MY0 - 0.06, 0.55), 0.008, 0.008, seg=8, mi=0)
    hb.tube((-11.9, MY0 - 0.06, 0.55), (-11.9, MY0 - 0.06, 0.50), 0.008, 0.006, seg=8, mi=0)
    hb.cylinder(-11.9, MY0 - 0.06, 0.56, 0.58, 0.018, seg=8, mi=0)
    hb.build("Hose_Bib", M['chrome'])

    # backlit onyx slot in a 20 mm bronze reveal + small lit window
    box("Onyx_Slot", 4.4, 4.9, MY0 + 0.02, MY0 + WT, 1.4, 4.6, M['onyx'])
    br = MB()
    br.frame(4.38, 4.92, MY0 - 0.012, MY0 + 0.03, 1.38, 4.62, 0.02, mi=0, axis='Y')
    br.frame(5.58, 7.02, MY0 - 0.012, MY0 + 0.03, 0.43, 1.37, 0.02, mi=0, axis='Y')
    br.build("Onyx_Reveals", M['bronze'])
    w = MB()
    w.box(5.6, 7.0, MY0 + 0.1, MY0 + 0.1 + T, 0.45, 1.35, 0)
    w.frame(5.58, 7.02, MY0 + 0.08, MY0 + 0.13, 0.43, 1.37, 0.02, mi=1, axis='Y')                       # slim dark frame
    w.build("Small_Window", [M['glass_tint'], M['frame']])
    # a softly lit wall behind the little window (not a glowing panel): warm, low emission
    box("Small_Window_Back", 5.6, 7.0, MY0 + WT + 0.9, MY0 + WT + 0.95, 0.45, 1.35,
        _mat.new_mat("SmallWindowGlow", (0.92, 0.86, 0.74, 1), rough=0.8, emit=(1.0, 0.82, 0.58, 1), emit_str=0.45))


# ================================================================ entry glass + portal
def entry(M):
    z0, z1 = Z_COURT, Z_SOF
    L = LOCAL
    e = MB()
    yg = MY0 + 0.20
    TG = 0.019                                                                       # 19 mm structural glass
    joints = (-2.85, -1.5, 1.15)                                                     # 12 mm silicone butt joints
    # frameless structural glazing (photos 02/05): full-height 19 mm panes butt-jointed with silicone, stiffened by
    # 300 mm glass fins on the inside, a 40 mm dark head channel and a flush floor channel - no metal mullions
    edges = [GLASS_X0] + list(joints) + [GLASS_X1]
    for pa0, pa1 in zip(edges[:-1], edges[1:]):
        ja0 = pa0 + (0.006 if pa0 in joints else 0.0)
        ja1 = pa1 - (0.006 if pa1 in joints else 0.0)
        # pane(s): the portal cuts the middle of the wall - glass above it only
        segs = []
        if ja1 <= PORTAL_X0 or ja0 >= PORTAL_X1:
            segs.append((ja0, ja1, z0 + 0.02, z1 - 0.04))
        else:
            if ja0 < PORTAL_X0:
                segs.append((ja0, PORTAL_X0 - 0.015, z0 + 0.02, z1 - 0.04))
            if ja1 > PORTAL_X1:
                segs.append((PORTAL_X1 + 0.015, ja1, z0 + 0.02, z1 - 0.04))
            segs.append((max(ja0, PORTAL_X0 + 0.015), min(ja1, PORTAL_X1 - 0.015), PORTAL_H + 0.015, z1 - 0.04))
        for (sx0, sx1, sz0, sz1) in segs:
            e.box(sx0, sx1, yg, yg + TG, sz0, sz1, 0)
            e.box(sx0, sx0 + 0.006, yg, yg + TG, sz0, sz1, 3)                          # green edges at the joints
            e.box(sx1 - 0.006, sx1, yg, yg + TG, sz0, sz1, 3)
    for jx in joints:                                                                # silicone joint + glass fin behind it
        zz0 = PORTAL_H + 0.015 if PORTAL_X0 < jx < PORTAL_X1 else z0 + 0.02
        e.box(jx - 0.006, jx + 0.006, yg + 0.002, yg + TG - 0.002, zz0, z1 - 0.04, 4)
        e.box(jx - TG / 2, jx + TG / 2, yg + TG + 0.004, yg + TG + 0.304, zz0 + 0.03, z1 - 0.07, 0)     # 300 mm fin
        e.box(jx - TG / 2, jx + TG / 2, yg + TG + 0.298, yg + TG + 0.304, zz0 + 0.03, z1 - 0.07, 3)     # its green edge
        e.box(jx - TG / 2, jx + TG / 2, yg + TG + 0.004, yg + TG + 0.010, zz0 + 0.03, z1 - 0.07, 3)
        for zz in (zz0 + 0.03, z1 - 0.13):                                           # 60 mm stainless fin clamps
            e.box(jx - 0.022, jx + 0.022, yg + TG - 0.001, yg + TG + 0.06, zz, zz + 0.06, 1)
    e.box(GLASS_X0 - 0.01, GLASS_X1 + 0.01, MY0 + 0.14, MY0 + 0.30, z1 - 0.04, z1, 2)   # head channel (dark)
    e.box(GLASS_X0, PORTAL_X0, yg - 0.015, yg + TG + 0.015, z0, z0 + 0.02, 2)           # flush floor channels
    e.box(PORTAL_X1, GLASS_X1, yg - 0.015, yg + TG + 0.015, z0, z0 + 0.02, 2)
    e.box(GLASS_X0 - 0.006, GLASS_X0, yg, yg + TG, z0 + 0.02, z1 - 0.04, 4)              # end joints to the stone
    e.box(GLASS_X1, GLASS_X1 + 0.006, yg, yg + TG, z0 + 0.02, z1 - 0.04, 4)
    e.build("Entry_Glass", [M['glass'], M['steel'], M['black'], M['glass_green'], L['silicone']])

    p = MB()
    p.box(PORTAL_X0, PORTAL_X0 + 0.35, MY0 - 0.30, MY0 + 0.9, z0, PORTAL_H)
    p.box(PORTAL_X1 - 0.35, PORTAL_X1, MY0 - 0.30, MY0 + 0.9, z0, PORTAL_H)
    p.box(PORTAL_X0, PORTAL_X1, MY0 - 0.30, MY0 + 0.9, PORTAL_H - 0.35, PORTAL_H)
    p.box(PORTAL_X0, PORTAL_X1, MY0 - 0.30, MY0 + 0.9, z0 - 0.05, z0 + 0.02)
    p.build("Entry_Portal", M['trav'])
    # 40 mm dark reveal lining the portal opening + 15 mm shadow gap where the glass meets the portal
    rv = MB()
    ox0, ox1, oz1 = PORTAL_X0 + 0.35, PORTAL_X1 - 0.35, PORTAL_H - 0.35
    rv.box(ox0, ox0 + 0.04, MY0 - 0.30, MY0 + 0.9, z0 + 0.02, oz1, 0)
    rv.box(ox1 - 0.04, ox1, MY0 - 0.30, MY0 + 0.9, z0 + 0.02, oz1, 0)
    rv.box(ox0, ox1, MY0 - 0.30, MY0 + 0.9, oz1 - 0.04, oz1, 0)
    rv.box(PORTAL_X0 - 0.015, PORTAL_X0, MY0 - 0.30, yg + 0.03, z0, PORTAL_H, 0)
    rv.box(PORTAL_X1, PORTAL_X1 + 0.015, MY0 - 0.30, yg + 0.03, z0, PORTAL_H, 0)
    rv.box(PORTAL_X0 - 0.015, PORTAL_X1 + 0.015, MY0 - 0.30, yg + 0.03, PORTAL_H, PORTAL_H + 0.015, 0)
    rv.build("Portal_Reveal", M['black'])
    dr = MB()
    dr.box(ox0 + 0.04, ox1 - 0.04, MY0 + 0.45, MY0 + 0.52, z0 + 0.02, oz1 - 0.04, 0)
    for gx in (DOOR_X0, DOOR_X1):                                                   # leaf reveal lines
        dr.box(gx - 0.004, gx + 0.004, MY0 + 0.44, MY0 + 0.45, z0 + 0.02, oz1 - 0.04, 2)
    # 1.2 m stainless bar pull on two standoffs (outside face) + floor pivot plate
    px = DOOR_X1 - 0.12
    dr.cylinder(px, MY0 + 0.38, 0.75, 1.95, 0.016, seg=14, mi=1)
    for zz in (0.90, 1.80):
        dr.tube((px, MY0 + 0.45, zz), (px, MY0 + 0.38, zz), 0.010, 0.010, seg=10, mi=1)
    dr.cylinder(DOOR_X0 + 0.12, MY0 + 0.485, z0 + 0.02, z0 + 0.024, 0.05, seg=16, mi=1)    # pivot plate
    dr.build("Entry_Door", [M['door'], M['steel'], M['black']])
    # house number plaque + intercom on the travertine right of the glass
    mp = MB()
    mp.box(4.05, 4.29, MY0 - 0.012, MY0, 1.55, 1.67, 0)
    for k, dx in enumerate((0.03, 0.10, 0.17)):                                      # "349" as three raised digits
        mp.box(4.05 + dx, 4.05 + dx + 0.04, MY0 - 0.016, MY0 - 0.012, 1.58, 1.64, 1)
    mp.box(4.08, 4.16, MY0 - 0.02, MY0, 1.25, 1.39, 2)                                # intercom body
    mp.box(4.10, 4.14, MY0 - 0.022, MY0 - 0.02, 1.34, 1.37, 3)                        # camera lens
    mp.cylinder(4.12, MY0 - 0.021, 1.28, 1.29, 0.008, seg=10, mi=1)                   # call button
    mp.build("Entry_Plaque", [M['bronze'], M['brass'], M['black_metal'], M['chrome']])


# ================================================================ L1 slab
def l1_slab(M):
    sl = MB()
    sl.plate(MX0 - 0.2, MX1, SLAB_Y0, MY1, Z_SOF, Z_UP, holes=[STAIR_HOLE])
    sl.build("L1_Slab", M['white'])
    st = MB()
    _edge_strip(st, MX0 - 0.2, MX1, SLAB_Y0, MY1, Z_SOF, Z_SOF + 0.02)
    st.build("L1_DripEdge", M['black'])
    dl = MB()
    under_box = lambda x: BOX_X0 < x < BOX_X1
    pts = [(x, MY0 - 0.3) for x in range(-11, 8, 2) if not under_box(x)]
    pts_box = [(x, MY0 - 0.6) for x in (-1.4, 0.6, 2.6)]                  # recessed in the box's slatted underside
    downlights(dl, pts, Z_SOF)
    downlights(dl, pts_box, Z_SOF - 0.15)
    dl.build("L1_Downlights", [M['emit_down'], M['black']])
    _spots("Spot_Soffit", pts, Z_SOF, energy=220, spot=95)
    _spots("Spot_SoffitBox", pts_box, Z_SOF - 0.15, energy=220, spot=95)


# ================================================================ stair lantern + wood slat box
def lantern_and_box(M):
    lt = MB()
    _glazing(lt, 'X', SKY_X0 + 0.2, BOX_X0, MY0 + 0.15, Z_UP, Z_UPC, panels=(-3.9,), fd=0.07)
    lt.build("Lantern_Glass", [M['glass'], M['frame']])
    box("Lantern_WestWall", -5.6, -5.2, MY0, 4.0, Z_UP, Z_UPC, M['trav'])
    sk = MB()
    sk.frame(-5.05, -2.75, 0.55, 2.65, Z_ROOF, Z_ROOF + 0.18, 0.06, mi=0, axis='Z')
    sk.frame(-5.03, -2.77, 0.57, 2.63, Z_ROOF + 0.18, Z_ROOF + 0.22, 0.03, mi=2, axis='Z')       # dark glazing frame
    sk.box(-5.05, -2.75, 0.55, 2.65, Z_ROOF + 0.19, Z_ROOF + 0.19 + T, 1)
    sk.build("Skylight", [M['white'], M['glass'], M['frame']])

    # wood box (photos 02/23/34): a SOLID warm golden box - 40 mm oak fins at 80 mm pitch, 40 mm deep, on a
    # charcoal backing 20 mm behind them (front + both sides), a finned underside soffit, the white roof slab
    # wrapping over its top; it reads as a ribbed timber block, not a cage
    L = LOCAL
    wb = MB()
    zb0, zb1 = Z_SOF - 0.15, Z_UPC
    FW, FG, FDp = 0.04, 0.04, 0.04                                                  # fin width / gap / depth
    _slats2(wb, 'X', BOX_X0 + 0.02, BOX_X1 - 0.02, BOX_Y0, FDp, zb0 + 0.015, zb1 - 0.015, w=FW, gap=FG, sign=1)
    _slats2(wb, 'Y', BOX_Y0 + 0.02, BOX_Y1, BOX_X0, FDp, zb0 + 0.015, zb1 - 0.015, w=FW, gap=FG, sign=1)
    _slats2(wb, 'Y', BOX_Y0 + 0.02, BOX_Y1, BOX_X1, FDp, zb0 + 0.015, zb1 - 0.015, w=FW, gap=FG, sign=-1)
    # corner fins (a full 40 x 40 post at each front corner closes the fin field)
    wb.box(BOX_X0, BOX_X0 + FW, BOX_Y0, BOX_Y0 + FW, zb0 + 0.015, zb1 - 0.015, 0)
    wb.box(BOX_X1 - FW, BOX_X1, BOX_Y0, BOX_Y0 + FW, zb0 + 0.015, zb1 - 0.015, 0)
    a = BOX_X0 + 0.02                                                               # finned underside soffit
    k = 0
    while a + FW <= BOX_X1 - 0.02 + 1e-6:
        wb.box(a, a + FW, BOX_Y0, UP_Y0 + 0.1, zb0, zb0 + FDp, k % 2)
        a += FW + FG
        k += 1
    # 15 mm end caps top + bottom on the three finned faces
    for (x0, x1, y0, y1) in ((BOX_X0 - 0.003, BOX_X1 + 0.003, BOX_Y0 - 0.003, BOX_Y0 + FDp),
                             (BOX_X0 - 0.003, BOX_X0 + FDp, BOX_Y0, BOX_Y1), (BOX_X1 - FDp, BOX_X1 + 0.003, BOX_Y0, BOX_Y1)):
        wb.box(x0, x1, y0, y1, zb0, zb0 + 0.015, 0)
        wb.box(x0, x1, y0, y1, zb1 - 0.015, zb1, 0)
    wb.build("Wood_Box", [L['fin_a'], L['fin_b']])
    bk = MB()                                                                       # charcoal backing behind the fins
    bk.box(BOX_X0 + FDp, BOX_X1 - FDp, BOX_Y0 + FDp, BOX_Y0 + FDp + 0.02, zb0, zb1, 0)
    bk.box(BOX_X0 + FDp, BOX_X0 + FDp + 0.02, BOX_Y0 + FDp, BOX_Y1, zb0, zb1, 0)
    bk.box(BOX_X1 - FDp - 0.02, BOX_X1 - FDp, BOX_Y0 + FDp, BOX_Y1, zb0, zb1, 0)
    bk.box(BOX_X0 + FDp, BOX_X1 - FDp, BOX_Y0 + FDp, UP_Y0 + 0.1, zb0 + FDp, zb0 + FDp + 0.02, 0)   # soffit backing
    bk.build("Wood_Box_Backing", L['fin_back'])
    ou = MB()                                                                       # black steel corner outriggers
    for (x, sx) in ((BOX_X0, 1), (BOX_X1, -1)):
        ou.box(x - 0.005 * sx if sx > 0 else x - 0.04, x + 0.04 if sx > 0 else x + 0.005, BOX_Y0 - 0.005, BOX_Y0 + 0.008, zb0, zb1, 0)
        ou.box(x - 0.008 if sx > 0 else x, x if sx > 0 else x + 0.008, BOX_Y0 - 0.005, BOX_Y0 + 0.04, zb0, zb1, 0)
    ou.build("Wood_Box_Outriggers", M['black_metal'])
    ib = MB()                                                                       # inner glazed liner of the box room
    ib.box(BOX_X0 + 0.115, BOX_X1 - 0.115, BOX_Y0 + 0.115, BOX_Y0 + 0.115 + T, zb0 + 0.12, zb1 - 0.12, 0)
    ib.box(BOX_X0 + 0.115, BOX_X0 + 0.115 + T, BOX_Y0 + 0.115, BOX_Y1, zb0 + 0.12, zb1 - 0.12, 0)
    ib.box(BOX_X1 - 0.115 - T, BOX_X1 - 0.115, BOX_Y0 + 0.115, BOX_Y1, zb0 + 0.12, zb1 - 0.12, 0)
    ib.box(BOX_X0 + 0.10, BOX_X1 - 0.10, BOX_Y0 + 0.10, BOX_Y0 + 0.13, zb0 + 0.10, zb0 + 0.12, 1)     # glass channels
    ib.box(BOX_X0 + 0.10, BOX_X1 - 0.10, BOX_Y0 + 0.10, BOX_Y0 + 0.13, zb1 - 0.12, zb1 - 0.10, 1)
    ib.build("Wood_Box_Glass", [M['glass'], M['frame']])
    box("Wood_Box_FloorPlate", BOX_X0 + 0.1, BOX_X1 - 0.1, BOX_Y0 + 0.1, BOX_Y1, zb0 + FDp + 0.02, Z_UP, M['white'])
    # the white roof slab continues over the box (photo 23: a crisp white edge caps the timber), with its coping + gravel
    rc = MB()
    rc.box(BOX_X0 - 0.05, BOX_X1 + 0.05, BOX_Y0 - 0.05, ROOF_Y0 + 0.01, Z_UPC, Z_ROOF, 0)
    rc.box(BOX_X0 - 0.05, BOX_X1 + 0.05, BOX_Y0 - 0.05, BOX_Y0 + 0.10, Z_ROOF, Z_ROOF + 0.06, 0)        # lip: front + sides only
    rc.box(BOX_X0 - 0.05, BOX_X0 + 0.10, BOX_Y0 - 0.05, ROOF_Y0 + 0.15, Z_ROOF, Z_ROOF + 0.06, 0)       # (the main roof lip is
    rc.box(BOX_X1 - 0.10, BOX_X1 + 0.05, BOX_Y0 - 0.05, ROOF_Y0 + 0.15, Z_ROOF, Z_ROOF + 0.06, 0)       # broken here)
    rc.build("Roof_BoxCap", M['white'])
    box("Roof_BoxCap_Gravel", BOX_X0 + 0.10, BOX_X1 - 0.10, BOX_Y0 + 0.10, ROOF_Y0 + 0.16, Z_ROOF, Z_ROOF + 0.035, L['ballast'])
    de = MB()
    _edge_strip(de, BOX_X0 - 0.05, BOX_X1 + 0.05, BOX_Y0 - 0.05, ROOF_Y0 + 0.01, Z_UPC, Z_UPC + 0.02)
    de.build("Roof_BoxCap_DripEdge", M['black'])


# ================================================================ living + family pavilions
def pavilions(M):
    trav, white, glass, frame = M['trav'], M['white'], M['glass'], M['frame']
    lv = MB()
    lv.box(LIV_X0 - WT, LIV_X1, LIV_Y0, FAM_Y1, Z_LIV - 0.35, Z_LIV, 0)                # floor slab
    lv.box(LIV_X0, LIV_X1 + 0.3, LIV_Y0 - 0.3, NA_Y0 - 0.3, Z_SOF, Z_SOF + 0.6, 1)     # roof slab (meets the north arm roof)
    lv.box(LIV_X0, LIV_X1, LIV_Y1, FAM_Y0, Z_LIV, Z_SOF, 0)                            # pier living/family
    lv.box(LIV_X0, LIV_X1, FAM_Y1 - WT, FAM_Y1, Z_LIV, Z_SOF, 0)                       # family north wall
    lv.box(LIV_X1 - 0.3, LIV_X1, LIV_Y0, LIV_Y0 + 0.3, Z_LIV, Z_SOF, 0)                # SE corner pier
    lv.box(LIV_X0 - WT, LIV_X1, LIV_Y0, LIV_Y0 + 0.3, Z_LAWN - 0.5, Z_LIV - 0.35, 0)   # wall under the living floor edge
    lv.build("Pavilion_Structure", [trav, white])
    sg = MB()                                                                        # shadow gaps + corner return on the piers
    _gap_y(sg, LIV_Y0, LIV_Y0 + 0.3, LIV_X1, Z_LIV + 0.02, +1); _gap_y(sg, LIV_Y0, LIV_Y0 + 0.3, LIV_X1, Z_SOF - DK, +1)
    _gap_x(sg, LIV_X1 - 0.3, LIV_X1, LIV_Y0, Z_LIV + 0.02, -1); _gap_x(sg, LIV_X1 - 0.3, LIV_X1, LIV_Y0, Z_SOF - DK, -1)
    _gap_x(sg, LIV_X0 - WT, LIV_X1, LIV_Y0, Z_LAWN - 0.45, -1)
    sg.build("Pavilion_ShadowGaps", M['black'])
    cr = MB()
    _corner_return(cr, LIV_X1, LIV_Y0, Z_LIV + 0.03, Z_SOF - DK, -1, +1)
    cr.build("Pavilion_CornerReturn", trav)
    # perforated parapet panels standing proud of the white fascia (photos 01/22): terrace S side, its E return
    pf = MB()
    _perf_panel(pf, 'X', MX1 + 0.2, LIV_X1 + 0.338, LIV_Y0 - 0.3, -1, Z_SOF + 0.02, Z_SOF + 0.72, mi=0)   # meets the tray's E panel
    pf.build("Pavilion_Fascia_S", [LOCAL['perf_x'], M['steel']])
    pf = MB()
    _perf_panel(pf, 'Y', LIV_Y0 - 0.33, NA_Y0 - 0.3, LIV_X1 + 0.3, +1, Z_SOF + 0.02, Z_SOF + 0.72, mi=0)
    pf.box(LIV_X1 + 0.2, LIV_X1 + 0.338, NA_Y0 - 0.308, NA_Y0 - 0.3, Z_SOF + 0.02, Z_SOF + 0.72, 0)  # north end return
    pf.build("Pavilion_Fascia_E", [LOCAL['perf_y'], M['steel']])
    # glazing: the living pavilion is an open loggia in the photos (04/10) - its S and E multi-slides are parked
    # open (stacked at the pier ends); a fixed clerestory band runs above the 2.8 m transom all round (photo 10);
    # the family pavilion stays closed
    ZT = Z_SOF - 0.5                                                                 # transom height
    gl = MB()
    # the multi-slides park away from the SE corner (photos 01/04: the corner stands fully open, the panels are
    # stacked at the west end of the south face and at the north end of the east face)
    _glazing(gl, 'X', LIV_X0 + WT, LIV_X1 - 0.3, LIV_Y0 + 0.1, Z_LIV, ZT, panels=(9.9,), slider=True, fd=0.09, stack='start')
    _glazing(gl, 'Y', LIV_Y0 + 0.3, LIV_Y1, LIV_X1 - 0.1, Z_LIV, ZT, panels=(5.6, 7.4, 9.2), slider=True, fd=0.09, stack='end')
    _glazing(gl, 'X', LIV_X0 + WT, LIV_X1 - 0.3, LIV_Y0 + 0.1, ZT - 0.05, Z_SOF, panels=(9.9,), fd=0.06, bead=False)
    _glazing(gl, 'Y', LIV_Y0 + 0.3, LIV_Y1, LIV_X1 - 0.1, ZT - 0.05, Z_SOF, panels=(5.6, 7.4, 9.2), fd=0.06, bead=False)
    _glazing(gl, 'Y', FAM_Y0, FAM_Y1 - WT, LIV_X1 - 0.1, Z_LIV, ZT, panels=(13.0, 14.6, 16.2), slider=True, fd=0.09)
    _glazing(gl, 'Y', FAM_Y0, FAM_Y1 - WT, LIV_X1 - 0.1, ZT - 0.05, Z_SOF, panels=(13.0, 14.6, 16.2), fd=0.06, bead=False)
    gl.box(LIV_X1 - 0.25, LIV_X1 + 0.05, LIV_Y0 - 0.1, FAM_Y1, Z_LIV - 0.02, Z_LIV + 0.02, 1)   # sill track plate
    gl.build("Pavilion_Glass", [glass, frame])
    dl = MB()
    pts = [(x, LIV_Y0 - 0.15) for x in (8.5, 10.5, 12.3)] + [(LIV_X1 + 0.15, y) for y in (5.0, 8.0, 11.0, 14.0, 17.0)]
    downlights(dl, pts, Z_SOF)
    dl.build("Pavilion_Downlights", [M['emit_down'], M['black']])
    _spots("Spot_Pav", pts, Z_SOF, energy=60, spot=110)


# ================================================================ upper floor (Z_UP .. Z_UPC)
def upper_floor(M):
    trav, white, glass, frame = M['trav'], M['white'], M['glass'], M['frame']
    up = MB()
    z0, z1 = Z_UP, Z_UPC
    up.wall('X', MX0, -5.5, UP_Y0, UP_Y0 + 0.4, z0, z1, holes=[(-11.8, -7.4, z0 + 1.1, z0 + 2.4)], mi=0)     # west box front + strip window
    up.wall('Y', UP_Y0, MY1, MX0, MX0 + 0.4, z0, z1, holes=[(1.4, 5.0, z0 + 0.6, z1 - 0.3), (15.0, 20.0, z0 + 0.6, z1 - 0.3)], mi=0)
    up.wall('X', MX0, MX1, MY1 - 0.4, MY1, z0, z1, holes=[(-11.0, -7.0, z0 + 0.9, z1 - 0.5), (-3.0, 1.0, z0 + 0.9, z1 - 0.5)], mi=0)
    up.wall('Y', 18.0, MY1, MX1 - 0.4, MX1, z0, z1, holes=[(18.4, 19.5, z0, z0 + 2.5), (20.2, 23.0, z0 + 0.4, z0 + 2.5)], mi=0)  # upbed2 E wall
    up.box(MX1 - 0.4, MX1, FAM_Y1, 18.0, z0, z1, 1)                                                          # pier at the end of the glass bar
    up.box(BOX_X1, BOX_X1 + 0.45, 4.0, 4.4, z0, z1, 1)                                                       # pier box / upfamily glass
    up.build("Upper_Walls", [trav, white])
    sg = MB()
    _gap_x(sg, MX0, -5.5, UP_Y0, z0 + 0.02, -1); _gap_x(sg, MX0, -5.5, UP_Y0, z1 - DK, -1)
    _gap_y(sg, UP_Y0, MY1, MX0, z0 + 0.02, -1); _gap_y(sg, UP_Y0, MY1, MX0, z1 - DK, -1)
    _gap_x(sg, MX0, MX1, MY1, z0 + 0.02, +1); _gap_x(sg, MX0, MX1, MY1, z1 - DK, +1)
    _gap_y(sg, 18.0, MY1, MX1, z0 + 0.02, +1); _gap_y(sg, 18.0, MY1, MX1, z1 - DK, +1)
    sg.build("Upper_ShadowGaps", M['black'])
    cr = MB()
    _corner_return(cr, MX0, UP_Y0, z0 + 0.03, z1 - DK, +1, +1)
    _corner_return(cr, MX0, MY1, z0 + 0.03, z1 - DK, +1, -1)
    _corner_return(cr, MX1, MY1, z0 + 0.03, z1 - DK, -1, -1)
    cr.build("Upper_CornerReturns", trav)
    uw = MB()
    _glazing(uw, 'X', -11.8, -7.4, UP_Y0 + 0.15, z0 + 1.1, z0 + 2.4, panels=(-9.6,), fd=0.07)
    _glazing(uw, 'Y', 1.4, 5.0, MX0 + 0.15, z0 + 0.6, z1 - 0.3, panels=(3.2,), fd=0.07)
    _glazing(uw, 'Y', 15.0, 20.0, MX0 + 0.15, z0 + 0.6, z1 - 0.3, panels=(17.5,), fd=0.07)
    _glazing(uw, 'X', -11.0, -7.0, MY1 - 0.15, z0 + 0.9, z1 - 0.5, panels=(-9.0,), fd=0.07)
    _glazing(uw, 'X', -3.0, 1.0, MY1 - 0.15, z0 + 0.9, z1 - 0.5, panels=(-1.0,), fd=0.07)
    _glazing(uw, 'Y', 4.0, FAM_Y1, MX1 - 0.2, z0, z1, panels=(6.4, 8.8, 11.2, 13.6, 16.0), slider=True, fd=0.09)   # upfamily + upbed1 glass bar
    _glazing(uw, 'X', BOX_X1 + 0.45, MX1 - 0.2, 4.0, z0, z1, panels=(5.7,), fd=0.07)                             # upfamily S glass
    _glazing(uw, 'Y', 18.4, 19.5, MX1 - 0.2, z0, z0 + 2.5, fd=0.07, bead=True)                                     # upbed2 door
    uw.box(MX1 - 0.2 - 0.045 - 0.03, MX1 - 0.2 - 0.045 - 0.006, 19.33, 19.36, z0 + 0.95, z0 + 1.25, 1)             # door pull (terrace side)
    _glazing(uw, 'Y', 20.2, 23.0, MX1 - 0.2, z0 + 0.4, z0 + 2.5, panels=(21.6,), fd=0.07)                          # upbed2 window
    uw.build("Upper_Glass", [glass, frame])


# ================================================================ roof terraces (turf trays, perforated parapets, rail)
def terraces(M):
    white, glass = M['white'], M['glass']
    zt = Z_SOF + 0.6
    tr = MB()
    tr.box(BOX_X1 + 0.12, MX1 + 0.2, SLAB_Y0, 4.0, Z_UP, zt, 0)                     # front tray (beside the wood box)
    tr.box(MX1, MX1 + 0.2, SLAB_Y0, 4.0, Z_SOF, Z_UP, 0)                            # its east fascia fill below the tray
    tr.box(TX0, TX1, NA_Y0 - 0.3, NA_Y1 + 0.3, Z_SOF, zt, 0)                        # north arm roof = dining terrace
    tr.build("Terrace_Trays", white)
    pf = MB()                                                                       # perforated parapet panels (front tray)
    _perf_panel(pf, 'X', BOX_X1 + 0.12, MX1 + 0.23, SLAB_Y0, -1, Z_SOF + 0.02, zt + 0.12, mi=0)
    pf.box(BOX_X1 + 0.12, BOX_X1 + 0.128, SLAB_Y0 - 0.038, SLAB_Y0 + 0.12, Z_SOF + 0.02, zt + 0.12, 0)   # west end return
    pf.build("Terrace_Fascia_S", [LOCAL['perf_x'], M['steel']])
    pf = MB()
    _perf_panel(pf, 'Y', SLAB_Y0 - 0.038, LIV_Y0 - 0.3 - 0.03, MX1 + 0.2, +1, Z_SOF + 0.02, zt + 0.12, mi=0)
    pf.build("Terrace_Fascia_E", [LOCAL['perf_y'], M['steel']])
    tf = MB()
    turfs = ((BOX_X1 + 0.2, MX1 + 0.12, SLAB_Y0 + 0.1, 3.95), (MX1 - 0.18, LIV_X1 + 0.22, LIV_Y0 - 0.22, NA_Y0 - 0.3),
             (8.0, TX1 - 0.4, NA_Y0 - 0.3, NA_Y1 - 0.4))
    for (x0, x1, y0, y1) in turfs:
        tf.box(x0, x1, y0, y1, zt, zt + 0.04)
    tf.build("Terrace_Turf", M['turf'])
    et = MB()                                                                       # 40 mm aluminium edge trims
    for (x0, x1, y0, y1) in turfs:
        et.frame(x0 - 0.004, x1 + 0.004, y0 - 0.004, y1 + 0.004, zt, zt + 0.045, 0.004, mi=0, axis='Z')
    et.build("Terrace_TurfTrim", M['steel'])
    gv = MB()
    gv.box(TX0, 8.0, NA_Y0 - 0.3, NA_Y1 + 0.3, zt, zt + 0.02)                        # gravel margins on the dining terrace
    gv.box(TX1 - 0.4, TX1, NA_Y0 - 0.3, NA_Y1 + 0.3, zt, zt + 0.02)
    gv.box(8.0, TX1 - 0.4, NA_Y1 - 0.4, NA_Y1 + 0.3, zt, zt + 0.02)
    gv.build("Terrace_Gravel", LOCAL['ballast'])
    gr = MB()
    zr = zt + 0.04
    rail_pts = [(BOX_X1 + 0.22, SLAB_Y0 + 0.1), (MX1 + 0.12, SLAB_Y0 + 0.1), (MX1 + 0.12, LIV_Y0 - 0.22),
                (LIV_X1 + 0.22, LIV_Y0 - 0.22), (LIV_X1 + 0.22, NA_Y0 - 0.22), (TX1 - 0.1, NA_Y0 - 0.22),
                (TX1 - 0.1, NA_Y1 + 0.2)]
    glass_rail(gr, rail_pts, zr, h=1.05)
    _rail_caps(gr, rail_pts, zr, mi=1)
    _glass_edges(gr, rail_pts, zr, 1.05, mi=2)
    gr.build("Terrace_Rail", [glass, M['steel'], M['glass_green']])


# ================================================================ roof slab
def roof(M):
    white = M['white']
    Y_SPLIT = 17.2
    SKY = (-5.0, -2.8, 0.6, 2.6)
    DIN = (9.0, 16.0, 18.6, 23.2)
    rf = MB()
    rf.plate(ROOF_X0, ROOF_X1, ROOF_Y0, Y_SPLIT, Z_UPC, Z_ROOF, holes=[SKY, ROOF_HOLE])
    rf.plate(ROOF_X0, 17.0, Y_SPLIT, ROOF_Y1, Z_UPC, Z_ROOF, holes=[DIN])
    # 60 mm raised parapet lip (150 mm wide) around the outer edge and around every opening (photo 22): the
    # ballast sits inside it, so the roof never reads as a flat white plane
    LW, LH = 0.15, 0.06
    rf.box(ROOF_X0, BOX_X0 - 0.05, ROOF_Y0, ROOF_Y0 + LW, Z_ROOF, Z_ROOF + LH)          # front lip, broken where the
    rf.box(BOX_X1 + 0.05, ROOF_X1, ROOF_Y0, ROOF_Y0 + LW, Z_ROOF, Z_ROOF + LH)          # roof runs out over the wood box
    rf.box(ROOF_X0, ROOF_X0 + LW, ROOF_Y0, ROOF_Y1, Z_ROOF, Z_ROOF + LH)                # west
    rf.box(ROOF_X1 - LW, ROOF_X1, ROOF_Y0, Y_SPLIT + LW, Z_ROOF, Z_ROOF + LH)           # east (front block)
    rf.box(17.0, ROOF_X1, Y_SPLIT, Y_SPLIT + LW, Z_ROOF, Z_ROOF + LH)                   # step in the east edge
    rf.box(17.0 - LW, 17.0, Y_SPLIT, ROOF_Y1, Z_ROOF, Z_ROOF + LH)                      # east (rear block)
    rf.box(ROOF_X0, 17.0, ROOF_Y1 - LW, ROOF_Y1, Z_ROOF, Z_ROOF + LH)                   # rear
    for (hx0, hx1, hy0, hy1) in (SKY, ROOF_HOLE, DIN):
        _coping(rf, hx0 - 0.15, hx1 + 0.15, hy0 - 0.15, hy1 + 0.15, Z_ROOF, w=0.15, h=0.06)
    rf.build("Roof", white)
    rg = MB()
    _gravel_plate(rg, ROOF_X0, ROOF_X1, ROOF_Y0, Y_SPLIT + 0.15, Z_ROOF, holes=[SKY, ROOF_HOLE], inset=0.15, t=0.035)
    _gravel_plate(rg, ROOF_X0, 17.0, Y_SPLIT - 0.15, ROOF_Y1, Z_ROOF, holes=[DIN], inset=0.15, t=0.035)
    rg.build("Roof_Gravel", LOCAL['ballast'])
    # roof drains: a 200 mm sump grate near each low corner + the overflow scuppers through the fascia
    dr = MB()
    for (x, y) in ((ROOF_X0 + 0.6, ROOF_Y0 + 0.6), (ROOF_X1 - 0.6, ROOF_Y0 + 0.6), (ROOF_X0 + 0.6, ROOF_Y1 - 0.6), (16.4, ROOF_Y1 - 0.6), (ROOF_X1 - 0.6, Y_SPLIT - 0.6)):
        dr.box(x - 0.12, x + 0.12, y - 0.12, y + 0.12, Z_ROOF + 0.02, Z_ROOF + 0.04, 0)
        for k in range(5):
            dr.box(x - 0.10, x + 0.10, y - 0.10 + k * 0.05, y - 0.10 + k * 0.05 + 0.012, Z_ROOF + 0.04, Z_ROOF + 0.05, 0)
    dr.build("Roof_Drains", M['black_metal'])
    de = MB()
    _edge_strip(de, ROOF_X0, ROOF_X1, ROOF_Y0, Y_SPLIT, Z_UPC, Z_UPC + 0.02)
    _edge_strip(de, ROOF_X0, 17.0, Y_SPLIT, ROOF_Y1, Z_UPC, Z_UPC + 0.02)
    # scupper outlets through the fascia (dark rectangular spouts)
    for (x, y, along) in ((-9.0, ROOF_Y0, 'S'), (4.0, ROOF_Y0, 'S'), (ROOF_X1, 9.0, 'E'), (ROOF_X0, 12.0, 'W')):
        if along == 'S':
            de.box(x - 0.08, x + 0.08, y - 0.06, y + 0.02, Z_ROOF - 0.12, Z_ROOF - 0.05)
        elif along == 'E':
            de.box(x - 0.02, x + 0.06, y - 0.08, y + 0.08, Z_ROOF - 0.12, Z_ROOF - 0.05)
        else:
            de.box(x - 0.06, x + 0.02, y - 0.08, y + 0.08, Z_ROOF - 0.12, Z_ROOF - 0.05)
    de.build("Roof_DripEdge", M['black'])
    rd = MB()
    pts = ([(x, ROOF_Y0 + 0.5) for x in range(-12, 14, 2)] +
           [(ROOF_X1 - 0.5, y) for y in range(0, 17, 2)] +
           [(ROOF_HOLE[0] - 0.5, y) for y in range(6, 15, 2)] +
           [(16.5, y) for y in range(18, 25, 2)] +
           [(x, DIN[2] - 0.4) for x in (10.5, 13.5)] + [(DIN[0] - 0.4, y) for y in (19.5, 22.0)] +
           [(x, ROOF_Y1 - 0.5) for x in range(-12, 8, 2)] +                       # rear soffit row (the rear elevation was unlit)
           [(ROOF_X0 + 0.5, y) for y in range(2, 24, 3)])                        # west soffit row
    downlights(rd, pts, Z_UPC)
    rd.build("Roof_Downlights", [M['emit_down'], M['black']])
    _spots("Spot_Roof", [(x, ROOF_Y0 + 0.5) for x in range(-12, 14, 4)] + [(ROOF_X1 - 0.5, y) for y in range(2, 17, 4)] +
           [(ROOF_HOLE[0] - 0.5, y) for y in (7, 11)] + [(16.5, y) for y in (19, 23)] + [(10.5, DIN[2] - 0.4), (13.5, DIN[2] - 0.4)] +
           [(x, ROOF_Y1 - 0.5) for x in range(-12, 8, 4)] + [(ROOF_X0 + 0.5, y) for y in (4, 10, 16, 22)],
           Z_UPC, energy=80, spot=105)


# ================================================================ north arm shell (gym + guest under the dining terrace)
def north_arm(M):
    white, glass, frame = M['white'], M['glass'], M['frame']
    na = MB()
    na.box(TX0, TX1, NA_Y0, NA_Y1, Z_COURT - 0.45, Z_LIV, 0)                                   # floor + foundation
    # the green wall opening runs almost full height (photo 15: the planting fills the wall up to a slim white
    # head band under the terrace); site.py builds the frame, backing and plants inside it
    na.wall('X', TX0, TX1, NA_Y0, NA_Y0 + WT, Z_LIV, Z_SOF, holes=[
        (8.0, 14.0, Z_LIV, Z_SOF - 0.4), (GREEN_X0, GREEN_X1, Z_LIV, Z_SOF - 0.1)], mi=0)
    na.wall('X', TX0, TX1, NA_Y1 - WT, NA_Y1, Z_LIV, Z_SOF, holes=[(15.0, 23.0, Z_LIV, Z_SOF - 0.5)], mi=0)
    na.box(TX1 - WT, TX1, NA_Y0, NA_Y1, Z_LIV, Z_SOF, 0)
    na.box(TX0, TX0 + WT, NA_Y0, NA_Y1, Z_LIV, Z_SOF, 0)
    na.build("NorthArm_Walls", white)
    sg = MB()
    _gap_x(sg, TX0, 8.0, NA_Y0, Z_LIV + 0.02, -1); _gap_x(sg, GREEN_X1, TX1, NA_Y0, Z_LIV + 0.02, -1)
    _gap_x(sg, TX0, 8.0, NA_Y0, Z_SOF - DK, -1); _gap_x(sg, GREEN_X1, TX1, NA_Y0, Z_SOF - DK, -1)
    sg.build("NorthArm_ShadowGaps", M['black'])
    box("GreenWall_WallBacking", GREEN_X0, GREEN_X1, NA_Y0 + 0.35, NA_Y0 + WT, Z_LIV, Z_SOF - 0.1, M['black'])
    nw = MB()
    _glazing(nw, 'X', 8.0, 14.0, NA_Y0 + 0.2, Z_LIV, Z_SOF - 0.4, panels=(9.5, 11.0, 12.5), slider=True, fd=0.09)
    _glazing(nw, 'X', 15.0, 23.0, NA_Y1 - 0.2, Z_LIV, Z_SOF - 0.5, panels=(17.0, 19.0, 21.0), slider=True, fd=0.09)
    nw.build("NorthArm_Glass", [glass, frame])
    dl = MB()
    pts = [(x, NA_Y0 - 0.15) for x in (8.5, 10.5, 12.5)]
    downlights(dl, pts, Z_SOF)
    dl.build("NorthArm_Downlights", [M['emit_down'], M['black']])
    _spots("Spot_NA", pts, Z_SOF, energy=60, spot=110)


# ================================================================ NE courtyard canopy
def canopy(M):
    white = M['white']
    hx0, hx1, hy0, hy1 = CAN_HOLE
    zc0, zc1 = Z_SOF, Z_UP + 0.1
    y1 = NA_Y0 - 0.3                                 # stop short of the north arm roof
    cn = MB()
    cn.plate(CAN_X0, CAN_X1, CAN_Y0, y1, zc0, zc1, holes=[CAN_HOLE])
    cn.box(CAN_X1 - 0.5, CAN_X1 - 0.1, CAN_Y0 + 0.1, CAN_Y0 + 0.5, Z_LIV, zc0)     # column
    _coping(cn, CAN_X0, CAN_X1, CAN_Y0, y1, zc1, w=0.08)
    _coping(cn, hx0 - 0.08, hx1 + 0.08, hy0 - 0.08, hy1 + 0.08, zc1, w=0.08)
    cn.build("Canopy", white)
    gv = MB()
    _gravel_plate(gv, CAN_X0, CAN_X1, CAN_Y0, y1, zc1, holes=[CAN_HOLE], inset=0.08)
    gv.build("Canopy_Gravel", LOCAL['ballast'])
    de = MB()
    _edge_strip(de, CAN_X0, CAN_X1, CAN_Y0, y1, zc0, zc0 + 0.02)
    de.box(CAN_X1 - 0.02, CAN_X1 + 0.06, 14.0, 14.16, zc1 - 0.12, zc1 - 0.05)     # scupper
    de.build("Canopy_DripEdge", M['black'])
    cl = MB()
    pts = [(19.4, 12.0), (19.4, 15.0), (24.1, 12.0), (24.1, 15.0), (21.8, 16.9)]
    downlights(cl, pts, zc0)
    cl.build("Canopy_Downlights", [M['emit_down'], M['black']])
    _spots("Spot_Canopy", pts, zc0, energy=50, spot=100)


# ================================================================ west stair (motor court -> living level)
def west_stair(M):
    x0, x1 = MX0 - 1.9, MX0 - 0.1
    ya, yb = MY0 - 0.5, 6.5
    n = 15
    ws = MB()
    stairs(ws, x0, x1, ya, yb, Z_COURT, Z_LIV, n=n, mi=0)
    ws.box(x0, x1, yb, 10.0, Z_LIV - 0.3, Z_LIV, 0)
    ws.box(x0, x1, ya, 10.0, Z_COURT - 0.45, Z_COURT, 0)
    ws.build("West_Stair", M['trav'])
    # separate tread slabs with a 15 mm nosing overhang and a 3 mm bevel
    tr = MB()
    dz, dy = Z_LIV / n, (yb - ya) / n
    for i in range(n):
        y = ya + dy * i
        tr.box(x0 + 0.002, x1 - 0.002, y - 0.015, y + dy + 0.001, Z_COURT + dz * (i + 1) - 0.03, Z_COURT + dz * (i + 1) + 0.004)
    tr.build("West_Stair_Treads", M['trav'], bevel=0.004, bevel_seg=2)
    wr = MB()
    xg = x0 + 0.04                                   # glass sits 40 mm in from the tread edge
    sloped_rail(wr, xg, ya, yb, Z_COURT, Z_LIV)
    rail_pts = [(xg, yb), (xg, 10.0), (x1, 10.0)]
    glass_rail(wr, rail_pts, Z_LIV, h=1.05)
    _rail_caps(wr, rail_pts, Z_LIV, mi=1)
    _glass_edges(wr, rail_pts, Z_LIV, 1.05, mi=2)
    # sloped shoe caps + green edge along the stair rail
    for i in range(int((yb - ya) / 0.6)):
        t = (i + 0.5) / int((yb - ya) / 0.6)
        y = ya + (yb - ya) * t
        wr.rbox(xg - 0.02, xg + 0.02, y - 0.02, y + 0.02, Z_COURT + Z_LIV * t + 0.08, Z_COURT + Z_LIV * t + 0.095, 0.006, 1)
    wr.build("West_Stair_Rail", [M['glass'], M['steel'], M['glass_green']])
    # o40 stainless handrail on the glass (brackets every 1.2 m), continuing level along the landing
    hr = MB()
    xr = xg + 0.07
    hr.path_tube([(xr, ya + 0.1, Z_COURT + 0.95), (xr, yb, Z_LIV + 0.95), (xr, 10.0 - 0.1, Z_LIV + 0.95)], 0.02, seg=12, mi=0)
    hr.sphere((xr, ya + 0.1, Z_COURT + 0.95), 0.02, seg=12, rings=8, mi=0)
    hr.sphere((xr, 10.0 - 0.1, Z_LIV + 0.95), 0.02, seg=12, rings=8, mi=0)
    for i in range(1, 7):
        t = i / 7
        y = ya + (yb - ya) * t
        z = Z_COURT + Z_LIV * t + 0.95
        hr.tube((xg + 0.006, y, z), (xr, y, z), 0.008, 0.008, seg=8, mi=0)
        hr.box(xg + 0.006, xg + 0.014, y - 0.03, y + 0.03, z - 0.03, z + 0.03, 0)
    for y in (8.0, 9.5):
        hr.tube((xg + 0.006, y, Z_LIV + 0.95), (xr, y, Z_LIV + 0.95), 0.008, 0.008, seg=8, mi=0)
    hr.build("West_Stair_Handrail", M['steel'], smooth=True)
    # recessed step lights in small housings
    sl = MB()
    for i in range(n):
        y = ya + dy * i + 0.15
        z = Z_COURT + dz * i + 0.05
        sl.box(MX0 - 0.16, MX0 - 0.10, y - 0.01, y + 0.15, z - 0.01, z + 0.04, 0)
        sl.box(MX0 - 0.142, MX0 - 0.10, y, y + 0.14, z, z + 0.03, 1)
    sl.build("West_Stair_Lights", [M['black_metal'], M['emit_bar']])


def build(M):
    LOCAL.clear()
    LOCAL.update(_local_materials(M))
    ground_floor(M)
    entry(M)
    l1_slab(M)
    lantern_and_box(M)
    pavilions(M)
    upper_floor(M)
    terraces(M)
    roof(M)
    north_arm(M)
    canopy(M)
    west_stair(M)
