"""Blender 4.3+ scene generator. No downloaded assets, no persistent Python handlers.

All armatures, IK targets, wind, smoke, water and camera animation are baked into
the .blend file as ordinary F-curves. Open the saved project and press Play.
"""
import bpy
import math
import random
import argparse
import sys
import json
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion, Euler

args=argparse.ArgumentParser()
args.add_argument('--out',default=str(Path(__file__).resolve().parents[1]))
args.add_argument('--engine',choices=['workbench','eevee'],default='workbench')
args.add_argument('--resolution',type=int,choices=[1080,2160],default=1080)
opts=args.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
ROOT=Path(opts.out).resolve();(ROOT/'renders').mkdir(parents=True,exist_ok=True)
rng=random.Random(11082027)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.render.engine='BLENDER_WORKBENCH' if opts.engine=='workbench' else 'BLENDER_EEVEE_NEXT'
scene.render.resolution_x=opts.resolution;scene.render.resolution_y=opts.resolution*16//9
scene.render.resolution_percentage=100
scene.render.fps=30;scene.render.fps_base=1
scene.frame_start=1;scene.frame_end=450
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
scene.render.image_settings.color_depth='8';scene.render.image_settings.compression=15
scene.render.film_transparent=False
scene.render.threads_mode='FIXED';scene.render.threads=4
scene.render.filepath='//renders/frames/frame_'
scene.view_settings.view_transform='Standard';scene.view_settings.look='None'
scene.view_settings.exposure=0;scene.view_settings.gamma=1
scene.display.render_aa='5'
sh=scene.display.shading;sh.light='STUDIO';sh.studiolight_rotate_z=.35
sh.color_type='MATERIAL';sh.background_type='WORLD';sh.show_shadows=False
sh.show_cavity=True;sh.cavity_type='SCREEN';sh.curvature_ridge_factor=.8;sh.curvature_valley_factor=.45
sh.cavity_ridge_factor=.7;sh.cavity_valley_factor=.6;sh.show_specular_highlight=False
sh.show_object_outline=False;sh.show_xray=False
scene.eevee.taa_render_samples=16
world=bpy.data.worlds.new('Ivory Hanji World');world.color=(.79,.75,.64);scene.world=world
world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.79,.75,.64,1)
world.node_tree.nodes['Background'].inputs[1].default_value=.8

def material(name,color,rough=1,alpha=1):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,alpha);m.use_nodes=True
    n=m.node_tree.nodes;links=m.node_tree.links;p=n.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough
    p.inputs['Alpha'].default_value=alpha
    noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=16;noise.inputs['Detail'].default_value=2
    ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.13;ramp.color_ramp.elements[1].position=.85
    ramp.color_ramp.elements[0].color=(*(v*.78 for v in color),1)
    ramp.color_ramp.elements[1].color=(*(min(1,v*1.10) for v in color),1)
    links.new(noise.outputs['Fac'],ramp.inputs[0]);links.new(ramp.outputs['Color'],p.inputs['Base Color'])
    if alpha<1:m.surface_render_method='DITHERED'
    return m

ivory=material('Crane · warm white plumage',(.89,.87,.78))
feather_grey=material('Feather quill subtle ink',(.58,.61,.56))
charcoal=material('Feather · charcoal ink',(.055,.067,.058))
red=material('Crown · restrained vermilion',(.55,.085,.045))
eye=material('Eyes · ink black',(.016,.022,.019))
legmat=material('Legs · warm ink grey',(.23,.25,.21))
ground_mats=[material('Hanji earth '+str(i),(.64+i*.022,.60+i*.024,.44+i*.026)) for i in range(7)]
rock_mats=[material('Wash rock '+str(i),(.24+i*.035,.28+i*.032,.24+i*.029)) for i in range(10)]
mount_mats=[[material(f'Ink mountain {row}.{i}',(.30+row*.052+i*.016,.34+row*.05+i*.016,.30+row*.045+i*.015)) for i in range(6)] for row in range(4)]
wood=material('Brush-dark wood',(.18,.13,.085))
bark=material('Autumn bark',(.24,.18,.12))
wall=material('Earthen wall',(.71,.64,.45))
straw=[material('Thatch '+str(i),(.42+i*.035,.32+i*.03,.17+i*.025)) for i in range(5)]
maples=[material('Maple pigment '+str(i),c) for i,c in enumerate([(.50,.07,.025),(.66,.15,.035),(.76,.25,.055),(.60,.12,.025),(.72,.32,.08),(.43,.08,.025)])]
ginkgos=[material('Ginkgo pigment '+str(i),c) for i,c in enumerate([(.82,.61,.12),(.88,.69,.18),(.69,.48,.07),(.90,.74,.27),(.72,.58,.14)])]
water_mats=[material('Clear creek '+str(i),(.45+i*.017,.55+i*.014,.49+i*.012),.25) for i in range(6)]
water_line=material('Water line pale ink',(.66,.73,.65),alpha=.50)
smoke_mat=material('Smoke wash',(.69,.68,.61),alpha=.10)
mist_mat=material('Valley mist',(.83,.82,.74),alpha=.055)

