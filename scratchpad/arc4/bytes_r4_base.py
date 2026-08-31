"""The ROUND-4 baseline, measured the same way as bytes_r5.py.

Loads `atlas4_r4.bak.py` as `atlas4` and `ar2_r4.bak.py` as `ar2` (both saved
before round 5 touched anything), so the two numbers are like for like: the
same three runs, the same cabinets, the same measuring code.  The ART is round
5's either way -- the art modules were rewritten by four agents before this
round's integration started and round 4's paint functions no longer exist for
most machines -- so what this isolates is the PACKING and the GEOMETRY.
"""
import importlib.util
import os
import sys
from collections import Counter

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
for _p in (os.path.join(_ROOT, "tools"), os.path.join(_ROOT, "scratchpad", "bsmt"),
           _HERE, os.path.join(_HERE, "art")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


atlas4 = _load("atlas4", os.path.join(_HERE, "atlas4_r4.bak.py"))
from a2kit import ArtSet                                     # noqa: E402
from bkit import Model                                       # noqa: E402
ar2 = _load("ar2", os.path.join(_ROOT, "scratchpad", "bsmt", "ar2_r4.bak.py"))

# round 4's atlas4 raises on `east-7-no-machine`, which no round-5 art module
# paints; fall its four panels back to art_g2's round-4 originals so the
# baseline can be built at all.
import art_g2                                                # noqa: E402
for _k, _fn in art_g2.LEGACY_PANELS.items():
    atlas4.PANELS.setdefault(_k, _fn)

RUNS = (("east", ar2.EAST_RUN, atlas4.EAST_SLUGS),
        ("south", ar2.SOUTH_RUN, atlas4.SOUTH_SLUGS),
        ("north", ar2.NORTH_RUN, atlas4.NORTH_SLUGS))

tot_a = tot_g = 0
tris = 0
print("ROUND-4 geometry + round-4 SQUARE packing")
print("%-8s %8s %8s %8s" % ("run", "atlas", "geom", "prims"))
for name, run, slugs in RUNS:
    art = ArtSet(name, slugs)
    akb = len(art.atlas.png) / 1024.0
    m = Model()
    for i, (z, bw, top, st, dy, mqh, slug, pl) in enumerate(run):
        ar2.upright(m, 0.0, i * 3.0, 0, art, slug, bw=bw, bd=2.55, top=top,
                    seed=i + 1, style=st, dy=dy, mqh=mqh, plinth=pl)
    p = os.path.join(_HERE, "_b4_%s.glb" % name)
    m.save(p)
    kb = os.path.getsize(p) / 1024.0
    os.remove(p)
    mats = Counter(mat.name for _, mat in m._parts)
    tris += sum(len(pt.tris) for pt, _ in m._parts)
    tot_a += akb
    tot_g += kb - akb
    print("%-8s %7.1fK %7.1fK %8d" % (name, akb, kb - akb, len(mats)))
print("-" * 40)
print("atlas %.1f KB + geometry %.1f KB = %.1f KB, %d tris"
      % (tot_a, tot_g, tot_a + tot_g, tris))
