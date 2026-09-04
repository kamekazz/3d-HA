"""Diff a before/after pair: how many pixels moved, and what the CHANGED pixels
(i.e. the pane) metered before vs after."""
import sys, os
from PIL import Image
import numpy as np
for pre in sys.argv[1:]:
    a = np.asarray(Image.open(pre + "_before.png").convert("RGB")).astype(int)
    b = np.asarray(Image.open(pre + "_after.png").convert("RGB")).astype(int)
    d = np.abs(a - b).max(axis=2)
    n = int((d > 2).sum())
    tag = os.path.basename(pre)
    if n == 0:
        print("%-22s IDENTICAL  (max channel delta %d, %d px differ at all)"
              % (tag, int(np.abs(a-b).max()), int((np.abs(a-b).max(axis=2) > 0).sum())))
        continue
    m = d > 2
    lum = lambda im: (0.2126*im[...,0] + 0.7152*im[...,1] + 0.0722*im[...,2])
    la, lb = lum(a)[m], lum(b)[m]
    print("%-22s changed %d px (%.2f%% of frame)  L before mean=%.1f p95=%.0f max=%.0f "
          "-> after mean=%.1f p95=%.0f max=%.0f"
          % (tag, n, 100.0*n/d.size, la.mean(), np.percentile(la,95), la.max(),
             lb.mean(), np.percentile(lb,95), lb.max()))
    # sRGB of the brightest changed pixel, before and after
    i = int(np.argmax(la))
    ys, xs = np.nonzero(m)
    y, x = ys[i], xs[i]
    print("%-22s   brightest changed px @(%d,%d): before sRGB %s -> after %s"
          % ("", x, y, tuple(a[y,x]), tuple(b[y,x])))
