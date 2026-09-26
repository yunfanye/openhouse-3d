"""Site: ground, motor court + reflecting pool, front lawn, pool terrace + glass-walled pool (pale plaster, teal
waterline mosaic, sculpted chaises on the ledge, underwater fixtures), volumetric gas fire, courtyard turf + lounge
groups, the living wall (explicit per-species leaf cards over a clump underlayer), east boundary, rear lawn +
hillside following landscape.hill_z.  Hedges opt into polish's leaf cards via ob["leaf_cards"].  (No trees: landscape.py)"""
import math, random
import bpy
from .plan import *
from archviz.mesh import *
from archviz.lights import *
from archviz.parts import *
from archviz import materials as _mat

LOCAL = {}


def _local_materials(M):
    """Site-specific variants (shared library untouched)."""
    # pool plaster: the library copy minus its caustic-web emission (in the dim dusk pool the web was the only thing
    # lit, so it read as a dark mosaic); the pale plaster is lit by the underwater fixtures instead (photo 24)
    shell = M['pool_shell'].copy(); shell.name = "PoolPlasterSite"
    b = shell.node_tree.nodes.get("Principled BSDF")
    if b is not None:
        for l in list(shell.node_tree.links):
            if l.to_node == b and l.to_socket.name in ("Emission Strength", "Emission Color"):
                shell.node_tree.links.remove(l)
        b.inputs["Emission Strength"].default_value = 0.0
    LOCAL['pool_shell'] = shell
    LOCAL['fire'] = _fire_volume_mat("GasFireVolume", FIRE)
    LOCAL['fire'].cycles.volume_step_rate = 0.35                       # 75 mm tongues need finer ray-march steps
    # pool water: the library scatter density reads as fog over the pool's 6 m sight lines at dusk; a lighter copy
    # keeps a faint glow around the underwater lights (photo 24) but stays clear to the far wall, and absorbs a bit
    # more red so depth reads blue
    pw = M['water'].copy(); pw.name = "PoolWaterSite"
    for n in pw.node_tree.nodes:
        if n.type == 'VOLUME_SCATTER':
            n.inputs["Density"].default_value = 0.006
        elif n.type == 'VOLUME_ABSORPTION':
            n.inputs["Density"].default_value = 0.20                   # photo 24: a saturated mid-blue over 1.5 m of depth
            n.inputs["Color"].default_value = (0.45, 0.84, 1.0, 1)
    for n in pw.node_tree.nodes:                                       # break up the library's regular wave trains
        if n.type == 'TEX_WAVE':
            n.inputs["Distortion"].default_value = n.inputs["Distortion"].default_value * 2.4
            n.inputs["Detail"].default_value = 4.0
        elif n.type == 'BUMP':
            n.inputs["Distance"].default_value = 0.02                  # glassy evening water, not a corrugated sheet
    LOCAL['water'] = pw
    # waterline band inside the pool: pale teal glass mosaic (photo 04) - never a dark band above the water
    LOCAL['tile_waterline'] = _mat.tiles("WaterlineMosaic", (0.58, 0.80, 0.82, 1), grout=(0.80, 0.84, 0.84, 1), size=(0.025, 0.025),
                                         gap=0.0025, rough=0.15, variation=0.3, mottle=0.15, bump=0.4, coat=0.6, plane='XZ')
    LOCAL['tile_waterline_y'] = _mat.tiles("WaterlineMosaicY", (0.58, 0.80, 0.82, 1), grout=(0.80, 0.84, 0.84, 1), size=(0.025, 0.025),
                                           gap=0.0025, rough=0.15, variation=0.3, mottle=0.15, bump=0.4, coat=0.6, plane='YZ')
    LOCAL['felt'] = _mat.noise_mat("GreenWallFelt", (0.03, 0.035, 0.025, 1), (0.06, 0.07, 0.05, 1), scale=40, rough=1.0, bump=0.3)
    LOCAL['hillside'] = _mat.noise_mat("HillsideScrub", (0.06, 0.09, 0.04, 1), (0.14, 0.17, 0.08, 1), scale=2.5, bump=0.6, detail=9, rough=0.95, spec=0.08, bump_dist=0.08)
    # ---- living-wall species (photo 15): each a card material with per-card colour driven by position (all cards of a
    # species share one object, so the library's per-object random would give every card the same tint)
    LOCAL['gw_fern'] = _spatial_variation(_mat.leaf_card("GW_Fern", (0.05, 0.16, 0.05, 1), (0.10, 0.28, 0.08, 1), (0.22, 0.40, 0.12, 1), 0.45, shape='needle', rough=0.7))
    LOCAL['gw_broad'] = _spatial_variation(_mat.leaf_card("GW_Broad", (0.04, 0.14, 0.05, 1), (0.08, 0.24, 0.08, 1), (0.16, 0.34, 0.12, 1), 0.3, shape='oval', rough=0.28))
    LOCAL['gw_filler'] = _spatial_variation(_mat.leaf_card("GW_Filler", (0.06, 0.19, 0.05, 1), (0.14, 0.32, 0.09, 1), (0.26, 0.44, 0.14, 1), 0.4, shape='cluster', rough=0.55))
    LOCAL['gw_lime'] = _spatial_variation(_mat.leaf_card("GW_Lime", (0.30, 0.46, 0.10, 1), (0.50, 0.62, 0.16, 1), (0.68, 0.74, 0.28, 1), 0.5, shape='cluster', rough=0.6))
    LOCAL['gw_rust'] = _spatial_variation(_mat.leaf_card("GW_Rust", (0.30, 0.10, 0.04, 1), (0.52, 0.22, 0.07, 1), (0.66, 0.38, 0.12, 1), 0.35, shape='lance', rough=0.5))
    LOCAL['gw_silver'] = _spatial_variation(_mat.leaf_card("GW_Silver", (0.34, 0.42, 0.30, 1), (0.52, 0.58, 0.44, 1), (0.70, 0.74, 0.60, 1), 0.45, shape='lance', rough=0.7))
    LOCAL['gw_sedge'] = _mat.foliage("GW_Sedge", (0.32, 0.44, 0.10, 1), (0.56, 0.64, 0.18, 1), 0.45, c3=(0.72, 0.72, 0.30, 1), rough=0.75)
    LOCAL['gw_under'] = _mat.foliage("GW_Under", (0.02, 0.06, 0.02, 1), (0.05, 0.13, 0.04, 1), 0.15, c3=(0.09, 0.20, 0.07, 1), rough=0.95)
    LOCAL['gw_under_lime'] = _mat.foliage("GW_UnderLime", (0.10, 0.20, 0.03, 1), (0.24, 0.36, 0.06, 1), 0.2, c3=(0.40, 0.50, 0.12, 1), rough=0.95)
    LOCAL['lawn_tuft'] = _mat.foliage("LawnGrassTuft", (0.22, 0.30, 0.10, 1), (0.46, 0.52, 0.22, 1), 0.5, c3=(0.62, 0.60, 0.30, 1), rough=0.8)


def _spatial_variation(m):
    """Re-route a leaf_card material's per-object random tint to a low-frequency noise of the object coordinates, so
    thousands of cards inside one mesh still vary in colour from place to place."""
    nt = m.node_tree
    oi = next((n for n in nt.nodes if n.type == 'OBJECT_INFO'), None)
    if oi is None:
        return m
    targets = [(l.to_node, l.to_socket) for l in nt.links if l.from_node == oi and l.from_socket.name == "Random"]
    if not targets:
        return m
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = 2.2; n.inputs["Detail"].default_value = 2.0
    nt.links.new(n.inputs["Vector"], tc.outputs["Object"])
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.clamp = True
    mr.inputs["From Min"].default_value = 0.32; mr.inputs["From Max"].default_value = 0.68
    nt.links.new(mr.inputs["Value"], n.outputs["Fac"])
    for node, sock in targets:
        nt.links.new(sock, mr.outputs["Result"])
    return m


def _fire_volume_mat(name, footprint):
    """Linear gas fire as an emissive VOLUME (photo 24): the flame box's Generated coordinates are rescaled to metres,
    a vertically stretched noise cut by a height-rising threshold gives separate licking tongues that thin out and die
    toward the top, a side fall-off keeps them over the burner rows; the emission colour runs white-yellow at the
    base -> orange -> deep red at the tips, and the emission strength fades with height."""
    fx0, fx1, fy0, fy1 = footprint
    Lx, Ly, Lz = (fx1 - fx0) - 0.2, 0.34, 0.70
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    out = nt.nodes["Material Output"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(sep.inputs["Vector"], tc.outputs["Generated"])
    x, y, z = sep.outputs["X"], sep.outputs["Y"], sep.outputs["Z"]
    def mapped(feature, stretch):
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (Lx / feature, Ly / feature, Lz / (feature * stretch))
        nt.links.new(mp.inputs["Vector"], tc.outputs["Generated"])
        return mp.outputs["Vector"]
    n1 = nt.nodes.new("ShaderNodeTexNoise"); n1.inputs["Scale"].default_value = 1.0; n1.inputs["Detail"].default_value = 3.0
    n1.inputs["Roughness"].default_value = 0.55; nt.links.new(n1.inputs["Vector"], mapped(0.07, 3.8))
    n2 = nt.nodes.new("ShaderNodeTexNoise"); n2.inputs["Scale"].default_value = 1.0; n2.inputs["Detail"].default_value = 2.0
    n2.inputs["Roughness"].default_value = 0.5; nt.links.new(n2.inputs["Vector"], mapped(0.03, 2.0))
    field = _mat._math(nt, 'ADD', _mat._math(nt, 'MULTIPLY', n1.outputs["Fac"], 0.78), _mat._math(nt, 'MULTIPLY', n2.outputs["Fac"], 0.22))
    field = _mat._stretch(nt, field, 0.36, 0.66)                      # Perlin sits around 0.5: stretch so peaks become tongues
    # burner rows: three lines of flame along the trough, blended so tongues merge into one ragged sheet
    rows = _mat._math(nt, 'COSINE', _mat._math(nt, 'MULTIPLY', _mat._math(nt, 'SUBTRACT', y, 0.5), 2 * math.pi * 3.0))
    rows = _mat._math(nt, 'ADD', 0.75, _mat._math(nt, 'MULTIPLY', rows, 0.25))
    side = _mat._math(nt, 'SUBTRACT', 1.0, _mat._math(nt, 'POWER', _mat._math(nt, 'MULTIPLY', _mat._math(nt, 'ABSOLUTE', _mat._math(nt, 'SUBTRACT', y, 0.5)), 2.0), 3.0), clamp=True)
    ends = _mat._math(nt, 'SUBTRACT', 1.0, _mat._math(nt, 'POWER', _mat._math(nt, 'MULTIPLY', _mat._math(nt, 'ABSOLUTE', _mat._math(nt, 'SUBTRACT', x, 0.5)), 2.0), 8.0), clamp=True)
    # threshold rises with height: a continuous sheet of flame at the base, separate tongues higher up, nothing at the top
    thr = _mat._math(nt, 'ADD', 0.30, _mat._math(nt, 'MULTIPLY', _mat._math(nt, 'POWER', z, 1.4), 0.72))
    d = _mat._math(nt, 'SUBTRACT', _mat._math(nt, 'MULTIPLY', field, _mat._math(nt, 'MULTIPLY', side, rows)), thr)
    d = _mat._math(nt, 'MULTIPLY', d, 2.6, clamp=True)
    d = _mat._math(nt, 'MULTIPLY', d, _mat._math(nt, 'MULTIPLY', ends, _mat._math(nt, 'SUBTRACT', 1.0, _mat._math(nt, 'POWER', z, 3.0))))
    col = _mat._ramp(nt, z, [(0.0, (1.0, 0.82, 0.32, 1)), (0.2, (1.0, 0.58, 0.12, 1)), (0.5, (1.0, 0.36, 0.04, 1)), (0.8, (0.80, 0.15, 0.02, 1)), (1.0, (0.4, 0.05, 0.01, 1))])
    strength = _mat._math(nt, 'MULTIPLY', d, _mat._math(nt, 'SUBTRACT', 26.0, _mat._math(nt, 'MULTIPLY', z, 16.0)))
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(em.inputs["Color"], col)
    nt.links.new(em.inputs["Strength"], strength)
    nt.links.new(out.inputs["Volume"], em.outputs["Emission"])
    return m


# derived
RP_X0, RP_X1, RP_Y0, RP_Y1 = GLASS_X0 - 0.6, GLASS_X1 + 0.6, -2.4, -0.35      # reflecting pool basin
BR_X0, BR_X1 = PORTAL_X0 - 0.3, PORTAL_X1 + 0.3                              # paver bridge to the door
RECESS = (9.0, 11.6, TY0, TY0 + 1.9)                                         # lit recess under the living pavilion (lawn level)
POOL_FLOOR = Z_LAWN + 0.05
GW_Z0, GW_Z1 = Z_LIV + 0.06, Z_SOF - 0.20                                    # green wall (fills the exterior's recess up to its Z_SOF-0.1 head)
GW_Y = NA_Y0 + 0.30                                                          # face of the planting substrate inside the recess


def _assign_card_uvs(ob):
    """Every polygon is a separate quad card: give each one a 0..1 UV square (the leaf_card materials cut the leaf
    outline in UV space)."""
    me = ob.data
    uv = me.uv_layers.new(name="UVMap")
    corners = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))
    for p in me.polygons:
        for k, li in enumerate(p.loop_indices):
            uv.data[li].uv = corners[k % 4]


