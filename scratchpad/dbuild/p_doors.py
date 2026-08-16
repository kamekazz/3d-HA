"""Dining Openings -- the linings and casing for the two REAL cased openings.

Round 1 painted these on a solid wall ("cased reveals"): from any viewpoint
outside the room they were flat panels, and the dollhouse view showed a sealed
box.  house.js now cuts a genuine hole for a `passage` and draws no panel at
all, so what is left to build is what a doorway actually is -- jamb and head
linings with real depth, and flat casing on the room face.

The linings run AWAY from the room, into the wall cavity, so the casing stays
flush with the wall plane and lands on top of the baseboard instead of floating
half a foot off it.  This renderer has no shadows, so the reveal's depth has to
come from albedo: the lining is a few steps below the casing, which is what a
real jamb in shade reads as anyway.
"""
from dcommon import (Model, box, EDGES, on_edge, TRIM, TRIM_LO, TRIM_SH,
                     E_NORTH, E_EAST, KIT_OP, FOY_OP, XW_WEST, PASS_H, emit)


def wbox(m, mat, i, u0, u1, y0, y1, n0, n1):
    if abs(u1 - u0) < 1e-6 or abs(y1 - y0) < 1e-6 or abs(n1 - n0) < 1e-6:
        return
    x, z = on_edge(i, (u0 + u1) / 2.0, (n0 + n1) / 2.0)
    m.add(box(abs(u1 - u0), abs(y1 - y0), abs(n1 - n0)), mat,
          at=(x, min(y0, y1), z), rot_y=EDGES[i]["rot"])


def cased(m, i, u0, u1, h, depth=0.52, casing=0.40, proud=0.075):
    t = 0.085
    # jamb + head lining, into the wall
    wbox(m, TRIM_LO, i, u0 - t, u0, 0.0, h, -depth, 0.01)
    wbox(m, TRIM_LO, i, u1, u1 + t, 0.0, h, -depth, 0.01)
    wbox(m, TRIM_LO, i, u0 - t, u1 + t, h - t, h, -depth, 0.01)
    # a dark line where the lining meets the far room, so the reveal has a lip
    wbox(m, TRIM_SH, i, u0 - t, u1 + t, h - t, h, -depth - 0.035, -depth)
    # flat casing on the room face + a cap over the head
    wbox(m, TRIM, i, u0 - casing, u0 + 0.01, 0.0, h + casing, 0.0, proud)
    wbox(m, TRIM, i, u1 - 0.01, u1 + casing, 0.0, h + casing, 0.0, proud)
    wbox(m, TRIM, i, u0 - casing, u1 + casing, h, h + casing, 0.0, proud)
    wbox(m, TRIM, i, u0 - casing - 0.05, u1 + casing + 0.05, h + casing,
         h + casing + 0.075, 0.0, proud + 0.05)


if __name__ == "__main__":
    m = Model()
    cased(m, E_NORTH, KIT_OP[0] - XW_WEST, KIT_OP[1] - XW_WEST, PASS_H)
    cased(m, E_EAST, FOY_OP[0], FOY_OP[1], PASS_H)
    emit(m, "Dining Openings", y=0.0)
