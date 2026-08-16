"""Honest metering for round 4.

    mstat.py <img> <x0> <y0> <x1> <y1> [label]

Coordinates are FRACTIONS of width/height (like crop.py) so a box is easy to
transfer between a photo and a render of different sizes -- but every statistic
is computed at NATIVE resolution, never on an upsampled crop.

Reports, for one clean field:
  mean, sd                  -- the tone statistics
  d1                        -- mean |delta| between horizontally adjacent px
  d1/sd                     -- the scale-blindness check (fabric wants ~0.3)
  hf/tot                    -- energy above a 9 px gaussian, / total variance.
                               THIS is the "field vs marks" number: a few fat
                               marks put their variance at low frequency, a
                               dense fine net puts it high.
  R-B                       -- warm/cool
  n                         -- sample size in pixels
"""
import sys
import numpy as np
from PIL import Image


def gauss_blur(a, sigma):
    """Separable gaussian, reflect edges."""
    r = int(sigma * 3) | 1
    x = np.arange(-r, r + 1, dtype=np.float64)
    k = np.exp(-(x ** 2) / (2 * sigma * sigma))
    k /= k.sum()
    out = np.apply_along_axis(lambda v: np.convolve(
        np.pad(v, r, mode="reflect"), k, mode="valid"), 0, a)
    out = np.apply_along_axis(lambda v: np.convolve(
        np.pad(v, r, mode="reflect"), k, mode="valid"), 1, out)
    return out


def stats(path, x0, y0, x1, y1, label="", sigma=9.0):
    im = Image.open(path).convert("RGB")
    W, H = im.size
    box = (int(W * x0), int(H * y0), int(W * x1), int(H * y1))
    a = np.asarray(im.crop(box)).astype(np.float64)
    lum = a @ np.array([0.2126, 0.7152, 0.0722])
    sd = lum.std()
    d1 = np.abs(np.diff(lum, axis=1)).mean()
    lo = gauss_blur(lum, sigma)              # 9 px gaussian, as the critic used
    hf = lum - lo
    hftot = hf.var() / max(lum.var(), 1e-9)
    rb = a[..., 0].mean() - a[..., 2].mean()
    print(f"{label or path:28s} {im.size} box={box} n={lum.size:7d}  "
          f"mean={lum.mean():6.1f} sd={sd:5.1f}  d1={d1:5.2f} "
          f"d1/sd={d1/max(sd,1e-9):5.3f}  hf/tot={hftot:5.3f}  R-B={rb:+5.1f}")
    return dict(mean=lum.mean(), sd=sd, d1=d1, hftot=hftot, rb=rb, n=lum.size)


if __name__ == "__main__":
    p = sys.argv[1]
    stats(p, *(float(v) for v in sys.argv[2:6]),
          label=sys.argv[6] if len(sys.argv) > 6 else "")
