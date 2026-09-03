import io
ROOT = r"C:\Users\Manuel\Desktop\Pro\3d HA"
p = ROOT + r"\frontend\js\eavelights.js"
s = open(p, encoding='utf-8').read()
rep = [
# --- exposure: washes hug the fascia and die within ~3 ft
("  { a: [-8.2, 26.32, 30.62], b: [1.74, 36.43, 30.62], down: [R2, -R2, 0], width: 9, clampY: 24.2 },\n  { a: [1.74, 36.43, 30.62], b: [11.67, 26.32, 30.62], down: [-R2, -R2, 0], width: 9, clampY: 24.2 },",
 "  { a: [-8.2, 26.32, 30.62], b: [1.74, 36.43, 30.62], down: [R2, -R2, 0], width: 4, clampY: 24.2 },\n  { a: [1.74, 36.43, 30.62], b: [11.67, 26.32, 30.62], down: [-R2, -R2, 0], width: 4, clampY: 24.2 },"),
("  { a: [2.3, 37.0, 27.82], b: [6.656, 41.437, 27.82], down: [R2, -R2, 0], width: 9 },\n  { a: [6.656, 41.437, 27.82], b: [21.519, 26.322, 27.82], down: [-R2, -R2, 0], width: 9, clampY: 23.8 },",
 "  { a: [2.3, 37.0, 27.82], b: [6.656, 41.437, 27.82], down: [R2, -R2, 0], width: 4 },\n  { a: [6.656, 41.437, 27.82], b: [21.519, 26.322, 27.82], down: [-R2, -R2, 0], width: 4, clampY: 23.8 },"),
("  { a: [-7.5, 16.4, 29.68], b: [14.4, 16.4, 29.68], down: [0, 1, 0], width: 6.5, alpha: 0.35 },\n  { a: [15.0, 16.4, 26.86], b: [21.4, 16.4, 26.86], down: [0, 1, 0], width: 6.5, alpha: 0.35 },",
 "  { a: [-7.5, 16.4, 29.68], b: [14.4, 16.4, 29.68], down: [0, 1, 0], width: 3, alpha: 0.14 },\n  { a: [15.0, 16.4, 26.86], b: [21.4, 16.4, 26.86], down: [0, 1, 0], width: 3, alpha: 0.14 },"),
("  { a: [20.6, 13.0, 29.9], b: [46.5, 13.0, 29.9], down: [0, -1, 0], width: 6 },",
 "  { a: [20.6, 13.0, 29.9], b: [46.5, 13.0, 29.9], down: [0, -1, 0], width: 3.5 },"),
("  { a: [21.0, 26.25, 27.9], b: [21.0, 26.25, -12.0], down: [0, -1, 0], width: 5 },",
 "  { a: [21.0, 26.25, 27.9], b: [21.0, 26.25, -12.0], down: [0, -1, 0], width: 3.5 },"),
("    const alpha = w.alpha ?? 0.68;", "    const alpha = w.alpha ?? 0.42;"),
("        const f = alpha * Math.pow(1 - t, 1.6);", "        const f = alpha * Math.pow(1 - t, 2.6);"),
# --- dots: wider skirt, per-dot brightness, bigger near-clamp so end-on runs streak
("const HALO_SIZE = 0.85;       // ft; screen size clamped in the shader", "const HALO_SIZE = 1.1;        // ft; screen size clamped in the shader"),
("  const haloSize = dots.map(() => HALO_SIZE);\n  for (const p of AMBER_POINTS) {\n    haloPts.push(local(p));\n    haloCols.push(AMBER);\n    haloSize.push(AMBER_HALO);\n  }",
 "  const haloSize = dots.map(() => HALO_SIZE);\n  // +-15% per-LED brightness, seeded so the string never twinkles between builds\n  let seed = 7;\n  const rnd = () => { seed = (seed * 16807) % 2147483647; return seed / 2147483647; };\n  const haloBright = dots.map(() => 0.85 + 0.3 * rnd());\n  for (const p of AMBER_POINTS) {\n    haloPts.push(local(p));\n    haloCols.push(AMBER);\n    haloSize.push(AMBER_HALO);\n    haloBright.push(1);\n  }"),
("  hg.setAttribute('aSize', new THREE.Float32BufferAttribute(haloSize, 1));",
 "  hg.setAttribute('aSize', new THREE.Float32BufferAttribute(haloSize, 1));\n  hg.setAttribute('aBright', new THREE.Float32BufferAttribute(haloBright, 1));"),
("      attribute float aSize;\n      varying vec3 vColor;\n      void main() {\n        vec4 mv = modelViewMatrix * vec4(position, 1.0);\n        float ps = aSize * uScale / max(0.5, -mv.z);\n        gl_PointSize = clamp(ps, 4.0, 26.0);\n        gl_Position = projectionMatrix * mv;\n        vColor = color;",
 "      attribute float aSize; attribute float aBright;\n      varying vec3 vColor;\n      void main() {\n        vec4 mv = modelViewMatrix * vec4(position, 1.0);\n        float ps = aSize * uScale / max(0.5, -mv.z);\n        gl_PointSize = clamp(ps, 6.0, 40.0);\n        gl_Position = projectionMatrix * mv;\n        vColor = color * aBright;"),
("        float core = smoothstep(0.40, 0.08, d);\n        float skirt = pow(max(0.0, 1.0 - d), 2.4) * 0.4;",
 "        float core = smoothstep(0.30, 0.06, d);\n        float skirt = pow(max(0.0, 1.0 - d), 1.5) * 0.5;"),
# --- ground: one tight warm pool on the walk / porch step
("const AMBER_POINTS = [[2.0, 0.4, 47.5], [7.5, 0.4, 46.0], [49.0, 0.4, 44.0]];\nconst AMBER_INTENSITY = 4;\nconst AMBER_RANGE = 9;",
 "const AMBER_POINTS = [[2.0, 0.4, 47.5], [7.5, 0.4, 46.0], [49.0, 0.4, 44.0]];\nconst AMBER_INTENSITY = 4;\nconst AMBER_RANGE = 8;\n// a tight warm pool over the walk and the bottom porch step (the photo's walk\n// is lit to ~40% grey right at the steps and black ten feet out)\nconst STEP_POOL = { pos: [13.5, 3.0, 46.0], intensity: 7, range: 9, color: 0xffc080 };"),
("  spot = new THREE.SpotLight(", "  {\n    const light = new THREE.PointLight(STEP_POOL.color, 0, STEP_POOL.range, 2);\n    light.name = 'eaveLight:step';\n    scene.add(light);\n    lights.push({ light, local: new THREE.Vector3(...STEP_POOL.pos), base: STEP_POOL.intensity });\n  }\n  spot = new THREE.SpotLight("),
# --- sky dome
("let suspended = false;", "let sky = null;            // night sky dome (scene root, follows the camera)\nlet skyMat = null;\nlet suspended = false;"),
("  window.addEventListener('houseShellLoaded', (e) => build(e.detail.shell));",
 "  // The night sky: the photo's black has faint sensor grain and a lift at the\n  // horizon, and a clipped flat colour reads as a void. A big BackSide sphere\n  // around the camera with a tiny tiled noise texture, night-only, fog off\n  // (it sits past fog-far on purpose so nothing in the yard ever reaches it).\n  skyMat = new THREE.MeshBasicMaterial({\n    map: makeSkyTexture(), side: THREE.BackSide, fog: false, toneMapped: false,\n    transparent: true, opacity: 0, depthWrite: false,\n  });\n  sky = new THREE.Mesh(new THREE.SphereGeometry(1200, 24, 12), skyMat);\n  sky.name = 'nightSky';\n  sky.renderOrder = -10;\n  sky.frustumCulled = false;\n  sky.visible = false;\n  scene.add(sky);\n\n  window.addEventListener('houseShellLoaded', (e) => build(e.detail.shell));"),
("// warm light through a closed venetian blind",
 "// Tiled grain for the sky dome: near-black with a faint vertical gradient\n// (blacker at the zenith), a hair of blue, and +-2/255 noise.\nfunction makeSkyTexture() {\n  const cv = document.createElement('canvas');\n  cv.width = 256; cv.height = 128;\n  const ctx = cv.getContext('2d');\n  const img = ctx.createImageData(256, 128);\n  let seed = 3;\n  for (let y = 0; y < 128; y++) {\n    const t = y / 127;                     // 0 = top of the dome, 1 = horizon\n    const base = 1.5 + 5.5 * t * t;\n    for (let x = 0; x < 256; x++) {\n      seed = (seed * 16807) % 2147483647;\n      const n = (seed / 2147483647 - 0.5) * 4;\n      const v = Math.max(0, base + n);\n      const i = (y * 256 + x) * 4;\n      img.data[i] = v; img.data[i + 1] = v + 0.5; img.data[i + 2] = v + 1.5; img.data[i + 3] = 255;\n    }\n  }\n  ctx.putImageData(img, 0, 0);\n  const tex = new THREE.CanvasTexture(cv);\n  tex.wrapS = THREE.RepeatWrapping;\n  tex.repeat.x = 6;\n  tex.colorSpace = THREE.SRGBColorSpace;\n  return tex;\n}\n\n// warm light through a closed venetian blind"),
("  if (Math.abs(night - lastApplied) < 1e-3) return;\n  lastApplied = night;",
 "  if (sky) {\n    sky.visible = night > 0.01;\n    if (sky.visible) sky.position.copy(camera.position);\n  }\n\n  if (Math.abs(night - lastApplied) < 1e-3) return;\n  lastApplied = night;\n  if (skyMat) skyMat.opacity = night;"),
("import { scene, renderer, onFrame } from './scene.js';", "import { scene, camera, renderer, onFrame } from './scene.js';"),
("export function suspendEaveLights() {\n  suspended = true;\n  const saved = lights.map((l) => l.light.intensity);\n  for (const l of lights) l.light.intensity = 0;\n  return () => {\n    suspended = false;\n    lights.forEach((l, i) => { l.light.intensity = saved[i]; });\n  };",
 "export function suspendEaveLights() {\n  suspended = true;\n  const saved = lights.map((l) => l.light.intensity);\n  for (const l of lights) l.light.intensity = 0;\n  const skyWas = sky ? sky.visible : false;\n  if (sky) sky.visible = false; // the card's studio backdrop, not our night sky\n  return () => {\n    suspended = false;\n    lights.forEach((l, i) => { l.light.intensity = saved[i]; });\n    if (sky) sky.visible = skyWas;\n  };"),
]
for a, b in rep:
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
p = ROOT + r"\frontend\js\daylight.js"
s = open(p, encoding='utf-8').read()
a = "  [-18, 0xff8844, 0.00, 0x1e2028, 0x07080c, 0.20, 0x010203], // night"
b = "  [-18, 0xff8844, 0.00, 0x1e2028, 0x07080c, 0.15, 0x010203], // night"
assert s.count(a) == 1
s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('ok')
