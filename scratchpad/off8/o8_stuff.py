"""Room 8 Office -- everything that makes it THIS office rather than an office.

  Office Art North      the framed specimen-grid print over the L desk
  Office Cabinet White  the white beadboard cabinet on the south wall
  Office Plant Fig      the fiddle-leaf fig in its black ribbed planter, SE
  Office Clutter        floor totes, bins, boxes, the bladeless fan, the wall
                        clock and the black wall tablet photo B shows

Sizes checked against the 6'8" door casing and the 29in desk tops: the print is
2.5 x 2.7 ft with its bottom rail 4.35 ft AFF (photo A: 63 px/ft on that wall,
frame 385-525 px against a chair rail at 600 px = 4.49-6.71 ft).
"""
import math
from o8kit import (Model, Material, Part, box, rounded_box, cylinder, torus,
                   quad, W, D, H, R, bx, save_and_place, BLACKMET, CHROME,
                   TRIM, WIN_S, PASS_S, RAIL, _blit)
from o8kit import contact_shadow as _cs


def cshadow(m, cx, cz, rx, rz, strength=0.28):
    _cs(m, cx, cz, rx, rz, y=0.058, strength=strength, steps=7, room=(W, D))


WOODF = Material("frameoak", "#b9ab95", roughness=0.68)
MATW = Material("artmat", "#f4f2ec", roughness=0.85)
WHITE = Material("cabw", "#eeece7", roughness=0.58)
WHITE_D = Material("cabwd", "#dcd9d2", roughness=0.60)
BLACKP = Material("blackpot", "#2c2e31", roughness=0.72)
LEAF = Material("leaf", "#3d5f38", roughness=0.80)
LEAF2 = Material("leaf2", "#4d7345", roughness=0.80)
STEM = Material("stem", "#4a4238", roughness=0.80)
PEBBLE = Material("pebble", "#d9d4c8", roughness=0.90)
CANVAS = Material("canvas", "#e6e3dc", roughness=0.90)
DARKB = Material("darkbag", "#26282b", roughness=0.88)
GREYB = Material("greybag", "#8d9195", roughness=0.85)
CLEARL = Material("liner", "#e9eaea", roughness=0.45, opacity=0.55)
SILVER = Material("silverf", "#c9cbcd", roughness=0.32, metallic=0.45)
CLOCKF = Material("clockface", "#4a4d51", roughness=0.55)


# ------------------------------------------------------------------- art
def art():
    """Grid-of-specimens print, light oak frame, wide white mat -- the one
    piece of pattern the room has (photos A, C and f all centre on it)."""
    m = Model()
    cx, y0 = 5.00, 4.35
    w, h, z = 2.50, 2.70, 0.055
    bx(m, WOODF, cx - w / 2, cx + w / 2, y0, y0 + h, z, z + 0.075)
    bx(m, MATW, cx - w / 2 + 0.09, cx + w / 2 - 0.09, y0 + 0.09,
       y0 + h - 0.09, z + 0.075, z + 0.088)
    cols, rows = 13, 14
    gx0, gx1 = cx - w / 2 + 0.28, cx + w / 2 - 0.28
    gy0, gy1 = y0 + 0.32, y0 + h - 0.32
    pal = [Material("sp%d" % i, c, roughness=0.75) for i, c in enumerate(
        ("#8d6f52", "#6f8b93", "#a8563f", "#cbb478", "#4f5d63", "#9a7f9e",
         "#7d9060", "#c47a55", "#5a6a8c"))]
    k = 3
    for r in range(rows):
        for c in range(cols):
            px = gx0 + (gx1 - gx0) * (c + 0.5) / cols
            py = gy0 + (gy1 - gy0) * (r + 0.5) / rows
            k = (k * 7 + 5) % len(pal)
            sz = 0.030 + 0.008 * ((c * 3 + r * 5) % 4)
            bx(m, pal[k], px - sz, px + sz, py - sz * 1.15, py + sz * 1.15,
               z + 0.088, z + 0.098)
    return m


