"""Rios Room round-2 shell: ceiling + cans, baseboards, the two SOUTH-wall
window units (over real cut openings) and the two NORTH-wall doors."""

import math
from common import *   # noqa

R = math.radians


def disc_down(m, mat, cx, cz, y, r, seg=28):
    """A flat disc facing straight DOWN -- a ceiling fixture that vanishes in
    the plan view instead of leaving a white dot lying on the floor."""
    v = [(cx, y, cz)] + [(cx + r * math.cos(2 * math.pi * i / seg), y,
                          cz + r * math.sin(2 * math.pi * i / seg))
                         for i in range(seg)]
    t = [(0, 1 + i, 1 + (i + 1) % seg) for i in range(seg)]
    m.add(Part(v, t), mat)


def ring_down(m, mat, cx, cz, y, r0, r1, seg=28):
    """A flat annulus facing DOWN -- the trim ring of a recessed can."""
    v, t = [], []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        v.append((cx + r0 * math.cos(a), y, cz + r0 * math.sin(a)))
        v.append((cx + r1 * math.cos(a), y, cz + r1 * math.sin(a)))
    for i in range(seg):
        a0, b0 = 2 * i, 2 * i + 1
        a1, b1 = (2 * i + 2) % (2 * seg), (2 * i + 3) % (2 * seg)
        t += [(a0, b0, b1), (a0, b1, a1)]
    m.add(Part(v, t), mat)


# ---------------------------------------------------------------- ceiling
CANS = [(3.30, 3.20), (9.10, 3.20), (3.30, 8.30), (9.10, 8.30)]


def ceiling():
    """Flat white 8 ft ceiling, one-sided so the plan view still sees the floor.

    Kept clearly the brightest surface in the room (critic item 10): a downward
    plane collects almost no light in this renderer, so its value is
    emissive-driven.  Cans get a real trim ring + a recessed reveal + a hot
    lens (critic item 9) instead of round 1's flat white ellipse.
    """
    m = Model()
    Y = H - 0.01

    m.add(quad((0, Y, 0), (W, Y, 0), (W, Y, D), (0, Y, D)), CEIL)

    for (cx, cz) in CANS:
        ring_down(m, TRIM_FLAT, cx, cz, Y - 0.022, 0.255, 0.345)   # trim ring
        ring_down(m, CAN_CONE, cx, cz, Y - 0.070, 0.215, 0.258)    # reveal
        disc_down(m, LENS, cx, cz, Y - 0.092, 0.222)               # lens

    # smoke detector (photo 3 shows it near the middle of the ceiling)
    disc_down(m, TRIM_FLAT, 6.10, 6.05, Y - 0.055, 0.30, 22)
    disc_down(m, CAN_CONE, 6.10, 6.05, Y - 0.075, 0.11, 16)

    # HVAC supply register, 10 x 5 in, four slats -- photo 3, near the doors
    rx, rz = 5.90, 1.35
    rect_down(m, TRIM_FLAT, rx - 0.48, rx + 0.48, Y - 0.030, rz - 0.27, rz + 0.27)
    vent = Material("vent", "#c2c4c4", roughness=0.6, emissive="#8e8e8e",
                    double_sided=False)
    for i in range(4):
        z = rz - 0.19 + i * 0.126
        rect_down(m, vent, rx - 0.40, rx + 0.40, Y - 0.050, z - 0.038, z + 0.038)
    return m


# -------------------------------------------------------------- baseboards
BB_H = 0.46      # 5.5 in
BB_T = 0.075     # 0.9 in


def run(m, x0, x1, z0, z1):
    bx(m, TRIM, x0, x1, 0.0, BB_H - 0.055, z0, z1)
    cx0, cx1 = (x0, x1) if x1 - x0 > z1 - z0 else (x0 + 0.012, x1 - 0.012)
    cz0, cz1 = (z0 + 0.012, z1 - 0.012) if x1 - x0 > z1 - z0 else (z0, z1)
    bx(m, TRIM, cx0, cx1, BB_H - 0.055, BB_H, cz0, cz1)


