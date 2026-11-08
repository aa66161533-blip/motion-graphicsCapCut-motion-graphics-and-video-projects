"""Procedural hanji finish + 450 Blender frames -> silent H.264 MP4.
The finish only grades/composites genuine rendered 3D frames; it creates no motion.
"""
from pathlib import Path
import argparse,subprocess,json,hashlib
import numpy as np
from PIL import Image,ImageFilter,ImageEnhance
p=argparse.ArgumentParser();p.add_argument('--sample',action='store_true');p.add_argument('--root',default=str(Path(__file__).resolve().parents[1]));a=p.parse_args()
root=Path(a.root);out=root/'renders';source=out/('samples' if a.sample else 'frames')
files=sorted(source.glob('frame_*.png'))
if not files:raise SystemExit('No Blender frames found; run render_frames.py first.')
if not a.sample and [int(f.stem.split('_')[-1]) for f in files]!=list(range(1,451)):raise SystemExit('Exactly frames 1..450 are required.')
W,H=Image.open(files[0]).size
rng=np.random.default_rng(20271108)
fine=rng.normal(0,1.8,(H,W)).astype(np.float32)
small=Image.fromarray(np.uint8(rng.uniform(90,165,(max(2,H//70),max(2,W//70))))).resize((W,H),Image.Resampling.BICUBIC).filter(ImageFilter.GaussianBlur(6))
cloud=(np.asarray(small).astype(np.float32)-128)*.09
paper=np.stack([235+fine+cloud,222+fine+cloud,193+fine+cloud],axis=2)
paper=Image.fromarray(np.uint8(np.clip(paper,0,255)))
y,x=np.mgrid[0:H,0:W].astype(np.float32);nx,ny=x/W,y/H
edge=np.maximum(np.abs(nx-.5)/.5,np.abs(ny-.5)/.5)
edge=np.clip((edge-.64)/.36,0,1)**1.6
reveal_noise=np.asarray(small).astype(np.float32)/255
def smooth(a,b,x):
 u=np.clip((x-a)/(b-a),0,1);return u*u*(3-2*u)
def finish(im,t):
 returning=float(smooth(13,15,t));intro=float(smooth(0,1.65,t))
 im=ImageEnhance.Color(im).enhance(.87-returning*.17)
 im=Image.blend(im,paper,.075+returning*.055)
 # An irregular ink-wash edge on real camera-rendered imagery.
 mask=(1-edge*(.40+returning*.46))*intro
 if t<2:mask*=smooth(reveal_noise*.4,reveal_noise*.4+1.1,t)
 mask=Image.fromarray(np.uint8(np.clip(mask*255,0,255)))
 return Image.composite(im,paper,mask)
if a.sample:
 previews=out/'previews';previews.mkdir(exist_ok=True)
 for f in files:
  t=(int(f.stem.split('_')[-1])-1)/30
  finish(Image.open(f).convert('RGB'),t).save(previews/(f.stem+'.jpg'),quality=94)
 print('Sample hanji finish complete')
else:
 dest=out/'autumn_cranes_15s.mp4'
 cmd=['ffmpeg','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r','30','-i','-','-frames:v','450','-an','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(dest)]
 with (out/'encoding.log').open('w') as log:
  proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=log)
  for i,f in enumerate(files):
   im=finish(Image.open(f).convert('RGB'),i/30);proc.stdin.write(im.tobytes())
   if i in (90,225,449):im.save(out/f'poster-{i:03d}.jpg',quality=94)
   if i%60==0:print(f'ENCODE {i+1}/450',flush=True)
  proc.stdin.close()
  if proc.wait()!=0:raise SystemExit('FFmpeg failed; see renders/encoding.log')
 print('Encoded',dest,flush=True)
