"""Round 5 focal wall: stone relief restored, the TV as photo f shows it, and a
matte wreath.

STONE.  Round 3 metered sd 34 and answered it by deleting the chamfer; round 4
shipped flat caps 0.036-0.058 ft proud of a bright joint plane and metered
mean 195.1 / sd 10.8 / |d1| 0.47 against photo f's 180.8-187.4 / 8.4-11.2 /
1.74-2.72.  Both were the wrong trade: p5_stone.png at native resolution shows
LARGE white plates with SOFT ROLLED shoulders and thin dark seams -- 1st to 99th
percentile 152-194 -- i.e. heavy relief that meters a small sd because the
relief is large-scale and the joints occupy about 1% of the pixels.

So the bevel comes back, shallower and in TWO soft steps (`plate5`), the joint
goes back to being genuinely darker but NARROW (0.024 ft of shrink, about 1.8 px
at this pose), and the fine gradient comes from a tiled speckle rather than from
more geometry -- shading cannot carry it here (see b5_soft's header).

TV.  Photo f shows a hard matte-black rectangle with a visible bezel edge and
one soft reflection; its left half meters 31.4 (rgb 28,31,41) at sd 3.8 and its
middle 83.8.  Round 3/4 painted a full-bleed mountain-lake picture over the
whole panel with no edge.  Photo A does show the set switched on, so this is a
choice between two photographs; photo f is 1200x1600 against A's 450x600 and is
where every other surface in this room was metered, so it wins.

WREATH.  Photo f's wreath meters 89.9-105.8 at rgb (89,90,95) -- a dark, almost
neutral dusty lavender, matte, with the stone showing through its centre.  Round
4's was #867f92 at roughness 0.94 over a solid torus and rendered as a glossy
purple disc with shards.
"""
import math
import random

from kit5 import *
from kit5 import Part, Material, Model, _shrink

rnd = random.Random(50510)

# ------------------------------------------------------------------- tiles
T_STONE = Tex(noise_tile(64, 0.86, 1.0, seed=61, blur=1), 1.00, "stonegrain")
LST = tex_lift(T_STONE)


