"""Draw original ornamental textile artwork as vector motifs, rasterized for a packed Blender texture."""
from pathlib import Path
import math,random
import numpy as np
from PIL import Image,ImageDraw
OUT=Path(__file__).parent/'assets';OUT.mkdir(exist_ok=True)
W,H=1800,2400

def textile(pale=False):
    rng=random.Random(24)
    base=(164,132,100) if pale else (127,67,46)
    ink=(183,161,118) if pale else (200,170,120)
    navy=(89,107,106) if pale else (45,70,71)
    im=Image.new('RGB',(W,H),base);d=ImageDraw.Draw(im)
    for off,col,width in ((14,ink,10),(36,navy,16),(70,ink,7),(90,navy,5),(166,ink,12),(193,navy,8),(216,ink,6)):
        d.rectangle((off,off,W-off,H-off),outline=col,width=width)
    def flower(x,y,r,rot=0,p=8,col=ink):
        # Eightfold pointed petals with a fine central arabesque.
        for j in range(p):
            a=j*2*math.pi/p+rot
            pts=[]
            for t in np.linspace(0,1,13):
                rr=r*(.20+.80*math.sin(math.pi*t/2));aa=a+.26*math.sin(math.pi*t)
                pts.append((x+rr*math.cos(aa),y+rr*math.sin(aa)))
            for t in np.linspace(1,0,13):
                rr=r*(.20+.80*math.sin(math.pi*t/2));aa=a-.26*math.sin(math.pi*t)
                pts.append((x+rr*math.cos(aa),y+rr*math.sin(aa)))
            d.polygon(pts,fill=col);d.line(pts+[pts[0]],fill=navy,width=max(1,int(r/22)))
        d.ellipse((x-r*.20,y-r*.20,x+r*.20,y+r*.20),fill=navy,outline=ink,width=2)
        d.ellipse((x-r*.06,y-r*.06,x+r*.06,y+r*.06),fill=ink)
    # Continuous floral border with curling tendrils.
    for x in range(120,W-110,120):
        for y in (125,H-125):flower(x,y,39,p=6)
    for y in range(245,H-180,120):
        for x in (125,W-125):flower(x,y,38,rot=.3,p=6)
    # Dense diagonal field of palmettes and small rosettes, never polka dots.
    for row,y in enumerate(range(300,H-260,142)):
        for x in range(295+(row%2)*70,W-245,140):
            if ((x-W/2)/300)**2+((y-H/2)/420)**2<1:continue
            flower(x,y,rng.uniform(31,48),rot=(row%2)*math.pi/8,p=8,col=ink)
            flower(x+64,y+68,14,p=4,col=navy)
            d.arc((x-62,y-90,x+90,y+90),30,160,fill=ink,width=3)
            d.arc((x-90,y-30,x+60,y+142),200,325,fill=ink,width=3)
    # Medallion and pendants.
    cx,cy=W/2,H/2
    for r,col in ((310,navy),(288,ink),(253,base),(230,ink),(196,navy)):
        pts=[(cx+r*(1+.1*math.cos(8*a))*math.cos(a),cy+r*1.36*(1+.1*math.cos(8*a))*math.sin(a)) for a in np.linspace(0,2*math.pi,200)]
        d.polygon(pts,fill=col)
    flower(cx,cy,173,p=12,col=ink);flower(cx,cy,76,rot=.2,p=8,col=base)
    for sg in (-1,1):flower(cx,cy+sg*490,81,p=8,col=ink)
    # Abrasion and micro-weave combine with the shader's physical bump.
    a=np.asarray(im,dtype=np.float32)
    nr=np.random.default_rng(805)
    grain=nr.normal(0,3.2,(H,W,1));weave=np.sin(np.arange(W)[None,:,None]*math.pi)*1.5
    rough=np.asarray(Image.fromarray(nr.integers(0,255,(120,90),dtype=np.uint8)).resize((W,H),Image.Resampling.BICUBIC),dtype=float)/255
    worn=np.clip((rough-.43)*.25,0,.18)[:,:,None]
    a=a*(1-worn)+np.array((188,170,141))*worn+grain+weave
    out=OUT/('rug_ivory.png' if pale else 'rug_rust.png');Image.fromarray(np.uint8(np.clip(a,0,255))).save(out)
    print(out)
if __name__=='__main__':textile();textile(True)
