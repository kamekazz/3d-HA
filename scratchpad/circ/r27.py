"""Room 27 -- Master Closet (13.6 x 8.4 x 8.0), level 2.

ORIENTATION, derived before anything was modelled:
  * Room rect world x 18.60..32.20, z 12.40..20.80.  Adjacencies
    (`roomkit.rooms --list`): Master Bath (16) NORTH across z=12.40, Hallway
    (17) WEST across x=18.60, exterior EAST (x=32.20) and SOUTH (z=20.80) --
    south of z=20.80 the second floor stops and the GARAGE (7, 1F only,
    x 18.90..39.30 z 13.00..34.70) continues, so the closet sits at the edge of
    the 2F over the garage roof.
  * wallscan.py on the registered 2F plan: north wall GAP x 19.40..21.40, every
    other wall SOLID for its whole length.  Room 16 has already cut that door on
    its own side at world x 19.10..21.60 (its opening id 123) -- matched
    EXACTLY, and cut as a `passage` here so room 16's own painted leaf fills it
    instead of two coplanar panels z-fighting.
  * WHICH WALL THE CEILING RAKES TO: raycasting the house-shell GLB straight
    down over the closet footprint gives a roof underside that is CONSTANT in x
    (x = 22 / 25 / 28 / 31.5 all identical) and falls in z:
        z=13 -> 21.54,  z=15 -> 20.58,  z=17 -> 19.61,  z=19 -> 18.65,
        z=20.5 -> 17.93   (world ft; slope 0.481 = a 6:12 pitch)
    So the roof falls SOUTH.  The shell pass had put the rake and the black
    accent wall on the EAST wall; that is a 90-degree error and is corrected
    here.  Two independent checks agree: (a) the plan makes z=20.80 the outer
    edge of the 2F with the garage roof beyond, and (b) in both photos the black
    raked wall is a LONG expanse -- the south wall is 13.6 ft, the east only 8.4.
  * Photos: 'Walk in the closet to Master Bedroom.jpg' looks E/SE with the black
    wall on the RIGHT (= south) and the wire shelving on the LEFT (= north);
    'Walking Closet for the Master bedroom.jpg' looks NW at the door with the
    black wall edge-on at the far left and the shelving on the right.  Both put
    the shelving on the HIGH side and the black panel on the RAKED side.

MEASURED vs INFERRED
  measured: room rect, wall heights, the door span (room 16's own cut), the
            rake slope and direction (shell raycast), all wall solidity (plan).
  inferred: the rake's break point (flat to z=2.60) and its low height (4.70 ft
            at the south wall) -- the shell's own numbers put the roof deck
            below this room's slab, so the shell cannot be used for the height,
            only the direction; the low height is read off the photos against
            the 6.5 ft wire rack beside it.
  inferred: the white STEPPED form along the base of the black wall.  It is
            unmistakable in the primary photo (five/six white treads with a
            shoe and folded towels standing on them) but nothing in the layout
            data explains it -- there is no stair within 4 ft of this room.  It
            is built as what it looks like: a white tiered platform/shoe bench
            against the raked wall.  Flagged in the report.
"""

import math
from ckit import *                                             # noqa: F401,F403
from ckit import save_and_place, openings, wall_skin, blit

ROOM, W, D, H = 27, 13.6, 8.4, 8.0

DOOR = (0.50, 3.00)          # north wall, local x  (== room 16 opening id 123)
DOOR_TOP_27 = 6.85

FLAT_Z = 2.60                # ceiling is flat to here, then rakes
LOW_Y = 4.70                 # ceiling height at the south wall
RAKE = (H - 0.01 - LOW_Y) / (D - FLAT_Z)


def ceil_y(z):
    return (H - 0.01) if z <= FLAT_Z else (H - 0.01) - RAKE * (z - FLAT_Z)


# ---------------------------------------------------------------- materials
CARP = [Material("m27c%d" % i, c, roughness=0.99) for i, c in enumerate(
    ("#8b8b88", "#93938f", "#848481", "#8f8f8b"))]
