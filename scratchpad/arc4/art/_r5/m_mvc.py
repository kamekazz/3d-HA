

# ======================================================= Marvel vs Capcom (E2)
# Roster: the TALLEST cabinet in the east run, stepped head, so its marquee
# sits higher than its neighbours'.  Marquee is a wide character-BATTLE
# illustration in reds, blues and oranges with no type separating from the art.
# Flank dark.  Front "plain black with a small recessed black coin/service box
# at centre and essentially no printed graphic - the emptiest lower front in
# the run", over a ROYAL BLUE riser carrying MARVEL (white) vs CAPCOM (red).
# Deck is "the clearest in the run: a pale grey/silver panel with TWO ball-top
# joysticks and a six-button-per-player array in green, red, white and blue".
_MVC_BLUE = _hx("#1633b4")
_MVC_BLUE2 = _hx("#3d6bec")


def _mvc_fighter(cv, u, v, s, body, rim, back, pose=0):
    """A rim-lit brawler silhouette.  Two poses so the left and right sides of
    the battle read as different fighters, not a mirrored pair."""
    cv.poly([(u - 0.30 * s, v + 0.62 * s), (u - 0.16 * s, v - 0.10 * s),
             (u + 0.16 * s, v - 0.10 * s), (u + 0.32 * s, v + 0.62 * s)],
            back)
    cv.poly([(u - 0.22 * s, v + 0.60 * s), (u - 0.12 * s, v - 0.06 * s),
             (u + 0.12 * s, v - 0.06 * s), (u + 0.24 * s, v + 0.60 * s)],
            body)
    cv.disc(u, v - 0.16 * s, 0.115 * s, body, ry=0.125 * s)
    if pose == 0:                                    # rising uppercut
        cv.seg(u + 0.10 * s, v + 0.02 * s, u + 0.46 * s, v - 0.34 * s,
               0.085 * s, body)
        cv.seg(u - 0.10 * s, v + 0.04 * s, u - 0.34 * s, v + 0.26 * s,
               0.080 * s, body)
        cv.disc(u + 0.48 * s, v - 0.36 * s, 0.075 * s, rim, ry=0.078 * s)
    else:                                            # straight punch
        cv.seg(u - 0.10 * s, v + 0.02 * s, u - 0.52 * s, v + 0.04 * s,
               0.090 * s, body)
        cv.seg(u + 0.10 * s, v + 0.06 * s, u + 0.30 * s, v + 0.30 * s,
               0.075 * s, body)
        cv.disc(u - 0.55 * s, v + 0.04 * s, 0.080 * s, rim, ry=0.084 * s)
    cv.seg(u - 0.20 * s, v + 0.58 * s, u - 0.30 * s, v + 0.92 * s,
           0.075 * s, body)
    cv.seg(u + 0.20 * s, v + 0.58 * s, u + 0.32 * s, v + 0.92 * s,
           0.075 * s, body)
    cv.seg(u - 0.15 * s, v - 0.06 * s, u - 0.20 * s, v + 0.58 * s,
           0.024 * s, rim)
    cv.seg(u + 0.15 * s, v - 0.06 * s, u + 0.22 * s, v + 0.58 * s,
           0.024 * s, rim)
    cv.seg(u - 0.09 * s, v - 0.24 * s, u + 0.09 * s, v - 0.24 * s,
           0.022 * s, rim)


