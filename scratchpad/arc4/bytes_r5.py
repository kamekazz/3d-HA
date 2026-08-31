"""Round-5 payload accounting for room 2 -- where every byte of the three
cabinet GLBs goes, split into ATLAS bytes and GEOMETRY bytes.

Run it with the venv python from anywhere:
    $PY scratchpad/arc4/bytes_r5.py
"""
import os
import sys
from collections import Counter

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
for _p in (os.path.join(_ROOT, "tools"), os.path.join(_ROOT, "scratchpad", "bsmt"),
           _HERE, os.path.join(_HERE, "art")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import ar2                                                   # noqa: E402
import atlas4                                                # noqa: E402
from a2kit import ArtSet                                     # noqa: E402
from bkit import Model                                       # noqa: E402
from roomkit.glb import Model as _M                          # noqa: E402,F401

RUNS = (("east", ar2.EAST_RUN, atlas4.EAST_SLUGS, ar2.W - 1.32, 270),
        ("south", ar2.SOUTH_RUN, atlas4.SOUTH_SLUGS, None, 180),
        ("north", ar2.NORTH_RUN, atlas4.NORTH_SLUGS, None, 0))


def main():
    tot_atlas = tot_geo = 0
    tris = verts = 0
    print("%-8s %8s %8s %8s   %s" % ("run", "atlas", "geom", "prims", "size"))
    for name, run, slugs, _, rot in RUNS:
        art = ArtSet(name, slugs)
        akb = len(art.atlas.png) / 1024.0
        m = Model()
        for i, (z, bw, top, st, dy, mqh, slug, pl) in enumerate(run):
            ar2.upright(m, 0.0, i * 3.0, 0, art, slug, bw=bw, bd=2.55, top=top,
                        seed=i + 1, style=st, dy=dy, mqh=mqh, plinth=pl)
        p = os.path.join(_HERE, "_bytes_%s.glb" % name)
        m.save(p)
        kb = os.path.getsize(p) / 1024.0
        mats = Counter()
        for part, mat in m._parts:
            mats[mat.name] += 1
            tris += len(part.tris)
            verts += len(part.verts)
        os.remove(p)
        tot_atlas += akb
        tot_geo += kb - akb
        print("%-8s %7.1fK %7.1fK %8d   %dx%d  (%d panels)"
              % (name, akb, kb - akb, len(mats), art.atlas.w, art.atlas.h,
                 len(art.atlas.rects)))
    print("-" * 52)
    print("cabinets only:  atlas %.1f KB + geometry %.1f KB = %.1f KB"
          % (tot_atlas, tot_geo, tot_atlas + tot_geo))
    print("%d verts, %d triangles across the three runs" % (verts, tris))


if __name__ == "__main__":
    main()
