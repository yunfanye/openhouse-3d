"""Low-poly suburban houses for the context around the pond and the subdivision (imported by context.py and
sitefar_suburb.py only).  One call adds a two-storey house into a Kit: merged meshes per material, so a whole row of
houses is a handful of objects.  Everything is built in the house's own frame (front = local -Y) and placed with
(cx, cy, heading).  Detail is "seen from 60-300 m": walls with a lap-line shader instead of siding geometry, roof
planes with a fascia, window / door quads over white casings, a garage bump with its door, rear decks, patios and
fences.  Materials: SF_* (created once, optionally hazed by camera distance)."""
import math
import random
from archviz.mesh import MB
from archviz import materials as _m

_MATS = {}

# siding / roof palettes seen in photos 26 and 30-32 (linear albedo; photo sRGB means in the notes)
SIDING = {
    # albedo, calibrated on 32's far row (render vs photo sRGB of the sunlit rear walls; the renders read cooler, so
    # these are warmer than the photo's hue): white 237/224/208, cream 220/209/197, beige 216/202/178, greige
    # 172/163/150, khaki 178/174/144, grey-blue 172/173/174
    'white': (0.66, 0.60, 0.50), 'cream': (0.64, 0.56, 0.44), 'beige': (0.58, 0.48, 0.34), 'tan': (0.47, 0.36, 0.24),
    'lightgrey': (0.47, 0.45, 0.41), 'grey': (0.31, 0.31, 0.30), 'greyblue': (0.30, 0.32, 0.34), 'blue': (0.08, 0.15, 0.30),
    'sage': (0.28, 0.30, 0.21), 'mocha': (0.28, 0.21, 0.15), 'yellow': (0.56, 0.47, 0.25), 'greige': (0.44, 0.39, 0.32),
    'khaki': (0.45, 0.42, 0.29),
}
ROOF = {'weathered': (0.31, 0.215, 0.14), 'charcoal': (0.085, 0.08, 0.07), 'brown': (0.27, 0.165, 0.10), 'grey': (0.21, 0.185, 0.15)}
# (32: sunlit roofs sRGB 165-185 / 142-147 / 112-120, i.e. warm weathered-wood blends)


