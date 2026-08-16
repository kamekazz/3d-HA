"""Round 3 focal wall: real fieldstone on the chamfer, a firebox that reads as
a fireplace instead of a second television, a dense wreath, and a TV picture
built from silhouettes instead of floating slabs.

Critic items 1, 5, 10, 11 (wreath) and 12 (blind stack).
"""
import math
import random

from kit3 import *
from kit3 import Part, Material, Model, _shrink

rnd = random.Random(30310)

# ============================================================== fieldstone
# ITEM 1.  Round 2 cut 1.34 ft Voronoi cells, shrank them 0.020 ft and extruded
# flat faces of four near-white materials -- hairline seams between white
# plates, i.e. cracked plaster.  Three things change here, and only one of them
# is density:
#   * the joint is a genuinely darker RECESSED plane (#8e8c88) behind the
#     stones, and the gap is 0.10 ft (~1.2 in) instead of 0.04 ft;
#   * every cell outline is broken into three jittered segments per edge, so no
#     stone has a straight edge (straight edges are what read as crazy paving);
#   * every stone is a bevelled pillow -- rim, bevel, cap, apex -- so light
#     breaks across it in four values instead of one.
# Density is raised only from 1.34 ft to 1.05 ft seeds (35 -> ~60 stones).  See
# the report: the photo's stones measure 1.0-1.8 ft across, so the requested
# 0.25-0.35 ft / 400-600 stones would be gravel, not fieldstone.
STONE = [Material("lrstoneA", "#e5e3dd", roughness=0.88),
         Material("lrstoneB", "#dbd8d2", roughness=0.90),
         Material("lrstoneC", "#eeece8", roughness=0.84),
         Material("lrstoneD", "#cdc9c2", roughness=0.93),
         Material("lrstoneE", "#e0ddd6", roughness=0.89)]
JOINT = Material("lrjoint", "#a6a39e", roughness=0.99)
WHITE = Material("lrfwhite", "#f2f1ec", roughness=0.55)
SHADE = Material("lrfshade", "#8b8880", roughness=0.95)
IRON = Material("lrfiron", "#2b2d30", roughness=0.55, metallic=0.25)
IRON2 = Material("lrfiron2", "#3a3d41", roughness=0.45, metallic=0.30)
VOID = Material("lrfvoid", "#131316", roughness=0.98)
EMBER = Material("lrfember", "#2a2320", roughness=0.95)
LOG = Material("lrflog", "#3a332c", roughness=0.95)
GLASSF = Material("lrfglass", "#1d2025", roughness=0.14, metallic=0.55)
WREATH = Material("lrwreath", "#867f92", roughness=0.94)
WREATH2 = Material("lrwreath2", "#968fa3", roughness=0.94)
WREATH3 = Material("lrwreath3", "#746d82", roughness=0.94)
VASE = Material("lrvase", "#d8d6d0", roughness=0.45)
LEAF = Material("lrleaf", "#57634f", roughness=0.85)

FW, FH, FD = 6.86, 9.00, 0.85
MANTEL_Y = 4.45
ZJ = FD / 2 - 0.10                 # joint plane
# firebox opening in face coordinates
FBX, FBY0, FBY1 = 1.72, 0.62, 3.22


def clip_out(poly, box):
    """Trim a stone cell back to the outside of the firebox rectangle."""
    x0, y0, x1, y1 = box
    n = len(poly)
    cx = sum(p[0] for p in poly) / n
    cy = sum(p[1] for p in poly) / n
    cands = []
    if cx <= x0:
        cands.append((x0 - cx, (-1.0, 0.0, -x0)))
    if cx >= x1:
        cands.append((cx - x1, (1.0, 0.0, x1)))
    if cy <= y0:
        cands.append((y0 - cy, (0.0, -1.0, -y0)))
    if cy >= y1:
        cands.append((cy - y1, (0.0, 1.0, y1)))
    if not cands:
        return []
    _, (nx, ny, c) = max(cands)
    out = []
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        dp = nx * p[0] + ny * p[1] - c
        dq = nx * q[0] + ny * q[1] - c
        if dp >= 0:
            out.append(p)
        if (dp < 0) != (dq < 0) and abs(dq - dp) > 1e-12:
            t = dp / (dp - dq)
            out.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
    return out


