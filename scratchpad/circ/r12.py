"""Room 12 -- First floor hallway + entry (7.6 x 27.6 x 9.0), level 1.

ORIENTATION (derived before anything was modelled -- see the report):
  * Room rect world x 10.70..18.30, z 4.60..32.20.  Adjacencies from
    `roomkit.rooms --list`: Living Room (5) is NORTH across z=4.60, Kitchen (6)
    is WEST over z 4.74..21.48 and Dining (4) is WEST over z 21.70..32.20,
    Garage (7) / Pantry (10) are EAST, and nothing sits south of z=32.2 -- so
    the SOUTH wall is the front facade and carries the FRONT DOOR.
  * The live `stairs` row on floor 2 is x 14.6..18.4, z 14.3..24.5,
    direction 'n': the flight is in the EAST half of this room and ascends
    NORTH.  Registering docs/floor plan/Main Floor Plan App.png to world feet
    (scratchpad/circ/planmap.py) puts the drawn tread hatch at x 14.44..18.49,
    z 14.46..24.48 -- the same rectangle to 0.2 ft, which independently
    confirms both the registration and the stair row.
  * So the primary photo ('First floor hallway.jpg'), which looks down the hall
    with the flight rising away on the RIGHT and a slider to the green
    BACKyard at the far end, is shot from the SOUTH looking NORTH:
    left = WEST, right = EAST.

OPENINGS -- all real cuts.  Spans from the registered plan (wallscan.py), with
the neighbours' existing cuts read out of the DB and matched:
    north  passage  world x 12.08..16.08 == room 5's opening id 32 EXACTLY
    west   passage  world z 16.29..19.69 == room 6's opening id  8 EXACTLY
    west   passage  world z 19.95..22.55 -- the 6-panel door photos 1 and 2 put
                    between the dining opening and the kitchen opening
    west   passage  world z 24.90..31.15 -- to Dining (plan gap 25.05..32.40;
                    room 4's own cut is z 22.70..28.30, overlapping 24.90..28.30)
    south  passage  world x 13.10..16.00 -- the front door (plan gap 13.15..16.00)
    south  window   x2  -- the sidelights either side of it
"""

import math
from ckit import *                                             # noqa: F401,F403
from ckit import save_and_place, openings, wall_skin, raked, blit, \
    stair_dress, plant_stand, leafy

ROOM, W, D, H = 12, 7.6, 27.6, 9.0

# ---- openings, in room-local feet -----------------------------------------
LR = (1.38, 5.38)            # north wall, local x   (== room 5 id 32)
KIT = (11.69, 15.09)         # west wall, local z    (== room 6 id 8)
CLOSET = (15.35, 17.95)      # west wall, local z    -- the 6-panel door
DIN = (20.30, 26.55)         # west wall, local z    -- to the Dining room
FRONT = (2.40, 5.30)         # south wall, local x   -- the front door
SL_W = (1.35, 2.15)          # south wall, local x   -- west sidelight
SL_E = (5.55, 6.35)          # south wall, local x   -- east sidelight
SL_Y = (0.60, 7.05)          # sidelight sill / head
DOOR_TOP_F = 7.05
PASS_TOP = 7.20

# ---- the app's own stair mesh (house.js buildStairs), in room-local feet ---
ST_X0, ST_X1 = 3.90, 7.70
ST_ZBOT, ST_ZTOP = 19.90, 9.70
ST_STEPS, ST_RISE = 17, 10.0
RAKE = ST_RISE / (ST_ZBOT - ST_ZTOP)


def stair_y(z):
    return max(0.0, min(ST_RISE, (ST_ZBOT - z) * RAKE))


# ---------------------------------------------------------------- materials
GREYWD = Material("h12tread", "#4a4844", roughness=0.72)
RUNNERG = Material("h12runner", "#5e5c58", roughness=0.98)
PLANK = [Material("h12pl%d" % i, c, roughness=0.90) for i, c in enumerate(
    ("#2b2a29", "#343333", "#3b3a38", "#434240", "#494844", "#32312f",
     "#3c3b39", "#363533"))]
