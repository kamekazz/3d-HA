"""Rios Room furniture, authored in room-local feet (see common.py)."""

import math
from common import *   # noqa

R = math.radians


def bx(m, mat, x0, x1, y0, y1, z0, z1):
    m.add(box(x1 - x0, y1 - y0, z1 - z0), mat,
          at=((x0 + x1) / 2.0, y0, (z0 + z1) / 2.0))


class Rnd:
    def __init__(self, s):
        self.s = s

    def f(self, a=0.0, b=1.0):
        self.s = (self.s * 1103515245 + 12345) % (1 << 31)
        return a + (b - a) * (((self.s >> 9) % 100000) / 100000.0)


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
SHELF_W  = Material("shelfw",  "#f2f1ed", roughness=0.55)
SHADE    = Material("shade",   "#b9b7b2", roughness=0.9)
BIN      = Material("bin",     "#efece5", roughness=0.95)
KNIT_GR  = Material("knitgr",  "#cdc7ba", roughness=1.0)
KNIT_TL  = Material("knittl",  "#3f9a92", roughness=1.0)
LEAF_DK  = Material("leafdk",  "#5d7370", roughness=0.72)
LEAF_SNK = Material("leafsnk", "#5c7a45", roughness=0.8)
LEAF_LT  = Material("leaflt",  "#a8b46a", roughness=0.8)
STEM     = Material("stem",    "#6d7a6a", roughness=0.8)
POT_W    = Material("potw",    "#f4f3ef", roughness=0.6)
TEAL     = Material("teal",    "#2f8d88", roughness=0.6)
TEAL_DK  = Material("tealdk",  "#1f5f5e", roughness=0.7)
TOY_G    = Material("toyg",    "#8fc24a", roughness=0.7)
TOY_Y    = Material("toyy",    "#e7c94a", roughness=0.7)
TOY_O    = Material("toyo",    "#dd7a4a", roughness=0.7)
TOY_P    = Material("toyp",    "#cf7fa0", roughness=0.7)
DARKOBJ  = Material("darkobj", "#4a4f52", roughness=0.6)
ART_INK  = Material("artink",  "#5b6165", roughness=0.8)
ART_GOLD = Material("artgold", "#c9b489", roughness=0.85)
ART_SKY  = Material("artsky",  "#e6e2d6", roughness=0.85)
CANVAS   = Material("canvas",  "#f6f5f1", roughness=0.9)
SHOE_D   = Material("shoed",   "#3a3d42", roughness=0.6)
SHOE_W   = Material("shoew",   "#e9e7e2", roughness=0.6)