def stone_face(m, x0, x1, y0, y1, pitch=1.05, cut=None):
    nx = max(1, int(round((x1 - x0) / pitch)))
    ny = max(1, int(round((y1 - y0) / pitch)))
    seeds = []
    for iy in range(ny):
        for ix in range(nx):
            sx = x0 + (x1 - x0) * (ix + 0.5 + rnd.uniform(-.44, .44)) / nx
            sy = y0 + (y1 - y0) * (iy + 0.5 + rnd.uniform(-.44, .44)) / ny
            if cut and cut[0] < sx < cut[2] and cut[1] < sy < cut[3]:
                continue
            seeds.append((sx, sy))
    n = 0
    for _seed, cell in voronoi_cells(seeds, (x0, y0, x1, y1)):
        if cut:
            cell = clip_out(cell, cut)
        if len(cell) < 3 or poly_area(cell) < 0.05:
            continue
        p = wobble(_shrink(cell, 0.030), rnd, amp=0.10, sub=3)
        h = rnd.uniform(0.07, 0.15)
        m.add(pillow(p, ZJ, h, rim=0.036, dome=rnd.uniform(0.004, 0.013)),
              STONE[rnd.randrange(len(STONE))])
        n += 1
    return n


m = Model()
m.add(box(FW, FH, ZJ + FD / 2), JOINT, at=(0, 0, -(FD / 2 - ZJ) / 2))  # joint plane
n_stone = stone_face(m, -FW / 2, FW / 2, 0.0, FH,
                     cut=(-FBX, FBY0, FBX, FBY1))
print("  stones on face: %d" % n_stone)

# stone returns down both ends of the chase
for sx in (-1, 1):
    y = 0.0
    while y < FH - 0.01:
        h = min(rnd.uniform(0.55, 1.20), FH - y)
        pro = rnd.uniform(0.04, 0.10)
        m.add(box(pro, h - 0.075, FD - 0.13), STONE[rnd.randrange(5)],
              at=(sx * (FW / 2 + pro / 2 - 0.01), y + 0.038, -0.02))
        y += h

# ============================================================== firebox
# ITEM 5.  Round 2 put a flat black rectangle in a flat black bezel flush with
# the stone, which from the reference pose is the same silhouette as the wall
# TV.  A real insert reads as: a stepped cast-iron surround standing proud of
# the stone, a projecting top hood, a recessed throat with a log bed behind
# glass, and a hearth ledge on the floor.
FZ = FD / 2
OW, OH = 3.44, 2.60            # surround outer
OY = 0.62
IWD, IHT = 2.62, 1.86          # glass
IY = 1.06
# throat
m.add(box(IWD + 0.30, IHT + 0.42, 0.60), VOID, at=(0, IY - 0.20, FZ - 0.66))
m.add(box(IWD + 0.10, 0.10, 0.52), EMBER, at=(0, IY - 0.16, FZ - 0.62))
for i, (lx, ly, lr) in enumerate(((-0.55, 0.04, 0.34), (0.30, 0.02, -0.26),
                                  (-0.10, 0.22, 0.12))):
    m.add(cylinder(0.115, 1.30, seg=8), LOG,
          at=(lx, IY - 0.06 + ly, FZ - 0.46), rot_z=math.pi / 2 + lr * 0.16,
          rot_y=lr)
# cast-iron surround: four flanges, stepped forward
for (bw, bh, bx, by, bz, bd) in (
        (OW, 0.22, 0.0, OY, 0.02, 0.13),                       # bottom rail
        (0.30, OH, -(OW - 0.30) / 2, OY, 0.02, 0.13),          # left stile
        (0.30, OH, (OW - 0.30) / 2, OY, 0.02, 0.13),           # right stile
        (OW, 0.40, 0.0, OY + OH - 0.40, 0.02, 0.13)):          # head
    m.add(box(bw, bh, bd), IRON, at=(bx, by, FZ + bz + bd / 2))