RAILBLK = Material("h12rail", "#1e1f24", roughness=0.42, metallic=0.15)
JUTE = Material("h12jute", "#cfc8ba", roughness=0.98)
JUTE2 = Material("h12jute2", "#c1b9a9", roughness=0.98)
CREAM = Material("h12cream", "#d9d3ca", roughness=0.66)
CREAM2 = Material("h12cream2", "#e2ddd5", roughness=0.62)
CHEV = Material("h12chev", "#cfc8be", roughness=0.70)
POT = Material("h12pot", "#eeece7", roughness=0.55)
LEAFA = Material("h12leafa", "#5d7055", roughness=0.88)
LEAFB = Material("h12leafb", "#7e9070", roughness=0.88)
LEAFC = Material("h12leafc", "#48583f", roughness=0.86)
STEM = Material("h12stem", "#6b7a5c", roughness=0.90)
BEAD = Material("h12bead", "#d5c2a6", roughness=0.80)
DRIED = Material("h12dried", "#c9b393", roughness=0.90)
SAGE = Material("h12sage", "#93a08a", roughness=0.90)
KRAFT = Material("h12kraft", "#c0a781", roughness=0.92)
PAPER = Material("h12paper", "#eae7e0", roughness=0.90)
GRIL = Material("h12gril", "#f2f1ee", roughness=0.55)
GRILD = Material("h12grild", "#9a9a97", roughness=0.70)


# ================================================================= 1 ceiling
def piece_ceiling():
    m = ceiling(
        W, D, H,
        # Open to the stairwell above, but only over the stretch where the
        # flight and its handrail actually break the 9 ft ceiling plane
        # (nosing + 2.6 ft rail clears 8.99 ft only north of local z 13.8).
        # The shell pass cut the hole all the way back to z 20.05, which in
        # single-floor view left a raw navy void over half the hall.
        hole=(3.78, W, 9.55, 14.20),
        cans=[(1.90, 20.40), (1.90, 16.40), (1.90, 12.40),
              (3.80, 7.10), (3.80, 3.20)],
        fixtures=[(3.80, 24.70, 0.62)],
        vents=[(1.15, 22.20, 0.52, 0.95)])
    disc_down(m, Material("h12smoke", "#f2f1ee", roughness=0.6),
              3.30, 22.60, H - 0.10, 0.27)
    m.add(cylinder(0.27, 0.09, 16), Material("h12smoke2", "#eceae6",
          roughness=0.6), at=(3.30, H - 0.11, 22.60))
    return m


# =============================================== 2 skirting, casings, leaves
def front_door_unit(m):
    """The 6-panel front door with a sidelight either side (entry photos).

    The leaf fills the `passage` cut, so nothing else is in the hole; the
    sidelights are `window` cuts and get the app's own glass, so this adds only
    their casing, stool and muntins.
    """
    sub = Model()
    a0, a1 = FRONT
    for a, b in ((a0 - 0.09, a0), (a1, a1 + 0.09)):
        bx(sub, TRIM, a, b, 0.0, DOOR_TOP_F, 0.0, 0.34)
    bx(sub, TRIM, a0 - 0.09, a1 + 0.09, DOOR_TOP_F, DOOR_TOP_F + 0.09, 0.0, 0.34)
    panel_door(sub, WHITEWD, a0 + 0.02, a1 - 0.02, 0.02, DOOR_TOP_F - 0.03,
               0.10, 0.26, rows=3)
    sub.add(cylinder(0.085, 0.055, 12), BLACKMET,
            at=(a1 - 0.34, 3.05, 0.30), rot_x=R(90))
    bx(sub, BLACKMET, a1 - 0.44, a1 - 0.28, 2.96, 3.06, 0.30, 0.46)
    bx(sub, BLACKMET, a1 - 0.36, a1 - 0.24, 3.60, 3.78, 0.24, 0.32)
    for (s0, s1) in (SL_W, SL_E):
        for a, b in ((s0 - 0.26, s0), (s1, s1 + 0.26)):
            bx(sub, TRIM, a, b, SL_Y[0] - 0.30, SL_Y[1] + 0.26, 0.0, 0.16)
        bx(sub, TRIM, s0 - 0.26, s1 + 0.26, SL_Y[1], SL_Y[1] + 0.26, 0.0, 0.16)
        bx(sub, TRIM, s0 - 0.26, s1 + 0.26, 0.0, SL_Y[0], 0.0, 0.16)
        for k in range(5):
            y = SL_Y[0] + (k + 1) * (SL_Y[1] - SL_Y[0]) / 6
            bx(sub, TRIM, s0, s1, y - 0.022, y + 0.022, 0.05, 0.09)
    bx(sub, TRIM, SL_W[0] - 0.30, SL_E[1] + 0.30, DOOR_TOP_F + 0.09,
       DOOR_TOP_F + 0.40, 0.0, 0.20)
    blit(m, sub, "s", W, D, 0.0)