def _card(mb, c, n, size, roll, mi=0, aspect=1.0):
    """One leaf card: a quad of side `size` centred at c, facing unit normal n, spun by `roll` about n."""
    n = Vector(n).normalized()
    ref = Vector((0, 0, 1)) if abs(n.z) < 0.9 else Vector((1, 0, 0))
    u = n.cross(ref).normalized(); v = n.cross(u).normalized()
    cr, sr = math.cos(roll), math.sin(roll)
    a, b = (u * cr + v * sr) * (size * aspect / 2), (v * cr - u * sr) * (size / 2)
    c = Vector(c)
    mb.quad(tuple(c - a - b), tuple(c + a - b), tuple(c + a + b), tuple(c - a + b), mi)


def _tuft(mb, c, r, rng, mi=0, blades=None, lean_dir=None, h_mult=2.6, r0=0.011):
    """Clump of 12-25 thin tapered blades arching outward (ornamental grass / sedge); `lean_dir` = (dx, dy, dz) bias so
    a tuft on a wall hangs outward and down."""
    n = blades or rng.randint(14, 24)
    h = r * h_mult
    for i in range(n):
        a = 2 * math.pi * i / n + rng.uniform(-0.3, 0.3)
        lean = rng.uniform(0.3, 0.8)
        hb = h * rng.uniform(0.6, 1.15)
        base = Vector((c[0] + rng.uniform(-0.25, 0.25) * r, c[1] + rng.uniform(-0.25, 0.25) * r, c[2]))
        d = Vector((math.cos(a), math.sin(a), 0))
        up = Vector((0, 0, 1))
        if lean_dir is not None:
            ld = Vector(lean_dir).normalized()
            d = (d * 0.35 + ld * 0.65).normalized()
            up = (ld * 0.6 + Vector((0, 0, 1)) * 0.4).normalized()
        mid = base + d * (hb * lean * 0.35) + up * (hb * 0.6)
        tip = base + d * (hb * lean) + up * (hb * (1.0 - lean * 0.45)) + Vector((0, 0, -0.15 * hb if lean_dir is not None else 0))
        mb.sweep(_taper3(base, mid, tip, r0 * r / 0.25, r0 * 0.6 * r / 0.25, 0.001, 4), mi)


def _taper3(p0, p1, p2, r0, r1, r2, seg):
    """Ring sections along a 3-point polyline with per-point radius and a consistent frame."""
    pts = [Vector(p0), Vector(p1), Vector(p2)]
    ref = Vector((0, 1, 0)) if abs((pts[-1] - pts[0]).normalized().z) > 0.8 else Vector((0, 0, 1))
    secs = []
    for k, p in enumerate(pts):
        t = pts[1] - pts[0] if k == 0 else (pts[-1] - pts[-2] if k == 2 else pts[2] - pts[0])
        t = t.normalized()
        n = t.cross(ref)
        if n.length < 1e-6:
            n = t.cross(Vector((1, 0, 0)))
        n.normalize(); b = t.cross(n).normalized()
        r = (r0, r1, r2)[k]
        secs.append([tuple(p + (n * math.cos(a) + b * math.sin(a)) * r) for a in [2 * math.pi * i / seg for i in range(seg)]])
    return secs


def _chaise(mb, x, y, z, rot=0.0, mi=0, w=0.70):
    """In-water chaise (photo 22): one sculpted slab - flat seat, a gentle rise at the foot, a curved back rising to a
    headrest - with a rounded cross-section, built as a sweep of rounded rectangles along the profile.  Foot toward the
    chaise's own -Y; `z` = the surface it lies on."""
    prof = [(-0.98, 0.09), (-0.85, 0.06), (-0.55, 0.035), (-0.20, 0.03), (0.15, 0.03), (0.40, 0.05), (0.58, 0.13),
            (0.74, 0.27), (0.88, 0.42), (0.98, 0.52), (1.04, 0.56)]
    t = 0.065
    c, s = math.cos(rot), math.sin(rot)
    secs = []
    for k, (py, pz) in enumerate(prof):
        # local slope -> section rotated about X so the slab keeps its thickness along the curve
        y0, z0 = prof[max(0, k - 1)]; y1, z1 = prof[min(len(prof) - 1, k + 1)]
        ang = math.atan2(z1 - z0, y1 - y0)
        ca, sa = math.cos(ang), math.sin(ang)
        ww = w * (0.94 if py < -0.8 else (1.0 if py < 0.55 else 0.9 - 0.25 * (py - 0.55)))
        sec = []
        for i in range(16):                                             # rounded rectangle: superellipse
            a = 2 * math.pi * i / 16
            cx_, cz_ = math.cos(a), math.sin(a)
            ex = math.copysign(abs(cx_) ** 0.45, cx_) * ww / 2
            ez = math.copysign(abs(cz_) ** 0.45, cz_) * t / 2
            ly, lz = py - ez * sa, pz + t / 2 + ez * ca
            sec.append((x + ex * c - ly * s, y + ex * s + ly * c, z + lz))
        secs.append(sec)
    mb.sweep(secs, mi)


def _ring(mb, c, r_in, r_out, t, axis, mi=0, seg=24):
    """Flat annulus of thickness t whose plane is normal to `axis` ('X' | 'Y' | 'Z'); c = centre on the surface."""
    cx, cy, cz = c
    secs = []
    for k in range(seg):
        a = 2 * math.pi * k / seg
        u, v = math.cos(a), math.sin(a)
        pts = []
        for (rr, d) in ((r_in, 0.0), (r_out, 0.0), (r_out, t), (r_in, t)):
            if axis == 'Z':
                pts.append((cx + rr * u, cy + rr * v, cz + d))
            elif axis == 'Y':
                pts.append((cx + rr * u, cy + d, cz + rr * v))
            else:
                pts.append((cx + d, cy + rr * u, cz + rr * v))
        secs.append(pts)
    mb.sweep(secs, mi, close=True, caps=False)


def _pool_fixture(mb, x, y, z, nx, ny, mi_ring=0, mi_lens=1):
    """Underwater light: 120 mm stainless ring + a slightly domed lens, on a wall whose outward normal is (nx, ny)
    (nx, ny) == (0, 0) means a floor fixture facing up."""
    if nx == 0 and ny == 0:
        _ring(mb, (x, y, z), 0.045, 0.06, 0.006, 'Z', mi_ring)
        mb.blob((x, y, z + 0.004), 0.045, seg=14, rings=6, mi=mi_lens, squash=0.25)
    elif nx == 0:
        _ring(mb, (x, y, z), 0.045, 0.06, 0.006 * ny, 'Y', mi_ring)
        mb.blob((x, y + ny * 0.004, z), 0.045, seg=14, rings=6, mi=mi_lens, ry=0.25)
    else:
        _ring(mb, (x, y, z), 0.045, 0.06, 0.006 * nx, 'X', mi_ring)
        mb.blob((x + nx * 0.004, y, z), 0.045, seg=14, rings=6, mi=mi_lens, rx=0.25)


def _agave(mb, x, y, z, n=14, L=0.55, mi=0, seed=0):
    """Spiky agave: radiating tapered leaves lofted from 4 sections each."""
    rng = random.Random(seed)
    for i in range(n):
        a = 2 * math.pi * i / n + rng.uniform(-0.15, 0.15)
        ln = L * rng.uniform(0.6, 1.0)
        lift = rng.uniform(0.35, 0.9)
        ux, uy = math.cos(a), math.sin(a)
        px, py = -uy, ux
        secs = []
        for (t, w, th) in ((0.0, 0.05, 0.02), (0.35, 0.09, 0.025), (0.75, 0.06, 0.015), (1.0, 0.004, 0.003)):
            cx, cy = x + ux * ln * t, y + uy * ln * t
            cz = z + 0.05 + ln * t * lift - 0.25 * ln * t * t
            secs.append([(cx + px * w, cy + py * w, cz - th), (cx - px * w, cy - py * w, cz - th),
                         (cx - px * w * 0.6, cy - py * w * 0.6, cz + th), (cx + px * w * 0.6, cy + py * w * 0.6, cz + th)])
        mb.sweep(secs, mi)


def _lantern(mb, x, y, z, mi_frame=0, mi_glass=1, mi_candle=2, w=0.2, h=0.36):
    """Black metal lantern with frosted glass sides and a warm candle inside."""
    hw = w / 2
    mb.box(x - hw, x + hw, y - hw, y + hw, z, z + 0.015, mi_frame)                       # base
    mb.box(x - hw, x + hw, y - hw, y + hw, z + h - 0.02, z + h, mi_frame)                # top
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.box(x + sx * hw - (0.008 if sx > 0 else 0), x + sx * hw + (0.008 if sx < 0 else 0),
                   y + sy * hw - (0.008 if sy > 0 else 0), y + sy * hw + (0.008 if sy < 0 else 0), z, z + h, mi_frame)
    mb.box(x - hw + 0.006, x + hw - 0.006, y - hw + 0.006, y + hw - 0.006, z + 0.015, z + h - 0.02, mi_glass)
    mb.cylinder(x, y, z + 0.015, z + 0.14, 0.035, seg=12, mi=mi_candle)
    mb.box(x - 0.02, x + 0.02, y - 0.02, y + 0.02, z + h, z + h + 0.03, mi_frame)         # hanging loop stub