def mats(haze=None):
    """SF_* materials (one set per haze setting)."""
    key = 'h' if haze else 'n'
    if key in _MATS:
        return _MATS[key]
    from archviz import trees as _tr
    d = {}
    for k, c in SIDING.items():
        m = _m.new_mat(f"SF_Siding_{k}_{key}", (*c, 1), rough=0.6, spec=0.3)
        nt, b = m.node_tree, _m._bsdf(m)
        wave = nt.nodes.new("ShaderNodeTexWave"); wave.wave_type = 'BANDS'; wave.bands_direction = 'Z'
        wave.wave_profile = 'SAW'; wave.inputs["Scale"].default_value = 1.65          # ~0.19 m lap courses
        nt.links.new(wave.inputs["Vector"], _m._coords(nt))
        _m._bump(nt, b, wave.outputs["Fac"], 0.25, 0.01)
        d['siding_' + k] = m
    for k, c in ROOF.items():
        d['roof_' + k] = _m.noise_mat(f"SF_Roof_{k}_{key}", (*[v * 0.8 for v in c], 1), (*[min(1, v * 1.2) for v in c], 1), scale=6.0,
                                      bump=0.3, rough=0.9, detail=6, spec=0.12)
    d['trim'] = _m.new_mat(f"SF_Trim_{key}", (0.78, 0.78, 0.76, 1), rough=0.45)
    d['glass'] = _m.new_mat(f"SF_Glass_{key}", (0.035, 0.04, 0.048, 1), rough=0.08, spec=0.7, coat=0.4)
    d['door_white'] = _m.new_mat(f"SF_GarageDoor_{key}", (0.74, 0.74, 0.72, 1), rough=0.4)
    d['door_dark'] = _m.new_mat(f"SF_DoorDark_{key}", (0.05, 0.05, 0.06, 1), rough=0.4)
    d['shutter'] = _m.new_mat(f"SF_Shutter_{key}", (0.035, 0.04, 0.05, 1), rough=0.5)
    d['brick'] = _m.noise_mat(f"SF_Brick_{key}", (0.20, 0.07, 0.045, 1), (0.30, 0.12, 0.08, 1), scale=30, bump=0.3, rough=0.85)
    d['stone'] = _m.noise_mat(f"SF_Stone_{key}", (0.36, 0.32, 0.27, 1), (0.52, 0.47, 0.40, 1), scale=12, bump=0.4, rough=0.85)
    d['deck'] = _m.noise_mat(f"SF_Deck_{key}", (0.22, 0.13, 0.08, 1), (0.34, 0.21, 0.13, 1), scale=8, bump=0.1, rough=0.7)
    d['deck_red'] = _m.noise_mat(f"SF_DeckRed_{key}", (0.28, 0.07, 0.05, 1), (0.38, 0.12, 0.08, 1), scale=8, bump=0.1, rough=0.7)
    d['patio'] = _m.noise_mat(f"SF_Patio_{key}", (0.40, 0.37, 0.33, 1), (0.52, 0.49, 0.45, 1), scale=5, bump=0.1, rough=0.85)
    d['concrete'] = _m.noise_mat(f"SF_Concrete_{key}", (0.46, 0.45, 0.42, 1), (0.56, 0.55, 0.52, 1), scale=4, bump=0.05, rough=0.85)
    d['fence'] = _m.new_mat(f"SF_FenceBlack_{key}", (0.02, 0.02, 0.022, 1), rough=0.5, metal=0.3)
    d['fence_wood'] = _m.noise_mat(f"SF_FenceWood_{key}", (0.30, 0.22, 0.15, 1), (0.42, 0.32, 0.22, 1), scale=10, bump=0.1, rough=0.8)
    if haze:
        for m in d.values():
            _tr.add_haze(m, haze['color'], dist=haze['dist'], strength=haze['strength'], max_fac=haze['max_fac'])
    _MATS[key] = d
    return d


class Kit:
    """Merged meshes per material key; build() writes one object per key (or one joined object)."""

    def __init__(self, M, haze=None):
        self.m = mats(haze)
        self.mb = {}

    def get(self, key):
        if key not in self.mb:
            self.mb[key] = MB()
        return self.mb[key]

    def build(self, name, coll):
        obs = []
        for key, mb in self.mb.items():
            if mb.f:
                obs.append(mb.build(f"{name}_{key}", [self.m[key]], coll=coll, recalc=False))
        return obs

    def build_joined(self, name, coll):
        """One object with one material slot per key (prototypes for instancing)."""
        keys = [k for k, mb in self.mb.items() if mb.f]
        out = MB()
        for i, k in enumerate(keys):
            mb = self.mb[k]
            base = len(out.v)
            out.v.extend(mb.v)
            out.f.extend(tuple(base + j for j in f) for f in mb.f)
            out.fm.extend([i] * len(mb.f))
        return out.build(name, [self.m[k] for k in keys], coll=coll, recalc=False)


class Frame:
    """Local house frame: (u across the front, w toward the back, z up) -> world."""

    def __init__(self, cx, cy, heading, z0):
        self.cx, self.cy, self.z0 = cx, cy, z0
        # heading = direction the FRONT faces (radians, 0 = -Y i.e. toward the viewer's street)
        self.c, self.s = math.cos(heading), math.sin(heading)

    def P(self, u, w, z):
        # local front normal is -w; rotate so that heading 0 -> front faces -Y
        x = u * self.c - w * self.s
        y = u * self.s + w * self.c
        return (self.cx + x, self.cy + y, self.z0 + z)


def _quad(mb, F, pts):
    mb._add([F.P(*p) for p in pts], [(0, 1, 2, 3)], 0)


