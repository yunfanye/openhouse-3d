"""Photo-matched cameras for the main-floor photos 04-14, 24 (owned by INT_CAM; bpy-free).
name -> (location, target, lens); shifts / resolutions in CAM_SHIFT_MAIN / CAM_RES_MAIN; pairs in PAIRS_MAIN.

Listing photos are perspective-corrected, so every camera is level (target at the camera's height) with a lens shift.
Cameras are solved with tools/intcam_solve.py from sub-pixel point AND line correspondences on architecture only (wall /
ceiling / floor junctions, corners, casings, door leaves; never furniture), several photos jointly with the uncertain plan
dimensions as named unknowns.  Inputs: cams/int_great.json (08-11, 14), cams/int_living.json (04-06).  Residuals and the
geometry discrepancies they expose are listed in REFERENCES.md / the gallery notes.
"""
CAMS_MAIN = {
    'p04': ((9.151, 5.424, 0.991), (9.124, -4.576, 0.991), 23.13),  # photo 04: foyer + front door from the stair foot (int_living.json, 1.3 px)
    'p05': ((11.467, 1.692, 1.113), (6.326, 10.269, 1.113), 15.92),  # photo 05: living -> hall + stair (int_living.json, 0.9 px)
    'p06': ((7.917, 2.116, 1.061), (16.653, 6.983, 1.061), 17.09),  # photo 06: living room from the foyer (int_living.json, 1.0 px)
    'p07': ((9.131, 5.897, 1.122), (9.186, 15.897, 1.122), 13.64),  # photo 07: powder room from its doorway (int_p07.json, 0.8 px)
    'p08': ((1.365, 6.739, 0.942), (8.779, 13.449, 0.942), 17.59),  # photo 08: great room from the SW corner (int_great.json, 1.4 px)
    'p09': ((6.129, 8.740, 1.349), (-3.869, 8.937, 1.349), 18.98),  # photo 09: fireplace wall, wide (int_great.json, 2.9 px)
    'p10': ((5.479, 8.894, 1.166), (-4.521, 8.863, 1.166), 32.24),  # photo 10: fireplace + TV (int_great.json, 1.9 px)
    'p11': ((9.095, 8.218, 1.129), (1.739, 14.991, 1.129), 20.91),  # photo 11: dining -> slider + great room, north of the pier (int_great.json, 3.3 px)
    'p12': ((8.162, 8.676, 1.238), (15.854, 15.067, 1.238), 22.52),  # photo 12: kitchen NE corner (int_great.json, 2.1 px)
    'p13': ((8.346, 11.016, 1.241), (16.353, 5.025, 1.241), 18.41),  # photo 13: kitchen range / pantry (int_great.json, 2.1 px)
    'p14': ((11.003, 10.695, 1.232), (1.769, 6.857, 1.232), 18.76),  # photo 14: kitchen -> dining + great room (int_great.json, 3.0 px)
    'p24': ((4.861, -0.023, 0.849), (-1.008, 8.073, 0.849), 16.09),  # photo 24: garage from the open door toward the back-left corner (int_p24.json, 1.1 px)
}
CAM_SHIFT_MAIN = {
    'p04': (-0.0077, -0.0044),
    'p05': (-0.0099, -0.0030),
    'p06': (0.0251, -0.0186),
    'p07': (0.0081, -0.0195),
    'p08': (0.0191, -0.0041),
    'p09': (0.0259, -0.0278),
    'p10': (0.0484, 0.0015),
    'p11': (0.0226, -0.0115),
    'p12': (0.0383, -0.0034),
    'p13': (-0.0177, -0.0068),
    'p14': (0.0114, 0.0002),
    'p24': (-0.0351, 0.0042),
}
CAM_RES_MAIN = {
    'p04': (1536, 1024),
    'p05': (1536, 1024),
    'p06': (1536, 1024),
    'p07': (768, 1152),
    'p08': (1536, 1024),
    'p09': (1536, 1024),
    'p10': (1536, 1024),
    'p11': (1536, 1024),
    'p12': (1536, 1024),
    'p13': (1536, 1024),
    'p14': (1536, 1024),
    'p24': (1536, 1024),
}
PAIRS_MAIN = [(f'p{n}', int(n)) for n in ('04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '24')]
# optional: roll in degrees (positive = image rotated clockwise) and exposure (stops) per camera
CAM_ROLL = {}
EXPOSURE = {}
