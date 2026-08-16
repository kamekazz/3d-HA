"""Room 16 -- Master Bath. (level 2, 14.8 x 12.7 x 8.0).  FURNISHING PASS.

ORIENTATION (derived before anything was modelled)
--------------------------------------------------
World rect x 18.6..33.4, z -0.3..12.4.  Local x 0 = WEST, 14.8 = EAST;
local z 0 = NORTH, 12.7 = SOUTH (house.js: north = -Z).

Adjacency from roomkit.rooms --list:
    Master Bed 14   x -1.89..18.62  z -12.38..6.30 (L-shaped; its east wing is
                    x 13.84..18.62, z 0.88..6.30)  -> WEST wall, north half
    Hallway 17      x 10.5..18.6    z  6.6..23.3   -> WEST wall, south half
    Master Closet 27 x 18.6..32.2   z 12.4..20.8   -> SOUTH wall
    nothing at z < -0.3 or x > 33.4                -> NORTH and EAST exterior

Floor-plan registration ('Second Floor Plan App.png'): the plan is the standard
plan rotated 180 deg, so world +x -> image LEFT and world +z -> image UP.  Fitted
from the Rios Room rect (world x -2..10.5, z 22.7..34.4 -> px 678..1035,
430..750): img_x = 977.8 - 28.6*wx, img_y = 1372 - 27.4*wz.  Cross-checked: the
wall between the master-bedroom wing (z<=6.30) and the hallway (z>=6.6) lands
exactly on the plan's wall stub running west off this room at z 6.2-6.5.

Sampling the plan on that transform as an ASCII grid gives, in local ft:
    NORTH wall  window (pale-blue tick)   x 11.0 .. 13.9
    EAST  wall  window (pale-blue tick)   z  0.4 ..  4.1
    WEST  wall  a clean 3.0 ft GAP        z  0.3 ..  3.6   <- door to bedroom
    WEST  wall  solid z 3.6..12.7, with a 1.35 x 2.85 ft blob at z 6.9..9.7
                                                          <- the console, NOT a door
    SOUTH wall  gap                       x  0.5 ..  2.9   <- door to master closet
    partition wall at x 2.9 running z 0..3.3              <- shower's west return
    fixtures: 4.5x1.9 blob x 3.5..8.0 on the south wall   <- double vanity
              1.4x2.2 blob x 12.0..13.4 on the south wall <- toilet
              4.2x5.9 rounded blob x 10.2..14.2, z 0..5.9 <- freestanding tub

PHOTO CONFIRMATION
------------------
'Master Bathroom A.jpg' is shot from the shower door.  The crown molding makes a
clean inside corner at image x~600 with the toilet sitting in it; left of that
corner is one wall (window at the far end, teal towel, small framed art, taupe
towel on a black bar, paper holder), right of it is the vanity wall.  The camera
therefore faces the corner formed by the two walls it is NOT on -- the SE corner
-- so the towel wall is EAST and the vanity wall is SOUTH, and the shower is NW.

Mirror test (a mirror cannot reflect the wall it hangs on): both mirrors hang on
the south wall and so look north.  The WEST sink's mirror reflects a blind-covered
window AND the shower's black-framed glass -- that window is on the NORTH wall,
west-adjacent to nothing but the shower.  The EAST sink's mirror reflects a
different window, shade rolled up, green trees, with the teal towel beside it --
the EAST wall window.  Two windows, on two different walls, exactly as the plan
draws them.  'Master Bath. 2.jpg' shows both at once meeting at an inside corner
with the tub tucked under them: that corner is the NE corner.

FLOOR: I agree with the shell pass.  Every photo shows the same grey wood-look
PLANK running unbroken from the bedroom doorway, under the vanity's open legs,
past the toilet and up to the shower curb; there is no tile field and no
threshold anywhere outside the shower pan.  floor_texture stays 'wood'.
"""
import json
import math
from bkit import *                                                  # noqa: F403
from bkit import (Model, Material, box, rounded_box, cylinder, prism, quad,
                  sag_plane, torus, Part, bx, rect_down, disc_down, ring_down,
                  ceiling, baseboards, door_unit, window_unit, contact_shadow,
                  wall_skin, oval_face, oval_ring, oval_tub, sweep_shell,
                  tube, bottle, rug, openings,
                  save_here, surfaces, Rnd, R, mix,
                  TRIM, TRIM_D, CEIL, CEIL_FLAT, CAN_CONE, LENS, VENT,
                  WHITEWD, BLACKMET, CHROME, GLASS, MARBLE, PORC,
                  BB_H, BB_T, CROWN_H, CASE_W)

ROOM, W, D, H = 16, 14.8, 12.7, 8.0

# ------------------------------------------------------------------ layout
DOOR_BED = (0.55, 3.35)      # west wall, local z  -> master bedroom
DOOR_CL = (0.50, 3.00)       # south wall, local x -> master closet
WIN_N = (11.00, 13.90)       # north wall, local x
WIN_E = (0.75, 3.95)         # east wall, local z
SILL, HEAD = 2.55, 6.35

