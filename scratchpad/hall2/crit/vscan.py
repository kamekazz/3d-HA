import sys
from PIL import Image
im = Image.open(sys.argv[1]).convert("RGB")
x = int(sys.argv[2]); y0=int(sys.argv[3]); y1=int(sys.argv[4])
for y in range(y0,y1):
    r,g,b = im.getpixel((x,y))
    L = 0.2126*r+0.7152*g+0.0722*b
    print(f"y={y} rgb=({r:3d},{g:3d},{b:3d}) L={L:6.1f}")
