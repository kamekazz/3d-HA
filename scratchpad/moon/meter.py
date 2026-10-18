"""Meter named regions of a frame (mean sRGB + luminance). Regions are
fractions of the frame so the same names work on any size.
    python meter.py <png> [name=x0,y0,x1,y1 ...]
With no regions: whole frame + the upper sky band + the centre box.
"""
import sys, json
from PIL import Image
im = Image.open(sys.argv[1]).convert('RGB'); W, H = im.size
regions = dict(whole=(0,0,1,1), sky=(0.2,0.0,0.8,0.12), centre=(0.3,0.3,0.7,0.7), ground=(0.1,0.85,0.9,1.0))
for a in sys.argv[2:]:
    k, v = a.split('='); regions[k] = tuple(float(x) for x in v.split(','))
out = {}
px = im.load()
for name, (x0,y0,x1,y1) in regions.items():
    xs = range(int(x0*W), max(int(x0*W)+1, int(x1*W)), 2); ys = range(int(y0*H), max(int(y0*H)+1, int(y1*H)), 2)
    n = 0; r = g = b = 0
    for y in ys:
        for x in xs:
            p = px[x, y]; r += p[0]; g += p[1]; b += p[2]; n += 1
    r/=n; g/=n; b/=n
    out[name] = dict(rgb=[round(r,1), round(g,1), round(b,1)], L=round(0.299*r+0.587*g+0.114*b,1))
print(json.dumps(out))
