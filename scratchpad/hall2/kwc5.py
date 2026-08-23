import os,sys
from PIL import Image
S = r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\hall2\shots"
OUT = r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\hall2\crops"
f,box,name,z = sys.argv[1], tuple(int(v) for v in sys.argv[2].split(",")), sys.argv[3], int(sys.argv[4])
base = S if os.path.exists(os.path.join(S,f)) else r"C:\Users\Manuel\Desktop\Pro\3d HA\docs\v2 Hallway-jpg"
im = Image.open(os.path.join(base,f)).convert("RGB").crop(box)
im = im.resize((im.width*z, im.height*z), Image.LANCZOS)
im.save(os.path.join(OUT, name+".png")); print(name, im.size)