def lift(hexc, f):
    r, g, b = (int(hexc[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % tuple(min(255, int(round(c * f))) for c in (r, g, b))


GST = Grain(71, fine=0.30, fine_amp=0.006, coarse=0.90, coarse_amp=0.012)

# ROUND 5b.  The first round-5 pass metered a clean face at 164.3 mean / sd 40.0
# over 312,800 px against photo f's stone at 180.7-182.9 / sd 3.5-6.9 on clean
# plates and 23.9-30.0 on fields that include joints: the render was 17 bytes
# DARK and carried three times the photo's within-stone contrast, because the
# relief was tall enough (0.085-0.135 ft over a 0.035 ft shoulder, ~65 deg) to
# shade every stone into a pillow.  The family lifts ~9%, and the SEVEN tones
# span 0x9c..0xc2 so that most of the field's spread is stone-TO-stone -- which
# is what "stones varying 89 -> 209 at ~6 inch scale" describes -- instead of
# gradient across one stone.
STONE = [TMaterial("lrstoneA", lift("#b6b2ac", LST), tex=T_STONE, roughness=0.97),
         TMaterial("lrstoneB", lift("#aeaaa4", LST), tex=T_STONE, roughness=0.97),
         TMaterial("lrstoneC", lift("#c2beb8", LST), tex=T_STONE, roughness=0.97),
         TMaterial("lrstoneD", lift("#a6a29c", LST), tex=T_STONE, roughness=0.97),
         TMaterial("lrstoneE", lift("#bcb8b2", LST), tex=T_STONE, roughness=0.97),
         TMaterial("lrstoneF", lift("#9e9a94", LST), tex=T_STONE, roughness=0.97),
         TMaterial("lrstoneG", lift("#b0aca6", LST), tex=T_STONE, roughness=0.97)]
STONE_P = Material("lrstonep", "#b6b2ac", roughness=0.97)      # untextured trim
# deep raked joint -- dark, but only 0.024 ft of it is ever visible
JOINT = Material("lrjoint", "#6f6c66", roughness=0.99)
WHITE = Material("lrfwhite", "#f2f1ec", roughness=0.55)
SHADE = Material("lrfshade", "#8b8880", roughness=0.95)
IRON = Material("lrfiron", "#2b2d30", roughness=0.55, metallic=0.25)
IRON2 = Material("lrfiron2", "#3a3d41", roughness=0.45, metallic=0.30)
VOID = Material("lrfvoid", "#131316", roughness=0.98)
EMBER = Material("lrfember", "#2a2320", roughness=0.95)
LOG = Material("lrflog", "#3a332c", roughness=0.95)
GLASSF = Material("lrfglass", "#3b414a", roughness=0.34, metallic=0.05)
GLASSR = Material("lrfglassr", "#6b737e", roughness=0.22, metallic=0.05)
GLASSR2 = Material("lrfglassr2", "#4e555e", roughness=0.26, metallic=0.05)
# matte, dark, barely purple.  Photo f's fronds meter 90.5 / 95.3 rgb(90,90,96);
# round 5b's #6b6774 family rendered 146.5 / 149.4, 55 bytes light, so the whole
# family is scaled 0.62.
T_WR = Tex(noise_tile(64, 0.62, 1.0, seed=83, blur=1), 0.42, "wreath")
LWR = tex_lift(T_WR)
WREATH = TMaterial("lrwreath", lift("#423f48", LWR), tex=T_WR, roughness=0.99, double_sided=True)
WREATH2 = TMaterial("lrwreath2", lift("#4a4752", LWR), tex=T_WR, roughness=0.99, double_sided=True)
WREATH3 = TMaterial("lrwreath3", lift("#39373f", LWR), tex=T_WR, roughness=0.99, double_sided=True)
VASE = Material("lrvase", "#d8d6d0", roughness=0.45)
LEAF = Material("lrleaf", "#57634f", roughness=0.85)

FW, FH, FD = 6.86, 9.00, 0.85
MANTEL_Y = 4.45
ZJ = FD / 2 - 0.095                # joint plane, recessed behind the stones
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
    # LEDGESTONE character: courses half as tall as round 4's and widths from
    # 0.34 ft to 1.6 ft, so the ~6 inch stones photo f shows between the big
    # plates actually exist.  Round 4/5a's near-equant 0.85 ft grid read as a
    # regular honeycomb.
    # NOTE: seeds are laid over the WHOLE face including the firebox cut.
    # Round 5b passed `cut=` and left the cut region seedless, so the Voronoi
    # cells around it grew until their CENTROIDS fell inside the box -- and
    # `clip_out` drops a cell whose centroid is inside -- which opened a bare
    # grey hole round the firebox a good foot wider than the surround.
    seeds = coursed_seeds(x0, x1, y0, y1, rnd, course=0.62, pitch=0.60,
                          wlo=0.58, whi=2.70, hlo=0.60, hhi=1.85)
    n = 0
    for _seed, cell in voronoi_cells(seeds, (x0, y0, x1, y1)):
        if cut:
            cell = clip_out(cell, cut)
        if len(cell) < 3 or poly_area(cell) < 0.04:
            continue
        p = wobble(_shrink(cell, 0.030), rnd, amp=0.060, sub=1)
        # relief kept, but HALVED and spread over a wide shoulder: the plate
        # face has to stay flat enough to meter the photo's sd 3.5-6.9 within
        # one stone while the joint still reads as a raked dark line.
        h = rnd.uniform(0.042, 0.072)
        # n_ring=1: at this relief the shoulder is a 30 deg chamfer and the
        # second ring only bought payload -- 84 stones at n_ring=2 put the
        # piece over the 300 KB cap.
        add5(m, plate5(p, ZJ, h, bevel=0.065, rise=0.26, n_ring=1, grain=GST,
                       uv_repeat=T_STONE.repeat,
                       tilt=(rnd.uniform(-.022, .022), rnd.uniform(-.022, .022))),
             STONE[rnd.randrange(len(STONE))])
        n += 1
    return n


m = Model()
m.add(box(FW, FH, ZJ + FD / 2), JOINT, at=(0, 0, -(FD / 2 - ZJ) / 2))
n_stone = stone_face(m, -FW / 2, FW / 2, 0.0, FH, cut=(-FBX, FBY0, FBX, FBY1))
print("  stones on face: %d" % n_stone)

for sx in (-1, 1):                              # returns down both chase ends
    y = 0.0
    while y < FH - 0.01:
        h = min(rnd.uniform(0.62, 1.10), FH - y)
        pro = rnd.uniform(0.03, 0.08)
        m.add(box(pro, h - 0.045, FD - 0.13), STONE_P,
              at=(sx * (FW / 2 + pro / 2 - 0.01), y + 0.023, -0.02))
        y += h

# ================================================================== firebox
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
# glass: confirmed good in round 4 (81.0 sd 32.8 vs photo f's 94.4 sd 26.9)
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

m.add(box(FW + 0.20, 0.34, FD + 0.60), STONE_P, at=(0, 0.0, 0.16))
m.add(box(FW + 0.24, 0.06, FD + 0.66), WHITE, at=(0, 0.34, 0.16))

m.add(box(FW * 0.86, 0.08, FD * 0.55 + 0.26), SHADE,
      at=(0, MANTEL_Y - 0.12, FZ * 0.55 + 0.10))
m.add(box(FW * 0.87, 0.10, FD * 0.55 + 0.30), WHITE,
      at=(0, MANTEL_Y - 0.04, FZ * 0.55 + 0.11))
m.add(box(FW * 0.83, 0.16, FD * 0.55 + 0.22), WHITE,
      at=(0, MANTEL_Y + 0.06, FZ * 0.55 + 0.09))

# =================================================================== wreath
# No solid torus: photo f shows the stone through the middle of the ring, and a
# filled torus behind thin fronds is exactly what read as a glossy disc.  Fronds
# only, three courses, matte, each a thin tapered plate laid tangentially.
WY, WR = 6.20, 0.60
WZ = FZ + 0.16
# Round 5a's 80 long fronds at +/-0.55 rad of jitter read as a spiky lavender
# star.  Photo f shows a DENSE soft ring: short overlapping leaves, an open
# centre about a third of the outer radius, and no shard longer than ~0.25 ft.
def leaf_quad(w, ln):
    """One leaf as a 2-triangle double-sided plate.  142 leaves as boxes is
    5112 welded verts (12 tris each); as quads it is 852."""
    return Part([(-w / 2, -ln / 2, 0.0), (w / 2, -ln / 2, 0.0),
                 (w / 2, ln / 2, 0.0), (-w / 2, ln / 2, 0.0)],
                [(0, 1, 2), (0, 2, 3)])


for course, (rr0, count, ln, wd, mat) in enumerate((
        (WR - 0.22, 30, 0.30, 0.105, WREATH3),
        (WR - 0.09, 36, 0.34, 0.115, WREATH),
        (WR + 0.04, 38, 0.32, 0.110, WREATH2),
        (WR + 0.16, 34, 0.26, 0.095, WREATH))):
    for i in range(count):
        a = 2 * math.pi * i / count + course * 0.21
        rr = rr0 + rnd.uniform(-0.035, 0.035)
        m.add(leaf_quad(wd, ln), mat if i % 3 else WREATH2,
              at=(rr * math.cos(a), WY + rr * math.sin(a),
                  WZ + 0.03 + 0.028 * course),
              # TANGENTIAL, not radial: rot_z = a + pi/2 pointed every leaf
              # straight out from the centre and drew a starburst.
              rot_z=a + rnd.uniform(-0.40, 0.40),
              rot_y=rnd.uniform(-0.16, 0.16),
              rot_x=rnd.uniform(-0.14, 0.14))

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
put("Living Fireplace", save5(m, "fireplace5"), FPOS, FROT)

# ====================================================================== TV
# Photo f: a hard matte-black rectangle with a visible edge.  Left half 31.4
# (rgb 28,31,41) sd 3.8, middle 83.8 where one soft reflection crosses it.
BEZEL = Material("lrbezel", "#0c0d10", roughness=0.35)
SCREEN = Material("lrtvscreen", "#1c1f28", roughness=0.28, metallic=0.02)
REFL = Material("lrtvrefl", "#2b313b", roughness=0.24, metallic=0.02)
REFL2 = Material("lrtvrefl2", "#242a33", roughness=0.26, metallic=0.02)
BAR = Material("lrbar", "#2a2b2e", roughness=0.7)

TVW, TVH = 6.62, 3.72
TVX, TVY0, TVZ = 8.435, 2.55, 0.05
m = Model()
m.add(box(TVW, TVH, 0.11), BEZEL, at=(TVX, TVY0, TVZ + 0.05))
IW, IH = TVW - 0.13, TVH - 0.13
m.add(box(IW, IH, 0.02), SCREEN, at=(TVX, TVY0 + 0.065, TVZ + 0.155))
# ONE soft off-axis reflection.  Round 5a stacked two small bright plates on
# the panel and they read as a grey rectangle floating in the middle of the
# screen -- exactly the "full-bleed picture" fault in miniature.  It is now a
# single wide band, nearly the panel's own value (photo f: 31.4 on the left
# half, 83.8 where the reflection crosses), spanning most of the width so its
# ends fall off the panel's live area rather than closing into a rectangle.
m.add(box(IW * 0.86, IH * 0.30, 0.008), REFL2,
      at=(TVX + 0.05, TVY0 + IH * 0.52, TVZ + 0.166), rot_z=math.radians(-4))
m.add(box(IW * 0.62, IH * 0.14, 0.008), REFL,
      at=(TVX + 0.30, TVY0 + IH * 0.56, TVZ + 0.172), rot_z=math.radians(-4))
m.add(box(4.10, 0.24, 0.20), BAR, at=(TVX, TVY0 - 0.42, TVZ + 0.10))
put_in_place("Living TV", m, save5(m, "tv5"))
