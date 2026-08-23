import sys, os, numpy as np
from PIL import Image
P=r"C:\Users\Manuel\Desktop\Pro\3d HA\docs\v2 Hallway-jpg"
S=r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\hall2\shots"
def load(f):
    p = os.path.join(P,f) if os.path.exists(os.path.join(P,f)) else os.path.join(S,f)
    return np.asarray(Image.open(p).convert("RGB")).astype(float)
def patch(a, x, y, r=4):
    c = a[max(0,y-r):y+r+1, max(0,x-r):x+r+1]
    L = c.mean(axis=2)
    return L.mean(), L.std(), c.reshape(-1,3).mean(axis=0)
if __name__ == "__main__":
    f = sys.argv[1]; a = load(f)
    print(f, a.shape)
    for spec in sys.argv[2:]:
        parts = spec.split(":")
        nm = parts[0]; x,y = (int(v) for v in parts[1].split(","))
        r = int(parts[2]) if len(parts)>2 else 4
        mu, sd, rgb = patch(a,x,y,r)
        print("  %-16s (%3d,%3d) r%d  V=%6.1f sd=%4.1f  rgb=%5.1f,%5.1f,%5.1f  B-R=%+.1f" % (nm,x,y,r,mu,sd,rgb[0],rgb[1],rgb[2],rgb[2]-rgb[0]))
