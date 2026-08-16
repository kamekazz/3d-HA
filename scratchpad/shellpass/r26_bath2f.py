"""Room 26 -- bath, second floor (8.1 x 8.7 x 8.0).

Photos: 'Second floor bathroom.jpg' (primary) + 2 more.  White walls, crown,
grey plank floor (NOT tile -- the plank runs straight in from the hallway),
white subway-tile shower with a black sliding-glass door, white vanity with
black hardware, toilet under a window, a flush square fixture and one can.

Adjacency: hallway 17 is north (door), Rios Room 15 is west, EAST (x=8.1) and
SOUTH (z=8.7) are exterior.  Standing in the north doorway looking south,
screen-left is EAST, so the shower is on the east side and the vanity on the
west, with the window and toilet on the south wall.
"""

from kit import *

ROOM, W, D, H = 26, 8.1, 8.7, 8.0
DOOR = (4.30, 7.00)          # north wall, local x
WIN = (3.30, 5.90)           # south wall, local x


def shell():
    out = []
    m = ceiling(W, D, H,
                cans=[(2.20, 6.30)],
                fixtures=[(4.60, 2.10, 0.62)],
                vents=[(1.30, 1.20, 0.52, 0.90)])
    out.append(save_and_place("Bath2F Ceiling", m, ROOM))
    m = baseboards(W, D, doors=[("n", *DOOR)])
    door_unit(m, "n", W, D, *DOOR)
    window_unit(m, "s", W, D, WIN[0], WIN[1], sill=3.05, head=6.30)
    out.append(save_and_place("Bath2F Baseboards", m, ROOM))
    return out


def shower():
    """Subway-tiled alcove, east side, with a black-railed sliding glass door."""
    m = Model()
    x0, x1, z0, z1 = 4.20, 8.00, 0.10, 4.55
    bx(m, GROUT, x0, x1, 0.0, 7.00, z0, z0 + 0.10)
    bx(m, GROUT, x1 - 0.10, x1, 0.0, 7.00, z0, z1)
    rn = Rnd(5501)
    for r in range(24):                       # subway courses on the back wall
        y = 0.34 + r * 0.275
        off = 0.0 if r % 2 == 0 else 0.42
        for c in range(6):
            tx = x0 + 0.06 + off + c * 0.84
            if tx + 0.78 > x1 - 0.10:
                continue
            bx(m, TILEW, tx, tx + 0.78, y, y + 0.24, z0 + 0.10, z0 + 0.135)
    for r in range(24):                       # and on the side wall
        y = 0.34 + r * 0.275
        off = 0.0 if r % 2 else 0.42
        for c in range(5):
            tz = z0 + 0.06 + off + c * 0.84
            if tz + 0.78 > z1:
                continue
            bx(m, TILEW, x1 - 0.135, x1 - 0.10, y, y + 0.24, tz, tz + 0.78)
    bx(m, Material("pan26", "#f1f1f0", roughness=0.42), x0, x1, 0.0, 0.34, z0, z1)
    # black barn-style rail + two glass panels
    bx(m, BLACKMET, x0 - 0.06, x1, 6.55, 6.68, z1 - 0.16, z1 - 0.06)
    bx(m, GLASS, x0, x0 + 1.95, 0.34, 6.55, z1 - 0.14, z1 - 0.10)
    bx(m, GLASS, x0 + 1.85, x1, 0.34, 6.55, z1 - 0.06, z1 - 0.02)
    bx(m, BLACKMET, x0 + 1.85, x0 + 1.95, 0.34, 6.55, z1 - 0.16, z1 - 0.02)
    bx(m, BLACKMET, x0 + 0.55, x0 + 0.65, 2.60, 4.30, z1 - 0.22, z1 - 0.14)
    # black shower head on the back wall
    bx(m, BLACKMET, x1 - 1.35, x1 - 1.25, 4.60, 5.85, z0 + 0.135, z0 + 0.23)
    m.add(cylinder(0.30, 0.09, 12), BLACKMET, at=(x1 - 1.30, 5.78, z0 + 0.85))
    return m


def vanity():
    """White vanity on the west wall + the toilet under the south window."""
    m = Model()
    x0, x1, z0, z1 = 0.12, 2.05, 3.60, 7.70
    contact_shadow(m, (x0 + x1) / 2 + 0.2, (z0 + z1) / 2, 1.55,
                   (z1 - z0) * 0.62, y=0.010, strength=0.22, room=(W, D))
    WHT = Material("v26", "#f0eeea", roughness=0.58)
    bx(m, WHT, x0, x1, 0.28, 2.88, z0, z1)
    bx(m, Material("v26t", "#f6f5f3", roughness=0.30),
       x0, x1 + 0.06, 2.88, 3.00, z0 - 0.05, z1 + 0.05)
    for i in range(2):
        dz0 = z0 + 0.12 + i * ((z1 - z0 - 0.24) / 2)
        dz1 = dz0 + (z1 - z0 - 0.24) / 2 - 0.08
        bx(m, Material("v26d", "#e8e6e1", roughness=0.62),
           x1, x1 + 0.03, 0.42, 2.76, dz0, dz1)
        bx(m, BLACKMET, x1 + 0.03, x1 + 0.10, 2.28, 2.64,
           (dz0 + dz1) / 2 - 0.04, (dz0 + dz1) / 2 + 0.04)
    bx(m, Material("basin26", "#ecebe8", roughness=0.28),
       x0 + 0.30, x1 - 0.20, 2.76, 2.90, z0 + 1.35, z1 - 1.35)
    bx(m, BLACKMET, x0 + 0.30, x0 + 0.40, 3.00, 3.55, 5.60, 5.70)
    bx(m, BLACKMET, x0 + 0.30, x0 + 0.75, 3.45, 3.55, 5.60, 5.70)
    bx(m, Material("mir26", "#eaeef0", roughness=0.86, metallic=0.0),
       x0, x0 + 0.04, 3.75, 6.30, z0 + 1.05, z1 - 1.05)
    # toilet, south wall west of the window
    tx, tz = 2.85, D - 0.95
    contact_shadow(m, tx, tz, 1.00, 1.30, y=0.010, strength=0.20, room=(W, D))
    m.add(rounded_box(1.25, 1.15, 1.50, r=0.28, seg=3), PORC, at=(tx, 0.0, tz))
    m.add(rounded_box(1.36, 0.24, 1.68, r=0.40, seg=4), PORC, at=(tx, 1.13, tz - 0.16))
    bx(m, PORC, tx - 0.82, tx + 0.82, 1.15, 2.50, D - 0.72, D - 0.06)
    bx(m, PORC, tx - 0.70, tx + 0.70, 2.50, 2.61, D - 0.78, D - 0.02)
    return m


if __name__ == "__main__":
    print("room 26 bath (2F)")
    surfaces(ROOM, wall_color="#e9e7e2", floor_color="#6b6967",
             floor_texture="wood")
    shell()
    save_and_place("Bath2F Shower", shower(), ROOM)
    save_and_place("Bath2F Vanity", vanity(), ROOM)
