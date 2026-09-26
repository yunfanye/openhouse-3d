"""Dusk sky + sun (a clear evening a few minutes after sunset: the horizon glows orange-pink under a band of
pink-lit altocumulus streaks, the zenith is a soft blue).  Graded Nishita sky + two procedural cloud layers + haze.

setup_world(scene, sun_dir=...) builds the world node tree; setup_sun(sun_dir=...) the sun lamp.  The house picks the
sun direction (a unit vector TOWARD the sun) in house.py SKY; tools/sky_test.py renders the sky alone.
"""
import math
import bpy
from mathutils import Vector
from .lights import add_light

SUN_DIR = Vector((-0.80, -0.45, 0.16)).normalized()      # default: west-south-west, just above the ridge


def setup_sun(energy=2.2, color=(1.0, 0.80, 0.62), sun_dir=None):
    sun_dir = Vector(sun_dir).normalized() if sun_dir is not None else SUN_DIR
    sun = add_light("Sun", 'SUN', (0, 0, 30), energy, color=color)
    sun.data.angle = math.radians(3.5)
    sun.rotation_euler = (-sun_dir).to_track_quat('-Z', 'Y').to_euler()
    return sun


def _n(nt, kind, **kw):
    n = nt.nodes.new(kind)
    for k, v in kw.items():
        setattr(n, k, v)
    return n


def _math(nt, op, a, b=None, clamp=False):
    n = nt.nodes.new("ShaderNodeMath"); n.operation = op; n.use_clamp = clamp
    if hasattr(a, "is_linked"):
        nt.links.new(n.inputs[0], a)
    else:
        n.inputs[0].default_value = a
    if b is not None:
        if hasattr(b, "is_linked"):
            nt.links.new(n.inputs[1], b)
        else:
            n.inputs[1].default_value = b
    return n.outputs[0]


def _ramp(nt, fac, stops):
    r = nt.nodes.new("ShaderNodeValToRGB")
    el = r.color_ramp.elements
    while len(el) < len(stops):
        el.new(0.5)
    for e, (p, c) in zip(el, stops):
        e.position = p; e.color = c
    nt.links.new(r.inputs["Fac"], fac)
    return r.outputs["Color"]


def _mix(nt, fac, a, b, blend='MIX'):
    m = nt.nodes.new("ShaderNodeMix"); m.data_type = 'RGBA'; m.blend_type = blend
    if hasattr(fac, "is_linked"):
        nt.links.new(m.inputs["Factor"], fac)
    else:
        m.inputs["Factor"].default_value = fac
    for sock, v in (("A", a), ("B", b)):
        if hasattr(v, "is_linked"):
            nt.links.new(m.inputs[sock], v)
        else:
            m.inputs[sock].default_value = v
    return m.outputs["Result"]


def _noise(nt, vec, scale, detail=4.0, rough=0.5, distortion=0.0):
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = scale; n.inputs["Detail"].default_value = detail
    n.inputs["Roughness"].default_value = rough; n.inputs["Distortion"].default_value = distortion
    nt.links.new(n.inputs["Vector"], vec)
    return n.outputs["Fac"]


def _mapped(nt, vec, scale=(1, 1, 1), loc=(0, 0, 0)):
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = scale; mp.inputs["Location"].default_value = loc
    nt.links.new(mp.inputs["Vector"], vec)
    return mp.outputs["Vector"]


