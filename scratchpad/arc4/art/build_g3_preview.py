"""Rebuild the three arcade cabinet runs and shoot the judged frames.

WHY THIS EXISTS.  Round 5 has four art agents editing four modules at once, and
at the moment g3 finished, `atlas4.keys_for()` raised on
`east-7-no-machine.marquee` -- that machine's four panels are somewhere in
another agent's in-flight edit, so the shared build could not run at all and no
in-scene check of g3's artwork was possible.

Rather than edit another agent's module or atlas4 (out of scope), this script
injects a plain unbranded dark panel for any CORE key no module currently
paints, builds ONLY the three cabinet runs (`ar2.py east south ncab`, which is
idempotent), and shoots.  The placeholder is exactly what the roster says that
slot should be -- "an honest unbranded black upright with no licensed
artwork" -- so nothing is invented by it; it is still a placeholder and the
integrator's own rebuild replaces it.

    $PY scratchpad/arc4/art/build_g3_preview.py [prefix]
"""
import os
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ARC4 = os.path.dirname(_HERE)
_ROOT = os.path.dirname(os.path.dirname(_ARC4))
for _p in (_ARC4, _HERE, os.path.join(_ROOT, "tools"),
           os.path.join(_ROOT, "scratchpad", "bsmt")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import atlas4                                                   # noqa: E402


def _placeholder(px, ox, oy, tile):
    """A plain unbranded dark upright panel: a slow vertical gradient and a
    pair of retainer rails.  No graphic, no title."""
    for y in range(tile):
        k = y / float(max(1, tile - 1))
        v = int(30 + 14 * (1.0 - k))
        if k < 0.05 or k > 0.95:
            v = 18
        px[oy + y][ox:ox + tile] = [(v, v, v + 4)] * tile


def patch():
    added = []
    for slugs in (atlas4.EAST_SLUGS, atlas4.SOUTH_SLUGS, atlas4.NORTH_SLUGS):
        for s in slugs:
            for p in atlas4.CORE:
                k = "%s.%s" % (s, p)
                if k not in atlas4.PANELS:
                    atlas4.PANELS[k] = _placeholder
                    added.append(k)
    return added


def main():
    prefix = sys.argv[1] if len(sys.argv) > 1 else "g3"
    added = patch()
    if added:
        print("PLACEHOLDER injected for %d key(s) no module paints right now:"
              % len(added))
        for k in added:
            print("   ", k)
    import ar2
    for name in ("east", "south", "ncab"):
        r = ar2.BUILDERS[name]()
        print("%-6s -> %.1f KB" % (name, r.get("kb", 0)))
    sys.argv = [sys.argv[0], prefix, "mq_east", "mq_north", "mq_south"]
    shoot = os.path.join(_ARC4, "shoot4.py")
    subprocess.run([sys.executable, shoot, prefix,
                    "mq_east", "mq_north", "mq_south"], check=False)


if __name__ == "__main__":
    main()
