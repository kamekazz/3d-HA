import sys, os, json
import numpy as np
from PIL import Image
P=r'C:\Users\Manuel\Desktop\Pro\3d HA\docs\v2 Hallway-jpg'
S=r'C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\hall2\shots'
def load(f):
    base = S if os.path.exists(os.path.join(S,f)) else P
    a=np.asarray(Image.open(os.path.join(base,f)).convert('RGB')).astype(float)
    return a, 0.2126*a[:,:,0]+0.7152*a[:,:,1]+0.0722*a[:,:,2]
def rep(name, L, a, x0,y0,x1,y1):
    c=L[y0:y1,x0:x1]; rgb=a[y0:y1,x0:x1].reshape(-1,3).mean(0)
    d1=(np.abs(np.diff(c,axis=1)).mean()+np.abs(np.diff(c,axis=0)).mean())/2
    print(f"{name:26s} n={c.size:5d} mean={c.mean():6.1f} sd={c.std():5.2f} |d1|={d1:5.2f} rgb=({rgb[0]:.0f},{rgb[1]:.0f},{rgb[2]:.0f})")
if __name__=='__main__':
    f=sys.argv[1]; a,L=load(f)
    for spec in sys.argv[2:]:
        nm,x0,y0,x1,y1=spec.split(',')
        rep(nm,L,a,int(x0),int(y0),int(x1),int(y1))
