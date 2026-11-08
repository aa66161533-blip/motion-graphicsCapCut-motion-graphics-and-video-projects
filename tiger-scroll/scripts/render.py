import bpy,sys,argparse,time,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--sample',action='store_true');p.add_argument('--percent',type=int,default=100);p.add_argument('--start',type=int,default=1);p.add_argument('--end',type=int,default=360);p.add_argument('--resume',action='store_true');a=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
root=Path(bpy.data.filepath).parent;s=bpy.context.scene;s.render.resolution_percentage=a.percent;s.display.render_aa='FXAA'
folder=root/'renders'/('samples' if a.sample else 'frames');folder.mkdir(parents=True,exist_ok=True)
s.render.image_settings.file_format='JPEG';s.render.image_settings.quality=97;s.render.image_settings.color_mode='RGB'
frames=[1,73,145,193,241,313,337,360] if a.sample else list(range(a.start,a.end+1));audit=[];began=time.monotonic()
for f in frames:
 out=folder/f'frame_{f:04d}.jpg'
 if a.resume and out.exists():continue
 s.frame_set(f);bpy.context.view_layer.update();s.render.filepath=str(out);t=time.monotonic();bpy.ops.render.render(write_still=True)
 audit.append({'frame':f,'time':(f-1)/24,'renderSeconds':time.monotonic()-t})
 print(f'TIGER_FRAME {f}/360 elapsed={time.monotonic()-began:.1f}s render={time.monotonic()-t:.2f}s',flush=True)
report={'frames':len(audit),'width':int(s.render.resolution_x*a.percent/100),'height':int(s.render.resolution_y*a.percent/100),'engine':s.render.engine,'seconds':time.monotonic()-began,'audit':audit}
(root/'renders'/('sample-report.json' if a.sample else f'render-report-{a.start}-{a.end}.json')).write_text(json.dumps(report,indent=2))
