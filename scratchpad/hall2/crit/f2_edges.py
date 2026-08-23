"""Find plank long-edges along a scanline of a photo (they are the sharp
local minima/maxima of a lengthwise-smoothed luminance profile)."""
import sys
import numpy as np
from PIL import Image

p, y0, y1, x0, x1 = sys.argv[1], *[int(v) for v in sys.argv[2:6]]
a = np.asarray(Image.open(p).convert("RGB")).astype(float)
L = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
prof = L[y0:y1, x0:x1].mean(axis=0)
# high-pass: subtract a wide box blur
k = 25
pad = np.pad(prof, k, mode="edge")
blur = np.convolve(pad, np.ones(2 * k + 1) / (2 * k + 1), mode="same")[k:-k]
hp = prof - blur
print("scanline y", y0, y1, "x", x0, x1, " mean", round(prof.mean(), 1))
print(" ".join(f"{x0+i}:{v:+.1f}" for i, v in enumerate(np.round(hp, 1))))
