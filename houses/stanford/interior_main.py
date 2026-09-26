"""Main-floor interiors (photos 04-14, 07, 24): finished floors, the main ceiling layer (2.50-2.52), interior
partitions with 2-panel doors, paint skins on every room face, baseboards, the U-shaped stair (both flights, landing,
the landing-enclosure wall, oak balustrades), the powder room, kitchen cabinetry + appliances, the great-room gas
fireplace, window dressings, furniture / art staging (virtual, after the listing photos), fixtures and lights, and
the finished garage interior.

Coordinates and levels come from plan.py.  Layout choices that the photos only imply (the powder room under the
landing, the plumbing chase north of it, the closed void behind the refrigerator wall, the coat closet notched into
the garage) are documented in REFERENCES.md.  Interior lights live in the collection 'Lights_Main'.
"""
import math
import random
import bpy
from .plan import *
from archviz.mesh import MB
from archviz.lights import add_light, area_light
from archviz.cladding import Face, holed_wall
from archviz import fenestration as fen
from archviz import materials as _m
from archviz import finishes as fz
from archviz import furnish as fu

LC = 'Lights_Main'
ZC = Z_C1                      # main ceiling underside
DOOR_H = 2.03
WARM = (1.0, 0.80, 0.58)       # 2700 K lamps
NEUTRAL = (1.0, 0.95, 0.88)    # 3500 K LED cans (the photos' white balance renders them near white)

# ---------------------------------------------------------------- key interior lines (see the docstring / REFERENCES)
# The core between the stair (plan ST_*) and the kitchen was re-planned after the stair moved back (LEAD, +0.95 m) with a
# joint solve of photos 12 + 13 + 14 (inputs in cams/int_great.json, 1.8-2.8 px rms):
# kitchen south (refrigerator) wall face y 7.36 +/- 0.07 (was 7.85), the pier at the west end of that run (east face
# x 8.94, north face y 8.10), the fridge x 9.88..10.81 against a return wall x 10.84, the angled pantry wall from
# (10.84, 8.70) to the counter-run end (11.63, 9.43).  The dining room's east wall (x ~8.46, photo 08: the medallion
# wall) is the powder room's west wall.  YR (11.65) is the rear wall's inner face YB1 - EWT.
HALL_X = (GAR[1], 7.20)                 # hall between the garage wall and its east wall (x 7.20 .. 7.32)
SOUTH_Y = ST_YM                         # the powder-door wall's south face (y ST_YM .. +IWT; INT_FRONT photo 06: 5.65 +/- 0.13)
FRIDGE_Y = 7.28                         # kitchen's south (refrigerator) wall face (INT_CAM joint 08-14 solve 7.28 +/- 0.05)
DIN_EX = 8.46                           # dining room east wall face (08: medallion wall ~8.35; 14: pier NW corner 8.58)
PIER = dict(x0=DIN_EX, x1=8.90, y0=FRIDGE_Y, y1=8.03)   # the pier ending the fridge-wall run (NE corner (8.90, 8.03) +/- 0.05, 11/14)
CORE_X = PIER['x1']                     # kept for callers: the kitchen's west line (pier east face)
PW = dict(x0=DIN_EX + IWT, x1=9.65, y0=SOUTH_Y + IWT, y1=FRIDGE_Y - IWT)   # powder room (door south, vanity north; 07: east wall 9.654)
PW_DOOR = (8.76, 9.58)                  # powder door (05/06 joint solve: casing outer 8.71 .. 9.72 +/- 0.08 -> a 32" leaf)
LINEN = dict(y0=5.93, y1=6.39)          # narrow closet door on the hall's east wall (seen in 05 edge-on and through the hall in 08)
PANTRY = ((10.84, 8.70), (11.63, 9.43))  # the angled pantry wall (door centred, 12 / 13), return end -> counter-run end
RETURN_X = PANTRY[0][0]                 # the fridge alcove's east wall face (x 10.84 .. 10.96), also the pantry's west wall
FRUIT_X0 = 11.0                         # the landing-enclosure wall at y ST_Y0 runs x 11.0 .. right wall
COAT = dict(y0=2.15, y1=2.91)           # coat-closet door on the foyer's west wall, hinged on its south jamb (photo 04)
FOYER_WX = 7.22                         # foyer west wall face (photo 04: 7.20-7.24, same plane as the entry leaf; INT_CAM)
COAT_Y1 = 3.85                          # the closet's north wall face (hall side); closet interior x 6.0 .. 7.03, y 1.75 .. 3.73
GENTRY = dict(y0=5.40, y1=6.21)         # garage entry door near the hall's end (photos 05, 14)
XR = XB1 - EWT                          # the right wall's inner face (12.30)
YR = YB1 - EWT                          # the rear wall's inner face (11.65)


