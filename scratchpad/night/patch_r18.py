ROOT = r"C:\Users\Manuel\Desktop\Pro\3d HA"
p = ROOT + r"\frontend\js\eavelights.js"
s = open(p, encoding='utf-8').read()

def block(s, start, end, new):
    i = s.index(start); j = s.index(end, i)
    return s[:i] + new + s[j:]

rep = [
# ---- 1. the garage "nova": every source on that face under the bloom threshold
("  { a: [20.6, 13.0, 29.9], b: [46.5, 13.0, 29.9], down: [0, -1, 0], width: 4.5, alpha: 0.7, clap: true, spacing: 1.5 },",
 "  // (kept well under scene.js's bloom threshold: with the sconce floods and the\n  // soffit strip on top of it, this face went nova and fogged the frame)\n  { a: [20.6, 13.0, 29.9], b: [46.5, 13.0, 29.9], down: [0, -1, 0], width: 4.5, alpha: 0.32, clap: true, spacing: 1.5 },"),
("width: 0.9, alpha: 0.85, soffit: true, spacing: 1.5", "width: 0.9, alpha: 0.38, soffit: true, spacing: 1.5"),
# ---- 2. bulbs: half the sprite, tighter halo, +-15% brightness
("const HALO_SIZE = 1.5;        // ft; the SPRITE -- the hot core is ~1/5 of it", "const HALO_SIZE = 0.8;        // ft; the SPRITE -- the hot core is ~1/5 of it"),
("  const haloBright = dots.map((d, i) => (0.9 + 0.2 * rnd()) * (dotGain[i] || 1));", "  const haloBright = dots.map((d, i) => (0.85 + 0.3 * rnd()) * (dotGain[i] || 1));"),
("        gl_PointSize = clamp(ps, 8.0 * uSizeMul, 60.0 * uSizeMul);", "        gl_PointSize = clamp(ps, 5.0 * uSizeMul, 36.0 * uSizeMul);"),
("(core * 2.0 + mid * 0.3 + tail * 0.05)", "(core * 2.0 + mid * 0.22 + tail * 0.03)"),
# ---- 3. the gable band back
("width: 4, alpha: 0.5, clampY: 24.2, clap: true", "width: 4.5, alpha: 0.62, clampY: 24.2, clap: true"),
("width: 4, alpha: 0.38, clap: true", "width: 4.5, alpha: 0.45, clap: true"),
("width: 4, alpha: 0.38, clampY: 23.8, clap: true", "width: 4.5, alpha: 0.45, clampY: 23.8, clap: true"),
# ---- 4/5. walk and drive lights: spots, generically
("const STEP_POOL = { pos: [10.5, 6.0, 49.0], intensity: 95, range: 18, color: 0xffb46b };",
 "// The walk fan (x 11..20, z 44..70) and the rock band beside it (x 8.6..15.6,\n// z 47..58) at ~100/255, the lawn either side dark: two downward spots whose\n// penumbra dies before the grass, not a point that spills in every direction.\nconst WALK_SPOTS = [\n  { pos: [13, 12, 50], target: [13, 0, 51], intensity: 260, angle: 0.55, penumbra: 0.6, range: 24, color: 0xffb46b },\n  { pos: [17, 12, 63], target: [17, 0, 64], intensity: 200, angle: 0.55, penumbra: 0.6, range: 24, color: 0xffb46b },\n];"),
("const DRIVE_SPOT = { pos: [33, 16, 26], target: [33, 0, 66], intensity: 2600,\n                     angle: 0.95, penumbra: 0.8, range: 66, color: 0xfff2e4 };",
 "// Two overlapping wide, fully-feathered spots from the garage eave: a broad,\n// near-even wash with no cone edge anywhere in frame (a single 0.95 rad cone\n// drew a hard grey wedge from the car to the bottom-right), falling to ~2/255\n// by the bottom edge on the range cutoff. The first casts the car's shadow.\nconst DRIVE_SPOTS = [\n  { pos: [28, 14, 26], target: [28, 0, 62], intensity: 1300, angle: 1.2, penumbra: 1.0, range: 60, color: 0xfff2e4, shadow: true },\n  { pos: [40, 14, 26], target: [40, 0, 62], intensity: 1100, angle: 1.2, penumbra: 1.0, range: 60, color: 0xfff2e4 },\n];"),
("let spot = null;           // the blue uplight (also in `lights`)\nlet spotTargetLocal = null;\nlet driveSpot = null;\nlet driveTargetLocal = null;",
 "const spotTargets = [];    // [{light, local}] every SpotLight's aim point, shell-local"),
("    spot.target.position.copy(spotTargetLocal).applyMatrix4(shell.matrixWorld);\n    driveSpot.target.position.copy(driveTargetLocal).applyMatrix4(shell.matrixWorld);",
 "    for (const t of spotTargets) t.light.target.position.copy(t.local).applyMatrix4(shell.matrixWorld);"),
# ---- 6. lit window: warmer, framed, and a glow onto the siding round it
("  ctx.fillStyle = '#ffe2b0';\n  ctx.fillRect(0, 0, 32, 128);",
 "  ctx.fillStyle = '#ffd9a0';\n  ctx.fillRect(0, 0, 32, 128);"),
("  ctx.fillStyle = grad;\n  ctx.fillRect(0, 0, 32, 128);\n  const tex = new THREE.CanvasTexture(cv);",
 "  ctx.fillStyle = grad;\n  ctx.fillRect(0, 0, 32, 128);\n  // the sash frame\n  ctx.strokeStyle = 'rgba(60, 40, 20, 0.85)';\n  ctx.lineWidth = 3;\n  ctx.strokeRect(1.5, 1.5, 29, 125);\n  ctx.fillStyle = 'rgba(60, 40, 20, 0.7)';\n  ctx.fillRect(0, 62, 32, 3);\n  const tex = new THREE.CanvasTexture(cv);"),
("  win.name = 'litWindow';\n  win.renderOrder = 2;\n  group.add(win);",
 "  win.name = 'litWindow';\n  win.renderOrder = 2;\n  group.add(win);\n  // the light it throws onto the siding round the frame\n  glowMat = new THREE.MeshBasicMaterial({\n    map: makeGlowTexture(), transparent: true, opacity: 0, toneMapped: false,\n    blending: THREE.AdditiveBlending, depthWrite: false,\n  });\n  const glow = new THREE.Mesh(new THREE.PlaneGeometry((w.x1 - w.x0) * 2.4, (w.y1 - w.y0) * 1.7), glowMat);\n  glow.position.copy(win.position).add(new THREE.Vector3(0, 0, 0.03));\n  glow.name = 'litWindowGlow';\n  glow.renderOrder = 2;\n  group.add(glow);"),
("let windowMat = null;", "let windowMat = null;\nlet glowMat = null;"),
("  for (const m of [ledMat, haloMat, bleedMat, washMat, windowMat]) {", "  for (const m of [ledMat, haloMat, bleedMat, washMat, windowMat, glowMat]) {"),
("bleedMat = null; washMat = null; windowMat = null;", "bleedMat = null; washMat = null; windowMat = null; glowMat = null;"),
("  windowMat.opacity = night;\n  windowMat.visible = on;", "  windowMat.opacity = night;\n  windowMat.visible = on;\n  glowMat.opacity = night;\n  glowMat.visible = on;"),
("// warm light through a closed venetian blind",
 "// warm radial glow for the siding round the lit window\nfunction makeGlowTexture() {\n  const cv = document.createElement('canvas');\n  cv.width = cv.height = 128;\n  const ctx = cv.getContext('2d');\n  const g = ctx.createRadialGradient(64, 64, 6, 64, 64, 64);\n  g.addColorStop(0, 'rgba(255, 200, 140, 0.55)');\n  g.addColorStop(0.35, 'rgba(255, 190, 120, 0.22)');\n  g.addColorStop(1, 'rgba(255, 180, 100, 0)');\n  ctx.fillStyle = g;\n  ctx.fillRect(0, 0, 128, 128);\n  const tex = new THREE.CanvasTexture(cv);\n  tex.colorSpace = THREE.SRGBColorSpace;\n  return tex;\n}\n\n// warm light through a closed venetian blind"),
]
for a, b in rep:
    assert s.count(a) >= 1, a[:70]
    s = s.replace(a, b)