def mesh_obj(name,verts,faces,mat,parent=None):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
    o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o)
    if isinstance(mat,list):
        for m in mat:me.materials.append(m)
    elif mat:me.materials.append(mat)
    if parent:o.parent=parent
    return o

def empty(name,location=(0,0,0),parent=None):
    o=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(o);o.location=location
    if parent:o.parent=parent
    return o

def sphere(name,location,scale,mat,parent=None,detail=16):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=detail,ring_count=max(6,detail//2),location=location)
    o=bpy.context.object;o.name=name;o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(mat)
    for p in o.data.polygons:p.use_smooth=True
    if parent:o.parent=parent
    return o

def ico(name,location,scale,mat,parent=None):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1,location=location)
    o=bpy.context.object;o.name=name;o.scale=scale;o.rotation_euler=(rng.random(),rng.random(),rng.random())
    o.data.materials.append(mat)
    if parent:o.parent=parent
    return o

def box(name,location,scale,mat,parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1,location=location)
    o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(mat)
    if parent:o.parent=parent
    return o

def tube(name,points,radius,mat,parent=None,radii=None,res=2):
    cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=3
    cu.bevel_depth=radius;cu.bevel_resolution=res
    sp=cu.splines.new('BEZIER');sp.bezier_points.add(len(points)-1)
    for i,(p,co) in enumerate(zip(sp.bezier_points,points)):
        p.co=co;p.handle_left_type=p.handle_right_type='AUTO';p.radius=radii[i] if radii else 1
    o=bpy.data.objects.new(name,cu);bpy.context.collection.objects.link(o);cu.materials.append(mat)
    if parent:o.parent=parent
    return o

def rod(name,a,b,r,mat,parent=None,r2=None):
    a,b=Vector(a),Vector(b);d=b-a
    bpy.ops.mesh.primitive_cone_add(vertices=10,radius1=r,radius2=r if r2 is None else r2,depth=d.length,location=(a+b)/2)
    o=bpy.context.object;o.name=name;o.rotation_euler=d.to_track_quat('Z','Y').to_euler();o.data.materials.append(mat)
    if parent:o.parent=parent
    return o

def key(o,prop,frame):o.keyframe_insert(data_path=prop,frame=frame)
def smooth(a,b,x):
    u=max(0,min(1,(x-a)/(b-a)));return u*u*(3-2*u)
def bell(a,b,c,d,t):return smooth(a,b,t)*(1-smooth(c,d,t))
def creek_y(x):return math.sin(x*.16)*1.15+x*.055

# True terrain, with front/middle/back depth and ink-toned facets.
verts=[];faces=[];NX,NY=60,45
for j in range(NY+1):
    y=-26+j*2
    for i in range(NX+1):
        x=-60+i*2;z=-.15+.12*math.sin(x*.21)*math.cos(y*.18)
        if y>9:z+=(y-9)*.012
        verts.append((x,y,z))
for j in range(NY):
    for i in range(NX):a=j*(NX+1)+i;faces.append((a,a+1,a+NX+2,a+NX+1))
earth=mesh_obj('Hand-painted earth',verts,faces,ground_mats)
for p in earth.data.polygons:p.material_index=rng.randrange(2,7);p.use_smooth=True

def mountain(name,x,y,h,r,row):
    vertices=[];faces=[];S,R=48,20
    for j in range(R+1):
        u=j/R
        for i in range(S+1):
            a=2*math.pi*i/S;rr=r*u*(1+.10*math.sin(a*5)+.06*math.cos(a*9))
            z=h*(1-u)**.66*(1+.075*math.sin(a*7+u*20))
            vertices.append((x+rr*math.cos(a),y+rr*math.sin(a)*.76,z))
    for j in range(R):
        for i in range(S):
            a=j*(S+1)+i;b=a+S+1;faces.append((a,b,b+1,a+1))
    o=mesh_obj(name,vertices,faces,mount_mats[row])
    for p in o.data.polygons:p.material_index=min(5,max(0,int(rng.gauss(2.6,1.3))));p.use_smooth=True
    # Sparse, fine ink fissures on the forward slopes.
    for k in range(10):
        a=math.pi*1.05+k/9*math.pi*.88;points=[]
        for j in range(8):
            u=.15+j*.095;rr=r*u*(1+.10*math.sin(a*5)+.06*math.cos(a*9))
            z=h*(1-u)**.66*(1+.075*math.sin(a*7+u*20))+.025
            points.append((x+rr*math.cos(a),y+rr*math.sin(a)*.76-.045,z))
        tube(name+' · dry brush ridge',points,.012,mount_mats[row][0],res=0)
    return o

