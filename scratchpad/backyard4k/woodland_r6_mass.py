from pathlib import Path
p=Path('frontend/js/environment.js');s=p.read_text();a=s.index("  localItem('shore', 'Rear far bank and woodland', () => {");b=s.index('\n}\n\nfunction addBackYard',a);far=s[a:b]
needle='    const farPos=[], farCol=[];'
replacement='''    const farPos=[], farCol=[];
    // At this distance crown interiors supply opaque, self-occluded mass;
    // the small real leaves form the irregular outer silhouette. The nested
    // lobes are deformed individually, so they do not become smooth spheres.
    const farCore=(x,y,z,rx,ry,rz)=>{
      const g=new THREE.IcosahedronGeometry(1,3),p=g.attributes.position;
      for(let i=0;i<p.count;i++) {
        const xx=p.getX(i),yy=p.getY(i),zz=p.getZ(i);
        const r=.81+.13*Math.sin(xx*8+zz*3)+.10*Math.sin(yy*9-xx*4)+.06*Math.sin(zz*15+yy*4);
        p.setXYZ(i,x+xx*rx*r,y+yy*ry*r,z+zz*rz*r);
      }
      g.computeVertexNormals();paintNoisy(g,color(0x727c62),rng,.17);
      g.userData.rearOakLeaf=true;g.userData.rearFarLeaf=true;g.userData.rearFarVolume=true;props.push(g);
    };'''
far=far.replace(needle,replacement,1)
needle='        leafCloud(...tip,width*.64,2.8+rank+rng()*2,width*.58,rank===0?750:1050,farPos,farCol,rank===0?1.0:1.3);'
replacement='''        const crownY=2.8+rank+rng()*2;
        leafCloud(...tip,width*.64,crownY,width*.58,rank===0?750:1050,farPos,farCol,rank===0?1.0:1.3);
        farCore(...tip,width*.64,crownY,width*.58);'''
assert needle in far;far=far.replace(needle,replacement,1)
s=s[:a]+far+s[b:]
s=s.replace('rearOakLeafMat = null, rearFarOakMat = null;', 'rearOakLeafMat = null, rearFarOakMat = null, rearFarVolumeMat = null;',1)
s=s.replace('length(vViewPosition)*.0017),0.0,.56)', 'length(vViewPosition)*.00050),0.0,.24)',1)
s=s.replace('farAirColor*(1.0+rearFarDay*.28)', 'farAirColor*(1.0+rearFarDay*.08)',1)
needle="        const leafMesh=new THREE.Mesh(BufferGeometryUtils.mergeGeometries(flat(selected),false),mat);"
replacement='''        const volumes=selected.filter(g=>g.userData?.rearFarVolume);
        if(volumes.length) {
          if(!rearFarVolumeMat) {
            rearFarVolumeMat=rearFarOakMat.clone();rearFarVolumeMat.map=null;rearFarVolumeMat.normalMap=null;rearFarVolumeMat.alphaTest=0;
            rearFarVolumeMat.onBeforeCompile=rearFarOakMat.onBeforeCompile;
            rearFarVolumeMat.customProgramCacheKey=()=> 'rear-distant-crown-interior-v1';
          }
          const volumeMesh=new THREE.Mesh(BufferGeometryUtils.mergeGeometries(flat(volumes),false),rearFarVolumeMat);
          volumeMesh.name='rear-distant-crown-interiors';volumeMesh.castShadow=volumeMesh.receiveShadow=true;volumeMesh.userData.ownGeometry=true;
          volumeMesh.onBeforeRender=()=>{
            const uniforms=rearFarOakMat.userData.rearAtmosphere;
            if(scene.background?.isColor)uniforms.rearFarSky.value.copy(scene.background);
            uniforms.rearFarDay.value=1-getNightFactor();
          };
          group.add(volumeMesh);
        }
        const leafGeos=selected.filter(g=>!g.userData?.rearFarVolume);
        if(!leafGeos.length)continue;
        const leafMesh=new THREE.Mesh(BufferGeometryUtils.mergeGeometries(flat(leafGeos),false),mat);'''
assert needle in s;s=s.replace(needle,replacement,1);p.write_text(s)
