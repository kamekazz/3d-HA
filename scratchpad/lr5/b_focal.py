"""North wall focal group: stone fireplace, wall TV, media console."""
import math, random
from kit import *

rnd = random.Random(20260815)

# ---------------------------------------------------------------- fireplace
STONE_A = Material("stoneA", "#ffffff", roughness=0.84, emissive="#3c3a36")
STONE_B = Material("stoneB", "#f3f1ea", roughness=0.86, emissive="#332f2b")
STONE_C = Material("stoneC", "#ffffff", roughness=0.80, emissive="#464440")
MORTAR = Material("mortar", "#c8c3b9", roughness=0.98)
WHITE = Material("mwhite", "#ffffff", roughness=0.6, emissive="#3e3e3c")
BLACK = Material("fblack", "#17181a", roughness=0.45)
VOID = Material("fvoid", "#08080a", roughness=0.9)
GLASSF = Material("fglass", "#26282d", roughness=0.18, metallic=0.4)
WREATH = Material("wreath", "#575062", roughness=0.92)
WREATH2 = Material("wreath2", "#6a6376", roughness=0.92)
VASE = Material("vase", "#25262a", roughness=0.5)
LEAF = Material("leaf", "#9fae92", roughness=0.85)

FW, FH, FD = 6.20, 9.00, 0.88          # breast width / height / depth
MANTEL_Y = 4.42
m = Model()
m.add(box(FW, FH, FD), MORTAR, at=(0, 0, 0))

# stacked-stone veneer: irregular flat stones, not a running bond.  Each course
# is split into stones whose own height wobbles inside the course, which is what
# stops it reading as brick.
front_z = FD / 2
y = 0.0
while y < FH - 0.01:
    ch = min(rnd.uniform(0.17, 0.50), FH - y)
    x = -FW / 2
    while x < FW / 2 - 0.01:
        w = min(rnd.uniform(0.55, 2.60), FW / 2 - x)
        mat = (STONE_A, STONE_B, STONE_C, STONE_A, STONE_C)[rnd.randrange(5)]
        pro = rnd.uniform(0.025, 0.06)
        sh = ch * rnd.uniform(0.86, 0.995)           # stone shorter than its course
        dy = rnd.uniform(0.0, ch - sh)
        m.add(box(w - 0.014, sh, pro), mat,
              at=(x + w / 2, y + dy, front_z + pro / 2 - 0.002))
        x += w
    for sx in (-1, 1):                              # returns
        pro = rnd.uniform(0.02, 0.06)
        mat = (STONE_A, STONE_B, STONE_C)[rnd.randrange(3)]
        m.add(box(pro, ch * 0.88, FD - 0.06), mat,
              at=(sx * (FW / 2 + pro / 2 - 0.002), y + 0.03, 0))
    y += ch

# firebox: slim black surround with a recessed dark opening behind glass
FBW, FBH, FBY = 3.30, 2.62, 0.78
m.add(box(FBW + 0.30, FBH + 0.28, 0.09), BLACK, at=(0, FBY - 0.14, front_z + 0.085))
m.add(box(FBW, FBH, 0.34), VOID, at=(0, FBY, front_z - 0.16))
m.add(box(FBW - 0.06, FBH - 0.06, 0.03), GLASSF, at=(0, FBY + 0.03, front_z + 0.105))
# stone hearth base flush with the breast
m.add(box(FW + 0.10, 0.34, FD + 0.10), STONE_C, at=(0, 0.0, 0.05))

SHADOW = Material("mshadow", "#8f8b84", roughness=0.98)
m.add(box(FW + 0.60, 0.07, FD + 0.24), SHADOW, at=(0, MANTEL_Y - 0.13, 0.10))
# mantel shelf
m.add(box(FW + 0.62, 0.07, FD + 0.26), WHITE, at=(0, MANTEL_Y - 0.03, 0.11))
m.add(box(FW + 0.54, 0.15, FD + 0.20), WHITE, at=(0, MANTEL_Y + 0.04, 0.09))
m.add(box(FW + 0.62, 0.06, FD + 0.28), WHITE, at=(0, MANTEL_Y + 0.19, 0.11))

# wreath above the mantel -- dark eucalyptus, ~1.9 ft across
WY, WR = 6.20, 0.72
m.add(torus(WR, 0.19, seg=26, ring=8), WREATH, at=(0, WY, front_z + 0.18), rot_x=math.pi / 2)
for i in range(30):                      # sprigs, so it is not a smooth donut
    a = 2 * math.pi * i / 30
    rr = WR + rnd.uniform(-0.07, 0.16)
    m.add(box(0.17, 0.36, 0.13), WREATH2 if i % 3 == 0 else WREATH,
          at=(rr * math.cos(a), WY + rr * math.sin(a), front_z + 0.20),
          rot_z=a + math.pi / 2 + rnd.uniform(-0.3, 0.3))

# two small vases with greenery on the mantel
for sx in (-1.95, 1.95):
    m.add(cylinder(0.15, 0.38, seg=12), VASE, at=(sx, MANTEL_Y + 0.35, front_z + 0.02))
    for k in range(4):
        a = 2 * math.pi * k / 4 + 0.4
        m.add(box(0.28, 0.05, 0.15), LEAF,
              at=(sx + 0.14 * math.cos(a), MANTEL_Y + 0.72 + 0.06 * k,
                  front_z + 0.02 + 0.14 * math.sin(a)),
              rot_y=a, rot_z=0.5)

