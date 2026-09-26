"""Great room + dining staging, window dressings, fixtures and lights for the main floor's rear rooms (photos 08-14).

House-local helper of interior_main (imported only by it, prefix ig_ = INT_GREAT).  Everything here is STAGING or a
light fitting: the pieces are modelled after the ones in the listing photos (a grey U sectional with a chaise, a carved
teak jhula, black carved rush chairs, a Persian rug, a glass table on scrolled iron, an espresso parquet dining set, a
brushed-nickel bell chandelier, a brass hugger fan), placed through the solved photo cameras (positions: notes).
"""
import math
import random
from mathutils import Vector
from .plan import *
from archviz.mesh import MB
from archviz.lights import add_light, area_light
from archviz.cladding import Face
from archviz import furnish as fu
from archviz import plants as _pl
from archviz import phototex as ptx
from . import interior_main as im

LC = im.LC
ZC = im.ZC
XR = im.XR
WARM = im.WARM
NEUTRAL = im.NEUTRAL
DAY = (1.0, 0.98, 0.95)                 # daylight through the rear windows (the photos are white-balanced to neutral walls)


def _op(name):
    return next(o for o in OPENINGS if o['name'] == name)


# ================================================================ photo textures (flat decor rectified from the listing photos)
# key -> (photo, canvas quad TL, TR, BR, BL in photo pixels (read on photo_grid zooms at 2.5-5x), texture size, options)
PHOTO_TEX = {
    'city_10':      ('10', [(208.8, 348.0), (361.2, 345.2), (362.8, 576.0), (210.0, 577.2)], (300, 450), {}),
    'blossom_10':   ('10', [(668.0, 315.2), (814.8, 314.8), (815.2, 429.2), (668.0, 429.2)], (400, 310), {}),
    'cafe_09':      ('09', [(77.3, 314.0), (172.7, 336.0), (172.3, 470.7), (76.7, 472.7)], (240, 300), {}),
    'medallion_08': ('08', [(1251.0, 410.0), (1320.0, 401.4), (1320.0, 484.4), (1251.6, 484.4)], (200, 220), {'mirror_half': True}),
    'print_b_14':   ('14', [(618.0, 452.0), (650.0, 455.0), (650.0, 498.0), (618.0, 497.0)], (160, 120), {}),
}
PHOTOS = __import__('os').path.join(__import__('os').path.dirname(__import__('os').path.abspath(__file__)), 'photos')