for n,(x,y,h,r,row) in enumerate([(-21,23,16,11,0),(19,27,18,12,0),(-8,41,22,13,1),(32,44,25,15,1),(-29,51,24,15,2),(10,60,28,17,2),(-11,76,29,18,3),(34,79,30,20,3)]):
    mountain(f'Ink ridge {n}',x,y,h,r,row)

# Meandering shallow stream: connected mesh, real ripples and reflective-like lines.
vertices=[];faces=[]
for i in range(151):
    x=-38+i*.5;y=creek_y(x);w=2.7+.35*math.sin(x*.29)
    vertices.extend([(x,y-w,.052),(x,y+w,.052)])
for i in range(150):faces.append((i*2,i*2+1,i*2+3,i*2+2))
stream=mesh_obj('Clear continuous creek',vertices,faces,water_mats)
for p in stream.data.polygons:p.material_index=2+int(2*math.sin(p.index*.1))
water_strokes=[]
for i in range(46):
    x=rng.uniform(-19,20);y=creek_y(x)+rng.uniform(-2.2,2.2)
    o=tube('Creek horizontal brush ripple',[(x-.5,y,.074),(x,y+.04,.076),(x+.7,y,.074)],.012,water_line,res=0)
    water_strokes.append((o,x,y,rng.uniform(0,6)))
for i in range(92):
    x=rng.uniform(-25,25);sign=rng.choice([-1,1]);y=creek_y(x)+sign*(2.8+rng.random()*.9)
    ico('Creek bank stone',(x,y,.10),(rng.uniform(.15,.50),rng.uniform(.15,.43),rng.uniform(.10,.30)),rng.choice(rock_mats[4:]))

# A traditional thatched cottage, wooden lattice and smoke chimney.
hut=empty('Traditional thatched cottage',(-8.2,13.5,.20))
box('Mud-plaster cottage',(0,0,1.2),(5.1,3.5,2.4),wall,hut)
box('Stone foundation',(0,0,.12),(5.6,4,.24),rock_mats[5],hut)
roof_verts=[(-3,-2.2,2.4),(3,-2.2,2.4),(3,2.2,2.4),(-3,2.2,2.4),(-1,0,4),(1,0,4)]
roof=mesh_obj('Hipped straw thatch',roof_verts,[(0,1,5,4),(1,2,5),(2,3,4,5),(3,0,4)],straw,hut)
for p in roof.data.polygons:p.material_index=p.index%5
for j in range(35):
    x=-2.8+j*.16
    for sign in [-1,1]:
        z=3.95-.25*max(0,abs(x)-1)
        tube('Thatched roof fiber',[(x,0,z),(x+.02,sign*1.2,3.10),(x+.07,sign*2.20,2.43)],.025,rng.choice(straw),hut,radii=[1.0,1.3,.6],res=0)
for x in [-1.6,1.6]:
    box('Wooden window',(x,-1.77,1.35),(1.05,.06,1.05),wood,hut)
    for k in range(4):box('Window lattice',(x-.4+k*.27,-1.82,1.35),(.035,.035,.90),straw[3],hut)
    for k in range(3):box('Window crossbar',(x,-1.84,1.05+k*.3),(.92,.04,.03),straw[3],hut)
box('Timber front door',(0,-1.78,.95),(.85,.09,1.9),wood,hut)
chimney=box('Earthen chimney',(2.75,.75,1.7),(.65,.65,3.4),rock_mats[3],hut)
smoke=[]
for i in range(12):
    o=sphere('Chimney smoke wash',(-5.45,14.25,3.9),(.5,.5,.6),smoke_mat,detail=12)
    smoke.append((o,i/12))

# Actual 3D maple and ginkgo leaves, gathered into independently moving boughs.
def leaf_shape(kind):
    if kind=='maple':
        return [(math.cos(i*math.pi/8)*(1 if i%2==0 else .43),math.sin(i*math.pi/8)*(1 if i%2==0 else .43),0) for i in range(16)]
    return [(0,-.45,0)]+[(math.sin(-1.18+i/12*2.36),math.cos(-1.18+i/12*2.36)*.9,0) for i in range(13)]

