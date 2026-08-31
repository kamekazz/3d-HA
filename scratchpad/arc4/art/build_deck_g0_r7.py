# -*- coding: utf-8 -*-
"""Round-7 deck preview sheet.

For each of art_g0's four machines it renders the `.deck` panel three ways:

    BIG      the paint function at 8x atlas resolution -- what is drawn
    SHIPPED  atlas4.render() at the EXACT texel count that ships (80x34 etc),
             then nearest-neighbour up, so nothing flatters it
    PHOTO    the matching crop from the owner's photographs

Writes scratchpad/arc4/art/deck_g0_r7.png.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
for p in (os.path.join(ROOT, "tools"), os.path.join(ROOT, "scratchpad", "bsmt"),
          os.path.join(ROOT, "scratchpad", "arc4"), HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

from PIL import Image, ImageDraw                                # noqa: E402
import ar2                                                     # noqa: E402,F401
import atlas4                                                  # noqa: E402

PH = os.path.join(ROOT, "docs", "photos-jpg")
MACH = [
    ("pac-man", "Arcade Room v4 3.jpg", (72, 178, 126, 206)),
    ("nba-jam", "Arcade Room v4 7.jpg", (288, 248, 370, 320)),
    ("tmnt-turtles-in-time", "Arcade Room v4 7.jpg", (333, 292, 468, 372)),
    ("golden-tee-3d-golf", "Arcade Room v4 6.jpg", (362, 200, 438, 228)),
]

CW, PAD = 1180, 16
rows = []
for slug, photo, box in MACH:
    key = slug + ".deck"
    w, h = atlas4.dims(key)

    def img(ww, hh):
        px = atlas4.render(key, ww, hh)
        im = Image.new("RGB", (ww, hh))
        im.putdata([tuple(c) for row in px for c in row])
        return im

    ship = img(w, h)
    big = img(w * 8, h * 8)
    k = CW // w
    ship_up = ship.resize((w * k, h * k), Image.NEAREST)
    big_up = big.resize((CW, int(CW * h / float(w))), Image.LANCZOS)
    ph = Image.open(os.path.join(PH, photo)).convert("RGB").crop(box)
    ph = ph.resize((CW, int(CW * ph.height / float(ph.width))), Image.LANCZOS)
    rows.append((slug, "%dx%d texels" % (w, h), big_up, ship_up, ph))

H = PAD
for _, _, b, s, p in rows:
    H += 22 + b.height + 8 + s.height + 8 + p.height + PAD + 14
sheet = Image.new("RGB", (CW + 2 * PAD, H), (18, 18, 22))
d = ImageDraw.Draw(sheet)
y = PAD
for slug, dim, b, s, p in rows:
    d.text((PAD, y), "%s.deck   drawn / SHIPPED %s / photo" % (slug, dim),
           fill=(235, 235, 240))
    y += 22
    for im in (b, s, p):
        sheet.paste(im, (PAD, y))
        y += im.height + 8
    y += PAD + 6
    d.line([(PAD, y - 10), (CW + PAD, y - 10)], fill=(70, 70, 80))
out = os.path.join(HERE, "deck_g0_r7.png")
sheet.save(out)
print("wrote", out, sheet.size)
