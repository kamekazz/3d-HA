"""Zoomed, gridded crop of a photo or render, for reading pixel coordinates."""
import sys, os
from PIL import Image, ImageDraw

PH = r"C:\Users\Manuel\Desktop\Pro\3d HA\docs\photos-jpg"
OUT = os.path.dirname(os.path.abspath(__file__))


def crop(src, x0, y0, x1, y1, zoom=3, grid=20, out="crop.png"):
    p = src if os.path.isabs(src) else os.path.join(PH, src)
    im = Image.open(p).convert("RGB")
    c = im.crop((x0, y0, x1, y1)).resize(((x1 - x0) * zoom, (y1 - y0) * zoom),
                                         Image.LANCZOS)
    d = ImageDraw.Draw(c)
    for x in range(x0 - x0 % grid, x1 + 1, grid):
        u = (x - x0) * zoom
        d.line([u, 0, u, c.height], fill=(255, 0, 255), width=1)
        d.text((u + 2, 2), str(x), fill=(255, 0, 255))
    for y in range(y0 - y0 % grid, y1 + 1, grid):
        v = (y - y0) * zoom
        d.line([0, v, c.width, v], fill=(0, 255, 255), width=1)
        d.text((2, v + 2), str(y), fill=(0, 255, 255))
    q = os.path.join(OUT, out)
    c.save(q)
    print(q, c.size)


if __name__ == "__main__":
    a = sys.argv[1:]
    crop(a[0], int(a[1]), int(a[2]), int(a[3]), int(a[4]),
         zoom=int(a[5]) if len(a) > 5 else 3,
         grid=int(a[6]) if len(a) > 6 else 20,
         out=a[7] if len(a) > 7 else "crop.png")
