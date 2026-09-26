"""1836 Webster St, Palo Alto (Old Palo Alto) — THE PLAN (bpy-free): site reading, levels, rooms, walls, openings.

Listing (MLS ML82053646, Compass): 1926 Spanish-revival stucco house, 5 bed / 3.5 bath, 2,831 sq ft on a 10,000 sq ft
lot.  Sold empty; the film stages it.  The street facade comes from photo 00 (added later); before that it was inferred
from photos 02 (living room looking out at the street), 04 (dining french doors onto the walled porch) and 30
(driveway side).  Photo 31 is the agent's floor plan (measurements in feet), the source of the room sizes.

Coordinates (metres): X = left(-)/right(+) as seen FROM THE STREET, Y = street(-)/rear(+), Z up.
Main floor = Z 0; the site grade is 0.55 m lower (3 steps up to the porch, 4 down to the rear patio).

SITE READING
  * lot ~17 x 54 m: front property line y = -7.0 (sidewalk beyond), rear fence y = 47.5, side fences x = -6.75 / 10.5
  * house front wall at y = 0, 11.5 m wide (x -5.75..5.75) at the front, the rear part narrower (to x 3.5)
  * driveway along the RIGHT (+X) side (photo 30: looking toward the street with the house on the right) to the
    detached flat-roofed GARAGE (17 x 23.5 ft) that sits behind the house on the +X side with its long axis along Y
    (photos 27/28/29: the garage's long wall bounds the brick patio, a wood gate closes the gap to the house)
  * WORKSHOP/SHED (12 x 23.5 ft, gable roof, door facing the house) at the far rear on the -X side (photos 09/27/28)
  * brick PATIO behind the family room with 4 brick steps + white metal rail to the french doors (29), lawn beyond
  * oleander hedge (white flowers) along the +X fence behind the garage; tall redwoods / pines behind the rear
    fence at -X; a grey gabled neighbour beyond the +X fence; a tan stucco neighbour at -X (photo 16)
  * ROOFS: continuous clay-tile planes across the lower front, with a diagonal front gable edge and a level
    porch eave; the surfaces rise toward the upper-storey wall and drain toward exterior eaves. The upper
    main gable joins a fully tiled, low-hipped +X wing. The hidden pitches and joins are inferred from the
    front/side/rear photos, not measured. Side and rear low roofs retain their membrane finish and drain
    toward flush exterior edges; no freestanding roof-edge parapets are modeled there. The actual side
    terrace enclosure and front porch wall remain, as shown in photos 16 and 00.
  * STREET FACADE (photo 00, added 2026-09-04 - straight on from the street): the living-room block at the left with the
    wide triple window (fixed centre with a 6-lite transom, narrow double-hungs, board shutters) and three vent dots at
    its upper left; a gable wall terminating under the tiled roof; the ENTRY tower in the middle at the street plane: a pointed (Tudor) arch
    recess with a plum door (small leaded lite, brass knocker), "1836" beside it, four brick steps with white pipe rails
    on both sides; above the entry a COMPLETE tiled roof with a straight diagonal front edge falling to the right;
    its tiles extend back to the upper-storey wall, without a recessed flat-roof tray; the walled PORCH only in front of the
    dining room (stucco parapet 1.05 m + a white iron picket rail with spear finials); french doors + two double-hungs
    behind it.  Upper floor: one level clay-tile cornice + white fascia across the whole width (a front hip on the
    gable block and a fully tiled low-hipped +X wing); windows left->right: a
    small shuttered double-hung (wic2), two tiny diamond-leaded squares with mini shutters (over the stair well), and
    the primary suite's shuttered triple (wide fixed centre + narrow double-hungs).  NO balcony, no french windows.
    Chimney: an interior breast at the living room's front-left corner rising just inside the block's left edge.
    Site: brick walk + steps, a curved low brick planter curb along the house, magnolia over the sidewalk at -X,
    white oleander by the driveway at +X, board fences with gates both sides.
  * MAIN LEVEL (photo 31, feet): living 14x18 | entry + stair | dining 13x16 (porch in front); behind: bedroom
    14x13 + half bath + bath | hall | kitchen 11.5x13 + laundry; rear: bedroom 15x12 | family 11.5x12.5
  * UPPER LEVEL: primary suite 13x19 (front, +X) + WIC + bath (granite vanity, 23/24); bedroom 9x13 (middle -X,
    slider to the deck, 16/26); bedroom 13x16.5 (rear, two paired window units on the rear wall, 18/20); hall bath (19)
  * INTERIOR CHARACTER: arched cased openings (02/15), 9 ft ceilings, crown moulding, white six-over-one double-hung
    sash windows, grey walls / white trim, carpet in the living room + bedrooms upstairs, honey maple strip floor
    in the dining/kitchen/family/main bedrooms, cream 12" tile in the entry, straight enclosed carpeted stair
    with a mid landing and a white wrought-iron rail, tiled fireplace with a raised hearth + wood mantel (01),
    white shaker kitchen with green tile counters + ochre/teal deco backsplash + a greenhouse window (05-07),
    black geometric cage pendant in the dining room (03/04)

FILM ROUTE (shots.py): aerial over the street -> porch -> the front door swings open -> entry -> living room ->
back through the arches -> dining -> kitchen -> arch -> family room -> out the (open) french doors -> crane over
the patio / lawn (garage, shed, redwoods) -> over the roof to the deck -> in through the (open) slider -> bedroom
-> upper hall -> primary suite -> a slow symmetrical bed reveal.  Every
opening on that route is built OPEN except the front door (archviz.film.open_doors animates it).
"""
import math

