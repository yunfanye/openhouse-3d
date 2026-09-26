"""Main level, rear half (plan.BACK_ROOMS): hall, kitchen, pantry/mid closets, laundry, hall2, family room, bedroom A,
half bath, bath A (+ vestibule), bedroom B.  Photos 05-13.

Finishes (floors, crown / base / chair-rail mouldings), built-ins (kitchen cabinets + tile counters + greenhouse-window
counter, laundry, closet bump-outs, window seat), fixtures (sinks, tubs, toilets, cans, flush mounts), staging
furniture and room lights.  Walls, window / door units, arches and the ceiling slab are exterior.py's.
Object names start with Back_; lights with L_Back_.
"""
import math, random
from .plan import *
from archviz.mesh import *
from archviz.lights import *
from archviz.parts import *
from archviz import materials as _mat
from archviz import plants as _pl

K30 = (1.0, 0.84, 0.66)
FL = 0.015                       # floor finish thickness
_L = {}


# ================================================================== local materials
def _shadow_glass(name):
    """Clear glass whose shadow rays pass (Cycles has no refractive caustics here, so plain glass boxes would black
    out the stall behind them): Glass BSDF for camera rays, Transparent for shadow rays."""
    m, nt, b = _mat._new(name)
    lp = nt.nodes.new("ShaderNodeLightPath")
    gl = nt.nodes.new("ShaderNodeBsdfGlass"); gl.inputs["IOR"].default_value = 1.45; gl.inputs["Roughness"].default_value = 0.0
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(mx.inputs["Fac"], lp.outputs["Is Shadow Ray"])
    nt.links.new(mx.inputs[1], gl.outputs["BSDF"]); nt.links.new(mx.inputs[2], tr.outputs["BSDF"])
    nt.links.new(nt.nodes["Material Output"].inputs["Surface"], mx.outputs["Shader"])
    return m


def _local(M):
    if _L:
        return _L
    _L['wall_dark'] = _mat.plaster("WallGreyLower", base=(0.50, 0.49, 0.47, 1), rough=0.85, grain=0.12)
    _L['cream_xz'] = _mat.tiles("CreamTileXZ", (0.84, 0.76, 0.62, 1), grout=(0.66, 0.60, 0.52, 1), size=(0.15, 0.15), gap=0.004,
                                rough=0.22, variation=0.06, mottle=0.3, bump=0.2, coat=0.5, plane='XZ')
    _L['cream_yz'] = _mat.tiles("CreamTileYZ", (0.84, 0.76, 0.62, 1), grout=(0.66, 0.60, 0.52, 1), size=(0.15, 0.15), gap=0.004,
                                rough=0.22, variation=0.06, mottle=0.3, bump=0.2, coat=0.5, plane='YZ')
    _L['peach_yz'] = _mat.tiles("TilePeachYZ", (0.86, 0.52, 0.36, 1), grout=(0.70, 0.66, 0.60, 1), size=(0.15, 0.15), gap=0.004,
                                rough=0.2, variation=0.06, mottle=0.2, bump=0.2, coat=0.6, plane='YZ')
    _L['teal_yz'] = _mat.tiles("TileTealYZ", (0.20, 0.36, 0.38, 1), grout=(0.70, 0.66, 0.60, 1), size=(0.15, 0.15), gap=0.004,
                               rough=0.2, variation=0.06, mottle=0.2, bump=0.2, coat=0.6, plane='YZ')
    _L['peach'] = _mat.new_mat("PeachCeramic", (0.86, 0.52, 0.36, 1), rough=0.2, coat=0.6)       # checkerboard squares (plain,
    _L['teal'] = _mat.new_mat("TealCeramic", (0.20, 0.36, 0.38, 1), rough=0.2, coat=0.6)         # grout = the plate behind)
    _L['grout'] = _mat.new_mat("Grout", (0.66, 0.62, 0.56, 1), rough=0.9)
    _L['emit_flush'] = _mat.new_mat("FlushMountGlow", (1, 0.95, 0.85, 1), rough=0.6, emit=(1.0, 0.86, 0.68, 1), emit_str=2.2)
    _L['emit_glass'] = _mat.new_mat("LampGlass", (1, 0.9, 0.75, 1), rough=0.5, emit=(1.0, 0.80, 0.55, 1), emit_str=5.0)
    _L['lemon'] = _mat.new_mat("Lemon", (0.95, 0.80, 0.10, 1), rough=0.45, coat=0.3)
    _L['board'] = _mat.wood("CuttingBoard", light=(0.62, 0.42, 0.24, 1), dark=(0.45, 0.28, 0.15, 1), grain_axis='Y', rough=0.5, coat=0.05)
    _L['louvre'] = _mat.new_mat("LouvreWhite", (0.90, 0.90, 0.88, 1), rough=0.4, coat=0.2)
    _L['tv_screen'] = _mat.new_mat("TVScreenDark", (0.02, 0.02, 0.025, 1), rough=0.08, coat=1.0)
    _L['dial'] = _mat.new_mat("ApplianceDial", (0.35, 0.35, 0.36, 1), rough=0.4, metal=0.6)
    # bath A (photo 13): 4" checkerboard peach / blue-grey with a pale grout, cream field tile + bullnose
    _L['peach2'] = _mat.new_mat("PeachCeramic2", (0.88, 0.55, 0.40, 1), rough=0.18, coat=0.7)
    _L['teal2'] = _mat.new_mat("BlueGreyCeramic", (0.42, 0.55, 0.60, 1), rough=0.18, coat=0.7)
    _L['grout_pale'] = _mat.new_mat("GroutPale", (0.80, 0.77, 0.72, 1), rough=0.9)
    _L['bullnose'] = _mat.new_mat("CreamBullnose", (0.86, 0.78, 0.64, 1), rough=0.2, coat=0.6)
    _L['cream4_xz'] = _mat.tiles("Cream4XZ", (0.86, 0.78, 0.64, 1), grout=(0.78, 0.74, 0.68, 1), size=(0.108, 0.108), gap=0.003,
                                 rough=0.2, variation=0.05, mottle=0.25, bump=0.15, coat=0.6, plane='XZ')
    _L['cream4_yz'] = _mat.tiles("Cream4YZ", (0.86, 0.78, 0.64, 1), grout=(0.78, 0.74, 0.68, 1), size=(0.108, 0.108), gap=0.003,
                                 rough=0.2, variation=0.05, mottle=0.25, bump=0.15, coat=0.6, plane='YZ')
    _L['cream4_xy'] = _mat.tiles("Cream4XY", (0.86, 0.78, 0.64, 1), grout=(0.78, 0.74, 0.68, 1), size=(0.108, 0.108), gap=0.003,
                                 rough=0.2, variation=0.05, mottle=0.25, bump=0.15, coat=0.6)
    _L['glass_clear'] = _shadow_glass("ShowerGlassClear")
    _L['towel'] = _mat.fabric("TowelWhite", (0.92, 0.92, 0.90, 1), weave=120, bump=0.5)
    _L['towel_grey'] = _mat.fabric("TowelGrey", (0.55, 0.56, 0.55, 1), weave=120, bump=0.5)
    _L['mat'] = _mat.fabric("BathMat", (0.88, 0.86, 0.80, 1), weave=90, bump=0.6)
    _L['register'] = _mat.new_mat("RegisterBrown", (0.30, 0.26, 0.22, 1), rough=0.5, metal=0.3)
    _L['plate'] = _mat.new_mat("SwitchPlate", (0.92, 0.92, 0.90, 1), rough=0.35, coat=0.2)
    _L['duvet'] = _mat.linen("DuvetWhite", base=(0.94, 0.93, 0.90, 1), wrinkle=0.55)
    _L['sheet'] = _mat.linen("SheetWhite", base=(0.95, 0.95, 0.93, 1), wrinkle=0.3)
    _L['throw_sage'] = _mat.fabric("ThrowSage", (0.52, 0.58, 0.48, 1), weave=40, bump=0.4)
    _L['throw_rust'] = _mat.fabric("ThrowRust", (0.62, 0.36, 0.26, 1), weave=40, bump=0.4)
    _L['curtain'] = _mat.fabric("CurtainLinen", (0.86, 0.83, 0.76, 1), weave=70, bump=0.2)
    _L['mat_white'] = _mat.new_mat("ArtMat", (0.95, 0.94, 0.91, 1), rough=0.7)
    _L['soap'] = _mat.new_mat("SoapBottle", (0.55, 0.62, 0.55, 1), rough=0.3, coat=0.5)
    _L['coir'] = _mat.fabric("CoirMat", (0.55, 0.42, 0.25, 1), weave=160, bump=0.7)
    _L['book_a'] = _mat.new_mat("BookNavyB", (0.08, 0.10, 0.22, 1), rough=0.8)
    _L['book_b'] = _mat.new_mat("BookRustB", (0.45, 0.16, 0.08, 1), rough=0.8)
    _L['book_c'] = _mat.new_mat("BookCreamB", (0.80, 0.74, 0.60, 1), rough=0.85)
    _L['garm1'] = _mat.fabric("GarmentNavy", (0.10, 0.13, 0.24, 1), weave=90, bump=0.2)
    _L['garm2'] = _mat.fabric("GarmentWhite", (0.88, 0.88, 0.85, 1), weave=90, bump=0.2)
    _L['garm3'] = _mat.fabric("GarmentCamel", (0.62, 0.46, 0.28, 1), weave=90, bump=0.2)
    return _L


# ================================================================== trim helpers
CROWN = [(0.0, -0.09), (0.012, -0.09), (0.02, -0.07), (0.03, -0.052), (0.045, -0.035), (0.06, -0.018), (0.075, -0.006), (0.075, 0.0), (0.0, 0.0)]
BASE = [(0.0, 0.0), (0.014, 0.0), (0.014, 0.10), (0.010, 0.11), (0.004, 0.118), (0.0, 0.12)]
RAIL = [(0.0, -0.03), (0.02, -0.03), (0.026, -0.02), (0.026, -0.005), (0.02, 0.01), (0.012, 0.015), (0.0, 0.02)]


def _profile_strip(mb, along, a0, a1, b, side, zref, prof, mi=0):
    """Extrude a (d, dz) profile (d = distance from the wall face into the room) from a0 to a1 along the wall."""
    if a1 - a0 < 0.02:
        return
    secs = []
    for a in (a0, a1):
        sec = []
        for (d, dz) in prof:
            bb = b + side * d
            sec.append((a, bb, zref + dz) if along == 'X' else (bb, a, zref + dz))
        secs.append(sec)
    mb.sweep(secs, mi)


