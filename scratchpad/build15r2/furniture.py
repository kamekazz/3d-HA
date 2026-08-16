"""Rios Room round-2 furniture, authored in room-local feet (see common.py).

Orientation vs round 1: windows are on the SOUTH wall, the birdcage is on the
WEST wall (tucked into the SW end), the console/art/fan are on the EAST wall,
and the doors are on the NORTH wall.
"""

import math
from common import *   # noqa

R = math.radians


def lathe(m, mat, at, profile, seg=20):
    """Solid of revolution from [(y, radius), ...] (feet, y from the base)."""
    for i in range(len(profile) - 1):
        (y0, r0), (y1, r1) = profile[i], profile[i + 1]
        m.add(cylinder(max(r0, 1e-3), y1 - y0, seg, r_top=max(r1, 1e-3)), mat,
              at=(at[0], at[1] + y0, at[2]))


def leaf(m, mat, at, w, l, rot_y=0.0, tilt=0.0, roll=0.0):
    m.add(cylinder(0.5, 0.035, 9, anchor="center"), mat, at=at,
          scale=(w, 1.0, l), rot_x=R(tilt), rot_z=R(roll), rot_y=R(rot_y))


# ------------------------------------------------------------ palettes
SHELF_W  = Material("shelfw",  "#f4f3ef", roughness=0.55)
SHADE    = Material("shade",   "#bcbab5", roughness=0.9)
BIN      = Material("bin",     "#f0ede6", roughness=0.95)
BIN_TL   = Material("bintl",   "#3f9a92", roughness=0.95)
KNIT_GR  = Material("knitgr",  "#c0bbb0", roughness=1.0)
KNIT_TL  = Material("knittl",  "#3f9a92", roughness=1.0)
LEAF_DK  = Material("leafdk",  "#5d7370", roughness=0.72)
LEAF_SNK = Material("leafsnk", "#5c7a45", roughness=0.8)
LEAF_LT  = Material("leaflt",  "#a8b46a", roughness=0.8)
STEM     = Material("stem",    "#6d7a6a", roughness=0.8)
POT_W    = Material("potw",    "#f4f3ef", roughness=0.6)
TEAL     = Material("teal",    "#2f8d88", roughness=0.6)
TEAL_DK  = Material("tealdk",  "#1f5f5e", roughness=0.7)
MUTE_G   = Material("muteg",   "#8fa47a", roughness=0.75)
MUTE_O   = Material("muteo",   "#c98a63", roughness=0.75)
MUTE_P   = Material("mutep",   "#c295a6", roughness=0.75)
DARKOBJ  = Material("darkobj", "#5a6064", roughness=0.6)
ART_INK  = Material("artink",  "#5b6165", roughness=0.8)
ART_GOLD = Material("artgold", "#c9b489", roughness=0.85)
ART_SKY  = Material("artsky",  "#e6e2d6", roughness=0.85)
CANVAS   = Material("canvas",  "#f7f6f2", roughness=0.9)
SHOE_D   = Material("shoed",   "#3a3d42", roughness=0.6)
SHOE_W   = Material("shoew",   "#e9e7e2", roughness=0.6)
BRONZE   = Material("bronze",  "#6b4d3a", roughness=0.85)
NICKEL   = Material("nickel",  "#c9ccce", roughness=0.35, metallic=0.6)


# =====================================================================
# south wall: leaning ladder shelf between the two windows
SHELF_CX, SHELF_ZFOOT = 6.50, 10.35


