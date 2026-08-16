"""Casings for the two real window openings, plus the wall art.

Everything here is authored DIRECTLY in room-local feet and placed with rot 0
(put_in_place), so no rotation bookkeeping: an east-wall casing is just a set of
boxes near x = 20.49.
"""
import math

from kit2 import *

TRIMW = Material("lrwtrim", "#dedcd6", roughness=0.55)
SHADE = Material("lrwshade", "#c8c5bd", roughness=0.95)
SASH = Material("lrwsash", "#e3e1db", roughness=0.5)


def window_casing(m, wall, along0, along1, y0, y1, depth=0.34):
    """Cased double-hung around a real opening.  `wall` is 'e' or 'w'; the
    opening runs `along0..along1` in z and `y0..y1` in y."""
    x = RW if wall == "e" else 0.0
    s = -1 if wall == "e" else 1          # into the room
    cz = (along0 + along1) / 2
    w = along1 - along0
    xc = x + s * depth / 2

    for z in (along0 + 0.09, along1 - 0.09):          # jambs
        m.add(box(depth, y1 - y0, 0.18), TRIMW, at=(xc, y0, z))
    m.add(box(depth, 0.18, w), TRIMW, at=(xc, y1 - 0.18, cz))        # head jamb
    m.add(box(depth, 0.14, w), TRIMW, at=(xc, y0, cz))               # sill pan
    m.add(box(depth * 0.55, 0.09, w - 0.30), SASH,                   # meeting rail
          at=(x + s * depth * 0.28, (y0 + y1) / 2, cz))
    m.add(box(depth * 0.55, y1 - y0 - 0.4, 0.08), SASH,
          at=(x + s * depth * 0.28, y0 + 0.2, cz))
    # roman shade parked at the head
    m.add(box(depth * 0.5, 0.72, w - 0.10), SHADE,
          at=(x + s * depth * 0.45, y1 - 0.86, cz))
    # casing proud of the wall face
    xo = x + s * 0.08
    for z in (along0 - 0.16, along1 + 0.16):
        m.add(box(0.16, y1 - y0 + 0.52, 0.30), TRIMW, at=(xo, y0 - 0.10, z))
    m.add(box(0.16, 0.26, w + 0.62), TRIMW, at=(xo, y1, cz))
    m.add(box(0.24, 0.10, w + 0.80), TRIMW, at=(x + s * 0.12, y1 + 0.26, cz))
    m.add(box(0.42, 0.10, w + 0.84), TRIMW, at=(x + s * 0.21, y0 - 0.10, cz))  # stool
    m.add(box(0.14, 0.30, w + 0.50), TRIMW, at=(xo, y0 - 0.40, cz))            # apron


m = Model()
window_casing(m, "e", 1.04, 4.02, 2.35, 6.90)
put_in_place("Living Window East Trim", m, save(m, "win_e2"))

m = Model()
window_casing(m, "w", 11.90, 14.90, 2.35, 6.90)
put_in_place("Living Window West Trim", m, save(m, "win_w2"))

# ------------------------------------------------------------------ art
FRAME = Material("lrframe", "#c6c4be", roughness=0.5)
CANV = Material("lrcanv", "#cdcac3", roughness=0.9)
BLUSH = Material("lrblush", "#bfa79c", roughness=0.9)
GREYA = Material("lrgreya", "#8d8882", roughness=0.9)
INK = Material("lrink", "#37373a", roughness=0.8)

# the wide horizontal canvas over the east sofa (photo f, right-hand wall)
BW, BH, BZ, BY = 5.60, 2.00, 9.30, 4.40
m = Model()
m.add(box(0.06, BH, BW), FRAME, at=(RW - 0.03, BY, BZ))
m.add(box(0.02, BH - 0.10, BW - 0.10), CANV, at=(RW - 0.075, BY + 0.05, BZ))
m.add(box(0.01, 1.12, 1.65), BLUSH, at=(RW - 0.09, BY + 0.02, BZ - 1.50), rot_x=0.06)
m.add(box(0.01, 0.78, 1.00), GREYA, at=(RW - 0.09, BY + 0.42, BZ + 0.20), rot_x=-0.09)
m.add(box(0.01, 0.60, 0.92), INK, at=(RW - 0.09, BY + 0.10, BZ + 1.50), rot_x=0.12)
m.add(box(0.01, 0.28, 0.52), GREYA, at=(RW - 0.09, BY + 0.62, BZ + 2.10))
put_in_place("Living Art East", m, save(m, "art_e2"))

# the pale blush/grey abstract on the west wall, between window and fireplace
AW, AH, AZ, AY = 2.40, 1.90, 8.20, 4.05
m = Model()
m.add(box(0.06, AH, AW), FRAME, at=(0.03, AY, AZ))
m.add(box(0.02, AH - 0.10, AW - 0.10), CANV, at=(0.075, AY + 0.05, AZ))
m.add(box(0.01, 0.95, 1.55), BLUSH, at=(0.09, AY + 0.55, AZ - 0.20), rot_x=-0.10)
m.add(box(0.01, 0.55, 0.95), GREYA, at=(0.09, AY + 0.30, AZ + 0.45), rot_x=0.16)
put_in_place("Living Art West", m, save(m, "art_w2"))

# dark twig/driftwood wall piece on the south wall by the column (photo B)
TWIG = Material("lrtwig", "#4a4a4c", roughness=0.95)
TWIG2 = Material("lrtwig2", "#5e5e60", roughness=0.95)
m = Model()
for i in range(22):
    a = -1.15 + 0.105 * i
    L = 1.35 + 0.5 * math.sin(i * 1.7)
    m.add(box(0.07, L, 0.06), TWIG2 if i % 3 == 0 else TWIG,
          at=(11.30 + 0.055 * i - 0.6, 4.55 + 0.5 * math.cos(i * 0.9),
              RD - 0.06), rot_z=a * 0.55)
put_in_place("Living Art South", m, save(m, "art_s2"))
