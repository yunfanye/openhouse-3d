"""Photo-matched cameras for the upper-floor photos 15-23 (owned by INT_CAM; bpy-free).
name -> (location, target, lens); lens shifts (perspective-corrected listing photos) in CAM_SHIFT_UPPER,
render sizes (the photo's pixel size) in CAM_RES_UPPER, photo pairs in PAIRS_UPPER, optional CAM_ASPECT / CAM_ROLL /
EXPOSURE per camera (house.py merges them).

16-23 are LEVEL cameras solved with tools/intcam_solve.py from sub-pixel wall / ceiling / baseboard / casing lines,
scaled by exterior anchors (the plan's window openings and wall faces) with the upper ceiling at plan.Z_C2 5.20 - inputs
cams/int_p15.json .. int_p23.json (16 + 17 jointly in int_p16_17.json).  No aspect stretch is needed
with the 5.20 ceiling (the 0.90-0.97 stretches earlier fits needed were a 5.44 ceiling).  15 (free down-pitch, the photo
is not perspective-corrected) is a free-pitch + roll solve (int_p15.json); 22 (int_p22.json) is the primary walk-in closet.
"""
ZU = 2.84   # == plan.Z_UP

CAMS_UPPER = {
    'p15': ((9.394, 6.480, 3.986), (18.153, 2.482, 1.284), 17.06),       # stair landing; free pitch -15.7 deg + roll (int_p15.json, far 1.5 px / near 5-23 px)
    'p16': ((4.094, 7.622, 3.850), (-1.047, 16.199, 3.850), 16.41),      # primary bedroom -> rear windows (int_p16_17.json, 1.0 px)
    'p17': ((4.182, 11.337, 3.853), (-2.987, 4.366, 3.853), 16.27),      # primary bedroom from the rear windows (int_p16_17.json, 1.2 px)
    'p18': ((1.477, 6.341, 3.816), (-4.013, -2.017, 3.816), 15.16),      # primary bath from its doorway (int_p18.json, 0.3 px)
    'p19': ((9.160, 7.524, 3.736), (15.540, 15.225, 3.736), 16.60),      # bedroom 19 from its doorway (int_p19.json, 0.6 px on lines)
    'p20': ((8.053, 4.820, 3.845), (2.147, -3.250, 3.845), 16.05),       # bedroom 20 from the back-right (int_p20.json, 0.5 px)
    'p21': ((9.278, 4.621, 3.916), (15.644, -3.090, 3.916), 14.19),       # bedroom 21 (brick bay) from just inside its door (int_p21.json, 0.7 px)
    'p22': ((2.775, 1.848, 3.892), (-6.102, 6.451, 3.892), 16.22),       # primary walk-in closet from its door (int_p22.json, 1.4 px)
    'p23': ((7.079, 7.980, 3.913), (12.654, 16.283, 3.913), 15.61),      # hall bath (int_p23.json, 0.4 px)
}
CAM_SHIFT_UPPER = {
    'p16': (-0.1151, 0.0008),
    'p17': (0.0665, 0.0001),
    'p18': (0.0, -0.0004),
    'p19': (0.0092, -0.0063),
    'p20': (0.0523, -0.0066),
    'p21': (-0.0099, -0.0005),
    'p22': (0.0000, 0.0052),
    'p23': (0.0, -0.0031),
}
CAM_RES_UPPER = {'p15': (768, 1152), 'p16': (1536, 1024), 'p17': (1536, 1024), 'p18': (1536, 1024), 'p19': (1536, 1024),
                 'p20': (1536, 1024), 'p21': (1536, 1024), 'p22': (1536, 1024), 'p23': (1536, 1024)}
# walkthrough checks (not photo pairs): the stair top looking along the hall, the master entry
CAMS_UPPER.update({
    'up_hall': ((9.30, 5.30, 4.35), (4.0, 5.30, 4.20), 16.0),
    'up_mvest': ((5.47, 6.10, 4.30), (5.47, 9.0, 4.20), 16.0),
    'up_master_in': ((5.60, 7.85, 4.30), (1.0, 9.2, 4.10), 16.0),
})
PAIRS_UPPER = [('p15', 15), ('p16', 16), ('p17', 17), ('p18', 18), ('p19', 19), ('p20', 20), ('p21', 21), ('p22', 22), ('p23', 23)]
CAM_ASPECT = {}           # {name: a}: render at (W, H / a), then stretch to (W, H) - none needed with the 5.20 ceiling
# optional: roll in degrees (positive = image rotated clockwise) and exposure (stops) per camera
CAM_ROLL = {'p15': -1.08}
EXPOSURE = {'p15': 0.45}   # photo 15 is ~0.5 EV brighter than its render over the whole frame (median / mean linear, twice)
