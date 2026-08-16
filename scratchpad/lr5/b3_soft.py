"""Round 3 soft goods.

Critic items 3 (the missing second east sofa + a chair-and-a-half armchair),
4 (the chaise ottoman buried in the east sofa), 6 (every seat one greige) and
7 (the rug reading as a tiled floor).
"""
import math
import random

from kit3 import *
from kit3 import Part, Material, Model

rnd = random.Random(3031)


def mats(tag, body, arm, seat, back, reveal, plinth):
    return dict(
        body=Material("lr%sb" % tag, body, roughness=0.95),
        arm=Material("lr%sa" % tag, arm, roughness=0.95),
        seat=Material("lr%ss" % tag, seat, roughness=0.96),
        back=Material("lr%sk" % tag, back, roughness=0.96),
        reveal=Material("lr%sr" % tag, reveal, roughness=0.99),
        plinth=Material("lr%sp" % tag, plinth, roughness=0.60))


# ITEM 6.  Round 2 gave sectional / east sofa / ottomans / chaise / armchair one
# greige, so the whole east half read as one continuous mass and the east sofa
# read as a mattress.  Photo f metered: armchair 188, SE sofa body 146, east
# sofa back 126 -- three clearly separate values, plus a warm sectional.  Every
# piece now has its own family, and each family still carries the internal
# value steps that stand in for the shadows this renderer does not draw.
SECT = mats("sect", "#6d6960", "#797569", "#827d72", "#767165", "#454239", "#2f2f2c")
EAST = mats("east", "#84817b", "#8d8a85", "#95928c", "#89857f", "#55524e", "#232324")
ESOU = mats("esou", "#6d706c", "#767974", "#7e817c", "#727570", "#454844", "#232324")
CHAI = mats("chai", "#837f78", "#8c8881", "#928e87", "#87837b", "#54514b", "#3a3833")
OTTO = mats("otto", "#8a8781", "#928f89", "#9a978f", "#8e8b85", "#585550", "#232324")

PIL_WAVE = Material("lrpwave", "#8d8a85", roughness=0.95)
PIL_WAVE2 = Material("lrpwave2", "#a5a29c", roughness=0.95)
PIL_CREAM = Material("lrpcream", "#b9b4aa", roughness=0.96)
PIL_TICK = Material("lrptick", "#565d68", roughness=0.95)
PIL_GREY = Material("lrpgrey", "#7e7b74", roughness=0.97)
FUR = Material("lrfur", "#9d9384", roughness=0.99)
FUR2 = Material("lrfur2", "#8b8273", roughness=0.99)
THROW_G = Material("lrthrowg", "#6a6a6e", roughness=0.99)
THROW_B = Material("lrthrowb", "#63696f", roughness=0.99)
SHERPA = Material("lrsherpa", "#a8a49c", roughness=0.99)

# Tight spread on purpose: at +/-6% the 0.18 ft mosaic merged into ~1 ft
# patches and read as a light/dark patchwork (ROOM-BRIEF round-2 lesson 3:
# overshooting is not closer).  +/-3% reads as flatweave grain.
RUG = [Material("lrrugA", "#68655e", roughness=0.99),
       Material("lrrugB", "#66635c", roughness=0.99),
       Material("lrrugC", "#6a675f", roughness=0.99),
       Material("lrrugD", "#65625b", roughness=0.99),
       Material("lrrugE", "#67645d", roughness=0.99)]
RUGE = Material("lrruge", "#5a5750", roughness=0.99)
WOODT = Material("lrwoodt", "#4c4945", roughness=0.7)
METAL = Material("lrmetal", "#17181a", roughness=0.45, metallic=0.3)
TRAY = Material("lrtray", "#a9a7a2", roughness=0.4)
GREEN = Material("lrgreen", "#43793f", roughness=0.8)
PAPER = Material("lrpaper", "#9d9a93", roughness=0.9)
DARK = Material("lrdark", "#1c1d21", roughness=0.4)


