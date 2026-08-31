import os, sys, time
_R = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..","..",".."))
for p in (os.path.join(_R,"tools"), os.path.join(_R,"scratchpad","bsmt"),
          os.path.join(_R,"scratchpad","arc4"), os.path.join(_R,"scratchpad","arc4","art")):
    if p not in sys.path: sys.path.insert(0,p)
import ar2, atlas4
def tot():
    atlas4._CACHE.clear()
    return sum(len(f().png) for f in (atlas4.east, atlas4.south, atlas4.north))/1024.
B=dict(atlas4.SIZE)
base=tot(); print("base %.2f KB"%base); sys.stdout.flush()
for lbl,kw in (("screen 40->28",{"screen":28}),
               ("bezel 40->32",{"bezel":32}),
               ("screen28+bezel32",{"screen":28,"bezel":32})):
    atlas4.SIZE.update(B); atlas4.SIZE.update(kw)
    t=tot(); print("  %-20s %.2f KB  (%+.2f)"%(lbl,t,t-base)); sys.stdout.flush()
