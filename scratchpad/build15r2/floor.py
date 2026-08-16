"""Rios Room round-2 floor: grey LVP planks + the window light pool + a
contact shadow under every piece that meets the floor.

Three critic findings live here.
  * item 4 -- round 1 laid 15-inch planks (12 columns across 15.5 ft) in a dark,
    high-contrast palette.  The photo is ~7 in LVP in a uniform light greige,
    so: 0.583 ft planks, eight tones inside a 10-level band.
  * item 3a -- the photo's floor is a bright wash under the windows fading to
    shadow at the camera.  `POOL` bakes two trapezoids out from the window
    openings, brightest at the wall.
  * item 3b -- nothing in the house had a contact shadow, so every piece
    floated.  `SHADOWS` bakes a soft dark blob under each footprint.  The
    renderer draws no shadows for generated geometry; this is the substitute.

Layer heights: slab 0.010 | planks 0.014 | pool 0.0155.. | shadows 0.0215..
"""

import math
from common import *   # noqa

PW = 0.583         # 7 in plank
PL = 4.00
GAP = 0.016

# Tones are calibrated against the render, not picked off the photo: the app
# renders an authored sRGB value about 1.35x brighter than it is authored.  The
# primary photo measures 125 (floor near the camera) -> 158 (floor at the
# window wall); #605e5b + the pool lands at 133 -> 175.
BASE = "#4f4d4a"
TONES = ["#4f4d4a", "#4b4946", "#54524f", "#494744", "#514f4f", "#4d4b48",
         "#57544e", "#474542"]
SEAM_C = "#333130"
POOL_HI = "#6d6960"
SHADOW_C = "#26241f"

MATS = [Material(f"plank{i}", c, roughness=0.62) for i, c in enumerate(TONES)]
SEAM = Material("seam", SEAM_C, roughness=0.95)

# --- the two light pools, one per south-wall window ------------------------
# Round 2a laid these down as stacked rectangles and the outermost band's
# straight side showed as a hard line across the floor -- the same failure the
# critic killed the wall wash for.  They are a DITHERED CELL GRID now: a smooth
# 2-D falloff quantised to NLEV tones with a per-cell jitter, so the edge of
# the pool breaks up instead of drawing a rectangle.
REACH, SPREAD, PEAK = 6.20, 0.34, 1.00
NLEV, CELL = 13, 0.32
POOLS = [WIN_E, WIN_W]


def smoothstep(a, b, v):
    t = min(1.0, max(0.0, (v - a) / (b - a)))
    return t * t * (3 - 2 * t)


def pool_t(x, z):
    """Smooth strength of the baked window light at (x, z), 0..PEAK."""
    best = 0.0
    for (wx0, wx1) in POOLS:
        cx, half = (wx0 + wx1) / 2, (wx1 - wx0) / 2
        d = max(0.0, D - z)                       # distance from the wall
        az = 1.0 - smoothstep(0.0, REACH, d)      # fades away from the window
        hw = half + SPREAD * d                    # splays as it goes
        ax = 1.0 - smoothstep(hw * 0.52, hw * 1.25, abs(x - cx))
        best = max(best, PEAK * az * ax)
    return best


def superellipse(cx, cz, rx, rz, p=2.0, seg=30):
    out = []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        ca, sa = math.cos(a), math.sin(a)
        k = (abs(ca) ** p + abs(sa) ** p) ** (-1.0 / p)
        out.append((cx + rx * k * ca, cz + rz * k * sa))
    return out


def blob(m, mat, cx, cz, rx, rz, y, p=2.0):
    """A soft contact-shadow blob, clamped to the room rect so the floor
    object's bounding box stays exactly the footprint (the app seats a model by
    its bbox centre -- an overhanging shadow would shift the whole plank field).
    """
    pts = [(min(max(x, 0.0), W), min(max(z, 0.0), D))
           for (x, z) in superellipse(cx, cz, rx, rz, p)]
    v = [(min(max(cx, 0.0), W), y, min(max(cz, 0.0), D))] + [(x, y, z) for (x, z) in pts]
    n = len(pts)
    t = [(0, 1 + (i + 1) % n, 1 + i) for i in range(n)]   # facing UP
    m.add(Part(v, t), mat)


