"""Continuous roof envelopes and outward drainage for the Webster reconstruction.

The hero photo fixes the diagonal front edge and level porch/upper eaves. Hidden
pitches are inferred. The former recessed front roof and exposed upper-wing tray
are replaced with complete clay-tile planes. The photographed side terrace stays.
"""
import math
import random
from . import plan as P


def value(plane,x,y):return plane[0]*x+plane[1]*y+plane[2]


def rectangle(x0,x1,y0,y1):return [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]


def area(poly):
    return abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(poly,poly[1:]+poly[:1])))/2 if len(poly)>2 else 0.


def clip(poly,line):
    """Convex polygon clipped to a*x+b*y+c >= 0."""
    out=[]
    for a,b in zip(poly,poly[1:]+poly[:1]):
        da,db=value(line,*a),value(line,*b)
        if da>=-1e-8:out.append(a)
        if (da>0) != (db>0) and abs(da-db)>1e-10:
            t=da/(da-db);out.append((a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1])))
    clean=[]
    for v in out:
        if not clean or math.dist(v,clean[-1])>1e-7:clean.append(v)
    if len(clean)>1 and math.dist(clean[0],clean[-1])<1e-7:clean.pop()
    return clean if area(clean)>1e-8 else []


def difference(a,b):return tuple(x-y for x,y in zip(a,b))


def subtract(poly,occluder):
    """Convex pieces left after subtracting another convex polygon."""
    if not occluder:return [poly]
    result=[];remaining=poly
    for a,b in zip(occluder,occluder[1:]+occluder[:1]):
        line=(-(b[1]-a[1]),b[0]-a[0],(b[1]-a[1])*a[0]-(b[0]-a[0])*a[1])
        outside=clip(remaining,tuple(-v for v in line))
        if outside:result.append(outside)
        remaining=clip(remaining,line)
        if not remaining:break
    return result


# Front roof: the diagonal plane drains +X and slightly toward the street;
# the broad porch plane drains toward the street. Their valley exits at the entry.
_m=(P.RAKE[1][1]-P.RAKE[0][1])/(P.RAKE[1][0]-P.RAKE[0][0])
FRONT_DIAGONAL=(_m,P.FRONT_ROOF_BACK_RISE,P.RAKE[0][1]-_m*P.RAKE[0][0])
_g=(P.FRONT_ROOF_JOIN_Z-P.PENT_EAVE_Z)/(P.UPY0-P.PENT_Y0)
FRONT_PORCH=(0.,_g,P.PENT_EAVE_Z-_g*P.PENT_Y0)
FRONT_PLANES=[FRONT_DIAGONAL,FRONT_PORCH]
FRONT_DOMAINS=[rectangle(-5.80,1.20,-.02,6.01),rectangle(1.20,5.83,P.PENT_Y0,6.01)]


def front_height(x,y):return max(value(p,x,y) for p in FRONT_PLANES)


def front_faces():
    result=[]
    for domain in FRONT_DOMAINS:
        for i,p in enumerate(FRONT_PLANES):
            poly=domain
            for q in FRONT_PLANES:poly=clip(poly,difference(p,q))
            if poly:result.append((f'front_{i}',p,poly))
    return result


# Upper main roof retains the rear gable and original ridge. A low hipped wing
# continues its coverage to the +X eave. Exact plane intersections replace curbs.
_rx=P.UP_RIDGE_X
_k=(P.Z_RIDGE-P.Z_EAVE)/(_rx-P.UPX0)
_yf=P.UPY0-.30;_ze=P.Z_EAVE-_k*.30
UPPER_MAIN_PLANES=[(_k,0.,P.Z_RIDGE-_k*_rx),(-_k,0.,P.Z_RIDGE+_k*_rx),(0.,_k,_ze-_k*_yf)]
UPPER_MAIN=rectangle(P.UPX0-.25,P.UPX1,P.UPY0-.30,P.UPY1+.30)
_wx=P.WINGX1+.30;_wy=P.WINGY1+.30;_wk=.064
UPPER_WING_PLANES=[(-_wk,0.,_ze+_wk*_wx),(0.,_wk,_ze-_wk*_yf),(0.,-_wk,_ze+_wk*_wy)]
_join_x=(UPPER_MAIN_PLANES[1][2]-UPPER_WING_PLANES[0][2])/(_k-_wk)
UPPER_WING=rectangle(_join_x-.025,_wx,_yf,_wy)


