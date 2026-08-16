"""Round 3 accents: two DIFFERENT canvases, a real houseplant instead of a
cartoon fir, and the clutter shuffled clear of the new second east sofa.

Critic item 11.
"""
import math
import random

from kit3 import *
from kit3 import Part, Material, Model

rnd = random.Random(9111)

FRAME = Material("lraframe", "#cfcbc3", roughness=0.5)
CANVAS = Material("lracanvas", "#c6c3bd", roughness=0.9)
CANVAS2 = Material("lracanvas2", "#b7b3ac", roughness=0.9)
BLOB = Material("lrablob", "#2c2d2f", roughness=0.85)
WARM = Material("lrawarm", "#a89b91", roughness=0.9)
BLUSH = Material("lrablush", "#c0a9a4", roughness=0.9)
BLUSH2 = Material("lrablush2", "#ab938f", roughness=0.9)
GREYB = Material("lragrey", "#8d8a85", roughness=0.9)

POT = Material("lrpot", "#a3a09a", roughness=0.8)
POT2 = Material("lrpot2", "#84807a", roughness=0.85)
SOIL = Material("lrsoil", "#3b3630", roughness=0.98)
STEM = Material("lrstem", "#4e5a44", roughness=0.9)
FOLI = Material("lrfoli", "#4e5a45", roughness=0.9)
FOLI2 = Material("lrfoli2", "#5c6a51", roughness=0.9)
FOLI3 = Material("lrfoli3", "#69775c", roughness=0.9)

DARKM = Material("lradark", "#3a3b3f", roughness=0.55)
CHROME = Material("lrchrome", "#b7babe", roughness=0.35, metallic=0.6)


# ------------------------------------------------------------------ canvases
# ITEM 11 (part).  Round 2 shipped Art East and Art West as the same pink/grey
# composition.  Photo f's east canvas is a wide white field with ONE solid
# black organic blob right of centre; photo A/B's west piece is a small blush
# and warm-grey abstract.  They are now unmistakably different pictures.
# `face` is the sign of the room-inward X direction: -1 for a canvas hung on
# the EAST wall (it looks west, into the room), +1 for the WEST wall.  Round 3
# note: get this wrong and the whole composition is painted on the back of the
# frame and the room shows a blank rectangle.
def wall_panel(length, height, face, thick=0.09):
    m = Model()
    m.add(box(thick, height, length), FRAME, at=(0, 0, 0))
    m.add(box(thick * 0.5, height - 0.13, length - 0.13), CANVAS,
          at=(face * thick * 0.55, 0.065, 0))
    return m


# --- east: wide white canvas, one black blob (photo f)
AL, AH, FC = 5.60, 2.00, -1.0
m = wall_panel(AL, AH, FC)
zf = FC * 0.075
for (cz, cy, w, h) in ((0.55, 1.02, 1.30, 0.86), (0.95, 0.88, 0.86, 0.62),
                       (0.30, 1.18, 0.70, 0.44), (0.72, 0.60, 0.62, 0.34)):
    m.add(box(0.02, h, w), BLOB, at=(zf, cy - h / 2, cz))
for (cz, cy, w, h, mat) in ((-1.70, 1.20, 1.60, 0.30, WARM),
                            (-1.20, 0.72, 1.10, 0.22, CANVAS2),
                            (-2.00, 0.60, 0.90, 0.18, WARM),
                            (-0.35, 1.52, 1.20, 0.16, CANVAS2)):
    m.add(box(0.018, h, w), mat, at=(zf + FC * 0.006, cy - h / 2, cz))
put("Living Art East", save(m, "art_e3"), (20.44, 4.37, 7.05))

