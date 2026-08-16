"""Round 5 soft goods -- the fine-scale gradient round 4 never had.

Round 4 matched every sd and the critic still called the room plastic, which was
right: on a CLEAN chaise-ottoman deck the round-4 render meters sd 8.6 / |d1|
0.77 / ratio 0.089 against photo f's sd 18-39 / |d1| 4.8-9.5 / ratio 0.26-0.32.

Two things were wrong with kit4's geometry and one with the whole approach.

  * kit4's `puff` parametrised a rounded box BY ITS NORMAL, which is degenerate
    on every flat face -- so each flat face of every cushion was a SINGLE quad
    split on one fixed diagonal.  That is the fold-card crease the critic saw,
    and it means the biggest, most camera-facing part of each cushion carried no
    tessellation at all.  `puff5` is a superellipsoid tessellated by ARC LENGTH
    to a cell size in feet, with the split diagonal alternating per cell.
  * `nub` was per-vertex white noise, so its feature size was whatever the
    tessellation happened to be.  `Grain` is a spatial field authored in feet.
  * AND: a first round-5 pass drove the whole texture budget through geometry --
    every cushion at 0.135 ft cells, displaced by that field, 2.9 MB of mesh.
    It rendered at sd 6.0 / |d1| 0.24, WORSE than round 4, because in this scene
    (one soft sun, near-uniform IBL, no bounce) a +/-15 deg normal wobble moves
    luminance by about +/-3 bytes.  Shading cannot carry fine texture here at
    any affordable cell size.  Measured, then abandoned.

So geometry now buys only what it is good at -- plump silhouette and mid-scale
form, at a cheap cell -- and the fine detail comes from a TILED baseColor
texture, which is what ROOM-BRIEF recommends and what nothing had implemented
(glb.py writes POSITION and NORMAL only; kit5 adds TEXCOORD_0 and an embedded
PNG).  A 64x64 seamless tile is 2.7 KB and puts detail at one render pixel.

Also this round, from the photographs:
  * ESOU (the south-east sofa) was #6d706c -- darker and greener than every
    other seat.  Photo f shows all three sofas in ONE cream: its own clean
    patches meter armchair 159.9 / NE ottoman 160.1 / SE sofa 168.1, an 8 byte
    spread, against round 4's 132 (SECT) to 185 (ESOU).  ESOU is now EAST
    verbatim and SECT is lifted towards the same family.
  * the rug runs UNDER the east sofas' fronts and under the sectional's chaise
    in photo f; round 4's stopped short of both.
  * the north-east sofa's fur throw hung 0.28 ft THROUGH the east wall.
  * photo f puts the tan throw over the NE sofa's BACK and shows the chaise
    ottoman clean -- no bolster, no drape.  Round 4 invented both, so removing
    them deletes a fabrication, not documented content.
"""
import math
import random

from kit5 import *
from kit5 import Part, Material, Model

rnd = random.Random(5051)

# ------------------------------------------------------- grain + weave tiles
GB = Grain(11, fine=0.42, fine_amp=0.013, coarse=1.05, coarse_amp=0.024)
GB2 = Grain(23, fine=0.42, fine_amp=0.013, coarse=1.05, coarse_amp=0.024)
GSH = Grain(31, fine=0.34, fine_amp=0.024, coarse=0.75, coarse_amp=0.040)
GFUR = Grain(41, fine=0.30, fine_amp=0.022, coarse=0.60, coarse_amp=0.034)
GRUG = Grain(53, fine=0.55, fine_amp=0.010, coarse=1.60, coarse_amp=0.020)

# repeat chosen so one texel lands on 1-2 render pixels in the reference pose
# (upholstery sits at 60-100 px/ft there, the rug at ~40).
T_BOUCLE = Tex(noise_tile(64, 0.68, 1.0, seed=7), 1.25, "boucle")
T_SHERPA = Tex(noise_tile(64, 0.60, 1.0, seed=17, blur=1), 1.05, "sherpa")
T_FUR = Tex(noise_tile(64, 0.64, 1.0, seed=27, streak=2), 1.10, "fur")
T_RUG = Tex(noise_tile(96, 0.66, 1.0, seed=37, streak=2), 2.90, "weave")
T_PIL = Tex(noise_tile(64, 0.70, 1.0, seed=47), 0.95, "pillow")

# every lift factor is SOLVED from its own tile's linear mean, not guessed
LB, LS, LF, LR, LP = (tex_lift(t) for t in
                      (T_BOUCLE, T_SHERPA, T_FUR, T_RUG, T_PIL))
