"""Room 26 -- bath, second floor (8.1 x 8.7 x 8.0).  FURNISHING PASS.

ORIENTATION (derived before anything was modelled)
--------------------------------------------------
World rect x 10.5..18.6, z 23.4..32.1.  Local x 0 = WEST, 8.1 = EAST;
local z 0 = NORTH, 8.7 = SOUTH (house.js: north = -Z).

Adjacency (roomkit.rooms --list / GET /api/house):
    Hallway 17    x 10.5..18.6  z  6.6..23.3  -> NORTH wall, exact x match
    Rios Room 15  x -2.0..10.5  z 22.7..34.4  -> WEST wall, covers all of z
    nothing at x > 18.6 or z > 32.1           -> EAST and SOUTH exterior
So the only walls that can carry a window are EAST and SOUTH, and the only wall
that can carry the door is NORTH.

Floor-plan registration ('Second Floor Plan App.png'; the plan is the standard
plan turned 180 deg, so world +x -> image LEFT and world +z -> image UP).  Fit
from the Rios Room rect: img_x = 977.8 - 28.6*wx, img_y = 1372 - 27.4*wz.  The
red overlay lands on the drawn room to within ~0.5 ft (scratchpad reg26.png).
Reading the plan on that transform, in local ft:

    SOUTH wall  PALE-BLUE tick (= window)  x 2.6 .. 5.7
    NORTH wall  wall drawn only for        x 3.3 .. 7.35   -> a 3.3 ft GAP at
                                                              x 0 .. 3.3 = door
    WEST  wall  1.9 x 4.1 block            x 0..1.9, z 4.4..8.5   -> vanity
    SOUTH-EAST  rounded blob               x 4.9..7.35, z 6.3..8.2 -> toilet
    the rest of the EAST side is undrawn   -> the shower alcove

PHOTO CONFIRMATION
------------------
'Second floor bathroom.jpg' is shot standing IN the doorway.  Facing south,
screen-left is EAST (forward (0,0,1) x up (0,1,0) = (-1,0,0) = west, so west is
to the right).  It shows: subway-tiled shower with the black barn rail hard on
the LEFT and very close = EAST, running away from the camera; white vanity on
the RIGHT = WEST; window dead ahead = SOUTH; toilet in front of the window on
its EAST side.  'Second floor bathroom B (2).jpg' from the same spot confirms
the toilet is EAST of the window and puts a framed print on the south wall above
it, seen THROUGH the shower glass -- which is only possible if the shower is
between the north door and the south-east corner, i.e. on the east side.

Mirror test: the round black mirror in 'Second floor bathroom B.jpg' hangs over
the vanity and reflects the shower's black-framed glass, so it cannot be on the
shower's wall -- it is opposite it, on the WEST wall.  That settles the vanity.

CORRECTION to the shell pass: it put the door at local x 4.30..7.00 (the EAST
end of the north wall) and the toilet WEST of the window.  Both are wrong -- the
plan's wall gap is at the WEST end, and standing in an east-end doorway you
would be inside the shower alcove, which no photo shows.

FLOOR: I agree with the shell pass.  Every shot shows the same grey wood-look
plank running unbroken from the hallway threshold under the vanity to the shower
curb; the only tile is the grey hexagon mosaic INSIDE the pan and the white
subway on the shower walls.  floor_texture stays 'wood'.
"""
import json
import math
from bkit import *                                                  # noqa: F403
from bkit import (Model, Material, box, rounded_box, cylinder, quad,
                  sag_plane, torus, Part, bx, rect_down, disc_down, ring_down,
                  ceiling, baseboards, door_unit, window_unit,
                  wall_skin, oval_face, oval_ring, tube, bottle, rug,
                  openings, soft_shadow, tile_face, hex_pan,
                  save_here, surfaces, Rnd, R, mix,
                  TRIM, TRIM_D, CEIL, CEIL_FLAT, CAN_CONE, LENS, VENT,
                  WHITEWD, BLACKMET, CHROME, GLASS, PORC,
                  BB_H, BB_T, CROWN_H, CASE_W)

