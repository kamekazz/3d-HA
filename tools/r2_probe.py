"""Wall-band luminance probe for the light gauntlet, round 2.

  python r2_probe.py grid  <img>                      -- coarse 12x9 luminance grid
  python r2_probe.py band  <img> y0 y1 [x0 x1] [n]    -- horizontal band, n buckets
                                                          (fractions of w/h)

Luminance is PIL's L (0.299R+0.587G+0.114B), 0-255.
"""
import sys
from PIL import Image


def load(p):
    return Image.open(p).convert("L")


def grid(path, nx=12, ny=9):
    im = load(path)
    w, h = im.size
    print(path, im.size)
    print("      " + "".join("%6.2f" % ((i + .5) / nx) for i in range(nx)))
    for j in range(ny):
        row = []
        for i in range(nx):
            b = im.crop((int(w * i / nx), int(h * j / ny),
                         int(w * (i + 1) / nx), int(h * (j + 1) / ny)))
            d = list(b.getdata())
            row.append(sum(d) / len(d))
        print("%4.2f  " % ((j + .5) / ny) + "".join("%6.0f" % v for v in row))


def band(path, y0, y1, x0=0.0, x1=1.0, n=7):
    im = load(path)
    w, h = im.size
    out = []
    for i in range(n):
        a = x0 + (x1 - x0) * i / n
        b = x0 + (x1 - x0) * (i + 1) / n
        c = im.crop((int(w * a), int(h * y0), int(w * b), int(h * y1)))
        d = list(c.getdata())
        out.append(sum(d) / len(d))
    print("%-60s %s" % (path.split("/")[-1],
                        " ".join("%.0f" % v for v in out)))
    return out


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "grid":
        grid(sys.argv[2])
    else:
        a = sys.argv[2:]
        band(a[0], float(a[1]), float(a[2]),
             float(a[3]) if len(a) > 3 else 0.0,
             float(a[4]) if len(a) > 4 else 1.0,
             int(a[5]) if len(a) > 5 else 7)
