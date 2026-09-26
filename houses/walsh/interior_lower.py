"""Lower level (Z 0 / sunken -0.9): foyer + sculptural spiral stair, billiard area with the moss art wall,
sunken lounge (moss W, backlit onyx wine wall N, travertine TV/fire wall E), sunken home theatre.
Photos 05, 06, 07, 08, 09, 31."""
import math, random, os
import numpy as np
from .plan import *
from archviz.mesh import *
from archviz.lights import *
from archviz.parts import *

from archviz import materials as _mat


def moss_material(name, c_dark, c_mid, c_light):
    """One tone of preserved moss (pole / reindeer moss): matte, fuzzy, slightly translucent.  Fine high-frequency
    noise gives the sponge-like fuzz, a mid-frequency noise mottles the tone across a clump."""
    m, nt, b = _mat._new(name)
    vec = _mat._coords(nt)
    fine = _mat._noise(nt, vec, scale=140.0, detail=3.0, rough=0.6)
    mid = _mat._noise(nt, vec, scale=18.0, detail=4.0, rough=0.6)
    f = _mat._math(nt, 'ADD', _mat._math(nt, 'MULTIPLY', fine, 0.45), _mat._math(nt, 'MULTIPLY', mid, 0.65))
    col = _mat._ramp(nt, f, [(0.25, c_dark + (1,)), (0.55, c_mid + (1,)), (0.85, c_light + (1,))])
    nt.links.new(b.inputs["Base Color"], col)
    _mat._set(b, "Roughness", 1.0); _mat._set(b, "Specular IOR Level", 0.04)
    _mat._set(b, "Subsurface Weight", 0.12); _mat._set(b, "Subsurface Radius", (0.01, 0.015, 0.005))
    _mat._set(b, "Sheen Weight", 0.5)
    _mat._bump(nt, b, _mat._math(nt, 'ADD', _mat._math(nt, 'MULTIPLY', fine, 0.8), _mat._math(nt, 'MULTIPLY', mid, 0.3)), 0.9, 0.006)
    return m


def screen_frame_material():
    """The cinema screen showing a stylised studio-logo frame (photo 08): a gold-to-blue sky, billowing sun-lit
    clouds, a dark stepped pedestal with a slim figure holding a torch.  Uses the object's Generated coordinates
    (u = along the wall, v = up), so it must be its own object."""
    m, nt, b = _mat._new("CinemaFrame")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(sep.inputs["Vector"], tc.outputs["Generated"])
    u, v = sep.outputs["Y"], sep.outputs["Z"]
    sky = _mat._ramp(nt, v, [(0.0, (1.0, 0.66, 0.26, 1)), (0.28, (0.90, 0.62, 0.42, 1)), (0.58, (0.30, 0.42, 0.66, 1)), (1.0, (0.06, 0.15, 0.40, 1))])
    # clouds: a stretched noise thresholded softly; lit tops warm, undersides mauve-grey; denser low in the frame
    cv = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(cv.inputs["X"], _mat._math(nt, 'MULTIPLY', u, 2.6)); nt.links.new(cv.inputs["Y"], _mat._math(nt, 'MULTIPLY', v, 1.6))
    n = _mat._noise(nt, cv.outputs["Vector"], scale=1.0, detail=7.0, rough=0.6, distortion=0.5)
    n2 = _mat._noise(nt, cv.outputs["Vector"], scale=2.5, detail=3.0)
    mask = _mat._stretch(nt, n, 0.42, 0.56)
    low = _mat._ramp(nt, v, [(0.10, (1, 1, 1, 1)), (0.95, (0.35, 0.35, 0.35, 1))])
    lsep = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(lsep.inputs["Color"], low)
    mask = _mat._math(nt, 'MULTIPLY', mask, lsep.outputs["Red"])
    ccol = _mat._ramp(nt, n2, [(0.3, (0.32, 0.25, 0.28, 1)), (0.5, (0.72, 0.58, 0.50, 1)), (0.65, (1.15, 1.0, 0.78, 1)), (0.85, (1.35, 1.25, 1.05, 1))])
    col = _mat._mixrgb(nt, mask, sky, ccol)
    # stepped pedestal (dark silhouette, ~16 % of the width at its foot) + slim figure + torch
    du = _mat._math(nt, 'ABSOLUTE', _mat._math(nt, 'SUBTRACT', u, 0.5))
    hw = _mat._math(nt, 'ADD', 0.025, _mat._math(nt, 'MULTIPLY', _mat._math(nt, 'SUBTRACT', 0.36, v), 0.16))
    steps = _mat._math(nt, 'MULTIPLY', _mat._math(nt, 'LESS_THAN', du, hw), _mat._math(nt, 'LESS_THAN', v, 0.36))
    col = _mat._mixrgb(nt, steps, col, (0.10, 0.08, 0.07, 1))
    fig = _mat._math(nt, 'MULTIPLY', _mat._math(nt, 'LESS_THAN', du, 0.014), _mat._math(nt, 'MULTIPLY', _mat._math(nt, 'GREATER_THAN', v, 0.36), _mat._math(nt, 'LESS_THAN', v, 0.60)))
    col = _mat._mixrgb(nt, fig, col, (0.62, 0.58, 0.60, 1))
    torch = _mat._math(nt, 'LESS_THAN', _mat._math(nt, 'ADD', _mat._math(nt, 'MULTIPLY', _mat._math(nt, 'SUBTRACT', u, 0.522), _mat._math(nt, 'SUBTRACT', u, 0.522)),
                                                        _mat._math(nt, 'MULTIPLY', _mat._math(nt, 'SUBTRACT', v, 0.64), _mat._math(nt, 'SUBTRACT', v, 0.64))), 0.00015)
    col = _mat._mixrgb(nt, torch, col, (2.0, 1.8, 1.2, 1))
    nt.links.new(b.inputs["Base Color"], col)
    nt.links.new(b.inputs["Emission Color"], col)
    _mat._set(b, "Emission Strength", 0.85); _mat._set(b, "Roughness", 0.9); _mat._set(b, "Specular IOR Level", 0.1)
    return m


SCREEN_IMAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "renders", "hero.png")


def screen_image_material(path, strength=1.4):
    """The cinema screen showing a real picture (a property film — one of our own finished renders).  The image is
    mapped by the screen object's Generated coordinates (u = along the wall = Y, v = up = Z), so the screen must be
    its own object with a 16:9 face.  The picture is emissive (it is the room's key light) with a soft corner
    vignette; the fabric itself is a matte white so the black bars / frame stay black.
    Returns (material, average colour) — the average is used to colour the light that spills into the room."""
    img = bpy.data.images.load(path, check_existing=True)
    px = np.empty(len(img.pixels), dtype=np.float32)
    img.pixels.foreach_get(px)
    avg = px.reshape(-1, 4)[::97, :3].mean(axis=0)                 # sparse sample of the sRGB pixels
    avg = tuple(float(c) ** 2.2 for c in avg)                        # -> linear-ish light colour
    m, nt, b = _mat._new("CinemaScreen")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(sep.inputs["Vector"], tc.outputs["Generated"])
    u, v = sep.outputs["Y"], sep.outputs["Z"]
    uv = nt.nodes.new("ShaderNodeCombineXYZ"); nt.links.new(uv.inputs["X"], u); nt.links.new(uv.inputs["Y"], v)
    tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = img; tex.extension = 'EXTEND'; tex.interpolation = 'Cubic'
    nt.links.new(tex.inputs["Vector"], uv.outputs["Vector"])
    # vignette: 1 - 0.30 * r^2 (r = 1 at the corners), so the corners sit ~30 % darker like a projected picture
    du = _mat._math(nt, 'MULTIPLY', _mat._math(nt, 'SUBTRACT', u, 0.5), 2.0)
    dv = _mat._math(nt, 'MULTIPLY', _mat._math(nt, 'SUBTRACT', v, 0.5), 2.0)
    r2 = _mat._math(nt, 'ADD', _mat._math(nt, 'MULTIPLY', du, du), _mat._math(nt, 'MULTIPLY', dv, dv))
    dark = _mat._math(nt, 'MULTIPLY', r2, 0.15, clamp=True)
    col = _mat._mixrgb(nt, dark, tex.outputs["Color"], (0.0, 0.0, 0.0, 1))
    nt.links.new(b.inputs["Base Color"], col)
    nt.links.new(b.inputs["Emission Color"], col)
    _mat._set(b, "Emission Strength", strength); _mat._set(b, "Roughness", 0.9); _mat._set(b, "Specular IOR Level", 0.05)
    return m, avg


LM = {}


def local_materials(M):
    """Materials specific to the lower level (kept out of the shared library)."""
    if LM:
        return LM
    LM['floor'] = _mat.tiles("LimestoneLower", (0.87, 0.82, 0.72, 1), grout=(0.62, 0.57, 0.49, 1), size=(1.2, 1.2), gap=0.004,
                             rough=0.30, variation=0.05, mottle=0.3, bump=0.08, coat=0.3)
    LM['moss_lime'] = moss_material("MossLime", (0.40, 0.55, 0.07), (0.62, 0.72, 0.15), (0.80, 0.85, 0.32))
    LM['moss_yellow'] = moss_material("MossYellow", (0.48, 0.50, 0.09), (0.70, 0.68, 0.18), (0.86, 0.82, 0.36))
    LM['moss_olive'] = moss_material("MossOlive", (0.12, 0.26, 0.05), (0.26, 0.40, 0.09), (0.40, 0.52, 0.15))
    LM['moss_deep'] = moss_material("MossDeep", (0.025, 0.09, 0.025), (0.07, 0.19, 0.045), (0.14, 0.28, 0.07))
    LM['moss_back'] = _mat.noise_mat("MossBacking", (0.02, 0.05, 0.02, 1), (0.04, 0.09, 0.03, 1), scale=40, bump=0.4, rough=1.0, spec=0.02)
    LM['onyx_wine'] = _mat.onyx("OnyxWineLounge", c1=(0.98, 0.78, 0.42, 1), c2=(0.85, 0.50, 0.16, 1), c3=(0.36, 0.15, 0.03, 1),
                                emit=0.8, freq=15.0, wobble=0.3, vein=0.45)
    LM['bottle_glass'] = _mat.new_mat("BottleGlass", (0.06, 0.12, 0.05, 1), rough=0.05, transmission=0.6, ior=1.5, coat=0.5)
    LM['bottle_pale'] = _mat.new_mat("BottleGlassPale", (0.55, 0.62, 0.35, 1), rough=0.05, transmission=0.8, ior=1.5, coat=0.5)
    LM['foil_red'] = _mat.new_mat("FoilRed", (0.35, 0.03, 0.03, 1), rough=0.35, metal=0.6)
    LM['foil_gold'] = _mat.new_mat("FoilGold", (0.75, 0.55, 0.20, 1), rough=0.3, metal=0.8)
    LM['boucle'] = _mat.fabric("BoucleLounge", (0.88, 0.85, 0.78, 1), weave=45.0, bump=0.35)
    if os.path.exists(SCREEN_IMAGE):
        LM['screen'], LM['screen_avg'] = screen_image_material(SCREEN_IMAGE)
    else:                                                            # no finished render yet: stylised studio frame
        LM['screen'], LM['screen_avg'] = screen_frame_material(), (0.55, 0.50, 0.55)
    LM['leather_white'] = _mat.leather("LeatherTheatre", (0.92, 0.91, 0.87, 1), rough=0.4)
    LM['velvet_black'] = _mat.fabric("VelvetBlack", (0.015, 0.014, 0.014, 1), rough=0.95, sheen=0.4, weave=150, bump=0.1)
    LM['acoustic'] = _mat.fabric("AcousticLinen", (0.70, 0.66, 0.58, 1), rough=0.95, sheen=0.3, weave=120, bump=0.3)
    LM['acoustic_pale'] = _mat.fabric("AcousticTaupe", (0.50, 0.45, 0.38, 1), rough=0.98, sheen=0.25, weave=140, bump=0.35)
    LM['cashmere'] = _mat.fabric("CashmereGrey", (0.50, 0.47, 0.43, 1), rough=0.95, sheen=0.5, weave=80, bump=0.3)
    LM['emit_slot'] = _mat.new_mat("EmitTheatreSlot", (1, 0.85, 0.65, 1), emit=(1.0, 0.80, 0.55, 1), emit_str=7.0)
    LM['emit_strip'] = _mat.new_mat("EmitTheatreStrip", (1, 0.85, 0.65, 1), emit=(1.0, 0.80, 0.55, 1), emit_str=9.0)
    LM['oak_ceiling_dark'] = _mat.wood("OakTheatreCeiling", light=(0.66, 0.52, 0.35, 1), dark=(0.50, 0.37, 0.23, 1), grain_axis='X', rough=0.45, coat=0.1)
    LM['oak_dark'] = _mat.wood("OakTheatre", light=(0.62, 0.48, 0.32, 1), dark=(0.46, 0.34, 0.21, 1), grain_axis='Z', rough=0.4, coat=0.15)
    return LM