def ladder_shelf(cx=SHELF_CX, z_foot=SHELF_ZFOOT, wdt=2.55, hgt=5.95):
    """White leaning ladder shelf, five shelves, deepest at the bottom.

    Leans back against the SOUTH wall, so the top rail is at high z and the
    feet stand out into the room at low z.

    Styling follows the photo (critic item 11): two WHITE fabric bins on the
    bottom shelf, and the clutter above is muted greys / soft greens rather
    than round 1's saturated primaries.
    """
    m = Model()
    z_top = D - 0.14
    lean = z_top - z_foot
    ang = math.degrees(math.atan2(lean, hgt))
    L = math.hypot(hgt, lean)

    def rail_z(y):
        return z_foot + lean * y / hgt

    for sx in (cx - wdt / 2 + 0.065, cx + wdt / 2 - 0.065):
        m.add(box(0.13, L, 0.105), SHELF_W, at=(sx, 0.0, z_foot), rot_x=R(ang))

    ys = [0.52, 1.85, 3.06, 4.20, 5.30]
    for y in ys:
        zb = rail_z(y) - 0.045
        bx(m, SHELF_W, cx - wdt / 2, cx + wdt / 2, y, y + 0.075, zb, D - 0.055)
        bx(m, SHELF_W, cx - wdt / 2, cx + wdt / 2, y - 0.055, y, zb, zb + 0.05)
        bx(m, SHADE, cx - wdt / 2 + 0.01, cx + wdt / 2 - 0.01, y - 0.085, y - 0.055,
           zb + 0.05, D - 0.06)

    # --- bottom shelf: two white fabric bins
    for sx in (cx - 0.60, cx + 0.60):
        bx(m, BIN, sx - 0.51, sx + 0.51, ys[0] + 0.075, ys[0] + 1.14,
           D - 1.10, D - 0.16)
        bx(m, SHADE, sx - 0.42, sx + 0.42, ys[0] + 1.03, ys[0] + 1.10,
           D - 1.02, D - 0.24)

    # --- shelf 2: soft toys, one teal bin
    y = ys[1] + 0.075
    for (dx, dz, w, h, d, mat) in ((-0.85, 0.40, 0.42, 0.30, 0.34, SHADE),
                                   (-0.32, 0.46, 0.50, 0.36, 0.40, MUTE_G),
                                   (0.22, 0.34, 0.34, 0.42, 0.30, TEAL),
                                   (0.72, 0.48, 0.40, 0.30, 0.34, MUTE_O),
                                   (1.02, 0.34, 0.26, 0.34, 0.26, SHOE_W)):
        m.add(rounded_box(w, h, d, 0.09, 3), mat, at=(cx + dx, y, D - dz - 0.20))

    # --- shelf 3: teal vase + a dark storage box
    y = ys[2] + 0.075
    lathe(m, TEAL, (cx - 0.72, y, D - 0.58),
          [(0, 0.13), (0.10, 0.24), (0.30, 0.27), (0.46, 0.16), (0.58, 0.11)])
    lathe(m, TEAL_DK, (cx - 0.28, y, D - 0.55),
          [(0, 0.10), (0.06, 0.17), (0.20, 0.18), (0.30, 0.09)])
    m.add(rounded_box(1.05, 0.40, 0.62, 0.06, 3), DARKOBJ, at=(cx + 0.55, y, D - 0.60))

    # --- shelf 4: small framed sign + two toys
    y = ys[3] + 0.075
    bx(m, DARKOBJ, cx - 0.70, cx - 0.06, y, y + 0.60, D - 0.42, D - 0.37)
    bx(m, ART_GOLD, cx - 0.65, cx - 0.11, y + 0.05, y + 0.55, D - 0.37, D - 0.34)
    m.add(rounded_box(0.34, 0.32, 0.28, 0.08, 3), TEAL, at=(cx + 0.25, y, D - 0.48))
    m.add(rounded_box(0.30, 0.36, 0.26, 0.08, 3), MUTE_P, at=(cx + 0.68, y, D - 0.46))

    # --- shelf 5: a couple of small dark objects
    y = ys[4] + 0.075
    m.add(rounded_box(0.30, 0.26, 0.24, 0.06, 3), DARKOBJ, at=(cx - 0.55, y, D - 0.34))
    m.add(rounded_box(0.24, 0.30, 0.22, 0.06, 3), DARKOBJ, at=(cx + 0.10, y, D - 0.33))
    lathe(m, POT_W, (cx + 0.72, y, D - 0.33),
          [(0, 0.09), (0.05, 0.13), (0.22, 0.13), (0.28, 0.10)])
    return m