BLK = Material("m27blk", "#1c1d20", roughness=0.94)
BLK2 = Material("m27blk2", "#232427", roughness=0.92)
BLK3 = Material("m27blk3", "#161719", roughness=0.95)
WIRE = Material("m27wire", "#c9ced1", roughness=0.34, metallic=0.55)
WIRE2 = Material("m27wire2", "#aeb3b6", roughness=0.38, metallic=0.55)
LIN = Material("m27lin", "#dedad2", roughness=0.97)          # cream quilt/linen
LIN2 = Material("m27lin2", "#cbc6bd", roughness=0.97)
NAVY = Material("m27navy", "#2d3550", roughness=0.93)
NAVY2 = Material("m27navy2", "#232a41", roughness=0.93)
CHARC = Material("m27char", "#3a3c40", roughness=0.94)
BLKWEAVE = Material("m27weave", "#26262a", roughness=0.96)
TEAL = Material("m27teal", "#4fbcb6", roughness=0.72)
MATG = Material("m27matg", "#8d9195", roughness=0.80)
TOTE = Material("m27tote", "#b9bec2", roughness=0.55, opacity=0.72)
SHOE = Material("m27shoe", "#1a1a1d", roughness=0.55)
GREYT = Material("m27greyt", "#a8a9a6", roughness=0.96)


# ================================================================= 1 ceiling
def piece_ceiling():
    """Flat over the north 2.6 ft, then a raking plane down to the south wall.
    One-sided, wound to face INTO the room (invisible from the plan pose)."""
    m = Model()
    Y = H - 0.01
    m.add(quad((0, Y, 0), (W, Y, 0), (W, Y, FLAT_Z), (0, Y, FLAT_Z)), CEIL)
    m.add(quad((0, Y, FLAT_Z), (W, Y, FLAT_Z), (W, LOW_Y, D), (0, LOW_Y, D)),
          CEIL)
    # cans -- two in the flat, three stepped down the rake (photo 1 shows one
    # right at the top of the black wall, photo 2 two more up the slope)
    for (cx, cz) in ((3.10, 1.35), (10.30, 1.35)):
        ring_down(m, CEIL_FLAT, cx, cz, Y - 0.022, 0.255, 0.345)
        ring_down(m, CAN_CONE, cx, cz, Y - 0.070, 0.215, 0.258)
        disc_down(m, LENS, cx, cz, Y - 0.092, 0.222)
    for (cx, cz) in ((2.20, 4.30), (7.20, 4.30), (11.90, 4.30)):
        y = ceil_y(cz)
        ring_down(m, CEIL_FLAT, cx, cz, y - 0.030, 0.255, 0.345)
        disc_down(m, LENS, cx, cz, y - 0.088, 0.222)
    # the break line where the rake meets the flat ceiling
    bx(m, TRIM_D, 0.0, W, Y - 0.10, Y - 0.008, FLAT_Z - 0.035, FLAT_Z + 0.035)
    return m


# =========================================================== 2 trim + door
def piece_baseboards():
    """Skirting on the three full-height walls, gapped at the door.  The south
    wall carries the black panel and the stepped platform instead."""
    m = baseboards(W, D, doors=[("n", *DOOR)])
    # kit.baseboards runs all four walls; the south run is hidden behind the
    # panel, which is harmless, but the east/west runs must stop where the rake
    # brings the ceiling down -- they do not, the skirting is at floor level.
    sub = Model()
    for a, b in ((DOOR[0] - CASE_W, DOOR[0] + 0.03),
                 (DOOR[1] - 0.03, DOOR[1] + CASE_W)):
        bx(sub, TRIM, a, b, 0.0, DOOR_TOP_27 + CASE_W, 0.0, 0.20)
    bx(sub, TRIM, DOOR[0] - CASE_W, DOOR[1] + CASE_W, DOOR_TOP_27,
       DOOR_TOP_27 + CASE_W, 0.0, 0.20)
    # jamb lining, so the cut reads as a cased opening from inside the closet
    bx(sub, TRIM, DOOR[0] - 0.04, DOOR[0] + 0.03, 0.0, DOOR_TOP_27, -0.18, 0.02)
    bx(sub, TRIM, DOOR[1] - 0.03, DOOR[1] + 0.04, 0.0, DOOR_TOP_27, -0.18, 0.02)
    bx(sub, TRIM, DOOR[0] - 0.04, DOOR[1] + 0.04, DOOR_TOP_27 - 0.07,
       DOOR_TOP_27, -0.18, 0.02)
    blit(m, sub, "n", W, D, 0.0)
    # light switch just inside the door
    bx(m, TRIM, 3.35, 3.72, 3.55, 4.05, 0.022, 0.075)
    return m