def _tumbler(mb, x, y, z, mi=0):
    mb.lathe(x, y, z, [(0, 0), (0.03, 0), (0.033, 0.01), (0.036, 0.09), (0.034, 0.09), (0.031, 0.012), (0, 0.012)], seg=16, mi=mi)


def _slatted_table(mb, x, y, z, w, d, h=0.34, mi=0, planks=4, gap=0.006, rot=0.0):
    """Teak coffee table: planked top (planks along the table's own X), 30 mm apron, square legs."""
    pw = (d - (planks - 1) * gap) / planks
    for i in range(planks):
        cy = -d / 2 + pw / 2 + i * (pw + gap)
        px, py = rot2(x, y + cy, x, y, rot)
        mb.cbox(px, py, z + h - 0.02, w, pw, 0.04, mi, rot)
    px, py = rot2(x, y, x, y, rot)
    mb.cbox(px, py, z + h - 0.07, w - 0.08, d - 0.08, 0.05, mi, rot)
    for sx in (-1, 1):
        for sy in (-1, 1):
            px, py = rot2(x + sx * (w / 2 - 0.05), y + sy * (d / 2 - 0.05), x, y, rot)
            mb.cbox(px, py, z + (h - 0.04) / 2, 0.05, 0.05, h - 0.04, mi, rot)


def _bollard(mb, x, y, z, mi_body=0, mi_glow=1, h=0.6):
    mb.box(x - 0.045, x + 0.045, y - 0.045, y + 0.045, z, z + h, mi_body)
    mb.box(x - 0.04, x + 0.04, y - 0.04, y + 0.04, z + h - 0.09, z + h - 0.03, mi_glow)
    mb.box(x - 0.05, x + 0.05, y - 0.05, y + 0.05, z + h - 0.03, z + h, mi_body)


def _towel_roll(mb, p0, p1, r, mi=0):
    mb.tube(p0, p1, r, r, seg=18, mi=mi)


def _ground(M):
    g = MB()          # hole under the sunken lounge / theatre (floor -0.9) so the ground can't poke through
    g.plate(-140, 180, -160, 160, -0.9, -0.34, holes=[(MX0 + WT, -5.0, 8.4, MY1 - WT)])
    g.build("Ground", M['ground'])
    # west of the house: court level in front, raised planting bed further back (trees go there)
    box("Bed_West_Low", -24, MX0, -14.5, 9.0, -0.34, -0.05, M['mulch'])
    b = MB()
    b.box(-24, MX0, 9.0, MY1, -0.34, Z_LIV - 0.08)
    b.build("Bed_West_High", M['mulch'])
    box("Bed_West_Wall", -24, MX0, 8.7, 9.0, -0.34, Z_LIV - 0.05, M['trav'])
    box("Bed_South", -18, 7.5, -17.5, -14.5, -0.34, 0.05, M['mulch'])
    box("Bed_East", LAWN_X1, 40, -20, 40, -0.34, Z_LAWN - 0.15, M['mulch'])
    # driveway + street (south-west)
    box("Driveway", -34, -14, -30, -6, -0.35, -0.04, M['asphalt'])
    box("Street", -70, 70, -42, -30, -0.35, -0.04, M['asphalt'])
    box("Street_Verge", -70, 70, -30, -17.5, -0.35, -0.1, M['ground'])


def _motor_court(M):
    mc = MB()
    mc.plate(-18.0, 7.5, -14.5, MY0, -0.3, 0.0, holes=[(RP_X0 - 0.1, RP_X1 + 0.1, RP_Y0 - 0.1, RP_Y1 + 0.1)])
    mc.build("MotorCourt", M['court'])
    # grass strips in the paving, running toward the house (photos 02 / 23: 120 mm turf bands every ~1.8 m)
    gs = MB()
    x = -17.1
    while x < 7.2:
        y_end = -3.2 if (RP_X0 - 0.5 < x < RP_X1 + 0.5) else MY0 - 0.25
        gs.box(x - 0.06, x + 0.06, -14.0, y_end, -0.002, 0.012)
        x += 1.8
    gs.build("Court_GrassStrips", M['turf'])
    # 40 mm flush black metal edge strips where the paving meets the beds / curbs + a slotted linear drain at the garage
    ed = MB()
    ed.box(-18.0, -17.96, -14.5, MY0, 0.0, 0.004, 0)
    ed.box(-18.0, 7.5, -14.5, -14.46, 0.0, 0.004, 0)
    ed.box(LAWN_X0 - 0.04, LAWN_X0, -14.5, -3.7, 0.0, 0.004, 0)
    ed.box(GAR_X0 - 0.2, GAR_X1 + 0.2, MY0 - 0.62, MY0 - 0.46, -0.03, 0.001, 0)               # drain body
    xx = GAR_X0 - 0.18
    while xx < GAR_X1 + 0.18:
        ed.box(xx, xx + 0.012, MY0 - 0.61, MY0 - 0.47, 0.001, 0.005, 1)                       # grate bars
        xx += 0.03
    ed.build("Court_Edging", [M['black_metal'], M['steel']])
    # light paver apron around the reflecting pool + bridge to the door
    ap = MB()
    ap.plate(RP_X0 - 0.6, RP_X1 + 0.6, -3.2, MY0, -0.001, 0.02, holes=[(RP_X0 - 0.1, RP_X1 + 0.1, RP_Y0 - 0.1, RP_Y1 + 0.1)])
    ap.build("Entry_Apron", M['pavers'])
    # reflecting pool: charcoal mosaic basin, still water near the brim, overflow slot, stone lip, floating slab bridge
    mosaic = _mat.tiles("CharcoalMosaic", (0.10, 0.10, 0.11, 1), grout=(0.24, 0.24, 0.24, 1), size=(0.03, 0.03), gap=0.002,
                        rough=0.3, variation=0.25, mottle=0.2, bump=0.35, coat=0.4)
    sh = MB()
    sh.box(RP_X0 - 0.1, RP_X1 + 0.1, RP_Y0 - 0.1, RP_Y1 + 0.1, -0.36, -0.30)
    sh.box(RP_X0 - 0.1, RP_X0, RP_Y0 - 0.1, RP_Y1 + 0.1, -0.30, 0.0)
    sh.box(RP_X1, RP_X1 + 0.1, RP_Y0 - 0.1, RP_Y1 + 0.1, -0.30, 0.0)
    sh.box(RP_X0 - 0.1, RP_X1 + 0.1, RP_Y0 - 0.1, RP_Y0, -0.30, 0.0)
    sh.box(RP_X0 - 0.1, RP_X1 + 0.1, RP_Y1, RP_Y1 + 0.1, -0.30, 0.0)
    sh.build("ReflPool_Basin", mosaic)
    WL = -0.035                                                                                # water level (near the brim, photo 02)
    box("ReflPool_Water", RP_X0 + 0.012, RP_X1 - 0.012, RP_Y0 + 0.012, RP_Y1 - 0.012, -0.30, WL, M['water_still'])
    slot = MB()                                                                                # 10 mm overflow slot all round
    slot.frame(RP_X0, RP_X1, RP_Y0, RP_Y1, -0.16, 0.0, 0.012, axis='Z')
    slot.build("ReflPool_Slot", M['black'])
    lip = MB()
    lip.frame(RP_X0 - 0.22, RP_X1 + 0.22, RP_Y0 - 0.22, RP_Y1 + 0.22, -0.01, 0.025, 0.12, axis='Z')
    lip.build("ReflPool_Lip", M['trav'], bevel=0.004)
    br = MB()                                                                                  # three 30 mm slabs floating 20 mm over the water
    n = 3
    L = (RP_Y1 + 0.25) - (RP_Y0 - 0.25)
    sl = (L - (n - 1) * 0.02) / n
    for i in range(n):
        ya = RP_Y0 - 0.25 + i * (sl + 0.02)
        br.box(BR_X0, BR_X1, ya, ya + sl, WL + 0.02, WL + 0.05 if WL + 0.05 < 0.02 else 0.02)
    br.build("ReflPool_Bridge", M['pavers_big'], bevel=0.003)
    for i in range(n):
        ya = RP_Y0 - 0.25 + i * (sl + 0.02)
        box(f"ReflPool_BridgeSupport_{i}", BR_X0 + 0.3, BR_X1 - 0.3, ya + 0.15, ya + sl - 0.15, -0.30, WL + 0.02, M['black'])
    ul = MB()
    for lx in ((RP_X0 + BR_X0) / 2, BR_X0 - 0.45, BR_X1 + 0.45, (BR_X1 + RP_X1) / 2, RP_X0 + 0.45, RP_X1 - 0.45):
        _pool_fixture(ul, lx, RP_Y0 + 0.5, -0.30, 0, 0, 0, 1)
        add_light(f"ReflLight_{lx:.1f}", 'POINT', (lx, RP_Y0 + 0.5, -0.2), 25, (0.8, 0.92, 1.0), size=0.06)
    ul.build("ReflPool_Lights", [M['steel'], M['emit_pool']], smooth=True)
    # low travertine curbs at the court's west / south edges
    box("Court_Curb_W", -18.3, -18.0, -14.5, MY0, -0.3, 0.12, M['trav'])
    box("Court_Curb_S", -18.3, 7.5, -14.8, -14.5, -0.3, 0.12, M['trav'])
    # bark chips on the camera-facing bed edges (front camera foreground) + path bollards along the drive
    ch = MB()
    rng = random.Random(17)
    for i in range(140):
        x = rng.uniform(-17.5, 7.0); y = rng.uniform(-17.3, -14.7)
        ch.cbox(x, y, 0.06, rng.uniform(0.04, 0.09), rng.uniform(0.02, 0.04), 0.012, 0, rng.uniform(0, math.pi))
    for i in range(60):
        x = rng.uniform(-23.5, -18.6); y = rng.uniform(-14.0, 2.0)
        ch.cbox(x, y, -0.04, rng.uniform(0.04, 0.09), rng.uniform(0.02, 0.04), 0.012, 0, rng.uniform(0, math.pi))
    ch.build("Bed_BarkChips", M['bark'])
    bl = MB()
    for y in range(-29, -15, 4):
        _bollard(bl, -13.7, y + 0.5, -0.04, 0, 1)
        add_light(f"Bollard_{y}", 'POINT', (-13.7, y + 0.5, 0.5), 8, WARM, size=0.05)
    _bollard(bl, LAWN_X0 - 2.35, -4.2, 0.0, 0, 1)
    add_light("Bollard_Stair", 'POINT', (LAWN_X0 - 2.35, -4.2, 0.55), 8, WARM, size=0.05)
    bl.build("Path_Bollards", [M['black_metal'], M['emit_cove']])
