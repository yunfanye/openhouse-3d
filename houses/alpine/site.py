"""Oval swimming pool, brick terraces, parterre, gallery and guest house."""
import math
from .plan import *
from .details import B,box,window,lantern,column,path_tube
from .exterior import roof
from archviz import parts,plants
from archviz.lights import area_light,add_light

def oval(b,cx,cy,rx,ry,z0,z1,mi,n=160):
    pts=[(cx+rx*math.cos(j*2*math.pi/n),cy+ry*math.sin(j*2*math.pi/n)) for j in range(n)]
    b.prism(pts,z0,z1,mi)

def ring(b,cx,cy,rx,ry,width,z0,z1,mi,n=160):
    for j in range(n):
        a=j*2*math.pi/n;c=(j+1)*2*math.pi/n
        pts=[(cx+(rx+width)*math.cos(a),cy+(ry+width)*math.sin(a)),(cx+(rx+width)*math.cos(c),cy+(ry+width)*math.sin(c)),(cx+rx*math.cos(c),cy+ry*math.sin(c)),(cx+rx*math.cos(a),cy+ry*math.sin(a))]
        b.prism(pts,z0,z1,mi)

def outdoor_chair(b,x,y,rot=0,z=Z):
    i=b.i;l=B(b.M)
    parts.armchair(l,0,0,z=z,w=.75,d=.74,mi=i['linen'],mi_legs=i['black'],style='jeanneret')
    for side in (-1,1):
        l.tube((side*.35,-.28,z+.18),(side*.35,.30,z+.62),.014,.014,mi=i['black'])
        l.tube((side*.35,.30,z+.18),(side*.35,-.28,z+.62),.014,.014,mi=i['black'])
    b.merge(l,(x,y,0),rot)

def build(M):
    b=B(M);i=b.i
    b.plate(-180,180,-160,210,-.9,-.28,holes=[(-8.7,8.7,27.8,36.2)],mi=i['turf'])
    # Long narrow estate parcel with a true oval aperture in the lawn around the pool.
    b.box(-15,15,-16,23,-.20,-.03,i['turf'])
    b.box(-15,15,41,91,-.20,-.03,i['turf'])
    # Map ellipse perimeter to rectangular lawn edge to avoid a buried pool.
    n=160
    for j in range(n):
        a=j*2*math.pi/n;c=(j+1)*2*math.pi/n
        def outer(t):
            co,si=math.cos(t),math.sin(t);rr=min(15/max(abs(co),1e-8),9/max(abs(si),1e-8))
            return (rr*co,32+rr*si)
        b.prism([(8.63*math.cos(a),32+4.08*math.sin(a)),outer(a),outer(c),(8.63*math.cos(c),32+4.08*math.sin(c))],-.20,-.03,i['turf'])
    # Brick motor court framed by a curved green island.
    b.box(-14.5,14.5,-14.5,-2.6,-.04,.006,i['paver'])
    oval(b,0,-11.4,8.6,4.5,.01,.025,i['turf'])
    ring(b,0,-11.4,8.6,4.5,.12,.008,.038,i['paver'])
    # Side path links the entire parcel.
    b.box(-14,-12.7,-8,86,.006,.027,i['paver'])
    b.box(12.7,14,-8,86,.006,.027,i['paver'])
    b.done('Site | lawn and motor court')
    # Pool shell is a deep oval basin and the water is closed volume with absorption.
    b=B(M)
    oval(b,0,32,8.2,3.65,-1.8,-1.68,i['pool'])
    ring(b,0,32,8.2,3.65,.15,-1.78,.03,i['pool'])
    ring(b,0,32,8.35,3.8,.28,-.02,.115,i['paver'])
    b.done('Pool | tiled shell and brick coping',bevel=.005)
    b=B(M);oval(b,0,32,8.18,3.63,-1.65,-.06,i['water']);b.done('Pool | reflective water')
    b=B(M)
    # Steps descend inside the west end.
    for j in range(4):b.box(-8.02+j*.35,-7.6+j*.36,31.13,32.87,-1.67,-.22-j*.27,i['pool'])
    for yy in (31.25,32.55):
        path_tube(b,[(-8.55,yy,.13),(-8.40,yy,.67),(-8.16,yy,.93),(-7.85,yy,.94),(-7.55,yy,.65),(-7.5,yy,-.42)],.031,i['steel'],seg=12)
    b.done('Pool | entry steps and polished handrails',smooth=True)
    # Four white chaises on the main lawn.
    b=B(M)
    for x in (-4.2,-1.4,1.4,4.2):
        l=B(M);parts.lounger(l,0,0,.04,mi=i['linen'],rot=0)
        # detailed slatted aluminium base beneath the cushion
        for a in (-.31,.31):l.box(a-.025,a+.025,-.94,.98,.10,.23,i['trim'])
        for yy in (-.60,.60):
            for xx in (-.3,.3):l.box(xx-.022,xx+.022,yy-.035,yy+.035,.0,.22,i['trim'])
        parts.cushion(l,0,.43,.58,w=.49,d=.40,t=.12,mi=i['blue'],upright=True)
        b.merge(l,(x,25.2,0),math.pi)
    for x in (-2.8,2.8):parts.round_table(b,x,25.2,0,.29,h=.35,mi=i['black'],mi_leg=i['black'])
    # Veranda cross-frame furniture grouped between the columns.
    for cx in (-9,-4.5,4.5):
        outdoor_chair(b,cx-.85,19.1,rot=math.pi,z=Z);outdoor_chair(b,cx+.85,19.1,rot=math.pi,z=Z)
        parts.table(b,cx,19.35,Z,.65,.65,h=.45,mi_top=i['black'],mi_leg=i['black'],leg_w=.024)
        outdoor_chair(b,cx-.8,19.1,rot=math.pi,z=UP);outdoor_chair(b,cx+.8,19.1,rot=math.pi,z=UP)
        parts.round_table(b,cx,19.45,UP,.31,h=.48,mi=i['black'],legs='three')
    b.done('Garden | chaise lounges and veranda furniture',bevel=.004)
    # Formal rose garden, pale gravel paths and eight symmetric beds.
    b=B(M);b.box(-10.8,10.8,43,59,-.03,.015,i['gravel'])
    beds=[]
    for sx in (-1,1):
        for yy in (44.0,49.0,54.0):
            xa,xb=sorted((sx*1.15,sx*9.7));yb=yy+3.7
            # rounded corner planting islands bounded by low clipped box.
            b.rbox(xa,xb,yy,yb,.018,.08,r=.06,mi=i['soil']);beds.append((xa,xb,yy,yb))
    # Circular fountain at the crossing in the center path.
    b.lathe(0,51.0,.03,[(0,0),(.60,0),(.66,.12),(.62,.19),(.46,.23),(.32,.28),(.25,.78),(.33,.88),(.32,.93),(0,.93)],seg=64,mi=i['brass'])
    ring(b,0,51,1.1,1.1,.24,.015,.09,i['paver'],n=96)
    b.done('Rose garden | gravel parterre and fountain',bevel=.006)
    for xa,xb,ya,yb in beds:
        for aa,bb,cc,dd in ((xa,xb,ya,ya+.30),(xa,xb,yb-.30,yb),(xa,xa+.30,ya+.3,yb-.3),(xb-.30,xb,ya+.3,yb-.3)):
            plants.hedge(f'Parterre box {aa} {cc}',aa,bb,cc,dd,.04,.43,kind='boxwood',size=.10,cov=.8,seed=int(abs(aa*13+cc*5)))
    # Two delicate rose arches frame the axial walk; their aperture remains clear.
    b=B(M)
    for yy in (42.3,59.8):
        for offset in (-.28,.28):
            pts=[(-1.05,yy+offset,.07),(-1.05,yy+offset,2.05)]+[(1.05*math.cos(math.pi-j*math.pi/32),yy+offset,2.05+1.05*math.sin(j*math.pi/32)) for j in range(33)]+[(1.05,yy+offset,.07)]
            path_tube(b,pts,.027,i['trim'])
        for z in (.45,.95,1.45,1.95):
            for x in (-1.05,1.05):b.tube((x,yy-.3,z),(x,yy+.3,z),.018,.018,mi=i['trim'])
    b.done('Garden | white rose arbors',smooth=True)
    # Rear art gallery and detached two-story guest house.
    build_gallery(M)
    # Street wall, timber gates and lit brick piers.
    b=B(M)
    for x in (-14.3,-6.0,6.0,14.3):
        b.box(x-.28,x+.28,-15.3,-14.72,0,1.6,i['brick']);b.box(x-.34,x+.34,-15.36,-14.66,1.60,1.7,i['paver'])
        lantern(M,f'Entry gate light {x}',(x,-15.04,1.36),hang=0,size=.21,energy=15)
    for a,c in ((-14,-6.3),(6.3,14.0)):
        for j in range(round((c-a)/.20)+1):
            x=a+j*.20;b.box(x-.035,x+.035,-15.02,-14.92,.1,1.38,i['trim'])
        for z in (.2,1.32):b.box(a,c,-15.03,-14.91,z,z+.07,i['trim'])
    b.done('Front | gate and picket fence',bevel=.006)

