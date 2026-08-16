"""Laundry (room 9) -- appliance wall, uppers, shelf, baskets, floor marks.

ORIENTATION CORRECTION.  The shell pass put the washer/dryer at the WEST end of
the north wall, which is where the floor plan puts the STEP AND DOOR IN FROM THE
GARAGE (the plan's "Indoor garage door" hatch sits at world x 21.8-26.5 =
laundry local x 0-4.6).  The plan's own appliance icon is at world x 29.4-31.9,
z 7.7-10.5 = laundry local x 7.5-10.0, z 0.4-3.2, i.e. hard against the EAST
wall on the north side, with a partition drawn at local x 7.5.  Photos alone
cannot separate the two ends -- the traced 11.0 x 5.7 rectangle merges the real
mudroom and the laundry alcove, so no single camera position reproduces
'Laundry room and garage door right next to it.jpg' exactly.  The plan is the
tie-breaker, so the run moves east and the west end is left clear as the way in.

Everything else is measured off that photo: top-load washer left, front-load
dryer right, white shaker uppers with black bar pulls, a floating shelf with
three dark bottles under a framed print, a full-width ledge carrying two woven
baskets and a white box.
"""
from gkit import *   # noqa: F401,F403
import gkit as G

ROOM = 9
W, D, H = 11.0, 5.7, 9.0

WALLW = Material("lwhite", "#f1efeb", roughness=0.58)
WALLW_D = Material("lwhited", "#dfdcd6", roughness=0.60)
APP = Material("app", "#eceae6", roughness=0.42)
APP_D = Material("appd", "#d6d4d0", roughness=0.45)
GLOSS = Material("lglass", "#191a1c", roughness=0.20, metallic=0.10)
ROSE = Material("rose", "#c3a087", roughness=0.35, metallic=0.35)
PANEL = Material("lpanel", "#2a2c30", roughness=0.45)
WICK = Material("wick", "#b39a72", roughness=0.88)
WICK_D = Material("wickd", "#8f7a58", roughness=0.90)
BOTL = Material("botl", "#3a3d40", roughness=0.40)
FRAME = Material("frame", "#3f4245", roughness=0.55)
ART = Material("art", "#f3f2ee", roughness=0.75)
BLKP = Material("blkp", "#232427", roughness=0.42, metallic=0.25)
GREEN = Material("lgreen", "#4f7a4a", roughness=0.80)
POT = Material("pot", "#f0eeea", roughness=0.55)


