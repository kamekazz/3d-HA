"""Room 17 -- Hallway, second floor (8.1 x 16.7 x 8.0), level 2.

ORIENTATION, derived before modelling:
  * Room rect world x 10.50..18.60, z 6.60..23.30.  Adjacencies: Master Bed (14)
    NORTH across z=6.60 (its edge 1 runs x 13.84..18.62 at z=6.30), Guest Room
    (13) WEST over z 6.5..17.3, Master Bath (16) and Master Closet (27) EAST,
    2F bath (26) SOUTH across z=23.3.
  * The stairwell is the level-1 `stairs` row (world x 14.6..18.4, z 14.3..24.5)
    = local x 4.1..7.9, z 7.7..16.7, i.e. the room's SOUTH-EAST half.
  * Registering docs/floor plan/Second Floor Plan App.png to world feet
    (planmap.py key "2f", six independent checks all within 0.2 ft) puts a wall
    line at world x 14.35 running z 13.40..23.55 -- that is the KNEE WALL, on
    the WEST side of the stairwell, exactly where the stair row says the well
    is.  The plan also draws the top treads at x 14.7..18.2, z 14.45..16.90.
  * So the primary photo ('Second-floor hallway.jpg'), which has the knee wall
    running away on the RIGHT and a cased opening slightly right of centre at
    the far end, is shot from the SOUTH looking NORTH: left = WEST, right =
    EAST, and that far opening is the master-bedroom doorway on the NORTH wall.
    'Hallway to Master Bedroom.jpg' is the same doorway close up, with the
    solid west wall (return-air grille + snake plant) on its left -- which the
    plan agrees is solid over world z 6.30..15.30.

OPENINGS (wallscan.py on the "2f" plan):
    north  world x 14.55..17.45  (2.90)  -> Master Bedroom, cased, no leaf
    west   world z 15.30..22.50  (7.20 gap in the plan).  Room 13 has already
           cut z 14.55..17.28 on its own side (its opening id 111) -- matched
           EXACTLY.  The rest of the plan gap faces a space that has no room in
           the layout at all (world x 6.7..10.5, z 17.3..22.7), so the second
           doorway there is cut as a hole with an opaque leaf in it.
    south  world x 11.40..14.20  (2.80)  -> the 2F bathroom (room 26)
    east   SOLID for its whole length -- the master bath is entered from the
           master bedroom and the master closet from its own door (see r27).
"""

import math
from ckit import *                                             # noqa: F401,F403
from ckit import save_and_place, openings, wall_skin, blit, plant_stand

ROOM, W, D, H = 17, 8.1, 16.7, 8.0

MBED = (4.05, 6.95)          # north wall, local x
GUEST = (7.95, 10.68)        # west wall, local z  (== room 13 id 111)
WDOOR = (11.90, 14.60)       # west wall, local z  -- second doorway
BATH = (0.90, 3.70)          # south wall, local x -- 2F bathroom
PASS_TOP = 7.00
LEAF_TOP = 6.78

KW_X = 3.95                  # knee wall, local x (world 14.45)
KW_Z0, KW_Z1 = 6.80, 16.70   # its run, local z
KW_H = 3.05
WELL = (4.10, 8.05, 7.70, 16.70)   # the stairwell footprint, local

# ---------------------------------------------------------------- materials
PLANK = [Material("h17pl%d" % i, c, roughness=0.90) for i, c in enumerate(
    ("#3c3b39", "#414040", "#464544", "#4a4947", "#4f4e4c", "#3f3e3c",
     "#4c4b49", "#444341"))]
WOOL = Material("h17wool", "#ded9cf", roughness=0.98)
WOOL2 = Material("h17wool2", "#cec9be", roughness=0.98)
POT = Material("h17pot", "#eeece7", roughness=0.55)
POTT = Material("h17pott", "#8fb9b6", roughness=0.50)          # the teal pot
LEAFA = Material("h17leafa", "#55693f", roughness=0.88)
LEAFB = Material("h17leafb", "#3f5230", roughness=0.86)
LEAFEDGE = Material("h17leafe", "#93a05e", roughness=0.88)
STEEL = Material("h17steel", "#8e9096", roughness=0.38, metallic=0.55)
STEEL2 = Material("h17steel2", "#adb0b5", roughness=0.34, metallic=0.55)
WELLDK = Material("h17well", "#3c3c3e", roughness=0.95)
GRIL = Material("h17gril", "#f2f1ee", roughness=0.55)
GRILD = Material("h17grild", "#9a9a97", roughness=0.70)


