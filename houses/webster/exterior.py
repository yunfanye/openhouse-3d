"""Envelope of 1836 Webster: every wall of plan.WALLS (with plan.OPENINGS cut out), the window / door units, the
arch heads, slabs, roofs (flat parapet roofs with vent dots, the clay-tile gable, the wing shed roof), chimney,
porch (floor, steps, hood, lantern), rear brick steps + rail, side-door stoop, deck floor, Juliet rail, trellis and
the exterior lanterns.  Interior finishes / furniture / lights are the interior_* modules'; the site is site.py.

Wall construction: each wall is ONE box of its outer material (stucco / paint) with the holes; exterior walls then get
a 10 mm paint skin on their inside face (same holes), so corners are always stucco outside and paint inside.
Walls that run into another wall's thickness are trimmed at that wall's face (no coplanar exposed faces)."""
import math, random
import bpy
from mathutils import Vector
from .plan import *
from archviz.mesh import *
from archviz.lights import *
from archviz.parts import *
from archviz import materials as _mat

K30 = (1.0, 0.84, 0.66)
SKIN = 0.01                       # inner paint skin on exterior walls
# local overrides / additions (plan.py is read-only for this module)
DOOR_BED2 = (10.55, 11.4)         # plan's 10.7..11.55 runs into the bed2|bed3 wall (y 11.45): shifted 0.15 toward the room
FRENCH_OPEN = {'FamFrench': (150.0, 150.0)}   # per-leaf open angles (a0 leaf, a1 leaf)
TOWER_Y = -0.2                    # the entry tower's street face is 0.2 m proud of the living block (photo 00): the door sits 0.3 m back
ARCH_SPRING, ARCH_APEX, ARCH_TOP = 1.82, 2.24, 2.45   # pointed (four-centred) arch over the front door (overlay on photo 00: spring 1.82, apex 2.24); the wall hole is cut to ARCH_TOP
# board-and-batten shutters (width) beside windows the plan does not tag; fixed-centre triples with a transom row
SHUTTERS = {'LivFront':.42,'PrimWE1':.4,'PrimWE2':.4,'LauW':.30}
FIXED_CENTRE = {'LivFront': dict(transom=.35,lites=6),'PrimWF':dict(transom=.25,lites=6)}
DOOR_HINGE = {'DoorPrim': 'a1'}   # the open leaf must lie away from the film route (it enters at y 11.1 heading +X)
UP_CENTRE = ((UPX0 + WINGX1) / 2, (UPY0 + UPY1) / 2)

_L = {}


def _stucco(name, base):
    """Sand-float stucco: fine sand grain + trowel undulation + a wide waviness in the bump, mottled tint."""
    m, nt, b = _mat._new(name)
    vec = _mat._coords(nt)
    fine = _mat._noise(nt, vec, scale=260.0, detail=5.0, rough=0.65)
    mid = _mat._noise(nt, vec, scale=16.0, detail=3.0, rough=0.55)
    low = _mat._noise(nt, vec, scale=0.7, detail=2.0)
    tint = _mat._ramp(nt, _mat._noise(nt, vec, scale=2.2, detail=2.0), [(0.35, (0.90, 0.91, 0.93, 1)), (0.65, (1.07, 1.06, 1.04, 1))])
    col = _mat._mixrgb(nt, 1.0, base, tint, 'MULTIPLY')
    nt.links.new(b.inputs["Base Color"], col)
    _mat._set(b, "Roughness", 0.93); _mat._set(b, "Specular IOR Level", 0.22)
    h = _mat._math(nt, 'ADD', _mat._math(nt, 'MULTIPLY', fine, 0.55),
                   _mat._math(nt, 'ADD', _mat._math(nt, 'MULTIPLY', mid, 0.30), _mat._math(nt, 'MULTIPLY', low, 0.15)))
    _mat._bump(nt, b, h, 0.5, 0.005)
    return m


def _clay(name):
    """Clay S-tile: per-tile colour variation (voronoi cells ~ one tile) over three clay tones, fine sandy bump,
    a little soot / lichen darkening in the pans."""
    m, nt, b = _mat._new(name)
    vec = _mat._coords(nt)
    cell = _mat._voronoi(nt, vec, scale=3.6, feature='F1', rand=1.0)
    csep = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(csep.inputs["Color"], cell.outputs["Color"])
    col = _mat._ramp(nt, csep.outputs["Red"], [(0.0, (0.50, 0.27, 0.19, 1)), (0.4, (0.66, 0.40, 0.29, 1)), (0.72, (0.76, 0.54, 0.42, 1)), (1.0, (0.58, 0.33, 0.24, 1))])   # weathered pale terracotta (photo p00_upper)
    dirt = _mat._noise(nt, vec, scale=6.0, detail=4.0)
    col = _mat._mixrgb(nt, _mat._math(nt, 'MULTIPLY', _mat._stretch(nt, dirt, 0.45, 0.7), 0.35), col, (0.30, 0.22, 0.17, 1))
    lich = _mat._noise(nt, vec, scale=14.0, detail=5.0)
    col = _mat._mixrgb(nt, _mat._math(nt, 'MULTIPLY', _mat._stretch(nt, lich, 0.55, 0.72), 0.45), col, (0.78, 0.76, 0.70, 1))   # lichen / lime bloom
    nt.links.new(b.inputs["Base Color"], col)
    _mat._set(b, "Roughness", 0.78); _mat._set(b, "Specular IOR Level", 0.3)
    fine = _mat._noise(nt, vec, scale=120.0, detail=4.0)
    _mat._bump(nt, b, fine, 0.25, 0.004)
    return m


def _local(M):
    if _L:
        return _L
    _L['stucco'] = _stucco("StuccoSandFloat", (0.36, 0.41, 0.46, 1))
    _L['stucco_pale'] = _stucco("StuccoSandFloatPale", (0.42, 0.46, 0.51, 1))
    _L['tile'] = _clay("ClayTileS")
    _L['screed'] = _mat.new_mat("WeepScreed", (0.18, 0.19, 0.20, 1), rough=0.6, metal=0.3)
    _L['meter'] = _mat.new_mat("MeterBoxGrey", (0.46, 0.47, 0.46, 1), rough=0.5, spec=0.4)
    _L['cap'] = _mat.noise_mat("ParapetCap", (0.62, 0.62, 0.60, 1), (0.74, 0.73, 0.70, 1), scale=40, bump=0.15, rough=0.85, spec=0.25)
    _L['gutter'] = _mat.new_mat("GutterWhite", (0.86, 0.86, 0.84, 1), rough=0.35, spec=0.5, coat=0.2)
    _L['galv'] = _mat.new_mat("Galvanised", (0.62, 0.63, 0.63, 1), rough=0.45, metal=0.85)
    _L['screen'] = _mat.new_mat("InsectScreen", (0.06, 0.06, 0.06, 1), rough=0.7, alpha=0.45)
    _L['coir'] = _mat.fabric("Doormat", (0.42, 0.30, 0.16, 1), weave=120, bump=0.6, rough=1.0)
    _L['border'] = _mat.tiles("PorchBorder", (0.50, 0.30, 0.20, 1), grout=(0.60, 0.53, 0.43, 1), size=(0.15, 0.15), gap=0.005, rough=0.4, variation=0.1, mottle=0.3, bump=0.2, coat=0.2)
    _L['paver'] = _mat.tiles("DeckPaver", (0.60, 0.58, 0.54, 1), grout=(0.42, 0.41, 0.39, 1), size=(0.4, 0.4), gap=0.008, rough=0.85, variation=0.08, mottle=0.35, bump=0.3)
    _L['mortar'] = _mat.noise_mat("RidgeMortar", (0.55, 0.53, 0.48, 1), (0.66, 0.64, 0.58, 1), scale=30, bump=0.3, rough=0.95, spec=0.1)
    _L['bulb'] = _mat.new_mat("LanternBulb", (1.0, 0.85, 0.6, 1), rough=0.2, emit=(1.0, 0.75, 0.45, 1), emit_str=14.0)
    _L['dot'] = _mat.plaster("VentDot", base=(0.04, 0.04, 0.045, 1), rough=0.95, grain=0.05)
    _L['plum'] = _mat.new_mat("DoorPlum", (0.30, 0.10, 0.18, 1), rough=0.35, coat=0.35)
    _L['frame_dark'] = _mat.new_mat("DoorFrameDark", (0.20, 0.17, 0.18, 1), rough=0.5)
    _L['soffit'] = _mat.plaster("SoffitStucco", base=(0.40, 0.44, 0.49, 1), rough=0.9, grain=0.2)
    _L['glass_lead'] = _mat.new_mat("GlassLeaded", (0.88, 0.92, 0.95, 1), rough=0.05, transmission=1.0, ior=1.5, spec=0.5)
    _L['lead'] = _mat.new_mat("LeadCame", (0.25, 0.25, 0.27, 1), rough=0.5, metal=0.8)
    _L['tread'] = _mat.tiles("PorchTread", (0.78, 0.68, 0.52, 1), grout=(0.60, 0.53, 0.43, 1), size=(0.3, 0.3), gap=0.005, rough=0.4, variation=0.06, mottle=0.3, bump=0.2, coat=0.2)
    return _L


# ---------------------------------------------------------------- frame helpers
def _ab(along, a, b):
    """(x, y) from wall coordinates."""
    return (a, b) if along == 'X' else (b, a)


def B(mb, along, a0, a1, b0, b1, z0, z1, mi):
    if along == 'X':
        mb.box(a0, a1, b0, b1, z0, z1, mi)
    else:
        mb.box(b0, b1, a0, a1, z0, z1, mi)


def _hexa_ab(mb, along, quad_bottom, quad_top, mi):
    """hexa from (a, b, z) tuples."""
    vs = [(*_ab(along, a, b), z) for (a, b, z) in quad_bottom + quad_top]
    mb.hexa(vs, mi)


def prism_y(mb, pts, y0, y1, mi=0):
    """Extrude an (x, z) polygon along Y (gable triangles, wedges, diamonds)."""
    n = len(pts)
    vs = [(x, y0, z) for (x, z) in pts] + [(x, y1, z) for (x, z) in pts]
    fs = [tuple(range(n)), tuple(reversed(range(n, 2 * n)))]
    for i in range(n):
        j = (i + 1) % n
        fs.append((i, j, n + j, n + i))
    mb._add(vs, fs, mi)


def prism_x(mb, pts, x0, x1, mi=0):
    """Extrude a (y, z) polygon along X."""
    n = len(pts)
    vs = [(x0, y, z) for (y, z) in pts] + [(x1, y, z) for (y, z) in pts]
    fs = [tuple(range(n)), tuple(reversed(range(n, 2 * n)))]
    for i in range(n):
        j = (i + 1) % n
        fs.append((i, j, n + j, n + i))
    mb._add(vs, fs, mi)


def prism_ab(mb, along, pts, b0, b1, mi=0):
    """Extrude an (a, z) polygon through a wall's thickness b0..b1."""
    if along == 'X':
        prism_y(mb, pts, b0, b1, mi)
    else:
        prism_x(mb, pts, b0, b1, mi)


def tube(mb, p0, p1, r, seg=8, mi=0):
    mb.tube(p0, p1, r, r, seg=seg, mi=mi)


# ---------------------------------------------------------------- walls
def outside_sign(w):
    """+1 if the outside is toward +b, -1 toward -b (exterior / upper walls)."""
    if w['kind'] == 'up':
        c = UP_CENTRE[1] if w['along'] == 'X' else UP_CENTRE[0]
        return -1 if (w['b0'] + w['b1']) / 2 < c else 1
    if w['along'] == 'X':
        return -1 if w['b1'] <= 2.06 else 1
    return -1 if w['b1'] <= -5.4 or (abs(w['b0']+.4)<1e-4 and w['a0']>=BED_REAR) else 1        # the porch-side wall at x -1.4..-1.25 faces +X


def trimmed_walls():
    """Copies of plan.WALLS: duplicates dropped, ends trimmed where a wall runs into another wall's thickness."""
    ws = []
    for w in WALLS:
        dup = False
        for v in ws:
            if v['along'] == w['along'] and v['b0'] - 1e-6 <= w['b0'] and w['b1'] <= v['b1'] + 1e-6 and \
               v['a0'] - 1e-6 <= w['a0'] and w['a1'] <= v['a1'] + 1e-6 and v['z0'] - 1e-6 <= w['z0'] and w['z1'] <= v['z1'] + 1e-6:
                dup = True
        if not dup:
            ws.append(dict(w))
    for p in ws:
        for q in ws:
            if p is q or p['along'] == q['along']:
                continue
            if p['z1'] <= q['z0'] + 1e-6 or p['z0'] >= q['z1'] - 1e-6:
                continue
            # p's thickness within q's length, q's thickness overlapping one END of p
            if not (q['a0'] - 1e-6 <= p['b0'] and p['b1'] <= q['a1'] + 1e-6):
                continue
            if q['b0'] < p['a1'] - 1e-6 and q['b1'] >= p['a1'] - 1e-6 and q['b0'] > p['a0']:
                p['a1'] = q['b0']
            elif q['b1'] > p['a0'] + 1e-6 and q['b0'] <= p['a0'] + 1e-6 and q['b1'] < p['a1']:
                p['a0'] = q['b1']
    return [w for w in ws if w['a1'] - w['a0'] > 1e-4]


