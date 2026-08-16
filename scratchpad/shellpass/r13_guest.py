"""Room 13 -- Guest Room (level 2, 12.4 x 10.8 x 8.0).

Photos: docs/photos-jpg/'Guest Room.jpg' (primary), 'Guest Room TV and Door.jpg',
'Guest Room Closet.jpg'.  Orientation from 'docs/floor plan/Second Floor Plan
App.png' (plan-up = world +z, plan-right = world -x, per room 15's notes):

    WEST  (x=0)     exterior -- the window, plan-blue at local z 1.3..4.9
    EAST  (x=12.4)  second-floor hallway (room 17) -- the entry door
    NORTH (z=0)     room 24 sits behind local x 0..7.8 -- the closet doors
    SOUTH (z=10.8)  room 25 behind -- blank; the bed's headboard wall

Shell only: ceiling + crown + 4 cans, baseboards + chair rail (the photo has a
clear rail at ~3.3 ft), window, doors, and the two pieces without which a
bedroom is not a bedroom -- the black bed and the black dresser.
"""

from kit import *

ROOM, W, D, H = 13, 12.4, 10.8, 8.0

WIN = (1.35, 4.90)          # local z on the west wall
DOOR = (1.00, 3.70)         # local z on the east wall
CLOSET = (2.60, 7.60)       # local x on the north wall
RAIL = 3.32


def shell():
    out = []
    m = ceiling(W, D, H,
                cans=[(3.1, 2.9), (9.0, 2.9), (3.1, 7.8), (9.0, 7.8)],
                vents=[(6.6, 1.15, 0.92, 0.50)])
    out.append(save_and_place("Guest Ceiling", m, ROOM))

    m = baseboards(W, D, rail=RAIL,
                   doors=[("e", DOOR[0], DOOR[1]),
                          ("n", CLOSET[0], CLOSET[1])])
    window_unit(m, "w", W, D, WIN[0], WIN[1], sill=2.15, head=6.35)
    door_unit(m, "e", W, D, DOOR[0], DOOR[1])
    door_unit(m, "n", W, D, CLOSET[0], CLOSET[1], panels=2)
    out.append(save_and_place("Guest Baseboards", m, ROOM))
    return out


# ------------------------------------------------------------------- pieces
BLACKWD = Material("blackwd", "#232326", roughness=0.55)
BLACKWD2 = Material("blackwd2", "#2e3033", roughness=0.55)
SHEET = Material("sheet", "#dedad3", roughness=0.92)
SHEET2 = Material("sheet2", "#efece6", roughness=0.92)
BLUE = Material("gblue", "#b9c8cf", roughness=0.9)


def bed():
    """Queen platform bed, black stained wood, headboard on the SOUTH wall."""
    m = Model()
    bw, bl = 5.10, 6.90
    x0 = (W - bw) / 2 - 0.6
    x1 = x0 + bw
    z1 = D - 0.16                      # headboard against the south wall
    z0 = z1 - bl
    contact_shadow(m, (x0 + x1) / 2, (z0 + z1) / 2 + 0.10,
                   bw * 0.62, bl * 0.55, y=0.010, strength=0.30, room=(W, D))

    # headboard
    bx(m, BLACKWD, x0, x1, 0.0, 3.95, z1 - 0.22, z1)
    bx(m, BLACKWD2, x0 + 0.22, x1 - 0.22, 1.15, 3.62, z1 - 0.26, z1 - 0.21)
    # footboard + rails
    bx(m, BLACKWD, x0, x1, 0.0, 1.72, z0, z0 + 0.20)
    bx(m, BLACKWD2, x0 + 0.22, x1 - 0.22, 0.55, 1.48, z0 - 0.04, z0 + 0.01)
    bx(m, BLACKWD, x0, x0 + 0.16, 0.0, 1.05, z0, z1)
    bx(m, BLACKWD, x1 - 0.16, x1, 0.0, 1.05, z0, z1)
    # mattress + bedding
    bx(m, SHEET2, x0 + 0.14, x1 - 0.14, 1.02, 1.72, z0 + 0.20, z1 - 0.22)
    m.add(sag_plane(bw - 0.16, bl - 0.55, sag=0.05, nx=8, nz=10,
                    y=1.74, edge_drop=0.30), SHEET,
          at=((x0 + x1) / 2, 0.0, (z0 + z1) / 2 - 0.02))
    # folded throw across the foot
    bx(m, BLUE, x0 + 0.10, x1 - 0.10, 1.70, 1.80, z0 + 0.55, z0 + 2.15)
    # pillows
    for i, cx in enumerate((x0 + 1.35, x1 - 1.35)):
        m.add(rounded_box(1.95, 0.52, 1.05, r=0.20, seg=3), SHEET2,
              at=(cx, 1.72, z1 - 1.05), rot_x=R(-16))
        m.add(rounded_box(1.55, 0.42, 0.85, r=0.16, seg=3), SHEET,
              at=(cx, 2.06, z1 - 1.28), rot_x=R(-22))
    m.add(rounded_box(1.35, 0.40, 1.35, r=0.14, seg=3), BLUE,
          at=((x0 + x1) / 2, 1.74, z1 - 2.05))
    return m


