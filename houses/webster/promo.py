"""Webster's editorial title design and original ambient music (system Python)."""
from pathlib import Path
import math
import os
import wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).parent
FILM = Path(os.environ.get('WEBSTER_FILM_DIR',str(ROOT/'output'/'film')))


from archviz.media import font


def tracked(draw, xy, text, size=25, spacing=4, color=(242, 239, 229, 255)):
    f = font(size); x, y = xy
    for c in text:
        draw.text((x, y), c, font=f, fill=color)
        x += f.getlength(c) + spacing


def canvas():
    # Local gradient protects type without darkening the architecture above it.
    a = np.zeros((1080, 1920, 4), dtype=np.uint8)
    a[:, :, :3] = (13, 20, 22)
    y = np.arange(1080)[:, None]
    x = np.arange(1920)[None, :]
    a[:, :, 3] = (185*np.clip((y-560)/520, 0, 1)**1.1 * np.clip((2250-x)/1300, .15, 1)).astype(np.uint8)
    return Image.fromarray(a)


def make_titles():
    out = FILM / 'titles'; out.mkdir(parents=True, exist_ok=True)
    cream = (251, 247, 236, 255); gold = (207, 179, 127, 255)
    im = canvas(); d = ImageDraw.Draw(im)
    d.line((98, 746, 176, 746), fill=gold, width=3)
    tracked(d, (200, 732), 'OLD PALO ALTO', 24, 5)
    d.text((92, 778), '1836 Webster Street', font=font(88, serif=True), fill=cream)
    tracked(d, (98, 910), 'CALIFORNIA  /  A 1926 CLASSIC, REIMAGINED', 23, 3)
    im.save(out / 'title_main.png')
    im = canvas(); d = ImageDraw.Draw(im)
    tracked(d, (98, 745), 'A PLACE TO MAKE YOUR OWN', 23, 4, cream)
    d.text((93, 780), '1836 Webster Street', font=font(78, serif=True), fill=cream)
    tracked(d, (98, 897), '5 BEDROOMS   /   3.5 BATHS   /   2,831 SQ FT', 22, 2.5)
    tracked(d, (98, 946), 'OLD PALO ALTO, CALIFORNIA', 20, 3)
    im.save(out / 'title_end.png')
    im = Image.new('RGBA', (1920, 1080)); d = ImageDraw.Draw(im)
    label = 'ARCHITECTURAL VISUALIZATION  /  VIRTUALLY STAGED'
    f = font(17)
    d.text((99, 1031), label, font=f, fill=(0, 0, 0, 190), stroke_width=2, stroke_fill=(0, 0, 0, 110))
    d.text((98, 1030), label, font=f, fill=(250, 248, 239, 215))
    im.save(out / 'disclosure.png')
    print('Titles:', out)


def score():
    """A 64-second original felt-key / warm-string score, with a natural decay tail.

    D major, 90 BPM. Six 4-bar phrases mirror arrival, living, dining, garden,
    deck and suite. No third-party recording, voices or copyrighted melody.
    """
    sr = 44100; duration = 64.05
    rng = np.random.default_rng(1836)
    mix = np.zeros((int(sr*duration), 2), dtype=np.float64)

    def put(sig, start, gain=1., pan=0):
        a = int(start*sr); n = min(len(sig), len(mix)-a)
        if n <= 0: return
        theta = (pan+1)*math.pi/4
        mix[a:a+n, 0] += sig[:n]*gain*math.cos(theta)
        mix[a:a+n, 1] += sig[:n]*gain*math.sin(theta)

    def key(midi, length=7):
        f = 440*2**((midi-69)/12); t = np.arange(int(sr*length))/sr
        sig = np.zeros_like(t)
        # Slight inharmonicity and beating of the strings, soft hammer transient.
        for h in range(1, 10):
            decay = (3.7-0.14*h)*(220/f)**.20
            amp = .72**(h-1)/h**1.15
            fh = f*h*math.sqrt(1+.00013*h*h)
            phase = rng.uniform(-.15,.15)
            env = (1-np.exp(-t/0.012))*np.exp(-t/decay)
            sig += amp*env*(np.sin(2*np.pi*fh*t+phase)+.22*np.sin(2*np.pi*fh*1.0009*t))
        sig += rng.normal(0,.006,len(t))*np.exp(-t/.023)
        return sig*.16

    chords = [(50,57,61,66,69), (47,54,57,62,66), (43,50,54,59,62),
              (45,52,57,59,64), (43,50,54,57,62), (50,57,61,66,69)]
    phrase = 32/3
    for ci, chord in enumerate(chords):
        start = ci*phrase
        # Breathing string pad with a slow bow envelope and gentle stereo spread.
        t = np.arange(int(sr*(phrase+3)))/sr
        env = (1-np.exp(-t/1.8))*np.clip((phrase+3-t)/3,0,1)
        swell = .8+.15*np.sin(2*np.pi*t/phrase-math.pi/2)
        for j, note in enumerate(chord[1:]):
            freq = 440*2**((note-69)/12)
            sig = sum(np.sin(2*np.pi*freq*h*t+.0018*freq*np.sin(2*np.pi*.23*t+j))/h**2.2 for h in range(1,6))
            put(sig*env*swell, start, .013 if ci < 3 else .018, (j-1.5)/2.1)
        for beat in range(16):
            if beat in (3,7,11,15): continue
            order = [0,2,4,3,1,3,4,2]
            note = chord[order[beat%8]] + (12 if beat%4==2 else 0)
            when = start+beat*(2/3)+rng.uniform(-.013,.013)
            put(key(note), max(0, when), rng.uniform(.70,.95), (note-62)/28)
        if ci in (0,2,4,5):
            for j,note in enumerate((chord[4]+12,chord[3]+12,chord[2]+12)):
                put(key(note),start+2.66+j*2,.35,-.12+j*.12)
    # Multitap stereo diffusion: mild spaciousness with no rhythmic echo foreground.
    dry=mix.copy()
    for delay,gain in ((.071,.18),(.113,.14),(.179,.11),(.263,.09),(.419,.07),(.631,.05),(.937,.035), (1.37,.025)):
        n=int(delay*sr)
        mix[n:,0]+=dry[:-n,1]*gain
        mix[n:,1]+=dry[:-n,0]*gain*.94
    t=np.arange(len(mix))/sr
    mix*=np.minimum(1,t/2.2)[:,None]*np.clip((duration-t)/3.8,0,1)[:,None]
    mix*=.62/max(np.max(np.abs(mix)),1e-6)
    output=FILM/'webster_original_score.wav'; output.parent.mkdir(parents=True,exist_ok=True)
    with wave.open(str(output),'wb') as w:
        w.setnchannels(2);w.setsampwidth(2);w.setframerate(sr)
        w.writeframes((np.clip(mix,-1,1)*32767).astype('<i2').tobytes())
    print('Score:',output,'peak',float(np.max(np.abs(mix))))


if __name__ == '__main__':
    import sys
    if 'score' in sys.argv: score()
    else: make_titles()
