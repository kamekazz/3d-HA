from pathlib import Path
p=Path('frontend/js/environment.js');s=p.read_text();a=s.index('function addRearLakeDetail(');b=s.index('\nfunction addBackYard(',a);f=s[a:b]
f=f.replace('    rearLakeTime: { value: 0 },','''    rearLakeTime: { value: 0 },
    rearLakeReflection: { value: null },
    rearLakeProjection: { value: new THREE.Matrix4() },''')
f=f.replace("shader.vertexShader = 'varying vec3 vRearLakeWorld;\\n' + shader.vertexShader;", "shader.vertexShader = 'varying vec3 vRearLakeWorld;\\nvarying vec4 vRearLakeReflect;\\nuniform mat4 rearLakeProjection;\\n' + shader.vertexShader;")
f=f.replace('vRearLakeWorld = (modelMatrix * vec4(transformed, 1.0)).xyz;', 'vRearLakeWorld = (modelMatrix * vec4(transformed, 1.0)).xyz;\\nvRearLakeReflect = rearLakeProjection * vec4(vRearLakeWorld, 1.0);')
f=f.replace("shader.fragmentShader = 'varying vec3 vRearLakeWorld;\\nuniform vec3 rearLakeSky;\\nuniform float rearLakeTime;\\n'", "shader.fragmentShader = 'varying vec3 vRearLakeWorld;\\nvarying vec4 vRearLakeReflect;\\nuniform sampler2D rearLakeReflection;\\nuniform vec3 rearLakeSky;\\nuniform float rearLakeTime;\\n'")
f=f.replace("      + 'outgoingLight = mix(outgoingLight, rearLakeSky * (0.86 + lakeWave * 0.025), 0.25 + lakeFresnel * 0.52);\\n'", "      + 'vec2 reflectedUV = vRearLakeReflect.xy / vRearLakeReflect.w + vec2(lakeWave * 0.0014, cos(vRearLakeWorld.x * 5.3 + rearLakeTime * 0.18) * 0.0007);\\n'\n      + 'vec3 reflectedTrees = texture2D(rearLakeReflection, reflectedUV).rgb;\\n'\n      + 'outgoingLight = mix(outgoingLight, reflectedTrees * (0.78 + lakeWave * 0.018), 0.48 + lakeFresnel * 0.30);\\n'")
f=f.replace("'rear-lake-water-v1'", "'rear-lake-water-v2'")
start=f.index('  water.onBeforeRender = ');end=f.index('  yard.add(water);',start)
f=f[:start]+'''  // A local planar reflection renders the real scene from a mirrored camera.
  // Oblique clipping keeps submerged terrain out. It owns its render target and
  // updates only when this mesh renders; there is no global frame subscription.
  const reflectionTarget=new THREE.WebGLRenderTarget(1024,768,{type:THREE.HalfFloatType});
  waterUniforms.rearLakeReflection.value=reflectionTarget.texture;
  const mirrorCamera=new THREE.PerspectiveCamera(),plane=new THREE.Plane(),clip=new THREE.Vector4(),q=new THREE.Vector4();
  const bias=new THREE.Matrix4().set(.5,0,0,.5,0,.5,0,.5,0,0,.5,.5,0,0,0,1);
  const lastCamera=new THREE.Matrix4(); let reflecting=false,lastReflect=-Infinity;
  waterMat.addEventListener('dispose',()=>reflectionTarget.dispose());
  water.onBeforeRender = (activeRenderer,activeScene,camera) => {
    if (scene.background?.isColor) waterUniforms.rearLakeSky.value.copy(scene.background);
    waterUniforms.rearLakeTime.value = performance.now() * 0.001;
    if(reflecting||camera.position.y<=waterY||camera.userData.rearLakeMirror)return;
    const now=performance.now();
    if(now-lastReflect<160 || (camera.matrixWorld.equals(lastCamera)&&now-lastReflect<2000))return;
    reflecting=true;lastReflect=now;lastCamera.copy(camera.matrixWorld);
    const direction=new THREE.Vector3();camera.getWorldDirection(direction);direction.y*=-1;
    mirrorCamera.position.copy(camera.position);mirrorCamera.position.y=2*waterY-camera.position.y;
    mirrorCamera.up.copy(camera.up);mirrorCamera.up.y*=-1;
    mirrorCamera.lookAt(mirrorCamera.position.clone().add(direction));
    mirrorCamera.near=camera.near;mirrorCamera.far=camera.far;
    mirrorCamera.projectionMatrix.copy(camera.projectionMatrix);
    mirrorCamera.updateMatrixWorld();mirrorCamera.matrixWorldInverse.copy(mirrorCamera.matrixWorld).invert();
    mirrorCamera.userData.rearLakeMirror=true;
    waterUniforms.rearLakeProjection.value.copy(bias).multiply(mirrorCamera.projectionMatrix).multiply(mirrorCamera.matrixWorldInverse);
    plane.set(new THREE.Vector3(0,1,0),-waterY-.015).applyMatrix4(mirrorCamera.matrixWorldInverse);
    clip.set(plane.normal.x,plane.normal.y,plane.normal.z,plane.constant);
    const projection=mirrorCamera.projectionMatrix.elements;
    q.set((Math.sign(clip.x)+projection[8])/projection[0],(Math.sign(clip.y)+projection[9])/projection[5],-1,(1+projection[10])/projection[14]);
    clip.multiplyScalar(2/clip.dot(q));projection[2]=clip.x;projection[6]=clip.y;projection[10]=clip.z+1;projection[14]=clip.w;
    mirrorCamera.projectionMatrixInverse.copy(mirrorCamera.projectionMatrix).invert();
    const previousTarget=activeRenderer.getRenderTarget(),previousXR=activeRenderer.xr.enabled;
    const previousShadow=activeRenderer.shadowMap.autoUpdate;
    const previousViewport=new THREE.Vector4();activeRenderer.getViewport(previousViewport);
    water.visible=false;
    try {
      activeRenderer.xr.enabled=false;activeRenderer.shadowMap.autoUpdate=false;
      activeRenderer.setRenderTarget(reflectionTarget);activeRenderer.clear();activeRenderer.render(activeScene,mirrorCamera);
    } finally {
      water.visible=true;activeRenderer.xr.enabled=previousXR;activeRenderer.shadowMap.autoUpdate=previousShadow;
      activeRenderer.setRenderTarget(previousTarget);activeRenderer.setViewport(previousViewport);reflecting=false;
    }
  };
''' + f[end:]
p.write_text(s[:a]+f+s[b:])
