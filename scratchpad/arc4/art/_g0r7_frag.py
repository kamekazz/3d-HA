# -*- coding: utf-8 -*-
"""Round-7 replacement blocks for art_g0.py.  Spliced by _r7_splice.py."""

HELPERS = '''
# =========================================================================
#  ROUND 7 -- THE CONTROL DECKS
# =========================================================================
# Four critics failed round 6 on the same surface, in the same words: the
# pushbuttons are "painted into the control-deck texture ... flat 2-3px
# coloured lozenges", every deck wears "the identical control deck", and "in
# the photo the deck is the largest continuous surface facing camera and it is
# printed edge-to-edge with game art on every machine; in the render every deck
# is an empty plane with a faint round ghost decal."
#
# ALL THREE OF THOSE ARE TRUE, AND THE ARITHMETIC SAYS WHY.
#
#   atlas4.SIZE["deck"] = 52 and a deck quad is ~2.35:1, so a deck packs at
#   80 x 34 TEXELS for 2.16 x 0.92 ft -- 37 texels per foot.  Round 5 drew its
#   button collars as `cv.ring(..., 0.096, 0.096, 0.018, ...)` at alpha 0.45:
#   a 3.3-texel radius with a 0.6-TEXEL stroke at 45% opacity.  After atlas4
#   supersamples, box-averages and re-quantises to QUANT 20 that ring is
#   sub-quantum -- it lands on the same output level as the field around it and
#   ceases to exist.  "A faint round ghost decal" is a generous reading of it.
#
#   And in the judged frames the decks are 34-75 px/ft (full_east puts NBA Jam
#   at ~37 px/ft, full_north puts Pac-Man at ~75), seen from ~1.8 ft above a
#   near-horizontal surface, so the deck's 0.92 ft depth is foreshortened to a
#   third of that.  A 2.25 in button is 6-14 px across the u axis and 2-5 px
#   along v.  "2-3 px lozenges" is what a REAL button measures there.
#
# So this round does three things and claims nothing more:
#
#   1.  The buttons stop being texture.  DECKS below is the geometry spec, and
#       it is authored at the sizes the PHOTOGRAPHS give -- which are BIGGER
#       than round 5 assumed (see the measurement note over DECKS).  Their read
#       has to come from dome relief, saturation and a collar that survives
#       quantisation, not from an inflated radius.
#   2.  Every collar is redrawn as a FILLED disc with a hard rim at 1.4-1.5x
#       the button radius, at full alpha, in a colour that steps at least 40
#       levels off the field it sits on.  4-5 texel radius, not 0.6-texel
#       stroke.
#   3.  The deck FIELD is drawn as the photograph's own artwork, edge to edge,
#       in shapes no smaller than ~3 texels: hardwood and white court lines for
#       NBA Jam, a tan-and-brick city street for Turtles, a grass fairway for
#       Golden Tee -- and, for Pac-Man, an honest black overlay, because that
#       is what four frames of it show.  See NOTES["pac-man.deck"].
#
# Every length below that is quoted in FEET is converted with _ft(): a _Cv
# LENGTH is a fraction of the panel's HEIGHT, and a deck panel is 0.92 ft deep
# in every one of ar2's rows, so `feet / 0.92` is exact rather than a fudge.

DECK_H_FT = 0.92            # ar2: (fd - 0.06) - (ft + 0.04), every machine


def _ft(v):
    """A real length in FEET as a _Cv LENGTH (a fraction of panel height)."""
    return v / DECK_H_FT


def _du(u):
    """DECKS' u (-0.5 .. +0.5) as the .deck tile's own u (0 .. 1)."""
    return u + 0.5


def _collar(cv, u, v, r_ft, shade, k=1.26, a=0.42, edge=None, ea=0.8):
    """The seat a pushbutton sits in, as the PHOTOGRAPHS show it -- and no more.

    Round 7's first pass drew this as a filled disc with a bright rim at 1.45x
    the button, and the preview sheet came back as a row of eyeballs: on NBA
    Jam and Turtles the collars out-weighed the printed art they were sitting
    on, which is the opposite of the defect being fixed.  Look at
    art/r7/nba_deck_zoom.png -- there is NO printed collar on that deck.  A
    real button's bezel IS its collar; the artwork runs right up to the hole
    and the only thing under the flange is a soft shadow.

    So this is a soft dark seat at 1.26x the button radius, and optionally a
    thin bezel edge.  Nothing is drawn inside `r`: the cap covers it, and if
    the geometry ever fails to build you see the deck art, not a black hole.
    """
    ro = _ft(r_ft * k)
    cv.ell(_du(u), v, ro, ro, shade, a)
    if edge is not None:
        ri = _ft(r_ft) * 1.05
        cv.ring(_du(u), v, ri, ri, _ft(r_ft) * 0.24, edge, ea)


def _stickpad(cv, u, v, r_ft, face, rim=None, a=0.94):
    """The black dust washer under a joystick.  This one IS in every photo of
    every one of these decks, as a hard black disc a little wider than the
    button next to it, so it is drawn solid."""
    ro = _ft(r_ft)
    cv.ell(_du(u), v, ro, ro, face, a)
    if rim is not None:
        cv.ring(_du(u), v, ro * 0.86, ro * 0.86, ro * 0.18, rim, a * 0.7)


def _text_fit(cv, s, cu, cvv, h, col, w, track=0.14, aspect=0.64, pad=0.014,
              **kw):
    """`cv.text`, but it CANNOT run off the panel.

    ROUND 7 BUG FIX.  Round 5 set "PAC-MAN" at h 0.215 / aspect 0.68 centred at
    u 0.170.  Its advance width is 0.488 in u, so it spanned -0.074 .. 0.414 --
    the P fell off the left edge and the render read "AC-MAN", which the brief
    called out by name.  Nothing on a deck sets type directly any more; it all
    comes through here, which shrinks the cap height until the string fits and
    then slides it inside the margins.  Returns the (centre, height) used.
    """
    def width(hh):
        gw = hh * aspect
        adv = gw * (1.0 + track)
        return (adv * len(s) - (adv - gw)) * cv.kx
    tw = width(h)
    room = 1.0 - 2.0 * pad
    if tw > room:
        k = room / tw
        h *= k
        w *= k
        if "ow" in kw:
            kw["ow"] = kw["ow"] * k
        tw = width(h)
    cu = min(max(cu, pad + tw * 0.5), 1.0 - pad - tw * 0.5)
    cv.text(s, cu, cvv, h, col, w, track=track, aspect=aspect, **kw)
    return cu, h


'''