def build_gallery(M):
    b=B(M);i=b.i
    b.box(-11.4,11.4,62.5,76,0,.04,i['paver'])
    b.box(-11,11,65,75,.04,.2,i['limestone'])
    holes=[(x-2.15,x+2.15,.2,3.8) for x in (-7,0,7)]
    b.wall('X',-11.4,11.4,65,65.28,.2,4.4,holes,i['brick'])
    b.box(-11.4,-11.12,65,76,.2,4.4,i['brick_y']);b.box(11.12,11.4,65,76,.2,4.4,i['brick_y']);b.box(-11.4,11.4,75.7,76,.2,4.4,i['brick'])
    b.box(-11.6,11.6,64.8,76.2,4.35,4.55,i['trim']);roof(b,-11.7,11.7,64.7,76.3,4.55,6.15)
    b.done('Gallery | detached brick pavilion',bevel=.006)
    for x in (-7,0,7):window(M,f'Gallery glass doors {x}',(x,64.96,.20),w=4.3,h=3.6,shutters=False,blinds=False)
    for x in (-10.7,-3.5,3.5,10.7):lantern(M,f'Gallery lantern {x}',(x,64.84,3.6),hang=.1,size=.24,energy=35)
    area_light('L_gallery',(0,69.5,4.3),(17,7),680,(1,.86,.64))
    b=B(M)
    b.box(-11.3,11.3,80,88.0,.1,6.9,i['brick'])
    b.box(-3.0,3.0,79.9,88.1,.1,3.0,i['white'])
    roof(b,-11.6,11.6,79.7,88.3,7.0,8.6)
    b.box(-11.4,11.4,79.7,80,6.72,7.03,i['trim']);b.done('Guest house | separate two-story volume',bevel=.006)
    for x in (-8,-4.5,4.5,8):
        for z in (.55,3.85):window(M,f'Guest house sash {x} {z}',(x,79.94,z),w=1.55,h=2.15,shutters=True,blinds=True)
