"""Room 13 -- the east wall (black double dresser + round mirror + its top
clutter), the south wall (wall TV, two small frames), the north wall wreath,
the west wall collage, and the sheepskin rug.
"""

import math

from gkit import *

rnd = Rnd(90211)

BLK = Material("gblk", "#1d1d20", roughness=0.52)
BLK2 = Material("gblk2", "#26262a", roughness=0.52)
BLK3 = Material("gblk3", "#141416", roughness=0.55)
WHITE = Material("gwhite", "#c3c0ba", roughness=0.72)
POT = Material("gpot", "#bab8b3", roughness=0.68)
LEAF = Material("gleaf", "#6d7d61", roughness=0.90, double_sided=True)
LEAF2 = Material("gleaf2", "#849377", roughness=0.90, double_sided=True)
SOIL = Material("gsoil", "#3f3a34", roughness=0.98)
SILVER = Material("gsilver", "#c8c9c6", roughness=0.35, metallic=0.45)
SCREEN = Material("gscreen", "#101215", roughness=0.22, metallic=0.10)
BOX = Material("gboxwd", "#4e6149", roughness=0.93, double_sided=True)
BOX2 = Material("gboxwd2", "#5f7154", roughness=0.93, double_sided=True)
BOXD = Material("gboxwd3", "#3b4d38", roughness=0.93, double_sided=True)
MATB = Material("gmat", "#c8c6c1", roughness=0.80)
FRM = Material("gfrm", "#242427", roughness=0.55)
FUR = Material("gfur", "#6a6967", roughness=0.99, double_sided=True)
FUR2 = Material("gfur2", "#726e67", roughness=0.99, double_sided=True)

DX0, DX1, DZ0, DZ1 = DRESSER            # 10.82 12.36 1.90 6.80
DH = 2.92                                # dresser carcase height


