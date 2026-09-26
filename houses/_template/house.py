"""Template house — configuration read by run.py and the tools (bpy-free).  Copy houses/_template to houses/<name>,
then fill plan.py, this file, shots.py and the geometry modules.  Only NAME, MODULES and CAMS are required; the
rest has defaults in run.py."""
from .plan import *
from .shots import SHOTS, BY_NAME, TITLES

NAME = "_template"
TITLE = "Template house"
BLEND = "template.blend"                              # --save writes output/<BLEND>
MODULES = ["exterior", "site", "interior", "landscape"]   # geometry modules, built in this order, each build(M)


def materials():
    """Material palette: the default library (archviz/materials.py) - extend / override entries here if needed."""
    from archviz import materials as _m
    M = _m.build_materials(perf_z0=Z_SOF + 0.11)
    return M


# sky: unit vector TOWARD the sun (dusk from the west-south-west), world strength, sun elevation (deg) / energy / colour
SKY = dict(sun_dir=(-0.80, -0.45, 0.16), sun_energy=2.2, sun_color=(1.0, 0.80, 0.62), strength=0.55, sun_elevation=1.2)

# cameras: name -> (location, look-at target, lens mm).  Match each to a listing photo and list the pairs below.
CAMS = {
    'hero':    ((16.0, -18.0, 2.2), (0.0, 4.0, 3.0), 28),          # 3/4 view from the lawn
    'entry':   ((0.0, -12.0, 1.6), (0.0, 2.0, 2.2), 32),           # straight at the door
    'living':  ((4.5, 1.0, 1.5), (-3.0, 6.0, 1.3), 20),
    'bedroom': ((-6.0, 1.2, Z_UP + 1.5), (-2.0, 8.0, Z_UP + 1.2), 20),
}
EXT = ['hero', 'entry']                                # exteriors (dusk exposure + f/11); everything else is an interior
EXPOSURE = {}                                          # per-camera EV overrides, e.g. {'bedroom': -0.3}
DOF = {}                                               # per-camera f-stop overrides
PHOTO_PAIRS = []                                       # [('hero', 1), ('living', 4), ...] -> tools/compare.py

# polish: hair grass (archviz.polish.add_grass); hedges / green walls opt into leaf cards with ob["leaf_cards"]
GRASS = [
    dict(name="Grass_Lawn", rect=(LAWN[0] + 0.2, LAWN[1] - 0.2, LAWN[2] + 0.2, LAWN[3] - 0.2), z=0.024,
         holes=[(-2.2, 2.2, -14.0, MY0)], mat='grass', count=40000, length=0.05, children=9, seed=3),
]

# film: doors the camera passes through (archviz.film.open_doors); passability probes (--probe)
DOORS = dict(static=[], entry=("Entry_Door", (DOOR_X0 + 0.1, MY0 + 0.1 + 0.022), 100))
PROBE_WALLS = [("living|kitchen y=7.0", 'Y', PARTITION_Y, (MX0, MX1), (0.2, 3.0))]