def _face_cuts(along, b, zlo, zhi, extra=()):
    """(a0, a1) intervals of plan openings lying in this face's wall plane that intersect z zlo..zhi."""
    cuts = []
    for o in OPENINGS:
        if o['along'] == along and abs(o['b'] - b) < 0.4 and o['z0'] < zhi and o['z1'] > zlo:
            cuts.append((o['a0'] - 0.05, o['a1'] + 0.05))
    cuts.extend(extra)
    return sorted(cuts)


def _segments(a0, a1, cuts):
    out, cur = [], a0
    for (c0, c1) in sorted(cuts):
        if c1 <= cur or c0 >= a1:
            continue
        if c0 > cur:
            out.append((cur, c0))
        cur = max(cur, c1)
    if a1 > cur:
        out.append((cur, a1))
    return out


def _trims(mb, faces, zf=FL, zc=Z_MC, crown=True, base=True, rail=False, mi=0, extra_cuts=()):
    for (along, a0, a1, b, side) in faces:
        if crown:
            for (s0, s1) in _segments(a0, a1, _face_cuts(along, b, zc - 0.1, zc + 0.1, extra_cuts)):
                _profile_strip(mb, along, s0, s1, b, side, zc, CROWN, mi)
        if base:
            for (s0, s1) in _segments(a0, a1, _face_cuts(along, b, -0.01, 0.13, extra_cuts)):
                _profile_strip(mb, along, s0, s1, b, side, zf, BASE, mi)
        if rail:
            for (s0, s1) in _segments(a0, a1, _face_cuts(along, b, 0.85, 0.95, extra_cuts)):
                _profile_strip(mb, along, s0, s1, b, side, 0.9, RAIL, mi)


def _lower_wall(mb, faces, mi=0, z0=FL + 0.12, z1=0.87):
    """Darker paint below the chair rail: a 5 mm plate on the wall face (openings cut)."""
    for (along, a0, a1, b, side) in faces:
        for (s0, s1) in _segments(a0, a1, _face_cuts(along, b, z0, z1)):
            if along == 'X':
                mb.box(s0, s1, b, b + side * 0.005, z0, z1, mi)
            else:
                mb.box(b, b + side * 0.005, s0, s1, z0, z1, mi)


def _floor(name, M, x0, x1, y0, y1, mat, z0=0.0, t=FL):
    mb = MB()
    mb.box(x0, x1, y0, y1, z0, z0 + t)
    return mb.build(name, [mat], coll='House')


def _rug(name, M, cx, cy, w, d, mat, t=0.012):
    mb = MB()
    mb.rbox(cx - w / 2, cx + w / 2, cy - d / 2, cy + d / 2, FL, FL + t, r=0.006, mi=0, seg=2)
    return mb.build(name, [mat], coll='House', smooth=True)


# ---- faces (along, a0, a1, b, side) = the room-side face of every wall of a room (side = +1: room on the +b side)
FACES = {
    'hall':    [('Y', 5.0, 12.75, -1.25, +1), ('Y', 5.0, 12.75, -0.3, -1)],
    'hall2':   [('Y', 11.3, 13.6, 2.1, +1), ('Y', 11.3, 13.6, 3.35, -1), ('X', 2.1, 3.35, 11.3, +1)],
    'kitchen': [('Y', 7.1, 11.15, 1.5, +1), ('Y', 7.1, 11.15, 5.5, -1), ('X', 1.5, 5.5, 7.1, +1), ('X', 1.5, 5.5, 11.15, -1)],
    'laundry': [('Y',11.3,13.6,3.5,1),('Y',12.65,13.6,5.5,-1),('Y',11.45,12.5,4.4,-1),('X',4.4,5.5,12.65,1),('X',3.5,4.65,11.3,1),('X',3.5,5.5,13.6,-1)],
    'bed_a':   [('Y', 5.9, 9.9, -5.5, +1), ('Y', 5.9, 9.9, -1.4, -1), ('X', -5.5, -1.4, 5.9, +1), ('X', -5.5, -1.4, 9.9, -1)],
    'bath_a':  [('Y', 10.05, 12.35, -5.5, +1), ('X', -5.5, -2.85, 10.05, +1), ('X', -5.5, -1.4, 12.35, -1), ('Y', 10.05, 11.5, -2.85, -1),
                ('X', -2.85, -1.4, 11.5, +1), ('Y', 11.5, 12.35, -1.4, -1)],
}

for _r in ('family','half','bed_b'):
    _x0,_x1,_y0,_y1=ROOMS[_r][:4]
    FACES[_r]=[('Y',_y0,_y1,_x0,1),('Y',_y0,_y1,_x1,-1),('X',_x0,_x1,_y0,1),('X',_x0,_x1,_y1,-1)]
# Bath vestibule is continuous; the powder room is in the living-room notch.
FACES['bath_a']=[('Y',10.05,12.75,-5.5,1),('X',-5.5,-1.4,10.05,1),('X',-5.5,-1.4,12.75,-1),('Y',10.05,12.75,-1.4,-1)]

# ================================================================== small builders
def _shaker_door(mb, along, a0, a1, b, side, z0, z1, mi, mi_knob=None, knob='a1', stile=0.06, panel=0.016):
    """Shaker cabinet door in the plane b (facing `side`): flat panel + a 60 mm frame standing proud, a knob."""
    def B(aa0, aa1, bb0, bb1, zz0, zz1, m):
        if along == 'X':
            mb.box(aa0, aa1, bb0, bb1, zz0, zz1, m)
        else:
            mb.box(bb0, bb1, aa0, aa1, zz0, zz1, m)
    f0, f1 = (b, b + side * panel) if side > 0 else (b + side * panel, b)
    B(a0, a1, f0, f1, z0, z1, mi)
    g0, g1 = (b + side * panel, b + side * (panel + 0.012)) if side > 0 else (b + side * (panel + 0.012), b + side * panel)
    B(a0, a0 + stile, g0, g1, z0, z1, mi); B(a1 - stile, a1, g0, g1, z0, z1, mi)
    B(a0, a1, g0, g1, z0, z0 + stile, mi); B(a0, a1, g0, g1, z1 - stile, z1, mi)
    if mi_knob is not None:
        ka = a1 - 0.05 if knob == 'a1' else a0 + 0.05
        kz = z0 + 0.10 if (z1 - z0) < 0.5 else (z1 - 0.12 if (z1 - z0) < 1.0 else z0 + 1.0)
        kb = b + side * (panel + 0.012)
        if along == 'X':
            mb.cylinder(ka, kb + side * 0.012, kz - 0.012, kz + 0.012, 0.012, seg=10, mi=mi_knob)
            B(ka - 0.006, ka + 0.006, kb, kb + side * 0.03, kz - 0.006, kz + 0.006, mi_knob)
        else:
            mb.cylinder(kb + side * 0.012, ka, kz - 0.012, kz + 0.012, 0.012, seg=10, mi=mi_knob)
            B(ka - 0.006, ka + 0.006, kb, kb + side * 0.03, kz - 0.006, kz + 0.006, mi_knob)


def _cabinet_run(mb, along, a0, a1, b_back, depth, side, z0, z1, mi, mi_knob, door_w=0.55, drawers=False, toe=0.1, hollow=False):
    """Base / upper cabinet carcass from the wall plane b_back projecting `depth` toward `side`, doors on the front."""
    front = b_back + side * depth
    def B(aa0, aa1, bb0, bb1, zz0, zz1, m):
        lo, hi = min(bb0, bb1), max(bb0, bb1)
        if along == 'X':
            mb.box(aa0, aa1, lo, hi, zz0, zz1, m)
        else:
            mb.box(lo, hi, aa0, aa1, zz0, zz1, m)
    zt = z0 + toe if toe else z0
    if hollow:
        B(a0,a1,b_back,b_back+side*.018,zt,z1,mi)
        B(a0,a1,b_back,front-side*.02,zt,zt+.018,mi)
        B(a0,a0+.018,b_back,front-side*.02,zt,z1,mi)
        B(a1-.018,a1,b_back,front-side*.02,zt,z1,mi)
    else:
        B(a0,a1,b_back,front-side*.02,zt,z1,mi)
    if toe:
        B(a0, a1, b_back, front - side * 0.06, z0, zt, mi)                  # toe kick (recessed 60 mm)
    n = max(1, round((a1 - a0) / door_w))
    w = (a1 - a0) / n
    for i in range(n):
        d0, d1 = a0 + i * w + 0.004, a0 + (i + 1) * w - 0.004
        if drawers:
            dz = (z1 - zt) / 3
            for k in range(3):
                _shaker_door(mb, along, d0, d1, front - side * 0.02, side, zt + k * dz + 0.004, zt + (k + 1) * dz - 0.004, mi, mi_knob, stile=0.045)
        else:
            _shaker_door(mb, along, d0, d1, front - side * 0.02, side, zt + 0.004, z1 - 0.004, mi, mi_knob, knob='a1' if i % 2 == 0 else 'a0')


def _toilet(mb, x, y, mi, tank=(0, 1)):
    """Toilet at (x, y) with its tank against the wall in direction `tank`."""
    tx, ty = tank
    ry = 1.35 if tx == 0 else 1.0
    cx, cy = x - tx * 0.1, y - ty * 0.1
    prof = [(0, 0.02), (0.15, 0.02), (0.14, 0.12), (0.17, 0.3), (0.19, 0.38), (0.17, 0.41), (0, 0.41)]
    if tx == 0:
        mb.lathe(cx, cy, 0.0, prof, seg=20, mi=mi, ry=1.35)
    else:
        # elongated along x: lathe with ry < 1 (x radius larger) via a wider profile
        mb.lathe(cx, cy, 0.0, [(r * 1.35, z) for (r, z) in prof], seg=20, mi=mi, ry=1 / 1.35)
    # seat + lid
    if tx == 0:
        mb.lathe(cx, cy, 0.41, [(0, 0), (0.19, 0), (0.19, 0.03), (0, 0.03)], seg=20, mi=mi, ry=1.35)
    else:
        mb.lathe(cx, cy, 0.41, [(0, 0), (0.26, 0), (0.26, 0.03), (0, 0.03)], seg=20, mi=mi, ry=1 / 1.35)
    # tank
    if tx == 0:
        mb.rbox(x - 0.22, x + 0.22, y + ty * 0.12 - 0.09, y + ty * 0.12 + 0.09, 0.42, 0.82, r=0.015, mi=mi)
    else:
        mb.rbox(x + tx * 0.12 - 0.09, x + tx * 0.12 + 0.09, y - 0.22, y + 0.22, 0.42, 0.82, r=0.015, mi=mi)


