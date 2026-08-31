def _blitz_deck(cv):
    """VIOLET NEBULA, edge to edge -- and round 5's football field deleted.

    Round 5 drew yard lines and hash marks across this deck.  They are an
    invention: docs/photos-jpg/Arcade Room v4 6.jpg px (308,185)-(378,222) at
    18x (scratchpad/arc4/art/ref_g1r7/g1_blitz_deck46.png) and v3 1 px
    (660,640)-(780,720) at 12x (g1_blitz_deck31.png) both show this panel with
    NO straight line on it at any magnification -- only large pale wisps, star
    specks and a warm magenta core right of centre, on the indigo the roster
    metered across v4 6 y=203 (#2b233b .. #615d80, mean ~#45415f).  ROOM-BRIEF
    says inventing detail the photograph contradicts is not a valid outcome,
    so the field goes and the nebula gets the whole panel: bigger wisps,
    brighter cores, three times the stars, and the warm core the photo does
    show.  Blitz is also the machine with the FEWEST and BIGGEST buttons of my
    four -- three per player plus one turbo, at r 0.066 ft, against the three
    fighting cabinets' dense clusters."""
    A = cv.A
    _bz_nebula(cv, 0, 0, A, 1, 91, stars=0)
    # --- large wisps, drawn as overlapping soft arcs rather than one mottle,
    #     so the structure survives the 2x box-average atlas4 does.
    for (u, v, r, c, al) in ((0.30, 0.34, 0.46, "#7d76b4", 0.42),
                             (0.74, 0.72, 0.40, "#4a4270", 0.50),
                             (1.16, 0.26, 0.44, "#9a92cc", 0.36),
                             (1.62, 0.62, 0.46, "#5a5288", 0.46),
                             (2.02, 0.30, 0.38, "#8880bc", 0.34),
                             (0.52, 0.94, 0.30, "#3a3358", 0.50)):
        cv.disc(u, v, r, _hx(c), a=al, ry=r * 0.70)
    # the warm core v4 6 shows right of centre
    for (u, v, r, c, al) in ((1.42, 0.46, 0.30, "#8d4a72", 0.44),
                             (1.46, 0.44, 0.19, "#c06a72", 0.42),
                             (1.49, 0.42, 0.10, "#e8a274", 0.42)):
        cv.disc(u, v, r, _hx(c), a=al, ry=r * 0.74)
    _rays(cv, 1.47, 0.44, 16, 0.10, 0.72, 0.011, _hx("#e6c0a8"), 0.20, seed=7)
    _speck(cv, 0, 0, A, 1, 150, _hx("#eae6ff"), 5, r=0.0085, a=0.80)
    _speck(cv, 0, 0, A, 1, 60, _hx("#ffffff"), 15, r=0.013, a=0.85)
    for (u, v, r) in ((0.44, 0.22, 0.030), (1.26, 0.80, 0.026),
                      (1.90, 0.52, 0.028), (0.88, 0.44, 0.022)):
        cv.disc(u, v, r, (255, 255, 255), a=0.9, ry=r)
        _rays(cv, u, v, 4, r, r * 4.4, 0.007, (255, 255, 255), 0.55, seed=3)
    # --- printed chrome legend along the back edge (the same winged wordmark
    #     the lower front panel carries and v4 7 reads directly at 8x)
    cv.rect(0, 0, A, 0.128, _hx("#0b0a14"))
    _bz_wing(cv, _du(cv, 0.0), 0.062, -1, 0.46, 0.045, _hx("#9aa0b4"), a=0.75)
    _bz_wing(cv, _du(cv, 0.0), 0.062, 1, 0.46, 0.045, _hx("#9aa0b4"), a=0.75)
    _chrome(cv, "NFL BLITZ", _du(cv, 0.0), 0.022, 0.082, 0.0150, ital=0.28,
            track=0.07, align="c")
    cv.rect(0, 0.124, A, 0.136, _hx("#3c3768"), a=0.9)
    # --- the two small dark legend plates, one per station
    for (u, sd) in ((-0.470, 41), (0.330, 43)):
        _legend(cv, _du(cv, u), 0.790, _du(cv, u + 0.140), 0.960, 3,
                _hx("#0d0c18"), _hx("#b9b4d8"), sd)
    cv.text("1P", _du(cv, -0.462), 0.190, 0.074, (236, 233, 250), 0.0145)
    cv.text("2P", _du(cv, 0.404), 0.190, 0.074, (236, 233, 250), 0.0145)
    _deck_sockets(cv, "nfl-blitz", _hx("#191630"), _hx("#06050c"),
                  bezel_hi=_hx("#cdc9e2"), bezel_lo=_hx("#3a3560"))
    cv.rect(0, 0.976, A, 1, _hx("#2a2748"))
    cv.noise(5.5, 89)
