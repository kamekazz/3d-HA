"""Room 1 -- Movie Room, 17.0 (x, W-E) x 23.5 (z, N-S) x 8.0 ft.

ORIENTATION (derived, see the build report):
  north wall z=0   shared with the Arcade Room -- the big black screen, the grey
                   media console, two black subs, and the door to the Arcade at
                   local x 13.35-16.05 (the plan's wall gap, world x 11.4-14.1)
  west  wall x=0   exterior -- the L-sectional, the five-panel art above it, and
                   the high basement window
  east  wall x=17  solid over z 0-16.6 (the stair runs behind it, world x
                   15.1-18.4 / z 15.2-27.6 = local z 3.8-16.2); OPEN over
                   z 16.6-23.5, which is the foot of that stair
  south wall z=23.5 exterior front wall, behind the camera in the photo

Everything is idempotent by piece name.  Run:  python mv.py
"""

import json
import urllib.request

from bkit import *          # noqa: F401,F403

ROOM, W, D, H = 1, 17.0, 23.5, 8.0
BASE = "http://127.0.0.1:5000"

DOOR = (13.35, 16.05)          # north wall, local x -- the plan's wall gap
WIN = (5.40, 9.00)             # west wall, local z
WIN_SILL, WIN_HEAD = 5.50, 7.35
STAIR = (16.60, 23.50)         # east wall, local z -- the stairwell opening
RAIL_Y = 3.35                  # chair rail top


# ----------------------------------------------------------------- palette
# sRGB picked off 'Movie room.jpg'; mid-tone verticals render ~1.25x their
# authored value in this scene, so fabrics are authored a little under the
# photo's metered luminance.
FAB = Material("mvfab", "#bdbab4", roughness=0.95)          # greige upholstery
FAB_D = Material("mvfabd", "#a9a6a1", roughness=0.95)       # its shaded return
BACKC = Material("mvbackc", "#5e6164", roughness=0.95)      # charcoal back cushions
SLATE = Material("mvslate", "#7d8f98", roughness=0.95)      # slate-blue pillows
BOUCLE = Material("mvbou", "#d6d1c6", roughness=1.0)        # cream boucle pillow
PATT_A = Material("mvpa", "#3d4a52", roughness=0.95)        # geometric pillow, dark
PATT_B = Material("mvpb", "#cfd2cf", roughness=0.95)        # geometric pillow, light
IVORY = Material("mviv", "#cfcbc2", roughness=0.95)         # swivel chairs
DKWOOD = Material("mvdw", "#2f2a27", roughness=0.6)         # furniture feet
BLK = Material("mvblk", "#0d0e11", roughness=0.30)          # screen
BEZ = Material("mvbez", "#232427", roughness=0.45)
BOXBLK = Material("mvbox", "#18191c", roughness=0.55)       # subwoofers
GREYWD = Material("mvgw", "#8d8b86", roughness=0.62)        # console doors
GREYWD2 = Material("mvgw2", "#7e7c78", roughness=0.64)
WHTOP = Material("mvwt", "#e6e4de", roughness=0.45)         # console white top
SPKR = Material("mvspk", "#dedbd4", roughness=0.85)         # in-wall speaker cloth
GREEN = Material("mvgrn", "#4b6b4a", roughness=0.9)
POT = Material("mvpot", "#1d1e20", roughness=0.6)
ARTINK = Material("mvart", "#4e5a64", roughness=0.85)       # the print's mid tone
ARTDK = Material("mvartd", "#232b33", roughness=0.85)
ARTLT = Material("mvartl", "#9aa5ac", roughness=0.85)
LAMPBLK = Material("mvlb", "#17181a", roughness=0.5)
LAMPSHD = Material("mvls", "#1c1d20", roughness=0.85)
TBLWOOD = Material("mvtw", "#4a423b", roughness=0.7)
FANW = Material("mvfw", "#e9e7e2", roughness=0.5)
STUD = Material("mvstud", "#8e9295", roughness=0.35, metallic=0.45)