def build_walls(M):
    from .roof_form import profiled_wall
    L = _local(M)
    st = MB()      # stucco
    pt = MB()      # paint
    cap = MB()     # precast parapet caps (0 cap, 1 joint)
    ws = trimmed_walls()
    for w in ws:
        holes = holes_for(w)
        along, a0, a1, b0, b1, z0, z1 = w['along'], w['a0'], w['a1'], w['b0'], w['b1'], w['z0'], w['z1']
        if w['kind'] == 'int':
            pt.wall(along, a0, a1, b0, b1, z0, z1, holes=holes, mi=0)
            continue
        if w['kind'] == 'par':
            holes = list(holes) + _scupper_holes(w)
        holes = _arch_holes(w, holes)
        if along == 'X' and abs(b0) < 1e-6 and abs(a0 + 1.25) < 1e-6 and w['kind'] == 'ext':
            z1 = ARCH_TOP                                    # the entry front: its top above the arch is the raked wedge (build_entry)
            w['entry_base']=True
        if w['kind'] in ('ext','up'):
            profiled_wall(st,w,holes,mi=0)
        else:
            st.wall(along, a0, a1, b0, b1, z0, z1, holes=holes, mi=0)
        if w['kind'] == 'par':
            _parapet_cap(cap, along, a0, a1, b0, b1, z1)
            continue
        # exterior: paint skin on the inside face over the interior height
        s = outside_sign(w)
        zi0, zi1 = (0.0, Z_MC) if w['kind'] == 'ext' else (Z_UP, Z_UPC)
        zi0, zi1 = max(zi0, z0), min(zi1, z1)
        if zi1 - zi0 < 0.05:
            continue
        if s > 0:
            sb0, sb1 = b0 - SKIN, b0
        else:
            sb0, sb1 = b1, b1 + SKIN
        skin=dict(w,b0=sb0,b1=sb1,z0=zi0,roof_ref_b=(b0+b1)/2)
        profiled_wall(pt,skin,holes,mi=0,paint=True)
    # gable triangles (front / rear of the gable block) + wing wedges
    # (their tops sit 0.12 under the roof surface = inside the roof slab, so no face is coplanar with the tiles)
    # (the triangles' edges sit 0.02 inside the 0.12 gable sheathing slab; the wing wedges follow the shed roof line
    #  and poke 0.01 into its 0.03 sheathing, so there is no slot under the eaves anywhere)
    # (only the REAR gable end: the front of the block is a hip, photo 00)
    # The profiled upper walls already include the rear gable infill.
    # the entry tower's proud street face (0.2 m in front of the plan wall) with the arched doorway cut through it
    fd = BY_NAME['FrontDoor']
    st.wall('X', -1.25, 1.2, TOWER_Y, 0.0, Z_GRADE, ARCH_TOP, holes=[(fd['a0'], fd['a1'], 0.0, ARCH_TOP)], mi=0)   # (its top above ARCH_TOP follows the tile band: build_entry)
    # chimney: stucco stack above the roof deck only (an interior breast below: interior_front), corbelled band near the top
    # the wing's rear bay cantilevers 1.35 m past the laundry rear wall (x 3.5..4.8, y 13.85..15.2): a stucco soffit box
    # carries it (no parapet may run through the primary bath above)
    st.box(3.5, WINGX1, 13.85, WINGY1, Z_MC, Z_ROOF1, 0)
    cx0, cx1, cy0, cy1, ctop = CHIMNEY
    st.box(cx0, cx1, cy0, cy1, Z_ROOF1 - 0.03, ctop, 0)
    st.box(cx0 - 0.03, cx1 + 0.03, cy0 - 0.03, cy1 + 0.03, ctop - 0.35, ctop - 0.25, 0)
    st.build("Ext_Walls_Stucco", [L['stucco']], coll='House')
    pt.build("Ext_Walls_Paint", [M['wall']], coll='House')
    cap.build("Ext_ParapetCaps", [L['cap'], L['dot']], coll='House')
    # chimney crown (concrete, with a drip) + clay pot + spark arrestor cage with a little hood
    mb = MB()
    mb.box(cx0 - 0.05, cx1 + 0.05, cy0 - 0.05, cy1 + 0.05, ctop, ctop + 0.09, 0)
    mb.box(cx0 - 0.05, cx1 + 0.05, cy0 - 0.05, cy0 - 0.04, ctop - 0.015, ctop, 0)
    mb.box(cx0 - 0.05, cx1 + 0.05, cy1 + 0.04, cy1 + 0.05, ctop - 0.015, ctop, 0)
    mb.box(cx0 - 0.05, cx0 - 0.04, cy0 - 0.05, cy1 + 0.05, ctop - 0.015, ctop, 0)
    mb.box(cx1 + 0.04, cx1 + 0.05, cy0 - 0.05, cy1 + 0.05, ctop - 0.015, ctop, 0)
    pcx, pcy = (cx0 + cx1) / 2, (cy0 + cy1) / 2
    mb.lathe(pcx, pcy, ctop + 0.09, [(0, 0), (0.14, 0), (0.13, 0.05), (0.11, 0.3), (0.125, 0.36), (0.10, 0.36), (0.09, 0.05), (0, 0.05)], seg=18, mi=1)
    for (x, y) in ((pcx - 0.12, pcy - 0.12), (pcx + 0.12, pcy - 0.12), (pcx + 0.12, pcy + 0.12), (pcx - 0.12, pcy + 0.12)):
        mb.box(x - 0.006, x + 0.006, y - 0.006, y + 0.006, ctop + 0.42, ctop + 0.72, 2)
    for zz in (ctop + 0.5, ctop + 0.62):
        mb.frame(pcx - 0.126, pcx + 0.126, pcy - 0.126, pcy + 0.126, zz, zz + 0.006, 0.006, mi=2, axis='Z')
    mb.hexa([(pcx - 0.17, pcy - 0.17, ctop + 0.72), (pcx + 0.17, pcy - 0.17, ctop + 0.72), (pcx + 0.17, pcy + 0.17, ctop + 0.72), (pcx - 0.17, pcy + 0.17, ctop + 0.72),
             (pcx - 0.04, pcy - 0.04, ctop + 0.82), (pcx + 0.04, pcy - 0.04, ctop + 0.82), (pcx + 0.04, pcy + 0.04, ctop + 0.82), (pcx - 0.04, pcy + 0.04, ctop + 0.82)], 2)
    mb.build("Ext_ChimneyCap", [L['cap'], L['tile'], M['iron_black']], coll='House', smooth=True)
    # base: weep screed band, louvred foundation vents, the electrical meter + conduit on the driveway wall
    _build_base(M, ws)
    # vent dots: groups of three on the single-storey exterior walls at z 3.15, on the upper walls at z 5.55 -
    # flush dark discs with a pale rim and three louvre bars (real round vents, not black buttons)
    dots = MB()
    for w in ws:
        if w['kind'] not in ('ext', 'up'):
            continue
        if w['kind']=='up' and w['along']=='X' and abs(w['b1']-UPY1)<1e-4:
            continue  # rear gable has one rectangular louver, photos 28/29
        along, a0, a1, b0, b1 = w['along'], w['a0'], w['a1'], w['b0'], w['b1']
        s = outside_sign(w)
        z = 3.15 if w['kind'] == 'ext' else 5.55
        if w['kind'] == 'up' and w['z1'] < z + 0.15:
            z = w['z1'] - 0.25
        face = b1 if s > 0 else b0
        L_ = a1 - a0
        if L_ < 1.2:
            continue
        if along == 'X' and (abs(b0 - 1.8) < 1e-6 or (abs(b0) < 1e-6 and a0 > -1.3) or abs(b0 - UPY0) < 1e-6 or abs(b0 - WINGY0) < 1e-6) and s < 0:
            continue                                                  # photo 00: no dots on the entry / dining / upper street fronts
        centres = [a0 + 0.9] if (along == 'X' and abs(b0) < 1e-6 and a0 < -5.0) else \
                  [a0 + 0.6 + (L_ - 1.2) * ((k + 0.5) / max(1, int(round((L_ - 0.8) / 2.4)))) for k in range(max(1, int(round((L_ - 0.8) / 2.4))))]
        for ac in centres:
            from .roof_form import wall_height
            if min(wall_height(w,ac+d,face) for d in (-.18,0,.18)) < z+.08:
                continue
            for d in (-0.13, 0.0, 0.13):
                p0 = _ab(along, ac + d, face - s * 0.02)
                p1 = _ab(along, ac + d, face + s * 0.002)
                tube(dots, (p0[0], p0[1], z), (p1[0], p1[1], z), 0.036, seg=14, mi=0)
                p2 = _ab(along, ac + d, face + s * 0.006)
                tube(dots, (p1[0], p1[1], z), (p2[0], p2[1], z), 0.044, seg=14, mi=1)          # rim (stucco colour)
                tube(dots, (p0[0], p0[1], z), (p2[0], p2[1], z), 0.030, seg=14, mi=0) if False else None
                for dz in (-0.018, 0.0, 0.018):                                                   # louvre bars
                    B(dots, along, ac + d - 0.03, ac + d + 0.03, min(face + s * 0.002, face + s * 0.007), max(face + s * 0.002, face + s * 0.007), z + dz - 0.003, z + dz + 0.003, 1)
    vc=UP_RIDGE_X;vz=Z_RIDGE-.40
    dots.box(vc-.15,vc+.15,UPY1+.002,UPY1+.012,vz-.16,vz+.16,0)
    dots.frame(vc-.18,vc+.18,UPY1+.009,UPY1+.035,vz-.19,vz+.19,.035,mi=1,axis='Y')
    for k in range(7):
        dots.box(vc-.147,vc+.147,UPY1+.015,UPY1+.042,vz-.14+k*.045,vz-.124+k*.045,1)
    dots.build("Ext_VentDots", [L['dot'], L['stucco_pale']], coll='House', smooth=True)
    return ws


def _arch_holes(w, holes):
    """The front door's wall hole is cut up to the arch top (the pointed head is filled by build_entry)."""
    fd = BY_NAME['FrontDoor']
    if w['along'] != 'X' or abs(w['b0']) > 1e-6:
        return holes
    return [(h[0], h[1], h[2], ARCH_TOP) if abs(h[0] - fd['a0']) < 1e-6 and abs(h[2] - fd['z0']) < 1e-6 else h for h in holes]


_ARCH = {}


def _arch_z(x, a0, a1):
    """Four-centred (Tudor) arch head: short-radius shoulders (r 0.2) springing at ARCH_SPRING, then straight haunches
    tangent to the shoulders meeting at a POINTED apex (ARCH_APEX) - photo p00_entry."""
    xc, w = (a0 + a1) / 2, (a1 - a0) / 2
    r1 = 0.2
    key = (round(a0, 4), round(a1, 4))
    if key not in _ARCH:
        cxl = xc - w + r1                                        # left shoulder centre (on the spring line)
        lo, hi = 0.02, math.pi / 2 - 0.02
        for _ in range(60):                                      # theta where the shoulder tangent points at the apex
            th = (lo + hi) / 2
            px, pz = cxl - r1 * math.cos(th), ARCH_SPRING + r1 * math.sin(th)
            tx, tz = math.sin(th), math.cos(th)
            cross = (xc - px) * tz - (ARCH_APEX - pz) * tx
            if cross > 0:
                lo = th
            else:
                hi = th
        th = (lo + hi) / 2
        _ARCH[key] = (cxl, cxl - r1 * math.cos(th), ARCH_SPRING + r1 * math.sin(th))
    cxl, px, pz = _ARCH[key]
    d = xc - abs(x - xc)                                         # mirror onto the left half
    if d <= px:
        return ARCH_SPRING + math.sqrt(max(0.0, r1 * r1 - (d - cxl) ** 2))
    return pz + (ARCH_APEX - pz) * (d - px) / max(1e-9, xc - px)


def _catmull(pts, n=60):
    """Catmull-Rom spline through (x, z) points, n samples."""
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    segs = len(pts) - 1
    for i in range(n + 1):
        t = i / n * segs
        k = min(segs - 1, int(t)); f = t - k
        p0, p1, p2, p3 = P[k], P[k + 1], P[k + 2], P[k + 3]
        x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * f + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * f * f + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * f ** 3)
        z = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * f + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * f * f + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * f ** 3)
        out.append((x, z))
    return out


_RAKE = RAKE if 'RAKE' in globals() else ((-2.85, Z_PAR), (1.2, 2.58))          # plan.RAKE (straight line, photo 00)


def _zr(x):
    """Straight photographed front roof edge, continued beneath the tree canopy."""
    (xa, za), (xb, zb) = _RAKE
    return za + (zb-za)*(x-xa)/(xb-xa)


def _face_y(x):
    """y of the street face carrying the coping: the living block (0) or the tower's proud face (TOWER_Y)."""
    return TOWER_Y if x > -1.25 else 0.0


