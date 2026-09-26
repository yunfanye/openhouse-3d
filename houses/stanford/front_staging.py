"""Staging kit for the Stanford front rooms (photos 04-07, 24): the procedural textiles, finishes and art of the foyer /
living room / hall, and parametric builders for the pieces the listing photos show (flare-arm sofa, slipper chairs, the
oval glass cocktail table with S-curved legs, the embossed octagonal side tables, the hammered vase, the brass bar cart,
the bronze candlestick lamp, the demilune console + embossed mirror, a peace lily and a dracaena in blue-and-white
porcelain, swag valances with jabots over embroidered sheers).

Imported only by interior_front.py.  Every builder works in world coordinates on an archviz MB and takes the material
index to use, so a caller can batch several pieces into one object.  Materials are registered under 'fs_*' keys.
Patterns are computed in a per-face 2D frame (`_surf_ab`): horizontal faces use (x, y), vertical faces use
(horizontal tangent, z), so a print reads the same on a pillow, a seat or a curtain without UV maps.
"""
import math
import random

from archviz import materials as _m
from archviz.mesh import MB, rot2

TAU = 2 * math.pi


# ================================================================ node helpers
def _sep(nt, sock):
    s = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(s.inputs["Vector"], sock)
    return s.outputs["X"], s.outputs["Y"], s.outputs["Z"]


def _comb(nt, x, y, z=0.0):
    c = nt.nodes.new("ShaderNodeCombineXYZ")
    for sock, v in zip(("X", "Y", "Z"), (x, y, z)):
        if hasattr(v, 'is_output'):
            nt.links.new(c.inputs[sock], v)
        else:
            c.inputs[sock].default_value = v
    return c.outputs["Vector"]


def _M(nt):
    return lambda op, a, b=None, clamp=False: _m._math(nt, op, a, b, clamp)


def _surf_ab(nt, scale=1.0, plane='auto'):
    """(a, b) pattern coordinates in metres * scale.  plane 'auto': horizontal faces (|n.z| > 0.7) use (x, y), others
    the horizontal tangent of the face and z (flat upholstery panels, curtains); 'XZ' / 'YZ' / 'XY' project on a fixed
    world plane (puffy pillows, where the normal wanders and would smear the print)."""
    M = _M(nt)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    px, py, pz = _sep(nt, tc.outputs["Object"])
    if plane != 'auto':
        c = {'X': px, 'Y': py, 'Z': pz}
        return M('MULTIPLY', c[plane[0]], scale), M('MULTIPLY', c[plane[1]], scale)
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    nx, ny, nz = _sep(nt, geo.outputs["Normal"])
    hl = M('ADD', M('SQRT', M('ADD', M('MULTIPLY', nx, nx), M('MULTIPLY', ny, ny))), 1e-4)
    av = M('DIVIDE', M('SUBTRACT', M('MULTIPLY', py, nx), M('MULTIPLY', px, ny)), hl)
    w = M('GREATER_THAN', M('ABSOLUTE', nz), 0.7)
    a = M('ADD', av, M('MULTIPLY', w, M('SUBTRACT', px, av)))
    b = M('ADD', pz, M('MULTIPLY', w, M('SUBTRACT', py, pz)))
    return M('MULTIPLY', a, scale), M('MULTIPLY', b, scale)


def _vor2(nt, a, b, rand=0.85):
    v = nt.nodes.new("ShaderNodeTexVoronoi")
    v.voronoi_dimensions = '2D'
    v.inputs["Scale"].default_value = 1.0
    v.inputs["Randomness"].default_value = rand
    nt.links.new(v.inputs["Vector"], _comb(nt, a, b))
    return v


def _const_ramp(nt, fac, stops):
    out = _m._ramp(nt, fac, stops)
    out.node.color_ramp.interpolation = 'CONSTANT'
    return out


def _fabric_finish(nt, b, col, rough=0.92, sheen=0.7, weave=160.0, bump=0.18):
    """Upholstery finish: the sheen is tinted by the print itself (a white sheen washes woven colours out at the grazing
    angles of a low listing-photo camera)."""
    nt.links.new(b.inputs["Base Color"], col)
    _m._set(b, "Roughness", rough); _m._set(b, "Sheen Weight", sheen * 0.25); _m._set(b, "Specular IOR Level", 0.25)
    if b.inputs.get("Sheen Tint") is not None:
        nt.links.new(b.inputs["Sheen Tint"], col)
    w = _m._noise(nt, _m._coords(nt), scale=weave, detail=2.0)
    _m._bump(nt, b, w, bump, 0.002)


# ================================================================ textiles
def floral_print(name, ground=(0.040, 0.024, 0.017, 1), petal=(0.30, 0.34, 0.31, 1), light=(0.44, 0.48, 0.44, 1), scale=4.6, plane='auto'):
    """Sofa pillows (photos 05, 06): big pale-sage blossoms with separated petals, small florets and thin vines on a
    chocolate ground."""
    m, nt, b = _m._new(name)
    M = _M(nt)
    a, bb = _surf_ab(nt, scale, plane)
    vor = _vor2(nt, a, bb, 0.75)
    cx, cy, _ = _sep(nt, vor.outputs["Position"])
    rnd, _, _ = _sep(nt, vor.outputs["Color"])
    lx, ly = M('SUBTRACT', a, cx), M('SUBTRACT', bb, cy)
    r = vor.outputs["Distance"]
    th = M('ADD', M('ARCTAN2', ly, lx), M('MULTIPLY', rnd, 6.0))
    k = M('ABSOLUTE', M('COSINE', M('MULTIPLY', th, 2.5)))
    size = M('ADD', 0.72, M('MULTIPLY', rnd, 0.35))
    edge = M('MULTIPLY', M('ADD', 0.22, M('MULTIPLY', M('POWER', k, 0.6), 0.24)), size)
    flower = M('LESS_THAN', r, edge)
    split = M('MULTIPLY', M('LESS_THAN', M('ABSOLUTE', M('SINE', M('MULTIPLY', th, 2.5))), 0.07), M('GREATER_THAN', r, 0.06))
    eye = M('LESS_THAN', r, M('MULTIPLY', 0.065, size))
    ring = M('MULTIPLY', M('GREATER_THAN', r, M('MULTIPLY', edge, 0.55)), M('LESS_THAN', r, M('MULTIPLY', edge, 0.62)))
    f2 = _vor2(nt, M('MULTIPLY', a, 2.6), M('MULTIPLY', bb, 2.6), 1.0)
    floret = M('LESS_THAN', f2.outputs["Distance"], 0.16)
    n = _m._noise(nt, _comb(nt, M('MULTIPLY', a, 1.4), M('MULTIPLY', bb, 1.4), 0.3), scale=1.0, detail=2.0)
    vine = M('LESS_THAN', M('ABSOLUTE', M('SUBTRACT', n, 0.5)), 0.022)
    col = _m._mixrgb(nt, M('MULTIPLY', M('MAXIMUM', floret, vine), M('SUBTRACT', 1.0, flower)), ground, petal)
    col = _m._mixrgb(nt, flower, col, petal)
    col = _m._mixrgb(nt, M('MULTIPLY', flower, ring), col, light)
    col = _m._mixrgb(nt, M('MULTIPLY', flower, M('MAXIMUM', split, eye)), col, ground)
    _fabric_finish(nt, b, col, sheen=0.8)
    return m


def leaf_print(name, ground=(0.50, 0.43, 0.32, 1), leaf=(0.31, 0.295, 0.22, 1), line=(0.58, 0.53, 0.43, 1), scale=5.0):
    """Slipper-chair upholstery (photos 04, 06): large outlined heart leaves with lighter veins, sage-taupe on cream."""
    m, nt, b = _m._new(name)
    M = _M(nt)
    a, bb = _surf_ab(nt, scale)
    vor = _vor2(nt, a, bb, 0.9)
    cx, cy, _ = _sep(nt, vor.outputs["Position"])
    rnd, rnd2, _ = _sep(nt, vor.outputs["Color"])
    lx, ly = M('SUBTRACT', a, cx), M('SUBTRACT', bb, cy)
    ang = M('MULTIPLY', rnd, TAU)
    ca, sa = M('COSINE', ang), M('SINE', ang)
    u = M('ADD', M('MULTIPLY', lx, ca), M('MULTIPLY', ly, sa))
    v = M('SUBTRACT', M('MULTIPLY', ly, ca), M('MULTIPLY', lx, sa))
    L = M('ADD', 0.40, M('MULTIPLY', rnd2, 0.12))
    t = M('DIVIDE', u, L)
    tt = M('SUBTRACT', 1.0, M('MULTIPLY', t, t))
    half = M('MULTIPLY', M('MULTIPLY', M('POWER', M('MAXIMUM', tt, 0.0), 0.7), M('ADD', 1.0, M('MULTIPLY', t, -0.3))), M('MULTIPLY', L, 0.62))
    av = M('ABSOLUTE', v)
    inside = M('MULTIPLY', M('LESS_THAN', av, half), M('LESS_THAN', M('ABSOLUTE', t), 1.0))
    outline = M('MULTIPLY', inside, M('GREATER_THAN', av, M('SUBTRACT', half, 0.028)))
    rib = M('MULTIPLY', inside, M('LESS_THAN', av, 0.010))
    lat = M('MULTIPLY', inside, M('LESS_THAN', M('FRACT', M('SUBTRACT', M('MULTIPLY', t, 3.5), M('MULTIPLY', av, 5.0))), 0.07))
    col = _m._mixrgb(nt, M('MULTIPLY', inside, 0.85), ground, leaf)
    col = _m._mixrgb(nt, M('MAXIMUM', M('MAXIMUM', rib, lat), outline), col, line)
    _fabric_finish(nt, b, col, sheen=0.55, weave=190.0)
    return m


def stripe_print(name, stops, period=0.30, axis='Z', sheen=0.8):
    """Woven stripes: `stops` = [(pos 0..1, colour)] repeating every `period` m along the world axis 'X' / 'Y' / 'Z'."""
    m, nt, b = _m._new(name)
    M = _M(nt)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    px, py, pz = _sep(nt, tc.outputs["Object"])
    f = M('FRACT', M('DIVIDE', {'X': px, 'Y': py, 'Z': pz}[axis], period))
    col = _const_ramp(nt, f, stops)
    fine = _m._noise(nt, _m._coords(nt, scale=(240, 240, 240)), scale=1.0, detail=1.0)
    col = _m._mixrgb(nt, M('MULTIPLY', fine, 0.2), col, (0.8, 0.8, 0.8, 1), 'MULTIPLY')
    _fabric_finish(nt, b, col, sheen=sheen, weave=220.0, bump=0.12)
    return m


def chenille(name, base, weave=120.0):
    """Sofa chenille: soft weave bump, a low sheen tinted like the yarn."""
    tint = tuple(min(1.0, c * 1.6) for c in base[:3]) + (1,)
    m = _m.fabric(name, base, rough=0.95, sheen=0.12, weave=weave, bump=0.3, sheen_tint=tint)
    return m


