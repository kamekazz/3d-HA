// Ephemeral actual-app illumination diagnostics. No production/source/state writes.
const fs=require('fs'),path=require('path');
const {chromium}=require('C:/Users/Manuel/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const woodlandOnly=process.argv.includes('--photo12-components');
const root=path.resolve(__dirname,'../..'),out=path.join(__dirname,'renders',woodlandOnly?'light-r5-photo12-components':'light-r5-diagnostic');
const source=fs.readFileSync(path.join(root,'tools/roomkit/shot.py'),'utf8');
const setup=source.match(/SETUP_JS = """([\s\S]*?)"""/)[1],ready=source.match(/READY_JS = """([\s\S]*?)"""/)[1];
const poses=JSON.parse(fs.readFileSync(path.join(__dirname,'canonical_poses.json'),'utf8'));
const trials=[{name:'canonical335-42',azimuth:335,elevation:42},{name:'south180-25',azimuth:180,elevation:25},{name:'south155-20',azimuth:155,elevation:20}];
(async()=>{fs.mkdirSync(out,{recursive:true});
 const browser=await chromium.launch({channel:'chrome',headless:true,args:['--use-gl=angle','--enable-unsafe-swiftshader','--hide-scrollbars','--disable-background-timer-throttling','--disable-renderer-backgrounding']});
 const errors=[],consoleErrors=[],httpErrors=[],data=[];
 try{const p=await browser.newPage({viewport:{width:1200,height:900},deviceScaleFactor:1});
 p.on('pageerror',e=>errors.push(String(e)));p.on('console',m=>{if(m.type()==='error')consoleErrors.push(m.text())});
 p.on('response',r=>{if(r.status()>=400)httpErrors.push({url:r.url(),status:r.status()})});
 await p.goto('http://127.0.0.1:5001',{waitUntil:'load',timeout:90000});
 await p.waitForFunction(()=>document.body.classList.contains('booted'),{},{timeout:120000});
 for(const poseName of woodlandOnly?['photo12']:['photo09','photo12']){
  const pose={...poses[poseName],size:[1200,900]};
  for(const trial of woodlandOnly?trials.slice(0,1):trials){
   const light={elevation:trial.elevation,azimuth:trial.azimuth,condition:'sunny'};
   await p.evaluate(`(${setup})(${JSON.stringify({pose,level:'all',light,markers:false,cutaway:false,exteriorsOn:false})})`);
   const loaded=await p.evaluate(`(${ready})()`);
   for(const component of woodlandOnly||(poseName==='photo09'&&trial.name!=='south155-20')?['whole','indirect-only','direct-only','without-ibl','without-hemi']:['whole']){
    const result=await p.evaluate(async({pose,component})=>{
     const sm=await import('/js/scene.js'),dm=await import('/js/daylight.js');
     const {scene,renderer,camera,controls,sunLight,hemiLight}=window.__scene3d;
     dm.settleDaylight();
     camera.position.fromArray(pose.pos);controls.target.fromArray(pose.target);camera.clearViewOffset();camera.aspect=4/3;camera.fov=pose.fov;camera.updateProjectionMatrix();camera.lookAt(controls.target);controls.update();camera.updateMatrixWorld(true);
     const saved={sun:sunLight.intensity,hemi:hemiLight.intensity,env:sm.getEnvIntensity()};
     if(component==='indirect-only')sunLight.intensity=0;
     if(component==='direct-only'){hemiLight.intensity=0;sm.setEnvIntensity(0);}
     if(component==='without-ibl')sm.setEnvIntensity(0);
     if(component==='without-hemi')hemiLight.intensity=0;
     let image,means;
     try{renderer.render(scene,camera);image=renderer.domElement.toDataURL('image/png');
      const c=document.createElement('canvas');c.width=600;c.height=450;const ctx=c.getContext('2d',{willReadFrequently:true});ctx.drawImage(renderer.domElement,0,0,600,450);
      const boxes={foreground:[60,365,480,85],siding:[280,143,80,28],middleLawn:[170,340,270,35]};means={};
      for(const [key,box]of Object.entries(boxes)){const a=ctx.getImageData(...box).data,m=[0,0,0];for(let i=0;i<a.length;i+=4)for(let j=0;j<3;j++)m[j]+=a[i+j];means[key]=m.map(v=>v/(a.length/4));}
     }finally{sunLight.intensity=saved.sun;hemiLight.intensity=saved.hemi;sm.setEnvIntensity(saved.env);}
     return{image,means,light:saved,sun: sunLight.position.clone().sub(sunLight.target.position).normalize().toArray(),position:camera.position.toArray(),target:controls.target.toArray(),fov:camera.fov,shadowEnabled:renderer.shadowMap.enabled};
    },{pose,component});
    const file=`${poseName}-${trial.name}-${component}.png`;fs.writeFileSync(path.join(out,file),Buffer.from(result.image.split(',')[1],'base64'));delete result.image;
    data.push({file,poseName,trial,component,loaded,...result});console.log(JSON.stringify({file,means:result.means,loaded}));
   }
  }
 }
 fs.writeFileSync(path.join(out,'probe.json'),JSON.stringify({data,errors,consoleErrors,httpErrors},null,2));console.log(JSON.stringify({errors,consoleErrors,httpErrors}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