def striped(m, w, h, at, rot_z, base, stripe):
    """A ticking-stripe pillow: plain body, thin stripe plates on the top half."""
    m.add(rounded_box(w, h, 0.38, r=0.13, seg=3), base, at=at,
          rot_z=rot_z, rot_x=-0.26)
    for k in range(5):
        m.add(box(w * 0.86, 0.055, 0.14), stripe,
              at=(at[0] + 0.02, at[1] + h * (0.52 + 0.085 * k), at[2] + 0.15),
              rot_z=rot_z, rot_x=-0.26)


def sofa(P, L, D, arm_w=0.92, back_h=2.84, seat_h=1.42, arm_h=2.16, n_seat=3,
         pillows=(), throw=None, fur=False, ret_w=0.0, ret_d=0.0, ret_side=-1):
    """Sofa authored facing +z (back at -z), on a visible dark plinth."""
    m = Model()
    base_h = 0.30
    m.add(box(L - 0.30, base_h, D - 0.30), P["plinth"], at=(0, 0, 0))
    m.add(rounded_box(L, seat_h - 0.24, D, r=0.18, seg=3), P["body"], at=(0, base_h, 0))
    m.add(rounded_box(L, back_h - base_h, 0.92, r=0.16, seg=3), P["arm"],
          at=(0, base_h, -D / 2 + 0.46))
    for sx in (-1, 1):
        m.add(rounded_box(arm_w, arm_h - base_h, D, r=0.34, seg=4), P["arm"],
              at=(sx * (L / 2 - arm_w / 2), base_h, 0))
        m.add(box(0.05, arm_h - base_h - 0.30, D - 0.30), P["reveal"],
              at=(sx * (L / 2 - arm_w), base_h + 0.15, 0.06))
    inner = L - 2 * arm_w
    cw = inner / n_seat
    for i in range(n_seat + 1):
        m.add(box(0.07, 0.58, D - 1.0), P["reveal"],
              at=(-inner / 2 + cw * i, seat_h - 0.20, 0.22))
    for i in range(n_seat):
        cx = -inner / 2 + cw * (i + 0.5)
        m.add(rounded_box(cw - 0.10, 0.52, D - 1.05, r=0.16, seg=3), P["seat"],
              at=(cx, seat_h - 0.16, 0.22))
        m.add(rounded_box(cw - 0.12, 1.22, 0.62, r=0.18, seg=3), P["back"],
              at=(cx, seat_h + 0.30, -D / 2 + 0.78), rot_x=-0.13)
    if ret_w:
        rx = ret_side * (L / 2 - ret_w / 2)
        rz = D / 2 + ret_d / 2
        m.add(box(ret_w - 0.3, base_h, ret_d - 0.2), P["plinth"], at=(rx, 0, rz))
        m.add(rounded_box(ret_w, seat_h - 0.24, ret_d + 0.1, r=0.18, seg=3), P["body"],
              at=(rx, base_h, rz))
        m.add(rounded_box(ret_w - 0.14, 0.50, ret_d - 0.16, r=0.16, seg=3), P["seat"],
              at=(rx, seat_h - 0.16, rz - 0.02))
        m.add(rounded_box(arm_w, arm_h - base_h, ret_d + 0.1, r=0.34, seg=4), P["arm"],
              at=(ret_side * (L / 2 - arm_w / 2), base_h, rz))
    for p in pillows:
        (px, mat, w, h, tilt) = p[:5]
        stripe = p[5] if len(p) > 5 else None
        at = (px, seat_h + 0.20, -D / 2 + 1.26)
        if stripe:
            striped(m, w, h, at, tilt, mat, stripe)
        else:
            m.add(rounded_box(w, h, 0.38, r=0.13, seg=3), mat, at=at,
                  rot_z=tilt, rot_x=-0.26)
    if fur:
        # faux-fur throw laid the full length of the back rail (photo f)
        m.add(sag_plane(L * 0.74, 1.15, sag=0.03, nx=14, nz=5, edge_drop=0.26), FUR,
              at=(L * 0.10, back_h - 0.02, -D / 2 + 0.48), rot_x=0.05)
        m.add(sag_plane(L * 0.70, 0.80, sag=0.02, nx=13, nz=4, edge_drop=0.14), FUR2,
              at=(L * 0.10, back_h + 0.05, -D / 2 + 0.38))
    if throw:
        (tx, tz, mat) = throw
        m.add(sag_plane(2.6, 2.4, sag=0.06, nx=9, nz=9, edge_drop=0.45), mat,
              at=(tx, back_h - 0.06, -D / 2 + 1.05 + tz), rot_x=0.08)
        m.add(sag_plane(2.5, 1.5, sag=0.05, nx=8, nz=6, edge_drop=0.22), mat,
              at=(tx, seat_h + 0.26, 0.55 + tz))
    return m


