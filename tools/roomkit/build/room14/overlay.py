"""Draw projected room-local points/edges over a render or the photo, to check
the camera model and to measure. Usage:

  python overlay.py render.png out.png render      # points in RENDER pixel space
  python overlay.py photo.jpg  out.png photo       # points in PHOTO pixel space
"""
import sys
from PIL import Image, ImageDraw
import proj

EDGES = [
    # room box wireframe (local ft)
    ((0, 0, 0), (15, 0, 0)), ((0, 8, 0), (15, 8, 0)),
    ((0, 0, 0), (0, 8, 0)), ((15, 0, 0), (15, 8, 0)),
    ((0, 0, 0), (0, 0, 16)), ((15, 0, 0), (15, 0, 16)),
    ((0, 8, 0), (0, 8, 16)), ((15, 8, 0), (15, 8, 16)),
    # ridge
    ((7.5, 14.5, 0), (7.5, 14.5, 16)),
    ((0, 8, 0), (7.5, 14.5, 0)), ((15, 8, 0), (7.5, 14.5, 0)),
]


def draw(img, edges, mode, color=(255, 0, 0), width=2):
    d = ImageDraw.Draw(img)
    f = proj.projp if mode == "photo" else proj.proj
    for a, b in edges:
        pa, pb = f(a), f(b)
        if pa[2] < 0.2 or pb[2] < 0.2:
            continue
        d.line([pa[0], pa[1], pb[0], pb[1]], fill=color, width=width)
    return img


if __name__ == "__main__":
    src, out, mode = sys.argv[1], sys.argv[2], sys.argv[3]
    im = Image.open(src).convert("RGB")
    draw(im, EDGES, mode)
    im.save(out)
    print(out, im.size)
