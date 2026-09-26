"""Dump a per-object scene signature after running a build script - for regression diffs when refactoring the engine.
  blender -b --python tools/scene_signature.py -- run.py scratch/sig.json --house walsh --norender
  (diff two JSON dumps with any json-aware tool; object names, mesh sizes, materials, modifiers, particle systems, lights, cameras)"""
import sys, os, json, runpy
import bpy
argv = sys.argv[sys.argv.index("--") + 1:]
script, out = argv[0], argv[1]
sys.argv = ["blender", "--"] + argv[2:]
runpy.run_path(script, run_name="__main__")
sig = {}
for ob in sorted(bpy.data.objects, key=lambda o: o.name):
    d = {"type": ob.type, "loc": [round(v, 4) for v in ob.location]}
    if ob.type == 'MESH':
        me = ob.data
        d.update(verts=len(me.vertices), polys=len(me.polygons), mats=[m.name if m else None for m in me.materials],
                 mods=[(m.type, getattr(m, 'levels', None), getattr(m, 'width', None)) for m in ob.modifiers],
                 psys=[(p.settings.count, p.settings.hair_length, p.settings.rendered_child_count, p.settings.render_type) for p in ob.particle_systems],
                 smooth=sum(1 for p in me.polygons if p.use_smooth), props={k: str(ob[k]) for k in ob.keys() if not k.startswith('_')})
    elif ob.type == 'LIGHT':
        d.update(kind=ob.data.type, energy=round(ob.data.energy, 3), color=[round(c, 3) for c in ob.data.color],
                 size=round(getattr(ob.data, 'shadow_soft_size', 0), 3), vis=[ob.visible_glossy, ob.visible_transmission, ob.visible_camera])
    elif ob.type == 'CAMERA':
        d.update(lens=ob.data.lens, dof=ob.data.dof.use_dof, fstop=round(ob.data.dof.aperture_fstop, 2), focus=round(ob.data.dof.focus_distance, 3))
    d["coll"] = [c.name for c in ob.users_collection]
    sig[ob.name] = d
sig["_world"] = {"nodes": sorted(n.type for n in bpy.context.scene.world.node_tree.nodes)} if bpy.context.scene.world else None
sig["_materials"] = sorted(m.name for m in bpy.data.materials if m.users)
S = bpy.context.scene
sig["_render"] = {"engine": S.render.engine, "samples": S.cycles.samples, "thr": S.cycles.adaptive_threshold, "res": [S.render.resolution_x, S.render.resolution_y],
                  "exposure": S.view_settings.exposure, "look": S.view_settings.look, "compositor": bool(getattr(S, "compositing_node_group", None) or getattr(S, "node_tree", None))}
json.dump(sig, open(out, "w"), indent=0, sort_keys=True)
print("[dump]", out, len(sig), "entries")