def _mvc_marquee(cv):
    """KEPT FROM ROUND 4 (redrawn in this module's kernel).  A wide full-bleed
    character-battle illustration -- hot reds and oranges radiating from the
    left, deep blues from the right, a white clash flash down the centre.  NO
    type: the roster says none separates from the art at any magnification, so
    none is drawn."""
    A = cv.A
    cv.grad(0, 0, A * 0.5, 1, _hx("#7a1408"), _hx("#2a0704"), horiz=True)
    cv.grad(A * 0.5, 0, A, 1, _hx("#0a1338"), _hx("#0d2a72"), horiz=True)
    _rays(cv, A * 0.16, 0.72, 15, 0.04, 2.0, 0.055, _hx("#e0641a"), 0.34, 2,
          spread=math.pi)
    _rays(cv, A * 0.86, 0.74, 15, 0.04, 2.0, 0.055, _hx("#2f68e8"), 0.34, 3,
          spread=math.pi)
    _mottle(cv, 0, 0, A * 0.55, 1, [_hx("#c8461a"), _hx("#8e1208"),
                                    _hx("#f0a028")], 5, n=14, rmin=0.10,
            rmax=0.34, a=0.40)
    _mottle(cv, A * 0.45, 0, A, 1, [_hx("#1c46c0"), _hx("#0d1c62"),
                                    _hx("#4f8cff")], 6, n=14, rmin=0.10,
            rmax=0.34, a=0.40)
    # the clash flash
    for j in range(9):
        cv.poly([(A * 0.5 - 0.30 + j * 0.008, 1.02),
                 (A * 0.5 - 0.05 + j * 0.008, 0.46),
                 (A * 0.5 + 0.30 - j * 0.008, -0.02),
                 (A * 0.5 + 0.05 - j * 0.008, 0.54)],
                _mix(_hx("#ffe6a8"), (255, 255, 255), j / 9.0), a=0.16)
    _mvc_fighter(cv, A * 0.20, 0.40, 0.72, _hx("#a8201a"), _hx("#ffb060"),
                 _hx("#3a0a06"), pose=0)
    _mvc_fighter(cv, A * 0.36, 0.46, 0.60, _hx("#d4681e"), _hx("#ffd89a"),
                 _hx("#4a1a06"), pose=1)
    _mvc_fighter(cv, A * 0.80, 0.40, 0.72, _hx("#1a35a8"), _hx("#7fc0ff"),
                 _hx("#080e34"), pose=1)
    _mvc_fighter(cv, A * 0.64, 0.46, 0.60, _hx("#3c1f92"), _hx("#c79bff"),
                 _hx("#100634"), pose=0)
    for j in range(26):                                  # speed streaks
        v = _hash(j, 3, 8)
        cv.seg(A * _hash(j, 5, 8), v, A * _hash(j, 5, 8) + 0.30, v,
               0.008, (255, 240, 220), a=0.20)
    for j in range(8):                                   # vignette
        cv.rect(0, 0, 0.06 + j * 0.035, 1, (10, 4, 4), a=0.06)
        cv.rect(A - 0.06 - j * 0.035, 0, A, 1, (4, 6, 16), a=0.06)
    cv.rect(0, 0, A, 0.026, _hx("#16181e"))
    cv.rect(0, 0.974, A, 1, _hx("#16181e"))
    cv.noise(4.5, 13)


def _mvc_side(cv):
    """Dark flank -- the roster resolves no graphic here, and inventing one
    would be a lie.  What it is NOT is a black slab: a deep navy ground with a
    huge low-contrast VS device, battle silhouettes at 12-18% contrast, a red
    diagonal slash, and the royal-blue base band that continues round from the
    riser.  Tile LEFT is the cabinet BACK."""
    A = cv.A
    cv.grad(0, 0, A, 1, _hx("#161d3a"), _hx("#080a16"))
    _mottle(cv, 0, 0, A, 1, [_hx("#1d2a5e"), _hx("#12163a"), _hx("#2a1840")],
            21, n=20, rmin=0.06, rmax=0.22, a=0.42)
    for j in range(5):                                   # red diagonal slash
        cv.poly([(-0.1, 0.30 + j * 0.012), (A + 0.1, 0.66 + j * 0.012),
                 (A + 0.1, 0.70 + j * 0.012), (-0.1, 0.34 + j * 0.012)],
                _hx("#7a1a18"), a=0.22)
    # a hero-strip of six comic frames down the flank, so the top third is not
    # bare -- dark, low-contrast, but structured
    for j in range(6):
        v0 = 0.045 + j * 0.145
        cv.rect(A * 0.055, v0, A * 0.945, v0 + 0.118, _hx("#0d1226"), a=0.55)
        cv.rect(A * 0.055, v0, A * 0.945, v0 + 0.008,
                _hx("#2a3670") if j % 2 else _hx("#5e2028"), a=0.70)
    _mvc_fighter(cv, A * 0.40, 0.235, 0.26, _hx("#2b3670"), _hx("#5872c8"),
                 _hx("#141a34"), pose=0)
    _mvc_fighter(cv, A * 0.60, 0.520, 0.26, _hx("#3a2358"), _hx("#7a5ec0"),
                 _hx("#161230"), pose=1)
    _mvc_fighter(cv, A * 0.42, 0.800, 0.26, _hx("#5e2028"), _hx("#c06a5a"),
                 _hx("#26100f"), pose=0)
    cv.text("VS", A * 0.50, 0.385, 0.130, _hx("#5468b8"), 0.022, track=0.05,
            align="c", a=0.70)
    cv.rect(0, 0.930, A, 1, _MVC_BLUE)                   # blue base band
    cv.grad(0, 0.930, A, 0.958, _MVC_BLUE2, _MVC_BLUE)
    cv.rect(0, 0, A, 0.014, _hx("#101218"))
    cv.grad(0, 0, 0.016, 1, _hx("#2a2e3a"), _hx("#101218"), horiz=True)
    cv.grad(A - 0.016, 0, A, 1, _hx("#101218"), _hx("#2a2e3a"), horiz=True)
    cv.noise(3.4, 27)