# =====================================================================
def ladder_shelf(cx=6.95, z_foot=1.35, wdt=2.55, hgt=5.95):
    """White leaning ladder shelf, five shelves, deepest at the bottom."""
    m = Model()
    z_top = 0.14
    lean = z_foot - z_top
    ang = -math.degrees(math.atan2(lean, hgt))
    L = math.hypot(hgt, lean)

    def rail_z(y):
        return z_foot - lean * y / hgt

    for sx in (cx - wdt / 2 + 0.065, cx + wdt / 2 - 0.065):
        m.add(box(0.13, L, 0.105), SHELF_W, at=(sx, 0.0, z_foot), rot_x=R(ang))

    ys = [0.52, 1.85, 3.06, 4.20, 5.30]
    for y in ys:
        zf = rail_z(y) + 0.045
        bx(m, SHELF_W, cx - wdt / 2, cx + wdt / 2, y, y + 0.075, 0.055, zf)
        # front lip
        bx(m, SHELF_W, cx - wdt / 2, cx + wdt / 2, y - 0.055, y, zf - 0.05, zf)
        bx(m, SHADE, cx - wdt / 2 + 0.01, cx + wdt / 2 - 0.01, y - 0.085, y - 0.055,
           0.06, zf - 0.05)

    # --- bottom shelf: two white fabric bins
    for i, sx in enumerate((cx - 0.60, cx + 0.60)):
        bx(m, BIN, sx - 0.51, sx + 0.51, ys[0] + 0.075, ys[0] + 1.14,
           0.16, 1.10)
        bx(m, DARKOBJ, sx - 0.42, sx + 0.42, ys[0] + 1.03, ys[0] + 1.10,
           0.24, 1.02)          # contents peeking over the rim

    # --- shelf 2: a scatter of toys
    y = ys[1] + 0.075
    for (dx, dz, w, h, d, mat) in ((-0.85, 0.35, 0.42, 0.30, 0.34, TOY_Y),
                                   (-0.35, 0.42, 0.50, 0.36, 0.40, TOY_G),
                                   (0.20, 0.30, 0.34, 0.42, 0.30, TEAL),
                                   (0.70, 0.44, 0.40, 0.30, 0.34, TOY_O),
                                   (1.02, 0.30, 0.26, 0.34, 0.26, SHOE_W)):
        m.add(rounded_box(w, h, d, 0.09, 3), mat, at=(cx + dx, y, dz))

    # --- shelf 3: teal vase + a dark storage box
    y = ys[2] + 0.075
    lathe(m, TEAL, (cx - 0.72, y, 0.34),
          [(0, 0.13), (0.10, 0.24), (0.30, 0.27), (0.46, 0.16), (0.58, 0.11)])
    lathe(m, TEAL_DK, (cx - 0.28, y, 0.30),
          [(0, 0.10), (0.06, 0.17), (0.20, 0.18), (0.30, 0.09)])
    m.add(rounded_box(1.05, 0.40, 0.62, 0.06, 3), TEAL_DK, at=(cx + 0.55, y, 0.36))

    # --- shelf 4: small framed sign + two toys
    y = ys[3] + 0.075
    bx(m, DARKOBJ, cx - 0.70, cx - 0.06, y, y + 0.66, 0.14, 0.19)
    bx(m, ART_GOLD, cx - 0.65, cx - 0.11, y + 0.05, y + 0.61, 0.11, 0.14)
    m.add(rounded_box(0.34, 0.32, 0.28, 0.08, 3), TEAL, at=(cx + 0.25, y, 0.26))
    m.add(rounded_box(0.30, 0.36, 0.26, 0.08, 3), TOY_P, at=(cx + 0.68, y, 0.24))

    # --- shelf 5: a couple of small dark objects
    y = ys[4] + 0.075
    m.add(rounded_box(0.30, 0.26, 0.24, 0.06, 3), DARKOBJ, at=(cx - 0.55, y, 0.16))
    m.add(rounded_box(0.24, 0.30, 0.22, 0.06, 3), DARKOBJ, at=(cx + 0.10, y, 0.15))
    lathe(m, POT_W, (cx + 0.72, y, 0.15),
          [(0, 0.09), (0.05, 0.13), (0.22, 0.13), (0.28, 0.10)])
    return m


# =====================================================================
def round_art(cx=6.95, y0=5.30, w=2.30, h=2.15):
    """White-framed square canvas with the circular line motif from the photo."""
    m = Model()
    f = 0.075
    bx(m, SHELF_W, cx - w / 2, cx + w / 2, y0, y0 + h, 0.030, 0.115)
    bx(m, CANVAS, cx - w / 2 + f, cx + w / 2 - f, y0 + f, y0 + h - f, 0.115, 0.125)
    r = min(w, h) * 0.33
    cy = y0 + h / 2
    n = 17
    for i in range(n):
        t = (i + 0.5) / n
        yy = cy - r + 2 * r * t
        half = r * math.sqrt(max(0.0, 1 - (2 * t - 1) ** 2))
        bx(m, ART_INK, cx - half, cx + half, yy - 0.028, yy + 0.028, 0.125, 0.132)
    return m


