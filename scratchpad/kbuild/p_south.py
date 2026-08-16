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
    # ---- backsplash (ROUND 3: rasterised cloud field, not stick veins)
    bx(m, MARBLE, CX0, CX1, CT, UP0, ZW - 0.055, ZW)
    splash_stone(m, "-z", ZW - 0.055, CX0, CX1, CT, UP0, 6613)

    # ---- base run + counter
    bx(m, WHITE_LO, CX0, CX1, TOE, CB, ZB, ZW)
    bx(m, BLACK, CX0, CX1, 0.0, TOE, ZB + 0.12, ZW)
    bx(m, QUARTZ, CX0, CX1, CB, CT, ZC, ZW)
    top_stone(m, CT, CX0, CX1, ZC + 0.02, ZW, 6619)
    bx(m, WHITE, CX0 - 0.10, CX0, 0.0, CT, ZC, ZW)

    for (a, b) in ((CX0 + 0.05, CX0 + 1.95), (CX0 + 2.02, CX1 - 0.05)):
        door(m, WHITE, "-z", ZB, a, b, CB - 0.60, CB - 0.03,
             panel=WHITE_LO, pull=("h", 0.5))
        two_door(m, WHITE, "-z", ZB, a, b, TOE + 0.03, CB - 0.68,
                 panel=WHITE_LO, pull_y=0.86)
        bx(m, WHITE_LO, a, b, UP0, UP1, ZU, ZW)
        # bar pulls on the uppers -- photo F, see two_door()
        two_door(m, WHITE, "-z", ZU, a + 0.03, b - 0.03, UP0 + 0.03, UP1 - 0.03,
                 pull_y=0.13, kind="v")
    bx(m, WHITE, CX0, CX1, UP0 - 0.03, UP0, ZU - 0.03, ZW)

    # ---- bridge cabinet over the fridge bay + finished flanking panels
    bx(m, WHITE_LO, FX0, FX1, 6.30, UP1, ZU - 0.62, ZW)
    two_door(m, WHITE, "-z", ZU - 0.62, FX0 + 0.05, FX1 - 0.05, 6.33, UP1 - 0.03,
             pull_y=0.20, kind="v")
    bx(m, WHITE, FX0 - 0.09, FX0, 0.0, UP1, ZU - 0.62, ZW)
    bx(m, WHITE, FX1, FX1 + 0.09, 0.0, UP1, ZU - 0.62, ZW)

    # ---- built-up crown right across the run (ROUND 3: chunky, shadow line)
    crown_run(m, TRIM, "-z", ZW, ZW - (ZU - 0.62), CX0 - 0.12, FX1 + 0.09, UP1,
              shadow=SHADOWLN, proj=0.30, h=0.62)

    # ---- small appliances (photos B/C: stainless coffee machine + toaster)
    bx(m, STEEL, CX0 + 0.55, CX0 + 1.55, CT, CT + 1.05, ZW - 1.14, ZW - 0.28)
    bx(m, GLASSBLK, CX0 + 0.62, CX0 + 1.48, CT + 0.10, CT + 0.62,
       ZW - 1.18, ZW - 1.12)
    bx(m, BLACK, CX0 + 0.60, CX0 + 1.50, CT + 0.86, CT + 1.05, ZW - 1.18, ZW - 0.30)
    bx(m, STEEL, CX0 + 2.10, CX0 + 3.10, CT, CT + 0.72, ZW - 1.02, ZW - 0.36)
    bx(m, BLACK, CX0 + 2.16, CX0 + 3.04, CT + 0.72, CT + 0.76, ZW - 0.98, ZW - 0.40)

    # ---- cased opening through to Dining (x 2.58 .. 5.58), with real jamb
    # returns so it reads as a doorway rather than a pale slab of the next room
    cased_opening(m, TRIM, "-z", ZW, 2.58, 5.58, 7.20, depth=0.42, casing=0.28,
                  shadow=SHADOWLN)
    return m


def fridge():
    """ROUND 3: the fridge is what the critic found as "a large PURE BLACK
    surface filling much of the frame" from the south-east pose.  It is not an
    inverted normal -- probe.py raycast the pixel and it is this piece's east
    side face, 1.6 ft from that camera, every material doubleSided.  The cause
    is albedo: #141517 with no emissive is linear 0.006, and a face turned away
    from the single sun lands on literally 0.  The photos' black appliances
    measure 55-134 with grazing reflection, so the body now uses APPL (a lifted
    charcoal with an emissive floor) and the doors carry a lighter sheen band.
    """
    m = Model()
    x0, x1 = FX0 + 0.03, FX1 - 0.03
    bx(m, APPL, x0, x1, 0.0, 5.92, FRZ, ZW)
    bx(m, APPL_LO, x0 + 0.03, x1 - 0.03, 0.10, 2.14, FRZ - 0.075, FRZ)
    bx(m, APPL_HI, x0 + 0.05, x1 - 0.05, 1.62, 1.80, FRZ - 0.079, FRZ - 0.072)
    bx(m, PULL, x0 + 0.20, x1 - 0.20, 1.86, 1.98, FRZ - 0.20, FRZ - 0.08)
    xm = (x0 + x1) / 2.0
    for (a, b) in ((x0 + 0.03, xm - 0.02), (xm + 0.02, x1 - 0.03)):
        bx(m, APPL_LO, a, b, 2.24, 5.86, FRZ - 0.075, FRZ)
        # a broad soft sheen band across the doors: black steel is never flat
        bx(m, APPL_HI, a + 0.04, b - 0.04, 4.30, 4.62, FRZ - 0.079, FRZ - 0.072)
        bx(m, APPL, a + 0.04, b - 0.04, 4.62, 5.05, FRZ - 0.079, FRZ - 0.072)
    bx(m, PULL, xm - 0.30, xm - 0.22, 3.55, 5.55, FRZ - 0.20, FRZ - 0.08)
    bx(m, PULL, xm + 0.22, xm + 0.30, 3.55, 5.55, FRZ - 0.20, FRZ - 0.08)
    scr = Material("screen", "#cfd8dd", roughness=0.18, emissive="#7c868c")
    bx(m, APPL, xm + 0.24, x1 - 0.26, 3.62, 5.28, FRZ - 0.086, FRZ - 0.076)
    bx(m, scr, xm + 0.30, x1 - 0.32, 3.74, 5.16, FRZ - 0.092, FRZ - 0.086)
    bx(m, APPL_HI, x0, x1, 5.86, 5.98, FRZ + 0.02, ZW)
    # the side that faces the hallway opening: keep it a lit charcoal, not a
    # hole -- this is the exact face the critic photographed
    bx(m, APPL_HI, x1 - 0.012, x1, 0.0, 5.92, FRZ, ZW - 0.02)
    return m


if __name__ == "__main__":
    emit(cabinets(), "Kitchen Cabinets South", y=FLOOR_TOP)
    emit(fridge(), "Kitchen Fridge", y=FLOOR_TOP)
