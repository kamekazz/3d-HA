"""Two-point per-wall albedo fit for `Hall2F Wall Wash Skins`.

Renders wpA_ (#808080) and wpB_ (#ffffff) must already exist -- `walls3.py probe`
makes them and then immediately re-places the real piece.

A wall's sample is `projected face mask AND the pixels that actually moved
between the two probes`.  The projection alone would swallow a door leaf, the
knee wall and the plants; the difference alone cannot say WHICH wall a pixel is
on when several move at once.  Together they are clean.
"""
import json
import math
import sys

import numpy as np

import proj
from wmeter import load

POSES = ["p_runner", "p_stairs", "p_doors2"]
KEYS = ["n", "e", "w", "an", "aw", "as", "jog", "s"]
A_SRGB, B_SRGB = 0.502, 1.0


def samples():
    out = {}
    for pose in POSES:
        A = load(f"shots/wpA_{pose}.png")
        B = load(f"shots/wpB_{pose}.png")
        moved = np.abs(B - A) > 8
        keys, ids = proj.wall_ids(pose, KEYS, ny=420, na=950)
        for i, k in enumerate(KEYS):
            m = (ids == i) & moved
            if m.sum() < 400:
                continue
            out.setdefault(k, []).append((pose, int(m.sum()),
                                          A[m].mean(), B[m].mean()))
    return out


def fit(a_val, b_val):
    """value = C * albedo**g through the two probe points (albedo in sRGB)."""
    g = math.log(b_val / a_val) / math.log(B_SRGB / A_SRGB)
    C = b_val / (B_SRGB ** g)
    return C, g


def solve(C, g, target):
    return min(1.0, max(0.02, (target / C) ** (1.0 / g)))


def main():
    tgt = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    s = samples()
    out = {}
    for k in KEYS:
        rows = s.get(k)
        if not rows:
            print(f"  {k:4s}  not visible in any pose -- left as is")
            continue
        n = sum(r[1] for r in rows)
        a = sum(r[1] * r[2] for r in rows) / n
        b = sum(r[1] * r[3] for r in rows) / n
        C, g = fit(a, b)
        line = (f"  {k:4s} px={n:6d}  A(.502)={a:6.1f}  B(1.0)={b:6.1f}  "
                f"g={g:5.3f} C={C:6.1f}")
        if k in tgt:
            alb = solve(C, g, tgt[k])
            hexs = "#%02x%02x%02x" % ((round(alb * 255),) * 3)
            out[k] = hexs
            line += f"   target={tgt[k]:5.1f} -> {hexs}"
        print(line + "   " + " ".join(f"[{r[0]} {r[1]}]" for r in rows))
    if out:
        with open("walls3_fit.json", "w") as fh:
            json.dump(out, fh, indent=1)
        print("wrote walls3_fit.json", out)


if __name__ == "__main__":
    main()
