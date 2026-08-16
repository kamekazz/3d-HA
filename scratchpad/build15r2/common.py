"""Rios Room (room 15) ROUND 2 -- shared helpers.

The footprint was re-traced under round 1: the room is now 12.5 x 11.7 ft
(was 15.5 x 16) and the ORIENTATION is different.  Re-derived from
`docs/floor plan/Second Floor Plan App.png` plus the level-2 adjacencies:

  plan-up = world +z (south), plan-right = world -x (west), so

    SOUTH wall (local z = 11.7) -- EXTERIOR, carries the two windows.
    NORTH wall (local z = 0)    -- closet double door (west end, room 25
                                   "Room 7" sits behind it) + entry door.
    WEST  wall (local x = 0)    -- EXTERIOR, the birdcage stands against it.
    EAST  wall (local x = 12.5) -- console / landscape art / tower fan;
                                   room 26 (2F bath) is behind it.

Everything is authored in ROOM-LOCAL feet and placed with rot=0 and
pos = (bbox centre x, bbox min y, bbox centre z), which is exactly the seat
the app gives a model.
"""

import os
import sys

sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")

from roomkit.glb import (Model, Material, box, rounded_box, cylinder, prism,
                         quad, sag_plane, torus, Part)          # noqa: F401
from roomkit.place import place

ROOM = 15
W = 12.5          # local x extent  (west wall x=0, east wall x=12.5)
D = 11.7          # local z extent  (north wall z=0, south wall z=11.7)
H = 8.0           # wall height

OUT = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- geometry
# The two south-wall windows.  Sizes are the critic's measurements off the
# primary photo (~4.8 ft tall, ~1.7 ft sill, ~1.3 ft header) reconciled with
# the widths read off the floor plan; round 1's 6.15 ft tall / 1.40 sill unit
# left a 5-inch header and read as a French door.
SILL = 1.75
HEAD = 6.60                      # = SILL + 4.85 of glass
WIN_E = (8.25, 10.95)            # opening in local x
WIN_W = (2.55, 4.75)

# North-wall doors (both built as closed leaves -- there is no room behind the
# entry door in the layout, so a real cut opening would show void).
CLOSET_X = (1.40, 6.40)
DOOR_X = (8.90, 11.60)
DOOR_TOP = 6.75
CASE_W = 0.28


def save_and_place(name, m, fname=None):
    path = os.path.join(OUT, (fname or name.replace(" ", "_").lower()) + ".glb")
    m.save(path)
    lo, hi = m.bounds()
    pos = ((lo[0] + hi[0]) / 2.0, lo[1], (lo[2] + hi[2]) / 2.0)
    res = place(name, path, ROOM, pos=pos, rot_y_deg=0.0, scale=1.0)
    size = tuple(round(hi[i] - lo[i], 3) for i in range(3))
    print(f"{name:22s} size={size}  pos=({pos[0]:.3f},{pos[1]:.3f},{pos[2]:.3f})  {res['action']}")
    return {"name": name, "size_ft": list(size),
            "pos": [round(p, 3) for p in pos], "rot": 0}


def bx(m, mat, x0, x1, y0, y1, z0, z1):
    m.add(box(x1 - x0, y1 - y0, z1 - z0), mat,
          at=((x0 + x1) / 2.0, y0, (z0 + z1) / 2.0))


def rect_up(m, mat, x0, x1, y, z0, z1):
    """A flat quad facing straight UP -- floor decals."""
    m.add(quad((x0, y, z1), (x1, y, z1), (x1, y, z0), (x0, y, z0)), mat)


def rect_down(m, mat, x0, x1, y, z0, z1):
    m.add(quad((x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)), mat)


def mix(a, b, t):
    """Blend two sRGB hex colours."""
    a = a.lstrip("#"); b = b.lstrip("#")
    out = []
    for i in (0, 2, 4):
        ca, cb = int(a[i:i + 2], 16), int(b[i:i + 2], 16)
        out.append(int(round(ca + (cb - ca) * t)))
    return "#%02x%02x%02x" % tuple(out)


class Rnd:
    def __init__(self, s):
        self.s = s

    def f(self, a=0.0, b=1.0):
        self.s = (self.s * 1103515245 + 12345) % (1 << 31)
        return a + (b - a) * (((self.s >> 9) % 100000) / 100000.0)


# ---- palette picked off docs/photos-jpg/Rios room.jpg ---------------------

TRIM     = Material("trim",     "#fbfbfa", roughness=0.55, emissive="#4e4e4e")
TRIM_FLAT= Material("trimflat", "#fdfdfc", roughness=0.55, emissive="#bcbcbc",
                    double_sided=False)
CEIL     = Material("ceil",     "#ffffff", roughness=0.95, emissive="#bcbcbc",
                    double_sided=False)
CAN_CONE = Material("cancone",  "#e8e8e6", roughness=0.5, emissive="#8a8a88",
                    double_sided=False)
LENS     = Material("lens",     "#fff7e6", roughness=0.3, emissive="#fff2d6",
                    emissive_strength=7.0, double_sided=False)
# The pane behind the blinds: the photo is blown-out daylight, not tinted glass.
PANE     = Material("pane",     "#ffffff", roughness=0.2, emissive="#ffffff",
                    emissive_strength=2.9)
LEAFOUT  = Material("leafout",  "#8e9d78", roughness=0.9, emissive="#66714f",
                    emissive_strength=1.5)
SLAT     = Material("slat",     "#f6f5f2", roughness=0.7, emissive="#3e3e3e")
WHITEWD  = Material("whitewd",  "#f6f5f2", roughness=0.6, emissive="#333333")
DOORSHADE= Material("doorshade","#cfccc6", roughness=0.7)
BLACKMET = Material("blackmet", "#26262a", roughness=0.45, metallic=0.4)
GREYMET  = Material("greymet",  "#a3a7a9", roughness=0.42, metallic=0.30,
                    emissive="#161718")
