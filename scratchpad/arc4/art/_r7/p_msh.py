def _msh_deck(cv):
    """FULL-BLEED COSMIC COMIC COLLAGE -- and a correction to round 5.

    Round 5 drew this deck dark navy with a chevron sweep, on the roster's
    word that "individual controls do not resolve at any magnification".  The
    controls still don't, but the DECK DOES: docs/photos-jpg/Arcade Room v4
    6.jpg px (432,236)-(490,274), upscaled 20x to
    scratchpad/arc4/art/ref_g1r7/g1_msh_deck.png, shows this machine's control
    panel from above at close range and it is the BRIGHTEST deck in the east
    run -- a pale cyan and white energy field with warm character forms and
    heavy black comic keylines running edge to edge.  Classified pixel by
    pixel (ref_g1r7, hue/sat/value buckets) the panel is roughly half near-
    white swirl, a quarter saturated blue, and a quarter warm yellow / green /
    red -- not one dark pixel anywhere on it.  So the round-5 navy was wrong
    and this is the fix.  It also makes MSH the light-and-warm deck of my
    four against MvC's grey stone, MK's steel blue and Blitz's violet."""
    A = cv.A
    W = (255, 255, 255)
    cv.grad(0, 0, A, 1, _hx("#2f89b0"), _hx("#125a80"))
    # --- the cosmic field: big pale energy clouds, edge to edge
    for (u, v, r, c, al) in ((0.26, 0.30, 0.42, "#eaf5fb", 0.92),
                             (0.80, 0.66, 0.44, "#c9e6f4", 0.85),
                             (1.30, 0.20, 0.36, "#f3f9fc", 0.86),
                             (1.72, 0.62, 0.42, "#d6ecf7", 0.86),
                             (2.06, 0.24, 0.32, "#bcdfef", 0.80),
                             (0.52, 0.92, 0.30, "#eaf5fb", 0.72),
                             (1.52, 0.96, 0.28, "#dbeef8", 0.68)):
        cv.disc(u, v, r, _hx(c), a=al, ry=r * 0.78)
    for (u, v, r) in ((0.42, 0.52, 0.19), (1.06, 0.36, 0.15),
                      (1.60, 0.30, 0.17), (2.02, 0.72, 0.16)):
        cv.disc(u, v, r, _hx("#0e4a6e"), a=0.55, ry=r * 0.80)
    _halftone(cv, 0.02, 0.16, 0.66, 0.94, _hx("#0d4b70"), 5, nx=13, a=0.30)
    _halftone(cv, 1.34, 0.10, A - 0.02, 0.70, _hx("#0d4b70"), 9, nx=13,
              a=0.26)
    # --- speed rays: the comic device that ties the whole panel together
    _rays(cv, 1.08, 0.50, 22, 0.16, 1.30, 0.013, _hx("#f4fbff"), 0.34, seed=3)
    # --- warm character forms, keylined black.  These are what make the panel
    #     read as Marvel and not as sky.
    for (u, v, s, body, cape) in ((0.36, 0.44, 0.62, "#c9281f", "#f0c81e"),
                                  (1.14, 0.60, 0.54, "#2f9b4a", "#0f5f8c"),
                                  (1.90, 0.40, 0.58, "#e07a1c", "#c9281f")):
        cv.poly([(u - 0.34 * s, v + 0.52 * s), (u + 0.10 * s, v - 0.46 * s),
                 (u + 0.44 * s, v + 0.10 * s), (u + 0.16 * s, v + 0.56 * s)],
                _hx(cape), a=0.88)
        _figure(cv, u, v, s, _hx(body), (10, 12, 18), pose=(u > 1.5))
    # --- black comic gutters, hard-edged, so the print survives the downsample
    for (u0, u1, w) in ((0.60, 0.86, 0.030), (1.44, 1.66, 0.026)):
        cv.poly([(u0, 0.0), (u0 + w * 3, 0.0), (u1 + w * 3, 1.0), (u1, 1.0)],
                (12, 14, 20), a=0.85)
    # --- printed deck legend along the back edge, and the gold T-molding line
    cv.rect(0, 0, A, 0.132, _hx("#10141c"))
    cv.rect(0, 0.126, A, 0.140, _hx("#c8a24e"), a=0.9)
    cv.text("MARVEL", _du(cv, -0.055), 0.020, 0.086, (240, 243, 249), 0.0165,
            track=0.06, align="c", ital=0.10)
    cv.text("SUPER HEROES", _du(cv, 0.175), 0.036, 0.050, _hx("#5fc8f0"),
            0.0110, track=0.10, align="c")
    cv.text("CAPCOM", _du(cv, -0.400), 0.034, 0.052, _hx("#e8cf8a"), 0.0110,
            track=0.10, align="c")
    _legend(cv, _du(cv, 0.300), 0.760, _du(cv, 0.470), 0.960, 4,
            _hx("#0f1218"), _hx("#9fd6ee"), 17)
    _legend(cv, _du(cv, -0.470), 0.760, _du(cv, -0.300), 0.960, 4,
            _hx("#0f1218"), _hx("#9fd6ee"), 23)
    _edge(cv, 0.028, _hx("#6a5320"), _hx("#e6cd86"), sides="tb")
    _deck_sockets(cv, "marvel-super-heroes", _hx("#101822"), _hx("#05080c"),
                  bezel_hi=_hx("#d8dde4"), bezel_lo=_hx("#3d434c"))
    cv.noise(6.5, 47)
