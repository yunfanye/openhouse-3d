"""349 Walsh Rd promo film: the 16-shot cut (SHOTS), the 78 s long take (TAKE) and the title texts (TITLES).

bpy-free (system python3 reads it for titles / contact sheets / the render driver).  Timing constants and the shot
format live in archviz/filmkit.py; the camera machinery in archviz/film.py.
"""
TITLES = dict(main="349 WALSH ROAD", sub="ATHERTON, CALIFORNIA", end="A MODERN ESTATE IN THE REDWOODS")

L = 2.6                  # == plan.Z_LIV (main-level floor); house.py asserts this
# name, seconds, waypoints [(cam, target), ...] evenly spaced in time, lens (start, end), f-stop, exposure, caption
# Bold, continuous moves: every shot is an orbit / arc / crane / tracking reveal through 3-4 waypoints, and most
# start and end still moving (ease 0.5-0.7) so the dissolves blend two moving images.  Coordinates: see plan.py.
SHOTS = [
    # ---- arrival (dusk exteriors)
    dict(name='aerial',   sec=6.0, lens=(30, 32), fstop=11, exp=0.6, caption=None, ease=(0.0, 0.7),          # drone orbit S -> E
         wp=[((28.0, -31.0, 15.5), (4.0, 4.0, 4.0)), ((46.0, -14.0, 20.0), (8.0, 8.0, 4.0)), ((44.0, 8.0, 18.0), (10.0, 10.0, 4.5))]),
    dict(name='drive',    sec=4.0, lens=(30, 30), fstop=11, exp=0.6, caption=None, ease=(0.6, 0.6),          # low lateral arc across the court, olives in the foreground
         wp=[((-9.0, -20.0, 1.5), (0.5, 1.0, 3.8)), ((-1.0, -18.0, 1.9), (1.0, 1.0, 3.5)), ((7.0, -16.5, 2.4), (0.0, 2.0, 4.2))]),
    dict(name='entry',    sec=3.5, lens=(32, 28), fstop=11, exp=0.6, caption=None, ease=(0.5, 0.6),          # crane up from the reflecting pool to the fin box
         wp=[((1.0, -8.5, 0.7), (1.15, 0.5, 2.2)), ((1.2, -11.0, 3.0), (0.8, 1.0, 3.5)), ((0.8, -14.0, 6.2), (0.6, 1.5, 5.5))]),
    # ---- lower level
    dict(name='stair',    sec=4.5, lens=(16, 18), fstop=4.5, exp=0.2, caption='THE GRAND STAIR', ease=(0.5, 0.6),   # rising orbit around the spiral
         wp=[((-0.43, 1.9, 1.4), (-2.9, 5.4, 1.8)), ((1.1, 5.2, 2.2), (-2.9, 5.4, 3.0)), ((0.5, 7.7, 3.1), (-2.9, 5.4, 4.3))]),
    dict(name='lounge',   sec=5.0, lens=(17, 19), fstop=4.5, exp=0.0, caption='LOWER LOUNGE', ease=(0.5, 0.7),      # billiard room -> down the steps -> wine wall
         wp=[((-6.3, 5.0, 1.65), (-9.5, 14.5, 0.9)), ((-7.5, 8.0, 1.3), (-9.0, 15.5, 0.8)), ((-8.4, 11.0, 0.55), (-8.6, 16.8, 0.75))]),
    dict(name='theatre',  sec=3.0, lens=(18, 18), fstop=4.5, exp=0.1, caption='SCREENING ROOM', ease=(0.6, 0.6),   # rising lateral drift behind the riser
         wp=[((-7.6, 23.0, 0.95), (-11.2, 20.0, 0.2)), ((-6.4, 22.2, 1.35), (-11.5, 20.8, 0.5))]),
    # ---- main level
    dict(name='living',   sec=4.5, lens=(18, 18), fstop=4.5, exp=0.0, caption='GREAT ROOM', ease=(0.6, 0.6),       # arc along the west side, pan across the onyx pier to the pool
         wp=[((8.3, 10.6, 1.5 + L), (11.0, 5.0, 1.4 + L)), ((8.0, 8.0, 1.6 + L), (12.2, 7.5, 1.5 + L)), ((9.0, 5.8, 1.5 + L), (12.4, 9.5, 1.6 + L))]),
    dict(name='kitchen',  sec=4.5, lens=(20, 20), fstop=5.6, exp=-0.25, caption=None, ease=(0.6, 0.6),            # tracking down the aisle, panning to the cabinet wall
         wp=[((-5.0, 9.0, 1.6 + L), (-9.5, 16.0, 1.3 + L)), ((-5.3, 12.6, 1.55 + L), (-10.5, 13.5, 1.2 + L)), ((-6.6, 15.8, 1.5 + L), (-11.5, 11.5, 1.3 + L))]),
    dict(name='dining',   sec=3.5, lens=(18, 18), fstop=4.5, exp=0.05, caption=None, ease=(0.6, 0.6),             # glide along the glass, pan to the table + stair
         wp=[((3.4, 16.8, 1.7 + L), (2.0, 10.0, 1.5 + L)), ((5.8, 14.4, 1.6 + L), (0.0, 9.0, 1.3 + L)), ((6.3, 11.2, 1.5 + L), (-2.0, 8.0, 1.4 + L))]),
    dict(name='master',   sec=3.5, lens=(22, 22), fstop=4.5, exp=-0.05, caption='PRIMARY SUITE', ease=(0.6, 0.6), # arc around the bed toward the glass
         wp=[((-6.1, 18.5, 1.55 + L), (-10.6, 21.6, 1.05 + L)), ((-6.0, 20.6, 1.5 + L), (-10.6, 20.6, 1.0 + L)), ((-6.7, 22.4, 1.45 + L), (-10.0, 19.4, 1.0 + L))]),
    dict(name='bath',     sec=3.0, lens=(18, 18), fstop=4.5, exp=0.05, caption=None, ease=(0.6, 0.6),             # glide around the tub
         wp=[((-1.1, 20.0, 1.5 + L), (-3.5, 23.6, 1.3 + L)), ((-1.0, 21.2, 1.45 + L), (-4.2, 22.5, 1.1 + L)), ((-1.4, 22.0, 1.35 + L), (-4.3, 21.0, 1.0 + L))]),
    # ---- outdoor living
    dict(name='green',    sec=4.0, lens=(24, 24), fstop=22, exp=0.6, caption='LIVING-WALL COURTYARD', ease=(0.6, 0.6),  # low tracking shot along the living wall
         wp=[((15.6, 12.4, 1.1 + L), (18.5, 17.8, 1.9 + L)), ((18.2, 12.0, 1.25 + L), (20.5, 17.8, 1.7 + L)), ((21.0, 12.6, 1.4 + L), (23.0, 17.5, 1.6 + L))]),
    dict(name='pool',     sec=5.0, lens=(20, 22), fstop=11, exp=0.6, caption='POOL & FIRE TERRACE', ease=(0.5, 0.7),   # crane from the fire trough up over the glass wall
         wp=[((17.8, -4.0, 1.45), (17.8, 12.0, 3.8)), ((17.8, -1.6, 2.4), (17.8, 12.0, 4.0)), ((17.8, 1.5, 4.3), (15.0, 13.0, 4.0)), ((18.5, 4.5, 5.0), (12.0, 14.0, 4.4))]),
    dict(name='court',    sec=4.5, lens=(22, 22), fstop=16, exp=0.6, caption=None, ease=(0.6, 0.6),               # drone arc inside the courtyard: SE corner over the pool to the turf, panning back to the pavilion
         wp=[((24.0, 2.8, 3.9), (10.0, 9.0, 4.4)), ((22.5, 9.5, 5.0), (12.0, 10.0, 4.5)), ((17.5, 15.0, 4.6), (10.0, 6.0, 4.4))]),
    dict(name='hero',     sec=6.5, lens=(21, 26), fstop=11, exp=0.6, caption=None, ease=(0.6, 0.3),               # rising orbit from the lawn to the street, end card
         wp=[((15.0, -9.0, 1.6), (4.0, 4.5, 4.6)), ((21.0, -20.0, 5.0), (4.0, 4.0, 5.0)), ((24.0, -30.0, 10.0), (2.0, 3.0, 5.0)), ((12.0, -38.0, 14.0), (0.0, 2.0, 5.5))]),
]
BY_NAME = {s['name']: s for s in SHOTS}
# BY_NAME['take'] is added at the bottom of this file (the long take)


