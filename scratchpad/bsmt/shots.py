import json, os, subprocess, sys
sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
from roomkit.rooms import fetch_house, room_facts, poses_for
PY = r"C:\Users\Manuel\Desktop\Pro\3d HA\backend\.venv\Scripts\python.exe"
TOOLS = r"C:\Users\Manuel\Desktop\Pro\3d HA\tools"
OUT = r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\bsmt\shots"

def shots(room, names, tag, level=0, day=True):
    f = room_facts(fetch_house(), room)
    P = poses_for(f)
    for n in names:
        pose = P[n]
        out = os.path.join(OUT, f"{tag}_{n}.png")
        cmd = [PY, "-m", "roomkit.shot", "--pose-json", json.dumps(pose),
               "--level", str(level), "--out", out]
        if day: cmd.append("--day")
        subprocess.run(cmd, cwd=TOOLS, check=True)
        print("ok", out)

if __name__ == "__main__":
    room = int(sys.argv[1]); tag = sys.argv[2]; names = sys.argv[3].split(",")
    day = "--night" not in sys.argv
    shots(room, names, tag, day=day)
