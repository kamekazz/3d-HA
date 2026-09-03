ROOT = r"C:\Users\Manuel\Desktop\Pro\3d HA"
p = ROOT + r"\frontend\js\eavelights.js"
s = open(p, encoding='utf-8').read()
rep = [
# r14: the course shadow x the bulb pools tiled the gable into bricks --
# subtler, thinner course lines and a gentler scallop on the walls
("          p *= soffit ? (0.3 + 0.7 * pool) : (0.5 + 0.5 * pool);",
 "          p *= soffit ? (0.3 + 0.7 * pool) : (0.68 + 0.32 * pool);"),
("          p *= 1.0 - 0.5 * (1.0 - smoothstep(0.0, 0.22, f));",
 "          p *= 1.0 - 0.28 * (1.0 - smoothstep(0.0, 0.12, f));"),
# and the gable fields a stop down: the band under the bulbs must be the bright thing
("  { a: [-8.2, 26.32, 30.62], b: [1.74, 36.43, 30.62], down: [R2, -R2, 0], width: 6, alpha: 0.8, clampY: 24.2, clap: true },\n  { a: [1.74, 36.43, 30.62], b: [11.67, 26.32, 30.62], down: [-R2, -R2, 0], width: 6, alpha: 0.8, clampY: 24.2, clap: true },",
 "  { a: [-8.2, 26.32, 30.62], b: [1.74, 36.43, 30.62], down: [R2, -R2, 0], width: 5.5, alpha: 0.68, clampY: 24.2, clap: true },\n  { a: [1.74, 36.43, 30.62], b: [11.67, 26.32, 30.62], down: [-R2, -R2, 0], width: 5.5, alpha: 0.68, clampY: 24.2, clap: true },"),
("  { a: [2.3, 37.0, 27.82], b: [6.656, 41.437, 27.82], down: [R2, -R2, 0], width: 6, alpha: 0.6, clap: true },\n  { a: [6.656, 41.437, 27.82], b: [21.519, 26.322, 27.82], down: [-R2, -R2, 0], width: 6, alpha: 0.6, clampY: 23.8, clap: true },",
 "  { a: [2.3, 37.0, 27.82], b: [6.656, 41.437, 27.82], down: [R2, -R2, 0], width: 5.5, alpha: 0.5, clap: true },\n  { a: [6.656, 41.437, 27.82], b: [21.519, 26.322, 27.82], down: [-R2, -R2, 0], width: 5.5, alpha: 0.5, clampY: 23.8, clap: true },"),
# the walk at the steps fell to 33 when the pool moved onto the rock strip:
# park it between the two so both read (walk ~100, cobbles ~60)
("const STEP_POOL = { pos: [7.0, 6.0, 51.0], intensity: 70, range: 18, color: 0xffb46b };",
 "const STEP_POOL = { pos: [10.5, 6.0, 49.0], intensity: 95, range: 18, color: 0xffb46b };"),
]
for a, b in rep:
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('ok')