FOY = (-5.6, MX1 - WT, MY0 + WT, FOYER_Y1, Z_COURT, Z_SOF)          # foyer (double height) incl. the stair
BIL = (-9.5, -5.6, MY0 + WT, FOYER_Y1, Z_COURT, Z_LIV - 0.37)        # billiard area, open to the foyer, ceiling = slab underside
LNG = ROOMS['lounge']                                                # (-12.05, -5.0, 8.4, 17.0, -0.9, 2.23)
THR = ROOMS['theatre']                                               # (-12.05, -5.0, 17.4, 23.55, -0.9, 2.23)
GAR = (-12.05, -9.5, MY0 + WT, 8.0, Z_COURT, Z_LIV - 0.37)
STEP_X0, STEP_X1 = -9.3, -5.8                                        # wide travertine steps billiard -> lounge
LANDING_A0, LANDING_A1 = math.radians(122), math.radians(160)        # dining landing on the stair


def _ccw(pts):
    a = sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))
    return pts if a > 0 else list(reversed(pts))


# ---------------------------------------------------------------- spiral stair
class Helix:
    """Piecewise stair path: run1 (Z 0 -> Z_LIV), flat landing, run2 (Z_LIV -> Z_UP). angle -> z."""
    def __init__(self):
        self.th0 = math.radians(-92)
        self.n1, self.n2 = 15, 22
        self.dz1, self.dz2 = Z_LIV / self.n1, (Z_UP - Z_LIV) / self.n2
        self.a_run1 = math.radians(214)
        self.a_land = LANDING_A1 - LANDING_A0
        self.a_run2 = math.radians(300)
        self.a1 = self.th0 + self.a_run1
        self.a2 = self.a1 + self.a_land
        self.a3 = self.a2 + self.a_run2
        self.dth1 = self.a_run1 / self.n1
        self.dth2 = self.a_run2 / self.n2

    def z_of(self, a):
        if a <= self.a1:
            return Z_LIV * (a - self.th0) / self.a_run1
        if a <= self.a2:
            return Z_LIV
        if a <= self.a3:
            return Z_LIV + (Z_UP - Z_LIV) * (a - self.a2) / self.a_run2
        return Z_UP

    def steps(self):
        for i in range(self.n1):
            yield (self.th0 + i * self.dth1, self.th0 + (i + 1) * self.dth1, self.dz1 * (i + 1))
        for i in range(self.n2):
            yield (self.a2 + i * self.dth2, self.a2 + (i + 1) * self.dth2, Z_LIV + self.dz2 * (i + 1))


def _ribbon(mb, hx, r, a_from, a_to, thick, below, above, mi=0, n=None, z_lo_clamp=-9.0, top_flat=None):
    """Sweep a vertical rectangular section (radius r..r+thick, nosing-line z - below .. z + above) along the helix."""
    n = n or max(4, int(abs(a_to - a_from) / math.radians(2.5)))
    cx, cy = STAIR_C
    secs = []
    for k in range(n + 1):
        a = a_from + (a_to - a_from) * k / n
        zc = hx.z_of(a) if top_flat is None else top_flat
        zb = max(zc - below, z_lo_clamp)
        zt = zc + above
        c, s = math.cos(a), math.sin(a)
        secs.append([(cx + r * c, cy + r * s, zb), (cx + (r + thick) * c, cy + (r + thick) * s, zb),
                     (cx + (r + thick) * c, cy + (r + thick) * s, zt), (cx + r * c, cy + r * s, zt)])
    mb.sweep(secs, mi)


def spiral_stair(M):
    hx = Helix()
    cx, cy = STAIR_C
    ri, ro = STAIR_RI, STAIR_RO
    # treads: solid oak blocks (closed risers) inside the ribbons, with a small nosing lip
    tr = MB()
    for (a0, a1, zt) in hx.steps():
        tr.arc_prism(cx, cy, ri + 0.01, ro - 0.01, a0, a1, zt - 0.19, zt, seg=3, mi=0)
        tr.arc_prism(cx, cy, ri + 0.01, ro - 0.01, a0, a1 + math.radians(1.2), zt - 0.035, zt + 0.004, seg=3, mi=0)   # 12 mm nosing
    # landing + bridge to the dining mezzanine at Z_LIV
    tr.arc_prism(cx, cy, ri + 0.01, ro - 0.01, hx.a1, hx.a2, Z_LIV - 0.19, Z_LIV, seg=8, mi=0)
    pts = [(cx + ro * math.cos(a), cy + ro * math.sin(a)) for a in [LANDING_A0 + (LANDING_A1 - LANDING_A0) * k / 8 for k in range(9)]]
    pts += [(-5.55, cy + ro * math.sin(LANDING_A1)), (-5.55, FOYER_Y1 + 0.2), (cx + ro * math.cos(LANDING_A0) + 0.6, FOYER_Y1 + 0.2)]
    tr.prism(_ccw(pts), Z_LIV - 0.19, Z_LIV, 0)
    tr.build("Stair_Treads", M['oak_h'])
    # continuous white helical soffit under the treads
    sf = MB()
    n = int((hx.a3 - hx.th0) / math.radians(2.5))
    secs = []
    for k in range(n + 1):
        a = hx.th0 + (hx.a3 - hx.th0) * k / n
        zb = max(hx.z_of(a) - 0.30, -0.02)
        c, s = math.cos(a), math.sin(a)
        secs.append([(cx + ri * c, cy + ri * s, zb), (cx + ro * c, cy + ro * s, zb),
                     (cx + ro * c, cy + ro * s, zb + 0.15), (cx + ri * c, cy + ri * s, zb + 0.15)])
    sf.sweep(secs, 0)
    sf.build("Stair_Soffit", M['white_int'], smooth=True)
    # outer white ribbon (gap at the dining landing) continuing as a curved parapet at the top; inner ribbon
    rb = MB()
    _ribbon(rb, hx, ro, hx.th0 - math.radians(8), LANDING_A0 - math.radians(2), 0.08, 0.28, 1.0, 0, z_lo_clamp=0.0)
    _ribbon(rb, hx, ro, LANDING_A1 + math.radians(2), hx.a3, 0.08, 0.28, 1.0, 0)
    _ribbon(rb, hx, ro, hx.a3, hx.a3 + math.radians(55), 0.08, 0.28, 1.0, 0, top_flat=Z_UP)
    _ribbon(rb, hx, ri - 0.06, hx.th0 + math.radians(30), hx.a3, 0.06, 0.28, 0.92, 0, z_lo_clamp=0.0)
    _ribbon(rb, hx, ri - 0.06, hx.a3, hx.a3 + math.radians(40), 0.06, 0.28, 0.92, 0, top_flat=Z_UP)
    rb.build("Stair_Ribbon", M['white_int'], smooth=True)
    # oak handrail strips capping both ribbons (a 5 cm band at the top edge)
    hr = MB()
    _ribbon(hr, hx, ro - 0.05, hx.th0 - math.radians(8), LANDING_A0 - math.radians(2), 0.05, -0.95, 1.0, 0)
    _ribbon(hr, hx, ro - 0.05, LANDING_A1 + math.radians(2), hx.a3, 0.05, -0.95, 1.0, 0)
    _ribbon(hr, hx, ro - 0.05, hx.a3, hx.a3 + math.radians(55), 0.05, -0.95, 1.0, 0, top_flat=Z_UP)
    _ribbon(hr, hx, ri - 0.06, hx.th0 + math.radians(30), hx.a3, 0.05, -0.87, 0.92, 0)
    _ribbon(hr, hx, ri - 0.06, hx.a3, hx.a3 + math.radians(40), 0.05, -0.87, 0.92, 0, top_flat=Z_UP)
    hr.build("Stair_Handrail", M['oak_h'], smooth=True, bevel=0.012, bevel_seg=4)
    # continuous LED strip tucked under the outer ribbon's lower lip (lights the treads' edge)
    led = MB()
    _ribbon(led, hx, ro - 0.02, hx.th0 + 3 * hx.dth1, LANDING_A0 - math.radians(2), 0.05, 0.292, -0.281, 0)
    _ribbon(led, hx, ro - 0.02, LANDING_A1 + math.radians(2), hx.a3, 0.05, 0.292, -0.281, 0)
    led.build("Stair_LED", M['emit_cove'], smooth=True)
    # oak-clad drum filling the inner radius of the lower turn (photo 11/13)
    dm = MB()
    dm.cylinder(cx, cy, 0.0, Z_LIV + 0.95, ri - 0.07, seg=48)
    dm.build("Stair_Drum", M['oak'], smooth=True)
    # fill the rectangular slab hole outside the stair circle at the upper floor (flush with Z_UP)
    fl = MB()
    hx0, hx1, hy0, hy1 = STAIR_HOLE
    R = ro + 0.09
    ring_in, ring_out = [], []
    for k in range(64):
        a = 2 * math.pi * k / 64
        c, s = math.cos(a), math.sin(a)
        ring_in.append((cx + R * c, cy + R * s))
        tx = (hx1 - cx) / c if c > 1e-6 else ((hx0 - cx) / c if c < -1e-6 else 1e9)
        ty = (hy1 - cy) / s if s > 1e-6 else ((hy0 - cy) / s if s < -1e-6 else 1e9)
        t = min(abs(tx), abs(ty))
        ring_out.append((cx + t * c, cy + t * s))
    for k in range(64):
        j = (k + 1) % 64
        fl.prism(_ccw([ring_in[k], ring_out[k], ring_out[j], ring_in[j]]), Z_SOF, Z_UP, 0)
    fl.build("Stair_HoleFill", M['white_int'])
    return hx