FT = 0.3048

# ---------------------------------------------------------------- levels
Z_GRADE = -0.55            # site grade (lawns, driveway, patio)
Z_MAIN = 0.0               # main floor
Z_MC = 2.75                # main ceiling
Z_UP = 3.05                # upper floor (top of the 0.30 slab)
Z_UPC = 5.45               # upper ceiling
Z_EAVE = 5.85              # top of the upper block walls (gable eave / coping)
Z_RIDGE = 6.70             # rear gable rise inferred from photos 28/29; front hip maintains the level cornice
Z_ROOF1 = 3.05             # single-storey roof deck (same as the upper floor)
Z_PAR = 3.62              # legacy name: measured height on the diagonal front roof edge at x=-2.85
Z_WING = 5.85              # +X wing wall top = the front eave line (photo 00: one level tile cornice across the whole upper front)
Z_WING_HI = 5.85           # = Z_EAVE: the shed roof meets the gable roof's eave line at x = WINGX0
WT = 0.25                  # exterior wall thickness (0.12 stucco skin + 0.13 painted inner skin)
WI = 0.15                  # interior partition thickness
T = 0.012                  # glass thickness
RISER = 3.05 / 17          # 17 risers to the upper floor
TREAD = 0.2625

# Rear offsets read together from photos 28/29 and the measured floor plan.
BED_REAR, FAMILY_REAR = 16.55, 17.95
FIREPLACE_FACE, FIREPLACE_CENTRE = -5.48, 2.95

# ---------------------------------------------------------------- lot / site
LOT = (-6.75, 10.5, -7.0, 47.5)                 # x0, x1, y0, y1 (fences on x0 / x1 / y1; the front line is open)
SIDEWALK = (-7.0, -8.5)                         # y range of the concrete sidewalk (full lot width)
PARKWAY = (-8.5, -9.4)                          # brick-paved strip to the curb
STREET = (-9.4, -19.0)                          # asphalt to the far kerb
DRIVE_X = (5.9, 9.4)                            # driveway strip (y from the sidewalk to the garage)
FRONT_WALK_X = (-0.9, 0.35)                     # brick walk from the sidewalk to the entry steps (photo 00), centred on the front door
GARAGE = (5.0, 10.2, 17.6, 24.8)                # x0, x1, y0, y1 (flat roof, top z 2.45 above grade -> 1.9)
GARAGE_H = 2.5                                  # wall height above grade
SHED = (-6.2, -2.5, 40.0, 47.2)                 # gable roof, ridge along Y, door + windows on the -Y end
SHED_H, SHED_RIDGE = 2.3, 3.4                   # above grade
PATIO = (-5.8, 5.0, BED_REAR + WT, 21.8)                # brick patio behind the family room (top z = Z_GRADE)
PATIO_PATH = (3.6, 5.0, 21.8, 26.0)             # brick path along the garage wall
GATE = (3.5, 5.0, FAMILY_REAR + WT)                         # x0, x1, y: wood gate between the family room corner and the garage
REAR_STEPS = (0.2, 2.4, FAMILY_REAR + WT, FAMILY_REAR + WT + 1.2)           # 3 brick risers from the patio to the family-room doors (rail on +X side)
LAWN_REAR = (-6.5, 4.9, 22.0, 39.5)             # main rear lawn (the shed sits in its own bed beyond)
LAWN_FRONT = (-6.5, 5.6, -6.8, -0.3)            # front lawn (minus the walk)
OLEANDER = (10.0, 24.8, 34.0)                   # x, y0, y1 along the +X fence behind the garage
SHRUB_BEDS = [(3.2, 18.9), (-1.0, 17.6)]        # 0.7 m mulch cut-outs in the patio bricks for the two rose shrubs (photo 29)
FRONT_TREE = (-4.3, -4.6)                       # small ornamental tree on the front lawn (its crown must clear the living window)
STREET_TREES = [(-8.6, -9.0), (8.8, -9.0)]      # big kerb-side trees (parkway)