p = save(m, "fireplace")
put("Living Fireplace", p, (11.6, 0.0, 0.69))

# ---------------------------------------------------------------- TV
SKY = Material("tvsky", "#dfe6ee", roughness=0.35, emissive="#666e79")
MTN = Material("tvmtn", "#7d6259", roughness=0.35, emissive="#2c1f1b")
MTN2 = Material("tvmtn2", "#5d443d", roughness=0.35, emissive="#1e1512")
BEZEL = Material("bezel", "#0e0f11", roughness=0.4)

TVW, TVH = 6.85, 3.92
m = Model()
m.add(box(TVW, TVH, 0.11), BEZEL, at=(0, 0, 0))
IW, IH = TVW - 0.09, TVH - 0.09
WATER = Material("tvwat", "#4f76a4", roughness=0.3, emissive="#1b2839")
FOAM = Material("tvfoam", "#aec2da", roughness=0.3, emissive="#454f5c")
# The photo's screen shows a mountain lake: pale sky, a brown ridge line, a
# dark shore and a big pale wave shape.  Built as bands plus tilted slivers so
# it reads as a photograph rather than a colour chart.
bands = [(0.00, 0.34, SKY), (0.34, 0.52, MTN), (0.52, 0.63, WATER), (0.63, 1.00, FOAM)]
for (a, b, mat) in bands:
    m.add(box(IW, (b - a) * IH, 0.02), mat, at=(0, 0.045 + (1 - b) * IH, 0.062))
ridge_y = 0.045 + (1 - 0.52) * IH
for (px, pw, ph, tilt, mat) in ((-2.55, 2.10, 0.62, 0.06, MTN2),
                                (-0.70, 2.60, 0.44, -0.04, MTN),
                                (1.35, 2.30, 0.56, 0.05, MTN2),
                                (2.95, 1.50, 0.34, -0.06, MTN)):
    m.add(box(pw, ph, 0.015), mat, at=(px, ridge_y, 0.068), rot_z=tilt)
# far shore + the lake's pale curved wave
m.add(box(IW, 0.16, 0.015), MTN2, at=(0, 0.045 + (1 - 0.63) * IH, 0.068))
for (px, pw, ph, tilt) in ((-1.90, 3.60, 0.30, 0.045), (0.90, 3.20, 0.22, -0.035),
                           (-0.40, 4.60, 0.18, 0.02)):
    m.add(box(pw, ph, 0.015), WATER,
          at=(px, 0.045 + (1 - 0.63) * IH - 0.30, 0.070), rot_z=tilt)
m.add(box(IW * 0.80, 0.26, 0.015), SKY,
      at=(-0.5, 0.045 + 0.16 * IH, 0.070), rot_z=0.02)
p = save(m, "tv")
put("Living TV", p, (18.7, 2.72, 0.062))

# ---------------------------------------------------------------- console
CASE = Material("ccase", "#5b5e63", roughness=0.7)
CTOP = Material("ctop", "#9b9ea2", roughness=0.6)
CDARK = Material("cdark", "#191b1e", roughness=0.95)
CLEG = Material("cleg", "#1b1c1f", roughness=0.5)
CITEM = Material("citem", "#dedbd2", roughness=0.8)
CITEM2 = Material("citem2", "#9aa2a8", roughness=0.7)

CW, CH, CD = 6.80, 1.52, 1.36
m = Model()
LEG = 0.36
m.add(box(CW, CH, CD), CASE, at=(0, LEG, 0))
m.add(box(CW + 0.12, 0.09, CD + 0.10), CTOP, at=(0, LEG + CH, 0))
# four bays: two closed doors (left/right), two open shelves in the middle
for i in range(4):
    cx = -CW / 2 + CW * (i + 0.5) / 4
    if i in (1, 2):
        m.add(box(CW / 4 - 0.14, CH - 0.30, 0.10), CDARK, at=(cx, LEG + 0.16, CD / 2 - 0.11))
        m.add(box(CW / 4 - 0.36, 0.06, CD - 0.34), CTOP, at=(cx, LEG + CH / 2 - 0.03, 0.02))
        m.add(box(0.42, 0.22, 0.30), CITEM, at=(cx - 0.28, LEG + CH / 2 + 0.03, 0.02))
        m.add(box(0.30, 0.30, 0.26), CITEM2, at=(cx + 0.30, LEG + 0.22, 0.02))
    else:
        m.add(box(CW / 4 - 0.16, CH - 0.26, 0.04), CASE, at=(cx, LEG + 0.14, CD / 2 + 0.015))
        m.add(box(CW / 4 - 0.16, 0.02, 0.03), CDARK, at=(cx, LEG + CH - 0.16, CD / 2 + 0.03))
for sx in (-1, 1):
    for sz in (-1, 1):
        m.add(cylinder(0.055, LEG + 0.04, seg=8), CLEG,
              at=(sx * (CW / 2 - 0.34), 0, sz * (CD / 2 - 0.24)),
              rot_x=sz * 0.16, rot_z=-sx * 0.16)
# a few objects on top
m.add(box(0.55, 0.10, 0.42), CITEM, at=(-2.0, LEG + CH + 0.09, 0.0))
m.add(box(0.34, 0.30, 0.30), CITEM2, at=(2.3, LEG + CH + 0.09, 0.0))
p = save(m, "console")
put("Living Media Console", p, (18.6, 0.0, 0.80))
