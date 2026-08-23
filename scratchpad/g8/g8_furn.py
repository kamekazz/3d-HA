"""Everything that stands in or hangs on room 7, from the v3 photos.

Wall assignment (derivation in the report):
  NORTH z=0     KIES banner, two skateboards, the broom rail and cleaning shelf
  WEST  x=0     three grey metal cabinets (the plan draws them at z 7.4-15.9),
                the red rolling tool chest, extinguisher, hose, feed sacks
  EAST  x=20.4  TV, prints, snowboard, skateboards, scooter, signage, the black
                pegboard and the Liqui Moly clock, the yellow ride-on car, the
                white moulded chair, the speaker cabinet and the wall fan

Everything on the north wall hangs off the furring face (gk.NF), not z=0.
"""
import math

from gk import *   # noqa: F401,F403
import gk as G

R90 = math.pi / 2


# =========================================================== NORTH: banner
def banner():
    """The big KIES MOTORSPORTS vinyl of a white M4, plus two boards.

    Photo 1: a landscape banner filling the north wall from just east of the
    service door to the corner, hung by grommets, its top a foot below the
    ceiling.  Built as flat plates on a vinyl ground -- the wordmark, the blue
    paint-splash ground and a blocked-out M4 -- because at any distance this
    room is ever seen from, that is what the graphic reads as.
    """
    m = Model()
    # Sized against the photo rather than the first pass's guess: the vinyl
    # runs from just east of the hung skateboards all the way to the NE
    # corner and its bottom edge sits about a foot off the floor.
    x0, x1, y0, y1 = 7.60, 18.85, 1.42, 7.30
    panel(m, BANNERW, "n", x0, x1, y0, y1, off=0.02)
    # pale blue paint-splash ground, so the white car separates from the vinyl
    for (a, b, c, d) in ((x0 + 0.25, x1 - 0.25, y0 + 0.30, y0 + 3.10),
                         (x0 + 1.10, x1 - 1.20, y0 + 3.10, y0 + 3.70),
                         (x0 + 2.60, x1 - 2.40, y0 + 3.70, y0 + 4.05)):
        panel(m, Material("gbansplash", "#e4e9f0", roughness=0.74),
              "n", a, b, c, d, off=0.03)

    # --- KIES, as real letterforms.  Four solid blocks read as "a smudge" at
    # any distance this room is seen from; strokes read as type.
    def stroke(a, b, c, d):
        panel(m, BANNERK, "n", a, b, c, d, off=0.05)

    cap, base, t = 1.15, 5.55, 0.24
    for i, ch in enumerate("KIES"):
        L = x0 + 3.45 + i * 1.22
        if ch == "K":
            stroke(L, L + t, base, base + cap)
            stroke(L + t, L + 0.82, base + cap * 0.52, base + cap * 0.76)
            stroke(L + t, L + 0.82, base + cap * 0.22, base + cap * 0.46)
            stroke(L + 0.62, L + 0.90, base + cap * 0.70, base + cap)
            stroke(L + 0.62, L + 0.90, base, base + cap * 0.30)
        elif ch == "I":
            stroke(L + 0.28, L + 0.28 + t, base, base + cap)
        elif ch == "E":
            stroke(L, L + t, base, base + cap)
            for yy in (base, base + (cap - t) / 2, base + cap - t):
                stroke(L, L + 0.86, yy, yy + t)
        else:                                     # S
            stroke(L, L + 0.90, base + cap - t, base + cap)
            stroke(L, L + 0.90, base + (cap - t) / 2, base + (cap - t) / 2 + t)
            stroke(L, L + 0.90, base, base + t)
            stroke(L, L + t, base + (cap - t) / 2, base + cap)
            stroke(L + 0.90 - t, L + 0.90, base, base + (cap - t) / 2 + t)
    # MOTORSPORTS, a fine letter-spaced rule under it
    for i in range(11):
        a = x0 + 3.50 + i * 0.42
        stroke(a, a + 0.26, base - 0.34, base - 0.16)

    # --- the M4, front three-quarter, blocked out so it reads at 40 px/ft
    cx = (x0 + x1) / 2.0
    CAR = Material("gbancar", "#b4bcc5", roughness=0.70)
    CART = Material("gbancart", "#98a2ad", roughness=0.70)
    GRIL = Material("gbangr", "#2b2e33", roughness=0.70)
    # a soft dark ground shadow first, so the car sits on the vinyl
    panel(m, Material("gbansh", "#a7aeb6", roughness=0.75), "n",
          cx - 3.75, cx + 3.75, y0 + 0.10, y0 + 0.42, off=0.055)
    panel(m, CAR, "n", cx - 3.55, cx + 3.55, y0 + 0.40, y0 + 2.15, off=0.06)
    panel(m, CART, "n", cx - 2.20, cx + 2.20, y0 + 2.15, y0 + 3.20, off=0.06)
    panel(m, Material("gbanglass", "#4e565f", roughness=0.55), "n",
          cx - 1.95, cx + 1.95, y0 + 2.25, y0 + 3.08, off=0.07)
    for dx in (-0.38, 0.38):                      # the M4 kidney grilles
        panel(m, GRIL, "n", cx + dx - 0.32, cx + dx + 0.32,
              y0 + 0.52, y0 + 1.95, off=0.08)
    for dx in (-2.50, 2.50):                      # headlights
        panel(m, GRIL, "n", cx + dx - 0.85, cx + dx + 0.85,
              y0 + 1.52, y0 + 1.92, off=0.08)
    panel(m, GRIL, "n", cx - 3.60, cx + 3.60, y0 + 0.22, y0 + 0.50, off=0.07)
    for dx in (-3.05, 3.05):                      # wheels
        panel(m, GRIL, "n", cx + dx - 0.60, cx + dx + 0.60,
              y0 + 0.02, y0 + 1.00, off=0.07)
    for dx in (-3.05, 3.05):
        panel(m, CART, "n", cx + dx - 0.30, cx + dx + 0.30,
              y0 + 0.28, y0 + 0.78, off=0.08)
    panel(m, Material("gbanplate", "#d8c23a", roughness=0.7), "n",
          cx - 0.42, cx + 0.42, y0 + 0.58, y0 + 0.88, off=0.09)
    for x in (x0 + 0.09, x1 - 0.09):              # grommet edge tape
        panel(m, TRIMS, "n", x - 0.05, x + 0.05, y0, y1, off=0.025)

    # two skateboards hung vertically between the door casing and the banner
    for (a, b) in ((2.30, 4.45), (4.65, 6.80)):
        deck = Material("gdeck%d" % int(a * 10),
                        "#c9cdd2" if a < 3 else "#e6e8ea", roughness=0.55)
        slab(m, deck, "n", 6.95, 7.42, a, b, t=0.09, off=0.02)
        for yy in (a + 0.30, b - 0.30):                        # trucks
            slab(m, BLKM, "n", 7.06, 7.31, yy - 0.10, yy + 0.10, t=0.13, off=0.11)
    # the small grey electrical panel by the door
    slab(m, GREY, "n", 7.05, 7.32, 7.55, 8.05, t=0.10, off=0.02)
    return m


