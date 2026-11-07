import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

// Every animation is a pure function of seconds. Capture never uses wall-clock time.
const capture=new URLSearchParams(location.search).has('capture');
if(capture)document.body.classList.add('capture');
const W=capture?1080:Math.min(720,Math.floor(innerHeight*.5625)),H=Math.round(W*16/9);
const renderer=new THREE.WebGLRenderer({antialias:true,alpha:false,preserveDrawingBuffer:true,powerPreference:'high-performance'});
renderer.setPixelRatio(1);renderer.setSize(W,H);renderer.outputColorSpace=THREE.LinearSRGBColorSpace;
renderer.setClearColor(0xeeeade);document.querySelector('#stage').appendChild(renderer.domElement);
const scene=new THREE.Scene();scene.background=new THREE.Color('#eeeade');
const camera=new THREE.PerspectiveCamera(48,9/16,.1,230);
const sceneTime={value:0}, paperColor=new THREE.Color('#eeeade');
const v3=(x,y,z)=>new THREE.Vector3(x,y,z);
let seed=2718;const rnd=()=>{seed=(Math.imul(seed,1664525)+1013904223)|0;return(seed>>>0)/4294967296;};
const noiseGLSL=`float hash(vec3 p){return fract(sin(dot(p,vec3(127.1,311.7,74.7)))*43758.5453);} float noise(vec3 p){vec3 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(mix(hash(i),hash(i+vec3(1,0,0)),f.x),mix(hash(i+vec3(0,1,0)),hash(i+vec3(1,1,0)),f.x),f.y),mix(mix(hash(i+vec3(0,0,1)),hash(i+vec3(1,0,1)),f.x),mix(hash(i+vec3(0,1,1)),hash(i+vec3(1,1,1)),f.x),f.y),f.z);}`;
const mats=[];
function ink(color,weight=.5){
 const m=new THREE.ShaderMaterial({uniforms:{base:{value:new THREE.Color(color)},paper:{value:paperColor},time:sceneTime,weight:{value:weight},wind:{value:0}},vertexShader:`varying vec3 wp;varying vec3 norm;uniform float time,wind;void main(){vec4 p=modelMatrix*vec4(position,1.);p.x+=sin(time*.8+p.y*.31+p.z*.2)*wind;wp=p.xyz;norm=normalize(mat3(modelMatrix)*normal);gl_Position=projectionMatrix*viewMatrix*p;}`,fragmentShader:`varying vec3 wp;varying vec3 norm;uniform vec3 base,paper;uniform float time,weight;${noiseGLSL} void main(){float n=noise(wp*1.3),fine=noise(wp*vec3(7.,.7,7.));float l=.48+.45*max(dot(normalize(norm),normalize(vec3(-.7,1.,.6))),0.);float striation=pow(.5+.5*sin(wp.y*8.+n*7.+wp.x*2.),13.)*.10;vec3 c=mix(base*.65,base*1.24,clamp(l+n*.3-striation,0.,1.));c=mix(c,paper, .10+fine*.12);float dist=distance(cameraPosition,wp);float fog=1.-exp(-dist*dist*.00012);fog=clamp(fog+max(0.,4.-wp.y)*.012,0.,.93);float front=time*24.-5.;float reveal=smoothstep(front+5.,front-4.,dist+n*7.);c=mix(paper,mix(c,paper,fog),reveal);gl_FragColor=vec4(c,1.);}`});mats.push(m);return m;
}
const rock=ink('#59665e'),cliffMat=ink('#65766a'),wood=ink('#4e594b'),roof=ink('#45594f'),stone=ink('#9ba69a'),leaf=ink('#627961'),bark=ink('#576154');
function mesh(g,m,parent=scene){const o=new THREE.Mesh(g,m);parent.add(o);return o;}
function cylinder(a,b,r1,r2,material,parent=scene,sides=8){const dir=b.clone().sub(a);const o=mesh(new THREE.CylinderGeometry(r2,r1,dir.length(),sides),material,parent);o.position.copy(a).add(b).multiplyScalar(.5);o.quaternion.setFromUnitVectors(v3(0,1,0),dir.normalize());return o;}
function box(w,h,d,x,y,z,material,parent=scene){const o=mesh(new THREE.BoxGeometry(w,h,d),material,parent);o.position.set(x,y,z);return o;}
// True radial height fields, with ridges on the flanks and irregular silhouettes.
function mountain(x,z,height,radius,material,offset=0){
 const seg=48,rings=27,vertices=[],indices=[];
 for(let j=0;j<=rings;j++){let u=j/rings;for(let i=0;i<=seg;i++){let a=i/seg*Math.PI*2;let r=radius*u*(1+.12*Math.sin(a*5+offset)+.08*Math.sin(a*9));let ridge=.68+.32*Math.pow(.5+.5*Math.sin(a*7+offset),2);let h=height*Math.pow(Math.max(0,1-u),.64)*(1+Math.sin(u*23+a*6+offset)*.075*ridge);vertices.push(x+Math.cos(a)*r, h-2+Math.sin(a*3)*u*.9,z+Math.sin(a)*r*.78);}}
 for(let j=0;j<rings;j++)for(let i=0;i<seg;i++){const a=j*(seg+1)+i,b=a+seg+1;indices.push(a,b,a+1,b,b+1,a+1);}
 const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(vertices,3));g.setIndex(indices);g.computeVertexNormals();return mesh(g,material);
}
const mountains=[];
for(let row=0;row<5;row++)for(const side of [-1,1]){
 const z=6-row*22;for(let i=0;i<2;i++){let x=side*(28+row*2+i*10);mountains.push(mountain(x,z-i*9,18+rnd()*17+row*2,9+rnd()*6,rock,rnd()*10));}
}
for(let i=0;i<8;i++)mountains.push(mountain(-45+i*13,-105-rnd()*13,30+rnd()*23,13,cliffMat,rnd()*8));
// Valley ground is a broad true mesh, submerged under the garden pool.
const ground=mesh(new THREE.PlaneGeometry(180,210,1,1),ink('#c7cdba'));ground.rotation.x=-Math.PI/2;ground.position.set(0,-1,-40);

