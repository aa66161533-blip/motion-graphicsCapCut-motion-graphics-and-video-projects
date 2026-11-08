"""Baked motion for the anatomical tiger rig; forward is -Y, Z is up."""
import math
from mathutils import Vector,Matrix
from geometry import key,smooth,bell

def root_y(t):
 if t<=6:return 6.65
 if t<=8:return 6.65-(t-6)*1.825
 if t<=10:return 3-(t-8)*1.25
 if t<=13:return .5-(t-10)*.9
 return -2.2+smooth(13.8,14.958333333,t)*8.85

def heading(t):return -.55*((1-smooth(6,10,t))+smooth(13.8,14.958333333,t))

def world_rot(pose,axis,angle):
 rest=pose.bone.matrix_local.to_3x3();pose.rotation_mode='QUATERNION';pose.rotation_quaternion=(rest.inverted()@Matrix.Rotation(angle,3,axis)@rest).to_quaternion()

def animate_tiger(r,t,f):
 emergence=smooth(6,8,t)*(1-smooth(13.8,14.958333333,t));r['volume'].location=(0,root_y(t),.82);r['volume'].scale=(1,.065+.935*emergence,1)
 r['root'].rotation_euler.z=heading(t);key(r['volume'],'location',f);key(r['volume'],'scale',f);key(r['root'],'rotation_euler',f)
 walk=smooth(6,6.8,t)*(1-smooth(12.65,13.15,t))*(1-smooth(13.8,14.3,t));period=1.65;stance=.65
 offsets={'HL':0,'FL':.25,'HR':.5,'FR':.75}
 for label,(target,rest) in r['feet'].items():
  cycle=(max(0,t-6)/period+offsets[label]);idx=math.floor(cycle);phase=cycle-idx
  def planted(k):
   start=6+(k-offsets[label])*period;end=start+period*stance
   ry=(root_y(max(6,min(13,start)))+root_y(max(6,min(13,end))))*.5
   rot=Matrix.Rotation(heading(max(6,min(13,start))),3,'Z');return Vector((0,ry,.82))+rot@rest
  p0=planted(idx)
  if phase<=stance:world=p0
  else:
   u=(phase-stance)/(1-stance);blend=u*u*(3-2*u);world=p0.lerp(planted(idx+1),blend);world.z+=.25*math.sin(math.pi*u)**1.4
  local=Matrix.Rotation(-heading(t),3,'Z')@(world-Vector((0,root_y(t),.82)))
  target.location=rest.lerp(local,walk*emergence);key(target,'location',f)
 for label,shadow in r.get('shadows',{}).items():
  local=Matrix.Rotation(heading(t),3,'Z')@(r['feet'][label][0].location+Vector((0,-.10,0)));wx=local.x;wy=root_y(t)+local.y*(.065+.935*emergence)
  shadow.location=(wx,wy,.83+.055*math.sin(wx*1.4)*math.sin(wy*.8)+.009);key(shadow,'location',f)
 for mat,alpha in zip(r.get('shadow_mats',[]),[.15,.07,.012]):mat.diffuse_color=(*tuple(mat.diffuse_color)[:3],alpha*emergence);mat.keyframe_insert(data_path='diffuse_color',frame=f)
 for bn in ['pelvis','spine','chest']:
  pose=r['arm'].pose.bones[bn];world_rot(pose,'Y',walk*.014*math.sin((t-6)/period*math.tau));key(pose,'rotation_quaternion',f)
 turn=bell(3,3.8,5.2,6,t)*.20;roar=bell(13,13.5,14.05,14.7,t)
 neck=r['arm'].pose.bones['neck'];world_rot(neck,'X',-.12*roar);key(neck,'rotation_quaternion',f)
 head=r['arm'].pose.bones['head'];rest=head.bone.matrix_local.to_3x3();head.rotation_mode='QUATERNION';rot=Matrix.Rotation(turn,3,'Z')@Matrix.Rotation(-.13*roar,3,'X');head.rotation_quaternion=(rest.inverted()@rot@rest).to_quaternion();key(head,'rotation_quaternion',f)
 for mat in r.get('mouth_mats',[]):mat.diffuse_color=(*tuple(mat.diffuse_color)[:3],roar);mat.keyframe_insert(data_path='diffuse_color',frame=f)
 jaw=r['arm'].pose.bones['jaw'];world_rot(jaw,'X',.65*roar);key(jaw,'rotation_quaternion',f)
 blink=bell(3.02,3.14,3.20,3.33,t)
 for o,shape in r['eyes']:shape.value=max(blink,roar*.12);key(shape,'value',f)
 for i in range(6):
  pose=r['arm'].pose.bones['tail'+str(i)];world_rot(pose,'Z',emergence*.045*math.sin(t*1.1-i*.6));key(pose,'rotation_quaternion',f)
