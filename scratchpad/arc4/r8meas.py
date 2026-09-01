"""Measure the three cabinet GLBs without touching the DB.

    $PY scratchpad/arc4/r8meas.py <tag>
"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "scratchpad", "bsmt"))
sys.path.insert(0, HERE)

OUT = os.path.join(HERE, "r8", "meas")
os.makedirs(OUT, exist_ok=True)
tag = sys.argv[1] if len(sys.argv) > 1 else "x"

import ar2

def fake_save(name, m, room, fname=None):
    path = os.path.join(OUT, "%s_%s.glb" % (tag, name.replace(" ", "_")))
    m.save(path)
    kb = os.path.getsize(path) / 1024.0
    tris = sum(len(p.tris) for p, _ in m._parts)
    prims = len({mt.key() for _, mt in m._parts})
    print("%-26s %8.2f KB  %6d tris  %3d prims" % (name, kb, tris, prims))
    return {"name": name, "kb": kb, "tris": tris, "prims": prims}

ar2.save_and_place = fake_save
res = [ar2.build_east_cabs(), ar2.build_south_cabs(), ar2.build_north_cabs()]
print("TOTAL %.2f KB" % sum(r["kb"] for r in res))
json.dump(res, open(os.path.join(OUT, tag + ".json"), "w"), indent=1)