# =====================================================================
def round_art(cx=SHELF_CX, y0=4.68, w=1.95, h=1.85):
    """White-framed square canvas with the circular line motif, SOUTH wall.

    Sits between the two window head casings, its lower half behind the
    ladder's top two shelves -- the overlap the photo shows.
    """
    m = Model()
    f = 0.075
    bx(m, SHELF_W, cx - w / 2, cx + w / 2, y0, y0 + h, D - 0.115, D - 0.030)
    bx(m, CANVAS, cx - w / 2 + f, cx + w / 2 - f, y0 + f, y0 + h - f,
       D - 0.125, D - 0.115)
    r = min(w, h) * 0.33
    cy = y0 + h / 2
    n = 17
    for i in range(n):
        t = (i + 0.5) / n
        yy = cy - r + 2 * r * t
        half = r * math.sqrt(max(0.0, 1 - (2 * t - 1) ** 2))
        bx(m, ART_INK, cx - half, cx + half, yy - 0.026, yy + 0.026,
           D - 0.132, D - 0.125)
    return m


# =====================================================================
def pouf(mat, r=0.95, h=1.15):
    m = Model()
    lathe(m, mat, (0, 0, 0),
          [(0, r * 0.62), (h * 0.16, r * 0.90), (h * 0.42, r), (h * 0.72, r * 0.93),
           (h * 0.92, r * 0.72), (h, r * 0.46)], seg=22)
    for i in range(26):
        a = 2 * math.pi * i / 26
        m.add(cylinder(0.024, h * 0.68, 6), mat,
              at=(r * 0.975 * math.cos(a), h * 0.17, r * 0.975 * math.sin(a)))
    return m


def place_pouf(name, mat, x, z, r, h):
    m = pouf(mat, r, h)
    lo, hi = m.bounds()
    path = os.path.join(OUT, name.replace(" ", "_").lower() + ".glb")
    m.save(path)
    place(name, path, ROOM, pos=(x, 0.0, z), rot_y_deg=0.0)
    print(f"{name:22s} size=({round(hi[0]-lo[0],2)}, {round(hi[1]-lo[1],2)}, "
          f"{round(hi[2]-lo[2],2)})  pos=({x},0,{z})")
    return {"name": name, "size_ft": [round(hi[i] - lo[i], 3) for i in range(3)],
            "pos": [x, 0.0, z], "rot": 0}


# =====================================================================
def rubber_plant(cx, cz, drift=(0.85, 0.0), top=6.15, seed=4242, nleaf=26):
    """Tall rubber tree in a white pot on a splayed black plant stand.

    `drift` is how far (x, z) the canopy leans away from the pot -- the photo
    has both of this room's rubber trees arching over their neighbouring wall.
    """
    m = Model()
    rn = Rnd(seed)
    stand_h = 1.05
    for i in range(4):
        a = math.pi / 4 + i * math.pi / 2
        x0, z0 = cx + 0.52 * math.cos(a), cz + 0.52 * math.sin(a)
        x1, z1 = cx + 0.72 * math.cos(a), cz + 0.72 * math.sin(a)
        dx, dz = x1 - x0, z1 - z0
        L = math.hypot(math.hypot(dx, dz), stand_h)
        m.add(box(0.075, L, 0.075), BLACKMET, at=(x0, 0, z0),
              rot_z=R(-math.degrees(math.atan2(dx, stand_h))),
              rot_x=R(math.degrees(math.atan2(dz, stand_h))))
    m.add(torus(0.55, 0.045, 22, 7), BLACKMET, at=(cx, stand_h - 0.06, cz))
    lathe(m, POT_W, (cx, stand_h - 0.30, cz),
          [(0, 0.40), (0.10, 0.50), (0.95, 0.58), (1.10, 0.56)], seg=22)
    base = stand_h - 0.30 + 1.05
    lathe(m, Material("soil", "#3c3a35", roughness=1.0), (cx, base - 0.04, cz),
          [(0, 0.54), (0.05, 0.53)], seg=18)

    segs = 13
    pts = []
    for i in range(segs + 1):
        t = i / segs
        y = base + (top - base) * t
        x = cx + 0.22 * math.sin(t * 2.6) + drift[0] * t * t
        z = cz + 0.16 * math.sin(t * 1.7) + drift[1] * t * t
        pts.append((x, y, z))
    for i in range(segs):
        (x0, y0, z0), (x1, y1, z1) = pts[i], pts[i + 1]
        dx, dy, dz = x1 - x0, y1 - y0, z1 - z0
        L = math.hypot(math.hypot(dx, dz), dy)
        r = 0.105 * (1 - 0.50 * i / segs)
        m.add(cylinder(r, L, 7), STEM, at=(x0, y0, z0),
              rot_z=R(-math.degrees(math.atan2(dx, dy))),
              rot_x=R(math.degrees(math.atan2(dz, dy))))

    ux, uz = drift[0], drift[1]
    n = math.hypot(ux, uz) or 1.0
    ux, uz = ux / n, uz / n
    for i in range(nleaf):
        t = 0.42 + 0.58 * (i / max(1, nleaf - 1.0))
        k = min(int(t * segs), segs)
        x, y, z = pts[k]
        a = i * 2.399
        reach = 0.34 + rn.f(0, 0.78)
        # bias the spread along the drift direction so the canopy hangs the way
        # the photo has it instead of ballooning symmetrically into the wall
        lx = x + reach * (0.45 * math.cos(a) + 0.75 * ux)
        lz = z + reach * (0.45 * math.sin(a) + 0.75 * uz)
        ly = y + rn.f(-0.30, 0.26)
        m.add(cylinder(0.040, math.hypot(reach, abs(ly - y)) * 0.55, 5), STEM,
              at=(x, y, z),
              rot_z=R(-math.degrees(math.atan2(lx - x, max(0.30, y - ly + 0.55)))),
              rot_x=R(math.degrees(math.atan2(lz - z, max(0.30, y - ly + 0.55)))))
        leaf(m, LEAF_DK, (lx, ly, lz), 0.56 + rn.f(0, 0.16), 0.76 + rn.f(0, 0.20),
             rot_y=math.degrees(a), tilt=rn.f(48, 76), roll=rn.f(-18, 18))
    return m


