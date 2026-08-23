# ================================================================== cabinets
# ROUND 3.  Round 2's uprights were the same box seven times with the hue
# swapped -- three flat colour fields (marquee / screen / lower panel) and a
# control panel that projected 0.06 ft past the carcase.  Both are fixed here:
#
#   * the body is a SWEPT SIDE PROFILE (a2kit.sweep), so the silhouette is real
#     geometry: base, apron, a control deck standing 0.70 ft proud of the
#     carcase front, a raked screen face, a marquee that overhangs, a stepped
#     or straight head.  Four profiles, and width / height / deck height /
#     marquee depth all vary per machine, so no two read alike end-on.
#   * every visible panel carries PRINTED ARTWORK from the shared RGB atlas
#     (a2kit.ART_TEX) rather than a hue: both flanks, the lower front panel and
#     the marquee title band each take their own tile.
#
# It is also five times cheaper -- ~160 verts a machine against ~850 for the
# box stack -- which is what buys the north wall inside the payload cap.

DECK_OUT = 0.70                     # control-deck projection past the carcase

STYLES = ("straight", "slope", "step", "riser")


def _profile(bd, top, style, dy, mqh, seed=0):
    """The (z, y) side profile of one machine, CCW, front at +z."""
    hd = bd / 2.0
    back = -hd
    fb = hd - 0.30                  # carcase front
    fd = fb + DECK_OUT              # deck front -- the number round 2 got wrong
    ft = hd - 0.62                  # screen / marquee plane
    mq_lo = top - mqh - 0.18
    mq_hi = top - 0.18
    base = [(back, 0.0), (fb, 0.0), (fb, dy - 0.55),
            (fd, dy - 0.26), (fd, dy), (ft, dy + 0.06)]
    if style == "slope":
        head = [(ft - 0.34, mq_lo - 0.06), (ft + 0.05, mq_lo),
                (ft + 0.05, mq_hi), (ft - 0.18, top), (back, top)]
    elif style == "step":
        head = [(ft, mq_lo - 0.10), (ft - 0.40, mq_lo - 0.10),
                (ft - 0.40, top), (back, top)]
    elif style == "riser":
        head = [(ft - 0.20, mq_lo - 0.30), (ft + 0.10, mq_lo - 0.22),
                (ft + 0.10, mq_hi + 0.10), (ft - 0.26, top), (back, top)]
    else:                                                    # straight
        head = [(ft, mq_hi + 0.06), (ft - 0.06, top), (back, top)]
    return base + head, (fb, fd, ft, mq_lo, mq_hi, dy)


