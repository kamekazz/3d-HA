import sys, os
from PIL import Image, ImageDraw
P=r'C:\Users\Manuel\Desktop\Pro\3d HA\docs\v2 Hallway-jpg'
S=r'C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\hall2\shots'
OUT=r'C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\hall2\crops'
f=sys.argv[1]; z=int(sys.argv[2]) if len(sys.argv)>2 else 2
step=int(sys.argv[3]) if len(sys.argv)>3 else 50
base = S if os.path.exists(os.path.join(S,f)) else P
im=Image.open(os.path.join(base,f)).convert('RGB')
w,h=im.size
im=im.resize((w*z,h*z), Image.LANCZOS)
d=ImageDraw.Draw(im)
for x in range(0,w,step):
    d.line([(x*z,0),(x*z,h*z)], fill=(255,0,0), width=1)
    d.text((x*z+2,2), str(x), fill=(255,0,0))
for y in range(0,h,step):
    d.line([(0,y*z),(w*z,y*z)], fill=(0,160,255), width=1)
    d.text((2,y*z+2), str(y), fill=(0,160,255))
o=os.path.join(OUT,'grid_'+os.path.splitext(f)[0]+'.png')
im.save(o); print(o, im.size)
