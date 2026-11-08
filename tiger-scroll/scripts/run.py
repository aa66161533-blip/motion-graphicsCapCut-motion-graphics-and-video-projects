import argparse,subprocess,shutil,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--blender',default=shutil.which('blender'));p.add_argument('--resume',action='store_true');a=p.parse_args();root=Path(__file__).resolve().parents[1]
if not a.blender:raise SystemExit('Install Blender 4.3.2 or pass --blender /path/to/blender')
if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):raise SystemExit('FFmpeg and FFprobe must be on PATH.')
def run(cmd):print('RUN',cmd,flush=True);subprocess.run(cmd,cwd=root,check=True)
if not a.resume or not (root/'tiger_scroll.blend').exists():run([a.blender,'--python-exit-code','1','-b','-t','4','-P','scripts/build.py'])
run([a.blender,'--python-exit-code','1','-b','tiger_scroll.blend','-t','4','-P','scripts/check_scene.py'])
run([a.blender,'--python-exit-code','1','-b','tiger_scroll.blend','-t','4','-P','scripts/render.py','--','--percent','100']+(['--resume'] if a.resume else []))
run([sys.executable,'scripts/encode.py']);run([sys.executable,'scripts/verify.py'])