def _mats(M):
    """Main-floor finishes and staging materials.  Colours were iterated against photo patch means (notes_INT_GREAT);
    keys used by interior_front / interior_upper are kept."""
    g = M.setdefault
    # ---- floors: a brown-cherry laminate (photos 11-14: less orange than a red cherry) and a beige cut-pile carpet
    g('laminate', fz.laminate_floor("LaminateBrownCherry", light=(0.225, 0.115, 0.078, 1), dark=(0.100, 0.050, 0.036, 1),
                                    plank=(1.22, 0.192), along='X', tint=0.14, rough=0.24, coat=0.4))
    M['carpet'] = fz.carpet("CarpetBeigeCutPile", (0.44, 0.31, 0.175, 1), alt=(0.37, 0.26, 0.145, 1), sheen=0.25)   # overrides the library key
    # ---- kitchen: honey-glazed maple, a tan speckled perimeter laminate and a dark speckled 'granite' island laminate
    g('maple', fz.cabinet_wood("MapleHoneyGlazed", light=(0.33, 0.14, 0.048, 1), dark=(0.21, 0.085, 0.028, 1), grain_axis='Z', glaze=0.15))
    g('maple_h', fz.cabinet_wood("MapleHoneyGlazedH", light=(0.33, 0.14, 0.048, 1), dark=(0.21, 0.085, 0.028, 1), grain_axis='X', glaze=0.15))
    g('maple_island', fz.cabinet_wood("MapleIslandGlazed", light=(0.105, 0.064, 0.040, 1), dark=(0.072, 0.044, 0.028, 1), grain_axis='Z',
                                      glaze=0.15))
    g('maple_y', fz.cabinet_wood("MapleHoneyGlazedY", light=(0.33, 0.14, 0.048, 1), dark=(0.21, 0.085, 0.028, 1), grain_axis='Y', glaze=0.15))
    g('counter_beige', fz.speckle("LaminateSandSpeckle", (0.30, 0.282, 0.262, 1),
                                  [((0.20, 0.165, 0.13, 1), 240, 0.22, 0.30), ((0.56, 0.50, 0.44, 1), 300, 0.22, 0.30),
                                   ((0.27, 0.25, 0.23, 1), 460, 0.18, 0.30), ((0.44, 0.30, 0.20, 1), 200, 0.10, 0.3)],
                                  mottle=(0.84, 1.12), mottle_scale=3.5, rough=0.34, bump=0.08))
    g('counter_dark', fz.speckle("LaminateGraniteMocha", (0.105, 0.088, 0.080, 1),
                                 [((0.006, 0.006, 0.006, 1), 260, 0.45, 0.36), ((0.30, 0.285, 0.27, 1), 300, 0.38, 0.33),
                                  ((0.55, 0.52, 0.50, 1), 420, 0.22, 0.32), ((0.26, 0.14, 0.09, 1), 240, 0.25, 0.32)],
                                 mottle=(0.92, 1.06), mottle_scale=5.0, rough=0.30, bump=0.10))
    g('oak_stair', _m.wood("OakGolden", light=(0.60, 0.36, 0.16, 1), dark=(0.44, 0.24, 0.10, 1), grain_axis='Z', rough=0.35, coat=0.35))
    g('oak_stair_h', _m.wood("OakGoldenH", light=(0.60, 0.36, 0.16, 1), dark=(0.44, 0.24, 0.10, 1), grain_axis='X', rough=0.35, coat=0.35))
    # ---- fireplace: travertine-look 12" porcelain (photo 10: beige / grey mottled tiles, visible joints)
    TILE = [(0.50, 0.41, 0.29, 1), (0.56, 0.46, 0.33, 1), (0.47, 0.39, 0.29, 1), (0.53, 0.43, 0.31, 1), (0.58, 0.49, 0.36, 1)]
    g('fire_tile', fz.stone_tile("FireplaceTileTravertine", TILE, plane='YZ', vein=0.45, pits=0.35, per_island=True))
    g('fire_tile_h', fz.stone_tile("FireplaceHearthTravertine", TILE, plane='XY', vein=0.30, pits=0.25, per_island=True))
    g('grout', _m.new_mat("TileGroutSand", (0.36, 0.32, 0.27, 1), rough=0.9))
    g('firebox_glass', fz.shadow_glass("FireboxGlassTinted", tint=(0.80, 0.78, 0.76, 1), reflect=0.25))
    g('refractory', _m.noise_mat("FireboxRefractory", (0.035, 0.033, 0.032, 1), (0.09, 0.085, 0.08, 1), scale=30, bump=0.4, rough=0.9))
    g('ceramic_log', _m.noise_mat("CeramicLogs", (0.28, 0.25, 0.22, 1), (0.66, 0.63, 0.58, 1), scale=18, bump=0.9, rough=0.9))
    # ---- woods
    g('espresso', _m.wood("Espresso", light=(0.075, 0.04, 0.025, 1), dark=(0.035, 0.018, 0.012, 1), grain_axis='X', rough=0.35, coat=0.4))
    g('espresso_v', _m.wood("EspressoV", light=(0.075, 0.04, 0.025, 1), dark=(0.035, 0.018, 0.012, 1), grain_axis='Z', rough=0.35, coat=0.4))
    g('dining_wood', fz.cerused_wood("DiningCerusedOakX", grain_axis='X'))
    g('dining_wood_y', fz.cerused_wood("DiningCerusedOakY", grain_axis='Y'))
    g('dining_wood_z', fz.cerused_wood("DiningCerusedOakZ", grain_axis='Z'))
    g('carved', fz.carved_wood("CarvedSheeshamTeak", base=(0.070, 0.030, 0.016, 1), high=(0.17, 0.085, 0.040, 1)))
    g('carved_black', fz.carved_wood("CarvedBlackLacquer", base=(0.022, 0.018, 0.016, 1), high=(0.075, 0.055, 0.040, 1), lacquer_black=True))
    g('media_black', _m.new_mat("MediaConsoleBlack", (0.030, 0.030, 0.032, 1), rough=0.38, coat=0.3))
    g('glass_smoke', _m.new_mat("SmokedGlass", (0.10, 0.10, 0.10, 1), rough=0.03, spec=0.6, transmission=0.7, coat=0.5))
    # ---- textiles
    g('fabric_sage', _m.fabric("SofaSageGrey", (0.36, 0.38, 0.34, 1), weave=90, bump=0.2))
    g('fabric_greige', _m.fabric("SectionalGreyMicrofiber", (0.19, 0.172, 0.152, 1), weave=150, bump=0.15, sheen=0.15))
    g('fabric_leaf', _leaf_print("SlipperChairLeaf"))
    g('fabric_stripe', _stripe_print("PillowStripe"))
    g('fabric_damask', _damask_print("PillowDamask"))
    g('fabric_seat', _m.fabric("DiningSeatBeigeLinen", (0.40, 0.365, 0.31, 1), weave=130, bump=0.2, sheen=0.2))
    M['fabric_white'] = _m.fabric("PillowWhite", (0.36, 0.355, 0.345, 1), weave=80, bump=0.3, sheen=0.2)             # overrides the library key
    g('fabric_ivory', _m.fabric("PillowIvoryTexture", (0.36, 0.355, 0.345, 1), weave=40, bump=0.45, sheen=0.3))
    g('pillow_yellow', _pattern("PillowYellowPink", (0.72, 0.52, 0.08, 1), (0.80, 0.30, 0.34, 1), 26.0, 0.56, fg2=(0.85, 0.72, 0.20, 1)))
    g('pillow_turq', _m.fabric("PillowTurquoise", (0.10, 0.42, 0.40, 1), weave=60, bump=0.4, sheen=0.2))
    g('jhula_cushion', _stripe_print("JhulaStripe", (0.55, 0.45, 0.30, 1), (0.66, 0.58, 0.44, 1), (0.36, 0.26, 0.16, 1), 38.0))
    g('sheer', _sheer("SheerWhite", (0.90, 0.89, 0.85, 1), 0.72))
    g('voile', fz.voile("VoileWhiteLinen", (0.86, 0.855, 0.83, 1), alpha=0.80))
    g('sheer_embroidered', _sheer("SheerEmbroidered", (0.86, 0.82, 0.72, 1), 0.62))
    g('drape_taupe', _m.fabric("SwagTaupe", (0.52, 0.42, 0.32, 1), weave=70, bump=0.2, sheen=0.8))
    g('blind_white', _m.new_mat("BlindVinylWhite", (0.78, 0.775, 0.76, 1), rough=0.42, spec=0.4))
    g('vertical_blind', fz.voile("VerticalBlindVinyl", (0.84, 0.84, 0.82, 1), alpha=0.97, slub=0.02))
    g('rug_persian', fz.persian_rug("RugPersianKashan", field=(0.42, 0.32, 0.225, 1), border=(0.24, 0.095, 0.05, 1), accent=(0.11, 0.065, 0.045, 1),
                                    ivory=(0.52, 0.42, 0.31, 1), dark=(0.03, 0.022, 0.018, 1), motif=7.5, border_w=0.13))
    g('rug_persian_09', fz.persian_rug("RugPersianIvory", field=(0.58, 0.52, 0.42, 1), border=(0.42, 0.14, 0.08, 1), accent=(0.12, 0.15, 0.22, 1),
                                       ivory=(0.66, 0.60, 0.50, 1), dark=(0.07, 0.07, 0.09, 1), motif=10.0, seed=2.0))
    g('rug_grey', _persian("RugFoyerGrey", (0.22, 0.24, 0.26, 1), (0.50, 0.52, 0.52, 1), (0.34, 0.37, 0.40, 1)))
    g('fringe', _m.fabric("RugFringe", (0.55, 0.49, 0.40, 1), weave=300, bump=0.6, sheen=0.1))
    g('rush', fz.rush("RushSeagrass", base=(0.46, 0.34, 0.15, 1), alt=(0.30, 0.20, 0.08, 1)))
    g('rope', M['rush'])
    # ---- metals / glass
    g('brass', M['brass'])
    g('brass_satin', _m.new_mat("FanBrassSatin", (0.60, 0.48, 0.28, 1), rough=0.34, metal=1.0))
    g('nickel_brushed', fz.brushed_metal("BrushedNickel", (0.58, 0.575, 0.56, 1), rough=0.30, axis='Z'))
    g('steel_brushed', fz.brushed_metal("StainlessBrushedX", (0.64, 0.635, 0.62, 1), rough=0.36, axis='X'))
    g('steel_brushed_y', fz.brushed_metal("StainlessBrushedY", (0.64, 0.635, 0.62, 1), rough=0.36, axis='Y'))
    g('steel_brushed_z', fz.brushed_metal("StainlessBrushedZ", (0.64, 0.635, 0.62, 1), rough=0.36, axis='Z'))
    g('pewter', _m.new_mat("PewterIron", (0.40, 0.40, 0.39, 1), rough=0.38, metal=1.0))
    g('glass_clear', _m.new_mat("TableGlass", (0.92, 0.96, 0.94, 1), rough=0.0, transmission=1.0, ior=1.5, spec=0.5))
    g('glass_ribbed', _ribbed_glass("PrismaticBellGlass"))
    g('frosted', _m.new_mat("FrostedShade", (0.95, 0.93, 0.88, 1), rough=0.35, transmission=0.8, ior=1.45, emit=(1.0, 0.85, 0.65, 1), emit_str=1.5))
    g('tulip', _m.new_mat("TulipFrostGlass", (0.92, 0.91, 0.87, 1), rough=0.40, transmission=0.8, ior=1.45, emit=(1.0, 0.86, 0.68, 1),
                          emit_str=1.0))
    g('shade_linen', _m.new_mat("LampShadeLinen", (0.85, 0.72, 0.52, 1), rough=0.8, transmission=0.3, emit=(1.0, 0.78, 0.52, 1), emit_str=2.0))
    g('red_glass', _m.new_mat("RubyGlassBowl", (0.75, 0.10, 0.08, 1), rough=0.1, transmission=0.8, ior=1.5, coat=0.5))
    g('cultured_marble', _m.new_mat("CulturedMarble", (0.82, 0.78, 0.68, 1), rough=0.12, coat=0.6))
    g('concrete_garage', _m.tiles("GarageSlab", (0.46, 0.46, 0.45, 1), grout=(0.30, 0.30, 0.30, 1), size=(3.6, 3.1), gap=0.006,
                                  rough=0.8, variation=0.03, mottle=0.55, bump=0.1))
    g('drywall_white', _m.plaster("GarageDrywall", base=(0.78, 0.78, 0.76, 1), rough=0.9, grain=0.03))
    g('bin_blue', _m.new_mat("BinBlue", (0.07, 0.24, 0.42, 1), rough=0.55))
    # ---- art
    g('art_city', _art_city("ArtCityStreetOil"))
    g('art_cafe', _art_cafe("ArtCafeTerrace"))
    g('art_blossom', _art_blossom("ArtAlmondBlossom"))
    g('art_fruit', _art("ArtFruitStill", [(0.70, 0.12, 0.05, 1), (0.85, 0.70, 0.10, 1), (0.35, 0.55, 0.12, 1), (0.45, 0.08, 0.12, 1)], 4.0))
    g('art_iris', _art("ArtIrises", [(0.10, 0.25, 0.55, 1), (0.30, 0.55, 0.20, 1), (0.85, 0.65, 0.10, 1), (0.70, 0.20, 0.08, 1)], 8.0))
    g('art_calligraphy', _art("ArtCalligraphy", [(0.72, 0.62, 0.42, 1), (0.30, 0.20, 0.10, 1), (0.62, 0.52, 0.34, 1), (0.40, 0.30, 0.18, 1)], 12.0))
    g('art_venice', _art("ArtVeniceCanal", [(0.55, 0.42, 0.22, 1), (0.25, 0.35, 0.45, 1), (0.70, 0.55, 0.30, 1), (0.30, 0.22, 0.14, 1)], 6.0))
    g('art_medallion', _art_medallion("ArtMedallionPlate"))
    g('frame_gold', _m.new_mat("FrameGold", (0.55, 0.40, 0.18, 1), rough=0.35, metal=0.8))
    g('frame_champagne', _ornate_gold("FrameChampagneGold", lo=(0.36, 0.28, 0.14, 1), hi=(0.78, 0.66, 0.40, 1)))
    g('frame_gold_ornate', _ornate_gold("FrameGoldOrnate"))
    g('frame_dark', _m.new_mat("FrameWalnut", (0.10, 0.06, 0.04, 1), rough=0.4))
    g('frame_slate', _m.new_mat("FrameSlateBlue", (0.20, 0.24, 0.28, 1), rough=0.4))
    g('plant_pot_blue', _m.new_mat("PorcelainBlueWhite", (0.70, 0.74, 0.82, 1), rough=0.15, coat=0.6))
    g('porcelain_blue', _blue_white("PorcelainBlueWhiteChinoiserie"))
    g('tv', M['tv'])
    g('bulb_glow', _m.new_mat("BulbGlowWarm", (1.0, 0.95, 0.85, 1), rough=0.3, emit=(1.0, 0.88, 0.70, 1), emit_str=6.0))
    g('appliance_black', _m.new_mat("ApplianceBlack", (0.015, 0.015, 0.017, 1), rough=0.25, coat=0.4))
    g('fan_blade', _m.wood("FanBladeLightWood", light=(0.62, 0.52, 0.38, 1), dark=(0.52, 0.42, 0.30, 1), grain_axis='X', rough=0.5, coat=0.2))
    g('fan_blade_maple', _m.wood("FanBladeBleachedMaple", light=(0.70, 0.60, 0.44, 1), dark=(0.60, 0.50, 0.36, 1), grain_axis='X', rough=0.45,
                                 coat=0.2, ring=30))
    g('clock_face', _m.new_mat("ClockDialWhite", (0.84, 0.83, 0.80, 1), rough=0.3, coat=0.4))
    g('ink', _m.new_mat("ClockInk", (0.012, 0.012, 0.012, 1), rough=0.4))
    g('mahogany', _m.wood("ClockMahogany", light=(0.22, 0.075, 0.035, 1), dark=(0.10, 0.03, 0.015, 1), grain_axis='Z', rough=0.3, coat=0.5))
    g('register_white', _m.new_mat("RegisterWhiteEnamel", (0.80, 0.80, 0.78, 1), rough=0.35, spec=0.5))
    g('duct_dark', _m.new_mat("DuctDark", (0.02, 0.02, 0.02, 1), rough=0.8))
    g('candle_orange', _m.new_mat("CandleOrange", (0.75, 0.22, 0.05, 1), rough=0.45, subsurface=0.3))
    g('candle_yellow', _m.new_mat("CandleOchre", (0.80, 0.50, 0.08, 1), rough=0.45, subsurface=0.3))
    g('vase_stripe', _stripe_vase("VaseStripedBrownGold"))
    g('reed', _m.noise_mat("DriedReed", (0.55, 0.38, 0.16, 1), (0.72, 0.56, 0.28, 1), scale=60, bump=0.1, rough=0.7))
    g('peach', _m.noise_mat("PeachSkin", (0.62, 0.22, 0.06, 1), (0.80, 0.42, 0.12, 1), scale=12, bump=0.05, rough=0.6))
    g('apple_red', _m.noise_mat("AppleRed", (0.45, 0.04, 0.03, 1), (0.70, 0.18, 0.06, 1), scale=10, bump=0.05, rough=0.35))
    g('ceramic_floral', _pattern("CeramicFloralWhite", (0.82, 0.80, 0.76, 1), (0.55, 0.40, 0.50, 1), 30.0, 0.62, fg2=(0.35, 0.50, 0.30, 1)))
    g('outlet', _m.new_mat("OutletAlmond", (0.78, 0.75, 0.68, 1), rough=0.35))
    return M


# ---------------------------------------------------------------- procedural textile / art materials
def _pattern(name, base, fg, scale, thresh, fg2=None, distortion=1.2):
    m, nt, b = _m._new(name)
    vec = _m._coords(nt)
    n = _m._noise(nt, vec, scale=scale, detail=3.0, distortion=distortion)
    f = _m._math(nt, 'GREATER_THAN', n, thresh)
    col = _m._mixrgb(nt, f, base, fg)
    if fg2 is not None:
        n2 = _m._noise(nt, _m._coords(nt, loc=(3.1, 1.7, 0.4)), scale=scale * 1.3, detail=2.0, distortion=distortion)
        col = _m._mixrgb(nt, _m._math(nt, 'GREATER_THAN', n2, thresh + 0.04), col, fg2)
    nt.links.new(b.inputs["Base Color"], col)
    _m._set(b, "Roughness", 0.9); _m._set(b, "Sheen Weight", 0.2)
    _m._bump(nt, b, _m._noise(nt, vec, scale=90.0, detail=2.0), 0.2, 0.003)
    return m


def _leaf_print(name):
    return _pattern(name, (0.66, 0.62, 0.50, 1), (0.42, 0.44, 0.34, 1), 9.0, 0.56, fg2=(0.78, 0.74, 0.62, 1))


def _damask_print(name):
    return _pattern(name, (0.20, 0.12, 0.08, 1), (0.52, 0.60, 0.56, 1), 14.0, 0.5, fg2=(0.62, 0.66, 0.60, 1))


def _stripe_print(name, c1=(0.55, 0.45, 0.32, 1), c2=(0.72, 0.66, 0.55, 1), c3=(0.30, 0.42, 0.45, 1), scale=22.0):
    m, nt, b = _m._new(name)
    wave = nt.nodes.new("ShaderNodeTexWave"); wave.wave_type = 'BANDS'; wave.bands_direction = 'Z'
    wave.inputs["Scale"].default_value = scale; wave.inputs["Distortion"].default_value = 0.0
    nt.links.new(wave.inputs["Vector"], _m._coords(nt))
    col = _m._ramp(nt, wave.outputs["Fac"], [(0.0, c1), (0.3, c2), (0.55, c3), (0.8, (0.62, 0.52, 0.40, 1))])
    nt.links.new(b.inputs["Base Color"], col)
    _m._set(b, "Roughness", 0.9); _m._set(b, "Sheen Weight", 0.2)
    return m


