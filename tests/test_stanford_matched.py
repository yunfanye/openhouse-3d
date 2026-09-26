import json
from pathlib import Path

from archviz import filmkit
from archviz.comparison import validate_timeline
from houses.stanford import matched_take as mt

HOUSE = Path(mt.__file__).resolve().parent
# Key times and labels of the independent reconstruction's houses/stanford/cinematic.py (the film this take matches).
OTHER_TIMES = [0, 4, 8, 10, 12, 14, 16, 18, 19.5, 21, 24, 25.5, 27, 29, 31.5, 34, 35, 36, 37.5, 39, 40.5, 43, 44.5, 46.5,
               48, 49, 49.7, 50.3, 51.5, 53.5, 55.5, 57.5, 58.5, 59.5, 62, 64, 66, 67, 68, 71, 73, 75, 77.5, 80]
OTHER_LABELS = {0: 'Aerial arrival', 12: 'Welcome home', 16: 'Oak stair', 27: 'Primary retreat', 53.5: 'Gather beautifully',
                62: 'Oak kitchen', 68: 'Pond-side living', 80: 'A place by the water'}
OTHER_LENSES = [32, 29, 25, 22, 21, 21, 21, 21, 21, 21, 21, 21, 21, 22, 22, 22, 21, 21, 21, 21, 21, 21, 21, 21,
                21, 21, 21, 21, 21, 21, 22, 22, 21, 21, 22, 22, 21, 22, 23, 25, 25, 27, 29, 32]


def test_matched_take_keeps_the_other_films_timing_and_lenses():
    keys = mt.TAKE['keys']
    assert [k['t'] for k in keys] == OTHER_TIMES
    assert {k['t']: k['label'] for k in keys if k['label']} == OTHER_LABELS
    assert [k['lens'] for k in keys] == OTHER_LENSES
    assert {k['fstop'] for k in keys} == {8}
    assert filmkit.frames_of(mt.TAKE) == 1921
    assert (mt.TAKE['door_t'], mt.TAKE['door_secs']) == (7.0, 2.5)
    assert mt.TAKE['position_tension'] == 0.6 and mt.TAKE['angular_aim'] is True


def test_matched_take_door_schedules_are_ordered():
    for name in ('powder', 'slider'):
        times = [t for t, _ in mt.TAKE[name]]
        assert times == sorted(times) and 0 < times[0] and times[-1] < 80
    assert [state for _, state in mt.TAKE['powder']] == ['open', 'closed']
    assert all(0.0 <= frac <= 1.0 for _, frac in mt.TAKE['slider'])


def test_lower_flight_eye_heights():
    assert mt.tread(mt.ST_X0 - 0.3) == mt.H
    assert abs(mt.tread(mt.ST_X0 + 0.01) - (mt.RISE + mt.H)) < 1e-9
    assert abs(mt.tread(mt.ST_X0 + 6 * mt.TREAD - 0.01) - (6 * mt.RISE + mt.H)) < 1e-9
    assert mt.tread(mt.ST_X0 + 9) == 6 * mt.RISE + mt.H


def test_matched_comparison_timeline_is_valid():
    data = validate_timeline(json.loads((HOUSE / 'matched_comparison_timeline.json').read_text()))
    assert data['frames'] == filmkit.frames_of(mt.TAKE)
    assert len(data['segments']) == 20
    assert all(1 <= s['photo'] <= 32 for s in data['segments'])