def _pedestal_sink(mb,x,y,mi_porc,mi_brass):
    from .interior_upper import _ring_slab,_oval_sink
    mb.lathe(x,y,0.,[(0,0),(.13,0),(.14,.025),(.10,.13),(.075,.56),(.105,.69),(0,.69)],seg=36,mi=mi_porc)
    _ring_slab(mb,x,y,.215,.165,x-.29,x+.29,y-.235,y+.235,.83,.85,mi_porc)
    _oval_sink(mb,x,y,.85,.215,.165,mi_porc)


def _flush_mount(mb, x, y, zc, mi_glow, mi_trim, size=0.35):
    mb.rbox(x - size / 2, x + size / 2, y - size / 2, y + size / 2, zc - 0.07, zc - 0.01, r=0.02, mi=mi_glow)
    mb.frame(x - size / 2 - 0.01, x + size / 2 + 0.01, y - size / 2 - 0.01, y + size / 2 + 0.01, zc - 0.03, zc, 0.015, mi=mi_trim, axis='Z')


def _semi_flush(mb, x, y, zc, mi_brass, mi_glass):
    mb.cylinder(x, y, zc - 0.03, zc, 0.06, seg=16, mi=mi_brass)
    mb.cylinder(x, y, zc - 0.12, zc - 0.03, 0.012, seg=8, mi=mi_brass)
    mb.lathe(x, y, zc - 0.32, [(0, 0), (0.09, 0.0), (0.15, 0.08), (0.16, 0.18), (0.12, 0.2), (0, 0.2)], seg=20, mi=mi_glass)
    mb.lathe(x, y, zc - 0.13, [(0, 0), (0.05, 0), (0.05, 0.01), (0, 0.01)], seg=12, mi=mi_brass)


def _floor_lamp(mb, x, y, mi_metal, mi_shade):
    mb.lathe(x, y, 0.0, [(0, 0), (0.14, 0), (0.14, 0.02), (0.02, 0.03), (0, 0.03)], seg=16, mi=mi_metal)
    mb.cylinder(x, y, 0.03, 1.45, 0.012, seg=8, mi=mi_metal)
    mb.lathe(x, y, 1.35, [(0.16, 0), (0.2, 0), (0.18, 0.28), (0.14, 0.28)], seg=24, mi=mi_shade)


def _sink_box(mb, x0, x1, y0, y1, ztop, depth, mi, wall=0.02, rim=0.03):
    """Drop-in sink: rim ring on the counter, 4 walls and a bottom (open top)."""
    mb.frame(x0 - rim, x1 + rim, y0 - rim, y1 + rim, ztop, ztop + 0.012, rim, mi=mi, axis='Z')
    mb.box(x0, x0 + wall, y0, y1, ztop - depth, ztop, mi); mb.box(x1 - wall, x1, y0, y1, ztop - depth, ztop, mi)
    mb.box(x0, x1, y0, y0 + wall, ztop - depth, ztop, mi); mb.box(x0, x1, y1 - wall, y1, ztop - depth, ztop, mi)
    mb.box(x0, x1, y0, y1, ztop - depth, ztop - depth + wall, mi)


def _checker(mb, along, a0, a1, b, side, z0, rows, mi_a, mi_b, mi_grout, t=0.15):
    """Checkerboard of 150 mm squares (4 mm gaps over a grout plate) on a wall face."""
    def B(aa0, aa1, bb0, bb1, zz0, zz1, m):
        lo, hi = min(bb0, bb1), max(bb0, bb1)
        if along == 'X':
            mb.box(aa0, aa1, lo, hi, zz0, zz1, m)
        else:
            mb.box(lo, hi, aa0, aa1, zz0, zz1, m)
    B(a0, a1, b, b + side * 0.004, z0, z0 + rows * t, mi_grout)
    n = int((a1 - a0) / t + 0.5)
    w = (a1 - a0) / n
    for i in range(n):
        for j in range(rows):
            m = mi_a if (i + j) % 2 == 0 else mi_b
            B(a0 + i * w + 0.002, a0 + (i + 1) * w - 0.002, b + side * 0.004, b + side * 0.012, z0 + j * t + 0.002, z0 + (j + 1) * t - 0.002, m)


def _louvre_door(mb, y0, y1, x, z0, z1, mi_frame, mi_slat):
    """Louvered bifold panel in the plane x, facing -X, spanning y0..y1."""
    mb.box(x - 0.03, x, y0, y0 + 0.05, z0, z1, mi_frame); mb.box(x - 0.03, x, y1 - 0.05, y1, z0, z1, mi_frame)
    mb.box(x - 0.03, x, y0, y1, z0, z0 + 0.08, mi_frame); mb.box(x - 0.03, x, y0, y1, z1 - 0.08, z1, mi_frame)
    mb.box(x - 0.03, x, y0, y1, z0 + (z1 - z0) / 2 - 0.03, z0 + (z1 - z0) / 2 + 0.03, mi_frame)
    z = z0 + 0.1
    while z < z1 - 0.1:
        if abs(z - (z0 + (z1 - z0) / 2)) > 0.05:
            mb.hexa([(x - 0.026, y0 + 0.05, z), (x - 0.006, y0 + 0.05, z + 0.012), (x - 0.006, y1 - 0.05, z + 0.012), (x - 0.026, y1 - 0.05, z),
                     (x - 0.026, y0 + 0.05, z + 0.008), (x - 0.006, y0 + 0.05, z + 0.02), (x - 0.006, y1 - 0.05, z + 0.02), (x - 0.026, y1 - 0.05, z + 0.008)], mi_slat)
        z += 0.042


def _panel_door_face(mb, along, a0, a1, b, side, z0, z1, mi, mi_knob, knob='a1'):
    """A closed 2-panel painted door face flush in a wall (closets), with a casing and a brass knob."""
    def B(aa0, aa1, bb0, bb1, zz0, zz1, m):
        lo, hi = min(bb0, bb1), max(bb0, bb1)
        if along == 'X':
            mb.box(aa0, aa1, lo, hi, zz0, zz1, m)
        else:
            mb.box(lo, hi, aa0, aa1, zz0, zz1, m)
    B(a0, a1, b, b + side * 0.02, z0, z1, mi)                                   # leaf face
    for (p0, p1) in ((z0 + 0.15, z0 + 0.9), (z0 + 1.05, z1 - 0.15)):            # two recessed panels (raised frames)
        B(a0 + 0.1, a0 + 0.13, b + side * 0.02, b + side * 0.03, p0, p1, mi); B(a1 - 0.13, a1 - 0.1, b + side * 0.02, b + side * 0.03, p0, p1, mi)
        B(a0 + 0.1, a1 - 0.1, b + side * 0.02, b + side * 0.03, p0, p0 + 0.03, mi); B(a0 + 0.1, a1 - 0.1, b + side * 0.02, b + side * 0.03, p1 - 0.03, p1, mi)
    B(a0 - 0.07, a0, b, b + side * 0.025, z0, z1 + 0.07, mi); B(a1, a1 + 0.07, b, b + side * 0.025, z0, z1 + 0.07, mi)   # casing
    B(a0 - 0.07, a1 + 0.07, b, b + side * 0.025, z1, z1 + 0.07, mi)
    ka = a1 - 0.07 if knob == 'a1' else a0 + 0.07
    if along == 'X':
        mb.sphere((ka, b + side * 0.05, z0 + 0.95), 0.025, seg=12, rings=8, mi=mi_knob)
    else:
        mb.sphere((b + side * 0.05, ka, z0 + 0.95), 0.025, seg=12, rings=8, mi=mi_knob)



def _rrect(x0, x1, y0, y1, z, r, seg=4):
    """Rounded-rectangle ring (CCW) at height z."""
    r = max(0.001, min(r, (x1 - x0) / 2 - 1e-4, (y1 - y0) / 2 - 1e-4))
    pts = []
    for (cx, cy, a0) in ((x1 - r, y0 + r, -math.pi / 2), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, math.pi / 2), (x0 + r, y0 + r, math.pi)):
        for k in range(seg + 1):
            a = a0 + math.pi / 2 * k / seg
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a), z))
    return pts


def _tub_shell(mb, x0, x1, y0, y1, z_floor, z_rim, mi, r=0.14):
    """Drop-in tub: a hollow rounded-rectangle shell lofted from a small flat floor up to a rolled rim that laps
    the deck (rim flange 6 cm wide)."""
    secs = []
    for (ins, z, rr) in ((0.16, z_floor, r * 0.5), (0.10, z_floor + 0.05, r * 0.7), (0.05, z_floor + 0.2, r * 0.85), (0.02, z_rim - 0.08, r),
                         (0.0, z_rim - 0.01, r), (-0.02, z_rim + 0.012, r + 0.02), (-0.06, z_rim + 0.012, r + 0.05), (-0.06, z_rim - 0.01, r + 0.05)):
        secs.append(_rrect(x0 + ins, x1 - ins, y0 + ins, y1 - ins, z, rr))
    mb.sweep(secs, mi)


def _register(mb, x, y, z, w=0.3, d=0.1, mi=0, along='X'):
    """Floor register: a flanged plate with angled louvres."""
    if along == 'X':
        mb.box(x - w / 2, x + w / 2, y - d / 2, y + d / 2, z, z + 0.004, mi)
        n = int(w / 0.02)
        for i in range(n):
            xx = x - w / 2 + 0.02 * (i + 0.5)
            mb.box(xx - 0.003, xx + 0.003, y - d / 2 + 0.012, y + d / 2 - 0.012, z + 0.004, z + 0.007, mi)
    else:
        mb.box(x - d / 2, x + d / 2, y - w / 2, y + w / 2, z, z + 0.004, mi)
        n = int(w / 0.02)
        for i in range(n):
            yy = y - w / 2 + 0.02 * (i + 0.5)
            mb.box(x - d / 2 + 0.012, x + d / 2 - 0.012, yy - 0.003, yy + 0.003, z + 0.004, z + 0.007, mi)


def _switch(mb, along, a, b, side, z, mi, n=1):
    """Light-switch plate on a wall face (b, facing `side`), rocker(s) inside."""
    w = 0.07 + 0.045 * (n - 1)
    if along == 'X':
        mb.box(a - w / 2, a + w / 2, b, b + side * 0.008, z - 0.058, z + 0.058, mi)
        for i in range(n):
            aa = a - w / 2 + 0.035 + 0.045 * i
            mb.box(aa - 0.014, aa + 0.014, b + side * 0.008, b + side * 0.013, z - 0.032, z + 0.032, mi)
    else:
        mb.box(b, b + side * 0.008, a - w / 2, a + w / 2, z - 0.058, z + 0.058, mi)
        for i in range(n):
            aa = a - w / 2 + 0.035 + 0.045 * i
            mb.box(b + side * 0.008, b + side * 0.013, aa - 0.014, aa + 0.014, z - 0.032, z + 0.032, mi)


