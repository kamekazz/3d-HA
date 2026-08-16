"""Kitchen Cabinets North -- the sink peninsula, built as a HALF WALL.

The critic's top defect: "the kitchen is sealed off.  Photos C and F are defined
by looking over a half-wall pass-through to the living room and its stone
fireplace; ours is a solid full-height wall."  p_openings.py now cuts the real
hole (edge 6, y 3.30..7.60); this piece builds what stands under it -- a
counter-height wall with its own painted back so it reads as solid from both
sides, capped by the quartz that carries the sink.

Second defect fixed here: the DISHWASHER.  Photo F shows a BLACK dishwasher
front under the peninsula immediately LEFT (west) of the sink.  Round 1 put a
white panel-front one on the east wall.

Fronts face SOUTH (+z).  x 5.75 .. 14.87, z -0.20 .. 2.20.
"""
from kcommon import *   # noqa

ZW = 0.0             # wall plane
ZBACK = -0.17        # painted back of the half wall (living-room side)
ZB = 2.03            # base carcase front
ZC = 2.20            # counter front edge
X0, X1 = 5.75, XW_EAST
HW0, HW1 = 6.03, 13.48       # the pass-through opening's extent
HWY = 3.30                   # top of the half wall = opening elevation

DW0, DW1 = 5.90, 7.90        # dishwasher
SB0, SB1 = 7.90, 10.85       # sink base
SX0, SX1 = 8.35, 10.45       # sink cut-out
SZ0, SZ1 = 0.42, 1.84


