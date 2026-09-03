ROOT = r"C:\Users\Manuel\Desktop\Pro\3d HA"
p = ROOT + r"\frontend\js\eavelights.js"
s = open(p, encoding='utf-8').read()
rep = [
# sky grain: isotropic and sub-visible (r6 tiled a 256x128 map 6x1 over the dome -> vertical streaks)
("  cv.width = 256; cv.height = 128;\n  const ctx = cv.getContext('2d');\n  const img = ctx.createImageData(256, 128);\n  let seed = 3;\n  for (let y = 0; y < 128; y++) {\n    const t = y / 127;                     // 0 = top of the dome, 1 = horizon\n    const base = 1.5 + 5.5 * t * t;\n    for (let x = 0; x < 256; x++) {\n      seed = (seed * 16807) % 2147483647;\n      const n = (seed / 2147483647 - 0.5) * 4;",
 "  // 256x256 tiled 8x4 over the dome: ~0.18 degrees per texel both ways. An\n  // anisotropic tile (r6: 256x128 tiled 6x1) read as vertical streaks.\n  cv.width = 256; cv.height = 256;\n  const ctx = cv.getContext('2d');\n  const img = ctx.createImageData(256, 256);\n  let seed = 3;\n  for (let y = 0; y < 256; y++) {\n    const t = y / 255;                     // 0 = top of the tile, 1 = bottom\n    const base = 1.5 + 3.0 * t;\n    for (let x = 0; x < 256; x++) {\n      seed = (seed * 16807) % 2147483647;\n      const n = (seed / 2147483647 - 0.5) * 2.4;"),
("  tex.wrapS = THREE.RepeatWrapping;\n  tex.repeat.x = 6;", "  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;\n  tex.repeat.set(8, 4);"),
# wash: r6 over-cut (gable field metered 45 vs the photo's 85, near-rake 62 vs 148)
("    const alpha = w.alpha ?? 0.42;", "    const alpha = w.alpha ?? 0.6;"),
("        const f = alpha * Math.pow(1 - t, 2.6);", "        const f = alpha * Math.pow(1 - t, 2.0);"),
("down: [R2, -R2, 0], width: 4, clampY: 24.2 },", "down: [R2, -R2, 0], width: 5.5, clampY: 24.2 },"),
("down: [-R2, -R2, 0], width: 4, clampY: 24.2 },", "down: [-R2, -R2, 0], width: 5.5, clampY: 24.2 },"),
("down: [R2, -R2, 0], width: 4 },", "down: [R2, -R2, 0], width: 5.5 },"),
("down: [-R2, -R2, 0], width: 4, clampY: 23.8 },", "down: [-R2, -R2, 0], width: 5.5, clampY: 23.8 },"),
("  { a: [20.6, 13.0, 29.9], b: [46.5, 13.0, 29.9], down: [0, -1, 0], width: 3.5 },",
 "  { a: [20.6, 13.0, 29.9], b: [46.5, 13.0, 29.9], down: [0, -1, 0], width: 4.5 },"),
# porch: brighter ceiling, but a range that dies before the second-floor siding
# (point lights are occluded by nothing, and at range 26 they were lifting the
# upstairs wall to ~37 where the photo has ~7-20)
("const PORCH_INTENSITY = 22;\nconst PORCH_RANGE = 26;", "const PORCH_INTENSITY = 30;\nconst PORCH_RANGE = 16;"),
("const STEP_POOL = { pos: [13.5, 3.0, 46.0], intensity: 7, range: 9, color: 0xffc080 };",
 "const STEP_POOL = { pos: [13.5, 3.0, 46.0], intensity: 10, range: 10, color: 0xffc080 };"),
]
for a, b in rep:
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)

p = ROOT + r"\frontend\js\daylight.js"
s = open(p, encoding='utf-8').read()
rep = [
("  [-18, 0xff8844, 0.00, 0x1e2028, 0x07080c, 0.15, 0x010203], // night",
 "  [-18, 0xff8844, 0.00, 0x1e2028, 0x07080c, 0.12, 0x010203], // night"),
# the IBL was the dominant night ambient: RoomEnvironment is a lit white box,
# so 0.05 of it put more on the driveway than the hemisphere did
("    THREE.MathUtils.lerp(1.15, 0.05, target.nightFactor) * w.hemiX;",
 "    THREE.MathUtils.lerp(1.15, 0.02, target.nightFactor) * w.hemiX;"),
]
for a, b in rep:
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('ok')
