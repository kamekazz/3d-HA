"""Round-7 probe: rebuild the three cabinet pieces at a given BTN roughness
and shoot two close deck frames.

    $PY scratchpad/arc4/r7eng/probe.py <tag> [roughness]
"""
import json
import os
import subprocess
import sys

_ROOT = r"C:\Users\Manuel\Desktop\Pro\3d HA"
PY = os.path.join(_ROOT, "backend", ".venv", "Scripts", "python.exe")
TOOLS = os.path.join(_ROOT, "tools")
OUT = os.path.join(_ROOT, "scratchpad", "arc4", "r7eng", "shots")
for _p in (TOOLS, os.path.join(_ROOT, "scratchpad", "bsmt"),
           os.path.join(_ROOT, "scratchpad", "arc4"),
           os.path.join(_ROOT, "scratchpad", "arc4", "art")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# world feet.  local (x, z) -> world (x - 2.1, z - 11.9); slab y = 0.
POSES = {
    # Golden Tee, north run, deck top y 2.60, faces +z
    "gt": {"pos": [11.45, 4.05, -8.55], "target": [11.45, 2.58, -10.45],
           "fov": 34, "size": [900, 700]},
    # NBA Jam, east run, deck top y 2.54, faces -x
    "nba": {"pos": [14.55, 4.05, -0.02], "target": [16.75, 2.52, -0.02],
            "fov": 34, "size": [900, 700]},
    # Marvel Super Heroes, east run, deck top 2.54
    "msh": {"pos": [14.55, 4.05, -6.80], "target": [16.75, 2.52, -6.80],
            "fov": 34, "size": [900, 700]},
}


def shoot(tag, names=("gt", "nba", "msh")):
    os.makedirs(OUT, exist_ok=True)
    for n in names:
        out = os.path.join(OUT, "%s_%s.png" % (tag, n))
        cmd = [PY, "-m", "roomkit.shot", "--pose-json", json.dumps(POSES[n]),
               "--level", "0", "--day", "--no-cutaway", "--out", out]
        r = subprocess.run(cmd, cwd=TOOLS, capture_output=True, text=True)
        print(" ", n, r.returncode, (r.stdout or r.stderr).strip()[-120:])


if __name__ == "__main__":
    tag = sys.argv[1]
    import ar2
    if len(sys.argv) > 2:
        ar2.BTN.roughness = float(sys.argv[2])
        print("BTN roughness", ar2.BTN.roughness)
    for k in ("east", "south", "ncab"):
        ar2.BUILDERS[k]()
    shoot(tag)