# ---------------------------------------------------------------- cabinet
def cabinet():
    """White beadboard two-door cabinet, south wall west of the nook opening.
    Photo A has the owner's leaf-print tote sitting on it."""
    m = Model()
    x0, x1 = 1.15, 3.40
    z0, z1 = D - 1.10, D - 0.09
    ht = 3.05
    cshadow(m, (x0 + x1) / 2, (z0 + z1) / 2, 1.35, 0.78, strength=0.30)
    bx(m, WHITE, x0, x1, 0.16, ht - 0.07, z0, z1)
    bx(m, WHITE, x0 - 0.05, x1 + 0.05, ht - 0.07, ht, z0 - 0.05, z1 + 0.03)
    bx(m, WHITE_D, x0 + 0.05, x1 - 0.05, 0.0, 0.16, z0 + 0.06, z1)
    # two doors with vertical beadboard grooves
    for d in range(2):
        dx0 = x0 + 0.07 + d * (x1 - x0 - 0.14) / 2
        dx1 = dx0 + (x1 - x0 - 0.14) / 2 - 0.05
        bx(m, WHITE, dx0, dx1, 0.28, ht - 0.20, z0 - 0.035, z0)
        n = int((dx1 - dx0) / 0.13)
        for i in range(1, n):
            gx = dx0 + i * (dx1 - dx0) / n
            bx(m, WHITE_D, gx - 0.014, gx + 0.014, 0.32, ht - 0.24,
               z0 - 0.048, z0 - 0.030)
        bx(m, CHROME, dx1 - 0.22 if d == 0 else dx0 + 0.14,
           dx1 - 0.14 if d == 0 else dx0 + 0.22, 1.55, 1.95,
           z0 - 0.075, z0 - 0.040)
    # the leaf-print tote on top
    tx = (x0 + x1) / 2 - 0.15
    bx(m, CANVAS, tx - 0.66, tx + 0.66, ht, ht + 1.05, z0 + 0.16, z0 + 0.62)
    for i, c in enumerate(("#c8443c", "#e0a12e", "#3f7d8c", "#7a9a3e",
                           "#c96aa0", "#4c4f8c")):
        col = i % 3
        row = i // 3
        m.add(rounded_box(0.20, 0.30, 0.06, r=0.06, seg=2),
              Material("leafp%d" % i, c, roughness=0.7),
              at=(tx - 0.36 + col * 0.36, ht + 0.28 + row * 0.42, z0 + 0.145))
    for s in (-1, 1):
        bx(m, DARKB, tx + s * 0.34 - 0.035, tx + s * 0.34 + 0.035,
           ht + 1.05, ht + 1.42, z0 + 0.36, z0 + 0.42)
    return m


