"""1836 Webster Street — 64-second continuous cinematic walkthrough.

Arrival -> entry -> living room orbit -> dining -> kitchen -> family room ->
rear garden crane -> roof deck -> bedroom -> primary-suite reveal. One camera,
no internal edit. The older finale is retained only as an optional test move.
The route uses the photograph-derived openings; the primary window is fixed.
"""
TITLES = dict(main="1836 WEBSTER STREET", sub="OLD PALO ALTO, CALIFORNIA", end="A 1926 CLASSIC ON A 10,000 SQ FT LOT")

UP = 3.05                                # == plan.Z_UP
H = 1.5                                  # eye height over a floor
U = UP + H


def K(t, cam, tgt, lens, fstop, exp, label=''):
    return dict(t=t, cam=cam, tgt=tgt, lens=lens, fstop=fstop, exp=exp, label=label)


_TAKE_KEYS = [
    # ---- arrival (dusk)
    K(0.0,  (6.0, -23.0, 9.0), (0.0, 4.0, 2.5),        32, 11, 0.6, 'aerial over the street'),
    K(4.0,  (2.5, -14.0, 4.2),  (0.0, 3.0, 2.4),        28, 11, 0.6, 'descending to the walk'),
    K(7.0,  (-0.28, -7.0, 1.05), (-0.28, 2.0, 1.7),     24, 9, 0.55, 'the brick walk'),
    K(9.0,  (-0.28, -2.3, 1.15), (-0.3, 3.0, 1.55),     24, 8, 0.5, 'the entry steps (door opening)'),
    K(9.8,  (-0.28, -0.75, 1.5), (-0.35, 4.0, 1.55),    23, 7, 0.45, 'under the arch'),
    K(10.8, (-0.3, 0.9, 1.5),   (-2.0, 5.0, 1.5),       22, 7, 0.35, 'through the front door'),
    # ---- entry -> living room (one slow clockwise sweep: fireplace, rear window, built-ins, the arch) -> back
    K(11.8, (-0.35, 2.75, 1.5), (-2.4, 4.5, 1.5),       21, 7, 0.28, 'entry, turning left'),
    K(12.8, (-0.6, 3.1, 1.5),   (-3.4, 3.8, 1.45),      21, 7, 0.25, 'toward the living arch'),
    K(13.9, (-1.35, 3.05, 1.45), (-5.3, 2.85, 1.25),    20, 6, 0.2, 'through the arch, the fireplace ahead'),
    K(15.9, (-2.8, 3.7, 1.45),  (-5.40, 2.95, 1.15),      20, 6, 0.15, 'the fireplace'),
    K(17.7, (-3.6, 4.1, 1.45),  (-3.7, 1.3, 1.25),       20, 6, 0.15, 'sweeping across the seating'),
    K(19.5, (-4.1, 3.9, 1.45),  (-2.2, 1.6, 1.3),      20, 6, 0.15, 'the front window and sofa'),
    K(20.7, (-3.65, 3.75, 1.45), (-0.9, 2.8, 1.4),       20, 6, 0.18, 'looking back to the arches'),
    K(21.8, (-2.6, 3.35, 1.45),  (0.4, 3.6, 1.4),        20, 6, 0.2, 'toward the arch'),
    K(22.9, (-1.3, 3.0, 1.45),  (2.2, 3.3, 1.35),       20, 6, 0.2, 'through the arch again'),
    K(24.1, (0.3, 3.0, 1.45),   (3.6, 4.2, 1.3),        20, 6, 0.2, 'entry -> dining arch'),
    # ---- dining -> kitchen -> family
    K(25.3, (1.6, 3.2, 1.45),   (4.5, 5.4, 1.3),        20, 6, 0.2, 'into the dining room'),
    K(26.8, (2.0, 4.5, 1.5),    (3.8, 8.0, 1.3),        20, 6, 0.2, 'the table, the kitchen door beyond'),
    K(28.1, (2.6, 6.3, 1.45),   (3.2, 10.3, 1.3),       20, 6, 0.18, 'to the kitchen door'),
    K(29.1, (3.00, 7.05, 1.45), (3.6, 10.9, 1.3),       20, 6, 0.15, 'through the kitchen door'),
    K(29.65,(3.25,7.70,1.45),(3.6,11.2,1.3),20,6,.15,'clearing the refrigerator'),
    K(30.8, (3.45, 9.0, 1.45),  (3.2, 12.6, 1.35),      20, 6, 0.15, 'down the kitchen aisle'),
    K(32.0, (3.15, 10.4, 1.45), (2.6, 13.8, 1.3),       20, 6, 0.15, 'turning to the arch'),
    K(32.8, (2.72, 11.25, 1.45), (2.55, 14.7, 1.25),    20, 6, 0.15, 'through the arch'),
    K(33.9, (2.72, 12.8, 1.45), (1.9, 16.2, 1.2),       20, 6, 0.15, 'hall2'),
    K(34.5, (2.68, 13.5, 1.45), (1.6, 16.8, 1.2),       20, 6, 0.15, 'clearing the hall corner'),
    K(35.0, (2.43, 14.02, 1.45), (0.8, 16.9, 1.15),     20, 6, 0.15, 'family room'),
    K(35.5, (2.08, 14.55, 1.45), (0.7, 17.2, 1.15),     20, 6, 0.17, 'opening onto the garden'),
    K(36.0, (1.85, 15.1, 1.45), (0.9, 18.5, 1.1),       21, 7, 0.22, 'toward the french doors'),
    K(37.0, (1.35, 17.0, 1.45), (1.25, 20.0, 1.0),      21, 7, 0.28, 'the french doors'),
    K(38.0, (1.3, 18.55, 1.4),   (1.3, 24.0, 0.6),       22, 8, 0.4, 'out over the steps'),
    # ---- backyard crane: rise over the patio, swing right across the yard, come back on the house, arc to the deck
    K(40.0, (0.8, 21.0, 2.4),   (5.5, 30.0, 1.0),       24, 11, 0.6, 'over the patio, rising'),
    K(41.7, (-0.5, 24.5, 4.6),  (7.5, 26.5, 0.8),       26, 11, 0.62, 'turning toward the oleander corner'),
    K(43.5, (-2.5, 26.5, 6.8),  (6.0, 21.5, 1.5),       26, 11, 0.65, 'the patio, gate and garage wall'),
    K(45.3, (-4.5, 25.0, 8.4),  (3.0, 16.0, 3.5),       26, 11, 0.65, 'back on the house'),
    K(47.1, (-6.5, 20.0, 8.0),  (-1.5, 11.5, 3.4),      25, 11, 0.62, 'the rear from the -X corner'),
    K(48.9, (-6.45, 14.0, 6.45),  (-3.0, 9.5, 4.6),       24, 10, 0.58, 'descending toward the deck'),
    K(50.1, (-6.0, 11.2, 5.3),  (-2.6, 9.6, 4.5),       23, 9, 0.5, 'over the parapet'),
    K(51.3, (-5.0, 9.9, 4.6),   (-1.2, 10.1, 4.45),     22, 8, 0.45, 'on the deck, facing the slider'),
    # ---- upper level
    K(52.5, (-3.3, 9.95, U),    (-0.3, 9.6, U - 0.15),  21, 7, 0.3, 'through the slider (the bed to the right)'),
    K(53.8, (-1.9, 10.4, U),    (0.4, 11.0, U - 0.1),   20, 6, 0.2, 'bedroom -> its door'),
    K(55.0, (-0.4, 10.95, U),   (2.4, 11.1, U - 0.1),   20, 6, 0.2, 'through the door'),
    K(56.2, (1.0, 11.05, U),    (3.8, 9.2, U - 0.25),   20, 6, 0.15, 'into the primary suite'),
    K(57.7, (1.9, 10.1, U),     (4.6, 9.15, U - 0.45),  21, 6, 0.15, 'the primary suite'),
    K(59.3, (2.30, 9.6, U-.08), (4.9, 9.2, U - 0.35),  23, 6, 0.18, 'settling into the suite portrait'),
    K(61.0, (2.0, 9.24, U-.16), (4.98, 9.2, U - 0.28), 24, 6, 0.2, 'window light across the linens'),
    K(63.0, (1.70, 9.2, U-.2), (4.98, 9.2, U - 0.15), 26, 6, 0.2, 'a quiet symmetrical suite reveal'),
]
# the finale is a second shot joined by a dissolve: rising over the entry swoop and pulling back over the street
_FINALE_KEYS = [
    K(0.0,  (3.0, 3.0, 5.2),    (0.5, -3.0, 1.0),        22, 11, 0.6, 'over the swoop, tilting down onto the walk'),
    K(2.0,  (2.2, -1.0, 7.5),   (0.0, 0.5, 0.5),         24, 11, 0.6, 'straight down onto the entry steps'),
    K(4.2,  (1.2, -8.0, 10.0),  (0.0, 4.0, 3.0),         24, 11, 0.6, 'the house from above the lawn'),
    K(8.5,  (0.5, -24.0, 13.0), (0.0, 5.0, 3.0),         27, 11, 0.6, 'end card'),
]
_SCALE = 64.0 / _TAKE_KEYS[-1]['t']          # fit the take into 64 s ; the final suite arc replaces the old dissolve
for _k in _TAKE_KEYS:
    _k['t'] = round(_k['t'] * _SCALE, 3)
