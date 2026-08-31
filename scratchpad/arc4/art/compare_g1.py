"""My panel over the photo crop of the same printed artwork, side by side."""
import os
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from PIL import Image                                           # noqa: E402
import art_g1 as G                                              # noqa: E402

C = os.path.join(HERE, "crops")
PAIRS = [
    ("pac-man.marquee", os.path.join(C, "pac_marq.png"),
     "v4 6 px (268,118)-(330,155)"),
    ("time-crisis.marquee", os.path.join(C, "tc_marq.png"),
     "v4 4 px (0,80)-(90,130)"),
    ("tmnt-turtles-in-time.marquee", os.path.join(C, "tm_marq.png"),
     "v4 7 px (460,160)-(600,240)"),
    ("marvel-super-heroes.front", os.path.join(C, "msh_front.png"),
     "v3 4 nearleft, front panel"),
    ("tmnt-turtles-in-time.front", os.path.join(C, "tm_front.png"),
     "v3 4 farend, front panel"),
    ("pac-man.front", os.path.join(C, "pac_all.png"),
     "v4 6 px (262,112)-(335,285)"),
]

TILE = 256
H = 200
GAP = 12
cells = []
for key, path, _ in PAIRS:
    px = [[(0, 0, 0)] * TILE for _ in range(TILE)]
    G.PANELS[key](px, 0, 0, TILE)
    mine = Image.new("RGB", (TILE, TILE))
    mine.putdata([p for row in px for p in row])
    mine = mine.resize((int(H * G.ASPECT[key]), H), Image.LANCZOS)
    ph = Image.open(path).convert("RGB")
    ph = ph.resize((int(H * ph.width / ph.height), H), Image.LANCZOS)
    cells.append((mine, ph))

W = max(m.width + p.width + GAP for m, p in cells) + GAP * 2
sheet = Image.new("RGB", (W, len(cells) * (H + GAP) + GAP), (24, 24, 28))
y = GAP
for m, p in cells:
    sheet.paste(m, (GAP, y))
    sheet.paste(p, (GAP + m.width + GAP, y))
    y += H + GAP
sheet.save(os.path.join(HERE, "compare_g1.png"))
print("wrote compare_g1.png  (mine left, photo right)")
for k, _, ev in PAIRS:
    print("  %-32s %s" % (k, ev))
