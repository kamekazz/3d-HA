import os, sys
from PIL import Image
P = r"C:\Users\Manuel\Desktop\Pro\3d HA\docs\v2 Hallway-jpg"
S = r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\hall2\shots"
OUT = r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\hall2\crops"
os.makedirs(OUT, exist_ok=True)
jobs = [
 (P,"hallway_with_white_runner_rug.jpg", (110,180,250,370), "ph_run_near", 6),
 (P,"hallway_with_white_runner_rug.jpg", (130,190,220,270), "ph_run_end", 9),
 (P,"hallway_looking_towards_stairs.jpg",(250,250,460,470), "ph_st_cap", 5),
 (P,"hallway_looking_towards_stairs.jpg",(255,255,340,320), "ph_st_far", 10),
]
for base,f,box,name,z in jobs:
    im = Image.open(os.path.join(base,f)).convert("RGB").crop(box)
    im = im.resize((im.width*z, im.height*z), Image.LANCZOS)
    im.save(os.path.join(OUT, name+".png")); print(name, im.size)
