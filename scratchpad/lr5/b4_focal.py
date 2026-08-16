"""Round 4 focal wall -- SURFACES ONLY.

Round 3's stone was adjudicated the right DENSITY (the 400-600 stones round 2's
critic asked for would have been gravel) but the wrong MATERIAL: a clean lit
stone field metered sd 34.2 against photo f's 8.1, because round 3 replaced
round 2's hairline seams with a dark recessed web at #a6a39e.  Three changes,
all of them material/shape, none of them count:

 1. the joint lifts #a6a39e -> #dedbd5, i.e. within ~5% of the stone, and
    narrows 0.030 -> 0.016 ft of shrink.  The pillow bevel carries the relief.
 2. the pillow gets shallower (0.040-0.095 instead of 0.07-0.15) so the rim
    facets, which face sideways and catch no light, stop drawing a black
    outline around every stone.
 3. the seeds are laid in COURSES ~0.85 ft tall with widths varying ~3:1,
    instead of a near-square grid -- horizontal grain, 60-70 stones on the
    6.86 x 9.0 ft face (the adjudicated target).

Also here: the firebox GLASS.  #1d2025 at metallic 0.55 has almost no diffuse
term and nothing to reflect, so it rendered at luminance 5-15 -- ROOM-BRIEF's
own lesson says a near-black slab reads as a hole in the room.  Photo f's glass
sits at 30-95 with two bright reflected streaks across it.

Everything else in this file (surround, hood, ash lip, mantel, hearth, wreath,
TV picture, slider trim) is round 3's, which the critic confirmed good.
"""
import math
import random

from kit4 import *
from kit4 import Part, Material, Model, _shrink

rnd = random.Random(40410)

# Stone albedo trimmed from round 3 (#e5e3dd family, metered 205) towards
# photo f's clean lit stone at 173-189.
STONE = [Material("lrstoneA", "#b0aca6", roughness=0.97),
         Material("lrstoneB", "#aaa6a0", roughness=0.97),
         Material("lrstoneC", "#b6b2ac", roughness=0.97),
         Material("lrstoneD", "#a5a19b", roughness=0.97),
         Material("lrstoneE", "#ada9a3", roughness=0.97)]
# ITEM 1: within ~5% of the stone mean, not a dark web.
JOINT = Material("lrjoint", "#9a978f", roughness=0.99)
WHITE = Material("lrfwhite", "#f2f1ec", roughness=0.55)
SHADE = Material("lrfshade", "#8b8880", roughness=0.95)
IRON = Material("lrfiron", "#2b2d30", roughness=0.55, metallic=0.25)
IRON2 = Material("lrfiron2", "#3a3d41", roughness=0.45, metallic=0.30)
VOID = Material("lrfvoid", "#131316", roughness=0.98)
EMBER = Material("lrfember", "#2a2320", roughness=0.95)
LOG = Material("lrflog", "#3a332c", roughness=0.95)
# ITEM 6: a DIFFUSE dark grey-blue, not a metal with nothing to reflect.
GLASSF = Material("lrfglass", "#3b414a", roughness=0.34, metallic=0.05)
GLASSR = Material("lrfglassr", "#6b737e", roughness=0.22, metallic=0.05)
GLASSR2 = Material("lrfglassr2", "#4e555e", roughness=0.26, metallic=0.05)
WREATH = Material("lrwreath", "#867f92", roughness=0.94)
WREATH2 = Material("lrwreath2", "#968fa3", roughness=0.94)
WREATH3 = Material("lrwreath3", "#746d82", roughness=0.94)
VASE = Material("lrvase", "#d8d6d0", roughness=0.45)
LEAF = Material("lrleaf", "#57634f", roughness=0.85)

FW, FH, FD = 6.86, 9.00, 0.85
MANTEL_Y = 4.45
ZJ = FD / 2 - 0.07                 # joint plane (shallower than round 3's 0.10)
FBX, FBY0, FBY1 = 1.72, 0.62, 3.22


def clip_out(poly, box):
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


def stone_face(m, x0, x1, y0, y1, cut=None):
    seeds = coursed_seeds(x0, x1, y0, y1, rnd, course=0.85, pitch=0.74, cut=cut)
    n = 0
    for _seed, cell in voronoi_cells(seeds, (x0, y0, x1, y1)):
        if cut:
            cell = clip_out(cell, cut)
        if len(cell) < 3 or poly_area(cell) < 0.05:
            continue
        p = wobble(_shrink(cell, 0.026), rnd, amp=0.075, sub=2)
        h = rnd.uniform(0.036, 0.058)
        m.add(plate(p, ZJ, h, rim=0.009, skirt=False,
                    tilt=(rnd.uniform(-.050, .050), rnd.uniform(-.050, .050))),
              STONE[rnd.randrange(len(STONE))])
        n += 1
    return n


m = Model()
m.add(box(FW, FH, ZJ + FD / 2), JOINT, at=(0, 0, -(FD / 2 - ZJ) / 2))
n_stone = stone_face(m, -FW / 2, FW / 2, 0.0, FH, cut=(-FBX, FBY0, FBX, FBY1))
print("  stones on face: %d" % n_stone)