def _framed_art(mb, along, a0, a1, b, side, z0, z1, mi_frame, mi_mat, mi_canvas, fw=0.03, mat=0.06, d=0.03):
    """Framed print with a white mat: frame (depth d) on the wall face b facing `side`."""
    if along == 'X':
        bb0, bb1 = (b, b + side * d) if side > 0 else (b + side * d, b)
        mb.frame(a0, a1, bb0, bb1, z0, z1, fw, mi=mi_frame, axis='Y')
        mb.box(a0 + fw, a1 - fw, bb0 + (0.006 if side > 0 else d - 0.012), bb1 - (d - 0.012 if side > 0 else 0.006), z0 + fw, z1 - fw, mi_mat)
        mb.box(a0 + fw + mat, a1 - fw - mat, bb0 + (0.009 if side > 0 else d - 0.012), bb1 - (d - 0.012 if side > 0 else 0.009), z0 + fw + mat, z1 - fw - mat, mi_canvas)
    else:
        bb0, bb1 = (b, b + side * d) if side > 0 else (b + side * d, b)
        mb.frame(bb0, bb1, a0, a1, z0, z1, fw, mi=mi_frame, axis='X')
        mb.box(bb0 + (0.006 if side > 0 else d - 0.012), bb1 - (d - 0.012 if side > 0 else 0.006), a0 + fw, a1 - fw, z0 + fw, z1 - fw, mi_mat)
        mb.box(bb0 + (0.009 if side > 0 else d - 0.012), bb1 - (d - 0.012 if side > 0 else 0.009), a0 + fw + mat, a1 - fw - mat, z0 + fw + mat, z1 - fw - mat, mi_canvas)


def _curtains(mb, along, a0, a1, b, side, z_rod, z_bot, mi_fabric, mi_rod, panel_w=0.38, folds=7, seed=0):
    """Rod with finials + brackets over an opening (a0..a1 on the face b facing `side`), a wavy linen panel stacked at each end."""
    rng = random.Random(seed)
    off = 0.11
    def P(a, bb, z):
        return (a, bb, z) if along == 'X' else (bb, a, z)
    r0, r1 = a0 - panel_w - 0.05, a1 + panel_w + 0.05
    mb.path_tube([P(r0, b + side * off, z_rod), P(r1, b + side * off, z_rod)], 0.012, seg=10, mi=mi_rod)
    for a in (r0, r1):
        mb.sphere(P(a, b + side * off, z_rod), 0.022, seg=12, rings=8, mi=mi_rod)
    for a in (a0 - 0.1, a1 + 0.1):
        mb.path_tube([P(a, b, z_rod), P(a, b + side * off, z_rod)], 0.006, seg=6, mi=mi_rod)
        if along == 'X':
            mb.box(a - 0.02, a + 0.02, b, b + side * 0.008, z_rod - 0.03, z_rod + 0.03, mi_rod)
        else:
            mb.box(b, b + side * 0.008, a - 0.02, a + 0.02, z_rod - 0.03, z_rod + 0.03, mi_rod)
    for (pa0, pa1) in ((a0 - panel_w - 0.02, a0 + 0.03), (a1 - 0.03, a1 + panel_w + 0.02)):
        n = max(8, int((pa1 - pa0) / 0.03))
        ph = rng.uniform(0, 6)
        secs = []
        for i in range(n + 1):
            t = i / n
            a = pa0 + (pa1 - pa0) * t
            dep = off + 0.03 * math.sin(2 * math.pi * folds * t + ph) + 0.012 * math.sin(2 * math.pi * folds * 2.3 * t + 1.7)
            secs.append([P(a, b + side * (dep + 0.006), z_rod - 0.02), P(a, b + side * (dep - 0.006), z_rod - 0.02),
                         P(a, b + side * (dep - 0.006 + 0.015), z_bot), P(a, b + side * (dep + 0.006 + 0.015), z_bot)])
        mb.sweep(secs, mi_fabric)
        for i in range(6):
            a = pa0 + (pa1 - pa0) * (i + 0.5) / 6
            mb.cylinder(*(P(a, b + side * off, z_rod)[:2]), z_rod - 0.02, z_rod + 0.02, 0.016, seg=10, mi=mi_rod)


def _nightstand2(mb, x, y, w, d, h, mi_body, mi_pull, front='-Y'):
    """Nightstand: box on tapered legs with one drawer + a brass bar pull on the `front` side."""
    mb.box(x - w / 2, x + w / 2, y - d / 2, y + d / 2, 0.14, h, mi_body)
    mb.box(x - w / 2 - 0.01, x + w / 2 + 0.01, y - d / 2 - 0.01, y + d / 2 + 0.01, h, h + 0.02, mi_body)
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.cylinder(x + sx * (w / 2 - 0.05), y + sy * (d / 2 - 0.05), 0.0, 0.14, 0.018, 0.014, seg=8, mi=mi_body)
    fy, s = (y - d / 2, -1) if front == '-Y' else (y + d / 2, +1)
    mb.box(x - w / 2 + 0.02, x + w / 2 - 0.02, fy + s * 0.001, fy + s * 0.012, h - 0.20, h - 0.03, mi_body)   # drawer front, proud
    mb.box(x - 0.06, x + 0.06, fy + s * 0.012, fy + s * 0.035, h - 0.12, h - 0.10, mi_pull)                      # bar pull
    for sx in (-1, 1):
        mb.cylinder(x + sx * 0.05, fy + s * 0.02, h - 0.115, h - 0.105, 0.005, seg=6, mi=mi_pull)


def _lamp2(mb, x, y, z, mi_base, mi_shade, mi_metal, base_r=0.1, base_h=0.28, shade_r=0.17, shade_h=0.2):
    """Table lamp with a visible harp + finial; shade slightly translucent (its material glows)."""
    lamp(mb, x, y, z, mi_base=mi_base, mi_shade=mi_shade, base_r=base_r, base_h=base_h, shade_r=shade_r, shade_h=shade_h)
    zt = z + base_h + 0.08 + shade_h
    mb.cylinder(x, y, z + base_h + 0.06, zt + 0.02, 0.004, seg=6, mi=mi_metal)
    mb.sphere((x, y, zt + 0.03), 0.012, seg=8, rings=6, mi=mi_metal)
    mb.lathe(x, y, z + base_h + 0.02, [(0, 0), (0.02, 0), (0.02, 0.06), (0, 0.06)], seg=10, mi=mi_metal)    # socket


def _louvre_door_x(mb, x0, x1, y, z0, z1, mi_frame, mi_slat, side=-1):
    """Louvered panel in the plane y, facing `side` (-1 = room on the -Y side), spanning x0..x1."""
    yo, yi = y + side * 0.03, y
    lo, hi = min(yo, yi), max(yo, yi)
    mb.box(x0, x0 + 0.05, lo, hi, z0, z1, mi_frame); mb.box(x1 - 0.05, x1, lo, hi, z0, z1, mi_frame)
    mb.box(x0, x1, lo, hi, z0, z0 + 0.08, mi_frame); mb.box(x0, x1, lo, hi, z1 - 0.08, z1, mi_frame)
    zm = z0 + (z1 - z0) / 2
    mb.box(x0, x1, lo, hi, zm - 0.03, zm + 0.03, mi_frame)
    z = z0 + 0.1
    while z < z1 - 0.1:
        if abs(z - zm) > 0.05:
            a, bb = y + side * 0.026, y + side * 0.006
            mb.hexa([(x0 + 0.05, a, z), (x0 + 0.05, bb, z + 0.012), (x1 - 0.05, bb, z + 0.012), (x1 - 0.05, a, z),
                     (x0 + 0.05, a, z + 0.008), (x0 + 0.05, bb, z + 0.02), (x1 - 0.05, bb, z + 0.02), (x1 - 0.05, a, z + 0.008)], mi_slat)
        z += 0.042