def _box(mb, F, u0, u1, w0, w1, z0, z1):
    vs = [F.P(u0, w0, z0), F.P(u1, w0, z0), F.P(u1, w1, z0), F.P(u0, w1, z0),
          F.P(u0, w0, z1), F.P(u1, w0, z1), F.P(u1, w1, z1), F.P(u0, w1, z1)]
    mb._add(vs, [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)], 0)


def _opening(kit, F, face, a, z, ww, hh, W, D, kind='glass', casing=0.09, shutters=False):
    """A window / door on a wall face: casing quad (trim) + inset glass quad, offset outward a few mm.
    face: 'F' (w = 0 plane, a along +u), 'B' (w = D, a along -u), 'L' (u = -W/2, a along +w), 'R' (u = +W/2)."""
    def pt(t, zz, off):
        if face == 'F':
            return (t, -off, zz)
        if face == 'B':
            return (-t, D + off, zz)
        if face == 'L':
            return (-W / 2 - off, t, zz)
        return (W / 2 + off, -t, zz)
    tr, gl = kit.get('trim'), kit.get(kind)
    c = casing
    _quad(tr, F, [pt(a - ww / 2 - c, z - c, 0.02), pt(a + ww / 2 + c, z - c, 0.02), pt(a + ww / 2 + c, z + hh + c, 0.02),
                  pt(a - ww / 2 - c, z + hh + c, 0.02)])
    _quad(gl, F, [pt(a - ww / 2, z, 0.03), pt(a + ww / 2, z, 0.03), pt(a + ww / 2, z + hh, 0.03), pt(a - ww / 2, z + hh, 0.03)])
    if kind == 'glass' and hh > 0.9:
        _quad(tr, F, [pt(a - ww / 2, z + hh * 0.5 - 0.025, 0.035), pt(a + ww / 2, z + hh * 0.5 - 0.025, 0.035),
                      pt(a + ww / 2, z + hh * 0.5 + 0.025, 0.035), pt(a - ww / 2, z + hh * 0.5 + 0.025, 0.035)])
    if shutters:
        sh = kit.get('shutter')
        for s0, s1 in ((a - ww / 2 - c - 0.42, a - ww / 2 - c - 0.02), (a + ww / 2 + c + 0.02, a + ww / 2 + c + 0.42)):
            _quad(sh, F, [pt(s0, z, 0.03), pt(s1, z, 0.03), pt(s1, z + hh, 0.03), pt(s0, z + hh, 0.03)])


def _gable_roof(kit, F, u0, u1, w0, w1, zt, pitch, key, along='u', ovh=0.35, gable_mat=None):
    """Two roof planes. along='u': ridge parallel to the front (side gables); 'w': ridge front-to-back."""
    mb = kit.get(key)
    tr = kit.get('trim')
    if along == 'u':
        wm = (w0 + w1) / 2
        zr = zt + (wm - w0) * pitch
        a0, a1 = u0 - ovh, u1 + ovh
        zf = zt - ovh * pitch
        _quad(mb, F, [(a0, w0 - ovh, zf), (a1, w0 - ovh, zf), (a1, wm, zr), (a0, wm, zr)])
        _quad(mb, F, [(a1, w1 + ovh, zf), (a0, w1 + ovh, zf), (a0, wm, zr), (a1, wm, zr)])
        for (ww_, sg) in ((w0 - ovh, -1), (w1 + ovh, 1)):          # fascia boards along both eaves
            _quad(tr, F, [(a0, ww_, zf - 0.22), (a1, ww_, zf - 0.22), (a1, ww_, zf), (a0, ww_, zf)])
        if gable_mat:
            g = kit.get(gable_mat)
            for uu in (u0, u1):
                g._add([F.P(uu, w0, zt), F.P(uu, w1, zt), F.P(uu, wm, zr - 0.05)], [(0, 1, 2)], 0)
        return zr
    um = (u0 + u1) / 2
    zr = zt + (um - u0) * pitch
    b0, b1 = w0 - ovh, w1 + ovh
    zf = zt - ovh * pitch
    _quad(mb, F, [(u0 - ovh, b0, zf), (um, b0, zr), (um, b1, zr), (u0 - ovh, b1, zf)])
    _quad(mb, F, [(u1 + ovh, b1, zf), (um, b1, zr), (um, b0, zr), (u1 + ovh, b0, zf)])
    for uu in (u0 - ovh, u1 + ovh):
        _quad(tr, F, [(uu, b0, zf - 0.22), (uu, b1, zf - 0.22), (uu, b1, zf), (uu, b0, zf)])
    if gable_mat:
        g = kit.get(gable_mat)
        for ww_ in (w0, w1):
            g._add([F.P(u0, ww_, zt), F.P(u1, ww_, zt), F.P(um, ww_, zr - 0.05)], [(0, 1, 2)], 0)
    return zr


