"""ROUND 7 PROOF -- four machines' control decks at ONE scale, side by side.

Task 2 asks for the wiring to be proved in the pixels, not in the data: the
three art modules' DECKS tables must reach the render as different button
counts, colours, radii, proudness and layouts.  These four poses stand the same
distance off four decks and frame them identically, so any difference in the
strip is a difference in the geometry.

    $PY scratchpad/arc4/r7eng/decks_sbs.py [tag]
"""
import json
import os
import subprocess
import sys

_ROOT = r"C:\Users\Manuel\Desktop\Pro\3d HA"
PY = os.path.join(_ROOT, "backend", ".venv", "Scripts", "python.exe")
TOOLS = os.path.join(_ROOT, "tools")
OUT = os.path.join(_ROOT, "scratchpad", "arc4", "r7eng", "shots")

# local (x, z) -> world (x - 2.1, z - 11.9); slab y = 0.
SZ = [760, 560]
FOV = 38
# The aim offsets (+0.26 ft up, 0.93 ft "screen-left") are CALIBRATED, not
# derived: roomkit.shot's camera does not frame `target` at the image centre at
# this fov, so cal1/cal2 measured the offset once and every pose below carries
# the same one.  All four cameras therefore stand 3.35 ft off their own deck's
# centre at 1.75 ft above it, and the four frames are the same scale to within
# the run's own 0.2 ft of deck-height variation.
DECKS = [
    ("tmnt-turtles-in-time   2 sticks (cyan + black) / 13 buttons"
     "  =  7 jumbo r 0.098 + 6 admin r 0.042",
     [12.95, 4.23, 2.25], [16.30, 2.74, 1.32]),
    ("nba-jam   ball top + BAT top / 8 buttons r 0.082, scattered,"
     " no two share a v",
     [12.95, 4.29, -0.01], [16.30, 2.80, -0.94]),
    ("mortal-kombat   2 sticks / 16 buttons  =  the 5-button MK arc x2"
     " + 4 aux + 2 start",
     [12.95, 4.37, -2.27], [16.30, 2.88, -3.20]),
    ("golden-tee-3d-golf   NO stick / trackball r 0.125 / 2 buttons r 0.062",
     [11.45, 4.35, -6.10], [10.52, 2.86, -9.44]),
]


def main(tag="sbs"):
    os.makedirs(OUT, exist_ok=True)
    paths = []
    for i, (label, pos, tgt) in enumerate(DECKS):
        out = os.path.join(OUT, "%s_%d.png" % (tag, i))
        pose = {"pos": pos, "target": tgt, "fov": FOV, "size": SZ}
        r = subprocess.run([PY, "-m", "roomkit.shot", "--pose-json",
                            json.dumps(pose), "--level", "0", "--day",
                            "--no-cutaway", "--out", out],
                           cwd=TOOLS, capture_output=True, text=True)
        print(" ", label, r.returncode)
        paths.append((label, out))

    from PIL import Image, ImageDraw
    ims = [Image.open(p).convert("RGB") for _, p in paths]
    w, h = ims[0].size
    sheet = Image.new("RGB", (w * 2, (h + 22) * 2), (16, 16, 18))
    d = ImageDraw.Draw(sheet)
    for i, im in enumerate(ims):
        x, y = (i % 2) * w, (i // 2) * (h + 22)
        sheet.paste(im, (x, y))
        d.text((x + 8, y + h + 5), paths[i][0], fill=(235, 235, 235))
    p = os.path.join(OUT, "%s_sheet.png" % tag)
    sheet.save(p)
    print(p, sheet.size)


if __name__ == "__main__":
    main(*(sys.argv[1:] or ["sbs"]))
