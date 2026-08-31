

# =============================================================== the machines
# ==================================================== Marvel Super Heroes (E1)
# Roster: black carcase, GOLD/TAN T-molding on every edge; a full-bleed comic
# collage flank in teal / blue-green on near-black; "the most typographic panel
# in the room" on the front (CAPCOM / MARVEL / SUPER HEROES / two blue title
# lines / fine legal type / a row of warm character heads) with a separate
# printed riser under it; a dark two-player deck whose controls do not resolve.
_MSH_GOLD0, _MSH_GOLD1 = _hx("#8e6f2c"), _hx("#f0d488")


def _msh_marquee(cv):
    """KEPT FROM ROUND 4.  Full-bleed painted character art on a dark ground;
    'MARVEL' white toward the left end, the rest of the title lost in the
    illustration, and it reads dim rather than brightly lit."""
    cv.grad(0, 0, cv.A, 1, _hx("#0b0e1c"), _hx("#05060d"))
    for (u, v, r, c, al) in ((0.55, 0.42, 0.62, _hx("#1d3f86"), 0.55),
                             (1.35, 0.66, 0.72, _hx("#25185e"), 0.45),
                             (2.35, 0.40, 0.66, _hx("#5b1f8e"), 0.55),
                             (3.05, 0.58, 0.55, _hx("#7a2bb0"), 0.45),
                             (1.95, 0.20, 0.40, _hx("#0f3a63"), 0.40)):
        for j in range(4):
            cv.disc(u, v, r * (1.0 - j * 0.20), c, a=al * 0.34,
                    ry=r * 0.75 * (1.0 - j * 0.20))

    def hero(u, s, body, rim, cape=None):
        cv.poly([(u - 0.20 * s, 1.02), (u - 0.11 * s, 0.30 * s + 0.12),
                 (u + 0.11 * s, 0.30 * s + 0.12), (u + 0.22 * s, 1.02)], body)
        cv.disc(u, 0.16 + 0.06 * s, 0.10 * s, body, ry=0.11 * s)
        cv.seg(u - 0.10 * s, 0.34, u - 0.34 * s, 0.62, 0.075 * s, body)
        cv.seg(u + 0.10 * s, 0.34, u + 0.36 * s, 0.20, 0.075 * s, body)
        cv.seg(u - 0.13 * s, 0.30, u - 0.16 * s, 0.92, 0.022 * s, rim)
        cv.seg(u + 0.13 * s, 0.30, u + 0.19 * s, 0.92, 0.022 * s, rim)
        cv.seg(u - 0.08 * s, 0.11, u + 0.08 * s, 0.11, 0.020 * s, rim)
        if cape:
            cv.poly([(u - 0.14 * s, 0.26), (u - 0.62 * s, 0.72),
                     (u - 0.44 * s, 1.02), (u - 0.10 * s, 0.86)], cape)
    hero(0.36, 1.00, _hx("#7e1b24"), _hx("#e8687a"))
    hero(0.79, 0.86, _hx("#123a7a"), _hx("#5fa8ff"), _hx("#0d2450"))
    hero(2.77, 0.94, _hx("#3d1560"), _hx("#c07dff"))
    hero(3.20, 0.80, _hx("#12403a"), _hx("#57e0b0"))
    hero(2.33, 0.72, _hx("#6a3a08"), _hx("#f0a83c"))
    for j in range(7):
        cv.rect(0, 0, cv.A, 1, (6, 8, 18), a=0.055)
        cv.disc(cv.A * 0.5, 0.5, 1.9 - j * 0.12, _hx("#1b2a52"), a=0.05,
                ry=0.62 - j * 0.04)
    for j in range(9):
        cv.rect(0, 0, 0.10 + j * 0.05, 1, (3, 4, 10), a=0.055)
        cv.rect(cv.A - 0.10 - j * 0.05, 0, cv.A, 1, (3, 4, 10), a=0.055)
    cv.text("MARVEL", cv.A * 0.42, 0.30, 0.34, (243, 244, 248), 0.055,
            track=0.10, align="c", shadow=(4, 4, 10), sh=(0.02, 0.025))
    cv.text("SUPER HEROES", cv.A * 0.42, 0.70, 0.115, (196, 205, 224), 0.026,
            track=0.16, align="c")
    cv.rect(0, 0, cv.A, 0.028, _hx("#191a22"))
    cv.rect(0, 0.972, cv.A, 1, _hx("#141520"))
    cv.noise(4.5, 11)