# ================================================================= 1 ceiling
def piece_ceiling():
    # NO crown: every shot of this floor shows a clean drywall corner.
    m = ceiling(W, D, H, crown=False,
                cans=[(6.30, 2.30), (2.30, 4.70), (5.90, 4.90), (2.10, 9.20),
                      (6.10, 12.40)],
                fixtures=[(2.70, 2.85, 0.52)],
                vents=[(1.30, 13.60, 0.52, 0.95)])
    return m


# ============================================== 2 skirting, casings, leaves
def leaf_unit(m, wall, a0, a1, top=LEAF_TOP, handle_left=True, depth=0.30):
    """A cased 6-panel leaf filling a `passage` cut (the app draws no panel in
    one), authored in ROOM-LOCAL axis order and blitted with ckit.blit."""
    sub = Model()
    for a, b in ((a0 - 0.08, a0), (a1, a1 + 0.08)):
        bx(sub, TRIM, a, b, 0.0, top, 0.0, depth)
    bx(sub, TRIM, a0 - 0.08, a1 + 0.08, top, top + 0.08, 0.0, depth)
    panel_door(sub, WHITEWD, a0 + 0.02, a1 - 0.02, 0.02, top - 0.03,
               0.08, depth - 0.08, rows=3)
    hx = a0 + 0.30 if handle_left else a1 - 0.30
    sub.add(cylinder(0.080, 0.05, 12), BLACKMET, at=(hx, 3.05, depth - 0.03),
            rot_x=R(90))
    bx(sub, BLACKMET, hx - 0.08, hx + 0.08, 2.97, 3.06, depth - 0.03, depth + 0.14)
    for a, b in ((a0 - 0.08 - CASE_W, a0 - 0.06), (a1 + 0.06, a1 + 0.08 + CASE_W)):
        bx(sub, TRIM, a, b, 0.0, top + CASE_W, 0.0, 0.10)
    bx(sub, TRIM, a0 - 0.08 - CASE_W, a1 + 0.08 + CASE_W, top + 0.08,
       top + CASE_W, 0.0, 0.10)
    blit(m, sub, wall, W, D, 0.0)


def cased(m, wall, a0, a1, top=PASS_TOP, jamb=True):
    sub = Model()
    for a, b in ((a0 - CASE_W, a0 + 0.03), (a1 - 0.03, a1 + CASE_W)):
        bx(sub, TRIM, a, b, 0.0, top + CASE_W, 0.0, 0.20)
    bx(sub, TRIM, a0 - CASE_W, a1 + CASE_W, top, top + CASE_W, 0.0, 0.20)
    if jamb:
        bx(sub, TRIM, a0 - 0.04, a0 + 0.03, 0.0, top, -0.16, 0.02)
        bx(sub, TRIM, a1 - 0.03, a1 + 0.04, 0.0, top, -0.16, 0.02)
        bx(sub, TRIM, a0 - 0.04, a1 + 0.04, top - 0.07, top, -0.16, 0.02)
    blit(m, sub, wall, W, D, 0.0)


