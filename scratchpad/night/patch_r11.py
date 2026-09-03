ROOT = r"C:\Users\Manuel\Desktop\Pro\3d HA"
p = ROOT + r"\frontend\js\eavelights.js"
s = open(p, encoding='utf-8').read()
rep = [
# drive: measured at the pose (diag3.py): 380 cd -> 9/23 on the concrete,
# 3000 -> 52/112 against the photo's ~28/57; the spot's penumbra term halves
# what a point of the same candela puts down, and the concrete is 37 ft from
# the eave at the frame's mid-row. Narrower cone so the lawn west of the drive
# stays under the 4/255 line.
("const DRIVE_SPOT = { pos: [33, 12.6, 33], target: [33, 0, 58], intensity: 380,\n                     angle: 1.0, penumbra: 0.45, range: 60, color: 0xffd2a0 };",
 "const DRIVE_SPOT = { pos: [33, 12.6, 33], target: [33, 0, 64], intensity: 2400,\n                     angle: 0.7, penumbra: 0.5, range: 70, color: 0xffd2a0 };"),
# main gable peaked at 212 against the photo's 143; the front gable is right
("  { a: [2.3, 37.0, 27.82], b: [6.656, 41.437, 27.82], down: [R2, -R2, 0], width: 7.5 },\n  { a: [6.656, 41.437, 27.82], b: [21.519, 26.322, 27.82], down: [-R2, -R2, 0], width: 7.5, clampY: 23.8 },",
 "  { a: [2.3, 37.0, 27.82], b: [6.656, 41.437, 27.82], down: [R2, -R2, 0], width: 7.5, alpha: 0.62 },\n  { a: [6.656, 41.437, 27.82], b: [21.519, 26.322, 27.82], down: [-R2, -R2, 0], width: 7.5, clampY: 23.8, alpha: 0.62 },"),
# blue: the yard's west trees are bare winter branches, so most of the cone
# passes through them -- brighter, and aimed a little lower so the trunks and
# the ground under them carry it
("const BLUE_SPOT = { pos: [-30, 0.5, 55], target: [-18, 10, 38], intensity: 900,\n                    angle: 0.45, penumbra: 0.5, range: 70, color: 0x2040ff };",
 "const BLUE_SPOT = { pos: [-30, 0.5, 55], target: [-18, 8, 38], intensity: 1600,\n                    angle: 0.45, penumbra: 0.5, range: 70, color: 0x2040ff };"),
]
for a, b in rep:
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('ok')
