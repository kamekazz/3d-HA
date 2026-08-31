"""Measure the three cabinet GLBs WITHOUT touching the DB or the live files."""
import os, sys, tempfile
_R = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
for p in (os.path.join(_R, "tools"), os.path.join(_R, "scratchpad", "bsmt"),
          os.path.join(_R, "scratchpad", "arc4"), os.path.join(_R, "scratchpad", "arc4", "art")):
    if p not in sys.path:
        sys.path.insert(0, p)
import bkit
TMP = tempfile.mkdtemp()
bkit.OUT = TMP
bkit.place = lambda *a, **k: {"action": "dry"}
import ar2
ar2.save_and_place = bkit.save_and_place
ar2.place = bkit.place
tot = 0.0
for k in ("east", "south", "ncab"):
    r = ar2.BUILDERS[k]()
    tot += r["kb"]
print("cabinets total %.1f KB" % tot)