def _front_lawn(M):
    lf = MB()
    lf.plate(LAWN_X0, LAWN_X1, LAWN_Y0, LAWN_Y1, -0.3, Z_LAWN - 0.04, holes=[FIRE])
    lf.build("Lawn_Fill", M['ground'])
    lw = MB()
    lw.plate(LAWN_X0 + 0.3, LAWN_X1, LAWN_Y0 + 0.3, LAWN_Y1, Z_LAWN - 0.04, Z_LAWN, holes=[(FIRE[0] - 0.16, FIRE[1] + 0.16, FIRE[2] - 0.16, FIRE[3] + 0.16)])
    lw.build("Lawn", M['lawn'])
    rw = MB()
    rw.box(LAWN_X0, LAWN_X0 + 0.3, LAWN_Y0, MY0, -0.3, Z_LAWN + 0.02)           # west wall (to the motor court)
    rw.box(LAWN_X0, LAWN_X1, LAWN_Y0, LAWN_Y0 + 0.3, -0.3, Z_LAWN + 0.02)       # south edge
    rw.box(LAWN_X1 - 0.3, LAWN_X1, LAWN_Y0, LAWN_Y1, Z_LAWN - 0.5, Z_LAWN + 0.02)  # east edge
    rw.build("Lawn_Wall", M['trav'])
    # steps down to the motor court in front of the house's east corner (photo 01 lower-left, photo 34)
    st = MB()
    stairs_x(st, -3.6, -1.9, LAWN_X0 - 2.0, LAWN_X0 + 0.3, Z_COURT, Z_LAWN, n=5)
    st.build("Lawn_Steps", M['trav'])
    lr = MB()
    glass_rail(lr, [(LAWN_X0 + 0.1, MY0 - 0.05), (LAWN_X0 + 0.1, -1.9)], Z_LAWN, h=1.05)
    glass_rail(lr, [(LAWN_X0 + 0.1, -3.6), (LAWN_X0 + 0.1, LAWN_Y0 + 0.3)], Z_LAWN, h=1.05)
    sloped_rail_x(lr, -3.6, LAWN_X0 - 2.0, LAWN_X0 + 0.1, Z_COURT, Z_LAWN)
    sloped_rail_x(lr, -1.9, LAWN_X0 - 2.0, LAWN_X0 + 0.1, Z_COURT, Z_LAWN)
    lr.build("Lawn_Rail", [M['glass'], M['steel']])
    # ornamental grasses along the south edge (real blade clumps), clipped hedge along the east edge (leaf cards on it)
    gr = MB()
    rng = random.Random(3)
    for i in range(34):
        x = LAWN_X0 + 0.9 + i * 0.5 + rng.uniform(-0.1, 0.1)
        y = LAWN_Y0 + 0.65 + rng.uniform(-0.15, 0.15)
        _tuft(gr, (x, y, Z_LAWN), 0.22 + rng.uniform(0, 0.08), rng, mi=0, blades=rng.randint(18, 26), h_mult=2.4)
    gr.build("Lawn_Grasses", LOCAL['lawn_tuft'], smooth=True)
    hg = MB()
    for i in range(24):
        y = LAWN_Y0 + 0.8 + i * 0.62
        hg.blob((LAWN_X1 - 0.65 + rng.uniform(-0.05, 0.05), y, Z_LAWN + 0.7), 0.62, seg=18, rings=12, jitter=0.18, seed=100 + i, squash=1.15)
    ob = hg.build("Lawn_Hedge_E", M['foliage_dark'], smooth=True, auto_smooth=False)
    sm = ob.modifiers.new("sub", 'SUBSURF'); sm.levels = 1; sm.render_levels = 1
    ob["leaf_cards"] = {"leaf": "cluster_shrub", "size": 0.18, "density": 260.0}


def _terrace(M):
    # fill under the terrace, minus the pool basin and the lit recess
    POOL_HOLE = (PX0 - 0.3, PX1 + 0.3, PY0 - 0.1, PY1 + 0.3)
    tf = MB()
    tf.plate(TX0, TX1, TY0, TY1, Z_LAWN - 0.5, Z_LIV - 0.06, holes=[RECESS, POOL_HOLE])
    tf.box(POOL_HOLE[0], POOL_HOLE[1], POOL_HOLE[2], POOL_HOLE[3], Z_LAWN - 0.5, POOL_FLOOR - 0.25)
    tf.box(RECESS[0], RECESS[1], RECESS[2], RECESS[3], Z_LAWN - 0.5, Z_LAWN - 0.1)
    tf.box(RECESS[0], RECESS[1], RECESS[2], RECESS[3], Z_LIV - 0.40, Z_LIV - 0.06)
    tf.build("Terrace_Fill", M['ground'])
    # pavers everywhere except the pool and the courtyard turf
    tp = MB()
    tp.box(TX0, PX0, TY0, TY1, Z_LIV - 0.06, Z_LIV)                       # west strip (living-pavilion front + stair top)
    tp.box(PX0, TX1, PY1, COURT_TURF[2], Z_LIV - 0.06, Z_LIV)              # walkway north of the pool
    tp.box(PX1, TX1, TY0, PY1, Z_LIV - 0.06, Z_LIV)                        # east of the pool
    tp.box(PX0, PX1, TY0, PY0, Z_LIV - 0.06, Z_LIV)                        # thin south coping strip
    tp.box(TX0, TX1, COURT_TURF[3], TY1, Z_LIV - 0.06, Z_LIV)              # band in front of the north arm
    tp.box(COURT_TURF[1], TX1, COURT_TURF[2], COURT_TURF[3], Z_LIV - 0.06, Z_LIV)   # east margin
    tp.box(PX0, COURT_TURF[0], COURT_TURF[2], COURT_TURF[3], Z_LIV - 0.06, Z_LIV)   # west margin
    tp.build("Terrace_Pavers", M['pavers_big'])
    # real 2 mm joints on the 1.2 m paver grid (thin dark strips just proud of the surface) so it reads in raking light
    regions = [(TX0, PX0, TY0, TY1), (PX0, TX1, PY1, COURT_TURF[2]), (PX1, TX1, TY0, PY1), (TX0, TX1, COURT_TURF[3], TY1),
               (COURT_TURF[1], TX1, COURT_TURF[2], COURT_TURF[3]), (PX0, COURT_TURF[0], COURT_TURF[2], COURT_TURF[3])]
    jt = MB()
    for (x0, x1, y0, y1) in regions:
        k = math.ceil(x0 / 1.2)
        while k * 1.2 < x1:
            jt.box(k * 1.2 - 0.0012, k * 1.2 + 0.0012, y0, y1, Z_LIV, Z_LIV + 0.0006); k += 1
        k = math.ceil(y0 / 1.2)
        while k * 1.2 < y1:
            jt.box(x0, x1, k * 1.2 - 0.0012, k * 1.2 + 0.0012, Z_LIV, Z_LIV + 0.0006); k += 1
    jt.build("Terrace_Joints", M['concrete'])
    # south retaining wall (lawn -> terrace) except the pool's glass bay; east edge wall
    sw = MB()
    sw.wall('X', TX0, PX0 - 0.25, TY0 - 0.35, TY0, Z_LAWN - 0.5, Z_LIV,
            holes=[(RECESS[0], RECESS[1], Z_LAWN - 0.1, Z_LIV - 0.40)])
    sw.box(PX1 + 0.25, TX1, TY0 - 0.35, TY0, Z_LAWN - 0.5, Z_LIV)
    sw.box(TX1 - 0.35, TX1, TY0 - 0.35, NA_Y1, Z_LAWN - 0.5, Z_LIV)
    sw.build("Terrace_Wall", M['trav'])
    # plinth under the glass wall: honed black granite (photos 01/24 - the dark base the flames read against)
    box("Terrace_GlassPlinth", PX0 - 0.25, PX1 + 0.25, TY0 - 0.35, TY0 + 0.1, Z_LAWN - 0.5, Z_LAWN + 0.18, M['black_gloss'])
    # lit recess under the living pavilion (photo 01: glowing glass door at lawn level, plant inside)
    gx0, gx1, gy0, gy1 = RECESS
    gz0, gz1 = Z_LAWN - 0.1, Z_LIV - 0.40
    gr = MB()
    gr.box(gx0, gx1, gy1 - 0.05, gy1, gz0, gz1, 0)
    gr.box(gx0, gx0 + 0.05, gy0, gy1, gz0, gz1, 0); gr.box(gx1 - 0.05, gx1, gy0, gy1, gz0, gz1, 0)
    gr.box(gx0, gx1, gy0, gy1, gz1 - 0.05, gz1, 0)
    gr.box(gx0, gx1, gy0, gy1, gz0, gz0 + 0.1, 1)
    gr.build("Recess", [M['white_int'], M['pavers']])
    box("Recess_Glow", gx0 + 0.3, gx1 - 0.3, gy0 + 0.5, gy1 - 0.3, gz1 - 0.06, gz1 - 0.05, M['emit_ceiling'])
    rgw = MB()                                                                            # small living wall at the back of the recess (photo 01)
    rgw.box(gx0 + 0.1, gx1 - 0.1, gy1 - 0.12, gy1 - 0.05, gz0 + 0.2, gz1 - 0.2)
    ob = rgw.build("Recess_GreenWall", LOCAL['gw_under'])
    vg = ob.vertex_groups.new(name="front"); vg.add([v.index for v in ob.data.vertices if v.co.y < gy1 - 0.1], 1.0, 'REPLACE')
    ob["leaf_cards"] = {"leaf": "GW_Filler", "size": 0.12, "density": 320.0, "group": "front"}
    gm = MB()
    gm.box(gx0 + 0.05, gx1 - 0.05, gy0 + 0.9, gy0 + 0.9 + T, gz0 + 0.1, gz1 - 0.05, 0)
    gm.box(10.3 - 0.02, 10.3 + 0.02, gy0 + 0.87, gy0 + 0.95, gz0 + 0.1, gz1 - 0.05, 1)
    gm.box(gx0 + 0.05, gx1 - 0.05, gy0 + 0.87, gy0 + 0.95, gz1 - 0.1, gz1 - 0.05, 1)
    gm.box(gx0 + 0.05, gx1 - 0.05, gy0 + 0.87, gy0 + 0.95, gz0 + 0.1, gz0 + 0.14, 1)
    gm.build("Recess_Door", [M['glass'], M['frame']])
    pp = MB()
    potted_plant(pp, gx0 + 0.5, gy1 - 0.55, gz0 + 0.1, pot_r=0.22, pot_h=0.4, h=1.1, seed=7, kind='broad')
    pp.build("Recess_Plant", [M['ceramic_black'], M['leaf_plant'], M['bark']], smooth=True)
    area_light("Recess_Light", ((gx0 + gx1) / 2, (gy0 + gy1) / 2, gz1 - 0.1), (1.8, 1.2), 40)
    # glass rail along the terrace's south edge, west of the stair
    sr = MB()
    glass_rail(sr, [(TX0 + 0.05, TY0 - 0.1), (ST_X0 - 0.05, TY0 - 0.1)], Z_LIV, h=1.05)
    sr.build("Terrace_Rail_S", [M['glass'], M['steel']])