# ---------------------------------------------------------------- main level: room volumes (x0, x1, y0, y1, z_floor, z_ceiling)
ROOMS = {
    'living':    (-5.5, -1.4, 0.25, 5.75, 0.0, Z_MC),
    'entry':     (-1.25, 1.05, 0.25, 5.0, 0.0, Z_MC),      # the entry runs to the street plane: its arched front door is at y 0 (photo 00);
                                                           # its front part y 0.25..ENTRY_VEST_Y1 has a dropped ceiling at ENTRY_VEST_ZC (under the rake)
    'alcove':    (-4.0, -1.5, 5.42, 5.75, 0.0, 2.40),      # living-room built-in bay on the -X wall (photo 01: shelves + chalkboard behind a cased opening)
    'stair':     (-0.15, 0.9, 5.0, 10.5, 0.0, Z_UPC),      # the enclosed stair well (open through the upper slab)
    'hall':      (-1.25, -0.3, 5.0, 12.75, 0.0, Z_MC),
    'dining':    (1.2, 5.5, 2.05, 6.95, 0.0, Z_MC),
    'kitchen':   (1.5, 5.5, 7.1, 11.15, 0.0, Z_MC),
    'pantry':    (1.2, 1.35, 7.1, 10.5, 0.0, Z_MC),       # inferred closed service void behind recessed appliances
    'mid':       (-0.15, 1.95, 10.5, 13.6, 0.0, Z_MC),      # closed: basement stair + closets behind the stair top
    'laundry':   (3.5, 5.5, 11.3, 13.6, 0.0, Z_MC),
    'hall2':     (2.1, 3.35, 11.3, 13.6, 0.0, Z_MC),        # kitchen arch -> family room
    'family':    (-0.15, 3.25, 13.75, FAMILY_REAR, 0.0, Z_MC),
    'bed_a':     (-5.5, -1.4, 5.9, 9.9, 0.0, Z_MC),         # bedroom 14x13 (photo 10)
    'half':      (-5.5, -4.2, 4.60, 5.75, 0.0, Z_MC),     # half bath (photo 12)
    'bath_a':    (-5.5, -2.85, 10.05, 12.35, 0.0, Z_MC),    # bath with tub (photo 13); vestibule below
    'bath_a_v':  (-2.85, -1.4, 10.05, 12.75, 0.0, Z_MC),
    'bed_b':     (-5.5, -0.3, 12.9, BED_REAR, 0.0, Z_MC),       # bedroom 15x12 (photo 11)
    # upper level
    'up_hall':   (-0.15, 0.9, 10.5, 13.4, Z_UP, Z_UPC),
    'prim':      (1.05, 5.3, 6.25, 12.4, Z_UP, Z_UPC),     # primary suite (its WIC is carved out of the front-left)
    'wic':       (1.05, 2.3, 6.25, 8.05, Z_UP, Z_UPC),
    'prim_bath': (2.7, 5.3, 12.55, 14.95, Z_UP, Z_UPC),
    'hall_bath': (1.05, 2.35, 12.55, 14.95, Z_UP, Z_UPC),
    'closet3':   (1.05, 1.40, 15.20, BED_REAR, Z_UP, Z_UPC),
    'bed3':      (-3.15, 0.9, 13.55, BED_REAR, Z_UP, Z_UPC),    # rear bedroom 13x16.5 (L: also the strip below)
    'bed3_s':    (-3.15, -0.15, 11.6, 13.55, Z_UP, Z_UPC),
    'bed2':      (-3.15, -0.5, 7.6, 11.45, Z_UP, Z_UPC),    # bedroom 9x13 with the slider to the deck
    'wic2':      (-3.15, -0.5, 6.25, 7.45, Z_UP, Z_UPC),
    'deck':      (-5.5, -3.65, 7.6, 11.45, Z_UP, Z_UP + 1.0),
}
# rooms grouped by the interior module that furnishes them
FRONT_ROOMS = ['living', 'entry', 'stair', 'dining']
BACK_ROOMS = ['hall', 'kitchen', 'pantry', 'mid', 'laundry', 'hall2', 'family', 'bed_a', 'half', 'bath_a', 'bath_a_v', 'bed_b']
UPPER_ROOMS = ['up_hall', 'prim', 'wic', 'prim_bath', 'hall_bath', 'closet3', 'bed3', 'bed3_s', 'bed2', 'wic2', 'deck']

