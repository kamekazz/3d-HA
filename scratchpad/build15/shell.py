"""Rios Room shell: ceiling (the room has none), baseboards, two north
windows, the entry door and the closet doors on the south wall."""

import math
from common import *   # noqa
from roomkit.glb import Part

LAYOUT = {}


def bx(m, mat, x0, x1, y0, y1, z0, z1):
    m.add(box(x1 - x0, y1 - y0, z1 - z0), mat,
          at=((x0 + x1) / 2.0, y0, (z0 + z1) / 2.0))


def disc_down(m, mat, cx, cz, y, r, seg=28):
    """A flat disc facing straight DOWN -- a ceiling fixture that vanishes in
    the plan view instead of leaving a white dot lying on the floor."""
    v = [(cx, y, cz)] + [(cx + r * math.cos(2 * math.pi * i / seg), y,
                          cz + r * math.sin(2 * math.pi * i / seg))
                         for i in range(seg)]
    t = [(0, 1 + i, 1 + (i + 1) % seg) for i in range(seg)]
    m.add(Part(v, t), mat)


def rect_down(m, mat, x0, x1, y, z0, z1):
    m.add(quad((x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)), mat)


# ---------------------------------------------------------------- ceiling
def ceiling():
    """Flat white 8 ft ceiling, one-sided so the plan view still sees the floor.

    Recessed cans back-projected (roughly) from the primary photo: three in a
    row across the room plus one near the north wall, all of which read from
    the doorway.  Plus the flush smoke detector and the HVAC register the
    photos show.
    """
    m = Model()
    Y = H - 0.01
    # plane facing DOWN (wound clockwise seen from above)
    m.add(quad((0, Y, 0), (W, Y, 0), (W, Y, D), (0, Y, D)), CEIL)

    CANS = [(3.4, 7.0), (7.75, 7.0), (12.1, 7.0), (8.1, 1.9), (7.75, 12.9)]
    for (cx, cz) in CANS:
        disc_down(m, TRIM_FLAT, cx, cz, Y - 0.004, 0.345)
        disc_down(m, LENS, cx, cz, Y - 0.016, 0.288)

    # smoke detector
    disc_down(m, TRIM_FLAT, 5.6, 11.4, Y - 0.05, 0.30, 22)
    # HVAC supply register, 10 x 5 in, with four slats
    rx, rz = 2.3, 14.4
    rect_down(m, TRIM_FLAT, rx - 0.48, rx + 0.48, Y - 0.02, rz - 0.27, rz + 0.27)
    vent = Material("vent", "#c2c4c4", roughness=0.6, emissive="#8e8e8e",
                    double_sided=False)
    for i in range(4):
        z = rz - 0.19 + i * 0.126
        rect_down(m, vent, rx - 0.40, rx + 0.40, Y - 0.035, z - 0.038, z + 0.038)
    return m


# -------------------------------------------------------------- baseboards
BB_H = 0.46      # 5.5 in
BB_T = 0.075     # 0.9 in

# south-wall openings (no board across a door)
DOOR_X = (9.90, 12.90)      # entry, opens to the 2F hallway
CLOSET_X = (1.60, 6.60)     # closet double door
CASE_W = 0.30


def run(m, x0, x1, z0, z1):
    bx(m, TRIM, x0, x1, 0.0, BB_H - 0.055, z0, z1)
    # squeezed chamfer cap so the top edge reads as a crisp line
    cx0, cx1 = (x0, x1) if x1 - x0 > z1 - z0 else (x0 + 0.012, x1 - 0.012)
    cz0, cz1 = (z0 + 0.012, z1 - 0.012) if x1 - x0 > z1 - z0 else (z0, z1)
    bx(m, TRIM, cx0, cx1, BB_H - 0.055, BB_H, cz0, cz1)