ROOM, W, D, H = 26, 8.1, 8.7, 8.0

# ------------------------------------------------------------------ layout
DOOR_N = (0.42, 3.22)          # north wall, local x  -> 2F hallway
WIN_S = (2.55, 5.65)           # south wall, local x
SILL, HEAD = 2.95, 6.40

SH = (4.45, 8.02, 0.10, 5.30)  # shower alcove x0,x1,z0,z1
VAN = (0.10, 2.05, 4.15, 8.25)  # vanity x0,x1,z0,z1
TOI_X = 6.45                   # toilet centre x, tank on the south wall

WALLC = "#e9e7e2"

# ----------------------------------------------------------------- palette
WHT = Material("b2wht", "#f2f1ed", roughness=0.58)         # vanity carcass
FR = Material("b2fr", "#edebe6", roughness=0.62)           # door/drawer fronts
TOPQ = Material("b2top", "#f7f6f3", roughness=0.34)        # quartz counter
SANI = Material("b2sani", "#f5f5f4", roughness=0.36)
MIRROR = Material("b2mir", "#eaeef0", roughness=0.86, metallic=0.0)
BLK = BLACKMET
SUBWAY = Material("b2sub", "#fbfaf8", roughness=0.42)
SUBWAY2 = Material("b2sub2", "#f4f3f0", roughness=0.42)
SUBGROUT = Material("b2grt", "#d9d7d3", roughness=0.88)
HEXT = Material("b2hex", "#6f7370", roughness=0.55)        # grey hex mosaic
HEXG = Material("b2hexg", "#54574f", roughness=0.85)
PANW = Material("b2pan", "#e9e8e5", roughness=0.45)
PLANT = Material("b2plant", "#5b7a52", roughness=0.85)
MATW = Material("b2mat", "#ecebe7", roughness=0.99)
MATD = Material("b2matd", "#b9b7b2", roughness=0.99)
SHADEG = Material("b2shade", "#f6f4ee", roughness=0.55, emissive="#8a8880")
ARTF = Material("b2artf", "#f3f2ef", roughness=0.7)
ARTI = Material("b2arti", "#7f8a96", roughness=0.75)
ARTI2 = Material("b2arti2", "#aeb7bf", roughness=0.75)

BOT = [Material("b2b%d" % i, c, roughness=0.45) for i, c in enumerate(
("#f0efeb", "#dee2e5", "#3a3d41", "#cbb5a6", "#aebfcb", "#ddd2ae",
     "#a97b7e", "#7d8a78"))]


# ===================================================================== shell
def build_openings():
    openings(ROOM, [
        # NORTH door to the hallway.  A `passage` would look through my hole at
        # room 17's un-cut wall (ROOM-BRIEF: cut BOTH sides), and room 17 is
        # another agent's, so this stays a painted door panel.
        ("door", 0, DOOR_N[0], DOOR_N[1] - DOOR_N[0], 0.0, 6.85),
        ("window", 2, W - WIN_S[1], WIN_S[1] - WIN_S[0], SILL, HEAD - SILL),
    ])


def build_ceiling():
    m = ceiling(W, D, H, cans=[(2.05, 2.10), (6.10, 6.85)],
                vents=[(1.20, 1.10, 0.95, 0.50)])
    Y = H - 0.01
    # the rounded-square flush LED panel over the middle of the room (photo B2)
    cx, cz, r = 3.05, 4.05, 0.83
    bx(m, CEIL_FLAT, cx - r, cx + r, Y - 0.035, Y, cz - r, cz + r)
    bx(m, LENS, cx - r + 0.08, cx + r - 0.08, Y - 0.135, Y - 0.035,
       cz - r + 0.08, cz + r - 0.08)
    # exhaust grille over the shower
    gx, gz, g = 6.25, 2.35, 0.42
    bx(m, CEIL_FLAT, gx - g, gx + g, Y - 0.030, Y, gz - g, gz + g)
    for i in range(5):
        z = gz - g + 0.09 + i * (2 * g - 0.18) / 4.6
        bx(m, VENT, gx - g + 0.07, gx + g - 0.07, Y - 0.052, Y - 0.036,
           z, z + 0.050)
    return m


