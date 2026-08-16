"""sd AND mean|delta| between adjacent pixels, at NATIVE resolution."""
import sys
import numpy as np
from PIL import Image, ImageDraw
path = sys.argv[1]
im = Image.open(path).convert("RGB")
a = np.asarray(im).astype(np.float32) @ np.array([0.2126, 0.7152, 0.0722], np.float32)
args = sys.argv[2:]
dbg = im.copy(); d = ImageDraw.Draw(dbg)
i = 0
while i < len(args):
    x0, y0, x1, y1 = (int(v) for v in args[i:i+4]); lab = args[i+4]; i += 5
    p = a[y0:y1, x0:x1]
    sd = float(p.std())
    dx = np.abs(np.diff(p, axis=1)).mean()
    dz = np.abs(np.diff(p, axis=0)).mean()
    d1 = float((dx + dz) / 2)
    print("%-16s n=%-7d mean=%6.1f  sd=%5.2f  mean|d|=%5.2f  |d1|/sd=%.3f"
          % (lab, p.size, p.mean(), sd, d1, d1 / sd if sd > 0.01 else 0))
    d.rectangle([x0, y0, x1, y1], outline=(255, 0, 0), width=2)
    d.text((x0+3, y0+3), lab, fill=(255, 0, 0))
dbg.save(path.rsplit(".", 1)[0] + "_boxes.png")
