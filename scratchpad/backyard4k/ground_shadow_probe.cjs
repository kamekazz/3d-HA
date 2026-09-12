const fs=require('fs'),path=require('path');
const {chromium}=require('C:/Users/Manuel/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root=path.resolve(__dirname,'../..'),out=path.join(__dirname,'renders/ground-r7-shadow-probe');fs.mkdirSync(out,{recursive:true});
const setup=fs.readFileSync(path.join(root,'tools/roomkit/shot.py'),'utf8').match(/SETUP_JS = """([\s\S]*?)"""/)[1];
const poses=JSON.parse(fs.readFileSync(path.join(__dirname,'lake_r2_poses.json'),'utf8'));
(async()=>{const browser=await chromium.launch({channel:'chrome',headless:true,args:['--use-gl=angle','--enable-unsafe-swiftshader','--disable-background-timer-throttling']});
try{const page=await browser.newPage({viewport:{width:3840,height:2880}}),errors=[],consoleErrors=[];page.on('pageerror',e=>errors.push(String(e)));page.on('console',m=>{if(m.type()==='error')consoleErrors.push(m.text());});
await page.goto('http://127.0.0.1:5001',{waitUntil:'load',timeout:90000});await page.waitForFunction(()=>document.body.classList.contains('booted'),{},{timeout:120000});
await page.evaluate(`(${setup})(${JSON.stringify({pose:poses.photo12,level:'all',light:{elevation:42,azimuth:335,condition:'sunny'},markers:false,cutaway:false,exteriorsOn:false})})`);
const data=[];
for(const trial of [{name:'baseline',clamp:null},{name:'normal-0.012',clamp:.012},{name:'normal-0.05',clamp:.05},{name:'normal-and-depth',clamp:.012,depth:-.00002}]){
 const result=await page.evaluate(async ({trial,pose})=>{const clamp=trial.clamp,env=await import('/js/environment.js'),THREE=await import('three'),{renderer,scene,camera,controls}=window.__scene3d;
 const chunk=THREE.ShaderChunk.shadowmap_vertex,needle='directionalLightShadows[ i ].shadowNormalBias';if(!chunk.includes(needle))throw Error('Unexpected r160 shader chunk');
 for(const name of ['rear-mown-turf','rear-short-grass-tufts','rear-mown-clover']){const m=env.getEnvironmentRoot().getObjectByName(name).material;
 if(!m.userData.r7Original)m.userData.r7Original={compile:m.onBeforeCompile,key:m.customProgramCacheKey()};const prior=m.userData.r7Original;
 m.onBeforeCompile=function(shader,r){prior.compile.call(this,shader,r);if(clamp!==null)shader.vertexShader=shader.vertexShader.replace('#include <shadowmap_vertex>',chunk.replace(needle,'min( '+needle+', '+clamp.toFixed(3)+' )'));if(trial.depth)shader.fragmentShader=shader.fragmentShader.replace('#include <lights_fragment_begin>',THREE.ShaderChunk.lights_fragment_begin.replace('directionalLightShadow.shadowBias,','max( directionalLightShadow.shadowBias, '+trial.depth.toFixed(5)+' ),'));};
 m.customProgramCacheKey=()=>prior.key+'|r7-probe-'+trial.name;m.needsUpdate=true;}
 camera.position.fromArray(pose.pos);controls.target.fromArray(pose.target);camera.fov=pose.fov;camera.aspect=4/3;camera.clearViewOffset();camera.updateProjectionMatrix();camera.lookAt(controls.target);controls.update();camera.updateMatrixWorld(true);
 renderer.render(scene,camera);const cv=document.createElement('canvas');cv.width=600;cv.height=450;const ctx=cv.getContext('2d',{willReadFrequently:true});ctx.drawImage(renderer.domElement,0,0,600,450);const a=ctx.getImageData(60,300,480,150).data,mean=[0,0,0];for(let i=0;i<a.length;i+=4){mean[0]+=a[i];mean[1]+=a[i+1];mean[2]+=a[i+2];}return{mean:mean.map(v=>v/(a.length/4)),image:renderer.domElement.toDataURL('image/png'),chunk,position:camera.position.toArray(),target:controls.target.toArray(),fov:camera.fov};},{trial,pose:poses.photo12});
 const name=trial.name;fs.writeFileSync(path.join(out,name+'.png'),Buffer.from(result.image.split(',')[1],'base64'));
 if(trial.clamp===null)fs.writeFileSync(path.join(out,'runtime-shadowmap-vertex.glsl'),result.chunk);data.push({name,mean:result.mean,position:result.position,target:result.target,fov:result.fov});}
fs.writeFileSync(path.join(out,'probe.json'),JSON.stringify({data,errors,consoleErrors},null,2));console.log(JSON.stringify({data,errors,consoleErrors}));
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