def build_trim():
    m = baseboards(W, D, doors=[("n", *DOOR_N), ("e", SH[2], SH[3])])
    # _blit maps a unit through house.js's edge parameter, which runs ASCENDING
    # on n/e and BACKWARDS on s/w -- so mirror the span for s/w units only.
    # CASING ONLY -- no leaf.  Room 17's `Hall2F Doors` models this doorway's
    # leaf with both_faces=True, so its 6-panel elevation serves the room 26 side
    # too.  The leaf that used to be here (world z 23.400-23.545, x 10.92-13.72)
    # sat 0.48 ft out of register with opening 128, so it hid room 17's relief
    # from the hallway and showed doubled panel outlines from inside the bath.
    # Owner approved dropping it, 22 Aug 2026 (scratchpad/hall2/BRIEF.md,
    # "Duplicate neighbour door panels").  Do NOT restore `door_unit` here.
    # `top=DOOR_TOP` keeps the casing head exactly where door_unit put it.
    cased_opening(m, "n", W, D, *DOOR_N, top=DOOR_TOP)
    window_unit(m, "s", W, D, W - WIN_S[1], W - WIN_S[0], sill=SILL, head=HEAD)
    return m


SKIN_LO, SKIN_HI = BB_H - 0.02, H - CROWN_H + 0.04

# The north wall's doorway onto the hallway.  Opening 128 was re-cut by the room
# 17 v2 door pass to register EXACTLY with the hallway's own opening 127 --
# local x 0.90..3.70 (world x 11.40..14.20), 0.48 ft east of where this file's
# DOOR_N puts it.  The skin's hole must follow the OPENING, not DOOR_N: this
# plane sits at world z 23.428, i.e. 0.128 ft into the hallway side of the wall
# face, so any part of it left standing across the opening reads as a slab in
# front of room 17's door leaf.  Owner-approved (22 Aug 2026).  DOOR_N itself is
# deliberately untouched -- it still drives this room's own casing and skirting.
DOOR_N_CUT = (0.90, 3.70)
HOLES = {
    "n": [(DOOR_N_CUT[0] - 0.32, DOOR_N_CUT[1] + 0.32, 0.0, 7.20)],
    "e": [(SH[2] - 0.10, SH[3] + 0.10, 0.0, H)],
    "s": [(WIN_S[0] - 0.30, WIN_S[1] + 0.30, SILL - 0.50, HEAD + 0.32)],
    "w": [],
}


def build_skins(colors):
    m = Model()
    for wall in "nesw":
        wall_skin(m, wall, W, D, colors[wall], SKIN_LO, SKIN_HI, HOLES[wall])
    return m