def closet_door_unit(m):
    sub = Model()
    a0, a1 = CLOSET
    for a, b in ((a0 - 0.08, a0), (a1, a1 + 0.08)):
        bx(sub, TRIM, a, b, 0.0, DOOR_TOP, 0.0, 0.30)
    bx(sub, TRIM, a0 - 0.08, a1 + 0.08, DOOR_TOP, DOOR_TOP + 0.08, 0.0, 0.30)
    panel_door(sub, WHITEWD, a0 + 0.02, a1 - 0.02, 0.02, DOOR_TOP - 0.03,
               0.08, 0.22, rows=3)
    sub.add(cylinder(0.080, 0.05, 12), BLACKMET, at=(a0 + 0.30, 3.05, 0.27),
            rot_x=R(90))
    bx(sub, BLACKMET, a0 + 0.22, a0 + 0.38, 2.97, 3.06, 0.27, 0.44)
    for a, b in ((a0 - 0.08 - CASE_W, a0 - 0.06), (a1 + 0.06, a1 + 0.08 + CASE_W)):
        bx(sub, TRIM, a, b, 0.0, DOOR_TOP + CASE_W, 0.0, 0.10)
    bx(sub, TRIM, a0 - 0.08 - CASE_W, a1 + 0.08 + CASE_W, DOOR_TOP + 0.08,
       DOOR_TOP + CASE_W, 0.0, 0.10)
    blit(m, sub, "w", W, D, 0.0)


def piece_baseboards():
    m = baseboards(W, D, doors=[("n", *LR),
                                ("w", *KIT), ("w", *CLOSET), ("w", *DIN),
                                ("s", SL_W[0], SL_E[1])])
    sub = Model()
    for a, b in ((LR[0] - CASE_W, LR[0] + 0.03), (LR[1] - 0.03, LR[1] + CASE_W)):
        bx(sub, TRIM, a, b, 0.0, PASS_TOP + CASE_W, 0.0, 0.20)
    bx(sub, TRIM, LR[0] - CASE_W, LR[1] + CASE_W, PASS_TOP, PASS_TOP + CASE_W,
       0.0, 0.20)
    blit(m, sub, "n", W, D, 0.0)

    for (a0, a1) in (KIT, DIN):
        sub = Model()
        for a, b in ((a0 - CASE_W, a0 + 0.03), (a1 - 0.03, a1 + CASE_W)):
            bx(sub, TRIM, a, b, 0.0, PASS_TOP + CASE_W, 0.0, 0.20)
        bx(sub, TRIM, a0 - CASE_W, a1 + CASE_W, PASS_TOP, PASS_TOP + CASE_W,
           0.0, 0.20)
        # jamb lining set into the cut so the wall's zero thickness never shows
        bx(sub, TRIM, a0 - 0.04, a0 + 0.03, 0.0, PASS_TOP, -0.14, 0.02)
        bx(sub, TRIM, a1 - 0.03, a1 + 0.04, 0.0, PASS_TOP, -0.14, 0.02)
        bx(sub, TRIM, a0 - 0.04, a1 + 0.04, PASS_TOP - 0.07, PASS_TOP,
           -0.14, 0.02)
        blit(m, sub, "w", W, D, 0.0)

    closet_door_unit(m)
    front_door_unit(m)

    # white floor register in the plank, west side (photo 1)
    rx, rz = 1.25, 17.00
    bx(m, GRIL, rx - 0.50, rx + 0.50, 0.030, 0.044, rz - 0.30, rz + 0.30)
    for k in range(9):
        z = rz - 0.24 + k * 0.06
        bx(m, GRILD, rx - 0.44, rx + 0.44, 0.044, 0.048, z, z + 0.030)
    # high wall return-air grille on the WEST wall (photo 1, top left), in the
    # pier between the closet door and the dining opening.  Kept nearly flush --
    # the first pass stood it 0.34 ft off the wall and it read as a black louvre
    # box hanging in the hall.
    gz0, gz1 = 18.35, 19.85
    bx(m, GRIL, 0.02, 0.13, 6.62, 7.44, gz0, gz1)
    for k in range(6):
        y = 6.70 + k * 0.125
        bx(m, GRILD, 0.13, 0.155, y, y + 0.055, gz0 + 0.05, gz1 - 0.05)
    # thresholds: the hall's west wall and its neighbours' walls are 0.02-0.25 ft
    # apart, and through a cut opening that gap shows as a dark slot between the
    # two slabs.  A saddle board bridges it.
    for (a0, a1) in (KIT, DIN):
        bx(m, GREYWD, -0.28, 0.10, 0.010, 0.052, a0 + 0.02, a1 - 0.02)
    return m


