"""Soft goods: rug, three sofas, armchair, two ottomans, coffee table."""
import math, random
from kit import *

rnd = random.Random(5150)

# The app renders no shadows, so form has to come from authored value steps:
# arms lighter than the body, seat tops lighter again, dark reveals between.
UPH = Material("uph", "#aea89d", roughness=0.95)          # body / base shell
UPHA = Material("upha", "#c3bdb2", roughness=0.95)        # arms + back outer
UPH2 = Material("uph2", "#cbc5ba", roughness=0.96)        # seat cushion tops
UPH3 = Material("uph3", "#b8b2a7", roughness=0.96)        # back cushions
PLINTH = Material("plinth", "#3a3a38", roughness=0.7)
PILLOW_W = Material("pilw", "#e9e6de", roughness=0.95)
PILLOW_S = Material("pils", "#7c8896", roughness=0.95)    # navy/white ticking stripe
PILLOW_G = Material("pilg", "#a7a197", roughness=0.98)
THROW = Material("throw", "#9b9a9e", roughness=0.99)
RUGM = Material("rug", "#9a958d", roughness=0.99)
RUGE = Material("ruge", "#938e86", roughness=0.99)
WOODT = Material("woodt", "#6e6a64", roughness=0.7)
METAL = Material("metal", "#17181a", roughness=0.45, metallic=0.3)
TRAY = Material("tray", "#f2f0ea", roughness=0.4)
GREEN = Material("green", "#67b562", roughness=0.8)


# --------------------------------------------------------------- sofa maker
REVEAL = Material("reveal", "#6d6961", roughness=0.99)


def sofa(L, D, arm_w=0.92, back_h=2.82, seat_h=1.42, arm_h=2.18, n_seat=3,
         pillows=(), throw=False, chaise=0.0):
    """Sofa authored facing +z (seat opens toward +z, back at -z)."""
    m = Model()
    base_h = 0.26
    m.add(box(L - 0.5, base_h, D - 0.5), PLINTH, at=(0, 0, 0))
    # frame block (arms + back read as one upholstered shell)
    m.add(rounded_box(L, seat_h - 0.22, D, r=0.18, seg=3), UPH, at=(0, base_h, 0))
    # back
    m.add(rounded_box(L, back_h - base_h, 0.92, r=0.16, seg=3), UPHA,
          at=(0, base_h, -D / 2 + 0.46))
    # arms
    for sx in (-1, 1):
        m.add(rounded_box(arm_w, arm_h - base_h, D, r=0.34, seg=4), UPHA,
              at=(sx * (L / 2 - arm_w / 2), base_h, 0))
        m.add(box(0.05, arm_h - base_h - 0.30, D - 0.30), REVEAL,
              at=(sx * (L / 2 - arm_w), base_h + 0.15, 0.06))
    # seat cushions
    inner = L - 2 * arm_w
    cw = inner / n_seat
    for i in range(n_seat + 1):
        m.add(box(0.07, 0.58, D - 1.0), REVEAL,
              at=(-inner / 2 + cw * i, seat_h - 0.20, 0.22))
    for i in range(n_seat):
        cx = -inner / 2 + cw * (i + 0.5)
        m.add(rounded_box(cw - 0.10, 0.52, D - 1.05, r=0.16, seg=3), UPH2,
              at=(cx, seat_h - 0.16, 0.22))
        # back cushion, leaning
        m.add(rounded_box(cw - 0.12, 1.22, 0.62, r=0.18, seg=3), UPH3,
              at=(cx, seat_h + 0.30, -D / 2 + 0.78), rot_x=-0.13)
    # chaise / return seat at the +x end
    if chaise:
        m.add(box(chaise - 0.4, base_h, D - 0.5), PLINTH, at=(L / 2 + chaise / 2, 0, 0))
        m.add(rounded_box(chaise, seat_h - 0.22, D, r=0.18, seg=3), UPH,
              at=(L / 2 + chaise / 2, base_h, 0))
        m.add(rounded_box(chaise - 0.14, 0.52, D - 0.5, r=0.16, seg=3), UPH2,
              at=(L / 2 + chaise / 2, seat_h - 0.16, 0.10))
    # decorative pillows
    for (px, mat, w, h, tilt) in pillows:
        m.add(rounded_box(w, h, 0.38, r=0.13, seg=3), mat,
              at=(px, seat_h + 0.20, -D / 2 + 1.26), rot_z=tilt, rot_x=-0.26)
    if throw:
        m.add(sag_plane(2.9, 3.0, sag=0.12, nx=9, nz=11, edge_drop=0.75), THROW,
              at=(-L / 2 + 2.0, back_h - 0.16, -D / 2 + 1.15), rot_x=0.10)
        m.add(sag_plane(2.7, 1.5, sag=0.08, nx=8, nz=6, edge_drop=0.30), THROW,
              at=(-L / 2 + 2.0, seat_h + 0.30, 0.55))
    return m


# --------------------------------------------------------------- rug
RL, RD_, RT = 17.6, 12.2, 0.075
m = Model()
m.add(box(RL, RT, RD_), RUGM, at=(0, 0, 0))
m.add(box(RL + 0.10, RT * 0.6, RD_ + 0.10), RUGE, at=(0, 0, 0))
# fine weave ribs so it does not read as a flat card
for i in range(52):
    z = -RD_ / 2 + RD_ * (i + 0.5) / 52
    m.add(box(RL - 0.06, 0.003, 0.040), RUGE, at=(0, RT, z))