def baseboards():
    m = Model()
    run(m, 0.0, BB_T, 0.0, D)                       # west
    run(m, W - BB_T, W, 0.0, D)                     # east
    run(m, 0.0, W, D - BB_T, D)                     # south
    # north, gapped at both door casings
    stops = [0.0, CLOSET_X[0] - CASE_W, CLOSET_X[1] + CASE_W,
             DOOR_X[0] - CASE_W, DOOR_X[1] + CASE_W, W]
    for a, b in ((stops[0], stops[1]), (stops[2], stops[3]), (stops[4], stops[5])):
        if b - a > 0.05:
            run(m, a, b, 0.0, BB_T)
    return m


# ------------------------------------------------------------------ window
def window(x0, x1, greenery=1.0, seed=918273):
    """A window unit on the SOUTH wall over a real cut opening.

    x0..x1 is the opening (which the wall shape actually removes); the casing,
    stool and apron sit on the solid wall around it.  Everything faces -z, i.e.
    into the room.

    Sizes come from the critic's measurement of the primary photo: ~4.8 ft of
    glass, sill 1.75, head 6.60, so ~1.4 ft of header above the head casing in
    an 8 ft room.  Round 1's 6.15 ft unit with a 5 in header read as a French
    door and crushed the apparent ceiling.
    """
    m = Model()
    Z = D                                   # wall plane
    zf = Z - 0.085                          # front face of the casing
    gw = x1 - x0
    rn = Rnd(seed)

    # ---- the view out: blown-out daylight with a foliage mass low down.
    #      The photo is white-hot through white blinds, NOT a green pane --
    #      round 1's scalloped green panel gave the whole wall a green cast.
    bx(m, PANE, x0, x1, SILL, HEAD, Z - 0.030, Z - 0.018)
    band = SILL + 0.46 * (HEAD - SILL)
    n_leaf = max(7, int(gw / 0.30))
    for i in range(n_leaf):
        u = rn.f()
        lx = x0 + 0.06 + (i + 0.5) * (gw - 0.12) / n_leaf
        r = (0.22 + 0.26 * u) * greenery
        ly = band + (u - 0.5) * 0.55
        if r > 0.03:
            m.add(cylinder(r, 0.008, 12, anchor="center"), LEAFOUT,
                  at=(lx, ly, Z - 0.034), rot_x=R(90))
    if greenery > 0.05:
        bx(m, LEAFOUT, x0 + 0.03, x1 - 0.03, SILL + 0.05, band,
           Z - 0.038, Z - 0.030)

    # ---- stool + apron below the opening
    bx(m, TRIM, x0 - 0.16, x1 + 0.16, SILL - 0.11, SILL, Z - 0.245, Z)
    bx(m, TRIM, x0 + 0.14, x1 - 0.14, SILL - 0.48, SILL - 0.11, Z - 0.075, Z)

    # ---- casings
    bx(m, TRIM, x0 - CASE_W, x0, SILL - 0.11, HEAD, zf, Z)
    bx(m, TRIM, x1, x1 + CASE_W, SILL - 0.11, HEAD, zf, Z)
    bx(m, TRIM, x0 - CASE_W, x1 + CASE_W, HEAD, HEAD + CASE_W, zf, Z)
    bx(m, TRIM, x0 - CASE_W - 0.07, x1 + CASE_W + 0.07,
       HEAD + CASE_W, HEAD + CASE_W + 0.12, Z - 0.175, Z)

    # ---- blinds: headrail + slats open ~28 deg, filling the opening
    bx(m, SLAT, x0 + 0.02, x1 - 0.02, HEAD - 0.22, HEAD - 0.02, Z - 0.155, Z - 0.055)
    n = int((HEAD - 0.30 - SILL - 0.06) / 0.170)
    for i in range(n):
        y = HEAD - 0.32 - i * 0.170
        m.add(box(gw - 0.05, 0.014, 0.130), SLAT,
              at=((x0 + x1) / 2, y, Z - 0.105), rot_x=R(-28))
    bot = HEAD - 0.32 - n * 0.170
    bx(m, SLAT, x0 + 0.02, x1 - 0.02, bot - 0.10, bot, Z - 0.150, Z - 0.060)
    for sx in (x0 + gw * 0.22, x1 - gw * 0.22):
        bx(m, SLAT, sx - 0.008, sx + 0.008, SILL + 0.10, HEAD - 0.22,
           Z - 0.172, Z - 0.160)
    return m