# ---------------------------------------------------------------- foyer + billiard area
def foyer(M):
    x0, x1, y0, y1, z0, z1 = FOY
    lm = local_materials(M)
    box("Foyer_Floor", BIL[0], x1, y0, y1, z0, z0 + 0.02, lm['floor'])               # continuous 1.2 m limestone floor into the billiard area
    w = MB()
    w.box(x1 - 0.03, x1, y0, y1, z0, z1, 0)                                            # east wall finish
    w.box(x0 - 0.15, x0, y0, y1, BIL[5], z1, 0)                                        # bulkhead: double-height foyer vs. low billiard ceiling
    w.box(x0 - 0.15, x1, y1, y1 + 0.2, z0, Z_LIV - 0.35, 0)                            # wall under the mezzanine
    w.build("Foyer_Walls", M['white_int'])
    foyer_dl = [(x, y) for x in (1.0, 3.0, 5.0) for y in (1.6, 4.2, 6.8)]
    ceiling_kit("Foyer_Ceiling", M, x0 - 0.15, x1, y0, y1, z1, holes=[STAIR_HOLE],
                diffusers=[(2.2, 1.3, 0), (5.6, 7.4, 0)], speakers=[(0.6, 7.6), (6.4, 1.2)], detector=(4.0, 5.6),
                downlight_pts=foyer_dl)
    # the downlights are real narrow spots (pools of light on the floor / portal, photo 05) - no glowing ceiling panel
    for (px, py) in foyer_dl:
        add_light(f"L_FoyerDL_{px:.0f}_{py:.0f}", 'SPOT', (px, py, z1 - 0.06), 55, WARM, size=0.05, spot=math.radians(60), blend=0.5)
    tr_ = MB()
    wall_trims(tr_, [(x1 - 0.038, x1 - 0.03, y0, y1)], z0 + 0.02, z1 - 0.02)                        # east wall: ceiling gap + skirting
    wall_trims(tr_, [(x0 - 0.15, x1, y1 - 0.008, y1)], z0 + 0.02, Z_LIV - 0.35, do_gap=True)          # wall under the mezzanine
    wall_trims(tr_, [(x0 - 0.008, x0, y0, y1)], z0 + 0.02, z1 - 0.02, do_skirt=False)                 # bulkhead face
    tr_.build("Foyer_Trims", M['black'])
    # striped painting on the east wall (photo 05) in a floater frame with a brass picture light, walnut bench + tray
    p = MB()
    floater_art(p, 1.4, 4.4, x1 - 0.03, 1.5, 3.3, along='Y', face=-1, mi_frame=0, mi_canvas=1, mi_light=2, mi_lens=3)
    p.build("Foyer_Art", [M['frame'], M['art_stripes'], M['brass'], M['emit_bar']])
    b = MB(); b.cbox(6.4, 2.9, 0.22, 0.45, 1.6, 0.44, 0)
    tray(b, 6.4, 3.3, 0.44, w=0.32, d=0.22, mi=1)
    b.lathe(6.4, 3.3, 0.452, [(0, 0), (0.05, 0), (0.08, 0.03), (0.075, 0.045), (0, 0.045)], seg=16, mi=2)   # small bowl
    for k in range(3):                                                                                         # keys
        b.cbox(6.32 + k * 0.03, 3.2, 0.457, 0.05, 0.012, 0.003, 3, rot=0.3 * k)
    books(b, 6.4, 2.45, 0.44, n=2, mi=4, rot=0.15, w=0.28, d=0.22)
    b.build("Foyer_Bench", [M['walnut'], M['black'], M['ceramic'], M['brass'], M['book']], bevel=0.012)
    # mezzanine parapet (dining edge over the void): white wall, oak cap, LED strip under the slab nose
    mp = MB()
    mp.box(-4.0, x1, y1, y1 + 0.16, Z_LIV - 0.35, Z_LIV + 1.0, 0)
    mp.box(-4.0, x1, y1 - 0.02, y1 + 0.18, Z_LIV + 1.0, Z_LIV + 1.05, 1)
    mp.build("Mezzanine_Parapet", [M['white_int'], M['oak_h']], bevel=0.01)
    box("Mezzanine_LED", -4.0, x1, y1 + 0.01, y1 + 0.06, Z_LIV - 0.35, Z_LIV - 0.33, M['emit_bar'])
    pd = MB()
    for (px, py, drop, r) in ((0.6, 4.3, 2.4, 0.14), (1.2, 5.0, 3.1, 0.11), (0.2, 5.3, 2.8, 0.09)):
        pd.cylinder(px, py, z1 - 0.02 - drop, z1 - 0.02, 0.0015, seg=6, mi=0)                                   # 3 mm cord
        pd.lathe(px, py, z1 - 0.02, [(0, -0.018), (0.03, -0.018), (0.045, -0.006), (0.045, 0), (0, 0)], seg=20, mi=2)  # brass canopy
        pd.sphere((px, py, z1 - 0.02 - drop - r), r, seg=20, rings=12, mi=1)
        pd.lathe(px, py, z1 - 0.02 - drop + 0.01, [(0, 0), (0.014, 0), (0.014, 0.03), (0, 0.03)], seg=12, mi=2)    # brass socket
    pd.build("Foyer_Pendants", [M['black_metal'], M['lampshade'], M['brass']], smooth=True)
    v = MB(); vase(v, 5.5, 1.2, 0.02, h=0.55, r=0.2, mi=0, style='round')
    v.build("Foyer_Vase", M['ceramic'], smooth=True)
    area_light("L_Foyer", (1.5, 4.5, z1 - 0.1), (8.0, 6.5), 70, WARM_SOFT)           # soft fill only (was 260: flat)
    add_light("L_FoyerArt", 'SPOT', (5.5, 2.9, z1 - 0.1), 120, WARM, size=0.05, spot=math.radians(50), blend=0.6, target=(x1, 2.9, 2.4))
    add_light("L_StairGlow", 'POINT', (STAIR_C[0], STAIR_C[1], 4.0), 60, WARM_SOFT, size=0.5)
    add_light("L_MezzStrip", 'AREA', (1.5, y1 + 0.05, Z_LIV - 0.36), 30, WARM)
    # warm wash on the portal / door from two soffit spots (photo 05: the door face glows)
    for px in (0.5, 1.8):
        add_light(f"L_FoyerPortal_{px:.0f}", 'SPOT', (px, 1.0, z1 - 0.06), 45, WARM, size=0.05, spot=math.radians(50), blend=0.6, target=(px, 0.4, 1.4))

    # ---- billiard area (west of the stair, low white ceiling, moss art wall on its west wall)
    bx0, bx1, by0, by1, bz0, bz1 = BIL
    bil_dl = [(-8.6, 2.2), (-6.5, 2.2), (-8.6, 6.6), (-6.5, 6.6)]
    ceiling_kit("Billiard_Ceiling", M, bx0, bx1, by0, by1, bz1, diffusers=[(-7.5, 1.0, 0)], speakers=[(-6.2, 7.6)], detector=(-8.8, 7.6),
                downlight_pts=bil_dl)
    for (px, py) in bil_dl:
        add_light(f"L_BilDL_{px:.0f}_{py:.0f}", 'SPOT', (px, py, bz1 - 0.05), 30, WARM, size=0.05, spot=math.radians(65), blend=0.5)
    w = MB()
    w.box(bx0 - 0.2, bx0, by0, by1, bz0, bz1, 0)                                            # wall to the garage
    w.wall('X', bx0 - 0.2, bx1, by1, by1 + 0.2, bz0, bz1, holes=[(STEP_X0, STEP_X1, LNG[4] - 0.1, bz1)], mi=0)   # opening to the lounge steps
    w.box(bx0 - 0.2, bx1, by0 - 0.02, by0, bz0, bz1, 0)                                      # front wall finish
    w.build("Billiard_Walls", M['white_int'])
    tr_ = MB()
    wall_trims(tr_, [(bx0, bx0 + 0.008, by0, by1), (bx0, bx1, by0, by0 + 0.008), (bx0, STEP_X0, by1 - 0.008, by1), (STEP_X1, bx1, by1 - 0.008, by1)], bz0 + 0.02, bz1 - 0.02)
    tr_.build("Billiard_Trims", M['black'])
    _moss_wall("Billiard_MossWall", M, bx0 + 0.01, by0 + 0.5, by1 - 0.5, bz0 + 0.25, bz1 - 0.2, n=4, seed=3)
    pt = MB()
    tcx, tcy = -7.55, 4.4
    pool_table(pt, tcx, tcy, bz0 + 0.02, rot=math.pi / 2, mi_wood=0, mi_felt=1, mi_ball=2, mi_cue=3)
    # pockets: 6 dark leather cups let into the rails (table is rotated 90 deg: 2.54 along Y, 1.42 along X)
    for (dx, dy) in ((-0.66, -1.22), (0.66, -1.22), (-0.66, 1.22), (0.66, 1.22), (-0.70, 0.0), (0.70, 0.0)):
        pt.lathe(tcx + dx, tcy + dy, bz0 + 0.02 + 0.82 + 0.061, [(0, -0.05), (0.05, -0.05), (0.062, -0.01), (0.068, 0), (0.05, 0), (0.05, -0.008), (0, -0.008)], seg=16, mi=4)
    pt.build("Pool_Table", [M['oak'], M['felt'], M['balls'], M['walnut'], M['leather_tan']], smooth=True)
    # cue rack on the front wall + a ball rack triangle
    cr = MB()
    cr.box(-9.0, -7.9, by0, by0 + 0.03, bz0 + 0.55, bz0 + 0.60, 0)
    cr.box(-9.0, -7.9, by0, by0 + 0.03, bz0 + 1.55, bz0 + 1.60, 0)
    for k in range(5):
        cx_ = -8.9 + k * 0.22
        cr.cylinder(cx_, by0 + 0.045, bz0 + 0.12, bz0 + 1.58, 0.007, 0.012, seg=8, mi=1)                     # cues (tip up)
        cr.cylinder(cx_, by0 + 0.045, bz0 + 0.12, bz0 + 0.5, 0.013, 0.013, seg=8, mi=2)                     # butt wrap
    ya, yb = by0 + 0.03, by0 + 0.055                                                                          # wooden ball-rack triangle hung on the wall
    tri = [(-7.55, ya, bz0 + 1.0), (-7.2, ya, bz0 + 1.0), (-7.375, ya, bz0 + 1.3), (-7.55, yb, bz0 + 1.0), (-7.2, yb, bz0 + 1.0), (-7.375, yb, bz0 + 1.3)]
    cr._add(tri, [(0, 2, 1), (3, 4, 5), (0, 1, 4, 3), (1, 2, 5, 4), (2, 0, 3, 5)], 0)
    cr.build("Billiard_CueRack", [M['walnut'], M['oak_pale'], M['black']])
    area_light("L_Billiard", (-7.55, 4.4, bz1 - 0.08), (2.0, 3.0), 20, WARM)         # table fill; the spots do the work
    for y in (2.4, 4.4, 6.4):                                                          # three grazing washes on the moss art
        add_light(f"L_BilliardMoss_{y:.0f}", 'SPOT', (bx0 + 0.55, y, bz1 - 0.05), 55, WARM, size=0.04, spot=math.radians(75), blend=0.7, target=(bx0, y, 0.7))


MOSS_MATS = ('moss_lime', 'moss_yellow', 'moss_olive', 'moss_deep')     # material slots 0..3 of a moss-wall object


def _moss_panels(mb, x, y0, y1, z0, z1, n=4, mi_strip=4, mi_back=5, seed=0, sign=1):
    """Preserved-moss art panels on a wall at x (facing +X when sign=1): per panel a near-black backing, then a
    dense field of rounded moss mounds (pole moss, 4-9 cm) whose tone follows an organic patch field - lime / yellow
    / olive / deep green (photo 06/07) - and a second scatter of small clumps on top of the mounds for fine relief;
    thin oak strips between the panels and top/bottom rails."""
    rng = random.Random(seed)
    w = (y1 - y0) / n
    # patch field: three products of sines with random phase / frequency -> organic 0.3-0.6 m patches in -1..1
    ph = [(rng.uniform(0, 6.3), rng.uniform(0, 6.3), rng.uniform(3.5, 7.0), rng.uniform(3.5, 7.0)) for _ in range(3)]

    def field(y, z):
        return sum(math.sin(fy * y + py) * math.sin(fz * z + pz) for (py, pz, fy, fz) in ph) / 3.0

    def tone(y, z):
        f = field(y, z) + rng.uniform(-0.12, 0.12)
        return 0 if f > 0.46 else (1 if f > 0.24 else (2 if f > -0.14 else 3))
    dx = lambda d: x + sign * d
    for i in range(n):
        ya, yb = y0 + i * w + 0.03, y0 + (i + 1) * w - 0.03
        mb.box(min(x, dx(0.02)), max(x, dx(0.02)), ya, yb, z0, z1, mi_back)
        # base layer: mounds on a jittered 6-8 cm grid; lime / yellow mounds sit a little prouder than the dark ones
        y = ya + 0.04
        while y < yb - 0.02:
            z = z0 + 0.04
            while z < z1 - 0.02:
                t = tone(y, z)
                r = rng.uniform(0.042, 0.080) * (1.12 if t < 2 else 0.92)
                mb.blob((dx(0.02 + r * 0.30), y + rng.uniform(-0.02, 0.02), z + rng.uniform(-0.02, 0.02)), r,
                        seg=7, rings=5, jitter=0.35, seed=rng.randint(0, 99999), mi=t, rx=rng.uniform(0.45, 0.7),
                        squash=rng.uniform(0.85, 1.15))
                z += rng.uniform(0.055, 0.080)
            y += rng.uniform(0.055, 0.080)
        # top layer: small clumps scattered over the mounds (fine fuzzy relief, tone follows the same patches)
        for k in range(int((yb - ya) * (z1 - z0) * 240)):
            y = rng.uniform(ya + 0.03, yb - 0.03); z = rng.uniform(z0 + 0.03, z1 - 0.03)
            t = tone(y, z)
            r = rng.uniform(0.016, 0.034)
            mb.blob((dx(rng.uniform(0.055, 0.085)), y, z), r, seg=6, rings=4, jitter=0.5, seed=rng.randint(0, 99999), mi=t,
                    rx=rng.uniform(0.6, 0.9))
        if i:
            mb.box(min(x, dx(0.10)), max(x, dx(0.10)), ya - 0.05, ya - 0.01, z0, z1, mi_strip)
    mb.box(min(x, dx(0.10)), max(x, dx(0.10)), y0 - 0.02, y1 + 0.02, z0 - 0.06, z0, mi_strip)
    mb.box(min(x, dx(0.10)), max(x, dx(0.10)), y0 - 0.02, y1 + 0.02, z1, z1 + 0.06, mi_strip)
    mb.box(min(x, dx(0.10)), max(x, dx(0.10)), y0 - 0.02, y0 + 0.02, z0, z1, mi_strip)
    mb.box(min(x, dx(0.10)), max(x, dx(0.10)), y1 - 0.02, y1 + 0.02, z0, z1, mi_strip)


