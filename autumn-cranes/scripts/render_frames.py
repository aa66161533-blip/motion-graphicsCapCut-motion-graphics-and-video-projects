"""Run inside Blender: blender -b autumn_cranes.blend -P scripts/render_frames.py -- --sample"""
import bpy,sys,argparse,time,json
from pathlib import Path
from mathutils import Vector
p=argparse.ArgumentParser();p.add_argument('--aa',choices=['FXAA','5','8','16'],default='FXAA');p.add_argument('--sample',action='store_true');p.add_argument('--start',type=int,default=1);p.add_argument('--end',type=int,default=450);p.add_argument('--resume',action='store_true');p.add_argument('--preview',action='store_true')
a=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
root=Path(bpy.data.filepath).resolve().parent;folder=root/'renders'/('samples' if a.sample else 'frames');folder.mkdir(parents=True,exist_ok=True)
s=bpy.context.scene;s.display.render_aa=a.aa;s.render.resolution_percentage=50 if a.preview else 100
s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.render.image_settings.compression=15
frames=[1,90,180,226,270,330,390,450] if a.sample else list(range(a.start,a.end+1))
started=time.monotonic();audit=[]
for i,f in enumerate(frames):
    path=folder/f'frame_{f:04d}.png'
    if a.resume and path.exists():continue
    s.frame_set(f);bpy.context.view_layer.update();s.render.filepath=str(path)
    t=time.monotonic();bpy.ops.render.render(write_still=True)
    heads=[]
    for name in ['Crane A','Crane B']:
        arm=bpy.data.objects[name+' · armature'];bone=arm.pose.bones['head'];rest=arm.data.bones['head']
        tip=arm.matrix_world@bone.matrix@rest.matrix_local.inverted()@Vector((1.73,0,4.045))
        heads.append(list(tip))
    audit.append({'frame':f,'seconds':(f-1)/30,'renderSeconds':time.monotonic()-t,'beakTips':heads})
    print(f'AUTUMN_FRAME {f}/450 elapsed={time.monotonic()-started:.1f}s render={time.monotonic()-t:.2f}s',flush=True)
report={'framesRendered':len(audit),'frameStart':frames[0],'frameEnd':frames[-1],'width':int(s.render.resolution_x*s.render.resolution_percentage/100),'height':int(s.render.resolution_y*s.render.resolution_percentage/100),'engine':s.render.engine,'elapsedSeconds':time.monotonic()-started,'audit':audit}
(root/'renders'/('sample-report.json' if a.sample else f'render-report-{a.start}-{a.end}.json')).write_text(json.dumps(report,indent=2))
print('AUTUMN_RENDER_FINISHED',flush=True)
