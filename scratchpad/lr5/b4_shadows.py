"""Round 4 contact shadows -- round 3's falloff (confirmed good), re-fitted to
the pieces that moved, plus one fix.

The fix: the coffee table's wide ambient halo was drawn with a SOLID core, so
from the plan pose a hard-edged 3.4 x 1.7 ft rectangle of 22% black sat on the
rug under an open X-frame.  That is one of the two "hard seams splitting the
rug into differently-toned panels".  Wide halos over open furniture now start
faded (`core=False`).

Footprints are hand-copied from b4_soft.py -- re-run this whenever a piece
moves.
"""
import math

from kit4 import *
from kit4 import Material, Model, shadow_mats

FAINT = shadow_mats(a0=0.22, tag="f")

m = Model()

# --- fireplace hearth on the chamfer -------------------------------------
nrm, _ = edge_normal(*EDGES[CH])
mid = ((EDGES[CH][0][0] + EDGES[CH][1][0]) / 2,
       (EDGES[CH][0][1] + EDGES[CH][1][1]) / 2)
hc = (mid[0] + nrm[0] * 0.755, mid[1] + nrm[1] * 0.755)
smooth_shadow4(m, foot_rect(hc[0], hc[1], 7.10, 1.51,
                            math.degrees(math.atan2(nrm[0], nrm[1]))), pad=0.80)

# --- north wall ----------------------------------------------------------
smooth_shadow4(m, foot_rect(8.435, 0.88, 5.90, 1.46), pad=0.75)   # media console
smooth_shadow4(m, foot_rect(19.80, 0.72, 1.20, 0.85), pad=0.50)   # etagere

# --- seating -------------------------------------------------------------
smooth_shadow4(m, foot_rect(4.35, 15.165, 7.60, 3.55))            # sectional body
smooth_shadow4(m, foot_rect(6.80, 12.090, 2.70, 2.60))            # chaise return
smooth_shadow4(m, foot_rect(18.695, 7.20, 3.55, 6.20))            # east sofa N
smooth_shadow4(m, foot_rect(18.495, 13.65, 3.95, 6.40))           # east sofa S
smooth_shadow4(m, foot_rect(2.95, 8.21, 5.00, 4.00, 72))          # armchair
smooth_shadow4(m, foot_rect(7.70, 8.40, 4.40, 2.50, 3))           # long ottoman
smooth_shadow4(m, foot_rect(14.70, 7.20, 2.64, 4.24))             # chaise ottoman

# --- coffee table: an OPEN X-frame on four slim legs ---------------------
CT = (11.80, 11.00, 2.0)
for (dx, dz) in ((-1.72, -0.88), (1.72, -0.88), (1.72, 0.88), (-1.72, 0.88)):
    r = math.radians(CT[2])
    px = CT[0] + dx * math.cos(r) + dz * math.sin(r)
    pz = CT[1] - dx * math.sin(r) + dz * math.cos(r)
    smooth_shadow4(m, foot_disc(px, pz, 0.13, seg=10), pad=0.34)
smooth_shadow4(m, foot_rect(CT[0], CT[1], 3.40, 1.70, CT[2]), pad=0.62,
               mats=FAINT, core=False)

# --- accents -------------------------------------------------------------
smooth_shadow4(m, foot_disc(1.45, 5.65, 0.55), pad=0.45)          # tower fan
smooth_shadow4(m, foot_disc(10.55, 16.00, 0.70), pad=0.50)        # plant
smooth_shadow4(m, foot_rect(13.05, 15.30, 2.40, 1.70, 8), pad=0.50)   # pet crate
smooth_shadow4(m, foot_disc(4.30, 12.20, 0.66), pad=0.45)         # basket
smooth_shadow4(m, foot_rect(9.40, 13.70, 2.90, 2.70), pad=0.40)   # cushions

# --- the rug itself ------------------------------------------------------
smooth_shadow4(m, foot_rect(11.20, 9.80, 13.34, 11.14), pad=0.55,
               y_base=0.020, mats=FAINT)

put_in_place("Living Floor Shadows", m, save(m, "shadows4"))
