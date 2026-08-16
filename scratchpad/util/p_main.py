"""Pantry (room 10) -- 3.1 x 5.7 ft reach-in off the first-floor hallway.

INFERRED.  'pantry door.jpg' and 'Pantry and garage door.jpg' both show the
double doors CLOSED, so there is no photograph of the inside of this room at
all.  What the photos do fix is the doorway: a pair of white six-panel leaves on
the 5.7 ft WEST wall, facing the hallway.  So the deep wall opposite the doors
(east, 5.7 ft) carries the shelf run, the two 3.1 ft end walls carry short
shelves, and the goods are ordinary dry-store stock.
"""
from gkit import *   # noqa: F401,F403
import gkit as G

ROOM = 10
W, D, H = 3.1, 5.7, 9.0

SH = Material("psh", "#eeece7", roughness=0.60)
SH_D = Material("pshd", "#dcd9d3", roughness=0.62)
STAND = Material("pstand", "#9aa0a4", roughness=0.45, metallic=0.35)
BOX_A = Material("pboxa", "#c8592f", roughness=0.72)
BOX_B = Material("pboxb", "#2f5f96", roughness=0.72)
BOX_C = Material("pboxc", "#d8b13a", roughness=0.72)
BOX_D = Material("pboxd", "#4f7a4a", roughness=0.72)
BOX_E = Material("pboxe", "#b0392f", roughness=0.72)
CARD = Material("pcard", "#b39a6e", roughness=0.90)
CAN = Material("pcan", "#b9bdc0", roughness=0.38, metallic=0.45)
CANLID = Material("pcanl", "#c04a34", roughness=0.55)
JAR = Material("pjar", "#d9d6cc", roughness=0.30, opacity=0.85)
JARLID = Material("pjarl", "#2f3235", roughness=0.45)
WICK = Material("pwick", "#b39a72", roughness=0.88)
WICK_D = Material("pwickd", "#8f7a58", roughness=0.90)
PAPER = Material("ppaper", "#f2f0ea", roughness=0.80)
BOT = Material("pbot", "#7fa6c8", roughness=0.25, opacity=0.80)

TIERS = (1.35, 2.62, 3.89, 5.16, 6.43)
RND = G.Rnd(4711)


def shelf_run(m, wall, a0, a1, depth, tiers=TIERS):
    """Shelf boards + standards on `wall` ('e', 'n', 's')."""
    for y in tiers:
        if wall == "e":
            bx(m, SH, W - depth, W - 0.03, y, y + 0.085, a0, a1)
            bx(m, SH_D, W - depth, W - depth + 0.035, y - 0.05, y, a0, a1)
        elif wall == "n":
            bx(m, SH, a0, a1, y, y + 0.085, 0.03, depth)
            bx(m, SH_D, a0, a1, y - 0.05, y, depth - 0.035, depth)
        else:
            bx(m, SH, a0, a1, y, y + 0.085, D - depth, D - 0.03)
            bx(m, SH_D, a0, a1, y - 0.05, y, D - depth, D - depth + 0.035)
    # vertical standards
    if wall == "e":
        for zz in (a0 + 0.14, (a0 + a1) / 2, a1 - 0.14):
            bx(m, STAND, W - 0.09, W - 0.03, 0.95, TIERS[-1] + 0.30,
               zz - 0.045, zz + 0.045)
    else:
        z = 0.06 if wall == "n" else D - 0.09
        for xx in (a0 + 0.14, a1 - 0.14):
            bx(m, STAND, xx - 0.045, xx + 0.045, 0.95, TIERS[-1] + 0.30,
               z, z + 0.06)


