"""Site (the lot and the street): graded front lawn, driveway + curved walk, beds and edging, sidewalk / parkway /
curb / street, the rear paver patio with its river-rock border and stepping stones, the neighbours' fence, neighbour
and street-facing houses (simplified massing with siding, roofs, windows, garage doors).  The common area behind the
lots, the path, the pond, its fountain and the suburb beyond are context.py.  Layout inferred from photos 01, 25-32
(aerials); see REFERENCES.md."""
import math
import random
from .plan import *
from archviz.mesh import MB
from archviz.cladding import Face, lap_siding
from archviz import roofing as rf

from . import site_front as _sf

SIDE_W = _sf.SW                # sidewalk y range (back edge, street edge): 31 joint solve + 01 (see site_front.py)
CURB = _sf.CURB_Y
STREET = _sf.STREET            # curb to curb (context.py imports it)
Z_SW = _sf.Z_SW                # sidewalk surface
Z_ST = _sf.Z_ST                # street surface at the gutter
LOT_L, LOT_R = -3.2, 14.3      # side lot lines (right: the neighbour's fence, photos 25/31)
REAR_LOT = 30.5                # rear lot line = the neighbour's fence corner (31: (14.4, 31.0 +/- 0.7); SITE_FAR 31 ortho 30.3)


def _grade(y):
    """Front-yard grade (kept for older callers): see site_front.grade."""
    return _sf.grade(0.0, y)


# neighbour footprints (x0, x1, y0, y1) that the front lawn must not run through (kept in step with neighbours())
NBR_FOOT = [(-18.7, -5.6, 5.0, 16.0), (-11.45, -5.72, 0.02, 5.0), (-5.72, -4.35, 0.2, 5.0), (16.15, 23.55, 0.0, 6.35),
            (17.45, 29.75, 1.25, 12.5), (23.55, 26.6, -0.6, 2.2), (-34.5, -21.9, 5.2, 15.8), (-28.2, -22.1, 0.02, 5.2)]


def ground(M):
    g = MB()
    # big terrain skirt far below the modelled grade (never seen, catches stray rays)
    g.box(-420, 420, -420, 420, Z_GRADE - 3.2, Z_GRADE - 3.0)
    g.build("Terrain", [M['ground']], coll='Site')


def hardscape(M):
    """Driveways, sidewalks, curbs, street, the walk, front beds, the tree ring, pedestals, front lawns: site_front.py."""
    _sf.build(M, footprints=NBR_FOOT)


def _slab_poly(mb, pts, zf, t):
    """A slab whose top follows zf(x, y) at the polygon's vertices (fan from the centroid), thickness t."""
    cx = sum(p[0] for p in pts) / len(pts); cy = sum(p[1] for p in pts) / len(pts)
    n = len(pts)
    top = [(x, y, zf(x, y)) for (x, y) in pts] + [(cx, cy, zf(cx, cy))]
    bot = [(x, y, z - t) for (x, y, z) in top]
    base = len(mb.v)
    mb.v.extend(top + bot)
    for i in range(n):
        j = (i + 1) % n
        mb.f.append((base + i, base + j, base + n)); mb.fm.append(0)
        mb.f.append((base + n + 1 + j, base + n + 1 + i, base + 2 * n + 1)); mb.fm.append(0)
        mb.f.append((base + i, base + n + 1 + i, base + n + 1 + j, base + j)); mb.fm.append(0)


def patio(M):
    """The rear paver patio, its river-rock border and the photographed staging: site_patio.py (evidence there)."""
    from . import site_patio
    site_patio.build(M)


FENCE_X = 14.30                # right-hand neighbour's black aluminium fence along the lot line (25 / 31 / SITE_FAR)
FENCE_Y0 = 10.85               # house end: the fence turns toward the neighbour's house here (27)
FENCE_H = 1.20                 # 4 ft (25: 1.18 m end post), double top rail + bottom rail, pickets ~0.11 m


