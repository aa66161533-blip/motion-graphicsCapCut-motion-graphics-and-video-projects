"""Illustration-led ink-wash motion graphic. Pillow + NumPy + FFmpeg."""
from pathlib import Path
from PIL import Image,ImageFilter
import numpy as np
import math,subprocess,json,hashlib

ROOT=Path(__file__).resolve().parent;OUT=ROOT/'renders';OUT.mkdir(exist_ok=True)
W,H,FPS,N=1080,1920,24,360
painting=Image.open(ROOT/'assets/painting.png').convert('RGB').resize((W,H),Image.Resampling.LANCZOS)
leaf0=Image.open(ROOT/'assets/leaf.png').convert('RGBA')
if leaf0.getbbox():leaf0=leaf0.crop(leaf0.getbbox())
leaf0.thumbnail((100,100),Image.Resampling.LANCZOS)
rng=np.random.default_rng(110827)
small=Image.fromarray(np.uint8(rng.uniform(80,175,(35,20)))).resize((W,H),Image.Resampling.BICUBIC).filter(ImageFilter.GaussianBlur(7))
fibres=(np.asarray(small).astype(np.float32)-128)*.095+rng.normal(0,1.05,(H,W)).astype(np.float32)
paper=Image.fromarray(np.uint8(np.clip(np.stack([237+fibres,220+fibres,190+fibres],axis=2),0,255)))
FW,FH=135,240
fy,fx=np.mgrid[0:FH,0:FW].astype(np.float32);nx,ny=fx/FW,fy/FH
noise=np.asarray(small.resize((FW,FH))).astype(np.float32)/255-.5
arrival=np.minimum.reduce([np.sqrt(((nx-.04)*.9)**2+((ny-.10)*.8)**2),np.sqrt(((nx-.82)*.9)**2+((ny-.18)*.8)**2)+.09,np.sqrt(((nx-.35)*.9)**2+((ny-.55)*.8)**2)+.16,np.sqrt(((nx-.4)*.9)**2+((ny-.84)*.8)**2)+.24])+noise*.17
protect=1-np.exp(-((nx-.65)/.16)**2-((ny-.37)/.10)**2)
def smooth(a,b,x):u=np.clip((x-a)/(b-a),0,1);return u*u*(3-2*u)
def clip(x):return max(0,min(1,x))

def warp(t):
 phase=math.tau*t/15;zoom=1.006+.010*math.sin(math.pi*t/15)**2
 def source(x,y):
  u,v=x/W,y/H
  pine=clip(1-u/.60)*clip(1-v/.40)
  branch=clip((u-.72)/.28)*math.exp(-((v-.56)/.2)**2)
  water=clip((v-.843)/.10)
  dx=1.4*pine*math.sin(phase*2+v*3)+branch*.65*math.sin(phase*2+v*7)+water*2.2*math.sin(v*93+phase*2)
  dy=.50*pine*math.sin(phase*2+.5)+water*.50*math.sin(u*17-phase*2)
  return ((x-W/2)/zoom+W/2+2*math.sin(phase)+dx,(y-H/2)/zoom+H/2+.6*math.sin(phase)+dy)
 mesh=[];cols,rows=24,40
 for j in range(rows):
  top=round(j*H/rows);bottom=round((j+1)*H/rows)
  for i in range(cols):
   left=round(i*W/cols);right=round((i+1)*W/cols)
   # Pillow MESH order is upper-left, lower-left, lower-right, upper-right.
   quad=source(left,top)+source(left,bottom)+source(right,bottom)+source(right,top)
   mesh.append(((left,top,right,bottom),quad))
 return painting.transform((W,H),Image.Transform.MESH,mesh,Image.Resampling.BICUBIC)

def frame(t):
 phase=math.tau*t/15
 image=warp(t).convert('RGBA')
 fog=np.zeros((FH,FW),np.float32)
 for cx,cy,rx,ry,p in [(.54,.245,.30,.040,0),(.85,.325,.27,.037,1.2),(.55,.79,.37,.023,2.1)]:
  fog+=np.exp(-((nx-cx-.025*math.sin(phase+p))/rx)**2-((ny-cy-.005*math.sin(phase+p))/ry)**2)*.13
 fog*=protect
 mask=Image.fromarray(np.uint8(np.clip(fog*255,0,255))).resize((W,H),Image.Resampling.BILINEAR)
 veil=Image.new('RGBA',(W,H),(242,229,205,0));veil.putalpha(mask);image.alpha_composite(veil)
 # Sparse, fine painted leaves; none cross the tiger's face.
 for i,(sx,sy,size,p) in enumerate([(.88,.08,28,0),(.96,.31,22,1.3),(.79,.55,24,3.2),(.06,.24,18,4.1),(.90,.76,20,5.0)]):
  u=t/15;x=W*(sx-.055*u)+8*math.sin(phase*.6+p);y=H*(sy+.14*u)+5*math.sin(phase+p)
  spr=leaf0.resize((size,max(1,round(size*leaf0.height/leaf0.width))),Image.Resampling.LANCZOS)
  spr=spr.rotate(p*35+t*(5+i),Image.Resampling.BICUBIC,expand=True)
  alpha=spr.getchannel('A').point(lambda a:int(a*.68));spr.putalpha(alpha)
  image.alpha_composite(spr,(int(x),int(y)))
 # Organic capillary reveal of the entire illustrated painting.
 progress=float(smooth(0,2.8,t));threshold=progress*1.3
 reveal=np.clip((threshold-arrival)/.115,0,1);reveal=reveal*reveal*(3-2*reveal)
 if t>=2.8:reveal[:]=1
 mask=Image.fromarray(np.uint8(reveal*255)).resize((W,H),Image.Resampling.BICUBIC)
 return Image.composite(image.convert('RGB'),paper,mask)

dest=OUT/'traditional_ink_15s.mp4'
cmd=['ffmpeg','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-frames:v',str(N),'-an','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(dest)]
with (OUT/'encoding.log').open('w') as log:
 proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=log)
 for f in range(N):
  im=frame(f/FPS);proc.stdin.write(im.tobytes())
  if f in (48,168,359):im.save(OUT/f'poster-{f:03d}.jpg',quality=95)
  if f%48==0:print(f'FRAME {f+1}/{N}',flush=True)
 proc.stdin.close()
 if proc.wait()!=0:raise RuntimeError('FFmpeg encoding failed')
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(dest)]))
v=next(s for s in probe['streams'] if s['codec_type']=='video')
checks={'h264':v['codec_name']=='h264','1080x1920':v['width']==W and v['height']==H,'24fps':v['r_frame_rate']=='24/1','360frames':int(v['nb_read_frames'])==N,'15seconds':abs(float(probe['format']['duration'])-15)<.001,'silent':len(probe['streams'])==1}
decoded=subprocess.run(['ffmpeg','-v','error','-i',str(dest),'-f','null','-'],capture_output=True,text=True);checks['fullDecode']=decoded.returncode==0 and not decoded.stderr.strip()
report={'passed':all(checks.values()),'checks':checks,'bytes':dest.stat().st_size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'method':'Traditional illustration with capillary ink reveal, localized pine/water deformation, animated mist and painted leaves.'}
(OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,indent=2),flush=True)
if not report['passed']:raise SystemExit(1)
