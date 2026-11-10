"""Cinematic autumn photograph animation. Deterministic 360-frame renderer."""
from pathlib import Path
import math,sys,json,subprocess,hashlib
import numpy as np
import cv2
from PIL import Image,ImageDraw,ImageFilter
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'renders';OUT.mkdir(exist_ok=True)
W,H,FPS,N=1080,1920,24,360
base=cv2.cvtColor(cv2.imread(str(ROOT/'assets/landscape.png')),cv2.COLOR_BGR2RGB)
base=cv2.resize(base,(W,H),interpolation=cv2.INTER_LANCZOS4)
y,x=np.mgrid[:H,:W].astype(np.float32);u=x/W;v=y/H
# Foreground canopy has independent wind; sky and rocks remain rigid.
hsv=cv2.cvtColor(base,cv2.COLOR_RGB2HSV)
canopy=(np.clip((hsv[:,:,1].astype(np.float32)-90)/100,0,1)*np.clip((.37-v)/.08,0,1)).astype(np.float32)
canopy=cv2.GaussianBlur(canopy,(0,0),3)
depth=np.clip((v-.36)/.64,0,1)**1.4
lakepoly=np.array([(.51,.446),(.62,.445),(.68,.461),(.70,.478),(.78,.483),(.82,.499),(.76,.507),(.70,.515),(.63,.524),(.58,.518),(.66,.501),(.72,.495),(.67,.483),(.61,.474),(.57,.466)],np.float32)
lake=np.zeros((H,W),np.uint8);cv2.fillPoly(lake,[np.int32(lakepoly*[W,H])],255)
lake=cv2.GaussianBlur(lake.astype(np.float32)/255,(0,0),3)
lum=base.mean(axis=2)/255;lake*=np.clip((lum-.47)/.3,0,1)
# Low-resolution atmospheric fields keep the mountain silhouettes crisp.
sh,sw=240,135;yy,xx=np.mgrid[:sh,:sw].astype(np.float32);uu=xx/sw;vv=yy/sh
leaf=Image.new('RGBA',(80,80));draw=ImageDraw.Draw(leaf)
pts=[(40,8),(46,25),(58,15),(56,32),(72,30),(58,44),(64,53),(46,53),(41,69),(36,53),(18,56),(23,45),(8,34),(25,33),(21,16),(35,26)]
draw.polygon(pts,fill=(242,172,17,235));draw.line([(40,68),(40,29),(40,15)],fill=(155,88,12,200),width=2)
for end in [(23,24),(58,23),(17,35),(64,35),(24,51),(57,50)]:draw.line([(40,48),end],fill=(174,111,13,150),width=1)
leaf=leaf.filter(ImageFilter.GaussianBlur(.35))

def frame(t):
 phase=math.tau*t/15;progress=.5-.5*math.cos(math.pi*t/15)
 # Depth-dependent push, 0.6–1.3%; rigid distant ridges and foreground parallax.
 zoom=1.006+.007*progress
 mx=(x-W*.52)/(zoom+.006*depth*progress)+W*.52
 my=(y-H*.48)/(zoom+.006*depth*progress)+H*.48
 mx+=canopy*(2.8*np.sin(t*1.25+v*14)+.55*np.sin(t*2.9+u*18))
 my+=canopy*1.2*np.sin(t*1.15+u*11)
 mx+=lake*1.6*np.sin(y*.22+x*.04-t*4)
 my+=lake*.75*np.sin(y*.31-t*5+x*.018)
 image=cv2.remap(base,mx,my,cv2.INTER_CUBIC,borderMode=cv2.BORDER_REFLECT).astype(np.float32)
 # A few fine sunlit ripples, restrained enough to retain the photograph.
 shine=(np.sin(y*.31-t*5.3+np.sin(x*.026)*2)*.5+.5)**9
 image+=lake[:,:,None]*shine[:,:,None]*np.array([8,6,2],np.float32)
 fog=np.zeros((sh,sw),np.float32)
 for cx,cy,rx,ry,offset in [(.32,.412,.29,.011,0),(.63,.432,.28,.012,1.4),(.39,.453,.20,.008,2.9)]:
  fog+=np.exp(-((uu-cx-.018*math.sin(t*.27+offset))/rx)**2-((vv-cy-.002*math.sin(t*.4+offset))/ry)**2)*(.045+.015*math.sin(t*.5+offset))
 fog=cv2.resize(fog,(W,H),interpolation=cv2.INTER_LINEAR)[:,:,None]
 image=image*(1-fog)+np.array([218,228,240],np.float32)*fog
 # Very gentle sunset warmth breathes without flashing.
 sun=np.exp(-((uu-.821)/.12)**2-((vv-.366)/.055)**2)
 sun=cv2.resize(sun,(W,H),interpolation=cv2.INTER_LINEAR)[:,:,None]
 image+=sun*float(1.3*math.sin(t*.43))*np.array([1,.55,.15],np.float32)
 result=Image.fromarray(np.uint8(np.clip(image,0,255))).convert('RGBA')
 for i,(sx,sy,sz) in enumerate([(.25,.06,18),(.58,.18,14),(.12,.34,20),(.77,.12,12)]):
  px=W*(sx+.045*math.sin(t*.6+i*1.7));py=H*(sy+.019*t)
  sprite=leaf.resize((sz,sz),Image.Resampling.LANCZOS)
  squash=.45+.55*abs(math.cos(t*1.6+i))
  sprite=sprite.resize((max(3,round(sz*squash)),sz),Image.Resampling.BICUBIC).rotate(t*(17+i*5)+i*41,Image.Resampling.BICUBIC,expand=True)
  sprite.putalpha(sprite.getchannel('A').point(lambda a:round(a*.82)))
  result.alpha_composite(sprite,(int(px),int(py)))
 return result.convert('RGB')

if '--preview' in sys.argv:
 for t in [0,4,9,14]:frame(t).save(OUT/f'preview-{t:02}.jpg',quality=94)
 raise SystemExit
path=OUT/'golden_autumn_15s.mp4'
cmd=['ffmpeg','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-frames:v',str(N),'-an','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(path)]
with (OUT/'encoding.log').open('w') as log:
 proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=log)
 for n in range(N):
  im=frame(n/FPS);proc.stdin.write(im.tobytes())
  if n in [0,144,359]:im.save(OUT/f'poster-{n:03}.jpg',quality=94)
  if n%48==0:print(f'FRAME {n+1}/{N}',flush=True)
 proc.stdin.close()
 if proc.wait():raise RuntimeError('Encoding failed')
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(path)]));vs=probe['streams'][0]
checks={'h264':vs['codec_name']=='h264','1080x1920':(vs['width'],vs['height'])==(W,H),'24fps':vs['r_frame_rate']=='24/1','360frames':int(vs['nb_read_frames'])==N,'15seconds':abs(float(probe['format']['duration'])-15)<.001,'silent':len(probe['streams'])==1}
r=subprocess.run(['ffmpeg','-v','error','-i',str(path),'-f','null','-'],capture_output=True,text=True);checks['fullDecode']=r.returncode==0 and not r.stderr.strip()
report={'passed':all(checks.values()),'checks':checks,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'animation':'Depth-dependent slow camera push, canopy breeze, travelling valley mist, sunlit lake ripples and four tiny drifting maple leaves.'}
(OUT/'verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2),flush=True)
if not report['passed']:raise SystemExit(1)
