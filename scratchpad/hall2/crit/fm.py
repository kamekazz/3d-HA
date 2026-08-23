"""Floor metering: sample a rect from an image, report mean RGB/L, sd, mean|d1|."""
import sys, os
from PIL import Image
import numpy as np

def stats(path, x0, y0, x1, y1, label=""):
    im = Image.open(path).convert("RGB")
    W, H = im.size
    # accept fractional coords
    if max(x0, y0, x1, y1) <= 1.0:
        x0, x1 = int(x0 * W), int(x1 * W)
        y0, y1 = int(y0 * H), int(y1 * H)
    a = np.asarray(im.crop((x0, y0, x1, y1))).astype(np.float64)
    L = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
    d1 = (np.abs(np.diff(L, axis=1)).mean() + np.abs(np.diff(L, axis=0)).mean()) / 2
    print(f"{label:28s} {os.path.basename(path):34s} [{x0},{y0},{x1},{y1}] {a.shape[1]}x{a.shape[0]}")
    print(f"   RGB {a[...,0].mean():6.1f} {a[...,1].mean():6.1f} {a[...,2].mean():6.1f}"
          f"   L {L.mean():6.1f}  sd {L.std():5.2f}  |d1| {d1:5.2f}  |d1|/sd {d1/max(L.std(),1e-6):5.3f}")
    return dict(L=L.mean(), sd=L.std(), d1=d1,
                R=a[...,0].mean(), G=a[...,1].mean(), B=a[...,2].mean())

if __name__ == "__main__":
    p = sys.argv[1]
    c = [float(v) for v in sys.argv[2:6]]
    stats(p, *c, label=sys.argv[6] if len(sys.argv) > 6 else "")