def _msh_side(cv):
    """The comic-collage wrap.  Tile LEFT is the cabinet BACK, tile RIGHT the
    front; the collage runs the whole flank to the floor and the gold
    T-molding follows every edge.  Round 4 authored the teal at 20-60; these
    are night-RGB photographs and ROOM-BRIEF says match relationships not
    absolutes, so the panels are lifted to 90-190 -- at round 4's values the
    flank rendered as one black slab."""
    A = cv.A
    cv.fill(_hx("#0a1116"))
    _panel_grid(cv, 0.024, 0.018, A - 0.024, 0.982, 5)
    # two small printed captions INSIDE panels, at a size that actually fits
    # the 64 px tile -- the first pass set them at h 0.105 in a 0.495-wide
    # frame, four times the panel width, and the flank read as one title block
    for (u, v, s, h, c) in ((A * 0.50, 0.088, "MARVEL", 0.036, (244, 246, 250)),
                            (A * 0.50, 0.474, "SUPER HEROES", 0.024,
                             _hx("#8fd8e0"))):
        w = cv.width(s, h, track=0.10, cond=0.78)
        cv.rect(u - w * 0.5 - 0.012, v - 0.014, u + w * 0.5 + 0.012,
                v + h + 0.014, (6, 12, 16), a=0.72)
        cv.text(s, u, v, h, c, h * 0.16, track=0.10, cond=0.78, align="c")
    _edge(cv, 0.019, _MSH_GOLD0, _MSH_GOLD1)
    cv.noise(3.5, 23)


def _msh_bezel(cv):
    """The one screen surround among my four that the photographs actually
    show carrying artwork: in v3 4 / e_run3x this machine's monitor is ringed
    by a blue-teal mottled printed bezel, not the black frame every other
    cabinet has.  ar2's `art.has(slug + '.bezel')` path already handles it --
    atlas4 needs this key added to EXTRA_KEYS."""
    A = cv.A
    # the photo's surround is a DARK blue-teal camo, not a bright teal frame:
    # the first pass sat two stops above the crop beside it in compare_g1_r5
    cv.grad(0, 0, A, 1, _hx("#0d2430"), _hx("#060f16"))
    _mottle(cv, 0, 0, A, 1, [_hx("#154c5c"), _hx("#081a2e"), _hx("#1e6c78")],
            97, n=26, rmin=0.06, rmax=0.22, a=0.44)
    for j in range(9):
        cv.seg(0, 0.08 + j * 0.105, A, 0.02 + j * 0.105, 0.010,
               _hx("#2c7f8a"), a=0.16)
    cv.rect(0, 0, A, 0.020, _MSH_GOLD0)
    cv.rect(0, 0.980, A, 1, _MSH_GOLD0)
    cv.noise(3.0, 101)


