import sys, os, numpy as np
from PIL import Image
P=r"C:\Users\Manuel\Desktop\Pro\3d HA\docs\v2 Hallway-jpg"
S=r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\hall2\shots"
def load(f):
    p = os.path.join(P,f) if os.path.exists(os.path.join(P,f)) else os.path.join(S,f)
    return np.asarray(Image.open(p).convert("RGB")).astype(float).mean(axis=2)
f=sys.argv[1]; thr=float(sys.argv[2]); ylim=int(sys.argv[3])
a=load(f); mask=(a>=thr); mask[ylim:,:]=False
seen=np.zeros_like(mask)
H,W=mask.shape
import collections
for y in range(H):
    for x in range(W):
        if mask[y,x] and not seen[y,x]:
            q=collections.deque([(y,x)]); seen[y,x]=True; pts=[]
            while q:
                cy,cx=q.popleft(); pts.append((cy,cx))
                for dy in(-1,0,1):
                    for dx in(-1,0,1):
                        ny,nx=cy+dy,cx+dx
                        if 0<=ny<H and 0<=nx<W and mask[ny,nx] and not seen[ny,nx]:
                            seen[ny,nx]=True; q.append((ny,nx))
            if len(pts)>=4:
                ys=[p[0] for p in pts]; xs=[p[1] for p in pts]
                print("  n=%4d  cx=%6.1f cy=%6.1f  w=%d h=%d" % (len(pts), sum(xs)/len(xs), sum(ys)/len(ys), max(xs)-min(xs)+1, max(ys)-min(ys)+1))
