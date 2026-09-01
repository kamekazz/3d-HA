import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
for p in (os.path.join(ROOT, "tools"), os.path.join(ROOT, "scratchpad", "bsmt"), HERE):
    sys.path.insert(0, p)
import ar2, atlas4
from atlas4 import Atlas, keys_for, EAST_SLUGS, SOUTH_SLUGS, NORTH_SLUGS

def total(label):
    atlas4._CACHE.clear()
    t = sum(len(Atlas(keys_for(sl)).png) / 1024.0
            for sl in (EAST_SLUGS, SOUTH_SLUGS, NORTH_SLUGS))
    print("%-46s %7.2f KB" % (label, t))
    return t

# area share by class
from collections import Counter
c = Counter()
for sl in (EAST_SLUGS, SOUTH_SLUGS, NORTH_SLUGS):
    for k in keys_for(sl):
        w, h = atlas4.dims(k)
        c[k.split(".")[-1]] += w * h
tot = sum(c.values())
for k, v in c.most_common():
    print("   %-10s %6d px  %4.1f%%" % (k, v, 100.0 * v / tot))
total("mq/front 20, rest 28  (current)")
for rest in (32, 36):
    atlas4.QUANT_REST = rest; total("rest %d" % rest)
atlas4.QUANT_REST = 28
for f in (22, 24):
    atlas4.QUANT_CLS["front"] = f; total("front %d, rest 28" % f)
atlas4.QUANT_CLS["front"] = 20
for mq in (22, 24):
    atlas4.QUANT_CLS["marquee"] = mq; total("marquee %d, front 20, rest 28" % mq)
atlas4.QUANT_CLS["marquee"] = 20