NBA_DECK = '''@_panel("nba-jam.deck")
def _nba_deck(cv):
    """ROUND 7.  The hardwood court, redrawn to survive 80 x 34 texels.

    Evidence: v4 7 px (288,248)-(370,330) at 14x -- art/r7/nba_deck_zoom.png.
    It is the clearest control deck in the whole set of photographs and it
    shows, unambiguously: warm terracotta boards running the LENGTH of the
    deck; THICK white court lines (a sideline sweeping the full width, a centre
    circle, a key and a three-point arc); a red-and-white NBA JAM starburst
    logo lying on the boards at the LEFT end; deep red T-molding round the
    edge; and eight large round buttons in ORANGE, WHITE, RED and CYAN
    SCATTERED across the court lines rather than ranked in rows.

    Scale check on the same crop: the T-molding measures 2.5 px and real
    T-molding is 0.75 in, so 0.30 in/px.  The deck then measures 24.6 in wide
    (right for a 2.30 ft carcase seen slightly foreshortened) and the buttons
    measure 7.5 px = 2.25 IN -- jumbo, not the 1.4 in round 5 assumed.

    Tile TOP = the deck's back edge at the screen; BOTTOM = the player's edge.
    """
    _boards(cv, 0.0, 0.0, 1.0, 1.0, 6, "#c47c46", "#9b5a2c", "#6b3a16", 707)
    _wear(cv, 0.0, 0.0, 1.0, 1.0, 15.0, 88, 3, vert=False)

    W = "#f6f1e2"
    lw = 0.072                      # 2.4 texels -- round 5 drew 0.030
    cv.stroke([(0.045, 0.115), (0.955, 0.115), (0.955, 0.885), (0.045, 0.885)],
              W, lw, closed=True)
    cv.seg((0.500, 0.115), (0.500, 0.885), W, lw)
    cv.ring(0.500, 0.500, 0.300, 0.300, lw, W)
    for (bu, sgn) in ((0.045, 1.0), (0.955, -1.0)):
        cv.stroke([(bu, 0.290), (bu + sgn * 0.150, 0.290),
                   (bu + sgn * 0.150, 0.710), (bu, 0.710)], W, lw)
        cv.ring(bu + sgn * 0.150, 0.500, 0.210, 0.210, lw, W)
        cv.arc(bu, 0.500, 0.960, 0.960,
               -math.pi * 0.42 if sgn > 0 else math.pi * 0.58,
               math.pi * 0.42 if sgn > 0 else math.pi * 1.42, lw, W)

    # the wordmark lying on the boards at the left end -- burst, then type
    _burst(cv, 0.150, 0.500, 0.520, 14, "#f4efe0", 0.085, 0.20, 0.56, 0.92)
    cv.ell(0.150, 0.500, 0.300, 0.300, "#2a1408", 0.55)
    _text_fit(cv, "NBA", 0.150, 0.395, 0.270, "#d8202e", 0.055, track=0.06,
              aspect=0.74, slant=0.10, outline="#f4e8cc", ow=0.040)
    _text_fit(cv, "JAM", 0.150, 0.645, 0.270, "#d8202e", 0.055, track=0.06,
              aspect=0.74, slant=0.10, outline="#f4e8cc", ow=0.040)

    # collars: hardwood is light, so the collar is DARK with a pale rim
    for (u, v) in _NBA_STICK_UV:
        _stickpad(cv, u, v, 0.135, "#17130f", "#6d5a44")
    for (u, v) in _NBA_BTN_UV:
        _collar(cv, u, v, 0.082, "#241811", rim="#e2d2ac", k=1.46, rimw=0.30,
                bore="#100b08", bore_a=0.5)

    cv.vgrad(0.0, 0.930, 1.0, 1.0, "#8c2028", "#4a1016")        # T-molding
    cv.seg((0.0, 0.930), (1.0, 0.930), "#100a0a", 0.030, 0.9)
    cv.vgrad(0.0, 0.0, 1.0, 0.048, "#6e1a22", "#3c0e12")
    _grain(cv, 9.0, 11)


'''

TM_DECK = '''@_panel("tmnt-turtles-in-time.deck")
def _tm_deck(cv):
    """ROUND 7.  The tan-and-brick New York street, rebuilt from the photograph.

    Evidence: v4 7 px (330,290)-(470,400) at 10x and (380,300)-(470,370) at
    16x -- art/r7/tm_deck_far.png, tm_deck_zoom.png.  Round 5 drew this deck as
    a DARK brick wall.  It is not: it is a bright warm TAN ground (a sunset
    street) with a brown-red brick block standing in it, a violet night sky
    over the far end, TURTLES wordmarks cascading diagonally across it in green
    and blue, a magenta splash, square character-portrait decals along the
    player's edge and a pale instruction label at the back.  Bright green
    T-molding all round.

    It is also the only deck in the room with a ROW OF SMALL VIOLET BUTTONS
    across its back edge (clearly visible in tm_deck_far.png), and the only one
    whose main buttons are jumbo domes.  Both are in DECKS.
    """
    cv.fill("#dcae76")
    cv.vgrad(0.0, 0.0, 1.0, 1.0, "#efc793", "#c1854a")          # sky -> street
    cv.hgrad(0.0, 0.0, 0.34, 1.0, "#3a2a5c", "#dcae76")         # night end
    cv.rect(0.0, 0.0, 0.150, 1.0, "#33254f")
    _stars(cv, [(0.0, 0.0), (0.230, 0.0), (0.230, 0.62), (0.0, 0.62)], 61, 26)

    # the block of brownstones -- the thing that makes this deck read as a city
    _bricks(cv, 0.130, 0.280, 0.520, 0.905, 5, "#a8593a", "#8d452c", "#40241a",
            38, 1.0, 12.0)
    _window_rows(cv, 0.155, 0.330, 0.495, 0.860, 4, 4, "#f0cf72", "#2b1c22",
                 71, 0.38)
    cv.rect(0.130, 0.262, 0.520, 0.302, "#3a221a")              # cornice
    _bricks(cv, 0.520, 0.400, 0.760, 0.905, 4, "#8f4a30", "#743c26", "#361e16",
            39, 1.0, 10.0)
    _window_rows(cv, 0.542, 0.440, 0.740, 0.865, 3, 3, "#e6c26a", "#26191e",
                 72, 0.30)
    cv.rect(0.520, 0.386, 0.760, 0.418, "#321d16")
    cv.rect(0.760, 0.520, 0.905, 0.905, "#7a4830", 0.85)        # far block
    _window_rows(cv, 0.778, 0.556, 0.890, 0.870, 2, 3, "#d8b262", "#241820",
                 73, 0.28)

    cv.rect(0.0, 0.905, 1.0, 0.960, "#38343a")                  # the street
    cv.seg((0.130, 0.934), (0.360, 0.934), "#8a867c", 0.030, 0.6)
    cv.seg((0.560, 0.934), (0.790, 0.934), "#8a867c", 0.030, 0.6)

    # the wordmarks, cascading down-right the way the photograph runs them
    cv.ell(0.470, 0.250, 0.170, 0.130, "#a8288e", 0.9)          # splash
    cv.ell(0.470, 0.250, 0.105, 0.078, "#d84ab4", 0.9)
    _tm_logo(cv, 0.600, 0.420, 0.300)
    _text_fit(cv, "TURTLES", 0.855, 0.185, 0.195, "#3fa8ee", 0.038, track=0.08,
              aspect=0.74, slant=0.07, outline="#10203c", ow=0.034)

    # the pale instruction label the photo shows at the back edge
    cv.rect(0.300, 0.075, 0.470, 0.205, "#e6ecf2")
    cv.rect(0.312, 0.090, 0.458, 0.190, "#b9cad8")
    for vv in (0.112, 0.142, 0.172):
        cv.seg((0.322, vv), (0.448, vv), "#2c3c4c", 0.022, 0.8)

    # the square character portraits along the player's edge
    for (i, u0) in enumerate((0.020, 0.372, 0.724)):
        bd = ("#d8322c", "#3a6ee0", "#e08a1c")[i]
        cv.rect(u0, 0.790, u0 + 0.128, 0.972, "#f2ecdc")
        cv.rect(u0 + 0.012, 0.806, u0 + 0.116, 0.956, "#20301c")
        cv.ell(u0 + 0.064, 0.892, 0.130, 0.130, "#4faa3c")
        cv.rect(u0 + 0.020, 0.856, u0 + 0.108, 0.888, bd)

    for (u, v) in _TM_STICK_UV:
        _stickpad(cv, u, v, 0.140, "#141110", "#7a6a52")
    for (u, v) in _TM_BTN_UV:
        _collar(cv, u, v, 0.098, "#1a1512", rim="#f0dfae", k=1.40, rimw=0.28,
                bore="#0d0b0a", bore_a=0.5)
    for (u, v) in _TM_ADM_UV:
        _collar(cv, u, v, 0.042, "#171420", rim="#c8bcd8", k=1.55, rimw=0.34,
                bore=None)

    cv.rect(0.0, 0.0, 1.0, 0.042, "#4fc23a")                    # green molding
    cv.vgrad(0.0, 0.960, 1.0, 1.0, "#57cd3e", "#1f6a22")
    _grain(cv, 8.0, 39)


'''

