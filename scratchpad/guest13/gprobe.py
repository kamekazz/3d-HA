"""Two-point wall probe for room 13.

Sets wall_color, shoots look_n/s/e/w and meters ONE clean patch of each wall
(above the chair rail) plus one wainscot patch, so a wall_color can be chosen
from a fitted slope instead of by eye.  Every box below was checked against an
m.py _boxes.png overlay.  Usage:  python gprobe.py "#d3d1cd" "#b0aeaa"
"""
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
from roomkit.place import _req                                  # noqa: E402

TOOLS = r"C:\Users\Manuel\Desktop\Pro\3d HA\tools"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "shots")
PY = sys.executable

# pose -> box of BARE wall above the chair rail (all verified on an overlay)
BOX = {"look_n": (730, 153, 1002, 297),
       "look_s": (60, 55, 235, 165),      # above the TV, upper wall
       "look_e": (600, 112, 770, 212),    # between the mirror and the door
       "look_w": (110, 135, 380, 245)}
WAINS = {"look_s": (102, 595, 272, 782), "look_w": (110, 560, 330, 750)}

POSES = json.loads(subprocess.check_output(
    [PY, "-m", "roomkit.rooms", "13", "--poses-only"], cwd=TOOLS))


def stats(path, b):
    a = np.asarray(Image.open(path).convert("RGB")).astype(np.float32)
    p = a[b[1]:b[3], b[0]:b[2]]
    lum = p @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    return float(lum.mean()), float(lum.std())


def run(color, tag, overlay=False):
    _req("PATCH", "/api/house/room/13", {"wall_color": color})
    vals, wv = {}, {}
    for name, b in BOX.items():
        png = os.path.join(OUT, "wp_%s_%s.png" % (tag, name))
        subprocess.run([PY, "-m", "roomkit.shot", "--pose-json",
                        json.dumps(POSES[name]), "--level", "2", "--day",
                        "--out", png], cwd=TOOLS, check=True,
                       stdout=subprocess.DEVNULL)
        vals[name] = stats(png, b)
        if name in WAINS:
            wv[name] = stats(png, WAINS[name])
        if overlay:
            im = Image.open(png).convert("RGB")
            d = ImageDraw.Draw(im)
            d.rectangle(list(b), outline=(255, 0, 0), width=3)
            if name in WAINS:
                d.rectangle(list(WAINS[name]), outline=(0, 160, 255), width=3)
            im.save(png.replace(".png", "_boxes.png"))
    avg = sum(v[0] for v in vals.values()) / 4
    print("%-9s %s  N=%.1f(sd%.1f) S=%.1f(sd%.1f) E=%.1f(sd%.1f) W=%.1f(sd%.1f)"
          "  AVG=%.1f   wainscot(S)=%.1f"
          % (tag, color, vals["look_n"][0], vals["look_n"][1],
             vals["look_s"][0], vals["look_s"][1], vals["look_e"][0],
             vals["look_e"][1], vals["look_w"][0], vals["look_w"][1], avg,
             wv.get("look_s", (0, 0))[0]))
    print("            wainscot S=%.1f(sd%.1f)  W=%.1f(sd%.1f)"
          % (wv["look_s"][0], wv["look_s"][1], wv["look_w"][0], wv["look_w"][1]))
    return vals, avg


if __name__ == "__main__":
    for a in sys.argv[1:]:
        run(a, a.lstrip("#"), overlay=True)
