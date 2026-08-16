"""Kitchen Fridge + Kitchen Cabinets South -- the far wall of photo A.

ROUND-2: round 1 stood a FAKE 9 ft partial wall across the middle of the room
at z 17.40 because the traced footprint was 10 ft deeper than the photographed
kitchen, and left the remainder bare -- a critic called that "a room someone
stopped furnishing".  The footprint has since been re-traced to 16.74 ft deep,
so the fake wall is GONE and this run stands against the real south wall.

Fronts face NORTH (-z).  The opening through to Dining is a real cut hole at
x 2.58..5.58 (p_openings.py, edge 0).
"""
from kcommon import *   # noqa

ZW = ZW_SOUTH           # 16.74, the real wall
ZB = ZW - 2.00          # base carcase front
ZC = ZW - 2.15          # counter front edge
ZU = ZW - 1.10          # wall cabinet front
CX0, CX1 = 5.90, 9.90           # counter run
FX0, FX1 = 9.90, 12.95          # fridge bay
FRZ = ZW - 2.95                 # fridge front


def cabinets():
    m = Model()
    # ---- backsplash
    bx(m, MARBLE, CX0, CX1, CT, UP0, ZW - 0.055, ZW)
    veins(m, VEIN, "-z", ZW - 0.055, CX0 + 0.25, CX1 - 0.25, CT + 0.2, UP0 - 0.2,
          6613, thin=0.038, spacing=0.55, angle=1.15)

    # ---- base run + counter
    bx(m, WHITE_LO, CX0, CX1, TOE, CB, ZB, ZW)
    bx(m, BLACK, CX0, CX1, 0.0, TOE, ZB + 0.12, ZW)
    bx(m, QUARTZ, CX0, CX1, CB, CT, ZC, ZW)
    veins(m, VEIN, "+y", CT + 0.005, CX0 + 0.25, CX1 - 0.25, ZC + 0.2, ZW - 0.2,
          6619, thin=0.062, spacing=0.62, angle=0.95)
    bx(m, WHITE, CX0 - 0.10, CX0, 0.0, CT, ZC, ZW)

    for (a, b) in ((CX0 + 0.05, CX0 + 1.95), (CX0 + 2.02, CX1 - 0.05)):
        door(m, WHITE, "-z", ZB, a, b, CB - 0.60, CB - 0.03,
             panel=WHITE_LO, pull=("h", 0.5))
        two_door(m, WHITE, "-z", ZB, a, b, TOE + 0.03, CB - 0.68,
                 panel=WHITE_LO, pull_y=0.86)
        bx(m, WHITE_LO, a, b, UP0, UP1, ZU, ZW)
        two_door(m, WHITE, "-z", ZU, a + 0.03, b - 0.03, UP0 + 0.03, UP1 - 0.03,
                 pull_y=0.13)
    bx(m, WHITE, CX0, CX1, UP0 - 0.03, UP0, ZU - 0.03, ZW)

    # ---- bridge cabinet over the fridge bay + finished flanking panels
    bx(m, WHITE_LO, FX0, FX1, 6.30, UP1, ZU - 0.62, ZW)
    two_door(m, WHITE, "-z", ZU - 0.62, FX0 + 0.05, FX1 - 0.05, 6.33, UP1 - 0.03,
             pull_y=0.17)
    bx(m, WHITE, FX0 - 0.09, FX0, 0.0, UP1, ZU - 0.62, ZW)
    bx(m, WHITE, FX1, FX1 + 0.09, 0.0, UP1, ZU - 0.62, ZW)

    # ---- stepped crown right across the run
    for (dz, y0, y1) in ((0.09, UP1, 8.22), (0.19, 8.22, 8.36),
                         (0.27, 8.36, 8.48), (0.20, 8.48, CR1)):
        bx(m, TRIM, CX0 - 0.12, FX1 + 0.09, y0, y1, ZU - 0.62 - dz, ZW)

    # ---- small appliances (photos B/C: stainless coffee machine + toaster)
    bx(m, STEEL, CX0 + 0.55, CX0 + 1.55, CT, CT + 1.05, ZW - 1.14, ZW - 0.28)
    bx(m, GLASSBLK, CX0 + 0.62, CX0 + 1.48, CT + 0.10, CT + 0.62,
       ZW - 1.18, ZW - 1.12)
    bx(m, BLACK, CX0 + 0.60, CX0 + 1.50, CT + 0.86, CT + 1.05, ZW - 1.18, ZW - 0.30)
    bx(m, STEEL, CX0 + 2.10, CX0 + 3.10, CT, CT + 0.72, ZW - 1.02, ZW - 0.36)
    bx(m, BLACK, CX0 + 2.16, CX0 + 3.04, CT + 0.72, CT + 0.76, ZW - 0.98, ZW - 0.40)

    # ---- casing on the cut opening through to Dining (x 2.58 .. 5.58)
    for (a, b) in ((2.43, 2.60), (5.56, 5.73)):
        bx(m, TRIM, a, b, 0.0, 7.32, ZW - 0.14, ZW)
    bx(m, TRIM, 2.43, 5.73, 7.20, 7.32, ZW - 0.14, ZW)
    return m


def fridge():
    m = Model()
    x0, x1 = FX0 + 0.03, FX1 - 0.03
    body = Material("fridgeblk", "#141517", roughness=0.30, metallic=0.35)
    bx(m, body, x0, x1, 0.0, 5.92, FRZ, ZW)
    bx(m, GLASSBLK, x0 + 0.03, x1 - 0.03, 0.10, 2.14, FRZ - 0.075, FRZ)
    bx(m, PULL, x0 + 0.20, x1 - 0.20, 1.86, 1.98, FRZ - 0.20, FRZ - 0.08)
    xm = (x0 + x1) / 2.0
    for (a, b) in ((x0 + 0.03, xm - 0.02), (xm + 0.02, x1 - 0.03)):
        bx(m, GLASSBLK, a, b, 2.24, 5.86, FRZ - 0.075, FRZ)
    bx(m, PULL, xm - 0.30, xm - 0.22, 3.55, 5.55, FRZ - 0.20, FRZ - 0.08)
    bx(m, PULL, xm + 0.22, xm + 0.30, 3.55, 5.55, FRZ - 0.20, FRZ - 0.08)
    scr = Material("screen", "#cfd8dd", roughness=0.18, emissive="#7c868c")
    bx(m, body, xm + 0.24, x1 - 0.26, 3.62, 5.28, FRZ - 0.086, FRZ - 0.076)
    bx(m, scr, xm + 0.30, x1 - 0.32, 3.74, 5.16, FRZ - 0.092, FRZ - 0.086)
    bx(m, body, x0, x1, 5.86, 5.98, FRZ + 0.02, ZW)
    return m


if __name__ == "__main__":
    emit(cabinets(), "Kitchen Cabinets South", y=FLOOR_TOP)
    emit(fridge(), "Kitchen Fridge", y=FLOOR_TOP)
