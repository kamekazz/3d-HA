"""Soft goods: rug, the south sectional, the east sofa, the armchair, two
ottomans and the coffee table -- re-laid into the 20.49 x 16.96 polygon."""
import math
import random

from kit2 import *

rnd = random.Random(5151)

# No shadows in this renderer, so form comes from authored value steps.
UPH = Material("lruph", "#757169", roughness=0.95)
UPHA = Material("lrupha", "#848078", roughness=0.95)
UPH2 = Material("lruph2", "#89857e", roughness=0.96)
UPH3 = Material("lruph3", "#7c7870", roughness=0.96)
REVEAL = Material("lrreveal", "#494641", roughness=0.99)
PLINTH = Material("lrplinth", "#383836", roughness=0.7)
PIL_W = Material("lrpilw", "#9e9c97", roughness=0.95)
PIL_S = Material("lrpils", "#545c65", roughness=0.95)
PIL_G = Material("lrpilg", "#706c65", roughness=0.98)
PIL_C = Material("lrpilc", "#938f87", roughness=0.97)
THROW = Material("lrthrow", "#69686b", roughness=0.99)
THROW2 = Material("lrthrow2", "#89857d", roughness=0.99)
RUGM = Material("lrrug", "#807c75", roughness=0.99)
RUGE = Material("lrruge", "#7a766f", roughness=0.99)
WOODT = Material("lrwoodt", "#494642", roughness=0.7)
METAL = Material("lrmetal", "#17181a", roughness=0.45, metallic=0.3)
TRAY = Material("lrtray", "#a5a39e", roughness=0.4)
GREEN = Material("lrgreen", "#43793f", roughness=0.8)
PAPER = Material("lrpaper", "#9d9a93", roughness=0.9)
DARK = Material("lrdark", "#1c1d21", roughness=0.4)


def sofa(L, D, arm_w=0.92, back_h=2.84, seat_h=1.42, arm_h=2.16, n_seat=3,
         pillows=(), throw=None, ret_w=0.0, ret_d=0.0, ret_side=-1):
    """Sofa authored facing +z (back at -z).  ret_* adds a chaise return of
    width ret_w at the ret_side end, running ret_d further forward."""
    m = Model()
    base_h = 0.26
    m.add(box(L - 0.5, base_h, D - 0.5), PLINTH, at=(0, 0, 0))
    m.add(rounded_box(L, seat_h - 0.22, D, r=0.18, seg=3), UPH, at=(0, base_h, 0))
    m.add(rounded_box(L, back_h - base_h, 0.92, r=0.16, seg=3), UPHA,
          at=(0, base_h, -D / 2 + 0.46))
    for sx in (-1, 1):
        m.add(rounded_box(arm_w, arm_h - base_h, D, r=0.34, seg=4), UPHA,
              at=(sx * (L / 2 - arm_w / 2), base_h, 0))
        m.add(box(0.05, arm_h - base_h - 0.30, D - 0.30), REVEAL,
              at=(sx * (L / 2 - arm_w), base_h + 0.15, 0.06))
    inner = L - 2 * arm_w
    cw = inner / n_seat
    for i in range(n_seat + 1):
        m.add(box(0.07, 0.58, D - 1.0), REVEAL,
              at=(-inner / 2 + cw * i, seat_h - 0.20, 0.22))
    for i in range(n_seat):
        cx = -inner / 2 + cw * (i + 0.5)
        m.add(rounded_box(cw - 0.10, 0.52, D - 1.05, r=0.16, seg=3), UPH2,
              at=(cx, seat_h - 0.16, 0.22))
        m.add(rounded_box(cw - 0.12, 1.22, 0.62, r=0.18, seg=3), UPH3,
              at=(cx, seat_h + 0.30, -D / 2 + 0.78), rot_x=-0.13)
    if ret_w:
        rx = ret_side * (L / 2 - ret_w / 2)
        rz = D / 2 + ret_d / 2
        m.add(box(ret_w - 0.4, base_h, ret_d - 0.2), PLINTH, at=(rx, 0, rz))
        m.add(rounded_box(ret_w, seat_h - 0.22, ret_d + 0.1, r=0.18, seg=3), UPH,
              at=(rx, base_h, rz))
        m.add(rounded_box(ret_w - 0.14, 0.50, ret_d - 0.16, r=0.16, seg=3), UPH2,
              at=(rx, seat_h - 0.16, rz - 0.02))
        m.add(rounded_box(arm_w, arm_h - base_h, ret_d + 0.1, r=0.34, seg=4), UPHA,
              at=(ret_side * (L / 2 - arm_w / 2), base_h, rz))
    for (px, mat, w, h, tilt) in pillows:
        m.add(rounded_box(w, h, 0.38, r=0.13, seg=3), mat,
              at=(px, seat_h + 0.20, -D / 2 + 1.26), rot_z=tilt, rot_x=-0.26)
    if throw:
        (tx, tz, mat) = throw
        m.add(sag_plane(2.9, 3.1, sag=0.12, nx=9, nz=11, edge_drop=0.80), mat,
              at=(tx, back_h - 0.16, -D / 2 + 1.15 + tz), rot_x=0.10)
        m.add(sag_plane(2.7, 1.6, sag=0.09, nx=8, nz=7, edge_drop=0.32), mat,
              at=(tx, seat_h + 0.32, 0.55 + tz))
    return m