def appliances():
    m = Model()
    NZ = 0.10                       # face of the north wall
    # ---------------- washer: top-load, black glass lid, raised console
    wx0, wx1 = 6.18, 8.47
    bx(m, APP, wx0, wx1, 0.16, 3.05, NZ, NZ + 2.50)
    bx(m, PANEL, wx0 + 0.03, wx1 - 0.03, 0.0, 0.18, NZ + 0.05, NZ + 2.45)
    bx(m, APP, wx0, wx1, 3.05, 3.14, NZ, NZ + 2.50)          # top deck
    bx(m, GLOSS, wx0 + 0.14, wx1 - 0.14, 3.14, 3.22, NZ + 0.72, NZ + 2.38)
    bx(m, APP, wx0, wx1, 3.14, 3.62, NZ, NZ + 0.68)          # console
    bx(m, PANEL, wx0 + 0.10, wx1 - 0.10, 3.24, 3.52, NZ + 0.62, NZ + 0.66)
    m.add(cylinder(0.155, 0.055, 16), ROSE, at=(wx0 + 0.52, 3.52, NZ + 0.34))
    for i in range(5):
        bx(m, PANEL, wx0 + 0.95 + i * 0.20, wx0 + 1.05 + i * 0.20, 3.44, 3.52,
           NZ + 0.26, NZ + 0.42)

    # ---------------- dryer: front-load, dark glass door, rose-gold ring
    dx0, dx1 = 8.53, 10.86
    bx(m, APP, dx0, dx1, 0.16, 3.05, NZ, NZ + 2.58)
    bx(m, PANEL, dx0 + 0.03, dx1 - 0.03, 0.0, 0.18, NZ + 0.05, NZ + 2.50)
    bx(m, APP, dx0, dx1, 3.05, 3.20, NZ, NZ + 2.58)
    bx(m, ROSE, dx0 + 0.05, dx1 - 0.05, 2.42, 2.62, NZ + 2.55, NZ + 2.60)  # facia band
    bx(m, APP_D, dx0 + 0.05, dx1 - 0.05, 2.62, 3.05, NZ + 2.55, NZ + 2.60)
    m.add(cylinder(0.145, 0.05, 16), ROSE, at=(dx0 + 0.62, 2.71, NZ + 2.61), rot_x=G.R(90))
    for i in range(6):
        bx(m, PANEL, dx0 + 1.05 + i * 0.16, dx0 + 1.13 + i * 0.16, 2.72, 2.94,
           NZ + 2.60, NZ + 2.63)
    m.add(cylinder(0.80, 0.10, 26), APP_D,
          at=((dx0 + dx1) / 2, 1.28, NZ + 2.58), rot_x=G.R(90))
    m.add(cylinder(0.71, 0.10, 26), GLOSS,
          at=((dx0 + dx1) / 2, 1.28, NZ + 2.64), rot_x=G.R(90))
    m.add(cylinder(0.30, 0.06, 20), Material("lint", "#4b4e52", roughness=0.6),
          at=((dx0 + dx1) / 2 - 0.28, 1.05, NZ + 2.68), rot_x=G.R(90))

    # tall finished end panel closing the west side of the alcove (the white
    # full-height panel at the left edge of both laundry photos)
    bx(m, WALLW, 5.42, 5.62, 0.0, 7.88, NZ, NZ + 2.52)
    bx(m, WALLW_D, 5.62, 5.66, 0.0, 7.88, NZ + 0.04, NZ + 2.48)

    # ---------------- full-width ledge over the run
    LX0, LX1, LY = 5.42, 10.94, 3.86
    bx(m, WALLW, LX0, LX1, LY, LY + 0.12, NZ, NZ + 1.42)
    bx(m, WALLW_D, LX0, LX1, LY - 0.06, LY, NZ + 1.36, NZ + 1.42)
    for xx in (LX0 + 0.06, LX1 - 0.18):        # end brackets down to the wall
        bx(m, WALLW, xx, xx + 0.12, LY - 1.05, LY, NZ, NZ + 0.22)

    # baskets + box + plant on the ledge
    for (bx0, bx1) in ((6.30, 7.40), (7.62, 8.70)):
        bx(m, WICK, bx0, bx1, LY + 0.12, LY + 0.82, NZ + 0.22, NZ + 1.16)
        bx(m, WICK_D, bx0 - 0.035, bx1 + 0.035, LY + 0.82, LY + 0.90,
           NZ + 0.185, NZ + 1.195)
        for i in range(3):                       # woven bands, front + sides
            y = LY + 0.24 + i * 0.19
            bx(m, WICK_D, bx0 - 0.012, bx1 + 0.012, y, y + 0.055,
               NZ + 0.208, NZ + 1.174)
        bx(m, WICK_D, bx0 + 0.42, bx0 + 0.68, LY + 0.60, LY + 0.72,
           NZ + 1.16, NZ + 1.185)
    bx(m, WALLW, 6.98, 7.44, LY + 0.12, LY + 0.62, NZ + 0.42, NZ + 0.94)
    bx(m, FRAME, 7.03, 7.39, LY + 0.28, LY + 0.44, NZ + 0.40, NZ + 0.42)
    m.add(cylinder(0.20, 0.30, 14, r_top=0.24), POT, at=(9.35, LY + 0.12, NZ + 0.70))
    m.add(cylinder(0.30, 0.34, 12, r_top=0.05), GREEN, at=(9.35, LY + 0.40, NZ + 0.70))
    m.add(cylinder(0.16, 0.24, 12), Material("ldet", "#d8dde2", roughness=0.4),
          at=(10.20, LY + 0.12, NZ + 0.62))

    # a woven box parked on the dryer
    bx(m, WICK, 9.10, 10.10, 3.20, 3.72, NZ + 0.55, NZ + 1.75)
    bx(m, WICK_D, 9.06, 10.14, 3.72, 3.80, NZ + 0.51, NZ + 1.79)

    # ---------------- upper cabinets, white shaker with black bar pulls
    def upper(x0, x1, y0, y1, doors=2):
        bx(m, WALLW_D, x0, x1, y0, y1, NZ, NZ + 1.22)
        w = (x1 - x0 - 0.06) / doors
        for d in range(doors):
            a = x0 + 0.03 + d * w
            bx(m, WALLW, a, a + w - 0.03, y0 + 0.03, y1 - 0.03,
               NZ + 1.22, NZ + 1.28)
            bx(m, WALLW_D, a + 0.13, a + w - 0.16, y0 + 0.16, y1 - 0.16,
               NZ + 1.26, NZ + 1.285)
            bx(m, BLKP, a + w * 0.5 - 0.05, a + w * 0.5 + 0.05, y0 + 0.22,
               y0 + 0.82, NZ + 1.28, NZ + 1.38)
        # crown
        bx(m, WALLW, x0 - 0.06, x1 + 0.06, y1, y1 + 0.10, NZ, NZ + 1.34)
        bx(m, WALLW, x0 - 0.03, x1 + 0.03, y1 + 0.10, y1 + 0.20, NZ, NZ + 1.28)

    upper(5.42, 7.30, 5.42, 7.68, 2)
    upper(9.20, 10.94, 5.42, 7.68, 2)

    # framed print + floating shelf between the cabinets
    bx(m, FRAME, 7.62, 8.86, 6.10, 7.62, NZ, NZ + 0.06)
    bx(m, ART, 7.70, 8.78, 6.18, 7.54, NZ + 0.06, NZ + 0.075)
    for i, (a, b, y) in enumerate(((7.86, 8.62, 6.72), (7.86, 8.62, 6.98),
                                   (7.98, 8.50, 7.24))):
        bx(m, FRAME, a, b, y, y + 0.055, NZ + 0.075, NZ + 0.085)
    bx(m, WALLW, 7.48, 9.00, 5.42, 5.54, NZ, NZ + 0.62)
    bx(m, WALLW_D, 7.48, 9.00, 5.34, 5.42, NZ, NZ + 0.56)
    for i, xx in enumerate((7.72, 8.24, 8.72)):
        m.add(cylinder(0.105, 0.44, 12, r_top=0.055), BOTL,
              at=(xx, 5.54, NZ + 0.30))
        m.add(cylinder(0.045, 0.16, 10), BLKP, at=(xx, 5.98, NZ + 0.30))
    return m


