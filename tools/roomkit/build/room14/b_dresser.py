"""Dresser + mirror — round 3.

Two failures to close:

 * "the mirror renders as a dark switched-off TV rather than a bright reflective
   pane".  Round 2 metered the pane at 190/223 = 0.85 and the photo at 0.88, so
   the MEAN was right -- what was missing is CONTRAST.  In the photo the pane is
   not a flat value at all: the left 55% of it is a blown-out reflected window
   with blind slats running 195..215, and the right side is dark clutter at
   60..95, mean ~140 against a 177 wall.  This build paints that: a large bright
   reflected window (near white, 1.05-1.12 of the wall) with slats, a bright
   reflected wall panel beside it, and only a small dark stack low-right.
 * "the dresser crowds the bed".  The bed shrank to a queen and moved east, and
   the case narrows 4.50 -> 4.00 ft so the north wall can hold
   dresser(0.05..4.05) + gap + window(4.55..6.65) + gap + bed(7.03..12.48) +
   nightstand(12.5..14.7) inside its 15 ft.

Photo proportions used: dresser top slab spans photo x 209..405 and its feet
reach y 800 from a slab front edge at y 645, so h/w = 0.79 on a face that is
foreshortened -- true 4.0 x 3.08 ft overall.  The mirror measures photo
206..352 x 511..630, i.e. 0.74 of the dresser's width and h/w 0.815.
"""
import sys
sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
from roomkit.glb import Model, Material, box, rounded_box, cylinder

OUT = sys.argv[1] if len(sys.argv) > 1 else "../glb/dresser.glb"

# palette carried over from round 2 (it metered right against the photo)
CASE = Material("case", "#777c84", roughness=0.68)
GRAINL = Material("grainl", "#82878f", roughness=0.64)
GRAIND = Material("graind", "#73787f", roughness=0.72)
PULL = Material("pull", "#565b63", roughness=0.55)
REVEAL = Material("reveal", "#5b6067", roughness=0.80)
FRAME = Material("frame", "#858a92", roughness=0.66)
KRAFT = Material("kraft", "#ab9271", roughness=0.90)
PILEC = Material("pile", "#43474e", roughness=0.85)
FOLD = Material("fold", "#767a82", roughness=0.88)
CERAM = Material("ceram", "#e6e4df", roughness=0.55)
# --- mirror: brighter base, and a reflection with real range ---------------
GBASE = Material("gbase", "#b7bcc3", roughness=0.14, metallic=0.06)
GWIN = Material("gwin", "#f7f9fb", roughness=0.08, metallic=0.03)
GSLAT = Material("gslat", "#dde2e8", roughness=0.10, metallic=0.03)
GWALL = Material("gwall", "#cbcfd5", roughness=0.16, metallic=0.05)
GDARK = Material("gdark", "#5b6069", roughness=0.22, metallic=0.06)

CW, CH, CD = 4.00, 2.72, 1.42     # case body
FOOT = 0.26
SLAB_W, SLAB_D, SLAB_T = 4.14, 1.52, 0.11

m = Model()

# ---- case ----------------------------------------------------------------
m.add(box(CW, CH, CD), CASE, at=(0, FOOT, 0))
for sx in (-1, 1):
    for sz in (-1, 1):
        m.add(box(0.20, FOOT, 0.20), CASE,
              at=(sx * (CW / 2 - 0.16), 0, sz * (CD / 2 - 0.16)))
m.add(box(SLAB_W, SLAB_T, SLAB_D), GRAINL, at=(0, FOOT + CH, 0))

# horizontal grain streaks on the case ends and front
for i, y in enumerate([0.45, 0.95, 1.55, 2.20, 2.62]):
    mat = GRAINL if i % 2 else GRAIND
    m.add(box(CW - 0.05, 0.05, 0.01), mat, at=(0, y, CD / 2 + 0.005))

# ---- six drawers, 2 cols x 3 rows ----------------------------------------
gx, gy = 0.05, 0.05
dw = (CW - 3 * gx) / 2
dh = (CH - 4 * gy) / 3
for r in range(3):
    for c in range(2):
        x = -CW / 2 + gx + dw / 2 + c * (dw + gx)
        y = FOOT + gy + r * (dh + gy)
        m.add(box(dw, dh, 0.06), GRAINL if (r + c) % 2 else CASE,
              at=(x, y, CD / 2 + 0.03))
        m.add(box(dw, 0.04, 0.03), REVEAL, at=(x, y - 0.04, CD / 2 + 0.035))
        m.add(box(dw * 0.44, 0.055, 0.05), PULL,
              at=(x, y + dh * 0.52, CD / 2 + 0.075))

# ---- mirror --------------------------------------------------------------
MW_, MH = 2.96, 2.42
RAIL = 0.20
MY = FOOT + CH + SLAB_T
MX = -0.10                                # sits slightly left of centre
MZ = -CD / 2 + 0.28
m.add(box(MW_, RAIL, 0.12), FRAME, at=(MX, MY, MZ))
m.add(box(MW_, RAIL, 0.12), FRAME, at=(MX, MY + MH - RAIL, MZ))
for sx in (-1, 1):
    m.add(box(RAIL, MH, 0.12), FRAME, at=(MX + sx * (MW_ / 2 - RAIL / 2), MY, MZ))

gw, gh = MW_ - 2 * RAIL, MH - 2 * RAIL
gz = MZ + 0.045
m.add(box(gw, gh, 0.02), GBASE, at=(MX, MY + RAIL, gz))

# reflected wall behind everything, then a big bright window on the left
m.add(box(gw * 0.98, gh * 0.96, 0.012), GWALL, at=(MX, MY + RAIL + gh * 0.02, gz + 0.012))
wx, wy = MX - gw * 0.16, MY + RAIL + gh * 0.20
ww, wh = gw * 0.52, gh * 0.66
m.add(box(ww, wh, 0.012), GWIN, at=(wx, wy, gz + 0.024))
for i in range(11):
    m.add(box(ww * 0.97, 0.018, 0.010), GSLAT,
          at=(wx, wy + wh * (i + 0.5) / 11, gz + 0.036))
# a dark stack low-right (the clothes/bag reflected) and the vault shadow above
m.add(box(gw * 0.40, gh * 0.46, 0.012), GDARK,
      at=(MX + gw * 0.27, MY + RAIL + gh * 0.02, gz + 0.024))
m.add(box(gw * 0.98, gh * 0.09, 0.012), GDARK,
      at=(MX, MY + RAIL, gz + 0.030))
m.add(box(gw * 0.98, gh * 0.10, 0.012), GDARK,
      at=(MX, MY + RAIL + gh * 0.90, gz + 0.024))

# ---- clutter on the slab (the photo's paper bag + folded darks) -----------
TOP = FOOT + CH + SLAB_T
m.add(box(0.78, 0.92, 0.52), KRAFT, at=(0.62, TOP, -0.10), rot_y=0.22)
m.add(rounded_box(1.05, 0.30, 0.62, r=0.08), PILEC, at=(-0.35, TOP, 0.02), rot_y=-0.15)
m.add(rounded_box(0.86, 0.22, 0.52, r=0.07), FOLD, at=(-0.40, TOP + 0.30, 0.04))
m.add(cylinder(0.17, 0.20, seg=16), CERAM, at=(-1.42, TOP, 0.10))

m.save(OUT)
lo, hi = m.bounds()
print("bounds", tuple(round(v, 3) for v in lo), tuple(round(v, 3) for v in hi))
print("size", tuple(round(hi[i] - lo[i], 3) for i in range(3)))
