"""Garage -- WEST wall run: tall cabinets, workbench + pegboard, shelving.

The 2-D floor plan (docs/floor plan/Main Floor Plan App.png) shows a ~2.4 ft
deep, ~8.5 ft long storage run against the garage's west wall (world
x 19.2-21.6, z 20.5-29.0 = local x 0.3-2.7, z 7.5-16.0).  Everything here is
built onto that evidence; the individual items are normal-garage inference.
"""
from gkit import *   # noqa: F401,F403
import gkit as G

ROOM = 7

# ------------------------------------------------------------ tall cabinets
def cabinets():
    m = Model()
    z0, z1, H, DEEP = 1.70, 5.70, 6.60, 1.90
    # carcass
    bx(m, G.WHITE_A, 0.10, 0.10 + DEEP, 0.0, H, z0, z1)
    # toe kick shadow
    bx(m, G.BLK, 0.10, 0.10 + DEEP, 0.0, 0.30, z0 + 0.02, z1 - 0.02)
    # four graphite doors, two banks
    for (a, b) in ((z0 + 0.05, z0 + 1.95), (z0 + 2.05, z1 - 0.05)):
        for (y0, y1) in ((0.32, 3.62), (3.70, H - 0.06)):
            bx(m, G.GRAPH, 0.10 + DEEP, 0.10 + DEEP + 0.055, y0, y1, a, b)
            # centre gap between the leaves of each bank
            mid = (a + b) / 2
            bx(m, G.GRAPH_L, 0.10 + DEEP, 0.10 + DEEP + 0.058,
               y0 + 0.03, y1 - 0.03, mid - 0.018, mid + 0.018)
            # bar pulls
            for hz in (mid - 0.13, mid + 0.13):
                bx(m, G.BLK, 0.10 + DEEP + 0.055, 0.10 + DEEP + 0.135,
                   (y0 + y1) / 2 - 0.42, (y0 + y1) / 2 + 0.42, hz - 0.028, hz + 0.028)
    # crown-ish top cap
    bx(m, G.WHITE, 0.08, 0.10 + DEEP + 0.10, H - 0.10, H, z0 - 0.05, z1 + 0.05)
    # clutter on top: two card boxes and a bin
    bx(m, G.CARD, 0.35, 1.55, H, H + 0.95, z0 + 0.25, z1 - 2.35)
    bx(m, G.CARD, 0.30, 1.45, H, H + 0.72, z0 + 2.05, z1 - 0.30)
    bx(m, G.YELLOW, 0.35, 1.50, H + 0.95, H + 1.06, z0 + 0.25, z1 - 2.35)
    return m


