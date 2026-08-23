"""Wall metering helpers for the room-17 wall-skin build.

Everything is reported on luma (Rec.601) so a value is directly comparable with
the 0-255 numbers the rest of this scratchpad quotes.

Renders are 900x1200, the photos are 450x600 -- exactly 2x.  `mean|d1|` is
scale-dependent, so a render is DOWNSAMPLED to the photo's 450x600 before its
fine-gradient number is taken; both numbers are reported.
"""
import os
import sys

from PIL import Image
import numpy as np

PHOTOS = r"C:\Users\Manuel\Desktop\Pro\3d HA\docs\v2 Hallway-jpg"
SHOTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shots")


def luma(im):
    a = np.asarray(im.convert("RGB"), dtype=np.float64)
    return 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]


def load(path, to450=False):
    im = Image.open(path)
    if to450 and im.size != (450, 600):
        im = im.resize((450, 600), Image.LANCZOS)
    return luma(im)


def stats(L, box):
    x0, y0, x1, y1 = box
    p = L[y0:y1, x0:x1]
    if p.size < 16:
        return None
    d = np.concatenate([np.abs(np.diff(p, axis=0)).ravel(),
                        np.abs(np.diff(p, axis=1)).ravel()])
    return dict(n=p.size, mean=p.mean(), sd=p.std(), d1=d.mean(),
                ratio=(d.mean() / p.std() if p.std() > 1e-9 else 0.0),
                lo=np.percentile(p, 2), hi=np.percentile(p, 98))


def show(tag, L, boxes):
    for name, b in boxes.items():
        s = stats(L, b)
        if not s:
            print(f"  {tag:16s} {name:22s} -- too small")
            continue
        print(f"  {tag:16s} {name:22s} n={s['n']:6d} mean={s['mean']:6.1f} "
              f"sd={s['sd']:5.2f} |d1|={s['d1']:5.2f} r={s['ratio']:5.3f} "
              f"p2-p98={s['lo']:5.1f}-{s['hi']:5.1f}")


def ramp(L, x0, x1, y0, y1, n=8):
    """Vertical tone ramp down a wall column: n horizontal bands."""
    out = []
    for i in range(n):
        a = y0 + (y1 - y0) * i // n
        b = y0 + (y1 - y0) * (i + 1) // n
        out.append(L[a:b, x0:x1].mean())
    return out
