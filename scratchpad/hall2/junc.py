import sys, os, numpy as np
from PIL import Image
P=r"C:\Users\Manuel\Desktop\Pro\3d HA\docs\v2 Hallway-jpg"
S=r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\hall2\shots"
def load(f):
    p=os.path.join(P,f) if os.path.exists(os.path.join(P,f)) else os.path.join(S,f)
    return np.asarray(Image.open(p).convert("RGB")).astype(float).mean(axis=2)
f=sys.argv[1]; a=load(f)
xs=[int(v) for v in sys.argv[2].split(",")]; y0,y1=(int(v) for v in sys.argv[3].split(":"))
for x in xs:
    col=a[y0:y1,x]
    i=int(np.argmin(col))
    print("  x=%4d  junction y=%4d  V=%5.1f   above=%5.1f below=%5.1f" % (x, y0+i, col[i], col[max(0,i-6)], col[min(len(col)-1,i+6)]))
