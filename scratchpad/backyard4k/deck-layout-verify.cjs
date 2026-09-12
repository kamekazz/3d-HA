const fs=require('fs');
const {chromium}=require('C:/Users/Manuel/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
(async()=>{const browser=await chromium.launch({channel:'chrome',headless:true,args:['--use-gl=angle','--enable-unsafe-swiftshader']});try{
const page=await browser.newPage({viewport:{width:800,height:600}}),errors=[];page.on('pageerror',e=>errors.push(String(e)));
await page.goto('http://127.0.0.1:5001',{waitUntil:'load',timeout:90000});
await page.waitForFunction(async()=>{const {objects3d}=await import('/js/objects.js');const d=[...objects3d.values()].find(o=>o.userData.name==='Backyard Deck');return d?.children.some(c=>c.name==='rear-deck-layout-detail');},{},{timeout:90000});
await page.waitForTimeout(3500);
const report=await page.evaluate(async()=>{
const T=await import('three'),e=await import('/js/environment.js'),{objects3d}=await import('/js/objects.js');
let deck=[...objects3d.values()].find(o=>o.userData.name==='Backyard Deck'),sofa=[...objects3d.values()].find(o=>o.userData.name==='Backyard Sofa');
const bounds=o=>{o.updateWorldMatrix(true,true);const b=new T.Box3().setFromObject(o);return {min:b.min.toArray(),max:b.max.toArray()};};
const snap=()=>{const g=deck.getObjectByName('rear-deck-layout-detail');return {deck:bounds(g),sofa:bounds(sofa.children[0]),deckChildren:deck.children.map(c=>({name:c.name,visible:c.visible})),deckParent:g.parent===deck,replacements:deck.children.filter(c=>c.name==='rear-deck-layout-detail').length};};
const before=snap();deck.position.x+=2;sofa.position.x+=1;e.rebuildYard();await new Promise(r=>setTimeout(r,1200));const moved=snap();
deck.position.x-=2;sofa.position.x-=1;e.rebuildYard();await new Promise(r=>setTimeout(r,1200));const restored=snap();
const house=await (await fetch('/api/house')).json();
for(const floor of house.floors)for(const room of floor.rooms)for(const o of room.objects){if(o.name==='Backyard Deck')o.position.x+=2;if(o.name==='Backyard Sofa')o.position.x+=1;}
(await import('/js/objects.js')).buildObjects(house);e.setEnvironmentData(house);
await new Promise(r=>setTimeout(r,2500));
deck=[...objects3d.values()].find(o=>o.userData.name==='Backyard Deck');sofa=[...objects3d.values()].find(o=>o.userData.name==='Backyard Sofa');
const reloaded=snap();
return {before,moved,restored,reloaded,shiftDeck:moved.deck.min[0]-before.deck.min[0],shiftSofa:moved.sofa.min[0]-before.sofa.min[0],reloadShiftDeck:reloaded.deck.min[0]-before.deck.min[0],reloadShiftSofa:reloaded.sofa.min[0]-before.sofa.min[0],restoredDeckDelta:restored.deck.min.map((v,i)=>v-before.deck.min[i]),restoredSofaDelta:restored.sofa.min.map((v,i)=>v-before.sofa.min[i])};
});report.errors=errors;fs.writeFileSync(__dirname+'/deck-layout-verify.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
if(report.shiftDeck!==2||Math.abs(report.shiftSofa-1)>1e-8||Math.abs(report.reloadShiftDeck-2)>1e-8||Math.abs(report.reloadShiftSofa-1)>1e-8||report.restored.replacements!==1||report.reloaded.replacements!==1||errors.length)throw Error('Lifecycle verification failed');
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
