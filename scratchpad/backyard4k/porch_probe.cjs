const fs=require('fs');
const {chromium}=require('C:/Users/Manuel/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
(async()=>{const b=await chromium.launch({channel:'chrome',headless:true,args:['--use-gl=angle','--enable-unsafe-swiftshader']});try{
const p=await b.newPage({viewport:{width:1200,height:800}});await p.goto('http://127.0.0.1:5001',{waitUntil:'load',timeout:90000});
await p.waitForFunction(()=>!!window.__scene3d,{}, {timeout:90000});
await p.waitForFunction(async()=>!!(await import('/js/house.js')).getShellRoot(),{}, {timeout:90000});
await p.waitForTimeout(8000);
const r=await p.evaluate(async()=>{const T=await import('three'),h=await import('/js/house.js');const s=h.getShellRoot();s.updateWorldMatrix(true,true);const meshes=[];
s.traverse(o=>{if(!o.isMesh)return;const q=new T.Box3().setFromObject(o);if(q.min.z<-20 && q.max.y>2&&q.min.y<12)meshes.push({name:o.name,min:q.min.toArray(),max:q.max.toArray(),mat:Array.isArray(o.material)?o.material.map(m=>m.name):o.material.name});});
const ray=new T.Raycaster(),hits=[];for(let y of [2.7,3,4,6,8,9,10])for(let x=-6;x<=20;x+=.5){ray.set(new T.Vector3(x,y,-30),new T.Vector3(0,0,1));let v=ray.intersectObject(s,true).find(v=>v.object.visible);if(v)hits.push({x,y,p:v.point.toArray().map(n=>+n.toFixed(3)),name:v.object.name,mat:v.object.material?.name});}
const glass=[];s.traverse(o=>{if(o.name!=='mesh_8')return;const a=o.geometry.attributes.position,v=new T.Vector3();for(let i=0;i<a.count;i++){v.fromBufferAttribute(a,i).applyMatrix4(o.matrixWorld);if(v.z< -24&&v.x>9&&v.x<17&&v.y<12)glass.push(v.toArray().map(n=>+n.toFixed(4)));}});
return {meshes,hits,glass};});fs.writeFileSync(__dirname+'/porch_probe.json',JSON.stringify(r,null,2));console.log(JSON.stringify({meshes:r.meshes,glass:r.glass}));
}finally{await b.close();}})().catch(e=>{console.error(e);process.exitCode=1});
