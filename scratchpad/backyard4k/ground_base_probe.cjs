const fs=require('fs'),path=require('path');
const {chromium}=require('C:/Users/Manuel/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root=path.resolve(__dirname,'../..'),out=path.join(__dirname,'renders/ground-r8-base-probe');fs.mkdirSync(out,{recursive:true});
const setup=fs.readFileSync(path.join(root,'tools/roomkit/shot.py'),'utf8').match(/SETUP_JS = """([\s\S]*?)"""/)[1];
const poses=JSON.parse(fs.readFileSync(path.join(__dirname,'lake_r2_poses.json'),'utf8'));
(async()=>{const browser=await chromium.launch({channel:'chrome',headless:true,args:['--use-gl=angle','--enable-unsafe-swiftshader','--disable-background-timer-throttling']});
try{const page=await browser.newPage({viewport:{width:3840,height:2880}}),errors=[];page.on('pageerror',e=>errors.push(String(e)));
await page.goto('http://127.0.0.1:5001',{waitUntil:'load',timeout:90000});await page.waitForFunction(()=>document.body.classList.contains('booted'),{},{timeout:120000});
await page.evaluate(`(${setup})(${JSON.stringify({pose:poses.photo12,level:'all',light:{elevation:42,azimuth:335,condition:'sunny'},markers:false,cutaway:false,exteriorsOn:false})})`);
const data=[];
for(const trial of [{name:'whole',base:1,blades:1},{name:'base-only',base:1,blades:1,baseOnly:true},{name:'deep-base',base:.40,blades:1.45},{name:'medium-base',base:.60,blades:1.35}]){
 const result=await page.evaluate(async ({trial,pose})=>{const env=await import('/js/environment.js'),{renderer,scene,camera,controls}=window.__scene3d,root=env.getEnvironmentRoot();
 const turf=root.getObjectByName('rear-mown-turf'),tufts=root.getObjectByName('rear-short-grass-tufts'),clover=root.getObjectByName('rear-mown-clover'),litter=root.getObjectByName('rear-fallen-leaves');
 for(const mesh of [turf,tufts]){mesh.userData.r8Original??=mesh.onBeforeRender;mesh.onBeforeRender=()=>{mesh.userData.r8Original();mesh.material.color.multiplyScalar(mesh===turf?trial.base:trial.blades);};}
 for(const mesh of [tufts,clover,litter])mesh.visible=!trial.baseOnly;
 camera.position.fromArray(pose.pos);controls.target.fromArray(pose.target);camera.fov=pose.fov;camera.aspect=4/3;camera.clearViewOffset();camera.updateProjectionMatrix();camera.lookAt(controls.target);controls.update();camera.updateMatrixWorld(true);
 renderer.render(scene,camera);const cv=document.createElement('canvas');cv.width=600;cv.height=450;const ctx=cv.getContext('2d',{willReadFrequently:true});ctx.drawImage(renderer.domElement,0,0,600,450);const a=ctx.getImageData(60,300,480,150).data,mean=[0,0,0];for(let i=0;i<a.length;i+=4){mean[0]+=a[i];mean[1]+=a[i+1];mean[2]+=a[i+2];}return{mean:mean.map(v=>v/(a.length/4)),image:renderer.domElement.toDataURL('image/png'),position:camera.position.toArray(),target:controls.target.toArray()};},{trial,pose:poses.photo12});
 fs.writeFileSync(path.join(out,trial.name+'.png'),Buffer.from(result.image.split(',')[1],'base64'));data.push({trial,mean:result.mean,position:result.position,target:result.target});}
fs.writeFileSync(path.join(out,'probe.json'),JSON.stringify({data,errors},null,2));console.log(JSON.stringify({data,errors}));
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