def _closet(mb, along, a0, a1, b_back, b_face, mi_wall, mi_trim, mi_knob, mi_rod, mi_garments, ajar=0.0, z_top=Z_MC):
    """Built-in closet box against the wall plane b_back, its door face at b_face (facing away from b_back):
    cheeks + header + top, a cased opening with two flat 2-panel leaves + brass knobs, a rod with garments and a
    top shelf inside; `ajar` (radians) swings the a0-side leaf open into the room."""
    side = 1 if b_face > b_back else -1
    lo, hi = min(b_back, b_face), max(b_back, b_face)
    def B(aa0, aa1, bb0, bb1, z0, z1, mi):
        bb0, bb1 = min(bb0, bb1), max(bb0, bb1)
        if along == 'X':
            mb.box(aa0, aa1, bb0, bb1, z0, z1, mi)
        else:
            mb.box(bb0, bb1, aa0, aa1, z0, z1, mi)
    def P(a, bb, z):
        return (a, bb, z) if along == 'X' else (bb, a, z)
    B(a0, a0 + 0.1, lo, hi, 0.0, z_top, mi_wall); B(a1 - 0.1, a1, lo, hi, 0.0, z_top, mi_wall)
    B(a0, a1, lo, hi, 2.12, z_top, mi_wall)                                                            # top / header mass
    B(a0 + 0.1, a1 - 0.1, b_face - side * 0.04, b_face, 2.05, 2.12, mi_trim)
    B(a0 + 0.1, a1 - 0.1, lo, hi, 0.0, 0.012, mi_wall)                                                 # closet floor
    B(a0 + 0.1, a1 - 0.1, b_back, b_back + side * 0.3, 1.9, 1.92, mi_trim)                             # top shelf
    # casing round the opening (proud of the face)
    if along == 'X':
        mb.frame(a0 + 0.03, a1 - 0.03, b_face, b_face + side * 0.02, 0.0, 2.19, 0.07, mi=mi_trim, axis='Y')
    else:
        mb.frame(b_face, b_face + side * 0.02, a0 + 0.03, a1 - 0.03, 0.0, 2.19, 0.07, mi=mi_trim, axis='X')
    # rod + garments
    mb.path_tube([P(a0 + 0.1, (lo + hi) / 2, 1.78), P(a1 - 0.1, (lo + hi) / 2, 1.78)], 0.012, seg=10, mi=mi_rod)
    n = int((a1 - a0 - 0.4) / 0.11)
    rng = random.Random(int(a0 * 7) & 255)
    for i in range(n):
        a = a0 + 0.25 + 0.11 * i
        hgt = rng.uniform(0.75, 1.1)
        mi_g = mi_garments[i % len(mi_garments)]
        if along == 'X':
            mb.rbox(a - 0.02, a + 0.02, (lo + hi) / 2 - 0.2, (lo + hi) / 2 + 0.2, 1.72 - hgt, 1.72, r=0.008, mi=mi_g, seg=2)
        else:
            mb.rbox((lo + hi) / 2 - 0.2, (lo + hi) / 2 + 0.2, a - 0.02, a + 0.02, 1.72 - hgt, 1.72, r=0.008, mi=mi_g, seg=2)
        mb.path_tube([P(a, (lo + hi) / 2, 1.72), P(a, (lo + hi) / 2, 1.79)], 0.003, seg=5, mi=mi_rod)
    # two flat 2-panel leaves (0.04 thick) in the opening; the a0 leaf may be ajar
    oa0, oa1 = a0 + 0.1, a1 - 0.1
    w = (oa1 - oa0) / 2 - 0.006
    for k in (0, 1):
        ha = oa0 + 0.003 if k == 0 else oa1 - 0.003                                                   # hinge line
        sgn = 1 if k == 0 else -1
        ang = ajar * (1 if k == 0 else 0)
        if along == 'X':
            rot = ang * side * -1
        else:
            rot = ang * side
        def LB(u0, u1, v0, v1, z0, z1, mi):
            """Box in leaf coordinates: u along the leaf from its hinge (0..w), v across its thickness (0 = face plane, + toward the room)."""
            cu, cv = (u0 + u1) / 2, (v0 + v1) / 2
            if along == 'X':
                cx0, cy0 = ha + sgn * cu, b_face + side * cv
                px, py = rot2(cx0, cy0, ha, b_face, rot)
                mb.cbox(px, py, (z0 + z1) / 2, u1 - u0, v1 - v0, z1 - z0, mi, rot)
            else:
                cx0, cy0 = b_face + side * cv, ha + sgn * cu
                px, py = rot2(cx0, cy0, b_face, ha, rot)
                mb.cbox(px, py, (z0 + z1) / 2, v1 - v0, u1 - u0, z1 - z0, mi, rot)
        LB(0, w, -0.04, 0.0, 0.02, 2.04, mi_trim)                                                     # leaf slab
        for (p0, p1) in ((0.15, 0.9), (1.05, 1.9)):                                                  # two raised panel frames
            LB(0.09, 0.12, 0.0, 0.01, p0, p1, mi_trim); LB(w - 0.12, w - 0.09, 0.0, 0.01, p0, p1, mi_trim)
            LB(0.09, w - 0.09, 0.0, 0.01, p0, p0 + 0.03, mi_trim); LB(0.09, w - 0.09, 0.0, 0.01, p1 - 0.03, p1, mi_trim)
        # knob near the meeting stile
        ku = w - 0.07
        if along == 'X':
            kx, ky = rot2(ha + sgn * ku, b_face + side * 0.03, ha, b_face, rot)
        else:
            kx, ky = rot2(b_face + side * 0.03, ha + sgn * ku, b_face, ha, rot)
        mb.sphere((kx, ky, 0.98), 0.02, seg=10, rings=6, mi=mi_knob)


def _towel_bar(mb, along, a0, a1, b, side, z, mi_metal, mi_towel, towel=True):
    """Wall towel bar with posts and a folded towel hanging over it."""
    def P(a, bb, zz):
        return (a, bb, zz) if along == 'X' else (bb, a, zz)
    mb.path_tube([P(a0, b + side * 0.07, z), P(a1, b + side * 0.07, z)], 0.008, seg=8, mi=mi_metal)
    for a in (a0, a1):
        mb.path_tube([P(a, b, z), P(a, b + side * 0.07, z)], 0.006, seg=6, mi=mi_metal)
        if along == 'X':
            mb.cylinder(a, b + side * 0.004, z - 0.02, z + 0.02, 0.018, seg=10, mi=mi_metal)
        else:
            mb.cylinder(b + side * 0.004, a, z - 0.02, z + 0.02, 0.018, seg=10, mi=mi_metal)
    if towel:
        ta0, ta1 = a0 + 0.06, a1 - 0.06
        if along == 'X':
            mb.rbox(ta0, ta1, min(b + side * 0.03, b + side * 0.10), max(b + side * 0.03, b + side * 0.10), z - 0.42, z + 0.012, r=0.012, mi=mi_towel, seg=3)
        else:
            mb.rbox(min(b + side * 0.03, b + side * 0.10), max(b + side * 0.03, b + side * 0.10), ta0, ta1, z - 0.42, z + 0.012, r=0.012, mi=mi_towel, seg=3)


def _pillows(mb, x, y, z, rot, mi, n=2, w=0.48, gap=0.02, seed=0):
    """Throw pillows standing along a sofa back: centred at (x, y) on the seat, leaning back, facing the sofa's -Y."""
    rng = random.Random(seed)
    for i in range(n):
        cx = (i - (n - 1) / 2) * (w + gap)
        px, py = rot2(x + cx, y, x, y, rot)
        mb.pillow_sq(px, py, z + w * 0.44, w, w, 0.15, mi, rot=rot + rng.uniform(-0.06, 0.06), pitch=math.pi / 2 - 0.3, seed=seed + i)


def _smoke_detector(mb, x, y, zc, mi):
    mb.lathe(x, y, zc - 0.035, [(0, 0), (0.06, 0), (0.065, 0.02), (0.05, 0.035), (0, 0.035)], seg=20, mi=mi)


# ================================================================== rooms
def finishes(M):
    L = _local(M)
    # ---- floors
    _floor("Back_Floor_Hall", M, -1.25, -0.3, 5.0, 12.90, M['maple'])
    _floor("Back_Floor_Hall2", M, 2.1, 3.35, 11.3, 13.75, M['maple'])
    _floor("Back_Floor_Family", M, -0.15, 3.25, 13.6, FAMILY_REAR, M['maple'])
    _floor("Back_Floor_Kitchen", M, 1.5, 5.5, 7.1, 11.15, M['maple_y'])
    _floor("Back_Floor_BedA", M, -5.5, -1.4, 5.9, 9.9, M['maple'])
    _floor("Back_Floor_BedB", M, -5.5, -0.3, 12.9, BED_REAR, M['maple'])
    lf=MB()
    from .exterior import _plate_holes
    _plate_holes(lf,3.5,5.5,11.3,13.6,0.,FL,[(4.4,5.5,11.3,12.65)],0)
    lf.build('Back_Floor_Laundry',[M['tile_bath_floor']],coll='House')
    mb = MB()
    mb.box(-5.5,-1.4,10.05,12.75,0,FL)
    mb.build("Back_Floor_Baths", [M['tile_bath_floor']], coll='House')
    # ---- mouldings
    mb = MB()
    for r in ('hall2', 'kitchen', 'laundry', 'family', 'half', 'bath_a', 'bed_b'):
        _trims(mb, FACES[r])
    _trims(mb, FACES['hall'], rail=True)
    _trims(mb, FACES['bed_a'], rail=True)
    mb.build("Back_Trims", [M['trim']], coll='House', smooth=True)
    mb = MB()
    _lower_wall(mb, FACES['hall']); _lower_wall(mb, FACES['bed_a'])
    mb.build("Back_LowerWalls", [L['wall_dark']], coll='House')


