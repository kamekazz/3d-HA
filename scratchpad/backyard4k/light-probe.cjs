// Read-only diagnostics of the real application. No scene or HA mutations.
const fs=require('fs');
const {chromium}=require('C:/Users/Manuel/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
(async()=>{
 const b=await chromium.launch({channel:'chrome',headless:true,args:['--use-gl=angle','--enable-unsafe-swiftshader']});
 try {
  const p=await b.newPage(),errors=[];p.on('pageerror',e=>errors.push(String(e)));
  await p.goto('http://127.0.0.1:5001',{waitUntil:'load'});
  await p.waitForFunction(()=>window.__scene3d);await p.waitForTimeout(9000);
  const state=await p.evaluate(async()=>{
   const {scene,renderer,sunLight,hemiLight}=window.__scene3d;
   const env=(await import('/js/environment.js')).getEnvironmentRoot();
   let local=null;env.traverse(o=>{if(o.userData.rearLightDetail)local=o.userData.rearLightDetail;});
   const deck=[...(await import('/js/objects.js')).objects3d.values()].find(o=>o.userData.name==='Backyard Deck');
   const meshes=[];deck?.traverse(o=>{if(o.isMesh)meshes.push({name:o.name,cast:o.castShadow,receive:o.receiveShadow});});
   const lights=[];scene.traverse(o=>{if(o.isLight)lights.push({type:o.type,name:o.name});});
   return {local,deck:meshes,lights,exposure:renderer.toneMappingExposure,shadow:{enabled:renderer.shadowMap.enabled,type:renderer.shadowMap.type,map:sunLight.shadow.mapSize.toArray(),normalBias:sunLight.shadow.normalBias,bias:sunLight.shadow.bias},background:scene.background?.getHexString?.(),sun:{color:sunLight.color.getHexString(),intensity:sunLight.intensity},hemi:{sky:hemiLight.color.getHexString(),ground:hemiLight.groundColor.getHexString(),intensity:hemiLight.intensity}};
  });
  fs.writeFileSync(__dirname+'/light-probe.json',JSON.stringify({url:'http://127.0.0.1:5001',state,errors},null,2));console.log(JSON.stringify({local:state.local,deckMeshes:state.deck.length,shadow:state.shadow,errors}));
 }finally{await b.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
