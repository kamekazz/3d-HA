from pathlib import Path
p=Path('frontend/js/environment.js');s=p.read_text()
s=s.replace('const far = x => L.yardN - 127 + 8 * Math.sin((x - mid) / 43)', 'const far = x => L.yardN - 260 + 13 * Math.sin((x - mid) / 43)',1)
a=s.index("  localItem('shore', 'Rear far bank and woodland', () => {");b=s.index('\n}\n\nfunction addBackYard',a);far=s[a:b]
far=far.replace('paintNoisy(bank,color(0x48503b),rng,.37)', 'paintNoisy(bank,color(0x939277),rng,.29)')
far=far.replace('if(rng()<.94)', 'if(rng()<.67)')
far=far.replace('height*.5,1.8+rng(),1100,farPos,farCol,1.5)', 'height*.5,1.8+rng(),1100,farPos,farCol,.95)')
far=far.replace('1400,farPos,farCol,1.7)', '1400,farPos,farCol,1.1)')
far=far.replace('rank===0?1.8:2.2)', 'rank===0?1.0:1.3)')
far=far.replace('woodland.userData.rearOakLeaf=true;', 'woodland.userData.rearOakLeaf=true;woodland.userData.rearFarLeaf=true;')
s=s[:a]+far+s[b:]
s=s.replace('let rearFoliageMat = null, rearBarkMat = null, rearOakLeafMat = null;', 'let rearFoliageMat = null, rearBarkMat = null, rearOakLeafMat = null, rearFarOakMat = null;',1)
a=s.index("    if(name==='props'&&geos.some(g=>g.userData?.rearOakLeaf)) {");b=s.index("    // Rear leaf surfaces keep normal",a)
s=s[:a]+'''    if(name==='props'&&geos.some(g=>g.userData?.rearOakLeaf)) {
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
      for(const distant of [false,true]) {
        const selected=geos.filter(g=>g.userData?.rearOakLeaf&&!!g.userData?.rearFarLeaf===distant);
        if(!selected.length)continue;
        if(distant&&!rearFarOakMat) {
          rearFarOakMat=rearOakLeafMat.clone();
          const atmosphere={rearFarSky:{value:new THREE.Color()},rearFarDay:{value:1}};
          rearFarOakMat.userData.rearAtmosphere=atmosphere;
          rearFarOakMat.onBeforeCompile=shader=>{
            Object.assign(shader.uniforms,atmosphere);
            shader.fragmentShader='uniform vec3 rearFarSky;\\nuniform float rearFarDay;\\n'+shader.fragmentShader;
            shader.fragmentShader=shader.fragmentShader.replace('#include <color_fragment>',
              '#include <color_fragment>\\nfloat farLeafLuma=dot(diffuseColor.rgb,vec3(.2126,.7152,.0722));\\ndiffuseColor.rgb=mix(vec3(farLeafLuma),diffuseColor.rgb,.40)*1.23;');
            shader.fragmentShader=shader.fragmentShader.replace('#include <opaque_fragment>',
              'float farAir=clamp(1.0-exp(-length(vViewPosition)*.0017),0.0,.56);\\n'+
              'vec3 farAirColor=mix(rearFarSky,vec3(dot(rearFarSky,vec3(.2126,.7152,.0722))),.36);\\n'+
              'outgoingLight=mix(outgoingLight,farAirColor*(1.0+rearFarDay*.28),farAir);\\n#include <opaque_fragment>');
          };
          rearFarOakMat.customProgramCacheKey=()=> 'rear-distant-oak-atmosphere-v1';
        }
        const mat=distant?rearFarOakMat:rearOakLeafMat;
        const leafMesh=new THREE.Mesh(BufferGeometryUtils.mergeGeometries(flat(selected),false),mat);
        leafMesh.name=distant?'rear-distant-oak-leaves':'rear-scanned-oak-leaves';
        leafMesh.castShadow=leafMesh.receiveShadow=true;leafMesh.userData.ownGeometry=true;
        if(distant)leafMesh.onBeforeRender=()=>{
          const uniforms=rearFarOakMat.userData.rearAtmosphere;
          if(scene.background?.isColor)uniforms.rearFarSky.value.copy(scene.background);
          uniforms.rearFarDay.value=1-getNightFactor();
        };
        group.add(leafMesh);
      }
      return group;
    }
''' +s[b:]
# Reflection uses the true mirrored view. The varying sampling footprint is
# specific to rough water, stretched horizontally by the shallow wavelets.
s=s.replace("+ 'vec2 reflectedUV = vRearLakeReflect.xy / vRearLakeReflect.w + vec2(lakeWave * 0.0014, cos(vRearLakeWorld.x * 5.3 + rearLakeTime * 0.18) * 0.0007);\\n'\n      + 'vec3 reflectedTrees = texture2D(rearLakeReflection, reflectedUV).rgb;\\n'\n      + 'outgoingLight = mix(outgoingLight, reflectedTrees * (0.78 + lakeWave * 0.018), 0.48 + lakeFresnel * 0.30);\\n'", """+ 'float lakeDistance=length(cameraPosition-vRearLakeWorld);\\n'
      + 'float lakeRoughness=smoothstep(25.0,270.0,lakeDistance);\\n'
      + 'float lakeCrossWave=sin(vRearLakeWorld.x*1.37+vRearLakeWorld.z*4.83-rearLakeTime*.19);\\n'
      + 'vec2 reflectedUV=vRearLakeReflect.xy/vRearLakeReflect.w+vec2((lakeWave+lakeCrossWave*.6)*(.0014+lakeRoughness*.0018),cos(vRearLakeWorld.z*7.9+rearLakeTime*.18)*.0006);\\n'
      + 'vec2 roughFootprint=vec2(.0012+lakeRoughness*.0026,.00035+lakeRoughness*.00055);\\n'
      + 'vec3 reflectedTrees=texture2D(rearLakeReflection,reflectedUV).rgb*.40;\\n'
      + 'reflectedTrees+=(texture2D(rearLakeReflection,reflectedUV+vec2(roughFootprint.x,0.0)).rgb+texture2D(rearLakeReflection,reflectedUV-vec2(roughFootprint.x,0.0)).rgb)*.20;\\n'
      + 'reflectedTrees+=(texture2D(rearLakeReflection,reflectedUV+roughFootprint).rgb+texture2D(rearLakeReflection,reflectedUV-roughFootprint).rgb)*.10;\\n'
      + 'float reflectedLuma=dot(reflectedTrees,vec3(.2126,.7152,.0722));\\n'
      + 'reflectedTrees=mix(reflectedTrees,vec3(reflectedLuma),lakeRoughness*.22);\\n'
      + 'float reflectAmount=(.27+lakeFresnel*.34)*(1.0-lakeRoughness*.25);\\n'
      + 'outgoingLight=mix(outgoingLight,reflectedTrees*(.85+lakeCrossWave*.026),reflectAmount);\\n'""",1)
s=s.replace("waterMat.customProgramCacheKey = () => 'rear-lake-water-v2';", "waterMat.customProgramCacheKey = () => 'rear-lake-water-v3';",1)
p.write_text(s)
