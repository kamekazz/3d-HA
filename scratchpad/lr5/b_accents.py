"""Small accents the photos show: tower fan by the armchair, wire plant etagere
next to the slider, a floor plant in the east corner."""
import math, random
from kit import *

rnd = random.Random(77)

DARKM = Material("dark", "#3c3d41", roughness=0.55)
CHROME = Material("chrome", "#b9bcc0", roughness=0.35, metallic=0.6)
WIRE = Material("wire", "#c9c5bd", roughness=0.5, metallic=0.3)
POT = Material("pot", "#e6e2d9", roughness=0.8)
POT2 = Material("pot2", "#bfb9ae", roughness=0.85)
FOLI = Material("foli", "#7e9070", roughness=0.9)
FOLI2 = Material("foli2", "#8fa07f", roughness=0.9)

# ---------------------------------------------------------- tower fan
m = Model()
m.add(cylinder(0.52, 0.10, seg=22), DARKM, at=(0, 0, 0))
m.add(cylinder(0.30, 0.22, seg=22, r_top=0.24), DARKM, at=(0, 0.10, 0))
m.add(cylinder(0.24, 1.05, seg=22, r_top=0.20), DARKM, at=(0, 0.32, 0))
# the bladeless loop
m.add(torus(0.52, 0.105, seg=26, ring=8), CHROME, at=(0, 1.95, 0), rot_x=math.pi / 2)
m.add(cylinder(0.20, 0.42, seg=20, r_top=0.30), DARKM, at=(0, 1.37, 0))
p = save(m, "towerfan")
put("Living Tower Fan", p, (4.5, 0.0, 4.2), rot=0)

# ---------------------------------------------------------- wire etagere
m = Model()
H, W, D = 5.10, 1.85, 1.15
for sx in (-1, 1):
    for sz in (-1, 1):
        m.add(box(0.055, H, 0.055), WIRE,
              at=(sx * (W / 2 - 0.05), 0, sz * (D / 2 - 0.05)))
for i, sy in enumerate((0.55, 1.85, 3.10, 4.35)):
    m.add(box(W, 0.05, D), WIRE, at=(0, sy, 0))
    m.add(box(W, 0.10, 0.04), WIRE, at=(0, sy + 0.05, D / 2 - 0.03))
    # a plant or two per shelf
    for k in range(2):
        px = -W / 4 + k * W / 2 + rnd.uniform(-0.12, 0.12)
        r = rnd.uniform(0.16, 0.24)
        m.add(cylinder(r, r * 1.5, seg=12), POT if (i + k) % 2 else POT2,
              at=(px, sy + 0.05, rnd.uniform(-0.12, 0.12)))
        for j in range(5):
            a = 2 * math.pi * j / 5 + i
            m.add(box(0.10, 0.46, 0.10), FOLI if j % 2 else FOLI2,
                  at=(px + 0.13 * math.cos(a), sy + 0.05 + r * 1.5,
                      0.13 * math.sin(a)), rot_z=0.45 * math.cos(a),
                  rot_x=0.45 * math.sin(a))
m.add(torus(0.42, 0.03, seg=24, ring=6), WIRE, at=(0, H - 0.10, 0), rot_x=math.pi / 2)
p = save(m, "etagere")
put("Living Etagere", p, (29.3, 0.0, 2.0), rot=270)

# ---------------------------------------------------------- corner plant
m = Model()
m.add(cylinder(0.62, 0.95, seg=18, r_top=0.72), POT, at=(0, 0, 0))
m.add(cylinder(0.66, 0.10, seg=18), POT2, at=(0, 0.95, 0))
m.add(cylinder(0.09, 2.10, seg=8), Material("stem", "#6b6055", roughness=0.9),
      at=(0, 0.95, 0))
for j in range(14):
    a = 2 * math.pi * j / 14 * 1.6
    h = 1.30 + 1.55 * (j / 14)
    r = 0.95 - 0.35 * (j / 14)
    m.add(box(0.62, 0.06, 0.46), FOLI if j % 2 else FOLI2,
          at=(r * math.cos(a) * 0.6, h, r * math.sin(a) * 0.6),
          rot_y=a, rot_z=0.35)
p = save(m, "plant")
put("Living Corner Plant", p, (29.4, 0.0, 15.3), rot=0)
