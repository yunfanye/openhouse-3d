"""Recess the west kitchen run while retaining appliance dimensions and door locations."""
import bpy

SETBACK = .60
FIXTURE_OBJECTS = ('Back_KitCabinets', 'Back_KitCounters', 'Back_KitAppliances',
                   'Back_KitMirror', 'Back_KitStaging', 'Back_OriginalDecoTileBand')


def recess_fixtures():
    counts={}
    for name in FIXTURE_OBJECTS:
        ob=bpy.data.objects[name]
        if ob.get('kitchen_setback_m'):
            assert abs(ob['kitchen_setback_m']-SETBACK)<1e-6
            continue
        vertices=[v for v in ob.data.vertices if v.co.x<3.0]
        assert vertices,(name,'missing west run')
        for v in vertices:v.co.x-=SETBACK
        ob.data.update();ob['kitchen_setback_m']=SETBACK
        counts[name]=len(vertices)
    return counts
