"""Room 1 metering: mean, detrended sd, mean|dh|, block/pixel sd ratio,
vertical plane-fit slope per 100 px.  Works on any image + box list."""
import sys, json
import numpy as np
from PIL import Image

def lum(p):
    a = np.asarray(Image.open(p).convert("RGB")).astype(float)
    return 0.2126*a[:,:,0] + 0.7152*a[:,:,1] + 0.0722*a[:,:,2]

def stats(L, box):
    x0,y0,x1,y1 = box
    c = L[y0:y1, x0:x1]
    h, w = c.shape
    yy, xx = np.mgrid[0:h, 0:w]
    A = np.stack([np.ones(c.size), xx.ravel(), yy.ravel()], 1)
    coef, *_ = np.linalg.lstsq(A, c.ravel(), rcond=None)
    fit = (A @ coef).reshape(h, w)
    det = c - fit
    dh = np.abs(np.diff(c, axis=1)).mean()
    # 8x8 block means sd vs pixel sd (on detrended)
    bh, bw = h//8, w//8
    blk = det[:bh*8, :bw*8].reshape(bh,8,bw,8).mean(axis=(1,3)) if bh and bw else det
    return dict(mean=round(float(c.mean()),1), sd=round(float(c.std()),2),
                det_sd=round(float(det.std()),2), dh=round(float(dh),2),
                blk_ratio=round(float(blk.std()/max(det.std(),1e-6)),2),
                slope_y100=round(float(coef[2])*100,1),
                slope_x100=round(float(coef[1])*100,1),
                px=f"{w}x{h}")

if __name__ == "__main__":
    spec = json.load(open(sys.argv[1]))
    for img, boxes in spec.items():
        L = lum(img)
        print("==", img, L.shape)
        for name, b in boxes.items():
            print(f"   {name:26s} {stats(L,b)}")
