"""Round 5 — the armchair, the TV, and the density the photo has and the render
does not.

The critic's list: the white "Tall Chest" in the NW corner is invented and
stands exactly where the photo has a PALE ARMCHAIR and a stack of LEANING
MATTRESS PANELS; the wall-mounted TV on the south wall (Master Bed 2) is the
largest object on that wall and is not built; and the photo is lived in — bags,
folded laundry, a plant, a tablet, a water bottle, a cushion on the sill, a bin,
floor vents, a second lamp — where the render has a plant, a lamp and a laptop.

Everything here is authored facing +z (south) and sitting on y=0, so `place`
seats it.  Run:  python r5_props.py <outdir>
"""
import math
import os
import sys

sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from roomkit.glb import (Model, Material, Part, box, rounded_box,   # noqa: E402
                         cylinder, prism)
from r5_raster import Field, raster, ramp, fbm                      # noqa: E402

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
os.makedirs(OUT, exist_ok=True)


def save(m, name):
    p = os.path.join(OUT, name + ".glb")
    m.save(p)
    lo, hi = m.bounds()
    print("%-22s %5.2f x %5.2f x %5.2f ft  %6.1f KB"
          % (name, hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2],
             os.path.getsize(p) / 1024))
    return p


# ===========================================================================
# 1. ARMCHAIR — the pale upholstered chair in front of Window North.
#    Photo patch 196.6 against a 176.2 wall = 1.116; on our 225 wall that is
#    251, which clips, so the field mean is parked at ~1.07 and the rest of the
#    budget is spent on weave spread.
# ===========================================================================
FAB = ramp("#c3c5c4", "#fbfcfa", 5, "chfab", roughness=0.97)
WOODL = Material("chleg", "#7d7368", roughness=0.7)
FAB_D = Material("chfab_d", "#b3b5b4", roughness=0.97)

m = Model()
CW, CD = 2.72, 2.66
SEAT, BACK = 1.28, 2.86
# splayed tapered legs
for sx in (-1, 1):
    for sz in (-1, 1):
        m.add(box(0.16, SEAT - 0.62, 0.16), WOODL,
              at=(sx * (CW / 2 - 0.20), 0, sz * (CD / 2 - 0.20)))
# seat box + arms + a rounded back
m.add(rounded_box(CW, 0.72, CD, r=0.20, seg=4), FAB_D, at=(0, SEAT - 0.62, 0))
m.add(rounded_box(CW - 0.30, 0.34, CD - 0.44, r=0.16, seg=4), FAB[3],
      at=(0, SEAT - 0.02, 0.06))                     # seat cushion
for sx in (-1, 1):
    m.add(rounded_box(0.40, 0.70, CD - 0.34, r=0.17, seg=4), FAB_D,
          at=(sx * (CW / 2 - 0.20), SEAT - 0.02, 0.02))
# the back: a bulged panel carrying the weave field
BW, BH = CW - 0.34, BACK - SEAT - 0.18
bf = Field(FAB)
NF = len(FAB)


def weave(u, w):
    t = 0.80 + (fbm(u * 4.0, w * 4.0, 61, 3) - 0.5) * 0.30
    e = min(BW / 2 - abs(u), BH / 2 - abs(w))
    if e < 0.0:
        return None
    if e < 0.18:
        t -= 0.34 * (1.0 - e / 0.18)
    return max(0, min(NF - 1, int(t * NF)))


CBY, CBZ = SEAT + 0.14 + BH / 2, -CD / 2 + 0.36
TIL = 0.13
ct, st = math.cos(TIL), math.sin(TIL)
raster(bf,
       lambda u, w: (u,
                     CBY + w * ct + 0.30 * math.cos(math.pi * 0.5 * min(1, abs(u) / (BW / 2))) * math.cos(math.pi * 0.5 * min(1, abs(w) / (BH / 2))) * st,
                     CBZ + w * st + 0.30 * math.cos(math.pi * 0.5 * min(1, abs(u) / (BW / 2))) * math.cos(math.pi * 0.5 * min(1, abs(w) / (BH / 2))) * ct),
       lambda u, w: (0.0, -st, ct),
       -BW / 2, BW / 2, -BH / 2, BH / 2, 20, 20, weave)
bf.emit(m)
m.add(rounded_box(BW, BH, 0.36, r=0.18, seg=4), FAB_D,
      at=(0, SEAT + 0.14, CBZ - 0.14), rot_x=-TIL)
save(m, "armchair")