# ================================================== NORTH: brooms and shelf
def brooms():
    """The mop-and-broom rail west of the service door, and the wire shelf.

    Photo 1 and photo 6: a five-hook rail at shoulder height with two mops, a
    push broom and a soft broom on it, and a white wire shelf below holding
    cleaning bottles.
    """
    m = Model()
    RAIL = Material("gbrail", "#f0efec", roughness=0.55)
    HOOK = Material("gbhook", "#5a5f63", roughness=0.45, metallic=0.4)
    HANDLE = [Material("gbh%d" % i, c, roughness=0.55)
              for i, c in enumerate(("#3557a8", "#3f9e52", "#b5b9bc", "#8fb04a"))]
    HEAD = [Material("gbd%d" % i, c, roughness=0.85)
            for i, c in enumerate(("#22242a", "#e3e2dd", "#6e737a", "#d9d3c2"))]

    bx(m, RAIL, 0.28, 3.20, 4.35, 4.60, NF, NF + 0.14)
    for i in range(5):
        x = 0.50 + i * 0.62
        bx(m, HOOK, x - 0.05, x + 0.05, 4.15, 4.38, NF + 0.02, NF + 0.24)
    # four hanging tools: a stick down to the floor, a head at the bottom
    for i, (x, hl, hw, hh) in enumerate(((0.52, 3.55, 0.55, 0.20),
                                         (1.14, 3.35, 0.42, 0.42),
                                         (1.76, 3.70, 0.75, 0.22),
                                         (2.38, 3.20, 0.50, 0.50))):
        top = 4.30
        m.add(cylinder(0.045, hl, 8), HANDLE[i], at=(x, top - hl, NF + 0.14))
        bx(m, HEAD[i], x - hw / 2, x + hw / 2, top - hl - hh, top - hl,
           NF + 0.03, NF + 0.28)
    # wire shelf with cleaning bottles
    SH = Material("gshelf", "#eceae6", roughness=0.5, metallic=0.3)
    bx(m, SH, 0.18, 2.10, 2.52, 2.60, NF, NF + 0.80)
    for x in (0.24, 2.02):
        bx(m, SH, x - 0.03, x + 0.03, 2.60, 3.05, NF + 0.70, NF + 0.78)
    bx(m, SH, 0.18, 2.10, 3.00, 3.06, NF + 0.68, NF + 0.80)
    for i, (x, r, h, c) in enumerate(((0.42, 0.14, 0.72, "#6b48a6"),
                                      (0.75, 0.12, 0.60, "#3f8f92"),
                                      (1.05, 0.15, 0.80, "#d9d5cc"),
                                      (1.40, 0.13, 0.66, "#c8b427"),
                                      (1.75, 0.14, 0.74, "#3557a8"))):
        m.add(cylinder(r, h, 10), Material("gbot%d" % i, c, roughness=0.4),
              at=(x, 2.60, NF + 0.36))
        m.add(cylinder(r * 0.45, 0.10, 8), PLASW, at=(x, 2.60 + h, NF + 0.36))
    return m


