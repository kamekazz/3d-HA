// Geometry-selected solar visibility scan, then bounded runtime ground response.
const fs=require('fs'),path=require('path');
const {chromium}=require('C:/Users/Manuel/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const out=path.join(__dirname,'renders/light-r5-threshold'),root=path.resolve(__dirname,'../..');
const shot=fs.readFileSync(path.join(root,'tools/roomkit/shot.py'),'utf8');
const setup=shot.match(/SETUP_JS = """([\s\S]*?)"""/)[1],ready=shot.match(/READY_JS = """([\s\S]*?)"""/)[1];
const poses=JSON.parse(fs.readFileSync(path.join(__dirname,'canonical_poses.json'),'utf8'));
(async()=>{fs.mkdirSync(out,{recursive:true});const b=await chromium.launch({channel:'chrome',headless:true,args:['--use-gl=angle','--enable-unsafe-swiftshader','--hide-scrollbars','--disable-background-timer-throttling','--disable-renderer-backgrounding']});
 const errors=[],httpErrors=[],data=[];
 try{const p=await b.newPage({viewport:{width:1200,height:900},deviceScaleFactor:1});p.on('pageerror',e=>errors.push(String(e)));p.on('response',r=>{if(r.status()>=400)httpErrors.push({url:r.url(),status:r.status()})});
 await p.goto('http://127.0.0.1:5001',{waitUntil:'load',timeout:90000});await p.waitForFunction(()=>document.body.classList.contains('booted'),{},{timeout:120000});
 await p.evaluate(()=>{window.__r5Threshold={points:{}};});
 for(const name of ['photo09','photo12']){
  const pose={...poses[name],size:[1200,900]};await p.evaluate(()=>window.__scene3d.camera.up.set(0,1,0));await p.evaluate(`(${setup})(${JSON.stringify({pose,level:'all',light:{azimuth:335,elevation:42,condition:'sunny'},markers:false,cutaway:false,exteriorsOn:false})})`);
  await p.evaluate(async({name,pose})=>{const T=await import('three'),env=(await import('/js/environment.js')).getEnvironmentRoot(),{scene,camera,controls,renderer}=window.__scene3d;
   camera.up.set(0,1,0);camera.position.fromArray(pose.pos);controls.target.fromArray(pose.target);camera.clearViewOffset();camera.aspect=4/3;camera.fov=pose.fov;camera.updateProjectionMatrix();camera.lookAt(controls.target);controls.update();camera.updateMatrixWorld(true);scene.updateMatrixWorld(true);renderer.render(scene,camera);
   const turf=env.getObjectByName('rear-mown-turf'),points=[];for(const y of [380,420])for(const x of [90,230,370,510]){const ray=new T.Raycaster();ray.setFromCamera(new T.Vector2(x/600*2-1,1-y/450*2),camera);const h=ray.intersectObject(turf,false)[0];points.push({pixel:[x,y],central:x===230||x===370,point:h?.point.toArray()||null});}window.__r5Threshold.points[name]=points;
  },{name,pose});
 }
 const scan=await p.evaluate(async()=>{const T=await import('three'),{scene}=window.__scene3d,casters=[],texCache=new Map(),points=window.__r5Threshold.points;
  const visible=o=>{for(let n=o;n;n=n.parent)if(!n.visible)return false;return true;};scene.traverse(o=>{if(o.isMesh&&o.castShadow&&visible(o)&&!['rear-short-grass-tufts','rear-mown-clover','rear-fallen-leaves','rear-mown-turf'].includes(o.name))casters.push(o);});
  const opaque=h=>{const m=Array.isArray(h.object.material)?h.object.material[h.face.materialIndex]:h.object.material;if(m.opacity===0)return false;if(!m.alphaTest||!m.map||!h.uv)return true;const tex=m.map,img=tex.image;if(!img?.width)return true;let v=texCache.get(tex);if(!v){const c=document.createElement('canvas');c.width=img.width;c.height=img.height;const ctx=c.getContext('2d',{willReadFrequently:true});ctx.drawImage(img,0,0);v={a:ctx.getImageData(0,0,c.width,c.height).data,w:c.width,h:c.height};texCache.set(tex,v);}const uv=h.uv.clone();tex.transformUv(uv);const x=Math.max(0,Math.min(v.w-1,Math.floor(uv.x*v.w))),y=Math.max(0,Math.min(v.h-1,Math.floor(uv.y*v.h)));return v.a[(y*v.w+x)*4+3]/255*m.opacity>=m.alphaTest;};
  const trials=[];for(const azimuth of [165,180,195,210])for(const elevation of [30,33,36]){const az=azimuth*Math.PI/180,el=elevation*Math.PI/180,direction=new T.Vector3(Math.cos(el)*Math.sin(az),Math.sin(el),-Math.cos(el)*Math.cos(az)),result={};
   for(const[name,list]of Object.entries(points))result[name]=list.map(p=>{if(!p.point)return{...p,valid:false};const origin=new T.Vector3(...p.point).add(new T.Vector3(0,.35,0)),ray=new T.Raycaster(origin,direction,.01,300),first=ray.intersectObjects(casters,false).find(opaque);return{...p,valid:true,blocked:!!first,first:first?{name:first.object.name,id:first.object.id,distance:first.distance,point:first.point.toArray()}:null};});
   const a=result.photo09.filter(p=>p.valid),ac=a.filter(p=>p.central),d=result.photo12.filter(p=>p.valid),shade09=ac.filter(p=>p.blocked).length/ac.length,shade09All=a.filter(p=>p.blocked).length/a.length,clear12=d.filter(p=>!p.blocked).length/d.length;
   trials.push({azimuth,elevation,shade09,shade09All,clear12,score:shade09+clear12+shade09All*.25,result});
  }trials.sort((a,b)=>b.score-a.score);return{points,trials,selected:trials[0],rayCaveat:'Origins0.35ft above actual turf; excludes low grass/litter casters; alpha-tested foliage respected; material side follows visible geometry.'};
 });
 fs.writeFileSync(path.join(out,'visibility.json'),JSON.stringify(scan,null,2));console.log(JSON.stringify({phase:'visibility',ranked:scan.trials.map(({azimuth,elevation,shade09,shade09All,clear12,score})=>({azimuth,elevation,shade09,shade09All,clear12,score})),selected:scan.selected}));
 const chosen=scan.selected,credible=chosen.shade09>=.75&&chosen.clear12>=.75;
 await p.evaluate(async()=>{const T=await import('three'),env=(await import('/js/environment.js')).getEnvironmentRoot(),sm=await import('/js/scene.js'),state=window.__r5Threshold;state.response={ibl:1,direct:{value:1}};
  const chunk=T.ShaderChunk.lights_fragment_begin,marker='getDirectionalLightInfo( directionalLight, directLight );';if(!chunk.includes(marker))throw Error('Unknown directional-light shader chunk');
  for(const name of ['rear-mown-turf','rear-short-grass-tufts','rear-mown-clover','rear-fallen-leaves']){const mesh=env.getObjectByName(name),m=mesh.material,before=m.onBeforeCompile,key=m.customProgramCacheKey(),renderBefore=mesh.onBeforeRender;
   m.onBeforeCompile=function(shader,renderer){before.call(this,shader,renderer);shader.uniforms.r5SunGain=state.response.direct;shader.fragmentShader='uniform float r5SunGain;\n'+shader.fragmentShader;shader.fragmentShader=shader.fragmentShader.replace('#include <lights_fragment_begin>',chunk.replace(marker,marker+'\ndirectLight.color *= r5SunGain;'));};m.customProgramCacheKey=()=>key+'|r5-ephemeral-light-response';m.needsUpdate=true;
   mesh.onBeforeRender=function(...args){renderBefore.apply(this,args);m.envMapIntensity=sm.getEnvIntensity()*state.response.ibl;};
  }
 });
 for(const name of ['photo09','photo12']){
  const pose={...poses[name],size:[1200,900]},light={azimuth:chosen.azimuth,elevation:chosen.elevation,condition:'sunny'};await p.evaluate(()=>window.__scene3d.camera.up.set(0,1,0));await p.evaluate(`(${setup})(${JSON.stringify({pose,level:'all',light,markers:false,cutaway:false,exteriorsOn:false})})`);const loaded=await p.evaluate(`(${ready})()`);
  const variants=[{name:'whole',ibl:1,sun:1},{name:'direct',ibl:0,sun:1,directOnly:true},{name:'ground-no-ibl',ibl:0,sun:1},...(credible?[{name:'ground-sun3-env0',ibl:0,sun:3},{name:'ground-sun4-env002',ibl:.02,sun:4}]:[])];
  for(const variant of variants){const result=await p.evaluate(async({pose,variant})=>{const sm=await import('/js/scene.js'),dm=await import('/js/daylight.js'),{scene,camera,controls,renderer,hemiLight}=window.__scene3d,state=window.__r5Threshold;
   dm.settleDaylight();state.response.ibl=variant.ibl;state.response.direct.value=variant.sun;const savedHemi=hemiLight.intensity,savedEnv=sm.getEnvIntensity();if(variant.directOnly){hemiLight.intensity=0;sm.setEnvIntensity(0);}
   camera.up.set(0,1,0);camera.position.fromArray(pose.pos);controls.target.fromArray(pose.target);camera.clearViewOffset();camera.aspect=4/3;camera.fov=pose.fov;camera.updateProjectionMatrix();camera.lookAt(controls.target);controls.update();camera.updateMatrixWorld(true);
   let image,mean;try{renderer.shadowMap.needsUpdate=true;renderer.render(scene,camera);image=renderer.domElement.toDataURL('image/png');const cv=document.createElement('canvas');cv.width=600;cv.height=450;const ctx=cv.getContext('2d',{willReadFrequently:true});ctx.drawImage(renderer.domElement,0,0,600,450);const a=ctx.getImageData(60,365,480,85).data;mean=[0,0,0];for(let i=0;i<a.length;i+=4)for(let j=0;j<3;j++)mean[j]+=a[i+j];mean=mean.map(v=>v/(a.length/4));}finally{hemiLight.intensity=savedHemi;sm.setEnvIntensity(savedEnv);state.response.ibl=1;state.response.direct.value=1;}return{image,mean,position:camera.position.toArray(),target:controls.target.toArray(),up:camera.up.toArray()};
  },{pose,variant});const file=`${name}-${chosen.azimuth}-${chosen.elevation}-${variant.name}.png`;fs.writeFileSync(path.join(out,file),Buffer.from(result.image.split(',')[1],'base64'));delete result.image;data.push({file,name,variant,loaded,...result});console.log(JSON.stringify({file,mean:result.mean}));}
 }
 fs.writeFileSync(path.join(out,'probe.json'),JSON.stringify({selected:chosen,credible,data,errors,httpErrors},null,2));console.log(JSON.stringify({credible,errors,httpErrors}));
 }finally{await b.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
