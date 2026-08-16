"""Baked contact shadows for every piece that meets the floor.

The app renders NO shadows for generated geometry, so without this every piece
floats -- the single defect both round-1 critics named.  One translucent-black
decal piece, clipped to the room polygon, sitting just above the rug pile so the
same object serves rug and bare floor alike.

Footprints are duplicated from the build scripts by hand: re-run this whenever a
piece moves.
"""
import math

from kit2 import *

m = Model()

# --- fireplace on the chamfer -------------------------------------------
n, _ = edge_normal(*EDGES[CH])
mid = ((EDGES[CH][0][0] + EDGES[CH][1][0]) / 2, (EDGES[CH][0][1] + EDGES[CH][1][1]) / 2)
hearth_c = (mid[0] + n[0] * 0.36, mid[1] + n[1] * 0.36)
soft_shadow(m, foot_rect(hearth_c[0], hearth_c[1], 6.92, 1.05,
                         math.degrees(math.atan2(n[0], n[1]))))

# --- north wall ----------------------------------------------------------
soft_shadow(m, foot_rect(8.435, 0.88, 5.90, 1.46))            # media console
soft_shadow(m, foot_rect(19.80, 0.72, 1.20, 0.85))            # etagere

# --- seating -------------------------------------------------------------
soft_shadow(m, foot_rect(4.35, 15.165, 7.60, 3.55))           # sectional body
soft_shadow(m, foot_rect(6.80, 12.090, 2.70, 2.60))           # chaise return
soft_shadow(m, foot_rect(18.595, 9.30, 3.75, 8.40))           # east sofa
soft_shadow(m, foot_rect(2.23, 7.75, 3.60, 4.00, 72))         # armchair
soft_shadow(m, foot_rect(7.70, 8.40, 4.40, 2.50, 3))          # long ottoman
soft_shadow(m, foot_rect(15.20, 7.00, 2.60, 4.20))            # chaise ottoman
soft_shadow(m, foot_rect(12.00, 10.50, 4.00, 2.20, 2),        # coffee table (legs)
            pads=(0.55, 0.28, 0.05))

# --- accents -------------------------------------------------------------
soft_shadow(m, foot_disc(1.10, 5.20, 0.55), pads=(0.55, 0.28, 0.05))
soft_shadow(m, foot_disc(19.50, 15.40, 0.66), pads=(0.60, 0.30, 0.05))
soft_shadow(m, foot_rect(12.50, 15.40, 2.40, 1.70, 8), pads=(0.60, 0.30, 0.05))
soft_shadow(m, foot_disc(4.30, 12.20, 0.66), pads=(0.55, 0.28, 0.05))
soft_shadow(m, foot_rect(10.20, 12.90, 2.90, 2.70), pads=(0.45, 0.22, 0.05))

# --- the rug itself ------------------------------------------------------
# Occlusion at the pile edge so the rug sits in the floor rather than on it.
# Drawn at y 0.020 -- BELOW the pile (0.079) and above the slab (0.010), so the
# part of the disc under the rug is swallowed by the rug and only the halo shows.
soft_shadow(m, foot_rect(11.20, 9.80, 13.30, 11.10), pads=(0.50, 0.26, 0.10),
            y_base=0.020)

put_in_place("Living Floor Shadows", m, save(m, "shadows"))
