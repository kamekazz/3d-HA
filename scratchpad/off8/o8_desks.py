"""Room 8 Office -- the two workstations.

Photo A / f: an L desk wrapping the NW corner (long leg under the framed art on
the north wall, return south along the west wall) carrying a curved ultrawide,
a black high-back gaming chair, a white 3-drawer pedestal and a tower on the
floor; and a sit/stand desk down the east wall under the two windows with a
cream desk pad, a wooden monitor riser, a 27in monitor, two white pedestals and
a black mesh task chair.

Desk tops measured against the 6'8" door in photo B and the 29-30in standard:
L desk 2.48 ft, the height-adjustable east desk 2.42 ft.
"""
import math
from o8kit import (Model, Material, Part, box, rounded_box, cylinder, torus,
                   quad, W, D, R, bx, save_and_place, BLACKMET, CHROME)
from o8kit import contact_shadow as _cs


def contact_shadow(m, cx, cz, rx, rz, y=0.012, strength=0.28, room=(W, D)):
    """Same smooth radial falloff, half the triangles -- this room carries a
    shadow under every piece and the 12x30 default blew the payload budget."""
    _cs(m, cx, cz, rx, rz, y=y, strength=strength, steps=7, room=room)

TOP_L = Material("desktopL", "#4e4c49", roughness=0.62)      # dark L-desk top
TOP_E = Material("desktopE", "#57534d", roughness=0.60)      # warmer east top
LEG = Material("deskleg", "#232529", roughness=0.48, metallic=0.30)
SCREEN = Material("screen", "#111214", roughness=0.30)
BEZEL = Material("bezel", "#2a2c2f", roughness=0.45)
WHITE = Material("whitebox", "#eeece8", roughness=0.60)
WHITE_D = Material("whiteboxd", "#dedbd5", roughness=0.62)
PAD = Material("deskpad", "#cec2a8", roughness=0.88)          # cream desk pad
MAT_K = Material("deskmat", "#26272a", roughness=0.92)
MESH = Material("mesh", "#8d9094", roughness=0.90)           # photo A: light grey mesh
MESHD = Material("meshd", "#6d7175", roughness=0.90)
THROW = Material("throw", "#b8c8a8", roughness=0.92)          # the green throw in photo A
GREYMESH = Material("greymesh", "#3a3c3f", roughness=0.88)
OAKSH = Material("oaksh", "#7e7364", roughness=0.72)          # riser shelf
KEYW = Material("keyw", "#e9e7e2", roughness=0.55)
PLANT = Material("succ", "#5e7a55", roughness=0.85)
POTW = Material("potw", "#e6e3dd", roughness=0.60)
SILVER = Material("silver", "#c6c8ca", roughness=0.35, metallic=0.45)


def rotm(sub, ang, cx, cz):
    """Spin a sub-model about a vertical axis and return its parts."""
    ca, sa = math.cos(ang), math.sin(ang)
    out = []
    for part, mat in sub._parts:
        v = [(cx + (x - cx) * ca - (z - cz) * sa, y,
              cz + (x - cx) * sa + (z - cz) * ca) for (x, y, z) in part.verts]
        out.append((Part(v, part.tris, part.smooth), mat))
    return out


