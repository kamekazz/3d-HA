"""Cost if each cabinet GLB carries only the panels it uses.

a2kit shares one atlas image by byte identity WITHIN a GLB, but the three
cabinet pieces (East / North / South) are three separate files, so a single
big atlas is paid for three times.  Per-piece sub-atlases are the cheap route.
"""
import os
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
from roomkit.glb import png_rgb                                 # noqa: E402
import art_g1 as G                                              # noqa: E402
from PIL import Image                                           # noqa: E402

GROUPS = {
    "EAST  (Marvel + TMNT, 10 panels)":
        [k for k in G.PANELS if k.startswith(("marvel", "tmnt"))],
    "SOUTH (Time Crisis, 5 panels)":
        [k for k in G.PANELS if k.startswith("time-crisis")],
    "NORTH (Pac-Man, 4 panels)":
        [k for k in G.PANELS if k.startswith("pac-man")],
}


def sheet(keys, tile, ncol=5):
    nrow = (len(keys) + ncol - 1) // ncol
    W, H = ncol * tile, nrow * tile
    px = [[(0, 0, 0)] * W for _ in range(H)]
    for i, k in enumerate(keys):
        G.PANELS[k]((px), (i % ncol) * tile, (i // ncol) * tile, tile)
    return px


for tile in (96, 128, 160, 192):
    tot = 0.0
    line = []
    for name, keys in GROUPS.items():
        kb = len(png_rgb(sheet(keys, tile))) / 1024.0
        tot += kb
        line.append("%s %.0f KB" % (name.split()[0], kb))
    print("tile %3d   %s   TOTAL %.1f KB" % (tile, "  ".join(line), tot))

# a 128 px eyeball sheet
tile = 128
keys = list(G.PANELS)
px = sheet(keys, tile)
im = Image.new("RGB", (5 * tile, ((len(keys) + 4) // 5) * tile))
im.putdata([p for row in px for p in row])
CELL = 150
rows = [["marvel-super-heroes.marquee", "marvel-super-heroes.riser",
         "marvel-super-heroes.front", "marvel-super-heroes.deck",
         "marvel-super-heroes.side"],
        ["tmnt-turtles-in-time.marquee", "tmnt-turtles-in-time.riser",
         "tmnt-turtles-in-time.front", "tmnt-turtles-in-time.deck",
         "tmnt-turtles-in-time.side"],
        ["time-crisis.marquee", "time-crisis.speaker", "time-crisis.front",
         "time-crisis.deck", "time-crisis.side"],
        ["pac-man.marquee", "pac-man.front", "pac-man.deck", "pac-man.side"]]
W = max(sum(int(CELL * G.ASPECT[k]) + 10 for k in r) for r in rows) + 10
out = Image.new("RGB", (W, len(rows) * (CELL + 10) + 10), (26, 26, 30))
y = 10
for r in rows:
    x = 10
    for k in r:
        i = keys.index(k)
        sub = im.crop(((i % 5) * tile, (i // 5) * tile,
                       (i % 5 + 1) * tile, (i // 5 + 1) * tile))
        w = int(CELL * G.ASPECT[k])
        out.paste(sub.resize((w, CELL), Image.LANCZOS), (x, y))
        x += w + 10
    y += CELL + 10
out.save(os.path.join(HERE, "preview_g1_at128.png"))
print("wrote preview_g1_at128.png")