def _pool(M):
    zf = POOL_FLOOR
    ps = MB()
    ps.box(PX0 - 0.3, PX1 + 0.3, PY0 - 0.1, PY1 + 0.3, zf - 0.25, zf, 0)          # floor
    ps.box(PX0 - 0.3, PX0, PY0 - 0.1, PY1 + 0.3, zf, Z_LIV, 0)                     # W wall
    ps.box(PX1, PX1 + 0.3, PY0 - 0.1, PY1 + 0.3, zf, Z_LIV, 0)                     # E wall
    ps.box(PX0 - 0.3, PX1 + 0.3, PY1, PY1 + 0.3, zf, Z_LIV, 0)                     # N wall
    ps.box(PX0, PX0 + 2.0, PY0, PY1, zf, Z_WATER - 0.10, 0)                         # tanning ledge
    ps.box(SPA[0], SPA[1], SPA[2], SPA[3], zf, Z_WATER - 0.9, 0)                    # spa bench block
    # three entry steps in the NE corner (photo 24 shows steps descending into the pool)
    STEPS = []
    for i in range(3):
        zt = Z_WATER - 0.35 - 0.35 * i
        ps.box(PX1 - 1.6, PX1, PY1 - 0.42 * (i + 1), PY1, zf, zt, 0)
        STEPS.append((PX1 - 1.6, PX1, PY1 - 0.42 * (i + 1), PY1 - 0.42 * i, zt))
    ps.build("Pool_Shell", LOCAL['pool_shell'])
    # pale teal glass-mosaic waterline band (60 mm under / 80 mm over the water) on the inside faces + travertine
    # bullnose nosings on the ledge and steps (their tops stay pale plaster so the shallow end glows like photo 04)
    mb_ = MB()
    zb0, zb1 = Z_WATER - 0.06, Z_LIV
    mb_.box(PX0 - 0.012, PX0, PY0, PY1, zb0, zb1, 1); mb_.box(PX1, PX1 + 0.012, PY0, PY1, zb0, zb1, 1)
    mb_.box(PX0, PX1, PY1, PY1 + 0.012, zb0, zb1, 0)
    for (x0, x1, y0, y1, zt) in STEPS:
        mb_.rbox(x0, x1, y0 - 0.02, y0 + 0.03, zt - 0.04, zt + 0.006, 0.012, 2)   # 30 mm bullnose nosing
    mb_.rbox(PX0 + 1.97, PX0 + 2.03, PY0, PY1, Z_WATER - 0.13, Z_WATER - 0.094, 0.015, 2)   # ledge bullnose
    mb_.build("Pool_MosaicBand", [LOCAL['tile_waterline'], LOCAL['tile_waterline_y'], M['trav']], smooth=False)
    # spa rim (mosaic) rising just above the water, with a spillway lip on the pool side (south)
    sp = MB()
    for (x0, x1, y0, y1, zt) in ((SPA[0], SPA[1], SPA[2], SPA[2] + 0.12, Z_WATER + 0.005), (SPA[0], SPA[1], SPA[3] - 0.12, SPA[3], Z_WATER + 0.05),
                                 (SPA[0], SPA[0] + 0.12, SPA[2], SPA[3], Z_WATER + 0.05), (SPA[1] - 0.12, SPA[1], SPA[2], SPA[3], Z_WATER + 0.05)):
        sp.box(x0, x1, y0, y1, Z_WATER - 0.9, zt)
    sp.box(SPA[0] + 0.12, SPA[1] - 0.12, SPA[2] + 0.12, SPA[3] - 0.12, Z_WATER - 0.9, Z_WATER - 0.55)   # spa seat
    sp.build("Spa_Rim", M['tile_spa'])
    add_light("Spa_Light", 'POINT', ((SPA[0] + SPA[1]) / 2, (SPA[2] + SPA[3]) / 2, Z_WATER - 0.35), 45, (0.70, 0.92, 1.0), size=0.15)
    # water (one slab touching the back of the glass wall; the spa water sits higher inside its rim and sheets over its lip)
    box("Pool_Water", PX0 + 0.001, PX1 - 0.001, TY0 + 0.002, PY1 - 0.001, zf + 0.001, Z_WATER, LOCAL['water'])
    box("Spa_Water", SPA[0] + 0.121, SPA[1] - 0.121, SPA[2] + 0.121, SPA[3] - 0.121, Z_WATER - 0.01, Z_WATER + 0.03, LOCAL['water'])
    box("Spa_Spillway", SPA[0] + 0.14, SPA[1] - 0.14, SPA[2] - 0.03, SPA[2] + 0.125, Z_WATER + 0.006, Z_WATER + 0.03, LOCAL['water'])
    # glass south wall: 3 panes + stainless shoe with cover caps + slim joints; 12 mm of green glass edge shows above the cap
    pw = MB()
    gz0, gz1 = Z_LAWN + 0.28, Z_LIV + 0.02
    pw.box(PX0 - 0.25, PX1 + 0.25, TY0 - 0.03, TY0, gz0, gz1 + 0.012, 0)
    pw.box(PX0 - 0.25, PX1 + 0.25, TY0 - 0.03, TY0, gz1 + 0.012, gz1 + 0.024, 2)          # visible edge (sea-green)
    pw.box(PX0 - 0.3, PX1 + 0.3, TY0 - 0.09, TY0 + 0.1, Z_LAWN + 0.18, Z_LAWN + 0.28, 1)
    for jx in (PX0 - 0.25 + (PX1 - PX0 + 0.5) / 3, PX0 - 0.25 + 2 * (PX1 - PX0 + 0.5) / 3):
        pw.box(jx - 0.006, jx + 0.006, TY0 - 0.04, TY0 + 0.01, gz0, gz1, 1)
    pw.box(PX0 - 0.3, PX1 + 0.3, TY0 - 0.06, TY0 + 0.02, gz1 - 0.03, gz1 + 0.012, 1)     # top channel (glass edge stands proud)
    x = PX0 - 0.1
    while x < PX1 + 0.1:                                                                  # shoe cover caps every 0.6 m
        pw.box(x - 0.02, x + 0.02, TY0 - 0.098, TY0 - 0.088, Z_LAWN + 0.20, Z_LAWN + 0.26, 1)
        x += 0.6
    pw.build("Pool_GlassWall", [M['glass'], M['steel'], M['glass_green']])
    # sculpted one-piece chaises on the tanning ledge, in ~100 mm of water, heads toward the pavilion (photo 22)
    lg = MB()
    for y in (5.2, 6.35, 7.5):                                       # side by side across the ledge, feet toward the deep water
        _chaise(lg, PX0 + 1.02, y, Z_WATER - 0.10, rot=math.pi / 2, mi=0)
    lg.build("Pool_Loungers", M['acrylic_white'], smooth=True, subsurf=1)
    tw = MB()
    _towel_roll(tw, (PX0 - 0.35, 6.2, Z_LIV + 0.1), (PX0 - 0.35, 6.7, Z_LIV + 0.1), 0.08)
    _towel_roll(tw, (PX0 - 0.35, 6.75, Z_LIV + 0.1), (PX0 - 0.35, 7.25, Z_LIV + 0.1), 0.08)
    tw.build("Pool_Towels", M['linen_white'], smooth=True)
    # travertine coping N / E / W: 4 mm chamfer, 6 mm joints every 0.6 m, two skimmer lids
    cp = MB()
    cp.box(PX0 - 0.45, PX0, PY0, PY1 + 0.45, Z_LIV - 0.06, Z_LIV + 0.02)
    cp.box(PX1, PX1 + 0.45, PY0, PY1 + 0.45, Z_LIV - 0.06, Z_LIV + 0.02)
    cp.box(PX0 - 0.45, PX1 + 0.45, PY1, PY1 + 0.45, Z_LIV - 0.06, Z_LIV + 0.02)
    cp.build("Pool_Coping", M['trav'], bevel=0.004)
    cj = MB()
    y = PY0 + 0.6
    while y < PY1 + 0.4:
        cj.box(PX0 - 0.45, PX0, y - 0.003, y + 0.003, Z_LIV + 0.02, Z_LIV + 0.0206)
        cj.box(PX1, PX1 + 0.45, y - 0.003, y + 0.003, Z_LIV + 0.02, Z_LIV + 0.0206)
        y += 0.6
    x = PX0 - 0.45 + 0.6
    while x < PX1 + 0.4:
        cj.box(x - 0.003, x + 0.003, PY1, PY1 + 0.45, Z_LIV + 0.02, Z_LIV + 0.0206)
        x += 0.6
    cj.build("Pool_CopingJoints", M['concrete'])
    sk = MB()
    for x in (PX0 + 2.8, PX1 - 2.8):
        sk.box(x - 0.1, x + 0.1, PY1 + 0.12, PY1 + 0.32, Z_LIV + 0.02, Z_LIV + 0.022)
        sk.frame(x - 0.11, x + 0.11, PY1 + 0.11, PY1 + 0.33, Z_LIV + 0.02, Z_LIV + 0.0225, 0.008, axis='Z')
    sk.build("Pool_Skimmers", M['ceramic'])
    # underwater lights: stainless ring + domed lens fixtures, with point lights
    # (the west pair sits in the tanning ledge's front face - the ledge is solid from the floor up to Z_WATER - 0.10)
    ul = MB()
    for (x, y, nx, ny, off) in ((16.4, PY1, 0, -1, 0.3), (18.6, PY1, 0, -1, 0.3), (20.8, PY1, 0, -1, 0.3), (PX1, 4.6, -1, 0, 0.3), (PX1, 7.6, -1, 0, 0.3),
                                (PX0 + 2.0, 5.0, 1, 0, 0.3), (PX0 + 2.0, 8.0, 1, 0, 0.3),
                                (PX0 + 0.55, PY0, 0, -1, 0.05), (PX0 + 1.45, PY0, 0, -1, 0.05)):   # last two: ledge face behind the glass
        _pool_fixture(ul, x, y, Z_LAWN + 0.55, nx, ny, 0, 1)
        add_light(f"Pool_Light_{x:.0f}_{y:.0f}", 'POINT', (x + nx * off, y + ny * off, Z_LAWN + 0.55), 120, (0.70, 0.92, 1.0), size=0.05 if off < 0.1 else 0.18)
    ul.build("Pool_LightLenses", [M['steel'], M['emit_pool']], smooth=True)
