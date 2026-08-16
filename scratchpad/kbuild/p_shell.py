"""Kitchen Ceiling + Kitchen Baseboards, re-cut for the polygon footprint.

Ceiling is ONE downward-facing plane (CEIL is double_sided=False) so it is
solid at eye level and invisible from the dollhouse/plan pose -- you must still
see the floor from above.  Crown runs every edge of the polygon, including the
three bay facets.

Recessed cans: SIX.  Round 1 put ten in a room that was 10 ft too deep; the
photos show four to six over a kitchen this size, and a critic counted ours.
"""
from kcommon import *   # noqa

Y = CEIL_Y          # 8.97

# openings, as (edge, u0, u1) -- baseboard and crown stop at a cased opening
DOOR_GAPS = {
    E_NORTH: [(0.15, 3.30)],
    E_EAST:  [(11.55, 14.95)],
    E_SOUTH: [(9.29, 12.29)],
}


def _runs(edge, length):
    gaps = sorted(DOOR_GAPS.get(edge, []))
    out, u = [], 0.0
    for a, b in gaps:
        if a - u > 0.02:
            out.append((u, a))
        u = b
    if length - u > 0.02:
        out.append((u, length))
    return out


def ceiling():
    m = Model()
    # main rectangle + the bay, both wound so the normal points DOWN
    m.add(quad((XW_WEST, Y, 0), (XW_EAST, Y, 0),
               (XW_EAST, Y, ZW_SOUTH), (XW_WEST, Y, ZW_SOUTH)), CEIL)
    m.add(quad((0.0, Y, 4.51), (XW_WEST, Y, 3.35),
               (XW_WEST, Y, 11.16), (0.0, Y, 10.0)), CEIL)

    # ---- crown: three steps, ~3 in of projection, all eight edges
    for i in range(len(POLY)):
        e = edge_info(i)
        for u0, u1 in _runs(i, e["len"]):
            edge_box(m, CEIL_TRIM, i, 8.52, 8.63, 0.245, u0, u1)
            edge_box(m, CEIL_TRIM, i, 8.63, 8.76, 0.185, u0, u1)
            edge_box(m, CEIL_TRIM, i, 8.76, Y, 0.100, u0, u1)

    # ---- six recessed cans, back-projected off photos A and F.
    # ROUND 4: FLAT DOWN-FACING DISCS, not cylinders.  The ceiling plane is
    # one-sided so the dollhouse camera can see into the room; that left the
    # cans as the only ceiling geometry visible from above, and the critic read
    # six white cylinders as "golf balls on the counters and floor".  A 2.6x
    # crop of photo F shows the real cans as an almost flush ring in the
    # plaster anyway, with no visible housing.
    for (cx, cz) in ((12.10, 2.55), (12.35, 8.10), (7.30, 3.30),
                     (7.05, 9.40), (5.35, 13.60), (11.60, 13.90)):
        m.add(disc_down(0.30, Y - 0.004, cx, cz), CEIL_TRIM_1S)
        m.add(disc_down(0.235, Y - 0.012, cx, cz), GLOW)

    # the round ceiling diffuser photo F shows at the living-room end
    m.add(disc_down(0.50, Y - 0.004, 4.10, 2.05, seg=24), CEIL_TRIM_1S)
    m.add(disc_down(0.40, Y - 0.016, 4.10, 2.05, seg=24), CEIL_TRIM_1S)
    return m


def baseboards():
    m = Model()
    h, cap, p = 0.46, 0.055, 0.075
    for i in range(len(POLY)):
        e = edge_info(i)
        for u0, u1 in _runs(i, e["len"]):
            edge_box(m, TRIM, i, 0.0, h - cap, p, u0, u1)
            edge_box(m, TRIM, i, h - cap, h, p - 0.012, u0, u1)
    return m


if __name__ == "__main__":
    import sys
    which = sys.argv[1:] or ["ceiling", "base"]
    if "ceiling" in which:
        emit(ceiling(), "Kitchen Ceiling")
    if "base" in which:
        emit(baseboards(), "Kitchen Baseboards", y=FLOOR_TOP)