def _gen_uv(nt, axis, flip=False):
    """(u, v) on a wall-hung canvas from Generated coordinates: axis 'X' for a canvas in an XZ plane, 'Y' for YZ;
    `flip` mirrors u for canvases whose viewer's right is the -X / -Y direction."""
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(sep.inputs["Vector"], tc.outputs["Generated"])
    u = sep.outputs["X"] if axis == 'X' else sep.outputs["Y"]
    if flip:
        u = _m._math(nt, 'SUBTRACT', 1.0, u)
    return u, sep.outputs["Z"]


def _uvvec(nt, u, v, sx=1.0, sy=1.0, ox=0.0, oy=0.0):
    c = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(c.inputs["X"], _m._math(nt, 'ADD', _m._math(nt, 'MULTIPLY', u, sx), ox))
    nt.links.new(c.inputs["Y"], _m._math(nt, 'ADD', _m._math(nt, 'MULTIPLY', v, sy), oy))
    return c.outputs["Vector"]


def _brush(nt, u, v, col, amount=0.18, scale=60.0):
    """Impasto: short directional strokes modulating the colour and the bump."""
    n = _m._noise(nt, _uvvec(nt, u, v, scale, scale * 0.35), scale=1.0, detail=3.0)
    return _m._mixrgb(nt, _m._math(nt, 'MULTIPLY', n, amount), col, (1.35, 1.35, 1.3, 1), 'MULTIPLY'), n


def _art_blossom(name, axis='Y', flip=False):
    """Van Gogh's 'Almond Blossom' as hung over the mantel (photo 10): a teal ground, yellow-olive branches that
    cross the canvas from the lower right, and many white / pale-pink blossoms along them."""
    m, nt, b = _m._new(name)
    u, v = _gen_uv(nt, axis, flip)
    ground = _m._ramp(nt, _m._noise(nt, _uvvec(nt, u, v, 6, 6), scale=1.0, detail=4.0),
                      [(0.3, (0.07, 0.26, 0.25, 1)), (0.7, (0.12, 0.36, 0.34, 1))])
    col = ground
    br_all = None
    for k, (sc, w, off) in enumerate(((1.6, 0.012, 0.0), (2.6, 0.009, 2.7), (4.0, 0.006, 5.1))):
        n = _m._noise(nt, _uvvec(nt, u, v, sc, sc, off, off * 0.7), scale=1.0, detail=2.0, distortion=1.2)
        br = _m._math(nt, 'LESS_THAN', _m._math(nt, 'ABSOLUTE', _m._math(nt, 'SUBTRACT', n, 0.5)), w)
        col = _m._mixrgb(nt, br, col, (0.52, 0.48, 0.12, 1) if k else (0.40, 0.34, 0.08, 1))
        near = _m._math(nt, 'LESS_THAN', _m._math(nt, 'ABSOLUTE', _m._math(nt, 'SUBTRACT', n, 0.5)), w * 9.0)
        br_all = near if br_all is None else _m._math(nt, 'MAXIMUM', br_all, near)
    vo = _m._voronoi(nt, _uvvec(nt, u, v, 11, 11), scale=1.0, feature='F1', rand=1.0)
    pick = _m._math(nt, 'GREATER_THAN', fz._sep(nt, vo.outputs["Color"])[0], 0.15)
    petal = _m._noise(nt, _uvvec(nt, u, v, 60, 60), scale=1.0, detail=2.0)
    dd = _m._math(nt, 'ADD', vo.outputs["Distance"], _m._math(nt, 'MULTIPLY', petal, 0.18))
    bloom = _m._math(nt, 'MULTIPLY', _m._math(nt, 'MULTIPLY', br_all, pick), _m._math(nt, 'LESS_THAN', dd, 0.46))
    bcol = _m._mixrgb(nt, _m._math(nt, 'GREATER_THAN', fz._sep(nt, vo.outputs["Color"])[1], 0.6), (0.86, 0.84, 0.76, 1), (0.88, 0.74, 0.70, 1))
    col = _m._mixrgb(nt, bloom, col, bcol)
    col = _m._mixrgb(nt, _m._math(nt, 'MULTIPLY', bloom, _m._math(nt, 'LESS_THAN', dd, 0.12)), col, (0.70, 0.55, 0.20, 1))
    col, n2 = _brush(nt, u, v, col, 0.15, 90.0)
    nt.links.new(b.inputs["Base Color"], col)
    _m._set(b, "Roughness", 0.45)
    _m._bump(nt, b, n2, 0.3, 0.002)
    return m


def _art_city(name):
    """The palette-knife city street (photos 09, 10): tall narrow dark blue-grey buildings on both sides with lit
    windows and red / orange / yellow sign boards, a bright warm band of light up the middle (the far end of the
    street), and in the lower third a pale reflective street with blue patches and dark little figures."""
    m, nt, b = _m._new(name)
    u, v = _gen_uv(nt, 'Y')
    du = _m._math(nt, 'ABSOLUTE', _m._math(nt, 'SUBTRACT', u, 0.5))
    blocks = _m._voronoi(nt, _uvvec(nt, u, v, 14, 4), scale=1.0, feature='F1', rand=0.9)       # tall facades
    br, bg, bb = fz._sep(nt, blocks.outputs["Color"])
    col = _m._ramp(nt, bg, [(0.0, (0.03, 0.05, 0.11, 1)), (0.5, (0.08, 0.13, 0.24, 1)), (1.0, (0.22, 0.28, 0.36, 1))])
    win = _m._voronoi(nt, _uvvec(nt, u, v, 40, 60), scale=1.0, feature='F1', rand=0.6)
    lit = _m._math(nt, 'MULTIPLY', _m._math(nt, 'LESS_THAN', win.outputs["Distance"], 0.22),
                   _m._math(nt, 'GREATER_THAN', fz._sep(nt, win.outputs["Color"])[0], 0.55))
    col = _m._mixrgb(nt, lit, col, (0.85, 0.62, 0.25, 1))
    sgn = _m._voronoi(nt, _uvvec(nt, u, v, 22, 30), scale=1.0, feature='F1', rand=1.0)
    s_on = _m._math(nt, 'MULTIPLY', _m._math(nt, 'LESS_THAN', sgn.outputs["Distance"], 0.28),
                    _m._math(nt, 'GREATER_THAN', fz._sep(nt, sgn.outputs["Color"])[0], 0.6))
    s_on = _m._math(nt, 'MULTIPLY', s_on, _m._math(nt, 'GREATER_THAN', v, 0.35))
    scol = _m._ramp(nt, fz._sep(nt, sgn.outputs["Color"])[1], [(0.0, (0.62, 0.05, 0.03, 1)), (0.5, (0.85, 0.40, 0.05, 1)),
                                                              (1.0, (0.92, 0.80, 0.30, 1))])
    col = _m._mixrgb(nt, s_on, col, scol)
    band = _m._math(nt, 'SUBTRACT', 1.0, _m._math(nt, 'MULTIPLY', du, 9.0, clamp=True))
    band = _m._math(nt, 'MULTIPLY', band, _m._math(nt, 'GREATER_THAN', v, 0.35))
    col = _m._mixrgb(nt, _m._math(nt, 'MULTIPLY', band, 0.85), col, (0.92, 0.80, 0.55, 1))
    low = _m._math(nt, 'LESS_THAN', v, 0.33)
    street = _m._ramp(nt, _m._noise(nt, _uvvec(nt, u, v, 10, 22), scale=1.0, detail=3.0),
                      [(0.3, (0.12, 0.25, 0.55, 1)), (0.55, (0.70, 0.72, 0.75, 1)), (0.8, (0.35, 0.45, 0.65, 1))])
    col = _m._mixrgb(nt, low, col, street)
    figs = _m._math(nt, 'MULTIPLY', _m._math(nt, 'MULTIPLY', _m._math(nt, 'GREATER_THAN', v, 0.14), _m._math(nt, 'LESS_THAN', v, 0.30)),
                    _m._math(nt, 'GREATER_THAN', _m._noise(nt, _uvvec(nt, u, v, 34, 5), scale=1.0, detail=2.0), 0.60))
    figs = _m._math(nt, 'MULTIPLY', figs, _m._math(nt, 'LESS_THAN', du, 0.32))
    col = _m._mixrgb(nt, figs, col, _m._mixrgb(nt, _m._math(nt, 'GREATER_THAN', bb, 0.6), (0.06, 0.05, 0.06, 1), (0.60, 0.08, 0.05, 1)))
    col, n2 = _brush(nt, u, v, col, 0.2, 70.0)
    nt.links.new(b.inputs["Base Color"], col)
    _m._set(b, "Roughness", 0.4)
    _m._bump(nt, b, n2, 0.5, 0.003)
    return m


def _art_cafe(name):
    """Van Gogh's 'Cafe Terrace at Night' (photo 09, the south wall): the yellow awning and lit terrace wall on the
    left, a deep blue star-dotted building and sky at the top right, a green tree at the right, blue cobbles below."""
    m, nt, b = _m._new(name)
    u, v = _gen_uv(nt, 'X', flip=True)
    col = _m._ramp(nt, _m._noise(nt, _uvvec(nt, u, v, 8, 8), scale=1.0, detail=3.0),
                   [(0.3, (0.04, 0.08, 0.26, 1)), (0.7, (0.12, 0.18, 0.42, 1))])
    stars = _m._math(nt, 'MULTIPLY', _m._math(nt, 'GREATER_THAN', v, 0.55),
                     _m._math(nt, 'LESS_THAN', _m._voronoi(nt, _uvvec(nt, u, v, 16, 16), scale=1.0).outputs["Distance"], 0.10))
    col = _m._mixrgb(nt, stars, col, (0.85, 0.82, 0.55, 1))
    wall = _m._math(nt, 'MULTIPLY', _m._math(nt, 'LESS_THAN', u, 0.42), _m._math(nt, 'GREATER_THAN', v, 0.22))
    wall = _m._math(nt, 'MULTIPLY', wall, _m._math(nt, 'LESS_THAN', v, _m._math(nt, 'ADD', 0.88, _m._math(nt, 'MULTIPLY', u, -0.4))))
    col = _m._mixrgb(nt, wall, col, _m._ramp(nt, _m._noise(nt, _uvvec(nt, u, v, 14, 14), scale=1.0, detail=2.0),
                                           [(0.3, (0.78, 0.52, 0.06, 1)), (0.7, (0.92, 0.72, 0.18, 1))]))
    terrace = _m._math(nt, 'MULTIPLY', _m._math(nt, 'LESS_THAN', u, 0.58), _m._math(nt, 'LESS_THAN', v, 0.30))
    terrace = _m._math(nt, 'MULTIPLY', terrace, _m._math(nt, 'GREATER_THAN', v, 0.08))
    col = _m._mixrgb(nt, terrace, col, (0.80, 0.55, 0.12, 1))
    tree = _m._math(nt, 'MULTIPLY', _m._math(nt, 'GREATER_THAN', u, 0.78), _m._math(nt, 'MULTIPLY', _m._math(nt, 'GREATER_THAN', v, 0.35),
                                                                               _m._math(nt, 'LESS_THAN', v, 0.62)))
    col = _m._mixrgb(nt, tree, col, (0.15, 0.40, 0.12, 1))
    cob = _m._math(nt, 'LESS_THAN', v, 0.12)
    cv = _m._voronoi(nt, _uvvec(nt, u, v, 40, 30), scale=1.0, feature='F1')
    ccol = _m._mixrgb(nt, _m._math(nt, 'LESS_THAN', cv.outputs["Distance"], 0.25), (0.15, 0.20, 0.35, 1), (0.45, 0.50, 0.62, 1))
    col = _m._mixrgb(nt, cob, col, ccol)
    col, n2 = _brush(nt, u, v, col, 0.2, 70.0)
    nt.links.new(b.inputs["Base Color"], col)
    _m._set(b, "Roughness", 0.45)
    _m._bump(nt, b, n2, 0.45, 0.003)
    return m


