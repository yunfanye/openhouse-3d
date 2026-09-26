"""Permanent features restored from listing photos 01, 19, 23–26.

Decorative glass motifs are modeled interpretations of the photographed glass;
window, vanity and light positions follow the shared architectural plan.
"""
import math
from archviz.mesh import MB
from archviz.parts import vase, books, faucet, twin_sconce
from archviz.lights import add_light
from archviz import materials as mat
from .plan import *


def living_board(M):
    # Shallow recessed blackboard and open shelves on the REAR wall, photo 01.
    mb=MB();x0,x1,y0,y1=ROOMS['alcove'][:4]
    mb.box(x0,x1,y0,y1,2.39,2.49,0)
    for xx in (x0,x1-.09):mb.box(xx,xx+.09,y0,y1,.12,2.4,0)
    sx0,sx1=x0+.09,x0+.47
    mb.box(sx0,sx1,y1-.025,y1,.13,2.4,0)
    for zz in (.13,.52,.92,1.32,1.72,2.12,2.37):
        mb.box(sx0,sx1,y0+.045,y1,zz,zz+.023,0)
    mb.box(sx1-.018,sx1+.018,y0+.035,y1,.13,2.4,0)
    mb.box(sx1+.045,x1-.13,y1-.024,y1-.016,.32,2.32,1)
    mb.frame(sx1+.01,x1-.095,y1-.05,y1-.013,.285,2.355,.035,mi=0,axis='Y')
    mb.box(sx1+.01,x1-.095,y1-.10,y1-.015,.27,.285,0)
    mb.build('Front_OriginalBlackboard',[M['trim'],M['chalk']],coll='House',bevel=.0015)
    st=MB()
    for k in range(5):
        zz=.55+k*.40
        if k%2: vase(st,(sx0+sx1)/2,y1-.16,zz,h=.21,r=.065,mi=0,style='round')
        else: books(st,(sx0+sx1)/2,y1-.15,zz,n=3,mi=1,w=.23,d=.17)
    st.build('Front_BlackboardShelfStaging',[M['ceramic'],M['book']],coll='House')


def powder(M):
    from .interior_back import _toilet,_shaker_door,_local
    from .interior_upper import _ring_slab,_oval_sink,_widespread
    L=_local(M);x0,x1,y0,y1=ROOMS['half'][:4]
    mb=MB();mb.box(x0,x1,y0,y1,.015,.030,0)
    mb.build('Back_PowderFloor',[M['tile_bath_floor']],coll='House')
    # Both fixtures against the rear wall, vanity next to the stained-glass side window.
    sx,sy=x0+.32,y1-.26;zf=.03;top=.83
    mb=MB()
    mb.box(sx-.28,sx+.28,y1-.51,y1-.025,zf+.09,zf+.11,0)
    for xx in (sx-.28,sx+.26):mb.box(xx,xx+.02,y1-.51,y1-.025,zf+.09,top-.025,0)
    mb.box(sx-.28,sx+.28,y1-.045,y1-.025,zf+.09,top-.025,0)
    for aa,bb in ((sx-.27,sx-.005),(sx+.005,sx+.27)):
        _shaker_door(mb,'X',aa,bb,y1-.51,-1,zf+.12,.64,0,2,stile=.035)
    _shaker_door(mb,'X',sx-.27,sx+.27,y1-.51,-1,.65,.79,0,None,stile=.03)
    _ring_slab(mb,sx,sy,.20,.155,sx-.295,sx+.295,y1-.535,y1-.01,top-.02,top,1)
    _oval_sink(mb,sx,sy,top,.205,.16,1)
    mb.box(sx-.295,sx+.295,y1-.04,y1-.01,top,top+.10,1)
    _widespread(mb,sx,y1-.10,top+.02,2,dir=(0,-1))
    _toilet(mb,x1-.32,y1-.25,1,tank=(0,1))
    # shallow mirrored medicine cabinet, chrome edges, vertical light to its left
    mb.box(sx-.24,sx+.24,y1-.09,y1-.005,1.28,2.02,0)
    mb.box(sx-.237,sx+.237,y1-.098,y1-.092,1.285,2.015,3)
    mb.frame(sx-.245,sx+.245,y1-.10,y1-.08,1.275,2.025,.012,mi=2,axis='Y')
    lx=sx+.36
    mb.tube((lx,y1-.01,1.67),(lx,y1-.045,1.67),.065,.065,seg=24,mi=2)
    mb.rbox(lx-.018,lx+.018,y1-.083,y1-.047,1.48,1.90,r=.006,mi=4)
    mb.v=[(x,y0+y1-y,z) for x,y,z in mb.v]
    mb.f=[tuple(reversed(f)) for f in mb.f]
    mb.build('Back_PowderOriginalFixtures',[M['cabinet'],M['porcelain'],M['chrome'],M['mirror'],M['emit_warm']],coll='House',bevel=.0015)
    add_light('L_Back_PowderBar','POINT',(lx,y0+.12,1.7),18,(1,.92,.81),size=.1)
    add_light('L_Back_PowderCeiling','POINT',((x0+x1)/2,(y0+y1)/2,2.5),20,(1,.95,.90),size=.18)
    # whitewashed horizontal boards and exposed painted beam seen in photo 25
    wm=mat.wood('PowderWhitewashedBoards',light=(.68,.64,.56,1),dark=(.48,.46,.40,1),grain_axis='Y',rough=.72,coat=.02)
    mb=MB()
    for k in range(19):mb.box(x1-.016,x1,y0,y1,.03+k*.14,.03+(k+1)*.14-.002,0)
    mb.box(x0,x1,y0+.34,y0+.45,2.59,2.72,0)
    mb.build('Back_PowderWoodwork',[wm],coll='House')
    stained_glass(M)


