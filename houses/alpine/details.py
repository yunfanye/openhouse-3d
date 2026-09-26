"""Reusable traditional architectural details, all geometry in metres."""
import math
from mathutils import Vector
from archviz.mesh import MB, collection
from archviz.lights import add_light
from archviz import parts

class B(MB):
    def __init__(self,M):
        super().__init__();self.M=M;self.keys=list(M);self.i={k:j for j,k in enumerate(self.keys)}
    def pillow(self,cx,cy,cz,w=.6,d=.42,t=.16,mi=0,rot=0,tilt=0,pitch=0):
        self.pillow_sq(cx,cy,cz,w,d,t,mi,rot=rot,pitch=pitch,nx=22,ny=18,dome=.42,p=3.1)
    def done(self,name,coll='House',bevel=0,smooth=False):
        return self.build(name,list(self.M.values()),coll=coll,bevel=bevel,smooth=smooth,auto_smooth=bool(bevel))
    def merge(self,other,origin=(0,0,0),rot=0):
        c,s=math.cos(rot),math.sin(rot);x,y,z=origin
        base=len(self.v)
        self.v.extend((x+a*c-b*s,y+a*s+b*c,z+h) for a,b,h in other.v)
        self.f.extend(tuple(base+j for j in f) for f in other.f);self.fm.extend(other.fm)

def box(M,name,bounds,key,bevel=0,coll='House'):
    b=B(M);b.box(*bounds,b.i[key]);return b.done(name,coll,bevel)

def path_tube(b,pts,r,mi,seg=10):
    # Connected rings give a continuous polished rail rather than visibly jointed cylinders.
    sections=[]
    for j,p in enumerate(pts):
        d=Vector(pts[min(j+1,len(pts)-1)])-Vector(pts[max(0,j-1)])
        q=d.normalized().to_track_quat('Z','Y')
        sections.append([Vector(p)+q@Vector((r*math.cos(2*math.pi*i/seg),r*math.sin(2*math.pi*i/seg),0)) for i in range(seg)])
    b.sweep(sections,mi)

def column(b,x,y,z,h,r=.235):
    i=b.i['trim']
    b.cbox(x,y,z+.075,r*2.9,r*2.9,.15,i)
    profile=[(r*1.32,.15),(r*1.32,.20),(r*1.17,.23),(r*1.14,.27),(r,.32),(r*.96,h*.20),(r*.84,h-.27),(r*.94,h-.24),(r*1.1,h-.18),(r*1.15,h-.13)]
    b.lathe(x,y,z,profile,seg=40,mi=i)
    b.cbox(x,y,z+h-.065,r*2.7,r*2.7,.13,i)

def baluster(b,x,y,z,h=.85):
    i=b.i['trim'];r=.04
    b.cbox(x,y,z+.07,.10,.10,.14,i)
    profile=[(r,.14),(r*1.17,.17),(r,.20),(r*.64,.24),(r*.66,.36),(r*1.1,.43),(r*1.18,.48),(r*.82,.54),(r*.58,.61),(r*.7,.66),(r*1.1,.69),(r*1.1,.73),(r,.75)]
    b.lathe(x,y,z,[(rr,zz*h/.85) for rr,zz in profile],seg=12,mi=i)
    b.cbox(x,y,z+h-.05,.1,.1,.1,i)

def rail(b,p0,p1,h=.95,wood=False,spacing=.2):
    a,c=Vector(p0),Vector(p1);n=max(1,round((c-a).length/spacing))
    for j in range(n+1):
        p=a.lerp(c,j/n);baluster(b,p.x,p.y,p.z,h-.13)
    path_tube(b,[tuple(a+Vector((0,0,h-.06))),tuple(c+Vector((0,0,h-.06)))],.043,b.i['walnut' if wood else 'trim'])
    path_tube(b,[tuple(a+Vector((0,0,.035))),tuple(c+Vector((0,0,.035)))],.05,b.i['trim'])

def panel(b,x0,x1,y,z0,z1,key='trim',w=.026):
    b.frame(x0,x1,y-.018,y+.018,z0,z1,w,b.i[key])
    b.frame(x0+.016,x1-.016,y-.022,y+.022,z0+.016,z1-.016,.012,b.i[key])

def casing(b,w,h):
    for d,thick,off in ((.085,.09,0),(.14,.055,.085),(.17,.032,.14)):
        b.frame(-w/2-d,w/2+d,-.10-off/3,.03,0,h+d,thick,b.i['trim'])