def _moss_wall(name, M, x, y0, y1, z0, z1, n, seed):
    lm = local_materials(M)
    ms = MB()
    _moss_panels(ms, x, y0, y1, z0, z1, n=n, mi_strip=4, mi_back=5, seed=seed)
    return ms.build(name, [lm[k] for k in MOSS_MATS] + [M['oak'], lm['moss_back']], smooth=True)


def _bottle(mb, x, y, z, mi=0, r=0.037, h=0.30, mi_label=None, mi_foil=None, face=-1):
    """Wine bottle: body / shoulder / neck, a paper label on the room-facing side (face = -1 -> -Y), a foil cap."""
    mb.cylinder(x, y, z, z + h * 0.68, r, seg=10, mi=mi)
    mb.cylinder(x, y, z + h * 0.68, z + h * 0.85, r, r * 0.4, seg=10, mi=mi)
    mb.cylinder(x, y, z + h * 0.85, z + h, r * 0.4, seg=10, mi=mi)
    if mi_label is not None:
        ly = y + face * (r - 0.004)
        mb.box(x - 0.028, x + 0.028, min(ly, ly + face * 0.006), max(ly, ly + face * 0.006), z + h * 0.22, z + h * 0.5, mi_label)
    if mi_foil is not None:
        mb.cylinder(x, y, z + h * 0.9, z + h + 0.002, r * 0.43, seg=10, mi=mi_foil)


def _bottle_lying(mb, x, y_base, z, mi=0, r=0.037, h=0.30, mi_foil=None):
    """Wine bottle lying on a shelf along +Y: base (punt end) at y_base facing the room, neck toward the wall (+Y)."""
    zc = z + r
    mb.tube((x, y_base, zc), (x, y_base + h * 0.68, zc), r, r, seg=12, mi=mi)
    mb.tube((x, y_base + h * 0.68, zc), (x, y_base + h * 0.85, zc), r, r * 0.4, seg=12, mi=mi)
    mb.tube((x, y_base + h * 0.85, zc), (x, y_base + h, zc), r * 0.4, r * 0.4, seg=12, mi=mi)
    if mi_foil is not None:
        mb.tube((x, y_base + h * 0.9, zc), (x, y_base + h + 0.002, zc), r * 0.43, r * 0.43, seg=12, mi=mi_foil)


# ================================================================== hyper-realism detail helpers (shared with interior_main)
def face_strips(x0, x1, y0, y1, sides='WESN', d=0.008):
    """Thin strips lying on the inner faces of a rectangular room's walls (for shadow gaps / skirting)."""
    out = []
    if 'W' in sides: out.append((x0, x0 + d, y0, y1))
    if 'E' in sides: out.append((x1 - d, x1, y0, y1))
    if 'S' in sides: out.append((x0, x1, y0, y0 + d))
    if 'N' in sides: out.append((x0, x1, y1 - d, y1))
    return out


def wall_trims(mb, strips, zf, zc, mi=0, gap=0.006, skirt=0.012, do_gap=True, do_skirt=True):
    """6 mm ceiling shadow gap + 12 mm skirting shadow gap along wall-face strips (dark recess lines)."""
    for (x0, x1, y0, y1) in strips:
        if do_gap:
            mb.box(x0, x1, y0, y1, zc - gap, zc, mi)
        if do_skirt:
            mb.box(x0, x1, y0, y1, zf, zf + skirt, mi)


def ceiling_kit(name, M, x0, x1, y0, y1, zc, diffusers=(), speakers=(), detector=None, downlight_pts=(), dl_r=0.055,
                holes=(), thick=0.02, mat=None, coll='House'):
    """Ceiling slab with RECESSED linear slot diffusers (real holes: dark 40 mm deep box + 3 white grille bars),
    domed 150 mm speaker discs, a smoke detector and trimmed downlights.
    diffusers: (cx, cy, rot) with rot 0 = slot along X, 1 = along Y (must not overlap each other / holes in x)."""
    L, W = 0.6, 0.06
    slot = []
    for (cx, cy, rot) in diffusers:
        hw, hd = (L / 2, W / 2) if rot == 0 else (W / 2, L / 2)
        slot.append((cx - hw, cx + hw, cy - hd, cy + hd))
    mb = MB()
    mb.plate(x0, x1, y0, y1, zc - thick, zc, holes=sorted(list(holes) + slot), mi=0)
    zb = zc - thick
    for (hx0, hx1, hy0, hy1) in slot:
        mb.box(hx0 - 0.01, hx1 + 0.01, hy0 - 0.01, hy1 + 0.01, zb + 0.04, zc + 0.01, 1)           # dark recess back, 40 mm up
        along_x = (hx1 - hx0) > (hy1 - hy0)
        for k in range(3):                                                                          # white grille bars
            if along_x:
                yy = hy0 + (hy1 - hy0) * (k + 1) / 4
                mb.box(hx0, hx1, yy - 0.003, yy + 0.003, zb + 0.015, zb + 0.022, 0)
            else:
                xx = hx0 + (hx1 - hx0) * (k + 1) / 4
                mb.box(xx - 0.003, xx + 0.003, hy0, hy1, zb + 0.015, zb + 0.022, 0)
    for (sx, sy) in speakers:
        mb.lathe(sx, sy, zb, [(0, -0.012), (0.05, -0.010), (0.070, -0.004), (0.076, 0.0), (0, 0.0)], seg=24, mi=0)
        mb.lathe(sx, sy, zb - 0.012, [(0, -0.001), (0.012, -0.001), (0.012, 0), (0, 0)], seg=12, mi=1)   # tweeter dot
    if detector is not None:
        dx, dy = detector
        mb.lathe(dx, dy, zb, [(0, -0.022), (0.04, -0.022), (0.052, -0.012), (0.054, 0), (0, 0)], seg=20, mi=0)
        mb.lathe(dx, dy, zb - 0.022, [(0, -0.002), (0.008, -0.002), (0.008, 0), (0, 0)], seg=8, mi=4)  # tiny LED
    if downlight_pts:
        downlights(mb, downlight_pts, zb, r=dl_r, mi=2, mi_trim=3)
    return mb.build(name, [mat or M['ceiling'], M['black'], M['emit_down'], M['black_metal'], M['emit_white']], coll=coll, smooth=False)


def track(mb, x0, x1, y, z, aims, mi_track=0, mi_head=1, mi_lens=2, along='X'):
    """Recessed black track (25 mm channel) with cylindrical heads ROTATED toward `aims` [(pos_along, (ax, ay, az)), ...]."""
    if along == 'X':
        mb.box(x0, x1, y - 0.0125, y + 0.0125, z - 0.012, z + 0.01, mi_track)
    else:
        mb.box(y - 0.0125, y + 0.0125, x0, x1, z - 0.012, z + 0.01, mi_track)
    for (p, aim) in aims:
        pivot = Vector((p, y, z - 0.03)) if along == 'X' else Vector((y, p, z - 0.03))
        stem0 = Vector((pivot.x, pivot.y, z - 0.012))
        mb.tube(tuple(stem0), tuple(pivot), 0.006, 0.006, seg=6, mi=mi_head)
        d = (Vector(aim) - pivot).normalized()
        mb.tube(tuple(pivot - d * 0.01), tuple(pivot + d * 0.065), 0.022, 0.022, seg=12, mi=mi_head)
        mb.tube(tuple(pivot + d * 0.065), tuple(pivot + d * 0.07), 0.017, 0.017, seg=12, mi=mi_lens)


def door_set(mb, a0, a1, b, z0, z1, along='X', mi_leaf=0, mi_black=1, mi_plate=2, pull_side=1, plate_side=1, face=1):
    """Oak door leaf in a black 20 mm reveal frame, 1.2 m black edge pull, 3 hinge lines, a white switch plate beside it.
    along='X': opening a0..a1 in x at wall plane y=b; face = side of the wall the room is on (+1 -> +Y)."""
    d = 0.12
    if along == 'X':
        mb.box(a0 - 0.02, a0, b - d / 2, b + d / 2, z0, z1 + 0.02, mi_black)
        mb.box(a1, a1 + 0.02, b - d / 2, b + d / 2, z0, z1 + 0.02, mi_black)
        mb.box(a0 - 0.02, a1 + 0.02, b - d / 2, b + d / 2, z1, z1 + 0.02, mi_black)
        mb.box(a0 + 0.004, a1 - 0.004, b - 0.022, b + 0.022, z0, z1 - 0.004, mi_leaf)
        px = a1 - 0.04 if pull_side > 0 else a0 + 0.04
        mb.box(px - 0.01, px + 0.01, b + face * 0.022, b + face * 0.040, 0.45 + z0, 1.65 + z0, mi_black)       # edge pull
        hx = a0 + 0.004 if pull_side > 0 else a1 - 0.004
        for hz in (0.25, 1.05, 1.85):
            mb.box(hx - 0.002, hx + 0.002, b - 0.023, b + 0.023, z0 + hz, z0 + hz + 0.1, mi_black)               # hinge lines
        sx = a1 + 0.16 if plate_side > 0 else a0 - 0.16
        mb.box(sx - 0.04, sx + 0.04, b + face * 0.02, b + face * 0.026, z0 + 1.06, z0 + 1.14, mi_plate)          # switch plate
    else:
        mb.box(b - d / 2, b + d / 2, a0 - 0.02, a0, z0, z1 + 0.02, mi_black)
        mb.box(b - d / 2, b + d / 2, a1, a1 + 0.02, z0, z1 + 0.02, mi_black)
        mb.box(b - d / 2, b + d / 2, a0 - 0.02, a1 + 0.02, z1, z1 + 0.02, mi_black)
        mb.box(b - 0.022, b + 0.022, a0 + 0.004, a1 - 0.004, z0, z1 - 0.004, mi_leaf)
        py = a1 - 0.04 if pull_side > 0 else a0 + 0.04
        mb.box(b + face * 0.022, b + face * 0.040, py - 0.01, py + 0.01, 0.45 + z0, 1.65 + z0, mi_black)
        hy = a0 + 0.004 if pull_side > 0 else a1 - 0.004
        for hz in (0.25, 1.05, 1.85):
            mb.box(b - 0.023, b + 0.023, hy - 0.002, hy + 0.002, z0 + hz, z0 + hz + 0.1, mi_black)
        sy = a1 + 0.16 if plate_side > 0 else a0 - 0.16
        mb.box(b + face * 0.02, b + face * 0.026, sy - 0.04, sy + 0.04, z0 + 1.06, z0 + 1.14, mi_plate)