def _mvc_front(cv):
    """Charcoal, brushed, with a giant low-contrast VS watermark so the field
    is never bare; ONE small recessed BLACK coin box dead centre with a
    coin-return cup under it (this is the smallest and darkest coin door of my
    four and the only one at mid height); and the ROYAL BLUE riser across the
    bottom third with the wordmark the photo resolves at 16x: white MARVEL,
    red CAPCOM, a white star VS device between them, a smaller second line."""
    A = cv.A
    cv.fill(_hx("#191c23"))
    cv.grad(0, 0, A, 0.70, _hx("#222732"), _hx("#101319"))
    for j in range(46):                                  # vertical brushing
        u = A * j / 46.0
        cv.seg(u, 0.0, u, 0.72, 0.006,
               _hx("#2e3440") if j % 2 else _hx("#14171d"), a=0.45)
    _mottle(cv, 0, 0, A, 0.70, [_hx("#3a1a1a"), _hx("#161f42")], 33, n=10,
            rmin=0.14, rmax=0.34, a=0.22)
    # a SCREENED ghost of the marquee's battle, printed at 10-14% contrast --
    # the roster's words are "essentially no printed graphic", and a screened
    # image is what that black panel actually is at arm's length.  Without it
    # the upper two thirds are the bare charcoal the critics called a slab.
    _mvc_fighter(cv, A * 0.235, 0.235, 0.46, _hx("#2b2027"), _hx("#4a3038"),
                 _hx("#1d1720"), pose=0)
    _mvc_fighter(cv, A * 0.765, 0.235, 0.46, _hx("#1f2438"), _hx("#33405e"),
                 _hx("#161a28"), pose=1)
    for iy in range(15):                                 # halftone screen
        for ix in range(19):
            u = A * (ix + 0.5) / 19.0
            v = 0.02 + 0.60 * (iy + 0.5) / 15.0
            r = 0.005 + 0.009 * _hash(ix, iy, 12)
            cv.disc(u, v, r, _hx("#0c0e14"), a=0.55, ry=r)
    cv.text("VS", A * 0.5, 0.145, 0.42, _hx("#3a4254"), 0.060, track=0.05,
            align="c", a=0.62)
    _fine(cv, A * 0.30, A * 0.70, 0.045, 0.010, (120, 126, 140), 6, words=5)
    for j in range(4):                                   # red / blue divider
        cv.rect(A * 0.04, 0.596 + j * 0.008, A * 0.50, 0.602 + j * 0.008,
                _hx("#8e2420"), a=0.55)
        cv.rect(A * 0.50, 0.596 + j * 0.008, A * 0.96, 0.602 + j * 0.008,
                _hx("#1f3faa"), a=0.55)
    # ---- the coin box: small, centred, black on black, with a return cup
    bu0, bu1, bv0, bv1 = A * 0.325, A * 0.675, 0.190, 0.450
    cv.rect(bu0 - 0.014, bv0 - 0.012, bu1 + 0.014, bv1 + 0.030,
            _hx("#0a0b0f"))
    _plate(cv, bu0, bv0, bu1, bv1, _hx("#101218"), _hx("#3c414c"),
           _hx("#050608"), bw=0.009)
    for j in range(2):
        su = bu0 + (bu1 - bu0) * (0.28 + 0.44 * j)
        cv.rect(su - 0.008, bv0 + 0.030, su + 0.008, bv0 + 0.086,
                _hx("#8e939c"))
        cv.rect(su - 0.004, bv0 + 0.036, su + 0.004, bv0 + 0.080,
                _hx("#08090c"))
        cv.disc(su, bv0 + 0.120, 0.013, _hx("#c9ccd2"), ry=0.013)
    cv.rect(bu0 + 0.030, bv1 + 0.036, bu1 - 0.030, bv1 + 0.098,
            _hx("#07080b"))
    cv.rect(bu0 + 0.030, bv1 + 0.036, bu1 - 0.030, bv1 + 0.048,
            _hx("#4a505c"))
    # ---- the royal blue riser
    rv = 0.725
    cv.rect(0, rv, A, 1, _MVC_BLUE)
    cv.grad(0, rv, A, 1, _MVC_BLUE2, _hx("#0c1c78"))
    _mottle(cv, 0, rv, A, 1, [_hx("#2f5ce8"), _hx("#0b1668"), _hx("#5c8bff")],
            41, n=18, rmin=0.06, rmax=0.20, a=0.34)
    _rays(cv, A * 0.5, rv + 0.16, 16, 0.03, 0.9, 0.020, _hx("#8fb2ff"), 0.22,
          9)
    cv.poly([(A * 0.06, rv + 0.055), (A * 0.94, rv + 0.030),
             (A * 0.96, rv + 0.230), (A * 0.04, rv + 0.255)],
            _hx("#0a0f3c"), a=0.55)
    cv.text("MARVEL", A * 0.315, rv + 0.075, 0.100, (245, 246, 250), 0.0200,
            track=0.04, align="c", ital=0.14, shadow=(4, 6, 30),
            sh=(0.010, 0.012))
    cv.text("CAPCOM", A * 0.715, rv + 0.085, 0.100, _hx("#e83028"), 0.0200,
            track=0.04, align="c", ital=0.14, shadow=(4, 6, 30),
            sh=(0.010, 0.012))
    # the little star VS device between and below the two words
    cv.disc(A * 0.515, rv + 0.185, 0.052, (250, 250, 252), ry=0.052, a=0.92)
    _rays(cv, A * 0.515, rv + 0.185, 8, 0.03, 0.115, 0.018, (250, 250, 252),
          0.92, 1)
    cv.text("VS", A * 0.515, rv + 0.150, 0.062, _hx("#12246e"), 0.014,
            track=0.03, align="c")
    cv.text("CLASH OF SUPER HEROES", A * 0.5, rv + 0.278, 0.034,
            (198, 214, 250), 0.0080, track=0.10, align="c")
    _fine(cv, A * 0.22, A * 0.78, rv + 0.330, 0.009, (150, 172, 220), 7,
          words=6, a=0.7)
    cv.rect(0, rv, A, rv + 0.012, _hx("#060a2c"))
    cv.rect(0, 0, A, 0.012, _hx("#0d0f14"))
    cv.grad(0, 0, 0.014, 1, _hx("#2b2f3a"), _hx("#0d0f14"), horiz=True)
    cv.grad(A - 0.014, 0, A, 1, _hx("#0d0f14"), _hx("#2b2f3a"), horiz=True)
    cv.noise(3.0, 37)