# footprint, in (cx, cz, rx, rz, superellipse power)
SHADOWS = [
    (9.90, 10.35, 1.14, 1.14, 2.0),    # pouf grey
    (4.30, 10.50, 1.02, 1.02, 2.0),    # pouf teal
    (6.50, 11.05, 1.38, 0.78, 3.5),    # ladder shelf feet + body
    (1.07,  9.00, 1.16, 1.82, 3.5),    # birdcage
    (2.65, 10.95, 0.92, 0.92, 2.0),    # rubber plant (SW)
   (11.55, 10.52, 0.92, 0.92, 2.0),    # rubber plant (SE)
   (11.90,  7.40, 0.78, 2.22, 3.5),    # console
   (11.95,  4.60, 0.60, 0.60, 2.0),    # tower fan
   (11.45,  2.95, 0.76, 0.76, 2.0),    # drum-shade lamp
    (7.60,  0.80, 0.80, 0.80, 2.0),    # snake plant
]
SH_STEPS = 9


def floor():
    m = Model()
    y0, y1 = 0.0, 0.014
    bx(m, SEAM, 0.0, W, -0.006, y0 + 0.002, 0.0, D)

    rn = Rnd(20260816)
    ncol = int(math.ceil(W / PW))
    for c in range(ncol):
        x0 = c * PW
        x1 = min(W, x0 + PW - GAP)
        if x1 - x0 < 0.05:
            continue
        off = rn.f(0.0, PL)
        z = -off
        while z < D:
            za, zb = max(0.0, z), min(D, z + PL - GAP)
            if zb - za > 0.06:
                bx(m, MATS[int(rn.f(0, len(MATS) - 0.001))], x0, x1, y0, y1, za, zb)
            z += PL

    # ---- window light pools (dithered cell grid) ----------------------------
    lev_mat = [Material(f"pool{k}", mix(BASE, POOL_HI, k / (NLEV - 1.0)),
                        roughness=0.62) for k in range(NLEV)]
    # Cells are one PLANK COLUMN wide and inset by the joint, so the pool
    # brightens the boards without painting over the seams between them.
    dr = Rnd(551133)
    nz = int(math.ceil(D / CELL))
    for c in range(int(math.ceil(W / PW))):
        x0 = c * PW
        x1 = min(W, x0 + PW - GAP)
        if x1 - x0 < 0.05:
            continue
        for iz in range(nz):
            z0, z1 = iz * CELL, min(D, (iz + 1) * CELL)
            t = pool_t((x0 + x1) / 2, (z0 + z1) / 2)
            k = int(t * (NLEV - 1) + dr.f(-0.48, 0.48) + 0.5)
            k = min(NLEV - 1, max(0, k))
            if k == 0:
                continue
            rect_up(m, lev_mat[k], x0, x1, 0.0165 + k * 0.00012, z0, z1)

    # ---- contact shadows ----------------------------------------------------
    for (cx, cz, rx, rz, p) in SHADOWS:
        under = mix(BASE, POOL_HI, pool_t(cx, cz))
        for j in range(SH_STEPS):
            f = 1.0 - 0.46 * j / (SH_STEPS - 1)
            t = 0.12 + 0.60 * j / (SH_STEPS - 1)
            mat = Material(f"sh{int(t*1000)}_{int(under[1:3],16)}",
                           mix(under, SHADOW_C, t), roughness=0.95)
            blob(m, mat, cx, cz, rx * f, rz * f, 0.0230 + j * 0.0004, p)
    return m


if __name__ == "__main__":
    m = floor()
    path = os.path.join(OUT, "rios_floor.glb")
    m.save(path)
    lo, hi = m.bounds()
    place("Rios Floor", path, ROOM, pos=(W / 2, 0.012, D / 2), rot_y_deg=0.0)
    print("Rios Floor", tuple(round(hi[i] - lo[i], 3) for i in range(3)),
          "pos", (W / 2, 0.012, D / 2))
