"""Solve each wall's albedo skin from real renders, per room.

    python probe2.py 26 178

Why not probe.py's hand-picked boxes: these bathrooms are small and crowded,
so every "clean wall" box I could draw by eye caught a towel bar, a mirror rim
or the shower frame, and the ROOM-BRIEF's own honest-metering section says a
sample that swallows objects is exactly how the last two reports went wrong.

Instead the sample is derived, not drawn.  For each wall it renders the room
twice with ONLY that wall's skin changed (grey 250 -> grey 120) and keeps the
pixels that moved.  There is no bounce light in this scene, so the pixels that
move ARE that wall's skin and nothing else -- fixtures, trim, floor and the
other three walls all sit still.  That gives a per-wall two-point response
curve measured on the real render, which fit_skin() inverts for the target.

Sample sizes are printed; they are the mask areas, in pixels, at native
render resolution (no upsampling).
"""
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = r"C:\Users\Manuel\Desktop\Pro\3d HA\tools"
PY = sys.executable
sys.path.insert(0, HERE)
from bkit import fit_skin, grey, save_here                          # noqa: E402

# pose -> the walls it can see.  The corner poses see two walls each and give
# the biggest, cleanest samples; the look_* poses are the fallback for a wall
# the corner shot cannot reach (in these rooms the shower alcove hides most of
# two walls, so their skin is only a sliver).
POSE_WALLS = {"corner_se": ("n", "w"), "corner_nw": ("s", "e")}
FALLBACK = {"n": "look_n", "s": "look_s", "e": "look_e", "w": "look_w"}
LUM = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)


def shot(room, level, pose, out):
    poses = json.loads(subprocess.check_output(
        [PY, "-m", "roomkit.rooms", str(room), "--poses-only"], cwd=TOOLS))
    subprocess.run([PY, "-m", "roomkit.shot", "--pose-json",
                    json.dumps(poses[pose]), "--level", str(level),
                    "--day", "--out", out], cwd=TOOLS, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def lum(path):
    return np.asarray(Image.open(path).convert("RGB")).astype(np.float32) @ LUM


def main():
    room = int(sys.argv[1])
    target = float(sys.argv[2]) if len(sys.argv) > 2 else 180.0
    mod = {16: "b16", 26: "b26", 23: "b23"}[room]
    level = 1 if room == 23 else 2
    name = {16: "Master Bath Wall Wash", 26: "Bath2F Wall Wash",
            23: "Bath1F Wall Wash"}[room]
    m = __import__(mod)

    A, B = 250, 120
    shots = os.path.join(HERE, "shots")
    os.makedirs(shots, exist_ok=True)
    solved, report = {}, []
    for pose, walls in POSE_WALLS.items():
        save_here(name, m.build_skins({w: grey(A) for w in "nesw"}), room)
        base = os.path.join(shots, f"pr{room}_{pose}_A.png")
        shot(room, level, pose, base)
        la = lum(base)
        for w in walls:
            cols = {k: grey(A) for k in "nesw"}
            cols[w] = grey(B)
            save_here(name, m.build_skins(cols), room)
            p = os.path.join(shots, f"pr{room}_{pose}_{w}.png")
            shot(room, level, pose, p)
            lb = lum(p)
            mask = (la - lb) > 10.0
            n = int(mask.sum())
            if n < 400:
                # the corner shot cannot see this wall: re-probe head-on
                fp = FALLBACK[w]
                b2 = os.path.join(shots, f"pr{room}_{fp}_A.png")
                save_here(name, m.build_skins({k: grey(A) for k in "nesw"}),
                          room)
                shot(room, level, fp, b2)
                la2 = lum(b2)
                save_here(name, m.build_skins(cols), room)
                p2 = os.path.join(shots, f"pr{room}_{fp}_{w}.png")
                shot(room, level, fp, p2)
                lb2 = lum(p2)
                mask = (la2 - lb2) > 10.0
                n = int(mask.sum())
                if n < 200:
                    print(f"  !! wall {w}: {n} px -- skin all but invisible")
                    solved[w] = grey(A)
                    continue
                la_, lb_ = la2, lb2
            else:
                la_, lb_ = la, lb
            ma, mb = float(la_[mask].mean()), float(lb_[mask].mean())
            v = fit_skin(A, ma, B, mb, target)
            solved[w] = grey(v)
            report.append((w, ma, mb, n, v))
    print(f"\nroom {room}: target {target:.0f}")
    print("wall   render@250  render@120   n(px)   -> skin albedo")
    for (w, ma, mb, n, v) in report:
        print(f"  {w}     {ma:8.1f}   {mb:8.1f}  {n:8d}   {grey(v)} ({v})")
    with open(os.path.join(HERE, f"skins{room}.json"), "w") as f:
        json.dump(solved, f)
    print(json.dumps(solved))


if __name__ == "__main__":
    main()
