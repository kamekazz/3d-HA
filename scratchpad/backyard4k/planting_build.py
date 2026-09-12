from pathlib import Path
p=Path('frontend/js/environment.js')
s=p.read_text(encoding='utf-8')
a=s.index('  // 2. The big clipped specimens',s.index('function addBackYard('))
b=s.index('  // The reference lake replaces',a)
s=s[:a]+'''  // Photo 03/08/09/10: clipped evergreen specimens frame the porch; the
  // central lawn is open. The rear-only detail builder owns its fixed RNG.
  addRearPlantingDetail(L, leaves, beds, props);

'''+s[b:]
s+='''

// Photo-derived rear planting arrangement. Geometric leaves are roughly one
// inch long; no photographic planes, giant low-poly mounds or shared RNG use.
// Each specimen stays an editable shrub item. Its bark and folded leaf faces
// join props, whose existing material path casts actual directional shadows.
function addRearPlantingDetail(L, leaves, beds, props) {
  const rng = mulberry32(0x504c414e);
  const tone = h => new THREE.Color(h);
  const leafPalette = [0x2d402e, 0x3c5134, 0x465b39, 0x344a31, 0x536342];
  const leafPositions = [], leafColors = [], leafUVs = [];
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
    // Elliptical clipped crowns retain a slightly irregular leaf silhouette,
    // with the bare lower branching visible as in photographs 09 and 10.
    const centre = new THREE.Vector3(x,y+ry+0.82,z);
    const shapePoint = (nx,ny,nz) => {
      if(form==='upright') {
        const side=0.82+0.18*(ny+1)*0.5;
        return new THREE.Vector3(x+nx*rx*side,centre.y+ny*ry,z+nz*rz*side);
      }
      return new THREE.Vector3(x+nx*rx,centre.y+ny*ry,z+nz*rz);
    };
    const core = new THREE.SphereGeometry(1,64,40);
    const cp=core.attributes.position;
    for(let i=0;i<cp.count;i++) {
      const nx=cp.getX(i),ny=cp.getY(i),nz=cp.getZ(i);
      const p=shapePoint(nx*.965,ny*.965,nz*.965);
      cp.setXYZ(i,p.x,p.y,p.z);
    }
    core.computeVertexNormals(); paint(core,tone(tint || 0x263829)); props.push(core);
    const stem=new THREE.Vector3(x,y,z);
    for(let j=0;j<5;j++) {
      const angle=j*Math.PI*2/5+.21;
      branch(stem.clone().add(new THREE.Vector3(Math.cos(angle)*.19,0,Math.sin(angle)*.19)),
        new THREE.Vector3(x+Math.cos(angle)*rx*.50,y+ry*1.02,z+Math.sin(angle)*rz*.50),.105,.046);
    }
    leafPositions.length=leafColors.length=leafUVs.length=0;
    const area=4*Math.PI*Math.pow((Math.pow(rx*ry,1.6075)+Math.pow(rx*rz,1.6075)+Math.pow(ry*rz,1.6075))/3,1/1.6075);
    const count=Math.round(area*37);
    const golden=Math.PI*(3-Math.sqrt(5));
    for(let i=0;i<count;i++) {
      const ny=1-2*(i+.5)/count, radius=Math.sqrt(1-ny*ny),a=i*golden;
      const nx=Math.cos(a)*radius,nz=Math.sin(a)*radius;
      const n=new THREE.Vector3(nx/rx,ny/ry,nz/rz).normalize();
      const p=shapePoint(nx,ny,nz).addScaledVector(n,(rng()-.3)*.105);
      const tangent=new THREE.Vector3().crossVectors(n,Math.abs(n.y)>.9?new THREE.Vector3(1,0,0):new THREE.Vector3(0,1,0)).normalize();
      tangent.applyAxisAngle(n,rng()*Math.PI*2);
      const across=new THREE.Vector3().crossVectors(n,tangent).normalize();
      const length=.078+rng()*.067, width=length*(.38+rng()*.15);
      const tip=p.clone().addScaledVector(tangent,length),bottom=p.clone().addScaledVector(tangent,-length);
      const left=p.clone().addScaledVector(across,width),right=p.clone().addScaledVector(across,-width);
      const ridge=p.clone().addScaledVector(n,.027+rng()*.028);
      const color=tone(tint || leafPalette[Math.floor(rng()*leafPalette.length)]).multiplyScalar(.77+rng()*.40);
      putTriangle(tip,left,ridge,color);putTriangle(left,bottom,ridge,color);
      color.multiplyScalar(.84);
      putTriangle(bottom,right,ridge,color);putTriangle(right,tip,ridge,color);
    }
    const g=new THREE.BufferGeometry();
    g.setAttribute('position',new THREE.Float32BufferAttribute(leafPositions,3));
    g.setAttribute('color',new THREE.Float32BufferAttribute(leafColors,3));
    g.setAttribute('uv',new THREE.Float32BufferAttribute(leafUVs,2));
    g.computeVertexNormals();props.push(g);
  });
  // East (left in photo 09) and west main specimens: asymmetric, dark green,
  // approximately door-height. Their lower crowns clear the woody stems.
  specimen(34.7,-36.5,4.9,3.45,4.35,L.lo);
  specimen(-2.1,-38.5,4.3,3.10,3.9,L.hi);
  // Upright clipped evergreen pair in the east gravel return (photo 08).
  specimen(40.0,-30.2,1.7,2.60,1.55,L.lo,'upright');
  specimen(39.0,-22.5,1.35,2.15,1.35,L.lo,'upright');
  specimen(35.0,-19.8,3.3,2.65,3.0,L.lo);
  // Low spreading hedge under the north deck rail, leaving the stair landing
  // x10.3..14.9 clear. Small leaf-colour variation follows photograph 10.
  for(const [x,z,rx,ry,rz,c] of [
    [19.0,-45.4,1.8,.80,1.30,0x606449], [22.0,-45.2,1.8,1.0,1.35,0x5a613f],
    [25.0,-44.9,1.9,.87,1.30,0x687145], [28.0,-43.5,1.4,.77,1.20,0x3b5636],
  ]) specimen(x,z,rx,ry,rz,L.hi,'round',c);
  // Sparse low evergreen accents at the west bed, never scattered across the
  // middle of the lawn. Shore tree/bank planting belongs to the lake builder.
  specimen(-4.7,-46.0,1.4,.58,1.15,L.hi,'round',0x58664b);
  specimen(3.0,-45.8,1.55,.56,1.1,L.hi,'round',0x4e6440);
}
'''
p.write_text(s,encoding='utf-8')
