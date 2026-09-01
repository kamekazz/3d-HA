import os, sys, json, struct
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
for p in (os.path.join(ROOT, "tools"), os.path.join(ROOT, "scratchpad", "bsmt"), HERE):
    sys.path.insert(0, p)
import ar2
out = {}
def fake(name, m, room, fname=None):
    g = {}
    for part, mt in m._parts:
        k = mt.name
        d = g.setdefault(k, [0, 0, mt])
        d[0] += len(part.verts) if part.smooth else len(part.tris) * 3
        d[1] += len(part.tris)
    rows = []
    for k, (nv, nt, mt) in g.items():
        wid = 24 + (4 if any(p.colors for p, mm in m._parts if mm.name == k) else 0) \
                 + (8 if any(p.uv for p, mm in m._parts if mm.name == k) else 0)
        rows.append((nv * wid + nt * 6, k, nv, nt))
    rows.sort(reverse=True)
    print("==", name)
    for b, k, nv, nt in rows:
        print("   %8.2f KB  %-22s %5d v %5d t" % (b / 1024.0, k, nv, nt))
    print("   %d prims, geometry ~%.1f KB" % (len(rows), sum(r[0] for r in rows) / 1024.0))
    return {"kb": 0}
ar2.save_and_place = fake
ar2.build_east_cabs(); ar2.build_south_cabs(); ar2.build_north_cabs()
