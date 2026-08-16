"""Room 8 -- Office (level 1, 10.6 x 11.6 x 9.0).

Photos: 'Office A.jpg' (primary), B, C, f.  The room's signature is a TWO-TONE
wall: greige above a chair rail at ~3.3 ft, dark charcoal wainscot below it,
white crown at 9 ft, tall white baseboards, grey plank floor, four cans.

Adjacency: bathroom 23 is west, office printers 22 and laundry 9 are south,
NORTH (z=0) and EAST (x=10.6) are exterior -- photo A's tall window is on the
east wall.
"""

from kit import *
from kit import _blit

ROOM, W, D, H = 8, 10.6, 11.6, 9.0
RAIL = 3.30
D_W1 = (0.90, 3.60)          # west wall -- plain door
D_W2 = (5.60, 8.60)          # west wall -- the glazed french door (photo B)
OPEN_S = (6.00, 9.00)        # south wall -- cased opening to the printer nook
WIN = (1.20, 4.00)           # east wall -- the tall window


def shell():
    out = []
    m = ceiling(W, D, H,
                cans=[(2.6, 2.7), (7.9, 2.7), (2.6, 8.4), (7.9, 8.4)],
                vents=[(5.30, 1.10, 0.95, 0.52)])
    out.append(save_and_place("Office Ceiling", m, ROOM))

    m = baseboards(W, D, rail=RAIL, wainscot="#3e4145",
                   doors=[("w", *D_W1), ("w", *D_W2), ("s", *OPEN_S)])
    door_unit(m, "w", W, D, *D_W1)
    french_door(m, "w", W, D, *D_W2)
    cased_opening(m, "s", W, D, *OPEN_S, top=7.20)
    window_unit(m, "e", W, D, WIN[0], WIN[1], sill=2.30, head=7.10)
    out.append(save_and_place("Office Baseboards", m, ROOM))
    return out


def french_door(m, wall, W, D, a0, a1):
    """The glazed 15-lite door photo B shows -- white stiles, clear panes."""
    sub = Model()
    bx(sub, WHITEWD, a0 + 0.03, a1 - 0.03, 0.0, DOOR_TOP, 0.0, 0.145)
    gw, gh = (a1 - a0) - 0.60, DOOR_TOP - 1.05
    for r in range(5):
        for c in range(3):
            px = a0 + 0.30 + c * gw / 3
            py = 0.60 + r * gh / 5
            bx(sub, GLASS, px + 0.05, px + gw / 3 - 0.05,
               py + 0.05, py + gh / 5 - 0.05, 0.03, 0.115)
    for a, b in ((a0 - CASE_W, a0 + 0.03), (a1 - 0.03, a1 + CASE_W)):
        bx(sub, TRIM, a, b, 0.0, DOOR_TOP + CASE_W, 0.0, 0.20)
    bx(sub, TRIM, a0 - CASE_W, a1 + CASE_W, DOOR_TOP, DOOR_TOP + CASE_W, 0.0, 0.20)
    sub.add(cylinder(0.08, 0.05, 12), BLACKMET, at=(a1 - 0.40, 3.05, 0.20),
            rot_x=R(90))
    _blit(m, sub, wall, W, D, 0.0)


# ------------------------------------------------------------------- pieces
DESKTOP = Material("desktop", "#6d6f72", roughness=0.60)
DESKLEG = Material("deskleg", "#2b2d30", roughness=0.5, metallic=0.3)
SCREEN = Material("screen", "#141518", roughness=0.35)
MESH = Material("mesh", "#b9bbbc", roughness=0.85)


def desks():
    """The L-desk in the NW corner with the ultrawide monitor (photo A) and
    the second desk along the east wall.  Chunky enough to read at 50 deg."""
    m = Model()

    def slab(x0, x1, z0, z1, h=2.48):
        contact_shadow(m, (x0 + x1) / 2, (z0 + z1) / 2, (x1 - x0) * 0.56,
                       (z1 - z0) * 0.62, y=0.010, strength=0.20, room=(W, D))
        bx(m, DESKTOP, x0, x1, h, h + 0.13, z0, z1)
        for px in (x0 + 0.25, x1 - 0.45):
            for pz in (z0 + 0.20, z1 - 0.40):
                bx(m, DESKLEG, px, px + 0.20, 0.0, h, pz, pz + 0.20)

    # L desk: north leg + west leg
    slab(0.35, 6.40, 0.20, 2.75)
    slab(0.35, 2.90, 2.75, 6.30)
    # ultrawide monitor on the north leg
    bx(m, DESKLEG, 2.85, 3.55, 2.61, 3.05, 1.05, 1.60)
    bx(m, SCREEN, 1.55, 5.30, 3.05, 5.05, 1.10, 1.28)
    bx(m, DESKLEG, 1.48, 5.37, 2.98, 5.12, 1.28, 1.36)
    m.add(cylinder(0.13, 0.30, 10), BLACKMET, at=(3.42, 5.12, 1.22))
    # keyboard + mouse
    bx(m, DESKLEG, 2.55, 4.35, 2.61, 2.67, 1.95, 2.45)
    m.add(rounded_box(0.28, 0.16, 0.42, r=0.07, seg=3), MESH, at=(4.70, 2.61, 2.15))
    # white pedestal drawers under the north leg
    bx(m, Material("ped", "#eceae6", roughness=0.62), 4.55, 5.90, 0.0, 2.40,
       0.55, 2.55)
    for i in range(3):
        bx(m, Material("pedd", "#e2dfda", roughness=0.62),
           4.62, 5.83, 0.30 + i * 0.68, 0.92 + i * 0.68, 2.55, 2.58)

    # mesh task chair
    cx, cz = 4.10, 4.30
    contact_shadow(m, cx, cz, 1.30, 1.30, y=0.010, strength=0.20, room=(W, D))
    m.add(cylinder(0.14, 1.35, 10), DESKLEG, at=(cx, 0.0, cz))
    for k in range(5):
        a = 2 * math.pi * k / 5
        bx(m, DESKLEG, cx - 0.06, cx + 0.06, 0.10, 0.22, cz - 0.05, cz + 1.05)
        m._parts[-1] = (_rot_about(m._parts[-1][0], cx, cz, a), DESKLEG)
    m.add(rounded_box(1.75, 0.34, 1.70, r=0.20, seg=3), MESH, at=(cx, 1.35, cz))
    m.add(rounded_box(1.62, 2.05, 0.30, r=0.16, seg=3), MESH,
          at=(cx, 1.65, cz + 0.72), rot_x=R(-9))

    # second desk on the east wall with a monitor
    slab(7.10, 10.35, 3.10, 8.10, h=2.42)
    bx(m, DESKLEG, 9.55, 10.20, 2.55, 3.00, 5.20, 5.90)
    bx(m, SCREEN, 9.75, 9.93, 3.00, 5.05, 4.05, 7.05)
    bx(m, DESKLEG, 9.68, 9.76, 2.93, 5.12, 3.98, 7.12)
    return m


def _rot_about(part, cx, cz, a):
    ca, sa = math.cos(a), math.sin(a)
    v = [(cx + (x - cx) * ca - (z - cz) * sa, y,
          cz + (x - cx) * sa + (z - cz) * ca) for (x, y, z) in part.verts]
    return Part(v, part.tris, part.smooth)


if __name__ == "__main__":
    print("room 8 Office")
    surfaces(ROOM, wall_color="#dedbd4", floor_color="#6b6967",
             floor_texture="wood")
    shell()
    save_and_place("Office Desks", desks(), ROOM)
