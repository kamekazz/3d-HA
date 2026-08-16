"""Room 13 -- the bed group: black panel bed, bedding, pillow stack, the small
table + white lamp in the north-west corner, and their contact shadows.

Everything is measured off photo 1 against the 6'8" door and a 60 in queen
mattress: headboard 3.95 ft, footboard 1.80, mattress top 2.05, bed 5.60 x 7.16
with the HEADBOARD ON THE NORTH WALL.
"""

from gkit import *

rnd = Rnd(13137)

BLK = Material("gblk", "#1d1d20", roughness=0.52)          # black stained wood
BLK2 = Material("gblk2", "#26262a", roughness=0.52)        # panel faces
BLK3 = Material("gblk3", "#141416", roughness=0.55)        # reveals
QUILT = Material("gquilt", "#7b776f", roughness=0.94)      # top coverlet
QUILT2 = Material("gquilt2", "#6e6a63", roughness=0.94)
SHEET = Material("gsheet", "#8f8a81", roughness=0.93)
PILLOW = Material("gpill", "#a8a39a", roughness=0.95)
PILLOW2 = Material("gpill2", "#96918a", roughness=0.95)
BLUE = Material("gblue", "#65767e", roughness=0.93)        # knit throw
GREYST = Material("ggreyst", "#71757a", roughness=0.95)    # striped lumbar
FLORAL = Material("gfloral", "#a6a29b", roughness=0.95)
FLORALD = Material("gflorald", "#2b2e31", roughness=0.95, double_sided=True)
PURPLE = Material("gpurp", "#3a2939", roughness=0.94)

X0, X1, ZH, ZF = BED                                        # 2.55 8.15 0.16 7.32
CX = (X0 + X1) / 2
HB_TOP, FB_TOP = 3.95, 1.80
DECK, MATT = 1.30, 2.05


def bed():
    m = Model()
    # ---- frame
    bx(m, BLK, X0, X1, 0.0, HB_TOP - 0.10, ZH, ZH + 0.22)          # headboard
    bx(m, BLK, X0 - 0.05, X1 + 0.05, HB_TOP - 0.10, HB_TOP, ZH - 0.03, ZH + 0.27)
    for a, b in ((X0 + 0.30, CX - 0.06), (CX + 0.06, X1 - 0.30)):  # hb panels
        bx(m, BLK3, a - 0.03, b + 0.03, 1.30, HB_TOP - 0.30, ZH + 0.19, ZH + 0.21)
        bx(m, BLK2, a, b, 1.34, HB_TOP - 0.34, ZH + 0.20, ZH + 0.235)
    bx(m, BLK, X0, X1, 0.0, FB_TOP - 0.09, ZF - 0.22, ZF)          # footboard
    bx(m, BLK, X0 - 0.05, X1 + 0.05, FB_TOP - 0.09, FB_TOP, ZF - 0.26, ZF + 0.03)
    for a, b in ((X0 + 0.30, CX - 0.06), (CX + 0.06, X1 - 0.30)):
        bx(m, BLK3, a - 0.03, b + 0.03, 0.45, FB_TOP - 0.30, ZF - 0.21, ZF - 0.19)
        bx(m, BLK2, a, b, 0.49, FB_TOP - 0.34, ZF - 0.235, ZF - 0.20)
    bx(m, BLK, X0, X0 + 0.17, 0.0, DECK - 0.10, ZH, ZF)            # side rails
    bx(m, BLK, X1 - 0.17, X1, 0.0, DECK - 0.10, ZH, ZF)
    for (px, pz) in ((X0 + 0.085, ZH + 0.11), (X1 - 0.085, ZH + 0.11),
                     (X0 + 0.085, ZF - 0.11), (X1 - 0.085, ZF - 0.11)):
        bx(m, BLK, px - 0.115, px + 0.115, 0.0, 0.34, pz - 0.115, pz + 0.115)

    # ---- mattress + bedding
    bx(m, SHEET, X0 + 0.14, X1 - 0.14, DECK, MATT, ZH + 0.22, ZF - 0.22)
    # The coverlet is a PUFF, not a plane: photo 1 shows a thick quilted
    # coverlet with a rounded roll at every edge and a visible fall down the
    # sides.  A sag_plane read as a bare mattress in the first pass.
    zq0, zq1 = ZH + 0.95, ZF - 0.18
    m.add(puff(X1 - X0 + 0.12, 0.70, zq1 - zq0, r=0.20, seg=16, rings=6,
               nub=0.014, rnd=rnd, anchor="center"), QUILT,
          at=(CX, MATT - 0.02, (zq0 + zq1) / 2))
    # quilt channels
    for i in range(11):
        z = zq0 + 0.30 + i * 0.52
        if z > zq1 - 0.25:
            break
        bx(m, QUILT2, X0 - 0.03, X1 + 0.03, MATT + 0.30, MATT + 0.315,
           z, z + 0.055)
    # turned-back white sheet under the pillows
    m.add(puff(X1 - X0 + 0.08, 0.34, 1.05, r=0.14, seg=14, rings=5,
               nub=0.012, rnd=rnd, anchor="center"), SHEET,
          at=(CX, MATT + 0.14, ZH + 1.35))

    # ---- light blue knit throw, laid across the foot third and falling
    # down the east side (photo 1)
    m.add(puff(X1 - X0 + 0.14, 0.20, 1.45, r=0.09, seg=16, rings=5, nub=0.016,
               rnd=rnd, anchor="center"), BLUE,
          at=(CX, MATT + 0.40, ZF - 2.45))
    m.add(bolster(X1 - X0 + 0.10, 0.045, seg=10, rings=4), BLUE,
          at=(CX, MATT + 0.495, ZF - 3.08))          # the turned-over edge
    m.add(puff(0.24, 1.45, 1.42, r=0.10, seg=9, rings=5, nub=0.016, rnd=rnd,
               anchor="center"), BLUE,
          at=(X0 - 0.07, MATT - 0.34, ZF - 2.35))
    # purple throw folded at the foot (photo 2)
    m.add(puff(1.25, 0.20, 0.86, r=0.09, seg=10, rings=4, nub=0.02, rnd=rnd,
               anchor="center"), PURPLE,
          at=(X1 - 0.95, MATT + 0.44, ZF - 0.85))

    # ---- pillow stack (photo 1): 2 euro shams standing against the
    # headboard, 2 standards in front, a striped lumbar and the floral square
    for cx in (CX - 1.06, CX + 1.06):
        m.add(puff(2.02, 1.98, 0.68, r=0.30, seg=15, rings=8, nub=0.034,
                   rnd=rnd, anchor="center"), PILLOW,
              at=(cx, MATT + 1.02, ZH + 0.62), rot_x=R(8))
    for cx in (CX - 0.98, CX + 0.98):
        m.add(puff(1.86, 1.42, 0.86, r=0.30, seg=15, rings=8, nub=0.036,
                   rnd=rnd, anchor="center"), PILLOW2,
              at=(cx, MATT + 0.70, ZH + 1.28), rot_x=R(21))
    # striped grey lumbar, front row west of centre
    lz, ly = ZH + 2.02, MATT + 0.44
    m.add(puff(2.05, 0.92, 0.58, r=0.19, seg=14, rings=6, nub=0.026,
               rnd=rnd, anchor="center"), GREYST,
          at=(CX - 0.72, ly, lz), rot_x=R(30))
    for i in range(5):
        m.add(box(1.80, 0.085, 0.055), PILLOW,
              at=(CX - 0.72, ly - 0.32 + i * 0.16, lz - 0.19 + i * 0.092),
              rot_x=R(30))
    # black-and-white floral square, front row east of centre (photo 1)
    m.add(puff(1.42, 1.30, 0.54, r=0.20, seg=14, rings=6, nub=0.026,
               rnd=rnd, anchor="center"), FLORAL,
          at=(CX + 1.02, MATT + 0.58, ZH + 1.98), rot_x=R(26))
    for i in range(11):
        m.add(cylinder(rnd.f(0.075, 0.135), 0.012, 7), FLORALD,
              at=(CX + 1.02 + rnd.f(-0.46, 0.46), MATT + 0.58 + rnd.f(-0.42, 0.42),
                  ZH + 1.74 + rnd.f(-0.12, 0.10)),
              rot_x=R(64), rot_z=R(rnd.f(0, 360)))

    shadow(m, rect_foot(X0 - 0.02, X1 + 0.02, ZH + 0.10, ZF + 0.02),
           pad=0.75, a0=0.46, tag="bed")
    return m


