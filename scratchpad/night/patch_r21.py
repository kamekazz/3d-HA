ROOT = r"C:\Users\Manuel\Desktop\Pro\3d HA"

def patch(path, reps, min_count=1):
    s = open(path, encoding='utf-8').read()
    for a, b in reps:
        assert s.count(a) >= min_count, (path, a[:70])
        s = s.replace(a, b)
    open(path, 'w', encoding='utf-8').write(s)

# ------------------------------------------------------------ roomlights.js
patch(ROOT + r"\frontend\js\roomlights.js", [
("let assignmentDirty = false;",
 "let assignmentDirty = false;\n// Shot/debug override: every exterior renders as ON, night only, off by\n// default. The night photograph the exterior is judged against has every\n// sconce and flood lit; HA usually has them off at the hour a shot is taken.\nlet forceExt = false;"),
("  rec.level01 = rec.on\n    ? (b === null || b === undefined ? 1 : 0.15 + 0.85 * (b / 255))\n    : 0;\n",
 "  rec.level01 = rec.on\n    ? (b === null || b === undefined ? 1 : 0.15 + 0.85 * (b / 255))\n    : 0;\n  if (forceExt && isExterior(rec) && getNightFactor() > 0.5) {\n    rec.on = true;\n    rec.level01 = 1;\n  }\n"),
("  window.__roomlights = {\n    poolSize: () => POOL_SIZE,",
 "  window.__roomlights = {\n    poolSize: () => POOL_SIZE,\n    forceExteriors: (v) => {\n      forceExt = !!v;\n      for (const e of exteriors) refreshFixture(e);\n      assignmentDirty = true;\n    },"),
])

# ------------------------------------------------------------ shot.py
patch(ROOT + r"\tools\roomkit\shot.py", [
("async ({ pose, level, light, markers, cutaway }) => {", "async ({ pose, level, light, markers, cutaway, exteriorsOn }) => {"),
("  if (light) window.__daylight?.simulate(light);",
 "  if (light) window.__daylight?.simulate(light);\n  // --exteriors-on: the porch sconces and garage floods are HA lights that are\n  // usually off when a shot is taken; the night photo has them lit. Night-gated\n  // inside roomlights.js, so it is a no-op on a day shot.\n  if (exteriorsOn) window.__roomlights?.forceExteriors(true);"),
("def take(pose, out, level=DEFAULT_LEVEL, light=None, settle=1200, markers=False,\n         cutaway=True):",
 "def take(pose, out, level=DEFAULT_LEVEL, light=None, settle=1200, markers=False,\n         cutaway=True, exteriors_on=False):"),
("        info = page.evaluate(SETUP_JS, {\"pose\": pose, \"level\": level, \"light\": light,\n                                        \"markers\": markers, \"cutaway\": cutaway})",
 "        info = page.evaluate(SETUP_JS, {\"pose\": pose, \"level\": level, \"light\": light,\n                                        \"markers\": markers, \"cutaway\": cutaway,\n                                        \"exteriorsOn\": exteriors_on})"),
("        page.evaluate(SETUP_JS, {\"pose\": pose, \"level\": level, \"light\": light,\n                                        \"markers\": markers, \"cutaway\": cutaway})",
 "        page.evaluate(SETUP_JS, {\"pose\": pose, \"level\": level, \"light\": light,\n                                        \"markers\": markers, \"cutaway\": cutaway,\n                                        \"exteriorsOn\": exteriors_on})"),
("    p.add_argument(\"--settle\", type=int, default=1200)",
 "    p.add_argument(\"--settle\", type=int, default=1200)\n    p.add_argument(\"--exteriors-on\", dest=\"exteriors_on\", action=\"store_true\",\n                   help=\"render every exterior HA light (porch sconces, garage floods) as ON \"\n                        \"regardless of HA state -- night shots only; the reference photo has them lit\")"),
("    print(json.dumps(take(pose, a.out, level, light, a.settle, a.markers, a.cutaway)))",
 "    print(json.dumps(take(pose, a.out, level, light, a.settle, a.markers, a.cutaway,\n                          a.exteriors_on)))"),
])

