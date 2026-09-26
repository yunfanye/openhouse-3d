"""Grand stair hall and furnished principal rooms inferred from photos 03–17."""
import math,random
from .plan import *
from .details import B,box,portal,artwork,baluster,path_tube,rail,panel,lantern
from archviz import parts,plants
from archviz.lights import area_light,add_light,room_light


def rug(M,name,x,y,w,d,key='rug_pale',round=False,z=Z):
    b=B(M)
    if round:b.cylinder(x,y,z+.006,z+.018,w/2,seg=128,mi=b.i[key],ry=d/2)
    else:b.rbox(x-w/2,x+w/2,y-d/2,y+d/2,z+.006,z+.018,.01,b.i[key])
    return b.done(name)

def cornice(b,rect,z):
    x0,x1,y0,y1=rect;i=b.i['trim']
    for dz,d,h in ((0,.035,.08),(.08,.055,.035),(.115,.085,.065),(.18,.12,.05)):
        b.box(x0,x1,y0,y0+d,z-dz-h,z-dz,i);b.box(x0,x1,y1-d,y1,z-dz-h,z-dz,i)
        b.box(x0,x0+d,y0,y1,z-dz-h,z-dz,i);b.box(x1-d,x1,y0,y1,z-dz-h,z-dz,i)

def panel_run(b,a0,a1,pos,z,rot=0,h=1.0):
    bb=B(b.M);i=bb.i['trim']
    bb.box(a0,a1,-.048,.006,z,z+.16,i)
    bb.box(a0,a1,-.032,.006,z+.16,z+.19,i)
    bb.box(a0,a1,-.048,.006,z+h-.055,z+h,i)
    n=max(1,round((a1-a0)/1.05))
    for j in range(n):
        a=a0+(a1-a0)*j/n+.10;c=a0+(a1-a0)*(j+1)/n-.10
        if c>a:panel(bb,a,c,-.015,z+.27,z+h-.15)
    b.merge(bb,pos,rot)

def fireplace(M,name,pos,rot=0):
    b=B(M);i=b.i
    b.box(-1.2,1.2,-.16,.32,0,.10,i['marble'])
    b.box(-.66,.66,-.015,.11,.12,1.12,i['black'])
    for x in (-.86,.86):
        b.box(x-.16,x+.16,-.16,.23,.10,1.27,i['trim'])
        b.frame(x-.13,x+.13,-.175,-.153,.23,1.17,.027,i['trim'])
    b.box(-1.04,1.04,-.18,.28,1.17,1.36,i['trim'])
    b.box(-1.17,1.17,-.28,.3,1.36,1.44,i['trim'])
    for j in range(6):
        b.tube((-.5+j*.17,-.1,.20),(-.37+j*.14,.04,.28),.065,.055,seg=10,mi=i['walnut'])
    out=B(M);out.merge(b,pos,rot);out.done(name,bevel=.01)
    flames=B(M);rng=random.Random(32)
    for j in range(36):
        x=rng.uniform(-.52,.52);y=rng.uniform(-.09,.01);h=rng.uniform(.09,.28);r=rng.uniform(.015,.034)
        flames.cylinder(x,y,.25,.25+h*.55,r,r*.52,seg=9,mi=i['fire'])
        flames.tube((x,y,.25+h*.52),(x+rng.uniform(-.02,.02),y,.25+h),r*.52,.002,seg=9,mi=i['fire'])
    ff=B(M);ff.merge(flames,pos,rot);ff.done(name+' | flame tongues',smooth=True)
    add_light('L_'+name,'POINT',(pos[0]+.18*math.sin(rot),pos[1]-.18*math.cos(rot),pos[2]+.4),15,(1,.42,.12),size=.24)

