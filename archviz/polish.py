"""Realism stage run after all geometry modules: hair-particle grass on lawns / turf (house.py GRASS specs), opt-in
particle-instanced leaf cards (any mesh with a "leaf_cards" custom property - hedges, green walls), camera depth of
field, compositor bloom.  Called from run.py; `--no-polish` skips it for fast previews."""
import math, random
import bpy
from mathutils import Vector
from .mesh import *
from . import materials as _mat


# ------------------------------------------------------------------ grass
def _emitter(name, x0, x1, y0, y1, z, holes=(), cell=1.0, padding=0.3):
    """Flat quad grid just above a lawn (holes = (hx0,hx1,hy0,hy1) rectangles to skip)."""
    mb = MB()
    nx, ny = max(1, int((x1 - x0) / cell)), max(1, int((y1 - y0) / cell))
    for i in range(nx):
        for j in range(ny):
            ax, bx = x0 + (x1 - x0) * i / nx, x0 + (x1 - x0) * (i + 1) / nx
            ay, by = y0 + (y1 - y0) * j / ny, y0 + (y1 - y0) * (j + 1) / ny
            cx, cy = (ax + bx) / 2, (ay + by) / 2
            if any(hx0 - padding < cx < hx1 + padding and hy0 - padding < cy < hy1 + padding for (hx0, hx1, hy0, hy1) in holes):
                continue
            mb.quad((ax, ay, z), (bx, ay, z), (bx, by, z), (ax, by, z))
    return mb.build(name, [], coll='Polish', recalc=False)


def _hair(ob, mat, count, length=0.045, children=10, radius=0.0035, clump=0.15, kink=0.08, seed=1, length_var=0.45):
    ob.data.materials.append(mat)
    mod = ob.modifiers.new("grass", 'PARTICLE_SYSTEM')
    ps = mod.particle_system
    ps.seed = seed
    st = ps.settings
    st.type = 'HAIR'
    st.count = count
    st.hair_length = length
    st.hair_step = 3
    st.emit_from = 'FACE'
    st.distribution = 'RAND'
    st.use_emit_random = True
    st.use_advanced_hair = True
    st.use_rotations = True
    st.rotation_factor_random = 0.35
    st.phase_factor_random = 2.0
    st.child_type = 'INTERPOLATED'
    st.rendered_child_count = children
    st.child_length = 1.0 - length_var * 0.5
    st.child_length_threshold = length_var
    st.clump_factor = clump
    st.roughness_1 = kink
    st.roughness_1_size = 0.6
    st.roughness_endpoint = 0.02
    st.radius_scale = radius
    st.root_radius = 1.0
    st.tip_radius = 0.0
    st.shape = -0.3
    st.material = len(ob.data.materials)
    ob.show_instancer_for_render = False
    return st


def add_grass(M, specs=()):
    """Hair grass from a list of specs (house.py GRASS).  Two forms:

        dict(name="Grass_FrontLawn", rect=(x0, x1, y0, y1), z=0.904, holes=[(hx0, hx1, hy0, hy1), ...],
             mat='grass', count=70000, length=0.05, children=9, seed=3)          # emitter grid above a lawn
        dict(object="Court_Turf", mat='turf_fibre', count=90000, length=0.022, children=6, clump=0.0, ...)
                                                                               # hair from an existing object's top faces
    `mat` is a key of M (or a Material).  Remaining keys are passed to the particle settings (see _hair)."""
    if not specs:
        return
    S = bpy.context.scene
    S.cycles_curves.shape = 'RIBBONS'
    S.cycles_curves.subdivisions = 2
    keys = ("length", "children", "radius", "clump", "kink", "seed", "length_var")
    for spec in specs:
        mat = spec["mat"]
        mat = M[mat] if isinstance(mat, str) else mat
        kw = {k: spec[k] for k in keys if k in spec}
        if "object" in spec:
            ob = bpy.data.objects.get(spec["object"])
            if ob is None:
                print(f"[polish] grass: no object {spec['object']}"); continue
            _top_faces_group(ob)
            _hair(ob, mat, spec["count"], **kw)
            ob.particle_systems[-1].vertex_group_density = "top"
            ob.show_instancer_for_render = True
        else:
            x0, x1, y0, y1 = spec["rect"]
            em = _emitter(spec["name"], x0, x1, y0, y1, spec["z"], holes=spec.get("holes", ()), cell=spec.get("cell", 1.0), padding=spec.get("padding", 0.3))
            _hair(em, mat, spec["count"], **kw)