def inside(poly,x,y):
    return all((b[0]-a[0])*(y-a[1])-(b[1]-a[1])*(x-a[0])>=-1e-7 for a,b in zip(poly,poly[1:]+poly[:1]))


def upper_height(x,y):
    z=[]
    for domain,planes in ((UPPER_MAIN,UPPER_MAIN_PLANES),(UPPER_WING,UPPER_WING_PLANES)):
        if inside(domain,x,y):z.append(min(value(p,x,y) for p in planes))
    return max(z) if z else P.Z_EAVE


def upper_faces():
    result=[]
    groups=[(UPPER_MAIN,UPPER_MAIN_PLANES),(UPPER_WING,UPPER_WING_PLANES)]
    for gi,(domain,planes) in enumerate(groups):
        other_domain,other_planes=groups[1-gi]
        for pi,p in enumerate(planes):
            poly=domain
            for q in planes:poly=clip(poly,difference(q,p))
            if not poly:continue
            occluder=other_domain
            for q in other_planes:occluder=clip(occluder,difference(q,p))
            for piece in subtract(poly,occluder):
                if area(piece)>1e-6:result.append((f'upper_{gi}_{pi}',p,piece))
    return result


# Side/rear low roofs meet their wall heads and fall toward exterior edges.
# Their membrane finish follows the different roof forms visible in photos 28–30.
LOW_FACES=[
    ('west_front',(.025,0.,3.64+.025*5.75),rectangle(-5.80,P.UPX0,6.0,7.45)),
    ('west_rear',(.025,0.,3.64+.025*5.75),rectangle(-5.80,P.UPX0,11.60,P.BED_REAR+P.WT+.05)),
    ('east',(-.035,0.,3.64+.035*5.75),rectangle(P.WINGX1,5.82,6.0,13.90)),
    ('family_rear',(0.,-.035,3.64+.035*(P.FAMILY_REAR+P.WT)),rectangle(-.40,3.56,P.UPY1,P.FAMILY_REAR+P.WT+.05)),
    ('rear_east',(-.025,0.,3.64+.025*3.5),rectangle(P.UPX1,3.56,P.WINGY1,P.UPY1)),
]


def lower_height(x,y):
    if y<=6.0001 and x>=-5.7501:
        return front_height(x,y)
    for name,p,poly in LOW_FACES:
        if inside(poly,x,y):return value(p,x,y)
    return P.Z_ROOF1


def wall_height(w,a,b):
    x,y=(a,b) if w['along']=='X' else (b,a)
    if w['kind']=='up':return upper_height(x,y)-.020
    if w['kind']=='ext':return lower_height(x,y)-.018
    return w['z1']


def profiled_wall(mb,w,holes,mi=0,paint=False):
    """Wall terminates in the roof thickness; no wall projects above the roof."""
    from . import exterior as E
    along,a0,a1,b0,b1,z0=w['along'],w['a0'],w['a1'],w['b0'],w['b1'],w['z0']
    points={a0,a1}
    points.update(a0+(a1-a0)*i/max(1,math.ceil((a1-a0)/.18)) for i in range(1,max(1,math.ceil((a1-a0)/.18))))
    points.update(v for v in (1.25,1.85,2.05,3.3,5.7,6.,7.45,7.6,11.45,11.6,13.85,15.2) if a0<v<a1)
    ref=(b0+b1)/2
    if paint:ref=w.get('roof_ref_b',ref)
    def height(a):
        h=wall_height(w,a,ref)
        if paint:h=min(h,P.Z_UPC if w['kind']=='up' else P.Z_MC)
        # Entry front head is formed around the Tudor arch by build_entry.
        if w.get('entry_base'):h=E.ARCH_TOP
        return max(z0+.001,h)
    for lo,hi in zip(sorted(points),sorted(points)[1:]):
        zl,zh=height(lo+1e-6),height(hi-1e-6);base=min(zl,zh)
        local_holes=[(max(lo,h0),min(hi,h1),max(z0,hz0),min(base,hz1))
                     for h0,h1,hz0,hz1 in holes if h0<hi and h1>lo and hz0<base and hz1>z0]
        mb.wall(along,lo,hi,b0,b1,z0,base,holes=local_holes,mi=mi)
        if abs(zl-zh)>1e-5:
            E.prism_ab(mb,along,[(lo,base-.001),(hi,base-.001),(hi,zh),(lo,zl)],b0,b1,mi)


