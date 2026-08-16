"""Round 4 soft goods.

Round 3's inventory, scale and the five seat VALUES were adjudicated correct,
so none of that moves.  What was still missing is everything that makes a
photograph of this room read as fabric:

ITEM 8  every upholstered part in rounds 1-3 was a `rounded_box`, which is
        rounded on its four VERTICAL edges only.  Seen from the reference pose
        and from above, that is a planar chamfered slab.  Every cushion, arm,
        back rail and pillow is now a `puff` (kit4) -- rounded on all three
        axes -- so the silhouettes are plump, as every piece in photo f is.

ITEM 3  photo f shows a sherpa throw swallowing the armchair, a big cream body
        pillow on the south-east sofa, a tan throw down the north-east sofa's
        back, and a visible boucle weave on all of them.  The weave is the
        `nub` argument: it offsets each puff vertex along its own radius, and
        with smooth normals that is a soft shading mottle at ~0.2 ft -- photo f
        meters the upholstery at sd 11-35, the round-3 render at ~2.

ITEM 4  the two east sofas were the same mesh mirrored with a 0.95 ft slot
        between them.  They are now different pieces -- 6.20 x 3.55 with square
        arms and 3 seats to the north, 6.40 x 3.95 with rolled arms and 2 wide
        seats to the south -- and the slot is closed to 0.15 ft.  Their accent
        pillows were flat wedges standing proud of the seats; they are now
        plump and sunk into the seat/back junction.

ITEM 5  the rug.  Round 2 overshot with raised ribs, round 3 undershot with
        flat +/-1.5% panels (clean lit patch: sd 2.0 against photo f's 20-25),
        and the round-3 file was 4.5 MB -- three times the whole ROOM budget --
        because it was written as 4453 flat-shaded boxes.  It is now a
        smooth-quad mottle plus a crosshatch of streaks, which is what photo
        f's flatweave actually looks like close up (photo_rugcrop.png).
"""
import math
import random

from kit4 import *
from kit4 import Part, Material, Model

rnd = random.Random(4041)


def mats(tag, body, arm, seat, back, reveal, plinth):
    return dict(
        body=Material("lr%sb" % tag, body, roughness=0.95),
        arm=Material("lr%sa" % tag, arm, roughness=0.95),
        seat=Material("lr%ss" % tag, seat, roughness=0.96),
        back=Material("lr%sk" % tag, back, roughness=0.96),
        reveal=Material("lr%sr" % tag, reveal, roughness=0.99),
        plinth=Material("lr%sp" % tag, plinth, roughness=0.60))


# Round 3's five families, unchanged: the critic confirmed the five seat values
# are in the right rank order against photo f's 126 / 146 / 166 / 188.
SECT = mats("sect", "#6d6960", "#797569", "#827d72", "#767165", "#454239", "#2f2f2c")
EAST = mats("east", "#84817b", "#8d8a85", "#95928c", "#89857f", "#55524e", "#232324")
ESOU = mats("esou", "#6d706c", "#767974", "#7e817c", "#727570", "#454844", "#232324")
CHAI = mats("chai", "#837f78", "#8c8881", "#928e87", "#87837b", "#54514b", "#3a3833")
OTTO = mats("otto", "#8a8781", "#928f89", "#9a978f", "#8e8b85", "#585550", "#232324")

PIL_WAVE = Material("lrpwave", "#8d8a85", roughness=0.95)
PIL_WAVE2 = Material("lrpwave2", "#a5a29c", roughness=0.95)
PIL_CREAM = Material("lrpcream", "#b9b4aa", roughness=0.96)
PIL_TICK = Material("lrptick", "#4c525c", roughness=0.95)
PIL_GREY = Material("lrpgrey", "#7e7b74", roughness=0.97)
FUR = Material("lrfur", "#9d9384", roughness=0.99)
FUR2 = Material("lrfur2", "#8b8273", roughness=0.99)
THROW_G = Material("lrthrowg", "#6a6a6e", roughness=0.99)
THROW_B = Material("lrthrowb", "#63696f", roughness=0.99)
# Photo f meters the sherpa throw on the armchair at 199.6 -- the brightest
# soft thing in the room, brighter than the chair it lies on (176.6).
SHERPA = Material("lrsherpa", "#b4b0a6", roughness=0.99)
SHERPA2 = Material("lrsherpa2", "#aaa69c", roughness=0.99)

NUB = 0.021          # boucle: ~0.25 in of radial wobble per puff vertex


def cushion(w, h, d, r, mat=None, nub=NUB):
    return puff(w, h, d, r=r, seg=13, rings=6, nub=nub, rnd=rnd)


