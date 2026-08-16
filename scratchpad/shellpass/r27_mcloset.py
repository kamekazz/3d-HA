"""Room 27 -- Master Closet (13.6 x 8.4 x 8.0) and the two small level-2
nooks, room 25 "Room 7" (8.6 x 5.4) and room 24 "Bathroom closet" (7.8 x 5.6).

Master closet photos: 'Walk in the closet to Master Bedroom.jpg',
'Walking Closet for the Master bedroom.jpg'.  Grey CARPET (not plank), white
walls, a SLOPED ceiling coming down over one side under the roof, a black
accent wall on that same side, cans in the slope, chrome wire shelving.

The room's east wall (world x = 32.2) is 1.2 ft short of the house's east edge,
so the roof falls toward the EAST -- the slope and the black wall go there.

Rooms 24 and 25 get ceiling + baseboards + surfaces only, per the brief.
NOTE room 24's footprint overlaps Master Bed (14)'s rect in the layout data;
its shell is built to its own rect and nothing there was touched.
"""

from kit import *

ROOM, W, D, H = 27, 13.6, 8.4, 8.0
DOOR = (1.30, 4.00)          # west wall, local z -- from the hallway
SLOPE_X, SLOPE_Y = 6.80, 4.55       # flat to x=6.8, then down to 4.55 at x=W


def sloped_ceiling():
    """Flat over the west half, then a raking plane down to the east knee wall.

    Wound to face INTO the room (one-sided) so it is solid at eye level and
    invisible from above -- the plan pose must still see the floor.
    """
    m = Model()
    Y = H - 0.01
    m.add(quad((0, Y, 0), (SLOPE_X, Y, 0), (SLOPE_X, Y, D), (0, Y, D)), CEIL)
    # rake: same winding order, just with the two east vertices dropped
    m.add(quad((SLOPE_X, Y, 0), (W, SLOPE_Y, 0), (W, SLOPE_Y, D),
               (SLOPE_X, Y, D)), CEIL)
    # cans: two in the flat, two in the rake (dropped to the raking plane)
    for (cx, cz) in ((2.6, 2.2), (2.6, 6.2)):
        ring_down(m, CEIL_FLAT, cx, cz, Y - 0.022, 0.255, 0.345)
        disc_down(m, LENS, cx, cz, Y - 0.075, 0.222)
    for (cx, cz) in ((9.0, 2.2), (9.0, 6.2)):
        y = Y - (Y - SLOPE_Y) * (cx - SLOPE_X) / (W - SLOPE_X)
        ring_down(m, CEIL_FLAT, cx, cz, y - 0.030, 0.255, 0.345)
        disc_down(m, LENS, cx, cz, y - 0.085, 0.222)
    # the raking plane's own trim line where it meets the flat ceiling
    bx(m, TRIM_D, SLOPE_X - 0.04, SLOPE_X + 0.04, Y - 0.14, Y - 0.01, 0.0, D)
    return m


