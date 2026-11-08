"""One-command Blender -> frame sequence -> hanji finish -> MP4 -> verification."""
import argparse,subprocess,shutil,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--blender',default=shutil.which('blender'));p.add_argument('--4k',dest='fourk',action='store_true');p.add_argument('--engine',choices=['workbench','eevee'],default='workbench');p.add_argument('--resume',action='store_true');a=p.parse_args()
root=Path(__file__).resolve().parents[1]
if not a.blender:raise SystemExit('Blender 4.3+ is required. Install from https://www.blender.org/download/ and add blender to PATH or use --blender /path/to/blender.')
if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):raise SystemExit('Install FFmpeg/FFprobe and add them to PATH: https://ffmpeg.org/download.html')
def run(cmd):
 print('RUN:',cmd,flush=True);subprocess.run(cmd,cwd=root,check=True)
blend=root/'autumn_cranes.blend'
if not a.resume or not blend.exists():run([a.blender,'-b','-t','4','-P','scripts/create_scene.py','--','--out',str(root),'--engine',a.engine,'--resolution','2160' if a.fourk else '1080'])
run([a.blender,'-b',str(blend),'-t','4','-P','scripts/render_frames.py','--']+(['--resume'] if a.resume else []))
run([sys.executable,'scripts/encode.py']);run([sys.executable,'scripts/verify.py'])
