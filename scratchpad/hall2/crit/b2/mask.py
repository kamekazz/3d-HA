import sys
from PIL import Image
im = Image.open(sys.argv[1]).convert("RGB")
W,H = im.size
px = im.load()
def is_l(c):
    r,g,b=c; return r>100 and g<r*0.55 and b>r*0.38 and b<r*0.92
cols={}
for y in range(H):
    for x in range(W):
        if is_l(px[x,y]):
            cols.setdefault(x,[]).append(y)
if len(sys.argv)>2 and sys.argv[2]=="cols":
    for x in sorted(cols):
        ys=cols[x]; print(x, min(ys), max(ys), len(ys))
else:
    n=sum(len(v) for v in cols.values())
    print("lurid px", n, "x range", min(cols) if cols else None, max(cols) if cols else None)
    xs=sorted(cols)
    # print runs of x
    runs=[]; s=xs[0]; p=xs[0]
    for x in xs[1:]:
        if x>p+3: runs.append((s,p)); s=x
        p=x
    runs.append((s,p))
    for a,b in runs:
        ya=min(min(cols[x]) for x in range(a,b+1) if x in cols)
        yb=max(max(cols[x]) for x in range(a,b+1) if x in cols)
        print(f"  x {a}..{b}   y {ya}..{yb}")
