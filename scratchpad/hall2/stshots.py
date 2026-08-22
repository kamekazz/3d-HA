"""Extra poses for the STAIRCASE round: looking UP the flight from the 1F entry.

`shots.py` only carries poses matched to the four 2F photos; the sixth photo,
`staircase_looking_up.jpg`, is taken standing in the 1F hall.  That view is the
only one that shows the risers, the string board and the newel/baluster bases,
so it is the one the round-3 balustrade work has to be checked against.  Room
17's own shaft lining is what stands in for the first floor there.
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shots import POSES, PY, TOOLS, OUT, P            # noqa: E402

POSES.update({
    # 'staircase_looking_up' -- standing at the bottom, looking up the flight
    "v2_up": P(16.30, -8.15, 26.20, 16.05, -3.60, 18.60),
    "v2_up2": P(15.10, -7.60, 25.40, 16.30, -4.40, 17.00),
})


def shoot(name, level=2, tag=""):
    out = os.path.join(OUT, f"{tag}{name}.png")
    cmd = [PY, "-m", "roomkit.shot", "--pose-json", json.dumps(POSES[name]),
           "--level", str(level), "--day", "--out", out, "--no-cutaway"]
    r = subprocess.run(cmd, cwd=TOOLS, capture_output=True, text=True)
    print(f"{name:<10} {'ok' if r.returncode == 0 else 'FAIL'}  {out}")
    if r.returncode:
        print(r.stdout[-1200:], r.stderr[-1200:])


if __name__ == "__main__":
    tag = os.environ.get("TAG", "")
    for n in (sys.argv[1:] or ["v2_up"]):
        shoot(n, tag=tag)
