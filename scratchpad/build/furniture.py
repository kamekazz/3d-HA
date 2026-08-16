"""Everything that stands in the dining room: table, chairs, chandelier, rug,
clock, buffet, TV, plants, table decor.

Colours are picked off `docs/photos-jpg/Dining f.jpg`.  Each material carries a
`lift`: extra radiance per unit albedo, standing in for the bounce light the app
does not render.  Without it the espresso table and black buffet render at byte
~15 in a room whose two visible walls get no direct sun at all.
"""
import math
import sys

from dk import *  # noqa
import tone

TABLE_C = (9.0, 9.9)        # table centre, room-local
TOP_Y = 2.50
TOP_W, TOP_D = 8.0, 3.90


def fmat(name, color, rough=0.8, metal=0.0, lift=0.45, ds=True, opacity=1.0):
    A = tone.hex_to_lin(color)
    E = [c * lift / tone.EMISSIVE_SCALE for c in A]
    st = 1.0
    if max(E) > 1.0:
        st = max(E) / 0.98
        E = [c / st for c in E]
    return Material(name, color, roughness=rough, metallic=metal,
                    emissive=tone.lin_to_hex(E) if max(E) > 0.002 else None,
                    emissive_strength=st, opacity=opacity, double_sided=ds)


# ------------------------------------------------------------------ palette
ESPRESSO = fmat("espresso", "#3a3430", 0.86, lift=1.35)
ESP_DARK = fmat("esp_dark", "#282320", 0.86, lift=1.05)
FABRIC = fmat("fabric", "#726c66", 0.95, lift=0.90)
FABRIC_S = fmat("fabric_s", "#625d57", 0.95, lift=0.90)
LEGWOOD = fmat("legwood", "#312b27", 0.88, lift=1.25)
BLACKMTL = fmat("blackmtl", "#24242a", 0.68, metal=0.15, lift=1.15)
GLASSSHADE = Material("shade", "#f6f8fa", 0.55, emissive="#c2cad0",
                      emissive_strength=1.0)
WOODFACE = fmat("woodface", "#8d7156", 0.9, lift=1.55)
WHITEPAINT = fmat("whitepaint", "#f6f6f4", 0.85, lift=0.55)
SCREEN = fmat("screen", "#191b1e", 0.35, lift=0.5)
RUGPILE = fmat("rugpile", "#c0b8a9", 0.97, lift=0.0)
RUGEDGE = fmat("rugedge", "#a89d8d", 0.97, lift=0.0)
LEAF = fmat("leaf", "#7d9a6c", 0.9, lift=0.85)
LEAF2 = fmat("leaf2", "#6b8a5c", 0.9, lift=0.85)
STEM = fmat("stem", "#5d6350", 0.9, lift=0.9)
TRUNK = fmat("trunk", "#7d7367", 0.9, lift=0.7)
POTWHITE = fmat("potwhite", "#f2f1ee", 0.85, lift=0.55)
SOIL = fmat("soil", "#3a3230", 0.95, lift=0.8)
SEATFAB = fmat("seatfab", "#59544f", 0.95, lift=0.58)
CHROME = fmat("chrome", "#9ea1a3", 0.5, metal=0.4, lift=0.4)


# -------------------------------------------------------------------- table

def build_table():
    m = Model()
    cx, cz = TABLE_C
    x0, x1 = cx - TOP_W / 2, cx + TOP_W / 2
    z0, z1 = cz - TOP_D / 2, cz + TOP_D / 2
    # top: a thick plank slab with a slim shadow reveal under the edge
    add_slab(m, ESPRESSO, x0, x1, TOP_Y - 0.155, TOP_Y, z0, z1)
    add_slab(m, ESP_DARK, x0 + 0.07, x1 - 0.07, TOP_Y - 0.26, TOP_Y - 0.155,
             z0 + 0.07, z1 - 0.07)
    # plank joints, barely there
    for k in range(1, 4):
        z = z0 + TOP_D * k / 4
        add_slab(m, ESP_DARK, x0 + 0.02, x1 - 0.02, TOP_Y - 0.008, TOP_Y + 0.002,
                 z - 0.012, z + 0.012)
    # twin block pedestals
    for s in (-1, 1):
        px = cx + s * 1.92
        add_slab(m, ESPRESSO, px - 0.62, px + 0.62, 0.14, TOP_Y - 0.26,
                 cz - 1.10, cz + 1.10)
        add_slab(m, ESP_DARK, px - 0.80, px + 0.80, 0.0, 0.14, cz - 1.28, cz + 1.28)
        add_slab(m, ESP_DARK, px - s * 0.62 - 0.02, px - s * 0.62 + 0.02, 0.14,
                 TOP_Y - 0.26, cz - 1.10, cz + 1.10)
    return m