SH = (2.95, 7.45, 0.05, 4.15)          # shower  x0,x1,z0,z1
TUB_C = (12.35, 3.35)                  # tub centre
VAN = (3.70, 9.70, 10.89, 12.64)       # vanity  x0,x1,z0,z1
TOI_X = 12.55                          # toilet centre x (tank on south wall)
CAB_Z = (6.90, 9.70)                   # west-wall console, local z

# ----------------------------------------------------------------- palette
# authored albedo picked off the photos; the four wall skins are solved from a
# two-point probe in probe16.py, not by eye.
WALLC = "#e4e2dd"
WHT = Material("mbwht", "#f3f2ef", roughness=0.55)          # cabinetry white
TOPQ = Material("mbtop", "#f7f7f5", roughness=0.34)         # quartz counter
SANI = Material("mbsani", "#f5f5f4", roughness=0.36)        # sanitaryware
MIRROR = Material("mbmir", "#eaeef0", roughness=0.86, metallic=0.0)
MARB = Material("mbmarb", "#eeedef", roughness=0.38)
VEIN = Material("mbvein", "#c9c9d1", roughness=0.42)
BLK = BLACKMET
RUGW = "#eeece8"
TOWEL_T = Material("mbtowt", "#c8c0bb", roughness=0.96)     # taupe bath sheet
TOWEL_M = Material("mbtowm", "#cfdee0", roughness=0.96)     # eucalyptus green
TOWEL_G = Material("mbtowg", "#b9bcbd", roughness=0.96)     # grey hand towel
SKY = Material("mbsky", "#cadfe6", roughness=0.75)          # almond-blossom art
BLOSSOM = Material("mbblos", "#f4f1e6", roughness=0.75)
BRANCH = Material("mbbrch", "#9a8f7e", roughness=0.8)
PLANT = Material("mbplant", "#4e6b4a", roughness=0.85)
WOODST = Material("mbwood", "#a98d6f", roughness=0.72)
SILV = Material("mbsilv", "#c9cbcd", roughness=0.45, metallic=0.25)
CLEARG = Material("mbclr", "#f2f4f2", roughness=0.30, opacity=0.35)
SHADEG = Material("mbshade", "#f6f4ee", roughness=0.55, emissive="#8a8880")

BOT = [Material("mbb%d" % i, c, roughness=0.45) for i, c in enumerate(
    ("#f0efeb", "#d8d4cd", "#2c2f33", "#c9a58c", "#8fb0c4", "#e2c96f",
     "#b9535b", "#5d6f5a"))]


# ===================================================================== shell
def build_openings():
    openings(ROOM, [
        ("window", 0, WIN_N[0], WIN_N[1] - WIN_N[0], SILL, HEAD - SILL),
        ("window", 1, WIN_E[0], WIN_E[1] - WIN_E[0], SILL, HEAD - SILL),
        # painted-panel doors: the neighbour rooms belong to other agents and a
        # `passage` here would look through my hole at their un-cut wall
        # (ROOM-BRIEF: an opening on a shared wall must be cut on BOTH sides).
        ("door", 3, D - DOOR_BED[1], DOOR_BED[1] - DOOR_BED[0], 0.0, 6.85),
        ("door", 2, W - DOOR_CL[1], DOOR_CL[1] - DOOR_CL[0], 0.0, 6.85),
    ])


def build_ceiling():
    m = ceiling(W, D, H,
                cans=[(5.20, 2.10), (10.40, 2.00), (2.20, 6.80), (9.00, 6.40),
                      (13.20, 6.40), (6.40, 11.00), (12.20, 10.30)],
                vents=[(1.80, 4.60, 1.05, 0.55), (13.20, 11.40, 1.05, 0.55)])
    Y = H - 0.01
    # the big square flush LED panel photo A and photo 3 both show
    cx, cz, r = 5.60, 5.40, 1.03
    bx(m, CEIL_FLAT, cx - r, cx + r, Y - 0.035, Y, cz - r, cz + r)
    bx(m, LENS, cx - r + 0.09, cx + r - 0.09, Y - 0.115, Y - 0.035,
       cz - r + 0.09, cz + r - 0.09)
    # square exhaust-fan grille
    gx, gz, g = 9.60, 2.20, 0.50
    bx(m, CEIL_FLAT, gx - g, gx + g, Y - 0.030, Y, gz - g, gz + g)
    for i in range(6):
        z = gz - g + 0.10 + i * (2 * g - 0.20) / 5.5
        bx(m, VENT, gx - g + 0.08, gx + g - 0.08, Y - 0.052, Y - 0.036,
           z, z + 0.055)
    return m


def build_trim():
    m = baseboards(W, D, doors=[("w", *DOOR_BED), ("s", *DOOR_CL),
                                ("n", SH[0], SH[1])])
    # kit.wall_band (used by baseboards/wall_skin) walks 's' and 'w' in plain
    # ascending room coordinates, but kit._blit maps a door/window unit through
    # house.js's own edge parameter, which runs BACKWARDS on those two walls
    # (edge 2 from x=W, edge 3 from z=D).  Mirror the span for the unit only.
    door_unit(m, "w", W, D, D - DOOR_BED[1], D - DOOR_BED[0])
    door_unit(m, "s", W, D, W - DOOR_CL[1], W - DOOR_CL[0])
    window_unit(m, "n", W, D, WIN_N[0], WIN_N[1], sill=SILL, head=HEAD)
    window_unit(m, "e", W, D, WIN_E[0], WIN_E[1], sill=SILL, head=HEAD)
    return m


