"""Focal group: the fieldstone fireplace on the CHAMFER, the wall TV, the media
console, and the trim around the real patio-slider opening."""
import math
import random

from kit2 import *

rnd = random.Random(20260816)

# ============================================================== fireplace
# Photo f: white PAINTED FIELDSTONE -- a jigsaw of irregular polygonal slabs
# 1.0-1.8 ft across with thin recessed joints and a faceted (domed) face.  Round
# 1 built horizontal courses of rectangles, which is why it read as painted
# brick.  This is a jittered Voronoi tessellation instead: no course lines at
# all, every stone a different convex polygon, every face domed so the light
# breaks across it.
STONE = [Material("lrstoneA", "#f7f6f2", roughness=0.88),
         Material("lrstoneB", "#eeece6", roughness=0.90),
         Material("lrstoneC", "#fcfbf8", roughness=0.84),
         Material("lrstoneD", "#e6e3dc", roughness=0.92)]
JOINT = Material("lrjoint", "#bcb8b0", roughness=0.99)
WHITE = Material("lrfwhite", "#efeee9", roughness=0.55)
SHADE = Material("lrfshade", "#8b8880", roughness=0.95)
BLACK = Material("lrfblack", "#191a1c", roughness=0.40)
VOID = Material("lrfvoid", "#08080a", roughness=0.95)
GLASSF = Material("lrfglass", "#23252a", roughness=0.16, metallic=0.45)
WREATH = Material("lrwreath", "#5a5364", roughness=0.92)
WREATH2 = Material("lrwreath2", "#6e6779", roughness=0.92)
VASE = Material("lrvase", "#d4d2cc", roughness=0.45)
LEAF = Material("lrleaf", "#57634f", roughness=0.85)

FW, FH, FD = 6.86, 9.00, 0.85
MANTEL_Y = 4.45


def voronoi(seeds, rect):
    """Clip `rect` by the perpendicular bisector against every other seed."""
    x0, y0, x1, y1 = rect
    cells = []
    for i, a in enumerate(seeds):
        poly = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        for j, b in enumerate(seeds):
            if i == j or not poly:
                continue
            nx, ny = b[0] - a[0], b[1] - a[1]
            c = nx * (a[0] + b[0]) / 2 + ny * (a[1] + b[1]) / 2
            out, n = [], len(poly)
            for k in range(n):
                p, q = poly[k], poly[(k + 1) % n]
                dp = nx * p[0] + ny * p[1] - c
                dq = nx * q[0] + ny * q[1] - c
                if dp <= 0:
                    out.append(p)
                if (dp < 0) != (dq < 0) and abs(dq - dp) > 1e-12:
                    t = dp / (dp - dq)
                    out.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
            poly = out
        if len(poly) >= 3:
            cells.append(poly)
    return cells


def shrink(poly, d):
    n = len(poly)
    cx = sum(p[0] for p in poly) / n
    cy = sum(p[1] for p in poly) / n
    out = []
    for (x, y) in poly:
        dx, dy = x - cx, y - cy
        L = math.hypot(dx, dy) or 1.0
        f = max(0.15, 1.0 - d / L)
        out.append((cx + dx * f, cy + dy * f))
    return out


def stone_face(m, x0, x1, y0, y1, pitch=1.34, z_back=0.0, lo=0.04, hi=0.16):
    seeds = []
    nx = max(1, int(round((x1 - x0) / pitch)))
    ny = max(1, int(round((y1 - y0) / pitch)))
    for iy in range(ny):
        for ix in range(nx):
            seeds.append((x0 + (x1 - x0) * (ix + 0.5 + rnd.uniform(-.46, .46)) / nx,
                          y0 + (y1 - y0) * (iy + 0.5 + rnd.uniform(-.46, .46)) / ny))
    for cell in voronoi(seeds, (x0, y0, x1, y1)):
        p = shrink(cell, 0.020)
        if len(p) < 3:
            continue
        m.add(face_slab(p, z_back, z_back + rnd.uniform(lo, hi),
                        dome=rnd.uniform(0.008, 0.034)),
              STONE[rnd.randrange(len(STONE))])


