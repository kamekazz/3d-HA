"""Level 1 shells: 12 First floor hallway, 23 Bathroom, 9 Laundry,
10 Pantry, 22 Office printers, 7 Garage.

Photos: 'First floor hallway*.jpg', 'Bathroom.jpg' / 'Bathroom A.jpg',
'Laundry.jpg', 'pantry door.jpg', 'First-floor bathroom.jpg' (which is in fact
the printer nook seen from the office -- the office's charcoal wainscot frames
the shot), and the garage has no photo (floor plan + construction sense).

NOTE ON BATHROOM FLOORS: the brief said tile.  'Bathroom.jpg' shows the same
light grey wood-look PLANK as the hall running under the vanity and up to the
shower curb; only the shower pan and the surround are tile.  Photo wins.
"""

from kit import *
from kit import _blit


# ===================================================== 12 first floor hallway
def hallway():
    ROOM, W, D, H = 12, 7.6, 27.6, 9.0
    print("room 12 First floor hallway")
    surfaces(ROOM, wall_color="#dcdcdb", floor_color="#6b6967",
             floor_texture="wood")

    # world z 16.29..19.69 is the cased opening the kitchen already cut in
    # this shared wall -- gap the skirting there but do not stand a leaf in it
    KITCHEN = (11.69, 15.09)
    D_W1 = (3.00, 5.70)          # 6-panel door, west wall (photo 1)
    DINING = (19.00, 23.00)      # cased opening through to Dining
    D_PANTRY = (3.20, 7.90)      # east wall, double doors
    D_GARAGE = (9.20, 11.90)     # east wall, 6-panel
    LIVING = (1.00, 6.60)        # north wall, wide cased opening
    FRONT = (2.20, 5.40)         # south wall, the front door

    # the stairwell is open to the floor above: cut the ceiling round it
    m = ceiling(W, D, H, hole=(3.78, W, 9.55, 20.05),
                cans=[(2.0, 3.0), (2.0, 7.6), (2.0, 12.2), (2.0, 16.8),
                      (2.0, 21.4), (5.6, 24.6)],
                fixtures=[(1.90, 25.9, 0.62)],
                vents=[(1.10, 21.6, 0.52, 0.95)])
    save_and_place("Hall1F Ceiling", m, ROOM)

    m = baseboards(W, D, doors=[("w", *KITCHEN), ("w", *D_W1), ("w", *DINING),
                                ("e", *D_PANTRY), ("e", *D_GARAGE),
                                ("n", *LIVING), ("s", *FRONT)])
    door_unit(m, "w", W, D, *D_W1)
    door_unit(m, "e", W, D, *D_PANTRY, panels=2)
    door_unit(m, "e", W, D, *D_GARAGE)
    cased_opening(m, "w", W, D, *KITCHEN, top=7.20)
    cased_opening(m, "w", W, D, *DINING, top=7.20)
    cased_opening(m, "n", W, D, *LIVING, top=7.20)
    front_door(m, "s", W, D, *FRONT)
    save_and_place("Hall1F Baseboards", m, ROOM)

    save_and_place("Hall1F Balustrade", balustrade(), ROOM)
    save_and_place("Hall1F Floor Runner", hall_runner(), ROOM)


def front_door(m, wall, W, D, a0, a1):
    sub = Model()
    panel_door(sub, WHITEWD, a0 + 0.03, a1 - 0.03, 0.0, 7.05, 0.0, 0.19, rows=2)
    for a, b in ((a0 - 0.34, a0 + 0.03), (a1 - 0.03, a1 + 0.34)):
        bx(sub, TRIM, a, b, 0.0, 7.42, 0.0, 0.24)
    bx(sub, TRIM, a0 - 0.34, a1 + 0.34, 7.05, 7.42, 0.0, 0.24)
    sub.add(cylinder(0.09, 0.06, 12), BLACKMET, at=(a1 - 0.45, 3.05, 0.25),
            rot_x=R(90))
    _blit(m, sub, wall, W, D, 0.0)