def setup_world(scene, strength=0.55, sun_elevation=1.2, sun_dir=None):
    sun_dir = Vector(sun_dir).normalized() if sun_dir is not None else SUN_DIR
    W = bpy.data.worlds.new("World")
    scene.world = W
    W.use_nodes = True
    nt = W.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = strength

    # --- clear-sky base: Nishita with the sun on the horizon (warm band low, blue above), hazy evening air
    sky = nt.nodes.new("ShaderNodeTexSky")
    sky.sky_type = 'MULTIPLE_SCATTERING'
    sky.sun_disc = False
    sky.sun_elevation = math.radians(sun_elevation)
    sky.sun_rotation = math.atan2(-sun_dir.x, sun_dir.y)
    sky.altitude = 60
    sky.air_density = 1.15
    sky.aerosol_density = 3.6
    sky.ozone_density = 2.4
    sky.sun_intensity = 1.0

    tc = nt.nodes.new("ShaderNodeTexCoord")
    d = tc.outputs["Generated"]
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(sep.inputs["Vector"], d)
    up = sep.outputs["Z"]                                   # sin(elevation)
    # how much this direction faces the sun (0..1): lights the cloud edges and warms the sky on that side
    dot = nt.nodes.new("ShaderNodeVectorMath"); dot.operation = 'DOT_PRODUCT'
    nt.links.new(dot.inputs[0], d); dot.inputs[1].default_value = tuple(sun_dir)
    toward = _math(nt, 'MULTIPLY', _math(nt, 'ADD', dot.outputs["Value"], 1.0), 0.5, clamp=True)

    # --- grade the Nishita result toward the photos: peach-pink low, lavender-blue high, a touch brighter overall
    grade = _ramp(nt, up, [(0.0, (1.30, 0.92, 0.84, 1)), (0.10, (1.12, 0.96, 0.98, 1)), (0.35, (0.80, 0.86, 1.05, 1)), (1.0, (0.62, 0.72, 1.0, 1))])
    base = _mix(nt, 1.0, sky.outputs["Color"], grade, 'MULTIPLY')
    # gentle overall lift so the sky never renders as a flat dark gradient behind the roof line
    base = _mix(nt, 1.0, base, (1.35, 1.35, 1.35, 1), 'MULTIPLY')

    # --- clouds: two altocumulus/stratus layers, stretched horizontally, compressed toward the horizon
    # (a flat sheet of cloud seen from below foreshortens near the horizon: scale Z up, XY down)
    def layer(scale_xy, scale_z, loc, lo, hi, detail=8.0, distortion=1.0):
        v = _mapped(nt, d, scale=(scale_xy, scale_xy, scale_z), loc=loc)
        n = _noise(nt, v, scale=1.0, detail=detail, rough=0.62, distortion=distortion)
        mr = nt.nodes.new("ShaderNodeMapRange"); mr.clamp = True
        mr.inputs["From Min"].default_value = lo; mr.inputs["From Max"].default_value = hi
        nt.links.new(mr.inputs["Value"], n)
        return mr.outputs["Result"], n
    dens1, n1 = layer(2.0, 9.0, (0.3, 0.1, 0.0), 0.50, 0.585, detail=9.0, distortion=0.8)    # broad streaks
    dens2, n2 = layer(5.5, 18.0, (1.7, 0.4, 0.2), 0.52, 0.63, detail=7.0, distortion=0.4)    # smaller puffs
    dens = _math(nt, 'ADD', _math(nt, 'MULTIPLY', dens1, 0.85), _math(nt, 'MULTIPLY', dens2, 0.6), clamp=True)
    # clouds live between ~3 and ~40 degrees elevation, fading out toward the zenith and cut off below the horizon
    band = _ramp(nt, up, [(0.0, (0, 0, 0, 1)), (0.04, (1, 1, 1, 1)), (0.35, (1, 1, 1, 1)), (0.75, (0, 0, 0, 1))])
    bsep = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(bsep.inputs["Color"], band)
    dens = _math(nt, 'MULTIPLY', dens, bsep.outputs["Red"])
    # cloud colour: the sun sits at the horizon so cloud BASES are lit pink-gold near it and go mauve away from
    # it; the thick cores (high noise) are a little darker than the wispy edges
    lit = _ramp(nt, toward, [(0.3, (0.66, 0.58, 0.70, 1)), (0.6, (1.25, 0.86, 0.80, 1)), (1.0, (1.75, 1.15, 0.85, 1))])
    core = _ramp(nt, n1, [(0.5, (1.0, 1.0, 1.0, 1)), (0.75, (0.72, 0.68, 0.72, 1))])
    ccol = _mix(nt, 1.0, lit, core, 'MULTIPLY')
    # low clouds get the horizon's orange, high ones stay pinker
    hcol = _ramp(nt, up, [(0.0, (1.15, 0.85, 0.70, 1)), (0.25, (1.0, 1.0, 1.0, 1))])
    ccol = _mix(nt, 1.0, ccol, hcol, 'MULTIPLY')
    col = _mix(nt, dens, base, ccol)
    # thin haze band right at the horizon (dust / distant smoke): a warm, slightly desaturated glow
    haze = _ramp(nt, up, [(0.0, (1.0, 1.0, 1.0, 1)), (0.06, (0, 0, 0, 1))])
    hsep = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(hsep.inputs["Color"], haze)
    col = _mix(nt, _math(nt, 'MULTIPLY', hsep.outputs["Red"], 0.45), col, (1.25, 0.95, 0.80, 1))
    nt.links.new(bg.inputs["Color"], col)
    nt.links.new(out.inputs["Surface"], bg.outputs["Background"])
    return W