def _art_medallion(name):
    """The framed medallion (photo 08, on the pier): a pale blue-grey field with a round silver plate carrying a
    gold floral spray."""
    m, nt, b = _m._new(name)
    u, v = _gen_uv(nt, 'Y')
    cu, cv = _m._math(nt, 'SUBTRACT', u, 0.5), _m._math(nt, 'SUBTRACT', v, 0.5)
    r = _m._math(nt, 'SQRT', _m._math(nt, 'ADD', _m._math(nt, 'MULTIPLY', cu, cu), _m._math(nt, 'MULTIPLY', cv, cv)))
    plate = _m._math(nt, 'LESS_THAN', r, 0.36)
    rim = _m._math(nt, 'MULTIPLY', plate, _m._math(nt, 'GREATER_THAN', r, 0.32))
    spray = _m._math(nt, 'MULTIPLY', _m._math(nt, 'LESS_THAN', r, 0.25),
                     _m._math(nt, 'GREATER_THAN', _m._noise(nt, _m._coords(nt, scale=(30, 30, 30)), scale=1.0, detail=3.0, distortion=1.5), 0.58))
    col = _m._mixrgb(nt, plate, (0.36, 0.44, 0.50, 1), (0.62, 0.66, 0.70, 1))
    col = _m._mixrgb(nt, rim, col, (0.30, 0.34, 0.40, 1))
    col = _m._mixrgb(nt, spray, col, (0.60, 0.46, 0.18, 1))
    nt.links.new(b.inputs["Base Color"], col)
    _m._set(b, "Roughness", 0.35); _m._set(b, "Metallic", 0.3)
    return m


def _ornate_gold(name, lo=(0.18, 0.12, 0.05, 1), hi=(0.62, 0.46, 0.20, 1)):
    """Carved and gilded frame moulding: gold leaf with dark rubbed recesses (noise relief)."""
    m, nt, b = _m._new(name)
    n = _m._noise(nt, _m._coords(nt, scale=(90, 90, 90)), scale=1.0, detail=4.0, distortion=1.0)
    col = _m._mixrgb(nt, _m._stretch(nt, n, 0.35, 0.6), lo, hi)
    nt.links.new(b.inputs["Base Color"], col)
    _m._set(b, "Roughness", 0.35); _m._set(b, "Metallic", 0.85)
    _m._bump(nt, b, n, 0.8, 0.003)
    return m


def _blue_white(name):
    """Blue-and-white porcelain (the planter by the slider, photo 14)."""
    m, nt, b = _m._new(name)
    n = _m._noise(nt, _m._coords(nt, scale=(14, 14, 14)), scale=1.0, detail=3.0, distortion=1.8)
    f = _m._math(nt, 'GREATER_THAN', n, 0.55)
    col = _m._mixrgb(nt, f, (0.78, 0.80, 0.84, 1), (0.08, 0.14, 0.42, 1))
    nt.links.new(b.inputs["Base Color"], col)
    _m._set(b, "Roughness", 0.15); _m._set(b, "Coat Weight", 0.7)
    return m


def _stripe_vase(name):
    """The barrel vase on the hearth (photo 10): dark brown with gold horizontal bands."""
    m, nt, b = _m._new(name)
    wave = nt.nodes.new("ShaderNodeTexWave"); wave.wave_type = 'BANDS'; wave.bands_direction = 'Z'
    wave.inputs["Scale"].default_value = 5.5; wave.inputs["Distortion"].default_value = 0.3
    nt.links.new(wave.inputs["Vector"], _m._coords(nt))
    f = _m._math(nt, 'GREATER_THAN', wave.outputs["Fac"], 0.72)
    col = _m._mixrgb(nt, f, (0.10, 0.05, 0.03, 1), (0.70, 0.52, 0.20, 1))
    nt.links.new(b.inputs["Base Color"], col)
    _m._set(b, "Roughness", 0.3); _m._set(b, "Coat Weight", 0.6)
    return m


def _ribbed_glass(name):
    """Clear prismatic (ribbed) glass for the chandelier bells: glass with vertical-rib bump and a faint frost."""
    m = _m.new_mat(name, (0.96, 0.97, 0.96, 1), rough=0.06, transmission=1.0, ior=1.5, spec=0.5, emit=(1.0, 0.90, 0.75, 1), emit_str=0.12)
    nt, b = m.node_tree, _m._bsdf(m)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(sep.inputs["Vector"], tc.outputs["Object"])
    ang = _m._math(nt, 'ARCTAN2', sep.outputs["Y"], sep.outputs["X"])
    rib = _m._math(nt, 'SINE', _m._math(nt, 'MULTIPLY', ang, 240.0))
    _m._bump(nt, b, rib, 0.3, 0.002)
    return m


def _sheer(name, color, alpha):
    m, nt, b = _m._new(name)
    _m._set(b, "Base Color", color); _m._set(b, "Roughness", 0.8); _m._set(b, "Sheen Weight", 0.6)
    tr = nt.nodes.new("ShaderNodeBsdfTranslucent"); tr.inputs["Color"].default_value = color
    tp = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix1 = nt.nodes.new("ShaderNodeMixShader"); mix1.inputs["Fac"].default_value = 0.45
    nt.links.new(mix1.inputs[1], b.outputs["BSDF"]); nt.links.new(mix1.inputs[2], tr.outputs["BSDF"])
    mix2 = nt.nodes.new("ShaderNodeMixShader"); mix2.inputs["Fac"].default_value = alpha
    nt.links.new(mix2.inputs[1], tp.outputs["BSDF"]); nt.links.new(mix2.inputs[2], mix1.outputs["Shader"])
    nt.links.new(nt.nodes["Material Output"].inputs["Surface"], mix2.outputs["Shader"])
    return m


