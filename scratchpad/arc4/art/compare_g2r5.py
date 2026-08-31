"""Round-5 G2: my four elevations beside the photo crops of the SAME four
machines, at the same height, so the wrap can be judged against the owner's
photographs rather than against itself.

    $PY scratchpad/arc4/art/compare_g2r5.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)

from PIL import Image, ImageDraw          # noqa: E402
import preview_g2r5 as P                  # noqa: E402

# hand-placed on docs/photos-jpg/Arcade Room v3 4.jpg (1200x1600) -- the only
# frame that sees all four machines whole.
CROPS = {
    "legends-ultimate": ("Arcade Room v3 4.jpg", (985, 548, 1185, 900)),
    "street-fighter-2-champion-edition":
        ("Arcade Room v3 4.jpg", (898, 548, 1012, 840)),
    "time-crisis": ("Arcade Room v3 4.jpg", (818, 540, 932, 900)),
    "terminator-2": ("Arcade Room v3 4.jpg", (728, 540, 832, 900)),
}
H = 620


def photo(slug):
    name, box = CROPS[slug]
    im = Image.open(os.path.join(ROOT, "docs", "photos-jpg", name)).crop(box)
    return im.resize((int(im.width * H / im.height), H), Image.LANCZOS)


def mine(slug):
    im = P.elevation(slug)
    return im.resize((int(im.width * H / im.height), H), Image.NEAREST)


if __name__ == "__main__":
    pad = 16
    cols = []
    for s in P.SLUGS:
        cols.append((s, photo(s), mine(s)))
    w = pad + sum(max(a.width, b.width) + pad for _, a, b in cols)
    out = Image.new("RGB", (w, H * 2 + pad * 3 + 22), (22, 22, 26))
    d = ImageDraw.Draw(out)
    x = pad
    for s, a, b in cols:
        cw = max(a.width, b.width)
        out.paste(a, (x + (cw - a.width) // 2, pad))
        out.paste(b, (x + (cw - b.width) // 2, pad * 2 + H))
        d.text((x, H * 2 + pad * 2 + 6), s, fill=(205, 208, 216))
        x += cw + pad
    d.text((pad, 2), "TOP: owner photo v3 4    BOTTOM: round-5 G2 wrap "
           "(flat panels, no lighting, no geometry)", fill=(150, 154, 162))
    p = os.path.join(HERE, "compare_g2r5.png")
    out.save(p)
    print("wrote", p, out.size)
