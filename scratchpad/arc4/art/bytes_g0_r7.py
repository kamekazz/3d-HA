"""Round-7 byte meter for art_g0's deck rewrite.

CAUTION, and this cost half an hour: the three wall-run atlases are NOT a
stable baseline while the other art agents are working -- the south atlas holds
no art_g0 panel at all and it moved 34.4 -> 37.0 KB between two runs of this
script.  So the attributable measurement is art_g0's OWN panels, packed alone,
with the round-6 backup and the round-7 module built in the same process.

    $PY scratchpad/arc4/art/bytes_g0_r7.py            four decks, R6 vs R7
    $PY scratchpad/arc4/art/bytes_g0_r7.py --all      all 17 art_g0 panels
"""
import importlib
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
for _p in (os.path.join(_ROOT, "tools"), os.path.join(_ROOT, "scratchpad", "bsmt"),
           os.path.join(_ROOT, "scratchpad", "arc4"), _HERE,
           os.path.join(_HERE, "_r5")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import ar2                                                   # noqa: E402,F401
import atlas4                                                # noqa: E402
from roomkit.glb import png_rgb                              # noqa: E402

SLUGS = ("pac-man", "nba-jam", "tmnt-turtles-in-time", "golden-tee-3d-golf")


def sheet(mod, panels):
    """Pack `panels` from `mod` at the sizes that ship, one row per panel."""
    tiles = []
    for k in panels:
        w, h = atlas4.dims(k)
        buf = [[(0, 0, 0)] * (max(w, h) * atlas4.SS)
               for _ in range(max(w, h) * atlas4.SS)]
        mod.PANELS[k](buf, 0, 0, max(w, h) * atlas4.SS)
        tiles.append(atlas4._box(buf, len(buf[0]), len(buf), w, h))
    width = max(len(t[0]) for t in tiles)
    px = []
    for t in tiles:
        for row in t:
            px.append(list(row) + [(0, 0, 0)] * (width - len(row)))
    return len(png_rgb(px)) / 1024.0, sum(len(t) * len(t[0]) for t in tiles)


if __name__ == "__main__":
    cls = ("marquee", "side", "front", "deck") if "--all" in sys.argv else ("deck",)
    new = importlib.import_module("art_g0")
    old = importlib.import_module("art_g0_r6.bak" if False else "art_g0_r6bak") \
        if os.path.exists(os.path.join(_HERE, "_r5", "art_g0_r6bak.py")) else None
    if old is None:
        import shutil
        shutil.copyfile(os.path.join(_HERE, "_r5", "art_g0_r6.bak.py"),
                        os.path.join(_HERE, "_r5", "art_g0_r6bak.py"))
        old = importlib.import_module("art_g0_r6bak")
    panels = [s + "." + c for s in SLUGS for c in cls
              if (s + "." + c) in new.PANELS and (s + "." + c) in old.PANELS]
    a, npx = sheet(old, panels)
    b, _ = sheet(new, panels)
    for k in panels:
        print("   %-34s %s texels" % (k, "x".join(map(str, atlas4.dims(k)))))
    print("round 6  %7.2f KB   round 7  %7.2f KB   delta %+.2f KB  (%d texels)"
          % (a, b, b - a, npx))
