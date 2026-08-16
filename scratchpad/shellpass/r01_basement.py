"""Level 0 shells: 1 Movie Room (17.0 x 23.5) and 2 Arcade Room (20.7 x 23.3).

Photos: 'Movie room.jpg', 'Arcade Room.jpg'.

Both basement rooms are the same shell: white ceiling with recessed cans AND
flush in-ceiling speaker grilles, white crown, a chair rail with a slightly
deeper grey below it (clear in the movie-room shot), tall white baseboards,
grey plank floor and a very large pale rug that covers most of it.  The rugs
are named "... Floor Rug" so objects.js keeps them unpickable -- they span most
of the footprint and would otherwise swallow every click in the room.
"""

from kit import *

WOOD = "#6b6967"


# ============================================================== 1 movie room
def movie():
    ROOM, W, D, H = 1, 17.0, 23.5, 8.0
    print("room 1 Movie Room")
    surfaces(ROOM, wall_color="#dcdbd8", floor_color=WOOD, floor_texture="wood")
    DOOR = (13.40, 16.10)        # north wall, right of the screen
    WIN = (1.80, 4.20)           # west wall -- the high basement window

    m = ceiling(W, D, H,
                cans=[(2.6, 2.6), (8.5, 2.6), (14.4, 2.6),
                      (2.6, 8.4), (14.4, 8.4),
                      (2.6, 14.2), (8.5, 14.2), (14.4, 14.2),
                      (5.5, 20.0), (11.5, 20.0)],
                speakers=[(5.5, 5.4, 0.55), (11.5, 5.4, 0.55),
                          (5.5, 17.0, 0.55), (11.5, 17.0, 0.55)],
                vents=[(8.5, 6.9, 1.00, 0.55)])
    save_and_place("Movie Ceiling", m, ROOM)

    m = baseboards(W, D, rail=3.35, wainscot="#c3c2bf",
                   doors=[("n", *DOOR)])
    door_unit(m, "n", W, D, *DOOR)
    window_unit(m, "w", W, D, WIN[0], WIN[1], sill=6.10, head=7.35)
    save_and_place("Movie Baseboards", m, ROOM)

    # ---- the screen wall: big black panel, media console, two black subs
    m = Model()
    BLK = Material("mblk", "#101114", roughness=0.35)
    GREYWD = Material("mgw", "#9a9a96", roughness=0.62)
    bx(m, BLK, 3.30, 11.10, 3.55, 7.05, 0.06, 0.16)
    bx(m, Material("mbez", "#2b2c30", roughness=0.5),
       3.22, 11.18, 3.47, 7.13, 0.04, 0.09)
    # media console
    cx0, cx1 = 4.60, 9.80
    contact_shadow(m, (cx0 + cx1) / 2, 0.95, 3.30, 1.35, y=0.010,
                   strength=0.22, room=(W, D))
    bx(m, GREYWD, cx0, cx1, 0.42, 2.35, 0.14, 1.65)
    for i in range(4):
        dx0 = cx0 + 0.10 + i * (cx1 - cx0 - 0.20) / 4
        bx(m, Material("mgw2", "#8d8d89", roughness=0.64),
           dx0, dx0 + (cx1 - cx0 - 0.20) / 4 - 0.07, 0.52, 2.25, 1.65, 1.68)
    for px in (cx0 + 0.20, cx1 - 0.32):
        bx(m, BLACKMET, px, px + 0.12, 0.0, 0.42, 0.30, 0.42)
        bx(m, BLACKMET, px, px + 0.12, 0.0, 0.42, 1.35, 1.47)
    # the two black subwoofer boxes either side
    for sx in (3.05, 10.95):
        contact_shadow(m, sx + 0.75, 0.95, 1.15, 1.15, y=0.010,
                       strength=0.20, room=(W, D))
        bx(m, BLK, sx, sx + 1.50, 0.0, 1.75, 0.20, 1.70)
    save_and_place("Movie Screen Wall", m, ROOM)

    save_and_place("Movie Floor Rug",
                   big_rug(W, D, 1.30, 15.70, 5.20, 21.40,
                           "#eae6dc", "#ded9cd", 0.10), ROOM)


