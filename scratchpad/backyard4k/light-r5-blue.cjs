// Final ephemeral living-grass spectral balance. No production edits.
const fs=require('fs'),path=require('path');
const {chromium}=require('C:/Users/Manuel/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const includeLitter=process.argv.includes('--include-litter');
const out=path.join(__dirname,includeLitter?'renders/light-r5-blue-final':'renders/light-r5-blue'),root=path.resolve(__dirname,'../..');
const source=fs.readFileSync(path.join(root,'tools/roomkit/shot.py'),'utf8'),setup=source.match(/SETUP_JS = """([\s\S]*?)"""/)[1];
const poses=JSON.parse(fs.readFileSync(path.join(__dirname,'canonical_poses.json'),'utf8'));
(async()=>{fs.mkdirSync(out,{recursive:true});const b=await chromium.launch({channel:'chrome',headless:true,args:['--use-gl=angle','--enable-unsafe-swiftshader','--hide-scrollbars','--disable-background-timer-throttling','--disable-renderer-backgrounding']});
 const errors=[],httpErrors=[],data=[];
 try{const p=await b.newPage({viewport:{width:1200,height:900},deviceScaleFactor:1});p.on('pageerror',e=>errors.push(String(e)));p.on('response',r=>{if(r.status()>=400)httpErrors.push({url:r.url(),status:r.status()})});
 await p.goto('http://127.0.0.1:5001',{waitUntil:'load',timeout:90000});await p.waitForFunction(()=>document.body.classList.contains('booted'),{},{timeout:120000});
 const ownership=await p.evaluate(async(includeLitter)=>{const T=await import('three'),env=(await import('/js/environment.js')).getEnvironmentRoot(),sm=await import('/js/scene.js'),blue={value:1},state=window.__r5Blue={blue,snow:0,white:new T.Color(0xe9edf2)},owned=[];
  const chunk=T.ShaderChunk.lights_fragment_begin,marker='getDirectionalLightInfo( directionalLight, directLight );';if(!chunk.includes(marker))throw Error('Unknown directional-light shader');
  const fallen=env.getObjectByName('rear-fallen-leaves');state.fallenCompile=fallen.material.onBeforeCompile;state.fallenKey=fallen.material.customProgramCacheKey();
  for(const name of ['rear-mown-turf','rear-short-grass-tufts','rear-mown-clover',...(includeLitter?['rear-fallen-leaves']:[])]){const mesh=env.getObjectByName(name),m=mesh.material,before=m.onBeforeCompile,key=m.customProgramCacheKey(),renderBefore=mesh.onBeforeRender;
   m.onBeforeCompile=function(shader,renderer){before.call(this,shader,renderer);shader.uniforms.r5Blue=blue;shader.fragmentShader='uniform float r5Blue;\n'+shader.fragmentShader;shader.fragmentShader=shader.fragmentShader.replace('#include <lights_fragment_begin>',chunk.replace(marker,marker+'\ndirectLight.color *= 4.0;'));
    if(name==='rear-mown-turf'){const snowMix='diffuseColor.rgb = mix(diffuseColor.rgb, rearSnowColor';if(!shader.fragmentShader.includes(snowMix))throw Error('Missing turf snow mix');shader.fragmentShader=shader.fragmentShader.replace(snowMix,'diffuseColor.b *= r5Blue;\n'+snowMix);}
   };m.customProgramCacheKey=()=>key+'|r5-living-grass-response';m.needsUpdate=true;
   mesh.onBeforeRender=function(...args){renderBefore.apply(this,args);m.envMapIntensity=sm.getEnvIntensity()*.02;if(name!=='rear-mown-turf'&&name!=='rear-fallen-leaves')m.color.b+=(m.color.b-state.white.b*state.snow)*(blue.value-1);};
   const users=[];env.traverse(o=>{if(o.isMesh&&(Array.isArray(o.material)?o.material.includes(m):o.material===m))users.push(o.name);});owned.push({name,materialId:m.id,users});
  }return owned;
 },includeLitter);
 for(const name of ['photo09','photo12']){const pose={...poses[name],size:[1200,900]},light={azimuth:195,elevation:30,condition:'sunny'};
  await p.evaluate(()=>window.__scene3d.camera.up.set(0,1,0));await p.evaluate(`(${setup})(${JSON.stringify({pose,level:'all',light,markers:false,cutaway:false,exteriorsOn:false})})`);
  const variants=[...(includeLitter?[{blue:1,snow:0},{blue:1.425,snow:0}]:[{blue:1,snow:0},{blue:1.4,snow:0},{blue:1.45,snow:0}]),...(name==='photo12'?[{blue:1,snow:1},{blue:1.425,snow:1}]:[])];
  for(const v of variants){const r=await p.evaluate(async({pose,v})=>{const dm=await import('/js/daylight.js'),env=await import('/js/environment.js'),state=window.__r5Blue,{scene,camera,controls,renderer}=window.__scene3d;dm.settleDaylight();state.blue.value=v.blue;state.snow=v.snow;env.setGroundSnow(v.snow);
   camera.up.set(0,1,0);camera.position.fromArray(pose.pos);controls.target.fromArray(pose.target);camera.clearViewOffset();camera.aspect=4/3;camera.fov=pose.fov;camera.updateProjectionMatrix();camera.lookAt(controls.target);controls.update();camera.updateMatrixWorld(true);renderer.render(scene,camera);
   const image=renderer.domElement.toDataURL('image/png'),cv=document.createElement('canvas');cv.width=600;cv.height=450;const ctx=cv.getContext('2d',{willReadFrequently:true});ctx.drawImage(renderer.domElement,0,0,600,450);const a=ctx.getImageData(60,365,480,85).data,mean=[0,0,0];for(let i=0;i<a.length;i+=4)for(let j=0;j<3;j++)mean[j]+=a[i+j];
   const colors=['rear-mown-turf','rear-short-grass-tufts','rear-mown-clover'].map(name=>{const m=env.getEnvironmentRoot().getObjectByName(name).material;return{name,color:m.color.toArray(),env:m.envMapIntensity};}),fallen=env.getEnvironmentRoot().getObjectByName('rear-fallen-leaves').material;
   return{image,mean:mean.map(v=>v/(a.length/4)),colors,fallenUnchanged:fallen.onBeforeCompile===state.fallenCompile&&fallen.customProgramCacheKey()===state.fallenKey,position:camera.position.toArray(),target:controls.target.toArray(),up:camera.up.toArray()};
  },{pose,v});const file=`${name}-blue${v.blue}-snow${v.snow}.png`;fs.writeFileSync(path.join(out,file),Buffer.from(r.image.split(',')[1],'base64'));delete r.image;data.push({file,name,...v,...r});console.log(JSON.stringify({file,mean:r.mean,colors:r.colors,fallenUnchanged:r.fallenUnchanged}));}
 }
 fs.writeFileSync(path.join(out,'probe.json'),JSON.stringify({ownership,data,errors,httpErrors},null,2));console.log(JSON.stringify({ownership,errors,httpErrors}));
 }finally{await b.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