# ------------------------------------------------------------------ dresser
def dresser():
    """Black six-drawer double dresser on the EAST wall, its front facing west.
    Photo 2: three rows of two drawers, round knobs, a plinth base."""
    m = Model()
    cz = (DZ0 + DZ1) / 2
    bx(m, BLK, DX0, DX1, 0.28, DH, DZ0, DZ1)
    bx(m, BLK2, DX0 - 0.045, DX1, DH, DH + 0.075, DZ0 - 0.045, DZ1 + 0.045)
    bx(m, BLK3, DX0 + 0.10, DX1, 0.0, 0.28, DZ0 + 0.10, DZ1 - 0.10)   # plinth
    dh = (DH - 0.42) / 3.0
    for r in range(3):
        y = 0.36 + r * dh
        for c in range(2):
            za = DZ0 + 0.07 + c * ((DZ1 - DZ0 - 0.21) / 2 + 0.07)
            zb = za + (DZ1 - DZ0 - 0.21) / 2
            bx(m, BLK3, DX0 - 0.012, DX0 - 0.008, y - 0.03, y + dh - 0.09,
               za - 0.035, zb + 0.035)
            bx(m, BLK2, DX0 - 0.038, DX0 - 0.012, y, y + dh - 0.12, za, zb)
            for k in (0.30, 0.70):
                m.add(cylinder(0.062, 0.075, 10), BLACKMET,
                      at=(DX0 - 0.043, y + (dh - 0.12) * 0.5,
                          za + (zb - za) * k), rot_z=R(90))
    # ---- top clutter (photo 1): white tray, black lantern, potted plant
    bx(m, WHITE, DX0 + 0.30, DX0 + 0.92, DH + 0.075, DH + 0.14, cz - 1.62, cz - 0.96)
    bx(m, Material("gtray2", "#dcdad5", roughness=0.7),
       DX0 + 0.36, DX0 + 0.86, DH + 0.11, DH + 0.15, cz - 1.56, cz - 1.02)
    # small white drum lamp (photo 1: the lit shade at the dresser's far end)
    lx, lz = DX0 + 0.66, cz - 0.10
    m.add(cylinder(0.26, 0.055, 14), BLACKMET, at=(lx, DH + 0.075, lz))
    m.add(cylinder(0.062, 0.72, 10), BLACKMET, at=(lx, DH + 0.13, lz))
    m.add(cylinder(0.44, 0.72, 20, r_top=0.38),
          Material("gdshade", "#c9c6c0", roughness=0.85), at=(lx, DH + 0.78, lz))
    disc_down(m, Material("gdbulb", "#fff6e2", roughness=0.3, emissive="#ffeec8",
                          emissive_strength=1.8), lx, lz, DH + 0.80, 0.36, 14)
    # black metal photo frame leaning behind the tray
    bx(m, BLACKMET, DX0 + 0.14, DX0 + 0.18, DH + 0.075, DH + 0.86,
       cz - 1.52, cz - 0.92)
    bx(m, Material("gdphoto", "#8b8e92", roughness=0.7),
       DX0 + 0.18, DX0 + 0.19, DH + 0.13, DH + 0.80, cz - 1.46, cz - 0.98)
    # potted rubber plant at the north end (photo 1's variegated rubber tree)
    px, pz = DX0 + 0.60, DZ0 + 0.62
    m.add(cylinder(0.42, 0.78, 16, r_top=0.36), POT, at=(px, DH + 0.075, pz))
    disc_down(m, SOIL, px, pz, DH + 0.83, 0.35, 12)
    for i in range(20):
        h = rnd.f(0.25, 1.45)
        a = rnd.f(0, 6.283)
        bx(m, Material("gstem", "#41402f", roughness=0.9),
           px - 0.020, px + 0.020, DH + 0.78, DH + 0.78 + h,
           pz - 0.020, pz + 0.020)
        sc = rnd.f(0.55, 0.92)
        lq = [(0.0, -0.07 * sc, 0.0), (0.20 * sc, 0.22 * sc, 0.0),
              (0.13 * sc, 0.62 * sc, 0.0), (0.0, 0.76 * sc, 0.0),
              (-0.13 * sc, 0.62 * sc, 0.0), (-0.20 * sc, 0.22 * sc, 0.0)]
        m.add(Part(lq, [(0, 1, 2), (0, 2, 3), (0, 3, 4), (0, 4, 5)], smooth=True),
              LEAF if i % 2 else LEAF2,
              at=(px + rnd.f(-0.30, 0.30), DH + 0.74 + h, pz + rnd.f(-0.28, 0.28)),
              rot_x=R(rnd.f(-38, 38)), rot_y=a, rot_z=R(rnd.f(-50, 50)))
    shadow(m, rect_foot(DX0 - 0.05, W - 0.05, DZ0, DZ1), pad=0.62, a0=0.42,
           tag="dr")
    return m


# ------------------------------------------------------------------- mirror
def mirror():
    """The thin round mirror over the dresser (photo 2).  Its face is the -x
    side; it reflects the west wall, which is why it reads as glass."""
    m = Model()
    import math as _m
    cz, cy, rr = (DZ0 + DZ1) / 2, 5.18, 1.14
    RIM = Material("gmirrim", "#dedcd6", roughness=0.55)
    GL = Material("gmirglass", "#b9c3ca", roughness=0.10, metallic=0.30)
    n = 40
    # a FLAT disc facing -x, not a cylinder: roomkit's cylinder() smooth-shades
    # its caps, so the first pass rendered the mirror as a white beach ball.
    for (rad, xoff, mat) in ((rr, 0.070, RIM), (rr - 0.085, 0.052, GL)):
        v = [(W - xoff, cy, cz)] + [
            (W - xoff, cy + rad * _m.sin(2 * _m.pi * i / n),
             cz + rad * _m.cos(2 * _m.pi * i / n)) for i in range(n)]
        m.add(Part(v, [(0, 1 + i, 1 + (i + 1) % n) for i in range(n)]), mat)
    # rim band so it is a mirror with thickness, not a decal
    for i in range(n):
        a0 = 2 * _m.pi * i / n
        a1 = 2 * _m.pi * (i + 1) / n
        p0 = (W - 0.070, cy + rr * _m.sin(a0), cz + rr * _m.cos(a0))
        p1 = (W - 0.070, cy + rr * _m.sin(a1), cz + rr * _m.cos(a1))
        q0 = (W - 0.008, p0[1], p0[2])
        q1 = (W - 0.008, p1[1], p1[2])
        m.add(Part([p0, p1, q1, q0], [(0, 2, 1), (0, 3, 2)], smooth=True), RIM)
    return m


