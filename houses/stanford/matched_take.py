"""The other reconstruction's 80-second route, re-authored key-for-key in this model (bpy-free).

An independent reconstruction of the same listing (its houses/stanford/cinematic.py, 2026-09-08 delivery) defines one
continuous 1,921-frame take: aerial arrival -> front door -> foyer and living room -> up the oak U-stair -> upper hall
-> primary bedroom -> back down the stair -> hall past the powder room -> great room -> dining -> kitchen -> slider
-> patio -> aerial finale.  This take
keeps every key time, label, lens and f-stop, and the door / slider schedule, so the two films can be played frame-locked.

The two plans use different origins and differ in room sizes, so each key is placed by what it frames in the same room,
not by one coordinate transform: exteriors translate with the house centre (+6.25 m in X), the approach with the entry
door, the stair per flight (both are U-stairs with the half landing at the right wall), the upper hall and primary
bedroom by their door and bed wall, the great room / kitchen / slider by +6.3 m in X (the fireplace wall, great-room
window and slider agree to ~0.1 m).  Exposure follows this model's own calibration.  Camera positions are staging.
"""
H = 1.55                                   # interior eye height above a floor or tread
RISE, TREAD, ST_X0, Z_UP = 2.84 / 14, 0.26, 9.76, 2.84
UP = Z_UP + H                              # upper-floor eye height 4.39
EXT, INT, UPR = 0.0, 0.0, 0.0              # exposure: exterior, main floor, upper floor (tuned on Cycles proofs)


def tread(x):
    """Eye height over the lower flight at plan x (it climbs +X from its first riser at ST_X0 to the half landing)."""
    k = min(6, int((x - ST_X0) / TREAD) + 1) if x > ST_X0 else 0
    return k * RISE + H


def K(t, cam, tgt, lens, exp, label=''):
    return dict(t=t, cam=cam, tgt=tgt, lens=lens, fstop=8, exp=exp, label=label)