PM_DECK = '''@_panel("pac-man.deck")
def _pm_deck(cv):
    """ROUND 7.  A BLACK deck, and that is the finding, not a shortcut.

    Evidence: v3 1 px (590,620)-(700,700) at 10x, v4 3 px (70,150)-(130,220) at
    14x and v4 7 px (0,175)-(45,235) at 18x -- art/r7/pac_deck_v31.png,
    pac_v43.png, pac_deck_v47.png.  v4 3 looks almost straight DOWN onto this
    deck, and there is no printed graphic on it in any of the three: it is a
    plain black overlay with a maroon T-molding lip along the front, a row of
    small round white / red / blue buttons across it, one red ball-top stick,
    and ONE pale rectangular instruction label at the right.  The roster agrees
    ("Black deck with a maroon lip along its front edge").

    So this deck is NOT given invented artwork.  Round 5's big yellow "PAC-MAN"
    legend across it was invented, it is not in any frame, and it is removed --
    which is also the honest fix for the "AC-MAN" clipping the brief named: the
    string was 0.488 wide in u centred at u 0.170, so the P was off-panel.  The
    legend is gone; the type that remains anywhere on a deck now goes through
    _text_fit, which cannot run off the panel.

    What this deck IS given is everything the photographs DO show, at a size
    that survives 80 x 34 texels: a lengthwise brushed sheen (the overlay is
    glossy and catches the cove light in v3 1), the bright chrome trim strip
    along the back edge, the pale instruction label, the maroon lip, and
    collars strong enough to read.  Authored LIFTED, because a2kit multiplies
    this tile by ART_DK (#4c4c4c) -- DECK_MAT_REQUEST keeps it there.
    """
    cv.vgrad(0.0, 0.0, 1.0, 1.0, "#84848e", "#4e4e58")
    _wear(cv, 0.0, 0.0, 1.0, 1.0, 16.0, 24, 3, vert=True)
    _sheen(cv, 0.0, 0.060, 1.0, 0.900, 22.0, 241, 4)
    cv.vgrad(0.0, 0.0, 1.0, 0.062, "#cfcfd8", "#6e6e78")        # chrome trim
    cv.seg((0.0, 0.070), (1.0, 0.070), "#2a2a32", 0.026, 0.85)

    # the pale instruction label -- the one printed thing on this deck
    cv.rect(0.700, 0.180, 0.930, 0.420, "#d6dae2")
    cv.rect(0.712, 0.198, 0.918, 0.402, "#aeb6c2")
    for vv in (0.238, 0.286, 0.334, 0.382):
        cv.seg((0.726, vv), (0.904, vv), "#33383f", 0.026, 0.85)

    for (u, v) in _PM_STICK_UV:
        _stickpad(cv, u, v, 0.120, "#101014", "#8e8e9a")
    for (u, v) in _PM_BTN_UV:
        _collar(cv, u, v, 0.055, "#1b1b21", rim="#c6c6d0", k=1.50, rimw=0.34,
                bore="#0a0a0d", bore_a=0.6)

    cv.vgrad(0.0, 0.885, 1.0, 1.0, "#e05460", "#8c2530")        # maroon lip
    cv.seg((0.0, 0.885), (1.0, 0.885), "#141014", 0.026, 0.9)
    _grain(cv, 9.0, 25)


'''

GT_DECK = '''@_panel("golden-tee-3d-golf.deck")
def _gt_deck(cv):
    """ROUND 7.  A full-bleed grass fairway -- and the yellow legend strip is
    NOT on it.

    Evidence: v4 7 px (112,180)-(175,205) at 20x and v4 6 px (360,190)-(440,230)
    at 16x -- art/r7/gt_deck_zoom.png, gt_deck_v46.png.  Both show the lit
    three-panel yellow strip standing on the DARK VERTICAL FACE ABOVE the deck,
    separated from the green by a hard dark step, and the deck itself as bright
    grass green from edge to edge with pale mown highlights, a pale bunker each
    side and the white trackball reading as the brightest thing on it.

    The roster describes the deck as "two printed bands", the upper one the
    yellow legend.  I am departing from that one clause, and saying so: the
    bezel panel (golden-tee-3d-golf.bezel) ALREADY draws that strip at its foot
    where the geometry puts it, and round 5 drew it a SECOND time across the
    back 15% of the deck, so the render carried two yellow strips where the
    photograph has one -- and it spent 5 of the deck's 34 rows on lettering at
    3.5 texels cap height, which is unreadable by construction.  The deck keeps
    only the dark green step the photo shows at its back edge.
    """
    cv.vgrad(0.0, 0.0, 1.0, 1.0, "#74ac4c", "#4e8232")
    for j in range(5):                                          # mown stripes
        v0 = 0.070 + j * 0.186
        if j % 2 == 0:
            cv.rect(0.0, v0, 1.0, v0 + 0.093, "#e8f2c4", 0.14)
    cv.poly([(0.0, 0.330), (0.300, 0.245), (0.640, 0.335), (1.0, 0.260),
             (1.0, 0.070), (0.0, 0.120)], "#3d6c2c")            # rough
    cv.poly([(0.0, 0.955), (1.0, 0.920), (1.0, 1.0), (0.0, 1.0)], "#2f5722")
    cv.ell(0.735, 0.545, 0.290, 0.250, "#94c669")               # putting green
    cv.ell(0.735, 0.545, 0.230, 0.196, "#a8d878")
    cv.ell(0.180, 0.640, 0.235, 0.205, "#ddd0a0")               # bunkers
    cv.ell(0.180, 0.640, 0.185, 0.158, "#f0e6c2")
    cv.ell(0.930, 0.320, 0.165, 0.140, "#e2d6a8")
    cv.poly([(0.290, 1.00), (0.455, 0.320), (0.545, 0.320), (0.415, 1.00)],
            "#cdd4ae", 0.40)                                    # cart path
    cv.seg((0.735, 0.545), (0.735, 0.330), "#f4f4ee", 0.040)    # flagstick
    cv.poly([(0.735, 0.330), (0.815, 0.360), (0.735, 0.392)], "#e03a2c")
    _wear(cv, 0.0, 0.120, 1.0, 1.0, 11.0, 56, 3, vert=False)

    cv.vgrad(0.0, 0.0, 1.0, 0.070, "#15200c", "#33481e")        # the dark step
    cv.seg((0.0, 0.072), (1.0, 0.072), "#101a08", 0.024, 0.85)

    _stickpad(cv, _GT_TRACK_UV[0], _GT_TRACK_UV[1], 0.163, "#161c12", "#9aa88c")
    for (u, v) in _GT_BTN_UV:
        _collar(cv, u, v, 0.062, "#181f14", rim="#e6eed2", k=1.52, rimw=0.32,
                bore="#0c110a", bore_a=0.55)
    _grain(cv, 8.0, 57)


'''

