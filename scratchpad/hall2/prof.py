"""Vertical/horizontal luminance profile through a point."""
import sys, os, numpy as np
from PIL import Image
P=r"C:\Users\Manuel\Desktop\Pro\3d HA\docs\v2 Hallway-jpg"
S=r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\hall2\shots"
def load(f):
    p = os.path.join(P,f) if os.path.exists(os.path.join(P,f)) else os.path.join(S,f)
    return np.asarray(Image.open(p).convert("RGB")).astype(float).mean(axis=2)
f=sys.argv[1]; a=load(f); mode=sys.argv[2]
x0,y0,x1,y1=(int(v) for v in sys.argv[3].split(","))
n=max(abs(x1-x0),abs(y1-y0))+1
xs=np.linspace(x0,x1,n); ys=np.linspace(y0,y1,n)
vals=[a[int(round(y)),int(round(x))] for x,y in zip(xs,ys)]
print(f, mode, sys.argv[3])
print(" ".join("%.0f"%v for v in vals))
