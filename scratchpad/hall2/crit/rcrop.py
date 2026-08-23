import os,sys
from PIL import Image
S=r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\hall2\shots"
O=r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\hall2\crit"
f=sys.argv[1]
im=Image.open(os.path.join(S,f)).convert("RGB")
for a in sys.argv[2:]:
    x0,y0,x1,y1,sc,name=a.split(",")
    c=im.crop((int(x0),int(y0),int(x1),int(y1)))
    s=float(sc); c=c.resize((int(c.width*s),int(c.height*s)),Image.LANCZOS)
    c.save(os.path.join(O,name)); print(name,c.size)