def sheer(name, ground=(0.86, 0.84, 0.78, 1), alpha=0.55, thread=None, motif='sprig', period=(0.13, 0.42)):
    """Semi-transparent sheer: translucent + transparent mix; optional embroidery (opaque thread) - 'sprig' rows of
    small flowers on stems (photo 04 sheers), 'wheat' sparse leaf sprays (the swag fabric)."""
    m, nt, b = _m._new(name)
    M = _M(nt)
    _m._set(b, "Base Color", ground); _m._set(b, "Roughness", 0.75); _m._set(b, "Sheen Weight", 0.6)
    tr = nt.nodes.new("ShaderNodeBsdfTranslucent"); tr.inputs["Color"].default_value = ground
    tp = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix1 = nt.nodes.new("ShaderNodeMixShader"); mix1.inputs["Fac"].default_value = 0.5
    nt.links.new(mix1.inputs[1], b.outputs["BSDF"]); nt.links.new(mix1.inputs[2], tr.outputs["BSDF"])
    fac = alpha
    if thread is not None:
        pa, pb = period
        a, bb = _surf_ab(nt, 1.0)
        row = M('FLOOR', M('DIVIDE', bb, pb))
        ca = M('SUBTRACT', M('FRACT', M('ADD', M('DIVIDE', a, pa), M('MULTIPLY', row, 0.5))), 0.5)       # -0.5..0.5 across a cell
        cb = M('FRACT', M('DIVIDE', bb, pb))                                                           # 0..1 up a row
        k = pb / pa
        if motif == 'sprig':
            # a hair-thin curved stem, a three-petal bud and two small leaves, ~5 cm tall, in staggered rows
            stem = M('MULTIPLY', M('LESS_THAN', M('ABSOLUTE', M('ADD', ca, M('MULTIPLY', M('SUBTRACT', cb, 0.45), M('SUBTRACT', cb, 0.45)))), 0.012),
                     M('MULTIPLY', M('GREATER_THAN', cb, 0.40), M('LESS_THAN', cb, 0.60)))
            bud = 0.0
            for (ox, oy) in ((-0.035, 0.64), (0.035, 0.64), (0.0, 0.665)):
                dx, dy = M('SUBTRACT', ca, ox), M('MULTIPLY', M('SUBTRACT', cb, oy), k)
                bud = M('MAXIMUM', bud, M('LESS_THAN', M('ADD', M('MULTIPLY', dx, dx), M('MULTIPLY', dy, dy)), 0.0016))
            leaves = 0.0
            for (ox, oy) in ((-0.05, 0.50), (0.05, 0.47)):
                dx, dy = M('SUBTRACT', ca, ox), M('MULTIPLY', M('SUBTRACT', cb, oy), k * 0.45)
                leaves = M('MAXIMUM', leaves, M('LESS_THAN', M('ADD', M('MULTIPLY', dx, dx), M('MULTIPLY', dy, dy)), 0.0012))
            mark = M('MAXIMUM', M('MAXIMUM', stem, bud), leaves)
        else:   # 'wheat': a slanted stem with paired leaflets, sparse (every other cell)
            keep = M('LESS_THAN', M('FRACT', M('MULTIPLY', M('ADD', M('FLOOR', M('DIVIDE', a, pa)), row), 0.5)), 0.25)
            s = M('ADD', ca, M('MULTIPLY', M('SUBTRACT', cb, 0.5), 0.5))
            stem = M('MULTIPLY', M('LESS_THAN', M('ABSOLUTE', s), 0.02), M('MULTIPLY', M('GREATER_THAN', cb, 0.2), M('LESS_THAN', cb, 0.8)))
            lf = M('MULTIPLY', M('LESS_THAN', M('ABSOLUTE', M('SUBTRACT', M('ABSOLUTE', s), 0.07)), 0.05),
                   M('LESS_THAN', M('FRACT', M('MULTIPLY', cb, 5.0)), 0.45))
            lf = M('MULTIPLY', lf, M('MULTIPLY', M('GREATER_THAN', cb, 0.35), M('LESS_THAN', cb, 0.82)))
            mark = M('MULTIPLY', M('MAXIMUM', stem, lf), keep)
        fac = M('ADD', alpha, M('MULTIPLY', mark, 1.0 - alpha))
        col = _m._mixrgb(nt, mark, ground, thread)
        nt.links.new(b.inputs["Base Color"], col); nt.links.new(tr.inputs["Color"], col)
    mix2 = nt.nodes.new("ShaderNodeMixShader")
    if hasattr(fac, 'is_output'):
        nt.links.new(mix2.inputs["Fac"], fac)
    else:
        mix2.inputs["Fac"].default_value = fac
    nt.links.new(mix2.inputs[1], tp.outputs["BSDF"]); nt.links.new(mix2.inputs[2], mix1.outputs["Shader"])
    nt.links.new(nt.nodes["Material Output"].inputs["Surface"], mix2.outputs["Shader"])
    return m


def patterned_rug(name, ground=(0.045, 0.046, 0.050, 1), motif=(0.15, 0.165, 0.168, 1), mid=(0.065, 0.066, 0.072, 1),
                  border=(0.16, 0.17, 0.17, 1), edge=(0.035, 0.035, 0.04, 1), tile=0.12, bw=(0.012, 0.045, 0.058)):
    """Machine-woven entry rug (photo 04): charcoal field with an all-over light-grey medallion lattice, a pale grey
    border band between thin dark lines.  Border widths `bw` are fractions of the rug's bounding box (Generated)."""
    m, nt, b = _m._new(name)
    M = _M(nt)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    gx, gy, _ = _sep(nt, tc.outputs["Generated"])
    px, py, _ = _sep(nt, tc.outputs["Object"])
    e = M('MINIMUM', M('MINIMUM', gx, M('SUBTRACT', 1.0, gx)), M('MINIMUM', gy, M('SUBTRACT', 1.0, gy)))
    sx = M('ABSOLUTE', M('SUBTRACT', M('FRACT', M('DIVIDE', px, tile)), 0.5))
    sy = M('ABSOLUTE', M('SUBTRACT', M('FRACT', M('DIVIDE', py, tile)), 0.5))
    rr = M('SQRT', M('ADD', M('MULTIPLY', sx, sx), M('MULTIPLY', sy, sy)))
    lat = M('MAXIMUM', M('LESS_THAN', M('ABSOLUTE', M('SUBTRACT', rr, 0.33)), 0.03), M('LESS_THAN', M('ABSOLUTE', M('SUBTRACT', sx, sy)), 0.022))
    petals = M('LESS_THAN', M('ADD', M('MULTIPLY', M('SUBTRACT', sx, 0.5), M('SUBTRACT', sx, 0.5)), M('MULTIPLY', sy, sy)), 0.012)
    dots = M('LESS_THAN', rr, 0.07)
    n = _m._noise(nt, _m._coords(nt, scale=(9, 9, 9)), scale=1.0, detail=3.0, distortion=1.5)
    scroll = M('LESS_THAN', M('ABSOLUTE', M('SUBTRACT', n, 0.5)), 0.03)
    col = _m._mixrgb(nt, M('MULTIPLY', M('GREATER_THAN', rr, 0.2), 0.5), ground, mid)
    col = _m._mixrgb(nt, M('MAXIMUM', M('MAXIMUM', lat, petals), M('MAXIMUM', dots, scroll)), col, motif)
    b1, b2, b3 = bw
    col = _m._mixrgb(nt, M('MULTIPLY', M('GREATER_THAN', e, b1), M('LESS_THAN', e, b3)), col, border)
    col = _m._mixrgb(nt, M('MULTIPLY', M('GREATER_THAN', e, b2 - 0.005), M('LESS_THAN', e, b2)), col, edge)
    col = _m._mixrgb(nt, M('LESS_THAN', e, b1), col, edge)
    fine = _m._noise(nt, _m._coords(nt, scale=(300, 300, 300)), scale=1.0, detail=1.0)
    col = _m._mixrgb(nt, M('MULTIPLY', fine, 0.25), col, (0.75, 0.75, 0.75, 1), 'MULTIPLY')
    nt.links.new(b.inputs["Base Color"], col)
    _m._set(b, "Roughness", 0.95); _m._set(b, "Sheen Weight", 0.25); _m._set(b, "Specular IOR Level", 0.15)
    if b.inputs.get("Sheen Tint") is not None:
        nt.links.new(b.inputs["Sheen Tint"], col)
    _m._bump(nt, b, fine, 0.25, 0.003)
    return m


def plush_carpet(name, base=(0.596, 0.534, 0.494, 1), speck=0.42, scale=100.0):
    """Cut-pile wall-to-wall carpet (photos 04-06: light greige, a faint pink-grey cast): a visible tuft speckle in the
    ALBEDO (the photos' pile reads std ~9-14 sRGB levels at 2-3 m; a bump-only pile is wiped out by the denoiser), soft
    0.3 m mottling and faint vacuum tracks, a tuft bump, and a low sheen tinted like the pile (a white sheen made it read
    as snow). `base` is the mean albedo: the speckle is symmetric about it, mottle + tracks are compensated."""
    m, nt, b = _m._new(name)
    M = _M(nt)
    f = _m._noise(nt, _m._coords(nt, scale=(scale, scale, scale)), scale=1.0, detail=3.0, rough=0.6)
    sp = _m._stretch(nt, f, 0.30, 0.70)
    mo = _m._noise(nt, _m._coords(nt, scale=(2.0, 2.0, 2.0)), scale=1.0, detail=3.0)
    t = _m._noise(nt, _m._coords(nt, scale=(0.9, 5.0, 1)), scale=1.0, detail=2.0)
    lo = tuple(c * (1 - speck) for c in base[:3]) + (1,)
    hi = tuple(c * (1 + speck) for c in base[:3]) + (1,)
    col = _m._mixrgb(nt, sp, lo, hi)
    col = _m._mixrgb(nt, _m._stretch(nt, mo, 0.35, 0.65), col, (0.82, 0.82, 0.82, 1), 'MULTIPLY')
    col = _m._mixrgb(nt, M('MULTIPLY', _m._stretch(nt, t, 0.4, 0.6), 0.5), col, (1.08, 1.08, 1.08, 1), 'MULTIPLY')
    nt.links.new(b.inputs["Base Color"], col)
    _m._set(b, "Roughness", 1.0); _m._set(b, "Sheen Weight", 0.45); _m._set(b, "Sheen Roughness", 0.5); _m._set(b, "Specular IOR Level", 0.1)
    if b.inputs.get("Sheen Tint") is not None:
        nt.links.new(b.inputs["Sheen Tint"], col)
    _m._bump(nt, b, sp, 0.5, 0.004)
    return m


