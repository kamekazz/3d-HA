"""Room 23 -- Bathroom, first floor (9.9 x 7.4 x 8.0).  FURNISHING PASS.

ORIENTATION (derived before anything was modelled)
--------------------------------------------------
World rect x 18.7..28.6, z -4.3..3.1.  Local x 0 = WEST, 9.9 = EAST;
local z 0 = NORTH, 7.4 = SOUTH (house.js: north = -Z).

Adjacency (GET /api/house):
    Living Room 5   x -1.9..18.6  z -12.4.. 4.6  -> WEST wall (party wall)
    Office 8        x 28.8..39.4  z  -4.5.. 7.1  -> EAST wall (party wall)
    nothing at z < -4.3                          -> NORTH exterior
    nothing at 3.1 < z < 7.3                     -> SOUTH is the untraced
                                                    circulation strip between
                                                    this room and the pantry
So the door can only be on the SOUTH wall, and there is nowhere sensible for a
window -- which is exactly what the photos show: this bathroom has none.

Floor-plan registration ('Main Floor Plan App.png'; the plan is turned 180 deg,
so world +x -> image LEFT and world +z -> image UP).  Fit from the garage,
living room, kitchen and dining rects: img_x = 900.6 - 21.73*wx,
img_y = 1340.6 - 22.91*wz.  The overlay lands on the drawn "Bathroom." room
(scratchpad reg23.png).  Reading the plan's own wall faces, in local ft:

    SOUTH wall  a clean 2.9 ft GAP        x 1.27 .. 4.20   -> the door
    NORTH wall  2.8 x 1.4 block + basin    x 0.1 .. 2.9    -> vanity
    NORTH wall  rounded blob               x 3.6 .. 5.1    -> toilet
    SOUTH-EAST  1.5 ft deep box            x 6.3 .. 9.9    -> shower alcove

PHOTO CONFIRMATION
------------------
'Bathroom.jpg' (primary) is shot standing IN the doorway with a jamb at each
edge of the frame.  Facing north, screen-left is WEST.  The vanity's counter
edge runs nearly HORIZONTALLY across the frame and its doors face the camera,
so the vanity is on the wall opposite the camera = NORTH, not on a side wall;
the toilet is immediately to its right = further EAST on the same wall; and the
tiled shower fills the right-hand third = EAST.  'Bathroom A.jpg' is the reverse
shot: the vanity is now in the right foreground and the open door dead ahead,
which is only consistent with the door on the SOUTH wall at its west end.

Mirror test: the round black mirror hangs over the vanity and reflects the open
door leaf and the doorway beyond it, so it faces the door -- the vanity wall and
the door wall are opposite each other, i.e. north and south.

CORRECTION to the shell pass: it recorded "door on the west wall".  The west
wall is the party wall with the Living Room, and the plan's only wall gap is on
the south.

FLOOR: I agree with the shell pass.  Both photos show the same grey wood-look
plank as the rest of the house running right up to the shower curb, with the
mats lying on it; the only tile is inside the shower.  floor_texture stays
'wood'.
"""
import json
import math
from bkit import *                                                  # noqa: F403
from bkit import (Model, Material, box, rounded_box, cylinder, quad,
                  sag_plane, torus, Part, bx, rect_down, disc_down, ring_down,
                  ceiling, baseboards, door_unit, wall_skin, oval_face,
                  oval_ring, bottle, openings, soft_shadow, tile_face,
                  save_here, surfaces, Rnd, R, mix, SHADOW_Y,
                  TRIM, TRIM_D, CEIL, CEIL_FLAT, CAN_CONE, LENS, VENT,
                  WHITEWD, BLACKMET, CHROME, GLASS, PORC,
                  BB_H, BB_T, CROWN_H, CASE_W)

ROOM, W, D, H = 23, 9.9, 7.4, 8.0

