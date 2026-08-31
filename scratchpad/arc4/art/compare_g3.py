"""Agent g3's round-5 panels beside the photograph each was read off.

Left of every pair is the owner's photograph, cropped to the surface and
upscaled with LANCZOS; right of it is the drawn panel, rendered through the
atlas pipeline at the size the atlas packs it and stretched to that panel's own
world aspect.  Writes `compare_g3.png`.

    $PY scratchpad/arc4/art/compare_g3.py
"""
import os
import sys

from PIL import Image, ImageDraw

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_HERE)))
sys.path.insert(0, _HERE)

import art_g3                                                   # noqa: E402
import preview_g3 as P                                          # noqa: E402

PHOTOS = os.path.join(_ROOT, "docs", "photos-jpg")

# (caption, panel key, photo file, crop box, "how the photo was framed")
PAIRS = [
    ("Star Wars flank", "star-wars-atari.side",
     "Arcade Room v4 9.jpg", (150, 225, 262, 470)),
    ("Star Wars flank, second frame", "star-wars-atari.side",
     "Arcade Room v4 8.jpg", (0, 150, 120, 340)),
    ("Ridge Racer front + deck", "ridge-racer.front",
     "Arcade Room v4 8.jpg", (497, 150, 560, 235)),
    ("Ridge Racer deck", "ridge-racer.deck",
     "Arcade Room v4 8.jpg", (500, 175, 562, 200)),
    ("Ridge Racer marquee", "ridge-racer.marquee",
     "Arcade Room v4 8.jpg", (500, 128, 562, 145)),
    ("Ridge Racer flank + base", "ridge-racer.side",
     "Arcade Room v4 5.jpg", (296, 145, 330, 225)),
    ("Multicade whole machine", "north-1-graffiti-multicade.side",
     "Arcade Room v3 1.jpg", (518, 560, 600, 835)),
    ("Multicade front, neutral exposure", "north-1-graffiti-multicade.front",
     "Arcade Room v4 6.jpg", (236, 192, 272, 262)),
    ("Multicade deck", "north-1-graffiti-multicade.deck",
     "Arcade Room v4 6.jpg", (238, 168, 274, 190)),
    ("Multicade front + coin recess (blue RGB wash)",
     "north-1-graffiti-multicade.front",
     "Arcade Room v3 1.jpg", (540, 690, 600, 800)),
]
H = 330
PAD = 22
BG = (22, 22, 26)


def main():
    cells = []
    for cap, key, fn, box in PAIRS:
        p = os.path.join(PHOTOS, fn)
        ph = Image.open(p).convert("RGB").crop(box)
        ph = ph.resize((max(8, int(H * ph.width / float(ph.height))), H),
                       Image.LANCZOS)
        n = P.size_of(key)
        rows = P.render(key, n)
        art = Image.new("RGB", (n, n))
        art.putdata([c for row in rows for c in row])
        ar = art_g3.PANEL_AR[key]
        art = art.resize((max(8, int(H * ar)), H), Image.NEAREST)
        cells.append((cap, fn, ph, art))

    per = 2
    rows_ = [cells[i:i + per] for i in range(0, len(cells), per)]
    wid = max(sum(a.width + b.width + PAD for _, _, a, b in r) + PAD * (len(r) + 1)
              for r in rows_)
    hei = len(rows_) * (H + 62) + PAD
    sheet = Image.new("RGB", (wid, hei), BG)
    d = ImageDraw.Draw(sheet)
    y = PAD + 14
    for r in rows_:
        x = PAD
        for cap, fn, ph, art in r:
            sheet.paste(ph, (x, y))
            sheet.paste(art, (x + ph.width + 6, y))
            d.rectangle([x - 1, y - 1, x + ph.width, y + H],
                        outline=(120, 120, 128))
            d.rectangle([x + ph.width + 5, y - 1,
                         x + ph.width + 6 + art.width, y + H],
                        outline=(120, 120, 128))
            d.text((x, y - 13), "PHOTO %s  |  DRAWN -- %s" % (fn, cap),
                   fill=(226, 226, 232))
            x += ph.width + art.width + PAD + 6
        y += H + 62
    out = os.path.join(_HERE, "compare_g3.png")
    sheet.save(out)
    print("wrote", out, sheet.size)


if __name__ == "__main__":
    main()
