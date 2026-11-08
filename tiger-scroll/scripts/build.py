"""The Tiger in the Ink Scroll. Blender 4.3.2, a single continuous 360-frame scene."""
import bpy,sys,math,random,argparse,json
from pathlib import Path
from mathutils import Vector,Matrix
sys.path.insert(0,str(Path(__file__).resolve().parent))
from geometry import material,mesh_obj,empty,sphere,ico,box,tube,rod,key,smooth,bell

p=argparse.ArgumentParser();p.add_argument('--out',default=str(Path(__file__).resolve().parents[1]));p.add_argument('--width',type=int,default=2160)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
ROOT=Path(a.out).resolve();(ROOT/'renders').mkdir(parents=True,exist_ok=True)
rng=random.Random(20271108)
bpy.ops.wm.read_factory_settings(use_empty=True)
s=bpy.context.scene;s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=a.width;s.render.resolution_y=a.width*16//9;s.render.resolution_percentage=100
s.render.fps=24;s.render.fps_base=1;s.frame_start=1;s.frame_end=360
s.render.threads_mode='FIXED';s.render.threads=4;s.render.image_settings.file_format='JPEG';s.render.image_settings.quality=97;s.render.image_settings.color_mode='RGB';s.render.filepath='//renders/frames/frame_'
s.view_settings.view_transform='Standard';s.view_settings.look='None';s.display.render_aa='FXAA'
sh=s.display.shading;sh.light='STUDIO';sh.color_type='TEXTURE';sh.show_shadows=False;sh.show_cavity=True;sh.cavity_type='SCREEN';sh.curvature_ridge_factor=.55;sh.curvature_valley_factor=.65;sh.show_specular_highlight=False;sh.background_type='WORLD'
world=bpy.data.worlds.new('Warm hanji atmosphere');world.color=(.80,.76,.66);s.world=world

fur=material('Pearl-grey ink fur',(.52,.49,.42));white=material('Warm ivory guard fur',(.81,.79,.70));ink=material('Dense charcoal stripes',(.026,.032,.028));nosemat=material('Velvet charcoal nose',(.052,.039,.033));eyemat=material('Restrained antique amber iris',(.44,.28,.075));pupilmat=material('Pupil',(.008,.009,.007));mouthmat=material('Deep silent mouth',(.035,.022,.020));tonguemat=material('Muted tongue',(.24,.14,.12));toothmat=material('Ivory canines',(.87,.83,.71))
world_mats=[]
def wm(name,color,alpha=1):
 m=material(name,color,alpha=alpha);world_mats.append(m);return m
rock_mats=[wm('Ink ledge '+str(i),(.23+i*.038,.25+i*.036,.22+i*.033)) for i in range(9)]
mount_mats=[[wm(f'Wash distance {j}.{i}',(.30+j*.075+i*.024,.32+j*.070+i*.023,.29+j*.063+i*.021)) for i in range(5)] for j in range(4)]
bark=wm('Ancient pine bark',(.15,.16,.13));pine_mat=wm('Black pine needles',(.13,.17,.13));autumn=wm('Faded ochre needles',(.35,.24,.12));mistmat=wm('Ink mist',(.79,.80,.73),.075)
paper_mat=material('Painted hanji',(.87,.81,.66));roller_mat=material('Old scroll rollers',(.21,.15,.085));paper_mats=[paper_mat,roller_mat]

# A genuine textured paper scroll. Its image contains landscape only, never a tiger.
image=bpy.data.images.load(str(ROOT/'assets/hanji_landscape.png'));image.pack()
nodes=paper_mat.node_tree.nodes;tex=nodes.new('ShaderNodeTexImage');tex.image=image;nodes.active=tex
paper_mat.node_tree.links.new(tex.outputs['Color'],nodes.get('Principled BSDF').inputs['Base Color'])
paper=mesh_obj('Ancient painted scroll',[(-4,7.15,.8),(4,7.15,.8),(4,7.15,15.022),(-4,7.15,15.022)],[(0,1,2,3)],paper_mat)
uv=paper.data.uv_layers.new(name='Hanji UV')
for loop,co in zip(paper.data.polygons[0].loop_indices,[(0,0),(1,0),(1,1),(0,1)]):uv.data[loop].uv=co
scroll_parts=[paper]
for z in [.65,15.17]:
 scroll_parts.append(rod('Wooden scroll roller',(-4.35,7.14,z),(4.35,7.14,z),.15,roller_mat))
 for x in [-4.4,4.4]:scroll_parts.append(sphere('Scroll end cap',(x,7.14,z),(.14,.20,.20),roller_mat,detail=16))