def _fire(M):
    fx0, fx1, fy0, fy1 = FIRE
    ft = MB()
    ft.box(fx0, fx1, fy0, fy1, Z_LAWN - 0.45, Z_LAWN - 0.40)
    ft.frame(fx0, fx1, fy0, fy1, Z_LAWN - 0.45, Z_LAWN + 0.02, 0.03, axis='Z')
    ft.build("Fire_Trough", M['black_metal'])
    box("Fire_Glass", fx0 + 0.03, fx1 - 0.03, fy0 + 0.03, fy1 - 0.03, Z_LAWN - 0.40, Z_LAWN - 0.215, M['fire_glass'])
    gl = MB()                                                    # ~1400 glossy black glass chunks heaped on the bed
    rng_g = random.Random(23)
    x = fx0 + 0.05
    while x < fx1 - 0.05:
        y = fy0 + 0.05
        while y < fy1 - 0.05:
            r = rng_g.uniform(0.014, 0.03)
            gl.blob((x + rng_g.uniform(-0.02, 0.02), y + rng_g.uniform(-0.02, 0.02), Z_LAWN - 0.215 + r * rng_g.uniform(0.3, 0.8)), r,
                    seg=6, rings=4, jitter=0.5, seed=rng_g.randint(0, 9999), squash=rng_g.uniform(0.5, 0.9))
            y += 0.05
        x += 0.05
    gl.build("Fire_GlassChunks", M['fire_glass'], smooth=True)
    tray = MB()
    tray.frame(fx0 + 0.03, fx1 - 0.03, fy0 + 0.03, fy1 - 0.03, Z_LAWN - 0.215, Z_LAWN - 0.19, 0.02, axis='Z')
    tray.build("Fire_BurnerTray", M['black_metal'])
    lip = MB()
    lip.frame(fx0 - 0.16, fx1 + 0.16, fy0 - 0.16, fy1 + 0.16, Z_LAWN - 0.06, Z_LAWN + 0.02, 0.16, axis='Z')
    lip.build("Fire_Lip", M['trav'])
    # three burner rows (dark steel tubes with a line of jet holes) under an emissive flame VOLUME (photo 24)
    br = MB()
    ym = (fy0 + fy1) / 2
    for row in (-0.11, 0.0, 0.11):
        br.tube((fx0 + 0.12, ym + row, Z_LAWN - 0.20), (fx1 - 0.12, ym + row, Z_LAWN - 0.20), 0.012, 0.012, seg=10)
    br.build("Fire_Burners", M['black_metal'], smooth=True)
    fv = MB()
    fv.box(fx0 + 0.10, fx1 - 0.10, ym - 0.17, ym + 0.17, Z_LAWN - 0.16, Z_LAWN + 0.54)      # tongues rise ~0.35 m over the lip
    vol = fv.build("Fire_Flames", LOCAL['fire'])
    vol.visible_shadow = False                                          # an emissive gas casts no shadow
    add_light("Fire_Glow", 'POINT', ((fx0 + fx1) / 2, (fy0 + fy1) / 2, Z_LAWN + 0.12), 260, (1.0, 0.48, 0.14), size=1.2)
    add_light("Fire_Glow2", 'POINT', (fx0 + 0.9, (fy0 + fy1) / 2, Z_LAWN + 0.05), 70, (1.0, 0.5, 0.15), size=0.5)
    add_light("Fire_Glow3", 'POINT', (fx1 - 0.9, (fy0 + fy1) / 2, Z_LAWN + 0.05), 70, (1.0, 0.5, 0.15), size=0.5)


def _terrace_stair(M):
    st = MB()
    stairs(st, ST_X0, ST_X1, TY0 - 3.2, TY0, Z_LAWN, Z_LIV, n=10)
    st.build("Terrace_Stair", M['trav'])
    sr = MB()
    sloped_rail(sr, ST_X0, TY0 - 3.2, TY0, Z_LAWN, Z_LIV)
    sloped_rail(sr, ST_X1, TY0 - 3.2, TY0, Z_LAWN, Z_LIV)
    sr.build("Terrace_Stair_Rail", [M['glass'], M['steel']])
    sl = MB()
    for i in range(10):
        z = Z_LAWN + 0.17 * i + 0.05
        y = TY0 - 3.2 + 0.32 * i + 0.1
        sl.box(ST_X0 + 0.02, ST_X0 + 0.04, y - 0.01, y + 0.13, z - 0.01, z + 0.05, 1)   # 60 x 20 mm black housings
        sl.box(ST_X0 + 0.04, ST_X0 + 0.044, y, y + 0.12, z, z + 0.03, 0)                # lens faces the tread
        sl.box(ST_X1 - 0.04, ST_X1 - 0.02, y - 0.01, y + 0.13, z - 0.01, z + 0.05, 1)
        sl.box(ST_X1 - 0.044, ST_X1 - 0.04, y, y + 0.12, z, z + 0.03, 0)
    sl.build("Stair_Lights", [M['emit_bar'], M['black_metal']])


def _courtyard(M):
    x0, x1, y0, y1 = COURT_TURF
    box("Court_Turf", x0 + 0.04, x1 - 0.04, y0 + 0.04, y1 - 0.04, Z_LIV - 0.05, Z_LIV + 0.02, M['turf'])
    tr = MB()
    tr.frame(x0, x1, y0, y1, Z_LIV, Z_LIV + 0.024, 0.04, axis='Z')                     # 40 mm flush metal edge trim
    tr.frame(x0 - 0.006, x1 + 0.006, y0 - 0.006, y1 + 0.006, Z_LIV - 0.004, Z_LIV + 0.001, 0.006, axis='Z')   # shadow line
    tr.build("Court_TurfTrim", M['black_metal'])
    # planter ring around the tree in the canopy cut-out (landscape puts the olive at the hole centre)
    hx, hy = (CAN_HOLE[0] + CAN_HOLE[1]) / 2, (CAN_HOLE[2] + CAN_HOLE[3]) / 2
    pr = MB()
    pr.cylinder(hx, hy, Z_LIV + 0.02, Z_LIV + 0.04, 0.9, seg=32)
    pr.build("Court_TreeRing", M['pebble'], smooth=True)
    st = MB()
    _ring(st, (hx, hy, Z_LIV + 0.02), 0.9, 0.94, 0.06, 'Z', 0, seg=40)                 # steel planter ring edge
    st.build("Court_TreeRingEdge", M['black_metal'], smooth=True)
# living-wall species: (card material key, card size, cards per m², how far the plant stands proud of the felt (min, max),
#                       tilt of the card away from the wall plane (rad), extra downward hang, underlayer clump material key)
GW_SPECIES = {
    'fern':   ('gw_fern',   0.34, 46.0,  (0.18, 0.34), 0.55, 0.25, 'gw_under'),        # radial fronds - stand well proud
    'broad':  ('gw_broad',  0.15, 190.0, (0.10, 0.26), 0.75, 0.15, 'gw_under'),        # glossy round leaves
    'filler': ('gw_filler', 0.13, 240.0, (0.06, 0.18), 0.85, 0.10, 'gw_under'),        # small-leaved dark filler
    'lime':   ('gw_lime',   0.13, 220.0, (0.08, 0.20), 0.85, 0.10, 'gw_under_lime'),   # lime-green mounds
    'sedge':  (None,        0.0,  0.0,   (0.06, 0.14), 0.0,  0.0,  'gw_under_lime'),   # fine hanging grass (blade geometry)
    'rust':   ('gw_rust',   0.16, 140.0, (0.10, 0.22), 0.7,  0.05, 'gw_under'),        # bromeliad-red accents
    'silver': ('gw_silver', 0.15, 170.0, (0.08, 0.20), 0.8,  0.05, 'gw_under'),        # silver-sage accents
}
GW_SWATHS = ['fern', 'filler', 'sedge', 'broad', 'lime', 'rust', 'fern', 'silver', 'filler', 'broad', 'sedge', 'lime']


def _gw_species(x, z, rng):
    """Which species grows at (x, z): diagonal swaths running from lower-left to upper-right (photo 15), their edges
    wandering, with a little random intermixing at the boundaries."""
    u = (x - GREEN_X0) * 0.62 + (z - GW_Z0) * 0.95 + 0.30 * math.sin(1.9 * x + 0.7 * z) + 0.18 * math.sin(4.1 * z - 1.3 * x)
    k = int(u / 0.85) % len(GW_SWATHS)
    if rng.random() < 0.12:                                                    # stragglers of the neighbouring swath
        k = (k + rng.choice((-1, 1))) % len(GW_SWATHS)
    sp = GW_SWATHS[k]
    if sp == 'rust' and rng.random() > 0.28:                                   # the red bromeliads come as patches, not a band
        sp = 'filler'
    return sp


