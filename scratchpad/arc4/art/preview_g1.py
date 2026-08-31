"""Render art_g1's panels, both as authored tiles and as they will appear
once mapped onto their real-world quad, and meter each one."""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image                                          # noqa: E402
import art_g1 as G                                             # noqa: E402

TILE = 256
OUT = os.path.dirname(os.path.abspath(__file__))
keys = list(G.PANELS)

tiles = {}
stats = {}
for k in keys:
    t0 = time.time()
    px = [[(0, 0, 0)] * TILE for _ in range(TILE)]
    G.PANELS[k](px, 0, 0, TILE)
    im = Image.new("RGB", (TILE, TILE))
    im.putdata([p for row in px for p in row])
    tiles[k] = im
    g = im.convert("L")
    d = list(g.getdata())
    mean = sum(d) / len(d)
    sd = (sum((v - mean) ** 2 for v in d) / len(d)) ** 0.5
    dd = 0
    n = 0
    for y in range(TILE):
        r = d[y * TILE:(y + 1) * TILE]
        for x in range(TILE - 1):
            dd += abs(r[x + 1] - r[x])
            n += 1
    stats[k] = (mean, sd, dd / n, time.time() - t0)

# --- sheet: every panel drawn at its true aspect, 1 row per machine
CELL_H = 190
PAD = 14
rows = [
    ["marvel-super-heroes.marquee", "marvel-super-heroes.riser",
     "marvel-super-heroes.front", "marvel-super-heroes.deck",
     "marvel-super-heroes.side"],
    ["tmnt-turtles-in-time.marquee", "tmnt-turtles-in-time.riser",
     "tmnt-turtles-in-time.front", "tmnt-turtles-in-time.deck",
     "tmnt-turtles-in-time.side"],
    ["time-crisis.marquee", "time-crisis.speaker", "time-crisis.front",
     "time-crisis.deck", "time-crisis.side"],
    ["pac-man.marquee", "pac-man.front", "pac-man.deck", "pac-man.side"],
]
W = max(sum(int(CELL_H * G.ASPECT[k]) + PAD for k in r) for r in rows) + PAD
H = len(rows) * (CELL_H + PAD) + PAD
sheet = Image.new("RGB", (W, H), (26, 26, 30))
y = PAD
for r in rows:
    x = PAD
    for k in r:
        w = int(CELL_H * G.ASPECT[k])
        sheet.paste(tiles[k].resize((w, CELL_H), Image.NEAREST), (x, y))
        x += w + PAD
    y += CELL_H + PAD
sheet.save(os.path.join(OUT, "preview_g1.png"))

# --- the raw authored tiles, as the atlas will hold them
gw = 5
gh = (len(keys) + gw - 1) // gw
raw = Image.new("RGB", (gw * TILE, gh * TILE), (0, 0, 0))
for i, k in enumerate(keys):
    raw.paste(tiles[k], ((i % gw) * TILE, (i // gw) * TILE))
raw.save(os.path.join(OUT, "preview_g1_tiles.png"))

from captions_g1 import CAPTIONS                                   # noqa: E402
CAP = dict(CAPTIONS)
with open(os.path.join(OUT, "preview_g1_caption.txt"), "w") as f:
    f.write("preview_g1.png -- one row per machine, each panel drawn at the\n"
            "real-world aspect of the quad it maps onto (ASPECT in art_g1),\n"
            "which is how it will look once mapped.  preview_g1_tiles.png is\n"
            "the same panels as authored square atlas tiles.\n"
            "Row order: Marvel Super Heroes / TMNT Turtles in Time /\n"
            "Time Crisis / Pac-Man.  Left to right within a row as listed.\n\n")
    for r in rows:
        for k in r:
            m, sd, d1, dt = stats[k]
            f.write("%s\n    A=%.2f  mean %.1f  sd %.1f  |d1| %.2f  "
                    "(%.1fs)\n    %s\n" % (k, G.ASPECT[k], m, sd, d1, dt,
                                            CAP.get(k, "")))
        f.write("\n")
print(open(os.path.join(OUT, "preview_g1_caption.txt")).read())