def window(M,name,pos,w=1.85,h=2.75,rot=0,shutters=True,opening=False,blinds=True):
    b=B(M);i=b.i;casing(b,w,h)
    if not opening:
        b.box(-w/2+.05,w/2-.05,.008,.02,.07,h-.06,i['glass'])
        b.frame(-w/2,w/2,-.035,.05,0,h,.065,i['trim'])
        b.box(-.034,.034,-.06,.052,0,h,i['trim'])
        for x in (-w/4,w/4):
            b.box(x-.014,x+.014,-.024,.038,.065,h-.065,i['trim'])
        for j in range(1,7):
            z=j*h/7;b.box(-w/2,w/2,-.023,.04,z-.013,z+.013,i['trim'])
        if blinds:
            for side in (-1,1):
                cx=side*w*.34
                b.frame(cx-w*.14,cx+w*.14,.13,.16,.06,h-.08,.032,i['trim'])
                for j in range(int(h/.10)):
                    z=.1+j*.10
                    # louvers tilted open 45 degrees
                    b.hexa([(cx-w*.14,.17,z-.018),(cx+w*.14,.17,z-.018),(cx+w*.14,.225,z+.029),(cx-w*.14,.225,z+.029),(cx-w*.14,.173,z-.027),(cx+w*.14,.173,z-.027),(cx+w*.14,.229,z+.020),(cx-w*.14,.229,z+.020)],i['trim'])
    else:
        # Real open French leaves folded toward the interior, clear center aperture.
        for side in (-1,1):
            leaf=B(M);ww=w/2-.025
            leaf.frame(0,ww,-.028,.028,.03,h-.04,.065,i['trim'])
            leaf.box(.055,ww-.055,-.008,.007,.10,h-.1,i['glass'])
            for j in range(1,7):leaf.box(.02,ww-.02,-.028,.028,j*h/7-.013,j*h/7+.013,i['trim'])
            leaf.box(ww/2-.013,ww/2+.013,-.025,.025,.06,h-.06,i['trim'])
            b.merge(leaf,(-w/2 if side<0 else w/2,0,0),math.radians(98 if side<0 else 82))
    # Interior architraves and painted returns conceal the brick reveals.
    b.frame(-w/2-.13,w/2+.13,.34,.47,-.04,h+.13,.11,i['trim'])
    for side in (-1,1):
        xx=side*(w/2-.025);b.box(xx-.025,xx+.025,.035,.45,0,h,i['trim'])
    b.box(-w/2,w/2,.035,.45,h-.025,h+.02,i['trim'])
    if shutters:
        for side in (-1,1):
            cx=side*(w/2+.46);sw=.68
            b.box(cx-sw/2,cx+sw/2,-.02,.022,-.05,h+.06,i['shutter'])
            b.frame(cx-sw/2,cx+sw/2,-.068,.032,-.05,h+.06,.045,i['shutter'])
            for j in range(int(h/.075)):
                b.box(cx-sw/2+.05,cx+sw/2-.05,-.075,-.03,j*.075,j*.075+.035,i['shutter'])
    out=B(M);out.merge(b,pos,rot);return out.done(name,bevel=.004)

def portal(M,name,pos,w,h,rot=0,arch=False):
    b=B(M);casing(b,w,h)
    if arch:
        pts=[(w*.5*math.cos(a),-.10,h+w*.26*math.sin(a)) for a in [j*math.pi/48 for j in range(49)]]
        path_tube(b,pts,.055,b.i['trim'])
    out=B(M);out.merge(b,pos,rot);return out.done(name,bevel=.004)

def lantern(M,name,pos,hang=.35,size=.32,energy=35):
    x,y,z=pos;b=B(M);i=b.i;s=size
    b.cylinder(x,y,z,z+hang,.012,seg=10,mi=i['black'])
    b.cbox(x,y,z-.025,s*1.2,s*1.2,.05,i['black'])
    b.cbox(x,y,z-s*1.38,s*.88,s*.88,.04,i['black'])
    for a in (-1,1):
        for c in (-1,1):b.tube((x+a*s/2,y+c*s/2,z),(x+a*s*.38,y+c*s*.38,z-s*1.35),.011,.011,mi=i['black'])
    b.cylinder(x,y,z-s*1.25,z-s*.4,.022,seg=12,mi=i['lamp'])
    b.blob((x,y,z-s*.38),.042,seg=12,rings=8,mi=i['lamp'])
    ob=b.done(name,bevel=.003)
    add_light('L_'+name,'POINT',(x,y,z-s*.65),energy,(1,.8,.55),size=.15)
    return ob

def artwork(M,name,pos,w,h,key='art_sea',rot=0):
    b=B(M);i=b.i
    b.box(-w/2,w/2,-.012,.012,-h/2,h/2,i[key])
    b.frame(-w/2-.025,w/2+.025,-.027,.016,-h/2-.025,h/2+.025,.025,i['brass'])
    out=B(M);out.merge(b,pos,rot);return out.done(name,bevel=.002)
