"""Architecture: the sectional door leaf, the service door, and the steps.

Both door pieces carry a word WALL_ARCH_RE matches ("door", "panel"), so
cutaway.js binds each to the wall it pierces and fades it with that wall
instead of leaving a leaf standing in the gap.

On the sectional door: the whole-house shell GLB models this door on the
EXTERIOR.  No opening is cut in room 7's south wall, so there is nothing for
the two to mis-register against -- this leaf is a separate mesh flush to the
INSIDE face of a solid wall, which is also physically right: a real sectional
door hangs inboard of the opening on its tracks, roughly one wall thickness
(house.js WALL_THICKNESS = 0.35 ft) behind the exterior face.
"""
import json
import math
import urllib.request

from gk import *   # noqa: F401,F403
import gk as G

TRACK = Material("gtrack", "#a8adb0", roughness=0.38, metallic=0.55)
SPRING = Material("gspring", "#212327", roughness=0.50, metallic=0.35)
LEAF = Material("gleaf", "#f4f3ef", roughness=0.58)
LEAFJ = Material("gleafj", "#d8d6d0", roughness=0.60)      # section joint shadow
HDW = Material("ghdw", "#26282b", roughness=0.42, metallic=0.40)


# ------------------------------------------------------- the sectional door
def door_panel():
    """16 x 7 ft flat white sectional, 4 sections, 3 galvanised struts.

    Photo 5 shows this door head on: it is FLAT -- no raised panels and, against
    the task brief, NO row of windows.  The four horizontal lines are the
    section joints and the light band at the top is the top section catching the
    header light, not glazing.
    """
    m = Model()
    x0, x1 = BAY_X0, BAY_X1
    zi = D - 0.34                        # inside face of the leaf
    t = 0.14
    secs = 4
    sh = BAY_TOP / secs
    for i in range(secs):
        y0, y1 = i * sh, (i + 1) * sh
        bx(m, LEAF, x0, x1, y0 + 0.035, y1 - 0.035, zi - t, zi)
        bx(m, LEAFJ, x0, x1, y1 - 0.035, y1 + 0.035, zi - t + 0.03, zi - 0.015)
    bx(m, LEAFJ, x0, x1, 0.0, 0.035, zi - t + 0.03, zi - 0.015)     # bottom seal

    # vertical reinforcement struts, on the inside face
    for u in (4.0, 8.0, 12.0):
        x = x0 + u
        bx(m, TRACK, x - 0.11, x + 0.11, 0.10, BAY_TOP - 0.10, zi, zi + 0.055)
        for i in range(1, secs):                                     # hinges
            bx(m, HDW, x - 0.15, x + 0.15, i * sh - 0.10, i * sh + 0.10,
               zi + 0.055, zi + 0.10)

    # vertical tracks either side, and the rollers' brackets
    for x in (x0 - 0.20, x1 + 0.20):
        bx(m, TRACK, x - 0.07, x + 0.07, 0.0, BAY_TOP + 0.55, zi - 0.02, zi + 0.22)

    # torsion tube + centre bearing plate + the black spring, above the head
    yt = BAY_TOP + 0.42
    # rot_z = -pi/2 (not +): the rotation runs before the translate, so +pi/2
    # sweeps the tube out to -X and the piece's bbox balloons to 34 ft.
    m.add(cylinder(0.055, x1 - x0 + 0.9, 10), TRACK,
          at=(x0 - 0.45, yt, zi + 0.10), rot_z=-math.pi / 2)
    xc = (x0 + x1) / 2
    bx(m, TRACK, xc - 0.30, xc + 0.30, yt - 0.30, yt + 0.30, zi + 0.04, zi + 0.16)
    m.add(cylinder(0.115, 2.6, 10), SPRING,
          at=(xc + 0.32, yt, zi + 0.10), rot_z=-math.pi / 2)
    m.add(cylinder(0.115, 2.0, 10), SPRING,
          at=(xc - 2.32, yt, zi + 0.10), rot_z=-math.pi / 2)
    # cable drums
    for x in (x0 - 0.32, x1 + 0.32):
        m.add(cylinder(0.16, 0.24, 10), TRACK, at=(x, yt - 0.12, zi + 0.10))
    return m


