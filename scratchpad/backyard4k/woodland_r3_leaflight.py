from pathlib import Path
p=Path('frontend/js/environment.js');s=p.read_text(encoding='utf-8');a=s.index('function addRearLakeDetail');b=s.index('\nfunction addBackYard',a);v=s[a:b]
v=v.replace('    const clusterCount=Math.ceil(count/38);','    const clusterCount=Math.ceil(count/38); positions.leafNormals ||= [];')
v=v.replace('        for(const k of indices) {\n          positions.push', '''        for(let vertex=0;vertex<indices.length;vertex++) {
          const k=indices[vertex],side=scale>1?(vertex<6?1:-1):(vertex%6<3?1:-1);
          const local=verts[k].clone().sub(c).applyQuaternion(q.clone().invert());
          const leafNormal=new THREE.Vector3(local.x/size*.16,1,local.z/size*.42).normalize().multiplyScalar(side).applyQuaternion(q);
          positions.leafNormals.push(...leafNormal.toArray());
          positions.push''')
v=v.replace('g.computeVertexNormals();g.userData.rearFoliage=true;props.push(g);','g.setAttribute(\'normal\',new THREE.Float32BufferAttribute(pos.leafNormals,3));g.userData.rearFoliage=true;props.push(g);')
v=v.replace('woodland.computeVertexNormals(); leaves.push(woodland);','woodland.setAttribute(\'normal\',new THREE.Float32BufferAttribute(farPos.leafNormals,3)); leaves.push(woodland);')
s=s[:a]+v+s[b:]
old='''      rearFoliageMat ||= new THREE.MeshStandardMaterial({
        vertexColors: true, roughness: 0.95, metalness: 0 });'''
new='''      if(!rearFoliageMat) {
        rearFoliageMat=new THREE.MeshStandardMaterial({vertexColors:true,roughness:.95,metalness:0});
        // A thin leaf transmits part of incident light from its opposite face.
        // Both terms use the actual shadowed sun / hemisphere irradiance;
        // no emissive constant, normal bias or extra light is introduced.
        rearFoliageMat.onBeforeCompile=shader=>{
          const marker='reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );';
          const physical=THREE.ShaderChunk.lights_physical_pars_fragment.replace(marker,marker+
            '\\nreflectedLight.directDiffuse += max(-dot(geometryNormal,directLight.direction),0.0) * directLight.color * BRDF_Lambert(material.diffuseColor) * 0.22;');
          shader.fragmentShader=shader.fragmentShader.replace('#include <lights_physical_pars_fragment>',physical);
          shader.fragmentShader=shader.fragmentShader.replace('#include <lights_fragment_end>','#include <lights_fragment_end>\\n'+
            '#if NUM_HEMI_LIGHTS > 0\\nvec3 rearLeafBackIrradiance=vec3(0.0);\\n'+
            '#pragma unroll_loop_start\\nfor(int i=0;i<NUM_HEMI_LIGHTS;i++){rearLeafBackIrradiance += getHemisphereLightIrradiance(hemisphereLights[i],-geometryNormal); }\\n#pragma unroll_loop_end\\n'+
            'reflectedLight.indirectDiffuse += rearLeafBackIrradiance * BRDF_Lambert(material.diffuseColor) * 0.28;\\n#endif');
        };
        rearFoliageMat.customProgramCacheKey=()=> 'rear-thin-leaf-v1';
      }'''
assert old in s;s=s.replace(old,new,1);p.write_text(s,encoding='utf-8')