# ==================================================== 3 the staircase itself
def piece_stair():
    """Treads, risers, the carpet runner and the closed white stringer laid
    over house.js's own stepped stair box, which renders flat blue-grey."""
    m = Model()
    dx0, dx1 = ST_X0 + 0.02, 7.58
    stair_dress(m, dx0, dx1, ST_ZBOT, ST_ZTOP, ST_STEPS, ST_RISE,
                GREYWD, TRIM, runner_mat=RUNNERG, runner_w=2.30, nose=0.075,
                skirt=("e", 0.10, 0.92))
    # closed stringer: the whole west face of the flight, floor to nosing line
    y0 = ST_RISE / ST_STEPS
    x = ST_X0 - 0.05
    m.add(quad((x, 0.0, ST_ZBOT + 0.03), (x, y0, ST_ZBOT + 0.03),
               (x, ST_RISE, ST_ZTOP), (x, 0.0, ST_ZTOP)), TRIM)
    # its raked skirt board, proud of that face
    raked(m, TRIM, x - 0.09, x, ST_ZBOT, ST_ZTOP, y0 + 0.06, ST_RISE + 0.06,
          0.86, extend=0.28, sink=0.36)
    return m


# ======================================================== 4 the balustrade
def piece_balustrade():
    """Square white newel with a black cap, turned white balusters and ONE
    continuous black handrail raked up the flight (photos 1, 2 and 4).  The
    shell pass drew the rail as 34 separate blocks; this is a single swept bar.
    """
    m = Model()
    x = ST_X0 - 0.09
    y0 = ST_RISE / ST_STEPS
    rail_h = 2.60

    def ny(z):
        return max(y0, stair_y(z))

    nz = ST_ZBOT - 0.05
    bx(m, TRIM, x - 0.26, x + 0.06, 0.0, 3.02, nz - 0.16, nz + 0.16)
    bx(m, TRIM, x - 0.30, x + 0.10, 3.02, 3.13, nz - 0.20, nz + 0.20)
    bx(m, RAILBLK, x - 0.32, x + 0.12, 3.13, 3.49, nz - 0.22, nz + 0.22)
    m.add(cylinder(0.085, 0.10, 10), RAILBLK, at=(x - 0.10, 3.49, nz))

    z = ST_ZBOT - 0.46
    while z > ST_ZTOP + 0.25:
        y = ny(z)
        m.add(cylinder(0.048, rail_h, 8), TRIM, at=(x - 0.10, y, z))
        m.add(cylinder(0.082, 0.36, 8), TRIM, at=(x - 0.10, y + 0.32, z))
        m.add(cylinder(0.072, 0.26, 8), TRIM, at=(x - 0.10, y + 1.30, z))
        m.add(cylinder(0.062, 0.18, 8), TRIM, at=(x - 0.10, y + 2.26, z))
        z -= 0.40

    raked(m, RAILBLK, x - 0.26, x + 0.06, nz, ST_ZTOP - 0.10,
          y0 + rail_h + 0.10, ST_RISE + rail_h + 0.10, 0.23, extend=0.10)
    raked(m, RAILBLK, x - 0.21, x + 0.01, nz, ST_ZTOP - 0.10,
          y0 + rail_h - 0.05, ST_RISE + rail_h - 0.05, 0.13, extend=0.08)
    return m


# ============================================ 5 the entry console + styling
CZ = 23.60                        # credenza centre, local z