def upright(m, cx, cz, rot, art_i, bw=2.20, bd=2.55, top=6.10, seed=1,
            style="straight", dy=2.52, mqh=0.62, mq_i=0, art_f=None,
            plinth=0.0):
    """One arcade cabinet, authored facing +z then spun by `rot` degrees."""
    sub = Model()
    rnd = Rnd(seed)
    prof, (fb, fd, ft, mq_lo, mq_hi, dy) = _profile(bd, top, style, dy, mqh, seed)
    x0, x1 = -bw / 2.0, bw / 2.0
    art_f = art_i if art_f is None else art_f
    if plinth:                                  # a raised base, some machines
        bx(sub, CABDK, x0 - 0.01, x1 + 0.01, 0.0, plinth, -bd / 2, fb)
        prof = [(z, y + plinth) for (z, y) in prof]
        mq_lo += plinth
        mq_hi += plinth
        dy += plinth
    sweep(sub, prof, x0, x1, ART, CABBLK, uvr(art_i))

    # printed lower front panel (its own tile, so the flanks and the face are
    # not the same graphic)
    zf = fb + 0.008
    uvq(sub, ART, [(x0 + 0.08, plinth + 0.16, zf), (x1 - 0.08, plinth + 0.16, zf),
                   (x1 - 0.08, dy - 0.62, zf), (x0 + 0.08, dy - 0.62, zf)],
        uvr(art_f))
    # a coin door, dead centre, low
    bx(sub, CPANEL, -0.34, 0.34, plinth + 0.30, plinth + 0.92, zf, zf + 0.055)
    bx(sub, CHR, -0.26, 0.26, plinth + 0.52, plinth + 0.60, zf + 0.055, zf + 0.07)

    # control deck: joysticks + buttons on the projecting top
    dz0, dz1 = ft + 0.18, fd - 0.14
    bx(sub, CPANEL, x0 + 0.04, x1 - 0.04, dy - 0.02, dy + 0.012, dz0 - 0.10, dz1)
    for k in range(2):
        jx = (-0.28 + 0.56 * k) * (bw / 2.20)
        bx(sub, CHR, jx - 0.045, jx + 0.045, dy + 0.012, dy + 0.20,
           dz0 + 0.16, dz0 + 0.25)
        bx(sub, BUTTONS[k], jx - 0.065, jx + 0.065, dy + 0.20, dy + 0.25,
           dz0 + 0.145, dz0 + 0.265)
        for b in range(3):
            bxx = jx + 0.20 + b * 0.145
            rect_up(sub, BUTTONS[(k + b) % 4], bxx - 0.055, bxx + 0.055,
                    dy + 0.018, dz0 + 0.10 + 0.055 * (b % 2),
                    dz0 + 0.21 + 0.055 * (b % 2))

    # raked screen in a dark bezel, on the profile's screen plane
    sz = ft - (0.30 if style == "slope" else 0.04)
    bx(sub, CABDK, x0 + 0.05, x1 - 0.05, dy + 0.30, mq_lo - 0.10,
       sz - 0.10, sz - 0.03)
    uvq(sub, SCRN, [(x0 + 0.17, dy + 0.42, sz - 0.028),
                    (x1 - 0.17, dy + 0.42, sz - 0.028),
                    (x1 - 0.17, mq_lo - 0.22, sz - 0.028),
                    (x0 + 0.17, mq_lo - 0.22, sz - 0.028)], uvr(12 + mq_i % 4))
    # marquee -- a real backlit lamp in the photos, so legitimately emissive,
    # and it carries a printed title band rather than a colour field
    mz = ft + (0.06 if style in ("slope", "riser") else 0.0)
    bx(sub, CABDK, x0 + 0.02, x1 - 0.02, mq_lo - 0.05, mq_hi + 0.05,
       mz - 0.075, mz - 0.02)
    uvq(sub, MQ_MATS[mq_i % 4],
        [(x0 + 0.06, mq_lo, mz - 0.015), (x1 - 0.06, mq_lo, mz - 0.015),
         (x1 - 0.06, mq_hi, mz - 0.015), (x0 + 0.06, mq_hi, mz - 0.015)],
        uvr(12 + (mq_i + 1) % 4))
    # pale cap: end-on from the dollhouse quadrant an all-black run merges into
    # one mass, and this line breaks it into machines
    bx(sub, Material("a2cap", "#787c82", roughness=0.55),
       x0 - 0.012, x1 + 0.012, top + plinth - 0.07, top + plinth,
       -bd / 2 - 0.012, ft - 0.30)

    ca, sa = math.cos(R(rot)), math.sin(R(rot))
    for part, mm in sub._parts:
        v = [(cx + x * ca + z * sa, y, cz - x * sa + z * ca)
             for (x, y, z) in part.verts]
        m._parts.append((Part(v, part.tris, part.smooth, part.colors,
                              part.uv), mm))


# ---- the machines, one row per wall.  Widths, heights, deck heights, marquee
# depths, plinths and profiles all differ; the photos' run is jagged, not a
# comb, and that is most of what "seven of the same box" meant.
EAST_RUN = [
    # (z, bw, top, style, dy, mqh, art, front art, marquee, plinth)
    (2.85, 2.34, 6.28, "slope",    2.56, 0.70, 0, 6, 0, 0.00),
    (5.11, 2.10, 5.86, "straight", 2.44, 0.55, 1, 9, 1, 0.10),
    (7.37, 2.42, 6.34, "riser",    2.60, 0.76, 2, 4, 2, 0.00),
    (9.63, 2.16, 5.98, "step",     2.48, 0.58, 3, 8, 3, 0.14),
    (11.89, 2.30, 6.22, "slope",   2.54, 0.66, 4, 1, 0, 0.00),
    (14.15, 2.04, 5.78, "straight", 2.40, 0.52, 5, 11, 2, 0.08),
    (16.41, 2.38, 6.16, "riser",   2.58, 0.72, 6, 3, 1, 0.00),
]

SOUTH_RUN = [
    (2.05, 2.95, 6.36, "step",     2.62, 0.80, 7, 2, 3, 0.00),
    (4.95, 2.42, 6.02, "straight", 2.46, 0.58, 8, 5, 0, 0.00),
    (7.55, 2.52, 6.24, "slope",    2.56, 0.68, 9, 0, 1, 0.12),
    (10.05, 2.28, 5.92, "riser",   2.42, 0.60, 10, 7, 2, 0.00),
]

