"""Round-5 preview sheet for agent g3's three machines.

Renders every panel THROUGH `render` -- i.e. at the exact size the atlas
packs it, supersampled and re-quantised to 16 levels -- then stretches it to
its own world ASPECT so what the sheet shows is what the cabinet will wear, not
a square tile.  Writes `wrap_g3.png` and prints the measured mean of each panel.

    $PY scratchpad/arc4/art/preview_g3.py
"""
import os
import sys

from PIL import Image, ImageDraw

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.dirname(_HERE))

import art_g3                                                   # noqa: E402

# atlas4's packing constants, MIRRORED rather than imported: importing atlas4
# merges all four art modules' PANELS and raises on a duplicate key, and while
# four agents are editing four modules in parallel that is guaranteed to be
# broken at any given second.  These four values are read out of
# scratchpad/arc4/atlas4.py at the top of every run and asserted against it, so
# the mirror cannot drift silently.
_A4 = os.path.join(os.path.dirname(_HERE), "atlas4.py")
_ns = {}
_src = open(_A4, encoding="utf-8").read()
_blk = _src[_src.index("SIZE = {"):_src.index("def size_of")]
exec(compile(_blk, _A4, "exec"), _ns)                           # noqa: S102
SIZE, SIZE_KEY = _ns["SIZE"], _ns["SIZE_KEY"]
SS, QUANT, DEFAULT_SIZE = _ns["SS"], _ns["QUANT"], _ns["DEFAULT_SIZE"]


def size_of(key):
    if key in SIZE_KEY:
        return SIZE_KEY[key]
    return SIZE.get(key.split(".")[-1], DEFAULT_SIZE)


def _q(v):
    v = int(v / QUANT + 0.5) * QUANT
    return 0 if v < 0 else (255 if v > 255 else v)


def render(key, n):
    """A byte-for-byte copy of render: supersample by SS, box-average
    down, re-quantise to QUANT levels."""
    big = n * SS
    buf = [[(0, 0, 0)] * big for _ in range(big)]
    art_g3.PANELS[key](buf, 0, 0, big)
    out = []
    inv = 1.0 / (SS * SS)
    for y in range(n):
        rows = buf[y * SS:(y + 1) * SS]
        row = []
        for x in range(n):
            r = g = b = 0
            for sr in rows:
                for c in sr[x * SS:(x + 1) * SS]:
                    r += c[0]
                    g += c[1]
                    b += c[2]
            row.append((_q(r * inv), _q(g * inv), _q(b * inv)))
        out.append(row)
    return out

MACHINES = [
    ("STAR WARS (Atari) -- EAST_RUN[0], NE corner, free-standing at ~40deg",
     "star-wars-atari", ("side", "front", "deck", "marquee")),
    ("RIDGE RACER -- Namco driving cabinet, SW corner",
     "ridge-racer", ("side", "front", "deck", "marquee")),
    ("GRAFFITI MULTICADE -- NORTH_RUN[0], no legible title",
     "north-1-graffiti-multicade", ("side", "front", "deck", "marquee")),
]
H = 430                     # display height of a side panel, px
PAD = 26
BG = (24, 24, 28)


def tile_image(key):
    n = size_of(key)
    rows = render(key, n)
    im = Image.new("RGB", (n, n))
    im.putdata([c for row in rows for c in row])
    return im, rows


def mean_of(rows):
    n = len(rows)
    s = 0
    for row in rows:
        for c in row:
            s += c[0] + c[1] + c[2]
    return s / (3.0 * n * n)


def main():
    cells = []
    means = {}
    for title, slug, panels in MACHINES:
        row = []
        for p in panels:
            key = "%s.%s" % (slug, p)
            im, rows = tile_image(key)
            means[key] = round(mean_of(rows), 1)
            ar = art_g3.PANEL_AR[key]
            if p in ("marquee", "deck"):
                w = int(H * 0.62 * ar)
                h = int(H * 0.62)
            else:
                h = H
                w = int(H * ar)
            row.append((key, im.resize((max(8, w), h), Image.NEAREST)))
        cells.append((title, row))

    wid = max(sum(im.width for _, im in row) + PAD * (len(row) + 1)
              for _, row in cells)
    hei = sum(max(im.height for _, im in row) + 54 for _, row in cells) + PAD
    sheet = Image.new("RGB", (wid, hei), BG)
    d = ImageDraw.Draw(sheet)
    y = PAD
    for title, row in cells:
        d.text((PAD, y - 16), title, fill=(232, 232, 238))
        x = PAD
        top = y + 12
        for key, im in row:
            sheet.paste(im, (x, top))
            d.rectangle([x - 1, top - 1, x + im.width, top + im.height],
                        outline=(96, 96, 104))
            d.text((x, top + im.height + 4),
                   "%s  %dpx  mean %.0f" % (key.split(".")[1],
                                            size_of(key), means[key]),
                   fill=(176, 176, 184))
            x += im.width + PAD
        y = top + max(im.height for _, im in row) + 46
    out = os.path.join(_HERE, "wrap_g3.png")
    sheet.save(out)
    print("wrote", out, sheet.size)
    for k in sorted(means):
        print("  %-44s %s" % (k, means[k]))
    return means


if __name__ == "__main__":
    main()