def piece_baseboards():
    m = baseboards(W, D, doors=[("n", *MBED), ("w", *GUEST), ("w", *WDOOR),
                                ("s", *BATH)])
    cased(m, "n", *MBED)
    cased(m, "w", *GUEST)
    leaf_unit(m, "w", *WDOOR)
    leaf_unit(m, "s", *BATH, handle_left=False)
    # high return-air grille, west wall at the north end ('Hallway to Master
    # Bedroom.jpg' puts it just below the ceiling, left of the opening)
    gz0, gz1 = 0.95, 2.45
    bx(m, GRIL, 0.02, 0.13, 6.30, 7.10, gz0, gz1)
    for k in range(6):
        y = 6.38 + k * 0.122
        bx(m, GRILD, 0.13, 0.155, y, y + 0.055, gz0 + 0.05, gz1 - 0.05)
    # thermostat / switch plates on the west wall
    bx(m, GRIL, 0.02, 0.08, 4.10, 4.72, 5.35, 5.72)
    bx(m, GRIL, 0.02, 0.07, 3.55, 4.05, 6.55, 6.90)
    # thresholds under the two west cuts (0.0-0.25 ft of open slab gap beyond)
    THR = Material("h17thr", "#4a4844", roughness=0.75)
    for (a0, a1) in (GUEST, WDOOR):
        bx(m, THR, -0.26, 0.10, 0.012, 0.052, a0 + 0.02, a1 - 0.02)
    bx(m, THR, BATH[0] + 0.02, BATH[1] - 0.02, 0.012, 0.052, D - 0.10, D + 0.26)
    return m


# ============================================================== 3 knee wall
def piece_kneewall():
    """The white capped half wall round the stairwell -- solid, no spindles,
    which is what every shot of this floor shows."""
    m = Model()
    x, z0, z1 = KW_X, KW_Z0, KW_Z1
    t = 0.42                                  # wall thickness
    # body, both faces, plus a skirting return on the hall side
    bx(m, TRIM, x - t, x, 0.0, KW_H, z0, z1)
    bx(m, TRIM, x - t - 0.055, x - t, 0.0, BB_H, z0, z1)
    bx(m, TRIM, x, x + 0.055, 0.0, BB_H, z0, z1)
    # a wide flat cap with a small nose either side (the photo's rail cap)
    bx(m, TRIM, x - t - 0.10, x + 0.10, KW_H, KW_H + 0.13, z0 - 0.10, z1)
    bx(m, TRIM_D, x - t - 0.07, x + 0.07, KW_H - 0.05, KW_H, z0 - 0.07, z1)
    # newel block where the run starts, at the head of the flight
    bx(m, TRIM, x - t - 0.09, x + 0.09, 0.0, KW_H + 0.26, z0 - 0.42, z0 + 0.05)
    bx(m, TRIM, x - t - 0.16, x + 0.16, KW_H + 0.26, KW_H + 0.40,
       z0 - 0.49, z0 + 0.12)
    return m


# ========================================================= 4 the stairwell
def piece_well():
    """The stairwell reads as a shadowed well with the top nosing of the flight.

    NOTE (also in the report): room 17's footprint has no void in it, and the
    app draws one opaque slab across the whole rect, so the real opening down
    to the first floor CANNOT be shown -- the app's stair mesh tops out 0.01 ft
    UNDER this floor's slab.  Footprints are ground truth and may not be
    edited, so this is a dark inset panel plus a white nosing board at the head
    of the flight, which reads as a well from the dollhouse pose.
    """
    m = Model()
    x0, x1, z0, z1 = WELL
    rect_up(m, WELLDK, x0 + 0.10, x1 - 0.06, 0.012, z0 + 0.10, z1 - 0.06)
    # the top tread's nosing, at the head of the flight
    bx(m, TRIM, x0 + 0.02, x1 - 0.02, 0.012, 0.085, z0 - 0.02, z0 + 0.14)
    bx(m, Material("h17noserun", "#8b8783", roughness=0.95),
       x0 + 0.72, x1 - 0.72, 0.085, 0.115, z0 - 0.02, z0 + 0.14)
    # a kerb round the other three sides so the panel does not read as a rug
    for (a, b, c, d) in ((x0 + 0.02, x0 + 0.12, z0 + 0.10, z1),
                         (x1 - 0.12, x1 - 0.02, z0 + 0.10, z1),
                         (x0 + 0.02, x1 - 0.02, z1 - 0.10, z1)):
        bx(m, TRIM, a, b, 0.012, 0.070, c, d)
    return m