# ----------------------------------------------------------------------- TV
def tv():
    """Wall-mounted panel on the SOUTH wall east of the closet (photo 2)."""
    m = Model()
    x0, x1, y0, y1 = 8.98, 12.16, 4.52, 6.34
    bx(m, BLK3, x0, x1, y0, y1, D - 0.115, D - 0.075)
    bx(m, SCREEN, x0 + 0.055, x1 - 0.055, y0 + 0.05, y1 - 0.05,
       D - 0.128, D - 0.116)
    bx(m, BLK3, (x0 + x1) / 2 - 0.42, (x0 + x1) / 2 + 0.42, y0 - 0.16, y0,
       D - 0.09, D - 0.055)
    return m


# ------------------------------------------------------------------- wreath
def wreath():
    """Boxwood wreath centred over the headboard on the NORTH wall."""
    m = Model()
    cx, cy, r = (BED[0] + BED[1]) / 2, 5.72, 0.78
    m.add(torus(r, 0.155, 24, 7), BOXD, at=(cx, cy, 0.185), rot_x=R(90))
    # flat tilted leaf quads, not prisms -- 4 verts each instead of 8, and the
    # first pass read as a smooth green donut because the torus dominated
    for i in range(170):
        a = rnd.f(0, 6.283)
        rad = r + rnd.f(-0.235, 0.235)
        w2, h2 = rnd.f(0.045, 0.085), rnd.f(0.055, 0.105)
        q = [(-w2, -h2, 0.0), (w2, -h2, 0.0), (w2, h2, 0.0), (-w2, h2, 0.0)]
        m.add(Part(q, [(0, 1, 2), (0, 2, 3)], smooth=True),
              (BOX2 if i % 3 == 0 else (BOX if i % 3 == 1 else BOXD)),
              at=(cx + rad * math.cos(a), cy + rad * math.sin(a),
                  0.075 + rnd.f(0.0, 0.20)),
              rot_x=R(rnd.f(-42, 42)), rot_y=R(rnd.f(-46, 46)),
              rot_z=R(rnd.f(0, 360)))
    return m


# ---------------------------------------------------------------------- art
def framed(m, plane, a, y, w, h, mat_ground, depth, dark=None, seed=3):
    """A framed picture on a wall plane. `plane` is ('w',x) ('n',z) or ('s',z);
    `a` is the along-wall coordinate."""
    r = Rnd(seed)
    def put(mat, a0, a1, y0, y1, d0, d1):
        if plane[0] == "w":
            bx(m, mat, plane[1] + d0, plane[1] + d1, y0, y1, a0, a1)
        elif plane[0] == "s":
            bx(m, mat, a0, a1, y0, y1, plane[1] - d1, plane[1] - d0)
        else:
            bx(m, mat, a0, a1, y0, y1, plane[1] + d0, plane[1] + d1)
    put(FRM, a - w / 2, a + w / 2, y - h / 2, y + h / 2, 0.0, depth)
    put(mat_ground, a - w / 2 + 0.075, a + w / 2 - 0.075,
        y - h / 2 + 0.075, y + h / 2 - 0.075, depth - 0.012, depth + 0.004)
    if dark:
        for i in range(6):
            aw = w * r.f(0.10, 0.20)
            ah = h * r.f(0.14, 0.26)
            ca = a + r.f(-w * 0.28, w * 0.28)
            cy = y + r.f(-h * 0.24, h * 0.24)
            put(dark, ca - aw / 2, ca + aw / 2, cy - ah / 2, cy + ah / 2,
                depth + 0.004, depth + 0.010)


def art_west():
    """The collage frame on the WEST wall south of the window (photo 1)."""
    m = Model()
    framed(m, ("w", 0.0), 5.75, 5.02, 1.62, 1.32, MATB, 0.075,
           dark=Material("gcol", "#6e7276", roughness=0.8), seed=11)
    return m


