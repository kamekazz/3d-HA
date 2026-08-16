"""Round 3 contact shadows -- a smooth radial penumbra, shaped to each piece.

Critic item 9: round 2's three nested outlines read as 2-3 stepped concentric
bands from above (a decal, not a shadow), and the coffee table got a solid
4.0 x 2.2 slab under an OPEN X-frame, which read as a stain on the rug.

Re-run this whenever any piece moves; footprints are hand-copied from the build
scripts.
"""
import math

from kit3 import *
from kit3 import Material, Model, shadow_mats

FAINT = shadow_mats(a0=0.22, tag="f")

m = Model()

# --- fireplace hearth on the chamfer -------------------------------------
nrm, _ = edge_normal(*EDGES[CH])
mid = ((EDGES[CH][0][0] + EDGES[CH][1][0]) / 2,
       (EDGES[CH][0][1] + EDGES[CH][1][1]) / 2)
hc = (mid[0] + nrm[0] * 0.755, mid[1] + nrm[1] * 0.755)
smooth_shadow(m, foot_rect(hc[0], hc[1], 7.10, 1.51,
                           math.degrees(math.atan2(nrm[0], nrm[1]))), pad=0.80)

# --- north wall ----------------------------------------------------------
smooth_shadow(m, foot_rect(8.435, 0.88, 5.90, 1.46), pad=0.75)   # media console
smooth_shadow(m, foot_rect(19.80, 0.72, 1.20, 0.85), pad=0.50)   # etagere

# --- seating -------------------------------------------------------------
smooth_shadow(m, foot_rect(4.35, 15.165, 7.60, 3.55))            # sectional body
smooth_shadow(m, foot_rect(6.80, 12.090, 2.70, 2.60))            # chaise return
smooth_shadow(m, foot_rect(18.66, 7.05, 3.62, 5.90))             # east sofa N
smooth_shadow(m, foot_rect(18.66, 13.90, 3.62, 5.90))            # east sofa S
smooth_shadow(m, foot_rect(2.95, 8.22, 5.00, 4.00, 72))          # armchair
smooth_shadow(m, foot_rect(7.70, 8.40, 4.40, 2.50, 3))           # long ottoman
smooth_shadow(m, foot_rect(14.70, 7.05, 2.60, 4.20))             # chaise ottoman

# --- coffee table: an OPEN X-frame on four slim legs ---------------------
# A solid slab under it read as a stain.  Four leg pads carry the weight and a
# very faint wide halo carries the mass of the top.
CT = (11.80, 11.00, 2.0)
for (dx, dz) in ((-1.72, -0.88), (1.72, -0.88), (1.72, 0.88), (-1.72, 0.88)):
    r = math.radians(CT[2])
    px = CT[0] + dx * math.cos(r) + dz * math.sin(r)
    pz = CT[1] - dx * math.sin(r) + dz * math.cos(r)
    smooth_shadow(m, foot_disc(px, pz, 0.13, seg=10), pad=0.34)
smooth_shadow(m, foot_rect(CT[0], CT[1], 3.40, 1.70, CT[2]), pad=0.55, mats=FAINT)

# --- accents -------------------------------------------------------------
smooth_shadow(m, foot_disc(1.45, 5.65, 0.55), pad=0.45)          # tower fan
smooth_shadow(m, foot_disc(10.55, 16.00, 0.70), pad=0.50)        # plant
smooth_shadow(m, foot_rect(13.05, 15.30, 2.40, 1.70, 8), pad=0.50)   # pet crate
smooth_shadow(m, foot_disc(4.30, 12.20, 0.66), pad=0.45)         # basket
smooth_shadow(m, foot_rect(9.40, 13.70, 2.90, 2.70), pad=0.40)   # cushions

# --- the rug itself ------------------------------------------------------
# Occlusion at the pile edge only: drawn at y 0.020, BELOW the pile (0.079) and
# above the slab (0.010), so the part under the rug is swallowed and only the
# halo shows.
smooth_shadow(m, foot_rect(11.20, 9.80, 13.34, 11.14), pad=0.55,
              y_base=0.020, mats=FAINT)

put_in_place("Living Floor Shadows", m, save(m, "shadows3"))
