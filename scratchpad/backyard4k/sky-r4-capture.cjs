/* Capture the real app using roomkit/shot.py's exact camera setup.
   node workflow_capture.cjs <round> [pose-name ...]
   Optional --pose-file file.json supplies alternate exact registered poses. */
const fs = require('fs');
const path = require('path');
const {chromium} = require('C:/Users/Manuel/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const here = __dirname, root = path.resolve(here, '../..');
const argv = process.argv.slice(2), round = argv.shift() || 'baseline';
let poseFile = path.join(here, 'workflow_poses.json');
const fi = argv.indexOf('--pose-file');
if(fi >= 0) poseFile = path.resolve(argv.splice(fi, 2)[1]);
let lightFile=null;
const li=argv.indexOf('--light-file');
if(li>=0)lightFile=path.resolve(argv.splice(li,2)[1]);
const poses = JSON.parse(fs.readFileSync(poseFile, 'utf8').replace(/^\uFEFF/, ''));
const selected = argv.length ? argv : Object.keys(poses);
const shot = fs.readFileSync(path.join(root, 'tools/roomkit/shot.py'), 'utf8');
const setup = shot.match(/SETUP_JS = """([\s\S]*?)"""/)[1];
const ready = shot.match(/READY_JS = """([\s\S]*?)"""/)[1];
const base = process.env.ROOMKIT_BASE || 'http://127.0.0.1:5001';
const light = lightFile ? JSON.parse(fs.readFileSync(lightFile,'utf8').replace(/^\uFEFF/,''))
  : {elevation:42,azimuth:335,condition:'sunny'};
function progress() {}
(async()=>{
  const browser = await chromium.launch({channel:'chrome',headless:true,args:[
    '--use-gl=angle','--enable-unsafe-swiftshader','--hide-scrollbars',
    '--disable-background-timer-throttling','--disable-renderer-backgrounding']});
  try {
    let page;
    for (const name of selected) {
      const pose = poses[name] || (name==='photo09_sun155' && poses.photo09); if(!pose) throw Error('Unknown pose: '+name);
      const outDir = path.join(here,'renders',round); fs.mkdirSync(outDir,{recursive:true});
      const out = path.join(outDir,name+'.png');
      progress('Capturing '+round, name+' · native '+pose.size.join(' × ')+' · rear daylight');
      page ||= await browser.newPage({viewport:{width:pose.size[0],height:pose.size[1]},deviceScaleFactor:1});
      const errors=[],consoleErrors=[],requestsFailed=[];
      page.on('pageerror',e=>errors.push(String(e)));
      page.on('console',m=>{if(m.type()==='error') consoleErrors.push(m.text())});
      page.on('requestfailed',r=>requestsFailed.push({url:r.url(),failure:r.failure()}));
      if(name===selected[0]) await page.goto(base,{waitUntil:'load',timeout:90000});
      await page.waitForFunction(()=>!!window.__scene3d,{},{timeout:60000});
      await page.waitForTimeout(3500);
      await page.evaluate(()=>window.__scene3d.camera.up.set(0,1,0));
      const captureLight=name==='photo09_sun155'?{...light,azimuth:155}:light;
      const options={pose,level:'all',light:captureLight,markers:false,cutaway:false,exteriorsOn:false};
      await page.evaluate(`(${setup})(${JSON.stringify(options)})`);
      let loaded;
      for(let i=0;i<80;i++) { loaded=await page.evaluate(`(${ready})()`); if(loaded.total>0&&loaded.loaded>=loaded.total)break; await page.waitForTimeout(250); }
      await page.waitForTimeout(1600);
      await page.evaluate(`(${setup})(${JSON.stringify(options)})`);
      await page.waitForTimeout(500);
      const state = await page.evaluate(async (capturePose)=>{
        const {camera,controls,renderer,scene}=window.__scene3d;
        if(capturePose.roll){
          const THREE=await import('three');
          const forward=controls.target.clone().sub(camera.position).normalize();
          const right=forward.clone().cross(new THREE.Vector3(0,1,0)).normalize();
          const up=right.clone().cross(forward);
          camera.up.copy(up.multiplyScalar(Math.cos(capturePose.roll)))
            .addScaledVector(right,-Math.sin(capturePose.roll));
          camera.lookAt(controls.target);
        }
        window.__cutaway?.settle(); renderer.render(scene,camera);
        const env=await import('/js/environment.js');
        const house=await import('/js/house.js');
        const THREE=await import('three');
        const frontItems=env.getYardItems().filter(i=>i.pivot[2]>=0).map(i=>({key:i.key,kind:i.kind,label:i.label,pivot:i.pivot,edit:i.edit}));
        let frontCount=0,frontXor=0,frontSum=0;
        env.getEnvironmentRoot().updateWorldMatrix(true,true);
        env.getEnvironmentRoot().traverse(o=>{
          const g=o.geometry;if(!g?.attributes?.position||!o.isMesh)return;
          if(o.isInstancedMesh){
            o.computeBoundingBox();
            if(o.boundingBox.clone().applyMatrix4(o.matrixWorld).max.z<0)return;
          }
          const p=g.attributes.position,idx=g.index;
          const matrices=[];
          if(o.isInstancedMesh){
            for(let n=0;n<o.count;n++){
              const im=new THREE.Matrix4();o.getMatrixAt(n,im);
              matrices.push(o.matrixWorld.clone().multiply(im).elements);
            }
          }else matrices.push(o.matrixWorld.elements);
          for(const m of matrices){
          for(let k=0;k<(idx?.count||p.count);k+=3){
            const ids=[0,1,2].map(t=>idx?idx.getX(k+t):k+t);
            if(ids.some(i=>m[2]*p.getX(i)+m[6]*p.getY(i)+m[10]*p.getZ(i)+m[14]<0))continue;
            let hash=2166136261;
            const mix=v=>{hash=Math.imul(hash^(Math.round(v*100000)|0),16777619)>>>0;};
            for(const i of ids)for(const name of ['position','normal','color','uv']){
              const at=g.attributes[name];if(at)for(let a=0;a<at.itemSize;a++)mix(at.array[i*at.itemSize+a]);
            }
            for(const v of m)mix(v);
            frontCount++;frontXor=(frontXor^hash)>>>0;frontSum=(frontSum+hash)>>>0;
          }
          }
        });
        const b=house.getBuildingBox();
        return {position:camera.position.toArray(),target:controls.target.toArray(),up:camera.up.toArray(),
          fov:camera.fov,aspect:camera.aspect,view:camera.view,
          canvas:[renderer.domElement.width,renderer.domElement.height],
          renderInfo:JSON.parse(JSON.stringify(renderer.info.render)),
          shadowMap:{enabled:renderer.shadowMap.enabled,type:renderer.shadowMap.type},
          buildingBox:b?{min:b.min.toArray(),max:b.max.toArray()}:null,
          frontGeometry:{selection:'environment triangles with every world-space vertex z >= 0',triangles:frontCount,xor:frontXor,sum:frontSum},frontItems};
      },pose);
      await page.screenshot({path:out,animations:'disabled'});
      const report={round,name,url:base,pose,light:captureLight,level:'all',cutaway:false,markers:false,
        captured:new Date().toISOString(),loaded,state,errors,consoleErrors,requestsFailed,out};
      fs.writeFileSync(path.join(outDir,name+'.json'),JSON.stringify(report,null,2));
      console.log(JSON.stringify({name,out,errors:errors.length,loaded,position:state.position,shadowMap:state.shadowMap,frontGeometry:state.frontGeometry}));
      const renderErrors=consoleErrors.filter(e=>/ReferenceError|TypeError|SyntaxError|THREE\.WebGLProgram|mergeGeometries|Error creating WebGL/i.test(e));
      if(errors.length || renderErrors.length || !loaded?.total || loaded.loaded < loaded.total) {
        throw Error('Capture rejected; see diagnostic JSON. '+[...errors,...renderErrors].join(' | '));
      }

    }
    progress('Render capture complete',round+' · '+selected.length+' camera views');
  } finally { await browser.close(); }
})().catch(e=>{progress('Capture needs attention',String(e));console.error(e);process.exitCode=1;});


