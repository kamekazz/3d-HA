"""Dining Chandelier, Dining Clock, Dining Fig Tree, Dining Snake Plant,
Dining Vents.
"""
import math

from dcommon import (Model, Material, box, rounded_box, cylinder, prism, torus,
                     quad, IRON, SHADE, CLOCKFACE, TRIM, TRIM_SH, GREY_MET,
                     LEAF, LEAF_L, STEM, SOIL, POT, ESPRESSO_D, krng,
                     TABLE_C, TABLE_H, RECESS_Y, CLOCK_X, CLOCK_Y, CLOCK_R,
                     FIG, SNAKE, ZW_SOUTH, XW_WEST, EDGES, E_WSOUTH, on_edge,
                     bx, emit)

CX, CZ = TABLE_C


# --------------------------------------------------------------------------
def build_chandelier():
    """Black six-arm fixture with frosted cylinder shades standing on the arms,
    ~2.9 ft of clear air over the table top (photos A, B, f)."""
    m = Model()
    body_y = 5.42
    m.add(cylinder(0.14, 0.30, seg=14), IRON, at=(CX, body_y, CZ))
    m.add(cylinder(0.26, 0.075, seg=16, r_top=0.10), IRON, at=(CX, body_y - 0.075, CZ))
    R = 1.06
    for k in range(6):
        a = 2 * math.pi * k / 6.0 + 0.26
        ax, az = CX + R * math.cos(a), CZ + R * math.sin(a)
        # arm: a flat bar out to the socket, with a small upturn
        m.add(box(R, 0.075, 0.105), IRON,
              at=(CX + R / 2 * math.cos(a), body_y + 0.02, CZ + R / 2 * math.sin(a)),
              rot_y=-a)
        m.add(cylinder(0.075, 0.20, seg=10), IRON, at=(ax, body_y + 0.095, az))
        m.add(cylinder(0.275, 0.76, seg=18), SHADE, at=(ax, body_y + 0.29, az))
        m.add(cylinder(0.285, 0.03, seg=18), TRIM, at=(ax, body_y + 0.28, az))
    # chain + rod up to the canopy at the tray recess
    for k in range(11):
        y = body_y + 0.30 + k * 0.29
        if y > RECESS_Y - 0.32:
            break
        m.add(torus(0.070, 0.021, seg=10, ring=6), IRON, at=(CX, y, CZ),
              rot_x=math.pi / 2 if k % 2 else 0.0)
    m.add(cylinder(0.030, RECESS_Y - body_y - 0.30, seg=8), IRON,
          at=(CX, body_y + 0.30, CZ))
    m.add(cylinder(0.32, 0.16, seg=18, r_top=0.20), IRON, at=(CX, RECESS_Y - 0.16, CZ))
    return m


# --------------------------------------------------------------------------
def build_clock():
    """2.3 ft round wall clock: black rim and Roman ticks over a planked
    natural-wood face, centred between the two front-facade windows."""
    m = Model()
    # INTO the room is -z here (the wall plane is z = 13.12), so the back of the
    # clock is the LARGEST z.  The first pass had the rim in front of the planks
    # and the whole clock rendered as a black bulge.
    zb = ZW_SOUTH - 0.055          # back plate
    zp = zb - 0.055                # plank face
    zr = zp - 0.045                # rim + ticks
    m.add(cylinder(CLOCK_R + 0.02, 0.055, seg=44), IRON, at=(CLOCK_X, CLOCK_Y, zb),
          rot_x=math.pi / 2)
    # planked natural-wood face
    n = 7
    for k in range(n):
        t = (k + 0.5) / n * 2 - 1
        w = 2 * math.sqrt(max(0.0, 1.0 - t * t)) * CLOCK_R * 0.985
        yy = CLOCK_Y - CLOCK_R + (k + 0.5) * 2 * CLOCK_R / n
        mat = CLOCKFACE if k % 2 == 0 else Material("clockface2", "#bba689",
                                                    roughness=0.88)
        bx(m, mat, CLOCK_X - w / 2, CLOCK_X + w / 2,
           yy - CLOCK_R / n * 0.94, yy + CLOCK_R / n * 0.94, zp, zb)
    # thin black rim ring
    m.add(torus(CLOCK_R - 0.030, 0.055, seg=48, ring=8), IRON,
          at=(CLOCK_X, CLOCK_Y, zp - 0.010), rot_x=math.pi / 2)
    # Roman numeral ticks around a hairline inner ring
    m.add(torus(CLOCK_R * 0.60, 0.016, seg=34, ring=6), IRON,
          at=(CLOCK_X, CLOCK_Y, zr + 0.012), rot_x=math.pi / 2)
    for k in range(12):
        a = 2 * math.pi * k / 12.0
        r = CLOCK_R * 0.79
        m.add(box(0.055, 0.22, 0.020), IRON,
              at=(CLOCK_X + r * math.sin(a), CLOCK_Y + r * math.cos(a), zr),
              rot_z=-a)
    # hands
    m.add(box(0.052, 0.58, 0.022), IRON, at=(CLOCK_X, CLOCK_Y, zr - 0.022),
          rot_z=math.radians(-38))
    m.add(box(0.038, 0.84, 0.022), IRON, at=(CLOCK_X, CLOCK_Y, zr - 0.022),
          rot_z=math.radians(112))
    m.add(cylinder(0.065, 0.045, seg=12), IRON, at=(CLOCK_X, CLOCK_Y, zr - 0.045),
          rot_x=math.pi / 2)
    return m


