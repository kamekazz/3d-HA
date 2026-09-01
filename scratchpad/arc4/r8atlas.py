import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
for p in (os.path.join(ROOT, "tools"), os.path.join(ROOT, "scratchpad", "bsmt"), HERE):
    sys.path.insert(0, p)
import ar2, atlas4          # ar2 import sets the true aspects
from atlas4 import Atlas, keys_for, EAST_SLUGS, SOUTH_SLUGS, NORTH_SLUGS

def total(label):
    atlas4._CACHE.clear()
    t = 0.0
    for n, sl in (("east", EAST_SLUGS), ("south", SOUTH_SLUGS), ("north", NORTH_SLUGS)):
        a = Atlas(keys_for(sl))
        t += len(a.png) / 1024.0
    print("%-40s %7.2f KB" % (label, t))
    return t

base = total("QUANT=%d as shipped" % atlas4.QUANT)
for q in (22, 24, 26):
    atlas4.QUANT = q
    total("QUANT=%d" % q)
atlas4.QUANT = 20
for k, v in (("side", 36), ("bezel", 28), ("screen", 24)):
    old = atlas4.SIZE[k]; atlas4.SIZE[k] = v
    total("SIZE[%s] %d -> %d" % (k, old, v))
    atlas4.SIZE[k] = old
