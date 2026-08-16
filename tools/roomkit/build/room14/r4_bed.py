"""Master Bed — round 3 rebuild.

Round 2 built a KING (6.6 ft frame) on a deep two-drawer storage plinth. Measured
off the photo the bed is a QUEEN on a low platform:

  * two euro shams span photo x 575..825 = 250 px; two shams = 52 in = 4.33 ft
    -> 57.7 px/ft at the head of the bed.
  * the nightstand beside it is 128 px tall (photo y 742..870) -> 2.2 ft, the
    standard height, at ~58 px/ft: the same scale.
  * the headboard spans photo x 605..886 = 281 px -> 281/55 = 5.1 ft, and stands
    872-616 = 256 px -> 4.6 ft off the floor. That is a stock queen panel
    headboard (63 in x 55 in), NOT a king.
  * the SE foot post runs photo y 880..960 = 80 px at the foot end (~72 px/ft
    there) -> the foot rail tops out 1.1 ft off the floor and the mattress top
    sits ~2.1 ft, i.e. a slim mattress on a low frame.
  * one shallow drawer front between the foot posts, ~0.6 ft tall, recessed.
"""
import sys
sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
from roomkit.glb import Model, Material, Part, box, rounded_box, sag_plane
import math

OUT = sys.argv[1] if len(sys.argv) > 1 else "../glb/bed.glb"

# grey weathered oak, same family as the dresser (metered in round 2 at 0.63 of
# the wall); the bed frame reads a shade lighter in the photo (156/177 = 0.88 on
# the sunlit headboard face, 118/177 on shaded sides) so it is authored lighter
# and let the renderer shade it.
OAK = Material("bedoak", "#717379", roughness=0.72)          # plank field
OAK_S = Material("bedoak_stile", "#616468", roughness=0.70)  # stiles/rails/posts
OAK_D = Material("bedoak_dark", "#484c50", roughness=0.75)     # reveals
LINEN = Material("duvet", "#eef0f1", roughness=0.99)
MATT = Material("mattress", "#dcdedf", roughness=0.95)
SHAM = Material("sham", "#d2d3d3", roughness=0.96)
PILLOW = Material("pillow", "#f3f4f5", roughness=0.97)
PULL = Material("pull", "#3c3c3e", roughness=0.5, metallic=0.4)

W = 5.35          # frame width
L = 7.30          # frame length, headboard back to foot rail face
HB_H = 4.55       # headboard height
RAIL_TOP = 1.15   # top of side/foot rails
DECK = 1.12       # mattress support
MATT_H = 0.86     # slim mattress

z_head = -L / 2   # -3.65
z_foot = L / 2    # +3.65

m = Model()

# ---- headboard -----------------------------------------------------------
# stiles to the floor, top cap, horizontal plank field between
ST = 0.30
m.add(box(ST, HB_H, 0.20), OAK_S, at=(-(W / 2 - ST / 2), 0, z_head + 0.10))
m.add(box(ST, HB_H, 0.20), OAK_S, at=(W / 2 - ST / 2, 0, z_head + 0.10))
m.add(box(W, 0.34, 0.24), OAK_S, at=(0, HB_H - 0.34, z_head + 0.10))      # top rail
m.add(box(W + 0.10, 0.09, 0.30), OAK_S, at=(0, HB_H - 0.09, z_head + 0.12))  # cap
# plank field, 4 boards with dark reveals, set 0.03 proud of the stiles
fw = W - 2 * ST
y0, y1 = 1.55, HB_H - 0.34
n = 4
for i in range(n):
    h = (y1 - y0) / n
    m.add(box(fw, h - 0.035, 0.10), OAK, at=(0, y0 + i * h, z_head + 0.17))
    m.add(box(fw, 0.035, 0.06), OAK_D, at=(0, y0 + i * h + h - 0.035, z_head + 0.15))
# lower blank panel behind the mattress
m.add(box(fw, y0, 0.10), OAK_S, at=(0, 0, z_head + 0.15))

# ---- side rails + foot ---------------------------------------------------
RT = 0.18
for sx in (-1, 1):
    m.add(box(RT, RAIL_TOP - 0.45, L - 0.45), OAK_S,
          at=(sx * (W / 2 - RT / 2), 0.45, 0.10))
# foot rail
m.add(box(W, 0.44, 0.20), OAK_S, at=(0, RAIL_TOP - 0.44, z_foot - 0.10))
m.add(box(W, 0.05, 0.24), OAK, at=(0, RAIL_TOP - 0.05, z_foot - 0.10))   # foot cap
# foot posts, floor to rail top
for sx in (-1, 1):
    m.add(box(0.32, RAIL_TOP, 0.30), OAK_S,
          at=(sx * (W / 2 - 0.16), 0, z_foot - 0.15))