// Pavilion cliff and a tall waterfall on its upstream left.
mountain(-9,-23,19,6.2,cliffMat,2.1);
mountain(3,-33,9,6.6,cliffMat,1.2);
const ledge=mesh(new THREE.CylinderGeometry(5.1,4.2,1.25,18),stone);ledge.position.set(3,6.3,-32);
const fallGroup=new THREE.Group();fallGroup.position.set(-7.4,0,-18.5);scene.add(fallGroup);
const waterfallMat=new THREE.ShaderMaterial({transparent:true,depthWrite:false,side:THREE.DoubleSide,uniforms:{time:sceneTime},vertexShader:`varying vec2 vUv;varying vec3 wp;void main(){vUv=uv;vec4 p=modelMatrix*vec4(position,1.);wp=p.xyz;gl_Position=projectionMatrix*viewMatrix*p;}`,fragmentShader:`varying vec2 vUv;varying vec3 wp;uniform float time;${noiseGLSL}void main(){float streak=noise(vec3(vUv.x*32.,vUv.y*8.+time*3.8,0.));float thread=pow(.5+.5*sin(vUv.x*180.+streak*4.),5.);float edge=smoothstep(0.,.10,vUv.x)*smoothstep(1.,.88,vUv.x);float alpha=edge*(.55+thread*.30);float reveal=smoothstep(1.,2.5,time);float fog=1.-exp(-pow(distance(cameraPosition,wp)*.012,2.));gl_FragColor=vec4(mix(vec3(.84,.91,.85),vec3(.95,.95,.90),streak),alpha*reveal*(1.-fog*.7));}`});
const crag=new THREE.CylinderGeometry(2.3,3.0,16,23,24);const cp=crag.attributes.position;for(let i=0;i<cp.count;i++){let x=cp.getX(i),y=cp.getY(i),z=cp.getZ(i),a=Math.atan2(z,x),u=(y+8)/16;let rough=1+.09*Math.sin(a*7+y*.45)+.055*Math.cos(a*13-y*.7);cp.setXYZ(i,x*rough,y+Math.pow(u,3)*(1.4+Math.sin(a*3)*1.0+Math.cos(a*7)*.5),z*rough);}crag.computeVertexNormals();const fallRock=mesh(crag,cliffMat);fallRock.position.set(-7.4,8.5,-20.1);
const fallGeo=new THREE.PlaneGeometry(2.2,15.8,14,50);const fp=fallGeo.attributes.position;for(let i=0;i<fp.count;i++){const u=(fp.getY(i)+7.9)/15.8;fp.setZ(i,(1-u)*.7+1.5);fp.setX(i,fp.getX(i)*(1+.06*Math.sin(u*19.)));}fallGeo.computeVertexNormals();
const waterfall=mesh(fallGeo,waterfallMat,fallGroup);waterfall.position.set(0,8.6,0);
// Curved falling threads: phase advances downwards in world space.
const streamers=[];
for(let i=0;i<36;i++){const o=mesh(new THREE.CylinderGeometry(.015,.025,.5+rnd()*.8,4),new THREE.MeshBasicMaterial({color:'#eef2e6',transparent:true,opacity:.5}),fallGroup);o.position.set((rnd()-.5)*2.1,rnd()*17+.5,.76+rnd()*.13);streamers.push({o,phase:rnd()*17,speed:4+rnd()*3});}

