"""Layered privacy hedges, mature trees, rose planting and palms beyond the estate."""
import math,random
from .details import B,box
from archviz import plants,trees
from archviz.lights import add_light

def build(M):
    rng=random.Random(805)
    plants.mats()['rose_red']=plants.flower_shader('Alpine rose carmine',kind='rose',c_in=(.33,.018,.028,1),c_out=(.73,.055,.095,1))
    # Clipped hedges have individual leaf cards over dark cores, plus irregular crowns.
    for side in (-1,1):
        x=side*15.0
        for j in range(5):
            ya=-14+j*21.2;yb=ya+21.25;h=6.3+(.6 if j in (1,3) else 0)
            plants.hedge(f'Privacy hedge {side} {j}',x-.65,x+.65,ya,yb,-.05,h,kind='hedge',seed=110+j+(side+1)*30,size=.21,cov=1.1)
        for j,y in enumerate((-9,8,30,52,74,91)):
            trees.oak(f'Boundary canopy {side} {j}',(side*(18.1+rng.uniform(0,4)),y,-.12),height=rng.uniform(11,16),spread=rng.uniform(7,10),trunk_r=.31,seed=15+j+(side+1)*10,detail=.29,min_z=5.5,mats={'bark':M['walnut']})
    # Hero foreground trees provide close parallax on arrival and a layered estate backdrop.
    trees.olive('Front flowering tree',(5.4,-10.8,.01),height=5.5,seed=12,detail=.85,mats={'bark':M['walnut']})
    trees.oak('Front left mature oak',(-22.4,-17,.01),height=14,spread=10,trunk_r=.55,seed=92,detail=.65,min_z=5.6,mats={'bark':M['walnut']})
    trees.olive('Garden olive',(11.5,39,.01),height=5.8,seed=22,detail=.85,mats={'bark':M['walnut']})
    for j in range(6):trees.oak(f'Distant estate canopy {j}',(-25+j*11,97+rng.uniform(-3,7),-.2),height=rng.uniform(14,20),spread=12,trunk_r=.45,seed=400+j,detail=.17,min_z=5,mats={'bark':M['walnut']})
    # White border flowers encircle the pool without filling the paved coping.
    for j in range(64):
        a=2*math.pi*j/64
        x=8.95*math.cos(a);y=32+4.40*math.sin(a)
        plants.shrub(f'Pool white border {j}',(x,y,-.02),r=.27,h=.34,kind='hydrangea',colour='hyd_white',seed=j+13)
    for x,y in ((-9.2,32),(9.2,32),(0,27.4),(2.4,36.6),(-11,23.0),(11,23.0)):
        plants.shrub(f'Clipped garden sphere {x} {y}',(x,y,0),r=.65,h=1.0,kind='boxwood',seed=int(abs(x*3+y)))
    # The parterre planting changes color through each bed as in the listing.
    colors=('rose_pink','rose_white','rose_red')
    for side in (-1,1):
        for row,y in enumerate((44.7,49.7,54.7)):
            for j in range(7):
                x=side*(2.0+j*1.05);yy=y+rng.uniform(.1,2.0)
                plants.shrub(f'Rose collection {side} {row} {j}',(x,yy,.06),r=rng.uniform(.40,.59),h=rng.uniform(1.0,1.7),kind='rose',colour=colors[(row+j//3)%3],seed=130+row*31+j+(side+1)*100)
    for yy in (42.3,59.8):
        for side in (-1,1):
            plants.shrub(f'Climbing roses {side} {yy}',(side*1.65,yy,.04),r=.38,h=2.4,kind='rose',colour='rose_white',seed=int(yy)+side)
    # Dense layered front planting.
    for j in range(18):
        x=-12+j*1.4;y=-14.2+rng.uniform(-.3,.2)
        if abs(x)<6.4:continue
        plants.shrub(f'Front white roses {j}',(x,y,0),r=.6,h=1.1,kind='rose',colour='rose_white',seed=240+j)
    for x in (-7.4,-3.0,3.0,7.4):
        plants.shrub(f'Front garden lavender {x}',(x,-9.8,.02),r=.7,h=.66,kind='lavender',seed=int(abs(x*13)))
    # Planter boxes on front portico, glazed white pots on the terrace.
    b=B(M);i=b.i
    for x in (-7.0,-2.8,2.8,7.0):
        b.box(x-.68,x+.68,-2.18,-1.70,.45,.98,i['trim']);b.box(x-.6,x+.6,-2.1,-1.78,.97,.99,i['soil'])
        b.frame(x-.7,x+.7,-2.22,-2.17,.51,.92,.035,i['trim'])
        plants.shrub(f'Portico planter {x}',(x,-1.94,.97),r=.48,h=.52,kind='hydrangea',seed=int(abs(x*19)))
    b.done('Front | painted planter boxes',bevel=.009)
    # Restrained pools of amber light bring scale and depth to the evening garden.
    b=B(M)
    for side in (-1,1):
        for j,y in enumerate((24,37,44,51,58,64)):
            x=side*(12.1 if y<40 else 10.45)
            b.cylinder(x,y,0,.48,.025,seg=12,mi=i['black']);b.cylinder(x,y,.47,.50,.12,.08,seg=16,mi=i['black'])
            b.cylinder(x,y,.43,.46,.07,seg=16,mi=i['lamp'])
            add_light(f'L_path {side} {j}','POINT',(x,y,.39),10,(1,.73,.40),size=.16)
    b.done('Garden | bronze path lights',bevel=.003)
    # Layered distant street canopy hides the finite ground edge in the final crane view.
    for j in range(23):
        x=-73+j*6.6;y=-45-rng.uniform(0,27)
        trees.oak(f'Distant street canopy {j}',(x,y,-.1),height=rng.uniform(15,21),spread=rng.uniform(11,16),trunk_r=.4,seed=700+j,detail=.16,min_z=5,mats={'bark':M['walnut']})
    # Botanical palm fronds above slender trunks, using the species leaf shader.
    MM=plants.mats()
    for j in range(10):
        x=-40+j*8.3;y=95+rng.uniform(-10,12);h=rng.uniform(17,24);b=B(M)
        b.tube((x,y,-.2),(x+.10,y,h),.19,.105,seg=14,mi=i['walnut'])
        b.done(f'Skyline | palm trunk {j}')
        F=plants.Foliage(990+j);plants._palm(F,x+.1,y,h-1.7,4.0,spread=1.4)
        F.build(f'Skyline | palm crown {j}',[MM['stem'],MM['soil'],MM['stem']],coll='Landscape')
