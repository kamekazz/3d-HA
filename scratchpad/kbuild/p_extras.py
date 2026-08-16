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
    """The runner in front of the range (photos A and F).

    ROUND 3.  Round 1 made it big bright flecks on a dark ground ("confetti");
    round 2 inverted that into a flat light-grey pepper field and the critic read
    it as terrazzo.  Cropping photo F at 2.5x settles it: the rug is a HIGH
    CONTRAST loop weave -- a cream ground carrying dense near-black loops laid in
    rows, with a bound dark edge and a short fringe on the ends.  Measured in the
    photo at 123.7 / sd 36.7; a pepper field cannot reach that spread, so this is
    a rasterised lattice field with real black in it.
    """
    m = Model()
    x0, x1 = 9.95, 12.55
    z0, z1 = 3.70, 8.90

    # near-black -> cream; the ground sits at 4..6 and the loops at 0..2, which
    # is what gives the photo's sd 36.7.  A one-tone pepper field cannot.
    pal = ramp("#141414", "#847f76", 7, "rug", roughness=0.97,
               emissive_lo="#070707", emissive_hi="#1e1c1a")
    bx(m, pal[5], x0, x1, 0.0, 0.038, z0, z1)

    # The GROUND is rasterised (cheap, and it needs no fine detail); the LOOPS
    # are individual rotated quads.  Rasterising the loops too made them square
    # and clumpy -- a mark only 3 px across cannot survive being quantised onto
    # a grid, and the result read as digital camouflage rather than weave.
    def ground(u, w):
        g = fbm(u * 6.5, w * 6.5, 991, 3)
        return 4 if g < 0.34 else (5 if g < 0.74 else 6)

    raster(m, pal, "+y", 0.038, x0 + 0.06, x1 - 0.06, z0 + 0.11, z1 - 0.11,
           0.055, ground, lift=0.002)

    PX, PZ = 0.072, 0.064        # the loop lattice, ~0.85 in pitch
    r = _rng(4242)
    nx, nz = int((x1 - x0 - 0.22) / PX), int((z1 - z0 - 0.30) / PZ)
    for i in range(nx):
        for j in range(nz):
            u = x0 + 0.11 + (i + 0.5) * PX + (r() - 0.5) * PX * 0.55
            w = z0 + 0.15 + (j + 0.5) * PZ + (r() - 0.5) * PZ * 0.55
            dens = 0.29 + 0.19 * fbm((u - x0) * 1.9, (w - z0) * 1.9, 771, 3)
            if r() > dens:
                continue
            a, b = PX * (0.46 + r() * 0.30), PZ * (0.40 + r() * 0.26)
            mat = pal[0] if r() < 0.66 else pal[2]
            m.add(quad((-a, 0, -b), (-a, 0, b), (a, 0, b), (a, 0, -b)), mat,
                  at=(u, 0.0425, w), rot_y=r() * 3.14159)

    # bound (whipped) edge all round, and a short fringe on the two ends
    edge = pal[1]
    for (a, b, c, d) in ((x0, x1, z0, z0 + 0.075), (x0, x1, z1 - 0.075, z1),
                         (x0, x0 + 0.055, z0, z1), (x1 - 0.055, x1, z0, z1)):
        bx(m, edge, a, b, 0.0, 0.046, c, d)
    fr = pal[4]
    n = int((x1 - x0 - 0.20) / 0.058)
    for k in range(n):
        u = x0 + 0.10 + k * 0.058
        L = 0.11 + 0.05 * ((k * 7) % 5) / 4.0
        bx(m, fr, u, u + 0.030, 0.0, 0.013, z0 - L, z0)
        bx(m, fr, u, u + 0.030, 0.0, 0.013, z1, z1 + L)
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
