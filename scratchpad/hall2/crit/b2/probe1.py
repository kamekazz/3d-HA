"""3-point albedo/roughness probe for the skirting BODY, all in one render.

Splits base.py's body band into three stacked sub-bands with different
materials, so one column scan in one shot reads three (albedo, roughness)
points against the same wall.
"""
import os, sys, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))
import base as B
from ckit import Material, Model

TESTS = [
    ("#f7f3ec", 0.70),   # control = what ships now
    ("#ffffff", 0.35),
    ("#ffffff", 0.12),
]
MATS = [Material("h17b_pr%d" % i, c, roughness=r) for i, (c, r) in enumerate(TESTS)]

# rebuild the profile with the body split three ways
import math
def _profile():
    st = [(0.000, 0.000), (B.T, 0.000), (B.T, 0.032),
          (B.T, 0.135), (B.T, 0.238), (B.T, 0.342),
          (B.CAPD, 0.360), (B.CAPD, 0.410)]
    bands = [(B.SK_TOE, False), (B.SK_TOE, False),
             (MATS[0], False), (MATS[1], False), (MATS[2], False),
             (B.SK_GRV, False), (B.SK_CAP, False)]
    d0, y0, d1, y1 = B.CAPD, 0.410, 0.010, B.BH
    for i in range(1, 4):
        a = (i / 3.0) * (math.pi / 2.0)
        st.append((d1 + (d0 - d1) * math.cos(a), y0 + (y1 - y0) * math.sin(a)))
        bands.append((B.SK_TOP, True))
    st.append((0.000, B.BH)); bands.append((B.SK_BK, False))
    return st, bands

B.PROF, B.BANDS = _profile()
B.main.__globals__["PROF"], B.main.__globals__["BANDS"] = B.PROF, B.BANDS
m, runs = B.piece()
from ckit import save_and_place
save_and_place("Hall2F Baseboards", m, 17)
