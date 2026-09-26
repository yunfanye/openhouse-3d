"""Site for 1836 Webster St: ground, lawns + beds, hardscape (walk, sidewalk, brick parkway, street, driveway, brick
patio), redwood fences + gates, the detached flat-roofed garage, the gabled workshop shed, the neighbours, and the
outdoor staging (patio dining + lounge set, planters, festoon string lights, porch chairs, path bollards, mailbox,
street lamp).  Detail pass 2026-09-04: every outbuilding / neighbour has real windows (frames, recessed glass,
muntins, sills), doors with hardware, eaves / gutters / downspouts, panel joints or lap siding, shingle courses;
fences are individual dog-eared boards on rails and capped posts; planters come from archviz.plants.

Everything reads its position from plan.py.  No trees (landscape.py), no house envelope (exterior.py: the rear brick
steps + their rail, the porch, the trellis, the hose bib on the house are exterior's).  Object names start with
Site_, collection 'Site'."""
import math, random
from mathutils import Vector
from .plan import *
from archviz.mesh import *
from archviz.lights import *
from archviz.parts import *
from archviz import materials as _mat
from archviz import plants

COLL = 'Site'
K30 = (1.0, 0.84, 0.66)
_L = {}


# ---------------------------------------------------------------- local materials
def _stucco(name, base, rough=0.9, blotch=0.18):
    """Sand-float stucco: fine aggregate bump + trowel undulation + faint weathering blotches."""
    m, nt, b = _mat._new(name)
    vec = _mat._coords(nt)
    fine = _mat._noise(nt, vec, scale=170.0, detail=6.0, rough=0.7)
    med = _mat._noise(nt, vec, scale=7.0, detail=3.0)
    stain = _mat._stretch(nt, _mat._noise(nt, vec, scale=0.9, detail=2.0), 0.42, 0.6)
    dark = (base[0] * 0.80, base[1] * 0.80, base[2] * 0.78, 1)
    col = _mat._mixrgb(nt, _mat._math(nt, 'MULTIPLY', stain, blotch), base, dark)
    col = _mat._mixrgb(nt, _mat._math(nt, 'MULTIPLY', fine, 0.12), col, dark)
    nt.links.new(b.inputs["Base Color"], col)
    _mat._set(b, "Roughness", rough); _mat._set(b, "Specular IOR Level", 0.25)
    h = _mat._math(nt, 'ADD', _mat._math(nt, 'MULTIPLY', fine, 0.65), _mat._math(nt, 'MULTIPLY', med, 0.35))
    _mat._bump(nt, b, h, 0.4, 0.012)
    return m


def _asphalt(name, base=(0.11, 0.11, 0.105, 1), light=(0.26, 0.26, 0.25, 1), cracks=True):
    """Asphalt: aggregate grain, faded patches, voronoi crack lines in some areas, dark oil stains."""
    m, nt, b = _mat._new(name)
    vec = _mat._coords(nt)
    grain = _mat._noise(nt, vec, scale=140.0, detail=6.0)
    patch = _mat._stretch(nt, _mat._noise(nt, vec, scale=0.35, detail=3.0), 0.4, 0.62)
    col = _mat._mixrgb(nt, _mat._math(nt, 'MULTIPLY', patch, 0.55), base, light)
    col = _mat._mixrgb(nt, _mat._math(nt, 'MULTIPLY', grain, 0.35), col, light)
    h = _mat._math(nt, 'MULTIPLY', grain, 0.6)
    if cracks:
        vor = _mat._voronoi(nt, vec, scale=0.45, feature='DISTANCE_TO_EDGE')
        crack = _mat._math(nt, 'LESS_THAN', vor.outputs["Distance"], 0.005)
        zone = _mat._math(nt, 'GREATER_THAN', _mat._noise(nt, vec, scale=0.22, detail=2.0), 0.6)
        crack = _mat._math(nt, 'MULTIPLY', crack, zone)
        col = _mat._mixrgb(nt, _mat._math(nt, 'MULTIPLY', crack, 0.6), col, (0.04, 0.04, 0.04, 1))
        h = _mat._math(nt, 'SUBTRACT', h, _mat._math(nt, 'MULTIPLY', crack, 0.6))
        stain = _mat._math(nt, 'GREATER_THAN', _mat._noise(nt, vec, scale=0.22, detail=2.0), 0.64)
        col = _mat._mixrgb(nt, _mat._math(nt, 'MULTIPLY', stain, 0.6), col, (0.05, 0.05, 0.05, 1))
    nt.links.new(b.inputs["Base Color"], col)
    _mat._set(b, "Roughness", 0.9); _mat._set(b, "Specular IOR Level", 0.25)
    _mat._bump(nt, b, h, 0.45, 0.015)
    return m


def _bark(name):
    """Bark mulch: voronoi chips in browns with a deep bump."""
    m, nt, b = _mat._new(name)
    vec = _mat._coords(nt)
    vor = _mat._voronoi(nt, vec, scale=42.0, feature='F1')
    csep = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(csep.inputs["Color"], vor.outputs["Color"])
    col = _mat._ramp(nt, csep.outputs["Red"], [(0.0, (0.09, 0.05, 0.03, 1)), (0.5, (0.22, 0.13, 0.07, 1)), (1.0, (0.38, 0.24, 0.13, 1))])
    n = _mat._noise(nt, vec, scale=3.0, detail=2.0)
    col = _mat._mixrgb(nt, _mat._math(nt, 'MULTIPLY', n, 0.35), col, (0.05, 0.03, 0.02, 1))
    nt.links.new(b.inputs["Base Color"], col)
    _mat._set(b, "Roughness", 0.95); _mat._set(b, "Specular IOR Level", 0.1)
    h = _mat._math(nt, 'SUBTRACT', 1.0, vor.outputs["Distance"])
    _mat._bump(nt, b, h, 0.9, 0.03)
    return m


