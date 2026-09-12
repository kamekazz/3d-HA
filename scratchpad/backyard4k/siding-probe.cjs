const fs=require('fs');
const {chromium}=require('C:/Users/Manuel/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
(async()=>{
 const b=await chromium.launch({channel:'chrome',headless:true,args:['--use-gl=angle','--enable-unsafe-swiftshader']});
 const p=await b.newPage(); await p.goto('http://127.0.0.1:5001',{waitUntil:'load'});
 await p.waitForFunction(()=>window.__scene3d);await p.waitForTimeout(7000);
 const d=await p.evaluate(async()=>{
  const THREE=await import('three'); const shell=(await import('/js/house.js')).getShellRoot();shell.updateWorldMatrix(true,true);
  const meshes=[];shell.traverse(m=>{if(!m.isMesh)return; const g=m.geometry,a=g.attributes.position,idx=g.index,tri=[];
   for(let k=0;k<(idx?.count||a.count);k+=3){const ids=[0,1,2].map(j=>idx?idx.getX(k+j):k+j),v=ids.map(i=>new THREE.Vector3().fromBufferAttribute(a,i).applyMatrix4(m.matrixWorld));
    if(v.some(p=>p.z> -6)||v.every(p=>p.y<2))continue;
    const n=v[1].clone().sub(v[0]).cross(v[2].clone().sub(v[0])).normalize();
    if(n.z>-.25)continue;
    tri.push({k,v:v.map(v=>v.toArray()),n:n.toArray(),uv:ids.map(i=>g.attributes.uv?[g.attributes.uv.getX(i),g.attributes.uv.getY(i)]:null)});
   } if(tri.length)meshes.push({name:m.name,mat:m.material.name,color:m.material.color?.getHexString(),map:m.material.map?.image?.src,tri});
  });return meshes;
 });fs.writeFileSync(__dirname+'/siding-probe.json',JSON.stringify(d)); console.log(d.map(m=>({name:m.name,mat:m.mat,count:m.tri.length})));await b.close();
})().catch(e=>{console.error(e);process.exitCode=1});
