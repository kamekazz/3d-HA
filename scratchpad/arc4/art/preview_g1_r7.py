"""Round-7 self-check sheet: the four rewritten control decks at SHIPPING
resolution, beside the owner's photographs of the same four decks.

    $PY scratchpad/arc4/art/preview_g1_r7.py   ->  art/deck_g1_r7.png

Three columns per machine:
  1  the photo crop the deck was drawn from, upscaled LANCZOS
  2  the panel EXACTLY as atlas4 will ship it (isotropic SIZE 52, SS 2 box
     average, QUANT 20), then nearest-upscaled so a texel is visible
  3  the same drawing at 6x the shipping size, so composition can be judged
     apart from resolution
and a fourth strip showing the deck at the RENDERED size it occupies in the
judged `full_east` / `full_north` frame, which is the size a critic sees.
"""
import io
import os
import sys

from PIL import Image, ImageDraw

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
for _p in (_HERE, os.path.join(_ROOT, "scratchpad", "arc4")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import art_g1                                                  # noqa: E402

PHOTO = os.path.join(_ROOT, "docs", "photos-jpg", "Arcade Room %s.jpg")
SS, QUANT, SIZE = 2, 20, 52

# slug, title, photo, crop box, px/ft in the judged frame, real deck width ft
ROWS = [
    ("marvel-super-heroes", "MARVEL SUPER HEROES  (east 1)",
     "v4 6", (430, 234, 492, 276), 45.3, 1.98),
    ("marvel-vs-capcom", "MARVEL VS CAPCOM  (east 2)",
     "v4 6", (452, 268, 545, 362), 43.0, 2.30),
    ("mortal-kombat", "MORTAL KOMBAT  (east 3)",
     "v4 6", (470, 352, 600, 450), 39.5, 2.04),
    ("nfl-blitz", "NFL BLITZ  (north 3)",
     "v4 6", (308, 185, 378, 222), 41.0, 2.06),
]


def _q(v):
    v = int(v / QUANT + 0.5) * QUANT
    return 0 if v < 0 else (255 if v > 255 else v)


def ship(slug, size=SIZE):
    """The panel exactly as atlas4 will pack it."""
    key = slug + ".deck"
    fn = art_g1.PANELS[key]
    a = art_g1.ASPECT[key] ** 0.5
    w, h = max(8, int(size * a + 0.5)), max(8, int(size / a + 0.5))
    bw, bh = w * SS, h * SS
    buf = [[(0, 0, 0)] * bw for _ in range(bh)]
    fn.rect(buf, 0, 0, bw, bh)
    im = Image.new("RGB", (bw, bh))
    im.putdata([c for row in buf for c in row])
    im = im.resize((w, h), Image.BOX)
    im.putdata([tuple(_q(c) for c in p) for p in im.getdata()])
    return im


def big(slug, size):
    key = slug + ".deck"
    fn = art_g1.PANELS[key]
    a = art_g1.ASPECT[key] ** 0.5
    w, h = int(size * a + 0.5), int(size / a + 0.5)
    buf = [[(0, 0, 0)] * w for _ in range(h)]
    fn.rect(buf, 0, 0, w, h)
    im = Image.new("RGB", (w, h))
    im.putdata([c for row in buf for c in row])
    return im


CW, PAD = 470, 14
rows = []
for slug, title, ph, box, pxft, wft in ROWS:
    src = Image.open(PHOTO % ph).crop(box)
    k = min(CW / src.width, 300.0 / src.height)
    photo = src.resize((int(src.width * k), int(src.height * k)),
                       Image.LANCZOS)
    sh = ship(slug)
    k2 = CW / sh.width
    shb = sh.resize((CW, max(1, int(sh.height * k2))), Image.NEAREST)
    hi = big(slug, 320)
    hib = hi.resize((CW, int(hi.height * CW / hi.width)), Image.LANCZOS)
    # the deck at the size the judged frame actually renders it
    rw = int(wft * pxft)
    rn = sh.resize((rw, max(1, int(sh.height * rw / sh.width))),
                   Image.LANCZOS)
    rows.append((title, photo, shb, hib, rn, sh.size, rw))

H = sum(max(r[1].height, r[2].height, r[3].height) + 96 for r in rows) + 60
W = CW * 3 + PAD * 4
sheet = Image.new("RGB", (W, H), (18, 18, 22))
d = ImageDraw.Draw(sheet)
d.text((PAD, 10), "art_g1 round 7 -- control decks.  left: the owner's "
       "photograph.  centre: the panel AS SHIPPED (atlas4 SIZE 52, SS2, "
       "QUANT 20), nearest-upscaled.  right: the drawing at 6x.",
       fill=(224, 226, 232))
d.text((PAD, 26), "bottom strip of each row = the deck at the pixel size the "
       "judged full_east / full_north frame renders it at.",
       fill=(150, 154, 164))
y = 46
for (title, photo, shb, hib, rn, sz, rw) in rows:
    d.text((PAD, y), title, fill=(255, 214, 120))
    d.text((PAD + CW + PAD, y), "SHIPPED  %d x %d texels" % sz,
           fill=(160, 200, 255))
    d.text((PAD + (CW + PAD) * 2, y), "6x, composition only",
           fill=(160, 200, 255))
    y += 16
    sheet.paste(photo, (PAD, y))
    sheet.paste(shb, (PAD + CW + PAD, y))
    sheet.paste(hib, (PAD + (CW + PAD) * 2, y))
    yb = y + max(photo.height, shb.height, hib.height) + 8
    d.text((PAD, yb + 2), "at judged distance, %d px wide:" % rw,
           fill=(150, 154, 164))
    sheet.paste(rn, (PAD + 210, yb))
    y = yb + max(rn.height, 16) + 34

out = os.path.join(_HERE, "deck_g1_r7.png")
sheet.save(out)
print("wrote", out, sheet.size)
