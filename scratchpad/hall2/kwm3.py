from PIL import Image
import numpy as np, os
P = r"C:\Users\Manuel\Desktop\Pro\3d HA\docs\v2 Hallway-jpg"
im = np.asarray(Image.open(os.path.join(P,"hallway_with_white_runner_rug.jpg")).convert("L")).astype(float)
# column through the middle of the bath door leaf
for x in (225, 235, 245):
    col = im[100:270, x]
    print("x",x, "".join("%d"%min(9,int(v/28)) for v in col))
print()
# rows: find door casing edges near y=180
for y in (130, 180, 230):
    print("y",y, "".join("%d"%min(9,int(v/28)) for v in im[y, 190:290]))
print()
# the cap's far end: scan columns 195..215 for the bright cap band
for x in (196, 200, 204, 208):
    col = im[180:270, x]
    print("cap x",x, "".join("%d"%min(9,int(v/28)) for v in col))