def garage_slab(name, joints_x=(3.1,), joints_y=(2.8,), base=(0.40, 0.40, 0.39, 1), hi=(0.50, 0.50, 0.49, 1)):
    """Smooth-trowelled garage slab (photo 24): mottled grey with darker oil / water stains, faint tyre tracks along Y
    and saw-cut control joints at the given x / y lines (object = world coordinates)."""
    m, nt, b = _m._new(name)
    M = _M(nt)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    px, py, _ = _sep(nt, tc.outputs["Object"])
    mot = _m._noise(nt, _m._coords(nt, scale=(1.2, 1.2, 1.2)), scale=1.0, detail=6.0, rough=0.6)
    fine = _m._noise(nt, _m._coords(nt, scale=(60, 60, 60)), scale=1.0, detail=3.0)
    stain = _m._stretch(nt, _m._noise(nt, _m._coords(nt, scale=(0.7, 0.7, 0.7), loc=(3.0, 1.0, 0.0)), scale=1.0, detail=4.0, distortion=0.8), 0.55, 0.72)
    trk = _m._noise(nt, _m._coords(nt, scale=(9.0, 0.4, 1.0)), scale=1.0, detail=2.0)
    col = _m._mixrgb(nt, M('MULTIPLY', _m._stretch(nt, mot, 0.35, 0.65), 0.25), base, hi)
    col = _m._mixrgb(nt, M('MULTIPLY', stain, 0.55), col, (0.24, 0.24, 0.235, 1))
    col = _m._mixrgb(nt, M('MULTIPLY', _m._stretch(nt, trk, 0.62, 0.72), 0.25), col, (0.30, 0.30, 0.29, 1))
    col = _m._mixrgb(nt, M('MULTIPLY', fine, 0.15), col, (0.8, 0.8, 0.8, 1), 'MULTIPLY')
    j = 0.0
    for x in joints_x:
        j = M('MAXIMUM', j, M('LESS_THAN', M('ABSOLUTE', M('SUBTRACT', px, x)), 0.004))
    for y in joints_y:
        j = M('MAXIMUM', j, M('LESS_THAN', M('ABSOLUTE', M('SUBTRACT', py, y)), 0.004))
    col = _m._mixrgb(nt, j, col, (0.12, 0.12, 0.12, 1))
    nt.links.new(b.inputs["Base Color"], col)
    nt.links.new(b.inputs["Roughness"], M('ADD', 0.55, M('MULTIPLY', stain, -0.2)))
    _m._bump(nt, b, M('SUBTRACT', M('MULTIPLY', fine, 0.2), M('MULTIPLY', j, 1.0)), 0.3, 0.004)
    return m


# ================================================================ metals, glass, porcelain
def hammered(name, base=(0.78, 0.78, 0.77, 1), rough=0.16, scale=70.0):
    m, nt, b = _m._new(name)
    _m._set(b, "Base Color", base); _m._set(b, "Metallic", 1.0); _m._set(b, "Roughness", rough)
    v = _m._voronoi(nt, _m._coords(nt, scale=(scale, scale, scale)), scale=1.0, feature='F1', rand=1.0)
    _m._bump(nt, b, v.outputs["Distance"], 0.45, 0.004)
    return m


def embossed(name, base=(0.62, 0.61, 0.58, 1), recess=(0.26, 0.25, 0.23, 1), rough=0.3, scale=55.0):
    """Repousse sheet metal (the Syrian octagonal tables, the mirror frame): a raised arabesque with dark recesses."""
    m, nt, b = _m._new(name)
    M = _M(nt)
    n = _m._noise(nt, _m._coords(nt, scale=(scale, scale, scale)), scale=1.0, detail=3.0, distortion=1.2)
    band = M('LESS_THAN', M('ABSOLUTE', M('SUBTRACT', n, 0.5)), 0.06)
    v = _m._voronoi(nt, _m._coords(nt, scale=(scale * 0.5,) * 3), scale=1.0, feature='F1', rand=0.3)
    dot = M('LESS_THAN', v.outputs["Distance"], 0.22)
    h = M('MAXIMUM', band, dot)
    col = _m._mixrgb(nt, M('SUBTRACT', 1.0, h), base, recess)
    nt.links.new(b.inputs["Base Color"], col)
    _m._set(b, "Metallic", 1.0)
    nt.links.new(b.inputs["Roughness"], M('ADD', rough, M('MULTIPLY', M('SUBTRACT', 1.0, h), 0.25)))
    _m._bump(nt, b, h, 0.5, 0.002)
    return m


def porcelain(name, white=(0.80, 0.80, 0.78, 1), blue=(0.025, 0.055, 0.26, 1), scale=11.0, bands=(0.10, 0.85)):
    """Blue-and-white Chinese export porcelain (the planters, photo 05): cobalt floral scroll + rim bands; bands are
    fractions of the object's height (Generated z)."""
    m, nt, b = _m._new(name)
    M = _M(nt)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    _, _, gz = _sep(nt, tc.outputs["Generated"])
    n = _m._noise(nt, _m._coords(nt, scale=(scale,) * 3), scale=1.0, detail=4.0, distortion=1.6)
    motif = M('GREATER_THAN', M('ABSOLUTE', M('SUBTRACT', n, 0.5)), 0.13)
    line = M('LESS_THAN', M('ABSOLUTE', M('SUBTRACT', n, 0.5)), 0.012)
    bd = M('ADD', M('LESS_THAN', M('ABSOLUTE', M('SUBTRACT', gz, bands[0])), 0.03), M('LESS_THAN', M('ABSOLUTE', M('SUBTRACT', gz, bands[1])), 0.035))
    k = M('MINIMUM', M('ADD', M('ADD', M('MULTIPLY', motif, 0.85), line), bd), 1.0)
    col = _m._mixrgb(nt, k, white, blue)
    nt.links.new(b.inputs["Base Color"], col)
    _m._set(b, "Roughness", 0.12); _m._set(b, "Coat Weight", 0.6); _m._set(b, "Specular IOR Level", 0.5)
    return m


# ================================================================ the palette
def mats(M):
    g = M.setdefault
    g('fs_sofa', chenille("FS_SofaSageChenille", (0.235, 0.26, 0.24, 1)))
    g('fs_floral', floral_print("FS_PillowFloral", plane='YZ'))
    sofa_stripes = [(0.0, (0.13, 0.075, 0.045, 1)), (0.10, (0.30, 0.21, 0.13, 1)), (0.16, (0.18, 0.08, 0.04, 1)), (0.22, (0.36, 0.30, 0.22, 1)),
                    (0.30, (0.10, 0.06, 0.04, 1)), (0.38, (0.20, 0.21, 0.22, 1)), (0.46, (0.30, 0.22, 0.14, 1)), (0.56, (0.14, 0.08, 0.05, 1)),
                    (0.64, (0.38, 0.32, 0.24, 1)), (0.74, (0.22, 0.11, 0.05, 1)), (0.82, (0.28, 0.24, 0.19, 1)), (0.90, (0.12, 0.07, 0.045, 1))]
    g('fs_stripe_sofa', stripe_print("FS_PillowStripeBrown", sofa_stripes, period=0.10, axis='Y'))
    # pillow OBJECTS (built flat in their own XY plane and then rotated) take the print in object space
    g('fs_stripe_sofa_obj', stripe_print("FS_PillowStripeBrownObj", sofa_stripes, period=0.10, axis='X'))
    g('fs_floral_obj', floral_print("FS_PillowFloralObj", plane='XY', scale=4.3))
    g('fs_stripe_chair', stripe_print("FS_PillowStripeBlue", [(0.0, (0.62, 0.58, 0.48, 1)), (0.16, (0.32, 0.40, 0.46, 1)), (0.30, (0.66, 0.64, 0.58, 1)),
                                                               (0.38, (0.40, 0.31, 0.21, 1)), (0.50, (0.70, 0.66, 0.56, 1)), (0.66, (0.46, 0.55, 0.60, 1)),
                                                               (0.80, (0.58, 0.52, 0.40, 1)), (0.90, (0.26, 0.20, 0.14, 1))], period=0.16, axis='Z'))
    g('fs_leaf', leaf_print("FS_SlipperLeaf"))
    g('fs_cherry', _m.wood("FS_CherryDark", light=(0.068, 0.024, 0.017, 1), dark=(0.033, 0.011, 0.008, 1), grain_axis='X', rough=0.25, coat=0.6))
    g('fs_cherry_v', _m.wood("FS_CherryDarkV", light=(0.068, 0.024, 0.017, 1), dark=(0.033, 0.011, 0.008, 1), grain_axis='Z', rough=0.25, coat=0.6))
    g('fs_espresso', _m.wood("FS_EspressoLeg", light=(0.045, 0.030, 0.022, 1), dark=(0.020, 0.013, 0.010, 1), grain_axis='Z', rough=0.35, coat=0.3))
    g('fs_mahogany', _m.wood("FS_Mahogany", light=(0.095, 0.036, 0.022, 1), dark=(0.045, 0.016, 0.010, 1), grain_axis='X', rough=0.3, coat=0.5))
    g('fs_glass', _m.new_mat("FS_TableGlass", (0.86, 0.95, 0.93, 1), rough=0.0, transmission=1.0, ior=1.5, spec=0.5))
    g('fs_hammered', hammered("FS_HammeredSilver"))
    g('fs_embossed', embossed("FS_EmbossedSilver"))
    g('fs_embossed_top', embossed("FS_EmbossedSilverDark", base=(0.40, 0.40, 0.39, 1), recess=(0.10, 0.10, 0.10, 1)))
    g('fs_brass', _m.new_mat("FS_AntiqueBrass", (0.56, 0.42, 0.22, 1), rough=0.33, metal=1.0))
    g('fs_bronze', _m.new_mat("FS_OilBronze", (0.16, 0.10, 0.06, 1), rough=0.42, metal=0.85))
    g('fs_gold', _m.new_mat("FS_BronzeGold", (0.45, 0.33, 0.16, 1), rough=0.38, metal=1.0))
    g('fs_copper', _m.new_mat("FS_CopperBand", (0.50, 0.27, 0.15, 1), rough=0.35, metal=1.0))
    g('fs_nickel', _m.new_mat("FS_BrushedNickel", (0.66, 0.65, 0.62, 1), rough=0.3, metal=1.0))
    g('fs_pewter', _m.new_mat("FS_PewterRod", (0.52, 0.52, 0.50, 1), rough=0.3, metal=1.0))
    g('fs_smoke_glass', _m.new_mat("FS_BronzeShelfGlass", (0.055, 0.035, 0.022, 1), rough=0.12, spec=0.6, coat=0.6))
    g('fs_shade', _m.new_mat("FS_ShadeTan", (0.62, 0.45, 0.26, 1), rough=0.85, transmission=0.25, sheen=0.4))
    g('fs_swag', sheer("FS_SwagTaupe", ground=(0.76, 0.65, 0.52, 1), alpha=0.55, thread=(0.38, 0.30, 0.20, 1), motif='wheat', period=(0.16, 0.22)))
    g('fs_tail', _m.fabric("FS_JabotTaupe", (0.52, 0.42, 0.33, 1), rough=0.8, sheen=0.9, weave=140, bump=0.1))
    g('fs_sheer', sheer("FS_SheerEmbroidered", ground=(0.88, 0.86, 0.80, 1), alpha=0.50, thread=(0.22, 0.20, 0.17, 1), motif='sprig'))
    g('fs_rug', patterned_rug("FS_RugFoyerGrey"))
    g('fs_carpet', plush_carpet("FS_CarpetGreige"))
    g('fs_porcelain', porcelain("FS_BlueWhitePorcelain"))
    g('fs_cobalt', _m.new_mat("FS_CobaltGlass", (0.04, 0.10, 0.45, 1), rough=0.08, transmission=0.85, ior=1.5, spec=0.6))
    g('fs_ebony', _m.wood("FS_EbonyStand", light=(0.035, 0.025, 0.02, 1), dark=(0.012, 0.010, 0.008, 1), grain_axis='Z', rough=0.4, coat=0.3))
    g('fs_twig', _m.noise_mat("FS_DriedTwig", (0.38, 0.31, 0.22, 1), (0.62, 0.55, 0.44, 1), scale=60, bump=0.3, rough=0.8))
    g('fs_frame_walnut', _m.wood("FS_FrameWalnut", light=(0.10, 0.055, 0.03, 1), dark=(0.05, 0.028, 0.016, 1), grain_axis='X', rough=0.35, coat=0.4))
    g('fs_frame_silver', embossed("FS_FrameSilverOrnate", base=(0.44, 0.44, 0.42, 1), recess=(0.07, 0.07, 0.065, 1), scale=60.0))   # 06
    g('fs_frame_bronze', _m.new_mat("FS_FrameBronzeGilt", (0.17, 0.105, 0.05, 1), rough=0.3, metal=0.85))   # 05: dark bronze
    g('fs_plastic_white', _m.new_mat("FS_PlasticWhite", (0.80, 0.80, 0.77, 1), rough=0.35, spec=0.5))
    g('fs_register', _m.new_mat("FS_RegisterWhite", (0.78, 0.78, 0.76, 1), rough=0.3, metal=0.3))
    g('fs_slot', _m.new_mat("FS_DuctDark", (0.02, 0.02, 0.02, 1), rough=0.8))
    g('fs_garage_slab', garage_slab("FS_GarageSlab", joints_x=(3.2,), base=(0.47, 0.455, 0.43, 1), hi=(0.56, 0.54, 0.51, 1)))   # 24: warm grey, x-joint 3.2
    # the powder vanity's honey maple (photo 07 door panel (123, 73, 34): browner, less saturated than the kitchen's)
    g('fs_vanity_maple', _m.wood("FS_VanityMaple", light=(0.34, 0.14, 0.042, 1), dark=(0.235, 0.093, 0.027, 1), grain_axis='Z', rough=0.38, coat=0.3))
    g('fs_vanity_maple_h', _m.wood("FS_VanityMapleH", light=(0.34, 0.14, 0.042, 1), dark=(0.235, 0.093, 0.027, 1), grain_axis='X', rough=0.38, coat=0.3))
    return M


