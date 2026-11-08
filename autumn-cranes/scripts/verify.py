from pathlib import Path
import subprocess,json,hashlib
root=Path(__file__).resolve().parents[1];p=root/'renders/autumn_cranes_15s.mp4'
r=subprocess.run(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(p)],capture_output=True,text=True,check=True)
probe=json.loads(r.stdout);v=next(s for s in probe['streams'] if s['codec_type']=='video')
scene=json.loads((root/'renders/scene-report.json').read_text())
rig=json.loads((root/'renders/rig-check.json').read_text())
checks={'h264':v['codec_name']=='h264','portrait9x16':v['width']*16==v['height']*9,'fullHDor4K':v['width'] in (1080,2160),'fps30':v['r_frame_rate']=='30/1','frames450':int(v['nb_read_frames'])==450,'duration15':abs(float(probe['format']['duration'])-15)<.001,'silent':not any(s['codec_type']=='audio' for s in probe['streams']),'twoCranes':scene['craneCount']==2,'fixedScale':all(v==[1,1,1] for v in scene['scale']),'bakedRig':scene['bakedAnimation'] and len(scene['armatures'])==2}
r=subprocess.run(['ffmpeg','-v','error','-i',str(p),'-f','null','-'],capture_output=True,text=True)
checks['rigAndFraming']=rig['passed'] and rig['evaluatedFrames']==450
checks['fullDecode']=r.returncode==0 and not r.stderr.strip()
sha=hashlib.sha256(p.read_bytes()).hexdigest();result={'passed':all(checks.values()),'checks':checks,'width':v['width'],'height':v['height'],'frames':int(v['nb_read_frames']),'fps':v['r_frame_rate'],'duration':float(probe['format']['duration']),'bytes':p.stat().st_size,'sha256':sha,'sceneEngine':scene['engine'],'blender':scene['blender']}
(root/'renders/verification.json').write_text(json.dumps(result,indent=2));(root/'renders/SHA256SUMS').write_text(sha+'  autumn_cranes_15s.mp4\n')
print(json.dumps(result,indent=2))
if not result['passed']:raise SystemExit(1)