def _tiled_face(tile,deck,plane,poly,rng,thickness):
    from mathutils import Vector
    from archviz.mesh import MB
    from . import exterior as E
    top=[(x,y,value(plane,x,y)-.009) for x,y in poly]
    E._slab_poly(deck,top,thickness,0)
    a,b,c=plane;g=math.hypot(a,b)
    u=Vector((a/g,b/g));v=Vector((-u.y,u.x))
    qs=[u.x*x+u.y*y for x,y in poly];bs=[v.x*x+v.y*y for x,y in poly]
    qe,qr=min(qs),max(qs);be,br=min(bs),max(bs)
    patch=MB()
    E._tile_field(patch,qe,g*qe+c-.004,qr,g*qr+c-.004,be,br,rng,along='X',s_end=math.hypot(qr-qe,g*(qr-qe)))
    patch.v=[(u.x*q+v.x*t,u.y*q+v.y*t,z) for q,t,z in patch.v]
    E._append_clipped_roof_tiles(tile,patch,[(x,y,value(plane,x,y)) for x,y in poly])


def _edge_band(mb,a,b,height=.14,width=.035,mi=0):
    from . import exterior as E
    dx,dy=b[0]-a[0],b[1]-a[1];l=math.hypot(dx,dy)
    nx,ny=dy/l*width,-dx/l*width
    E._slab_poly(mb,[a,b,(b[0]+nx,b[1]+ny,b[2]),(a[0]+nx,a[1]+ny,a[2])],height,mi)


def build_front(M):
    from archviz.mesh import MB
    from . import exterior as E
    L=E._local(M);tile=MB();deck=MB();trim=MB();flash=MB();rng=random.Random(18361)
    for name,p,poly in front_faces():_tiled_face(tile,deck,p,poly,rng,P.FRONT_ROOF_THICKNESS)
    # Closing fascia at the roof's side edges and the lower roofs behind it.
    for a,b in [((-5.80,-.02),(-5.80,6.01)),((5.83,1.25),(5.83,6.01)),((-5.80,6.01),(P.UPX0,6.01))]:
        _edge_band(trim,(*a,front_height(*a)-.015),(*b,front_height(*b)-.015),mi=0)
    # Finish the proud entry's front gable above the arched door.
    E.prism_y(deck,[(-1.25,E.ARCH_TOP-.01),(1.2,E.ARCH_TOP-.01),(1.2,E._zr(1.2)-.025),(-1.25,E._zr(-1.25)-.025)],E.TOWER_Y,.25,0)
    E._slab_poly(deck,[(-1.25,E.TOWER_Y+.18,E._zr(-1.25)-.02),(1.2,E.TOWER_Y+.18,E._zr(1.2)-.02),
                      (1.2,.03,front_height(1.2,.03)-.01),(-1.25,.03,front_height(-1.25,.03)-.01)],.055,0)
    # Roof-to-wall flashing follows the actual roof height, below all window apertures.
    for x0,x1 in ((P.UPX0,P.UPX1),(P.WINGX0,P.WINGX1)):
        n=80
        for i in range(n):
            x=x0+(x1-x0)*i/n;xx=x0+(x1-x0)*(i+1)/n
            z,zz=front_height(x,6),front_height(xx,6)
            E.prism_y(flash,[(x,z-.025),(xx,zz-.025),(xx,zz+.055),(x,z+.055)],5.985,6.008,0)
    deck.build('Ext_FrontRoof_Deck',[L['soffit']],coll='House')
    tile.build('Ext_FrontRoof_Tiles',[L['tile']],coll='House',smooth=True)
    trim.build('Ext_FrontRoof_Fascia',[M['trim']],coll='House')
    flash.build('Ext_FrontRoof_Flashing',[L['galv']],coll='House')
    # Front gutter has fall to the entry downspout; the valley also discharges here.
    gutter=MB();yy=P.PENT_Y0-.065
    gutter.path_tube([(1.23,yy,2.62),(5.82,yy,2.65)],.045,seg=14,mi=0)
    gutter.path_tube([(1.23,yy,2.62),(1.23,-.23,2.51),(1.13,-.27,2.42)],.042,seg=12,mi=0)
    gutter.build('Ext_FrontRoof_Gutter',[L['gutter']],coll='House',smooth=True)