# ============================================================ 5 soft goods
def piece_runner():
    """The chunky cream knit runner down the middle of the hall (primary photo,
    metered 190.9 / sd 24.8)."""
    m = Model()
    x0, x1, z0, z1 = 0.85, 3.35, 2.40, 12.20
    contact_shadow(m, (x0 + x1) / 2, (z0 + z1) / 2, 1.42, 4.90, y=0.050,
                   strength=0.42, room=(W, D))
    bx(m, WOOL, x0, x1, 0.056, 0.116, z0, z1)
    # chunky braid: fat rolls across the width, readable at 50 degrees
    # shallow rolls: the first pass used r=0.055 cylinders and their shaded
    # undersides read as hard black stripes, nothing like the photo's soft knit
    n = int((z1 - z0) / 0.26)
    for i in range(n):
        z = z0 + 0.07 + i * 0.26
        m.add(cylinder(0.030, x1 - x0 - 0.10, 8), (WOOL if i % 2 else WOOL2),
              at=((x0 + x1) / 2, 0.110, z + 0.06), rot_z=R(90))
    return m


def piece_floor_planks():
    m = Model()
    rn = Rnd(4407)
    pw = W / 14.0
    for c in range(14):
        x0 = c * pw
        z = -1.0
        while z < D:
            L = rn.f(3.2, 7.2)
            z1 = min(D, z + L)
            if z1 > 0.0:
                rect_up(m, PLANK[int(rn.f(0, 7.99))], x0 + 0.012,
                        x0 + pw - 0.012, 0.014, max(0.0, z) + 0.014, z1 - 0.014)
            z = z1
    return m


# ================================================================ 6 styling
def blade(m, mat, cx, cy, cz, ang, lean, h, w):
    dx, dz = math.cos(ang), math.sin(ang)
    tipx, tipz = cx + lean * dx, cz + lean * dz
    px, pz = -dz * w / 2, dx * w / 2
    v = [(cx + px, cy, cz + pz), (cx - px, cy, cz - pz),
         (cx + (tipx - cx) * 0.55 - px * 0.85, cy + h * 0.58,
          cz + (tipz - cz) * 0.55 - pz * 0.85),
         (cx + (tipx - cx) * 0.55 + px * 0.85, cy + h * 0.58,
          cz + (tipz - cz) * 0.55 + pz * 0.85),
         (tipx, cy + h, tipz)]
    m.add(Part(v, [(0, 1, 2), (0, 2, 3), (3, 2, 4)], smooth=True), mat)


def snake_plant(m, cx, cz, pot_mat, seed, stand_h=1.15, scale=1.0):
    contact_shadow(m, cx, cz, 0.86, 0.86, y=0.050, strength=0.46, room=(W, D))
    plant_stand(m, cx, cz, 0.50, stand_h, BLACKMET)
    m.add(cylinder(0.46, 0.80 * scale, 16, r_top=0.40), pot_mat,
          at=(cx, stand_h, cz))
    rn = Rnd(seed)
    y0 = stand_h + 0.72 * scale
    for i in range(12):
        a = 2 * math.pi * i / 12 + rn.f(-0.22, 0.22)
        blade(m, (LEAFB if i % 3 else LEAFA), cx + 0.14 * math.cos(a), y0,
              cz + 0.14 * math.sin(a), a, rn.f(0.18, 0.55),
              rn.f(1.55, 2.60) * scale, rn.f(0.18, 0.27))
    for i in range(4):
        a = 2 * math.pi * i / 4 + 0.7
        blade(m, LEAFEDGE, cx + 0.10 * math.cos(a), y0,
              cz + 0.10 * math.sin(a), a, rn.f(0.20, 0.45),
              rn.f(1.5, 2.3) * scale, 0.14)


def piece_plants():
    m = Model()
    snake_plant(m, 0.85, 1.55, POT, 771, stand_h=1.15)          # west wall
    snake_plant(m, 7.30, 1.35, POTT, 913, stand_h=1.35, scale=0.9)   # east wall
    return m


