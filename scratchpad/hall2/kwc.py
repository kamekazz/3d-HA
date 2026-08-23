import os, sys
from PIL import Image
S = r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\hall2\shots"
OUT = r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\hall2\crops"
jobs = [
 ("p_runner", (60,600,420,1150), 2),
 ("p_stairs", (500,600,900,1200), 2),
 ("p_down",   (540,280,900,900), 2),
]
tag = sys.argv[1]
for name,box,z in jobs:
    p = os.path.join(S, tag+name+".png")
    if not os.path.exists(p): continue
    im = Image.open(p).convert("RGB").crop(box)
    im = im.resize((im.width*z, im.height*z), Image.LANCZOS)
    o = os.path.join(OUT, "r_"+tag+name+".png"); im.save(o); print(o, im.size)
