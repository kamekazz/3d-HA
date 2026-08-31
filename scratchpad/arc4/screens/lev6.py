import os, sys, time
_R = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
for p in (os.path.join(_R,"tools"), os.path.join(_R,"scratchpad","bsmt"),
          os.path.join(_R,"scratchpad","arc4"), os.path.join(_R,"scratchpad","arc4","art")):
    if p not in sys.path: sys.path.insert(0,p)
import ar2, atlas4
def south():
    atlas4._CACHE.clear()
    return len(atlas4.south().png)/1024.
B=dict(atlas4.SIZE)
for v in (40,32,28,24):
    atlas4.SIZE.update(B); atlas4.SIZE["screen"]=v
    t=time.time(); k=south()
    print("SIZE[screen]=%2d  south atlas %7.2f KB  (%.0fs)"%(v,k,time.time()-t)); sys.stdout.flush()
