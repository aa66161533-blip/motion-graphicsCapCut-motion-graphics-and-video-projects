import {spawnSync} from 'node:child_process';
import {readFile,writeFile,stat} from 'node:fs/promises';
import {createHash} from 'node:crypto';
const file='renders/seongyeong_15s_3d.mp4';
function command(args){const r=spawnSync('ffprobe',args,{encoding:'utf8'});if(r.status!==0)throw new Error(r.stderr);return JSON.parse(r.stdout);}
const probe=command(['-v','error','-count_frames','-show_streams','-show_format','-of','json',file]);
const v=probe.streams.find(s=>s.codec_type==='video');
const capture=JSON.parse(await readFile('renders/capture-report.json','utf8'));
const checks={codec:v.codec_name==='h264',dimensions:v.width===1080&&v.height===1920,fps:v.r_frame_rate==='30/1',frames:Number(v.nb_read_frames)===450,duration:Math.abs(Number(probe.format.duration)-15)<.001,noAudio:!probe.streams.some(s=>s.codec_type==='audio'),capture450:capture.capturedFrames===450,noBrowserErrors:capture.errors.length===0,twoKoi:capture.koiCount===2,perspectiveCamera:capture.camera==='PerspectiveCamera'};
const decode=spawnSync('ffmpeg',['-v','error','-i',file,'-f','null','-'],{encoding:'utf8'});checks.decodes=decode.status===0&&!decode.stderr.trim();
const poses=capture.poses;let largestStep=0;for(let i=1;i<poses.length;i++){const step=Math.hypot(...poses[i].position.map((v,j)=>v-poses[i-1].position[j]));largestStep=Math.max(largestStep,step);}checks.continuousCamera=largestStep<.5;
const hash=createHash('sha256').update(await readFile(file)).digest('hex');
const result={passed:Object.values(checks).every(Boolean),checks,largestCameraStep:largestStep,bytes:(await stat(file)).size,sha256:hash,video:{width:v.width,height:v.height,fps:v.r_frame_rate,frames:Number(v.nb_read_frames),duration:Number(probe.format.duration),codec:v.codec_name},captureSeconds:capture.elapsedSeconds};
await writeFile('renders/verification.json',JSON.stringify(result,null,2));await writeFile('renders/SHA256SUMS',hash+'  seongyeong_15s_3d.mp4\n');
console.log(JSON.stringify(result,null,2));if(!result.passed)process.exitCode=1;