NORTH_RUN = [
    (6.55, 2.44, 6.20, "slope",    2.56, 0.72, 5, 9, 2, 0.00),
    (9.00, 2.28, 6.34, "straight", 2.50, 0.64, 8, 8, 0, 0.10),
    (11.30, 2.18, 6.02, "riser",   2.44, 0.56, 1, 3, 3, 0.00),
    (13.55, 2.32, 6.26, "step",    2.54, 0.68, 11, 2, 1, 0.06),
]


def build_east_cabs():
    """The hero run: seven uprights down the east wall, facing west."""
    m = Model()
    cshadow(m, W - 1.45, (EAST_RUN[0][0] + EAST_RUN[-1][0]) / 2, 1.55,
            (EAST_RUN[-1][0] - EAST_RUN[0][0]) / 2 + 1.25, feather=0.85,
            strength=1.00, room=(W, D))
    for i, (z, bw, top, st, dy, mqh, ai, af, mi, pl) in enumerate(EAST_RUN):
        upright(m, W - 1.32, z, 270, ai, bw=bw, bd=2.55, top=top, seed=i + 1,
                style=st, dy=dy, mqh=mqh, mq_i=mi, art_f=af, plinth=pl)
    return save_and_place("Arcade Cabinets East", m, ROOM)


def build_south_cabs():
    """Legends Ultimate, Capcom Champion, Time Crisis and T2 on the south wall,
    plus the black diagonal acoustic panel between them and the door, the black
    hex cluster above the T2 group, and Ridge Racer round the SW corner."""
    m = Model()
    cshadow(m, 5.9, D - 1.45, 5.95, 1.45, feather=0.85, strength=1.00,
            room=(W, D))
    for (cx, bw, top, st, dy, mqh, ai, af, mi, pl) in SOUTH_RUN:
        upright(m, cx, D - 1.32, 180, ai, bw=bw, bd=2.55, top=top,
                seed=int(cx * 7), style=st, dy=dy, mqh=mqh, mq_i=mi,
                art_f=af, plinth=pl)
    # the blue CAPCOM lower cabinet the Champion Edition stands on
    bx(m, Material("a2capc", "#1c4c9a", roughness=0.6),
       3.62, 6.28, 0.0, 2.55, D - 2.55, D - 0.06)
    bx(m, Material("a2capy", "#e0b21c", roughness=0.5),
       4.30, 5.60, 0.42, 0.70, D - 2.62, D - 2.56)
    # black diagonal-rib acoustic panel between the run and the door
    sub = Model()
    bx(sub, ACOU, SA(13.20), SA(11.60), 3.20, 6.70, 0.0, 0.09)
    RIB = Material("a2rib", "#474b52", roughness=0.88)
    for k in range(9):
        bx(sub, RIB, SA(13.10) + k * 0.17, SA(13.04) + k * 0.17,
           3.30 + k * 0.34, 6.60, 0.09, 0.10)
    blit(m, sub, "s", W, D, 0.0)
    # black / iridescent hexes over the T2 group -- `v3 4`, far wall upper band
    hex_wall(m, "s",
             [(6.40, 6.95, "d"), (7.65, 7.35, "w"), (8.90, 6.95, "d"),
              (10.15, 7.35, "d"), (11.40, 6.95, "w"), (5.15, 7.35, "d"),
              (3.90, 6.95, "d"), (2.65, 7.35, "w")])

    # ---- east of the door: the 1.2 ft stub carries the vertical RGB bar and a
    # wall-mounted mini cabinet; the Connect-4 game stands on the floor beside it
    sub = Model()
    hp = [(0.30 * math.cos(R(60 * j + 30)), 0.30 * math.sin(R(60 * j + 30)))
          for j in range(6)]
    for k in range(7):                       # hexagon segments of the light bar
        wpanel(sub, LEDS[(k + 3) % 5], hp, SA(16.85), 2.35 + k * 0.62, 0.0, 0.07)
    blit(m, sub, "s", W, D, 0.0)
    # mini cabinet hung on the wall east of the door
    bx(m, CABBLK, 17.35, 18.85, 2.45, 5.35, D - 0.62, D - 0.04)
    bx(m, SCRN, 17.52, 18.68, 3.40, 4.60, D - 0.645, D - 0.62)
    bx(m, LEDS[0], 17.50, 18.70, 4.75, 5.20, D - 0.645, D - 0.62)
    bx(m, LEDS[4], 17.50, 18.70, 2.70, 3.20, D - 0.645, D - 0.62)
    # Connect-4 on a low white console
    cshadow(m, 19.22, D - 0.95, 1.35, 0.80, feather=0.70, strength=0.82,
            room=(W, D))
    bx(m, WHTM, 17.90, 20.55, 0.0, 2.05, D - 1.70, D - 0.16)
    bx(m, TRIM, 17.83, 20.62, 2.05, 2.17, D - 1.76, D - 0.10)
    G = Material("a2game", "#17181c", roughness=0.62)
    bx(m, G, 18.35, 20.10, 2.17, 4.05, D - 1.10, D - 0.96)
    for r_ in range(5):
        for c_ in range(5):
            bx(m, WHTM, 18.47 + c_ * 0.33, 18.69 + c_ * 0.33,
               2.29 + r_ * 0.31, 2.51 + r_ * 0.31, D - 0.965, D - 0.955)

    # ---- Ridge Racer, round the corner on the west wall's south end
    cshadow(m, 1.40, 21.55, 1.45, 1.30, feather=0.80, strength=0.94,
            room=(W, D))
    upright(m, 1.32, 21.55, 90, 10, bw=2.42, bd=2.55, top=6.06, seed=77,
            style="step", dy=2.58, mqh=0.66, mq_i=3, art_f=1)
    return save_and_place("Arcade Cabinets South", m, ROOM)


