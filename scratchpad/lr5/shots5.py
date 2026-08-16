"""Round-5 shot set for room 5 (Living Room)."""
import json, os, subprocess, sys

TOOLS = r"C:\Users\Manuel\Desktop\Pro\3d HA\tools"
OUT = r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\lr5"
PY = sys.executable

REF = {"pos": [15.58, 13.70, 2.84], "target": [-123.6, -14.1, -138.4],
       "fov": 100, "size": [900, 1200]}
POSES = json.loads(subprocess.check_output(
    [PY, "-m", "roomkit.rooms", "5", "--poses-only"], cwd=TOOLS))
POSES["ref"] = REF
# same pose at the PHOTO's own pixel count, so |d1| is compared like for like
POSES["refhi"] = dict(REF, size=[1200, 1600])
POSES["fire"] = {"pos": [8.60, 12.80, -1.60], "target": [-9.6, 11.5, -19.4],
                 "fov": 42, "size": [900, 900]}
POSES["rug"] = {"pos": [8.325, 20.0, -3.88], "target": [8.325, 8.0, -3.88],
                "fov": 30, "size": [900, 900]}
# dollhouse: same SE azimuth as roomkit's doll_se, pulled in on room 5 and
# raised, because at 55 deg the room's own 9 ft south wall hid the sectional.
POSES["doll5"] = {"pos": [14.72, 40.30, 7.30], "target": [8.325, 10.0, -4.60],
                  "fov": 40, "size": [1200, 900]}

tag = os.environ.get("TAG", "r5")
for name in sys.argv[1:]:
    pose = POSES[name]
    png = os.path.join(OUT, f"{tag}_{name}.png")
    subprocess.run([PY, "-m", "roomkit.shot", "--pose-json", json.dumps(pose),
                    "--level", "1", "--day", "--out", png], cwd=TOOLS, check=True)
    print(png)
