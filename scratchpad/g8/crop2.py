import sys, os
import numpy as np
from PIL import Image, ImageDraw
PH = r"C:\Users\Manuel\Desktop\Pro\3d HA\docs\photos-jpg"
OUT = os.path.dirname(os.path.abspath(__file__))
def go(src,x0,y0,x1,y1,zoom=6,grid=10,out="crop.png",lo=None,hi=None):
    p = src if os.path.isabs(src) else os.path.join(PH,src)
    im = Image.open(p).convert("RGB")
    a = np.asarray(im.crop((x0,y0,x1,y1))).astype(float)
    g = a.mean(axis=2)
    if lo is None: lo = np.percentile(g,2)
    if hi is None: hi = np.percentile(g,98)
    a = np.clip((a-lo)*255.0/max(1e-6,(hi-lo)),0,255).astype(np.uint8)
    c = Image.fromarray(a).resize(((x1-x0)*zoom,(y1-y0)*zoom), Image.NEAREST)
    d = ImageDraw.Draw(c)
    for x in range(x0-x0%grid, x1+1, grid):
        u=(x-x0)*zoom; d.line([u,0,u,c.height],fill=(255,0,255)); d.text((u+2,2),str(x),fill=(255,0,255))
    for y in range(y0-y0%grid, y1+1, grid):
        v=(y-y0)*zoom; d.line([0,v,c.width,v],fill=(0,255,255)); d.text((2,v+2),str(y),fill=(0,255,255))
    c.save(os.path.join(OUT,out)); print(out, c.size, "lo=%.0f hi=%.0f"%(lo,hi))
if __name__=="__main__":
    a=sys.argv[1:]
    go(a[0],int(a[1]),int(a[2]),int(a[3]),int(a[4]),int(a[5]) if len(a)>5 else 6,
       int(a[6]) if len(a)>6 else 10, a[7] if len(a)>7 else "crop.png")