# ======================================================= 3 black accent wall
def piece_black_wall():
    """The dark embossed panel on the SOUTH (raked) wall.

    Relief, not a flat slab: horizontal plank-height bands broken into offset
    blocks that stand 0.01-0.035 ft proud of each other, in three near-black
    tones.  That is what gives it fine-scale gradient at dollhouse distance --
    a single quad meters sd 0 and reads as a hole in the room.
    """
    m = Model()
    z1 = D - 0.045
    z0 = D - 0.085
    top = LOW_Y - 0.06
    bot = 0.10
    rn = Rnd(2718)
    rows = 11
    bh = (top - bot) / rows
    for r in range(rows):
        y0 = bot + r * bh
        y1 = y0 + bh - 0.012
        x = -rn.f(0.0, 1.1)
        while x < W:
            wdt = rn.f(0.85, 2.30)
            a, b = max(0.0, x), min(W, x + wdt)
            if b - a > 0.05:
                mat = (BLK, BLK2, BLK3)[int(rn.f(0, 2.99))]
                d = rn.f(0.0, 0.030)
                bx(m, mat, a, b, y0, y1, z0 - d, z1)
            x += wdt + 0.03
    # the panel's own top edge follows the rake -- trim it with a thin shadow
    # line so it does not read as a rectangle stuck on the wall
    bx(m, BLK3, 0.0, W, top, top + 0.03, z0 - 0.005, z1)
    return m


# ================================================== 4 the white stepped bench
def piece_steps():
    """The white tiered platform along the base of the black wall.

    Primary photo: five/six white treads descending west -> east, a shoe and
    folded towels standing on them, carpet running up to the top one.  See the
    module docstring -- this is the one INFERRED structure in the room.
    """
    m = Model()
    n = 6
    x0, x1 = 0.0, 5.65
    y_hi, y_lo = 2.62, 0.46
    dep = 1.12                       # how far it projects from the south wall
    zb = D - 0.10
    contact_shadow(m, (x0 + x1) / 2 + 0.25, zb - dep / 2 - 0.10,
                   (x1 - x0) / 2 + 0.55, dep * 0.75, y=0.050, strength=0.44,
                   room=(W, D))
    sw = (x1 - x0) / n
    for i in range(n):
        a = x0 + i * sw
        b = a + sw
        y = y_hi - (y_hi - y_lo) * i / (n - 1)
        d = dep - 0.10 * i
        bx(m, TRIM, a, b, 0.0, y, zb - d, zb)             # riser block
        bx(m, TRIM_D, a, b, y - 0.055, y, zb - d - 0.055, zb)   # nosing
        if i:                                             # vertical riser face
            yp = y_hi - (y_hi - y_lo) * (i - 1) / (n - 1)
            bx(m, TRIM, a - 0.045, a, y, yp, zb - d - 0.045, zb)
    # the low plinth that carries on east of the last tread
    bx(m, TRIM, x1, W, 0.0, y_lo, zb - 0.52, zb)
    bx(m, TRIM_D, x1, W, y_lo - 0.05, y_lo, zb - 0.575, zb)
    # things standing on the treads (photo): folded towels, a shoe, a basket
    for (a, wdt, i, mat, hh) in ((0.55, 1.15, 0, LIN, 0.42),
                                 (2.05, 0.95, 1, LIN2, 0.30),
                                 (3.05, 0.80, 2, GREYT, 0.36),
                                 (4.20, 0.75, 4, LIN, 0.26)):
        y = y_hi - (y_hi - y_lo) * i / (n - 1)
        d = dep - 0.10 * i
        bx(m, mat, a, a + wdt, y, y + hh, zb - d + 0.10, zb - 0.14)
    for sx in (3.95, 4.35):
        m.add(rounded_box(0.34, 0.16, 0.82, 0.07, 3), SHOE,
              at=(sx, y_hi - (y_hi - y_lo) * 3 / (n - 1), zb - dep + 0.62))
    return m