# --- west: small blush / warm-grey abstract (photo A, photo B right edge)
AL, AH, FC = 2.40, 1.90, 1.0
m = Model()
m.add(box(0.10, AH, AL), FRAME, at=(0, 0, 0))
m.add(box(0.05, AH - 0.12, AL - 0.12), CANVAS, at=(FC * 0.055, 0.06, 0))
zf = FC * 0.08
m.add(box(0.02, 0.92, 1.15), BLUSH, at=(zf, 0.52, -0.32))
m.add(box(0.02, 0.46, 0.72), BLUSH2, at=(zf + FC * 0.006, 0.70, -0.10))
m.add(box(0.02, 0.66, 0.80), GREYB, at=(zf + FC * 0.012, 0.22, 0.55))
m.add(box(0.02, 0.20, 1.30), WARM, at=(zf + FC * 0.018, 1.34, 0.20))
put("Living Art West", save(m, "art_w3"), (0.05, 4.05, 8.20))

# ------------------------------------------------------------------ houseplant
# ITEM 11 (part).  Round 2's plant was a helix of boxes climbing a stick -- a
# cartoon fir tree.  This is a broad-leafed floor plant: tapered pot, soil,
# arching stems, and leaf BLADES (tapered hexagons) at three greens.
LEAF = [(0.0, 0.0), (0.13, 0.16), (0.15, 0.48), (0.0, 0.78),
        (-0.15, 0.48), (-0.13, 0.16)]
m = Model()
m.add(cylinder(0.52, 1.05, seg=20, r_top=0.66), POT, at=(0, 0, 0))
m.add(cylinder(0.68, 0.11, seg=20), POT2, at=(0, 1.03, 0))
m.add(cylinder(0.60, 0.06, seg=18), SOIL, at=(0, 1.08, 0))
for j in range(22):
    a = 2 * math.pi * j / 22 * 1.37 + rnd.uniform(-0.2, 0.2)
    h = 1.30 + 1.75 * ((j * 7) % 22) / 22.0
    r = 0.30 + 0.85 * (1.0 - (h - 1.30) / 1.75)
    px, pz = r * math.cos(a), r * math.sin(a)
    m.add(cylinder(0.035, math.hypot(h - 1.10, r) * 0.9, seg=6), STEM,
          at=(px * 0.35, 1.08, pz * 0.35), rot_x=-0.55 * math.sin(a),
          rot_z=0.55 * math.cos(a))
    m.add(prism(LEAF, 0.035), (FOLI, FOLI2, FOLI3)[j % 3],
          at=(px, h, pz), rot_x=math.pi / 2 - rnd.uniform(0.25, 0.75),
          rot_y=a + math.pi / 2, rot_z=rnd.uniform(-0.3, 0.3),
          scale=(rnd.uniform(0.85, 1.25),) * 3)
put("Living Corner Plant", save(m, "plant3"), (10.55, 0.0, 16.00))

# ------------------------------------------------------------------ tower fan
# Nudged clear of the widened armchair and of the fireplace hearth.
m = Model()
m.add(cylinder(0.52, 0.10, seg=22), DARKM, at=(0, 0, 0))
m.add(cylinder(0.30, 0.22, seg=22, r_top=0.24), DARKM, at=(0, 0.10, 0))
m.add(cylinder(0.24, 1.05, seg=22, r_top=0.20), DARKM, at=(0, 0.32, 0))
m.add(torus(0.52, 0.105, seg=26, ring=8), CHROME, at=(0, 1.95, 0), rot_x=math.pi / 2)
m.add(cylinder(0.20, 0.42, seg=20, r_top=0.30), DARKM, at=(0, 1.37, 0))
put("Living Tower Fan", save(m, "towerfan3"), (1.45, 0.0, 5.65))

# ---------------------------------------------------- clutter, re-spaced
# Same pieces, moved clear of the plant and the relocated coffee table.
import os
put("Living Pet Crate", os.path.join(OUT, "crate.glb"), (13.05, 0.0, 15.30), rot=8)
put("Living Cushions", os.path.join(OUT, "cushions.glb"), (9.40, 0.0, 13.70))