# ------------------------------------------------------------------- chairs
def task_chair(m, cx, cz, face, mesh=MESH, arms=True, high=False,
               throw=False):
    """A five-star mesh task chair, `face` = radians the sitter looks toward
    (+z is south).  Chunky enough to read at 50 deg from above."""
    sub = Model()
    contact_shadow(sub, cx, cz, 1.45, 1.45, y=0.012, strength=0.26, room=(W, D))
    sub.add(cylinder(0.155, 1.28, 10), LEG, at=(cx, 0.10, cz))
    for k in range(5):
        a = 2 * math.pi * k / 5 + 0.3
        arm = Model()
        bx(arm, LEG, cx - 0.075, cx + 0.075, 0.16, 0.28, cz - 0.06, cz + 1.02)
        arm.add(cylinder(0.105, 0.20, 8), LEG, at=(cx, 0.0, cz + 0.98))
        m._parts.extend(rotm(arm, a, cx, cz))
    seat = Model()
    seat.add(rounded_box(1.82, 0.36, 1.72, r=0.22, seg=3), MESHD,
             at=(cx, 1.28, cz))
    bh = 2.55 if high else 2.00
    seat.add(rounded_box(1.66, bh, 0.28, r=0.18, seg=3), mesh,
             at=(cx, 1.60, cz + 0.72), rot_x=R(-9))
    if high:      # gaming chair: headrest pillow + white stitch piping
        seat.add(rounded_box(1.10, 0.46, 0.30, r=0.14, seg=3), mesh,
                 at=(cx, 3.95, cz + 0.60))
        bx(seat, Material("piping", "#d8d6cf", roughness=0.6),
           cx - 0.80, cx - 0.72, 1.70, 3.75, cz + 0.60, cz + 0.66)
        bx(seat, Material("piping", "#d8d6cf", roughness=0.6),
           cx + 0.72, cx + 0.80, 1.70, 3.75, cz + 0.60, cz + 0.66)
    if throw:
        seat.add(rounded_box(1.42, 1.30, 0.26, r=0.16, seg=2), THROW,
                 at=(cx, 2.05, cz + 0.86), rot_x=R(-9))
    if arms:
        for s in (-1, 1):
            bx(seat, LEG, cx + s * 0.86 - 0.07, cx + s * 0.86 + 0.07,
               1.46, 2.10, cz - 0.30, cz - 0.16)
            bx(seat, LEG, cx + s * 0.86 - 0.11, cx + s * 0.86 + 0.11,
               2.10, 2.22, cz - 0.62, cz + 0.26)
    m._parts.extend(rotm(seat, face, cx, cz))
    m._parts.extend(sub._parts)


def monitor(m, cx, z0, z1, wide, y0, h, curve=0.0, cam=True):
    """A screen standing in the x/z plane facing -x..+x is wrong for this room:
    every monitor here faces WEST (-x) or SOUTH.  Built facing -x (the sitter
    is west of it) with `wide` along z."""
    n = 3 if curve else 1
    for i in range(n):
        za = z0 + (z1 - z0) * i / n
        zb = z0 + (z1 - z0) * (i + 1) / n
        off = curve * (abs(i - (n - 1) / 2.0) / max(1, (n - 1) / 2.0))
        bx(m, BEZEL, cx - 0.055 - off, cx + 0.055 - off, y0, y0 + h, za, zb)
        bx(m, SCREEN, cx - 0.075 - off, cx - 0.055 - off, y0 + 0.05,
           y0 + h - 0.05, za + 0.04, zb - 0.04)
    zc = (z0 + z1) / 2
    bx(m, BEZEL, cx - 0.06, cx + 0.16, y0 - 0.42, y0 + 0.12, zc - 0.24, zc + 0.24)
    bx(m, LEG, cx - 0.10, cx + 0.30, y0 - 0.50, y0 - 0.42, zc - 0.46, zc + 0.46)
    if cam:
        m.add(rounded_box(0.16, 0.20, 0.34, r=0.06, seg=2), BLACKMET,
              at=(cx - 0.02, y0 + h, zc))
    _ = wide


# ------------------------------------------------------------------ L  desk
LX0, LX1, LZ0, LZ1 = 0.30, 6.35, 0.25, 2.85        # north leg
RX0, RX1, RZ0, RZ1 = 0.30, 2.95, 2.85, 7.05        # west return
LTOP = 2.48


