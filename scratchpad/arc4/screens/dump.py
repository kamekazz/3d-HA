import os, sys
_R = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..","..",".."))
for p in (os.path.join(_R,"tools"), os.path.join(_R,"scratchpad","bsmt"),
          os.path.join(_R,"scratchpad","arc4"), os.path.join(_R,"scratchpad","arc4","art")):
    if p not in sys.path: sys.path.insert(0,p)
import ar2, atlas4
from PIL import Image
for k in sorted(x for x in atlas4.PANELS if x.endswith(".screen")):
    w,h = atlas4.dims(k)
    px = atlas4.render(k, w, h)
    im = Image.new("RGB",(w,h))
    im.putdata([tuple(c) for row in px for c in row])
    lum=[0.299*c[0]+0.587*c[1]+0.114*c[2] for row in px for c in row]
    print("%-46s %dx%d  mean %5.1f  max %3.0f"%(k,w,h,sum(lum)/len(lum),max(lum)))
    im.resize((w*6,h*6),Image.NEAREST).save(os.path.join(_R,"scratchpad","arc4","screens","panel_%s.png"%k.replace(".","_")))
