"""Every marquee in the room: is its ART inside its PANEL?

The quad in `ar2.upright` spans x0+0.06 .. x1-0.06 and takes `atlas.uv(
"<slug>.marquee")`, which is that panel's own packed rect with a HALF-TEXEL
inset.  So the mapping is 1:1 and cannot overscan -- what "ORTAL KOMBAT" was is
(a) type authored into the bleed, plus (b) the neighbouring cabinet's head
standing proud of a recessed 'step' marquee.  This prints, per marquee, the
clear margin between the tile edge and the first column carrying ink, as a
percentage of the panel width; a marquee with <5% is one occlusion away from
losing a letter.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
for p in (os.path.join(ROOT, "tools"), os.path.join(ROOT, "scratchpad", "bsmt"), HERE):
    sys.path.insert(0, p)
import ar2, atlas4
from atlas4 import Atlas, keys_for, EAST_SLUGS, SOUTH_SLUGS, NORTH_SLUGS

for run, slugs in (("east", EAST_SLUGS), ("south", SOUTH_SLUGS),
                   ("north", NORTH_SLUGS)):
    a = Atlas(keys_for(slugs))
    for s in slugs:
        k = s + ".marquee"
        w, h = atlas4.dims(k)
        u0, v0, u1, v1 = a.uv(k)
        span = (u1 - u0) * a.w
        t = atlas4.render(k, w, h)
        # column contrast against that column's own median: "ink" = a column
        # whose peak deviation from the panel's median luma exceeds 45
        lum = [[0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2] for c in row] for row in t]
        flat = sorted(v for row in lum for v in row)
        med = flat[len(flat) // 2]
        ink = [x for x in range(w)
               if max(abs(lum[y][x] - med) for y in range(h)) > 45]
        if not ink:
            l = r = None
        else:
            l, r = ink[0] / float(w), (w - 1 - ink[-1]) / float(w)
        print("%-6s %-36s %3dx%-3d texels  uv span %5.1f tx (%.1f%% of %d)   "
              "clear L %s  R %s"
              % (run, s, w, h, span, 100.0 * span / w, w,
                 "  --" if l is None else "%4.1f%%" % (100 * l),
                 "  --" if r is None else "%4.1f%%" % (100 * r)))
