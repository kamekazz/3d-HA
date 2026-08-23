"""Extra inspection poses for the baseboard piece only.  v3.py's poses are
shared by every agent this round and must not be edited, so the two views this
piece needs -- the alcove dead end (all three of its runs at once) and the free
end at V0 where the skirting dies at the stairwell -- live here."""
import json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.abspath(os.path.join(HERE, "..", "..", "tools"))
PY = os.path.abspath(os.path.join(HERE, "..", "..", "backend", ".venv", "Scripts", "python.exe"))
OUT = os.path.join(HERE, "shots")
BASE = 18.0

def P(x, y, z, tx, ty, tz, fov=70, size=(1000, 750)):
    return {"pos": [x, BASE + y, z], "target": [tx, BASE + ty, tz],
            "fov": fov, "size": list(size)}

POSES = {
    # low in the alcove looking WSW: edges 4, 5 and 6 in one frame
    "b_alcove": P(10.90, 2.30, 18.60, 7.05, 0.30, 21.20, fov=76),
    # the free end at V0 (11.92, 6.81 local) where the run dies at the stairwell
    "b_end":    P(15.30, 2.60, 11.40, 18.20, 0.35, 13.00, fov=66),
    # close on the outside-corner mitre at the near pier V7
    "b_pier":   P(12.30, 1.90, 15.20, 10.55, 0.30, 17.50, fov=68),
}

def shoot(name, tag=""):
    out = os.path.join(OUT, f"{tag}{name}.png")
    cmd = [PY, "-m", "roomkit.shot", "--pose-json", json.dumps(POSES[name]),
           "--level", "2", "--day", "--out", out, "--no-cutaway"]
    r = subprocess.run(cmd, cwd=TOOLS, capture_output=True, text=True)
    print(f"{name:<10} {'ok' if r.returncode == 0 else 'FAIL'}  {out}")
    if r.returncode:
        print(r.stdout[-800:], r.stderr[-800:])

if __name__ == "__main__":
    tag = os.environ.get("TAG", "")
    for n in (sys.argv[1:] or list(POSES)):
        shoot(n, tag)
