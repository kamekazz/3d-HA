from pathlib import Path
p=Path('frontend/js/environment.js')
s=p.read_text(encoding='utf-8');a=s.index('  const limb = (a, b, r0, r1, tint, bucket) => {',s.index('function addRearLakeDetail'));b=s.index('  // Unequal gaps, diameters',a)
new='''  // Real swept bark surfaces retain their UVs through the editable buckets.
  // One physical tile is 1 x 2 metres; circumference and length are in feet.
  const branch = (points, r0, r1, bucket, tint = 0xffffff) => {
    const curve=new THREE.CatmullRomCurve3(points.map(p=>new THREE.Vector3(...p)));
    const length=curve.getLength(), rings=Math.max(5,Math.ceil(length*2.6));
    const sides=r0>.3?28:10,frames=curve.computeFrenetFrames(rings,false),p=[],uv=[],idx=[];
    const phase=rng()*6.28;
    for(let i=0;i<=rings;i++) {
      const t=i/rings,c=curve.getPointAt(t),base=r0*Math.pow(1-t,.88)+r1*t;
      for(let j=0;j<=sides;j++) {
        const a=j/sides*Math.PI*2;
        const ridges=1+.065*Math.sin(a*7+t*4+phase)+.028*Math.sin(a*17-t*7);
        const flare=1+Math.exp(-t*length*2)*Math.max(0,Math.sin(a*5+phase))*.20;
        const r=base*ridges*flare,n=frames.normals[i],bn=frames.binormals[i];
        p.push(c.x+r*(Math.cos(a)*n.x+Math.sin(a)*bn.x),c.y+r*(Math.cos(a)*n.y+Math.sin(a)*bn.y),c.z+r*(Math.cos(a)*n.z+Math.sin(a)*bn.z));
        uv.push(j/sides*Math.PI*2*r0/3.28084,t*length/6.56168);
        if(i<rings&&j<sides){const k=i*(sides+1)+j;idx.push(k,k+sides+1,k+1,k+1,k+sides+1,k+sides+2);}
      }
    }
    const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(p,3));
    g.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));g.setIndex(idx);g.computeVertexNormals();
    paint(g,color(tint));if(bucket===masses)g.userData.rearBark=true;bucket.push(g);
  };
  const limb=(a,b,r0,r1,tint,bucket)=>branch([a,b],r0,r1,bucket,bucket===masses?0xffffff:tint);
  // Leaves form small botanical sprays around branch tips. Their curved ovate
  // outline and lighter midrib remove the old triangular confetti silhouette.
  const leafCloud = (cx, cy, cz, rx, ry, rz, count, positions, colors, scale = 1) => {
    const clusterCount=Math.ceil(count/38);
    for(let cl=0;cl<clusterCount;cl++) {
      let dx,dy,dz;do {dx=rng()*2-1;dy=rng()*2-1;dz=rng()*2-1;}while(dx*dx+dy*dy+dz*dz>1);
      const center=new THREE.Vector3(cx+dx*rx,cy+dy*ry,cz+dz*rz);
      const hue=.285+rng()*.035,luminance=.185+rng()*.055;
      const axis=new THREE.Vector3(rng()-.5,.25+rng()*.5,rng()-.5).normalize();
      for(let n=0;n<38&&cl*38+n<count;n++) {
        const c=center.clone().addScaledVector(axis,(rng()-.5)*1.65);
        c.add(new THREE.Vector3((rng()-.5)*1.2,(rng()-.5)*.7,(rng()-.5)*1.2));
        const size=(.22+rng()*.13)*scale;
        const q=new THREE.Quaternion().setFromEuler(new THREE.Euler((rng()-.5)*1.4,rng()*6.28,(rng()-.5)*1.2));
        const verts=[[-size,0,0],[-size*.45,-size*.08,size*.39],[size*.28,-size*.10,size*.42],
          [size,0,0],[size*.28,-size*.08,-size*.42],[-size*.45,-size*.06,-size*.39],[0,size*.11,0]]
          .map(v=>new THREE.Vector3(...v).applyQuaternion(q).add(c));
        const tint=new THREE.Color().setHSL(hue,.24+rng()*.06,luminance*(.92+rng()*.16),THREE.SRGBColorSpace);
        for(let edge=0;edge<6;edge++)for(const k of [edge,(edge+1)%6,6,6,(edge+1)%6,edge]) {
          positions.push(...verts[k].toArray());const light=k===6?1.10:1;
          colors.push(tint.r*light,tint.g*light,tint.b*light);
        }
      }
    }
  };
  const matureTree = (x, z, radius, height, lean) => localItem('tree', 'Rear mature broadleaf', () => {
    const y=bedY-.20,pos=[],col=[],phase=rng()*6.28;
    const spine=Array.from({length:7},(_,i)=>[x+lean*i/6+Math.sin(i*1.25+phase)*radius*.30,y+height*i/6,z+Math.sin(i*.85)*radius*.5]);
    spine[0]=[x,y,z];branch(spine,radius,radius*.045,masses);
    for(let i=0;i<5;i++) {
      const a=phase+i*1.256+(rng()-.5)*.5,r=radius*(1.7+rng());
      branch([[x,y+.52,z],[x+Math.cos(a)*r*.5,y+.06,z+Math.sin(a)*r*.5],[x+Math.cos(a)*r,y-.09,z+Math.sin(a)*r]],radius*.32,.013,masses);
    }
    // Scaffold forks are visible below the crown. Their joins, rise and length
    // vary by tree; no common hanging level can make a flat foliage ceiling.
    const lowJoin=radius>.4?(.17+rng()*.16):(.34+rng()*.15);
    for(let b=0;b<8;b++) {
      const angle=phase+b*2.399+(rng()-.5)*.6,join=lowJoin+b*.063;
      const origin=[x+lean*join,y+height*join,z+Math.sin(join*5)*radius*.4];
      const reach=(radius>.4?5:3)+rng()*5;
      const rise=2.8+rng()*6;
      const tip=[origin[0]+Math.cos(angle)*reach,origin[1]+rise,origin[2]+Math.sin(angle)*reach];
      const bend=[origin[0]+Math.cos(angle)*reach*.42,origin[1]+rise*.22,origin[2]+Math.sin(angle)*reach*.40];
      const thick=radius*(b<2?.46:.32);
      branch([origin,bend,tip],thick,.045,masses);
      for(let t=0;t<5;t++) {
        const ta=angle+(t-2)*.50,j=.46+t*.12;
        const from=origin.map((v,i)=>v+(tip[i]-v)*j);
        const end=[from[0]+Math.cos(ta)*(2+rng()*3),from[1]+.7+rng()*2.7,from[2]+Math.sin(ta)*(2+rng()*3)];
        branch([from,[(from[0]+end[0])*.5,from[1]+.35,(from[2]+end[2])*.5],end],.075,.009,masses);
        leafCloud(...end,2.4+rng()*1.4,1.1+rng()*1.4,2+rng()*1.2,360,pos,col,.50);
      }
    }
    // The reference has a low, dense western thicket and a larger eastern
    // water window, with a few pendulous shoots framing its upper edge.
    if(x<mid-9)for(let b=0;b<3;b++) {
      const end=[x-2+rng()*5,y+4+rng()*6,z-2-rng()*6];
      branch([[x,y+height*.30,z],[x-1,y+7,z-3],end],radius*.16,.012,masses);
      leafCloud(...end,3,2.3,2.8,1000,pos,col,.46);
    }
    if(radius>.45&&rng()<.60) {
      const end=[x+(rng()-.5)*8,y+7+rng()*8,z-5-rng()*7];
      branch([[x+lean*.4,y+height*.42,z],[end[0],end[1]+3,end[2]+2],end],radius*.20,.015,masses);
      leafCloud(...end,3.2,2.5,2.4,1200,pos,col,.49);
    }
    const g=new THREE.BufferGeometry();
    g.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));
    g.setAttribute('color',new THREE.Float32BufferAttribute(col,3));
    g.setAttribute('uv',new THREE.Float32BufferAttribute(new Float32Array(pos.length/3*2),2));
    g.computeVertexNormals();g.userData.rearFoliage=true;props.push(g);
  });
'''
s=s[:a]+new+s[b:];p.write_text(s,encoding='utf-8')