def build():
    m = Model()

    # ---- the half wall's painted back + the jambs of the two openings ------
    bx(m, WALLPT, HW0, HW1, 0.0, HWY, ZBACK, ZW)
    bx(m, WALLPT, HW0 - 0.14, HW0, 0.0, 7.60, ZBACK, ZW)     # east jamb of walk-through
    bx(m, WALLPT, HW1, HW1 + 0.14, 0.0, 7.60, ZBACK, ZW)     # west jamb of the corner
    bx(m, WALLPT, HW0, HW1, 7.60, 7.74, ZBACK, ZW)           # header over the opening
    bx(m, TRIM, 2.43 - 0.10, 2.43, 0.0, 7.70, ZBACK, ZW)     # walk-through casing
    bx(m, TRIM, 5.58, 5.58 + 0.10, 0.0, 7.70, ZBACK, ZW)
    bx(m, TRIM, 2.33, 5.68, 7.60, 7.70, ZBACK, ZW)

    # ---- backsplash east of the pass-through (that corner stays full height)
    bx(m, MARBLE, HW1, X1, CT, UP0, ZW, ZW + 0.055)
    veins(m, VEIN, "+z", ZW + 0.055, HW1 + 0.2, X1 - 0.2, CT + 0.2, UP0 - 0.2,
          8821, thin=0.038, spacing=0.55, angle=1.15)

    # ---- carcase + toe kick
    bx(m, WHITE_LO, X0, X1, TOE, CB, ZW + 0.06, ZB)
    bx(m, BLACK, X0 + 0.10, X1, 0.0, TOE, ZW + 0.06, ZB - 0.12)

    # ---- countertop, built round the sink opening, capping the half wall
    for (a, b, c, d) in ((X0, SX0, ZBACK - 0.03, ZC), (SX1, X1, ZBACK - 0.03, ZC),
                         (SX0, SX1, ZBACK - 0.03, SZ0), (SX0, SX1, SZ1, ZC)):
        bx(m, QUARTZ, a, b, CB, CT, c, d)
    for (a, b, sd) in ((X0 + 0.3, SX0 - 0.2, 5501), (SX1 + 0.2, X1 - 0.3, 5507)):
        veins(m, VEIN, "+y", CT + 0.005, a, b, ZBACK + 0.15, ZC - 0.15, sd,
              thin=0.062, spacing=0.62, angle=1.15)
    # low marble curb along the pass-through side, as in photo F
    bx(m, MARBLE, HW0, HW1, CT, CT + 0.34, ZBACK - 0.03, ZBACK + 0.10)

    # ---- undermount stainless sink
    bx(m, STEEL, SX0, SX1, 2.36, CB, SZ0, SZ1)
    for (a, b, c, d) in ((SX0, SX0 + 0.05, SZ0, SZ1), (SX1 - 0.05, SX1, SZ0, SZ1),
                         (SX0, SX1, SZ0, SZ0 + 0.05), (SX0, SX1, SZ1 - 0.05, SZ1)):
        bx(m, STEEL, a, b, 2.36, CB + 0.005, c, d)
    bx(m, STEEL, SX0 + 0.05, SX1 - 0.05, 2.36, 2.42, SZ0 + 0.05, SZ1 - 0.05)
    m.add(cylinder(0.075, 0.03, seg=12), PULL,
          at=((SX0 + SX1) / 2, 2.41, (SZ0 + SZ1) / 2))

    # ---- black gooseneck faucet + soap dispenser (photo F)
    fx, fz = (SX0 + SX1) / 2.0 - 0.08, ZW + 0.28
    m.add(cylinder(0.115, 0.10, seg=16), BLACK, at=(fx, CT, fz))
    m.add(cylinder(0.058, 0.92, seg=14), BLACK, at=(fx, CT + 0.08, fz))
    arc_tube(m, BLACK, 0.42, fx, CT + 1.00, fz, 0.0, math.pi / 2 * 0.94, 8, 0.052)
    m.add(cylinder(0.050, 0.30, seg=12), BLACK, at=(fx, CT + 0.72, fz + 0.42))
    m.add(cylinder(0.068, 0.09, seg=12), BLACK, at=(fx, CT + 0.68, fz + 0.42))
    m.add(cylinder(0.035, 0.30, seg=10), BLACK, at=(fx + 0.10, CT + 0.28, fz),
          rot_z=-1.1)
    m.add(cylinder(0.055, 0.34, seg=12), BLACK, at=(fx - 0.62, CT, fz))
    m.add(box(0.10, 0.05, 0.16), BLACK, at=(fx - 0.62, CT + 0.32, fz + 0.06))

    # ---- BLACK dishwasher, immediately west of the sink (photo F) ----------
    DWM = Material("dwblack", "#141517", roughness=0.34, metallic=0.38)
    door(m, DWM, "+z", ZB, DW0 + 0.04, DW1 - 0.04, 0.30, CB - 0.02,
         rail=0.075, depth=0.030, proud=0.016, panel=GLASSBLK)
    bx(m, DWM, DW0 + 0.10, DW1 - 0.10, CB - 0.20, CB - 0.10, ZB + 0.06, ZB + 0.16)
    bx(m, PULL, DW0 + 0.14, DW1 - 0.14, CB - 0.19, CB - 0.11, ZB + 0.13, ZB + 0.19)
    ctrl = Material("dwctrl", "#3a3d41", roughness=0.4)
    bx(m, ctrl, DW0 + 0.30, DW0 + 0.95, CB - 0.09, CB - 0.05, ZB + 0.04, ZB + 0.07)

    # ---- doors: sink base | drawer over two-door | corner base ------------
    two_door(m, WHITE, "+z", ZB, SB0 + 0.04, SB1 - 0.04, TOE + 0.03, CB - 0.03,
             panel=WHITE_LO, pull_y=0.90)
    for (a, b) in ((10.90, 12.96), (13.02, X1 - 0.04)):
        door(m, WHITE, "+z", ZB, a, b, CB - 0.60, CB - 0.03,
             panel=WHITE_LO, pull=("h", 0.5))
        two_door(m, WHITE, "+z", ZB, a, b, TOE + 0.03, CB - 0.68,
                 panel=WHITE_LO, pull_y=0.86)

    # ---- finished west end panel, returning down to the floor
    bx(m, WHITE, X0 - 0.10, X0, 0.0, CT, ZBACK, ZC)
    bx(m, QUARTZ, X0 - 0.14, X0, CB, CT, ZBACK - 0.03, ZC)
    return m


if __name__ == "__main__":
    emit(build(), "Kitchen Cabinets North", y=FLOOR_TOP)