def console(M,name,x,y,z=Z,rot=0):
    b=B(M);i=b.i
    parts.table(b,0,0,0,1.5,.43,h=.79,top_t=.05,mi_top=i['walnut'],mi_leg=i['black'],leg_w=.035)
    for xx in (-.65,.65):
        for yy in (-.13,.13):b.lathe(xx,yy,0,[(.025,.04),(.045,.10),(.024,.22),(.033,.5),(.026,.74)],seg=12,mi=i['black'])
    parts.vase(b,0,0,.79,h=.29,r=.14,mi=i['porcelain'])
    out=B(M);out.merge(b,(x,y,z),rot);out.done(name,bevel=.004)
    plants.stems(name+' flowers',(x,y,z+1.04),kind='eucalyptus',height=.58,seed=23,spread=.7)

def table_lamp(M,name,x,y,z):
    b=B(M);i=b.i;parts.lamp(b,x,y,z,mi_base=i['porcelain'],mi_shade=i['linen'],base_r=.14,base_h=.32,shade_r=.25,shade_h=.3)
    b.done(name,bevel=.003)
    add_light('L_'+name,'POINT',(x,y,z+.4),18,(1,.87,.68),size=.16)

def chandelier(M,x,y,z):
    b=B(M);i=b.i;b.cylinder(x,y,z-.85,z,.018,seg=12,mi=i['brass'])
    b.lathe(x,y,z-.9,[(.06,0),(.13,.10),(.07,.19)],seg=24,mi=i['brass'])
    for j in range(8):
        a=j*math.pi/4;cx=x+.77*math.cos(a);cy=y+.77*math.sin(a)
        pts=[(x+.10*math.cos(a),y+.10*math.sin(a),z-.8),(x+.40*math.cos(a),y+.40*math.sin(a),z-1.03),(cx,cy,z-.99),(cx,cy,z-.81)]
        path_tube(b,pts,.025,i['brass'])
        b.cylinder(cx,cy,z-.91,z-.72,.024,seg=12,mi=i['brass'])
        b.lathe(cx,cy,z-.74,[(.14,0),(.10,.22),(.098,.225),(.132,.005)],seg=24,mi=i['linen'])
        b.blob((cx,cy,z-.64),.032,seg=12,rings=6,mi=i['lamp'])
    b.done('Dining | eight shaded brass chandelier',bevel=.003)
    area_light('L_Dining chandelier',(x,y,z-.82),(1.2,1.2),170,(1,.86,.65))