# =====================================================================
def pouf(mat, r=0.95, h=1.15):
    m = Model()
    lathe(m, mat, (0, 0, 0),
          [(0, r * 0.62), (h * 0.16, r * 0.90), (h * 0.42, r), (h * 0.72, r * 0.93),
           (h * 0.92, r * 0.72), (h, r * 0.46)], seg=22)
    # knit ribs -- shallow, so the silhouette stays round
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
def rubber_plant(cx=12.55, cz=1.02):
    """Tall rubber tree in a white pot on a black plant stand."""
    m = Model()
    rn = Rnd(4242)
    stand_h = 1.05
    # stand: four splayed legs + a ring
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
    # pot
    lathe(m, POT_W, (cx, stand_h - 0.30, cz),
          [(0, 0.40), (0.10, 0.50), (0.95, 0.58), (1.10, 0.56)], seg=22)
    base = stand_h - 0.30 + 1.05
    lathe(m, Material("soil", "#3c3a35", roughness=1.0), (cx, base - 0.04, cz),
          [(0, 0.54), (0.05, 0.53)], seg=18)

    # trunk: a shallow S leaning north-west, topping out near the ceiling
    top = 6.20
    segs = 13
    px, pz = cx, cz
    pts = []
    for i in range(segs + 1):
        t = i / segs
        y = base + (top - base) * t
        x = cx + 0.28 * math.sin(t * 2.6) - 0.75 * t * t
        z = cz + 0.30 * math.sin(t * 1.7)
        pts.append((x, y, z))
    for i in range(segs):
        (x0, y0, z0), (x1, y1, z1) = pts[i], pts[i + 1]
        dx, dy, dz = x1 - x0, y1 - y0, z1 - z0
        L = math.hypot(math.hypot(dx, dz), dy)
        r = 0.105 * (1 - 0.50 * i / segs)
        m.add(cylinder(r, L, 7), STEM, at=(x0, y0, z0),
              rot_z=R(-math.degrees(math.atan2(dx, dy))),
              rot_x=R(math.degrees(math.atan2(dz, dy))))

    # leaves: big rounded ovals clustered in the upper canopy, spread wide and
    # tilted toward vertical so they show their faces from eye level
    for i in range(28):
        t = 0.42 + 0.58 * (i / 27.0)
        k = min(int(t * segs), segs)
        x, y, z = pts[k]
        a = i * 2.399
        reach = 0.45 + rn.f(0, 1.15)
        lx = x + reach * math.cos(a) - 0.30
        lz = z + reach * 0.62 * math.sin(a)
        ly = y + rn.f(-0.30, 0.28)
        m.add(cylinder(0.040, math.hypot(reach, abs(ly - y)) * 0.55, 5), STEM,
              at=(x, y, z),
              rot_z=R(-math.degrees(math.atan2(lx - x, max(0.30, y - ly + 0.55)))),
              rot_x=R(math.degrees(math.atan2(lz - z, max(0.30, y - ly + 0.55)))))
        leaf(m, LEAF_DK, (lx, ly, lz), 0.80 + rn.f(0, 0.24), 1.10 + rn.f(0, 0.30),
             rot_y=math.degrees(a), tilt=rn.f(48, 76), roll=rn.f(-18, 18))
    return m