LAYOUT = '''
# ---- THE CONTROL LAYOUT, HELD AS DATA -----------------------------------
# The printed collars above and the DECKS geometry spec at the foot of this
# module are BOTH built from these lists, so a collar and the control that sits
# in it cannot drift apart.  Round 5 wrote the two out separately and they did
# drift -- the collars ended up on a 3-over-3 grid the spec never described.
#
#   button  (u, v, radius_ft, colour)
#   stick   (u, v, top, top_d_ft, top_colour)
#   u  -0.5 .. +0.5 across the machine, v 0 at the back edge .. 1 at the
#      player's edge.  EVERY LENGTH IN FEET.
#
# BUTTON SIZES ARE MEASURED, NOT ASSUMED.  Scale solved off v4 7 with the
# T-molding as the ruler (real T-molding is 0.75 in; it measures 2.5 px in the
# 14x NBA crop, so 0.30 in/px, which then returns the deck width as 24.6 in --
# right for a 2.30 ft carcase, so the ruler checks out).  On that scale NBA
# Jam's buttons are 7.5 px = 2.25 IN across.  Round 5 specified r 0.058 ft
# (1.4 in) for them, which is a standard Happ bezel and is 40% too small.
#
#   Pac-Man     1.32 in  r 0.055   the photo calls them "small" and they are
#   Golden Tee  1.49 in  r 0.062   small, either side of the trackball
#   NBA Jam     1.97 in  r 0.082   large; 2.25 in measured, 1.97 built (see
#                                  NOTES -- the collars would touch at 2.25)
#   Turtles     2.35 in  r 0.098   jumbo; the biggest in the room, and that is
#                                  most of what makes this deck read
#   trackball   3.00 in  r 0.125   the standard Golden Tee ball, unchanged

_PM_STICKS = [(-0.160, 0.575, "ball", 0.118, "#d8323a")]
_PM_BUTTONS = [
    (-0.430, 0.500, 0.055, "#eceae2"), (-0.340, 0.560, 0.055, "#eceae2"),
    (-0.010, 0.470, 0.055, "#d8262c"), (0.075, 0.545, 0.055, "#eceae2"),
    (0.160, 0.470, 0.055, "#eceae2"), (0.245, 0.545, 0.055, "#2f6ad8"),
    (0.330, 0.470, 0.055, "#eceae2"), (0.415, 0.545, 0.055, "#d8262c"),
]

_NBA_STICKS = [(-0.330, 0.520, "ball", 0.128, "#141418"),
               (0.075, 0.600, "bat", 0.150, "#d8323a")]
_NBA_BUTTONS = [
    (-0.435, 0.640, 0.082, "#2fa8e0"), (-0.160, 0.300, 0.082, "#e2661e"),
    (-0.075, 0.520, 0.082, "#eceae2"), (-0.180, 0.740, 0.082, "#d8262c"),
    (0.245, 0.310, 0.082, "#2fa8e0"), (0.330, 0.540, 0.082, "#e2661e"),
    (0.240, 0.770, 0.082, "#eceae2"), (0.430, 0.410, 0.082, "#d8262c"),
]

_TM_STICKS = [(-0.300, 0.520, "ball", 0.140, "#3ab8e8"),
              (0.140, 0.640, "ball", 0.140, "#17171b")]
_TM_BUTTONS = [
    (-0.150, 0.310, 0.098, "#35c6ee"), (-0.055, 0.470, 0.098, "#35c6ee"),
    (-0.135, 0.645, 0.098, "#35c6ee"),
    (0.300, 0.310, 0.098, "#f2cc22"), (0.400, 0.470, 0.098, "#f2cc22"),
    (0.310, 0.645, 0.098, "#f2cc22"),
    (0.055, 0.330, 0.098, "#d8221c"),
]
_TM_ADMIN = [(-0.320, 0.115, 0.042, "#7a52d8"), (-0.192, 0.115, 0.042, "#7a52d8"),
             (-0.064, 0.115, 0.042, "#7a52d8"), (0.064, 0.115, 0.042, "#7a52d8"),
             (0.192, 0.115, 0.042, "#7a52d8"), (0.320, 0.115, 0.042, "#7a52d8")]

_GT_TRACK = (0.0, 0.545, 0.125, "#f2f2ec")
_GT_BUTTONS = [(-0.330, 0.400, 0.062, "#d8323a"),
               (0.330, 0.400, 0.062, "#d8323a")]


def _uv(rows):
    return tuple((r[0], r[1]) for r in rows)


_PM_STICK_UV = _uv(_PM_STICKS)
_PM_BTN_UV = _uv(_PM_BUTTONS)
_NBA_STICK_UV = _uv(_NBA_STICKS)
_NBA_BTN_UV = _uv(_NBA_BUTTONS)
_TM_STICK_UV = _uv(_TM_STICKS)
_TM_BTN_UV = _uv(_TM_BUTTONS)
_TM_ADM_UV = _uv(_TM_ADMIN)
_GT_TRACK_UV = (_GT_TRACK[0], _GT_TRACK[1])
_GT_BTN_UV = _uv(_GT_BUTTONS)


'''

DECKS_BLOCK = '''DECKS = _R7_DECKS


# =========================================================================
'''

DECKS_HEAD = '''# =========================================================================
#  DECKS -- the control layout, for ar2.upright() to place as GEOMETRY
# =========================================================================
# ROUND 7.  Round 5 authored this table and it did not reach the render: the
# joysticks were built, the buttons were not, and what shipped was round 4's
# painted lozenge cluster repeated on all six machines.  The engine agent is
# building real domed geometry from this table now, so it is written to be
# consumed without a judgement call left in it.
#
# ---- COORDINATE FRAME.  UNCHANGED from round 5, deliberately -- it is also
#      the `.deck` art tile's own frame, and the printed collars above are
#      generated from these same rows, so a collar and its control cannot
#      drift apart.
#
#   u   across the machine, -0.5 .. +0.5.   local x = u * (bw - 0.12)
#       u = -0.5 is the x0 edge, which is the LEFT edge of the .deck tile.
#       The tile's own u is simply u + 0.5.
#   v   along the deck, 0 at the BACK edge (z = ft + 0.04, up against the
#       screen) and 1 at the player's edge (z = fd - 0.06).
#           local z = (ft + 0.04) + v * ((fd - 0.06) - (ft + 0.04))
#       and with ar2's DECK_OUT that bracket is exactly 0.92 ft on every
#       machine, which is what `_ft()` above divides by.
#   y   every control sits ON the deck surface, y = dy (dy already includes
#       the plinth by the time upright() reaches its control loop).
#
#   EVERY LENGTH IN THIS TABLE IS IN FEET.
#
# ---- WHAT EACH KEY MEANS.
#   sticks[]    u, v            centre on the deck
#               shaft_r         shaft radius; shaft_h its height above the deck
#               top             "ball" | "bat" | "none"
#               top_d           ball DIAMETER, or a bat top's overall length
#               top_color       authored sRGB
#               pad_r           the black dust washer already PRINTED under it;
#                               geometry does not need to build it
#   buttons[]   u, v            centre
#               r               the button's own radius (its bezel edge)
#               h               HOW PROUD OF THE DECK IT STANDS, in feet
#               shape           "round" on every machine here -- no squares
#               profile         "convex" = a short cylinder with a DOMED cap
#               dome_rise       cap rise above the cylinder shoulder, in feet
#               cap_r           cap radius at the shoulder (r_top for a taper)
#               color           authored sRGB
#               collar_r        the PRINTED collar's radius, already in the
#                               .deck tile.  Do not re-draw it; do not build
#                               geometry out to it.
#   trackball   u, v, r, color  a sphere HALF-SUNK in the deck: a hemisphere of
#                               radius r centred at y = dy.  bezel_r is the
#                               printed ring; no geometry needed for it.
#
# ---- HOW BIG THESE ARE ON SCREEN, so nobody is surprised.
#   Judged frames put the decks at 34-75 px/ft (full_east -> NBA Jam ~37,
#   full_north -> Pac-Man ~75), and a deck is near-horizontal seen from ~1.8 ft
#   above, so v is foreshortened roughly 3:1.  A 1.97 in NBA Jam button is then
#   about 6 px across u and 2 px along v.  THAT IS WHAT THE REAL BUTTON
#   MEASURES; no honest radius makes it bigger.  What buys the read is
#   (a) the dome -- a domed cap catches a specular the flat rect_up could not,
#   (b) saturation -- these are authored at full chroma, and
#   (c) the collar, which doubles the mark to ~9 px and is drawn at full alpha
#       with a hard rim so QUANT 20 cannot swallow it.
#
# ---- MATERIAL.  See BUTTON_MAT_REQUEST below.  a2kit's `a2hw` is roughness
#      0.42 and every up-facing cap blows out against the ceiling cans; these
#      caps and the trackball want their own rougher material.
'''