def _hip_roof(kit, F, u0, u1, w0, w1, zt, pitch, key, ovh=0.35):
    mb = kit.get(key)
    a0, a1, b0, b1 = u0 - ovh, u1 + ovh, w0 - ovh, w1 + ovh
    zf = zt - ovh * pitch
    half = (b1 - b0) / 2
    zr = zf + half * pitch
    r0, r1 = a0 + half, a1 - half
    if r1 < r0:
        r0 = r1 = (a0 + a1) / 2
    wm = (b0 + b1) / 2
    _quad(mb, F, [(a0, b0, zf), (a1, b0, zf), (r1, wm, zr), (r0, wm, zr)])
    _quad(mb, F, [(a1, b1, zf), (a0, b1, zf), (r0, wm, zr), (r1, wm, zr)])
    mb._add([F.P(a0, b1, zf), F.P(a0, b0, zf), F.P(r0, wm, zr)], [(0, 1, 2)], 0)
    mb._add([F.P(a1, b0, zf), F.P(a1, b1, zf), F.P(r1, wm, zr)], [(0, 1, 2)], 0)
    tr = kit.get('trim')
    for (p, q) in (((a0, b0), (a1, b0)), ((a1, b1), (a0, b1)), ((a0, b1), (a0, b0)), ((a1, b0), (a1, b1))):
        _quad(tr, F, [(p[0], p[1], zf - 0.22), (q[0], q[1], zf - 0.22), (q[0], q[1], zf), (p[0], p[1], zf)])
    return zr