def floater_art(mb, a0, a1, b, z0, z1, along='X', face=1, mi_frame=0, mi_canvas=1, mi_light=None, mi_lens=None, fw=0.015, depth=0.03, gap=0.006):
    """Canvas in a floater frame: outer bars (fw wide, depth deep), a 6 mm shadow gap, a 40 mm-deep canvas set 8 mm back;
    optional slim brass picture light above with an emissive underside."""
    ib = fw + gap
    if along == 'X':
        B = lambda x0, x1, dz0, dz1, zz0, zz1, mi: mb.box(x0, x1, min(b + face * dz0, b + face * dz1), max(b + face * dz0, b + face * dz1), zz0, zz1, mi)
    else:
        B = lambda x0, x1, dz0, dz1, zz0, zz1, mi: mb.box(min(b + face * dz0, b + face * dz1), max(b + face * dz0, b + face * dz1), x0, x1, zz0, zz1, mi)
    B(a0, a1, 0.0, depth, z0, z0 + fw, mi_frame); B(a0, a1, 0.0, depth, z1 - fw, z1, mi_frame)
    B(a0, a0 + fw, 0.0, depth, z0 + fw, z1 - fw, mi_frame); B(a1 - fw, a1, 0.0, depth, z0 + fw, z1 - fw, mi_frame)
    B(a0 + ib, a1 - ib, 0.0, depth - 0.008, z0 + ib, z1 - ib, mi_canvas)
    if mi_light is not None:
        cm = (a0 + a1) / 2
        B(cm - 0.18, cm + 0.18, 0.0, 0.16, z1 + 0.14, z1 + 0.155, mi_light)
        B(cm - 0.006, cm + 0.006, 0.0, 0.012, z1 + 0.05, z1 + 0.14, mi_light)
        B(cm - 0.16, cm + 0.16, 0.10, 0.15, z1 + 0.139, z1 + 0.14, mi_lens if mi_lens is not None else mi_light)


def fireplace_insert(mb, a0, a1, b, z0, z1, along='X', faces=(1,), mi_frame=0, mi_glass=1, mi_pebble=2, mi_flame=3, depth=0.3, seed=1, n_flames=40, bed=True, bed_centre=None):
    """Linear gas fire: 40 mm black steel frame around the opening (a0..a1 x z0..z1 in the wall plane b), a glass face
    per side, a grey pebble bed and slender jittered flame tongues. faces: (+1,) or (-1,) or (1,-1) for a see-through."""
    rng = random.Random(seed)
    fw = 0.04
    for f in faces:
        off = 0.004
        if along == 'X':
            F = lambda x0, x1, zz0, zz1, mi, d0, d1: mb.box(x0, x1, min(b + f * d0, b + f * d1), max(b + f * d0, b + f * d1), zz0, zz1, mi)
        else:
            F = lambda x0, x1, zz0, zz1, mi, d0, d1: mb.box(min(b + f * d0, b + f * d1), max(b + f * d0, b + f * d1), x0, x1, zz0, zz1, mi)
        F(a0 - fw, a1 + fw, z0 - fw, z0, mi_frame, 0, 0.012); F(a0 - fw, a1 + fw, z1, z1 + fw, mi_frame, 0, 0.012)
        F(a0 - fw, a0, z0, z1, mi_frame, 0, 0.012); F(a1, a1 + fw, z0, z1, mi_frame, 0, 0.012)
        F(a0, a1, z0, z1, mi_glass, off, off + 0.006)                                              # glass face
    if not bed:
        return
    bc = b if bed_centre is None else bed_centre           # centre line of the pebble bed / flames (for see-through piers)
    for i in range(int((a1 - a0) / 0.035) * 3):
        p = rng.uniform(a0 + 0.03, a1 - 0.03)
        q = rng.uniform(-depth / 2 + 0.03, depth / 2 - 0.03)
        r = rng.uniform(0.014, 0.026)
        c = (p, bc + q, z0 + r * 0.8) if along == 'X' else (bc + q, p, z0 + r * 0.8)
        mb.blob(c, r, seg=7, rings=4, jitter=0.25, seed=i, mi=mi_pebble, squash=0.7)
    for i in range(n_flames):
        p = rng.uniform(a0 + 0.04, a1 - 0.04)
        q = rng.uniform(-0.05, 0.05)
        h = rng.uniform(0.08, 0.35) * (1.0 if rng.random() < 0.75 else 0.5)
        c = (p, bc + q) if along == 'X' else (bc + q, p)
        mb.cylinder(c[0], c[1], z0 + 0.03, z0 + 0.03 + h, rng.uniform(0.012, 0.024), 0.003, seg=6, mi=mi_flame)


def fig_plant(mb, x, y, z, pot_r=0.28, pot_h=0.42, h=1.7, mi_pot=0, mi_leaf=1, mi_stem=2, mi_soil=3, seed=0, n_leaves=14):
    """Fiddle-leaf fig: ceramic pot with soil, a woody stem, big rounded leaves (MB.pillow) at random rot / pitch."""
    rng = random.Random(seed)
    mb.lathe(x, y, z, [(0, 0), (pot_r * 0.82, 0), (pot_r * 0.95, pot_h * 0.5), (pot_r, pot_h), (pot_r * 0.9, pot_h), (pot_r * 0.9, pot_h - 0.04), (0, pot_h - 0.04)], seg=24, mi=mi_pot)
    mb.cylinder(x, y, z + pot_h - 0.045, z + pot_h - 0.035, pot_r * 0.89, seg=24, mi=mi_soil)
    top = (x + 0.04, y - 0.02, z + pot_h + h)
    mb.path_tube([(x, y, z + pot_h - 0.04), (x + 0.02, y + 0.01, z + pot_h + h * 0.5), top], 0.016, seg=7, mi=mi_stem)
    for i in range(n_leaves):
        t = 0.3 + 0.7 * i / n_leaves
        a = i * 2.4 + rng.uniform(-0.3, 0.3)
        base = (x + 0.02 * t, y + 0.01 * t, z + pot_h + h * t)
        L = rng.uniform(0.12, 0.22)
        tip = (base[0] + L * math.cos(a), base[1] + L * math.sin(a), base[2] + rng.uniform(-0.02, 0.08))
        mb.path_tube([base, tip], 0.005, seg=5, mi=mi_stem)
        w, d = rng.uniform(0.24, 0.32), rng.uniform(0.16, 0.22)
        lc = (tip[0] + (w / 2) * math.cos(a) * 0.9, tip[1] + (w / 2) * math.sin(a) * 0.9, tip[2] + 0.01)
        mb.pillow(lc[0], lc[1], lc[2], w, d, 0.012, mi_leaf, rot=a, tilt=rng.uniform(-0.25, 0.25), pitch=rng.uniform(-0.35, 0.15))


def rug(name, x0, x1, y0, y1, zf, mat, coll='House'):
    """12 mm rug slab with rounded edges; name it Rug_* so the polish stage adds fibres."""
    mb = MB()
    mb.rbox(x0, x1, y0, y1, zf + 0.002, zf + 0.014, r=0.006, seg=2)
    return mb.build(name, mat, coll=coll, smooth=True)


def sq_pillow(mb, x, y, z, w=0.5, t=0.15, mi=0, rot=0.0, lean=0.3, puff=0.55):
    """Square throw pillow standing on a seat (base at z), leaning back by `lean` (rad) toward its local +Y."""
    n0 = len(mb.v)
    mb.rbox(-w / 2, w / 2, -t / 2, t / 2, 0, w * 0.92, r=0.055, mi=mi, seg=3, puff=0.0)
    c, s_ = math.cos(rot), math.sin(rot)
    tl = math.tan(lean)
    for i in range(n0, len(mb.v)):
        vx, vy, vz = mb.v[i]
        vy = vy * (1 + puff * 0.6 * math.sin(math.pi * min(1.0, max(0.0, vz / (w * 0.92)))) * (1 - 2 * abs(vx) / w))   # belly
        vy += tl * vz
        mb.v[i] = (x + vx * c - vy * s_, y + vx * s_ + vy * c, z + vz)


_FACING = {'N': math.pi, 'S': 0.0, 'E': math.pi / 2, 'W': -math.pi / 2}     # rotation that turns local -Y toward the compass direction


def _channel_sofa(mb, x, y, w, d, facing='E', z=0.0, mi=0, seat_h=0.40, back_h=0.68, ch=0.145, arms='both', back=True, arm_w=0.20, back_d=0.24):
    """Channel-tufted low sofa (photo 07): a plinth, a seat made of front-to-back channels (rounded stuffed lofts with
    12 mm seams between them) and a back of matching vertical channels; slab arms.  Centred at (x, y), width w along
    its own X, facing `facing` (N/S/E/W).  Channels are ~145 mm wide."""
    rot = _FACING[facing]

    def B(cx, cy, cz, sx, sy, sz, r=0.05, puff=0.0):
        px, py = rot2(x + cx, y + cy, x, y, rot)
        mb.rcbox(px, py, z + cz, sx, sy, sz, r, mi, rot, puff=puff)
    hw, hd = w / 2, d / 2
    aw_l = arm_w if arms in ('both', 'left') else 0.0
    aw_r = arm_w if arms in ('both', 'right') else 0.0
    base_h = seat_h - 0.16
    B(0, 0, base_h / 2, w, d, base_h, r=0.02)                                             # plinth
    seat_w = w - aw_l - aw_r
    off = (aw_l - aw_r) / 2                                                              # seat centre shifts away from the arm
    seat_d = d - (back_d if back else 0.0) - 0.02
    n = max(1, int(round(seat_w / ch)))
    cw = seat_w / n
    for i in range(n):
        cx = off - seat_w / 2 + cw * (i + 0.5)
        B(cx, -(back_d if back else 0.0) / 2, seat_h - 0.08, cw - 0.012, seat_d, 0.17, r=0.055, puff=0.45)
    if back:
        for i in range(n):
            cx = off - seat_w / 2 + cw * (i + 0.5)
            B(cx, hd - back_d / 2, seat_h + (back_h - seat_h) / 2, cw - 0.012, back_d - 0.02, back_h - seat_h + 0.02, r=0.055, puff=0.35)
    if aw_l:
        B(-(hw - aw_l / 2), 0, (seat_h + 0.14) / 2, aw_l, d, seat_h + 0.14, r=0.05, puff=0.12)
    if aw_r:
        B(hw - aw_r / 2, 0, (seat_h + 0.14) / 2, aw_r, d, seat_h + 0.14, r=0.05, puff=0.12)


def _rock_table(mb, cx, cy, z, r, h, seed=0, n=9, mi=0):
    """Sculptural faceted 'rock' coffee table (photo 07): an irregular polygon top over slightly inset facets."""
    rng = random.Random(seed)
    top = [(cx + r * rng.uniform(0.72, 1.0) * math.cos(2 * math.pi * k / n + rng.uniform(-0.15, 0.15)),
            cy + r * rng.uniform(0.72, 1.0) * math.sin(2 * math.pi * k / n + rng.uniform(-0.15, 0.15))) for k in range(n)]
    mb.prism(top, z + h * 0.45, z + h, mi)
    base = [(cx + (px - cx) * 0.8, cy + (py - cy) * 0.8) for (px, py) in top]
    mb.prism(base, z, z + h * 0.45, mi)


def candle(mb, x, y, z, r=0.035, h=0.12, mi_wax=0, mi_flame=1):
    mb.cylinder(x, y, z, z + h, r, seg=14, mi=mi_wax)
    mb.cylinder(x, y, z + h, z + h + 0.03, 0.006, 0.001, seg=6, mi=mi_flame)


def tray(mb, x, y, z, w=0.45, d=0.3, mi=0, rot=0.0):
    mb.rcbox(x, y, z + 0.006, w, d, 0.012, r=0.005, mi=mi, rot=rot)
    mb.frame(x - w / 2, x + w / 2, y - d / 2, y + d / 2, z + 0.012, z + 0.04, 0.012, mi=mi, axis='Z')


