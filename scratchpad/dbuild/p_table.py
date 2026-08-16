"""Dining Table, Dining Chairs, Dining Table Decor.

Photo B looks straight down the table's long axis at the bay: the top is a dark
espresso plank slab on two block pedestals, three parsons chairs a side and one
at each end -- eight.  Photos A/B/f all show the table loaded with everyday
clutter (paper-towel post on a white tray, wood-lidded canisters, a glass caddy,
packages, a green throw over a chair), and every critic so far has said the
renders come back tidier than the photos.  So the clutter is part of the build.
"""
import math

from dcommon import (Model, Material, box, rounded_box, cylinder, torus, quad,
                     sag_plane, ESPRESSO, ESPRESSO_D, LINEN, LINEN_D, CHROME,
                     PAPER, WOODLID, KRAFT, GREENTHROW, GLASSY, IRON,
                     TABLE_C, TABLE_W, TABLE_D, TABLE_H, CHAIRS,
                     CHAIR_W, CHAIR_D, CHAIR_SEAT, CHAIR_BACK, bx, emit)

CX, CZ = TABLE_C
PED_DX = 1.85


def build_table():
    m = Model()
    top = 0.185
    y1 = TABLE_H
    y0 = y1 - top
    # plank top: eight boards with a hairline reveal, so it is not one flat slab
    nb = 8
    bw = TABLE_D / nb
    for k in range(nb):
        z0 = CZ - TABLE_D / 2 + k * bw
        mat = ESPRESSO if k % 2 == 0 else ESPRESSO_D
        bx(m, mat, CX - TABLE_W / 2, CX + TABLE_W / 2, y0, y1,
           z0 + 0.012, z0 + bw - 0.012)
    # recessed apron under the top, and the two block pedestals
    bx(m, ESPRESSO_D, CX - TABLE_W / 2 + 0.16, CX + TABLE_W / 2 - 0.16,
       y0 - 0.155, y0, CZ - TABLE_D / 2 + 0.16, CZ + TABLE_D / 2 - 0.16)
    for s in (-1, 1):
        px = CX + s * PED_DX
        bx(m, ESPRESSO, px - 0.72, px + 0.72, 0.10, y0 - 0.155,
           CZ - 0.62, CZ + 0.62)                      # column
        bx(m, ESPRESSO_D, px - 0.86, px + 0.86, 0.0, 0.10, CZ - 0.76, CZ + 0.76)
        bx(m, ESPRESSO_D, px - 0.80, px + 0.80, y0 - 0.20, y0 - 0.155,
           CZ - 0.70, CZ + 0.70)
    return m


# --------------------------------------------------------------------------
def chair(m, cx, cz, yaw_deg):
    """One parsons chair: linen box seat, tall slightly-reclined back with a
    rolled crown, four tapered espresso legs.  Authored facing +z (back to the
    NORTH) and spun by `yaw_deg`."""
    a = math.radians(yaw_deg)
    ca, sa = math.cos(a), math.sin(a)

    def put(part, mat, lx, ly, lz, rot_x=0.0):
        m.add(part, mat, at=(cx + lx * ca + lz * sa, ly, cz - lx * sa + lz * ca),
              rot_x=rot_x, rot_y=a)

    W, D = CHAIR_W, CHAIR_D
    seat_t = 0.30
    # legs: tapered, the back pair slightly splayed
    for (lx, lz) in ((-W / 2 + 0.14, -D / 2 + 0.14), (W / 2 - 0.14, -D / 2 + 0.14),
                     (-W / 2 + 0.14, D / 2 - 0.14), (W / 2 - 0.14, D / 2 - 0.14)):
        put(box(0.135, CHAIR_SEAT - seat_t + 0.02, 0.135), ESPRESSO_D, lx, 0.0, lz)
        put(box(0.095, 0.28, 0.095), ESPRESSO_D, lx, 0.0, lz)
    # seat
    put(rounded_box(W, seat_t, D, r=0.075, seg=3), LINEN,
        0.0, CHAIR_SEAT - seat_t, 0.0)
    put(box(W - 0.06, 0.05, D - 0.06), LINEN_D, 0.0, CHAIR_SEAT - seat_t - 0.05, 0.0)
    # back: reclined 6 deg, rolled top
    bh = CHAIR_BACK - CHAIR_SEAT + 0.14
    tilt = math.radians(6.0)
    put(box(W - 0.10, bh, 0.235), LINEN, 0.0, CHAIR_SEAT - 0.14, -D / 2 + 0.19,
        rot_x=tilt)
    put(box(W - 0.10, 0.135, 0.30), LINEN_D, 0.0, CHAIR_BACK - 0.135,
        -D / 2 + 0.19 - bh * math.sin(tilt))
    # a shadow line where the back meets the seat
    put(box(W - 0.14, 0.045, 0.055), LINEN_D, 0.0, CHAIR_SEAT, -D / 2 + 0.30)