# ------------------------------------------------------------------- doors
def panel_door(m, mat, x0, x1, y0, y1, z_back, z_front, rows=3):
    """A six-panel door slab on the NORTH wall: leaf from z_back (the wall) to
    z_front (into the room), raised panels proud of z_front."""
    bx(m, mat, x0, x1, y0, y1, z_back, z_front)
    w, h = x1 - x0, y1 - y0
    sx, sy = 0.135 * w, 0.075 * h
    heights = [0.30, 0.30, 0.40] if rows == 3 else [0.45, 0.55]
    tot = sum(heights)
    y = y0 + sy
    for frac in reversed(heights):
        ph = (h - sy * (len(heights) + 1)) * frac / tot
        for cxx in ((x0 + sx, x0 + w / 2 - sx / 2), (x0 + w / 2 + sx / 2, x1 - sx)):
            # a darker reveal a hair bigger than the panel: a flat white panel
            # on a flat white leaf has no shading at all in this renderer and
            # the six-panel door reads as a blank slab
            bx(m, DOORSHADE, cxx[0] - 0.035, cxx[1] + 0.035, y - 0.035, y + ph + 0.035,
               z_front, z_front + 0.022)
            bx(m, mat, cxx[0], cxx[1], y, y + ph, z_front + 0.020, z_front + 0.062)
        y += ph + sy


def casing(m, x0, x1, top):
    for a, b in ((x0 - CASE_W, x0 + 0.03), (x1 - 0.03, x1 + CASE_W)):
        bx(m, TRIM, a, b, 0.0, top + CASE_W, 0.0, 0.19)
    bx(m, TRIM, x0 - CASE_W, x1 + CASE_W, top, top + CASE_W, 0.0, 0.19)


def entry_door():
    """Standard single door -- 2.70 x 6.75, not round 1's 3.6 x 7.1 slab."""
    m = Model()
    x0, x1 = DOOR_X
    panel_door(m, WHITEWD, x0 + 0.03, x1 - 0.03, 0.0, DOOR_TOP, 0.0, 0.145)
    casing(m, x0, x1, DOOR_TOP)
    hx = x0 + 0.36
    m.add(cylinder(0.085, 0.055, 14), BLACKMET, at=(hx, 3.05, 0.20), rot_x=R(90))
    m.add(box(0.075, 0.075, 0.30), BLACKMET, at=(hx + 0.10, 3.01, 0.34))
    return m


def closet_doors():
    m = Model()
    x0, x1 = CLOSET_X
    mid = (x0 + x1) / 2
    panel_door(m, WHITEWD, x0 + 0.03, mid - 0.02, 0.0, DOOR_TOP, 0.0, 0.135)
    panel_door(m, WHITEWD, mid + 0.02, x1 - 0.03, 0.0, DOOR_TOP, 0.0, 0.135)
    casing(m, x0, x1, DOOR_TOP)
    for hx in (mid - 0.24, mid + 0.24):
        m.add(cylinder(0.075, 0.05, 12), BLACKMET, at=(hx, 3.05, 0.19), rot_x=R(90))
    return m


if __name__ == "__main__":
    import json
    L = []
    L.append(save_and_place("Rios Ceiling", ceiling()))
    L.append(save_and_place("Rios Baseboards", baseboards()))
    L.append(save_and_place("Rios Window East", window(*WIN_E, greenery=0.95, seed=4471)))
    L.append(save_and_place("Rios Window West", window(*WIN_W, greenery=1.0, seed=918273)))
    L.append(save_and_place("Rios Door", entry_door()))
    L.append(save_and_place("Rios Closet Doors", closet_doors()))
    print(json.dumps(L, indent=1))
