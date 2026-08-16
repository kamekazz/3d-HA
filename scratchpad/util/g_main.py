"""Garage -- the big defining pieces: the car, the sectional-door hardware,
the step up to the house door, and every contact shadow / floor mark.

No interior photo of this garage exists.  The sectional door and the person
door were already in the shell; the plan gives the west storage run, the two
east blobs and the step at the house door.  Everything else -- including the
car -- is inference.  The car is deliberately a light silver saloon so it does
NOT read as a second copy of the black SUV that environment.js parks on the
driveway outside.
"""
import math

from gkit import *   # noqa: F401,F403
import gkit as G

ROOM = 7
W, D, H = 20.4, 21.7, 9.0
CEIL = 8.87
DOOR_X0, DOOR_X1 = 1.76, 18.64        # existing "Garage Door Panel" opening
DOOR_HEAD = 7.42

SOUTH_SKIN = "#b4b0a8"
CAR_CX, CAR_CZ = 12.70, 12.70         # bay centre (west bay is the stuff bay)


# --------------------------------------------------------------------- car
BODY = Material("carbody", "#a4a8ad", roughness=0.46, metallic=0.16)
BODY_D = Material("carbodyd", "#83878c", roughness=0.48, metallic=0.16)
TINT = Material("cartint", "#252a30", roughness=0.42, metallic=0.0, opacity=0.88)
TAIL = Material("cartail", "#9c2620", roughness=0.30)
HEAD = Material("carhead", "#e6ecef", roughness=0.20)


def car():
    m = Model()
    S = [(-7.55, 2.42, 0.66, 1.98), (-6.95, 2.82, 0.56, 2.26),
         (-6.10, 2.94, 0.56, 2.52), (-5.72, 2.96, 1.32, 2.55),
         (-4.90, 2.99, 1.66, 2.64), (-4.08, 2.99, 1.32, 2.72),
         (-3.68, 2.99, 0.54, 2.76), (-1.50, 3.00, 0.52, 2.86),
         (1.50, 3.00, 0.52, 2.86), (3.28, 2.99, 0.55, 2.83),
         (3.66, 2.98, 1.32, 2.81), (4.48, 2.96, 1.66, 2.78),
         (5.30, 2.93, 1.32, 2.74), (5.68, 2.91, 0.55, 2.71),
         (6.90, 2.80, 0.60, 2.56), (7.42, 2.44, 0.74, 2.36)]
    m.add(G.loft([(z, G.section(hw, y0, y1, 0.30)) for (z, hw, y0, y1) in S]),
          BODY, at=(CAR_CX, 0.0, CAR_CZ))

    # cabin: trapezoid sections (wide at the belt, narrow at the roof)
    C = [(-3.55, 2.52, 2.44, 2.80, 2.98), (-2.45, 2.66, 2.36, 2.84, 4.02),
         (-1.20, 2.72, 2.30, 2.86, 4.52), (1.75, 2.72, 2.30, 2.86, 4.55),
         (3.10, 2.66, 2.36, 2.84, 4.30), (4.45, 2.50, 2.42, 2.80, 3.05)]
    cab = [(z, [(-hb, yb), (hb, yb), (ht, yt), (-ht, yt)])
           for (z, hb, ht, yb, yt) in C]
    m.add(G.loft(cab, caps=True), TINT, at=(CAR_CX, 0.0, CAR_CZ))
    # painted roof + pillars over the glass
    m.add(G.loft([(z, [(-ht + 0.04, yt - 0.05), (ht - 0.04, yt - 0.05),
                       (ht - 0.10, yt + 0.03), (-ht + 0.10, yt + 0.03)])
                  for (z, hb, ht, yb, yt) in C[2:4]], caps=False),
          BODY, at=(CAR_CX, 0.0, CAR_CZ))
    for dz in (-1.22, 1.77):
        bx(m, BODY, CAR_CX - 2.75, CAR_CX + 2.75, 4.44, 4.58,
           CAR_CZ + dz - 0.10, CAR_CZ + dz + 0.10)
    # B pillars
    for dz in (0.30,):
        for dx in (-2.76, 2.76):
            bx(m, BODY_D, CAR_CX + dx - 0.06, CAR_CX + dx + 0.06, 2.84, 4.52,
               CAR_CZ + dz - 0.16, CAR_CZ + dz + 0.16)

    # wheels
    for (dz, dx) in ((-4.90, -2.62), (-4.90, 2.62), (4.48, -2.62), (4.48, 2.62)):
        G.wheel(m, CAR_CX + dx, 1.12, CAR_CZ + dz)

    # lights, grille, plates, mirrors, door lines
    bx(m, HEAD, CAR_CX - 2.35, CAR_CX - 1.05, 1.62, 2.10, CAR_CZ - 7.60, CAR_CZ - 7.30)
    bx(m, HEAD, CAR_CX + 1.05, CAR_CX + 2.35, 1.62, 2.10, CAR_CZ - 7.60, CAR_CZ - 7.30)
    bx(m, G.BLK, CAR_CX - 0.95, CAR_CX + 0.95, 1.52, 2.05, CAR_CZ - 7.62, CAR_CZ - 7.34)
    bx(m, G.BLK, CAR_CX - 2.30, CAR_CX + 2.30, 0.72, 1.28, CAR_CZ - 7.58, CAR_CZ - 7.36)
    bx(m, TAIL, CAR_CX - 2.36, CAR_CX - 0.95, 1.90, 2.32, CAR_CZ + 7.30, CAR_CZ + 7.50)
    bx(m, TAIL, CAR_CX + 0.95, CAR_CX + 2.36, 1.90, 2.32, CAR_CZ + 7.30, CAR_CZ + 7.50)
    bx(m, G.WHITE, CAR_CX - 0.62, CAR_CX + 0.62, 1.05, 1.52, CAR_CZ + 7.36, CAR_CZ + 7.48)
    for dx in (-3.05, 3.05):
        bx(m, BODY_D, CAR_CX + dx - 0.22, CAR_CX + dx + 0.22, 2.62, 2.98,
           CAR_CZ - 3.30, CAR_CZ - 2.80)
    for dz in (-1.25, 0.32, 1.80):
        for dx in (-3.01, 3.01):
            bx(m, BODY_D, CAR_CX + dx - 0.02, CAR_CX + dx + 0.02, 0.70, 2.84,
               CAR_CZ + dz - 0.025, CAR_CZ + dz + 0.025)
    for (dz, dx) in ((-0.55, -3.02), (-0.55, 3.02)):
        m.add(cylinder(0.08, 0.16, 8, anchor="center"), G.CHR,
              at=(CAR_CX + dx, 2.45, CAR_CZ + dz), rot_z=G.R(90))
    return m


