"""Round-7 payload levers art_g0 can offer from INSIDE its own four panels.
Each row rebuilds all three wall-run atlases for real."""
import os, sys
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
for _p in (os.path.join(_ROOT, "tools"), os.path.join(_ROOT, "scratchpad", "bsmt"),
           os.path.join(_ROOT, "scratchpad", "arc4"), _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import ar2   # noqa
import atlas4  # noqa

BASE = dict(atlas4.SIZE_KEY)

def total():
    atlas4._CACHE.clear()
    return sum(len(f().png) for f in (atlas4.east, atlas4.south, atlas4.north)) / 1024.0

def run(label, **keys):
    atlas4.SIZE_KEY.clear(); atlas4.SIZE_KEY.update(BASE)
    atlas4.SIZE_KEY.update(keys)
    t = total()
    print("%-52s %7.2f KB" % (label, t))
    return t

if __name__ == "__main__":
    b = run("round 7 as it stands")
    for k, v in (("pac-man.deck", 46), ("pac-man.deck", 42),
                 ("golden-tee-3d-golf.deck", 46)):
        t = run("SIZE_KEY[%s] = %d" % (k, v), **{k: v})
        print("%54s %+.2f" % ("", t - b))
    t = run("BOTH: pac-man.deck 44 + golden-tee-3d-golf.deck 48",
            **{"pac-man.deck": 44, "golden-tee-3d-golf.deck": 48})
    print("%54s %+.2f" % ("", t - b))
