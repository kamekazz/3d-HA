ROOT = r"C:\Users\Manuel\Desktop\Pro\3d HA"
p = ROOT + r"\frontend\js\eavelights.js"
s = open(p, encoding='utf-8').read()

def block(s, start, end, new):
    i = s.index(start); j = s.index(end, i)
    return s[:i] + new + s[j:]

rep = [
# ---- bulbs: a real bloom. Sprite ~5x the core; gaussian core -> amber mid -> long tail
("const HALO_SIZE = 0.7;        // ft; screen size clamped in the shader",
 "const HALO_SIZE = 2.4;        // ft; the SPRITE -- the hot core is ~1/5 of it\nconst BLEED_SIZE = 7.0;       // ft; the faint atmospheric bleed round every bulb"),
("const AMBER_HALO = 0.3;       // the bed fixtures are smaller lamps", "const AMBER_HALO = 1.0;       // the bed fixtures are smaller lamps"),
("  const haloSize = dots.map(() => HALO_SIZE);",
 "  // +-12% size variance per bulb\n  const haloSize = dots.map(() => HALO_SIZE * (0.88 + 0.24 * rnd()));"),
("  const haloBright = dots.map(() => 0.9 + 0.2 * rnd());", "  const haloBright = dots.map((d, i) => (0.9 + 0.2 * rnd()) * (dotGain[i] || 1));"),
("  const dots = [];\n  let jseed = 11;", "  const dots = [];\n  const dotGain = [];\n  let jseed = 11;"),
("  const pushDot = (v) => {\n    for (const d of dots) if (d.distanceToSquared(v) < 0.16) return; // shared corner\n    dots.push(v);\n  };",
 "  const pushDot = (v, gain) => {\n    for (const d of dots) if (d.distanceToSquared(v) < 0.16) return; // shared corner\n    dots.push(v);\n    dotGain.push(gain);\n  };"),
("      const n = Math.max(1, Math.round(len / LED_SPACING));\n      for (let k = 0; k <= n; k++) {\n        // a little spacing jitter on the interior bulbs (+-6% of a gap)\n        const jit = (k === 0 || k === n) ? 0 : (jitter() - 0.5) * 0.12;\n        pushDot(new THREE.Vector3().lerpVectors(a, b, (k + jit) / n).add(off));\n      }",
 "      const n = Math.max(1, Math.round(len / (run.spacing || LED_SPACING)));\n      for (let k = 0; k <= n; k++) {\n        // a little spacing jitter on the interior bulbs (+-6% of a gap)\n        const jit = (k === 0 || k === n) ? 0 : (jitter() - 0.5) * 0.12;\n        pushDot(new THREE.Vector3().lerpVectors(a, b, (k + jit) / n).add(off), run.gain || 1);\n      }"),
("  haloMat = makeHaloMaterial();\n  halos = new THREE.Points(hg, haloMat);\n  halos.name = 'eaveHalos';\n  halos.renderOrder = 3;\n  halos.frustumCulled = false;\n  group.add(halos);",
 "  haloMat = makeHaloMaterial(1.0, 1.0, 0);\n  halos = new THREE.Points(hg, haloMat);\n  halos.name = 'eaveHalos';\n  halos.renderOrder = 3;\n  halos.frustumCulled = false;\n  group.add(halos);\n  // the bleed: the same points, a much bigger and dimmer gaussian, so the lit\n  // roofline carries a hair of atmosphere against the sky instead of a knife edge\n  bleedMat = makeHaloMaterial(BLEED_SIZE / HALO_SIZE, 0.08, 1);\n  const bleed = new THREE.Points(hg, bleedMat);\n  bleed.name = 'eaveBleed';\n  bleed.renderOrder = 2;\n  bleed.frustumCulled = false;\n  group.add(bleed);"),
("let haloMat = null;", "let haloMat = null;\nlet bleedMat = null;"),
("  for (const m of [ledMat, haloMat, washMat, windowMat]) {", "  for (const m of [ledMat, haloMat, bleedMat, washMat, windowMat]) {"),
("  group = null; halos = null; ledMat = null; haloMat = null; washMat = null; windowMat = null;",
 "  group = null; halos = null; ledMat = null; haloMat = null; bleedMat = null; washMat = null; windowMat = null;"),
("  if (haloMat && renderer) {\n    // gl_PointSize is in device pixels; scale = drawing-buffer height / 2 is\n    // what three's own PointsMaterial uses for sizeAttenuation\n    haloMat.uniforms.uScale.value = renderer.domElement.height / 2;\n  }",
 "  if (haloMat && renderer) {\n    // gl_PointSize is in device pixels; scale = drawing-buffer height / 2 is\n    // what three's own PointsMaterial uses for sizeAttenuation\n    haloMat.uniforms.uScale.value = renderer.domElement.height / 2;\n    bleedMat.uniforms.uScale.value = renderer.domElement.height / 2;\n  }"),
("  haloMat.uniforms.uOpacity.value = night;", "  haloMat.uniforms.uOpacity.value = night;\n  bleedMat.uniforms.uOpacity.value = night;"),
# ---- sky grain up a touch
("    const base = 2.6;                      // flat: any gradient tiles into bands", "    const base = 4.0;                      // flat: any gradient tiles into bands"),
("      const n = (seed / 2147483647 - 0.5) * 2.4;", "      const n = (seed / 2147483647 - 0.5) * 4.0;"),
("// Tiled grain for the sky dome: near-black, a hair of blue, +-1/255 noise.", "// Tiled grain for the sky dome: near-black, a hair of blue, +-2/255 noise."),
# ---- garage: the east gable rake string read as a sourceless sunburst seen
# end-on from the street; the front run gets the main run's density and a lift
("  { pts: [[20.602, 13.046, 30.66], [48.016, 13.046, 30.66]], out: [0, -LED_DROP, LED_OUT] },\n  { pts: [[48.016, 13.046, 30.66], [48.016, 23.324, 9.288], [48.016, 13.046, -12.086]],\n    out: [LED_OUT, -LED_DROP, 0] },\n  { pts: [[48.016, 13.046, -12.086], [20.602, 13.046, -12.086]], out: [0, -LED_DROP, -LED_OUT] },",
 "  // (no string on the garage's east gable rakes: seen end-on from the street\n  // they merged into one sourceless flare at the corner)\n  { pts: [[20.602, 13.046, 30.66], [48.016, 13.046, 30.66]], out: [0, -LED_DROP, LED_OUT],\n    spacing: 1.5, gain: 1.25 },\n  { pts: [[48.016, 13.046, -12.086], [20.602, 13.046, -12.086]], out: [0, -LED_DROP, -LED_OUT] },"),
# ---- wash: shorter decay, more of the light in the soffits
("  { a: [-8.2, 26.32, 30.62], b: [1.74, 36.43, 30.62], down: [R2, -R2, 0], width: 5.5, alpha: 0.68, clampY: 24.2, clap: true },\n  { a: [1.74, 36.43, 30.62], b: [11.67, 26.32, 30.62], down: [-R2, -R2, 0], width: 5.5, alpha: 0.68, clampY: 24.2, clap: true },",
 "  { a: [-8.2, 26.32, 30.62], b: [1.74, 36.43, 30.62], down: [R2, -R2, 0], width: 4, alpha: 0.62, clampY: 24.2, clap: true },\n  { a: [1.74, 36.43, 30.62], b: [11.67, 26.32, 30.62], down: [-R2, -R2, 0], width: 4, alpha: 0.62, clampY: 24.2, clap: true },"),
("  { a: [2.3, 37.0, 27.82], b: [6.656, 41.437, 27.82], down: [R2, -R2, 0], width: 5.5, alpha: 0.5, clap: true },\n  { a: [6.656, 41.437, 27.82], b: [21.519, 26.322, 27.82], down: [-R2, -R2, 0], width: 5.5, alpha: 0.5, clampY: 23.8, clap: true },",
 "  { a: [2.3, 37.0, 27.82], b: [6.656, 41.437, 27.82], down: [R2, -R2, 0], width: 4, alpha: 0.45, clap: true },\n  { a: [6.656, 41.437, 27.82], b: [21.519, 26.322, 27.82], down: [-R2, -R2, 0], width: 4, alpha: 0.45, clampY: 23.8, clap: true },"),
("  { a: [20.6, 13.0, 29.9], b: [46.5, 13.0, 29.9], down: [0, -1, 0], width: 6, alpha: 0.75, clap: true },",
 "  { a: [20.6, 13.0, 29.9], b: [46.5, 13.0, 29.9], down: [0, -1, 0], width: 4.5, alpha: 0.7, clap: true, spacing: 1.5 },"),
("  { a: [-8.2, 26.27, 30.7], b: [1.74, 36.38, 30.7], down: [0, 0, -1], width: 1.1, alpha: 0.9, soffit: true },\n  { a: [1.74, 36.38, 30.7], b: [11.67, 26.27, 30.7], down: [0, 0, -1], width: 1.1, alpha: 0.9, soffit: true },\n  { a: [2.3, 36.95, 27.9], b: [6.656, 41.39, 27.9], down: [0, 0, -1], width: 1.0, alpha: 0.8, soffit: true },\n  { a: [6.656, 41.39, 27.9], b: [21.519, 26.27, 27.9], down: [0, 0, -1], width: 1.0, alpha: 0.8, soffit: true },\n  { a: [20.6, 13.0, 30.68], b: [48.0, 13.0, 30.68], down: [0, 0, -1], width: 0.9, alpha: 0.9, soffit: true },",
 "  { a: [-8.2, 26.27, 30.7], b: [1.74, 36.38, 30.7], down: [0, 0, -1], width: 1.3, alpha: 1.0, soffit: true },\n  { a: [1.74, 36.38, 30.7], b: [11.67, 26.27, 30.7], down: [0, 0, -1], width: 1.3, alpha: 1.0, soffit: true },\n  { a: [2.3, 36.95, 27.9], b: [6.656, 41.39, 27.9], down: [0, 0, -1], width: 1.2, alpha: 0.95, soffit: true },\n  { a: [6.656, 41.39, 27.9], b: [21.519, 26.27, 27.9], down: [0, 0, -1], width: 1.2, alpha: 0.95, soffit: true },\n  { a: [20.6, 13.0, 30.68], b: [48.0, 13.0, 30.68], down: [0, 0, -1], width: 0.9, alpha: 1.0, soffit: true, spacing: 1.5 },"),
("    const spacing = w.scallop === false ? 0 : len / Math.max(1, Math.round(len / LED_SPACING));",
 "    const spacing = w.scallop === false ? 0 : len / Math.max(1, Math.round(len / (w.spacing || LED_SPACING)));"),
("        float band = soffit ? 0.35 : 1.0;", "        float band = soffit ? 0.35 : 0.8;"),
# ---- drive spot: near-neutral, and a real shadow so the car sits on the concrete
("const DRIVE_SPOT = { pos: [33, 16, 26], target: [33, 0, 66], intensity: 2600,\n                     angle: 0.95, penumbra: 0.8, range: 66, color: 0xffbe80 };",
 "const DRIVE_SPOT = { pos: [33, 16, 26], target: [33, 0, 66], intensity: 2600,\n                     angle: 0.95, penumbra: 0.8, range: 66, color: 0xfff2e4 };"),
("  driveSpot.name = 'eaveLight:drive';\n  scene.add(driveSpot);",
 "  driveSpot.name = 'eaveLight:drive';\n  // The one shadow-casting light here: without it the car floats on the lit\n  // concrete. Set ONCE at init (a shadow toggle is a program cache-key term,\n  // like the light count). The spot's own fov covers the drive; the frustum\n  // is trimmed to it so the 1k map spends its texels on the car (x ~28,\n  // z 58..74) and not on the sky.\n  driveSpot.castShadow = true;\n  driveSpot.shadow.mapSize.set(1024, 1024);\n  driveSpot.shadow.camera.near = 6;\n  driveSpot.shadow.camera.far = 80;\n  driveSpot.shadow.bias = -0.0004;\n  driveSpot.shadow.normalBias = 0.3;\n  scene.add(driveSpot);"),
]
for a, b in rep:
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b)

