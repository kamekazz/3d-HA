ROOT = r"C:\Users\Manuel\Desktop\Pro\3d HA"
p = ROOT + r"\frontend\js\eavelights.js"
s = open(p, encoding='utf-8').read()
rep = [
# ---- wash: a bright band hugging the fascia, then a cubic decay. The critic's
# point: the photo's gable is near-white 1 ft under the rake and ~60/255 at the
# window head; a smooth (1-t)^1.5 over 8 ft filled the field flat.
("    const alpha = w.alpha ?? 0.72;", "    const alpha = w.alpha ?? 0.85;\n    const band = (w.band ?? 1.5) / w.width;   // fraction of the width at full strength"),
("    const rows = 6; // alpha samples across the width -- the falloff is a curve",
 "    const rows = 12; // alpha samples across the width -- the falloff is a curve"),
("        const f = alpha * Math.pow(1 - t, 1.5);",
 "        const f = alpha * (t < band ? 1 : Math.pow((1 - t) / (1 - band), 3));"),
("down: [R2, -R2, 0], width: 8, clampY: 24.2 },", "down: [R2, -R2, 0], width: 6.5, clampY: 24.2 },"),
("down: [-R2, -R2, 0], width: 8, clampY: 24.2 },", "down: [-R2, -R2, 0], width: 6.5, clampY: 24.2 },"),
("down: [R2, -R2, 0], width: 8 },", "down: [R2, -R2, 0], width: 6.5 },"),
("down: [-R2, -R2, 0], width: 8, clampY: 23.8 },", "down: [-R2, -R2, 0], width: 6.5, clampY: 23.8 },"),
("  { a: [-7.5, 16.4, 29.68], b: [14.4, 16.4, 29.68], down: [0, 1, 0], width: 3, alpha: 0.14 },\n  { a: [15.0, 16.4, 26.86], b: [21.4, 16.4, 26.86], down: [0, 1, 0], width: 3, alpha: 0.14 },",
 "  { a: [-7.5, 16.4, 29.68], b: [14.4, 16.4, 29.68], down: [0, 1, 0], width: 2, alpha: 0.12, band: 0.3 },\n  { a: [15.0, 16.4, 26.86], b: [21.4, 16.4, 26.86], down: [0, 1, 0], width: 2, alpha: 0.12, band: 0.3 },"),
("  { a: [20.6, 13.0, 29.9], b: [46.5, 13.0, 29.9], down: [0, -1, 0], width: 4.5 },",
 "  { a: [20.6, 13.0, 29.9], b: [46.5, 13.0, 29.9], down: [0, -1, 0], width: 6, alpha: 0.8 },"),
("  { a: [21.0, 26.25, 27.9], b: [21.0, 26.25, -12.0], down: [0, -1, 0], width: 3.5 },",
 "  { a: [21.0, 26.25, 27.9], b: [21.0, 26.25, -12.0], down: [0, -1, 0], width: 5 },"),
("down: [0, -1, 0], width: 0.55, alpha: 0.45 },", "down: [0, -1, 0], width: 0.55, alpha: 0.45, band: 0.2 },"),
# ---- LEDs: the brightest pixels in the frame, each with its own bloom
("  const haloBright = dots.map(() => 0.85 + 0.3 * rnd());", "  const haloBright = dots.map(() => 0.75 + 0.5 * rnd());"),
("  // +-15% per-LED brightness, seeded so the string never twinkles between builds",
 "  // +-25% per-LED brightness, seeded so the string never twinkles between builds"),
("        float core = smoothstep(0.30, 0.06, d);\n        float skirt = pow(max(0.0, 1.0 - d), 1.5) * 0.5;\n        vec3 c = mix(vColor, vec3(1.0), core * 0.6) * (core + skirt);",
 "        float core = smoothstep(0.32, 0.05, d);\n        float skirt = pow(max(0.0, 1.0 - d), 1.2) * 0.6;\n        // the core overshoots 1.0 on purpose: additive onto lit siding it must\n        // still clip to white, or the dot is just a pinhead riding on the wash\n        vec3 c = mix(vColor, vec3(1.0), core * 0.8) * (core * 1.9 + skirt);"),
("  ledMat.emissiveIntensity = 2.8 * night;", "  ledMat.emissiveIntensity = 6.0 * night;"),
# ---- ground: the drive is lit by the garage string (13 ft up, 27 ft of LEDs).
# One wide spot from the eave, aimed down the drive; its cone excludes the wall
# behind it, so the garage face keeps the strip's falloff.
("const STEP_POOL = { pos: [13.5, 3.0, 46.0], intensity: 18, range: 12, color: 0xffc080 };",
 "const STEP_POOL = { pos: [14.0, 4.0, 47.0], intensity: 30, range: 14, color: 0xffc080 };\n// The concrete is the brightest ground surface in the photo: warm grey ~35%\n// under the garage string, ~15% at the car, black by the street.\nconst DRIVE_SPOT = { pos: [33, 12.6, 33], target: [33, 0, 58], intensity: 110,\n                     angle: 1.0, penumbra: 0.45, range: 70, color: 0xffd2a0 };"),
("let spot = null;           // the blue uplight (also in `lights`)\nlet spotTargetLocal = null;",
 "let spot = null;           // the blue uplight (also in `lights`)\nlet spotTargetLocal = null;\nlet driveSpot = null;\nlet driveTargetLocal = null;"),
("  spot = new THREE.SpotLight(BLUE_SPOT.color, 0, BLUE_SPOT.range, BLUE_SPOT.angle,\n                             BLUE_SPOT.penumbra, 2);",
 "  driveSpot = new THREE.SpotLight(DRIVE_SPOT.color, 0, DRIVE_SPOT.range, DRIVE_SPOT.angle,\n                                  DRIVE_SPOT.penumbra, 2);\n  driveSpot.name = 'eaveLight:drive';\n  scene.add(driveSpot);\n  scene.add(driveSpot.target);\n  lights.push({ light: driveSpot, local: new THREE.Vector3(...DRIVE_SPOT.pos), base: DRIVE_SPOT.intensity });\n  driveTargetLocal = new THREE.Vector3(...DRIVE_SPOT.target);\n  spot = new THREE.SpotLight(BLUE_SPOT.color, 0, BLUE_SPOT.range, BLUE_SPOT.angle,\n                             BLUE_SPOT.penumbra, 2);"),
("  spotTargetLocal.applyMatrix4(toLocal);", "  spotTargetLocal.applyMatrix4(toLocal);\n  driveTargetLocal.applyMatrix4(toLocal);"),
("    spot.target.position.copy(spotTargetLocal).applyMatrix4(shell.matrixWorld);",
 "    spot.target.position.copy(spotTargetLocal).applyMatrix4(shell.matrixWorld);\n    driveSpot.target.position.copy(driveTargetLocal).applyMatrix4(shell.matrixWorld);"),
# ---- blue: onto the west tree mass (x -22..-14, z 30..45) and the west wall;
# raised axis so the lower cone edge only grazes the lawn
("const BLUE_SPOT = { pos: [-30, 3, 46], target: [-16, 6, 30], intensity: 1000,\n                    angle: 0.6, penumbra: 0.5, range: 70, color: 0x2040ff };",
 "const BLUE_SPOT = { pos: [-30, 0.5, 55], target: [-18, 10, 38], intensity: 900,\n                    angle: 0.45, penumbra: 0.5, range: 70, color: 0x2040ff };"),
# ---- amber: just in front of the actual shrubs (front bed east end: orange mum\n# x 5.3, dark-red mum 7.2, boxwood ~8.5 at z ~46-48; garage-corner group x 47..50 z 32..36)
("const AMBER_POINTS = [[2.0, 0.4, 47.5], [7.5, 0.4, 46.0], [49.0, 0.4, 44.0]];\nconst AMBER_INTENSITY = 4;\nconst AMBER_RANGE = 8;",
 "const AMBER_POINTS = [[5.3, 0.3, 49.0], [8.6, 0.3, 48.8], [48.5, 0.3, 37.5]];\nconst AMBER_INTENSITY = 5;\nconst AMBER_RANGE = 7;"),
]
for a, b in rep:
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('ok')