NEW_INIT = r'''  // The lights, once, before the boot compile (see the header).
  const addPoint = (name, pos, intensity, range, color) => {
    const light = new THREE.PointLight(color, 0, range, 2);
    light.name = name;
    scene.add(light);
    lights.push({ light, local: new THREE.Vector3(...pos), base: intensity });
  };
  const addSpot = (name, cfg) => {
    const light = new THREE.SpotLight(cfg.color, 0, cfg.range, cfg.angle, cfg.penumbra, 2);
    light.name = name;
    if (cfg.shadow) {
      // The one shadow-casting light here: without it the car floats on the lit
      // concrete. Set ONCE at init (a shadow toggle is a program cache-key term,
      // like the light count). The spot's own fov is the shadow frustum, so the
      // car (x ~28, z 58..74) sits inside it; near/far trimmed to the drive.
      light.castShadow = true;
      light.shadow.mapSize.set(2048, 2048);
      light.shadow.camera.near = 4;
      light.shadow.camera.far = 70;
      light.shadow.bias = -0.0004;
      light.shadow.normalBias = 0.3;
    }
    scene.add(light);
    scene.add(light.target);
    lights.push({ light, local: new THREE.Vector3(...cfg.pos), base: cfg.intensity });
    spotTargets.push({ light, local: new THREE.Vector3(...cfg.target) });
  };
  for (const p of PORCH_POINTS) addPoint('eaveLight:porch', p, PORCH_INTENSITY, PORCH_RANGE, 0xffb46b);
  for (const p of AMBER_POINTS) addPoint('eaveLight:amber', p, AMBER_INTENSITY, AMBER_RANGE, AMBER);
  for (const c of WALK_SPOTS) addSpot('eaveLight:walk', c);
  for (const c of DRIVE_SPOTS) addSpot('eaveLight:drive', c);
  addSpot('eaveLight:blue', BLUE_SPOT);
  // the measured numbers are world feet; the lights are placed relative to the
  // shell, so express them in its local space like the geometry
  const toLocal = measuredToLocal();
  for (const l of lights) l.local.applyMatrix4(toLocal);
  for (const t of spotTargets) t.local.applyMatrix4(toLocal);

'''
s = block(s, "  // The lights, once, before the boot compile (see the header).", "  // The night sky:", NEW_INIT)
open(p, 'w', encoding='utf-8').write(s)

# ---- roomlights exterior branch: the coach lamps and floods are lamps, not novas
p = ROOT + r"\frontend\js\roomlights.js"
s = open(p, encoding='utf-8').read()
rep = [
("const EXTERIOR_BASE = 70;\nconst EXTERIOR_RANGE = 34;         // ft",
 "// 70 cd blew the siding round every sconce to white and, once scene.js's\n// night bloom landed, fogged the whole upper frame off the garage floods.\n// 18 cd puts ~150/255 on the wall a foot under the lamp, like the photograph.\nconst EXTERIOR_BASE = 18;\nconst EXTERIOR_RANGE = 26;         // ft"),
]
for a, b in rep:
    assert s.count(a) >= 1, a[:70]
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('ok')