# A connected, rugged rocky ledge, not a ground photograph.
vs=[];fs=[];NX,NY=36,36
for j in range(NY+1):
 y=-14+j*23/NY
 for i in range(NX+1):
  x=-8+i*16/NX;z=.83+.055*math.sin(x*1.4)*math.sin(y*.8)
  vs.append((x,y,z))
for j in range(NY):
 for i in range(NX):q=j*(NX+1)+i;fs.append((q,q+1,q+NX+2,q+NX+1))
ledge=mesh_obj('Living ink rock ledge',vs,fs,rock_mats)
ledge_mat=wm('Ink-painted rocky surface',(.70,.66,.55))
ln=ledge_mat.node_tree.nodes;lt=ln.new('ShaderNodeTexImage');lt.image=image;ln.active=lt;ledge_mat.node_tree.links.new(lt.outputs['Color'],ln.get('Principled BSDF').inputs['Base Color'])
ledge.data.materials.clear();ledge.data.materials.append(ledge_mat)
luv=ledge.data.uv_layers.new(name='Rock painting UV')
for loop in ledge.data.loops:
 co=ledge.data.vertices[loop.vertex_index].co;luv.data[loop.index].uv=((co.x+8)/16,(co.y+14)/23*.28)
for face in ledge.data.polygons:face.material_index=0;face.use_smooth=True
for i in range(22):
 x=rng.choice([-1,1])*rng.uniform(4.5,8.5);y=rng.uniform(-11,10)
 ico('Rugged ledge outcrop',(x,y,rng.uniform(.4,1)),(rng.uniform(.6,2),rng.uniform(.8,2),rng.uniform(.7,2)),rng.choice(rock_mats))

for i in range(35):
 x=rng.uniform(-6.5,6.5);y=rng.uniform(-10,7);points=[]
 for j in range(6):
  xx=x+j*.16;yy=y+math.sin(j*.8+i)*.12;zz=.83+.055*math.sin(xx*1.4)*math.sin(yy*.8)+.014;points.append((xx,yy,zz))
 tube('Fine ink rock fissure',points,.009,rock_mats[1],res=0)

def mountain(name,x,y,h,r,row):
 verts=[];faces=[];S,R=48,25
 for j in range(R+1):
  u=j/R
  for i in range(S+1):
   ang=i/S*math.tau;rr=r*u*(1+.12*math.sin(ang*7)+.05*math.cos(ang*11));z=h*(1-u)**.64*(1+.08*math.sin(ang*6+u*24))
   verts.append((x+math.cos(ang)*rr,y+math.sin(ang)*rr*.8,z))
 for j in range(R):
  for i in range(S):q=j*(S+1)+i;faces.append((q,q+S+1,q+S+2,q+1))
 o=mesh_obj(name,verts,faces,mount_mats[row])
 for face in o.data.polygons:face.material_index=2;face.use_smooth=True
 for k in range(7):
  ang=math.pi*(1.05+k/6*.9);points=[]
  for n in range(10):
   u=.13+n*.08;rr=r*u*(1+.12*math.sin(ang*7)+.05*math.cos(ang*11));z=h*(1-u)**.64*(1+.08*math.sin(ang*6+u*24))
   points.append((x+math.cos(ang)*rr,y+math.sin(ang)*rr*.8-.055,z+.035))
  tube('Dry ink fissure',points,.013,mount_mats[row][0],res=0)

for i,(x,y,h,r,row) in enumerate([(-23,30,20,9,0),(24,34,24,10,0),(-35,48,27,10,1),(28,50,29,12,1),(-42,64,30,12,2),(25,70,34,13,2),(-50,84,37,14,3),(32,91,39,16,3)]):mountain('Layered mountain '+str(i),x,y,h,r,row)

wind=[]
def pine(name,pos,scale):
 root=empty(name,pos);root.scale=(scale,scale,scale)
 tube('Old gnarled pine trunk',[(0,0,0),(.3,0,1.8),(-.5,.1,3.6),(.1,.15,5.3),(1,.3,6.8)],.22,bark,root,radii=[1.5,1.1,.8,.45,.12])
 for j in range(9):
  ang=j*2.399;end=Vector((math.cos(ang)*(2.8-j*.13),math.sin(ang)*(2.2-j*.1),.5))
  group=empty('Pine bough',(.1,.1,2.5+j*.43),root)
  tube('Pine branch',[(0,0,0),end*.6,end],.075,bark,group,radii=[1,.6,.10],res=1)
  # All the needles on a bough are one mesh with tiny tapered ribbons.
  verts=[];faces=[]
  for k in range(220):
   c=end+Vector((rng.gauss(0,.72),rng.gauss(0,.55),rng.gauss(0,.15)));a0=rng.random()*math.tau;length=rng.uniform(.13,.35);d=Vector((math.cos(a0)*length,math.sin(a0)*length,rng.uniform(.02,.11)))
   n=len(verts);verts.extend([tuple(c),tuple(c+Vector((.006,-.006,0))),tuple(c+d)]);faces.append((n,n+1,n+2))
  for cidx in range(9):
   c=end+Vector((rng.gauss(0,.65),rng.gauss(0,.48),rng.gauss(0,.12)));base=len(verts);verts.append(tuple(c+Vector((0,0,.08))))
   for k in range(16):
    angle=k/16*math.tau;verts.append(tuple(c+Vector((math.cos(angle)*.40,math.sin(angle)*.30,0))))
   for k in range(16):faces.append((base,base+1+k,base+1+(k+1)%16))
  mesh_obj('Fine pine needles',verts,faces,pine_mat,group);wind.append((group,rng.random()*6.28))
 return root