# ================================================================ geometry helpers
def _rrect(cx, cy, wx, wy, r, n=3):
    """Rounded-rectangle outline (CCW) centred at (cx, cy)."""
    r = max(1e-4, min(r, wx / 2 - 1e-4, wy / 2 - 1e-4))
    pts = []
    for (qx, qy, a0) in ((wx / 2 - r, -wy / 2 + r, -math.pi / 2), (wx / 2 - r, wy / 2 - r, 0.0), (-wx / 2 + r, wy / 2 - r, math.pi / 2),
                         (-wx / 2 + r, -wy / 2 + r, math.pi)):
        for k in range(n + 1):
            a = a0 + math.pi / 2 * k / n
            pts.append((cx + qx + r * math.cos(a), cy + qy + r * math.sin(a)))
    return pts


def soft_loft(mb, frame, specs, r, mi=0, n=3, cap=True):
    """Loft rounded-rectangle sections: specs = [(z, cx, cy, wx, wy), ...] in a local frame (x across, y depth, z up);
    frame(lx, ly, lz) -> world point.  The top / bottom are closed with filleted rings so the piece reads as upholstery."""
    secs = []
    if cap:
        z, cx, cy, wx, wy = specs[0]
        for k, s in ((0.45, 0.0), (0.8, r * 0.45)):
            secs.append([frame(px, py, z - r * 0.35 + s) for (px, py) in _rrect(cx, cy, max(0.02, wx - 2 * r * (1 - k)), max(0.02, wy - 2 * r * (1 - k)), r * k, n)])
    for (z, cx, cy, wx, wy) in specs:
        secs.append([frame(px, py, z) for (px, py) in _rrect(cx, cy, wx, wy, r, n)])
    if cap:
        z, cx, cy, wx, wy = specs[-1]
        for k, s in ((0.8, r * 0.45), (0.45, r * 0.8), (0.12, r * 0.95)):
            secs.append([frame(px, py, z + s) for (px, py) in _rrect(cx, cy, max(0.02, wx - 2 * r * (1 - k)), max(0.02, wy - 2 * r * (1 - k)), r * k, n)])
    mb.sweep(secs, mi)


def local_frame(x, y, rot, z0=0.0):
    """Local furniture frame: local -y is the piece's front, rotated by `rot` about Z and placed at (x, y)."""
    c, s = math.cos(rot), math.sin(rot)
    return lambda lx, ly, lz: (x + lx * c - ly * s, y + lx * s + ly * c, z0 + lz)


def tapered_leg(mb, top, bot, w0, w1, mi=0, rot=0.0):
    """Square tapered leg from top (x, y, z) to bot (x, y, z): w0 at the top, w1 at the foot."""
    (x0, y0, z0), (x1, y1, z1) = top, bot
    c, s = math.cos(rot), math.sin(rot)
    def ring(x, y, z, w):
        h = w / 2
        return [(x + dx * c - dy * s, y + dx * s + dy * c, z) for (dx, dy) in ((-h, -h), (h, -h), (h, h), (-h, h))]
    mb.hexa(ring(x1, y1, z1, w1) + ring(x0, y0, z0, w0), mi)


# ================================================================ upholstery
def flare_sofa(mb, x, y, rot, w=2.12, d=0.93, mi_body=0, mi_leg=1, seat_h=0.49, back_h=0.86, arm_h=0.69):
    """Transitional sofa (photos 04-06): tall flared track arms, a tight back, two plump bench-seat cushions, dark
    tapered legs that splay slightly outward.  Faces its local -y."""
    F = local_frame(x, y, rot)
    aw = 0.17                                    # arm width at the base (flares to ~0.26 at the top)
    xi = w / 2 - aw                              # inner face of the arm at the base
    # deck / seat platform (photo 06: the upholstered base shows below the cushions, flush with the arm fronts)
    fy0, by0 = -d / 2 + 0.01, d / 2 - 0.12
    soft_loft(mb, F, [(0.14, 0.0, (fy0 + by0) / 2, 2 * xi + 0.02, by0 - fy0), (seat_h - 0.17, 0.0, (fy0 + by0) / 2, 2 * xi + 0.02, by0 - fy0)], 0.035, mi_body)
    # back: a tight upholstered back leaning 8 degrees, its top rolled
    lean = math.tan(math.radians(8))
    specs = []
    for k in range(6):
        z = seat_h - 0.16 + (back_h - seat_h + 0.12) * k / 5
        specs.append((z, 0.0, d / 2 - 0.12 + (z - seat_h) * lean, 2 * xi + 0.04, 0.20 - 0.05 * k / 5))
    soft_loft(mb, F, specs, 0.05, mi_body)
    # two thick bench cushions, their fronts flush with the arms (photo 06)
    sw = xi
    cf, cb = -d / 2 + 0.005, d / 2 - 0.22
    for s in (-1, 1):
        cx = s * sw / 2
        soft_loft(mb, F, [(seat_h - 0.17, cx, (cf + cb) / 2, sw - 0.012, cb - cf), (seat_h - 0.02, cx, (cf + cb) / 2 - 0.004, sw - 0.012, cb - cf)], 0.06, mi_body)
    # flared arms: the outer face leans out, the arm top slopes down ~3 cm toward the front
    for s in (-1, 1):
        specs = []
        for k in range(7):
            t = k / 6
            z = 0.14 + (arm_h - 0.14) * t
            fl = 0.15 * t ** 1.8
            wx = aw + fl
            cx = s * (w / 2 - aw / 2 + fl / 2)
            specs.append((z, cx, 0.0, wx, d - 0.01 + 0.02 * t))
        soft_loft(mb, F, specs, 0.07, mi_body)
    # legs: front legs splay forward/outward, rear legs back
    for sx in (-1, 1):
        for sy in (-1, 1):
            tx, ty = sx * (w / 2 - 0.10), sy * (d / 2 - 0.10)
            bx, by = tx + sx * 0.02, ty + sy * 0.03
            p0, p1 = F(tx, ty, 0.15), F(bx, by, 0.0)
            tapered_leg(mb, p0, p1, 0.05, 0.03, mi_leg, rot)


def slipper_chair(mb, x, y, rot, mi_up=0, mi_leg=1, w=0.60, d=0.66, seat_h=0.47, back_h=0.92):
    """Armless slipper chair (photos 04, 06): upholstered base + a thick box cushion, a tall back leaning ~10 deg,
    square tapered espresso legs, the rear pair raked back."""
    F = local_frame(x, y, rot)
    soft_loft(mb, F, [(0.30, 0.0, 0.0, w, d), (seat_h - 0.11, 0.0, 0.0, w, d)], 0.03, mi_up, cap=True)
    soft_loft(mb, F, [(seat_h - 0.11, 0.0, -0.02, w - 0.005, d - 0.06), (seat_h, 0.0, -0.02, w - 0.005, d - 0.06)], 0.045, mi_up)
    lean = math.tan(math.radians(10))
    specs = []
    for k in range(6):
        z = seat_h - 0.10 + (back_h - seat_h + 0.10) * k / 5
        specs.append((z, 0.0, d / 2 - 0.05 + (z - seat_h) * lean, w, 0.11 - 0.02 * k / 5))
    soft_loft(mb, F, specs, 0.04, mi_up)
    for sx in (-1, 1):
        tapered_leg(mb, F(sx * (w / 2 - 0.05), -d / 2 + 0.06, 0.31), F(sx * (w / 2 - 0.05), -d / 2 + 0.07, 0.0), 0.042, 0.03, mi_leg, rot)
        tapered_leg(mb, F(sx * (w / 2 - 0.05), d / 2 - 0.06, 0.31), F(sx * (w / 2 - 0.05), d / 2 + 0.05, 0.0), 0.042, 0.03, mi_leg, rot)