# ==================================================================== shower
def build_shower():
    """East alcove: white subway on three sides, grey hex pan, black barn-rail
    slider on the WEST face (photos 1 and B2)."""
    m = Model()
    x0, x1, z0, z1 = SH
    # --- grout backing planes, then tile faces standing proud of them
    bx(m, SUBGROUT, x1 - 0.10, x1, 0.0, 7.10, z0, z1)              # east back
    bx(m, SUBGROUT, x0 - 0.10, x1, 0.0, 7.10, z0, z0 + 0.10)       # north end
    bx(m, SUBGROUT, x0 - 0.10, x1, 0.0, 7.10, z1 - 0.10, z1)       # south end
    rn = Rnd(3313)

    def jit(r, a):
        return SUBWAY if (int(a * 7) + r) % 3 else SUBWAY2

    tile_face(m, SUBWAY, "zy", x1 - 0.105, z0 + 0.10, z1 - 0.10, 0.30, 7.05,
              0.68, 0.295, gap=0.022, facing=-1, jitter=jit)
    tile_face(m, SUBWAY, "xy", z0 + 0.105, x0 + 0.05, x1 - 0.10, 0.30, 7.05,
              0.68, 0.295, gap=0.022, facing=1, jitter=jit)
    tile_face(m, SUBWAY, "xy", z1 - 0.105, x0 + 0.05, x1 - 0.10, 0.30, 7.05,
              0.68, 0.295, gap=0.022, facing=-1, jitter=jit)
    # --- pan: white curb + grey hexagon mosaic floor
    bx(m, PANW, x0 - 0.05, x1, 0.0, 0.30, z0, z1)
    hex_pan(m, HEXT, HEXG, x0 + 0.06, x1 - 0.12, z0 + 0.12, z1 - 0.12, 0.30,
            r=0.165)
    m.add(cylinder(0.11, 0.02, 12), CHROME, at=((x0 + x1) / 2, 0.30, 2.90))
    bx(m, PANW, x0 - 0.05, x0 + 0.12, 0.30, 0.44, z0, z1)          # curb
    # --- niche in the east tile (photo B2)
    bx(m, Material("b2nich", "#dcdbd8", roughness=0.5),
       x1 - 0.30, x1 - 0.10, 3.30, 4.60, z0 + 0.85, z0 + 2.15)
    for i in range(3):
        bottle(m, BOT[i + 2], x1 - 0.20, z0 + 1.05 + i * 0.42, 0.085,
               0.40 + 0.09 * i, y=3.34)
    # --- black barn rail, its track wheels, and two glass panels
    bx(m, BLK, x0 - 0.02, x0 + 0.06, 6.20, 6.86, z0, z1)           # head rail
    for zz in (z0 + 0.70, z0 + 1.20, z0 + 3.20, z0 + 3.70):
        m.add(cylinder(0.15, 0.055, 12), BLK, at=(x0 - 0.06, 6.68, zz),
              rot_z=R(90))
    zm = (z0 + z1) / 2
    bx(m, GLASS, x0 + 0.055, x0 + 0.095, 0.44, 6.60, z0 + 0.04, zm + 0.06)
    bx(m, GLASS, x0 + 0.010, x0 + 0.050, 0.44, 6.60, zm - 0.06, z1 - 0.04)
    for (a, b, xa, xb) in ((z0 + 0.02, z0 + 0.10, x0 + 0.03, x0 + 0.12),
                           (zm + 0.02, zm + 0.10, x0 + 0.03, x0 + 0.12),
                           (zm - 0.10, zm - 0.02, x0 - 0.02, x0 + 0.07),
                           (z1 - 0.10, z1 - 0.02, x0 - 0.02, x0 + 0.07)):
        bx(m, BLK, xa, xb, 0.44, 6.60, a, b)
    bx(m, BLK, x0 - 0.02, x0 + 0.12, 0.44, 0.53, z0, z1)           # bottom rail
    bx(m, BLK, x0 - 0.16, x0 - 0.06, 2.55, 4.35, zm - 0.42, zm - 0.32)  # handle
    for hy in (2.58, 4.28):
        bx(m, BLK, x0 - 0.16, x0 + 0.02, hy, hy + 0.08, zm - 0.44, zm - 0.28)
    # --- black shower column on the east wall: riser, rain arm, handheld
    ex = x1 - 0.14
    bx(m, BLK, ex - 0.10, ex, 2.10, 6.20, 1.05, 1.17)
    m.add(cylinder(0.075, 0.60, 8), BLK, at=(ex - 0.28, 6.18, 1.11),
          rot_z=R(-90))
    m.add(cylinder(0.30, 0.085, 14), BLK, at=(ex - 0.60, 6.14, 1.11))
    m.add(cylinder(0.070, 0.40, 8), BLK, at=(ex - 0.10, 3.40, 1.11),
          rot_z=R(72))
    m.add(cylinder(0.15, 0.10, 12), BLK, at=(ex - 0.06, 2.55, 1.11),
          rot_z=R(-90))
    # corner caddy with bottles
    for sy in (3.00, 4.05):
        bx(m, BLK, ex - 0.62, ex, sy, sy + 0.05, z0 + 0.12, z0 + 0.56)
        rn2 = Rnd(int(sy * 100) + 5)
        for i in range(3):
            bottle(m, BOT[(i + int(sy)) % len(BOT)],
                   ex - 0.48 + i * 0.17, z0 + 0.24 + rn2.f(0, 0.18),
                   0.070, rn2.f(0.26, 0.44), y=sy + 0.05)
    return m