m = Model()
m.add(box(FW, FH, FD - 0.16), JOINT, at=(0, 0, -0.08))        # dark backing
stone_face(m, -FW / 2, FW / 2, 0.0, FH, z_back=FD / 2 - 0.09)
for sx in (-1, 1):                                            # stone returns
    y = 0.0
    while y < FH - 0.01:
        h = min(rnd.uniform(0.5, 1.15), FH - y)
        pro = rnd.uniform(0.03, 0.09)
        m.add(box(pro, h - 0.055, FD - 0.13), STONE[rnd.randrange(4)],
              at=(sx * (FW / 2 + pro / 2 - 0.01), y + 0.028, -0.02))
        y += h

# firebox: flat black surround, recessed dark box, glass
FBW, FBH, FBY = 3.20, 2.30, 0.72
fz = FD / 2 + 0.03
m.add(box(FBW + 0.46, FBH + 0.42, 0.07), BLACK, at=(0, FBY - 0.21, fz + 0.035))
m.add(box(FBW, FBH, 0.36), VOID, at=(0, FBY, fz - 0.20))
m.add(box(FBW - 0.05, FBH - 0.05, 0.03), GLASSF, at=(0, FBY + 0.025, fz + 0.075))
m.add(box(FW + 0.06, 0.30, FD + 0.14), STONE[1], at=(0, 0.0, 0.04))   # hearth

# mantel shelf: slim white slab with a grey reveal under it (no shadows here)
m.add(box(FW * 0.86, 0.08, FD * 0.55 + 0.26), SHADE,
      at=(0, MANTEL_Y - 0.12, fz * 0.55 + 0.10))
m.add(box(FW * 0.87, 0.10, FD * 0.55 + 0.30), WHITE,
      at=(0, MANTEL_Y - 0.04, fz * 0.55 + 0.11))
m.add(box(FW * 0.83, 0.16, FD * 0.55 + 0.22), WHITE,
      at=(0, MANTEL_Y + 0.06, fz * 0.55 + 0.09))

# wreath (dark eucalyptus, ~1.4 ft) above the mantel
WY, WR = 6.25, 0.60
m.add(torus(WR, 0.17, seg=24, ring=8), WREATH, at=(0, WY, fz + 0.24),
      rot_x=math.pi / 2)
for i in range(28):
    a = 2 * math.pi * i / 28
    rr = WR + rnd.uniform(-0.07, 0.15)
    m.add(box(0.16, 0.34, 0.12), WREATH2 if i % 3 == 0 else WREATH,
          at=(rr * math.cos(a), WY + rr * math.sin(a), fz + 0.26),
          rot_z=a + math.pi / 2 + rnd.uniform(-0.3, 0.3))

# two small white pots of greenery on the mantel (photo f)
for sx in (-1.75, 1.75):
    m.add(cylinder(0.24, 0.30, seg=14, r_top=0.20), VASE,
          at=(sx, MANTEL_Y + 0.14, fz * 0.55 + 0.10))
    for k in range(6):
        a = 2 * math.pi * k / 6 + 0.4
        m.add(box(0.34, 0.05, 0.22), LEAF,
              at=(sx + 0.16 * math.cos(a), MANTEL_Y + 0.48 + 0.05 * k,
                  fz * 0.55 + 0.10 + 0.14 * math.sin(a)),
              rot_y=a, rot_z=0.45 * math.cos(a), rot_x=0.35 * math.sin(a))

n, _ = edge_normal(*EDGES[CH])
mid = ((EDGES[CH][0][0] + EDGES[CH][1][0]) / 2, (EDGES[CH][0][1] + EDGES[CH][1][1]) / 2)
# objects.js seats a model on its BBOX centre, and the breast's mantel/wreath
# reach much further into the room than FD -- so push out by half the real
# bbox depth or the back of the chase ends up outside the house.
_lo, _hi = m.bounds()
_off = (_hi[2] - _lo[2]) / 2
FPOS = (mid[0] + n[0] * _off, 0.0, mid[1] + n[1] * _off)
FROT = math.degrees(math.atan2(n[0], n[1]))
FFOOT = [(mid[0] + n[0] * 0.02, mid[1] + n[1] * 0.02)]
put("Living Fireplace", save(m, "fireplace2"), FPOS, FROT)
print("  fireplace bbox depth %.2f, rot %.2f deg, pos (%.2f,%.2f)"
      % (_hi[2] - _lo[2], FROT, FPOS[0], FPOS[2]))