def balustrade():
    """The staircase rail: square white newel, turned white balusters and the
    BLACK handrail every hallway photo leads with.  The level-1 stair runs
    world x 14.6..18.4 / z 14.3..24.5 rising north, i.e. local x 3.9..7.7 /
    z 9.7..19.9 -- so the rail stands on the west edge at x = 3.90 and the
    newel is at its SOUTH end, the bottom of the flight."""
    m = Model()
    x = 3.90
    z_bot, z_top = 19.90, 9.70
    RISE = 9.0 / (z_bot - z_top)          # the flight climbs a full storey

    def y_at(z):
        return max(0.0, min(8.6, (z_bot - z) * RISE))

    # skirt board following the rake
    n = 34
    for i in range(n):
        z0 = z_bot - i * (z_bot - z_top) / n
        z1 = z0 - (z_bot - z_top) / n
        y = y_at((z0 + z1) / 2)
        bx(m, TRIM, x - 0.11, x, max(0.0, y - 0.62), y + 0.06, z1, z0)
    # balusters
    i = 0
    z = z_bot - 0.55
    while z > z_top + 0.20:
        y = y_at(z)
        m.add(cylinder(0.052, 2.55, 8), TRIM, at=(x - 0.055, y, z))
        m.add(cylinder(0.088, 0.42, 8), TRIM, at=(x - 0.055, y + 0.55, z))
        m.add(cylinder(0.082, 0.30, 8), TRIM, at=(x - 0.055, y + 1.45, z))
        z -= 0.42
        i += 1
    # black handrail, raked
    for k in range(n):
        z0 = z_bot - k * (z_bot - z_top) / n
        z1 = z0 - (z_bot - z_top) / n
        y = y_at((z0 + z1) / 2)
        bx(m, BLACKMET, x - 0.17, x + 0.03, y + 2.55, y + 2.78, z1, z0)
    # newel post at the bottom + its cap
    bx(m, TRIM, x - 0.22, x + 0.08, 0.0, 3.05, z_bot - 0.15, z_bot + 0.15)
    bx(m, BLACKMET, x - 0.28, x + 0.14, 3.05, 3.42, z_bot - 0.21, z_bot + 0.21)
    return m


def hall_runner():
    m = Model()
    W, D = 7.6, 27.6
    x0, x1, z0, z1 = 0.55, 3.45, 1.60, 9.20
    contact_shadow(m, (x0 + x1) / 2, (z0 + z1) / 2, 1.60, 3.60, y=0.008,
                   strength=0.12, room=(W, D))
    JUTE = Material("jute", "#d9d2c4", roughness=0.98)
    JUTE2 = Material("jute2", "#cbc3b3", roughness=0.98)
    bx(m, JUTE, x0, x1, 0.016, 0.058, z0, z1)
    for i in range(int((z1 - z0) / 0.36)):
        z = z0 + 0.08 + i * 0.36
        bx(m, JUTE2, x0 + 0.05, x1 - 0.05, 0.058, 0.068, z, z + 0.17)
    return m


