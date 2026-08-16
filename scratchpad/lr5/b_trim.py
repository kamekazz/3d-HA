"""Openings and trim: north window, patio slider, east window, wall art, baseboards.

Windows are flush pieces standing ON the inside wall face (the app draws no real
openings) -- so everything is authored with its BACK at model z=0 and grows
forward into the room.  `wall_pos` then seats that back on the wall plane.
"""
import math
from kit import *

TRIMW = Material("trimw", "#fcfcfa", roughness=0.55, emissive="#3a3a3a")
SKY = Material("osky", "#ffffff", roughness=0.9, emissive="#fbfcfd")
TREE = Material("otree", "#b5c1ad", roughness=0.9, emissive="#9aa793")
FENCE = Material("ofence", "#e2ded4", roughness=0.9, emissive="#bab7ae")
DECK = Material("odeck", "#c0bbb1", roughness=0.9, emissive="#928e87")
RAIL = Material("orail", "#f8f8f6", roughness=0.7, emissive="#b0b0ae")
SHADE = Material("shade", "#f8f7f3", roughness=0.95, emissive="#5e5e5c")


def wall_pos(m, wall, along, y):
    """(x, y, z) for a piece authored back-at-z=0, seated on `wall`."""
    lo, hi = m.bounds()
    d = hi[2] - lo[2]
    if wall == "n":
        return (along, y, d / 2), 0
    if wall == "s":
        return (along, y, RD - d / 2), 180
    if wall == "e":
        return (RW - d / 2, y, along), 270
    return (d / 2, y, along), 90


def outside(m, w, h, z0, deck=False):
    if deck:
        bands = [(0.00, 0.40, SKY), (0.40, 0.62, TREE), (0.62, 0.72, FENCE),
                 (0.72, 1.00, DECK)]
    else:
        bands = [(0.00, 0.54, SKY), (0.54, 0.78, TREE), (0.78, 0.90, FENCE),
                 (0.90, 1.00, DECK)]
    for (a, b, mat) in bands:
        bh = (b - a) * h
        m.add(box(w, bh, 0.02), mat, at=(0, (1 - b) * h, z0 + 0.01))
    if deck:
        m.add(box(w, 0.11, 0.02), RAIL, at=(0, 0.285 * h, z0 + 0.03))
        m.add(box(w, 0.08, 0.02), RAIL, at=(0, 0.135 * h, z0 + 0.03))
        for i in range(12):
            m.add(box(0.055, 0.20 * h, 0.02), RAIL,
                  at=(-w / 2 + w * (i + 0.5) / 12, 0.115 * h, z0 + 0.03))


# ------------------------------------------------------------ double hung
def double_hung(w, h, shade_frac=0.17):
    m = Model()
    outside(m, w, h, 0.0)
    # sash bars, sitting just in front of the view
    m.add(box(w, 0.11, 0.05), TRIMW, at=(0, h * 0.50, 0.03))
    m.add(box(0.07, h, 0.04), TRIMW, at=(0, 0, 0.035))
    m.add(box(w, 0.055, 0.04), TRIMW, at=(0, h * 0.25, 0.035))
    m.add(box(w, 0.055, 0.04), TRIMW, at=(0, h * 0.75, 0.035))
    # shade parked at the head
    m.add(box(w - 0.03, shade_frac * h, 0.09), SHADE, at=(0, h * (1 - shade_frac), 0.04))
    # casing
    cw = w + 0.44
    m.add(box(cw, 0.22, 0.14), TRIMW, at=(0, h, 0.10))
    m.add(box(cw + 0.16, 0.09, 0.22), TRIMW, at=(0, h + 0.22, 0.10))
    for sx in (-1, 1):
        m.add(box(0.22, h + 0.22, 0.14), TRIMW, at=(sx * (cw / 2 - 0.11), 0, 0.10))
    m.add(box(cw + 0.20, 0.09, 0.44), TRIMW, at=(0, -0.09, 0.10))       # stool
    m.add(box(cw - 0.08, 0.28, 0.13), TRIMW, at=(0, -0.37, 0.10))       # apron
    return m


WW, WH = 3.05, 4.60
SILL = 2.42
m = double_hung(WW, WH)
p = save(m, "win_n")
pos, rot = wall_pos(m, "n", 4.30, SILL - 0.46)
put("Living Window North", p, pos, rot)

m = double_hung(WW, WH)
p = save(m, "win_e")
pos, rot = wall_pos(m, "e", 3.40, SILL - 0.46)
put("Living Window East", p, pos, rot)

