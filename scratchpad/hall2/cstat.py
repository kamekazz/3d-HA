import sys, os, numpy as np
from PIL import Image
P=r"C:\Users\Manuel\Desktop\Pro\3d HA\docs\v2 Hallway-jpg"
S=r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\hall2\shots"
def load(f):
    p = os.path.join(P,f) if os.path.exists(os.path.join(P,f)) else os.path.join(S,f)
    return np.asarray(Image.open(p).convert("RGB")).astype(float)
f=sys.argv[1]; a=load(f)
for spec in sys.argv[2:]:
    nm, box = spec.split(":")
    x0,y0,x1,y1 = (int(v) for v in box.split(","))
    L = a[y0:y1, x0:x1].mean(axis=2)
    d1 = (np.abs(np.diff(L,axis=1)).mean() + np.abs(np.diff(L,axis=0)).mean())/2
    print("  %-14s %s  n=%5d  mean=%6.2f sd=%5.2f  min=%3.0f max=%3.0f  |d1|=%5.3f  |d1|/sd=%5.3f"
          % (nm, box, L.size, L.mean(), L.std(), L.min(), L.max(), d1, d1/max(L.std(),1e-6)))