# ================================================================ 23 bathroom
def bathroom():
    ROOM, W, D, H = 23, 9.9, 7.4, 8.0
    print("room 23 Bathroom")
    surfaces(ROOM, wall_color="#eeece8", floor_color="#7c7a78",
             floor_texture="wood")
    DOOR = (2.20, 4.90)                     # west wall, local z
    save_and_place("Bath1F Ceiling",
                   ceiling(W, D, H, cans=[(2.4, 2.2), (7.4, 2.2)],
                           fixtures=[(4.9, 5.4, 0.55)],
                           vents=[(5.60, 1.05, 0.95, 0.52)]), ROOM)
    m = baseboards(W, D, doors=[("w", *DOOR)])
    door_unit(m, "w", W, D, *DOOR)
    save_and_place("Bath1F Baseboards", m, ROOM)

    # ---- grey shaker vanity + round mirror + black 3-light bar + toilet
    m = Model()
    x0, x1, z0, z1 = 0.30, 3.85, 0.12, 2.05
    contact_shadow(m, (x0 + x1) / 2, z1 - 0.75, (x1 - x0) * 0.58, 1.55,
                   y=0.010, strength=0.22, room=(W, D))
    bx(m, GREYCAB, x0, x1, 0.28, 2.85, z0, z1)
    bx(m, Material("b1top", "#f5f4f2", roughness=0.30),
       x0 - 0.05, x1 + 0.05, 2.85, 2.97, z0, z1 + 0.05)
    for i in range(2):
        dx0 = x0 + 0.12 + i * ((x1 - x0 - 0.24) / 2)
        dx1 = dx0 + (x1 - x0 - 0.24) / 2 - 0.08
        bx(m, Material("b1door", "#9ea3a6", roughness=0.62),
           dx0, dx1, 0.40, 2.72, z1, z1 + 0.03)
        bx(m, BLACKMET, (dx0 + dx1) / 2 - 0.04, (dx0 + dx1) / 2 + 0.04,
           2.25, 2.60, z1 + 0.03, z1 + 0.10)
    bx(m, Material("b1basin", "#eeedeb", roughness=0.28),
       x0 + 0.55, x1 - 0.55, 2.72, 2.88, z0 + 0.35, z1 - 0.35)
    bx(m, BLACKMET, (x0 + x1) / 2 - 0.05, (x0 + x1) / 2 + 0.05, 2.97, 3.55,
       z0 + 0.22, z0 + 0.32)
    bx(m, BLACKMET, (x0 + x1) / 2 - 0.05, (x0 + x1) / 2 + 0.05, 3.45, 3.55,
       z0 + 0.32, z0 + 0.72)
    # round mirror + three-light bar on the north wall
    m.add(cylinder(1.05, 0.05, 26), Material("b1mir", "#eaeef0",
          roughness=0.86, metallic=0.0), at=((x0 + x1) / 2, 3.95, 0.055),
          rot_x=R(90))
    m.add(cylinder(1.14, 0.04, 26), BLACKMET, at=((x0 + x1) / 2, 3.93, 0.035),
          rot_x=R(90))
    bx(m, BLACKMET, (x0 + x1) / 2 - 1.05, (x0 + x1) / 2 + 1.05, 6.20, 6.30,
       0.06, 0.16)
    for k in (-0.72, 0.0, 0.72):
        bx(m, BLACKMET, (x0 + x1) / 2 + k - 0.20, (x0 + x1) / 2 + k + 0.20,
           5.72, 6.22, 0.10, 0.50)
        rect_down(m, LENS, (x0 + x1) / 2 + k - 0.17, (x0 + x1) / 2 + k + 0.17,
                  5.73, 0.13, 0.47)
    # toilet
    tx, tz = 5.15, 1.05
    contact_shadow(m, tx, tz, 1.05, 1.35, y=0.010, strength=0.20, room=(W, D))
    m.add(rounded_box(1.28, 1.18, 1.52, r=0.28, seg=3), PORC, at=(tx, 0.0, tz))
    m.add(rounded_box(1.40, 0.25, 1.72, r=0.42, seg=4), PORC,
          at=(tx, 1.16, tz + 0.16))
    bx(m, PORC, tx - 0.84, tx + 0.84, 1.18, 2.52, 0.06, 0.72)
    bx(m, PORC, tx - 0.72, tx + 0.72, 2.52, 2.63, 0.02, 0.78)
    save_and_place("Bath1F Vanity", m, ROOM)

    # ---- white subway shower with a black-framed slider, east end
    m = Model()
    x0, x1, z0, z1 = 6.15, 9.75, 0.15, 5.05
    bx(m, GROUT, x0, x1, 0.0, 7.00, z0, z0 + 0.10)
    bx(m, GROUT, x1 - 0.10, x1, 0.0, 7.00, z0, z1)
    for r in range(24):
        y = 0.36 + r * 0.275
        off = 0.0 if r % 2 == 0 else 0.42
        for c in range(6):
            tx2 = x0 + 0.06 + off + c * 0.84
            if tx2 + 0.78 < x1 - 0.10:
                bx(m, TILEW, tx2, tx2 + 0.78, y, y + 0.24, z0 + 0.10, z0 + 0.135)
        for c in range(6):
            tz = z0 + 0.06 + off + c * 0.84
            if tz + 0.78 < z1:
                bx(m, TILEW, x1 - 0.135, x1 - 0.10, y, y + 0.24, tz, tz + 0.78)
    bx(m, Material("b1pan", "#f0f0ef", roughness=0.42), x0, x1, 0.0, 0.36, z0, z1)
    bx(m, GLASS, x0, x0 + 1.85, 0.36, 6.50, z1 - 0.14, z1 - 0.10)
    bx(m, GLASS, x0 + 1.75, x1, 0.36, 6.50, z1 - 0.06, z1 - 0.02)
    for a, b in ((x0, x0 + 0.08), (x0 + 1.75, x0 + 1.85), (x1 - 0.08, x1)):
        bx(m, BLACKMET, a, b, 0.36, 6.56, z1 - 0.16, z1 - 0.02)
    bx(m, BLACKMET, x0, x1, 6.46, 6.56, z1 - 0.16, z1 - 0.02)
    bx(m, BLACKMET, x0 + 0.55, x0 + 0.63, 2.60, 4.30, z1 - 0.22, z1 - 0.14)
    bx(m, BLACKMET, x1 - 1.30, x1 - 1.22, 4.70, 5.95, z0 + 0.135, z0 + 0.22)
    m.add(cylinder(0.32, 0.09, 12), BLACKMET, at=(x1 - 1.26, 5.88, z0 + 0.82))
    save_and_place("Bath1F Shower", m, ROOM)


