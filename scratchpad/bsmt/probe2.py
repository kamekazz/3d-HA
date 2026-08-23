"""Solve room 2's four per-wall skin albedos by probing the real renderer.

Render the room with every skin at grey A, then once per wall with THAT wall's
skin at grey B and the others still at A.  With one sun and no bounce light the
only pixels that move are that wall's own skin, so the diff IS the wall mask --
no hand-drawn sample box can swallow a cabinet or a door casing.

Two points (A, B) give a log-linear fit  render = k * albedo**g  per wall, which
is then inverted for the target render value.

  python probe2.py measure     -> writes probe2.json
  python probe2.py solve <T>   -> prints the four hex albedos for target T
"""
import json
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = r"C:\Users\Manuel\Desktop\Pro\3d HA\tools"
PY = r"C:\Users\Manuel\Desktop\Pro\3d HA\backend\.venv\Scripts\python.exe"
SHOTS = os.path.join(HERE, "probe")
A_HEX, B_HEX = "#fafafa", "#6e6e6e"

# room-centre poses, one per wall, in WORLD coords (room origin -2.1, 0, -11.9)
POSES = {
    "n": {"pos": [8.25, 4.6, 1.0], "target": [8.25, 3.6, -11.9]},
    "s": {"pos": [8.25, 4.6, -2.0], "target": [8.25, 3.6, 11.4]},
    "e": {"pos": [5.0, 4.6, -0.25], "target": [18.6, 3.6, -0.25]},
    "w": {"pos": [11.0, 4.6, -0.25], "target": [-2.1, 3.6, -0.25]},
}


def build(skin):
    src = open(os.path.join(HERE, "ar2.py"), encoding="utf-8").read()
    line = 'SKIN = ' + json.dumps(skin)
    out = []
    for ln in src.splitlines():
        out.append(line if ln.startswith("SKIN = ") else ln)
    open(os.path.join(HERE, "ar2.py"), "w", encoding="utf-8").write(
        "\n".join(out) + "\n")
    subprocess.run([PY, "ar2.py", "skins"], cwd=HERE, check=True,
                   stdout=subprocess.DEVNULL)


def shoot(tag):
    os.makedirs(SHOTS, exist_ok=True)
    for w, p in POSES.items():
        pose = dict(p, fov=70, size=[1100, 850])
        for attempt in range(4):
            r = subprocess.run(
                [PY, "-m", "roomkit.shot", "--pose-json", json.dumps(pose),
                 "--level", "0", "--day", "--out",
                 os.path.join(SHOTS, f"{tag}_{w}.png")],
                cwd=TOOLS, stdout=subprocess.DEVNULL)
            if r.returncode == 0:
                break
        else:
            raise RuntimeError("shot failed 4x for " + w)


def lum(path):
    a = np.asarray(Image.open(path).convert("RGB")).astype(float)
    return 0.2126 * a[:, :, 0] + 0.7152 * a[:, :, 1] + 0.0722 * a[:, :, 2]


def measure():
    build({w: A_HEX for w in "nesw"})
    shoot("A")
    res = {}
    for w in "nesw":
        build({k: (B_HEX if k == w else A_HEX) for k in "nesw"})
        shoot("B" + w)
        la = lum(os.path.join(SHOTS, f"A_{w}.png"))
        lb = lum(os.path.join(SHOTS, f"B{w}_{w}.png"))
        mask = np.abs(la - lb) > 6.0
        n = int(mask.sum())
        res[w] = dict(n=n,
                      a=float(la[mask].mean()) if n else 0.0,
                      b=float(lb[mask].mean()) if n else 0.0,
                      a_sd=float(la[mask].std()) if n else 0.0)
        print(f"  {w}: n={n:7d}  at{A_HEX}={res[w]['a']:6.1f} "
              f"(sd {res[w]['a_sd']:.2f})  at{B_HEX}={res[w]['b']:6.1f}")
    json.dump(res, open(os.path.join(HERE, "probe2.json"), "w"), indent=1)


def hexlum(h):
    h = h.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def solve(target):
    res = json.load(open(os.path.join(HERE, "probe2.json")))
    la, lb = hexlum(A_HEX), hexlum(B_HEX)
    out = {}
    for w in "nesw":
        r = res[w]
        if r["n"] < 400 or abs(r["a"] - r["b"]) < 2:
            print(f"  {w}: UNSOLVABLE (n={r['n']}), left at {A_HEX}")
            out[w] = A_HEX
            continue
        g = math.log(r["a"] / r["b"]) / math.log(la / lb)
        k = r["a"] / la ** g
        need = (target / k) ** (1.0 / g)
        need = max(6.0, min(255.0, need))
        v = int(round(need))
        out[w] = "#%02x%02x%02x" % (v, v, v)
        print(f"  {w}: gamma={g:.3f} k={k:.3f}  albedo {need:5.1f} -> {out[w]}"
              f"   (reach at 255 = {k * 255 ** g:.0f})")
    print(json.dumps(out))
    return out


if __name__ == "__main__":
    if sys.argv[1] == "measure":
        measure()
    else:
        solve(float(sys.argv[2]))