# ============================================== WEST: grey metal cabinets
def cabinets():
    """Three two-door grey steel cabinets, 8.55 ft of run.

    The floor plan draws this run at world x 19.46-21.68, z 20.41-28.90
    (garage-local x 0.56-2.78 by z 7.41-15.90) and photos 1, 2, 4 and 5 show
    what it is: matt grey two-door metal cabinets with white lever handles,
    boxes and a helmet bag stored on top.
    """
    m = Model()
    z0, dep, hh = 7.35, 2.20, 6.45
    for u in range(3):
        a = z0 + u * 2.85
        b = a + 2.80
        bx(m, GREY, 0.05, dep, 0.10, hh, a, b)                    # carcass
        bx(m, GREYD, 0.05, 0.16, 0.0, 0.10, a, b)                 # plinth
        for (c, d) in ((a + 0.05, (a + b) / 2 - 0.02),
                       ((a + b) / 2 + 0.02, b - 0.05)):           # two doors
            bx(m, GREY, dep, dep + 0.055, 0.30, hh - 0.10, c, d)
            bx(m, GREYD, dep + 0.02, dep + 0.03, 0.30, hh - 0.10,
               c - 0.015, c + 0.015)
        # white lever handles either side of the centre joint
        for dz in (-0.16, 0.16):
            bx(m, PLASW, dep + 0.055, dep + 0.20, 3.05, 3.24,
               (a + b) / 2 + dz - 0.03, (a + b) / 2 + dz + 0.03)
        bx(m, GREYD, dep, dep + 0.06, hh - 0.10, hh, a + 0.05, b - 0.05)
    # a framed KIES print taped to the middle door
    slab(m, Material("gkprint", "#e9e9e6", roughness=0.7), "w",
         z0 + 3.30, z0 + 4.35, 4.05, 5.55, t=0.05, off=dep + 0.055)
    slab(m, Material("gkprintk", "#4a4d52", roughness=0.7), "w",
         z0 + 3.50, z0 + 4.15, 4.45, 5.15, t=0.04, off=dep + 0.10)
    # stored on top: a black helmet bag, two card boxes, a spare wheel bag
    m.add(rounded_box(1.75, 0.95, 1.35, 0.28, 3), BLKM,
          at=(1.05, hh, z0 + 1.35))
    bx(m, CARD, 0.25, 1.85, hh, hh + 0.85, z0 + 3.15, z0 + 4.55)
    bx(m, CARD, 0.30, 1.70, hh + 0.85, hh + 1.45, z0 + 3.40, z0 + 4.35)
    m.add(cylinder(0.72, 0.55, 14), BLKM, at=(1.10, hh, z0 + 7.05), rot_z=R90)
    return m


