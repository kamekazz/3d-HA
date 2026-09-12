const fs=require('fs');
const {chromium}=require('C:/Users/Manuel/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
(async()=>{
 const b=await chromium.launch({channel:'chrome',headless:true,args:['--use-gl=angle','--enable-unsafe-swiftshader']});
 try {
 const p=await b.newPage(),errors=[];p.on('pageerror',e=>errors.push(String(e)));
 await p.goto('http://127.0.0.1:5001',{waitUntil:'load'});await p.waitForFunction(()=>window.__scene3d);await p.waitForTimeout(9000);
 await p.evaluate(()=>window.__daylight.simulate({elevation:25,azimuth:180,condition:'sunny'}));await p.waitForTimeout(2000);
 const state=await p.evaluate(async()=>{
 const {scene,renderer,sunLight,camera}=window.__scene3d;
 const env=(await import('/js/environment.js')).getEnvironmentRoot(); const THREE=await import('three');
 renderer.render(scene,camera);env.updateWorldMatrix(true,true);
 const shadowCam=sunLight.shadow.camera,direction=sunLight.position.clone().sub(sunLight.target.position).normalize();
 const casters=[];scene.traverse(o=>{if(o.isMesh&&o.castShadow&&o.visible){let v=true;for(let a=o;a;a=a.parent)v=v&&a.visible;if(v)casters.push(o);}});
 const points=[];
 for(const z of [-75,-65,-55,-45])for(const x of [10,20]){
 const point=new THREE.Vector3(x,.72,z),ndc=point.clone().project(shadowCam);
 const hits=new THREE.Raycaster(point,direction,.1,100).intersectObjects(casters,false);
 points.push({x,z,ndc:ndc.toArray(),inside:Math.abs(ndc.x)<1&&Math.abs(ndc.y)<1&&Math.abs(ndc.z)<1,hit:hits[0]?{name:hits[0].object.name,distance:hits[0].distance,position:hits[0].point.toArray()}:null});}
 const foliage=casters.filter(o=>o.name.includes('foliage')).map(o=>({name:o.name,min:new THREE.Box3().setFromObject(o).min.toArray(),max:new THREE.Box3().setFromObject(o).max.toArray()}));
 return {sun:direction.toArray(),sunIntensity:sunLight.intensity,cast:sunLight.castShadow,shadowEnabled:renderer.shadowMap.enabled,shadowCamera:{left:shadowCam.left,right:shadowCam.right,bottom:shadowCam.bottom,top:shadowCam.top,near:shadowCam.near,far:shadowCam.far},foliage,points};
 });
 fs.writeFileSync(__dirname+'/light-south-probe.json',JSON.stringify({state,errors},null,2));console.log(JSON.stringify({state,errors}));
 }finally{await b.close();}
})().catch(e=>{console.error(e);process.exitCode=1});