branches=[]
def tree(name,pos,height,kind):
    root=empty(name,pos);pal=maples if kind=='maple' else ginkgos
    tube(name+' · ink trunk',[(0,0,0),(.18,0,height*.35),(-.12,.05,height*.64),(.45,.15,height*.95)],.22,bark,root,radii=[1.5,1,.65,.15])
    for j in range(9):
        a=j*2.399;z=height*(.42+j*.055);r=height*(.40-j*.024)
        pivot=empty(name+' · branch joint',(.10,0,z),root)
        end=Vector((math.cos(a)*r,math.sin(a)*r,height*.12))
        tube(name+' · living branch',[(0,0,0),end*.58,end],.075,bark,pivot,radii=[1.2,.7,.12])
        vs=[];fs=[];ids=[];shape=leaf_shape(kind)
        for k in range(43):
            c=end+Vector((rng.gauss(0,r*.38),rng.gauss(0,r*.32),rng.gauss(0,height*.08)))
            scale=rng.uniform(.16,.32) if kind=='maple' else rng.uniform(.18,.34)
            rot=Euler((rng.uniform(.1,2.9),rng.uniform(-.8,.8),rng.uniform(0,6.28))).to_matrix()
            start=len(vs);vs.append(tuple(c));vs.extend(tuple(c+rot@Vector(p)*scale) for p in shape)
            for q in range(len(shape)):fs.append((start,start+1+q,start+1+(q+1)%len(shape)));ids.append(rng.randrange(len(pal)))
        o=mesh_obj(name+' · pigmented leaves',vs,fs,pal,pivot)
        for p,mi in zip(o.data.polygons,ids):p.material_index=mi
        branches.append((pivot,rng.uniform(0,6.28),kind))
    return root

tree('Foreground vermilion maple',(-9,-.5,0),8.2,'maple')
tree('Golden ginkgo',(6.7,8,.1),8.6,'ginkgo')
tree('Cottage autumn maple',(-12,15,.2),7.2,'maple')
tree('Distant ginkgo',(14,18,.2),7.6,'ginkgo')
tree('Far red maple',(-17,23,.2),7.0,'maple')
tree('Near frame maple',(-12,-9,.1),9,'maple')
falling=[]
for i in range(32):
    shape=leaf_shape('maple');o=mesh_obj('Drifting red maple leaf',[(0,0,0)]+shape,[(0,1+j,1+(j+1)%len(shape)) for j in range(len(shape))],rng.choice(maples))
    o.scale=(.16,.16,.16);falling.append((o,rng.uniform(-4,12),rng.uniform(-7,9),rng.uniform(-3,6),rng.uniform(0,6.28)))
for i in range(70):
    x=rng.uniform(-18,20);y=rng.uniform(-8,18)
    if abs(y-creek_y(x))<2.8:continue
    shape=leaf_shape(rng.choice(['maple','ginkgo']));o=mesh_obj('Fallen autumn pigment',[(0,0,.02)]+[(a*.15,b*.15,.025) for a,b,c in shape],[(0,1+j,1+(j+1)%len(shape)) for j in range(len(shape))],rng.choice(maples+ginkgos));o.location=(x,y,0);o.rotation_euler.z=rng.random()*6.28

mist=[]
for i in range(10):
    x=rng.uniform(-25,25);y=rng.uniform(15,50);z=rng.uniform(2,5)
    o=sphere('Mountain mist wash',(x,y,z),(8,2.3,.7),mist_mat,detail=12);mist.append((o,Vector((x,y,z)),rng.uniform(0,6.28)))