# ============================================== WEST: red chest and corner
def tool_chest():
    """The red rolling tool cabinet and the SW-corner clutter.

    Photos 2, 4 and 5: a red Milwaukee roller with a black work top, standing
    between the grey cabinets and the door opening.  Photo 1's near-left corner
    adds a white storage box with the red fire extinguisher over it, a coiled
    white hose and a sack of feed on the floor.
    """
    m = Model()
    z0, z1 = 16.40, 20.20
    bx(m, RED, 0.10, 1.95, 0.30, 3.05, z0, z1)                    # carcass
    bx(m, BLKM, 0.05, 2.02, 3.05, 3.22, z0 - 0.03, z1 + 0.03)     # work top
    for i in range(4):                                            # drawer faces
        y = 0.42 + i * 0.62
        bx(m, REDD, 1.95, 2.00, y, y + 0.52, z0 + 0.06, z1 - 0.06)
        bx(m, SILV, 1.98, 2.08, y + 0.34, y + 0.44, z0 + 0.30, z1 - 0.30)
    for z in (z0 + 0.35, z1 - 0.35):                              # castors
        for x in (0.35, 1.70):
            m.add(cylinder(0.15, 0.30, 10), BLKM, at=(x, 0.0, z), rot_z=R90)
    # a red top chest sitting on the roller
    bx(m, RED, 0.15, 1.85, 3.22, 4.05, z0 + 0.20, z1 - 1.30)
    bx(m, BLKM, 0.12, 1.90, 4.05, 4.14, z0 + 0.17, z1 - 1.27)

    # SW corner: white box, extinguisher, coiled hose, feed sack
    bx(m, PLASW, 0.10, 1.65, 0.0, 1.55, 20.55, 21.35)
    bx(m, Material("gwbl", "#c9cdd0", roughness=0.5),
       0.10, 1.65, 1.35, 1.45, 20.52, 21.38)
    m.add(cylinder(0.32, 1.55, 12), Material("gext", "#a71f19", roughness=0.45),
          at=(0.55, 1.55, 20.05))
    m.add(cylinder(0.14, 0.30, 8), BLKM, at=(0.55, 3.10, 20.05))
    for i in range(6):                                            # hose coil
        m.add(torus(0.62 - i * 0.045, 0.075, 22, 6),
              Material("ghose", "#e8e6e0", roughness=0.55),
              at=(1.35, 0.09 + i * 0.13, 19.05))
    m.add(rounded_box(1.55, 0.55, 1.05, 0.22, 3),
          Material("gfeed", "#d8c98a", roughness=0.9), at=(1.20, 0.0, 17.95))
    m.add(rounded_box(1.35, 0.42, 0.90, 0.18, 3),
          Material("gfeedk", "#3d4048", roughness=0.9), at=(1.10, 0.55, 17.95))
    return m


