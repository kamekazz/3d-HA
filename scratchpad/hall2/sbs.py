import os
from PIL import Image
PH = r"C:\Users\Manuel\Desktop\Pro\3d HA\docs\v2 Hallway-jpg"
SH = r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\hall2\shots"
O  = r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\hall2\crops"
JOBS = [
 ("cap", ("staircase_looking_down.jpg",(285,120,450,250)), ("kneewall_p_down.png",(590,300,900,560))),
 ("end", ("hallway_with_white_runner_rug.jpg",(128,215,215,360)), ("kneewall_p_runner.png",(120,620,330,1180))),
 ("run", ("hallway_looking_towards_stairs.jpg",(250,250,450,520)), ("kneewall_p_stairs.png",(540,690,900,1160))),
]
H = 620
for nm,(pf,pb),(rf,rb) in JOBS:
    a = Image.open(os.path.join(PH,pf)).convert("RGB").crop(pb)
    b = Image.open(os.path.join(SH,rf)).convert("RGB").crop(rb)
    a = a.resize((int(a.width*H/a.height), H), Image.LANCZOS)
    b = b.resize((int(b.width*H/b.height), H), Image.LANCZOS)
    c = Image.new("RGB",(a.width+b.width+8,H),(20,20,20))
    c.paste(a,(0,0)); c.paste(b,(a.width+8,0))
    c.save(os.path.join(O,"sbs_"+nm+".png")); print(nm, c.size)