# ============================================ north wall: the frontal machines
def build_north_cabs():
    """`Arcade Room v3 1` shows FOUR frontal uprights on the north wall --
    Pac-Man and three others -- a tall glass-fronted lit Funko display cabinet
    in the NE corner and a large plush in a net bag hung over it.  Round 2 built
    none of them, which is why the room's north half was dead floor."""
    m = Model()
    cshadow(m, (NORTH_RUN[0][0] + NORTH_RUN[-1][0]) / 2, 1.45,
            (NORTH_RUN[-1][0] - NORTH_RUN[0][0]) / 2 + 1.35, 1.55,
            feather=0.85, strength=1.00, room=(W, D))
    for (cx, bw, top, st, dy, mqh, ai, af, mi, pl) in NORTH_RUN:
        upright(m, cx, 1.32, 0, ai, bw=bw, bd=2.55, top=top,
                seed=int(cx * 11), style=st, dy=dy, mqh=mqh, mq_i=mi,
                art_f=af, plinth=pl)

    # ---- the glass-fronted lit Funko display cabinet, NE corner
    fx0, fx1, fz0, fz1, fh = 17.45, 20.00, 0.06, 1.36, 5.55
    cshadow(m, (fx0 + fx1) / 2, (fz0 + fz1) / 2, (fx1 - fx0) / 2,
            (fz1 - fz0) / 2, feather=0.70, strength=0.86, room=(W, D))
    CASEW = Material("a2case", "#f0eee9", roughness=0.42)
    bx(m, CASEW, fx0, fx1, 0.0, 0.42, fz0, fz1)                  # plinth
    for (a, b) in ((fx0, fx0 + 0.10), (fx1 - 0.10, fx1)):        # stiles
        bx(m, CASEW, a, b, 0.42, fh, fz0, fz1)
    bx(m, CASEW, fx0, fx1, fh - 0.16, fh, fz0, fz1)              # head
    bx(m, CASEW, fx0, fx1, 0.42, fh, fz0, fz0 + 0.10)            # back
    nsh = 5
    for s in range(nsh):
        sy = 0.60 + s * ((fh - 1.05) / nsh)
        bx(m, CASEW, fx0 + 0.10, fx1 - 0.10, sy, sy + 0.055, fz0 + 0.08, fz1 - 0.16)
        bx(m, LEDS[s % 5], fx0 + 0.12, fx1 - 0.12, sy - 0.045, sy - 0.005,
           fz0 + 0.12, fz1 - 0.30)
        for k in range(6):
            bxx = fx0 + 0.20 + k * ((fx1 - fx0 - 0.40) / 6.0)
            bxw = (fx1 - fx0 - 0.40) / 6.0 - 0.03
            uvq(m, ART, [(bxx, sy + 0.055, fz1 - 0.20),
                         (bxx + bxw, sy + 0.055, fz1 - 0.20),
                         (bxx + bxw, sy + 0.055 + 0.58, fz1 - 0.20),
                         (bxx, sy + 0.055 + 0.58, fz1 - 0.20)],
                uvr((s * 6 + k) % 12))
    bx(m, GLASS, fx0 + 0.10, fx1 - 0.10, 0.42, fh - 0.16, fz1 - 0.09, fz1 - 0.05)

    # ---- the plush in a net bag, hung above and west of the case
    px, py, pz = 16.30, 4.35, 0.75
    PLUSH = Material("a2plush", "#f0ece2", roughness=0.98)
    m.add(puff(1.45, 1.55, 1.20, r=0.52, seg=10, rings=5), PLUSH,
          at=(px, py, pz))
    for dx in (-0.44, 0.44):
        m.add(puff(0.42, 0.50, 0.34, r=0.15, seg=8, rings=4), PLUSH,
              at=(px + dx, py + 1.30, pz))
    bx(m, Material("a2eye", "#1a1c20", roughness=0.4),
       px - 0.34, px - 0.18, py + 0.95, py + 1.10, pz + 0.52, pz + 0.56)
    bx(m, Material("a2eye2", "#1a1c20", roughness=0.4),
       px + 0.18, px + 0.34, py + 0.95, py + 1.10, pz + 0.52, pz + 0.56)
    NET = Material("a2net", "#d8d4cc", roughness=0.9, opacity=0.42)
    for k in range(7):                       # the net bag, crossed strands
        t = -0.72 + k * 0.24
        bx(m, NET, px + t - 0.018, px + t + 0.018, py - 0.10, py + 2.05,
           pz + 0.58, pz + 0.60)
    for k in range(5):
        bx(m, NET, px - 0.78, px + 0.78, py + 0.10 + k * 0.42,
           py + 0.14 + k * 0.42, pz + 0.58, pz + 0.60)
    m.add(cylinder(0.05, 0.34, 8), BLACKMET, at=(px, py + 2.05, pz + 0.30),
          rot_x=R(90))

    # ---- the black speaker on a stand that stands between them (photo v3 1)
    sx, sz = 15.10, 1.05
    cshadow(m, sx, sz, 0.60, 0.60, feather=0.60, strength=0.74, room=(W, D))
    m.add(cylinder(0.62, 0.07, 12), BLACKMET, at=(sx, 0.0, sz))
    m.add(cylinder(0.075, 2.35, 8), BLACKMET, at=(sx, 0.07, sz))
    bx(m, CABBLK, sx - 0.52, sx + 0.52, 2.35, 3.95, sz - 0.42, sz + 0.42)
    m.add(cylinder(0.30, 0.03, 12), Material("a2spk", "#2a2d33", roughness=0.9),
          at=(sx, 0.0, sz + 0.44), rot_x=R(90))
    return save_and_place("Arcade Cabinets North", m, ROOM)