# ================================================================ EAST: TV
def tv():
    """A 65 in flat panel and the two small framed prints north of it."""
    m = Model()
    z0, z1 = 3.35, 8.05
    slab(m, BLKM, "e", z0, z1, 4.55, 7.20, t=0.13, off=0.05)
    slab(m, BLK, "e", z0 + 0.05, z1 - 0.05, 4.60, 7.15, t=0.03, off=0.18)
    for (a, b) in ((1.95, 2.75), (2.95, 3.75)):
        slab(m, Material("gfrm", "#26282b", roughness=0.5), "e",
             a, b, 5.35, 6.45, t=0.06, off=0.03)
        slab(m, Material("gart%d" % int(a * 10),
                         "#d9c14c" if a < 2.5 else "#c8617a", roughness=0.7),
             "e", a + 0.07, b - 0.07, 5.42, 6.38, t=0.03, off=0.09)
    return m


# ========================================================== EAST: pegboard
def pegboard():
    """The black pegboard, the Liqui Moly clock and the small signage.

    Photo 1, right-hand wall, reading from the north end: a framed wave print,
    a line drawing of a car, an M badge, a PARKING ONLY sign, then the pegboard
    with its hooks and caps, with the round Liqui Moly clock above it.
    """
    m = Model()
    z0, z1, y0, y1 = 13.60, 17.60, 3.55, 6.25
    slab(m, CHAR, "e", z0, z1, y0, y1, t=0.09, off=0.03)
    slab(m, Material("gpegf", "#2c2f33", roughness=0.75), "e",
         z0 - 0.06, z1 + 0.06, y0 - 0.06, y1 + 0.06, t=0.05, off=0.03)
    # hook rows -- little dark pegs, dense enough to read as perforation
    for j in range(5):
        yy = y0 + 0.30 + j * 0.52
        for i in range(11):
            zz = z0 + 0.25 + i * 0.35
            slab(m, Material("gpeghk", "#1b1d20", roughness=0.5), "e",
                 zz, zz + 0.16, yy, yy + 0.05, t=0.10, off=0.12)
    # caps hanging on it
    for (zz, c) in ((14.15, "#1e1f22"), (14.75, "#2b2e33"), (16.55, "#23252a")):
        m.add(rounded_box(0.62, 0.36, 0.72, 0.16, 3),
              Material("gcap%d" % int(zz * 10), c, roughness=0.7),
              at=(W - 0.35, 4.55, zz), rot_y=R90)
    # tools on the pegboard
    for (zz, c, hh) in ((15.20, "#c04a2a", 0.75), (15.55, "#3f7fb0", 0.62),
                        (15.90, "#c9a227", 0.70)):
        m.add(cylinder(0.05, hh, 8), Material("gtl%d" % int(zz * 10), c,
                                              roughness=0.5),
              at=(W - 0.22, 5.05, zz))

    # Liqui Moly clock above it
    CLK = Material("gclkf", "#f0eeea", roughness=0.45)
    m.add(cylinder(0.86, 0.16, 26), CLK, at=(W - 0.12, 7.05, 15.45), rot_z=R90)
    m.add(cylinder(0.74, 0.04, 26), Material("gclkd", "#fdfdfc", roughness=0.35),
          at=(W - 0.28, 7.05, 15.45), rot_z=R90)
    slab(m, Material("gclkr", "#c0231f", roughness=0.5), "e",
         15.16, 15.74, 7.02, 7.26, t=0.03, off=0.33)
    for i in range(2):                                            # hands
        slab(m, BLK, "e", 15.45 - 0.04, 15.45 + 0.04, 7.05, 7.05 + 0.55 - i * 0.2,
             t=0.02, off=0.34)

    # signage north of the pegboard
    slab(m, Material("gsign", "#f2f1ee", roughness=0.6), "e",
         10.75, 11.55, 4.95, 5.75, t=0.04, off=0.03)
    slab(m, Material("gsignk", "#b3241d", roughness=0.6), "e",
         10.88, 11.42, 5.42, 5.58, t=0.03, off=0.08)
    slab(m, BLK, "e", 11.85, 13.05, 5.05, 5.40, t=0.04, off=0.03)   # M badge
    slab(m, Material("gline", "#e7e6e2", roughness=0.7), "e",
         11.75, 13.35, 5.60, 6.55, t=0.04, off=0.03)                # car print
    slab(m, Material("glinek", "#9aa0a6", roughness=0.7), "e",
         11.95, 13.15, 5.85, 6.30, t=0.03, off=0.08)
    slab(m, Material("gwavef", "#2a2c30", roughness=0.5), "e",      # wave print
         11.90, 13.30, 6.70, 7.55, t=0.05, off=0.03)
    slab(m, Material("gwave", "#2f6f9e", roughness=0.6), "e",
         11.98, 13.22, 6.78, 7.47, t=0.03, off=0.09)
    return m