def _tile_roof_mat(name, c1=(0.50, 0.22, 0.12, 1), c2=(0.68, 0.36, 0.20, 1), pitch=0.25, course=0.12):
    """Barrel-tile roof for distant houses: corrugation across the slope (chosen by the face normal) + z-based course
    lines + per-tile mottling."""
    m, nt, b = _mat._new(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(sep.inputs["Vector"], tc.outputs["Object"])
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    nsep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(nsep.inputs["Vector"], geo.outputs["Normal"])
    M_ = lambda op, a, c=None: _mat._math(nt, op, a, c)
    wx = M_('SINE', M_('MULTIPLY', sep.outputs["X"], 2 * math.pi / pitch))
    wy = M_('SINE', M_('MULTIPLY', sep.outputs["Y"], 2 * math.pi / pitch))
    facing_y = M_('GREATER_THAN', M_('ABSOLUTE', nsep.outputs["Y"]), 0.5)
    corr = _mat._mixrgb(nt, facing_y, wy, wx)      # faces toward +-Y corrugate along X
    csep = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(csep.inputs["Color"], corr)
    corr = csep.outputs["Red"]
    line = M_('LESS_THAN', M_('FRACT', M_('DIVIDE', sep.outputs["Z"], course)), 0.12)
    n = _mat._noise(nt, tc.outputs["Object"], scale=6.0, detail=3.0)
    col = _mat._mixrgb(nt, _mat._stretch(nt, n, 0.35, 0.65), c1, c2)
    col = _mat._mixrgb(nt, M_('MULTIPLY', line, 0.7), col, (0.22, 0.10, 0.06, 1))
    nt.links.new(b.inputs["Base Color"], col)
    _mat._set(b, "Roughness", 0.85); _mat._set(b, "Specular IOR Level", 0.3)
    h = M_('SUBTRACT', M_('MULTIPLY', corr, 0.5), M_('MULTIPLY', line, 0.6))
    _mat._bump(nt, b, h, 0.7, 0.03)
    return m


def _shingle_mat(name, c1=(0.30, 0.25, 0.20, 1), c2=(0.44, 0.38, 0.30, 1), course=0.10):
    """Composition shingles for distant roofs: z-based course lines, staggered tab joints, granule noise."""
    m, nt, b = _mat._new(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(sep.inputs["Vector"], tc.outputs["Object"])
    M_ = lambda op, a, c=None: _mat._math(nt, op, a, c)
    row = M_('FLOOR', M_('DIVIDE', sep.outputs["Z"], course))
    line = M_('LESS_THAN', M_('FRACT', M_('DIVIDE', sep.outputs["Z"], course)), 0.1)
    off = M_('MULTIPLY', M_('FRACT', M_('MULTIPLY', row, 0.5)), 0.15)
    tab = M_('LESS_THAN', M_('FRACT', M_('DIVIDE', M_('ADD', M_('ADD', sep.outputs["X"], sep.outputs["Y"]), off), 0.3)), 0.03)
    n = _mat._noise(nt, tc.outputs["Object"], scale=90.0, detail=4.0)
    col = _mat._mixrgb(nt, M_('MULTIPLY', n, 0.5), c1, c2)
    col = _mat._mixrgb(nt, M_('MULTIPLY', M_('MAXIMUM', line, tab), 0.6), col, (0.12, 0.10, 0.08, 1))
    nt.links.new(b.inputs["Base Color"], col)
    _mat._set(b, "Roughness", 0.95); _mat._set(b, "Specular IOR Level", 0.15)
    h = M_('SUBTRACT', M_('MULTIPLY', n, 0.3), M_('MULTIPLY', M_('MAXIMUM', line, tab), 0.8))
    _mat._bump(nt, b, h, 0.6, 0.012)
    return m


def _local(M):
    """Site-only materials (the shared library is never edited)."""
    if _L:
        return _L
    _L['glow'] = _mat.new_mat("SiteWindowGlow", (1.0, 0.8, 0.5, 1), rough=0.3, emit=(1.0, 0.74, 0.45, 1), emit_str=0.7)
    _L['glass_dark'] = _mat.new_mat("SiteGlassDark", (0.10, 0.12, 0.14, 1), rough=0.03, spec=0.9, coat=0.8)
    _L['glass_clear'] = _mat.new_mat("SiteGlassClear", (0.9, 0.92, 0.94, 1), rough=0.02, spec=0.9, transmission=1.0, ior=1.5)
    _L['interior_dark'] = _mat.new_mat("SiteInteriorDark", (0.10, 0.09, 0.08, 1), rough=0.9)
    _L['curtain'] = _mat.new_mat("NeighbourCurtainLit", (0.95, 0.86, 0.70, 1), rough=0.9, emit=(1.0, 0.78, 0.50, 1), emit_str=1.1)
    _L['curtain_dim'] = _mat.new_mat("NeighbourCurtain", (0.72, 0.68, 0.60, 1), rough=0.9)
    _L['paint_line'] = _mat.new_mat("RoadPaint", (0.75, 0.72, 0.55, 1), rough=0.8)
    _L['kerb'] = _mat.noise_mat("Kerb", (0.55, 0.54, 0.51, 1), (0.66, 0.65, 0.62, 1), scale=10, bump=0.15, rough=0.85)
    _L['gravel'] = _mat.noise_mat("DrivewayGravel", (0.42, 0.41, 0.38, 1), (0.60, 0.58, 0.54, 1), scale=90, bump=0.7, detail=5, rough=0.9, bump_dist=0.02)
    _L['asphalt'] = _asphalt("DrivewayAsphalt")
    _L['asphalt_street'] = _asphalt("StreetAsphalt", (0.13, 0.13, 0.125, 1), (0.28, 0.28, 0.27, 1))
    _L['mulch'] = _bark("BarkMulch")
    _L['cushion'] = _mat.fabric("OutdoorCushion", (0.80, 0.76, 0.66, 1), weave=80, bump=0.2)
    _L['cushion_grey'] = _mat.fabric("OutdoorCushionGrey", (0.40, 0.40, 0.38, 1), weave=80, bump=0.2)
    _L['blanket'] = _mat.fabric("OutdoorBlanket", (0.52, 0.30, 0.24, 1), weave=40, bump=0.4)
    _L['terracotta'] = _mat.noise_mat("Terracotta", (0.55, 0.30, 0.18, 1), (0.68, 0.40, 0.26, 1), scale=20, bump=0.25, rough=0.8)
    _L['dark_int'] = _mat.new_mat("ShedDarkInterior", (0.02, 0.02, 0.02, 1), rough=1.0)
    _L['cord'] = _mat.new_mat("LightCord", (0.02, 0.02, 0.02, 1), rough=0.6)
    _L['bulb'] = _mat.new_mat("FestoonBulb", (1.0, 0.85, 0.6, 1), rough=0.2, emit=(1.0, 0.72, 0.42, 1), emit_str=10.0)
    _L['brick_edge'] = _mat.tiles("BrickSoldier", (0.50, 0.24, 0.16, 1), grout=(0.55, 0.50, 0.44, 1), size=(0.1, 0.2), gap=0.008,
                                  rough=0.85, variation=0.22, mottle=0.5, bump=0.5, offset=0.0)
    _L['stucco_garage'] = _stucco("GarageStucco", (0.58, 0.60, 0.63, 1))
    _L['stucco_tan'] = _stucco("NeighbourTanStucco", (0.55, 0.45, 0.32, 1), blotch=0.22)
    _L['stucco_grey'] = _stucco("NeighbourGreyStucco", (0.50, 0.52, 0.55, 1))
    _L['stucco_white'] = _stucco("CottageWhiteStucco", (0.72, 0.70, 0.64, 1))
    _L['cap'] = _mat.noise_mat("ParapetCap", (0.60, 0.60, 0.58, 1), (0.70, 0.70, 0.68, 1), scale=40, bump=0.2, rough=0.85)
    _L['joint'] = _mat.new_mat("PanelJoint", (0.30, 0.31, 0.32, 1), rough=0.9)
    _L['galv'] = _mat.new_mat("Galvanised", (0.60, 0.62, 0.64, 1), rough=0.45, metal=0.8)
    _L['vent'] = _mat.new_mat("FoundationVent", (0.08, 0.08, 0.08, 1), rough=0.8)
    _L['siding_y'] = _mat.wood("ShedSidingY", light=(0.54, 0.56, 0.58, 1), dark=(0.42, 0.44, 0.46, 1), grain_axis='Y', scale=1.0, rough=0.85, coat=0.0)
    _L['siding_x'] = _mat.wood("ShedSidingX", light=(0.54, 0.56, 0.58, 1), dark=(0.42, 0.44, 0.46, 1), grain_axis='X', scale=1.0, rough=0.85, coat=0.0)
    _L['shingle_shed'] = _mat.tiles("ShedShingle", (0.34, 0.24, 0.15, 1), grout=(0.12, 0.09, 0.06, 1), size=(0.3, 0.14), gap=0.006, rough=0.95,
                                    variation=0.35, mottle=0.5, bump=0.5, offset=0.5)
    _L['shingle_far'] = _shingle_mat("NeighbourShingle")
    _L['tile_far'] = _tile_roof_mat("NeighbourTile")
    _L['screen'] = _mat.new_mat("ScreenMesh", (0.05, 0.05, 0.05, 1), rough=0.8, alpha=0.45)
    _L['doormat'] = _mat.fabric("DoormatCoir", (0.46, 0.36, 0.22, 1), weave=140, bump=0.7, rough=0.95)
    _L['lens'] = _mat.new_mat("LampLens", (1.0, 0.92, 0.8, 1), rough=0.4, emit=(1.0, 0.85, 0.6, 1), emit_str=5.0)
    _L['lens_frost'] = _mat.new_mat("LampLensFrost", (0.95, 0.92, 0.85, 1), rough=0.5, emit=(1.0, 0.82, 0.55, 1), emit_str=2.5)
    _L['mailbox'] = _mat.new_mat("MailboxBlack", (0.03, 0.03, 0.03, 1), rough=0.45, metal=0.5)
    _L['flag_red'] = _mat.new_mat("MailboxFlag", (0.7, 0.08, 0.06, 1), rough=0.5)
    _L['post_grey'] = _mat.wood("PostWeathered", light=(0.46, 0.42, 0.36, 1), dark=(0.30, 0.27, 0.22, 1), grain_axis='Z', rough=0.9, coat=0.0)
    _L['board_a'] = _mat.wood("FenceBoardA", light=(0.42, 0.27, 0.16, 1), dark=(0.25, 0.15, 0.09, 1), grain_axis='Z', rough=0.85, coat=0.0)
    _L['board_b'] = _mat.wood("FenceBoardB", light=(0.36, 0.30, 0.24, 1), dark=(0.22, 0.18, 0.14, 1), grain_axis='Z', rough=0.9, coat=0.0)
    _L['board_c'] = _mat.wood("FenceBoardC", light=(0.50, 0.42, 0.34, 1), dark=(0.32, 0.26, 0.20, 1), grain_axis='Z', rough=0.9, coat=0.0)
    _L['candle'] = _mat.new_mat("Candle", (0.95, 0.9, 0.8, 1), rough=0.5, emit=(1.0, 0.7, 0.35, 1), emit_str=4.0)
    _L['steel_pole'] = _mat.new_mat("PoleGreen", (0.08, 0.12, 0.09, 1), rough=0.5, metal=0.3)
    _L['brick_xz'] = _mat.tiles("BrickWallXZ", (0.52, 0.25, 0.17, 1), grout=(0.60, 0.55, 0.48, 1), size=(0.2, 0.065), gap=0.008, rough=0.85,
                                variation=0.25, mottle=0.5, bump=0.5, offset=0.5, plane='XZ')
    _L['brick_yz'] = _mat.tiles("BrickWallYZ", (0.52, 0.25, 0.17, 1), grout=(0.60, 0.55, 0.48, 1), size=(0.2, 0.065), gap=0.008, rough=0.85,
                                variation=0.25, mottle=0.5, bump=0.5, offset=0.5, plane='YZ')
    _L['copper'] = _mat.new_mat("CopperPipe", (0.55, 0.32, 0.22, 1), rough=0.4, metal=0.9)
    return _L


def _curb_y(x):
    """Centre line of the curved brick planter curb along the house front (photo 00): y -1.0 at the walk, bowing out
    to y -1.8 at the -X fence / the driveway edge."""
    wx0, wx1 = FRONT_WALK_X
    if x < wx0:
        t = (x - wx0) / (LOT[0] - wx0)
    else:
        t = (x - wx1) / (DRIVE_X[0] - wx1)
    t = max(0.0, min(1.0, t))
    return -1.0 - 0.8 * t * t


# ---------------------------------------------------------------- helpers
def _wedge_y(mb, pts_xz, y0, y1, mi=0):
    """Extrude a polygon given in the XZ plane along Y from y0 to y1 (gable ends, roof slabs)."""
    n = len(pts_xz)
    vs = [(x, y0, z) for (x, z) in pts_xz] + [(x, y1, z) for (x, z) in pts_xz]
    fs = [tuple(range(n)), tuple(reversed(range(n, 2 * n)))]
    for i in range(n):
        j = (i + 1) % n
        fs.append((i, j, n + j, n + i))
    mb._add(vs, fs, mi)


def _wedge_x(mb, pts_yz, x0, x1, mi=0):
    """Extrude a polygon given in the YZ plane along X."""
    n = len(pts_yz)
    vs = [(x0, y, z) for (y, z) in pts_yz] + [(x1, y, z) for (y, z) in pts_yz]
    fs = [tuple(range(n)), tuple(reversed(range(n, 2 * n)))]
    for i in range(n):
        j = (i + 1) % n
        fs.append((i, j, n + j, n + i))
    mb._add(vs, fs, mi)


def _bx(mb, along, a0, a1, b0, b1, z0, z1, mi):
    """Box in wall coordinates: along 'X' -> (a = x, b = y); along 'Y' -> (a = y, b = x)."""
    if along == 'X':
        mb.box(a0, a1, b0, b1, z0, z1, mi)
    else:
        mb.box(b0, b1, a0, a1, z0, z1, mi)


def _pt(along, a, b):
    return (a, b) if along == 'X' else (b, a)


def _win(mb, along, a0, a1, b, s, z0, z1, cols, rows, mi_frame, mi_glass, mi_back=None, recess=0.06, casing=0.06, sill=True, back=0.30):
    """Window unit in a wall hole (a0..a1, z0..z1) whose outside face is at plane b, outside toward +s: proud casing +
    sill, a 40 mm frame recessed into the reveal, muntins (cols x rows lites), glass, an optional plane `back` behind
    the glass (a dark interior or a lit curtain).  No two boxes share a coplanar face (Cycles renders those black)."""
    fw = 0.04
    bi = b - s * recess
    lo, hi = min(bi, b), max(bi, b)
    _bx(mb, along, a0 - casing, a1 + casing, b, b + s * 0.02, z1, z1 + casing, mi_frame)
    _bx(mb, along, a0 - casing, a0, b, b + s * 0.02, z0, z1, mi_frame)
    _bx(mb, along, a1, a1 + casing, b, b + s * 0.02, z0, z1, mi_frame)
    if sill:
        _bx(mb, along, a0 - casing - 0.02, a1 + casing + 0.02, b - s * 0.04, b + s * 0.05, z0 - 0.045, z0, mi_frame)
        _bx(mb, along, a0 - casing - 0.02, a1 + casing + 0.02, b + s * 0.035, b + s * 0.05, z0 - 0.06, z0 - 0.045, mi_frame)   # drip
    # reveal linings (poke 1 mm into the wall so no face is shared with the hole), then the frame between them
    _bx(mb, along, a0 - 0.001, a0 + 0.012, lo, hi, z0 - 0.001, z1 + 0.001, mi_frame)
    _bx(mb, along, a1 - 0.012, a1 + 0.001, lo, hi, z0 - 0.001, z1 + 0.001, mi_frame)
    _bx(mb, along, a0 + 0.012, a1 - 0.012, lo, hi, z1 - 0.012, z1 + 0.001, mi_frame)
    _bx(mb, along, a0 + 0.012, a1 - 0.012, lo, hi, z0 - 0.001, z0 + 0.012, mi_frame)
    _bx(mb, along, a0 + 0.012, a0 + fw, bi - s * 0.02, bi + s * 0.02, z0 + 0.012, z1 - 0.012, mi_frame)
    _bx(mb, along, a1 - fw, a1 - 0.012, bi - s * 0.02, bi + s * 0.02, z0 + 0.012, z1 - 0.012, mi_frame)
    _bx(mb, along, a0 + fw, a1 - fw, bi - s * 0.02, bi + s * 0.02, z0 + 0.012, z0 + fw, mi_frame)
    _bx(mb, along, a0 + fw, a1 - fw, bi - s * 0.02, bi + s * 0.02, z1 - fw, z1 - 0.012, mi_frame)
    ga0, ga1, gz0, gz1 = a0 + fw, a1 - fw, z0 + fw, z1 - fw
    vs = [ga0 + (ga1 - ga0) * c / cols for c in range(1, cols)]
    for ac in vs:
        _bx(mb, along, ac - 0.011, ac + 0.011, bi - s * 0.012, bi + s * 0.012, gz0, gz1, mi_frame)
    for r in range(1, rows):
        zc = gz0 + (gz1 - gz0) * r / rows
        edges = [ga0] + [v for ac in vs for v in (ac - 0.011, ac + 0.011)] + [ga1]
        for k in range(0, len(edges), 2):
            _bx(mb, along, edges[k], edges[k + 1], bi - s * 0.012, bi + s * 0.012, zc - 0.011, zc + 0.011, mi_frame)
    _bx(mb, along, ga0, ga1, bi - s * 0.003, bi + s * 0.003, gz0, gz1, mi_glass)
    if mi_back is not None:
        _bx(mb, along, a0 - 0.05, a1 + 0.05, bi - s * back, bi - s * (back - 0.01), z0 - 0.05, z1 + 0.05, mi_back)


def _door(mb, along, a0, a1, b, s, z0, z1, mi_frame, mi_leaf, mi_glass=None, glazed=None, mi_knob=None, recess=0.10, panel=True, casing=0.06):
    """Door unit in a wall hole: casing, jambs + head, a 40 mm leaf recessed into the reveal with two raised panels or a
    glazed upper part (glazed = (fraction from, fraction to) of the leaf height), a knob + escutcheon."""
    bi = b - s * recess
    lo, hi = min(bi, b), max(bi, b)
    _bx(mb, along, a0 - casing, a1 + casing, b, b + s * 0.02, z1, z1 + casing, mi_frame)
    _bx(mb, along, a0 - casing, a0, b, b + s * 0.02, z0, z1, mi_frame)
    _bx(mb, along, a1, a1 + casing, b, b + s * 0.02, z0, z1, mi_frame)
    _bx(mb, along, a0 - 0.001, a0 + 0.045, lo, hi, z0, z1 + 0.001, mi_frame)                 # jambs (poke 1 mm into the wall)
    _bx(mb, along, a1 - 0.045, a1 + 0.001, lo, hi, z0, z1 + 0.001, mi_frame)
    _bx(mb, along, a0 + 0.045, a1 - 0.045, lo, hi, z1 - 0.045, z1 + 0.001, mi_frame)         # head between the jambs
    la0, la1 = a0 + 0.045, a1 - 0.045
    h = z1 - 0.045 - z0
    if glazed and mi_glass is not None:
        gz0, gz1 = z0 + h * glazed[0], z0 + h * glazed[1]
        ba0, ba1 = la0 + 0.09, la1 - 0.09
        for (ra0, ra1, rz0, rz1) in ((la0, la1, z0 + 0.01, gz0), (la0, la1, gz1, z1 - 0.045), (la0, ba0, gz0, gz1), (ba1, la1, gz0, gz1)):
            _bx(mb, along, ra0, ra1, bi - s * 0.02, bi + s * 0.02, rz0, rz1, mi_leaf)         # rails + stiles round the glazed opening
        for (ra0, ra1, rz0, rz1) in ((ba0, ba0 + 0.03, gz0, gz1), (ba1 - 0.03, ba1, gz0, gz1), (ba0 + 0.03, ba1 - 0.03, gz0, gz0 + 0.03), (ba0 + 0.03, ba1 - 0.03, gz1 - 0.03, gz1)):
            _bx(mb, along, ra0, ra1, bi - s * 0.026, bi + s * 0.026, rz0, rz1, mi_frame)     # glazing bead frame
        _bx(mb, along, ba0 + 0.03, ba1 - 0.03, bi - s * 0.004, bi + s * 0.004, gz0 + 0.03, gz1 - 0.03, mi_glass)
        zc = (gz0 + gz1) / 2
        _bx(mb, along, ba0 + 0.03, ba1 - 0.03, bi - s * 0.012, bi + s * 0.012, zc - 0.012, zc + 0.012, mi_frame)   # divider
        if panel:
            _bx(mb, along, la0 + 0.10, la1 - 0.10, bi + s * 0.02, bi + s * 0.032, z0 + 0.12, gz0 - 0.08, mi_leaf)
    else:
        _bx(mb, along, la0, la1, bi - s * 0.02, bi + s * 0.02, z0 + 0.01, z1 - 0.045, mi_leaf)
    if panel and not (glazed and mi_glass is not None):
        for (pz0, pz1) in ((z0 + 0.12, z0 + h * 0.42), (z0 + h * 0.5, z1 - 0.14)):
            _bx(mb, along, la0 + 0.10, la1 - 0.10, bi + s * 0.02, bi + s * 0.032, pz0, pz1, mi_leaf)
            _bx(mb, along, la0 + 0.13, la1 - 0.13, bi + s * 0.032, bi + s * 0.04, pz0 + 0.03, pz1 - 0.03, mi_leaf)
    if mi_knob is not None:
        ka = la1 - 0.08
        kx, ky = _pt(along, ka, bi + s * 0.02)
        _bx(mb, along, ka - 0.03, ka + 0.03, bi + s * 0.02, bi + s * 0.03, z0 + 0.95, z0 + 1.05, mi_knob)
        sx, sy = _pt(along, ka, bi + s * 0.055)
        mb.sphere((sx, sy, z0 + 1.0), 0.028, seg=10, rings=6, mi=mi_knob)
        mb.tube((kx, ky, z0 + 1.0), (sx, sy, z0 + 1.0), 0.008, 0.008, seg=6, mi=mi_knob)


def _downspout(mb, x, y, z0, z1, out, mi, r=0.035, straps=3, shoe=True):
    """Round downspout hugging a wall at (x, y) (already offset 0.06 from the face); `out` = unit (dx, dy) pointing away
    from the wall.  Straps, an elbow at the top into the wall, a shoe + splash block at the bottom."""
    ox, oy = out
    mb.cylinder(x, y, z0 + 0.25, z1 - 0.12, r, seg=10, mi=mi)
    mb.tube((x, y, z1 - 0.12), (x - ox * 0.11, y - oy * 0.11, z1 - 0.02), r, r, seg=10, mi=mi)             # elbow into the parapet / gutter
    mb.tube((x - ox * 0.11, y - oy * 0.11, z1 - 0.02), (x - ox * 0.16, y - oy * 0.16, z1 - 0.02), r, r, seg=10, mi=mi)
    for k in range(straps):
        z = z0 + 0.45 + (z1 - z0 - 0.9) * k / max(1, straps - 1)
        mb.box(x - r - 0.012 - abs(oy) * 0.0, x + r + 0.012, y - r - 0.012, y + r + 0.012, z, z + 0.03, mi)
        mb.box(x - ox * 0.075 - 0.02, x - ox * 0.075 + 0.02, y - oy * 0.075 - 0.02, y - oy * 0.075 + 0.02, z, z + 0.03, mi)
    if shoe:
        mb.tube((x, y, z0 + 0.25), (x + ox * 0.18, y + oy * 0.18, z0 + 0.06), r, r * 0.9, seg=10, mi=mi)
        mb.box(x + ox * 0.15 - 0.16, x + ox * 0.15 + 0.16, y + oy * 0.15 - 0.16, y + oy * 0.15 + 0.16, z0 - 0.01, z0 + 0.05, mi + 1)   # splash block


def _gutter(mb, along, a0, a1, b, s, z, mi, w=0.12, h=0.10):
    """Half-round-ish gutter hung on a fascia at plane b (outside toward s), top edge at z."""
    _bx(mb, along, a0, a1, b, b + s * w, z - h, z - h + 0.02, mi)
    _bx(mb, along, a0, a1, b + s * (w - 0.015), b + s * w, z - h, z, mi)
    _bx(mb, along, a0, a1, b, b + s * 0.012, z - h, z, mi)
    _bx(mb, along, a0, a0 + 0.015, b + s * 0.012, b + s * (w - 0.015), z - h + 0.02, z, mi)
    _bx(mb, along, a1 - 0.015, a1, b + s * 0.012, b + s * (w - 0.015), z - h + 0.02, z, mi)


def _lap_siding(mb, along, a0, a1, b, s, z0, z1, mi, exposure=0.15, thick=0.022, gable=None, skip=()):
    """Horizontal lap siding on a wall face at plane b (outside toward s): one wedge per course, thick at the butt,
    thin at the top.  `gable` = (a_mid, z_eave, z_ridge) clips courses to the gable triangle; `skip` = (a0, a1, z0, z1)
    openings the courses run around."""
    z = z0
    while z < z1 - 0.005:
        zt = min(z + exposure + 0.02, z1 + 0.015)
        wa0, wa1, wa0t, wa1t = a0, a1, a0, a1
        if gable:
            am, zg0, zg1 = gable
            if zt > zg0:
                f = min(1.0, max(0.0, (zt - zg0) / (zg1 - zg0)))
                wa0t, wa1t = a0 + (am - a0) * f, a1 - (a1 - am) * f
                fb = min(1.0, max(0.0, (z - zg0) / (zg1 - zg0)))
                wa0, wa1 = a0 + (am - a0) * fb, a1 - (a1 - am) * fb
                if wa1t - wa0t < 0.02:
                    break
        segs = [(max(wa0, wa0t), min(wa1, wa1t))]
        for (sa0, sa1, sz0, sz1) in skip:
            if sz1 <= z or sz0 >= zt:
                continue
            new = []
            for (c0, c1) in segs:
                if sa1 <= c0 or sa0 >= c1:
                    new.append((c0, c1)); continue
                if sa0 > c0:
                    new.append((c0, sa0))
                if sa1 < c1:
                    new.append((sa1, c1))
            segs = new
        for (c0, c1) in segs:
            if c1 - c0 < 0.01:
                continue
            bot = [_pt(along, c0, b) + (z,), _pt(along, c1, b) + (z,), _pt(along, c1, b + s * thick) + (z,), _pt(along, c0, b + s * thick) + (z,)]
            top = [_pt(along, c0, b) + (zt,), _pt(along, c1, b) + (zt,), _pt(along, c1, b + s * 0.004) + (zt,), _pt(along, c0, b + s * 0.004) + (zt,)]
            mb.hexa(bot + top, mi)
        z += exposure


def _shingle_courses(mb, xe, ze, xr, zr, y0, y1, mi, exposure=0.14, butt=0.012):
    """Shingle courses on a roof plane running along Y from the eave (xe, ze) up to the ridge (xr, zr)."""
    dx, dz = xr - xe, zr - ze
    L = math.hypot(dx, dz)
    ux, uz = dx / L, dz / L
    nx, nz = -uz, ux
    if nz < 0:
        nx, nz = -nx, -nz
    d = 0.0
    while d < L - 0.02:
        d1 = min(d + exposure + 0.035, L)
        p0 = (xe + ux * d, ze + uz * d); p1 = (xe + ux * d1, ze + uz * d1)
        vs = [(p0[0], y0, p0[1]), (p0[0], y1, p0[1]), (p0[0] + nx * butt, y1, p0[1] + nz * butt), (p0[0] + nx * butt, y0, p0[1] + nz * butt),
              (p1[0], y0, p1[1]), (p1[0], y1, p1[1]), (p1[0] + nx * 0.003, y1, p1[1] + nz * 0.003), (p1[0] + nx * 0.003, y0, p1[1] + nz * 0.003)]
        mb.hexa(vs, mi)
        d += exposure


def _joints(mb, along, a0, a1, b, s, z0, z1, mi, dz=(), da=()):
    """Panel joint lines (thin dark strips 3 mm proud) on a face: horizontal at heights dz, vertical at positions da."""
    for z in dz:
        _bx(mb, along, a0, a1, b, b + s * 0.003, z - 0.004, z + 0.004, mi)
    for a in da:
        _bx(mb, along, a - 0.004, a + 0.004, b, b + s * 0.0025, z0, z1, mi)


def _vent(mb, along, a, b, s, z, mi, w=0.32, h=0.12):
    """Foundation vent: a dark recessed rectangle with 3 louvre bars, proud 6 mm."""
    _bx(mb, along, a - w / 2, a + w / 2, b, b + s * 0.006, z, z + h, mi)
    for k in range(3):
        zz = z + h * (k + 0.5) / 3
        _bx(mb, along, a - w / 2 + 0.01, a + w / 2 - 0.01, b + s * 0.006, b + s * 0.012, zz - 0.008, zz + 0.008, mi + 1)


def _jelly_light(mb, x, y, z, along, s, mi_black, mi_lens, name):
    """Small wall light: a round backplate, a short arm, a frosted jar; plus a point light."""
    if along == 'X':
        mb.box(x - 0.06, x + 0.06, y, y + s * 0.02, z - 0.06, z + 0.06, mi_black)
        mb.cylinder(x, y + s * 0.09, z - 0.09, z + 0.03, 0.04, 0.035, seg=12, mi=mi_lens)
        mb.box(x - 0.045, x + 0.045, y + s * 0.02, y + s * 0.14, z + 0.03, z + 0.06, mi_black)
        add_light(name, 'POINT', (x, y + s * 0.09, z - 0.05), 18, K30, size=0.05)
    else:
        mb.box(x, x + s * 0.02, y - 0.06, y + 0.06, z - 0.06, z + 0.06, mi_black)
        mb.cylinder(x + s * 0.09, y, z - 0.09, z + 0.03, 0.04, 0.035, seg=12, mi=mi_lens)
        mb.box(x + s * 0.02, x + s * 0.14, y - 0.045, y + 0.045, z + 0.03, z + 0.06, mi_black)
        add_light(name, 'POINT', (x + s * 0.09, y, z - 0.05), 18, K30, size=0.05)


def _board(mb, along, a, w, b, t, z0, z1, mi, ear=0.03, lean=0.0):
    """One fence board (dog-eared top) in the plane b, thickness t, from z0 to z1; `lean` shifts the top sideways."""
    pts = [(a, z0), (a + w, z0), (a + w + lean, z1 - ear), (a + w - ear + lean, z1), (a + ear + lean, z1), (a + lean, z1 - ear)]
    if along == 'X':
        _wedge_y(mb, pts, b - t / 2, b + t / 2, mi)
    else:
        _wedge_x(mb, [(aa, zz) for (aa, zz) in pts], b - t / 2, b + t / 2, mi)


def _post_cap(mb, x, y, z, w, mi):
    """Pyramid cap on a fence post."""
    hw = w / 2 + 0.02
    mb.box(x - hw, x + hw, y - hw, y + hw, z, z + 0.02, mi)
    mb.hexa([(x - hw, y - hw, z + 0.02), (x + hw, y - hw, z + 0.02), (x + hw, y + hw, z + 0.02), (x - hw, y + hw, z + 0.02),
             (x - 0.012, y - 0.012, z + 0.06), (x + 0.012, y - 0.012, z + 0.06), (x + 0.012, y + 0.012, z + 0.06), (x - 0.012, y + 0.012, z + 0.06)], mi)


def _fence_run(mb, p0, p1, h=1.8, rng=None, side=1, mis=(0, 1, 3, 4), mi_post=2, mi_rail=2):
    """Axis-aligned board fence from p0 to p1: individual dog-eared 0.14 boards (0.012 gaps, 4 weathering tints, random
    height / lean), two rails + a kick board on the `side` face, capped 0.1 posts every 2.4 m."""
    rng = rng or random.Random(7)
    (x0, y0), (x1, y1) = p0, p1
    zb = Z_GRADE - 0.06
    along = 'X' if abs(x1 - x0) > abs(y1 - y0) else 'Y'
    if along == 'X':
        a0, a1, b = min(x0, x1), max(x0, x1), y0
    else:
        a0, a1, b = min(y0, y1), max(y0, y1), x0
    L = a1 - a0
    n = int(L / 0.152)
    for i in range(n):
        s = a0 + i * 0.152 + 0.006
        r = rng.random()
        mi = mis[0] if r < 0.4 else (mis[1] if r < 0.68 else (mis[2] if r < 0.9 else mis[3]))
        top = zb + h + rng.uniform(-0.02, 0.02)
        _board(mb, along, s, 0.14, b, 0.02, zb + 0.02, top, mi, lean=rng.uniform(-0.006, 0.006))
    for zr in (0.42, 1.32):
        _bx(mb, along, a0, a1, b + side * 0.012, b + side * 0.046, zb + zr, zb + zr + 0.09, mi_rail)
    _bx(mb, along, a0, a1, b + side * 0.012, b + side * 0.034, zb + 0.02, zb + 0.17, mi_rail)           # kick board
    k = 0.0
    while k <= L + 0.01:
        pa = a0 + min(k, L)
        px, py = _pt(along, pa, b)
        mb.box(px - 0.05, px + 0.05, py - 0.05, py + 0.05, zb - 0.3, zb + h + 0.08, mi_post)
        _post_cap(mb, px, py, zb + h + 0.08, 0.1, mi_post)
        k += 2.4


def _gate(mb, along, a0, a1, b, h=1.8, mis=(0, 1, 3, 4), mi_post=2, mi_iron=5, rng=None):
    """Board gate between two capped posts: dog-eared boards, two rails + a diagonal brace (Z), strap hinges, a latch."""
    rng = rng or random.Random(3)
    zb = Z_GRADE - 0.04
    for pa in (a0, a1):
        px, py = _pt(along, pa, b)
        mb.box(px - 0.06, px + 0.06, py - 0.06, py + 0.06, zb - 0.3, zb + h + 0.12, mi_post)
        _post_cap(mb, px, py, zb + h + 0.12, 0.12, mi_post)
    s = a0 + 0.09
    while s + 0.14 <= a1 - 0.08:
        r = rng.random()
        mi = mis[0] if r < 0.6 else (mis[1] if r < 0.8 else mis[2])
        _board(mb, along, s, 0.14, b, 0.022, zb + 0.06, zb + h - 0.02 + rng.uniform(-0.01, 0.01), mi)
        s += 0.152
    for zr in (0.35, 1.3):
        _bx(mb, along, a0 + 0.08, a1 - 0.08, b + 0.012, b + 0.045, zb + zr, zb + zr + 0.09, mi_post)
    pa, pb = (a0 + 0.14, zb + 0.44), (a1 - 0.14, zb + 1.3)              # diagonal brace: one board from the bottom hinge side up
    dx_, dz_ = pb[0] - pa[0], pb[1] - pa[1]
    Ln = math.hypot(dx_, dz_); nx_, nz_ = -dz_ / Ln * 0.045, dx_ / Ln * 0.045
    pts = [(pa[0] - nx_, pa[1] - nz_), (pb[0] - nx_, pb[1] - nz_), (pb[0] + nx_, pb[1] + nz_), (pa[0] + nx_, pa[1] + nz_)]
    if along == 'X':
        _wedge_y(mb, pts, b + 0.046, b + 0.078, mi_post)
    else:
        _wedge_x(mb, pts, b + 0.046, b + 0.078, mi_post)
    for zh in (0.5, 1.45):                                              # T-strap hinges on the a0 post side
        _bx(mb, along, a0 + 0.07, a0 + 0.42, b + 0.046, b + 0.053, zb + zh - 0.02, zb + zh + 0.02, mi_iron)
        _bx(mb, along, a0 - 0.02, a0 + 0.02, b + 0.061, b + 0.075, zb + zh - 0.06, zb + zh + 0.06, mi_iron)
    _bx(mb, along, a1 - 0.22, a1 - 0.07, b + 0.046, b + 0.056, zb + 1.02, zb + 1.06, mi_iron)     # latch bar
    _bx(mb, along, a1 - 0.03, a1 + 0.05, b + 0.061, b + 0.08, zb + 1.0, zb + 1.08, mi_iron)       # catch on the post


def _digit(mb, x, z, y, d, mi, s=0.11):
    """Seven-segment house number digit on a Y-facing wall at plane y (proud by 0.006)."""
    segs = {'1': 'bc', '8': 'abcdefg', '3': 'abcdg', '6': 'acdefg'}[d]
    w, h, t = s * 0.6, s, 0.014
    y0, y1 = y - 0.006, y
    if 'a' in segs: mb.box(x, x + w, y0, y1, z + h - t, z + h, mi)
    if 'g' in segs: mb.box(x, x + w, y0, y1, z + h / 2 - t / 2, z + h / 2 + t / 2, mi)
    if 'd' in segs: mb.box(x, x + w, y0, y1, z, z + t, mi)
    if 'b' in segs: mb.box(x + w - t, x + w, y0, y1, z + h / 2, z + h, mi)
    if 'c' in segs: mb.box(x + w - t, x + w, y0, y1, z, z + h / 2, mi)
    if 'f' in segs: mb.box(x, x + t, y0, y1, z + h / 2, z + h, mi)
    if 'e' in segs: mb.box(x, x + t, y0, y1, z, z + h / 2, mi)


# ---------------------------------------------------------------- ground / lawns / beds
def _ground(M):
    L = _local(M)
    g = Z_GRADE
    mb = MB()
    mb.box(-250, 250, -250, 300, g - 0.06, g - 0.01, 0)
    mb.build("Site_Ground", [M['ground']], coll=COLL)

    mb = MB()
    x0, x1, y0, y1 = LAWN_FRONT
    x = x0
    while x < x1 - 1e-6:                                                     # front lawn in strips up to the planter curb
        xb = min(x + 0.25, x1)
        if xb <= FRONT_WALK_X[0] + 1e-6 or x >= FRONT_WALK_X[1] - 1e-6:
            mb.box(x, xb, y0, _curb_y((x + xb) / 2) - 0.13, g - 0.005, g, 0)
        x = xb
    x0, x1, y0, y1 = LAWN_REAR
    mb.plate(x0, x1, y0, y1, g - 0.005, g, holes=[(PATIO_PATH[0], min(PATIO_PATH[1], x1), y0, PATIO_PATH[3])], mi=1)
    mb.build("Site_Lawns", [M['lawn'], M['lawn_rear']], coll=COLL)

    # bark-mulch beds (their tops sit ABOVE the ground plane at g - 0.004: they used to hide under it and read as
    # flat olive ground): house front, porch front, side yards, rear-west of the patio, behind the garage, the rear zone
    mb = MB()
    zt = g - 0.004
    x = LOT[0]
    while x < DRIVE_X[0] - 1e-6:                                            # planter bed between the curb and the house front
        xb = min(x + 0.25, DRIVE_X[0])
        if xb <= PORCH_STEPS[0] + 1e-6 or x >= PORCH_STEPS[1] - 1e-6:
            mb.box(x, xb, _curb_y((x + xb) / 2) - 0.14, 0.0, g - 0.06, zt, 0)
        x = xb
    mb.box(5.6, 5.78, -6.8, 17.6, g - 0.06, zt, 0)                          # sliver between lawn / house and the drainage strip
    mb.box(DRIVE_X[1], LOT[1], -2.0, 17.6, g - 0.06, zt, 0)                 # strip driveway | +X fence
    mb.box(LOT[0], -5.75, 0.0, 17.35, g - 0.06, zt, 0)                      # -X side yard
    mb.box(-6.75, PATIO[0], BED_REAR + WT, 22.0, g - 0.06, zt, 0)                       # rear-west of the patio (photo 29: bare ground)
    mb.box(LOT[0], LAWN_REAR[0] + 0.05, 22.0, LAWN_REAR[3], g - 0.06, zt, 0)   # bed inside the -X fence
    mb.box(5.85, LOT[1], 26.5, LAWN_REAR[3], g - 0.06, zt, 0)               # behind the garage (oleander bed)
    mb.box(GARAGE[1], LOT[1], 17.6, 26.5, g - 0.06, zt, 0)                  # sliver east of the garage
    mb.box(LOT[0], LOT[1], LAWN_REAR[3], LOT[3], g - 0.06, zt, 0)           # rear zone (the shed sits here)
    mb.build("Site_Mulch", [L['mulch']], coll=COLL)

    # gravel: the drainage strip along the house wall on the driveway side (photo 30), a strip round the garage base,
    # and a path from the brick path's end along the lawn edge to the rear zone
    mb = MB()
    mb.box(5.78, 6.15, -6.8, 17.6, g - 0.06, g - 0.002, 0)
    mb.box(GARAGE[0] - 0.3, GARAGE[0], GARAGE[2] + 0.2, GARAGE[3], g - 0.06, g - 0.002, 0)
    mb.box(LAWN_REAR[1], 5.85, 26.0, LAWN_REAR[3] + 0.5, g - 0.06, g - 0.002, 0)
    mb.box(GARAGE[0] - 0.3, GARAGE[1] + 0.3, GARAGE[3] + 0.0, GARAGE[3] + 0.3, g - 0.06, g - 0.002, 0)
    mb.build("Site_Gravel", [L['gravel']], coll=COLL)

    # a 0.7 m concrete path down the -X side yard
    mb = MB()
    y = 0.2
    while y < 17.35:
        y2 = min(y + 1.2, 17.35)
        mb.box(-6.5, -5.8, y + 0.004, y2 - 0.004, g - 0.04, g + 0.005, 0)
        y = y2
    mb.build("Site_SidePath", [M['sidewalk']], coll=COLL)


# ---------------------------------------------------------------- hardscape
def _hardscape(M):
    L = _local(M)
    g = Z_GRADE
    # front walk (photo 00): brick in running bond with a soldier-course border, sidewalk -> the entry steps
    mb = MB()
    wx0, wx1 = FRONT_WALK_X
    mb.box(wx0 + 0.1, wx1 - 0.1, SIDEWALK[0], PORCH_STEPS[2], g - 0.05, g + 0.008, 0)
    mb.build("Site_FrontWalk", [M['brick']], coll=COLL)
    # curved brick planter curb: one course on a footing + a rowlock cap, from the walk / steps out to both lot edges
    mb = MB()      # 0 brick wall (xz), 1 rowlock cap
    for (xa, xb) in ((LOT[0], wx0), (wx1, DRIVE_X[0])):
        x = xa
        while x < xb - 1e-6:
            x2 = min(x + 0.25, xb)
            ya, yb = _curb_y(x), _curb_y(x2)
            mb.hexa([(x, ya - 0.12, g - 0.15), (x2, yb - 0.12, g - 0.15), (x2, yb + 0.12, g - 0.15), (x, ya + 0.12, g - 0.15),
                     (x, ya - 0.12, g + 0.2), (x2, yb - 0.12, g + 0.2), (x2, yb + 0.12, g + 0.2), (x, ya + 0.12, g + 0.2)], 0)
            mb.hexa([(x, ya - 0.14, g + 0.2), (x2, yb - 0.14, g + 0.2), (x2, yb + 0.14, g + 0.2), (x, ya + 0.14, g + 0.2),
                     (x, ya - 0.14, g + 0.265), (x2, yb - 0.14, g + 0.265), (x2, yb + 0.14, g + 0.265), (x, ya + 0.14, g + 0.265)], 1)
            x = x2
    mb.build("Site_PlanterCurb", [L['brick_xz'], L['brick_edge']], coll=COLL)

    # sidewalk band (near side), the far side, kerbs, brick parkways, the street
    mb = MB()
    sw0, sw1 = SIDEWALK
    x = -30.0
    while x < 30.0:
        mb.box(x + 0.004, min(x + 1.5, 30.0) - 0.004, sw1, sw0, g - 0.05, g, 0)          # near sidewalk slabs
        mb.box(x + 0.004, min(x + 1.5, 30.0) - 0.004, -21.4, -19.9, g - 0.05, g, 0)      # far sidewalk
        x += 1.5
    mb.build("Site_Sidewalks", [M['sidewalk']], coll=COLL)

    mb = MB()
    pk0, pk1 = PARKWAY
    mb.box(-30, 30, pk1, pk0, g - 0.05, g, 0)                                             # near parkway (brick)
    mb.box(-30, 30, -19.9, -19.0, g - 0.05, g, 0)                                         # far parkway
    mb.build("Site_Parkways", [M['brick']], coll=COLL)

    mb = MB()
    st0, st1 = STREET
    mb.box(-30, 30, st1, st0, g - 0.2, g - 0.15, 0)                                       # asphalt, 0.15 below the kerb top
    mb.build("Site_Street", [L['asphalt_street']], coll=COLL)
    mb = MB()
    x = -30.0
    while x < 30.0:                                                                        # dashed centre line
        mb.box(x, x + 2.0, (st0 + st1) / 2 - 0.06, (st0 + st1) / 2 + 0.06, g - 0.15, g - 0.148, 0)
        x += 5.0
    mb.build("Site_StreetLine", [L['paint_line']], coll=COLL)
    mb = MB()
    x = -30.0
    while x < 30.0:                                                                        # kerbs in 3 m stones with joints
        mb.box(x + 0.003, min(x + 3.0, 30.0) - 0.003, st0 - 0.15, st0, g - 0.2, g, 0)      # near kerb
        mb.box(x + 0.003, min(x + 3.0, 30.0) - 0.003, st1, st1 + 0.15, g - 0.2, g, 0)      # far kerb
        x += 3.0
    # storm drain: kerb inlet (a dark slot in the kerb face) + a grate in the gutter, at x -4 (outside the walk)
    mb.box(-4.6, -3.4, st0 - 0.16, st0 - 0.15, g - 0.14, g - 0.03, 1)
    mb.box(-4.5, -3.5, st0 - 0.75, st0 - 0.15, g - 0.152, g - 0.14, 2)
    for k in range(7):
        xx = -4.45 + k * 0.15
        mb.box(xx, xx + 0.03, st0 - 0.72, st0 - 0.18, g - 0.14, g - 0.128, 1)
    mb.build("Site_Kerbs", [L['kerb'], M['iron_black'], L['vent']], coll=COLL)

    # driveway (asphalt with cracks, photo 30) from the sidewalk to the garage front, a scored concrete apron
    mb = MB()
    dx0, dx1 = DRIVE_X
    mb.box(6.15, dx1, -8.5, GARAGE[2], g - 0.05, g, 0)
    mb.build("Site_Driveway", [L['asphalt']], coll=COLL)
    mb = MB()
    for (ya, yb) in ((pk1 - 0.05, pk1 + 0.45), (pk1 + 0.45, pk0 - 0.004), (pk0 + 0.004, sw0 + 0.2)):
        mb.box(dx0 - 0.3, dx1 + 0.3, ya, yb - 0.004, g - 0.05, g + 0.002, 0)              # apron in 3 scored slabs
    x = GARAGE[0]
    while x < GARAGE[1] - 0.01:                                                            # pad behind the garage (photo 28)
        mb.box(x + 0.004, min(x + 1.3, GARAGE[1]) - 0.004, GARAGE[3], 26.5, g - 0.05, g + 0.002, 0)
        x += 1.3
    mb.build("Site_Concrete", [M['sidewalk']], coll=COLL)

    # brick patio + path, soldier-course edge (a separate object rotated 90 deg so the brick pattern turns)
    mb = MB()
    px0, px1, py0, py1 = PATIO
    holes = [(-.4,3.5,py0,FAMILY_REAR+WT)] + sorted((cx - 0.35, cx + 0.35, cy - 0.35, cy + 0.35) for (cx, cy) in SHRUB_BEDS)
    from .exterior import _plate_holes
    _plate_holes(mb,px0+.1,px1,py0,py1-.1,g-.03,g+.02,holes,0)
    mb.box(PATIO_PATH[0] + 0.1, PATIO_PATH[1], py1 - 0.1, PATIO_PATH[3] - 0.1, g - 0.03, g + 0.02, 0)
    mb.build("Site_Patio", [M['brick']], coll=COLL)
    mb = MB()
    for (cx, cy) in SHRUB_BEDS:
        mb.box(cx - 0.35, cx + 0.35, cy - 0.35, cy + 0.35, g - 0.06, g + 0.0, 0)
    mb.build("Site_PatioBeds", [L['mulch']], coll=COLL)
    # edge strips built in a frame rotated -90 deg about Z, then the object is rotated +90 deg -> bricks run across
    mb = MB()
    def R(x0, x1, y0, y1, z0, z1):
        mb.box(min(y0, y1), max(y0, y1), min(-x0, -x1), max(-x0, -x1), z0, z1, 0)
    R(px0, px0 + 0.1, py0, py1, g - 0.03, g + 0.022)                     # -X edge of the patio
    R(px0, px1, py1 - 0.1, py1, g - 0.03, g + 0.022)                     # +Y edge
    R(PATIO_PATH[0], PATIO_PATH[0] + 0.1, py1 - 0.1, PATIO_PATH[3], g - 0.03, g + 0.022)
    R(PATIO_PATH[0], PATIO_PATH[1], PATIO_PATH[3] - 0.1, PATIO_PATH[3], g - 0.03, g + 0.022)
    R(wx0, wx0 + 0.1, SIDEWALK[0], PORCH_STEPS[2], g - 0.05, g + 0.01)     # front walk soldier borders
    R(wx1 - 0.1, wx1, SIDEWALK[0], PORCH_STEPS[2], g - 0.05, g + 0.01)
    ob = mb.build("Site_BrickEdges", [L['brick_edge']], coll=COLL)
    ob.rotation_euler = (0, 0, math.pi / 2)


# ---------------------------------------------------------------- fences + gates
def _fences(M):
    L = _local(M)
    rng = random.Random(11)
    mb = MB()      # 0 board a, 1 grey, 2 post, 3 board b, 4 board c
    x0, x1, y0, y1 = LOT
    _fence_run(mb, (x0, 0.6), (x0, y1), rng=rng, side=1)                 # -X side from the front cross fence back (rails face into our lot)
    _fence_run(mb, (-8.0, 0.6), (-6.95, 0.6), rng=rng, side=1)            # cross fence panel: neighbour's wall -> the side-yard gate
    _fence_run(mb, (x1, -2.0), (x1, y1), rng=rng, side=-1)               # +X side along the driveway
    _fence_run(mb, (x0, y1), (x1, y1), rng=rng, side=-1)                 # rear
    mb.build("Site_Fences", [M['fence'], M['fence_grey'], L['post_grey'], L['board_b'], L['board_c']], coll=COLL)

    mb = MB()      # 0 board a, 1 grey, 2 post, 3 board b, 4 board c, 5 iron
    gx0, gx1, gy = GATE
    _gate(mb, 'X', gx0, gx1, gy, h=1.8, rng=rng)                         # patio | driveway gate (photo 27/29)
    # tall post beside the gate for the festoon lines
    mb.box(gx1 - 0.14, gx1 - 0.04, gy - 0.05, gy + 0.05, Z_GRADE - 0.35, 2.75, 2)
    _post_cap(mb, gx1 - 0.09, gy, 2.75, 0.1, 2)
    _gate(mb, 'X', -6.95, -5.85, 0.6, h=1.8, rng=rng)                    # -X side-yard gate (photo 00: between the neighbour's chimney and our wall)
    mb.build("Site_Gates", [M['fence'], M['fence_grey'], L['post_grey'], L['board_b'], L['board_c'], M['iron_black']], coll=COLL)


# ---------------------------------------------------------------- garage (photos 27 / 28)
def _garage(M):
    L = _local(M)
    gx0, gx1, gy0, gy1 = GARAGE
    g = Z_GRADE
    zt = g + GARAGE_H                     # top of the parapet cap
    zw = zt - 0.20                        # wall top under the cornice band
    WT_ = 0.2
    # +Y (rear) face: the glazed side door near the -X corner, the 6-lite window toward +X (photo 28)
    DOOR = (5.75, 6.65, g, g + 2.05)
    WIN = (7.75, 8.65, g + 1.15, g + 1.95)
    ROLL = (5.55, 9.65, g, g + 2.15)      # roll-up door in the -Y face (toward the driveway)
    st = MB()      # 0 stucco, 1 cap, 2 joint, 3 white trim, 4 glass, 5 interior, 6 galv, 7 vent, 8 lens, 9 black, 10 membrane, 11 concrete, 12 knob
    st.wall('X', gx0, gx1, gy0, gy0 + WT_, g - 0.1, zw, holes=[ROLL], mi=0)
    st.wall('X', gx0, gx1, gy1 - WT_, gy1, g - 0.1, zw, holes=[DOOR, WIN], mi=0)
    st.wall('Y', gy0 + WT_, gy1 - WT_, gx0, gx0 + WT_, g - 0.1, zw, mi=0)
    st.wall('Y', gy0 + WT_, gy1 - WT_, gx1 - WT_, gx1, g - 0.1, zw, mi=0)
    st.box(gx0 + WT_, gx1 - WT_, gy0 + WT_, gy1 - WT_, g - 0.1, g, 11)                          # slab
    st.box(gx0 + 0.02, gx1 - 0.02, gy0 + 0.02, gy1 - 0.02, zw - 0.16, zw - 0.14, 10)             # roof membrane (inside the parapet)
    st.box(gx0 + WT_ - 0.01, gx1 - WT_ + 0.01, gy0 + WT_ - 0.01, gy1 - WT_ + 0.01, zw - 0.14, zw - 0.13, 5)   # dark ceiling (seen through the door glass)
    # cornice band 40 mm proud + a cap with a drip, joints every 1.2 m
    st.box(gx0 - 0.04, gx1 + 0.04, gy0 - 0.04, gy1 + 0.04, zw - 0.02, zt - 0.05, 0)
    st.box(gx0 - 0.07, gx1 + 0.07, gy0 - 0.07, gy1 + 0.07, zt - 0.05, zt - 0.02, 1)
    st.box(gx0 - 0.06, gx1 + 0.06, gy0 - 0.06, gy1 + 0.06, zt - 0.02, zt, 1)
    x = gx0 + 1.2
    while x < gx1 - 0.3:
        st.box(x - 0.0015, x + 0.0015, gy0 - 0.075, gy1 + 0.075, zt - 0.05, zt + 0.001, 2); x += 1.2
    # panel joints (photo 28: a horizontal joint ~1.2 m up + vertical joints every ~1.22 m)
    dz = (g + 1.25,)
    _joints(st, 'X', gx0, gx1, gy0, -1, g, zw, 2, dz=dz, da=[gx0 + 1.22 * k for k in range(1, 5) if gx0 + 1.22 * k < ROLL[0] - 0.1 or gx0 + 1.22 * k > ROLL[1] + 0.1])
    _joints(st, 'X', gx0, gx1, gy1, +1, g, zw, 2, dz=dz, da=[7.0, 9.2])
    _joints(st, 'Y', gy0, gy1, gx0, -1, g, zw, 2, dz=dz, da=[gy0 + 1.22 * k for k in range(1, 6)])
    _joints(st, 'Y', gy0, gy1, gx1, +1, g, zw, 2, dz=dz, da=[gy0 + 1.22 * k for k in range(1, 6)])
    # roll-up door: 4 x 4 raised panels, section joints, a T handle, a lock, the track reveal
    rx0, rx1, rz0, rz1 = ROLL
    yd = gy0 + 0.11
    st.box(rx0, rx1, yd, yd + 0.03, rz0, rz1, 3)
    pw, ph = (rx1 - rx0) / 4, (rz1 - rz0) / 4
    for i in range(4):
        for j in range(4):
            px, pz = rx0 + i * pw, rz0 + j * ph
            st.box(px + 0.07, px + pw - 0.07, yd - 0.014, yd, pz + 0.07, pz + ph - 0.07, 3)
            st.box(px + 0.10, px + pw - 0.10, yd - 0.022, yd - 0.014, pz + 0.10, pz + ph - 0.10, 3)
    for j in range(1, 4):
        st.box(rx0, rx1, yd - 0.004, yd, rz0 + j * ph - 0.006, rz0 + j * ph + 0.006, 2)
    st.box(rx0 + 0.02, rx1 - 0.02, yd - 0.004, yd, rz0, rz0 + 0.03, 9)                                 # bottom seal
    st.box((rx0 + rx1) / 2 - 0.09, (rx0 + rx1) / 2 + 0.09, yd - 0.05, yd - 0.03, rz0 + 0.9, rz0 + 0.93, 9)   # T handle
    st.box((rx0 + rx1) / 2 - 0.015, (rx0 + rx1) / 2 + 0.015, yd - 0.05, yd, rz0 + 0.82, rz0 + 0.93, 9)
    st.cylinder((rx0 + rx1) / 2 + 0.2, yd - 0.008, rz0 + 0.95, rz0 + 0.98, 0.018, seg=10, mi=9)       # lock cylinder (vertical stub)
    for xx in (rx0 + 0.02, rx1 - 0.02):                                                                 # tracks (visible edges)
        st.box(xx - 0.02, xx + 0.02, yd + 0.03, yd + 0.06, rz0, rz1 + 0.05, 6)
    # side door (glazed upper half, raised lower panel, knob), stoop, light above; the 6-lite window with a dark room behind
    _door(st, 'X', DOOR[0], DOOR[1], gy1, +1, DOOR[2], DOOR[3], 3, 3, mi_glass=4, glazed=(0.45, 0.96), mi_knob=12)
    st.box(DOOR[0] - 0.15, DOOR[1] + 0.15, gy1, gy1 + 0.55, g - 0.06, g + 0.06, 11)                   # concrete stoop
    st.box(DOOR[0] - 0.3, DOOR[1] + 0.3, gy1 + 0.55, gy1 + 0.9, g - 0.06, g + 0.0, 11)
    _jelly_light(st, (DOOR[0] + DOOR[1]) / 2, gy1, DOOR[3] + 0.25, 'X', +1, 9, 8, "Site_L_GarageDoor")
    _win(st, 'X', WIN[0], WIN[1], gy1, +1, WIN[2], WIN[3], 2, 3, 3, 4, mi_back=5, recess=0.08)
    # the dark interior box behind the door glass
    st.box(DOOR[0] - 0.2, DOOR[1] + 0.2, gy1 - 0.9, gy1 - 0.88, g, DOOR[3], 5)
    # downspouts: one between the door and the window, one on the +X corner, one at the -X / -Y corner (photos 27/28)
    _downspout(st, 7.2, gy1 + 0.075, g, zt - 0.03, (0, 1), 6)
    _downspout(st, gx1 - 0.12, gy1 + 0.075, g, zt - 0.03, (0, 1), 6)
    _downspout(st, gx0 - 0.075, gy0 + 0.35, g, zt - 0.03, (-1, 0), 6)
    for (xx, yy) in ((7.2, gy1 + 0.02), (gx1 - 0.12, gy1 + 0.02), (gx0 - 0.02, gy0 + 0.35)):           # scupper boxes through the band
        st.box(xx - 0.06, xx + 0.06, yy - 0.06, yy + 0.06, zt - 0.11, zt - 0.05, 6)
    # electrical: meter box + conduits on the -X face near the gate end (photo 27), a conduit up to the cornice
    st.box(gx0 - 0.09, gx0, gy0 + 0.9, gy0 + 1.15, g + 1.55, g + 1.9, 6)
    st.box(gx0 - 0.1, gx0 - 0.09, gy0 + 0.92, gy0 + 1.13, g + 1.57, g + 1.88, 9)
    st.cylinder(gx0 - 0.04, gy0 + 1.02, g + 1.9, zw - 0.02, 0.014, seg=8, mi=6)
    st.cylinder(gx0 - 0.04, gy0 + 1.02, g - 0.05, g + 1.55, 0.014, seg=8, mi=6)
    st.cylinder(gx0 - 0.04, gy0 + 1.1, g - 0.05, g + 1.55, 0.010, seg=8, mi=6)
    # lights: the existing lantern by the roll-up door, a jelly-jar on the -X face at the +Y end (photo 27)
    st.box(5.22, 5.38, gy0 - 0.12, gy0, g + 2.15, g + 2.42, 9)
    st.box(5.245, 5.355, gy0 - 0.11, gy0 - 0.01, g + 2.18, g + 2.36, 8)
    _jelly_light(st, gx0, gy1 - 0.6, g + 2.15, 'Y', -1, 9, 8, "Site_L_GarageSide")
    # foundation vents (photo 28) + roof vents
    for (along, a, b, s) in (('X', 9.3, gy1, +1), ('X', 6.9, gy1, +1), ('Y', gy0 + 2.0, gx0, -1), ('Y', gy0 + 5.0, gx0, -1), ('Y', gy1 - 1.0, gx1, +1)):
        _vent(st, along, a, b, s, g + 0.08, 7)
    st.cylinder(gx0 + 1.2, gy0 + 3.0, zw - 0.14, zw + 0.25, 0.04, seg=10, mi=6)
    st.cylinder(gx0 + 1.2, gy0 + 3.0, zw + 0.25, zw + 0.30, 0.06, seg=10, mi=6)
    st.cylinder(gx1 - 1.5, gy1 - 2.0, zw - 0.14, zw + 0.20, 0.03, seg=10, mi=6)
    st.build("Site_Garage", [L['stucco_garage'], L['cap'], L['joint'], M['trim'], L['glass_dark'], L['interior_dark'], L['galv'],
                             L['vent'], L['lens_frost'], M['iron_black'], M['roof_flat'], M['sidewalk'], M['brass']], coll=COLL, smooth=True)
    add_light("Site_L_Garage", 'POINT', (5.3, gy0 - 0.25, g + 2.2), 25, K30, size=0.08)


# ---------------------------------------------------------------- shed (workshop, photo 27)
def _shed(M):
    L = _local(M)
    sx0, sx1, sy0, sy1 = SHED
    g = Z_GRADE
    zt = g + SHED_H
    zr = g + SHED_RIDGE
    xm = (sx0 + sx1) / 2
    k = (zr - zt) / (xm - sx0)
    e = 0.25                                             # eave overhang
    mb = MB()      # 0 siding y, 1 siding x, 2 trim white, 3 dark interior, 4 glass, 5 shingle, 6 screen, 7 vent, 8 concrete, 9 knob, 10 fascia wood
    dx0, dx1 = xm - 0.42, xm + 0.42
    DOOR = (dx0, dx1, g, g + 2.0)
    WINS = [(sx0 + 0.55, sx0 + 1.15, g + 1.05, g + 1.85), (sx1 - 1.15, sx1 - 0.55, g + 1.05, g + 1.85)]
    # core walls (thin, with the door / window holes) + gable ends + a dark interior
    mb.wall('X', sx0, sx1, sy0, sy0 + 0.12, g - 0.1, zt, holes=[DOOR] + WINS, mi=3)
    mb.wall('X', sx0, sx1, sy1 - 0.12, sy1, g - 0.1, zt, mi=3)
    mb.wall('Y', sy0 + 0.12, sy1 - 0.12, sx0, sx0 + 0.12, g - 0.1, zt, mi=3)
    mb.wall('Y', sy0 + 0.12, sy1 - 0.12, sx1 - 0.12, sx1, g - 0.1, zt, mi=3)
    _wedge_y(mb, [(sx0, zt), (sx1, zt), (xm, zr)], sy0, sy0 + 0.12, 3)
    _wedge_y(mb, [(sx0, zt), (sx1, zt), (xm, zr)], sy1 - 0.12, sy1, 3)
    mb.box(sx0 + 0.12, sx1 - 0.12, sy0 + 0.12, sy1 - 0.12, g - 0.1, g, 8)               # floor slab
    # lap siding on all four faces (courses run around the openings, clipped to the gables)
    _lap_siding(mb, 'X', sx0 + 0.04, sx1 - 0.04, sy0, -1, g + 0.05, zr - 0.05, 1, gable=(xm, zt, zr), skip=[DOOR] + WINS)
    _lap_siding(mb, 'X', sx0 + 0.04, sx1 - 0.04, sy1, +1, g + 0.05, zr - 0.05, 1, gable=(xm, zt, zr))
    _lap_siding(mb, 'Y', sy0 + 0.04, sy1 - 0.04, sx0, -1, g + 0.05, zt - 0.02, 0)
    _lap_siding(mb, 'Y', sy0 + 0.04, sy1 - 0.04, sx1, +1, g + 0.05, zt - 0.02, 0)
    # corner boards, a skirt board, the gable rake boards
    for (cx, cy) in ((sx0, sy0), (sx1, sy0), (sx0, sy1), (sx1, sy1)):
        mb.box(cx - 0.045, cx + 0.045, cy - 0.045, cy + 0.045, g, zt + 0.02, 2)
    for (ya, yb) in ((sy0 - 0.05, sy0), (sy1, sy1 + 0.05)):
        mb.box(sx0 - 0.05, sx1 + 0.05, ya, yb, g, g + 0.05, 2)
    for (xa, xb) in ((sx0 - 0.05, sx0), (sx1, sx1 + 0.05)):
        mb.box(xa, xb, sy0 - 0.05, sy1 + 0.05, g, g + 0.05, 2)
    # roof: deck slabs with an overhang, shingle courses on both slopes, fascia + rake boards, rafter tails, a ridge cap
    ze = zt - e * k
    for (xa, xb) in ((sx0 - e, xm), (xm, sx1 + e)):
        za = ze if xa < xm else zr
        zb = zr if xa < xm else ze
        _wedge_y(mb, [(xa, za), (xb, zb), (xb, zb + 0.05), (xa, za + 0.05)], sy0 - 0.2, sy1 + 0.2, 10)   # deck (its underside = the soffit)
    _shingle_courses(mb, sx0 - e - 0.03, ze + 0.05 - 0.03 * k, xm, zr + 0.05, sy0 - 0.22, sy1 + 0.22, 5)
    _shingle_courses(mb, sx1 + e + 0.03, ze + 0.05 - 0.03 * k, xm, zr + 0.05, sy0 - 0.22, sy1 + 0.22, 5)
    _wedge_y(mb, [(xm - 0.17, zr + 0.05 - 0.17 * k + 0.01), (xm, zr + 0.075), (xm + 0.17, zr + 0.05 - 0.17 * k + 0.01),
                  (xm + 0.17, zr + 0.05 - 0.17 * k + 0.025), (xm, zr + 0.09), (xm - 0.17, zr + 0.05 - 0.17 * k + 0.025)], sy0 - 0.22, sy1 + 0.22, 5)   # ridge cap
    for (xa, xb) in ((sx0 - e - 0.03, sx0 - e), (sx1 + e, sx1 + e + 0.03)):                            # eave fascia
        mb.box(xa, xb, sy0 - 0.2, sy1 + 0.2, ze - 0.14, ze + 0.06, 2)
    for (ya, yb) in ((sy0 - 0.23, sy0 - 0.2), (sy1 + 0.2, sy1 + 0.23)):                                  # rake boards
        _wedge_y(mb, [(sx0 - e, ze - 0.14), (xm, zr - 0.14), (xm, zr + 0.06), (sx0 - e, ze + 0.06)], ya, yb, 2)
        _wedge_y(mb, [(xm, zr - 0.14), (sx1 + e, ze - 0.14), (sx1 + e, ze + 0.06), (xm, zr + 0.06)], ya, yb, 2)
    y = sy0 + 0.1
    while y < sy1:                                                                                       # rafter tails under the eaves (follow the slope)
        for (xa, xb) in ((sx0 - e + 0.03, sx0 + 0.05), (sx1 - 0.05, sx1 + e - 0.03)):
            za = (ze + (xa - (sx0 - e)) * k if xa < xm else ze + ((sx1 + e) - xa) * k) - 0.004
            zb = (ze + (xb - (sx0 - e)) * k if xb < xm else ze + ((sx1 + e) - xb) * k) - 0.004
            mb.hexa([(xa, y - 0.025, za - 0.12), (xb, y - 0.025, zb - 0.12), (xb, y + 0.025, zb - 0.12), (xa, y + 0.025, za - 0.12),
                     (xa, y - 0.025, za), (xb, y - 0.025, zb), (xb, y + 0.025, zb), (xa, y + 0.025, za)], 10)
        y += 0.6
    # -Y end: the open door (leaf swung out, a dark room behind, a screen door in the frame), the two 2x3 windows, a gable vent
    _door(mb, 'X', DOOR[0], DOOR[1], sy0, -1, DOOR[2], DOOR[3], 2, 3, recess=0.08, panel=False, casing=0.07)
    mb.box(dx0 + 0.02, dx1 - 0.02, sy0 - 0.06, sy0 - 0.045, g + 0.05, DOOR[3] - 0.06, 6)                 # screen door mesh
    mb.frame(dx0 + 0.01, dx1 - 0.01, sy0 - 0.07, sy0 - 0.04, g + 0.03, DOOR[3] - 0.045, 0.05, mi=2, axis='Y')
    mb.box(dx0 + 0.06, dx1 - 0.06, sy0 - 0.07, sy0 - 0.04, g + 0.95, g + 1.0, 2)
    lz0, lz1 = g + 0.02, DOOR[3] - 0.06                                                                  # the wood leaf, swung open ~95 deg
    mb.box(dx1 + 0.03, dx1 + 0.07, sy0 - 0.86, sy0 - 0.02, lz0, lz1, 2)
    for (pz0, pz1) in ((lz0 + 0.12, lz0 + 0.8), (lz0 + 0.95, lz1 - 0.12)):
        mb.box(dx1 + 0.07, dx1 + 0.08, sy0 - 0.78, sy0 - 0.1, pz0, pz1, 2)
    mb.sphere((dx1 + 0.10, sy0 - 0.78, g + 1.0), 0.028, seg=10, rings=6, mi=9)
    mb.box(dx0 - 0.1, dx1 + 0.1, sy0 - 0.45, sy0, g - 0.06, g + 0.05, 8)                                 # concrete step
    for (wa0, wa1, wz0, wz1) in WINS:
        _win(mb, 'X', wa0, wa1, sy0, -1, wz0, wz1, 2, 3, 2, 4, mi_back=3, recess=0.05, casing=0.07)
    mb.box(xm - 0.16, xm + 0.16, sy0 - 0.02, sy0, zt + 0.35, zt + 0.65, 2)                               # gable vent frame
    for kk in range(4):
        zz = zt + 0.39 + kk * 0.065
        mb.box(xm - 0.13, xm + 0.13, sy0 - 0.03, sy0 - 0.02, zz, zz + 0.03, 7)
    for a in (sx0 + 0.45, sx1 - 0.45):
        _vent(mb, 'X', a, sy0, -1, g + 0.1, 7, w=0.28, h=0.1)
    mb.build("Site_Shed", [L['siding_y'], L['siding_x'], M['trim'], L['dark_int'], L['glass_dark'], L['shingle_shed'], L['screen'], L['vent'],
                           M['sidewalk'], M['brass'], L['post_grey']], coll=COLL)


# ---------------------------------------------------------------- neighbours
def _neighbours(M):
    L = _local(M)
    g = Z_GRADE
    # ---- tan two-storey at -X (photo 16), hip clay-tile roof, eaves + gutters, real windows, a front door with steps
    mb = MB()      # 0 stucco, 1 tile, 2 glass, 3 trim, 4 curtain lit, 5 curtain dim, 6 galv, 7 interior, 8 knob, 9 cap
    x0, x1, y0, y1, h = -20.0, -8.0, 2.0, 14.0, 6.5
    WT_ = 0.3
    WE = [(3.6, 4.6, 1.1, 2.4, True), (6.8, 7.8, 1.1, 2.4, False), (10.4, 11.4, 1.1, 2.4, True), (4.9, 5.9, 4.2, 5.5, False), (8.3, 9.3, 4.2, 5.5, True), (11.7, 12.7, 4.2, 5.5, False)]
    WS = [(-19.0, -17.9, 1.0, 2.3, False), (-12.2, -11.1, 1.0, 2.3, True), (-17.6, -16.5, 4.2, 5.5, True), (-13.6, -12.5, 4.2, 5.5, False), (-10.8, -9.7, 4.2, 5.5, False)]
    DOOR = (-14.9, -13.9, 0.45, 2.6)
    WN = [(-17.5, -16.4, 1.1, 2.4, False), (-12.5, -11.4, 4.2, 5.5, True)]
    mb.wall('Y', y0, y1, x1 - WT_, x1, g - 0.1, g + h, holes=[(a, b, g + c, g + d) for (a, b, c, d, _) in WE], mi=0)
    mb.wall('X', x0, x1 - WT_, y0, y0 + WT_, g - 0.1, g + h, holes=[(a, b, g + c, g + d) for (a, b, c, d, _) in WS] + [(DOOR[0], DOOR[1], g + DOOR[2], g + DOOR[3])], mi=0)
    mb.wall('X', x0, x1 - WT_, y1 - WT_, y1, g - 0.1, g + h, holes=[(a, b, g + c, g + d) for (a, b, c, d, _) in WN], mi=0)
    mb.wall('Y', y0 + WT_, y1 - WT_, x0, x0 + WT_, g - 0.1, g + h, mi=0)
    # brick wainscot round the base (photo 00) + a brick chimney breast on the +X face by the fence
    for (xa, xb, ya, yb, mi_) in ((x0 - 0.03, x1 + 0.03, y0 - 0.03, y0, 10), (x0 - 0.03, x1 + 0.03, y1, y1 + 0.03, 10),
                                  (x0 - 0.03, x0, y0, y1, 11), (x1, x1 + 0.03, y0, y1, 11)):
        mb.box(xa, xb, ya, yb, g - 0.05, g + 0.75, mi_)
    mb.box(x0 - 0.05, x1 + 0.05, y0 - 0.05, y1 + 0.05, g + 0.75, g + 0.79, 10)                             # wainscot cap course
    chx0, chx1, chy0, chy1 = x1, x1 + 0.55, 2.3, 3.2
    mb.box(chx0, chx1, chy0, chy1, g - 0.05, g + 8.3, 11)
    mb.box(chx0 - 0.03, chx1 + 0.06, chy0 - 0.06, chy1 + 0.06, g + 8.3, g + 8.4, 9)
    mb.box(chx0 + 0.12, chx1 - 0.12, chy0 + 0.12, chy1 - 0.12, g + 8.4, g + 8.62, 7)
    mb.box(x0 + WT_, x1 - WT_, y0 + WT_, y1 - WT_, g + 3.0, g + 3.3, 7)                                   # a floor slab (dark) so rooms read as rooms
    mb.box(x0 + WT_, x1 - WT_, y0 + WT_, y1 - WT_, g + h - 0.3, g + h, 7)
    for (a, b, c, d, lit) in WE:
        _win(mb, 'Y', a, b, x1, +1, g + c, g + d, 2, 3, 3, 2, mi_back=4 if lit else 5, recess=0.07)
    for (a, b, c, d, lit) in WS:
        _win(mb, 'X', a, b, y0, -1, g + c, g + d, 2, 3, 3, 2, mi_back=4 if lit else 5, recess=0.07)
    for (a, b, c, d, lit) in WN:
        _win(mb, 'X', a, b, y1, +1, g + c, g + d, 2, 3, 3, 2, mi_back=4 if lit else 5, recess=0.07)
    _door(mb, 'X', DOOR[0], DOOR[1], y0, -1, g + DOOR[2], g + DOOR[3], 3, 3, mi_knob=8, recess=0.12)
    for k in range(3):                                                                                     # 3 concrete risers up to a stoop at the door
        mb.box(DOOR[0] - 0.45, DOOR[1] + 0.45, y0 - 1.15 + k * 0.33, y0, g - 0.06, g + 0.15 * (k + 1), 9)
    _jelly_light(mb, DOOR[1] + 0.25, y0, g + 2.3, 'X', -1, 6, 3, "Site_L_NeighW_Door")
    # eaves: fascia ring + gutters on all sides, two downspouts at the +X corners, the hip roof (tile material with
    # corrugation + courses), ridge / hip caps, chimney + cap with two pots
    ov = 0.45
    mb.box(x0 - ov, x1 + ov, y0 - ov, y1 + ov, g + h - 0.02, g + h + 0.16, 3)                             # fascia (hollow look not needed)
    mb.box(x0 - ov + 0.02, x1 + ov - 0.02, y0 - ov + 0.02, y1 + ov - 0.02, g + h - 0.03, g + h - 0.02, 3)  # soffit face
    _gutter(mb, 'Y', y0 - ov, y1 + ov, x1 + ov, +1, g + h + 0.16, 6)
    _gutter(mb, 'Y', y0 - ov, y1 + ov, x0 - ov, -1, g + h + 0.16, 6)
    _gutter(mb, 'X', x0 - ov, x1 + ov, y0 - ov, -1, g + h + 0.16, 6)
    _gutter(mb, 'X', x0 - ov, x1 + ov, y1 + ov, +1, g + h + 0.16, 6)
    _downspout(mb, x1 + ov + 0.075, y0 + 0.25, g, g + h + 0.1, (1, 0), 6)
    _downspout(mb, x1 + ov + 0.075, y1 - 0.25, g, g + h + 0.1, (1, 0), 6)
    rise = 2.5
    mb.hexa([(x0 - ov, y0 - ov, g + h + 0.16), (x1 + ov, y0 - ov, g + h + 0.16), (x1 + ov, y1 + ov, g + h + 0.16), (x0 - ov, y1 + ov, g + h + 0.16),
             (x0 + 3.0, y0 + 6.0, g + h + 0.16 + rise), (x1 - 3.0, y0 + 6.0, g + h + 0.16 + rise), (x1 - 3.0, y1 - 6.0, g + h + 0.16 + rise), (x0 + 3.0, y1 - 6.0, g + h + 0.16 + rise)], 1)
    zr = g + h + 0.16 + rise
    mb.tube((x0 + 3.0 - 0.1, y0 + 6.0, zr + 0.03), (x1 - 3.0 + 0.1, y0 + 6.0, zr + 0.03), 0.09, 0.09, seg=10, mi=1)   # ridge cap
    for (cx, cy) in ((x0 - ov, y0 - ov), (x1 + ov, y0 - ov), (x1 + ov, y1 + ov), (x0 - ov, y1 + ov)):
        rx = x0 + 3.0 if cx < 0.5 * (x0 + x1) else x1 - 3.0
        mb.tube((cx, cy, g + h + 0.2), (rx, y0 + 6.0, zr + 0.03), 0.07, 0.07, seg=8, mi=1)                  # hip caps
    cx0, cx1, cy0, cy1 = x0 + 3.0, x0 + 3.8, y0 + 5.5, y0 + 6.3
    mb.box(cx0, cx1, cy0, cy1, g + h, g + h + 3.2, 0)
    mb.box(cx0 - 0.06, cx1 + 0.06, cy0 - 0.06, cy1 + 0.06, g + h + 3.2, g + h + 3.3, 9)
    for xx in (cx0 + 0.22, cx1 - 0.22):
        mb.cylinder(xx, (cy0 + cy1) / 2, g + h + 3.3, g + h + 3.7, 0.12, 0.1, seg=12, mi=1)
    mb.build("Site_NeighbourWest", [L['stucco_tan'], L['tile_far'], L['glass_dark'], M['trim'], L['curtain'], L['curtain_dim'], L['galv'],
                                    L['interior_dark'], M['brass'], L['cap'], L['brick_xz'], L['brick_yz']], coll=COLL, smooth=True)
    add_light("Site_L_NeighW_Win", 'POINT', (x1 - 1.0, 7.3, g + 1.9), 40, K30, size=0.3)

    # ---- grey gabled house with a dormer at +X behind the garage (photo 28): shingle roof, rake + eave boards, gutters
    mb = MB()      # 0 stucco, 1 shingle, 2 glass, 3 trim, 4 curtain lit, 5 curtain dim, 6 galv, 7 interior, 8 cap
    x0, x1, y0, y1, h = 12.5, 22.0, 19.0, 30.0, 6.0
    ym = (y0 + y1) / 2
    WW = [(21.0, 22.0, 1.2, 2.5, True), (24.5, 25.5, 1.2, 2.5, False), (28.0, 29.0, 1.2, 2.5, True), (22.5, 23.5, 3.6, 4.9, False), (26.5, 27.5, 3.6, 4.9, True)]
    WSs = [(14.0, 15.0, 1.1, 2.4, False), (17.5, 18.5, 1.1, 2.4, True), (19.5, 20.5, 1.1, 2.4, False)]
    mb.wall('Y', y0, y1, x0, x0 + WT_, g - 0.1, g + h, holes=[(a, b, g + c, g + d) for (a, b, c, d, _) in WW], mi=0)
    mb.wall('Y', y0, y1, x1 - WT_, x1, g - 0.1, g + h, mi=0)
    mb.wall('X', x0 + WT_, x1 - WT_, y0, y0 + WT_, g - 0.1, g + h, holes=[(a, b, g + c, g + d) for (a, b, c, d, _) in WSs], mi=0)
    mb.wall('X', x0 + WT_, x1 - WT_, y1 - WT_, y1, g - 0.1, g + h, mi=0)
    mb.box(x0 + WT_, x1 - WT_, y0 + WT_, y1 - WT_, g + 2.9, g + 3.2, 7)
    mb.box(x0 + WT_, x1 - WT_, y0 + WT_, y1 - WT_, g + h - 0.3, g + h, 7)
    _wedge_x(mb, [(y0, g + h), (y1, g + h), (ym, g + h + 2.6)], x0, x0 + WT_, 0)                             # gable ends
    _wedge_x(mb, [(y0, g + h), (y1, g + h), (ym, g + h + 2.6)], x1 - WT_, x1, 0)
    mb.box(x0 + WT_, x1 - WT_, y0 + WT_, y1 - WT_, g + h, g + h + 0.02, 7)
    for (a, b, c, d, lit) in WW:
        _win(mb, 'Y', a, b, x0, -1, g + c, g + d, 2, 2, 3, 2, mi_back=4 if lit else 5, recess=0.07)
    for (a, b, c, d, lit) in WSs:
        _win(mb, 'X', a, b, y0, -1, g + c, g + d, 2, 2, 3, 2, mi_back=4 if lit else 5, recess=0.07)
    kk = 2.6 / (ym - y0)
    ov = 0.35
    for (ya, yb) in ((y0 - ov, ym), (ym, y1 + ov)):
        za = g + h - ov * kk if ya < ym else g + h + 2.6
        zb = g + h + 2.6 if ya < ym else g + h - ov * kk
        _wedge_x(mb, [(ya, za), (yb, zb), (yb, zb + 0.12), (ya, za + 0.12)], x0 - 0.35, x1 + 0.35, 1)
    _wedge_x(mb, [(ym - 0.2, g + h + 2.6 + 0.12 - 0.2 * kk + 0.01), (ym, g + h + 2.75), (ym + 0.2, g + h + 2.6 + 0.12 - 0.2 * kk + 0.01),
                  (ym + 0.2, g + h + 2.6 + 0.12 - 0.2 * kk + 0.04), (ym, g + h + 2.78), (ym - 0.2, g + h + 2.6 + 0.12 - 0.2 * kk + 0.04)], x0 - 0.36, x1 + 0.36, 1)   # ridge cap
    for (ya, yb) in ((y0 - ov - 0.03, y0 - ov), (y1 + ov, y1 + ov + 0.03)):                                # eave fascia
        mb.box(x0 - 0.35, x1 + 0.35, ya, yb, g + h - ov * kk - 0.2, g + h - ov * kk + 0.12, 3)
    _gutter(mb, 'X', x0 - 0.35, x1 + 0.35, y0 - ov - 0.03, -1, g + h - ov * kk + 0.1, 6)
    _gutter(mb, 'X', x0 - 0.35, x1 + 0.35, y1 + ov + 0.03, +1, g + h - ov * kk + 0.1, 6)
    _downspout(mb, x0 - 0.075, y0 + 0.3, g, g + h - ov * kk + 0.05, (-1, 0), 6)
    for (xa, xb) in ((x0 - 0.38, x0 - 0.35), (x1 + 0.35, x1 + 0.38)):                                      # rake boards
        _wedge_x(mb, [(y0 - ov, g + h - ov * kk - 0.2), (ym, g + h + 2.6 - 0.2), (ym, g + h + 2.6 + 0.12), (y0 - ov, g + h - ov * kk + 0.12)], xa, xb, 3)
        _wedge_x(mb, [(ym, g + h + 2.6 - 0.2), (y1 + ov, g + h - ov * kk - 0.2), (y1 + ov, g + h - ov * kk + 0.12), (ym, g + h + 2.6 + 0.12)], xa, xb, 3)
    # dormer on the -Y roof plane (photo 28): a box with a gable cap, a framed window, its own rake boards
    dx0, dx1, dy0, dy1 = x0 + 1.2, x0 + 3.0, y0 + 1.2, y0 + 3.4
    mb.box(dx0, dx1, dy0, dy1, g + h + 0.4, g + h + 2.0, 0)
    _wedge_y(mb, [(dx0 - 0.1, g + h + 2.0), (dx1 + 0.1, g + h + 2.0), ((dx0 + dx1) / 2, g + h + 2.65)], dy0 - 0.1, dy1, 0)
    _wedge_y(mb, [(dx0 - 0.25, g + h + 1.9), ((dx0 + dx1) / 2, g + h + 2.65), ((dx0 + dx1) / 2, g + h + 2.75), (dx0 - 0.25, g + h + 2.0)], dy0 - 0.15, dy1 + 0.1, 1)
    _wedge_y(mb, [((dx0 + dx1) / 2, g + h + 2.65), (dx1 + 0.25, g + h + 1.9), (dx1 + 0.25, g + h + 2.0), ((dx0 + dx1) / 2, g + h + 2.75)], dy0 - 0.15, dy1 + 0.1, 1)
    mb.box(dx0 - 0.25, dx1 + 0.25, dy0 - 0.18, dy0 - 0.15, g + h + 1.85, g + h + 2.0, 3)
    _win(mb, 'X', dx0 + 0.35, dx1 - 0.35, dy0, -1, g + h + 0.7, g + h + 1.7, 2, 2, 3, 2, mi_back=5, recess=0.06)
    cx0, cx1, cy0, cy1 = x1 - 3.0, x1 - 2.3, ym - 0.4, ym + 0.4
    mb.box(cx0, cx1, cy0, cy1, g + h, g + h + 3.4, 0)
    mb.box(cx0 - 0.06, cx1 + 0.06, cy0 - 0.06, cy1 + 0.06, g + h + 3.4, g + h + 3.5, 8)
    mb.cylinder((cx0 + cx1) / 2, (cy0 + cy1) / 2, g + h + 3.5, g + h + 3.85, 0.11, 0.1, seg=12, mi=8)
    mb.build("Site_NeighbourEast", [L['stucco_grey'], L['shingle_far'], L['glass_dark'], M['trim'], L['curtain'], L['curtain_dim'], L['galv'],
                                    L['interior_dark'], L['cap']], coll=COLL, smooth=True)

    # ---- cottages across the street: framed windows, doors with a stoop + porch posts and a small roof, eaves
    mb = MB()      # 0 tan stucco, 1 grey stucco, 2 tile, 3 shingle, 4 glass, 5 curtain lit, 6 curtain dim, 7 trim, 8 interior, 9 white stucco
    for i, (x0, x1, kind) in enumerate(((-22.0, -12.0, 'hip'), (-8.0, 0.0, 'gable'), (5.0, 14.0, 'hip'))):
        y0, y1, h = -33.0, -24.0, 4.2 + 0.4 * (i % 2)
        mi_w = (0, 1, 9)[i]
        xm = (x0 + x1) / 2
        wins = []
        for k in range(3):
            wx = x0 + (x1 - x0) * (k + 0.5) / 3
            if abs(wx - xm) < 0.9:
                wx += 1.1
            wins.append((wx - 0.55, wx + 0.55, g + 1.0, g + 2.3, (k + i) % 2 == 0))
        DOOR = (xm - 0.5, xm + 0.5, g, g + 2.1)
        holes = sorted([(a, b, c, d) for (a, b, c, d, _) in wins] + [DOOR])
        mb.wall('X', x0, x1, y1 - WT_, y1, g - 0.1, g + h, holes=holes, mi=mi_w)
        mb.wall('X', x0, x1, y0, y0 + WT_, g - 0.1, g + h, mi=mi_w)
        mb.wall('Y', y0 + WT_, y1 - WT_, x0, x0 + WT_, g - 0.1, g + h, mi=mi_w)
        mb.wall('Y', y0 + WT_, y1 - WT_, x1 - WT_, x1, g - 0.1, g + h, mi=mi_w)
        mb.box(x0 + WT_, x1 - WT_, y0 + WT_, y1 - WT_, g + h - 0.3, g + h, 8)
        for (a, b, c, d, lit) in wins:
            _win(mb, 'X', a, b, y1, +1, c, d, 2, 2, 7, 4, mi_back=5 if lit else 6, recess=0.07)
        _door(mb, 'X', DOOR[0], DOOR[1], y1, +1, DOOR[2], DOOR[3], 7, 7, mi_knob=7, recess=0.12)
        mb.box(DOOR[0] - 0.7, DOOR[1] + 0.7, y1, y1 + 1.4, g - 0.06, g + 0.02, 7)                             # stoop
        for xx in (DOOR[0] - 0.55, DOOR[1] + 0.55):                                                         # porch posts + a little roof
            mb.box(xx - 0.06, xx + 0.06, y1 + 1.15, y1 + 1.27, g, g + 2.45, 7)
        mb.box(DOOR[0] - 0.8, DOOR[1] + 0.8, y1 - 0.05, y1 + 1.45, g + 2.45, g + 2.55, 7)
        _wedge_x(mb, [(y1 - 0.05, g + 2.55), (y1 + 1.5, g + 2.55), (y1 + 1.5, g + 2.62), (y1 - 0.05, g + 3.1)], DOOR[0] - 0.85, DOOR[1] + 0.85, 2 if kind == 'hip' else 3)
        _jelly_light(mb, DOOR[1] + 0.2, y1, g + 2.25, 'X', +1, 8, 10, f"Site_L_Cottage_{i}")
        ov = 0.4
        mb.box(x0 - ov, x1 + ov, y0 - ov, y1 + ov, g + h - 0.02, g + h + 0.15, 7)                            # eave fascia ring
        if kind == 'hip':
            mb.hexa([(x0 - ov, y0 - ov, g + h + 0.15), (x1 + ov, y0 - ov, g + h + 0.15), (x1 + ov, y1 + ov, g + h + 0.15), (x0 - ov, y1 + ov, g + h + 0.15),
                     (x0 + 2.5, y0 + 4.2, g + h + 2.15), (x1 - 2.5, y0 + 4.2, g + h + 2.15), (x1 - 2.5, y1 - 4.2, g + h + 2.15), (x0 + 2.5, y1 - 4.2, g + h + 2.15)], 2)
            mb.tube((x0 + 2.4, y0 + 4.2, g + h + 2.18), (x1 - 2.4, y0 + 4.2, g + h + 2.18), 0.08, 0.08, seg=10, mi=2)
        else:
            _wedge_y(mb, [(x0, g + h), (x1, g + h), (xm, g + h + 2.4)], y0, y0 + WT_, mi_w)
            _wedge_y(mb, [(x0, g + h), (x1, g + h), (xm, g + h + 2.4)], y1 - WT_, y1, mi_w)
            kk = 2.4 / (xm - x0)
            for (xa, xb) in ((x0 - ov, xm), (xm, x1 + ov)):
                za = g + h - ov * kk if xa < xm else g + h + 2.4
                zb = g + h + 2.4 if xa < xm else g + h - ov * kk
                _wedge_y(mb, [(xa, za), (xb, zb), (xb, zb + 0.12), (xa, za + 0.12)], y0 - 0.3, y1 + 0.3, 3)
            mb.tube((xm, y0 - 0.32, g + h + 2.55), (xm, y1 + 0.32, g + h + 2.55), 0.06, 0.06, seg=8, mi=3)
        mb.box(xm + 2.0, xm + 2.6, y0 + 3.0, y0 + 3.6, g + h, g + h + 2.9, mi_w)                             # chimney
        mb.box(xm + 1.95, xm + 2.65, y0 + 2.95, y0 + 3.65, g + h + 2.9, g + h + 3.0, 7)
    mb.build("Site_Cottages", [L['stucco_tan'], L['stucco_grey'], L['tile_far'], L['shingle_far'], L['glass_dark'], L['curtain'], L['curtain_dim'],
                               M['trim'], L['interior_dark'], L['stucco_white'], L['lens_frost']], coll=COLL, smooth=True)


# ---------------------------------------------------------------- outdoor staging
def _festoon(mb, p0, p1, sag=0.25, mi_cord=0, mi_bulb=1, lights=True, name="Site_L_Festoon", every=0.45, light_every=1.35):
    """Catenary of festoon bulbs from p0 to p1 (3D points): a dark cord + small emissive bulbs + a few point lights."""
    p0, p1 = Vector(p0), Vector(p1)
    n = 24
    pts = []
    for i in range(n + 1):
        t = i / n
        p = p0.lerp(p1, t)
        p.z -= sag * 4 * t * (1 - t)
        pts.append(tuple(p))
    mb.path_tube(pts, 0.004, seg=5, mi=mi_cord)
    L = (p1 - p0).length
    k = every / 2
    j = 0
    while k < L:
        t = k / L
        p = p0.lerp(p1, t); p.z -= sag * 4 * t * (1 - t) + 0.06
        mb.cylinder(p.x, p.y, p.z + 0.02, p.z + 0.06, 0.008, seg=6, mi=mi_cord)      # bulb socket
        mb.sphere((p.x, p.y, p.z), 0.028, seg=10, rings=6, mi=mi_bulb)
        if lights and j % max(1, int(round(light_every / every))) == 1:
            add_light(f"{name}_{round(p.x, 1)}_{round(p.y, 1)}", 'POINT', (p.x, p.y, p.z - 0.03), 6, (1.0, 0.8, 0.6), size=0.03)
        k += every
        j += 1


def _teak_chair(mb, x, y, rot, z, mi_wood, mi_seat):
    """Slatted teak dining chair centred at (x, y) facing +Y (rotated by rot): 4 legs, apron, 5 seat slats, 4 back slats,
    a thin seat cushion (sewn pillow)."""
    def B(cx, cy, cz, sx, sy, sz, mi_):
        px, py = rot2(x + cx, y + cy, x, y, rot)
        mb.cbox(px, py, z + cz, sx, sy, sz, mi_, rot)
    w, d = 0.46, 0.48
    for sx_, sy_ in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        B(sx_ * (w / 2 - 0.02), sy_ * (d / 2 - 0.02), 0.22, 0.035, 0.035, 0.44, mi_wood)
    B(0, 0, 0.42, w, d, 0.03, mi_wood)                                    # apron ring (as a thin frame)
    for k in range(5):
        B(0, -d / 2 + 0.05 + k * 0.095, 0.455, w - 0.04, 0.07, 0.02, mi_wood)
    for sx_ in (-1, 1):                                                   # back posts (raked)
        B(sx_ * (w / 2 - 0.02), d / 2 - 0.03, 0.72, 0.035, 0.035, 0.6, mi_wood)
    for k in range(4):
        B(0, d / 2 - 0.03, 0.62 + k * 0.1, w - 0.11, 0.02, 0.065, mi_wood)
    B(0, d / 2 - 0.03, 1.02, w, 0.04, 0.05, mi_wood)                       # top rail
    px, py = rot2(x, y - 0.02, x, y, rot)
    mb.pillow_sq(px, py, z + 0.49, w - 0.06, d - 0.1, 0.045, mi_seat, rot=rot, seed=int(x * 5 + y * 3))


def _teak_table(mb, x, y, z, w, d, mi_wood):
    """Slatted teak table: 4 legs, a frame, slats across the top."""
    h = 0.74
    for sx_, sy_ in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        mb.cbox(x + sx_ * (w / 2 - 0.05), y + sy_ * (d / 2 - 0.05), z + h / 2 - 0.02, 0.06, 0.06, h - 0.04, mi_wood)
    mb.cbox(x, y, z + h - 0.06, w, d, 0.05, mi_wood)
    n = int(d / 0.09)
    for k in range(n):
        yy = y - d / 2 + 0.03 + (d - 0.06) * (k + 0.5) / n
        mb.cbox(x, yy, z + h - 0.015, w - 0.02, (d - 0.06) / n - 0.012, 0.03, mi_wood)


def _lantern(mb, x, y, z, mi_black, mi_glass, mi_candle, name, s=0.16, h=0.26):
    for sx_, sy_ in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        mb.box(x + sx_ * s / 2 - 0.008, x + sx_ * s / 2 + 0.008, y + sy_ * s / 2 - 0.008, y + sy_ * s / 2 + 0.008, z, z + h, mi_black)
    mb.box(x - s / 2, x + s / 2, y - s / 2, y + s / 2, z, z + 0.015, mi_black)
    mb.box(x - s / 2 - 0.01, x + s / 2 + 0.01, y - s / 2 - 0.01, y + s / 2 + 0.01, z + h, z + h + 0.012, mi_black)
    mb.hexa([(x - s / 2, y - s / 2, z + h + 0.012), (x + s / 2, y - s / 2, z + h + 0.012), (x + s / 2, y + s / 2, z + h + 0.012), (x - s / 2, y + s / 2, z + h + 0.012),
             (x - 0.03, y - 0.03, z + h + 0.07), (x + 0.03, y - 0.03, z + h + 0.07), (x + 0.03, y + 0.03, z + h + 0.07), (x - 0.03, y + 0.03, z + h + 0.07)], mi_black)
    mb.tube((x, y, z + h + 0.07), (x, y, z + h + 0.12), 0.006, 0.006, seg=6, mi=mi_black)
    mb.box(x - s / 2 + 0.008, x + s / 2 - 0.008, y - s / 2 + 0.008, y + s / 2 - 0.008, z + 0.015, z + h, mi_glass)
    mb.cylinder(x, y, z + 0.015, z + 0.10, 0.035, seg=12, mi=mi_candle)
    add_light(name, 'POINT', (x, y, z + 0.12), 4, (1.0, 0.72, 0.4), size=0.03)


def _mailbox(mb, x, y, g, mi_post, mi_box, mi_flag, mi_trim):
    """US rural mailbox (round-top steel box, door, flag) on a 4x4 post with a bracket, the house number on its side."""
    mb.box(x - 0.045, x + 0.045, y - 0.045, y + 0.045, g - 0.35, g + 1.05, mi_post)
    mb.box(x - 0.09, x + 0.09, y - 0.30, y + 0.30, g + 1.05, g + 1.09, mi_post)
    mb.box(x - 0.02, x + 0.02, y - 0.02, y + 0.16, g + 0.85, g + 1.05, mi_post)                            # bracket knee
    bw, bh, bl = 0.17, 0.12, 0.50                                                                          # body: rectangle + half-round top
    z0 = g + 1.09
    prof = [(-bw / 2, 0), (bw / 2, 0)] + [(bw / 2 * math.cos(a), bh + bw / 2 * math.sin(a)) for a in [math.pi * k / 10 for k in range(0, 11)]]
    prof = [(-bw / 2, 0), (bw / 2, 0), (bw / 2, bh)] + [(bw / 2 * math.cos(math.pi * k / 10), bh + bw / 2 * math.sin(math.pi * k / 10)) for k in range(1, 10)] + [(-bw / 2, bh)]
    secs = [[(x + px, y - bl / 2, z0 + pz) for (px, pz) in prof], [(x + px, y + bl / 2, z0 + pz) for (px, pz) in prof]]
    mb.sweep(secs, mi_box)
    mb.box(x - bw / 2 - 0.006, x + bw / 2 + 0.006, y - bl / 2 - 0.012, y - bl / 2, z0, z0 + bh + bw / 2 + 0.006, mi_box)   # door rim
    mb.box(x - 0.03, x + 0.03, y - bl / 2 - 0.03, y - bl / 2 - 0.012, z0 + bh + 0.02, z0 + bh + 0.035, mi_box)          # door pull
    mb.box(x + bw / 2, x + bw / 2 + 0.012, y - 0.05, y + 0.05, z0 + 0.03, z0 + 0.05, mi_flag)                            # flag pivot
    mb.box(x + bw / 2 + 0.004, x + bw / 2 + 0.012, y + 0.03, y + 0.05, z0 + 0.03, z0 + 0.32, mi_flag)                    # flag (up)
    mb.box(x + bw / 2 + 0.004, x + bw / 2 + 0.012, y - 0.02, y + 0.08, z0 + 0.32, z0 + 0.40, mi_flag)
    xx = x - 0.12
    for d in "1836":                                                                                       # number on the street face
        _digit(mb, xx, z0 + 0.03, y - bl / 2 - 0.012, d, mi_trim, s=0.06)
        xx += 0.05


def _street_lamp(mb, x, y, g, mi_pole, mi_lens):
    """Period street lamp: a fluted tapered pole on a base, an acorn glass head; a warm point light."""
    mb.cylinder(x, y, g - 0.2, g + 0.1, 0.12, 0.12, seg=16, mi=mi_pole)
    mb.lathe(x, y, g + 0.1, [(0.10, 0), (0.10, 0.05), (0.065, 0.14), (0.05, 0.6), (0.042, 3.4), (0.04, 3.6), (0.06, 3.63), (0.06, 3.68), (0.035, 3.74), (0, 3.74)], seg=16, mi=mi_pole)
    mb.lathe(x, y, g + 3.84, [(0, 0), (0.06, 0), (0.16, 0.22), (0.2, 0.45), (0.15, 0.62), (0.05, 0.72), (0, 0.72)], seg=18, mi=mi_lens)
    mb.lathe(x, y, g + 4.5, [(0.04, 0), (0.09, 0.02), (0.08, 0.06), (0.03, 0.1), (0.025, 0.16), (0, 0.16)], seg=12, mi=mi_pole)
    add_light("Site_L_StreetLamp", 'POINT', (x, y, g + 4.2), 260, (1.0, 0.82, 0.6), size=0.25)


def _staging(M):
    L = _local(M)
    g = Z_GRADE
    # ---- patio: slatted teak dining set on the garage side (the strip x 0.2..2.4 from the steps to the lawn stays clear)
    mb = MB()      # 0 teak, 1 cushion, 2 ceramic, 3 glass, 4 iron, 5 candle, 6 blanket
    tx, ty = 3.7, 20.4
    _teak_table(mb, tx, ty, g + 0.02, 0.85, 1.6, 0)
    for (cx, cy, rot) in ((2.95, 19.95, -math.pi / 2), (2.95, 20.85, -math.pi / 2), (4.45, 19.95, math.pi / 2), (4.45, 20.85, math.pi / 2)):
        _teak_chair(mb, cx, cy, rot, g + 0.02, 0, 1)
    # tabletop dressing: a bowl + tumblers + a candle lantern
    mb.lathe(tx, ty + 0.2, g + 0.76, [(0, 0), (0.1, 0), (0.15, 0.05), (0.16, 0.08), (0.14, 0.08), (0.08, 0.03), (0, 0.02)], seg=20, mi=2)
    for (ox, oy) in ((-0.22, -0.3), (0.2, -0.42), (0.24, 0.05)):
        mb.lathe(tx + ox, ty + oy, g + 0.76, [(0, 0), (0.03, 0), (0.034, 0.09), (0.03, 0.09), (0.027, 0.01), (0, 0.01)], seg=12, mi=3)
    _lantern(mb, tx - 0.05, ty - 0.45, g + 0.76, 4, 3, 5, "Site_L_TableLantern")
    # lounge: a 2-seat outdoor sofa along the patio's -X edge facing +X, a low round table, a folded blanket + cushions
    outdoor_sofa(mb, -1.02, 19.3, 1.6, d=0.9, rot=math.pi / 2, z=g + 0.02, mi_frame=0, mi_cushion=1, seats=2)
    mb.pillow_sq(-0.95, 18.85, g + 0.02 + 0.66, 0.45, 0.45, 0.13, 1, rot=math.pi / 2, pitch=1.2, seed=4)
    mb.pillow_sq(-0.95, 19.75, g + 0.02 + 0.66, 0.45, 0.45, 0.13, 6, rot=math.pi / 2, pitch=1.15, seed=5)
    mb.rcbox(-1.25, 19.55, g + 0.02 + 0.47, 0.42, 0.34, 0.06, r=0.02, mi=6, puff=0.5)                     # folded blanket on the arm end
    round_table(mb, -0.15, 19.3, g + 0.02, 0.28, h=0.38, top_t=0.03, mi=0, mi_leg=0, legs='three')
    _lantern(mb, -0.15, 19.3, g + 0.02 + 0.38, 4, 3, 5, "Site_L_LoungeLantern", s=0.12, h=0.2)
    mb.build("Site_PatioFurniture", [M['teak'], L['cushion'], M['ceramic'], M['glass'], M['iron_black'], L['candle'], L['blanket']], coll=COLL, smooth=True)

    # planters (archviz.plants): an olive + a boxwood by the garage wall, a fern by the steps, a lemon behind the garage
    plants.potted("Site_Pot_Olive", (4.65,20.7,g), kind='olive', height=1.35, pot='terracotta', seed=4, coll=COLL)
    plants.potted("Site_Pot_Box", (4.62, 21.5, g + 0.0), kind='boxwood', height=0.7, pot='concrete', seed=5, coll=COLL)
    plants.potted("Site_Pot_Fern", (-2.1,18.2,g), kind='fern', height=0.5, pot='terracotta', seed=6, coll=COLL)
    plants.potted("Site_Pot_Citrus", (9.5, 25.5, g + 0.0), kind='citrus', height=1.3, pot='terracotta', seed=7, coll=COLL)

    # festoon string lights: a U round the patio perimeter at ~2.6 m (posts at the far corners + the gate post)
    mb = MB()      # 0 cord / posts, 1 bulb, 2 galv
    px0, px1, py0, py1 = PATIO
    for (qx, qy) in ((px0 + 0.06, py1 - 0.06), (px1 - 0.12, py1 - 0.06)):
        mb.cylinder(qx, qy, g - 0.3, 2.7, 0.03, seg=10, mi=0)                             # post
        mb.cylinder(qx, qy, g - 0.01, g + 0.02, 0.11, seg=14, mi=2)                       # base plate
        mb.cylinder(qx, qy, g + 0.02, g + 0.2, 0.045, 0.032, seg=10, mi=2)                # base sleeve
        mb.sphere((qx, qy, 2.72), 0.035, seg=10, rings=6, mi=0)                           # finial
        gx_ = qx - 0.75 if qx < 1.0 else qx                                               # guy wire to a ground stake (away from the lawn edge)
        gy_ = qy + 0.75
        mb.tube((qx, qy, 2.6), (gx_, gy_, g + 0.05), 0.003, 0.003, seg=4, mi=2)
        mb.cylinder(gx_, gy_, g - 0.25, g + 0.08, 0.012, seg=6, mi=2)
    mb.cylinder(-1.2,BED_REAR+WT+.01,2.5,2.62, 0.012, seg=8, mi=0)                               # hook on the house rear wall
    _festoon(mb, (-1.2,BED_REAR+WT+.03,2.6), (px0 + 0.06, py1 - 0.06, 2.65), name="Site_L_FestW")
    _festoon(mb, (px0 + 0.06, py1 - 0.06, 2.65), (px1 - 0.12, py1 - 0.06, 2.65), name="Site_L_FestN")
    _festoon(mb, (px1 - 0.12, py1 - 0.06, 2.65), (GATE[1] - 0.09, GATE[2] + 0.02, 2.7), name="Site_L_FestE")
    mb.build("Site_Festoon", [L['cord'], L['bulb'], L['galv']], coll=COLL, smooth=True)

    # ---- porch: two rattan chairs with cushions, a side table, planters (x -1.25..0.7 stays clear), a coir doormat
    mb = MB()
    for (cx, cy) in ((3.35, 1.15), (4.6, 1.15)):
        armchair(mb, cx, cy, rot=0.0, z=0.0, w=0.8, d=0.8, mi=0, mi_legs=0, style='barrel')
        mb.pillow_sq(cx, cy + 0.02, 0.465, 0.5, 0.5, 0.09, 1, seed=int(cx * 10))
        mb.pillow_sq(cx, cy + 0.24, 0.66, 0.44, 0.42, 0.11, 2, pitch=1.15, seed=int(cx * 10) + 1)
    round_table(mb, 3.975, 1.15, 0.0, 0.18, h=0.5, top_t=0.03, mi=0, mi_leg=0, legs='three')
    mb.lathe(3.975, 1.15, 0.5, [(0, 0), (0.04, 0), (0.05, 0.12), (0.03, 0.2), (0.02, 0.24), (0, 0.24)], seg=14, mi=3)   # a small vase
    sx0, sx1, sy0, sy1 = PORCH_STEPS
    td = (sy1 - sy0) / 4                                                                                                # tread depth
    mb.rcbox(-0.28, -0.06, 0.009, 0.72, 0.26, 0.018, r=0.006, mi=4)                                                   # coir mat inside the arch recess (tower face y -0.2, door at y 0.125)
    mb.build("Site_PorchFurniture", [M['cane'], L['cushion'], L['cushion_grey'], M['ceramic'], L['doormat']], coll=COLL, smooth=True)
    plants.stems("Site_PorchVaseStems", (3.975, 1.15, 0.74), kind='olive', height=0.35, n=4, seed=8, coll=COLL)
    plants.potted("Site_PorchPot_W", (1.7, 0.6, 0.0), kind='olive', height=1.1, pot='terracotta', seed=9, coll=COLL)
    plants.potted("Site_PorchPot_E", (5.2, 0.55, 0.0), kind='boxwood', height=0.65, pot='terracotta', seed=12, coll=COLL)
    plants.potted("Site_PorchPot_Lav", (2.45, 0.5, 0.0), kind='lavender', height=0.4, pot='terracotta', seed=13, coll=COLL)

    # house numbers "1836" on the entry wall right of the arch (photo 00), the mailbox, irrigation valves, a hose bib
    mb = MB()      # 0 iron, 1 brass, 2 post, 3 box, 4 flag, 5 trim, 6 copper
    # (the brass "1836" is exterior's, on the proud entry-tower face)
    _mailbox(mb, 0.9, -8.71, g, 2, 3, 4, 5)
    vy = -0.72
    mb.tube((-1.72, vy, g + 0.16), (-1.28, vy, g + 0.16), 0.012, 0.012, seg=8, mi=6)                     # manifold
    for k in range(4):                                                                                  # 4 anti-siphon valves on risers
        vx = -1.65 + k * 0.1
        mb.cylinder(vx, vy, g - 0.2, g + 0.3, 0.011, seg=8, mi=6)
        mb.cylinder(vx, vy - 0.06, g - 0.2, g + 0.16, 0.011, seg=8, mi=6)
        mb.tube((vx, vy - 0.06, g + 0.16), (vx, vy, g + 0.16), 0.011, 0.011, seg=8, mi=6)
        mb.cbox(vx, vy, g + 0.33, 0.055, 0.075, 0.06, 1)                                                 # valve body
        mb.cylinder(vx, vy, g + 0.36, g + 0.41, 0.026, 0.02, seg=10, mi=1)                              # bonnet
        mb.cylinder(vx, vy, g + 0.41, g + 0.425, 0.034, seg=10, mi=0)                                   # round handle
        mb.cylinder(vx, vy + 0.045, g + 0.31, g + 0.35, 0.02, seg=8, mi=1)                              # solenoid
    mb.tube((1.5, 0.0, -0.25), (1.5, -0.09, -0.25), 0.012, 0.012, seg=8, mi=1)                          # hose bib on the porch parapet's street face (photo 00)
    mb.tube((1.5, -0.09, -0.25), (1.5, -0.09, -0.31), 0.012, 0.012, seg=8, mi=1)
    mb.cylinder(1.5, -0.09, -0.25, -0.19, 0.02, seg=10, mi=1)
    mb.cylinder(1.05, -0.09, -0.14, -0.13, 0.028, seg=8, mi=0)
    mb.build("Site_Small", [M['iron_black'], M['brass'], L['post_grey'], L['mailbox'], L['flag_red'], M['trim'], L['copper']], coll=COLL, smooth=True)
    # hose reel on the driveway-side house wall (the hose bib is exterior's at 5.86, 8.0): bracket, axle, drum, a coiled hose
    mb = MB()      # 0 iron, 1 hose
    mb.box(5.75, 5.9, 7.62, 7.78, -0.22, -0.16, 0)                                        # wall bracket
    mb.box(5.75, 5.9, 7.62, 7.78, 0.10, 0.16, 0)
    mb.box(5.86, 5.9, 7.64, 7.76, -0.22, 0.16, 0)
    mb.tube((5.9, 7.7, -0.03), (6.12, 7.7, -0.03), 0.015, 0.015, seg=8, mi=0)              # axle
    mb.tube((5.93, 7.7, -0.03), (5.95, 7.7, -0.03), 0.19, 0.19, seg=20, mi=0)              # drum flanges
    mb.tube((6.07, 7.7, -0.03), (6.09, 7.7, -0.03), 0.19, 0.19, seg=20, mi=0)
    mb.tube((5.95, 7.7, -0.03), (6.07, 7.7, -0.03), 0.07, 0.07, seg=14, mi=0)              # hub
    for k in range(4):                                                                     # coiled hose (rings)
        xx = 5.965 + k * 0.03
        rr = 0.085 + (k % 2) * 0.026
        ring = [(xx, 7.7 + rr * math.cos(a), -0.03 + rr * math.sin(a)) for a in [2 * math.pi * i / 24 for i in range(25)]]
        mb.path_tube(ring, 0.013, seg=6, mi=1)
    mb.tube((6.12, 7.7, -0.03), (6.16, 7.7, -0.03), 0.03, 0.03, seg=10, mi=0)              # crank boss
    mb.tube((6.16, 7.7, -0.03), (6.16, 7.7 + 0.12, -0.03), 0.008, 0.008, seg=6, mi=0)
    mb.tube((6.16, 7.82, -0.03), (6.22, 7.82, -0.03), 0.012, 0.012, seg=6, mi=0)
    mb.build("Site_HoseReel", [M['iron_black'], _mat.new_mat("HoseGreen", (0.10, 0.22, 0.10, 1), rough=0.6)], coll=COLL, smooth=True)

    # path bollards along the front walk (a visible frosted lens under the cap)
    mb = MB()
    for (bx, by) in ((-0.85, -5.5), (0.85, -5.5), (-0.85, -2.5), (0.85, -2.5)):
        mb.cylinder(bx, by, g - 0.15, g + 0.38, 0.04, seg=14, mi=0)
        mb.cylinder(bx, by, g + 0.38, g + 0.45, 0.036, seg=14, mi=1)
        mb.cylinder(bx, by, g + 0.45, g + 0.5, 0.05, seg=14, mi=0)
        add_light(f"Site_L_Bollard_{bx:+.1f}_{by:+.1f}", 'POINT', (bx, by, g + 0.41), 8, K30, size=0.04)
    mb.build("Site_Bollards", [M['iron_black'], L['lens']], coll=COLL, smooth=True)

    # street lamp on the parkway, outside the front camera corridor (x -3..8)
    mb = MB()
    _street_lamp(mb, -12.6, -8.95, g, 0, 1)
    mb.build("Site_StreetLamp", [L['steel_pole'], L['lens']], coll=COLL, smooth=True)


# ---------------------------------------------------------------- entry point
def build(M):
    _local(M)
    _ground(M)
    _hardscape(M)
    _fences(M)
    _garage(M)
    _shed(M)
    _neighbours(M)
    _staging(M)