# -------------------------------------------------------------- fiddle fig
def plant():
    """Fiddle-leaf fig, black ribbed planter on a black metal stand, white
    pebble top dressing -- SE corner, in front of the south window."""
    m = Model()
    cx, cz = 9.62, 10.30
    cshadow(m, cx, cz, 1.15, 1.15, strength=0.30)
    # stand
    for k in range(4):
        a = math.pi / 2 * k + math.pi / 4
        px, pz = cx + 0.62 * math.cos(a), cz + 0.62 * math.sin(a)
        bx(m, BLACKP, px - 0.045, px + 0.045, 0.0, 1.05, pz - 0.045, pz + 0.045)
    # ribbed planter
    seg = 16
    for i in range(seg):
        a0 = 2 * math.pi * i / seg
        a1 = 2 * math.pi * (i + 1) / seg
        r = 0.80 if i % 2 == 0 else 0.735
        p0 = (cx + r * math.cos(a0), 0, cz + r * math.sin(a0))
        p1 = (cx + r * math.cos(a1), 0, cz + r * math.sin(a1))
        m.add(Part([(p0[0], 0.62, p0[2]), (p1[0], 0.62, p1[2]),
                    (p1[0], 2.05, p1[2]), (p0[0], 2.05, p0[2])],
                   [(0, 1, 2), (0, 2, 3)]), BLACKP)
    v = [(cx, 2.02, cz)] + [(cx + 0.74 * math.cos(2 * math.pi * i / seg), 2.02,
                             cz + 0.74 * math.sin(2 * math.pi * i / seg))
                            for i in range(seg)]
    m.add(Part(v, [(0, 1 + (i + 1) % seg, 1 + i) for i in range(seg)]), PEBBLE)
    # two stems, gently curved, with a dense canopy of big fiddle leaves.
    # Everything is clamped to x < 10.42 / z < 11.30 so no leaf pokes through
    # the east wall or the nook casing.
    for (sx, sz, lx, lz, top, n) in ((-0.18, -0.12, -0.55, -0.30, 6.45, 9),
                                     (0.16, 0.10, 0.30, 0.45, 5.35, 7)):
        px, pz = cx + sx, cz + sz
        prev = (px, 2.0, pz)
        for i in range(1, n + 1):
            t = i / float(n)
            y = 2.0 + (top - 2.0) * t
            qx = px + lx * t * t
            qz = pz + lz * t * t
            bx(m, STEM, min(prev[0], qx) - 0.038, max(prev[0], qx) + 0.038,
               prev[1], y, min(prev[2], qz) - 0.038, max(prev[2], qz) + 0.038)
            if i >= 2:
                for j in range(2):
                    a = 2.1 * i + 3.0 * j
                    r = 0.40 + 0.10 * (j)
                    ly = y - 0.12 * j
                    lxx = min(10.30, max(8.90, qx + r * math.cos(a)))
                    lzz = min(11.15, max(9.20, qz + r * math.sin(a)))
                    m.add(rounded_box(0.80, 0.11, 0.58, r=0.20, seg=2),
                          LEAF if (i + j) % 2 else LEAF2,
                          at=(lxx, ly, lzz), rot_y=a, rot_z=R(20 - 12 * j))
            prev = (qx, y, qz)
    return m


