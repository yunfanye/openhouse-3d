"""349 Walsh Rd, Atherton — house configuration read by run.py and the tools (bpy-free).

Geometry modules (MODULES) each expose build(M) and are built in order; polish + sky + cameras + render settings are
generic (run.py).  Cameras are matched to listing photos (PHOTO_PAIRS drives tools/compare.py).
"""
from .plan import *
from .shots import SHOTS, TAKE, BY_NAME, TITLES, L as _L

NAME = "walsh"
TITLE = "349 Walsh Rd, Atherton CA"
BLEND = "villa_walsh_v2.blend"                      # --save writes output/<BLEND>
MODULES = ["exterior", "site", "interior_lower", "interior_main", "interior_suite", "interior_upper", "landscape"]
assert abs(_L - Z_LIV) < 1e-6, "shots.L must equal plan.Z_LIV"


def materials():
    """The material palette for this house: the default library with the fascia perforations at this soffit height."""
    from archviz import materials as _m
    return _m.build_materials(perf_z0=Z_SOF + 0.11)


# ---------------------------------------------------------------- sky (dusk a few minutes after sunset, sun WSW)
SKY = dict(sun_dir=(-0.80, -0.45, 0.16), sun_energy=2.2, sun_color=(1.0, 0.80, 0.62), strength=0.55, sun_elevation=1.2)

# ---------------------------------------------------------------- cameras: name -> (location, target, lens mm)
CAMS = {
    # exterior (matching listing photos)
    'hero':     ((18.5, -10.0, 2.6),   (4.0, 4.5, 4.6),        21),    # photo 01 / 34
    'aerial':   ((30.0, -14.0, 12.0),  (6.0, 6.0, 4.0),        26),    # photo 34
    'front':    ((0.6, -26.0, 4.0),    (0.6, 2.0, 4.6),        32),    # photo 23
    'entry':    ((1.0, -16.0, 2.3),    (1.0, 2.0, 3.6),        32),    # photo 02
    'court':    ((24.0, 2.8, 3.9),     (9.0, 9.6, 4.3),        22),    # photo 04 (from the SE corner: spa in the right foreground, pool running to the pavilion)
    'court_n':  ((18.0, 3.6, 4.2),     (17.0, 16.0, 5.2),      20),    # photo 03
    'pool':     ((17.8, -3.4, 1.8),    (17.8, 12.0, 4.0),      20),    # photo 24 (through the glass wall)
    'drone':    ((34.0, 2.0, 16.0),    (8.0, 11.0, 4.0),       30),    # photo 22
    'garden':   ((21.0, -6.8, 3.2),    (9.0, 6.5, 4.6),        24),    # from the lawn's SE quarter (clear of the east oak + the lawn olive crowns)
    'green':    ((16.2, 12.6, 1.2 + Z_LIV), (19.6, 17.8, 1.7 + Z_LIV), 24),  # photo 15 (low, whole wall with the sofa group in front)
    'terrace':  ((20.8, 23.3, 1.65 + Z_UP), (10.0, 12.5, 0.9 + Z_UP), 20),  # photo 21 (roof dining terrace, table centred, glass bar behind)
    'rear':     ((-11.6, 31.2, 3.3),   (-1.0, 21.5, 4.6),      24),    # 3/4 from the NW corner of the rear lawn (inside the glass rail)
    # interiors
    'foyer':    ((3.0, 7.6, 1.7),      (-2.0, 1.5, 2.6),       18),    # photo 05
    'stair':    ((0.8, 7.4, 1.6),      (-3.0, 4.5, 5.5),       16),    # photo 09
    'lounge':   ((-7.4, 5.8, 1.75),    (-8.6, 15.0, 1.0),      17),    # photo 06
    'wine':     ((-8.4, 10.2, 0.6),    (-8.5, 16.8, 0.75),     19),    # photo 07 (sunken lounge floor -0.9)
    'theatre':  ((-7.6, 23.0, 0.95),   (-11.2, 20.0, 0.2),     18),    # photo 08 (from the back corner over the aisle)
    'living':   ((8.8, 10.6, 1.6 + Z_LIV), (11.0, 5.0, 1.4 + Z_LIV), 18),  # photo 10
    'dining':   ((3.0, 17.3, 1.7 + Z_LIV), (5.5, 5.0, 1.6 + Z_LIV),  18),  # photo 11
    'kitchen':  ((-4.9, 9.4, 1.6 + Z_LIV), (-9.5, 16.0, 1.3 + Z_LIV), 20), # photo 12
    'family':   ((8.4, 12.0, 1.55 + Z_LIV), (10.8, 17.6, 1.3 + Z_LIV), 18),  # photo 14 (toward the TV wall)
    'master':   ((-5.6, 18.4, 1.5 + Z_LIV), (-10.6, 21.6, 1.05 + Z_LIV), 22),  # photo 17 (from the fireplace side across the bed to the glass)
    'bath':     ((-1.0, 19.9, 1.5 + Z_LIV), (-3.5, 23.6, 1.3 + Z_LIV),  18),  # photo 18
    'closet':   ((3.0, 19.9, 1.5 + Z_LIV), (0.5, 23.6, 1.4 + Z_LIV),    18),  # photo 19
    'gym':      ((13.5, 18.5, 1.5 + Z_LIV), (9.0, 23.0, 1.4 + Z_LIV),   18),  # photo 20
    'office':   ((7.0, 18.2, 1.5 + Z_LIV), (4.5, 23.5, 1.4 + Z_LIV),    18),  # photo 16
    'upfamily': ((6.6, 10.4, 1.5 + Z_UP), (1.5, 5.0, 1.2 + Z_UP),      18),  # photo 30 (from the NE corner, TV pier + sofa + desk)
    'upbed':    ((1.5, 18.4, 1.55 + Z_UP), (7.5, 21.2, 1.1 + Z_UP),    18),  # photo 33 (bed side-on, terrace door + console beyond)
    'guest':    ((23.5, 18.6, 1.4 + Z_LIV), (16.5, 23.4, 1.3 + Z_LIV), 18),  # photo 25
}
EXT = ['hero', 'aerial', 'front', 'entry', 'court', 'court_n', 'pool', 'drone', 'garden', 'green', 'terrace', 'rear']
# per-camera exposure (EV): exteriors are dusk-lit by sun/sky, interiors by their own lights; bright pale rooms need less
EXPOSURE = {'upfamily': -0.7, 'upbed': -0.45, 'master': -0.05, 'kitchen': -0.25, 'closet': -0.15, 'bath': 0.05, 'dining': 0.05,
            'family': 0.0, 'living': 0.0, 'foyer': 0.2, 'stair': 0.1, 'lounge': 0.0, 'wine': -0.05, 'theatre': 0.1,
            'gym': 0.05, 'office': 0.1, 'guest': 0.15, 'rear': 0.9, 'terrace': 0.7}