def _top_faces_group(ob):
    """Vertex group 'top' = vertices of upward-facing faces (so hair grows only from the top of a slab)."""
    if "top" in ob.vertex_groups:
        return
    vg = ob.vertex_groups.new(name="top")
    idx = sorted({v for p in ob.data.polygons if p.normal.z > 0.7 for v in p.vertices})
    if idx:
        vg.add(idx, 1.0, 'REPLACE')


def add_rug_fibres(M):
    """Short dense fibres on every object named Rug_* (boucle / shag look), colour from the rug's own material."""
    for ob in [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith("Rug_")]:
        base = ob.data.materials[0] if ob.data.materials else M['rug']
        fib = base.copy(); fib.name = base.name + "_Fibre"
        nt = fib.node_tree
        b = nt.nodes.get("Principled BSDF")
        if b is not None:
            hi = nt.nodes.new("ShaderNodeHairInfo")
            col_in = b.inputs["Base Color"]
            src = col_in.links[0].from_socket if col_in.links else None
            shade = _mat._ramp(nt, hi.outputs["Intercept"], [(0.0, (0.78, 0.78, 0.78, 1)), (1.0, (1.12, 1.12, 1.12, 1))])
            if src is not None:
                mixed = _mat._mixrgb(nt, 1.0, src, shade, 'MULTIPLY')
                nt.links.new(col_in, mixed)
            b.inputs["Roughness"].default_value = 0.85
        _top_faces_group(ob)
        area = sum(p.area for p in ob.data.polygons if p.normal.z > 0.7)
        _hair(ob, fib, int(min(80000, area * 3200)), length=0.007, children=12, seed=13, radius=0.0007, clump=0.0, kink=0.45, length_var=0.35)
        ob.particle_systems[-1].vertex_group_density = "top"
        ob.show_instancer_for_render = True


# ------------------------------------------------------------------ leaf cards on the near trees
def _leaf_object(name, mat, size=1.0):
    mb = MB()
    mb.quad((-0.5 * size, -0.5 * size, 0), (0.5 * size, -0.5 * size, 0), (0.5 * size, 0.5 * size, 0), (-0.5 * size, 0.5 * size, 0))
    ob = mb.build(name, [mat], coll='Polish', recalc=False)
    me = ob.data
    uv = me.uv_layers.new(name="UVMap")
    for li, l in enumerate(me.loops):
        v = me.vertices[l.vertex_index].co
        uv.data[li].uv = (v.x / size + 0.5, v.y / size + 0.5)
    ob.location = (0, 0, -80)                     # source object parked out of sight
    return ob


