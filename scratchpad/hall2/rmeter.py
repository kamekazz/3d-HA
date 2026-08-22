"""Meter clean patches out of a room-17 render, with the boxes drawn back out.

Same statistics as photometer.py (mean, sd, mean|d1|, |d1|/sd at NATIVE
resolution) so render and photo numbers are directly comparable.  Every box is
echoed onto `<render>_boxes.png` -- look at it before trusting a number.

    python rmeter.py shots/r3a_v2_north.png north
    python rmeter.py shots/r3a_v2_south.png south
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
LUM = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)

# renders are 900x1200.  Boxes verified against the *_boxes.png overlays.
SETS = {
    # looking NORTH from the south end: west wall on the left, east/knee on the
    # right, master-bedroom door at the far end, runner down the middle.
    "north": {
        "floor near (left of runner)":    (196, 1130, 300, 1198),
        "floor near (right of runner)":   (546, 1130, 600, 1196),
        "floor mid  (right of runner)":   (506, 985, 538, 1060),
        "wall WEST  (low, S of sculpture)": (236, 620, 266, 790),
        "wall WEST  (upper)":             (246, 406, 320, 450),
        "wall NORTH (right of door)":     (700, 470, 740, 700),
        "ceiling    (mid)":               (430, 150, 620, 260),
    },
    # looking SOUTH from the north end: the WEST wall is on the RIGHT of frame.
    "south": {
        "floor near (right of runner)":   (566, 872, 612, 946),
        "floor near (left of runner)":    (344, 900, 372, 980),
        "wall WEST  (right of frame, upper)": (640, 180, 780, 288),
        "ceiling    (mid)":               (200, 120, 380, 230),
    },
}


def stats(lum):
    dh = np.abs(lum[:, 1:] - lum[:, :-1])
    dv = np.abs(lum[1:] - lum[:-1])
    d1 = 0.5 * (dh.mean() + dv.mean())
    sd = float(lum.std())
    return dict(n=lum.size, mean=float(lum.mean()), sd=sd, d1=float(d1),
                ratio=d1 / sd if sd > 1e-6 else 0.0)


def run(path, which):
    img = Image.open(path).convert("RGB")
    a = np.asarray(img).astype(np.float32)
    print(f"\n{os.path.basename(path)}   ({a.shape[1]}x{a.shape[0]})")
    print(f"  {'patch':<38}{'n':>8}{'mean':>8}{'sd':>7}{'|d1|':>7}{'|d1|/sd':>9}")
    for k, (x0, y0, x1, y1) in SETS[which].items():
        s = stats(a[y0:y1, x0:x1] @ LUM)
        print(f"  {k:<38}{s['n']:>8}{s['mean']:>8.1f}{s['sd']:>7.2f}"
              f"{s['d1']:>7.2f}{s['ratio']:>9.3f}")
    vis = img.copy()
    d = ImageDraw.Draw(vis)
    for b in SETS[which].values():
        d.rectangle(b, outline=(255, 0, 0), width=3)
    out = path.replace(".png", "_boxes.png")
    vis.save(out)
    return out


if __name__ == "__main__":
    for i in range(1, len(sys.argv), 2):
        run(os.path.join(HERE, sys.argv[i]), sys.argv[i + 1])