def tall_cabinet():
    """Broom / utility closet at the WEST end of the north wall.

    The photo's tall white unit is modelled as the alcove end panel (see
    appliances()); this taller cupboard fills the otherwise-dead west end and
    keeps the sight line from the hall doorway to the appliance run open."""
    m = Model()
    x0, x1, z0, z1, TOPY = 0.20, 1.98, 0.10, 2.32, 7.68
    bx(m, WALLW_D, x0, x1, 0.0, TOPY, z0, z1)
    bx(m, PANEL, x0 + 0.04, x1 - 0.04, 0.0, 0.28, z0 + 0.04, z1 - 0.06)
    for (y0, y1) in ((0.30, 3.78), (3.86, TOPY - 0.04)):
        for d in range(2):
            a = x0 + 0.04 + d * ((x1 - x0 - 0.10) / 2)
            b = a + (x1 - x0 - 0.10) / 2 - 0.03
            bx(m, WALLW, a, b, y0, y1, z1, z1 + 0.06)
            bx(m, WALLW_D, a + 0.11, b - 0.11, y0 + 0.13, y1 - 0.13,
               z1 + 0.055, z1 + 0.072)
        bx(m, BLKP, x0 + 0.78, x0 + 0.88, (y0 + y1) / 2 - 0.30,
           (y0 + y1) / 2 + 0.30, z1 + 0.06, z1 + 0.155)
    bx(m, WALLW, x0 - 0.06, x1 + 0.06, TOPY, TOPY + 0.10, z0, z1 + 0.12)
    bx(m, WALLW, x0 - 0.03, x1 + 0.03, TOPY + 0.10, TOPY + 0.20, z0, z1 + 0.06)
    return m


def hamper():
    m = Model()
    bx(m, WICK, 3.05, 4.30, 0.0, 1.72, 0.62, 2.12)
    bx(m, WICK_D, 3.00, 4.35, 1.72, 1.82, 0.57, 2.17)
    for i in range(4):
        y = 0.22 + i * 0.36
        bx(m, WICK_D, 3.025, 4.325, y, y + 0.075, 0.595, 2.145)
    bx(m, Material("towel", "#dfe3e6", roughness=0.92),
       3.22, 4.14, 1.58, 1.94, 0.82, 1.92)
    return m


def floor_marks():
    m = Model()
    # floor register near the south wall (the photo shows one)
    RG = Material("reg", "#e6e4e0", roughness=0.55)
    RGS = Material("regs", "#8d8f91", roughness=0.70)
    bx(m, RG, 4.55, 5.70, 0.0, 0.022, 4.55, 5.28)
    for i in range(9):
        zz = 4.62 + i * 0.075
        bx(m, RGS, 4.62, 5.63, 0.022, 0.030, zz, zz + 0.042)
    for (cx, cz, rx, rz, st) in ((7.35, 1.40, 1.55, 1.55, 0.36),
                                 (9.70, 1.45, 1.55, 1.60, 0.36),
                                 (1.09, 1.25, 1.15, 1.35, 0.34),
                                 (3.68, 1.37, 0.95, 1.00, 0.30)):
        G.contact_shadow(m, cx, cz, rx, rz, y=0.012, tone="#26262a",
                         strength=st, steps=8, room=(W, D))
    return m


if __name__ == "__main__":
    tot = 0
    tot += G.save_and_place("Laundry Washer Dryer", appliances(), ROOM)
    tot += G.save_and_place("Laundry Tall Cabinet", tall_cabinet(), ROOM)
    tot += G.save_and_place("Laundry Hamper", hamper(), ROOM)
    tot += G.save_and_place("Laundry Floor Marks", floor_marks(), ROOM)
    print("  laundry total %.1f KB" % tot)