def house(kit, cx, cy, heading, z0=0.0, W=13.0, D=10.5, H=5.6, siding='white', roof='weathered', seed=0, style=None):
    """One two-storey house.  (cx, cy) = centre of the main block's FRONT wall line; heading = direction the front
    faces (0 = -Y).  style keys: garage ('L'/'R'/None), garage_w, roof ('side'/'front'/'hip'), front_gable (bool),
    brick (front ground floor), shutters, deck (None/'wood'/'red'/'patio'), deck_w, sunroom, fence ('black'/'wood'/None),
    yard (rear yard depth for the fence), porch."""
    st = dict(garage='L', garage_w=6.6, roof='side', front_gable=True, brick=False, shutters=True, deck=None, deck_w=4.0,
              sunroom=False, fence=None, yard=14.0, porch=True, pitch=0.55)
    st.update(style or {})
    rng = random.Random(seed)
    F = Frame(cx, cy, heading, z0)
    sk = 'siding_' + siding
    rk = 'roof_' + roof
    wall = kit.get(sk)
    # main block (front wall at w = 0, rear at w = D)
    u0, u1 = -W / 2, W / 2
    _box(wall, F, u0, u1, 0.0, D, -0.3, H)
    if st['brick']:
        _box(kit.get('brick'), F, u0 - 0.02, u1 + 0.02, -0.06, 0.4, -0.3, 2.9)
    # garage bump in front (one storey)
    gw = st['garage_w']
    g = st['garage']
    if g:
        ga0, ga1 = (u0 - 0.6, u0 - 0.6 + gw) if g == 'L' else (u1 + 0.6 - gw, u1 + 0.6)
        gd = 6.4
        _box(kit.get('brick' if st['brick'] else sk), F, ga0, ga1, -gd, 0.2, -0.3, 2.9)
        _gable_roof(kit, F, ga0, ga1, -gd, 0.4, 2.95, 0.42, rk, along='w' if rng.random() < 0.45 else 'u', ovh=0.3,
                    gable_mat=sk)
        dw = 4.9 if gw > 6 else 2.6
        am = (ga0 + ga1) / 2
        _quad(kit.get('trim'), F, [(am - dw / 2 - 0.1, -gd - 0.02, 0.0), (am + dw / 2 + 0.1, -gd - 0.02, 0.0),
                                   (am + dw / 2 + 0.1, -gd - 0.02, 2.25), (am - dw / 2 - 0.1, -gd - 0.02, 2.25)])
        _quad(kit.get('door_white'), F, [(am - dw / 2, -gd - 0.04, 0.0), (am + dw / 2, -gd - 0.04, 0.0), (am + dw / 2, -gd - 0.04, 2.13),
                                         (am - dw / 2, -gd - 0.04, 2.13)])
        _quad(kit.get('concrete'), F, [(am - dw / 2 - 0.4, -gd - 7.5, -0.26), (am + dw / 2 + 0.4, -gd - 7.5, -0.26),
                                       (am + dw / 2 + 0.3, -gd, -0.26), (am - dw / 2 - 0.3, -gd, -0.26)])
        free0, free1 = (ga1 + 0.3, u1) if g == 'L' else (u0, ga0 - 0.3)
    else:
        free0, free1 = u0, u1
    # roof: main block
    zt = H + 0.25
    if st['roof'] == 'hip':
        _hip_roof(kit, F, u0, u1, 0.0, D, zt, st['pitch'], rk)
    elif st['roof'] == 'front':
        _gable_roof(kit, F, u0, u1, 0.0, D, zt, st['pitch'], rk, along='w', gable_mat=sk)
    else:
        _gable_roof(kit, F, u0, u1, 0.0, D, zt, st['pitch'], rk, along='u', gable_mat=sk)
    if st['front_gable'] and st['roof'] != 'front':
        fa0 = free0 + (free1 - free0) * rng.uniform(0.05, 0.35)
        fa1 = min(free1, fa0 + rng.uniform(3.2, 4.4))
        _box(wall, F, fa0, fa1, -0.6, 0.05, 2.9, H)
        _gable_roof(kit, F, fa0, fa1, -0.6, 2.0, zt, 0.85, rk, along='w', ovh=0.3, gable_mat=sk)
    # front openings: door + windows (upper row over the free span, lower windows)
    zu, hu = 3.55, 1.5
    n_up = max(2, int((free1 - free0) / 2.6))
    for i in range(n_up):
        a = free0 + (free1 - free0) * (i + 0.5) / n_up
        _opening(kit, F, 'F', a, zu, 0.9, hu, W, D, shutters=st['shutters'])
    door_a = free0 + 1.2 if g == 'L' else free1 - 1.2
    _opening(kit, F, 'F', door_a, 0.0, 0.95, 2.05, W, D, kind='door_dark', casing=0.12)
    for a in (door_a + (2.2 if g == 'L' else -2.2),):
        if free0 + 0.8 < a < free1 - 0.8:
            _opening(kit, F, 'F', a, 0.65, 1.6, 1.45, W, D, shutters=st['shutters'])
    if st['porch']:
        _box(kit.get('concrete'), F, door_a - 1.2, door_a + 1.2, -1.6, 0.0, -0.3, -0.12)
    # rear: slider + windows on both floors
    rear_up = max(2, int(W / 3.6))
    for i in range(rear_up):
        a = u0 + W * (i + 0.5) / rear_up
        _opening(kit, F, 'B', -a, zu, 0.9 if i != rear_up - 1 else 1.4, hu, W, D)
    sl_a = u0 + W * (st['slider_f'] if st.get('slider_f') is not None else rng.uniform(0.35, 0.6))
    _opening(kit, F, 'B', -sl_a, 0.0, 1.8, 2.05, W, D)
    _opening(kit, F, 'B', -(sl_a + 3.0 if sl_a + 3.6 < u1 else sl_a - 3.0), 0.8, 1.5, 1.35, W, D)
    # sides: one window per floor
    for face in ('L', 'R'):
        _opening(kit, F, face, D * 0.55, zu, 0.9, 1.4, W, D)
        _opening(kit, F, face, D * 0.3, 0.9, 0.9, 1.3, W, D)
    # rear additions
    if st['sunroom']:
        s0, s1 = sl_a - 2.5, sl_a + 2.5
        _box(kit.get('glass'), F, s0, s1, D, D + 3.6, 0.2, 2.6)
        _box(kit.get('trim'), F, s0 - 0.05, s1 + 0.05, D, D + 3.65, 2.6, 2.75)
        _gable_roof(kit, F, s0, s1, D, D + 3.6, 2.75, 0.45, rk, along='w', ovh=0.2)
    dk = st['deck']
    if dk in ('wood', 'red'):
        dw_ = st['deck_w']
        d0, d1 = sl_a - dw_ / 2, sl_a + dw_ / 2
        mk = kit.get('deck' if dk == 'wood' else 'deck_red')
        _box(mk, F, d0, d1, D, D + 3.6, 0.35, 0.5)
        for (pa, pb) in ((d0, d1),):
            _box(mk, F, pa, pb, D + 3.55, D + 3.6, 0.5, 1.4)                      # rail + balusters read as one panel
            _box(mk, F, pa, pa + 0.05, D, D + 3.6, 0.5, 1.4)
            _box(mk, F, pb - 0.05, pb, D, D + 3.6, 0.5, 1.4)
        for k in range(3):                                                      # stairs
            _box(mk, F, d1 - 1.2, d1, D + 3.6 + k * 0.28, D + 3.6 + (k + 1) * 0.28, -0.3, 0.35 - k * 0.14)
    elif dk == 'patio':
        _box(kit.get('patio'), F, sl_a - 2.5, sl_a + 2.5, D, D + 4.0, -0.3, -0.24)
    fz = st['fence']
    if fz:
        fk = kit.get('fence' if fz == 'black' else 'fence_wood')
        y1 = D + st['yard']
        hgt = 1.25 if fz == 'black' else 1.8
        pts = [(u0 - 0.5, D - 1.0), (u0 - 0.5, y1), (u1 + 0.5, y1), (u1 + 0.5, D - 1.0)]
        for (p, q) in zip(pts[:-1], pts[1:]):
            L = math.hypot(q[0] - p[0], q[1] - p[1])
            n = max(1, int(L / 1.9))
            for k in range(n + 1):
                t = k / n
                pu, pw = p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t
                _box(fk, F, pu - 0.04, pu + 0.04, pw - 0.04, pw + 0.04, -0.3, hgt)
            for zz in ((hgt - 0.1, hgt - 0.05), (0.08, 0.13)) if fz == 'black' else ((0.05, hgt),):
                if fz == 'black':
                    _box(fk, F, min(p[0], q[0]) - 0.02, max(p[0], q[0]) + 0.02, min(p[1], q[1]) - 0.02, max(p[1], q[1]) + 0.02, *zz)
                else:
                    _box(fk, F, min(p[0], q[0]) - 0.02, max(p[0], q[0]) + 0.02, min(p[1], q[1]) - 0.02, max(p[1], q[1]) + 0.02, -0.3, hgt)
            if fz == 'black':                                                   # pickets: a sparse comb
                m = max(2, int(L / 0.35))
                for k in range(m):
                    t = (k + 0.5) / m
                    pu, pw = p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t
                    _box(fk, F, pu - 0.012, pu + 0.012, pw - 0.012, pw + 0.012, 0.05, hgt - 0.05)
    return F