def photo_tex(key, rough=0.45, coat=0.15):
    """Material showing the rectified photo quad `key` (PHOTO_TEX) on a UV quad.  'mirror_half' mirrors the left half
    onto the right (the medallion's right side is hidden by a plant in 08)."""
    import bpy
    import numpy as np
    ph, quad, size, opt = PHOTO_TEX[key]
    name = f"PhotoTex_IG_{key}"
    img = bpy.data.images.get(name)
    if img is None:
        rgb = ptx.rectify_array(ptx._photo_array(__import__('os').path.join(PHOTOS, f"{ph}.jpg")), quad, size)
        if opt.get('mirror_half'):
            w = rgb.shape[1]
            rgb[:, w - w // 2:] = rgb[:, :w // 2][:, ::-1]
        w, h = size
        img = bpy.data.images.new(name, w, h, alpha=False)
        px = np.ones((h, w, 4), np.float32)
        px[..., :3] = rgb[::-1]
        img.pixels.foreach_set(px.ravel())
        img.update()
        try:
            img.pack()
        except RuntimeError:
            pass
    return ptx.photo_material(f"Photo_IG_{key}", img, rough=rough, coat=coat)


def photo_art(M, name, key, along, a0, a1, b, s, z0, z1, frame_mat, fw=0.06, d=0.035):
    """A framed picture (im.frame_art ring) whose visible canvas is the rectified photo texture `key`."""
    art = MB()
    im.frame_art(art, along, a0, a1, b, s, z0, z1, 0, 1, fw=fw, d=d)
    art.build(name, [frame_mat, M['paper']])
    cz0, cz1, ca0, ca1 = z0 + fw, z1 - fw, a0 + fw, a1 - fw
    ptx.uv_quad_mesh(name + "_Canvas", ptx.rect_corners(along, ca0, ca1, b + s * 0.0152, cz0, cz1, s), photo_tex(key), coll='House')


# ================================================================ layout (world coordinates; see notes_INT_GREAT for the evidence)
G = dict(
    # U sectional (photos 08, 09, 10 through INT_CAM's cameras): an armless chaise at the west end (its east side x 2.40, front
    # y 8.13 in 09), a two-seat run along the garage wall, a corner seat, and a return facing west (front x ~4.5, arm end
    # y ~8.6-8.85 in 08; camera 10 stands just north of it)
    sec_y0=6.50, sec_d=1.05, chaise=(1.55, 2.47, 8.10), mid=(2.47, 4.10), corner=(4.10, 5.18), ret_y1=8.44,
    rug=(1.56, 5.10, 8.16, 10.45),                   # Tabriz, fringed E/W ends (09: near corner (3.08, 8.16), far (1.56, 10.32))
    table=(3.05, 9.25, 1.25, 0.66),                  # glass cocktail table on scrolled iron (x, y, w, d; 09 legs 2.9..3.2, 9.0..9.4)
    side=(0.58, 6.87),                               # glass side table in the SW corner (09: top edge y 6.43 .. 7.26 at x 0.58)
    tv=(10.78, 0.95),                                # media console centre y, front x (10: y 10.33 .. 11.23; 09 agrees)
    swing=(4.68, 10.72),                             # jhula centre (08: post bases (3.88, 10.80) / (5.59, 10.50); 09: x 3.4-3.6)
    chair1=(1.75, 11.22, 0.10), bench=(2.45, 11.30), chair2=(3.30, 11.05, -0.15),   # 09 / 08 leg contacts, 08 back tops
    fan=(3.02, 8.85),                                # fan canopy (INT_CAM solve +/- 0.07)
    cans=[(1.18, 8.33), (1.18, 9.70)],               # eyeball cans either side of the chase (09, 10)
    register=(2.05, 10.85),                          # ceiling supply register (09: (2.17, 11.02); 08: (1.76, 10.47))
    cafe=(2.60, 3.15, 1.35, 1.96),                   # 'Cafe Terrace' on the garage wall above the sectional (09)
)
D = dict(
    table=(7.64, 10.00, 1.62, 0.96),                # long axis N-S (14: NE top corner (8.12, 10.81); 11: 2 chairs per long side)
    chand=(7.13, 9.80),                             # canopy: 14 says (7.18, 9.85), 11 ~0.1 m west; centred in the room
    chand_drop=0.86,                                # shade bottoms at z ~1.64 (14)
    clock=(8.53, 1.74, 0.175),                      # 11: centre z 1.72, 0.35 across (through a provisional p11)
    register=(8.05, 11.30),                         # photos 11, 14 (the supply register by the slider)
    jali=(4.60, 5.42, 0.95, 1.45),                  # carved folding panel on the rear wall behind the swing (08)
)


# ================================================================ plants (custom species on archviz.plants.Foliage)
def _plant_mats():
    MM = _pl.mats()
    if 'corn' not in MM:
        MM['corn'] = _pl.leaf_shader("LeafCornPlant", 'strap', (0.07, 0.18, 0.05, 1), (0.10, 0.24, 0.07, 1), (0.14, 0.30, 0.09, 1),
                                     under=(0.16, 0.26, 0.12, 1), translucent=0.3, rough=0.4, coat=0.2, band=0.0, rib=0.10,
                                     rib_col=(0.45, 0.52, 0.18, 1))
        MM['pothos'] = _pl.leaf_shader("LeafPothos", 'heart', (0.10, 0.26, 0.05, 1), (0.16, 0.34, 0.07, 1), (0.30, 0.42, 0.10, 1),
                                       under=(0.20, 0.32, 0.12, 1), translucent=0.3, rough=0.3, coat=0.35, p=0.9, q=0.7, veins=5, rib=0.015)
        MM['lily'] = _pl.leaf_shader("LeafPeaceLily", 'elliptic', (0.04, 0.13, 0.04, 1), (0.06, 0.18, 0.05, 1), (0.10, 0.23, 0.07, 1),
                                     under=(0.14, 0.24, 0.10, 1), translucent=0.2, rough=0.3, coat=0.45, p=1.0, q=1.1, veins=9, vein_k=0.6,
                                     rib=0.012)
    return MM


def _corn(F, x, y, z, h, canes=(1.0, 0.72, 0.5), spread=1.0):
    """Corn plant (Dracaena fragrans): bare woody canes of different heights, each topped by a loose rosette of long,
    broad strap leaves that rise and then arch over and down (tips below the rosette), with a pale centre stripe."""
    rng = F.rng
    for k, hf in enumerate(canes):
        ox, oy = (0.0, 0.0) if k == 0 else (rng.uniform(-0.08, 0.08), rng.uniform(-0.08, 0.08))
        hc = h * hf * 0.62
        top = Vector((x + ox + rng.uniform(-0.06, 0.06), y + oy + rng.uniform(-0.06, 0.06), z + hc))
        F.wood.tube((x + ox, y + oy, z - 0.02), tuple(top), 0.032, 0.024, seg=8, mi=2)
        n = 22 + int(10 * hf)
        for i in range(n):
            az = rng.uniform(0, 2 * math.pi)
            out = Vector((math.cos(az), math.sin(az), 0))
            young = rng.random() < 0.3                                     # upright young leaves in the centre
            el = rng.uniform(0.9, 1.35) if young else rng.uniform(0.25, 0.85)
            d = (out * math.cos(el) + Vector((0, 0, 1)) * math.sin(el)).normalized()
            L = rng.uniform(0.35, 0.55) if young else rng.uniform(0.55, 0.85)
            L *= spread * (0.85 + 0.3 * hf)
            W = rng.uniform(0.065, 0.095)
            side = out.cross(Vector((0, 0, 1))).normalized()
            base = top + Vector((0, 0, rng.uniform(-0.18, 0.06)))
            # archviz.plants.Foliage.leaf bends a positive droop UP for side = out x Z, so arch down with a negative one
            F.leaf('corn', base, d, side, L, W, n=6, droop=-(rng.uniform(0.4, 0.8) if young else rng.uniform(1.3, 2.1)),
                   twist=rng.uniform(-0.5, 0.5))


def _lily(F, x, y, z, h, spread=1.0, n=22):
    """Peace-lily / aglaonema clump: glossy elliptic leaves on arching petioles."""
    rng = F.rng
    for i in range(n):
        az = rng.uniform(0, 2 * math.pi)
        out = Vector((math.cos(az), math.sin(az), 0))
        el = rng.uniform(0.7, 1.35)
        d = (out * math.cos(el) + Vector((0, 0, 1)) * math.sin(el)).normalized()
        pts, dend = F.arc((x + out.x * 0.02, y + out.y * 0.02, z - 0.01), d, h * rng.uniform(0.35, 0.6), 0.006, 0.004, n=3,
                          gravity=0.25, wiggle=0.05)
        L = h * rng.uniform(0.32, 0.45) * spread
        W = L * rng.uniform(0.34, 0.42)
        side = out.cross(Vector((0, 0, 1))).normalized()
        F.leaf('lily', pts[-1], dend, side, L, W, n=4, droop=-rng.uniform(0.5, 1.1), twist=rng.uniform(-0.3, 0.3))


def _pothos(F, x, y, z, trails, seed_dir=0.0):
    """Trailing pothos: a small crown of heart leaves plus vines that run along `trails` (lists of points) with
    leaves at the nodes."""
    rng = F.rng
    for i in range(14):
        az = rng.uniform(0, 2 * math.pi)
        out = Vector((math.cos(az), math.sin(az), 0))
        d = (out * 0.7 + Vector((0, 0, 0.7))).normalized()
        side = out.cross(Vector((0, 0, 1))).normalized()
        F.leaf('pothos', (x + out.x * 0.04, y + out.y * 0.04, z + 0.02), d, side, rng.uniform(0.07, 0.11), rng.uniform(0.05, 0.08), n=3,
               droop=-rng.uniform(0.3, 1.0))
    for tr in trails:
        pts = [Vector(p) for p in tr]
        F.wood.path_tube([tuple(p) for p in pts], 0.003, seg=4, mi=2)
        for k in range(len(pts) - 1):
            a, b = pts[k], pts[k + 1]
            seg = (b - a)
            m = max(1, int(seg.length / 0.07))
            for j in range(m):
                p = a + seg * ((j + 0.5) / m)
                out = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), 0)).normalized()
                d = (out + Vector((0, 0, rng.uniform(-0.6, 0.3)))).normalized()
                side = out.cross(Vector((0, 0, 1))).normalized()
                F.leaf('pothos', p, d, side, rng.uniform(0.06, 0.10), rng.uniform(0.045, 0.07), n=2, droop=-rng.uniform(0.2, 0.9))