def baseboards():
    m = Model()
    run(m, 0.0, W, 0.0, BB_T)                       # north
    run(m, 0.0, BB_T, 0.0, D)                       # west
    run(m, W - BB_T, W, 0.0, D)                     # east
    # south, gapped at both door casings
    stops = [0.0, CLOSET_X[0] - CASE_W, CLOSET_X[1] + CASE_W,
             DOOR_X[0] - CASE_W, DOOR_X[1] + CASE_W, W]
    for a, b in ((stops[0], stops[1]), (stops[2], stops[3]), (stops[4], stops[5])):
        if b - a > 0.05:
            run(m, a, b, D - BB_T, D)
    return m


# ------------------------------------------------------------------ window
def window(trim_w, trim_h=5.90, sill_y=1.55, cx=0.0):
    """A flush white window unit on the north wall (glass faces +z, into room).

    Built at north-wall z=0 in room coordinates; `cx` is its centre in local x.
    Blinds are lowered with the slats open, which is what all four photos show.
    """
    m = Model()
    cw = 0.30                                  # casing width
    gw = trim_w - 2 * cw                       # glass width
    x0, x1 = cx - trim_w / 2, cx + trim_w / 2
    gy0 = sill_y + 0.51                        # top of the stool
    gy1 = gy0 + trim_h - 0.91                  # under the head casing

    # ---- the view through the glass: bright sky + a mass of foliage
    bx(m, GLASSLIT, x0 + cw, x1 - cw, gy0, gy1, 0.004, 0.014)
    # foliage: one continuous canopy across the lower-middle of the pane, built
    # from overlapping discs so its top edge is lumpy instead of a straight line
    rnd = 918273
    band = gy0 + 0.80 * (gy1 - gy0)
    n_leaf = max(8, int(gw / 0.24))
    for i in range(n_leaf):
        rnd = (rnd * 1103515245 + 12345) % (1 << 31)
        u = ((rnd >> 9) % 1000) / 1000.0
        lx = x0 + cw + 0.05 + (i + 0.5) * (gw - 0.10) / n_leaf
        r = 0.30 + 0.30 * u
        ly = band + (u - 0.5) * 0.75
        m.add(cylinder(r, 0.010, 12, anchor="center"), LEAFOUT,
              at=(lx, ly, 0.016), rot_x=math.radians(90))
    # solid ground of foliage under the canopy
    bx(m, LEAFOUT, x0 + cw + 0.02, x1 - cw - 0.02, gy0 + 0.02, band, 0.014, 0.022)

    # ---- apron, stool
    bx(m, TRIM, x0 + 0.28, x1 - 0.28, sill_y, sill_y + 0.40, 0.0, 0.055)
    bx(m, TRIM, x0 - 0.06, x1 + 0.06, sill_y + 0.40, sill_y + 0.51, 0.0, 0.185)
    # ---- side casings
    bx(m, TRIM, x0, x0 + cw, gy0, gy1, 0.0, 0.062)
    bx(m, TRIM, x1 - cw, x1, gy0, gy1, 0.0, 0.062)
    # ---- head casing + crown cap
    bx(m, TRIM, x0, x1, gy1, gy1 + 0.30, 0.0, 0.070)
    bx(m, TRIM, x0 - 0.07, x1 + 0.07, gy1 + 0.30, gy1 + 0.40, 0.0, 0.115)

    # ---- blind: headrail + open slats
    bx(m, SLAT, x0 + cw + 0.02, x1 - cw - 0.02, gy1 - 0.20, gy1 - 0.02, 0.020, 0.115)
    n = int((gy1 - 0.24 - gy0 - 0.05) / 0.163)
    for i in range(n):
        y = gy1 - 0.30 - i * 0.163
        m.add(box(gw - 0.05, 0.014, 0.125), SLAT,
              at=((x0 + x1) / 2, y, 0.072), rot_x=math.radians(26))
    # bottom rail
    bx(m, SLAT, x0 + cw + 0.02, x1 - cw - 0.02,
       gy1 - 0.30 - n * 0.163 - 0.10, gy1 - 0.30 - n * 0.163, 0.025, 0.110)
    # lift cords
    for sx in (cx - gw * 0.28, cx + gw * 0.28):
        bx(m, SLAT, sx - 0.008, sx + 0.008, gy0 + 0.05, gy1 - 0.20, 0.130, 0.142)
    return m


