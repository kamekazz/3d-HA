# -*- coding: utf-8 -*-
"""ROUND 8 preview sheet -> scratchpad/arc4/art/r8_south-decks.png

Two blocks.

  BLOCK A -- the four south control decks, one row each:
      1  the PHOTOGRAPH, cropped to that deck and upscaled (LANCZOS)
      2  ROUND 7, packed at the real atlas texel size and stretched to the
         panel's true aspect
      3  ROUND 8, the same, so the A/B is like for like
      4  ROUND 8 with every element of DECKS[slug] drawn on at its true
         radius in feet, so the button spec can be judged against the print

  BLOCK B -- the four printed lower FRONTS, round 7 against round 8, with the
      T-molding bead FRONT_RECT now leaves drawn either side at its true
      width, so "does the art bleed into the bead" is checkable.

Nothing is upscaled before quantisation; columns 2-4 are the bytes that ship.

    $PY scratchpad/arc4/art/_r8_dump.py scratchpad/arc4/art/_r8pk/new
    $PY scratchpad/arc4/art/_r8_dump.py scratchpad/arc4/art/_r8pk/old old
    $PY scratchpad/arc4/art/_r8_preview.py
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)

from PIL import Image, ImageDraw  # noqa: E402
import art_g2  # noqa: E402

PK = os.path.join(HERE, "_r8pk")
PHOTO = os.path.join(ROOT, "docs", "photos-jpg")
SLUGS = ["legends-ultimate", "street-fighter-2-champion-edition",
         "time-crisis", "terminator-2"]
LABEL = {
    "legends-ultimate": "LEGENDS ULTIMATE   bw 2.95   untouched this round",
    "street-fighter-2-champion-edition":
        "SFII CHAMPION EDITION   bw 2.42   rendered as a BARE BLUE PLATE",
    "time-crisis": "TIME CRISIS   bw 2.52   the control: printed in round 7",
    "terminator-2":
        "TERMINATOR 2   bw 2.28   rendered as a BARE GREY PLATE",
}
CROP = {
    "legends-ultimate": ("Arcade Room v4 3.jpg", (395, 300, 510, 450)),
    "street-fighter-2-champion-edition":
        ("Arcade Room v4 4.jpg", (96, 162, 146, 190)),
    "time-crisis": ("Arcade Room v4 4.jpg", (36, 166, 110, 200)),
    "terminator-2": ("Arcade Room v4 5.jpg", (190, 166, 224, 187)),
}
FCROP = {
    "legends-ultimate": ("Arcade Room v4 8.jpg", (438, 175, 490, 220)),
    "street-fighter-2-champion-edition":
        ("Arcade Room v4 8.jpg", (404, 155, 442, 215)),
    "time-crisis": ("Arcade Room v4 8.jpg", (386, 150, 414, 210)),
    "terminator-2": ("Arcade Room v4 8.jpg", (355, 145, 392, 200)),
}
BW = art_g2._BW
H = 190
FH = 250


def _hex(c):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def packed(which, key, h):
    im = Image.open(os.path.join(PK, which, key.replace(".", "__") + ".png"))
    meta = json.load(open(os.path.join(PK, which, "meta.json")))
    a = meta["aspect"][key]
    return im.resize((int(h * a), h), Image.NEAREST), im.size, meta


def photo(box_table, slug, h):
    name, box = box_table[slug]
    im = Image.open(os.path.join(PHOTO, name)).convert("RGB").crop(box)
    z = h / float(im.height)
    return im.resize((max(1, int(im.width * z)), h), Image.LANCZOS)


def overlay(slug, base):
    """Draw DECKS[slug] on the stretched deck panel at true scale."""
    im = base.convert("RGB").copy()
    d = ImageDraw.Draw(im, "RGBA")
    bw = BW[slug]
    hw_paint = bw * 0.5 - 0.06
    k = (bw * 0.5 - 0.10) / hw_paint
    fx = im.width / (2.0 * hw_paint)
    fy = im.height / 0.92
    spec = art_g2.DECKS[slug]

    def at(u, v):
        return (im.width * 0.5 * (1.0 + k * u), im.height * v)

    for g in (spec.get("guns") or ()):
        cx, cy = at(g["u"], g["v"])
        L = g["len_ft"] * fy
        W = 0.16 * fx
        a = math.radians(g["yaw_deg"])
        pts = []
        for (dx, dy) in ((-W, -L * .5), (W, -L * .5), (W, L * .5),
                         (-W, L * .5)):
            pts.append((cx + dx * math.cos(a) - dy * math.sin(a),
                        cy + dx * math.sin(a) + dy * math.cos(a)))
        d.polygon(pts, fill=_hex(g["body"]) + (225,),
                  outline=(255, 255, 255, 120))
    for s in (spec.get("sticks") or ()):
        cx, cy = at(s["u"], s["v"])
        r = s["dust_r_ft"]
        d.ellipse([cx - r * fx, cy - r * fy, cx + r * fx, cy + r * fy],
                  fill=_hex(s["dust_color"]) + (215,))
        r = s["top_r_ft"]
        d.ellipse([cx - r * fx, cy - r * fy, cx + r * fx, cy + r * fy],
                  fill=_hex(s["top_color"]) + (255,),
                  outline=(255, 255, 255, 150))
    tb = spec.get("trackball")
    if tb:
        cx, cy = at(tb["u"], tb["v"])
        r = tb["r_ft"]
        d.ellipse([cx - r * fx, cy - r * fy, cx + r * fx, cy + r * fy],
                  fill=_hex(tb["color"]) + (255,),
                  outline=_hex(tb["bezel_color"]) + (255,), width=2)
    for b in (spec.get("buttons") or ()):
        cx, cy = at(b["u"], b["v"])
        r = b["r_ft"]
        d.ellipse([cx - r * fx, cy - r * fy, cx + r * fx, cy + r * fy],
                  fill=_hex(b["color"]) + (255,), outline=(0, 0, 0, 150))
    return im


def with_bead(slug, base, inset):
    """Paste the panel inside the bead FRONT_RECT leaves for it, to scale."""
    bw = BW[slug]
    pw = bw - 2.0 * inset
    tot = int(base.width * bw / pw)
    im = Image.new("RGB", (tot, base.height), (26, 26, 30))
    d = ImageDraw.Draw(im)
    b = int(round((tot - base.width) / 2.0))
    d.rectangle([0, 0, max(0, b - 1), im.height], fill=(150, 60, 70))
    d.rectangle([tot - b, 0, tot, im.height], fill=(150, 60, 70))
    im.paste(base, (b, 0))
    return im


def main():
    pad, lab = 16, 26
    rows = []
    for s in SLUGS:
        key = s + ".deck"
        old, odim, _ = packed("old", key, H)
        new, ndim, _ = packed("new", key, H)
        rows.append((LABEL[s], [
            ("PHOTOGRAPH  %s %s" % CROP[s], photo(CROP, s, H)),
            ("ROUND 7  packed %dx%d texels" % odim, old),
            ("ROUND 8  packed %dx%d texels" % ndim, new),
            ("ROUND 8 + DECKS geometry at true ft", overlay(s, new)),
        ]))

    frows = []
    for s in SLUGS:
        key = s + ".front"
        old, odim, ometa = packed("old", key, FH)
        new, ndim, nmeta = packed("new", key, FH)
        oi = ometa["inset"][s]
        ni = nmeta["inset"][s]
        frows.append((s.upper(), [
            ("PHOTOGRAPH  %s %s" % FCROP[s], photo(FCROP, s, FH)),
            ("ROUND 7 front, bead %.2f ft" % oi, with_bead(s, old, oi)),
            ("ROUND 8 front, bead %.2f ft" % ni, with_bead(s, new, ni)),
        ]))

    def block_w(rs):
        return pad + max(sum(i.width + pad for _, i in r) for _, r in rs)

    W = max(block_w(rows), block_w(frows))
    HT = (46 + sum(lab + H + 22 + pad for _ in rows)
          + 54 + sum(lab + FH + 22 + pad for _ in frows) + pad)
    out = Image.new("RGB", (W, HT), (22, 22, 26))
    d = ImageDraw.Draw(out)
    d.text((pad, 10), "ARCADE ROOM -- SOUTH RUN -- ROUND 8 (art_g2).  "
           "Columns 2-4 are packed at the REAL atlas texel size and only "
           "then stretched: no upscaling flattery.", fill=(235, 237, 242))
    d.text((pad, 26), "BLOCK A -- THE TWO BARE DECKS.  Champion Edition and "
           "Terminator 2 rendered as flat plates because ART_DK's 0.0723 "
           "linear factor put their diffuse under the scene's ambient floor. "
           "Both are re-levelled to the photographs' deck-to-deck ratio and "
           "need a2kit.DECK_MAT = D.", fill=(150, 154, 162))
    y = 46
    for title, cells in rows:
        d.text((pad, y), title, fill=(232, 234, 240))
        y += lab
        x = pad
        for cap, im in cells:
            out.paste(im, (x, y))
            d.rectangle([x - 1, y - 1, x + im.width, y + im.height],
                        outline=(92, 96, 106))
            d.text((x + 2, y + im.height + 5), cap, fill=(150, 154, 162))
            x += im.width + pad
        y += H + 22 + pad
    d.text((pad, y + 6), "BLOCK B -- THE PRINTED LOWER FRONTS, cut to bleed. "
           "The red strip either side is the T-molding bead FRONT_RECT now "
           "leaves for the carcase agent, drawn at its true width "
           "(0.02-0.10 ft -> 0.06 ft on all four).", fill=(150, 154, 162))
    y += 34
    for title, cells in frows:
        d.text((pad, y), title, fill=(232, 234, 240))
        y += lab
        x = pad
        for cap, im in cells:
            out.paste(im, (x, y))
            d.rectangle([x - 1, y - 1, x + im.width, y + im.height],
                        outline=(92, 96, 106))
            d.text((x + 2, y + im.height + 5), cap, fill=(150, 154, 162))
            x += im.width + pad
        y += FH + 22 + pad
    p = os.path.join(HERE, "r8_south-decks.png")
    out.save(p)
    print("wrote", p, out.size)


if __name__ == "__main__":
    main()