# =====================================================================
CAGE = dict(cx=1.07, cz=9.00, wd=1.90, dp=3.20)


def birdcage(cx, cz, wd, dp):
    """Large light-grey parrot cage on a rolling stand, back to the WEST wall,
    tucked into the south-west end of it the way the primary photo has it.

    Round 1 built it 5.87 ft tall and stood it 1.3 ft off the wall; the critic
    measured ~4.5-5 ft and hard into the corner.  wd runs east-west (depth off
    the wall), dp runs north-south (its long side, against the wall).
    """
    m = Model()
    x0, x1 = cx - wd / 2, cx + wd / 2
    z0, z1 = cz - dp / 2, cz + dp / 2
    stand_top = 1.40
    body_top = 4.10
    arch_top = 4.95
    bar = 0.038

    for (lx, lz) in ((x0 + 0.10, z0 + 0.10), (x1 - 0.10, z0 + 0.10),
                     (x0 + 0.10, z1 - 0.10), (x1 - 0.10, z1 - 0.10)):
        bx(m, GREYMET, lx - 0.05, lx + 0.05, 0.22, stand_top, lz - 0.05, lz + 0.05)
        m.add(cylinder(0.105, 0.055, 12), BLACKMET, at=(lx, 0.05, lz), rot_x=R(90))
        bx(m, GREYMET, lx - 0.035, lx + 0.035, 0.10, 0.24, lz - 0.035, lz + 0.035)
    for i in range(7):
        z = z0 + 0.12 + i * (dp - 0.24) / 6
        bx(m, GREYMET, x0 + 0.08, x1 - 0.08, 0.50, 0.54, z - 0.028, z + 0.028)
    for i in range(4):
        x = x0 + 0.10 + i * (wd - 0.20) / 3
        bx(m, GREYMET, x - 0.028, x + 0.028, 0.54, 0.575, z0 + 0.10, z1 - 0.10)
    for zz in (z0 + 0.10, z1 - 0.10):
        bx(m, GREYMET, x0 + 0.05, x1 - 0.05, 1.10, 1.17, zz - 0.035, zz + 0.035)

    # seed skirt / tray
    bx(m, GREYMET, x0 - 0.09, x1 + 0.09, stand_top - 0.28, stand_top,
       z0 - 0.09, z1 + 0.09)
    bx(m, Material("graten", "#c6c9ca", roughness=0.5, metallic=0.4),
       x0, x1, stand_top, stand_top + 0.04, z0, z1)
    for i in range(11):
        z = z0 + 0.10 + i * (dp - 0.20) / 10
        bx(m, GREYMET, x0 + 0.05, x1 - 0.05, stand_top + 0.04, stand_top + 0.075,
           z - 0.022, z + 0.022)

    def vbars(a0, a1, fixed, axis, y0, y1, step=0.125):
        n = max(2, int((a1 - a0) / step))
        for i in range(n + 1):
            v = a0 + (a1 - a0) * i / n
            if axis == "x":
                bx(m, GREYMET, v - bar / 2, v + bar / 2, y0, y1,
                   fixed - bar / 2, fixed + bar / 2)
            else:
                bx(m, GREYMET, fixed - bar / 2, fixed + bar / 2, y0, y1,
                   v - bar / 2, v + bar / 2)

    top_body = stand_top + 0.08
    vbars(x0, x1, z0, "x", top_body, body_top)
    vbars(x0, x1, z1, "x", top_body, body_top)
    vbars(z0, z1, x0, "z", top_body, body_top)
    vbars(z0, z1, x1, "z", top_body, body_top)
    for y in (top_body + 0.05, 2.30, 3.10, body_top - 0.05):
        bx(m, GREYMET, x0 - 0.02, x1 + 0.02, y, y + 0.055, z0 - 0.03, z0 + 0.03)
        bx(m, GREYMET, x0 - 0.02, x1 + 0.02, y, y + 0.055, z1 - 0.03, z1 + 0.03)
        bx(m, GREYMET, x0 - 0.03, x0 + 0.03, y, y + 0.055, z0 - 0.02, z1 + 0.02)
        bx(m, GREYMET, x1 - 0.03, x1 + 0.03, y, y + 0.055, z0 - 0.02, z1 + 0.02)

    # arched play top: barrel arch springing across the depth (x)
    steps = 12
    for j in range(steps):
        t0, t1 = j / steps, (j + 1) / steps
        a0, a1 = t0 * math.pi, t1 * math.pi
        rx, ry = wd / 2, arch_top - body_top
        p0 = (cx - rx * math.cos(a0), body_top + ry * math.sin(a0))
        p1 = (cx - rx * math.cos(a1), body_top + ry * math.sin(a1))
        L = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
        ang = -math.degrees(math.atan2(p1[0] - p0[0], p1[1] - p0[1]))
        for zz in (z0, z1):
            m.add(box(bar, L, bar), GREYMET, at=(p0[0], p0[1], zz), rot_z=R(ang))
    nrib = max(2, int(dp / 0.28))
    for i in range(nrib + 1):
        zz = z0 + dp * i / nrib
        for j in range(steps):
            t0, t1 = j / steps, (j + 1) / steps
            a0, a1 = t0 * math.pi, t1 * math.pi
            p0 = (cx - (wd / 2) * math.cos(a0),
                  body_top + (arch_top - body_top) * math.sin(a0))
            p1 = (cx - (wd / 2) * math.cos(a1),
                  body_top + (arch_top - body_top) * math.sin(a1))
            L = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
            ang = -math.degrees(math.atan2(p1[0] - p0[0], p1[1] - p0[1]))
            m.add(box(0.032, L, 0.032), GREYMET, at=(p0[0], p0[1], zz), rot_z=R(ang))

    # door outline on the EAST face (the one you see from the room) + latch
    for yy in (1.95, 3.45):
        bx(m, GREYMET, x1 + 0.02, x1 + 0.05, yy, yy + 0.05, cz - 0.62, cz + 0.62)
    for zz in (cz - 0.62, cz + 0.62):
        bx(m, GREYMET, x1 + 0.02, x1 + 0.05, 1.95, 3.50, zz, zz + 0.05)

    for i in range(int((body_top - top_body) / 0.30)):
        yy = top_body + 0.18 + i * 0.30
        for zz in (z0, z1):
            bx(m, GREYMET, x0, x1, yy, yy + 0.030, zz - 0.015, zz + 0.015)
        for xx in (x0, x1):
            bx(m, GREYMET, xx - 0.015, xx + 0.015, yy, yy + 0.030, z0, z1)

    for y, zz in ((2.40, cz - 0.55), (3.20, cz + 0.45)):
        bx(m, Material("perch", "#a08b6d", roughness=0.9),
           x0 + 0.12, x1 - 0.12, y, y + 0.09, zz - 0.045, zz + 0.045)
    rn = Rnd(77)
    for i in range(12):
        mat = (MUTE_G, ART_GOLD, MUTE_O, MUTE_P, TEAL)[i % 5]
        m.add(rounded_box(0.16, 0.20, 0.16, 0.05, 2),  mat,
              at=(cx + rn.f(-0.6, 0.6), 3.35 + rn.f(0, 0.65), cz + rn.f(-1.3, 1.3)))
    for zz in (cz - 0.9, cz + 0.9):
        lathe(m, Material("dish", "#dcdfe0", roughness=0.4, metallic=0.3),
              (x1 - 0.35, 2.20, zz), [(0, 0.13), (0.16, 0.19)], seg=12)
    return m


