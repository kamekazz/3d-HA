import sys
from PIL import Image
im = Image.open(sys.argv[1]).convert("RGB")
y = int(sys.argv[2]); x0=int(sys.argv[3]); x1=int(sys.argv[4])
for x in range(x0,x1):
    r,g,b = im.getpixel((x,y))
    L = 0.2126*r+0.7152*g+0.0722*b
    print(f"x={x} rgb=({r:3d},{g:3d},{b:3d}) L={L:6.1f}")