# ================================================================= 9 laundry
def laundry():
    # STALE FOOTPRINT -- DO NOT RUN THIS FUNCTION.  Room 9 was re-traced from
    # 11.0 x 5.7 to 4.4 x 5.7 (world x 28.5-32.9); everything below is 6.6 ft
    # east of the room and lands in room 22.  The laundry's ceiling,
    # baseboards, doors and wall skins are rebuilt at the real size by
    # scratchpad/laundry2/l9.py -- run that instead.
    raise SystemExit("r12_l1rest.laundry() is stale; run scratchpad/laundry2/l9.py")
    ROOM, W, D, H = 9, 11.0, 5.7, 9.0
    print("room 9 Laundry")
    surfaces(ROOM, wall_color="#dbdbda", floor_color="#6b6967",
             floor_texture="wood")
    D_W = (1.50, 4.20)         # west wall -> pantry / hall
    D_S = (7.40, 10.10)        # south wall -> garage
    save_and_place("Laundry Ceiling",
                   ceiling(W, D, H, cans=[(2.4, 1.5), (6.6, 1.5)],
                           vents=[(9.0, 4.6, 0.90, 0.50)]), ROOM)
    m = baseboards(W, D, doors=[("w", *D_W), ("s", *D_S)])
    door_unit(m, "w", W, D, *D_W)
    door_unit(m, "s", W, D, *D_S)
    save_and_place("Laundry Baseboards", m, ROOM)

    # ---- the washer/dryer pair with white uppers and a floating shelf
    m = Model()
    WHT = Material("lwht", "#f0efec", roughness=0.6)
    WHT2 = Material("lwht2", "#e5e3de", roughness=0.62)
    contact_shadow(m, 2.85, 1.30, 3.15, 1.75, y=0.010, strength=0.22,
                   room=(W, D))
    # top-load washer (photo left) and front-load dryer (photo right)
    bx(m, WHT, 0.45, 2.75, 0.0, 3.05, 0.20, 2.55)
    bx(m, BLACKMET, 0.55, 2.65, 3.05, 3.14, 0.30, 2.45)
    bx(m, BLACKMET, 0.60, 2.60, 2.72, 2.82, 0.16, 0.22)      # control strip
    bx(m, WHT, 2.90, 5.25, 0.0, 3.05, 0.20, 2.55)
    m.add(cylinder(0.78, 0.09, 22), Material("ldoor", "#d3d6d8",
          roughness=0.25, metallic=0.3), at=(4.05, 1.55, 0.16), rot_x=R(90))
    m.add(cylinder(0.88, 0.05, 22), WHT2, at=(4.05, 1.55, 0.13), rot_x=R(90))
    bx(m, BLACKMET, 3.05, 5.10, 2.70, 2.82, 0.16, 0.22)
    # upper cabinets left + right, floating shelf between
    bx(m, WHT, 0.25, 2.35, 4.90, 8.05, 0.10, 1.55)
    bx(m, WHT2, 0.33, 2.27, 4.98, 7.97, 1.55, 1.60)
    bx(m, WHT, 3.95, 5.55, 4.90, 8.05, 0.10, 1.55)
    bx(m, WHT2, 4.03, 5.47, 4.98, 7.97, 1.55, 1.60)
    bx(m, WHT, 0.25, 5.55, 4.62, 4.78, 0.10, 1.05)           # floating shelf
    bx(m, WHT, 2.35, 3.95, 5.30, 5.44, 0.10, 0.95)
    for bxx in (2.55, 3.30):                                  # woven baskets
        bx(m, Material("basket", "#b79a72", roughness=0.9),
           bxx, bxx + 0.62, 4.78, 5.25, 0.25, 0.90)
    bx(m, Material("lart", "#26272b", roughness=0.8), 2.55, 3.75, 6.10, 7.65,
       0.10, 0.14)
    save_and_place("Laundry Washer Dryer", m, ROOM)


