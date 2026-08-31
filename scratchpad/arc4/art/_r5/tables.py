

# ================================================================== the tables
# ASPECT is width/height of the REAL quad ar2.py maps each panel onto, computed
# from that file's own numbers for these four machines rather than assumed:
#
#   marquee : (bw - 0.12) / mqh
#   front   : (bw - 0.16) / ((dy - 0.62) - (plinth + 0.16))
#   side    : (fd - back) / (top + plinth)  = 2.95 / (top + plinth)
#   deck    : (bw - 0.12) / ((fd - 0.06) - (ft + 0.04))  = (bw - 0.12) / 0.92
#
#   slug                  bw    top   dy    mqh  plinth | mq    front side deck
#   marvel-super-heroes   2.10  5.86  2.44  0.55  0.10  | 3.60  1.24  0.50 2.15
#   marvel-vs-capcom      2.42  6.34  2.60  0.76  0.00  | 3.03  1.24  0.47 2.50
#   mortal-kombat         2.16  5.98  2.48  0.58  0.14  | 3.52  1.28  0.48 2.22
#   nfl-blitz             2.18  6.02  2.44  0.56  0.00  | 3.68  1.22  0.49 2.24
#
# Round 4 used one aspect per panel CLASS for all sixteen machines (3.40 / 1.00
# / 0.43 / 2.60), which stretched every front by ~24% and squeezed every side.
ASPECT = {
    "marvel-super-heroes.marquee": 3.600,
    "marvel-super-heroes.front":   1.244,
    "marvel-super-heroes.side":    0.495,
    "marvel-super-heroes.deck":    2.152,
    # bezel = (bw - 0.10) / ((mq_lo - 0.10) - (dy + 0.30)), plinth folded in
    "marvel-super-heroes.bezel":   0.873,
    "marvel-vs-capcom.marquee":    3.026,
    "marvel-vs-capcom.front":      1.242,
    "marvel-vs-capcom.side":       0.465,
    "marvel-vs-capcom.deck":       2.500,
    "mortal-kombat.marquee":       3.517,
    "mortal-kombat.front":         1.282,
    "mortal-kombat.side":          0.482,
    "mortal-kombat.deck":          2.217,
    "nfl-blitz.marquee":           3.679,
    "nfl-blitz.front":             1.217,
    "nfl-blitz.side":              0.490,
    "nfl-blitz.deck":              2.239,
}

# Which a2kit material each panel expects.  These are true printed albedos.
MATERIAL_HINT = {
    "marvel-super-heroes.marquee": "MQ (emissive, DIM -- 'reads dim, not "
                                   "brightly lit'; keep a2kit's #2b2118/1.0)",
    "marvel-super-heroes.front": "ART",
    "marvel-super-heroes.side": "ART",
    "marvel-super-heroes.deck": "ART_D  -- a dark navy deck, but ART_DK "
                                "(#4c4c4c) kills the gold chevrons",
    "marvel-super-heroes.bezel": "ART.  ADD 'marvel-super-heroes.bezel' to "
                                 "atlas4.EXTRA_KEYS -- this is the only one "
                                 "of my four whose monitor surround carries "
                                 "printed art in the photographs (blue-teal "
                                 "mottle, v3 4 / e_run3x).  The other three "
                                 "keep a2kit's plain #15151a BEZEL.",
    "marvel-vs-capcom.marquee": "MQ (emissive; the battle illustration is the "
                                "brightest of my four)",
    "marvel-vs-capcom.front": "ART",
    "marvel-vs-capcom.side": "ART",
    "marvel-vs-capcom.deck": "ART_DM  -- THE PALE SILVER DECK.  ART_DK would "
                             "make the room's one light control panel grey.",
    "mortal-kombat.marquee": "MQ (emissive; navy ground, bone roundel)",
    "mortal-kombat.front": "ART",
    "mortal-kombat.side": "ART",
    "mortal-kombat.deck": "ART_D  -- NOT ART_DK: the blue is the identity",
    "nfl-blitz.marquee": "MQ (emissive but LOW -- the roster says 'Not lit'; "
                         "a2kit already has it at a dark tint)",
    "nfl-blitz.front": "ART",
    "nfl-blitz.side": "ART",
    "nfl-blitz.deck": "ART_D  -- the nebula is mid-value already",
}