# ===========================================================================
# 2. LEANING MATTRESS PANELS — three pale slabs propped on the wall, exactly
#    what the photo shows where round 4 stood an invented white chest.
# ===========================================================================
PAN = ramp("#c8c9c6", "#f2f3f0", 4, "pan", roughness=0.95)
m = Model()
pf = Field(PAN)
for i, (dx, th, hh, tilt) in enumerate(((-0.00, 0.22, 3.55, 0.115),
                                        (0.26, 0.20, 3.38, 0.135),
                                        (0.50, 0.17, 3.20, 0.155))):
    w = 1.28 - i * 0.06
    m.add(box(w, hh, th), PAN[1 + (i % 2)],
          at=(dx * 1.6, 0, dx + 0.10), rot_x=-tilt)
    # a quilted face so it reads as a mattress panel, not a plank
    ct, st = math.cos(-tilt), math.sin(-tilt)

    def face(u, v, dx=dx, hh=hh, th=th, ct=ct, st=st):
        y, z = v + hh / 2, th / 2 + 0.004
        return (dx * 1.6 + u, y * ct - z * st, dx + 0.10 + y * st + z * ct)

    raster(pf, face, lambda u, v, ct=ct, st=st: (0.0, -st, ct),
           -w / 2 + 0.03, w / 2 - 0.03, -hh / 2 + 0.03, hh / 2 - 0.03, 6, 16,
           lambda u, v: max(0, min(len(PAN) - 1,
                                   int((0.72 + 0.16 * math.sin(v * 6.0)
                                        + (fbm(u * 3, v * 3, 5, 2) - 0.5) * 0.2)
                                       * len(PAN)))))
pf.emit(m)
save(m, "lean_panels")

# ===========================================================================
# 3. WALL TV — Master Bed 2.  This is a Home Assistant house, so it is a
#    controllable device, not decor: it is placed as `Master TV` and the room's
#    media_player entity marker sits on the same wall.
#    Measured off Master Bed 2 against the two doors flanking it (door leaves
#    6.67 ft tall, 178 px and 97 px, so 26.7 and 14.5 px/ft): the panel is
#    ~3.9 ft tall by ~5.1 ft along the wall, i.e. a 65-70 in set, mounted with
#    its bottom ~3.3 ft off the floor over a white soundbar.
# ===========================================================================
SCREEN = Material("tv_screen", "#131417", roughness=0.16, metallic=0.25)
BEZEL = Material("tv_bezel", "#26282b", roughness=0.4, metallic=0.3)
BAR = Material("tv_bar", "#f2f2f0", roughness=0.6)
BRK = Material("tv_brk", "#3a3c3f", roughness=0.5, metallic=0.4)
TVW, TVH = 4.62, 2.66
m = Model()
m.add(box(TVW, TVH, 0.09), BEZEL, at=(0, 0, 0.055))
m.add(box(TVW - 0.06, TVH - 0.06, 0.02), SCREEN, at=(0, 0.03, 0.105))
m.add(box(TVW * 0.30, TVH * 0.55, 0.012), Material("tv_glow", "#1b1d22",
                                                   roughness=0.1, metallic=0.3),
      at=(TVW * 0.16, TVH * 0.30, 0.113))          # a soft window reflection
m.add(box(1.30, 0.42, 0.055), BRK, at=(0, TVH / 2 - 0.21, 0.01))
m.add(cylinder(0.115, 2.40, seg=14, anchor="center"), BAR,
      at=(0, -0.36, 0.10), rot_z=math.pi / 2)      # the white soundbar
save(m, "tv")

# ===========================================================================
# 4. DENSITY.  Bags and folded laundry on the dresser, a plant, a bin, a
#    tablet + bottle + speaker on the nightstand, a cushion on the sill, two
#    floor vents, a second lamp, a laundry stack on the floor.
# ===========================================================================
KRAFT = Material("kraft", "#b9a382", roughness=0.9)
CLOTH_D = Material("cloth_dark", "#3a3c40", roughness=0.95)
CLOTH_M = Material("cloth_mid", "#8d9095", roughness=0.95)
CLOTH_L = Material("cloth_pale", "#e6e7e5", roughness=0.95)
POT = Material("pot", "#f0f0ee", roughness=0.8)
LEAF = Material("leaf", "#5f7f57", roughness=0.85)
WHITE = Material("propwhite", "#ececeb", roughness=0.8)
CHROME = Material("propchrome", "#9aa0a6", roughness=0.3, metallic=0.7)
DARKP = Material("propdark", "#2b2d30", roughness=0.5)
GLASSP = Material("propglass", "#cfd8de", roughness=0.25, opacity=0.75)

# --- dresser-top clutter: a kraft shopping bag, a dark laundry heap, a plant
m = Model()
m.add(box(0.92, 1.18, 0.52), KRAFT, at=(0.55, 0, 0.02))
m.add(box(0.80, 0.10, 0.42), KRAFT, at=(0.55, 1.18, 0.02))
for i in range(2):                                   # handles
    m.add(box(0.05, 0.26, 0.04), KRAFT, at=(0.30 + i * 0.5, 1.20, -0.16))
m.add(rounded_box(1.05, 0.34, 0.62, r=0.12, seg=3), CLOTH_D, at=(-0.62, 0, 0.0))
m.add(rounded_box(0.92, 0.26, 0.55, r=0.11, seg=3), CLOTH_M, at=(-0.60, 0.32, 0.03))
m.add(rounded_box(0.80, 0.20, 0.48, r=0.10, seg=3), CLOTH_L, at=(-0.58, 0.56, 0.02))
m.add(rounded_box(0.62, 0.40, 0.40, r=0.10, seg=3), CLOTH_D, at=(0.42, 1.16, 0.04))
save(m, "dresser_clutter")