# projecting hood over the head -- the step that separates a firebox from a TV
m.add(box(OW + 0.34, 0.15, 0.34), IRON2, at=(0, OY + OH - 0.05, FZ + 0.15))
m.add(box(OW + 0.20, 0.10, 0.26), IRON, at=(0, OY + OH - 0.18, FZ + 0.13))
# ash lip under the opening
m.add(box(OW + 0.24, 0.11, 0.30), IRON2, at=(0, OY - 0.09, FZ + 0.13))
# glass with two mullions
m.add(box(IWD, IHT, 0.03), GLASSF, at=(0, IY, FZ + 0.075))
for gx in (-IWD / 6, IWD / 6):
    m.add(box(0.045, IHT, 0.05), IRON2, at=(gx, IY, FZ + 0.085))
m.add(box(IWD, 0.05, 0.05), IRON2, at=(0, IY + IHT - 0.05, FZ + 0.085))

# raised stone hearth on the floor (photo f)
m.add(box(FW + 0.20, 0.34, FD + 0.60), STONE[2], at=(0, 0.0, 0.16))
m.add(box(FW + 0.24, 0.06, FD + 0.66), WHITE, at=(0, 0.34, 0.16))

# mantel shelf with a grey reveal under it (no shadows in this renderer)
m.add(box(FW * 0.86, 0.08, FD * 0.55 + 0.26), SHADE,
      at=(0, MANTEL_Y - 0.12, FZ * 0.55 + 0.10))
m.add(box(FW * 0.87, 0.10, FD * 0.55 + 0.30), WHITE,
      at=(0, MANTEL_Y - 0.04, FZ * 0.55 + 0.11))
m.add(box(FW * 0.83, 0.16, FD * 0.55 + 0.22), WHITE,
      at=(0, MANTEL_Y + 0.06, FZ * 0.55 + 0.09))

# ============================================================== wreath
# ITEM 11.  Round 2's wreath was a torus with 28 radial boxes sticking out of
# it, so you could see the stone through the ring.  This is a solid ring of
# short overlapping leaf plates in three courses -- dense, no holes, and every
# plate stands clear of the stone face.
WY, WR = 6.20, 0.62
WZ = FZ + 0.16
m.add(torus(WR, 0.20, seg=26, ring=8), WREATH3, at=(0, WY, WZ + 0.06),
      rot_x=math.pi / 2)
for course, (rr0, count, tube, mat) in enumerate((
        (WR - 0.14, 34, 0.30, WREATH3), (WR + 0.02, 38, 0.34, WREATH),
        (WR + 0.16, 30, 0.30, WREATH2))):
    for i in range(count):
        a = 2 * math.pi * i / count + course * 0.31
        rr = rr0 + rnd.uniform(-0.045, 0.045)
        m.add(box(0.20, tube, 0.10), mat if i % 4 else WREATH2,
              at=(rr * math.cos(a), WY + rr * math.sin(a),
                  WZ + 0.05 + 0.055 * course),
              rot_z=a + math.pi / 2 + rnd.uniform(-0.45, 0.45),
              rot_y=rnd.uniform(-0.3, 0.3))

# two small white pots of greenery on the mantel (photo f)
for sx in (-1.75, 1.75):
    m.add(cylinder(0.24, 0.30, seg=14, r_top=0.20), VASE,
          at=(sx, MANTEL_Y + 0.14, FZ * 0.55 + 0.10))
    for k in range(6):
        a = 2 * math.pi * k / 6 + 0.4
        m.add(box(0.34, 0.05, 0.22), LEAF,
              at=(sx + 0.16 * math.cos(a), MANTEL_Y + 0.48 + 0.05 * k,
                  FZ * 0.55 + 0.10 + 0.14 * math.sin(a)),
              rot_y=a, rot_z=0.45 * math.cos(a), rot_x=0.35 * math.sin(a))

