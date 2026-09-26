"""Wall/opening operations in metres, shared by procedural house plans (no bpy).

Walls use along=X|Y, a0/a1 (span), b0/b1 (thickness), z0/z1.
Openings use name, along, a0/a1, b (wall plane), z0/z1.
An opening may touch a wall boundary, but only positive overlap counts.
"""


def overlapping(wall, opening, tolerance=1e-4):
    return (wall['along'] == opening['along']
            and wall['b0'] - tolerance <= opening['b'] <= wall['b1'] + tolerance
            and opening['a0'] < wall['a1'] and opening['a1'] > wall['a0']
            and opening['z0'] < wall['z1'] and opening['z1'] > wall['z0'])


def holes_for(wall, openings, tolerance=1e-4):
    holes = []
    for opening in openings:
        if not overlapping(wall, opening, tolerance):
            continue
        a0, a1 = max(opening['a0'], wall['a0']), min(opening['a1'], wall['a1'])
        z0, z1 = max(opening['z0'], wall['z0']), min(opening['z1'], wall['z1'])
        if a1 - a0 > tolerance and z1 - z0 > tolerance:
            holes.append((a0, a1, z0, z1))
    return sorted(holes)


def unmatched_openings(walls, openings):
    bad = []
    for opening in openings:
        count = sum(overlapping(wall, opening) for wall in walls)
        if count != 1:
            bad.append((opening['name'], count))
    return bad


def validate(walls, openings):
    """Reject malformed dimensions, duplicate names, and uncontained openings."""
    for label, records in [('wall', walls), ('opening', openings)]:
        names = set()
        for item in records:
            if item['along'] not in ('X', 'Y'):
                raise ValueError(f'Invalid {label} axis: {item}')
            for low, high in [('a0', 'a1'), ('z0', 'z1')] + ([('b0', 'b1')] if label == 'wall' else []):
                if not item[low] < item[high]:
                    raise ValueError(f'Invalid {label} bounds: {item}')
            if 'name' in item:
                if item['name'] in names:
                    raise ValueError(f'Duplicate {label} name: {item["name"]}')
                names.add(item['name'])
    bad = unmatched_openings(walls, openings)
    if bad:
        raise ValueError(f'Openings must overlap exactly one wall: {bad}')
    for opening in openings:
        wall = next(w for w in walls if overlapping(w, opening))
        if any(opening[lo] < wall[lo] - 1e-4 or opening[hi] > wall[hi] + 1e-4
               for lo, hi in [('a0', 'a1'), ('z0', 'z1')]):
            raise ValueError(f'Opening extends beyond wall: {opening["name"]}')
