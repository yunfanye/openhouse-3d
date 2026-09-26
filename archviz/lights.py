"""Light helpers shared by every house.

`room_light()` accepts either an (x0, x1, y0, y1, z_floor, z_ceiling) tuple or a room NAME; names are looked up in
the registry filled by `set_rooms(plan.ROOMS)` (run.py does this for the active house).
"""
import math
import bpy
from .mesh import collection, look_at

WARM = (1.0, 0.76, 0.52)
WARM_SOFT = (1.0, 0.82, 0.62)

_ROOMS = {}


def set_rooms(rooms):
    """Register the active house's interior volumes so room_light('kitchen') works."""
    _ROOMS.clear()
    _ROOMS.update(rooms or {})


def add_light(name, kind, loc, energy, color=WARM, size=0.1, spot=math.radians(80), blend=0.5, target=None, coll='Lights'):
    """POINT / SPOT / SUN light. Spots point straight down unless `target` is given."""
    ld = bpy.data.lights.new(name, kind)
    ld.energy = energy
    ld.color = color
    if kind in ('POINT', 'SPOT'):
        ld.shadow_soft_size = size
    if kind == 'SPOT':
        ld.spot_size = spot
        ld.spot_blend = blend
    ob = bpy.data.objects.new(name, ld)
    ob.location = loc
    collection(coll).objects.link(ob)
    if target is not None:
        look_at(ob, target)
    elif kind == 'SPOT':
        ob.rotation_euler = (0, 0, 0)          # -Z = straight down
    return ob


def area_light(name, loc, size, energy, color=WARM_SOFT, down=True, target=None, coll='Lights', spread=math.radians(180)):
    """Rectangular area light at loc with size (w, h); points down by default."""
    ld = bpy.data.lights.new(name, 'AREA')
    ld.shape = 'RECTANGLE'
    ld.size, ld.size_y = size
    ld.energy = energy
    ld.color = color
    ld.spread = spread
    ob = bpy.data.objects.new(name, ld)
    ob.location = loc
    if target is not None:
        look_at(ob, target)
    elif not down:
        ob.rotation_euler = (math.pi, 0, 0)
    collection(coll).objects.link(ob)
    return ob


def room_light(name, room, energy=None, z_off=0.08, color=WARM_SOFT, shrink=0.7):
    """One area light just under the ceiling of a registered room (see set_rooms) (or an (x0,x1,y0,y1,z0,z1) tuple)."""
    x0, x1, y0, y1, z0, z1 = _ROOMS[room] if isinstance(room, str) else room
    w, d = (x1 - x0) * shrink, (y1 - y0) * shrink
    if energy is None:
        energy = 5.0 * w * d
    return area_light(name, ((x0 + x1) / 2, (y0 + y1) / 2, z1 - z_off), (w, d), energy, color)
