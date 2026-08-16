"""Scan one wall line of a registered plan and report solid runs vs gaps."""
import sys
import numpy as np
sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\circ")
from planmap import load


def scan(key, axis, at, a0, a1, band=0.45, step=0.05, thresh=0.30):
    """axis 'x': wall at world x=at, scan along z a0..a1.
       axis 'z': wall at world z=at, scan along x a0..a1."""
    mask, w2p = load(key)
    vals = []
    n = int(round((a1 - a0) / step))
    for i in range(n + 1):
        a = a0 + i * step
        # sample a short perpendicular band centred on the wall
        hits = []
        for d in np.arange(-band, band + 1e-9, 0.05):
            wx, wz = (at + d, a) if axis == "x" else (a, at + d)
            px, py = w2p(wx, wz)
            ix, iy = int(round(px)), int(round(py))
            hits.append(mask[iy, ix])
        vals.append((a, float(np.mean(hits))))
    runs = []
    cur = None
    for a, v in vals:
        s = v >= thresh
        if cur is None or cur[0] != s:
            if cur:
                runs.append((cur[0], cur[1], a))
            cur = (s, a)
    if cur:
        runs.append((cur[0], cur[1], vals[-1][0]))
    for s, b0, b1 in runs:
        if b1 - b0 < 0.09:
            continue
        print(f"  {'SOLID' if s else 'GAP  '}  {b0:7.2f} .. {b1:7.2f}   ({b1-b0:5.2f} ft)")


if __name__ == "__main__":
    key, axis, at, a0, a1 = sys.argv[1], sys.argv[2], *(float(v) for v in sys.argv[3:6])
    band = float(sys.argv[6]) if len(sys.argv) > 6 else 0.45
    th = float(sys.argv[7]) if len(sys.argv) > 7 else 0.30
    print(f"{key} wall {axis}={at} over {a0}..{a1}")
    scan(key, axis, at, a0, a1, band=band, thresh=th)
