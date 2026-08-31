"""Per-tile PNG cost, in the encoder the app actually ships (glb.png_rgb,
filter type 0) and in two cheaper filterings, so the integrator can see what
the filter choice is worth."""
import os
import struct
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
import art_g2 as A                                   # noqa: E402

T = A.TILE
ORDER = list(A.PANELS.keys())


def enc(rows, ftype):
    raw = bytearray()
    prev = [0] * (len(rows[0]) * 3)
    for row in rows:
        cur = [c for px in row for c in px]
        raw.append(ftype)
        if ftype == 0:
            raw.extend(v & 0xFF for v in cur)
        elif ftype == 2:
            raw.extend((cur[i] - prev[i]) & 0xFF for i in range(len(cur)))
        elif ftype == 1:
            raw.extend((cur[i] - (cur[i - 3] if i >= 3 else 0)) & 0xFF
                       for i in range(len(cur)))
        prev = cur
    return len(zlib.compress(bytes(raw), 9)) + 60


tot0 = tot2 = 0
big = []
for n in ORDER:
    px = [[(0, 0, 0)] * T for _ in range(T)]
    A.PANELS[n](px, 0, 0, T)
    a, b, c = enc(px, 0), enc(px, 1), enc(px, 2)
    flat = [v for row in px for p in row for v in p]
    big.append((a, n, b, c, sum(flat) / len(flat)))
    tot0 += a
    tot2 += min(a, b, c)
big.sort(reverse=True)
print("%-32s %8s %8s %8s %6s" % ("panel", "none", "sub", "up", "mean"))
for a, n, b, c, m in big:
    print("%-32s %8d %8d %8d %6.1f" % (n, a, b, c, m))
print("TOTAL filter-0 (what png_rgb does) : %d bytes" % tot0)
print("TOTAL best-filter-per-tile         : %d bytes" % tot2)
