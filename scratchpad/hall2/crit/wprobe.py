"""Solve room 17's eight wall skins by PROBING (ROOM-BRIEF option 2).

Render the room with every skin at a base grey, then once per wall with only
THAT wall's skin dropped to near-black.  The scene has no bounce light, so the
pixels that moved ARE that wall -- no hand-drawn sample box can swallow a door
casing, a plant or the knee wall.  Two renders per wall give a log-linear
response  value = k * albedo**g  which is then inverted onto the target.

    python wprobe.py            # full sweep -> crit/skins.json
    python wprobe.py meter      # just re-meter the current skins, no refit
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
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
PY = os.path.join(ROOT, "backend", ".venv", "Scripts", "python.exe")
OUT = os.path.join(HERE, "probe")
os.makedirs(OUT, exist_ok=True)

import walls as W                                             # noqa: E402

LUM = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
GREY = "#c8c8c8"
DARK = "#3c3c3c"
BY = 18.0


def P(x, y, z, tx, ty, tz, fov=74, size=(900, 1200)):
    return {"pos": [6.70 + x, BY + y, 6.55 + z],
            "target": [6.70 + tx, BY + ty, 6.55 + tz],
            "fov": fov, "size": list(size)}


# The three judged poses, plus two extra ones aimed into the west alcove (the
# judged set never looks at edges 3/5/6 straight on).  ROUND-V3 forbids editing
# v3.py's poses; adding your own in your own file is explicitly allowed.
POSES = {
    "p_stairs": P(5.40, 5.30, 15.35, 6.25, 4.05, 0.65),
    "p_runner": P(5.90, 5.30, 1.85, 5.85, 3.95, 16.55),
    "p_doors2": P(6.40, 5.25, 11.75, 0.70, 3.60, 15.05),
    "pa":       P(6.30, 5.20, 13.60, 0.60, 4.00, 11.20, fov=72, size=(900, 900)),
    "pb":       P(6.35, 5.20, 12.60, 1.70, 4.00, 16.10, fov=72, size=(900, 900)),
}
# which pose each wall is solved in
POSE = {2: "p_runner", 3: "pb", 4: "pb", 5: "pa",
        6: "pa", 7: "p_runner", 8: "p_stairs", 9: "p_stairs"}

# What each wall should meter, from the photographs (crit/cprof.py).  The six
# shots are separately auto-exposed, so these are the per-wall values read in
# the shot that looks straight at that wall:
#   runner  west wall 160 (near) .. 185 (far), mean of the clean field 165
#   stairs  west wall 182, east/knee side 149
#   doors2  alcove right wall 172, the return between the doors 211-223
#   down    shaft walls 170
TARGET = {2: 174.0, 3: 186.0, 4: 178.0, 5: 178.0,
          6: 172.0, 7: 176.0, 8: 168.0, 9: 162.0}


def place(colors):
    W.save_and_place(W.piece(colors))


def shoot(pose, tag):
    dst = os.path.join(OUT, f"{tag}{pose}.png")
    r = subprocess.run([PY, "-m", "roomkit.shot", "--pose-json",
                        json.dumps(POSES[pose]), "--level", "2", "--day",
                        "--no-cutaway", "--out", dst],
                       cwd=os.path.join(ROOT, "tools"),
                       capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(r.stdout[-900:] + r.stderr[-900:])
    return np.asarray(Image.open(dst).convert("RGB")).astype(np.float32)


def lum(a):
    return a @ LUM


def sweep():
    base_c = {e: GREY for e in W.FACE}
    place(base_c)
    need = sorted(set(POSE.values()))
    base = {p: shoot(p, "wb_base_") for p in need}

    fits = {}
    for wall in sorted(W.FACE):
        c = dict(base_c)
        c[wall] = DARK
        place(c)
        pose = POSE[wall]
        img = shoot(pose, f"wb_{wall}_")
        d = np.abs(lum(base[pose]) - lum(img))
        mask = d > 8.0
        n = int(mask.sum())
        if n < 400:
            print(f"  edge {wall}: only {n} px moved -- unsolvable in {pose}")
            fits[wall] = None
            continue
        a0 = float(lum(base[pose])[mask].mean())
        a1 = float(lum(img)[mask].mean())
        sd0 = float(lum(base[pose])[mask].std())
        fits[wall] = (a0, a1, n, sd0)
        print(f"  edge {wall} [{pose}]: n={n:7d}  {GREY}={a0:6.1f} sd {sd0:5.2f}"
              f"   {DARK}={a1:6.1f}")
        Image.fromarray((mask * 255).astype(np.uint8)).save(
            os.path.join(OUT, f"mask_{wall}.png"))

    json.dump({str(k): v for k, v in fits.items()},
              open(os.path.join(OUT, "fits.json"), "w"), indent=1)

    print("\n  solved skins:")
    solved = {}
    for wall in sorted(W.FACE):
        f = fits[wall]
        if not f:
            solved[wall] = GREY
            continue
        a0, a1 = f[0], f[1]
        p0, p1 = int(GREY[1:3], 16), int(DARK[1:3], 16)
        g = math.log(a0 / a1) / math.log(p0 / p1)
        k = a0 / (p0 ** g)
        t = TARGET[wall]
        alb = max(6.0, min(255.0, (t / k) ** (1.0 / g)))
        solved[wall] = "#%02x%02x%02x" % ((int(round(alb)),) * 3)
        print(f"    edge {wall}  g={g:5.3f}  k={k:7.4f}  target {t:5.1f}"
              f"  ->  {solved[wall]}")
    json.dump({str(k): v for k, v in solved.items()},
              open(os.path.join(HERE, "skins.json"), "w"), indent=1)
    return solved


def meter(colors=None):
    """Re-render with the given (or current) skins and report each wall's
    achieved mean, using the same moved-pixel masks the fit used."""
    colors = colors or W.SKINS
    place(colors)
    need = sorted(set(POSE.values()))
    cur = {p: shoot(p, "wm_cur_") for p in need}
    vals = {}
    for wall in sorted(W.FACE):
        c = dict(colors)
        c[wall] = DARK
        place(c)
        pose = POSE[wall]
        img = shoot(pose, f"wm_{wall}_")
        mask = np.abs(lum(cur[pose]) - lum(img)) > 8.0
        if mask.sum() < 400:
            print(f"  edge {wall}: unsolvable")
            continue
        g = lum(cur[pose])[mask]
        vals[wall] = (g.mean(), g.std(), int(mask.sum()))
        print(f"  edge {wall} [{pose}]: mean={g.mean():6.1f} sd={g.std():5.2f}"
              f"  target {TARGET[wall]:5.1f}  n={int(mask.sum())}")
    vv = [v[0] for v in vals.values()]
    print(f"\n  wall spread = {max(vv) - min(vv):.1f}   "
          f"(min {min(vv):.1f} / max {max(vv):.1f} / mean {sum(vv)/len(vv):.1f})")
    place(colors)
    return vals


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "meter":
        meter()
    else:
        s = sweep()
        print("\n  re-metering with the solved skins ...")
        meter(s)