EXPOSURE_DEFAULT = {'ext': 0.6, 'int': 0.3}
DOF = {'green': 22.0, 'court': 16.0, 'kitchen': 5.6, 'closet': 5.6}          # per-camera f-stop overrides
DOF_DEFAULT = {'ext': 11.0, 'int': 4.5}

# camera -> listing photo index (photos/NN-*.jpg) for tools/compare.py
PHOTO_PAIRS = [
    ('hero', 1), ('aerial', 34), ('front', 23), ('entry', 2), ('court', 4), ('court_n', 3), ('pool', 24), ('drone', 22),
    ('green', 15), ('terrace', 21), ('foyer', 5), ('stair', 9), ('lounge', 6), ('wine', 7), ('theatre', 8),
    ('living', 10), ('dining', 11), ('kitchen', 12), ('family', 14), ('master', 17), ('bath', 18), ('closet', 19),
    ('gym', 20), ('office', 16), ('upfamily', 30), ('upbed', 33), ('guest', 25),
]

# ---------------------------------------------------------------- polish: hair grass (archviz.polish.add_grass)
GRASS = [
    # front lawn (real turf, mown in stripes): skip the fire trough + the stair landing strip
    dict(name="Grass_FrontLawn", rect=(LAWN_X0 + 0.2, LAWN_X1 - 0.2, LAWN_Y0 + 0.5, LAWN_Y1 - 0.4), z=Z_LAWN + 0.004,
         holes=[(FIRE[0] - 0.2, FIRE[1] + 0.2, FIRE[2] - 0.2, FIRE[3] + 0.2), (ST_X0 - 0.2, ST_X1 + 0.2, TY0 - 3.4, TY0)],
         mat='grass', count=70000, length=0.05, children=9, seed=3),
    dict(name="Grass_RearLawn", rect=(-12.6, 7.3, MY1 + 0.2, REAR_Y1 - 1.3), z=Z_LIV + 0.004,
         mat='grass_rear', count=40000, length=0.05, children=9, seed=5),
    # grass strips in the motor-court paving (thin boxes -> emit from their top faces)
    dict(object="Court_GrassStrips", mat='grass', count=24000, length=0.04, children=8, seed=7, radius=0.003),
    # artificial turf (courtyard + roof terraces): short, dense, uniform "velvet" fibres
    dict(object="Court_Turf", mat='turf_fibre', count=90000, length=0.022, children=6, seed=11, radius=0.0025, clump=0.0, kink=0.02, length_var=0.15),
    dict(object="Terrace_Turf", mat='turf_fibre', count=60000, length=0.022, children=6, seed=11, radius=0.0025, clump=0.0, kink=0.02, length_var=0.15),
]

