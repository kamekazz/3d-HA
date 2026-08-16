"""Two-point log-linear probe: solve each wall's skin albedo from real renders.

    python probe.py 16

Renders the four look_* poses with every wall skinned at grey A, then again at
grey B, meters the SAME clean wall boxes both times (boxes verified by eye on
<img>_boxes.png), and fits  meter = f(albedo)  per wall.  The analytic tone
inverse stopped predicting after the daylight change, so this measures instead.
"""
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = r"C:\Users\Manuel\Desktop\Pro\3d HA\tools"
PY = sys.executable

sys.path.insert(0, HERE)
from bkit import fit_skin, grey, save_here                            # noqa: E402

# clean-wall sample boxes, per look pose, in render pixels (1100x850)
BOXES = {
    16: {
        "look_n": [(580, 360, 880, 760)],
        "look_s": [(585, 300, 645, 480), (300, 320, 370, 480)],
        "look_e": [(880, 300, 970, 600)],
        "look_w": [(620, 300, 740, 560), (60, 320, 160, 560)],
    },
}
WALLOF = {"look_n": "n", "look_s": "s", "look_e": "e", "look_w": "w"}


def shot(room, level, pose, out):
    poses = json.loads(subprocess.check_output(
        [PY, "-m", "roomkit.rooms", str(room), "--poses-only"], cwd=TOOLS))
    subprocess.run([PY, "-m", "roomkit.shot", "--pose-json",
                    json.dumps(poses[pose]), "--level", str(level),
                    "--day", "--out", out], cwd=TOOLS, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def meter(path, boxes, save=None):
    im = Image.open(path).convert("RGB")
    a = np.asarray(im).astype(np.float32)
    dbg = im.copy()
    d = ImageDraw.Draw(dbg)
    tot, n = 0.0, 0
    parts = []
    for (x0, y0, x1, y1) in boxes:
        p = a[y0:y1, x0:x1]
        lum = p @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
        tot += float(lum.sum())
        n += lum.size
        parts.append((lum.size, round(float(lum.mean()), 1),
                      round(float(lum.std()), 1)))
        d.rectangle([x0, y0, x1, y1], outline=(255, 0, 0), width=2)
    if save:
        dbg.save(save)
    return tot / n, n, parts


def run(room, level, build, colors, tag):
    save_here(build["skin_name"], build["make"](colors), room)
    out = {}
    for pose, boxes in BOXES[room].items():
        png = os.path.join(HERE, "shots", f"p_{tag}_{pose}.png")
        shot(room, level, pose, png)
        mean, n, parts = meter(png, boxes,
                               save=png.replace(".png", "_boxes.png"))
        out[WALLOF[pose]] = (mean, n, parts)
    return out


def main():
    room = int(sys.argv[1])
    if room == 16:
        import b16 as mod
        level = 2
        build = {"skin_name": "Master Bath Wall Wash", "make": mod.build_skins}
    elif room == 26:
        import b26 as mod
        level = 2
        build = {"skin_name": "Bath2F Wall Wash", "make": mod.build_skins}
    else:
        import b23 as mod
        level = 1
        build = {"skin_name": "Bath1F Wall Wash", "make": mod.build_skins}

    A, B = 250, 120
    ca = {w: grey(A) for w in "nesw"}
    cb = {w: grey(B) for w in "nesw"}
    ra = run(room, level, build, ca, "a")
    rb = run(room, level, build, cb, "b")

    target = float(sys.argv[2]) if len(sys.argv) > 2 else 190.0
    solved = {}
    print(f"\nwall   probe{A:>4}  probe{B:>4}   -> albedo for target {target:.0f}")
    for w in "nesw":
        ma, mb = ra[w][0], rb[w][0]
        v = fit_skin(A, ma, B, mb, target)
        solved[w] = grey(v)
        print(f"  {w}    {ma:7.1f}  {mb:7.1f}    {solved[w]}  ({v})"
              f"   n={ra[w][1]}")
    print(json.dumps(solved))
    with open(os.path.join(HERE, f"skins{room}.json"), "w") as f:
        json.dump(solved, f)


if __name__ == "__main__":
    main()