# ------------------------------------------------------------------- chairs

def chair(m, cx, cz, rot):
    """One parsons chair, authored facing +z (back to the north) then rotated."""
    r = math.radians(rot)

    def putr(w, h, d, x, y, z, mat, rad=0.09):
        p = rounded_box(w, h, d, rad, 3)
        nx = x * math.cos(r) + z * math.sin(r)
        nz = -x * math.sin(r) + z * math.cos(r)
        m.add(p, mat, at=(cx + nx, y, cz + nz), rot_y=r)

    SEAT_Y = 1.42
    # seat: one slim cushion on a thin rail
    putr(1.58, 0.22, 1.54, 0.0, SEAT_Y, 0.0, SEATFAB, rad=0.07)
    putr(1.50, 0.17, 1.46, 0.0, SEAT_Y - 0.16, 0.0, SEATFAB, rad=0.05)
    # back: one tall slim panel, slightly reclined, with a soft rolled crown
    putr(1.56, 1.79, 0.235, 0.0, SEAT_Y + 0.18, -0.645, FABRIC, rad=0.10)
    m_top = rounded_box(1.50, 0.22, 0.245, 0.11, 4)
    m.add(m_top, FABRIC, at=(cx + (-0.665) * math.sin(r), SEAT_Y + 1.90,
                             cz + (-0.665) * math.cos(r)), rot_y=r)
    # four thin tapered legs
    for sx, sz, ln in ((-1, 1, 1.11), (1, 1, 1.11), (-1, -1, 1.13), (1, -1, 1.13)):
        lx, lz = sx * 0.66, sz * 0.60
        p = cylinder(0.072, ln, 4, anchor="base", r_top=0.046)
        nx = lx * math.cos(r) + lz * math.sin(r)
        nz = -lx * math.sin(r) + lz * math.cos(r)
        m.add(p, LEGWOOD, at=(cx + nx, 0.0, cz + nz), rot_y=r + math.pi / 4)


def build_chairs():
    m = Model()
    cx, cz = TABLE_C
    for x in (cx - 2.7, cx, cx + 2.7):
        chair(m, x, cz - 2.75, 0)          # north side, back to the north wall
        chair(m, x, cz + 2.75, 180)        # south side
    chair(m, cx - 4.85, cz, 90)            # west end
    chair(m, cx + 4.85, cz, 270)           # east end
    return m


# -------------------------------------------------------------- chandelier

def build_chandelier():
    m = Model()
    cx, cz = TABLE_C
    ARM_Y, R, N = 5.45, 1.02, 6
    # hub
    m.add(cylinder(0.30, 0.20, 24), BLACKMTL, at=(cx, ARM_Y - 0.06, cz))
    m.add(cylinder(0.17, 0.14, 20, r_top=0.09), BLACKMTL, at=(cx, ARM_Y + 0.14, cz))
    for i in range(N):
        a = 2 * math.pi * i / N + math.pi / 12
        ax, az = math.cos(a), math.sin(a)
        # arm: a flat bar out to the cup
        m.add(box(R - 0.14, 0.09, 0.115), BLACKMTL,
              at=(cx + ax * (R / 2 - 0.02), ARM_Y, cz + az * (R / 2 - 0.02)),
              rot_y=-a)
        # cup + frosted cylinder shade standing on it
        m.add(cylinder(0.185, 0.10, 18), BLACKMTL,
              at=(cx + ax * R, ARM_Y + 0.075, cz + az * R))
        m.add(cylinder(0.27, 0.76, 22), GLASSSHADE,
              at=(cx + ax * R, ARM_Y + 0.16, cz + az * R))
        m.add(cylinder(0.235, 0.02, 18), GLASSSHADE,
              at=(cx + ax * R, ARM_Y + 0.16, cz + az * R))
    # stem / chain up to the medallion, plus the canopy
    for k in range(10):
        y = ARM_Y + 0.30 + k * 0.29
        m.add(torus(0.075, 0.022, 10, 6), BLACKMTL, at=(cx, y, cz),
              rot_x=math.pi / 2 if k % 2 else 0.0)
    m.add(box(0.055, 2.87, 0.055), BLACKMTL, at=(cx, ARM_Y + 0.30, cz))
    m.add(cylinder(0.29, 0.16, 20, r_top=0.20), BLACKMTL, at=(cx, 8.62, cz))
    return m


# ----------------------------------------------------------------------- rug

