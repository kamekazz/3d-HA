import sys, statistics
from PIL import Image

def lum(p): return 0.299*p[0]+0.587*p[1]+0.114*p[2]

def band(path, y0, y1, x0, x1, n=8):
    im = Image.open(path).convert('RGB')
    w = (x1-x0)//n
    out=[]
    for i in range(n):
        bx=im.crop((x0+i*w, y0, x0+(i+1)*w, y1))
        vals=[lum(p) for p in bx.getdata()]
        out.append(round(statistics.median(vals),1))
    return out

def box(path, x0,y0,x1,y1):
    im = Image.open(path).convert('RGB')
    d=list(im.crop((x0,y0,x1,y1)).getdata())
    vals=[lum(p) for p in d]
    vals.sort()
    r=[sum(c[i] for c in d)/len(d) for i in range(3)]
    return dict(median=round(statistics.median(vals),1), mean=round(sum(vals)/len(vals),1),
                p99=round(vals[int(len(vals)*0.99)],1), mx=round(vals[-1],1),
                rgb=tuple(round(v) for v in r))

if __name__=='__main__':
    pass