DECKS_BODY = '''

def _mk_btn(row, h, dome, cap_k, collar_k):
    return {"u": row[0], "v": row[1], "r": row[2], "h": h,
            "shape": "round", "profile": "convex",
            "dome_rise": dome, "cap_r": round(row[2] * cap_k, 4),
            "color": row[3], "collar_r": round(row[2] * collar_k, 4)}


def _mk_stick(row, shaft_r, shaft_h, pad_r, shaft_color="#141416"):
    return {"u": row[0], "v": row[1], "shaft_r": shaft_r, "shaft_h": shaft_h,
            "shaft_color": shaft_color, "top": row[2], "top_d": row[3],
            "top_color": row[4], "pad_r": pad_r}


DECKS = {
    # --------------------------------------------------------------- PAC-MAN
    # v3 1 (590,620)-(700,700), v4 3 (70,150)-(130,220), v4 7 (0,175)-(45,235).
    # ONE red ball-top left of centre and ONE ROW of small round buttons in
    # white, red and blue running the width -- the only single-row deck in the
    # room, and the only one with SMALL buttons.  Nothing else on this machine
    # is arranged in rows, so the row is the identity of the deck.
    "pac-man": {
        "why": "single red ball-top stick left of centre; one shallow row of "
               "eight SMALL (1.3 in) round buttons in white / red / blue "
               "across the full width. No second station, no arc, no cluster.",
        "sticks": [_mk_stick(s, 0.038, 0.180, 0.104) for s in _PM_STICKS],
        "buttons": [_mk_btn(b, 0.028, 0.011, 0.74, 1.32) for b in _PM_BUTTONS],
    },
    # --------------------------------------------------------------- NBA JAM
    # v4 7 (288,248)-(370,330) at 14x -- art/r7/nba_deck_zoom.png, the best
    # control-deck photograph in the set.  TWO stations, and they are NOT
    # mirror images: the left stick is a BLACK BALL top, the right one is a RED
    # BAT top (a tapered handle, clearly not a sphere, on a black dust washer).
    # The eight buttons are SCATTERED around the painted court lines at four
    # different v values -- no two of them share a row.
    "nba-jam": {
        "why": "two stations, one BLACK BALL top and one RED BAT top; eight "
               "large (2.0 in) round buttons in orange / white / red / cyan "
               "SCATTERED across the court lines, not ranked. NO trackball on "
               "this machine -- re-checked in round 5 and again in round 7; "
               "the white disc in the crop is a button, and Golden Tee's "
               "trackball two machines away is visibly a different object.",
        "sticks": [_mk_stick(_NBA_STICKS[0], 0.042, 0.190, 0.118),
                   _mk_stick(_NBA_STICKS[1], 0.040, 0.215, 0.118)],
        "buttons": [_mk_btn(b, 0.036, 0.015, 0.76, 1.28) for b in _NBA_BUTTONS],
    },
    # -------------------------------------------------------- TURTLES IN TIME
    # v4 7 (330,290)-(470,400) at 10x -- art/r7/tm_deck_far.png.  The JUMBO
    # deck: seven 2.35 in domes, three cyan on the left station, three yellow
    # on the right, and one red between them.  The ball tops are CYAN and
    # BLACK -- not yellow; the yellow on this machine is in the buttons.  And
    # it is the only deck in the room with a ROW OF SIX SMALL VIOLET admin
    # buttons across its back edge, which is plainly visible in that crop.
    "tmnt-turtles-in-time": {
        "why": "two ball tops, CYAN and BLACK; seven JUMBO 2.35 in domes -- "
               "three cyan, three yellow, one red -- plus a row of six small "
               "violet admin buttons along the back edge. The real cabinet is "
               "four-player; this carcase is 2.04 ft and takes two stations.",
        "sticks": [_mk_stick(s, 0.044, 0.200, 0.126) for s in _TM_STICKS],
        "buttons": ([_mk_btn(b, 0.046, 0.019, 0.78, 1.24) for b in _TM_BUTTONS]
                    + [_mk_btn(b, 0.018, 0.007, 0.72, 1.45)
                       for b in _TM_ADMIN]),
    },
    # --------------------------------------------------- GOLDEN TEE 3D GOLF
    # v4 7 (112,180)-(175,205) at 20x and v4 6 (360,190)-(440,230) at 16x --
    # art/r7/gt_deck_zoom.png, gt_deck_v46.png.  A white trackball centred, two
    # small buttons either side, NO joystick.  It is the only trackball in the
    # room and the only deck with no stick at all.
    "golden-tee-3d-golf": {
        "why": "white 3 in trackball centred, two small (1.5 in) buttons "
               "either side, NO joystick. The trackball is the machine's whole "
               "control interface and it is the only one in the room.",
        "sticks": [],
        "trackball": {"u": _GT_TRACK[0], "v": _GT_TRACK[1], "r": _GT_TRACK[2],
                      "color": _GT_TRACK[3], "bezel_r": 0.176,
                      "bezel_color": "#161c12"},
        "buttons": [_mk_btn(b, 0.030, 0.012, 0.74, 1.34) for b in _GT_BUTTONS],
    },
}


# =========================================================================
#  BUTTON_MAT_REQUEST -- the third open defect the round-6 integrator flagged
# =========================================================================
# "a2kit's HW material a2hw is roughness 0.42, so every up-facing cap -- ball
#  tops, button crowns, Golden Tee's trackball -- blows out against the ceiling
#  cans.  The trackball reads as a bright white dome."
#
# That is one roughness value shared by three runs, and it is a2kit's file, not
# this one, so it is REQUESTED rather than edited.  A moulded polycarbonate
# button crown is not a machined metal part: it is satin, and it is the LEAST
# specular thing on the machine after the vinyl.  Values asked for, with the
# reason each one is what it is:
#
#   a2btn   roughness 0.72  metallic 0.0   coloured button crowns and ball tops.
#                                          Injection-moulded translucent
#                                          plastic.  0.42 puts a mirror
#                                          highlight on a 6 px disc and the
#                                          disc becomes a white dot.
#   a2ball  roughness 0.70  metallic 0.0   Golden Tee's trackball, SEPARATELY,
#                                          because it is the one white cap in
#                                          the room and it is 3 in across, so
#                                          it is the piece the blow-out is
#                                          actually visible on.  Authored
#                                          #f2f2ec, NOT #ffffff, so it has
#                                          headroom before it clips.
#   a2shaft roughness 0.55  metallic 0.0   joystick shafts and dust washers --
#                                          these ARE semi-gloss black plastic
#                                          and want to stay a little shiny.
#
# NONE of these should carry emissive.  ar2.BUTTONS' existing emissive is fine
# on a saturated coloured cap and must NOT be applied to the white buttons or
# the trackball: a white cap with emissive blooms, which is exactly the defect
# being reported.
BUTTON_MAT_REQUEST = {
    "a2btn": {"roughness": 0.72, "metallic": 0.0,
              "for": "coloured button crowns, ball tops"},
    "a2ball": {"roughness": 0.70, "metallic": 0.0, "color": "#f2f2ec",
               "for": "the Golden Tee trackball only"},
    "a2shaft": {"roughness": 0.55, "metallic": 0.0,
                "for": "joystick shafts and dust washers"},
    "_no_emissive_on": ("#eceae2", "#f2f2ec", "#e8e8ea"),
}


# =========================================================================
'''

