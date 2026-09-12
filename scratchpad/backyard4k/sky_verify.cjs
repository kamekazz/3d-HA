const fs=require('fs'),{chromium}=require('C:/Users/Manuel/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
(async()=>{const browser=await chromium.launch({channel:'chrome',headless:true,args:['--use-gl=angle','--enable-unsafe-swiftshader']});try{
const page=await browser.newPage({viewport:{width:1200,height:900}}),errors=[];page.on('pageerror',e=>errors.push(String(e)));
await page.goto('http://127.0.0.1:5001',{waitUntil:'load',timeout:90000});
await page.waitForFunction(async()=>!!(await import('/js/environment.js')).getEnvironmentRoot()?.getObjectByName('rear-atmosphere-detail'),{},{timeout:90000});
await page.waitForTimeout(10000);
const report=await page.evaluate(async()=>{
const THREE=await import('three'),env=await import('/js/environment.js'),daylight=await import('/js/daylight.js');
const {renderer,scene,camera,controls}=window.__scene3d,clouds=env.getEnvironmentRoot().getObjectByName('rear-atmosphere-detail');
window.__daylight.mode('auto');window.__daylight.simulate({elevation:42,azimuth:335,condition:'sunny'});daylight.settleDaylight();
const gl=renderer.getContext(),size=renderer.getDrawingBufferSize(new THREE.Vector2());
// Lake ripples read performance.now inside onBeforeRender. Freeze that clock
// during this synchronous A/B so animated water is not misreported as a sky edit.
const originalNow=performance.now.bind(performance),fixedNow=originalNow();
Object.defineProperty(performance,'now',{value:()=>fixedNow,configurable:true});
const read=()=>{renderer.render(scene,camera);const a=new Uint8Array(size.x*size.y*4);gl.readPixels(0,0,size.x,size.y,gl.RGBA,gl.UNSIGNED_BYTE,a);return a;};
const compare=(pos,target)=>{camera.position.fromArray(pos);controls.target.fromArray(target);camera.lookAt(controls.target);camera.updateMatrixWorld(true);read();
clouds.visible=false;const off=read();clouds.visible=true;const on=read();let changedPixels=0,maxDelta=0;
for(let i=0;i<off.length;i+=4){let changed=false;for(let j=0;j<3;j++){const d=Math.abs(off[i+j]-on[i+j]);if(d)changed=true;maxDelta=Math.max(maxDelta,d);}if(changed)changedPixels++;}
return{position:pos,target,changedPixels,maxDelta,pixels:size.x*size.y};};
const comparisons={front:compare([80,45,110],[16,15,0]),west:compare([-110,20,-5],[16,15,0]),east:compare([120,20,-5],[16,15,0]),interior:compare([16,8,-15],[16,8,-30]),rear:compare([18,5.7,-86],[13.5,16,-24.5])};
Object.defineProperty(performance,'now',{value:originalNow,configurable:true});
const bounds=clouds.children.map(m=>{m.geometry.computeBoundingBox();const b=m.geometry.boundingBox;return{name:m.name,min:b.min.toArray(),max:b.max.toArray(),north:b.max.z<0};});
const uniforms=()=>{clouds.children.forEach(m=>m.onBeforeRender());return clouds.children.map(m=>({name:m.name,day:m.material.uniforms.cloudDay.value,wet:m.material.uniforms.cloudWet.value,color:m.material.uniforms.cloudColor.value.toArray()}));};
const dry=uniforms();env.setGroundWet(1);const wet=uniforms();env.setGroundWet(0);
window.__daylight.simulate({elevation:-18,azimuth:335,condition:'sunny'});daylight.settleDaylight();const night=uniforms();
return{comparisons,bounds,dry,wet,night};
});fs.writeFileSync(__dirname+'/sky_verify.json',JSON.stringify({report,errors},null,2));console.log(JSON.stringify({report,errors}));
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