def piece_console():
    """The cream two-door credenza on black legs against the EAST wall of the
    entry, with what is standing on it (both entry photos)."""
    m = Model()
    hw, dep = 2.05, 1.30
    z0, z1 = CZ - hw, CZ + hw
    x1 = W - 0.10
    x0 = x1 - dep
    contact_shadow(m, (x0 + x1) / 2 + 0.20, CZ, 1.00, hw + 0.50, y=0.078,
                   strength=0.46, room=(W, D))
    for lz in (z0 + 0.16, z1 - 0.16):
        for lx in (x0 + 0.12, x1 - 0.10):
            bx(m, BLACKMET, lx - 0.035, lx + 0.035, 0.0, 0.62,
               lz - 0.035, lz + 0.035)
        bx(m, BLACKMET, x0 + 0.09, x1 - 0.07, 0.56, 0.62, lz - 0.030, lz + 0.030)
    bx(m, CREAM, x0, x1, 0.62, 2.62, z0, z1)
    bx(m, CREAM2, x0 - 0.03, x1, 2.62, 2.72, z0 - 0.03, z1 + 0.03)
    for k, (d0, d1) in enumerate(((z0 + 0.06, CZ - 0.03), (CZ + 0.03, z1 - 0.06))):
        bx(m, CREAM2, x0 - 0.035, x0, 0.70, 2.55, d0, d1)
        for j in range(4):
            zz = d0 + 0.16 + j * (d1 - d0 - 0.32) / 3
            bx(m, CHEV, x0 - 0.040, x0 - 0.036, 0.86, 2.40, zz - 0.010, zz + 0.010)
        pz = d1 - 0.10 if k == 0 else d0 + 0.10
        bx(m, BLACKMET, x0 - 0.10, x0 - 0.05, 0.95, 2.35, pz - 0.025, pz + 0.025)
    bx(m, Material("h12tray", "#2b2c30", roughness=0.6),
       x0 + 0.14, x1 - 0.20, 2.72, 2.98, z0 + 0.20, z0 + 1.00)
    bx(m, KRAFT, x0 + 0.18, x1 - 0.34, 2.72, 3.30, CZ - 0.30, CZ + 0.22)
    bx(m, PAPER, x0 + 0.30, x1 - 0.18, 2.72, 2.80, z0 + 1.10, z0 + 1.70)
    bx(m, Material("h12pink", "#d76a90", roughness=0.85),
       x0 + 0.34, x0 + 0.62, 2.80, 3.36, z0 + 1.18, z0 + 1.24)
    bx(m, KRAFT, x0 + 0.22, x1 - 0.28, 2.72, 3.02, z1 - 0.95, z1 - 0.45)
    m.add(cylinder(0.24, 0.30, 12), POT, at=(x1 - 0.60, 2.72, z1 - 0.30))
    leafy(m, x1 - 0.60, 3.02, z1 - 0.30, 0.42, 0.85, LEAFB, n=7, seed=31,
          leaf=0.26)
    m.add(cylinder(0.20, 0.26, 12), POT, at=(x1 - 0.66, 2.72, z0 + 0.34))
    leafy(m, x1 - 0.66, 2.98, z0 + 0.34, 0.55, 0.62, LEAFA, n=8, seed=12,
          leaf=0.30)
    for sz in (z0 + 0.55, z0 + 0.95):
        bx(m, Material("h12shoe", "#e6e4e0", roughness=0.8),
           x0 + 0.30, x0 + 1.05, 0.0, 0.32, sz, sz + 0.30)
    return m


def piece_wreath():
    """The beaded ring with dried florals over the credenza (entry photos)."""
    m = Model()
    x = W - 0.07
    cz, cy, r = CZ + 0.25, 5.50, 0.86
    n = 30
    for i in range(n):
        a = 2 * math.pi * i / n
        m.add(cylinder(0.075, 0.11, 7), BEAD,
              at=(x - 0.055, cy + r * math.sin(a), cz + r * math.cos(a)),
              rot_z=R(90))
    rn = Rnd(4711)
    for i in range(24):
        a = math.pi * 1.15 + rn.f(-0.85, 0.85)
        L = rn.f(0.35, 0.80)
        z = cz + (r - 0.08) * math.cos(a)
        y = cy + (r - 0.08) * math.sin(a)
        mat = (DRIED, SAGE, BEAD)[i % 3]
        m.add(box(0.10, L, 0.17, anchor="center"), mat,
              at=(x - 0.12, y - L * 0.18, z),
              rot_x=R(rn.f(-40, 40)), rot_z=R(rn.f(-30, 30)))
    for i in range(14):
        a = math.pi * 1.20 + rn.f(-1.1, 1.1)
        z = cz + (r + rn.f(-0.32, 0.36)) * math.cos(a)
        y = cy + (r + rn.f(-0.32, 0.36)) * math.sin(a)
        m.add(cylinder(rn.f(0.10, 0.17), 0.035, 9), LEAFB,
              at=(x - 0.10, y, z), rot_z=R(90))
    return m