def _holey_copy(mat, name, coverage=0.55, scale=6.0):
    """Copy of a foliage material with noise-cut holes so light and sky show through the canopy core."""
    m = mat.copy(); m.name = name
    nt = m.node_tree
    b = nt.nodes.get("Principled BSDF")
    out = nt.nodes["Material Output"]
    surf = out.inputs["Surface"].links[0].from_socket if out.inputs["Surface"].links else b.outputs["BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = scale; n.inputs["Detail"].default_value = 3.0
    nt.links.new(n.inputs["Vector"], tc.outputs["Object"])
    gt = nt.nodes.new("ShaderNodeMath"); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = 1.0 - coverage
    nt.links.new(gt.inputs[0], n.outputs["Fac"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(mix.inputs["Fac"], gt.outputs[0])
    nt.links.new(mix.inputs[1], tr.outputs["BSDF"]); nt.links.new(mix.inputs[2], surf)
    nt.links.new(out.inputs["Surface"], mix.outputs["Shader"])
    return m


def _foliage_area(ob):
    vg = ob.vertex_groups.get("foliage")
    if vg is None:
        return 0.0
    idx = vg.index
    me = ob.data
    in_grp = [any(g.group == idx for g in v.groups) for v in me.vertices]
    return sum(p.area for p in me.polygons if all(in_grp[i] for i in p.vertices))


LEAF_KEYS = {'oak': 'leaf_oak', 'olive': 'leaf_olive', 'shrub': 'leaf_shrub', 'needle': 'leaf_needle',
             'cluster_oak': 'leaf_cluster_oak', 'cluster_olive': 'leaf_cluster_olive', 'cluster_shrub': 'leaf_cluster_shrub'}


def add_leaf_cards(M):
    """Particle-instanced leaf cards on every mesh that opts in with a custom property, e.g.

        ob["leaf_cards"] = {"leaf": "cluster_shrub", "size": 0.14, "density": 120, "holey": 0.6, "group": "foliage"}

    leaf     one of LEAF_KEYS (a leaf_card material in the library) or the name of an existing material
    size     card size (m); density = cards per m² of the emitting faces (count is capped at 140k)
    group    vertex group to emit from (default 'foliage'; created from material slots >= 1 if missing, or the
             whole mesh when the object has a single material)
    holey    optional: material slot 1 (the canopy core) is swapped for a noise-perforated copy with this coverage
    Trees built by archviz/trees.py carry their own leaf geometry and do not use this."""
    leaf_obs = {}
    holey = {}
    rng = random.Random(9)
    for ob in [o for o in bpy.data.objects if o.type == 'MESH' and o.get("leaf_cards") is not None]:
        spec = ob["leaf_cards"]
        leaf_key = spec.get("leaf", "oak")
        size = float(spec.get("size", 0.2)); density = float(spec.get("density", 80.0))
        grp = spec.get("group", "foliage")
        if leaf_key not in leaf_obs:
            mat = M.get(LEAF_KEYS.get(leaf_key, "")) or bpy.data.materials.get(leaf_key)
            if mat is None:
                print(f"[polish] {ob.name}: unknown leaf material '{leaf_key}'"); continue
            leaf_obs[leaf_key] = _leaf_object(f"LeafCard_{leaf_key}", mat)
        leaf = leaf_obs[leaf_key]
        if grp not in ob.vertex_groups:
            vg = ob.vertex_groups.new(name=grp)
            if len(ob.data.materials) > 1:
                idx = sorted({v for p in ob.data.polygons if p.material_index >= 1 for v in p.vertices})
            else:
                idx = list(range(len(ob.data.vertices)))
            if not idx:
                continue
            vg.add(idx, 1.0, 'REPLACE')
        vgi = ob.vertex_groups[grp].index
        in_grp = [any(g.group == vgi for g in v.groups) for v in ob.data.vertices]
        area = sum(p.area for p in ob.data.polygons if all(in_grp[i] for i in p.vertices))
        if area < 0.05:
            continue
        count = int(min(140000, area * density))
        mod = ob.modifiers.new("leaves", 'PARTICLE_SYSTEM')
        ps = mod.particle_system
        ps.vertex_group_density = grp
        ps.seed = rng.randint(1, 999)
        st = ps.settings
        st.type = 'HAIR'
        st.count = count
        st.hair_length = size * 0.5
        st.emit_from = 'FACE'
        st.distribution = 'RAND'
        st.use_emit_random = True
        st.use_modifier_stack = True
        st.use_advanced_hair = True
        st.render_type = 'OBJECT'
        st.instance_object = leaf
        st.particle_size = size
        st.size_random = float(spec.get("size_random", 0.45))
        st.use_rotations = True
        st.rotation_mode = 'NOR'
        st.rotation_factor_random = float(spec.get("rot_random", 0.7))
        st.phase_factor_random = 2.0
        if hasattr(st, 'use_rotation_instance'):
            st.use_rotation_instance = True
        ob.show_instancer_for_render = True
        cov = spec.get("holey")
        if cov is not None and len(ob.data.materials) > 1:
            base = ob.data.materials[1]
            if base.name not in holey:
                holey[base.name] = _holey_copy(base, base.name + "_Holey", coverage=float(cov))
            ob.data.materials[1] = holey[base.name]


# ------------------------------------------------------------------ camera + compositor
def set_dof(cam_ob, target, fstop):
    cd = cam_ob.data
    cd.dof.use_dof = True
    cd.dof.focus_distance = (Vector(target) - Vector(cam_ob.location)).length
    cd.dof.aperture_fstop = fstop
    cd.dof.aperture_blades = 7


def setup_compositor(scene, bloom=0.12, size=6.0, threshold=1.2):
    nt = bpy.data.node_groups.new("Composite", 'CompositorNodeTree')
    scene.use_nodes = True
    scene.compositing_node_group = nt
    rl = nt.nodes.new("CompositorNodeRLayers")
    glare = nt.nodes.new("CompositorNodeGlare")
    glare.inputs["Type"].default_value = 'Bloom'
    glare.inputs["Threshold"].default_value = threshold
    glare.inputs["Strength"].default_value = bloom
    glare.inputs["Size"].default_value = size
    glare.inputs["Saturation"].default_value = 0.85
    nt.links.new(glare.inputs["Image"], rl.outputs["Image"])
    # Blender 5.x: the compositing tree is a node group whose Group Output is the composite result
    nt.interface.new_socket("Image", in_out='OUTPUT', socket_type='NodeSocketColor')
    out = nt.nodes.new("NodeGroupOutput")
    nt.links.new(out.inputs["Image"], glare.outputs["Image"])
    return nt


def build(M, grass=()):
    add_grass(M, grass)
    add_leaf_cards(M)
    # add_rug_fibres(M)   # hair fibres read as grey fur at these camera distances; the boucle shader + rbox rug wins
