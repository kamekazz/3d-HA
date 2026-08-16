"""Round 4 accents -- ITEM 7 (Art East) and ITEM 8 (the floor cushion).

ITEM 7: round 3's east canvas used a mid-grey ground (#c6c3bd) and a frame the
same colour as its own canvas, so it metered 89 against an east wall of 98 --
i.e. a panel painted the wall's own value, not the white canvas photo f shows.
The ground goes near-white and smooth (a smoother material collects more
environment specular in this scene -- ROOM-BRIEF's own note), and the frame
becomes a slim DARK border so the piece has an outline against the wall
whatever the wall lands at.

ITEM 8: "Living Cushions" was a rounded box under a sag plane and read as a
curved white pod.  It is now a plump square floor cushion plus a folded
blanket, which is what photo B leaves on the rug.

Everything else here is round 3's, re-placed unchanged so the file stays the
single idempotent source for these objects.
"""
import math
import os
import random

from kit4 import *
from kit4 import Part, Material, Model

rnd = random.Random(9111)

# ITEM 7: near-white ground, slim dark frame.
FRAME_E = Material("lraframee", "#2f3033", roughness=0.45)
CANVAS_E = Material("lracanvase", "#f6f4ef", roughness=0.42)
FRAME = Material("lraframe", "#cfcbc3", roughness=0.5)
CANVAS = Material("lracanvas", "#e8e5df", roughness=0.55)
CANVAS2 = Material("lracanvas2", "#dcd8d1", roughness=0.9)
BLOB = Material("lrablob", "#232427", roughness=0.85)
WARM = Material("lrawarm", "#c9beb2", roughness=0.9)
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

CUSH = Material("lrcushA", "#a8a49b", roughness=0.97)
CUSH2 = Material("lrcushB", "#9e9a91", roughness=0.97)
BLANK = Material("lrcblank", "#767a7e", roughness=0.98)
BLANK2 = Material("lrcblank2", "#6c7075", roughness=0.98)

# ------------------------------------------------------------------ canvases
# `face` is the sign of the room-inward X direction: -1 on the EAST wall,
# +1 on the WEST wall.  Get it wrong and the composition is painted on the
# back of the frame and the room shows a blank rectangle.
AL, AH, FC = 5.60, 2.00, -1.0
m = Model()
m.add(box(0.11, AH, AL), FRAME_E, at=(0, 0, 0))                     # dark frame
m.add(box(0.06, AH - 0.11, AL - 0.11), CANVAS_E, at=(FC * 0.060, 0.055, 0))
zf = FC * 0.085


def blot(cz, cy, rz, ry, seed, n=26):
    """An ORGANIC closed shape in the canvas plane (x = depth, y = up,
    z = across).  Round 3/4a drew the black mass as four stacked boxes and it
    read as stacked rectangles rather than photo f's single soft blob."""
    r = random.Random(seed)
    p1, p2, p3 = r.uniform(0, 6), r.uniform(0, 6), r.uniform(0, 6)
    v = []
    for k in range(n):
        a = 2 * math.pi * k / n
        f = 1.0 + 0.26 * math.sin(3 * a + p1) + 0.15 * math.sin(5 * a + p2)             + 0.08 * math.sin(7 * a + p3)
        v.append((zf, cy + ry * f * math.sin(a), cz + rz * f * math.cos(a)))
    return Part(v, [(0, i, i + 1) for i in range(1, n - 1)])


m.add(blot(0.62, 0.95, 0.62, 0.40, 7), BLOB)
for (cz, cy, rz, ry, sd, mat) in ((-1.65, 1.18, 0.78, 0.14, 11, WARM),
                                  (-1.15, 0.74, 0.54, 0.10, 13, CANVAS2),
                                  (-2.00, 0.58, 0.44, 0.08, 17, WARM),
                                  (-0.30, 1.50, 0.58, 0.07, 19, CANVAS2)):
    m.add(blot(cz, cy, rz, ry, sd, n=18), mat)
put("Living Art East", save(m, "art_e4"), (20.44, 4.37, 7.05))

AL, AH, FC = 2.40, 1.90, 1.0
m = Model()
m.add(box(0.10, AH, AL), FRAME, at=(0, 0, 0))
m.add(box(0.05, AH - 0.12, AL - 0.12), CANVAS, at=(FC * 0.055, 0.06, 0))
zf = FC * 0.08
m.add(box(0.02, 0.92, 1.15), BLUSH, at=(zf, 0.52, -0.32))
m.add(box(0.02, 0.46, 0.72), BLUSH2, at=(zf + FC * 0.006, 0.70, -0.10))
m.add(box(0.02, 0.66, 0.80), GREYB, at=(zf + FC * 0.012, 0.22, 0.55))
m.add(box(0.02, 0.20, 1.30), WARM, at=(zf + FC * 0.018, 1.34, 0.20))
put("Living Art West", save(m, "art_w4"), (0.05, 4.05, 8.20))

# ------------------------------------------------------------------ houseplant
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
put("Living Corner Plant", save(m, "plant4"), (10.55, 0.0, 16.00))

# ------------------------------------------------------------------ tower fan
m = Model()
m.add(cylinder(0.52, 0.10, seg=22), DARKM, at=(0, 0, 0))
m.add(cylinder(0.30, 0.22, seg=22, r_top=0.24), DARKM, at=(0, 0.10, 0))
m.add(cylinder(0.24, 1.05, seg=22, r_top=0.20), DARKM, at=(0, 0.32, 0))
m.add(torus(0.52, 0.105, seg=26, ring=8), CHROME, at=(0, 1.95, 0), rot_x=math.pi / 2)
m.add(cylinder(0.20, 0.42, seg=20, r_top=0.30), DARKM, at=(0, 1.37, 0))
put("Living Tower Fan", save(m, "towerfan4"), (1.45, 0.0, 5.65))

# --------------------------------------------------------------- floor cushion
# ITEM 8.  A plump square floor cushion (a puff, not a rounded box under a
# sag plane) with a piped seam, plus the folded blanket photo B leaves beside
# it.  NOT named "Floor Cushions" -- that would match objects.js SURFACE_RE
# and make real furniture unpickable.
m = Model()
m.add(puff(2.55, 0.82, 2.35, r=0.40, seg=20, rings=9, nub=0.026, rnd=rnd), CUSH,
      at=(0, 0, 0))
m.add(box(2.50, 0.05, 2.30), CUSH2, at=(0, 0.40, 0))
for k in range(3):
    m.add(sag_plane(1.65, 1.15 - 0.10 * k, sag=0.04, nx=7, nz=5, edge_drop=0.12),
          BLANK if k % 2 else BLANK2, at=(1.55, 0.28 + 0.11 * k, 0.34),
          rot_y=0.24)
put("Living Cushions", save(m, "cushions4"), (9.40, 0.0, 13.70))

# ---------------------------------------------------- clutter, unchanged
put("Living Pet Crate", os.path.join(OUT, "crate.glb"), (13.05, 0.0, 15.30), rot=8)