def stained_glass(M):
    """Leaded floral medallions, colored glass and white sash (photo 25)."""
    o=BY_NAME['PowderW'];cy=(o['a0']+o['a1'])/2;x=-5.555
    colors=[(.06,.25,.50,1),(.08,.46,.39,1),(.55,.19,.08,1),(.68,.55,.24,1),(.72,.77,.68,1)]
    mats=[mat.new_mat('PowderGlass'+str(i),c,rough=.18,coat=.7) for i,c in enumerate(colors)]+[M['steel'],M['trim']]
    mb=MB()
    for center,rad in ((1.43,.21),(1.91,.15)):
        for ring in range(2):
            for k in range(12):
                ang=math.tau*k/12+ring*math.pi/12
                pts=[]
                for j in range(25):
                    a=math.tau*j/24
                    rr=(.48+.44*math.cos(a))*rad if ring==0 else (.71+.19*math.cos(a))*rad
                    th=ang+.17*math.sin(a)
                    pts.append((x,cy+rr*math.sin(th),center+rr*math.cos(th)))
                mb._add(pts[:-1],[tuple(range(len(pts)-1))],(k+ring*2)%5)
                mb.path_tube(pts,.0028,seg=6,mi=5)
        mb.tube((x-.002,cy,center),(x+.004,cy,center),.024,.024,seg=20,mi=3)
    mb.box(x-.004,x+.022,o['a0']+.04,o['a1']-.04,1.68,1.72,6)
    mb.build('Back_PowderFloralGlass',mats,coll='House',smooth=True)


def glazed_upper(mb,ya,yb,xback,z0,z1):
    """Hollow white cabinet, divided glass doors, interior shelves; no solid door behind the glass."""
    xf=xback-.32;t=.018
    mb.box(xback-.02,xback,ya,yb,z0,z1,0)
    mb.box(xf,xback,ya,ya+t,z0,z1,0);mb.box(xf,xback,yb-t,yb,z0,z1,0)
    for zz in (z0,z0+.28,z0+.56,z1-.018):mb.box(xf+.02,xback,ya,yb,zz,zz+.018,0)
    n=max(1,round((yb-ya)/.52));dw=(yb-ya)/n
    for i in range(n):
        a,b=ya+i*dw+.004,ya+(i+1)*dw-.004
        mb.frame(xf-.024,xf+.004,a,b,z0+.005,z1-.005,.035,mi=0,axis='X')
        mb.box(xf-.013,xf-.009,a+.035,b-.035,z0+.04,z1-.04,2)
        for k in range(1,4):mb.box(xf-.023,xf-.008,a,b,z0+(z1-z0)*k/4-.008,z0+(z1-z0)*k/4+.008,0)
        mid=(a+b)/2;mb.box(xf-.023,xf-.008,mid-.008,mid+.008,z0,z1,0)
        mb.sphere((xf-.04,b-.06,z0+.1),.012,seg=12,rings=8,mi=1)