def l_desk(m):
    contact_shadow(m, 3.3, 1.5, 3.35, 1.55, strength=0.30, room=(W, D))
    contact_shadow(m, 1.6, 4.9, 1.60, 2.35, strength=0.30, room=(W, D))
    bx(m, TOP_L, LX0, LX1, LTOP, LTOP + 0.14, LZ0, LZ1)
    bx(m, TOP_L, RX0, RX1, LTOP, LTOP + 0.14, RZ0, RZ1)
    # rounded inner corner so the L reads as one worktop, not two planks
    for i in range(6):
        a = math.pi * 0.5 * i / 6
        b = math.pi * 0.5 * (i + 1) / 6
        cx0, cz0 = RX1, LZ1
        r = 1.05
        p = [(cx0, LTOP + 0.14, cz0),
             (cx0 + r * math.sin(a), LTOP + 0.14, cz0 + r * math.cos(a)),
             (cx0 + r * math.sin(b), LTOP + 0.14, cz0 + r * math.cos(b))]
        m.add(Part(p, [(0, 2, 1)]), TOP_L)
        m.add(Part([(p[0][0], LTOP, p[0][2]), (p[1][0], LTOP, p[1][2]),
                    (p[2][0], LTOP, p[2][2])], [(0, 1, 2)]), TOP_L)
    for (px, pz) in ((LX0 + 0.30, LZ0 + 0.25), (LX1 - 0.50, LZ0 + 0.25),
                     (LX1 - 0.50, LZ1 - 0.55), (RX1 - 0.50, RZ1 - 0.55),
                     (RX0 + 0.30, RZ1 - 0.55), (RX0 + 0.30, RZ0 + 0.60)):
        bx(m, LEG, px, px + 0.22, 0.0, LTOP, pz, pz + 0.22)
        bx(m, LEG, px - 0.14, px + 0.36, 0.0, 0.10, pz - 0.30, pz + 0.52)
    # modesty panel along the north wall (photo A: dark under the worktop)
    bx(m, LEG, LX0 + 0.5, LX1 - 0.5, 1.55, LTOP - 0.06, LZ0 + 0.05, LZ0 + 0.13)

    # ultrawide, curved, on the north leg
    monitor(m, 0.0, 0.0, 0.0, 0, 0, 0) if False else None
    _ultrawide(m, cx=3.30, z0=1.05, z1=1.35)

    # white 3-drawer pedestal tucked under the north leg
    _pedestal(m, 4.55, 5.92, 0.55, 2.55, 2.34)
    # tower + a small tray of gear on the floor under the return
    bx(m, MAT_K, 0.55, 1.45, 0.0, 1.72, 4.75, 6.45)
    bx(m, SCREEN, 0.60, 0.66, 0.20, 1.55, 4.90, 6.30)
    contact_shadow(m, 1.0, 5.6, 0.95, 1.20, strength=0.24, room=(W, D))

    # desk mat + keyboard + mouse on the return
    bx(m, MAT_K, 0.55, 2.80, LTOP + 0.14, LTOP + 0.155, 3.55, 5.35)
    bx(m, MAT_K, 0.85, 1.35, LTOP + 0.155, LTOP + 0.235, 3.95, 5.05)
    for i in range(6):
        bx(m, Material("keycap", "#3b3d40", roughness=0.6),
           0.88, 1.32, LTOP + 0.235, LTOP + 0.245,
           4.00 + i * 0.17, 4.14 + i * 0.17)
    m.add(rounded_box(0.30, 0.16, 0.44, r=0.07, seg=2), MAT_K,
          at=(1.85, LTOP + 0.155, 4.45))
    # small stuff on the north leg -- succulent, tray, three figures
    m.add(cylinder(0.26, 0.30, 10), POTW, at=(1.15, LTOP + 0.14, 1.05))
    m.add(rounded_box(0.44, 0.34, 0.44, r=0.16, seg=2), PLANT,
          at=(1.15, LTOP + 0.40, 1.05))
    bx(m, WHITE_D, 1.75, 2.45, LTOP + 0.14, LTOP + 0.26, 0.75, 1.35)
    for i, c in enumerate(("#c9b48a", "#6f8fa8", "#b0716b")):
        m.add(rounded_box(0.20, 0.30, 0.20, r=0.07, seg=2),
              Material("fig%d" % i, c, roughness=0.7),
              at=(1.90 + i * 0.24, LTOP + 0.26, 1.05))
    # photo A: a white globe lamp and a small dark speaker at the east end of
    # the north leg, and headphones parked on the return
    m.add(cylinder(0.24, 0.16, 12), Material("lampbase", "#e6e3dd", roughness=0.5),
          at=(5.95, LTOP + 0.14, 1.30))
    m.add(rounded_box(0.62, 0.62, 0.62, r=0.28, seg=3),
          Material("globe", "#fbf7ec", roughness=0.30, emissive="#ffeec9",
                   emissive_strength=1.5),
          at=(5.95, LTOP + 0.28, 1.30))
    m.add(rounded_box(0.34, 0.52, 0.30, r=0.07, seg=2), MAT_K,
          at=(5.20, LTOP + 0.14, 0.85))
    m.add(cylinder(0.11, 0.95, 8), MAT_K, at=(2.30, LTOP + 0.14, 3.95))
    m.add(torus(0.30, 0.075), MAT_K, at=(2.30, LTOP + 1.05, 3.95), rot_x=R(90))
    m.add(cylinder(0.13, 0.42, 10), Material("cupk", "#3b3d40", roughness=0.6),
          at=(5.35, LTOP + 0.14, 1.05))
    for i in range(5):
        bx(m, Material("pen%d" % (i % 3), ["#d9d5cc", "#3b3d40", "#8a8e93"][i % 3],
                       roughness=0.6),
           5.30 + (i % 3) * 0.05, 5.34 + (i % 3) * 0.05, LTOP + 0.44,
           LTOP + 0.80, 1.00 + i * 0.03, 1.04 + i * 0.03)


