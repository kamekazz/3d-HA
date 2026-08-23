import sys, os
import numpy as np
from PIL import Image
P=r'C:\Users\Manuel\Desktop\Pro\3d HA\docs\v2 Hallway-jpg'
S=r'C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\hall2\shots'
f=sys.argv[1]; base = S if os.path.exists(os.path.join(S,f)) else P
a=np.asarray(Image.open(os.path.join(base,f)).convert('RGB')).astype(float)
L=0.2126*a[:,:,0]+0.7152*a[:,:,1]+0.0722*a[:,:,2]
for spec in sys.argv[2:]:
    y,x0,x1=[int(v) for v in spec.split(',')]
    print(f"--- y={y}")
    print("  " + " ".join(f"{x}:{L[y,x]:.0f}" for x in range(x0,x1+1)))
