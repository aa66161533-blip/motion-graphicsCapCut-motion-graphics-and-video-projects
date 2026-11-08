import bpy,bmesh,math
from pathlib import Path
from mathutils import Vector,Matrix
from geometry import empty,sphere,rod,smooth,material,mesh_obj
from tiger import animate_tiger

def make_tiger(fur,white,ink,nosemat,eyemat,pupilmat,mouthmat,tonguemat,toothmat):
 volume=empty('Ink-to-volume transformation',(0,6.65,.82));root=empty('One Korean tiger rig',parent=volume)
 data=bpy.data.armatures.new('Tiger anatomical skeleton');arm=bpy.data.objects.new('Tiger armature',data);bpy.context.collection.objects.link(arm);arm.parent=root
 specs={'pelvis':((0,1.5,2.2),(0,.5,2.2),None),'spine':((0,.5,2.2),(0,-.4,2.3),'pelvis'),'chest':((0,-.4,2.3),(0,-1.2,2.5),'spine'),'neck':((0,-1.2,2.5),(0,-1.90,2.58),'chest'),'head':((0,-1.90,2.58),(0,-2.55,2.76),'neck'),'jaw':((0,-2.22,2.40),(0,-2.80,2.33),'head')}
 leg_paths={}
 for side,label in [(-1,'L'),(1,'R')]:
  for kind in ['F','H']:
   if kind=='F':points=[(side*.56,-.95,2.35),(side*.60,-.75,1.4),(side*.56,-1.02,.45),(side*.56,-1.10,.20),(side*.56,-1.33,.10)];radii=[(.32,.34),(.23,.23),(.125,.14),(.26,.27),(.28,.29)];parent='chest'
   else:points=[(side*.59,1.10,2.25),(side*.62,.65,1.40),(side*.59,1.40,.50),(side*.59,1.35,.20),(side*.59,1.13,.10)];radii=[(.40,.43),(.28,.28),(.15,.16),(.25,.26),(.27,.29)];parent='pelvis'
   names=[kind+label+'_'+n for n in ['upper','lower','ankle','paw']]
   for i,bn in enumerate(names):specs[bn]=(points[i],points[i+1],parent if i==0 else names[i-1])
   leg_paths[kind+label]=(points,radii,names)
 tail_points=[(0,1.5,2.3),(0,2.0,2.0),(0,2.5,1.65),(0,3.0,1.2),(0,3.45,.9),(0,3.7,1.0),(0,3.9,1.25)]
 for i in range(6):specs['tail'+str(i)]=(tail_points[i],tail_points[i+1],'pelvis' if i==0 else 'tail'+str(i-1))
 bpy.ops.object.select_all(action='DESELECT');arm.select_set(True);bpy.context.view_layer.objects.active=arm;bpy.ops.object.mode_set(mode='EDIT')
 for name,(a,b,parent) in specs.items():
  bone=data.edit_bones.new(name);bone.head=a;bone.tail=b
  if parent:bone.parent=data.edit_bones[parent]
 bpy.ops.object.mode_set(mode='OBJECT');arm.select_set(False)
 feet={}
 for label,(points,radii,names) in leg_paths.items():
  target=empty('Tiger '+label+' foot target',points[3],root);pole=empty('Tiger '+label+' leg pole',(points[0][0],3 if label[0]=='F' else -2,1.3),root)
  c=arm.pose.bones[names[2]].constraints.new('IK');c.target=target;c.pole_target=pole;c.chain_count=3;c.use_stretch=False
  feet[label]=(target,Vector(points[3]))
 # Import a CC0 anatomical study and adapt it to the authored animation rig.
 before=set(bpy.data.objects)
 asset=Path(__file__).resolve().parents[1]/'assets/tiger_cc0.glb'
 bpy.ops.import_scene.gltf(filepath=str(asset))
 imported=[o for o in bpy.data.objects if o not in before and o.type=='MESH']
 for o in imported:
  matrix=o.matrix_world.copy()
  for v in o.data.vertices:v.co=Matrix.Rotation(-math.pi/2,4,'Z')@(matrix@v.co)*2.5
  o.parent=None;o.matrix_world=Matrix.Identity(4)
  for mat in o.data.materials:
   if mat and mat.use_nodes:
    candidates=[n for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image and 'normal' not in n.image.name.lower()]
    if candidates:mat.node_tree.nodes.active=candidates[-1]
  for face in o.data.polygons:face.use_smooth=True
  o.data.update()
 body=next(o for o in imported if 'Continuous anatomical' in o.name)
 # Separate the lower mandible at the lip boundary; do not stretch a sealed face.
 jaw=body.copy();jaw.data=body.data.copy();bpy.context.collection.objects.link(jaw);jaw.name='Separated anatomical lower mandible'
 def jaw_face(face):
  c=face.calc_center_median();return c.y< -2.52 and c.z<2.385 and abs(c.x)<.40
 bm=bmesh.new();bm.from_mesh(jaw.data);bmesh.ops.delete(bm,geom=[f for f in bm.faces if not jaw_face(f)],context='FACES');bm.to_mesh(jaw.data);bm.free()
 bm=bmesh.new();bm.from_mesh(body.data)
 remove=[face for face in bm.faces if jaw_face(face) or (face.calc_center_median().y< -2.55 and abs(face.calc_center_median().x)<.40 and min(v.co.z for v in face.verts)<2.385<max(v.co.z for v in face.verts))]
 bmesh.ops.delete(bm,geom=remove,context='FACES');bm.to_mesh(body.data);bm.free()
 imported.append(jaw)
 def distance_to_segment(p,a,b):
  a,b=Vector(a),Vector(b);v=b-a;u=max(0,min(1,(p-a).dot(v)/v.length_squared));return (p-(a+v*u)).length
 def weights(co):
  y,z=co.y,co.z
  # The jaw and head occupy their true anatomical positions in the imported study.
  if y< -1.95 and z>1.80:return [('head',1)]
  if y>1.64 and z> .65 and (abs(co.x)<.28 or y>2.05):
   ds=[distance_to_segment(co,tail_points[i],tail_points[i+1]) for i in range(6)];i=min(range(6),key=lambda i:ds[i]);return [('tail'+str(i),1)]
  leg_weight=(1-smooth(1.48,2.08,z))*smooth(.24,.45,abs(co.x))
  if y<-.48:kind='F';base='chest'
  elif y>.46:kind='H';base='pelvis'
  else:leg_weight=0;kind='F';base='spine'
  if leg_weight>.001:
   label=kind+('L' if co.x<0 else 'R');points,radii,names=leg_paths[label]
   ds=[distance_to_segment(co,points[i],points[i+1]) for i in range(4)];leg_weight*=1-smooth(.25,.50,min(ds));ws=[math.exp(-d*d/.10) for d in ds];total=sum(ws)
   return [(n,w/total*leg_weight) for n,w in zip(names,ws)]+[(base,1-leg_weight)]
  if y< -1.52:return [('neck',1)]
  centers=[1.25,.3,-.8];names=['pelvis','spine','chest'];ws=[math.exp(-((y-c)/.60)**2) for c in centers];total=sum(ws)
  return [(n,w/total) for n,w in zip(names,ws)]
 def bind(o,force=None):
  groups={}
  for v in o.data.vertices:
   for name,w in ([(force,1)] if force else weights(v.co)):
    if w<.00001:continue
    if name not in groups:groups[name]=o.vertex_groups.new(name=name)
    groups[name].add([v.index],w,'REPLACE')
  mod=o.modifiers.new('Authored quadruped skin','ARMATURE');mod.object=arm;mod.use_deform_preserve_volume=True;o.parent=root
  return o
 eyes=[]
 for o in imported:
  eye=any(n in o.name.lower() for n in ['iris','pupil','eyeball','glint'])
  if eye:
   bind(o,'head');o.shape_key_add(name='Basis');blink=o.shape_key_add(name='Blink');zc=sum(v.co.z for v in blink.data)/len(blink.data)
   for v in blink.data:v.co.z=zc+(v.co.z-zc)*.025
   eyes.append((o,blink))
  else:bind(o,'jaw' if o==jaw else None)
 # Mouth interior and dentition are newly modelled for the silent roar.
 extras=[]
 extras.append(bind(sphere('Anatomical dark oral cavity',(0,-2.61,2.28),(.26,.22,.32),mouthmat,detail=20),'head'))
 extras.append(bind(sphere('Muted tongue',(0,-2.72,2.31),(.17,.19,.035),tonguemat,detail=16),'jaw'))
 for side in [-1,1]:
  extras.append(bind(rod('Upper feline canine',(side*.19,-2.80,2.40),(side*.18,-2.82,2.19),.042,toothmat,r2=.005),'head'))
  extras.append(bind(rod('Lower feline canine',(side*.19,-2.75,2.32),(side*.18,-2.79,2.47),.032,toothmat,r2=.004),'jaw'))
 # Bake extra primitive transforms into their rest-space vertices before skinning.
 for o in extras:
  matrix=o.matrix_basis.copy()
  for v in o.data.vertices:v.co=matrix@v.co
  o.matrix_basis=Matrix.Identity(4)
 shadows={};shadow_mats=[material('Soft paw contact '+str(i),(.08,.09,.07),alpha=v) for i,v in enumerate([.15,.07,.012])]
 for label in feet:
  vs=[(0,0,0)];fs=[];ids=[]
  for ring in range(1,4):
   for k in range(24):
    angle=k/24*math.tau;vs.append((math.cos(angle)*.34*ring/3,math.sin(angle)*.47*ring/3,0))
  for k in range(24):fs.append((0,1+k,1+(k+1)%24));ids.append(0)
  for ring in range(2):
   for k in range(24):a=1+ring*24+k;b=1+ring*24+(k+1)%24;fs.append((a,b,b+24,a+24));ids.append(ring+1)
  o=mesh_obj('Soft grounded paw wash '+label,vs,fs,shadow_mats)
  for face,mi in zip(o.data.polygons,ids):face.material_index=mi
  shadows[label]=o
 objects=[o for o in bpy.data.objects if o==volume or o==root or o==arm or o.parent==root]+list(shadows.values())
 return dict(volume=volume,root=root,arm=arm,feet=feet,eyes=eyes,objects=objects,body=body,mouth_mats=[mouthmat,tonguemat,toothmat],shadows=shadows,shadow_mats=shadow_mats)

