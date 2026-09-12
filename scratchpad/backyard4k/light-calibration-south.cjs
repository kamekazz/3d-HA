const fs=require('fs');
const {chromium}=require('C:/Users/Manuel/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const shot=fs.readFileSync('tools/roomkit/shot.py','utf8'),setup=shot.match(/SETUP_JS = """([\s\S]*?)"""/)[1],ready=shot.match(/READY_JS = """([\s\S]*?)"""/)[1];
const pose=JSON.parse(fs.readFileSync('scratchpad/backyard4k/elevation_poses.json','utf8')).photo09;pose.size=[1200,900];
(async()=>{const b=await chromium.launch({channel:'chrome',headless:true,args:['--use-gl=angle','--enable-unsafe-swiftshader','--hide-scrollbars','--disable-background-timer-throttling','--disable-renderer-backgrounding']});try{
const p=await b.newPage({viewport:{width:1200,height:900}}),errors=[];p.on('pageerror',e=>errors.push(String(e)));
await p.goto('http://127.0.0.1:5001',{waitUntil:'load',timeout:90000});await p.waitForFunction(()=>window.__scene3d);await p.waitForTimeout(3500);
for(const light of [{elevation:35,azimuth:180,condition:'sunny'},{elevation:30,azimuth:195,condition:'sunny'},{elevation:25,azimuth:180,condition:'sunny'}]){
const options={pose,level:'all',light,markers:false,cutaway:false,exteriorsOn:false};await p.evaluate(`(${setup})(${JSON.stringify(options)})`);
for(let i=0;i<80;i++){const r=await p.evaluate(`(${ready})()`);if(r.total>0&&r.loaded>=r.total)break;await p.waitForTimeout(250);}
await p.waitForTimeout(2200);await p.evaluate(`(${setup})(${JSON.stringify(options)})`);await p.waitForTimeout(500);await p.evaluate(async()=>{(await import('/js/daylight.js')).settleDaylight();});
await p.evaluate(()=>{const {renderer,scene,camera}=window.__scene3d;renderer.render(scene,camera)});
const file=`scratchpad/backyard4k/light-cal-${light.azimuth}-${light.elevation}-${light.condition}.png`;await p.screenshot({path:file});console.log(JSON.stringify({file,light,errors}));
}
}finally{await b.close()}})().catch(e=>{console.error(e);process.exitCode=1});

