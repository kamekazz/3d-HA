"""Measured payload levers for round 7, on the round-7 art, all three atlases.

    $PY scratchpad/arc4/art/levers_g1_r7.py

Round 7's four rewritten control decks cost the room real bytes -- the
artwork on them went from four near-empty tinted planes to four printed
panels -- and ROOM-BRIEF forbids paying for that by deleting content.  So this
is the alternative: fidelity dials on the panel classes that carry the LEAST
information, each one measured rather than guessed, for whoever integrates.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
for _p in (os.path.join(_ROOT, "tools"), os.path.join(_ROOT, "scratchpad", "bsmt"),
           os.path.join(_ROOT, "scratchpad", "arc4"), _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import ar2                                     # noqa: E402,F401
import atlas4                                  # noqa: E402

BASE_SIZE = dict(atlas4.SIZE)
BASE_Q = atlas4.QUANT


def total():
    atlas4._CACHE.clear()
    return sum(len(f().png) for f in (atlas4.east, atlas4.south,
                                      atlas4.north)) / 1024.0


def run(label, base=None, **kw):
    atlas4.SIZE.update(BASE_SIZE)
    atlas4.QUANT = BASE_Q
    for k, v in kw.items():
        if k == "quant":
            atlas4.QUANT = v
        else:
            atlas4.SIZE[k] = v
    t = total()
    d = "" if base is None else "  (%+.2f)" % (t - base)
    print("%-44s %7.1f KB%s" % (label, t, d))
    atlas4.SIZE.update(BASE_SIZE)
    atlas4.QUANT = BASE_Q
    return t


if __name__ == "__main__":
    b = run("round 7, shipping settings")
    run("SIZE[side]    42 -> 36", b, side=36)
    run("SIZE[front]   92 -> 88", b, front=88)
    run("SIZE[marquee] 102 -> 98", b, marquee=98)
    run("SIZE[screen]  28 -> 24", b, screen=24)
    run("SIZE[bezel]   32 -> 28", b, bezel=28)
    run("SIZE[riser]   58 -> 50", b, riser=50)
    run("QUANT         20 -> 22", b, quant=22)
    print("-" * 62)
    run("COMBO  side 36 + screen 24 + bezel 28", b,
        side=36, screen=24, bezel=28)
    run("  + front 88", b, side=36, screen=24, bezel=28, front=88)
    run("  + front 88 + marquee 98", b, side=36, screen=24, bezel=28,
        front=88, marquee=98)
