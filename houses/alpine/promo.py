"""Original title treatment and instrumental score, generated with system Python."""
from pathlib import Path
import math,wave,json
import numpy as np
from PIL import Image,ImageDraw
from archviz.media import font
ROOT=Path(__file__).parent
FILM=ROOT/'output/film'

def tracked(d,xy,text,size=22,space=4,fill=(241,234,217,255)):
    f=font(size);x,y=xy
    for c in text:
        d.text((x,y),c,font=f,fill=fill);x+=f.getlength(c)+space

def canvas():
    a=np.zeros((1080,1920,4),dtype=np.uint8);a[:,:,:3]=(9,17,18)
    y=np.arange(1080)[:,None];x=np.arange(1920)[None,:]
    a[:,:,3]=(175*np.clip((y-690)/390,0,1)**1.25*np.clip((2300-x)/1450,.2,1)).astype(np.uint8)
    return Image.fromarray(a)

def titles():
    folder=FILM/'titles';folder.mkdir(parents=True,exist_ok=True)
    white=(250,246,235,255);gold=(214,188,136,255)
    im=canvas();d=ImageDraw.Draw(im)
    tracked(d,(96,790),'BEVERLY HILLS',22,5,gold)
    d.text((90,824),'805 North Alpine Drive',font=font(79,serif=True),fill=white)
    d.line((98,945,190,945),fill=gold,width=2)
    tracked(d,(218,932),'A PRIVATE GEORGIAN ESTATE',21,4)
    im.save(folder/'opening.png')
    im=canvas();d=ImageDraw.Draw(im)
    tracked(d,(96,786),'EXTRAORDINARY SCALE.  EXCEPTIONAL PRIVACY.',20,3,gold)
    d.text((90,819),'805 North Alpine Drive',font=font(76,serif=True),fill=white)
    tracked(d,(98,927),'7 BEDROOMS    /    9 BATHROOMS    /    12,750 SQ FT',20,2.6)
    tracked(d,(98,974),'BEVERLY HILLS, CALIFORNIA',18,3.3)
    im.save(folder/'closing.png')
    im=Image.new('RGBA',(1920,1080));d=ImageDraw.Draw(im)
    label='ARCHITECTURAL VISUALIZATION'
    d.text((1860,1044),label,font=font(15),anchor='rs',fill=(249,247,235,180),stroke_width=1,stroke_fill=(0,0,0,75))
    im.save(folder/'disclosure.png')
    print('Alpine title artwork prepared.')

