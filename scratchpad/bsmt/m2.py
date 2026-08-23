"""Meter named boxes in an image at NATIVE resolution: mean, sd, mean|d1|.

  python m2.py <image> <label>=x0,y0,x1,y1 ...      [--overlay out.png]

sd is scale-blind, so |d1| (mean absolute difference between horizontally
adjacent pixels) is reported beside it, plus the ratio |d1|/sd.
"""
import sys
import numpy as np
from PIL import Image, ImageDraw


def meter(a, box):
    x0, y0, x1, y1 = box
    p = a[y0:y1, x0:x1]
    lum = 0.2126 * p[:, :, 0] + 0.7152 * p[:, :, 1] + 0.0722 * p[:, :, 2]
    d1 = np.abs(np.diff(lum, axis=1)).mean()
    d1v = np.abs(np.diff(lum, axis=0)).mean()
    sd = lum.std()
    return dict(n=lum.size, mean=lum.mean(), sd=sd, d1=(d1 + d1v) / 2,
                ratio=((d1 + d1v) / 2) / sd if sd > 1e-6 else 0.0,
                rgb=tuple(round(p[:, :, k].mean(), 1) for k in range(3)))


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    ov = None
    for a in sys.argv[1:]:
        if a.startswith("--overlay="):
            ov = a.split("=", 1)[1]
    img = Image.open(args[0]).convert("RGB")
    arr = np.asarray(img).astype(float)
    print(f"{args[0]}  {img.size}")
    d = ImageDraw.Draw(img)
    for spec in args[1:]:
        label, nums = spec.split("=")
        box = tuple(int(v) for v in nums.split(","))
        r = meter(arr, box)
        print(f"  {label:22s} n={r['n']:7d}  mean={r['mean']:6.1f}  "
              f"sd={r['sd']:5.2f}  |d1|={r['d1']:5.2f}  |d1|/sd={r['ratio']:.3f}  "
              f"rgb={r['rgb']}")
        d.rectangle(box, outline=(255, 0, 0), width=3)
        d.text((box[0] + 4, box[1] + 4), label, fill=(255, 0, 0))
    if ov:
        img.save(ov)
        print("  overlay ->", ov)