def pillow(mb, x, y, z, size, rot, pitch=1.25, t=0.16, mi=0, seed=0, h=None):
    mb.pillow_sq(x, y, z, size, size if h is None else h, t, mi, rot=rot, pitch=pitch, seed=seed)


def pillow_obj(name, mats, loc, w, h, t, yaw, pitch, spin=0.0, seed=0, coll='House'):
    """A throw pillow as its own object: built flat (width along x, height along y), spun in its own plane by `spin`,
    stood up by `pitch` (about x; ~1.2 = leaning back) and turned by `yaw` (its front then faces the yaw direction's -y).
    Lets a pillow roll in its plane (corners up), which pillow_sq's rot/pitch cannot do."""
    from mathutils import Matrix
    mb = MB()
    mb.pillow_sq(0.0, 0.0, 0.0, w, h, t, 0, rot=0.0, pitch=0.0, seed=seed)
    ob = mb.build(name, mats, coll=coll, smooth=True)
    ob.matrix_world = Matrix.Translation(loc) @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Rotation(pitch, 4, 'X') @ Matrix.Rotation(spin, 4, 'Z')
    return ob


# ================================================================ tables
def _ellipse(cx, cy, a, b, rot, n):
    c, s = math.cos(rot), math.sin(rot)
    return [(cx + a * math.cos(TAU * i / n) * c - b * math.sin(TAU * i / n) * s, cy + a * math.cos(TAU * i / n) * s + b * math.sin(TAU * i / n) * c)
            for i in range(n)]


def oval_cocktail_table(mb, x, y, rot, a=0.62, b=0.34, h=0.47, mi_wood=0, mi_glass=1, mi_foot=2, seg=48):
    """Oval glass-top cocktail table (photos 04-06): a moulded cherry rim around an inset glass, a narrow apron,
    four S-curved legs with reeded knee blocks near the ends, an oval under-shelf, dark metal feet."""
    from archviz.trees import _sections
    from mathutils import Vector
    c, s = math.cos(rot), math.sin(rot)
    def P(t, off, z):                            # point at parameter t on the ellipse, offset `off` m along its normal
        ex, ey = a * math.cos(t), b * math.sin(t)
        nx, ny = b * math.cos(t), a * math.sin(t)
        L = math.hypot(nx, ny)
        ex, ey = ex + off * nx / L, ey + off * ny / L
        return (x + ex * c - ey * s, y + ex * s + ey * c, z)
    # rim: a closed sweep of a moulded bullnose profile (offset from the ellipse, z); the glass sits in a rabbet
    rt = 0.058                                   # rim depth (photos 04-06: a heavy moulded cherry band)
    prof = [(0.0, h - rt), (0.010, h - rt * 0.72), (0.014, h - rt * 0.38), (0.008, h - 0.004), (-0.006, h), (-0.052, h), (-0.056, h - 0.010),
            (-0.052, h - 0.016), (-0.020, h - 0.018), (-0.016, h - rt)]
    secs = [[P(TAU * i / seg, o, z) for (o, z) in prof] for i in range(seg)]
    mb.sweep(secs, mi_wood, close=True, caps=False)
    # apron ring below the rim
    for i in range(seg):
        t0, t1 = TAU * i / seg, TAU * (i + 1) / seg
        mb.hexa([P(t0, -0.012, h - 0.085), P(t1, -0.012, h - 0.085), P(t1, -0.032, h - 0.085), P(t0, -0.032, h - 0.085),
                 P(t0, -0.012, h - 0.042), P(t1, -0.012, h - 0.042), P(t1, -0.032, h - 0.042), P(t0, -0.032, h - 0.042)], mi_wood)
    # glass: an elliptic plate resting in the rabbet
    ring_b = [P(TAU * i / seg, -0.050, h - 0.024) for i in range(seg)]
    ring_t = [P(TAU * i / seg, -0.050, h - 0.015) for i in range(seg)]
    mb.sweep([ring_b, ring_t], mi_glass, caps=True)
    # S-curved legs near the ends (param angles): a knee that bows out under the rim, the foot kicked outward
    for t in (0.62, math.pi - 0.62, math.pi + 0.62, TAU - 0.62):
        pts, rad = [], []
        for k in range(10):
            u = k / 9
            off = -0.035 + 0.030 * math.sin(math.pi * min(1.0, u * 1.6)) * (1 - u) + 0.075 * u ** 2.2
            z = (h - 0.085) * (1 - u) + 0.028 * u
            pts.append(Vector(P(t, off, z)))
            rad.append(0.031 - 0.013 * u + 0.006 * math.sin(math.pi * u))
        mb.sweep(_sections(pts, rad, 10), mi_wood)
        kx, ky, _ = P(t, -0.035, 0.0)
        mb.cylinder(kx, ky, h - 0.135, h - 0.05, 0.036, 0.033, seg=12, mi=mi_wood)          # reeded knee block
        fx, fy, _ = pts[-1]
        mb.cylinder(fx, fy, 0.0, 0.03, 0.021, 0.017, seg=10, mi=mi_foot)
    # under-shelf with a thick edge, carried on the legs
    sh = [P(TAU * i / seg, -0.12, 0.195) for i in range(seg)]
    shb = [P(TAU * i / seg, -0.12, 0.170) for i in range(seg)]
    mb.sweep([shb, sh], mi_wood, caps=True)


def octagon_table(mb, x, y, r=0.20, h=0.50, mi=0, mi_top=None, rot=math.pi / 8):
    """Syrian repousse octagonal side table (photos 04-06): an octagonal top with a lip, an apron with a pointed
    arch cut into each face, slim corner legs, a lower shelf."""
    mi_top = mi if mi_top is None else mi_top
    mb.cylinder(x, y, h - 0.03, h, r + 0.012, seg=8, mi=mi_top, rot=rot)
    mb.cylinder(x, y, h - 0.05, h - 0.03, r - 0.005, seg=8, mi=mi, rot=rot)
    corners = [(x + r * math.cos(rot + TAU * i / 8), y + r * math.sin(rot + TAU * i / 8)) for i in range(8)]
    for i in range(8):
        (ax, ay), (bx, by) = corners[i], corners[(i + 1) % 8]
        nx, ny = (ax + bx) / 2 - x, (ay + by) / 2 - y
        L = math.hypot(nx, ny); nx, ny = nx / L, ny / L
        # apron with a pointed arch: 6 vertical slices whose bottoms follow the arch
        for k in range(6):
            u0, u1 = k / 6, (k + 1) / 6
            um = (u0 + u1) / 2
            zb = h - 0.05 - 0.17 * (1 - abs(2 * um - 1) ** 0.6) - 0.02
            p0 = (ax + (bx - ax) * u0, ay + (by - ay) * u0); p1 = (ax + (bx - ax) * u1, ay + (by - ay) * u1)
            q = lambda p, d: (p[0] - nx * d, p[1] - ny * d)
            a0_, a1_, b0_, b1_ = p0, p1, q(p1, 0.012), q(p0, 0.012)
            mb.hexa([(*a0_, zb), (*a1_, zb), (*b0_, zb), (*b1_, zb), (*a0_, h - 0.05), (*a1_, h - 0.05), (*b0_, h - 0.05), (*b1_, h - 0.05)], mi)
        # corner leg (a narrow bent slab at each corner)
        cx, cy = corners[i]
        mb.cylinder(cx - 0.012 * math.cos(rot + TAU * i / 8), cy - 0.012 * math.sin(rot + TAU * i / 8), 0.0, h - 0.05, 0.018, seg=6, mi=mi)
    mb.cylinder(x, y, 0.07, 0.09, r - 0.02, seg=8, mi=mi, rot=rot)


def hammered_vase(mb, x, y, z, r=0.17, h=0.30, mi=0):
    """Round hammered-silver vase (photo 04): a squat globe with a short neck and a flared lip."""
    prof = [(0, 0), (r * 0.45, 0.0), (r * 0.80, h * 0.08), (r * 0.98, h * 0.30), (r, h * 0.45), (r * 0.92, h * 0.62), (r * 0.62, h * 0.80),
            (r * 0.25, h * 0.88), (r * 0.22, h * 0.95), (r * 0.32, h), (r * 0.28, h), (r * 0.18, h * 0.93), (0, h * 0.93)]
    mb.lathe(x, y, z, prof, seg=36, mi=mi)


def urn_vase(mb, x, y, z, r=0.13, h=0.36, mi=0):
    prof = [(0, 0), (r * 0.55, 0), (r * 0.6, 0.03), (r * 0.95, h * 0.35), (r, h * 0.5), (r * 0.7, h * 0.75), (r * 0.45, h * 0.86),
            (r * 0.55, h), (r * 0.48, h), (r * 0.36, h * 0.9), (0, h * 0.9)]
    mb.lathe(x, y, z, prof, seg=28, mi=mi)


def bar_cart(mb, x, y, rot, a=0.40, b=0.20, mi_metal=0, mi_shelf=1, mi_wheel=2, tiers=(0.29, 0.78)):
    """Oval two-tier brass bar cart (photos 05, 06): bronze-glass shelves in brass trays with a gallery rail, four
    tube legs on casters."""
    c, s = math.cos(rot), math.sin(rot)
    def P(t, k, z):
        ex, ey = a * k * math.cos(t), b * k * math.sin(t)
        return (x + ex * c - ey * s, y + ex * s + ey * c, z)
    n = 40
    for zt in tiers:
        mb.sweep([[P(TAU * i / n, 0.97, zt) for i in range(n)], [P(TAU * i / n, 0.97, zt + 0.012) for i in range(n)]], mi_shelf, caps=True)
        mb.sweep([[P(TAU * i / n, 1.0, zt - 0.02) for i in range(n)], [P(TAU * i / n, 1.0, zt + 0.03) for i in range(n)],
                  [P(TAU * i / n, 0.985, zt + 0.03) for i in range(n)], [P(TAU * i / n, 0.985, zt - 0.02) for i in range(n)]], mi_metal, close=True, caps=False)
        ring = [__import__('mathutils').Vector(P(TAU * i / n, 1.0, zt + 0.085)) for i in range(n + 1)]
        mb.path_tube(ring, 0.0055, seg=6, mi=mi_metal)
        for i in range(0, n, 4):
            p0, p1 = P(TAU * i / n, 1.0, zt + 0.03), P(TAU * i / n, 1.0, zt + 0.085)
            mb.tube(p0, p1, 0.004, 0.004, seg=5, mi=mi_metal)
    for t in (0.42, math.pi - 0.42, math.pi + 0.42, TAU - 0.42):
        bx, by, _ = P(t, 1.0, 0.0)
        mb.cylinder(bx, by, 0.075, tiers[1] + 0.09, 0.0095, seg=10, mi=mi_metal)
        mb.sphere((bx, by, tiers[1] + 0.095), 0.013, seg=10, rings=6, mi=mi_metal)
        mb.cylinder(bx, by, 0.05, 0.075, 0.012, seg=8, mi=mi_metal)
        mb.cylinder(bx, by, 0.03, 0.05, 0.016, seg=10, mi=mi_metal)
        # caster wheel
        mb.tube((bx - 0.012 * c, by - 0.012 * s, 0.024), (bx + 0.012 * c, by + 0.012 * s, 0.024), 0.024, 0.024, seg=12, mi=mi_wheel)