# ============================================= west wall: the two gaming booths
def razer_chair(m, cx, cz, rot=180, scale=1.0):
    """The black gaming chair -- two booths and the desk all use it."""
    sub = Model()
    sub.add(cylinder(0.16, 1.05, 10), BLACKMET, at=(0.0, 0.22, 0.0))
    for k in range(5):
        a = R(72 * k)
        sub.add(box(1.00, 0.13, 0.20), BLACKMET,
                at=(0.46 * math.cos(a), 0.10, 0.46 * math.sin(a)), rot_y=-a)
        sub.add(cylinder(0.11, 0.20, 8), BLACKMET,
                at=(0.88 * math.cos(a), 0.11, 0.88 * math.sin(a)), rot_x=R(90))
    slab(sub, BLKF2, -0.86, 0.86, 1.27, 1.52, -0.84, 0.84, r=0.13)
    slab(sub, BLKF, 0.38, 0.78, 1.52, 3.48, -0.80, 0.80, r=0.13)
    slab(sub, BLKF2, 0.30, 0.60, 3.48, 3.92, -0.50, 0.50, r=0.11)
    for dz in (-0.86, 0.86):
        slab(sub, BLKF2, -0.30, 0.44, 1.52, 2.26, dz - 0.09, dz + 0.09, r=0.07)
    ca, sa = math.cos(R(rot)), math.sin(R(rot))
    for part, mm in sub._parts:
        m._parts.append((Part([(cx + x * ca + z * sa, y * scale,
                                cz - x * sa + z * ca)
                               for (x, y, z) in part.verts],
                              part.tris, part.smooth), mm))