def kitchen(M):
    L = _local(M)
    X0, X1, Y0, Y1 = 2.1, 5.5, 7.1, 11.15
    CT = 0.9                                                      # counter top
    cab = MB()                                                    # 0 cabinet, 1 knob
    # ---- +X wall run: base cabinets + dishwasher, uppers flanking the garden window
    _cabinet_run(cab, 'Y', Y0, 9.98, 5.5, 0.58, -1, 0, CT - 0.03, 0, 1, door_w=0.5,hollow=True)
    _cabinet_run(cab, 'Y', 10.62, Y1, 5.5, 0.58, -1, 0, CT - 0.03, 0, 1, door_w=0.5, drawers=True)
    cab.box(4.92, 5.5, 9.98, 10.62, 0.1, CT - 0.03, 0)            # dishwasher carcass (front is the appliance panel)
    from .fixtures import glazed_upper, original_backsplash
    glazed_upper(cab,Y0,8.2,5.5,1.5,2.35)
    glazed_upper(cab,10.6,Y1,5.5,1.5,2.35)
    cab.box(5.18, 5.5, 8.2, 10.6, 2.2, 2.35, 0)                    # header over the window
    # Original appliance order, from dining toward the rear: fridge, cooktop, wall oven.
    _cabinet_run(cab,'Y',8.20,9.95,2.1,.60,1,0,CT-.03,0,1,door_w=.55)
    _cabinet_run(cab,'Y',10.55,11.10,2.1,.60,1,0,CT-.03,0,1,drawers=True)
    cab.box(2.1,2.70,9.95,10.55,.1,2.35,0)
    _shaker_door(cab,'Y',9.97,10.53,2.7,1,1.95,2.33,0,1)
    cab.box(2.1,2.75,7.2,8.1,1.85,2.35,0)
    _shaker_door(cab,'Y',7.22,7.65,2.75,1,1.87,2.33,0,1)
    _shaker_door(cab,'Y',7.66,8.08,2.75,1,1.87,2.33,0,1,knob='a0')
    for ya,yb in ((8.2,8.6),(9.6,9.95),(10.55,11.1)):
        _cabinet_run(cab,'Y',ya,yb,2.1,.32,1,1.5,2.35,0,1,door_w=.5)
    cab.box(2.1,2.55,8.6,9.6,1.45,2.35,0)
    _shaker_door(cab,'Y',8.62,9.1,2.55,1,1.72,2.33,0,1)
    _shaker_door(cab,'Y',9.11,9.58,2.55,1,1.72,2.33,0,1,knob='a0')
    cab.build("Back_KitCabinets", [M['cabinet'], M['steel'], M['glass']], coll='House')
    # ---- counters (green tile) with the sink hole, bullnose edges, backsplash row + deco band
    ct = MB()                                                     # 0 tile top, 1 tile YZ (backsplash), 2 deco YZ, 3 bullnose
    ct.plate(4.9, 5.5, Y0, Y1, CT, CT + 0.03, holes=[(4.98, 5.46, 8.98, 9.83)], mi=0)
    ct.rbox(4.87, 4.92, Y0, Y1, CT - 0.01, CT + 0.035, r=0.012, mi=3)
    ct.plate(2.1, 2.7, 8.2, 9.95, CT, CT + 0.03, mi=0); ct.plate(2.1, 2.7, 10.55, 11.1, CT, CT + 0.03, mi=0)
    ct.rbox(2.68, 2.73, 8.2, 9.95, CT - 0.01, CT + 0.035, r=0.012, mi=3); ct.rbox(2.68, 2.73, 10.55, 11.1, CT - 0.01, CT + 0.035, r=0.012, mi=3)
    ct.box(5.488, 5.5, Y0, Y1, CT + 0.03, 1.0, 1)                  # green row
    ct.box(5.488, 5.5, Y0, 8.3, 1.0, 1.15, 2); ct.box(5.488, 5.5, 10.5, Y1, 1.0, 1.15, 2)      # deco band beside the window
    for ya,yb in ((8.2,9.95),(10.55,11.1)):
        ct.box(2.1,2.112,ya,yb,CT+.03,1.0,1)
        ct.box(2.1,2.112,ya,yb,1.0,1.15,2)
    ct.box(2.1,2.112,8.55,9.65,1.42,1.5,2)
    # the counter continues into the greenhouse window (its sill = the counter; the box is exterior's)
    ct.box(5.5, 5.5 + 0.43, 8.32, 10.48, CT + 0.005, CT + 0.03, 0)
    ct.build("Back_KitCounters", [M['tile_green'], M['tile_green_vy'], M['tile_deco_y'], M['tile_green']], coll='House')
    mir = MB(); mir.box(2.112, 2.116, 8.63, 9.57, 1.08, 1.42); mir.build("Back_KitMirror", [M['mirror']], coll='House')
    # ---- appliances + sink + fixtures
    ap = MB()                                                     # 0 white appliance, 1 steel, 2 black gloss, 3 porcelain, 4 chrome, 5 dial
    _sink_box(ap, 5.0, 5.44, 9.0, 9.81, CT + 0.03, 0.2, 3)
    ap.lathe(5.4, 9.42, CT + 0.03, [(0, 0), (0.03, 0), (0.028, 0.02), (0.016, 0.03), (0, 0.03)], seg=14, mi=4)          # escutcheon
    ap.path_tube([(5.4, 9.42, CT + 0.05), (5.4, 9.42, CT + 0.28), (5.36, 9.42, CT + 0.35), (5.28, 9.42, CT + 0.37),
                  (5.2, 9.42, CT + 0.34), (5.17, 9.42, CT + 0.29)], 0.011, seg=10, mi=4)                                    # gooseneck spout
    ap.cylinder(5.17, 9.42, CT + 0.27, CT + 0.29, 0.014, seg=10, mi=4)
    ap.tube((5.4, 9.42, CT + 0.2), (5.4, 9.55, CT + 0.24), 0.008, 0.006, seg=8, mi=4)                                       # lever
    ap.lathe(5.4, 9.05, CT + 0.03, [(0, 0), (0.025, 0), (0.026, 0.08), (0.02, 0.1), (0.008, 0.11), (0.008, 0.14), (0, 0.14)], seg=12, mi=3)   # soap dispenser
    ap.tube((5.4, 9.05, CT + 0.17), (5.4, 8.99, CT + 0.16), 0.006, 0.005, seg=6, mi=4)
    ap.box(2.72, 2.755, 10.01, 10.49, 1.265, 1.29, 1); ap.box(2.755, 2.77, 10.01, 10.49, 1.26, 1.295, 1)                       # oven handle
    ap.rbox(2.757, 2.775, 10.11, 10.39, 0.92, 1.29, r=0.006, mi=0, seg=2)                                                     # tea towel over it
    ap.box(4.905, 4.925, 10.0, 10.6, 0.1, CT - 0.04, 0)              # dishwasher front
    ap.box(4.9, 4.905, 10.02, 10.58, CT - 0.11, CT - 0.05, 5)
    # oven column: oven with a dark window, warming niche above
    ap.box(2.7, 2.72, 9.97, 10.53, 0.72, 1.45, 0); ap.box(2.72, 2.728, 10.03, 10.47, 0.85, 1.25, 2)
    ap.box(2.7, 2.705, 10.0, 10.5, 1.3, 1.36, 5)
    ap.box(2.7, 2.72, 9.97, 10.53, 0.1, 0.72, 0); ap.box(2.7, 2.72, 9.97, 10.53, 1.45, 1.95, 0); ap.box(2.72, 2.728, 10.03, 10.47, 1.55, 1.85, 2)
    # cooktop: black glass inset with four rings
    ap.box(2.16, 2.66, 8.7, 9.5, CT + 0.03, CT + 0.036, 2)
    for (cx, cy) in ((2.3, 8.85), (2.52, 8.85), (2.3, 9.35), (2.52, 9.35)):
        ap.lathe(cx, cy, CT + 0.036, [(0.06, 0), (0.09, 0), (0.09, 0.003), (0.06, 0.003)], seg=20, mi=5)
    ap.box(2.55, 2.59, 8.6, 9.6, 1.45, 1.47, 1)                     # hood underside (stainless lip)
    # stainless counter-depth fridge (0.65 deep)
    ap.rbox(2.1, 2.75, 7.2, 8.1, 0.0, 1.83, r=0.01, mi=1)
    ap.box(2.75, 2.754, 7.22, 7.64, 0.05, 1.8, 5); ap.box(2.75, 2.754, 7.66, 8.08, 0.05, 1.8, 5)       # door reveals (dial grey lines)
    ap.box(2.755, 2.775, 7.6, 7.63, 0.7, 1.55, 1); ap.box(2.755, 2.775, 7.67, 7.7, 0.7, 1.55, 1)     # pulls
    ap.build("Back_KitAppliances", [M['appliance'], M['steel'], M['black_gloss'], M['porcelain'], M['chrome'], L['dial']], coll='House', smooth=True)
    original_backsplash(M)
    # ---- ceiling cans + under-cabinet strips
    ce = MB()                                                     # 0 lens, 1 trim, 2 strip
    pts = [(x, y) for x in (3.0, 4.4) for y in (7.9, 9.2, 10.5)]
    downlights(ce, pts, Z_MC, r=0.055, mi=0, mi_trim=1)
    for (ya, yb) in ((Y0 + 0.03, 8.17), (10.63, Y1 - 0.03)):
        ce.box(5.2, 5.46, ya, yb, 1.49, 1.5, 2)
        ce.box(5.16, 5.19, ya - 0.01, yb + 0.01, 1.46, 1.52, 3)                                      # light rail hiding the strip
    _switch(ce, 'X', 3.45, 11.15, -1, 1.2, 4, n=2)
    _switch(ce, 'X', 3.45, 7.1, +1, 1.2, 4)
    ce.build("Back_KitCeilingLights", [M['emit_down'], M['trim'], M['emit_cove'], M['cabinet'], L['plate']], coll='House')
    for i, (x, y) in enumerate(pts):
        add_light(f"L_Back_KitCan{i}", 'SPOT', (x, y, Z_MC - 0.03), 22, K30, size=0.04, spot=math.radians(70), blend=0.5)
    for i, (ya, yb) in enumerate(((Y0 + 0.03, 8.17), (10.63, Y1 - 0.03))):
        area_light(f"L_Back_KitStrip{i}", (5.33, (ya + yb) / 2, 1.47), (0.2, yb - ya - 0.1), 6, K30)
    # Preserve the approved film's fill-light placement when the backing wall is recessed.
    room_light("L_Back_KitFill", (2.1,5.5,7.1,11.15,0.,Z_MC), energy=6, color=K30)
    # ---- staging
    st = MB()                                                     # 0 board wood, 1 lemon, 2 steel, 3 clay, 4 branch, 5 leaf
    st.lathe(5.2, 8.0, CT + 0.03, [(0, 0), (0.12, 0), (0.17, 0.05), (0.18, 0.08), (0.16, 0.085), (0.14, 0.02), (0, 0.02)], seg=20, mi=0)   # bowl
    rng = random.Random(7)
    for i in range(7):
        a = 2 * math.pi * i / 7
        r = 0.09 if i < 6 else 0.0
        st.blob((5.2 + r * math.cos(a), 8.0 + r * math.sin(a), CT + 0.03 + 0.05 + (0.06 if i == 6 else 0)), 0.038, seg=10, rings=7, mi=1, squash=0.85, rx=1.15)
    st.rbox(5.05, 5.4, 10.75, 11.05, CT + 0.03, CT + 0.05, r=0.006, mi=0)                            # cutting board
    st.lathe(2.4, 9.65, CT + 0.03, [(0, 0), (0.09, 0), (0.1, 0.06), (0.08, 0.16), (0.03, 0.19), (0.03, 0.21), (0, 0.21)], seg=20, mi=2)   # kettle
    st.path_tube([(2.4, 9.65, CT + 0.2), (2.4, 9.65, CT + 0.29), (2.4, 9.58, CT + 0.3), (2.4, 9.5, CT + 0.24)], 0.008, seg=6, mi=2)
    vase(st, 5.25, 7.35, CT + 0.03, h=0.32, r=0.09, mi=3, style='tall')
    st.hexa([(2.2, 10.78, CT + 0.03), (2.42, 10.78, CT + 0.03), (2.42, 10.98, CT + 0.03), (2.2, 10.98, CT + 0.03),
             (2.2, 10.78, CT + 0.2), (2.42, 10.78, CT + 0.13), (2.42, 10.98, CT + 0.13), (2.2, 10.98, CT + 0.2)], 0)             # knife block
    for k in range(4):
        st.box(2.24 + k * 0.045, 2.26 + k * 0.045, 10.85, 10.91, CT + 0.19 - k * 0.016, CT + 0.29 - k * 0.016, 2)
    st.lathe(2.45, 10.6, CT + 0.03, [(0, 0), (0.07, 0), (0.07, 0.012), (0.012, 0.014), (0.012, 0.3), (0, 0.3)], seg=12, mi=2)   # paper-towel holder
    st.cylinder(2.45, 10.6, CT + 0.06, CT + 0.28, 0.06, seg=16, mi=6)
    st.build("Back_KitStaging", [L['board'], L['lemon'], M['steel'], M['clay'], M['bark'], M['leaf_plant'], M['paper']], coll='House', smooth=True)
    _pl.stems("Back_KitStems", (5.25, 7.35, CT + 0.35), kind='eucalyptus', height=0.5, seed=3)
    _pl.potted("Back_KitHerb1", (5.74, 8.62, CT + 0.03), kind='rosemary', height=0.2, pot='terracotta', pot_r=0.065, pot_h=0.085, seed=11)
    _pl.potted("Back_KitHerb2", (5.74, 10.2, CT + 0.03), kind='lavender', height=0.2, pot='terracotta', pot_r=0.065, pot_h=0.085, seed=12)
    _pl.potted("Back_KitFern", (5.76, 9.42, CT + 0.03), kind='fern', height=0.22, pot='ceramic', pot_r=0.07, pot_h=0.09, seed=13)
    _rug("Back_Rug_Kitchen", M, 3.8, 9.2, 0.7, 2.0, M['rug_blue'], t=0.01)
    # The entire west run sits behind both doorway edges; keep its dimensions and appliance order.
    from .kitchen_recess import recess_fixtures
    recess_fixtures()


