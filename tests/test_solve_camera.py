import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from solve_camera import project, solve              # noqa: E402
import solve_scene                                     # noqa: E402

BOX = np.array([[x, y, z] for x in (0.0, 4.0, 9.0) for y in (0.0, 1.5) for z in (0.0, 2.5, 5.0)])


def test_level_camera_with_shift_is_recovered():
    truth = [2.0, -14.0, 1.4, 12.0, 26.0, 0.03, 0.12]
    uv, depth = project(truth, BOX, (1536, 1024), 'level')
    assert (depth > 0).all()
    sol, res = solve((1536, 1024), BOX, uv, {'loc': [0, -10, 2], 'yaw': 0, 'lens': 20}, 'level')
    assert np.abs(res).max() < 0.05
    got = [sol[k] for k in ('x', 'y', 'z', 'yaw', 'lens', 'shift_x', 'shift_y')]
    assert np.allclose(got, truth, atol=1e-3)


def test_free_camera_with_pitch_is_recovered():
    truth = [5.0, -40.0, 30.0, 3.0, -30.0, 35.0]
    uv, _ = project(truth, BOX, (1536, 1152), 'free')
    sol, res = solve((1536, 1152), BOX, uv, {'loc': [4, -35, 25], 'yaw': 0, 'pitch': -25, 'lens': 30}, 'free')
    assert np.abs(res).max() < 0.05
    assert math.isclose(sol['pitch'], -30.0, abs_tol=1e-3)


def test_scene_solve_recovers_a_plan_unknown(tmp_path):
    """A setback seen from two cameras is determined; the solver returns it with the cameras."""
    cams = {'a': [0.0, -12.0, 1.5, 10.0, 24.0, 0.0, 0.1], 'b': [8.0, -11.0, 1.6, -15.0, 26.0, 0.05, 0.08]}
    setback = 1.35
    pts3 = [[x, setback if z > 3 else 0.0, z] for x in (0.0, 3.0, 6.0) for z in (0.0, 2.0, 4.0, 5.5)]
    cfg = {'unknowns': {'s': 0.5}, 'photos': {}}
    for key, cam in cams.items():
        uv, _ = project(cam, np.array(pts3), (1536, 1024), 'level')
        cfg['photos'][key] = {'size': [1536, 1024], 'model': 'level',
                              'init': {'loc': [cam[0] + 1, cam[1] + 1, 1.2], 'yaw': cam[3] + 4, 'lens': 22},
                              'points': [[u, v, p[0], 's' if p[2] > 3 else 0.0, p[2]] for (u, v), p in zip(uv.tolist(), pts3)]}
    (tmp_path / 'c.json').write_text(json.dumps(cfg))
    names, photos, x, r, se = solve_scene.solve(json.loads((tmp_path / 'c.json').read_text()))
    assert math.isclose(x[names.index('s')], setback, abs_tol=1e-3)
    assert np.abs(r).max() < 0.05
