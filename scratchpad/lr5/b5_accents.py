"""Round 5 accents -- the east canvas regression, and the rest re-placed.

ROUND 4'S EAST CANVAS METERED sd 0.0 OVER 31,500 PX -- a blank slab.  The cause
is in b4_accents.py and it is not a tonal decision at all: the canvas ground is
a 0.06 ft slab centred at x = -0.060, i.e. spanning -0.090..-0.030, and every
mark was drawn at zf = FC * 0.085 = -0.085 -- INSIDE that slab.  Round 4 painted
the composition and then buried it a hundredth of a foot deep.  Marks now sit at
-0.100, clear of the ground's front face at -0.090.

So the fix is round 3's marks on round 4's brighter ground, exactly as asked,
and CANVAS_E stays at #f6f4ef.  The round-4 report proposed dropping it to
#b8b5af to match photo f's canvas/wall RATIO; that reasoning is dead now for a
second reason as well as the one the critic gave -- with the per-wall skins the
east wall renders 168.0 instead of 135.8, so #f6f4ef lands the ratio at ~1.3
against photo f's own 154.8 / 113.5 = 1.36.  The ratio and the white canvas are
no longer in conflict.

Composition, read off p5_art.png at native resolution: an off-white ground; a
pale grey stepped wash across the north (left) two thirds; a short heavy black
bar low on the left; a large solid black block, ragged-edged, right of centre and
low, covering ~20% of the canvas; a small grey vertical mark upper right.
"""
import math
import os
import random

from kit5 import *
from kit5 import Part, Material, Model

rnd = random.Random(9111)

T_CAN = Tex(noise_tile(64, 0.93, 1.0, seed=97, blur=1), 0.55, "canvasweave")
LC = tex_lift(T_CAN)


