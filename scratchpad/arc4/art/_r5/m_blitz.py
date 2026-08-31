

# ============================================================== NFL Blitz (N3)
# Roster: near-black / dark navy marquee with a RED-and-WHITE flare across the
# top left and "NFL BLITZ" in chunky ITALIC chrome caps, not lit.  Flank shows
# BLUE and a RED/ORANGE form against dark.  Front is black with TWO large dark
# recessed rectangular panels side by side in the upper half, each with a
# single small white dot, and a LARGE CHROME WINGED BADGE across the lower
# part.  Deck is "a printed BLUE-VIOLET MOTTLED / NEBULA graphic across the
# whole deck" (samples #2b233b .. #615d80, mean ~#45415f) with rows of round
# buttons in blue, green, red and yellow.
_BZ_NEB = [_hx("#4b4374"), _hx("#2a2340"), _hx("#6f68a0"), _hx("#332c56"),
           _hx("#8a83c0")]


def _bz_nebula(cv, u0, v0, u1, v1, seed, a=1.0, dark=None, stars=44):
    """The violet nebula that is this machine's whole visual identity: it is
    on the deck in every photograph and on the flank in the one sliver v4 6
    gives of it."""
    cv.grad(u0, v0, u1, v1, _hx("#3b3459"), dark or _hx("#181528"))
    _mottle(cv, u0, v0, u1, v1, _BZ_NEB, seed, n=26, rmin=0.07, rmax=0.26,
            a=0.44 * a)
    _mottle(cv, u0, v0, u1, v1, [_hx("#9a92d8"), _hx("#5348a0")], seed + 1,
            n=14, rmin=0.03, rmax=0.11, a=0.30 * a)
    _speck(cv, u0, v0, u1, v1, stars, (238, 238, 250), seed + 2, r=0.006,
           a=0.60 * a)


def _bz_wing(cv, u, v, dirn, span, h, col, a=1.0):
    """One half of the winged badge: five tapered feathers fanning outward and
    down off a hub, longest at the top.  The first pass drew them as one wide
    triangle each and the badge read as two paper darts."""
    for j in range(5):
        t = j / 4.0
        L = span * (1.00 - 0.17 * j)
        y0 = v - h * 0.34 + t * h * 0.30
        cv.poly([(u, y0),
                 (u + dirn * L, y0 + h * (0.06 + 0.34 * t)),
                 (u + dirn * L * 0.94, y0 + h * (0.20 + 0.34 * t)),
                 (u, y0 + h * 0.17)], col, a)


def _blitz_marquee(cv):
    """KEPT FROM ROUND 4 (redrawn here).  Near-black navy ground, the red and
    white flare sweeping out of the top left, and NFL BLITZ in chunky italic
    chrome spanning nearly the full width with the terminal Z distinct.  NOT
    lit -- a2kit gives this marquee one of the low emissive tints."""
    A = cv.A
    cv.grad(0, 0, A, 1, _hx("#131834"), _hx("#05060e"))
    _mottle(cv, 0, 0, A, 1, [_hx("#1b2350"), _hx("#0a0d22")], 15, n=16,
            rmin=0.12, rmax=0.40, a=0.36)
    _speck(cv, 0, 0, A, 1, 34, (200, 210, 240), 16, r=0.006, a=0.35)
    # the red / white flare across the top left
    for j in range(7):
        t = j / 6.0
        cv.poly([(-0.05, 0.14 + t * 0.030), (A * 0.72, 0.05 + t * 0.024),
                 (A * 0.74, 0.085 + t * 0.024), (-0.05, 0.185 + t * 0.030)],
                _mix(_hx("#e02418"), (255, 255, 255), t * 0.85), a=0.60)
    cv.seg(-0.05, 0.10, A * 0.60, 0.045, 0.014, (250, 250, 252), a=0.75)
    for j in range(4):                                   # a second flare
        cv.poly([(A * 0.20, 0.93 - j * 0.012), (A * 1.05, 0.80 - j * 0.012),
                 (A * 1.05, 0.84 - j * 0.012), (A * 0.20, 0.97 - j * 0.012)],
                _mix(_hx("#1b3fd0"), (255, 255, 255), j * 0.20), a=0.34)
    _chrome(cv, "NFL BLITZ", A * 0.50, 0.245, 0.520, 0.062, ital=0.30,
            track=0.075, cond=0.86, align="c")
    cv.rect(0, 0, A, 0.024, _hx("#15151c"))
    cv.rect(0, 0.976, A, 1, _hx("#15151c"))
    cv.noise(4.0, 19)