# ============================================================ EAST: boards
def boards():
    """The snowboard, two skateboards and the mounted scooter."""
    m = Model()
    # snowboard, nose up
    slab(m, Material("gsnow", "#1c1e22", roughness=0.45), "e",
         8.35, 8.92, 2.35, 7.15, t=0.10, off=0.04)
    slab(m, Material("gsnowe", "#3a3d42", roughness=0.45), "e",
         8.42, 8.85, 2.55, 6.95, t=0.05, off=0.14)
    # skateboards
    for (z, a, b, c) in ((9.55, 2.75, 5.60, "#e9eaec"),
                         (10.30, 5.35, 7.15, "#cfd3d8")):
        slab(m, Material("gsk%d" % int(z * 10), c, roughness=0.55), "e",
             z, z + 0.52, a, b, t=0.09, off=0.04)
        slab(m, Material("gskg", "#3a4a6a", roughness=0.6), "e",
             z + 0.06, z + 0.46, a + 0.35, b - 0.35, t=0.03, off=0.13)
        for yy in (a + 0.28, b - 0.28):
            slab(m, BLKM, z + 0.12, z + 0.40, yy - 0.09, yy + 0.09,
                 wall="e", t=0.12, off=0.13) if False else \
                slab(m, BLKM, "e", z + 0.12, z + 0.40, yy - 0.09, yy + 0.09,
                     t=0.12, off=0.13)
    # scooter handlebar mounted on the wall
    SC = Material("gsc", "#b02a22", roughness=0.45, metallic=0.2)
    bx(m, SC, W - 0.55, W - 0.42, 4.85, 5.05, 10.05, 11.05)
    for z in (10.05, 11.05):
        m.add(cylinder(0.07, 0.42, 8), BLKM, at=(W - 0.48, 4.62, z))
    m.add(cylinder(0.06, 0.85, 8), Material("gscg", "#4fc9a0", roughness=0.6),
          at=(W - 0.48, 4.05, 10.55))
    return m


# ============================================================== EAST: gear
def gear():
    """Brooms leaning, hanging bags, a shovel and the cat-print towel."""
    m = Model()
    # two brooms and a shovel leaning against the wall
    for (z, c, hh, hd) in ((14.55, "#d9d6cf", 5.10, "#2a2c30"),
                           (15.05, "#c9662a", 4.70, "#b8b4ab"),
                           (15.55, "#8a6a40", 5.30, "#3a3d42")):
        m.add(cylinder(0.055, hh, 8), Material("gbr%d" % int(z * 10), c,
                                               roughness=0.55),
              at=(W - 0.55, 0.10, z), rot_x=-0.13)
        bx(m, Material("gbrh%d" % int(z * 10), hd, roughness=0.85),
           W - 1.30, W - 0.35, 0.0, 0.22, z - 0.30, z + 0.30)
    # black gear bag hanging off a wall hook
    bx(m, STEELD, W - 0.30, W - 0.08, 4.85, 5.05, 17.05, 17.45)
    m.add(rounded_box(0.75, 2.05, 1.55, 0.32, 3), BLKM,
          at=(W - 0.55, 2.75, 17.25))
    # a second, taller bag near the door end
    m.add(rounded_box(0.62, 2.60, 1.05, 0.26, 3),
          Material("ggbag", "#2b2f34", roughness=0.7), at=(W - 0.48, 0.0, 18.75))
    # cat-print towel over a rail
    bx(m, STEELD, W - 0.26, W - 0.10, 4.02, 4.14, 16.15, 16.95)
    slab(m, Material("gtow", "#efece4", roughness=0.85), "e",
         16.15, 16.95, 3.05, 4.10, t=0.06, off=0.16)
    for i, c in enumerate(("#d9534f", "#e8b83a", "#4a8fc0", "#5aa469")):
        slab(m, Material("gtowb%d" % i, c, roughness=0.85), "e",
             16.15, 16.95, 3.10 + i * 0.13, 3.18 + i * 0.13, t=0.03, off=0.23)
    return m