# ------------------------------------------------------------------ layout
DOOR_S = (1.30, 4.15)              # south wall, local x
VAN = (0.28, 3.42, 0.06, 1.96)     # vanity  x0,x1,z0,z1  (north wall)
TOI_X = 4.60                       # toilet centre x, tank on the north wall
SH = (6.15, 9.84, 2.05, 7.34)      # shower alcove x0,x1,z0,z1

WALLC = "#eeece8"

# ----------------------------------------------------------------- palette
GREYCB = Material("b1grey", "#b0b2b0", roughness=0.62)     # grey shaker base
GREYFR = Material("b1greyf", "#a9aba9", roughness=0.64)
TOPQ = Material("b1top", "#f8f7f5", roughness=0.34)
SANI = Material("b1sani", "#f5f5f4", roughness=0.36)
MIRROR = Material("b1mir", "#eaeef0", roughness=0.86, metallic=0.0)
BLK = BLACKMET
TILE = Material("b1tile", "#fbfaf8", roughness=0.40)
TILE2 = Material("b1tile2", "#f3f2ef", roughness=0.40)
TGROUT = Material("b1grt", "#a9a7a4", roughness=0.88)
PANF = Material("b1pan", "#4c4e4d", roughness=0.55)
PANW = Material("b1panw", "#eceae7", roughness=0.45)
PLANT = Material("b1plant", "#5b7a52", roughness=0.85)
MATW = Material("b1mat", "#eceae6", roughness=0.99)
MATD = Material("b1matd", "#8f8d89", roughness=0.99)
SHADEG = Material("b1shade", "#f7f5ef", roughness=0.55, emissive="#8a8880")

BOT = [Material("b1b%d" % i, c, roughness=0.45) for i, c in enumerate(
    ("#f0efeb", "#cfd8de", "#2c2f33", "#c9a58c", "#89b5d8", "#e2c96f",
     "#b9535b", "#5d6f5a"))]


# ===================================================================== shell
def build_openings():
    openings(ROOM, [
        # edge 2 = SOUTH, offset measured from x = W descending
        ("door", 2, W - DOOR_S[1], DOOR_S[1] - DOOR_S[0], 0.0, 6.85),
    ])


def build_ceiling():
    m = ceiling(W, D, H, cans=[(7.95, 3.35), (2.20, 4.40)],
                vents=[(5.90, 0.95, 0.95, 0.50)])
    Y = H - 0.01
    # rectangular flush fixture over the middle of the room (photo, top left)
    cx, cz, rx, rz = 3.05, 2.60, 1.05, 0.55
    bx(m, CEIL_FLAT, cx - rx, cx + rx, Y - 0.035, Y, cz - rz, cz + rz)
    bx(m, LENS, cx - rx + 0.08, cx + rx - 0.08, Y - 0.130, Y - 0.035,
       cz - rz + 0.08, cz + rz - 0.08)
    return m


def build_trim():
    m = baseboards(W, D, doors=[("s", *DOOR_S), ("e", SH[2], SH[3]),
                                ("s", SH[0], SH[1])])
    # _blit runs BACKWARDS on the s and w walls (house.js edge parameter), so
    # a unit on the south wall takes a mirrored span; wall_band above does not.
    door_unit(m, "s", W, D, W - DOOR_S[1], W - DOOR_S[0])
    return m


SKIN_LO, SKIN_HI = BB_H - 0.02, H - CROWN_H + 0.04
HOLES = {
    "n": [],
    "e": [(SH[2] - 0.10, SH[3] + 0.10, 0.0, H)],
    "s": [(DOOR_S[0] - 0.32, DOOR_S[1] + 0.32, 0.0, 7.20),
          (SH[0] - 0.10, SH[1] + 0.10, 0.0, H)],
    "w": [],
}


def build_skins(colors):
    m = Model()
    for wall in "nesw":
        wall_skin(m, wall, W, D, colors[wall], SKIN_LO, SKIN_HI, HOLES[wall])
    return m


