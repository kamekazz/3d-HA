"""Round-5 preview sheet for art_g0's four wrapped machines.

Writes scratchpad/arc4/art/wrap_g0.png: for each machine, every panel it
claims, drawn at the SHIPPING atlas size (so what you look at is what the
cabinet gets), then rescaled to the panel's real world aspect and blown up so
a human can judge it.  A panel that reads as a dark slab with a label on it
here will read as one on the cabinet.

    $PY scratchpad/arc4/art/preview_g0_r5.py
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ARC4 = os.path.abspath(os.path.join(_HERE, ".."))
_TOOLS = os.path.abspath(os.path.join(_ARC4, "..", "..", "tools"))
for _p in (_TOOLS, _ARC4, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import art_g0                                              # noqa: E402

# art_g1 / art_g3 still carry round 4's pac-man, tmnt and golden-tee panels;
# atlas4 refuses a duplicate key, and resolving that is the INTEGRATOR's merge
# step (see art_g0.WRAP_R5).  For this preview the other three modules are
# emptied before atlas4 imports them, so nothing on disk is touched.
import art_g1                                              # noqa: E402
import art_g2                                              # noqa: E402
import art_g3                                              # noqa: E402
for _m in (art_g1, art_g2, art_g3):
    _m.PANELS = {}

import atlas4                                              # noqa: E402
from PIL import Image, ImageDraw                           # noqa: E402

MACHINES = [
    ("PAC-MAN  (north 2)", "pac-man", ("side", "front", "deck")),
    ("NBA JAM  (east 5)", "nba-jam", ("side", "front", "deck")),
    ("TURTLES IN TIME  (east 6)", "tmnt-turtles-in-time",
     ("side", "front", "deck")),
    ("GOLDEN TEE 3D GOLF  (north 4)", "golden-tee-3d-golf",
     ("side", "front", "deck", "bezel")),
]

CELL_H = 300
GAP = 14
PAD = 30
HDR = 26

# what a2kit multiplies each deck tile by, so the preview shows the RENDERED
# value and not just the authored one
DECK_FACTOR = {"pac-man": 0x4c / 255.0,          # ART_DK, as shipped
               "nba-jam": 0xc9 / 255.0,          # ART_D  -- REQUESTED
               "tmnt-turtles-in-time": 0xc9 / 255.0,
               "golden-tee-3d-golf": 0xc9 / 255.0}


def tile_image(key):
    n = atlas4.size_of(key)
    rows = atlas4.render(key, n)
    im = Image.new("RGB", (n, n))
    im.putdata([c for row in rows for c in row])
    return im, n


def main():
    cells = []
    for (title, slug, panels) in MACHINES:
        row = []
        for pn in panels:
            key = "%s.%s" % (slug, pn)
            im, n = tile_image(key)
            ar = art_g0.ASPECT[key]
            h = CELL_H
            w = max(24, int(round(h * ar)))
            im = im.resize((w, h), Image.NEAREST)
            if pn == "deck":
                f = DECK_FACTOR[slug]
                im = im.point(lambda v, _f=f: int(v * _f))
            row.append((key, n, im))
        cells.append((title, row))

    wid = PAD * 2 + max(sum(c[2].width for c in r) + GAP * (len(r) - 1)
                        for (_, r) in cells)
    hgt = PAD + sum(HDR + CELL_H + 30 + GAP for _ in cells) + PAD
    sheet = Image.new("RGB", (wid, hgt), (24, 24, 27))
    d = ImageDraw.Draw(sheet)
    y = PAD
    for (title, row) in cells:
        d.text((PAD, y + 6), title, fill=(240, 240, 240))
        y += HDR
        x = PAD
        for (key, n, im) in row:
            sheet.paste(im, (x, y))
            d.rectangle([x - 1, y - 1, x + im.width, y + im.height],
                        outline=(90, 90, 96))
            d.text((x, y + im.height + 8),
                   "%s   %dpx  ar %.2f" % (key.split(".")[-1], n,
                                           im.width / float(im.height)),
                   fill=(170, 170, 176))
            x += im.width + GAP
        y += CELL_H + 30 + GAP
    out = os.path.join(_HERE, "wrap_g0.png")
    sheet.save(out)
    print("wrote", out, sheet.size)

    # mean / sd per panel, so "is it a dark slab" is a number too
    for (_, slug, panels) in MACHINES:
        for pn in panels:
            key = "%s.%s" % (slug, pn)
            rows = atlas4.render(key, atlas4.size_of(key))
            px = [sum(c) / 3.0 for r in rows for c in r]
            m = sum(px) / len(px)
            sd = (sum((v - m) ** 2 for v in px) / len(px)) ** 0.5
            print("%-34s mean %6.1f  sd %5.1f" % (key, m, sd))


if __name__ == "__main__":
    main()
