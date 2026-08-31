

# ========================================================= Mortal Kombat (E3)
# Roster: dark navy-to-black marquee carrying a large pale CIRCULAR emblem --
# the dragon roundel -- flanked by pale upright glyphs that do not resolve.
# Black flank, dark RED/MAROON T-molding on the whole silhouette.  Front is
# black with a LARGE display-face MK wordmark, red-outlined, a pale dragon form
# curling round its right side, an ornate pale scroll below it, three or four
# short lines of small light text, and a wide pale logo band low on the panel;
# a dark red-brown printed riser under that.  Deck is "a wide BLUE / TEAL
# printed deck -- the only strongly blue deck in the east run".
_MK_MAROON = _hx("#5a1d22")
_MK_BONE = _hx("#e6dcc4")


def _mk_dragon(cv, u, v, s, c, a=1.0, w=1.0):
    """The curled dragon: a coiled body, a horned head, a barbed tail.  Drawn
    as strokes so one skeleton serves the pale roundel emblem, the huge
    watermark on the flank and the small form curling round the K."""
    pts = []
    for i in range(15):
        t = i / 14.0
        ang = -2.3 + t * 4.4
        rr = s * (0.44 - 0.20 * t)
        pts.append((u + math.cos(ang) * rr * 1.05, v + math.sin(ang) * rr))
    cv.path(pts, s * 0.155 * w, c, a)                    # body coil
    hu, hv = pts[0]
    cv.poly([(hu - s * 0.09, hv - s * 0.03), (hu + s * 0.30, hv - s * 0.13),
             (hu + s * 0.34, hv + s * 0.02), (hu - s * 0.07, hv + s * 0.13)],
            c, a)                                        # snout
    cv.seg(hu + s * 0.02, hv - s * 0.10, hu - s * 0.16, hv - s * 0.34,
           s * 0.055 * w, c, a)                          # horn
    cv.seg(hu + s * 0.14, hv - s * 0.11, hu + s * 0.06, hv - s * 0.36,
           s * 0.045 * w, c, a)                          # horn
    tu, tv = pts[-1]
    cv.poly([(tu, tv - s * 0.10), (tu + s * 0.34, tv - s * 0.30),
             (tu + s * 0.20, tv + s * 0.02), (tu + s * 0.36, tv + s * 0.20),
             (tu, tv + s * 0.10)], c, a)                  # barbed tail
    for j in range(4):                                    # dorsal spines
        i = 4 + j * 3
        if i < len(pts) - 1:
            px, py = pts[i]
            qx, qy = pts[i + 1]
            nx, ny = -(qy - py), (qx - px)
            L = math.hypot(nx, ny) or 1.0
            cv.seg(px, py, px + nx / L * s * 0.16, py + ny / L * s * 0.16,
                   s * 0.045 * w, c, a)


def _mk_roundel(cv, u, v, s, ring, fill, glow=None):
    if glow:
        for j in range(5):
            cv.disc(u, v, s * (0.90 - j * 0.11), glow, a=0.13,
                    ry=s * (0.90 - j * 0.11))
    cv.disc(u, v, s * 0.50, fill, ry=s * 0.50)
    cv.disc(u, v, s * 0.44, _mix(fill, (0, 0, 0), 0.45), ry=s * 0.44)
    for j in range(46):
        a0 = j * 2 * math.pi / 46.0
        cv.seg(u + math.cos(a0) * s * 0.47, v + math.sin(a0) * s * 0.47,
               u + math.cos(a0 + 0.09) * s * 0.47,
               v + math.sin(a0 + 0.09) * s * 0.47, s * 0.055, ring)
    _mk_dragon(cv, u + s * 0.03, v, s * 0.62, ring)


