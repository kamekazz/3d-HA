"""Take the round-2 shot set for room 5."""
import json, os, subprocess, sys

TOOLS = r"C:\Users\Manuel\Desktop\Pro\3d HA\tools"
OUT = r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\lr5"
PY = sys.executable

# Reproduces Living Room f / A: standing near the south-east corner on a phone
# ultrawide, looking north-west across the room at the fireplace corner.  The
# target is pushed 200 ft out along the ray because shot.py's flyTo only partly
# converges its target -- a near target gives a different framing run to run.
REF = {"pos": [15.58, 13.70, 2.84],
       "target": [-123.6, -14.1, -138.4],
       "fov": 100, "size": [900, 1200]}

POSES = json.loads(subprocess.check_output(
    [PY, "-m", "roomkit.rooms", "5", "--poses-only"], cwd=TOOLS))
POSES["ref"] = REF
# roomkit's generic doll pose stands 39 ft out and fills half the frame with the
# neighbouring rooms; this one is the same 50 deg / SE orbit pulled in to 27 ft.
POSES["doll5"] = {"pos": [18.29, 37.68, 10.34], "target": [8.325, 10.52, -3.88],
                  "fov": 42, "size": [1200, 900]}
POSES["south"] = {"pos": [8.33, 13.60, -8.80], "target": [9.20, 11.30, 4.60],
                  "fov": 80, "size": [1100, 850]}

for name in sys.argv[1:]:
    pose = POSES[name]
    png = os.path.join(OUT, f"r2_{name}.png")
    subprocess.run([PY, "-m", "roomkit.shot", "--pose-json", json.dumps(pose),
                    "--level", "1", "--day", "--out", png], cwd=TOOLS, check=True)
    print(png)