def _msh_front(cv):
    """Full bleed, top to bottom.  Gold hairline frame; a teal comic-burst
    ghost across the WHOLE field so nothing is bare black; CAPCOM lockup;
    MARVEL at 80% of the panel width; SUPER HEROES; the blue secondary lockup;
    legal type; a flush printed COIN PLATE low LEFT (this machine has no proud
    coin door in any frame, so COIN carries an empty list for it) beside a row
    of warm character heads; and the printed riser band across the bottom
    fifth, carrying the title over the blue-green scene the photograph shows
    on the real riser."""
    A = cv.A
    cv.fill(_hx("#0d1016"))
    cv.grad(0, 0, A, 1, _hx("#182029"), _hx("#080a0e"))
    # full-field comic burst: rays from upper-left, a wash, a halftone field
    _rays(cv, A * 0.26, 0.30, 22, 0.05, 1.45, 0.030, _hx("#12525e"), 0.32, 4)
    _mottle(cv, 0.0, 0.0, A, 1.0,
            [_hx("#0f4a58"), _hx("#123f74"), _hx("#1b6c78"), _hx("#0d2a4c")],
            17, n=22, rmin=0.10, rmax=0.34, a=0.30)
    for iy in range(11):
        for ix in range(15):
            u = A * (ix + 0.5) / 15.0
            v = (iy + 0.5) / 11.0
            t = 1.0 - min(1.0, math.hypot(u - A * 0.26, v - 0.30) / 1.25)
            r = 0.006 + 0.020 * t
            cv.disc(u, v, r, _hx("#1d7f8c"), a=0.26, ry=r)
    cv.rect(0, 0, A, 1, (5, 8, 12), a=0.30)
    wht = (240, 242, 248)
    # ---- publisher lockup
    cv.rect(A * 0.205, 0.055, A * 0.315, 0.098, wht)
    cv.text("CAPCOM", A * 0.345, 0.050, 0.056, wht, 0.0135, track=0.13)
    # ---- the title, near the full width of the panel
    cv.text("MARVEL", A * 0.5, 0.140, 0.175, wht, 0.0330, track=0.070,
            align="c", shadow=_hx("#5a0f16"), sh=(0.016, 0.020))
    cv.text("SUPER HEROES", A * 0.5, 0.330, 0.062, (214, 220, 234), 0.0135,
            track=0.150, align="c")
    # ---- the blue secondary lockup (illegible in every photo: drawn as the
    # blue lockup the panel shows, not as invented words)
    blu, blu2 = _hx("#3f6fd8"), _hx("#93b8ff")
    cv.text("MARVEL", A * 0.52, 0.430, 0.082, blu2, 0.0180, track=0.05,
            align="c", ital=0.18, outline=_hx("#16255e"), ow=0.008)
    cv.text("SUPER HEROES", A * 0.50, 0.528, 0.055, blu, 0.0130, track=0.09,
            align="c", ital=0.18)
    _fine(cv, A * 0.135, A * 0.865, 0.604, 0.011, (132, 138, 152), 3, words=9)
    _fine(cv, A * 0.205, A * 0.795, 0.628, 0.011, (112, 118, 132), 4, words=7)
    # ---- flush printed coin plate, low LEFT.  No geometry: the panel is
    # unbroken in v3 4 / v4 8, so this is printed, recessed-looking and dark.
    cu0, cu1, cw0, cw1 = A * 0.055, A * 0.300, 0.660, 0.790
    _plate(cv, cu0, cw0, cu1, cw1, _hx("#1a1c22"), _hx("#3b3f49"),
           _hx("#0a0b0e"), bw=0.010)
    for j in range(2):
        su = cu0 + (cu1 - cu0) * (0.30 + 0.40 * j)
        cv.rect(su - 0.009, cw0 + 0.022, su + 0.009, cw0 + 0.062,
                _hx("#c8a24e"))
        cv.rect(su - 0.005, cw0 + 0.028, su + 0.005, cw0 + 0.056,
                _hx("#2a2410"))
    cv.rect(cu0 + 0.020, cw1 - 0.040, cu1 - 0.020, cw1 - 0.014,
            _hx("#0b0c10"))
    cv.rect(cu0 + 0.020, cw1 - 0.040, cu1 - 0.020, cw1 - 0.034,
            _hx("#454a55"))
    # ---- the row of warm character heads, to its right
    heads = ("#b03a26", "#d4763c", "#eaa955", "#9c3444", "#c85c2e",
             "#f0bd78")
    for i, hc in enumerate(heads):
        u = A * 0.375 + i * A * 0.098
        base = _hx(hc)
        cv.poly([(u - 0.044, 0.786), (u - 0.037, 0.700), (u - 0.020, 0.684),
                 (u + 0.020, 0.684), (u + 0.037, 0.700), (u + 0.044, 0.786)],
                _mix(base, (0, 0, 0), 0.30))
        cv.disc(u, 0.662, 0.040, base, ry=0.042)
        cv.poly([(u - 0.042, 0.650), (u - 0.034, 0.614), (u + 0.034, 0.614),
                 (u + 0.042, 0.650)], _mix(base, (18, 12, 10), 0.55))
        cv.disc(u - 0.015, 0.660, 0.0085, (22, 16, 14), ry=0.0080)
        cv.disc(u + 0.015, 0.660, 0.0085, (22, 16, 14), ry=0.0080)
        cv.seg(u - 0.013, 0.686, u + 0.013, 0.686, 0.0065,
               _mix(base, (0, 0, 0), 0.5))
    # ---- the printed riser band across the bottom (there is no riser quad in
    # the geometry -- see round 4's declared notes -- so it lives here)
    rv = 0.812
    cv.grad(0, rv, A, 1, _hx("#13506e"), _hx("#0a2536"))
    for j in range(13):
        u = A * (0.04 + j * 0.078)
        r = 0.030 + 0.030 * _hash(j, 2, 9)
        cv.disc(u, rv + 0.055 + 0.10 * _hash(j, 3, 9), r, _hx("#1f96a4"),
                a=0.44, ry=r * 0.85)
    for j in range(5):
        u = A * (0.14 + j * 0.19)
        cv.poly([(u - 0.030, 1.0), (u - 0.014, rv + 0.062),
                 (u + 0.014, rv + 0.062), (u + 0.032, 1.0)], _hx("#0a2c3e"))
        cv.disc(u, rv + 0.048, 0.020, _hx("#0a2c3e"), ry=0.022)
    cv.rect(0, rv + 0.010, A, 0.988, (4, 14, 22), a=0.34)
    cv.text("MARVEL", A * 0.5, rv + 0.032, 0.088, (242, 244, 250), 0.0175,
            track=0.075, align="c", shadow=(3, 10, 16), sh=(0.010, 0.013))
    cv.text("SUPER HEROES", A * 0.5, rv + 0.130, 0.038, (206, 226, 238),
            0.0095, track=0.145, align="c")
    cv.rect(0, rv, A, rv + 0.012, _MSH_GOLD0)
    _edge(cv, 0.017, _MSH_GOLD0, _MSH_GOLD1)
    cv.noise(3.2, 31)