# ---------------------------------------------------------------- workbench
def workbench():
    m = Model()
    z0, z1 = 6.30, 13.30
    x0, x1 = 0.10, 2.60
    TOP = 3.00

    # --- pegboard + upper shelf on the wall
    bx(m, G.PEG, x0 - 0.02, x0 + 0.07, 3.32, 6.70, z0 - 0.15, z1 + 0.15)
    for zz in (z0 - 0.15, z1 + 0.15):
        bx(m, G.WHITE, x0 - 0.03, x0 + 0.10, 3.28, 6.74, zz - 0.06, zz + 0.06)
    bx(m, G.WHITE, x0 - 0.03, x0 + 0.10, 6.62, 6.74, z0 - 0.15, z1 + 0.15)
    bx(m, G.WHITE, x0 - 0.03, x0 + 0.10, 3.28, 3.40, z0 - 0.15, z1 + 0.15)
    # upper shelf over the bench with the shop light under it
    bx(m, G.WHITE, x0, x0 + 1.05, 5.55, 5.68, z0 + 0.10, z1 - 0.10)
    for zz in (z0 + 0.35, (z0 + z1) / 2, z1 - 0.35):
        bx(m, G.WHITE_A, x0 + 0.90, x0 + 1.02, 5.68, 6.10, zz - 0.05, zz + 0.05)
    bx(m, G.STEEL_D, x0 + 0.30, x0 + 0.72, 5.40, 5.55, z0 + 0.55, z1 - 0.55)
    bx(m, G.LENS, x0 + 0.33, x0 + 0.69, 5.34, 5.41, z0 + 0.58, z1 - 0.58)
    # shelf clutter
    for i, (zz, w, h, mat) in enumerate((
            (z0 + 0.55, 0.62, 0.55, G.BLUE), (z0 + 1.30, 0.55, 0.42, G.CARD),
            (z0 + 2.00, 0.48, 0.62, G.RED), (z0 + 2.70, 0.50, 0.40, G.CARD),
            (z0 + 4.55, 0.60, 0.50, G.GREEN), (z0 + 5.35, 0.52, 0.58, G.YELLOW),
            (z0 + 6.10, 0.46, 0.44, G.CARD))):
        bx(m, mat, x0 + 0.12, x0 + 0.86, 5.68, 5.68 + h, zz - w / 2, zz + w / 2)

    # --- bench top (butcher block) and frame
    bx(m, G.OAKTOP, x0, x1, TOP - 0.12, TOP, z0, z1)
    bx(m, G.OAKEDGE, x0, x1, TOP - 0.16, TOP - 0.12, z0, z1)
    for zz in (z0 + 0.16, z1 - 0.16):
        bx(m, G.STEEL_D, x0 + 0.12, x0 + 0.28, 0.0, TOP - 0.16, zz - 0.08, zz + 0.08)
        bx(m, G.STEEL_D, x1 - 0.28, x1 - 0.12, 0.0, TOP - 0.16, zz - 0.08, zz + 0.08)
    bx(m, G.STEEL_D, x0 + 0.12, x1 - 0.12, TOP - 0.42, TOP - 0.30, z0 + 0.16, z1 - 0.16)
    # lower shelf
    bx(m, G.STEEL_D, x0 + 0.14, x1 - 0.14, 0.62, 0.72, z0 + 0.10, z1 - 0.10)

    # --- red rolling tool chest under the north end
    cz0, cz1 = z0 + 0.22, z0 + 2.90
    bx(m, G.RED, x0 + 0.16, x1 - 0.22, 0.28, TOP - 0.50, cz0, cz1)
    for i in range(5):
        y = 0.36 + i * 0.44
        bx(m, G.REDD, x1 - 0.22, x1 - 0.16, y, y + 0.38, cz0 + 0.05, cz1 - 0.05)
        bx(m, G.RED, x1 - 0.20, x1 - 0.13, y + 0.02, y + 0.36, cz0 + 0.07, cz1 - 0.07)
        bx(m, G.CHR, x1 - 0.14, x1 - 0.07, y + 0.13, y + 0.23, cz0 + 0.55, cz1 - 0.55)
    for zz in (cz0 + 0.22, cz1 - 0.22):
        m.add(cylinder(0.15, 0.28, 12), G.BLKR, at=(x0 + 0.55, 0.0, zz))
        m.add(cylinder(0.15, 0.28, 12), G.BLKR, at=(x1 - 0.45, 0.0, zz))

    # --- bins on the lower shelf
    for i, (zz, mat) in enumerate(((z0 + 3.55, G.PLAS_G), (z0 + 4.45, G.PLAS_G),
                                   (z0 + 5.35, G.PLAS_G), (z0 + 6.25, G.PLAS_G))):
        bx(m, mat, x0 + 0.22, x1 - 0.28, 0.72, 1.52, zz - 0.38, zz + 0.38)
        bx(m, G.YELLOW, x0 + 0.19, x1 - 0.25, 1.52, 1.62, zz - 0.41, zz + 0.41)

    # --- bench-top objects
    # vise at the north end
    bx(m, G.STEEL_D, x1 - 0.95, x1 - 0.30, TOP, TOP + 0.20, z0 + 0.30, z0 + 0.80)
    bx(m, G.BLUE, x1 - 0.90, x1 - 0.35, TOP + 0.20, TOP + 0.62, z0 + 0.34, z0 + 0.55)
    bx(m, G.BLUE, x1 - 0.90, x1 - 0.35, TOP + 0.20, TOP + 0.62, z0 + 0.62, z0 + 0.78)
    m.add(cylinder(0.045, 0.62, 10), G.CHR, at=(x1 - 0.62, TOP + 0.72, z0 + 0.56),
          rot_z=G.R(90))
    bx(m, G.STEEL_D, x1 - 0.80, x1 - 0.45, TOP + 0.62, TOP + 0.74, z0 + 0.44, z0 + 0.68)
    # circular saw
    bx(m, G.ORANGE, x0 + 0.55, x0 + 1.35, TOP, TOP + 0.55, z0 + 1.70, z0 + 2.30)
    bx(m, G.CHR, x0 + 1.32, x0 + 1.37, TOP + 0.05, TOP + 0.52, z0 + 1.78, z0 + 2.24)
    bx(m, G.BLK, x0 + 1.28, x0 + 1.34, TOP + 0.20, TOP + 0.58, z0 + 1.72, z0 + 2.12)
    # open toolbox + jars
    bx(m, G.RED, x0 + 0.45, x0 + 1.75, TOP, TOP + 0.62, z1 - 2.55, z1 - 1.60)
    bx(m, G.BLK, x0 + 0.95, x0 + 1.25, TOP + 0.62, TOP + 0.92, z1 - 2.35, z1 - 1.80)
    for i, zz in enumerate((z1 - 1.25, z1 - 0.95, z1 - 0.65)):
        m.add(cylinder(0.135, 0.34, 12), G.WHITE, at=(x0 + 0.55, TOP, zz))
        m.add(cylinder(0.135, 0.05, 12), G.BLK, at=(x0 + 0.55, TOP + 0.34, zz))
    # coffee-can of odds
    m.add(cylinder(0.22, 0.42, 14), G.STEEL, at=(x0 + 1.25, TOP, z1 - 0.90))

    # --- pegboard tools (x from the board face outward)
    px = x0 + 0.07
    def hang(zz, y, w, h, d, mat, horiz=False):
        if horiz:
            bx(m, mat, px, px + d, y, y + h, zz - w / 2, zz + w / 2)
        else:
            bx(m, mat, px, px + d, y - h, y, zz - w / 2, zz + w / 2)

    hang(z0 + 0.55, 5.28, 0.13, 0.95, 0.13, G.BLK)            # hammer handle
    bx(m, G.STEEL, px, px + 0.16, 5.23, 5.39, z0 + 0.32, z0 + 0.80)
    for i, zz in enumerate((z0 + 1.10, z0 + 1.36, z0 + 1.62, z0 + 1.88)):
        hang(zz, 5.30, 0.11, 0.62 + 0.09 * i, 0.10, G.CHR)     # wrenches
    hang(z0 + 2.30, 5.28, 0.16, 0.72, 0.12, G.BLUE)            # pliers
    hang(z0 + 2.62, 5.28, 0.16, 0.64, 0.12, G.RED)
    bx(m, G.YELLOW, px, px + 0.13, 5.32, 5.49, z0 + 3.05, z0 + 6.15)   # level
    for i, zz in enumerate((z0 + 3.20, z0 + 3.44, z0 + 3.68, z0 + 3.92, z0 + 4.16)):
        hang(zz, 5.12, 0.10, 0.75, 0.10, G.RED if i % 2 else G.YELLOW)  # drivers
    # hand saw
    bx(m, G.CHR, px, px + 0.10, 4.05, 5.05, z0 + 4.70, z0 + 4.90)
    bx(m, G.OAKEDGE, px, px + 0.16, 5.05, 5.35, z0 + 4.62, z0 + 4.98)
    # coiled extension cord + hose
    m.add(torus(0.55, 0.10, 18, 8), G.ORANGE, at=(px + 0.20, 4.85, z0 + 5.75),
          rot_z=G.R(90))
    m.add(torus(0.62, 0.11, 18, 8), G.GREEN, at=(px + 0.22, 4.30, z0 + 6.60),
          rot_z=G.R(90))
    # C-clamps
    for i, zz in enumerate((z1 - 0.90, z1 - 0.62, z1 - 0.34)):
        hang(zz, 5.30, 0.14, 0.50, 0.14, G.STEEL_D)
    return m