# ------------------------------------------------------------------- DECKS
# The joystick / button GEOMETRY spec, for ar2.py's upright() to consume.
# ar2 currently hard-codes, for every machine in the room: two sticks at
# jx = (-0.28 + 0.56k) * (bw / 2.20) with box tops in BUTTONS[k] (one red, one
# blue), and three FLAT SQUARE buttons per player from rect_up().  That is the
# defect all three critics named.  Replace that block with a read of this
# table; the machines whose art module has no DECKS entry can keep the old
# path until their module ships one.
#
# FRAME.  Exactly the frame the `.deck` texture is authored in, so a printed
# socket and the button standing in it cannot drift:
#
#     u in [-0.5, +0.5]  across the deck art quad's WIDTH  (bw - 0.12 ft),
#                        u = 0 at the cabinet centreline
#     v in [0, 1]        from the deck's BACK edge (z = ft + 0.04, nearest the
#                        screen) to its FRONT edge (z = fd - 0.06)
#
#     x = u * (bw - 0.12)
#     z = (ft + 0.04) + v * ((fd - 0.06) - (ft + 0.04))      # 0.92 ft deep
#     y = dy + 0.014                                          # the art plane
#
# "width_ft" and "depth_ft" are those two spans, restated so the table can be
# checked against ar2 without re-deriving them.  ALL OTHER LENGTHS ARE FEET.
#
# SHAPES -- and the payload, which was MEASURED, not guessed.  A round button
# can cost anything from 165 to 2350 bytes depending on how it is built, and
# the room has 0.6 KB of headroom, so use the recipes below.  Bytes per button
# in a saved GLB, materials held constant, my 52 buttons:
#
#     flat square quad (what ar2's rect_up does today)      165 B
#     DOMED 8-GON CAP, smooth=True   <- BUILD THIS          310 B
#     domed 10-gon cap, smooth                              382 B
#     flat 8-gon cap, smooth=False                          669 B
#     cylinder(r, h, 8)                                     813 B
#     prism(octagon, h)                                    2350 B
#
#   buttons  ``art_g1.button_cap(r, h)`` returns (verts, tris, smooth) for a
#            9-vertex domed octagon cap sitting at the deck plane, apex at
#            y + h.  Wrap it: ``m.add(Part(v, t, smooth=sm), mat, at=(x, y, z))``.
#            Smooth welding is the whole trick -- the same shape unwelded is
#            2.2x the bytes, and the dome plus shared normals is what makes it
#            read CONVEX rather than as ar2's flat square.  There is no side
#            wall: these buttons stand 0.020-0.026 ft (0.25-0.31 in) proud and
#            the wall is invisible from any standing camera, while the printed
#            socket ring in the deck art already gives the seat.
#            "col" is both the material colour and its emissive tint, as
#            ar2.BUTTONS already does.
#   sticks   shaft = cylinder(shaft_r, shaft_h, seg=6) on the art plane.
#            top "ball" = ``art_g1.ball_top(top_r)`` -> (verts, tris, smooth),
#                         seated at y + shaft_h - top_r*0.4
#            top "bat"  = cylinder(top_r, top_h, seg=8) at y + shaft_h, i.e. a
#                         stubby vertical grip, not a sphere
#            "base_r" is the painted socket / dust-washer radius; ar2 does not
#            need to build it, it is already printed into the deck art.
#            MEASURED: this stick is 1700 B against round 4's two boxes at
#            2007 B, so the sticks pay for a third of the extra buttons.
#
# NET for my four machines against round 4's controls: buttons +11.8 KB (52
# domed caps against 24 flat squares), sticks -2.4 KB, coin doors -4 boxes
# (Marvel Super Heroes has none and only Blitz has two).  About +9 KB.
#
# WHY THE FOUR DIFFER.  MvC is the roster's only deck whose controls actually
# resolve ("TWO ball-top joysticks and a six-button-per-player array in green,
# red, white and blue"), MK's is "a dense multi-button array (about six per
# player) in red, blue, white and green" with black ball tops, Blitz's is
# "rows of round buttons in blue, green, red and yellow" on the nebula, and
# MSH's does not resolve at any magnification -- so MSH takes the real
# machine's standard Capcom CPS-2 layout (6 per player, two arced rows) with
# BAT tops, which is declared in the report as the one layout I chose rather
# than read.  Button radius runs 0.040 (MK, the densest) to 0.062 (Blitz, the
# sports cabinet with three big buttons a side); counts run 3+1 to 6.
def button_cap(r, h, seg=8, dome=0.45):
    """One arcade button as (verts, tris, smooth), ready for roomkit's Part.

    A domed regular n-gon fan: seg + 1 vertices, seg triangles, welded so the
    normals interpolate and it reads convex.  Origin is the deck art plane, so
    ``m.add(Part(*button_cap(r, h)), mat, at=(x, y_deck, z))`` seats it.
    Measured at 310 bytes in a saved GLB -- see the note above the table.
    """
    v = [(0.0, h, 0.0)]
    rim = h * (1.0 - dome)
    for i in range(seg):
        a = 2.0 * math.pi * i / seg
        v.append((math.cos(a) * r, rim, math.sin(a) * r))
    t = [(0, i + 1, 1 + (i + 1) % seg) for i in range(seg)]
    return v, t, True