def _msh_deck(cv):
    """Dark navy two-player deck with a gold/red chevron sweep and printed
    player zones.  The roster refuses to resolve this machine's controls, so
    the LAYOUT (6 buttons per player in two arced rows, bat-top sticks) is the
    real cabinet's standard Capcom CPS-2 fighting layout rather than an
    invention -- declared in the report.  Every socket below is painted from
    DECKS, so the print and the buttons register."""
    A = cv.A
    cv.grad(0, 0, A, 1, _hx("#1c2434"), _hx("#0a0e15"))
    _mottle(cv, 0, 0, A, 1, [_hx("#123f52"), _hx("#1d5f6e"), _hx("#26305e")],
            29, n=16, rmin=0.10, rmax=0.30, a=0.34)
    for j in range(7):                                   # chevron sweep
        u = A * (0.02 + j * 0.155)
        cv.poly([(u, 1.0), (u + 0.10, 1.0), (u + 0.46, 0.0), (u + 0.36, 0.0)],
                _hx("#8f2e2a") if j % 2 else _hx("#12313f"), a=0.42)
    cv.rect(0, 0, A, 0.020, _hx("#b8923c"))
    cv.rect(0, 0.980, A, 1, _hx("#b8923c"))
    for u in (_du(cv, -0.255), _du(cv, 0.245)):          # player zones
        cv.rect(u - 0.34, 0.235, u + 0.34, 0.790, (6, 10, 16), a=0.46)
        cv.rect(u - 0.34, 0.235, u + 0.34, 0.248, _hx("#c8a24e"), a=0.75)
        cv.rect(u - 0.34, 0.778, u + 0.34, 0.790, _hx("#c8a24e"), a=0.75)
    cv.text("1P", _du(cv, -0.455), 0.100, 0.085, _hx("#e8cf8a"), 0.017)
    cv.text("2P", _du(cv, 0.395), 0.100, 0.085, _hx("#e8cf8a"), 0.017)
    cv.text("MARVEL", _du(cv, 0.0), 0.055, 0.075, (232, 236, 244), 0.015,
            track=0.10, align="c")
    cv.text("SUPER HEROES", _du(cv, 0.0), 0.150, 0.042, _hx("#89b6ff"),
            0.0095, track=0.13, align="c")
    _deck_sockets(cv, "marvel-super-heroes", _hx("#3a4150"), _hx("#0a0d12"))
    cv.noise(4.0, 47)
