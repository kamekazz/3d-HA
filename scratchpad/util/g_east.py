"""Garage -- EAST wall run + loose kit.

The floor plan shows two blobs hard against the garage's east wall (local
z 3.4-5.6 and z 16.2-18.6).  What they *are* is not readable from the plan and
there is no interior photo, so the identification (water heater at the north
blob, wheelie bins at the south blob, next to the sectional door) is inference
from normal construction practice, not measurement.
"""
from gkit import *   # noqa: F401,F403
import gkit as G

ROOM = 7
EW = 20.4          # east wall
CEIL = 8.87


def water_heater():
    """North-east floor-plan blob (local z 3.4-5.6).  INFERRED."""
    m = Model()
    cx, cz = EW - 1.20, 4.50
    m.add(cylinder(1.02, 0.22, 22), G.STEEL_D, at=(cx, 0.0, cz))       # drain pan
    m.add(cylinder(0.90, 4.55, 22), G.WHITE_A, at=(cx, 0.22, cz))
    m.add(cylinder(0.90, 0.30, 22, r_top=0.60), G.WHITE_A, at=(cx, 4.77, cz))
    m.add(cylinder(0.28, 0.55, 12), G.STEEL, at=(cx, 5.07, cz))        # flue collar
    m.add(cylinder(0.24, CEIL - 5.62, 12), G.STEEL, at=(cx, 5.62, cz))  # vent
    # supply / return copper
    for dz in (-0.42, 0.42):
        m.add(cylinder(0.075, 1.30, 10), G.ORANGE, at=(cx + 0.55, 5.00, cz + dz))
    bx(m, G.ORANGE, cx + 0.48, EW - 0.06, 6.22, 6.37, cz - 0.50, cz + 0.50)
    # controls + label plate
    bx(m, G.BLK, cx - 0.98, cx - 0.62, 0.75, 1.55, cz - 0.34, cz + 0.34)
    bx(m, G.STEEL_D, cx - 0.96, cx - 0.66, 2.60, 3.30, cz - 0.26, cz + 0.26)
    return m


def freezer():
    m = Model()
    z0, z1 = 6.30, 10.80
    x0, x1 = EW - 2.45, EW - 0.12
    m.add(rounded_box(x1 - x0, 2.62, z1 - z0, 0.12, 3), G.WHITE,
          at=((x0 + x1) / 2, 0.0, (z0 + z1) / 2))
    bx(m, G.BLK, x0 + 0.05, x1 - 0.05, 0.0, 0.22, z0 + 0.05, z1 - 0.05)
    bx(m, G.WHITE_A, x0 + 0.03, x1 - 0.03, 2.62, 2.78, z0 + 0.03, z1 - 0.03)  # lid
    bx(m, G.CHR, x0 + 0.10, x0 + 0.32, 2.36, 2.52, z0 + 1.55, z1 - 1.55)      # handle
    bx(m, G.BLK, x0 + 0.12, x0 + 0.42, 1.90, 2.14, z1 - 0.85, z1 - 0.35)      # dial
    # boxes stacked on the lid
    bx(m, G.CARD, x0 + 0.35, x0 + 1.75, 2.78, 3.62, z0 + 0.35, z0 + 1.85)
    bx(m, G.CARD, x0 + 0.50, x0 + 1.60, 3.62, 4.22, z0 + 0.50, z0 + 1.70)
    bx(m, G.PLAS_G, x0 + 0.45, x1 - 0.30, 2.78, 3.55, z1 - 1.95, z1 - 0.40)
    bx(m, G.YELLOW, x0 + 0.42, x1 - 0.27, 3.55, 3.66, z1 - 1.98, z1 - 0.37)
    return m


