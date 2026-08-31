# -*- coding: utf-8 -*-
"""Round-7 deck preview sheet -> scratchpad/arc4/art/deck_g2_r7.png

Four rows, one per machine.  Left to right:

  1  THE PHOTOGRAPH, cropped to that machine's deck and upscaled (LANCZOS).
  2  the deck AS THE ATLAS WILL PACK IT -- rendered at atlas4's real isotropic
     size for that panel, re-quantised the way atlas4 does, then nearest-
     neighbour stretched to the panel's true aspect.  Nothing is flattered.
  3  the same, with every element of `DECKS[slug]` drawn on top at its TRUE
     radius in feet, so the button spec can be judged against the print it is
     supposed to land in.
  4  the art at 256 (what is authored), for reference only.

    $PY scratchpad/arc4/art/_r7_preview.py
"""
import math
import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..")))

from PIL import Image, ImageDraw            # noqa: E402

import art_g2                               # noqa: E402
for _n in ("art_g0", "art_g1", "art_g3"):   # atlas4 raises on missing owners
    _s = types.ModuleType(_n)
    _s.PANELS = {}
    sys.modules[_n] = _s
import atlas4                               # noqa: E402

PHOTO = os.path.join(ROOT, "docs", "photos-jpg")

SLUGS = ["legends-ultimate", "street-fighter-2-champion-edition",
         "time-crisis", "terminator-2"]
LABEL = {
    "legends-ultimate": "LEGENDS ULTIMATE   bw 2.95   ART_D",
    "street-fighter-2-champion-edition": "SFII CHAMPION EDITION   bw 2.42   ART_DK",
    "time-crisis": "TIME CRISIS   bw 2.52   ART_D",
    "terminator-2": "TERMINATOR 2   bw 2.28   ART_DK",
}
# the crop each deck was drawn from
CROP = {
    "legends-ultimate": ("Arcade Room v4 3.jpg", (395, 300, 510, 450)),
    "street-fighter-2-champion-edition":
        ("Arcade Room v4 4.jpg", (96, 162, 142, 188)),
    "time-crisis": ("Arcade Room v4 4.jpg", (30, 160, 130, 250)),
    "terminator-2": ("Arcade Room v4 5.jpg", (190, 166, 222, 186)),
}
H = 190                      # row height for the stretched panels


def packed(slug):
    """the deck exactly as atlas4 will pack it, and its (w, h) in texels."""
    key = "%s.deck" % slug
    w, h = atlas4.dims(key)
    rows = atlas4.render(key, w, h)
    im = Image.new("RGB", (w, h))
    im.putdata([c for r in rows for c in r])
    return im, w, h


# a2kit.DECK_MAT + the measured up-facing exposure of this scene.  Fitted off
# scratchpad/arc4/shots/r6_full_south.png against round 5's authored panels:
#   ART_DK (terminator-2, champion edition)  authored ~26 -> metered 80   x3.05
#   ART_D  (time-crisis, legends-ultimate)   authored ~110 -> metered 97  x0.88
# Linear approximation; it clips, and it is what makes a "dark navy" authored
# deck arrive as pale blue-grey.
XFER = {"legends-ultimate": 0.88, "time-crisis": 0.88,
        "street-fighter-2-champion-edition": 3.05, "terminator-2": 3.05}


def as_rendered(slug, im):
    f = XFER[slug]
    return im.point(lambda v: min(255, int(v * f + 0.5)))


def authored(slug, n=256):
    buf = [[(0, 0, 0)] * n for _ in range(n)]
    art_g2.PANELS["%s.deck" % slug](buf, 0, 0, n)
    im = Image.new("RGB", (n, n))
    im.putdata([c for r in buf for c in r])
    return im


def stretched(slug):
    im, w, h = packed(slug)
    a = art_g2.A[slug]["deck"]
    return im.resize((int(H * a), H), Image.NEAREST), w, h


