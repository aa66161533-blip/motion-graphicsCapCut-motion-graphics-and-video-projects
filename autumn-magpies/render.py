"""15-second ink-painting cinemagraph: moving water and two articulated magpies."""
from pathlib import Path
import sys, math, json, hashlib, subprocess
import cv2
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parent; OUT=ROOT/'renders'; OUT.mkdir(exist_ok=True)
W,H,FPS,N=1080,1920,24,360
base=cv2.cvtColor(cv2.imread(str(ROOT/'assets/painting.png')),cv2.COLOR_BGR2RGB)
base=cv2.resize(base,(W,H),interpolation=cv2.INTER_LANCZOS4)
y,x=np.mgrid[:H,:W].astype(np.float32);u=x/W;v=y/H

def poly(points,blur=3):
 m=np.zeros((H,W),np.uint8)
 cv2.fillPoly(m,[np.array([(round(a*W),round(b*H)) for a,b in points],np.int32)],255)
 return cv2.GaussianBlur(m,(0,0),blur).astype(np.float32)/255
waterfall=poly([(.42,.471),(.47,.44),(.54,.432),(.53,.45),(.62,.442),(.65,.427),(.66,.445),(.615,.467),(.60,.511),(.586,.559),(.51,.573),(.50,.543),(.53,.48),(.56,.465),(.50,.472),(.46,.494),(.43,.512)],5)
luminance=np.mean(base,axis=2)/255
waterfall*=np.clip((luminance-.57)/.28,0,1)
stream=poly([(.61,.732),(.99,.73),(.99,.775),(.72,.80),(.66,.828),(.53,.84),(.48,.861),(.67,.88),(.65,.918),(.47,.938),(.33,.984),(.13,.988),(.28,.937),(.46,.91),(.50,.89),(.34,.866),(.33,.835),(.52,.79)],6)
stream*=np.clip((luminance-.65)/.23,0,1)
foliage=np.clip((base[:,:,0].astype(float)-base[:,:,1].astype(float)-25)/90,0,1).astype(np.float32)
foliage*=np.exp(-((u-.25)/.48)**4)*np.exp(-((v-.19)/.27)**4)
# Lower mandibles are isolated and the original footprints inpainted.
jaw_defs=[([(390,1036),(411,1034),(431,1032),(429,1037),(405,1045),(390,1047)],(392,1041),17), ([(487,1124),(476,1117),(454,1111),(450,1109),(468,1123),(488,1130)],(487,1126),-19)]
clean=base.copy();jaws=[]
for points,pivot,closing in jaw_defs:
 m=np.zeros((H,W),np.uint8);cv2.fillPoly(m,[np.array(points,np.int32)],255)
 sprite=np.dstack([base,m]);jaws.append((sprite,pivot,closing))
 clean=cv2.inpaint(clean,cv2.dilate(m,np.ones((3,3),np.uint8)),4,cv2.INPAINT_TELEA)
# Smooth, independent local head rotations, throat breathing and tail sway.
heads=[(371,1045,45,63),(505,1135,39,58)]
headweights=[np.exp(-(((x-cx)/rx)**4+((y-cy)/ry)**4)*.65).astype(np.float32) for cx,cy,rx,ry in heads]
tails=[(220,1240,38,95),(620,1330,32,99)]
tailweights=[np.exp(-(((x-cx)/rx)**2+((y-cy)/ry)**2)*1.6).astype(np.float32) for cx,cy,rx,ry in tails]

def chatter(t,i):
 # Bursts alternate; long resting intervals between calls.
 cycle=(t+(0 if i==0 else 1.65))%3.8
 gate=math.sin(math.pi*cycle/1.45)**2 if cycle<1.45 else 0
 return gate*(.30+.70*(.5+.5*math.sin(2*math.pi*5.3*t+i))**2)

