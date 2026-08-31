def _mk_deck(cv):
    """STEEL-BLUE FIELD WITH RAKED LIGHT BEAMS, a printed fighter silhouette,
    a dragon roundel and a five-line button legend per station.

    docs/photos-jpg/Arcade Room v4 6.jpg px (470,352)-(600,450), upscaled 11x
    to scratchpad/arc4/art/ref_g1r7/g1_mk_deck.png, resolves this deck better
    than any other frame in the set: a LIGHT steel/sky blue printed field (not
    round 5's navy), pale near-white beams raking front-to-back, a black
    character mark printed low and outboard of the player-one cluster, a
    column of small dark legend type at the back of each station, and large
    YELLOW / RED / WHITE / BLUE buttons.  A hue-bucket dump of that crop
    (ref_g1r7) puts the field at hue 200-215 with value 0.45-0.72, which is
    twice the value round 5 authored.  The maroon T-molding closes the front
    edge -- it is the loudest edge on this machine in every frame."""
    A = cv.A
    cv.grad(0, 0, A, 1, _hx("#5c86a8"), _hx("#89aec8"))
    _mottle(cv, 0, 0, A, 1, [_hx("#3f6d92"), _hx("#a3c6dc"), _hx("#2b5578")],
            13, n=16, rmin=0.16, rmax=0.40, a=0.32)
    # --- raked beams of printed light, edge to edge
    for (u, w0, w1, c, al) in ((-0.30, 0.070, 0.100, "#e8f3fb", 0.55),
                               (0.16, 0.030, 0.048, "#f4fafe", 0.44),
                               (0.62, 0.100, 0.140, "#dceaf6", 0.46),
                               (1.24, 0.044, 0.062, "#f4fafe", 0.40),
                               (1.58, 0.086, 0.120, "#e8f3fb", 0.48),
                               (2.04, 0.036, 0.052, "#f4fafe", 0.36)):
        _beam(cv, u, w0, w1, _hx(c), al)
    # --- the back of the panel falls into shadow-blue under the screen shelf,
    #     and the outer ends darken.  Print, not baked light.
    cv.grad(0, 0, A, 0.30, _hx("#16324c"), _hx("#16324c"), a=0.42)
    cv.grad(0, 0, 0.26, 1, _hx("#1d3d59"), _hx("#1d3d59"), horiz=True, a=0.34)
    cv.grad(A - 0.26, 0, A, 1, _hx("#1d3d59"), _hx("#1d3d59"), horiz=True,
            a=0.34)
    # --- the dragon roundel, printed large and faint at the centre back
    _mk_roundel(cv, _du(cv, -0.055), 0.44, 0.30, _hx("#12354f"),
                _hx("#5f8cae"))
    # --- printed character marks, one per station, low and outboard
    _figure(cv, _du(cv, -0.455), 0.700, 0.44, (14, 18, 26), (14, 18, 26),
            pose=0, a=0.80)
    _figure(cv, _du(cv, 0.455), 0.700, 0.44, (14, 18, 26), (14, 18, 26),
            pose=1, a=0.80)
    # --- the five-line button legend at the back of each station.  Mortal
    #     Kombat is the one machine in this run whose panel legend is famous:
    #     HIGH PUNCH / BLOCK / HIGH KICK over LOW PUNCH / LOW KICK.
    for (u, sd) in ((-0.180, 29), (0.268, 31)):
        _legend(cv, _du(cv, u), 0.085, _du(cv, u + 0.130), 0.310, 5,
                _hx("#0b1d2e"), _hx("#c8d8e6"), sd)
    # --- the wordmark, small, in bone, along the back edge
    cv.rect(0, 0, A, 0.062, _hx("#0b1522"), a=0.92)
    cv.text("MORTAL KOMBAT", _du(cv, 0.0), 0.010, 0.044, _MK_BONE, 0.0090,
            track=0.10, cond=0.82, align="c")
    cv.text("1P", _du(cv, -0.470), 0.108, 0.070, _MK_BONE, 0.0140)
    cv.text("2P", _du(cv, 0.412), 0.108, 0.070, _MK_BONE, 0.0140)
    _deck_sockets(cv, "mortal-kombat", _hx("#132c42"), _hx("#050c15"),
                  bezel_hi=_hx("#dbe4ec"), bezel_lo=_hx("#3a4652"))
    _edge(cv, 0.034, _hx("#3a1014"), _hx("#a3262a"), sides="b")
    cv.noise(6.0, 61)