# ==================================================================== shower
def build_shower():
    """East alcove: white tile on three sides in a running bond with grey
    grout, dark charcoal pan, black-framed slider on the WEST face, black rain
    head and two black corner shelves (photo 'Bathroom.jpg')."""
    m = Model()
    x0, x1, z0, z1 = SH
    bx(m, TGROUT, x1 - 0.10, x1, 0.0, 7.30, z0, z1)               # east back
    bx(m, TGROUT, x0 - 0.10, x1, 0.0, 7.30, z0, z0 + 0.10)        # north end
    bx(m, TGROUT, x0 - 0.10, x1, 0.0, 7.30, z1 - 0.10, z1)        # south end
    rn = Rnd(4242)

    def jit(r, a):
        return TILE if (int(a * 6) + r) % 3 else TILE2

    tile_face(m, TILE, "zy", x1 - 0.105, z0 + 0.10, z1 - 0.10, 0.34, 7.26,
              0.72, 0.335, gap=0.030, facing=-1, jitter=jit)
    tile_face(m, TILE, "xy", z0 + 0.105, x0 + 0.02, x1 - 0.10, 0.34, 7.26,
              0.72, 0.335, gap=0.030, facing=1, jitter=jit)
    tile_face(m, TILE, "xy", z1 - 0.105, x0 + 0.02, x1 - 0.10, 0.34, 7.26,
              0.72, 0.335, gap=0.030, facing=-1, jitter=jit)
    # pan + curb
    bx(m, PANW, x0 - 0.06, x1, 0.0, 0.34, z0, z1)
    rect_down(m, PANF, x0 + 0.08, x1 - 0.11, 0.345, z0 + 0.11, z1 - 0.11)
    m.add(cylinder(0.13, 0.02, 12), CHROME, at=((x0 + x1) / 2, 0.345,
                                                (z0 + z1) / 2 + 0.5))
    bx(m, PANW, x0 - 0.06, x0 + 0.14, 0.34, 0.50, z0, z1)          # curb
    # black-framed slider on the west face: two panels + head/foot rails
    zm = (z0 + z1) / 2
    bx(m, BLK, x0 - 0.02, x0 + 0.14, 6.62, 6.78, z0, z1)
    bx(m, BLK, x0 - 0.02, x0 + 0.14, 0.50, 0.62, z0, z1)
    bx(m, GLASS, x0 + 0.055, x0 + 0.095, 0.62, 6.62, z0 + 0.04, zm + 0.08)
    bx(m, GLASS, x0 + 0.010, x0 + 0.050, 0.62, 6.62, zm - 0.08, z1 - 0.04)
    for (a, b, xa, xb) in ((z0 + 0.02, z0 + 0.11, x0 + 0.03, x0 + 0.12),
                           (zm + 0.02, zm + 0.11, x0 + 0.03, x0 + 0.12),
                           (zm - 0.11, zm - 0.02, x0 - 0.02, x0 + 0.07),
                           (z1 - 0.11, z1 - 0.02, x0 - 0.02, x0 + 0.07)):
        bx(m, BLK, xa, xb, 0.62, 6.62, a, b)
    bx(m, BLK, x0 - 0.14, x0 - 0.05, 2.60, 4.45, zm - 0.50, zm - 0.40)  # handle
    for hy in (2.62, 4.36):
        bx(m, BLK, x0 - 0.14, x0 + 0.02, hy, hy + 0.09, zm - 0.52, zm - 0.36)
    # black rain head on a swan arm off the EAST wall, plus a valve
    ex = x1 - 0.14
    m.add(cylinder(0.13, 0.09, 12), BLK, at=(ex, 6.35, z0 + 1.25), rot_z=R(-90))
    m.add(cylinder(0.075, 0.95, 8), BLK, at=(ex - 0.05, 6.32, z0 + 1.25),
          rot_z=R(-72))
    m.add(cylinder(0.36, 0.10, 16), BLK, at=(ex - 0.92, 6.02, z0 + 1.25))
    m.add(cylinder(0.16, 0.11, 12), BLK, at=(ex - 0.02, 3.35, z0 + 1.25),
          rot_z=R(-90))
    # two black corner shelves with bottles (photo shows them mid-height)
    for sy in (3.35, 4.35):
        bx(m, BLK, ex - 1.05, ex, sy, sy + 0.05, z0 + 0.11, z0 + 0.62)
        rn2 = Rnd(int(sy * 100))
        for i in range(3):
            bottle(m, BOT[(i + int(sy)) % len(BOT)],
                   ex - 0.88 + i * 0.24, z0 + 0.24 + rn2.f(0, 0.20),
                   0.075, rn2.f(0.28, 0.46), y=sy + 0.05)
    return m