def _mk_marquee(cv):
    """KEPT FROM ROUND 4 (redrawn here).  Navy-to-black ground, the pale
    dragon roundel dead centre, pale upright display glyphs left and right.
    The roster is explicit that the letters do NOT resolve at 30x and the
    roundel does, so the type is drawn condensed and half-swallowed by the
    smoke while the emblem carries the identity."""
    A = cv.A
    cv.grad(0, 0, A, 1, _hx("#101a3c"), _hx("#04060e"))
    _mottle(cv, 0, 0, A, 1, [_hx("#16265e"), _hx("#0a1130"), _hx("#2a2050")],
            3, n=20, rmin=0.14, rmax=0.44, a=0.34)
    for j in range(6):                                   # gold glow behind
        cv.disc(A * 0.5, 0.5, 0.70 - j * 0.09, _hx("#8a6a22"), a=0.10,
                ry=0.52 - j * 0.07)
    _speck(cv, 0, 0, A, 1, 40, _hx("#c8a34e"), 7, r=0.008, a=0.45)
    cv.text("MORTAL", A * 0.215, 0.240, 0.400, _MK_BONE, 0.052, track=0.05,
            cond=0.62, align="c", outline=_hx("#3a1418"), ow=0.010)
    cv.text("KOMBAT", A * 0.785, 0.240, 0.400, _MK_BONE, 0.052, track=0.05,
            cond=0.62, align="c", outline=_hx("#3a1418"), ow=0.010)
    for j in range(6):                                   # smoke over the type
        cv.disc(A * (0.16 + j * 0.14), 0.55, 0.34, _hx("#0b1130"), a=0.16,
                ry=0.30)
    _mk_roundel(cv, A * 0.5, 0.50, 0.84, _MK_BONE, _hx("#0c1130"),
                glow=_hx("#d8b45c"))
    cv.rect(0, 0, A, 0.026, _MK_MAROON)
    cv.rect(0, 0.974, A, 1, _MK_MAROON)
    cv.noise(4.2, 17)


def _mk_side(cv):
    """Black flank, no figurative graphic in any frame -- so this is cast
    stone, not a slab: a dark grey-brown masonry field with real cracking, an
    ember glow rising off the floor, a huge maroon dragon-roundel watermark and
    a pale ghost lockup, inside the maroon T-molding the roster names as this
    machine's most distinctive edge.  Tile LEFT is the cabinet BACK."""
    A = cv.A
    cv.grad(0, 0, A, 1, _hx("#2b2a2c"), _hx("#15171c"))
    _mottle(cv, 0, 0, A, 1, [_hx("#3a3630"), _hx("#1d1e24"), _hx("#443c34")],
            11, n=26, rmin=0.06, rmax=0.20, a=0.42)
    for j in range(9):                                   # slab courses
        v = 0.06 + j * 0.104
        cv.seg(0, v, A, v + 0.004, 0.006, _hx("#0e0f13"), a=0.55)
        cv.seg(0, v - 0.008, A, v - 0.004, 0.005, _hx("#514c46"), a=0.35)
    _cracks(cv, 0.02, 0.05, A - 0.02, 0.97, 14, _hx("#0a0b0e"), 19, w=0.006,
            a=0.55)
    for j in range(7):                                   # ember glow, bottom
        cv.disc(A * (0.10 + j * 0.13), 1.02, 0.20 - j * 0.008,
                _hx("#c25a16"), a=0.11, ry=0.17)
    _speck(cv, 0.05, 0.72, A - 0.05, 0.99, 26, _hx("#f0913a"), 23, r=0.005,
           a=0.55)
    # the roundel watermark, not a loose dragon: at 64 px a bare dragon curl
    # reads as a red smear, and the ring is what makes it legible as an emblem
    for j in range(4):
        cv.disc(A * 0.50, 0.415, 0.235 - j * 0.020, _hx("#2c0c0f"), a=0.24,
                ry=0.235 - j * 0.020)
    for j in range(40):
        a0 = j * 2 * math.pi / 40.0
        cv.seg(A * 0.50 + math.cos(a0) * A * 0.395,
               0.415 + math.sin(a0) * 0.190,
               A * 0.50 + math.cos(a0 + 0.10) * A * 0.395,
               0.415 + math.sin(a0 + 0.10) * 0.190, 0.018, _hx("#5c2026"),
               a=0.55)
    _mk_dragon(cv, A * 0.52, 0.415, 0.52, _hx("#6e2b31"), a=0.55, w=1.20)
    cv.text("MORTAL", A * 0.50, 0.660, 0.062, _hx("#c0b6a2"), 0.013,
            cond=0.66, track=0.06, align="c", a=0.88)
    cv.text("KOMBAT", A * 0.50, 0.740, 0.062, _hx("#c0b6a2"), 0.013,
            cond=0.66, track=0.06, align="c", a=0.88)
    _edge(cv, 0.020, _hx("#3a1216"), _hx("#8e3038"))
    cv.noise(3.8, 29)


