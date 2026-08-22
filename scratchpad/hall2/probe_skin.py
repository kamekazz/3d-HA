import json, struct, sys

p = r"C:\Users\Manuel\Desktop\Pro\3d HA\backend\uploads\models\model_256.glb"
d = open(p, "rb").read()
ln = struct.unpack("<I", d[12:16])[0]
j = json.loads(d[20:20 + ln])
boff = 20 + ln + 8
M = 3.28084
FMT = {5121: ("B", 1), 5123: ("H", 2), 5125: ("I", 4), 5126: ("f", 4)}


def read(ai):
    a = j["accessors"][ai]
    bv = j["bufferViews"][a["bufferView"]]
    off = boff + bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    f, sz = FMT[a["componentType"]]
    ncomp = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[a["type"]]
    stride = bv.get("byteStride") or sz * ncomp
    return [struct.unpack_from("<%d%s" % (ncomp, f), d, off + stride * i)
            for i in range(a["count"])]


def cover(key, ax, ay, samples, filt=None):
    for mesh in j["meshes"]:
        for pr in mesh["primitives"]:
            name = j["materials"][pr["material"]]["name"]
            if key not in name:
                continue
            P = [(v[0] * M, v[1] * M, v[2] * M) for v in read(pr["attributes"]["POSITION"])]
            I = [t[0] for t in read(pr["indices"])]
            n = len(I) // 3
            print("== %s  %d tris" % (name, n))
            for (sx, sy) in samples:
                hit = 0
                for i in range(n):
                    a, b, c = P[I[3 * i]], P[I[3 * i + 1]], P[I[3 * i + 2]]
                    if filt and not (filt(a) and filt(b) and filt(c)):
                        continue
                    ua, ub, uc = (a[ax], a[ay]), (b[ax], b[ay]), (c[ax], c[ay])
                    d1 = (ub[0] - ua[0]) * (sy - ua[1]) - (ub[1] - ua[1]) * (sx - ua[0])
                    d2 = (uc[0] - ub[0]) * (sy - ub[1]) - (uc[1] - ub[1]) * (sx - ub[0])
                    d3 = (ua[0] - uc[0]) * (sy - uc[1]) - (ua[1] - uc[1]) * (sx - uc[0])
                    if (d1 >= 0 and d2 >= 0 and d3 >= 0) or (d1 <= 0 and d2 <= 0 and d3 <= 0):
                        hit += 1
                print("   (%6.2f,%6.2f) -> %s" % (sx, sy, "COVERED x%d" % hit if hit else "open"))


import os, datetime
print(datetime.datetime.fromtimestamp(os.path.getmtime(p)), [m["name"] for m in j["materials"]])
for mesh in j["meshes"]:
    for pr in mesh["primitives"]:
        a = j["accessors"][pr["attributes"]["POSITION"]]
        print("  ", j["materials"][pr["material"]]["name"],
              [round(v * M, 3) for v in a["min"]], [round(v * M, 3) for v in a["max"]])
for k in [m["name"] for m in j["materials"]]:
    print("### SOUTH wall skin only (z>16.4), sampled in (x,y)  -- bath door x 0.90..3.70")
    cover(k, 0, 1, [(2.30, 3.0), (1.10, 1.5), (3.50, 6.0), (0.50, 3.0)],
          filt=lambda v: v[2] > 16.4)
    print("### WEST wall skin only (x<0.20), sampled in (z,y)"
          "  -- doors z 7.95-10.68 / 11.25-13.40 / 13.98-16.38")
    cover(k, 2, 1, [(9.30, 3.0), (12.30, 3.0), (15.20, 3.0), (5.00, 3.0), (11.0, 3.0)],
          filt=lambda v: v[0] < 0.20)
    print("### NORTH wall skin only (z<0.20), sampled in (x,y)  -- master door x 4.05..6.95")
    cover(k, 0, 1, [(5.50, 3.0), (2.00, 3.0)], filt=lambda v: v[2] < 0.20)
