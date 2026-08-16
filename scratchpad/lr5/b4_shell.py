"""Round 4 shell -- wall tone only.

Round 3 re-toned #b0afac -> #979693 and reported "average 169, in the photo's
range".  A critic re-metered and found that average covered only the two
brightest walls: with #979693 the four CLEAN wall patches meter

    north 194.3   west 134.0   east 98.2   south 72.3   -> average 124.7

against photo f's 148-177 (mean of four clean patches 160.3).  A two-point
probe (wallprobe.py, #979693 and #c9c8c4) gives a per-wall slope of
0.55 (N) / 0.87 (W) / 0.89 (E) / 0.81 (S) render bytes per albedo byte, so the
albedo that lands the FOUR-wall average on the photo's is ~194.

Nothing else in the shell changes: the ceiling, crown, cans and baseboards are
round 3's and were confirmed good.
"""
from kit4 import *

WALL = "#c0bfbb"
FLOOR = "#4c4e53"
req("PATCH", "/api/house/room/5",
    {"wall_color": WALL, "floor_color": FLOOR,
     "wall_texture": "plaster", "floor_texture": "wood"})
print("  surfaces wall %s floor %s" % (WALL, FLOOR))