# ============================================================== TV
SKY = Material("lrtvsky", "#7c848e", roughness=0.35, emissive="#1e2126")
MTN = Material("lrtvmtn", "#494039", roughness=0.35, emissive="#100d0b")
MTN2 = Material("lrtvmtn2", "#372f2b", roughness=0.35, emissive="#090707")
WATER = Material("lrtvwat", "#33455a", roughness=0.30, emissive="#0a0e14")
FOAM = Material("lrtvfoam", "#68727e", roughness=0.30, emissive="#171b20")
BEZEL = Material("lrbezel", "#0d0e10", roughness=0.40)

TVW, TVH = 6.62, 3.72
TVX, TVY0, TVZ = 8.435, 2.55, 0.05
m = Model()
m.add(box(TVW, TVH, 0.10), BEZEL, at=(TVX, TVY0, TVZ + 0.05))
IW, IH = TVW - 0.10, TVH - 0.10
SB = TVY0 + 0.05                       # screen bottom
# Photo A's screen is a mountain lake.  Round 1 (and this build's first pass)
# drew it as full-width horizontal BANDS, which reads as a test card at any
# distance.  Now: one sky field, one water field, and the land only ever as
# tilted slivers along the horizon, so the silhouette carries the image.
m.add(box(IW, IH, 0.02), SKY, at=(TVX, SB, TVZ + 0.108))
HOR = SB + IH * 0.46
m.add(box(IW, IH * 0.46, 0.015), WATER, at=(TVX, SB, TVZ + 0.114))
# keep every sliver inside the screen: they widen the model bbox otherwise and
# put_in_place would then centre the TV on the painting, not on the panel
for (px, pw, ph, tilt, mat) in ((-2.00, 2.20, 0.78, 0.07, MTN2),
                                (-0.90, 2.55, 0.52, -0.05, MTN),
                                (0.75, 1.95, 0.86, 0.06, MTN2),
                                (2.05, 2.00, 0.44, -0.07, MTN),
                                (-1.90, 1.30, 0.34, 0.10, MTN)):
    m.add(box(pw, ph, 0.012), mat, at=(TVX + px, HOR - ph * 0.42, TVZ + 0.120),
          rot_z=tilt)
m.add(box(IW, 0.10, 0.012), MTN2, at=(TVX, HOR - 0.05, TVZ + 0.124))
# the pale wave shapes across the lower third
for (px, pw, ph, tilt) in ((-1.45, 3.10, 0.24, 0.04), (0.90, 2.80, 0.18, -0.03),
                           (-0.30, 4.30, 0.15, 0.02), (1.55, 2.10, 0.13, 0.05)):
    m.add(box(pw, ph, 0.012), FOAM,
          at=(TVX + px, SB + IH * 0.30 - ph / 2, TVZ + 0.126), rot_z=tilt)
m.add(box(IW * 0.72, 0.20, 0.012), SKY,
      at=(TVX - 0.6, SB + IH * 0.74, TVZ + 0.126), rot_z=0.02)
# soundbar under the screen, on the wall (photo f)
m.add(box(4.10, 0.24, 0.20), Material("lrbar", "#2a2b2e", roughness=0.7),
      at=(TVX, TVY0 - 0.42, TVZ + 0.10))
put_in_place("Living TV", m, save(m, "tv2"))

# ============================================================== media console
CASE = Material("lrccase", "#43464a", roughness=0.70)
CTOP = Material("lrctop", "#616467", roughness=0.60)
CDARK = Material("lrcdark", "#17191c", roughness=0.95)
CLEG = Material("lrcleg", "#1a1b1e", roughness=0.50)
CITEM = Material("lrcitem", "#97958e", roughness=0.80)
CITEM2 = Material("lrcitem2", "#676d71", roughness=0.70)
CITEM3 = Material("lrcitem3", "#7d7a72", roughness=0.85)

