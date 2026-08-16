"""Kitchen Island -- quartz top on a white shaker box, drawers + the beverage
fridge photo B shows on the east (working) face, raised panels on the seating
(west) face and both ends.

Re-sited for the re-traced room: the usable floor is x 2.28..14.87 and the east
counter's front edge is 12.72, so the island sits at x 5.25..9.15 -- a 3.57 ft
work aisle to the range wall, a 3.10 ft aisle to the peninsula and to the fridge
run, and the two stools tuck into the mouth of the west bay.
"""
from kcommon import *   # noqa

CX0, CX1 = 5.25, 9.15        # counter (1.10 ft seating overhang to the west)
CZ0, CZ1 = 5.30, 10.70
BX0, BX1 = 6.35, 8.95        # cabinet body
BZ0, BZ1 = 5.48, 10.52
ICB = 2.86                   # counter underside


def build():
    m = Model()

    # carcase + toe kick (recessed on the working side only)
    bx(m, WHITE_LO, BX0, BX1, TOE, ICB, BZ0, BZ1)
    bx(m, BLACK, BX0, BX1 - 0.10, 0.0, TOE, BZ0 + 0.10, BZ1 - 0.10)
    bx(m, WHITE, BX0 - 0.02, BX0 + 0.02, 0.0, ICB, BZ0, BZ1)   # seating-side skin
    bx(m, WHITE, BX0, BX1, 0.0, TOE, BZ0, BZ0 + 0.10)
    bx(m, WHITE, BX0, BX1, 0.0, TOE, BZ1 - 0.10, BZ1)

    # ---- quartz top: this is the biggest single surface in the room, and the
    # critic metered it as plain white paint.  Heavy continuous veining.
    bx(m, QUARTZ, CX0, CX1, ICB, CT, CZ0, CZ1)
    veins(m, VEIN, "+y", CT + 0.005, CX0 + 0.12, CX1 - 0.12, CZ0 + 0.15,
          CZ1 - 0.15, 31337, thin=0.072, spacing=0.62, angle=1.05)
    # a little veining rolls over the front edge too
    veins(m, VEIN, "-x", CX0 + 0.004, CZ0 + 0.2, CZ1 - 0.2, ICB + 0.02,
          CT - 0.02, 31341, thin=0.026, spacing=0.9, angle=0.5)

    # ---- east (working) face: 3 drawers | beverage fridge | door
    for (a, b) in ((TOE + 0.03, TOE + 0.86), (TOE + 0.92, TOE + 1.72),
                   (TOE + 1.78, ICB - 0.03)):
        door(m, WHITE, "+x", BX1, BZ0 + 0.06, 7.40, a, b,
             panel=WHITE_LO, pull=("h", 0.5))

    bf0, bf1 = 7.48, 9.38                      # beverage fridge
    bx(m, BLACK, BX1 - 0.10, BX1 + 0.03, TOE, ICB - 0.02, bf0, bf1)
    for (a, b) in ((bf0 + 0.05, (bf0 + bf1) / 2 - 0.03),
                   ((bf0 + bf1) / 2 + 0.03, bf1 - 0.05)):
        bx(m, GLASSBLK, BX1 + 0.02, BX1 + 0.05, TOE + 0.06, ICB - 0.08, a, b)
        bx(m, STEEL, BX1 + 0.03, BX1 + 0.07, TOE + 0.06, TOE + 0.10, a, b)
        bx(m, STEEL, BX1 + 0.03, BX1 + 0.07, ICB - 0.12, ICB - 0.08, a, b)
        bx(m, STEEL, BX1 + 0.03, BX1 + 0.07, TOE + 0.06, ICB - 0.08, a, a + 0.04)
        bx(m, STEEL, BX1 + 0.03, BX1 + 0.07, TOE + 0.06, ICB - 0.08, b - 0.04, b)
    shelf = Material("shelf", "#6f7478", roughness=0.5, emissive="#25292c")
    for i in range(4):
        y = TOE + 0.22 + i * 0.52
        bx(m, shelf, BX1 - 0.06, BX1 + 0.01, y, y + 0.05, bf0 + 0.10, bf1 - 0.10)
    for s in (-0.10, 0.06):
        bx(m, STEEL, BX1 + 0.06, BX1 + 0.11, TOE + 0.20, ICB - 0.22,
           (bf0 + bf1) / 2 + s, (bf0 + bf1) / 2 + s + 0.04)

    door(m, WHITE, "+x", BX1, 9.46, BZ1 - 0.06, TOE + 0.03, ICB - 0.03,
         panel=WHITE_LO, pull=("k", 0.14), pull_y=0.90)

    # ---- seating (west) face + ends: decorative raised panels
    for (a, b) in ((BZ0 + 0.10, 7.95), (8.03, BZ1 - 0.10)):
        door(m, WHITE, "-x", BX0 - 0.02, a, b, TOE + 0.10, ICB - 0.06,
             panel=WHITE_LO, rail=0.16, depth=0.02, proud=0.035)
    for face, at in (("-z", BZ0), ("+z", BZ1)):
        door(m, WHITE, face, at, BX0 + 0.10, BX1 - 0.10, TOE + 0.10, ICB - 0.06,
             panel=WHITE_LO, rail=0.16, depth=0.02, proud=0.035)

    # ---- the photo's hero prop: black paper-towel stand
    px, pz = 7.55, 6.55
    m.add(cylinder(0.30, 0.055, seg=20), BLACK, at=(px, CT, pz))
    m.add(cylinder(0.055, 1.05, seg=12), BLACK, at=(px, CT + 0.04, pz))
    paper = Material("paper", "#f7f7f5", roughness=0.9, emissive="#6e6e6e")
    m.add(cylinder(0.235, 0.85, seg=20), paper, at=(px, CT + 0.09, pz))
    m.add(cylinder(0.075, 0.10, seg=10), BLACK, at=(px, CT + 1.06, pz))

    # small white salt + pepper mills
    m.add(cylinder(0.115, 0.52, seg=14, r_top=0.085), TRIM, at=(6.60, CT, 7.55))
    m.add(cylinder(0.100, 0.42, seg=14, r_top=0.075), TRIM, at=(6.82, CT, 7.85))
    return m


if __name__ == "__main__":
    emit(build(), "Kitchen Island", y=FLOOR_TOP)
