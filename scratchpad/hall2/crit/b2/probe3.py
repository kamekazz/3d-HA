"""Paint the whole skirting one lurid colour: shows exactly which pixels are
mine, and whether the bright ribbon above the field is my cap or someone
else's wall band."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))
import base as B
from ckit import Material, save_and_place
LURID = Material("h17b_lurid", "#ff0090", roughness=0.6)
for n in ("SK_BODY","SK_CAP","SK_TOP","SK_GRV","SK_TOE","SK_BK"):
    setattr(B, n, LURID)
B.PROF, B.BANDS = B._profile()
m, runs = B.piece()
save_and_place("Hall2F Baseboards", m, 17)
