"""Shoot a set of room-1 poses.  usage: shoot.py <outdir> <prefix> [poses...]"""
import json, subprocess, sys, os
PY = r"C:\Users\Manuel\Desktop\Pro\3d HA\backend\.venv\Scripts\python.exe"
TOOLS = r"C:\Users\Manuel\Desktop\Pro\3d HA\tools"
poses = json.loads(subprocess.run([PY, "-m", "roomkit.rooms", "1", "--poses-only"],
                                  cwd=TOOLS, capture_output=True, text=True).stdout)
EXTRA = {
 "photo4": {"pos": [12.1, 5.4, 16.4], "target": [3.6, 2.2, 31.0], "fov": 92, "size": [900, 1200]},
 "photo2": {"pos": [16.4, 5.3, 30.6], "target": [1.0, 3.0, 14.0], "fov": 78, "size": [900, 1200]},
 "photo3": {"pos": [6.0, 5.3, 31.5], "target": [8.0, 3.4, 12.0], "fov": 80, "size": [900, 1200]},
}
poses.update(EXTRA)
outdir, prefix = sys.argv[1], sys.argv[2]
os.makedirs(outdir, exist_ok=True)
for name in sys.argv[3:]:
    p = poses[name]
    cmd = [PY, "-m", "roomkit.shot", "--pose-json", json.dumps(p), "--level", "0",
           "--day", "--out", os.path.join(outdir, prefix + name + ".png")]
    if name not in ("doll_se","doll_sw","doll_ne","doll_nw","doll","plan"):
        cmd.append("--no-cutaway")
    r = subprocess.run(cmd, cwd=TOOLS, capture_output=True, text=True)
    print(name, r.returncode, (r.stdout or r.stderr).strip()[-160:])
