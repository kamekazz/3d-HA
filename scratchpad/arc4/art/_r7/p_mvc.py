def _mvc_deck(cv):
    """GRANITE TERRAZZO LAMINATE -- and the one deck of my four that carries
    NO game artwork, which I am saying out loud rather than inventing some.

    docs/photos-jpg/Arcade Room v4 6.jpg px (452,268)-(545,362), upscaled 13x
    to scratchpad/arc4/art/ref_g1r7/g1_mvc_deck.png, is the best control-panel
    photograph in the whole set: this deck fills a third of the frame under
    white ceiling cans.  What it shows is a hard, high-contrast BLACK-AND-
    WHITE SPECKLED STONE laminate running edge to edge and over the front lip,
    two black ball-top joysticks, and per player a red row, a green row and a
    blue pair of large round buttons in printed collars.  There is no
    wordmark, no character art, no court, no instruction panel printed on the
    field itself -- the roster's "pale grey/silver panel" is this stone.

    The brief asks for each deck to be printed edge to edge with its own
    game's artwork.  On this machine the photograph refuses, and ROOM-BRIEF is
    explicit that arguing with the photograph is a valid outcome.  So the
    artwork here is the STONE -- authored as real chips with hard edges rather
    than as a grey fill -- plus the two small dark legend plates the photo
    does show at the back of each station, and the printed collars.  What
    stops it reading as a tinted slab is chip contrast (#101013 to #f4f2ec on
    a #8d8c8a ground, a 200-level spread) at a chip size that survives the
    atlas downsample; see `_terrazzo`."""
    A = cv.A
    _terrazzo(cv, 0, 0, A, 1, _hx("#8d8c8a"),
              (_hx("#141417"), _hx("#f2f0ea"), _hx("#5c6068"), _hx("#c6c2b9"),
               _hx("#101013"), _hx("#e4e1d8"), _hx("#74787f"), _hx("#a8a49c")),
              37, n=340, rmin=0.026, rmax=0.062)
    _terrazzo(cv, 0, 0, A, 1, _hx("#8d8c8a"),
              (_hx("#1a1a1e"), _hx("#efece4"), _hx("#6a6e76")),
              91, n=260, rmin=0.014, rmax=0.030)
    # the panel is a shallow wedge: the back edge catches the ceiling cans and
    # the player's edge falls away.  A print gradient, not baked lighting --
    # the laminate itself is darker at the front where it is worn.
    cv.grad(0, 0.62, A, 1.0, (255, 255, 255), (0, 0, 0), a=0.13)
    cv.grad(0, 0, A, 0.16, (255, 255, 255), (0, 0, 0), a=0.10)
    # the two small dark legend plates v4 6 shows at the back of each station
    for (u, sd) in ((-0.335, 11), (0.115, 13)):
        _legend(cv, _du(cv, u), 0.080, _du(cv, u + 0.155), 0.245, 3,
                _hx("#17181c"), _hx("#c8ccd4"), sd)
    cv.text("1P", _du(cv, -0.470), 0.130, 0.076, _hx("#1b1c20"), 0.0145)
    cv.text("2P", _du(cv, 0.412), 0.130, 0.076, _hx("#1b1c20"), 0.0145)
    # a brushed steel nosing along the back edge, and the black T-molding line
    cv.grad(0, 0, A, 0.030, _hx("#e6e8ec"), _hx("#7d828b"))
    cv.rect(0, 0.972, A, 1, _hx("#1b1c20"))
    _deck_sockets(cv, "marvel-vs-capcom", _hx("#25262b"), _hx("#0c0d10"),
                  bezel_hi=_hx("#eceef2"), bezel_lo=_hx("#42464d"))
    cv.noise(11.0, 53)
