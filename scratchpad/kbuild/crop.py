"""Crop / measure helper: crop.py <img> <x0> <y0> <x1> <y1> <out> [scale]
Coordinates are FRACTIONS of width/height.  Also prints luminance stats.
"""
import sys
from PIL import Image
import numpy as np

p = sys.argv[1]
x0, y0, x1, y1 = (float(v) for v in sys.argv[2:6])
out = sys.argv[6]
scale = float(sys.argv[7]) if len(sys.argv) > 7 else 1.0
im = Image.open(p).convert("RGB")
W, H = im.size
box = (int(W * x0), int(H * y0), int(W * x1), int(H * y1))
c = im.crop(box)
if scale != 1.0:
    c = c.resize((int(c.width * scale), int(c.height * scale)), Image.LANCZOS)
c.save(out)
a = np.asarray(im.crop(box)).astype(np.float32)
lum = a @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
print(f"{p} {box} size={c.size} mean={lum.mean():.1f} sd={lum.std():.1f} "
      f"rgb={[round(float(a[...,i].mean()),1) for i in range(3)]} "
      f"p5={np.percentile(lum,5):.0f} p95={np.percentile(lum,95):.0f}")
