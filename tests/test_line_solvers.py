import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import backproject                                       # noqa: E402
import intcam_solve                                      # noqa: E402
import joint_solve_lines                                 # noqa: E402
from solve_camera import project as project7             # noqa: E402

SIZE = (1536, 1024)
ROOM = dict(x0=0.0, x1=5.0, y0=0.0, y1=4.0, z0=0.0, z1=2.44)


def _truth():
    return dict(x=1.2, y=0.6, z=1.05, yaw=38.0, pitch=0.0, roll=0.0, lens=17.0, shift_x=0.012, shift_y=-0.02, aspect=1.0)


def _room_readings(cam):
    """A few corner points plus points read along the far walls' ceiling and floor lines (as a photo gives them)."""
    r = ROOM
    corners = [(r['x1'], r['y1'], r['z0']), (r['x1'], r['y1'], r['z1']), (r['x0'], r['y1'], r['z1']), (r['x1'], r['y0'] + 1.0, r['z1'])]
    uv, _ = intcam_solve.project(cam, np.array(corners), SIZE)
    points = [[float(u), float(v), *p, f'c{i}'] for i, ((u, v), p) in enumerate(zip(uv, corners))]
    edges = [((r['x0'], r['y1'], r['z1']), (r['x1'], r['y1'], r['z1'])), ((r['x0'], r['y1'], r['z0']), (r['x1'], r['y1'], r['z0'])),
             ((r['x1'], r['y0'], r['z1']), (r['x1'], r['y1'], r['z1'])), ((r['x1'], r['y0'], r['z0']), (r['x1'], r['y1'], r['z0']))]
    lines = []
    for a, b in edges:
        for t in (0.25, 0.5, 0.8):
            p = np.array(a) + (np.array(b) - np.array(a)) * t
            (u, v), = intcam_solve.project(cam, p[None, :], SIZE)[0]
            lines.append([float(u), float(v), list(a), list(b), 'edge'])
    return points, lines


def test_intcam_point_and_line_solve_recovers_a_level_camera():
    cam = _truth()
    points, lines = _room_readings(cam)
    cfg = {'size': list(SIZE), 'model': 'level', 'points': points, 'lines': lines,
           'init': {'loc': [1.6, 0.9, 1.3], 'yaw': 30.0, 'lens': 20.0}}
    prob = intcam_solve.Problem(cfg)
    x, _ = prob.solve()
    _, (got,) = prob.unpack(x)
    assert np.abs(prob.resid(x)).max() < 0.05
    for k in ('x', 'y', 'z', 'yaw', 'lens', 'shift_x', 'shift_y'):
        assert abs(got[k] - cam[k]) < 1e-3, k


def test_joint_line_solve_recovers_a_plan_unknown(tmp_path):
    """Two photos see a wall whose depth s is unknown; lines along its top and points at its ends pin it."""
    s_true = 1.35
    cams = {'a': dict(x=0.0, y=-12.0, z=1.5, yaw=10.0, pitch=0.0, roll=0.0, lens=24.0, shift_x=0.0, shift_y=0.1, aspect=1.0, skew=0.0),
            'b': dict(x=8.0, y=-11.0, z=1.6, yaw=-15.0, pitch=0.0, roll=0.0, lens=26.0, shift_x=0.05, shift_y=0.08, aspect=1.0, skew=0.0)}
    photos = {}
    for key, c in cams.items():
        pts3 = np.array([[x, 0.0, z] for x in (0.0, 3.0, 6.0) for z in (0.0, 2.0)] + [[x, s_true, 5.5] for x in (0.0, 6.0)])
        uv, _ = joint_solve_lines.project(c, pts3, SIZE)
        pts = [(float(u), float(v), float(p[0]), 's' if p[1] else 0.0, float(p[2]), f'p{i}') for i, ((u, v), p) in enumerate(zip(uv, pts3))]
        mid, _ = joint_solve_lines.project(c, np.array([[2.0, s_true, 5.5], [4.5, s_true, 5.5]]), SIZE)
        pts += [('L', float(u), float(v), (0.0, 's', 5.5), (6.0, 's', 5.5), 'top') for (u, v) in mid]
        photos[key] = dict(size=SIZE, model='level', points=pts,
                           init=dict(loc=(c['x'] + 0.5, c['y'] + 1.0, c['z'] + 0.3), yaw=c['yaw'] + 3.0, lens=c['lens'] + 2.0))
    cfg = tmp_path / 'cfg.py'
    cfg.write_text(f"UNK = {{'s': 0.5}}\nPHOTOS = {photos!r}\n")
    _, names, _, x, r, _ = joint_solve_lines.solve(str(cfg))
    assert abs(x[names.index('s')] - s_true) < 1e-3
    assert np.abs(r).max() < 0.05


def test_backproject_inverts_the_level_projection():
    sol = dict(x=2.0, y=-14.0, z=1.4, yaw=12.0, lens=26.0, shift_x=0.03, shift_y=0.12)
    ground = np.array([[1.0, 2.0, -0.4], [6.5, 9.0, -0.4], [-3.0, 20.0, -0.4]])
    uv, _ = project7([sol[k] for k in ('x', 'y', 'z', 'yaw', 'lens', 'shift_x', 'shift_y')], ground, SIZE, 'level')
    cam = backproject.camera(sol, SIZE)
    for (u, v), g in zip(uv, ground):
        assert np.allclose(backproject.to_plane(cam, SIZE, u, v, -0.4), g, atol=1e-6)