def fence(M):
    """Black aluminium picket fence of the right-hand neighbour's yard (photos 25-28, 31): along the lot line from the
    neighbour's rear corner to the rear lot line, along the rear line, and a short return to the neighbour's house."""
    from .site_patio import z_lawn
    f = MB()
    h = FENCE_H

    def run(p0, p1):
        (x0, y0), (x1, y1) = p0, p1
        L = math.hypot(x1 - x0, y1 - y0)
        ux, uy = (x1 - x0) / L, (y1 - y0) / L
        nx, ny = -uy, ux
        zg = min(z_lawn(x0, y0), z_lawn(x1, y1))
        for (z0, z1) in ((0.10, 0.13), (h - 0.17, h - 0.14), (h - 0.035, h - 0.005)):
            f.hexa([(x0 - nx * 0.013, y0 - ny * 0.013, zg + z0), (x1 - nx * 0.013, y1 - ny * 0.013, zg + z0),
                    (x1 + nx * 0.013, y1 + ny * 0.013, zg + z0), (x0 + nx * 0.013, y0 + ny * 0.013, zg + z0),
                    (x0 - nx * 0.013, y0 - ny * 0.013, zg + z1), (x1 - nx * 0.013, y1 - ny * 0.013, zg + z1),
                    (x1 + nx * 0.013, y1 + ny * 0.013, zg + z1), (x0 + nx * 0.013, y0 + ny * 0.013, zg + z1)])
        n = max(1, int(L / 0.11))
        for i in range(1, n):
            x, y = x0 + ux * L * i / n, y0 + uy * L * i / n
            f.box(x - 0.008, x + 0.008, y - 0.008, y + 0.008, zg + 0.06, zg + h - 0.02)
        m = max(1, int(round(L / 1.85)))
        for i in range(m + 1):
            x, y = x0 + ux * L * i / m, y0 + uy * L * i / m
            f.box(x - 0.025, x + 0.025, y - 0.025, y + 0.025, zg - 0.05, zg + h + 0.03)
            f.box(x - 0.03, x + 0.03, y - 0.03, y + 0.03, zg + h + 0.03, zg + h + 0.05)
    run((FENCE_X, FENCE_Y0), (FENCE_X, REAR_LOT))
    run((FENCE_X, REAR_LOT), (FENCE_X + 13.0, REAR_LOT))
    run((FENCE_X, FENCE_Y0), (15.35, FENCE_Y0))
    f.build("Fence_Neighbour", [M['iron_black']], coll='Site')


def lawn_rear(M):
    """The rear lawn of the lot (and the neighbours' yards next to it) as a real surface with holes for the patio,
    its bed and the stepping stones; hair grass grows from it (house GRASS spec, see _grass_specs)."""
    from . import site_patio as sp
    from archviz import paving as _pv
    mb = MB()
    cell = 0.10
    x0, x1, y0, y1 = LOT_L - 2.0, 17.0, YB1 + 0.10, REAR_LOT
    zl = sp.z_lawn
    stones = [(x, y, r + 0.04) for (x, y, r) in sp.STONES]
    nx, ny = int(round((x1 - x0) / cell)), int(round((y1 - y0) / cell))
    for i in range(nx):
        for j in range(ny):
            ax, ay = x0 + i * cell, y0 + j * cell
            cx, cy = ax + cell / 2, ay + cell / 2
            if cy < 15.0 + 4.0 and _pv.point_in_poly(cx, cy, sp.BED_POLY):
                continue
            if any((cx - x) ** 2 + (cy - y) ** 2 < r * r for (x, y, r) in stones):
                continue
            if 0.0 - 0.3 < cx < XB1 + 0.3 and cy < YB1 + 0.25:
                continue                                        # foundation strip along the rear wall
            if abs(cx - FENCE_X) < 0.03:
                continue
            mb.quad((ax, ay, zl(ax, ay)), (ax + cell, ay, zl(ax + cell, ay)), (ax + cell, ay + cell, zl(ax + cell, ay + cell)),
                    (ax, ay + cell, zl(ax, ay + cell)))
    mb.build("Lawn_Rear_Lot", [M['sn_lawn']], coll='Site', recalc=False)


