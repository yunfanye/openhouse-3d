"""1836 Webster St, Palo Alto — house configuration read by run.py and the tools (bpy-free).

Geometry modules (MODULES) each expose build(M) and are built in order.  Ownership:
  exterior        every wall in plan.WALLS (with plan.OPENINGS cut out), every window / exterior door unit, the
                  arches' curved heads, slabs (main floor, upper floor / single-storey roof deck with the stair well),
                  roofs (flat + parapet caps + vent dots, gable, wing shed roof), chimney, porch floor + steps + hood,
                  rear brick steps + rail, deck floor, Juliet rail, exterior light fixtures
  site            ground, driveway, walk, sidewalk / parkway / street, patio bricks, fences + gate, garage, shed,
                  lawn planes / beds / mulch, outdoor furniture, string lights, neighbour masses
  interior_front  finishes + furniture + lights of living, entry, stair (the flights, rail), dining
  interior_back   finishes + furniture + lights of hall, kitchen (all built-ins), laundry, hall2, family, bed_a,
                  half, bath_a, bed_b
  interior_upper  finishes + furniture + lights of the upper rooms + deck furniture
  landscape       trees, shrubs, hedges (oleander), street trees, ground cover
Finishes = floors, ceilings, crown / base mouldings, door + window casings on the INSIDE, interior door leaves are
built by exterior (they are openings).  Every module reads positions only from plan.py.
"""
from .plan import *
from .shots import SHOTS, TAKE, FINALE, CUT, BY_NAME, TITLES

NAME = "webster"
TITLE = "1836 Webster St, Palo Alto CA"
BLEND = "webster.blend"
MODULES = ["exterior", "site", "interior_front", "interior_back", "interior_upper", "landscape", "refinements"]

# 3000 K lamps for the interiors (the listing photos are daylight; the film is a warm dusk)
K30 = (1.0, 0.84, 0.66)


