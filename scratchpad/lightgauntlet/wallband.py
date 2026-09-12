"""Find a horizontal band whose 8 boxes are ALL wall — i.e. all 8 moved when the
wall fill was turned on. Widest such band, then the darkest one of those."""
import sys, numpy as np
from PIL import Image
a=np.asarray(Image.open(sys.argv[1]).convert('L'),float)
b=np.asarray(Image.open(sys.argv[2]).convert('L'),float)
h,w=a.shape
def med(m,y0,y1,x0,x1,n=8):
    xs=np.linspace(x0,x1,n+1).astype(int)
    return [float(np.median(m[y0:y1,xs[i]:xs[i+1]])) for i in range(n)]
best=None
for y0 in range(0,h-20,5):
    for hh in (16,24,36):
        y1=y0+hh
        if y1>h: continue
        for x0 in range(0,w-240,20):
            for x1 in range(x0+240,w+1,20):
                d=med(b,y0,y1,x0,x1); s=med(a,y0,y1,x0,x1)
                if min(d[i]-s[i] for i in range(8))<8: continue
                score=(x1-x0)
                if best is None or score>best[0]: best=(score,y0,y1,x0,x1,s,d)
if best:
    print('band y%d-%d x%d-%d  width %d'%(best[1],best[2],best[3],best[4],best[0]))
    print(' before',[round(v) for v in best[5]],'ratio %.2f'%(max(best[5])/max(min(best[5]),0.5)))
    print(' after ',[round(v) for v in best[6]],'ratio %.2f'%(max(best[6])/max(min(best[6]),0.5)))
else: print('none')