# ------------------------------------------------------------ eavelights.js
patch(ROOT + r"\frontend\js\eavelights.js", [
# ground: no pools. One wide, fully feathered spot from the porch soffit over
# the walk fan / rock band / steps, two from the garage eave down the drive.
("const WALK_SPOTS = [\n  { pos: [14, 10, 52], target: [14.5, 0, 52], intensity: 380, angle: 0.6, penumbra: 0.7, range: 22, color: 0xffb46b },\n  { pos: [18.5, 10, 63], target: [19, 0, 64], intensity: 380, angle: 0.5, penumbra: 0.8, range: 22, color: 0xffb46b },\n];",
 "// A single wide, fully-feathered spot from the porch soffit: the walk fan, the\n// rock band, the step treads and the top of the drive in one even wash with no\n// pool edge anywhere (two tight 10 ft spots read as 'spotlights in a void').\nconst WALK_SPOTS = [\n  { pos: [18, 12.3, 41], target: [19, 0, 58], intensity: 320, angle: 0.9, penumbra: 1.0, range: 36, color: 0xffb46b },\n];"),
("const DRIVE_SPOTS = [\n  { pos: [28, 14, 26], target: [28, 0, 62], intensity: 2400, angle: 1.2, penumbra: 1.0, range: 68, color: 0xfff2e4, shadow: true },\n  { pos: [40, 14, 26], target: [40, 0, 68], intensity: 2800, angle: 1.2, penumbra: 1.0, range: 68, color: 0xfff2e4 },\n];",
 "const DRIVE_SPOTS = [\n  { pos: [34, 14, 26], target: [30, 0, 60], intensity: 2200, angle: 1.0, penumbra: 1.0, range: 62, color: 0xfff2e4, shadow: true },\n  { pos: [24, 14, 27], target: [21, 0, 58], intensity: 1400, angle: 1.0, penumbra: 1.0, range: 55, color: 0xfff2e4 },\n];"),
# blue: flood the west end -- column, west wall, the tree mass
("const BLUE_SPOT = { pos: [-30, 0.5, 55], target: [-18, 8, 38], intensity: 1600,\n                    angle: 0.45, penumbra: 0.5, range: 70, color: 0x2040ff };",
 "const BLUE_SPOT = { pos: [-34, 1, 52], target: [-10, 12, 34], intensity: 4500,\n                    angle: 0.6, penumbra: 0.5, range: 80, color: 0x2040ff };"),
# siding: each clapboard throws a real shadow line
("          p *= 1.0 - 0.28 * (1.0 - smoothstep(0.0, 0.12, f));", "          p *= 1.0 - 0.45 * (1.0 - smoothstep(0.0, 0.18, f));"),
# lit window: cool white through blinds, with a mullion
("  ctx.fillStyle = '#ffd9a0';\n  ctx.fillRect(0, 0, 32, 128);\n  ctx.fillStyle = 'rgba(110, 70, 30, 0.6)';",
 "  ctx.fillStyle = '#dfe9ff';                 // ~6000K: an LED ceiling light behind the blind\n  ctx.fillRect(0, 0, 32, 128);\n  ctx.fillStyle = 'rgba(40, 50, 80, 0.6)';"),
("  grad.addColorStop(0, 'rgba(255,250,230,0.45)');\n  grad.addColorStop(0.35, 'rgba(255,220,170,0)');\n  grad.addColorStop(1, 'rgba(40,20,5,0.7)');",
 "  grad.addColorStop(0, 'rgba(240,246,255,0.45)');\n  grad.addColorStop(0.35, 'rgba(220,230,255,0)');\n  grad.addColorStop(1, 'rgba(10,15,30,0.7)');"),
("  ctx.strokeStyle = 'rgba(60, 40, 20, 0.85)';\n  ctx.lineWidth = 3;\n  ctx.strokeRect(1.5, 1.5, 29, 125);\n  ctx.fillStyle = 'rgba(60, 40, 20, 0.7)';\n  ctx.fillRect(0, 62, 32, 3);",
 "  ctx.strokeStyle = 'rgba(30, 35, 50, 0.9)';\n  ctx.lineWidth = 3;\n  ctx.strokeRect(1.5, 1.5, 29, 125);\n  ctx.fillStyle = 'rgba(30, 35, 50, 0.8)';\n  ctx.fillRect(0, 62, 32, 3);                // meeting rail\n  ctx.fillRect(15, 0, 2, 128);               // mullion"),
("  g.addColorStop(0, 'rgba(255, 200, 140, 0.55)');\n  g.addColorStop(0.35, 'rgba(255, 190, 120, 0.22)');\n  g.addColorStop(1, 'rgba(255, 180, 100, 0)');",
 "  g.addColorStop(0, 'rgba(210, 225, 255, 0.5)');\n  g.addColorStop(0.35, 'rgba(200, 215, 255, 0.2)');\n  g.addColorStop(1, 'rgba(190, 210, 255, 0)');"),
])
print('ok')
