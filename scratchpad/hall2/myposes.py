"""Extra poses for the doors piece only -- v3.py's four are untouched.

p_guest looks NW across the alcove at the Guest-room door (opening 136), which
none of the round's four shared poses can see; p_bathclose is a close read of
the bath leaf for the panel/cove check.
"""
import json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.abspath(os.path.join(HERE, "..", "..", "tools"))
PY = os.path.abspath(os.path.join(HERE, "..", "..", "backend", ".venv", "Scripts", "python.exe"))
OUT = os.path.join(HERE, "shots"); os.makedirs(OUT, exist_ok=True)
B = 18.0
def P(x, y, z, tx, ty, tz, fov=70, size=(900, 1200)):
    return {"pos": [x, B + y, z], "target": [tx, B + ty, tz], "fov": fov, "size": list(size)}
POSES = {
    "p_guest":     P(11.40, 5.20, 21.30, 8.44, 3.70, 17.32),
    "p_bathclose": P(12.70, 5.20, 19.60, 12.77, 3.60, 23.44),
    "p_riosclose": P(9.60, 5.10, 19.90, 8.55, 3.50, 22.70),
}
if __name__ == "__main__":
    tag = os.environ.get("TAG", "")
    for n in (sys.argv[1:] or list(POSES)):
        out = os.path.join(OUT, f"{tag}{n}.png")
        cmd = [PY, "-m", "roomkit.shot", "--pose-json", json.dumps(POSES[n]),
               "--level", "2", "--day", "--out", out, "--no-cutaway"]
        r = subprocess.run(cmd, cwd=TOOLS, capture_output=True, text=True)
        print(f"{n:<12} {'ok' if r.returncode == 0 else 'FAIL'}  {out}")
        if r.returncode:
            print(r.stdout[-800:], r.stderr[-800:])
