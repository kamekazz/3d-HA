"""Sample mean luma in named boxes of a PNG.  usage: meter.py <png> x0 y0 x1 y1 [...]"""
import sys
from PIL import Image

im = Image.open(sys.argv[1]).convert("RGB")
a = sys.argv[2:]
for i in range(0, len(a), 4):
    x0, y0, x1, y1 = (int(v) for v in a[i:i + 4])
    px = [im.getpixel((x, y)) for x in range(x0, x1) for y in range(y0, y1)]
    lum = [0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2] for p in px]
    n = len(lum)
    mean = sum(lum) / n
    sd = (sum((v - mean) ** 2 for v in lum) / n) ** 0.5
    mx = max(lum)
    clip = sum(1 for p in px if max(p) >= 253) / float(n)
    rgb = tuple(round(sum(p[c] for p in px) / n, 1) for c in range(3))
    print("(%4d,%4d)-(%4d,%4d) n=%5d  mean %6.1f  sd %5.1f  max %5.1f  clip %4.1f%%  rgb %s"
          % (x0, y0, x1, y1, n, mean, sd, mx, 100 * clip, rgb))