def score():
    """64 s original piano, warm strings, bass and restrained cinematic percussion.
    Eight eight-second phrases; D major with extended voicings. All sounds synthesized.
    """
    sr=48000;dur=64.;rng=np.random.default_rng(805)
    mix=np.zeros((int(sr*dur),2),np.float64)
    def put(sig,when,gain=1,pan=0):
        start=max(0,int(when*sr));n=min(len(sig),len(mix)-start)
        if n<=0:return
        angle=(pan+1)*math.pi/4
        mix[start:start+n,0]+=sig[:n]*gain*math.cos(angle)
        mix[start:start+n,1]+=sig[:n]*gain*math.sin(angle)
    def key(note,length=7):
        f=440*2**((note-69)/12);t=np.arange(int(sr*length))/sr;s=np.zeros_like(t)
        for h in range(1,12):
            decay=(4.6-.22*h)*(220/f)**.22
            amp=.74**(h-1)/h**1.1;freq=f*h*math.sqrt(1+.00011*h*h)
            env=(1-np.exp(-t/.008))*np.exp(-t/decay)
            s+=amp*env*(np.sin(2*math.pi*freq*t)+.24*np.sin(2*math.pi*freq*1.0008*t+.17))
        s+=rng.normal(0,.007,len(t))*np.exp(-t/.018)
        return s*.13
    chords=[(38,50,57,61,64,69),(35,47,54,57,62,66),(31,43,50,54,57,62),(33,45,52,57,59,64),
            (30,42,50,57,61,66),(31,43,50,54,62,69),(33,45,52,57,59,64),(38,50,57,61,64,69)]
    for ci,chord in enumerate(chords):
        start=ci*8
        # Soft-bowed string choir with independent detuning and slow phrasing.
        t=np.arange(int(sr*11))/sr
        env=(1-np.exp(-t/1.8))*np.clip((11-t)/3,0,1)
        swell=.78+.20*np.sin(math.pi*np.minimum(t,8)/8)**2
        for j,note in enumerate(chord[2:]):
            f=440*2**((note-69)/12);s=np.zeros_like(t)
            for detune in (-.0024,0,.0021):
                phase=rng.uniform(0,6.28)
                for h in range(1,8):
                    s+=np.sin(2*math.pi*f*h*(1+detune)*t+phase+.16*np.sin(2*math.pi*4.6*t+j))/h**1.8
            put(s*env*swell,start,.0065 if ci<4 else .009,(j-1.5)/2.1)
        # Quiet felt-piano arpeggios leave room for the architecture.
        order=[1,3,5,4,2,4,5,3,2,3,4,5]
        for beat in range(12):
            if beat in (5,11) and ci<6:continue
            note=chord[order[beat]]+(12 if beat in (2,8) else 0)
            put(key(note),start+beat*2/3+rng.uniform(0,.012),rng.uniform(.62,.87),(note-62)/32)
        # Bass swell grounds the crane move; little low-frequency energy in the hall.
        f=440*2**((chord[0]-69)/12);t=np.arange(sr*9)/sr
        env=(1-np.exp(-t/.6))*np.exp(-t/4)*np.clip((9-t)/2,0,1)
        s=(np.sin(2*math.pi*f*t)+.24*np.sin(4*math.pi*f*t))*env
        put(s,start,.035 if ci<4 else .055,0)
        if ci>=4:
            for when in (start,start+4):
                tt=np.arange(int(sr*1.3))/sr
                thump=np.sin(2*math.pi*(42*tt+20*.04*(1-np.exp(-tt/.04))))*np.exp(-tt/.23)*(1-np.exp(-tt/.004))
                put(thump,when,.018)
    # A short upper-register motif follows the arrival and the final rise.
    for start,mel in ((1.4,(81,78,76,74)),(33.4,(78,81,83,81)),(54.4,(76,78,81,86))):
        for j,note in enumerate(mel):put(key(note,7),start+j*1.45,.27,-.20+j*.11)
    # Subtle broadband cymbal breath on the outdoor reveal.
    for start in (39.,52.):
        n=int(sr*3.8);noise=rng.normal(0,1,n);smooth=np.convolve(noise,np.ones(13)/13,mode='same')
        tt=np.arange(n)/sr;env=np.sin(math.pi*tt/3.8)**2
        put((noise-smooth)*env,start,.0012,.15)
    # Decorrelated early reflections and a long concert-hall tail.
    dry=mix.copy()
    for delay,gain in ((.037,.20),(.071,.18),(.113,.15),(.173,.13),(.271,.11),(.419,.09),(.631,.07),(.937,.055),(1.31,.040),(1.79,.028),(2.31,.018)):
        n=int(delay*sr);mix[n:,0]+=dry[:-n,1]*gain;mix[n:,1]+=dry[:-n,0]*gain*.97
    t=np.arange(len(mix))/sr
    mix*=np.minimum(1,t/1.6)[:,None]*np.clip((dur-t)/3.4,0,1)[:,None]
    peak=float(np.max(np.abs(mix)));mix*=.77/peak
    out=FILM/'alpine_original_score.wav';out.parent.mkdir(parents=True,exist_ok=True)
    with wave.open(str(out),'wb') as w:
        w.setnchannels(2);w.setsampwidth(2);w.setframerate(sr);w.writeframes((np.clip(mix,-1,1)*32767).astype('<i2').tobytes())
    (FILM/'score_notes.json').write_text(json.dumps(dict(title='Alpine / An Evening in the Flats',duration=64,sample_rate=sr,channels=2,composition='Original synthesized piano, strings, bass and subtle percussion',third_party_audio=False,peak_dbfs=20*math.log10(.77)),indent=2))
    print('Original Alpine score:',out)
if __name__=='__main__':titles();score()