def lift(hexc, f):
    r, g, b = (int(hexc[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % tuple(min(255, int(round(c * f))) for c in (r, g, b))


FRAME_E = Material("lraframee", "#2f3033", roughness=0.45)
CANVAS_E = TMaterial("lracanvase", lift("#f6f4ef", LC), tex=T_CAN, roughness=0.42)
WASH = Material("lrawash", "#dbd8d2", roughness=0.55)
WASH2 = Material("lrawash2", "#cbc7c1", roughness=0.60)
BLOB = Material("lrablob", "#1a1b1e", roughness=0.88)
FRAME = Material("lraframe", "#cfcbc3", roughness=0.5)
CANVAS = Material("lracanvas", "#e8e5df", roughness=0.55)
CANVAS2 = Material("lracanvas2", "#dcd8d1", roughness=0.9)
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

T_CU = Tex(noise_tile(64, 0.72, 1.0, seed=53), 1.05, "cushion")
LCU = tex_lift(T_CU)
CUSH = TMaterial("lrcushA", lift("#a8a49b", LCU), tex=T_CU, roughness=0.97)
CUSH2 = Material("lrcushB", "#9e9a91", roughness=0.97)
BLANK = TMaterial("lrcblank", lift("#767a7e", LCU), tex=T_CU, roughness=0.98)
BLANK2 = TMaterial("lrcblank2", lift("#6c7075", LCU), tex=T_CU, roughness=0.98)

# ------------------------------------------------------------------ canvases
# `face` is the sign of the room-inward X direction: -1 on the EAST wall.
AL, AH, FC = 5.60, 2.00, -1.0
m = Model()
m.add(box(0.11, AH, AL), FRAME_E, at=(0, 0, 0))
add5(m, tbox(0.06, AH - 0.11, AL - 0.11, repeat=T_CAN.repeat), CANVAS_E,
     at=(FC * 0.060, 0.055, 0))
ZM = FC * 0.100                       # CLEAR of the ground's front face


def plate(mat, z0, z1, y0, y1, depth=0.0):
    v = [(ZM + FC * depth, y0, z0), (ZM + FC * depth, y0, z1),
         (ZM + FC * depth, y1, z1), (ZM + FC * depth, y1, z0)]
    m.add(Part(v, [(0, 1, 2), (0, 2, 3)]), mat)


def blot(cz, cy, rz, ry, seed, n=26, depth=0.010, mat=BLOB):
    """An ORGANIC closed shape in the canvas plane."""
    r = random.Random(seed)
    p1, p2, p3 = r.uniform(0, 6), r.uniform(0, 6), r.uniform(0, 6)
    v = []
    for k in range(n):
        a = 2 * math.pi * k / n
        f = (1.0 + 0.20 * math.sin(3 * a + p1) + 0.11 * math.sin(5 * a + p2)
             + 0.06 * math.sin(7 * a + p3))
        v.append((ZM + FC * depth, cy + ry * f * math.sin(a),
                  cz + rz * f * math.cos(a)))
    m.add(Part(v, [(0, i, i + 1) for i in range(1, n - 1)]), mat)


# pale stepped wash across the north (left) two thirds -- three rectangles that
# step down, which is what reads as one shape with a stepped edge
plate(WASH, -2.55, -0.05, 1.02, 1.72, 0.002)
plate(WASH, -2.55, -1.05, 0.72, 1.02, 0.004)
plate(WASH2, -2.45, -1.55, 1.10, 1.60, 0.006)
plate(WASH2, -0.60, 0.35, 1.28, 1.74, 0.006)
# the heavy short black bar, low on the left
plate(BLOB, -2.45, -1.55, 0.665, 0.735, 0.010)
plate(WASH2, -1.55, -1.05, 0.680, 0.720, 0.010)
# a small grey vertical mark upper right, and a faint plate low centre
plate(WASH2, 0.72, 0.86, 1.28, 1.78, 0.006)
plate(WASH, -0.75, 0.05, 0.14, 0.44, 0.004)
# the black block: ~20% of the canvas, ragged, right of centre and low
blot(0.72, 0.60, 0.72, 0.42, 7, n=30, depth=0.012)
put("Living Art East", save5(m, "art_e5"), (20.44, 4.37, 7.05))

AL, AH, FC = 2.40, 1.90, 1.0
m = Model()
m.add(box(0.10, AH, AL), FRAME, at=(0, 0, 0))
m.add(box(0.05, AH - 0.12, AL - 0.12), CANVAS, at=(FC * 0.055, 0.06, 0))
zf = FC * 0.095
m.add(box(0.02, 0.92, 1.15), BLUSH, at=(zf, 0.52, -0.32))
m.add(box(0.02, 0.46, 0.72), BLUSH2, at=(zf + FC * 0.006, 0.70, -0.10))
m.add(box(0.02, 0.66, 0.80), GREYB, at=(zf + FC * 0.012, 0.22, 0.55))
m.add(box(0.02, 0.20, 1.30), WARM, at=(zf + FC * 0.018, 1.34, 0.20))
put("Living Art West", save5(m, "art_w5"), (0.05, 4.05, 8.20))

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
put("Living Corner Plant", save5(m, "plant5"), (10.55, 0.0, 16.00))

# ------------------------------------------------------------------ tower fan
m = Model()
m.add(cylinder(0.52, 0.10, seg=22), DARKM, at=(0, 0, 0))
m.add(cylinder(0.30, 0.22, seg=22, r_top=0.24), DARKM, at=(0, 0.10, 0))
m.add(cylinder(0.24, 1.05, seg=22, r_top=0.20), DARKM, at=(0, 0.32, 0))
m.add(torus(0.52, 0.105, seg=26, ring=8), CHROME, at=(0, 1.95, 0), rot_x=math.pi / 2)
m.add(cylinder(0.20, 0.42, seg=20, r_top=0.30), DARKM, at=(0, 1.37, 0))
put("Living Tower Fan", save5(m, "towerfan5"), (1.45, 0.0, 5.65))

# --------------------------------------------------------------- floor cushion
m = Model()
add5(m, puff5(2.55, 0.82, 2.35, r=0.40, cell=0.22, uv_repeat=T_CU.repeat,
              grain=Grain(91, fine=0.40, fine_amp=0.014, coarse=0.9,
                          coarse_amp=0.022)), CUSH, at=(0, 0, 0))
m.add(box(2.50, 0.05, 2.30), CUSH2, at=(0, 0.40, 0))
for k in range(3):
    add5(m, drape5(1.65, 1.15 - 0.10 * k, sag=0.04, edge_drop=0.12, cell=0.18,
                   uv_repeat=T_CU.repeat),
         BLANK if k % 2 else BLANK2, at=(1.55, 0.28 + 0.11 * k, 0.34),
         rot_y=0.24)
put("Living Cushions", save5(m, "cushions5"), (9.40, 0.0, 13.70))

put("Living Pet Crate", os.path.join(OUT, "crate.glb"), (13.05, 0.0, 15.30), rot=8)