def materials():
    """The default library plus this house's palette (keys used by every module)."""
    from archviz import materials as _m
    M = _m.build_materials(perf_z0=Z_ROOF1 + 0.11)
    # ---- exterior
    M['stucco'] = _m.plaster("StuccoBlueGrey", base=(0.36, 0.41, 0.46, 1), rough=0.9, grain=0.25)      # photos 28-30
    M['stucco_wing'] = M['stucco']
    M['trim'] = _m.new_mat("TrimWhite", (0.88, 0.88, 0.85, 1), rough=0.35, spec=0.5, coat=0.3)          # painted wood sashes / casings
    M['door_grey'] = _m.new_mat("DoorGrey", (0.30, 0.31, 0.32, 1), rough=0.4, coat=0.4)                # front door (photo 02)
    M['clay_tile'] = _m.noise_mat("ClayTile", (0.50, 0.22, 0.12, 1), (0.66, 0.34, 0.20, 1), scale=6, bump=0.3, rough=0.8)
    M['roof_flat'] = _m.noise_mat("RoofTorchDown", (0.45, 0.44, 0.42, 1), (0.58, 0.57, 0.54, 1), scale=25, bump=0.2, rough=0.9)
    M['iron_white'] = _m.new_mat("IronWhite", (0.90, 0.90, 0.88, 1), rough=0.45, metal=0.3)           # stair / porch rails
    M['iron_black'] = _m.new_mat("IronBlack", (0.03, 0.03, 0.03, 1), rough=0.5, metal=0.6)            # pendant, Juliet rail, lanterns
    M['brick'] = _m.tiles("BrickPavers", (0.50, 0.24, 0.16, 1), grout=(0.55, 0.50, 0.44, 1), size=(0.2, 0.1), gap=0.008,
                          rough=0.85, variation=0.22, mottle=0.5, bump=0.5, offset=0.5)
    M['fence'] = _m.wood("FenceRedwood", light=(0.40, 0.25, 0.15, 1), dark=(0.24, 0.14, 0.08, 1), grain_axis='Z', rough=0.85, coat=0.0)
    M['fence_grey'] = _m.wood("FenceWeathered", light=(0.42, 0.36, 0.30, 1), dark=(0.26, 0.22, 0.18, 1), grain_axis='Z', rough=0.9, coat=0.0)
    M['garage_grey'] = _m.plaster("GaragePanel", base=(0.42, 0.44, 0.46, 1), rough=0.85, grain=0.1)
    M['shed_grey'] = _m.plaster("ShedSiding", base=(0.46, 0.48, 0.50, 1), rough=0.85, grain=0.1)
    M['shingle'] = _m.noise_mat("Shingle", (0.32, 0.26, 0.20, 1), (0.42, 0.36, 0.28, 1), scale=30, bump=0.4, rough=0.9)
    M['neighbour'] = _m.plaster("NeighbourTan", base=(0.55, 0.45, 0.32, 1), rough=0.9, grain=0.15)
    M['neighbour2'] = _m.plaster("NeighbourGrey", base=(0.50, 0.52, 0.55, 1), rough=0.9, grain=0.15)
    M['sidewalk'] = _m.tiles("Sidewalk", (0.58, 0.57, 0.54, 1), grout=(0.40, 0.39, 0.37, 1), size=(1.5, 1.5), gap=0.01, rough=0.9, variation=0.05, mottle=0.3, bump=0.2)
    # ---- interior finishes (photos 01-26)
    M['wall'] = _m.plaster("WallGrey", base=(0.58, 0.57, 0.55, 1), rough=0.85, grain=0.12)             # "agreeable grey" with the stucco texture
    M['wall_white'] = _m.plaster("WallWhite", base=(0.86, 0.85, 0.83, 1), rough=0.8, grain=0.05)
    M['ceiling'] = _m.plaster("CeilingWhite", base=(0.90, 0.89, 0.87, 1), rough=0.9, grain=0.15)        # textured ceilings
    M['carpet'] = _m.rug("CarpetGreige", (0.44, 0.41, 0.36, 1), (0.54, 0.51, 0.46, 1), scale=90)
    M['carpet_up'] = _m.rug("CarpetUpper", (0.40, 0.39, 0.36, 1), (0.50, 0.49, 0.46, 1), scale=90)
    M['maple'] = _m.wood_planks("MapleStrip", light=(0.80, 0.60, 0.36, 1), dark=(0.68, 0.48, 0.27, 1), plank=(1.8, 0.07), gap=0.002, rough=0.3, coat=0.35)
    M['maple_y'] = _m.wood_planks("MapleStripY", light=(0.80, 0.60, 0.36, 1), dark=(0.68, 0.48, 0.27, 1), plank=(1.8, 0.07), along='Y', gap=0.002, rough=0.3, coat=0.35)
    M['tile_entry'] = _m.tiles("EntryTile", (0.80, 0.70, 0.54, 1), grout=(0.62, 0.55, 0.45, 1), size=(0.3, 0.3), gap=0.005, rough=0.35, variation=0.06, mottle=0.3, bump=0.2, coat=0.2)
    M['tile_fire'] = _m.tiles("FireplaceTile", (0.82, 0.72, 0.56, 1), grout=(0.60, 0.52, 0.42, 1), size=(0.2, 0.2), gap=0.004, rough=0.25, variation=0.08, mottle=0.4, bump=0.2, coat=0.4, plane='YZ')
    M['tile_fire_h'] = _m.tiles("FireplaceTileH", (0.82, 0.72, 0.56, 1), grout=(0.60, 0.52, 0.42, 1), size=(0.2, 0.2), gap=0.004, rough=0.25, variation=0.08, mottle=0.4, bump=0.2, coat=0.4)
    M['tile_green'] = _m.tiles("KitchenGreenTile", (0.30, 0.46, 0.38, 1), grout=(0.55, 0.55, 0.50, 1), size=(0.15, 0.15), gap=0.005, rough=0.2, variation=0.12, mottle=0.4, bump=0.3, coat=0.6)
    M['tile_green_v'] = _m.tiles("KitchenGreenTileV", (0.30, 0.46, 0.38, 1), grout=(0.55, 0.55, 0.50, 1), size=(0.15, 0.15), gap=0.005, rough=0.2, variation=0.12, mottle=0.4, bump=0.3, coat=0.6, plane='XZ')
    M['tile_green_vy'] = _m.tiles("KitchenGreenTileVY", (0.30, 0.46, 0.38, 1), grout=(0.55, 0.55, 0.50, 1), size=(0.15, 0.15), gap=0.005, rough=0.2, variation=0.12, mottle=0.4, bump=0.3, coat=0.6, plane='YZ')
    M['tile_deco'] = _m.tiles("DecoBand", (0.62, 0.36, 0.14, 1), grout=(0.22, 0.34, 0.34, 1), size=(0.15, 0.15), gap=0.03, rough=0.3, variation=0.35, mottle=0.9, bump=0.2, coat=0.5, plane='XZ')
    M['tile_deco_y'] = _m.tiles("DecoBandY", (0.62, 0.36, 0.14, 1), grout=(0.22, 0.34, 0.34, 1), size=(0.15, 0.15), gap=0.03, rough=0.3, variation=0.35, mottle=0.9, bump=0.2, coat=0.5, plane='YZ')
    M['tile_white'] = _m.tiles("BathWhiteTile", (0.90, 0.90, 0.88, 1), grout=(0.70, 0.70, 0.68, 1), size=(0.15, 0.15), gap=0.004, rough=0.15, variation=0.03, mottle=0.1, bump=0.2, coat=0.6, plane='XZ')
    M['tile_white_y'] = _m.tiles("BathWhiteTileY", (0.90, 0.90, 0.88, 1), grout=(0.70, 0.70, 0.68, 1), size=(0.15, 0.15), gap=0.004, rough=0.15, variation=0.03, mottle=0.1, bump=0.2, coat=0.6, plane='YZ')
    M['tile_bath_floor'] = _m.tiles("BathFloorTile", (0.84, 0.76, 0.64, 1), grout=(0.62, 0.56, 0.48, 1), size=(0.3, 0.3), gap=0.004, rough=0.3, variation=0.05, mottle=0.3, bump=0.2, coat=0.3)
    M['tile_peach'] = _m.tiles("TilePeach", (0.86, 0.52, 0.36, 1), grout=(0.70, 0.66, 0.60, 1), size=(0.15, 0.15), gap=0.004, rough=0.2, variation=0.06, mottle=0.2, bump=0.2, coat=0.6, plane='XZ')
    M['tile_teal'] = _m.tiles("TileTeal", (0.20, 0.36, 0.38, 1), grout=(0.70, 0.66, 0.60, 1), size=(0.15, 0.15), gap=0.004, rough=0.2, variation=0.06, mottle=0.2, bump=0.2, coat=0.6, plane='XZ')
    M['granite'] = _m.noise_mat("GraniteSpeckle", (0.30, 0.24, 0.20, 1), (0.62, 0.56, 0.50, 1), scale=220, bump=0.05, detail=6, rough=0.12, spec=0.6)
    M['cabinet'] = _m.new_mat("CabinetWhite", (0.88, 0.88, 0.86, 1), rough=0.3, spec=0.5, coat=0.35)
    M['cabinet_cream'] = _m.new_mat("CabinetCream", (0.80, 0.70, 0.52, 1), rough=0.35, coat=0.3)
    M['appliance'] = _m.new_mat("ApplianceWhite", (0.90, 0.90, 0.88, 1), rough=0.3, coat=0.5)
    M['porcelain'] = _m.new_mat("Porcelain", (0.93, 0.93, 0.91, 1), rough=0.12, coat=0.8)
    M['chalk'] = _m.new_mat("SlateBoard", (0.06, 0.07, 0.07, 1), rough=0.7)
    # lawns: no mowing stripes (the striped library turf / blades read as painted bands from the patio)
    M['lawn'] = _m.turf("LawnPlain", c_dark=(0.08, 0.19, 0.05, 1), c_light=(0.17, 0.31, 0.09, 1))
    M['lawn_rear'] = _m.turf("LawnRearPlain", c_dark=(0.09, 0.21, 0.06, 1), c_light=(0.19, 0.34, 0.11, 1))
    M['grass'] = _m.grass_blade("GrassBladePlain", stripes=False)
    M['grass_rear'] = _m.grass_blade("GrassBladeRearPlain", stripes=False)
    M['glass_frost'] = _m.new_mat('WebsterEtchedGlass',(.82,.88,.86,1),rough=.44,transmission=.62,ior=1.45)
    from .refinements import refine_materials
    refine_materials(M)
    return M