def laundry(M):
    L = _local(M)
    ap = MB()                                                     # 0 appliance, 1 dial, 2 dark glass, 3 cabinet, 4 knob, 5 porcelain, 6 chrome
    for i,x0 in enumerate((3.53,4.26)):
        ap.rbox(x0,x0+.68,12.9,13.58,.02,.96,r=.025,mi=0,seg=4)
        ap.rbox(x0+.015,x0+.665,13.46,13.57,.96,1.15,r=.035,mi=0,seg=4)
        ap.box(x0+.06,x0+.62,13.453,13.461,1.012,1.105,0)
        for dx in (.13,.33,.53):
            ap.tube((x0+dx,13.447,1.06),(x0+dx,13.418,1.06),.025,.023,seg=24,mi=1)
        if i==0:
            ap.rbox(x0+.045,x0+.635,12.97,13.42,.958,.964,r=.018,mi=1)
            ap.rbox(x0+.052,x0+.628,12.977,13.414,.964,.975,r=.018,mi=0)
        else:
            # The dryer door is vertical, not a horizontal disc protruding into the aisle.
            ap.tube((x0+.34,12.90,.49),(x0+.34,12.881,.49),.235,.235,seg=48,mi=1)
            ap.tube((x0+.34,12.879,.49),(x0+.34,12.873,.49),.215,.215,seg=48,mi=0)
            ap.box(x0+.49,x0+.535,12.854,12.874,.58,.64,0)
    ap.build("Back_LauAppliances", [M['appliance'], L['dial'], M['black_gloss'], M['cabinet'], M['steel'], M['porcelain'], M['chrome']], coll='House', smooth=True)
    cab = MB()                                                    # 0 cabinet, 1 knob
    _cabinet_run(cab, 'X', 3.52, 5.48, 13.6, 0.32, -1, 1.7, 2.35, 0, 1, door_w=0.5)          # uppers over the machines
    _cabinet_run(cab, 'Y', 11.5, 12.7, 3.5, 0.58, +1, 0, 0.87, 0, 1, door_w=0.6,hollow=True)             # counter run on the -X wall
    cab.build("Back_LauCabinets", [M['cabinet'], M['steel']], coll='House')
    ct = MB()                                                     # 0 counter (white laminate), 1 porcelain, 2 chrome
    ct.plate(3.5, 4.1, 11.5, 12.7, 0.87, 0.9, holes=[(3.62, 3.98, 11.65, 12.15)], mi=0)
    _sink_box(ct, 3.62, 3.98, 11.65, 12.15, 0.9, 0.25, 1)
    faucet(ct, 3.55, 11.9, 0.91, h=0.25, mi=2, reach=0.15, dir=(1, 0))
    ct.build("Back_LauCounter", [M['acrylic_white'], M['porcelain'], M['chrome']], coll='House', smooth=True)
    mb = MB()
    _flush_mount(mb, 4.5, 12.45, Z_MC, 0, 1, size=0.3)
    mb.build("Back_LauLight", [L['emit_flush'], M['trim']], coll='House')
    area_light("L_Back_LauCeiling", (4.5, 12.45, Z_MC - 0.09), (0.3, 0.3), 30, K30)


def family(M):
    L = _local(M)
    # ---- closet bump-out with louvered bifold doors, the 'mid' closet door face on the -Y wall
    cl = MB()                                                     # 0 wall, 1 trim, 2 louvre, 3 brass
    cl.box(2.65, 3.25, 14.2, 15.75, 0.0, Z_MC, 0)
    cl.box(2.62, 2.65, 14.2, 14.26, 0.0, 2.12, 1); cl.box(2.62, 2.65, 15.69, 15.75, 0.0, 2.12, 1); cl.box(2.62, 2.65, 14.2, 15.75, 2.05, 2.12, 1)
    for ya,yb in ((14.27,14.98),(14.99,15.68)):
        _panel_door_face(cl,'Y',ya,yb,2.65,-1,.03,2.04,1,3)
    _trims(cl, [('Y', 14.2, 15.75, 2.65, -1), ('X', 2.65, 3.25, 14.2, -1), ('X', 2.65, 3.25, 15.75, +1)], mi=1)
    _panel_door_face(cl, 'X', 1.3, 2.05, 13.75, +1, 0.0, 2.05, 1, 3, knob='a0')
    cl.build("Back_FamCloset", [M['wall'], M['trim'], L['louvre'], M['brass']], coll='House')
    # ---- media wall: walnut console + TV
    md = MB()                                                     # 0 walnut, 1 tv body, 2 screen, 3 black metal
    md.rbox(-0.25, 1.15, 13.78, 14.22, 0.12, 0.52, r=0.01, mi=0)
    for x in (-0.2, 1.1):
        md.cylinder(x, 13.85, 0.0, 0.12, 0.015, seg=8, mi=3); md.cylinder(x, 14.15, 0.0, 0.12, 0.015, seg=8, mi=3)
    md.box(-0.24, 1.14, 13.79, 14.21, 0.3, 0.304, 3)               # drawer reveal line
    tv(md, 0.05, 1.05, 13.83, 0.72, 1.3, mi=1, along='X', d=0.035)
    md.box(0.06, 1.04, 13.83, 13.832, 0.73, 1.29, 2)
    books(md, -0.1, 14.0, 0.52, n=3, mi=0, rot=0.3, w=0.24, d=0.2)
    md.v=[(x+.22,y,z) for x,y,z in md.v]
    md.build("Back_FamMedia", [M['walnut'], M['tv'], L['tv_screen'], M['black_metal']], coll='House', smooth=True)
    # ---- seating
    sf = MB()                                                     # 0 fabric grey, 1 pillow, 2 leather tan, 3 legs
    sofa(sf, -0.8, 15.2, 2.2, 0.9, rot=math.pi / 2, mi_seat=0, mi_back=0, mi_base=0, cushion_gap=0.02, pillows=0)
    _pillows(sf, -0.89, 15.2, 0.42, math.pi / 2, 1, n=3, w=0.46, seed=3)
    sf.rbox(-1.22, -0.98, 15.98, 16.12, 0.62, 0.65, r=0.01, mi=1, puff=0.5, seg=2)                 # throw folded on the arm
    sf.rbox(-1.245, -1.222, 16.0, 16.1, 0.35, 0.63, r=0.008, mi=1, seg=2)
    armchair(sf, 2.55, 16.5, rot=-math.pi / 2, w=0.78, d=0.8, mi=2, mi_legs=3, style='barrel')
    sf.v=[(x+1.10 if x<0 else x,y,z) for x,y,z in sf.v]
    sf.build("Back_FamSeating", [M['fabric_grey'], M['fabric_sand'], M['leather_tan'], M['black_metal']], coll='House', smooth=True, subsurf=1)
    _rug("Back_Rug_Family", M, 1.35, 15.8, 2.4, 1.8, M['rug'])
    # ---- side table, floor lamp, plant, flush mount
    ac = MB()                                                     # 0 walnut, 1 black metal, 2 shade, 3 pot, 4 leaf, 5 stem, 6 glow, 7 trim
    round_table(ac, 1.15, 15.6, FL, 0.28, h=0.45, mi=0, mi_leg=1, legs='three')
    _floor_lamp(ac, 2.95, 16.95, 1, 2)
    _flush_mount(ac, 1.5, 15.85, Z_MC, 6, 7, size=0.36)
    _switch(ac,'Y',13.32,3.35,-1,1.2,7,n=2)
    _smoke_detector(ac, 0.0, 16.5, Z_MC, 7)
    _register(ac, 2.9, 16.0, FL, along='Y', mi=1)
    ac.build("Back_FamAccessories", [M['walnut'], M['black_metal'], M['lampshade'], M['plant_pot'], M['leaf_plant'], M['bark'], L['emit_flush'], M['trim']],
             coll='House', smooth=True)
    _pl.potted("Back_FamPlant", (.20, 16.85, FL), kind='fiddle', height=1.0, pot='basket', seed=4)
    area_light("L_Back_FamCeiling", (1.5, 15.85, Z_MC - 0.09), (0.5, 0.5), 60, K30)
    add_light("L_Back_FamLamp", 'POINT', (2.95, 16.95, 1.5), 15, K30, size=0.08)
    room_light("L_Back_FamFill", 'family', energy=10, color=K30)


def halls(M):
    L = _local(M)
    _rug("Back_Rug_Hall", M, -0.78, 9.3, 0.6, 6.5, M['rug_plum'], t=0.01)
    mb = MB()                                                     # 0 brass, 1 glass glow, 2 frame, 3 canvas a, 4 canvas b
    for (x, y) in ((-0.78, 7.0), (-0.78, 11.5), (2.72, 12.45)):
        _semi_flush(mb, x, y, Z_MC, 0, 1)
    picture(mb, 6.0, 6.55, -1.25, 1.35, 1.85, mi_frame=2, mi_canvas=3, along='Y', face=1)
    picture(mb, 7.4, 7.95, -1.25, 1.35, 1.85, mi_frame=2, mi_canvas=4, along='Y', face=1)
    picture(mb, 12.0, 12.6, -0.3, 1.35, 1.9, mi_frame=2, mi_canvas=3, along='Y', face=-1)
    mb.build("Back_HallFixtures", [M['brass'], L['emit_glass'], M['frame'], M['art_lines'], M['art_bw']], coll='House', smooth=True)
    for i, (x, y) in enumerate(((-0.78, 7.0), (-0.78, 11.5), (2.72, 12.45))):
        add_light(f"L_Back_Hall{i}", 'POINT', (x, y, Z_MC - 0.24), 45, K30, size=0.1)


