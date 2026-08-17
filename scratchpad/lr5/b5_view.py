"""Round 5 outdoor boards -- same three views, re-cut to fit their openings.

Round 3 built each board 1.7 ft OUTSIDE the wall and a good 3 ft wider than the
opening it backs.  Seen through the window that is correct; seen from the
dollhouse quadrant it is a coloured slab standing in the yard outside the shell,
and the round-4 report listed it as a known gap.  Each board now sits 0.30 ft
behind its opening and overhangs the aperture by ~0.7 ft, which still covers the
parallax out to 68 degrees of view angle but tucks the whole board behind the
wall from outside.  Blob counts are also roughly halved: the three boards were
190 KB of the room's payload for scenery seen through three holes.


Critic item 12: round 2's boards were six full-width colour bands, so every
opening framed flat painted cardboard with a hard horizon.  Now: a five-step
sky gradient, a haze band at the horizon, a treeline built from 34 overlapping
irregular canopy blobs at four greens (so the skyline is ragged, never a line),
trunks behind them, a shrub row, and a grass field with soft patches.

Layers are stacked towards the room along `push`, so the nearest thing (the
deck rail, the fence) is drawn last and highest.
"""
import math
import random

from kit3 import *
from kit3 import Part, Material, Model

rnd = random.Random(4242)

SKY = [Material("lroskyA", "#93aec9", roughness=0.95),
       Material("lroskyB", "#a8bfd4", roughness=0.95),
       Material("lroskyC", "#becfdd", roughness=0.95),
       Material("lroskyD", "#d2dee5", roughness=0.95),
       Material("lroskyE", "#e2e8e9", roughness=0.95)]
HAZE = Material("lrohaze", "#c9d5d5", roughness=0.95)
TREE = [Material("lrotreeA", "#4f5c48", roughness=0.96),
        Material("lrotreeB", "#5e6c53", roughness=0.96),
        Material("lrotreeC", "#6d7b5f", roughness=0.96),
        Material("lrotreeD", "#7d8a6c", roughness=0.96)]
TRUNK = Material("lrotrunk", "#4a4640", roughness=0.96)
SHRUB = Material("lroshrub", "#5c6a4d", roughness=0.96)
GRASS = [Material("lrograssA", "#77855f", roughness=0.96),
         Material("lrograssB", "#6d7b56", roughness=0.96),
         Material("lrograssC", "#828f69", roughness=0.96)]
FENCE = Material("lrofence", "#a29d92", roughness=0.9)
RAIL = Material("lrorail", "#dedad2", roughness=0.8)
DECK = Material("lrodeck", "#8b8781", roughness=0.9)
DECK2 = Material("lrodeck2", "#7b7872", roughness=0.9)


def view_board(m, axis, at, push, lo, hi, y0, y1, deck=False):
    h, w = y1 - y0, hi - lo
    hor = y0 + h * (0.62 if deck else 0.58)

    def plate(mat, pts, depth):
        d = at + push * depth
        if axis == "z":
            v3 = [(u, v, d) for (u, v) in pts]
        else:
            v3 = [(d, v, u) for (u, v) in pts]
        n = len(pts)
        m.add(Part(v3, [(0, i, i + 1) for i in range(1, n - 1)]), mat)

    def band(mat, u0, u1, v0, v1, depth):
        plate(mat, [(u0, v0), (u1, v0), (u1, v1), (u0, v1)], depth)

    def blob(cu, cv, ru, rv, seg=11):
        return [(cu + ru * (j := rnd.uniform(0.68, 1.22)) * math.cos(a),
                 cv + rv * j * math.sin(a))
                for a in (2 * math.pi * k / seg for k in range(seg))]

    # sky: five steps, brightest at the horizon
    for i, mat in enumerate(SKY):
        band(mat, lo, hi, y1 - (y1 - hor) * (i + 1) / 5.0,
             y1 - (y1 - hor) * i / 5.0, 0.000)
    band(HAZE, lo, hi, hor - 0.05 * h, hor + 0.08 * h, 0.008)
    # ground
    for i, mat in enumerate(GRASS):
        band(mat, lo, hi, y0 + h * 0.02 * i, hor + 0.02 * h, 0.016)
    for k in range(3):
        plate(GRASS[k % 3], blob(lo + w * rnd.random(),
                                 y0 + (hor - y0) * rnd.uniform(0.05, 0.80),
                                 w * rnd.uniform(0.08, 0.20),
                                 h * rnd.uniform(0.02, 0.05)), 0.024)
    # trunks, then the ragged canopy over them
    for k in range(7):
        u = lo + w * (k + 0.5) / 7 + rnd.uniform(-0.2, 0.2)
        band(TRUNK, u - w * 0.006, u + w * 0.006, hor - 0.01 * h,
             hor + h * rnd.uniform(0.04, 0.11), 0.032)
    for k in range(12):
        u = lo - w * 0.04 + w * 1.08 * (k + rnd.uniform(-0.45, 0.45)) / 12.0
        rv = h * rnd.uniform(0.075, 0.185)
        ru = w * rnd.uniform(0.045, 0.100)
        plate(TREE[k % 4], blob(u, hor + rv * 0.62, ru * 1.7, rv),
              0.040 + 0.0015 * (k % 6))
    for k in range(8):
        u = lo + w * (k + 0.5) / 8
        plate(SHRUB, blob(u, hor - h * 0.005, w * rnd.uniform(0.05, 0.10),
                          h * rnd.uniform(0.018, 0.040)), 0.058)
    if deck:
        band(DECK, lo, hi, y0, y0 + h * 0.24, 0.070)
        for k in range(6):
            band(DECK2, lo, hi, y0 + h * 0.24 * k / 6,
                 y0 + h * 0.24 * (k + 0.30) / 6, 0.074)
        band(RAIL, lo, hi, y0 + h * 0.235, y0 + h * 0.280, 0.082)
        band(RAIL, lo, hi, y0 + h * 0.480, y0 + h * 0.530, 0.082)
        for i in range(14):
            u = lo + w * (i + 0.5) / 14
            band(RAIL, u - w * 0.006, u + w * 0.006, y0 + h * 0.265,
                 y0 + h * 0.495, 0.078)
    else:
        band(FENCE, lo, hi, hor - h * 0.10, hor - h * 0.02, 0.066)
        for i in range(14):
            u = lo + w * (i + 0.5) / 14
            band(FENCE, u - w * 0.004, u + w * 0.004, hor - h * 0.115,
                 hor - h * 0.02, 0.070)


m = Model()      # behind the patio slider (aperture x 12.00..18.85, y 0..6.90)
view_board(m, "z", -0.35, +1.0, 11.25, 19.60, -0.60, 7.60, deck=True)
put_in_place("Living Outdoor View North", m, save(m, "view_n5"))

m = Model()      # behind the east window (aperture z 1.04..4.02, y 2.35..6.90)
view_board(m, "x", 20.79, -1.0, 0.30, 4.80, 1.70, 7.60)
put_in_place("Living Outdoor View East", m, save(m, "view_e5"))

m = Model()      # behind the west window (aperture z 11.90..14.90, y 2.35..6.90)
view_board(m, "x", -0.30, +1.0, 11.15, 15.65, 1.70, 7.60)
put_in_place("Living Outdoor View West", m, save(m, "view_w5"))
