"""Shared helpers for the Rios Room (room 15) build.

Everything in this build is authored in ROOM-LOCAL coordinates
(x 0..15.5 west->east, z 0..16 north->south, y 0..8 up from the slab) and
placed with rot=0 and pos = (bbox centre x, bbox min y, bbox centre z),
which is exactly the seat the app gives a model.  That removes the
"author facing +z then rotate" bookkeeping entirely.
"""

import os
import sys

sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")

from roomkit.glb import (Model, Material, box, rounded_box, cylinder, prism,
                         quad, sag_plane, torus)          # noqa: F401
from roomkit.place import place

ROOM = 15
W = 15.5          # local x extent  (west wall x=0, east wall x=15.5)
D = 16.0          # local z extent  (north wall z=0, south wall z=16)
H = 8.0           # wall height

OUT = os.path.dirname(os.path.abspath(__file__))


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


# ---- palette picked off docs/photos-jpg/Rios room.jpg ---------------------

TRIM     = Material("trim",     "#fbfbfa", roughness=0.55, emissive="#5a5a5a")
TRIM_FLAT= Material("trimflat", "#fbfbfa", roughness=0.55, emissive="#c2c2c2",
                    double_sided=False)
CEIL     = Material("ceil",     "#ffffff", roughness=0.95, emissive="#d4d4d4",
                    double_sided=False)
LENS     = Material("lens",     "#fff6e2", roughness=0.3, emissive="#ffe9c0",
                    emissive_strength=3.0, double_sided=False)
GLASSLIT = Material("glasslit", "#ffffff", roughness=0.25, emissive="#ffffff",
                    emissive_strength=2.6)
LEAFOUT  = Material("leafout",  "#93a37b", roughness=0.9, emissive="#6b7a52",
                    emissive_strength=1.5)
SLAT     = Material("slat",     "#f3f2ef", roughness=0.7, emissive="#484848")
WHITEWD  = Material("whitewd",  "#f4f3f0", roughness=0.6)
BLACKMET = Material("blackmet", "#26262a", roughness=0.45, metallic=0.4)
GREYMET  = Material("greymet",  "#9ca0a2", roughness=0.42, metallic=0.30,
                    emissive="#141516")