# ==================================================================== vanity
def build_vanity():
    """White raised-panel vanity on the WEST wall, white quartz top, black
    knobs and a black faucet, round black mirror above, plant and clutter on
    the counter (photos B and B2)."""
    m = Model()
    x0, x1, z0, z1 = VAN
    soft_shadow(m, (x0 + x1) / 2 + 0.30, (z0 + z1) / 2, 1.05,
                (z1 - z0) / 2, strength=0.74, spill=0.70, room=(W, D))
    TOE, BODY, TOP = 0.30, 2.86, 2.99
    bx(m, WHT, x0 + 0.09, x1, TOE, BODY, z0 + 0.06, z1 - 0.06)     # carcass
    bx(m, WHT, x0, x1 - 0.14, 0.0, TOE, z0 + 0.14, z1 - 0.14)      # toe kick
    bx(m, TOPQ, x0, x1 + 0.055, BODY, TOP, z0 - 0.045, z1 + 0.045)
    # fronts: two raised-panel doors south, two drawers north (photo B)
    xf = x1 + 0.035
    dz = z1 - 0.10
    for (a, b) in ((z0 + 2.05, z0 + 3.00), (z0 + 3.05, z0 + 4.00)):
        bx(m, FR, x1 - 0.02, xf, TOE + 0.05, BODY - 0.10, a, b)
        bx(m, Material("b2frp", "#f4f3ef", roughness=0.62),
           xf, xf + 0.035, TOE + 0.22, BODY - 0.27, a + 0.16, b - 0.16)
        m.add(cylinder(0.075, 0.10, 10), BLK,
              at=(xf + 0.05, BODY - 0.32, (a + b) / 2), rot_z=R(-90))
    for i in range(2):
        a = z0 + 0.10 + i * 0.94
        bx(m, FR, x1 - 0.02, xf, TOE + 0.05 + 0.0, BODY - 0.10, a, a + 0.86)
        bx(m, Material("b2frp2", "#f4f3ef", roughness=0.62),
           xf, xf + 0.035, TOE + 0.22, BODY - 0.27, a + 0.14, a + 0.72)
        m.add(cylinder(0.075, 0.10, 10), BLK,
              at=(xf + 0.05, BODY - 0.32, a + 0.43), rot_z=R(-90))
    # rectangular undermount basin + black faucet
    cz = (z0 + z1) / 2 + 0.35
    bx(m, Material("b2basin", "#eeedea", roughness=0.30),
       x0 + 0.28, x1 - 0.22, BODY - 0.13, BODY + 0.02, cz - 0.72, cz + 0.72)
    m.add(cylinder(0.070, 0.62, 10), BLK, at=(x0 + 0.34, TOP, cz))
    m.add(cylinder(0.050, 0.40, 8), BLK, at=(x0 + 0.34, TOP + 0.60, cz),
          rot_z=R(-90))
    m.add(cylinder(0.048, 0.14, 8), BLK, at=(x0 + 0.72, TOP + 0.48, cz))
    for hz in (cz - 0.42, cz + 0.42):
        m.add(cylinder(0.045, 0.24, 8), BLK, at=(x0 + 0.34, TOP, hz))
    # round black-framed mirror
    oval_face(m, MIRROR, "zy", cz, 5.05, 1.28, 1.28, x0 + 0.055, 1)
    oval_ring(m, BLK, "zy", cz, 5.05, 1.28, 1.28, 0.075, x0 + 0.02, x0 + 0.09)
    # counter clutter + the trailing plant photo B puts beside the sink
    rn = Rnd(6161)
    for i in range(6):
        u = rn.f(z0 + 0.25, z1 - 0.25)
        if abs(u - cz) < 0.85:
            u += 1.15 if u > cz else -1.15
        u = min(max(u, z0 + 0.18), z1 - 0.18)
        bottle(m, BOT[i % len(BOT)], rn.f(x0 + 0.30, x1 - 0.25), u,
               rn.f(0.050, 0.082), rn.f(0.24, 0.52), y=TOP,
               cap=BOT[(i + 3) % len(BOT)])
    px, pz = x0 + 0.72, z0 + 0.72
    m.add(cylinder(0.24, 0.42, 12, r_top=0.28),
          Material("b2pot", "#efece4", roughness=0.8), at=(px, TOP, pz))
    rn2 = Rnd(77)
    for i in range(11):
        a = 2 * math.pi * i / 11
        m.add(box(0.22, 0.07, 0.22), PLANT,
              at=(px + 0.24 * math.cos(a), TOP + 0.42 + rn2.f(0.0, 0.42),
                  pz + 0.24 * math.sin(a)),
              rot_z=R(rn2.f(-40, 40)), rot_x=R(rn2.f(-40, 40)), rot_y=a)
    # black towel ring at the north end of the vanity wall + grey hand towel
    m.add(torus(0.28, 0.030, 18, 6), BLK, at=(x0 + 0.10, 4.20, z0 - 0.95),
          rot_z=R(90))
    bx(m, BLK, x0 + 0.03, x0 + 0.11, 4.46, 4.62, z0 - 1.00, z0 - 0.90)
    bx(m, Material("b2towg", "#cfd4d2", roughness=0.96),
       x0 + 0.06, x0 + 0.20, 3.25, 4.28, z0 - 1.20, z0 - 0.72)
    # switch plate by the door
    bx(m, Material("b2plate", "#f4f2ee", roughness=0.55),
       x0 + 0.02, x0 + 0.04, 4.05, 4.55, 3.55, 3.95)
    return m