def original_backsplash(M):
    """Raised ochre and teal ornamental band, repeating glazed floral scroll medallions."""
    mats=[mat.new_mat('DecoOchreGlaze',(.66,.38,.10,1),rough=.27,coat=.65),
          mat.new_mat('DecoTealGlaze',(.08,.26,.27,1),rough=.24,coat=.6)]
    mb=MB()
    for x,sign,runs in ((5.483,-1,((7.1,8.3),(10.5,11.15))),(2.118,1,((8.2,9.95),(10.55,11.1)))):
        for a,b in runs:
            n=max(1,round((b-a)/.15))
            for k in range(n):
                cy=a+(k+.5)*(b-a)/n;cz=1.076
                mb.tube((x,cy,cz),(x+sign*.003,cy,cz),.044,.044,seg=24,mi=1)
                for petal in range(8):
                    ang=math.tau*petal/8
                    points=[]
                    for j in range(17):
                        u=math.tau*j/16;r=.032+.017*math.cos(u);th=ang+.19*math.sin(u)
                        points.append((x+sign*.005,cy+r*math.cos(th),cz+r*math.sin(th)))
                    mb.path_tube(points,.002,seg=5,mi=0)
                mb.tube((x,cy,cz),(x+sign*.006,cy,cz),.010,.010,seg=12,mi=0)
                for zz in (1.009,1.145):mb.tube((x,a+k*(b-a)/n,zz),(x,a+(k+1)*(b-a)/n,zz),.0025,.0025,seg=6,mi=0)
    mb.build('Back_OriginalDecoTileBand',mats,coll='House',smooth=True)