# =====================================================================
CONSOLE_CZ, CONSOLE_L, CONSOLE_DP, CONSOLE_H = 7.40, 4.00, 1.15, 2.55


def console(cz=CONSOLE_CZ, length=CONSOLE_L, depth=CONSOLE_DP, h=CONSOLE_H):
    """Narrow white console against the EAST wall, plants and shoes on it."""
    m = Model()
    x1 = W - 0.09
    x0 = x1 - depth
    z0, z1 = cz - length / 2, cz + length / 2
    bx(m, SHELF_W, x0, x1, h - 0.09, h, z0, z1)
    bx(m, SHELF_W, x0 + 0.02, x1 - 0.06, 0.42, 0.50, z0 + 0.08, z1 - 0.08)
    for (lx, lz) in ((x0 + 0.06, z0 + 0.06), (x1 - 0.06, z0 + 0.06),
                     (x0 + 0.06, z1 - 0.06), (x1 - 0.06, z1 - 0.06)):
        bx(m, SHELF_W, lx - 0.06, lx + 0.06, 0.0, h - 0.09, lz - 0.06, lz + 0.06)
    bx(m, SHELF_W, x1 - 0.10, x1 - 0.05, h - 0.30, h - 0.09, z0 + 0.06, z1 - 0.06)

    rn = Rnd(555)
    for i in range(6):
        zz = z0 + 0.35 + i * (length - 0.8) / 5
        mat = SHOE_D if i % 2 else SHOE_W
        m.add(rounded_box(0.85, 0.34, 0.34, 0.10, 3), mat,
              at=((x0 + x1) / 2, 0.50, zz), rot_y=R(rn.f(-8, 8)))
    for (dz, r, ph) in ((-1.45, 0.20, 0.42), (-0.75, 0.26, 0.50),
                        (0.55, 0.22, 0.44), (1.35, 0.30, 0.55)):
        px, pz = (x0 + x1) / 2, cz + dz
        lathe(m, POT_W, (px, h, pz), [(0, r * 0.75), (ph * 0.75, r), (ph, r * 0.92)])
        for k in range(7):
            a = k * 2.399
            bl = prism([(-0.075, -0.022), (0.075, -0.022),
                        (0.05, 0.022), (-0.05, 0.022)], 0.40 + rn.f(0, 0.32))
            m.add(bl, LEAF_SNK, at=(px + r * 0.30 * math.cos(a), h + ph - 0.06,
                                    pz + r * 0.30 * math.sin(a)),
                  rot_y=R(math.degrees(a)), rot_z=R(rn.f(-26, 26)),
                  rot_x=R(rn.f(-18, 18)))
    m.add(rounded_box(0.42, 0.26, 0.30, 0.06, 3), DARKOBJ,
          at=((x0 + x1) / 2, h, cz - 0.15))
    return m