def site_mats(M):
    """Site materials owned by this module (calibrated on photos 01-03, 25-31); shared keys are not overridden."""
    if 'sn_lawn' in M:
        return M
    # lawns calibrated by hue / saturation of sampled patches, photo vs 32-spp polish render (SITE_NEAR follow-up):
    #   rear (25 / 28: hue 67, sat 0.65-0.74, bright yellow-green)   front (01: hue 67-75, sat 0.26-0.34)
    #   parkway (01 / 30: hue 53-54, sat 0.26-0.36, sun-dried tan)
    M['sn_lawn'] = lawn_mat("LotLawnBase", dark=(0.12, 0.17, 0.012, 1), light=(0.29, 0.36, 0.04, 1), dry=(0.40, 0.36, 0.10, 1))
    M['sn_grass'] = grass_mat("LotGrassBlade", root=(0.07, 0.12, 0.008, 1), tip=(0.55, 0.63, 0.06, 1), dry=(0.60, 0.54, 0.14, 1),
                              spec=0.2)
    M['sn_lawn_front'] = lawn_mat("LotLawnFront", dark=(0.07, 0.10, 0.03, 1), light=(0.17, 0.22, 0.07, 1), dry=(0.30, 0.27, 0.12, 1))
    M['sn_grass_front'] = grass_mat("LotGrassBladeFront", root=(0.05, 0.08, 0.02, 1), tip=(0.30, 0.39, 0.11, 1), dry=(0.46, 0.41, 0.20, 1),
                                    dry_frac=0.22, spec=0.2)
    M['sn_lawn_park'] = lawn_mat("ParkwayLawn", dark=(0.10, 0.10, 0.04, 1), light=(0.24, 0.22, 0.10, 1), dry=(0.36, 0.30, 0.14, 1))
    M['sn_grass_park'] = grass_mat("ParkwayGrassBlade", root=(0.07, 0.08, 0.02, 1), tip=(0.39, 0.36, 0.10, 1), dry=(0.54, 0.44, 0.20, 1),
                                   dry_frac=0.45, spec=0.2)
    return M


def lawn_mat(name, dark, light, dry, stripe=0.035, period=0.95):
    """Kentucky-blue / fescue lawn under the hair grass: fine blade noise, broad patchiness, a few dry patches and a
    subtle mowing stripe (bands parallel to Y, `period` m, +/- `stripe`)."""
    from archviz import materials as _m
    m, nt, b = _m._new(name)
    vec = _m._coords(nt)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(sep.inputs["Vector"], tc.outputs["Object"])
    fine = _m._noise(nt, vec, scale=140.0, detail=2.0)
    broad = _m._noise(nt, _m._coords(nt, scale=(0.5, 0.5, 0.5)), scale=1.0, detail=4.0)
    col = _m._ramp(nt, fine, [(0.3, dark), (0.7, light)])
    col = _m._mixrgb(nt, _m._math(nt, 'MULTIPLY', _m._stretch(nt, broad, 0.35, 0.65), 0.35), col, dry)
    s_ = _m._math(nt, 'SINE', _m._math(nt, 'MULTIPLY', sep.outputs["X"], 2 * math.pi / period))
    st = _m._math(nt, 'ADD', 1.0, _m._math(nt, 'MULTIPLY', _m._math(nt, 'MULTIPLY', _m._math(nt, 'SIGN', s_), 1.0), stripe))
    stc = nt.nodes.new("ShaderNodeCombineColor")
    for k in ("Red", "Green", "Blue"):
        nt.links.new(stc.inputs[k], st)
    col = _m._mixrgb(nt, 1.0, col, stc.outputs["Color"], 'MULTIPLY')
    nt.links.new(b.inputs["Base Color"], col)
    _m._set(b, "Roughness", 0.95); _m._set(b, "Specular IOR Level", 0.15); _m._set(b, "Sheen Weight", 0.15)
    _m._bump(nt, b, fine, 0.4, 0.01)
    return m


