import os
from PIL import Image
S = r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\hall2\shots"
OUT = r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\hall2\crops"
jobs = [
 ("kneewall3_p_runner.png", (100,600,420,1150), "r_run_near", 3),
 ("kneewall3_p_stairs.png", (540,680,900,1200), "r_st_cap", 3),
]
for f,box,name,z in jobs:
    im = Image.open(os.path.join(S,f)).convert("RGB").crop(box)
    im = im.resize((im.width*z, im.height*z), Image.LANCZOS)
    im.save(os.path.join(OUT, name+".png")); print(name, im.size)