# =====================================================================
def landscape_art(cz=CONSOLE_CZ, y0=3.45, w=2.45, h=1.95):
    """Framed abstract landscape over the console, EAST wall."""
    m = Model()
    f = 0.075
    z0, z1 = cz - w / 2, cz + w / 2
    bx(m, SHELF_W, W - 0.115, W - 0.030, y0, y0 + h, z0, z1)
    bx(m, ART_SKY, W - 0.125, W - 0.115, y0 + f, y0 + h - f, z0 + f, z1 - f)
    bx(m, ART_GOLD, W - 0.133, W - 0.125, y0 + f, y0 + h * 0.46, z0 + f, z1 - f)
    bx(m, Material("artband", "#a89a78", roughness=0.85),
       W - 0.140, W - 0.133, y0 + h * 0.30, y0 + h * 0.40, z0 + f, z1 - f)
    bx(m, Material("artband2", "#d8d2c2", roughness=0.85),
       W - 0.140, W - 0.133, y0 + h * 0.52, y0 + h * 0.66, z0 + f + 0.25, z1 - f - 0.45)
    return m


# =====================================================================
def tower_fan(cx=11.95, cz=4.60, h=2.80):
    m = Model()
    lathe(m, Material("fanw", "#eeedea", roughness=0.5), (cx, 0, cz),
          [(0, 0.42), (0.09, 0.44), (0.14, 0.30), (0.32, 0.33),
           (h - 0.30, 0.33), (h - 0.06, 0.31), (h, 0.24)], seg=20)
    for i in range(9):
        y = 0.75 + i * 0.14
        m.add(torus(0.335, 0.020, 18, 5),
              Material("fangrill", "#c9c8c4", roughness=0.6), at=(cx, y, cz))
    return m


