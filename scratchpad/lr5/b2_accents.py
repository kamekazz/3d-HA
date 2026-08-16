"""Accents and the lived-in clutter the photos are full of: the bladeless tower
fan, the wire plant etagere, a floor plant, the white wire pet crate, a blanket
basket and floor cushions."""
import math
import random

from kit2 import *

rnd = random.Random(78)

DARKM = Material("lradark", "#3a3b3f", roughness=0.55)
CHROME = Material("lrchrome", "#b7babe", roughness=0.35, metallic=0.6)
WIRE = Material("lrwire", "#c6c2ba", roughness=0.5, metallic=0.3)
WHITEW = Material("lrwhitew", "#c9c8c4", roughness=0.5, metallic=0.2)
POT = Material("lrpot", "#9b9892", roughness=0.8)
POT2 = Material("lrpot2", "#807c74", roughness=0.85)
FOLI = Material("lrfoli", "#54604a", roughness=0.9)
FOLI2 = Material("lrfoli2", "#5f6b54", roughness=0.9)
BASKET = Material("lrbasket", "#8a8272", roughness=0.95)
BLANK1 = Material("lrblank1", "#8d8981", roughness=0.99)
BLANK2 = Material("lrblank2", "#6a696d", roughness=0.99)
CUSH = Material("lrcush", "#9c9993", roughness=0.96)
CUSH2 = Material("lrcush2", "#6d6a64", roughness=0.96)

# ------------------------------------------------------------ tower fan
m = Model()
m.add(cylinder(0.52, 0.10, seg=22), DARKM, at=(0, 0, 0))
m.add(cylinder(0.30, 0.22, seg=22, r_top=0.24), DARKM, at=(0, 0.10, 0))
m.add(cylinder(0.24, 1.05, seg=22, r_top=0.20), DARKM, at=(0, 0.32, 0))
m.add(torus(0.52, 0.105, seg=26, ring=8), CHROME, at=(0, 1.95, 0), rot_x=math.pi / 2)
m.add(cylinder(0.20, 0.42, seg=20, r_top=0.30), DARKM, at=(0, 1.37, 0))
put("Living Tower Fan", save(m, "towerfan2"), (1.10, 0.0, 5.20))

# ------------------------------------------------------------ wire etagere
m = Model()
H, W_, D_ = 5.05, 1.20, 0.85
for sx in (-1, 1):
    for sz in (-1, 1):
        m.add(box(0.05, H, 0.05), WIRE, at=(sx * (W_ / 2 - 0.05), 0, sz * (D_ / 2 - 0.05)))
for i, sy in enumerate((0.52, 1.78, 3.02, 4.28)):
    m.add(box(W_, 0.05, D_), WIRE, at=(0, sy, 0))
    m.add(box(W_, 0.09, 0.04), WIRE, at=(0, sy + 0.05, D_ / 2 - 0.03))
    for k in range(2):
        px = -W_ / 4 + k * W_ / 2 + rnd.uniform(-0.08, 0.08)
        r = rnd.uniform(0.14, 0.20)
        m.add(cylinder(r, r * 1.5, seg=12), POT if (i + k) % 2 else POT2,
              at=(px, sy + 0.05, rnd.uniform(-0.08, 0.08)))
        for j in range(5):
            a = 2 * math.pi * j / 5 + i
            m.add(box(0.10, 0.42, 0.10), FOLI if j % 2 else FOLI2,
                  at=(px + 0.12 * math.cos(a), sy + 0.05 + r * 1.5, 0.12 * math.sin(a)),
                  rot_z=0.45 * math.cos(a), rot_x=0.45 * math.sin(a))
m.add(torus(0.34, 0.03, seg=24, ring=6), WIRE, at=(0, H - 0.10, 0))
put("Living Etagere", save(m, "etagere2"), (19.80, 0.0, 0.72))

# ------------------------------------------------------------ corner plant
m = Model()
m.add(cylinder(0.60, 0.92, seg=18, r_top=0.70), POT, at=(0, 0, 0))
m.add(cylinder(0.64, 0.10, seg=18), POT2, at=(0, 0.92, 0))
m.add(cylinder(0.09, 2.05, seg=8), Material("lrstem", "#6a5f54", roughness=0.9),
      at=(0, 0.92, 0))
