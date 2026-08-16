import json, os, subprocess, sys
TOOLS = r"C:\Users\Manuel\Desktop\Pro\3d HA\tools"
PY = sys.executable
room, level, pose, out = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
extra = sys.argv[5:]
poses = json.loads(subprocess.check_output([PY, "-m", "roomkit.rooms", room, "--poses-only"], cwd=TOOLS))
subprocess.run([PY, "-m", "roomkit.shot", "--pose-json", json.dumps(poses[pose]),
                "--level", level, "--day", "--out", out] + extra, cwd=TOOLS, check=True)
