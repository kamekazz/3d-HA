from pathlib import Path
p=Path('frontend/js/environment.js');s=p.read_text(encoding='utf-8');a=s.index('function addRearPlantingDetail(');h=s[a:]
h=h.replace('const centre = new THREE.Vector3(x,y+ry+0.82,z);','const lift = ry < 1.2 ? 0.08 : 0.62;\n    const centre = new THREE.Vector3(x,y+ry+lift,z);')
h=h.replace("const side=0.82+0.18*(ny+1)*0.5;\n        return new THREE.Vector3(x+nx*rx*side,centre.y+ny*ry,z+nz*rz*side);","const radial=Math.sqrt(nx*nx+nz*nz);\n        const side=(0.64+0.30*(ny+1)*0.5)*Math.sqrt(Math.max(0,1-Math.pow(Math.abs(ny),6)));\n        const factor=radial>0.0001?side/radial:0;\n        return new THREE.Vector3(x+nx*rx*factor,centre.y+ny*ry,z+nz*rz*factor);")
h=h.replace('core.computeVertexNormals(); paint(core,tone(tint || 0x263829)); props.push(core);','core.computeVertexNormals(); paint(core,tone(tint || 0x263829));\n    core.userData.rearFoliage=true; props.push(core);')
h=h.replace('.027+rng()*.028','.010+rng()*.017')
h=h.replace('g.computeVertexNormals();props.push(g);','g.computeVertexNormals();g.userData.rearFoliage=true;props.push(g);')
h=h.replace('L.hi','L.lo')
bed='''  // Scalloped river-gravel beds connect the porch planting. The open middle
  // lawn and the north stair landing stay outside these polygons.
  const bed = points => {
    const curve=new THREE.CatmullRomCurve3(points.map(([x,z])=>new THREE.Vector3(x,0,z)),true,'centripetal');
    const outline=curve.getPoints(60).map(p=>[p.x,p.z]);
    addBedPoly(rng,outline,L.lo+.075,beds,8,[],.18,true);
    addCobbleRun(rng,outline,L.lo+.075,beds,.45);
  };
  bed([[15.7,-43.3],[29.6,-43.1],[30.6,-32],[31.8,-19],[42.7,-18],
    [43.0,-33],[40.5,-42],[33.5,-46.2],[25,-47.5],[16.5,-47.2]]);
  bed([[-7.8,-25],[-.3,-25],[1.3,-33.8],[2.2,-41.5],[5.0,-44.4],
    [4.4,-47.7],[-3,-47.0],[-7.5,-42]]);
'''
h=h.replace('  // East (left in photo 09)',bed+'  // East (left in photo 09)')
s=s[:a]+h;p.write_text(s,encoding='utf-8')