# ==================================================================== vanity
def build_vanity():
    """Grey shaker vanity on the NORTH wall with a white top, black bar pulls
    and faucet, a round black mirror and the black three-light bar over it."""
    m = Model()
    x0, x1, z0, z1 = VAN
    soft_shadow(m, (x0 + x1) / 2, z0 + 1.05, (x1 - x0) / 2, 1.05,
                strength=0.74, spill=0.70, room=(W, D))
    TOE, BODY, TOP = 0.32, 2.88, 3.01
    bx(m, GREYCB, x0, x1, TOE, BODY, z0, z1 - 0.06)
    bx(m, GREYCB, x0 + 0.10, x1 - 0.10, 0.0, TOE, z0, z1 - 0.20)
    bx(m, TOPQ, x0 - 0.045, x1 + 0.045, BODY, TOP, z0, z1 + 0.05)
    # two shaker doors + one drawer bank
    zf = z1 - 0.10
    mid = (x0 + x1) / 2
    for (a, b) in ((x0 + 0.07, mid - 0.03), (mid + 0.03, x1 - 0.07)):
        bx(m, GREYFR, a, b, TOE + 0.06, BODY - 0.60, zf, z1 - 0.02)
        bx(m, GREYCB, a + 0.13, b - 0.13, TOE + 0.19, BODY - 0.73,
           z1 - 0.02, z1 + 0.012)
        hx = b - 0.20 if a < mid else a + 0.10
        bx(m, BLK, hx, hx + 0.10, TOE + 0.32, BODY - 0.86, z1, z1 + 0.055)
        bx(m, BLK, hx + 0.02, hx + 0.08, TOE + 0.30, TOE + 0.36,
           z1 + 0.03, z1 + 0.075)
    bx(m, GREYFR, x0 + 0.07, x1 - 0.07, BODY - 0.54, BODY - 0.08, zf,
       z1 - 0.02)
    bx(m, BLK, mid - 0.42, mid + 0.42, BODY - 0.35, BODY - 0.27, z1, z1 + 0.055)
    # rectangular vessel-ish basin + black faucet
    bx(m, Material("b1basin", "#f0efec", roughness=0.30),
       mid - 0.85, mid + 0.85, BODY - 0.13, BODY + 0.03, z0 + 0.30, z1 - 0.22)
    fz = z0 + 0.18
    m.add(cylinder(0.070, 0.66, 10), BLK, at=(mid, TOP, fz))
    m.add(cylinder(0.050, 0.42, 8), BLK, at=(mid, TOP + 0.64, fz), rot_x=R(90))
    m.add(cylinder(0.048, 0.15, 8), BLK, at=(mid, TOP + 0.50, fz + 0.40))
    for hx in (mid - 0.46, mid + 0.46):
        m.add(cylinder(0.045, 0.24, 8), BLK, at=(hx, TOP, fz))
    # round black mirror on the north wall
    oval_face(m, MIRROR, "xy", mid, 5.05, 1.22, 1.22, 0.055, 1)
    oval_ring(m, BLK, "xy", mid, 5.05, 1.22, 1.22, 0.070, 0.020, 0.090)
    # black three-light bar above it
    bx(m, BLK, mid - 1.10, mid + 1.10, 6.52, 6.60, 0.02, 0.11)
    for i in (-1, 0, 1):
        lx = mid + i * 0.82
        bx(m, BLK, lx - 0.045, lx + 0.045, 6.32, 6.52, 0.05, 0.14)
        for (a0, a1) in ((lx - 0.24, lx - 0.20), (lx + 0.20, lx + 0.24)):
            bx(m, BLK, a0, a1, 5.86, 6.34, 0.14, 0.18)
            bx(m, BLK, a0, a1, 5.86, 5.92, 0.14, 0.50)
        bx(m, BLK, lx - 0.24, lx + 0.24, 6.30, 6.36, 0.14, 0.50)
        bx(m, BLK, lx - 0.24, lx + 0.24, 5.84, 5.90, 0.14, 0.50)
        m.add(box(0.36, 0.42, 0.30), SHADEG, at=(lx, 5.92, 0.19))
    # counter clutter: pump bottles + a small plant (photo)
    rn = Rnd(2929)
    for i in range(9):
        u = rn.f(x0 + 0.22, x1 - 0.22)
        if abs(u - mid) < 0.95:
            u += 1.15 if u > mid else -1.15
        u = min(max(u, x0 + 0.16), x1 - 0.16)
        bottle(m, BOT[i % len(BOT)], u, rn.f(z0 + 0.20, z0 + 0.50),
               rn.f(0.055, 0.10), rn.f(0.30, 0.66), y=TOP,
               cap=BOT[(i + 2) % len(BOT)])
    px, pz = x1 - 0.42, z0 + 0.52
    m.add(cylinder(0.24, 0.40, 12, r_top=0.28),
          Material("b1pot", "#efece4", roughness=0.8), at=(px, TOP, pz))
    rn2 = Rnd(313)
    for i in range(9):
        a = 2 * math.pi * i / 9
        m.add(box(0.26, 0.09, 0.26), PLANT,
              at=(px + 0.26 * math.cos(a), TOP + 0.40 + rn2.f(0.0, 0.34),
                  pz + 0.26 * math.sin(a)),
              rot_z=R(rn2.f(-40, 40)), rot_x=R(rn2.f(-40, 40)), rot_y=a)
    return m