def _slab_poly(mb, top, th, mi):
    """Prism under a planar polygon (list of (x, y, z_top)): the same polygon th lower + side quads."""
    n = len(top)
    vs = [(x, y, z - th) for (x, y, z) in top] + [tuple(p) for p in top]
    fs = [tuple(reversed(range(n))), tuple(range(n, 2 * n))] + [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    mb._add(vs, fs, mi)


def _wedge_poly(mb, top, z_bot, mi):
    """Prism between a sloped polygon top and a flat bottom at z_bot (soffit closures under eaves)."""
    n = len(top)
    vs = [(x, y, z_bot) for (x, y, z) in top] + [tuple(p) for p in top]
    fs = [tuple(reversed(range(n))), tuple(range(n, 2 * n))] + [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    mb._add(vs, fs, mi)


# Eave collector positions and the photographed terrace outlet (legacy variable name).
SCUPPERS = [('X', -5.2, 17.1), ('Y', 13.5, 5.5), ('Y', 13.0, -5.75), ('X', -5.3, 11.45)]


def _scupper_holes(w):
    out = []
    for (along, a, b0) in SCUPPERS:
        if w['along'] == along and abs(w['b0'] - b0) < 1e-4 and w['a0'] + 0.2 < a < w['a1'] - 0.2 and w['z0'] < Z_UP + 0.5:
            out.append((a - 0.12, a + 0.12, w['z0'] + 0.02, w['z0'] + 0.12))
    return out


def _parapet_cap(cap, along, a0, a1, b0, b1, z1):
    """Precast cap 35 mm proud each side with a drip lip under both edges and hairline joints every 1.2 m."""
    B(cap, along, a0 - 0.035, a1 + 0.035, b0 - 0.035, b1 + 0.035, z1, z1 + 0.06, 0)
    B(cap, along, a0 - 0.035, a1 + 0.035, b0 - 0.035, b0 - 0.023, z1 - 0.015, z1, 0)
    B(cap, along, a0 - 0.035, a1 + 0.035, b1 + 0.023, b1 + 0.035, z1 - 0.015, z1, 0)
    a = a0 + 1.2
    while a < a1 - 0.3:
        B(cap, along, a - 0.0015, a + 0.0015, b0 - 0.036, b1 + 0.036, z1 + 0.0605, z1 + 0.0612, 1)
        B(cap, along, a - 0.0015, a + 0.0015, b0 - 0.0362, b0 - 0.035, z1, z1 + 0.06, 1)
        B(cap, along, a - 0.0015, a + 0.0015, b1 + 0.035, b1 + 0.0362, z1, z1 + 0.06, 1)
        a += 1.2


def _build_base(M, ws):
    """Weep screed band at grade + 0.10, louvred foundation vents every ~3 m, the meter box + conduit (photo 30)."""
    L = _local(M)
    mb = MB()   # 0 screed metal, 1 vent frame (pale stucco), 2 vent slots (dark), 3 galvanised, 4 glass
    zs0, zs1 = Z_GRADE + 0.10, Z_GRADE + 0.16
    for w in ws:
        if w['kind'] != 'ext' or w['z0'] > Z_GRADE + 0.01:
            continue
        if w['kind']=='up' and w['along']=='X' and abs(w['b1']-UPY1)<1e-4:
            continue  # rear gable has one rectangular louver, photos 28/29
        along, a0, a1, b0, b1 = w['along'], w['a0'], w['a1'], w['b0'], w['b1']
        s = outside_sign(w)
        face = b1 if s > 0 else b0
        lo, hi = min(face, face + s * 0.008), max(face, face + s * 0.008)
        B(mb, along, a0 - 0.008, a1 + 0.008, lo, hi, zs0, zs1, 0)
        B(mb, along, a0 - 0.008, a1 + 0.008, min(face, face + s * 0.012), max(face, face + s * 0.012), zs0, zs0 + 0.012, 0)   # drip lip
        # foundation vents: 0.36 x 0.16, clear of floor-level openings (doors) and of the corners
        Lw = a1 - a0
        if Lw < 2.6:
            continue
        low_holes = [(h[0] - 0.5, h[1] + 0.5) for h in holes_for(w) if h[2] < 0.5]
        n = max(1, int(round((Lw - 1.0) / 3.2)))
        for k in range(n):
            ac = a0 + 0.5 + (Lw - 1.0) * ((k + 0.5) / n)
            if any(h0 < ac < h1 for (h0, h1) in low_holes):
                continue
            zv0, zv1 = Z_GRADE + 0.20, Z_GRADE + 0.36
            B(mb, along, ac - 0.18, ac + 0.18, min(face, face + s * 0.006), max(face, face + s * 0.006), zv0, zv1, 1)
            for j in range(5):
                zz = zv0 + 0.02 + j * 0.03
                B(mb, along, ac - 0.155, ac + 0.155, min(face + s * 0.006, face + s * 0.008), max(face + s * 0.006, face + s * 0.008), zz, zz + 0.012, 2)
    # meter box on the driveway wall between the trellis and the garden window, conduit up to a weatherhead and down to the grade
    x, y = 5.75, 7.45
    mb.box(x, x + 0.14, y - 0.17, y + 0.17, 1.25, 1.62, 5)
    mb.box(x + 0.14, x + 0.15, y - 0.15, y + 0.15, 1.28, 1.59, 1)
    mb.sphere((x + 0.15, y, 1.44), 0.075, seg=14, rings=8, mi=4)
    mb.cylinder(x + 0.16, y, 1.44 - 0.05, 1.44 + 0.05, 0.075, 0.07, seg=14, mi=3) if False else None
    for (z0, z1) in ((1.62, Z_ROOF1 + 0.55), (Z_GRADE - 0.3, 1.25)):
        mb.cylinder(x + 0.06, y, z0, z1, 0.02, seg=10, mi=3)
    mb.lathe(x + 0.06, y, Z_ROOF1 + 0.55, [(0, 0), (0.02, 0), (0.05, 0.06), (0.06, 0.12), (0.0, 0.14)], seg=10, mi=3)     # weatherhead
    for zz in (0.3, 1.9, 2.8):
        mb.box(x, x + 0.09, y - 0.03, y + 0.03, zz - 0.012, zz + 0.012, 3)                                         # pipe straps
    mb.build("Ext_Base", [L['screed'], L['stucco_pale'], L['dot'], L['galv'], M['glass'], L['meter']], coll='House', smooth=True)


# ---------------------------------------------------------------- window / door units
# material slots of the units meshes
WIN = dict(trim=0, glass=1, frost=2, steel=3, lead=4, lglass=5, screen=6, brass=7)   # Ext_Windows
DOR = dict(trim=0, glass=1, brass=2, steel=3)                             # Ext_Doors


def _wall_of(o, ws):
    for w in ws:
        if w['along'] == o['along'] and w['b0'] - 1e-4 <= o['b'] <= w['b1'] + 1e-4 and o['a0'] < w['a1'] and o['a1'] > w['a0'] \
           and o['z0'] < w['z1'] and o['z1'] > w['z0']:
            return w
    return None


def _sash(mb, along, a0, a1, bc, z0, z1, grid, mi_f, mi_g, stile=0.045, rail=0.045, t=0.035, mesh=True):
    """One sash in the plane b = bc: stiles / rails, a glass pane, cols x rows muntins."""
    hb0, hb1 = bc - t / 2, bc + t / 2
    B(mb, along, a0, a0 + stile, hb0, hb1, z0, z1, mi_f)
    B(mb, along, a1 - stile, a1, hb0, hb1, z0, z1, mi_f)
    B(mb, along, a0 + stile, a1 - stile, hb0, hb1, z0, z0 + rail, mi_f)
    B(mb, along, a0 + stile, a1 - stile, hb0, hb1, z1 - rail, z1, mi_f)
    ga0, ga1, gz0, gz1 = a0 + stile, a1 - stile, z0 + rail, z1 - rail
    B(mb, along, ga0, ga1, bc - T / 2, bc + T / 2, gz0, gz1, mi_g)
    cols, rows = grid
    for i in range(1, cols):
        a = ga0 + (ga1 - ga0) * i / cols
        B(mb, along, a - 0.01, a + 0.01, bc - 0.012, bc + 0.012, gz0, gz1, mi_f)
    for j in range(1, rows):
        z = gz0 + (gz1 - gz0) * j / rows
        B(mb, along, ga0, ga1, bc - 0.012, bc + 0.012, z - 0.01, z + 0.01, mi_f)


def _casing(mb, along, a0, a1, b_face, s, z0, z1, mi, w=0.09, proud=0.025, sill=True):
    """Flat casing board around a hole on the face b_face (s = direction the board projects)."""
    bb0, bb1 = (b_face, b_face + s * proud) if s > 0 else (b_face + s * proud, b_face)
    if along == 'X':
        mb.frame(a0 - w, a1 + w, bb0, bb1, z0 - (0.02 if sill else w), z1 + w, w, mi=mi, axis='Y')
    else:
        mb.frame(bb0, bb1, a0 - w, a1 + w, z0 - (0.02 if sill else w), z1 + w, w, mi=mi, axis='X')


def _stop(mb, along, a0, a1, bA, bB, z0, z1, mi, w=0.014):
    """Door stop: a thin strip around the jambs and head that the closed leaf shuts against."""
    lo, hi = sorted((bA, bB))
    B(mb, along, a0, a0 + w, lo, hi, z0, z1, mi)
    B(mb, along, a1 - w, a1, lo, hi, z0, z1, mi)
    B(mb, along, a0 + w, a1 - w, lo, hi, z1 - w, z1, mi)


def _frame(mb, along, a0, a1, b0, b1, z0, z1, mi, jamb=0.04, head=0.04, sill=0.05):
    """Frame lining the hole through the full wall depth."""
    B(mb, along, a0, a0 + jamb, b0, b1, z0, z1, mi)
    B(mb, along, a1 - jamb, a1, b0, b1, z0, z1, mi)
    B(mb, along, a0 + jamb, a1 - jamb, b0, b1, z1 - head, z1, mi)
    if sill > 0:
        B(mb, along, a0 + jamb, a1 - jamb, b0, b1, z0, z0 + sill, mi)
    return a0 + jamb, a1 - jamb, z0 + sill, z1 - head


def _ext_trim(mb, along, a0, a1, bo, s, z0, z1, w=0.09, proud=0.03, sill=True):
    """Outside: flat casing with a drip cap over the head, a sloped 90 mm sill with a drip lip under its nose."""
    _casing(mb, along, a0, a1, bo, s, z0, z1, WIN['trim'], w=w, proud=proud, sill=sill)
    cb0, cb1 = min(bo, bo + s * (proud + 0.02)), max(bo, bo + s * (proud + 0.02))
    B(mb, along, a0 - w - 0.02, a1 + w + 0.02, cb0, cb1, z1 + w, z1 + w + 0.03, WIN['trim'])                       # head cap
    B(mb, along, a0 - w - 0.02, a1 + w + 0.02, min(bo + s * (proud + 0.01), bo + s * (proud + 0.02)), max(bo + s * (proud + 0.01), bo + s * (proud + 0.02)),
      z1 + w - 0.012, z1 + w, WIN['trim'])                                                                          # its drip
    if sill:
        sa0, sa1 = a0 - 0.11, a1 + 0.11
        bn = bo + s * 0.09
        _hexa_ab(mb, along, [(sa0, bo, z0 - 0.05), (sa1, bo, z0 - 0.05), (sa1, bn, z0 - 0.05), (sa0, bn, z0 - 0.05)],
                 [(sa0, bo, z0 + 0.0), (sa1, bo, z0 + 0.0), (sa1, bn, z0 - 0.012), (sa0, bn, z0 - 0.012)], WIN['trim'])    # sloped sill
        B(mb, along, sa0, sa1, min(bn - s * 0.015, bn), max(bn - s * 0.015, bn), z0 - 0.065, z0 - 0.05, WIN['trim'])      # drip lip


def _int_trim(mb, along, a0, a1, bi, s, z0, z1, w=0.07, sill=True):
    """Inside: casing, stool + apron (s = the outside direction; the boards project toward -s)."""
    _casing(mb, along, a0, a1, bi, -s, z0, z1, WIN['trim'], w=w, proud=0.018, sill=sill)
    if sill:
        B(mb, along, a0 - 0.09, a1 + 0.09, min(bi, bi - s * 0.05), max(bi, bi - s * 0.05), z0, z0 + 0.025, WIN['trim'])   # stool
        B(mb, along, a0 - 0.07, a1 + 0.07, min(bi, bi - s * 0.018), max(bi, bi - s * 0.018), z0 - 0.09, z0, WIN['trim'])  # apron


def _screen(mb, along, a0, a1, bc, z0, z1):
    """Insect screen: white 30 mm frame + a dark 45 % transparent mesh, in the plane bc."""
    fw = 0.03
    lo, hi = bc - 0.008, bc + 0.008
    B(mb, along, a0, a0 + fw, lo, hi, z0, z1, WIN['trim'])
    B(mb, along, a1 - fw, a1, lo, hi, z0, z1, WIN['trim'])
    B(mb, along, a0 + fw, a1 - fw, lo, hi, z0, z0 + fw, WIN['trim'])
    B(mb, along, a0 + fw, a1 - fw, lo, hi, z1 - fw, z1, WIN['trim'])
    B(mb, along, a0 + fw, a1 - fw, bc - 0.0008, bc + 0.0008, z0 + fw, z1 - fw, WIN['screen'])


def unit_dh(mb, along, a0, a1, b0, b1, z0, z1, s, grid, casing=True, frost=False, kind='dh', screen=False, lower_grid=(1,1)):
    """Double-hung sash window in the hole (a0..a1, z0..z1) of a wall b0..b1 whose outside is toward s: frame lining
    the reveal, two sashes in the inner half of the wall, meeting rail with a brass cam lock, sash lifts, optional
    exterior insect screen over the lower sash, casings / drip cap / sloped sill outside, stool + apron inside."""
    mi_g = WIN['frost'] if frost else WIN['glass']
    ia0, ia1, iz0, iz1 = _frame(mb, along, a0, a1, b0, b1, z0, z1, WIN['trim'])
    bo = b1 if s > 0 else b0                       # outer face
    bi = b0 if s > 0 else b1                       # inner face
    if kind == 'fixed':
        _sash(mb, along, ia0, ia1, bo - s * 0.11, iz0, iz1, grid, WIN['trim'], mi_g)
    else:
        zm = (iz0 + iz1) / 2
        _sash(mb, along, ia0, ia1, bo - s * 0.10, zm - 0.015, iz1, grid, WIN['trim'], mi_g)           # upper sash (outer)
        _sash(mb, along, ia0, ia1, bo - s * 0.15, iz0, zm + 0.02, lower_grid, WIN['trim'], mi_g)            # lower sash (inner)
        B(mb, along, ia0, ia1, bo - s * 0.165, bo - s * 0.085, zm - 0.015, zm + 0.02, WIN['trim'])       # meeting rail
        ac = (ia0 + ia1) / 2
        rb0, rb1 = min(bo - s * 0.165, bo - s * 0.12), max(bo - s * 0.165, bo - s * 0.12)
        B(mb, along, ac - 0.025, ac + 0.025, rb0, rb1, zm + 0.02, zm + 0.031, WIN['brass'])              # cam lock base
        cx_, cy_ = _ab(along, ac, bo - s * 0.14)
        mb.cylinder(cx_, cy_, zm + 0.031, zm + 0.045, 0.014, seg=10, mi=WIN['brass'])
        B(mb, along, ac - 0.004, ac + 0.03, min(bo - s * 0.14, bo - s * 0.17), max(bo - s * 0.14, bo - s * 0.17), zm + 0.045, zm + 0.052, WIN['brass'])   # cam lever
        for aa in (ia0 + 0.12, ia1 - 0.12):                                                              # sash lifts
            B(mb, along, aa - 0.02, aa + 0.02, min(bo - s * 0.1675, bo - s * 0.185), max(bo - s * 0.1675, bo - s * 0.185), iz0 + 0.02, iz0 + 0.03, WIN['brass'])
            B(mb, along, aa - 0.02, aa + 0.02, min(bo - s * 0.18, bo - s * 0.185), max(bo - s * 0.18, bo - s * 0.185), iz0 + 0.03, iz0 + 0.045, WIN['brass'])
        if screen:
            _screen(mb, along, ia0 + 0.004, ia1 - 0.004, bo - s * 0.05, iz0 + 0.004, zm + 0.02)
    if casing:
        _ext_trim(mb, along, a0, a1, bo, s, z0, z1)
        _int_trim(mb, along, a0, a1, bi, s, z0, z1)


def _shutters(mb, along, a0, a1, bo, s, z0, z1, w, casing=0.09):
    """Board-and-batten shutters on the wall face either side of the exterior casing: boards with 4 mm gaps,
    two battens, 30 mm thick, a little taller than the casing (photo 00 / p00_living)."""
    zz0, zz1 = z0 - 0.05, z1 + casing + 0.02
    nb = max(2, int(round(w / 0.105)))
    bw = (w - 0.004 * (nb - 1)) / nb
    lo, hi = min(bo, bo + s * 0.03), max(bo, bo + s * 0.03)
    for (sa0, sa1) in ((a0 - casing - 0.03 - w, a0 - casing - 0.03), (a1 + casing + 0.03, a1 + casing + 0.03 + w)):
        for i in range(nb):
            ba0 = sa0 + i * (bw + 0.004)
            B(mb, along, ba0, ba0 + bw, lo, hi, zz0, zz1, WIN['trim'])
        for zb in (zz0 + (zz1 - zz0) * 0.2, zz1 - (zz1 - zz0) * 0.2 - 0.09):
            B(mb, along, sa0, sa1, min(bo + s * 0.03, bo + s * 0.05), max(bo + s * 0.03, bo + s * 0.05), zb, zb + 0.09, WIN['trim'])
        for zh in (zz0 + 0.15, zz1 - 0.15):                                          # strap hinges to the wall
            B(mb, along, sa0 - 0.02 if sa0 < a0 else sa1, sa0 if sa0 < a0 else sa1 + 0.02, min(bo + s * 0.005, bo + s * 0.03), max(bo + s * 0.005, bo + s * 0.03), zh - 0.012, zh + 0.012, WIN['steel'])


def _fixed_centre(mb, along, a0, a1, b0, b1, z0, z1, s, transom=0.0, lites=6):
    """Wide fixed pane in the inner half of the wall, optional transom row of `lites` small panes at the top."""
    ia0, ia1, iz0, iz1 = _frame(mb, along, a0, a1, b0, b1, z0, z1, WIN['trim'])
    bo = b1 if s > 0 else b0
    bc = bo - s * 0.11
    if transom > 0:
        zt = iz1 - transom
        _sash(mb, along, ia0, ia1, bc, zt - 0.02, iz1, (lites, 1), WIN['trim'], WIN['glass'], stile=0.045, rail=0.04)
        _sash(mb, along, ia0, ia1, bc, iz0, zt + 0.02, (1, 1), WIN['trim'], WIN['glass'], stile=0.045, rail=0.05)
    else:
        _sash(mb, along, ia0, ia1, bc, iz0, iz1, (1, 1), WIN['trim'], WIN['glass'], stile=0.05, rail=0.06)


def unit_dh3(mb, along, a0, a1, b0, b1, z0, z1, s, grid, mullions, screen=False, fixed_centre=None):
    bounds = [a0] + list(mullions) + [a1]
    nsec = len(bounds) - 1
    for i in range(nsec):
        ua0 = bounds[i] + (0.04 if i > 0 else 0.0)
        ua1 = bounds[i + 1] - (0.04 if i < nsec - 1 else 0.0)
        if fixed_centre is not None and nsec == 3 and i == 1:
            _fixed_centre(mb, along, ua0, ua1, b0, b1, z0, z1, s, fixed_centre.get('transom', 0.0), fixed_centre.get('lites', 6))
            continue
        unit_dh(mb, along, ua0, ua1, b0, b1, z0, z1, s, grid, casing=False, screen=(screen and i % 2 == 0))
    for m in mullions:
        B(mb, along, m - 0.04, m + 0.04, b0, b1, z0, z1, WIN['trim'])
    bo = b1 if s > 0 else b0
    bi = b0 if s > 0 else b1
    _ext_trim(mb, along, a0, a1, bo, s, z0, z1)
    _int_trim(mb, along, a0, a1, bi, s, z0, z1)


def _lattice(mb, along, a0, a1, bc, z0, z1, pitch=0.14, r=0.005, mi=0):
    """Diamond lead cames in the rectangle a0..a1 x z0..z1 at plane bc."""
    def clip_line(sign):
        # lines a - sign*z = c   ->  z = sign*(a - c)
        cs = []
        cmin = min(a0 - sign * z0, a0 - sign * z1, a1 - sign * z0, a1 - sign * z1)
        cmax = max(a0 - sign * z0, a0 - sign * z1, a1 - sign * z0, a1 - sign * z1)
        c = cmin + pitch * math.sqrt(2) / 2
        while c < cmax:
            cs.append(c)
            c += pitch * math.sqrt(2)
        for c in cs:
            pts = []
            for a in (a0, a1):
                z = sign * (a - c)
                if z0 <= z <= z1:
                    pts.append((a, z))
            for z in (z0, z1):
                a = c + sign * z
                if a0 < a < a1:
                    pts.append((a, z))
            if len(pts) >= 2:
                (pa, pz), (qa, qz) = pts[0], pts[-1]
                p0 = _ab(along, pa, bc); p1 = _ab(along, qa, bc)
                tube(mb, (p0[0], p0[1], pz), (p1[0], p1[1], qz), r, seg=4, mi=mi)
    clip_line(1.0)
    clip_line(-1.0)


def unit_leaded(mb, along, a0, a1, b0, b1, z0, z1, s):
    ia0, ia1, iz0, iz1 = _frame(mb, along, a0, a1, b0, b1, z0, z1, WIN['trim'])
    bo = b1 if s > 0 else b0
    bi = b0 if s > 0 else b1
    bc = bo - s * 0.10
    _sash(mb, along, ia0, ia1, bc, iz0, iz1, (1, 1), WIN['trim'], WIN['lglass'])
    _lattice(mb, along, ia0 + 0.045, ia1 - 0.045, bc, iz0 + 0.045, iz1 - 0.045, mi=WIN['lead'])
    _ext_trim(mb, along, a0, a1, bo, s, z0, z1, w=0.08)
    _int_trim(mb, along, a0, a1, bi, s, z0, z1)


def unit_garden(mb, along, a0, a1, b0, b1, z0, z1, s, depth):
    """Greenhouse window: white frame box projecting `depth` outside, glass front / sides / sloped top, 2 shelves."""
    bo = b1 if s > 0 else b0
    bi = b0 if s > 0 else b1
    bf = bo + s * depth                                   # front plane
    lo, hi = (bo, bf) if s > 0 else (bf, bo)
    f = 0.04
    # frame: sill plate, corner posts, head bar, front rails
    B(mb, along, a0 - 0.05, a1 + 0.05, lo - 0.02, hi + 0.02, z0 - 0.04, z0 + 0.03, WIN['trim'])        # sill / floor
    for a in (a0, a1 - f):
        B(mb, along, a, a + f, min(bf, bf - s * f), max(bf, bf - s * f), z0, z1 - 0.15, WIN['trim'])  # front posts
        B(mb, along, a, a + f, lo, hi, z0, z0 + f, WIN['trim'])
    B(mb, along, a0, a1, min(bf, bf - s * f), max(bf, bf - s * f), z1 - 0.19, z1 - 0.15, WIN['trim'])     # front head rail
    B(mb, along, a0, a1, min(bf, bf - s * f), max(bf, bf - s * f), z0, z0 + f, WIN['trim'])
    B(mb, along, a0, a1, min(bo, bo + s * f), max(bo, bo + s * f), z1 + 0.06, z1 + 0.10, WIN['trim'])     # wall head rail
    # glass: front, sides, sloped top (from the wall at z1+0.08 to the front at z1-0.17)
    B(mb, along, a0 + f, a1 - f, bf - T / 2, bf + T / 2, z0 + f, z1 - 0.19, WIN['glass'])
    for a in (a0 + f / 2, a1 - f / 2):
        B(mb, along, a - T / 2, a + T / 2, lo + f, hi - f, z0 + f, z1 - 0.15, WIN['glass'])
    top = [(a0, bo, z1 + 0.08), (a1, bo, z1 + 0.08), (a1, bf, z1 - 0.17), (a0, bf, z1 - 0.17)]
    _hexa_ab(mb, along, [(a, b, z) for (a, b, z) in top], [(a, b, z + T) for (a, b, z) in top], WIN['glass'])
    for zz in (z0 + 0.42, z0 + 0.82):                                                                    # glass shelves
        B(mb, along, a0 + f, a1 - f, lo + f, hi - f, zz, zz + 0.008, WIN['glass'])
    for a in (a0 - 0.012, a1 + 0.012):                                                                   # screens over the side lights
        aa0, aa1 = min(a, a + (0.016 if a < a0 else -0.016)), max(a, a + (0.016 if a < a0 else -0.016))
        B(mb, along, aa0, aa1, lo + f + 0.02, hi - f - 0.02, z0 + f + 0.02, z1 - 0.17, WIN['screen'])
        B(mb, along, aa0 - 0.004, aa1 + 0.004, lo + f, lo + f + 0.02, z0 + f, z1 - 0.15, WIN['trim'])
        B(mb, along, aa0 - 0.004, aa1 + 0.004, hi - f - 0.02, hi - f, z0 + f, z1 - 0.15, WIN['trim'])
        B(mb, along, aa0 - 0.004, aa1 + 0.004, lo + f, hi - f, z1 - 0.17, z1 - 0.15, WIN['trim'])
    B(mb, along, a0 - 0.06, a1 + 0.06, min(bo, bo + s * (depth + 0.04)), max(bo, bo + s * (depth + 0.04)), z1 + 0.10, z1 + 0.13, WIN['trim'])   # cap over the head
    # hole lining + inside casing
    _frame(mb, along, a0, a1, b0, b1, z0, z1, WIN['trim'], sill=0.0)
    _casing(mb, along, a0, a1, bi, -s, z0, z1, WIN['trim'], w=0.07, proud=0.018)
    B(mb, along, a0 - 0.05, a1 + 0.05, min(bo, bo + s * 0.06), max(bo, bo + s * 0.06), z0 - 0.09, z0 - 0.04, WIN['steel'])   # metal drip


def _leaf_map(along, a_h, b_h, s_in, theta, sign_a):
    """(u, v, z) -> world (x, y, z) for a leaf hinged at (a_h, b_h): u along the leaf (0 at the hinge, toward
    sign_a * a when closed), v across its thickness (toward +b when closed), rotated theta (rad) so the free end
    swings toward s_in * b."""
    c, sn = math.cos(theta), math.sin(theta)
    da, db = sign_a * c, s_in * sn
    na, nb = -s_in * sn * sign_a * sign_a, c            # rotated (0, 1)
    na = -s_in * sn * sign_a
    def f(u, v, z):
        a = a_h + u * da + v * na
        b = b_h + u * db + v * nb
        x, y = _ab(along, a, b)
        return (x, y, z)
    return f


def lbox(mb, f, u0, u1, v0, v1, z0, z1, mi):
    mb.hexa([f(u0, v0, z0), f(u1, v0, z0), f(u1, v1, z0), f(u0, v1, z0),
             f(u0, v0, z1), f(u1, v0, z1), f(u1, v1, z1), f(u0, v1, z1)], mi)


def _raised_panel(mb, f, u0, u1, z0, z1, t, mi):
    """Raised panel on both faces of a leaf: a 5 mm proud frame round a field (reads as a real panel door)."""
    for sv in (-1, 1):
        v0, v1 = (t / 2, t / 2 + 0.006) if sv > 0 else (-t / 2 - 0.006, -t / 2)
        for (uu0, uu1, zz0, zz1) in ((u0, u1, z0, z0 + 0.04), (u0, u1, z1 - 0.04, z1), (u0, u0 + 0.04, z0, z1), (u1 - 0.04, u1, z0, z1)):
            lbox(mb, f, uu0, uu1, v0, v1, zz0, zz1, mi)
        vv0, vv1 = (t / 2, t / 2 + 0.003) if sv > 0 else (-t / 2 - 0.003, -t / 2)
        lbox(mb, f, u0 + 0.06, u1 - 0.06, vv0, vv1, z0 + 0.06, z1 - 0.06, mi)                 # the raised field


def _hinges(mb, f, z0, z1, t, side, mi, n=3):
    """Three butt hinges on the hinge edge (u = 0): a barrel + leaf plate on the face the door swings toward."""
    v = side * (t / 2 + 0.006)
    zs = [z0 + 0.25, (z0 + z1) / 2, z1 - 0.25] if n == 3 else [z0 + 0.25, z1 - 0.25]
    for z in zs:
        p0 = f(0.0, v, z - 0.05); p1 = f(0.0, v, z + 0.05)
        mb.tube(p0, p1, 0.008, 0.008, seg=8, mi=mi)
        lbox(mb, f, 0.0, 0.032, v - 0.0015, v + 0.0015, z - 0.05, z + 0.05, mi)


def _knob(mb, f, L, z0, t, mi, lever=False, u_off=0.07):
    """Rose + spindle + knob (or a lever pointing back toward the hinge) on both faces near the free edge."""
    for sv in (-1, 1):
        p = f(L - u_off, sv * (t / 2), z0 + 1.0)
        q = f(L - u_off, sv * (t / 2 + 0.01), z0 + 1.0)
        mb.tube(p, q, 0.03, 0.03, seg=14, mi=mi)                                             # rose
        r = f(L - u_off, sv * (t / 2 + 0.065), z0 + 1.0)
        mb.tube(q, r, 0.011, 0.011, seg=8, mi=mi)                                            # spindle / neck
        if lever:
            e = f(L - u_off - 0.12, sv * (t / 2 + 0.065), z0 + 1.0)
            mb.tube(r, e, 0.009, 0.007, seg=8, mi=mi)
            mb.sphere(e, 0.009, seg=8, rings=5, mi=mi)
        else:
            mb.sphere(r, 0.028, seg=32, rings=16, mi=mi, squash=0.8)


def _deadbolt(mb, f, L, z0, t, mi, u_off=0.07):
    for sv in (-1, 1):
        p = f(L - u_off, sv * (t / 2), z0 + 1.16)
        q = f(L - u_off, sv * (t / 2 + 0.012), z0 + 1.16)
        mb.tube(p, q, 0.027, 0.027, seg=14, mi=mi)
    lbox(mb, f, L - u_off - 0.004, L - u_off + 0.004, t / 2 + 0.012, t / 2 + 0.024, z0 + 1.14, z0 + 1.18, mi)   # thumb-turn (room side)


def _panel_leaf(mb, f, L, z0, z1, mi_f, mi_g=None, lites=None, t=0.045, stile=0.09, kick=0.2, top=0.09, glass_from=None, style='panel', mi_knob=None, lever=False):
    """Door leaf in the leaf frame f (u 0..L from the hinge, v -t/2..t/2, z0..z1)."""
    if style == 'panel':
        lbox(mb, f, 0, L, -t / 2, t / 2, z0, z1, mi_f)
        for (pz0, pz1) in ((z0 + 0.15, z0 + 0.95), (z0 + 1.1, z1 - 0.15)):                    # two raised panels, both faces
            _raised_panel(mb, f, 0.1, L - 0.1, pz0, pz1, t, mi_f)
    elif style in ('french', 'glazed'):
        # cut the glazed area: rebuild as stiles / rails + glass + muntins (the slab is the kick + rails)
        gz0 = z0 + (kick if style == 'french' else glass_from)
        gz1 = z1 - top
        gu0, gu1 = stile, L - stile
        lbox(mb, f, gu0, gu1, -T / 2, T / 2, gz0, gz1, mi_g)
        cols, rows = lites
        for i in range(1, cols):
            u = gu0 + (gu1 - gu0) * i / cols
            lbox(mb, f, u - 0.01, u + 0.01, -0.015, 0.015, gz0, gz1, mi_f)
        for j in range(1, rows):
            z = gz0 + (gz1 - gz0) * j / rows
            lbox(mb, f, gu0, gu1, -0.015, 0.015, z - 0.01, z + 0.01, mi_f)
        # glazing beads round the pane on both faces
        for sv in (-1, 1):
            v0, v1 = (0.012, 0.018) if sv > 0 else (-0.018, -0.012)
            for (uu0, uu1, zz0, zz1) in ((gu0 - 0.012, gu1 + 0.012, gz0 - 0.012, gz0), (gu0 - 0.012, gu1 + 0.012, gz1, gz1 + 0.012),
                                         (gu0 - 0.012, gu0, gz0, gz1), (gu1, gu1 + 0.012, gz0, gz1)):
                lbox(mb, f, uu0, uu1, v0, v1, zz0, zz1, mi_f)
        if style == 'glazed':
            _raised_panel(mb, f, 0.1, L - 0.1, z0 + 0.15, gz0 - 0.12, t, mi_f)                # the lower panel of the side door
    if mi_knob is not None:
        _knob(mb, f, L, z0, t, mi_knob, lever=lever)


def _glazed_slab(mb, f, L, z0, z1, gz0, gz1, stile, t, mi_f):
    """Leaf slab with a rectangular hole (for glazed leaves): four boxes around the glass."""
    lbox(mb, f, 0, L, -t / 2, t / 2, z0, gz0, mi_f)
    lbox(mb, f, 0, L, -t / 2, t / 2, gz1, z1, mi_f)
    lbox(mb, f, 0, stile, -t / 2, t / 2, gz0, gz1, mi_f)
    lbox(mb, f, L - stile, L, -t / 2, t / 2, gz0, gz1, mi_f)


def unit_door(mb, o, w, ws):
    """Interior / side door: frame + casings both sides + a hinged leaf (open angle into the room it serves)."""
    along, b0, b1 = w['along'], w['b0'], w['b1']
    a0, a1, z0, z1 = o['a0'], o['a1'], o['z0'], o['z1']
    if o['name'] == 'DoorBed2':
        a0, a1 = DOOR_BED2
    hinge = DOOR_HINGE.get(o['name'], o.get('hinge', 'a0'))
    ext = o.get('ext', False)
    if ext:
        s_out = outside_sign(w)
        s_in = -s_out
    else:
        s_in = ROOM_SIDE[o['name']]
    mi_f = DOR['trim']
    ia0, ia1, iz0, iz1 = _frame(mb, along, a0, a1, b0, b1, z0, z1, mi_f, jamb=0.03, head=0.03, sill=0.0)
    for sgn in (-1, 1):
        face = b1 if sgn > 0 else b0
        _casing(mb, along, a0, a1, face, sgn, z0, z1, mi_f, w=0.07, proud=0.018, sill=False)
    # stop: the leaf closes against it (on the non-room side of the leaf plane)
    b_face_in = b0 if s_in < 0 else b1                       # the room-side face
    b_leaf = b_face_in - s_in * 0.05                         # leaf centre plane (5 cm into the wall from the room face)
    _stop(mb, along, ia0, ia1, b_leaf - s_in * 0.0225, b_leaf - s_in * 0.04, iz0, iz1, mi_f)
    L = ia1 - ia0 - 0.006
    theta = math.radians(o.get('open', 0.0))
    if hinge == 'a0':
        f = _leaf_map(along, ia0 + 0.003, b_leaf, s_in, theta, +1)
    else:
        f = _leaf_map(along, ia1 - 0.003, b_leaf, s_in, theta, -1)
    if o.get('style') == 'glazed':
        _glazed_slab(mb, f, L, iz0, iz1 - 0.003, iz0 + 0.95, iz1 - 0.12, 0.09, 0.045, mi_f)
        _panel_leaf(mb, f, L, iz0, iz1 - 0.003, mi_f, DOR['glass'], lites=(1, 1), style='glazed', glass_from=0.95, top=0.12, mi_knob=DOR['brass'])
    else:
        _panel_leaf(mb, f, L, iz0, iz1 - 0.003, mi_f, style='panel', mi_knob=DOR['brass'])
    _hinges(mb, f, iz0, iz1, 0.045, +1 if s_in > 0 else -1, DOR['brass'])
    if ext:
        B(mb, along, ia0, ia1, b0, b1, z0, z0 + 0.025, DOR['steel'])                                     # threshold
        lbox(mb, f, 0.02, L - 0.02, -0.045 / 2 - 0.006, -0.045 / 2, iz0 + 0.002, iz0 + 0.035, DOR['steel'])  # door sweep (outside face)
        _deadbolt(mb, f, L, iz0, 0.045, DOR['brass'])


def unit_french(mb, o, w):
    along, b0, b1 = w['along'], w['b0'], w['b1']
    a0, a1, z0, z1 = o['a0'], o['a1'], o['z0'], o['z1']
    s_out = outside_sign(w)
    s_in = -s_out
    mi_f = DOR['trim']
    ia0, ia1, iz0, iz1 = _frame(mb, along, a0, a1, b0, b1, z0, z1, mi_f, jamb=0.045, head=0.045, sill=0.0)
    bo = b1 if s_out > 0 else b0
    bi = b0 if s_out > 0 else b1
    _casing(mb, along, a0, a1, bo, s_out, z0, z1, mi_f, w=0.09, proud=0.03, sill=False)
    _casing(mb, along, a0, a1, bi, s_in, z0, z1, mi_f, w=0.07, proud=0.018, sill=False)
    B(mb, along, ia0, ia1, b0, b1, z0, z0 + 0.03, DOR['steel'])                    # threshold
    b_leaf = bi - s_in * 0.06
    _stop(mb, along, ia0, ia1, b_leaf - s_in * 0.0225, b_leaf - s_in * 0.045, iz0 + 0.03, iz1, mi_f)
    ang0, ang1 = FRENCH_OPEN.get(o['name'], (o.get('open', 0.0), o.get('open', 0.0)))
    L = (ia1 - ia0) / 2 - 0.006
    cols, rows = o.get('lites', (2, 5))
    for (hinge_a, sign_a, ang) in ((ia0 + 0.003, +1, ang0), (ia1 - 0.003, -1, ang1)):
        f = _leaf_map(along, hinge_a, b_leaf, s_in, math.radians(ang), sign_a)
        kick = 0.2
        _glazed_slab(mb, f, L, iz0 + 0.03, iz1 - 0.003, iz0 + 0.03 + kick, iz1 - 0.003 - 0.09, 0.09, 0.045, mi_f)
        _panel_leaf(mb, f, L, iz0 + 0.03, iz1 - 0.003, mi_f, DOR['glass'], lites=(cols, rows), style='french', kick=kick, top=0.09, mi_knob=DOR['brass'], lever=True)
        _hinges(mb, f, iz0 + 0.03, iz1 - 0.003, 0.045, +1 if s_in > 0 else -1, DOR['brass'])
        _raised_panel(mb, f, 0.1, L - 0.1, iz0 + 0.06, iz0 + 0.03 + kick - 0.03, 0.045, mi_f) if kick > 0.18 else None
        if sign_a < 0:                                                                                  # astragal on the a1 leaf, outside face
            lbox(mb, f, L - 0.012, L + 0.022, -0.045 / 2 - 0.014, -0.045 / 2, iz0 + 0.03, iz1 - 0.003, mi_f)
        lbox(mb, f, 0.02, L - 0.02, -0.045 / 2 - 0.005, -0.045 / 2, iz0 + 0.032, iz0 + 0.06, DOR['steel'])       # sweeps


def unit_slider(mb, o, w):
    along, b0, b1 = w['along'], w['b0'], w['b1']
    a0, a1, z0, z1 = o['a0'], o['a1'], o['z0'], o['z1']
    s = outside_sign(w)
    bo = b1 if s > 0 else b0
    bi = b0 if s > 0 else b1
    mi_f = DOR['trim']
    ia0, ia1, iz0, iz1 = _frame(mb, along, a0, a1, b0, b1, z0, z1, mi_f, jamb=0.05, head=0.05, sill=0.0)
    B(mb, along, ia0, ia1, bo - s * 0.04, bo - s * 0.16, z0, z0 + 0.035, DOR['steel'])                 # sill track
    for off in (0.07, 0.125):                                                                         # track ribs
        B(mb, along, ia0, ia1, bo - s * (off - 0.004), bo - s * (off + 0.004), z0 + 0.035, z0 + 0.045, DOR['steel'])
        B(mb, along, ia0, ia1, bo - s * (off - 0.004), bo - s * (off + 0.004), iz1 - 0.01, iz1, DOR['steel'])
    _casing(mb, along, a0, a1, bo, s, z0, z1, mi_f, w=0.08, proud=0.03, sill=False)
    _casing(mb, along, a0, a1, bi, -s, z0, z1, mi_f, w=0.07, proud=0.018, sill=False)
    half = (ia1 - ia0) / 2
    pa0, pa1 = ia0, ia0 + half + 0.02
    for (off, mi_g) in ((0.07, DOR['glass']), (0.125, DOR['glass'])):                                  # fixed (outer) + parked slider (inner)
        bc = bo - s * off
        _sash(mb, along, pa0, pa1, bc, z0 + 0.045, iz1 - 0.01, (1, 1), mi_f, mi_g, stile=0.06, rail=0.08, t=0.04)
    hb = bo - s * 0.125
    B(mb, along, pa1 - 0.09, pa1 - 0.06, hb + 0.02 * (-s), hb + 0.05 * (-s), z0 + 0.9, z0 + 1.15, DOR['steel'])   # pull


def unit_sliding_cl(mb, o, w):
    along, b0, b1 = w['along'], w['b0'], w['b1']
    a0, a1, z0, z1 = o['a0'], o['a1'], o['z0'], o['z1']
    s_room = ROOM_SIDE[o['name']]                       # bed3 side
    mi_f = DOR['trim']
    ia0, ia1, iz0, iz1 = _frame(mb, along, a0, a1, b0, b1, z0, z1, mi_f, jamb=0.03, head=0.03, sill=0.0)
    face = b1 if s_room > 0 else b0
    _casing(mb, along, a0, a1, face, s_room, z0, z1, mi_f, w=0.07, proud=0.018, sill=False)
    half = (ia1 - ia0) / 2
    for i, off in enumerate((0.03, 0.075)):
        bc = face - s_room * off
        pa0 = ia0 + i * (half - 0.02)
        pa1 = pa0 + half + 0.02
        lbox_along = None
        B(mb, along, pa0, pa1, bc - 0.018, bc + 0.018, iz0 + 0.01, iz1 - 0.01, mi_f)
        B(mb, along, pa0 + 0.06, pa1 - 0.06, bc - 0.022, bc - 0.018 - 0.0, iz0 + 0.2, iz1 - 0.2, mi_f) if False else None
    B(mb, along, ia0, ia1, face - s_room * 0.11, face - s_room * 0.005, iz1 - 0.05, iz1, mi_f)        # track fascia


def unit_arch(mb, o, w):
    """Curved head infill above the spring line (a plastered elliptical arch)."""
    along, b0, b1 = w['along'], w['b0'], w['b1']
    a0, a1, z1 = o['a0'], o['a1'], o['z1']
    zs = o.get('spring', 1.6)
    c, half = (a0 + a1) / 2, (a1 - a0) / 2
    n = 14
    def zc(a):
        t = max(-1.0, min(1.0, (a - c) / half))
        return zs + (z1 - zs) * math.sqrt(max(0.0, 1 - t * t))
    for side in (-1, 1):
        for k in range(n):
            t0 = k / n; t1 = (k + 1) / n
            aa0 = c + side * half * t0
            aa1 = c + side * half * t1
            lo, hi = sorted((aa0, aa1))
            bot = [(lo, b0, zc(lo)), (hi, b0, zc(hi)), (hi, b1, zc(hi)), (lo, b1, zc(lo))]
            top = [(lo, b0, z1), (hi, b0, z1), (hi, b1, z1), (lo, b1, z1)]
            _hexa_ab(mb, along, bot, top, 0)


def unit_cased(mb, o, w):
    along, b0, b1 = w['along'], w['b0'], w['b1']
    a0, a1, z0, z1 = o['a0'], o['a1'], o['z0'], o['z1']
    _frame(mb, along, a0, a1, b0, b1, z0, z1, DOR['trim'], jamb=0.03, head=0.03, sill=0.0)
    for sgn in (-1, 1):
        face = b1 if sgn > 0 else b0
        _casing(mb, along, a0, a1, face, sgn, z0, z1, DOR['trim'], w=0.07, proud=0.018, sill=False)


# which side of its wall each interior door's room is on (+1 -> +b)
# windows that carry an exterior insect screen over the lower sash (side / rear windows the film never looks out of)
SCREENED = {'LivW1', 'BedAW', 'BedBW1', 'BedBW3', 'LauW', 'PrimWE2', 'FamWE', 'Bed3WW', 'DinWE'}

ROOM_SIDE = {
    'DoorLau': +1, 'DoorBedA': -1, 'DoorHalf': -1, 'DoorBathA': -1, 'DoorBedB': -1,
    'DoorPrim': +1, 'DoorBed2': -1, 'DoorBed3': +1, 'DoorHBath': +1, 'DoorPBath': +1, 'DoorWic': -1, 'DoorWic2': -1,
    'DoorCl3': -1,
}


def build_entry_door(M):
    """The plum front door leaf as its own object (film.open_doors swings it about plan.ENTRY_HINGE, inward +Y):
    a flush slab with a small rectangular diamond-leaded lite, a brass drop knocker, lever + rose + deadbolt, kick plate, hinges."""
    L = _local(M)
    o = BY_NAME['FrontDoor']
    mb = MB()      # 0 plum, 1 leaded glass, 2 brass, 3 lead cames
    x0, x1 = o['a0'] + 0.038, o['a1'] - 0.038
    yc = ENTRY_HINGE[1]
    t = 0.045
    z0, z1 = 0.015, o['z1'] - 0.038
    cx = (x0 + x1) / 2
    lx0, lx1, lz0, lz1 = cx - 0.15, cx + 0.15, 1.55, 1.90
    for (bx0, bx1, bz0, bz1) in ((x0, x1, z0, lz0), (x0, x1, lz1, z1), (x0, lx0, lz0, lz1), (lx1, x1, lz0, lz1)):
        mb.box(bx0, bx1, yc - t / 2, yc + t / 2, bz0, bz1, 0)
    mb.box(lx0, lx1, yc - 0.004, yc + 0.004, lz0, lz1, 1)
    _lattice(mb, 'X', lx0 + 0.01, lx1 - 0.01, yc, lz0 + 0.01, lz1 - 0.01, pitch=0.085, r=0.003, mi=3)
    for sv in (-1, 1):                                                                                  # glazing bead round the lite
        y0_, y1_ = (yc + t / 2, yc + t / 2 + 0.006) if sv > 0 else (yc - t / 2 - 0.006, yc - t / 2)
        mb.frame(lx0 - 0.02, lx1 + 0.02, y0_, y1_, lz0 - 0.02, lz1 + 0.02, 0.02, mi=0, axis='Y')
    # brass drop knocker under the lite (outside face), lever handle + rose both faces, deadbolt, kick plate, hinges
    yo = yc - t / 2
    mb.box(cx - 0.02, cx + 0.02, yo - 0.012, yo, 1.40, 1.47, 2)
    mb.box(cx - 0.012, cx + 0.012, yo - 0.03, yo - 0.012, 1.30, 1.42, 2)
    mb.sphere((cx, yo - 0.022, 1.29), 0.016, seg=10, rings=6, mi=2)
    for sv in (-1, 1):
        y = yc + sv * t / 2
        mb.tube((x1 - 0.08, y, 1.0), (x1 - 0.08, y + sv * 0.01, 1.0), 0.032, 0.032, seg=14, mi=2)
        mb.tube((x1 - 0.08, y + sv * 0.01, 1.0), (x1 - 0.08, y + sv * 0.065, 1.0), 0.011, 0.011, seg=8, mi=2)
        mb.tube((x1 - 0.08, y + sv * 0.065, 1.0), (x1 - 0.21, y + sv * 0.065, 1.0), 0.009, 0.007, seg=8, mi=2)
        mb.tube((x1 - 0.08, y, 1.17), (x1 - 0.08, y + sv * 0.012, 1.17), 0.027, 0.027, seg=14, mi=2)
    mb.box(x1 - 0.085, x1 - 0.075, yc + t / 2 + 0.012, yc + t / 2 + 0.024, 1.15, 1.19, 2)
    mb.box(x0 + 0.03, x1 - 0.03, yo - 0.002, yo, z0 + 0.02, z0 + 0.24, 2)
    for z in (0.3, 1.05, 1.8):
        mb.tube((ENTRY_HINGE[0] + 0.005, yc + t / 2 + 0.006, z - 0.05), (ENTRY_HINGE[0] + 0.005, yc + t / 2 + 0.006, z + 0.05), 0.008, 0.008, seg=8, mi=2)
        mb.box(x0, x0 + 0.032, yc + t / 2, yc + t / 2 + 0.003, z - 0.05, z + 0.05, 2)
    return mb.build("Entry_Door", [L['plum'], L['glass_lead'], M['brass'], L['lead']], coll='House', smooth=False)


def build_units(M, ws):
    L = _local(M)
    win = MB(); dor = MB(); arch = MB()
    for o in OPENINGS:
        w = _wall_of(o, ws)
        if w is None:
            print("[exterior] no wall for opening", o['name'])
            continue
        k = o['kind']
        along, b0, b1 = w['along'], w['b0'], w['b1']
        a0, a1, z0, z1 = o['a0'], o['a1'], o['z0'], o['z1']
        s = outside_sign(w) if w['kind'] in ('ext', 'up', 'par') else 1
        if k == 'hole':
            continue
        scr = o['name'] in SCREENED
        if k == 'dh':
            unit_dh(win, along, a0, a1, b0, b1, z0, z1, s, o['grid'], screen=scr, frost=o.get('frost',False), lower_grid=o.get('lower_grid',(1,1)))
        elif k == 'dh3':
            fc = FIXED_CENTRE.get(o['name'], dict(transom=0.0) if o.get('fixed_centre') else None)
            unit_dh3(win, along, a0, a1, b0, b1, z0, z1, s, o['grid'], o['mullions'], screen=scr, fixed_centre=fc)
        elif k == 'paired':
            # One shared reveal; the former per-pane frames doubled the mullion widths.
            ia0,ia1,iz0,iz1=_frame(win,along,a0,a1,b0,b1,z0,z1,WIN['trim'],jamb=.030,head=.030,sill=.04)
            mid=(ia0+ia1)/2;bo=b1 if s>0 else b0
            for aa,bb in ((ia0,mid-.0175),(mid+.0175,ia1)):
                _sash(win,along,aa,bb,bo-s*.11,iz0,iz1,(1,1),WIN['trim'],WIN['frost'] if o.get('frost') else WIN['glass'],stile=.0225,rail=.028)
            B(win,along,mid-.0175,mid+.0175,b0,b1,iz0,iz1,WIN['trim'])
            _ext_trim(win,along,a0,a1,bo,s,z0,z1)
            _int_trim(win,along,a0,a1,b0 if s>0 else b1,s,z0,z1)
        elif k in ('fixed','fixed_lites'):
            unit_dh(win, along, a0, a1, b0, b1, z0, z1, s, o.get('grid',(1,1)), frost=o.get('frost', False), kind='fixed')
        elif k == 'leaded':
            unit_leaded(win, along, a0, a1, b0, b1, z0, z1, s)
        elif k == 'garden':
            unit_garden(win, along, a0, a1, b0, b1, z0, z1, s, o.get('depth', 0.45))
        elif k == 'french':
            unit_french(dor, o, w)
        elif k == 'slider':
            unit_slider(dor, o, w)
        elif k == 'sliding_cl':
            unit_sliding_cl(dor, o, w)
        elif k == 'arch':
            unit_arch(arch, o, w)
        elif k == 'cased':
            unit_cased(dor, o, w)
        elif k == 'door':
            if o.get('style') == 'front':
                continue                                                                                   # the arched recess, frame + leaf: build_entry / build_entry_door
            unit_door(dor, o, w, ws)
        # board-and-batten shutters (plan kw or the SHUTTERS table) on exterior windows
        sh = o.get('shutters', SHUTTERS.get(o['name'], 0.0))
        if sh and k in ('dh', 'dh3', 'leaded', 'fixed') and w['kind'] in ('ext', 'up'):
            bo = b1 if s > 0 else b0
            _shutters(win, along, a0, a1, bo, s, z0, z1, sh, casing=0.08 if k == 'leaded' else 0.09)
    win.build("Ext_Windows", [M['trim'], M['glass'], M['glass_frost'], M['steel'], L['lead'], L['glass_lead'], L['screen'], M['brass']], coll='House')
    dor.build("Ext_Doors", [M['trim'], M['glass'], M['brass'], M['steel']], coll='House',smooth=True)
    arch.build("Ext_Arches", [M['wall']], coll='House')


# ---------------------------------------------------------------- slabs, roofs, porch, steps, rails, lanterns
FOOTPRINT = [(-5.75, -.3, 0., BED_REAR+WT), (-.3, 1.2, 0., FAMILY_REAR+WT), (1.2, 5.75, 1.8, 13.85), (1.2,3.5,13.85,FAMILY_REAR+WT)]
# Slab edges sit inside stucco; coincident outer faces cause black shadow seams.
SLAB_FOOTPRINT = [(-5.73,-.3,.02,BED_REAR+WT-.02),(-.3,1.2,.02,FAMILY_REAR+WT-.02),
                  (1.2,5.73,1.82,13.83),(1.2,3.48,13.83,FAMILY_REAR+WT-.02)]
UPPER_FOOTPRINT = SLAB_FOOTPRINT
GABLE_RECT = (UPX0, UPX1, UPY0, UPY1)
WING_RECT = (WINGX0, WINGX1, WINGY0, WINGY1)
DECK_RECT = (-5.5, UPX0, 7.6, 11.45)


def _plate_holes(mb, x0, x1, y0, y1, z0, z1, holes, mi=0):
    """Slab minus arbitrary axis-aligned rectangles (they may share x ranges)."""
    xs = sorted({x0, x1} | {h[0] for h in holes} | {h[1] for h in holes})
    xs = [x for x in xs if x0 <= x <= x1]
    for xa, xb in zip(xs, xs[1:]):
        if xb - xa < 1e-6:
            continue
        xm = (xa + xb) / 2
        cuts = sorted((max(y0,h[2]), min(y1,h[3])) for h in holes
                      if h[0] <= xm <= h[1] and h[2] < y1 and h[3] > y0)
        cur = y0
        for (hy0, hy1) in cuts:
            if hy0 > cur:
                mb.box(xa, xb, cur, hy0, z0, z1, mi)
            cur = max(cur, hy1)
        if y1 > cur:
            mb.box(xa, xb, cur, y1, z0, z1, mi)


def build_slabs(M):
    mb = MB()
    for (x0, x1, y0, y1) in SLAB_FOOTPRINT:
        _plate_holes(mb,x0,x1,y0,y1,-.30,0.,[(4.65,5.75,11.45,12.5)],0)                                      # main floor (concrete)
    mb.box(PORCH[0], PORCH[1] + 0.25, PORCH[2] - 0.25, PORCH[3], -0.30, -0.02, 0)
    for (x0, x1, y0, y1) in UPPER_FOOTPRINT:
        _plate_holes(mb, x0, x1, y0, y1, Z_MC, Z_ROOF1,
                     [STAIR_WELL,(-6.5,6.0,-.3,UPY0)],1)
    roof_holes = [GABLE_RECT, WING_RECT, DECK_RECT,(-6.5,6.,-.3,UPY0)]
    for (x0, x1, y0, y1) in UPPER_FOOTPRINT:
        _plate_holes(mb, x0, x1, y0, y1, Z_ROOF1, Z_ROOF1 + 0.02, roof_holes, 2)  # torch-down roof finish
    mb.box(DECK_RECT[0], DECK_RECT[1], DECK_RECT[2], DECK_RECT[3], Z_ROOF1, Z_ROOF1 + 0.04, 3)   # deck pavers
    mb.box(PORCH[0], PORCH[1], PORCH[2], PORCH[3], -0.02, 0.0, 4)                                 # porch tile
    # porch tile border course (0.15 m) round the porch floor, and step nosings
    L = _local(M)
    px0, px1, py0, py1 = PORCH
    for (bx0, bx1, by0, by1) in ((px0, px1, py0, py0 + 0.15), (px0, px1, py1 - 0.15, py1), (px0, px0 + 0.15, py0, py1), (px1 - 0.15, px1, py0, py1)):
        mb.box(bx0, bx1, by0, by1, 0.0, 0.003, 5)
    # Independent flat interior ceilings below the continuous sloping front roof.
    for key in ('living','dining'):
        x0,x1,y0,y1=ROOMS[key][:4]
        mb.box(x0,x1,y0,y1,Z_MC,Z_MC+.02,1)
    mb.box(-1.25,1.05,ENTRY_VEST_Y1,5.0,Z_MC,Z_MC+.02,1)
    mb.box(-1.25,-.3,5.,6.01,Z_MC,Z_MC+.02,1)
    mb.build("Ext_Slabs", [M['concrete'], M['ceiling'], M['roof_flat'], L['paver'], M['tile_entry'], L['border']], coll='House')


RAKE = 0.30          # gable-end overhang beyond UPY0 / UPY1
EAVE_W = 0.25        # -X eave overhang of the gable roof
TILE_P = 0.25        # S-tile pitch across the slope
TILE_E = 0.34        # course exposure up the slope
TILE_A = 0.045       # barrel height
TILE_T = 0.014       # tile shell thickness


def _tile_field(tile, xe, ze, xr, zr, y0, y1, rng, mi=0, s_end=None, along='X', b_of=None):
    """Courses of S-tiles on the plane through (xe, ze) [eave] -> (xr, zr) [ridge], from y0 to y1.  Each course is one
    closed corrugated section (top profile + shell underside) swept from its lower edge (riding 25 mm up on the
    course below) to its upper edge (lapped 70 mm under the next course).  Per-column height jitter, per-course
    lateral offset.  Returns the slope length."""
    dx, dz = xr - xe, zr - ze
    Lslope = math.hypot(dx, dz)
    ux, uz = dx / Lslope, dz / Lslope
    nx, nz = (-uz, ux) if dx > 0 else (uz, -ux)
    if nz < 0:
        nx, nz = -nx, -nz
    s_end = Lslope - 0.05 if s_end is None else s_end
    ncols = int(math.ceil((y1 - y0) / TILE_P))
    b_of = b_of or (lambda ss: (y0, y1))
    n = 0
    s0 = -0.05
    while s0 < s_end - 0.08:
        s1 = min(s0 + TILE_E + 0.07, s_end)
        off_y = rng.uniform(-0.01, 0.01)
        jit = [rng.uniform(-0.004, 0.004) for _ in range(ncols + 1)]
        # top profile across the course: barrel every pitch (a raised half-sine over 45 % of the pitch, flat pan between)
        ntot = ncols * 10
        prof = []
        for kk in range(ntot + 1):
            y = y0 + (y1 - y0) * kk / ntot
            t = ((y - y0 - off_y) / TILE_P) % 1.0
            h = TILE_A * (max(0.0, math.sin(math.pi * t / 0.45)) ** 0.8 if t < 0.45 else 0.0) + jit[min(ncols, int((y - y0 - off_y) / TILE_P) % (ncols + 1))]
            prof.append((y, h))
        # closed section: top left->right, then underside right->left
        sec_top = prof
        sec_bot = [(y, h - TILE_T) for (y, h) in reversed(prof)]
        secs = []
        for (ss, lift) in ((s0, 0.025), (s1, 0.0)):
            sec = []
            bb0, bb1 = b_of(max(0.0, ss))
            for (y, h) in sec_top + sec_bot:
                hh = h + lift
                yy = min(max(y, bb0), max(bb0, bb1))                       # clamp to the plane's outline (hips / mitres)
                a = xe + ux * ss + nx * hh
                x_, y_ = _ab(along, a, yy)
                sec.append((x_, y_, ze + uz * ss + nz * hh))
            secs.append(sec)
        tile.sweep(secs, mi, close=False, caps=True)
        n += 1
        s0 += TILE_E
    return Lslope


def _lapped_tubes(tile, p0, p1, r=0.08, L=0.40, lap=0.08, mi=0):
    """A run of overlapping barrel tiles (slightly tapered so each lap steps) from p0 to p1."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    total = d.length
    if total < 1e-6:
        return
    d.normalize()
    t = 0.0
    while t < total - 0.02:
        a = p0 + d * t
        b = p0 + d * min(t + L, total)
        tile.tube(tuple(a), tuple(b), r * 0.9, r, seg=12, mi=mi)
        t += L - lap


def build_roof(M):
    from .roof_form import build_upper, build_low_rear
    build_upper(M)
    build_low_rear(M)


def _append_clipped_roof_tiles(target, patch, outline, insets=None):
    """Cut complete tile courses to a convex roof face, preserving clean cut edges.

    Clamping all outlying profile vertices to one line collapses barrels into
    spikes. Bisecting the closed tile shells gives actual hip/valley cuts.
    """
    import bmesh
    me=bpy.data.meshes.new('RoofTileClipTemporary')
    me.from_pydata(patch.v,[],patch.f)
    bm=bmesh.new();bm.from_mesh(me);bpy.data.meshes.remove(me)
    insets=insets or {}
    for i,(a,b) in enumerate(zip(outline,outline[1:]+outline[:1])):
        delta=Vector(b)-Vector(a)
        outward=Vector((delta.y,-delta.x,0)).normalized()
        origin=Vector(a)-outward*insets.get(i,0.)
        bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),
                              plane_co=origin,plane_no=outward,dist=.00001,
                              clear_outer=True,clear_inner=False)
        boundary=[e for e in bm.edges if e.is_boundary]
        if boundary:bmesh.ops.holes_fill(bm,edges=boundary,sides=0)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.verts.index_update()
    target._add([tuple(v.co) for v in bm.verts],[[v.index for v in f.verts] for f in bm.faces],0)
    bm.free()


def build_front_roof(M):
    from .roof_form import build_front
    build_front(M)


def build_rainwater(M):
    """Half-round gutters on the gable's -X eave and the wing eave (with brackets + downspouts onto the roof deck),
    scupper linings + leader heads + downspouts to grade at the parapet scuppers (photo 30 shows one by the side door)."""
    L = _local(M)
    mb = MB()      # 0 white gutter metal, 1 galvanised, 2 stucco (splash pads)
    k = (Z_RIDGE - Z_EAVE) / (UP_RIDGE_X - UPX0)
    y0, y1 = UPY0 - RAKE, UPY1 + RAKE
    # gable -X eave
    xg = UPX0 - EAVE_W - 0.07
    zg = Z_EAVE - k * EAVE_W - 0.10
    _trough(mb, xg, y0, y1, zg + 0.04, 0.065, 0)
    yy = y0 + 0.3
    while yy < y1:
        mb.box(xg - 0.07, UPX0 - EAVE_W + 0.01, yy - 0.012, yy + 0.012, zg + 0.045, zg + 0.07, 1)     # brackets
        yy += 0.6
    _downspout(mb, (xg, UPY0 + 0.35, zg - 0.06), (UPX0 - 0.06, UPY0 + 0.35), Z_ROOF1 + 0.02, wall_x=UPX0)
    # wing: gutter along the +X pent fascia, downspout onto the laundry roof
    xw = WINGX1 + RAKE + 0.07
    zw = Z_EAVE - k * RAKE - 0.10
    _trough(mb, xw, WINGY0 - RAKE, WINGY1 + RAKE, zw + 0.04, 0.06, 0)
    yy = WINGY0 - RAKE + 0.3
    while yy < WINGY1 + RAKE:
        mb.box(WINGX1 + RAKE - 0.01, xw + 0.07, yy - 0.012, yy + 0.012, zw + 0.04, zw + 0.065, 1)
        yy += 0.6
    _downspout(mb, (xw, 13.3, zw - 0.06), (WINGX1 + 0.06, 13.3), Z_ROOF1 + 0.02, wall_x=WINGX1)
    # entry tower: leader from the tile pent's left end, along the tower's +X face, round the corner and down its street face (photo p00_entry)
    mb.path_tube([(1.13, TOWER_Y - 0.07, 2.42), (1.13, TOWER_Y - 0.07, Z_GRADE + 0.12), (1.13, TOWER_Y - 0.36, Z_GRADE + 0.02)], 0.04, seg=10, mi=0)
    mb.box(1.04, 1.22, TOWER_Y - 0.16, TOWER_Y + 0.02, 2.24, 2.44, 0)                                      # leader head under the skirt's soffit
    mb.cylinder(1.13, TOWER_Y - 0.07, 2.42, 2.52, 0.035, seg=10, mi=0)
    for zz in (Z_GRADE + 0.5, 1.5, 2.5):
        mb.box(1.08, 1.2, TOWER_Y - 0.11, TOWER_Y, zz - 0.012, zz + 0.012, 0)
    # parapet scuppers -> leader heads -> downspouts to the grade
    for (along, a, b0) in SCUPPERS:
        if b0 == 11.45:            # deck parapet: spout only (it drains onto the single-storey roof)
            x, y = a, 11.6
            _lining(mb, 'X', x - 0.13, x + 0.13, y - 0.16, y + 0.10, Z_UP + 0.015, Z_UP + 0.125, 0.012, 1)
            continue
        b1 = b0 + WT
        s = +1 if (along == 'X' and b1 > 2.06) or (along == 'Y' and b1 > -5.4) else -1
        face = b1 if s > 0 else b0
        from .roof_form import lower_height
        hx,hy=_ab(along,a,face)
        zh0 = lower_height(hx,hy)-.04
        # Open eave collector at the actual roof height, without a parapet sleeve.
        lo, hi = (face, face + 0.18) if s > 0 else (face - 0.18, face)
        B(mb, along, a - 0.16, a + 0.16, lo, hi, zh0 - 0.22, zh0 + 0.02, 0)                    # leader head (box)
        B(mb, along, a - 0.13, a + 0.13, lo + 0.01, hi - 0.01, zh0 - 0.21, zh0 + 0.035, 0) if False else None
        px, py = _ab(along, a, face + s * 0.07)
        mb.cylinder(px, py, Z_GRADE - 0.02, zh0 - 0.22, 0.045, seg=12, mi=0)                   # downspout
        for zz in (Z_GRADE + 0.5, Z_GRADE + 1.6, Z_ROOF1 - 0.4):                                 # straps
            B(mb, along, a - 0.055, a + 0.055, min(face, face + s * 0.12), max(face, face + s * 0.12), zz - 0.012, zz + 0.012, 0)
        # shoe at the bottom kicking out from the wall + a splash pad
        sx, sy = _ab(along, a, face + s * 0.32)
        mb.tube((px, py, Z_GRADE + 0.10), (sx, sy, Z_GRADE + 0.02), 0.045, 0.045, seg=12, mi=0)
        B(mb, along, a - 0.2, a + 0.2, min(face + s * 0.05, face + s * 0.6), max(face + s * 0.05, face + s * 0.6), Z_GRADE - 0.01, Z_GRADE + 0.02, 2)
    mb.build("Ext_Rainwater", [L['gutter'], L['galv'], M['concrete']], coll='House', smooth=True)


def _trough(mb, x, y0, y1, z_top, r, mi):
    """Half-round gutter along Y: an open semicircular shell (2 mm thick) with a rolled front bead and end caps."""
    outer = [(x + r * math.cos(a), z_top - r + r * math.sin(a)) for a in [-math.pi * k / 10 for k in range(11)]]
    inner = [(x + (r - 0.004) * math.cos(a), z_top - r + (r - 0.004) * math.sin(a)) for a in [-math.pi * (10 - k) / 10 for k in range(11)]]
    prof = outer + inner
    secs = [[(px, yy, pz) for (px, pz) in prof] for yy in (y0, y1)]
    mb.sweep(secs, mi, close=False, caps=True)
    mb.tube((x - r, y0, z_top), (x - r, y1, z_top), 0.008, 0.008, seg=8, mi=mi)              # front bead


def _lining(mb, along, a0, a1, b0, b1, z0, z1, w, mi):
    """Hollow rectangular sleeve through a wall (a scupper / vent lining)."""
    if along == 'X':
        mb.frame(a0, a1, b0, b1, z0, z1, w, mi=mi, axis='Y')
    else:
        mb.frame(b0, b1, a0, a1, z0, z1, w, mi=mi, axis='X')


def _downspout(mb, p_top, wall_pt, z_bottom, wall_x):
    """Downspout from a gutter outlet (p_top) with an elbow back to the wall, down along it, an elbow out at the bottom."""
    x0, y0, z0 = p_top
    wx, wy = wall_pt
    d = -1 if wx < x0 else 1
    pts = [(x0, y0, z0 + 0.05), (x0, y0, z0 - 0.08), (wx - d * 0.0, wy, z0 - 0.25), (wx, wy, z_bottom + 0.30), (wx - d * 0.25, wy, z_bottom + 0.06)]
    mb.path_tube(pts, 0.04, seg=10, mi=0)
    for zz in (z0 - 0.5, z_bottom + 0.6):
        mb.box(min(wx, wx + d * 0.10), max(wx, wx + d * 0.10), wy - 0.05, wy + 0.05, zz - 0.012, zz + 0.012, 1)
    mb.box(wx - d * 0.45 - 0.2, wx - d * 0.45 + 0.2, wy - 0.18, wy + 0.18, z_bottom - 0.005, z_bottom + 0.02, 2)   # splash pad


def _lantern(mb, x, y, z, along, s, mi_iron=0, mi_glass=1, w=0.16, h=0.32):
    """Black iron box lantern on a wall face; along = the wall's axis, s = direction it projects."""
    if along == 'X':
        x0, x1, y0, y1 = x - w / 2, x + w / 2, min(y, y + s * w), max(y, y + s * w)
    else:
        x0, x1, y0, y1 = min(x, x + s * w), max(x, x + s * w), y - w / 2, y + w / 2
    mb.box(x0 + 0.03, x1 - 0.03, y0 + 0.03, y1 - 0.03, z - h / 2 + 0.04, z + h / 2 - 0.06, mi_glass)
    mb.box(x0, x1, y0, y1, z - h / 2, z - h / 2 + 0.04, mi_iron)                                  # base
    mb.box(x0 - 0.01, x1 + 0.01, y0 - 0.01, y1 + 0.01, z + h / 2 - 0.06, z + h / 2 - 0.02, mi_iron)  # cap
    mb.cylinder((x0 + x1) / 2, (y0 + y1) / 2, z + h / 2 - 0.02, z + h / 2 + 0.03, 0.03, 0.01, seg=8, mi=mi_iron)
    for (cx, cy) in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):                                      # corner bars
        mb.box(cx - 0.008, cx + 0.008, cy - 0.008, cy + 0.008, z - h / 2, z + h / 2 - 0.06, mi_iron)
    # wall backplate with two screws + the arm, a candle bulb inside
    if along == 'X':
        mb.box(x - 0.045, x + 0.045, min(y, y + s * 0.012), max(y, y + s * 0.012), z - 0.14, z + 0.14, mi_iron)
        mb.box(x - 0.02, x + 0.02, min(y, y + s * 0.03), max(y, y + s * 0.03), z - 0.03, z + 0.03, mi_iron)
        for dz in (-0.11, 0.11):
            mb.cylinder(x, y + s * 0.012, z + dz - 0.004, z + dz + 0.004, 0.006, seg=8, mi=mi_iron) if False else None
            tube(mb, (x, y + s * 0.012, z + dz), (x, y + s * 0.016, z + dz), 0.006, seg=8, mi=mi_iron)
        bx, by = x, y + s * (w / 2 + 0.03)
    else:
        mb.box(min(x, x + s * 0.012), max(x, x + s * 0.012), y - 0.045, y + 0.045, z - 0.14, z + 0.14, mi_iron)
        mb.box(min(x, x + s * 0.03), max(x, x + s * 0.03), y - 0.02, y + 0.02, z - 0.03, z + 0.03, mi_iron)
        for dz in (-0.11, 0.11):
            tube(mb, (x + s * 0.012, y, z + dz), (x + s * 0.016, y, z + dz), 0.006, seg=8, mi=mi_iron)
        bx, by = x + s * (w / 2 + 0.03), y
    mb.cylinder(bx, by, z - h / 2 + 0.04, z - h / 2 + 0.10, 0.012, seg=8, mi=mi_iron)                         # candle sleeve
    mb.sphere((bx, by, z - h / 2 + 0.13), 0.022, seg=10, rings=6, mi=2, squash=1.3)                            # bulb


def _digit7(mb, x, z, y, d, mi, s=0.11, t=0.012):
    """Brass seven-segment house number, s tall, on the face y (drawn toward -y)."""
    w = s * 0.55
    segs = {'0': 'abcdef', '1': 'bc', '2': 'abged', '3': 'abgcd', '4': 'fgbc', '5': 'afgcd', '6': 'afgedc', '7': 'abc', '8': 'abcdefg', '9': 'abcdfg'}[d]
    geo = {'a': (0, w, s - t, s), 'd': (0, w, 0, t), 'g': (0, w, s / 2 - t / 2, s / 2 + t / 2),
           'b': (w - t, w, s / 2, s), 'c': (w - t, w, 0, s / 2), 'f': (0, t, s / 2, s), 'e': (0, t, 0, s / 2)}
    for c in segs:
        (dx0, dx1, dz0, dz1) = geo[c]
        mb.box(x + dx0, x + dx1, y - 0.008, y, z + dz0, z + dz1, mi)


def build_entry(M):
    """Photo 00 entry: pointed-arch recess through the proud tower face, plum-framed door opening, recess floor +
    threshold, a downlight in the arch, four brick steps with bullnoses and two white pipe rails (bent tops into the
    wall), "1836" in brass, the straight tiled front roof edge and its fascia,
    the level porch eave, the walled porch's iron picket rail, the rear + side lanterns."""
    L = _local(M)
    rng = random.Random(23)
    o = BY_NAME['FrontDoor']
    a0, a1 = o['a0'], o['a1']
    xc = (a0 + a1) / 2
    st = MB()      # 0 stucco
    # ---- arch head infill (from the intrados up to the rectangular hole top) through the tower face + wall
    n = 16
    for side in (-1, 1):
        for kk in range(n):
            lo = xc + side * (a1 - a0) / 2 * kk / n
            hi = xc + side * (a1 - a0) / 2 * (kk + 1) / n
            lo, hi = min(lo, hi), max(lo, hi)
            # (only in FRONT of the door plane, y <= 0.06: the rectangular door + its head + the back panel sit behind the arch,
            #  so the leaf's square top corners pass behind the shoulders when the film swings it open)
            st.hexa([(lo, TOWER_Y, _arch_z(lo, a0, a1)), (hi, TOWER_Y, _arch_z(hi, a0, a1)), (hi, 0.06, _arch_z(hi, a0, a1)), (lo, 0.06, _arch_z(lo, a0, a1)),
                     (lo, TOWER_Y, ARCH_TOP + 0.01), (hi, TOWER_Y, ARCH_TOP + 0.01), (hi, 0.06, ARCH_TOP + 0.01), (lo, 0.06, ARCH_TOP + 0.01)], 0)
    st.box(a0, a1, 0.06, 0.25, o['z1'] + 0.03, ARCH_TOP + 0.02, 0)                                     # recess back panel over the door (behind the arch, above the frame head)
    st.build("Ext_Entry", [L['stucco']], coll='House')
    tile = MB()    # 0 tile, 1 mortar
    sh = MB()      # 0 soffit stucco, 1 white board, 2 galvanised
    A = TILE_A
    # ---- the coping: ONE barrel-pan-barrel S-tile strip 0.24 wide swept along the level parapet, round the fillet and down the
    #      rake to the tower's right corner (laps 2 mm: reads as a smooth straight band); a white board 0.14 tall under its front edge
    prof = []
    W_ = 0.24
    for k in range(25):
        u = k / 24 * W_
        if u < 0.09:
            h = A * max(0.0, math.sin(math.pi * u / 0.09)) ** 0.8
        elif u < 0.15:
            h = 0.0
        else:
            h = A * max(0.0, math.sin(math.pi * (u - 0.15) / 0.09)) ** 0.8
        prof.append((u, h))
    xb = _RAKE[1][0]
    xs_c = [-5.75 + (xb + 5.75) * i / 420 for i in range(421)]
    secs = []; boards = []
    for x in xs_c:
        f = _face_y(x)
        z = _zr(x)
        lap = 0.002 * (1.0 - ((x + 5.75) / 0.34) % 1.0)
        top = [(x, f - 0.04 + u, z + h + lap + 0.004) for (u, h) in prof]
        bot = [(x, f - 0.04 + u, z + h + lap + 0.004 - TILE_T) for (u, h) in reversed(prof)]
        secs.append(top + bot)
        boards.append([(x, f - 0.07, z - 0.16), (x, f - 0.04, z - 0.16), (x, f - 0.04, z - 0.01), (x, f - 0.07, z - 0.01)])
    tile.sweep(secs, 0, close=False, caps=True)
    sh.sweep(boards, 1, close=False, caps=True)
    # the coping's bed: a thin sloped stucco strip closing the wall top under the tiles (the 0.035 gap)
    for x0_, x1_ in zip(xs_c, xs_c[1:]):
        f0, f1 = _face_y(x0_), _face_y(x1_)
        _slab_poly(sh, [(x0_, f0 - 0.04, _zr(x0_) + 0.004), (x1_, f1 - 0.04, _zr(x1_) + 0.004), (x1_, 0.26, _zr(x1_) + 0.004), (x0_, 0.26, _zr(x0_) + 0.004)], 0.04, 0)
    # Level street-facing porch eave; the continuous tiled roof is built by roof_form.
    py0, pz0 = PENT_Y0, PENT_EAVE_Z
    sh.box(PENT_X0,5.82,py0-.04,py0,pz0-.17,pz0-.012,1)
    sh.box(PENT_X0,5.82,py0-.055,py0+.01,pz0-.008,pz0+.008,2)
    tile.build("Ext_EntryTile", [L['tile'], L['mortar']], coll='House', smooth=True)
    sh.build("Ext_PentSoffit", [L['soffit'], M['trim'], L['galv']], coll='House')
    # ---- door frame (dark, in the recess), stop, threshold, recess floor, interior casing, arch downlight
    dr = MB()      # 0 dark frame, 1 white trim, 2 brass, 3 brick
    dr.box(a0, a0 + 0.035, 0.06, 0.20, 0.0, o['z1'] + 0.035, 0)
    dr.box(a1 - 0.035, a1, 0.06, 0.20, 0.0, o['z1'] + 0.035, 0)
    dr.box(a0 + 0.035, a1 - 0.035, 0.06, 0.20, o['z1'], o['z1'] + 0.035, 0)
    _stop(dr, 'X', a0 + 0.035, a1 - 0.035, ENTRY_HINGE[1] + 0.024, ENTRY_HINGE[1] + 0.042, 0.0, o['z1'], 0)
    dr.box(a0 + 0.035, a1 - 0.035, 0.06, 0.11, 0.0, 0.02, 2)                                             # brass threshold
    dr.box(a0, a1, TOWER_Y - 0.01, 0.06, -0.03, 0.0, 3)                                                  # brick recess floor
    _casing(dr, 'X', a0, a1, 0.25, +1, 0.0, o['z1'], 1, w=0.07, proud=0.018, sill=False)                    # inside casing (entry side)
    dr.cylinder(xc, -0.06, _arch_z(xc, a0, a1) - 0.03, _arch_z(xc, a0, a1) + 0.02, 0.05, seg=14, mi=0)
    dr.build("Ext_EntryFrame", [L['frame_dark'], M['trim'], M['brass'], M['brick']], coll='House')
    add_light("L_Ext_Front", 'POINT', (xc, -0.06, _arch_z(xc, a0, a1) - 0.08), 22, K30, size=0.06)
    # ---- steps (4 brick risers with bullnoses) + pipe rails, "1836"
    mb = MB()      # 0 brick, 1 iron white, 2 brass
    x0, x1, ys, ye = PORCH_STEPS
    n = stairs(mb, x0, x1, ys, ye, Z_GRADE, 0.0, n=4, mi=0, base=0.35)
    dz = (0.0 - Z_GRADE) / n; dy = (ye - ys) / n
    for i in range(n):
        ya = ys + dy * i
        mb.box(x0 - 0.015, x1 + 0.015, ya - 0.025, ya + 0.01, Z_GRADE + dz * (i + 1) - 0.02, Z_GRADE + dz * (i + 1) + 0.012, 0)
    for xr_ in (x0 + 0.07, x1 - 0.07):
        mb.cylinder(xr_, ys + 0.08, Z_GRADE - 0.2, Z_GRADE + dz + 0.85, 0.018, seg=10, mi=1)
        mb.path_tube([(xr_, ys + 0.08, Z_GRADE + dz + 0.85), (xr_, -0.42, 0.86), (xr_, -0.30, 0.94), (xr_, TOWER_Y + 0.02, 0.94)], 0.018, seg=10, mi=1)
    for i, d in enumerate("1836"):                                                                   # overlay on photo 00: x 0.6..0.98, z 1.28..1.44, stepping up slightly
        _digit7(mb, 0.65 + i * 0.105, 1.22 + i * 0.015, TOWER_Y, d, 2, s=0.11)
    mb.build("Ext_EntrySteps", [M['brick'], M['iron_white'], M['brass']], coll='House', smooth=True)
    # ---- porch picket rail on the parapet (front + the +X side), spear finials, a scroll at the tower end
    rl = MB()      # 0 iron white
    zb, zt_ = 1.06, 1.56
    runs = [('X', 1.24, 5.73, 0.125), ('Y', 0.25, 1.78, 5.625)]
    for (along, r0, r1, b) in runs:
        B(rl, along, r0, r1, b - 0.015, b + 0.015, zb, zb + 0.012, 0)
        B(rl, along, r0, r1, b - 0.015, b + 0.015, zt_, zt_ + 0.012, 0)
        a = r0 + 0.06
        while a < r1 - 0.03:
            px, py = _ab(along, a, b)
            rl.cylinder(px, py, zb, zt_ + 0.05, 0.006, seg=8, mi=0)
            rl.lathe(px, py, zt_ + 0.05, [(0, 0), (0.014, 0), (0.004, 0.055), (0, 0.06)], seg=8, mi=0)
            a += 0.11
    rl.cylinder(5.625, 0.125, 1.05, zt_ + 0.12, 0.012, seg=10, mi=0)                                        # corner post
    rl.lathe(5.625, 0.125, zt_ + 0.12, [(0, 0), (0.022, 0), (0.006, 0.08), (0, 0.09)], seg=10, mi=0)
    for i in range(12):                                                                                    # scroll where the rail meets the tower
        a0_, a1_ = 2 * math.pi * i / 12, 2 * math.pi * (i + 1) / 12
        rl.tube((1.33 + 0.07 * math.cos(a0_), 0.125, 1.32 + 0.07 * math.sin(a0_)), (1.33 + 0.07 * math.cos(a1_), 0.125, 1.32 + 0.07 * math.sin(a1_)), 0.006, 0.006, seg=6, mi=0)
    rl.tube((1.26, 0.125, 1.25), (1.21, 0.125, 1.25), 0.006, 0.006, seg=6, mi=0)
    rl.build("Ext_PorchRail", [M['iron_white']], coll='House', smooth=True)
    # ---- lanterns (rear door, side door); the front door is lit by the arch downlight
    lan = MB()
    _lantern(lan, 2.35, FAMILY_REAR+WT, 2.0, 'X', +1)
    # The side light is recessed in the photographed entrance bay.
    lan.build("Ext_Lanterns", [M['iron_black'], M['glass_frost'], L['bulb']], coll='House', smooth=True)
    add_light("L_Ext_Rear", 'POINT', (2.35, FAMILY_REAR+.45, 2.0), 30, K30, size=0.1)
    add_light("L_Ext_Side", 'POINT', (4.85,11.95,2.4), 25, K30, size=0.1)


def build_rear(M):
    mb = MB()      # 0 brick, 1 iron white, 2 concrete
    x0, x1, y_top, y_bot = REAR_STEPS
    n = stairs(mb, x0, x1, y_bot, y_top, Z_GRADE, 0.0, n=3, mi=0, base=0.2)
    dz = (0.0 - Z_GRADE) / n; dy = (y_top - y_bot) / n
    for i in range(n):
        ya = y_bot + dy * i
        mb.box(x0 - 0.02, x1 + 0.02, ya + dy - 0.02 if dy < 0 else ya - 0.02, ya + dy + 0.02 if dy < 0 else ya + 0.02, Z_GRADE + dz * (i + 1) - 0.015, Z_GRADE + dz * (i + 1) + 0.015, 0)   # brick bullnose
    # rail on the +X side of the steps: two posts + a sloping top rail (photo 29)
    zt = 0.9
    p0 = (x1 - 0.05, y_bot - 0.05, Z_GRADE)
    p1 = (x1 - 0.05, y_top + 0.05, 0.0)
    for (p, ztop) in ((p0, Z_GRADE + zt), (p1, zt)):
        tube(mb, p, (p[0], p[1], ztop), 0.02, seg=8, mi=1)
    tube(mb, (p0[0], p0[1], Z_GRADE + zt), (p1[0], p1[1], zt), 0.025, seg=8, mi=1)
    tube(mb, (p0[0], p0[1], Z_GRADE + zt * 0.55), (p1[0], p1[1], zt * 0.55), 0.015, seg=6, mi=1)
    tube(mb, (p1[0], p1[1], zt), (p1[0], y_top - 0.3, zt), 0.022, seg=8, mi=1)
    tube(mb, (p1[0], y_top - 0.3, zt), (p1[0], y_top - 0.3, 0.0), 0.02, seg=8, mi=1)
    # side door stoop: 2 concrete steps out to +X and a pipe rail on the -Y side
    o = BY_NAME['SideDoor']
    ya, yb = o['a0'] - 0.1, o['a1'] + 0.1
    stairs_x(mb, ya, yb, 5.75, 4.65, Z_GRADE, 0.0, n=2, mi=2, base=0.2)
    for (x, z) in ((5.70,Z_GRADE),(4.80,0.0)):
        tube(mb, (x, ya - 0.03, z), (x, ya - 0.03, z + 0.9), 0.02, seg=8, mi=1)
    tube(mb, (5.70,ya-.03,Z_GRADE+.9),(4.80,ya-.03,.9), 0.022, seg=8, mi=1)
    mb.build("Ext_RearSteps", [M['brick'], M['iron_white'], M['concrete']], coll='House', smooth=True)


def build_trellis(M):
    mb = MB()
    x0, x1, y0, y1, z0, z1 = 6.28,6.32,7.5,10.4,Z_GRADE+.08,2.65
    y = y0
    while y <= y1 + 1e-6:
        mb.box(x0, x1, y - 0.015, y + 0.015, z0, z1, 0)
        y += 0.3
    z = z0
    while z <= z1 + 1e-6:
        mb.box(x0 + 0.04, x1 + 0.04, y0 - 0.015, y1 + 0.015, z - 0.015, z + 0.015, 0)
        z += 0.3
    mb.build("Ext_Trellis", [M['trim']], coll='House')


def build(M):
    ws = build_walls(M)
    build_units(M, ws)
    build_entry_door(M)
    build_slabs(M)
    build_roof(M)
    build_entry(M)
    build_front_roof(M)
    build_rear(M)
    build_trellis(M)
    from .fixtures import window_air_conditioners
    window_air_conditioners(M)
    build_rainwater(M)