def plant(name, pos, species, h, pot='white', pot_r=0.2, pot_h=0.3, seed=0, trails=(), stand=None, M=None, pot_mat=None):
    """Potted custom plant; returns the pot/stem object.  stand = (r, h) draws a small wooden plant stand first."""
    MM = _plant_mats()
    x, y, z = pos
    F = _pl.Foliage(seed)
    style = _pl.POT_STYLES.get(pot, 'ceramic')
    zs = _pl.pot(F, x, y, z, pot_r, pot_h, style, 0, 1, saucer=False)
    if species == 'corn':
        _corn(F, x, y, zs, h)
    elif species == 'lily':
        _lily(F, x, y, zs, h)
    elif species == 'pothos':
        _pothos(F, x, y, zs, trails)
    slots = [pot_mat or MM[style], MM['soil'], MM['bark'] if species == 'corn' else MM['stem'], MM['stem'], MM['cane']]
    ob = F.build(name, slots)
    prune(name + "_Leaves", ymax=YB1 - EWT - 0.015, zmax=ZC - 0.005)
    return ob


def prune(obname, ymax=None, zmax=None):
    """Delete leaf quads that cross a wall plane (y > ymax) or the ceiling (z > zmax): leaves must not poke through the
    rear wall and show outside (photos 27 / 28)."""
    import bpy
    import bmesh
    ob = bpy.data.objects.get(obname)
    if ob is None:
        return
    bm = bmesh.new(); bm.from_mesh(ob.data)
    mw = ob.matrix_world
    bad = [f for f in bm.faces if any((ymax is not None and (mw @ v.co).y > ymax) or (zmax is not None and (mw @ v.co).z > zmax)
                                      for v in f.verts)]
    if bad:
        bmesh.ops.delete(bm, geom=bad, context='FACES')
        bm.to_mesh(ob.data)
    bm.free()


