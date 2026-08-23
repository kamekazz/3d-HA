"""Sample luma along a line (x0,y0)->(x1,y1), n samples, report sd / mean|d1|."""
import sys, math
from PIL import Image
im = Image.open(sys.argv[1]).convert("RGB")
x0,y0,x1,y1,n = [float(v) for v in sys.argv[2:7]]
n=int(n)
vals=[]
for i in range(n):
    f=i/(n-1.0)
    x,y = x0+(x1-x0)*f, y0+(y1-y0)*f
    r,g,b = im.getpixel((int(round(x)),int(round(y))))
    vals.append(0.2126*r+0.7152*g+0.0722*b)
mean=sum(vals)/len(vals)
sd=(sum((v-mean)**2 for v in vals)/len(vals))**0.5
d1=sum(abs(vals[i+1]-vals[i]) for i in range(len(vals)-1))/(len(vals)-1)
print("mean %.1f  sd %.2f  mean|d1| %.2f  |d1|/sd %.3f" % (mean,sd,d1,d1/sd if sd else 0))
print(" ".join("%.0f"%v for v in vals))