m = Model()
m.add(cylinder(0.30, 0.46, seg=16, r_top=0.34), POT, at=(0, 0, 0))
for i in range(9):
    a = 2 * math.pi * i / 9
    m.add(box(0.10, 0.62, 0.30), LEAF,
          at=(0.16 * math.cos(a), 0.42, 0.16 * math.sin(a)),
          rot_z=0.55 * math.cos(a), rot_x=-0.55 * math.sin(a), rot_y=a)
save(m, "plant")

# --- white bin on the floor beside the dresser
m = Model()
m.add(cylinder(0.44, 1.02, seg=18, r_top=0.50), WHITE, at=(0, 0, 0))
m.add(cylinder(0.51, 0.06, seg=18), Material("binrim", "#dcdcda", roughness=0.8),
      at=(0, 0.98, 0))
save(m, "bin")

# --- nightstand props: a tablet on a stand, a water bottle, a puck speaker
m = Model()
m.add(box(0.86, 0.62, 0.035), DARKP, at=(-0.16, 0.12, 0), rot_x=-0.22)
m.add(box(0.80, 0.56, 0.012), Material("tabscreen", "#8fa6bf", roughness=0.2),
      at=(-0.16, 0.15, 0.025), rot_x=-0.22)
m.add(box(0.30, 0.14, 0.30), DARKP, at=(-0.16, 0, 0.12))
m.add(cylinder(0.13, 0.86, seg=14), GLASSP, at=(0.62, 0, -0.10))
m.add(cylinder(0.11, 0.10, seg=14), CHROME, at=(0.62, 0.86, -0.10))
m.add(cylinder(0.20, 0.16, seg=16), WHITE, at=(0.30, 0, 0.30))
save(m, "nightstand_props")

# --- a small second lamp for the dresser (the photo has one at each end)
m = Model()
m.add(cylinder(0.22, 0.05, seg=16), Material("lampbase", "#c9cbcc", roughness=0.5),
      at=(0, 0, 0))
m.add(cylinder(0.045, 0.72, seg=10), CHROME, at=(0, 0.05, 0))
m.add(cylinder(0.34, 0.62, seg=18, r_top=0.42),
      Material("lampshade", "#f4f3ef", roughness=0.9), at=(0, 0.74, 0))
save(m, "lamp_small")

# --- cushion on the east window sill
CUSH = ramp("#5c5f63", "#f0f1ef", 4, "cush", roughness=0.95)
m = Model()
cf = Field(CUSH)
CWID, CHGT, CTH = 1.32, 1.00, 0.34


def zig(u, w):
    n = len(CUSH)
    e = min(CWID / 2 - abs(u), CHGT / 2 - abs(w))
    if e < 0:
        return None
    s = abs(((u * 2.0 + abs(((w * 1.8) % 1.0) - 0.5) * 2.2) % 1.0) - 0.5) * 2
    t = 0.30 + 0.62 * s
    if e < 0.09:
        t = 0.2
    return max(0, min(n - 1, int(t * n)))


for sz in (1, -1):
    raster(cf, lambda u, w, sz=sz: (u, w + CHGT / 2, sz * (CTH / 2 + 0.002)),
           lambda u, w, sz=sz: (0.0, 0.0, float(sz)),
           -CWID / 2, CWID / 2, -CHGT / 2, CHGT / 2, 13, 9, zig)
cf.emit(m)
m.add(rounded_box(CWID, CHGT, CTH, r=0.13, seg=4), CUSH[1], at=(0, 0, 0))
save(m, "sill_cushion")

# --- floor vents (named with "floor" so objects.js keeps them unpickable)
m = Model()
m.add(box(0.98, 0.02, 0.42), Material("ventframe", "#8a8a88", roughness=0.6,
                                      metallic=0.2), at=(0, 0, 0))
for i in range(9):
    m.add(box(0.86, 0.012, 0.022), Material("ventslat", "#4a4a49", roughness=0.6),
          at=(0, 0.021, -0.17 + i * 0.0425))
save(m, "floor_vent")

# --- folded laundry stack on the floor + an open hamper
m = Model()
m.add(prism([(-0.62, -0.52), (0.62, -0.52), (0.70, 0.60), (-0.70, 0.60)], 1.18),
      Material("hamper", "#d8d6d1", roughness=0.95))
for i, mat in enumerate((CLOTH_L, CLOTH_M, CLOTH_D, CLOTH_L)):
    m.add(rounded_box(1.02 - i * 0.04, 0.20, 0.86, r=0.07, seg=3), mat,
          at=(0.02 * (i % 2), 1.10 + i * 0.20, 0.02))
save(m, "laundry")