def candlestick_lamp(mb_base, mb_shade, x, y, z, h=0.66, shade_w=(0.40, 0.24), shade_h=0.28, mi_base=0, mi_shade=0, rot=0.0):
    """Oil-rubbed-bronze candlestick lamp with a tapered square bell shade and a finial (photos 05, 06)."""
    prof = [(0, 0), (0.085, 0.0), (0.085, 0.015), (0.07, 0.025), (0.045, 0.05), (0.03, 0.09), (0.022, 0.13), (0.028, 0.16), (0.018, 0.20),
            (0.016, 0.34), (0.026, 0.37), (0.02, 0.40), (0.014, 0.42), (0.012, h - shade_h + 0.02), (0.02, h - shade_h + 0.05), (0.008, h - shade_h + 0.07),
            (0.005, h + 0.02), (0, h + 0.02)]
    mb_base.lathe(x, y, z, prof, seg=18, mi=mi_base)
    mb_base.lathe(x, y, z + h + 0.02, [(0, 0), (0.012, 0.0), (0.018, 0.02), (0.01, 0.045), (0, 0.05)], seg=12, mi=mi_base)
    wb, wt = shade_w
    c, s = math.cos(rot), math.sin(rot)
    secs_o, secs_i = [], []
    for k in range(7):
        u = k / 6
        wv = wb + (wt - wb) * (u ** 0.8) + 0.02 * math.sin(math.pi * u)
        zz = z + h - shade_h + shade_h * u
        pts = []
        for (px, py) in _rrect(0.0, 0.0, wv, wv, wv * 0.18, 2):
            pts.append((x + px * c - py * s, y + px * s + py * c, zz))
        secs_o.append(pts)
        secs_i.append([(x + (px - x) * 0.97, y + (py - y) * 0.97, pz) for (px, py, pz) in pts])
    mb_shade.sweep(secs_o + list(reversed(secs_i)), mi_shade, close=True, caps=False)


def demilune(mb, x_wall, y, r=0.42, h=0.78, side=+1, mi=0):
    """Mahogany demilune console against a wall at x = x_wall (room toward +x*side): half-round top with a
    bullnose, an apron, four turned legs, a half-moon lower shelf."""
    def arc(rr, z0, z1):
        pts = [(x_wall + side * rr * math.cos(t), y + rr * math.sin(t)) for t in (-math.pi / 2 + math.pi * i / 24 for i in range(25))]
        if side < 0:
            pts.reverse()
        mb.prism(pts, z0, z1, mi)          # the chord closes the half-disc along the wall
    arc(r, h - 0.03, h)
    arc(r - 0.03, h - 0.10, h - 0.03)
    arc(r - 0.04, 0.10, 0.125)
    for t in (-1.35, -0.45, 0.45, 1.35):
        lx, ly = x_wall + side * (r - 0.06) * math.cos(t), y + (r - 0.06) * math.sin(t)
        mb.lathe(lx, ly, 0.0, [(0, 0), (0.016, 0), (0.02, 0.03), (0.014, 0.06), (0.016, 0.20), (0.022, 0.30), (0.016, 0.38), (0.017, 0.55),
                               (0.022, 0.60), (0.024, h - 0.12), (0.022, h - 0.10), (0, h - 0.10)], seg=12, mi=mi)


def plant_stand(mb, x, y, r=0.17, h=0.14, mi=0):
    """Low carved blackwood stand under the peace lily's porcelain pot (photo 05)."""
    mb.cylinder(x, y, h - 0.03, h, r, seg=8, mi=mi, rot=math.pi / 8)
    mb.cylinder(x, y, h - 0.06, h - 0.03, r - 0.02, seg=8, mi=mi, rot=math.pi / 8)
    for i in range(4):
        t = math.pi / 4 + i * math.pi / 2
        lx, ly = x + (r - 0.03) * math.cos(t), y + (r - 0.03) * math.sin(t)
        mb.path_tube([(lx, ly, h - 0.05), (lx + 0.012 * math.cos(t), ly + 0.012 * math.sin(t), h * 0.4), (lx + 0.02 * math.cos(t), ly + 0.02 * math.sin(t), 0.0)], 0.012, seg=6, mi=mi)


def planter(mb, x, y, z, r=0.17, h=0.25, mi=0, mi_soil=1):
    """Chinese porcelain planter with a rolled rim; returns the soil height."""
    mb.lathe(x, y, z, [(0, 0), (r * 0.66, 0.0), (r * 0.70, 0.02), (r * 0.93, h * 0.45), (r, h * 0.78), (r * 0.98, h * 0.92), (r * 1.04, h * 0.95),
                       (r * 1.04, h), (r * 0.92, h), (r * 0.90, h - 0.04), (0, h - 0.04)], seg=32, mi=mi)
    mb.lathe(x, y, z + h - 0.06, [(0, 0), (r * 0.9, 0.0), (r * 0.88, 0.012), (0, 0.02)], seg=20, mi=mi_soil)
    return z + h - 0.045


# ================================================================ plants (archviz.plants machinery, custom species)
def _leaf_mats():
    from archviz import plants as _pl
    MM = _pl.mats()
    if 'fs_lily' not in MM:
        S = _pl.leaf_shader
        MM['fs_lily'] = S("FS_LeafPeaceLily", 'elliptic', (0.020, 0.075, 0.022, 1), (0.035, 0.11, 0.035, 1), (0.06, 0.16, 0.05, 1),
                          under=(0.10, 0.20, 0.08, 1), translucent=0.2, rough=0.22, coat=0.5, p=1.05, q=0.95, veins=9, vein_k=0.55, rib=0.014,
                          rib_col=(0.16, 0.30, 0.10, 1))
        MM['fs_dracaena'] = S("FS_LeafDracaena", 'lanceolate', (0.025, 0.10, 0.03, 1), (0.05, 0.16, 0.05, 1), (0.10, 0.24, 0.07, 1),
                              under=(0.12, 0.24, 0.10, 1), translucent=0.3, rough=0.35, coat=0.3, p=0.9, q=1.15, rib=0.05, rib_col=(0.30, 0.40, 0.12, 1))
        MM['fs_aloe'] = S("FS_LeafAloe", 'lanceolate', (0.10, 0.22, 0.07, 1), (0.16, 0.30, 0.10, 1), (0.22, 0.38, 0.14, 1), translucent=0.2,
                          rough=0.4, coat=0.2, p=0.8, q=1.4, rib=0.0)
    return MM


def peace_lily(name, x, y, z, h=0.62, seed=5, coll='House', mat_stem=None):
    """Spathiphyllum (photo 05): ~26 glossy dark elliptic leaves on long petioles that arch outward from the soil into
    a rounded mound, the outer leaves drooping over the rim."""
    from archviz import plants as _pl
    from mathutils import Vector
    _leaf_mats()
    F = _pl.Foliage(seed)
    rng = F.rng
    n = 26
    for i in range(n):
        az = TAU * i / n + rng.uniform(-0.3, 0.3)
        out = Vector((math.cos(az), math.sin(az), 0))
        inner = (i % 3 == 0)
        el = rng.uniform(1.15, 1.40) if inner else rng.uniform(0.62, 1.05)
        d = (out * math.cos(el) + Vector((0, 0, 1)) * math.sin(el)).normalized()
        Lp = h * (rng.uniform(0.45, 0.62) if inner else rng.uniform(0.30, 0.48))
        pts, dend = F.arc((x + out.x * 0.025, y + out.y * 0.025, z), d, Lp, 0.0045, 0.003, n=4, gravity=0.30 if not inner else 0.12, wiggle=0.03)
        L = h * rng.uniform(0.36, 0.48)
        side = out.cross(Vector((0, 0, 1))).normalized()
        F.leaf('fs_lily', pts[-1], dend, side, L, L * rng.uniform(0.34, 0.42), n=7,
               droop=rng.uniform(0.5, 0.9) if inner else rng.uniform(0.9, 1.5), twist=rng.uniform(-0.35, 0.35))
    return F.build(name, [mat_stem or _pl.mats()['stem']] * 3, coll=coll)


def dracaena(name, x, y, z, h=1.55, seed=7, coll='House', canes=(0.40, 0.70, 1.00)):
    """Dracaena 'Janet Craig' on staggered canes (the hall end, photo 05): each cane carries a long leafy crown - dark
    glossy strap leaves spiralling up its top ~0.6 m, the lower ones arching out and down, the young ones upright."""
    from archviz import plants as _pl
    from mathutils import Vector
    _leaf_mats()
    F = _pl.Foliage(seed)
    rng = F.rng
    for ci, ch in enumerate(canes):
        cx, cy = x + rng.uniform(-0.05, 0.05), y + rng.uniform(-0.05, 0.05)
        top = Vector((cx + rng.uniform(-0.05, 0.05), cy + rng.uniform(-0.05, 0.05), z + ch))
        F.wood.tube((cx, cy, z - 0.02), tuple(top), 0.016, 0.013, seg=8, mi=2)
        crown = 0.55 + 0.1 * ci
        F.wood.tube(tuple(top), tuple(top + Vector((0, 0, crown - 0.08))), 0.012, 0.008, seg=6, mi=2)       # the leafy stem
        nl = 30
        for i in range(nl):
            t = i / (nl - 1)
            az = i * math.radians(137.5) + rng.uniform(-0.2, 0.2)
            out = Vector((math.cos(az), math.sin(az), 0))
            el = 0.05 + 1.0 * t ** 1.3 + rng.uniform(-0.1, 0.1)
            d = (out * math.cos(el) + Vector((0, 0, 1)) * math.sin(el)).normalized()
            base = top + Vector((0, 0, crown * t - 0.05))
            L = rng.uniform(0.42, 0.62) * (h / 1.5) * (1.0 - 0.3 * t)
            side = out.cross(Vector((0, 0, 1))).normalized()
            F.leaf('fs_dracaena', tuple(base), d, side, L, rng.uniform(0.045, 0.065), n=5, droop=rng.uniform(0.7, 1.4) * (1.0 - 0.6 * t),
                   twist=rng.uniform(-0.4, 0.4))
    return F.build(name, [_pl.mats()['cane']] * 3, coll=coll)


