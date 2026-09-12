function addRearPlantingDetail(L, leaves, beds, props) {
  const rng = mulberry32(0x504c414e);
  const tone = h => new THREE.Color(h);
  const leafPalette = [0x2d402e, 0x3c5134, 0x465b39, 0x344a31, 0x536342];
  const leafPositions = [], leafColors = [], leafUVs = [];
  // Preserve the pre-refit Outside-editor anchors as the crowns grow outward.
  const specimenPivots = [
    [47.4973239899,.1344256699,-41.2042770386],[-2.0937818289,.1358322799,-38.4869632721],
    [46.1022090912,.1651925743,-30.2025556564],[47.513999939,.1673579514,-23.1960716248],
    [51.0037460327,.1411488354,-15.9901437759],[19.0027084351,.1222221926,-45.3964042664],
    [21.9888420105,.1311081797,-45.213760376],[24.9989175797,.1228073686,-44.909954071],
    [28.0164308548,.1339447647,-43.4938659668],[-4.6885583401,.1226787269,-45.9995193481],
    [3.0034079552,.1160103306,-45.8008804321],
  ];
  let specimenIndex = 0;
  const putTriangle = (a,b,c,color) => {
    for (const p of [a,b,c]) {
      leafPositions.push(p.x,p.y,p.z);
      leafColors.push(color.r,color.g,color.b);
      leafUVs.push(0,0);
    }
  };
  const branch = (a,b,r0,r1) => {
    const d = new THREE.Vector3().subVectors(b,a);
    const g = new THREE.CylinderGeometry(r1,r0,d.length(),8);
    g.applyQuaternion(new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0,1,0),d.clone().normalize()));
    g.translate(...a.clone().add(b).multiplyScalar(0.5).toArray());
    paint(g,tone(0x4b4538)); props.push(g);
  };
  const specimen = scoped('shrub','Clipped evergreen', (x,z,rx,ry,rz,y,form='round',tint=null) => {
    items[curItem].authoredPivot=specimenPivots[specimenIndex++];
    // Elliptical clipped crowns retain a slightly irregular leaf silhouette,
    // with the bare lower branching visible as in photographs 09 and 10.
    const lift = ry < 1.7 ? 0.12 : form==='upright' ? 0.10 : 1.05;
    const centre = new THREE.Vector3(x,y+ry+lift,z);
    const shapePoint = (nx,ny,nz) => {
      if(form==='upright') {
        const radial=Math.sqrt(nx*nx+nz*nz);
        const side=(0.64+0.30*(ny+1)*0.5)*Math.sqrt(Math.max(0,1-Math.pow(Math.abs(ny),6)));
        const factor=radial>0.0001?side/radial:0;
        return new THREE.Vector3(x+nx*rx*factor,centre.y+ny*ry,z+nz*rz*factor);
      }
      // Clipped mature holly has broad shoulders and a subtly flattened crown,
      // not a geometric ball. Continuous lobes keep the core and leaves aligned.
      const signedPow=v=>Math.sign(v)*Math.pow(Math.abs(v),.88);
      const ripple=1+.018*Math.sin(nx*9+nz*5)+.013*Math.cos(nz*11-ny*7)+.009*Math.sin(ny*17+nx*4);
      return new THREE.Vector3(x+signedPow(nx)*rx*ripple,
        centre.y+signedPow(ny)*ry*(1+.014*Math.sin(nx*8+nz*7)),z+signedPow(nz)*rz*ripple);
    };
    const core = new THREE.SphereGeometry(1,64,40);
    const cp=core.attributes.position;
    for(let i=0;i<cp.count;i++) {
      const nx=cp.getX(i),ny=cp.getY(i),nz=cp.getZ(i);
      const p=shapePoint(nx*.965,ny*.965,nz*.965);
      cp.setXYZ(i,p.x,p.y,p.z);
    }
    core.computeVertexNormals(); paint(core,tone(tint || 0x263829));
    core.userData.rearFoliage=true; props.push(core);
    const stem=new THREE.Vector3(x,y,z);
    for(let j=0;j<5;j++) {
      const angle=j*Math.PI*2/5+.21;
      const start=stem.clone().add(new THREE.Vector3(Math.cos(angle)*.22,0,Math.sin(angle)*.22));
      const fork=new THREE.Vector3(x+Math.cos(angle)*rx*.17,y+lift*.70+ry*.10,z+Math.sin(angle)*rz*.17);
      const tip=new THREE.Vector3(x+Math.cos(angle+.12)*rx*.59,y+lift+ry*.67,z+Math.sin(angle+.12)*rz*.59);
      branch(start,fork,ry>3?.15:.085,.072);branch(fork,tip,.077,.022);
      for(let k=0;k<2;k++) {
        const a=angle+(k?-.42:.46);
        branch(fork.clone().lerp(tip,.33+k*.19),
          new THREE.Vector3(x+Math.cos(a)*rx*.68,y+lift+ry*(.47+k*.26),z+Math.sin(a)*rz*.68),.043,.013);
      }
    }
    leafPositions.length=leafColors.length=leafUVs.length=0;
    const area=4*Math.PI*Math.pow((Math.pow(rx*ry,1.6075)+Math.pow(rx*rz,1.6075)+Math.pow(ry*rz,1.6075))/3,1/1.6075);
    const count=Math.round(area*56);
    const golden=Math.PI*(3-Math.sqrt(5));
    for(let i=0;i<count;i++) {
      const ny=1-2*(i+.5)/count, radius=Math.sqrt(1-ny*ny),a=i*golden;
      const nx=Math.cos(a)*radius,nz=Math.sin(a)*radius;
      const n=new THREE.Vector3(nx/rx,ny/ry,nz/rz).normalize();
      const p=shapePoint(nx,ny,nz).addScaledVector(n,(rng()-.25)*.14);
      const tangent=new THREE.Vector3().crossVectors(n,Math.abs(n.y)>.9?new THREE.Vector3(1,0,0):new THREE.Vector3(0,1,0)).normalize();
      tangent.applyAxisAngle(n,rng()*Math.PI*2);
      const across=new THREE.Vector3().crossVectors(n,tangent).normalize();
      const length=.078+rng()*.067, width=length*(.38+rng()*.15);
      const tip=p.clone().addScaledVector(tangent,length),bottom=p.clone().addScaledVector(tangent,-length);
      const left=p.clone().addScaledVector(across,width),right=p.clone().addScaledVector(across,-width);
      const ridge=p.clone().addScaledVector(n,.010+rng()*.017);
      const color=tone(tint || leafPalette[Math.floor(rng()*leafPalette.length)]).multiplyScalar(.77+rng()*.40);
      putTriangle(tip,left,ridge,color);putTriangle(left,bottom,ridge,color);
      color.multiplyScalar(.84);
      putTriangle(bottom,right,ridge,color);putTriangle(right,tip,ridge,color);
    }
    const g=new THREE.BufferGeometry();
    g.setAttribute('position',new THREE.Float32BufferAttribute(leafPositions,3));
    g.setAttribute('color',new THREE.Float32BufferAttribute(leafColors,3));
    g.setAttribute('uv',new THREE.Float32BufferAttribute(leafUVs,2));
    g.computeVertexNormals();g.userData.rearFoliage=true;props.push(g);
  });
  // Scalloped river-gravel beds connect the porch planting. The open middle
  // lawn and the north stair landing stay outside these polygons.
  const bedPivots = [
    [[35.3551387787,.1835728735,-30.1528596878],[35.3296627998,.1884338260,-30.1425476074]],
    [[-1.9727630615,.1842523515,-36.0511617661],[-2.0201001167,.1884332448,-36.0553941727]],
  ];
  let bedIndex=0;
  const bed = points => {
    const curve=new THREE.CatmullRomCurve3(points.map(([x,z])=>new THREE.Vector3(x,0,z)),true,'centripetal');
    const outline=curve.getPoints(60).map(p=>[p.x,p.z]);
    const anchors=bedPivots[bedIndex++];
    const bedItem=items.length;
    addBedPoly(rng,outline,L.lo+.075,beds,8,[],.18,true);
    items[bedItem].authoredPivot=anchors[0];
    const edgeItem=items.length;
    addCobbleRun(rng,outline,L.lo+.075,beds,.45);
    items[edgeItem].authoredPivot=anchors[1];
  };
  bed([[15.7,-43.3],[42.5,-43.3],[42.8,-31],[46.8,-22],[46.8,-13.0],
    [54.5,-12.9],[55,-28],[59,-38],[58.5,-45],[51,-49.3],[25,-48.4],[16.5,-47.2]]);
  bed([[-7.8,-25],[-.3,-25],[1.3,-33.8],[2.2,-41.5],[5.0,-44.4],
    [4.4,-47.7],[-3,-48.0],[-11.5,-45.7],[-12.0,-36.5]]);
  // East (left in photo 09) and west mature specimens: the photo's substantial
  // clipped masses rise above the rails. The outward offsets keep every crown
  // clear of the measured deck x3..20.6 / x20.6..42.2 footprints.
  specimen(50.4,-41.2,7.60,5.35,6.74,L.lo);
  specimen(-4.4,-38.5,6.67,4.81,6.05,L.lo);
  // Upright clipped evergreen pair in the east gravel return (photo 08).
  specimen(46.1,-30.2,1.7,2.60,1.55,L.lo,'upright');
  specimen(47.5,-23.2,1.35,2.15,1.35,L.lo,'upright');
  specimen(51.0,-16.0,3.3,2.65,3.0,L.lo);
  // Low spreading hedge under the north deck rail, leaving the stair landing
  // x10.3..14.9 clear. Small leaf-colour variation follows photograph 10.
  for(const [x,z,rx,ry,rz,c] of [
    [19.0,-45.4,2.25,1.25,1.55,0x606449], [22.0,-45.2,2.3,1.50,1.6,0x5a613f],
    [25.0,-44.9,2.4,1.40,1.55,0x687145], [28.0,-43.5,1.8,1.10,1.4,0x3b5636],
  ]) specimen(x,z,rx,ry,rz,L.lo,'round',c);
  // Sparse low evergreen accents at the west bed, never scattered across the
  // middle of the lawn. Shore tree/bank planting belongs to the lake builder.
  specimen(-4.7,-46.0,1.4,.58,1.15,L.lo,'round',0x58664b);
  specimen(3.0,-45.8,1.55,.56,1.1,L.lo,'round',0x4e6440);
}