# ---------------------------------------------------------------- film: doors the long take passes through (archviz.film.open_doors)
DOORS = dict(
    # leaves cut out of the merged suite-door meshes and left open: (name, sources, bbox, hinge (x, y), angle)
    static=[
        ("VestDoorL", ("Suite_Doors", "Suite_DoorHardware"), (-1.02, -0.09, 17.70, 18.05, Z_LIV, Z_LIV + 2.45), (-1.0, 17.875), +100),
        ("VestDoorR", ("Suite_Doors", "Suite_DoorHardware"), (-0.11, 0.82, 17.70, 18.05, Z_LIV, Z_LIV + 2.45), (0.8, 17.875), -100),
        ("MasterDoor", ("Suite_Doors", "Suite_DoorHardware"), (-4.78, -4.42, 18.28, 19.32, Z_LIV, Z_LIV + 2.35), (-4.6, 18.3), +100),
        ("BathDoor", ("Suite_Doors", "Suite_DoorHardware"), (-3.12, -2.08, 19.42, 19.78, Z_LIV, Z_LIV + 2.35), (-3.1, 19.6), +100),
    ],
    # the entry pivot door (exterior.py: leaf DOOR_X0..DOOR_X1 at y 0.45..0.52, floor pivot at DOOR_X0 + 0.12), animated open
    entry=("Entry_Door", (0.47, 0.485), 100),
)

# ---------------------------------------------------------------- film: passability probes (--probe)
STAIR_PROBE = dict(centre=STAIR_C, radius=1.75, z_from=(5.8, 2.5))
PROBE_WALLS = [
    # name, axis of the wall plane ('X' = plane x=b, along y; 'Y' = plane y=b, along x), b, (a0, a1), (z0, z1)
    ("foyer|billiard  x=-4.35", 'X', -4.35, (0.5, 8.3), (0.3, 2.1)),
    ("billiard|lounge y=8.4", 'Y', 8.4, (-12.0, -5.0), (-0.6, 2.0)),
    ("lounge|theatre  y=17.2", 'Y', 17.2, (-12.0, -5.0), (-0.6, 2.0)),
    ("dining|kitchen  x=-4.45", 'X', -4.45, (8.5, 17.5), (2.9, 5.4)),
    ("dining|living   x=7.3", 'X', 7.3, (3.9, 11.1), (2.9, 5.4)),
    ("dining|family   x=7.3", 'X', 7.3, (11.5, 17.7), (2.9, 5.4)),
    ("living S glass  y=3.9", 'Y', 3.9, (7.6, 12.4), (2.9, 5.4)),
    ("living E glass  x=12.4", 'X', 12.4, (4.0, 11.1), (2.9, 5.4)),
    ("family E glass  x=12.4", 'X', 12.4, (11.5, 17.7), (2.9, 5.4)),
    ("kitchen|master  y=17.7", 'Y', 17.7, (-12.0, -4.7), (2.9, 5.4)),
    ("dining|office   y=17.8", 'Y', 17.8, (-4.3, 7.0), (2.9, 5.4)),
    ("foyer front glass y=0.45", 'Y', 0.45, (-4.5, 7.0), (0.3, 5.5)),
    ("court E screen  x=24.6", 'X', 24.6, (3.2, 17.8), (2.9, 7.5)),
    ("living|family  y=11.3", 'Y', 11.3, (7.6, 12.4), (2.9, 5.4)),
    ("master N glass y=23.7", 'Y', 23.7, (-12.0, -4.7), (2.9, 5.4)),
    ("kitchen N side y=17.0 (cabinets?)", 'Y', 17.0, (-12.0, -4.7), (2.9, 5.4)),
    ("master S side  y=18.6 (headboard?)", 'Y', 18.6, (-12.0, -4.7), (2.9, 5.4)),
    ("master mid     y=20.5 (bed?)", 'Y', 20.5, (-12.0, -4.7), (2.9, 5.4)),
    ("lounge mid     y=12.0 (sofas?)", 'Y', 12.0, (-12.0, -5.0), (-0.6, 2.0)),
    ("billiard mid   y=5.0 (table?)", 'Y', 5.0, (-12.0, -4.5), (0.1, 2.0)),
    ("foyer mid      y=4.0 (stair core?)", 'Y', 4.0, (-4.5, 7.0), (0.3, 5.5)),
    ("dining mid     x=1.5 (table?)", 'X', 1.5, (8.5, 17.5), (2.9, 5.4)),
    ("kitchen mid    x=-8.0 (islands?)", 'X', -8.0, (8.5, 17.5), (2.9, 5.4)),
    ("living mid     x=9.5", 'X', 9.5, (4.0, 11.1), (2.9, 5.4)),
    ("court canopy   y=14.5 (canopy height?)", 'Y', 14.5, (12.6, 24.4), (2.9, 9.0)),
]
