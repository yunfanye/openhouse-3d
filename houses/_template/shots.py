"""Promo film for the template house (bpy-free): shots, titles.  Format: archviz/filmkit.py docstring."""
TITLES = dict(main="TEMPLATE HOUSE", sub="SOMEWHERE, CALIFORNIA", end="A HOUSE BUILT FROM ITS PHOTOS")

# name, seconds, waypoints [(camera, look-at), ...] evenly spaced in time, lens (start, end), f-stop, exposure, caption,
# ease (in, out): 0 = come to rest at the cut, 1 = keep the full velocity through it
SHOTS = [
    dict(name='arrive', sec=5.0, lens=(28, 30), fstop=11, exp=0.6, caption=None, ease=(0.0, 0.6),
         wp=[((22.0, -24.0, 9.0), (0.0, 4.0, 3.0)), ((14.0, -16.0, 3.0), (0.0, 3.0, 2.5)), ((3.0, -10.0, 1.8), (0.0, 2.0, 2.2))]),
    dict(name='living', sec=4.0, lens=(20, 20), fstop=4.5, exp=0.0, caption='LIVING ROOM', ease=(0.6, 0.6),
         wp=[((4.5, 1.0, 1.5), (-3.0, 6.0, 1.3)), ((3.5, 3.5, 1.5), (-4.0, 7.0, 1.2))]),
    dict(name='hero', sec=5.0, lens=(24, 28), fstop=11, exp=0.6, caption=None, ease=(0.6, 0.0),
         wp=[((12.0, -10.0, 1.8), (0.0, 4.0, 3.0)), ((20.0, -22.0, 8.0), (0.0, 3.0, 3.5))]),
]
BY_NAME = {s['name']: s for s in SHOTS}
# A continuous long take (one camera move through timed keys, doors opening) is optional: see houses/walsh/shots.py TAKE.
