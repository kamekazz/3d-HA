"""Meter a rectangular patch of any image.  Usage:

    python m.py <img> x0 y0 x1 y1 [label] [x0 y0 x1 y1 label] ...

Coordinates are PIXELS.  Prints mean/sd of Rec.709 luminance plus mean RGB.
Also writes <img>_boxes.png with every sampled box outlined, so the sample
can be checked by eye (the round-3 report's numbers were wrong because the
samples silently swallowed other objects).
"""
import sys
from PIL import Image, ImageDraw
import numpy as np

path = sys.argv[1]
im = Image.open(path).convert("RGB")
a = np.asarray(im).astype(np.float32)
args = sys.argv[2:]
dbg = im.copy()
d = ImageDraw.Draw(dbg)
i = 0
while i < len(args):
    x0, y0, x1, y1 = (int(v) for v in args[i:i + 4])
    label = args[i + 4] if i + 4 < len(args) and not args[i + 4].lstrip("-").isdigit() else "?"
    i += 5 if label != "?" else 4
    p = a[y0:y1, x0:x1]
    lum = p @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    print("%-22s n=%-7d mean=%6.1f sd=%5.1f  rgb=(%.0f,%.0f,%.0f)  min=%.0f max=%.0f"
          % (label, lum.size, lum.mean(), lum.std(),
             p[..., 0].mean(), p[..., 1].mean(), p[..., 2].mean(),
             lum.min(), lum.max()))
    d.rectangle([x0, y0, x1, y1], outline=(255, 0, 0), width=2)
    d.text((x0 + 3, y0 + 3), label, fill=(255, 0, 0))
dbg.save(path.rsplit(".", 1)[0] + "_boxes.png")