# ---------------------------------------------------------------- stair (straight, enclosed, mid landing; photo 15)
STAIR_X0, STAIR_X1 = -0.15, 0.9
STAIR_F1 = (5.0, 7.1)              # flight 1: 8 risers rising +Y, top tread z = 8 * RISER
STAIR_LAND = (7.1, 8.1)            # landing at z = 8 * RISER
STAIR_F2 = (8.1, 10.5)             # flight 2: 9 risers to Z_UP at y = 10.5
STAIR_WELL = (STAIR_X0, STAIR_X1, 6.3, 10.5)     # hole in the upper slab

# ---------------------------------------------------------------- upper block outline
UPX0, UPX1 = -3.4, 1.65             # gable block (exterior faces), ridge at x = UP_RIDGE_X
UPY0, UPY1 = 6.0, BED_REAR + WT            # its front / rear faces (rear flush with the main rear wall)
UP_RIDGE_X = (UPX0 + UPX1) / 2
WINGX0, WINGX1 = UPX1, 5.55         # +X wing (primary suite; flat roof with a tile cornice on 3 sides), y WINGY0..WINGY1 (photo 00: its front eave is level with the gable block's)
WINGY0, WINGY1 = 6.0, 15.2
CHIMNEY = (-6.08, -5.76, 2.3, 3.6, 5.2)         # external flue behind the flush west-wall fireplace, photo 01
DECK_PAR = 1.0                                   # deck parapet height above Z_UP
# Roof revision: the diagonal front line is a roof edge, not a parapet cap.
# Its continuation under the tree canopy and the hidden pitches are inferred.
RAKE = ((-2.85, Z_PAR), (1.2, 2.58))
ENTRY_VEST_Y1, ENTRY_VEST_ZC = 1.85, 2.4
PENT_Y0, PENT_Y1 = 1.25, 1.85
PENT_EAVE_Z, PENT_TOP_Z = 2.74, 3.08
PENT_X0 = 1.2
FRONT_ROOF_FRONT_Y = -.02
FRONT_ROOF_JOIN_Y = UPY0
FRONT_ROOF_JOIN_Z = 3.54
FRONT_ROOF_THICKNESS = .055
FRONT_ROOF_BACK_RISE = .015


# ---------------------------------------------------------------- walls
# along='X': a = x (a0..a1), b = y (b0..b1);  along='Y': a = y, b = x.   kind: 'ext' (stucco outside, paint inside),
# 'int' (paint), 'par' (parapet: stucco both sides), 'up' (upper-level exterior)
def W(along, a0, a1, b0, b1, z0, z1, kind):
    return dict(along=along, a0=a0, a1=a1, b0=b0, b1=b1, z0=z0, z1=z1, kind=kind)


