"""What you see THROUGH the three real openings.

Round 1 painted the view onto a flush decal stuck on the wall.  Now the wall is
genuinely cut, so the view has to be a board standing OUTSIDE the room -- placed
in room-local coordinates with a negative/over-range offset.  These are hidden
with everything else in House mode (house.js setLevel), and from inside the room
they are only visible through the opening.
"""
from kit2 import *

SKY = Material("lrosky", "#c2cedb", roughness=0.95)
SKY2 = Material("lrosky2", "#d4dce5", roughness=0.95)
TREE = Material("lrotree", "#6c7a62", roughness=0.95)
TREE2 = Material("lrotree2", "#7e8c72", roughness=0.95)
FENCE = Material("lrofence", "#a7a297", roughness=0.9)
RAIL = Material("lrorail", "#d8d3ca", roughness=0.8)
DECK = Material("lrodeck", "#8a8680", roughness=0.9)
GRASS = Material("lrograss", "#7c8663", roughness=0.95)


def view_board(m, axis, at, lo, hi, y0, y1, deck=False):
    """A painted backdrop board. axis 'z' spans x lo..hi at z=at (faces +z);
    axis 'x' spans z lo..hi at x=at."""
    w = hi - lo
    c = (lo + hi) / 2
    h = y1 - y0

    def band(a, b, mat, out=0.0):
        bh = (b - a) * h
        yc = y0 + (1 - b) * h
        if axis == "z":
            m.add(box(w, bh, 0.08), mat, at=(c, yc, at + out))
        else:
            m.add(box(0.08, bh, w), mat, at=(at + out, yc, c))

    if deck:
        for (a, b, mat) in ((0.00, 0.30, SKY2), (0.30, 0.42, SKY),
                            (0.42, 0.66, TREE), (0.66, 0.74, TREE2),
                            (0.74, 0.80, RAIL), (0.80, 1.00, DECK)):
            band(a, b, mat)
        for i in range(14):                    # balusters under the top rail
            u = lo + w * (i + 0.5) / 14
            if axis == "z":
                m.add(box(0.09, 0.055 * h * 4, 0.06), RAIL,
                      at=(u, y0 + 0.20 * h, at + 0.06))
            else:
                m.add(box(0.06, 0.055 * h * 4, 0.09), RAIL,
                      at=(at + 0.06, y0 + 0.20 * h, u))
    else:
        for (a, b, mat) in ((0.00, 0.34, SKY2), (0.34, 0.46, SKY),
                            (0.46, 0.72, TREE), (0.72, 0.82, TREE2),
                            (0.82, 0.90, FENCE), (0.90, 1.00, GRASS)):
            band(a, b, mat)


m = Model()
# behind the patio slider (north wall, opening x 12.00..18.85)
view_board(m, "z", -1.70, 10.60, 20.30, -0.60, 8.40, deck=True)
put_in_place("Living Outdoor View North", m, save(m, "view_n"))

m = Model()
# behind the east window (opening z 1.04..4.02)
view_board(m, "x", 22.20, -0.60, 5.70, 1.20, 8.00)
put_in_place("Living Outdoor View East", m, save(m, "view_e"))

m = Model()
# behind the west window (opening z 11.90..14.90)
view_board(m, "x", -1.70, 10.40, 16.40, 1.20, 8.00)
put_in_place("Living Outdoor View West", m, save(m, "view_w"))