def art_south():
    """The pair of small frames on the SOUTH wall west of the closet (photo 3)."""
    m = Model()
    for i, a in enumerate((1.20, 2.55)):
        framed(m, ("s", D), a, 5.05, 0.82, 1.02, MATB, 0.070,
               dark=Material("gcol2", "#57585c", roughness=0.8), seed=21 + i)
    return m


# ---------------------------------------------------------------------- rug
def rug():
    """The white faux-sheepskin between the bed and the dresser (photo 1): a
    two-lobe outline, not a rectangle, with a nubbed pile field on it."""
    m = Model()
    cx, cz = 9.55, 5.55
    # union of two overlapping ovals -- photo 1's sheepskin is two lobes with
    # a waist between them, not an ellipse
    lobes = [(cx - 0.10, cz - 1.05, 1.02, 1.45), (cx + 0.12, cz + 1.15, 0.94, 1.35)]
    pts = []
    n = 64
    for i in range(n):
        t = 2 * math.pi * i / n
        ux, uz = math.sin(t), math.cos(t)
        best = None
        for (lx, lz, rx, rz) in lobes:
            # ray from the rug centre, distance to this lobe's boundary
            A = (ux / rx) ** 2 + (uz / rz) ** 2
            B = 2 * ((cx - lx) * ux / rx ** 2 + (cz - lz) * uz / rz ** 2)
            C = ((cx - lx) / rx) ** 2 + ((cz - lz) / rz) ** 2 - 1.0
            disc = B * B - 4 * A * C
            if disc < 0:
                continue
            s_ = (-B + math.sqrt(disc)) / (2 * A)
            best = s_ if best is None else max(best, s_)
        r_ = (best or 1.0) * (1.0 + 0.035 * math.sin(7 * t))
        pts.append((cx + ux * r_, cz + uz * r_))
    m.add(Part([(p[0], 0.030, p[1]) for p in pts],
               [(0, 1 + i, i) for i in range(1, n - 1)]), FUR)
    # A sheepskin is an inch of shaggy pile, not a pile of boulders.  Round 1
    # used 240 puffs 0.06 ft tall and read as rubble; round 2 used flat quads
    # tilted +/-13 deg and read as crumpled paper, because with one overhead
    # sun a 13 deg tilt is a 40-byte value swing.  These are FLAT and LEVEL --
    # every quad faces +Y, so its rendered value tracks its albedo and the
    # metered sd can be aimed at the photo's.
    tones = [Material("gfurm%d" % k, c, roughness=0.99, double_sided=True)
             for k, c in enumerate(ramp("#6a6967", 5, 4))]
    for i in range(430):
        j = 0 if rnd.f(0, 1) < 0.5 else 1
        lx, lz, rx, rz = lobes[j]
        t = rnd.f(0, 6.283)
        s = math.sqrt(rnd.f(0.0, 1.0)) * 0.92
        px = lx + rx * s * math.sin(t)
        pz = lz + rz * s * math.cos(t)
        w2, d2 = rnd.f(0.075, 0.145), rnd.f(0.075, 0.145)
        q = [(-w2, 0.0, -d2), (w2, 0.0, -d2), (w2, 0.0, d2), (-w2, 0.0, d2)]
        m.add(Part(q, [(0, 2, 1), (0, 3, 2)], smooth=True),
              tones[int(rnd.f(0, 4.999))],
              at=(px, 0.0325, pz),
              rot_y=R(rnd.f(0, 90)))
    shadow(m, [(p[0], p[1]) for p in pts[::4]], pad=0.34, a0=0.20,
           core=False, tag="rug")
    return m


if __name__ == "__main__":
    print("room 13 pieces")
    save_and_place("Guest Dresser", dresser())
    save_and_place("Guest Mirror Round", mirror())
    save_and_place("Guest TV", tv())
    save_and_place("Guest Wreath", wreath())
    save_and_place("Guest Art West", art_west())
    save_and_place("Guest Art South", art_south())
    save_and_place("Guest Floor Rug", rug(), fname="guest_floor_rug")
