"""art_g0's round-5 panels beside the photograph crops they were drawn from.

Writes scratchpad/arc4/art/compare_g0_r5.png.  Left of each pair is the shipping
atlas tile, resampled to the quad's real world aspect; right is the crop named in
NOTES_R5, at native pixels upscaled with LANCZOS.  If a panel reads as a dark
slab with a label on it next to its own photograph, it is not done.
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ARC4 = os.path.abspath(os.path.join(_HERE, ".."))
_ROOT = os.path.abspath(os.path.join(_ARC4, "..", ".."))
_TOOLS = os.path.join(_ROOT, "tools")
for _p in (_TOOLS, _ARC4, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import art_g0                                              # noqa: E402
import art_g1                                              # noqa: E402
import art_g2                                              # noqa: E402
import art_g3                                              # noqa: E402
for _m in (art_g1, art_g2, art_g3):
    _m.PANELS = {}
import atlas4                                              # noqa: E402
from PIL import Image, ImageDraw                           # noqa: E402

PHOTO = os.path.join(_ROOT, "docs", "photos-jpg")

PAIRS = [
    ("pac-man.front", "Arcade Room v3 1.jpg", (600, 660, 700, 810)),
    ("pac-man.side", "Arcade Room v4 6.jpg", (262, 130, 300, 280)),
    ("nba-jam.front", "Arcade Room v3 4.jpg", (322, 690, 420, 830)),
    ("nba-jam.deck", "Arcade Room v4 7.jpg", (322, 300, 420, 400)),
    ("tmnt-turtles-in-time.front", "Arcade Room v3 4.jpg", (412, 685, 500, 830)),
    ("tmnt-turtles-in-time.deck", "Arcade Room v4 7.jpg", (408, 280, 600, 400)),
    ("golden-tee-3d-golf.front", "Arcade Room v4 6.jpg", (368, 215, 434, 300)),
    ("golden-tee-3d-golf.deck", "Arcade Room v4 7.jpg", (96, 168, 186, 205)),
]

H = 250
GAP = 10
PAIR_GAP = 34
PAD = 26


def main():
    cells = []
    for (key, pf, box) in PAIRS:
        n = atlas4.size_of(key)
        rows = atlas4.render(key, n)
        a = Image.new("RGB", (n, n))
        a.putdata([c for r in rows for c in r])
        ar = art_g0.ASPECT[key]
        a = a.resize((max(20, int(H * ar)), H), Image.NEAREST)
        im = Image.open(os.path.join(PHOTO, pf)).convert("RGB").crop(box)
        w = max(20, int(H * im.width / float(im.height)))
        b = im.resize((w, H), Image.LANCZOS)
        cells.append((key, pf, box, a, b))

    per = 2
    rows_ = [cells[i:i + per] for i in range(0, len(cells), per)]
    wid = PAD * 2 + max(sum(c[3].width + GAP + c[4].width + PAIR_GAP
                            for c in r) for r in rows_)
    hgt = PAD * 2 + len(rows_) * (H + 46)
    sheet = Image.new("RGB", (wid, hgt), (24, 24, 27))
    d = ImageDraw.Draw(sheet)
    y = PAD
    for r in rows_:
        x = PAD
        for (key, pf, box, a, b) in r:
            sheet.paste(a, (x, y))
            sheet.paste(b, (x + a.width + GAP, y))
            d.rectangle([x - 1, y - 1, x + a.width, y + H],
                        outline=(90, 160, 90))
            d.rectangle([x + a.width + GAP - 1, y - 1,
                         x + a.width + GAP + b.width, y + H],
                        outline=(160, 120, 90))
            d.text((x, y + H + 8), "%s   |   %s %s" % (key, pf, box),
                   fill=(190, 190, 196))
            x += a.width + GAP + b.width + PAIR_GAP
        y += H + 46
    out = os.path.join(_HERE, "compare_g0_r5.png")
    sheet.save(out)
    print("wrote", out, sheet.size)


if __name__ == "__main__":
    main()
