const fs=require('fs'),path=require('path');
const {chromium}=require('C:/Users/Manuel/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root=path.resolve(__dirname,'../..'),out=path.join(__dirname,'renders/ground-material-probe-r8');
fs.mkdirSync(out,{recursive:true});
const setup=fs.readFileSync(path.join(root,'tools/roomkit/shot.py'),'utf8').match(/SETUP_JS = """([\s\S]*?)"""/)[1];
const poses=JSON.parse(fs.readFileSync(path.join(__dirname,'workflow_matched_poses.json'),'utf8'));
(async()=>{
  const browser=await chromium.launch({channel:'chrome',headless:true,args:['--use-gl=angle','--enable-unsafe-swiftshader','--disable-background-timer-throttling']});
  try{
    const page=await browser.newPage({viewport:{width:1280,height:960}}),errors=[];
    page.on('pageerror',e=>errors.push(String(e)));
    await page.goto('http://127.0.0.1:5001',{waitUntil:'load',timeout:90000});
    await page.waitForFunction(()=>document.body.classList.contains('booted'),{},{timeout:120000});
    const opts={pose:{...poses.photo12,size:[1280,960]},level:'all',light:{elevation:42,azimuth:335,condition:'sunny'},markers:false,cutaway:false,exteriorsOn:false};
    await page.evaluate(`(${setup})(${JSON.stringify(opts)})`);
    const data=await page.evaluate(async()=>{
      const env=await import('/js/environment.js'),{renderer,scene,camera}=window.__scene3d;
      const t=env.getEnvironmentRoot().getObjectByName('rear-mown-turf'),m=t.material,litter=env.getEnvironmentRoot().getObjectByName('rear-fallen-leaves'),lm=litter.material;
      const state={boot:window.__boot.state(),map:{src:m.map.image?.src,width:m.map.image?.width,height:m.map.image?.height},normal:{src:m.normalMap?.image?.src,width:m.normalMap?.image?.width,scale:m.normalScale.toArray()},litter:{width:lm.map.image?.width,height:lm.map.image?.height,normalWidth:lm.normalMap?.image?.width,alphaTest:lm.alphaTest,normalScale:lm.normalScale.toArray(),triangles:litter.geometry.attributes.position.count/3},images:{}};
      for(const [name,wet,snow] of [['dry',0,0],['wet',1,0],['snow',0,1]]){
        env.setGroundWet(wet);env.setGroundSnow(snow);renderer.render(scene,camera);state.images[name]=renderer.domElement.toDataURL('image/png');
      }
      env.setGroundWet(0);env.setGroundSnow(0);
      const maps=[m.map,m.normalMap,lm.map,lm.normalMap];window.__groundProbe={disposed:0};maps.forEach(map=>map.addEventListener('dispose',()=>window.__groundProbe.disposed++));
      env.rebuildYard();
      state.disposedOnRebuild=window.__groundProbe.disposed;
      return state;
    });
    for(const [name,url] of Object.entries(data.images))fs.writeFileSync(path.join(out,name+'.png'),Buffer.from(url.split(',')[1],'base64'));
    delete data.images;
    await page.waitForFunction(async()=>{const env=await import('/js/environment.js');const m=env.getEnvironmentRoot().getObjectByName('rear-mown-turf').material;return m.map.image?.width===768&&m.normalMap?.image?.width===512;},{},{timeout:30000});
    data.rebuildMapsReloaded=true;
    await page.route('**/textures/backyard/grass-*.webp',route=>route.abort());
    await page.route('**/textures/backyard/oak-leaf-*.webp',route=>route.abort());
    await page.evaluate(async()=>{const env=await import('/js/environment.js');env.rebuildYard();});
    await page.waitForFunction(async()=>{const env=await import('/js/environment.js');return env.getEnvironmentRoot().getObjectByName('rear-mown-turf').material.userData.albedoLoadFailed;},{},{timeout:30000});
    data.fallback=await page.evaluate(async()=>{const env=await import('/js/environment.js');const t=env.getEnvironmentRoot().getObjectByName('rear-mown-turf'),l=env.getEnvironmentRoot().getObjectByName('rear-fallen-leaves');const {renderer,scene,camera}=window.__scene3d;renderer.render(scene,camera);return {canvas:t.material.map.isCanvasTexture,normal:t.material.normalMap===null,litterCanvas:l.material.map.isCanvasTexture,failures:t.material.userData,color:t.material.color.getHexString()};});
    data.errors=errors;fs.writeFileSync(path.join(out,'probe.json'),JSON.stringify(data,null,2));
    if(data.map.width!==768||data.normal.width!==512||data.normal.scale[1]>=0||data.litter.width!==384||data.litter.normalWidth!==256||data.litter.normalScale[1]>=0||data.disposedOnRebuild!==4||!data.fallback.canvas||!data.fallback.litterCanvas||errors.length)throw Error('Material probe failed: '+JSON.stringify(data));
    console.log(JSON.stringify(data));
  }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