def ball_top(r, seg=8, rings=3):
    """A ball-top joystick knob as (verts, tris, smooth); origin at its base,
    so seat it at y + shaft_h - r * 0.4.  Measured cheaper than the two boxes
    round 4 used for a stick."""
    v = []
    for i in range(rings + 1):
        ph = math.pi * i / rings
        for j in range(seg):
            th = 2.0 * math.pi * j / seg
            v.append((r * math.sin(ph) * math.cos(th), r * (1.0 - math.cos(ph)),
                      r * math.sin(ph) * math.sin(th)))
    t = []
    for i in range(rings):
        for j in range(seg):
            a = i * seg + j
            b = i * seg + (j + 1) % seg
            t.append((a, b, b + seg))
            t.append((a, b + seg, a + seg))
    return v, t, True


def _row(v, us, cols, r, h):
    return [{"u": u, "v": v, "r": r, "h": h, "shape": "round", "col": c}
            for (u, c) in zip(us, cols)]


def _starts(v, us, r=0.026, h=0.015, col="#e6e9ef"):
    return [{"u": u, "v": v, "r": r, "h": h, "shape": "round", "col": col,
             "role": "start"} for u in us]


_AMB, _ORA, _RED = "#f0c024", "#e8801c", "#d02b26"
_GRN, _BLU, _WHT = "#2faa4e", "#2f63de", "#eef0f4"
_YEL = "#f0c81e"

