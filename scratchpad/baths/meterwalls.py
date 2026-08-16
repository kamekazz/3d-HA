"""Honest per-wall metering of the FINISHED room.

    python meterwalls.py 26

Reuses the masks probe2.py already produced: for each wall it saved a render
with every skin at grey 250 and a render with only that wall at 120, so the
pixels that moved are exactly that wall's skin.  Those masks are geometry, not
colour, so they still select the same wall in the finished room -- as long as
the pose is identical, which it is.

Reports, per wall, at NATIVE render resolution (nothing upsampled):
  mean   -- Rec.709 luminance
  sd     -- standard deviation.  SCALE-BLIND on its own: a few big soft patches
            and real surface grain meter the same, which is how earlier rooms
            passed their numbers and read plastic.
  |d1|   -- mean |difference| between horizontally adjacent pixels inside the
            mask.  This is the fine-scale term sd cannot see.
  |d1|/sd- normalised texture; the ROOM-BRIEF's photo reference is 0.32-0.39
            for fabric, and a render that sits near 0.07 is plastic.
"""
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
LUM = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
POSE_WALLS = {"corner_se": ("n", "w"), "corner_nw": ("s", "e")}
FALLBACK = {"n": "look_n", "s": "look_s", "e": "look_e", "w": "look_w"}


def lum(p):
    return np.asarray(Image.open(p).convert("RGB")).astype(np.float32) @ LUM


def stats(img, mask):
    v = img[mask]
    if v.size < 50:
        return None
    d = np.abs(np.diff(img, axis=1))
    dm = mask[:, :-1] & mask[:, 1:]
    d1 = float(d[dm].mean()) if dm.sum() > 50 else float("nan")
    return dict(n=int(v.size), mean=float(v.mean()), sd=float(v.std()), d1=d1)


def main():
    room = int(sys.argv[1])
    shots = os.path.join(HERE, "shots")
    rows = []
    for pose, walls in POSE_WALLS.items():
        for w in walls:
            for p in (pose, FALLBACK[w]):
                a = os.path.join(shots, f"pr{room}_{p}_A.png")
                b = os.path.join(shots, f"pr{room}_{p}_{w}.png")
                fin = os.path.join(shots, f"fin{room}_{p}.png")
                if not (os.path.exists(a) and os.path.exists(b)
                        and os.path.exists(fin)):
                    continue
                mask = (lum(a) - lum(b)) > 10.0
                if mask.sum() < 200:
                    continue
                s = stats(lum(fin), mask)
                if s:
                    rows.append((w, p, s))
                break
    print(f"room {room} -- finished walls, native resolution")
    print("wall  pose         n(px)     mean     sd    |d1|   |d1|/sd")
    for (w, p, s) in rows:
        print(f"  {w}   {p:11s} {s['n']:8d}  {s['mean']:7.1f} {s['sd']:6.1f}"
              f" {s['d1']:6.2f}   {s['d1']/max(s['sd'],1e-6):5.3f}")
    if rows:
        ms = [s["mean"] for (_, _, s) in rows]
        print(f"  spread across {len(ms)} walls: {max(ms)-min(ms):.1f}"
              f"  (mean {sum(ms)/len(ms):.1f})")


if __name__ == "__main__":
    main()
