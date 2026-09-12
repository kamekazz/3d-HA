from pathlib import Path
p=Path('frontend/js/environment.js');s=p.read_text(encoding='utf-8')
s=s.replace('  let rearFoliageMat = null;','  let rearFoliageMat = null, rearBarkMat = null;')
needle='''    // Rear leaf surfaces keep normal per-item editing but use a matte material.'''
insert='''    // Only the new rear bark uses the photographed CC0 oak PBR material.
    // Split within the buckets so every tree retains its existing edit group.
    if(name==='masses'&&geos.some(g=>g.userData?.rearBark)) {
      const group=new THREE.Group(),ordinary=geos.filter(g=>!g.userData?.rearBark);
      if(ordinary.length)group.add(bucketMesh(name,ordinary));
      if(!rearBarkMat) {
        const loader=new THREE.TextureLoader(),albedo=loader.load('/textures/backyard/oak-bark-albedo.webp');
        const normal=loader.load('/textures/backyard/oak-bark-normal.webp');
        albedo.colorSpace=THREE.SRGBColorSpace;
        for(const tex of [albedo,normal]){tex.wrapS=tex.wrapT=THREE.RepeatWrapping;tex.anisotropy=8;}
        rearBarkMat=new THREE.MeshStandardMaterial({map:albedo,normalMap:normal,normalScale:new THREE.Vector2(.85,.85),vertexColors:true,roughness:.97});
        rearBarkMat.addEventListener('dispose',()=>{albedo.dispose();normal.dispose();});
      }
      const barkMesh=new THREE.Mesh(BufferGeometryUtils.mergeGeometries(flat(geos.filter(g=>g.userData?.rearBark)),false),rearBarkMat);
      barkMesh.name='rear-lake-bark';barkMesh.castShadow=barkMesh.receiveShadow=true;
      barkMesh.userData.ownGeometry=true;group.add(barkMesh);return group;
    }
'''
assert needle in s;s=s.replace(needle,insert+needle,1)
a=s.index('function addRearLakeDetail');b=s.index('\nfunction addBackYard',a);part=s[a:b]
part=part.replace('360,pos,col,.50','220,pos,col,.50').replace('1000,pos,col,.46','650,pos,col,.46').replace('1200,pos,col,.49','800,pos,col,.49').replace('4.5,500,farPos','4.5,300,farPos')
s=s[:a]+part+s[b:];p.write_text(s,encoding='utf-8')