# Shared crane anatomy. Rigid feathers and continuous skinned neck share one rig.
def crane(name,position):
    root=empty(name+' · root',position);root['species']='red-crowned crane';root['constant_scale']=True
    data=bpy.data.armatures.new(name+' · anatomical skeleton');arm=bpy.data.objects.new(name+' · armature',data);bpy.context.collection.objects.link(arm);arm.parent=root
    bpy.context.view_layer.objects.active=arm;arm.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
    specs={
        'body':((0,0,1.8),(.2,0,2.4),None),
        'neck0':((.40,0,2.10),(.55,0,2.80),'body'),
        'neck1':((.55,0,2.80),(.45,0,3.50),'neck0'),
        'neck2':((.45,0,3.50),(.85,0,4.05),'neck1'),
        'head':((.85,0,4.05),(1.30,0,4.05),'neck2')}
    for side,label in [(-1,'R'),(1,'L')]:
        specs['wing_'+label]=((-.02,side*.28,2.12),(-.78,side*.43,2.10),'body')
        specs['wrist_'+label]=((-.78,side*.43,2.10),(-1.32,side*.47,1.90),'wing_'+label)
        specs['thigh_'+label]=((.04,side*.17,1.92),(-.23,side*.17,1.05),'body')
        specs['shin_'+label]=((-.23,side*.17,1.05),(.05,side*.17,.13),'thigh_'+label)
        specs['foot_'+label]=((.05,side*.17,.13),(.43,side*.17,.10),'shin_'+label)
    for bn,(a,b,parent) in specs.items():
        bone=data.edit_bones.new(bn);bone.head=a;bone.tail=b
        if parent:bone.parent=data.edit_bones[parent]
    bpy.ops.object.mode_set(mode='OBJECT');arm.select_set(False)
    targets={}
    for label in ['R','L']:
        side=-1 if label=='R' else 1
        target=empty(name+' · '+label+' foot IK',(.05,side*.17,.13),root)
        pole=empty(name+' · '+label+' knee pole',(-3,side*.17,1),root)
        con=arm.pose.bones['shin_'+label].constraints.new('IK');con.target=target;con.pole_target=pole;con.chain_count=2;con.use_stretch=False
        targets[label]=target
    nt=empty(name+' · neck IK',(.85,0,4.05),root)
    pole=empty(name+' · neck plane',(3,0,2.5),root)
    con=arm.pose.bones['neck2'].constraints.new('IK');con.target=nt;con.chain_count=3;con.use_stretch=False;con.pole_target=pole
    aim=empty(name+' · beak aim',(1.6,0,4.0),root)
    con=arm.pose.bones['head'].constraints.new('DAMPED_TRACK');con.target=aim;con.track_axis='TRACK_Y'
    parts=[]
    def skin(o,bone):
        # All vertex coordinates are baked in rig rest space before attaching.
        bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
        if o.type=='CURVE':bpy.ops.object.convert(target='MESH');o=bpy.context.object
        bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
        group=o.vertex_groups.new(name=bone);group.add(list(range(len(o.data.vertices))),1,'REPLACE')
        mod=o.modifiers.new('Anatomical deformation','ARMATURE');mod.object=arm;o.parent=root;parts.append(o);return o
    skin(sphere(name+' body',(0,0,2.05),(.82,.33,.45),ivory),'body')
    skin(sphere(name+' shoulder',(.38,0,2.15),(.42,.29,.36),ivory),'body')
    # Continuous neck rings, weighted smoothly across adjacent cervical bones.
    centers=[Vector((.40,0,2.10)),Vector((.55,0,2.80)),Vector((.45,0,3.50)),Vector((.85,0,4.05))]
    vs=[];fs=[];weights=[]
    for j in range(25):
        q=j/24*3;seg=min(2,int(q));u=q-seg;c=centers[seg].lerp(centers[seg+1],u);r=.13-j/24*.045
        for k in range(14):
            a=k/14*math.pi*2;vs.append(tuple(c+Vector((math.cos(a)*r,math.sin(a)*r,0))));weights.append((seg,u))
    for j in range(24):
        for k in range(14):a=j*14+k;b=j*14+(k+1)%14;fs.append((a,b,b+14,a+14))
    neck=mesh_obj(name+' continuous neck',vs,fs,[ivory,charcoal],root)
    for p in neck.data.polygons:p.use_smooth=True;p.material_index=1 if (p.index%14 in (7,8,9,10)) else 0
    groups=[neck.vertex_groups.new(name='neck'+str(i)) for i in range(3)]
    for j,(seg,u) in enumerate(weights):
        q=seg+u;ws=[max(0,1-abs(q-(k+.5))) for k in range(3)];total=sum(ws)
        for k,w in enumerate(ws):
            if w>0:groups[k].add([j],w/total,'REPLACE')
    mod=neck.modifiers.new('Continuous cervical skin','ARMATURE');mod.object=arm;parts.append(neck)
    skin(sphere(name+' head',(.89,0,4.06),(.24,.145,.155),ivory),'head')
    skin(sphere(name+' red crown',(.87,0,4.19),(.155,.122,.042),red),'head')
    for side in [-1,1]:
        skin(sphere(name+' black cheek',(.84,side*.133,4.035),(.16,.027,.088),charcoal),'head')
        skin(sphere(name+' dark eye',(1.005,side*.147,4.105),(.027,.016,.026),eye,detail=12),'head')
    skin(rod(name+' tapered beak',(1.08,0,4.06),(1.73,0,4.045),.061,legmat,r2=.006),'head')
    for side,label in [(-1,'R'),(1,'L')]:
        skin(rod(name+' upper leg',(.04,side*.17,1.92),(-.23,side*.17,1.05),.043,legmat,r2=.031),'thigh_'+label)
        skin(sphere(name+' hock',(-.23,side*.17,1.05),(.059,.05,.061),legmat,detail=12),'shin_'+label)
        skin(rod(name+' lower leg',(-.23,side*.17,1.05),(.05,side*.17,.13),.027,legmat,r2=.021),'shin_'+label)
        for d in [-1,0,1]:
            skin(tube(name+' long toe',[(.05,side*.17,.13),(.24,side*.17+d*.06,.08),(.48,side*.17+d*.105,.075)],.016,legmat,res=1),'foot_'+label)
        skin(tube(name+' hind toe',[(.05,side*.17,.13),(-.15,side*.17,.075)],.014,legmat,res=1),'foot_'+label)
        # Overlapping ivory coverts and black primary feathers, each a 3D ellipsoid.
        for row in range(3):
            for k in range(8):
                x=-.15-k*.085-row*.03;y=side*(.35+row*.045);z=2.25-row*.10
                o=sphere(name+' layered covert',(x,y,z),(.25,.055,.085),ivory,detail=12);o.rotation_euler.y=-.12-k*.02;skin(o,'wing_'+label)
        for k in range(10):
            x=-.78-k*.064;y=side*(.43+k*.016);z=2.05-k*.034
            o=sphere(name+' black primary',(x,y,z),(.33+k*.006,.038,.063),charcoal,detail=12);o.rotation_euler.y=-.12-k*.02;skin(o,'wrist_'+label)
        for k in range(4):
            o=sphere(name+' white flight feather',(-.73-k*.08,side*.49,2.14-k*.018),(.32,.045,.068),ivory,detail=12);skin(o,'wrist_'+label)
    for k in range(5):
        o=sphere(name+' trailing tail',(-.73-k*.065,(k-2)*.075,1.91),(.36,.045,.08),charcoal,detail=12);skin(o,'body')
    # One skinned render mesh per crane; groups and material slots remain intact.
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts:o.select_set(True)
    bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();bird=bpy.context.object;bird.name=name+' · unified skinned anatomy'
    return dict(root=root,arm=arm,neck=nt,aim=aim,feet=targets,mesh=bird)

