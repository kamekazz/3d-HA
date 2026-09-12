const fs=require('fs');
const {chromium}=require('C:/Users/Manuel/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
(async()=>{const b=await chromium.launch({channel:'chrome',headless:true,args:['--use-gl=angle','--enable-unsafe-swiftshader']});try{
const p=await b.newPage({viewport:{width:1000,height:750}});await p.goto('http://127.0.0.1:5001',{waitUntil:'load',timeout:90000});
await p.waitForFunction(async()=>!!(await import('/js/house.js')).getShellRoot(),{}, {timeout:90000});await p.waitForTimeout(5000);
const r=await p.evaluate(async()=>{const T=await import('three'),h=await import('/js/house.js'),s=h.getShellRoot();s.updateWorldMatrix(true,true);const triangles=[],ray=new T.Raycaster(),hits=[];
s.traverse(o=>{if(!o.isMesh)return;const g=o.geometry,at=g.attributes.position,idx=g.index;for(let k=0;k<(idx?.count||at.count);k+=3){let v=[0,1,2].map(j=>new T.Vector3().fromBufferAttribute(at,idx?idx.getX(k+j):k+j).applyMatrix4(o.matrixWorld));
if(v.every(v=>v.y<2.3&&v.y>-.5)&&v.some(v=>v.z< -10)&&v.some(v=>v.y>1.9))triangles.push({mesh:o.name,k,material:Array.isArray(o.material)?o.material.map(m=>m.name):o.material.name,vertices:v.map(v=>v.toArray().map(a=>+a.toFixed(4)))});}});
for(let z=-55;z<=-25;z+=2)for(let x=5;x<=25;x+=2){ray.set(new T.Vector3(x,3.1,z),new T.Vector3(0,-1,0));const v=ray.intersectObject(s,true)[0];if(v)hits.push({x,z,y:+v.point.y.toFixed(4),mesh:v.object.name,face:v.faceIndex});}
return{triangles,hits};});fs.writeFileSync(__dirname+'/ground-probe.json',JSON.stringify(r,null,2));console.log(JSON.stringify({triangles:r.triangles,hits:r.hits.filter(v=>v.x===11)}));
}finally{await b.close();}})().catch(e=>{console.error(e);process.exitCode=1});
