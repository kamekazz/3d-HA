"""Meter wall + floor together: one look_n shot (wall) and one plan shot (floor)."""
import json, os, subprocess, sys, tempfile
sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
from PIL import Image
import numpy as np

TOOLS = r"C:\Users\Manuel\Desktop\Pro\3d HA\tools"
PY = sys.executable
OUT = r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\lr5"


def lum(path, frac=0.24):
    a = np.asarray(Image.open(path).convert("RGB")).astype(np.float32)
    h, w = a.shape[:2]
    p = a[int(h*(.5-frac/2)):int(h*(.5+frac/2)), int(w*(.5-frac/2)):int(w*(.5+frac/2))]
    return float((p @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)).mean())


poses = json.loads(subprocess.check_output(
    [PY, "-m", "roomkit.rooms", "5", "--poses-only"], cwd=TOOLS))
res = {}
for name in sys.argv[1:] or ["look_n", "plan"]:
    png = os.path.join(OUT, f"probe_{name}.png")
    subprocess.run([PY, "-m", "roomkit.shot", "--pose-json", json.dumps(poses[name]),
                    "--level", "1", "--day", "--out", png], cwd=TOOLS, check=True,
                   stdout=subprocess.DEVNULL)
    res[name] = round(lum(png), 1)
print(json.dumps(res))
