from pathlib import Path
p=Path('frontend/js/environment.js');s=p.read_text()
a=s.index('  // A crown is many overlapping twig sprays',s.index('function addRearLakeDetail'));b=s.index('  const matureTree =',a)
s=s[:a]+'''  // Individual scanned oak leaves curve along their central vein. These are
  // four-triangle surfaces, not whole-crown billboards; the photograph's alpha
  // supplies the natural lobes while its normal map supplies the small veins.
  const leafCloud = (cx, cy, cz, rx, ry, rz, count, positions, colors, scale = 1) => {
    if(scale<=1)count=Math.ceil(count*1.45);
    const clusterCount=Math.ceil(count/28); positions.leafNormals ||= [];positions.leafUVs ||= [];
    const indices=[0,2,1,1,2,3,2,4,3,3,4,5];
    for(let cl=0;cl<clusterCount;cl++) {
      let dx,dy,dz;do {dx=rng()*2-1;dy=rng()*2-1;dz=rng()*2-1;}while(dx*dx+dy*dy+dz*dz>1);
      const center=new THREE.Vector3(cx+dx*rx,cy+dy*ry,cz+dz*rz);
      const depth=Math.sqrt(dx*dx+dy*dy+dz*dz);
      const shade=.42+depth*.26+rng()*.19;
      const axis=new THREE.Vector3(rng()-.5,.2+rng()*.4,rng()-.5).normalize();
      for(let n=0;n<28&&cl*28+n<count;n++) {
        const c=center.clone().addScaledVector(axis,(rng()-.5)*1.6);
        c.add(new THREE.Vector3((rng()-.5)*1.15,(rng()-.5)*.8,(rng()-.5)*1.15));
        const halfLength=(.19+rng()*.115)*scale,halfWidth=halfLength*.586;
        const bend=halfLength*(.11+rng()*.17);
        const q=new THREE.Quaternion().setFromEuler(new THREE.Euler((rng()-.5)*2.1,rng()*6.28,(rng()-.5)*1.9));
        const local=[[-halfLength,0,-halfWidth],[-halfLength,0,halfWidth],
          [0,bend,-halfWidth],[0,bend,halfWidth],[halfLength,-bend*.35,-halfWidth],[halfLength,-bend*.35,halfWidth]];
        const verts=local.map(v=>new THREE.Vector3(...v).applyQuaternion(q).add(c));
        const normals=local.map(v=>new THREE.Vector3(v[0]/halfLength*.24,1,v[2]/halfWidth*.1).normalize().applyQuaternion(q));
        const uvs=[[0,0],[1,0],[0,.5],[1,.5],[0,1],[1,1]];
        const brightness=shade*(.9+rng()*.2),warm=.96+rng()*.08;
        for(const k of indices) {
          positions.leafNormals.push(...normals[k].toArray());positions.push(...verts[k].toArray());
          positions.leafUVs.push(...uvs[k]);colors.push(brightness*warm,brightness,brightness*(.96+rng()*.035));
        }
      }
    }
  };
''' +s[b:]
s=s.replace("g.setAttribute('uv',new THREE.Float32BufferAttribute(new Float32Array(pos.length/3*2),2));\n    g.setAttribute('normal',new THREE.Float32BufferAttribute(pos.leafNormals,3));\n    g.userData.rearFoliage=true;g.userData.rearSingleLeafSurface=true;props.push(g);", "g.setAttribute('uv',new THREE.Float32BufferAttribute(pos.leafUVs,2));\n    g.setAttribute('normal',new THREE.Float32BufferAttribute(pos.leafNormals,3));\n    g.userData.rearFoliage=true;g.userData.rearOakLeaf=true;g.userData.rearSingleLeafSurface=true;props.push(g);",1)
s=s.replace("const far = x => L.yardN - 127 + 8 * Math.sin((x - mid) / 43);", "const far = x => L.yardN - 127 + 8 * Math.sin((x - mid) / 43)\n    + 4.2*Math.sin((x-mid)/9.4)+1.3*Math.sin((x-mid)/3.1);",1)
a=s.index("  localItem('shore', 'Rear far bank and woodland', () => {",s.index('function addRearLakeDetail'));b=s.index('\n}\n\nfunction addBackYard',a)
s=s[:a]+'''  localItem('shore', 'Rear far bank and woodland', () => {
    const bankHeight=x=>L.lo+.55+1.4*worldNoise(x,-210,9)+.55*Math.sin(x*.37);
    const bank = ribbon(lakeX0, lakeX1, far, x=>far(x)-10,
      waterY+.012, L.lo+1.4, 360);
    const bp=bank.attributes.position;
    for(let i=0;i<bp.count;i++) {
      const x=bp.getX(i),t=Math.max(0,Math.min(1,(far(x)-bp.getZ(i))/10));
      bp.setY(i,waterY+.012+(bankHeight(x)-waterY)*t);
    }
    bank.computeVertexNormals();paintNoisy(bank,color(0x676c50),rng,.37);beds.push(bank);
    const terrain = ribbon(lakeX0, lakeX1, x=>far(x)-10, x=>far(x)-95,L.lo+1.5,L.lo+3,200);
    lawns.push(terrain);
    const farPos=[], farCol=[];
    // Low, broken water-edge scrub hides the bank in places and leaves mud,
    // reeds and short grass visible between clusters. Nothing forms a rail.
    for(let x=lakeX0;x<lakeX1;x+=2.5+rng()*3.7) {
      const z=far(x)-1.4-rng()*4,height=1.2+rng()*4.3;
      if(rng()<.78) {
        branch([[x,waterY,z],[x+.3,height*.7+L.lo,z-.4],[x-.5,height+L.lo,z-.7]],.05,.009,masses);
        leafCloud(x,L.lo+height*.70,z,2.1+rng()*1.7,height*.5,1.8+rng(),360,farPos,farCol,1.5);
      }
      for(let j=0;j<8;j++) {
        const xx=x+(rng()-.5)*3,zz=far(xx)-rng()*2.2,h=.4+rng()*1.5;
        const g=new THREE.PlaneGeometry(.025+rng()*.045,h);g.rotateY(rng()*6.28);g.rotateZ((rng()-.5)*.45);g.translate(xx,waterY+h*.5,zz);
        paint(g,color(rng()<.4?0x898367:0x707b53));leaves.push(g);
      }
    }
    // Three unequal ranks overlap in depth: low pioneer trees on the bank,
    // broad middle crowns and taller crowns receding behind those gaps.
    for(let rank=0;rank<3;rank++)for(let x=lakeX0-12;x<lakeX1+12;x+=7+rng()*7) {
      const xx=x+(rng()-.5)*5,z=far(xx)-8-rank*20-rng()*13;
      const height=rank===0?7+rng()*10:rank===1?16+rng()*14:23+rng()*21;
      const width=(rank===0?4.8:7)+rng()*4,lean=(rng()-.5)*4;
      branch([[xx,L.lo+1,z],[xx+lean*.35,L.lo+height*.48,z-1],[xx+lean,L.lo+height,z-2]],.19+rank*.09,.02,masses);
      for(let b=0;b<4;b++) {
        const a=rng()*6.28,r=width*(.25+rng()*.5);
        const tip=[xx+lean+Math.cos(a)*r,L.lo+height*(.50+b*.115),z+Math.sin(a)*r];
        branch([[xx+lean*.4,L.lo+height*.4,z],[(xx+tip[0])*.5,tip[1]-1.7,(z+tip[2])*.5],tip],.095,.012,masses);
        leafCloud(...tip,width*.64,2.8+rank+rng()*2,width*.58,rank===0?750:1050,farPos,farCol,rank===0?1.8:2.2);
      }
    }
    const woodland = new THREE.BufferGeometry();
    woodland.setAttribute('position',new THREE.Float32BufferAttribute(farPos,3));
    woodland.setAttribute('color',new THREE.Float32BufferAttribute(farCol,3));
    woodland.setAttribute('uv',new THREE.Float32BufferAttribute(farPos.leafUVs,2));
    woodland.setAttribute('normal',new THREE.Float32BufferAttribute(farPos.leafNormals,3));
    woodland.userData.rearFoliage=true;woodland.userData.rearOakLeaf=true;woodland.userData.rearSingleLeafSurface=true;props.push(woodland);
  });''' +s[b:]