NEW_HALO = r'''// Screen-space bloom for a bulb. The sprite is ~5x the hot core: a gaussian
// white core, an amber mid, and a long gaussian tail that fades into the
// siding -- additive, so the bulbs crowding a gable apex build a hot-spot.
// sizeMul/gain/mode make the same shader serve the wide, faint "bleed" layer.
function makeHaloMaterial(sizeMul, gain, mode) {
  return new THREE.ShaderMaterial({
    uniforms: {
      uScale: { value: 300 },
      uOpacity: { value: 0 },
      uSizeMul: { value: sizeMul },
      uGain: { value: gain },
      uMode: { value: mode },
    },
    vertexShader: `
      uniform float uScale; uniform float uSizeMul;
      attribute float aSize; attribute float aBright;
      varying vec3 vColor; varying float vBright;
      void main() {
        vec4 mv = modelViewMatrix * vec4(position, 1.0);
        float ps = aSize * uSizeMul * uScale / max(0.5, -mv.z);
        gl_PointSize = clamp(ps, 8.0 * uSizeMul, 60.0 * uSizeMul);
        gl_Position = projectionMatrix * mv;
        vColor = color; vBright = aBright;
      }`,
    fragmentShader: `
      uniform float uOpacity; uniform float uGain; uniform float uMode;
      varying vec3 vColor; varying float vBright;
      float g(float d, float s) { return exp(-(d * d) / (2.0 * s * s)); }
      void main() {
        float d = length(gl_PointCoord - 0.5) * 2.0;
        if (d > 1.0) discard;
        vec3 c;
        if (uMode > 0.5) {
          c = vColor * (g(d, 0.42) * uGain);          // bleed: one soft gaussian
        } else {
          float core = g(d, 0.09);
          float mid = g(d, 0.24);
          float tail = g(d, 0.5);
          // the core overshoots 1.0 so it still clips on lit siding, but it
          // clips THROUGH the amber -- a 2700K bulb, not a 6500K pinhead
          c = mix(vColor, vec3(1.0), core * 0.6) * (core * 2.4 + mid * 0.55 + tail * 0.16) * uGain;
        }
        gl_FragColor = vec4(c * vBright * uOpacity, 1.0);
        #include <colorspace_fragment>
      }`,
    vertexColors: true,
    transparent: true,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });
}

'''
s = block(s, "// Screen-space halo:", "// Tiled grain for the sky dome", NEW_HALO)
open(p, 'w', encoding='utf-8').write(s)
print('ok')
