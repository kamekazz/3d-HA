"""Two-point per-wall probe for the circulation rooms.

Shoots one CLOSE, narrow-fov pose per wall aimed at a patch that is bare wall
and nothing else (verified against the _boxes overlays), meters the centre
patch, and prints mean/sd so a per-wall albedo skin can be fitted from a real
render instead of guessed.  Also meters the floor from a plan-ish pose.

    python probe.py 12 1 tag [--skin "#aabbcc"]      # all four walls
"""
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw

TOOLS = r"C:\Users\Manuel\Desktop\Pro\3d HA\tools"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "shots")
PY = sys.executable
FRAC = 0.26

# world-feet poses: a close shot square-on to a KNOWN-CLEAN patch of each wall
POSES = {
    12: {
        "w": {"pos": [13.5, 13.5, 8.6], "target": [10.7, 13.5, 8.6]},
        "e": {"pos": [15.5, 13.5, 8.6], "target": [18.3, 13.5, 8.6]},
        "n": {"pos": [17.2, 13.5, 7.4], "target": [17.2, 13.5, 4.6]},
        "s": {"pos": [14.5, 13.0, 29.2], "target": [14.5, 15.9, 32.2]},
        "floor": {"pos": [15.7, 13.2, 13.2], "target": [15.7, 8.0, 10.6]},
    },
    17: {
        "w": {"pos": [13.3, 22.8, 12.9], "target": [10.5, 22.8, 12.9]},
        "e": {"pos": [15.8, 23.0, 22.6], "target": [18.6, 23.0, 22.6]},
        "n": {"pos": [11.6, 23.0, 9.4], "target": [11.6, 23.0, 6.6]},
        "s": {"pos": [16.0, 23.0, 20.5], "target": [16.0, 23.0, 23.3]},
        "floor": {"pos": [12.2, 22.6, 10.2], "target": [12.2, 18.0, 7.8]},
    },
    27: {
        "w": {"pos": [21.4, 22.6, 18.6], "target": [18.6, 22.6, 18.6]},
        "e": {"pos": [29.4, 20.6, 16.6], "target": [32.2, 20.6, 16.6]},
        "n": {"pos": [22.0, 23.0, 15.2], "target": [22.0, 23.0, 12.4]},
        "s": {"pos": [22.0, 23.0, 18.0], "target": [22.0, 23.0, 20.8]},
        "floor": {"pos": [22.0, 22.4, 15.4], "target": [22.0, 18.0, 13.0]},
    },
}


def stats(path, frac=FRAC):
    a = np.asarray(Image.open(path).convert("RGB")).astype(np.float32)
    h, w = a.shape[:2]
    y0, y1 = int(h * (0.5 - frac / 2)), int(h * (0.5 + frac / 2))
    x0, x1 = int(w * (0.5 - frac / 2)), int(w * (0.5 + frac / 2))
    p = a[y0:y1, x0:x1]
    lum = p @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    im = Image.open(path).convert("RGB")
    d = ImageDraw.Draw(im)
    d.rectangle([x0, y0, x1, y1], outline=(255, 0, 0), width=3)
    im.save(path.replace(".png", "_boxes.png"))
    return (round(float(lum.mean()), 1), round(float(lum.std()), 1), int(lum.size),
            [round(float(p[..., i].mean()), 1) for i in range(3)])


def main():
    room, level, tag = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    only = sys.argv[4:] or list(POSES[room])
    os.makedirs(OUT, exist_ok=True)
    for name in only:
        pose = dict(POSES[room][name])
        pose["fov"] = 26 if name != "floor" else 34
        pose["size"] = [800, 620]
        png = os.path.join(OUT, f"probe_{room}_{tag}_{name}.png")
        subprocess.run([PY, "-m", "roomkit.shot", "--pose-json", json.dumps(pose),
                        "--level", str(level), "--day", "--out", png],
                       cwd=TOOLS, check=True, stdout=subprocess.DEVNULL)
        mean, sd, n, rgb = stats(png)
        print(f"  {name:6s} mean={mean:6.1f} sd={sd:5.1f} n={n:<7d} rgb={rgb}")


if __name__ == "__main__":
    main()