def grass_mat(name, root, tip, dry, stripe=0.035, period=0.95, dry_frac=0.12, spec=0.35):
    """Hair-grass blades (archviz.polish): dark root -> sunlit tip, ~12 % dry blades, broad patchiness and the same
    subtle mowing stripe as lawn_mat (the stripe is read at the blade's root position)."""
    from archviz import materials as _m
    m, nt, b = _m._new(name)
    hi = nt.nodes.new("ShaderNodeHairInfo")
    col = _m._ramp(nt, hi.outputs["Intercept"], [(0.0, root), (0.55, (tip[0] * 0.72, tip[1] * 0.8, tip[2] * 0.62, 1)), (1.0, tip)])
    col = _m._mixrgb(nt, _m._math(nt, 'GREATER_THAN', hi.outputs["Random"], 1.0 - dry_frac), col, dry)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(sep.inputs["Vector"], tc.outputs["Object"])
    patch = _m._noise(nt, _m._coords(nt, scale=(0.6, 0.6, 0.6)), scale=1.0, detail=3.0)
    col = _m._mixrgb(nt, _m._math(nt, 'MULTIPLY', _m._stretch(nt, patch, 0.35, 0.65), 0.3), col, (0.80, 0.86, 0.62, 1), 'MULTIPLY')
    s_ = _m._math(nt, 'SINE', _m._math(nt, 'MULTIPLY', sep.outputs["X"], 2 * math.pi / period))
    st = _m._math(nt, 'ADD', 1.0, _m._math(nt, 'MULTIPLY', _m._math(nt, 'SIGN', s_), stripe))
    stc = nt.nodes.new("ShaderNodeCombineColor")
    for k in ("Red", "Green", "Blue"):
        nt.links.new(stc.inputs[k], st)
    col = _m._mixrgb(nt, 1.0, col, stc.outputs["Color"], 'MULTIPLY')
    nt.links.new(b.inputs["Base Color"], col)
    _m._set(b, "Roughness", 0.6); _m._set(b, "Specular IOR Level", spec); _m._set(b, "Coat Weight", 0.1 if spec > 0.3 else 0.0)
    tr = nt.nodes.new("ShaderNodeBsdfTranslucent"); nt.links.new(tr.inputs["Color"], col)
    mix = nt.nodes.new("ShaderNodeMixShader"); mix.inputs["Fac"].default_value = 0.3
    nt.links.new(mix.inputs[1], b.outputs["BSDF"]); nt.links.new(mix.inputs[2], tr.outputs["BSDF"])
    nt.links.new(nt.nodes["Material Output"].inputs["Surface"], mix.outputs["Shader"])
    return m


def _grass_specs(M):
    """Replace the house's rectangular rear grass emitter by hair on the lot lawn surface (runtime: GRASS is read by
    run.py after every module has been built)."""
    import sys
    H = sys.modules.get(__name__.rsplit('.', 1)[0] + '.house')
    if H is None or not hasattr(H, 'GRASS'):
        return
    mine = ('Lawn_Rear_Lot', 'Lawn_Front_Lot', 'Lawn_Parkway')
    keep = [g for g in H.GRASS if g.get('name') not in ('Grass_Rear', 'Grass_Front') and g.get('object') not in mine]
    keep.append(dict(object="Lawn_Rear_Lot", mat=M['sn_grass'], count=160000, length=0.075, children=10, seed=5))
    keep.append(dict(object="Lawn_Front_Lot", mat=M['sn_grass_front'], count=140000, length=0.065, children=10, seed=3))
    keep.append(dict(object="Lawn_Parkway", mat=M['sn_grass_park'], count=30000, length=0.06, children=10, seed=4))
    H.GRASS[:] = keep