# ======================= round 7b: preview-sheet corrections ==============
LAYOUT = LAYOUT.replace('''_NBA_STICKS = [(-0.330, 0.520, "ball", 0.128, "#141418"),
               (0.075, 0.600, "bat", 0.150, "#d8323a")]
_NBA_BUTTONS = [
    (-0.435, 0.640, 0.082, "#2fa8e0"), (-0.160, 0.300, 0.082, "#e2661e"),
    (-0.075, 0.520, 0.082, "#eceae2"), (-0.180, 0.740, 0.082, "#d8262c"),
    (0.245, 0.310, 0.082, "#2fa8e0"), (0.330, 0.540, 0.082, "#e2661e"),
    (0.240, 0.770, 0.082, "#eceae2"), (0.430, 0.410, 0.082, "#d8262c"),
]''', '''_NBA_STICKS = [(-0.220, 0.520, "ball", 0.128, "#141418"),
               (0.150, 0.600, "bat", 0.150, "#d8323a")]
_NBA_BUTTONS = [
    (-0.320, 0.800, 0.082, "#2fa8e0"), (-0.060, 0.300, 0.082, "#e2661e"),
    (0.020, 0.510, 0.082, "#eceae2"), (-0.075, 0.725, 0.082, "#d8262c"),
    (0.300, 0.310, 0.082, "#2fa8e0"), (0.390, 0.520, 0.082, "#e2661e"),
    (0.295, 0.740, 0.082, "#eceae2"), (0.420, 0.300, 0.082, "#d8262c"),
]''')
assert "-0.220, 0.520" in LAYOUT

NBA_DECK = '''@_panel("nba-jam.deck")
def _nba_deck(cv):
    """ROUND 7.  The hardwood court, redrawn to survive 80 x 34 texels.

    Evidence: v4 7 px (288,248)-(370,330) at 14x -- art/r7/nba_deck_zoom.png.
    It is the clearest control deck in the whole set of photographs and it
    shows, unambiguously: warm terracotta boards running the LENGTH of the
    deck; white court lines (a sideline sweeping the full width, a centre
    circle, a key and a three-point arc); a red-and-white NBA JAM starburst
    logo lying on the boards at the LEFT END, clear of the controls; deep red
    T-molding round the edge; and eight large round buttons in ORANGE, WHITE,
    RED and CYAN SCATTERED across the court lines rather than ranked in rows.

    Scale check on the same crop: the T-molding measures 2.5 px and real
    T-molding is 0.75 in, so 0.30 in/px.  The deck then measures 24.6 in wide
    (right for a 2.30 ft carcase seen slightly foreshortened) and the buttons
    measure 7.5 px = 2.25 IN -- jumbo, not the 1.4 in round 5 assumed.

    Tile TOP = the deck's back edge at the screen; BOTTOM = the player's edge.
    """
    _boards(cv, 0.0, 0.0, 1.0, 1.0, 6, "#c47c46", "#9b5a2c", "#6b3a16", 707)
    _wear(cv, 0.0, 0.0, 1.0, 1.0, 15.0, 88, 3, vert=False)

    W = "#f4efdf"
    lw = 0.052                      # 1.8 texels; round 5 drew 0.030 at alpha 1
    cv.stroke([(0.038, 0.130), (0.962, 0.130), (0.962, 0.870), (0.038, 0.870)],
              W, lw, closed=True)
    cv.seg((0.500, 0.130), (0.500, 0.870), W, lw)
    cv.ring(0.500, 0.500, 0.290, 0.290, lw, W)
    for (bu, sgn) in ((0.038, 1.0), (0.962, -1.0)):
        cv.stroke([(bu, 0.300), (bu + sgn * 0.132, 0.300),
                   (bu + sgn * 0.132, 0.700), (bu, 0.700)], W, lw)
        cv.arc(bu, 0.500, 0.980, 0.980,
               -math.pi * 0.40 if sgn > 0 else math.pi * 0.60,
               math.pi * 0.40 if sgn > 0 else math.pi * 1.40, lw, W)

    # the wordmark lying on the boards at the left end
    _burst(cv, 0.098, 0.455, 0.420, 14, "#f6f1e2", 0.070, 0.20, 0.54, 0.85)
    _text_fit(cv, "NBA", 0.098, 0.335, 0.200, "#d0202c", 0.044, track=0.05,
              aspect=0.74, slant=0.10, outline="#f6ecd0", ow=0.030)
    _text_fit(cv, "JAM", 0.098, 0.575, 0.200, "#d0202c", 0.044, track=0.05,
              aspect=0.74, slant=0.10, outline="#f6ecd0", ow=0.030)

    for (u, v) in _NBA_STICK_UV:
        _stickpad(cv, u, v, 0.118, "#17130f")
    for (u, v) in _NBA_BTN_UV:
        _collar(cv, u, v, 0.082, "#301c10", k=1.28, a=0.45, edge="#22140a",
                ea=0.55)

    cv.vgrad(0.0, 0.938, 1.0, 1.0, "#7e1e26", "#400e14")        # T-molding
    cv.seg((0.0, 0.938), (1.0, 0.938), "#160c0c", 0.026, 0.9)
    cv.vgrad(0.0, 0.0, 1.0, 0.042, "#5e1620", "#320c10")
    _grain(cv, 9.0, 11)


'''