def build_upper(M):
    from archviz.mesh import MB
    from . import exterior as E
    L=E._local(M);tile=MB();deck=MB();trim=MB();rng=random.Random(1136)
    faces=upper_faces()
    for name,p,poly in faces:_tiled_face(tile,deck,p,poly,rng,.09)
    outline=[(P.UPX0-.25,_yf),(_wx,_yf),(_wx,_wy),(P.UPX1,_wy),(P.UPX1,P.UPY1+.30),(P.UPX0-.25,P.UPY1+.30)]
    for a,b in zip(outline,outline[1:]+outline[:1]):
        # Subdivide gable edges and intersections, keeping fascia beneath the tiled envelope.
        n=max(1,math.ceil(math.dist(a,b)/.1))
        for i in range(n):
            aa=(a[0]+(b[0]-a[0])*i/n,a[1]+(b[1]-a[1])*i/n)
            bb=(a[0]+(b[0]-a[0])*(i+1)/n,a[1]+(b[1]-a[1])*(i+1)/n)
            _edge_band(trim,(*aa,upper_height(*aa)-.01),(*bb,upper_height(*bb)-.01),mi=0)
    # Main ridge cap remains at the photographed rear-gable ridge.
    E._lapped_tubes(tile,(_rx,P.UPY0+3.1,P.Z_RIDGE+.05),(_rx,P.UPY1+.30,P.Z_RIDGE+.05),r=.07,L=.40,lap=.07)
    tile.build('Ext_RoofTile',[L['tile']],coll='House',smooth=True)
    deck.build('Ext_RoofSoffit',[L['soffit']],coll='House')
    trim.build('Ext_UpperRoofFascia',[M['trim']],coll='House')


def build_low_rear(M):
    from archviz.mesh import MB
    from . import exterior as E
    L=E._local(M);roof=MB();trim=MB();gutter=MB()
    for name,p,poly in LOW_FACES:
        E._slab_poly(roof,[(x,y,value(p,x,y)) for x,y in poly],.05,0)
        for a,b in zip(poly,poly[1:]+poly[:1]):
            _edge_band(trim,(*a,value(p,*a)),(*b,value(p,*b)),height=.065,mi=0)
        if abs(p[0])<1e-8 and p[1]<0:
            patch=MB();edge=max(v[1] for v in poly)
            E._trough(patch,edge+.04,min(v[0] for v in poly),max(v[0] for v in poly),value(p,0,edge)-.045,.055,0)
            patch.v=[(y,x,z) for x,y,z in patch.v]
            offset=len(gutter.v);gutter.v.extend(patch.v);gutter.f.extend(tuple(offset+i for i in f) for f in patch.f);gutter.fm.extend(patch.fm)
            continue
        x=min(v[0] for v in poly) if p[0]>0 else max(v[0] for v in poly)
        y0,y1=min(v[1] for v in poly),max(v[1] for v in poly)
        E._trough(gutter,x+(-.04 if p[0]>0 else .04),y0,y1,value(p,x,y0)-.045,.055,0)
    roof.build('Ext_LowRoof_Deck',[M['roof_flat']],coll='House')
    trim.build('Ext_LowRoofFascia',[L['cap']],coll='House')
    gutter.build('Ext_LowRoofGutters',[L['gutter']],coll='House',smooth=True)