# ================================================================ neighbour houses (simplified massing)
def simple_house(name, M, x0, x1, y0, y1, h2, siding, roof, pitch=0.58, gable='side', garage=None, brick_front=False,
                 front_gables=(), wins=()):
    """A plausible suburban neighbour: two-storey box with lap siding (geometry), a side- or front-gabled roof with
    shingles, white trim, windows with shutters, an optional garage bump (x0, x1, depth, door colour key) and
    decorative front gables over the upper storey.  All in world coordinates, facing -Y (the street)."""
    body = MB()
    body.box(x0, x1, y0, y1, Z_GRADE - 0.2, Z_GRADE + h2)
    body.build(f"{name}_Body", [M['siding_back']], coll='Neighbours')
    # windows on every face: (face, a, z, w, h, shutters) - front from `wins`, rear / sides generated
    faces = {'F': ('X', y0, -1, x0, x1), 'B': ('X', y1, 1, x0, x1), 'L': ('Y', x0, -1, y0, y1), 'R': ('Y', x1, 1, y0, y1)}
    allw = [('F', wx, wz, ww, wh, True) for (wx, wz, ww, wh) in wins]
    L = x1 - x0
    for f in (0.2, 0.5, 0.8):
        allw.append(('B', x0 + L * f, 3.3, 0.9, 1.5, False))
    allw.append(('B', x0 + L * 0.35, 0.05, 1.8, 2.05, False))               # patio slider
    allw.append(('B', x0 + L * 0.72, 0.75, 1.6, 1.4, False))
    for side in ('L', 'R'):
        allw.append((side, (y0 + y1) / 2 + 1.0, 3.3, 0.9, 1.4, False))
        allw.append((side, (y0 + y1) / 2 - 2.0, 0.9, 0.9, 1.3, False))
    sid = MB()
    for key, (al, b, out, a0, a1) in faces.items():
        cut = [(a - w / 2 - 0.1, a + w / 2 + 0.1, z - 0.1, z + h + 0.1) for (fk, a, z, w, h, _) in allw if fk == key]
        cut = [(c0, c1, Z_GRADE + z0, Z_GRADE + z1) for (c0, c1, z0, z1) in cut]
        zb = Z_GRADE + 2.9 if (brick_front and key == 'F') else Z_GRADE + 0.1
        lap_siding(sid, Face(al, b, out), a0, a1, zb, Z_GRADE + h2 - 0.1, holes=cut, exposure=0.19)
    sid.build(f"{name}_Siding", [siding], coll='Neighbours')
    if brick_front:
        bk = MB(); bk.box(x0 - 0.02, x1 + 0.02, y0 - 0.12, y0 + 0.1, Z_GRADE - 0.1, Z_GRADE + 2.9)
        bk.build(f"{name}_Brick", [M['brick']], coll='Neighbours')
    t = MB()
    fr = MB()
    for (key, a, wz, ww, wh, shut) in allw:
        al, b, out, _, _ = faces[key]
        F = Face(al, b, out)
        z0 = Z_GRADE + wz
        d0 = 0.13 if (brick_front and key == 'F' and wz < 2.5) else 0.0
        F.box(fr, a - ww / 2, a + ww / 2, d0 - 0.04, d0 + 0.01, z0, z0 + wh, 1)
        for (b0, b1, c0, c1) in ((a - ww / 2 - 0.09, a - ww / 2, z0 - 0.09, z0 + wh + 0.09), (a + ww / 2, a + ww / 2 + 0.09, z0 - 0.09, z0 + wh + 0.09),
                                 (a - ww / 2, a + ww / 2, z0 - 0.09, z0), (a - ww / 2, a + ww / 2, z0 + wh, z0 + wh + 0.09)):
            F.box(t, b0, b1, d0 + 0.01, d0 + 0.04, c0, c1, 0)                  # casing frame around the glass
        F.box(fr, a - 0.015, a + 0.015, d0 + 0.01, d0 + 0.03, z0, z0 + wh, 0)
        F.box(fr, a - ww / 2, a + ww / 2, d0 + 0.01, d0 + 0.03, z0 + wh / 2 - 0.02, z0 + wh / 2 + 0.02, 0)
        if shut:
            F.box(fr, a - ww / 2 - 0.5, a - ww / 2 - 0.1, d0 + 0.02, d0 + 0.05, z0, z0 + wh, 2)
            F.box(fr, a + ww / 2 + 0.1, a + ww / 2 + 0.5, d0 + 0.02, d0 + 0.05, z0, z0 + wh, 2)
    t.build(f"{name}_Trim", [M['trim']], coll='Neighbours')
    fr.build(f"{name}_Windows", [M['trim'], M['neighbour_glass'], M['shutter']], coll='Neighbours')
    sh = [roof]
    zt = Z_GRADE + h2 + 0.25
    k = 0.32
    zf = zt - k * pitch
    if gable == 'side':
        ym = (y0 + y1) / 2
        rf.slope(f"{name}_RoofF", sh, (x0 - k, y0 - k, zf), (1, 0), (0, 1), pitch, [(x0 - k, y0 - k), (x1 + k, y0 - k), (x1 + k, ym), (x0 - k, ym)], 0.1, 'Neighbours')
        rf.slope(f"{name}_RoofB", sh, (x0 - k, y1 + k, zf), (1, 0), (0, -1), pitch, [(x0 - k, y1 + k), (x1 + k, y1 + k), (x1 + k, ym), (x0 - k, ym)], 0.1, 'Neighbours')
        zr = zt + (ym - y0) * pitch
        tri = MB()
        for x in (x0, x1):
            tri._add([(x, y0, zt - 0.3), (x, y1, zt - 0.3), (x, ym, zr - 0.15)], [(0, 1, 2)], 0)
        tri.build(f"{name}_Gables", [siding], coll='Neighbours')
    else:
        xm = (x0 + x1) / 2
        rf.slope(f"{name}_RoofL", sh, (x0 - k, y0 - k, zf), (0, 1), (1, 0), pitch, [(x0 - k, y0 - k), (xm, y0 - k), (xm, y1 + k), (x0 - k, y1 + k)], 0.1, 'Neighbours')
        rf.slope(f"{name}_RoofR", sh, (x1 + k, y0 - k, zf), (0, 1), (-1, 0), pitch, [(x1 + k, y0 - k), (xm, y0 - k), (xm, y1 + k), (x1 + k, y1 + k)], 0.1, 'Neighbours')
        zr = zt + (xm - x0) * pitch
        tri = MB()
        for y in (y0, y1):
            tri._add([(x0, y, zt - 0.3), (x1, y, zt - 0.3), (xm, y, zr - 0.15)], [(0, 1, 2)], 0)
        tri.build(f"{name}_Gables", [siding], coll='Neighbours')
    for i, (gx0, gx1) in enumerate(front_gables):
        gm = (gx0 + gx1) / 2
        p2 = 0.85
        zg = zt + (gm - gx0) * p2
        rf.slope(f"{name}_FG{i}L", sh, (gx0 - k, y0 - 0.7 - k, zf), (0, 1), (1, 0), p2, [(gx0 - k, y0 - 0.7 - k), (gm, y0 - 0.7 - k), (gm, y0 + 2.5), (gx0 - k, y0 + 2.5)], 0.1, 'Neighbours')
        rf.slope(f"{name}_FG{i}R", sh, (gx1 + k, y0 - 0.7 - k, zf), (0, 1), (-1, 0), p2, [(gx1 + k, y0 - 0.7 - k), (gm, y0 - 0.7 - k), (gm, y0 + 2.5), (gx1 + k, y0 + 2.5)], 0.1, 'Neighbours')
        fg = MB()
        fg.box(gx0, gx1, y0 - 0.7, y0, Z_GRADE + 2.9, zt - 0.3)
        fg._add([(gx0, y0 - 0.7, zt - 0.3), (gx1, y0 - 0.7, zt - 0.3), (gm, y0 - 0.7, zg - 0.15)], [(0, 1, 2)], 0)
        fg.build(f"{name}_FG{i}", [siding], coll='Neighbours')
    if garage:
        gx0, gx1, depth, door = garage
        gb = MB()
        gb.box(gx0, gx1, y0 - depth, y0, Z_GRADE - 0.1, Z_GRADE + 2.9)
        gb.build(f"{name}_Garage", [M['brick'] if brick_front else siding], coll='Neighbours')
        gd = MB()
        gd.box(gx0 + 0.5, gx1 - 0.5, y0 - depth - 0.02, y0 - depth + 0.02, Z_GRADE, Z_GRADE + 2.13)
        gd.build(f"{name}_GarageDoor", [M[door]], coll='Neighbours')
        rf.slope(f"{name}_GarageRoof", sh, (gx0 - k, y0 - depth - k, Z_GRADE + 3.05), (1, 0), (0, 1), 0.33,
                 [(gx0 - k, y0 - depth - k), (gx1 + k, y0 - depth - k), (gx1 + k, y0 + 0.3), (gx0 - k, y0 + 0.3)], 0.1, 'Neighbours')