print("  lift boucle %.3f sherpa %.3f fur %.3f rug %.3f pillow %.3f"
      % (LB, LS, LF, LR, LP))

# Geometry is form only now, so the cells go back up and the payload with them.
C_SEAT = 0.230
C_BACK = 0.250
C_ARM = 0.300
C_RAIL = 0.340
C_PILL = 0.260
UVR = T_BOUCLE.repeat


def lift(hexc, f):
    """Raise an albedo so a multiplying tile leaves the MEAN where it was.

    baseColorTexture multiplies baseColorFactor in LINEAR space, and a tile
    running 0.80-1.0 in sRGB has a linear mean well below 1, so painting the
    photo's colour straight on would darken every seat by ~20 bytes.
    """
    r, g, b = (int(hexc[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % tuple(min(255, int(round(c * f))) for c in (r, g, b))


DIM = 0.93          # albedo scale that lands the FOUR seats' mean on photo f's


def mats(tag, body, arm, seat, back, reveal, plinth):
    return dict(
        body=TMaterial("lr%sb" % tag, lift(body, LB * DIM), tex=T_BOUCLE, roughness=0.95),
        arm=TMaterial("lr%sa" % tag, lift(arm, LB * DIM), tex=T_BOUCLE, roughness=0.95),
        seat=TMaterial("lr%ss" % tag, lift(seat, LB * DIM), tex=T_BOUCLE, roughness=0.96),
        back=TMaterial("lr%sk" % tag, lift(back, LB * DIM), tex=T_BOUCLE, roughness=0.96),
        reveal=Material("lr%sr" % tag, reveal, roughness=0.99),
        plinth=Material("lr%sp" % tag, plinth, roughness=0.60))


SECT = mats("sect", "#78746b", "#827e74", "#8b877c", "#807b70", "#4e4b42", "#2f2f2c")
EAST = mats("east", "#84817b", "#8d8a85", "#95928c", "#89857f", "#55524e", "#232324")
ESOU = mats("esou", "#84817b", "#8d8a85", "#95928c", "#89857f", "#55524e", "#232324")
CHAI = mats("chai", "#837f78", "#8c8881", "#928e87", "#87837b", "#54514b", "#3a3833")
OTTO = mats("otto", "#8a8781", "#928f89", "#9a978f", "#8e8b85", "#585550", "#232324")

PIL_WAVE = TMaterial("lrpwave", lift("#8d8a85", LP), tex=T_PIL, roughness=0.95)
PIL_WAVE2 = TMaterial("lrpwave2", lift("#a5a29c", LP), tex=T_PIL, roughness=0.95)
PIL_CREAM = TMaterial("lrpcream", lift("#b9b4aa", LP), tex=T_PIL, roughness=0.96)
PIL_TICK = Material("lrptick", "#4c525c", roughness=0.95)
PIL_GREY = TMaterial("lrpgrey", lift("#7e7b74", LP), tex=T_PIL, roughness=0.97)
FUR = TMaterial("lrfur", lift("#9d9384", LF), tex=T_FUR, roughness=0.99)
FUR2 = TMaterial("lrfur2", lift("#8b8273", LF), tex=T_FUR, roughness=0.99)
THROW_G = TMaterial("lrthrowg", lift("#6a6a6e", LS), tex=T_SHERPA, roughness=0.99)
THROW_B = TMaterial("lrthrowb", lift("#63696f", LS), tex=T_SHERPA, roughness=0.99)
SHERPA = TMaterial("lrsherpa", lift("#b4b0a6", LS), tex=T_SHERPA, roughness=0.99)
SHERPA2 = TMaterial("lrsherpa2", lift("#aaa69c", LS), tex=T_SHERPA, roughness=0.99)


def stripes(m, at, w, h, rot_z, mat, d=0.46, r=0.20):
    for k in range(6):
        f = 0.26 + 0.106 * k
        dy = h * f
        prof = math.sqrt(max(0.0, 1.0 - (2.0 * f - 1.0) ** 2))
        dz = (d / 2 - r) + r * prof - 0.012
        ww = w * (0.94 - 0.30 * abs(2.0 * f - 1.0))
        m.add(box(ww, 0.048, 0.04), mat,
              at=(at[0] + 0.02, at[1] + dy, at[2] + dz),
              rot_z=rot_z, rot_x=-0.26)


def sofa(P, L, D, arm_w=0.92, back_h=2.84, seat_h=1.42, arm_h=2.16, n_seat=3,
         arm_r=0.38, pillows=(), throw=None, fur=False, ret_w=0.0, ret_d=0.0,
         ret_side=-1, seat_r=0.26, g=GB):
    m = Model()
    base_h = 0.30
    m.add(box(L - 0.30, base_h, D - 0.30), P["plinth"], at=(0, 0, 0))
    add5(m, tbox(L - 0.06, seat_h - 0.30, D - 0.06, repeat=UVR),
         P["body"], at=(0, base_h, 0))
    add5(m, puff5(L, back_h - base_h, 1.00, box_u=0.34, box_v=0.34,
                  cell=C_RAIL, grain=g, v0=0.30, uv_repeat=UVR), P["arm"],
         at=(0, base_h, -D / 2 + 0.50))
    for sx in (-1, 1):
        add5(m, puff5(arm_w, arm_h - base_h, D, r=arm_r, cell=C_ARM, grain=g,
                      v0=0.32, uv_repeat=UVR), P["arm"],
             at=(sx * (L / 2 - arm_w / 2), base_h, 0))
        m.add(box(0.05, arm_h - base_h - 0.40, D - 0.55), P["reveal"],
              at=(sx * (L / 2 - arm_w), base_h + 0.18, 0.06))
    inner = L - 2 * arm_w
    cw = inner / n_seat
    for i in range(n_seat + 1):
        m.add(box(0.06, 0.46, D - 1.25), P["reveal"],
              at=(-inner / 2 + cw * i, seat_h - 0.24, 0.24))
    for i in range(n_seat):
        cx = -inner / 2 + cw * (i + 0.5)
        add5(m, puff5(cw - 0.09, 0.62, D - 1.02, r=seat_r, cell=C_SEAT, grain=g,
                      v0=0.30, uv_repeat=UVR), P["seat"],
             at=(cx, seat_h - 0.24, 0.22))
        add5(m, puff5(cw - 0.10, 1.34, 0.74, r=0.28, cell=C_BACK, grain=g,
                      uv_repeat=UVR), P["back"],
             at=(cx, seat_h + 0.16, -D / 2 + 0.82), rot_x=-0.13)
    if ret_w:
        rx = ret_side * (L / 2 - ret_w / 2)
        rz = D / 2 + ret_d / 2
        m.add(box(ret_w - 0.3, base_h, ret_d - 0.2), P["plinth"], at=(rx, 0, rz))
        add5(m, tbox(ret_w - 0.06, seat_h - 0.30, ret_d + 0.04, repeat=UVR),
             P["body"], at=(rx, base_h, rz))
        add5(m, puff5(ret_w - 0.12, 0.58, ret_d - 0.14, r=0.24, cell=C_SEAT,
                      grain=g, v0=0.30, uv_repeat=UVR), P["seat"],
             at=(rx, seat_h - 0.22, rz - 0.02))
        add5(m, puff5(arm_w, arm_h - base_h, ret_d + 0.06, r=arm_r, cell=C_ARM,
                      grain=g, v0=0.32, uv_repeat=UVR), P["arm"],
             at=(ret_side * (L / 2 - arm_w / 2), base_h, rz))
    for p in pillows:
        (px, mat, w, h, tilt) = p[:5]
        stripe = p[5] if len(p) > 5 else None
        at = (px, seat_h + 0.02, -D / 2 + 1.22)
        add5(m, puff5(w, h, 0.46, r=0.20, cell=C_PILL, grain=GB2,
                      uv_repeat=T_PIL.repeat), mat,
             at=at, rot_z=tilt, rot_x=-0.26)
        if stripe:
            stripes(m, at, w, h, tilt, stripe, d=0.46, r=0.20)
    if fur:
        # photo f: a tan faux-fur throw rolled along the back rail and falling
        # down the OUTSIDE of it.  Kept short so it cannot reach the wall.
        add5(m, bolster5(L * 0.80, 0.20, cell=0.17, grain=GFUR,
                         uv_repeat=T_FUR.repeat), FUR,
             at=(L * 0.06, back_h - 0.06, -D / 2 + 0.40), rot_x=0.06)
        add5(m, drape5(L * 0.78, 0.80, sag=0.05, edge_drop=0.26, cell=0.17,
                       grain=GFUR, uv_repeat=T_FUR.repeat), FUR2,
             at=(L * 0.06, back_h - 0.16, -D / 2 + 0.28), rot_x=0.10)
    if throw:
        (tx, tz, mat) = throw
        add5(m, drape5(1.55, 2.55, sag=0.06, edge_drop=0.95, cell=0.18,
                       grain=GSH, uv_repeat=T_SHERPA.repeat), mat,
             at=(tx, arm_h - 0.04, 0.10 + tz), rot_z=0.05)
        add5(m, drape5(1.45, 1.30, sag=0.07, edge_drop=0.30, cell=0.18,
                       grain=GSH, uv_repeat=T_SHERPA.repeat), mat,
             at=(tx + 0.35, seat_h + 0.22, 0.75 + tz), rot_y=0.22)
    return m


def anchor_capped(name, m, glb, model_pt, room_pt, rot_deg, cap_x=None):
    """put_anchor, but pulled back so the piece's MEASURED bbox cannot cross a
    wall.  Round 4's NE sofa reached x 20.77 against a wall at 20.49 because the
    anchor was its back RAIL and the fur throw hung behind it."""
    lo, hi = m.bounds()
    cx, cz = (lo[0] + hi[0]) / 2, (lo[2] + hi[2]) / 2
    th = math.radians(rot_deg)
    dx, dz = model_pt[0] - cx, model_pt[1] - cz
    wx = dx * math.cos(th) + dz * math.sin(th)
    wz = -dx * math.sin(th) + dz * math.cos(th)
    px, pz = room_pt[0] - wx, room_pt[1] - wz
    if cap_x is not None:
        half = (hi[2] - lo[2]) / 2 if rot_deg % 180 else (hi[0] - lo[0]) / 2
        px = min(px, cap_x - half)
    put(name, glb, (px, lo[1], pz), rot_deg)
    return px


# ============================================================== ITEM 5 the rug
# p5_rug.png at native resolution: a flatweave whose grain is 2-4 px of light
# and dark slub.  Round 4 wrote it as 1350 unshared streak quads (5400 verts for
# 2700 triangles) and still metered |d1| 3.29 / sd 9.9.  The streaks are now a
# streaked tile at 0.023 ft a texel, and the mesh is a shared-vertex grid that
# only has to carry the lie of the pile.
# Extended east and south: photo f runs the rug under both east sofas' fronts
# and under the sectional's chaise return.
RX, RZ, RL, RDp, RT = 11.90, 9.70, 14.40, 12.00, 0.075
RUGM = TMaterial("lrrug5", lift("#5f5c55", LR), tex=T_RUG, roughness=0.99)
RUGE = Material("lrruge", "#504c46", roughness=0.99)

m = Model()
m.add(box(RL + 0.16, RT * 0.60, RDp + 0.16), RUGE, at=(0, 0, 0))     # bound edge
add5(m, grid5(RL, RDp, cell=0.30, grain=GRUG, y=RT, uv_repeat=T_RUG.repeat),
     RUGM)
put("Living Floor Rug", save5(m, "rug5"), (RX, 0.004, RZ))

# ============================================================ south sectional
SD, SRD = 3.55, 2.60
m = sofa(SECT, 7.60, SD, n_seat=3, ret_w=2.70, ret_d=SRD, ret_side=-1,
         throw=(-0.6, 0.0, THROW_G), pillows=[
             (-2.6, PIL_CREAM, 1.50, 1.42, 0.10), (-1.4, PIL_GREY, 1.44, 1.34, -0.14),
             (0.2, PIL_WAVE, 1.46, 1.36, 0.08), (1.5, PIL_GREY, 1.44, 1.34, 0.13),
             (2.6, PIL_CREAM, 1.50, 1.42, -0.09)])
add5(m, drape5(2.2, 1.9, sag=0.12, edge_drop=0.48, cell=0.18, grain=GSH,
               uv_repeat=T_SHERPA.repeat), THROW_B, at=(2.1, 1.50, 2.5))
put_anchor("Living Sofa South", m, save5(m, "sofa_s5"),
           (0.0, -SD / 2), (4.35, 16.90), 180)

# ================================================================= east sofas
ED = 3.55
m = sofa(EAST, 6.20, ED, arm_w=0.92, arm_r=0.30, back_h=2.84, n_seat=3, fur=True,
         pillows=[(-1.95, PIL_WAVE, 1.44, 1.38, 0.12),
                  (-0.35, PIL_WAVE2, 1.40, 1.32, -0.10),
                  (1.35, PIL_WAVE, 1.44, 1.38, 0.09)])
anchor_capped("Living Sofa East", m, save5(m, "sofa_e5"),
              (0.0, -ED / 2), (20.47, 7.20), 270, cap_x=20.44)

ESD = 3.95
m = sofa(ESOU, 6.40, ESD, arm_w=1.15, arm_r=0.52, back_h=3.05, arm_h=2.30,
         n_seat=2, seat_r=0.30, g=GB2, pillows=[
             (-1.55, PIL_CREAM, 1.62, 1.52, 0.15, PIL_TICK),
             (0.25, PIL_CREAM, 1.54, 1.44, -0.11, PIL_TICK),
             (1.75, PIL_GREY, 1.48, 1.38, 0.08)])
add5(m, bolster5(2.55, 0.44, cell=0.19, grain=GB, uv_repeat=T_PIL.repeat),
     PIL_CREAM, at=(-0.55, 1.86, -0.30), rot_y=0.20, rot_z=0.10)
anchor_capped("Living Sofa East South", m, save5(m, "sofa_es5"),
              (0.0, -ESD / 2), (20.47, 13.65), 270, cap_x=20.44)

# ==================================================================== armchair
m = sofa(CHAI, 5.00, 4.00, arm_w=0.94, arm_r=0.44, back_h=2.78, arm_h=2.14,
         n_seat=1, seat_r=0.30)
add5(m, puff5(2.55, 0.62, 1.55, r=0.28, cell=0.22, grain=GSH,
              uv_repeat=T_SHERPA.repeat), SHERPA, at=(0.02, 1.62, -1.02),
     rot_x=-0.30)
add5(m, puff5(2.20, 0.44, 1.30, r=0.20, cell=0.22, grain=GSH,
              uv_repeat=T_SHERPA.repeat), SHERPA2, at=(0.02, 2.42, -1.30),
     rot_x=0.10)
add5(m, puff5(0.85, 0.52, 2.90, r=0.24, cell=0.22, grain=GSH,
              uv_repeat=T_SHERPA.repeat), SHERPA, at=(-1.66, 2.02, 0.10),
     rot_z=0.10)
add5(m, drape5(0.95, 1.35, sag=0.05, edge_drop=0.60, cell=0.18, grain=GSH,
               uv_repeat=T_SHERPA.repeat), SHERPA2, at=(-1.72, 2.02, 0.60))
put_anchor("Living Armchair", m, save5(m, "armchair5"), (0.0, -2.0), (1.05, 7.60), 72)


# ==================================================================== ottomans
def ottoman(P, w, d, h=1.42, g=GB):
    m = Model()
    m.add(box(w - 0.34, 0.30, d - 0.34), P["plinth"], at=(0, 0, 0))
    add5(m, puff5(w, h - 0.30, d, box_u=0.32, box_v=0.33, cell=C_SEAT, grain=g,
                  v0=0.30, uv_repeat=UVR), P["body"], at=(0, 0.30, 0))
    return m


m = ottoman(OTTO, 4.40, 2.50, h=1.40)
m.add(box(4.44, 0.05, 2.54), OTTO["reveal"], at=(0, 1.10, 0))
m.add(box(1.12, 0.05, 0.82), Material("lrlap", "#8b8d90", roughness=0.35),
      at=(-0.5, 1.40, 0.10), rot_y=0.28)
m.add(box(0.40, 0.05, 0.22), Material("lrdark", "#1c1d21", roughness=0.4),
      at=(0.9, 1.40, -0.30), rot_y=-0.35)
add5(m, drape5(1.5, 1.1, sag=0.07, edge_drop=0.26, cell=0.18, grain=GSH,
               uv_repeat=T_SHERPA.repeat), THROW_B, at=(1.3, 1.42, 0.42))
put("Living Ottoman", save5(m, "ottoman5"), (7.70, 0.0, 8.40), rot=3)

# photo f shows this ottoman CLEAN: the tan throw is on the NE sofa's back, not
# here.  Round 4's rolled bolster + drape on it were an invention, so removing
# them deletes a fabrication, not documented content.
m = ottoman(EAST, 4.20, 2.60, h=1.44, g=GB2)
m.add(box(4.24, 0.05, 2.64), EAST["reveal"], at=(0, 1.14, 0))
put("Living Chaise Ottoman", save5(m, "chaise5"), (14.70, 0.0, 7.20), rot=270)

# ================================================================ coffee table
WOODT = Material("lrwoodt", "#4c4945", roughness=0.7)
METAL = Material("lrmetal", "#17181a", roughness=0.45, metallic=0.3)
TRAY = Material("lrtray", "#a9a7a2", roughness=0.4)
GREEN = Material("lrgreen", "#43793f", roughness=0.8)
PAPER = Material("lrpaper", "#9d9a93", roughness=0.9)
DARK = Material("lrdark", "#1c1d21", roughness=0.4)
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
put("Living Coffee Table", save5(m, "coffee5"), (11.80, 0.0, 11.00), rot=2)