p = save(m, "rug")
put("Living Rug", p, (15.9, 0.004, 8.4))

# --------------------------------------------------------------- sofas
m = sofa(10.6, 3.62, n_seat=3, throw=True, pillows=[
    (-3.3, PILLOW_W, 1.55, 1.45, 0.10), (-2.0, PILLOW_S, 1.45, 1.35, -0.14),
    (2.0, PILLOW_S, 1.45, 1.35, 0.12), (3.3, PILLOW_W, 1.55, 1.45, -0.09)])
p = save(m, "sofa_s")
put("Living Sofa South", p, (21.6, 0.0, 17.0 - 3.62 / 2), rot=180)

m = sofa(8.6, 3.55, n_seat=3, throw=True, pillows=[
    (-2.5, PILLOW_G, 1.45, 1.40, 0.12), (-1.3, PILLOW_W, 1.40, 1.30, -0.10),
    (1.3, PILLOW_W, 1.40, 1.30, 0.10), (2.5, PILLOW_S, 1.45, 1.40, -0.13)])
p = save(m, "sofa_e")
put("Living Sofa East", p, (30.5 - 3.55 / 2, 0.0, 7.9), rot=270)

m = sofa(8.0, 3.55, n_seat=3, throw=True, pillows=[
    (-2.2, PILLOW_W, 1.45, 1.38, 0.11), (-1.0, PILLOW_G, 1.40, 1.32, -0.12),
    (1.6, PILLOW_S, 1.45, 1.38, 0.13)])
p = save(m, "sofa_w")
put("Living Sofa West", p, (2.55, 0.0, 11.6), rot=99)

# --------------------------------------------------------------- armchair
m = sofa(3.95, 3.45, arm_w=0.80, back_h=2.72, arm_h=2.10, n_seat=1, throw=True,
         pillows=[(0.0, PILLOW_W, 1.55, 1.45, 0.06)])
p = save(m, "armchair")
put("Living Armchair", p, (6.8, 0.0, 3.9), rot=34)

# --------------------------------------------------------------- ottomans
def ottoman(w, d, h=1.42):
    m = Model()
    m.add(box(w - 0.55, 0.26, d - 0.55), PLINTH, at=(0, 0, 0))
    m.add(rounded_box(w, h - 0.26, d, r=0.20, seg=4), UPH, at=(0, 0.26, 0))
    m.add(rounded_box(w - 0.16, 0.18, d - 0.16, r=0.16, seg=3), UPH2, at=(0, h - 0.20, 0))
    return m

p = save(ottoman(3.60, 2.30, h=1.36), "bench")
put("Living Bench Ottoman", p, (8.5, 0.0, 7.7), rot=6)

m = ottoman(3.85, 3.45, h=1.48)
m.add(box(1.15, 0.05, 0.85), Material("lap", "#c9ccce", roughness=0.35),
      at=(-0.4, 1.48, 0.25), rot_y=0.3)
m.add(box(0.42, 0.06, 0.24), Material("phone", "#1b1c20", roughness=0.3),
      at=(0.85, 1.48, -0.35), rot_y=-0.4)
p = save(m, "ottoman_sq")
put("Living Ottoman", p, (12.9, 0.0, 12.9), rot=4)

# --------------------------------------------------------------- coffee table
TW, TD, TH = 4.30, 2.25, 1.48
m = Model()
m.add(box(TW, 0.15, TD), WOODT, at=(0, TH - 0.15, 0))
for sx in (-1, 1):
    x = sx * (TW / 2 - 0.30)
    m.add(box(0.09, TH - 0.15, 0.09), METAL, at=(x, 0, TD / 2 - 0.22))
    m.add(box(0.09, TH - 0.15, 0.09), METAL, at=(x, 0, -TD / 2 + 0.22))
    m.add(box(0.07, 0.07, TD - 0.44), METAL, at=(x, TH - 0.22, 0))
    m.add(box(0.07, 1.55, 0.07), METAL, at=(x, 0.10, 0), rot_x=math.radians(58))
    m.add(box(0.07, 1.55, 0.07), METAL, at=(x, 0.10, 0), rot_x=math.radians(-58))
m.add(box(TW - 1.2, 0.07, 0.07), METAL, at=(0, 0.14, 0))
# white tray with a bright green ribbon, exactly as the photo
m.add(box(2.30, 0.10, 1.30), TRAY, at=(-0.35, TH, 0.02))
m.add(box(2.30, 0.16, 0.06), TRAY, at=(-0.35, TH, 0.66))
m.add(box(2.30, 0.16, 0.06), TRAY, at=(-0.35, TH, -0.62))
m.add(box(0.70, 0.30, 0.55), GREEN, at=(-0.35, TH + 0.06, 0.02), rot_y=0.4)
m.add(box(0.30, 0.06, 0.30), Material("cup", "#e6e2d8", roughness=0.5),
      at=(1.35, TH, -0.30))
p = save(m, "coffee")
put("Living Coffee Table", p, (13.4, 0.0, 9.3), rot=0)


# --------------------------------------------------------------- chaise ottoman
# The big rectangular ottoman that sits in front of the east sofa in photo f.
m = ottoman(5.30, 3.05, h=1.44)
m.add(sag_plane(2.4, 2.2, sag=0.06, nx=8, nz=8, edge_drop=0.34), THROW,
      at=(-1.1, 1.44, 0.15))
p = save(m, "chaise")
put("Living Chaise Ottoman", p, (23.8, 0.0, 8.6), rot=270)