TM_DECK = '''@_panel("tmnt-turtles-in-time.deck")
def _tm_deck(cv):
    """ROUND 7.  The tan-and-brick New York street, rebuilt from the photograph.

    Evidence: v4 7 px (330,290)-(470,400) at 10x and (380,300)-(470,370) at
    16x -- art/r7/tm_deck_far.png, tm_deck_zoom.png.  Round 5 drew this deck as
    a DARK brick wall.  It is not: it is a bright warm TAN ground (a sunset
    street) with a brown-red brick block standing in it, a violet night sky
    over the far end, TURTLES wordmarks cascading diagonally across it in green
    and blue, a magenta splash, square character-portrait decals along the
    player's edge and a pale instruction label at the back.  Bright green
    T-molding all round.

    It is also the only deck in the room with a ROW OF SMALL VIOLET BUTTONS
    across its back edge (clearly visible in tm_deck_far.png), and the only one
    whose main buttons are jumbo domes.  Both are in DECKS.
    """
    cv.fill("#dcae76")
    cv.vgrad(0.0, 0.0, 1.0, 1.0, "#efc793", "#c1854a")          # sky -> street
    cv.hgrad(0.0, 0.0, 0.34, 1.0, "#3a2a5c", "#dcae76")         # night end
    cv.rect(0.0, 0.0, 0.140, 1.0, "#33254f")
    _stars(cv, [(0.0, 0.0), (0.220, 0.0), (0.220, 0.60), (0.0, 0.60)], 61, 22)

    # the block of brownstones -- the thing that makes this deck read as a city
    _bricks(cv, 0.120, 0.290, 0.520, 0.905, 5, "#a8593a", "#8d452c", "#40241a",
            38, 1.0, 12.0)
    _window_rows(cv, 0.146, 0.340, 0.496, 0.862, 4, 4, "#f0cf72", "#2b1c22",
                 71, 0.38)
    cv.rect(0.120, 0.272, 0.520, 0.310, "#3a221a")              # cornice
    _bricks(cv, 0.520, 0.410, 0.762, 0.905, 4, "#8f4a30", "#743c26", "#361e16",
            39, 1.0, 10.0)
    _window_rows(cv, 0.542, 0.450, 0.742, 0.866, 3, 3, "#e6c26a", "#26191e",
                 72, 0.30)
    cv.rect(0.520, 0.394, 0.762, 0.424, "#321d16")
    cv.rect(0.762, 0.530, 0.906, 0.905, "#7a4830", 0.85)        # far block
    _window_rows(cv, 0.780, 0.566, 0.892, 0.870, 2, 3, "#d8b262", "#241820",
                 73, 0.28)

    cv.rect(0.0, 0.905, 1.0, 0.958, "#38343a")                  # the street
    cv.seg((0.140, 0.934), (0.360, 0.934), "#8a867c", 0.026, 0.55)
    cv.seg((0.580, 0.934), (0.800, 0.934), "#8a867c", 0.026, 0.55)

    # the wordmarks, cascading down-right the way the photograph runs them
    cv.ell(0.478, 0.256, 0.150, 0.116, "#9c2486", 0.9)          # splash
    cv.ell(0.478, 0.256, 0.092, 0.070, "#d84ab4", 0.9)
    _tm_logo(cv, 0.606, 0.430, 0.280)
    _text_fit(cv, "TURTLES", 0.862, 0.176, 0.175, "#3fa8ee", 0.032, track=0.08,
              aspect=0.74, slant=0.07, outline="#10203c", ow=0.026)

    # the pale instruction label the photo shows at the back edge
    cv.rect(0.024, 0.210, 0.186, 0.352, "#e6ecf2")
    cv.rect(0.036, 0.226, 0.174, 0.336, "#adc0d0")
    for vv in (0.252, 0.284, 0.316):
        cv.seg((0.048, vv), (0.162, vv), "#2c3c4c", 0.024, 0.8)

    # the square character portraits along the player's edge
    for (i, u0) in enumerate((0.022, 0.374, 0.726)):
        bd = ("#d8322c", "#3a6ee0", "#e08a1c")[i]
        cv.rect(u0, 0.800, u0 + 0.118, 0.968, "#efe8d6")
        cv.rect(u0 + 0.012, 0.816, u0 + 0.106, 0.952, "#23331e")
        cv.ell(u0 + 0.059, 0.896, 0.108, 0.108, "#4faa3c")
        cv.rect(u0 + 0.020, 0.862, u0 + 0.098, 0.890, bd)

    for (u, v) in _TM_STICK_UV:
        _stickpad(cv, u, v, 0.126, "#141110")
    for (u, v) in _TM_BTN_UV:
        _collar(cv, u, v, 0.098, "#2c1d14", k=1.24, a=0.44, edge="#1d120c",
                ea=0.55)
    for (u, v) in _TM_ADM_UV:
        _collar(cv, u, v, 0.042, "#241c30", k=1.45, a=0.55, edge="#141020",
                ea=0.7)

    cv.rect(0.0, 0.0, 1.0, 0.040, "#4fc23a")                    # green molding
    cv.vgrad(0.0, 0.958, 1.0, 1.0, "#57cd3e", "#1f6a22")
    _grain(cv, 8.0, 39)


'''

PM_DECK = '''@_panel("pac-man.deck")
def _pm_deck(cv):
    """ROUND 7.  A BLACK deck, and that is the finding, not a shortcut.

    Evidence: v3 1 px (590,620)-(700,700) at 10x, v4 3 px (70,150)-(130,220) at
    14x and v4 7 px (0,175)-(45,235) at 18x -- art/r7/pac_deck_v31.png,
    pac_v43.png, pac_deck_v47.png.  v4 3 looks almost straight DOWN onto this
    deck, and there is no printed graphic on it in any of the three: a plain
    black overlay, a maroon T-molding lip along the front, a row of small round
    white / red / blue buttons across it, one red ball-top stick, and ONE pale
    rectangular instruction label at the right.  The roster agrees ("Black deck
    with a maroon lip along its front edge").

    So this deck is NOT given invented artwork, and I am saying so rather than
    quietly filling it: OF THE FOUR, THIS IS THE ONE THAT STILL READS AS A
    TINTED SLAB, because the object does.  Round 5's big yellow "PAC-MAN"
    legend across it was invented, is in no frame, and is removed -- which is
    also the honest fix for the "AC-MAN" clipping the brief named: the string
    was 0.488 wide in u centred at u 0.170, so the P fell off the left edge.
    Type on a deck now goes through _text_fit, which cannot run off the panel.

    What it IS given is everything the photographs DO show, at a size that
    survives 80 x 34 texels: a lengthwise brushed sheen (the overlay is glossy
    and catches the cove light in v3 1), the bright trim strip along the back
    edge, the pale instruction label, the maroon lip, and seats light enough to
    read on black.  Authored LIFTED, because a2kit multiplies this tile by
    ART_DK (#4c4c4c) -- DECK_MAT_REQUEST keeps it there.
    """
    cv.vgrad(0.0, 0.0, 1.0, 1.0, "#7e7e88", "#4c4c56")
    _wear(cv, 0.0, 0.0, 1.0, 1.0, 9.0, 24, 3, vert=True)
    _sheen(cv, 0.0, 0.070, 1.0, 0.880, 16.0, 241, 4)
    cv.vgrad(0.0, 0.0, 1.0, 0.056, "#c6c6d0", "#6a6a74")        # back trim
    cv.seg((0.0, 0.064), (1.0, 0.064), "#26262e", 0.022, 0.85)

    # the pale instruction label -- the one printed thing on this deck
    cv.rect(0.706, 0.140, 0.928, 0.360, "#ced3db")
    cv.rect(0.718, 0.156, 0.916, 0.344, "#a4acb8")
    for vv in (0.192, 0.238, 0.284, 0.330):
        cv.seg((0.732, vv), (0.902, vv), "#33383f", 0.024, 0.85)

    for (u, v) in _PM_STICK_UV:
        _stickpad(cv, u, v, 0.104, "#121216", "#7e7e8a")
    for (u, v) in _PM_BTN_UV:
        _collar(cv, u, v, 0.055, "#b6b6c2", k=1.34, a=0.34, edge="#0f0f13",
                ea=0.7)

    cv.vgrad(0.0, 0.900, 1.0, 1.0, "#b03a46", "#6c1c26")        # maroon lip
    cv.seg((0.0, 0.900), (1.0, 0.900), "#141014", 0.024, 0.9)
    _grain(cv, 9.0, 25)


'''