# =====================================================================
LAMP_X, LAMP_Z = 11.45, 2.95


def lamp_drum(cx=LAMP_X, cz=LAMP_Z, h=5.10):
    """The drum-shade floor lamp that frames the left of the primary photo.

    NOT called "Floor Lamp": objects.js makes anything whose name contains
    "floor" unpickable, and this is real furniture.
    """
    m = Model()
    lathe(m, NICKEL, (cx, 0, cz),
          [(0, 0.58), (0.06, 0.60), (0.10, 0.20), (0.16, 0.09)], seg=20)
    m.add(cylinder(0.045, h - 1.05, 12), NICKEL, at=(cx, 0.16, cz))
    shade_h, r_b, r_t = 0.98, 0.74, 0.68
    lathe(m, BRONZE, (cx, h - shade_h, cz),
          [(0, r_b), (shade_h, r_t)], seg=24)
    m.add(torus(r_b, 0.022, 24, 6), BRONZE, at=(cx, h - shade_h, cz))
    m.add(torus(r_t, 0.022, 24, 6), BRONZE, at=(cx, h, cz))
    # the lit underside of the shade
    lathe(m, Material("shadelit", "#f6ead6", roughness=0.5, emissive="#e8d3ae",
                      emissive_strength=1.6),
          (cx, h - shade_h + 0.02, cz), [(0, r_b - 0.03), (0.03, r_b - 0.03)], seg=24)
    return m


# =====================================================================
def trailing_plant(cx=W - 0.30, cz=1.95, y=5.45):
    """The trailing plant hanging high on the EAST wall above the console --
    photo 3's top-right corner, and the leaves at the top-left of the primary
    photo."""
    m = Model()
    rn = Rnd(6161)
    bx(m, SHELF_W, W - 0.10, W - 0.02, y - 0.06, y + 0.34, cz - 0.62, cz + 0.62)
    lathe(m, POT_W, (cx - 0.22, y, cz),
          [(0, 0.26), (0.06, 0.32), (0.44, 0.34), (0.50, 0.32)], seg=18)
    lathe(m, Material("soil3", "#3c3a35", roughness=1.0), (cx - 0.22, y + 0.44, cz),
          [(0, 0.31), (0.04, 0.30)], seg=14)
    for v in range(6):
        a = v * 1.05 - 2.6
        px = cx - 0.22 + 0.26 * math.cos(a)
        pz = cz + 0.30 * math.sin(a)
        drop = 1.10 + rn.f(0, 1.35)
        segs = 7
        for i in range(segs):
            t0, t1 = i / segs, (i + 1) / segs
            y0 = y + 0.42 - drop * t0
            y1 = y + 0.42 - drop * t1
            sway = 0.30 * math.sin(t0 * 3.1 + v)
            x0 = px - 0.14 * t0 * t0
            z0 = pz + sway * 0.5
            m.add(cylinder(0.022, y0 - y1, 5), STEM, at=(x0, y1, z0))
            leaf(m, LEAF_DK, (x0 + rn.f(-0.16, 0.16), y1, z0 + rn.f(-0.20, 0.20)),
                 0.30 + rn.f(0, 0.14), 0.38 + rn.f(0, 0.16),
                 rot_y=rn.f(0, 360), tilt=rn.f(55, 85), roll=rn.f(-20, 20))
    return m