WALLS = [
    # ---- main level exterior (z 0 .. Z_MC + 0.30 slab: walls run to the roof deck; parapets above are separate)
    W('X', -5.75, -1.25, 0.0, 0.25, Z_GRADE, Z_ROOF1, 'ext'),          # living front
    W('X', -1.25, 1.2, 0.0, 0.25, Z_GRADE, Z_ROOF1, 'ext'),            # entry front at the street plane (pointed-arch doorway; swoop parapet above: exterior.py)
    W('Y', 0.25, 2.05, 1.05, 1.2, Z_GRADE, Z_ROOF1, 'ext'),            # entry +X wall facing the walled porch
    W('X', 1.2, 5.75, 1.8, 2.05, Z_GRADE, Z_ROOF1, 'ext'),             # dining front (porch side)
    W('Y', 0.25, 13.6, -5.75, -5.5, Z_GRADE, Z_ROOF1, 'ext'),          # -X wall, front part
    W('Y', 13.6, BED_REAR + WT, -5.75, -5.5, Z_GRADE, Z_ROOF1, 'ext'),         # -X wall, rear bedroom
    W('X', -5.75, -0.30, BED_REAR, BED_REAR + WT, Z_GRADE, Z_ROOF1, 'ext'),
    W('X', -0.30, 3.5, FAMILY_REAR, FAMILY_REAR + WT, Z_GRADE, Z_ROOF1, 'ext'),
    W('Y', BED_REAR + WT, FAMILY_REAR + WT, -0.40, -0.15, Z_GRADE, Z_ROOF1, 'ext'),          # rear wall
    W('Y', 13.6, FAMILY_REAR + WT, 3.25, 3.5, Z_GRADE, Z_ROOF1, 'ext'),           # family room +X wall
    W('X', 3.5, 5.75, 13.6, 13.85, Z_GRADE, Z_ROOF1, 'ext'),           # laundry rear wall (the step-in)
    W('Y',2.05,11.45,5.5,5.75,Z_GRADE,Z_ROOF1,'ext'),
    W('Y',12.50,13.85,5.5,5.75,Z_GRADE,Z_ROOF1,'ext'),
    W('X',4.65,5.75,11.15,11.45,Z_GRADE,Z_ROOF1,'ext'),
    W('Y',11.45,12.50,4.40,4.65,Z_GRADE,Z_ROOF1,'ext'),
    W('X',4.4,5.75,12.50,12.65,Z_GRADE,Z_ROOF1,'ext'),           # +X wall: dining, kitchen, laundry
    W('X', -5.75, -5.5, 0.0, 0.25, Z_GRADE, Z_ROOF1, 'ext'),           # (corner fill)
    # ---- main level partitions
    W('Y', 0.25, 5.75, -1.4, -1.25, 0.0, Z_MC, 'int'),                 # living | entry / hall (arch)
    W('X', -5.5, -1.4, 5.75, 5.9, 0.0, Z_MC, 'int'),                   # living | bed_a
    W('Y', 5.9, 12.75, -1.4, -1.25, 0.0, Z_MC, 'int'),                  # bed_a / baths / bed_b | hall / family
    W('X', -5.5, -1.4, 9.9, 10.05, 0.0, Z_MC, 'int'),                  # bed_a | baths
    W('Y',10.05,12.75,-2.85,-2.70,0.,Z_MC,'int'),
    W('X', -5.5, -0.3, 12.75, 12.9, 0.0, Z_MC, 'int'),
    W('Y', 12.9, BED_REAR + WT, -0.30, -0.15, 0., Z_MC, 'int'),
    W('X', -5.5, -4.05, 4.45, 4.60, 0., Z_MC, 'int'),
    W('Y', 4.60, 5.75, -4.20, -4.05, 0., Z_MC, 'int'),                 # baths | bed_b
    W('Y', 2.05, 6.95, 1.05, 1.2, 0.0, Z_MC, 'int'),                   # entry | dining (arch)
    W('Y', 5.0, 10.5, 0.9, 1.2, 0.0, Z_MC, 'int'),                     # stair | dining / pantry (thick)
    W('Y', 5.0, 10.5, -0.3, -0.15, 0.0, Z_MC, 'int'),                  # hall | stair
    W('Y', 10.5, 12.90, -0.3, -0.15, 0.0, Z_MC, 'int'),                 # hall | mid
    W('X', 1.2, 5.5, 6.95, 7.1, 0.0, Z_MC, 'int'),                     # dining | kitchen / pantry (door)
    W('Y', 7.1, 10.5, 1.35, 1.5, 0.0, Z_MC, 'int'),                   # recessed kitchen backing wall
    W('Y', 10.5, 11.15, 1.35, 1.5, 0.0, Z_MC, 'int'),
    W('Y', 11.3, 13.6, 1.95, 2.1, 0.0, Z_MC, 'int'),                  # original hall2 width retained
    W('X', 1.35, 4.65, 11.15, 11.3, 0.0, Z_MC, 'int'),                 # return from the recess; original openings retained
    W('Y', 11.3, 13.6, 3.35, 3.5, 0.0, Z_MC, 'int'),                   # hall2 | laundry
    W('X', -0.3, 2.1, 13.6, 13.75, 0.0, Z_MC, 'int'),                  # mid | family (the hall and hall2 stay open)
    W('X', -0.15, 1.35, 10.5, 10.65, 0.0, Z_MC, 'int'),                # stair top | mid, ends at new kitchen wall
    W('X', 1.2, 1.35, 10.5, 10.65, 0.0, Z_MC, 'int'),                  # service void end (merged look)
    # Only the photographed terrace enclosure remains above a roof surface.
    # All other roof-edge walls finish underneath the roof planes in exterior.py.
    W('Y', 7.6, 11.45, -5.75, -5.5, Z_ROOF1, Z_UP + DECK_PAR, 'par'),
    W('X', -5.75, -3.4, 7.45, 7.6, Z_ROOF1, Z_UP + DECK_PAR, 'par'),
    W('X', -5.75, -3.4, 11.45, 11.6, Z_ROOF1, Z_UP + DECK_PAR, 'par'),
    # ---- upper level exterior (gable block + wing); z from the roof deck to the eave / wing top
    W('X', UPX0, UPX1, UPY0, UPY0 + WT, Z_ROOF1, Z_EAVE, 'up'),        # gable block front wall (gable triangle above: exterior.py)
    W('X', WINGX0, WINGX1, WINGY0, WINGY0 + WT, Z_ROOF1, Z_WING, 'up'),  # wing front wall (sloped top wedge to Z_WING_HI: exterior.py)
    W('Y', UPY0, UPY1, UPX0, UPX0 + WT, Z_ROOF1, Z_EAVE, 'up'),        # -X wall
    W('X', UPX0, UPX1, UPY1 - WT, UPY1, Z_ROOF1, Z_EAVE, 'up'),        # rear wall (gable end)
    W('Y', WINGY1, UPY1, UPX1 - WT, UPX1, Z_ROOF1, Z_EAVE, 'up'),      # gable block +X wall behind the wing
    W('Y', WINGY0, WINGY1, WINGX1 - WT, WINGX1, Z_ROOF1, Z_WING, 'up'),  # wing +X wall
    W('X', WINGX0, WINGX1, WINGY1 - WT, WINGY1, Z_ROOF1, Z_WING, 'up'),  # wing rear wall (the set-back box, photo 29)
    # ---- upper partitions
    W('Y', 6.25, 10.5, 0.9, 1.05, Z_UP, Z_UPC, 'int'),                 # stair well | prim / wic
    W('Y', 10.5, 13.4, 0.9, 1.05, Z_UP, Z_UPC, 'int'),                 # up_hall | prim / hall_bath (doors)
    W('Y', 13.4, BED_REAR, 0.9, 1.05, Z_UP, Z_UPC, 'int'),                 # bed3 | hall_bath / closet3 (sliding doors)
    W('Y', 11.6, 13.55, -0.3, -0.15, Z_UP, Z_UPC, 'int'),              # up_hall | bed3 strip
    W('Y', 6.25, 11.6, -0.5, -0.15, Z_UP, Z_UPC, 'int'),               # wic2 / bed2 | stair well / up_hall (door)
    W('X', -3.15, -0.5, 7.45, 7.6, Z_UP, Z_UPC, 'int'),                # wic2 | bed2 (door)
    W('X', -3.15, -0.15, 11.45, 11.6, Z_UP, Z_UPC, 'int'),             # bed2 | bed3 strip
    W('X', -0.15, 0.9, 13.4, 13.55, Z_UP, Z_UPC, 'int'),               # up_hall end | bed3 (door)
    W('Y', 6.25, 8.05, 2.3, 2.45, Z_UP, Z_UPC, 'int'),                 # wic | prim (door)
    W('X', 1.05, 2.3, 8.05, 8.2, Z_UP, Z_UPC, 'int'),                  # wic | prim
    W('X', 1.05, WINGX1 - WT, 12.4, 12.55, Z_UP, Z_UPC, 'int'),               # prim | baths (door to prim_bath)
    W('Y', 12.55, WINGY1, 2.35, 2.7, Z_UP, Z_UPC, 'int'),              # hall_bath / closet3 | prim_bath (the gable +X wall continues beyond)
    W('X', 1.05, WINGX0, 14.95, 15.20, Z_UP, Z_UPC, 'int'),               # hall_bath | closet3
    # ---- walled porch in front of the dining room only (photo 00): stucco parapet 1.05 m over the porch floor + an iron picket rail (exterior.py)
    W('X', 1.2, 5.75, 0.0, 0.25, Z_GRADE, 1.05, 'par'),
    W('Y', 0.25, 1.8, 5.5, 5.75, Z_GRADE, 1.05, 'par'),
]
PORCH = (1.2, 5.5, 0.25, 1.8)              # walled porch floor (z 0, cream tile) in front of the dining room; reached from its french doors only
PORCH_STEPS = (-0.85, 0.3, -1.1, 0.0)      # ENTRY steps: 4 brick risers from the walk up to the arched front door, white pipe rails both sides (photo 00)
WALLS = [w for w in WALLS if w['b1'] - w['b0'] > 1e-6 and w['a1'] - w['a0'] > 1e-6 and w['z1'] - w['z0'] > 1e-6]


