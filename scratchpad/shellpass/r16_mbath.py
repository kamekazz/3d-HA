"""Room 16 -- Master Bath. (level 2, 14.8 x 12.7 x 8.0).

Photos: 'Master Bath. 1.jpg' (primary), 2, 3, 'Master Bathroom A.jpg'.

Adjacency (world): master bedroom 14 is x -1.9..18.6 / z -12.4..6.3, so the
WEST wall borders the BEDROOM over local z 0..6.6 and the second-floor hallway
(17) over local z 6.9..12.7.  Master Closet 27 is behind the SOUTH wall.
NORTH (z=0) and EAST (x=14.8) are exterior.

NOTE ON THE FLOOR: the brief said bathrooms are tile.  All four master-bath
photos show the same grey wood-look PLANK running unbroken from the bedroom
through this room -- only the shower pan and surround are tile.  Photo wins.
"""

from kit import *

ROOM, W, D, H = 16, 14.8, 12.7, 8.0

DOOR_BED = (1.50, 4.30)      # west wall, local z -- to the master bedroom
DOOR_HALL = (9.60, 12.20)    # west wall, local z -- to the hallway
DOOR_CL = (4.60, 7.20)       # south wall, local x -- to the master closet
WIN = (3.60, 7.20)           # east wall, local z -- over the tub


def shell():
    out = []
    m = ceiling(W, D, H,
                cans=[(3.0, 2.6), (8.2, 2.6), (12.6, 2.6),
                      (3.0, 7.4), (8.2, 7.4), (12.6, 7.4),
                      (5.6, 11.0), (11.0, 11.0)],
                vents=[(1.55, 4.20, 0.55, 1.05), (9.90, 1.10, 1.00, 0.52)])
    out.append(save_and_place("Master Bath Ceiling", m, ROOM))

    m = baseboards(W, D, doors=[("w", *DOOR_BED), ("w", *DOOR_HALL),
                                ("s", *DOOR_CL)])
    door_unit(m, "w", W, D, *DOOR_BED)
    door_unit(m, "w", W, D, *DOOR_HALL)
    door_unit(m, "s", W, D, *DOOR_CL)
    window_unit(m, "e", W, D, WIN[0], WIN[1], sill=2.70, head=6.35)
    out.append(save_and_place("Master Bath Baseboards", m, ROOM))
    return out


# ------------------------------------------------------------------- pieces
def tub():
    """Freestanding slipper tub under the east window, with the black floor
    filler the photo shows standing beside it."""
    m = Model()
    cx, cz = 12.55, 5.35
    contact_shadow(m, cx, cz, 1.95, 3.55, y=0.010, strength=0.26, room=(W, D))
    # body: stacked rounded slabs tapering to the base = a slipper silhouette
    for i, (hy, w, l, r) in enumerate((
            (0.00, 1.90, 3.60, 0.55), (0.28, 2.35, 4.55, 0.75),
            (0.75, 2.75, 5.35, 0.95), (1.35, 2.95, 5.75, 1.05),
            (1.95, 2.98, 5.80, 1.10))):
        m.add(rounded_box(w, 0.75, l, r=r, seg=4), PORC, at=(cx, hy, cz))
    # rim + hollow
    m.add(rounded_box(2.62, 0.30, 5.35, r=0.95, seg=4),
          Material("tubin", "#e5e5e4", roughness=0.35), at=(cx, 2.32, cz))
    m.add(cylinder(0.09, 0.03, 8), BLACKMET, at=(cx, 2.34, cz + 1.70))
    # black floor-mounted filler
    m.add(cylinder(0.115, 2.35, 10), BLACKMET, at=(14.20, 0.0, cz - 2.05))
    m.add(cylinder(0.075, 0.72, 8), BLACKMET,
          at=(14.20, 2.30, cz - 1.75), rot_x=R(70))
    return m


