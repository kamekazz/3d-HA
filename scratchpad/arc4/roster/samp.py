import sys
from PIL import Image
src = sys.argv[1]
im = Image.open(src).convert('RGB')
for spec in sys.argv[2:]:
    lbl, x, y, r = spec.split(':')
    x,y,r = int(x), int(y), int(r)
    px = [im.getpixel((i,j)) for i in range(x-r,x+r+1) for j in range(y-r,y+r+1)]
    n=len(px)
    m = tuple(round(sum(p[k] for p in px)/n) for k in range(3))
    print(f"{lbl:28s} ({x},{y}) r{r}  rgb{m}  #{m[0]:02x}{m[1]:02x}{m[2]:02x}")
