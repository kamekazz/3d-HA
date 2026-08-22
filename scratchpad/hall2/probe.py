"""Solve room 17's four wall skins by PROBING, per ROOM-BRIEF option 2.

Renders the room with every skin at a base grey, then once per wall with only
THAT wall's skin dropped to near-black.  The pixels that moved are that wall
and nothing else -- no hand-drawn sample box can swallow a door casing, a
plant or the knee wall.  Two renders per wall give a log-linear response that
is then inverted onto the target value.

    python probe.py            # full sweep, prints the fit and the solved hexes
"""
import json
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PY = os.path.join(ROOT, "backend", ".venv", "Scripts", "python.exe")
OUT = os.path.join(HERE, "probe")
os.makedirs(OUT, exist_ok=True)

import build as B                                              # noqa: E402

LUM = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
BASE = "#c8c8c8"
DARK = "#3c3c3c"
# Every probe pose is shot with --no-cutaway, standing inside the room, so the
# walls are all solid -- the same conditions the judged v2_* renders use.
BY = 18.0
POSES = {
    "v2_north": {"pos": [12.45, BY + 5.35, 21.60], "target": [13.30, BY + 4.30, 6.90],
                 "fov": 74, "size": [900, 1200]},
    "v2_south": {"pos": [12.45, BY + 5.35, 8.10], "target": [12.60, BY + 4.10, 23.00],
                 "fov": 74, "size": [900, 1200]},
    # the east wall only exists over the north landing, and neither v2 pose sees it
    "pe": {"pos": [12.00, BY + 5.00, 12.10], "target": [18.50, BY + 4.60, 9.60],
           "fov": 70, "size": [900, 900]},
    # the south wall is nearly all doorway; this looks straight at what is left
    "ps": {"pos": [12.50, BY + 5.00, 16.60], "target": [12.30, BY + 4.40, 23.20],
           "fov": 70, "size": [900, 900]},
}
POSE = {"n": "v2_north", "e": "pe", "w": "v2_south", "s": "ps"}


def place_skins(colors):
    B.save_and_place("Hall2F Wall Wash Skins", B.piece_skins(colors))


def shoot(name, tag):
    dst = os.path.join(OUT, f"{tag}{name}.png")
    r = subprocess.run([PY, "-m", "roomkit.shot", "--pose-json",
                        json.dumps(POSES[name]), "--level", "2", "--day",
                        "--no-cutaway", "--out", dst],
                       cwd=os.path.join(ROOT, "tools"),
                       capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(r.stdout[-800:] + r.stderr[-800:])
    return np.asarray(Image.open(dst).convert("RGB")).astype(np.float32)


def lum(a):
    return a @ LUM


def main():
    colors = {k: BASE for k in "nswe"}
    place_skins(colors)
    base = {p: shoot(p, "pb_base_") for p in ("v2_north", "v2_south", "pe", "ps")}

    fits = {}
    for wall in "nswe":
        c = dict(colors)
        c[wall] = DARK
        place_skins(c)
        pose = POSE[wall]
        img = shoot(pose, f"pb_{wall}_")
        d = np.abs(lum(base[pose]) - lum(img))
        mask = d > 8.0
        n = int(mask.sum())
        if n < 400:
            print(f"  {wall}: only {n} px moved -- wall not solvable in this pose")
            fits[wall] = None
            continue
        a0 = float(lum(base[pose])[mask].mean())
        a1 = float(lum(img)[mask].mean())
        sd0 = float(lum(base[pose])[mask].std())
        fits[wall] = (a0, a1, n, sd0)
        print(f"  {wall}: n={n:7d}  base({BASE})={a0:6.1f} sd {sd0:5.2f}"
              f"   dark({DARK})={a1:6.1f}")
        Image.fromarray((mask * 255).astype(np.uint8)).save(
            os.path.join(OUT, f"mask_{wall}.png"))

    json.dump(fits, open(os.path.join(OUT, "fits.json"), "w"), indent=1)

    # log-linear response: value = k * albedo**g, solved from the two probes
    print("\n  solved skins:")
    solved = {}
    for wall, f in fits.items():
        if not f:
            solved[wall] = BASE
            continue
        a0, a1 = f[0], f[1]
        p0, p1 = int(BASE[1:3], 16), int(DARK[1:3], 16)
        g = math.log(a0 / a1) / math.log(p0 / p1)
        k = a0 / (p0 ** g)
        t = TARGET[wall]
        alb = max(6.0, min(255.0, (t / k) ** (1.0 / g)))
        solved[wall] = "#%02x%02x%02x" % ((int(round(alb)),) * 3)
        print(f"    {wall}  g={g:5.3f}  target {t:5.1f}  ->  {solved[wall]}")
    json.dump(solved, open(os.path.join(OUT, "solved.json"), "w"), indent=1)


# what each wall should meter.  From 'Second-floor hallway.jpg': the west wall
# runs 171-179, the far/east wall 141, the ceiling 141.5.  A real room's walls
# sit within ~30, and the photo itself carries a ~35 spread, so the targets
# keep that spread rather than flattening it.
TARGET = {"n": 165.0, "s": 165.0, "e": 158.0, "w": 175.0}

if __name__ == "__main__":
    main()
