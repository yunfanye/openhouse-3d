"""Render the interior in photo 22, whose old counterpart showed exterior glazing.

This is a separate photo-derived detail scene. The concealed closet/stair junction
is not resolved by the whole-house model; do not present this as its surveyed layout
or silently insert it into the production film. All geometry is modeled in Blender.

blender -b --python-exit-code 1 --python houses/webster/render_photo_closet.py
"""
from pathlib import Path
import argparse
import json
import sys

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from archviz.mesh import MB, look_at
from archviz.lights import area_light
from archviz import materials as mat


def rod(name, start, end, radius, material):
    start, end = Vector(start), Vector(end)
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=radius,
                                      depth=(end - start).length,
                                      location=(start + end) / 2)
    ob = bpy.context.object
    ob.name = name
    ob.rotation_euler = (end - start).to_track_quat('Z', 'Y').to_euler()
    ob.data.materials.append(material)
    for polygon in ob.data.polygons:
        polygon.use_smooth = True


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    white = mat.plaster('Closet warm white', (.76, .75, .71, 1), grain=.018)
    trim = mat.new_mat('Painted shelving', (.84, .83, .79, 1), rough=.48)
    carpet = mat.rug('Grey closet carpet', (.24, .23, .21, 1),
                     (.36, .35, .32, 1), scale=160)
    metal = mat.new_mat('Galvanized hanging rail', (.25, .28, .27, 1),
                        rough=.36, metal=.8)
    lead = mat.new_mat('Diamond lead came', (.11, .12, .12, 1),
                       rough=.45, metal=.65)
    glass = mat.new_mat('Clear closet glazing', (.96, .98, 1, 1),
                        rough=.025, transmission=1, ior=1.45)
    windows = [(0.40, .91, 1.42, 2.12), (1.92, 2.37, 1.43, 2.04)]
    mb = MB()
    mb.wall('Y', -.55, 3.02, -.12, 0, 0, 2.48, windows)
    mb.box(0, 1.88, 3.0, 3.12, 0, 2.48)
    mb.box(1.85, 1.97, -.55, 3.0, 0, 2.48)
    mb.box(0, 1.85, -.55, 3.0, 2.48, 2.58)
    # Full-height end of the stair enclosure; the narrow aisle continues left.
    mb.box(.92, 1.85, 1.98, 2.10, 0, 2.48)
    mb.build('Closet walls and ceiling', [white], bevel=.003)
    mb = MB()
    mb.box(0, 1.85, -.55, 3.0, -.08, 0)
    mb.build('Closet carpet', [carpet])
    mb = MB()
    mb.box(.0, .015, -.55, 3, 0, .065)
    mb.box(0, .92, 2.981, 3.0, 0, .065)
    mb.box(.905, .925, 1.98, 2.99, 0, .065)
    # Sloping, boarded stair enclosure visible on the right of the photograph.
    mb.hexa([(.94, -.55, 0), (1.85, -.55, 0), (1.85, 1.98, 0), (.94, 1.98, 0),
             (.94, -.55, .15), (1.85, -.55, .15),
             (1.85, 1.98, 1.65), (.94, 1.98, 1.65)])
    for j in range(12):
        y = -.55 + j * 2.53 / 12
        z = .15 + (y + .55) * 1.50 / 2.53
        mb.box(.94, 1.85, y, y + .008, z, z + .008)
    mb.box(1.52, 1.85, -.55, 1.98, 2.16, 2.185)
    mb.box(1.83, 1.85, -.55, 1.98, 2.02, 2.16)
    mb.box(.03, .91, 2.69, 2.995, 2.04, 2.065)
    mb.box(.03, .91, 2.97, 2.995, 1.91, 2.04)
    for y in (.4, 1.45):
        mb.box(1.52, 1.85, y, y + .025, 2.10, 2.16)
    for a, b, z0, z1 in windows:
        mb.frame(-.025, .035, a - .055, b + .055, z0 - .055, z1 + .055,
                 .04, axis='X')
        mb.frame(-.115, -.03, a, b, z0, z1, .035, axis='X')
        mb.box(-.02, .075, a - .055, b + .055, z0 - .06, z0 - .045)
    mb.build('Shelves trim and stair enclosure', [trim], bevel=.0015)
    rod('Long hanging rail', (1.50, -.55, 2.04), (1.50, 1.96, 2.04), .016, metal)
    rod('Rear hanging rail', (.035, 2.68, 1.94), (.91, 2.68, 1.94), .014, metal)
    for index, (a, b, z0, z1) in enumerate(windows):
        pane = MB()
        pane.box(-.069, -.066, a + .035, b - .035, z0 + .035, z1 - .035)
        pane.build(f'Window {index + 1} glass', [glass])
        # Clip two diagonal line families to the rectangular clear opening.
        ya, yb, za, zb = a + .035, b - .035, z0 + .035, z1 - .035
        for slope in (-2.15, 2.15):
            for k in range(-18, 19):
                intercept = k * .49
                hits = []
                for y in (ya, yb):
                    z = slope * y + intercept
                    if za <= z <= zb:
                        hits.append((-.055, y, z))
                for z in (za, zb):
                    y = (z - intercept) / slope
                    if ya <= y <= yb:
                        hits.append((-.055, y, z))
                if len(hits) == 2 and (Vector(hits[0]) - Vector(hits[1])).length > .001:
                    rod(f'Diamond came {index} {slope} {k}', *hits, .004, lead)
        area_light(f'Window daylight {index}', (-.14, (a+b)/2, (z0+z1)/2),
                   (b-a, z1-z0), 30, color=(.92, .96, 1),
                   target=(1.4, (a+b)/2, 1.0))
    area_light('Open doorway fill', (.85, -.4, 2.08), (1.3, .8),
               12, color=(1, .96, .9), target=(.85, 2.9, 1.2))
    world = bpy.data.worlds.new('Soft daylight')
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs['Color'].default_value = (.80, .87, 1, 1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value = .65
    scene.world = world
    camera_data = bpy.data.cameras.new('Photo 22 interior')
    camera = bpy.data.objects.new('Photo 22 interior', camera_data)
    scene.collection.objects.link(camera)
    camera.location = (.92, -.23, 1.54)
    look_at(camera, (.92, 2.85, 1.52))
    camera_data.lens = 18
    camera_data.sensor_width = 36
    camera_data.clip_start = .02
    scene.camera = camera
    return scene


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--preview', action='store_true')
    ap.add_argument('--out', type=Path,
                    default=ROOT / 'houses/webster/output/final/details')
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    args = ap.parse_args(argv)
    scene = build()
    scene.render.engine = 'CYCLES'
    from archviz.rendering import configure_device
    device = configure_device(scene)
    scene.cycles.samples = 48 if args.preview else 160
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 12
    scene.cycles.diffuse_bounces = 8
    scene.cycles.adaptive_threshold = .012
    scene.render.resolution_x = 960 if args.preview else 1920
    scene.render.resolution_y = 640 if args.preview else 1280
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Medium High Contrast'
    scene.view_settings.exposure = 0
    folder = args.out / ('preview' if args.preview else 'renders')
    folder.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(folder / '22.png')
    scene['reference_photo'] = 'houses/webster/photos/22.jpg'
    scene['reconstruction_scope'] = (
        'Separate photo-derived closet detail. Hidden dimensions and stair junction inferred; '
        'not incorporated into the production house or film.')
    if not args.preview:
        model = args.out / 'model'
        model.mkdir(exist_ok=True)
        from archviz.rendering import pack_scene
        pack_scene()
        bpy.ops.wm.save_as_mainfile(filepath=str(model / 'photo_22_closet.blend'))
    bpy.ops.render.render(write_still=True)
    (folder / '22.json').write_text(json.dumps({
        'reference_photo': scene['reference_photo'],
        'scope': scene['reconstruction_scope'],
        'camera_location': list(scene.camera.location),
        'camera_rotation': list(scene.camera.rotation_euler),
        'lens_mm': scene.camera.data.lens,
        'resolution': [scene.render.resolution_x, scene.render.resolution_y],
        'samples': scene.cycles.samples,
        'engine': 'Cycles / ' + device,
    }, indent=2) + '\n')


if __name__ == '__main__':
    main()