# ====================================================== 5 chrome wire racks
def rack(m, x0, x1, z0, z1, levels, top, shadow=True):
    if shadow:
        contact_shadow(m, (x0 + x1) / 2, (z0 + z1) / 2, (x1 - x0) * 0.56,
                       (z1 - z0) * 1.05, y=0.050, strength=0.46, room=(W, D))
    for px in (x0 + 0.09, x1 - 0.09):
        for pz in (z0 + 0.07, z1 - 0.07):
            m.add(cylinder(0.052, top, 8), WIRE, at=(px, 0.0, pz))
    for i in range(levels):
        y = 0.52 + i * (top - 0.72) / max(1, levels - 1)
        for k in range(8):
            z = z0 + 0.06 + k * (z1 - z0 - 0.12) / 7
            bx(m, WIRE2, x0, x1, y, y + 0.030, z, z + 0.040)
        bx(m, WIRE, x0, x1, y, y + 0.050, z0, z0 + 0.045)
        bx(m, WIRE, x0, x1, y, y + 0.050, z1 - 0.045, z1)
    return [0.52 + i * (top - 0.72) / max(1, levels - 1) for i in range(levels)]


def piece_shelving():
    """Two chrome wire racks down the NORTH (high) wall, loaded with folded
    linen, a clear tote and stacked dark clothes -- photo 2's right-hand side."""
    m = Model()
    ys = rack(m, 4.55, 8.85, 0.16, 1.92, 4, 6.55)
    rack(m, 9.15, 13.35, 0.16, 1.92, 4, 6.55)
    rn = Rnd(4242)
    # loads: quilts sagging over the rail, folded stacks, a clear tote
    for i in range(22):
        x = rn.f(4.70, 13.15)
        y = ys[int(rn.f(0, 3.99))]
        mat = (LIN, LIN2, NAVY, CHARC, LIN)[int(rn.f(0, 4.99))]
        hgt = rn.f(0.28, 0.62)
        wdt = rn.f(0.70, 1.55)
        bx(m, mat, x, min(13.30, x + wdt), y + 0.05, y + 0.05 + hgt,
           0.30, 1.80)
    # the clear tote on the second shelf (photo 2)
    bx(m, TOTE, 10.15, 12.55, ys[1] + 0.05, ys[1] + 0.80, 0.32, 1.80)
    bx(m, MATG, 10.25, 12.45, ys[1] + 0.12, ys[1] + 0.62, 0.40, 1.72)
    # a cream quilt spilling over the front edge of the top-but-one shelf
    m.add(sag_plane(2.10, 1.30, 0.30, 6, 5, y=ys[2] + 0.42, edge_drop=0.55),
          LIN, at=(6.60, 0.0, 0.95))
    return m


# ============================================== 6 hanging rail (west end)
def piece_hanging():
    """The white wire rail run at the WEST end of the north wall -- photo 1's
    far-left rack with blankets piled on it."""
    m = Model()
    x0, x1 = 0.35, 4.20
    z0, z1 = 0.16, 1.92
    ys = rack(m, x0, x1, z0, z1, 3, 6.30)
    rn = Rnd(881)
    for i in range(9):
        x = rn.f(0.50, 3.85)
        y = ys[int(rn.f(0, 2.99))]
        bx(m, (LIN if i % 2 else LIN2), x, min(4.15, x + rn.f(0.8, 1.5)),
           y + 0.05, y + 0.05 + rn.f(0.30, 0.70), 0.30, 1.82)
    # big cream duvet slumped over the top shelf, exactly as photo 1 shows
    m.add(sag_plane(2.60, 1.70, 0.38, 7, 5, y=ys[2] + 0.55, edge_drop=0.80),
          LIN, at=(2.10, 0.0, 1.00))
    m.add(sag_plane(1.70, 1.30, 0.30, 6, 5, y=ys[1] + 0.45, edge_drop=0.60),
          LIN2, at=(1.35, 0.0, 1.02))
    # hanging rail under the middle shelf with a few garments
    bx(m, WIRE, x0 + 0.15, x1 - 0.15, ys[1] - 0.07, ys[1] - 0.03, 0.95, 1.00)
    for i in range(7):
        x = x0 + 0.35 + i * 0.48
        mat = (NAVY, CHARC, LIN2, NAVY2)[i % 4]
        bx(m, mat, x, x + 0.32, ys[1] - rn.f(1.55, 2.45), ys[1] - 0.05,
           0.78, 1.20)
    return m