nrm, _ = edge_normal(*EDGES[CH])
mid = ((EDGES[CH][0][0] + EDGES[CH][1][0]) / 2,
       (EDGES[CH][0][1] + EDGES[CH][1][1]) / 2)
_lo, _hi = m.bounds()
_off = (_hi[2] - _lo[2]) / 2
FPOS = (mid[0] + nrm[0] * _off, 0.0, mid[1] + nrm[1] * _off)
FROT = math.degrees(math.atan2(nrm[0], nrm[1]))
put("Living Fireplace", save(m, "fireplace3"), FPOS, FROT)

# ============================================================== TV
# ITEM 10.  Round 2 drew the picture as tilted BOXES over a blue field: brown
# slabs floating on blue, which reads as a corrupted image.  The land is now
# ONE continuous jagged ridge polygon per range, so the silhouette carries the
# image the way a real photograph on a screen does.
SKY = [Material("lrtvsky%d" % i, c, roughness=0.35, emissive=e)
       for i, (c, e) in enumerate((("#9fb3c6", "#3b4550"), ("#b6c6d3", "#454f58"),
                                   ("#ccd7dc", "#4e565b"), ("#dee5e3", "#565c5b")))]
FAR = Material("lrtvfar", "#9fadb8", roughness=0.35, emissive="#374049")
MID = Material("lrtvmid", "#7c8087", roughness=0.35, emissive="#282b2f")
NEAR = Material("lrtvnear", "#5d5f5c", roughness=0.35, emissive="#1c1d1c")
SUNF = Material("lrtvsun", "#8e8d84", roughness=0.35, emissive="#2f2f2c")
WATER = Material("lrtvwat", "#3f5268", roughness=0.30, emissive="#141b23")
WAT2 = Material("lrtvwat2", "#526a82", roughness=0.30, emissive="#1b232c")
FOAM = Material("lrtvfoam", "#93a3b1", roughness=0.30, emissive="#31373d")
SHORE = Material("lrtvshore", "#3b3730", roughness=0.4, emissive="#121110")
BEZEL = Material("lrbezel", "#0d0e10", roughness=0.40)

TVW, TVH = 6.62, 3.72
TVX, TVY0, TVZ = 8.435, 2.55, 0.05
m = Model()
m.add(box(TVW, TVH, 0.10), BEZEL, at=(TVX, TVY0, TVZ + 0.05))
IW, IH = TVW - 0.10, TVH - 0.10
SB = TVY0 + 0.05
X0, X1 = TVX - IW / 2, TVX + IW / 2
HOR = SB + IH * 0.44
for i, mat in enumerate(SKY):
    y = SB + IH * (0.44 + 0.56 * (3 - i) / 4)
    m.add(box(IW, IH * 0.56 / 4 + 0.01, 0.012), mat, at=(TVX, y, TVZ + 0.108))


def peaks(vals):
    return [(i / (len(vals) - 1.0), v) for i, v in enumerate(vals)]


# 24 samples per ridge, so the skyline is a rolling silhouette rather than a
# row of triangles.
m.add(ridge(X0, X1, HOR, peaks([0.30, 0.44, 0.55, 0.62, 0.58, 0.50, 0.56,
                                0.68, 0.78, 0.84, 0.80, 0.72, 0.66, 0.72,
                                0.82, 0.88, 0.84, 0.74, 0.64, 0.58, 0.62,
                                0.54, 0.44, 0.34]), TVZ + 0.114, rnd), FAR)
m.add(ridge(X0, X1, HOR, peaks([0.14, 0.24, 0.34, 0.44, 0.52, 0.56, 0.52,
                                0.44, 0.38, 0.42, 0.52, 0.62, 0.68, 0.64,
                                0.56, 0.48, 0.44, 0.50, 0.58, 0.54, 0.44,
                                0.34, 0.24, 0.14]), TVZ + 0.118, rnd), MID)
m.add(ridge(X0 + 0.8, X1 - 1.3, HOR, peaks([0.08, 0.16, 0.26, 0.34, 0.38,
                                            0.34, 0.28, 0.22, 0.26, 0.32,
                                            0.28, 0.20, 0.12, 0.06]),
            TVZ + 0.122, rnd), SUNF)