SKIN_LO, SKIN_HI = BB_H - 0.02, H - CROWN_H + 0.04
HOLES = {
    "n": [(WIN_N[0] - 0.30, WIN_N[1] + 0.30, SILL - 0.50, HEAD + 0.32),
          (SH[0] - 0.10, SH[1] + 0.10, 0.0, H)],
    "e": [(WIN_E[0] - 0.30, WIN_E[1] + 0.30, SILL - 0.50, HEAD + 0.32)],
    "s": [(DOOR_CL[0] - 0.32, DOOR_CL[1] + 0.32, 0.0, 7.20)],
    "w": [(DOOR_BED[0] - 0.32, DOOR_BED[1] + 0.32, 0.0, 7.20)],
}


def build_skins(colors):
    m = Model()
    for wall in "nesw":
        wall_skin(m, wall, W, D, colors[wall], SKIN_LO, SKIN_HI, HOLES[wall])
    return m


# ==================================================================== shower
def build_shower():
    """NW corner.  Marble slab surround, white pan, black-framed clear glass.

    Photo 1 sees it from the SE: a painted return wall on its west side (that is
    the plan's partition at local x 2.9), a glass front facing south and a glass
    return facing east.  Photo 2 sees the marble back through the door.
    """
    m = Model()
    x0, x1, z0, z1 = SH
    WALLM = Material("mbshw", WALLC, roughness=0.95)
    # ---- solid west return wall, full height: painted outside, marble inside
    bx(m, WALLM, x0, x0 + 0.20, 0.0, H - 0.02, z0, z1)
    bx(m, MARB, x0 + 0.20, x0 + 0.215, 0.0, 7.10, z0, z1)
    # ---- marble back (north) slab
    bx(m, MARB, x0, x1, 0.0, 7.10, z0, z0 + 0.16)
    # veining: chains of short staggered segments that wander down the slab.
    # Long straight bars read as tape stuck on the wall; hairlines read as
    # scratches through the glass in front of them.
    rn = Rnd(7717)

    def vein_chain(u0, u1, ymax, place):
        u, y, n = rn.f(u0, u1), ymax, 0
        while y > 0.25 and n < 40:
            du, dy = rn.f(-0.17, 0.17), rn.f(0.16, 0.30)
            t = rn.f(0.040, 0.085)
            place(min(max(min(u, u + du), u0), u1),
                  min(max(max(u, u + du) + t, u0 + t), u1), y - dy, y)
            u = min(max(u + du, u0), u1)
            y -= dy * 0.92
            n += 1

    for _ in range(4):
        vein_chain(x0 + 0.30, x1 - 0.30, 7.0,
                   lambda a, b, c, d: bx(m, VEIN, a, b, c, d,
                                         z0 + 0.16, z0 + 0.172))
    for _ in range(3):
        vein_chain(z0 + 0.30, z1 - 0.30, 6.8,
                   lambda a, b, c, d: bx(m, VEIN, x0 + 0.215, x0 + 0.227,
                                         c, d, a, b))
    # ---- pan + curb
    PAN = Material("mbpan", "#f2f2f0", roughness=0.42)
    bx(m, PAN, x0 + 0.215, x1, 0.0, 0.30, z0 + 0.17, z1)
    bx(m, MARB, x0 + 0.215, x1, 0.30, 0.42, z1 - 0.22, z1)          # south curb
    bx(m, MARB, x1 - 0.22, x1, 0.30, 0.42, z0 + 0.17, z1)           # east curb
    m.add(cylinder(0.12, 0.02, 12), CHROME, at=((x0 + x1) / 2, 0.29, (z0 + z1) / 2 + 0.4))
    # ---- glass: south front (fixed panel + door) and east return
    bx(m, GLASS, x0 + 0.22, x1 - 0.05, 0.42, 6.95, z1 - 0.065, z1 - 0.025)
    bx(m, GLASS, x1 - 0.065, x1 - 0.025, 0.42, 6.95, z0 + 0.20, z1 - 0.06)
    # black frame: posts + head rails only -- one box spanning the whole run
    # renders as a solid black slab and reads as a hole (round-2 lesson)
    for a, b in ((x0 + 0.20, x0 + 0.30), (x1 - 0.10, x1 - 0.02)):
        bx(m, BLK, a, b, 0.42, 6.99, z1 - 0.085, z1 - 0.015)
    bx(m, BLK, x0 + 0.20, x1 - 0.02, 6.91, 6.99, z1 - 0.085, z1 - 0.015)
    for a, b in ((z0 + 0.20, z0 + 0.30), (z1 - 0.20, z1 - 0.10)):
        bx(m, BLK, x1 - 0.085, x1 - 0.015, 0.42, 6.99, a, b)
    bx(m, BLK, x1 - 0.085, x1 - 0.015, 6.91, 6.99, z0 + 0.20, z1 - 0.08)
    # door stile + long vertical bar handle (photo 1/2)
    dx = x0 + 2.55
    bx(m, BLK, dx, dx + 0.09, 0.42, 6.99, z1 - 0.085, z1 - 0.015)
    bx(m, BLK, dx + 0.42, dx + 0.52, 2.30, 4.35, z1 - 0.24, z1 - 0.10)
    for hy in (2.34, 4.29):
        bx(m, BLK, dx + 0.40, dx + 0.54, hy, hy + 0.09, z1 - 0.24, z1 - 0.07)
    for hy in (1.10, 3.60, 6.20):                                   # hinges
        bx(m, BLK, dx - 0.06, dx + 0.02, hy, hy + 0.34, z1 - 0.16, z1 - 0.01)
    # ---- fittings on the WEST wall: rain head, riser, handheld, valve
    wx = x0 + 0.23
    bx(m, BLK, wx, wx + 0.12, 1.55, 6.05, z0 + 1.05, z0 + 1.17)      # slide bar
    m.add(cylinder(0.085, 0.60, 8), BLK, at=(wx + 0.30, 6.05, z0 + 1.11),
          rot_z=R(90))
    m.add(cylinder(0.34, 0.09, 14), BLK, at=(wx + 0.62, 6.02, z0 + 1.11))
    m.add(cylinder(0.075, 0.42, 8), BLK, at=(wx + 0.10, 3.35, z0 + 1.11),
          rot_z=R(-72))                                              # handheld
    m.add(cylinder(0.155, 0.10, 12), BLK, at=(wx + 0.06, 3.55, z0 + 1.11),
          rot_z=R(90))
    m.add(cylinder(0.16, 0.11, 12), BLK, at=(wx + 0.06, 3.95, z0 + 1.90),
          rot_z=R(90))                                               # valve trim
    m.add(cylinder(0.10, 0.16, 10), BLK, at=(wx + 0.10, 3.20, z0 + 1.90),
          rot_z=R(90))
    # ---- corner caddies with bottles (photo 1)
    for sy in (3.05, 4.15):
        bx(m, BLK, x0 + 0.22, x0 + 0.95, sy, sy + 0.05, z0 + 0.17, z0 + 0.62)
        rn2 = Rnd(int(sy * 100))
        for i in range(3):
            bottle(m, BOT[(i + int(sy)) % len(BOT)],
                   x0 + 0.36 + i * 0.20, z0 + 0.30 + rn2.f(0, 0.20),
                   0.075, rn2.f(0.28, 0.48), y=sy + 0.05)
    # recessed niche on the back wall
    bx(m, Material("mbnich", "#dedde0", roughness=0.5),
       x0 + 1.95, x0 + 3.35, 3.30, 4.55, z0 + 0.05, z0 + 0.16)
    for i in range(3):
        bottle(m, BOT[i + 2], x0 + 2.20 + i * 0.42, z0 + 0.11, 0.085,
               0.42 + 0.10 * i, y=3.34)
    # grey towel over the glass front (photo 1)
    tz = z1 - 0.10
    bx(m, TOWEL_G, x0 + 3.75, x0 + 4.55, 4.05, 6.05, tz - 0.06, tz + 0.06)
    return m


