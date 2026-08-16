"""Room shell: real wall openings, polygon ceiling + crown + cans, baseboards."""
import json
import math
import urllib.request

from kit2 import *

# ---------------------------------------------------------------- openings
# Cut for real (house.js buildRoom -> shape.holes.push).  Round 1 faked every
# window as a flush decal, which is invisible from outside the room and breaks
# the dollhouse view.  `offset` runs along the edge from its FIRST vertex.
OPENINGS = [
    # patio slider, north wall, local x 12.00..18.85 (floor plan glazing run)
    dict(edge_index=N, offset=7.13, width=6.85, elevation=0.0, height=6.90,
         type="window"),
    # east window by the north corner, local z 1.04..4.02
    dict(edge_index=E, offset=1.04, width=2.98, elevation=2.35, height=4.55,
         type="window"),
    # west window, local z 11.90..14.90
    dict(edge_index=W, offset=2.06, width=3.00, elevation=2.35, height=4.55,
         type="window"),
    # kitchen pass-through over the half wall, local x 0.50..9.00 (photo B)
    dict(edge_index=S, offset=11.49, width=8.50, elevation=3.45, height=4.05,
         type="window"),
    # cased opening to the first-floor hallway, local x 14.00..18.00 (photo B)
    dict(edge_index=S, offset=2.49, width=4.00, elevation=0.0, height=7.00,
         type="window"),
]

house = json.load(urllib.request.urlopen("http://127.0.0.1:5000/api/house"))
room = next(r for f in house["floors"] for r in f["rooms"] if r["id"] == ROOM)
for op in room.get("openings", []):
    req("DELETE", f"/api/house/opening/{op['id']}")
for op in OPENINGS:
    req("POST", f"/api/house/room/{ROOM}/opening", op)
print("  openings:", len(OPENINGS))

# ---------------------------------------------------------------- ceiling
CEIL = Material("lrceil", "#ffffff", roughness=0.96, emissive="#d8d8d8",
                double_sided=False)
CROWN = Material("lrcrown", "#fbfbfa", roughness=0.7, emissive="#8f8f8f")
CANT = Material("lrcant", "#ffffff", roughness=0.6, emissive="#8e8e8e",
                double_sided=False)
CANA = Material("lrcana", "#fffdf6", roughness=0.4, emissive="#a09c92",
                double_sided=False)
LENS = Material("lrlens", "#ffffff", roughness=0.35, emissive="#b3b1aa",
                double_sided=False)

m = Model()
# polygon ceiling, single quad-fan wound to face DOWN so the plan view still
# sees the floor.  POLY's order fans downward-facing already.
v = [(x, RH, z) for (x, z) in POLY]
m.add(Part(v, [(0, i, i + 1) for i in range(1, len(POLY) - 1)]), CEIL)

CR = [(0.0, 0.0), (-0.52, 0.0), (-0.50, 0.055), (-0.42, 0.085),
      (-0.30, 0.12), (-0.07, 0.31), (0.0, 0.33)]
for i in range(len(POLY)):
    sweep_edge(m, CROWN, CR, i, y=RH)

CANS = [(7.6, 2.6), (13.4, 2.6), (18.6, 3.4), (6.2, 6.9), (2.6, 11.4),
        (8.2, 13.2), (14.4, 13.6), (18.9, 8.2), (18.9, 14.6)]
for (cx, cz) in CANS:
    m.add(disc_down(0.345), CANT, at=(cx, RH - 0.035, cz))
    m.add(disc_down(0.275), CANA, at=(cx, RH - 0.012, cz))

# Flat round flush-mount over the seating group (photo A).  EVERY part is a
# single-face disc looking DOWN: round 1 used cylinders and a double-sided
# material here, and the fixture then hovered over the room as a white oval in
# the plan and dollhouse views, where the ceiling must be invisible.
FLUSH = Material("lrflush", "#fbfbfa", roughness=0.7, emissive="#8f8f8f",
                 double_sided=False)
fx, fz = 10.6, 8.2
m.add(disc_down(0.82, seg=36), FLUSH, at=(fx, RH - 0.004, fz))
m.add(disc_down(0.78, seg=36), LENS, at=(fx, RH - 0.075, fz))
m.add(disc_down(0.62, seg=36), FLUSH, at=(fx, RH - 0.105, fz))
m.add(disc_down(0.44, seg=32), LENS, at=(fx, RH - 0.135, fz))
m.add(disc_down(0.26, seg=28), FLUSH, at=(fx, RH - 0.155, fz))

put_in_place("Living Ceiling", m, save(m, "ceiling2"))

# ---------------------------------------------------------------- baseboards
BB = Material("lrbb", "#fbfbf8", roughness=0.6, emissive="#343434")
BBP = [(0.0, 0.0), (0.0, 0.082), (0.40, 0.082), (0.455, 0.055), (0.47, 0.0)]
m = Model()
run_edge_gaps(m, BB, BBP, N, gaps=[(7.13, 13.98)])        # patio slider
run_edge_gaps(m, BB, BBP, S, gaps=[(2.49, 6.49)])         # hallway opening
run_edge_gaps(m, BB, BBP, W)
run_edge_gaps(m, BB, BBP, E)
# chamfer carries the stone breast floor-to-ceiling: no skirting there
put_in_place("Living Baseboards", m, save(m, "baseboards2"))

# ---------------------------------------------------------------- kitchen bar cap
# The pass-through is a half wall with a white countertop cap and a full-height
# square column at its east end (photo B).  The wall below the opening is the
# room's own; this is the cap and the column.
CAP = Material("lrcap", "#d9d6ce", roughness=0.35)
COL = Material("lrcol", "#e2e0d9", roughness=0.6)
m = Model()
n, _ = edge_normal(*EDGES[S])            # (0,-1): into the room
zc = 16.96
m.add(box(8.90, 0.13, 0.92), CAP, at=(4.75, 3.45, zc - 0.30))
m.add(box(8.90, 0.10, 0.10), CAP, at=(4.75, 3.35, zc - 0.74))
# column between the pass-through and the hallway wall
m.add(box(0.78, 7.62, 0.62), COL, at=(9.42, 0.0, zc - 0.31))
m.add(box(0.92, 0.22, 0.76), COL, at=(9.42, 7.62, zc - 0.31))
m.add(box(0.92, 0.10, 0.76), COL, at=(9.42, 0.0, zc - 0.31))
# cased jambs + head for the hallway opening (local x 14.00..18.00)
for cx in (13.86, 18.14):
    m.add(box(0.28, 7.14, 0.34), COL, at=(cx, 0.0, zc - 0.17))
m.add(box(4.56, 0.30, 0.34), COL, at=(16.0, 7.00, zc - 0.17))
put_in_place("Living Baseboards Trim", m, save(m, "s_trim"))