def mower():
    m = Model()
    cx, cz = EW - 1.35, 13.30
    m.add(rounded_box(1.85, 0.62, 2.15, 0.16, 3), G.REDD, at=(cx, 0.52, cz))
    for dx, dz, r in ((-0.80, -0.85, 0.40), (0.80, -0.85, 0.40),
                      (-0.82, 0.88, 0.50), (0.82, 0.88, 0.50)):
        m.add(cylinder(r, 0.26, 14, anchor="center"), G.BLKR,
              at=(cx + dx, r, cz + dz), rot_z=G.R(90))
    m.add(cylinder(0.42, 0.70, 14), G.BLK, at=(cx - 0.10, 1.14, cz - 0.15))
    m.add(cylinder(0.26, 0.30, 12), G.STEEL, at=(cx + 0.42, 1.14, cz + 0.10))
    for dx in (-0.72, 0.72):
        m.add(box(0.10, 2.85, 0.10), G.BLK, at=(cx + dx, 0.72, cz + 0.72),
              rot_x=G.R(-34))
    bx(m, G.BLK, cx - 0.80, cx + 0.80, 2.98, 3.10, cz + 2.28, cz + 2.42)
    # bagger
    m.add(rounded_box(1.35, 1.00, 0.95, 0.20, 3), G.GREEN, at=(cx, 0.75, cz + 1.55))
    # red gas can beside it
    bx(m, G.RED, cx + 1.00, cx + 1.72, 0.0, 1.05, cz - 1.70, cz - 1.00)
    m.add(cylinder(0.10, 0.45, 10), G.YELLOW, at=(cx + 1.36, 1.05, cz - 1.55))
    # leaf blower
    m.add(cylinder(0.34, 1.35, 14), G.ORANGE, at=(cx - 1.05, 0.34, cz + 1.75),
          rot_z=G.R(72))
    return m


def bins():
    """South-east floor-plan blob (local z 16.2-18.6), beside the sectional door."""
    m = Model()
    for (cz, body, lid) in ((16.05, G.PLAS_G, G.BLK),
                            (18.15, G.PLAS_G, G.BLUE),
                            (20.25, G.PLAS_G, G.GREEN)):
        cx = EW - 1.22
        m.add(rounded_box(2.05, 3.05, 1.95, 0.16, 3), body, at=(cx, 0.22, cz))
        m.add(box(2.12, 0.16, 2.02), lid, at=(cx, 3.27, cz))
        bx(m, lid, cx - 1.06, cx - 0.96, 3.27, 3.46, cz - 0.95, cz + 0.95)
        for dz in (-0.80, 0.80):
            m.add(cylinder(0.24, 0.20, 12, anchor="center"), G.BLKR,
                  at=(cx - 0.86, 0.24, cz + dz), rot_z=G.R(90))
    # recycling crate on the floor in front
    bx(m, G.BLUE, EW - 3.85, EW - 2.55, 0.0, 1.05, 16.60, 18.10)
    return m