# ======================================================================= tub
def build_tub():
    """Freestanding oval soaker in the NE corner, long axis N-S, tucked under
    the north window with the east window down its side (photo 2)."""
    m = Model()
    cx, cz = TUB_C
    contact_shadow(m, cx, cz, 1.72, 3.15, y=0.010, strength=0.30, room=(W, D))
    # one continuous flared skin -- stacked slabs terrace into a pancake stack
    oval_tub(m, SANI, Material("mbtubin", "#e9e9e8", roughness=0.36),
             cx, cz, 2.74, 5.64, 2.30, wall=0.19, seg=32)
    m.add(cylinder(0.085, 0.03, 8), BLK, at=(cx, 0.44, cz + 1.45))
    # black floor-mounted filler standing in the NE corner beside the tub
    fx, fz = 14.18, 1.15
    m.add(cylinder(0.135, 0.10, 12), BLK, at=(fx, 0.0, fz))
    m.add(cylinder(0.105, 2.32, 10), BLK, at=(fx, 0.08, fz))
    m.add(cylinder(0.070, 0.80, 8), BLK, at=(fx, 2.28, fz), rot_x=R(72))
    m.add(cylinder(0.075, 0.28, 8), BLK, at=(fx - 0.24, 1.95, fz))
    # a wooden stool with a potted plant south of the filler (photo 1)
    sx, sz = 14.12, 6.35
    contact_shadow(m, sx, sz, 0.62, 0.62, y=0.010, strength=0.20, room=(W, D))
    for (ox, oz) in ((-0.34, -0.30), (0.34, -0.30), (-0.34, 0.30), (0.34, 0.30)):
        m.add(cylinder(0.055, 1.55, 6), WOODST, at=(sx + ox, 0.0, sz + oz))
    m.add(cylinder(0.52, 0.13, 14), WOODST, at=(sx, 1.55, sz))
    m.add(cylinder(0.36, 0.62, 12, r_top=0.44),
          Material("mbpot", "#e6e1d8", roughness=0.8), at=(sx, 1.68, sz))
    rn = Rnd(451)
    for i in range(9):
        a = 2 * math.pi * i / 9
        m.add(box(0.10, 1.05, 0.30), PLANT,
              at=(sx + 0.20 * math.cos(a), 2.24, sz + 0.20 * math.sin(a)),
              rot_z=R(rn.f(-32, 32)), rot_x=R(rn.f(-32, 32)), rot_y=a)
    # small round magnifying mirror standing on the tub deck (photos 1 & 2)
    m.add(cylinder(0.24, 0.03, 12), BLK, at=(cx - 0.55, 2.32, cz - 1.85))
    m.add(cylinder(0.035, 0.62, 6), BLK, at=(cx - 0.55, 2.35, cz - 1.85))
    oval_face(m, MIRROR, "xy", cx - 0.55, 3.28, 0.30, 0.30, cz - 1.90, -1, 16)
    oval_ring(m, BLK, "xy", cx - 0.55, 3.28, 0.30, 0.30, 0.045,
              cz - 1.94, cz - 1.86, 16)
    return m