# ============================================================= 2 arcade room
def arcade():
    ROOM, W, D, H = 2, 20.7, 23.3, 8.0
    print("room 2 Arcade Room")
    surfaces(ROOM, wall_color="#e4e2de", floor_color=WOOD, floor_texture="wood")
    DOOR = (9.40, 12.10)         # north wall

    m = ceiling(W, D, H,
                cans=[(3.2, 2.8), (10.3, 2.8), (17.5, 2.8),
                      (3.2, 9.6), (17.5, 9.6),
                      (3.2, 16.4), (10.3, 16.4), (17.5, 16.4),
                      (7.0, 21.2), (13.6, 21.2)],
                speakers=[(6.8, 6.0, 0.52), (13.9, 6.0, 0.52),
                          (6.8, 18.5, 0.52), (13.9, 18.5, 0.52)],
                vents=[(10.3, 6.4, 1.00, 0.55)])
    save_and_place("Arcade Ceiling", m, ROOM)

    m = baseboards(W, D, doors=[("n", *DOOR)])
    door_unit(m, "n", W, D, *DOOR)
    save_and_place("Arcade Baseboards", m, ROOM)

    save_and_place("Arcade Floor Rug",
                   big_rug(W, D, 2.60, 18.10, 6.40, 20.60,
                           "#d9d7d2", "#cbc8c3", 0.10), ROOM)
    save_and_place("Arcade Cabinets", cabinets(W, D), ROOM)


def cabinets(W, D):
    """Two runs of upright arcade cabinets -- the one thing that makes this
    room read as an arcade from 50 degrees up.  Colour-blocked marquees, not
    modelled art."""
    m = Model()
    CAB = Material("cab", "#25262a", roughness=0.6)
    SCR = Material("cscr", "#15161a", roughness=0.35)
    CP = Material("cctl", "#3a3c42", roughness=0.6)
    HUES = ["#c0392b", "#2b6fc0", "#e0a21c", "#2fa15a", "#8e44ad",
            "#d4562a", "#1f9ec4", "#c9333f"]

    def cab_at(cx, cz, rot, hue):
        """One 2.3 x 2.6 ft upright, `rot` = 0 back to north, 90 back to west."""
        sub = Model()
        bw, bd = 2.30, 2.55
        contact_shadow(sub, 0, 0.30, 1.55, 1.75, y=0.010, strength=0.24)
        bx(sub, CAB, -bw / 2, bw / 2, 0.0, 6.10, -bd / 2, bd / 2 - 0.55)
        bx(sub, CAB, -bw / 2, bw / 2, 0.0, 3.05, bd / 2 - 0.55, bd / 2)
        bx(sub, CP, -bw / 2 + 0.10, bw / 2 - 0.10, 3.05, 3.20,
           bd / 2 - 0.62, bd / 2)
        bx(sub, SCR, -bw / 2 + 0.12, bw / 2 - 0.12, 3.45, 5.15,
           bd / 2 - 0.60, bd / 2 - 0.52)
        mat = Material("marq" + hue[1:], hue, roughness=0.55,
                       emissive=hue, emissive_strength=1.1)
        bx(sub, mat, -bw / 2 + 0.08, bw / 2 - 0.08, 5.30, 6.02,
           bd / 2 - 0.60, bd / 2 - 0.52)
        bx(sub, mat, -bw / 2 + 0.08, bw / 2 - 0.08, 0.30, 2.85,
           bd / 2 - 0.02, bd / 2)
        ca, sa = math.cos(R(rot)), math.sin(R(rot))
        for part, mm in sub._parts:
            v = [(cx + x * ca + z * sa, y, cz - x * sa + z * ca)
                 for (x, y, z) in part.verts]
            m._parts.append((Part(v, part.tris, part.smooth), mm))

    # west run, backs to the west wall, facing east
    for i in range(6):
        cab_at(1.40, 3.20 + i * 2.55, 90, HUES[i % len(HUES)])
    # east run, backs to the east wall, facing west
    for i in range(6):
        cab_at(W - 1.40, 3.60 + i * 2.55, 270, HUES[(i + 3) % len(HUES)])
    return m


def big_rug(W, D, x0, x1, z0, z1, c0, c1, y):
    m = Model()
    contact_shadow(m, (x0 + x1) / 2, (z0 + z1) / 2, (x1 - x0) * 0.53,
                   (z1 - z0) * 0.53, y=0.008, strength=0.10, room=(W, D))
    A = Material("rugA" + c0[1:], c0, roughness=0.98)
    B = Material("rugB" + c1[1:], c1, roughness=0.98)
    bx(m, B, x0, x1, 0.014, 0.052, z0, z1)
    bx(m, A, x0 + 0.16, x1 - 0.16, 0.052, 0.064, z0 + 0.16, z1 - 0.16)
    return m


if __name__ == "__main__":
    movie()
    arcade()
