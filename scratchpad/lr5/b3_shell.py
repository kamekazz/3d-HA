"""Round 3 shell: wall/floor tone, ceiling with NON-emissive crown, crisp
recessed cans, a two-part flush mount, and NON-emissive baseboards.

Critic items 2, 8 and 13.  The emissive on the crown and the baseboards was the
single biggest reason the room read as bright white fins bounding darker
partitions; the "no emissive" rule in ROOM-BRIEF covers room-scale trim runs.
"""
import math

from kit3 import *
from kit3 import Part, Material, Model

# ------------------------------------------------------------------ surfaces
# Item 2.  Metered on the round-2 build: north wall 211, west wall 156 at
# #b0afac against photo f's 155-171 (mean 162).  One directional sun and no
# bounce means the spread cannot be closed (ROOM-BRIEF: "a known limit"), so
# the base colour is picked to land the AVERAGE of the visible walls in the
# photo's range rather than to fix one wall.
WALL = "#979693"
FLOOR = "#4c4e53"
req("PATCH", "/api/house/room/5",
    {"wall_color": WALL, "floor_color": FLOOR,
     "wall_texture": "plaster", "floor_texture": "wood"})
print("  surfaces wall %s floor %s" % (WALL, FLOOR))

# ------------------------------------------------------------------- ceiling
CEIL = Material("lrceil", "#ffffff", roughness=0.96, emissive="#c4c4c4",
                double_sided=False)
# NO emissive on the crown (item 8).
CROWN = Material("lrcrown", "#fdfdfb", roughness=0.62)
# Cans: a crisp bright trim ring, a distinctly darker throat, a pale lens.
# Round 2 gave all three near-equal emissive and they came out as grey smudges.
CAN_RING = Material("lrcanring", "#ffffff", roughness=0.5, emissive="#e6e6e4",
                    double_sided=False)
CAN_THROAT = Material("lrcanth", "#cfcdc8", roughness=0.9, emissive="#7a7975",
                      double_sided=False)
CAN_LENS = Material("lrcanlens", "#fffdf6", roughness=0.35, emissive="#cbc8c0",
                    double_sided=False)

m = Model()
v = [(x, RH, z) for (x, z) in POLY]
m.add(Part(v, [(0, i, i + 1) for i in range(1, len(POLY) - 1)]), CEIL)

CR = [(0.0, 0.0), (-0.52, 0.0), (-0.50, 0.055), (-0.42, 0.085),
      (-0.30, 0.12), (-0.07, 0.31), (0.0, 0.33)]
for i in range(len(POLY)):
    sweep_edge(m, CROWN, CR, i, y=RH)

CANS = [(7.6, 2.6), (13.4, 2.6), (18.6, 3.4), (6.2, 6.9), (2.6, 11.4),
        (8.2, 13.2), (14.4, 13.6), (18.9, 8.2), (18.9, 14.6)]
for (cx, cz) in CANS:
    m.add(annulus_down(0.285, 0.365, seg=26), CAN_RING, at=(cx, RH - 0.030, cz))
    m.add(disc_down(0.290, seg=26), CAN_THROAT, at=(cx, RH - 0.012, cz))
    m.add(disc_down(0.195, seg=22), CAN_LENS, at=(cx, RH - 0.070, cz))

# Flush mount over the seating group (photo A): a plain white disc with one
# thin rim, not round 2's five-ring concentric target.
FLUSH = Material("lrflush", "#ffffff", roughness=0.6, emissive="#e4e4e2",
                 double_sided=False)
FRIM = Material("lrfrim", "#f2f1ee", roughness=0.7, emissive="#a9a8a4",
                double_sided=False)
fx, fz = 10.6, 8.2
m.add(annulus_down(0.80, 0.92, seg=40), FRIM, at=(fx, RH - 0.020, fz))
m.add(disc_down(0.82, seg=40), FLUSH, at=(fx, RH - 0.090, fz))

put_in_place("Living Ceiling", m, save(m, "ceiling3"))

# ---------------------------------------------------------------- baseboards
# NO emissive (item 8).
BB = Material("lrbb", "#fbfbf8", roughness=0.6)
BBP = [(0.0, 0.0), (0.0, 0.082), (0.40, 0.082), (0.455, 0.055), (0.47, 0.0)]
m = Model()
run_edge_gaps(m, BB, BBP, N, gaps=[(7.13, 13.98)])        # patio slider
run_edge_gaps(m, BB, BBP, S, gaps=[(2.49, 6.49)])         # hallway opening
run_edge_gaps(m, BB, BBP, W)
run_edge_gaps(m, BB, BBP, E)
put_in_place("Living Baseboards", m, save(m, "baseboards3"))