# head posts (visible sliver beside the mattress)
for sx in (-1, 1):
    m.add(box(0.30, RAIL_TOP, 0.28), OAK_S,
          at=(sx * (W / 2 - 0.15), 0, z_head + 0.34))

# ---- ONE shallow drawer at the foot --------------------------------------
DW, DH = W - 2 * 0.36, 0.60
m.add(box(DW, DH, 0.08), OAK, at=(0, 0.10, z_foot - 0.26))
m.add(box(DW, 0.035, 0.05), OAK_D, at=(0, 0.10 + DH, z_foot - 0.27))   # reveal over
m.add(box(0.90, 0.055, 0.05), PULL, at=(0, 0.10 + DH * 0.55, z_foot - 0.21))
# dark recess band under the rail so the drawer reads as set back
m.add(box(DW, 0.06, 0.04), OAK_D, at=(0, 0.10 - 0.06, z_foot - 0.27))

# ---- mattress + bedding --------------------------------------------------
m.add(rounded_box(W - 0.36, MATT_H, L - 1.05, r=0.10, seg=3), MATT,
      at=(0, DECK, 0.02))
# duvet: a FLAT top that only breaks over the mattress edge.  sag_plane domes
# the whole panel, and under this renderer's hemisphere term that dome shows up
# as a pale elliptical blob in the middle of the bed -- a real duvet is flat on
# top with the fall confined to the last few inches, so it is meshed by hand.
DW_, DD_ = W + 0.14, L - 1.40
DTOP = DECK + MATT_H + 0.09
NXD, NZD = 26, 30
dv, dt = [], []
for iz in range(NZD + 1):
    for ix in range(NXD + 1):
        x = (ix / NXD - 0.5) * DW_
        z = (iz / NZD - 0.5) * DD_
        ex = DW_ / 2 - abs(x)
        ez = DD_ / 2 - abs(z)
        e = min(ex, ez)
        t = 1.0 - min(1.0, max(0.0, e / 0.42))      # 0 inside, 1 at the edge
        y = -1.02 * (t * t * (3 - 2 * t))
        y += 0.022 * math.sin(x * 2.6 + z * 1.7) * (1 - t)   # soft wrinkles
        dv.append((x, DTOP + y, z))
for iz in range(NZD):
    for ix in range(NXD):
        a = iz * (NXD + 1) + ix
        dt += [(a, a + NXD + 1, a + 1), (a + 1, a + NXD + 1, a + NXD + 2)]
m.add(Part(dv, dt, smooth=True), LINEN, at=(0, 0, 0.60))
# a soft foot drape hanging past the foot of the mattress
m.add(sag_plane(W - 0.30, 0.95, sag=0.02, nx=10, nz=4, edge_drop=0.30), LINEN,
      at=(0, DECK + MATT_H - 0.18, z_foot - 0.62))

# ---- pillows: FOUR readable pieces, not two bolsters ----------------------
# Round-3 critic: "pillows read as two white bolsters, not the photo's
# four-piece stack".  They were four pieces already; the failure was that the
# pair on each row met with no gap and no value break, so each row fused into
# one lozenge.  Fixed three ways: a 0.16 ft gap down the centre of BOTH rows, a
# value split (standing euro shams a shade greyer than the sleeping pillows,
# which is what the photo shows), and a thin piped edge on the shams so their
# silhouette has a line in it at distance.
SHAM_W, SHAM_T, SHAM_H = 2.05, 0.46, 1.86
PIL_W, PIL_T, PIL_D = 2.35, 0.60, 1.24
GAP = 0.16

# back row: two euro shams standing against the headboard, tipped back
for sx in (-1, 1):
    cx = sx * (SHAM_W + GAP) / 2
    m.add(rounded_box(SHAM_W, SHAM_H, SHAM_T, r=0.16, seg=5), SHAM,
          at=(cx, DECK + MATT_H - 0.06, z_head + 1.02), rot_x=-0.30)
    # piping: a slightly darker seam band around the face
    m.add(rounded_box(SHAM_W - 0.13, SHAM_H - 0.13, SHAM_T + 0.035, r=0.14, seg=5),
          MATT, at=(cx, DECK + MATT_H + 0.00, z_head + 1.02), rot_x=-0.30)

# front row: two sleeping pillows lying flat, clearly separated
for sx in (-1, 1):
    cx = sx * (PIL_W + GAP) / 2
    m.add(rounded_box(PIL_W, PIL_T, PIL_D, r=0.26, seg=5), PILLOW,
          at=(cx, DECK + MATT_H + 0.01, z_head + 1.62), rot_x=-0.16)

m.save(OUT)
lo, hi = m.bounds()
print("bounds lo", tuple(round(v, 3) for v in lo), "hi", tuple(round(v, 3) for v in hi))
print("size", tuple(round(hi[i] - lo[i], 3) for i in range(3)))
