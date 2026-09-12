const fs=require('fs');
const {chromium}=require('C:/Users/Manuel/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
(async()=>{
  const browser=await chromium.launch({channel:'chrome',headless:true,args:['--use-gl=angle','--enable-unsafe-swiftshader']});
  try{
    const page=await browser.newPage({viewport:{width:900,height:700}}),errors=[];
    page.on('pageerror',e=>errors.push(String(e)));
    await page.goto('http://127.0.0.1:5001',{waitUntil:'load',timeout:90000});
    await page.waitForFunction(async()=>{
      const {objects3d}=await import('/js/objects.js');
      return [...objects3d.values()].some(o=>o.getObjectByName('rear-grill-cloth-cover'));
    },{},{timeout:90000});
    await page.waitForTimeout(3500);
    const report=await page.evaluate(async()=>{
      const T=await import('three'),e=await import('/js/environment.js'),{objects3d}=await import('/js/objects.js');
      const grill=[...objects3d.values()].find(o=>o.userData.name==='Backyard Grill');
      const bounds=o=>{o.updateWorldMatrix(true,true);const b=new T.Box3().setFromObject(o);return {min:b.min.toArray(),max:b.max.toArray()};};
      const cover=()=>grill.getObjectByName('rear-grill-cloth-cover');
      const initialCover=cover(),source=grill.children.find(c=>c!==initialCover),materials=[];
      source.traverse(o=>{if(o.isMesh)for(const m of Array.isArray(o.material)?o.material:[o.material])materials.push({m,uuid:m.uuid,color:m.color?.getHex(),roughness:m.roughness,metalness:m.metalness});});
      let coverDisposed=0,glassDisposed=0;
      initialCover.children[0].geometry.addEventListener('dispose',()=>coverDisposed++);
      e.getEnvironmentRoot().getObjectByName('rear-slider-reflective-pane').material.addEventListener('dispose',()=>glassDisposed++);
      const before=bounds(cover());grill.position.x+=2;const moved=bounds(cover());
      e.rebuildYard();await new Promise(r=>setTimeout(r,1200));const rebuilt=bounds(cover());
      const singleCover=grill.children.filter(c=>c.userData.rearGrillCover).length===1;
      grill.position.x-=2;e.rebuildYard();await new Promise(r=>setTimeout(r,1200));const restored=bounds(cover());
      const materialUnchanged=materials.every(({m,uuid,color,roughness,metalness})=>m.uuid===uuid&&m.color?.getHex()===color&&m.roughness===roughness&&m.metalness===metalness);
      e.setYardEditing(true);await new Promise(r=>setTimeout(r,1200));
      const item=e.getYardItems().find(i=>i.label==='Rear porch detail'&&!i.isClone);
      const porch=e.getYardPickables().find(o=>o.userData.yardKey===item.key);
      const panes=porch.getObjectByName('rear-porch-glazing'),cabinet=porch.getObjectByName('rear-porch-stainless-cabinet');
      const paneBefore=bounds(panes);porch.position.x+=1.5;const paneMoved=bounds(panes);
      const editorCoupled=panes.parent===porch&&cabinet.parent===porch;
      e.setYardEditing(false);await new Promise(r=>setTimeout(r,1200));
      return {before,moved,rebuilt,restored,shift:moved.min[0]-before.min[0],rebuildShift:rebuilt.min[0]-before.min[0],restoreDelta:restored.min.map((v,i)=>v-before.min[i]),singleCover,sourceHidden:source.visible===false,materialUnchanged,coverDisposed,glassDisposed,editorCoupled,editorPaneShift:paneMoved.min[0]-paneBefore.min[0]};
    });
    report.errors=errors;fs.writeFileSync(__dirname+'/porch-r2-verify.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
    if(Math.abs(report.shift-2)>1e-7||Math.abs(report.rebuildShift-2)>1e-7||report.restoreDelta.some(v=>Math.abs(v)>1e-7)||!report.singleCover||!report.materialUnchanged||!report.coverDisposed||!report.glassDisposed||!report.editorCoupled||Math.abs(report.editorPaneShift-1.5)>1e-7||errors.length)throw Error('Porch lifecycle verification failed');
  }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
