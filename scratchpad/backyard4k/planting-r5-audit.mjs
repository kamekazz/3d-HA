import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import crypto from 'node:crypto';
import {pathToFileURL} from 'node:url';
const THREE=await import(pathToFileURL(path.join(os.tmpdir(),'planting-r4-three.mjs')));
const root=process.cwd(),dir=path.join(root,'scratchpad/backyard4k');
const source=fs.readFileSync(path.join(root,'frontend/js/environment.js'),'utf8');
const before=fs.readFileSync(path.join(dir,'planting-r5-before.js'),'utf8');
const after=source.slice(source.indexOf('function addRearPlantingDetail('),source.indexOf('// Imported site-pad surgery'));
const helper=name=>source.slice(source.indexOf('function '+name+'('),source.indexOf('\n}',source.indexOf('function '+name+'('))+2);
function run(code){
  const f=new Function('THREE',`${helper('mulberry32')}\n${helper('paint')}\n
    const items=[],bedsAudit=[]; let curItem=-1;
    const scoped=(kind,label,fn)=>(...args)=>{curItem=items.length;items.push({kind,label,geos:[]});fn(...args);curItem=-1;};
    const props={push(g){items[curItem].geos.push(g);}};
    const addBedPoly=(...args)=>{items.push({kind:'bed',label:'Rock bed',geos:[]});bedsAudit.push(args.slice(1));};
    const addCobbleRun=(...args)=>{items.push({kind:'edge',label:'Cobble run',geos:[]});bedsAudit.push(args.slice(1));};
    ${code}\naddRearPlantingDetail({lo:.12},[],[],props);return {items,bedsAudit};`);
  const result=f(THREE);
  return {beds:result.bedsAudit,items:result.items.map(item=>{
    const hash=crypto.createHash('sha256'),box=new THREE.Box3(),foliage=new THREE.Box3();let bytes=0,flatBytes=0,triangles=0;
    for(const g of item.geos){
      g.computeBoundingBox();box.union(g.boundingBox);if(g.userData.rearFoliage)foliage.union(g.boundingBox);
      for(const [name,a] of Object.entries(g.attributes)){hash.update(name);hash.update(Buffer.from(a.array.buffer));bytes+=a.array.byteLength;}
      if(g.index){hash.update(Buffer.from(g.index.array.buffer));bytes+=g.index.array.byteLength;}
      const vertices=g.index?.count||g.attributes.position.count;triangles+=vertices/3;
      flatBytes+=vertices*Object.values(g.attributes).reduce((n,a)=>n+a.itemSize*4,0);
    }
    const [x,,z]=item.authoredPivot;
    return {label:item.label,pivot:item.authoredPivot,key:`${item.kind}:${Math.round(x*10)}:${Math.round(z*10)}`,hash:hash.digest('hex'),bytes,flatBytes,triangles,
      bounds:box.isEmpty()?null:[box.min.toArray(),box.max.toArray()],foliageBounds:foliage.isEmpty()?null:[foliage.min.toArray(),foliage.max.toArray()]};
  })};
}
const old=run(before),current=run(after),changed=[];
if(JSON.stringify(old.beds)!==JSON.stringify(current.beds))throw Error('Bed calls changed');
for(let i=0;i<old.items.length;i++){
  const a=old.items[i],b=current.items[i];
  if(a.key!==b.key||JSON.stringify(a.pivot)!==JSON.stringify(b.pivot))throw Error('Identity changed '+i);
  if(a.hash!==b.hash){changed.push(b.key);if(b.flatBytes>300000)throw Error('Piece exceeds 300 KB '+b.key);}
}
if(changed.length)throw Error('Existing geometry changed '+JSON.stringify(changed));
if(current.items.length!==old.items.length+1)throw Error('Expected one new tree');
const tree=current.items.at(-1);
const textureBytes=fs.statSync(path.join(root,'frontend/textures/rear-conifer-spray.png')).size;
if(tree.flatBytes+textureBytes>300000 || tree.bounds[1][2]>=0)throw Error('Budget or rear bounds failed');
const repeat=run(after);
if(JSON.stringify(current)!==JSON.stringify(repeat))throw Error('Non-deterministic planting');
const result={protocol:'Offline execution using exact Three.js r160; bed factories recorded as calls, no browser/capture',itemCount:current.items.length,identitiesUnchanged:true,bedCallsUnchanged:true,changed,unchangedGeometryCount:old.items.length-changed.length,newKeys:[tree.key],deterministic:true,textureBytes,pieceTotalBytes:tree.flatBytes+textureBytes,items:current.items};
fs.writeFileSync(path.join(dir,'planting-r5-audit.json'),JSON.stringify(result,null,2));
console.log(JSON.stringify({...result,items:current.items.slice(-1)},null,2));
