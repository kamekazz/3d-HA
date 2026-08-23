import sys, os
import numpy as np
from PIL import Image
P=r'C:\Users\Manuel\Desktop\Pro\3d HA\docs\v2 Hallway-jpg'
S=r'C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\hall2\shots'
f=sys.argv[1]; base = S if os.path.exists(os.path.join(S,f)) else P
a=np.asarray(Image.open(os.path.join(base,f)).convert('RGB')).astype(float)
L=0.2126*a[:,:,0]+0.7152*a[:,:,1]+0.0722*a[:,:,2]
for spec in sys.argv[2:]:
    x,y0,y1=[int(v) for v in spec.split(',')]
    print(f"--- x={x}  y {y0}..{y1}")
    print("  " + " ".join(f"{y}:{L[y,x]:.0f}" for y in range(y0,y1+1)))
