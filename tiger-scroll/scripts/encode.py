"""Ink-grade genuine Blender frames and return continuously to the opening painting."""
from pathlib import Path
import argparse,subprocess
import numpy as np
from PIL import Image,ImageOps,ImageFilter,ImageEnhance
p=argparse.ArgumentParser();p.add_argument('--sample',action='store_true');a=p.parse_args()
root=Path(__file__).resolve().parents[1];folder=root/'renders'/('samples' if a.sample else 'frames');files=sorted(folder.glob('frame_*.jpg'))
if not files:raise SystemExit('No rendered frames found.')
if not a.sample and [int(f.stem.split('_')[-1]) for f in files]!=list(range(1,361)):raise SystemExit('Exactly 360 frames are required.')
W,H=Image.open(files[0]).size;rng=np.random.default_rng(13424)
paper_a=np.empty((H,W,3),np.uint8);grain=rng.normal(0,.9,(H,W)).astype(np.float32)
for i,v in enumerate([237,228,205]):paper_a[:,:,i]=np.uint8(np.clip(v+grain,0,255))
paper=Image.fromarray(paper_a);del paper_a,grain
small=Image.fromarray(np.uint8(rng.uniform(50,205,(max(2,H//100),max(2,W//100))))).resize((W,H),Image.Resampling.BICUBIC).filter(ImageFilter.GaussianBlur(10))
field=np.asarray(small).astype(np.float32)/255
yy,xx=np.mgrid[0:H,0:W].astype(np.float32);radial=np.sqrt((xx/W-.48)**2+((yy/H-.68)*.8)**2)*2;del xx,yy
def smooth(a,b,t):u=np.clip((t-a)/(b-a),0,1);return u*u*(3-2*u)
def grade(im,t):
 flat=1-float(smooth(5.9,8.1,t))
 mono=ImageOps.colorize(ImageOps.grayscale(im),black='#252722',white='#eadebf')
 image=Image.blend(ImageEnhance.Color(im).enhance(.20),mono,.78*flat+.12)
 image=Image.blend(image,paper,.032)
 # Ink breathing through the paper accompanies the first blink/head turn.
 spread=float(smooth(3,3.8,t)*(1-smooth(4.6,5.6,t)))
 if spread>0:
  wash=ImageOps.colorize(small,black='#514d40',white='#efe2c6');front=float(smooth(3,4.8,t));mask=smooth(radial+field*.09,radial+field*.09+.14,front)*spread*.14;mask=Image.fromarray(np.uint8(np.clip(mask*255,0,255)));image=Image.composite(wash,image,mask)
 return image
opening=grade(Image.open(files[0]).convert('RGB'),0)
def finish(im,t):
 im=grade(im,t)
 if t>=13.65:
  amount=float(smooth(13.65,14.958333333,t))
  # A nonuniform ink dissolve, no edit or camera cut.
  m=np.clip((amount*1.5-field*.48)*2.0,0,1)
  if t>=14.9583:m[:]=1
  mask=Image.fromarray(np.uint8(m*255));im=Image.composite(opening,im,mask)
 return im
if a.sample:
 out=root/'renders/previews';out.mkdir(exist_ok=True)
 for f in files:finish(Image.open(f).convert('RGB'),(int(f.stem.split('_')[-1])-1)/24).save(out/(f.stem+'.jpg'),quality=95)
 print('Finished sample ink grading',flush=True)
else:
 out=root/'renders/tiger_scroll_15s_4k.mp4'
 cmd=['ffmpeg','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r','24','-i','-','-frames:v','360','-an','-c:v','libx264','-preset','fast','-crf','18','-maxrate','40M','-bufsize','80M','-pix_fmt','yuv420p','-movflags','+faststart',str(out)]
 with (root/'renders/encoding.log').open('w') as log:
  proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=log)
  for i,f in enumerate(files):
   im=finish(Image.open(f).convert('RGB'),i/24);proc.stdin.write(im.tobytes())
   if i in (0,192,312,324,359):im.save(root/f'renders/poster-{i:03d}.jpg',quality=95)
   if i%24==0:print(f'ENCODE {i+1}/360',flush=True)
  proc.stdin.close()
  if proc.wait()!=0:raise SystemExit('Encoding failed; see renders/encoding.log')
 print('Encoded',out,flush=True)