TAKE = dict(name='cinematic', keys=_TAKE_KEYS, door_t=8.3 * _SCALE, door_secs=1.6, caption=None, exp=0.6, fstop=11, lens=(24, 24),
            sec=_TAKE_KEYS[-1]['t'], wp=[])
FINALE = dict(name='finale', keys=_FINALE_KEYS, caption=None, exp=0.6, fstop=11, lens=(24, 24), sec=_FINALE_KEYS[-1]['t'], wp=[])

# a few eased shots for quick tests / stills-in-motion (not part of the one-take cut)
SHOTS = [
    dict(name='hero', sec=6.0, lens=(26, 28), fstop=11, exp=0.6, caption=None, ease=(0.0, 0.5),
         wp=[((-14.0, -20.0, 2.0), (0.5, 4.0, 2.8)), ((-6.0, -18.0, 4.0), (0.5, 4.0, 2.8)), ((4.0, -19.0, 6.0), (0.0, 4.0, 3.0))]),
    dict(name='living', sec=4.0, lens=(20, 20), fstop=5.6, exp=0.15, caption='LIVING ROOM', ease=(0.5, 0.5),
         wp=[((-1.9, 5.2, 1.5), (-5.0, 1.5, 1.1)), ((-2.6, 4.2, 1.45), (-5.6, 2.2, 1.2))]),
]
BY_NAME = {s['name']: s for s in SHOTS}
BY_NAME['take'] = TAKE
BY_NAME['cinematic'] = TAKE
BY_NAME['finale'] = FINALE
CUT = [TAKE]                              # 64 seconds; one physically continuous camera, no internal edit
SHOTS = CUT