def shelving():
    """Chrome wire shelving down the north wall + a hanging rail run on the
    south wall -- a closet with neither reads as an empty box."""
    m = Model()
    WIRE = Material("wire", "#c9ced1", roughness=0.35, metallic=0.5)
    BIN = Material("bin", "#e7e4de", roughness=0.9)
    FOLD = Material("fold", "#d8d4cd", roughness=0.95)
    NAVY = Material("navy", "#3b445c", roughness=0.9)

    def rack(x0, x1, z0, z1, levels, top):
        contact_shadow(m, (x0 + x1) / 2, (z0 + z1) / 2, (x1 - x0) * 0.55,
                       (z1 - z0) * 1.25, y=0.010, strength=0.18, room=(W, D))
        for px in (x0 + 0.10, x1 - 0.10):
            for pz in (z0 + 0.08, z1 - 0.08):
                m.add(cylinder(0.055, top, 8), WIRE, at=(px, 0.0, pz))
        for i in range(levels):
            y = 0.55 + i * (top - 0.75) / max(1, levels - 1)
            for k in range(9):                 # wire deck, drawn as rods
                z = z0 + 0.06 + k * (z1 - z0 - 0.12) / 8
                bx(m, WIRE, x0, x1, y, y + 0.035, z, z + 0.045)
            bx(m, WIRE, x0, x1, y, y + 0.055, z0, z0 + 0.05)
            bx(m, WIRE, x0, x1, y, y + 0.055, z1 - 0.05, z1)
        return

    rack(0.55, 5.35, 0.15, 1.85, 4, 6.10)
    rack(5.85, 10.20, 0.15, 1.85, 4, 6.10)
    # folded stacks and bins on the shelves
    rn = Rnd(4242)
    for i in range(16):
        x = rn.f(0.75, 10.0)
        lvl = int(rn.f(0, 3.99))
        y = 0.585 + lvl * (6.10 - 0.75) / 3
        mat = (BIN, FOLD, NAVY)[int(rn.f(0, 2.99))]
        h = rn.f(0.35, 0.85)
        bx(m, mat, x, x + rn.f(0.9, 1.7), y, y + h, 0.30, 1.70)

    # hanging rail on the south wall, under the rake
    z1 = D - 0.12
    bx(m, WIRE, 0.60, 12.20, 5.35, 5.42, z1 - 1.85, z1 - 1.78)
    for px in (0.65, 6.40, 12.15):
        bx(m, WIRE, px, px + 0.07, 5.35, 6.30, z1 - 1.90, z1 - 1.73)
        bx(m, WIRE, px, px + 0.07, 6.22, 6.30, z1 - 1.90, z1)
    rn = Rnd(919)
    for i in range(26):                        # hanging clothes
        x = 0.85 + i * 0.43
        if x > 11.9:
            break
        c = ("#3b445c", "#e7e4de", "#2c2e33", "#b9bcc0", "#4d5560")[i % 5]
        mat = Material("hang%d" % (i % 5), c, roughness=0.92)
        bx(m, mat, x, x + 0.30, 5.35 - rn.f(2.0, 3.2), 5.36,
           z1 - 1.92, z1 - 1.15)
    return m


def black_wall():
    """The dark accent wall under the rake, east side (both photos)."""
    m = Model()
    BLK = Material("acc", "#26272b", roughness=0.88)
    bx(m, BLK, W - 0.055, W - 0.015, BB_H, SLOPE_Y - 0.05, 0.06, D - 0.06)
    return m


if __name__ == "__main__":
    print("room 27 Master Closet")
    surfaces(ROOM, wall_color="#eeece8", floor_color="#7d7d7a",
             floor_texture="carpet")
    save_and_place("Master Closet Ceiling", sloped_ceiling(), ROOM)
    m = baseboards(W, D, doors=[("w", *DOOR)])
    door_unit(m, "w", W, D, *DOOR)
    save_and_place("Master Closet Baseboards", m, ROOM)
    save_and_place("Master Closet Wall Wash Dark", black_wall(), ROOM)
    save_and_place("Master Closet Shelving", shelving(), ROOM)

    # ---- room 25 "Room 7" -- Rios Room's closet, off its north wall --------
    print("room 25 Room 7")
    W25, D25 = 8.6, 5.4
    surfaces(25, wall_color="#e9e7e2", floor_color="#6b6967",
             floor_texture="wood")
    save_and_place("R25 Ceiling", ceiling(W25, D25, 8.0, crown=False,
                                          cans=[(2.4, 2.7), (6.2, 2.7)]), 25)
    m = baseboards(W25, D25, doors=[("s", 1.20, 6.20)])
    save_and_place("R25 Baseboards", m, 25)

    # ---- room 24 "Bathroom closet" ----------------------------------------
    print("room 24 Bathroom closet")
    W24, D24 = 7.8, 5.6
    surfaces(24, wall_color="#e9e7e2", floor_color="#6b6967",
             floor_texture="wood")
    save_and_place("R24 Ceiling", ceiling(W24, D24, 8.0, crown=False,
                                          cans=[(2.2, 2.8), (5.6, 2.8)]), 24)
    m = baseboards(W24, D24, doors=[("s", 2.60, 7.60)])
    save_and_place("R24 Baseboards", m, 24)
