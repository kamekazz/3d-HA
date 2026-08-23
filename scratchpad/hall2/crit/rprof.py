import os,sys
from PIL import Image
import numpy as np
S=r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\hall2\shots"
a=np.asarray(Image.open(os.path.join(S,sys.argv[1])).convert("RGB"),dtype=float)
L=0.2126*a[:,:,0]+0.7152*a[:,:,1]+0.0722*a[:,:,2]
for arg in sys.argv[2:]:
    k=arg.split(",")
    if k[0]=="r": print("row y=%s x%s-%s:"%(k[1],k[2],k[3])," ".join("%d"%v for v in L[int(k[1]),int(k[2]):int(k[3])]))
    elif k[0]=="c": print("col x=%s y%s-%s:"%(k[1],k[2],k[3])," ".join("%d"%v for v in L[int(k[2]):int(k[3]),int(k[1])]))
    else:
        _,y0,y1,x0,x1,lbl=k
        b=L[int(y0):int(y1),int(x0):int(x1)]
        print("%-24s mean %6.1f sd %5.2f |d1|h %5.2f |d1|v %5.2f"%(lbl,b.mean(),b.std(),np.abs(np.diff(b,axis=1)).mean(),np.abs(np.diff(b,axis=0)).mean()))