# ----------------------------------------------------------- service door
WREATH_G = [Material("gwr%d" % i, c, roughness=0.85)
            for i, c in enumerate(("#4e7048", "#3d5c39", "#5f8253", "#2f4a2d"))]


def entry_door():
    """Six-panel leaf detail, casing and the green wreath, on the north wall.

    house.js already draws a plain white box in the opening; this sits 0.11 ft
    proud of it so the two cannot z-fight, and adds what the box has not got --
    the stiles and rails of a six-panel door, the casing, the black lever and
    deadbolt, and the wreath from photo 6.
    """
    m = Model()
    y0 = 1.25                       # the opening is raised to the house floor
    x0, x1 = DOOR_X0, DOOR_X1
    hh = 6.75
    zf = NF                         # the furred north face (gk.NF)

    # jamb linings through the 0.42 ft reveal the furring makes
    for (a, b) in ((x0 - 0.06, x0 + 0.03), (x1 - 0.03, x1 + 0.06)):
        bx(m, TRIMS, a, b, y0, y0 + hh + 0.03, 0.06, zf)
    bx(m, TRIMS, x0 - 0.06, x1 + 0.06, y0 + hh, y0 + hh + 0.06, 0.06, zf)
    bx(m, TRIMW, x0 - 0.06, x1 + 0.06, y0 - 0.09, y0, 0.06, zf + 0.05)   # sill

    # casing: 3 1/2 in flat stock round the opening
    for (a, b) in ((x0 - 0.35, x0 - 0.02), (x1 + 0.02, x1 + 0.35)):
        bx(m, TRIMW, a, b, y0 - 0.02, y0 + hh + 0.35, zf, zf + 0.06)
    bx(m, TRIMW, x0 - 0.35, x1 + 0.35, y0 + hh + 0.02, y0 + hh + 0.35,
       zf, zf + 0.06)

    # leaf: fills the reveal so the engine's own white panel behind it never
    # shows, with the stiles and rails standing proud of the face.
    bx(m, DOORW, x0 + 0.02, x1 - 0.02, y0, y0 + hh, 0.09, zf)
    STILES = ((0.02, 0.42), (1.30, 1.70), (2.58, 2.98))     # left, muntin, right
    RAILS = ((0.00, 0.52), (2.72, 3.12), (4.62, 5.02), (6.35, 6.75))
    for (a, b) in RAILS:
        bx(m, DOORW, x0 + 0.02, x1 - 0.02, y0 + a, y0 + b, zf, zf + 0.035)
    for (a, b) in STILES:
        bx(m, DOORW, x0 + a, x0 + b, y0, y0 + hh, zf, zf + 0.035)
    for (ya, yb) in ((0.52, 2.72), (3.12, 4.62), (5.02, 6.35)):
        for (xa, xb) in ((0.42, 1.30), (1.70, 2.58)):
            bx(m, DOORP, x0 + xa, x0 + xb, y0 + ya, y0 + yb,
               zf - 0.055, zf - 0.012)

    # hardware: black lever + deadbolt on the strike side (photo 6: handle left)
    bx(m, BLKM, x0 + 0.28, x0 + 0.46, y0 + 2.98, y0 + 3.22, zf, zf + 0.10)
    m.add(cylinder(0.05, 0.32, 8), BLKM, at=(x0 + 0.37, y0 + 3.10, zf + 0.10),
          rot_x=math.pi / 2)
    m.add(cylinder(0.11, 0.06, 10), BLKM, at=(x0 + 0.37, y0 + 3.62, zf + 0.06))

    # wreath -- 2.1 ft of eucalyptus on the upper panel
    cx, cy = (x0 + x1) / 2.0, y0 + 4.75
    for i in range(34):
        a = 2 * math.pi * i / 34
        rr = 0.86 + 0.06 * math.sin(a * 3.0)
        m.add(rounded_box(0.34, 0.30, 0.26, 0.10, 2), WREATH_G[i % 4],
              at=(cx + rr * math.cos(a), cy + rr * math.sin(a) - 0.15, zf + 0.12),
              rot_y=a)
    return m


