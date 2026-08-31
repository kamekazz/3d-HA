"""Payload levers for round 5, measured on the real three atlases.

Every row is the sum of the three packed wall-run atlases, built for real.
Geometry is unaffected by any of these, so the room delta is the atlas delta.

    $PY scratchpad/arc4/levers_r5.py
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
for _p in (os.path.join(_ROOT, "tools"), os.path.join(_ROOT, "scratchpad", "bsmt"),
           _HERE, os.path.join(_HERE, "art")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import ar2                     # noqa: E402,F401  (pushes the true aspects)
import atlas4                  # noqa: E402


def total():
    atlas4._CACHE.clear()
    return sum(len(f().png) for f in (atlas4.east, atlas4.south,
                                      atlas4.north)) / 1024.0


BASE_SIZE = dict(atlas4.SIZE)
BASE_Q = atlas4.QUANT
BASE_KEY = dict(atlas4.SIZE_KEY)


def run(label, **kw):
    atlas4.SIZE.update(BASE_SIZE)
    atlas4.SIZE_KEY.clear()
    atlas4.SIZE_KEY.update(BASE_KEY)
    atlas4.QUANT = BASE_Q
    for k, v in kw.items():
        if k == "quant":
            atlas4.QUANT = v
        elif k == "sidekeys":
            for s in v:
                atlas4.SIZE_KEY[s] = v[s]
        else:
            atlas4.SIZE[k] = v
    t = total()
    print("%-46s %7.1f KB" % (label, t))
    return t


if __name__ == "__main__":
    base = run("shipping settings")
    run("QUANT 16 -> 20", quant=20)
    run("QUANT 16 -> 24", quant=24)
    run("SIZE[side] 58 -> 48", side=48)
    run("SIZE[front] 92 -> 84", front=84)
    run("SIZE[marquee] 104 -> 96", marquee=96)
    run("SIZE[deck] 52 -> 46", deck=46)
    print("-" * 56)
    atlas4.SIZE.update(BASE_SIZE)
    atlas4.QUANT = 20
    atlas4.SIZE["side"] = 48
    c = total()
    print("%-46s %7.1f KB  (%+.1f)" % ("COMBO  QUANT 20 + side 48", c, c - base))
    atlas4.SIZE["front"] = 86
    c = total()
    print("%-46s %7.1f KB  (%+.1f)" % ("  + front 86", c, c - base))
    atlas4.QUANT = 24
    c = total()
    print("%-46s %7.1f KB  (%+.1f)" % ("  + QUANT 24", c, c - base))
