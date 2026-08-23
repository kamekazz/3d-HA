from PIL import Image
import numpy as np, os
P = r"C:\Users\Manuel\Desktop\Pro\3d HA\docs\v2 Hallway-jpg"
im = np.asarray(Image.open(os.path.join(P,"hallway_with_white_runner_rug.jpg")).convert("L")).astype(float)
def col(x, y0, y1):
    print(f"--- x={x}")
    prev=None
    for y in range(y0,y1):
        v=im[y,x]
        if prev is None or abs(v-prev)>12:
            print(f"   y={y} L={v:.0f}")
        prev=v
col(235, 100, 270)
col(196, 185, 215)
col(203, 185, 215)
