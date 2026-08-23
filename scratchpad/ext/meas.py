"""Metering + cropping for the exterior rounds. Reports mean RGB, sd, and the
mean |adjacent-pixel delta| on both axes (the scale-blind lesson)."""
import sys, os
from PIL import Image
import numpy as np

def stats(path, box, label=""):
    im = Image.open(path).convert("RGB")
    a = np.asarray(im.crop(box)).astype(np.float64)
    lum = a @ np.array([0.299, 0.587, 0.114])
    dx = np.abs(np.diff(lum, axis=1)).mean()
    dy = np.abs(np.diff(lum, axis=0)).mean()
    m = a.reshape(-1, 3).mean(0)
    print("%-28s n=%5d  RGB %5.1f,%5.1f,%5.1f  G-R %+5.1f  lum %6.2f  sd %5.2f  |dx| %5.2f  |dy| %5.2f"
          % (label or os.path.basename(path), lum.size, m[0], m[1], m[2], m[1]-m[0],
             lum.mean(), lum.std(), dx, dy))
    return dict(rgb=m, lum=lum.mean(), sd=lum.std(), dx=dx, dy=dy)

def crop(path, box, out, scale=1):
    im = Image.open(path).convert("RGB").crop(box)
    if scale != 1:
        im = im.resize((im.width*scale, im.height*scale), Image.NEAREST)
    im.save(out)
    print("crop ->", out, im.size)

if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "stats":
        stats(sys.argv[2], tuple(int(v) for v in sys.argv[3].split(",")),
              sys.argv[4] if len(sys.argv) > 4 else "")
    elif cmd == "crop":
        crop(sys.argv[2], tuple(int(v) for v in sys.argv[3].split(",")), sys.argv[4],
             int(sys.argv[5]) if len(sys.argv) > 5 else 1)
