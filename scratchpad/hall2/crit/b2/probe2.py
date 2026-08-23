"""Face-TILT probe: three stacked body sub-bands whose normals tilt up by
15deg / 8deg / 0deg, same material.  Reads how much a board face that leans
back toward the wall gains on each wall orientation."""
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))
import base as B
from ckit import Material, save_and_place

MAT = Material("h17b_pt", "#ffffff", roughness=0.55)
H = 0.103
def prof():
    y = [0.032, 0.032+H, 0.032+2*H, 0.342]
    d = [B.T]
    for deg in (15.0, 8.0, 0.0):
        d.append(d[-1] - H*math.tan(math.radians(deg)))
    # renormalise so the top of the field is back at T (keep the same proud)
    st = [(0.000, 0.000), (d[0], 0.000)]
    bands = [(B.SK_TOE, False)]
    for i in range(3):
        st.append((d[i], y[i])); bands.append((MAT, False))
    st.append((d[3], y[3])); bands.append((MAT, False))
    st.append((B.CAPD, 0.360)); bands.append((B.SK_GRV, False))
    st.append((B.CAPD, 0.410)); bands.append((B.SK_CAP, False))
    d0, y0, d1, y1 = B.CAPD, 0.410, 0.010, B.BH
    for i in range(1, 4):
        a = (i/3.0)*(math.pi/2.0)
        st.append((d1 + (d0-d1)*math.cos(a), y0 + (y1-y0)*math.sin(a)))
        bands.append((B.SK_TOP, True))
    st.append((0.000, B.BH)); bands.append((B.SK_BK, False))
    return st, bands

B.PROF, B.BANDS = prof()
print(B.PROF)
m, runs = B.piece()
save_and_place("Hall2F Baseboards", m, 17)
