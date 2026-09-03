ROOT = r"C:\Users\Manuel\Desktop\Pro\3d HA"
p = ROOT + r"\frontend\js\eavelights.js"
s = open(p, encoding='utf-8').read()
rep = [
# drive: r11 put 30-86 on the concrete by the car (photo 20-57) but 9-14 at
# the bottom of the frame (photo 2) and 4-9 on the lawn beside it (photo 2-3).
# Shorter range so the cutoff kills it by the street; tighter cone so the
# lawn west of the drive only ever sees the penumbra.
("const DRIVE_SPOT = { pos: [33, 12.6, 33], target: [33, 0, 64], intensity: 2400,\n                     angle: 0.7, penumbra: 0.5, range: 70, color: 0xffd2a0 };",
 "const DRIVE_SPOT = { pos: [33, 12.6, 33], target: [33, 0, 62], intensity: 2000,\n                     angle: 0.6, penumbra: 0.5, range: 48, color: 0xffd2a0 };"),
# main gable still 179/156/118 against the photo's 143/100/71 down the rake
("down: [R2, -R2, 0], width: 7.5, alpha: 0.62 },", "down: [R2, -R2, 0], width: 7.5, alpha: 0.5 },"),
("down: [-R2, -R2, 0], width: 7.5, clampY: 23.8, alpha: 0.62 },", "down: [-R2, -R2, 0], width: 7.5, clampY: 23.8, alpha: 0.5 },"),
]
for a, b in rep:
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('ok')