def glassware(mb, x, y, z, kind='decanter', mi=0):
    if kind == 'decanter':
        mb.lathe(x, y, z, [(0, 0), (0.07, 0), (0.09, 0.05), (0.075, 0.14), (0.025, 0.2), (0.022, 0.3), (0.03, 0.32), (0.0, 0.32)], seg=18, mi=mi)
    elif kind == 'wine':
        mb.lathe(x, y, z, [(0, 0), (0.035, 0), (0.035, 0.005), (0.004, 0.006), (0.004, 0.09), (0.03, 0.11), (0.036, 0.16), (0.028, 0.21), (0.0, 0.21)], seg=16, mi=mi)
    else:  # tumbler
        mb.lathe(x, y, z, [(0, 0), (0.036, 0), (0.04, 0.09), (0.0, 0.09)], seg=14, mi=mi)


def piping(mb, x0, x1, y0, y1, z, r=0.006, mi=0):
    """Rounded rim (piping) around the top edge of a rectangular upholstered pad."""
    mb.rbox(x0 - r, x1 + r, y0 - r, y0 + r, z - r, z + r, r=r * 0.9, mi=mi, seg=2)
    mb.rbox(x0 - r, x1 + r, y1 - r, y1 + r, z - r, z + r, r=r * 0.9, mi=mi, seg=2)
    mb.rbox(x0 - r, x0 + r, y0, y1, z - r, z + r, r=r * 0.9, mi=mi, seg=2)
    mb.rbox(x1 - r, x1 + r, y0, y1, z - r, z + r, r=r * 0.9, mi=mi, seg=2)


def ceramics_row(mb, pts, z, mis=(0, 1, 2), seed=0):
    """Varied ceramic vessels (3 glazes) at (x, y) points."""
    rng = random.Random(seed)
    for i, (x, y) in enumerate(pts):
        k = rng.choice(('round', 'tall', 'bowl'))
        vase(mb, x, y, z, h=rng.uniform(0.1, 0.3), r=rng.uniform(0.06, 0.12), mi=mis[i % len(mis)], style=k)


def basket(mb, x, y, z, r=0.2, h=0.28, mi=0):
    mb.lathe(x, y, z, [(0, 0), (r * 0.8, 0), (r, h * 0.7), (r * 0.98, h), (r * 0.93, h), (r * 0.9, h * 0.3), (0, h * 0.28)], seg=20, mi=mi)


# ---------------------------------------------------------------- sunken lounge
def lounge(M):
    x0, x1, y0, y1, z0, z1 = LNG
    lm = local_materials(M)
    box("Lounge_Floor", x0, x1, y0, y1, z0, z0 + 0.02, lm['floor'])
    ceiling_kit("Lounge_Ceiling", M, x0, x1, y0, y1, z1, diffusers=[(-11.0, 9.6, 1), (-6.1, 9.6, 1), (-8.5, 16.7, 0)],
                speakers=[(-11.2, 12.2), (-5.9, 12.2)], detector=(-8.5, 9.2))
    tr_ = MB()
    wall_trims(tr_, [(x0 + 0.005, x0 + 0.013, y0, y1), (x1 - 0.008, x1, y0, y0 + 2.4), (x1 - 0.008, x1, y1 - 0.6, y1),
                     (x0, STEP_X0 - 0.2, y0 + 0.2, y0 + 0.208), (STEP_X1 + 0.2, x1, y0 + 0.2, y0 + 0.208)], z0 + 0.02, z1 - 0.02)
    tr_.build("Lounge_Trims", M['black'])
    # five wide travertine steps down from the billiard area, LED under each nosing
    st = MB()
    nz = 5
    for i in range(nz):
        za = -0.18 * (i + 1)
        st.box(STEP_X0, STEP_X1, y0 + 0.32 * i, y0 + 0.32 * (i + 1), z0, za + 0.18, 0)
    st.box(x0, STEP_X0, y0, y0 + 0.2, z0, z1, 1); st.box(STEP_X1, x1, y0, y0 + 0.2, z0, z1, 1)    # walls beside the opening
    st.box(STEP_X0 - 0.2, STEP_X0, y0, y0 + 1.7, z0, z0 + 0.98, 1)                                   # cheek walls
    st.box(STEP_X1, STEP_X1 + 0.2, y0, y0 + 1.7, z0, z0 + 0.98, 1)
    st.build("Lounge_Steps", [M['trav'], M['white_int']])
    led = MB()
    for i in range(nz):
        led.box(STEP_X0 + 0.05, STEP_X1 - 0.05, y0 + 0.32 * (i + 1) - 0.03, y0 + 0.32 * (i + 1), -0.18 * (i + 1) + 0.15, -0.18 * (i + 1) + 0.165)
    led.build("Lounge_StepLEDs", M['emit_bar'])
    w = MB()
    w.box(x1, x1 + 0.2, y0, y1, z0, z1, 0)                    # east wall body
    w.box(x0, x1, y1, y1 + 0.4, z0, z1, 0)                    # north wall (shared with the theatre)
    w.box(x0 - 0.02, x0 + 0.005, y0, y1, z0, z1, 0)           # west wall finish (behind the moss panels)
    w.build("Lounge_Walls", M['white_int'])
    # west wall: moss art panels (photo 06/07 left)
    _moss_wall("Lounge_MossWall", M, x0 + 0.01, y0 + 0.6, y1 - 0.6, z0 + 0.35, z1 - 0.25, n=5, seed=11)
    # ---- north wall (photo 07): backlit stratified onyx behind full-height glass doors, travertine piers either
    #      side, three bays of cantilevered bronze shelves - bottles standing on some rows, lying in cradles on others
    WX0, WX1 = x0 + 0.42, x1 - 0.42                                                    # onyx / glass span
    wn = MB()
    wn.box(WX0, WX1, y1 - 0.06, y1, z0 + 0.02, z1 - 0.02, 0)                            # onyx slab (backlit)
    wn.box(x0 + 0.05, WX0, y1 - 0.48, y1, z0 + 0.02, z1 - 0.02, 1)                     # travertine piers
    wn.box(WX1, x1 - 0.05, y1 - 0.48, y1, z0 + 0.02, z1 - 0.02, 1)
    wn.box(WX0, WX1, y1 - 0.48, y1 - 0.06, z1 - 0.10, z1 - 0.02, 2)                    # white head above the doors
    wn.box(WX0, WX1, y1 - 0.48, y1 - 0.06, z0 + 0.02, z0 + 0.06, 2)                    # sill plinth
    wn.build("Wine_Wall", [lm['onyx_wine'], M['trav'], M['white_int']])
    sh = MB(); bt = MB()
    rng = random.Random(7)
    bays = ((WX0 + 0.25, WX0 + 2.1), (WX0 + 2.4, WX1 - 2.4), (WX1 - 2.1, WX1 - 0.25))
    for row in range(5):
        z = z0 + 0.70 + row * 0.33
        lying = row in (1, 3)
        for (sa, sb) in bays:
            sh.box(sa, sb, y1 - 0.36, y1 - 0.06, z, z + 0.022, 0)                                     # 22 mm bronze shelf
            if lying:                                                                                 # bottles on their sides in wire cradles, bases to the room
                n = int((sb - sa) / 0.115)
                for i in range(n):
                    if rng.random() < 0.85:
                        bx = sa + 0.07 + i * 0.115
                        _bottle_lying(bt, bx, y1 - 0.08, z + 0.022, mi=rng.choice((0, 0, 3)), r=0.037, h=0.30, mi_foil=1 + (rng.random() < 0.5))
                        sh.box(bx - 0.045, bx + 0.045, y1 - 0.30, y1 - 0.10, z + 0.022, z + 0.03, 0)   # cradle bar
            else:
                for i in range(int((sb - sa) / 0.13)):
                    if rng.random() < 0.8:
                        _bottle(bt, sa + 0.08 + i * 0.13, y1 - 0.21, z + 0.022, rng.choice((0, 0, 3)), h=rng.uniform(0.28, 0.31),
                                mi_label=2, mi_foil=1 + (rng.random() < 0.5))
    # low console under the shelves: black steel frame with a dark wire-mesh front
    sh.box(WX0 + 0.3, WX1 - 0.3, y1 - 0.56, y1 - 0.06, z0 + 0.06, z0 + 0.58, 1)
    sh.frame(WX0 + 0.3, WX1 - 0.3, y1 - 0.57, y1 - 0.55, z0 + 0.08, z0 + 0.56, 0.02, mi=0, axis='Y')
    for k in range(int((WX1 - WX0 - 0.6) / 0.05)):                                                  # mesh: vertical rods
        xx = WX0 + 0.32 + k * 0.05
        sh.box(xx - 0.002, xx + 0.002, y1 - 0.565, y1 - 0.56, z0 + 0.08, z0 + 0.56, 0)
    sh.build("Wine_Shelves", [M['bronze'], M['black']])
    bt.build("Wine_Bottles", [lm['bottle_glass'], lm['foil_red'], M['paper'], lm['bottle_pale'], lm['foil_gold']], smooth=True)
    # full-height glass doors in a slim bronze frame (the room reflects in them, photo 07), two pulls
    gd = MB()
    gd.box(WX0 + 0.01, WX1 - 0.01, y1 - 0.47, y1 - 0.458, z0 + 0.06, z1 - 0.10, 0)
    gd.frame(WX0, WX1, y1 - 0.475, y1 - 0.453, z0 + 0.06, z1 - 0.10, 0.02, mi=1, axis='Y')
    xm = (WX0 + WX1) / 2
    gd.box(xm - 0.01, xm + 0.01, y1 - 0.475, y1 - 0.453, z0 + 0.06, z1 - 0.10, 1)                  # centre stile
    for xx in (xm - 0.06, xm + 0.06):
        gd.cylinder(xx, y1 - 0.50, z0 + 0.85, z0 + 1.35, 0.008, seg=10, mi=1)                       # bronze bar pulls
        for zz in (z0 + 0.9, z0 + 1.3):
            gd.tube((xx, y1 - 0.50, zz), (xx, y1 - 0.475, zz), 0.006, 0.006, seg=6, mi=1)
    gd.build("Wine_GlassDoors", [M['glass'], M['bronze']])
    gw = MB()
    glassware(gw, WX0 + 0.9, y1 - 0.3, z0 + 0.58, 'decanter', 0)
    for k in range(3):
        glassware(gw, WX0 + 1.25 + k * 0.11, y1 - 0.25 - (k % 2) * 0.1, z0 + 0.58, 'wine', 0)
    glassware(gw, WX1 - 0.9, y1 - 0.3, z0 + 0.58, 'decanter', 0)
    gw.build("Wine_Glassware", M['glass'], smooth=True)
    # ---- east wall: grey travertine TV wall with linear fire, oak built-ins with lit niches either side
    tvw = MB()
    tvw.box(x1 - 0.08, x1, y0 + 2.4, y1 - 2.4, z0 + 0.02, z1 - 0.02, 0)
    tvw.box(x1 - 0.30, x1 - 0.08, y0 + 3.0, y1 - 3.0, z0 + 0.42, z0 + 0.72, 1)                     # 30 cm deep black firebox
    tvw.build("Lounge_TVWall", [M['trav'], M['black']])
    fp = MB()
    fireplace_insert(fp, y0 + 3.0, y1 - 3.0, x1 - 0.08, z0 + 0.42, z0 + 0.72, along='Y', faces=(-1,), mi_frame=0, mi_glass=1, mi_pebble=2, mi_flame=3, depth=0.2, seed=5, n_flames=44)
    fp.build("Lounge_Fireplace", [M['black_metal'], M['glass'], M['pebble'], M['fire']], smooth=True)
    t = MB()
    tv(t, y0 + 3.3, y1 - 3.3, x1 - 0.08, z0 + 1.15, z0 + 2.3, 0, along='Y')
    t.box(x1 - 0.1225, x1 - 0.119, y0 + 3.3 + 0.005, y1 - 3.3 - 0.005, z0 + 1.155, z0 + 2.295, 1)    # screen panel inside a 5 mm bezel
    t.box(x1 - 0.14, x1 - 0.08, y0 + 3.6, y1 - 3.6, z0 + 1.02, z0 + 1.08, 2)                       # soundbar
    t.build("Lounge_TV", [M['black_gloss'], M['tv'], M['black']])
    bi = MB()
    for (ya, yb) in ((y0 + 1.9, y0 + 2.4), (y1 - 2.4, y1 - 0.6)):
        if yb - ya < 0.6:
            continue
        shelves(bi, x1 - 0.32, x1, ya, yb, z0 + 0.02, z1 - 0.02, n=6, t=0.03, mi=0, back=True)
        for k in range(6):
            z = z0 + 0.02 + (z1 - 0.04 - z0) * k / 6
            bi.box(x1 - 0.31, x1 - 0.3, ya + 0.04, yb - 0.04, z + 0.06, z + 0.07, 1)
            if k % 2 == 0:
                vase(bi, x1 - 0.18, ya + 0.35, z + 0.03, h=0.24, r=0.08, mi=2, style='round')
            else:
                vase(bi, x1 - 0.18, yb - 0.4, z + 0.03, h=0.12, r=0.11, mi=2, style='bowl')
    bi.build("Lounge_Builtins", [M['oak'], M['emit_bar'], M['ceramic_cream']])
    # ---- seating (photos 06/07): a long channel-tufted cream boucle sectional along the moss wall facing the TV,
    #      with a return + chaise at its south end; faceted black nesting tables; brown velvet ottoman; rug
    rug("Rug_Lounge", -11.2, -5.8, 11.4, 16.4, z0 + 0.02, M['rug'])
    sf = MB()
    _channel_sofa(sf, -10.45, 13.95, 4.9, 1.05, facing='E', z=z0 + 0.02, mi=0, arms='right')          # main run (faces the TV wall)
    _channel_sofa(sf, -9.05, 11.95, 2.0, 1.05, facing='N', z=z0 + 0.02, mi=0, arms='right', back=True)  # south return
    _channel_sofa(sf, -9.05, 16.0, 1.85, 1.05, facing='S', z=z0 + 0.02, mi=0, arms='none', back=True)   # north return
    for (px, py, mi_, rot) in ((-10.75, 12.9, 1, math.pi / 2 + 0.12), (-10.75, 14.3, 2, math.pi / 2 - 0.08), (-10.75, 15.4, 1, math.pi / 2 + 0.05),
                               (-8.4, 16.35, 2, math.pi + 0.1), (-9.6, 11.6, 1, 0.12)):
        sq_pillow(sf, px, py, z0 + 0.02 + 0.40, 0.5, 0.15, mi_, rot=rot, lean=0.3)
    sf.drape(-10.85, -10.15, 14.8, 15.6, z0 + 0.47, t=0.025, mi=3, sag=0.05, rot=0.1, folds=2, seed=4)   # throw
    sf.build("Lounge_Sectional", [lm['boucle'], M['fabric_brown'], M['fabric_taupe'], M['throw']], smooth=True, subsurf=1)
    ct = MB()
    _rock_table(ct, -8.15, 13.75, z0 + 0.02, 0.72, 0.40, seed=5)                                     # faceted black 'rock' tables
    _rock_table(ct, -7.15, 14.45, z0 + 0.02, 0.40, 0.32, seed=8)
    ct.build("Lounge_CoffeeTable", M['black'], smooth=False)
    ot = MB(); ot.cylinder(-6.85, 12.5, z0 + 0.02, z0 + 0.40, 0.52, seg=28, mi=0)
    ot.build("Lounge_Ottoman", M['fabric_brown'], smooth=True, bevel=0.06)
    dc = MB()
    zt = z0 + 0.42
    vase(dc, -8.05, 13.95, zt, h=0.34, r=0.17, mi=0, style='round')                                # hammered brass vessel + branches
    branches(dc, -8.05, 13.95, zt + 0.32, h=0.75, n=8, seed=2, mi=1, leaves=6, mi_leaf=2, spread=0.5)
    vase(dc, -8.55, 13.35, zt, h=0.08, r=0.13, mi=3, style='bowl')
    books(dc, -7.85, 13.3, zt, n=3, mi=3, rot=0.2)
    tray(dc, -7.75, 14.1, zt, w=0.3, d=0.2, mi=4, rot=0.1)
    candle(dc, -7.8, 14.12, zt + 0.012, r=0.03, h=0.09, mi_wax=5, mi_flame=6)
    candle(dc, -7.68, 14.06, zt + 0.012, r=0.025, h=0.06, mi_wax=5, mi_flame=6)
    dc.build("Lounge_Decor", [M['brass'], M['bark'], M['leaf_plant'], M['book'], M['black'], M['ceramic_cream'], M['fire']], smooth=True)
    # recessed track slots with aimed heads (photo 07) - and a real spot per head so the light actually pools
    tk = MB()
    aims = [(10.8, [(-10.8, (x0, 10.8, 0.6)), (-9.3, (-9.3, 11.9, -0.5)), (-7.8, (-7.8, 11.9, -0.5)), (-6.3, (x1, 11.5, 0.8))]),
            (13.4, [(-10.8, (x0, 13.4, 0.8)), (-9.3, (-8.2, 13.7, -0.5)), (-7.8, (-8.2, 13.7, -0.5)), (-6.3, (x1, 13.4, 1.5))]),
            (16.0, [(-10.8, (-10.8, y1, 1.2)), (-9.3, (-9.3, y1, 1.2)), (-7.8, (-7.8, y1, 1.2)), (-6.3, (-6.3, y1, 1.2))])]
    for (ty, heads) in aims:
        track(tk, x0 + 1.0, x1 - 1.0, ty, z1 - 0.02, heads)
        for (px, aim) in heads:                                                     # the wine-wall heads are dimmer: the onyx is backlit
            add_light(f"L_LoungeTrack_{px:.0f}_{ty:.0f}", 'SPOT', (px, ty, z1 - 0.06), 12 if ty > 15 else 28, WARM, size=0.03, spot=math.radians(40), blend=0.6, target=aim)
    tk.build("Lounge_Tracks", [M['black'], M['black_metal'], M['emit_white']], smooth=True)
    area_light("L_Lounge", (-8.5, 12.5, z1 - 0.1), (4.0, 4.0), 14, WARM_SOFT)      # faint fill only; spots / onyx / coves do the work
    add_light("L_LoungeFire", 'POINT', (x1 - 0.3, 12.7, z0 + 0.6), 25, (1.0, 0.5, 0.18), size=0.3)
    for y in (10.8, 12.4, 14.0, 15.6):                                              # grazing washes down the moss art
        add_light(f"L_LoungeMoss_{y:.0f}", 'SPOT', (x0 + 0.5, y, z1 - 0.08), 40, WARM, size=0.04, spot=math.radians(70), blend=0.7, target=(x0, y, -0.2))
    add_light("L_LoungeSteps", 'SPOT', ((STEP_X0 + STEP_X1) / 2, y0 + 0.8, z1 - 0.05), 45, WARM, size=0.1, spot=math.radians(90), blend=0.7)
    add_light("L_LoungeNiche", 'SPOT', (x1 - 0.6, y1 - 1.5, z1 - 0.08), 18, WARM, size=0.04, spot=math.radians(60), blend=0.7, target=(x1, y1 - 1.5, 0.5))