birds=[crane('Crane A',(-2.1,-.65,.03)),crane('Crane B',(1.0,1.05,.03))]
assert len(birds)==2

# Ripples centred near the first bird's drinking point, plus quiet stream rings.
rings=[]
for i in range(5):
    bpy.ops.mesh.primitive_torus_add(major_radius=1,minor_radius=.009,major_segments=72,minor_segments=4,location=(.5,-.65,.082))
    o=bpy.context.object;o.name='Drinking concentric ripple';o.data.materials.append(water_line);rings.append((o,i*.52))

# Camera and an optional Eevee lighting setup; Workbench uses its studio light.
bpy.ops.object.camera_add(location=(15,-29,16));camera=bpy.context.object;camera.name='Single continuous camera';scene.camera=camera
camera.data.lens=65;camera.data.clip_end=260;camera.data.dof.use_dof=False
for kind,loc,energy,size in [('AREA',(-8,-12,20),1800,18),('AREA',(13,4,14),1000,14)]:
    bpy.ops.object.light_add(type=kind,location=loc);light=bpy.context.object;light.data.energy=energy;light.data.shape='DISK';light.data.size=size;light.rotation_euler=(Vector((0,0,1))-light.location).to_track_quat('-Z','Y').to_euler()

times=[0,3,6,10,13,15]
positions=[Vector(v) for v in [(15,-29,16),(11,-19,10),(8,-19,9),(7,-18,8),(9,-22,11),(15,-30,17)]]
looks=[Vector(v) for v in [(0,3,2.5),(.2,1,2.4),(1.4,.2,2.8),(1.7,.2,2.8),(1.8,3,3),(1,4,2.9)]]
def path(points,t):
    i=0
    while i<len(times)-2 and t>times[i+1]:i+=1
    dt=times[i+1]-times[i];u=max(0,min(1,(t-times[i])/dt));a,b=points[i],points[i+1]
    ip=max(0,i-1);inn=min(len(points)-1,i+2)
    va=(b-points[ip])*(dt/(times[i+1]-times[ip]));vb=(points[inn]-a)*(dt/(times[inn]-times[i]))
    if i==0:va*=.3
    if i==len(points)-2:vb*=0
    return a*(2*u**3-3*u*u+1)+va*(u**3-2*u*u+u)+b*(-2*u**3+3*u*u)+vb*(u**3-u*u)

