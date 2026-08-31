"""Render art_g2's panels twice: as authored square tiles, and stretched to
the aspect each one actually lands on.  Also reports the PNG cost."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image                      # noqa: E402  (preview only)
import art_g2 as A                         # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
T = A.TILE
ORDER = [
    "marvel-vs-capcom.marquee", "marvel-vs-capcom.side",
    "marvel-vs-capcom.front", "marvel-vs-capcom.deck",
    "marvel-vs-capcom.riser",
    "terminator-2.marquee", "terminator-2.side", "terminator-2.front",
    "terminator-2.deck",
    "nfl-blitz.marquee", "nfl-blitz.side", "nfl-blitz.front",
    "nfl-blitz.deck",
    "east-7-no-machine.marquee", "east-7-no-machine.side",
    "east-7-no-machine.front", "east-7-no-machine.deck",
]


def tile_of(name):
    px = [[(0, 0, 0)] * T for _ in range(T)]
    A.PANELS[name](px, 0, 0, T)
    im = Image.new("RGB", (T, T))
    im.putdata([p for row in px for p in row])
    return im, px


tiles = {}
for n in ORDER:
    tiles[n] = tile_of(n)
    im, px = tiles[n]
    flat = [c for row in px for p in row for c in p]
    print("%-32s mean %5.1f" % (n, sum(flat) / len(flat)))

# ---- atlas cost: pack all 17 into a 5x4 grid and weigh the PNG
COLS, ROWS = 5, 4
at = Image.new("RGB", (COLS * T, ROWS * T), (0, 0, 0))
for i, n in enumerate(ORDER):
    at.paste(tiles[n][0], ((i % COLS) * T, (i // COLS) * T))
at.save(os.path.join(HERE, "atlas_g2.png"), optimize=True)
print("atlas_g2.png (5x4 x 256) =",
      os.path.getsize(os.path.join(HERE, "atlas_g2.png")), "bytes")

# ---- grid preview, square tiles, 4 across
PAD, COLS = 10, 5
g = Image.new("RGB", (COLS * (T + PAD) + PAD, 4 * (T + PAD) + PAD), (26, 26, 30))
for i, n in enumerate(ORDER):
    g.paste(tiles[n][0], (PAD + (i % COLS) * (T + PAD),
                          PAD + (i // COLS) * (T + PAD)))
g.save(os.path.join(HERE, "preview_g2.png"))

# ---- how each panel actually lands: tile stretched to its own aspect
H = 190
cells = []
for n in ORDER:
    a = A.ASPECT[n.split(".")[1]]
    w = max(40, int(H * a))
    cells.append((n, tiles[n][0].resize((w, H), Image.LANCZOS)))
rowsets, cur, curw = [], [], 0
for c in cells:
    if curw + c[1].width + 12 > 1500 and cur:
        rowsets.append(cur)
        cur, curw = [], 0
    cur.append(c)
    curw += c[1].width + 12
rowsets.append(cur)
W = max(sum(c[1].width + 12 for c in r) + 12 for r in rowsets)
Hh = len(rowsets) * (H + 12) + 12
p = Image.new("RGB", (W, Hh), (26, 26, 30))
y = 12
for r in rowsets:
    x = 12
    for n, im in r:
        p.paste(im, (x, y))
        x += im.width + 12
    y += H + 12
p.save(os.path.join(HERE, "preview_g2_onpanel.png"))

with open(os.path.join(HERE, "preview_g2_caption.txt"), "w") as f:
    f.write("preview_g2.png -- authored square tiles, 5 across, "
            "reading order:\n")
    for i, n in enumerate(ORDER):
        f.write("  row %d col %d  %s\n" % (i // 5 + 1, i % 5 + 1, n))
    f.write("\npreview_g2_onpanel.png -- the same tiles stretched to the "
            "aspect each lands on\n(marquee 3.40:1, side 0.49:1, front "
            "1.25:1, deck 2.35:1, riser 6.20:1),\nwhich is how they will "
            "read on the cabinet.  Same order, wrapped by width.\n")
print("wrote preview_g2.png, preview_g2_onpanel.png, preview_g2_caption.txt")
