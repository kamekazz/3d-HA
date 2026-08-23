import os,sys
from PIL import Image
import numpy as np
S=r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\hall2\shots"
def lum(p):
    a=np.asarray(Image.open(p).convert("RGB"),dtype=float)
    return 0.2126*a[:,:,0]+0.7152*a[:,:,1]+0.0722*a[:,:,2]
f=sys.argv[1]
L=lum(os.path.join(S,f))
print(f, L.shape)
def stat(y0,y1,x0,x1,lbl):
    b=L[y0:y1,x0:x1]
    d1=np.abs(np.diff(b,axis=1)).mean()
    print("%-22s mean %6.1f  sd %5.2f  |d1| %5.2f  min %d max %d"%(lbl,b.mean(),b.std(),d1,b.min(),b.max()))
for a in sys.argv[2:]:
    y0,y1,x0,x1,lbl=a.split(",")
    stat(int(y0),int(y1),int(x0),int(x1),lbl)
