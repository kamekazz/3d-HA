"""Luminance probe across a band of a lightshot frame (before/after comparable).

  python wallprobe.py shots/r13_r2base shots/r13_r2a --band 0.09 0.15 --x0 .22 --x1 .98 -n 12

--axis h  : N boxes spread along X inside the y-band (a wall traverse)
--axis v  : N boxes spread along Y inside the x-band (a corridor run)
Median inside each box, so one plant leaf clipping a box does not decide it.
"""
import argparse, statistics
from PIL import Image

def series(path, y0, y1, x0, x1, n, axis):
    im = Image.open(path).convert('L')
    w, h = im.size
    out = []
    for i in range(n):
        if axis == 'h':
            span = (x1 - x0) / n
            a, b = int(w*(x0+i*span)), int(w*(x0+(i+1)*span))
            box = (a, int(h*y0), b, int(h*y1))
        else:
            span = (y1 - y0) / n
            a, b = int(h*(y0+i*span)), int(h*(y0+(i+1)*span))
            box = (int(w*x0), a, int(w*x1), b)
        out.append(round(statistics.median(list(im.crop(box).getdata()))))
    return out

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('prefix', nargs='+')
    p.add_argument('--band', nargs=2, type=float, default=[0.10, 0.16])
    p.add_argument('--x0', type=float, default=0.05)
    p.add_argument('--x1', type=float, default=0.95)
    p.add_argument('--axis', default='h', choices=['h', 'v'])
    p.add_argument('-n', type=int, default=9)
    a = p.parse_args()
    for pre in a.prefix:
        on = series(pre+'_on.png', a.band[0], a.band[1], a.x0, a.x1, a.n, a.axis)
        off = series(pre+'_off.png', a.band[0], a.band[1], a.x0, a.x1, a.n, a.axis)
        print('%-28s ON  %s   max/min %.2f' % (pre.split('/')[-1], on, max(on)/max(1, min(on))))
        print('%-28s OFF %s' % ('', off))
