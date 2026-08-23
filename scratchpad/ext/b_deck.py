"""Backyard: the raised composite deck, its railing and its two stair flights.

Photographed in "Backyard v3 9" (from the camera under the eave) and
"Backyard v3 5" (aerial from the far corner): grey composite boards on the
DIAGONAL, white square-baluster railing with flat newel caps, two levels with a
single step between them, and steps down at two points -- a short flight to the
lawn and a taller one down onto the gravel bed at the east.

Anchored to the shell GLB's own walls, not to room 3's traced rect (which sits
under the house): main-block rear wall z = -24.5, garage-wing rear wall
z = -10.9, rear grade y = 2.13 on the raised pad and 0.16 on the east strip.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from kit import (Model, Material, deck_surface, railing, stair, add_box,
                 board_tex, world_pos, OUT)

# ---- world layout (feet) ---------------------------------------------------
LOW = 0.16                 # east strip grade  -> authored y 0
GY = 2.13                  # house-pad grade
LD = 3.30                  # lower deck top
UD = 3.95                  # upper deck top
RH = 3.05                  # railing height

UX0, UX1, UZ0, UZ1 = 3.0, 20.0, -32.6, -24.4     # upper, against the rear wall
LX0, LX1, LZ0, LZ1 = 3.0, 24.5, -42.2, -32.6     # lower, out into the yard

B = lambda y: y - LOW      # authored y

DECK = Material("deck_composite", "#6f7069", roughness=0.92, metallic=0.0,
                double_sided=False, tex=board_tex(7))
FASCIA = Material("deck_fascia", "#616259", roughness=0.92, metallic=0.0)
RAIL = Material("deck_rail", "#eeece7", roughness=0.55, metallic=0.0)
POST = Material("deck_post", "#5f605c", roughness=0.95, metallic=0.0)

# Contact shadows baked into the deck surface, (cx, cz, rx, rz, strength).
# Radii run ~0.8 ft past each piece's footprint so the ramp is visible beside
# the object instead of buried under it.
SHADOWS = [
    (11.5, -27.2, 3.2, 2.4, 0.34),    # grill
    (18.6, -37.0, 4.9, 2.5, 0.30),    # wicker sofa (along the east rail)
    (8.2, -36.2, 2.6, 2.6, 0.28),     # armchair W
    (12.0, -39.6, 2.6, 2.6, 0.28),    # armchair S
    (14.6, -35.4, 2.2, 2.2, 0.24),    # ottoman
    (10.4, -34.6, 2.2, 2.2, 0.24),    # ottoman
    (11.6, -36.9, 2.8, 2.0, 0.26),    # coffee table
    (22.6, -39.6, 1.9, 1.9, 0.32),    # parasol base
]


def build():
    m = Model()
    # --- decking
    m.add(deck_surface(UX0, UZ0, UX1, UZ1, B(UD), shadows=SHADOWS), DECK)
    m.add(deck_surface(LX0, LZ0, LX1, LZ1, B(LD), shadows=SHADOWS), DECK)

    # --- fascia + framing skirt round each platform
    for (x0, z0, x1, z1, top) in ((UX0, UZ0, UX1, UZ1, UD),
                                  (LX0, LZ0, LX1, LZ1, LD)):
        add_box(m, FASCIA, x1 - x0 + 0.3, 0.85, 0.3, (x0 + x1) / 2, B(top) - 0.85, z0)
        add_box(m, FASCIA, x1 - x0 + 0.3, 0.85, 0.3, (x0 + x1) / 2, B(top) - 0.85, z1)
        add_box(m, FASCIA, 0.3, 0.85, z1 - z0, x0, B(top) - 0.85, (z0 + z1) / 2)
        add_box(m, FASCIA, 0.3, 0.85, z1 - z0, x1, B(top) - 0.85, (z0 + z1) / 2)
        # posts down to grade
        for x in [x0 + 0.6, (x0 + x1) / 2, x1 - 0.6]:
            for z in [z0 + 0.6, z1 - 0.6]:
                add_box(m, POST, 0.42, B(top) - 0.85, 0.42, x, 0, z)

    # --- railing. Open where the deck meets the house and at the two stairs.
    railing(m, RAIL, UX0, UZ0, UX0, UZ1 - 0.4, B(UD), RH)          # upper west
    railing(m, RAIL, UX1, UZ0, UX1, UZ1 - 0.4, B(UD), RH)          # upper east
    railing(m, RAIL, LX0, LZ0, LX0, LZ1, B(LD), RH)                # lower west
    railing(m, RAIL, UX1, LZ1, LX1, LZ1, B(LD), RH)                # lower east return
    railing(m, RAIL, LX1, LZ0, LX1, -38.6, B(LD), RH)              # lower east, N of stair
    railing(m, RAIL, LX1, -34.6, LX1, LZ1, B(LD), RH)              # lower east, S of stair
    railing(m, RAIL, LX0, LZ0, 8.0, LZ0, B(LD), RH)                # lower north, W of stair
    railing(m, RAIL, 12.6, LZ0, LX1, LZ0, B(LD), RH)               # lower north, E of stair

    # --- stairs: east flight down to the gravel strip, north flight to the lawn
    stair(m, DECK, FASCIA, LX1 + 0.1, -36.6, 4.0, (1, 0), B(LD), 0.0,
          width_axis='z')
    stair(m, DECK, FASCIA, 10.3, LZ0 - 0.1, 4.6, (0, -1), B(LD), B(GY),
          width_axis='x')
    # closed stringers down each side of the east flight, following the slope
    for z in (-34.55, -38.65):
        for i in range(5):
            add_box(m, FASCIA, 1.06, B(LD) - i * 0.628 + 0.10, 0.22,
                    LX1 + 0.63 + i * 1.05, 0.0, z)

    return m


if __name__ == "__main__":
    m = build()
    p = os.path.join(OUT, "backyard_deck.glb")
    m.save(p)
    lo, hi = m.bounds()
    print("bounds", [round(v, 2) for v in lo], [round(v, 2) for v in hi])
    print("size KB", round(os.path.getsize(p) / 1024, 1))
    print("place pos", [round(v, 3) for v in world_pos(m, 3, LOW)])