// Procedural soft fog sprites in actual world space with depth sorting.
const fogCanvas=document.createElement('canvas');fogCanvas.width=fogCanvas.height=128;
const ctx=fogCanvas.getContext('2d'),grad=ctx.createRadialGradient(64,64,0,64,64,64);grad.addColorStop(0,'rgba(242,242,230,.40)');grad.addColorStop(.45,'rgba(242,242,230,.19)');grad.addColorStop(1,'rgba(242,242,230,0)');ctx.fillStyle=grad;ctx.fillRect(0,0,128,128);
const fogTexture=new THREE.CanvasTexture(fogCanvas),fogSprites=[];
for(let i=0;i<34;i++){const o=new THREE.Sprite(new THREE.SpriteMaterial({map:fogTexture,transparent:true,depthWrite:false,opacity:.45}));const p=i<12?v3(-7.4+(rnd()-.5)*4,1+rnd()*3,-17+(rnd()-.5)*3):v3((rnd()-.5)*45,4+rnd()*8,-rnd()*85);o.position.copy(p);o.scale.set(i<12?7:25,i<12?3:5,1);scene.add(o);fogSprites.push({o,p,phase:rnd()*6});}

// Architectural geometry: six timber posts, railings, stairs, brackets and a tiled curved roof.
const pavilion=new THREE.Group();pavilion.position.set(3,7,-32);scene.add(pavilion);
box(6,.32,5,0,.10,0,stone,pavilion);box(5.55,.27,4.55,0,.4,0,wood,pavilion);
for(let i=0;i<3;i++)box(2.6,.23,1.1,0,-.06-i*.23,2.6+i*.8,stone,pavilion);
for(const x of [-2.35,0,2.35])for(const z of [-1.85,1.85]){
 cylinder(v3(x,.5,z),v3(x,4,z),.12,.10,wood,pavilion,10);
 box(.5,.12,.5,x,3.86,z,wood,pavilion);
 for(const sign of [-1,1])cylinder(v3(x,3.3,z),v3(x+sign*.5,3.92,z),.06,.06,wood,pavilion,6);
}
for(const z of [-1.85,1.85])box(5.1,.2,.2,0,3.98,z,wood,pavilion);
for(const x of [-2.35,2.35])box(.2,.2,4.25,x,3.98,0,wood,pavilion);
for(const z of [-1.95,1.95])for(const x of [-2.35,2.35]){
 box(1.6,.10,.11,x*.65,1.25,z,wood,pavilion);
 for(let i=0;i<4;i++)box(.055,.66,.055,x*.65+(i-1.5)*.36,.9,z,wood,pavilion);
}
for(const x of [-2.4,2.4]){box(.1,.1,3.8,x,1.25,0,wood,pavilion);for(let i=0;i<9;i++)box(.055,.7,.055,x,.9,(i-4)*.43,wood,pavilion);}
// Curved giwa: gable profile with upturned corners; actual thickness and tile ridges.
function roofY(x,z){const u=Math.abs(z)/3.2;return 5.2-1.38*u+.58*Math.pow(u,3)+.30*Math.pow(Math.abs(x)/3.65,5)*u;}
const roofVerts=[],roofIdx=[],nx=42,nz=40;
for(let j=0;j<=nz;j++)for(let i=0;i<=nx;i++){let x=(i/nx-.5)*7.3,z=(j/nz-.5)*6.4;roofVerts.push(x,roofY(x,z),z);}
for(let j=0;j<nz;j++)for(let i=0;i<nx;i++){let a=j*(nx+1)+i,b=a+nx+1;roofIdx.push(a,b,a+1,b,b+1,a+1);}
const roofGeo=new THREE.BufferGeometry();roofGeo.setAttribute('position',new THREE.Float32BufferAttribute(roofVerts,3));roofGeo.setIndex(roofIdx);roofGeo.computeVertexNormals();const roofTop=mesh(roofGeo,roof,pavilion);roofTop.material.side=THREE.DoubleSide;
for(let i=0;i<=36;i++){let x=(i/36-.5)*7.3;const pts=[];for(let j=0;j<=24;j++){let z=(j/24-.5)*6.4;pts.push(v3(x,roofY(x,z)+.045,z));}mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts),24,.037,4,false),roof,pavilion);}
for(const z of [-3.2,3.2]){const pts=[];for(let i=0;i<35;i++){let x=(i/34-.5)*7.3;pts.push(v3(x,roofY(x,z)-.04,z));}mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts),34,.13,6,false),wood,pavilion);}
cylinder(v3(-3.85,5.25,0),v3(3.85,5.25,0),.13,.13,roof,pavilion);
for(const x of [-3.85,3.85]){const tip=mesh(new THREE.SphereGeometry(.18,8,6),roof,pavilion);tip.position.set(x,5.36,0);tip.scale.y=1.5;}

