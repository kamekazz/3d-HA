ROOT = r"C:\Users\Manuel\Desktop\Pro\3d HA"
p = ROOT + r"\frontend\js\eavelights.js"
s = open(p, encoding='utf-8').read()
rep = [
# ground: measured (diag2.py) -- 110 cd put 33/255 on the concrete 17 ft out;
# the photo wants ~90 there, ~38 at the car, single digits by the street
("const DRIVE_SPOT = { pos: [33, 12.6, 33], target: [33, 0, 58], intensity: 110,\n                     angle: 1.0, penumbra: 0.45, range: 70, color: 0xffd2a0 };",
 "const DRIVE_SPOT = { pos: [33, 12.6, 33], target: [33, 0, 58], intensity: 380,\n                     angle: 1.0, penumbra: 0.45, range: 60, color: 0xffd2a0 };"),
("const STEP_POOL = { pos: [14.0, 4.0, 47.0], intensity: 30, range: 14, color: 0xffc080 };",
 "const STEP_POOL = { pos: [14.0, 4.0, 47.0], intensity: 75, range: 16, color: 0xffc080 };"),
# gable profile: r9 metered 143/193/104/46/12 down the front gable against the\n# photo's 78/147/176/99/51 -- right shape, band a foot short and the tail too fast
("    const alpha = w.alpha ?? 0.85;\n    const band = (w.band ?? 1.5) / w.width;   // fraction of the width at full strength",
 "    const alpha = w.alpha ?? 0.8;\n    const band = (w.band ?? 2.2) / w.width;   // fraction of the width at full strength"),
("        const f = alpha * (t < band ? 1 : Math.pow((1 - t) / (1 - band), 3));",
 "        const f = alpha * (t < band ? 1 : Math.pow((1 - t) / (1 - band), 2.2));"),
("down: [R2, -R2, 0], width: 6.5, clampY: 24.2 },", "down: [R2, -R2, 0], width: 7.5, clampY: 24.2 },"),
("down: [-R2, -R2, 0], width: 6.5, clampY: 24.2 },", "down: [-R2, -R2, 0], width: 7.5, clampY: 24.2 },"),
("down: [R2, -R2, 0], width: 6.5 },", "down: [R2, -R2, 0], width: 7.5 },"),
("down: [-R2, -R2, 0], width: 6.5, clampY: 23.8 },", "down: [-R2, -R2, 0], width: 7.5, clampY: 23.8 },"),
]
for a, b in rep:
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('ok')
