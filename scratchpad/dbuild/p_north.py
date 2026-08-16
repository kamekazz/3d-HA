"""Dining Buffet, Dining TV, Dining Side Table -- the north (kitchen) wall.

Photo C is the reference: a black sideboard on eight fronts, a big framed flat
panel centred over it, and on top the deep-red rose ball in a dark vessel, a
black coffee machine, a white tray and a framed print.  Photo B adds the little
black side table standing between the table's east end and the buffet.
"""
import math

from dcommon import (Model, Material, box, rounded_box, cylinder, torus,
                     BLACKLAQ, BLACKLAQ_D, IRON, CHROME, PAPER, ROSE, ROSE_D, TRIM,
                     GLASSY, ESPRESSO_D, GREY_MET,
                     BUF_C, BUF_W, BUF_D, BUF_H, TV_W, TV_H, TV_Y, SIDE_T,
                     bx, emit)

Z0 = 0.06                    # the buffet's back, just off the wall plane
X0, X1 = BUF_C - BUF_W / 2, BUF_C + BUF_W / 2


def front(m, x0, x1, y0, y1, pull="bar"):
    """A recessed door/drawer front with a slim black bar pull.

    The carcase behind is BLACKLAQ_D and the fronts stand proud in BLACKLAQ, so
    the reveal between doors is a real tone step -- without it the whole piece
    rendered as one undifferentiated black mass."""
    bx(m, BLACKLAQ_D, x0, x1, y0, y1, Z0 + BUF_D - 0.075, Z0 + BUF_D - 0.035)
    r = min(0.10, (x1 - x0) / 3.0, (y1 - y0) / 3.0)
    for (a, b, c, d) in ((x0, x1, y0, y0 + r), (x0, x1, y1 - r, y1),
                         (x0, x0 + r, y0, y1), (x1 - r, x1, y0, y1)):
        bx(m, BLACKLAQ, a, b, c, d, Z0 + BUF_D - 0.035, Z0 + BUF_D)
    if pull:
        cx = (x0 + x1) / 2.0
        L = min(0.72, (x1 - x0) * 0.55)
        bx(m, IRON, cx - L / 2, cx + L / 2, (y0 + y1) / 2 - 0.028,
           (y0 + y1) / 2 + 0.028, Z0 + BUF_D, Z0 + BUF_D + 0.052)