# ==================================================================== toilet
def build_toilet():
    """Elongated toilet on the NORTH wall east of the vanity, plus the paper
    holder, a small bin and the floor register the photos show."""
    m = Model()
    tx = TOI_X
    zn = 0.06
    soft_shadow(m, tx, zn + 1.05, 0.80, 1.20, strength=0.70, spill=0.62,
                room=(W, D))
    m.add(rounded_box(1.00, 1.10, 1.26, r=0.25, seg=3), SANI,
          at=(tx, 0.0, zn + 1.02))
    m.add(rounded_box(1.24, 0.28, 1.58, r=0.40, seg=4), SANI,
          at=(tx, 1.06, zn + 1.00))
    m.add(rounded_box(1.16, 0.09, 1.48, r=0.38, seg=4),
          Material("b1lid", "#f7f7f6", roughness=0.30),
          at=(tx, 1.32, zn + 1.00))
    bx(m, SANI, tx - 0.74, tx + 0.74, 1.06, 2.36, zn + 0.02, zn + 0.66)
    bx(m, SANI, tx - 0.80, tx + 0.80, 2.36, 2.48, zn - 0.02, zn + 0.72)
    m.add(cylinder(0.05, 0.09, 8), BLK, at=(tx + 0.56, 2.48, zn + 0.34))
    # paper holder on the north wall between the toilet and the shower
    bx(m, BLK, tx + 1.05, tx + 1.55, 2.05, 2.15, 0.05, 0.13)
    m.add(cylinder(0.18, 0.42, 12), Material("b1tp", "#f6f5f2", roughness=0.9),
          at=(tx + 1.30, 2.10, 0.28), rot_z=R(90))
    # small chrome bin beside it
    soft_shadow(m, tx + 1.55, 0.62, 0.40, 0.40, strength=0.60, spill=0.45,
                room=(W, D))
    m.add(cylinder(0.34, 0.92, 12, r_top=0.30),
          Material("b1bin", "#cfd1d2", roughness=0.5, metallic=0.20),
          at=(tx + 1.55, 0.0, 0.62))
    # floor register (photo 'Bathroom.jpg', bottom right, and 'Bathroom A')
    RG = Material("b1reg", "#dcdcd9", roughness=0.55)
    bx(m, RG, 5.15, 6.05, 0.0, 0.022, 5.45, 6.00)
    for i in range(5):
        bx(m, VENT, 5.22 + i * 0.165, 5.32 + i * 0.165, 0.0, 0.030,
           5.50, 5.95)
    return m