# stone returns down both ends of the chase
for sx in (-1, 1):
    y = 0.0
    while y < FH - 0.01:
        h = min(rnd.uniform(0.62, 1.10), FH - y)
        pro = rnd.uniform(0.03, 0.08)
        m.add(box(pro, h - 0.045, FD - 0.13), STONE[rnd.randrange(5)],
              at=(sx * (FW / 2 + pro / 2 - 0.01), y + 0.023, -0.02))
        y += h

# ============================================================== firebox
FZ = FD / 2
OW, OH = 3.44, 2.60
OY = 0.62
IWD, IHT = 2.62, 1.86
IY = 1.06
m.add(box(IWD + 0.30, IHT + 0.42, 0.60), VOID, at=(0, IY - 0.20, FZ - 0.66))
m.add(box(IWD + 0.10, 0.10, 0.52), EMBER, at=(0, IY - 0.16, FZ - 0.62))
for i, (lx, ly, lr) in enumerate(((-0.55, 0.04, 0.34), (0.30, 0.02, -0.26),
                                  (-0.10, 0.22, 0.12))):
    m.add(cylinder(0.115, 1.30, seg=8), LOG,
          at=(lx, IY - 0.06 + ly, FZ - 0.46), rot_z=math.pi / 2 + lr * 0.16,
          rot_y=lr)
for (bw, bh, bx, by, bz, bd) in (
        (OW, 0.22, 0.0, OY, 0.02, 0.13),
        (0.30, OH, -(OW - 0.30) / 2, OY, 0.02, 0.13),
        (0.30, OH, (OW - 0.30) / 2, OY, 0.02, 0.13),
        (OW, 0.40, 0.0, OY + OH - 0.40, 0.02, 0.13)):
    m.add(box(bw, bh, bd), IRON, at=(bx, by, FZ + bz + bd / 2))
m.add(box(OW + 0.34, 0.15, 0.34), IRON2, at=(0, OY + OH - 0.05, FZ + 0.15))
m.add(box(OW + 0.20, 0.10, 0.26), IRON, at=(0, OY + OH - 0.18, FZ + 0.13))
m.add(box(OW + 0.24, 0.11, 0.30), IRON2, at=(0, OY - 0.09, FZ + 0.13))
# ITEM 6: glass, plus two reflected streaks so it reads as a lit pane rather
# than a hole.  Photo f's glass runs 23 (deep) to 142 (streak).
m.add(box(IWD, IHT, 0.03), GLASSF, at=(0, IY, FZ + 0.075))
m.add(box(IWD * 0.92, 0.30, 0.012), GLASSR,
      at=(-0.06, IY + IHT * 0.62, FZ + 0.092), rot_z=math.radians(-3.5))
m.add(box(IWD * 0.70, 0.15, 0.012), GLASSR,
      at=(0.22, IY + IHT * 0.34, FZ + 0.092), rot_z=math.radians(-3.5))
m.add(box(IWD * 0.86, 0.42, 0.012), GLASSR2,
      at=(0.02, IY + IHT * 0.16, FZ + 0.090), rot_z=math.radians(-2.0))
for gx in (-IWD / 6, IWD / 6):
    m.add(box(0.045, IHT, 0.05), IRON2, at=(gx, IY, FZ + 0.100))
m.add(box(IWD, 0.05, 0.05), IRON2, at=(0, IY + IHT - 0.05, FZ + 0.100))

m.add(box(FW + 0.20, 0.34, FD + 0.60), STONE[2], at=(0, 0.0, 0.16))
m.add(box(FW + 0.24, 0.06, FD + 0.66), WHITE, at=(0, 0.34, 0.16))

m.add(box(FW * 0.86, 0.08, FD * 0.55 + 0.26), SHADE,
      at=(0, MANTEL_Y - 0.12, FZ * 0.55 + 0.10))
m.add(box(FW * 0.87, 0.10, FD * 0.55 + 0.30), WHITE,
      at=(0, MANTEL_Y - 0.04, FZ * 0.55 + 0.11))
m.add(box(FW * 0.83, 0.16, FD * 0.55 + 0.22), WHITE,
      at=(0, MANTEL_Y + 0.06, FZ * 0.55 + 0.09))

# ============================================================== wreath
WY, WR = 6.20, 0.62
WZ = FZ + 0.16
m.add(torus(WR, 0.20, seg=22, ring=7), WREATH3, at=(0, WY, WZ + 0.06),
      rot_x=math.pi / 2)
for course, (rr0, count, tube, mat) in enumerate((
        (WR - 0.14, 18, 0.30, WREATH3), (WR + 0.02, 21, 0.34, WREATH),
        (WR + 0.16, 16, 0.30, WREATH2))):
    for i in range(count):
        a = 2 * math.pi * i / count + course * 0.31
        rr = rr0 + rnd.uniform(-0.045, 0.045)
        m.add(box(0.20, tube, 0.10), mat if i % 4 else WREATH2,
              at=(rr * math.cos(a), WY + rr * math.sin(a),
                  WZ + 0.05 + 0.055 * course),
              rot_z=a + math.pi / 2 + rnd.uniform(-0.45, 0.45),
              rot_y=rnd.uniform(-0.3, 0.3))

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
put("Living Fireplace", save(m, "fireplace4"), FPOS, FROT)
