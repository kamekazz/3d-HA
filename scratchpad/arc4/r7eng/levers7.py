"""Round-7 payload levers, measured on the REAL three cabinet GLBs.

Unlike levers_r5.py (which summed the three packed atlas PNGs) this builds the
actual saved files, so geometry and atlas move together and the number is the
one the room's payload cap sees.

    $PY scratchpad/arc4/r7eng/levers7.py
"""
import os
import sys

_ROOT = r"C:\Users\Manuel\Desktop\Pro\3d HA"
for _p in (os.path.join(_ROOT, "tools"), os.path.join(_ROOT, "scratchpad", "bsmt"),
           os.path.join(_ROOT, "scratchpad", "arc4"),
           os.path.join(_ROOT, "scratchpad", "arc4", "art")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

OUT = os.path.join(_ROOT, "scratchpad", "arc4", "r7eng", "glb")
os.makedirs(OUT, exist_ok=True)
import bkit                                                   # noqa: E402
import atlas4                                                 # noqa: E402

_KB = []


def _snp(name, m, room, fname=None):
    path = os.path.join(OUT, "lever.glb")
    m.save(path)
    kb = os.path.getsize(path) / 1024.0
    _KB.append(kb)
    return {"name": name, "kb": kb, "tris": sum(len(p.tris) for p, _ in m._parts)}


bkit.save_and_place = _snp
import ar2                                                    # noqa: E402
ar2.save_and_place = _snp

BASE_SIZE = dict(atlas4.SIZE)
BASE_KEY = dict(atlas4.SIZE_KEY)
BASE_Q = atlas4.QUANT


def total(**kw):
    atlas4.SIZE.clear(); atlas4.SIZE.update(BASE_SIZE)
    atlas4.SIZE_KEY.clear(); atlas4.SIZE_KEY.update(BASE_KEY)
    atlas4.QUANT = BASE_Q
    for k, v in kw.items():
        if k == "quant":
            atlas4.QUANT = v
        elif k == "keys":
            atlas4.SIZE_KEY.update(v)
        else:
            atlas4.SIZE[k] = v
    atlas4._CACHE.clear()
    del _KB[:]
    for b in ("east", "south", "ncab"):
        ar2.BUILDERS[b]()
    return sum(_KB)


if __name__ == "__main__":
    base = total()
    print("%-52s %7.1f KB" % ("round-7 shipping settings", base))
    rows = [
        ("SIZE[front] 92 -> 86", dict(front=86)),
        ("SIZE[front] 92 -> 84", dict(front=84)),
        ("SIZE[marquee] 104 -> 96", dict(marquee=96)),
        ("SIZE[side] 58 -> 48", dict(side=48)),
        ("SIZE[side] 58 -> 44", dict(side=44)),
        ("SIZE[bezel] -> 28", dict(bezel=28)),
        ("SIZE[screen] -> 24", dict(screen=24)),
        ("QUANT 20 -> 22", dict(quant=22)),
        ("QUANT 20 -> 24", dict(quant=24)),
        ("art_g0 SIZE_KEY_REQUEST", dict(keys={
            "nba-jam.side": 40, "pac-man.side": 40, "pac-man.deck": 44,
            "golden-tee-3d-golf.deck": 48})),
        ("art_g2 SIZE_KEY_REQUEST", dict(keys={
            "marvel-super-heroes.side": 38, "marvel-vs-capcom.side": 38,
            "mortal-kombat.side": 38, "legends-ultimate.screen": 24,
            "street-fighter-2-champion-edition.screen": 24,
            "time-crisis.screen": 24, "terminator-2.screen": 24})),
    ]
    for label, kw in rows:
        t = total(**kw)
        print("%-52s %7.1f KB  (%+.1f)" % (label, t, t - base))
    print("-" * 62)
    print("SIZE table:", BASE_SIZE, "QUANT", BASE_Q)