GT_DECK = '''@_panel("golden-tee-3d-golf.deck")
def _gt_deck(cv):
    """ROUND 7.  A full-bleed grass fairway -- and the yellow legend strip is
    NOT on it.

    Evidence: v4 7 px (112,180)-(175,205) at 20x and v4 6 px (360,190)-(440,230)
    at 16x -- art/r7/gt_deck_zoom.png, gt_deck_v46.png.  Both show the lit
    three-panel yellow strip standing on the DARK VERTICAL FACE ABOVE the deck,
    separated from the green by a hard dark step, and the deck itself as bright
    grass green from edge to edge with pale mown highlights, a pale bunker each
    side and the white trackball reading as the brightest thing on it.

    The roster describes the deck as "two printed bands", the upper one the
    yellow legend.  I am departing from that one clause, and saying so: the
    bezel panel (golden-tee-3d-golf.bezel) ALREADY draws that strip at its foot
    where the geometry puts it, and round 5 drew it a SECOND time across the
    back 15% of the deck, so the render carried two yellow strips where the
    photograph has one -- and it spent 5 of the deck's 34 rows on lettering at
    3.5 texels cap height, which is unreadable by construction.  The deck keeps
    only the dark green step the photo shows at its back edge.
    """
    cv.vgrad(0.0, 0.0, 1.0, 1.0, "#74ac4c", "#4e8232")
    for j in range(5):                                          # mown stripes
        v0 = 0.070 + j * 0.186
        if j % 2 == 0:
            cv.rect(0.0, v0, 1.0, v0 + 0.093, "#e8f2c4", 0.14)
    cv.poly([(0.0, 0.330), (0.300, 0.245), (0.640, 0.335), (1.0, 0.260),
             (1.0, 0.070), (0.0, 0.120)], "#3d6c2c")            # rough
    cv.poly([(0.0, 0.955), (1.0, 0.920), (1.0, 1.0), (0.0, 1.0)], "#2f5722")
    cv.ell(0.735, 0.545, 0.290, 0.250, "#94c669")               # putting green
    cv.ell(0.735, 0.545, 0.230, 0.196, "#a8d878")
    cv.ell(0.180, 0.640, 0.235, 0.205, "#ddd0a0")               # bunkers
    cv.ell(0.180, 0.640, 0.185, 0.158, "#f0e6c2")
    cv.ell(0.930, 0.320, 0.165, 0.140, "#e2d6a8")
    cv.poly([(0.290, 1.00), (0.455, 0.320), (0.545, 0.320), (0.415, 1.00)],
            "#cdd4ae", 0.40)                                    # cart path
    cv.seg((0.735, 0.545), (0.735, 0.330), "#f4f4ee", 0.036)    # flagstick
    cv.poly([(0.735, 0.330), (0.812, 0.358), (0.735, 0.388)], "#e03a2c")
    _wear(cv, 0.0, 0.120, 1.0, 1.0, 11.0, 56, 3, vert=False)

    cv.vgrad(0.0, 0.0, 1.0, 0.066, "#15200c", "#33481e")        # the dark step
    cv.seg((0.0, 0.068), (1.0, 0.068), "#101a08", 0.022, 0.85)

    # the trackball's printed bezel ring -- a RING, not a filled disc: the ball
    # is 3 in of white geometry and the photo's brightest mark, so a black
    # plate under it would fight it.
    cv.ring(_du(_GT_TRACK_UV[0]), _GT_TRACK_UV[1], _ft(0.150), _ft(0.150),
            _ft(0.036), "#1d2716", 0.8)
    cv.ring(_du(_GT_TRACK_UV[0]), _GT_TRACK_UV[1], _ft(0.176), _ft(0.176),
            _ft(0.026), "#c9d8ae", 0.35)
    for (u, v) in _GT_BTN_UV:
        _collar(cv, u, v, 0.062, "#1c2814", k=1.34, a=0.46, edge="#101a08",
                ea=0.6)
    _grain(cv, 8.0, 57)


'''

# round 7c: Pac-Man's field was reading blue-purple and blotchy.  The photo's
# overlay is a NEUTRAL black; the blue in the frame is the room's RGB cove
# light, which the renderer supplies, so authoring it into the albedo doubles
# it.  Sheen down too -- four broad bands read as dirt at 34 rows.
PM_DECK = PM_DECK.replace(
    'cv.vgrad(0.0, 0.0, 1.0, 1.0, "#7e7e88", "#4c4c56")',
    'cv.vgrad(0.0, 0.0, 1.0, 1.0, "#7c7c7e", "#4e4e50")')
PM_DECK = PM_DECK.replace('_wear(cv, 0.0, 0.0, 1.0, 1.0, 9.0, 24, 3, vert=True)',
                          '_wear(cv, 0.0, 0.0, 1.0, 1.0, 6.0, 24, 2, vert=True)')
PM_DECK = PM_DECK.replace('_sheen(cv, 0.0, 0.070, 1.0, 0.880, 16.0, 241, 4)',
                          '_sheen(cv, 0.0, 0.070, 1.0, 0.880, 13.0, 241, 3)')
PM_DECK = PM_DECK.replace('"#c6c6d0", "#6a6a74")', '"#c4c4c6", "#6a6a6c")')
PM_DECK = PM_DECK.replace('"#ced3db")', '"#d0d2d6")')
PM_DECK = PM_DECK.replace('"#a4acb8")', '"#a6a8ae")')
PM_DECK = PM_DECK.replace('_collar(cv, u, v, 0.055, "#b6b6c2", k=1.34, a=0.34',
                          '_collar(cv, u, v, 0.055, "#b0b0b4", k=1.32, a=0.30')
assert "#7c7c7e" in PM_DECK and "6.0, 24, 2" in PM_DECK

# round 7d.  The Pac-Man field came back BLUE-VIOLET in the shipped-size
# preview even though it is authored grey.  Cause, worth recording: the paint
# quantises to multiples of 8 and atlas4 then re-quantises to multiples of
# QUANT 20, so a field authored at (124,124,126) -- two levels apart, invisible
# in the buffer -- lands on (120,120,140) and the deck goes lilac.  ANY
# near-neutral surface in this atlas must be authored EXACTLY neutral
# (r == g == b) or the two-stage quantiser will split its channels.
PM_DECK = (PM_DECK
           .replace('"#7c7c7e", "#4e4e50")', '"#7c7c7c", "#4c4c4c")')
           .replace('"#c4c4c6", "#6a6a6c")', '"#c4c4c4", "#6a6a6a")')
           .replace('"#26262e", 0.022', '"#242424", 0.022')
           .replace('"#d0d2d6")', '"#d0d0d0")')
           .replace('"#a6a8ae")', '"#a4a4a4")')
           .replace('"#33383f", 0.024', '"#343434", 0.024')
           .replace('"#b0b0b4", k=1.32', '"#b4b4b4", k=1.32')
           .replace('"#0f0f13",\n                ea=0.7)', '"#141414",\n                ea=0.7)')
           .replace('"#121216", "#7e7e8a")', '"#141414", "#848484")'))
assert "#7c7c7c" in PM_DECK and "#141414" in PM_DECK
PM_DECK = PM_DECK.replace(
    '    Round 5\'s big yellow "PAC-MAN"',
    '    NOTE for anyone editing this panel: it is authored EXACTLY neutral\n'
    '    (r == g == b on every grey).  The paint quantises to multiples of 8\n'
    '    and atlas4 re-quantises to multiples of QUANT 20, so a grey two\n'
    '    levels off neutral lands on a 20-level channel split and the whole\n'
    '    deck goes lilac -- which is exactly what the first round-7 pass did.\n'
    '    Round 5\'s big yellow "PAC-MAN"')