def _hex(c):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def overlay(slug, base):
    """Draw DECKS[slug] on the stretched panel at true scale."""
    im = base.copy()
    d = ImageDraw.Draw(im, "RGBA")
    bw = art_g2._BW[slug]
    hw_paint = bw * 0.5 - 0.06                 # painted quad half-width, ft
    k = (bw * 0.5 - 0.10) / hw_paint
    fx = im.width / (2.0 * hw_paint)           # px per foot across
    fy = im.height / 0.92                      # px per foot back-to-front

    def at(u, v):
        return (im.width * 0.5 * (1.0 + k * u), im.height * v)

    for g in d and (art_g2.DECKS[slug].get("guns") or ()):
        cx, cy = at(g["u"], g["v"])
        L, W = g["len_ft"] * fy, 0.16 * fx
        a = math.radians(g["yaw_deg"])
        pts = []
        for (dx, dy) in ((-W, -L * 0.5), (W, -L * 0.5), (W, L * 0.5),
                         (-W, L * 0.5)):
            pts.append((cx + dx * math.cos(a) - dy * math.sin(a),
                        cy + dx * math.sin(a) + dy * math.cos(a)))
        d.polygon(pts, fill=_hex(g["body"]) + (235,),
                  outline=(255, 255, 255, 120))
    for s in (art_g2.DECKS[slug].get("sticks") or ()):
        cx, cy = at(s["u"], s["v"])
        r = s["dust_r_ft"]
        d.ellipse([cx - r * fx, cy - r * fy, cx + r * fx, cy + r * fy],
                  fill=_hex(s["dust_color"]) + (220,))
        r = s["top_r_ft"]
        d.ellipse([cx - r * fx, cy - r * fy, cx + r * fx, cy + r * fy],
                  fill=_hex(s["top_color"]) + (255,),
                  outline=(255, 255, 255, 150))
    tb = art_g2.DECKS[slug].get("trackball")
    if tb:
        cx, cy = at(tb["u"], tb["v"])
        r = tb["r_ft"]
        d.ellipse([cx - r * fx, cy - r * fy, cx + r * fx, cy + r * fy],
                  fill=_hex(tb["color"]) + (255,),
                  outline=_hex(tb["bezel_color"]) + (255,), width=2)
    for b in (art_g2.DECKS[slug].get("buttons") or ()):
        cx, cy = at(b["u"], b["v"])
        r = b["r_ft"]
        d.ellipse([cx - r * fx, cy - r * fy, cx + r * fx, cy + r * fy],
                  fill=_hex(b["color"]) + (255,),
                  outline=(0, 0, 0, 140))
    lip = art_g2.DECKS[slug].get("lip")
    if lip:
        d.rectangle([0, im.height - 4, im.width, im.height - 1],
                    fill=_hex(lip["color"]) + (255,))
    return im


def photo(slug):
    name, box = CROP[slug]
    im = Image.open(os.path.join(PHOTO, name)).convert("RGB").crop(box)
    z = H / float(im.height)
    return im.resize((max(1, int(im.width * z)), H), Image.LANCZOS)


def main():
    pad, lab = 16, 30
    rows = []
    for s in SLUGS:
        st, w, h = stretched(s)
        rows.append((s, [
            ("PHOTOGRAPH  %s %s" % CROP[s], photo(s)),
            ("PACKED  %dx%d texels, stretched to A=%.2f"
             % (w, h, art_g2.A[s]["deck"]), st),
            ("+ DECKS geometry at true ft", overlay(s, st)),
            ("AS RENDERED  x%.2f (%s)" % (XFER[s],
             "ART_D" if XFER[s] < 1 else "ART_DK"), as_rendered(s, st)),
        ]))
    W = pad + max(sum(i.width + pad for _, i in r) for _, r in rows)
    HH = sum(lab + H + 20 + pad for _ in rows) + pad + 46
    out = Image.new("RGB", (W, HH), (22, 22, 26))
    d = ImageDraw.Draw(out)
    d.text((pad, 12), "ARCADE ROOM -- SOUTH RUN CONTROL DECKS -- ROUND 7 "
           "(art_g2).  Column 2 is the real atlas resolution: no upscaling "
           "flattery.", fill=(235, 237, 242))
    d.text((pad, 26), "Deck packs at SIZE=52 isotropic -> ~32-37 texels/ft. "
           "A 1.1in button is 3.1 texels, which is why the buttons are "
           "GEOMETRY and the PRINTED COLLARS are the artwork.",
           fill=(150, 154, 162))
    y = 46 + pad
    for s, cells in rows:
        d.text((pad, y - 1), LABEL[s], fill=(232, 234, 240))
        y += lab
        x = pad
        for cap, im in cells:
            out.paste(im, (x, y))
            d.rectangle([x - 1, y - 1, x + im.width, y + im.height],
                        outline=(92, 96, 106))
            d.text((x + 2, y + im.height + 4), cap, fill=(150, 154, 162))
            x += im.width + pad
        y += H + 20 + pad
    p = os.path.join(HERE, "deck_g2_r7.png")
    out.save(p)
    print("wrote", p, out.size)


if __name__ == "__main__":
    main()
