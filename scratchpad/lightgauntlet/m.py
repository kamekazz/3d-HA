import sys
from PIL import Image
def stat(p, box=None):
    im = Image.open(p).convert('RGB')
    w,h = im.size
    if box: im = im.crop(box)
    L = im.convert('L'); d=sorted(L.getdata())
    n=len(d)
    px = list(im.getdata())
    return dict(size=(w,h), mean=round(sum(d)/n,1),
                p50=d[n//2], p95=d[int(n*.95)], p99=d[int(n*.99)], mx=d[-1],
                below40=round(100*sum(1 for v in d if v<40)/n),
                meanRGB=tuple(round(sum(c[i] for c in px)/n) for i in range(3)))
for p in sys.argv[1:]:
    print(p, stat(p))