def build(M):
    i={k:j for j,k in enumerate(M)}
    # Main partitions; wide cased openings follow the camera route.
    for x in (-3.4,3.4):
        holes=[(2.05,4.65,Z,3.4),(7.6,9.0,Z,3.25),(12.7,15.65,Z,3.35)]
        b=B(M);b.wall('Y',.2,17.8,x-.09,x+.09,Z,4.03,holes,i['white']);b.done(f'Partition {x}',bevel=.009)
        for a,c,_,h in holes:portal(M,f'Cased opening {x} {a}',(x,(a+c)/2,Z),c-a,h-Z,rot=math.pi/2)
        # Side upper gallery walls are continuous, with doors to the suites.
        b=B(M);b.wall('Y',.2,17.8,x-.09,x+.09,UP,7.85,[(3,4.3,UP,6.85),(10.2,11.5,UP,6.85)],i['white']);b.done(f'Upper suite partition {x}')
        for yy in (3.65,10.85):portal(M,f'Upper door casing {x} {yy}',(x,yy,UP),1.3,2.6,rot=math.pi/2)
    for xx,yy,holes in (((-11.8,-3.4),9.1,[(-8.7,-5.5,Z,3.35)]),((3.4,11.8),8.6,[(5.6,8.9,Z,3.35)]),((-3.4,3.4),12.,[(-3.1,-1.65,Z,3.25),(1.65,3.1,Z,3.25)])):
        b=B(M);b.wall('X',*xx,yy-.10,yy+.10,Z,4.03,holes,i['white']);b.done(f'Transverse partition {yy}',bevel=.006)
        for a,c,z,h in holes:portal(M,f'Transverse architrave {a} {yy}',((a+c)/2,yy,Z),c-a,h-Z,arch=yy==12.)
    # Floors, cornice mouldings, baseboards and recessed luminaire trims.
    b=B(M)
    for name,room in ROOMS.items():
        x0,x1,y0,y1,z0,z1=room
        if name!='hall':b.box(x0,x1,y0,y1,z0-.006,z0+.003,i['floor' if name!='bath' else 'marble'])
        cornice(b,(x0,x1,y0,y1),z1)
        for zz,h,w in ((z0,.14,.035),(z0+.14,.035,.047)):
            # bases divided at doorways so no trim floats across a portal
            for y in (y0,y1):
                b.box(x0,x1,y,y+.025,zz,zz+h,i['trim'])
            for x in (x0,x1):
                b.box(x,x+.025,y0,2.0 if y0<2 else y0,zz,zz+h,i['trim'])
        if name!='hall':
            for xx in (x0+.65,x1-.65):
                for yy in (y0+.7,(y0+y1)/2,y1-.7):
                    b.cylinder(xx,yy,z1-.014,z1-.003,.052,seg=20,mi=i['steel']);b.cylinder(xx,yy,z1-.018,z1-.016,.031,seg=16,mi=i['lamp'])
            room_light('L_room_'+name,room,energy=245 if z0==Z else 130,color=(1,.84,.65),shrink=.63)
    b.done('Interior | floors cornices and luminaires',bevel=.003)
    # Grand hall paneling and long galleries.
    b=B(M)
    for x in (-3.3,3.3):
        for a,c in ((.35,1.91),(4.77,7.5),(9.13,11.8)):
            panel_run(b,a,c,(x,0,0),Z,rot=math.pi/2,h=1.05)
    for x in (-2.45,2.45):rail(b,(x,1.1,UP),(x,10.55,UP),h=.95,wood=True,spacing=.19)
    rail(b,(-2.45,10.6,UP),(-1.25,10.6,UP),h=.95,wood=True)
    rail(b,(1.25,10.6,UP),(2.45,10.6,UP),h=.95,wood=True)
    # Stair flares out into a pair of scroll-ended walnut handrails.
    count=23;ystart=5.25;length=5.15
    for j in range(count):
        t=j/(count-1);w=1.16+.51*(1-t)**3;yy=ystart+j*length/count;zz=Z+(j+1)*(UP-Z)/count
        b.box(-w,w,yy,yy+length/count+.035,Z,zz-.018,i['trim'])
        b.rbox(-w-.045,w+.045,yy-.035,yy+length/count+.028,zz-.025,zz,.015,i['walnut'])
        b.box(-.93,.93,yy-.036,yy+length/count+.029,zz,zz+.016,i['runner'])
        b.box(-.93,.93,yy-.037,yy-.024,zz-(UP-Z)/count,zz+.012,i['runner'])
        for side in (-1,1):baluster(b,side*(w-.06),yy+.1,zz,.88)
    for side in (-1,1):
        pts=[]
        for j in range(65):
            t=j/64;w=1.16+.51*(1-t)**3
            pts.append((side*(w-.06),ystart+t*length+.06,Z+t*(UP-Z)+1.05))
        path_tube(b,pts,.047,i['walnut'],seg=12)
        pts=[]
        for j in range(50):
            a=j/49*math.pi*1.6;r=.22*(1-j/62)
            pts.append((side*(1.60+r*math.cos(a)),5.08+r*math.sin(a),Z+1.06))
        path_tube(b,pts,.042,i['walnut'],seg=10)
    b.done('Grand hall | flared staircase, paneling and balustrades',bevel=.004)
    rug(M,'Hall | circular antique rug',0,2.8,2.7,2.7,'rug',True)
    artwork(M,'Hall | tidal landscape',(-3.275,6.10,2.50),2.40,1.55,'art_sea',-math.pi/2)
    artwork(M,'Hall | mineral canvas',(3.275,6.10,2.50),2.40,1.55,'art_gold',math.pi/2)
    for x in (-2.65,2.65):console(M,f'Hall console {x}',x,.70)
    for x in (-1.1,1.1):artwork(M,f'Upper landing canvas {x}',(x,11.84,6.45),.84,1.15,'art_gold')
    room_light('L_hall bounce',ROOMS['hall'],energy=90,color=(1,.91,.77))
    # Formal living room: a pair of pale sofas, slender brass/glass table, fireplace and artwork.
    rug(M,'Living | antique carpet',-8.25,4.8,5.15,6.2,'rug')
    b=B(M)
    parts.sofa(b,-10.30,4.8,3.1,1.02,rot=math.pi/2,z=Z,mi_seat=i['linen'],mi_pillow=i['blue'],mi_base=i['linen'],pillows=4,cushion_gap=.035,back_h=.91)
    parts.sofa(b,-6.20,4.8,3.1,1.02,rot=-math.pi/2,z=Z,mi_seat=i['linen'],mi_pillow=i['blue'],pillows=4,cushion_gap=.035,back_h=.91)
    parts.table(b,-8.25,4.85,Z,1.4,2.6,h=.43,top_t=.026,mi_top=i['glass'],mi_leg=i['brass'],leg_w=.028)
    b.frame(-8.95,-7.55,3.55,6.15,Z+.42,Z+.455,.025,i['brass'],axis='Z')
    parts.books(b,-8.3,4.6,Z+.46,n=3,mi=i['blue'])
    parts.vase(b,-8.15,5.25,Z+.46,h=.28,r=.13,mi=i['porcelain'])
    for x in (-10.3,-6.2):
        parts.armchair(b,x,7.52,rot=.15 if x<-8 else -.15,z=Z,w=.84,d=.83,mi=i['linen'],mi_legs=i['walnut'],style='club')
        parts.round_table(b,x,2.50,Z,.4,h=.60,mi=i['walnut'],mi_leg=i['brass'],legs='three')
    b.done('Living | linen seating and brass table',bevel=.003)
    plants.stems('Living | white flowers',(-8.15,5.25,Z+.72),kind='eucalyptus',height=.65,seed=16)
    for x in (-10.3,-6.2):table_lamp(M,f'Living table lamp {x}',x,2.5,Z+.6)
    fireplace(M,'Living | limestone fireplace',(-10.25,8.94,Z))
    artwork(M,'Living | overmantel abstract',(-10.25,8.94,Z+2.15),1.5,1.06,'art_gold')
    # Formal dining, seen through the hall and kitchen openings.
    rug(M,'Dining | silk patterned rug',8,4.9,5.5,5.8)
    b=B(M);parts.table(b,8,4.7,Z,2.0,3.1,h=.79,top_t=.09,mi_top=i['walnut'],mi_leg=i['walnut'],legs='drum')
    for side in (-1,1):
        for yy in (3.65,4.7,5.75):parts.dining_chair(b,8+side*1.27,yy,rot=side*-math.pi/2,z=Z,mi_wood=i['walnut'],mi_seat=i['linen'],w=.61,d=.65)
    for yy,rot in ((2.86,math.pi),(6.54,0)):parts.dining_chair(b,8,yy,rot=rot,z=Z,mi_wood=i['walnut'],mi_seat=i['linen'],w=.65,d=.65)
    parts.vase(b,8,4.7,Z+.80,h=.23,r=.20,mi=i['porcelain']);b.done('Dining | walnut dining ensemble',bevel=.006)
    chandelier(M,8,4.7,3.95)
    plants.stems('Dining | branches',(8,4.7,1.49),kind='eucalyptus',height=.64,seed=82)
    fireplace(M,'Dining | fireplace',(11.68,4.8,Z),-math.pi/2)
    artwork(M,'Dining | landscape',(11.66,4.8,2.70),1.6,1.0,'art_sea',-math.pi/2)
    # Library: oak cabinets, colorful art, blush sofas and reading table.
    rug(M,'Library | quiet wool carpet',-8.05,13.25,5.6,6.5)
    b=B(M)
    for yy in (10.2,12.0,13.8,15.6,17.1):
        # Cases face the central library; model in local XZ then rotate to wall.
        sh=B(M);parts.shelves(sh,-.79,.79,-.42,0,1.25,3.65,n=4,t=.045,mi=i['oak']);sh.box(-.82,.82,-.47,0,Z,1.23,i['oak'])
        for xx in (-.39,.39):panel(sh,xx-.32,xx+.32,-.48,.63,1.1,'oak')
        rng=random.Random(int(yy*10))
        for z in (1.28,1.88,2.48,3.08):
            for j in range(8):
                x=-.65+j*.13;h=rng.uniform(.20,.39)
                sh.box(x,x+.065,-.3,-.04,z,z+h,i[('linen','blue','walnut','sage')[rng.randrange(4)]])
            parts.vase(sh,.52,-.2,z,h=.26,r=.1,mi=i['porcelain'])
        b.merge(sh,(-11.64,yy,0),math.pi/2)
    parts.sofa(b,-9.3,13.25,2.6,.92,rot=math.pi/2,z=Z,mi_seat=i['blush'],mi_pillow=i['linen'],pillows=3,cushion_gap=.025,back_h=.88)
    parts.sofa(b,-5.63,13.25,2.6,.92,rot=-math.pi/2,z=Z,mi_seat=i['blush'],mi_pillow=i['linen'],pillows=3,cushion_gap=.025,back_h=.88)
    parts.table(b,-7.45,13.25,Z,1.15,2.0,h=.4,top_t=.08,mi_top=i['oak'],mi_leg=i['oak'],legs='pedestal')
    parts.books(b,-7.5,13.35,.87,n=3,mi=i['sage']);parts.vase(b,-7.35,12.95,.87,h=.30,r=.11,mi=i['porcelain'])
    b.done('Library | oak built-ins and blush upholstery',bevel=.005)
    artwork(M,'Library | large abstract',(-3.53,10.62,2.58),2.1,1.3,'art_rose',math.pi/2)
    # Garden salon at center rear.
    rug(M,'Salon | wool area rug',0,15.1,6.5,4.0)
    b=B(M)
    parts.sofa(b,-2.5,15.35,2.6,.90,rot=math.pi/2,z=Z,mi_seat=i['linen'],mi_pillow=i['sage'],pillows=3,cushion_gap=.03,back_h=.88)
    parts.sofa(b,2.5,15.35,2.6,.90,rot=-math.pi/2,z=Z,mi_seat=i['linen'],mi_pillow=i['sage'],pillows=3,cushion_gap=.03,back_h=.88)
    parts.round_table(b,0,15.3,Z,.73,h=.43,mi=i['walnut'],mi_leg=i['walnut'])
    parts.vase(b,0,15.3,.89,h=.24,r=.12,mi=i['porcelain']);b.done('Salon | garden-facing seating',bevel=.004)
    fireplace(M,'Salon | fireplace',(0,12.18,Z),math.pi)
    artwork(M,'Salon | overmantel',(0,12.20,2.68),1.5,1.05,'art_rose',math.pi)
    plants.potted('Salon | olive',(-3.1,17.0,Z),kind='olive',height=1.95,pot='ceramic',seed=13)
    build_kitchen(M)
    build_upper(M)

