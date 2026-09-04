import sys, numpy as np
from PIL import Image
def band(a,y0,y1,x0,x1,n=8):
    xs=np.linspace(x0,x1,n+1).astype(int)
    return [round(float(np.median(a[y0:y1, xs[i]:xs[i+1]])),1) for i in range(n)]
target=[float(v) for v in sys.argv[2].split(',')]
a=np.asarray(Image.open(sys.argv[1]).convert('L'),dtype=float)
h,w=a.shape
best=[]
for y0 in range(0,h-15,4):
    for hh in (12,16,20,25,30,40,60,80,100):
        y1=y0+hh
        if y1>h: continue
        for x0 in range(0,w-200,20):
            for x1 in range(x0+240,w+1,20):
                s=band(a,y0,y1,x0,x1)
                d=sum(abs(s[i]-target[i]) for i in range(8))
                if d<12: best.append((d,y0,y1,x0,x1,s))
best.sort(key=lambda t:t[0])
for b in best[:6]: print(round(b[0],1), b[1:5], b[5])
if not best: print('no match under 12')