# ================================================================ great room
def great_room(M):
    xs = XB0 + EWT
    ym = (im.FP['y0'] + im.FP['y1']) / 2
    xf = xs + im.FP['depth']
    # ---------- sectional (U: chaise W, two seats + corner along the garage wall, a return facing W)
    sec, pil = MB(), MB()
    y0, dd = G['sec_y0'], G['sec_d']
    cx0, cx1, cyn = G['chaise']
    m0, m1 = G['mid']
    k0, k1 = G['corner']
    # the chaise is its own object: photo 08 shows it pulled back to a seat-length module (x 1.92.., north end y 7.56 -
    # 08 and 09 cannot agree on one chaise; notes_INT_GREAT), so 08 gets its own copy (interior_main.PHOTO_ONLY / PHOTO_HIDE)
    # the sofa was moved between 08 and 09 (INT_CAM joint 08-14 solve: through p08 the chaise's W end is x 1.77 +/- 0.06 and
    # its N end y 7.27 +/- 0.12; 09 puts them at 1.55 / 8.10).  08 gets its own chaise (interior_main.PHOTO_ONLY / PHOTO_HIDE).
    for (nm, a0_, a1_, y1_) in (("Great_Chaise", cx0, cx1, cyn), ("Great_ChaiseP08", 1.77, 2.69, 7.27)):
        chm, _ = MB(), MB()
        fu.sectional(chm, _, 0.0, 0.0, 0.0, [dict(kind='chaise', x0=a0_, y0=y0, x1=a1_, y1=y1_, face='+Y', n=1)], mi=0, mi_leg=1,
                     seat_h=0.47, back_h=0.86)
        chm.build(nm, [M['fabric_greige'], M['espresso']], smooth=True)
    runs = [dict(kind='seats', x0=m0, y0=y0, x1=m1, y1=y0 + dd, face='+Y', n=2),
            dict(kind='corner', x0=k0, y0=y0, x1=k1, y1=y0 + dd, face='+Y', n=1, corner_side='a1'),
            dict(kind='seats', x0=k0, y0=y0 + dd, x1=k1, y1=G['ret_y1'], face='-X', n=2, arm_r=True)]
    pl = [(2.75, y0 + 0.32, 0.78, 0.50, math.pi + 0.08, 1.25), (3.65, y0 + 0.32, 0.78, 0.50, math.pi - 0.06, 1.25),
          (k1 - 0.32, y0 + 0.42, 0.80, 0.52, math.pi * 0.75, 1.25), (k1 - 0.32, G['ret_y1'] - 0.45, 0.78, 0.48, -math.pi / 2 - 0.08, 1.25)]
    fu.sectional(sec, pil, 0.0, 0.0, 0.0, runs, mi=0, mi_leg=1, pillows=pl, mi_pil=0, seed=3, seat_h=0.47, back_h=0.86)
    sec.build("Great_Sectional", [M['fabric_greige'], M['espresso']], smooth=True)
    pil.build("Great_Pillows", [M['fabric_white']], smooth=True)
    p2 = MB()
    p2.pillow_sq(k1 - 0.34, y0 + 0.62, 0.80, 0.48, 0.48, 0.15, 0, rot=math.pi * 0.8, pitch=1.25, seed=11)
    p2.pillow_sq(k1 - 0.30, G['ret_y1'] - 0.95, 0.80, 0.46, 0.46, 0.15, 0, rot=-math.pi / 2 + 0.1, pitch=1.25, seed=12)
    p2.build("Great_PillowsTextured", [M['fabric_ivory']], smooth=True)
    # ---------- Persian rug (a single box so the Generated mapping spans it) + fringes on the short ends
    rx0, rx1, ry0, ry1 = G['rug']
    rug = MB()
    rug.box(rx0, rx1, ry0, ry1, 0.004, 0.014)
    rug.build("Rug_Great", [M['rug_persian']])
    fr = MB()
    for xe, s in ((rx0, -1), (rx1, 1)):
        for k in range(int((ry1 - ry0) / 0.012)):
            yy = ry0 + 0.006 + k * 0.012
            fr.box(min(xe, xe + s * 0.075), max(xe, xe + s * 0.075), yy - 0.0018, yy + 0.0018, 0.004, 0.0075)
    fr.build("Rug_Great_Fringe", [M['fringe']])
    # ---------- glass cocktail table on scrolled iron, with a pewter box, books, a candy bowl (08, 09, 10)
    tx, ty, tw, td = G['table']
    gl, ir = MB(), MB()
    fu.scroll_table(gl, ir, tx, ty, 0.0, w=tw, d=td, h=0.46, clip=0.11)
    fu.scroll_table(gl, ir, G['side'][0], G['side'][1], 0.0, w=0.60, d=0.80, h=0.60, clip=0.08)
    gl.build("Great_TableGlass", [M['glass_clear']])
    ir.build("Great_TableIron", [M['pewter']], smooth=True)
    acc, bk = MB(), MB()
    bx_, by_ = tx - 0.10, ty + 0.03
    for k, (w_, d_, t_) in enumerate(((0.32, 0.24, 0.028), (0.29, 0.21, 0.024))):          # two books
        z_ = 0.475 + sum((0.028, 0.024)[:k])
        bk.rbox(bx_ - w_ / 2, bx_ + w_ / 2, by_ - d_ / 2, by_ + d_ / 2, z_, z_ + t_, 0.004)
    zb_ = 0.527
    acc.rbox(bx_ - 0.13, bx_ + 0.13, by_ - 0.09, by_ + 0.09, zb_, zb_ + 0.08, 0.02)          # pewter box (08, 09, 10)
    acc.rbox(bx_ - 0.14, bx_ + 0.14, by_ - 0.10, by_ + 0.10, zb_ + 0.08, zb_ + 0.115, 0.03, puff=0.4)
    acc.path_tube([(bx_ - 0.05, by_, zb_ + 0.115), (bx_ - 0.045, by_, zb_ + 0.15), (bx_ + 0.045, by_, zb_ + 0.15), (bx_ + 0.05, by_, zb_ + 0.115)],
                  0.006, seg=6)
    acc.build("Great_TableBox", [M['pewter']], smooth=True)
    bk.build("Great_TableBooks", [M['paper']])
    bowl = MB()
    bowl.lathe(tx + 0.30, ty - 0.12, 0.475, [(0.0, 0.0), (0.05, 0.0), (0.08, 0.04), (0.075, 0.045), (0.045, 0.01), (0.0, 0.008)], seg=20)
    bowl.build("Great_CandyBowl", [M['glass_green']])
    # side-table vignette: white flowers in a glass vase, a globe, a blue bowl (10)
    sx, sy = G['side']
    vg = MB()
    vg.lathe(sx + 0.05, sy + 0.08, 0.61, [(0.0, 0.0), (0.04, 0.0), (0.05, 0.12), (0.03, 0.26), (0.035, 0.28), (0.0, 0.28)], seg=16)
    vg.build("Great_SideVase", [M['glass_clear']])
    gb = MB()
    gb.sphere((sx - 0.12, sy - 0.10, 0.76), 0.07, seg=18, rings=12)
    gb.cylinder(sx - 0.12, sy - 0.10, 0.61, 0.69, 0.012, seg=8)
    gb.build("Great_Globe", [_globe_mat(M)], smooth=True)
    bb = MB()
    bb.lathe(sx + 0.16, sy - 0.12, 0.61, [(0.0, 0.0), (0.05, 0.0), (0.09, 0.05), (0.07, 0.09), (0.0, 0.09)], seg=18)
    bb.build("Great_BlueBowl", [_m_blue(M)], smooth=True)
    _pl.stems("Great_SideFlowers", (sx + 0.05, sy + 0.08, 0.88), kind='magnolia', height=0.35, seed=41)
    prune("Great_SideFlowers_Leaves", ymax=YB1 - EWT - 0.015)
    # ---------- media console + 60" TV in the NW corner (10)
    tvy, tvx = G['tv']
    con, cg = MB(), MB()
    fu.media_console(con, cg, tvx - 0.23, tvy, math.pi / 2, w=0.92, d=0.46, h=0.53, mi=0, mi_glass=0, mi_dark=1)
    con.build("Great_MediaConsole", [M['media_black'], M['appliance_black']], smooth=False)
    cg.build("Great_MediaGlass", [M['glass_smoke']])
    tvm = MB()
    fu.flat_tv(tvm, tvx - 0.24, tvy + 0.06, math.pi / 2, w=1.36, h=0.80, z=0.575, mi_body=0, mi_screen=1)
    tvm.build("Great_TV", [M['appliance_black'], M['tv']])
    # ---------- hearth: three scrolled candle holders with pillar candles, a striped barrel vase with dried reeds (10)
    cnd, cw = MB(), MB()
    for (dy, hgt, col) in ((-0.40, 0.32, 0), (-0.33, 0.22, 1), (-0.36, 0.14, 0)):
        cy = ym - 0.47 + dy + 0.33
        cxp = xf + 0.13 + (0.05 if hgt < 0.2 else 0.0)
        cw.lathe(cxp, cy, 0.012, [(0.0, 0.0), (0.06, 0.0), (0.05, 0.03), (0.02, 0.06), (0.035, hgt * 0.5), (0.02, hgt - 0.03), (0.045, hgt - 0.01),
                                  (0.045, hgt), (0.0, hgt)], seg=12)
        cnd.cylinder(cxp, cy, 0.012 + hgt, 0.012 + hgt + (0.10 if hgt > 0.2 else 0.08), 0.034, seg=16, mi=col)
    cw.build("Great_CandleHolders", [M['bronze']], smooth=True)
    cnd.build("Great_Candles", [M['candle_orange'], M['candle_yellow']], smooth=True)
    vz = MB()
    vy = ym + 0.50
    vz.lathe(xf + 0.12, vy, 0.012, [(0.0, 0.0), (0.06, 0.0), (0.095, 0.07), (0.11, 0.18), (0.10, 0.29), (0.07, 0.36), (0.065, 0.37), (0.0, 0.37)], seg=24)
    vz.build("Great_HearthVase", [M['vase_stripe']], smooth=True)
    rd = MB()
    rng = random.Random(7)
    for k in range(16):
        a = rng.uniform(0, 2 * math.pi)
        lean = rng.uniform(0.05, 0.22)
        top = (xf + 0.12 + lean * 0.9 * math.cos(a), vy + lean * math.sin(a), 0.30 + rng.uniform(0.35, 0.55))
        rd.tube((xf + 0.12, vy, 0.18), top, 0.004, 0.0025, seg=5)
    rd.build("Great_Reeds", [M['reed']])
    # ---------- art: almond blossom over the mantel (gold), city street on the west wall (ornate gold),
    # cafe terrace on the south wall near the SW corner
    photo_art(M, "Great_ArtBlossom", 'blossom_10', 'Y', ym - 0.355, ym + 0.355, xf, +1, 1.40, 2.00, M['frame_champagne'], fw=0.095, d=0.045)
    photo_art(M, "Great_ArtCity", 'city_10', 'Y', 6.89, 7.68, xs, +1, 0.82, 1.92, M['frame_gold_ornate'], fw=0.09, d=0.045)
    photo_art(M, "Great_ArtCafe", 'cafe_09', 'X', 2.70, 3.26, 6.47, +1, 1.24, 1.92, M['frame_dark'], fw=0.035)
    photo_art(M, "Great_ArtPrintB", 'print_b_14', 'X', 3.62, 4.30, 6.47, +1, 1.33, 1.87, M['frame_champagne'], fw=0.05)
    art4 = MB()                                                    # the third frame (hidden by the corn plant in 14)
    im.frame_art(art4, 'X', 4.70, 5.24, 6.47, +1, 1.35, 1.84, 0, 1, fw=0.045)
    art4.build("Great_ArtPrintA", [M['frame_champagne'], M['art_venice']])
    # the medallion piece on the dining room's east wall over a glass-top console with vases (08)
    ptx.uv_quad_mesh("Dining_ArtMedallion", ptx.rect_corners('Y', 7.14, 7.62, im.DIN_EX - 0.03, 1.08, 1.68, -1), photo_tex('medallion_08'),
                     coll='House', thickness=0.025, edge_mat=M['frame_slate'])
    cw_, cg_ = MB(), MB()
    cx0, cx1, cy0, cy1, ch_ = im.DIN_EX - 0.36, im.DIN_EX - 0.02, 7.02, 7.98, 0.70
    for (lx, ly) in ((cx0 + 0.03, cy0 + 0.03), (cx1 - 0.03, cy0 + 0.03), (cx0 + 0.03, cy1 - 0.03), (cx1 - 0.03, cy1 - 0.03)):
        cw_.box(lx - 0.02, lx + 0.02, ly - 0.02, ly + 0.02, 0.0, ch_ - 0.03)
    cw_.box(cx0, cx1, cy0, cy1, ch_ - 0.06, ch_ - 0.02)
    cw_.box(cx0 + 0.02, cx1 - 0.02, cy0 + 0.02, cy1 - 0.02, 0.14, 0.16)
    cg_.box(cx0 - 0.01, cx1 + 0.005, cy0 - 0.01, cy1 + 0.01, ch_ - 0.02, ch_)
    cw_.build("Dining_Console", [M['espresso']])
    cg_.build("Dining_ConsoleGlass", [M['glass_clear']])
    vv = MB()
    vv.lathe((cx0 + cx1) / 2, 7.72, ch_, [(0.0, 0.0), (0.05, 0.0), (0.045, 0.10), (0.03, 0.20), (0.012, 0.26), (0.0, 0.27)], seg=16)
    vv.build("Dining_ConsoleVase", [M['ceramic_floral']], smooth=True)
    vv2 = MB()
    vv2.lathe((cx0 + cx1) / 2, 7.42, ch_, [(0.0, 0.0), (0.035, 0.0), (0.045, 0.08), (0.03, 0.2), (0.02, 0.22), (0.0, 0.22)], seg=16)
    vv2.build("Dining_ConsoleVase2", [M['pewter']], smooth=True)
    # ---------- ceiling: brass hugger fan with 4 tulip lights, two eyeball cans near the chase, a return grille
    fan(M, "Great_Fan", G['fan'][0], G['fan'][1])
    rg = MB()
    fu.register(rg, G['register'][0], G['register'][1], ZC, w=0.30, d=0.12, along='X', mi=0, mi_dark=1)
    rg.build("Great_Register", [M['register_white'], M['duct_dark']])
    im.recessed(M, "Great_Cans", G['cans'], energy=6)
    # ---------- the swing (jhula), the carved chairs + bench under the window, plants
    jh, jb, jc = MB(), MB(), MB()
    fu.jhula(jh, jb, jc, G['swing'][0], G['swing'][1], 0.0, w=1.82, h=1.80, mi=0, mi_chain=1, mi_cush=0, mi_bolster=0)   # 08: finials z ~1.7-1.8
    jh.build("Great_Swing", [M['carved'], M['brass']], smooth=False)
    jb.build("Great_SwingBench", [M['carved'], M['brass']])
    jc.build("Great_SwingCushion", [M['jhula_cushion']], smooth=True)
    jp = MB()
    bx, by = G['swing']
    jp.pillow_sq(bx - 0.42, by + 0.12, 0.74, 0.34, 0.34, 0.12, 0, rot=0.1, pitch=1.2, seed=31)
    jp.pillow_sq(bx + 0.42, by + 0.12, 0.74, 0.34, 0.34, 0.12, 0, rot=-0.1, pitch=1.2, seed=32)
    jp.build("Great_SwingPillows", [M['jhula_cushion']], smooth=True)
    ch, rs = MB(), MB()
    for key in ('chair1', 'chair2'):
        x, y, r = G[key]
        fu.carved_chair(ch, rs, x, y, r, seat_z=0.40, back_z=0.86)
    bxx, byy = G['bench']
    fu.carved_bench(ch, bxx, byy, 0.0, w=1.0, d=0.36, h=0.40)
    ch.build("Great_CarvedChairs", [M['carved_black']])
    rs.build("Great_ChairRush", [M['rush']], smooth=True)
    cp = MB()
    x1, y1_, r1 = G['chair1']
    x2, y2_, r2 = G['chair2']
    cp.pillow_sq(x1, y1_ + 0.12, 0.66, 0.42, 0.42, 0.13, 0, rot=r1, pitch=1.2, seed=21)
    cp.pillow_sq(x2, y2_ + 0.12, 0.66, 0.40, 0.40, 0.13, 1, rot=r2, pitch=1.2, seed=22)
    cp.build("Great_ChairPillows", [M['pillow_yellow'], M['pillow_turq']], smooth=True)
    plant("Plant_WindowBench", (bxx, byy, 0.40), 'lily', 0.50, pot='black', pot_r=0.13, pot_h=0.14, seed=23)
    plant("Plant_SwingDracaena", (bx + 0.40, 11.22, 0.0), 'lily', 1.05, pot='white', pot_r=0.17, pot_h=0.28, seed=24)   # 08: behind the bench
    plant("Plant_CornGreat", (5.55, 6.95, 0.0), 'corn', 1.95, pot='black', pot_r=0.22, pot_h=0.34, seed=25)
    # ---------- window treatment: 2" white blinds lowered (slats open) + white voile grommet panels tied back
    window_dressing(M)


