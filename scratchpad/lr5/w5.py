"""Round-5 wall meter: shoot all four look_* poses and report EVERY wall with
both statistics (sd and mean |d1|), from the same clean boxes b5_shell probed
with.  Never re-ships a skin -- it only looks."""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from m5 import meter                                    # noqa: E402

TOOLS = r"C:\Users\Manuel\Desktop\Pro\3d HA\tools"
OUT = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable

BOX = {"look_n": (690, 137, 1080, 200),
       "look_w": (390, 195, 700, 330),
       "look_e": (700, 200, 1000, 480),
       "look_s": (340, 150, 430, 500)}

POSES = json.loads(subprocess.check_output(
    [PY, "-m", "roomkit.rooms", "5", "--poses-only"], cwd=TOOLS))

tag = sys.argv[1] if len(sys.argv) > 1 else "w"
vals = {}
for name, b in BOX.items():
    png = os.path.join(OUT, "%s_%s.png" % (tag, name))
    subprocess.run([PY, "-m", "roomkit.shot", "--pose-json",
                    json.dumps(POSES[name]), "--level", "1", "--day",
                    "--out", png], cwd=TOOLS, check=True,
                   stdout=subprocess.DEVNULL)
    rows = meter(png, [(b[0], b[1], b[2], b[3], name)])
    vals[name[-1]] = rows[0][2]
print("  N=%.1f W=%.1f E=%.1f S=%.1f  spread=%.1f  avg=%.1f"
      % (vals["n"], vals["w"], vals["e"], vals["s"],
         max(vals.values()) - min(vals.values()),
         sum(vals.values()) / 4.0))