for j in range(15):
    a = 2 * math.pi * j / 15 * 1.6
    h = 1.28 + 1.55 * (j / 15)
    r = 0.95 - 0.35 * (j / 15)
    m.add(box(0.60, 0.06, 0.44), FOLI if j % 2 else FOLI2,
          at=(r * math.cos(a) * 0.6, h, r * math.sin(a) * 0.6), rot_y=a, rot_z=0.35)
put("Living Corner Plant", save(m, "plant2"), (19.50, 0.0, 15.40))

# ------------------------------------------------------------ wire pet crate
# The white wire crate in the foreground of photo B.
m = Model()
CW_, CH_, CD_ = 2.40, 1.95, 1.70
for sx in (-1, 1):
    m.add(box(0.05, CH_, CD_ - 0.05), WHITEW, at=(sx * (CW_ / 2 - 0.03), 0, 0))
for sz in (-1, 1):
    m.add(box(CW_ - 0.05, 0.05, 0.05), WHITEW, at=(0, CH_ - 0.03, sz * (CD_ / 2 - 0.03)))
    m.add(box(CW_ - 0.05, 0.05, 0.05), WHITEW, at=(0, 0.02, sz * (CD_ / 2 - 0.03)))
for i in range(11):                     # front + back bars
    x = -CW_ / 2 + CW_ * (i + 0.5) / 11
    for sz in (-1, 1):
        m.add(box(0.045, CH_, 0.045), WHITEW, at=(x, 0, sz * (CD_ / 2 - 0.03)))
for i in range(8):                      # side bars
    z = -CD_ / 2 + CD_ * (i + 0.5) / 8
    for sx in (-1, 1):
        m.add(box(0.045, CH_, 0.045), WHITEW, at=(sx * (CW_ / 2 - 0.03), 0, z))
for i in range(5):                      # top bars
    z = -CD_ / 2 + CD_ * (i + 0.5) / 5
    m.add(box(CW_, 0.045, 0.045), WHITEW, at=(0, CH_ - 0.02, z))
m.add(box(CW_ - 0.10, 0.10, CD_ - 0.10), Material("lrtray2", "#97948e", roughness=0.7),
      at=(0, 0.05, 0))
m.add(sag_plane(1.9, 1.3, sag=0.06, nx=7, nz=6, edge_drop=0.12), BLANK1,
      at=(0, 0.24, 0))
put("Living Pet Crate", save(m, "crate"), (12.50, 0.0, 15.40), rot=8)

# ------------------------------------------------------------ blanket basket
m = Model()
m.add(cylinder(0.62, 1.05, seg=20, r_top=0.68), BASKET, at=(0, 0, 0))
for i in range(9):
    m.add(torus(0.63 + 0.005 * (i % 2), 0.035, seg=22, ring=5), BASKET,
          at=(0, 0.09 + i * 0.11, 0))   # HORIZONTAL: rot_x would stand it up
m.add(sag_plane(1.35, 1.25, sag=0.10, nx=7, nz=7, edge_drop=0.36), BLANK1,
      at=(0, 1.16, 0))
m.add(sag_plane(1.05, 0.95, sag=0.08, nx=6, nz=6, edge_drop=0.30), BLANK2,
      at=(0.16, 1.30, -0.10), rot_y=0.5)
put("Living Basket", save(m, "basket"), (4.30, 0.0, 12.20))

# ------------------------------------------------------------ floor cushions
# Photo B leaves a big cream cushion and a folded blanket on the floor.
m = Model()
m.add(rounded_box(1.85, 0.42, 1.65, r=0.28, seg=4), CUSH, at=(0, 0, 0), rot_y=0.2)
m.add(rounded_box(1.35, 0.32, 1.20, r=0.22, seg=4), CUSH2,
      at=(1.05, 0.0, 0.80), rot_y=-0.45)
m.add(sag_plane(1.5, 1.2, sag=0.05, nx=6, nz=6, edge_drop=0.10), BLANK2,
      at=(1.15, 0.36, 0.85), rot_y=-0.45)
put("Living Cushions", save(m, "cushions"), (10.20, 0.0, 12.90))