KEYS = [
    # ---- aerial arrival over the street to the front door (door opens at 7.0 s over 2.5 s)
    K(0, (-10.75, -23, 12.9), (6.25, 3, 3.4), 32, EXT, 'Aerial arrival'),
    K(4, (-0.75, -16, 5.6), (7.25, 1.5, 2.9), 29, EXT),
    K(8, (6.76, -6.6, 1.65), (7.9, 1.4, 1.45), 25, EXT),
    K(10, (7.9, -1.1, 1.55), (8.05, 3.4, 1.40), 22, EXT),
    # ---- foyer, the living room on the right, the stair foot
    K(12, (7.9, 2.45, H), (10.6, 3.25, 1.33), 21, INT, 'Welcome home'),
    K(14, (9.55, 3.95, H), (10.9, 5.35, 2.2), 21, INT),
    # ---- up the lower flight (+X), the half landing and its window, the upper flight (-X)
    K(16, (9.75, 5.35, 1.72), (11.9, 5.4, 2.75), 21, INT, 'Oak stair'),
    K(18, (11.05, 5.35, tread(11.05)), (11.95, 6.6, 3.25), 21, INT),
    K(19.5, (11.5, 5.4, 1.42 + H), (10.3, 6.4, 3.85), 21, INT),
    K(21, (11.5, 6.35, 1.42 + H), (9.0, 6.35, 4.2), 21, INT),
    # ---- the upper hall west, then north into the passage to the primary bedroom's door
    K(24, (8.4, 6.35, UP), (5.95, 6.9, UP - 0.08), 21, UPR),
    K(25.5, (5.75, 6.38, UP), (4.2, 8.1, UP - 0.25), 21, UPR),
    K(27, (5.5, 7.52, UP), (1.0, 10.0, UP - 0.36), 21, UPR, 'Primary retreat'),
    K(29, (4.25, 7.55, UP), (0.8, 9.65, UP - 0.36), 22, UPR),
    K(31.5, (3.6, 9.25, UP - 0.05), (0.3, 9.25, UP - 0.38), 22, UPR),
    K(34, (4.55, 7.55, UP), (1.65, 5.1, UP - 0.23), 22, UPR),
    K(35, (5.45, 7.55, UP), (5.6, 3.0, UP - 0.2), 21, UPR),
    K(36, (5.45, 6.6, UP), (6.8, 5.5, UP - 0.13), 21, UPR),
    # ---- back along the hall to the stair head and down both flights
    K(37.5, (6.2, 6.35, UP), (9.2, 6.2, UP - 0.63), 21, UPR),
    K(39, (7.4, 6.35, UP), (10.4, 6.25, UP - 1.13), 21, UPR),
    K(40.5, (9.3, 6.35, UP), (12.1, 6.25, 2.9), 21, UPR),
    K(43, (11.5, 6.3, 1.42 + H), (10.7, 4.85, 2.67), 21, INT),
    K(44.5, (11.5, 5.4, 1.42 + H), (9.4, 5.3, 1.62), 21, INT),
    K(46.5, (10.1, 5.35, tread(10.1)), (7.4, 3.6, 1.4), 21, INT),
    # ---- the foyer and front door, the hall past the powder room (door closes 45-48 s) into the great room
    K(48, (8.85, 4.15, H), (5.9, 3.25, 1.48), 21, INT),
    K(49, (7.85, 4.4, H), (6.2, 6.1, 1.46), 21, INT),
    K(49.7, (7.15, 4.85, H), (6.6, 7.3, 1.46), 21, INT),
    K(50.3, (6.95, 5.35, H), (6.95, 7.9, 1.46), 21, INT),
    K(51.5, (6.95, 6.35, H), (7.1, 8.7, 1.39), 21, INT),
    K(53.5, (7.1, 7.8, H), (1.05, 9.05, 1.33), 21, INT, 'Gather beautifully'),
    K(55.5, (5.75, 8.45, H), (0.8, 9.2, 1.36), 22, INT),
    # ---- the rear windows and slider, across the dining area to the kitchen (the slider opens 61-64 s)
    K(57.5, (6.05, 9.35, H), (5.95, 13.35, 1.41), 22, INT),
    K(58.5, (6.35, 9.95, H), (9.3, 12.8, 1.41), 21, INT),
    K(59.5, (6.95, 10.7, H), (11.2, 10.3, 1.33), 21, INT),
    K(62, (9.0, 10.8, H), (12.0, 9.35, 1.3), 22, INT, 'Oak kitchen'),
    K(64, (8.95, 9.0, H), (10.8, 11.25, 1.3), 22, INT),
    K(66, (7.75, 10.85, H), (6.95, 14.5, 1.41), 21, INT),
    # ---- through the slider onto the patio; the pond; rising back over the house
    K(67, (7.05, 11.65, H), (7.02, 17, 1.61), 22, EXT),
    K(68, (7.0, 12.6, 1.58), (5.3, 35, 2.1), 23, EXT, 'Pond-side living'),
    K(71, (6.75, 19, 2.6), (-5.75, 26, 2.9), 25, EXT),
    K(73, (3.25, 24, 6.4), (-4.75, 14, 2.9), 25, EXT),
    K(75, (-5.75, 22, 12.9), (6.25, 9, 2.9), 27, EXT),
    K(77.5, (-11.75, 3, 15.9), (6.25, 5, 3.4), 29, EXT),
    K(80, (-7.75, -18, 12.9), (6.25, 4, 3.4), 32, EXT, 'A place by the water'),
]
TAKE = dict(name='cinematic', sec=80, keys=KEYS, wp=[], lens=(32, 32), fstop=8, exp=EXT, caption=None,
            door_t=7.0, door_secs=2.5, position_tension=0.60, angular_aim=True,
            powder=((45.0, 'open'), (48.0, 'closed')),              # the other film closes its powder door 45 -> 48 s
            slider=((61.0, 0.0), (64.0, 1.0), (72.0, 1.0), (76.0, 0.0)),   # (s, open fraction): opens, closes behind
            shut=('Door_Bed19', 'Door_Bed20'))       # film-only: both leaves swing across the upper hall when open