def setup_scene(scene):
    from .refinements import setup_scene as setup
    setup(scene)


def make_titles():
    from .promo import make_titles as make
    make()


# ---------------------------------------------------------------- sky (dusk, sun low at the front-left = WSW)
SKY = dict(sun_dir=(-0.80, -0.45, 0.16), sun_energy=2.4, sun_color=(1.0, 0.80, 0.62), strength=0.55, sun_elevation=1.2)

# ---------------------------------------------------------------- cameras: name -> (location, target, lens mm)
CAMS = {
    'hero':     ((0.0, -15.5, 1.6), (0.0, 30.0, 1.6), 35),         # photo 00: straight on from the street, level, ~35 mm (solved from the facade widths)
    'front':    ((-7.5, -18.5, 2.2), (0.5, 4.0, 2.8), 26),         # 3/4 from the street (clear of the kerb tree), living block + entry
    'porch':    ((3.6, -4.5, 1.4), (3.4, 4.0, 1.8), 24),           # up the porch to the dining french doors
    'aerial':   ((-16.0, -24.0, 14.0), (0.0, 8.0, 2.0), 30),
    'rear':     ((-1.5, 29.0, 1.2), (0.0, 15.0, 3.0), 26),         # photo 29
    'patio':    ((1.2, 18.2, 1.1), (-2.0, 40.0, 0.5), 22),         # photo 27 (from the steps, shed + garage)
    'yard':     ((-3.0, 37.0, 1.4), (2.0, 18.0, 2.0), 24),         # photo 28
    'drive':    ((8.0, 14.0, 1.0), (5.0, -6.0, 2.5), 26),          # photo 30
    'deck':     ((-5.0, 11.0, Z_UP + 1.5), (-3.0, 8.5, Z_UP + 1.2), 22),
    # interiors
    'living':   ((-1.9, 5.2, 1.5), (-5.0, 1.5, 1.1), 18),           # photo 01 (fireplace between the windows)
    'living2':  ((-5.0, 5.4, 1.5), (-1.0, 0.8, 1.3), 18),           # photo 02 (window + arch to the entry)
    'entry':    ((-0.2, 2.4, 1.5), (0.4, 8.0, 1.6), 18),            # photo 15 (stair)
    'dining':   ((1.6, 6.6, 1.5), (4.5, 2.4, 1.3), 18),             # photo 04
    'dining2':  ((5.1, 2.5, 1.5), (1.5, 6.5, 1.4), 18),             # photo 03
    'kitchen':  ((3.4, 7.4, 1.5), (3.3, 12.5, 1.3), 18),            # photo 05
    'kitchen2': ((4.9, 11.0, 1.5), (3.5, 6.5, 1.3), 18),            # photo 06
    'family':   ((-0.9, 14.1, 1.5), (3.0, 17.0, 1.2), 18),          # photo 09
    'bed_a':    ((-2.3, 9.0, 1.5), (-5.2, 6.4, 1.1), 18),            # photo 10: toward the -X window with the front-wall closet on the left (clear of the open hall door)
    'bed_b':    ((-1.6, 13.4, 1.5), (-5.2, 16.8, 1.2), 18),         # photo 11
    'bath_a':   ((-3.0, 12.2, 1.4), (-5.4, 10.4, 1.0), 18),         # photo 13
    'prim':     ((3.0, 6.9, Z_UP + 1.5), (2.6, 13.6, Z_UP + 1.2), 18),   # photo 21: from the front of the suite toward the bath opening, hall door left, +X window right
    'pbath':    ((3.55, 12.7, Z_UP + 1.5), (4.3, 14.8, Z_UP + 1.15), 18), # photo 23 (clear of the open door leaf at x 3.0)
    'bed2':     ((-1.25, 11.25, Z_UP + 1.5), (-3.2, 8.3, Z_UP + 1.15), 18), # photo 16 (from the door; the bed now sits on the +X wall)
    'bed3':     ((0.3, 14.7, Z_UP + 1.5), (-2.8, 16.9, Z_UP + 1.2), 18), # photo 20
}
# Photo-aligned review views: each image 00–30 has a counterpart.
CAMS.update({
    'drive': ((8.35,14.5,1.35),(5.3,9.75,1.9),22),
    'rear': ((-4,30,1.15),(-.8,17.1,2.4),26),
    'yard': ((-4,34,1.25),(3,18,2.2),28),
    'patio': ((1.2,19.1,1.10),(3.2,33.0,.85),18),
    'living': ((-1.75,1.75,1.60),(-4.80,3.45,1.40),18),
    'living2': ((-3.82,5.08,1.5),(-2.75,.35,1.4),18),
    'kitchen2': ((2.96,10.78,1.5),(4.60,8.10,1.35),18),
    'kitchen3': ((4.9,7.45,1.5),(2.25,9.70,1.3),18),
    'laundry': ((3.80,12.02,1.55),(4.65,13.50,1.15),18),
    'family': ((.15,14.1,1.5),(2.20,17.25,1.35),18),
    'bed_b': ((-.85,13.3,1.5),(-4.7,15.85,1.3),18),
    'bed_b2': ((-3.8,13.3,1.5),(-2.3,16.35,1.3),18),
    'bath_a': ((-3.0,10.4,1.4),(-4.5,12.1,1.2),18),
    'bath_a2': ((-3.2,12.0,1.45),(-4.8,10.45,1.3),18),
    'powder': ((-4.30,5.60,1.50),(-5.12,4.90,1.30),16),
    'prim_alt': ((2.3,8.28,4.55),(5.0,9.84,4.40),14),
    'prim_front': ((2.1,11.65,4.6),(5.05,8.9,4.35),18),
    'leaded_detail': ((-1.7,3.0,4.90),(-.5,6.0,4.68),42),
    'dining2': ((1.65,2.5,1.5),(4.4,6.0,1.4),18),
    'bed3': ((.30,15.30,4.55),(-2.55,14.90,4.35),18),
    'bed3b': ((-2.7,12.4,4.55),(-.6,16.5,4.3),18),
    'hbath': ((1.16,12.72,4.58),(1.95,14.18,4.30),16),
    'pbath2': ((4.35,13.0,4.65),(2.95,14.60,4.25),20),
    'wic2': ((-.67,6.82,4.55),(-3.18,6.80,4.35),20),
    'wic2b': ((-3.0,6.8,4.55),(-.60,7.1,4.3),18),
    'bed2b': ((-2.8,9.9,4.55),(-.5,8.55,4.35),18),
})
EXT = ['hero', 'front', 'porch', 'aerial', 'rear', 'patio', 'yard', 'drive', 'deck', 'leaded_detail']
EXPOSURE = {'drive':1.0,'pbath':.1,'pbath2':.2,'hbath':.4,'wic2':.5,'wic2b':.5,'porch': 0.5, 'deck': 0.5, 'rear': 0.7, 'patio': 0.7, 'yard': 0.7}
EXPOSURE_DEFAULT = {'ext': 0.6, 'int': 0.2}
DOF = {}
DOF_DEFAULT = {'ext': 11.0, 'int': 4.5}
PHOTO_PAIRS = [('hero',0),('living',1),('living2',2),('dining2',3),('dining',4),
               ('kitchen',5),('kitchen2',6),('kitchen3',7),('laundry',8),('family',9),
               ('bed_a',10),('bed_b',11),('bath_a2',12),('bath_a',13),('prim_alt',14),
               ('entry',15),('bed2',16),('wic2',17),('bed3b',18),('hbath',19),
               ('prim_front',20),('prim',21),('leaded_detail',22),('pbath',23),('pbath2',24),
               ('powder',25),('bed2b',26),('patio',27),('yard',28),('rear',29),('drive',30),
               ('front',99),('aerial',99),('deck',99)]

