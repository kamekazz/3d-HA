"""Meter rectangles of a render (or a photo) — mean, sd, rgb.

    python r5_meter.py shot.png name x0 x1 y0 y1 [name x0 x1 y0 y1 ...]
"""
import sys

import numpy as np
from PIL import Image

im = Image.open(sys.argv[1]).convert("RGB")
a = np.asarray(im).astype(np.float32)
lum = a @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
args = sys.argv[2:]
for i in range(0, len(args), 5):
    name = args[i]
    x0, x1, y0, y1 = (int(v) for v in args[i + 1:i + 5])
    q = lum[y0:y1, x0:x1]
    c = a[y0:y1, x0:x1]
    print("%-22s mean %6.1f  sd %5.1f  rgb %s" %
          (name, q.mean(), q.std(),
           [round(float(c[..., k].mean()), 1) for k in range(3)]))