def build_buffet():
    m = Model()
    plinth = 0.28
    top = BUF_H
    # recessed plinth, carcase, and a top that overhangs a little
    bx(m, BLACKLAQ_D, X0 + 0.12, X1 - 0.12, 0.0, plinth, Z0 + 0.12, Z0 + BUF_D - 0.10)
    bx(m, BLACKLAQ, X0, X1, plinth, top - 0.085, Z0, Z0 + BUF_D)
    bx(m, BLACKLAQ_D, X0 - 0.05, X1 + 0.05, top - 0.085, top, Z0 - 0.04, Z0 + BUF_D + 0.05)
    # eight fronts on a 4 x 2 grid
    gy = (top - 0.085 - plinth)
    for c in range(4):
        a = X0 + 0.055 + c * (BUF_W - 0.11) / 4
        b = a + (BUF_W - 0.11) / 4 - 0.045
        front(m, a, b, plinth + 0.05, plinth + gy * 0.46 - 0.02)
        front(m, a, b, plinth + gy * 0.46 + 0.02, plinth + gy - 0.05)

    # --- what stands on it (photo C) ----------------------------------------
    y = top
    # dark footed vessel with the deep-red rose ball
    vx = BUF_C - 0.55
    m.add(cylinder(0.30, 0.52, seg=20, r_top=0.36), BLACKLAQ_D, at=(vx, y, 0.85))
    m.add(cylinder(0.42, 0.10, seg=20, r_top=0.30), BLACKLAQ_D, at=(vx, y, 0.85))
    for k in range(150):                      # the ball, as a dense rose dome
        a = 2.399963 * k
        t = (k + 0.5) / 150.0
        yy = 1.0 - 1.55 * t                   # a dome, flat where it meets the pot
        r = math.sqrt(max(0.0, 1.0 - yy * yy))
        m.add(cylinder(0.062, 0.055, seg=6, r_top=0.030),
              ROSE if k % 3 else ROSE_D,
              at=(vx + 0.46 * r * math.cos(a), y + 0.52 + 0.30 + 0.44 * yy,
                  0.85 + 0.46 * r * math.sin(a)))
    # black drip coffee machine
    cx = BUF_C + 1.45
    bx(m, BLACKLAQ, cx - 0.42, cx + 0.42, y, y + 1.02, 0.42, 1.18)
    bx(m, BLACKLAQ_D, cx - 0.34, cx + 0.34, y + 0.06, y + 0.44, 1.18, 1.26)
    bx(m, GREY_MET, cx - 0.30, cx + 0.30, y + 0.72, y + 0.86, 1.18, 1.24)
    # white tray with a couple of things on it
    bx(m, PAPER, BUF_C - 2.15, BUF_C - 1.15, y, y + 0.075, 0.55, 1.30)
    m.add(cylinder(0.18, 0.36, seg=14), PAPER, at=(BUF_C - 1.90, y + 0.075, 0.92))
    m.add(cylinder(0.14, 0.26, seg=14), GLASSY, at=(BUF_C - 1.45, y + 0.075, 0.80))
    # a small framed print leaning on the wall behind
    m.add(box(0.86, 0.62, 0.045), TRIM, at=(BUF_C - 2.30, y + 0.02, 0.24),
          rot_x=math.radians(-7))
    m.add(box(0.72, 0.48, 0.02), GREY_MET, at=(BUF_C - 2.30, y + 0.09, 0.27),
          rot_x=math.radians(-7))
    return m


def build_tv():
    """A framed flat panel over the buffet.  The frame is a BORDER, not a slab:
    a full rectangle in front of the screen renders as a blank white panel."""
    m = Model()
    x0, x1 = BUF_C - TV_W / 2, BUF_C + TV_W / 2
    y0, y1 = TV_Y, TV_Y + TV_H
    f = 0.115
    bx(m, BLACKLAQ_D, x0 + f, x1 - f, y0 + f, y1 - f, 0.035, 0.075)   # screen
    for (a, b, c, d) in ((x0, x1, y0, y0 + f), (x0, x1, y1 - f, y1),
                         (x0, x0 + f, y0, y1), (x1 - f, x1, y0, y1)):
        bx(m, TRIM, a, b, c, d, 0.020, 0.100)                          # frame
    bx(m, BLACKLAQ, x0 + f, x1 - f, y0 + f, y1 - f, 0.075, 0.085)
    return m


def build_side_table():
    """The little black side table between the dining table and the buffet."""
    m = Model()
    sx, sz = SIDE_T
    h, w = 1.85, 1.16
    for (dx, dz) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        m.add(box(0.10, h - 0.09, 0.10), BLACKLAQ_D,
              at=(sx + dx * (w / 2 - 0.09), 0.0, sz + dz * (w / 2 - 0.09)))
    bx(m, BLACKLAQ, sx - w / 2, sx + w / 2, h - 0.09, h, sz - w / 2, sz + w / 2)
    bx(m, BLACKLAQ_D, sx - w / 2 + 0.10, sx + w / 2 - 0.10, 0.72, 0.80,
       sz - w / 2 + 0.10, sz + w / 2 - 0.10)
    # a stack of mail and a small dark box, because nothing in this house is bare
    bx(m, PAPER, sx - 0.34, sx + 0.28, h, h + 0.09, sz - 0.26, sz + 0.24)
    bx(m, BLACKLAQ_D, sx - 0.10, sx + 0.36, h + 0.09, h + 0.44, sz - 0.12, sz + 0.30)
    return m


if __name__ == "__main__":
    emit(build_buffet(), "Dining Buffet", y=0.0)
    emit(build_tv(), "Dining TV", y=TV_Y)
    emit(build_side_table(), "Dining Side Table", y=0.0)
