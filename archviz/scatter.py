"""Instanced scattering for big backdrops (Blender 5.x geometry nodes; house-agnostic).

Thousands of distant houses or trees are cheapest as instances: a handful of prototype objects live in a collection
that is NOT linked to the scene, and one point-cloud object carries a geometry-nodes modifier (Instance on Points ->
Collection Info) that places a chosen prototype at every point with its own rotation and scale.  Cycles renders
instances without copying their meshes, so a 10 000-house suburb costs little more memory than its prototypes.

  protos = scatter.prototypes("Proto_Houses")          # an unlinked collection
  scatter.adopt(ob, protos)                            # move a built object (at the origin) into it
  scatter.instance_points("Suburb_Houses", pts, protos, index=[...], rot_z=[...], scale=[...], coll="Backdrop")

Prototype order is the collection's child order (alphabetical by object name in Collection Info with "Separate
Children"): name prototypes with a sortable prefix (P00_, P01_ ...) and pass `index` in that order.
"""
import bpy
from .mesh import collection


def prototypes(name):
    """A collection that holds prototype objects; it is not linked to the scene, so the prototypes never render at
    their own (origin) positions."""
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    c.use_fake_user = False
    return c


def adopt(ob, protos, parts=()):
    """Move `ob` (and any extra `parts` objects) out of the scene collections into the prototype collection."""
    for o in (ob, *parts):
        if o is None:
            continue
        for c in list(o.users_collection):
            c.objects.unlink(o)
        protos.objects.link(o)
    return ob


def _node_group(protos):
    """One node group per prototype collection (the collection is the Collection Info node's own input)."""
    name = 'Scatter_' + protos.name
    ng = bpy.data.node_groups.get(name)
    if ng is not None:
        return ng
    ng = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    ng.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    N, L = ng.nodes, ng.links
    gi = N.new('NodeGroupInput')
    go = N.new('NodeGroupOutput')
    ci = N.new('GeometryNodeCollectionInfo')
    ci.transform_space = 'ORIGINAL'
    ci.inputs['Separate Children'].default_value = True
    ci.inputs['Reset Children'].default_value = True
    ci.inputs['Collection'].default_value = protos
    iop = N.new('GeometryNodeInstanceOnPoints')
    iop.inputs['Pick Instance'].default_value = True
    L.new(iop.inputs['Points'], gi.outputs['Geometry'])
    L.new(iop.inputs['Instance'], ci.outputs['Instances'])
    idx = N.new('GeometryNodeInputNamedAttribute'); idx.data_type = 'INT'
    idx.inputs['Name'].default_value = 'proto'
    L.new(iop.inputs['Instance Index'], idx.outputs['Attribute'])
    rot = N.new('GeometryNodeInputNamedAttribute'); rot.data_type = 'FLOAT_VECTOR'
    rot.inputs['Name'].default_value = 'rot'
    e2r = N.new('FunctionNodeEulerToRotation')
    L.new(e2r.inputs['Euler'], rot.outputs['Attribute'])
    L.new(iop.inputs['Rotation'], e2r.outputs['Rotation'])
    sc = N.new('GeometryNodeInputNamedAttribute'); sc.data_type = 'FLOAT_VECTOR'
    sc.inputs['Name'].default_value = 'scale'
    L.new(iop.inputs['Scale'], sc.outputs['Attribute'])
    L.new(go.inputs['Geometry'], iop.outputs['Instances'])
    return ng


def instance_points(name, pts, protos, index=None, rot_z=None, scale=None, coll='Backdrop', tilt=None):
    """One object whose geometry-nodes modifier instances prototypes of `protos` at `pts` [(x, y, z)].
    index: prototype index per point (default 0); rot_z: heading in radians; scale: float or (sx, sy, sz) per
    point; tilt: optional (rx, ry) per point in radians (leaning trees)."""
    n = len(pts)
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(p) for p in pts], [], [])
    a = me.attributes.new('proto', 'INT', 'POINT')
    a.data.foreach_set('value', [int(i) for i in (index or [0] * n)])
    rots = []
    for k in range(n):
        rx, ry = tilt[k] if tilt else (0.0, 0.0)
        rots += [rx, ry, float(rot_z[k]) if rot_z else 0.0]
    a = me.attributes.new('rot', 'FLOAT_VECTOR', 'POINT')
    a.data.foreach_set('vector', rots)
    scs = []
    for k in range(n):
        s = scale[k] if scale else 1.0
        scs += list(s) if isinstance(s, (tuple, list)) else [s, s, s]
    a = me.attributes.new('scale', 'FLOAT_VECTOR', 'POINT')
    a.data.foreach_set('vector', scs)
    ob = bpy.data.objects.new(name, me)
    collection(coll).objects.link(ob)
    mod = ob.modifiers.new('Scatter', 'NODES')
    mod.node_group = _node_group(protos)
    return ob