def fan(M, name, x, y):
    b, bl, g = MB(), MB(), MB()
    lamps = fu.hugger_fan(b, bl, g, x, y, ZC, blade_r=0.66, n_blades=5, lights=4, rot=0.35)
    b.build(f"{name}_Body", [M['brass_satin']], smooth=True)
    bl.build(f"{name}_Blades", [M['fan_blade_maple']])
    g.build(f"{name}_Glass", [M['tulip']], smooth=True)
    for k, p in enumerate(lamps):
        add_light(f"L_{name}_{k}", 'POINT', p, 4.0, color=WARM, size=0.035, coll=LC)


def window_dressing(M):
    gw = _op('great_win')
    yw = YB1 - EWT                     # the wall's room face (11.65)
    bl = MB()
    units = gw.get('units', 1)
    fw, mull = 0.05, 0.06
    uw = (gw['a1'] - gw['a0'] - 2 * fw - (units - 1) * mull) / units
    for u in range(units):
        a0 = gw['a0'] + fw + u * (uw + mull) - 0.01
        fu.h_blinds(bl, 'X', a0, a0 + uw + 0.02, yw + 0.004, -1, 1.30, gw['z1'] - 0.02, tilt=-0.25, mi=0)   # 08: raised to ~1.3 m
    kw = _op('kitchen_win')
    fu.h_blinds(bl, 'X', kw['a0'] + 0.02, kw['a1'] - 0.02, yw + 0.004, -1, kw['z0'] + 0.04, kw['z1'] - 0.02, tilt=-0.35, mi=0)
    bl.build("Blinds_Rear", [M['blind_white']])
    # sheers: a long rod near the ceiling, two wide voile panels tied back at mid height (08, 09)
    rd, sh, gm, tie = MB(), MB(), MB(), MB()
    ra0, ra1 = gw['a0'] - 0.62, gw['a1'] + 0.52
    zr = 2.34
    fu.rod(rd, 'X', ra0, ra1, yw, -1, zr, out=0.11, r=0.011, finial=0.03)
    fu.grommet_panel(sh, gm, 'X', ra0 + 0.05, gw['a0'] + 0.52, yw, -1, zr, 0.012, out=0.11, folds=9, depth=0.09,
                     tie=(ra0 + 0.30, 1.18, 0.45), tie_mb=tie, seed=1)
    fu.grommet_panel(sh, gm, 'X', gw['a1'] - 0.50, ra1 - 0.05, yw, -1, zr, 0.012, out=0.11, folds=9, depth=0.09,
                     tie=(ra1 - 0.30, 1.18, 0.45), tie_mb=tie, seed=2)
    rd.build("Great_CurtainRod", [M['nickel_brushed']])
    gm.build("Great_Grommets", [M['nickel_brushed']])
    sh.build("Great_Sheers", [M['voile']])
    tie.build("Great_Tiebacks", [M['voile']])


