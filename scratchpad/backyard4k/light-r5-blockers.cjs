// Runtime-only shadow caster ablations and actual turf/sun rays. No production writes.
const fs=require('fs'),path=require('path');
const {chromium}=require('C:/Users/Manuel/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const corrected=process.argv.includes('--corrected');
const out=path.join(__dirname,corrected?'renders/light-r5-blockers-corrected':'renders/light-r5-blockers'),root=path.resolve(__dirname,'../..');
const shot=fs.readFileSync(path.join(root,'tools/roomkit/shot.py'),'utf8');
const setup=shot.match(/SETUP_JS = """([\s\S]*?)"""/)[1],ready=shot.match(/READY_JS = """([\s\S]*?)"""/)[1];
const poses=JSON.parse(fs.readFileSync(path.join(__dirname,'canonical_poses.json'),'utf8'));
(async()=>{fs.mkdirSync(out,{recursive:true});
 const b=await chromium.launch({channel:'chrome',headless:true,args:['--use-gl=angle','--enable-unsafe-swiftshader','--hide-scrollbars','--disable-background-timer-throttling','--disable-renderer-backgrounding']});
 const errors=[],httpErrors=[],data=[],rays=[];
 try{const p=await b.newPage({viewport:{width:1200,height:900},deviceScaleFactor:1});
 p.on('pageerror',e=>errors.push(String(e)));p.on('response',r=>{if(r.status()>=400)httpErrors.push({url:r.url(),status:r.status()})});
 await p.goto('http://127.0.0.1:5001',{waitUntil:'load',timeout:90000});await p.waitForFunction(()=>document.body.classList.contains('booted'),{},{timeout:120000});
 for(const c of [{poseName:'photo12',azimuth:335,elevation:42},{poseName:'photo12',azimuth:180,elevation:corrected?42:25},{poseName:'photo09',azimuth:180,elevation:corrected?42:25}]){
  const pose={...poses[c.poseName],size:[1200,900]},light={azimuth:c.azimuth,elevation:c.elevation,condition:'sunny'};
  await p.evaluate(()=>window.__scene3d.camera.up.set(0,1,0));
  await p.evaluate(`(${setup})(${JSON.stringify({pose,level:'all',light,markers:false,cutaway:false,exteriorsOn:false})})`);
  const loaded=await p.evaluate(`(${ready})()`);
  const trials=corrected?(c.azimuth===335?['whole','direct','no-receive-direct']:['whole','direct','no-ibl','no-receive-direct']):(c.azimuth===335?['whole','direct','no-shadows-whole','no-shadows-direct','no-grass-cast','no-near-leaves-cast','no-far-leaves-cast','no-tree-cast','no-shell-cast']:['whole','direct','no-ibl','no-shadows-direct']);
  for(const trial of trials){
   const r=await p.evaluate(async({pose,trial})=>{
    const sm=await import('/js/scene.js'),dm=await import('/js/daylight.js'),env=(await import('/js/environment.js')).getEnvironmentRoot(),T=await import('three');
    const {renderer,scene,camera,controls,sunLight,hemiLight}=window.__scene3d;dm.settleDaylight();
    camera.up.set(0,1,0);camera.position.fromArray(pose.pos);controls.target.fromArray(pose.target);camera.clearViewOffset();camera.aspect=4/3;camera.fov=pose.fov;camera.updateProjectionMatrix();camera.lookAt(controls.target);controls.update();camera.updateMatrixWorld(true);
    const saved={hemi:hemiLight.intensity,env:sm.getEnvIntensity(),shadows:renderer.shadowMap.enabled},changed=[],receiveChanged=[];
    if(trial==='no-receive-direct')scene.traverse(o=>{if(o.isMesh&&o.receiveShadow){receiveChanged.push(o);o.receiveShadow=false;}});
    const isGrass=o=>['rear-mown-turf','rear-short-grass-tufts','rear-mown-clover','rear-fallen-leaves'].includes(o.name);
    const isTree=o=>['rear-scanned-oak-leaves','rear-distant-oak-leaves','rear-lake-bark'].includes(o.name);
    const visible=o=>{for(let n=o;n;n=n.parent)if(!n.visible)return false;return true;};
    scene.traverse(o=>{if(!o.isMesh||!o.castShadow)return;let disable=false;
     if(trial==='no-grass-cast')disable=isGrass(o);
     if(trial==='no-near-leaves-cast')disable=o.name==='rear-scanned-oak-leaves';
     if(trial==='no-far-leaves-cast')disable=o.name==='rear-distant-oak-leaves';
     if(trial==='no-tree-cast')disable=isTree(o);
     if(trial==='no-shell-cast'){for(let n=o;n;n=n.parent)if(n.userData.kind==='house-shell')disable=true;}
     if(disable){changed.push(o);o.castShadow=false;}
    });
    if(trial.includes('no-shadows'))renderer.shadowMap.enabled=false;
    if(!trial.includes('whole')){sm.setEnvIntensity(0);if(trial!=='no-ibl')hemiLight.intensity=0;}
    let image,mean,casters;
    try{renderer.shadowMap.needsUpdate=true;renderer.render(scene,camera);image=renderer.domElement.toDataURL('image/png');
     const cv=document.createElement('canvas');cv.width=600;cv.height=450;const ctx=cv.getContext('2d',{willReadFrequently:true});ctx.drawImage(renderer.domElement,0,0,600,450);const a=ctx.getImageData(60,365,480,85).data;mean=[0,0,0];for(let i=0;i<a.length;i+=4)for(let j=0;j<3;j++)mean[j]+=a[i+j];mean=mean.map(v=>v/(a.length/4));
     casters=[];if(trial==='whole')scene.traverse(o=>{if(!o.isMesh||!o.castShadow||!visible(o))return;const box=new T.Box3().setFromObject(o);casters.push({id:o.id,name:o.name,kind:o.userData.kind||'',min:box.min.toArray(),max:box.max.toArray(),instanced:!!o.isInstancedMesh,count:o.count||1,material:(Array.isArray(o.material)?o.material:[o.material]).map(m=>({name:m.name,type:m.type,side:m.side,shadowSide:m.shadowSide,alphaTest:m.alphaTest,opacity:m.opacity}))});});
    }finally{renderer.shadowMap.enabled=saved.shadows;changed.forEach(o=>o.castShadow=true);receiveChanged.forEach(o=>o.receiveShadow=true);hemiLight.intensity=saved.hemi;sm.setEnvIntensity(saved.env);renderer.shadowMap.needsUpdate=true;}
    return{image,mean,disabled:changed.map(o=>({id:o.id,name:o.name})),casters,position:camera.position.toArray(),target:controls.target.toArray(),up:camera.up.toArray(),sun:sunLight.position.clone().normalize().toArray()};
   },{pose,trial});
   const file=`${c.poseName}-${c.azimuth}-${c.elevation}-${trial}.png`;fs.writeFileSync(path.join(out,file),Buffer.from(r.image.split(',')[1],'base64'));delete r.image;data.push({file,...c,trial,loaded,...r});console.log(JSON.stringify({file,mean:r.mean,disabled:r.disabled}));
  }
  const sampled=await p.evaluate(async(pose)=>{
   const T=await import('three'),env=(await import('/js/environment.js')).getEnvironmentRoot(),{scene,camera,controls,sunLight,renderer}=window.__scene3d;
   camera.up.set(0,1,0);camera.position.fromArray(pose.pos);controls.target.fromArray(pose.target);camera.clearViewOffset();camera.aspect=4/3;camera.fov=pose.fov;camera.updateProjectionMatrix();camera.lookAt(controls.target);controls.update();camera.updateMatrixWorld(true);scene.updateMatrixWorld(true);renderer.render(scene,camera);
   const turf=env.getObjectByName('rear-mown-turf'),tufts=env.getObjectByName('rear-short-grass-tufts'),casters=[];
   const visible=o=>{for(let n=o;n;n=n.parent)if(!n.visible)return false;return true;};
   scene.traverse(o=>{if(o.isMesh&&o.castShadow&&visible(o)&&!['rear-short-grass-tufts','rear-mown-clover','rear-fallen-leaves','rear-mown-turf'].includes(o.name))casters.push(o);});
   const cache=new Map();
   const opaque=hit=>{const m=Array.isArray(hit.object.material)?hit.object.material[hit.face.materialIndex]:hit.object.material;if(m.opacity===0)return false;if(!m.alphaTest||!m.map||!hit.uv)return true;
    const tex=m.map,img=tex.image;if(!img?.width)return true;let v=cache.get(tex);if(!v){const c=document.createElement('canvas');c.width=img.width;c.height=img.height;const ctx=c.getContext('2d',{willReadFrequently:true});ctx.drawImage(img,0,0);v={a:ctx.getImageData(0,0,c.width,c.height).data,w:c.width,h:c.height};cache.set(tex,v);}
    const uv=hit.uv.clone();tex.transformUv(uv);const x=Math.max(0,Math.min(v.w-1,Math.floor(uv.x*v.w))),y=Math.max(0,Math.min(v.h-1,Math.floor(uv.y*v.h)));return v.a[(y*v.w+x)*4+3]/255*m.opacity>=m.alphaTest;};
   const rays=[],direction=sunLight.position.clone().sub(sunLight.target.position).normalize(),normal=new T.Vector3(),n=tufts.geometry.attributes.normal;
   let minY=1,maxY=-1;for(let i=0;i<n.count;i++){normal.fromBufferAttribute(n,i);minY=Math.min(minY,normal.y);maxY=Math.max(maxY,normal.y);}
   for(const [sx,sy]of [[120,390],[300,405],[490,395]]){
    const ray=new T.Raycaster();ray.setFromCamera(new T.Vector2(sx/600*2-1,1-sy/450*2),camera);const land=ray.intersectObject(turf,false)[0];if(!land){rays.push({pixel:[sx,sy],ground:null});continue;}
    const origin=land.point.clone().add(new T.Vector3(0,.35,0));ray.set(origin,direction);ray.near=.01;ray.far=300;
    const hits=ray.intersectObjects(casters,false),solid=hits.filter(opaque),first=solid[0];
    const describe=h=>{const box=new T.Box3().setFromObject(h.object);return{name:h.object.name,id:h.object.id,distance:h.distance,point:h.point.toArray(),normal:h.face.normal.clone().transformDirection(h.object.matrixWorld).toArray(),bounds:{min:box.min.toArray(),max:box.max.toArray()},faceIndex:h.faceIndex,material:Array.isArray(h.object.material)?h.object.material[h.face.materialIndex].name:h.object.material.name};};
    rays.push({pixel:[sx,sy],ground:land.point.toArray(),groundFaceNormal:land.face.normal.toArray(),origin:origin.toArray(),sun:direction.toArray(),shadowNDC:origin.clone().project(sunLight.shadow.camera).toArray(),first:first?describe(first):null,next:solid.slice(1,3).map(describe),geometricHits:hits.length,alphaSolidHits:solid.length});
   }
   return{rays,excludedRayCasters:'Grass, clover and litter excluded after elevating origins0.35ft; their causal effect is isolated by no-grass-cast render. Alpha-tested leaf texels are respected. Ray face side follows visible material, may differ from depth shadowSide.',bladeNormalY:[minY,maxY],groundMaterial:{name:turf.material.name,color:turf.material.color.toArray(),roughness:turf.material.roughness,metalness:turf.material.metalness,side:turf.material.side},bladeMaterial:{color:tufts.material.color.toArray(),roughness:tufts.material.roughness,metalness:tufts.material.metalness,side:tufts.material.side}};
  },pose);rays.push({...c,...sampled});console.log(JSON.stringify({phase:'rays',...c,rays:sampled.rays}));
 }
 fs.writeFileSync(path.join(out,'probe.json'),JSON.stringify({data,rays,errors,httpErrors},null,2));console.log(JSON.stringify({errors,httpErrors}));
 }finally{await b.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
