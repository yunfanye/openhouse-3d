"""Photo-derived spatial hypothesis, metres, +Y toward rear garden.

Evidence: 00/01/18/19 establish the rear double veranda, five window bays,
5 roof dormers, oval pool, lawn, formal rose parterre and rear gallery.
02/32 establish the matching front colonnade and semicircular motor court.
03/13 establish a two-storey central stair hall with a single flared stair,
side galleries and four rooflights. 04-11 establish staged principal rooms.
28-31 establish separate gallery and two-storey guest house.

Inferred: dimensions, depths, exact room adjacency and unpictured connections.
Lot uses listing's approximate 99 x 345 ft dimensions. Principal house 24 x 18 m.
No measured floor plan was supplied. Model is an architectural visualization.
"""
Z=.45
UP=4.25
CEIL=4.03
TOP=8.05
RIDGE=10.65
BAYS=(-9,-4.5,0,4.5,9)
COLS=(-11.55,-6.93,-2.31,2.31,6.93,11.55)
ROOMS={
 'hall':(-3.4,3.4,.3,12,Z,7.85),
 'living':(-11.7,-3.5,.3,9,Z,CEIL),
 'library':(-11.7,-3.5,9.2,17.7,Z,CEIL),
 'dining':(3.5,11.7,.3,8.5,Z,CEIL),
 'kitchen':(3.5,11.7,8.7,17.7,Z,CEIL),
 'salon':(-3.4,3.4,12.2,17.7,Z,CEIL),
 'primary':(-11.7,-3.5,8.5,17.7,UP,7.85),
 'bedroom':(-11.7,-3.5,.3,8.3,UP,7.85),
 'bath':(3.5,11.7,10.5,17.7,UP,7.85),
 'guestroom':(3.5,11.7,.3,10.3,UP,7.85),
}
POOL=(0,32,8.2,3.65)
GALLERY=(-11.4,11.4,65,76)
GUEST=(-11.4,11.4,79,88)