def api(method, path, payload):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(BASE + path, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode()


# ================================================================= openings
def openings():
    """Real cut openings: the door to the Arcade, the basement window, and the
    stairwell.  The shell pass drew a door leaf at 13.4-16.1 but the DB hole was
    at 11.03-14.03 -- the plan's wall gap (world x 11.4-14.1) says the leaf was
    right and the hole was wrong."""
    with urllib.request.urlopen(f"{BASE}/api/house", timeout=30) as r:
        house = json.loads(r.read().decode())
    room = next(rm for f in house["floors"] for rm in f["rooms"] if rm["id"] == ROOM)
    have = {(o["edge_index"], o["type"]): o for o in room.get("openings", [])}

    want = [
        # edge 0 = north (0,0)->(W,0), offset along +x
        dict(edge_index=0, type="door", offset=DOOR[0], width=DOOR[1] - DOOR[0],
             height=6.83, elevation=0.0),
        # edge 1 = east (W,0)->(W,D), offset along +z
        dict(edge_index=1, type="passage", offset=STAIR[0],
             width=STAIR[1] - STAIR[0] - 0.05, height=7.20, elevation=0.0),
        # edge 3 = west (0,D)->(0,0), offset measured from z=D backwards
        dict(edge_index=3, type="window", offset=D - WIN[1],
             width=WIN[1] - WIN[0], height=WIN_HEAD - WIN_SILL,
             elevation=WIN_SILL),
    ]
    for spec in want:
        key = (spec["edge_index"], spec["type"])
        if key in have:
            api("PATCH", f"/api/house/opening/{have[key]['id']}", spec)
            print(f"  opening {key} updated")
        else:
            api("POST", f"/api/house/room/{ROOM}/opening", spec)
            print(f"  opening {key} created")


# ================================================================== ceiling
def build_ceiling():
    m = ceiling(W, D, H,
                cans=[(2.6, 2.6), (8.5, 2.6), (14.4, 2.6),
                      (2.6, 8.4), (14.4, 8.4),
                      (2.6, 14.2), (8.5, 14.2), (14.4, 14.2),
                      (5.5, 20.2), (11.5, 20.2)],
                speakers=[(5.4, 5.6, 0.55), (11.6, 5.6, 0.55),
                          (5.4, 17.4, 0.55), (11.6, 17.4, 0.55)],
                vents=[(8.5, 6.9, 1.00, 0.55)])
    return save_and_place("Movie Ceiling", m, ROOM)


# =============================================================== trim/shell
def build_trim():
    m = baseboards(W, D, rail=RAIL_Y, wainscot="#b0aeaa",
                   doors=[("n", *DOOR), ("e", *STAIR)])
    cased_opening(m, "n", W, D, *DOOR, top=6.83)
    basement_window(m, "w", W, D, D - WIN[1], D - WIN[0], WIN_SILL, WIN_HEAD)
    cased_opening(m, "e", W, D, STAIR[0], STAIR[1] - 0.05, top=7.20)
    return save_and_place("Movie Baseboards", m, ROOM)


def basement_window(m, wall, W, D, a0, a1, sill, head):
    """Casing, stool, apron and two muntins around the REAL cut opening.

    kit.window_unit paints an emissive white pane over the hole; at this size it
    read as a projector screen hanging on the wall, so there is no pane here --
    the opening's own glass panel (house.js, 0.22 opacity) is the glazing."""
    sub = Model()
    bx(sub, TRIM, a0 - 0.20, a1 + 0.20, sill - 0.12, sill, 0.0, 0.26)      # stool
    bx(sub, TRIM, a0 + 0.10, a1 - 0.10, sill - 0.42, sill - 0.12, 0.0, 0.075)  # apron
    for a, b in ((a0 - CASE_W, a0 + 0.02), (a1 - 0.02, a1 + CASE_W)):
        bx(sub, TRIM, a, b, sill - 0.12, head + CASE_W, 0.0, 0.10)
    bx(sub, TRIM, a0 - CASE_W, a1 + CASE_W, head, head + CASE_W, 0.0, 0.10)
    for k in (1, 2):                                    # two muntins
        c = a0 + (a1 - a0) * k / 3.0
        bx(sub, TRIM, c - 0.035, c + 0.035, sill, head, 0.015, 0.055)
    blit(m, sub, wall, W, D, 0.0)


# ============================================================== screen wall
def build_screen():
    m = Model()
    # black acoustic panel + the ~100" screen inside it
    bx(m, BEZ, 1.95, 9.75, 3.32, 7.14, 0.04, 0.10)
    bx(m, BLK, 2.05, 9.65, 3.40, 7.06, 0.10, 0.19)
    # two white in-wall speaker panels flanking it
    for sx in (0.60, 10.15):
        bx(m, TRIM, sx, sx + 0.78, 4.45, 6.20, 0.04, 0.07)
        bx(m, SPKR, sx + 0.05, sx + 0.73, 4.50, 6.15, 0.07, 0.10)
    # a third grille under the rail, and the return register
    bx(m, TRIM, 4.30, 5.75, 2.42, 2.94, 0.04, 0.07)
    bx(m, SPKR, 4.35, 5.70, 2.47, 2.89, 0.07, 0.09)
    bx(m, TRIM, 9.35, 10.45, 1.92, 2.36, 0.04, 0.08)

    # ---- media console: white top, grey-oak doors, thin black legs
    cx0, cx1, cz1 = 2.30, 9.70, 1.55
    contact_shadow(m, (cx0 + cx1) / 2, cz1 * 0.55, 4.35, 1.35, y=0.010,
                   strength=0.26, room=(W, D))
    bx(m, GREYWD, cx0, cx1, 0.46, 2.22, 0.12, cz1)
    for i in range(4):
        dw = (cx1 - cx0 - 0.16) / 4
        dx0 = cx0 + 0.08 + i * dw
        bx(m, GREYWD2, dx0, dx0 + dw - 0.05, 0.54, 2.14, cz1, cz1 + 0.030)
        bx(m, BLACKMET, dx0 + dw * 0.42, dx0 + dw * 0.58, 2.02, 2.06,
           cz1 + 0.030, cz1 + 0.065)
    bx(m, WHTOP, cx0 - 0.09, cx1 + 0.09, 2.22, 2.35, 0.06, cz1 + 0.09)
    for px_ in (cx0 + 0.22, cx1 - 0.32):
        bx(m, BLACKMET, px_, px_ + 0.10, 0.0, 0.46, 0.28, 0.38)
        bx(m, BLACKMET, px_, px_ + 0.10, 0.0, 0.46, cz1 - 0.22, cz1 - 0.12)
        bx(m, BLACKMET, px_, px_ + 0.10, 0.40, 0.46, 0.28, cz1 - 0.12)

    # ---- two black subwoofers
    for (sx, sw, sh, sd) in ((0.45, 1.45, 1.55, 1.45), (9.95, 1.85, 1.90, 1.75)):
        contact_shadow(m, sx + sw / 2, 0.20 + sd / 2, sw * 0.80, sd * 0.80,
                       y=0.010, strength=0.24, room=(W, D))
        bx(m, BOXBLK, sx, sx + sw, 0.0, sh, 0.18, 0.18 + sd)
        bx(m, BEZ, sx + 0.10, sx + sw - 0.10, sh * 0.18, sh * 0.86,
           0.18 + sd, 0.18 + sd + 0.012)

    # ---- dressing on the console top: two plants, a smart display
    for px_ in (3.05, 8.15):
        m.add(cylinder(0.22, 0.36, 10, r_top=0.26), POT, at=(px_, 2.35, 0.72))
        for k in range(7):
            a = 2 * math.pi * k / 7
            m.add(puff(0.30, 0.20, 0.26, r=0.09), GREEN,
                  at=(px_ + 0.22 * math.cos(a), 2.62 + 0.07 * (k % 3),
                      0.72 + 0.22 * math.sin(a)))
    bx(m, TRIM, 6.55, 7.45, 2.35, 2.42, 0.55, 1.02)
    bx(m, BEZ, 6.58, 7.42, 2.42, 2.98, 0.62, 0.72)
    bx(m, Material("mvscr2", "#2a3138", roughness=0.25, emissive="#33424e",
                   emissive_strength=1.4),
       6.63, 7.37, 2.47, 2.93, 0.60, 0.622)
    return save_and_place("Movie Screen Wall", m, ROOM)


# ==================================================================== rug
def build_rug():
    """Cream rug + every contact shadow in the room baked into the floor decal,
    so nothing floats.  Named '... Floor Rug' so objects.js keeps it unpickable."""
    m = Model()
    x0, x1, z0, z1 = 2.30, 14.75, 5.55, 21.35
    contact_shadow(m, (x0 + x1) / 2, (z0 + z1) / 2, (x1 - x0) * 0.53,
                   (z1 - z0) * 0.53, y=0.006, strength=0.09, room=(W, D))
    A = Material("mvrugA", "#a8a296", roughness=1.0)
    B = Material("mvrugB", "#9c968a", roughness=1.0)
    bx(m, B, x0, x1, 0.014, 0.050, z0, z1)
    bx(m, A, x0 + 0.30, x1 - 0.30, 0.050, 0.062, z0 + 0.30, z1 - 0.30)
    # contact shadows for the furniture, on top of the rug
    Y = 0.064
    contact_shadow(m, 2.0, 15.4, 2.6, 5.4, y=Y, strength=0.30, room=(W, D))   # sectional W
    contact_shadow(m, 5.6, 22.1, 5.6, 2.1, y=Y, strength=0.30, room=(W, D))   # sectional S
    contact_shadow(m, 7.8, 16.0, 2.1, 2.3, y=Y, strength=0.30, room=(W, D))   # ottoman
    contact_shadow(m, 14.4, 13.3, 1.7, 1.9, y=Y, strength=0.28, room=(W, D))  # chair 1
    contact_shadow(m, 14.4, 8.6, 1.7, 1.9, y=Y, strength=0.28, room=(W, D))   # chair 2
    contact_shadow(m, 1.3, 10.6, 1.0, 1.1, y=Y, strength=0.22, room=(W, D))   # side table
    return save_and_place("Movie Floor Rug", m, ROOM)


# =============================================================== sectional
def build_sectional():
    """L-shaped greige sectional wrapping the SW corner: the plan's scan shows a
    west leg at local z 11.7-19.2 and a south leg at x 2.1-12.7, z 21.1-23.5."""
    m = Model()
    rnd = Rnd(20260816)
    # a seat pad tops out at 17-18 in, the arm at ~25, the charcoal back at ~33
    BASE_Y, SEAT_Y, ARM_Y, BACK_Y = 0.46, 1.46, 2.10, 2.78
    ARM_W = 0.42

    def run(x0, x1, z0, z1, facing, seats, arms=(True, True)):
        """A straight run.  facing 'e' -> back at x0; facing 'n' -> back at z1."""
        if facing == "e":
            back_x = x0 + 0.66                        # front face of the back
            ia = z0 + (ARM_W if arms[0] else 0.0)
            ib = z1 - (ARM_W if arms[1] else 0.0)
            slab(m, FAB_D, x0, x1 - 0.16, 0.05, BASE_Y, z0 + 0.05, z1 - 0.05)
            slab(m, FAB, x0, back_x, BASE_Y, BACK_Y - 0.44, z0, z1, r=0.06)
            slab(m, FAB_D, back_x, x1, BASE_Y, SEAT_Y - 0.26, ia, ib, r=0.06)
            for i in range(seats):
                a = ia + 0.05 + i * (ib - ia) / seats
                b = a + (ib - ia) / seats - 0.18
                slab(m, FAB, back_x + 0.04, x1 - 0.12, SEAT_Y - 0.30, SEAT_Y,
                     a, b, r=0.09)                                   # seat pad
                cush(m, BACKC, x0 + 0.10, back_x + 0.26, SEAT_Y - 0.10,
                     BACK_Y, a, b, r=0.17, nub=0.012, rnd=rnd)       # back cushion
            for k, on in enumerate(arms):
                if not on:
                    continue
                za, zb = (z0, z0 + ARM_W) if k == 0 else (z1 - ARM_W, z1)
                slab(m, FAB, x0, x1, BASE_Y, ARM_Y, za, zb, r=0.12)
                nailheads(m, STUD, (x1 - 0.01, za + 0.07), (x1 - 0.01, zb - 0.07),
                          ARM_Y - 0.20, 5)
            for cz in (z0 + 0.32, z1 - 0.32):
                for cx in (x0 + 0.34, x1 - 0.30):
                    leg(m, DKWOOD, cx, cz, 0.46, 0.16)
        else:                                          # facing north, back at z1
            back_z = z1 - 0.66
            ia = x0 + (ARM_W if arms[0] else 0.0)
            ib = x1 - (ARM_W if arms[1] else 0.0)
            slab(m, FAB_D, x0 + 0.05, x1 - 0.05, 0.05, BASE_Y, z0 + 0.16, z1)
            slab(m, FAB, x0, x1, BASE_Y, BACK_Y - 0.44, back_z, z1, r=0.06)
            slab(m, FAB_D, ia, ib, BASE_Y, SEAT_Y - 0.26, z0, back_z, r=0.06)
            for i in range(seats):
                a = ia + 0.05 + i * (ib - ia) / seats
                b = a + (ib - ia) / seats - 0.18
                slab(m, FAB, a, b, SEAT_Y - 0.30, SEAT_Y, z0 + 0.12,
                     back_z - 0.04, r=0.09)
                cush(m, BACKC, a, b, SEAT_Y - 0.10, BACK_Y,
                     back_z - 0.26, z1 - 0.10, r=0.17, nub=0.012, rnd=rnd)
            for k, on in enumerate(arms):
                if not on:
                    continue
                xa, xb = (x0, x0 + ARM_W) if k == 0 else (x1 - ARM_W, x1)
                slab(m, FAB, xa, xb, BASE_Y, ARM_Y, z0, z1, r=0.12)
                nailheads(m, STUD, (xa + 0.07, z0 + 0.01), (xb - 0.07, z0 + 0.01),
                          ARM_Y - 0.20, 5)
            for cx in (x0 + 0.32, x1 - 0.32):
                for cz in (z0 + 0.30, z1 - 0.34):
                    leg(m, DKWOOD, cx, cz, 0.46, 0.16)

    # west leg -- the one the photo looks along
    run(0.22, 3.72, 10.55, 19.85, "e", 3, arms=(True, False))
    # corner + south leg
    run(0.22, 9.55, 20.35, 23.32, "n", 3, arms=(False, True))

    # ---- throw pillows: the room's only real colour, so they carry it
    P = [(11.45, PATT_A), (12.75, SLATE), (14.05, PATT_A),
         (15.35, BOUCLE), (16.65, SLATE), (17.95, PATT_A), (19.20, SLATE)]
    for cz, mat in P:
        cush(m, mat, 0.80, 1.34, 1.52, 2.42, cz - 0.48, cz + 0.48,
             r=0.20, nub=0.02, rnd=rnd)
        if mat is PATT_A:                     # the geometric weave, blocked out
            for k in range(4):
                y = 1.68 + k * 0.19
                for off in (-0.34, 0.10):
                    bx(m, PATT_B, 1.31, 1.355, y, y + 0.085,
                       cz + off + (k % 2) * 0.17, cz + off + 0.26 + (k % 2) * 0.17)
    for cx, mat in ((2.20, SLATE), (4.40, PATT_A), (6.70, BOUCLE)):
        cush(m, mat, cx - 0.48, cx + 0.48, 1.52, 2.42, 22.20, 22.74,
             r=0.20, nub=0.02, rnd=rnd)
    # a knitted throw slung over the corner, and one over the west arm
    THROW = Material("mvthrow", "#8d99a0", roughness=1.0)
    m.add(sag_plane(2.10, 2.60, 0.05, 8, 9, edge_drop=0.30), THROW,
          at=(1.85, 1.60, 21.30))
    m.add(sag_plane(1.25, 1.90, 0.04, 6, 8, edge_drop=0.34), THROW,
          at=(2.40, 1.58, 11.30))
    return save_and_place("Movie Sectional", m, ROOM)


# ================================================================= ottoman
def build_ottoman():
    m = Model()
    x0, x1, z0, z1 = 6.05, 9.60, 14.05, 18.05
    contact_shadow(m, (x0 + x1) / 2, (z0 + z1) / 2, 2.05, 2.25, y=0.008,
                   strength=0.26)
    slab(m, FAB_D, x0 + 0.06, x1 - 0.06, 0.42, 0.60, z0 + 0.06, z1 - 0.06, r=0.04)
    slab(m, FAB, x0, x1, 0.60, 1.26, z0, z1, r=0.10)
    slab(m, FAB, x0 + 0.05, x1 - 0.05, 1.26, 1.42, z0 + 0.05, z1 - 0.05, r=0.13)
    for cx in (x0 + 0.34, x1 - 0.34):
        for cz in (z0 + 0.34, z1 - 0.34):
            leg(m, DKWOOD, cx, cz, 0.42, 0.19, taper=0.55)
    # a dark tray with two remotes and a book -- the photo's room is lived in
    TRAY = Material("mvtray", "#2b2c2e", roughness=0.55)
    bx(m, TRAY, 7.05, 8.75, 1.42, 1.50, 15.35, 16.75)
    bx(m, TRAY, 7.05, 8.75, 1.42, 1.58, 15.35, 15.42)
    bx(m, TRAY, 7.05, 8.75, 1.42, 1.58, 16.68, 16.75)
    bx(m, Material("mvrem", "#4b4d50", roughness=0.5),
       7.25, 7.45, 1.50, 1.56, 15.55, 16.45)
    bx(m, Material("mvrem", "#4b4d50", roughness=0.5),
       7.60, 7.80, 1.50, 1.56, 15.60, 16.40)
    bx(m, Material("mvbook", "#96a3a9", roughness=0.9),
       8.05, 8.62, 1.50, 1.62, 15.60, 16.55)
    return save_and_place("Movie Ottoman", m, ROOM)


# ============================================================ swivel chairs
def build_chairs():
    """Two ivory barrel swivel chairs on the east side, facing the screen."""
    m = Model()

    def chair(cx, cz, rot):
        sub = Model()
        seat_y = 1.46
        # drum base
        sub.add(cylinder(0.62, 0.13, 16), DKWOOD, at=(0, 0.0, 0))
        sub.add(cylinder(0.36, 0.24, 12), DKWOOD, at=(0, 0.13, 0))
        # seat block + pad
        sub.add(puff(2.30, 1.10, 2.30, r=0.34), IVORY, at=(0, 0.32, 0.02))
        slab(sub, IVORY, -0.80, 0.80, seat_y - 0.30, seat_y, -0.60, 1.06, r=0.16)
        # wrap-around barrel back: one swept band, not a ring of lumps
        barrel(sub, IVORY, 0.0, 0.0, 1.00, 0.64,
               R(165), R(375), seat_y - 0.34, 0.58, 1.34, steps=26)
        ca, sa = math.cos(R(rot)), math.sin(R(rot))
        for part, mm in sub._parts:
            v = [(cx + x * ca + z * sa, y, cz - x * sa + z * ca)
                 for (x, y, z) in part.verts]
            m._parts.append((Part(v, part.tris, part.smooth), mm))

    chair(14.35, 13.25, 240)
    chair(14.45, 8.55, 300)
    return save_and_place("Movie Swivel Chairs", m, ROOM)


# ===================================================================== art
def build_art():
    """Five-panel print on the west wall, over the sectional."""
    m = Model()
    z0, z1 = 11.60, 19.60
    y0, y1 = 4.05, 6.55
    n, gap = 5, 0.14
    pw = (z1 - z0 - gap * (n - 1)) / n
    sub = Model()
    rnd = Rnd(4242)
    for i in range(n):
        a = (D - z1) + i * (pw + gap)
        # frameless canvas: a 0.9 in edge return, then the printed face
        bx(sub, ARTDK, a, a + pw, y0, y1, 0.026, 0.098)
        bx(sub, ARTINK, a + 0.012, a + pw - 0.012, y0 + 0.012, y1 - 0.012,
           0.098, 0.106)
        # pale sky over a dark horizon, with two or three broad silhouettes --
        # round C's five thin bars per panel read as a bar chart, not a print
        bx(sub, ARTLT, a + 0.012, a + pw - 0.012, y1 - 1.05, y1 - 0.012,
           0.106, 0.112)
        bx(sub, ARTDK, a + 0.012, a + pw - 0.012, y0 + 0.012, y1 - 1.28,
           0.106, 0.113)
        for k in range(2):
            w0 = a + 0.10 + k * (pw - 0.20) / 2 + rnd.f(0.0, 0.16)
            w1 = w0 + (pw - 0.20) / 2 * rnd.f(0.55, 0.92)
            bx(sub, ARTDK, w0, w1, y1 - 1.28, y1 - 1.05 + rnd.f(0.12, 0.60),
               0.113, 0.119)
        bx(sub, ARTINK, a + 0.012, a + pw - 0.012, y1 - 1.34, y1 - 1.22,
           0.113, 0.120)
    blit(m, sub, "w", W, D, 0.0)
    return save_and_place("Movie Art Panels", m, ROOM)


# ============================================== side table, lamp, tower fan
def build_side():
    m = Model()
    # small dark-wood side table at the north end of the sectional
    tx, tz = 1.30, 10.55
    contact_shadow(m, tx, tz, 0.85, 0.95, y=0.008, strength=0.20)
    bx(m, TBLWOOD, tx - 0.85, tx + 0.85, 1.94, 2.06, tz - 0.95, tz + 0.95)
    for dx, dz in ((-0.70, -0.80), (0.70, -0.80), (-0.70, 0.80), (0.70, 0.80)):
        bx(m, TBLWOOD, tx + dx - 0.05, tx + dx + 0.05, 0.0, 1.94,
           tz + dz - 0.05, tz + dz + 0.05)
    # black table lamp
    m.add(cylinder(0.30, 0.07, 14), LAMPBLK, at=(tx, 2.06, tz))
    m.add(cylinder(0.055, 0.62, 8), LAMPBLK, at=(tx, 2.13, tz))
    m.add(cylinder(0.42, 0.52, 16, r_top=0.32), LAMPSHD, at=(tx, 2.72, tz))
    m.add(cylinder(0.30, 0.02, 14), Material("mvbulb", "#fff3dd", roughness=0.3,
                                             emissive="#fff0d2",
                                             emissive_strength=3.0),
          at=(tx, 3.22, tz))
    # white bladeless tower fan, north of it
    fx, fz = 0.95, 7.20
    contact_shadow(m, fx, fz, 0.55, 0.55, y=0.008, strength=0.18)
    m.add(cylinder(0.48, 0.07, 16), FANW, at=(fx, 0.0, fz))
    m.add(cylinder(0.23, 1.05, 12, r_top=0.20), FANW, at=(fx, 0.07, fz))
    # the bladeless loop: one torus standing in the XY plane, stretched tall
    m.add(torus(0.52, 0.085, 22, 8), FANW, at=(fx, 1.86, fz),
          rot_x=R(90), scale=(0.86, 1.0, 1.30))
    return save_and_place("Movie Side Table", m, ROOM)


# ============================================================== stair guard
def build_stair():
    """A white newel and half-wall at the south jamb of the stairwell opening,
    which is what the photo's bottom-right corner actually shows."""
    m = Model()
    NEWEL = Material("mvnewel", "#141416", roughness=0.42)
    # half wall closing the south end of the opening, capped in white
    bx(m, TRIM, W - 0.44, W, 0.0, 3.02, STAIR[1] - 1.70, STAIR[1] - 0.02)
    bx(m, TRIM, W - 0.52, W, 3.02, 3.16, STAIR[1] - 1.78, STAIR[1] - 0.02)
    # black newel at its open end, with a level cap rail running north
    nx, nz = W - 0.24, STAIR[1] - 1.90
    m.add(box(0.32, 3.28, 0.32), NEWEL, at=(nx, 0.0, nz))
    m.add(box(0.42, 0.16, 0.42), NEWEL, at=(nx, 3.28, nz))
    m.add(box(0.13, 0.13, 1.20), NEWEL, at=(nx, 3.00, nz - 0.70))
    return save_and_place("Movie Stair Rail", m, ROOM)


if __name__ == "__main__":
    print("room 1 Movie Room")
    surfaces(ROOM, wall_color="#dcdbd8", floor_color="#6b6967",
             floor_texture="wood")
    openings()
    out = [build_ceiling(), build_trim(), build_screen(), build_rug(),
           build_sectional(), build_ottoman(), build_chairs(), build_art(),
           build_side(), build_stair()]
    print("total %.1f KB" % sum(p["kb"] for p in out))