def ribbed(x0, x1, z0, z1, y, block=0.30, ribs=3, amp=0.008):
    """Basket-weave loop pile: square blocks of parallel ribs, alternating
    direction block by block.  A single rib direction reads as corduroy and
    moires badly against the pixel grid; the photo's rug is a basket weave.
    """
    verts, tris = [], []

    def strip(ax0, ax1, bt0, bt1, along_x):
        """One rib: a half-round ridge from bt0..bt1 across ax0..ax1."""
        bm = (bt0 + bt1) / 2
        base = len(verts)
        for (t, yy) in ((bt0, y), (bm, y + amp), (bt1, y)):
            if along_x:
                verts.append((ax0, yy, t)); verts.append((ax1, yy, t))
            else:
                verts.append((t, yy, ax0)); verts.append((t, yy, ax1))
        for k in range(2):
            a = base + 2 * k
            tris.extend([(a, a + 2, a + 3), (a, a + 3, a + 1)])

    nx = max(1, int(round((x1 - x0) / block)))
    nz = max(1, int(round((z1 - z0) / block)))
    bx, bz = (x1 - x0) / nx, (z1 - z0) / nz
    for i in range(nx):
        for j in range(nz):
            ax0, ax1 = x0 + i * bx, x0 + (i + 1) * bx
            az0, az1 = z0 + j * bz, z0 + (j + 1) * bz
            if (i + j) % 2 == 0:
                for k in range(ribs):
                    strip(ax0, ax1, az0 + k * bz / ribs, az0 + (k + 1) * bz / ribs,
                          True)
            else:
                for k in range(ribs):
                    strip(az0, az1, ax0 + k * bx / ribs, ax0 + (k + 1) * bx / ribs,
                          False)
    return Part(verts, tris)


def build_rug():
    m = Model()
    cx, cz = 9.1, 9.3
    hw, hd = 6.75, 5.3
    x0, x1, z0, z1 = cx - hw, cx + hw, cz - hd, cz + hd
    m.add(ribbed(x0 + 0.36, x1 - 0.36, z0 + 0.36, z1 - 0.36, 0.030), RUGPILE)
    # flat binding border
    add_slab(m, RUGEDGE, x0, x1, 0.004, 0.036, z0, z0 + 0.40)
    add_slab(m, RUGEDGE, x0, x1, 0.004, 0.036, z1 - 0.40, z1)
    add_slab(m, RUGEDGE, x0, x0 + 0.40, 0.004, 0.036, z0, z1)
    add_slab(m, RUGEDGE, x1 - 0.40, x1, 0.004, 0.036, z0, z1)
    return m


# --------------------------------------------------------------------- clock

def build_clock():
    m = Model()
    cx, cy, cz = 9.5, 5.60, D - 0.055
    R = 1.16
    rx = -math.pi / 2
    m.add(cylinder(R - 0.10, 0.075, 44), WOODFACE, at=(cx, cy, cz), rot_x=rx)
    # plank joints across the face
    for k in (-1, 0, 1):
        m.add(box(2 * math.sqrt(max(0.0, (R - 0.14) ** 2 - (k * 0.42) ** 2)),
                  0.018, 0.02, "center"), BLACKMTL,
              at=(cx, cy + k * 0.42, cz - 0.078))
    # black rim
    m.add(torus(R - 0.05, 0.055, 44, 8), BLACKMTL, at=(cx, cy, cz - 0.05), rot_x=rx)
    m.add(cylinder(R, 0.055, 44, r_top=R - 0.10), BLACKMTL, at=(cx, cy, cz), rot_x=rx)
    # roman numerals, abstracted to ticks
    for i in range(12):
        a = 2 * math.pi * i / 12
        rr = R - 0.30
        long_ = (i % 3 == 0)
        m.add(box(0.075, 0.30 if long_ else 0.20, 0.02, "center"), BLACKMTL,
              at=(cx + rr * math.sin(a), cy + rr * math.cos(a), cz - 0.085),
              rot_z=-a)
    # hands
    m.add(box(0.055, 0.62, 0.02, "center"), BLACKMTL,
          at=(cx + 0.11, cy + 0.28, cz - 0.10), rot_z=math.radians(-22))
    m.add(box(0.045, 0.86, 0.02, "center"), BLACKMTL,
          at=(cx - 0.24, cy - 0.33, cz - 0.10), rot_z=math.radians(35))
    m.add(cylinder(0.075, 0.03, 16), BLACKMTL, at=(cx, cy, cz - 0.115), rot_x=rx)
    return m


# -------------------------------------------------------------------- buffet