def blade(m, mat, cx, cy, cz, ang, lean, h, w):
    """One upright sword leaf: a tapered strip leaning out of the pot."""
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


def piece_plants():
    """The snake plant and the rubber plant on black wire stands flanking the
    front door in both entry photos."""
    m = Model()
    # --- snake plant, EAST of the door assembly (photo left) ---------------
    sx, sz = 6.60, D - 1.30
    contact_shadow(m, sx, sz, 0.85, 0.85, y=0.078, strength=0.46, room=(W, D))
    plant_stand(m, sx, sz, 0.55, 1.55, BLACKMET)
    m.add(cylinder(0.52, 0.92, 16, r_top=0.46), POT, at=(sx, 1.55, sz))
    rn = Rnd(505)
    for i in range(13):
        a = 2 * math.pi * i / 13 + rn.f(-0.2, 0.2)
        blade(m, (LEAFC if i % 3 else LEAFA), sx + 0.16 * math.cos(a), 2.40,
              sz + 0.16 * math.sin(a), a, rn.f(0.22, 0.62),
              rn.f(1.85, 3.10), rn.f(0.20, 0.30))
    # --- rubber plant, WEST of the door (photo right, big glossy leaves) ---
    rx, rz = 1.15, D - 1.15
    contact_shadow(m, rx, rz, 1.05, 1.05, y=0.078, strength=0.48, room=(W, D))
    plant_stand(m, rx, rz, 0.62, 1.30, BLACKMET)
    m.add(cylinder(0.62, 0.80, 18, r_top=0.55), POT, at=(rx, 1.30, rz))
    m.add(cylinder(0.052, 3.20, 6), STEM, at=(rx + 0.04, 2.05, rz + 0.02))
    m.add(cylinder(0.042, 2.30, 6), STEM, at=(rx - 0.16, 2.05, rz - 0.10),
          rot_z=R(-9))
    rn = Rnd(88)
    for i in range(16):
        t = i / 15.0
        y = 2.35 + 0.35 + t * 2.65
        a = 2.1 * i + rn.f(-0.3, 0.3)
        reach = 0.55 + 0.42 * (1.0 - abs(t - 0.45))
        lx = rx + 0.04 + reach * math.cos(a)
        lz = rz + 0.02 + reach * math.sin(a)
        m.add(cylinder(0.024, reach, 5), STEM,
              at=(rx + 0.04, y, rz + 0.02), rot_z=R(78 * math.cos(a) - 90),
              rot_x=R(78 * math.sin(a)))
        leaf = rounded_box(0.52, 0.055, 0.86, r=0.20, seg=3, anchor="center")
        m.add(leaf, (LEAFC if i % 2 else LEAFA), at=(lx, y - 0.10, lz),
              rot_y=R(math.degrees(a)), rot_z=R(rn.f(-22, 10)),
              rot_x=R(rn.f(-18, 18)))
    return m


def piece_floor_planks():
    """A real plank field over the slab.

    The app's 'wood' slab texture meters sd 2.9 against the photo's 13.6-15.2,
    which is why the hall floor read as a flat grey sheet.  This is 14 plank
    columns of randomised butt lengths, one quad each, each carrying its own
    albedo -- ~170 triangles for the whole 7.6 x 27.6 ft floor.
    """
    m = Model()
    rn = Rnd(9021)
    pw = W / 13.0
    for c in range(13):
        x0 = c * pw
        z = -1.0
        k = c
        while z < D:
            L = rn.f(3.4, 7.6)
            z1 = min(D, z + L)
            if z1 > 0.0:
                mat = PLANK[int(rn.f(0, 7.99))]
                rect_up(m, mat, x0 + 0.012, x0 + pw - 0.012, 0.014,
                        max(0.0, z) + 0.014, z1 - 0.014)
            z = z1
            k += 1
    return m


