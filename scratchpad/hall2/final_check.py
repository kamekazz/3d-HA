import glob
import json
import os
import subprocess
import urllib.request

TOOLS = r"C:\Users\Manuel\Desktop\Pro\3d HA\tools"
PY = r"C:\Users\Manuel\Desktop\Pro\3d HA\backend\.venv\Scripts\python.exe"
OUT = r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\hall2\shots"
MODELS = r"C:\Users\Manuel\Desktop\Pro\3d HA\backend\uploads\models"

poses = json.loads(subprocess.run(
    [PY, "-m", "roomkit.rooms", "17", "--poses-only"],
    cwd=TOOLS, capture_output=True, text=True).stdout)
res = subprocess.run(
    [PY, "-m", "roomkit.shot", "--pose-json", json.dumps(poses["doll_se"]),
     "--level", "2", "--day", "--out", os.path.join(OUT, "g_doll_se.png")],
    cwd=TOOLS, capture_output=True, text=True)
print("doll_se shot rc =", res.returncode)

h = json.load(urllib.request.urlopen("http://127.0.0.1:5000/api/house"))
for f in h["floors"]:
    for room in f["rooms"]:
        if room["id"] != 17:
            continue
        ops = sorted(room["openings"], key=lambda o: (o["edge_index"], o["offset"]))
        print("room 17 has %d openings: %s" % (len(ops), sorted(o["id"] for o in ops)))
        for o in ops:
            print("   %4d %-8s e%d  off %5.2f  w %4.2f  h %4.2f"
                  % (o["id"], o["type"], o["edge_index"], o["offset"],
                     o["width"], o["height"]))
        tot = 0.0
        for ob in room["objects"]:
            kb = os.path.getsize(os.path.join(MODELS, "model_%d.glb" % ob["model_id"])) / 1024
            tot += kb
            print("   %-28s %8.1f KB" % (ob["name"], kb))
        print("   room 17 total %.1f KB" % tot)

allglb = glob.glob(os.path.join(MODELS, "*.glb"))
print("house payload %.1f MB across %d models"
      % (sum(os.path.getsize(p) for p in allglb) / 1048576, len(allglb)))
