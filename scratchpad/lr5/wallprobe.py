"""Two-point probe: set wall_color, shoot the four look_* poses, meter a
hand-verified CLEAN patch of each wall.  (Round 3 reported an average of the
two brightest walls only; these four boxes were each checked against the
_boxes.png overlay.)"""
import json, os, subprocess, sys
sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
from roomkit.place import _req
from PIL import Image
import numpy as np

TOOLS = r"C:\Users\Manuel\Desktop\Pro\3d HA\tools"
OUT = r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\lr5"
PY = sys.executable

# pose -> (x0, y0, x1, y1) of bare wall, verified visually
BOX = {"look_n": (690, 125, 1080, 200),
       "look_w": (390, 195, 700, 330),
       "look_e": (700, 200, 1000, 480),
       "look_s": (340, 150, 430, 500)}

POSES = json.loads(subprocess.check_output(
    [PY, "-m", "roomkit.rooms", "5", "--poses-only"], cwd=TOOLS))


def stats(path, b):
    a = np.asarray(Image.open(path).convert("RGB")).astype(np.float32)
    p = a[b[1]:b[3], b[0]:b[2]]
    lum = p @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    return float(lum.mean()), float(lum.std())


def run(color, tag):
    _req("PATCH", "/api/house/room/5", {"wall_color": color})
    vals = {}
    for name, b in BOX.items():
        png = os.path.join(OUT, f"wp_{tag}_{name}.png")
        subprocess.run([PY, "-m", "roomkit.shot", "--pose-json",
                        json.dumps(POSES[name]), "--level", "1", "--day",
                        "--out", png], cwd=TOOLS, check=True,
                       stdout=subprocess.DEVNULL)
        vals[name] = stats(png, b)
    avg = sum(v[0] for v in vals.values()) / 4
    print("%-9s %s  N=%.1f W=%.1f E=%.1f S=%.1f  AVG=%.1f" % (
        tag, color, vals["look_n"][0], vals["look_w"][0], vals["look_e"][0],
        vals["look_s"][0], avg))
    return vals, avg


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        run(arg, arg.lstrip("#"))