# ------------------------------------------------------------------ rug
# ITEM 7.  Round 2 stood 76 raised ribs on the pile; at render scale they
# aliased into a ~0.7 ft grid with grout lines -- a tiled floor across 43% of
# the room.  The pile is now flat, and its texture is a random 0.28 ft mosaic
# of four values within 8% of each other, which reads as flatweave noise rather
# than as a grid.  Photo f meters the rug at 144-150 mean / sd 25.
RX, RZ, RL, RDp, RT = 11.20, 9.80, 13.20, 11.00, 0.075
m = Model()
m.add(box(RL, RT, RDp), RUG[1], at=(0, 0, 0))
m.add(box(RL + 0.14, RT * 0.55, RDp + 0.14), RUGE, at=(0, 0, 0))   # bound edge
CELL = 0.18
nxc, nzc = int(RL / CELL), int(RDp / CELL)
for iz in range(nzc):
    z = -RDp / 2 + RDp * (iz + 0.5) / nzc
    for ix in range(nxc):
        x = -RL / 2 + RL * (ix + 0.5) / nxc
        m.add(box(RL / nxc, 0.004, RDp / nzc), RUG[rnd.randrange(5)], at=(x, RT, z))
put("Living Floor Rug", save(m, "rug3"), (RX, 0.004, RZ))

# ------------------------------------------------------------ south sectional
SD, SRD = 3.55, 2.60
m = sofa(SECT, 7.60, SD, n_seat=3, ret_w=2.70, ret_d=SRD, ret_side=-1,
         throw=(-0.6, 0.0, THROW_G), pillows=[
             (-2.6, PIL_CREAM, 1.50, 1.42, 0.10), (-1.4, PIL_GREY, 1.44, 1.34, -0.14),
             (0.2, PIL_WAVE, 1.46, 1.36, 0.08), (1.5, PIL_GREY, 1.44, 1.34, 0.13),
             (2.6, PIL_CREAM, 1.50, 1.42, -0.09)])
m.add(sag_plane(2.2, 1.9, sag=0.10, nx=8, nz=8, edge_drop=0.42), THROW_B,
      at=(2.1, 1.52, 2.5))
put_anchor("Living Sofa South", m, save(m, "sofa_s3"),
           (0.0, -SD / 2), (4.35, 16.94), 180)

# --------------------------------------------------------------- east sofas
# ITEM 3.  Photo f shows TWO separate sofas down the east side -- different
# pillow sets, separate black plinths, a band of rug between them.  Round 2
# collapsed them into one 8.4 ft sofa and left the south-east quadrant empty.
# The east wall is 16.96 ft and the window occupies z 1.04..4.02, so the pair
# is 5.9 ft each with a 0.95 ft band of rug between (see the report).
ED = 3.62
m = sofa(EAST, 5.90, ED, n_seat=3, fur=True, pillows=[
    (-1.85, PIL_WAVE, 1.44, 1.38, 0.12), (-0.30, PIL_WAVE2, 1.40, 1.32, -0.10),
    (1.30, PIL_WAVE, 1.44, 1.38, 0.09)])