def frame(t):
 src=clean.copy()
 for i,(sprite,pivot,closing) in enumerate(jaws):
  # Original open beak closes in rests; opens in short chattering bursts.
  angle=closing*(1-chatter(t,i))
  mat=cv2.getRotationMatrix2D(pivot,angle,1)
  spr=cv2.warpAffine(sprite,mat,(W,H),flags=cv2.INTER_CUBIC)
  a=spr[:,:,3:4].astype(np.float32)/255
  src=(src*(1-a)+spr[:,:,:3]*a).astype(np.uint8)
 mx=x.copy();my=y.copy()
 for i,((cx,cy,rx,ry),weight) in enumerate(zip(heads,headweights)):
  ang=math.radians((1.4*math.sin(t*1.9+i*2)+1.2*chatter(t,i))*(1 if i==0 else -1))
  mx+=weight*((x-cx)*(math.cos(ang)-1)+(y-cy)*math.sin(ang))
  my+=weight*(-(x-cx)*math.sin(ang)+(y-cy)*(math.cos(ang)-1)-.7*math.sin(t*4+i))
 for i,weight in enumerate(tailweights):
  mx+=weight*2.1*math.sin(t*2.0+i*2.2);my+=weight*.8*math.sin(t*1.7+i)
 mx+=foliage*(1.8*np.sin(t*1.25+v*13));my+=foliage*.7*np.sin(t*1.4+u*12)
 mx+=waterfall*1.4*np.sin(y*.14-t*10+x*.05)
 my+=waterfall*(4*np.sin(y*.075-t*12)+1.1*np.sin(y*.21-t*18))
 mx+=stream*3.2*np.sin(y*.11+x*.028-t*5.2)
 my+=stream*1.5*np.sin(y*.13+x*.043-t*5.8)
 image=cv2.remap(src,mx,my,cv2.INTER_CUBIC,borderMode=cv2.BORDER_REFLECT).astype(np.float32)
 # Downward travelling bright water filaments, limited to painted white water.
 streak=(np.sin(y*.11-t*17+np.sin(x*.073)*3)+.4*np.sin(y*.26-t*23+x*.08))
 image+=waterfall[:,:,None]*streak[:,:,None]*7
 image+=stream[:,:,None]*np.sin(y*.19-t*6+x*.02)[:,:,None]*2.3
 # Moving mist at the foot of the falls, separate from the foreground birds.
 mist=np.exp(-((u-.56-.018*math.sin(t*.45))/.14)**2-((v-.561-.003*math.sin(t*.6))/.016)**2)*(.07+.025*math.sin(t*.8))
 image=image*(1-mist[:,:,None])+np.array([239,230,213])*mist[:,:,None]
 # Brief eyelid closures; retain the painted eyes between blinks.
 for i,(ex,ey) in enumerate([(377,1032),(500,1118)]):
  blink=(t-(2.4+i*1.3))%4.6
  if blink<.12:
   cv2.ellipse(image,(ex,ey),(5,2),0,0,360,(38,38,33),-1,cv2.LINE_AA)
 return np.uint8(np.clip(image,0,255))

if '--preview' in sys.argv:
 for t in [0,.15,.5,1.5,3.2,7.0]:Image.fromarray(frame(t)).save(OUT/f'preview-{t:.2f}.jpg',quality=93)
 raise SystemExit
path=OUT/'autumn_magpies_15s.mp4'
cmd=['ffmpeg','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-frames:v',str(N),'-an','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(path)]
with (OUT/'encoding.log').open('w') as log:
 proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=log)
 for n in range(N):
  im=frame(n/FPS);proc.stdin.write(im.tobytes())
  if n in [0,144,288]:Image.fromarray(im).save(OUT/f'poster-{n:03}.jpg',quality=94)
  if n%48==0:print(f'FRAME {n+1}/{N}',flush=True)
 proc.stdin.close()
 if proc.wait():raise RuntimeError('Encoding failed')
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(path)]))
vstream=probe['streams'][0]
checks={'h264':vstream['codec_name']=='h264','1080x1920':(vstream['width'],vstream['height'])==(W,H),'24fps':vstream['r_frame_rate']=='24/1','360frames':int(vstream['nb_read_frames'])==N,'15seconds':abs(float(probe['format']['duration'])-15)<.001,'silent':len(probe['streams'])==1}
r=subprocess.run(['ffmpeg','-v','error','-i',str(path),'-f','null','-'],capture_output=True,text=True)
checks['fullDecode']=r.returncode==0 and not r.stderr.strip()
report={'passed':all(checks.values()),'checks':checks,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'animation':'Two alternating articulated magpie beaks, local head/throat/tail motion and blinking; advecting waterfall and stream, maple movement, moving mist.'}
(OUT/'verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2),flush=True)
if not report['passed']:raise SystemExit(1)
