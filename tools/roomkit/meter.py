"""Meter how bright each interior wall of an EMPTY room actually renders.

Every builder so far has independently discovered that walls facing away from
the sun render far darker than the photographs, and each has papered over it
with a per-room emissive "wall wash" — which critics then flagged as visible
hard-edged panels. Before changing the scene lighting, measure the deficit.

Uses an unfurnished room so no builder's emissive confounds the reading, shoots
the four wall-facing poses, and reports the mean/sd of the central patch of each
render (which is wall and nothing else).

    python -m roomkit.meter 13 --level 2
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile

from PIL import Image
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
TOOLS = os.path.abspath(os.path.join(HERE, ".."))


def patch_stats(path, frac=0.28):
    """Mean/sd of the centre patch — for a look_* pose that is bare wall."""
    im = Image.open(path).convert("RGB")
    a = np.asarray(im).astype(np.float32)
    h, w = a.shape[:2]
    y0, y1 = int(h * (0.5 - frac / 2)), int(h * (0.5 + frac / 2))
    x0, x1 = int(w * (0.5 - frac / 2)), int(w * (0.5 + frac / 2))
    p = a[y0:y1, x0:x1]
    lum = p @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    return {"mean": round(float(lum.mean()), 1), "sd": round(float(lum.std()), 1),
            "rgb": [round(float(p[..., i].mean()), 1) for i in range(3)]}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("room", type=int)
    p.add_argument("--level", type=int, required=True)
    p.add_argument("--tag", default="meter")
    p.add_argument("--day", action="store_true", default=True)
    a = p.parse_args()

    poses = json.loads(subprocess.check_output(
        [PY, "-m", "roomkit.rooms", str(a.room), "--poses-only"], cwd=TOOLS))

    out = {}
    tmp = tempfile.mkdtemp(prefix="meter")
    for name in ("look_n", "look_s", "look_e", "look_w"):
        png = os.path.join(tmp, f"{a.tag}_{name}.png")
        cmd = [PY, "-m", "roomkit.shot", "--pose-json", json.dumps(poses[name]),
               "--level", str(a.level), "--out", png]
        if a.day:
            cmd.append("--day")
        subprocess.run(cmd, cwd=TOOLS, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        out[name] = patch_stats(png)

    means = [v["mean"] for v in out.values()]
    print(json.dumps(out, indent=2))
    print(f"\nroom {a.room}: brightest wall {max(means):.0f}, darkest {min(means):.0f}, "
          f"spread {max(means) - min(means):.0f} bytes")
    print(f"shots in {tmp}")


if __name__ == "__main__":
    main()