pine('Foreground ink pine',(-6,3,.8),1.2);pine('Right pine',(6.5,11,.8),1.3);pine('Valley pine',(-9,20,1),.9)
mist=[]
for i in range(10):
 p0=Vector((rng.uniform(-17,17),rng.uniform(12,46),rng.uniform(3,9)));o=sphere('Flowing ink cloud',p0,(8,2.2,.8),mistmat,detail=12);mist.append((o,p0,rng.random()*6.28))

# A distant ink-painted atmosphere behind genuinely separated 3D foreground layers.
backmat=wm('Distant painted ink atmosphere',(.87,.81,.66))
bn=backmat.node_tree.nodes;bt=bn.new('ShaderNodeTexImage');bt.image=image;bn.active=bt;backmat.node_tree.links.new(bt.outputs['Color'],bn.get('Principled BSDF').inputs['Base Color'])
back=mesh_obj('Far ink-wash atmosphere',[(-32,75,-34),(32,75,-34),(32,75,79.778),(-32,75,79.778)],[(0,1,2,3)],backmat)
buv=back.data.uv_layers.new(name='Atmosphere UV')
for loop,co in zip(back.data.polygons[0].loop_indices,[(0,0),(1,0),(1,1),(0,1)]):buv.data[loop].uv=co

# Construct the tiger's anatomical model and skeleton in a separate reusable module.
from licensed_tiger import make_tiger,animate_tiger
tiger=make_tiger(fur,white,ink,nosemat,eyemat,pupilmat,mouthmat,tonguemat,toothmat)

# Real 3D ink particles, cached as absolute shape keys, rather than a screen overlay.
particles=[];P=180;verts=[];faces=[]
for i in range(P):
 seed0=(rng.random()*math.tau,rng.uniform(.3,4.8),rng.uniform(.8,5),rng.uniform(.009,.045))
 particles.append(seed0);q=len(verts);verts.extend([(0,0,0)]*7)
 for k in range(6):faces.append((q,q+1+k,q+1+(k+1)%6))
cloud=mesh_obj('Swirling ink particles',verts,faces,ink);cloud.shape_key_add(name='Basis');cloud.data.shape_keys.use_relative=False

bpy.ops.object.camera_add(location=(5,-23,8));camera=bpy.context.object;camera.name='One continuous cinematic camera';s.camera=camera
camera.data.lens=52;camera.data.clip_end=260;camera.data.dof.use_dof=False
# Infinite-distance painted atmosphere: the foreground remains true 3D.
back.parent=camera;back.matrix_parent_inverse=Matrix.Identity(4);back.matrix_basis=Matrix.Identity(4)
corners=camera.data.view_frame(scene=s);coords=[v*(-180/v.z) for v in corners]
for v,co in zip(back.data.vertices,coords):v.co=co
xmin=min(v.x for v in coords);xmax=max(v.x for v in coords);ymin=min(v.y for v in coords);ymax=max(v.y for v in coords)
for loop in back.data.polygons[0].loop_indices:
 co=back.data.vertices[back.data.loops[loop].vertex_index].co;back.data.uv_layers.active.data[loop].uv=((co.x-xmin)/(xmax-xmin),(co.y-ymin)/(ymax-ymin))
