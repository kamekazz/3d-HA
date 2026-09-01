"""Is QUANT 22 safe?  It is the one lever that pays for round 7 outright
(-6.79 KB against my +5.5), and round 4 only ever measured 24, where it said
banding begins on a marquee.  22 was never tested.  This renders the panel
round 4 named -- a marquee, the hero surface -- plus the deck this round is
judged on, at 20 and at 22, and writes them side by side with the per-pixel
difference so a human can see whether a band appears.

    $PY scratchpad/arc4/art/quant22_g1_r7.py  ->  art/_r7/quant22.png
"""
import os
import sys

from PIL import Image, ImageDraw

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
for _p in (os.path.join(_ROOT, "tools"), os.path.join(_ROOT, "scratchpad", "bsmt"),
           os.path.join(_ROOT, "scratchpad", "arc4"), _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import ar2                                     # noqa: E402,F401
import atlas4                                  # noqa: E402

KEYS = ["marvel-super-heroes.marquee", "mortal-kombat.marquee",
        "nfl-blitz.marquee", "marvel-super-heroes.deck",
        "marvel-vs-capcom.deck", "mortal-kombat.deck", "nfl-blitz.deck"]


def grab(q):
    atlas4.QUANT = q
    atlas4._CACHE.clear()
    out = {}
    for k in KEYS:
        w, h = atlas4.dims(k)
        rows = atlas4.render(k, w, h)
        im = Image.new("RGB", (w, h))
        im.putdata([c for r in rows for c in r])
        out[k] = im
    return out


if __name__ == "__main__":
    a, b = grab(20), grab(22)
    atlas4.QUANT = 20
    S = 5
    W = max(a[k].width for k in KEYS) * S * 3 + 60
    H = sum(a[k].height * S + 28 for k in KEYS) + 30
    sheet = Image.new("RGB", (W, H), (16, 16, 20))
    d = ImageDraw.Draw(sheet)
    d.text((10, 8), "QUANT 20 (ships)   |   QUANT 22   |   10x abs difference",
           fill=(230, 232, 238))
    y = 28
    worst = 0
    for k in KEYS:
        ia, ib = a[k], b[k]
        diff = Image.new("RGB", ia.size)
        px = []
        for (p, q) in zip(ia.getdata(), ib.getdata()):
            dv = [min(255, abs(p[i] - q[i]) * 10) for i in range(3)]
            worst = max(worst, max(abs(p[i] - q[i]) for i in range(3)))
            px.append(tuple(dv))
        diff.putdata(px)
        d.text((10, y), k, fill=(255, 214, 120))
        y += 14
        for i, im in enumerate((ia, ib, diff)):
            sheet.paste(im.resize((im.width * S, im.height * S), Image.NEAREST),
                        (10 + i * (ia.width * S + 16), y))
        y += ia.height * S + 14
    out = os.path.join(_HERE, "_r7", "quant22.png")
    sheet.save(out)
    print("wrote", out, "worst per-channel step:", worst)