# ------------------------------------------------------------------ rug
RX, RZ, RL, RDp, RT = 11.20, 9.80, 13.20, 11.00, 0.075
m = Model()
m.add(box(RL, RT, RDp), RUGM, at=(0, 0, 0))
m.add(box(RL + 0.10, RT * 0.6, RDp + 0.10), RUGE, at=(0, 0, 0))
for i in range(46):
    z = -RDp / 2 + RDp * (i + 0.5) / 46
    m.add(box(RL - 0.06, 0.003, 0.040), RUGE, at=(0, RT, z))
for i in range(30):                      # faint cross weave, both ways
    x = -RL / 2 + RL * (i + 0.5) / 30
    m.add(box(0.030, 0.002, RDp - 0.06), RUGE, at=(x, RT + 0.001, 0))
put("Living Floor Rug", save(m, "rug2"), (RX, 0.004, RZ))

# ------------------------------------------------------------ south sectional
# Backed onto the kitchen half wall, chaise return at its EAST end (photo B).
SD, SRD = 3.55, 2.60
m = sofa(7.60, SD, n_seat=3, ret_w=2.70, ret_d=SRD, ret_side=-1,
         throw=(-0.6, 0.0, THROW), pillows=[
             (-2.6, PIL_W, 1.50, 1.42, 0.10), (-1.4, PIL_S, 1.44, 1.34, -0.14),
             (0.2, PIL_C, 1.46, 1.36, 0.08), (1.5, PIL_S, 1.44, 1.34, 0.13),
             (2.6, PIL_W, 1.50, 1.42, -0.09)])
m.add(sag_plane(2.2, 1.9, sag=0.10, nx=8, nz=8, edge_drop=0.42), THROW2,
      at=(2.1, 1.52, 2.5))
put_anchor("Living Sofa South", m, save(m, "sofa_s2"),
           (0.0, -SD / 2), (4.35, 16.94), 180)

# ------------------------------------------------------------------ east sofa
ED = 3.75
m = sofa(8.40, ED, n_seat=3, throw=(1.9, 0.0, THROW2), pillows=[
    (-2.5, PIL_G, 1.45, 1.40, 0.12), (-1.3, PIL_W, 1.40, 1.30, -0.10),
    (0.0, PIL_S, 1.42, 1.32, 0.06), (1.3, PIL_W, 1.40, 1.30, 0.10),
    (2.5, PIL_S, 1.45, 1.40, -0.13)])
m.add(rounded_box(1.5, 0.42, 1.2, r=0.16, seg=3), PIL_C, at=(-2.6, 1.60, 0.55),
      rot_z=0.12)
put_anchor("Living Sofa East", m, save(m, "sofa_e2"),
           (0.0, -ED / 2), (RW - 0.02, 9.30), 270)

# ------------------------------------------------------------------ armchair
m = sofa(3.60, 4.00, arm_w=0.82, back_h=2.74, arm_h=2.10, n_seat=1,
         throw=(0.0, 0.0, THROW2),
         pillows=[(0.0, PIL_W, 1.55, 1.45, 0.06)])