def aloe(name, x, y, z, h=0.22, seed=9, coll='House'):
    from archviz import plants as _pl
    from mathutils import Vector
    _leaf_mats()
    F = _pl.Foliage(seed)
    rng = F.rng
    for i in range(14):
        az = rng.uniform(0, TAU)
        out = Vector((math.cos(az), math.sin(az), 0))
        el = rng.uniform(0.8, 1.35)
        d = (out * math.cos(el) + Vector((0, 0, 1)) * math.sin(el)).normalized()
        F.leaf('fs_aloe', (x, y, z), d, out.cross(Vector((0, 0, 1))).normalized(), h * rng.uniform(0.7, 1.0), 0.022, n=3, droop=rng.uniform(0.1, 0.5))
    return F.build(name, [_pl.mats()['stem']] * 3, coll=coll)


# ================================================================ window dressing
def swag_valance(mb, x0, x1, y, ztop, drop, depth=0.11, mi=0, mi_lace=None, folds=5, n=36, m=24, lace=0.04, side=+1):
    """A scarf swag across x0..x1 hanging in front of the plane y (it bulges toward y + side*depth, the room): a broad
    U whose hem sags `drop` below the rod at the centre and rises steeply into the gathered ends, `folds` stacked
    U-shaped folds (ridges in depth and small drops in height), and a scalloped lace border strip along the hem."""
    mi_lace = mi if mi_lace is None else mi_lace
    def hem(u):
        return ztop - 0.05 - drop * (1.0 - abs(2 * u - 1) ** 2.6)
    secs = []
    for i in range(n + 1):
        u = i / n
        xx = x0 + (x1 - x0) * u
        zb = hem(u)
        env = math.sin(math.pi * u) ** 0.5
        front, back = [], []
        for k in range(m + 1):
            t = k / m
            z = ztop - t * (ztop - zb) - 0.012 * math.sin(math.pi * folds * t) ** 2 * env
            ridge = 0.022 * math.sin(math.pi * folds * t) ** 2 * env
            bulge = depth * (t ** 0.7) * env + ridge
            front.append((xx, y + side * (bulge + 0.005), z))
            back.append((xx, y + side * bulge * 0.85, z + 0.002))
        secs.append(front + list(reversed(back)))
    mb.sweep(secs, mi)
    # lace: a thin strip under the hem with a scalloped lower edge
    k_sc = max(6, int((x1 - x0) / 0.05))
    for i in range(n * 2):
        u0, u1 = i / (n * 2), (i + 1) / (n * 2)
        pts = []
        for u in (u0, u1):
            xx = x0 + (x1 - x0) * u
            env = math.sin(math.pi * u) ** 0.5
            yb = y + side * (depth * env + 0.005)
            zt = hem(u) + 0.004
            zl = zt - lace * (0.55 + 0.45 * abs(math.sin(math.pi * u * k_sc)))
            pts.append((xx, yb, zt, zl))
        (xa, ya, zta, zla), (xb, yb_, ztb, zlb) = pts
        mb.quad((xa, ya, zta), (xb, yb_, ztb), (xb, yb_, zlb), (xa, ya, zla), mi_lace)


def jabot(mb, xa, xb, y, ztop, zbot, mi=0, pleats=3, depth=0.03, taper=0.35):
    """A cascade tail: a pleated panel hanging from the rod whose width narrows toward the hem."""
    nx, nz = pleats * 6, 12
    for iz in range(nz):
        za, zb = ztop - (ztop - zbot) * iz / nz, ztop - (ztop - zbot) * (iz + 1) / nz
        for ix in range(nx):
            def P(u, z):
                t = (ztop - z) / (ztop - zbot)
                w0 = xb - xa
                w = w0 * (1 - taper * t)
                xc = (xa + xb) / 2
                xx = xc - w / 2 + w * u
                return (xx, y + depth * (0.5 + 0.5 * math.sin(2 * math.pi * pleats * u)), z)
            u0, u1 = ix / nx, (ix + 1) / nx
            mb.quad(P(u0, za), P(u1, za), P(u1, zb), P(u0, zb), mi)


def sheer_panel(mb, x0, x1, y, z0, z1, folds=10, depth=0.035, mi=0):
    """Floor-length gathered sheer (a sinusoid in plan, slight flare at the hem)."""
    nx, nz = folds * 6, 8
    for iz in range(nz):
        za, zb = z1 - (z1 - z0) * iz / nz, z1 - (z1 - z0) * (iz + 1) / nz
        for ix in range(nx):
            def P(u, z):
                t = (z1 - z) / (z1 - z0)
                return (x0 + (x1 - x0) * u, y + depth * (1 + 0.3 * t) * math.sin(2 * math.pi * folds * u), z)
            u0, u1 = ix / nx, (ix + 1) / nx
            mb.quad(P(u0, za), P(u1, za), P(u1, zb), P(u0, zb), mi)


def finial_rod(mb, x0, x1, y, z, mi=0, r=0.011):
    """Decorative curtain rod with fleur-de-lis style finials and wall brackets (photo 04)."""
    mb.tube((x0, y, z), (x1, y, z), r, r, seg=10, mi=mi)
    for (xe, sgn) in ((x0, -1), (x1, 1)):
        mb.sphere((xe, y, z), r * 1.8, seg=10, rings=6, mi=mi)
        mb.tube((xe, y, z), (xe + sgn * 0.05, y, z), r * 0.6, r * 0.3, seg=6, mi=mi)
        for dz in (-1, 1):
            mb.path_tube([(xe + sgn * 0.01, y, z), (xe + sgn * 0.035, y, z + dz * 0.028), (xe + sgn * 0.055, y, z + dz * 0.015)], 0.004, seg=5, mi=mi)
        mb.box(xe - sgn * 0.12 - 0.008, xe - sgn * 0.12 + 0.008, y - 0.12, y, z - 0.02, z + 0.01, mi)


def slab_oval_hole(mb, x0, x1, y0, y1, z0, z1, cx, cy, rx, ry, n=40, mi=0):
    """A rectangular slab with an elliptical hole (a vanity top over an integral bowl): rays from the hole centre pair
    each ellipse point with a point on the rectangle (the four corner rays included)."""
    corners = [(x1, y1), (x0, y1), (x0, y0), (x1, y0)]
    angs = sorted([TAU * i / n for i in range(n)] + [math.atan2(py - cy, px - cx) % TAU for (px, py) in corners])
    E, R = [], []
    for t in angs:
        c, s_ = math.cos(t), math.sin(t)
        E.append((cx + rx * c, cy + ry * s_))
        ks = []
        if abs(c) > 1e-9:
            ks += [(x1 - cx) / c, (x0 - cx) / c]
        if abs(s_) > 1e-9:
            ks += [(y1 - cy) / s_, (y0 - cy) / s_]
        k = min(v for v in ks if v > 0)
        R.append((cx + k * c, cy + k * s_))
    m = len(angs)
    for i in range(m):
        j = (i + 1) % m
        (ea, eb), (ra, rb) = (E[i], E[j]), (R[i], R[j])
        mb.quad((*ra, z1), (*rb, z1), (*eb, z1), (*ea, z1), mi)
        mb.quad((*ea, z0), (*eb, z0), (*rb, z0), (*ra, z0), mi)
        mb.quad((*ea, z1), (*eb, z1), (*eb, z0), (*ea, z0), mi)
        mb.quad((*ra, z0), (*rb, z0), (*rb, z1), (*ra, z1), mi)


def bowl(mb, cx, cy, z_rim, rx, ry, depth=0.16, mi=0, n=40):
    """Open elliptical basin (integral vanity bowl): rings from the rim down, closed only at the bottom."""
    prof = [(1.0, 0.0), (0.98, -0.03), (0.93, -0.07), (0.82, -0.11), (0.64, -0.14), (0.40, -0.155), (0.15, -0.16)]
    secs = []
    for (k, dz) in prof:
        z = z_rim + dz * depth / 0.16
        secs.append([(cx + rx * k * math.cos(TAU * i / n), cy + ry * k * math.sin(TAU * i / n), z) for i in range(n)])
    mb.sweep(secs, mi, close=False, caps=False)
    zb = secs[-1][0][2]
    mb._add(secs[-1] + [(cx, cy, zb - 0.002)], [(i, (i + 1) % n, n) for i in range(n)], mi)


def rng_for(seed):
    return random.Random(seed)


