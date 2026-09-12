const fs=require('fs'),path=require('path');
const {chromium}=require('C:/Users/Manuel/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root=path.resolve(__dirname,'../..'),out=path.join(__dirname,'renders/light-canopy-union');fs.mkdirSync(out,{recursive:true});
const setup=fs.readFileSync(path.join(root,'tools/roomkit/shot.py'),'utf8').match(/SETUP_JS = """([\s\S]*?)"""/)[1];
const poses=JSON.parse(fs.readFileSync(path.join(__dirname,'lake_r2_poses.json'),'utf8'));
const lower={size:[3840,2880],pos:[-2,4.1,-80.8],target:[26,1.5,-114.8],fov:68};
fs.writeFileSync(path.join(__dirname,'ground_r6_lower_pose.json'),JSON.stringify({photo12:lower},null,2));
(async()=>{const browser=await chromium.launch({channel:'chrome',headless:true,args:['--use-gl=angle','--enable-unsafe-swiftshader','--disable-background-timer-throttling']});
try{const page=await browser.newPage({viewport:{width:3840,height:2880}});
await page.goto('http://127.0.0.1:5001',{waitUntil:'load',timeout:90000});await page.waitForFunction(()=>document.body.classList.contains('booted'),{},{timeout:120000});
const data=[];
for(const trial of [{name:'baseline',pose:poses.photo12},{name:'sky-visible',pose:poses.photo12,ao:false}]){
 await page.evaluate(`(${setup})(${JSON.stringify({pose:trial.pose,level:'all',light:{elevation:42,azimuth:335,condition:'sunny'},markers:false,cutaway:false,exteriorsOn:false})})`);
 const result=await page.evaluate(async trial=>{const env=await import('/js/environment.js'),{renderer,scene,camera}=window.__scene3d;
 if(trial.ao===false&&!window.__r6AOOff){for(const name of ['rear-mown-turf','rear-short-grass-tufts','rear-mown-clover']){const m=env.getEnvironmentRoot().getObjectByName(name).material,prior=m.onBeforeCompile,key=m.customProgramCacheKey();m.onBeforeCompile=function(shader,r){prior.call(this,shader,r);if(shader.uniforms.rearSkyCount)shader.uniforms.rearSkyCount.value=0;};m.customProgramCacheKey=()=>key+'|r6-diagnostic-no-sky-block';m.needsUpdate=true;}window.__r6AOOff=true;}
 renderer.render(scene,camera);const cv=document.createElement('canvas');cv.width=600;cv.height=450;const ctx=cv.getContext('2d',{willReadFrequently:true});ctx.drawImage(renderer.domElement,0,0,600,450);const a=ctx.getImageData(60,300,480,150).data,mean=[0,0,0];for(let i=0;i<a.length;i+=4){mean[0]+=a[i];mean[1]+=a[i+1];mean[2]+=a[i+2];}return{mean:mean.map(v=>v/(a.length/4)),image:renderer.domElement.toDataURL('image/png')};},trial);
 fs.writeFileSync(path.join(out,trial.name+'.png'),Buffer.from(result.image.split(',')[1],'base64'));data.push({name:trial.name,pose:trial.pose,mean:result.mean});}
fs.writeFileSync(path.join(out,'probe.json'),JSON.stringify(data,null,2));console.log(JSON.stringify(data));
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