def bike():
    """Against the north wall, east of the person door."""
    m = Model()
    cx, cz, cy = 16.60, 0.72, 0.0
    for dx, r in ((-2.10, 1.08), (2.10, 1.08)):
        m.add(torus(r, 0.075, 20, 7), G.BLKR, at=(cx + dx, r + 0.06, cz), rot_x=G.R(90))
        m.add(torus(r * 0.45, 0.035, 16, 6), G.CHR, at=(cx + dx, r + 0.06, cz), rot_x=G.R(90))
        m.add(cylinder(0.10, 0.16, 10, anchor="center"), G.CHR,
              at=(cx + dx, r + 0.06, cz), rot_z=G.R(90))
    import math
    F = Material("bikefr", "#2f6f8f", roughness=0.4, metallic=0.35)
    for (ax, ay, bxx, byy) in ((-2.10, 1.08, -0.35, 2.35), (-0.35, 2.35, 0.85, 2.30),
                               (0.85, 2.30, 2.10, 1.08), (-0.35, 2.35, 0.15, 1.05),
                               (0.15, 1.05, 2.10, 1.08), (0.15, 1.05, 0.85, 2.30),
                               (-2.10, 1.08, 0.15, 1.05)):
        dx_, dy = bxx - ax, byy - ay
        L = (dx_ ** 2 + dy ** 2) ** 0.5
        # box() spans y 0..L about the origin; rot_z maps +Y onto (dx,dy)
        m.add(box(0.10, L, 0.10), F, at=(cx + ax, cy + ay, cz),
              rot_z=math.atan2(-dx_, dy))
    bx(m, G.BLK, cx - 0.55, cx + 0.05, 2.42, 2.58, cz - 0.30, cz + 0.30)   # saddle
    bx(m, G.BLK, cx + 0.70, cx + 1.00, 2.52, 2.62, cz - 0.95, cz + 0.95)   # bars
    m.add(cylinder(0.055, 0.85, 10), G.CHR, at=(cx + 0.85, 2.30, cz))
    m.add(cylinder(0.30, 0.10, 14, anchor="center"), G.BLK,
          at=(cx + 0.15, 1.05, cz + 0.14), rot_z=G.R(90))                  # chainring
    # helmet + a kick scooter parked beside it
    m.add(cylinder(0.42, 0.34, 14, r_top=0.30), G.RED, at=(cx - 2.60, 0.0, cz + 0.15))
    bx(m, G.STEEL_D, cx + 3.10, cx + 4.55, 0.30, 0.42, cz - 0.16, cz + 0.16)
    m.add(cylinder(0.055, 2.55, 10), G.STEEL_D, at=(cx + 4.42, 0.30, cz), rot_z=G.R(-12))
    bx(m, G.BLK, cx + 3.55, cx + 4.30, 2.60, 2.72, cz - 0.55, cz + 0.55)
    for dx in (3.20, 4.45):
        m.add(cylinder(0.30, 0.14, 12, anchor="center"), G.BLKR,
              at=(cx + dx, 0.30, cz), rot_z=G.R(90))
    return m


def ladder():
    """Extension ladder + shop vac + broom, leaning on the WEST wall (south end)."""
    m = Model()
    # built upright at the origin, then tipped about Z so the top leans west
    def rails(h, rung_n, halfz, mat, rung_h=0.10):
        s = Model()
        for dz in (-halfz, halfz):
            s.add(box(0.14, h, 0.26), mat, at=(0.0, 0.0, dz))
        for i in range(rung_n):
            y = 0.60 + i * (h - 0.9) / max(1, rung_n - 1)
            s.add(box(0.12, rung_h, halfz * 2 - 0.24), mat, at=(0.0, y, 0.0))
        return s

    for (sub, at, tilt) in ((rails(7.85, 8, 0.72, G.SILV_D), (1.62, 0.0, 20.05), G.R(8)),
                            (rails(5.60, 5, 0.60, G.ORANGE), (2.05, 0.0, 18.15), G.R(7))):
        for part, mat in sub._parts:
            m.add(part, mat, at=at, rot_z=tilt)
    # shop vac
    m.add(cylinder(0.72, 1.55, 18), G.STEEL_D, at=(3.70, 0.0, 20.80))
    m.add(cylinder(0.74, 0.55, 18, r_top=0.55), G.RED, at=(3.70, 1.55, 20.80))
    m.add(torus(0.55, 0.11, 16, 7), G.BLK, at=(3.70, 1.40, 20.80), rot_x=G.R(90))
    # broom + push brush
    m.add(cylinder(0.055, 4.55, 8), G.OAKEDGE, at=(0.62, 0.0, 16.20), rot_z=G.R(-7))
    bx(m, G.BLK, 0.42, 0.90, 0.0, 0.40, 16.02, 16.40)
    return m


if __name__ == "__main__":
    tot = 0
    tot += G.save_and_place("Garage Water Heater", water_heater(), ROOM)
    tot += G.save_and_place("Garage Freezer", freezer(), ROOM)
    tot += G.save_and_place("Garage Mower", mower(), ROOM)
    tot += G.save_and_place("Garage Bins", bins(), ROOM)
    tot += G.save_and_place("Garage Bike", bike(), ROOM)
    tot += G.save_and_place("Garage Ladder", ladder(), ROOM)
    print("  east/loose total %.1f KB" % tot)