# ---------------------------------------------------------------- polish: hair grass on the lawns
def _curb_y(x):
    """Centre line of the curved brick planter curb (mirror of site._curb_y): y -1.0 at the walk, -1.8 at the ends."""
    wx0, wx1 = FRONT_WALK_X
    t = (x - wx0) / (LOT[0] - wx0) if x < wx0 else (x - wx1) / (DRIVE_X[0] - wx1)
    t = max(0.0, min(1.0, t))
    return -1.0 - 0.8 * t * t


def _curb_holes(step=0.5):
    """No hair in the bed behind the curb: stepped rectangles from the curb line (minus its width) to the house."""
    out, x = [], LAWN_FRONT[0]
    while x < LAWN_FRONT[1]:
        xb = min(x + step, LAWN_FRONT[1])
        out.append((x, xb, _curb_y((x + xb) / 2) - 0.2, 0.5))
        x = xb
    return out


GRASS = [
    dict(name="Grass_Front", rect=(LAWN_FRONT[0] + 0.025, LAWN_FRONT[1] - 0.025, LAWN_FRONT[2] + 0.025, -0.95), z=Z_GRADE + 0.002,
         holes=[(FRONT_WALK_X[0] - 0.015, FRONT_WALK_X[1] + 0.015, LAWN_FRONT[2], LAWN_FRONT[3])] + _curb_holes(0.12), cell=0.10, padding=0.0, mat='grass', count=42000, length=0.034, children=11, seed=3),
    dict(name="Grass_Rear", rect=(LAWN_REAR[0] + 0.15, LAWN_REAR[1] - 0.15, LAWN_REAR[2] + 0.15, LAWN_REAR[3] - 0.15), z=Z_GRADE + 0.004,
         holes=[(PATIO_PATH[0] - 0.1, PATIO_PATH[1], PATIO_PATH[2], PATIO_PATH[3] + 0.1)], cell=0.2, padding=0.02, mat='grass_rear', count=60000, length=0.04, children=9, seed=5),
]

# ---------------------------------------------------------------- film: the front door swings open (archviz.film.open_doors)
DOORS = dict(static=[], entry=("Entry_Door", ENTRY_HINGE, 100))
PROBE_WALLS = [
    ("living|entry x=-1.3", 'X', -1.3, (0.3, 5.7), (0.2, 2.6)),
    ("entry|dining x=1.1", 'X', 1.1, (2.1, 6.9), (0.2, 2.6)),
    ("dining|kitchen y=7.0", 'Y', 7.0, (1.2, 5.5), (0.2, 2.6)),
    ("kitchen|hall2 y=11.2", 'Y', 11.2, (2.1, 5.5), (0.2, 2.6)),
    ("family rear y=17.2", 'Y', 17.2, (-1.3, 3.3), (0.2, 2.6)),
    ("deck slider x=-3.3", 'X', -3.3, (7.6, 11.5), (3.2, 5.3)),
    ("bed2|hall x=-0.3", 'X', -0.3, (7.6, 11.5), (3.2, 5.3)),
    ("hall|prim x=1.0", 'X', 1.0, (10.5, 13.4), (3.2, 5.3)),
    ("prim front y=6.1", 'Y', 6.1, (1.05, 4.55), (3.2, 5.3)),
]