# ================================================================ dining
def dining(M):
    cx, cy, w, d = D['table']
    top, wood, ch, seat = MB(), MB(), MB(), MB()
    fu.parquet_table(top, wood, cx, cy, math.pi / 2, w=w, d=d, h=0.765, mi_top=1, mi_top2=0)    # long axis along Y
    top.build("Dining_TableTop", [M['dining_wood'], M['dining_wood_y']])
    wood.build("Dining_Table", [M['dining_wood']])
    ex, wx = cx + d / 2 + 0.40, cx - d / 2 - 0.24                 # the east chairs stand pulled out (14: backs at x ~8.85)
    places = [(ex, cy - 0.40, -math.pi / 2), (ex, cy + 0.40, -math.pi / 2), (wx, cy - 0.40, math.pi / 2), (wx, cy + 0.40, math.pi / 2),
              (cx, cy + w / 2 + 0.24, 0.0), (cx, cy - w / 2 - 0.24, math.pi)]
    groups = {'East': (MB(), MB()), 'W': (ch, seat), 'North': (MB(), MB()), 'South': (MB(), MB())}
    for i, (x, y, r) in enumerate(places):
        g_ = 'East' if i < 2 else ('W' if i < 4 else ('North' if i == 4 else 'South'))
        fu.panel_back_chair(groups[g_][0], groups[g_][1], x, y, r)
    ch.build("Dining_Chairs", [M['dining_wood_z']])
    seat.build("Dining_Seats", [M['fabric_seat']], smooth=True)
    # chairs the photographer moved for photos 12 / 13 (interior_main.PHOTO_HIDE / before_render)
    groups['East'][0].build("Dining_ChairsEast", [M['dining_wood_z']])
    groups['East'][1].build("Dining_SeatsEast", [M['fabric_seat']], smooth=True)
    groups['North'][0].build("Dining_ChairNorth", [M['dining_wood_z']])
    groups['North'][1].build("Dining_SeatNorth", [M['fabric_seat']], smooth=True)
    groups['South'][0].build("Dining_ChairSouth", [M['dining_wood_z']])
    groups['South'][1].build("Dining_SeatSouth", [M['fabric_seat']], smooth=True)
    # brushed-nickel five-arm chandelier with clear ribbed bells facing down (11, 14)
    body, gl = MB(), MB()
    lamps = fu.bell_chandelier(body, gl, D['chand'][0], D['chand'][1], ZC, drop=D['chand_drop'], r=0.30, arms=5)
    body.build("Dining_Chandelier", [M['nickel_brushed']], smooth=True)
    gl.build("Dining_ChandelierGlass", [M['glass_ribbed']], smooth=True)
    bulbs = MB()
    for k, p in enumerate(lamps):
        add_light(f"L_Chandelier_{k}", 'POINT', p, 4.0, color=WARM, size=0.03, coll=LC)
        bulbs.sphere((p[0], p[1], p[2] + 0.01), 0.028, seg=12, rings=8)
    bulbs.build("Dining_ChandelierBulbs", [M['bulb_glow']], smooth=True)
    # the round wooden wall clock with Roman numerals right of the slider (11)
    yw = YB1 - EWT
    ckx, ckz, ckr = D['clock']
    cl = MB()
    fu.wall_clock(cl, ckx, yw, ckz, r=ckr, along='X', face=-1, mi_rim=0, mi_face=1, mi_ink=2)
    cl.build("Dining_Clock", [M['mahogany'], M['clock_face'], M['ink']])
    # slider: white cornice valance box + vertical blinds stacked to the east (11)
    sl = _op('slider')
    vb, cn = MB(), MB()
    fu.cornice(cn, 'X', sl['a0'] - 0.19, sl['a1'] + 0.13, yw, -1, 2.13, 2.27, depth=0.13)   # 11: x 6.25 .. 8.34, face ~0.14
    fu.v_blinds(vb, 'X', sl['a0'] - 0.06, sl['a1'] + 0.08, yw, -1, 0.03, 2.20, stack_at='a1', stack_w=0.36, n=34, mi=0)
    cn.build("Dining_Valance", [M['trim_int']])
    vb.build("Dining_VerticalBlinds", [M['vertical_blind']])
    # ceiling supply register near the slider, a light switch left of it, an outlet right of it (11)
    rg = MB()
    fu.register(rg, D['register'][0], D['register'][1], ZC, w=0.36, d=0.14, along='X', mi=0, mi_dark=1)
    rg.build("Dining_Register", [M['register_white'], M['duct_dark']])
    sw = MB()
    Face('X', yw, -1).box(sw, sl['a0'] - 0.36, sl['a0'] - 0.29, 0.007, 0.013, 1.16, 1.28, 0)
    Face('X', yw, -1).box(sw, sl['a1'] + 0.20, sl['a1'] + 0.27, 0.007, 0.013, 0.28, 0.40, 0)
    sw.build("Dining_Plates", [M['outlet']])
    # carved jali panel on the rear wall between the swing and the slider (08, 11)
    ja0, ja1, jz0, jz1 = D['jali']
    jl = MB()
    f = Face('X', yw, -1)
    f.box(jl, ja0, ja1, 0.007, 0.027, jz0, jz0 + 0.05, 0); f.box(jl, ja0, ja1, 0.007, 0.027, jz1 - 0.05, jz1, 0)
    f.box(jl, ja0, ja0 + 0.05, 0.007, 0.027, jz0 + 0.05, jz1 - 0.05, 0); f.box(jl, ja1 - 0.05, ja1, 0.007, 0.027, jz0 + 0.05, jz1 - 0.05, 0)
    nx_, nz_ = 6, 9
    for i in range(nx_ + 1):
        u = ja0 + 0.05 + (ja1 - ja0 - 0.10) * i / nx_
        f.box(jl, u - 0.008, u + 0.008, 0.007, 0.023, jz0 + 0.05, jz1 - 0.05, 0)
    for k in range(nz_ + 1):
        z = jz0 + 0.05 + (jz1 - jz0 - 0.10) * k / nz_
        f.box(jl, ja0 + 0.05, ja1 - 0.05, 0.007, 0.021, z - 0.007, z + 0.007, 0)
    jl.build("Dining_JaliPanel", [M['carved']])
    # corn plant in a blue-and-white planter on a stand left of the slider (14)
    st = MB()
    st.cylinder(sl['a0'] - 0.42, yw - 0.40, 0.0, 0.10, 0.20, seg=8)
    st.build("Plant_SliderStand", [M['espresso']])
    plant("Plant_CornSlider", (sl['a0'] - 0.42, yw - 0.40, 0.10), 'corn', 1.55, pot='white', pot_r=0.19, pot_h=0.30, seed=26,
          pot_mat=M['porcelain_blue'])


