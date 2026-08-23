"""Wall-tone profiler.  Prints, for a list of vertical strips, the luminance
profile down the strip, plus sd / mean|d1| for a named clean patch.

Photos are 450x600; renders are 900x1200.  mean|d1| is scale-dependent, so a
render is downsampled 2x before measuring so both are metered at the SAME
pixels-per-foot.  --half does that.
"""
import sys
import numpy as np
from PIL import Image

LUM = np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)


def load(path, half=False):
    im = Image.open(path).convert("RGB")
    if half:
        im = im.resize((im.width // 2, im.height // 2), Image.BOX)
    return np.asarray(im).astype(np.float32)


def prof(a, x0, x1, y0, y1, n=8, label=""):
    g = a[:, :, :] @ LUM
    ys = np.linspace(y0, y1, n + 1)
    out = []
    for k in range(n):
        s = g[int(ys[k]):int(ys[k + 1]), x0:x1]
        out.append(s.mean())
    print(f"  {label:28s} " + " ".join(f"{v:5.1f}" for v in out)
          + f"   span={out[0]-out[-1]:+6.1f}")
    return out


def patch(a, x0, y0, x1, y1, label=""):
    s = a[y0:y1, x0:x1]
    g = s @ LUM
    d1 = (np.abs(np.diff(g, axis=1)).mean() + np.abs(np.diff(g, axis=0)).mean()) / 2
    print(f"  {label:28s} mean={g.mean():6.2f}  sd={g.std():5.2f}  "
          f"|d1|={d1:5.2f}  |d1|/sd={d1/max(g.std(),1e-6):5.3f}  "
          f"rgb=({s[:,:,0].mean():.0f},{s[:,:,1].mean():.0f},{s[:,:,2].mean():.0f})  "
          f"n={(y1-y0)*(x1-x0)}")
    return g.mean(), g.std(), d1