BOOTHS = [(7.55, 10.35), (10.95, 13.75)]     # local z spans of the two openings
BOOTH_D = 1.55                               # how far the bay stands proud


def build_booths():
    """`Arcade Room v3 1` (crop 0,430-560,850) and `v3 2` both show two deep
    lit gaming bays on the west wall, each with a Razer chair, a wall monitor,
    a worktop and headset hooks.  Round 2 left this as open floor and disclosed
    it; it is a prominent feature of two of the four photographs.

    The plan's west wall is the exterior foundation, so the bays cannot be cut
    INTO it: they are built as a stud bay standing BOOTH_D proud of the wall
    with two openings through it, which is what the photo's ~1 ft white reveals
    read as anyway."""
    m = Model()
    z0, z1 = BOOTHS[0][0] - 0.34, BOOTHS[1][1] + 0.34
    BAY = Material("a2bay", "#e9e7e2", roughness=0.86)
    HEAD = 6.70
    piers = [(z0, BOOTHS[0][0]), (BOOTHS[0][1], BOOTHS[1][0]),
             (BOOTHS[1][1], z1)]
    for (a, b) in piers:
        bx(m, BAY, 0.0, BOOTH_D, 0.0, H - 0.02, a, b)
        bx(m, TRIM, 0.0, BOOTH_D + 0.02, 0.0, BB_H, a, b)          # skirting
    bx(m, BAY, 0.0, BOOTH_D, HEAD, H - 0.02, z0, z1)               # header
    for (a, b) in BOOTHS:
        bx(m, TRIM, BOOTH_D - 0.055, BOOTH_D, 0.0, HEAD + 0.08, a - 0.09, a)
        bx(m, TRIM, BOOTH_D - 0.055, BOOTH_D, 0.0, HEAD + 0.08, b, b + 0.09)
        bx(m, TRIM, BOOTH_D - 0.055, BOOTH_D, HEAD, HEAD + 0.08, a, b)
    DARK = Material("a2booth", "#1a1c21", roughness=0.9)
    for i, (a, b) in enumerate(BOOTHS):
        # the cavity: dark lining on the three inner faces
        bx(m, DARK, 0.02, 0.07, 0.0, HEAD, a, b)                   # back
        bx(m, DARK, 0.02, BOOTH_D - 0.06, 0.0, HEAD, a, a + 0.05)
        bx(m, DARK, 0.02, BOOTH_D - 0.06, 0.0, HEAD, b - 0.05, b)
        bx(m, DARK, 0.02, BOOTH_D - 0.06, HEAD - 0.05, HEAD, a, b)
        # RGB strips down both reveals -- the cyan/green edges in the photo
        for zz in (a + 0.055, b - 0.095):
            bx(m, LEDS[(i * 2) % 5], BOOTH_D - 0.34, BOOTH_D - 0.30,
               0.45, HEAD - 0.30, zz, zz + 0.04)
        # wall monitor
        bx(m, BLACKMET, 0.09, 0.19, 3.10, 5.30, a + 0.34, b - 0.34)
        bx(m, Material("a2bms", "#0b0e13", roughness=0.15, emissive="#12202e",
                       emissive_strength=1.0),
           0.19, 0.205, 3.20, 5.20, a + 0.42, b - 0.42)
        # worktop with a keyboard and a pad
        bx(m, WHTM, 0.07, BOOTH_D - 0.24, 2.30, 2.40, a + 0.10, b - 0.10)
        bx(m, Material("a2kb2", "#16181c", roughness=0.6),
           0.42, 1.10, 2.40, 2.46, a + 0.62, b - 0.62)
        # headset hooks
        for zz in (a + 0.26, b - 0.26):
            bx(m, BLACKMET, 0.16, 0.42, 5.55, 5.63, zz - 0.03, zz + 0.03)
            m.add(cylinder(0.24, 0.34, 8), BLKF2, at=(0.36, 5.20, zz),
                  rot_x=R(90))
        cshadow(m, BOOTH_D + 0.55, (a + b) / 2.0, 0.95, 0.95, feather=0.72,
                strength=0.80, room=(W, D))
        razer_chair(m, BOOTH_D - 0.30, (a + b) / 2.0, rot=90)
    return save_and_place("Arcade Booths", m, ROOM)