def _globe_mat(M):
    if 'globe' not in M:
        from archviz import materials as _m
        M['globe'] = _m.noise_mat("DeskGlobe", (0.10, 0.25, 0.45, 1), (0.55, 0.50, 0.30, 1), scale=5, bump=0.1, rough=0.3)
    return M['globe']


def _m_blue(M):
    if 'bowl_blue' not in M:
        from archviz import materials as _m
        M['bowl_blue'] = _m.new_mat("BowlCobalt", (0.08, 0.14, 0.40, 1), rough=0.2, coat=0.6)
    return M['bowl_blue']


# ================================================================ lights
def lights(M):
    """Daylight through the rear windows (area panels just inside each opening, aimed into the room) plus a soft
    ceiling fill per room.  Calibrated on photo 09 patch means (wall 194 vs 186, ceiling 193 vs 198); upward 'bounce'
    panels were tried and over-lit the ceiling (246) without changing the seat / wall ratio."""
    yw = YB1 - EWT
    for (name, key, e) in (("Great", 'great_win', 320.0), ("Slider", 'slider', 380.0), ("Sink", 'kitchen_win', 60.0)):
        o = _op(key)
        a0, a1, z0, z1 = o['a0'], o['a1'], o['z0'], o['z1']
        area_light(f"L_Day_{name}", ((a0 + a1) / 2, yw - 0.10, (z0 + z1) / 2), (a1 - a0, z1 - z0), e, color=DAY,
                   target=((a0 + a1) / 2, yw - 3.0, (z0 + z1) / 2 - 0.9), coll=LC, spread=math.radians(150))   # spares the ceiling a little
    rooms = (("Great", (XB0 + EWT + 0.15, GAR[1] - 0.15, 6.6, YB1 - EWT - 0.15), 60),
             ("Dining", (GAR[1] + 0.05, im.DIN_EX - 0.05, 6.6, YB1 - EWT - 0.15), 80),
             ("Kitchen", (im.PIER['x1'] + 0.05, XR - 0.05, im.FRIDGE_Y + 0.1, YB1 - EWT - 0.05), 25))
    for (name, rect, e) in rooms:
        x0, x1, y0, y1 = rect
        area_light(f"L_Fill_{name}", ((x0 + x1) / 2, (y0 + y1) / 2, ZC - 0.06), ((x1 - x0) * 0.85, (y1 - y0) * 0.85), e,
                   color=(1.0, 0.97, 0.93), coll=LC)