# ================================================== 7 the floor, as photographed
def bag(m, mat, cx, cz, rx, rz, h, seed):
    """A slumped soft bag -- a squashed sphere-ish blob from stacked rings."""
    rn = Rnd(seed)
    lay = 5
    prev = None
    verts, tris = [], []
    for i in range(lay + 1):
        t = i / lay
        y = h * t
        s = math.sin(math.acos(min(1.0, t * 0.95))) * (1.0 - 0.10 * t)
        ring = []
        for k in range(10):
            a = 2 * math.pi * k / 10
            ring.append(len(verts))
            verts.append((cx + rx * s * math.cos(a) * rn.f(0.88, 1.12), y,
                          cz + rz * s * math.sin(a) * rn.f(0.88, 1.12)))
        if prev:
            for k in range(10):
                k2 = (k + 1) % 10
                tris += [(prev[k], prev[k2], ring[k2]),
                         (prev[k], ring[k2], ring[k])]
        prev = ring
    top = len(verts)
    verts.append((cx, h * 1.02, cz))
    for k in range(10):
        tris.append((prev[k], prev[(k + 1) % 10], top))
    m.add(Part(verts, tris, smooth=True), mat)


def piece_floorstuff():
    """The floor of this closet is genuinely covered -- both photos show duffel
    bags, laundry baskets, rolled mats, black woven baskets and shoes.  A tidy
    empty closet would not be this room."""
    m = Model()
    # ---- contact shadows first, all at y = 0.05 so they beat the slab
    for (cx, cz, rx, rz, s) in ((3.35, 5.55, 1.35, 1.05, 0.50),
                                (6.05, 6.20, 1.05, 0.90, 0.48),
                                (8.30, 5.10, 0.95, 0.85, 0.46),
                                (10.60, 6.35, 1.15, 0.95, 0.48),
                                (1.55, 6.65, 0.95, 0.80, 0.46),
                                (12.30, 4.25, 0.80, 0.70, 0.42)):
        contact_shadow(m, cx, cz, rx, rz, y=0.050, strength=s, room=(W, D))
    # ---- navy duffels
    bag(m, NAVY, 3.30, 5.50, 1.05, 0.72, 0.92, 331)
    bag(m, NAVY2, 10.55, 6.30, 0.88, 0.62, 0.80, 917)
    bag(m, CHARC, 6.00, 6.15, 0.72, 0.55, 0.62, 553)
    # ---- cream laundry basket with towels
    m.add(cylinder(0.72, 1.05, 16, r_top=0.80), LIN, at=(8.25, 0.05, 5.05))
    bag(m, LIN2, 8.25, 5.05, 0.66, 0.66, 1.55, 77)
    m.add(cylinder(0.58, 0.86, 14, r_top=0.64), LIN2, at=(1.50, 0.05, 6.60))
    # ---- black woven baskets
    for (cx, cz, r, h) in ((4.95, 7.00, 0.62, 0.72), (6.35, 7.25, 0.56, 0.66)):
        m.add(cylinder(r, h, 14, r_top=r * 0.95), BLKWEAVE, at=(cx, 0.05, cz))
        m.add(cylinder(r * 0.98, 0.06, 14), CHARC, at=(cx, 0.05 + h, cz))
        bag(m, GREYT, cx, cz, r * 0.85, r * 0.85, h + 0.42, int(cx * 100))
    # ---- rolled mats leaning on the black wall
    for (cx, col, ln) in ((11.85, TEAL, 2.05), (12.40, MATG, 2.15)):
        m.add(cylinder(0.31, ln, 14), col, at=(cx, 0.34, D - 1.15),
              rot_x=R(74))
    # ---- folded piles and a grey throw on the carpet
    rn = Rnd(6161)
    for i in range(9):
        cx = rn.f(2.0, 12.4)
        cz = rn.f(3.6, 7.6)
        mat = (LIN, LIN2, GREYT, CHARC)[int(rn.f(0, 3.99))]
        bx(m, mat, cx, cx + rn.f(0.75, 1.45), 0.055,
           0.055 + rn.f(0.14, 0.34), cz, cz + rn.f(0.55, 1.05))
    # ---- shoes lined along the foot of the steps
    for i in range(7):
        sx = 0.65 + i * 0.42
        m.add(rounded_box(0.32, 0.17, 0.80, 0.07, 3), SHOE,
              at=(sx, 0.055, D - 1.62 + (i % 2) * 0.12))
    return m