def goods_east(m):
    depth = 1.05
    x0, x1 = W - depth + 0.06, W - 0.10
    rows = [
        # (tier, z0, z1, kind, mat)
        (0, 0.28, 0.72, "box", BOX_A), (0, 0.76, 1.12, "box", BOX_C),
        (0, 1.20, 1.95, "wick", None), (0, 2.05, 2.80, "wick", None),
        (0, 2.95, 3.60, "card", CARD), (0, 3.70, 4.25, "box", BOX_B),
        (0, 4.35, 5.40, "paper", None),
        (1, 0.25, 1.55, "cans", None), (1, 1.65, 2.15, "box", BOX_D),
        (1, 2.25, 2.72, "box", BOX_E), (1, 2.82, 3.95, "jars", None),
        (1, 4.05, 4.60, "box", BOX_C), (1, 4.70, 5.45, "wick", None),
        (2, 0.25, 0.85, "box", BOX_B), (2, 0.95, 2.15, "cans", None),
        (2, 2.25, 3.05, "card", CARD), (2, 3.15, 4.15, "jars", None),
        (2, 4.25, 4.80, "box", BOX_A), (2, 4.90, 5.45, "box", BOX_D),
        (3, 0.30, 1.30, "wick", None), (3, 1.40, 2.00, "box", BOX_C),
        (3, 2.10, 3.20, "jars", None), (3, 3.30, 3.90, "box", BOX_E),
        (3, 4.00, 5.10, "cans", None),
        (4, 0.35, 1.55, "card", CARD), (4, 1.65, 2.35, "box", BOX_B),
        (4, 2.45, 3.55, "wick", None), (4, 3.65, 5.30, "card", CARD),
    ]
    for (t, z0, z1, kind, mat) in rows:
        y = TIERS[t] + 0.085
        if kind == "box":
            h = 0.62 + RND.f(0.0, 0.34)
            bx(m, mat, x0 + RND.f(0.0, 0.12), x1 - RND.f(0.05, 0.22), y, y + h, z0, z1)
        elif kind == "card":
            bx(m, mat, x0, x1 - 0.08, y, y + 0.55 + RND.f(0, 0.2), z0, z1)
            bx(m, SH_D, x0 + 0.05, x1 - 0.13, y + 0.02, y + 0.06, z0 + 0.04, z1 - 0.04)
        elif kind == "cans":
            n = int((z1 - z0) / 0.30)
            for i in range(n):
                zz = z0 + 0.15 + i * 0.30
                for dx in (0.22, 0.62):
                    m.add(cylinder(0.135, 0.36, 12), CAN, at=(x0 + dx, y, zz))
                    m.add(cylinder(0.135, 0.035, 12), CANLID, at=(x0 + dx, y + 0.36, zz))
        elif kind == "jars":
            n = int((z1 - z0) / 0.34)
            for i in range(n):
                zz = z0 + 0.17 + i * 0.34
                hh = 0.46 + RND.f(0, 0.18)
                m.add(cylinder(0.155, hh, 12), JAR, at=(x0 + 0.30, y, zz))
                m.add(cylinder(0.155, 0.05, 12), JARLID, at=(x0 + 0.30, y + hh, zz))
        elif kind == "wick":
            bx(m, WICK, x0 + 0.04, x1 - 0.10, y, y + 0.62, z0, z1)
            bx(m, WICK_D, x0, x1 - 0.06, y + 0.62, y + 0.70, z0 - 0.035, z1 + 0.035)
            for i in range(2):
                bx(m, WICK_D, x0 + 0.02, x1 - 0.08, y + 0.18 + i * 0.22,
                   y + 0.24 + i * 0.22, z0 - 0.012, z1 + 0.012)
        elif kind == "paper":
            for i in range(2):
                m.add(cylinder(0.26, 0.92, 14), PAPER,
                      at=(x0 + 0.32 + i * 0.52, y, (z0 + z1) / 2))


def shelves():
    m = Model()
    shelf_run(m, "e", 0.14, 5.56, 1.05)
    shelf_run(m, "n", 0.14, 1.95, 0.62, TIERS[:4])
    shelf_run(m, "s", 0.14, 1.95, 0.62, TIERS[:4])
    goods_east(m)
    # end-wall goods: bottles and small boxes
    for (t, xa, xb, mat) in ((0, 0.22, 0.62, BOX_C), (1, 0.24, 0.70, BOX_A),
                             (2, 0.22, 0.66, BOX_D), (3, 0.26, 0.72, BOX_B)):
        y = TIERS[t] + 0.085
        bx(m, mat, xa, xb, y, y + 0.60, 0.06, 0.58)
        bx(m, mat, xa, xb, y, y + 0.60, D - 0.58, D - 0.06)
    for t in range(4):
        y = TIERS[t] + 0.085
        for i in range(3):
            m.add(cylinder(0.115, 0.72, 10), BOT, at=(0.85 + i * 0.28, y, 0.30))
            m.add(cylinder(0.115, 0.62, 10), JAR, at=(0.85 + i * 0.28, y, D - 0.30))
    return m


def floor_stock():
    """Floor of a reach-in: a case of water, a sack, a folding step stool."""
    m = Model()
    bx(m, Material("pcase", "#4a76a8", roughness=0.55), 1.35, 2.95, 0.0, 0.78,
       4.15, 5.45)
    for i in range(4):
        m.add(cylinder(0.15, 0.28, 10), BOT, at=(1.62 + i * 0.32, 0.78, 4.55))
    bx(m, CARD, 1.45, 2.90, 0.78, 1.42, 4.25, 5.40)
    m.add(rounded_box(1.15, 0.55, 0.85, 0.16, 3), Material("psack", "#cfc3a4",
          roughness=0.90), at=(2.30, 0.0, 3.35))
    # folding step stool leaning on the north end
    bx(m, Material("pstool", "#dcd9d3", roughness=0.60), 1.55, 2.65, 0.0, 0.12,
       0.55, 1.45)
    for zz in (0.62, 1.38):
        bx(m, Material("pstool", "#dcd9d3", roughness=0.60), 1.60, 2.60, 0.0,
           1.30, zz - 0.05, zz + 0.05)
    bx(m, Material("pstool", "#dcd9d3", roughness=0.60), 1.55, 2.65, 1.30, 1.42,
       0.55, 1.45)
    for (cx, cz, rx, rz, st) in ((2.15, 4.80, 1.05, 0.95, 0.34),
                                 (2.30, 3.35, 0.75, 0.60, 0.28),
                                 (2.10, 1.00, 0.80, 0.72, 0.30)):
        G.contact_shadow(m, cx, cz, rx, rz, y=0.012, tone="#26262a",
                         strength=st, steps=8, room=(W, D))
    return m


if __name__ == "__main__":
    tot = 0
    tot += G.save_and_place("Pantry Shelves", shelves(), ROOM)
    tot += G.save_and_place("Pantry Floor Stock", floor_stock(), ROOM)
    print("  pantry total %.1f KB" % tot)
