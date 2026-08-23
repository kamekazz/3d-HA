"""Three-point per-wall albedo solve.

The two-point log-linear fit that closed the Office/Garage/Laundry is not quite
right here: `roughness 0.95, metalness 0` still carries an F0=0.04 environment
specular that does NOT scale with albedo, so the true response is
`f(k*albedo + s)` and a pure power law through the two endpoints reads mid
albedos low -- the first pass asked for 167 on the alcove north wall and got 185.

So: keep the two probe renders as the endpoints, add the CURRENT render as a
third interior point, and fit a quadratic in (log albedo, log value).  Solved by
bisection because the quadratic need not be invertible in closed form on the
branch we want.

    python wfit3.py '{"w":162, ...}'   # tag of the current render is arg 2
"""
import json
import math
import sys

import numpy as np

import proj
from wmeter import load

POSES = ["p_runner", "p_stairs", "p_doors2"]
KEYS = ["n", "e", "w", "an", "aw", "as", "jog", "s"]


def measure(tag):
    """Weighted mean of each wall over the clean, z-buffered, moved-pixel set."""
    acc = {}
    for pose in POSES:
        A = load(f"shots/wpA_{pose}.png")
        B = load(f"shots/wpB_{pose}.png")
        moved = np.abs(B - A) > 8
        keys, ids = proj.wall_ids(pose, KEYS, ny=420, na=950)
        try:
            R = load(f"shots/{tag}{pose}.png")
        except FileNotFoundError:
            continue
        for i, k in enumerate(KEYS):
            m = (ids == i) & moved
            if m.sum() < 400:
                continue
            v = R[m]
            dv = np.concatenate([np.abs(np.diff(R, axis=0))[m[1:]],
                                 np.abs(np.diff(R, axis=1))[m[:, 1:]]])
            a = acc.setdefault(k, [0, 0.0, [], 0.0])
            a[0] += int(m.sum())
            a[1] += float(v.sum())
            a[2].append((pose, int(m.sum()), float(v.mean()), float(v.std()),
                         float(dv.mean())))
            a[3] += float(dv.sum()) * 0        # placeholder, per-pose is enough
    return {k: (a[1] / a[0], a[0], a[2]) for k, a in acc.items()}


def solve(pts, target):
    """pts: [(albedo, value)] -- >=3 gives a quadratic in log-log."""
    pts = sorted(pts)
    xs = np.log(np.array([p[0] for p in pts]))
    ys = np.log(np.array([p[1] for p in pts]))
    deg = 2 if len(pts) >= 3 else 1
    c = np.polyfit(xs, ys, deg)
    lo, hi = math.log(0.03), math.log(1.0)
    t = math.log(target)
    for _ in range(80):
        mid = (lo + hi) / 2
        if np.polyval(c, mid) < t:
            lo = mid
        else:
            hi = mid
    return min(1.0, max(0.03, math.exp((lo + hi) / 2)))


def main():
    tgt = json.loads(sys.argv[1])
    tag = sys.argv[2] if len(sys.argv) > 2 else "walls3_"
    cur = json.load(open("walls3_fit.json"))
    mA, mB, mC = measure("wpA_"), measure("wpB_"), measure(tag)
    out = {}
    for k in KEYS:
        if k not in mA or k not in mC:
            print(f"  {k:4s} not visible")
            continue
        a_cur = int(cur[k][1:3], 16) / 255.0
        pts = [(0.502, mA[k][0]), (1.0, mB[k][0]), (a_cur, mC[k][0])]
        alb = solve(pts, tgt[k])
        hexs = "#%02x%02x%02x" % ((round(alb * 255),) * 3)
        out[k] = hexs
        rows = " ".join(f"[{p} {n} {v:.0f}]" for p, n, v, _s, _d in mC[k][2])
        print(f"  {k:4s} now={mC[k][0]:6.1f} (albedo {cur[k]})  "
              f"target={tgt[k]:5.1f} -> {hexs}   {rows}")
    json.dump(out, open("walls3_fit.json", "w"), indent=1)
    print("wrote walls3_fit.json", out)


if __name__ == "__main__":
    main()
