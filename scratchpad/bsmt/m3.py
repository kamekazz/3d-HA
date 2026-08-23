import sys, os, json
from PIL import Image
import numpy as np

def lum(img):
    a = np.asarray(img.convert("RGB"), dtype=np.float64)
    return 0.2126*a[...,0] + 0.7152*a[...,1] + 0.0722*a[...,2], a

def stats(name, path, boxes):
    img = Image.open(path)
    L, A = lum(img)
    out=[]
    for label,(x0,y0,x1,y1) in boxes.items():
        p = L[y0:y1, x0:x1]
        c = A[y0:y1, x0:x1]
        if p.size < 40: 
            print(f"  {label}: too small"); continue
        d1 = np.mean(np.abs(np.diff(p, axis=1))) if p.shape[1]>1 else 0
        d1b = np.mean(np.abs(np.diff(p, axis=0))) if p.shape[0]>1 else 0
        md = (d1+d1b)/2
        sd = p.std()
        rgb = c.reshape(-1,3).mean(axis=0)
        print(f"  {label:22s} n={p.size:7d} mean={p.mean():6.1f} sd={sd:5.2f} |d1|={md:5.2f} ratio={md/max(sd,1e-6):.3f}  rgb=({rgb[0]:.0f},{rgb[1]:.0f},{rgb[2]:.0f}) R-B={rgb[0]-rgb[2]:+.1f}")
        out.append((label,p.mean(),sd,md))
    return out

if __name__ == "__main__":
    cfg = json.load(open(sys.argv[1]))
    for path, boxes in cfg.items():
        print(path)
        stats(path, path, {k: tuple(v) for k,v in boxes.items()})