def dresser():
    """The tall black dresser on the NORTH wall, east of the closet doors."""
    m = Model()
    x0, x1 = 8.45, 11.95
    z0, z1 = 0.09, 1.72
    contact_shadow(m, (x0 + x1) / 2, (z0 + z1) / 2 + 0.10,
                   (x1 - x0) * 0.60, (z1 - z0) * 1.15, y=0.010, strength=0.26,
                   room=(W, D))
    bx(m, BLACKWD, x0, x1, 0.16, 3.05, z0, z1)
    bx(m, BLACKWD2, x0 - 0.04, x1 + 0.04, 3.05, 3.16, z0 - 0.04, z1 + 0.04)
    for i in range(3):                        # feet
        pass
    bx(m, BLACKWD2, x0 + 0.10, x1 - 0.10, 0.0, 0.16, z0 + 0.10, z1 - 0.10)
    for r in range(3):                        # drawer fronts
        y = 0.32 + r * 0.86
        for c in range(2):
            dx0 = x0 + 0.10 + c * ((x1 - x0 - 0.30) / 2 + 0.10)
            dx1 = dx0 + (x1 - x0 - 0.30) / 2
            bx(m, BLACKWD2, dx0, dx1, y, y + 0.72, z1, z1 + 0.028)
            bx(m, BLACKMET, (dx0 + dx1) / 2 - 0.30, (dx0 + dx1) / 2 + 0.30,
               y + 0.30, y + 0.38, z1 + 0.028, z1 + 0.10)
    # white lamp + a plant on top
    m.add(cylinder(0.10, 0.95, 10), BLACKMET, at=(x0 + 0.70, 3.16, (z0 + z1) / 2))
    m.add(cylinder(0.42, 0.72, 14, r_top=0.36), Material("shade", "#f4f2ee",
          roughness=0.8), at=(x0 + 0.70, 4.05, (z0 + z1) / 2))
    m.add(cylinder(0.34, 0.42, 12), Material("pot", "#efece6", roughness=0.75),
          at=(x1 - 0.75, 3.16, (z0 + z1) / 2))
    rn = Rnd(7717)
    GRN = Material("gleaf", "#7f9068", roughness=0.9)
    for i in range(9):
        m.add(cylinder(0.30 + 0.13 * rn.f(), 0.010, 8), GRN,
              at=(x1 - 0.75 + rn.f(-0.5, 0.5), 3.62 + rn.f(0, 1.15),
                  (z0 + z1) / 2 + rn.f(-0.4, 0.4)),
              rot_x=R(rn.f(46, 78)), rot_z=R(rn.f(-40, 40)))
    return m


if __name__ == "__main__":
    print("room 13 Guest Room")
    surfaces(ROOM, wall_color="#dedbd5", floor_color="#6b6967",
             floor_texture="wood")
    L = shell()
    L.append(save_and_place("Guest Bed", bed(), ROOM))
    L.append(save_and_place("Guest Dresser", dresser(), ROOM))
