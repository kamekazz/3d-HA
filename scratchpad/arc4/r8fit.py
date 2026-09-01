"""Two-point log-linear fit of the carcase response, per wall run."""
import math, statistics, sys
from PIL import Image

def lin(v):
    v = v / 255.0
    return ((v + 0.055) / 1.055) ** 2.4 if v > 0.04045 else v / 12.92

def srgb(a):
    return 255.0 * (1.055 * a ** (1 / 2.4) - 0.055) if a > 0.0031308 else 255.0 * 12.92 * a

def L(p):
    return 0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2]

def pair(fa, fb):
    a = Image.open(fa).convert("RGB").load()
    b = Image.open(fb).convert("RGB").load()
    im = Image.open(fa); W, H = im.size
    la, lb = [], []
    for y in range(H):
        for x in range(W):
            va, vb = L(a[x, y]), L(b[x, y])
            if vb - va > 18:
                la.append(va); lb.append(vb)
    return statistics.median(la), statistics.median(lb), len(la)

A_LUM = 0.299*0x47 + 0.587*0x49 + 0.114*0x54      # #474954
B_LUM = 128.0                                      # #808080
TARGET = 0.215                                     # v4 6 clean black / floor

for run, fa, fb, floor in (
        ("east",  "scratchpad/arc4/shots/r8p_full_east.png", None, 173.5),
        ("north", "scratchpad/arc4/shots/r8_full_north.png",
                  "scratchpad/arc4/shots/probeD_full_north.png", 175.5),
        ("south", "scratchpad/arc4/shots/r8_full_south.png",
                  "scratchpad/arc4/shots/probeD_full_south.png", 167.5)):
    if fb is None:
        continue
    ra, rb, n = pair(fa, fb)
    x1, y1 = math.log(lin(A_LUM)), math.log(lin(ra))
    x2, y2 = math.log(lin(B_LUM)), math.log(lin(rb))
    k = (y2 - y1) / (x2 - x1)
    c = y1 - k * x1
    tgt = TARGET * floor
    want = (math.log(lin(tgt)) - c) / k
    hexlum = srgb(math.exp(want))
    print("%-6s n=%6d  #474954 -> %5.1f   #808080 -> %5.1f   k=%.3f  "
          "target render %.1f  needs authored luma %.1f"
          % (run, n, ra, rb, k, tgt, hexlum))