def shower():
    """Glass corner enclosure with a marble surround, NW corner."""
    m = Model()
    x0, x1, z0, z1 = 0.90, 5.70, 0.10, 4.55
    VEIN = Material("mvein", "#c9c9cb", roughness=0.35)
    # marble back + side walls (inside faces)
    bx(m, MARBLE, x0, x1, 0.0, 7.10, z0, z0 + 0.16)
    bx(m, MARBLE, x0, x0 + 0.16, 0.0, 7.10, z0, z1)
    rn = Rnd(3311)
    for i in range(9):                      # veining
        vx = rn.f(x0 + 0.3, x1 - 0.3)
        bx(m, VEIN, vx, vx + rn.f(0.03, 0.07), rn.f(0.5, 3.0), rn.f(4.5, 6.9),
           z0 + 0.16, z0 + 0.175)
    # pan + curb
    bx(m, Material("pan", "#f2f2f1", roughness=0.4), x0, x1, 0.0, 0.30, z0, z1)
    bx(m, MARBLE, x0, x1, 0.30, 0.40, z1 - 0.22, z1)
    bx(m, MARBLE, x1 - 0.22, x1, 0.30, 0.40, z0, z1)
    # glass: front panel + return, black frame
    bx(m, GLASS, x0, x1, 0.40, 6.95, z1 - 0.06, z1 - 0.02)
    bx(m, GLASS, x1 - 0.06, x1 - 0.02, 0.40, 6.95, z0, z1)
    for a, b in ((x0, x0 + 0.09), (x1 - 0.09, x1)):
        bx(m, BLACKMET, a, b, 0.40, 6.98, z1 - 0.08, z1)
    bx(m, BLACKMET, x0, x1, 6.90, 6.98, z1 - 0.08, z1)
    # the RETURN's frame is two posts and a head rail -- writing it as one box
    # spanning the whole z range made a solid black slab that read as a hole
    for a, b in ((z0, z0 + 0.09), (z1 - 0.17, z1 - 0.08)):
        bx(m, BLACKMET, x1 - 0.09, x1 - 0.02, 0.40, 6.98, a, b)
    bx(m, BLACKMET, x1 - 0.09, x1 - 0.02, 6.90, 6.98, z0, z1 - 0.08)
    # black handle + rain head + riser
    bx(m, BLACKMET, x0 + 1.85, x0 + 1.95, 2.55, 4.05, z1 - 0.20, z1 - 0.08)
    bx(m, BLACKMET, x0 + 1.30, x0 + 1.42, 1.60, 6.20, z0 + 0.16, z0 + 0.28)
    m.add(cylinder(0.36, 0.10, 14), BLACKMET, at=(x0 + 1.36, 6.05, z0 + 0.80))
    bx(m, BLACKMET, x0 + 1.30, x0 + 1.42, 6.10, 6.20, z0 + 0.28, z0 + 0.86)
    return m


def vanity():
    """Double vanity on the SOUTH wall + the toilet in the SW corner."""
    m = Model()
    x0, x1 = 6.20, 13.90
    z1 = D - 0.10
    z0 = z1 - 2.05
    contact_shadow(m, (x0 + x1) / 2, z0 + 1.0, (x1 - x0) * 0.56, 1.85,
                   y=0.010, strength=0.24, room=(W, D))
    WHT = Material("vwht", "#f1efeb", roughness=0.55)
    bx(m, WHT, x0, x1, 0.30, 2.90, z0, z1)
    bx(m, WHT, x0 + 0.12, x1 - 0.12, 0.0, 0.30, z0 + 0.16, z1)   # toe kick
    bx(m, Material("vtop", "#f6f6f4", roughness=0.30),
       x0 - 0.05, x1 + 0.05, 2.90, 3.02, z0 - 0.05, z1)
    for i in range(4):                              # shaker doors
        dx0 = x0 + 0.10 + i * (x1 - x0 - 0.20) / 4
        dx1 = dx0 + (x1 - x0 - 0.20) / 4 - 0.08
        bx(m, Material("vdoor", "#e9e7e2", roughness=0.6),
           dx0, dx1, 0.42, 2.78, z0 - 0.03, z0)
        bx(m, BLACKMET, (dx0 + dx1) / 2 - 0.04, (dx0 + dx1) / 2 + 0.04,
           2.30, 2.66, z0 - 0.07, z0 - 0.03)
    for cx in (x0 + 1.95, x1 - 1.95):               # two rectangular basins
        bx(m, Material("basin", "#eceae7", roughness=0.28),
           cx - 0.95, cx + 0.95, 2.78, 2.92, z0 + 0.45, z1 - 0.45)
        bx(m, BLACKMET, cx - 0.05, cx + 0.05, 3.02, 3.55, z0 + 0.30, z0 + 0.40)
        bx(m, BLACKMET, cx - 0.05, cx + 0.05, 3.45, 3.55, z0 + 0.40, z0 + 0.80)
        bx(m, Material("mirror", "#eaeef0", roughness=0.86, metallic=0.0),
           cx - 1.30, cx + 1.30, 3.70, 6.55, z1 - 0.04, z1)
        bx(m, BLACKMET, cx - 1.36, cx + 1.36, 3.64, 3.70, z1 - 0.06, z1)
        bx(m, BLACKMET, cx - 1.36, cx + 1.36, 6.55, 6.61, z1 - 0.06, z1)
    # toilet, SW corner against the south wall
    tx, tz = 3.10, z1 - 0.95
    contact_shadow(m, tx, tz, 1.05, 1.35, y=0.010, strength=0.22, room=(W, D))
    m.add(rounded_box(1.30, 1.20, 1.55, r=0.30, seg=3), PORC, at=(tx, 0.0, tz))
    m.add(rounded_box(1.42, 0.26, 1.75, r=0.42, seg=4), PORC, at=(tx, 1.18, tz - 0.18))
    bx(m, PORC, tx - 0.85, tx + 0.85, 1.20, 2.55, z1 - 0.72, z1 - 0.06)
    bx(m, PORC, tx - 0.72, tx + 0.72, 2.55, 2.66, z1 - 0.78, z1 - 0.02)
    return m


if __name__ == "__main__":
    print("room 16 Master Bath.")
    surfaces(ROOM, wall_color="#e6e3dd", floor_color="#6b6967",
             floor_texture="wood")
    shell()
    save_and_place("Master Bath Tub", tub(), ROOM)
    save_and_place("Master Bath Shower", shower(), ROOM)
    save_and_place("Master Bath Vanity", vanity(), ROOM)