put_anchor("Living Sofa East", m, save(m, "sofa_e3"),
           (0.0, -ED / 2), (RW - 0.02, 7.05), 270)

m = sofa(ESOU, 5.90, ED, n_seat=3, throw=(1.35, 0.0, THROW_B), pillows=[
    (-1.85, PIL_CREAM, 1.46, 1.40, 0.13, PIL_TICK),
    (-0.30, PIL_CREAM, 1.42, 1.34, -0.09, PIL_TICK),
    (1.30, PIL_GREY, 1.42, 1.34, 0.07)])
put_anchor("Living Sofa East South", m, save(m, "sofa_es3"),
           (0.0, -ED / 2), (RW - 0.02, 13.90), 270)

# ------------------------------------------------------------------ armchair
# ITEM 3 (part).  Photo f's chair is a chair-and-a-half: it is as wide as it is
# deep and swallows a whole sherpa throw plus a body pillow.  3.60 ft was a
# dining-scale accent chair.
m = sofa(CHAI, 5.00, 4.00, arm_w=0.94, back_h=2.78, arm_h=2.14, n_seat=1,
         pillows=[(0.0, SHERPA, 2.30, 1.72, 0.03)])
m.add(sag_plane(2.6, 1.5, sag=0.04, nx=9, nz=6, edge_drop=0.28), SHERPA,
      at=(0.10, 2.72, -1.42), rot_x=0.06)
put_anchor("Living Armchair", m, save(m, "armchair3"), (0.0, -2.0), (1.05, 7.60), 72)


# ------------------------------------------------------------------ ottomans
def ottoman(P, w, d, h=1.42):
    m = Model()
    m.add(box(w - 0.34, 0.30, d - 0.34), P["plinth"], at=(0, 0, 0))
    m.add(rounded_box(w, h - 0.30, d, r=0.20, seg=4), P["body"], at=(0, 0.30, 0))
    m.add(rounded_box(w - 0.16, 0.18, d - 0.16, r=0.16, seg=3), P["seat"],
          at=(0, h - 0.20, 0))
    return m


m = ottoman(OTTO, 4.40, 2.50, h=1.40)
m.add(box(4.44, 0.05, 2.54), OTTO["reveal"], at=(0, 1.12, 0))       # piped seam
m.add(box(1.12, 0.05, 0.82), Material("lrlap", "#8b8d90", roughness=0.35),
      at=(-0.5, 1.40, 0.10), rot_y=0.28)
m.add(box(0.40, 0.05, 0.22), DARK, at=(0.9, 1.40, -0.30), rot_y=-0.35)
m.add(sag_plane(1.5, 1.1, sag=0.05, nx=6, nz=6, edge_drop=0.22), THROW_B,
      at=(1.3, 1.42, 0.42))
put("Living Ottoman", save(m, "ottoman3"), (7.70, 0.0, 8.40), rot=3)

# ITEM 4.  The chaise ottoman ran to x 17.3 against the east sofa's front rail
# at 16.27 -- its corner was buried a foot inside the sofa seat.  The sofa's
# front rail is now at x 16.85 and the ottoman ends at 16.00: 0.85 ft of rug.
m = ottoman(EAST, 4.20, 2.60, h=1.44)
m.add(box(4.24, 0.05, 2.64), EAST["reveal"], at=(0, 1.16, 0))       # piped seam
m.add(sag_plane(2.1, 2.0, sag=0.06, nx=8, nz=8, edge_drop=0.34), FUR2,
      at=(-0.9, 1.44, 0.10))
put("Living Chaise Ottoman", save(m, "chaise3"), (14.70, 0.0, 7.05), rot=270)

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
put("Living Coffee Table", save(m, "coffee3"), (11.80, 0.0, 11.00), rot=2)
