from PIL import Image
import numpy as np, os
P = r"C:\Users\Manuel\Desktop\Pro\3d HA\docs\v2 Hallway-jpg"
im = np.asarray(Image.open(os.path.join(P,"hallway_with_white_runner_rug.jpg")).convert("L")).astype(float)
for x in (200, 208, 270, 278, 286):
    print(f"--- x={x}: " + " ".join(f"{y}:{im[y,x]:.0f}" for y in range(230, 275)))
