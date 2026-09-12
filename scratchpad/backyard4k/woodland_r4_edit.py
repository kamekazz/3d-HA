from pathlib import Path
import json
p=Path('frontend/js/environment.js'); s=p.read_text(); start=s.index('  // Leaves form small botanical sprays',s.index('function addRearLakeDetail')); end=s.index('  // Unequal gaps, diameters',start)
s=s[:start]+'''  // A crown is many overlapping twig sprays, with shaded leaves inside and
  // sunlit tips outside. Each curved ovate leaf has one six-triangle surface;
  // DoubleSide supplies its underside without duplicating all its vertices.
  const leafCloud = (cx, cy, cz, rx, ry, rz, count, positions, colors, scale = 1) => {
    const clusterCount=Math.ceil(count/28); positions.leafNormals ||= [];
    const indices=[0,1,6,1,2,6,2,3,6,3,4,6,4,5,6,5,0,6];
    for(let cl=0;cl<clusterCount;cl++) {
      let dx,dy,dz;do {dx=rng()*2-1;dy=rng()*2-1;dz=rng()*2-1;}while(dx*dx+dy*dy+dz*dz>1);
      const center=new THREE.Vector3(cx+dx*rx,cy+dy*ry,cz+dz*rz);
      const depth=Math.sqrt(dx*dx+dy*dy+dz*dz);
      const hue=.265+rng()*.06,luminance=.13+depth*.075+rng()*.045;
      const axis=new THREE.Vector3(rng()-.5,.2+rng()*.4,rng()-.5).normalize();
      for(let n=0;n<28&&cl*28+n<count;n++) {
        const c=center.clone().addScaledVector(axis,(rng()-.5)*1.6);
        c.add(new THREE.Vector3((rng()-.5)*1.15,(rng()-.5)*.8,(rng()-.5)*1.15));
        const size=(.25+rng()*.18)*scale;
        const q=new THREE.Quaternion().setFromEuler(new THREE.Euler((rng()-.5)*2.1,rng()*6.28,(rng()-.5)*1.9));
        const local=[[-size,0,0],[-size*.47,-size*.09,size*.42],[size*.28,-size*.10,size*.45],
          [size,0,0],[size*.28,-size*.08,-size*.45],[-size*.47,-size*.06,-size*.42],[0,size*.105,0]];
        const verts=local.map(v=>new THREE.Vector3(...v).applyQuaternion(q).add(c));
        const normals=local.map(v=>new THREE.Vector3(v[0]/size*.16,1,v[2]/size*.42).normalize().applyQuaternion(q));
        const tint=new THREE.Color().setHSL(hue,.19+rng()*.14,luminance*(.88+rng()*.24),THREE.SRGBColorSpace);
        for(const k of indices) {
          positions.leafNormals.push(...normals[k].toArray());positions.push(...verts[k].toArray());
          const light=k===6?1.06:1;colors.push(tint.r*light,tint.g*light,tint.b*light);
        }
      }
    }
  };
  const matureTree = (x, z, radius, height, lean, authoredPivot) => localItem('tree', 'Rear mature broadleaf', () => {
    items[curItem].authoredPivot=authoredPivot;
    const y=bedY-.20,pos=[],col=[],phase=rng()*6.28;
    const spine=Array.from({length:7},(_,i)=>[x+lean*i/6+Math.sin(i*1.25+phase)*radius*.30,y+height*i/6,z+Math.sin(i*.85)*radius*.5]);
    spine[0]=[x,y,z];branch(spine,radius,radius*.045,masses);
    for(let i=0;i<5;i++) {
      const a=phase+i*1.256+(rng()-.5)*.5,r=radius*(1.7+rng());
      branch([[x,y+.52,z],[x+Math.cos(a)*r*.5,y+.06,z+Math.sin(a)*r*.5],[x+Math.cos(a)*r,y-.09,z+Math.sin(a)*r]],radius*.32,.013,masses);
    }
    const lowJoin=radius>.4?(.17+rng()*.12):(.34+rng()*.10);
    for(let b=0;b<9;b++) {
      const angle=phase+b*2.399+(rng()-.5)*.6,join=lowJoin+b*.060;
      const origin=[x+lean*join,y+height*join,z+Math.sin(join*5)*radius*.4];
      const reach=(radius>.4?6:4)+rng()*5, rise=2.8+rng()*6;
      const tip=[origin[0]+Math.cos(angle)*reach,origin[1]+rise,origin[2]+Math.sin(angle)*reach];
      const bend=[origin[0]+Math.cos(angle)*reach*.42,origin[1]+rise*.22,origin[2]+Math.sin(angle)*reach*.40];
      branch([origin,bend,tip],radius*(b<2?.46:.32),.035,masses);
      for(let t=0;t<5;t++) {
        const ta=angle+(t-2)*.50,j=.42+t*.13;
        const from=origin.map((v,i)=>v+(tip[i]-v)*j);
        const end=[from[0]+Math.cos(ta)*(2+rng()*3),from[1]+.7+rng()*2.7,from[2]+Math.sin(ta)*(2+rng()*3)];
        branch([from,[(from[0]+end[0])*.5,from[1]+.35,(from[2]+end[2])*.5],end],.075,.009,masses);
        leafCloud(...end,2.3+rng(),1.4+rng(),2.2+rng(),280,pos,col,.95);
      }
    }
    // Interlocking crown tiers enclose the site from ground and aerial views.
    // They continue the existing trunks upward, rather than forming a screen.
    for(let b=0;b<5;b++) {
      const a=phase+b*2.399,reach=3.5+rng()*4;
      const end=[x+lean+Math.cos(a)*reach,y+height*(.77+rng()*.20),z+Math.sin(a)*reach];
      const from=[x+lean*.65,y+height*.61,z];
      branch([from,[(from[0]+end[0])*.5,end[1]-3,(z+end[2])*.5],end],radius*.26,.025,masses);
      leafCloud(...end,4.6+rng()*1.8,3.5+rng()*1.4,4.4+rng()*1.4,1650,pos,col,1);
    }
    // The western side has low branches and a thick shaded understory; the
    // center/eastern water window remains below the spreading upper branches.
    for(let b=0;b<3;b++) {
      const end=[x+(b-1)*4.8+(rng()-.5)*3,y+9+rng()*5,z-1+(rng()-.5)*5];
      const origin=[x+lean*.27,y+height*(.20+rng()*.10),z];
      branch([origin,[(origin[0]+end[0])*.5,end[1]+1,(z+end[2])*.5],end],radius*.22,.025,masses);
      leafCloud(...end,4.6+rng(),2.5+rng(),3.4+rng(),1300,pos,col,.9);
    }
    if(x<mid-9)for(let b=0;b<3;b++) {
      const end=[x-2+rng()*5,y+3+rng()*4,z-1-rng()*4];
      branch([[x,y+height*.27,z],[x-1,y+7,z-3],end],radius*.16,.012,masses);
      leafCloud(...end,3.7,2.6,3,1000,pos,col,.8);
    }
    const g=new THREE.BufferGeometry();
    g.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));
    g.setAttribute('color',new THREE.Float32BufferAttribute(col,3));
    g.setAttribute('uv',new THREE.Float32BufferAttribute(new Float32Array(pos.length/3*2),2));
    g.setAttribute('normal',new THREE.Float32BufferAttribute(pos.leafNormals,3));
    g.userData.rearFoliage=true;g.userData.rearSingleLeafSurface=true;props.push(g);
  });
''' +s[end:]
pivots=json.loads(Path('scratchpad/backyard4k/rear-tree-pivots-r3.json').read_text())
s=s.replace('  for(const [offset,r,h,lean,dz] of [[-48', '  const rearTreePivots='+json.dumps([a['pivot'] for a in pivots])+';\n  let treeOrdinal=0;\n  for(const [offset,r,h,lean,dz] of [[-48',1)
s=s.replace('matureTree(x,shore(x)+2.5+dz,r,h,lean);','matureTree(x,shore(x)+2.5+dz,r,h,lean,rearTreePivots[treeOrdinal++]);',1)
s=s.replace('function measureItem(item, buckets) {','function measureItem(item, buckets) {\n  if(item.authoredPivot)return item.authoredPivot.slice();',1)
s=s.replace('rearFoliageMat=new THREE.MeshStandardMaterial({vertexColors:true,roughness:.95,metalness:0});','rearFoliageMat=new THREE.MeshStandardMaterial({vertexColors:true,roughness:.95,metalness:0,side:THREE.DoubleSide});',1)
# Far bank uses the same actual leaf geometry, so put it through rear foliage bucket.
s=s.replace('woodland.setAttribute(\'normal\',new THREE.Float32BufferAttribute(farPos.leafNormals,3)); leaves.push(woodland);',"woodland.setAttribute('normal',new THREE.Float32BufferAttribute(farPos.leafNormals,3)); woodland.userData.rearFoliage=true;woodland.userData.rearSingleLeafSurface=true;props.push(woodland);",1)
p.write_text(s)
