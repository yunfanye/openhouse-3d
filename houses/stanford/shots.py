"""13695 Stanford Dr — one continuous ~62-second golden-hour take (bpy-free).

Pond -> the rear -> around the sunlit left side -> front door -> foyer / living room / stair -> hall -> great room ->
around the kitchen island -> dining slider -> patio -> crane back over the lawn.  Re-routed in the 2026-09-24 review
(the stair, foyer wall, kitchen, dining set, front tree and fountain moved).  One camera, no cuts.  Keys are timed in seconds;
positions are metres in plan.py coordinates; the look direction is interpolated as a unit vector (archviz.film).
"""
TITLES = dict(main="13695 STANFORD DRIVE", sub="CARMEL, INDIANA", end="A LAKESIDE HOME IN STANFORD PARK")

H = 1.55                                 # interior eye height


def K(t, cam, tgt, lens, fstop, exp, label=''):
    return dict(t=t, cam=cam, tgt=tgt, lens=lens, fstop=fstop, exp=exp, label=label)


_KEYS = [
    # ---- the pond at golden hour: close on the backlit fountain (-14.1, 92.1), then skimming the water toward the house row
    K(0.0,  (-22.0, 104.0, 1.6),  (-14.0, 92.0, 3.0),   30, 11, -0.2, 'the fountain, backlit'),
    K(3.0,  (-9.5, 99.0, 2.0),    (-5.0, 78.0, 3.2),    28, 11, -0.2, 'drifting past the spray'),
    K(6.2,  (-1.0, 78.0, 4.5),    (5.0, 30.0, 5.0),     26, 11, -0.2, 'rising: the house row across the water'),
    K(9.2,  (3.0, 56.0, 12.5),    (6.0, 15.0, 5.0),     25, 11, -0.2, 'toward the shore, climbing'),
    K(11.9, (5.0, 42.0, 17.5),    (6.0, 10.0, 5.0),     25, 11, -0.2, 'over the path trees'),
    K(14.4, (9.0, 26.0, 14.0),    (6.0, 6.0, 4.0),      25, 11, -0.2, 'the rear of the house'),
    # ---- around the sunlit left side (the enlarged front tree fills the right-hand approach) to photo 01's viewpoint
    K(16.8, (-5.0, 15.0, 12.5),   (6.0, 6.0, 3.5),      25, 11, -0.2, 'orbiting the rear-left corner'),
    K(19.2, (-5.5, -3.0, 11.0),   (6.0, 3.0, 3.0),      25, 11, -0.2, 'the sunlit front-left three-quarter'),
    K(21.4, (-0.5, -10.5, 4.0),   (6.0, 1.5, 3.0),      24, 11, -0.2, 'around the front-left corner'),
    K(23.2, (5.3, -13.4, 2.0),    (6.2, 1.0, 3.2),      23, 10, -0.2, 'the facade (door opening)'),
    K(25.0, (5.0, -5.8, 1.7),     (7.3, 1.5, 1.6),      22, 9, -0.2, 'up the drive'),
    K(26.3, (6.9, -1.7, 1.62),    (7.9, 3.0, 1.45),     22, 9, -0.2, 'the walk to the open door'),
    K(27.5, (7.8, 0.7, H),        (7.95, 5.0, 1.4),     21, 8, -0.4, 'through the front door'),
    # ---- foyer, living room and the stair (moved 1 m back in the 2026-09-24 review); into the hall past the foyer wall
    K(29.2, (7.95, 2.45, H),      (10.8, 4.4, 1.35),    20, 8, -0.3, 'the living room opens on the right'),
    K(30.6, (8.25, 3.5, H),       (10.3, 6.0, 2.6),     20, 8, -0.3, 'the stair, looking up'),
    K(31.4, (8.05, 4.1, H),       (8.4, 7.2, 1.9),      20, 8, -0.3, 'past the stair foot'),
    K(32.3, (7.6, 4.75, H),       (6.5, 7.0, 1.45),     20, 8, -0.3, 'turning toward the hall'),
    K(33.3, (7.0, 5.65, H),       (6.8, 8.5, 1.4),      20, 8, -0.3, 'the hall'),
    # ---- great room: fireplace -> rear windows and the swing -> across the dining to the kitchen
    K(34.6, (6.75, 7.35, H),      (3.0, 9.8, 1.3),      19, 8, -0.3, 'into the great room: the fireplace'),
    K(36.2, (6.0, 7.9, H),        (0.4, 9.1, 1.2),      19, 8, -0.3, 'toward the fireplace'),
    K(38.0, (5.75, 8.95, H),      (1.6, 12.2, 1.25),    19, 8, -0.35, 'the rear windows'),
    K(39.6, (5.8, 9.35, H),       (5.4, 13.0, 1.25),    19, 8, -0.35, 'the swing'),
    K(40.8, (5.85, 9.3, H),       (8.6, 12.6, 1.2),     19, 8, -0.3, 'turning toward the dining'),
    K(42.0, (5.95, 9.2, H),       (10.6, 9.6, 1.1),     19, 8, -0.3, 'across the dining to the kitchen'),
    # ---- kitchen: past the table's south end, the south aisle, around the island's east end, the north aisle
    K(43.2, (6.4, 8.3, H),        (10.8, 9.6, 1.05),    20, 8, -0.3, 'past the dining table'),
    K(44.4, (8.35, 8.45, H),      (11.4, 10.0, 1.05),   20, 8, -0.3, 'into the kitchen'),
    K(45.6, (9.45, 8.5, H),       (11.6, 10.9, 1.1),    20, 8, -0.3, 'the island and the range wall'),
    K(46.8, (10.4, 8.75, H),      (10.2, 11.6, 1.15),   20, 8, -0.3, 'the sink window'),
    K(48.0, (10.55, 9.85, H),     (9.0, 11.3, 1.15),    20, 8, -0.3, 'around the island'),
    K(49.2, (9.55, 10.65, H),     (7.4, 11.4, 1.2),     20, 8, -0.35, 'turning to the patio doors (sliding open)'),
    K(50.4, (8.45, 10.95, H),     (6.9, 12.8, 1.25),    20, 8, -0.4, 'the open slider'),
    K(51.3, (7.55, 11.3, H),      (7.1, 14.5, 1.2),     21, 8, -0.4, 'to the slider'),
    K(52.1, (7.05, 11.8, H - 0.05), (6.95, 16.0, 1.2),  21, 8, -0.3, 'through the slider'),
    # ---- the patio, a rising 180-degree turn, and the pull-back over the lawn to the house at sunset
    K(53.3, (6.95, 13.5, 1.5),    (6.6, 22.0, 1.4),     22, 9, -0.3, 'onto the patio'),
    K(54.8, (6.4, 16.3, 2.6),     (-0.2, 20.5, 2.0),    23, 10, -0.3, 'rising, turning left'),
    K(56.4, (4.8, 19.6, 4.8),     (-3.5, 14.5, 2.5),    24, 11, -0.3, 'still turning'),
    K(58.0, (3.4, 22.6, 7.4),     (5.0, 11.0, 4.0),     24, 11, -0.3, 'the house at sunset'),
    K(61.4, (3.5, 32.0, 15.0),    (6.0, 7.0, 4.0),      25, 11, -0.3, 'pulling back over the lawn'),
    K(64.4, (3.0, 40.5, 18.2),    (6.0, 7.5, 5.0),      26, 11, -0.3, 'over the lawn, the end card'),
    K(66.0, (2.85, 43.0, 19.3),   (6.0, 7.5, 5.2),      26, 11, -0.3, 'end'),
]
TAKE = dict(name='cinematic', keys=_KEYS, door_t=22.4, door_secs=1.8, slider_t=48.8, slider_secs=1.6, caption=None,
            exp=0.0, fstop=11, lens=(24, 24), sec=_KEYS[-1]['t'], wp=[])
SHOTS = [TAKE]
BY_NAME = {'cinematic': TAKE, 'take': TAKE}