def bed_a(M):
    """Photo 10 / plan 31: the closet is a built-in on the FRONT wall (y 5.9) at its +X end; the bed backs onto the
    rear wall, nightstands + lamps, dresser + art on the front wall beside the closet, linen curtains on the window
    group, a bench at the foot, a rug."""
    L = _local(M)
    bd = MB()   # 0 frame fabric, 1 sheet, 2 walnut, 3 lamp base, 4 shade, 5 oak pale, 6 art frame, 7 canvas, 8 throw, 9 duvet,
                # 10 brass, 11 curtain, 12 mat white, 13 trim, 14 wall, 15 register, 16 plate, 17 book, 18-20 garments
    bed(bd, -3.9, 8.825, rot=0.0, w=1.6, l=2.15, mi_frame=0, mi_linen=1, mi_pillow=1, mi_throw=8, mi_duvet=9, head_h=1.1, seed=2)
    for x in (-5.15, -2.65):
        _nightstand2(bd, x, 9.65, 0.5, 0.42, 0.56, 2, 10, front='-Y')
        _lamp2(bd, x, 9.65, 0.58, 3, 4, 10, base_r=0.1, base_h=0.26, shade_r=0.16, shade_h=0.19)
    books(bd, -2.52, 9.52, 0.58, n=2, mi=17, rot=0.2, w=0.18, d=0.14)
    _closet(bd, 'X', -3.5, -1.55, 5.9, 6.5, 14, 13, 10, 10, [18, 19, 20, 19], ajar=0.5)
    # dresser (drawer fronts proud + bar pulls) + art with a mat above it, on the front wall left of the closet
    DX0, DX1 = -5.3, -3.75
    bd.rbox(DX0, DX1, 5.93, 6.38, 0.06, 0.92, r=0.01, mi=5)
    for sx in (DX0 + 0.08, DX1 - 0.08):
        for sy in (5.98, 6.33):
            bd.cylinder(sx, sy, 0.0, 0.06, 0.02, 0.016, seg=8, mi=5)
    for k in range(3):
        z0 = 0.16 + k * 0.245
        bd.box(DX0 + 0.05, DX1 - 0.05, 6.38, 6.395, z0, z0 + 0.22, 5)
        for cx in (DX0 + 0.4, DX1 - 0.4):
            bd.box(cx - 0.06, cx + 0.06, 6.395, 6.42, z0 + 0.1, z0 + 0.12, 10)
    _framed_art(bd, 'X', DX0 + 0.2, DX1 - 0.2, 5.9, +1, 1.25, 2.05, 6, 12, 7)
    vase(bd, DX0 + 0.25, 6.15, 0.92, h=0.2, r=0.06, mi=3, style='tall')
    books(bd, DX1 - 0.35, 6.17, 0.92, n=3, mi=17, rot=0.1, w=0.22, d=0.16)
    _curtains(bd, 'Y', 6.7, 8.5, -5.5, +1, 2.44, 0.03, 11, 10, seed=3)
    bd.rcbox(-3.9, 7.4, 0.42, 1.0, 0.38, 0.08, r=0.03, mi=0, puff=0.4)                                 # bench at the foot
    for sx in (-4.35, -3.45):
        for sy in (7.24, 7.56):
            bd.cylinder(sx, sy, 0.0, 0.38, 0.018, 0.014, seg=8, mi=2)
    _register(bd, -5.15, 7.2, FL, along='Y', mi=15)
    _switch(bd, 'Y', 8.55, -1.4, -1, 1.2, 16)
    bd.build("Back_BedA_Furniture", [M['fabric_taupe'], L['sheet'], M['walnut'], M['ceramic'], M['lampshade'], M['oak_pale'], M['frame'], M['art_abstract'],
                                     L['throw_sage'], L['duvet'], M['brass'], L['curtain'], L['mat_white'], M['trim'], M['wall'], L['register'], L['plate'],
                                     L['book_a'], L['garm1'], L['garm2'], L['garm3']], coll='House', smooth=True)
    _pl.potted("Back_BedA_Plant", (-5.0, 9.5, 0.58), kind='fern', height=0.2, pot='ceramic', pot_r=0.065, pot_h=0.085, seed=7)
    _rug("Back_Rug_BedA", M, -3.9, 7.7, 2.4, 1.8, M['rug_blue'])
    fm = MB()
    _flush_mount(fm, -3.45, 7.9, Z_MC, 0, 1, size=0.34)
    _smoke_detector(fm, -2.4, 9.0, Z_MC, 1)
    fm.build("Back_BedA_Light", [L['emit_flush'], M['trim']], coll='House', smooth=True)
    area_light("L_Back_BedACeiling", (-3.45, 7.9, Z_MC - 0.09), (0.45, 0.45), 50, K30)
    for i, x in enumerate((-5.15, -2.65)):
        add_light(f"L_Back_BedALamp{i}", 'POINT', (x, 9.65, 1.0), 12, K30, size=0.08)
    room_light("L_Back_BedAFill", 'bed_a', energy=8, color=K30)


def half_bath(M):
    from .fixtures import powder
    powder(M)


def bath_a(M):
    from .fixtures import main_bath
    main_bath(M)


def bed_b(M):
    L = _local(M)
    # ---- built-in closet on the -X wall's front part (photo 11 / plan 'CL'), corner window seat + shelves
    bi = MB()                                                     # 0 wall, 1 trim, 2 brass, 3 cushion, 4 book, 5-7 garments
    _closet(bi, 'Y', 12.9, 14.7, -5.5, -4.9, 0, 1, 2, 2, [5, 6, 7, 6], ajar=0.0)
    bi.box(-5.5, -4.95, 15.15, BED_REAR, FL, 0.5, 1); bi.box(-5.5, -4.2, 16.00, BED_REAR, FL, 0.5, 1)          # bench
    bi.box(-5.5, -4.95, 15.15, BED_REAR, 0.47, 0.5, 1)
    bi.rcbox(-5.2, 15.85, 0.53, 0.52, 1.36, 0.06, r=0.025, mi=3, puff=0.4); bi.rcbox(-4.85, 16.28, 0.53, 1.26, 0.5, 0.06, r=0.025, mi=3, puff=0.4)
    shelves(bi, -5.5, -4.95, 15.15, 15.55, 0.5, 2.2, n=4, t=0.025, mi=1, back=False)
    for k in range(4):
        books(bi, -5.4, 15.158, 0.5 + k * 0.425 + 0.0125, n=3, mi=4, rot=0.0, w=0.22, d=0.2)
    bi.build("Back_BedB_BuiltIns", [M['wall'], M['trim'], M['brass'], M['fabric_sand'], M['book'], L['garm1'], L['garm2'], L['garm3']], coll='House')
    # ---- bed against the +X wall, nightstands, desk + chair, curtains, art, rug
    bd = MB()   # 0 frame, 1 sheet, 2 oak pale, 3 lamp base, 4 shade, 5 chair wood, 6 seat, 7 throw, 8 duvet, 9 brass, 10 curtain,
                # 11 frame, 12 mat, 13 canvas, 14 register, 15 plate, 16 book, 17 black
    bed(bd, -1.475, 14.9, rot=-math.pi / 2, w=1.6, l=2.15, mi_frame=0, mi_linen=1, mi_pillow=1, mi_throw=7, mi_duvet=8, head_h=1.1, seed=5)
    for y in (13.83, 16.05):
        _nightstand2(bd, -.60, y, 0.42, 0.5, 0.56, 2, 9, front='-Y')
        _lamp2(bd, -.60, y, 0.58, 3, 4, 9, base_r=0.1, base_h=0.26, shade_r=0.16, shade_h=0.19)
    books(bd, -.52, 16.2, 0.58, n=2, mi=16, rot=1.4, w=0.18, d=0.14)
    table(bd, -2.55, 16.22, FL, 1.1, 0.55, h=0.75, top_t=0.03, mi_top=2, mi_leg=2, legs='four', leg_w=0.04)
    bd.box(-2.9, -2.2, 15.96, 15.975, 0.6, 0.71, 2); bd.box(-2.6, -2.5, 15.945, 15.96, 0.65, 0.66, 9)               # desk drawer + pull
    dining_chair(bd, -2.55, 15.7, rot=math.pi, z=FL, mi_wood=5, mi_seat=6)
    bd.rbox(-2.75, -2.42, 16.1, 16.35, 0.78, 0.795, r=0.004, mi=17, seg=1)                                              # laptop (closed)
    books(bd, -2.15, 16.25, 0.78, n=3, mi=16, rot=0.05, w=0.22, d=0.17)
    bd.lathe(-2.95, 16.3, 0.78, [(0, 0), (0.07, 0), (0.07, 0.015), (0.01, 0.02), (0, 0.02)], seg=14, mi=17)            # desk lamp
    bd.tube((-2.95, 16.3, 0.8), (-2.85, 16.2, 1.15), 0.006, 0.006, seg=6, mi=17)
    bd.lathe(-2.85, 16.2, 1.13, [(0.0, 0.0), (0.06, 0.0), (0.045, 0.06), (0, 0.06)], seg=14, mi=17)
    _framed_art(bd, 'Y', 14.35, 15.45, -.3, -1, 1.4, 2.0, 11, 12, 13)
    _curtains(bd, 'X', -1.85, -.9, BED_REAR, -1, 2.44, 0.8, 10, 9, seed=5, panel_w=0.3)
    _register(bd, -4.6, 15.3, FL, along='Y', mi=14)
    _switch(bd, 'Y', 13.7, -.3, -1, 1.2, 15)
    bd.build("Back_BedB_Furniture", [M['fabric'], L['sheet'], M['oak_pale'], M['ceramic'], M['lampshade'], M['walnut'], M['cane'], L['throw_rust'],
                                     L['duvet'], M['brass'], L['curtain'], M['frame'], L['mat_white'], M['art_lines'], L['register'], L['plate'],
                                     L['book_b'], M['black']], coll='House', smooth=True)
    _rug("Back_Rug_BedB", M, -3.3, 14.9, 2.2, 1.6, M['rug_camel'])
    fm = MB()
    _flush_mount(fm, -3.45, 14.8, Z_MC, 0, 1, size=0.34)
    _smoke_detector(fm, -2.2, 13.2, Z_MC, 1)
    fm.build("Back_BedB_Light", [L['emit_flush'], M['trim']], coll='House', smooth=True)
    area_light("L_Back_BedBCeiling", (-3.45, 14.8, Z_MC - 0.09), (0.45, 0.45), 50, K30)
    for i, y in enumerate((13.83, 16.05)):
        add_light(f"L_Back_BedBLamp{i}", 'POINT', (-.6, y, 1.0), 12, K30, size=0.08)
    room_light("L_Back_BedBFill", 'bed_b', energy=8, color=K30)


def build(M):
    _local(M)
    finishes(M)
    kitchen(M)
    laundry(M)
    family(M)
    halls(M)
    bed_a(M)
    half_bath(M)
    bath_a(M)
    bed_b(M)