def setup_day(scene, sun_dir=(0.5, -0.6, 0.6), sun_energy=3.6, strength=1.0, sun_color=(1.0, 0.95, 0.88),
              sun_angle=1.2, clouds=0.35, haze=1.0, deepen=0.0, shade_warm=0.0):
    """Clear daylight for listing-photo matches: a physically based sky (multiple scattering) lit by the existing
    'Sun' lamp (re-aimed along `sun_dir`, a unit vector TOWARD the sun), faint fair-weather cloud streaks, no disc.
    Replaces the world built by setup_world()."""
    sd = Vector(sun_dir).normalized()
    sun = bpy.data.objects.get("Sun")
    if sun is None:
        sun = setup_sun(energy=sun_energy, color=sun_color, sun_dir=sd)
    sun.data.energy = sun_energy
    sun.data.color = sun_color
    sun.data.angle = math.radians(sun_angle)
    sun.rotation_euler = (-sd).to_track_quat('-Z', 'Y').to_euler()
    W = bpy.data.worlds.new("WorldDay")
    scene.world = W
    W.use_nodes = True
    nt = W.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = strength
    sky = nt.nodes.new("ShaderNodeTexSky")
    sky.sky_type = 'MULTIPLE_SCATTERING'
    sky.sun_disc = False
    sky.sun_elevation = math.asin(max(0.02, sd.z))
    sky.sun_rotation = math.atan2(-sd.x, sd.y)
    sky.altitude = 250
    sky.air_density = 1.0
    sky.aerosol_density = 1.2 * haze
    sky.ozone_density = 1.0
    sky.sun_intensity = 1.0
    col = sky.outputs["Color"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    d = tc.outputs["Generated"]
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(sep.inputs["Vector"], d)
    up = sep.outputs["Z"]
    if deepen > 0:
        # polarised listing-photo sky: bluer and deeper with elevation, the horizon left pale.  Only camera rays see
        # the deepened colour; the light the sky casts into shade stays the physical (paler) sky, so shaded walls do
        # not turn blue.
        k = deepen
        grade = _ramp(nt, up, [(0.0, (1.0, 1.0, 1.0, 1)), (0.12, (1 - 0.12 * k, 1 - 0.06 * k, 1.0 + 0.02 * k, 1)),
                                (0.45, (1 - 0.32 * k, 1 - 0.18 * k, 1.0 + 0.05 * k, 1)), (1.0, (1 - 0.45 * k, 1 - 0.28 * k, 1.0, 1))])
        seen = _mix(nt, 1.0, col, grade, 'MULTIPLY')
        lp = nt.nodes.new("ShaderNodeLightPath")
        lit = _mix(nt, 1.0, col, (1.0 + 0.25 * shade_warm, 1.0 + 0.12 * shade_warm, 1.0 - 0.1 * shade_warm, 1), 'MULTIPLY')
        col = _mix(nt, lp.outputs["Is Camera Ray"], lit, seen)
    if clouds > 0:
        v = _mapped(nt, d, scale=(2.2, 2.2, 10.0), loc=(0.4, 0.2, 0.0))
        n = _noise(nt, v, scale=1.0, detail=8.0, rough=0.6, distortion=0.6)
        mr = nt.nodes.new("ShaderNodeMapRange"); mr.clamp = True
        mr.inputs["From Min"].default_value = 0.54; mr.inputs["From Max"].default_value = 0.66
        nt.links.new(mr.inputs["Value"], n)
        band = _ramp(nt, up, [(0.0, (0, 0, 0, 1)), (0.06, (1, 1, 1, 1)), (0.45, (1, 1, 1, 1)), (0.85, (0, 0, 0, 1))])
        bs = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(bs.inputs["Color"], band)
        dens = _math(nt, 'MULTIPLY', _math(nt, 'MULTIPLY', mr.outputs["Result"], bs.outputs["Red"]), clouds)
        # cloud brightness tracks the sky luminance near the horizon so it stays plausible under any exposure
        white = _mix(nt, 1.0, col, (2.4, 2.4, 2.5, 1), 'MULTIPLY')
        col = _mix(nt, dens, col, white)
    nt.links.new(bg.inputs["Color"], col)
    nt.links.new(out.inputs["Surface"], bg.outputs["Background"])
    return W


# ------------------------------------------------------------------ photo-matched sky seen by camera rays only
def camera_sky(world, gradient, features=(), scale=4.0, name="CamSky"):
    """Make CAMERA rays of `world` see a photo-matched sky; every other ray (the light the sky casts, reflections)
    keeps the world's own colour, so walls do not turn blue.  Returns the gain Math node (inputs[1] = a multiplier,
    e.g. 2 ** -exposure, so display-referred targets stay put under a per-camera exposure).

    gradient  [(sin_elevation, (r, g, b)), ...] scene-linear colours (any magnitude; divided by `scale` for the ramp)
    features  sky-plane shapes (p = (d.x / d.z, d.y / d.z), direction-only, so they sit at infinity):
      dict(kind='blob', c=(x, y), b1=(x, y), b2=(x, y), color=(r, g, b), alpha=1.0, soft=0.35, noise=0.45, freq=6.0,
           shade=(r, g, b), shade_amt=0.0)          b1 / b2 = dual basis: (p - c).b1, (p - c).b2 are the ellipse coords
      dict(kind='streak', a=(x, y), b=(x, y), width=w, color=(r, g, b), alpha=1.0, noise=0.6, along=3.0, across=2.0)
          a line from a to b of half-width w (sky-plane units), feathered by an anisotropic noise (cirrus / contrails)
    """
    nt = world.node_tree
    out = next(n for n in nt.nodes if n.type == 'OUTPUT_WORLD')
    bg = next(n for n in nt.nodes if n.type == 'BACKGROUND')
    lit = bg.inputs["Color"].links[0].from_socket if bg.inputs["Color"].is_linked else None
    lit_default = tuple(bg.inputs["Color"].default_value)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nrm = nt.nodes.new("ShaderNodeVectorMath"); nrm.operation = 'NORMALIZE'
    nt.links.new(nrm.inputs[0], tc.outputs["Generated"])
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(sep.inputs["Vector"], nrm.outputs["Vector"])
    zc = _math(nt, 'MAXIMUM', sep.outputs["Z"], 0.03)
    px, py = _math(nt, 'DIVIDE', sep.outputs["X"], zc), _math(nt, 'DIVIDE', sep.outputs["Y"], zc)
    P = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(P.inputs["X"], px); nt.links.new(P.inputs["Y"], py)
    P = P.outputs["Vector"]
    # base gradient on sin(elevation)
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    el = ramp.color_ramp.elements
    stops = sorted(gradient)
    while len(el) < len(stops):
        el.new(0.5)
    for e, (pos, c) in zip(el, stops):
        e.position = max(0.0, min(1.0, pos))
        e.color = (c[0] / scale, c[1] / scale, c[2] / scale, 1.0)
    nt.links.new(ramp.inputs["Fac"], _math(nt, 'MAXIMUM', sep.outputs["Z"], 0.0))
    col = _mix(nt, 1.0, ramp.outputs["Color"], (scale, scale, scale, 1), 'MULTIPLY')

    def vsub(a, b):
        n = nt.nodes.new("ShaderNodeVectorMath"); n.operation = 'SUBTRACT'
        nt.links.new(n.inputs[0], a); n.inputs[1].default_value = (b[0], b[1], 0.0)
        return n.outputs["Vector"]

    def vdot(a, b):
        n = nt.nodes.new("ShaderNodeVectorMath"); n.operation = 'DOT_PRODUCT'
        nt.links.new(n.inputs[0], a); n.inputs[1].default_value = (b[0], b[1], 0.0)
        return n.outputs["Value"]

    def mrange(v, a, b, c, d, smooth=True):
        n = nt.nodes.new("ShaderNodeMapRange"); n.clamp = True
        if smooth:
            n.interpolation_type = 'SMOOTHSTEP'
        nt.links.new(n.inputs["Value"], v)
        n.inputs["From Min"].default_value, n.inputs["From Max"].default_value = a, b
        n.inputs["To Min"].default_value, n.inputs["To Max"].default_value = c, d
        return n.outputs["Result"]

    for i, f in enumerate(features):
        if f['kind'] == 'blob':
            q = vsub(P, f['c'])
            u1, u2 = vdot(q, f['b1']), vdot(q, f['b2'])
            cmb = nt.nodes.new("ShaderNodeCombineXYZ")
            nt.links.new(cmb.inputs["X"], u1); nt.links.new(cmb.inputs["Y"], u2)
            ln = nt.nodes.new("ShaderNodeVectorMath"); ln.operation = 'LENGTH'
            nt.links.new(ln.inputs[0], cmb.outputs["Vector"])
            nz = _noise(nt, _mapped(nt, cmb.outputs["Vector"], scale=(f.get('freq', 6.0),) * 3, loc=(i * 7.3, i * 3.1, 0.0)),
                        1.0, detail=8.0, rough=0.62)
            r = _math(nt, 'ADD', ln.outputs["Value"], _math(nt, 'MULTIPLY', _math(nt, 'SUBTRACT', nz, 0.5), f.get('noise', 0.45)))
            soft = f.get('soft', 0.35)
            a = _math(nt, 'MULTIPLY', mrange(r, 1.0 - soft, 1.0, 1.0, 0.0), f.get('alpha', 1.0))
            ccol = f['color']
            if f.get('shade_amt', 0.0) > 0:
                # shaded belly: lower in the ellipse (u2 < 0 when b2 points up) and deeper inside
                s = _math(nt, 'MULTIPLY', mrange(u2, 0.3, -0.9, 0.0, 1.0), mrange(r, 0.9, 0.2, 0.0, 1.0))
                ccol = _mix(nt, _math(nt, 'MULTIPLY', s, f['shade_amt']), (*f['color'], 1), (*f['shade'], 1))
            else:
                ccol = (*ccol, 1)
            col = _mix(nt, a, col, ccol)
        else:
            ax, ay = f['a']; bx, by = f['b']
            dx, dy = bx - ax, by - ay
            L2 = dx * dx + dy * dy
            L = L2 ** 0.5
            q = vsub(P, f['a'])
            t = vdot(q, (dx / L2, dy / L2))
            e = vdot(q, (-dy / L / f['width'], dx / L / f['width']))
            cmb = nt.nodes.new("ShaderNodeCombineXYZ")
            nt.links.new(cmb.inputs["X"], _math(nt, 'MULTIPLY', t, f.get('along', 3.0)))
            nt.links.new(cmb.inputs["Y"], _math(nt, 'MULTIPLY', e, f.get('across', 2.0)))
            nz = _noise(nt, _mapped(nt, cmb.outputs["Vector"], loc=(i * 5.7, i * 2.3, 0.0)), 1.0, detail=8.0, rough=0.62)
            big = _noise(nt, _mapped(nt, cmb.outputs["Vector"], scale=(0.35, 0.25, 1.0), loc=(i * 1.9, i * 4.1, 0.0)), 1.0, detail=3.0)
            across = mrange(_math(nt, 'ABSOLUTE', e), 1.0, 0.0, 0.0, 1.0)
            ends = _math(nt, 'MULTIPLY', mrange(t, 0.0, 0.18, 0.0, 1.0), mrange(t, 1.0, 0.82, 0.0, 1.0))
            fib = _math(nt, 'MULTIPLY', mrange(nz, 0.3, 0.7, 0.0, 1.0, smooth=False), mrange(big, 0.3, 0.7, 0.45, 1.0, smooth=False))
            tex = _math(nt, 'ADD', 1.0 - f.get('noise', 0.6), _math(nt, 'MULTIPLY', fib, f.get('noise', 0.6)))
            a = _math(nt, 'MULTIPLY', _math(nt, 'MULTIPLY', _math(nt, 'MULTIPLY', across, ends), tex), f.get('alpha', 1.0))
            col = _mix(nt, a, col, (*f['color'], 1))
    gain = nt.nodes.new("ShaderNodeMath"); gain.operation = 'MULTIPLY'; gain.name = name + "_gain"
    gain.inputs[1].default_value = 1.0
    gsep = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(gsep.inputs["Color"], col)
    gcomb = nt.nodes.new("ShaderNodeCombineColor")
    for ch in ("Red", "Green", "Blue"):
        m = nt.nodes.new("ShaderNodeMath"); m.operation = 'MULTIPLY'
        nt.links.new(m.inputs[0], gsep.outputs[ch]); nt.links.new(m.inputs[1], gain.outputs[0])
        nt.links.new(gcomb.inputs[ch], m.outputs[0])
    gain.inputs[0].default_value = 1.0
    lp = nt.nodes.new("ShaderNodeLightPath")
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = 'RGBA'
    nt.links.new(mix.inputs["Factor"], lp.outputs["Is Camera Ray"])
    if lit is not None:
        nt.links.new(mix.inputs["A"], lit)
    else:
        mix.inputs["A"].default_value = lit_default
    nt.links.new(mix.inputs["B"], gcomb.outputs["Color"])
    nt.links.new(bg.inputs["Color"], mix.outputs["Result"])
    del out
    return gain
