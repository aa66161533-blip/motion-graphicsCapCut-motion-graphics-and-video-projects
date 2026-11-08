"""Inspect actual baked animation in Blender; no rendering or model changes."""
import bpy,json,math
from pathlib import Path
s=bpy.context.scene;root=Path(bpy.data.filepath).parent;arm=bpy.data.objects['Tiger armature'];volume=bpy.data.objects['Ink-to-volume transformation'];cam=s.camera
eyes=[o for o in bpy.data.objects if o.type=='MESH' and o.data.shape_keys and 'Blink' in o.data.shape_keys.key_blocks]
poses=[]
for f in range(1,361):
 s.frame_set(f);poses.append(list(cam.location))
steps=[math.dist(poses[i],poses[i-1]) for i in range(1,len(poses))]
s.frame_set(77);blink=max(o.data.shape_keys.key_blocks['Blink'].value for o in eyes)
s.frame_set(145);flat=volume.scale.y
s.frame_set(193);full=volume.scale.y
s.frame_set(325);jaw=arm.pose.bones['jaw'].rotation_quaternion.angle
checks={'oneTigerRig':len([o for o in bpy.data.objects if o.type=='ARMATURE'])==1,'oneCamera':len([o for o in bpy.data.objects if o.type=='CAMERA'])==1,'360Frames':s.frame_start==1 and s.frame_end==360,'24fps':s.render.fps==24,'native4K':s.render.resolution_x==2160 and s.render.resolution_y==3840,'blinkAt3Seconds':blink>.95,'flatToVolume':flat<.10 and full>.99,'silentRoarJaw':jaw>.55,'continuousCamera':max(steps)<1}
report={'passed':all(checks.values()),'checks':checks,'bones':len(arm.data.bones),'blinkValue':blink,'flatDepth':flat,'fullDepth':full,'roarJawRadians':jaw,'maxCameraFrameStep':max(steps),'eyeMeshes':len(eyes),'packedImages':sum(bool(im.packed_file) for im in bpy.data.images)}
(root/'renders/rig-check.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2),flush=True)
if not report['passed']:raise RuntimeError('Scene checks failed')