m.add(ridge(X0, X1, HOR, peaks([0.04, 0.10, 0.16, 0.22, 0.26, 0.24, 0.20,
                                0.16, 0.18, 0.24, 0.30, 0.34, 0.30, 0.24,
                                0.20, 0.16, 0.20, 0.26, 0.24, 0.18, 0.14,
                                0.10, 0.06, 0.03]), TVZ + 0.126, rnd), NEAR)
# lake
m.add(box(IW, IH * 0.44, 0.012), WATER, at=(TVX, SB, TVZ + 0.130))
m.add(box(IW, 0.16, 0.012), WAT2, at=(TVX, HOR - 0.16, TVZ + 0.134))
for (px, pw, py, ph) in ((-1.10, 2.60, 0.60, 0.10), (0.90, 2.20, 0.40, 0.08)):
    m.add(box(pw, ph, 0.012), WAT2, at=(TVX + px, SB + py, TVZ + 0.138))
m.add(box(IW * 0.34, 0.06, 0.012), FOAM, at=(TVX - 0.5, SB + 0.74, TVZ + 0.140))
# rocky foreshore across the bottom
m.add(ridge(X0, X1, SB, peaks([0.34, 0.20, 0.30, 0.16, 0.26, 0.12, 0.22,
                               0.30, 0.18, 0.28, 0.14, 0.24]), TVZ + 0.142, rnd),
      SHORE)
# soundbar under the screen, on the wall (photo f)
m.add(box(4.10, 0.24, 0.20), Material("lrbar", "#2a2b2e", roughness=0.7),
      at=(TVX, TVY0 - 0.42, TVZ + 0.10))
put_in_place("Living TV", m, save(m, "tv3"))

# ============================================================== slider trim
# ITEM 12 (part).  The blind stack was five isolated slats -- a comb.  It is
# now a tight overlapping stack drawn to the west jamb, which is what photo A
# shows.
TRIMW = Material("lrtrimw", "#e2e0da", roughness=0.55)
BLIND = Material("lrblind", "#cfccc4", roughness=0.95)
BLIND2 = Material("lrblind2", "#b6b2aa", roughness=0.95)
SX0, SX1, SHH = 12.00, 18.85, 6.90
m = Model()
for x in (SX0 + 0.10, SX1 - 0.10):
    m.add(box(0.20, SHH, 0.30), TRIMW, at=(x, 0.0, 0.15))
m.add(box(SX1 - SX0, 0.20, 0.30), TRIMW, at=((SX0 + SX1) / 2, SHH - 0.20, 0.15))
m.add(box(SX1 - SX0, 0.14, 0.34), TRIMW, at=((SX0 + SX1) / 2, 0.0, 0.17))
m.add(box(0.22, SHH - 0.20, 0.26), TRIMW, at=((SX0 + SX1) / 2, 0.0, 0.13))
m.add(box(SX1 - SX0 + 0.62, 0.26, 0.16), TRIMW, at=((SX0 + SX1) / 2, SHH, 0.08))
m.add(box(SX1 - SX0 + 0.80, 0.10, 0.24), TRIMW, at=((SX0 + SX1) / 2, SHH + 0.26, 0.08))
for x in (SX0 - 0.15, SX1 + 0.15):
    m.add(box(0.30, SHH + 0.26, 0.16), TRIMW, at=(x, 0.0, 0.08))
# headrail plus a dense folded stack, not a comb
m.add(box(SX1 - SX0 - 0.30, 0.16, 0.22), TRIMW,
      at=((SX0 + SX1) / 2, SHH - 0.34, 0.24))
for i in range(14):
    m.add(box(0.075, SHH - 0.66, 0.30), BLIND if i % 2 else BLIND2,
          at=(SX0 + 0.34 + i * 0.055, 0.22, 0.24), rot_y=0.42 + 0.05 * (i % 3))
put_in_place("Living Slider Trim", m, save(m, "slidertrim3"))