def _green_wall(M):
    """Living wall in the north arm's recess (photos 03/10/15): dark felt substrate, a dense underlayer of dark clumps
    for depth, then explicit leaf cards / blade tufts per species standing 6-35 cm proud, trailing tendrils, drip line,
    and uplights grazing the wall from the paving."""
    rng = random.Random(21)
    box("GreenWall_Felt", GREEN_X0 - 0.02, GREEN_X1 + 0.02, GW_Y, GW_Y + 0.04, GW_Z0 - 0.06, GW_Z1 + 0.06, LOCAL['felt'])
    # irrigation trays: horizontal black planter rows every 0.30 m (the pockets the plants grow from)
    tr = MB()
    z = GW_Z0 + 0.15
    while z < GW_Z1:
        tr.box(GREEN_X0, GREEN_X1, GW_Y - 0.05, GW_Y, z - 0.015, z + 0.015)
        z += 0.30
    tr.build("GreenWall_Trays", M['black'])
    # ---- underlayer: overlapping dark clumps hugging the felt (hide the substrate, give the wall body)
    gw = MB()
    umats = ['gw_under', 'gw_under_lime']
    z = GW_Z0 + 0.05
    row = 0
    while z < GW_Z1 - 0.02:
        x = GREEN_X0 + 0.06 + (0.06 if row % 2 else 0.0)
        while x < GREEN_X1 - 0.04:
            sp = _gw_species(x, z, rng)
            um = GW_SPECIES[sp][6]
            r = rng.uniform(0.075, 0.12)
            gw.blob((x + rng.uniform(-0.03, 0.03), GW_Y - r * 0.55, z + rng.uniform(-0.03, 0.03)), r, seg=8, rings=5, jitter=0.6,
                    seed=rng.randint(0, 9999), mi=umats.index(um), squash=rng.uniform(0.8, 1.2), ry=0.75, rx=1.15)
            x += 0.12
        z += 0.11
        row += 1
    gw.build("GreenWall_Under", [LOCAL['gw_under'], LOCAL['gw_under_lime']], smooth=True)
    # ---- species layer: explicit leaf cards (one mesh per species material) + sedge blade tufts
    cards = {k: MB() for k in GW_SPECIES if GW_SPECIES[k][0]}
    sedge = MB()
    area = (GREEN_X1 - GREEN_X0) * (GW_Z1 - GW_Z0)
    n_samples = int(area * 260)
    for i in range(n_samples):
        x = rng.uniform(GREEN_X0 + 0.04, GREEN_X1 - 0.04); z = rng.uniform(GW_Z0 + 0.03, GW_Z1 - 0.03)
        sp = _gw_species(x, z, rng)
        matkey, size, dens, proud, tilt, hang, _ = GW_SPECIES[sp]
        if sp == 'sedge':
            if rng.random() < 0.28:
                r = rng.uniform(0.09, 0.14)
                _tuft(sedge, (x, GW_Y - rng.uniform(*proud) * 0.4, z), r, rng, mi=0, blades=rng.randint(14, 22),
                      lean_dir=(rng.uniform(-0.3, 0.3), -1.0, -0.55), h_mult=3.2, r0=0.006)
            continue
        if rng.random() > dens / 260.0:
            continue
        p = rng.uniform(*proud)
        # card normal: outward (-Y) tilted a random amount, biased downward for hanging habits
        th = rng.uniform(0, 2 * math.pi)
        t = rng.uniform(0.15, 1.0) * tilt
        n = Vector((math.sin(t) * math.cos(th), -math.cos(t), math.sin(t) * math.sin(th) - hang))
        c = (x, GW_Y - p, z)
        s = size * rng.uniform(0.7, 1.3)
        _card(cards[sp], c, n, s, rng.uniform(0, 2 * math.pi), 0, aspect=1.0 if sp in ('fern', 'filler', 'lime') else rng.uniform(0.7, 1.0))
        if sp in ('broad', 'rust', 'silver'):                             # a second, half-hidden leaf behind each
            n2 = Vector((math.sin(t * 0.6) * math.cos(th + 1.3), -math.cos(t * 0.6), math.sin(t * 0.6) * math.sin(th + 1.3) - hang * 0.5))
            _card(cards[sp], (x + rng.uniform(-0.04, 0.04), GW_Y - p * 0.55, z + rng.uniform(-0.04, 0.04)), n2, s * 0.85, rng.uniform(0, 6.3), 0)
    for sp, mb_ in cards.items():
        ob = mb_.build(f"GreenWall_{sp.capitalize()}", LOCAL[GW_SPECIES[sp][0]], recalc=False)
        _assign_card_uvs(ob)
    sedge.build("GreenWall_Sedge", LOCAL['gw_sedge'], smooth=True)
    # trailing tendrils drooping off the wall + a few small white flowers + the drip line along the top
    td = MB()
    rng2 = random.Random(31)
    for i in range(110):
        x = rng2.uniform(GREEN_X0 + 0.2, GREEN_X1 - 0.2); z = rng2.uniform(GW_Z0 + 0.35, GW_Z1 - 0.1)
        yf = GW_Y - 0.12
        L = rng2.uniform(0.25, 0.75); dx = rng2.uniform(-0.12, 0.12)
        pts = [(x, yf, z), (x + dx * 0.4, yf - 0.12, z - L * 0.35), (x + dx, yf - 0.17, z - L * 0.7), (x + dx * 1.3, yf - 0.16, z - L)]
        td.path_tube(pts, 0.006, seg=5, mi=0)
        for k in range(5):
            t = (k + 1) / 6
            px = x + dx * t * 1.3; pz = z - L * t; py = yf - 0.16 * min(1.0, t * 1.5)
            _card(td, (px + rng2.uniform(-0.03, 0.03), py - 0.03, pz), (rng2.uniform(-0.4, 0.4), -0.8, rng2.uniform(-0.6, 0.1)), 0.07, rng2.uniform(0, 6.3), 1)
    ob = td.build("GreenWall_Tendrils", [M['green2'], LOCAL['gw_filler']], recalc=False)
    _assign_card_uvs(ob)
    fl = MB()
    for i in range(26):
        x = rng2.uniform(GREEN_X0 + 0.2, GREEN_X1 - 0.2); z = rng2.uniform(GW_Z0 + 0.2, GW_Z1 - 0.15)
        fl.sphere((x, GW_Y - 0.19, z), 0.016, seg=8, rings=5)
    fl.build("GreenWall_Flowers", M['ceramic'], smooth=True)
    dl = MB()
    dl.tube((GREEN_X0 - 0.05, GW_Y - 0.06, GW_Z1 + 0.03), (GREEN_X1 + 0.05, GW_Y - 0.06, GW_Z1 + 0.03), 0.006, 0.006, seg=8)
    x = GREEN_X0 + 0.25
    while x < GREEN_X1:
        dl.cylinder(x, GW_Y - 0.06, GW_Z1 + 0.0, GW_Z1 + 0.03, 0.004, seg=6)
        x += 0.5
    dl.build("GreenWall_DripLine", M['black'], smooth=True)
    # uplights set in the paving band in front of the wall, grazing upward (photo 03: warm pools climbing the foliage)
    ul = MB()
    n_up = 7
    for i in range(n_up):
        x = GREEN_X0 + 0.7 + i * (GREEN_X1 - GREEN_X0 - 1.4) / (n_up - 1)
        ul.cylinder(x, NA_Y0 - 0.42, Z_LIV - 0.005, Z_LIV + 0.012, 0.055, seg=14, mi=0)
        ul.cylinder(x, NA_Y0 - 0.42, Z_LIV + 0.012, Z_LIV + 0.016, 0.062, seg=14, mi=1)
        add_light(f"GreenWall_Up_{i}", 'SPOT', (x, NA_Y0 - 0.42, Z_LIV + 0.03), 110, (1.0, 0.86, 0.62), size=0.04,
                  spot=math.radians(62), blend=0.6, target=(x, GW_Y - 0.15, GW_Z1 - 0.3))
    ul.build("GreenWall_Uplights", [M['emit_down'], M['steel']])


def _east_boundary(M):
    sc = MB()
    slats(sc, 'Y', TY0 + 0.2, 9.0, TX1 - 0.02, 0.05, Z_LIV, Z_LIV + 2.6, w=0.05, gap=0.05, sign=-1)
    sc.box(TX1 - 0.12, TX1 - 0.02, TY0 + 0.2, 9.0, Z_LIV + 2.55, Z_LIV + 2.62)
    sc.box(TX1 - 0.12, TX1 - 0.02, TY0 + 0.2, 9.0, Z_LIV, Z_LIV + 0.06)
    sc.build("East_Screen", M['dark_slats'])
    box("East_Wall", TX1 - 0.35, TX1, 9.0, NA_Y1, Z_LIV, Z_LIV + 2.75, M['white'])
    # outdoor shower: travertine panel + rain head near the pool's NE corner (photo 15 right)
    sh = MB()
    sh.box(TX1 - 0.55, TX1 - 0.35, 9.3, 11.3, Z_LIV, Z_LIV + 2.85, 0)
    sh.box(TX1 - 0.9, TX1 - 0.55, 10.25, 10.35, Z_LIV + 2.55, Z_LIV + 2.6, 1)
    sh.cylinder(TX1 - 0.85, 10.3, Z_LIV + 2.53, Z_LIV + 2.55, 0.12, seg=20, mi=1)
    sh.box(TX1 - 0.6, TX1 - 0.55, 10.25, 10.35, Z_LIV + 1.0, Z_LIV + 1.15, 1)
    sh.build("Shower_Panel", [M['trav_grey'], M['chrome']])
    # drain grate in the paving under it
    box("Shower_Drain", TX1 - 1.4, TX1 - 0.6, 9.8, 10.8, Z_LIV - 0.004, Z_LIV + 0.002, M['black_metal'])


def _furniture(M):
    z = Z_LIV + 0.02
    teak, cush, endgrain = 0, 1, 2
    fu = MB()
    # --- lounge group on the turf outside the family pavilion (photos 03 / 22): two 3-seat sofas facing each other
    #     across a low square coffee table, an armchair closing each end
    cx, cy = 16.4, 13.6
    outdoor_sofa(fu, cx, cy + 1.55, 2.35, rot=0.0, z=z, mi_frame=teak, mi_cushion=cush, seats=3)          # north sofa faces south
    outdoor_sofa(fu, cx, cy - 1.55, 2.35, rot=math.pi, z=z, mi_frame=teak, mi_cushion=cush, seats=3)      # south sofa faces north
    outdoor_sofa(fu, cx - 2.05, cy, 0.95, rot=math.pi / 2, z=z, mi_frame=teak, mi_cushion=cush, seats=1)  # west armchair faces east
    outdoor_sofa(fu, cx + 2.05, cy, 0.95, rot=-math.pi / 2, z=z, mi_frame=teak, mi_cushion=cush, seats=1) # east armchair faces west
    _slatted_table(fu, cx, cy, z, 1.25, 1.25, h=0.33, mi=teak, planks=5)
    # --- under the canopy, in front of the green wall (photo 15): sofa + sofa, two square tables, teak stools
    outdoor_sofa(fu, 20.4, 16.55, 2.3, rot=0.0, z=z, mi_frame=teak, mi_cushion=cush, seats=3)              # faces south
    outdoor_sofa(fu, 23.55, 14.1, 1.95, rot=-math.pi / 2, z=z, mi_frame=teak, mi_cushion=cush, seats=2)     # faces west
    _slatted_table(fu, 20.2, 15.0, z, 1.2, 1.2, h=0.33, mi=teak)
    _slatted_table(fu, 21.35, 15.0, z, 1.1, 1.1, h=0.33, mi=teak)
    for sx in (18.75, 19.15):                                                                            # solid teak side stools (end grain on top)
        fu.cbox(sx, 16.4, z + 0.19, 0.36, 0.36, 0.38, teak)
        fu.cbox(sx, 16.4, z + 0.385, 0.34, 0.34, 0.01, endgrain)
    # --- lounge chairs against the dark slat screen, east of the pool (photo 24 right)
    for y in (5.0, 6.7):
        outdoor_sofa(fu, 23.5, y, 1.05, rot=-math.pi / 2, z=z, mi_frame=teak, mi_cushion=cush, seats=1)
    _slatted_table(fu, 23.5, 5.85, z, 0.45, 0.45, h=0.42, mi=teak, planks=3)
    # --- small round table + two stools by the gym door (photo 20)
    round_table(fu, 13.0, 16.95, z, 0.32, h=0.46, top_t=0.05, mi=teak, legs='drum')
    fu.cylinder(12.45, 16.95, z, z + 0.42, 0.17, seg=14, mi=teak)
    fu.cylinder(13.55, 16.95, z, z + 0.42, 0.17, seg=14, mi=teak)
    fu.build("Court_Furniture", [M['teak'], M['fabric'], M['oak']], bevel=0.012)
    # --- accessories: books, tray + tumblers, folded blanket, lanterns, moss bowls, potted agave
    ac = MB()
    books(ac, cx - 0.42, cy - 0.32, z + 0.33, n=2, mi=0, rot=0.15, w=0.28, d=0.22)
    ac.rbox(cx + 0.08, cx + 0.53, cy - 0.5, cy - 0.17, z + 0.33, z + 0.35, 0.006, 1)                      # tray
    _tumbler(ac, cx + 0.21, cy - 0.35, z + 0.35, 2); _tumbler(ac, cx + 0.39, cy - 0.31, z + 0.35, 2)
    ac.drape(cx + 0.35, cx + 1.05, cy + 1.05, cy + 1.8, z + 0.62, t=0.03, mi=3, sag=0.05, seed=4)         # blanket on the north sofa
    _lantern(ac, 20.45, 14.75, z + 0.35, 4, 5, 6, w=0.2, h=0.36)
    _lantern(ac, 21.55, 15.25, z + 0.35, 4, 5, 6, w=0.16, h=0.3)
    books(ac, 21.15, 14.75, z + 0.35, n=2, mi=0, rot=-0.2, w=0.26, d=0.2)
    ac.build("Court_Accessories", [M['book'], M['black_metal'], M['glass'], M['throw'], M['black_metal'], M['glass_frost'], M['lampshade']], smooth=False)
    bw = MB()                                                                                              # moss bowls (photo 15)
    vase(bw, 20.2, 15.0, z + 0.34, h=0.12, r=0.24, mi=0, style='bowl')
    bw.blob((20.2, 15.0, z + 0.46), 0.2, seg=12, rings=7, jitter=0.35, seed=5, mi=1, squash=0.5)
    vase(bw, cx, cy + 0.12, z + 0.33, h=0.11, r=0.22, mi=0, style='bowl')
    bw.blob((cx, cy + 0.12, z + 0.45), 0.19, seg=12, rings=7, jitter=0.35, seed=6, mi=1, squash=0.5)
    bw.build("Court_Bowls", [M['ceramic_black'], M['moss']], smooth=True)
    ag = MB()
    ag.lathe(12.0, 17.25, z, [(0, 0), (0.22, 0), (0.25, 0.32), (0.22, 0.32), (0.2, 0.3), (0, 0.3)], seg=24, mi=0)   # pot
    ag.cylinder(12.0, 17.25, z + 0.29, z + 0.31, 0.21, seg=20, mi=1)                                         # soil
    _agave(ag, 12.0, 17.25, z + 0.3, n=16, L=0.55, mi=2, seed=3)
    ag.build("Court_Agave", [M['clay'], M['soil'], M['olive']], smooth=True)
    # (the teak dining set lives on the roof dining terrace - interior_upper; photos 22/03 show only lounge seating on the turf)