def cabinet(b,x0,x1,z0,z1,depth=.66,upper=False):
    i=b.i;w=x1-x0
    if not upper:b.box(x0,x1,0,depth,z0,z1,i['trim'])
    else:
        b.box(x0,x0+.035,0,depth,z0,z1,i['trim']);b.box(x1-.035,x1,0,depth,z0,z1,i['trim'])
        b.box(x0,x1,depth-.025,depth,z0,z1,i['oak']);b.box(x0,x1,0,depth,z0,z0+.035,i['trim']);b.box(x0,x1,0,depth,z1-.035,z1,i['trim'])
    n=max(1,round(w/.60))
    for j in range(n):
        a=x0+j*w/n+.018;c=x0+(j+1)*w/n-.018
        b.frame(a,c,-.036,-.009,z0+.035,z1-.025,.062,i['trim'])
        if upper:
            b.box(a+.067,c-.067,-.014,-.002,z0+.103,z1-.092,i['glass'])
            b.box(a+.05,c-.05,.47,.5,z0+.06,z1-.04,i['oak'])
            for zz in (z0+.37,z0+.79,z0+1.21):
                if zz>z1-.1:continue
                b.box(a+.055,c-.055,.015,.50,zz,zz+.024,i['oak'])
                for k in range(3):b.cylinder((a+c)/2,.24,zz+.026+k*.018,zz+.035+k*.018,.14,seg=20,mi=i['porcelain'])
        else:
            b.box(a+.064,c-.064,-.025,-.011,z0+.12,z1-.15,i['trim'])
            b.box(a,c,-.052,-.026,z1-.18,z1-.16,i['trim'])
        b.blob((c-.075,-.069,z0+.17 if upper else z1-.10),.022,seg=12,rings=6,mi=i['black'])

