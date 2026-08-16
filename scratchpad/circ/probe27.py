"""Two-point per-surface probe for room 27, with CLEAN patches only.

The room's north wall is almost entirely behind the wire racks, so it is
metered above them (local y 7.2); the south wall is entirely behind the black
accent panel, so the 's' probe meters the PANEL, which is what is actually
visible there.  Every pose is checked against the _boxes overlay.
"""
import json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from probe import stats
TOOLS = r"C:\Users\Manuel\Desktop\Pro\3d HA\tools"
PY = sys.executable
# world feet; room 27 origin (18.60, 18.0, 12.40)
P = {
 "n":     {"pos": [25.4, 25.2, 14.6], "target": [25.4, 25.2, 12.4]},
 "s":     {"pos": [25.4, 21.0, 18.6], "target": [25.4, 21.0, 20.8]},
 "e":     {"pos": [29.4, 20.6, 16.6], "target": [32.2, 20.6, 16.6]},
 "w":     {"pos": [21.4, 22.6, 18.6], "target": [18.6, 22.6, 18.6]},
 "ceil":  {"pos": [25.4, 22.0, 13.6], "target": [25.4, 26.0, 13.9]},
 "floor": {"pos": [20.8, 22.0, 17.6], "target": [20.8, 18.0, 15.2]},
}
tag = sys.argv[1]
only = sys.argv[2:] or list(P)
os.makedirs("shots", exist_ok=True)
for k in only:
    pose = dict(P[k]); pose["fov"] = 24 if k not in ("floor","ceil") else 30
    pose["size"] = [800, 620]
    png = os.path.abspath(os.path.join("shots", "p27_%s_%s.png" % (tag, k)))
    subprocess.run([PY, "-m", "roomkit.shot", "--pose-json", json.dumps(pose),
                    "--level", "2", "--day", "--out", png], cwd=TOOLS,
                   check=True, stdout=subprocess.DEVNULL)
    mean, sd, n, rgb = stats(png)
    print("  %-6s mean=%6.1f sd=%5.1f n=%d rgb=%s" % (k, mean, sd, n, rgb))