def gable_garage(name, M, x0, x1, y0, y1, wall, roof, door='garage_white', pitch=0.75):
    """A one-storey front-gabled garage bump (tan brick, oculus in the gable, white sectional door) - photos 30/31."""
    b = MB()
    zt = Z_GRADE + 2.75
    b.box(x0, x1, y0, y1, Z_GRADE - 0.1, zt)
    xm = (x0 + x1) / 2
    zr = zt + (xm - x0) * pitch
    b._add([(x0, y0, zt), (x1, y0, zt), (xm, y0, zr - 0.2)], [(0, 1, 2)], 0)
    b.build(f"{name}_GarageBump", [wall], coll='Neighbours')
    k = 0.3
    rf.slope(f"{name}_GarageRoofL", [roof], (x0 - k, y0 - k, zt + 0.25 - k * pitch), (0, 1), (1, 0), pitch,
             [(x0 - k, y0 - k), (xm, y0 - k), (xm, y1 + 0.5), (x0 - k, y1 + 0.5)], 0.1, 'Neighbours')
    rf.slope(f"{name}_GarageRoofR", [roof], (x1 + k, y0 - k, zt + 0.25 - k * pitch), (0, 1), (-1, 0), pitch,
             [(x1 + k, y0 - k), (xm, y0 - k), (xm, y1 + 0.5), (x1 + k, y1 + 0.5)], 0.1, 'Neighbours')
    t = MB()
    rf.rake_board(t, (x0 - k, y0 - k), (xm, y0 - k), zt + 0.25 - k * pitch, zr + 0.25, (0, -1))
    rf.rake_board(t, (x1 + k, y0 - k), (xm, y0 - k), zt + 0.25 - k * pitch, zr + 0.25, (0, -1))
    t.cylinder(xm, y0 - 0.02, zr - 0.95, zr - 0.93, 0.22, seg=24)
    t.build(f"{name}_GarageTrim", [M['trim']], coll='Neighbours')
    d = MB()
    d.box(xm - 2.4, xm + 2.4, y0 - 0.03, y0 + 0.01, Z_GRADE, Z_GRADE + 2.13)
    for i in range(1, 4):
        d.box(xm - 2.4, xm + 2.4, y0 - 0.035, y0 - 0.03, Z_GRADE + 2.13 * i / 4 - 0.006, Z_GRADE + 2.13 * i / 4 + 0.006)
    d.build(f"{name}_GarageDoor", [M[door]], coll='Neighbours')


def neighbours(M):
    """The adjacent houses (measured massing, site_nbrs.py), the street row beyond them, and the parked cars (31)."""
    from . import site_nbrs as nb
    nb.mats(M)
    nb.left_house(M)
    nb.right_house(M)
    nb.street_row(M, simple_house)
    # parked as in 31 / 30 (staging): two SUVs on the left neighbour's drive, a dark sedan on the right one's
    nb.car("Car_NbrL_White", M, -10.1, -2.6, math.pi / 2, M['nb_car_white'], L=4.9, W=1.95, H=1.75)       # 31: silver SUV
    nb.car("Car_NbrL_Grey", M, -7.45, -2.3, math.pi / 2, M['nb_car_dark'], L=4.7, W=1.9, H=1.68)          # 31: dark SUV
    nb.car("Car_NbrR_Dark", M, 22.0, -2.7, math.pi / 2, M['nb_car_dark'], L=4.9, W=1.85, H=1.45, suv=False)


def build(M):
    site_mats(M)
    ground(M)
    hardscape(M)
    patio(M)
    lawn_rear(M)
    fence(M)
    neighbours(M)
    _grass_specs(M)