def build_buffet():
    m = Model()
    cx = 12.5
    z0, z1 = 0.10, 1.72
    x0, x1 = cx - 2.60, cx + 2.60
    add_slab(m, ESP_DARK, x0 + 0.10, x1 - 0.10, 0.0, 0.26, z0 + 0.10, z1 - 0.06)
    add_slab(m, ESP_DARK, x0 + 0.06, x1 - 0.06, 0.26, 2.78, z0 + 0.06, z1 - 0.02)
    add_slab(m, ESPRESSO, x0, x1, 2.78, 2.92, z0 - 0.03, z1 + 0.03)     # top slab
    # four door/drawer fronts with reveals
    for i in range(4):
        a = x0 + 0.16 + i * ((x1 - x0 - 0.32) / 4)
        b = a + (x1 - x0 - 0.32) / 4 - 0.07
        add_slab(m, ESPRESSO, a, b, 0.40, 1.42, z1 - 0.02, z1 + 0.02)
        add_slab(m, ESPRESSO, a, b, 1.52, 2.66, z1 - 0.02, z1 + 0.02)
        for y in (1.30, 2.52):
            add_slab(m, CHROME, (a + b) / 2 - 0.21, (a + b) / 2 + 0.21,
                     y - 0.026, y + 0.026, z1 + 0.02, z1 + 0.075)
    # what sits on it in the photo: a red rose ball, a coffee maker, a tray
    m.add(cylinder(0.30, 0.34, 20, r_top=0.26), ESP_DARK, at=(11.2, 2.92, 0.95))
    m.add(cylinder(0.42, 0.44, 22), fmat("roses", "#5e1f26", 0.9, lift=0.45),
          at=(11.2, 3.24, 0.95))
    add_slab(m, ESP_DARK, 13.55, 14.40, 2.92, 4.16, 0.62, 1.42)
    add_slab(m, CHROME, 13.60, 14.35, 3.58, 3.76, 0.58, 0.64)
    add_slab(m, WHITEPAINT, 9.9, 10.9, 2.92, 3.00, 0.75, 1.45)
    return m


# ------------------------------------------------------------------------ tv

def build_tv():
    m = Model()
    cx, y0 = 12.5, 4.36
    w, h = 4.60, 2.64
    fr = 0.10
    # frame as a border, screen proud of it -- a full frame slab in front of the
    # screen is what made round 8 render a blank white panel
    add_slab(m, SCREEN, cx - w / 2 + fr, cx + w / 2 - fr, y0 + fr, y0 + h - fr,
             0.05, 0.115)
    for (a, b, c, d) in ((cx - w / 2, cx + w / 2, y0, y0 + fr),
                         (cx - w / 2, cx + w / 2, y0 + h - fr, y0 + h),
                         (cx - w / 2, cx - w / 2 + fr, y0, y0 + h),
                         (cx + w / 2 - fr, cx + w / 2, y0, y0 + h)):
        add_slab(m, WHITEPAINT, a, b, c, d, 0.05, 0.135)
    return m


# --------------------------------------------------------------------- plants

def leaf(L, wd, th=0.026):
    # fiddle-leaf: violin outline, widest past the middle, blunt tip
    def half(u):
        return wd / 2 * math.sin(math.pi * u) ** 0.62 * (0.62 + 0.58 * u)
    pts, n = [], 12
    for i in range(n + 1):
        u = i / n
        pts.append((half(u), u * L))
    for i in range(n - 1, 0, -1):
        u = i / n
        pts.append((-half(u), u * L))
    return prism(pts, th)


def build_fig():
    """Fiddle-leaf fig in a white pot on a black stand -- the SW corner."""
    m = Model()
    cx, cz = 2.35, 12.40
    # black three-leg plant stand
    for i in range(3):
        a = 2 * math.pi * i / 3 + 0.4
        m.add(box(0.075, 1.05, 0.075), BLACKMTL,
              at=(cx + 0.52 * math.cos(a), 0.0, cz + 0.52 * math.sin(a)),
              rot_x=math.radians(9) * math.sin(a), rot_z=math.radians(-9) * math.cos(a))
    m.add(torus(0.55, 0.045, 20, 6), BLACKMTL, at=(cx, 1.02, cz))
    # pot + soil
    m.add(cylinder(0.60, 1.02, 28, r_top=0.55), POTWHITE, at=(cx, 0.98, cz))
    m.add(cylinder(0.55, 0.05, 24), SOIL, at=(cx, 1.95, cz))
    # trunk: bare for the first 3 ft, as the photo's standard-form tree is
    m.add(cylinder(0.090, 5.20, 10, r_top=0.050), TRUNK, at=(cx, 1.92, cz))
    rng = 7
    for i in range(34):
        rng = (rng * 1103515245 + 12345) % 2147483648
        t = i / 33.0
        y = 3.40 + t * 3.35 + ((rng >> 3) % 40) / 190.0
        a = 2.399963 * i + ((rng >> 11) % 100) / 260.0
        br = 0.24 + 0.95 * ((rng >> 5) % 100) / 100.0
        bx, bz = cx + br * math.cos(a), cz + br * math.sin(a)
        m.add(cylinder(0.026, br, 5), STEM, at=(cx, y, cz),
              rot_z=-math.pi / 2, rot_y=-a)
        drop = math.radians(-16 + (rng % 62))
        L = 0.74 + 0.50 * ((rng >> 17) % 100) / 100.0
        m.add(leaf(L, L * 0.70), LEAF if i % 3 else LEAF2,
              at=(bx, y - br * 0.05, bz), rot_x=drop, rot_y=-a,
              rot_z=math.radians(-34 + (rng % 69)))
    return m