# ---------------------------------------------------------------- openings
# kind: 'hole' (plain hole, no unit), 'dh' double-hung sash window (grid = (cols, rows) of lites per sash), 'dh3' triple (mullions), 'fixed',
# 'french' (2 leaves, 'open' -> both swung inward 100 deg), 'slider' (2 panels, open half = a1-side),
# 'door' (leaf; 'open' angle), 'arch' (cased arched opening, no door), 'cased' (rectangular cased opening),
# 'garden' (projecting greenhouse window), 'leaded' (fixed diamond-leaded), 'sliding_cl' (closet sliders)
# along/b as WALLS (the wall plane it sits in - matched by exterior.py); a0..a1, z0..z1 = the hole.
def O(name, along, a0, a1, b, z0, z1, kind, **kw):
    d = dict(name=name, along=along, a0=a0, a1=a1, b=b, z0=z0, z1=z1, kind=kind)
    d.update(kw)
    return d


OPENINGS = [
    # ---- living room
    O('LivFront', 'X', -4.9, -2.0, 0.0, 0.5, 2.35, 'dh3', mullions=(-4.1, -2.8), grid=(3, 2)),   # photo 00: sill 0.5, head 2.35 (measured)
    O('LivWestLarge', 'Y', 0.65, 1.95, -5.75, 0.65, 2.3, 'dh', grid=(3, 2)),
    O('LivW1', 'Y', 3.80, 4.40, -5.75, 0.95, 2.2, 'dh', grid=(2, 2)),
    O('Firebox', 'Y', 2.575, 3.325, -5.75, .20, .90, 'hole'),
    O('PowderW', 'Y', 5.00, 5.58, -5.75, 1.1, 2.2, 'fixed', frost=True),             # small window right of the fireplace (photo 01)
    O('ArchLiv', 'Y', 2.35, 3.65, -1.4, 0.0, 2.15, 'arch', spring=1.6),
    # ---- entry / dining
    O('FrontDoor', 'X', -0.83, 0.27, 0.0, 0.0, 2.1, 'door', hinge='a0', open=0.0, style='front', arch='tudor', recess=0.3),   # plum door in a pointed-arch recess at the street plane (photo 00)
    O('ArchDin', 'Y', 2.35, 3.65, 1.05, 0.0, 2.15, 'arch', spring=1.6),
    O('DinFrench', 'X', 2.55, 4.15, 1.8, 0.0, 2.25, 'french', open=0.0, lites=(3, 5)),
    O('DinW1', 'X', 1.65, 2.25, 1.8, 0.15, 2.25, 'fixed_lites', grid=(2, 5)),
    O('DinW2', 'X', 4.45, 5.05, 1.8, 0.15, 2.25, 'fixed_lites', grid=(2, 5)),
    O('DinWE', 'Y', 4.05, 4.95, 5.5, 0.85, 2.25, 'dh', grid=(3, 2)),
    O('DinWN','X',4.42,5.08,6.95,.85,2.25,'dh',grid=(3,2)),
    O('DoorKit', 'X', 2.4, 3.25, 6.95, 0.0, 2.1, 'cased'),
    # ---- kitchen / laundry / family
    O('KitGarden', 'Y', 8.3, 10.5, 5.5, 1.0, 2.2, 'garden', depth=0.45),
    O('ArchKit', 'X', 2.3, 3.15, 11.15, 0.0, 2.15, 'arch', spring=1.6),
    O('DoorLau', 'X', 3.75, 4.50, 11.15, 0.0, 2.05, 'door', hinge='a1', open=90.0),
    O('RecessW','X',4.80,5.42,11.15,.95,2.20,'dh',grid=(3,2)),
    O('SideDoor', 'Y', 11.55, 12.35, 4.40, 0.0, 2.05, 'door', hinge='a0', open=0.0, style='glazed', ext=True),
    O('LauW', 'Y', 12.75, 13.42, 5.5, 1.1, 2.2, 'dh', grid=(2, 2)),
    O('FamFrench', 'X', 0.5, 2.1, FAMILY_REAR, 0.0, 2.25, 'french', open=100.0, lites=(2, 5)),
    O('FamW1', 'X', 2.55, 3.1, FAMILY_REAR, 0.15, 2.25, 'fixed_lites', grid=(2, 5)),
    O('FamReturn', 'Y', 16.97, 17.72, -0.40, .9, 2.25, 'dh', grid=(3, 2)),
    O('FamWE', 'Y', 17.02, 17.72, 3.25, 0.9, 2.25, 'dh', grid=(2, 2)),
    # ---- bedrooms / baths (main)
    O('BedAW', 'Y', 6.7, 8.5, -5.75, 0.9, 2.25, 'dh3', mullions=(7.6,), grid=(3, 2)),
    O('DoorBedA', 'Y', 8.7, 9.55, -1.4, 0.0, 2.05, 'door', hinge='a1', open=95.0),
    O('DoorHalf', 'Y', 4.82, 5.57, -4.20, 0.0, 2.05, 'door', hinge='a0', open=0.0),
    O('BathAW', 'Y', 10.60, 11.55, -5.75, 1.0, 2.25, 'dh', grid=(3, 2), frost=True),
    O('BathVestArch','Y',10.50,11.40,-2.85,0.,2.15,'cased'),
    O('DoorBathA', 'Y', 11.6, 12.3, -1.4, 0.0, 2.05, 'door', hinge='a1', open=0.0),
    O('DoorBedB', 'X', -1.18, -0.38, 12.75, 0.0, 2.05, 'door', hinge='a0', open=95.0),
    O('BedBW2', 'Y', 15.55, 16.30, -5.75, 0.9, 2.25, 'dh', grid=(3, 2)),
    O('BedBW3', 'X', -4.95, -4.00, BED_REAR, 0.9, 2.25, 'dh', grid=(3, 2)),
    O('BedBW4', 'X', -1.85, -0.90, BED_REAR, 0.9, 2.25, 'dh', grid=(3, 2)),
    # ---- upper level
    O('PrimWF', 'X', 3.05, 5.05, WINGY0, Z_UP + 0.65, Z_UP + 2.25, 'dh3', mullions=(3.5, 4.6), grid=(2, 3), shutters=0.4, fixed_centre=True),   # photo 00: wide fixed centre + two narrow DH, board shutters
    O('StairW1', 'X', -1.3, -0.85, UPY0, Z_UP + 1.35, Z_UP + 1.85, 'leaded', shutters=0.18),   # the two tiny diamond-leaded squares (photo 00)
    O('StairW2', 'X', -0.1, 0.35, UPY0, Z_UP + 1.35, Z_UP + 1.85, 'leaded', shutters=0.18),
    O('Wic2WF', 'X', -2.95, -2.4, UPY0, Z_UP + 1.3, Z_UP + 2.0, 'dh', grid=(2, 2), shutters=0.3),   # short, high closet window (measured)   # small shuttered DH at the upper left (photo 00)
    O('PrimWE1', 'Y', 7.0, 7.9, WINGX1 - WT, Z_UP + 0.8, Z_UP + 2.15, 'dh', grid=(3, 2)),
    O('PrimWE2', 'Y', 10.7, 11.6, WINGX1 - WT, Z_UP + 0.8, Z_UP + 2.15, 'dh', grid=(3, 2)),
    O('PBathWE', 'Y', 13.2, 14.1, WINGX1 - WT, Z_UP + 1.1, Z_UP + 2.15, 'dh', grid=(3, 2)),
    O('PBathWN', 'X', 3.70, 4.72, WINGY1 - WT, Z_UP + 0.85, Z_UP + 1.85, 'paired', frost=True),
    O('Bed3WN', 'X', -2.72, -1.30, UPY1 - WT, Z_UP + 0.8, Z_UP + 2.15, 'paired'),
    O('Bed3WN2', 'X', -1.08, 0.34, UPY1 - WT, Z_UP + 0.8, Z_UP + 2.15, 'paired'),
    O('HallBathWN', 'X', 1.74, 2.27, WINGY1-WT, Z_UP+1.12, Z_UP+2.05, 'paired'),
    O('Bed2InnerW','Y',7.88,8.63,-.5,Z_UP+.75,Z_UP+2.12,'dh',grid=(3,2),frost=True),
    O('Bed2Slider', 'Y', 8.6, 10.4, UPX0, Z_UP, Z_UP + 2.1, 'slider', open=True),   # open half y 9.5..10.4
    O('Wic2W', 'Y', 6.59, 6.97, UPX0, Z_UP + 0.60, Z_UP + 2.15, 'fixed_lites', grid=(2,6)),
    O('DoorPrim', 'Y', 10.7, 11.55, 0.9, Z_UP, Z_UP + 2.05, 'door', hinge='a1', open=100.0),
    O('DoorBed2', 'Y', 10.55, 11.4, -0.5, Z_UP, Z_UP + 2.05, 'door', hinge='a1', open=88.0),
    O('DoorBed3', 'X', 0.0, 0.85, 13.4, Z_UP, Z_UP + 2.05, 'door', hinge='a0', open=100.0),
    O('DoorHBath', 'Y', 12.6, 13.35, 0.9, Z_UP, Z_UP + 2.05, 'door', hinge='a1', open=-90.0),
    O('DoorPBath', 'X', 3.0, 3.8, 12.4, Z_UP, Z_UP + 2.05, 'door', hinge='a0', open=100.0),
    O('DoorWic', 'Y', 7.2, 8.0, 2.3, Z_UP, Z_UP + 2.05, 'door', hinge='a0', open=0.0),
    O('DoorWic2', 'X', -1.6, -0.8, 7.45, Z_UP, Z_UP + 2.05, 'door', hinge='a0', open=-95.0),   # photo 16: the reach-in closet stands open
    O('DoorCl3', 'Y', 15.25, 16.40, 0.9, Z_UP, Z_UP + 2.05, 'sliding_cl'),
]
BY_NAME = {o['name']: o for o in OPENINGS}
ENTRY_HINGE = (-0.83, 0.125)           # the front door leaf's hinge line (x, y) -> house.py DOORS / archviz.film


def wall_plane(w):
    """(axis, b_lo, b_hi) of a wall: the plane coordinate range across its thickness."""
    return w['along'], w['b0'], w['b1']


def holes_for(w, tol=1e-4):
    from archviz.plan import holes_for as holes
    return holes(w, OPENINGS, tol)


def check():
    from archviz.plan import unmatched_openings
    return unmatched_openings(WALLS, OPENINGS)


if __name__ == "__main__":
    b = check()
    print("openings not in exactly one wall:", b if b else "none")
    print(len(WALLS), "walls,", len(OPENINGS), "openings")
