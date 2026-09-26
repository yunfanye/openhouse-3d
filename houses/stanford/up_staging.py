"""Contents of the upper floor (photos 15-23): fixtures, window treatments, furniture, textiles, art and lights, each
placed from point solves of its photograph (cams/int_p*.json) and shaped after the real piece in the photo.
Flat art, prints, rugs, shower curtains and towels carry their own pixels, rectified from the listing photographs
(archviz.phototex; the photo and the quad of every texture are listed in PHOTO_TEX).  Everything here is staging (the
seller's furniture, virtually re-created) except the bath fixtures, fans, lights and blinds, which are fixtures.
Imported only by interior_upper."""
import math
import os
import random

from .plan import *
from . import interior_upper as U
from .interior_upper import XMT
from archviz.mesh import MB
from archviz.lights import add_light, area_light
from archviz.cladding import Face
from archviz import materials as _m
from archviz import plants as _pl
from archviz import stagekit as sk
from archviz import phototex as ptx

COLL, LCOLL = U.COLL, U.LCOLL
Z0, Z1 = U.Z0, U.Z1
PHOTOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'photos')

# ---------------------------------------------------------------- photo textures: key -> (photo, quad TL,TR,BR,BL, size, opts)
PHOTO_TEX = {
    'art_bed':      ('17', [(839, 351), (897.5, 344), (897.5, 432), (840, 437)], (160, 240), {}),
    'emb_1':        ('16', [(929.5, 407.5), (998, 402.5), (998, 463), (930, 464.5)], (200, 180), {}),
    'emb_2':        ('16', [(1030, 386.25), (1094.5, 378.75), (1095, 461.25), (1031.25, 463)], (180, 220), {}),
    'emb_3':        ('16', [(1133.75, 392.5), (1229.5, 382.5), (1230, 456.25), (1134.5, 458.75)], (240, 180), {}),
    'bokeh':        ('19', [(334, 303.5), (479, 324.5), (479, 446.5), (334, 442.5)], (300, 300), {}),
    'paris_1':      ('19', [(885, 360), (945, 348), (945, 410), (885, 415)], (160, 170), {}),
    'paris_2':      ('19', [(990, 361), (1075, 349), (1075, 424), (990, 427)], (220, 190), {}),
    'map_21':       ('21', [(74, 290), (322.5, 330), (322.5, 460), (74, 455)], (400, 200), {}),
    'still_21':     ('21', [(1201, 371), (1338, 353), (1340, 441), (1203, 449)], (300, 190), {}),
    'camel_15':     ('15', [(363, 491), (415, 491), (415, 542), (363, 542)], (120, 110), {}),
    'curtain_18':   ('18', [(1008, 330), (1290, 312), (1290, 548), (1008, 548)], (300, 250), {'tile': True, 'mirror': True}),
    'curtain_23':   ('23', [(1112, 330), (1368, 300), (1368, 560), (1112, 560)], (280, 280), {'tile': True, 'mirror': True}),
    'towel_18':     ('18', [(243, 405), (330, 409), (326, 528), (243, 524)], (120, 170), {}),
    'towel_23':     ('23', [(300, 300), (418, 316), (415, 468), (302, 462)], (140, 190), {}),
    'soap_18':      ('18', [(1392, 588), (1470, 588), (1470, 690), (1392, 690)], (90, 120), {}),
    'soap_23':      ('23', [(1406, 628), (1488, 628), (1488, 725), (1406, 725)], (90, 110), {}),
    'birds_16':     ('16', [(1045, 560), (1106.25, 562), (1098.75, 618.75), (1040.5, 613.75)], (160, 150), {'tile': True}),
    'pano_20a':     ('20', [(75, 309), (162, 317), (162, 349), (75, 343)], (260, 90), {}),
    'pano_20b':     ('20', [(123, 386), (204, 392), (204, 421), (123, 417)], (240, 80), {}),
    'plaque_20':    ('20', [(572, 357), (627, 363), (627, 414), (572, 412)], (120, 130), {}),
}


# the photo cameras used to rectify textures of surfaces given in 3D (INT_UP point solves, cams/int_p*.json)
PHOTO_CAM = {        # INT_CAM's final cameras (cams_upper.py, tools/intcam_solve.py); yaw = heading from +Y toward +X
    '15': dict(x=9.394, y=6.48, z=3.986, yaw=114.5341, pitch=-15.6758, lens=17.06, sx=0.0, sy=0.0),
    '16': dict(x=4.094, y=7.622, z=3.85, yaw=329.0618, lens=16.41, sx=-0.1151, sy=0.0008),
    '17': dict(x=4.182, y=11.337, z=3.853, yaw=225.8023, lens=16.27, sx=0.0665, sy=0.0001),
    '18': dict(x=1.477, y=6.341, z=3.816, yaw=213.2991, lens=15.16, sx=0.0, sy=-0.0004),
    '19': dict(x=9.16, y=7.524, z=3.736, yaw=39.6405, lens=16.6, sx=0.0092, sy=-0.0063),
    '20': dict(x=8.053, y=4.82, z=3.845, yaw=216.1984, lens=16.05, sx=0.0523, sy=-0.0066),
    '21': dict(x=9.211, y=4.8, z=3.892, yaw=139.835, lens=14.89, sx=0.0, sy=0.0022),
    '22': dict(x=2.775, y=1.848, z=3.892, yaw=297.4081, lens=16.22, sx=0.0, sy=0.0052),
    '23': dict(x=7.079, y=7.98, z=3.913, yaw=33.8792, lens=15.61, sx=0.0, sy=-0.0031),
}


def project(cam, p, size=(1536, 1024)):
    """World point -> photo pixel through a level (+ lens shift, + vertical aspect) camera."""
    c = PHOTO_CAM[cam]
    W, H = size
    S_ = max(W, H)
    yaw = math.radians(c['yaw'])
    fwd = (math.sin(yaw), math.cos(yaw), 0.0)
    right = (math.cos(yaw), -math.sin(yaw), 0.0)
    rel = (p[0] - c['x'], p[1] - c['y'], p[2] - c['z'])
    d = rel[0] * fwd[0] + rel[1] * fwd[1]
    k = c['lens'] / 36.0
    xn = (rel[0] * right[0] + rel[1] * right[1]) / d * k
    yn = rel[2] / d * k
    return (W / 2 + (xn - c['sx']) * S_, H / 2 - (yn - c['sy']) * S_ * c.get('a', 1.0))


def tex3d(name, cam, corners, size, **kw):
    """Photo texture of a planar 3D rectangle (world corners TL, TR, BR, BL as the texture should read)."""
    quad = [project(cam, c) for c in corners]
    PHOTO_TEX[name] = (cam, quad, size, kw)
    return photo_tex(name, rough=kw.get('rough', 0.9))


def photo_tex(key, gain=1.0, rough=0.6, coat=0.0):
    ph, quad, size, opt = PHOTO_TEX[key]
    if opt.get('mirror'):                       # seen in a mirror: flip left <-> right
        quad = [quad[1], quad[0], quad[3], quad[2]]
    img = ptx.rectify(os.path.join(PHOTOS, f"{ph}.jpg"), quad, size, f"PhotoTex_{key}", gain=opt.get('gain', gain),
                      flatten=opt.get('flatten', 0.0), saturation=opt.get('sat', 1.0), tile=opt.get('tile', False))
    return ptx.photo_material(f"Photo_{key}", img, rough=rough, coat=coat)


# ================================================================ materials
def mats(M):
    S = M.setdefault
    S('espresso', _m.wood("EspressoWood", light=(0.075, 0.055, 0.045, 1), dark=(0.035, 0.025, 0.022, 1), grain_axis='X', rough=0.45, coat=0.3))
    S('black_paint', _m.new_mat("BlackSatinFurn", (0.018, 0.018, 0.02, 1), rough=0.38, coat=0.25))
    S('grey_paint', _m.wood("GreyWashDresser", light=(0.13, 0.13, 0.13, 1), dark=(0.09, 0.09, 0.09, 1), grain_axis='X', rough=0.45, coat=0.25))
    S('cherry', _m.wood("CherryChest", light=(0.42, 0.14, 0.05, 1), dark=(0.28, 0.08, 0.03, 1), grain_axis='X', rough=0.4, coat=0.35))
    S('oak_lam', _m.wood("OakLaminate", light=(0.30, 0.15, 0.06, 1), dark=(0.20, 0.09, 0.035, 1), grain_axis='Z', rough=0.45, coat=0.3))
    S('oak_furn', _m.wood("OakVeneerFurn", light=(0.46, 0.24, 0.10, 1), dark=(0.30, 0.15, 0.06, 1), grain_axis='X', rough=0.5, coat=0.2))
    S('silver', _m.new_mat("PolishedSilver", (0.80, 0.80, 0.79, 1), rough=0.18, metal=1.0))
    S('champagne', _m.new_mat("ChampagneFrame", (0.62, 0.56, 0.46, 1), rough=0.3, metal=0.85))
    S('frame_gold', _m.new_mat("FrameGoldBead", (0.62, 0.46, 0.22, 1), rough=0.35, metal=0.8))
    S('frame_black', _m.new_mat("FrameBlack", (0.03, 0.03, 0.03, 1), rough=0.4, coat=0.3))
    S('gold_metal', _m.new_mat("GoldMetal", (0.72, 0.52, 0.24, 1), rough=0.28, metal=1.0))
    S('mat_board', _m.new_mat("MatBoardWhite", (0.85, 0.85, 0.82, 1), rough=0.8))
    S('shade_white', _m.new_mat("DrumShadeWhite", (0.88, 0.87, 0.84, 1), rough=0.8, transmission=0.3))
    S('lamp_crystal', _m.new_mat("LampCrystal", (0.95, 0.96, 0.98, 1), rough=0.03, transmission=1.0, ior=1.55))
    S('glass_clear', _m.new_mat("TableGlass", (0.9, 0.95, 0.93, 1), rough=0.0, transmission=1.0, ior=1.5))
    S('fan_body', _m.new_mat("FanPewter", (0.46, 0.45, 0.43, 1), rough=0.32, metal=0.9))
    S('fan_blade_light', _m.wood("FanBladeWhitewash", light=(0.70, 0.66, 0.60, 1), dark=(0.60, 0.56, 0.50, 1), grain_axis='X', rough=0.5, coat=0.2))
    S('fan_blade_white', _m.new_mat("FanBladeWhite", (0.82, 0.82, 0.80, 1), rough=0.45, coat=0.2))
    S('fan_glass', _m.new_mat("FanFrostedTulip", (0.92, 0.90, 0.86, 1), rough=0.35, transmission=0.55))
    S('comforter_vine', _vine_quilt("ComforterVineQuilt"))
    S('sheet_white', _m.linen("SheetWhite", base=(0.84, 0.84, 0.82, 1), wrinkle=0.35))
    S('sofa_blue', _m.fabric("SofaBlueGreyVelvet", (0.19, 0.25, 0.30, 1), rough=0.75, sheen=0.7, weave=140, bump=0.08))
    S('recliner_grey', _m.leather("ReclinerCharcoal", base=(0.085, 0.085, 0.09, 1), rough=0.42))
    S('chair_grey', _m.fabric("ChairGreyMesh", (0.22, 0.23, 0.24, 1), rough=0.7, sheen=0.4, weave=160))
    S('bird_print', _birds("BirdPrintPillow"))
    S('bike_white', _m.new_mat("BikeShroudSilver", (0.50, 0.51, 0.52, 1), rough=0.35, metal=0.4, coat=0.4))
    S('bike_frame', _m.new_mat("BikeFrameGrey", (0.30, 0.31, 0.32, 1), rough=0.35, metal=0.6))
    S('vinyl_black', _m.leather("VinylBlack", base=(0.02, 0.02, 0.022, 1), rough=0.4))
    S('marble_top', _m.new_mat("CulturedMarble", (0.80, 0.77, 0.70, 1), rough=0.10, coat=0.7, spec=0.5))
    S('porcelain', _m.new_mat("PorcelainWhite", (0.86, 0.86, 0.84, 1), rough=0.06, coat=0.8))
    S('maple_cab', _m.wood("VanityMaple", light=(0.20, 0.068, 0.016, 1), dark=(0.14, 0.045, 0.010, 1), grain_axis='Z', rough=0.4, coat=0.35))
    S('mirror', _m.new_mat("UpMirror", (0.95, 0.95, 0.95, 1), rough=0.0, metal=1.0))
    S('paper', _m.new_mat("PaperWhite", (0.85, 0.85, 0.83, 1), rough=0.9))
    S('dark_plastic', _m.new_mat("DarkPlastic", (0.03, 0.03, 0.035, 1), rough=0.35, coat=0.3))
    S('cardboard', _m.new_mat("Cardboard", (0.55, 0.41, 0.25, 1), rough=0.9))
    S('printer_grey', _m.new_mat("PrinterGrey", (0.10, 0.10, 0.11, 1), rough=0.35, coat=0.3))
    S('wire', _m.new_mat("WireShelfWhite", (0.86, 0.86, 0.84, 1), rough=0.3, spec=0.5, coat=0.3))
    S('art_hall', _m.art_abstract("ArtHallPrint", bg=(0.74, 0.70, 0.62, 1), fg=(0.30, 0.26, 0.22, 1), scale=5.0, thresh=0.58))
    return M


def _ramp(nt, fac, stops, constant=False):
    """Colour ramp with any number of stops (archviz.materials._ramp re-sorts its elements while assigning them, which
    scrambles ramps with more than two stops)."""
    r = nt.nodes.new("ShaderNodeValToRGB")
    cr = r.color_ramp
    if constant:
        cr.interpolation = 'CONSTANT'
    stops = sorted(stops, key=lambda t: t[0])
    cr.elements[0].position, cr.elements[0].color = stops[0]
    cr.elements[-1].position, cr.elements[-1].color = stops[-1]
    for (pos, col) in stops[1:-1]:
        e = cr.elements.new(pos)
        e.color = col
    nt.links.new(r.inputs["Fac"], fac)
    return r.outputs["Color"]


