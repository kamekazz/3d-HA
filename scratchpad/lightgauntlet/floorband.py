"""Locate the floor as "the pixels that moved when the floor fill moved", then
report an 8-box median band across it for every frame given.

  python floorband.py base.png changed.png [more.png ...]
"""
import sys
import numpy as np
from PIL import Image


def L(p):
    return np.asarray(Image.open(p).convert('L'), float)


def med(m, y0, y1, x0, x1, n=8):
    xs = np.linspace(x0, x1, n + 1).astype(int)
    return [float(np.median(m[y0:y1, xs[i]:xs[i + 1]])) for i in range(n)]


a, b = L(sys.argv[1]), L(sys.argv[2])
h, w = a.shape
moved = (b - a) >= 4.0
# widest run of columns, inside the tallest band of rows, that is >=70% moved
rows = moved.mean(axis=1)
best = None
for hh in (24, 36, 48):
    for y0 in range(0, h - hh, 4):
        y1 = y0 + hh
        cols = moved[y0:y1].mean(axis=0) >= 0.7
        run = x0 = 0
        for x in range(w + 1):
            if x < w and cols[x]:
                run += 1
            else:
                if run > 0 and (best is None or run > best[0]):
                    best = (run, y0, y1, x - run, x)
                run = 0
    if best and best[0] >= 300:
        break
if not best:
    print('nothing moved by >=4')
    sys.exit(0)
_, y0, y1, x0, x1 = best
print('band y%d-%d x%d-%d  width %d' % (y0, y1, x0, x1, best[0]))
for p in sys.argv[1:]:
    v = med(L(p), y0, y1, x0, x1)
    print('  %-44s %s  median %.1f' % (p.split('/')[-1], [round(x) for x in v],
                                       float(np.median(v))))
