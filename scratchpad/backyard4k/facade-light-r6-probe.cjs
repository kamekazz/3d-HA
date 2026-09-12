// Ephemeral rear facade lighting components. Does not write app state or source.
const fs=require('fs'),path=require('path');
const {chromium}=require('C:/Users/Manuel/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root=path.resolve(__dirname,'../..'),out=path.join(__dirname,'renders/facade-light-r6-components');
const source=fs.readFileSync(path.join(root,'tools/roomkit/shot.py'),'utf8');
const setup=source.match(/SETUP_JS = """([\s\S]*?)"""/)[1],ready=source.match(/READY_JS = """([\s\S]*?)"""/)[1];
const pose={...JSON.parse(fs.readFileSync(path.join(__dirname,'canonical_poses.json'))).photo09,size:[1200,900]};
const light=JSON.parse(fs.readFileSync(path.join(__dirname,'reference-light-r5.json')));
const candidates=process.argv.includes('--candidates');
const variants=candidates?[{name:'whole',sun:1,hemi:1,env:1},...[2,3,4].map(hemi=>({name:`hemi${hemi}`,sun:1,hemi,env:1}))]:[
 {name:'whole',sun:1,hemi:1,env:1},{name:'direct-only',sun:1,hemi:0,env:0},
 {name:'hemi-only',sun:0,hemi:1,env:0},{name:'ibl-only',sun:0,hemi:0,env:1},
 {name:'without-shadow',sun:1,hemi:1,env:1,shadow:false}];
(async()=>{fs.mkdirSync(out,{recursive:true});const browser=await chromium.launch({channel:'chrome',headless:true,args:['--use-gl=angle','--enable-unsafe-swiftshader','--hide-scrollbars','--disable-background-timer-throttling','--disable-renderer-backgrounding']});
 const errors=[],httpErrors=[],data=[];
 try {const p=await browser.newPage({viewport:{width:1200,height:900},deviceScaleFactor:1});
 p.on('pageerror',e=>errors.push(String(e)));p.on('console',m=>{if(m.type()==='error'&&/shader|WebGLProgram/.test(m.text()))errors.push(m.text());});
 p.on('response',r=>{if(r.status()>=400)httpErrors.push({url:r.url(),status:r.status()});});
 await p.goto('http://127.0.0.1:5001',{waitUntil:'load',timeout:90000});
 await p.waitForFunction(()=>document.body.classList.contains('booted'),{},{timeout:120000});
 await p.evaluate(()=>window.__scene3d.camera.up.set(0,1,0));
 await p.evaluate(`(${setup})(${JSON.stringify({pose,level:'all',light,markers:false,cutaway:false,exteriorsOn:false})})`);
 const loaded=await p.evaluate(`(${ready})()`);
 const ownership=await p.evaluate(async()=>{
  const T=await import('three'),e=await import('/js/environment.js'),sm=await import('/js/scene.js');
  const state=window.__facadeR6={sun:{value:1},hemi:{value:1},env:1,meshes:[]};
  const chunk=T.ShaderChunk.lights_fragment_begin,direct='getDirectionalLightInfo( directionalLight, directLight );',hemi='irradiance += getHemisphereLightIrradiance( hemisphereLights[ i ], geometryNormal );';
  if(!chunk.includes(direct)||!chunk.includes(hemi))throw Error('Unrecognized Three lighting shader');
  const audit=[];
  for(const name of ['rear-lapped-vinyl','rear-white-fascia-casings']){
   const mesh=e.getEnvironmentRoot().getObjectByName(name),m=mesh.material,before=m.onBeforeCompile,key=m.customProgramCacheKey(),render=mesh.onBeforeRender;
   state.meshes.push(mesh);m.onBeforeCompile=function(shader,renderer){before.call(this,shader,renderer);shader.uniforms.facadeR6Sun=state.sun;shader.uniforms.facadeR6Hemi=state.hemi;
    shader.fragmentShader='uniform float facadeR6Sun;\nuniform float facadeR6Hemi;\n'+shader.fragmentShader;
    shader.fragmentShader=shader.fragmentShader.replace('#include <lights_fragment_begin>',chunk.replace(direct,direct+'\ndirectLight.color *= facadeR6Sun;').replace(hemi,'irradiance += facadeR6Hemi * getHemisphereLightIrradiance( hemisphereLights[ i ], geometryNormal );'));
   };m.customProgramCacheKey=()=>key+'|facade-r6-diagnostic';m.needsUpdate=true;
   mesh.onBeforeRender=function(...args){render.apply(this,args);m.envMapIntensity=sm.getEnvIntensity()*state.env;};
   const users=[];sm.scene.traverse(o=>{if(o.isMesh&&(Array.isArray(o.material)?o.material.includes(m):o.material===m))users.push(o.name);});
   audit.push({name,users,materialId:m.id,color:m.color.toArray(),emissive:m.emissive.toArray(),roughness:m.roughness,normalCount:mesh.geometry.attributes.normal.count});
  }return audit;
 });
 for(const v of variants){const result=await p.evaluate(async({v,pose})=>{
  const sm=await import('/js/scene.js'),dm=await import('/js/daylight.js'),state=window.__facadeR6;
  dm.settleDaylight();state.sun.value=v.sun;state.hemi.value=v.hemi;state.env=v.env;state.meshes.forEach(m=>m.receiveShadow=v.shadow!==false);
  const {scene,camera,controls,renderer,sunLight,hemiLight}=window.__scene3d;
  camera.up.set(0,1,0);camera.position.fromArray(pose.pos);controls.target.fromArray(pose.target);camera.clearViewOffset();camera.aspect=4/3;camera.fov=pose.fov;camera.updateProjectionMatrix();camera.lookAt(controls.target);controls.update();camera.updateMatrixWorld(true);renderer.render(scene,camera);
  const image=renderer.domElement.toDataURL('image/png'),c=document.createElement('canvas');c.width=600;c.height=450;const ctx=c.getContext('2d',{willReadFrequently:true});ctx.drawImage(renderer.domElement,0,0,600,450);
  const boxes={sidingGable:[312,136,45,23],sidingCenter:[314,198,50,25],sidingWing:[237,181,15,20],foreground:[60,365,480,85]},means={};
  for(const [name,box]of Object.entries(boxes)){const a=ctx.getImageData(...box).data,sum=[0,0,0];for(let i=0;i<a.length;i+=4)for(let j=0;j<3;j++)sum[j]+=a[i+j];means[name]=sum.map(s=>s/(a.length/4));}
  return{image,means,global:{sun:sunLight.intensity,hemi:hemiLight.intensity,env:sm.getEnvIntensity(),exposure:renderer.toneMappingExposure},position:camera.position.toArray(),up:camera.up.toArray(),target:controls.target.toArray(),groundResponse:(await import('/js/environment.js')).getEnvironmentRoot().getObjectByName('rear-mown-turf').material.customProgramCacheKey()};
 },{v,pose});fs.writeFileSync(path.join(out,v.name+'.png'),Buffer.from(result.image.split(',')[1],'base64'));delete result.image;data.push({variant:v,...result});console.log(JSON.stringify({variant:v,means:result.means}));}
 fs.writeFileSync(path.join(out,candidates?'candidates.json':'components.json'),JSON.stringify({loaded,ownership,data,errors,httpErrors},null,2));console.log(JSON.stringify({loaded,ownership,errors,httpErrors}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