def main_bath(M):
    """Photos 12/13: pedestal and toilet; tub, separate shower and peach/blue checker tile."""
    from .interior_back import _local,_checker,_tub_shell,_pedestal_sink,_toilet,_towel_bar
    L=_local(M);mb=MB()
    # Tub spans the north wall; the glass shower occupies its east end (floor plan 31).
    tx0,tx1,ty0,ty1=-5.42,-3.77,11.82,12.64
    mb.plate(tx0-.05,tx1+.06,ty0-.06,ty1+.06,.05,.55,holes=[(tx0+.07,tx1-.07,ty0+.06,ty1-.06)],mi=0)
    _tub_shell(mb,tx0+.07,tx1-.07,ty0+.06,ty1-.06,.13,.565,1,r=.13)
    mb.box(tx0-.05,tx1+.06,ty0-.06,ty0-.045,.04,.55,0)
    mb.build('Back_BathOriginalTub',[L['cream4_xy'],M['porcelain']],coll='House',smooth=True)
    mb=MB()
    mb.box(-5.5,-3.70,12.73,12.75,.10,1.11,0)
    mb.box(-5.5,-5.485,11.7,12.75,.1,1.11,1)
    _checker(mb,'X',-5.5,-3.70,12.73,-1,.59,3,2,3,4,t=.15)
    _checker(mb,'Y',11.72,12.75,-5.485,1,.59,3,2,3,4,t=.15)
    # pony partition between the tub and the separate shower, tile both sides
    mb.box(-3.76,-3.65,11.75,12.75,.02,1.1,0)
    _checker(mb,'Y',11.75,12.75,-3.76,-1,.59,3,2,3,4,t=.15)
    mb.box(-3.78,-3.63,11.73,12.75,1.10,1.14,0)
    # shower wall tile, pan and curb
    mb.box(-3.65,-2.88,12.73,12.75,.03,2.18,0)
    mb.box(-2.90,-2.85,11.70,12.75,.03,2.18,1)
    mb.box(-3.65,-2.87,11.72,12.73,.03,.075,0)
    mb.box(-3.66,-2.85,11.70,11.78,.03,.14,0)
    mb.build('Back_BathOriginalTile',[L['cream4_xz'],L['cream4_yz'],L['peach2'],L['teal2'],L['grout_pale']],coll='House')
    mb=MB()
    mb.box(-3.70,-3.69,11.78,12.73,1.14,2.13,0)
    mb.box(-3.64,-2.89,11.737,11.743,.14,2.13,0)
    mb.frame(-3.67,-2.85,11.72,11.76,.13,2.16,.025,mi=1,axis='Y')
    for zz in (.44,1.86):mb.box(-2.93,-2.87,11.713,11.762,zz-.03,zz+.03,1)
    mb.path_tube([(-3.53,11.74,.95),(-3.53,11.67,.95),(-3.53,11.67,1.23),(-3.53,11.74,1.23)],.008,seg=12,mi=1)
    mb.box(-3.725,-3.675,11.75,12.75,2.13,2.16,1)
    mb.build('Back_BathOriginalShowerGlass',[L['glass_clear'],M['chrome']],coll='House')
    mb=MB()
    for xx,yy,z in ((-3.25,12.71,1.14),(-3.91,12.71,.85)):
        mb.tube((xx,yy,z),(xx,yy-.05,z),.055,.055,seg=20,mi=0)
        mb.tube((xx,yy-.05,z),(xx+.035,yy-.08,z+.07),.012,.008,seg=12,mi=0)
    mb.path_tube([(-3.25,12.71,1.96),(-3.25,12.58,2.01),(-3.25,12.48,1.97)],.012,seg=12,mi=0)
    mb.lathe(-3.25,12.48,1.935,[(.055,0),(.055,.01),(.015,.04)],seg=24,mi=0)
    mb.path_tube([(-3.91,12.70,.75),(-3.91,12.56,.75),(-3.91,12.54,.73)],.019,seg=12,mi=0)
    mb.box(-3.29,-3.20,12.2,12.29,.075,.078,1)
    mb.build('Back_BathOriginalBrass',[M['brass'],M['chrome']],coll='House',smooth=True)
    # Source has a white pedestal, not the earlier fitted vanity.
    mb=MB();_pedestal_sink(mb,-4.25,10.34,0,1)
    from .interior_upper import _widespread
    _widespread(mb,-4.25,10.17,.865,1,dir=(0,1))
    _toilet(mb,-5.10,10.42,0,tank=(0,-1))
    mb.box(-4.58,-3.92,10.05,10.105,1.12,1.99,2)
    mb.frame(-4.63,-3.87,10.04,10.13,1.07,2.04,.055,mi=3,axis='Y')
    mb.box(-5.07,-4.73,10.05,10.18,1.10,2.15,3)
    mb.box(-5.035,-4.765,10.181,10.185,1.14,2.11,2)
    mb.frame(-5.07,-4.73,10.18,10.195,1.10,2.15,.03,mi=3,axis='Y')
    twin_sconce(mb,-4.25,10.10,2.10,0,1,1,4)
    _towel_bar(mb,'X',-3.55,-3.05,10.05,1,1.18,1,5)
    mb.build('Back_BathOriginalPedestal',[M['porcelain'],M['brass'],M['mirror'],M['trim'],L['emit_glass'],L['towel']],coll='House',smooth=True)
    add_light('L_Back_BathSconce','POINT',(-4.25,10.32,2.23),24,(1,.9,.76),size=.15)
    add_light('L_Back_BathCeiling','POINT',(-4.1,11.2,2.57),32,(1,.96,.9),size=.25)
    add_light('L_Back_BathShower','POINT',(-3.24,12.12,2.55),15,(1,.95,.85),size=.18)


def window_air_conditioners(M):
    """The same primary-suite sash unit seen in photos 20 and 30, including louvers and brackets."""
    mb=MB()
    for name,inside,outside in (('PrimWE2',5.21,5.94),):
        o=BY_NAME[name];cy=(o['a0']+o['a1'])/2;z=o['z0']+.02;side=1 if outside>inside else -1
        mb.rbox(min(inside,outside),max(inside,outside),cy-.31,cy+.31,z,z+.29,r=.012,mi=0)
        # Interior intake grille and narrow controls, external condenser grille.
        for face in (inside,outside):
            direction=-side if face==inside else side
            mb.box(face,face+direction*.005,cy-.26,cy+.23,z+.045,z+.245,1)
            for k in range(10):mb.box(face+direction*.006,face+direction*.012,cy-.265,cy+.235,z+.05+k*.019,z+.06+k*.019,0)
        for yy in (cy-.25,cy+.25):
            mb.tube((outside-side*.07,yy,z-.01),(outside-side*.38,yy,z-.32),.012,.012,seg=8,mi=2)
        for yy in (cy+.26,cy+.29):mb.tube((inside,yy,z+.17),(inside-side*.016,yy,z+.17),.012,.012,seg=12,mi=2)
    mb.build('Ext_OriginalWindowAC',[M['appliance'],M['black_metal'],M['steel']],coll='House',bevel=.002)
