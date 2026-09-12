const fs=require('fs'),path=require('path');
const {chromium}=require('C:/Users/Manuel/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root=path.resolve(__dirname,'../..'),out=path.join(__dirname,'renders/ground-tint-probe');fs.mkdirSync(out,{recursive:true});
const setup=fs.readFileSync(path.join(root,'tools/roomkit/shot.py'),'utf8').match(/SETUP_JS = """([\s\S]*?)"""/)[1];
const poses=JSON.parse(fs.readFileSync(path.join(__dirname,'workflow_matched_poses.json'),'utf8'));
(async()=>{const browser=await chromium.launch({channel:'chrome',headless:true,args:['--use-gl=angle','--enable-unsafe-swiftshader','--disable-background-timer-throttling']});
try{const page=await browser.newPage({viewport:{width:3840,height:2880}});
await page.goto('http://127.0.0.1:5001',{waitUntil:'load',timeout:90000});await page.waitForFunction(()=>document.body.classList.contains('booted'),{},{timeout:120000});
await page.evaluate(`(${setup})(${JSON.stringify({pose:poses.photo12,level:'all',light:{elevation:42,azimuth:335,condition:'sunny'},markers:false,cutaway:false,exteriorsOn:false})})`);
const trials=await page.evaluate(async()=>{const env=await import('/js/environment.js'),THREE=await import('three'),{renderer,scene,camera}=window.__scene3d;
const turf=env.getEnvironmentRoot().getObjectByName('rear-mown-turf'),prior=turf.onBeforeRender;
const canvas=document.createElement('canvas');canvas.width=3840;canvas.height=2880;const ctx=canvas.getContext('2d',{willReadFrequently:true}),results=[];
for(const tint of ['aab7c5','b5bec5','bac4cb']){turf.onBeforeRender=()=>{prior();turf.material.color.set('#'+tint);};renderer.render(scene,camera);ctx.drawImage(renderer.domElement,0,0);
const p=ctx.getImageData(1267,2188,1229,547).data,s=[0,0,0];for(let i=0;i<p.length;i+=4){s[0]+=p[i];s[1]+=p[i+1];s[2]+=p[i+2];}const mean=s.map(v=>v/(p.length/4));
const prev=document.createElement('canvas');prev.width=1280;prev.height=960;prev.getContext('2d').drawImage(canvas,0,0,1280,960);results.push({tint,mean,image:prev.toDataURL('image/png')});}
turf.onBeforeRender=prior;return results;});
for(const trial of trials){fs.writeFileSync(path.join(out,trial.tint+'.png'),Buffer.from(trial.image.split(',')[1],'base64'));delete trial.image;}
fs.writeFileSync(path.join(out,'tints.json'),JSON.stringify(trials,null,2));console.log(JSON.stringify(trials));
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