# ==================================================================== vanity
def build_vanity():
    """72in white shaker double vanity on the SOUTH wall, black bar pulls, quartz
    top, two undermount rectangles, black gooseneck faucets, two black oval
    mirrors, a sconce and a towel ring at each outer end (photo A / photo 3)."""
    m = Model()
    x0, x1, z0, z1 = VAN
    contact_shadow(m, (x0 + x1) / 2, z0 + 0.95, (x1 - x0) * 0.55, 1.55,
                   y=0.010, strength=0.25, room=(W, D))
    TOE, BODY, TOP = 0.42, 2.92, 3.04
    # legs + carcass (the real one stands on short square legs -- photo A)
    for lx in (x0 + 0.08, x1 - 0.20):
        for lz in (z0 + 0.04, z1 - 0.16):
            bx(m, WHT, lx, lx + 0.12, 0.0, TOE, lz, lz + 0.12)
    bx(m, WHT, x0, x1, TOE, BODY, z0, z1)
    bx(m, TOPQ, x0 - 0.045, x1 + 0.045, BODY, TOP, z0 - 0.05, z1)
    # fronts: [wide drawer over 2 doors] [3 drawers] [wide drawer over 2 doors]
    FR = Material("mbfr", "#eeece8", roughness=0.60)
    ctr = (x0 + x1) / 2
    blocks = [(x0 + 0.07, ctr - 0.80), (ctr + 0.80, x1 - 0.07)]
    zf = z0 - 0.035
    for (bx0, bx1) in blocks:
        bx(m, FR, bx0, bx1, BODY - 0.52, BODY - 0.09, zf, z0)       # top drawer
        bx(m, BLK, (bx0 + bx1) / 2 - 0.42, (bx0 + bx1) / 2 + 0.42,
           BODY - 0.34, BODY - 0.26, zf - 0.055, zf)
        mid = (bx0 + bx1) / 2
        for (dx0, dx1) in ((bx0, mid - 0.025), (mid + 0.025, bx1)):
            bx(m, FR, dx0, dx1, TOE + 0.06, BODY - 0.58, zf, z0)
            hx = dx1 - 0.14 if dx0 < mid else dx0 + 0.10
            bx(m, BLK, hx, hx + 0.055, BODY - 1.55, BODY - 0.72,
               zf - 0.055, zf)
    for i in range(3):
        dy0 = TOE + 0.06 + i * 0.79
        bx(m, FR, ctr - 0.76, ctr + 0.76, dy0, dy0 + 0.70, zf, z0)
        bx(m, BLK, ctr - 0.40, ctr + 0.40, dy0 + 0.30, dy0 + 0.38,
           zf - 0.055, zf)
    # basins, faucets, mirrors, sconces, towel rings
    for cx in (x0 + 1.55, x1 - 1.55):
        bx(m, Material("mbbasin", "#efeeec", roughness=0.30),
           cx - 0.82, cx + 0.82, BODY - 0.14, BODY + 0.02, z0 + 0.42, z1 - 0.30)
        fz = z0 + 0.20
        m.add(cylinder(0.075, 0.72, 10), BLK, at=(cx, TOP, fz))
        m.add(cylinder(0.055, 0.42, 8), BLK, at=(cx, TOP + 0.70, fz),
              rot_x=R(-90))
        m.add(cylinder(0.052, 0.16, 8), BLK, at=(cx, TOP + 0.56, fz + 0.40))
        oval_face(m, MIRROR, "xy", cx, 5.52, 1.06, 1.44, z1 - 0.055, -1)
        oval_ring(m, BLK, "xy", cx, 5.52, 1.06, 1.44, 0.075,
                  z1 - 0.085, z1 - 0.020)
    for sx in (x0 - 0.62, x1 + 0.62):                # sconces at the outer ends
        # black round backplate flat on the wall, stem up, clear glass cylinder
        m.add(cylinder(0.165, 0.075, 14), BLK, at=(sx, 5.30, z1 - 0.02),
              rot_x=R(-90))
        bx(m, BLK, sx - 0.040, sx + 0.040, 5.30, 5.92, z1 - 0.115, z1 - 0.055)
        bx(m, BLK, sx - 0.135, sx + 0.135, 5.86, 5.96, z1 - 0.30, z1 - 0.055)
        # opaque frosted shade: a transparent, low-roughness cylinder renders
        # near-black in this renderer and read as a dark stub
        m.add(cylinder(0.135, 0.52, 12), SHADEG, at=(sx, 5.96, z1 - 0.185))
        m.add(cylinder(0.135, 0.035, 12), BLK, at=(sx, 6.48, z1 - 0.185))
    # black towel ring + grey hand towel, below the east sconce
    rx = x0 - 0.62
    m.add(torus(0.30, 0.032, 18, 6), BLK, at=(rx, 4.55, z1 - 0.14), rot_x=R(90))
    bx(m, BLK, rx - 0.035, rx + 0.035, 4.82, 4.98, z1 - 0.14, z1 - 0.03)
    bx(m, TOWEL_G, rx - 0.34, rx + 0.15, 3.52, 4.62, z1 - 0.21, z1 - 0.09)
    # switch + outlet plates
    for (px, py) in ((x1 + 1.35, 4.20), (x0 - 1.20, 4.20)):
        bx(m, Material("mbplate", "#f4f2ee", roughness=0.55),
           px - 0.24, px + 0.24, py, py + 0.44, z1 - 0.035, z1 - 0.015)
    # counter clutter -- the photo's counters are crowded end to end
    rn = Rnd(9091)
    for i in range(22):
        u = rn.f(x0 + 0.30, x1 - 0.30)
        if abs(u - (x0 + 1.55)) < 0.75 or abs(u - (x1 - 1.55)) < 0.75:
            u += 0.95 if u > (x0 + x1) / 2 else -0.95
        u = min(max(u, x0 + 0.18), x1 - 0.18)
        bottle(m, BOT[i % len(BOT)], u, rn.f(z0 + 0.25, z0 + 0.62),
               rn.f(0.055, 0.105), rn.f(0.30, 0.78), y=TOP,
               cap=BOT[(i + 3) % len(BOT)])
    for u in (x0 + 0.55, x1 - 0.50):                 # toothbrush tumblers
        m.add(cylinder(0.13, 0.34, 10), Material("mbcup", "#e9e7e2",
                                                 roughness=0.5), at=(u, TOP, z0 + 0.34))
        for k in range(2):
            m.add(cylinder(0.026, 0.55, 6), BOT[2 + k],
                  at=(u + 0.05 * (k - 0.5), TOP + 0.20, z0 + 0.34))
    return m