# ==================================================================== toilet
def build_toilet():
    """Elongated toilet, tank on the SOUTH wall east of the window, with the
    paper holder, the floor register and the framed print above it."""
    m = Model()
    tx = TOI_X
    zs = D - 0.06
    soft_shadow(m, tx, zs - 1.05, 0.80, 1.20, strength=0.70, spill=0.62,
                room=(W, D))
    m.add(rounded_box(1.00, 1.08, 1.24, r=0.25, seg=3), SANI,
          at=(tx, 0.0, zs - 1.02))
    m.add(rounded_box(1.24, 0.28, 1.56, r=0.40, seg=4), SANI,
          at=(tx, 1.04, zs - 1.00))
    m.add(rounded_box(1.16, 0.09, 1.46, r=0.38, seg=4),
          Material("b2lid", "#f7f7f6", roughness=0.30),
          at=(tx, 1.30, zs - 1.00))
    bx(m, SANI, tx - 0.74, tx + 0.74, 1.04, 2.34, zs - 0.66, zs - 0.02)
    bx(m, SANI, tx - 0.80, tx + 0.80, 2.34, 2.46, zs - 0.72, zs + 0.0)
    m.add(cylinder(0.05, 0.09, 8), BLK, at=(tx - 0.56, 2.46, zs - 0.34))
    # paper holder on the EAST wall beside it
    bx(m, BLK, W - 0.13, W - 0.05, 2.05, 2.15, zs - 1.00, zs - 0.55)
    m.add(cylinder(0.18, 0.42, 12), Material("b2tp", "#f6f5f2", roughness=0.9),
          at=(W - 0.28, 2.10, zs - 0.78), rot_z=R(90))
    # framed print on the south wall above the toilet (photo B2)
    bx(m, TRIM, tx - 0.72, tx + 0.72, 3.40, 5.15, D - 0.075, D - 0.020)
    bx(m, ARTF, tx - 0.64, tx + 0.64, 3.49, 5.06, D - 0.090, D - 0.075)
    # one soft botanical mass, not confetti: 26 loose 0.09 ft squares read as
    # dead pixels at any distance, an overlapping cluster of larger leaves reads
    # as a picture
    rn = Rnd(919)
    for i in range(15):
        a = 2 * math.pi * i / 15 + rn.f(-0.22, 0.22)
        r = rn.f(0.12, 0.44)
        m.add(box(rn.f(0.20, 0.34), rn.f(0.20, 0.34), 0.010),
              ARTI if i % 2 else ARTI2,
              at=(tx + r * math.cos(a), 4.35 + r * math.sin(a) * 0.95,
                  D - 0.098), rot_z=R(rn.f(0, 180)))
    bx(m, ARTI, tx - 0.028, tx + 0.028, 3.62, 4.35, D - 0.096, D - 0.090)
    # black towel bar on the south wall WEST of the window
    for bxx in (0.55, 2.25):
        bx(m, BLK, bxx - 0.05, bxx + 0.05, 4.62, 4.84, D - 0.26, D - 0.04)
    m.add(cylinder(0.035, 1.70, 8), BLK, at=(0.55, 4.74, D - 0.22),
          rot_z=R(-90))
    # folded, not a slab: a flat rectangle of towel reads as a mis-mapped panel
    T1 = Material("b2towb", "#e7e6e2", roughness=0.96)
    T2 = Material("b2towb2", "#cbc9c4", roughness=0.96)
    for i in range(6):
        fa = 0.74 + i * (1.32 / 6)
        bx(m, T1 if i % 2 == 0 else T2,
           fa + 0.010, fa + (1.32 / 6) - 0.010, 3.05, 4.82,
           D - (0.30 if i % 2 == 0 else 0.245), D - 0.16)
    bx(m, T1, 0.72, 2.08, 4.66, 4.86, D - 0.34, D - 0.14)
    # floor register between the mat and the toilet
    RG = Material("b2reg", "#dcdcd9", roughness=0.55)
    bx(m, RG, 4.85, 5.75, 0.0, 0.022, D - 0.72, D - 0.16)
    for i in range(5):
        bx(m, VENT, 4.92 + i * 0.165, 5.02 + i * 0.165, 0.0, 0.030,
           D - 0.66, D - 0.22)
    return m