DECKS = {
    "marvel-super-heroes": {
        "width_ft": 1.98, "depth_ft": 0.92,
        "sticks": [
            {"u": -0.400, "v": 0.575, "base_r": 0.075, "shaft_r": 0.026,
             "shaft_h": 0.155, "top": "bat", "top_r": 0.048, "top_h": 0.115,
             "shaft_col": "#b4b9c0", "top_col": "#16171b"},
            {"u": 0.030, "v": 0.575, "base_r": 0.075, "shaft_r": 0.026,
             "shaft_h": 0.155, "top": "bat", "top_r": 0.048, "top_h": 0.115,
             "shaft_col": "#b4b9c0", "top_col": "#16171b"},
        ],
        "buttons": (
            _row(0.395, (-0.262, -0.185, -0.108), (_AMB, _ORA, _RED),
                 0.046, 0.022) +
            _row(0.640, (-0.248, -0.171, -0.094), (_AMB, _ORA, _RED),
                 0.046, 0.022) +
            _row(0.395, (0.168, 0.245, 0.322), (_AMB, _ORA, _RED),
                 0.046, 0.022) +
            _row(0.640, (0.182, 0.259, 0.336), (_AMB, _ORA, _RED),
                 0.046, 0.022) +
            _starts(0.130, (-0.320, 0.110))),
    },
    "marvel-vs-capcom": {
        "width_ft": 2.30, "depth_ft": 0.92,
        "sticks": [
            {"u": -0.385, "v": 0.560, "base_r": 0.078, "shaft_r": 0.027,
             "shaft_h": 0.160, "top": "ball", "top_r": 0.055, "top_h": 0.110,
             "shaft_col": "#c2c6cc", "top_col": "#f2f3f6"},
            {"u": 0.045, "v": 0.560, "base_r": 0.078, "shaft_r": 0.027,
             "shaft_h": 0.160, "top": "ball", "top_r": 0.055, "top_h": 0.110,
             "shaft_col": "#c2c6cc", "top_col": "#f2f3f6"},
        ],
        "buttons": (
            _row(0.400, (-0.245, -0.172, -0.099), (_GRN, _RED, _WHT),
                 0.048, 0.023) +
            _row(0.620, (-0.245, -0.172, -0.099), (_BLU, _GRN, _RED),
                 0.048, 0.023) +
            _row(0.400, (0.190, 0.263, 0.336), (_GRN, _RED, _WHT),
                 0.048, 0.023) +
            _row(0.620, (0.190, 0.263, 0.336), (_BLU, _GRN, _RED),
                 0.048, 0.023) +
            _starts(0.120, (-0.310, 0.120))),
    },
    "mortal-kombat": {
        "width_ft": 2.04, "depth_ft": 0.92,
        "sticks": [
            {"u": -0.405, "v": 0.590, "base_r": 0.072, "shaft_r": 0.025,
             "shaft_h": 0.150, "top": "ball", "top_r": 0.050, "top_h": 0.100,
             "shaft_col": "#9aa0a8", "top_col": "#101116"},
            {"u": 0.020, "v": 0.590, "base_r": 0.072, "shaft_r": 0.025,
             "shaft_h": 0.150, "top": "ball", "top_r": 0.050, "top_h": 0.100,
             "shaft_col": "#9aa0a8", "top_col": "#101116"},
        ],
        "buttons": (
            _row(0.380, (-0.258, -0.190, -0.122), (_RED, _BLU, _WHT),
                 0.040, 0.020) +
            _row(0.610, (-0.224, -0.156, -0.088), (_GRN, _RED, _BLU),
                 0.040, 0.020) +
            _row(0.380, (0.162, 0.230, 0.298), (_RED, _BLU, _WHT),
                 0.040, 0.020) +
            _row(0.610, (0.196, 0.264, 0.332), (_GRN, _RED, _BLU),
                 0.040, 0.020) +
            _starts(0.180, (-0.330, 0.100), r=0.024)),
    },
    "nfl-blitz": {
        "width_ft": 2.06, "depth_ft": 0.92,
        "sticks": [
            {"u": -0.395, "v": 0.575, "base_r": 0.082, "shaft_r": 0.028,
             "shaft_h": 0.165, "top": "bat", "top_r": 0.042, "top_h": 0.135,
             "shaft_col": "#aeb3ba", "top_col": "#121218"},
            {"u": 0.055, "v": 0.575, "base_r": 0.082, "shaft_r": 0.028,
             "shaft_h": 0.165, "top": "bat", "top_r": 0.042, "top_h": 0.135,
             "shaft_col": "#aeb3ba", "top_col": "#121218"},
        ],
        "buttons": (
            _row(0.450, (-0.265, -0.160, -0.055), (_BLU, _GRN, _RED),
                 0.062, 0.026) +
            _row(0.700, (-0.160,), (_YEL,), 0.062, 0.026) +
            _row(0.450, (0.175, 0.280, 0.385), (_BLU, _GRN, _RED),
                 0.062, 0.026) +
            _row(0.700, (0.280,), (_YEL,), 0.062, 0.026) +
            _starts(0.185, (-0.320, 0.130))),
    },
}

