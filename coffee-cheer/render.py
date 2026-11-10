"""Animate the ORIGINAL coffee image without regenerating or retyping its lettering."""
from pathlib import Path
import argparse,math,json,hashlib,subprocess
import cv2
import numpy as np
W,H,FPS,N=1080,1920,30,450
ROOT=Path(__file__).resolve().parent

def ease(a,b,t):
 q=np.clip((t-a)/(b-a),0,1);return q*q*(3-2*q)

class Scene:
 def __init__(self,path):
  image=cv2.imread(str(path))
  if image is None:raise ValueError(f'Cannot read source image: {path}')
  h,w=image.shape[:2]
  if abs(w/h-9/16)>.02:raise ValueError('Source must have a portrait 9:16 aspect ratio to preserve composition.')
  self.base=cv2.cvtColor(cv2.resize(image,(W,H),interpolation=cv2.INTER_LANCZOS4),cv2.COLOR_BGR2RGB)
  self.y,self.x=np.mgrid[:H,:W].astype(np.float32);self.u=self.x/W;self.v=self.y/H
  # Keep the original lettering and red banner rigid; no text reconstruction.
  protect=np.zeros((H,W),np.uint8)
  cv2.rectangle(protect,(30,300),(1070,810),255,-1)
  self.protect=cv2.GaussianBlur(protect.astype(np.float32)/255,(0,0),10)
  hsv=cv2.cvtColor(self.base,cv2.COLOR_RGB2HSV)
  self.leaves=np.clip((hsv[:,:,1].astype(np.float32)-85)/100,0,1)*np.clip((.17-self.v)/.025,0,1)
  self.leaves=cv2.GaussianBlur(self.leaves.astype(np.float32),(0,0),3)
  # Cup and saucer remain one rigid foreground layer.
  self.depth=np.clip((self.v-.43)/.54,0,1)*(1-self.protect)
  heartzone=np.exp(-((self.u-.65)/.085)**6-((self.v-.525)/.045)**6)
  warm=(self.base[:,:,0].astype(np.float32)-self.base[:,:,2].astype(np.float32))
  bright=np.clip((self.base.mean(axis=2)-145)/80,0,1)
  self.heart=(heartzone*bright*np.clip(warm/75,0,1)).astype(np.float32)
  self.heart=cv2.GaussianBlur(self.heart,(0,0),7)

 def frame(self,t):
  # Smooth continuous push, hold, then pull back. Lettering scales rigidly.
  z=1+.022*float(ease(0,3,t))-.022*float(ease(13,15,t))
  mx=(self.x-W/2)/z+W/2;my=(self.y-H/2)/z+H/2
  # Restrained background parallax, suppressed across lettering and cup.
  back=(1-self.protect)*np.clip((.59-self.v)/.07,0,1)*np.clip((self.v-.41)/.04,0,1)
  mx+=back*1.8*math.sin(math.pi*t/15)
  wind=float(ease(6,6.6,t))*(1-.7*float(ease(9.4,10.5,t)))
  mx+=self.leaves*wind*(5*np.sin(t*1.8+self.v*7)+1.5*np.sin(t*2.7+self.u*9))
  my+=self.leaves*wind*1.8*np.sin(t*1.8+self.u*6)
  image=cv2.remap(self.base,mx,my,cv2.INTER_CUBIC,borderMode=cv2.BORDER_REFLECT).astype(np.float32)
  # Procedural layered steam begins at three seconds and rises continuously.
  strength=float(ease(3,3.7,t))*(1-.55*float(ease(12.7,15,t)))
  if strength>0:
   steam=np.zeros((H//2,W//2),np.float32)
   for j in range(5):
    points=[]
    for q in np.linspace(0,1,90):
     px=.525+(j-2)*.010+.018*q*np.sin(q*8-t*1.45+j*.9)
     py=.626-q*.195
     points.append((round(px*W/2),round(py*H/2)))
    cv2.polylines(steam,[np.array(points,np.int32)],False,.11*strength,2,cv2.LINE_AA)
   steam=cv2.GaussianBlur(steam,(0,0),3.2)
   steam=cv2.resize(steam,(W,H),interpolation=cv2.INTER_LINEAR)*(1-self.protect)
   image=image*(1-steam[:,:,None])+np.array([255,240,217])*steam[:,:,None]
  # Illuminate the existing golden heart; do not draw any new text or logo.
  sparkle=float(ease(10,10.4,t))*(1-float(ease(12.6,13.2,t)))
  if sparkle>0:
   pulse=.60+.40*math.sin(t*5)**2
   image+=self.heart[:,:,None]*sparkle*pulse*np.array([33,23,8])
   glow=np.zeros((H,W,3),np.uint8)
   for i,(ux,vy) in enumerate([(.61,.505),(.70,.508),(.655,.552),(.72,.535),(.59,.529)]):
    lum=max(0,math.sin(t*5.5+i*1.7))**8*sparkle
    if lum<.025:continue
    cx,cy=round(ux*W),round(vy*H);r=round(4+9*lum)
    color=(round(255*lum),round(220*lum),round(120*lum))
    cv2.line(glow,(cx-r,cy),(cx+r,cy),color,1,cv2.LINE_AA)
    cv2.line(glow,(cx,cy-r),(cx,cy+r),color,1,cv2.LINE_AA)
    cv2.circle(glow,(cx,cy),2,color,-1,cv2.LINE_AA)
   image+=glow.astype(np.float32)+cv2.GaussianBlur(glow,(0,0),4).astype(np.float32)*.7
  return np.uint8(np.clip(image,0,255))

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--image',type=Path,default=ROOT/'assets/coffee-original.png');ap.add_argument('--output',type=Path,default=ROOT/'renders/output.mp4');ap.add_argument('--preview',action='store_true');args=ap.parse_args()
 if not args.image.is_file():ap.error('Original image is missing. Save the attached ORIGINAL PNG/JPG and pass --image /path/to/file. No video has been rendered.')
 scene=Scene(args.image);args.output.parent.mkdir(parents=True,exist_ok=True)
 if args.preview:
  for t in [0,4.5,8,11,14.9]:cv2.imwrite(str(args.output.parent/f'preview-{t:.1f}.jpg'),cv2.cvtColor(scene.frame(t),cv2.COLOR_RGB2BGR))
  return
 cmd=['ffmpeg','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-frames:v',str(N),'-an','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(args.output)]
 with (args.output.parent/'encoding.log').open('w') as log:
  proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=log)
  for n in range(N):
   proc.stdin.write(scene.frame(n/FPS).tobytes())
   if n%60==0:print(f'FRAME {n+1}/{N}',flush=True)
  proc.stdin.close()
  if proc.wait():raise RuntimeError('FFmpeg encoding failed')
 probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(args.output)]));v=probe['streams'][0]
 checks={'h264':v['codec_name']=='h264','1080x1920':(v['width'],v['height'])==(W,H),'30fps':v['r_frame_rate']=='30/1','450frames':int(v['nb_read_frames'])==N,'15seconds':abs(float(probe['format']['duration'])-15)<.001,'silent':len(probe['streams'])==1}
 r=subprocess.run(['ffmpeg','-v','error','-i',str(args.output),'-f','null','-'],capture_output=True,text=True);checks['fullDecode']=r.returncode==0 and not r.stderr.strip()
 report={'passed':all(checks.values()),'checks':checks,'sha256':hashlib.sha256(args.output.read_bytes()).hexdigest(),'sourceSha256':hashlib.sha256(args.image.read_bytes()).hexdigest(),'method':'Original lettering retained as image pixels; rigid camera scale; local leaf animation, background parallax, rising steam, existing-heart glow.'}
 (args.output.parent/'verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
 if not report['passed']:raise SystemExit(1)
if __name__=='__main__':main()