# ------------------------------------------------------------------ steps
MAT_RUB = Material("gmatr", "#3b3b3c", roughness=0.88)
MAT_SQ = Material("gmatsq", "#57565a", roughness=0.85)
MAT_BR = Material("gmatbr", "#2b2b2c", roughness=0.95)


def steps():
    """Two painted treads up to the door, white rails both sides, doormats.

    Photo 6: the garage slab sits two risers below the house floor.  Room 7's
    slab is flat in this app (all first-floor rooms share slab Y 8), so the
    step is built as a platform and the door opening is raised to meet it.
    """
    m = Model()
    cx = (DOOR_X0 + DOOR_X1) / 2.0
    wid = 4.55
    x0, x1 = cx - wid / 2, cx + wid / 2
    RISE = 0.625

    # lower tread, then the landing at the threshold
    for i, (z1, y) in enumerate(((2.62, RISE), (1.42, 2 * RISE))):
        bx(m, TRIMW, x0, x1, y - 0.10, y, 0.0, z1)              # tread
        bx(m, TRIMS, x0, x1, 0.0, y - 0.10, z1 - 0.09, z1)      # riser
        bx(m, TRIMW, x0 - 0.02, x1 + 0.02, y - 0.115, y - 0.10,
           z1 - 0.11, z1 + 0.04)                                # nosing

    # side rails: newel posts + a top rail, as in photo 6
    for sx in (x0 + 0.09, x1 - 0.09):
        for z in (0.30, 2.35):
            bx(m, TRIMW, sx - 0.09, sx + 0.09, 2 * RISE, 2 * RISE + 2.25,
               z - 0.09, z + 0.09)
        bx(m, TRIMW, sx - 0.075, sx + 0.075, 2 * RISE + 2.10, 2 * RISE + 2.25,
           0.24, 2.45)
        bx(m, TRIMW, sx - 0.055, sx + 0.055, 2 * RISE + 0.95, 2 * RISE + 1.05,
           0.30, 2.40)

    # the grid scraper mat at the foot of the steps (photo 6)
    mz0, mz1 = 2.72, 4.28
    mx0, mx1 = cx - 1.55, cx + 1.55
    bx(m, MAT_RUB, mx0, mx1, 0.0, 0.055, mz0, mz1)
    for i in range(8):
        for j in range(3):
            ax = mx0 + 0.10 + i * (mx1 - mx0 - 0.20) / 8
            az = mz0 + 0.10 + j * (mz1 - mz0 - 0.20) / 3
            bx(m, MAT_SQ, ax, ax + 0.26, 0.055, 0.075, az, az + 0.30)

    # the second, bristly mat under the banner (photo 1)
    bx(m, MAT_BR, 8.45, 11.85, 0.0, 0.05, 0.28, 2.05)
    return m


def raise_opening():
    """Lift opening 4 to the house floor level so the door sits on the landing.

    Nothing is on the other side of this wall in the model (the strip at world
    x 21.9-28.5, z 3.1-13.0 is unmodelled), so there is no neighbour opening to
    keep registered with -- this is room 7's own wall only.
    """
    body = json.dumps({"elevation": 1.25, "height": 6.75, "width": 3.0,
                       "offset": 3.53}).encode()
    req = urllib.request.Request(BASE + "/api/house/opening/4", data=body,
                                 method="PATCH")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as r:
        print("  opening 4 ->", r.read().decode()[:80])


if __name__ == "__main__":
    raise_opening()
    save_and_place("Garage Door Panel", door_panel())
    save_and_place("Garage Entry Door", entry_door())
    save_and_place("Garage Steps", steps())
