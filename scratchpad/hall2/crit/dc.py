import os,sys
from PIL import Image
P = r"C:\Users\Manuel\Desktop\Pro\3d HA\docs\v2 Hallway-jpg"
out = r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\hall2\crit"
def crop(f,box,scale,name):
    im=Image.open(os.path.join(P,f)).convert("RGB").crop(box)
    im=im.resize((im.width*scale,im.height*scale),Image.LANCZOS)
    im.save(os.path.join(out,name)); print(name, im.size)
# doors_2: right door panels + handle region
crop("two_closed_white_doors_2.jpg",(250,30,360,340),4,"ph_d2_right.png")
# doors_2: left door with hinges on its right edge
crop("two_closed_white_doors_2.jpg",(60,10,240,350),3,"ph_d2_left.png")
# doors_1: right door top panels, casing
crop("two_closed_white_doors_1.jpg",(180,0,380,200),4,"ph_d1_top.png")
# doors_1: handle closeup
crop("two_closed_white_doors_1.jpg",(180,120,260,190),8,"ph_d1_handle.png")
