from pathlib import Path
import subprocess,json,hashlib
from PIL import Image,ImageChops
import numpy as np
root=Path(__file__).resolve().parents[1];file=root/'renders/tiger_scroll_15s_4k.mp4'
r=subprocess.run(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(file)],capture_output=True,text=True,check=True)
d=json.loads(r.stdout);v=next(x for x in d['streams'] if x['codec_type']=='video');rig=json.loads((root/'renders/rig-check.json').read_text())
frames=sorted((root/'renders/frames').glob('frame_*.jpg'))
checks={'h264':v['codec_name']=='h264','native2160x3840':v['width']==2160 and v['height']==3840,'24fps':v['r_frame_rate']=='24/1','360Frames':int(v['nb_read_frames'])==360,'15Seconds':abs(float(d['format']['duration'])-15)<.001,'silent':not any(x['codec_type']=='audio' for x in d['streams']),'rigChecks':rig['passed'],'360NativeFrames':len(frames)==360 and all(Image.open(f).size==(2160,3840) for f in frames)}
r=subprocess.run(['ffmpeg','-v','error','-i',str(file),'-f','null','-'],capture_output=True,text=True);checks['fullDecode']=r.returncode==0 and not r.stderr.strip()
# JPEG comments contain different render times; compare image pixels, not headers.
a=Image.open(root/'renders/poster-000.jpg').convert('RGB');b=Image.open(root/'renders/poster-359.jpg').convert('RGB')
checks['originalPaintingRestored']=ImageChops.difference(a,b).getbbox() is None
r=subprocess.run(['ffmpeg','-v','error','-i',str(file),'-vf',"select='eq(n,0)+eq(n,359)'",'-vsync','0','-frames:v','2','-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True,check=True)
pixels=np.frombuffer(r.stdout,dtype=np.uint8).reshape(2,3840,2160,3);loop_mae=float(np.abs(pixels[0].astype(np.int16)-pixels[1].astype(np.int16)).mean());checks['encodedLoopMatches']=loop_mae<2
sha=hashlib.sha256(file.read_bytes()).hexdigest();result={'passed':all(checks.values()),'checks':checks,'width':v['width'],'height':v['height'],'fps':v['r_frame_rate'],'frames':int(v['nb_read_frames']),'duration':float(d['format']['duration']),'bytes':file.stat().st_size,'sha256':sha,'encodedOpeningClosingMeanPixelError':loop_mae,'engine':'Blender Workbench 4.3.2','rendererNote':'Native 4K geometry render, followed by ink grading and a continuous return dissolve.'}
(root/'renders/verification.json').write_text(json.dumps(result,indent=2));(root/'renders/SHA256SUMS').write_text(sha+'  tiger_scroll_15s_4k.mp4\n');print(json.dumps(result,indent=2))
if not result['passed']:raise SystemExit(1)