def _persian(name, field, ivory, navy):
    """Hand-knotted-look rug: a red field of medallion / vine motifs, ivory + navy guard borders (Generated coords)."""
    m, nt, b = _m._new(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(sep.inputs["Vector"], tc.outputs["Generated"])
    u, v = sep.outputs["X"], sep.outputs["Y"]
    du = _m._math(nt, 'MINIMUM', u, _m._math(nt, 'SUBTRACT', 1.0, u))
    dv = _m._math(nt, 'MINIMUM', v, _m._math(nt, 'SUBTRACT', 1.0, v))
    edge = _m._math(nt, 'MINIMUM', _m._math(nt, 'MULTIPLY', du, 1.0), _m._math(nt, 'MULTIPLY', dv, 1.6))
    vor = _m._voronoi(nt, _m._coords(nt, scale=(9, 9, 9)), scale=1.0, feature='F1', rand=0.2)
    motif = _m._noise(nt, _m._coords(nt, scale=(16, 16, 16)), scale=1.0, detail=5.0, distortion=2.2)
    fieldc = _m._mixrgb(nt, _m._math(nt, 'GREATER_THAN', motif, 0.55), field, ivory)
    fieldc = _m._mixrgb(nt, _m._math(nt, 'LESS_THAN', vor.outputs["Distance"], 0.16), fieldc, navy)
    fieldc = _m._mixrgb(nt, _m._math(nt, 'GREATER_THAN', motif, 0.66), fieldc, (0.55, 0.40, 0.18, 1))
    band1 = _m._math(nt, 'LESS_THAN', edge, 0.06)
    band2 = _m._math(nt, 'LESS_THAN', edge, 0.035)
    col = _m._mixrgb(nt, band1, fieldc, ivory)
    col = _m._mixrgb(nt, band2, col, navy)
    fine = _m._noise(nt, _m._coords(nt), scale=180.0, detail=2.0)
    col = _m._mixrgb(nt, _m._math(nt, 'MULTIPLY', fine, 0.25), col, (0.75, 0.75, 0.75, 1), 'MULTIPLY')
    nt.links.new(b.inputs["Base Color"], col)
    _m._set(b, "Roughness", 0.95); _m._set(b, "Sheen Weight", 0.8)
    _m._bump(nt, b, fine, 0.3, 0.004)
    return m


def _art(name, colors, scale):
    """An impasto painting: blotchy multi-colour strokes (object-space noise) under a satin varnish."""
    m, nt, b = _m._new(name)
    vec = _m._coords(nt)
    n1 = _m._noise(nt, vec, scale=scale, detail=6.0, rough=0.6, distortion=1.5)
    col = _m._ramp(nt, n1, [(0.25, colors[0]), (0.45, colors[1]), (0.6, colors[2]), (0.78, colors[3])])
    n2 = _m._noise(nt, vec, scale=scale * 6, detail=3.0)
    col = _m._mixrgb(nt, _m._math(nt, 'MULTIPLY', n2, 0.25), col, (1.2, 1.2, 1.2, 1), 'MULTIPLY')
    nt.links.new(b.inputs["Base Color"], col)
    _m._set(b, "Roughness", 0.45)
    _m._bump(nt, b, n2, 0.4, 0.003)
    return m


# ================================================================ geometry helpers
def skin(mb, along, a0, a1, b, s, z0, z1, holes=(), off=0.002, t=0.004, mi=0):
    """Paint panel covering a wall face at plane b whose room lies toward s (+1/-1), with rectangular holes."""
    b0, b1 = (b + s * off, b + s * (off + t)) if s > 0 else (b + s * (off + t), b + s * off)
    holed_wall(mb, along, a0, a1, b0, b1, z0, z1, holes=holes, mi=mi)


def baseboard(mb, along, a0, a1, b, s, gaps=(), h=0.095, t=0.014, z0=0.0, mi=0):
    spans, cur = [], a0
    for g0, g1 in sorted(gaps):
        if g0 > cur:
            spans.append((cur, g0))
        cur = max(cur, g1)
    if cur < a1:
        spans.append((cur, a1))
    for (c0, c1) in spans:
        if c1 - c0 < 0.02:
            continue
        b0, b1 = (b + s * 0.006, b + s * (0.006 + t)) if s > 0 else (b + s * (0.006 + t), b + s * 0.006)
        if along == 'X':
            mb.box(c0, c1, b0, b1, z0, z0 + h, mi)
            mb.box(c0, c1, b0, b1 + (0.004 if s > 0 else 0) - (0.004 if s < 0 else 0), z0 + h, z0 + h + 0.012, mi)
        else:
            mb.box(b0, b1, c0, c1, z0, z0 + h, mi)
            mb.box(b0 + (0 if s > 0 else -0.004), b1 + (0.004 if s > 0 else 0), c0, c1, z0 + h, z0 + h + 0.012, mi)


def _wbox(mb, along, a0, a1, b0, b1, z0, z1, mi=0):
    if along == 'X':
        mb.box(a0, a1, b0, b1, z0, z1, mi)
    else:
        mb.box(b0, b1, a0, a1, z0, z1, mi)


def door_unit(M, name, along, a0, a1, b0, b1, hinge='a0', swing=+1, angle=0.0, z0=0.0, h=DOOR_H, layout='two', knob=True,
              frame=True):
    """Interior pre-hung door in a wall opening (a0..a1 along the wall, wall thickness b0..b1): jambs + casings on both
    faces (white), a 2-panel leaf (its own object, hinged at `hinge` end, swinging toward `swing` side by `angle`
    degrees) and a satin-nickel knob on both faces."""
    trim = MB()
    f = Face(along, b1, +1)
    depth = b1 - b0
    if frame:
        fen.interior_door_frame(f, trim, a0, a1, z0, z0 + h + 0.02, depth, mi=0)
        trim.build(f"{name}_Frame", [M['trim_int']])
    leaf = MB()
    la0, la1 = a0 + 0.02, a1 - 0.02
    dm = -depth / 2
    if layout == 'four':
        fu.panel_leaf_grid(f, leaf, la0, la1, z0 + 0.01, z0 + h, dm - 0.0175, dm + 0.0175, mi_out=0, mi_in=0)
    else:
        fen.panel_leaf(f, leaf, la0, la1, z0 + 0.01, z0 + h, dm - 0.0175, dm + 0.0175, layout=layout, mi_out=0, mi_in=0, raise_=0.007)
    kx = la1 - 0.065 if hinge == 'a0' else la0 + 0.065
    fen.lever(f, leaf, kx, z0 + 0.92, dm + 0.0175, side=1, mi=1, knob=knob)
    fen.lever(f, leaf, kx, z0 + 0.92, dm - 0.0175, side=-1, mi=1, knob=knob)
    ob = leaf.build(f"{name}_Leaf", [M['trim_int'], M['nickel']])
    # three satin-nickel butt hinges on the hinge jamb, visible from the side the door swings toward (photos 04, 05, 07)
    hg = MB()
    ha_ = la0 if hinge == 'a0' else la1
    dh = dm + swing * 0.0175
    for zc in (z0 + h - 0.18, z0 + h / 2, z0 + 0.28):
        px, py, _ = f.p(ha_, dh, 0)
        hg.cylinder(px, py, zc - 0.05, zc + 0.05, 0.0065, seg=10)
        f.box(hg, min(ha_, ha_ + (0.022 if hinge == 'a0' else -0.022)), max(ha_, ha_ + (0.022 if hinge == 'a0' else -0.022)),
              min(dh, dh + swing * 0.0015), max(dh, dh + swing * 0.0015), zc - 0.045, zc + 0.045)
        f.box(hg, min(ha_, ha_ - (0.022 if hinge == 'a0' else -0.022)), max(ha_, ha_ - (0.022 if hinge == 'a0' else -0.022)),
              min(dh, dh + swing * 0.0015), max(dh, dh + swing * 0.0015), zc - 0.045, zc + 0.045)
    hg.build(f"{name}_Hinges", [M['nickel']])
    if angle:
        ha = la0 if hinge == 'a0' else la1
        pivot = f.p(ha, dm + swing * 0.0175, 0)
        for v in ob.data.vertices:
            v.co.x -= pivot[0]; v.co.y -= pivot[1]
        ob.location = (pivot[0], pivot[1], 0.0)
        sgn = 1 if hinge == 'a0' else -1
        ob.rotation_euler = (0, 0, math.radians(angle) * sgn * swing * (1 if along == 'X' else -1))
    return ob


# ================================================================ floors + ceilings
def floors(M):
    lam, car = MB(), MB()
    zt = Z_MAIN
    # laminate: dining + kitchen + pantry (the foyer / stair foot / hall / powder / living floors: interior_front.py)
    lam.box(5.85, XR, 6.47, YR, zt - 0.02, zt)                                # dining + kitchen (+ the dining nook front)
    lam.box(PANTRY[0][0], XR, 6.9, PANTRY[1][1], zt - 0.02, zt)                  # pantry
    lam.build("Floor_Laminate", [M['laminate']])
    car.box(XB0 + EWT, 5.85, 6.47, YR, zt - 0.02, zt + 0.004)                  # great room
    car.build("Floor_Carpet", [M['carpet']])
    # transition strip at the great room / dining line
    t = MB()
    t.box(5.84, 5.86, 6.47, YR, zt, zt + 0.007)
    t.build("Floor_Transitions", [M['oak_stair']])
    # the structural slab under everything (hides the foundation from below-grade views)
    s = MB()
    s.box(GAR[1], XB1, YB0 + 0.25, GAR[3] + IWT, zt - 0.30, zt - 0.02)          # beside the garage (not under its bay)
    s.box(XB0, XB1, GAR[3] + IWT, YB1, zt - 0.30, zt - 0.02)                     # behind the garage
    s.box(BAY[0], BAY[1], BAY[2], YB0 + 0.25, zt - 0.30, zt - 0.02)
    s.build("Slab_Main", [M['concrete']])


def ceilings(M):
    c = MB()
    z0, z1 = ZC, ZC + 0.02
    c.box(XB0 + EWT, GAR[1], 6.35, YR, z0, z1)                                 # great room (west of the hall line)
    c.plate(GAR[1], XR, 1.75, YR, z0, z1, holes=[(ST_X0, XR, ST_Y0, ST_Y1)])  # foyer, hall, living rear, core, dining, kitchen
    c.box(BAY[0] + BWT, BAY[1] - BWT, BAY[2] + BWT, 1.75, z0, z1)                 # living room in the brick bay
    c.build("Ceiling_Main", [M['ceiling']])
    # drywall returns around the stairwell opening (2.50 .. 2.86), seen from the living room / stair
    r = MB()
    r.box(ST_X0, XR, ST_Y0 - 0.12, ST_Y0, z0, Z_UP + 0.02)
    r.box(ST_X0 - 0.12, ST_X0, ST_Y0, ST_YM, z0, Z_UP + 0.02)
    r.build("Stairwell_Returns", [M['paint_blue']])
    # their faces toward the well are the upper hall's beige (photo 15, INT_FRONT): skins from the ceiling to the upper floor
    rs = MB()
    skin(rs, 'X', ST_X0, XR, ST_Y0, +1, z0, Z_UP + 0.02)
    skin(rs, 'Y', ST_Y0, ST_YM, ST_X0, +1, z0, Z_UP + 0.02)
    rs.build("Stairwell_ReturnsWell", [M['paint_cream']])
    # garage ceiling (single storey, 2.55)
    g = MB()
    g.box(GAR[0] + EWT, GAR[1] - EWT, BWT, GAR[3], Z_C1 + 0.05, Z_C1 + 0.07)
    g.build("Ceiling_Garage", [M['drywall_white']])


# ================================================================ partitions, skins, doors
def partitions(M):
    w = MB()
    H = ZC + 0.02
    # hall east wall (x 7.20 .. 7.32) from the powder-door wall to the dining room, with the linen-closet door
    holed_wall(w, 'Y', SOUTH_Y, 6.47, HALL_X[1], HALL_X[1] + IWT, 0.0, H, holes=[(LINEN['y0'], LINEN['y1'], 0.0, DOOR_H + 0.02)])
    # the powder-door wall (y SOUTH_Y .. +IWT) from the hall to the stair's top riser line
    holed_wall(w, 'X', HALL_X[1], ST_X0, SOUTH_Y, PW['y0'], 0.0, H, holes=[(PW_DOOR[0], PW_DOOR[1], 0.0, DOOR_H + 0.02)])
    # linen closet (x 7.32 .. 8.40, y 5.92 .. 6.35) behind the dining room's south wall (y 6.35 .. 6.47)
    w.box(HALL_X[1] + IWT, DIN_EX + IWT, 6.35, 6.47, 0.0, H)
    # dining east wall = powder west wall (x 8.40 .. 8.52), then the pier body to its north face (y 8.10)
    w.box(DIN_EX, DIN_EX + IWT, PW['y0'], PIER['y0'], 0.0, H)
    w.box(PIER['x0'], PIER['x1'], PIER['y0'] - IWT, PIER['y1'], 0.0, H)
    # powder room east wall; the refrigerator wall (thick behind the stairwell) to the return
    w.box(PW['x1'], PW['x1'] + IWT, PW['y0'], PW['y1'], 0.0, H)
    w.box(PIER['x1'], ST_X0, FRIDGE_Y - IWT, FRIDGE_Y, 0.0, H)
    w.box(ST_X0, RETURN_X, ST_Y1 + IWT, FRIDGE_Y, 0.0, H)
    # stairwell back wall (main-floor part), from the powder room's east wall to the right wall
    w.box(PW['x1'], XR, ST_Y1, ST_Y1 + IWT, 0.0, H)
    # the return (fridge alcove east wall = pantry west wall) from the stairwell back wall to the angled wall
    w.box(RETURN_X, RETURN_X + IWT, ST_Y1 + IWT, PANTRY[0][1], 0.0, H)
    # the stub at the end of the range-wall counter run, from the angled wall to the right wall
    w.box(PANTRY[1][0], XR, PANTRY[1][1] - IWT, PANTRY[1][1], 0.0, H)
    # landing-enclosure ("fruit") wall at the living room's rear-right
    w.box(FRUIT_X0, XR, ST_Y0, ST_Y0 + 0.12, 0.0, H)
    # foyer west wall (face x 7.15) with the coat-closet door, and the closet's north wall toward the hall (photos 04, 05)
    holed_wall(w, 'Y', 1.75, COAT_Y1, FOYER_WX - IWT, FOYER_WX, 0.0, H, holes=[(COAT['y0'], COAT['y1'], 0.0, DOOR_H + 0.02)])
    w.box(GAR[1], FOYER_WX, COAT_Y1 - IWT, COAT_Y1, 0.0, H)
    w.build("Partitions_Main", [M['paint_blue']])
    # pantry 45-degree wall with its door opening (built as a slab in its own frame)
    (px0, py0), (px1, py1) = PANTRY
    L = math.hypot(px1 - px0, py1 - py0)
    ux, uy = (px1 - px0) / L, (py1 - py0) / L
    nx, ny = uy, -ux                                   # normal toward the kitchen
    if nx * (10.0 - px0) + ny * (10.0 - py0) < 0:
        nx, ny = -nx, -ny
    pw = MB()
    d0, d1 = (L - 0.78) / 2, (L + 0.78) / 2           # 2'6" leaf + jambs (photos 12, 13: centred between the corners)
    for (a0, a1, z0, z1) in ((-IWT, d0, 0.0, H), (d1, L + IWT, 0.0, H), (d0, d1, DOOR_H + 0.02, H)):
        P = lambda a, n, z: (px0 + ux * a + nx * n, py0 + uy * a + ny * n, z)
        pw.hexa([P(a0, -0.12, z0), P(a1, -0.12, z0), P(a1, 0.0, z0), P(a0, 0.0, z0),
                 P(a0, -0.12, z1), P(a1, -0.12, z1), P(a1, 0.0, z1), P(a0, 0.0, z1)])
    pw.build("Pantry_Wall", [M['paint_blue']])
    # the pantry door (2 x 2 panel leaf, closed, knob on its right as seen from the kitchen): built along X, then mapped
    obs = [door_unit(M, "Pantry_Door", 'X', d0, d1, -0.12, 0.0, hinge='a0', layout='four')]
    for suffix in ("_Frame", "_Hinges"):
        extra = bpy.data.objects.get("Pantry_Door" + suffix)
        if extra is not None:
            obs.append(extra)
    fu.transform_objects(obs, (px0, py0), (ux, uy), (nx, ny))
    return (px0, py0, ux, uy, nx, ny, L, d0, d1)


def skins(M, pantry):
    """Paint skins over every visible main-floor wall face (blue), the stairwell (cream), the garage (white)."""
    blue, cream, white = MB(), MB(), MB()
    base = MB()
    H = ZC
    op = {o['name']: o for o in OPENINGS}
    def hole(o):
        return (o['a0'], o['a1'], o['z0'], o['z1'])
    fd = op['front_door']
    # ---- foyer / living (open plan)
    skin(blue, 'X', GAR[1], BAY[0], 1.75, +1, 0, H, [hole(fd)])                                  # door wall
    baseboard(base, 'X', GAR[1], BAY[0], 1.75, +1, gaps=[(fd['a0'] - 0.07, fd['a1'] + 0.07)])
    skin(blue, 'Y', COAT_Y1, 6.47, GAR[1], +1, 0, H, [(GENTRY['y0'], GENTRY['y1'], 0, DOOR_H + 0.02)])            # hall west wall
    baseboard(base, 'Y', COAT_Y1, 6.47, GAR[1], +1, gaps=[(GENTRY['y0'] - 0.07, GENTRY['y1'] + 0.07)])
    skin(blue, 'Y', 1.75, COAT_Y1, FOYER_WX, +1, 0, H, [(COAT['y0'], COAT['y1'], 0, DOOR_H + 0.02)])                # foyer west wall
    baseboard(base, 'Y', 1.75, COAT_Y1, FOYER_WX, +1, gaps=[(COAT['y0'] - 0.07, COAT['y1'] + 0.07)])
    skin(blue, 'X', GAR[1], FOYER_WX + 0.004, COAT_Y1, +1, 0, H)                                                  # closet N wall (hall)
    baseboard(base, 'X', GAR[1], FOYER_WX, COAT_Y1, +1)
    skin(white, 'Y', 1.75, COAT_Y1 - IWT, GAR[1], +1, 0, H)                                                       # closet interior
    skin(white, 'Y', 1.75, COAT_Y1 - IWT, FOYER_WX - IWT, -1, 0, H, [(COAT['y0'], COAT['y1'], 0, DOOR_H + 0.02)])
    skin(white, 'X', GAR[1], FOYER_WX - IWT, COAT_Y1 - IWT, -1, 0, H)
    skin(blue, 'Y', BAY[2] + BWT, 1.75, BAY[0] + BWT, +1, 0, H)                                    # porch return (living side)
    skin(blue, 'X', BAY[0] - 0.004, BAY[0] + BWT + 0.004, 1.75, +1, 0, H)                           # its end, seen from the foyer
    skin(blue, 'Y', 1.75, 1.75 + 0.01, BAY[0], -1, 0, H)
    baseboard(base, 'Y', BAY[2] + BWT, 1.75, BAY[0] + BWT, +1)
    lw = op['living_win']
    skin(blue, 'X', BAY[0] + BWT, BAY[1] - BWT, BAY[2] + BWT, +1, 0, H, [hole(lw)])                 # bay front
    baseboard(base, 'X', BAY[0] + BWT, BAY[1] - BWT, BAY[2] + BWT, +1)
    skin(blue, 'Y', BAY[2] + BWT, 1.5, BAY[1] - BWT, -1, 0, H)                                     # bay right
    baseboard(base, 'Y', BAY[2] + BWT, 1.5, BAY[1] - BWT, -1)
    skin(blue, 'X', BAY[1] - BWT, XR, 1.5, +1, 0, H)                                               # little jog
    skin(blue, 'Y', 1.5, ST_Y0, XR, -1, 0, H)                                                      # right wall (living)
    baseboard(base, 'Y', 1.5, ST_Y0, XR, -1)
    skin(blue, 'X', FRUIT_X0, XR, ST_Y0, -1, 0, H)                                                 # the fruit wall
    baseboard(base, 'X', FRUIT_X0, XR, ST_Y0, -1)
    skin(blue, 'Y', ST_Y0, ST_Y0 + 0.12, FRUIT_X0, -1, 0, H)                                       # its end
    # stair foot + hall
    skin(blue, 'X', HALL_X[1], ST_X0, SOUTH_Y, -1, 0, H, [(PW_DOOR[0], PW_DOOR[1], 0, DOOR_H + 0.02)])
    baseboard(base, 'X', HALL_X[1], ST_X0, SOUTH_Y, -1, gaps=[(PW_DOOR[0] - 0.07, PW_DOOR[1] + 0.07)])
    skin(blue, 'Y', SOUTH_Y, 6.47, HALL_X[1], -1, 0, H, [(LINEN['y0'], LINEN['y1'], 0, DOOR_H + 0.02)])
    baseboard(base, 'Y', SOUTH_Y, 6.47, HALL_X[1], -1, gaps=[(LINEN['y0'] - 0.07, LINEN['y1'] + 0.07)])
    # linen closet interior (x 7.32 .. 8.46, y 5.99 .. 6.35)
    lx0, lx1, ly0, ly1 = HALL_X[1] + IWT, DIN_EX, PW['y0'], 6.35
    skin(white, 'Y', ly0, ly1, lx1, -1, 0, H)
    skin(white, 'X', lx0, lx1, ly0, +1, 0, H)
    skin(white, 'X', lx0, lx1, ly1, -1, 0, H)
    # ---- great room / dining / kitchen
    skin(blue, 'Y', 6.47, YR, XB0 + EWT, +1, 0, H)                                             # west wall (fireplace)
    baseboard(base, 'Y', 6.47, YR, XB0 + EWT, +1, gaps=[(FP['y0'], FP['y1'])])
    rear = [hole(op[n]) for n in ('great_win', 'slider', 'kitchen_win')]
    skin(blue, 'X', XB0 + EWT, XR, YR, -1, 0, H, rear)
    baseboard(base, 'X', XB0 + EWT, PIER['x1'], YR, -1, gaps=[(op['slider']['a0'] - 0.07, op['slider']['a1'] + 0.07)])
    skin(blue, 'X', XB0 + EWT, GAR[1], 6.47, +1, 0, H)                                            # garage wall (great side)
    baseboard(base, 'X', XB0 + EWT, GAR[1], 6.47, +1)
    skin(blue, 'X', HALL_X[1], DIN_EX, 6.47, +1, 0, H)                                            # dining south wall
    baseboard(base, 'X', HALL_X[1], DIN_EX, 6.47, +1)
    skin(blue, 'Y', 6.47, PIER['y1'], DIN_EX, -1, 0, H)                                           # dining east wall (medallion)
    baseboard(base, 'Y', 6.47, PIER['y1'], DIN_EX, -1)
    skin(blue, 'X', DIN_EX - 0.004, PIER['x1'] + 0.004, PIER['y1'], +1, 0, H)                     # pier north face
    baseboard(base, 'X', DIN_EX, PIER['x1'], PIER['y1'], +1)
    skin(blue, 'Y', FRIDGE_Y, PIER['y1'], PIER['x1'], +1, 0, H)                                   # pier east face (kitchen)
    skin(blue, 'X', PIER['x1'], RETURN_X, FRIDGE_Y, +1, 0, H)                                     # refrigerator wall
    skin(blue, 'Y', FRIDGE_Y, PANTRY[0][1], RETURN_X, -1, 0, H)                                   # fridge alcove return
    skin(blue, 'X', PANTRY[1][0], XR, PANTRY[1][1], +1, 0, H)                                     # stub at the counter run's end
    skin(blue, 'Y', PANTRY[1][1], YR, XR, -1, 0, H)                                            # right wall (range)
    # angled pantry wall skin (kitchen side), with the door hole
    px0, py0, ux, uy, nx, ny, L, d0, d1 = pantry
    P = lambda a, n, z: (px0 + ux * a + nx * n, py0 + uy * a + ny * n, z)
    for (a0, a1, z0, z1) in ((0.0, d0, 0, H), (d1, L, 0, H), (d0, d1, DOOR_H + 0.02, H)):
        blue.hexa([P(a0, 0.002, z0), P(a1, 0.002, z0), P(a1, 0.006, z0), P(a0, 0.006, z0),
                   P(a0, 0.002, z1), P(a1, 0.002, z1), P(a1, 0.006, z1), P(a0, 0.006, z1)])
    for (a0, a1) in ((0.0, d0 - 0.07), (d1 + 0.07, L)):
        base.hexa([P(a0, 0.006, 0), P(a1, 0.006, 0), P(a1, 0.02, 0), P(a0, 0.02, 0),
                   P(a0, 0.006, 0.095), P(a1, 0.006, 0.095), P(a1, 0.02, 0.095), P(a0, 0.02, 0.095)])
    # ---- powder room
    skin(blue, 'X', PW['x0'], PW['x1'], PW['y0'], +1, 0, H, [(PW_DOOR[0], PW_DOOR[1], 0, DOOR_H + 0.02)])
    skin(blue, 'X', PW['x0'], PW['x1'], PW['y1'], -1, 0, H)
    skin(blue, 'Y', PW['y0'], PW['y1'], PW['x0'], +1, 0, H)
    skin(blue, 'Y', PW['y0'], PW['y1'], PW['x1'], -1, 0, H)
    baseboard(base, 'Y', PW['y0'], PW['y1'], PW['x1'], -1)
    baseboard(base, 'X', PW['x0'], PW['x1'], PW['y0'], +1, gaps=[(PW_DOOR[0] - 0.07, PW_DOOR[1] + 0.07)])
    # ---- stairwell (cream, both storeys' height on the landing side walls)
    lw2 = op['landing_win']
    skin(cream, 'Y', ST_Y0 + 0.12, ST_Y1, XR, -1, 0, Z_C2, [hole(lw2)])                           # right wall at the landing
    skin(cream, 'X', ST_X0, XR, ST_Y1, -1, 0, Z_C2)                                               # back wall
    skin(cream, 'X', FRUIT_X0, XR, ST_Y0 + 0.12, +1, Z_LAND, ZC + 0.34)                           # fruit wall, landing side
    blue.build("Skin_Blue", [M['paint_blue']])
    cream.build("Skin_Stairwell", [M['paint_cream']])
    base.build("Baseboards_Main", [M['trim_int']])
    # ---- garage (white drywall on its interior faces)
    gx0, gx1 = GAR[0] + EWT, GAR[1] - EWT
    skin(white, 'X', gx0, gx1, GAR[3], -1, Z_GAR, Z_C1 + 0.05)
    skin(white, 'Y', BWT, GAR[3], gx0, +1, Z_GAR, Z_C1 + 0.05)
    skin(white, 'Y', BWT, GAR[3], gx1, -1, Z_GAR, Z_C1 + 0.05, [(GENTRY['y0'], GENTRY['y1'], 0.0, DOOR_H + 0.02)])
    gd = op['garage_door']; gw = op['garage_win']
    skin(white, 'X', gx0, gx1, BWT, +1, Z_GAR, Z_C1 + 0.05, [hole(gd), hole(gw)])
    white.build("Skin_White", [M['drywall_white']])


def doors(M):
    # coat closet (on the foyer's west wall, x 7.15) and the garage entry (hall west wall): leaves closed, knobs
    door_unit(M, "Door_Coat", 'Y', COAT['y0'], COAT['y1'], FOYER_WX - IWT, FOYER_WX, hinge='a0')
    door_unit(M, "Door_Garage", 'Y', GENTRY['y0'], GENTRY['y1'], GAR[1] - EWT, GAR[1])
    door_unit(M, "Door_Powder", 'X', PW_DOOR[0], PW_DOOR[1], SOUTH_Y, PW['y0'], hinge='a0', swing=-1, angle=95)   # opens OUT (07)
    door_unit(M, "Door_Linen", 'Y', LINEN['y0'], LINEN['y1'], HALL_X[1], HALL_X[1] + IWT, hinge='a0', layout='four')
    # coat closet (x 6.0 .. 7.03): a shelf and a rod
    sh = MB()
    sh.box(GAR[1] + 0.01, FOYER_WX - IWT - 0.01, 1.76, COAT_Y1 - IWT - 0.01, 1.70, 1.72)
    sh.cylinder(GAR[1] + 0.33, (1.75 + COAT_Y1 - IWT) / 2, 1.62, 1.63, 0.012, seg=8)
    sh.build("CoatCloset_Shelf", [M['trim_int']])


# ================================================================ fireplace chase position
FP = dict(y0=8.09, y1=9.95, depth=0.545)         # chase on the west wall (INT_CAM joint 09+10 solve: +/- 0.015, depth +/- 0.05)


# ================================================================ kitchen
def kitchen(M):
    """The kitchen: cabinets, counters, appliances (houses/stanford/ig_kitchen.py, a helper of this module)."""
    from . import ig_kitchen
    return ig_kitchen.kitchen(M)


def _counter(mb, x0, x1, y0, y1, z, sink=None):
    if sink:
        sx0, sx1, sy0, sy1 = sink
        mb.plate(x0, x1, y0, y1, z, z + 0.035, holes=[(sx0, sx1, sy0, sy1)])
    else:
        mb.box(x0, x1, y0, y1, z, z + 0.035)


def _panel(mb, f, a0, a1, z0, z1):
    f.box(mb, a0, a1, 0.0, 0.006, z0, z1, 1)


def _arched(mb, f, a0, a1, z0, z1, mi=0):
    """Cabinet door with a cathedral-arch raised panel (photos 12-14): a 19 mm frame, a sunken bevel ring and a raised
    field whose top follows a segmental arch, so the rails and the arch throw readable shadow lines."""
    f.box(mb, a0, a1, 0.0, 0.019, z0, z1, mi)
    m = 0.058
    fa0, fa1, fz0, fz1 = a0 + m, a1 - m, z0 + m, z1 - m
    n = 10
    w = fa1 - fa0
    rise = min(0.07, w * 0.2)
    for i in range(n):
        u0, u1 = i / n, (i + 1) / n
        za = fz1 - rise + rise * math.sin(math.pi * (u0 + u1) / 2)
        f.box(mb, fa0 + w * u0, fa0 + w * u1, 0.019, 0.025, fz0, za, mi)                     # bevel step
        f.box(mb, fa0 + w * u0 + (0.022 if i == 0 else 0), fa0 + w * u1 - (0.022 if i == n - 1 else 0), 0.025, 0.034,
              fz0 + 0.022, za - 0.022, mi)                                                  # raised field
    # frame rail edges (a thin proud bead around the opening)
    f.box(mb, a0 + m - 0.012, a0 + m - 0.004, 0.019, 0.027, z0 + m - 0.012, z1 - m + 0.012, mi)
    f.box(mb, a1 - m + 0.004, a1 - m + 0.012, 0.019, 0.027, z0 + m - 0.012, z1 - m + 0.012, mi)
    f.box(mb, a0 + m - 0.012, a1 - m + 0.012, 0.019, 0.027, z0 + m - 0.012, z0 + m - 0.004, mi)


def _fronts(mb, hw, f, a0, a1, z0, z1, ndoors, along='X', drawer=True):
    W = (a1 - a0) / ndoors
    zd = z1 - 0.17
    for i in range(ndoors):
        b0, b1 = a0 + i * W + 0.003, a0 + (i + 1) * W - 0.003
        if drawer:
            f.box(mb, b0, b1, 0.0, 0.019, zd + 0.004, z1 - 0.004, 0)
            f.box(hw, (b0 + b1) / 2 - 0.06, (b0 + b1) / 2 + 0.06, 0.019, 0.032, zd + 0.07, zd + 0.085, 0)
        _arched(mb, f, b0, b1, z0 + 0.004, zd - 0.004)
        hx = b1 - 0.04 if i % 2 == 0 else b0 + 0.04
        f.box(hw, hx - 0.006, hx + 0.006, 0.019, 0.034, zd - 0.20, zd - 0.08, 0)


def _base_cabinet(cab, hw, f, a0, a1, wall_b, dep, zb, zt, kind, along='X', sign=-1):
    if along == 'X':
        if sign < 0:
            cab.box(a0, a1, wall_b - dep, wall_b, zb, zt)
        else:
            cab.box(a0, a1, wall_b, wall_b + dep, zb, zt)
    else:
        cab.box(wall_b - dep, wall_b, a0, a1, zb, zt)
    if kind in ('db', 'sink'):
        _fronts(cab, hw, f, a0, a1, zb, zt, 2 if a1 - a0 > 0.55 else 1, along, drawer=(kind != 'sink'))
    elif kind == 'drawers':
        n = 3
        hh = (zt - zb) / n
        for i in range(n):
            f.box(cab, a0 + 0.003, a1 - 0.003, 0.0, 0.019, zb + i * hh + 0.004, zb + (i + 1) * hh - 0.004, 0)
            f.box(hw, (a0 + a1) / 2 - 0.07, (a0 + a1) / 2 + 0.07, 0.019, 0.032, zb + (i + 0.6) * hh, zb + (i + 0.6) * hh + 0.015, 0)
    elif kind == 'corner':
        _fronts(cab, hw, f, a0, a1, zb, zt, 1, along)


def _uppers(cab, hw, f, a0, a1, wall_b, z0, z1, n=2, along='X', sign=-1, depth=0.33):
    if along == 'X':
        if sign < 0:
            cab.box(a0, a1, wall_b - depth, wall_b, z0, z1)
        else:
            cab.box(a0, a1, wall_b, wall_b + depth, z0, z1)
    else:
        cab.box(wall_b - depth, wall_b, a0, a1, z0, z1)
    W = (a1 - a0) / n
    for i in range(n):
        b0, b1 = a0 + i * W + 0.003, a0 + (i + 1) * W - 0.003
        _arched(cab, f, b0, b1, z0 + 0.004, z1 - 0.004)
        hx = b1 - 0.04 if i % 2 == 0 else b0 + 0.04
        f.box(hw, hx - 0.006, hx + 0.006, 0.019, 0.034, z0 + 0.05, z0 + 0.16, 0)
    f.box(cab, a0 - 0.03, a1 + 0.03, 0.0, 0.05, z1, z1 + 0.05, 0)          # crown


# ================================================================ great room fireplace
def fireplace(M):
    """Direct-vent gas fireplace in a painted chase centred on the west wall (photos 09, 10; measured through p10):
    a painted mantel (flat outer legs, fluted pilasters with plinths and capitals, a frieze, bed moulding, a stepped
    crown and a 1.39 m shelf), a field of 12" travertine-look tiles with real joints around a black louvred firebox
    (glass front, ceramic logs, a scrolled grate bar) and a flush tile hearth."""
    x0 = XB0 + EWT
    y0, y1, d = FP['y0'], FP['y1'], FP['depth']
    xf = x0 + d
    ym = (y0 + y1) / 2
    ta0, ta1, tz1 = ym - 0.635, ym + 0.635, 1.074
    fa0, fa1, fz0, fz1 = ym - 0.466, ym + 0.466, 0.02, 0.885
    # the chase: solid behind the firebox, its front 0.42 m open where the firebox sits
    ch = MB()
    ch.box(x0, xf - 0.42, y0, y1, 0.0, ZC)
    holed_wall(ch, 'Y', y0, y1, xf - 0.42, xf, 0.0, ZC, holes=[(fa0, fa1, 0.0, fz1)])
    ch.build("Fireplace_Chase", [M['paint_blue']])
    f = Face('Y', xf, +1)
    tile, grout, hearth, mantel, black, glass, logs = MB(), MB(), MB(), MB(), MB(), MB(), MB()
    # --- tile field (1.27 x 1.07) with 3 mm joints over a grout backer; firebox opening 0.93 x 0.87
    for (a0_, a1_, z0_, z1_) in ((ta0, fa0, 0.0, tz1), (fa1, ta1, 0.0, tz1), (fa0, fa1, fz1, tz1)):
        f.box(grout, a0_, a1_, 0.0, 0.006, z0_, z1_, 0)
    g = 0.0015
    def T(a0, a1, z0, z1):
        f.box(tile, a0 + g, a1 - g, 0.006, 0.014, z0 + g, z1 - g, 0)
    for (a0, a1) in ((ta0, fa0), (fa1, ta1)):                       # side columns: rows at 0.49 / 0.89 (photo 10)
        for (z0, z1) in ((0.0, 0.49), (0.49, 0.89), (0.89, tz1)):
            T(a0, a1, z0, z1)
    for (a0, a1) in ((fa0, ym - 0.155), (ym - 0.155, ym + 0.155), (ym + 0.155, fa1)):   # top row joints (photo 10)
        T(a0, a1, 0.89, tz1)
    # --- hearth: one row of 12" tiles flush with the carpet, 0.30 deep, wider than the mantel
    hy0, hy1 = y0 - 0.11, y1 + 0.02
    n = 7
    for i in range(n):
        a0 = hy0 + (hy1 - hy0) * i / n
        a1 = hy0 + (hy1 - hy0) * (i + 1) / n
        hearth.box(xf + g, xf + 0.30 - g, a0 + g, a1 - g, 0.0, 0.012)
    grout.box(xf, xf + 0.30, hy0, hy1, 0.0, 0.008)
    # --- mantel (painted poplar): legs, fluted pilasters, capitals, frieze, bed moulding, crown, shelf
    for s_ in (-1, 1):
        la0, la1 = sorted((ym + s_ * 0.925, ym + s_ * 0.805))
        f.box(mantel, la0, la1, 0.0, 0.03, 0.0, tz1, 0)                                # flat outer leg
        pa0, pa1 = sorted((ym + s_ * 0.805, ym + s_ * 0.635))
        f.box(mantel, pa0 - 0.008, pa1 + 0.008, 0.0, 0.068, 0.0, 0.13, 0)              # plinth
        f.box(mantel, pa0 - 0.008, pa1 + 0.008, 0.0, 0.072, 0.13, 0.145, 0)
        f.box(mantel, pa0, pa1, 0.0, 0.05, 0.145, tz1, 0)                              # pilaster
        nfl = 9
        for k in range(nfl + 1):                                                        # fillets between 9 flutes
            u = pa0 + 0.012 + (pa1 - pa0 - 0.024) * k / nfl
            f.box(mantel, u - 0.0035, u + 0.0035, 0.05, 0.057, 0.17, tz1 - 0.03, 0)
        f.box(mantel, pa0 + 0.006, pa1 - 0.006, 0.05, 0.057, 0.145, 0.17, 0)
        f.box(mantel, pa0 + 0.006, pa1 - 0.006, 0.05, 0.057, tz1 - 0.03, tz1, 0)
        f.box(mantel, pa0 - 0.01, pa1 + 0.01, 0.0, 0.07, tz1, tz1 + 0.026, 0)          # capital
    f.box(mantel, ta0 - 0.012, ta1 + 0.012, 0.0, 0.03, tz1 - 0.012, tz1, 0)            # opening head bead
    f.box(mantel, ym - 0.925, ym + 0.925, 0.0, 0.045, tz1 + 0.026, 1.30, 0)             # frieze
    f.box(mantel, ym - 0.90, ym + 0.90, 0.0, 0.066, tz1 + 0.026, tz1 + 0.056, 0)       # bed moulding band
    f.box(mantel, ym - 0.905, ym + 0.905, 0.0, 0.07, tz1 + 0.056, tz1 + 0.066, 0)
    f.box(mantel, ym - 0.88, ym + 0.88, 0.045, 0.05, 1.16, 1.27, 0)                     # raised frieze panel
    for k in range(6):                                                                 # stepped crown cove 1.30-1.37
        t = (k + 1) / 6
        f.box(mantel, ym - 0.925 - 0.03 * t, ym + 0.925 + 0.03 * t, 0.0, 0.05 + 0.10 * t ** 1.5, 1.30 + 0.0117 * k, 1.30 + 0.0117 * (k + 1), 0)
    f.box(mantel, y0 + 0.012, y1 - 0.012, 0.0, 0.19, 1.37, 1.395, 0)             # shelf
    f.box(mantel, y0 + 0.02, y1 - 0.02, 0.0, 0.195, 1.375, 1.39, 0)
    # --- firebox
    fu.gas_firebox(black, glass, logs, Face('Y', xf + 0.012, +1), fa0, fa1, fz0, fz1, mi=0, mi_glass=0, mi_log=0, mi_inner=1)
    add_light("L_Firebox_Bounce", 'POINT', (xf - 0.10, ym, 0.72), 22.0, color=(1.0, 0.95, 0.9), size=0.2, coll=LC)
    grout.build("Fireplace_Grout", [M['grout']])
    tile.build("Fireplace_Tile", [M['fire_tile']])
    hearth.build("Fireplace_Hearth", [M['fire_tile_h']])
    mantel.build("Fireplace_Mantel", [M['trim_int']])
    black.build("Fireplace_Firebox", [M['appliance_black'], M['refractory']])
    glass.build("Fireplace_Glass", [M['firebox_glass']])
    logs.build("Fireplace_Logs", [M['ceramic_log']], smooth=True)
    return xf, ym


# per-photo staging: objects hidden for the listed cameras (the photographer moved them; restored for every other camera)
PHOTO_HIDE = {
    'p12': ("Dining_ChairsEast", "Dining_SeatsEast", "Dining_ChairSouth", "Dining_SeatSouth"),   # 12: the photographer stands there
    'p13': ("Dining_ChairsEast", "Dining_SeatsEast", "Dining_ChairNorth", "Dining_SeatNorth"),   # 13: ... and at the north end
}


PHOTO_HIDE['p08'] = ("Great_Chaise",)
PHOTO_ONLY = {"Great_ChaiseP08": ('p08',)}               # objects shown only for these photo cameras


def before_render(S, name):
    managed = {n for v in PHOTO_HIDE.values() for n in v} | set(PHOTO_ONLY)
    hide = set(PHOTO_HIDE.get(name, ())) | {n for n, cams in PHOTO_ONLY.items() if name not in cams}
    for n in managed:
        ob = bpy.data.objects.get(n)
        if ob is not None:
            ob.hide_render = n in hide


def _hide_photo_only():
    for n in PHOTO_ONLY:
        ob = bpy.data.objects.get(n)
        if ob is not None:
            ob.hide_render = True


def build(M):
    from . import ig_staging as st
    _mats(M)
    floors(M)
    ceilings(M)
    pantry = partitions(M)
    skins(M, pantry)
    doors(M)
    kit = kitchen(M)
    fireplace(M)
    st.great_room(M)
    st.dining(M)
    kitchen_accessories(M, kit)
    st.lights(M)       # foyer, living, stair, powder and garage lights: interior_front.py
    _hide_photo_only()  # the default (film / non-photo) state; before_render shows them for their photo


# ================================================================ staging helpers
def upholstered_sofa(mb, x, y, w, d, rot, mi_body=0, mi_leg=1, arm='rolled', seat_h=0.44, back_h=0.86, cushions=3):
    """Transitional sofa facing its own -Y: rolled arms, loose seat + back cushions, tapered dark legs."""
    from archviz.mesh import rot2
    def R(cx, cy, cz, sx, sy, sz, mi, r=0.05, puff=0.0):
        px, py = rot2(x + cx, y + cy, x, y, rot)
        mb.rcbox(px, py, cz, sx, sy, sz, r, mi, rot, puff=puff)
    aw = 0.20
    R(0, 0.05, 0.28, w - 0.04, d - 0.1, 0.22, mi_body, r=0.04)                       # deck/base
    sw = (w - 2 * aw) / cushions
    for i in range(cushions):
        cx = -w / 2 + aw + sw * (i + 0.5)
        R(cx, -0.06, seat_h - 0.05, sw - 0.02, d - 0.30, 0.16, mi_body, r=0.07, puff=0.5)
        R(cx, d / 2 - 0.16, seat_h + 0.25, sw - 0.02, 0.2, back_h - seat_h - 0.08, mi_body, r=0.08, puff=0.4)
    R(0, d / 2 - 0.06, (back_h - 0.1) / 2 + 0.12, w - 0.1, 0.12, back_h - 0.12, mi_body, r=0.05)    # frame back
    for s in (-1, 1):
        R(s * (w / 2 - aw / 2), 0.0, 0.40, aw, d - 0.02, 0.36, mi_body, r=0.08, puff=0.3)
        px, py = rot2(x + s * (w / 2 - aw / 2), y - d / 2 + 0.08, x, y, rot)
        mb.cylinder(px, py, 0.55, 0.62, 0.105, seg=16, mi=mi_body)                    # rolled arm front
    for sx in (-1, 1):
        for sy in (-1, 1):
            px, py = rot2(x + sx * (w / 2 - 0.08), y + sy * (d / 2 - 0.08), x, y, rot)
            mb.cylinder(px, py, 0.0, 0.18, 0.025, 0.018, seg=8, mi=mi_leg)


def pillows(mb, specs, mi):
    """specs: (x, y, z, w, rot, pitch) square throw pillows leaning back."""
    for i, (px, py, pz, w, rot, pitch) in enumerate(specs):
        mb.pillow_sq(px, py, pz, w, w, 0.15, mi, rot=rot, pitch=pitch, seed=i + 3)


def slipper_chair(mb, x, y, rot, mi_up=0, mi_leg=1):
    from archviz.mesh import rot2
    def R(cx, cy, cz, sx, sy, sz, mi, r=0.03, puff=0.0):
        px, py = rot2(x + cx, y + cy, x, y, rot)
        mb.rcbox(px, py, cz, sx, sy, sz, r, mi, rot, puff=puff)
    R(0, 0, 0.40, 0.58, 0.60, 0.14, mi_up, r=0.05, puff=0.4)
    R(0, 0.27, 0.74, 0.58, 0.10, 0.62, mi_up, r=0.04)
    for sx in (-1, 1):
        for sy in (-1, 1):
            px, py = rot2(x + sx * 0.24, y + sy * 0.25, x, y, rot)
            mb.cylinder(px, py, 0.0, 0.34, 0.022, 0.016, seg=8, mi=mi_leg)


def oval_table(mb_wood, mb_glass, x, y, a, b, h, rot=0.0, shelf=True):
    """Oval glass-top cocktail table: dark wood rim + four sabre legs + a lower shelf (photos 04-06)."""
    import math as _mm
    seg = 40
    ring = []
    for i in range(seg):
        t = 2 * _mm.pi * i / seg
        ring.append((x + a * _mm.cos(t) * _mm.cos(rot) - b * _mm.sin(t) * _mm.sin(rot), y + a * _mm.cos(t) * _mm.sin(rot) + b * _mm.sin(t) * _mm.cos(rot)))
    inner = [(x + (px - x) * 0.86, y + (py - y) * 0.82) for px, py in ring]
    for i in range(seg):
        j = (i + 1) % seg
        p0, p1, q1, q0 = ring[i], ring[j], inner[j], inner[i]
        mb_wood.hexa([(p0[0], p0[1], h - 0.05), (p1[0], p1[1], h - 0.05), (q1[0], q1[1], h - 0.05), (q0[0], q0[1], h - 0.05),
                      (p0[0], p0[1], h), (p1[0], p1[1], h), (q1[0], q1[1], h), (q0[0], q0[1], h)])
    mb_glass.v.extend([(px, py, h - 0.012) for px, py in inner] + [(x, y, h - 0.012)])
    base = len(mb_glass.v) - seg - 1
    for i in range(seg):
        mb_glass.f.append((base + i, base + (i + 1) % seg, base + seg)); mb_glass.fm.append(0)
    for k, t in enumerate((0.55, 2.59, 3.69, 5.73)):
        cx, cy = x + a * 0.78 * _mm.cos(t), y + b * 0.72 * _mm.sin(t)
        mb_wood.path_tube([(cx, cy, h - 0.05), (cx + 0.02 * _mm.cos(t), cy + 0.02 * _mm.sin(t), h * 0.5), (cx + 0.07 * _mm.cos(t), cy + 0.07 * _mm.sin(t), 0.02)], 0.022, seg=8)
    if shelf:
        mb_wood.cylinder(x, y, 0.16, 0.18, a * 0.6, seg=seg, ry=b * 0.6)


def frame_art(mb, along, a0, a1, b, s, z0, z1, mi_frame=0, mi_art=1, fw=0.06, d=0.035):
    """A framed painting on a wall at plane b (room side s): a moulded frame ring standing proud of a recessed canvas."""
    def slab(c0, c1, e0, e1, h0, h1, mi):
        lo, hi = b + s * c0, b + s * c1
        _wbox(mb, along, e0, e1, min(lo, hi), max(lo, hi), h0, h1, mi)
    slab(0.004, 0.014, a0 + fw * 0.5, a1 - fw * 0.5, z0 + fw * 0.5, z1 - fw * 0.5, mi_art)       # canvas (stretcher depth)
    slab(0.004, d, a0, a1, z0, z0 + fw, mi_frame)
    slab(0.004, d, a0, a1, z1 - fw, z1, mi_frame)
    slab(0.004, d, a0, a0 + fw, z0 + fw, z1 - fw, mi_frame)
    slab(0.004, d, a1 - fw, a1, z0 + fw, z1 - fw, mi_frame)
    slab(d, d + 0.008, a0 + fw * 0.3, a1 - fw * 0.3, z0 + fw * 0.3, z0 + fw * 0.7, mi_frame)   # raised inner bead
    slab(d, d + 0.008, a0 + fw * 0.3, a1 - fw * 0.3, z1 - fw * 0.7, z1 - fw * 0.3, mi_frame)


def swag(mb, x0, x1, y, ztop, sag, depth=0.10, n=28, m=8, mi=0, folds=5):
    """A draped valance swag across x0..x1 hanging from ztop in front of the plane y; it bulges toward -y for a
    positive `depth` and toward +y for a negative one (the room side)."""
    secs = []
    for i in range(n + 1):
        u = i / n
        x = x0 + (x1 - x0) * u
        zb = ztop - 0.10 - sag * math.sin(math.pi * u)
        front, back = [], []
        for k in range(m + 1):
            t = k / m
            z = ztop - t * (ztop - zb)
            bulge = depth * math.sin(math.pi * min(1.0, t * 1.1)) * (0.35 + 0.65 * math.sin(math.pi * u))
            bulge += 0.012 * math.sin(folds * math.pi * t + 3 * u)
            front.append((x, y - bulge - 0.008, z))
            back.append((x, y - bulge * 0.85, z + 0.004))
        secs.append(front + list(reversed(back)))
    mb.sweep(secs, mi)


def curtain_panel(mb, x0, x1, y, z0, z1, folds=9, depth=0.05, along='X', mi=0, tie=None):
    """Pleated fabric panel hanging from z1 to z0 across x0..x1 at plane y (a sinusoid in plan), optionally tied back
    (tie = (x_tie, z_tie): the lower part gathered toward x_tie)."""
    nx, nz = folds * 6, 10
    for iz in range(nz):
        za, zb = z1 - (z1 - z0) * iz / nz, z1 - (z1 - z0) * (iz + 1) / nz
        for ix in range(nx):
            def P(u, z):
                xx = x0 + (x1 - x0) * u
                if tie:
                    tx, tz = tie
                    g = max(0.0, min(1.0, (tz + 0.35 - z) / 0.7)) if z < tz + 0.35 else 0.0
                    g = min(1.0, g * 1.2) if z > tz - 0.05 else max(0.0, 1.0 - (tz - 0.05 - z) / 1.6) * 0.85
                    xx = xx + (tx - xx) * g * 0.8
                off = depth * math.sin(2 * math.pi * folds * u)
                return (xx, y + off, z) if along == 'X' else (y + off, xx, z)
            u0, u1 = ix / nx, (ix + 1) / nx
            mb.quad(P(u0, za), P(u1, za), P(u1, zb), P(u0, zb), mi)


def rod(mb, along, a0, a1, b, z, mi=0):
    if along == 'X':
        mb.tube((a0, b, z), (a1, b, z), 0.012, 0.012, seg=10, mi=mi)
        for a in (a0, a1):
            mb.sphere((a, b, z), 0.03, seg=10, rings=6, mi=mi)
    else:
        mb.tube((b, a0, z), (b, a1, z), 0.012, 0.012, seg=10, mi=mi)
        for a in (a0, a1):
            mb.sphere((b, a, z), 0.03, seg=10, rings=6, mi=mi)


def ceiling_fan(M, name, x, y, zc, mi_blade='fan_blade', finish='brass', drop=0.30, lights=4):
    f, bl, gl = MB(), MB(), MB()
    f.cylinder(x, y, zc - 0.06, zc, 0.08, 0.07, seg=18)
    f.cylinder(x, y, zc - drop, zc - 0.06, 0.012, seg=8)
    f.lathe(x, y, zc - drop - 0.12, [(0, 0), (0.10, 0.0), (0.13, 0.04), (0.13, 0.08), (0.10, 0.12), (0, 0.12)], seg=20)
    zb = zc - drop - 0.07
    for k in range(5):
        a = 2 * math.pi * k / 5 + 0.3
        c, s = math.cos(a), math.sin(a)
        f.tube((x + 0.10 * c, y + 0.10 * s, zb), (x + 0.24 * c, y + 0.24 * s, zb - 0.01), 0.012, 0.01, seg=6)
        # blade: a slightly pitched rectangle from r 0.2 to 0.66
        pts = []
        for (r, w) in ((0.20, 0.07), (0.66, 0.075)):
            pts.append((x + r * c - w * s, y + r * s + w * c))
            pts.append((x + r * c + w * s, y + r * s - w * c))
        (a0, a1), (b0, b1) = (pts[0], pts[1]), (pts[2], pts[3])
        bl.hexa([(a0[0], a0[1], zb - 0.012), (a1[0], a1[1], zb - 0.018), (b1[0], b1[1], zb - 0.018), (b0[0], b0[1], zb - 0.012),
                 (a0[0], a0[1], zb - 0.004), (a1[0], a1[1], zb - 0.010), (b1[0], b1[1], zb - 0.010), (b0[0], b0[1], zb - 0.004)])
    zl = zc - drop - 0.14
    for k in range(lights):
        a = 2 * math.pi * k / lights + 0.8
        cx, cy = x + 0.11 * math.cos(a), y + 0.11 * math.sin(a)
        f.tube((x, y, zl + 0.02), (cx, cy, zl - 0.03), 0.008, 0.008, seg=6)
        gl.lathe(cx, cy, zl - 0.17, [(0, 0.0), (0.055, 0.02), (0.065, 0.08), (0.05, 0.13), (0.025, 0.15), (0, 0.15)], seg=16)
        add_light(f"L_{name}_{k}", 'POINT', (cx, cy, zl - 0.10), 18, color=WARM, size=0.04, coll=LC)
    f.build(f"{name}_Body", [M[finish]])
    bl.build(f"{name}_Blades", [M[mi_blade]])
    gl.build(f"{name}_Glass", [M['frosted']])


def recessed(M, name, pts, z=ZC, energy=22, spot=math.radians(100)):
    dl = MB()
    for (x, y) in pts:
        dl.cylinder(x, y, z - 0.008, z + 0.01, 0.075, seg=20, mi=1)
        dl.cylinder(x, y, z - 0.012, z + 0.01, 0.058, seg=20, mi=0)          # the lens sits below the trim ring's face
    dl.build(name, [M['emit_down'], M['trim_int']])
    for i, (x, y) in enumerate(pts):
        add_light(f"L_{name}_{i}", 'SPOT', (x, y, z - 0.03), energy, color=NEUTRAL, size=0.05, spot=spot, blend=0.6, coll=LC)


def table_lamp(M, name, x, y, z, h=0.62, shade=(0.19, 0.13, 0.24), body='brass', energy=12):
    mb, sh = MB(), MB()
    mb.lathe(x, y, z, [(0, 0), (0.08, 0.0), (0.08, 0.02), (0.03, 0.05), (0.05, 0.15), (0.06, 0.28), (0.02, 0.36), (0.012, h - shade[2]), (0, h - shade[2])], seg=18)
    r1, r0, sh_h = shade
    sh.lathe(x, y, z + h - sh_h, [(r1, 0), (r1 - 0.006, 0), (r0 - 0.006, sh_h), (r0, sh_h)], seg=24)
    mb.build(f"{name}_Base", [M[body]])
    sh.build(f"{name}_Shade", [M['shade_linen']])
    add_light(f"L_{name}", 'POINT', (x, y, z + h - sh_h * 0.55), energy, color=WARM, size=0.05, coll=LC)


def kitchen_accessories(M, kit):
    from . import ig_kitchen
    ig_kitchen.accessories(M, kit)