# ==================================================================== toilet
def build_toilet():
    """Elongated two-piece in the SE corner, tank on the SOUTH wall, with the
    paper holder, brush + plunger stand and bin photo A shows around it."""
    m = Model()
    tx = TOI_X
    zs = D - 0.06
    contact_shadow(m, tx, zs - 1.15, 0.95, 1.30, y=0.010, strength=0.23,
                   room=(W, D))
    m.add(rounded_box(1.05, 1.14, 1.30, r=0.26, seg=3), SANI,
          at=(tx, 0.0, zs - 1.05))                       # pedestal
    m.add(rounded_box(1.28, 0.30, 1.62, r=0.42, seg=4), SANI,
          at=(tx, 1.10, zs - 1.02))                      # bowl rim
    m.add(rounded_box(1.20, 0.09, 1.52, r=0.40, seg=4),
          Material("mblid", "#f7f7f6", roughness=0.30),
          at=(tx, 1.38, zs - 1.02))                      # seat + lid
    bx(m, SANI, tx - 0.78, tx + 0.78, 1.10, 2.42, zs - 0.68, zs - 0.02)
    bx(m, SANI, tx - 0.84, tx + 0.84, 2.42, 2.54, zs - 0.74, zs + 0.0)
    m.add(cylinder(0.05, 0.10, 8), BLK, at=(tx - 0.60, 2.54, zs - 0.36))
    # paper holder on the EAST wall beside it
    bx(m, BLK, W - 0.14, W - 0.05, 2.05, 2.15, zs - 1.05, zs - 0.55)
    m.add(cylinder(0.19, 0.44, 12), Material("mbtp", "#f6f5f2", roughness=0.9),
          at=(W - 0.30, 2.10, zs - 0.80), rot_z=R(90))
    # brush + plunger stand
    for (ox, col) in ((-1.30, BLK), (-1.05, BLK)):
        m.add(cylinder(0.085, 1.35, 8), col, at=(tx + ox, 0.30, zs - 1.10))
        m.add(cylinder(0.14, 0.32, 10), col, at=(tx + ox, 0.0, zs - 1.10))
    bx(m, BLK, tx - 1.42, tx - 0.92, 0.28, 0.34, zs - 1.28, zs - 0.92)
    # small white bin
    contact_shadow(m, tx - 1.85, zs - 0.60, 0.42, 0.42, y=0.010, strength=0.16)
    m.add(cylinder(0.36, 0.95, 12, r_top=0.32),
          Material("mbbin", "#eeedea", roughness=0.6), at=(tx - 1.85, 0.0, zs - 0.60))
    return m