def world_rotation(bone,axis,angle):
    basis=bone.bone.matrix_local.to_3x3()
    bone.rotation_mode='QUATERNION';bone.rotation_quaternion=(basis.inverted()@Matrix.Rotation(angle,3,axis)@basis).to_quaternion()

# Tree canopies share a continuous wind shape while twig joints remain animated.
canopy_winds=[]
for tree_root in [o for o in bpy.data.objects if o.type=='EMPTY' and 'branch joint' not in o.name and o.name in ['Foreground vermilion maple','Golden ginkgo','Cottage autumn maple','Distant ginkgo','Far red maple','Near frame maple']]:
    leaves=[o for o in bpy.data.objects if o.type=='MESH' and 'pigmented leaves' in o.name and o.parent and o.parent.parent==tree_root]
    if not leaves:continue
    bpy.context.view_layer.update();bpy.ops.object.select_all(action='DESELECT')
    for o in leaves:
        m=o.matrix_world.copy();o.parent=None;o.matrix_world=m;o.select_set(True)
    bpy.context.view_layer.objects.active=leaves[0];bpy.ops.object.join();o=bpy.context.object;o.name=tree_root.name+' · unified wind canopy'
    m=o.matrix_world.copy();o.parent=tree_root;o.matrix_world=m
    o.shape_key_add(name='Basis');wind=o.shape_key_add(name='Autumn breeze')
    for v in wind.data:
        z=v.co.z;v.co.x+=.19*math.sin(z*.35+.5);v.co.y+=.10*math.sin(v.co.x*.55)
    canopy_winds.append((wind,rng.random()*6.28))

# Bake every frame. No external handler is needed when opening the .blend file.
audit=[]
for frame in range(1,451):
    t=(frame-1)/30
    scene.frame_set(frame)
    for idx,b in enumerate(birds):
        # Slow root travel pauses during the drinking and stretching performance.
        travel=.19*min(t,6)+.19*max(0,t-10)
        b['root'].location=(-2.1+idx*3.1+travel, -.65+idx*1.7+math.sin(t*.5+idx)*.035,.03)
        key(b['root'],'location',frame)
        walking=1-bell(5.5,6.1,9.6,10.1,t)
        phase=t*2*math.pi/1.8+idx*.8
        for label,offset in [('R',0),('L',math.pi)]:
            s=-1 if label=='R' else 1;p=phase+offset
            cycle=(p/(2*math.pi))%1
            if cycle<.65:offset=.11115*(1-2*cycle/.65);lift=0
            else:
                u=(cycle-.65)/.35;offset=-.11115*math.cos(math.pi*u);lift=.18*math.sin(math.pi*u)**1.5
            foot=b['feet'][label];foot.location=(.05+walking*offset,s*.17,.13+walking*lift)
            key(foot,'location',frame)
        drink=bell(6.0,7.3,8.5,9.8,t) if idx==0 else 0
        idle=.025*math.sin(t*1.6+idx)
        b['neck'].location=Vector((.85,0,4.05+idle)).lerp(Vector((1.80,0,.53)),drink)
        b['aim'].location=b['neck'].location+Vector((.85,0,-.04-.55*drink))
        key(b['neck'],'location',frame);key(b['aim'],'location',frame)
        world_rotation(b['arm'].pose.bones['body'],'Y',.11*drink+walking*.012*math.sin(phase*2))
        key(b['arm'].pose.bones['body'],'rotation_quaternion',frame)
        spread=bell(6.25,7.8,8.5,9.85,t) if idx==1 else 0
        for side,label in [(-1,'R'),(1,'L')]:
            upper=b['arm'].pose.bones['wing_'+label]
            rest=upper.bone.matrix_local.to_3x3()
            rotation=Matrix.Rotation(side*1.20*spread,3,'X')@Matrix.Rotation(-side*1.15*spread,3,'Z')
            upper.rotation_mode='QUATERNION';upper.rotation_quaternion=(rest.inverted()@rotation@rest).to_quaternion()
            key(upper,'rotation_quaternion',frame)
            wrist=b['arm'].pose.bones['wrist_'+label];world_rotation(wrist,'Z',-side*.36*spread);key(wrist,'rotation_quaternion',frame)
    for wind,phase_offset in canopy_winds:
        wind.value=.5+.5*math.sin(t*.8+phase_offset);key(wind,'value',frame)
    for o,p,kind in branches:
        o.rotation_euler=(.022*math.sin(t*.83+p),.018*math.sin(t*.65+p),.035*math.sin(t*.68+p));key(o,'rotation_euler',frame)
    for o,start,x,y,p in falling:
        age=t-start;z=max(.04,7-age*.65)
        o.location=(x+.24*age+math.sin(age*1.0+p)*.45,y+math.sin(age*.65+p)*.5,z)
        o.rotation_euler=(age*1.15+p,math.sin(age+p)*.7,age*.6+p)
        key(o,'location',frame);key(o,'rotation_euler',frame)
    for o,p in smoke:
        u=(t*.10+p)%1;size=(.36+u*.83)*smooth(0,.10,u)*(1-smooth(.75,1,u))
        o.location=(-5.45+u*1.1+math.sin(t*.32+p*6)*.12,14.25+u*.45,3.75+u*4.5)
        o.scale=(size,size*.9,size*1.3);key(o,'location',frame);key(o,'scale',frame)
    for o,p,phase in mist:
        o.location=p+Vector((math.sin(t*.17+phase)*.8,math.cos(t*.12+phase)*.2,math.sin(t*.15+phase)*.10));key(o,'location',frame)
    for o,x,y,phase in water_strokes:
        o.location=(math.sin(t*.8+phase)*.05,math.sin(t*.7+phase)*.07,math.sin(t*1.3+phase)*.003);key(o,'location',frame)
    for o,p in rings:
        age=(t+p)%2.6;radius=.07+age*.42;active=bell(6.2,6.8,9.1,9.9,t)
        o.location=(birds[0]['root'].location.x+2.35,-.65,.087)
        o.scale=(radius,radius,.5);o.hide_render=active<.005
        key(o,'location',frame);key(o,'scale',frame);key(o,'hide_render',frame)
    camera.location=path(positions,t);target=path(looks,t);camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=55+smooth(13,15,t)*12
    key(camera,'location',frame);key(camera,'rotation_euler',frame);key(camera.data,'lens',frame)
    if frame in (1,91,181,226,301,391,450):audit.append({'frame':frame,'seconds':t,'camera':list(camera.location),'craneRoots':[list(b['root'].location) for b in birds],'drink':bell(6,7.3,8.5,9.8,t),'wingSpread':bell(6.25,7.8,8.5,9.85,t)})

