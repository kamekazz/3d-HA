import os
from PIL import Image
P = r"C:\Users\Manuel\Desktop\Pro\3d HA\docs\v2 Hallway-jpg\hallway_with_white_runner_rug.jpg"
O = r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\hall2\crops"
im = Image.open(P).convert("RGB")
for box, nm, z in (((130,180,290,300),"kw_farend",6), ((90,150,300,400),"kw_wide",4)):
    c = im.crop(box); c = c.resize((c.width*z, c.height*z), Image.LANCZOS)
    c.save(os.path.join(O, nm+".png")); print(nm, c.size)