def piece_wall_art():
    """The abstract welded-steel sculpture on the west wall (primary photo)."""
    m = Model()
    x = 0.05
    z0, z1, y0, y1 = 3.30, 5.05, 3.65, 6.45
    rn = Rnd(1212)
    # a woven lattice, not a scatter: rods spanning most of the panel in both
    # directions, jittered in depth and angle so it reads as welded sticks
    for i in range(15):
        y = y0 + (i + 0.5) * (y1 - y0) / 15 + rn.f(-0.055, 0.055)
        a = rn.f(0.10, 0.42)
        b = rn.f(0.58, 0.94)
        m.add(box(0.036, 0.036, (b - a) * (z1 - z0)),
              (STEEL if i % 3 else STEEL2),
              at=(x + rn.f(0.0, 0.085), y, z0 + (a + b) / 2 * (z1 - z0)),
              rot_x=R(rn.f(-7, 7)))
    for i in range(13):
        z = z0 + (i + 0.5) * (z1 - z0) / 13 + rn.f(-0.05, 0.05)
        a = rn.f(0.05, 0.38)
        b = rn.f(0.60, 0.97)
        m.add(box(0.036, (b - a) * (y1 - y0), 0.036),
              (STEEL2 if i % 3 else STEEL),
              at=(x + rn.f(0.0, 0.085), y0 + (a + b) / 2 * (y1 - y0), z),
              rot_z=R(rn.f(-6, 6)))
    return m


# ============================================================== 7 wall skins
def piece_skins(colors):
    m = Model()
    top = H - 0.06
    bot = BB_H - 0.03
    holes = {
        "n": [(MBED[0] - 0.34, MBED[1] + 0.34, 0.0, PASS_TOP + 0.34)],
        "w": [(GUEST[0] - 0.34, GUEST[1] + 0.34, 0.0, PASS_TOP + 0.34),
              (WDOOR[0] - 0.42, WDOOR[1] + 0.42, 0.0, LEAF_TOP + 0.42)],
        "s": [(BATH[0] - 0.42, BATH[1] + 0.42, 0.0, LEAF_TOP + 0.42)],
        "e": [],
    }
    for wall in "nswe":
        wall_skin(m, wall, W, D, colors[wall], bot, top, holes[wall])
    return m


# ===================================================================== main
SKINS = {"n": "#6b6b6b", "s": "#f1f1f1", "e": "#c8c8c8", "w": "#a4a4a4"}

WANT_OPENINGS = [
    ("passage", 0, MBED[0], MBED[1] - MBED[0], 0.0, PASS_TOP),
    ("passage", 3, D - GUEST[1], GUEST[1] - GUEST[0], 0.0, 6.78),
    ("passage", 3, D - WDOOR[1], WDOOR[1] - WDOOR[0], 0.0, LEAF_TOP),
    ("passage", 2, W - BATH[1], BATH[1] - BATH[0], 0.0, LEAF_TOP),
]

PIECES = {
    "ceiling": ("Hall2F Ceiling", piece_ceiling),
    "base": ("Hall2F Baseboards", piece_baseboards),
    "knee": ("Hall2F Knee Wall", piece_kneewall),
    "well": ("Hall2F Floor Stairwell", piece_well),
    "runner": ("Hall2F Floor Runner", piece_runner),
    "planks": ("Hall2F Floor Planks", piece_floor_planks),
    "plants": ("Hall2F Plants", piece_plants),
    "art": ("Hall2F Wall Art", piece_wall_art),
}


def main(only=None):
    print("room 17 Hallway (2F)")
    if only in (None, "surf"):
        surfaces(ROOM, wall_color="#d4d6d7", floor_color="#474642",
                 floor_texture="wood")
        openings(ROOM, WANT_OPENINGS)
    for k, (name, fn) in PIECES.items():
        if only in (None, k):
            save_and_place(name, fn(), ROOM)
    if only in (None, "skins"):
        save_and_place("Hall2F Wall Wash Skins", piece_skins(SKINS), ROOM)
    # the shell pass's balustrade is superseded by "Hall2F Knee Wall"
    if only is None:
        from roomkit.place import _req
        try:
            _req("DELETE", "/api/house/object/%d" % _find_obj("Hall2F Balustrade"))
            print("  removed superseded 'Hall2F Balustrade'")
        except Exception as exc:              # already gone
            print("  (Hall2F Balustrade:", exc, ")")


def _find_obj(name):
    from ckit import room_row
    for o in room_row(ROOM).get("objects", []):
        if o.get("name") == name:
            return o["id"]
    raise LookupError(name)


if __name__ == "__main__":
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else None)