# ------------------------------------------------------------------- doors
def panel_door(m, mat, x0, x1, y0, y1, zf, zb, rows=3):
    """A six-panel door slab: flat leaf plus raised panels on the room face."""
    bx(m, mat, x0, x1, y0, y1, zf, zb)
    w, h = x1 - x0, y1 - y0
    sx, sy = 0.135 * w, 0.075 * h
    heights = [0.30, 0.30, 0.40] if rows == 3 else [0.45, 0.55]
    tot = sum(heights)
    y = y0 + sy
    for k, frac in enumerate(reversed(heights)):
        ph = (h - sy * (len(heights) + 1)) * frac / tot
        for cxx in ((x0 + sx, x0 + w / 2 - sx / 2), (x0 + w / 2 + sx / 2, x1 - sx)):
            bx(m, mat, cxx[0], cxx[1], y, y + ph, zf - 0.028, zf)
        y += ph + sy


def entry_door():
    m = Model()
    x0, x1 = DOOR_X
    top = 6.80
    zb, zf = D, D - 0.145          # slab: back at the wall, face into the room
    panel_door(m, WHITEWD, x0 + 0.03, x1 - 0.03, 0.0, top, zf, zb)
    # casing
    bx(m, TRIM, x0 - CASE_W, x0 + 0.03, 0.0, top + CASE_W, D - 0.055, D)
    bx(m, TRIM, x1 - 0.03, x1 + CASE_W, 0.0, top + CASE_W, D - 0.055, D)
    bx(m, TRIM, x0 - CASE_W, x1 + CASE_W, top, top + CASE_W, D - 0.055, D)
    # lever handle
    hx = x0 + 0.36
    m.add(cylinder(0.085, 0.055, 14), BLACKMET, at=(hx, 3.05, zf - 0.03), rot_x=math.radians(90))
    m.add(box(0.075, 0.075, 0.30), BLACKMET, at=(hx - 0.10, 3.01, zf - 0.17))
    return m


def closet_doors():
    m = Model()
    x0, x1 = CLOSET_X
    top = 6.80
    zb, zf = D, D - 0.135
    mid = (x0 + x1) / 2
    panel_door(m, WHITEWD, x0 + 0.03, mid - 0.02, 0.0, top, zf, zb, rows=3)
    panel_door(m, WHITEWD, mid + 0.02, x1 - 0.03, 0.0, top, zf, zb, rows=3)
    bx(m, TRIM, x0 - CASE_W, x0 + 0.03, 0.0, top + CASE_W, D - 0.055, D)
    bx(m, TRIM, x1 - 0.03, x1 + CASE_W, 0.0, top + CASE_W, D - 0.055, D)
    bx(m, TRIM, x0 - CASE_W, x1 + CASE_W, top, top + CASE_W, D - 0.055, D)
    for hx in (mid - 0.24, mid + 0.24):
        m.add(cylinder(0.075, 0.05, 12), BLACKMET,
              at=(hx, 3.05, zf - 0.03), rot_x=math.radians(90))
    return m


if __name__ == "__main__":
    import json
    L = []
    L.append(save_and_place("Rios Ceiling", ceiling()))
    L.append(save_and_place("Rios Baseboards", baseboards()))
    L.append(save_and_place("Rios Window West", window(4.50, trim_h=6.15, sill_y=1.40, cx=3.05)))
    L.append(save_and_place("Rios Window East", window(3.60, trim_h=6.15, sill_y=1.40, cx=10.35)))
    L.append(save_and_place("Rios Door", entry_door()))
    L.append(save_and_place("Rios Closet Doors", closet_doors()))
    print(json.dumps(L, indent=1))