# -------------------------------------------------------------------- COIN
# The coin-door GEOMETRY, replacing ar2's one hard-coded
#     bx(CPANEL, -0.34, 0.34, plinth+0.30, plinth+0.92, ...)
#     bx(CHR,    -0.26, 0.26, plinth+0.52, plinth+0.60, ...)
# which puts the SAME grey rectangle at the SAME place on all sixteen cabinets.
#
# FRAME.  The `.front` panel's own frame, so the printed plate and the box
# register exactly:
#     u in [-0.5, +0.5] across the front art quad's WIDTH  (bw - 0.16 ft)
#     v in [0, 1]       from the panel's TOP (y = dy - 0.62) DOWNWARD to its
#                       BOTTOM (y = plinth + 0.16)
#
#     x  = u * (bw - 0.16)
#     y  = (dy - 0.62) - v * ((dy - 0.62) - (plinth + 0.16))
#     z0 = zf (= fb + 0.008, the front art plane);  z1 = z0 + "depth"
#
# A machine may have ZERO doors (Marvel Super Heroes -- its lower front is
# unbroken printed art in v3 4, v4 8 and v4 9, and the plate is PAINTED flush
# instead), one, or two (NFL Blitz).  Every entry is also drawn into the front
# artwork at the same rectangle, so if the integrator skips the geometry
# entirely the panels still read correctly -- the geometry only adds relief.
COIN = {
    "marvel-super-heroes": [],
    "marvel-vs-capcom": [
        {"u0": -0.175, "u1": 0.175, "v0": 0.190, "v1": 0.450,
         "depth": 0.030, "colour": "#101218", "trim": "#3c414c",
         "note": "small, black-on-black, dead centre at MID height, with a "
                 "painted coin-return cup below it"},
    ],
    "mortal-kombat": [
        {"u0": -0.290, "u1": 0.290, "v0": 0.735, "v1": 0.905,
         "depth": 0.045, "colour": "#6d5230", "trim": "#b99457",
         "note": "WIDE, LOW, BRONZE twin door -- 58% of the panel width, "
                 "sitting on the pale logo band, two slots and two cups"},
    ],
    "nfl-blitz": [
        {"u0": -0.425, "u1": -0.015, "v0": 0.060, "v1": 0.430,
         "depth": 0.022, "colour": "#15161f", "trim": "#3e4054",
         "note": "LEFT of the twin recessed doors that fill this machine's "
                 "upper front half; white return button painted at centre"},
        {"u0": 0.045, "u1": 0.455, "v0": 0.060, "v1": 0.430,
         "depth": 0.022, "colour": "#15161f", "trim": "#3e4054",
         "note": "RIGHT door, mirror of the left"},
    ],
}

# ------------------------------------------------------------------ CARCASE
# Not this module's to set (a2kit.CARCASE owns it) but recorded here because
# round 5 changed what the panels expect of the trim.  Only one is a change:
CARCASE_HINT = {
    "marvel-super-heroes": "#8a7038  (unchanged -- the gold T-molding is "
                           "drawn into .side and .front as well)",
    "marvel-vs-capcom": "#17181c  (unchanged)",
    "mortal-kombat": "#5a1d22  (unchanged)",
    "nfl-blitz": "#2b2b3c  suggested, up from #22222a: v4 6 and v4 7 both "
                 "show this machine's front edge glowing blue-violet, and "
                 "the roster warns that may be the wall RGB, so this is a "
                 "small cool lift and NOT purple trim.  Optional.",
}

