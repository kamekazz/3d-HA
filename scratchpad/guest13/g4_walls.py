"""Room 13 -- per-wall albedo skins for the two walls the single sun never
reaches.

ROOM-BRIEF, "Wall-to-wall brightness spread: a known limit": one `wall_color`
cannot land four walls that render 100 bytes apart, and the fix that IS allowed
is option 2 -- "give each wall its own albedo ... a plain NON-EMISSIVE skin
covering a whole wall face is just a painted surface".  What was rejected twice
before was an EMISSIVE partial panel, which glowed at night and showed hard
rectangular edges.

So: two flat quads, one per wall, corner to corner and floor to ceiling, no
emissive, roughness 0.95 to match house.js's wall material exactly, sitting
0.012 ft proud of the wall.  Named into objects.js SURFACE_RE ("wall wash") so
they can never steal the room's clicks.

Measured two-point fit at wall_color #b0aeaa (see the room json):
    south wall renders 108 and east 134 against north 219 / west 173.
"""

from gkit import *

import os
SKIN_S = Material("gskin_s", os.environ.get("SKS", "#c9c7c2"), roughness=0.95)
SKIN_E = Material("gskin_e", os.environ.get("SKE", "#a6a4a0"), roughness=0.95)
T = 0.012

# The EAST wall carries opening 111 (local z 8.05..10.78 == DOOR, world z
# 14.55..17.28), which is the same hole room 17 cut on its side for the Guest
# door.  A skin drawn corner to corner therefore stood as a solid plane at world
# x 10.488 -- 0.012 ft INSIDE the hallway's wall face -- right in front of the
# hallway's door leaf, so the leaf was invisible from the hall and had to be
# pulled nearly flush to be seen at all.  Owner-approved (22 Aug 2026): punch the
# hole.  Padded so the skin stops clear of room 17's casing.
DOOR_PAD = 0.28
HOLE_E = (DOOR[0] - DOOR_PAD, min(D, DOOR[1] + DOOR_PAD), 0.0, 7.0)


def _east(m, z0, z1, y0, y1):
    """One rect of the EAST skin (x = W - T); the face looks -x."""
    if z1 - z0 < 0.02 or y1 - y0 < 0.02:
        return
    x = W - T
    m.add(quad((x, y0, z0), (x, y1, z0), (x, y1, z1), (x, y0, z1)), SKIN_E)


def walls():
    m = Model()
    # SOUTH (z = D): the face looks -z, so wind it CCW seen from -z
    m.add(quad((0.0, 0.0, D - T), (0.0, H, D - T), (W, H, D - T), (W, 0.0, D - T)),
          SKIN_S)
    # EAST (x = W), corner to corner and floor to ceiling except the doorway.
    hz0, hz1, hy0, hy1 = HOLE_E
    _east(m, 0.0, hz0, 0.0, H)              # north of the opening, full height
    _east(m, hz1, D, 0.0, H)                # south of it (nothing if hz1 == D)
    _east(m, hz0, hz1, 0.0, hy0)            # under it (nothing if hy0 == 0)
    _east(m, hz0, hz1, hy1, H)              # over it, up to the ceiling
    return m


if __name__ == "__main__":
    print("room 13 wall skins")
    save_and_place("Guest Wall Wash", walls())