# ================================================== EAST floor: ride-on car
def ride_on():
    """The yellow child's ride-on, tipped up nose-first against the east wall.

    Photo 1 shows it standing on its tail leaning on the wall, not driving on
    the floor, which is why it is built along X and rolled with rot_z: the
    rotation runs before the translate, so tipping in the X-Y plane is what
    leans it INTO the east wall.
    """
    body = Model()
    bx(body, YEL, -1.85, 1.85, 0.30, 1.05, -1.00, 1.00)            # tub
    bx(body, YEL, -0.85, 0.95, 1.05, 1.55, -0.85, 0.85)            # cowl
    bx(body, BLKM, -0.90, -0.75, 1.12, 1.50, -0.80, 0.80)          # screen
    bx(body, YELD, -1.87, 1.87, 0.62, 0.72, -1.02, 1.02)           # side crease
    bx(body, BLKM, 0.10, 0.90, 1.02, 1.12, -0.62, 0.62)            # seat
    for sx in (-1.25, 1.25):
        for sz in (-0.92, 0.92):
            body.add(cylinder(0.34, 0.26, 12), BLKM, at=(sx, 0.30, sz),
                     rot_x=R90)
    for sz in (-0.70, 0.70):
        bx(body, Material("gyl", "#f6f0d0", roughness=0.35),
           1.80, 1.88, 0.80, 1.00, sz - 0.25, sz + 0.25)           # lights
    m = Model()
    for part, mat in body._parts:
        # rot_z tips it nose-up, rot_y then turns its SIDE to the room:
        # photo 1 shows both near-side wheels, not the front of the car.
        m.add(part, mat, at=(W - 1.25, 0.0, 12.25), rot_z=1.15,
              rot_y=R90)
    return m


# ========================================================== EAST: the chair
def chair():
    """White moulded shell on wooden dowel legs (photo 1)."""
    m = Model()
    cx, cz = 18.35, 3.80
    m.add(rounded_box(1.55, 0.45, 1.45, 0.30, 3), PLASW, at=(cx, 1.15, cz))
    m.add(rounded_box(1.50, 1.35, 0.42, 0.28, 3), PLASW,
          at=(cx, 1.45, cz - 0.55))
    for (dx, dz) in ((-0.55, -0.45), (0.55, -0.45), (-0.55, 0.50), (0.55, 0.50)):
        m.add(cylinder(0.055, 1.20, 8), WOOD, at=(cx + dx, 0.0, cz + dz),
              rot_x=0.10 if dz > 0 else -0.10, rot_z=0.09 * (1 if dx > 0 else -1))
    for dz in (-0.45, 0.50):
        bx(m, STEELD, cx - 0.60, cx + 0.60, 1.05, 1.13, cz + dz - 0.04,
           cz + dz + 0.04)
    # a bag of something left on the seat
    m.add(rounded_box(0.80, 0.55, 0.60, 0.16, 3),
          Material("gseatbag", "#e6dfd2", roughness=0.85), at=(cx, 1.60, cz))
    return m


