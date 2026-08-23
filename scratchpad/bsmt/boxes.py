import sys, json
from PIL import Image, ImageDraw
import numpy as np
def run(path, boxes, out):
    img = Image.open(path).convert("RGB")
    a = np.asarray(img, dtype=np.float64)
    L = 0.2126*a[...,0]+0.7152*a[...,1]+0.0722*a[...,2]
    d = ImageDraw.Draw(img)
    for label,(x0,y0,x1,y1) in boxes.items():
        p = L[y0:y1, x0:x1]; c = a[y0:y1, x0:x1].reshape(-1,3)
        h = (np.mean(np.abs(np.diff(p,axis=1)))+np.mean(np.abs(np.diff(p,axis=0))))/2
        rgb = c.mean(axis=0)
        print(f"  {label:20s} n={p.size:6d} mean={p.mean():6.1f} sd={p.std():5.2f} |d1|={h:5.2f} r={h/max(p.std(),1e-6):.3f} rgb=({rgb[0]:.0f},{rgb[1]:.0f},{rgb[2]:.0f})")
        d.rectangle([x0,y0,x1,y1], outline=(255,0,0), width=3)
        d.text((x0+4,y0+2), label, fill=(255,0,0))
    img.save(out)