# --------------------------------------------------------------------------
def leafblade(m, mat, x, y, z, ang, tilt, L, W):
    """One violin/blade leaf as a tapered quad pair."""
    ca, sa = math.cos(ang), math.sin(ang)
    ct, st = math.cos(tilt), math.sin(tilt)
    pts = [(0.0, 0.0, 0.0), (W * 0.55, L * 0.28, 0.0), (W * 0.42, L * 0.66, 0.0),
           (W * 0.62, L * 0.86, 0.0), (0.0, L, 0.0), (-W * 0.62, L * 0.86, 0.0),
           (-W * 0.42, L * 0.66, 0.0), (-W * 0.55, L * 0.28, 0.0)]
    P = []
    for (px, py, _pz) in pts:
        yy = py * ct
        zz = py * st
        P.append((x + px * ca - zz * sa, y + yy, z + px * sa + zz * ca))
    for k in range(1, len(P) - 1):
        m.add(quad(P[0], P[k], P[k + 1], P[k + 1]), mat)


def build_fig():
    """Fiddle-leaf fig in a white pot on a black three-leg stand, in the corner
    where the front wall meets the bay (photos A and f)."""
    m = Model()
    fx, fz = FIG
    # stand
    for k in range(3):
        a = 2 * math.pi * k / 3.0 + 0.4
        m.add(box(0.075, 1.05, 0.075), IRON,
              at=(fx + 0.42 * math.cos(a), 0.0, fz + 0.42 * math.sin(a)),
              rot_z=math.radians(6 * math.cos(a)), rot_x=math.radians(-6 * math.sin(a)))
    m.add(torus(0.44, 0.035, seg=20, ring=6), IRON, at=(fx, 0.98, fz))
    m.add(torus(0.34, 0.030, seg=18, ring=6), IRON, at=(fx, 0.28, fz))
    # pot
    m.add(cylinder(0.50, 0.86, seg=22, r_top=0.56), POT, at=(fx, 0.92, fz))
    m.add(cylinder(0.53, 0.06, seg=22), SOIL, at=(fx, 1.72, fz))
    # trunk + branches + leaves
    m.add(cylinder(0.085, 3.95, seg=8, r_top=0.055), STEM, at=(fx, 1.74, fz))
    r = krng(4041)
    for k in range(42):
        t = k / 41.0
        y = 3.20 + t * 2.95
        a = 2.399963 * k
        reach = 0.55 + 1.35 * (0.30 + 0.70 * math.sin(math.pi * t))
        bxp, bzp = fx + reach * 0.40 * math.cos(a), fz + reach * 0.40 * math.sin(a)
        m.add(cylinder(0.032, reach * 0.55, seg=6), STEM,
              at=(fx, y, fz), rot_z=math.radians(-58 * math.cos(a)),
              rot_x=math.radians(58 * math.sin(a)))
        L = 0.80 + 0.40 * r()
        leafblade(m, LEAF if k % 3 else LEAF_L, bxp, y + 0.05, bzp,
                  a, math.radians(44 + 30 * r()), L, L * 0.70)
    return m


def build_snake():
    """Snake plant in a white pot, standing beside the foyer opening (photo f)."""
    m = Model()
    sx, sz = SNAKE
    m.add(cylinder(0.44, 0.82, seg=20, r_top=0.50), POT, at=(sx, 0.0, sz))
    m.add(cylinder(0.47, 0.05, seg=20), SOIL, at=(sx, 0.80, sz))
    r = krng(1717)
    for k in range(24):
        a = 2.399963 * k
        L = 1.05 + 0.95 * r()
        leafblade(m, LEAF if k % 3 else LEAF_L,
                  sx + 0.20 * math.cos(a), 0.80, sz + 0.20 * math.sin(a),
                  a, math.radians(5 + 19 * r()), L, 0.155)
    return m


# --------------------------------------------------------------------------
def build_vents():
    """A dark floor register near the front wall (photo B) and a white wall
    register on the short west wall (photo f)."""
    m = Model()
    bx(m, GREY_MET, 4.05, 5.15, 0.028, 0.048, 12.30, 12.86)
    for k in range(9):
        z = 12.36 + k * 0.058
        bx(m, ESPRESSO_D, 4.10, 5.10, 0.048, 0.056, z, z + 0.030)
    x, z = on_edge(E_WSOUTH, 1.55, 0.055)
    m.add(box(0.98, 0.62, 0.05), TRIM, at=(x, 0.72, z), rot_y=EDGES[E_WSOUTH]["rot"])
    for k in range(7):
        m.add(box(0.88, 0.026, 0.045), TRIM_SH,
              at=(x, 0.80 + k * 0.072, z), rot_y=EDGES[E_WSOUTH]["rot"])
    return m


if __name__ == "__main__":
    emit(build_chandelier(), "Dining Chandelier", y=5.42 - 0.075)
    emit(build_clock(), "Dining Clock")
    emit(build_fig(), "Dining Fig Tree", y=0.0)
    emit(build_snake(), "Dining Snake Plant", y=0.0)
    emit(build_vents(), "Dining Vents", y=0.028)