# ----------------------------------------------------------------- shelving
def shelving():
    m = Model()
    z0, z1, H, DEEP = 14.10, 18.70, 6.20, 1.85
    x0, x1 = 0.12, 0.12 + DEEP
    for zz in (z0 + 0.10, z1 - 0.10):
        for xx in (x0 + 0.09, x1 - 0.09):
            bx(m, G.STEEL_D, xx - 0.07, xx + 0.07, 0.0, H, zz - 0.07, zz + 0.07)
    tiers = (0.30, 1.72, 3.14, 4.56, H - 0.10)
    for y in tiers:
        bx(m, G.STEEL, x0, x1, y, y + 0.09, z0, z1)
    # loads
    load = [
        (0, z0 + 0.75, G.PLAS_G, 1.05, 0.95), (0, z0 + 1.95, G.PLAS_G, 1.05, 0.95),
        (0, z0 + 3.15, G.BLUE, 1.05, 0.95),
        (1, z0 + 0.80, G.CARD, 1.10, 0.95), (1, z0 + 2.05, G.CARD, 1.05, 0.80),
        (1, z0 + 3.30, G.PLAS_G, 1.00, 1.00),
        (2, z0 + 0.85, G.PLAS_G, 1.05, 1.00), (2, z0 + 2.10, G.YELLOW, 0.95, 0.72),
        (2, z0 + 3.25, G.CARD, 1.05, 0.90),
        (3, z0 + 0.90, G.CARD, 1.05, 1.05), (3, z0 + 2.20, G.PLAS_G, 1.05, 0.85),
        (3, z0 + 3.35, G.GREEN, 0.90, 0.62),
    ]
    for (tier, zz, mat, w, h) in load:
        y = tiers[tier] + 0.09
        bx(m, mat, x0 + 0.10, x1 - 0.18, y, y + h, zz - w / 2, zz + w / 2)
        if mat is G.PLAS_G:
            bx(m, G.YELLOW, x0 + 0.07, x1 - 0.15, y + h, y + h + 0.10,
               zz - w / 2 - 0.03, zz + w / 2 + 0.03)
    # paint cans on the top tier
    for zz in (z0 + 0.70, z0 + 1.10, z0 + 1.50, z0 + 2.30):
        m.add(cylinder(0.30, 0.62, 14), G.STEEL, at=(x0 + 0.75, tiers[-1] + 0.09, zz))
        m.add(cylinder(0.30, 0.06, 14), G.BLUE, at=(x0 + 0.75, tiers[-1] + 0.71, zz))
    return m


if __name__ == "__main__":
    tot = 0
    tot += G.save_and_place("Garage Cabinets Tall", cabinets(), ROOM)
    tot += G.save_and_place("Garage Workbench", workbench(), ROOM)
    tot += G.save_and_place("Garage Shelving", shelving(), ROOM)
    print("  west wall total %.1f KB" % tot)