def _mvc_deck(cv):
    """PALE GREY / SILVER -- the only light control panel among my four, and
    the roster calls it the clearest deck in the run.  Brushed steel across the
    whole surface, a black legend band along the back edge, two red/blue player
    chevrons, and printed sockets generated from DECKS so they sit under the
    real buttons."""
    A = cv.A
    cv.grad(0, 0, A, 1, _hx("#d6d9de"), _hx("#a2a7b0"))
    for j in range(70):                                  # brushed grain
        v = j / 70.0
        cv.seg(0, v, A, v + 0.004, 0.006,
               _hx("#e8ebef") if j % 2 else _hx("#9aa0aa"), a=0.42)
    cv.rect(0, 0, A, 0.175, _hx("#14161c"))
    cv.text("MARVEL", _du(cv, -0.115), 0.038, 0.098, (242, 243, 247), 0.0180,
            track=0.05, align="c", ital=0.14)
    cv.text("VS", _du(cv, 0.010), 0.048, 0.078, _hx("#7f8794"), 0.0150,
            track=0.05, align="c")
    cv.text("CAPCOM", _du(cv, 0.140), 0.038, 0.098, _hx("#e83028"), 0.0180,
            track=0.05, align="c", ital=0.14)
    for (u, c) in ((-0.255, _hx("#c02a24")), (0.245, _hx("#1f4fc8"))):
        cu = _du(cv, u)
        cv.poly([(cu - 0.40, 0.235), (cu + 0.40, 0.235), (cu + 0.34, 0.300),
                 (cu - 0.34, 0.300)], c, a=0.85)
        cv.poly([(cu - 0.34, 0.845), (cu + 0.34, 0.845), (cu + 0.40, 0.910),
                 (cu - 0.40, 0.910)], c, a=0.85)
    cv.text("1P", _du(cv, -0.455), 0.255, 0.072, _hx("#22252c"), 0.014)
    cv.text("2P", _du(cv, 0.400), 0.255, 0.072, _hx("#22252c"), 0.014)
    _deck_sockets(cv, "marvel-vs-capcom", _hx("#5c626c"), _hx("#1a1d23"))
    cv.rect(0, 0.978, A, 1, _hx("#5e646e"))
    cv.noise(3.6, 53)
