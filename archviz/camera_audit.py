"""Inspect the actual baked camera and evaluated geometry throughout a scene."""
import math


def audit(scene, near_distance=.18, clearance=.32):
    import bpy
    from mathutils import Vector
    fps = scene.render.fps / scene.render.fps_base
    directions = [Vector(value) for value in ((1, 0, 0), (-1, 0, 0), (0, 1, 0),
                                               (0, -1, 0), (0, 0, 1), (0, 0, -1))]
    original_frame = scene.frame_current
    obstacles, crossings, near, speed, pan = [], [], [], [], []
    previous = None
    try:
        for frame in range(scene.frame_start, scene.frame_end + 1):
            scene.frame_set(frame)
            graph = bpy.context.evaluated_depsgraph_get()
            camera = scene.camera.evaluated_get(graph)
            location = camera.matrix_world.translation.copy()
            direction = camera.matrix_world.to_quaternion() @ Vector((0, 0, -1))
            if previous:
                travel = location - previous[0]
                speed.append((frame, travel.length * fps))
                if travel.length > 1e-8:                  # the lens swept through a surface between two frames
                    hit, point, _, _, obj, _ = scene.ray_cast(graph, previous[0], travel.normalized(), distance=travel.length)
                    if hit:
                        crossings.append({'frame': frame, 'object': obj.name, 'metres': (point - previous[0]).length})
                pan.append((frame, math.degrees(direction.angle(previous[1])) * fps))
            previous = location, direction
            for ray in directions:
                hit, point, _, _, obj, _ = scene.ray_cast(graph, location, ray, distance=clearance)
                if hit:
                    near.append({'frame': frame, 'metres': (point - location).length, 'object': obj.name})
            hit, point, _, _, obj, _ = scene.ray_cast(graph, location, direction, distance=near_distance)
            if hit:
                obstacles.append({'frame': frame, 'metres': (point - location).length, 'object': obj.name})
    finally:
        scene.frame_set(original_frame)
    return {'frames': scene.frame_end - scene.frame_start + 1, 'fps': fps,
            'lens_obstructions': obstacles, 'path_crossings': crossings, 'near_surfaces': near,
            'peak_speed_mps': max(speed, key=lambda item: item[1], default=None),
            'peak_pan_degps': max(pan, key=lambda item: item[1], default=None),
            'near_distance_m': near_distance, 'clearance_m': clearance}
