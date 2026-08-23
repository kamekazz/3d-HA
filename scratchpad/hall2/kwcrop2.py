import os
from PIL import Image
P = r"C:\Users\Manuel\Desktop\Pro\3d HA\docs\v2 Hallway-jpg"
OUT = r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\hall2\crops"
jobs = [
 ("hallway_with_white_runner_rug.jpg", (130,225,190,360), "kw_end",  6),
 ("hallway_looking_towards_stairs.jpg",(240,240,360,380), "kw_far",  6),
 ("hallway_looking_towards_stairs.jpg",(300,300,450,600), "kw_near", 4),
 ("staircase_looking_down.jpg",        (280,120,450,240), "kw_cap",  6),
]
for f,box,name,z in jobs:
    im = Image.open(os.path.join(P,f)).convert("RGB").crop(box)
    im = im.resize((im.width*z, im.height*z), Image.LANCZOS)
    im.save(os.path.join(OUT, name+".png")); print(name, im.size)
