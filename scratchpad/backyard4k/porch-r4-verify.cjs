const fs=require('fs');
const {chromium}=require('C:/Users/Manuel/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
(async()=>{
  const browser=await chromium.launch({channel:'chrome',headless:true,args:['--use-gl=angle','--enable-unsafe-swiftshader']});
  try{
    const page=await browser.newPage({viewport:{width:900,height:700}}),errors=[];
    page.on('pageerror',e=>errors.push(String(e)));
    await page.goto('http://127.0.0.1:5001',{waitUntil:'load',timeout:90000});
    await page.waitForFunction(async()=>{
      const e=await import('/js/environment.js');
      return !!e.getEnvironmentRoot()?.getObjectByName('rear-porch-workstation');
    },{},{timeout:90000});
    await page.waitForTimeout(5000);
    const report=await page.evaluate(async()=>{
      const T=await import('three'),e=await import('/js/environment.js'),h=await import('/js/house.js'),{objects3d}=await import('/js/objects.js');
      const root=()=>e.getEnvironmentRoot(),get=n=>root().getObjectByName(n);
      const bounds=o=>{o.updateWorldMatrix(true,true);const b=new T.Box3().setFromObject(o);return {min:b.min.toArray(),max:b.max.toArray(),size:b.getSize(new T.Vector3()).toArray()};};
      const shellMaterials=[];h.getShellRoot().traverse(o=>{if(o.isMesh)for(const m of Array.isArray(o.material)?o.material:[o.material])shellMaterials.push({m,color:m.color?.getHex(),roughness:m.roughness,metalness:m.metalness});});
      const cabinet=get('rear-porch-stainless-cabinet'),workstation=get('rear-porch-workstation');
      const counter=get('workstation-continuous-counter'),body=get('workstation-recessed-body');
      const box=get('rear-porch-weatherproof-wall-box');
      const initial={counter:bounds(counter),body:bounds(body),workstation:bounds(workstation),wallBox:bounds(box)};
      const front=new T.Vector3(0,0,-1).transformDirection(workstation.matrixWorld).toArray();
      const planter=[...objects3d.values()].find(o=>o.userData.name==='Backyard Planter Two');
      const planterBounds=planter?bounds(planter):null;
      const wb=new T.Box3(new T.Vector3(...initial.workstation.min),new T.Vector3(...initial.workstation.max));
      const pb=planterBounds?new T.Box3(new T.Vector3(...planterBounds.min),new T.Vector3(...planterBounds.max)):null;
      const parentCorrect=workstation.parent===cabinet&&box.parent===cabinet;
      const meshCallback=typeof body.onBeforeRender==='function';
      const envMapAssigned=!!counter.material.envMap;
      let steelDisposals=0,glassDisposals=0;
      counter.material.addEventListener('dispose',()=>steelDisposals++);
      get('rear-slider-reflective-pane').material.addEventListener('dispose',()=>glassDisposals++);
      e.setYardEditing(true);await new Promise(r=>setTimeout(r,1300));
      const item=e.getYardItems().find(i=>i.label==='Rear porch detail'&&!i.isClone);
      const owner=e.getYardPickables().find(o=>o.userData.yardKey===item.key);
      const editedWorkstation=owner.getObjectByName('rear-porch-workstation');
      const before=bounds(editedWorkstation);owner.position.x+=1.5;const moved=bounds(editedWorkstation);
      const editorCoupled=owner.getObjectByName('rear-porch-stainless-cabinet').parent===owner&&!!owner.getObjectByName('rear-porch-glazing');
      owner.position.x-=1.5;e.setYardEditing(false);await new Promise(r=>setTimeout(r,1300));
      e.rebuildYard();await new Promise(r=>setTimeout(r,1800));
      const rebuilt=bounds(get('workstation-continuous-counter'));
      return {initial,front,planterBounds,planterIntersectsWorkstation:pb?wb.intersectsBox(pb):null,parentCorrect,meshCallback,envMapAssigned,editorCoupled,editorShift:moved.min[0]-before.min[0],steelDisposals,glassDisposals,rebuilt,shellMaterialsUnchanged:shellMaterials.every(({m,color,roughness,metalness})=>m.color?.getHex()===color&&m.roughness===roughness&&m.metalness===metalness)};
    });
    report.errors=errors;fs.writeFileSync(__dirname+'/porch-r4-verify.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
    if(!report.parentCorrect||!report.editorCoupled||!report.envMapAssigned||Math.abs(report.editorShift-1.5)>1e-6||!report.steelDisposals||!report.glassDisposals||!report.shellMaterialsUnchanged||errors.length)throw Error('Porch R4 integration verification failed');
  }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
