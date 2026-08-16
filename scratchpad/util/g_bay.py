"""Garage -- the second bay.

The footprint is a two-car garage (20.4 x 21.7 ft) but the west wall carries a
2.5 ft storage run, so only one car parks comfortably.  The classic real-world
result is that the second bay silts up with yard and household kit; that is
what this piece is.  INFERRED -- there is no interior photo.
"""
import math

from gkit import *   # noqa: F401,F403
import gkit as G

ROOM = 7
TOTE = Material("tote", "#4c525a", roughness=0.70)
TOTE_L = Material("totel", "#b0913f", roughness=0.66)
SOIL = Material("soil", "#3f3a33", roughness=0.92)
COOL = Material("cool", "#c9ccd0", roughness=0.55)
GALV = Material("galv", "#9ba0a4", roughness=0.45, metallic=0.40)


def bay():
    m = Model()

    # --- stack of four storage totes
    for i in range(4):
        y = i * 1.18
        bx(m, TOTE, 6.90, 8.70, y, y + 1.05, 11.35, 13.45)
        bx(m, TOTE_L, 6.84, 8.76, y + 1.05, y + 1.18, 11.28, 13.52)
    # a second, shorter stack beside it
    for i in range(2):
        y = i * 0.92
        bx(m, TOTE, 7.10, 8.60, y, y + 0.80, 13.80, 15.30)
        bx(m, G.BLUE, 7.04, 8.66, y + 0.80, y + 0.92, 13.74, 15.36)

    # --- stacked bags of soil / salt
    for i, (y, dx, dz) in enumerate(((0.00, 0.0, 0.0), (0.42, 0.10, 0.14),
                                     (0.84, -0.06, 0.06), (1.26, 0.14, -0.08))):
        m.add(rounded_box(2.15, 0.44, 1.35, 0.20, 3), SOIL if i % 2 else G.ORANGE,
              at=(4.55 + dx, y, 15.95 + dz), rot_y=G.R(4 * i))

    # --- cooler
    m.add(rounded_box(1.55, 1.55, 2.35, 0.14, 3), COOL, at=(6.05, 0.0, 18.15))
    bx(m, G.BLUE, 5.24, 6.86, 1.55, 1.75, 16.94, 19.36)
    bx(m, G.WHITE, 5.30, 5.42, 0.85, 1.12, 17.55, 18.75)

    # --- folded patio chairs leaning on nothing much, against the tote stack
    for i, dz in enumerate((0.0, 0.28, 0.56)):
        sub = Model()
        sub.add(box(0.10, 3.35, 1.75), G.GREEN if i == 1 else G.STEEL_D, at=(0, 0, 0))
        for part, mat in sub._parts:
            m.add(part, mat, at=(3.75 + i * 0.16, 0.0, 12.55 + dz), rot_z=G.R(11))

    # --- wheelbarrow, tipped up on its nose against the wall side
    wb = Model()
    tub = prism([(-1.05, -1.35), (1.05, -1.35), (0.80, 1.30), (-0.80, 1.30)], 0.95)
    wb.add(tub, G.GREEN, at=(0.0, 0.55, 0.0))
    for dx in (-0.55, 0.55):
        wb.add(box(0.11, 0.11, 3.95), G.OAKEDGE, at=(dx, 0.42, 0.55))
        wb.add(box(0.12, 0.62, 0.12), G.STEEL_D, at=(dx, 0.0, -0.55))
    wb.add(cylinder(0.52, 0.30, 14, anchor="center"), G.BLKR,
           at=(0.0, 0.52, -1.75), rot_z=G.R(90))
    for part, mat in wb._parts:
        m.add(part, mat, at=(4.35, 0.0, 19.05), rot_y=G.R(-14))

    # --- kids' wagon
    m.add(rounded_box(1.95, 0.70, 3.05, 0.16, 3), G.RED, at=(7.85, 0.62, 17.35))
    for (dx, dz) in ((-0.72, -1.05), (0.72, -1.05), (-0.72, 1.05), (0.72, 1.05)):
        m.add(cylinder(0.34, 0.22, 12, anchor="center"), G.BLKR,
              at=(7.85 + dx, 0.34, 17.35 + dz), rot_z=G.R(90))
    m.add(box(0.09, 2.15, 0.09), G.BLK, at=(7.85, 0.30, 16.10), rot_x=G.R(-52))

    # --- sports bin with a couple of balls
    bx(m, TOTE, 3.55, 5.35, 0.0, 1.35, 11.20, 12.15)
    m.add(cylinder(0.42, 0.42, 14, r_top=0.30), G.ORANGE, at=(4.10, 1.35, 11.70))
    m.add(cylinder(0.34, 0.34, 14, r_top=0.24), G.WHITE, at=(4.85, 1.35, 11.55))

    # --- galvanised buckets + a paint stack
    for i, (cx, cz) in enumerate(((6.55, 15.95), (6.55, 15.95), (5.95, 19.75))):
        m.add(cylinder(0.55, 0.90, 14, r_top=0.48), GALV,
              at=(cx, 0.92 * (1 if i == 1 else 0), cz))
    return m


if __name__ == "__main__":
    G.save_and_place("Garage Bay Storage", bay(), ROOM)