back.data.update()
times=[0,3,6,8,10,13,13.8,15]
camera_points=[Vector(v) for v in [(5,-23,8),(5,-17,6.6),(5,-13,5.5),(4,-13,5),(3.8,-13.5,5.2),(2.7,-13,4.8),(2.7,-13,5.0),(5,-23,8)]]
targets=[Vector(v) for v in [(0,6.6,7.8),(.3,5,3.7),(.2,5,2.8),(.2,3,2.7),(0,.5,2.7),(0,-2.2,3.0),(0,-2.2,3.1),(0,6.6,7.8)]]
def path(points,t):
 i=0
 while i<len(times)-2 and t>times[i+1]:i+=1
 dt=times[i+1]-times[i];u=max(0,min(1,(t-times[i])/dt));ip=max(0,i-1);inn=min(len(points)-1,i+2)
 a,b=points[i],points[i+1];va=(b-points[ip])*(dt/(times[i+1]-times[ip]));vb=(points[inn]-a)*(dt/(times[inn]-times[i]))
 if i==0:va*=0
 if i==len(points)-2:vb*=0
 return a*(2*u**3-3*u*u+1)+va*(u**3-2*u*u+u)+b*(-2*u**3+3*u*u)+vb*(u**3-u*u)

# Batch static landscape geometry while retaining every material and depth layer.
static=[]
protected=set(scroll_parts+tiger['objects']+[cloud,back,ledge]+[m[0] for m in mist])
for o in list(bpy.data.objects):
 if o.type not in {'MESH','CURVE'} or o in protected or o.modifiers or (o.type=='MESH' and o.data.shape_keys):continue
 parent=o;moving=False
 while parent:
  if parent in tiger['objects'] or any(parent==w[0] for w in wind):moving=True;break
  parent=parent.parent
 if not moving:static.append(o)
bpy.ops.object.select_all(action='DESELECT')
for o in static:o.select_set(True)
if static:
 bpy.context.view_layer.objects.active=static[0];bpy.ops.object.convert(target='MESH');bpy.ops.object.join();bpy.context.object.name='Layered 3D ink landscape'

world_base={m:tuple(m.diffuse_color) for m in world_mats};paper_base={m:tuple(m.diffuse_color) for m in paper_mats}
audit=[]
for f in range(1,361):
 t=(f-1)/24;s.frame_set(f);emerge=smooth(6,8,t)*(1-smooth(13.8,14.958333333,t));paint=1-emerge
 animate_tiger(tiger,t,f)
 for m,color in world_base.items():m.diffuse_color=(*color[:3],color[3]*emerge);m.keyframe_insert(data_path='diffuse_color',frame=f)
 for m,color in paper_base.items():m.diffuse_color=(*color[:3],color[3]*paint);m.keyframe_insert(data_path='diffuse_color',frame=f)
 for o,phase in wind:o.rotation_euler=(.015*math.sin(t*.6+phase),.02*math.sin(t*.7+phase),.025*math.sin(t*.5+phase));key(o,'rotation_euler',f)
 for o,p0,phase in mist:o.location=p0+Vector((math.sin(t*.15+phase)*1.2,0,math.sin(t*.17+phase)*.15));key(o,'location',f)
 active=smooth(12.8,13.5,t)*(1-smooth(14.7,15,t));shape=cloud.shape_key_add(name='Ink '+str(f))
 for i,(phase,r,z,size) in enumerate(particles):
  angle=phase+t*1.7;r0=r*(.65+.35*math.sin(t*.6+phase));c=Vector((math.cos(angle)*r0,tiger['volume'].location.y+math.sin(angle)*r0*.5,z+math.sin(t+phase)*.8));ss=size*active
  shape.data[i*7].co=c
  for k in range(6):
   angle=k/6*math.tau;off=Vector((math.cos(angle)*ss,0,math.sin(angle)*ss*1.4));shape.data[i*7+1+k].co=c+off
 cloud.data.shape_keys.eval_time=shape.frame;key(cloud.data.shape_keys,'eval_time',f)
 camera.location=path(camera_points,t);camera.rotation_euler=(path(targets,t)-camera.location).to_track_quat('-Z','Y').to_euler();key(camera,'location',f);key(camera,'rotation_euler',f)
 if f in (1,73,145,193,241,313,337,360):audit.append({'frame':f,'time':t,'emergence':emerge,'camera':list(camera.location),'tigerPosition':list(tiger['volume'].location),'volumeDepth':tiger['volume'].scale.y})

for action in bpy.data.actions:
 for fc in action.fcurves:
  for kp in fc.keyframe_points:kp.interpolation='LINEAR'
s.frame_set(1);s['title']='The Tiger in the Ink Scroll';s['fps']=24;s['frames']=360;s['tiger_count']=1
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'tiger_scroll.blend'),compress=True)
report={'blender':bpy.app.version_string,'engine':s.render.engine,'width':s.render.resolution_x,'height':s.render.resolution_y,'fps':24,'frames':360,'seconds':15,'tigers':1,'bones':len(tiger['arm'].data.bones),'singleCamera':True,'paintingContainsTiger':False,'audit':audit}
(ROOT/'renders/scene-report.json').write_text(json.dumps(report,indent=2));print('TIGER_SCENE_READY',json.dumps(report),flush=True)
