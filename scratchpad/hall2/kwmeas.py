from PIL import Image
import numpy as np, os
P = r"C:\Users\Manuel\Desktop\Pro\3d HA\docs\v2 Hallway-jpg"
im = np.asarray(Image.open(os.path.join(P,"hallway_with_white_runner_rug.jpg")).convert("L")).astype(float)
print("shape", im.shape)
# vertical scanlines across the knee wall near end (x ~ 150..175 in original)
for x in (150,155,158,162,166,170,174):
    col = im[190:360, x]
    s = "".join("%d"%min(9,int(v/28)) for v in col)
    print(x, s)