# ================================================================= 8 carpet
def piece_carpet():
    """A low-relief carpet field over the slab: the app's carpet texture gives
    the nap, this gives the large-scale tone drift the photo has (sd 11-14, not
    the flat slab's 0)."""
    m = Model()
    rn = Rnd(1919)
    cell = 1.15
    nx, nz = int(W / cell) + 1, int(D / cell) + 1
    for i in range(nx):
        for k in range(nz):
            x0 = i * cell
            z0 = k * cell
            rect_up(m, CARP[int(rn.f(0, 3.99))], x0, min(W, x0 + cell), 0.014,
                    z0, min(D, z0 + cell))
    return m


# ============================================================== 9 wall skins
def piece_skins(colors):
    """Per-wall NON-emissive albedo skins on all four walls.  The east and west
    walls are cut down to the raking ceiling in 0.7 ft bands so a skin never
    pokes through the roof plane."""
    m = Model()
    bot = BB_H - 0.03
    holes = {"n": [(DOOR[0] - 0.34, DOOR[1] + 0.34, 0.0, DOOR_TOP_27 + 0.34)],
             "s": [], "e": [], "w": []}
    wall_skin(m, "n", W, D, colors["n"], bot, H - 0.06, holes["n"])
    wall_skin(m, "s", W, D, colors["s"], bot, LOW_Y - 0.10)
    for wall in ("e", "w"):
        mat = Material("skin" + colors[wall].lstrip("#"), colors[wall],
                       roughness=0.95, metallic=0.0)
        z = 0.0
        while z < D - 0.001:            # 0.12 ft bands: the rake step is ~1 in
            z2 = min(D, z + 0.12)
            y1 = ceil_y(z2) - 0.045
            if wall == "w":
                bx(m, mat, 0.026, 0.036, bot, y1, z, z2)
            else:
                bx(m, mat, W - 0.036, W - 0.026, bot, y1, z, z2)
            z = z2
    return m


# ===================================================================== main
SKINS = {"n": "#c8c8c8", "s": "#dcdcdc", "e": "#c0c0c0", "w": "#c0c0c0"}

WANT_OPENINGS = [
    # edge 0 = north wall (z = 12.40 world), offset measured from x = 18.60.
    # Room 16's own cut (id 123) is world x 19.10..21.60 -> offset 0.50 w 2.50.
    ("passage", 0, DOOR[0], DOOR[1] - DOOR[0], 0.0, DOOR_TOP_27),
]

PIECES = {
    "ceiling": ("Master Closet Ceiling", piece_ceiling),
    "base": ("Master Closet Baseboards", piece_baseboards),
    "black": ("Master Closet Wall Wash Dark", piece_black_wall),
    "steps": ("Master Closet Step Bench", piece_steps),
    "shelving": ("Master Closet Shelving", piece_shelving),
    "hang": ("Master Closet Hanging Rack", piece_hanging),
    "stuff": ("Master Closet Clutter", piece_floorstuff),
    "carpet": ("Master Closet Floor Carpet", piece_carpet),
}


def main(only=None):
    print("room 27 Master Closet")
    if only in (None, "surf"):
        surfaces(ROOM, wall_color="#e6e4e0", floor_color="#8b8b88",
                 floor_texture="carpet")
        openings(ROOM, WANT_OPENINGS)
    for k, (name, fn) in PIECES.items():
        if only in (None, k):
            save_and_place(name, fn(), ROOM)
    if only in (None, "skins"):
        save_and_place("Master Closet Wall Wash Skins", piece_skins(SKINS), ROOM)


if __name__ == "__main__":
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else None)
