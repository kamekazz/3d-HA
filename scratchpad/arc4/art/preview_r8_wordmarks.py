"""ROUND 8 self-check -- the wordmark pass, art_g0 + art_g1.

    $PY scratchpad/arc4/art/preview_r8_wordmarks.py  ->  art/r8_wordmarks.png

One row per panel that round 8 touched.  Four columns:
  1  the owner's photograph of that panel, cropped and LANCZOS-upscaled
  2  round 7, exactly as it shipped (same atlas4 path, SIZE / SS / QUANT)
  3  round 8, exactly as it will ship
  4  round 8 at 5x, so composition can be judged apart from resolution
Column 2 is rendered by importing the round-7 backups, so the A/B is honest.
"""
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
for p in (HERE, os.path.join(ROOT, "scratchpad", "arc4")):
    if p not in sys.path:
        sys.path.insert(0, p)

PHOTO = os.path.join(ROOT, "docs", "photos-jpg", "Arcade Room %s.jpg")

# key, caption, photo, crop box
ROWS = [
    ("marvel-super-heroes.front", "MARVEL SUPER HEROES .front  "
     "(was CAPCOM + title x3)", "v3 4", (100, 688, 216, 884)),
    ("mortal-kombat.front", "MORTAL KOMBAT .front  (was MK + MORTAL KOMBAT)",
     "v3 4", (265, 640, 350, 850)),
    ("mortal-kombat.marquee", "MORTAL KOMBAT .marquee  (was cropped to "
     "'ORTAL KOMBAT' on the cabinet)", "v4 7", (244, 138, 328, 194)),
    ("tmnt-turtles-in-time.front", "TURTLES .front  (was TURTLES + "
     "title-size TURTLES on the riser)", "v3 4", (395, 660, 485, 880)),
    ("nba-jam.front", "NBA JAM .front  (was NBA JAM + NBA JAM)",
     "v3 4", (325, 640, 410, 860)),
    ("marvel-vs-capcom.front", "MARVEL VS CAPCOM .front  (riser lockup was "
     "edge to edge)", "v3 4", (180, 620, 275, 860)),
    ("pac-man.front", "PAC-MAN .front  (was a black plaque reading PAC-MAN)",
     "v4 6", (268, 180, 330, 285)),
    ("golden-tee-3d-golf.front", "GOLDEN TEE .front  (wordmark was at title "
     "size)", "v4 6", (370, 190, 436, 290)),
    ("nfl-blitz.front", "NFL BLITZ .front  (unchanged art; painted edge trim "
     "removed)", "v4 7", (34, 176, 120, 302)),
]


def panels(mod0, mod1):
    """Render every ROW key with art_g0/art_g1 bound to the given modules."""
    import importlib
    for m in ("atlas4", "art_g0", "art_g1"):
        if m in sys.modules:
            del sys.modules[m]
    sys.modules["art_g0"] = importlib.import_module(mod0)
    sys.modules["art_g1"] = importlib.import_module(mod1)
    atlas4 = importlib.import_module("atlas4")
    out = {}
    for key, _, _, _ in ROWS:
        w, h = atlas4.dims(key)
        rows = atlas4.render(key, w, h)
        im = Image.new("RGB", (w, h))
        im.putdata([tuple(int(c) for c in p) for r in rows for p in r])
        big = atlas4.render(key, w * 5, h * 5)
        bim = Image.new("RGB", (w * 5, h * 5))
        bim.putdata([tuple(int(c) for c in p) for r in big for p in r])
        out[key] = (im, bim)
    return out


R7 = panels("art_g0_r7bak", "art_g1_r7bak")
R8 = panels("art_g0", "art_g1")

CW, PAD, RH = 300, 14, 300
W = CW * 4 + PAD * 5
H = 64 + len(ROWS) * (RH + 46)
sheet = Image.new("RGB", (W, H), (18, 18, 22))
d = ImageDraw.Draw(sheet)
d.text((PAD, 10), "Arcade Room round 8 -- wordmarks (art_g0 + art_g1).  "
       "1 the owner's photograph.  2 ROUND 7 as shipped.  3 ROUND 8 as it "
       "will ship.  4 round 8 at 5x.", fill=(226, 228, 234))
d.text((PAD, 28), "2 and 3 go through atlas4's own render path at the panel's "
       "own shipping texel size, then nearest-upscaled -- what you see is "
       "every texel that reaches the cabinet.", fill=(150, 154, 164))
y = 50
for key, cap, ph, box in ROWS:
    src = Image.open(PHOTO % ph).crop(box)
    k = min(CW / float(src.width), RH / float(src.height))
    photo = src.resize((max(1, int(src.width * k)), max(1, int(src.height * k))),
                       Image.LANCZOS)
    cells = [photo]
    for (im, bim) in (R7[key], R8[key]):
        kk = min(CW / float(im.width), RH / float(im.height))
        cells.append(im.resize((int(im.width * kk), int(im.height * kk)),
                               Image.NEAREST))
    bim = R8[key][1]
    kk = min(CW / float(bim.width), RH / float(bim.height))
    cells.append(bim.resize((int(bim.width * kk), int(bim.height * kk)),
                            Image.LANCZOS))
    d.text((PAD, y), cap, fill=(255, 214, 120))
    d.text((PAD + CW + PAD, y + 14), "ROUND 7  %dx%d texels" % R7[key][0].size,
           fill=(240, 130, 130))
    d.text((PAD + (CW + PAD) * 2, y + 14),
           "ROUND 8  %dx%d texels" % R8[key][0].size, fill=(140, 220, 150))
    yy = y + 30
    for i, c in enumerate(cells):
        sheet.paste(c, (PAD + (CW + PAD) * i, yy))
    y = yy + RH + 16

out = os.path.join(HERE, "r8_wordmarks.png")
sheet.save(out)
print("wrote", out, sheet.size)