# ------------------------------------------------------ sectional-door gear
def opener():
    m = Model()
    TR = G.STEEL
    # vertical track each side of the opening, then the horizontal run back
    for xx in (DOOR_X0 + 0.28, DOOR_X1 - 0.28):
        bx(m, TR, xx - 0.11, xx + 0.11, 0.30, DOOR_HEAD - 0.55, D - 0.58, D - 0.40)
        # curve, approximated by three short segments
        for i, (yy, zz, ln) in enumerate(((DOOR_HEAD - 0.50, D - 0.62, 0.55),
                                          (DOOR_HEAD - 0.16, D - 1.05, 0.75),
                                          (DOOR_HEAD - 0.02, D - 1.70, 0.60))):
            bx(m, TR, xx - 0.11, xx + 0.11, yy - 0.09, yy + 0.09, zz - ln / 2, zz + ln / 2)
        bx(m, TR, xx - 0.11, xx + 0.11, DOOR_HEAD - 0.04, DOOR_HEAD + 0.10,
           D - 9.60, D - 1.90)
        # hangers to the ceiling
        for zz in (D - 3.40, D - 8.60):
            bx(m, G.STEEL_D, xx - 0.05, xx + 0.05, DOOR_HEAD + 0.10, CEIL, zz - 0.06, zz + 0.06)
    # torsion tube + springs above the head
    m.add(cylinder(0.105, DOOR_X1 - DOOR_X0 + 0.4, 12), G.STEEL_D,
          at=(DOOR_X0 - 0.20, DOOR_HEAD + 0.42, D - 0.44), rot_z=G.R(-90))
    for sx in (W / 2 - 2.05, W / 2 + 0.35):
        m.add(cylinder(0.21, 1.70, 14), G.BLK,
              at=(sx, DOOR_HEAD + 0.42, D - 0.44), rot_z=G.R(-90))
    for dxx in (DOOR_X0 + 0.10, W / 2 - 0.10, DOOR_X1 - 0.10):
        bx(m, G.STEEL_D, dxx - 0.16, dxx + 0.16, DOOR_HEAD + 0.20, DOOR_HEAD + 0.66,
           D - 0.56, D - 0.34)
    for xx in (DOOR_X0 + 0.28, DOOR_X1 - 0.28):   # cable drums
        m.add(cylinder(0.30, 0.22, 12), G.STEEL_D,
              at=(xx, DOOR_HEAD + 0.31, D - 0.44), rot_z=G.R(90))

    # centre rail from the header back to the motor head
    RX = (DOOR_X0 + DOOR_X1) / 2
    bx(m, G.STEEL, RX - 0.16, RX + 0.16, CEIL - 0.85, CEIL - 0.60, D - 10.80, D - 0.55)
    bx(m, G.STEEL_D, RX - 0.09, RX + 0.09, CEIL - 0.62, CEIL - 0.55, D - 10.80, D - 0.55)
    bx(m, G.BLK, RX - 0.13, RX + 0.13, CEIL - 0.78, CEIL - 0.70, D - 3.20, D - 2.55)  # trolley
    # header bracket + door arm
    bx(m, G.STEEL_D, RX - 0.30, RX + 0.30, DOOR_HEAD + 0.10, CEIL - 0.55, D - 0.60, D - 0.40)
    m.add(box(0.10, 2.28, 0.12), G.STEEL_D, at=(RX, CEIL - 0.80, D - 2.85),
          rot_x=G.R(107.5))
    # motor head hung on angle iron
    bx(m, G.WHITE_A, RX - 0.72, RX + 0.72, CEIL - 1.55, CEIL - 0.62, D - 11.90, D - 10.55)
    bx(m, G.BLK, RX - 0.55, RX + 0.55, CEIL - 1.72, CEIL - 1.55, D - 11.70, D - 10.75)
    bx(m, G.LENS, RX - 0.42, RX + 0.42, CEIL - 1.80, CEIL - 1.72, D - 11.60, D - 10.85)
    for dxx in (-0.62, 0.62):
        for zz in (D - 11.70, D - 10.75):
            bx(m, G.STEEL_D, RX + dxx - 0.05, RX + dxx + 0.05, CEIL - 0.62, CEIL,
               zz - 0.05, zz + 0.05)
    # safety eyes at the jambs + the wall button by the person door
    for xx in (DOOR_X0 + 0.34, DOOR_X1 - 0.34):
        bx(m, G.STEEL_D, xx - 0.09, xx + 0.09, 0.30, 0.62, D - 0.55, D - 0.42)
        bx(m, G.YELLOW, xx - 0.07, xx + 0.07, 0.48, 0.60, D - 0.60, D - 0.55)
    bx(m, G.WHITE, 6.95, 7.45, 4.10, 4.85, 0.02, 0.09)
    bx(m, G.ORANGE, 7.03, 7.37, 4.36, 4.66, 0.09, 0.115)
    return m