# ------------------------------------------------------------------ the long take (one continuous camera move)
# t (s), camera, look-at, lens (mm), f-stop, exposure (EV), label.  Route: drone descent onto the motor court ->
# the pivot door swings open -> foyer -> billiard room -> down into the lounge to the wine wall and back -> a
# rising 3/4 orbit around the spiral stair onto the dining mezzanine -> dining -> kitchen loop -> through the
# suite's double doors and the master door -> primary bedroom -> out through the north glass -> up over the rear
# lawn and the roof -> down into the courtyard along the living wall -> over the pool into the open living pavilion
# -> out its south face over the front lawn -> rising orbit to the street under the end card.
def K(t, cam, tgt, lens, fstop, exp, label=''):
    return dict(t=t, cam=cam, tgt=tgt, lens=lens, fstop=fstop, exp=exp, label=label)


_TAKE_KEYS = [
    # ---- arrival
    K(0.0,  (34.0, -30.0, 17.0), (4.0, 4.0, 4.0),     30, 11, 0.6, 'aerial descent'),
    K(3.6,  (22.0, -28.0, 10.0), (3.0, 2.0, 4.0),     30, 11, 0.6, 'aerial descent'),
    K(6.8,  (8.0, -21.0, 3.2),   (1.0, 0.0, 3.6),     28, 11, 0.6, 'over the court'),
    K(8.8,  (2.8, -12.0, 1.9),   (1.15, 0.5, 2.0),    26, 8, 0.55, 'to the door (opening)'),
    K(10.4, (1.4, -4.5, 1.6),    (1.3, 2.0, 1.9),     24, 7, 0.45, 'through the door'),
    K(11.8, (1.4, 1.2, 1.6),     (0.5, 7.5, 2.6),     22, 7, 0.3, 'foyer'),
    K(13.4, (1.0, 2.2, 1.6),     (-2.5, 7.5, 2.4),    21, 7, 0.28, 'foyer, turning'),
    K(15.0, (0.2, 2.5, 1.55),    (-4.5, 4.5, 1.4),    21, 7, 0.25, 'foyer -> billiard'),
    K(16.8, (-4.8, 2.4, 1.6),    (-8.5, 9.0, 0.9),    20, 7, 0.15, 'billiard room'),
    # ---- lower lounge: in looking at the wine wall, drift toward the moss-wall corner, then PULL BACK out of the
    #      lounge (the room recedes) and across the billiard room to the foot of the stair, never turning more
    #      than ~45 degrees per key
    K(18.8, (-7.4, 6.0, 1.5),    (-8.6, 15.0, 0.9),   19, 7, 0.05, 'top of the lounge steps'),
    K(21.0, (-8.2, 10.0, 0.6),   (-8.5, 16.8, 0.75),  19, 7, 0.0, 'lounge -> wine wall'),
    K(23.2, (-9.2, 12.0, 0.65),  (-11.8, 16.3, 0.6),  20, 7, 0.0, 'toward the moss-wall corner'),
    K(25.4, (-8.6, 9.6, 0.9),    (-11.5, 14.5, 0.5),  20, 7, 0.0, 'pulling back'),
    K(27.4, (-7.4, 6.4, 1.4),    (-9.5, 13.0, 0.7),   19, 7, 0.08, 'back at the top of the steps'),
    K(29.2, (-6.0, 3.6, 1.55),   (-7.5, 10.0, 1.0),   19, 7, 0.15, 'across the billiard room'),
    # ---- up the spiral stair: the camera climbs alongside the treads (S -> E -> N, counter-clockwise), 1.5 m above them
    K(31.0, (-4.2, 2.0, 1.6),    (-3.2, 5.8, 1.4),    18, 7, 0.2, 'stair: foot of the flight'),
    K(32.8, (-1.4, 1.9, 1.9),    (-2.9, 5.4, 1.9),    17, 7, 0.2, 'stair: climbing S->E'),
    K(34.6, (2.0, 3.6, 2.4),     (-2.9, 5.4, 2.5),    17, 7, 0.2, 'stair: east side'),
    K(36.4, (2.2, 6.8, 3.0),     (-3.2, 5.6, 3.1),    17, 7, 0.2, 'stair: E->N'),
    K(38.0, (0.4, 8.4, 3.9),     (-4.6, 8.8, 3.4),    17, 7, 0.15, 'stair: reaching the landing'),
    K(39.6, (-0.2, 10.0, 4.35),  (-3.5, 13.0, 3.9),   18, 7, 0.05, 'onto the mezzanine'),
    # ---- main level (kitchen loop given room to breathe)
    K(41.6, (2.0, 12.5, 4.15),   (-5.0, 15.0, 3.9),   18, 7, 0.05, 'dining'),
    K(43.8, (-1.5, 15.8, 4.15),  (-9.0, 13.0, 3.8),   19, 7, -0.15, 'dining -> kitchen'),
    K(46.0, (-6.5, 14.5, 4.15),  (-11.5, 11.5, 3.8),  20, 8, -0.25, 'kitchen aisle'),
    K(47.8, (-7.6, 12.6, 4.12),  (-11.8, 13.0, 3.85), 20, 8, -0.25, 'kitchen, the cabinet wall'),
    K(49.6, (-7.5, 11.0, 4.1),   (-11.0, 15.0, 3.9),  20, 8, -0.25, 'round the island'),
    K(51.8, (-5.0, 12.8, 4.15),  (-6.0, 18.5, 3.9),   20, 8, -0.2, 'turning north'),
    K(54.4, (-2.4, 14.6, 4.15),  (-0.6, 19.0, 3.9),   19, 7, -0.05, 'to the suite doors'),
    K(57.2, (0.3, 17.4, 4.1),    (-1.6, 19.6, 3.9),   18, 7, 0.05, 'through the double doors'),
    K(59.0, (-0.6, 18.7, 4.1),   (-4.8, 19.1, 3.8),   18, 7, 0.0, 'corridor'),
    K(60.4, (-2.9, 18.9, 4.1),   (-7.5, 19.6, 3.7),   18, 7, 0.0, 'corridor W'),
    K(61.8, (-4.7, 18.8, 4.1),   (-9.5, 20.5, 3.7),   19, 7, -0.05, 'master door'),
    K(64.4, (-6.5, 20.3, 4.05),  (-10.8, 21.2, 3.6),  20, 7, -0.05, 'primary bedroom'),
    K(66.6, (-7.5, 22.4, 4.05),  (-10.5, 19.8, 3.5),  20, 7, -0.05, 'to the north glass'),
    # ---- out the back, over the roof, round the courtyard's east side, west over the pool to the living wall
    K(68.0, (-7.9, 24.8, 4.2),   (-9.5, 20.0, 3.6),   20, 8, 0.2, 'through the glass'),
    K(69.8, (-6.5, 28.5, 6.5),   (-4.0, 17.0, 4.5),   22, 9, 0.5, 'pulling back from the rear'),
    K(72.2, (-2.0, 31.0, 12.5),  (4.0, 12.0, 3.5),    22, 11, 0.6, 'rising over the rear lawn'),
    K(75.2, (8.0, 28.0, 15.0),   (12.0, 14.0, 5.0),   24, 11, 0.6, 'over the roof'),
    K(78.6, (20.0, 24.0, 13.0),  (14.0, 10.0, 4.5),   24, 11, 0.6, 'the courtyard from the NE'),
    K(81.2, (25.0, 15.0, 10.0),  (14.0, 12.0, 4.5),   24, 11, 0.6, 'down the east side'),
    K(83.8, (24.0, 6.0, 7.5),    (16.0, 14.0, 4.5),   23, 11, 0.6, 'descending over the pool'),
    K(86.4, (19.0, 4.5, 4.8),    (19.0, 17.0, 4.4),   22, 11, 0.55, 'over the pool, facing the living wall'),
    K(89.2, (14.5, 7.5, 4.4),    (17.5, 17.5, 4.2),   22, 11, 0.5, 'toward the wall and the olive'),
    K(91.4, (13.2, 8.6, 4.25),   (10.5, 12.5, 4.0),   20, 9, 0.3, 'turning to the pavilion'),
    K(93.8, (12.7, 9.0, 4.15),   (9.0, 8.0, 3.8),     19, 8, 0.1, 'facing the pavilion'),
    K(96.4, (12.2, 8.8, 4.1),    (8.5, 6.5, 3.9),     19, 7, 0.0, 'into the pavilion'),
    K(98.6, (10.0, 8.8, 4.0),    (9.6, 4.5, 3.7),     19, 7, 0.0, 'past the onyx pier'),
    K(100.6, (10.4, 4.6, 3.9),   (11.5, -3.0, 2.6),   20, 8, 0.3, 'out the south face'),
    # ---- finale: a slow clockwise sweep that turns back to the house as it climbs
    K(103.4, (14.5, 0.0, 4.8),   (20.0, -7.0, 4.2),   22, 11, 0.55, 'over the lawn, looking out'),
    K(105.6, (16.5, -3.5, 5.4),  (26.0, -2.0, 4.8),   22, 11, 0.6, 'turning east'),
    K(107.8, (19.0, -7.0, 6.0),  (26.0, 4.0, 4.0),    22, 11, 0.6, 'turning north-east'),
    K(110.0, (22.0, -12.0, 7.8), (18.0, 6.0, 5.0),    23, 11, 0.6, 'turning north'),
    K(112.2, (23.0, -17.0, 9.0), (7.0, 3.0, 4.6),     24, 11, 0.6, 'back on the house'),
    K(115.0, (22.0, -27.0, 12.0), (2.0, 3.0, 5.0),    25, 11, 0.6, 'orbit out'),
    K(117.8, (12.0, -35.0, 14.5), (0.0, 2.0, 5.5),    26, 11, 0.6, 'end card'),
]
_SCALE = 78.0 / _TAKE_KEYS[-1]['t']          # fit the take into 78 s
for _k in _TAKE_KEYS:
    _k['t'] = round(_k['t'] * _SCALE, 3)
TAKE = dict(name='take', keys=_TAKE_KEYS, door_t=8.3 * _SCALE, door_secs=1.6, caption=None, exp=0.6, fstop=11, lens=(24, 24),
            sec=_TAKE_KEYS[-1]['t'], wp=[])

BY_NAME['take'] = TAKE