# ====================================================================== mats
def build_mats():
    """One patterned grey/white bath mat under the window (photos 1, B, B2)."""
    m = Model()
    x0, x1, z0, z1 = 2.25, 4.75, 6.55, 8.30
    soft_shadow(m, (x0 + x1) / 2, (z0 + z1) / 2, (x1 - x0) / 2, (z1 - z0) / 2,
                strength=0.55, spill=0.72, n=3.6, steps=8)
    # Flat woven mat.  A sagged pile plane plus flat banding boxes tears itself
    # apart (the bands poke through the crown of the sag and sink under it at
    # the edges), so the pile is a slab and the weave is its top face.
    y0 = 0.054
    BANDM = Material("b2matb", "#cdcbc6", roughness=0.99)
    bx(m, MATD, x0, x1, y0, y0 + 0.048, z0, z1)
    n = 13
    for i in range(n):
        a = z0 + 0.06 + i * (z1 - z0 - 0.12) / n
        b = a + (z1 - z0 - 0.12) / n
        bx(m, MATW if i % 2 == 0 else BANDM, x0 + 0.06, x1 - 0.06,
           y0 + 0.048, y0 + 0.070, a, b)
    return m


# ====================================================================== main
def main(skins=None):
    print("room 26 bath (2F) -- furnishing pass")
    surfaces(ROOM, wall_color=WALLC, floor_color="#6b6967", floor_texture="wood")
    build_openings()
    out = []
    out.append(save_here("Bath2F Ceiling", build_ceiling(), ROOM))
    out.append(save_here("Bath2F Baseboards", build_trim(), ROOM))
    if skins:
        out.append(save_here("Bath2F Wall Wash", build_skins(skins), ROOM))
    out.append(save_here("Bath2F Shower", build_shower(), ROOM))
    out.append(save_here("Bath2F Vanity", build_vanity(), ROOM))
    out.append(save_here("Bath2F Toilet", build_toilet(), ROOM))
    out.append(save_here("Bath2F Floor Mat", build_mats(), ROOM))
    print("  total %.2f MB" % (sum(p["kb"] for p in out) / 1024.0))
    return out


if __name__ == "__main__":
    import os
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skins26.json")
    main(json.load(open(p)) if os.path.exists(p) else None)