# =====================================================================
def birdcage(cx=14.32, cz=2.95, wd=2.15, dp=3.05):
    """Large light-grey parrot cage on a rolling stand, back to the east wall.

    wd runs east-west (x), dp runs north-south (z) -- the cage's long side is
    against the east wall, which is how the primary photo reads it.
    """
    m = Model()
    x0, x1 = cx - wd / 2, cx + wd / 2
    z0, z1 = cz - dp / 2, cz + dp / 2
    stand_top = 1.62
    body_top = 4.95
    arch_top = 5.80
    bar = 0.038

    # --- rolling stand
    for (lx, lz) in ((x0 + 0.10, z0 + 0.10), (x1 - 0.10, z0 + 0.10),
                     (x0 + 0.10, z1 - 0.10), (x1 - 0.10, z1 - 0.10)):
        bx(m, GREYMET, lx - 0.05, lx + 0.05, 0.24, stand_top, lz - 0.05, lz + 0.05)
        m.add(cylinder(0.115, 0.055, 12), BLACKMET, at=(lx, 0.06, lz), rot_x=R(90))
        bx(m, GREYMET, lx - 0.035, lx + 0.035, 0.11, 0.26, lz - 0.035, lz + 0.035)
    # lower shelf: a grid
    for i in range(7):
        z = z0 + 0.12 + i * (dp - 0.24) / 6
        bx(m, GREYMET, x0 + 0.08, x1 - 0.08, 0.56, 0.60, z - 0.028, z + 0.028)
    for i in range(4):
        x = x0 + 0.10 + i * (wd - 0.20) / 3
        bx(m, GREYMET, x - 0.028, x + 0.028, 0.60, 0.635, z0 + 0.10, z1 - 0.10)
    # apron rails
    for zz in (z0 + 0.10, z1 - 0.10):
        bx(m, GREYMET, x0 + 0.05, x1 - 0.05, 1.28, 1.36, zz - 0.035, zz + 0.035)

    # --- seed skirt / tray
    bx(m, GREYMET, x0 - 0.09, x1 + 0.09, stand_top - 0.30, stand_top,
       z0 - 0.09, z1 + 0.09)
    bx(m, Material("graten", "#c6c9ca", roughness=0.5, metallic=0.4),
       x0, x1, stand_top, stand_top + 0.04, z0, z1)
    for i in range(11):
        z = z0 + 0.10 + i * (dp - 0.20) / 10
        bx(m, GREYMET, x0 + 0.05, x1 - 0.05, stand_top + 0.04, stand_top + 0.075,
           z - 0.022, z + 0.022)

    # --- cage: vertical bars on four faces
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
    # horizontal rings
    for y in (top_body + 0.05, 2.55, 3.55, body_top - 0.05):
        bx(m, GREYMET, x0 - 0.02, x1 + 0.02, y, y + 0.055, z0 - 0.03, z0 + 0.03)
        bx(m, GREYMET, x0 - 0.02, x1 + 0.02, y, y + 0.055, z1 - 0.03, z1 + 0.03)
        bx(m, GREYMET, x0 - 0.03, x0 + 0.03, y, y + 0.055, z0 - 0.02, z1 + 0.02)
        bx(m, GREYMET, x1 - 0.03, x1 + 0.03, y, y + 0.055, z0 - 0.02, z1 + 0.02)

    # --- arched play top: barrel arch springing across the width (x)
    steps = 12
    for j in range(steps):
        t0, t1 = j / steps, (j + 1) / steps
        a0, a1 = t0 * math.pi, t1 * math.pi
        rx = wd / 2
        ry = arch_top - body_top
        p0 = (cx - rx * math.cos(a0), body_top + ry * math.sin(a0))
        p1 = (cx - rx * math.cos(a1), body_top + ry * math.sin(a1))
        L = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
        ang = -math.degrees(math.atan2(p1[0] - p0[0], p1[1] - p0[1]))
        for zz in (z0, z1):
            m.add(box(bar, L, bar), GREYMET, at=(p0[0], p0[1], zz), rot_z=R(ang))
    # ribs across the arch
    nrib = int(dp / 0.28)
    for i in range(nrib + 1):
        zz = z0 + (dp) * i / nrib
        for j in range(steps):
            t0, t1 = j / steps, (j + 1) / steps
            a0, a1 = t0 * math.pi, t1 * math.pi
            p0 = (cx - (wd / 2) * math.cos(a0), body_top + (arch_top - body_top) * math.sin(a0))
            p1 = (cx - (wd / 2) * math.cos(a1), body_top + (arch_top - body_top) * math.sin(a1))
            L = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
            ang = -math.degrees(math.atan2(p1[0] - p0[0], p1[1] - p0[1]))
            m.add(box(0.032, L, 0.032), GREYMET, at=(p0[0], p0[1], zz), rot_z=R(ang))

    # --- door outline on the west face + latch
    for yy in (2.20, 4.05):
        bx(m, GREYMET, x0 - 0.05, x0 - 0.02, yy, yy + 0.05, cz - 0.62, cz + 0.62)
    for zz in (cz - 0.62, cz + 0.62):
        bx(m, GREYMET, x0 - 0.05, x0 - 0.02, 2.20, 4.10, zz, zz + 0.05)

    # horizontal mesh wires, so the cage reads as mesh rather than jail bars
    for i in range(int((body_top - top_body) / 0.30)):
        yy = top_body + 0.18 + i * 0.30
        for zz in (z0, z1):
            bx(m, GREYMET, x0, x1, yy, yy + 0.030, zz - 0.015, zz + 0.015)
        for xx in (x0, x1):
            bx(m, GREYMET, xx - 0.015, xx + 0.015, yy, yy + 0.030, z0, z1)

    # --- perches and toys inside
    for y, zz in ((2.85, cz - 0.55), (3.75, cz + 0.45)):
        bx(m, Material("perch", "#a08b6d", roughness=0.9),
           x0 + 0.12, x1 - 0.12, y, y + 0.09, zz - 0.045, zz + 0.045)
    rn = Rnd(77)
    for i in range(14):
        mat = (TOY_G, TOY_Y, TOY_O, TOY_P, TEAL)[i % 5]
        m.add(rounded_box(0.16, 0.20, 0.16, 0.05, 2), mat,
              at=(cx + rn.f(-0.7, 0.7), 3.95 + rn.f(0, 0.9), cz + rn.f(-1.3, 1.3)))
    # food dishes
    for zz in (cz - 0.9, cz + 0.9):
        lathe(m, Material("dish", "#dcdfe0", roughness=0.4, metallic=0.3),
              (x0 + 0.35, 2.60, zz), [(0, 0.13), (0.16, 0.19)], seg=12)
    return m


