"""Verify frame completeness, encode native 1080p24 H.264, titles and original score.
Uses the isolated imageio-ffmpeg binary in output/.media_env (or system ffmpeg).
"""
import sys,os,subprocess,json,hashlib,shutil
from pathlib import Path
BASE=Path(__file__).resolve().parent
OUT=BASE/'output';FILM=OUT/'film';FRAMES=FILM/'frames/take'

def ffmpeg():
    binary=shutil.which('ffmpeg')
    if binary:return binary
    bins=list((OUT/'.media_env').glob('lib/python*/site-packages/imageio_ffmpeg/binaries/ffmpeg-*'))
    if not bins:raise RuntimeError('Install imageio-ffmpeg into output/.media_env.')
    return str(bins[0])

def run(args):
    subprocess.run([ffmpeg(),'-hide_banner','-nostdin',*args],check=True)

def validate_frames():
    from PIL import Image
    expected=[FRAMES/f'f_{j:04d}.png' for j in range(1,1537)]
    missing=[p.name for p in expected if not p.exists()]
    if missing:raise RuntimeError(f'Missing {len(missing)} frames: {missing[:12]}')
    for p in expected:
        with Image.open(p) as im:
            if im.size!=(1920,1080):raise RuntimeError(f'{p}: wrong size {im.size}')
            im.verify()
    return expected

def encode():
    frames=validate_frames();titles=FILM/'titles';score=FILM/'alpine_original_score.wav'
    master=FILM/'805_North_Alpine_Drive_Promo.mp4'
    measured=subprocess.run([ffmpeg(),'-hide_banner','-nostdin','-i',str(score),'-af','loudnorm=I=-17:TP=-1.5:LRA=10:print_format=json','-f','null','-'],capture_output=True,text=True,check=True).stderr
    stats=json.loads(measured[measured.rfind('{'):measured.rfind('}')+1])
    (FILM/'audio_normalization.json').write_text(json.dumps(stats,indent=2))
    normalization=(f"loudnorm=I=-17:TP=-1.5:LRA=10:measured_I={stats['input_i']}:measured_TP={stats['input_tp']}:"
                   f"measured_LRA={stats['input_lra']}:measured_thresh={stats['input_thresh']}:offset={stats['target_offset']}:linear=true")
    # High-bitrate broadly compatible H.264, no frame interpolation and no internal edit.
    filters=(
      '[0:v]format=rgba[base];'
      '[1:v]format=rgba,fade=t=in:st=0.8:d=1:alpha=1,fade=t=out:st=6.3:d=0.9:alpha=1[opening];'
      '[2:v]format=rgba,fade=t=in:st=58.1:d=1.2:alpha=1[closing];'
      '[base][opening]overlay=0:0:shortest=1[a];'
      '[a][closing]overlay=0:0:shortest=1[b];'
      '[b][3:v]overlay=0:0:shortest=1,fade=t=in:st=0:d=0.65,fade=t=out:st=63:d=1,format=yuv420p[v];'
      f'[4:a]{normalization},afade=t=in:st=0:d=0.7,afade=t=out:st=62:d=2[audio]'
    )
    run(['-y','-framerate','24','-start_number','1','-i',str(FRAMES/'f_%04d.png'),
      '-loop','1','-framerate','24','-i',str(titles/'opening.png'),
      '-loop','1','-framerate','24','-i',str(titles/'closing.png'),
      '-loop','1','-framerate','24','-i',str(titles/'disclosure.png'),'-i',str(score),
      '-filter_complex',filters,'-map','[v]','-map','[audio]','-t','64','-r','24',
      '-c:v','libx264','-preset','slow','-crf','17','-profile:v','high','-level','4.2',
      '-c:a','aac','-b:a','320k','-ar','48000','-movflags','+faststart',
      '-metadata','title=805 North Alpine Drive | Beverly Hills',
      '-metadata','comment=Photo-derived architectural visualization. Inferred dimensions and room connections. Original 64-second continuous camera and synthesized score.',
      '-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709',str(master)])
    clean=FILM/'805_North_Alpine_Drive_Clean.mp4'
    run(['-y','-framerate','24','-start_number','1','-i',str(FRAMES/'f_%04d.png'),'-t','64','-c:v','libx264','-preset','slow','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',str(clean)])
    # Decode every video frame and audio sample; fail on corrupt media.
    for video in (master,clean):run(['-v','error','-xerror','-i',str(video),'-f','null','-'])
    (FILM/'delivery_manifest.json').write_text(json.dumps(dict(duration_seconds=64,fps=24,resolution=[1920,1080],native_rendered_frames=len(frames),camera_takes=1,internal_cuts=0,master=str(master.name),clean=str(clean.name),source_listing='https://www.zillow.com/homedetails/805-N-Alpine-Dr-Beverly-Hills-CA-90210/20519812_zpid/',audio='Original synthesized instrumental score',decode_verified=True),indent=2))
    print(master)
if __name__=='__main__':encode()