# ---------------------------------------------------------------- sunken home theatre
def theatre(M):
    """Sunken cinema (photo 08): black-velvet screen wall carrying a real picture, side walls that step from black
    velvet to a pale taupe acoustic panel to oak (flat boards with reveals on the S wall, dense slats on the N wall)
    separated by vertical LED strips, an oak-band ceiling with two long recessed light slots either side of a pale
    central panel, three white-leather chaises with oak cube tables in front of a long sofa on the riser, and a
    ceiling-hung projector at the back.  The screen is the key light; everything else is a warm accent."""
    x0, x1, y0, y1, z0, z1 = THR
    lm = local_materials(M)
    ym = (y0 + y1) / 2
    XV, XP, XO = x0 + 2.3, x0 + 3.5, x1                                    # velvet -> pale panel -> oak wall zones
    box("Theatre_Floor", x0, x1, y0, y1, z0, z0 + 0.02, M['carpet'])
    # ---- shell: velvet screen wall + velvet returns, black backing everywhere else (the panelling sits on it)
    w = MB()
    w.box(x0, x0 + 0.02, y0, y1, z0, z1, 0)                                                        # screen wall
    w.box(x0 + 0.02, XV, y0, y0 + 0.02, z0, z1, 0); w.box(x0 + 0.02, XV, y1 - 0.02, y1, z0, z1, 0)   # velvet returns
    w.box(XV, x1, y0, y0 + 0.02, z0, z1, 1); w.box(XV, x1, y1 - 0.02, y1, z0, z1, 1)              # black backing
    w.box(x1 - 0.02, x1, y0, y1, z0, z1, 1)
    w.box(x0, x0 + 0.6, y0, y1, z1 - 0.03, z1 - 0.02, 0)                                           # black ceiling over the screen
    w.build("Theatre_Shell", [lm['velvet_black'], M['black']])
    # ---- side-wall panelling
    pn = MB()
    for (ya, yb) in ((y0 + 0.02, y0 + 0.052), (y1 - 0.052, y1 - 0.02)):
        pn.rbox(XV + 0.02, XP - 0.02, ya, yb, z0 + 0.035, z1 - 0.03, r=0.006, mi=2, seg=2)       # pale taupe acoustic panel, 32 mm proud
    xs = [XP, x0 + 5.0, x1 - 0.8]                                                                  # vertical LED strip positions
    # S wall (camera left): flat oak boards, 5 mm dark reveals every 0.42 m; a wide board either side of each strip
    edges = sorted({XP, x1} | {x for x in xs} | {XP + 0.42 * k for k in range(1, 20) if XP + 0.42 * k < x1 - 0.05})
    for xa, xb in zip(edges[:-1], edges[1:]):
        if xb - xa < 0.05:
            continue
        pn.box(xa + 0.0025 + (0.02 if xa in xs else 0), xb - 0.0025 - (0.02 if xb in xs else 0), y0 + 0.02, y0 + 0.045, z0 + 0.035, z1 - 0.03, 0)
    # N wall (camera right): dense vertical oak slats 40 x 28 mm on an 80 mm pitch (skipping the strips)
    xx = XP + 0.05
    while xx < x1 - 0.05:
        if all(abs(xx - sx) > 0.05 for sx in xs):
            pn.box(xx - 0.02, xx + 0.02, y1 - 0.048, y1 - 0.02, z0 + 0.035, z1 - 0.03, 1)
        xx += 0.08
    # E wall (behind the seats): oak boards with reveals
    for k in range(int((y1 - y0) / 0.42) + 1):
        ya = y0 + 0.42 * k
        yb = min(y1, ya + 0.42)
        pn.box(x1 - 0.045, x1 - 0.02, ya + 0.0025, yb - 0.0025, z0 + 0.035, z1 - 0.03, 0)
    # vertical LED strips: 30 mm emissive bar in a 40 mm black recess, S and N walls
    for x in xs:
        for (ya, yb) in ((y0 + 0.02, y0 + 0.032), (y1 - 0.032, y1 - 0.02)):
            pn.box(x - 0.015, x + 0.015, ya, yb, z0 + 0.35, z1 - 0.35, 3)
    pn.build("Theatre_Panelling", [lm['oak_dark'], lm['oak_dark'], lm['acoustic_pale'], lm['emit_strip']])
    tr_ = MB()
    wall_trims(tr_, [(XV, x1, y0 + 0.02, y0 + 0.05), (XV, x1, y1 - 0.05, y1 - 0.02), (x1 - 0.05, x1 - 0.02, y0, y1)], z0 + 0.02, z1 - 0.02)
    tr_.build("Theatre_Trims", M['black'])
    # ---- ceiling: pale base with two downlights over the screen, oak bands dropping 70 mm with LED slots at their inner edges
    YS = 1.25                                                                                       # slot half-spacing from the room axis
    ceiling_kit("Theatre_Ceiling", M, x0, x1, y0, y1, z1, diffusers=[(x1 - 0.5, ym - 0.6, 1)], speakers=[(x0 + 2.4, ym), (x0 + 4.9, ym)],
                detector=(x1 - 0.5, ym + 0.9), downlight_pts=[(x0 + 1.1, y0 + 1.1), (x0 + 1.1, y1 - 1.1)], dl_r=0.04)
    cb = MB()
    for (ya, yb) in ((y0 + 0.05, ym - YS), (ym + YS, y1 - 0.05)):
        cb.box(x0 + 0.6, x1 - 0.05, ya, yb, z1 - 0.09, z1 - 0.02, 0)                                # oak band
    cb.box(x0 + 0.6, x1 - 0.05, ym - YS + 0.10, ym + YS - 0.10, z1 - 0.045, z1 - 0.02, 1)          # central pale acoustic panel (25 mm proud)
    cb.build("Theatre_CeilingBands", [lm['oak_ceiling_dark'], lm['acoustic_pale']])
    sl = MB()
    for (ya, yb) in ((ym - YS, ym - YS + 0.06), (ym + YS - 0.06, ym + YS)):
        sl.box(x0 + 0.65, x1 - 0.1, ya, yb, z1 - 0.025, z1 - 0.02, 0)                              # recessed LED slot
    for yy in (y0 + 0.6, y0 + 2.0, y0 + 3.4, y1 - 0.6):
        sl.box(x0 + 3.99, x0 + 4.0, yy - 0.06, yy + 0.06, z0 + 0.2, z0 + 0.215, 0)                  # riser step lights
    sl.build("Theatre_Slots", lm['emit_slot'])
    # ---- surround speakers (fabric boxes high on the side walls) + soundbar under the screen
    ac = MB()
    for (sx, sy, d_) in ((x0 + 4.3, y0 + 0.03, 1), (x0 + 4.3, y1 - 0.03, -1), (x0 + 1.5, y0 + 0.03, 1), (x0 + 1.5, y1 - 0.03, -1)):
        ac.box(sx - 0.09, sx + 0.09, min(sy, sy + d_ * 0.1), max(sy, sy + d_ * 0.1), z0 + 1.75, z0 + 2.03, 1)
        ac.box(sx - 0.07, sx + 0.07, min(sy + d_ * 0.1, sy + d_ * 0.104), max(sy + d_ * 0.1, sy + d_ * 0.104), z0 + 1.8, z0 + 1.98, 0)   # grille
    ac.box(x0 + 0.08, x0 + 0.14, ym - 0.6, ym + 0.6, z0 + 0.42, z0 + 0.49, 1)                       # soundbar under the screen
    ac.build("Theatre_Acoustics", [M['fabric_dark'], M['black']])
    # ---- screen: black velvet frame on the velvet wall; the picture is its OWN object so its Generated coords map the frame
    SW = 3.9; SH = SW * 9 / 16; ZS = z0 + 0.56
    sc = MB()
    sc.frame(x0 + 0.05, x0 + 0.08, ym - SW / 2 - 0.06, ym + SW / 2 + 0.06, ZS - 0.06, ZS + SH + 0.06, 0.06, mi=0, axis='X')
    sc.build("Theatre_ScreenFrame", lm['velvet_black'])
    box("Theatre_Screen", x0 + 0.05, x0 + 0.062, ym - SW / 2, ym + SW / 2, ZS, ZS + SH, lm['screen'])
    box("Theatre_Riser", x0 + 4.0, x1 - 0.05, y0 + 0.05, y1 - 0.05, z0 + 0.02, z0 + 0.32, M['carpet'])
    # ---- front row (photo 08): white leather modular chaises - a low plinth, a thick piped seat pad, a low back with a
    # rolled headrest and padded arms on the aisle sides, oak cube tables between them
    se = MB()
    for i in range(3):
        y = y0 + 1.25 + i * 1.6
        se.rbox(x0 + 1.7, x0 + 3.3, y - 0.44, y + 0.44, z0 + 0.03, z0 + 0.30, r=0.04, mi=0)                    # plinth
        se.rbox(x0 + 1.74, x0 + 2.98, y - 0.40, y + 0.40, z0 + 0.30, z0 + 0.50, r=0.07, mi=0, puff=0.4)       # seat pad
        piping(se, x0 + 1.78, x0 + 2.94, y - 0.36, y + 0.36, z0 + 0.495, r=0.006, mi=2)
        se.rbox(x0 + 2.96, x0 + 3.34, y - 0.40, y + 0.40, z0 + 0.30, z0 + 0.86, r=0.07, mi=0, puff=0.3)       # low back cushion
        piping(se, x0 + 2.99, x0 + 3.31, y - 0.36, y + 0.36, z0 + 0.855, r=0.006, mi=2)
        se.rbox(x0 + 2.98, x0 + 3.20, y - 0.26, y + 0.26, z0 + 0.84, z0 + 0.95, r=0.05, mi=0, puff=0.5)        # rolled headrest
        se.rbox(x0 + 1.7, x0 + 3.3, y - 0.52, y - 0.44, z0 + 0.30, z0 + 0.62, r=0.035, mi=0, puff=0.2)        # padded arms
        se.rbox(x0 + 1.7, x0 + 3.3, y + 0.44, y + 0.52, z0 + 0.30, z0 + 0.62, r=0.035, mi=0, puff=0.2)
    for y in (y0 + 2.05, y0 + 3.65):
        se.cbox(x0 + 2.5, y, z0 + 0.25, 1.1, 0.5, 0.46, 1)                                                     # oak cube tables between the chaises
        se.lathe(x0 + 2.85, y, z0 + 0.48, [(0, -0.05), (0.04, -0.05), (0.045, 0), (0, 0)], seg=14, mi=2)      # cup holder
    for y in (y0 + 0.45, y1 - 0.45):
        se.cbox(x0 + 2.5, y, z0 + 0.25, 1.1, 0.5, 0.46, 1)                                                     # end tables
    # a folded cashmere throw over the middle chaise's arm, a wine glass and a remote on the cube tables
    yt = y0 + 1.25 + 1.6
    se.rcbox(x0 + 2.35, yt + 0.44, z0 + 0.66, 0.42, 0.20, 0.07, r=0.03, mi=5, puff=0.35)                       # over the arm
    se.rcbox(x0 + 2.35, yt + 0.55, z0 + 0.42, 0.40, 0.05, 0.42, r=0.02, mi=5, puff=0.25)                       # hanging fold
    se.rcbox(x0 + 2.35, yt + 0.30, z0 + 0.535, 0.44, 0.24, 0.05, r=0.02, mi=5, puff=0.3)                       # fold on the seat
    glassware(se, x0 + 2.25, y0 + 2.05, z0 + 0.48, kind='wine', mi=6)
    se.rcbox(x0 + 2.55, y0 + 3.72, z0 + 0.49, 0.045, 0.17, 0.018, r=0.006, mi=3, rot=0.25)                     # remote
    # back row: long white leather sofa on the riser, oak trays, popcorn
    sofa(se, x0 + 5.4, ym, y1 - y0 - 0.9, 1.1, rot=math.pi / 2, z=z0 + 0.32, mi_seat=0, cushion_gap=0.03, arms=True, arm_w=0.25, back_h=0.9, seat_h=0.45, soft=0.07)
    for y in (y0 + 1.3, y0 + 3.1, y1 - 1.3):
        se.cbox(x0 + 4.35, y, z0 + 0.54, 0.5, 0.6, 0.44, 1)
        se.lathe(x0 + 4.35, y - 0.15, z0 + 0.76, [(0, -0.05), (0.04, -0.05), (0.045, 0), (0, 0)], seg=14, mi=2)
    se.lathe(x0 + 4.35, y0 + 3.25, z0 + 0.76, [(0, 0), (0.09, 0), (0.13, 0.08), (0.135, 0.1), (0, 0.1)], seg=18, mi=3)   # popcorn bowl
    rng = random.Random(21)
    for k in range(26):
        se.blob((x0 + 4.35 + rng.uniform(-0.09, 0.09), y0 + 3.25 + rng.uniform(-0.09, 0.09), z0 + 0.86 + rng.uniform(0, 0.03)), 0.014, seg=6, rings=4, jitter=0.5, seed=k, mi=4)
    se.build("Theatre_Seating", [lm['leather_white'], M['oak'], M['leather_tan'], M['ceramic_black'], M['paper'], lm['cashmere'], M['glass_tint']], smooth=True, bevel=0.02)
    # ---- projector: a large black unit hung from the ceiling at the back on a pole mount, lens toward the screen
    pj = MB()
    px, py = x0 + 2.7, y1 - 1.3
    pj.rcbox(px, py, z1 - 0.58, 0.56, 0.46, 0.20, r=0.02, mi=0)
    pj.cylinder(px + 0.05, py, z1 - 0.48, z1 - 0.02, 0.025, seg=10, mi=0)
    pj.cylinder(px + 0.05, py, z1 - 0.06, z1 - 0.02, 0.09, seg=16, mi=0)                             # ceiling plate
    pj.tube((px - 0.28, py, z1 - 0.58), (px - 0.33, py, z1 - 0.58), 0.055, 0.05, seg=16, mi=0)       # lens barrel
    pj.tube((px - 0.33, py, z1 - 0.58), (px - 0.335, py, z1 - 0.58), 0.045, 0.045, seg=16, mi=1)     # lens glass
    for k in range(6):                                                                               # vent slots
        pj.box(px + 0.10, px + 0.24, py - 0.23, py - 0.225, z1 - 0.65 + 0.025 * k, z1 - 0.64 + 0.025 * k, 2)
    pj.build("Theatre_Projector", [M['black'], M['glass_tint'], M['black_metal']])
    # ---- lights: the screen is the key (a wide area light coloured by the picture), slots + strips are warm accents
    sr, sg, sb = lm['screen_avg']
    area_light("L_TheatreScreen", (x0 + 0.14, ym, ZS + SH / 2), (SW * 0.9, SH * 0.9), 14, (sr, sg, sb), target=(x1, ym, z0 + 0.7), spread=math.radians(120))
    for (yy, sgn) in ((ym - YS + 0.03, 1), (ym + YS - 0.03, -1)):
        area_light(f"L_TheatreSlot_{sgn}", ((x0 + x1) / 2 + 0.3, yy, z1 - 0.03), (x1 - x0 - 0.8, 0.05), 3.5, (1.0, 0.80, 0.55))
    for (px_, py_) in ((x0 + 1.1, y0 + 1.1), (x0 + 1.1, y1 - 1.1)):
        add_light(f"L_TheatreDL_{px_:.0f}_{py_:.0f}", 'SPOT', (px_, py_, z1 - 0.05), 6, WARM, size=0.03, spot=math.radians(50), blend=0.6)
    for x in xs:                                                                                    # the vertical wall strips glow onto the oak
        for (yy, sgn) in ((y0 + 0.06, 1), (y1 - 0.06, -1)):
            area_light(f"L_TheatreStrip_{x:.0f}_{sgn}", (x, yy, (z0 + z1) / 2), (0.03, z1 - z0 - 0.8), 2.5, WARM, target=(x, yy + sgn * 1.0, (z0 + z1) / 2))


def build(M):
    local_materials(M)
    spiral_stair(M)
    foyer(M)
    lounge(M)
    theatre(M)
    x0, x1, y0, y1, z0, z1 = GAR
    box("Garage_Floor", x0, x1, y0, y1, z0, z0 + 0.02, M['concrete'])
    box("Garage_Ceiling", x0, x1, y0, y1, z1 - 0.02, z1, M['ceiling'])
    area_light("L_Garage", ((x0 + x1) / 2, (y0 + y1) / 2, z1 - 0.1), (2, 4), 30, WARM_SOFT)
