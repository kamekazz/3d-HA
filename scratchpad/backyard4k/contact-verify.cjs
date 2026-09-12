const fs=require('fs');
const {chromium}=require('C:/Users/Manuel/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
(async()=>{const browser=await chromium.launch({channel:'chrome',headless:true,args:['--use-gl=angle','--enable-unsafe-swiftshader']});try{
const page=await browser.newPage({viewport:{width:800,height:600}}),errors=[];
page.on('pageerror',e=>errors.push(String(e)));
page.on('console',m=>{if(m.type()==='error'&&/shader|WebGLProgram/.test(m.text()))errors.push(m.text());});
await page.goto('http://127.0.0.1:5001',{waitUntil:'load',timeout:90000});
await page.waitForFunction(async()=>{const e=await import('/js/environment.js');let found=false;e.getEnvironmentRoot()?.traverse(o=>{if(o.userData.rearLightDetail?.contacts)found=true;});return found;},{},{timeout:90000});
await page.waitForTimeout(3500);
const report=await page.evaluate(async()=>{
const e=await import('/js/environment.js'),{objects3d}=await import('/js/objects.js');
const {renderer,scene,camera}=window.__scene3d;
e.setYardEditing(true);await new Promise(r=>setTimeout(r,1200));
let owner;e.getEnvironmentRoot().traverse(o=>{if(o.userData.rearLightDetail?.contacts)owner=o;});
const c=owner.userData.rearLightDetail.contacts;
const shrubs=e.getYardItems().filter(i=>i.label==='Clipped evergreen'),item=shrubs[0];
const shrub=e.getYardPickables().find(o=>o.userData.yardKey===item.key);
const deck=[...objects3d.values()].find(o=>o.userData.name==='Backyard Deck');
const snap=()=>{renderer.render(scene,camera);return {center:c.centers[0].toArray(),radius:c.radii[0].toArray(),deckInverse:c.deckToLocal.toArray(),deckVisible:c.deckVisible.value};};
const before=snap();shrub.position.x+=3;shrub.scale.multiplyScalar(1.5);deck.position.x+=2;const moved=snap();
shrub.visible=false;deck.visible=false;const deleted=snap();
deck.position.x-=2;deck.visible=true;e.setYardEditing(false);await new Promise(r=>setTimeout(r,1200));
let rebuilt;e.getEnvironmentRoot().traverse(o=>{if(o.userData.rearLightDetail?.contacts)rebuilt=o;});renderer.render(scene,camera);
return {count:owner.userData.rearLightDetail.crowns,before,moved,deleted,rebuiltCount:rebuilt.userData.rearLightDetail.crowns,
shrubMoves:Math.abs(moved.center[0]-before.center[0])>2,
shrubScales:Math.abs(moved.radius[0]/before.radius[0]-1.5)<1e-6,
shrubDeletes:deleted.radius[3]===0,deckMoves:Math.abs(moved.deckInverse[12]-before.deckInverse[12]+2)<1e-6,
deckDeletes:deleted.deckVisible===0};
});report.errors=errors;fs.writeFileSync(__dirname+'/contact-verify.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
if(errors.length||!report.shrubMoves||!report.shrubScales||!report.shrubDeletes||!report.deckMoves||!report.deckDeletes||report.count!==11||report.rebuiltCount!==11)throw Error('Rear contact verification failed');
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
