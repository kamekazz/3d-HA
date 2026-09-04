ROOT = r"C:\Users\Manuel\Desktop\Pro\3d HA"

def patch(path, reps):
    s = open(path, encoding='utf-8').read()
    for a, b in reps:
        assert s.count(a) >= 1, (path, a[:70])
        s = s.replace(a, b)
    open(path, 'w', encoding='utf-8').write(s)

patch(ROOT + r"\frontend\js\eavelights.js", [
# ---- ground: inverse-square from the roofline, not a wash. One eave spot whose
# cone ends at the car's rear; the sconces (roomlights) light the door apron.
("const DRIVE_SPOTS = [\n  { pos: [34, 14, 26], target: [30, 0, 60], intensity: 5000, angle: 1.0, penumbra: 1.0, range: 75, color: 0xfff2e4, shadow: true },\n  { pos: [24, 14, 27], target: [21, 0, 58], intensity: 3200, angle: 1.0, penumbra: 1.0, range: 70, color: 0xfff2e4 },\n  // the garage door face itself, from the eave (the photo has it as the\n  // brightest surface on that wall; the sconces alone leave it at ~70)\n  { pos: [33, 12.6, 34], target: [33, 3, 29.8], intensity: 420, angle: 0.75, penumbra: 0.8, range: 20, color: 0xffe6c8 },\n];",
 "const DRIVE_SPOTS = [\n  // the garage string's throw down the drive: the door apron is the sconces'\n  // (roomlights), this carries z 40..60 and the cone/range end at the car's\n  // rear, so nothing lights the car's rear face, plate or tyres\n  { pos: [33, 13, 30.5], target: [30, 0, 52], intensity: 300, angle: 0.75, penumbra: 1.0, range: 40, color: 0xfff2e4, shadow: true },\n  // the garage door face itself, from the eave (the photo has it as the\n  // brightest surface on that wall; the sconces alone leave it at ~70)\n  { pos: [33, 12.6, 34], target: [33, 3, 29.8], intensity: 1050, angle: 0.75, penumbra: 0.8, range: 20, color: 0xffe6c8 },\n];"),
("const WALK_SPOTS = [\n  { pos: [18, 12.3, 41], target: [19, 0, 58], intensity: 1400, angle: 0.9, penumbra: 1.0, range: 40, color: 0xffb46b },\n];",
 "const WALK_SPOTS = [\n  // short and steep: the steps and the upper fan; cone and range end at z ~58\n  { pos: [16, 12.3, 41], target: [15, 0, 54], intensity: 1000, angle: 0.7, penumbra: 1.0, range: 30, color: 0xffb46b },\n];\n// the low path light at the rock band's end, where the photo's is\nconst PATH_LIGHT = { pos: [11.6, 1.2, 57], intensity: 6, range: 9, color: 0xffb46b };"),
("  for (const c of WALK_SPOTS) addSpot('eaveLight:walk', c);",
 "  for (const c of WALK_SPOTS) addSpot('eaveLight:walk', c);\n  addPoint('eaveLight:path', PATH_LIGHT.pos, PATH_LIGHT.intensity, PATH_LIGHT.range, PATH_LIGHT.color);"),
# ---- porch ceiling -30%
("const PORCH_INTENSITY = 36;", "const PORCH_INTENSITY = 25;"),
# ---- siding band: a foot wider, softer knee, a touch less at the top
("width: 5.5, alpha: 0.66, clampY: 24.2, clap: true", "width: 6.5, alpha: 0.56, clampY: 24.2, clap: true, band: 1.6"),
("width: 5.5, alpha: 0.5, clap: true", "width: 6.5, alpha: 0.45, clap: true, band: 1.6"),
("width: 5.5, alpha: 0.5, clampY: 23.8, clap: true", "width: 6.5, alpha: 0.45, clampY: 23.8, clap: true, band: 1.6"),
("        float band = soffit ? 0.35 : 0.8;", "        float band = soffit ? 0.35 : 1.6;"),
("          : pow(max(0.0, 1.0 - (d - band) / max(0.01, W - band)), soffit ? 1.6 : 3.0);",
 "          : pow(max(0.0, 1.0 - (d - band) / max(0.01, W - band)), soffit ? 1.6 : 2.2);"),
# ---- blue: onto the west wall and the shrub mass, not up into bare branches
("const BLUE_SPOT = { pos: [-34, 1, 52], target: [-10, 12, 34], intensity: 4500,",
 "const BLUE_SPOT = { pos: [-34, 1, 52], target: [-10, 6, 34], intensity: 4500,"),
])
print('ok')
