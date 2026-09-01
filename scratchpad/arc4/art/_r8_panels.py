# -*- coding: utf-8 -*-
"""Quick look: every art_g2 panel drawn at 256 and stretched to its true
aspect, so a repeated wordmark or a painted border is visible.

    $PY scratchpad/arc4/art/_r8_panels.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from PIL import Image, ImageDraw  # noqa: E402
import art_g2  # noqa: E402

SLUGS = ["legends-ultimate", "street-fighter-2-champion-edition",
         "time-crisis", "terminator-2"]
CLS = ["marquee", "front", "side", "deck"]
H = 240


def paint(key, n=256):
    buf = [[(0, 0, 0)] * n for _ in range(n)]
    art_g2.PANELS[key](buf, 0, 0, n)
    im = Image.new("RGB", (n, n))
    im.putdata([c for r in buf for c in r])
    return im


rows = []
for s in SLUGS:
    row = []
    for c in CLS:
        a = art_g2.A[s][c]
        im = paint("%s.%s" % (s, c))
        row.append((c, im.resize((max(24, int(H * a)), H), Image.LANCZOS)))
    rows.append((s, row))

pad, lab = 14, 22
W = pad + max(sum(im.width + pad for _, im in r) for _, r in rows)
HT = pad + sum(H + lab + pad for _ in rows) + 30
out = Image.new("RGB", (W, HT), (16, 16, 18))
d = ImageDraw.Draw(out)
d.text((pad, 6), "art_g2 panels at 256, stretched to true aspect "
       "(marquee / front / side / deck)", fill=(210, 210, 210))
y = 30
for s, r in rows:
    d.text((pad, y), s.upper(), fill=(180, 200, 230))
    x = pad
    for c, im in r:
        out.paste(im, (x, y + lab))
        d.text((x, y + lab + H + 2), c, fill=(150, 150, 150))
        x += im.width + pad
    y += H + lab + pad
p = os.path.join(HERE, "_r8_panels.png")
out.save(p)
print("wrote", p, out.size)
