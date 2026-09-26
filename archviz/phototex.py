"""Textures rectified from reference photographs (bpy + NumPy, no PIL).

A flat, photographed object - a painting, a framed print, a rug seen from above, a shower curtain - is reproduced most
faithfully by its own pixels.  `rectify()` maps a quadrilateral of a reference photo (four pixel corners, clockwise from
the top-left) onto an axis-aligned image through a homography with bilinear sampling, so a painting hung on a wall and
photographed at an angle becomes a front-on texture.  `flatten` divides out the photo's low-frequency lighting (for
fabrics with folds or a light fall-off), `gain` scales the linear albedo so that the re-lit render reads like the photo.

The result is an in-memory (packable) image; nothing is written next to the photos.  `photo_material()` wraps it in a
Principled material on the object's UV map.  Record the photo and quad of every texture in the house's references.
"""
import math

import numpy as np

try:
    import bpy
except ImportError:          # pragma: no cover - bpy-free import for tests/tools
    bpy = None

_CACHE = {}


def _photo_array(path):
    """(H, W, 3) float array of the photo in sRGB-encoded 0..1, row 0 = top."""
    key = str(path)
    if key not in _CACHE:
        img = bpy.data.images.load(key, check_existing=True)
        img.reload()
        _ = img.pixels[0]                  # force the pixel buffer to load
        w, h = img.size
        px = np.empty(w * h * 4, np.float32)
        img.pixels.foreach_get(px)
        _CACHE[key] = px.reshape(h, w, 4)[::-1, :, :3].copy()
    return _CACHE[key]


def homography(src, dst):
    """3x3 H with dst ~ H @ src for four point pairs (DLT)."""
    A = []
    for (x, y), (u, v) in zip(src, dst):
        A.append([-x, -y, -1, 0, 0, 0, u * x, u * y, u])
        A.append([0, 0, 0, -x, -y, -1, v * x, v * y, v])
    _, _, vt = np.linalg.svd(np.asarray(A, float))
    H = vt[-1].reshape(3, 3)
    return H / H[2, 2]


def _bilinear(arr, u, v):
    h, w = arr.shape[:2]
    u = np.clip(u, 0, w - 1.001); v = np.clip(v, 0, h - 1.001)
    u0 = np.floor(u).astype(int); v0 = np.floor(v).astype(int)
    fu = (u - u0)[..., None]; fv = (v - v0)[..., None]
    a = arr[v0, u0]; b = arr[v0, u0 + 1]; c = arr[v0 + 1, u0]; d = arr[v0 + 1, u0 + 1]
    return (a * (1 - fu) + b * fu) * (1 - fv) + (c * (1 - fu) + d * fu) * fv


def _box_blur(a, r):
    """Separable box blur of an (h, w, 3) array with radius r pixels (edge-clamped)."""
    if r < 1:
        return a
    out = a
    for axis in (0, 1):
        pad = [(0, 0)] * 3
        pad[axis] = (r, r)
        p = np.pad(out, pad, mode='edge')
        c = np.cumsum(p, axis=axis, dtype=np.float64)
        c = np.concatenate([np.zeros_like(np.take(c, [0], axis=axis)), c], axis=axis)
        n = out.shape[axis]
        hi = np.take(c, np.arange(2 * r + 1, 2 * r + 1 + n), axis=axis)
        lo = np.take(c, np.arange(0, n), axis=axis)
        out = ((hi - lo) / (2 * r + 1)).astype(np.float32)
    return out