// Windswept pines: branching 3D trunks and clusters of fine needles.
const swaying=[];
function pine(x,y,z,s=1){const tree=new THREE.Group();tree.position.set(x,y,z);tree.scale.setScalar(s);scene.add(tree);
const joints=[v3(0,0,0),v3(.3,2,0),v3(-.2,4.1,0),v3(.6,6.1,.2),v3(1.1,7.8,.1)];for(let i=0;i<4;i++)cylinder(joints[i],joints[i+1],.28-i*.055,.22-i*.05,bark,tree,7);
for(let j=0;j<7;j++){const a=v3(.2,3.2+j*.56,0),b=v3((j%2?1:-1)*(2.5-j*.16),3.8+j*.58,(rnd()-.5)*2.2);cylinder(a,b,.10,.035,bark,tree,6);const tuft=new THREE.Group();tuft.position.copy(b);tree.add(tuft);swaying.push({o:tuft,phase:rnd()*6});
for(let k=0;k<5;k++){const c=mesh(new THREE.SphereGeometry(.8,9,5),leaf,tuft);c.position.set((rnd()-.5)*1.9,(rnd()-.5)*.25,(rnd()-.5)*1.4);c.scale.set(1,.22,.85);}
const pos=[];for(let k=0;k<85;k++){let a=rnd()*Math.PI*2,r=rnd()*1.3,cx=Math.cos(a)*r,cz=Math.sin(a)*r;pos.push(cx,0,cz,cx+Math.cos(a)*.45,.1+rnd()*.25,cz+Math.sin(a)*.45);}const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));tuft.add(new THREE.LineSegments(g,new THREE.LineBasicMaterial({color:'#516450',transparent:true,opacity:.6})));}
return tree;}
pine(-1.7,6.8,-33,1);pine(7.8,6.6,-35,.72);pine(-12,-.1,-9,1.3);pine(13,0,-45,1.0);
for(let i=0;i<13;i++){let side=i%2?1:-1;pine(side*(17+rnd()*10),7+rnd()*6,-15-rnd()*65,.28+rnd()*.4);}

