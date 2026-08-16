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


def walls():
    m = Model()
    # SOUTH (z = D): the face looks -z, so wind it CCW seen from -z
    m.add(quad((0.0, 0.0, D - T), (0.0, H, D - T), (W, H, D - T), (W, 0.0, D - T)),
          SKIN_S)
    # EAST (x = W): the face looks -x
    m.add(quad((W - T, 0.0, 0.0), (W - T, H, 0.0), (W - T, H, D), (W - T, 0.0, D)),
          SKIN_E)
    return m


if __name__ == "__main__":
    print("room 13 wall skins")
    save_and_place("Guest Wall Wash", walls())
