import sys, os
from PIL import Image
import numpy as np
P = r"C:\Users\Manuel\Desktop\Pro\3d HA\docs\v2 Hallway-jpg"
def L(im):
    a=np.asarray(im.convert("RGB"),dtype=float)
    return 0.2126*a[:,:,0]+0.7152*a[:,:,1]+0.0722*a[:,:,2]
for f in ["two_closed_white_doors_1.jpg","two_closed_white_doors_2.jpg","hallway_looking_towards_stairs.jpg"]:
    im=Image.open(os.path.join(P,f)); print(f, im.size)
