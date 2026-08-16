"""Round-4 shot set for room 5 (Living Room)."""
import json, os, subprocess, sys

TOOLS = r"C:\Users\Manuel\Desktop\Pro\3d HA\tools"
OUT = r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\lr5"
PY = sys.executable

REF = {"pos": [15.58, 13.70, 2.84],
       "target": [-123.6, -14.1, -138.4],
       "fov": 100, "size": [900, 1200]}

POSES = json.loads(subprocess.check_output(
    [PY, "-m", "roomkit.rooms", "5", "--poses-only"], cwd=TOOLS))
POSES["ref"] = REF
POSES["south"] = {"pos": [8.33, 13.60, -8.80], "target": [9.20, 11.30, 4.60],
                  "fov": 80, "size": [1100, 850]}
# tight crops for metering
POSES["fire"] = {"pos": [8.60, 12.80, -1.60], "target": [-9.6, 11.5, -19.4],
                 "fov": 42, "size": [900, 900]}
POSES["rug"] = {"pos": [8.325, 20.0, -3.88], "target": [8.325, 8.0, -3.88],
                "fov": 30, "size": [900, 900]}

tag = os.environ.get("TAG", "r4")
for name in sys.argv[1:]:
    pose = POSES[name]
    png = os.path.join(OUT, f"{tag}_{name}.png")
    subprocess.run([PY, "-m", "roomkit.shot", "--pose-json", json.dumps(pose),
                    "--level", "1", "--day", "--out", png], cwd=TOOLS, check=True)
    print(png)
