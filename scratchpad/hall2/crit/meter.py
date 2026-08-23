import sys
import numpy as np
from PIL import Image
im = np.asarray(Image.open(sys.argv[1]).convert("RGB")).astype(float)
for spec in sys.argv[2:]:
    name, x0,y0,x1,y1 = spec.split(",")[0], *[int(v) for v in spec.split(",")[1:5]]
    p = im[y0:y1, x0:x1]
    L = p @ [0.2126,0.7152,0.0722]
    d1 = (np.abs(np.diff(L,axis=1)).mean()+np.abs(np.diff(L,axis=0)).mean())/2
    print(f"{name:<16} n={p.shape[0]*p.shape[1]:>6}  RGB={p[...,0].mean():6.1f},{p[...,1].mean():6.1f},{p[...,2].mean():6.1f}  L={L.mean():6.1f}  sd={L.std():5.2f}  |d1|={d1:5.2f}  ratio={d1/max(L.std(),1e-6):.3f}")
