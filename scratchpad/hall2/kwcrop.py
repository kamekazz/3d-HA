import os
from PIL import Image
P = r"C:\Users\Manuel\Desktop\Pro\3d HA\docs\v2 Hallway-jpg"
OUT = r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\hall2\crops"
os.makedirs(OUT, exist_ok=True)
jobs = [
 ("hallway_with_white_runner_rug.jpg", (120,190,230,360), "kw_runner", 4),
 ("hallway_looking_towards_stairs.jpg",(240,255,450,470), "kw_stairs", 3),
 ("staircase_looking_down.jpg",        (270,100,450,300), "kw_down",   4),
 ("staircase_looking_up.jpg",          (140, 40,260,160), "kw_up",     5),
]
for f,box,name,z in jobs:
    im = Image.open(os.path.join(P,f)).convert("RGB").crop(box)
    im = im.resize((im.width*z, im.height*z), Image.LANCZOS)
    im.save(os.path.join(OUT, name+".png"))
    print(name, im.size)
