"""Kitchen Window West (now the real BAY), Kitchen Rug, Kitchen Counter Items,
Kitchen Trash Can.

The footprint re-trace gave the room its three-facet west bay back, and
p_openings.py cuts real window holes in all three facets (edges 4, 3, 2), so
this piece is no longer a flush decal standing in for a bay -- it is the casing,
stool, apron and blinds that dress three genuine openings.
"""
from kcommon import *   # noqa
from kcommon import _rng, edge_info

BAY = [(E_BAY_N, 0.53, 2.03), (E_BAY_F, 0.45, 5.04), (E_BAY_S, 0.53, 2.03)]
WY0, WY1 = 2.20, 6.50        # opening elevation .. head


def window():
    m = Model()
    for edge, u0, u1 in BAY:
        # casing: jambs + head, standing 0.13 ft proud of the wall plane
        for a, b in ((u0 - 0.16, u0), (u1, u1 + 0.16)):
            edge_box(m, TRIM, edge, WY0 - 0.30, WY1 + 0.16, 0.13, a, b)
        edge_box(m, TRIM, edge, WY1, WY1 + 0.16, 0.13, u0 - 0.16, u1 + 0.16)
        # stool (sill) + apron
        edge_box(m, TRIM, edge, WY0 - 0.10, WY0, 0.34, u0 - 0.26, u1 + 0.26)
        edge_box(m, TRIM, edge, WY0 - 0.34, WY0 - 0.10, 0.18, u0 - 0.14, u1 + 0.14)
        # a faint pane behind the app's own glass panel, so the opening still
        # reads as glazed when the camera is off-axis
        edge_box(m, GLASS, edge, WY0 + 0.02, WY1 - 0.02, 0.02,
                 u0 + 0.04, u1 - 0.04, out=0.03)
        # white 2 in horizontal blinds, drawn most of the way down
        n = 17
        for s in range(n):
            y = WY1 - 0.16 - s * (WY1 - WY0 - 0.95) / n
            edge_box(m, TRIM, edge, y, y + 0.045, 0.075, u0 + 0.05, u1 - 0.05,
                     out=0.055)
        edge_box(m, TRIM, edge, WY1 - 0.20, WY1 - 0.06, 0.11, u0 + 0.02,
                 u1 - 0.02, out=0.04)   # headrail
    return m


def rug():
    """The black/white flecked runner in front of the range (photos A and F)."""
    m = Model()
    x0, x1 = 9.95, 12.55
    z0, z1 = 3.70, 8.90
    base = Material("rugbase", "#616362", roughness=0.97, emissive="#242525")
    dark = Material("rugdark", "#333534", roughness=0.97, emissive="#0d0d0d")
    bx(m, base, x0, x1, 0.0, 0.040, z0, z1)
    rnd = _rng(4242)
    for _ in range(2600):
        u = x0 + 0.10 + rnd() * (x1 - x0 - 0.20)
        w = z0 + 0.10 + rnd() * (z1 - z0 - 0.20)
        s = 0.010 + rnd() * 0.014
        m.add(box(s, 0.004, s * 0.75), dark, at=(u, 0.038, w), rot_y=rnd() * 3.1)
    bx(m, dark, x0, x1, 0.0, 0.042, z0, z0 + 0.14)
    bx(m, dark, x0, x1, 0.0, 0.042, z1 - 0.14, z1)
    return m


def counter_items():
    """The clutter band photos A and F both show along the east counter south of
    the range, plus the kettle on the cooktop and the dark bowls by the sink."""
    m = Model()
    XCF, XWL = 12.72, 14.87

    # kettle on the front-left burner
    m.add(cylinder(0.30, 0.46, seg=18, r_top=0.22), TRIM, at=(13.30, 3.06, 4.94))
    m.add(cylinder(0.075, 0.13, seg=10), BLACK, at=(13.30, 3.52, 4.94))
    m.add(box(0.045, 0.20, 0.50), BLACK, at=(13.30, 3.50, 4.94))

    palette = [
        ("#c98a86", 0.34, 0.58, 0.20), ("#eee6d4", 0.28, 0.50, 0.18),
        ("#aec4d4", 0.32, 0.54, 0.22), ("#e2cf9c", 0.26, 0.44, 0.17),
        ("#c3b0c4", 0.30, 0.56, 0.20), ("#e9e6e0", 0.24, 0.42, 0.17),
        ("#a8c4b2", 0.28, 0.50, 0.20), ("#dcc3b3", 0.26, 0.48, 0.19),
    ]
    z = 6.95
    rnd = _rng(99)
    for i, (col, w, h, d) in enumerate(palette):
        mat = Material(f"pk{i}", col, roughness=0.72, emissive="#333333")
        x = XWL - 0.34 - rnd() * 0.55
        bx(m, mat, x - w / 2, x + w / 2, CT, CT + h, z, z + d)
        z += d + 0.055
    for i in range(6):
        mat = Material(f"jr{i}", ["#e6e3dc", "#cfd8d4", "#e9d7b8"][i % 3],
                       roughness=0.5, emissive="#3a3a3a")
        m.add(cylinder(0.11 + 0.02 * (i % 3), 0.42 + 0.10 * (i % 2), seg=12), mat,
              at=(XWL - 0.55 - 0.30 * (i % 2), CT, 7.10 + i * 0.24))
    m.add(box(0.62, 0.85, 0.42), WOODBLK, at=(XWL - 0.62, CT, 9.65))
    for i in range(5):
        m.add(box(0.05, 0.34, 0.05), TRIM,
              at=(XWL - 0.86 + i * 0.115, CT + 0.80, 9.58), rot_x=-0.13)

    # dark serving bowls + a small plant on the peninsula, by the sink (photo F)
    m.add(cylinder(0.36, 0.20, seg=18, r_top=0.44), BLACK, at=(12.30, CT, 1.05))
    m.add(cylinder(0.30, 0.16, seg=18, r_top=0.36), BLACK, at=(13.05, CT, 0.80))
    m.add(cylinder(0.26, 0.30, seg=14, r_top=0.30), TRIM, at=(11.30, CT, 0.85))
    for i in range(7):
        m.add(rounded_box(0.42, 0.10, 0.30, r=0.05, seg=3), GREEN,
              at=(11.30 + math.cos(i) * 0.22, CT + 0.32 + (i % 3) * 0.13,
                  0.85 + math.sin(i) * 0.20), rot_y=i * 0.9, rot_z=0.35)
    return m


def trash():
    """The brushed-steel step bin standing in the bay in photo C."""
    m = Model()
    x, z = 1.15, 5.30
    m.add(cylinder(0.62, 2.05, seg=22, r_top=0.58), STEEL, at=(x, 0.0, z))
    m.add(cylinder(0.60, 0.10, seg=22), BLACK, at=(x, 2.05, z))
    m.add(cylinder(0.56, 0.07, seg=22), STEEL, at=(x, 2.13, z))
    m.add(box(0.30, 0.06, 0.10), BLACK, at=(x + 0.42, 0.12, z))
    return m


if __name__ == "__main__":
    import sys
    which = sys.argv[1:] or ["window", "rug", "items", "trash"]
    if "trash" in which:
        emit(trash(), "Kitchen Trash Can", y=FLOOR_TOP)
    if "window" in which:
        emit(window(), "Kitchen Window West")
    if "rug" in which:
        emit(rug(), "Kitchen Rug", y=FLOOR_TOP + 0.002)
    if "items" in which:
        emit(counter_items(), "Kitchen Counter Items", y=CT + FLOOR_TOP)