# =====================================================================
def console(cz=11.90, length=4.00, depth=1.15, h=2.55):
    """Narrow white console against the west wall, plants and shoes on it."""
    m = Model()
    x0, x1 = 0.09, 0.09 + depth
    z0, z1 = cz - length / 2, cz + length / 2
    bx(m, SHELF_W, x0, x1, h - 0.09, h, z0, z1)                     # top
    bx(m, SHELF_W, x0 + 0.06, x1 - 0.02, 0.42, 0.50, z0 + 0.08, z1 - 0.08)  # shelf
    for (lx, lz) in ((x0 + 0.06, z0 + 0.06), (x1 - 0.06, z0 + 0.06),
                     (x0 + 0.06, z1 - 0.06), (x1 - 0.06, z1 - 0.06)):
        bx(m, SHELF_W, lx - 0.06, lx + 0.06, 0.0, h - 0.09, lz - 0.06, lz + 0.06)
    # rail under the top
    bx(m, SHELF_W, x0 + 0.05, x0 + 0.10, h - 0.30, h - 0.09, z0 + 0.06, z1 - 0.06)

    rn = Rnd(555)
    # shoes on the lower shelf
    for i in range(6):
        zz = z0 + 0.35 + i * (length - 0.8) / 5
        mat = SHOE_D if i % 2 else SHOE_W
        m.add(rounded_box(0.85, 0.34, 0.34, 0.10, 3), mat,
              at=((x0 + x1) / 2, 0.50, zz), rot_y=R(rn.f(-8, 8)))
    # a tray of small potted plants + a jar on top
    for i, (dz, r, ph) in enumerate(((-1.45, 0.20, 0.42), (-0.75, 0.26, 0.50),
                                     (0.55, 0.22, 0.44), (1.35, 0.30, 0.55))):
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
    # a couple of small dark objects between the pots
    m.add(rounded_box(0.42, 0.26, 0.30, 0.06, 3), DARKOBJ,
          at=((x0 + x1) / 2, h, cz - 0.15))
    return m