# -------------------------------------------------------------------- step
def step():
    """Step up from the garage slab to the house door (the plan draws it)."""
    m = Model()
    x0, x1, z1, h = 2.24, 6.92, 2.05, 0.60
    bx(m, G.CONC_L, x0, x1, 0.0, h - 0.05, 0.0, z1)
    bx(m, G.CONC, x0 - 0.05, x1 + 0.05, h - 0.05, h, -0.02, z1 + 0.05)   # nosing
    bx(m, G.BLK, x0 - 0.05, x1 + 0.05, h - 0.06, h - 0.045, z1 + 0.02, z1 + 0.05)
    # rubber walk-off mat on the tread
    bx(m, Material("mat", "#2e3134", roughness=0.95), x0 + 0.45, x1 - 0.45,
       h, h + 0.035, 0.35, z1 - 0.28)
    # a pair of boots
    for dx in (0.0, 0.42):
        bx(m, Material("boot", "#4a3b2e", roughness=0.85),
           x1 - 1.35 + dx, x1 - 1.05 + dx, h + 0.035, h + 0.62, 0.55, 1.30)
    return m


# ------------------------------------------------- floor marks + shadows
def soft(m, cx, cz, rx, rz, y=0.013, tone="#25262a", strength=0.30,
         steps=8, seg=18):
    """Smooth radial falloff -- same idea as kit.contact_shadow but with the
    ring/segment count tuned down: 21 blobs at kit's defaults cost 590 KB,
    which blows the per-piece budget on its own."""
    a = round(1.0 - (1.0 - strength) ** (1.0 / steps), 4)
    mat = Material("csh%d" % int(strength * 100 + 0.5), tone, roughness=0.98,
                   opacity=a)
    n = 2.7
    for i in range(steps):
        s = 1.0 - 0.90 * (i / steps)
        v = [(cx, y + i * 0.0013, cz)]
        for k in range(seg):
            t = 2 * math.pi * k / seg
            ct, st = math.cos(t), math.sin(t)
            px = cx + rx * s * math.copysign(abs(ct) ** (2.0 / n), ct)
            pz = cz + rz * s * math.copysign(abs(st) ** (2.0 / n), st)
            px = min(max(px, 0.05), W - 0.05)
            pz = min(max(pz, 0.05), D - 0.05)
            v.append((px, y + i * 0.0013, pz))
        m.add(Part(v, [(0, 1 + (k + 1) % seg, 1 + k) for k in range(seg)]), mat)


