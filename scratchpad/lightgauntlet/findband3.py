"""Fast band search: integral image over medians is not separable, so use means
for the coarse hunt and verify the winner with medians."""
import sys, numpy as np
from PIL import Image
def band(a,y0,y1,x0,x1,n=8):
    xs=np.linspace(x0,x1,n+1).astype(int)
    return [round(float(np.median(a[y0:y1, xs[i]:xs[i+1]])),1) for i in range(n)]
target=np.array([float(v) for v in sys.argv[2].split(',')])
a=np.asarray(Image.open(sys.argv[1]).convert('L'),dtype=float)
h,w=a.shape
ii=np.zeros((h+1,w+1)); ii[1:,1:]=a.cumsum(0).cumsum(1)
def mean(y0,y1,x0,x1): return (ii[y1,x1]-ii[y0,x1]-ii[y1,x0]+ii[y0,x0])/max(1,(y1-y0)*(x1-x0))
best=[]
for y0 in range(0,h-15,3):
    for hh in (14,20,30,50,80):
        y1=y0+hh
        if y1>h: continue
        for x0 in range(0,w-240,15):
            for x1 in range(x0+240,w+1,15):
                xs=np.linspace(x0,x1,9).astype(int)
                s=np.array([mean(y0,y1,xs[i],xs[i+1]) for i in range(8)])
                d=float(np.abs(s-target).sum())
                if d<40: best.append((d,y0,y1,x0,x1))
best.sort(key=lambda t:t[0])
seen=[]
for d,y0,y1,x0,x1 in best[:400]:
    s=band(a,y0,y1,x0,x1)
    dd=sum(abs(s[i]-target[i]) for i in range(8))
    seen.append((dd,y0,y1,x0,x1,s))
seen.sort(key=lambda t:t[0])
for b in seen[:6]: print(round(b[0],1), b[1:5], b[5])
if not seen: print('no match')