# =========================================================== west-wall console
def build_console():
    """The white glass-door cabinet on the WEST wall (plan: 1.35 x 2.85 ft blob
    at local z 6.9..9.7) with the almond-blossom canvas over it, the air purifier
    on its little stool, and the counted clutter from photo 1."""
    m = Model()
    z0, z1 = CAB_Z
    x0, x1 = 0.06, 1.41
    cz = (z0 + z1) / 2
    contact_shadow(m, (x0 + x1) / 2, cz, 0.85, 1.62, y=0.010, strength=0.24,
                   room=(W, D))
    for lz in (z0 + 0.05, z1 - 0.17):
        for lx in (x0 + 0.02, x1 - 0.14):
            bx(m, WHT, lx, lx + 0.12, 0.0, 0.32, lz, lz + 0.12)
    bx(m, WHT, x0, x1, 0.32, 2.62, z0, z1)
    bx(m, TOPQ, x0 - 0.03, x1 + 0.05, 2.62, 2.74, z0 - 0.05, z1 + 0.05)
    # two glass doors with a dark interior behind them
    bx(m, Material("mbdark", "#26282b", roughness=0.7),
       x1 - 0.10, x1 - 0.06, 0.44, 2.50, z0 + 0.07, z1 - 0.07)
    for (a, b) in ((z0 + 0.07, cz - 0.03), (cz + 0.03, z1 - 0.07)):
        bx(m, GLASS, x1 - 0.055, x1 - 0.030, 0.44, 2.50, a, b)
        for (fa, fb) in ((a, a + 0.075), (b - 0.075, b)):
            bx(m, WHT, x1 - 0.06, x1 - 0.01, 0.44, 2.50, fa, fb)
        bx(m, WHT, x1 - 0.06, x1 - 0.01, 0.44, 0.51, a, b)
        bx(m, WHT, x1 - 0.06, x1 - 0.01, 2.43, 2.50, a, b)
    for hz in (cz - 0.11, cz + 0.11):
        bx(m, BLK, x1 - 0.10, x1 - 0.055, 1.20, 1.86, hz - 0.025, hz + 0.025)
    bx(m, Material("mbshelf", "#4a4d51", roughness=0.7),
       x1 - 0.16, x1 - 0.06, 1.45, 1.50, z0 + 0.10, z1 - 0.10)
    # clutter on top: a crowd of bottles + a snake plant on a small riser
    rn = Rnd(2233)
    for i in range(19):
        bottle(m, BOT[i % len(BOT)], rn.f(x0 + 0.20, x1 - 0.18),
               rn.f(z0 + 0.20, z1 - 0.85), rn.f(0.05, 0.10),
               rn.f(0.26, 0.72), y=2.74, cap=BOT[(i + 5) % len(BOT)])
    px, pz = (x0 + x1) / 2 - 0.05, z1 - 0.48
    m.add(cylinder(0.30, 0.60, 12, r_top=0.36),
          Material("mbpot2", "#efece4", roughness=0.8), at=(px, 2.74, pz))
    for i in range(8):
        a = 2 * math.pi * i / 8
        m.add(box(0.10, 0.98, 0.26), PLANT,
              at=(px + 0.16 * math.cos(a), 3.30, pz + 0.16 * math.sin(a)),
              rot_z=R(rn.f(-30, 30)), rot_x=R(rn.f(-30, 30)), rot_y=a)
    # almond-blossom canvas above it (photo 1) -- wide landscape, thin frame
    az0, az1 = 6.30, 10.35
    bx(m, TRIM, 0.02, 0.075, 4.28, 6.02, az0, az1)
    bx(m, SKY, 0.075, 0.090, 4.34, 5.96, az0 + 0.05, az1 - 0.05)
    rn2 = Rnd(88)
    for i in range(22):                                     # branches
        by = 4.40 + 1.52 * (i % 7) / 6.0 + rn2.f(-0.09, 0.09)
        bz = rn2.f(az0 + 0.10, az1 - 0.60)
        bx(m, BRANCH, 0.090, 0.097, by, by + 0.026, bz, bz + rn2.f(0.45, 1.35))
        if i % 3 == 0:                                       # a stub going up
            bx(m, BRANCH, 0.090, 0.097, by, by + rn2.f(0.16, 0.34),
               bz + 0.10, bz + 0.126)
    for i in range(70):                                      # blossom
        by = rn2.f(4.40, 5.92)
        bz = rn2.f(az0 + 0.08, az1 - 0.08)
        s = rn2.f(0.038, 0.062)
        bx(m, BLOSSOM, 0.090, 0.101, by, by + s, bz, bz + s)
    # air-purifier tower on its four-leg stool, north of the console (photo 1)
    dx, dz = 0.78, 5.85
    contact_shadow(m, dx, dz, 0.58, 0.58, y=0.010, strength=0.18, room=(W, D))
    for (ox, oz) in ((-0.28, -0.26), (0.28, -0.26), (-0.28, 0.26), (0.28, 0.26)):
        m.add(cylinder(0.045, 0.62, 6), WHT, at=(dx + ox, 0.0, dz + oz))
    m.add(cylinder(0.42, 0.10, 14), WHT, at=(dx, 0.62, dz))
    m.add(cylinder(0.34, 0.72, 14), SILV, at=(dx, 0.72, dz))
    m.add(rounded_box(0.70, 1.55, 0.34, r=0.16, seg=4), SILV, at=(dx, 1.42, dz))
    bx(m, Material("mbduct", "#e9eaeb", roughness=0.4),
       dx - 0.20, dx + 0.20, 1.66, 2.80, dz - 0.06, dz + 0.06)
    # floor register near the doorway (photo 1)
    RG = Material("mbreg", "#dcdcd9", roughness=0.55)
    bx(m, RG, 1.55, 2.45, 0.0, 0.022, 3.55, 4.10)
    for i in range(5):
        bx(m, VENT, 1.62 + i * 0.165, 1.72 + i * 0.165, 0.0, 0.030, 3.60, 4.05)
    return m


