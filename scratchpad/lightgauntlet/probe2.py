"""Band probe: median luminance across N boxes in a horizontal band."""
import sys, statistics
from PIL import Image

def series(path, y0, y1, x0, x1, n):
    im = Image.open(path).convert('L'); w,h = im.size
    Y0,Y1 = int(h*y0), int(h*y1); out=[]
    span=(x1-x0)/n
    for i in range(n):
        a=int(w*(x0+i*span)); b=int(w*(x0+(i+1)*span))
        px=list(im.crop((a,Y0,b,Y1)).getdata())
        out.append(round(statistics.median(px)))
    return out

def stats(path):
    im=Image.open(path).convert('L'); d=list(im.getdata())
    s=sorted(d)
    return dict(mean=round(sum(d)/len(d),1), p50=s[len(s)//2], p95=s[int(len(s)*.95)],
                p99=s[int(len(s)*.99)], frac40=round(sum(1 for x in d if x<40)/len(d),2))

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(); p.add_argument('path'); p.add_argument('--band',nargs=2,type=float,default=[.10,.16])
    p.add_argument('--x0',type=float,default=.05); p.add_argument('--x1',type=float,default=.95); p.add_argument('-n',type=int,default=9)
    a=p.parse_args()
    print(a.path, stats(a.path))
    print('  band',a.band, series(a.path,a.band[0],a.band[1],a.x0,a.x1,a.n))