def _blitz_side(cv):
    """The violet nebula wrap with a red/orange flare and a chrome vertical
    lockup -- v4 6's sliver between Pac-Man and this machine shows BLUE and a
    RED/ORANGE form against dark, which is exactly this.  Tile LEFT is the
    cabinet BACK, so the football and the lockup sit forward where the flank is
    not occluded by Golden Tee."""
    A = cv.A
    _bz_nebula(cv, 0, 0, A, 1, 71, stars=52)
    for j in range(6):                                   # red/orange flare
        cv.poly([(-0.05, 0.60 + j * 0.014), (A + 0.05, 0.30 + j * 0.014),
                 (A + 0.05, 0.355 + j * 0.014), (-0.05, 0.655 + j * 0.014)],
                _mix(_hx("#d8360e"), _hx("#f0a028"), j / 5.0), a=0.50)
    # the football
    fu, fv, fs = A * 0.52, 0.415, 0.115
    cv.disc(fu, fv, fs * 1.45, _hx("#5a2a14"), ry=fs)
    cv.disc(fu, fv - fs * 0.10, fs * 1.30, _hx("#8a4520"), ry=fs * 0.82)
    cv.seg(fu - fs * 0.70, fv, fu + fs * 0.70, fv, fs * 0.10,
           (242, 242, 246))
    for j in range(4):
        u = fu - fs * 0.36 + j * fs * 0.24
        cv.seg(u, fv - fs * 0.20, u, fv + fs * 0.20, fs * 0.075,
               (242, 242, 246))
    # cond 0.70: at cond 1.0 "BLITZ" is 0.576 wide in a frame only 0.490 wide
    # and the Z ran off the front edge of the cabinet
    _chrome(cv, "NFL", A * 0.50, 0.610, 0.086, 0.015, ital=0.26, track=0.12,
            cond=0.82, align="c")
    _chrome(cv, "BLITZ", A * 0.50, 0.706, 0.112, 0.019, ital=0.26,
            track=0.05, cond=0.72, align="c")
    for j in range(3):                                   # yard-line hatching
        v = 0.845 + j * 0.048
        cv.seg(A * 0.10, v, A * 0.90, v, 0.008, (226, 230, 244), a=0.16)
    _edge(cv, 0.018, _hx("#191a24"), _hx("#5f5a92"))
    cv.noise(3.6, 67)