def _ultrawide(m, cx, z0, z1):
    """34in curved ultrawide on a monitor arm, facing SOUTH into the room.

    One continuous strip -- the first cut drew five boxes with gaps between
    them and read as five separate monitors."""
    y0, h = 3.16, 1.30
    xa, xb = 1.50, 5.20
    n = 8
    pts = []
    for i in range(n + 1):
        t = (i / n - 0.5) * 2.0
        pts.append((xa + (xb - xa) * i / n, z0 - 0.17 * (1.0 - t * t)))
    for i in range(n):
        (x0, zz0), (x1, zz1) = pts[i], pts[i + 1]
        m.add(Part([(x0, y0, zz0), (x1, y0, zz1), (x1, y0 + h, zz1),
                    (x0, y0 + h, zz0)], [(0, 1, 2), (0, 2, 3)]), BEZEL)
        m.add(Part([(x0, y0 + 0.055, zz0 + 0.022), (x1, y0 + 0.055, zz1 + 0.022),
                    (x1, y0 + h - 0.055, zz1 + 0.022),
                    (x0, y0 + h - 0.055, zz0 + 0.022)],
                   [(0, 1, 2), (0, 2, 3)]), SCREEN)
        m.add(Part([(x0, y0, zz0 - 0.085), (x1, y0, zz1 - 0.085),
                    (x1, y0 + h, zz1 - 0.085), (x0, y0 + h, zz0 - 0.085)],
                   [(0, 2, 1), (0, 3, 2)]), BEZEL)
        for yy in (y0, y0 + h):
            m.add(Part([(x0, yy, zz0 - 0.085), (x1, yy, zz1 - 0.085),
                        (x1, yy, zz1), (x0, yy, zz0)],
                       [(0, 1, 2), (0, 2, 3)]), BEZEL)
    bx(m, LEG, cx - 0.22, cx + 0.22, 2.62, y0 + 0.30, z0 + 0.02, z0 + 0.20)
    bx(m, LEG, cx - 0.45, cx + 0.45, 2.62, 2.72, z0 - 0.10, z0 + 0.45)
    m.add(rounded_box(0.20, 0.22, 0.34), BLACKMET, at=(cx, y0 + h, z0 - 0.19))


