"""Brick Georgian envelope, two colonnades, window joinery and hipped slate roof."""
import math
from .plan import *
from .details import B,box,column,rail,window,portal,lantern
from archviz.lights import area_light

def roof(b,x0,x1,y0,y1,eave,ridge):
    y=(y0+y1)/2;hx=min((y1-y0)*.15,2.6);i=b.i['slate']
    # Hipped roof with a long ridge, matching the broad shallow-pitched listing roof.
    vs=[(x0,y0,eave),(x1,y0,eave),(x1,y1,eave),(x0,y1,eave),(x0+hx,y,ridge),(x1-hx,y,ridge)]
    b._add(vs,[(0,1,5,4),(1,2,5),(2,3,4,5),(3,0,4)],i)


def build(M):
    b=B(M);i=b.i
    b.box(-12,12,0,18,.15,Z,i['limestone'])
    b.plate(-12,12,0,18,4.03,UP,holes=[(-2.45,2.45,1.0,10.6)],mi=i['trim'])
    b.plate(-12,12,0,18,7.85,8.05,holes=[(-2.8,2.8,2.2,10)],mi=i['ceiling'])
    # Four rooflights are visible in the stair hall; roof above has translucent monitors.
    for xx in (-1.48,1.48):
        for yy in (4.25,7.95):
            b.box(xx-1.2,xx+1.2,yy-1.4,yy+1.4,7.98,8.02,i['skylight'])
            b.frame(xx-1.24,xx+1.24,yy-1.44,yy+1.44,7.87,8.05,.12,i['trim'],axis='Z')
            for n in (-2,-1,0,1,2):b.box(xx-1.2,xx+1.2,yy+n*.47-.014,yy+n*.47+.014,7.955,7.99,i['trim'])
            for n in (-1,0,1):b.box(xx+n*.6-.017,xx+n*.6+.017,yy-1.4,yy+1.4,7.955,7.99,i['trim'])
            area_light(f'L_rooflight_{xx}_{yy}',(xx,yy,7.83),(2.3,2.7),135,(.89,.94,1))
    b.done('House | floors and rooflight ceiling')
    for y,sg,rot in ((0,1,0),(18,-1,math.pi)):
        for z0,z1 in ((Z,4.03),(UP,8.05)):
            upper=z0==UP;bottom=z0+.25;top=z0+2.98
            holes=[]
            for x in BAYS:
                w=2.02 if y==18 else 1.85
                if y==0 and x==0 and not upper:
                    holes.append((-1.32,1.32,Z,3.86))
                else:holes.append((x-w/2,x+w/2,Z if y==18 and not upper and x in (0,9) else bottom,top))
            b=B(M);b.wall('X',-12,12,y-.15,y+.15,z0,z1,holes,i['brick']);b.done(f'Brick facade {y} {z0}',bevel=.012)
            b=B(M);b.wall('X',-11.75,11.75,y+sg*.16,y+sg*.185,z0,z1,holes,i['white']);b.done(f'Facade inner plaster {y} {z0}')
            for x in BAYS:
                if y==0 and x==0 and not upper:continue
                opening=y==18 and not upper and x in (0,9)
                zz=Z if opening else bottom
                window(M,f'French window {x} {y} {z0}',(x,y-sg*.19,zz),w=2.02 if y==18 else 1.85,h=top-zz,rot=rot,shutters=True,opening=opening,blinds=not opening)
    # Thresholds for open rear doors (wall bottom removed explicitly).
    # Side elevations with tall sash windows.
    for x,sg,rot in ((-12,1,-math.pi/2),(12,-1,math.pi/2)):
        for z0,z1 in ((Z,4.03),(UP,8.05)):
            ys=(3.0,6.6,15.0) if x>0 and z0==Z else (3.0,6.6,11.0,15.0)
            holes=[(y-.8,y+.8,z0+.65,z0+2.95) for y in ys]
            b=B(M);b.wall('Y',0,18,x-.15,x+.15,z0,z1,holes,i['brick_y']);b.done(f'Side brick {x} {z0}',bevel=.008)
            b=B(M);b.wall('Y',.2,17.8,x+sg*.16,x+sg*.18,z0,z1,holes,i['white']);b.done(f'Side interior {x} {z0}')
            for y in ys:window(M,f'Side sash {x} {y} {z0}',(x-sg*.19,y,z0+.65),w=1.6,h=2.3,rot=rot,shutters=False)
    # Colonnaded front portico and double-level rear veranda.
    b=B(M)
    for ya,yb,cy,rear in ((-2.6,-.02,-2.22,False),(18.02,20.6,20.2,True)):
        b.box(-12.5,12.5,ya,yb,Z-.18,Z-.008,i['paver'])
        for step in range(3):
            ys=ya-(3-step)*.27 if not rear else yb+step*.27
            b.box(-12.5,12.5,ys,ys+.28,(step if not rear else 2-step)*.15,(step+1 if not rear else 3-step)*.15,i['paver'])
        for x in COLS:column(b,x,cy,Z,7.40,.245)
        b.box(-12.65,12.65,ya-.16,yb+.12,7.86,8.13,i['trim'])
        b.box(-12.58,12.58,ya-.10,yb+.09,7.78,7.88,i['trim'])
        b.box(-12.53,12.53,ya-.07,yb+.06,7.69,7.8,i['trim'])
        # closely spaced beadboard seams in the portico ceiling
        for j in range(151):
            x=-12.5+j/6;b.box(x,x+.008,ya,yb,7.682,7.688,i['shutter'])
        if rear:
            b.box(-12.25,12.25,18.08,20.38,4.05,UP-.018,i['paver'])
            b.box(-12.4,12.4,20.29,20.48,3.88,4.14,i['trim'])
            for a,c in zip(COLS[:-1],COLS[1:]):rail(b,(a+.22,20.22,UP),(c-.22,20.22,UP),h=.97)
            for x in (-12.1,12.1):rail(b,(x,18.1,UP),(x,20.2,UP),h=.97)
    b.done('Colonnades | turned columns, balcony and cornices',bevel=.007)
    for y in (-1.2,19.2):
        for x in BAYS:
            lantern(M,f'Veranda lantern {x} {y}',(x,y,3.59 if y>0 else 6.80),hang=.36,size=.3,energy=45 if y>0 else 80)
            if y>0:lantern(M,f'Upper lantern {x}',(x,y,7.45),hang=.22,size=.27,energy=38)
    # Entry with sidelights and elliptical fanlight above a six-panel door.
    b=B(M)
    b.frame(-1.4,1.4,-.19,.17,Z,3.42,.12,i['trim'])
    for side in (-1,1):
        b.frame(side*.97-.21,side*.97+.21,-.16,.09,Z+.06,3.29,.06,i['trim'])
        b.box(side*.97-.14,side*.97+.14,-.015,.005,Z+.12,3.22,i['glass'])
        for j in range(16):b.box(side*.97-.14,side*.97+.14,.075,.13,Z+.13+j*.165,Z+.17+j*.165,i['trim'])
    for j in range(48):
        a=j*math.pi/48;c=(j+1)*math.pi/48
        b.quad((0,-.035,3.35),(1.30*math.cos(a),-.035,3.35+.5*math.sin(a)),(1.30*math.cos(c),-.035,3.35+.5*math.sin(c)),(0,-.035,3.35),i['glass'])
        b.tube((1.35*math.cos(a),-.11,3.35+.55*math.sin(a)),(1.35*math.cos(c),-.11,3.35+.55*math.sin(c)),.055,.055,seg=8,mi=i['trim'])
    for a in (.35,.70,1.05,1.4,1.75,2.1,2.45,2.8):b.tube((0,-.06,3.35),(1.28*math.cos(a),-.06,3.35+.49*math.sin(a)),.017,.017,mi=i['trim'])
    b.done('Entry | sidelights and fanlight',bevel=.003)
    b=B(M);b.box(-.72,.72,-.07,.045,Z,3.34,i['trim'])
    for x in (-.355,.355):
        for z,h in ((.9,.52),(1.83,.82),(2.84,.57)):
            b.frame(x-.27,x+.27,-.091,-.07,z-h/2,z+h/2,.035,i['trim'])
            b.box(x-.225,x+.225,-.083,-.075,z-h/2+.04,z+h/2-.04,i['trim'])
    b.cylinder(.56,-.12,1.48,1.56,.037,seg=16,mi=i['brass'])
    b.done('Entry_Door',bevel=.006)
    # Slate hipped roof, dormers, stepped chimneys and central monitor.
    b=B(M);roof(b,-12.7,12.7,-2.75,20.75,8.14,RIDGE);b.done('House | hipped slate roof')
    for y,rot in ((-1.55,0),(19.55,math.pi)):
        for x in BAYS:
            b=B(M)
            b.box(-.70,.70,0,1.45,8.43,9.55,i['trim'])
            b._add([(-.76,-.02,9.55),(.76,-.02,9.55),(0,-.02,9.96),(-.76,1.47,9.55),(.76,1.47,9.55),(0,1.47,9.96)],[(0,1,2),(3,5,4),(0,3,4,1),(0,2,5,3),(1,4,5,2)],i['trim'])
            b.quad((-.84,-.12,9.58),(0,-.12,10.02),(0,1.53,10.02),(-.84,1.53,9.58),i['slate'])
            b.quad((0,-.12,10.02),(.84,-.12,9.58),(.84,1.53,9.58),(0,1.53,10.02),i['slate'])
            b.frame(-.47,.47,-.07,-.025,8.56,9.48,.06,i['trim'])
            b.box(-.40,.40,-.028,-.02,8.63,9.42,i['glass'])
            for j in range(10):b.box(-.40,.4,-.08,-.05,8.65+j*.07,8.677+j*.07,i['trim'])
            out=B(M);out.merge(b,(x,y,0),rot);out.done(f'Dormer {x} {y}',bevel=.006)
    b=B(M)
    for x,y in ((-11.9,4.1),(11.9,10.8)):
        b.box(x-.48,x+.48,y-.7,y+.7,6.6,10.65,i['brick'])
        b.box(x-.53,x+.53,y-.75,y+.75,10.2,10.36,i['brick'])
        b.box(x-.54,x+.54,y-.76,y+.76,10.61,10.75,i['brick'])
        b.box(x-.30,x+.30,y-.50,y+.50,10.73,10.78,i['black'])
    b.box(-2.8,2.8,7.1,10.7,10.29,10.68,i['trim'])
    b.box(-2.65,2.65,7.2,10.6,10.68,10.73,i['skylight'])
    for j in range(9):b.box(-2.7+j*.675,-2.675+j*.675,7.15,10.65,10.72,10.77,i['trim'])
    b.done('Chimneys and rooflight monitor',bevel=.008)