def _mk_front(cv):
    """MK / dragon across the upper third, the ornate scroll and its lines of
    small text under it, the wide pale logo band low, and my WIDEST and LOWEST
    coin door: a bronze TWIN door spanning 58% of the panel with two slots and
    two return cups, sitting on the band rather than floating in a black
    field.  A dark red-brown riser closes the bottom."""
    A = cv.A
    cv.fill(_hx("#1b1a1c"))
    cv.grad(0, 0, A, 1, _hx("#26242a"), _hx("#0e0f13"))
    _mottle(cv, 0, 0, A, 1, [_hx("#39332e"), _hx("#191a20"), _hx("#453a30")],
            31, n=22, rmin=0.10, rmax=0.30, a=0.40)
    _cracks(cv, 0.02, 0.03, A - 0.02, 0.97, 16, _hx("#0a0a0d"), 33, w=0.005,
            a=0.50)
    for j in range(6):                                   # ember wash, bottom
        cv.disc(A * (0.12 + j * 0.16), 1.00, 0.26, _hx("#a8481a"), a=0.09,
                ry=0.20)
    cv.rect(0, 0, A, 0.030, _MK_MAROON)
    # ---- the MK wordmark and its dragon, upper third
    cv.text("MK", A * 0.415, 0.075, 0.260, _MK_BONE, 0.060, track=0.02,
            align="c", outline=_hx("#a3251f"), ow=0.019,
            shadow=(6, 5, 8), sh=(0.016, 0.018))
    _mk_dragon(cv, A * 0.775, 0.205, 0.360, _hx("#d8cdb2"), a=0.95)
    _rays(cv, A * 0.775, 0.205, 12, 0.10, 0.34, 0.010, _hx("#8a5a20"), 0.30,
          6)
    # ---- the ornate scroll / banner
    sv = 0.395
    cv.poly([(A * 0.115, sv + 0.030), (A * 0.180, sv), (A * 0.820, sv),
             (A * 0.885, sv + 0.030), (A * 0.820, sv + 0.078),
             (A * 0.180, sv + 0.078)], _hx("#c6bda6"))
    cv.poly([(A * 0.140, sv + 0.032), (A * 0.190, sv + 0.012),
             (A * 0.810, sv + 0.012), (A * 0.860, sv + 0.032),
             (A * 0.810, sv + 0.066), (A * 0.190, sv + 0.066)],
            _hx("#6b6252"))
    cv.text("MORTAL KOMBAT", A * 0.5, sv + 0.022, 0.040, _hx("#efe8d6"),
            0.0090, track=0.11, cond=0.85, align="c")
    # ---- three short lines of small light text
    for j in range(3):
        _fine(cv, A * (0.26 - j * 0.03), A * (0.74 + j * 0.03),
              0.505 + j * 0.030, 0.012, (176, 170, 154), 40 + j, words=5 + j)
    # ---- the wide pale logo band, low
    bv0, bv1 = 0.610, 0.700
    cv.rect(A * 0.045, bv0, A * 0.955, bv1, _hx("#cdc6b2"))
    cv.grad(A * 0.045, bv0, A * 0.955, bv1, _hx("#efe9d8"), _hx("#a49c88"))
    cv.rect(A * 0.045, bv0, A * 0.955, bv0 + 0.010, _hx("#7d2a24"))
    cv.rect(A * 0.045, bv1 - 0.010, A * 0.955, bv1, _hx("#7d2a24"))
    cv.text("MIDWAY", A * 0.230, bv0 + 0.022, 0.046, _hx("#2b2724"), 0.0105,
            track=0.10, align="c")
    cv.text("ARCADE LEGACY", A * 0.640, bv0 + 0.026, 0.038, _hx("#3a332c"),
            0.0090, track=0.11, align="c")
    # ---- the coin door: WIDE, LOW, bronze, twin, with two cups
    du0, du1, dv0, dv1 = A * 0.210, A * 0.790, 0.735, 0.905
    cv.rect(du0 - 0.016, dv0 - 0.012, du1 + 0.016, dv1 + 0.016,
            _hx("#0c0c0f"))
    _plate(cv, du0, dv0, du1, dv1, _hx("#6d5230"), _hx("#3a2a16"),
           _hx("#b99457"), bw=0.013)
    cv.seg((du0 + du1) * 0.5, dv0, (du0 + du1) * 0.5, dv1, 0.012,
           _hx("#33260f"))
    for j in range(2):
        cu = du0 + (du1 - du0) * (0.25 + 0.50 * j)
        cv.rect(cu - 0.055, dv0 + 0.024, cu + 0.055, dv0 + 0.052,
                _hx("#241a0c"))
        cv.rect(cu - 0.011, dv0 + 0.028, cu + 0.011, dv0 + 0.048,
                _hx("#e2c684"))
        cv.text("25", cu, dv0 + 0.064, 0.030, _hx("#f0dca8"), 0.0070,
                track=0.10, align="c")
        cv.rect(cu - 0.062, dv1 - 0.062, cu + 0.062, dv1 - 0.016,
                _hx("#100c07"))
        cv.rect(cu - 0.062, dv1 - 0.062, cu + 0.062, dv1 - 0.050,
                _hx("#8c6c3c"))
    # ---- dark red-brown riser
    cv.rect(0, 0.930, A, 1, _hx("#3b201c"))
    cv.grad(0, 0.930, A, 1, _hx("#5a2f26"), _hx("#24120f"))
    _speck(cv, 0, 0.935, A, 0.998, 24, _hx("#8a4a34"), 51, r=0.008, a=0.45)
    _edge(cv, 0.018, _hx("#3a1216"), _hx("#8e3038"))
    cv.noise(3.4, 43)


