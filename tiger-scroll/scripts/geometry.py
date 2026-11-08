import bpy,math,random
from mathutils import Vector
rng=random.Random(4407)
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