_FN = {
    "marvel-super-heroes.marquee": _msh_marquee,
    "marvel-super-heroes.side": _msh_side,
    "marvel-super-heroes.front": _msh_front,
    "marvel-super-heroes.deck": _msh_deck,
    "marvel-super-heroes.bezel": _msh_bezel,
    "marvel-vs-capcom.marquee": _mvc_marquee,
    "marvel-vs-capcom.side": _mvc_side,
    "marvel-vs-capcom.front": _mvc_front,
    "marvel-vs-capcom.deck": _mvc_deck,
    "mortal-kombat.marquee": _mk_marquee,
    "mortal-kombat.side": _mk_side,
    "mortal-kombat.front": _mk_front,
    "mortal-kombat.deck": _mk_deck,
    "nfl-blitz.marquee": _blitz_marquee,
    "nfl-blitz.side": _blitz_side,
    "nfl-blitz.front": _blitz_front,
    "nfl-blitz.deck": _blitz_deck,
}


# ---------------------------------------------------------------- PANEL_PX
# AN OFFER TO THE INTEGRATOR, AND THIS ROUND'S PAYLOAD SAVING.
#
# atlas4 packs SQUARE tiles, so a 3.6:1 marquee is authored squeezed 3.6x and
# unsqueezed by the quad.  That spends 120 ROWS on a band that needs about 50,
# and leaves only 120 columns of native detail for the widest, most-read
# surface on the machine -- which is a large part of why round 4's marquees
# still look soft in shots/r4_mq_east.png.
#
# `Cv` now paints non-square, and `PANELS[key].rect(px, ox, oy, w, h)` renders
# a panel at any w x h.  PANEL_PX is the (w, h) I recommend: for each panel
# class, an ISOTROPIC tile -- w = S*sqrt(A), h = S/sqrt(A) -- at an S chosen so
# every rect is CHEAPER than the square it replaces while carrying MORE
# horizontal detail.  Measured on my four machines by
# scratchpad/arc4/art/bytes_g1_r5.py; the number is in the report.
#
# If the integrator does not want to touch atlas4's packer, ignore this: the
# square `paint(px, ox, oy, tile)` contract is unchanged and every panel here
# still renders correctly through it.
#
# Measured on my four machines, whole-sheet PNG, SS 2, QUANT 16:
#     square, as atlas4 packs today (120/96/64/48)          74.9 KB
#     isotropic rect at S 100/92/62/46                      61.6 KB
#     isotropic rect at S  88/92/50/44   <- SHIPPED         54.6 KB
#     isotropic rect at S  76/74/50/40                      43.7 KB  (soft)
# The shipped row keeps the FRONT at the same pixel count as the 96x96 square
# (104x81) because the fronts are the typographic panels, spends the saving on
# the marquee -- which still gets 169 columns against the square's 120 -- and
# takes the flanks down hardest, because every one of my four machines stands
# shoulder to shoulder in its run (east gaps 0.00-0.16 ft) and its flanks are
# almost never seen.
_PANEL_S = {"marquee": 88, "front": 92, "side": 50, "deck": 44, "bezel": 42}


def _iso(A, s):
    r = A ** 0.5
    return (max(8, int(s * r + 0.5)), max(8, int(s / r + 0.5)))


PANEL_PX = dict((k, _iso(A, _PANEL_S[k.split(".")[-1]]))
                for (k, A) in ASPECT.items())


def _make(key):
    fn = _FN[key]
    A = ASPECT[key]

    def paint(px, ox, oy, tile):
        """The unchanged square-tile contract atlas4 calls today."""
        cv = Cv(tile, A)
        fn(cv)
        cv.blit(px, ox, oy)

    def paint_rect(px, ox, oy, w, h):
        """The same drawing at any w x h -- see PANEL_PX."""
        cv = Cv(w, A, hpx=h)
        fn(cv)
        cv.blit(px, ox, oy)

    paint.__name__ = "paint_" + key.replace("-", "_").replace(".", "_")
    paint.aspect = A
    paint.rect = paint_rect
    paint.px = PANEL_PX[key]
    return paint


PANELS = dict((k, _make(k)) for k in _FN)