def _mk_deck(cv):
    """The wide BLUE / TEAL deck the roster calls the only strongly blue one in
    the east run: an ice-blue lightning field with dragon-scale hatching, a
    black legend strip along the back edge, and small dense sockets -- this
    machine's buttons are the SMALLEST of my four (r 0.040 ft against Blitz's
    0.062) and its stick tops are black balls."""
    A = cv.A
    cv.grad(0, 0, A, 1, _hx("#1d5f9e"), _hx("#0a2846"))
    _mottle(cv, 0, 0, A, 1, [_hx("#2f8ed0"), _hx("#0d3763"), _hx("#4fc0e8")],
            13, n=20, rmin=0.10, rmax=0.32, a=0.40)
    for j in range(15):                                  # scale hatching
        u = A * (j / 15.0)
        for k in range(5):
            v = 0.20 + k * 0.19
            cv.disc(u + (0.06 if k % 2 else 0.0), v, 0.085, _hx("#1a4d80"),
                    a=0.30, ry=0.075)
            cv.disc(u + (0.06 if k % 2 else 0.0), v - 0.012, 0.060,
                    _hx("#5cb4e0"), a=0.16, ry=0.048)
    for j in range(4):                                   # lightning forks
        u = A * (0.16 + j * 0.24)
        cv.path([(u, 0.06), (u + 0.10, 0.34), (u - 0.04, 0.38),
                 (u + 0.12, 0.78), (u + 0.02, 0.80), (u + 0.14, 0.99)],
                0.014, _hx("#cfeaff"), a=0.36)
    cv.rect(0, 0, A, 0.150, _hx("#0a1424"))
    cv.text("MORTAL KOMBAT", _du(cv, 0.0), 0.030, 0.084, _MK_BONE, 0.0160,
            track=0.09, cond=0.80, align="c")
    for u in (_du(cv, -0.250), _du(cv, 0.245)):
        cv.rect(u - 0.36, 0.215, u + 0.36, 0.800, _hx("#07162a"), a=0.40)
        cv.rect(u - 0.36, 0.215, u + 0.36, 0.228, _hx("#a32620"), a=0.85)
        cv.rect(u - 0.36, 0.788, u + 0.36, 0.800, _hx("#a32620"), a=0.85)
    cv.text("1P", _du(cv, -0.450), 0.230, 0.070, _hx("#dfe8f4"), 0.014)
    cv.text("2P", _du(cv, 0.398), 0.230, 0.070, _hx("#dfe8f4"), 0.014)
    _deck_sockets(cv, "mortal-kombat", _hx("#0d1c2e"), _hx("#050a12"))
    cv.rect(0, 0.982, A, 1, _hx("#4a1418"))
    cv.noise(4.2, 61)
