from pathlib import Path
p=Path('frontend/js/environment.js');s=p.read_text();a=s.index('function addRearLakeDetail(');b=s.index('\nfunction addBackYard(',a);f=s[a:b]
needle="  localItem('shore', 'Rear far bank and woodland', () => {"
insert='''  // Visible daytime housings and the hanging feeder in reference 11. They
  // introduce no light source and do not override HA fixture state.
  for(const offset of [-7,13]) localItem('prop','Rear shore path-light housing',()=>{
    const x=mid+offset,z=lawnEdge(x)-.85;
    limb([x,bedY,z],[x,bedY+1.35,z],.065,.075,0x202326,props);
    const head=new THREE.CylinderGeometry(.14,.13,.26,16);head.translate(x,bedY+1.40,z);
    paint(head,color(0x181d20));props.push(head);
    const cap=new THREE.CylinderGeometry(.165,.165,.045,18);cap.translate(x,bedY+1.55,z);
    paint(cap,color(0x292c2c));props.push(cap);
  });
  localItem('prop','Rear hanging bird feeder',()=>{
    const x=mid-8,z=shore(x)+4;
    const curve=new THREE.CatmullRomCurve3([[x,bedY,z],[x,bedY+4.5,z],[x+.15,bedY+4.9,z],[x+.65,bedY+4.9,z],[x+.85,bedY+4.5,z]].map(p=>new THREE.Vector3(...p)));
    const hook=new THREE.TubeGeometry(curve,30,.018,6,false);paint(hook,color(0x333832));props.push(hook);
    limb([x+.85,bedY+4.5,z],[x+.85,bedY+3.7,z],.01,.01,0x30362c,props);
    const body=new THREE.CylinderGeometry(.15,.15,.65,12);body.translate(x+.85,bedY+3.4,z);paint(body,color(0xb0b5a1));props.push(body);
    for(const yy of [bedY+3.02,bedY+3.76]){const tray=new THREE.CylinderGeometry(.26,.26,.06,14);tray.translate(x+.85,yy,z);paint(tray,color(0x384638));props.push(tray);}
  });
  localItem('shore','Rear gravel fallen leaves',()=>{
    for(let i=0;i<200;i++) {
      const x=nearX0+rng()*(nearX1-nearX0),z=lawnEdge(x)-rng()*(lawnEdge(x)-shore(x)-3),size=.10+rng()*.14;
      const g=new THREE.CircleGeometry(size,5);g.rotateX(-Math.PI/2);g.scale(1,.5,.55);g.rotateY(rng()*6.28);g.translate(x,bedY+.008,z);
      paint(g,color(rng()<.5?0x796349:0x9c885e));beds.push(g);
    }
  });
'''
f=f.replace(needle,insert+needle)
f=f.replace('// Narrower leaves have six perimeter points and a raised midrib, rather than a broad diamond.','// Narrow leaves have a raised midrib.')
p.write_text(s[:a]+f+s[b:])