# ------------------------------------------------------------ patio slider
SW, SH = 6.30, 6.85
m = Model()
outside(m, SW, SH, 0.0, deck=True)
m.add(box(0.20, SH, 0.07), TRIMW, at=(0, 0, 0.05))
for sx in (-1, 1):
    m.add(box(0.17, SH, 0.07), TRIMW, at=(sx * (SW / 2 - 0.085), 0, 0.05))
m.add(box(SW, 0.15, 0.07), TRIMW, at=(0, SH - 0.15, 0.05))
m.add(box(SW, 0.15, 0.07), TRIMW, at=(0, 0.0, 0.05))
for i in range(6):                     # vertical-blind stack at the left jamb
    m.add(box(0.11, SH - 0.34, 0.06), SHADE,
          at=(-SW / 2 + 0.26 + i * 0.12, 0.17, 0.10), rot_y=0.55)
m.add(box(SW + 0.46, 0.22, 0.15), TRIMW, at=(0, SH, 0.09))
m.add(box(SW + 0.62, 0.10, 0.24), TRIMW, at=(0, SH + 0.22, 0.09))
for sx in (-1, 1):
    m.add(box(0.23, SH + 0.22, 0.15), TRIMW, at=(sx * (SW / 2 + 0.115), 0, 0.09))
m.add(box(SW + 0.46, 0.10, 0.20), TRIMW, at=(0, -0.10, 0.07))
p = save(m, "slider")
pos, rot = wall_pos(m, "n", 25.60, 0.0)
put("Living Slider", p, pos, rot)

# ------------------------------------------------------------ framed art
FRAME = Material("frame", "#eeece7", roughness=0.5, emissive="#303030")
CANV = Material("canv", "#f4f1eb", roughness=0.9, emissive="#414040")
BLUSH = Material("blush", "#e5d1c8", roughness=0.9, emissive="#3d3633")
GREYA = Material("greya", "#bab4ae", roughness=0.9, emissive="#302e2c")
INK = Material("ink", "#3c3c3e", roughness=0.8, emissive="#121212")

AW, AH = 1.86, 2.36
m = Model()
m.add(box(AW, AH, 0.05), FRAME, at=(0, 0, 0.025))
m.add(box(AW - 0.10, AH - 0.10, 0.02), CANV, at=(0, 0.05, 0.055))
m.add(box(AW - 0.52, 1.05, 0.01), BLUSH, at=(-0.10, 0.75, 0.068), rot_z=0.10)
m.add(box(AW - 0.85, 0.62, 0.01), GREYA, at=(0.22, 0.45, 0.070), rot_z=-0.16)
p = save(m, "art_n")
pos, rot = wall_pos(m, "n", 7.35, 5.30 - AH / 2)
put("Living Art North", p, pos, rot)

BW, BH = 5.70, 2.05
m = Model()
m.add(box(BW, BH, 0.06), FRAME, at=(0, 0, 0.03))
m.add(box(BW - 0.10, BH - 0.10, 0.02), CANV, at=(0, 0.05, 0.065))
m.add(box(1.70, 1.15, 0.01), BLUSH, at=(-1.55, 0.55, 0.078), rot_z=0.06)
m.add(box(1.05, 0.80, 0.01), GREYA, at=(0.15, 0.95, 0.078), rot_z=-0.09)
m.add(box(0.95, 0.62, 0.01), INK, at=(1.55, 0.60, 0.078), rot_z=0.12)
m.add(box(0.55, 0.30, 0.01), GREYA, at=(2.20, 1.15, 0.078))
p = save(m, "art_e")
pos, rot = wall_pos(m, "e", 9.60, 6.05 - BH / 2)
put("Living Art East", p, pos, rot)

# ------------------------------------------------------------ baseboards
BB = Material("bb", "#fbfbf8", roughness=0.6, emissive="#3c3c3c")
BBP = [(0.0, 0.0), (0.0, 0.082), (0.40, 0.082), (0.455, 0.055), (0.47, 0.0)]
m = Model()
run_with_gaps(m, BB, BBP, "n", 0.0, (-RW / 2, RW / 2),
              [(lx(8.80), lx(14.40)), (lx(22.20), lx(29.00))], -RD / 2)
run_with_gaps(m, BB, BBP, "s", 0.0, (-RW / 2, RW / 2), [], RD / 2)
run_with_gaps(m, BB, BBP, "e", 0.0, (-RD / 2, RD / 2), [], RW / 2)
run_with_gaps(m, BB, BBP, "w", 0.0, (-RD / 2, RD / 2), [], -RW / 2)
p = save(m, "baseboards")
put("Living Baseboards", p, (RW / 2, 0.0, RD / 2))