def _blitz_front(cv):
    """TWIN coin doors in the upper half -- the only twin door among my four --
    each a near-black recessed panel with a lit bevel and one small white
    return button, exactly as v4 6 and v4 7 show them; then the big chrome
    winged badge across the lower part, spanning 90% of the panel, NFL small
    over BLITZ large with the wings spreading both ways.  The field behind is a
    faint blue nebula haze rather than flat black."""
    A = cv.A
    cv.fill(_hx("#131420"))
    cv.grad(0, 0, A, 1, _hx("#1c1d31"), _hx("#0a0a11"))
    _mottle(cv, 0, 0, A, 1, [_hx("#2a2a4c"), _hx("#101020"), _hx("#3a3468")],
            77, n=18, rmin=0.14, rmax=0.36, a=0.26)
    _speck(cv, 0, 0, A, 1, 30, (190, 196, 226), 79, r=0.006, a=0.28)
    # ---- the twin doors (COIN['nfl-blitz'] gives ar2 the same two rects)
    for j in range(2):
        u0 = A * (0.075 + j * 0.470)
        u1 = u0 + A * 0.410
        v0, v1 = 0.060, 0.430
        cv.rect(u0 - 0.014, v0 - 0.012, u1 + 0.014, v1 + 0.014,
                _hx("#05050a"))
        _plate(cv, u0, v0, u1, v1, _hx("#15161f"), _hx("#3e4054"),
               _hx("#040407"), bw=0.011)
        cv.rect(u0 + 0.030, v0 + 0.034, u1 - 0.030, v0 + 0.048,
                _hx("#0a0a10"))
        cv.rect(u0 + 0.030, v0 + 0.034, u1 - 0.030, v0 + 0.040,
                _hx("#33364a"))
        for k in range(2):                               # coin slots
            su = u0 + (u1 - u0) * (0.30 + 0.40 * k)
            cv.rect(su - 0.009, v0 + 0.086, su + 0.009, v0 + 0.140,
                    _hx("#6d7280"))
            cv.rect(su - 0.005, v0 + 0.092, su + 0.005, v0 + 0.134,
                    _hx("#06060a"))
        cv.disc((u0 + u1) * 0.5, v1 - 0.070, 0.030, (246, 247, 250),
                ry=0.030)                                # the white dot
        cv.disc((u0 + u1) * 0.5, v1 - 0.070, 0.020, (206, 210, 220),
                ry=0.020)
        cv.rect(u0 + 0.055, v1 - 0.032, u1 - 0.055, v1 - 0.010,
                _hx("#050509"))
    # ---- the chrome winged badge
    bu, bv = A * 0.50, 0.660
    _bz_wing(cv, bu - A * 0.135, bv, -1.0, A * 0.42, 0.30, _hx("#8e95a4"))
    _bz_wing(cv, bu + A * 0.135, bv, 1.0, A * 0.42, 0.30, _hx("#8e95a4"))
    _bz_wing(cv, bu - A * 0.140, bv - 0.012, -1.0, A * 0.38, 0.26,
             _hx("#dfe4ee"))
    _bz_wing(cv, bu + A * 0.140, bv - 0.012, 1.0, A * 0.38, 0.26,
             _hx("#dfe4ee"))
    for j in range(5):                                   # red under-flare
        cv.poly([(A * 0.06, bv + 0.140 + j * 0.008),
                 (A * 0.94, bv + 0.140 + j * 0.008),
                 (A * 0.88, bv + 0.168 + j * 0.008),
                 (A * 0.12, bv + 0.168 + j * 0.008)],
                _mix(_hx("#c81f14"), (255, 255, 255), j * 0.18), a=0.55)
    _chrome(cv, "NFL", bu, bv - 0.098, 0.085, 0.016, ital=0.28, track=0.14,
            align="c")
    _chrome(cv, "BLITZ", bu, bv - 0.006, 0.140, 0.026, ital=0.28, track=0.05,
            align="c")
    _fine(cv, A * 0.28, A * 0.72, 0.870, 0.011, (128, 132, 152), 83, words=6)
    cv.rect(0, 0.905, A, 1, _hx("#0b0b12"))
    cv.grad(0, 0.905, A, 0.930, _hx("#3f3a66"), _hx("#0b0b12"))
    _edge(cv, 0.016, _hx("#191a24"), _hx("#5f5a92"))
    cv.noise(3.2, 73)


def _blitz_deck(cv):
    """The nebula deck the roster measures at mean ~#45415f -- the most
    distinctive control surface on the north wall.  Blitz is the odd machine
    out among my four: BIG round buttons, THREE per player plus one turbo, and
    BAT-top sticks, against the three fighting cabinets' dense 6+6 arrays."""
    A = cv.A
    _bz_nebula(cv, 0, 0, A, 1, 91, stars=60)
    for j in range(3):                                   # yard lines
        v = 0.30 + j * 0.24
        cv.seg(0, v, A, v, 0.010, (226, 230, 244), a=0.20)
    for j in range(9):
        u = A * (0.06 + j * 0.11)
        cv.seg(u, 0.30, u, 0.78, 0.007, (226, 230, 244), a=0.12)
    cv.rect(0, 0, A, 0.150, _hx("#0d0c18"))
    _chrome(cv, "NFL BLITZ", _du(cv, 0.0), 0.028, 0.095, 0.017, ital=0.28,
            track=0.08, align="c")
    for (u, c) in ((-0.250, _hx("#c81f14")), (0.250, _hx("#1f46c8"))):
        cu = _du(cv, u)
        cv.rect(cu - 0.42, 0.215, cu + 0.42, 0.232, c, a=0.85)
        cv.rect(cu - 0.42, 0.855, cu + 0.42, 0.872, c, a=0.85)
    cv.text("1P", _du(cv, -0.455), 0.255, 0.078, (232, 234, 246), 0.015)
    cv.text("2P", _du(cv, 0.398), 0.255, 0.078, (232, 234, 246), 0.015)
    _deck_sockets(cv, "nfl-blitz", _hx("#141327"), _hx("#06050c"))
    cv.rect(0, 0.982, A, 1, _hx("#2a2748"))
    cv.noise(4.4, 89)