# =====================================================================
SNAKE_X, SNAKE_Z = 7.60, 0.80


def snake_plant(cx=SNAKE_X, cz=SNAKE_Z):
    m = Model()
    rn = Rnd(31337)
    lathe(m, POT_W, (cx, 0, cz),
          [(0, 0.44), (0.08, 0.52), (0.95, 0.62), (1.05, 0.60)], seg=22)
    lathe(m, Material("soil2", "#3c3a35", roughness=1.0), (cx, 0.98, cz),
          [(0, 0.57), (0.05, 0.56)], seg=18)
    for i in range(11):
        a = i * 2.399
        lean = rn.f(5, 18)
        hgt = 1.35 + rn.f(0, 1.25)
        px = cx + rn.f(-0.16, 0.16)
        pz = cz + rn.f(-0.16, 0.16)
        blade = prism([(-0.14, -0.035), (0.14, -0.035), (0.10, 0.035), (-0.10, 0.035)],
                      hgt)
        m.add(blade, LEAF_SNK, at=(px, 1.00, pz), rot_y=R(math.degrees(a)),
              rot_z=R(lean * (1 if i % 2 else -1)), rot_x=R(rn.f(-12, 12)))
        tip = prism([(-0.10, -0.03), (0.10, -0.03), (0.0, 0.03)], 0.42)
        m.add(tip, LEAF_LT, at=(px, 1.00 + hgt - 0.02, pz), rot_y=R(math.degrees(a)),
              rot_z=R(lean * (1 if i % 2 else -1)), rot_x=R(rn.f(-12, 12)))
    return m


# =====================================================================
def gallery_art(cx=SNAKE_X, y0=4.20, w=1.42, h=1.75):
    """Small framed print on the NORTH wall between closet and entry door."""
    m = Model()
    f = 0.06
    bx(m, SHELF_W, cx - w / 2, cx + w / 2, y0, y0 + h, 0.030, 0.115)
    bx(m, CANVAS, cx - w / 2 + f, cx + w / 2 - f, y0 + f, y0 + h - f, 0.115, 0.125)
    for r in range(3):
        for c in range(3):
            px = cx - 0.38 + c * 0.38
            py = y0 + 0.30 + r * 0.40
            mat = (TEAL, ART_INK, MUTE_G, MUTE_O, ART_GOLD)[(r * 3 + c) % 5]
            bx(m, mat, px - 0.10, px + 0.10, py, py + 0.23, 0.125, 0.133)
    return m


PIECES = [
    ("Rios Ladder Shelf", lambda: ladder_shelf()),
    ("Rios Round Art", lambda: round_art()),
    ("Rios Rubber Plant", lambda: rubber_plant(2.65, 10.95, drift=(0.60, -0.45),
                                               top=6.10, seed=4242, nleaf=26)),
    ("Rios Rubber Plant East", lambda: rubber_plant(11.62, 10.55, drift=(0.20, -1.20),
                                                    top=6.30, seed=8181, nleaf=24)),
    ("Rios Birdcage", lambda: birdcage(**CAGE)),
    ("Rios Console", lambda: console()),
    ("Rios Landscape Art", lambda: landscape_art()),
    ("Rios Tower Fan", lambda: tower_fan()),
    ("Rios Lamp Drum", lambda: lamp_drum()),
    ("Rios Trailing Plant", lambda: trailing_plant()),
    ("Rios Snake Plant", lambda: snake_plant()),
    ("Rios Gallery Art", lambda: gallery_art()),
]


if __name__ == "__main__":
    import json
    L = []
    for name, fn in PIECES:
        L.append(save_and_place(name, fn()))
    L.append(place_pouf("Rios Pouf Grey", KNIT_GR, 9.90, 10.35, 0.98, 1.15))
    L.append(place_pouf("Rios Pouf Teal", KNIT_TL, 4.30, 10.50, 0.86, 1.05))
    print(json.dumps(L))