// Pond: physically placed surface, actual reflected scene from an inverted camera.
const pond=new THREE.Group();pond.position.set(4,0,-24);scene.add(pond);
const reflectionTarget=new THREE.WebGLRenderTarget(512,912,{depthBuffer:true});
const reflectionCamera=new THREE.PerspectiveCamera();
const reflectionMatrix=new THREE.Matrix4();
const waterMat=new THREE.ShaderMaterial({transparent:true,depthWrite:false,uniforms:{time:sceneTime,reflection:{value:reflectionTarget.texture},reflectMatrix:{value:reflectionMatrix},paper:{value:paperColor}},vertexShader:`varying vec3 wp;varying vec4 rp;uniform mat4 reflectMatrix;void main(){vec4 p=modelMatrix*vec4(position,1.);wp=p.xyz;rp=reflectMatrix*p;gl_Position=projectionMatrix*viewMatrix*p;}`,fragmentShader:`varying vec3 wp;varying vec4 rp;uniform float time;uniform sampler2D reflection;uniform vec3 paper;${noiseGLSL}void main(){vec2 uv=rp.xy/rp.w*.5+.5;uv+=vec2(sin(wp.z*3.+time)*.0015,cos(wp.x*2.-time)*.0015);vec3 refl=texture2D(reflection,clamp(uv,0.,1.)).rgb;float ring=0.;for(int i=0;i<3;i++){vec2 c=vec2(float(i)*2.-2.,sin(float(i)*2.)*2.);float r=length(wp.xz-vec2(4.,-24.)-c);float phase=mod(time*.65+float(i)*1.4,5.);ring+=exp(-pow((r-phase)*9.,2.))*(1.-phase/5.); }vec3 color=mix(vec3(.71,.79,.67),refl,.30)+ring*.055;float fog=1.-exp(-pow(distance(cameraPosition,wp)*.009,2.));gl_FragColor=vec4(mix(color,paper,fog),.40);}`});
const pondSurface=mesh(new THREE.CircleGeometry(10.8,80),waterMat,pond);pondSurface.rotation.x=-Math.PI/2;pondSurface.position.y=.38;
const bed=mesh(new THREE.CircleGeometry(10.7,80),ink('#adbaa1'),pond);bed.rotation.x=-Math.PI/2;bed.position.y=-.65;
// Border stones follow the pond, leaving its front open to the camera.
for(let i=0;i<43;i++){let a=i/43*Math.PI*2;if(a>.4&&a<2.5)continue;const o=mesh(new THREE.IcosahedronGeometry(.55+rnd()*.45,1),stone);o.position.set(4+Math.cos(a)*10.6,-.12,-24+Math.sin(a)*10.6);o.scale.set(1.3,.6,1);o.rotation.set(rnd(),rnd(),rnd());}
for(let i=0;i<14;i++){const o=mesh(new THREE.SphereGeometry(.16+rnd()*.16,7,5),stone);o.position.set(4+(rnd()-.5)*14,-.56,-24+(rnd()-.5)*13);o.scale.y=.4;}

// Exactly two volumetric koi; their routes and articulated tails are time-driven.
const koi=[];
for(let i=0;i<2;i++){
 const group=new THREE.Group();scene.add(group);const bodyMat=ink(i?'#cf7339':'#ab4436');
 const body=mesh(new THREE.SphereGeometry(1,20,12),bodyMat,group);body.scale.set(.27,.19,.85);
 const head=mesh(new THREE.SphereGeometry(.28,12,8),bodyMat,group);head.position.z=.59;head.scale.set(.87,.75,1);
 const patch=mesh(new THREE.SphereGeometry(1,14,9),ink('#e3d9b5'),group);patch.position.set(.02,.10,-.07);patch.scale.set(.18,.13,.32);
 const tail=new THREE.Group();tail.position.z=-.73;group.add(tail);
 const finShape=new THREE.Shape();finShape.moveTo(0,0);finShape.quadraticCurveTo(.45,-.2,.39,-.65);finShape.quadraticCurveTo(0,-.48,-.39,-.65);finShape.quadraticCurveTo(-.45,-.2,0,0);
 const finMat=new THREE.MeshBasicMaterial({color:i?'#df9b55':'#c76651',side:THREE.DoubleSide,transparent:true,opacity:.82});const tailFin=mesh(new THREE.ShapeGeometry(finShape,12),finMat,tail);tailFin.rotation.x=Math.PI/2;
 for(const side of [-1,1]){const fin=mesh(new THREE.SphereGeometry(1,9,5),finMat,group);fin.position.set(side*.28,-.015,.22);fin.scale.set(.30,.025,.20);fin.rotation.y=side*.4;}
 for(const side of [-1,1]){const eye=mesh(new THREE.SphereGeometry(.026,8,6),new THREE.MeshBasicMaterial({color:'#202b28'}),group);eye.position.set(side*.205,.08,.66);}
 const points=[v3(-3.4,-.05,-1.1),v3(-1.3,-.08,3.0),v3(3.5,-.03,1.7),v3(3.2,-.08,-2.4),v3(-.3,-.02,-3.3)].map(p=>p.add(v3(4,0,-24)));
 const path=new THREE.CatmullRomCurve3(points,true,'centripetal');koi.push({group,tail,path,phase:i*.49});
}

