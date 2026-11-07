import { chromium } from 'playwright';
import { createServer } from 'vite';
import { mkdir, writeFile, readFile } from 'node:fs/promises';
import { spawnSync } from 'node:child_process';
import path from 'node:path';
import {existsSync} from 'node:fs';

const sample=process.argv.includes('--sample');
const dir=path.resolve('renders');await mkdir(dir,{recursive:true});
const server=await createServer({server:{host:'127.0.0.1',port:5173,strictPort:false}});await server.listen();
const url=server.resolvedUrls.local[0]+'?capture=1';
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||(existsSync('/usr/bin/chromium')?'/usr/bin/chromium':undefined),headless:true,args:['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-background-timer-throttling','--disable-renderer-backgrounding']});
const page=await browser.newPage({viewport:{width:1080,height:1920},deviceScaleFactor:1});
const errors=[];page.on('pageerror',e=>{errors.push(String(e));console.error(String(e));});page.on('console',msg=>{if(msg.type()==='error'){errors.push(msg.text());console.error(msg.text());}});
try{
 await page.goto(url,{waitUntil:'networkidle',timeout:120000});await page.waitForFunction(()=>window.sceneReady,null,{timeout:20000});
 const report=await page.evaluate(()=>window.sceneReport);
 console.log(JSON.stringify(report));
 const times=sample?[0,2,4,6,8,10,12,14.9666667]:Array.from({length:450},(_,i)=>i/30);
 if(!sample)await mkdir(path.join(dir,'frames'),{recursive:true});
 const poses=[];const start=Date.now();
 for(let i=0;i<times.length;i++){
  const result=await page.evaluate(t=>{const pose=window.renderAt(t);const canvas=document.querySelector('canvas');return {pose,image:canvas.toDataURL('image/jpeg',.97).split(',')[1]};},times[i]);
  const file=sample?`sample-${String(i).padStart(2,'0')}.jpg`:`frames/frame-${String(i).padStart(4,'0')}.jpg`;
  await writeFile(path.join(dir,file),Buffer.from(result.image,'base64'));poses.push(result.pose);
  if(sample||i%30===0)console.log(`${i+1}/${times.length}, ${(Date.now()-start)/1000}s, t=${times[i].toFixed(3)}`);
 }
 if(errors.length)throw new Error(errors.join('\n'));
 const metadata={...report,capturedFrames:times.length,errors,elapsedSeconds:(Date.now()-start)/1000,poses};
 await writeFile(path.join(dir,sample?'sample-report.json':'capture-report.json'),JSON.stringify(metadata,null,2));
 if(!sample){
  const args=['-y','-framerate','30','-start_number','0','-i',path.join(dir,'frames/frame-%04d.jpg'),'-frames:v','450','-c:v','libx264','-preset','slow','-crf','18','-pix_fmt','yuv420p','-r','30','-an','-movflags','+faststart',path.join(dir,'seongyeong_15s_3d.mp4')];
  const result=spawnSync('ffmpeg',args,{stdio:'inherit'});if(result.status!==0)throw new Error('FFmpeg encoding failed');
 }
 console.log(sample?'Sample capture passed':'450 frames captured and encoded');
}finally{await browser.close();await server.close();}
