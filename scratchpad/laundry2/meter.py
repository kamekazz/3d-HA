"""Meter named crops of an image: mean, sd and mean|d1| at NATIVE resolution.

sd is scale-blind (ROOM-BRIEF), so every row reports the fine-scale gradient
too -- mean absolute difference between horizontally adjacent pixels, and the
ratio |d1|/sd, which is what separates a real woven surface from flat paint.
"""
import sys
from PIL import Image


def stats(im, box):
    c = im.crop(box).convert("L")
    px = list(c.getdata())
    w, h = c.size
    n = len(px)
    mean = sum(px) / n
    sd = (sum((p - mean) ** 2 for p in px) / n) ** 0.5
    d1, cnt = 0.0, 0
    for y in range(h):
        row = px[y * w:(y + 1) * w]
        for x in range(w - 1):
            d1 += abs(row[x + 1] - row[x])
            cnt += 1
    d1 /= max(1, cnt)
    return mean, sd, d1, n


def run(path, regions):
    im = Image.open(path).convert("RGB")
    print(path, im.size)
    for name, box in regions:
        m, sd, d1, n = stats(im, box)
        print("  %-18s mean %6.1f  sd %5.2f  |d1| %5.2f  |d1|/sd %5.3f  n=%d"
              % (name, m, sd, d1, d1 / sd if sd > 0.01 else 0, n))


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "both"
    PHOTO = ("../../docs/photos-jpg/"
             "Laundry room and garage door right next to it.jpg")
    photo_regions = [
        ("basket L", (192, 678, 254, 728)),
        ("basket R", (322, 678, 374, 722)),
        ("dryer box", (402, 762, 468, 802)),
        ("wall band", (250, 630, 330, 670)),
        ("wall upper", (560, 470, 700, 640)),
        ("washer front", (95, 935, 295, 1115)),
        ("dryer front", (660, 1085, 730, 1155)),
        ("ledge top", (130, 726, 300, 742)),
        ("cabinet door", (60, 400, 160, 600)),
    ]
    render_regions = [
        ("basket L", (392, 470, 520, 560)),
        ("basket R", (610, 462, 740, 556)),
        ("dryer box", (580, 660, 730, 760)),
        ("wall band", (250, 372, 430, 420)),
        ("wall upper", (760, 330, 850, 400)),
        ("washer front", (110, 880, 400, 1060)),
        ("dryer front", (600, 900, 860, 960)),
        ("ledge top", (200, 562, 340, 588)),
        ("cabinet door", (180, 60, 330, 280)),
    ]
    if which in ("photo", "both"):
        run(PHOTO, photo_regions)
    if which in ("render", "both"):
        run(sys.argv[2] if len(sys.argv) > 2 else "r2_ref.png", render_regions)
