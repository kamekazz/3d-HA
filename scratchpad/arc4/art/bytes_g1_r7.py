"""Round-7 payload accounting for art_g1's four decks.

    $PY scratchpad/arc4/art/bytes_g1_r7.py

Measures the three packed wall-run atlases for real, swapping ONE deck panel
at a time back to the round-6 drawing, so every number below is a measured
delta and not an estimate.  Geometry is untouched by anything in this file, so
the atlas delta IS the room delta.
"""
import importlib
import os
import shutil
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
for _p in (os.path.join(_ROOT, "tools"), os.path.join(_ROOT, "scratchpad", "bsmt"),
           os.path.join(_ROOT, "scratchpad", "arc4"), _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import ar2                                        # noqa: E402,F401
import atlas4                                     # noqa: E402
import art_g1                                     # noqa: E402

# the round-6 module, imported under its own name so both live at once
_BAK = os.path.join(_HERE, "art_g1_r6.bak.py")
_tmp = os.path.join(tempfile.gettempdir(), "art_g1_r6_probe.py")
shutil.copyfile(_BAK, _tmp)
sys.path.insert(0, os.path.dirname(_tmp))
old = importlib.import_module("art_g1_r6_probe")

SLUGS = ("marvel-super-heroes", "marvel-vs-capcom", "mortal-kombat",
         "nfl-blitz")


def total():
    atlas4._CACHE.clear()
    return sum(len(f().png) for f in (atlas4.east, atlas4.south,
                                      atlas4.north)) / 1024.0


NEW = dict((s + ".deck", art_g1.PANELS[s + ".deck"]) for s in SLUGS)
OLD = dict((s + ".deck", old.PANELS[s + ".deck"]) for s in SLUGS)

if __name__ == "__main__":
    for k in OLD:
        atlas4.PANELS[k] = OLD[k]
    base = total()
    print("%-46s %7.1f KB" % ("round 6 decks (all four)", base))
    for k in sorted(NEW):
        for kk in OLD:
            atlas4.PANELS[kk] = OLD[kk]
        atlas4.PANELS[k] = NEW[k]
        t = total()
        print("%-46s %7.1f KB  (%+.2f)" % ("  + round 7 " + k, t, t - base))
    for k in NEW:
        atlas4.PANELS[k] = NEW[k]
    allnew = total()
    print("%-46s %7.1f KB  (%+.2f)" % ("round 7 decks (all four)", allnew,
                                       allnew - base))

    print("-" * 60)
    print("levers, measured against round 7 art:")
    for lbl, key, v in (("SIZE[screen] 28 -> 24", "screen", 24),
                        ("SIZE[bezel]  32 -> 28", "bezel", 28),
                        ("SIZE[side]   42 -> 38", "side", 38),
                        ("SIZE[riser]  58 -> 52", "riser", 52),
                        ("SIZE[deck]   52 -> 48", "deck", 48),
                        ("SIZE[front]  92 -> 88", "front", 88)):
        keep = atlas4.SIZE[key]
        atlas4.SIZE[key] = v
        t = total()
        atlas4.SIZE[key] = keep
        print("  %-42s %7.1f KB  (%+.2f)" % (lbl, t, t - allnew))
    keep = dict(atlas4.SIZE)
    atlas4.SIZE["screen"] = 24
    atlas4.SIZE["bezel"] = 28
    atlas4.SIZE["side"] = 38
    atlas4.SIZE["riser"] = 52
    t = total()
    print("  %-42s %7.1f KB  (%+.2f)" % ("COMBO of the four above", t,
                                         t - allnew))
    atlas4.SIZE.update(keep)
