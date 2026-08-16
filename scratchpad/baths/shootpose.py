"""Shoot a custom pose given in ROOM-LOCAL feet, matched to the photo's stance.

    python shootpose.py <room> <level> px py pz tx ty tz <fov> <out>

The stock corner_* poses stand in a corner of the room; the reference photos are
taken standing IN the doorway.  poses.json is the master bedroom's and must not
be edited, so the pose is passed through --pose-json instead.
"""
import json, subprocess, sys
TOOLS = r"C:\Users\Manuel\Desktop\Pro\3d HA\tools"
PY = sys.executable
room, level = sys.argv[1], sys.argv[2]
v = [float(x) for x in sys.argv[3:9]]
import os
fov, out = float(sys.argv[9]), os.path.abspath(sys.argv[10])
facts = json.loads(subprocess.check_output(
    [PY, "-m", "roomkit.rooms", room], cwd=TOOLS))["facts"]
ox, oy, oz = facts["origin_world"]
pose = {"pos": [ox + v[0], oy + v[1], oz + v[2]],
        "target": [ox + v[3], oy + v[4], oz + v[5]],
        "fov": fov, "size": [900, 1200]}
subprocess.run([PY, "-m", "roomkit.shot", "--pose-json", json.dumps(pose),
                "--level", level, "--day", "--out", out], cwd=TOOLS, check=True)
