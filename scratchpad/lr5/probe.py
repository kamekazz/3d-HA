"""Sample mean RGB in boxes of an image: probe.py img x0,y0,x1,y1 [more...]"""
import sys
from PIL import Image
im = Image.open(sys.argv[1]).convert("RGB")
print(im.size)
for spec in sys.argv[2:]:
    x0, y0, x1, y1 = [int(v) for v in spec.split(",")]
    c = im.crop((x0, y0, x1, y1))
    px = list(c.getdata())
    n = len(px)
    r = sum(p[0] for p in px) / n
    g = sum(p[1] for p in px) / n
    b = sum(p[2] for p in px) / n
    print(f"{spec:24s} rgb=({r:5.1f},{g:5.1f},{b:5.1f}) lum={0.2126*r+0.7152*g+0.0722*b:6.1f}")
