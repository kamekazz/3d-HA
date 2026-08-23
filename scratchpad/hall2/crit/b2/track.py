"""Track a baseboard along x: for each column find the brightest pixel (the cap
ribbon) inside a search band, then sample `off` px below it (the board face).
Reports the face series' mean / sd / mean|d1|, and the cap series too."""
import sys
from PIL import Image
im = Image.open(sys.argv[1]).convert("RGB")
x0,x1,ya,yb,off = (int(v) for v in sys.argv[2:7])
step = int(sys.argv[7]) if len(sys.argv)>7 else 1
def L(x,y):
    r,g,b = im.getpixel((x,y)); return 0.2126*r+0.7152*g+0.0722*b
cap=[]; face=[]; wall=[]
for x in range(x0,x1,step):
    best=max(range(ya,yb), key=lambda y: L(x,y))
    cap.append(L(x,best)); face.append(L(x,min(im.height-1,best+off)))
    wall.append(L(x,max(0,best-off)))
def st(v,n):
    m=sum(v)/len(v); sd=(sum((a-m)**2 for a in v)/len(v))**.5
    d=sum(abs(v[i+1]-v[i]) for i in range(len(v)-1))/(len(v)-1)
    print("%-6s mean %6.1f  sd %5.2f  mean|d1| %5.2f  |d1|/sd %.3f"%(n,m,sd,d,d/sd if sd else 0))
    return m
mc=st(cap,"cap"); mf=st(face,"face"); mw=st(wall,"wall")
print("cap/wall %.3f  face/wall %.3f  cap/face %.3f"%(mc/mw,mf/mw,mc/mf))
print("face:", " ".join("%.0f"%v for v in face[:70]))