for action in bpy.data.actions:
    # Frame-by-frame sampling uses linear keys; no Bezier overshoot or IK target jumps.
    for fc in action.fcurves:
        for kp in fc.keyframe_points:
            if fc.data_path!='hide_render':kp.interpolation='LINEAR'
# Static opaque geometry batching preserves depth and material slots.
static=[]
for o in list(bpy.data.objects):
    if o.type not in {'MESH','CURVE'} or o.modifiers:continue
    if o.type=='MESH' and o.data.shape_keys:continue
    p=o;moving=False
    while p:
        if p.animation_data:moving=True;break
        p=p.parent
    if not moving:static.append(o)
bpy.ops.object.select_all(action='DESELECT')
for o in static:o.select_set(True)
if static:
    bpy.context.view_layer.objects.active=static[0];bpy.ops.object.convert(target='MESH')
    bpy.ops.object.join();bpy.context.object.name='Batched hand-painted static landscape'

sys.path.insert(0,str(Path(__file__).resolve().parent))
from rig_tools import inspect_and_fit
rig_result=inspect_and_fit(ROOT,fit=True)
print('RIG_CHECK',json.dumps(rig_result),flush=True)
if not rig_result['passed']:raise RuntimeError('Rig/framing verification failed; see renders/rig-check.json')
scene.frame_set(180)
scene['project_title']='가을 산수화, 학 두 마리의 산책'
scene['crane_count']=2;scene['duration_seconds']=15
scene['renderer_note']='CPU-compatible Workbench ink palette; optional procedural Eevee material nodes included.'
scene['animation_note']='All motion baked into ordinary object/pose F-curves; no Python handlers required.'
for area in bpy.context.screen.areas if bpy.context.screen else []:
    if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'autumn_cranes.blend'),compress=True)
report={'blender':bpy.app.version_string,'engine':scene.render.engine,'width':scene.render.resolution_x,'height':scene.render.resolution_y,'fps':30,'frameStart':1,'frameEnd':450,'craneCount':2,'armatures':[b['arm'].name for b in birds],'bonesPerCrane':len(birds[0]['arm'].data.bones),'scale':[list(b['root'].scale) for b in birds],'externalAssets':False,'bakedAnimation':True,'audit':audit}
(ROOT/'renders/scene-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print('AUTUMN_SCENE_SAVED',json.dumps(report,ensure_ascii=False),flush=True)
