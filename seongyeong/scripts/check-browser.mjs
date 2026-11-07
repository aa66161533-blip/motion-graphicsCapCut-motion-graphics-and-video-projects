import { chromium } from 'playwright';
import {createServer} from 'vite';
import {existsSync} from 'node:fs';
import {writeFile,mkdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
const server=await createServer({server:{host:'127.0.0.1',port:5180}});await server.listen();
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||(existsSync('/usr/bin/chromium')?'/usr/bin/chromium':undefined),args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const page=await browser.newPage({viewport:{width:420,height:840}});const errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
const results={};
try{
 await page.goto(server.resolvedUrls.local[0],{waitUntil:'networkidle'});await page.waitForFunction(()=>window.sceneReady);
 await page.locator('#play').click();results.pauseControl=(await page.locator('#play').textContent())==='재생';
 await page.locator('#scrub').fill('12');await page.locator('#scrub').dispatchEvent('input');results.scrubControl=(await page.locator('#time').textContent()).startsWith('12.0');
 const a=await page.evaluate(()=>{window.renderAt(6);return window.getFrame();});await page.evaluate(()=>window.renderAt(9));
 const b=await page.evaluate(()=>{window.renderAt(6);return window.getFrame();});results.deterministicSameTime=createHash('sha256').update(a).digest('hex')===createHash('sha256').update(b).digest('hex');
 const c=await page.evaluate(()=>{window.renderAt(6.5);return window.getFrame();});results.animatedScene=a!==c;
 const samples=await page.evaluate(()=>[0,3.999,4,4.001,7.999,8,8.001,9.999,10,10.001,11.999,12,12.001,14.999,15].map(t=>window.renderAt(t)));
 results.knotsContinuous=true;for(let i=1;i<samples.length;i++){if(samples[i].time-samples[i-1].time<.01&&Math.hypot(...samples[i].position.map((v,j)=>v-samples[i-1].position[j]))>.02)results.knotsContinuous=false;}
 const info=await page.evaluate(()=>window.sceneReport);results.webgl2=info.renderer==='WebGL2';results.twoKoi=info.koiCount===2;results.noErrors=errors.length===0;
 await page.evaluate(()=>window.renderAt(14.9666666667));await mkdir('renders',{recursive:true});await page.screenshot({path:'renders/browser-player.png'});
 await page.locator('#restart').click();await page.waitForFunction(()=>Number(document.querySelector('#scrub').value)<3,null,{timeout:15000});results.restartControl=Number(await page.locator('#scrub').inputValue())<3;
 const passed=Object.values(results).every(Boolean);await writeFile('renders/browser-check.json',JSON.stringify({passed,results,errors},null,2));console.log(JSON.stringify({passed,results,errors},null,2));if(!passed)process.exitCode=1;
}finally{await browser.close();await server.close();}
