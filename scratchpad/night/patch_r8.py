ROOT = r"C:\Users\Manuel\Desktop\Pro\3d HA"
p = ROOT + r"\frontend\js\eavelights.js"
s = open(p, encoding='utf-8').read()
rep = [
# sky: flat grain only. A per-tile vertical gradient tiled 4x over the dome
# drew four visible bands (r7 showed one as a dark arc across the top).
("  for (let y = 0; y < 256; y++) {\n    const t = y / 255;                     // 0 = top of the tile, 1 = bottom\n    const base = 1.5 + 3.0 * t;\n    for (let x = 0; x < 256; x++) {",
 "  for (let y = 0; y < 256; y++) {\n    const base = 2.6;                      // flat: any gradient tiles into bands\n    for (let x = 0; x < 256; x++) {"),
("// Tiled grain for the sky dome: near-black with a faint vertical gradient\n// (blacker at the zenith), a hair of blue, and +-2/255 noise.",
 "// Tiled grain for the sky dome: near-black, a hair of blue, +-1/255 noise."),
# gable field: r7 metered 30/43 against the photo's 85/77 with the rakes at\n# 68/114 vs 148 -- the wash needs to reach the field, not just rim the rakes
("    const alpha = w.alpha ?? 0.6;", "    const alpha = w.alpha ?? 0.72;"),
("        const f = alpha * Math.pow(1 - t, 2.0);", "        const f = alpha * Math.pow(1 - t, 1.5);"),
("down: [R2, -R2, 0], width: 5.5, clampY: 24.2 },", "down: [R2, -R2, 0], width: 8, clampY: 24.2 },"),
("down: [-R2, -R2, 0], width: 5.5, clampY: 24.2 },", "down: [-R2, -R2, 0], width: 8, clampY: 24.2 },"),
("down: [R2, -R2, 0], width: 5.5 },", "down: [R2, -R2, 0], width: 8 },"),
("down: [-R2, -R2, 0], width: 5.5, clampY: 23.8 },", "down: [-R2, -R2, 0], width: 8, clampY: 23.8 },"),
# porch ceiling 82 vs 142; walk at the steps 24 vs 110
("const PORCH_INTENSITY = 30;", "const PORCH_INTENSITY = 40;"),
("const STEP_POOL = { pos: [13.5, 3.0, 46.0], intensity: 10, range: 10, color: 0xffc080 };",
 "const STEP_POOL = { pos: [13.5, 3.0, 46.0], intensity: 18, range: 12, color: 0xffc080 };"),
]
for a, b in rep:
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('ok')