# --------------------------------------------------------------- nightstand
TBL = Material("gtbl", "#2a2a2d", roughness=0.55)
SHADE = Material("gshade", "#c9c6c0", roughness=0.85)
LAMPGLASS = Material("glampg", "#dfe4e6", roughness=0.25, opacity=0.55)
BULB = Material("gbulb", "#fff6e2", roughness=0.3, emissive="#ffeec8",
                emissive_strength=2.2)


def nightstand():
    """Small dark table in the NORTH-WEST corner with the white drum lamp
    photo 1 shows beside the headboard, plus a small black frame."""
    m = Model()
    x0, x1, z0, z1 = 0.32, 1.72, 0.30, 1.78
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    bx(m, TBL, x0, x1, 1.78, 1.92, z0, z1)                       # top
    bx(m, TBL, x0 + 0.10, x1 - 0.10, 0.82, 1.78, z0 + 0.10, z1 - 0.10)
    bx(m, Material("gtbl2", "#333336", roughness=0.55),
       x0 + 0.14, x1 - 0.14, 1.18, 1.68, z0 + 0.06, z0 + 0.10)   # drawer front
    bx(m, BLACKMET, cx - 0.20, cx + 0.20, 1.40, 1.47, z0 + 0.03, z0 + 0.07)
    for (px, pz) in ((x0 + 0.09, z0 + 0.09), (x1 - 0.09, z0 + 0.09),
                     (x0 + 0.09, z1 - 0.09), (x1 - 0.09, z1 - 0.09)):
        bx(m, TBL, px - 0.07, px + 0.07, 0.0, 0.86, pz - 0.07, pz + 0.07)
    # lamp: clear glass column, white drum shade
    m.add(cylinder(0.30, 0.07, 16), CHROME, at=(cx, 1.92, cz))
    m.add(cylinder(0.235, 0.86, 16), LAMPGLASS, at=(cx, 1.99, cz))
    m.add(cylinder(0.055, 0.30, 8), CHROME, at=(cx, 2.85, cz))
    m.add(cylinder(0.47, 0.80, 20, r_top=0.42), SHADE, at=(cx, 2.92, cz))
    disc_down(m, BULB, cx, cz, 2.94, 0.40, 16)
    # small black frame leaning on the table
    bx(m, BLACKMET, x1 - 0.72, x1 - 0.14, 1.92, 2.44, z1 - 0.34, z1 - 0.30)
    bx(m, Material("gphoto", "#8e9297", roughness=0.7),
       x1 - 0.67, x1 - 0.19, 1.97, 2.39, z1 - 0.30, z1 - 0.292)
    shadow(m, rect_foot(x0, x1, z0, z1), pad=0.55, a0=0.40, tag="ns")
    return m


if __name__ == "__main__":
    print("room 13 bed group")
    save_and_place("Guest Bed", bed())
    save_and_place("Guest Night Table", nightstand())