put_anchor("Living Armchair", m, save(m, "armchair2"), (0.0, -2.0), (0.55, 7.20), 72)


# ------------------------------------------------------------------ ottomans
def ottoman(w, d, h=1.42):
    m = Model()
    m.add(box(w - 0.55, 0.26, d - 0.55), PLINTH, at=(0, 0, 0))
    m.add(rounded_box(w, h - 0.26, d, r=0.20, seg=4), UPH, at=(0, 0.26, 0))
    m.add(rounded_box(w - 0.16, 0.18, d - 0.16, r=0.16, seg=3), UPH2,
          at=(0, h - 0.20, 0))
    return m


# the long one between the armchair and the coffee table (photo f)
m = ottoman(4.40, 2.50, h=1.40)
m.add(box(1.12, 0.05, 0.82), Material("lrlap", "#87898c", roughness=0.35),
      at=(-0.5, 1.40, 0.10), rot_y=0.28)
m.add(box(0.40, 0.05, 0.22), DARK, at=(0.9, 1.40, -0.30), rot_y=-0.35)
m.add(sag_plane(1.5, 1.1, sag=0.05, nx=6, nz=6, edge_drop=0.22), THROW2,
      at=(1.3, 1.42, 0.42))
put("Living Ottoman", save(m, "ottoman2"), (7.70, 0.0, 8.40), rot=3)

# the chaise ottoman in front of the east sofa (photo f)
m = ottoman(4.20, 2.60, h=1.44)
m.add(sag_plane(2.1, 2.0, sag=0.06, nx=8, nz=8, edge_drop=0.34), THROW,
      at=(-0.9, 1.44, 0.10))
put("Living Chaise Ottoman", save(m, "chaise2"), (15.20, 0.0, 7.00), rot=270)

# ------------------------------------------------------------------ coffee table
TW, TD, TH = 4.00, 2.20, 1.46
m = Model()
m.add(box(TW, 0.15, TD), WOODT, at=(0, TH - 0.15, 0))
for sx in (-1, 1):
    x = sx * (TW / 2 - 0.28)
    m.add(box(0.09, TH - 0.15, 0.09), METAL, at=(x, 0, TD / 2 - 0.22))
    m.add(box(0.09, TH - 0.15, 0.09), METAL, at=(x, 0, -TD / 2 + 0.22))
    m.add(box(0.07, 0.07, TD - 0.44), METAL, at=(x, TH - 0.22, 0))
    m.add(box(0.07, 1.52, 0.07), METAL, at=(x, 0.10, 0), rot_x=math.radians(58))
    m.add(box(0.07, 1.52, 0.07), METAL, at=(x, 0.10, 0), rot_x=math.radians(-58))
m.add(box(TW - 1.2, 0.07, 0.07), METAL, at=(0, 0.14, 0))
# the white tray with the bright green object, exactly as every photo shows
m.add(box(2.10, 0.10, 1.24), TRAY, at=(-0.30, TH, 0.02))
m.add(box(2.10, 0.16, 0.06), TRAY, at=(-0.30, TH, 0.63))
m.add(box(2.10, 0.16, 0.06), TRAY, at=(-0.30, TH, -0.59))
m.add(box(0.66, 0.28, 0.52), GREEN, at=(-0.30, TH + 0.06, 0.02), rot_y=0.4)
m.add(box(0.30, 0.06, 0.30), Material("lrcup", "#9c9992", roughness=0.5),
      at=(1.30, TH, -0.28))
m.add(box(0.78, 0.09, 0.56), PAPER, at=(1.20, TH, 0.30), rot_y=-0.2)
m.add(box(0.70, 0.06, 0.50), Material("lrbook", "#5f646a", roughness=0.8),
      at=(1.24, TH + 0.09, 0.34), rot_y=-0.12)
m.add(box(0.42, 0.05, 0.17), DARK, at=(0.95, TH + 0.15, -0.05), rot_y=0.5)
put("Living Coffee Table", save(m, "coffee2"), (12.00, 0.0, 10.50), rot=2)
