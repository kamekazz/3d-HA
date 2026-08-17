"""Kitchen Window West (now the real BAY), Kitchen Rug, Kitchen Counter Items,
Kitchen Trash Can.

The footprint re-trace gave the room its three-facet west bay back, and
p_openings.py cuts real window holes in all three facets (edges 4, 3, 2), so
this piece is no longer a flush decal standing in for a bay -- it is the casing,
stool, apron and blinds that dress three genuine openings.
"""
from kcommon import *   # noqa
from kcommon import _rng, edge_info
from ktex import TexModel, TexMaterial, png_gray, tex_plane
import kfield

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

    ROUND 4 -- REGRESSION FIX.  Round 3 built ~1200 individually rotated loop
    quads and the critic measured the result WARM (R-B went -1.9 -> +6.9) and
    too coarse (sd 50.5 -> 56.7 against photo F's honest 39.0): "warm confetti",
    and 392 KB of it.  Round 2's finer neutral speckle read closer to a woven
    mat, so this goes back to that scale and stays strictly neutral.

    A 2.5x crop of photo F shows a pale neutral ground carrying dense SMALL dark
    loops on a jittered offset lattice with visible weave rows -- marks about a
    third of round 3's.  That is a 1.32 x 1.76 ft tiling image at 132 px/ft
    (0.09 in per texel) on one quad: 17 KB, and finer than the geometry could
    ever be, since a 3 px mark cannot survive being drawn as a quad.

    The image is authored in ALBEDO, not render value -- round 3 measured this
    surface at 116.6 from a #141414..#847f76 ramp, so the ramp's own endpoints
    are the calibration and the contrast is simply pulled in to land sd ~40.
    """
    m = TexModel()
    x0, x1 = 9.95, 12.55
    z0, z1 = 3.70, 8.90

    pal = ramp("#141414", "#847f76", 7, "rug", roughness=0.97,
               emissive_lo="#070707", emissive_hi="#1e1c1a")
    bx(m, pal[5], x0, x1, 0.0, 0.038, z0, z1)

    TW, TD = 1.32, 1.76
    weave = kfield.loop_weave(TW, TD, 132, 4242, ground=111.0, loop=108.0,
                              density=0.50, pitch_in=0.42)
    # ROUND 4b -- calibrated, not guessed.  The version above rendered
    # 135.4 / sd 31.2 / R-B +0.4 against photo F's 120.1 / sd 38.1 / R-B -2.2
    # (both at ~90-127 px per foot, native, n=19k and 85k).  Neutral and finer
    # were the two things the critic asked for and both landed; it is simply 15
    # bytes too light and a little too calm.  A floor-facing surface here
    # measures render = 0.89*albedo + 55.3, so 135.4 came off an image mean of
    # 90.0 with an image sd of 35.1, and the photo wants 72.8 / 42.8.  Targeting
    # 45 rather than 42.8 pays for the dark loops the 0..255 clip eats.
    weave = 72.8 + (weave - weave.mean()) * (45.0 / weave.std())
    rmat = TexMaterial("rugweave", png_gray(weave, levels=64), roughness=0.97,
                       emissive="#151413", mip=False)
    tex_plane(m, rmat, "+y", 0.042, x0 + 0.06, x1 - 0.06, z0 + 0.11, z1 - 0.11,
              rep=((x1 - x0 - 0.12) / TW, (z1 - z0 - 0.22) / TD))

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

    # ---- THE PILE ----------------------------------------------------------
    # ROUND 4.  Round 3 laid eight bottles in a tidy evenly-spaced row; a 3x
    # crop of photo F shows a TWO-DEEP chaotic pile against the backsplash --
    # tall cracker/cereal boxes standing at the back, a big yellow-green chip
    # bag standing behind them, a cracker box lying FLAT at the front, a crowd
    # of supplement bottles two rows deep with coloured caps, a teal cloth
    # draped over the front edge, and the knife block hard against them.
    # So: a back row of boxes, a front row of bottles at random depths, and
    # nothing on a shared centre line.
    rnd = _rng(99)

    def mat(name, col, rough=0.72, em="#333333"):
        return Material(name, col, roughness=rough, emissive=em)

    # back row: boxes standing against the backsplash, jittered and touching
    boxes = [("#d8cfc0", 0.30, 0.72, 0.14), ("#c8ac7e", 0.26, 0.62, 0.13),
             ("#b98f8b", 0.30, 0.66, 0.15), ("#8f6f8c", 0.24, 0.56, 0.13),
             ("#d9d3c6", 0.28, 0.70, 0.14), ("#c6b48f", 0.22, 0.52, 0.12)]
    z = 6.92
    for i, (col, w, h, d) in enumerate(boxes):
        x = XWL - 0.16 - d / 2 - rnd() * 0.10
        bx(m, mat(f"bx{i}", col), x - d / 2, x + d / 2, CT, CT + h,
           z, z + w)
        z += w - 0.02 - rnd() * 0.03

    # the chip bag: a tapered prism with a crimped top, standing behind
    bag = mat("chipbag", "#c9cf6a", 0.62, "#3c3f22")
    bx(m, bag, XWL - 0.62, XWL - 0.20, CT, CT + 0.86, 7.72, 8.22)
    bx(m, bag, XWL - 0.52, XWL - 0.30, CT + 0.86, CT + 1.04, 7.80, 8.14)
    bx(m, bag, XWL - 0.50, XWL - 0.32, CT + 1.04, CT + 1.10, 7.86, 8.08)

    # a cracker box lying FLAT at the front of the pile (photo F's blue one)
    bx(m, mat("thins", "#5f7fa8"), XCF + 0.10, XCF + 0.72, CT, CT + 0.17,
       7.05, 7.74)
    bx(m, mat("thinslid", "#8fa7c4"), XCF + 0.12, XCF + 0.70, CT + 0.17,
       CT + 0.19, 7.08, 7.71)

    # the bottle crowd: two ragged rows, mixed heights, coloured caps
    # materials are pooled, not built per item: Model.add groups by material, so
    # 28 unique materials would be 28 primitives for 28 small cylinders.
    caps = [mat(f"cap{k}", c, 0.6, "#2e2e2e") for k, c in
            enumerate(("#d98f6a", "#cf7f9c", "#e0b45c", "#9fb6c6", "#d4d0c6",
                       "#c98fa8"))]
    bodies = [mat(f"btl{k}", c, 0.5, "#3a3a3a") for k, c in
              enumerate(("#e8e5de", "#eae2d0", "#e6e9ea"))]
    for i in range(14):
        r = 0.095 + 0.035 * rnd()
        h = 0.30 + 0.26 * rnd()
        x = XWL - 0.42 - rnd() * 0.72
        zc = 7.02 + i * 0.155 + (rnd() - 0.5) * 0.16
        m.add(cylinder(r, h, seg=12), bodies[i % 3], at=(x, CT, zc))
        m.add(cylinder(r * 0.86, 0.07, seg=10), caps[i % len(caps)],
              at=(x, CT + h, zc))

    # the teal cloth draped over the counter edge in front of the pile
    cloth = mat("cloth", "#7fb5ad", 0.95, "#2b3b39")
    bx(m, cloth, XCF + 0.02, XCF + 0.40, CT, CT + 0.05, 8.28, 8.86)
    bx(m, cloth, XCF + 0.02, XCF + 0.08, CT - 0.30, CT + 0.03, 8.34, 8.80)

    # the wooden knife block, hard against the south end of the pile
    m.add(box(0.62, 0.85, 0.42), WOODBLK, at=(XWL - 0.62, CT, 9.42))
    for i in range(5):
        m.add(box(0.05, 0.34, 0.05), TRIM,
              at=(XWL - 0.86 + i * 0.115, CT + 0.80, 9.35), rot_x=-0.13)

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
