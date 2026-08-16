"""Room 8 Office -- shared geometry facts and helpers.

Local frame: x 0 (WEST) .. 10.6 (EAST), z 0 (NORTH) .. 11.6 (SOUTH), y from the
slab.  North and east are exterior; bathroom 23 is west, printer nook 22 is
south-east, laundry 9 is south-west.
"""
import math
import os
import sys

sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\shellpass")
sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")

from kit import (Model, Material, box, rounded_box, cylinder, prism, quad,     # noqa: F401
                 sag_plane, torus, Part, place, R, mix, Rnd, bx, rect_down,
                 rect_up, disc_down, ring_down, spans, wall_band, contact_shadow,
                 panel_door, _blit, cased_opening, ceiling, baseboards,
                 TRIM, TRIM_D, CEIL, CEIL_FLAT, CAN_CONE, LENS, VENT, WHITEWD,
                 DOORSHADE, BLACKMET, CHROME, GLASS, BB_H, BB_T, CROWN_H,
                 CASE_W, DOOR_TOP, surfaces)

OUT = os.path.dirname(os.path.abspath(__file__))
ROOM, W, D, H = 8, 10.6, 11.6, 9.0
RAIL = 3.30                     # chair-rail top, measured off photo f (3.1-3.4)
WAINSCOT = "#303337"

# real cut openings (see o8_openings.py) in each wall's own local axis
DOOR_W = (7.59, 10.59)          # west wall, z span -- 15-lite french door
WIN_N = (0.45, 3.45)            # east wall, z span
WIN_S = (7.95, 10.95)           # east wall, z span
WIN_SILL, WIN_HEAD = 1.85, 7.50
PASS_S = (5.60, 8.90)           # south wall, x span -- cased opening to nook
PASS_TOP = 7.20


def save_and_place(name, m, fname=None):
    path = os.path.join(OUT, "glb",
                        (fname or name.replace(" ", "_").lower()) + ".glb")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    m.save(path)
    lo, hi = m.bounds()
    pos = ((lo[0] + hi[0]) / 2.0, lo[1], (lo[2] + hi[2]) / 2.0)
    res = place(name, path, ROOM, pos=pos, rot_y_deg=0.0, scale=1.0)
    kb = os.path.getsize(path) / 1024.0
    size = tuple(round(hi[i] - lo[i], 3) for i in range(3))
    print(f"  {name:26s} {kb:7.1f} KB  size={size}  {res['action']}")
    return {"name": name, "size_ft": list(size), "kb": round(kb, 1),
            "pos": [round(p, 3) for p in pos], "rot": 0}


# ---------------------------------------------------------------- wall skins
def wall_skin(m, wall, color, y0, y1, holes=(), inset=0.030, rough=0.95):
    """A plain, NON-emissive albedo skin covering one whole wall face.

    Not the rejected "wall wash": no emissive, no partial rectangle.  It exists
    because the scene has one sun and no bounce, so an unlit wall renders 60-85
    bytes below a sunlit one at the same paint colour (ROOM-BRIEF: "give each
    wall its own albedo").  roughness matches the room wall's 0.95 so the seam
    at the crown/rail does not show.
    """
    mat = Material("skin" + color.lstrip("#"), color, roughness=rough,
                   metallic=0.0)
    total = W if wall in "ns" else D
    # holes are (a0, a1, hy0, hy1) in the wall's own axis
    bands = [(y0, y1, [])]
    for (a0, a1, hy0, hy1) in holes:
        nb = []
        for (b0, b1, hs) in bands:
            if hy1 <= b0 or hy0 >= b1:
                nb.append((b0, b1, hs))
                continue
            if b0 < hy0:
                nb.append((b0, hy0, list(hs)))
            nb.append((max(b0, hy0), min(b1, hy1), list(hs) + [(a0, a1)]))
            if b1 > hy1:
                nb.append((hy1, b1, list(hs)))
        bands = [b for b in nb if b[1] - b[0] > 0.01]
        # merge duplicate y-ranges
        merged = {}
        for (b0, b1, hs) in bands:
            merged.setdefault((round(b0, 4), round(b1, 4)), []).extend(hs)
        bands = [(k[0], k[1], v) for k, v in merged.items()]
    for (b0, b1, hs) in bands:
        for (a, b) in spans(total, hs):
            if wall == "n":
                bx(m, mat, a, b, b0, b1, inset, inset + 0.012)
            elif wall == "s":
                bx(m, mat, a, b, b0, b1, D - inset - 0.012, D - inset)
            elif wall == "w":
                bx(m, mat, inset, inset + 0.012, b0, b1, a, b)
            else:
                bx(m, mat, W - inset - 0.012, W - inset, b0, b1, a, b)


SKIN_TOP = H - CROWN_H + 0.05          # tuck under the crown
SKIN_BOT = RAIL - 0.16                 # tuck behind the chair rail

HOLES = {
    "n": [],
    "e": [(WIN_N[0] - 0.03, WIN_N[1] + 0.03, WIN_SILL, WIN_HEAD + 0.02),
          (WIN_S[0] - 0.03, WIN_S[1] + 0.03, WIN_SILL, WIN_HEAD + 0.02)],
    "s": [(PASS_S[0] - 0.03, PASS_S[1] + 0.03, 0.0, PASS_TOP + 0.02)],
    "w": [(DOOR_W[0] - 0.03, DOOR_W[1] + 0.03, 0.0, 7.02)],
}
# NOTE: house.js edge 3 measures its offset from z=D descending; wall_band('w')
# uses plain ascending z, so DOOR_W is already stored in room-local z.


def skins(colors):
    """colors = {'n': '#..', 'e': ..., 's': ..., 'w': ...}"""
    m = Model()
    for wall in "nesw":
        wall_skin(m, wall, colors[wall], SKIN_BOT, SKIN_TOP, HOLES[wall])
    return m