def build_chairs():
    m = Model()
    for (x, z, yaw) in CHAIRS:
        chair(m, x, z, yaw)
    # the olive throw draped over the near-side chair, exactly as photo B has it
    tx, tz, _ = CHAIRS[4]
    m.add(sag_plane(1.30, 0.95, sag=0.05, nx=6, nz=6, edge_drop=0.10),
          GREENTHROW, at=(tx, CHAIR_BACK - 0.06, tz + 0.20))
    m.add(box(1.24, 1.05, 0.075), GREENTHROW, at=(tx, CHAIR_BACK - 1.15, tz + 0.72))
    return m


# --------------------------------------------------------------------------
def build_decor():
    """What is actually sitting on the table in photos A, B and f."""
    m = Model()
    y = TABLE_H

    def placemat(px, pz):
        m.add(cylinder(0.78, 0.022, seg=22), ESPRESSO_D, at=(px, y, pz),
              scale=(1.0, 1.0, 0.72))

    placemat(CX - 1.55, CZ - 0.15)
    placemat(CX - 0.15, CZ + 0.35)

    # white serving tray with the paper-towel post and two canisters
    tx, tz = CX - 2.35, CZ - 0.10
    m.add(box(1.55, 0.055, 1.05), PAPER, at=(tx, y, tz))
    m.add(box(1.62, 0.045, 1.12), PAPER, at=(tx, y + 0.055, tz))
    m.add(cylinder(0.32, 0.030, seg=20), CHROME, at=(tx - 0.48, y + 0.10, tz - 0.18))
    m.add(cylinder(0.045, 0.98, seg=10), CHROME, at=(tx - 0.48, y + 0.10, tz - 0.18))
    m.add(cylinder(0.235, 0.70, seg=20), PAPER, at=(tx - 0.48, y + 0.14, tz - 0.18))
    for (dx, dz, h) in ((0.30, -0.22, 0.46), (0.55, 0.16, 0.34)):
        m.add(cylinder(0.185, h, seg=16), GLASSY, at=(tx + dx, y + 0.10, tz + dz))
        m.add(cylinder(0.205, 0.085, seg=16), WOODLID,
              at=(tx + dx, y + 0.10 + h, tz + dz))
    # a small glass caddy of odds and ends
    m.add(box(0.42, 0.34, 0.42), GLASSY, at=(CX - 1.05, y, CZ - 0.95))
    for k in range(5):
        m.add(cylinder(0.018, 0.52, seg=6), PAPER,
              at=(CX - 1.10 + 0.035 * k, y + 0.20, CZ - 0.95),
              rot_z=math.radians(-9 + 4.5 * k))
    # the cardboard parcel and the padded envelope photo B has at the far end
    m.add(box(1.10, 0.52, 0.78), KRAFT, at=(CX + 1.95, y, CZ + 0.42),
          rot_y=math.radians(11))
    m.add(box(0.80, 0.10, 0.58), KRAFT, at=(CX + 2.75, y, CZ - 0.55),
          rot_y=math.radians(-18))
    m.add(box(0.62, 0.16, 0.46), PAPER, at=(CX + 2.72, y + 0.10, CZ - 0.55),
          rot_y=math.radians(-18))
    # a dark bowl and a phone
    m.add(cylinder(0.28, 0.13, seg=18, r_top=0.34), ESPRESSO_D,
          at=(CX + 0.95, y, CZ - 0.62))
    m.add(box(0.30, 0.025, 0.58), IRON, at=(CX + 0.30, y, CZ - 1.15),
          rot_y=math.radians(24))
    return m


if __name__ == "__main__":
    emit(build_table(), "Dining Table", y=0.0)
    emit(build_chairs(), "Dining Chairs", y=0.0)
    emit(build_decor(), "Dining Table Decor", y=TABLE_H)
