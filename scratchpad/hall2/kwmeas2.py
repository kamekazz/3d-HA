from PIL import Image
import numpy as np, os
P = r"C:\Users\Manuel\Desktop\Pro\3d HA\docs\v2 Hallway-jpg"
im = np.asarray(Image.open(os.path.join(P,"hallway_with_white_runner_rug.jpg")).convert("L")).astype(float)
x0,x1,y0,y1 = 125,225,195,375
print("cols", " ".join("%3d"%x for x in range(x0,x1,10)))
for y in range(y0,y1,3):
    row = im[y, x0:x1]
    print("%3d "%y + "".join("%d"%min(9,int(v/28)) for v in row))