s=s.replace('let rearFoliageMat = null, rearBarkMat = null;', 'let rearFoliageMat = null, rearBarkMat = null, rearOakLeafMat = null;',1)
needle="    // Rear leaf surfaces keep normal per-item editing but use a matte material."
replacement='''    // Only these leaf surfaces carry photographic leaf UVs. Other rear plants
    // keep their existing foliage material and the front bypasses this branch.
    if(name==='props'&&geos.some(g=>g.userData?.rearOakLeaf)) {
      const group=new THREE.Group(),ordinary=geos.filter(g=>!g.userData?.rearOakLeaf);
      if(ordinary.length)group.add(bucketMesh(name,ordinary));
      if(!rearOakLeafMat) {
        const loader=new THREE.TextureLoader(),map=loader.load('/textures/backyard/oak-leaf-albedo.webp');
        const normal=loader.load('/textures/backyard/oak-leaf-normal-dx.webp');
        map.colorSpace=THREE.SRGBColorSpace;map.anisotropy=8;normal.anisotropy=8;
        rearOakLeafMat=new THREE.MeshStandardMaterial({map,normalMap:normal,normalScale:new THREE.Vector2(.4,-.4),
          vertexColors:true,alphaTest:.45,side:THREE.DoubleSide,roughness:.91,metalness:0});
        rearOakLeafMat.addEventListener('dispose',()=>{map.dispose();normal.dispose();});
      }
      const leafMesh=new THREE.Mesh(BufferGeometryUtils.mergeGeometries(flat(geos.filter(g=>g.userData?.rearOakLeaf)),false),rearOakLeafMat);
      leafMesh.name='rear-scanned-oak-leaves';leafMesh.castShadow=leafMesh.receiveShadow=true;
      leafMesh.userData.ownGeometry=true;group.add(leafMesh);return group;
    }
''' +needle
s=s.replace(needle,replacement,1)
p.write_text(s)