# ====================================================================== mats
def build_mats():
    """Two striped grey/white mats: a long runner along the vanity wall and a
    second one in front of the shower (both photos)."""
    m = Model()

    BAND = Material("b1band", "#93918c", roughness=0.99)

    def mat(x0, x1, z0, z1, nband, along_x=True):
        """Flat striped mat.  A sagged pile plane plus flat stripe boxes tears
        itself apart -- the stripes poke through the crown of the sag and sink
        under it at the edges -- so the pile is a slab and the stripes are part
        of its top face, laid edge to edge."""
        soft_shadow(m, (x0 + x1) / 2, (z0 + z1) / 2, (x1 - x0) / 2,
                    (z1 - z0) / 2, strength=0.42, spill=0.40, n=3.6, steps=7)
        y0 = SHADOW_Y + 0.004
        bx(m, MATD, x0, x1, y0, y0 + 0.052, z0, z1)               # rolled edge
        n = nband * 2 + 1
        for i in range(n):
            if along_x:
                a = x0 + 0.06 + i * (x1 - x0 - 0.12) / n
                b = a + (x1 - x0 - 0.12) / n
                bx(m, MATW if i % 2 == 0 else BAND, a, b,
                   y0 + 0.052, y0 + 0.074, z0 + 0.06, z1 - 0.06)
            else:
                a = z0 + 0.06 + i * (z1 - z0 - 0.12) / n
                b = a + (z1 - z0 - 0.12) / n
                bx(m, MATW if i % 2 == 0 else BAND, x0 + 0.06, x1 - 0.06,
                   y0 + 0.052, y0 + 0.074, a, b)

    mat(0.55, 4.55, 2.10, 3.55, 7, along_x=True)      # runner at the vanity
    mat(4.55, 6.05, 2.60, 5.05, 5, along_x=False)     # outside the shower
    return m


# ====================================================================== main
def main(skins=None):
    print("room 23 Bathroom (1F) -- furnishing pass")
    surfaces(ROOM, wall_color=WALLC, floor_color="#7c7a78", floor_texture="wood")
    build_openings()
    out = []
    out.append(save_here("Bath1F Ceiling", build_ceiling(), ROOM))
    out.append(save_here("Bath1F Baseboards", build_trim(), ROOM))
    if skins:
        out.append(save_here("Bath1F Wall Wash", build_skins(skins), ROOM))
    out.append(save_here("Bath1F Shower", build_shower(), ROOM))
    out.append(save_here("Bath1F Vanity", build_vanity(), ROOM))
    out.append(save_here("Bath1F Toilet", build_toilet(), ROOM))
    out.append(save_here("Bath1F Floor Mats", build_mats(), ROOM))
    print("  total %.2f MB" % (sum(p["kb"] for p in out) / 1024.0))
    return out


if __name__ == "__main__":
    import os
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skins23.json")
    main(json.load(open(p)) if os.path.exists(p) else None)
