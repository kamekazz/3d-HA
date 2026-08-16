"""Room 17 -- Hallway, second floor (8.1 x 16.7 x 8.0).

Photos: 'Second-floor hallway.jpg' (primary) + 3 more.  Cool grey walls, NO
crown (the drywall meets the ceiling clean in every shot), tall white
baseboards, grey plank floor, a white runner, three cans and a flush disc, and
the room's defining feature: the white capped KNEE WALL round the stairwell.

The stairwell is the level-1 stair (world x 14.6..18.4, z 14.3..24.5, rising
north), i.e. local x 4.1..7.9 / z 7.7..16.7 of this room -- so the knee wall
runs north along local x = 4.05 and returns across the head of the flight.

Doors (world -> local z on the west wall): guest room 13 at z 7.5..10.2,
room 25 further south.  East wall: master bath 16 (z 0..5.8) and master
closet 27 (z 5.8..14.2).  South: bath 26.
"""

from kit import *

ROOM, W, D, H = 17, 8.1, 16.7, 8.0

D_GUEST = (0.90, 3.60)       # west wall
D_R25 = (11.60, 14.30)       # west wall
D_MBATH = (1.60, 4.30)       # east wall
D_MCL = (6.40, 9.10)         # east wall
STAIR_X, STAIR_Z0 = 4.05, 7.70


def shell():
    out = []
    m = ceiling(W, D, H, crown=False,
                cans=[(2.0, 3.4), (6.1, 3.4), (2.0, 13.6)],
                fixtures=[(4.05, 8.60, 0.55)],
                vents=[(6.30, 6.10, 0.52, 0.95)])
    out.append(save_and_place("Hall2F Ceiling", m, ROOM))

    m = baseboards(W, D, doors=[("w", *D_GUEST), ("w", *D_R25),
                                ("e", *D_MBATH), ("e", *D_MCL)])
    door_unit(m, "w", W, D, *D_GUEST)
    door_unit(m, "w", W, D, *D_R25)
    door_unit(m, "e", W, D, *D_MBATH)
    door_unit(m, "e", W, D, *D_MCL)
    out.append(save_and_place("Hall2F Baseboards", m, ROOM))
    return out


def balustrade():
    """The white knee wall round the stairwell -- a solid capped half wall,
    exactly what the photo shows (no spindles on this floor)."""
    m = Model()
    x = STAIR_X
    z0, z1 = STAIR_Z0, D - 0.02
    # the long run north-south, on the west side of the stairwell
    bx(m, TRIM, x - 0.24, x, 0.0, 3.05, z0, z1)
    bx(m, TRIM_D, x - 0.30, x + 0.06, 3.05, 3.20, z0 - 0.06, z1)
    bx(m, TRIM, x - 0.22, x - 0.02, 0.0, 0.52, z0, z1)           # skirt
    # the return across the head of the flight
    bx(m, TRIM, x - 0.24, W - 0.02, 0.0, 3.05, z0, z0 + 0.24)
    bx(m, TRIM_D, x - 0.30, W - 0.02, 3.05, 3.20, z0 - 0.06, z0 + 0.30)
    # newel block where the two runs meet
    bx(m, TRIM, x - 0.34, x + 0.10, 0.0, 3.32, z0 - 0.10, z0 + 0.34)
    bx(m, TRIM_D, x - 0.40, x + 0.16, 3.32, 3.46, z0 - 0.16, z0 + 0.40)
    return m


def runner():
    """The chunky white wool runner down the middle of the hall."""
    m = Model()
    x0, x1, z0, z1 = 0.95, 3.75, 2.40, 11.60
    contact_shadow(m, (x0 + x1) / 2, (z0 + z1) / 2, (x1 - x0) * 0.62,
                   (z1 - z0) * 0.55, y=0.008, strength=0.14, room=(W, D))
    WOOL = Material("wool", "#efece5", roughness=0.98)
    WOOL2 = Material("wool2", "#e2ded6", roughness=0.98)
    bx(m, WOOL, x0, x1, 0.016, 0.062, z0, z1)
    n = int((z1 - z0) / 0.42)
    for i in range(n):                          # braided nap, readable at 50 deg
        z = z0 + 0.10 + i * 0.42
        bx(m, WOOL2, x0 + 0.05, x1 - 0.05, 0.062, 0.074, z, z + 0.20)
    return m


if __name__ == "__main__":
    print("room 17 Hallway (2F)")
    surfaces(ROOM, wall_color="#d4d6d7", floor_color="#6b6967",
             floor_texture="wood")
    shell()
    save_and_place("Hall2F Balustrade", balustrade(), ROOM)
    save_and_place("Hall2F Floor Runner", runner(), ROOM)