# ================================================================== 10 pantry
def pantry():
    ROOM, W, D, H = 10, 3.1, 5.7, 9.0
    print("room 10 Pantry")
    surfaces(ROOM, wall_color="#dcdcdb", floor_color="#6b6967",
             floor_texture="wood")
    save_and_place("Pantry Ceiling",
                   ceiling(W, D, H, cans=[(1.55, 2.85)]), ROOM)
    m = baseboards(W, D, doors=[("w", 0.55, 5.15)])
    SHELF = Material("pshelf", "#f0efec", roughness=0.62)
    for i in range(5):                       # open pantry shelving, east wall
        y = 1.20 + i * 1.30
        bx(m, SHELF, W - 1.15, W - 0.09, y, y + 0.09, 0.35, D - 0.35)
    save_and_place("Pantry Baseboards", m, ROOM)


# ========================================================= 22 office printers
def printers():
    ROOM, W, D, H = 22, 6.2, 5.8, 8.0
    print("room 22 Office printers")
    surfaces(ROOM, wall_color="#e2dfd8", floor_color="#6b6967",
             floor_texture="wood")
    save_and_place("Printers Ceiling",
                   ceiling(W, D, H, cans=[(1.9, 2.7), (4.5, 2.7)]), ROOM)
    m = baseboards(W, D, doors=[("n", 1.60, 4.60)])
    cased_opening(m, "n", W, D, 1.60, 4.60, top=7.20)
    save_and_place("Printers Baseboards", m, ROOM)


# =================================================================== 7 garage
def garage():
    ROOM, W, D, H = 7, 20.4, 21.7, 9.0
    print("room 7 Garage")
    surfaces(ROOM, wall_color="#dad7d0", floor_color="#8e8d89",
             floor_texture="concrete")
    m = ceiling(W, D, H, crown=False,
                fixtures=[(5.5, 7.0, 0.75), (14.5, 7.0, 0.75),
                          (5.5, 15.0, 0.75), (14.5, 15.0, 0.75)])
    save_and_place("Garage Ceiling", m, ROOM)

    # no skirting in a garage -- a poured concrete curb instead
    m = Model()
    CURB = Material("curb", "#a5a49f", roughness=0.95)
    for w in "nswe":
        wall_band(m, CURB, w, W, D, 0.0, 0.42, 0.09,
                  gaps={"n": [(2.70, 6.00)], "s": [(1.90, 18.50)]}.get(w, ()))
    door_unit(m, "n", W, D, 3.00, 5.70)
    save_and_place("Garage Baseboards", m, ROOM)

    # ---- the sectional garage door on the south (street) wall
    m = Model()
    PAN = Material("gpan", "#e9e7e2", roughness=0.72)
    PAN2 = Material("gpan2", "#d8d5cf", roughness=0.74)
    x0, x1 = 2.10, 18.30
    for r in range(5):
        y = 0.05 + r * 1.53
        bx(m, PAN, x0, x1, y, y + 1.44, D - 0.30, D - 0.14)
        bx(m, PAN2, x0 + 0.12, x1 - 0.12, y + 0.10, y + 1.34, D - 0.35, D - 0.30)
        if r == 3:                            # the row of lites
            for c in range(4):
                px = x0 + 1.4 + c * (x1 - x0 - 2.8) / 4
                bx(m, GLASS, px, px + (x1 - x0 - 2.8) / 4 - 0.35,
                   y + 0.30, y + 1.14, D - 0.36, D - 0.32)
    bx(m, TRIM, x0 - 0.34, x1 + 0.34, 7.70, 8.10, D - 0.42, D - 0.10)
    bx(m, TRIM, x0 - 0.34, x0, 0.0, 7.80, D - 0.42, D - 0.10)
    bx(m, TRIM, x1, x1 + 0.34, 0.0, 7.80, D - 0.42, D - 0.10)
    save_and_place("Garage Door Panel", m, ROOM)


if __name__ == "__main__":
    hallway()
    bathroom()
    laundry()
    pantry()
    printers()
    garage()