def _to_lin(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def _to_srgb(c):
    c = np.clip(c, 0.0, 1.0)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def rectify_array(arr, quad, size, flatten=0.0, gain=1.0, saturation=1.0, tile=False):
    """NumPy core of `rectify` (arr: (H, W, 3) sRGB 0..1, row 0 = top) -> (h, w, 3) sRGB array, row 0 = top."""
    w, h = size
    H = homography([(0, 0), (1, 0), (1, 1), (0, 1)], quad)
    gx, gy = np.meshgrid((np.arange(w) + 0.5) / w, (np.arange(h) + 0.5) / h)
    P = H @ np.stack([gx.ravel(), gy.ravel(), np.ones(gx.size)])
    u = (P[0] / P[2]).reshape(h, w); v = (P[1] / P[2]).reshape(h, w)
    out = _bilinear(arr, u, v).astype(np.float32)
    lin = _to_lin(out)
    if flatten > 0:
        r = max(1, int(round(flatten * max(w, h))))
        low = _box_blur(lin, r)
        lin = lin / np.maximum(low, 1e-3) * lin.reshape(-1, 3).mean(0)
    if saturation != 1.0:
        grey = lin.mean(axis=2, keepdims=True)
        lin = grey + (lin - grey) * saturation
    lin = lin * gain
    if tile:                              # cross-fade the borders so the texture repeats without seams
        k = max(2, int(0.08 * min(w, h)))
        ramp = np.linspace(0, 1, k)[None, :, None]
        lin[:, :k] = lin[:, :k] * ramp + lin[:, -k:][:, ::-1] * (1 - ramp)
        ramp = np.linspace(0, 1, k)[:, None, None]
        lin[:k] = lin[:k] * ramp + lin[-k:][::-1] * (1 - ramp)
    return _to_srgb(lin)


def rectify(photo, quad, size, name, flatten=0.0, gain=1.0, saturation=1.0, tile=False):
    """New bpy image `name` (w x h = size) from the photo quadrilateral `quad` = [(u, v) TL, TR, BR, BL] in photo pixels."""
    if name in bpy.data.images:
        return bpy.data.images[name]
    rgb = rectify_array(_photo_array(photo), quad, size, flatten, gain, saturation, tile)
    w, h = size
    img = bpy.data.images.new(name, w, h, alpha=False)      # byte image, sRGB by default (setting the colour space
    px = np.ones((h, w, 4), np.float32)                      # after the pixels would regenerate the buffer)
    px[..., :3] = rgb[::-1]
    img.pixels.foreach_set(px.ravel())
    img.update()
    try:
        img.pack()
    except RuntimeError:
        pass
    return img


def photo_material(name, img, rough=0.6, coat=0.0, sheen=0.0, bump=0.0, repeat=(1.0, 1.0), src='UV', spec=0.4, plane='XY'):
    """Principled material showing `img` on the UV map (src='UV') or tiled on object coordinates (src='Object') in
    `plane` ('XY', 'XZ', 'YZ'), `repeat` tiles per metre."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs['Scale'].default_value = (repeat[0], repeat[1], 1.0)
    if src == 'UV' or plane == 'XY':
        nt.links.new(tc.outputs['UV' if src == 'UV' else 'Object'], mp.inputs['Vector'])
    else:
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(tc.outputs['Object'], sep.inputs['Vector'])
        comb = nt.nodes.new("ShaderNodeCombineXYZ")
        a, c = {'XZ': ('X', 'Z'), 'YZ': ('Y', 'Z')}[plane]
        nt.links.new(sep.outputs[a], comb.inputs['X'])
        nt.links.new(sep.outputs[c], comb.inputs['Y'])
        nt.links.new(comb.outputs['Vector'], mp.inputs['Vector'])
    tx = nt.nodes.new("ShaderNodeTexImage")
    tx.image = img
    tx.extension = 'REPEAT' if repeat != (1.0, 1.0) or src != 'UV' else 'EXTEND'
    nt.links.new(mp.outputs['Vector'], tx.inputs['Vector'])
    nt.links.new(tx.outputs['Color'], b.inputs['Base Color'])
    for k, val in (("Roughness", rough), ("Coat Weight", coat), ("Sheen Weight", sheen), ("Specular IOR Level", spec)):
        s = b.inputs.get(k)
        if s is not None:
            s.default_value = val
    if bump > 0:
        bw = nt.nodes.new("ShaderNodeRGBToBW")
        nt.links.new(tx.outputs['Color'], bw.inputs['Color'])
        bn = nt.nodes.new("ShaderNodeBump")
        bn.inputs['Strength'].default_value = bump
        bn.inputs['Distance'].default_value = 0.002
        nt.links.new(bw.outputs['Val'], bn.inputs['Height'])
        nt.links.new(bn.outputs['Normal'], b.inputs['Normal'])
    return m


def uv_quad_mesh(name, corners, mat, coll=None, thickness=0.0, mi_edge=None, edge_mat=None):
    """A textured planar quad (corners in world space, TL, TR, BR, BL as seen from the front) with UVs 0..1; with
    `thickness` > 0 it becomes a canvas slab pushed back along the quad's normal (sides use `edge_mat` or `mat`)."""
    import bmesh
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    tl, tr, br, bl = corners
    V = [bm.verts.new(c) for c in (tl, bl, br, tr)]      # counter-clockwise seen from the front -> normal to the viewer
    f = bm.faces.new(V)
    for loop, uv in zip(f.loops, ((0, 1), (0, 0), (1, 0), (1, 1))):
        loop[uvl].uv = uv
    f.material_index = 0
    f.normal_update()
    if thickness > 0:
        n = f.normal.copy()
        B = [bm.verts.new(v.co - n * thickness) for v in V]
        back = bm.faces.new(list(reversed(B)))
        back.material_index = 1 if edge_mat else 0
        for i in range(4):
            j = (i + 1) % 4
            s = bm.faces.new([V[j], V[i], B[i], B[j]])
            s.material_index = 1 if edge_mat else 0
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    if edge_mat:
        me.materials.append(edge_mat)
    ob = bpy.data.objects.new(name, me)
    (bpy.data.collections.get(coll) if coll else bpy.context.scene.collection).objects.link(ob)
    return ob


def rect_corners(along, a0, a1, b, z0, z1, face):
    """World corners TL, TR, BR, BL of a rectangle on a wall plane (along 'X' at y = b, or 'Y' at x = b) seen from the
    side the wall faces (`face` = +1: toward +y / +x)."""
    if along == 'X':
        l, r = (a1, a0) if face > 0 else (a0, a1)      # seen from +y, +x is on the viewer's left
        return [(l, b, z1), (r, b, z1), (r, b, z0), (l, b, z0)]
    l, r = (a0, a1) if face > 0 else (a1, a0)          # seen from +x, +y is on the viewer's right
    return [(b, l, z1), (b, r, z1), (b, r, z0), (b, l, z0)]


def mean_luma(img_or_arr):
    a = img_or_arr
    return float(np.asarray(a).reshape(-1, 3).mean())


__all__ = ['rectify', 'rectify_array', 'photo_material', 'uv_quad_mesh', 'rect_corners', 'homography', 'math']