# ================================================================ garage kit (photo 24) - local coordinates, placed as objects
def obox(mb, p0, p1, a, b, mi=0):
    """Oriented box around the segment p0 -> p1 with half-extent vectors a, b (perpendicular to it)."""
    ax = [p1[i] - p0[i] for i in range(3)]
    cr = (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
    if sum(cr[i] * ax[i] for i in range(3)) < 0:
        b = tuple(-v for v in b)
    def ring(p):
        return [tuple(p[i] + sa * a[i] + sb * b[i] for i in range(3)) for (sa, sb) in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    mb.hexa(ring(p0) + ring(p1), mi)


def place(ob, x, y, z=0.0, yaw=0.0):
    ob.location = (x, y, z)
    ob.rotation_euler = (0.0, 0.0, yaw)
    return ob


def wheelie_cart(mb, mi_body=0, mi_lid=1, mi_dark=2, mi_steel=3, mi_label=4, w=0.74, d=0.87, h=1.08):
    """96-gallon wheeled refuse / recycling cart (photo 24): tapered body whose lower front is stepped back between two
    proud pilasters (the lift pocket with its bar), a top rim band, an overhanging lid with a front lip, the hinge rod +
    handle and two wheels at the back. Front toward -y, origin at the floor centre."""
    bw0, bw1 = w / 2 - 0.09, w / 2 - 0.025
    yf0, yf1, yb0, yb1 = -d / 2 + 0.13, -d / 2 + 0.06, d / 2 - 0.10, d / 2 - 0.04
    z0, z1 = 0.05, h - 0.07

    def yf(z):
        return yf0 + (yf1 - yf0) * (z - z0) / (z1 - z0)

    def bw(z):
        return bw0 + (bw1 - bw0) * (z - z0) / (z1 - z0)
    mb.hexa([(-bw0, yf0, z0), (bw0, yf0, z0), (bw0, yb0, z0), (-bw0, yb0, z0),
             (-bw1, yf1, z1), (bw1, yf1, z1), (bw1, yb1, z1), (-bw1, yb1, z1)], mi_body)
    p = 0.035                                                                       # pilasters / rim stand proud
    xi = 0.12
    za, zb = z0 + 0.03, z1 - 0.20
    for s in (-1, 1):
        def xs(z):
            return (xi, bw(z)) if s > 0 else (-bw(z), -xi)
        ring = []
        for z in (za, zb):
            xa, xb = xs(z)
            ring += [(xa, yf(z) - p, z), (xb, yf(z) - p, z), (xb, yf(z) + 0.02, z), (xa, yf(z) + 0.02, z)]
        mb.hexa(ring, mi_body)
    za, zb = z1 - 0.20, z1
    mb.hexa([(-bw(za) - 0.01, yf(za) - p, za), (bw(za) + 0.01, yf(za) - p, za), (bw(za) + 0.01, yb0 + 0.06, za), (-bw(za) - 0.01, yb0 + 0.06, za),
             (-bw1 - 0.012, yf1 - p, zb), (bw1 + 0.012, yf1 - p, zb), (bw1 + 0.012, yb1 + 0.01, zb), (-bw1 - 0.012, yb1 + 0.01, zb)], mi_body)
    zbar = 0.50
    mb.tube((-0.10, yf(zbar) - 0.045, zbar), (0.10, yf(zbar) - 0.045, zbar), 0.012, 0.012, seg=8, mi=mi_steel)
    for s in (-1, 1):
        mb.box(s * 0.10 - 0.015, s * 0.10 + 0.015, yf(zbar) - 0.05, yf(zbar) + 0.01, zbar - 0.03, zbar + 0.03, mi_body)
    # lid + front lip, hinge rod, handle, axle housing, wheels, front skid, label
    mb.rbox(-w / 2, w / 2, -d / 2 - 0.02, d / 2 + 0.01, z1, z1 + 0.05, r=0.015, mi=mi_lid)
    mb.box(-w / 2, w / 2, -d / 2 - 0.03, -d / 2 + 0.01, z1 - 0.035, z1 + 0.05, mi_lid)
    mb.tube((-w / 2 + 0.06, d / 2 + 0.02, z1 - 0.01), (w / 2 - 0.06, d / 2 + 0.02, z1 - 0.01), 0.022, 0.022, seg=10, mi=mi_body)
    mb.tube((-w / 2 + 0.12, d / 2 + 0.05, z1 - 0.06), (w / 2 - 0.12, d / 2 + 0.05, z1 - 0.06), 0.017, 0.017, seg=8, mi=mi_body)
    mb.box(-bw0, bw0, yb0 - 0.10, yb0 + 0.05, 0.02, 0.20, mi_body)
    for s in (-1, 1):
        mb.tube((s * (bw0 + 0.005), yb0 - 0.02, 0.11), (s * (bw0 + 0.075), yb0 - 0.02, 0.11), 0.11, 0.11, seg=18, mi=mi_dark)
    mb.box(-bw0 + 0.04, bw0 - 0.04, yf0 - 0.01, yf0 + 0.08, 0.0, 0.05, mi_body)
    zl = z1 - 0.12
    mb.box(-bw(zl) + 0.06, -bw(zl) + 0.26, yf(zl) - p - 0.004, yf(zl) - p + 0.01, zl - 0.02, zl + 0.02, mi_label)


def plastic_chair(mb, mi=0, w=0.50, d=0.50, seat=0.44, back=0.86):
    """White resin stacking chair, front toward -y, origin at the floor centre."""
    mb.rbox(-w / 2, w / 2, -d / 2, d / 2 - 0.04, seat - 0.04, seat, r=0.02, mi=mi)
    mb.rbox(-w / 2, w / 2, d / 2 - 0.06, d / 2, seat, back, r=0.025, mi=mi)
    for k in range(3):
        z_ = seat + 0.12 + 0.11 * k
        mb.box(-w / 2 + 0.05, w / 2 - 0.05, d / 2 - 0.065, d / 2 - 0.055, z_, z_ + 0.05, mi)
    for sx in (-1, 1):
        mb.rbox(sx * w / 2 - (0.03 if sx > 0 else -0.03) - 0.02, sx * w / 2 - (0.03 if sx > 0 else -0.03) + 0.02, -d / 2 + 0.02, d / 2 - 0.04,
                seat + 0.16, seat + 0.20, r=0.015, mi=mi)                                          # arm rests
        for sy in (-1, 1):
            mb.tube((sx * (w / 2 - 0.05), sy * (d / 2 - 0.06), seat - 0.04), (sx * (w / 2 - 0.01), sy * (d / 2 - 0.01), 0.0), 0.022, 0.02, seg=8, mi=mi)


def riding_mower(mb, mi_red=0, mi_black=1, mi_grey=2, L=1.30, W=0.72):
    """Compact riding mower (photo 24): red hood + fenders, black seat with a back, steering column and wheel, grey deck,
    small front / large rear tyres. Front toward -y, origin at the floor centre."""
    ry0, ry1 = -L / 2, L / 2
    mb.rbox(-0.30, 0.30, ry0 + 0.20, ry1 - 0.25, 0.08, 0.20, r=0.04, mi=mi_grey)                  # cutting deck
    mb.rbox(-0.24, 0.24, ry0 + 0.02, ry0 + 0.52, 0.22, 0.48, r=0.08, mi=mi_red)                  # hood
    mb.rbox(-0.22, 0.22, ry0 + 0.05, ry0 + 0.46, 0.46, 0.52, r=0.05, mi=mi_red)
    mb.rbox(-0.25, 0.25, ry0 + 0.45, ry1 - 0.05, 0.24, 0.38, r=0.05, mi=mi_red)                  # body / footboard
    for s in (-1, 1):
        mb.rbox(s * 0.25 - 0.10, s * 0.25 + 0.10, ry1 - 0.50, ry1 - 0.02, 0.36, 0.50, r=0.05, mi=mi_red)   # rear fenders
    mb.rbox(-0.20, 0.20, ry1 - 0.45, ry1 - 0.12, 0.50, 0.58, r=0.04, mi=mi_black)                 # seat
    mb.rbox(-0.19, 0.19, ry1 - 0.16, ry1 - 0.08, 0.56, 0.80, r=0.04, mi=mi_black)                 # seat back
    col0, col1 = (0.0, ry0 + 0.52, 0.48), (0.0, ry0 + 0.62, 0.80)
    mb.tube(col0, col1, 0.02, 0.02, seg=8, mi=mi_black)
    ring = [(0.15 * math.cos(TAU * i / 16), col1[1] + 0.03 * math.sin(TAU * i / 16) * 0.3, col1[2] + 0.02 + 0.15 * math.sin(TAU * i / 16) * 0.28)
            for i in range(17)]
    mb.path_tube(ring, 0.014, seg=6, mi=mi_black)
    mb.tube((-0.15, col1[1], col1[2] + 0.02), (0.15, col1[1], col1[2] + 0.02), 0.01, 0.01, seg=6, mi=mi_black)
    for (sy, r, wd) in ((ry0 + 0.18, 0.13, 0.10), (ry1 - 0.22, 0.20, 0.15)):
        for s in (-1, 1):
            mb.tube((s * (W / 2 - wd), sy, r), (s * W / 2, sy, r), r, r, seg=20, mi=mi_black)
            mb.tube((s * (W / 2 + 0.002), sy, r), (s * (W / 2 + 0.004), sy, r), r * 0.55, r * 0.55, seg=16, mi=mi_grey)


def extension_ladder(mb, foot, top, rung_dir, span=0.42, fly=0.10, mi=0):
    """Aluminium extension ladder leaning from `foot` to `top` (near rail axis). rung_dir: horizontal unit vector from the
    near rail to the far rail. Rails are 0.08 deep (normal to the ladder plane) x 0.025; the fly section sits `fly` in
    front of the base section."""
    L = [top[i] - foot[i] for i in range(3)]
    ln = math.sqrt(sum(v * v for v in L))
    Lu = [v / ln for v in L]
    R = (rung_dir[0], rung_dir[1], 0.0)
    N = (Lu[1] * R[2] - Lu[2] * R[1], Lu[2] * R[0] - Lu[0] * R[2], Lu[0] * R[1] - Lu[1] * R[0])
    nn = math.sqrt(sum(v * v for v in N))
    N = tuple(v / nn for v in N)
    a = tuple(0.0125 * v for v in R)
    b = tuple(0.04 * v for v in N)
    for (off_n, s0, s1, sp) in ((0.0, 0.0, 1.0, span), (fly, 0.18, 0.93, span - 0.05)):
        base = [foot[i] + N[i] * off_n + (span - sp) / 2 * R[i] for i in range(3)]
        for k in (0.0, sp):
            p0 = [base[i] + R[i] * k + L[i] * s0 for i in range(3)]
            p1 = [base[i] + R[i] * k + L[i] * s1 for i in range(3)]
            obox(mb, p0, p1, a, b, mi)
        n_r = int(ln * (s1 - s0) / 0.30)
        for j in range(1, n_r + 1):
            t = s0 + (s1 - s0) * j / (n_r + 1)
            c0 = [base[i] + L[i] * t for i in range(3)]
            c1 = [c0[i] + R[i] * sp for i in range(3)]
            mb.tube(tuple(c0), tuple(c1), 0.016, 0.016, seg=6, mi=mi)


def hose_reel(mb, mi_frame=0, mi_hose=1, mi_dark=2, r=0.22, wd=0.20):
    """Wall / floor hose reel (photo 24): two white side discs with spokes, a drum of wound green hose, a grey frame and
    crank. Axis along x, origin at the floor centre."""
    zc = r + 0.03
    for s in (-1, 1):
        mb.tube((s * wd / 2, 0.0, zc), (s * (wd / 2 + 0.02), 0.0, zc), r, r, seg=28, mi=mi_frame)
        mb.tube((s * (wd / 2 + 0.02), 0.0, zc), (s * (wd / 2 + 0.03), 0.0, zc), r * 0.30, r * 0.30, seg=16, mi=mi_dark)
    for k in range(5):
        x_ = -wd / 2 + 0.02 + (wd - 0.04) * k / 4
        mb.tube((x_ - 0.018, 0.0, zc), (x_ + 0.018, 0.0, zc), r * 0.82, r * 0.82, seg=24, mi=mi_hose)
    mb.tube((-wd / 2 - 0.04, 0.0, zc), (wd / 2 + 0.06, 0.0, zc), 0.015, 0.015, seg=6, mi=mi_dark)
    mb.tube((wd / 2 + 0.06, 0.0, zc), (wd / 2 + 0.06, 0.10, zc - 0.05), 0.012, 0.012, seg=6, mi=mi_dark)
    for s in (-1, 1):
        mb.tube((s * (wd / 2 + 0.04), -0.16, 0.0), (s * (wd / 2 + 0.04), 0.0, zc), 0.014, 0.014, seg=6, mi=mi_dark)
        mb.tube((s * (wd / 2 + 0.04), 0.16, 0.0), (s * (wd / 2 + 0.04), 0.0, zc), 0.014, 0.014, seg=6, mi=mi_dark)


__all__ = ['mats', 'flare_sofa', 'slipper_chair', 'pillow', 'oval_cocktail_table', 'octagon_table', 'hammered_vase', 'urn_vase',
           'bar_cart', 'candlestick_lamp', 'demilune', 'plant_stand', 'planter', 'peace_lily', 'dracaena', 'aloe', 'swag_valance',
           'jabot', 'sheer_panel', 'finial_rod', 'soft_loft', 'local_frame', 'tapered_leg', 'MB', 'rot2']
