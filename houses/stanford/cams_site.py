"""Photo-matched cameras for the site / context photos (bpy-free): 26 from the patio toward the pond, 29 on the
common path, 31 and 32 the aerials.  name -> (location, target, lens); shifts / rolls / resolutions as in house.py.
Solve inputs: cams/aerials.json (31 + 32), cams/p26.json; p29 from the path's vanishing point and width (REFERENCES.md)."""
CAMS_SITE = {
    'p26':    ((5.743, 13.915, 0.981), (5.824, 23.914, 0.981), 17.29),       # photo 26 (cams/p26.json: fence posts, far shore, riprap, far houses)
    'p29':    ((-3.9, 32.5, 1.3), (-13.88, 33.128, 1.3), 17.3),              # photo 29: on the belt path looking west (path VP, width; T1 tie)
    'aerial': ((1.898, -111.149, 68.693), (2.107, -102.06, 64.529), 67.48),   # photo 31 (cams/aerials.json, joint 31+32, 2.3 px rms; tele frame)
    'p32':    ((2.117, -96.168, 68.367), (2.26, -86.584, 65.515), 22.33),     # photo 32 (joint solve, 1.9 px rms; pitch pinned by the horizon)
}
CAM_SHIFT_SITE = {'p26': (-0.019, 0.0271), 'p29': (0.0, -0.008)}
CAM_ROLL_SITE = {'aerial': -0.62, 'p32': -0.02}
EXPOSURE = {'p29': 1.1}         # under the canopy: the listing photo is lifted ~1 EV (path 173 sRGB in the photo)
CAM_CLIP_SITE = {'p32': 30000.0, 'aerial': 6000.0, 'p26': 3000.0, 'p29': 3000.0}   # run.py: camera clip_end (default 800)
CAM_RES_SITE = {'p26': (1536, 1024), 'p29': (1536, 1024), 'aerial': (1536, 1152), 'p32': (1536, 1152)}