// Batch only static opaque meshes; moving fish and the hidden reflection bed remain separate.
leaf.uniforms.wind.value=.075;bark.uniforms.wind.value=.015;
scene.updateMatrixWorld(true);
const movingRoots=new Set(koi.map(k=>k.group));
const batches=new Map();const remove=[];
scene.traverse(o=>{if(!o.isMesh||!mats.includes(o.material)||o===bed)return;let p=o;while(p){if(movingRoots.has(p))return;p=p.parent;}const g=o.geometry.clone();for(const name of Object.keys(g.attributes))if(name!=='position'&&name!=='normal')g.deleteAttribute(name);g.applyMatrix4(o.matrixWorld);if(!batches.has(o.material))batches.set(o.material,[]);batches.get(o.material).push(g.index?g.toNonIndexed():g);remove.push(o);});
for(const o of remove)o.removeFromParent();for(const [material,geometries] of batches){const merged=mergeGeometries(geometries,false);if(!merged)throw new Error('Static geometry batching failed');mesh(merged,material);}

// One smooth camera journey. Time knots are 0,4,8,12,15 seconds.
const cameraTimes=[0,4,8,10,12,15];
const cameraPoints=[v3(1,15,38),v3(-2,12,10),v3(-2,12,-8),v3(10,14,-17),v3(13,13,-20),v3(10,9,-7)];
const targetPoints=[v3(0,13,-20),v3(-7,11,-19),v3(0,9,-28),v3(3,9,-32),v3(3,8.8,-32),v3(4,3.5,-26)];
function smoothPath(points,t){let i=0;while(i<cameraTimes.length-2&&t>cameraTimes[i+1])i++;let dt=cameraTimes[i+1]-cameraTimes[i],u=THREE.MathUtils.clamp((t-cameraTimes[i])/dt,0,1);const a=points[i],b=points[i+1],prev=points[Math.max(0,i-1)],next=points[Math.min(points.length-1,i+2)];
const va=b.clone().sub(prev).multiplyScalar(dt/(cameraTimes[i+1]-cameraTimes[Math.max(0,i-1)]));const vb=next.clone().sub(a).multiplyScalar(dt/(cameraTimes[Math.min(points.length-1,i+2)]-cameraTimes[i]));
if(i===0)va.multiplyScalar(.6);if(i===points.length-2)vb.set(0,0,0);
return a.clone().multiplyScalar(2*u**3-3*u*u+1).addScaledVector(va,u**3-2*u*u+u).addScaledVector(b,-2*u**3+3*u*u).addScaledVector(vb,u**3-u*u);}

