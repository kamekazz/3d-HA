"""Shoot room 13 poses.  Usage: python shots.py TAG pose [pose ...]"""
import json, os, subprocess, sys

TOOLS = r"C:\Users\Manuel\Desktop\Pro\3d HA\tools"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shots")
PY = sys.executable
os.makedirs(OUT, exist_ok=True)

POSES = json.loads(subprocess.check_output(
    [PY, "-m", "roomkit.rooms", "13", "--poses-only"], cwd=TOOLS))

# Photo 1 viewpoint.  Solving the photo's 7 identifiable points (bed corners,
# the two window jambs, the NW corner) for camera + yaw puts the photographer
# just OUTSIDE the room's south-east corner, i.e. standing back in the entry
# doorway on the east wall: local (13.0, eye 5.3, 9.9) -> world (11.1, 23.3,
# 16.4), yaw -34 deg (north, swung west), pitch -22.  Phone ultrawide -> 100
# deg vertical fov.  shot.py's flyTo only partly converges its target, so the
# target is pushed 200 ft out along the ray.
import math
_p = [10.05, 23.30, 16.35]   # local (11.95, 5.30, 9.85): just INSIDE the
#      east wall -- standing back in the hallway as the photo does puts the
#      hallway's own west wall between the camera and the room.
_yaw = math.radians(-34.0)         # 0 = due north (-z); + = toward east
_pitch = math.radians(-22.0)
POSES["ref"] = {
    "pos": _p,
    "target": [_p[0] + 200 * math.sin(_yaw) * math.cos(_pitch),
               _p[1] + 200 * math.sin(_pitch),
               _p[2] - 200 * math.cos(_yaw) * math.cos(_pitch)],
    "fov": 100, "size": [900, 1200],
}

if __name__ == "__main__":
    tag = sys.argv[1]
    for name in sys.argv[2:]:
        png = os.path.join(OUT, f"{tag}_{name}.png")
        subprocess.run([PY, "-m", "roomkit.shot", "--pose-json",
                        json.dumps(POSES[name]), "--level", "2", "--day",
                        "--out", png], cwd=TOOLS, check=True)
        print(png)