def _vine_quilt(name):
    """White quilted comforter with trailing vines of tiny rose-brown flowers and green leaves in bands across the bed
    (photos 16/17): bands every ~0.22 m along the sheet's v (UV in metres), wavy, with quilting channels in the bump."""
    m, nt, b = _m._new(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(sep.inputs["Vector"], tc.outputs["UV"])
    u, v = sep.outputs["X"], sep.outputs["Y"]
    wave = _m._math(nt, 'MULTIPLY', _m._math(nt, 'SINE', _m._math(nt, 'MULTIPLY', v, 19.0)), 0.022)
    uu = _m._math(nt, 'ADD', u, wave)                         # vines run along the bed (photos 16, 17), ~0.22 m apart
    band = _m._math(nt, 'FRACT', _m._math(nt, 'DIVIDE', uu, 0.215))
    d = _m._math(nt, 'ABSOLUTE', _m._math(nt, 'SUBTRACT', band, 0.5))
    line = _m._math(nt, 'LESS_THAN', d, 0.085)
    stem = _m._math(nt, 'LESS_THAN', d, 0.012)
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(comb.inputs["X"], uu); nt.links.new(comb.inputs["Y"], v)
    vo = _m._voronoi(nt, comb.outputs["Vector"], scale=80.0, rand=0.9)
    flower = _m._math(nt, 'MAXIMUM', _m._math(nt, 'MULTIPLY', line, _m._math(nt, 'LESS_THAN', vo.outputs["Distance"], 0.42)),
                      _m._math(nt, 'MULTIPLY', stem, 0.7))
    cs = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(cs.inputs["Color"], vo.outputs["Color"])
    petal = _ramp(nt, cs.outputs["Red"], [(0.0, (0.55, 0.26, 0.26, 1)), (0.45, (0.62, 0.38, 0.34, 1)), (0.6, (0.36, 0.44, 0.26, 1)),
                                              (1.0, (0.45, 0.36, 0.30, 1))])
    base = (0.86, 0.855, 0.84, 1)
    col = _m._mixrgb(nt, flower, base, petal)
    nt.links.new(b.inputs["Base Color"], col)
    _m._set(b, "Roughness", 0.92); _m._set(b, "Sheen Weight", 0.5); _m._set(b, "Specular IOR Level", 0.25)
    ch = _m._math(nt, 'ABSOLUTE', _m._math(nt, 'SINE', _m._math(nt, 'MULTIPLY', v, 2 * math.pi / 0.107)))
    wr = _m._noise(nt, _m._coords(nt), scale=5.0, detail=3.0, distortion=0.6)
    h = _m._math(nt, 'ADD', _m._math(nt, 'MULTIPLY', ch, 0.6), _m._math(nt, 'MULTIPLY', wr, 0.5))
    _m._bump(nt, b, h, 0.35, 0.012)
    return m


def _birds(name):
    """Bird-print pillow cotton (photo 16): colourful songbirds scattered on ivory."""
    m, nt, b = _m._new(name)
    vec = _m._coords(nt)
    v = _m._voronoi(nt, vec, scale=16.0, rand=0.8)
    cc = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(cc.inputs["Color"], v.outputs["Color"])
    spot = _m._math(nt, 'LESS_THAN', v.outputs["Distance"], 0.30)
    hue = _ramp(nt, cc.outputs["Red"], [(0.0, (0.72, 0.14, 0.06, 1)), (0.25, (0.85, 0.60, 0.10, 1)), (0.5, (0.12, 0.40, 0.50, 1)),
                                           (0.75, (0.25, 0.48, 0.15, 1)), (1.0, (0.55, 0.30, 0.45, 1))])
    col = _m._mixrgb(nt, spot, (0.86, 0.84, 0.78, 1), hue)
    nt.links.new(b.inputs["Base Color"], col)
    _m._set(b, "Roughness", 0.85); _m._set(b, "Sheen Weight", 0.4)
    return m


# ================================================================ generic fixtures
def ceiling_fan(M, name, x, y, zc, blade=0.62, rot=0.3, blades='fan_blade_light', downrod=0.12, energy=0.0):
    """Five-blade fan with a short downrod, a louvred motor housing with a lower trim ring, curved blade irons and a
    4-tulip light kit with a pull chain (photos 16, 17, 19-21)."""
    mb, bl, gl = MB(), MB(), MB()
    zm = zc - downrod - 0.05
    mb.cylinder(x, y, zc - 0.05, zc, 0.075, 0.065, seg=20, mi=0)                       # canopy
    mb.cylinder(x, y, zm + 0.08, zc - 0.05, 0.011, seg=8, mi=0)                        # downrod
    mb.lathe(x, y, zm - 0.06, [(0.0, 0), (0.07, 0.0), (0.135, 0.03), (0.15, 0.07), (0.14, 0.11), (0.09, 0.14), (0.03, 0.15), (0.0, 0.15)], seg=28, mi=0)
    for k in range(22):                                                                # vent louvres
        a = 2 * math.pi * k / 22
        mb.tube((x + 0.147 * math.cos(a), y + 0.147 * math.sin(a), zm + 0.035), (x + 0.12 * math.cos(a), y + 0.12 * math.sin(a), zm + 0.075),
                0.004, 0.004, seg=4, mi=0)
    for i in range(5):
        a = rot + 2 * math.pi * i / 5
        c, s = math.cos(a), math.sin(a)
        mb.path_tube([(x + 0.10 * c, y + 0.10 * s, zm - 0.01), (x + 0.18 * c + 0.03 * s, y + 0.18 * s - 0.03 * c, zm - 0.03),
                      (x + 0.26 * c, y + 0.26 * s, zm - 0.03)], 0.012, seg=6, mi=0)
        L0, L1 = 0.22, 0.22 + blade
        pts = []
        for (L, w_) in ((L0, 0.065), (L1 - 0.06, 0.082), (L1, 0.07)):
            for sgn in (-1, 1):
                pts.append((x + L * c - sgn * w_ * s, y + L * s + sgn * w_ * c, zm - 0.035 + sgn * 0.010))
        q0 = [pts[0], pts[2], pts[3], pts[1]]
        q1 = [pts[2], pts[4], pts[5], pts[3]]
        for q in (q0, q1):
            bl.hexa([(a_[0], a_[1], a_[2] - 0.005) for a_ in q] + [(a_[0], a_[1], a_[2] + 0.005) for a_ in q], 0)
    mb.cylinder(x, y, zm - 0.13, zm - 0.06, 0.055, 0.045, seg=16, mi=0)               # switch cup
    for i in range(4):
        a = rot + 2 * math.pi * i / 4 + 0.4
        cx, cy = x + 0.105 * math.cos(a), y + 0.105 * math.sin(a)
        mb.tube((x, y, zm - 0.10), (cx, cy, zm - 0.13), 0.008, 0.008, seg=5, mi=0)
        gl.lathe(cx, cy, zm - 0.26, [(0.0, 0.0), (0.028, 0.0), (0.05, 0.03), (0.06, 0.08), (0.045, 0.12), (0.022, 0.13), (0.0, 0.13)], seg=16, mi=0)
    mb.cylinder(x, y, zm - 0.40, zm - 0.14, 0.0015, seg=4, mi=0)                       # pull chain
    mb.sphere((x, y, zm - 0.41), 0.008, seg=6, rings=4, mi=0)
    mb.build(name, [M['fan_body']], coll=COLL, smooth=True)
    bl.build(name + "_Blades", [M[blades]], coll=COLL)
    gl.build(name + "_Glass", [M['fan_glass']], coll=COLL, smooth=True)
    if energy > 0:
        add_light("L_" + name, 'POINT', (x, y, zm - 0.2), energy, color=(1.0, 0.90, 0.78), size=0.1, coll=LCOLL)


def smoke_detector(mb, x, y, z, mi=0):
    mb.cylinder(x, y, z - 0.035, z, 0.065, 0.06, seg=20, mi=mi)


def blinds(M, name, o, mat, drop=1.0, tilt=0.5, face=None, inset=0.02, valance=False):
    """2" faux-wood blinds inside a window's return (plan opening `o`), lowered to `drop` (fraction), slats `tilt`."""
    from archviz.furnish import h_blinds
    mb = MB()
    along = o['along']
    if face is None:
        if o['name'].startswith('rear'):
            b, s = YB1 - EWT, -1
        elif o['name'] == 'bay_up_win':
            b, s = Y_BAY + BWT, +1
        elif o['name'] == 'cen_win':
            b, s = CEN[2] + EWT, +1
        else:
            b, s = U.YF, +1
    else:
        b, s = face
    z1 = o['z1'] - 0.005
    z0 = z1 - (z1 - o['z0']) * drop
    units = o.get('units', 1)
    spans = [(o['a0'] + 0.01, o['a1'] - 0.01)] if units == 1 else [(o['a0'] + 0.02, (o['a0'] + o['a1']) / 2 - 0.03),
                                                                   ((o['a0'] + o['a1']) / 2 + 0.03, o['a1'] - 0.02)]
    for (a0, a1) in spans:
        h_blinds(mb, along, a0, a1, b + s * (-0.10 + inset), s, z0, z1, tilt=tilt, mi=0, mi_cord=1)
        if valance:
            if along == 'X':
                y0_, y1_ = sorted((b + s * (-0.10 + inset + 0.055), b + s * (-0.10 + inset + 0.075)))
                mb.box(a0 - 0.01, a1 + 0.01, y0_, y1_, z1 - 0.075, z1 + 0.005, 0)
    mb.build(name, [M[mat], M['cord_white']], coll=COLL)


def frame_art(M, name, along, a0, a1, b, side, z0, z1, tex, frame='frame_gold', fw=0.035, depth=0.03, mat_w=0.0, profile='flat'):
    """Framed art on a wall: a moulded frame (fw wide, depth deep) around a rectified photo texture; optional mat."""
    fm = MB()
    f = Face(along, b, side)
    for (p0, p1, q0, q1) in ((a0, a1, z1 - fw, z1), (a0, a1, z0, z0 + fw), (a0, a0 + fw, z0, z1), (a1 - fw, a1, z0, z1)):
        f.box(fm, p0, p1, 0.002, depth, q0, q1, 0)
        if profile == 'step':
            f.box(fm, p0 + (0.008 if p1 - p0 > fw else 0), p1 - (0.008 if p1 - p0 > fw else 0), depth, depth + 0.008,
                  q0 + (0.008 if q1 - q0 > fw else 0), q1 - (0.008 if q1 - q0 > fw else 0), 0)
    mats = [M[frame]]
    if mat_w > 0:
        e = fw
        for (p0, p1, q0, q1) in ((a0 + e, a1 - e, z1 - e - mat_w, z1 - e), (a0 + e, a1 - e, z0 + e, z0 + e + mat_w),
                                 (a0 + e, a0 + e + mat_w, z0 + e, z1 - e), (a1 - e - mat_w, a1 - e, z0 + e, z1 - e)):
            f.box(fm, p0, p1, 0.002, depth * 0.35, q0, q1, 1)
        mats.append(M['mat_board'])
    fm.build(name + "_Frame", mats, coll=COLL)
    e = fw + mat_w
    d = depth * 0.3
    corners = ptx.rect_corners(along, a0 + e, a1 - e, b + side * d, z0 + e, z1 - e, side)
    mat = tex if not isinstance(tex, str) else M[tex]
    ptx.uv_quad_mesh(name, corners, mat, coll=COLL)


def canvas_art(M, name, along, a0, a1, b, side, z0, z1, tex, depth=0.035):
    """Gallery-wrapped canvas (no frame): the photo texture on the front, its edges wrapped."""
    corners = ptx.rect_corners(along, a0, a1, b + side * depth, z0, z1, side)
    ptx.uv_quad_mesh(name, corners, tex, coll=COLL, thickness=depth - 0.004, edge_mat=M['mat_board'])


def light_bar(M, name, a0, a1, b, side, z, n=6, along='Y', energy=35):
    """Chrome vanity bar with n clear globe bulbs (photos 18, 23)."""
    mb = MB()
    f = Face(along, b, side)
    f.box(mb, a0, a1, 0.0, 0.045, z - 0.035, z + 0.035, 0)
    for i in range(n):
        a = a0 + (a1 - a0) * (i + 0.5) / n
        p = f.p(a, 0.075, z - 0.01)
        mb.sphere(p, 0.048, seg=16, rings=10, mi=1)
    mb.build(name, [M['chrome'], M['bulb']], coll=COLL, smooth=True)
    for i in range(0, n, 2):
        a = a0 + (a1 - a0) * (i + 1.0) / n
        p = f.p(a, 0.20, z - 0.05)
        add_light(f"L_{name}_{i}", 'POINT', p, energy, color=(1.0, 0.91, 0.78), size=0.12, coll=LCOLL)


def bouquet(M, name, x, y, z, kind='hydrangea', r=0.07, seed=0, vase=True, stem_h=0.06):
    """A small posy: a clear / white vase and a dome of florets (hydrangea: pale green-white; mauve; red roses)."""
    rng = random.Random(seed)
    mb = MB()
    if vase:
        mb.lathe(x, y, z, [(0.0, 0.0), (0.035, 0.0), (0.04, 0.03), (0.03, stem_h), (0.034, stem_h + 0.01), (0.0, stem_h + 0.01)], seg=16, mi=0)
    zc = z + stem_h + r * 0.8
    n = {'rose': 5, 'hydrangea': 40, 'mauve': 30}.get(kind, 30)
    for i in range(n):
        th = rng.uniform(0, 2 * math.pi); ph = rng.uniform(0, 1.3)
        rr = r * rng.uniform(0.75, 1.0)
        c = (x + rr * math.sin(ph) * math.cos(th), y + rr * math.sin(ph) * math.sin(th), zc + rr * math.cos(ph) * 0.8)
        mb.sphere(c, r * (0.28 if kind != 'rose' else 0.45), seg=8, rings=5, mi=1 + (i % 2))
    for i in range(6):
        a = rng.uniform(0, 2 * math.pi)
        mb.tube((x, y, zc - r * 0.5), (x + r * 1.3 * math.cos(a), y + r * 1.3 * math.sin(a), zc - r * 0.2), 0.012, 0.004, seg=4, mi=3)
    cols = {'hydrangea': ((0.82, 0.86, 0.72, 1), (0.70, 0.80, 0.55, 1)), 'mauve': ((0.62, 0.50, 0.62, 1), (0.80, 0.78, 0.84, 1)),
            'rose': ((0.50, 0.03, 0.04, 1), (0.40, 0.02, 0.03, 1))}[kind]
    ms = [M['glass_clear'], _m.fabric(f"{name}_Petal1", cols[0], rough=0.7, sheen=0.3, weave=200, bump=0.2),
          _m.fabric(f"{name}_Petal2", cols[1], rough=0.7, sheen=0.3, weave=200, bump=0.2),
          _m.new_mat(f"{name}_Leaf", (0.10, 0.25, 0.08, 1), rough=0.5)]
    mb.build(name, ms, coll=COLL, smooth=True)


def _stripe_comforter(name):
    """Bedroom 19's comforter (photo 19): bands across the bed, measured from the foot hem (UV v in metres; the side
    drops show them as vertical stripes): the foot drop and ~0.25 m of the top in butter yellow, a lavender-grey band,
    a white band with a grey quatrefoil trellis, lavender, thin white / yellow pin stripes, lavender to the head."""
    m, nt, b = _m._new(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(sep.inputs["Vector"], tc.outputs["UV"])
    u, v = sep.outputs["X"], sep.outputs["Y"]
    Y, LAV, WH = (0.70, 0.47, 0.14, 1), (0.27, 0.27, 0.38, 1), (0.84, 0.83, 0.80, 1)
    stops = [(0.0, Y), (0.22, LAV), (0.42, WH), (0.64, LAV), (0.72, WH), (0.73, Y), (0.745, WH), (0.755, LAV)]
    t = _m._math(nt, 'DIVIDE', v, 2.5)            # bands across the bed, from the foot hem (19: vertical stripes on the side drop)
    col = _ramp(nt, t, stops, constant=True)
    tr = _m._math(nt, 'MULTIPLY', _m._math(nt, 'SINE', _m._math(nt, 'MULTIPLY', u, 24.0)), _m._math(nt, 'SINE', _m._math(nt, 'MULTIPLY', v, 24.0)))
    line = _m._math(nt, 'LESS_THAN', _m._math(nt, 'ABSOLUTE', tr), 0.10)
    inwhite = _m._math(nt, 'MULTIPLY', _m._math(nt, 'GREATER_THAN', t, 0.42), _m._math(nt, 'LESS_THAN', t, 0.64))
    col = _m._mixrgb(nt, _m._math(nt, 'MULTIPLY', line, inwhite), col, (0.40, 0.40, 0.46, 1))
    nt.links.new(b.inputs["Base Color"], col)
    _m._set(b, "Roughness", 0.8); _m._set(b, "Sheen Weight", 0.6)
    ch = _m._math(nt, 'ABSOLUTE', _m._math(nt, 'SINE', _m._math(nt, 'MULTIPLY', u, 2 * math.pi / 0.25)))
    _m._bump(nt, b, _m._math(nt, 'ADD', ch, _m._noise(nt, _m._coords(nt), scale=6.0, detail=3.0)), 0.3, 0.01)
    return m


def _matelasse(name, base=(0.84, 0.84, 0.83, 1)):
    """White matelasse coverlet (photo 20): a woven relief of waves / diamonds in the bump."""
    m, nt, b = _m._new(name)
    vec = _m._coords(nt)
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(sep.inputs["Vector"], vec)
    w1 = _m._math(nt, 'SINE', _m._math(nt, 'ADD', _m._math(nt, 'MULTIPLY', sep.outputs["X"], 28.0), _m._math(nt, 'MULTIPLY', sep.outputs["Y"], 16.0)))
    w2 = _m._math(nt, 'SINE', _m._math(nt, 'SUBTRACT', _m._math(nt, 'MULTIPLY', sep.outputs["X"], 28.0), _m._math(nt, 'MULTIPLY', sep.outputs["Y"], 16.0)))
    h = _m._math(nt, 'ABSOLUTE', _m._math(nt, 'MULTIPLY', w1, w2))
    n = _m._noise(nt, vec, scale=5.0, detail=3.0)
    nt.links.new(b.inputs["Base Color"], _m._mixrgb(nt, _m._math(nt, 'MULTIPLY', h, 0.10), base, (0.72, 0.72, 0.72, 1), 'MULTIPLY'))
    _m._set(b, "Roughness", 0.9); _m._set(b, "Sheen Weight", 0.5)
    _m._bump(nt, b, _m._math(nt, 'ADD', h, _m._math(nt, 'MULTIPLY', n, 0.8)), 0.45, 0.006)
    return m


def bed19(M):
    """Photo 19 (s19f): king bed, head to the x XR wall with no headboard, box spring in a lavender-grey tailored
    skirt, the striped comforter, seven pillows; two oak-laminate bookcases on the rear wall (x 8.59..9.21 tall 0.90,
    9.24..10.49 low 0.76) filled with books; the bokeh canvas (x 9.57..10.32, z 4.09..4.89) and two framed Paris
    etchings (y 8.91..9.39 / 9.63..10.10); the gold quatrefoil stand with the porcelain lantern lamp, a stack of floor
    cushions, a burgundy leather ottoman at the front-left, a wall clock on the left wall, the closet door open."""
    x0, x1, y0, y1 = U.R['bed19']
    M.setdefault('stripe19', _stripe_comforter("ComforterStripes19"))
    M.setdefault('skirt_lav', _m.fabric("SkirtLavenderGrey", (0.17, 0.17, 0.24, 1), rough=0.85, sheen=0.5, weave=90))
    M.setdefault('pillow_lav', _m.fabric("PillowLavenderGrey", (0.36, 0.36, 0.46, 1), rough=0.85, sheen=0.5, weave=90))
    M.setdefault('pillow_butter', _m.fabric("PillowButter", (0.78, 0.66, 0.38, 1), rough=0.85, sheen=0.4, weave=90))
    M.setdefault('pillow_ivory', _m.fabric("PillowIvoryTrellis", (0.82, 0.81, 0.78, 1), rough=0.85, sheen=0.4, weave=90))
    bw, bl = 1.93, 2.03
    bx, by = x1 - bl / 2 - 0.02, 9.66                                          # 19: skirt near-foot corner (10.39, 8.69)
    rot = -math.pi / 2                                          # head (+Y local) toward +X
    fm = MB()
    sk.box_spring(fm, bx, by, rot, bw, bl, Z0 + 0.04, Z0 + 0.36, 0)
    sk.mattress(fm, bx, by, rot, bw, bl, Z0 + 0.36, Z0 + 0.62, 1)
    fm.build("Up_Bed19_Mattress", [M['sheet_white'], M['sheet_white']], coll=COLL, smooth=True)
    sk_ = MB()
    sk.bed_skirt(sk_, bx, by, rot, bw + 0.02, bl + 0.01, Z0 + 0.005, Z0 + 0.36, mi=0, pleat=0.3, depth=0.015, seed=19, z=0.0)
    sk_.build("Up_Bed19_Skirt", [M['skirt_lav']], coll=COLL, smooth=True)
    sk.draped_cover("Up_Bed19_Comforter", [M['stripe19']], bx, by, rot, Z0 + 0.64, bw + 0.04, bl, 0.30, 0.30, COLL,
                    thickness=0.06, r=0.09, z_floor=Z0, head_gap=0.30, folds=1.8, fold_amp=0.02, flare=0.03, corner_droop=0.8, seed=19)
    pm = MB()
    L = sk.F(pm, bx, by, rot, Z0)
    for i, (lx, ly, lz, w_, d_, t_, mi, pitch) in enumerate((
            (-0.50, bl / 2 - 0.12, 0.93, 0.92, 0.62, 0.18, 0, 1.25), (0.50, bl / 2 - 0.12, 0.93, 0.92, 0.62, 0.18, 0, 1.25),
            (-0.50, bl / 2 - 0.28, 0.86, 0.78, 0.52, 0.16, 2, 1.15), (0.50, bl / 2 - 0.28, 0.86, 0.78, 0.52, 0.16, 2, 1.15),
            (0.0, bl / 2 - 0.42, 0.80, 0.92, 0.34, 0.14, 1, 1.05), (-0.36, bl / 2 - 0.46, 0.80, 0.40, 0.40, 0.12, 0, 1.0),
            (0.30, bl / 2 - 0.50, 0.79, 0.40, 0.40, 0.12, 2, 1.0))):
        L.pillow(lx, ly, lz, w_, d_, t_, mi, pitch=pitch, seed=190 + i)
    pm.build("Up_Bed19_Pillows", [M['pillow_lav'], M['pillow_butter'], M['pillow_ivory']], coll=COLL, smooth=True)
    books = [M.setdefault(f'book_{i}', _m.new_mat(f"BookCover{i}", c, rough=0.55, coat=0.2)) for i, c in enumerate((
        (0.45, 0.10, 0.08, 1), (0.10, 0.16, 0.35, 1), (0.75, 0.72, 0.64, 1), (0.12, 0.30, 0.16, 1), (0.62, 0.45, 0.16, 1), (0.05, 0.05, 0.06, 1),
        (0.55, 0.55, 0.58, 1), (0.30, 0.45, 0.62, 1)))]
    for i, (xa, xb, h, n) in enumerate(((8.88, 9.46, 0.90, 2), (9.49, 10.68, 0.76, 1))):
        cm, bk = MB(), MB()
        zs = sk.bookcase(cm, (xa + xb) / 2, y1 - 0.16, 0.0, xb - xa, 0.30, h, shelves=n, mi=0, z=Z0)
        cm.build(f"Up_Bed19_Bookcase_{i}", [M['oak_lam']], coll=COLL)
        for j, zz in enumerate(zs):
            nsec = 1 if xb - xa < 0.8 else 2
            for k in range(nsec):
                sa = xa + 0.03 + k * (xb - xa - 0.06) / nsec
                sb = sa + (xb - xa - 0.06) / nsec - 0.02
                sk.book_row(bk, (sa + sb) / 2, y1 - 0.17, Z0 + zz, 0.0, sb - sa, 0.22, 0.26, list(range(len(books))), seed=1900 + i * 10 + j * 3 + k,
                            fill=0.85, stacks=1, mi_page=len(books))
        bk.build(f"Up_Bed19_Books_{i}", books + [M['paper']], coll=COLL)
    dec = MB()                                                                             # top-of-bookcase decor
    dec.lathe(9.02, y1 - 0.16, Z0 + 0.90, [(0, 0), (0.04, 0), (0.02, 0.05), (0.03, 0.12), (0.07, 0.2), (0.08, 0.26), (0, 0.26)], seg=16, mi=0)
    dec.lathe(9.30, y1 - 0.14, Z0 + 0.90, [(0, 0), (0.035, 0), (0.05, 0.06), (0.03, 0.14), (0.025, 0.17), (0, 0.17)], seg=12, mi=1)
    dec.lathe(10.52, y1 - 0.16, Z0 + 0.76, [(0, 0), (0.03, 0), (0.035, 0.08), (0.012, 0.14), (0.015, 0.16), (0, 0.16)], seg=12, mi=2)
    dec.cylinder(9.80, y1 - 0.16, Z0 + 0.76, Z0 + 0.79, 0.11, 0.13, seg=16, mi=3)                         # brass bowl
    dec.box(10.12, 10.28, y1 - 0.22, y1 - 0.10, Z0 + 0.76, Z0 + 0.82, 4)                                    # box + clock
    dec.cylinder(10.04, y1 - 0.18, Z0 + 0.76, Z0 + 0.82, 0.03, seg=12, mi=4)
    dec.build("Up_Bed19_Decor", [M['lamp_crystal'], M['dark_plastic'], M['porcelain'], M['gold_metal'], M['espresso']], coll=COLL, smooth=True)
    canvas_art(M, "Up_Bed19_Bokeh", 'X', 9.80, 10.53, y1, -1, 4.05, 4.74,
               tex3d('bokeh19', '19', ptx.rect_corners('X', 9.80, 10.53, y1 - 0.035, 4.05, 4.74, -1), (300, 300)))
    for (key, a0, a1, z0, z1) in (('paris_1', 9.74, 10.19, 4.20, 4.57), ('paris_2', 9.05, 9.51, 4.07, 4.46)):
        frame_art(M, f"Up_Bed19_{key}", 'Y', a0, a1, x1, -1, z0, z1, photo_tex(key), frame='champagne', fw=0.025, mat_w=0.045)
    # gold quatrefoil stand + lantern lamp beside the bed (-Y side, at the head)
    st = MB()
    cx, cy = 11.98, 8.40
    st.cylinder(cx, cy, Z0 + 0.60, Z0 + 0.63, 0.19, seg=32, mi=1)
    st.cylinder(cx, cy, Z0 + 0.585, Z0 + 0.60, 0.195, seg=32, mi=0)
    for k in range(3):
        a = 2 * math.pi * k / 3 + 0.4
        st.path_tube([(cx + 0.17 * math.cos(a), cy + 0.17 * math.sin(a), Z0 + 0.59), (cx + 0.06 * math.cos(a), cy + 0.06 * math.sin(a), Z0 + 0.35),
                      (cx + 0.10 * math.cos(a), cy + 0.10 * math.sin(a), Z0 + 0.22), (cx + 0.06 * math.cos(a), cy + 0.06 * math.sin(a), Z0 + 0.10),
                      (cx + 0.24 * math.cos(a), cy + 0.24 * math.sin(a), Z0)], 0.008, seg=6, mi=0)
    for zz in (Z0 + 0.25, Z0 + 0.45):
        for k in range(4):
            a = 2 * math.pi * k / 4
            st.path_tube([(cx + 0.03 * math.cos(a + t / 6 * 2 * math.pi), cy + 0.03 * math.sin(a + t / 6 * 2 * math.pi), zz + 0.04 * math.sin(t / 6 * math.pi)) for t in range(7)],
                         0.005, seg=5, mi=0)
    st.build("Up_Bed19_GoldStand", [M['gold_metal'], M['glass_clear']], coll=COLL, smooth=True)
    M.setdefault('porcelain_blue', _porcelain("PorcelainBlueWhite"))
    lm = MB()
    c = sk.lantern_lamp(lm, cx - 0.02, cy, Z0 + 0.63, 0, 1, 2)
    lm.build("Up_Bed19_Lantern", [M['espresso'], M['porcelain_blue'], M['gold_metal']], coll=COLL, smooth=True)
    add_light("L_Up_Bed19_Lamp_0", 'POINT', c, 6, color=(1.0, 0.86, 0.68), size=0.05, coll=LCOLL)
    # floor cushions (blue patterned top, orange, red, orange, a flat tan mat)
    M.setdefault('cush_blue', _m.fabric("FloorCushionIndigo", (0.08, 0.16, 0.38, 1), rough=0.8, sheen=0.4, weave=70))
    M.setdefault('cush_orange', _m.fabric("FloorCushionOrange", (0.72, 0.20, 0.03, 1), rough=0.8, sheen=0.4, weave=70))
    M.setdefault('cush_red', _m.fabric("FloorCushionRed", (0.55, 0.05, 0.04, 1), rough=0.8, sheen=0.4, weave=70))
    M.setdefault('cush_tan', _m.fabric("FloorCushionTan", (0.55, 0.47, 0.36, 1), rough=0.8, sheen=0.4, weave=70))
    fc = MB()
    L = sk.F(fc, 11.72, 7.55, 0.12, Z0)
    zz = 0.0
    for i, (mi, h, dx) in enumerate(((3, 0.035, 0.0), (1, 0.06, 0.02), (2, 0.05, -0.02), (1, 0.06, 0.03), (0, 0.08, 0.0))):
        L.rbox(-0.50 + dx, 0.50 + dx, -0.33, 0.33, zz, zz + h, r=min(0.025, h / 2 - 0.002), mi=mi, puff=0.35)
        zz += h * 0.95
    fc.build("Up_Bed19_FloorCushions", [M['cush_blue'], M['cush_orange'], M['cush_red'], M['cush_tan']], coll=COLL, smooth=True)
    M.setdefault('leather_burgundy', _m.leather("LeatherBurgundy", base=(0.20, 0.035, 0.03, 1), rough=0.35))
    ot = MB()
    L = sk.F(ot, 8.93, 8.50, 0.0, Z0)                                        # photo 19: its top-right corner at (9.13, 8.72)
    L.rbox(-0.19, 0.19, -0.28, 0.28, 0.08, 0.44, r=0.06, mi=0, puff=0.3)
    for sx in (-1, 1):
        for sy in (-1, 1):
            L.box(sx * 0.15 - 0.02, sx * 0.15 + 0.02, sy * 0.24 - 0.02, sy * 0.24 + 0.02, 0.0, 0.08, 1)
    ot.build("Up_Bed19_Ottoman", [M['leather_burgundy'], M['espresso']], coll=COLL, smooth=True)
    from archviz.furnish import wall_clock, register
    ck = MB()
    wall_clock(ck, 11.25, x0, 4.35, r=0.13, along='Y', face=+1, mi_rim=0, mi_face=1, mi_ink=0)
    ck.build("Up_Bed19_Clock", [M['black_paint'], M['paper']], coll=COLL)
    rg = MB()
    register(rg, 8.95, 7.25, Z1, w=0.30, d=0.14, along='X', mi=0, mi_dark=1)
    rg.build("Up_Bed19_Register", [M['porcelain'], M['dark_plastic']], coll=COLL)
    ceiling_fan(M, "Up_Bed19_Fan", 10.54, 9.445, Z1, blade=0.30, blades='fan_blade_white', downrod=0.08)


def _porcelain(name):
    """Blue-and-white porcelain (the lantern lamp, photo 19): white glaze with cobalt voronoi motifs."""
    m, nt, b = _m._new(name)
    v = _m._voronoi(nt, _m._coords(nt), scale=35.0, rand=0.6)
    spot = _m._math(nt, 'LESS_THAN', v.outputs["Distance"], 0.25)
    nt.links.new(b.inputs["Base Color"], _m._mixrgb(nt, spot, (0.86, 0.87, 0.88, 1), (0.05, 0.12, 0.45, 1)))
    _m._set(b, "Roughness", 0.1); _m._set(b, "Coat Weight", 0.8)
    return m


def bed20(M):
    """Photo 20 (s20h): queen bed head to the x 8.60 wall (white matelasse coverlet, textured white shams, grey
    pillows, a white skirt), a painted round side table with red roses at the near side, the black desk with a laser
    printer and the black leather task chair on the -X wall, two framed panoramas and a carved plaque on the front
    wall, a tall mirror panel with three beaded pieces, honey faux-wood blinds (fully down, open)."""
    x0, x1, y0, y1 = U.R['bed20']
    M.setdefault('matelasse', _matelasse("CoverletMatelasse"))
    M.setdefault('sham_white', _matelasse("ShamWhiteTextured", base=(0.82, 0.82, 0.82, 1)))
    M.setdefault('pillow_greyknit', _m.fabric("PillowGreyKnit", (0.24, 0.25, 0.27, 1), rough=0.9, sheen=0.3, weave=60, bump=0.4))
    bw, bl = 1.52, 2.03
    dy = 0.0                                                                   # positions below: INT_CAM's p20 back-projections
    bx, by = x1 - bl / 2 - 0.02, 2.42                                         # photo 20: skirt near side y 3.2, foot x 6.38
    rot = -math.pi / 2
    fm = MB()
    sk.box_spring(fm, bx, by, rot, bw, bl, Z0 + 0.14, Z0 + 0.40, 0)
    sk.mattress(fm, bx, by, rot, bw, bl, Z0 + 0.40, Z0 + 0.64, 0)
    fm.build("Up_Bed20_Mattress", [M['sheet_white']], coll=COLL, smooth=True)
    sk_ = MB()
    sk.bed_skirt(sk_, bx, by, rot, bw + 0.02, bl + 0.01, Z0 + 0.02, Z0 + 0.40, mi=0, pleat=0.22, depth=0.012, seed=20, z=0.0)
    sk_.build("Up_Bed20_Skirt", [M['sheet_white']], coll=COLL, smooth=True)
    sk.draped_cover("Up_Bed20_Coverlet", [M['matelasse']], bx, by, rot, Z0 + 0.655, bw + 0.02, bl, 0.36, 0.34, COLL,
                    thickness=0.02, r=0.05, z_floor=Z0, head_gap=0.32, folds=2.5, fold_amp=0.015, flare=0.02, corner_droop=0.85, seed=20)
    pm = MB()
    L = sk.F(pm, bx, by, rot, Z0)
    for i, (lx, ly, lz, w_, d_, t_, mi, pitch) in enumerate((
            (-0.37, bl / 2 - 0.10, 0.95, 0.66, 0.50, 0.18, 1, 1.25), (0.37, bl / 2 - 0.10, 0.95, 0.66, 0.50, 0.18, 1, 1.25),
            (-0.37, bl / 2 - 0.26, 0.88, 0.62, 0.46, 0.18, 0, 1.1), (0.30, bl / 2 - 0.28, 0.87, 0.62, 0.46, 0.18, 0, 1.0))):
        L.pillow(lx, ly, lz, w_, d_, t_, mi, pitch=pitch, seed=200 + i)
    pm.build("Up_Bed20_Pillows", [M['sham_white'], M['pillow_greyknit']], coll=COLL, smooth=True)
    # painted round side table (floral top, gilt turned pedestal) + red roses
    M.setdefault('painted_top', _m.art_abstract("SideTableFloral", bg=(0.72, 0.66, 0.52, 1), fg=(0.35, 0.30, 0.26, 1), scale=12.0, thresh=0.58))
    t_ = MB()
    tx, ty = 8.15, 3.72
    t_.cylinder(tx, ty, Z0 + 0.60, Z0 + 0.625, 0.25, seg=40, mi=0)
    t_.lathe(tx, ty, Z0, [(0.0, 0.0), (0.16, 0.0), (0.17, 0.03), (0.05, 0.08), (0.035, 0.20), (0.05, 0.28), (0.03, 0.42), (0.045, 0.52), (0.08, 0.60), (0.0, 0.60)],
             seg=20, mi=1)
    t_.build("Up_Bed20_SideTable", [M['painted_top'], M['gold_metal']], coll=COLL, smooth=True)
    bouquet(M, "Up_Bed20_Roses", tx + 0.08, ty - 0.12, Z0 + 0.625, kind='rose', r=0.09, seed=20, stem_h=0.22)
    # desk + printer + chair
    dk = MB()
    sk.desk(dk, x0 + 0.30, 5.02, math.pi / 2, 1.20, 0.60, h=0.76, mi=0, modesty=True, z=Z0)           # 20: along the -X wall, near end y 4.42
    dk.build("Up_Bed20_Desk", [M['black_paint']], coll=COLL)
    pr = MB()
    L = sk.F(pr, x0 + 0.30, 4.70, math.pi / 2, Z0 + 0.76)
    L.rbox(-0.21, 0.21, -0.19, 0.19, 0.0, 0.26, r=0.02, mi=0)
    L.box(-0.18, 0.18, -0.20, -0.19, 0.16, 0.22, 1)
    pr.build("Up_Bed20_Printer", [M['printer_grey'], M['dark_plastic']], coll=COLL, smooth=True)
    oc = MB()
    sk.office_chair(oc, 6.08, 4.15, -math.pi / 2 + 0.6, mi=0, mi_metal=1, z=Z0)
    oc.build("Up_Bed20_Chair", [M['vinyl_black'], M['black_paint']], coll=COLL, smooth=True)
    # front-wall art and the mirror panel on the -X wall
    frame_art(M, "Up_Bed20_Pano_0", 'X', 8.12, 8.40, U.YF, +1, 4.45, 4.58, photo_tex('pano_20a'), frame='frame_black', fw=0.015)
    frame_art(M, "Up_Bed20_Pano_1", 'X', 7.99, 8.26, U.YF, +1, 4.17, 4.31, photo_tex('pano_20b'), frame='frame_black', fw=0.015)
    ptx.uv_quad_mesh("Up_Bed20_Plaque", ptx.rect_corners('X', 6.00, 6.30, U.YF + 0.015, 4.37, 4.64, +1), photo_tex('plaque_20'),
                     coll=COLL, thickness=0.012, edge_mat=M['cherry'])
    mp = MB()
    mp.box(x0, x0 + 0.02, 2.74, 3.05, 3.23, 4.50, 0)                                    # 20: y 2.74..3.05, z 3.23..4.50
    mp.box(x0 + 0.02, x0 + 0.024, 2.755, 3.035, 3.25, 4.48, 1)
    for zz in (4.26, 3.88, 3.45):
        mp.rbox(x0 + 0.024, x0 + 0.04, 2.81, 2.98, zz - 0.11, zz + 0.11, r=0.006, mi=2)
    mp.build("Up_Bed20_MirrorArt", [M['mat_board'], M['mirror'], M['art_bead'] if 'art_bead' in M else M['cherry']], coll=COLL)
    ceiling_fan(M, "Up_Bed20_Fan", 6.905, 3.127, Z1, blade=0.30, blades='fan_blade_white', downrod=0.06)


def bed21(M):
    """Photo 21 (s21f): queen bed with an espresso cube-panel headboard (to 1.56 m) and footboard, head to the
    x XR wall (y 2.2..3.7), the paisley comforter and red / ivory / brocade pillows; the kilim runner beside the
    bed; the glass console with a gold X base against the headboard wall; the gold etagere at the -X wall; the island
    map canvas (y 3.63..4.33) and the yellow still life (x 8.91..9.49); sheers tied back on a black rod (z 5.17) over
    white blinds."""
    x0, x1, y0, y1 = U.R['bed21']
    bw, bl = 1.52, 2.03
    bx, by = x1 - bl / 2 - 0.09, 2.80                                         # headboard y 1.95..3.64, foot x 10.21
    rot = -math.pi / 2
    fm = MB()
    sk.cube_panel_bed(fm, bx, by, rot, bw, bl, mi=0, head_h=1.44, foot_h=0.76, z=Z0)
    M.setdefault('espresso_dark', _m.wood("EspressoDark", light=(0.035, 0.024, 0.02, 1), dark=(0.018, 0.012, 0.01, 1), grain_axis='X', rough=0.4, coat=0.35))
    fm.build("Up_Bed21_Bed", [M['espresso_dark']], coll=COLL)
    mm = MB()
    sk.mattress(mm, bx, by, rot, bw, bl, Z0 + 0.36, Z0 + 0.64, 0)
    mm.build("Up_Bed21_Mattress", [M['sheet_white']], coll=COLL, smooth=True)
    tex = tex3d('paisley21', '21', [(11.4, 2.2, Z0 + 0.66), (11.4, 3.4, Z0 + 0.66), (10.4, 3.4, Z0 + 0.66), (10.4, 2.2, Z0 + 0.66)], (360, 330),
                flatten=0.25, tile=True, gain=0.62)
    _uv_repeat(tex, (1.0 / 1.2, 1.0 / 1.1))
    sk.draped_cover("Up_Bed21_Comforter", [tex], bx, by, rot, Z0 + 0.66, bw + 0.02, bl - 0.02, 0.36, 0.20, COLL,
                    thickness=0.05, r=0.08, z_floor=Z0, head_gap=0.40, folds=2.0, fold_amp=0.02, flare=0.02, corner_droop=0.9, seed=21)
    M.setdefault('pillow_red21', _m.fabric("PillowTomatoRed", (0.48, 0.035, 0.03, 1), rough=0.55, sheen=0.8, weave=120))
    M.setdefault('pillow_brocade', _m.art_abstract("PillowBrocade", bg=(0.36, 0.17, 0.10, 1), fg=(0.72, 0.55, 0.40, 1), scale=18.0, thresh=0.55))
    pm = MB()
    L = sk.F(pm, bx, by, rot, Z0)
    for i, (lx, ly, lz, w_, d_, t_, mi, pitch) in enumerate((
            (-0.40, bl / 2 - 0.14, 0.96, 0.66, 0.50, 0.17, 0, 1.2), (0.40, bl / 2 - 0.14, 0.96, 0.66, 0.50, 0.17, 0, 1.2),
            (-0.36, bl / 2 - 0.26, 0.90, 0.62, 0.46, 0.17, 1, 1.1), (0.36, bl / 2 - 0.26, 0.90, 0.62, 0.46, 0.17, 1, 1.1),
            (-0.18, bl / 2 - 0.38, 0.85, 0.44, 0.44, 0.13, 2, 1.0), (0.20, bl / 2 - 0.40, 0.84, 0.40, 0.40, 0.13, 1, 1.0),
            (0.02, bl / 2 - 0.50, 0.80, 0.40, 0.28, 0.10, 2, 0.9))):
        L.pillow(lx, ly, lz, w_, d_, t_, mi, pitch=pitch, seed=210 + i)
    pm.build("Up_Bed21_Pillows", [M['pillow_red21'], M['sheet_white'], M['pillow_brocade']], coll=COLL, smooth=True)
    rc = [(10.21, 4.60, Z0 + 0.009), (11.70, 4.61, Z0 + 0.009), (11.69, 3.70, Z0 + 0.009), (10.21, 3.70, Z0 + 0.009)]
    ptx.uv_quad_mesh("Up_Bed21_Rug", rc, tex3d('kilim21', '21', rc, (450, 280)), coll=COLL, thickness=0.008, edge_mat=M['cush_tan'] if 'cush_tan' in M else None)
    # glass console with a gold X base (legs at y 3.3..4.5 on the headboard wall)
    cn = MB()
    cx0, cx1, cy0, cy1 = 11.74, 12.30, 3.70, 4.78
    cn.box(cx0, cx1, cy0, cy1, Z0 + 0.74, Z0 + 0.752, 0)
    for xx in (cx0 + 0.03, cx1 - 0.03):
        cn.tube((xx, cy0 + 0.02, Z0), (xx, cy0 + 0.02, Z0 + 0.73), 0.012, 0.012, seg=8, mi=1)
        cn.tube((xx, cy1 - 0.02, Z0), (xx, cy1 - 0.02, Z0 + 0.73), 0.012, 0.012, seg=8, mi=1)
        cn.tube((xx, cy0 + 0.02, Z0 + 0.03), (xx, cy1 - 0.02, Z0 + 0.70), 0.012, 0.012, seg=8, mi=1)
        cn.tube((xx, cy1 - 0.02, Z0 + 0.03), (xx, cy0 + 0.02, Z0 + 0.70), 0.012, 0.012, seg=8, mi=1)
    cn.tube((cx0 + 0.03, cy0 + 0.02, Z0 + 0.72), (cx1 - 0.03, cy0 + 0.02, Z0 + 0.72), 0.01, 0.01, seg=6, mi=1)
    cn.tube((cx0 + 0.03, cy1 - 0.02, Z0 + 0.72), (cx1 - 0.03, cy1 - 0.02, Z0 + 0.72), 0.01, 0.01, seg=6, mi=1)
    cn.build("Up_Bed21_Console", [M['glass_clear'], M['gold_metal']], coll=COLL)
    bouquet(M, "Up_Bed21_Flowers", 12.02, 4.55, Z0 + 0.752, kind='hydrangea', r=0.07, seed=21, stem_h=0.14)
    # gold etagere at the -X wall (y 1.9..2.6)
    et = MB()
    ex0, ex1, ey0, ey1 = 8.64, 9.06, 2.05, 2.75
    for (xx, yy) in ((ex0 + 0.02, ey0 + 0.02), (ex1 - 0.02, ey0 + 0.02), (ex0 + 0.02, ey1 - 0.02), (ex1 - 0.02, ey1 - 0.02)):
        et.tube((xx, yy, Z0), (xx, yy, Z0 + 0.80), 0.011, 0.011, seg=8, mi=1)
    for zz in (Z0 + 0.30, Z0 + 0.79):
        et.box(ex0, ex1, ey0, ey1, zz, zz + 0.01, 0)
    for k in range(4):
        yy = ey0 + 0.07 + k * (ey1 - ey0 - 0.14) / 3
        et.path_tube([(ex1 - 0.02, yy - 0.08, Z0 + 0.02), (ex1 - 0.02, yy, Z0 + 0.25), (ex1 - 0.02, yy + 0.08, Z0 + 0.02)], 0.006, seg=5, mi=1)
    et.build("Up_Bed21_Etagere", [M['glass_clear'], M['gold_metal']], coll=COLL)
    ed = MB()
    ed.box(8.68, 9.00, 2.25, 2.55, Z0 + 0.80, Z0 + 0.83, 0)                                   # books / tray + decor
    ed.lathe(8.84, 2.40, Z0 + 0.83, [(0, 0), (0.09, 0), (0.1, 0.07), (0.05, 0.1), (0, 0.1)], seg=16, mi=1)
    ed.build("Up_Bed21_EtagereDecor", [M['paper'], M['porcelain_blue'] if 'porcelain_blue' in M else M['porcelain']], coll=COLL, smooth=True)
    canvas_art(M, "Up_Bed21_Map", 'Y', 3.976, 4.674, x1, -1, 4.122, 4.639, photo_tex('map_21'))
    frame_art(M, "Up_Bed21_StillLife", 'X', 9.06, 9.633, y0, +1, 4.173, 4.645, photo_tex('still_21'), frame='frame_black', fw=0.03)
    # sheers on a black rod over the double window
    from archviz.finishes import voile
    M.setdefault('sheer_leaf', voile("SheerEmbroideredLeaf", color=(0.90, 0.80, 0.62, 1), alpha=0.6))
    rd = MB()
    yr_ = y0 + 0.10
    zr = 4.97                                                                  # INT_CAM 21: rod ends (9.62 / 11.65, z 4.97)
    rd.tube((9.62, yr_, zr), (11.65, yr_, zr), 0.009, 0.009, seg=8, mi=0)
    for xx in (9.60, 11.67):
        rd.sphere((xx, yr_, zr), 0.02, seg=10, rings=6, mi=0)
    for xx in (9.72, 11.55):
        rd.tube((xx, y0, zr + 0.02), (xx, yr_, zr + 0.01), 0.006, 0.006, seg=5, mi=0)
    rd.build("Up_Bed21_Rod", [M['black_paint']], coll=COLL)
    sh = MB()
    for (ac, lean, zb) in ((11.05, 1, Z0 + 0.55), (10.22, -1, Z0 + 0.18)):   # each panel gathered on the rod, tied at ~1.2 m
        sk.sheer_tieback(sh, 'X', ac, y0 + 0.10, +1, zr - 0.03, zb, w=0.46, gather_z=Z0 + 1.20, lean=lean * 0.15, folds=6, mi=0, seed=21 + lean,
                         pinch=0.30, flare=0.60)
    sh.build("Up_Bed21_Sheers", [M['sheer_leaf']], coll=COLL, smooth=True)
    ceiling_fan(M, "Up_Bed21_Fan", 10.58, 3.22, Z1, blade=0.30, blades='fan_blade_white', downrod=0.06)


def _uv_repeat(mat, rep):
    """Scale a photo_material's mapping (a tiling photo texture on metre UVs)."""
    for n in mat.node_tree.nodes:
        if n.type == 'MAPPING':
            n.inputs['Scale'].default_value = (rep[0], rep[1], 1.0)
        if n.type == 'TEX_IMAGE':
            n.extension = 'REPEAT'


# ================================================================ rooms
def master(M):
    """Photos 16/17 (joint solve s1617, 3.7 / 4.3 px): queen platform bed, headboard y 7.84..9.55 (top 1.28 m) on the
    x 0.15 wall; the abstract in a gold beaded frame above it (y 8.37..8.91, z 4.50..5.16); black two-drawer
    nightstands with an open shelf and crystal lamps; the blue-grey track-arm sofa between the rear windows under three
    crewel embroideries; the charcoal power recliner by the left window; the grey Louis-Philippe dresser on the +X
    wall; a small cherry chest in the front-left corner; the folding recumbent bike on the front wall."""
    x0, x1, y0, y1 = U.R['master']
    bw, bl = 1.28, 1.95                                           # full-size: headboard y 8.58..9.98 (1.40 wide) in 16 + 17
    by = 9.28
    bx = x0 + 0.08 + bl / 2
    rot = math.pi / 2                                             # head (+Y local) toward -X
    fm = MB()
    sk.platform_bed(fm, bx, by, rot, bw, bl, mi=0, head_h=1.15, head_t=0.05, z=Z0)
    fm.build("Up_Master_Bed", [M['espresso']], coll=COLL)
    mm = MB()
    sk.mattress(mm, bx, by, rot, bw, bl, Z0 + 0.34, Z0 + 0.60, 0)
    mm.build("Up_Master_Mattress", [M['sheet_white']], coll=COLL, smooth=True)
    sk.draped_cover("Up_Master_Comforter", [M['comforter_vine']], bx, by, rot, Z0 + 0.62, bw + 0.02, bl, 0.44, 0.42, COLL,
                    thickness=0.05, r=0.08, z_floor=Z0, head_gap=-0.02, folds=2.0, fold_amp=0.022, flare=0.05, corner_droop=0.92,
                    lumps=[(0.0, bl / 2 - 0.30, 0.62, 0.24, 0.15)], seed=16)                       # pillows under the comforter (16, 17)
    for i, yy in enumerate((8.33, 10.26)):
        ns = MB()
        sk.chest(ns, x0 + 0.21, yy, math.pi / 2, 0.48, 0.40, 0.64, mi=0, mi_pull=1, drawers=2, feet='square', pulls='knob', shelf=True,
                 plinth=0.06, bevel_top=False, top_over=0.01, z=Z0)
        ns.box(x0 + 0.05, x0 + 0.42, yy - 0.24, yy + 0.24, Z0 + 0.645, Z0 + 0.652, 2)                   # white marble tray
        ns.build(f"Up_Master_Nightstand_{i}", [M['black_paint'], M['silver'], M['porcelain']], coll=COLL)
        lp = MB()
        c = sk.crystal_lamp(lp, x0 + 0.25, yy + (-0.04 if i == 0 else 0.04), Z0 + 0.652, 0, 1, 2, h=0.66, shade_r=0.15, shade_h=0.21)
        lp.build(f"Up_Master_Lamp_{i}", [M['silver'], M['lamp_crystal'], M['shade_white']], coll=COLL, smooth=True)
        add_light(f"L_Up_Master_Lamp_{i}", 'POINT', c, 8, color=(1.0, 0.86, 0.68), size=0.05, coll=LCOLL)
        bk = MB()                                                                                        # clutter on the open shelf
        sk.book_row(bk, x0 + 0.22, yy, Z0 + 0.10, math.pi / 2, 0.40, 0.26, 0.16, [0, 1, 2], seed=30 + i, stacks=2)
        bk.build(f"Up_Master_NSShelf_{i}", [M['paper'], M['cardboard'], M['clothes_navy'] if 'clothes_navy' in M else M['dark_plastic']], coll=COLL)
    # clock + flowers on the front nightstand (photo 16), a small plant ball on the rear one (17)
    ck = MB()
    ck.box(x0 + 0.20, x0 + 0.26, 8.40, 8.52, Z0 + 0.652, Z0 + 0.70, 0)
    ck.build("Up_Master_Clock", [M['dark_plastic']], coll=COLL)
    bouquet(M, "Up_Master_Flowers", x0 + 0.24, 8.16, Z0 + 0.66, kind='mauve', r=0.07, seed=16)
    bouquet(M, "Up_Master_Hydrangea17", x0 + 0.30, 10.02, Z0 + 0.66, kind='hydrangea', r=0.06, seed=17)
    frame_art(M, "Up_Master_ArtBed", 'Y', 9.03, 9.44, x0, +1, 4.32, 4.90, photo_tex('art_bed'), frame='frame_gold', fw=0.03, profile='step')
    # sofa + pillows between the rear windows (photo 16: arms at u 880 / 1250 -> x ~1.55 .. 3.60)
    so, pil = MB(), MB()
    sx_, sy_ = 2.43, y1 - 0.40                                   # 16: arms x 1.22 .. 3.65, front leg y 11.2
    sk.track_sofa(so, pil, sx_, sy_, 0.0, w=2.40, d=0.80, mi=0, mi_leg=1, mi_button=2, seat_h=0.46, back_h=0.86, arm_h=0.60, z=Z0)
    so.build("Up_Master_Sofa", [M['sofa_blue'], M['espresso'], M['sofa_blue']], coll=COLL, smooth=True)
    L = sk.F(pil, sx_, sy_, 0.0, Z0)
    for i, (lx, w_) in enumerate(((-0.82, 0.50), (0.0, 0.40), (0.82, 0.50))):
        L.pillow(lx, 0.12, 0.72, w_, w_, 0.15, 0, pitch=1.25, lrot=(0.08 if i == 0 else -0.08 if i == 2 else 0.0), seed=160 + i)
    bird = ptx.photo_material("Photo_birds_16", ptx.rectify(os.path.join(PHOTOS, '16.jpg'), PHOTO_TEX['birds_16'][1], (160, 150), "PhotoTex_birds_16",
                              tile=True, gain=1.08), rough=0.8, sheen=0.3, src='Object', plane='XZ', repeat=(1 / 0.42, 1 / 0.40))
    pil.build("Up_Master_BirdPillows", [bird], coll=COLL, smooth=True)
    # embroideries: back-projected through INT_CAM's 16 camera (champagne stepped frames)
    for (key, a0, a1, z0, z1) in (('emb_1', 1.56, 2.08, 4.17, 4.57), ('emb_2', 2.30, 2.72, 4.16, 4.64), ('emb_3', 2.95, 3.47, 4.16, 4.55)):
        frame_art(M, f"Up_Master_{key}", 'X', a0, a1, y1, -1, z0, z1, photo_tex(key), frame='champagne', fw=0.045, profile='step')
    rc = MB()
    sk.recliner(rc, 0.95, y1 - 0.62, math.pi + 0.35, w=0.95, d=0.98, mi=0, z=Z0)
    rc.build("Up_Master_Recliner", [M['recliner_grey']], coll=COLL, smooth=True)
    st = MB()                                                                                            # small photo frame on a side table
    st.box(1.30, 1.58, y1 - 0.40, y1 - 0.12, Z0, Z0 + 0.52, 0)
    st.box(1.36, 1.52, y1 - 0.30, y1 - 0.28, Z0 + 0.52, Z0 + 0.66, 1)
    st.build("Up_Master_SideTable", [M['black_paint'], M['frame_silver'] if 'frame_silver' in M else M['silver']], coll=COLL)
    dr = MB()
    sk.chest(dr, x1 - 0.30, 8.65, -math.pi / 2, 1.40, 0.50, 0.88, mi=0, mi_pull=1, drawers=4, feet='bun', pulls='bail', split=True,
             drawer_heights=[0.8, 1.0, 1.0, 1.1], z=Z0)
    dr.build("Up_Master_Dresser", [M['grey_paint'], M['silver']], coll=COLL)
    ch = MB()
    sk.chest(ch, 0.47, y0 + 0.21, math.pi, 0.60, 0.40, 1.02, mi=0, mi_pull=1, drawers=4, feet='plinth', pulls='bar', plinth=0.05, z=Z0)   # 17
    ch.build("Up_Master_CherryChest", [M['cherry'], M['silver']], coll=COLL)
    bk = MB()
    sk.recumbent_bike(bk, 2.62, y0 + 0.26, math.pi / 2, 0, 1, 2, z=Z0)                   # 17: pedals toward +X, front foot (3.05, 6.75)
    bk.build("Up_Master_Bike", [M['bike_frame'], M['vinyl_black'], M['bike_white']], coll=COLL, smooth=True)
    ceiling_fan(M, "Up_Master_Fan", 2.416, 9.311, U.Z_SOFFIT + U.TRAY, blade=0.52, blades='fan_blade_light', downrod=0.10)    # 16+17 canopy
    sd = MB()
    smoke_detector(sd, 2.9, y0 + 0.9, Z1)
    sd.build("Up_Master_Smoke", [M['porcelain']], coll=COLL)


# ================================================================ baths
def vanity(M, name, along, a0, a1, b_wall, side, z=Z0, sinks=2, depth=0.56, h=0.81, drawers_end=True):
    """Honey-maple builder vanity (photos 18, 23): a drawer bank at the toilet end (three drawers), sink bases with
    raised-panel doors and a false drawer front each, a bank of two drawers between the sinks; a one-piece cultured-
    marble top with integral oval bowls, a 10 cm backsplash; satin-nickel single-lever faucets and D pulls."""
    from archviz.furnish import raised_panel_door, drawer_front, bar_pull
    f = Face(along, b_wall, side)
    mb = MB()
    L = a1 - a0
    f.box(mb, a0, a1, 0.0, depth - 0.02, z + 0.09, z + h - 0.035, 0)                     # carcass
    f.box(mb, a0 + 0.02, a1 - 0.02, 0.0, depth - 0.07, z, z + 0.09, 4)                   # toe kick
    fr = MB()
    ff = Face(along, b_wall + side * (depth - 0.02), side)
    # column layout: [drawer bank 0.38] [sink base] [drawer bank 0.40] [sink base] ...
    cols = []
    a = a0 + 0.012
    bank = 0.38
    sink_w = (L - 0.024 - bank * (2 if sinks == 2 else 1)) / sinks
    order = (['bank', 'sink', 'bank', 'sink'] if sinks == 2 else ['bank', 'sink'])
    for kind in order:
        w_ = bank if kind == 'bank' else sink_w
        cols.append((kind, a, a + w_))
        a += w_
    zt = z + h - 0.045
    for kind, c0, c1 in cols:
        if kind == 'bank':
            n = 3
            hs = [0.20, 0.23, 0.23]
            zz = zt
            for k in range(n):
                z1_ = zz; z0_ = zz - hs[k] * (zt - z - 0.10) / sum(hs)
                drawer_front(ff, fr, c0 + 0.003, c1 - 0.003, z0_ + 0.003, z1_ - 0.003, mi=0)
                bar_pull(ff, fr, (c0 + c1) / 2, (z0_ + z1_) / 2 + 0.02, length=0.096, mi=1)
                zz = z0_
        else:
            drawer_front(ff, fr, c0 + 0.003, c1 - 0.003, zt - 0.15, zt - 0.003, mi=0)            # false drawer front
            bar_pull(ff, fr, (c0 + c1) / 2, zt - 0.07, length=0.128, mi=1)
            if c1 - c0 > 0.55:
                am = (c0 + c1) / 2
                for (d0, d1, ka) in ((c0, am, am - 0.035), (am, c1, am + 0.035)):
                    raised_panel_door(ff, fr, d0 + 0.004, d1 - 0.004, z + 0.10, zt - 0.16, style='square', mi=0)
                    bar_pull(ff, fr, ka, zt - 0.26, length=0.096, vertical=True, mi=1)
            else:
                raised_panel_door(ff, fr, c0 + 0.004, c1 - 0.004, z + 0.10, zt - 0.16, style='square', mi=0)
                bar_pull(ff, fr, c1 - 0.05, zt - 0.26, length=0.096, vertical=True, mi=1)
    fr.build(name + "_Fronts", [M['maple_cab'], M['brushed']], coll=COLL)
    top = MB()
    f.box(top, a0 - 0.012, a1 + 0.012, -0.001, depth + 0.02, z + h - 0.035, z + h, 0)            # counter
    f.box(top, a0 - 0.012, a1 + 0.012, -0.001, 0.018, z + h, z + h + 0.10, 0)                   # backsplash
    for kind, c0, c1 in cols:
        if kind != 'sink':
            continue
        am = (c0 + c1) / 2
        p = f.p(am, depth * 0.55, z + h - 0.004)
        top.lathe(p[0], p[1], z + h - 0.15, [(0.0, 0.0), (0.13, 0.02), (0.20, 0.08), (0.215, 0.14), (0.225, 0.146), (0.0, 0.146)], seg=32, mi=1,
                  ry=0.72 if along == 'X' else 1.39)
        q = f.p(am, 0.075, z + h)
        top.cylinder(q[0], q[1], z + h, z + h + 0.012, 0.03, seg=16, mi=2)                         # faucet deck plate
        if along == 'X':
            top.box(q[0] - 0.08, q[0] + 0.08, q[1] - 0.025, q[1] + 0.025, z + h, z + h + 0.006, 2)
        else:
            top.box(q[0] - 0.025, q[0] + 0.025, q[1] - 0.08, q[1] + 0.08, z + h, z + h + 0.006, 2)
        top.cylinder(q[0], q[1], z + h, z + h + 0.20, 0.018, 0.015, seg=12, mi=2)
        r = f.p(am, 0.19, z + h + 0.175)
        top.tube((q[0], q[1], z + h + 0.19), r, 0.012, 0.010, seg=10, mi=2)
        top.tube(f.p(am, 0.02, z + h + 0.21), f.p(am, 0.09, z + h + 0.20), 0.007, 0.006, seg=6, mi=2)      # lever
    top.build(name, [M['marble_top'], M['porcelain'], M['brushed']], coll=COLL, smooth=False)
    carc = mb.build(name + "_Carcass", [M['maple_cab'], M['maple_cab'], M['maple_cab'], M['maple_cab'], M['espresso']], coll=COLL)
    return [c for c in cols if c[0] == 'sink'], carc


def toilet(M, name, x, y, rot, z=Z0, lid_up=False):
    """Two-piece elongated toilet (photos 18, 23), back to the wall at (x, y), facing along rot (0 = +Y)."""
    mb = MB()
    L = sk.F(mb, x, y, rot, z)
    L.rbox(-0.25, 0.25, 0.02, 0.21, 0.40, 0.76, r=0.03, mi=0)                       # tank
    L.rbox(-0.26, 0.26, 0.01, 0.225, 0.76, 0.795, r=0.012, mi=0)                    # lid
    L.lathe(0.0, 0.46, 0.0, [(0.0, 0.0), (0.12, 0.0), (0.11, 0.10), (0.15, 0.22), (0.19, 0.35), (0.185, 0.38), (0.0, 0.38)], seg=28, mi=0, ry=1.38)
    L.rbox(-0.08, 0.08, 0.18, 0.34, 0.0, 0.30, r=0.05, mi=0)                        # trapway
    L.lathe(0.0, 0.47, 0.38, [(0.0, 0.0), (0.19, 0.0), (0.195, 0.025), (0.0, 0.025)], seg=28, mi=0, ry=1.4)       # seat
    if not lid_up:
        L.lathe(0.0, 0.47, 0.405, [(0.0, 0.0), (0.185, 0.0), (0.18, 0.02), (0.0, 0.03)], seg=28, mi=0, ry=1.4)    # lid down
    L.box(-0.22, -0.14, 0.205, 0.225, 0.68, 0.70, 1)                               # trip lever
    L.tube((0.12, 0.03, 0.18), (0.12, 0.0, 0.10), 0.006, 0.006, seg=6, mi=1)        # supply
    mb.build(name, [M['porcelain'], M['chrome']], coll=COLL, smooth=True)


def alcove_tub(M, name, x0, x1, y0, y1, curtain_mat, rod_x, z=Z0, gathered=0.0):
    """Built-in 60" tub/shower (photos 18, 23) along a Y wall: an enamelled shell with an apron and rim, a tiled...
    painted surround, a chrome rod and a fabric curtain (photo texture) hanging just inside the rim."""
    mb = MB()
    t = 0.07
    mb.box(x0, x1, y0, y1, z, z + 0.08, 0)
    for (a, b_, c, d) in ((x0, x0 + t, y0, y1), (x1 - t, x1, y0, y1), (x0 + t, x1 - t, y0, y0 + t), (x0 + t, x1 - t, y1 - t, y1)):
        mb.box(a, b_, c, d, z, z + 0.46, 0)
    mb.build(name, [M['porcelain']], coll=COLL)
    rod = MB()
    rod.tube((rod_x, y0 + 0.01, z + 1.98), (rod_x, y1 - 0.01, z + 1.98), 0.013, 0.013, seg=10, mi=0)
    for yy in (y0 + 0.012, y1 - 0.012):
        rod.box(rod_x - 0.03, rod_x + 0.03, yy - 0.01, yy + 0.01, z + 1.95, z + 2.01, 0)
    rod.build(name + "_Rod", [M['chrome']], coll=COLL)
    cm = MB()
    sk.shower_curtain(cm, 'Y', y0 + 0.02, y1 - 0.02, rod_x, z + 1.98, z + 0.22, gathered=gathered, folds=9, amp=0.03, mi=0, mi_ring=1, rings=12, seed=7)
    ob = cm.build(name + "_Curtain", [curtain_mat, M['chrome']], coll=COLL, smooth=True)
    _uv_from_object(ob, 'Y', 1.0 / 0.62, 1.0 / 0.52)
    _uv_repeat(curtain_mat, (1.0, 1.0))


def _uv_from_object(ob, plane, su, sv):
    """UVs from object coordinates (metres) in a vertical plane ('Y': (y, z), 'X': (x, z)) scaled by su, sv."""
    me = ob.data
    uvl = me.uv_layers.new(name="UVMap") if not me.uv_layers else me.uv_layers[0]
    for poly in me.polygons:
        for li in poly.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            a = v.y if plane == 'Y' else v.x
            uvl.data[li].uv = (a * su, v.z * sv)


def mirror_panel(M, name, along, a0, a1, b, side, z0, z1):
    mb = MB()
    f = Face(along, b, side)
    f.box(mb, a0, a1, 0.002, 0.008, z0, z1, 0)
    mb.build(name, [M['mirror']], coll=COLL)


def towel_bar(M, name, along, a0, a1, b, side, z, towel_tex=None, t0=None, t1=None, zb=None):
    """Chrome towel bar with square posts (photos 18, 23) and an optional towel folded over it (a photo texture on
    its front face, draped over the bar)."""
    mb = MB()
    f = Face(along, b, side)
    for a in (a0, a1):
        f.box(mb, a - 0.022, a + 0.022, 0.0, 0.012, z - 0.028, z + 0.028, 0)
        f.box(mb, a - 0.012, a + 0.012, 0.012, 0.07, z - 0.012, z + 0.012, 0)
    mb.tube(f.p(a0, 0.062, z), f.p(a1, 0.062, z), 0.008, 0.008, seg=10, mi=0)
    mb.build(name, [M['chrome']], coll=COLL)
    if towel_tex is not None:
        tw = MB()
        c0, c1 = t0, t1
        f.box(tw, c0, c1, 0.072, 0.080, zb, z + 0.012, 0)                                   # back layer
        tw.build(name + "_TowelBack", [towel_tex], coll=COLL)
        corners = ptx.rect_corners(along, c0, c1, b + side * 0.082, zb - 0.004, z + 0.012, side)
        ptx.uv_quad_mesh(name + "_Towel", corners, towel_tex, coll=COLL, thickness=0.004)
        rl = MB()
        rl.tube(f.p(c0, 0.074, z + 0.004), f.p(c1, 0.074, z + 0.004), 0.012, 0.012, seg=10, mi=0)    # the fold over the bar
        rl.build(name + "_TowelFold", [towel_tex], coll=COLL, smooth=True)


def paper_holder(M, name, along, a, b, side, z):
    mb = MB()
    f = Face(along, b, side)
    f.box(mb, a - 0.035, a + 0.035, 0.0, 0.012, z - 0.025, z + 0.025, 0)
    mb.tube(f.p(a, 0.012, z), f.p(a, 0.06, z), 0.008, 0.008, seg=8, mi=0)
    mb.tube(f.p(a - 0.07, 0.06, z), f.p(a + 0.03, 0.06, z), 0.008, 0.008, seg=8, mi=0)
    mb.build(name, [M['chrome']], coll=COLL)
    # roll: a horizontal cylinder along the wall
    r = MB()
    p0, p1 = f.p(a - 0.075, 0.075, z - 0.005), f.p(a + 0.02, 0.075, z - 0.005)
    r.tube(p0, p1, 0.055, 0.055, seg=20, mi=0)
    r.build(name + "_Roll", [M['paper']], coll=COLL, smooth=True)


def outlet(M, name, along, a, b, side, z, gfci=True):
    mb = MB()
    f = Face(along, b, side)
    f.box(mb, a - 0.035, a + 0.035, 0.0, 0.006, z - 0.058, z + 0.058, 0)
    f.box(mb, a - 0.022, a + 0.022, 0.006, 0.010, z - 0.034, z + 0.034, 0)
    mb.build(name, [M['porcelain']], coll=COLL)


def bottle(M, name, x, y, z, tex=None, h=0.17, r=0.04):
    """Pump soap dispenser (photos 18, 23): a round-shouldered bottle with a photo-textured label and a black pump."""
    mb = MB()
    mb.lathe(x, y, z, [(0.0, 0.0), (r * 0.95, 0.0), (r, 0.01), (r, h * 0.72), (r * 0.8, h * 0.84), (r * 0.35, h * 0.9), (r * 0.3, h), (0.0, h)], seg=24, mi=0)
    mb.build(name, [tex or M['porcelain']], coll=COLL, smooth=True)
    _uv_cyl(bpy_obj(name), x, y, z, h)
    pm = MB()
    pm.cylinder(x, y, z + h, z + h + 0.04, 0.012, seg=10, mi=0)
    pm.box(x - 0.008, x + 0.03, y - 0.008, y + 0.008, z + h + 0.035, z + h + 0.05, 0)
    pm.build(name + "_Pump", [M['dark_plastic']], coll=COLL)


def bpy_obj(name):
    import bpy
    return bpy.data.objects[name]


def _uv_cyl(ob, x, y, z, h):
    me = ob.data
    uvl = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            a = math.atan2(v.y - y, v.x - x)
            uvl.data[li].uv = ((a / math.pi + 1.0) % 1.0 * 2.0, (v.z - z) / h)


def floor_rug(M, name, corners, key, cam, size, thick=0.008, edge='rug_edge'):
    """A bath / area rug whose top carries its own pixels (rectified from the photo through the solved camera)."""
    tex = tex3d(key, cam, [(c[0], c[1], Z0 + 0.002) for c in corners], size)
    M.setdefault('rug_edge', _m.fabric("RugEdgeCotton", (0.70, 0.70, 0.68, 1), rough=0.95, weave=120))
    ptx.uv_quad_mesh(name, [(c[0], c[1], Z0 + thick) for c in corners], tex, coll=COLL, thickness=thick - 0.001, edge_mat=M[edge])


def primary_bath(M):
    """Photo 18 (z18j: camera just outside the bath door in the primary's south wall, far wall y 3.96): the double
    vanity on the x 0.15 wall from y 4.97 to the door wall, a 1.3 m mirror (z 3.72..4.63) and a six-globe chrome bar
    above it; the toilet (centre x 0.70) against the far wall beside the vanity end, the paper holder and a bidet
    sprayer on the far wall, the towel bar (x 1.27..1.96, z 4.12) with a brown checked towel; the 60" tub along the
    x 2.84 wall behind the blue paisley curtain (front x 2.03); a striped runner beside the tub and a navy trellis rug
    in front of the vanity; soap dispensers and a small posy on the counter."""
    x0, x1, y0, y1 = U.R['mbath']
    sinks, _ = vanity(M, "Up_MBath_Vanity", 'Y', 4.80, y1 - 0.02, x0, +1, sinks=2, depth=0.56, h=0.79)
    mirror_panel(M, "Up_MBath_Mirror", 'Y', 4.72, y1 - 0.05, x0, +1, Z0 + 0.88, Z0 + 1.84)
    light_bar(M, "Up_MBath_LightBar", 5.05, 6.35, x0, +1, Z0 + 2.08, n=6, along='Y', energy=30)
    toilet(M, "Up_MBath_Toilet", 0.70, y0, 0.0)
    paper_holder(M, "Up_MBath_Paper", 'X', 0.95, y0, +1, Z0 + 0.62)
    sp = MB()                                                                     # bidet sprayer + hose
    sp.box(0.48, 0.52, y0, y0 + 0.03, Z0 + 0.78, Z0 + 0.86, 0)
    sp.path_tube([(0.50, y0 + 0.03, Z0 + 0.78), (0.52, y0 + 0.05, Z0 + 0.50), (0.56, y0 + 0.12, Z0 + 0.22)], 0.005, seg=5, mi=0)
    sp.build("Up_MBath_Sprayer", [M['chrome']], coll=COLL)
    towel_bar(M, "Up_MBath_TowelBar", 'X', 1.33, 1.94, y0, +1, Z0 + 1.26, towel_tex=photo_tex('towel_18', rough=0.95), t0=1.52, t1=1.76, zb=Z0 + 0.91)
    alcove_tub(M, "Up_MBath_Tub", XMT_TUB0, x1, y0, y0 + 1.52, photo_tex('curtain_18', rough=0.85), XMT_TUB0 + 0.03)
    tw = MB()
    two_tone(tw, 'X', XMT_TUB0, x1, y0 + 1.52, y0 + 1.64)
    tw.build("Up_MBath_TubEnd", [M['up_bath']], coll=COLL)
    floor_rug(M, "Up_MBath_Runner", [(1.50, 4.82), (2.02, 4.82), (2.02, 3.76), (1.50, 3.76)], 'rug_stripe18', '18', (160, 300))
    floor_rug(M, "Up_MBath_Rug", [(0.67, 5.45), (1.39, 5.45), (1.39, 4.80), (0.67, 4.80)], 'rug_trellis18', '18', (240, 220))
    for i, sy_ in enumerate(sinks):
        a = (sy_[1] + sy_[2]) / 2
        bottle(M, f"Up_MBath_Soap_{i}", x0 + 0.32, a - 0.22, Z0 + 0.79, photo_tex('soap_18', rough=0.3), h=0.13 if i == 0 else 0.16)
    bouquet(M, "Up_MBath_Posy", x0 + 0.22, 4.92, Z0 + 0.79, kind='hydrangea', r=0.06, seed=18, stem_h=0.13)
    outlet(M, "Up_MBath_Outlet", 'Y', 4.90, x0, +1, Z0 + 1.08)
    from archviz.furnish import register
    rg = MB()
    register(rg, 1.3, 5.3, Z1, w=0.30, d=0.14, along='Y', mi=0, mi_dark=1)
    rg.build("Up_MBath_Register", [M['porcelain'], M['dark_plastic']], coll=COLL)


XMT_TUB0 = U.XMT - 0.81                   # primary tub front (curtain plane, photo 18: 2.03)


def two_tone(mb, along, a0, a1, b0, b1, z0=Z0, z1=Z1):
    U.two_tone_wall(mb, along, a0, a1, b0, b1, z0, z1, [], 0, 0)


def hall_bath(M):
    """Photo 23 (s23: camera 1.2 m inside the door, looking at the far-right corner): the double vanity on the x 8.31
    wall ending at the pier face (y 9.50) with a 1.5 m mirror and a six-globe bar; the toilet in the nook beside the pier
    (the paper holder on the pier's return), the towel bar with a brown lattice towel and an orchid on the tank; the 60"
    tub along the x 5.87 wall behind a white curtain with gold pompom dots."""
    x0, x1, y0, y1 = U.R['hbath']
    sinks, _ = vanity(M, "Up_HBath_Vanity", 'Y', 7.80, U.YHP - 0.01, x1, -1, sinks=2, depth=0.56, h=0.81)
    mirror_panel(M, "Up_HBath_Mirror", 'Y', 7.86, 9.40, x1, -1, Z0 + 0.90, Z0 + 1.81)
    light_bar(M, "Up_HBath_LightBar", 8.02, 9.30, x1, -1, Z0 + 2.26, n=6, along='Y', energy=30)
    tx = (U.XHB + 0.76 + U.XPE) / 2
    toilet(M, "Up_HBath_Toilet", tx, U.YHN, math.pi)
    paper_holder(M, "Up_HBath_Paper", 'Y', 9.72, U.XPE, -1, Z0 + 0.76)
    towel_bar(M, "Up_HBath_TowelBar", 'X', 6.80, 7.44, U.YHN, -1, Z0 + 1.44, towel_tex=photo_tex('towel_23', rough=0.95), t0=7.06, t1=7.30, zb=Z0 + 1.04)
    alcove_tub(M, "Up_HBath_Tub", U.XHB, U.XHB + 0.76, U.YHN - 1.52, U.YHN, photo_tex('curtain_23', rough=0.85), U.XHB + 0.73, gathered=0.0)
    tw = MB()
    two_tone(tw, 'X', U.XHB, U.XHB + 0.76, U.YHN - 1.64, U.YHN - 1.52)
    tw.build("Up_HBath_TubEnd", [M['up_bath']], coll=COLL)
    # orchid on the tank
    vp = MB()
    vp.lathe(tx, U.YHN - 0.12, Z0 + 0.795, [(0.0, 0.0), (0.04, 0.0), (0.055, 0.08), (0.06, 0.09), (0.0, 0.09)], seg=16, mi=0)
    vp.build("Up_HBath_OrchidPot", [M['dark_plastic']], coll=COLL)
    orchid(M, "Up_HBath_Orchid", tx, U.YHN - 0.12, Z0 + 0.885, seed=23)
    for i, sy_ in enumerate(sinks):
        a = (sy_[1] + sy_[2]) / 2
        bottle(M, f"Up_HBath_Soap_{i}", x1 - 0.30, a + 0.24, Z0 + 0.81, photo_tex('soap_23', rough=0.3), h=0.14 if i == 0 else 0.17)
    outlet(M, "Up_HBath_Outlet", 'Y', 9.45, x1, -1, Z0 + 1.20)
    outlet(M, "Up_HBath_Outlet2", 'X', 7.95, U.YHP, -1, Z0 + 1.15)
    floor_rug(M, "Up_HBath_Rug", [(7.10, 8.40), (7.70, 8.40), (7.70, 7.40), (7.10, 7.40)], 'rug_23', '23', (200, 300))


def orchid(M, name, x, y, z, seed=0):
    """Phalaenopsis-like stems with magenta flowers and two strap leaves (photo 23)."""
    rng = random.Random(seed)
    mb = MB()
    for k in range(3):
        a = rng.uniform(0, 2 * math.pi)
        pts = [(x, y, z), (x + 0.03 * math.cos(a), y + 0.03 * math.sin(a), z + 0.12), (x + 0.07 * math.cos(a), y + 0.07 * math.sin(a), z + 0.22)]
        mb.path_tube(pts, 0.003, seg=4, mi=0)
        for j in range(3):
            c = (pts[2][0] + 0.03 * j * math.cos(a), pts[2][1] + 0.03 * j * math.sin(a), pts[2][2] - 0.02 * j)
            mb.sphere(c, 0.022, seg=8, rings=5, mi=1, squash=0.5)
    for k in range(2):
        a = rng.uniform(0, 2 * math.pi)
        mb.rcbox(x + 0.06 * math.cos(a), y + 0.06 * math.sin(a), z + 0.02, 0.14, 0.05, 0.01, r=0.004, mi=2, rot=a)
    mb.build(name, [M.setdefault('orchid_stem', _m.new_mat("OrchidStem", (0.12, 0.2, 0.08, 1), rough=0.5)),
                    M.setdefault('orchid_petal', _m.fabric("OrchidMagenta", (0.55, 0.08, 0.28, 1), rough=0.5, sheen=0.3, weave=200)),
                    M.setdefault('orchid_leaf', _m.new_mat("OrchidLeaf", (0.06, 0.20, 0.06, 1), rough=0.35, coat=0.3))], coll=COLL, smooth=True)


# ================================================================ walk-in closet (photo 22)
def wire_shelf(mb, along, a0, a1, b, side, z, depth=0.31, rod=True, pitch=0.025, mi=0):
    """Ventilated wire shelving: wires across the depth every `pitch`, front lip with a hang rod below, wall clips and
    triangular support brackets (photo 22)."""
    f = Face(along, b, side)
    n = int((a1 - a0) / pitch)
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        f.box(mb, a - 0.0018, a + 0.0018, 0.015, depth, z - 0.0035, z, mi)
    for d in (0.02, depth * 0.5, depth - 0.005):
        mb.tube(f.p(a0, d, z - 0.002), f.p(a1, d, z - 0.002), 0.0028, 0.0028, seg=5, mi=mi)
    mb.tube(f.p(a0, depth, z - 0.03), f.p(a1, depth, z - 0.03), 0.003, 0.003, seg=5, mi=mi)             # front lip
    for dz in (0.0, -0.03):
        mb.tube(f.p(a0, depth + 0.004, z + dz), f.p(a1, depth + 0.004, z + dz), 0.0028, 0.0028, seg=5, mi=mi)
    if rod:
        mb.tube(f.p(a0, depth - 0.02, z - 0.055), f.p(a1, depth - 0.02, z - 0.055), 0.004, 0.004, seg=6, mi=mi)
    k = 0
    a = a0 + 0.15
    while a < a1 - 0.05:
        mb.tube(f.p(a, 0.0, z - 0.33), f.p(a, depth - 0.01, z - 0.03), 0.004, 0.004, seg=5, mi=mi)
        f.box(mb, a - 0.01, a + 0.01, 0.0, 0.01, z - 0.345, z - 0.315, mi)
        a += 0.60
        k += 1


def hanger(mb, x, y, z, rot, mi=0, w=0.40):
    """A plastic tubular hanger seen hanging from a rod (photo 22): hook + a triangle frame."""
    L = sk.F(mb, x, y, rot, z)
    L.path([(0, 0, 0.0), (0, 0.012, 0.015), (0, 0.0, 0.03), (0, -0.012, 0.015), (0, 0.0, -0.02)], 0.003, seg=5, mi=mi)
    L.path([(0, -w / 2, -0.17), (0, 0.0, -0.03), (0, w / 2, -0.17), (0, -w / 2, -0.17)], 0.004, seg=5, mi=mi)


def wic(M):
    """Photo 22 = the primary walk-in closet behind the left-gable window (z22w: camera in its east doorway, looking
    west; honey faux-wood blinds, fully lowered, as photo 01 shows from outside): white walls, ventilated wire shelves +
    rods on the far (x 0.15) and right (back, y 3.84) walls; empty white hangers on the far rod; coats near the door
    (navy, charcoal, red, purple quilted, a grey garment bag, grey suits); a black cap case and cartons on the far
    shelf, folded blankets on the back shelf; an oak nightstand-chest under the window with a boxed CRT TV, a comforter
    bag and a carton; a champagne floor mirror in the far-right corner.  The shallow chase in the front-left corner is
    architecture (interior_upper.CH22)."""
    x0, x1, y0, y1 = U.R['wic']
    zs = Z0 + 1.66
    w = MB()
    wire_shelf(w, 'Y', U.CH22[3] + 0.01, y1 - 0.01, x0, +1, zs)
    wire_shelf(w, 'X', x0 + 0.31, x1 - 0.05, y1, -1, zs)
    for i in range(9):                                                                   # empty hangers on the far rod
        hanger(w, x0 + 0.29, y0 + 0.47 + 0.03 * i + (0.04 if i > 4 else 0), zs - 0.055, 0.0, mi=0)
    for i in range(8):
        hanger(w, 0.55 + 0.03 * i, y1 - 0.29, zs - 0.055, math.pi / 2, mi=0)
    w.build("Up_WIC_Shelving", [M['wire']], coll=COLL)
    M.setdefault('coat_navy', _m.fabric("CoatNavy", (0.025, 0.035, 0.075, 1), rough=0.9, sheen=0.4, weave=80))
    M.setdefault('coat_charcoal', _m.fabric("CoatCharcoal", (0.035, 0.035, 0.04, 1), rough=0.9, sheen=0.4, weave=80))
    M.setdefault('coat_red', _m.fabric("JacketRed", (0.38, 0.02, 0.04, 1), rough=0.8, sheen=0.5, weave=100))
    M.setdefault('coat_purple', _m.fabric("QuiltedPurple", (0.11, 0.03, 0.09, 1), rough=0.6, sheen=0.6, weave=30, bump=0.6))
    M.setdefault('bag_grey', _m.new_mat("GarmentBagGrey", (0.55, 0.57, 0.60, 1), rough=0.35, coat=0.2))
    M.setdefault('suit_grey', _m.fabric("SuitGrey", (0.17, 0.18, 0.20, 1), rough=0.85, sheen=0.3, weave=150))
    c = MB()
    M.setdefault('coat_iceblue', _m.fabric("QuiltedIceBlue", (0.52, 0.58, 0.64, 1), rough=0.45, sheen=0.8, weave=30, bump=0.6))
    xs = [(1.98, 'coat_navy', 0.72, 'jacket'), (2.07, 'coat_charcoal', 0.95, 'coat'), (2.15, 'coat_red', 0.92, 'jacket'),
          (2.25, 'coat_purple', 0.90, 'quilted'), (2.40, 'coat_iceblue', 1.02, 'quilted'), (2.54, 'coat_charcoal', 1.10, 'coat'),
          (2.62, 'suit_grey', 1.05, 'suit'), (2.70, 'coat_navy', 1.15, 'coat'), (2.78, 'bag_grey', 1.1, 'bag')]
    mats_ = []
    for i, (xx, mat, ln, kind) in enumerate(xs):
        if mat not in mats_:
            mats_.append(mat)
        sk.garment(c, xx, y1 - 0.28, zs - 0.06, rot=0.0, kind=kind, length=ln, width=0.46, thick=0.13 if kind != 'bag' else 0.12,
                   mi=mats_.index(mat), seed=220 + i, sway=0.02)
    c.build("Up_WIC_Coats", [M[k] for k in mats_], coll=COLL, smooth=True)
    M.setdefault('blanket_blue', _m.fabric("BlanketBlue", (0.35, 0.50, 0.68, 1), rough=0.95, weave=40, bump=0.5))
    M.setdefault('blanket_olive', _m.fabric("BlanketOlive", (0.40, 0.36, 0.14, 1), rough=0.95, weave=40, bump=0.5))
    M.setdefault('blanket_rust', _m.fabric("BlanketRust", (0.45, 0.14, 0.10, 1), rough=0.95, weave=40, bump=0.5))
    fb = MB()
    sk.folded_stack(fb, 1.95, y1 - 0.16, zs, 0.0, 0.46, 0.30, [0, 0, 0], seed=221, t=0.05)
    sk.folded_stack(fb, 1.55, y1 - 0.16, zs, 0.1, 0.36, 0.30, [1, 2, 1], seed=222, t=0.045)
    fb.build("Up_WIC_Blankets", [M['blanket_blue'], M['blanket_olive'], M['blanket_rust']], coll=COLL, smooth=True)
    bx = MB()
    bx.rcbox(x0 + 0.16, y0 + 0.70, zs + 0.06, 0.26, 0.20, 0.11, r=0.05, mi=0, puff=0.4)       # black cap case (far shelf)
    bx.box(x0 + 0.02, x0 + 0.30, y1 - 0.72, y1 - 0.56, zs, zs + 0.20, 1)                     # tall tin
    bx.box(x0 + 0.04, x0 + 0.30, y1 - 0.54, y1 - 0.02, zs, zs + 0.10, 2)                     # shipping carton
    bx.box(0.75, 1.10, y1 - 0.30, y1 - 0.04, zs, zs + 0.16, 2)                               # gift box
    bx.build("Up_WIC_ShelfBoxes", [M['dark_plastic'], M['dark_plastic'], M['cardboard']], coll=COLL, smooth=True)
    ch = MB()
    cx_, cy_ = 0.98, y0 + 0.25                                                           # 22: under the window's -X half, front to +X
    sk.chest(ch, cx_, cy_, math.pi / 2, 0.46, 0.46, 0.70, mi=0, mi_pull=1, drawers=1, feet='none', pulls='knob', plinth=0.0, z=Z0)
    ch.build("Up_WIC_Chest", [M['oak_lam'], M['brushed']], coll=COLL)
    ca = MB()
    ca.rbox(cx_ - 0.22, cx_ + 0.20, cy_ - 0.22, cy_ + 0.20, Z0 + 0.705, Z0 + 0.83, r=0.006, mi=0)
    ca.build("Up_WIC_Carton", [M['cardboard']], coll=COLL, smooth=True)
    tv = MB()                                                                            # small flat TV on its stand, seen edge-on
    tv.box(cx_ - 0.10, cx_ - 0.05, cy_ - 0.22, cy_ + 0.14, Z0 + 0.87, Z0 + 1.14, 0)
    tv.box(cx_ - 0.12, cx_ - 0.02, cy_ - 0.08, cy_ + 0.02, Z0 + 0.83, Z0 + 0.87, 0)
    tv.build("Up_WIC_TV", [M['dark_plastic']], coll=COLL, smooth=True)
    bg = MB()
    bg.rcbox(cx_ + 0.02, cy_ + 0.08, Z0 + 0.98, 0.26, 0.20, 0.30, r=0.07, mi=0, puff=0.45)
    bg.build("Up_WIC_ComforterBag", [M.setdefault('bag_clear', _m.new_mat("ComforterBagPale", (0.62, 0.74, 0.80, 1), rough=0.3, coat=0.4))],
             coll=COLL, smooth=True)
    mr = MB()                                                                            # floor mirror leaning in the far-right corner
    L = sk.F(mr, x0 + 0.20, y1 - 0.22, 0.0, Z0)
    L.hexa([(-0.05, -0.20, 0.0), (0.0, -0.20, 0.0), (0.0, 0.20, 0.0), (-0.05, 0.20, 0.0),
            (-0.17, -0.20, 1.40), (-0.12, -0.20, 1.40), (-0.12, 0.20, 1.40), (-0.17, 0.20, 1.40)], 0)
    L.hexa([(0.0, -0.16, 0.05), (0.004, -0.16, 0.05), (0.004, 0.16, 0.05), (0.0, 0.16, 0.05),
            (-0.116, -0.16, 1.35), (-0.112, -0.16, 1.35), (-0.112, 0.16, 1.35), (-0.116, 0.16, 1.35)], 1)
    mr.build("Up_WIC_FloorMirror", [M['champagne'], M['mirror']], coll=COLL)
    from archviz.furnish import register
    rg = MB()
    register(rg, 1.30, y0 + 0.95, Z1, w=0.30, d=0.14, along='X', mi=0, mi_dark=1)
    rg.build("Up_WIC_Register", [M['porcelain'], M['dark_plastic']], coll=COLL)


# ================================================================ stairwell (photo 15), laundry, hall
def stairwell(M):
    """Photo 15: a crystal-bead drum pendant on a rigid rod over the landing, the framed camel print right of the
    landing window, plants on the landing (a tall lucky-bamboo / dracaena in a large white embossed pot on a caddy, a
    small aloe in a blue pot on a caddy, a palm in the corner by the window), a round silver mirror on the north wall."""
    cx, cy = (ST_LAND + U.XR) / 2 - 0.10, (ST_Y0 + ST_Y1) / 2 + 0.01  # photo 15 solve: (11.74, 5.86), drum centre 1.02 below the ceiling
    p, g = MB(), MB()
    c = sk.drum_pendant(p, cx, cy, Z1, 1.07, 0, 1, r=0.085, h=0.10, seed=15)            # drum centre z 4.18
    p.build("Up_Pendant", [M['brushed'], M['crystal']], coll=COLL, smooth=True)
    g.cylinder(cx, cy, c[2] - 0.035, c[2] + 0.035, 0.025, seg=12, mi=0)
    g.build("Up_PendantBulb", [M['bulb']], coll=COLL)
    add_light("L_Up_Pendant", 'POINT', c, 12, color=(1.0, 0.88, 0.72), size=0.04, coll=LCOLL)
    o = next(o for o in OPENINGS if o['name'] == 'landing_win')
    frame_art(M, "Up_LandingPrint", 'Y', o['a0'] - 0.52, o['a0'] - 0.18, U.XR, -1, Z_LAND + 1.95, Z_LAND + 2.28, photo_tex('camel_15'),
              frame='cherry', fw=0.02, mat_w=0.04)
    zl = Z_LAND
    _pl.potted("Up_LandingPlant_0", (U.XR - 0.30, ST_Y1 - 0.30, zl), kind='fiddle', height=1.35, pot='white', pot_r=0.21, seed=40, coll=COLL)
    _pl.potted("Up_LandingPlant_1", (U.XR - 0.25, o['a0'] - 0.25, zl), kind='palm', height=0.95, pot='white', pot_r=0.16, seed=41, coll=COLL)
    _pl.potted("Up_LandingPlant_2", (U.XR - 0.62, ST_Y1 - 0.22, zl), kind='fern', height=0.40, pot='black', pot_r=0.12, seed=42, coll=COLL)
    md = MB()                                                                  # round silver-framed mirror on the north wall
    mx, mz = ST_LAND + 0.35, Z_LAND + 1.62
    md.tube((mx, ST_Y1 - 0.003, mz), (mx, ST_Y1 - 0.025, mz), 0.165, 0.165, seg=36, mi=0)
    md.tube((mx, ST_Y1 - 0.025, mz), (mx, ST_Y1 - 0.028, mz), 0.13, 0.13, seg=36, mi=1)
    md.build("Up_Stair_Mirror", [M['silver'], M['mirror']], coll=COLL)
    smoke = MB()
    smoke_detector(smoke, ST_X0 + 0.3, ST_Y1 - 0.4, Z1)
    smoke.build("Up_Stair_Smoke", [M['porcelain']], coll=COLL)


def laundry(M):
    x0, x1, y0, y1 = U.R['laundry']
    mb = MB()
    for i, cx in enumerate((x0 + 0.40, x0 + 1.10)):
        mb.rbox(cx - 0.34, cx + 0.34, y1 - 0.72, y1 - 0.04, Z0, Z0 + 0.98, r=0.03, mi=0)
        mb.cylinder(cx, y1 - 0.73, Z0 + 0.35, Z0 + 0.36, 0.20, seg=24, mi=1)
    mb.build("Up_Laundry_Pair", [M['porcelain'], M['dark_plastic']], coll=COLL)
    sh = MB()
    wire_shelf(sh, 'X', x0 + 0.05, x0 + 1.6, y1, -1, Z0 + 1.75)
    sh.build("Up_Laundry_Shelf", [M['wire']], coll=COLL)


def hall(M):
    """Upper hall: dome flush-mounts, a framed print, the smoke detector and a return-air grille."""
    frame_art(M, "Up_Hall_Art", 'X', 6.3, 7.0, U.HY0, +1, Z0 + 1.35, Z0 + 1.85, 'art_hall', frame='frame_gold')
    mb = MB()
    for (x, y) in ((6.6, (U.HY0 + U.HY1) / 2), (9.2, (ST_Y0 + ST_Y1) / 2)):
        mb.lathe(x, y, Z1 - 0.09, [(0.0, 0.0), (0.10, 0.005), (0.16, 0.04), (0.17, 0.08), (0.17, 0.09), (0.0, 0.09)], seg=28, mi=0)
    mb.build("Up_Hall_Flushmounts", [M['fan_glass']], coll=COLL, smooth=True)


def build(M):
    mats(M)
    master(M)
    bed19(M)
    bed20(M)
    bed21(M)
    primary_bath(M)
    hall_bath(M)
    wic(M)
    stairwell(M)
    laundry(M)
    hall(M)
    window_dressing(M)
    lights(M)


def window_dressing(M):
    """White 2" blinds in the primary suite (16: left window fully lowered, right window ~55 %), honey faux-wood blinds
    in the front gables (20, 22), white in 19, white behind the sheers in 21, white on the landing window (15)."""
    op = {o['name']: o for o in OPENINGS}
    blinds(M, "Up_Blinds_rear_up_l", op['rear_up_l'], 'blind_white', drop=0.97, tilt=0.55)
    blinds(M, "Up_Blinds_rear_up_m", op['rear_up_m'], 'blind_white', drop=0.52, tilt=0.4)
    blinds(M, "Up_Blinds_rear_up_r", op['rear_up_r'], 'blind_wood', drop=0.58, tilt=0.30, valance=True)       # photo 19
    blinds(M, "Up_Blinds_rg_win", op['rg_win'], 'blind_wood', drop=1.0, tilt=0.12, valance=True)              # photo 20: open slats
    blinds(M, "Up_Blinds_lg_win", op['lg_win'], 'blind_wood', drop=1.0, tilt=0.35, valance=True)              # photos 22 + 01
    blinds(M, "Up_Blinds_cen_win", op['cen_win'], 'blind_white', drop=0.5, tilt=0.4)                         # photo 01 (outside)
    blinds(M, "Up_Blinds_bay_up_win", op['bay_up_win'], 'blind_white', drop=0.98, tilt=0.35)                  # photo 21 (behind sheers)
    blinds(M, "Up_Blinds_landing_win", op['landing_win'], 'blind_white', drop=0.97, tilt=0.15, face=(U.XR, +1))  # photo 15


def lights(M):
    """Photo lighting: large neutral fills under each ceiling (the listing photos are HDR-processed flash/daylight
    exposures: even, bright, neutral), scaled per camera in before_render."""
    for name, (x0, x1, y0, y1) in U.R.items():
        if name in ('vest', 'lin', 'clo19'):
            continue
        w, d = (x1 - x0) * 0.7, (y1 - y0) * 0.7
        e = float(os.environ.get('UP_FILL', 13.0)) * w * d
        area_light(f"L_Up_Fill_{name}", ((x0 + x1) / 2, (y0 + y1) / 2, Z1 - 0.05), (w, d), e, color=(1.0, 0.975, 0.95), coll=LCOLL)
        eb = float(os.environ.get('UP_BOUNCE', 6.0)) * w * d            # floor bounce: lights the ceiling as the photos' HDR does
        area_light(f"L_Up_Bounce_{name}", ((x0 + x1) / 2, (y0 + y1) / 2, Z0 + 0.25), (w, d), eb, color=(1.0, 0.97, 0.94), down=False, coll=LCOLL)
    area_light("L_Up_Fill_stair", ((ST_X0 + U.XR) / 2, (ST_Y0 + ST_Y1) / 2, Z1 - 0.06), (1.8, 1.4), 45, color=(1.0, 0.97, 0.93), coll=LCOLL)
    area_light("L_Up_Bounce_stair", ((ST_X0 + U.XR) / 2, (ST_Y0 + ST_Y1) / 2, Z_LAND + 0.3), (1.2, 1.4), 20, color=(1.0, 0.97, 0.94), down=False,
               coll=LCOLL)


PHOTO_CAMS = {'p15', 'p16', 'p17', 'p18', 'p19', 'p20', 'p21', 'p22', 'p23'}
FILL_GAIN = {'p16': 0.65, 'p17': 0.75, 'p19': 1.0, 'p20': 0.75, 'p21': 1.1, 'p18': 0.75, 'p23': 0.75, 'p22': 0.55, 'p15': 1.0}
# a soft 'bounce flash' behind the photographer (listing photos are flash / HDR brackets: the walls facing the camera are lit)
CAM_FILL = {'p17': 90.0, 'p20': 40.0, 'p21': 160.0, 'p22': 20.0}


def _cam_fill(S, name):
    import bpy
    from mathutils import Vector
    ob = bpy.data.objects.get("L_Up_CamFill")
    if ob is None:
        ob = area_light("L_Up_CamFill", (0, 0, 0), (1.2, 1.0), 0.0, color=(1.0, 0.97, 0.94), coll=LCOLL)
        ob.visible_camera = False
        ob.visible_glossy = False
        ob.visible_transmission = False
        ob.data.spread = math.radians(140)
    e = CAM_FILL.get(name, 0.0)
    ob.data.energy = e
    ob.hide_render = e <= 0.0
    if e > 0 and S.camera is not None:
        cam = S.camera                                         # (matrix_world may be stale right after a camera is made)
        rot = cam.rotation_euler.to_quaternion()
        fwd = rot @ Vector((0, 0, -1))
        ob.location = Vector(cam.location) + fwd * 0.30 + Vector((0, 0, 0.30))     # just in front of the lens (in the room)
        ob.rotation_euler = cam.rotation_euler.copy()


DOOR_STATE = {'p18': {'Door_MBath': 100}}           # photo 18 is taken from the open bath door


def before_render(S, name):
    """Photo cameras: decorative lamps off (the photos show them unlit), fills per camera, per-photo door states;
    other cameras: defaults."""
    import bpy
    photo = name in PHOTO_CAMS
    _cam_fill(S, name)
    for dn in ('Door_MBath',):
        ob = bpy.data.objects.get(dn)
        if ob is None:
            continue
        if '_rest' not in ob:
            ob['_rest'] = tuple(ob.rotation_euler)
        rz = ob['_rest'][2]
        ang = DOOR_STATE.get(name, {}).get(dn)
        if ang is not None:
            rz = math.radians(ang) * ob.get('open_sign', 1)
        ob.rotation_euler = (ob['_rest'][0], ob['_rest'][1], rz)
    if not photo:          # house.before_render has already restored every light's build-time energy (ob['_e0'])
        return
    for ob in bpy.data.objects:
        if ob.type != 'LIGHT' or not ob.name.startswith('L_Up_') or ob.name == 'L_Up_CamFill':
            continue
        e = ob.get('_e0', ob.data.energy)
        if '_Lamp_' in ob.name:
            e = 0.0
        elif ob.name.startswith(('L_Up_Fill', 'L_Up_Bounce')):
            e *= FILL_GAIN.get(name, 1.0)
        ob.data.energy = e