# ====================================== EAST corner: speaker, plant, fan
def corner():
    """The black speaker cabinet, the artificial garland and the wall fan."""
    m = Model()
    bx(m, BLK, W - 1.75, W - 0.20, 0.0, 3.05, 1.60, 3.10)
    bx(m, Material("gspkg", "#2f3237", roughness=0.85),
       W - 1.72, W - 0.62, 0.35, 2.75, 1.55, 1.62)
    # garland / artificial plant hooked on the wall
    GRN = [Material("ggl%d" % i, c, roughness=0.85)
           for i, c in enumerate(("#3f6b3c", "#4f7c46", "#33562f", "#5d8a4e"))]
    r = Rnd(19)
    for i in range(66):
        t = i / 65.0
        y = 3.20 + t * 2.35
        rad = 0.62 * math.sin(math.pi * (0.18 + 0.82 * t)) + 0.18
        a = r.f(0, 6.283)
        m.add(rounded_box(0.36, 0.16, 0.30, 0.07, 2), GRN[i % 4],
              at=(W - 0.42 - abs(rad * math.cos(a)) - r.f(0.0, 0.20),
                  y + r.f(-0.14, 0.14), 1.55 + rad * math.sin(a)),
              rot_y=a, rot_z=r.f(-0.5, 0.5))
    for i in range(10):                                       # red berries
        t = i / 9.0
        m.add(cylinder(0.09, 0.09, 8), Material("gberry", "#a5302a",
                                                roughness=0.5),
              at=(W - 0.70 - r.f(0, 0.2), 3.35 + t * 2.05,
                  1.55 + r.f(-0.5, 0.5)))
    # wall fan
    m.add(cylinder(0.72, 0.30, 18), Material("gfanc", "#c7cacd", roughness=0.35,
                                             metallic=0.5),
          at=(W - 0.62, 6.35, 1.15), rot_z=R90)
    m.add(cylinder(0.66, 0.06, 18), Material("gfang", "#9aa0a5", roughness=0.4,
                                             metallic=0.5),
          at=(W - 0.98, 6.35, 1.15), rot_z=R90)
    bx(m, STEELD, W - 0.30, W - 0.05, 5.95, 6.75, 1.05, 1.25)
    return m


# ================================================== NORTH floor: the stack
def paper():
    """The toilet-roll packs and the Scott box stacked beside the steps."""
    m = Model()
    WRAP = Material("gwrap", "#eef1f4", roughness=0.45)
    BLUE_W = Material("gwrapb", "#2f5f96", roughness=0.45)
    for (x, z, h) in ((7.05, 1.35, 1.15), (7.05, 2.20, 1.15), (7.90, 1.75, 1.15)):
        m.add(rounded_box(0.85, h, 0.80, 0.16, 3), WRAP, at=(x, 0.0, z))
        m.add(rounded_box(0.87, 0.22, 0.82, 0.16, 3), BLUE_W, at=(x, 0.42, z))
    m.add(rounded_box(0.90, 0.62, 0.72, 0.08, 2),
          Material("gscott", "#d9dde2", roughness=0.6), at=(7.45, 1.15, 1.75))
    m.add(rounded_box(0.62, 0.24, 0.50, 0.06, 2), BLUE_W, at=(7.45, 1.77, 1.75))
    return m


PIECES = [
    ("Garage Banner", banner),
    ("Garage Brooms", brooms),
    ("Garage Cabinets", cabinets),
    ("Garage Tool Chest", tool_chest),
    ("Garage TV", tv),
    ("Garage Pegboard", pegboard),
    ("Garage Boards", boards),
    ("Garage Gear", gear),
    ("Garage Ride On Car", ride_on),
    ("Garage Chair", chair),
    ("Garage Speaker", corner),
    ("Garage Paper Stack", paper),
]

if __name__ == "__main__":
    ON_FLOOR = {"Garage Ride On Car", "Garage Chair", "Garage Tool Chest"}
    tot = 0.0
    for name, fn in PIECES:
        tot += save_and_place(name, fn(), on_floor=name in ON_FLOOR)["kb"]
    print("  furniture total %.1f KB" % tot)
