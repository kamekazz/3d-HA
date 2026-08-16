"""Round-5 meter: reports sd AND fine-scale gradient, at NATIVE resolution.

The round-4 report's numbers were not wrong arithmetic -- they were the wrong
statistic.  sd is scale-blind: a few big soft patches and real fabric grain can
meter the same sd.  What separates them is the mean absolute difference between
ADJACENT pixels (|d1|), and the normalised ratio |d1|/sd.

    photo upholstery  |d1| 11.84   |d1|/sd 0.324-0.394
    round-4 render    |d1|  1.62   |d1|/sd 0.070

Usage:
    python m5.py <img> x0 y0 x1 y1 [label] ...

NEVER pass an upsampled crop: resampling interpolates neighbouring pixels,
which deflates |d1| and inflates sd.  One round-4 rug figure (sd 20.5) was
really 10.9 for exactly that reason.  This script refuses to guess -- it meters
the file you give it, so give it the native render.
"""
import sys
import numpy as np
from PIL import Image, ImageDraw

W709 = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)


def stats(lum):
    """sd, mean|d1| over both axes, and the normalised ratio."""
    sd = float(lum.std())
    dh = np.abs(np.diff(lum, axis=1)).mean() if lum.shape[1] > 1 else 0.0
    dv = np.abs(np.diff(lum, axis=0)).mean() if lum.shape[0] > 1 else 0.0
    d1 = float((dh + dv) / 2.0)
    return sd, d1, (d1 / sd if sd > 1e-6 else 0.0)


def meter(path, boxes, outline=True):
    im = Image.open(path).convert("RGB")
    a = np.asarray(im).astype(np.float32)
    dbg = im.copy()
    d = ImageDraw.Draw(dbg)
    rows = []
    for (x0, y0, x1, y1, label) in boxes:
        p = a[y0:y1, x0:x1]
        if p.size == 0:
            print("%-20s EMPTY BOX" % label)
            continue
        lum = p @ W709
        sd, d1, ratio = stats(lum)
        rows.append((label, lum.size, lum.mean(), sd, d1, ratio,
                     lum.min(), lum.max()))
        print("%-20s n=%-7d mean=%6.1f sd=%5.1f  |d1|=%5.2f  |d1|/sd=%.3f"
              "  rgb=(%3.0f,%3.0f,%3.0f)  min=%3.0f max=%3.0f"
              % (label, lum.size, lum.mean(), sd, d1, ratio,
                 p[..., 0].mean(), p[..., 1].mean(), p[..., 2].mean(),
                 lum.min(), lum.max()))
        if outline:
            d.rectangle([x0, y0, x1, y1], outline=(255, 0, 0), width=2)
            d.text((x0 + 3, y0 + 3), label, fill=(255, 0, 0))
    if outline:
        dbg.save(path.rsplit(".", 1)[0] + "_boxes.png")
    return rows


if __name__ == "__main__":
    path = sys.argv[1]
    args = sys.argv[2:]
    boxes = []
    i = 0
    while i < len(args):
        x0, y0, x1, y1 = (int(v) for v in args[i:i + 4])
        lab = args[i + 4] if i + 4 < len(args) and not args[i + 4].lstrip("-").isdigit() else "?"
        i += 5 if lab != "?" else 4
        boxes.append((x0, y0, x1, y1, lab))
    im = Image.open(path)
    print("# %s  native size %dx%d" % (path.rsplit("\\", 1)[-1], im.width, im.height))
    meter(path, boxes)