# ============================================================ east-wall decor
def build_towels():
    """East wall between the tub and the toilet: robe hook + eucalyptus towel by
    the window, a small framed abstract, and the long black bar with the taupe
    bath sheet (photo A, photo 3)."""
    m = Model()
    xw = W
    # robe hook + folded green towel, just south of the east window
    bx(m, BLK, xw - 0.13, xw - 0.04, 5.05, 5.20, 4.30, 4.44)
    m.add(cylinder(0.045, 0.20, 8), BLK, at=(xw - 0.22, 5.02, 4.37), rot_z=R(90))
    bx(m, TOWEL_M, xw - 0.30, xw - 0.10, 3.35, 5.05, 4.12, 4.62)
    # small framed abstract print
    fz0, fz1 = 4.85, 5.90
    bx(m, TRIM, xw - 0.075, xw - 0.020, 3.05, 4.00, fz0, fz1)
    bx(m, Material("mbart2", "#f2f1ee", roughness=0.7),
       xw - 0.090, xw - 0.075, 3.12, 3.93, fz0 + 0.06, fz1 - 0.06)
    bx(m, Material("mbart2b", "#8d8f90", roughness=0.7),
       xw - 0.098, xw - 0.088, 3.24, 3.60, fz0 + 0.16, fz0 + 0.44)
    bx(m, Material("mbart2b", "#8d8f90", roughness=0.7),
       xw - 0.098, xw - 0.088, 3.42, 3.78, fz0 + 0.52, fz0 + 0.86)
    # the long black towel bar + taupe bath sheet
    b0, b1 = 6.35, 8.75
    for bz in (b0, b1):
        bx(m, BLK, xw - 0.28, xw - 0.04, 4.50, 4.72, bz - 0.05, bz + 0.05)
    m.add(cylinder(0.038, b1 - b0, 8), BLK, at=(xw - 0.24, 4.62, b0),
          rot_x=R(-90))
    bx(m, TOWEL_T, xw - 0.32, xw - 0.14, 2.55, 4.70, b0 + 0.18, b1 - 0.18)
    bx(m, TOWEL_T, xw - 0.35, xw - 0.26, 4.34, 4.72, b0 + 0.18, b1 - 0.18)
    # wall thermostat/return plate the photo shows high on this wall
    bx(m, Material("mbplate2", "#f2f0ec", roughness=0.55),
       xw - 0.045, xw - 0.020, 4.05, 4.55, 9.55, 9.95)
    return m


# ====================================================================== rugs
def build_rugs():
    m = Model()
    rug(m, 4.05, 9.45, 8.85, 10.70, RUGW, shadow=0.32)     # in front of vanity
    rug(m, 10.60, 12.10, 9.25, 10.30, RUGW, shadow=0.24)   # in front of toilet
    rug(m, 9.20, 12.30, 6.85, 8.55, RUGW, shadow=0.28)     # beside the tub
    rug(m, 4.00, 8.05, 4.85, 7.75, RUGW, shadow=0.32)      # outside the shower
    return m


# ====================================================================== main
def main(skins=None):
    print("room 16 Master Bath. -- furnishing pass")
    surfaces(ROOM, wall_color=WALLC, floor_color="#6f6d6b", floor_texture="wood")
    build_openings()
    out = []
    out.append(save_here("Master Bath Ceiling", build_ceiling(), ROOM))
    out.append(save_here("Master Bath Baseboards", build_trim(), ROOM))
    if skins:
        out.append(save_here("Master Bath Wall Wash", build_skins(skins), ROOM))
    out.append(save_here("Master Bath Shower", build_shower(), ROOM))
    out.append(save_here("Master Bath Tub", build_tub(), ROOM))
    out.append(save_here("Master Bath Vanity", build_vanity(), ROOM))
    out.append(save_here("Master Bath Toilet", build_toilet(), ROOM))
    out.append(save_here("Master Bath Cabinet", build_console(), ROOM))
    out.append(save_here("Master Bath Towels", build_towels(), ROOM))
    out.append(save_here("Master Bath Floor Rugs", build_rugs(), ROOM))
    print("  total %.2f MB" % (sum(p["kb"] for p in out) / 1024.0))
    return out


if __name__ == "__main__":
    import os
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skins16.json")
    main(json.load(open(p)) if os.path.exists(p) else None)