def build_snake():
    """Snake plant on the floor by the east wall, as in Dining f."""
    m = Model()
    cx, cz = 16.9, 15.15
    m.add(cylinder(0.56, 0.90, 24, r_top=0.50), POTWHITE, at=(cx, 0.0, cz))
    m.add(cylinder(0.50, 0.05, 20), SOIL, at=(cx, 0.86, cz))
    for i in range(15):
        a = 2 * math.pi * i / 15 + 0.3
        r = 0.09 + 0.24 * ((i * 7) % 3) / 2.0
        h = 1.15 + 0.80 * ((i * 5) % 4) / 3.0
        blade = prism([(-0.215, -0.045), (0.215, -0.045), (0.15, 0.045),
                       (-0.15, 0.045)], h)
        m.add(blade, LEAF2 if i % 3 else LEAF,
              at=(cx + r * math.cos(a), 0.88, cz + r * math.sin(a)),
              rot_x=math.radians(13) * math.sin(a), rot_y=-a,
              rot_z=math.radians(13) * math.cos(a), scale=(1.0, 1.0, 1.0))
    return m


# ---------------------------------------------------------------- table decor

def build_decor():
    m = Model()
    # two dark oval placemats
    ox, oz = TABLE_C
    for (px, pz) in ((ox - 1.4, oz - 0.85), (ox + 1.9, oz + 0.85)):
        m.add(cylinder(0.72, 0.022, 28), ESP_DARK, at=(px, TOP_Y, pz),
              scale=(1.0, 1.0, 0.72))
    # white serving tray, west end
    tx, tz = ox - 2.85, oz
    add_slab(m, WHITEPAINT, tx - 0.82, tx + 0.82, TOP_Y, TOP_Y + 0.055,
             tz - 0.58, tz + 0.58)
    add_slab(m, WHITEPAINT, tx - 0.82, tx + 0.82, TOP_Y, TOP_Y + 0.14,
             tz - 0.58, tz - 0.52)
    add_slab(m, WHITEPAINT, tx - 0.82, tx + 0.82, TOP_Y, TOP_Y + 0.14,
             tz + 0.52, tz + 0.58)
    # paper-towel roll on a chrome post
    m.add(cylinder(0.235, 0.88, 20), WHITEPAINT, at=(tx - 0.42, TOP_Y + 0.055, tz))
    m.add(cylinder(0.30, 0.035, 20), CHROME, at=(tx - 0.42, TOP_Y + 0.05, tz))
    # two glass canisters with wooden lids
    for dx, hh in ((0.28, 0.42), (0.70, 0.30)):
        m.add(cylinder(0.20, hh, 18), fmat("glassjar", "#dfe4e6", 0.25,
                                           lift=0.8, opacity=0.55),
              at=(tx + dx, TOP_Y + 0.055, tz + 0.10))
        m.add(cylinder(0.21, 0.09, 18), WOODFACE,
              at=(tx + dx, TOP_Y + 0.055 + hh, tz + 0.10))
    return m


PIECES = {
    "Dining Table": build_table,
    "Dining Chairs": build_chairs,
    "Dining Chandelier": build_chandelier,
    "Dining Rug": build_rug,
    "Dining Clock": build_clock,
    "Dining Buffet": build_buffet,
    "Dining TV": build_tv,
    "Dining Fig Tree": build_fig,
    "Dining Snake Plant": build_snake,
    "Dining Table Decor": build_decor,
}

if __name__ == "__main__":
    want = sys.argv[1:] or list(PIECES)
    for name in list(PIECES):
        if any(w.lower() in name.lower() for w in want):
            place_local(name, PIECES[name]())
