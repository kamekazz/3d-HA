"""Kitchen Cabinets East -- the range wall (photo A left / photo F right).

Room-local: the east wall is x = 14.87 and fronts face WEST (-x).  z runs 2.20
(the peninsula corner) .. 10.60 (finished end panel); everything south of that
is the cased opening to the hallway and its staircase, which photo A shows.

Round-2 fixes carried here:
  * hardware -- round black KNOBS on every door, black bar pulls on drawers only
  * the crown over the uppers is now three stepped runs projecting ~3 in, not a
    thin flat cap
  * the white dishwasher that was on this wall has moved to the peninsula and
    turned black (photo F)
  * counter and backsplash carry real Calacatta veining at ~6 in spacing
"""
from kcommon import *   # noqa

XW = XW_EAST         # wall plane 14.87
XB = 12.87           # base carcase front
XC = 12.72           # countertop front (overhangs the doors)
XU = 13.77           # wall-cabinet front

Z0, Z1 = 2.20, 10.60
RG0, RG1 = 4.30, 6.80        # range slot
END = 10.45                  # finished end panel starts


def build():
    m = Model()

    # ---------------------------------------------------- backsplash (marble)
    # ROUND 3, the critic's headline defect: this was a flat mid-grey field
    # (163 / sd 5.1) with pale stick-marks.  It is now a rasterised cloud field.
    bx(m, MARBLE, XW - 0.055, XW, CT, UP0, 0.0, Z1)
    splash_stone(m, "-x", XW - 0.055, 0.0, Z1, CT, UP0, 4211)

    # ---------------------------------------------------- base run
    for (a, b) in ((Z0, RG0), (RG1, Z1)):
        bx(m, WHITE_LO, XB, XW, TOE, CB, a, b)
        bx(m, BLACK, XB + 0.12, XW, 0.0, TOE, a, b)
    for (a, b) in ((Z0, RG0), (RG1, Z1)):
        bx(m, QUARTZ, XC, XW, CB, CT, a, b)
        top_stone(m, CT, XC + 0.02, XW, a, b, 9137 + int(a * 10))

    # base cabinet north of the range: two doors
    two_door(m, WHITE, "-x", XB, Z0 + 0.05, RG0 - 0.04, TOE + 0.03, CB - 0.03,
             panel=WHITE_LO, pull_y=0.90)
    # south of the range: a wide drawer over a two-door cabinet, then an end unit
    door(m, WHITE, "-x", XB, RG1 + 0.05, 9.36, CB - 0.62, CB - 0.03,
         panel=WHITE_LO, pull=("h", 0.5))
    two_door(m, WHITE, "-x", XB, RG1 + 0.05, 9.36, TOE + 0.03, CB - 0.70,
             panel=WHITE_LO, pull_y=0.86)
    door(m, WHITE, "-x", XB, 9.42, END - 0.04, CB - 0.62, CB - 0.03,
         panel=WHITE_LO, pull=("h", 0.5))
    door(m, WHITE, "-x", XB, 9.42, END - 0.04, TOE + 0.03, CB - 0.70,
         panel=WHITE_LO, pull=("k", 0.16), pull_y=0.90)

    # finished end panel + counter return
    bx(m, WHITE, XB, XW, 0.0, CB, END, Z1)
    bx(m, QUARTZ, XC, XW, CB, CT, END, Z1)

    # ---------------------------------------------------- wall cabinets
    # UPPER doors get VERTICAL BAR PULLS.  Round 1 had them, round 1's critic
    # wrongly called for knobs, round 2 changed all ~30 doors, and round 2's
    # critic re-checked photo F: bar pulls on every upper, knobs on base doors
    # only.  Verified again against the photo before restoring them.
    for (a, b) in ((0.10, 1.95), (1.95, RG0)):
        bx(m, WHITE_LO, XU, XW, UP0, UP1, a, b)
        two_door(m, WHITE, "-x", XU, a + 0.03, b - 0.03, UP0 + 0.03, UP1 - 0.03,
                 pull_y=0.13, kind="v")
    # short cabinet over the microwave
    bx(m, WHITE_LO, XU, XW, 5.98, UP1, RG0, RG1)
    two_door(m, WHITE, "-x", XU, RG0 + 0.03, RG1 - 0.03, 6.01, UP1 - 0.03,
             pull_y=0.20, kind="v")
    for (a, b) in ((RG1, 8.70), (8.70, 10.50)):
        bx(m, WHITE_LO, XU, XW, UP0, UP1, a, b)
        two_door(m, WHITE, "-x", XU, a + 0.03, b - 0.03, UP0 + 0.03, UP1 - 0.03,
                 pull_y=0.13, kind="v")
    bx(m, WHITE, XU - 0.03, XW, UP0 - 0.03, UP0, 0.10, 10.50)

    # ------------------------------------------- built-up crown over the uppers
    # Round 2's four thin steps totalled 0.27 ft of projection and still read as
    # "a thin band"; photo F's is a deep built-up stack with a hard shadow line.
    crown_run(m, TRIM, "-x", XW, XW - XU, 0.06, 10.56, UP1, shadow=SHADOWLN,
              proj=0.30, h=0.62)
    # crown + carcase return down the open south end of the wall run
    bx(m, TRIM, XU - 0.30, XW, UP0, UP1, 10.50, 10.56)

    # ---------------------------------- casing on the hallway opening (photo A)
    # Built with real jamb returns now: the app cuts a genuine hole and draws no
    # panel, so an unframed hole reads as a flat pale slab of the next room.
    cased_opening(m, TRIM, "-x", XW, 11.55, 14.95, 7.20, depth=0.46,
                  casing=0.40, shadow=SHADOWLN)
    return m


if __name__ == "__main__":
    emit(build(), "Kitchen Cabinets East", y=FLOOR_TOP)