# ---------------------------------------------------------------- clutter
def clutter():
    """Density.  Every critic so far has said the renders come back tidier and
    emptier than the photos; photo A's floor carries four bags and two bins."""
    m = Model()

    def bag(x, z, w, d, h, mat, handle=True, rot=0.0):
        sub = Model()
        cshadow(sub, x, z, w * 0.60, d * 0.72, strength=0.26)
        bx(sub, mat, x - w / 2, x + w / 2, 0.0, h, z - d / 2, z + d / 2)
        bx(sub, mat, x - w / 2 - 0.035, x + w / 2 + 0.035, h - 0.13, h,
           z - d / 2 - 0.035, z + d / 2 + 0.035)
        bx(sub, DARKB, x - w / 2 + 0.05, x + w / 2 - 0.05, h - 0.02, h + 0.05,
           z - d / 2 + 0.05, z + d / 2 - 0.05)
        if handle:      # one soft centred loop -- two risers and a bar
            for s in (-1, 1):
                bx(sub, DARKB, x + s * 0.22 - 0.028, x + s * 0.22 + 0.028,
                   h - 0.04, h + 0.30, z - 0.028, z + 0.028)
            bx(sub, DARKB, x - 0.25, x + 0.25, h + 0.30, h + 0.35,
               z - 0.028, z + 0.028)
        ca, sa = math.cos(rot), math.sin(rot)
        for part, mm in sub._parts:
            v = [(x + (px - x) * ca - (pz - z) * sa, py,
                  z + (px - x) * sa + (pz - z) * ca)
                 for (px, py, pz) in part.verts]
            m._parts.append((Part(v, part.tris, part.smooth), mm))

    # floor bags and totes -- photo A, in front of the cabinet and the nook
    bag(4.15, 10.50, 1.30, 0.72, 1.45, DARKB, rot=R(12))
    bag(4.95, 9.20, 1.12, 0.64, 1.32, GREYB, rot=R(-22))
    bag(6.05, 10.62, 1.00, 0.60, 1.18, CANVAS, rot=R(6))
    bag(0.95, 8.30, 1.05, 0.62, 1.25, DARKB, rot=R(-8))
    # a stack of flat boxes / binders against the south wall
    for i in range(3):
        bx(m, Material("bin%d" % i, ["#d9d5cc", "#3f4245", "#b7562f"][i],
                       roughness=0.75),
           2.05 + i * 0.03, 3.05 - i * 0.03, 0.06 + i * 0.20,
           0.24 + i * 0.20, 9.65 + i * 0.03, 10.35 - i * 0.03)
    cshadow(m, 2.55, 10.0, 0.62, 0.48, strength=0.24)

    # tall kitchen bin with a clear liner (photo A, in front of the nook)
    BIN = Material("binbody", "#c9c6c0", roughness=0.62)
    m.add(cylinder(0.46, 1.42, 14, r_top=0.50), BIN, at=(7.30, 0.0, 10.35))
    m.add(cylinder(0.53, 0.26, 14), CLEARL, at=(7.30, 1.30, 10.35))
    cshadow(m, 7.30, 10.35, 0.60, 0.60, strength=0.28)
    # the black round bin that stands out in the middle of the floor in photo C
    m.add(cylinder(0.53, 1.30, 14, r_top=0.49), DARKB, at=(6.55, 0.0, 8.55))
    m.add(cylinder(0.56, 0.10, 14), Material("binrim", "#3a3d41", roughness=0.5),
          at=(6.55, 1.24, 8.55))
    cshadow(m, 6.55, 8.55, 0.68, 0.68, strength=0.28)
    # small bin under the east desk (photo f)
    m.add(cylinder(0.30, 0.92, 12, r_top=0.34), BIN, at=(10.00, 0.0, 8.30))
    cshadow(m, 10.00, 8.30, 0.42, 0.42, strength=0.24)

    # bladeless fan at the north end of the east desk (photo f)
    fx, fz = 9.95, 1.15
    cshadow(m, fx, fz, 0.60, 0.60, strength=0.24)
    m.add(cylinder(0.42, 0.10, 14), SILVER, at=(fx, 0.0, fz))
    m.add(cylinder(0.32, 1.05, 14, r_top=0.28), SILVER, at=(fx, 0.10, fz))
    ring = Model()
    ring.add(torus(0.52, 0.075), SILVER, at=(fx, 1.85, fz))
    for part, mm in ring._parts:
        v = [(px, (py - 1.85) * 1.0 + 1.85, pz) for (px, py, pz) in part.verts]
        m._parts.append((Part(v, part.tris, part.smooth), mm))

    # wall clock + the black wall tablet, south wall west of the nook casing
    sub = Model()
    cxw = W - 4.05                      # _blit('s') frame: a = W - x
    sub.add(cylinder(0.62, 0.075, 22), CLOCKF, at=(cxw, 6.05, 0.055),
            rot_x=R(90))
    sub.add(cylinder(0.66, 0.045, 22), Material("clockrim", "#3a3d41",
                                                roughness=0.5),
            at=(cxw, 6.05, 0.040), rot_x=R(90))
    bx(sub, Material("hand", "#e7e5e0", roughness=0.5),
       cxw - 0.02, cxw + 0.02, 6.05, 6.48, 0.128, 0.148)
    bx(sub, Material("hand", "#e7e5e0", roughness=0.5),
       cxw - 0.02, cxw + 0.34, 6.03, 6.07, 0.128, 0.148)
    bx(sub, Material("tabletb", "#151618", roughness=0.35),
       cxw - 0.46, cxw + 0.46, 4.20, 4.92, 0.0, 0.055)
    bx(sub, Material("tabletf", "#26282b", roughness=0.25),
       cxw - 0.40, cxw + 0.40, 4.26, 4.86, 0.055, 0.068)
    _blit(m, sub, "s", W, D, 0.052)
    return m


if __name__ == "__main__":
    save_and_place("Office Art North", art())
    save_and_place("Office Cabinet White", cabinet())
    save_and_place("Office Plant Fig", plant())
    save_and_place("Office Clutter", clutter())