# ================================================================ 6 runner
def piece_runner():
    m = Model()
    x0, x1, z0, z1 = 0.70, 3.30, 1.30, 8.60   # sits on top of the plank field
    contact_shadow(m, (x0 + x1) / 2, (z0 + z1) / 2, 1.45, 3.55, y=0.078,
                   strength=0.44, room=(W, D))
    bx(m, JUTE, x0, x1, 0.024, 0.064, z0, z1)
    for i in range(int((z1 - z0) / 0.34)):
        z = z0 + 0.07 + i * 0.34
        bx(m, JUTE2, x0 + 0.05, x1 - 0.05, 0.064, 0.074, z, z + 0.16)
    return m


# ============================================================== 7 wall skins
def piece_skins(colors):
    m = Model()
    top = H - CROWN_H + 0.04
    bot = BB_H - 0.03
    holes = {
        "n": [(LR[0] - 0.34, LR[1] + 0.34, 0.0, PASS_TOP + 0.34)],
        "w": [(KIT[0] - 0.34, KIT[1] + 0.34, 0.0, PASS_TOP + 0.34),
              (CLOSET[0] - 0.42, CLOSET[1] + 0.42, 0.0, DOOR_TOP + 0.42),
              (DIN[0] - 0.34, DIN[1] + 0.34, 0.0, PASS_TOP + 0.34)],
        "s": [(SL_W[0] - 0.34, SL_E[1] + 0.34, 0.0, DOOR_TOP_F + 0.46)],
        "e": [],
    }
    for wall in "nswe":
        wall_skin(m, wall, W, D, colors[wall], bot, top, holes[wall])
    return m


# ===================================================================== main
# Fitted from the two-point probes p1 (#d3d3d1) / p2 (#9a9a98) measured off
# real renders -- see the report.  b and k per wall, then L solved for target.
#   w  198.0 / 154.0 -> b 0.797  target 190 -> albedo luma 200
#   e  164.7 / 114.6 -> b 1.151  target 200 -> albedo luma 250
#   n  232.0 / 208.1 -> b 0.345  target 196 -> albedo luma 129
#   s  138.4 /  89.5 -> b 1.383  target 196 needs luma 271 -- IMPOSSIBLE.
#      The south wall is the one the sun never reaches; pure white caps it at
#      180, which is the renderer's residue ROOM-BRIEF warns about.
SKINS = {"n": "#8a8a8c", "s": "#ffffff", "e": "#ffffff", "w": "#c8c8ca"}

WANT_OPENINGS = [
    ("passage", 0, LR[0], LR[1] - LR[0], 0.0, 7.00),
    ("passage", 3, D - KIT[1], KIT[1] - KIT[0], 0.0, PASS_TOP),
    ("passage", 3, D - CLOSET[1], CLOSET[1] - CLOSET[0], 0.0, DOOR_TOP),
    ("passage", 3, D - DIN[1], DIN[1] - DIN[0], 0.0, PASS_TOP),
    ("passage", 2, W - FRONT[1], FRONT[1] - FRONT[0], 0.0, DOOR_TOP_F),
    ("window", 2, W - SL_W[1], SL_W[1] - SL_W[0], SL_Y[0], SL_Y[1] - SL_Y[0]),
    ("window", 2, W - SL_E[1], SL_E[1] - SL_E[0], SL_Y[0], SL_Y[1] - SL_Y[0]),
]

PIECES = {
    "ceiling": ("Hall1F Ceiling", piece_ceiling),
    "base": ("Hall1F Baseboards", piece_baseboards),
    "stair": ("Hall1F Stair Treads", piece_stair),
    "rail": ("Hall1F Balustrade", piece_balustrade),
    "console": ("Hall1F Entry Console", piece_console),
    "wreath": ("Hall1F Entry Wreath", piece_wreath),
    "plants": ("Hall1F Entry Plants", piece_plants),
    "runner": ("Hall1F Floor Runner", piece_runner),
    "planks": ("Hall1F Floor Planks", piece_floor_planks),
}


def main(only=None):
    print("room 12 First floor hallway")
    if only in (None, "surf"):
        surfaces(ROOM, wall_color="#dcdcdb", floor_color="#565452",
                 floor_texture="wood")
        openings(ROOM, WANT_OPENINGS)
    for k, (name, fn) in PIECES.items():
        if only in (None, k):
            save_and_place(name, fn(), ROOM)
    if only in (None, "skins"):
        save_and_place("Hall1F Wall Wash Skins", piece_skins(SKINS), ROOM)


if __name__ == "__main__":
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else None)
