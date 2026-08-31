"""What round 5's art_g0 costs, isolated from the other three agents.

Two builds, because the other three modules are being rewritten in parallel and
a "current merged total" is a moving target:

  ISOLATED   every machine except art_g0's four is round FOUR (from the
             vendored backups r4mq/g1.py, art_g2_r4.bak.py, art_g3_r4.bak.py,
             plus art_g0.LEGACY_R4 for the three machines art_g0 drew in round
             4 and handed over in round 5).  Compared against round 4's
             measured 73.8 / 47.8 / 41.5 KB, the delta IS art_g0's bill.
  LIVE       whatever art_g1..g3 hold on disk right now, if they are complete.

    $PY scratchpad/arc4/art/bytes_g0_r5.py
"""

import importlib.util
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ARC4 = os.path.abspath(os.path.join(_HERE, ".."))
_TOOLS = os.path.abspath(os.path.join(_ARC4, "..", "..", "tools"))
for _p in (_TOOLS, _ARC4, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import art_g0                                              # noqa: E402
import atlas4                                              # noqa: E402

ROUND4_KB = {"east": 73.8, "south": 47.8, "north": 41.5}


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build(label, panels):
    atlas4.PANELS = panels
    atlas4._CACHE.clear()
    tot = old = 0.0
    print(label)
    for name in ("east", "south", "north"):
        a = getattr(atlas4, name)()
        kb = len(a.png) / 1024.0
        tot += kb
        old += ROUND4_KB[name]
        print("  %-6s %4dx%-4d %2d panels  %6.1f KB   round4 %5.1f  %+6.1f"
              % (name, a.w, a.h, len(a.rects), kb, ROUND4_KB[name],
                 kb - ROUND4_KB[name]))
    print("  TOTAL %.1f KB   round4 %.1f   delta %+.1f KB" % (tot, old,
                                                              tot - old))
    return tot


def main():
    r4 = {}
    for path in (os.path.join(_HERE, "r4mq", "g1.py"),
                 os.path.join(_HERE, "art_g2_r4.bak.py"),
                 os.path.join(_HERE, "art_g3_r4.bak.py")):
        m = _load("r4_" + os.path.basename(path).split(".")[0], path)
        r4.update(m.PANELS)
    r4.update(art_g0.LEGACY_R4)          # star-wars / SF2 / multicade, round 4

    iso = dict(r4)
    iso.update(art_g0.PANELS)            # art_g0's four, ROUND 5
    build("ISOLATED  (art_g0 round 5, everyone else round 4)", iso)

    print()
    import art_g1
    import art_g2
    import art_g3
    live = {}
    for m in (art_g1, art_g2, art_g3, art_g0):
        live.update(m.PANELS)
    missing = [k for s in (atlas4.EAST_SLUGS + atlas4.SOUTH_SLUGS +
                           atlas4.NORTH_SLUGS)
               for k in ("%s.%s" % (s, p) for p in atlas4.CORE)
               if k not in live]
    if missing:
        print("LIVE build is incomplete -- no module claims: %s" %
              ", ".join(sorted(set(m.split(".")[0] for m in missing))))
        for k in missing:
            live[k] = r4[k]
        print("          filled from the round-4 backups for this measurement")
    build("LIVE      (art_g1..g3 as they stand on disk)", live)

    print()
    print("art_g0's own panels, as packed:")
    atlas4.PANELS = iso
    atlas4._CACHE.clear()
    for k in sorted(art_g0.PANELS):
        n = atlas4.size_of(k)
        rows = atlas4.render(k, n)
        px = [sum(c) / 3.0 for r in rows for c in r]
        m = sum(px) / len(px)
        sd = (sum((v - m) ** 2 for v in px) / len(px)) ** 0.5
        d1 = cnt = 0
        for r in rows:
            for i in range(len(r) - 1):
                d1 += abs(sum(r[i]) - sum(r[i + 1])) / 3.0
                cnt += 1
        print("  %-36s %3dpx  mean %6.1f  sd %5.1f  |d1| %5.2f"
              % (k, n, m, sd, d1 / max(1, cnt)))


if __name__ == "__main__":
    main()