// A subtle final paper pass, not an image plane: fibers remain fixed on the page.
const target=new THREE.WebGLRenderTarget(W,H);
const postScene=new THREE.Scene(),postCamera=new THREE.OrthographicCamera(-1,1,1,-1,0,1);
const postMat=new THREE.ShaderMaterial({uniforms:{image:{value:target.texture},time:sceneTime,resolution:{value:new THREE.Vector2(W,H)}},vertexShader:`varying vec2 uv0;void main(){uv0=uv;gl_Position=vec4(position.xy,0.,1.);}`,fragmentShader:`varying vec2 uv0;uniform sampler2D image;uniform float time;uniform vec2 resolution;float h(vec2 p){return fract(sin(dot(p,vec2(12.9898,78.233)))*43758.5453);}void main(){vec3 c=texture2D(image,uv0).rgb;vec2 px=uv0*resolution;float fiber=h(floor(px*.45))*.5+h(floor(px*vec2(.05,.5)))*.5;float vignette=1.-.035*pow(length((uv0-.5)*vec2(1.,.7)),2.);c=c*vignette+(fiber-.5)*.025;float fade=smoothstep(0.,1.65,time);c=mix(vec3(.942,.932,.891)+(fiber-.5)*.025,c,fade);gl_FragColor=vec4(pow(clamp(c,0.,1.),vec3(.95)),1.);}`});
mesh(new THREE.PlaneGeometry(2,2),postMat,postScene);
const report={width:W,height:H,duration:15,fps:30,frames:450,koiCount:koi.length,pavilionPosts:6,mountains:mountains.length,renderer:renderer.capabilities.isWebGL2?'WebGL2':'WebGL',camera:'PerspectiveCamera',cameraKnots:cameraTimes,continuous:true,audio:false};
function renderAt(t){t=THREE.MathUtils.clamp(t,0,15);sceneTime.value=t;camera.position.copy(smoothPath(cameraPoints,t));camera.lookAt(smoothPath(targetPoints,t));camera.updateMatrixWorld();
 for(const s of streamers){s.o.position.y=16.4-((s.phase+t*s.speed)%15.6);s.o.position.z=1.51+(1-s.o.position.y/16.5)*.7;s.o.visible=t>1.1;}
 for(const s of fogSprites){s.o.position.copy(s.p);s.o.position.x+=Math.sin(t*.16+s.phase)*1.3;s.o.position.y+=Math.sin(t*.23+s.phase)*.22;}
 for(const s of swaying){s.o.rotation.z=Math.sin(t*.8+s.phase)*.025;s.o.rotation.x=Math.sin(t*.65+s.phase)*.018;}
 for(const f of koi){const u=(t*.026+f.phase)%1;f.group.position.copy(f.path.getPointAt(u));const tangent=f.path.getTangentAt(u);f.group.rotation.y=Math.atan2(tangent.x,tangent.z);f.group.rotation.z=Math.sin(t*2+f.phase)*.03;f.tail.rotation.y=Math.sin(t*4.8+f.phase*6)*.42;}
 // Planar reflection uses the same scene, with a mirrored camera below water.
 reflectionCamera.copy(camera);reflectionCamera.position.y=.76-camera.position.y;const look=smoothPath(targetPoints,t);look.y=.76-look.y;reflectionCamera.up.set(0,-1,0);reflectionCamera.lookAt(look);reflectionCamera.updateMatrixWorld();
 reflectionMatrix.copy(reflectionCamera.projectionMatrix).multiply(reflectionCamera.matrixWorldInverse);
 pondSurface.visible=false;for(const f of koi)f.group.visible=false;bed.visible=false;
 renderer.setRenderTarget(reflectionTarget);renderer.render(scene,reflectionCamera);
 pondSurface.visible=true;for(const f of koi)f.group.visible=true;bed.visible=true;
 renderer.setRenderTarget(target);renderer.render(scene,camera);renderer.setRenderTarget(null);renderer.render(postScene,postCamera);
 document.querySelector('#scrub').value=t;document.querySelector('#time').textContent=`${t.toFixed(1)} / 15`;
 return {time:t,position:camera.position.toArray(),target:look.toArray(),drawCalls:renderer.info.render.calls};}
window.renderAt=renderAt;window.sceneReport=report;window.sceneReady=true;window.getFrame=()=>renderer.domElement.toDataURL('image/png');
let playing=!capture,clock=performance.now(),current=0;
document.querySelector('#play').onclick=()=>{playing=!playing;document.querySelector('#play').textContent=playing?'일시정지':'재생';clock=performance.now();};
document.querySelector('#restart').onclick=()=>{current=0;playing=true;renderAt(0);clock=performance.now();document.querySelector('#play').textContent='일시정지';};
document.querySelector('#scrub').oninput=e=>{current=Number(e.target.value);playing=false;document.querySelector('#play').textContent='재생';renderAt(current);};
function tick(now){if(!capture){if(playing){current=Math.min(15,current+Math.max(0,(now-clock)/1000));renderAt(current);if(current===15){playing=false;document.querySelector('#play').textContent='재생';}}clock=now;requestAnimationFrame(tick);}}
renderAt(0);clock=performance.now();if(!capture)requestAnimationFrame(tick);