def stripes(m, at, w, h, rot_z, mat, d=0.46, r=0.20):
    """Ticking stripes that lie ON the pillow instead of hovering off it.

    Round 4a placed them all at a fixed z, but a puff narrows towards its top,
    so the upper stripes floated in front of the pillow and read as venetian
    blinds.  dz now follows the puff's own elliptical profile.
    """
    for k in range(6):
        f = 0.26 + 0.106 * k                      # fraction of the pillow height
        dy = h * f
        prof = math.sqrt(max(0.0, 1.0 - (2.0 * f - 1.0) ** 2))
        dz = (d / 2 - r) + r * prof - 0.012
        ww = w * (0.94 - 0.30 * abs(2.0 * f - 1.0))
        m.add(box(ww, 0.048, 0.04), mat,
              at=(at[0] + 0.02, at[1] + dy, at[2] + dz),
              rot_z=rot_z, rot_x=-0.26)


def sofa(P, L, D, arm_w=0.92, back_h=2.84, seat_h=1.42, arm_h=2.16, n_seat=3,
         arm_r=0.38, pillows=(), throw=None, fur=False, ret_w=0.0, ret_d=0.0,
         ret_side=-1, seat_r=0.26):
    """Sofa authored facing +z (back at -z), on a visible dark plinth.

    Every soft part is a puff; only the plinth, the frame rail and the seams
    stay boxy, which is what the photographs show too.
    """
    m = Model()
    base_h = 0.30
    m.add(box(L - 0.30, base_h, D - 0.30), P["plinth"], at=(0, 0, 0))
    m.add(rounded_box(L - 0.06, seat_h - 0.30, D - 0.06, r=0.22, seg=3),
          P["body"], at=(0, base_h, 0))
    # plump back rail
    m.add(cushion(L, back_h - base_h, 1.00, 0.42), P["arm"],
          at=(0, base_h, -D / 2 + 0.50))
    for sx in (-1, 1):
        m.add(cushion(arm_w, arm_h - base_h, D, arm_r), P["arm"],
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
        m.add(cushion(cw - 0.09, 0.62, D - 1.02, seat_r), P["seat"],
              at=(cx, seat_h - 0.24, 0.22))
        m.add(cushion(cw - 0.10, 1.34, 0.74, 0.28), P["back"],
              at=(cx, seat_h + 0.16, -D / 2 + 0.82), rot_x=-0.13)
    if ret_w:
        rx = ret_side * (L / 2 - ret_w / 2)
        rz = D / 2 + ret_d / 2
        m.add(box(ret_w - 0.3, base_h, ret_d - 0.2), P["plinth"], at=(rx, 0, rz))
        m.add(rounded_box(ret_w - 0.06, seat_h - 0.30, ret_d + 0.04, r=0.20, seg=3),
              P["body"], at=(rx, base_h, rz))
        m.add(cushion(ret_w - 0.12, 0.58, ret_d - 0.14, 0.24), P["seat"],
              at=(rx, seat_h - 0.22, rz - 0.02))
        m.add(cushion(arm_w, arm_h - base_h, ret_d + 0.06, arm_r), P["arm"],
              at=(ret_side * (L / 2 - arm_w / 2), base_h, rz))
    for p in pillows:
        (px, mat, w, h, tilt) = p[:5]
        stripe = p[5] if len(p) > 5 else None
        # sunk into the seat/back junction, not standing on the deck
        at = (px, seat_h + 0.02, -D / 2 + 1.22)
        m.add(cushion(w, h, 0.46, 0.20), mat, at=at, rot_z=tilt, rot_x=-0.26)
        if stripe:
            stripes(m, at, w, h, tilt, stripe, d=0.46, r=0.20)
    if fur:
        # photo f: a tan faux-fur throw ROLLED along the whole back rail, then
        # falling down the outside.  Round 3 drew two flat sag planes and the
        # critic never saw a throw at all.
        m.add(bolster(L * 0.80, 0.20, seg=12, rings=6, nub=0.045, rnd=rnd), FUR,
              at=(L * 0.06, back_h - 0.06, -D / 2 + 0.36), rot_x=0.06)
        m.add(sag_plane(L * 0.78, 0.95, sag=0.05, nx=13, nz=4, edge_drop=0.30), FUR2,
              at=(L * 0.06, back_h - 0.16, -D / 2 + 0.20), rot_x=0.10)
    if throw:
        (tx, tz, mat) = throw
        m.add(sag_plane(1.55, 2.55, sag=0.05, nx=6, nz=10, edge_drop=0.95), mat,
              at=(tx, arm_h - 0.04, 0.10 + tz), rot_z=0.05)
        m.add(sag_plane(1.45, 1.30, sag=0.06, nx=6, nz=6, edge_drop=0.30), mat,
              at=(tx + 0.35, seat_h + 0.22, 0.75 + tz), rot_y=0.22)
    return m


# ================================================================== ITEM 5 rug
# photo_rugcrop.png: a coarse crosshatch flatweave -- long light and dark
# streaks in both directions over a mid ground, at roughly 0.1-0.2 ft.  So the
# rug is a base slab, a 0.36 ft tonal mottle, and ~700 thin streak quads.
# Written with SMOOTH quads (4 verts) instead of round 3's flat boxes (36
# verts): same field, 4.50 MB -> ~0.2 MB.
RX, RZ, RL, RDp, RT = 11.20, 9.80, 13.20, 11.00, 0.075
RUG_BASE = "#5c5952"
RUG = [Material("lrrug%d" % i, c, roughness=0.99)
       for i, c in enumerate(ramp(RUG_BASE, 6, 5))]
RUG_STREAK = [Material("lrrugs%d" % i, c, roughness=0.99)
              for i, c in enumerate(ramp(RUG_BASE, 6, 13))]
RUGE = Material("lrruge", "#504c46", roughness=0.99)

m = Model()
m.add(box(RL, RT, RDp), RUG[2], at=(0, 0, 0))
m.add(box(RL + 0.14, RT * 0.55, RDp + 0.14), RUGE, at=(0, 0, 0))    # bound edge
mottle(m, RL, RDp, 0.58, RUG, at=(0, RT, 0), rnd=rnd)
for k in range(1350):
    horiz = rnd.random() < 0.5
    ln = rnd.uniform(0.55, 2.20)
    th = rnd.uniform(0.024, 0.050)
    x = rnd.uniform(-RL / 2 + 0.9, RL / 2 - 0.9)
    z = rnd.uniform(-RDp / 2 + 0.9, RDp / 2 - 0.9)
    w, d = (ln, th) if horiz else (th, ln)
    q = [(-w / 2, 0, -d / 2), (w / 2, 0, -d / 2), (w / 2, 0, d / 2), (-w / 2, 0, d / 2)]
    m.add(Part(q, [(0, 2, 1), (0, 3, 2)], smooth=True),
          RUG_STREAK[rnd.randrange(len(RUG_STREAK))], at=(x, RT + 0.002, z))
put("Living Floor Rug", save(m, "rug4"), (RX, 0.004, RZ))

# ============================================================ south sectional
SD, SRD = 3.55, 2.60
m = sofa(SECT, 7.60, SD, n_seat=3, ret_w=2.70, ret_d=SRD, ret_side=-1,
         throw=(-0.6, 0.0, THROW_G), pillows=[
             (-2.6, PIL_CREAM, 1.50, 1.42, 0.10), (-1.4, PIL_GREY, 1.44, 1.34, -0.14),
             (0.2, PIL_WAVE, 1.46, 1.36, 0.08), (1.5, PIL_GREY, 1.44, 1.34, 0.13),
             (2.6, PIL_CREAM, 1.50, 1.42, -0.09)])
m.add(sag_plane(2.2, 1.9, sag=0.12, nx=8, nz=8, edge_drop=0.48), THROW_B,
      at=(2.1, 1.50, 2.5))
put_anchor("Living Sofa South", m, save(m, "sofa_s4"),
           (0.0, -SD / 2), (4.35, 16.94), 180)

# =============================================================== ITEM 4 east
# North: 6.20 x 3.55, square arms, three seats, tan fur throw.  z 4.10..10.30.
ED = 3.55
m = sofa(EAST, 6.20, ED, arm_w=0.92, arm_r=0.30, back_h=2.84, n_seat=3, fur=True,
         pillows=[(-1.95, PIL_WAVE, 1.44, 1.38, 0.12),
                  (-0.35, PIL_WAVE2, 1.40, 1.32, -0.10),
                  (1.35, PIL_WAVE, 1.44, 1.38, 0.09)])
put_anchor("Living Sofa East", m, save(m, "sofa_e4"),
           (0.0, -ED / 2), (RW - 0.02, 7.20), 270)

# South: a DIFFERENT sofa -- deeper, taller back, rolled arms, two wide seats,
# navy ticking pillows and the big cream body pillow photo f puts on the seat.
# z 10.45..16.85, so the slot between the pair is 0.15 ft, not 0.95.
ESD = 3.95
m = sofa(ESOU, 6.40, ESD, arm_w=1.15, arm_r=0.52, back_h=3.05, arm_h=2.30,
         n_seat=2, seat_r=0.30, pillows=[
             (-1.55, PIL_CREAM, 1.62, 1.52, 0.15, PIL_TICK),
             (0.25, PIL_CREAM, 1.54, 1.44, -0.11, PIL_TICK),
             (1.75, PIL_GREY, 1.48, 1.38, 0.08)])
m.add(bolster(2.55, 0.44, seg=14, rings=6, nub=0.028, rnd=rnd), PIL_CREAM,
      at=(-0.55, 1.86, -0.30), rot_y=0.20, rot_z=0.10)
put_anchor("Living Sofa East South", m, save(m, "sofa_es4"),
           (0.0, -ESD / 2), (RW - 0.02, 13.65), 270)

# ================================================================== armchair
# photo_chaircrop.png: the chair-and-a-half is swallowed by a chunky sherpa
# throw over the back and down the near arm, plus a sherpa body pillow.  Round
# 3 shipped a single flat sag plane and one rounded box.
m = sofa(CHAI, 5.00, 4.00, arm_w=0.94, arm_r=0.44, back_h=2.78, arm_h=2.14,
         n_seat=1, seat_r=0.30)
m.add(puff(2.55, 0.62, 1.55, r=0.28, seg=16, rings=8, nub=0.060, rnd=rnd), SHERPA,
      at=(0.02, 1.62, -1.02), rot_x=-0.30)                 # throw over the back
m.add(puff(2.20, 0.44, 1.30, r=0.20, seg=14, rings=7, nub=0.055, rnd=rnd), SHERPA2,
      at=(0.02, 2.42, -1.30), rot_x=0.10)
m.add(puff(0.85, 0.52, 2.90, r=0.24, seg=13, rings=7, nub=0.055, rnd=rnd), SHERPA,
      at=(-1.66, 2.02, 0.10), rot_z=0.10)                  # over the near arm
m.add(sag_plane(0.95, 1.35, sag=0.05, nx=5, nz=6, edge_drop=0.60), SHERPA2,
      at=(-1.72, 2.02, 0.60))
put_anchor("Living Armchair", m, save(m, "armchair4"), (0.0, -2.0), (1.05, 7.60), 72)


# ================================================================== ottomans
def ottoman(P, w, d, h=1.42, weave=None):
    m = Model()
    m.add(box(w - 0.34, 0.30, d - 0.34), P["plinth"], at=(0, 0, 0))
    m.add(puff(w, h - 0.30, d, r=0.30, seg=14, rings=7, nub=NUB, rnd=rnd),
          P["body"], at=(0, 0.30, 0))
    if weave:
        mottle(m, w - 0.42, d - 0.42, 0.26, weave, at=(0, h - 0.012, 0), rnd=rnd)
    return m


OTT_W = [Material("lrottw%d" % i, c, roughness=0.97)
         for i, c in enumerate(ramp("#9a978f", 4, 6))]
m = ottoman(OTTO, 4.40, 2.50, h=1.40, weave=OTT_W)
m.add(box(4.44, 0.05, 2.54), OTTO["reveal"], at=(0, 1.10, 0))
m.add(box(1.12, 0.05, 0.82), Material("lrlap", "#8b8d90", roughness=0.35),
      at=(-0.5, 1.40, 0.10), rot_y=0.28)
m.add(box(0.40, 0.05, 0.22), Material("lrdark", "#1c1d21", roughness=0.4),
      at=(0.9, 1.40, -0.30), rot_y=-0.35)
m.add(sag_plane(1.5, 1.1, sag=0.07, nx=6, nz=6, edge_drop=0.26), THROW_B,
      at=(1.3, 1.42, 0.42))
put("Living Ottoman", save(m, "ottoman4"), (7.70, 0.0, 8.40), rot=3)

EAS_W = [Material("lreasw%d" % i, c, roughness=0.97)
         for i, c in enumerate(ramp("#95928c", 4, 6))]
m = ottoman(EAST, 4.20, 2.60, h=1.44, weave=EAS_W)
m.add(box(4.24, 0.05, 2.64), EAST["reveal"], at=(0, 1.14, 0))
m.add(bolster(1.85, 0.13, seg=10, rings=5, nub=0.030, rnd=rnd), FUR2,
      at=(-0.95, 1.50, -0.28), rot_y=0.10)
m.add(sag_plane(1.80, 1.05, sag=0.05, nx=8, nz=5, edge_drop=0.34), FUR,
      at=(-0.95, 1.46, 0.22), rot_y=0.10)
put("Living Chaise Ottoman", save(m, "chaise4"), (14.70, 0.0, 7.20), rot=270)

# =============================================================== coffee table
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
put("Living Coffee Table", save(m, "coffee4"), (11.80, 0.0, 11.00), rot=2)
