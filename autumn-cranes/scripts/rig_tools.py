"""Shared Blender camera-fit and rig checks, using evaluated (posed) geometry."""
import bpy,json
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

def inspect_and_fit(root,fit=True):
    scene=bpy.context.scene;cam=scene.camera
    meshes=[bpy.data.objects[n+' · unified skinned anatomy'] for n in ('Crane A','Crane B')]
    rows=[];max_extent=.39;lenses={}
    for f in range(1,451):
        scene.frame_set(f);bpy.context.view_layer.update();dep=bpy.context.evaluated_depsgraph_get()
        points=[]
        for m in meshes:
            obj=m.evaluated_get(dep)
            points.extend(world_to_camera_view(scene,cam,obj.matrix_world@Vector(p)) for p in obj.bound_box)
        lenses[f]=cam.data.lens
        xs=[p.x for p in points];ys=[p.y for p in points]
        max_extent=max(max_extent,max(abs(v-.5) for v in xs+ys))
        rows.append((f,min(xs),max(xs),min(ys),max(ys)))
    factor=min(1,.39/max_extent) if fit else 1
    if fit:
        for f in range(1,451):cam.data.lens=lenses[f]*factor;cam.data.keyframe_insert(data_path='lens',frame=f)
    bounds=[]
    for f,x0,x1,y0,y1 in rows:bounds.append({'frame':f,'xmin':.5+(x0-.5)*factor,'xmax':.5+(x1-.5)*factor,'ymin':.5+(y0-.5)*factor,'ymax':.5+(y1-.5)*factor})
    scene.frame_set(226);bpy.context.view_layer.update()
    arm=bpy.data.objects['Crane A · armature'];pose=arm.pose.bones['head'];bone=arm.data.bones['head']
    tip=arm.matrix_world@pose.matrix@bone.matrix_local.inverted()@Vector((1.73,0,4.045))
    max_step=0;previous=None
    for f in range(1,451):
        scene.frame_set(f);p=cam.location.copy()
        if previous is not None:max_step=max(max_step,(p-previous).length)
        previous=p
    passed=all(b['xmin']>=.105 and b['xmax']<=.895 and b['ymin']>=.105 and b['ymax']<=.895 for b in bounds)
    passed=passed and len([o for o in bpy.data.objects if o.type=='ARMATURE'])==2 and abs(tip.z-.052)<.12 and max_step<.5
    result={'passed':passed,'evaluatedFrames':450,'craneArmatures':2,'renderMeshes':len(meshes),'cameraFitFactor':factor,'drinkingBeakHeight':tip.z,'waterHeight':.052,'maxCameraStep':max_step,'framingBounds':{'xmin':min(b['xmin'] for b in bounds),'xmax':max(b['xmax'] for b in bounds),'ymin':min(b['ymin'] for b in bounds),'ymax':max(b['ymax'] for b in bounds)},'samples':[bounds[i] for i in (0,89,179,225,269,329,389,449)]}
    (Path(root)/'renders/rig-check.json').write_text(json.dumps(result,indent=2))
    scene.frame_set(180)
    return result