def build_kitchen(M):
    b=B(M);i=b.i
    # Long cabinet/range wall on east side, facing west.
    local=B(M)
    for a,c in ((9.0,10.2),(12.1,13.0),(13.0,17.3)):
        cabinet(local,a,c,Z+.09,Z+.88)
        local.box(a-.03,c+.03,-.055,.70,Z+.88,Z+.93,i['counter'])
    for a,c in ((9.0,10.2),(12.15,13.55),(15.0,17.3)):cabinet(local,a,c,2.20,3.70,depth=.40,upper=True)
    # Five-burner stainless range and broad brushed-metal hood.
    local.box(10.25,12.06,0,.74,Z+.11,Z+.91,i['steel'])
    local.box(10.32,11.22,-.022,-.01,Z+.19,Z+.63,i['black']);local.box(11.30,11.98,-.022,-.01,Z+.19,Z+.63,i['black'])
    for a,c in ((10.35,11.18),(11.33,11.95)):local.tube((a,-.09,Z+.68),(c,-.09,Z+.68),.023,.023,mi=i['steel'])
    for k in range(7):local.blob((10.38+k*.245,-.06,Z+.79),.033,seg=14,rings=8,mi=i['black'])
    for xx in (10.60,11.20,11.78):
        for yy in (.18,.54):
            local.cylinder(xx,yy,Z+.94,Z+.956,.108,seg=24,mi=i['black'])
            for off in (-.15,0,.15):local.box(xx-.17,xx+.17,yy+off-.009,yy+off+.009,Z+.96,Z+.975,i['black'])
    local.box(10.2,12.12,-.11,.66,2.08,2.18,i['steel'])
    local.hexa([(10.2,-.11,2.18),(12.12,-.11,2.18),(12.12,.66,2.18),(10.2,.66,2.18),(10.5,.15,3.2),(11.82,.15,3.2),(11.82,.66,3.2),(10.5,.66,3.2)],i['steel'])
    local.box(10.48,11.85,.12,.64,3.2,3.7,i['steel'])
    local.v=[(a,-c,z) for a,c,z in local.v]
    b.merge(local,(11.0,0,0),math.pi/2)
    # Rear cabinets beside the open French doors.
    local=B(M);cabinet(local,4.48,7.67,Z+.1,Z+.88);local.box(4.44,7.72,-.055,.70,Z+.88,Z+.94,i['counter'])
    cabinet(local,5.65,7.67,2.22,3.72,depth=.40,upper=True)
    b.merge(local,(0,17.0,0))
    # Island, paneled on both long sides, authentic warm stone worktop.
    b.plate(6.3,8.05,11.0,14.3,Z+.06,Z+.92,holes=[(6.69,7.65,12.95,13.55)],mi=i['trim'])
    b.plate(6.22,8.13,10.92,14.38,Z+.92,Z+.98,holes=[(6.69,7.65,12.95,13.55)],mi=i['counter'])
    for x,rot in ((6.28,math.pi/2),(8.07,math.pi/2)):
        l=B(M)
        for j in range(4):panel(l,11.03+j*.81,11.03+(j+1)*.81-.045,0,Z+.2,Z+.80)
        b.merge(l,(x,0,0),rot)
    # Undermounted sink represented with a recessed dark bowl and thin rim.
    b.frame(6.66,7.68,12.92,13.58,Z+.978,Z+.99,.035,i['steel'],axis='Z')
    b.box(6.70,7.64,12.96,13.54,Z+.72,Z+.74,i['porcelain'])
    b.frame(6.69,7.65,12.95,13.55,Z+.735,Z+.98,.027,i['porcelain'],axis='Z')
    parts.faucet(b,7.16,13.64,Z+.985,h=.29,mi=i['steel'],reach=.19,dir=(0,-1))
    parts.vase(b,7.1,11.65,Z+.99,h=.3,r=.20,mi=i['porcelain'],style='bowl')
    for j in range(5):b.blob((7.0+(j%3)*.10,11.65+(j//3)*.12,Z+1.23),.073,seg=18,rings=10,mi=i['counter'])
    parts.vase(b,5.6,17.3,Z+.95,h=.5,r=.11,mi=i['blue'])
    b.done('Kitchen | inset cabinets, glass cupboards, range and stone island',bevel=.006)
    plants.stems('Kitchen | cut branches',(5.6,17.3,Z+1.42),kind='magnolia',height=.75,seed=22)
    area_light('L_kitchen range',(11.1,11.2,2.12),(1.5,.45),42,(1,.85,.65))
    # Countertop still life, towels and decanters.
    b=B(M)
    parts.books(b,11.28,16.1,Z+.95,n=2,mi=i['walnut'],rot=math.pi/2)
    for yy in (14.4,14.65):parts.vase(b,11.22,yy,Z+.95,h=.22,r=.075,mi=i['porcelain'])
    b.drape(6.3,6.73,11.0,11.9,Z+.987,t=.012,mi=i['linen'],sag=.006)
    b.done('Kitchen | styled accessories',smooth=True)

def build_upper(M):
    i={k:j for j,k in enumerate(M)}
    for name,xy,w,l in (('Primary',(-8.0,13.2),2.12,2.25),('Guest bedroom',(-8.1,4.8),1.95,2.1),('East bedroom',(8.1,4.5),1.95,2.1)):
        x,y=xy;rug(M,name+' carpet',x,y-1,5.5,5,'rug_pale',z=UP)
        b=B(M);parts.bed(b,x,y,z=UP,w=w,l=l,mi_frame=i['blue'],mi_linen=i['linen'],mi_pillow=i['linen'],mi_throw=i['sage'],head_h=1.45,channels=7,seed=13)
        for xx in (x-w/2-.5,x+w/2+.5):parts.nightstand(b,xx,y+.80,z=UP,w=.73,d=.55,h=.65,mi=i['walnut'])
        parts.armchair(b,x+1.8,y-2.4,z=UP,rot=-.4,mi=i['linen'],mi_legs=i['walnut'],style='club')
        b.done(name+' furniture',bevel=.005)
        for xx in (x-w/2-.5,x+w/2+.5):table_lamp(M,name+f' lamp {xx}',xx,y+.8,UP+.65)
    b=B(M);b.box(3.4,11.8,10.3,10.5,UP,7.85,i['white'])
    b.box(4.5,8.0,16.93,17.65,UP+.08,UP+.88,i['trim']);b.box(4.46,8.04,16.90,17.68,UP+.88,UP+.94,i['marble'])
    for x in (5.25,7.2):
        parts.basin(b,x,17.2,UP+.94,r=.25,mi=i['porcelain']);parts.faucet(b,x,17.5,UP+.95,mi=i['steel'])
        b.frame(x-.68,x+.68,17.69,17.75,UP+1.2,UP+2.7,.048,i['brass']);b.box(x-.63,x+.63,17.7,17.72,UP+1.25,UP+2.65,i['mirror'])
    parts.bathtub(b,10.6,14.25,UP,l=2.1,w=.92,h=.6,mi=i['porcelain'])
    b.done('Upper | marble bath',bevel=.004)
