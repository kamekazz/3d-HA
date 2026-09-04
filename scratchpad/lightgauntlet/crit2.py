import sys, json
from PIL import Image, ImageStat

def lum(im):
    return im.convert('L')

def stats(path):
    im = Image.open(path).convert('RGB')
    w,h = im.size
    L = im.convert('L')
    import numpy as np
    a = np.asarray(L, dtype=float)
    rgb = np.asarray(im, dtype=float)
    cx0,cx1 = int(w*0.3), int(w*0.7)
    cy0,cy1 = int(h*0.3), int(h*0.7)
    centre = a[cy0:cy1, cx0:cx1]
    return dict(size=(w,h), mean=round(a.mean(),1), centre=round(centre.mean(),1),
                p50=round(float(np.percentile(a,50)),1),
                p95=round(float(np.percentile(a,95)),1),
                p99=round(float(np.percentile(a,99)),1),
                max=round(float(a.max()),1),
                frac_below40=round(float((a<40).mean()*100),1),
                rgb_mean=[round(float(rgb[:,:,i].mean()),1) for i in range(3)],
                bright_rgb=[round(float(rgb[:,:,i][a>=np.percentile(a,99)].mean()),1) for i in range(3)])

def band(path, y0, y1, x0, x1, n=8):
    import numpy as np
    im = Image.open(path).convert('L')
    a = np.asarray(im, dtype=float)
    xs = np.linspace(x0, x1, n+1).astype(int)
    out=[]
    for i in range(n):
        box = a[y0:y1, xs[i]:xs[i+1]]
        out.append(round(float(np.median(box)),1))
    return out

if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd=='stats':
        for p in sys.argv[2:]:
            print(p, json.dumps(stats(p)))
    elif cmd=='band':
        p=sys.argv[2]; y0,y1,x0,x1=[int(v) for v in sys.argv[3:7]]
        n=int(sys.argv[7]) if len(sys.argv)>7 else 8
        s=band(p,y0,y1,x0,x1,n)
        print(p, s, 'peak:edge=%.2f'%(max(s)/max(min(s),0.5)))