CW, CH_, CD = 5.90, 1.44, 1.46
CX, CZ, LEG = 8.435, 0.88, 0.34
m = Model()
m.add(box(CW, CH_, CD), CASE, at=(CX, LEG, CZ))
m.add(box(CW + 0.12, 0.09, CD + 0.10), CTOP, at=(CX, LEG + CH_, CZ))
for i in range(4):
    cx = CX - CW / 2 + CW * (i + 0.5) / 4
    if i in (1, 2):
        m.add(box(CW / 4 - 0.14, CH_ - 0.28, 0.10), CDARK,
              at=(cx, LEG + 0.15, CZ + CD / 2 - 0.11))
        m.add(box(CW / 4 - 0.34, 0.06, CD - 0.34), CTOP,
              at=(cx, LEG + CH_ / 2 - 0.03, CZ + 0.02))
        m.add(box(0.42, 0.20, 0.30), CITEM, at=(cx - 0.26, LEG + CH_ / 2 + 0.03, CZ))
        m.add(box(0.30, 0.28, 0.26), CITEM2, at=(cx + 0.28, LEG + 0.20, CZ))
        m.add(box(0.34, 0.10, 0.24), CITEM3, at=(cx - 0.24, LEG + 0.20, CZ))
    else:
        m.add(box(CW / 4 - 0.16, CH_ - 0.24, 0.04), CASE,
              at=(cx, LEG + 0.13, CZ + CD / 2 + 0.015))
        m.add(box(CW / 4 - 0.16, 0.02, 0.03), CDARK,
              at=(cx, LEG + CH_ - 0.16, CZ + CD / 2 + 0.03))
for sx in (-1, 1):
    for sz in (-1, 1):
        m.add(cylinder(0.055, LEG + 0.05, seg=8), CLEG,
              at=(CX + sx * (CW / 2 - 0.34), 0, CZ + sz * (CD / 2 - 0.24)),
              rot_x=sz * 0.16, rot_z=-sx * 0.16)
# clutter on top: a speaker, a stack of remotes, a small trailing plant
m.add(box(0.52, 0.10, 0.40), CITEM, at=(CX - 1.9, LEG + CH_ + 0.09, CZ - 0.05))
m.add(box(0.34, 0.06, 0.16), CDARK, at=(CX - 1.55, LEG + CH_ + 0.14, CZ + 0.22),
      rot_y=0.25)
m.add(box(0.30, 0.05, 0.14), CITEM3, at=(CX - 1.25, LEG + CH_ + 0.14, CZ + 0.10),
      rot_y=-0.4)
m.add(box(0.30, 0.62, 0.26), CITEM2, at=(CX + 2.1, LEG + CH_ + 0.09, CZ))
m.add(cylinder(0.20, 0.24, seg=12), CITEM, at=(CX + 1.3, LEG + CH_ + 0.09, CZ))
for k in range(5):
    a = 2 * math.pi * k / 5
    m.add(box(0.26, 0.05, 0.16), Material("lrcleaf", "#556249", roughness=0.9),
          at=(CX + 1.3 + 0.12 * math.cos(a), LEG + CH_ + 0.34, CZ + 0.12 * math.sin(a)),
          rot_y=a, rot_z=0.5)
put_in_place("Living Media Console", m, save(m, "console2"))

# ============================================================== slider trim
# The opening itself is cut in the wall; this is the frame, the stile and the
# vertical-blind stack parked at the west jamb (photo A).
TRIMW = Material("lrtrimw", "#dedcd6", roughness=0.55)
BLIND = Material("lrblind", "#c9c6be", roughness=0.95)
SX0, SX1, SHH = 12.00, 18.85, 6.90
m = Model()
for x in (SX0 + 0.10, SX1 - 0.10):
    m.add(box(0.20, SHH, 0.30), TRIMW, at=(x, 0.0, 0.15))
m.add(box(SX1 - SX0, 0.20, 0.30), TRIMW, at=((SX0 + SX1) / 2, SHH - 0.20, 0.15))
m.add(box(SX1 - SX0, 0.14, 0.34), TRIMW, at=((SX0 + SX1) / 2, 0.0, 0.17))
m.add(box(0.22, SHH - 0.20, 0.26), TRIMW, at=((SX0 + SX1) / 2, 0.0, 0.13))
# casing proud of the wall
m.add(box(SX1 - SX0 + 0.62, 0.26, 0.16), TRIMW, at=((SX0 + SX1) / 2, SHH, 0.08))
m.add(box(SX1 - SX0 + 0.80, 0.10, 0.24), TRIMW, at=((SX0 + SX1) / 2, SHH + 0.26, 0.08))
for x in (SX0 - 0.15, SX1 + 0.15):
    m.add(box(0.30, SHH + 0.26, 0.16), TRIMW, at=(x, 0.0, 0.08))
for i in range(5):
    m.add(box(0.10, SHH - 0.50, 0.06), BLIND,
          at=(SX0 + 0.38 + i * 0.11, 0.26, 0.26), rot_y=0.6)
put_in_place("Living Slider Trim", m, save(m, "slidertrim"))
