import os, sys
from PIL import Image
P=r"C:\Users\Manuel\Desktop\Pro\3d HA\docs\v2 Hallway-jpg"
O=r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\hall2\crops"
os.makedirs(O, exist_ok=True)
f, box, z, nm = sys.argv[1], tuple(int(v) for v in sys.argv[2].split(",")), float(sys.argv[3]), sys.argv[4]
im = Image.open(os.path.join(P,f)).convert("RGB")
print("full size", im.size)
im = im.crop(box)
im = im.resize((int(im.width*z), int(im.height*z)), Image.LANCZOS)
im.save(os.path.join(O,nm+".png")); print(nm, im.size)