# =====================================================================
def landscape_art(cz=11.90, y0=3.55, w=2.65, h=2.05):
    """Framed abstract landscape over the console, on the west wall."""
    m = Model()
    f = 0.075
    z0, z1 = cz - w / 2, cz + w / 2
    bx(m, SHELF_W, 0.030, 0.115, y0, y0 + h, z0, z1)
    bx(m, ART_SKY, 0.115, 0.125, y0 + f, y0 + h - f, z0 + f, z1 - f)
    bx(m, ART_GOLD, 0.125, 0.133, y0 + f, y0 + h * 0.46, z0 + f, z1 - f)
    bx(m, Material("artband", "#a89a78", roughness=0.85),
       0.133, 0.140, y0 + h * 0.30, y0 + h * 0.40, z0 + f, z1 - f)
    bx(m, Material("artband2", "#d8d2c2", roughness=0.85),
       0.133, 0.140, y0 + h * 0.52, y0 + h * 0.66, z0 + f + 0.25, z1 - f - 0.45)
    return m


# =====================================================================
def tower_fan(cx=0.78, cz=9.05, h=2.80):
    m = Model()
    lathe(m, Material("fanw", "#eeedea", roughness=0.5), (cx, 0, cz),
          [(0, 0.42), (0.09, 0.44), (0.14, 0.30), (0.32, 0.33),
           (h - 0.30, 0.33), (h - 0.06, 0.31), (h, 0.24)], seg=20)
    for i in range(9):
        y = 0.75 + i * 0.14
        m.add(torus(0.335, 0.020, 18, 5), Material("fangrill", "#c9c8c4", roughness=0.6),
              at=(cx, y, cz))
    return m


# =====================================================================
def snake_plant(cx=1.30, cz=14.95):
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
def gallery_art(cx=7.90, y0=3.90, w=1.55, h=1.95):
    """Small framed print set on the south wall between the two doors."""
    m = Model()
    f = 0.06
    bx(m, SHELF_W, cx - w / 2, cx + w / 2, y0, y0 + h, D - 0.115, D - 0.030)
    bx(m, CANVAS, cx - w / 2 + f, cx + w / 2 - f, y0 + f, y0 + h - f,
       D - 0.125, D - 0.115)
    rn = Rnd(9090)
    for r in range(3):
        for c in range(3):
            px = cx - 0.42 + c * 0.42
            py = y0 + 0.34 + r * 0.46
            mat = (TEAL, ART_INK, TOY_G, TOY_O, ART_GOLD)[(r * 3 + c) % 5]
            bx(m, mat, px - 0.11, px + 0.11, py, py + 0.26,
               D - 0.133, D - 0.125)
    return m


if __name__ == "__main__":
    import json
    L = []
    L.append(save_and_place("Rios Ladder Shelf", ladder_shelf()))
    L.append(save_and_place("Rios Round Art", round_art()))
    L.append(place_pouf("Rios Pouf Grey", KNIT_GR, 4.00, 1.75, 0.98, 1.15))
    L.append(place_pouf("Rios Pouf Teal", KNIT_TL, 9.00, 1.35, 0.86, 1.05))
    L.append(save_and_place("Rios Rubber Plant", rubber_plant()))
    L.append(save_and_place("Rios Birdcage", birdcage()))
    L.append(save_and_place("Rios Console", console()))
    L.append(save_and_place("Rios Landscape Art", landscape_art()))
    L.append(save_and_place("Rios Tower Fan", tower_fan()))
    L.append(save_and_place("Rios Snake Plant", snake_plant()))
    L.append(save_and_place("Rios Gallery Art", gallery_art()))
    print(json.dumps(L))