def floor_marks():
    m = Model()
    JOINT = Material("joint", "#4e4d4a", roughness=0.95, opacity=0.30)
    STAIN = "#3a352c"

    # saw-cut control joints: quartering the slab
    bx(m, JOINT, W / 2 - 0.035, W / 2 + 0.035, 0.0, 0.005, 0.12, D - 0.12)
    bx(m, JOINT, 0.12, W - 0.12, 0.0, 0.005, D / 2 - 0.035, D / 2 + 0.035)

    # drip / oil staining under the engine bay and a couple of older marks
    soft(m, CAR_CX - 0.35, CAR_CZ - 4.30, 1.55, 1.95, y=0.010,
         tone=STAIN, strength=0.30, steps=7, seg=16)
    soft(m, CAR_CX + 1.20, CAR_CZ - 2.10, 0.75, 0.95, y=0.010,
         tone=STAIN, strength=0.18, steps=6, seg=14)
    soft(m, 14.20, 16.90, 1.15, 1.45, y=0.010,
         tone="#4a453c", strength=0.14, steps=6, seg=14)
    soft(m, 5.60, 18.60, 0.95, 1.25, y=0.010,
         tone="#4a453c", strength=0.12, steps=6, seg=14)
    # tyre paths worn from the door into the bay
    for dx in (-2.62, 2.62):
        soft(m, CAR_CX + dx, D - 5.20, 0.42, 5.00, y=0.009,
             tone="#55524b", strength=0.13, steps=5, seg=12)

    # ---- contact shadows.  rx/rz are a touch bigger than the footprint so the
    # falloff has somewhere to fade out; strength is the centre darkness.
    S = [
        (CAR_CX, CAR_CZ, 3.30, 7.85, 0.42),        # car
        (1.05, 3.70, 1.55, 2.45, 0.34),            # tall cabinets
        (1.35, 9.80, 1.75, 4.05, 0.32),            # workbench
        (1.05, 16.40, 1.45, 2.75, 0.32),           # shelving
        (19.20, 4.50, 1.35, 1.45, 0.34),           # water heater
        (19.15, 8.55, 1.55, 2.75, 0.32),           # freezer
        (18.75, 13.55, 1.55, 1.85, 0.28),          # mower
        (19.20, 16.05, 1.30, 1.30, 0.30),          # bins
        (19.20, 18.15, 1.30, 1.30, 0.30),
        (19.20, 20.25, 1.30, 1.30, 0.30),
        (17.10, 17.35, 0.90, 1.00, 0.20),          # recycling crate
        (16.55, 0.85, 3.30, 0.75, 0.22),           # bike
        (5.75, 13.10, 2.45, 3.15, 0.34),           # stuff bay
        (5.30, 17.90, 2.05, 1.85, 0.30),
        (20.85, 0.85, 1.05, 0.55, 0.18),           # scooter
        (1.70, 19.95, 1.05, 1.30, 0.24),           # ladders
        (2.10, 18.15, 0.85, 1.05, 0.20),
        (3.70, 20.80, 0.95, 0.95, 0.26),           # shop vac
        (4.58, 1.05, 2.75, 1.35, 0.30),            # step
    ]
    for (cx, cz, rx, rz, st) in S:
        soft(m, cx, cz, rx, rz, y=0.013, tone="#25262a", strength=st,
             steps=8, seg=18)
    return m


# --------------------------------------------------- south-wall albedo skin
def wall_wash_south():
    """A plain NON-emissive repaint of the south wall's exposed strips.

    Metered empty, this room's four walls sat at N 233 / W 200 / E 168 / S 142.
    The dollhouse quadrant used here (doll_ne) leaves the SOUTH and WEST walls
    standing, so that pair is what a critic sees -- 58 bytes apart.  This is the
    "give each wall its own albedo" fix ROOM-BRIEF allows: roughness matched to
    the room wall (0.95), no emissive, and it covers every exposed strip corner
    to corner so there is no rectangular edge on the wall.
    """
    m = Model()
    SKIN = Material("wsouth", SOUTH_SKIN, roughness=0.95)
    ZW = D - 0.035
    def face(x0, x1, y0, y1):
        m.add(quad((x0, y0, ZW), (x0, y1, ZW), (x1, y1, ZW), (x1, y0, ZW)), SKIN)
    face(0.0, DOOR_X0 + 0.02, 0.0, H)
    face(DOOR_X1 - 0.02, W, 0.0, H)
    face(DOOR_X0 + 0.02, DOOR_X1 - 0.02, 8.05, H)
    return m


if __name__ == "__main__":
    tot = 0
    tot += G.save_and_place("Garage Car", car(), ROOM)
    tot += G.save_and_place("Garage Opener", opener(), ROOM)
    tot += G.save_and_place("Garage Step", step(), ROOM)
    tot += G.save_and_place("Garage Floor Marks", floor_marks(), ROOM)
    print("  main total %.1f KB" % tot)
