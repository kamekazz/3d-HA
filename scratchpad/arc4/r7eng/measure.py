"""Build the three cabinet GLBs WITHOUT touching the DB, and report bytes.

    $PY scratchpad/arc4/r7eng/measure.py
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


def _fake_place(name, path, room, **kw):
    return {"action": "measured"}


bkit.place = _fake_place
_real_snp = bkit.save_and_place


def _snp(name, m, room, fname=None):
    path = os.path.join(OUT, (fname or name.replace(" ", "_")) + ".glb")
    m.save(path)
    kb = os.path.getsize(path) / 1024.0
    tris = sum(len(p.tris) for p, _ in m._parts)
    prims = len({id(mat) for _, mat in m._parts})
    print("  %-26s %8.1f KB  %6d tris  %2d materials" % (name, kb, tris, prims))
    return {"name": name, "kb": round(kb, 1), "tris": tris, "mats": prims}


bkit.save_and_place = _snp
import ar2                                                    # noqa: E402
ar2.save_and_place = _snp

if __name__ == "__main__":
    which = sys.argv[1:] or ["east", "south", "north"]
    tot = 0.0
    tt = 0
    for k in which:
        r = ar2.BUILDERS[k]()
        tot += r["kb"]
        tt += r["tris"]
    print("  %-26s %8.1f KB  %6d tris" % ("THREE CABINET PIECES", tot, tt))
