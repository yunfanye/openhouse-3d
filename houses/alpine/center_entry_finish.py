"""Keep the center-door sightline open in the inferred garden staging."""
import bpy

def apply(scene):
    if scene.get('Alpine center entry staging'):return
    scene['Alpine center entry staging']=True
    ob=bpy.data.objects.get('Clipped garden sphere 0 27.4')
    if not ob:return
    for part in [ob,*list(ob.children)]:
        if part.type!='MESH':continue
        for v in part.data.vertices:
            v.co.x*=.85
            v.co.y=27.4+(v.co.y-27.4)*.85
            v.co.z*=.72
        part.data.update()
    ob.location.x-=1.65
