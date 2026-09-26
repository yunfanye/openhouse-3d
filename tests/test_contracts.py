import json
from pathlib import Path

from archviz import filmkit
from houses.webster import house, plan


def test_webster_plan_contract():
    assert len(plan.WALLS) == 64
    assert len(plan.OPENINGS) == 56
    assert plan.check() == []
    baseline = Path(__file__).with_name('fixtures') / 'webster_holes.json'
    assert json.loads(json.dumps([plan.holes_for(w) for w in plan.WALLS])) == json.loads(baseline.read_text())


def test_webster_photo_inventory():
    assert sorted(n for _, n in house.PHOTO_PAIRS if n < 99) == list(range(31))


def test_take_endpoint_is_inclusive():
    assert filmkit.frames_of({'sec': 64, 'keys': []}) == 1537
    assert filmkit.frames_of({'sec': 64}) == 1536
    assert filmkit.frames_of(house.TAKE) == 1537


def test_frame_configuration_does_not_leak_between_houses(tmp_path):
    filmkit.configure(str(tmp_path / 'a'), 'draft')
    filmkit.configure(str(tmp_path / 'b'))
    assert filmkit.FRAMES == 'frames'


def test_full_webster_opening_containment():
    from archviz.plan import validate
    validate(plan.WALLS, plan.OPENINGS)