def _pedestal(m, x0, x1, z0, z1, h):
    contact_shadow(m, (x0 + x1) / 2, (z0 + z1) / 2, (x1 - x0) * 0.62,
                   (z1 - z0) * 0.62, strength=0.24, room=(W, D))
    bx(m, WHITE, x0, x1, 0.09, h, z0, z1)
    bx(m, LEG, x0 + 0.10, x1 - 0.10, 0.0, 0.09, z0 + 0.10, z1 - 0.10)
    for i in range(3):
        y = 0.24 + i * (h - 0.40) / 3
        bx(m, WHITE_D, x0 + 0.05, x1 - 0.05, y, y + (h - 0.40) / 3 - 0.06,
           z1, z1 + 0.022)
        bx(m, CHROME, (x0 + x1) / 2 - 0.22, (x0 + x1) / 2 + 0.22,
           y + (h - 0.40) / 3 - 0.16, y + (h - 0.40) / 3 - 0.10, z1 + 0.022,
           z1 + 0.055)


# --------------------------------------------------------------- east  desk
EX0, EX1, EZ0, EZ1 = 7.55, 10.36, 1.70, 7.25
ETOP = 2.42


def east_desk(m):
    contact_shadow(m, (EX0 + EX1) / 2, (EZ0 + EZ1) / 2, 1.55, 3.05,
                   strength=0.30, room=(W, D))
    bx(m, TOP_E, EX0, EX1, ETOP, ETOP + 0.13, EZ0, EZ1)
    for pz in (EZ0 + 0.35, EZ1 - 0.60):
        bx(m, LEG, EX1 - 0.62, EX1 - 0.40, 0.0, ETOP, pz, pz + 0.22)
        bx(m, LEG, EX0 + 0.42, EX1 - 0.36, 0.0, 0.11, pz - 0.02, pz + 0.24)
        bx(m, LEG, EX0 + 0.44, EX0 + 0.60, 0.10, ETOP - 0.30, pz, pz + 0.20)
    bx(m, LEG, EX0 + 0.50, EX1 - 0.44, ETOP - 0.32, ETOP - 0.16,
       EZ0 + 0.45, EZ0 + 0.62)
    # cream desk pad
    bx(m, PAD, EX0 + 0.30, EX1 - 1.05, ETOP + 0.13, ETOP + 0.145,
       EZ0 + 1.35, EZ0 + 3.45)
    # wooden monitor riser shelf
    for pz in (EZ0 + 1.05, EZ0 + 4.25):
        bx(m, OAKSH, EX1 - 1.55, EX1 - 0.30, ETOP + 0.13, ETOP + 0.52,
           pz, pz + 0.20)
    bx(m, OAKSH, EX1 - 1.62, EX1 - 0.22, ETOP + 0.52, ETOP + 0.62,
       EZ0 + 0.95, EZ0 + 4.55)
    _monitor_e(m, cx=EX1 - 0.62, zc=EZ0 + 2.75, wide=2.10, y0=ETOP + 0.62,
               h=1.22)
    # white keyboard + mouse on the pad
    bx(m, KEYW, EX0 + 0.75, EX0 + 1.35, ETOP + 0.145, ETOP + 0.225,
       EZ0 + 1.60, EZ0 + 3.35)
    m.add(rounded_box(0.30, 0.15, 0.44, r=0.07, seg=2), KEYW,
          at=(EX0 + 0.60, ETOP + 0.145, EZ0 + 2.30))
    # two white pedestals under the desk (photo f)
    _pedestal(m, EX1 - 1.45, EX1 - 0.25, 5.40, 7.05, 2.22)
    _pedestal(m, EX1 - 1.35, EX1 - 0.28, 2.05, 3.45, 2.05)
    # light grey mesh chair with the green throw over its back (photo A),
    # sitter faces EAST toward the window
    task_chair(m, 7.00, 4.35, R(-90), throw=True)
    # a few desk-top objects: cup, pen pot, a stack of books, a small speaker
    m.add(cylinder(0.15, 0.42, 10), Material("cupw", "#e8e5df", roughness=0.5),
          at=(EX1 - 1.85, ETOP + 0.13, EZ0 + 4.55))
    m.add(cylinder(0.17, 0.44, 10), Material("penp", "#3b3d40", roughness=0.6),
          at=(EX1 - 0.55, ETOP + 0.13, EZ0 + 4.95))
    for i, c in enumerate(("#8f4f52", "#3f5f7a", "#d7d2c6")):
        bx(m, Material("bk%d" % i, c, roughness=0.75), EX0 + 0.42, EX0 + 1.30,
           ETOP + 0.13 + i * 0.10, ETOP + 0.22 + i * 0.10,
           EZ0 + 4.25 + i * 0.05, EZ0 + 5.05 - i * 0.05)
    m.add(rounded_box(0.30, 0.44, 0.30, r=0.08, seg=2), MAT_K,
          at=(EX1 - 0.50, ETOP + 0.62, EZ0 + 0.65))
    # photo A's desk is crowded: a hair dryer, small tubs, a pink bottle,
    # papers and a row of figures along the riser
    m.add(cylinder(0.16, 0.62, 10), Material("bottlep", "#c8536b", roughness=0.5),
          at=(EX1 - 0.45, ETOP + 0.62, EZ0 + 3.75))
    m.add(cylinder(0.19, 0.30, 10), Material("tubw", "#e6e3dd", roughness=0.6),
          at=(EX1 - 1.15, ETOP + 0.62, EZ0 + 3.95))
    bx(m, MAT_K, EX1 - 1.30, EX1 - 0.55, ETOP + 0.13, ETOP + 0.34,
       EZ0 + 4.75, EZ0 + 5.15)
    m.add(cylinder(0.14, 0.55, 8), MAT_K, at=(EX1 - 0.95, ETOP + 0.34, EZ0 + 4.95))
    for i, c in enumerate(("#7fae5a", "#d4a13c", "#c4585a", "#5b8fb0", "#d0d2cf")):
        m.add(rounded_box(0.19, 0.26, 0.19, r=0.06, seg=2),
              Material("toy%d" % i, c, roughness=0.72),
              at=(EX1 - 0.42, ETOP + 0.62, EZ0 + 1.35 + i * 0.30))
    bx(m, Material("paper", "#eeece6", roughness=0.85), EX0 + 0.35, EX0 + 1.25,
       ETOP + 0.13, ETOP + 0.16, EZ0 + 3.85, EZ0 + 4.55)


def _monitor_e(m, cx, zc, wide, y0, h):
    bx(m, BEZEL, cx - 0.055, cx + 0.055, y0, y0 + h, zc - wide / 2, zc + wide / 2)
    bx(m, SCREEN, cx - 0.075, cx - 0.056, y0 + 0.05, y0 + h - 0.05,
       zc - wide / 2 + 0.04, zc + wide / 2 - 0.04)
    bx(m, BEZEL, cx - 0.02, cx + 0.16, y0 - 0.02, y0 + 0.10, zc - 0.30, zc + 0.30)
    m.add(rounded_box(0.14, 0.18, 0.30, r=0.05, seg=2), BLACKMET,
          at=(cx - 0.02, y0 + h, zc))


def build_l():
    m = Model()
    l_desk(m)
    # light grey mesh task chair at the L desk (photo A), sitter faces NORTH
    task_chair(m, 3.60, 3.95, R(190))
    return m


def build_e():
    m = Model()
    east_desk(m)
    return m


if __name__ == "__main__":
    save_and_place("Office Desks", build_l())
    save_and_place("Office Workstation East", build_e())