def _rear_garden(M):
    # rear lawn at the living level behind the main block and the north arm
    RX0, RX1 = -13.0, TX1
    box("Rear_Fill", RX0 - 10, RX1 + 6, MY1, REAR_Y1 + 0.3, -0.34, Z_LIV - 0.05, M['mulch'])
    box("Rear_Lawn", RX0, RX1, MY1 + 0.05, REAR_Y1 - 1.1, Z_LIV - 0.05, Z_LIV, M['lawn_rear'])
    box("Rear_Path", MX0 + 0.4, MX1 - 0.4, MY1, MY1 + 0.9, Z_LIV - 0.05, Z_LIV + 0.01, M['pavers_big'])
    # white retaining wall + planted strip in front of it, hillside rising behind (photo 17)
    box("Rear_Wall", RX0 - 1.0, RX1 + 1.0, REAR_Y1, REAR_Y1 + 0.3, Z_LIV - 0.3, Z_LIV + 1.15, M['white'])
    box("Rear_WallCap", RX0 - 1.02, RX1 + 1.02, REAR_Y1 - 0.02, REAR_Y1 + 0.32, Z_LIV + 1.15, Z_LIV + 1.2, M['concrete'])
    wh = MB()
    x = RX0 + 0.5
    while x < RX1:                                                                        # weep holes along the wall base
        wh.box(x - 0.02, x + 0.02, REAR_Y1 - 0.004, REAR_Y1 + 0.02, Z_LIV + 0.04, Z_LIV + 0.08)
        x += 2.0
    wh.build("Rear_WeepHoles", M['black'])
    box("Rear_Bed", RX0, RX1, REAR_Y1 - 1.1, REAR_Y1, Z_LIV - 0.05, Z_LIV + 0.02, M['mulch'])
    fb = MB()
    rng = random.Random(9)
    x = RX0 + 0.5
    while x < RX1 - 0.4:
        r = rng.uniform(0.45, 0.7)
        mi = 0 if rng.random() < 0.6 else (1 if rng.random() < 0.5 else 2)
        cx_, cy_ = x, REAR_Y1 - 0.55 + rng.uniform(-0.1, 0.1)
        fb.blob((cx_, cy_, Z_LIV + r * 0.85), r, seg=10, rings=7, jitter=0.5, seed=rng.randint(0, 999), mi=mi, squash=1.15)
        for k in range(3):                                                                # satellite clumps break the sphere silhouette
            fb.blob((cx_ + rng.uniform(-0.4, 0.4), cy_ + rng.uniform(-0.25, 0.25), Z_LIV + r * rng.uniform(0.6, 1.4)), r * 0.45,
                    seg=8, rings=6, jitter=0.5, seed=rng.randint(0, 999), mi=mi, squash=1.0)
        x += rng.uniform(0.7, 1.0)
    ob = fb.build("Rear_Shrubs", [M['shrub'], M['fabric_rust'], M['fabric_white']], smooth=True)
    ob["leaf_cards"] = {"leaf": "cluster_shrub", "size": 0.15, "density": 90.0, "group": "all"}
    vg = ob.vertex_groups.new(name="all"); vg.add(list(range(len(ob.data.vertices))), 1.0, 'REPLACE')
    ch = MB()
    for i in range(120):
        ch.cbox(rng.uniform(RX0 + 0.2, RX1 - 0.2), rng.uniform(REAR_Y1 - 1.05, REAR_Y1 - 0.15), Z_LIV + 0.025,
                rng.uniform(0.04, 0.09), rng.uniform(0.02, 0.04), 0.012, 0, rng.uniform(0, math.pi))
    ch.build("Rear_BarkChips", M['bark'])
    # hillside behind the retaining wall: a smooth grid surface following landscape.hill_z (the trees stand on that
    # curve) with gentle undulation, dark scrub ground-cover material
    from .landscape import hill_z
    hl = MB()
    hx0, hx1, hy0, hy1 = RX0 - 60, RX1 + 60, REAR_Y1 + 0.3, 110.0
    nx, ny = 44, 40
    hn = random.Random(5)
    def hz(x, y):
        return hill_z(y) + 0.35 * math.sin(0.23 * x + 0.4) * math.sin(0.19 * y) + 0.15 * math.sin(0.7 * x) * math.cos(0.5 * y)
    grid = [[(hx0 + (hx1 - hx0) * i / nx, hy0 + (hy1 - hy0) * j / ny) for j in range(ny + 1)] for i in range(nx + 1)]
    for i in range(nx):
        for j in range(ny):
            (xa, ya), (xb, yb) = grid[i][j], grid[i + 1][j + 1]
            hl.quad((xa, ya, hz(xa, ya) - 0.3), (xb, ya, hz(xb, ya) - 0.3), (xb, yb, hz(xb, yb) - 0.3), (xa, yb, hz(xa, yb) - 0.3))
    hl.box(hx0, hx1, hy0 - 0.05, hy0 + 0.3, Z_LIV - 0.4, Z_LIV + 0.7)                                    # toe of the slope behind the wall
    hl.build("Rear_Hill", LOCAL['hillside'], smooth=True, recalc=False)
    # teak chaises on the lawn (photo 17): slatted deck, quilted cushion following the raked back, wheels at the foot
    lg = MB()
    for x in (-9.2, -7.6):
        y0, y1 = 27.25, 29.15                                                                          # foot (south) .. head (north)
        for k in range(14):                                                                            # deck slats
            yy = y0 + 0.05 + (y1 - 0.25 - y0 - 0.1) * k / 13
            lg.cbox(x, yy, Z_LIV + 0.30, 0.68, 0.075, 0.025, 0)
        lg.cbox(x - 0.33, (y0 + y1) / 2, Z_LIV + 0.30, 0.04, y1 - y0, 0.06, 0); lg.cbox(x + 0.33, (y0 + y1) / 2, Z_LIV + 0.30, 0.04, y1 - y0, 0.06, 0)
        for sx in (-1, 1):
            lg.cbox(x + sx * 0.3, y1 - 0.15, Z_LIV + 0.14, 0.05, 0.05, 0.28, 0)                         # rear legs
            lg.tube((x + sx * 0.36 - 0.02, y0 + 0.15, Z_LIV + 0.09), (x + sx * 0.36 + 0.02, y0 + 0.15, Z_LIV + 0.09), 0.09, 0.09, seg=18, mi=0)  # wheels
            lg.cbox(x + sx * 0.3, y0 + 0.15, Z_LIV + 0.2, 0.04, 0.04, 0.22, 0)                            # front legs to the axle
        lg.rcbox(x, y0 + 0.62, Z_LIV + 0.36, 0.64, 1.2, 0.07, 0.03, 1, puff=0.45)                      # seat pad
        # raked back: cushion tilted 40 deg on a slatted back frame
        ang = math.radians(40)
        for k in range(5):
            t = 0.08 + k * 0.13
            lg.cbox(x, y1 - 0.35 + t * math.cos(ang) - 0.2, Z_LIV + 0.33 + t * math.sin(ang), 0.62, 0.07, 0.02, 0)
        lg.pillow(x, y1 - 0.15 - 0.05, Z_LIV + 0.33 + 0.36 * math.sin(ang) - 0.06, w=0.62, d=0.68, t=0.09, mi=1, pitch=ang)
        lg.pillow(x, y1 - 0.02, Z_LIV + 0.33 + 0.72 * math.sin(ang) - 0.05, w=0.40, d=0.28, t=0.10, mi=1, pitch=ang + 0.15)   # headrest roll
    table(lg, -8.4, 29.5, Z_LIV, 0.5, 0.5, h=0.45, top_t=0.04, mi_top=0, legs='four', leg_w=0.04)
    lg.build("Rear_Loungers", [M['teak'], M['fabric_white']], bevel=0.012)
    rr = MB()
    glass_rail(rr, [(RX0 + 0.05, MY1 + 0.2), (RX0 + 0.05, REAR_Y1 - 1.2)], Z_LIV, h=1.05)
    glass_rail(rr, [(RX1 - 0.05, NA_Y1 + 0.2), (RX1 - 0.05, REAR_Y1 - 1.2)], Z_LIV, h=1.05)
    rr.build("Rear_Rails", [M['glass'], M['steel']])
    # guest wing north strip: gravel path + clipped hedge (photo 25)
    box("Guest_Gravel", 14.0, TX1, NA_Y1 + 0.05, NA_Y1 + 1.6, Z_LIV - 0.02, Z_LIV + 0.01, M['pebble'])
    hg = MB()
    x = 14.4
    while x < TX1 - 0.3:
        hg.blob((x, NA_Y1 + 2.3, Z_LIV + 0.75), 0.6, seg=10, rings=7, jitter=0.3, seed=int(x * 7), squash=1.2)
        x += 0.75
    ob = hg.build("Guest_Hedge", [M['shrub']], smooth=True)
    ob["leaf_cards"] = {"leaf": "cluster_shrub", "size": 0.15, "density": 110.0}
    add_light("Rear_Wall_Wash", 'AREA', (-3.0, REAR_Y1 - 0.4, Z_LIV + 0.1), 150, (1.0, 0.85, 0.6), size=0.5) if False else None
    for x in (-10.0, -4.0, 2.0, 8.0, 14.0, 20.0):
        add_light(f"Rear_Up_{x:.0f}", 'SPOT', (x, REAR_Y1 - 0.35, Z_LIV + 0.05), 60, (1.0, 0.86, 0.62), size=0.05,
                  spot=math.radians(70), blend=0.6, target=(x, REAR_Y1 + 0.1, Z_LIV + 1.4))


def build(M):
    _local_materials(M)
    _ground(M)
    _motor_court(M)
    _front_lawn(M)
    _terrace(M)
    _pool(M)
    _fire(M)
    _terrace_stair(M)
    _courtyard(M)
    _green_wall(M)
    _east_boundary(M)
    _furniture(M)
    _rear_garden(M)
