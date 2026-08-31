# -*- coding: utf-8 -*-
"""Round-7 replacement text for the four SOUTH-RUN control decks in art_g2.py.

Not imported by the app; `_r7_splice.py` pastes these strings into art_g2.py,
which is the file the integrator reads.  Kept as a separate fragment so the
edit is reproducible.
"""

HELPERS = r'''
# =========================================================================
#  ROUND 7 -- CONTROL-DECK ARTWORK.  Shared drawing helpers.
# =========================================================================
# WHY THESE EXIST, AND WHAT THEY ARE SIZED TO.
#
# atlas4 packs a deck ISOTROPICALLY at SIZE["deck"] = 52, so a deck of aspect
# A lands at 52*sqrt(A) x 52/sqrt(A) texels:
#
#   legends-ultimate A 3.08 -> 91 x 30    street-fighter-2 CE A 2.50 -> 82 x 33
#   time-crisis      A 2.61 -> 84 x 32    terminator-2        A 2.35 -> 80 x 34
#
# Every one of those is ~32-37 texels per FOOT in BOTH directions.  A real
# 1.1 in arcade button is 0.092 ft -> 3.1 texels.  THAT is round 6's "flat
# 2-3 px coloured lozenges with no dome": the critic measured the texture, not
# the drawing.  A button CANNOT be painted here at any level of care, which is
# why `DECKS` below hands the controls to the integrator as geometry -- and why
# what IS painted for each control is its COLLAR, which is 3-4x wider.
#
# What a 256-buffer pixel is worth on the way out:
#     horizontally  256 -> ~82 texels, so 1 texel = 3.1 buffer px
#     vertically    256 -> ~32 texels, so 1 texel = 8.0 buffer px
# so the working minima for anything meant to survive are
#     >= 6 buffer px wide  AND  >= 16 buffer px tall  (2 texels each way).
# Round 5 drew 4 px keylines and 15 px caps.  Four px is HALF a texel and 15 px
# is under two rows -- which is why round 6's decks metered as empty planes
# with a ghost decal.  Nothing below is thinner than 8 px vertically.

_BW = {"legends-ultimate": 2.95,
       "street-fighter-2-champion-edition": 2.42,
       "time-crisis": 2.52,
       "terminator-2": 2.28}

_DK_DEPTH_FT = 0.92                 # ar2.upright's deck depth


def _dk_px(slug):
    """(px per foot across, px per foot back-to-front) in the 256 buffer."""
    return 256.0 / (_BW[slug] - 0.12), 256.0 / _DK_DEPTH_FT


def _uv(slug, u, v):
    """`DECKS` (u, v) -> (x, y) in this module's 256 paint buffer.

    THE PRINT AND THE GEOMETRY ARE DRIVEN FROM THE SAME TABLE.  Every collar
    painted below is read straight out of `DECKS[slug]`, so a printed ring can
    never drift off the modelled button that stands in it -- which is the
    failure mode that turns a control panel back into a slab.

    ar2 places a control at x = u * (bw/2 - 0.10); the painted quad spans
    bw - 0.12, i.e. half-width bw/2 - 0.06.  `k` is the ratio.
    """
    hw = _BW[slug] * 0.5
    k = (hw - 0.10) / (hw - 0.06)
    return 128.0 * (1.0 + k * u), 256.0 * v


# THE ONE NUMBER TO MOVE IF THE LIGHTING OR a2kit.DECK_MAT CHANGES.
DECK_XFER = {
    # a2kit.DECK_MAT today: ART_D (x0.88) for these two...
    "legends-ultimate": 0.88,
    "time-crisis": 0.88,
    # ...and ART_DK (x3.05) for these two.  Only the ART_DK pair is authored
    # through `_dk`; the ART_D pair is authored as-is.
    "street-fighter-2-champion-edition": 3.05,
    "terminator-2": 3.05,
}
_ART_DK = 3.05

# AN OPTIONAL, PAIRED CHANGE FOR THE INTEGRATOR -- BOTH LINES OR NEITHER.
# Champion Edition is the room's one PALE control deck (photo-read, see
# `ce_deck`).  Under ART_DK it has to live in the authored 0..84 band, and
# atlas4.QUANT = 20 leaves that band FIVE levels per channel; a busy pale
# collage posterises in it, which is visible in the AS RENDERED column of
# `deck_g2_r7.png`.  Adding one row to a2kit.DECK_MAT gives it the same
# thirteen-level ladder every other printed deck in the room has:
#
#     DECK_MAT["street-fighter-2-champion-edition"] = "D"
#     art_g2.DECK_XFER["street-fighter-2-champion-edition"] = 0.88
#
# Do BOTH or NEITHER: one without the other is 3.5x out either way.  The
# module SHIPS the un-requested value, so doing nothing is safe.
DECK_MAT_REQUEST = {
    "street-fighter-2-champion-edition": {
        "want": "D",
        "why": ("pale printed collage; ART_DK + QUANT 20 leaves 5 levels "
                "per channel and it posterises"),
        "paired_with": "art_g2.DECK_XFER[slug] = 0.88",
        "optional": True,
    },
}
# MEASURED, not assumed.  An ART_DK (#4c4c4c) deck faces UP, and this scene
# gives an up-facing surface far more than the 0.30 albedo factor takes away:
# round 5 authored terminator-2's deck ground at ~(26,24,33) and the round-6
# render (`shots/r6_full_south.png`, sample (160,240)-(300,262)) meters it at
# (80,78,79).  That is why round 5's "black" T2 deck arrived as a MID GREY
# slab and round 5's dark-navy Champion Edition arrived pale blue-grey.
# ART_D (#c9c9c9) decks measure ~0.88 and are authored as-is.
#
# So the two ART_DK decks below are written in TRUE ALBEDO -- the colour the
# surface should be in the finished render, which is the number a critic can
# hold against the photograph -- and `_dk` divides by this on the way into the
# buffer.  If a2kit's DECK_MAT or the daylight changes, this ONE number moves.


def _buf_dk(v):
    """`_buf` for an ART_DK panel: fill with a TRUE-ALBEDO hex, divided."""
    c = _dk(v)
    return _buf("#%02x%02x%02x"
                % tuple(min(255, int(x * 255 + 0.5)) for x in c))


def _dk(v):
    """True-albedo hex -> the value to paint on an ART_DK deck."""
    c = _c(v)
    f = DECK_XFER.get(_dk.slug, _ART_DK)
    return (c[0] / f, c[1] / f, c[2] / f)


_dk.slug = "terminator-2"          # set by each ART_DK deck before it paints


def _dkv(y0, y1, stops):
    """`_vgrad` in true albedo, divided for ART_DK."""
    f = _vgrad(y0, y1, stops)

    k = DECK_XFER.get(_dk.slug, _ART_DK)

    def g(x, y):
        c = f(x, y)
        return (c[0] / k, c[1] / k, c[2] / k)
    return g


def _collar(b, cx, cy, rx, ry, rings):
    """A PRINTED collar -- the concentric ring a button or a stick sits in.

    This is the most photo-supported graphic on any deck in this room.
    `scratchpad/arc4/art/r7/v45_nearDeck.png` (v4 5 px (0,300)-(95,445) at 12x)
    shows every button on the near cabinet standing inside a tan printed ring,
    and `r7/v43_lu2.png` (v4 3 px (380,270)-(600,460) at 7x) shows the Legends
    Ultimate's sticks inside three-ring pink/white/black targets.  A collar is
    0.28-0.45 ft across, i.e. 9-15 texels -- three to four times the button
    itself -- so the COLLAR is what makes a control read at atlas resolution
    and the modelled button is what makes it read at camera resolution.

    `rings` is [(radius_fraction, colour, alpha), ...], painted outside in.
    """
    for (f, col, a) in rings:
        _disc(b, cx, cy, rx * f, ry * f,
              _c(col) if isinstance(col, str) else col, a)


def _collars_for(b, slug, rings_btn, rings_stick, k_btn=2.7, k_stick=3.5,
                 cf=None):
    """Paint one collar under every button and stick in `DECKS[slug]`."""
    fx, fy = _dk_px(slug)
    if cf is not None:
        rings_btn = [(f, cf(c), a) for (f, c, a) in rings_btn]
        rings_stick = [(f, cf(c), a) for (f, c, a) in rings_stick]
    d = DECKS[slug]
    for s in d.get("sticks") or ():
        cx, cy = _uv(slug, s["u"], s["v"])
        r = s["top_r_ft"] * k_stick
        _collar(b, cx, cy, r * fx, r * fy, rings_stick)
    for bt in d.get("buttons") or ():
        cx, cy = _uv(slug, bt["u"], bt["v"])
        r = bt["r_ft"] * k_btn
        _collar(b, cx, cy, r * fx, r * fy, rings_btn)


def _cells(b, x0, y0, x1, y1, cols, nx, ny, seed, gut=2.0, a=1.0,
           cf=None):
    """A printed mosaic of small colour cells -- a multicade licence collage.

    Champion Edition's deck really is one of these; see `r7/v44_ce_deck.png`
    (v4 4 px (96,162)-(142,188) at 30x).  Cells are sized so the SHORT side is
    at least 3 output texels; below that they average to a flat tint and the
    panel goes back to being a slab.
    """
    cf = cf or _c
    cw = (x1 - x0) / float(nx)
    ch = (y1 - y0) / float(ny)
    for j in range(ny):
        for i in range(nx):
            h = _h2(i * 7 + 3, j * 11 + 5, seed)
            col = cols[int(h * len(cols)) % len(cols)]
            jx = (_h2(i, j, seed + 1) - 0.5) * gut
            _rect(b, x0 + i * cw + gut * 0.5 + jx, y0 + j * ch + gut * 0.5,
                  x0 + (i + 1) * cw - gut * 0.5 + jx,
                  y0 + (j + 1) * ch - gut * 0.5, cf(col), a)


def _keyline(b, pts, w, col, a=1.0, closed=True, cf=None):
    """A printed keyline.  `w` is the stroke in BUFFER px measured vertically;
    kx=1.0 keeps it even on the squeezed panel."""
    _pline(b, pts, w, (cf or _c)(col), a, kx=1.0, closed=closed)


def _chamfer(x0, y0, x1, y1, c):
    """Rect path with the two FRONT corners cut -- Time Crisis's printed border
    does exactly this in v4 4 (r7/v44_tc.png)."""
    return [(x0, y0), (x1, y0), (x1, y1 - c), (x1 - c, y1),
            (x0 + c, y1), (x0, y1 - c)]


def _well(b, slug, g, fill, rim, rim_w=6.0, rim_col="#d6b877", pad=0.10):
    """The printed holster well a light gun lies in, taken from its own
    `DECKS` entry so the print and the modelled cradle register."""
    fx, fy = _dk_px(slug)
    cx, cy = _uv(slug, g["u"], g["v"])
    hw = (g["len_ft"] * 0.46 + pad) * fx
    hh = (g["len_ft"] * 0.20 + pad * 0.5) * fy
    _rrect(b, cx - hw, cy - hh, cx + hw, cy + hh, 14.0, _c(fill), 1.0)
    _rrect(b, cx - hw + 8, cy - hh + 8, cx + hw - 8, cy + hh - 8, 11.0,
           _c(rim), 1.0)
    _keyline(b, [(cx - hw, cy - hh), (cx + hw, cy - hh),
                 (cx + hw, cy + hh), (cx - hw, cy + hh)],
             rim_w, rim_col, 0.9)


'''


LU = r'''def lu_deck(px, ox, oy, tile=TILE):
    """BLACK GALAXY DECK -- and this one is READ now, not inferred.

    ROUND 5 DECLARED THIS DECK "INFERRED" AND WAS RIGHT TO.  IT NO LONGER HAS
    TO BE.  Round 5 worked from v3 4 and v4 8, where the machine is 130 px tall
    and its controls are single pixels.  `docs/photos-jpg/Arcade Room v4 3.jpg`
    sees the SAME deck from a few feet away at the bottom right of frame, and
    at 7-10x (crops `r7/v43_lu.png`, px (395,300)-(510,450) at 10x, and
    `r7/v43_lu2.png`, px (380,270)-(600,460) at 7x) it resolves:

      * a NEAR-BLACK ground carrying a MAGENTA / VIOLET NEBULA over the right
        half with white star specks -- a printed space graphic, not a plain
        panel;
      * "LEGENDS ULTIMATE" printed along the FRONT edge in CHARTREUSE
        yellow-green italic caps.  That is the machine identifying itself on a
        second surface and it independently corroborates the marquee reading;
      * THREE-RING PRINTED COLLARS -- pink / white / black -- round both
        joysticks, and a gold ring behind every button;
      * a big printed bezel ring dead centre for the trackball, whose ball is
        DARK and speckled, not white.

    The joysticks are RED ball-tops (round 5 guessed white).  There is NO
    spinner: round 5 inferred one from the product spec, and at 10x the centre
    of this deck holds a trackball and a block of small dark admin buttons and
    nothing else.  Dropped, and said so.

    Tile TOP = deck BACK (screen end), tile BOTTOM = the player's edge.
    Material is ART_D (#c9c9c9 in a2kit.DECK_MAT), i.e. roughly 0.9x on the way
    out, so what is authored here is very nearly true albedo.
    """
    slug = "legends-ultimate"
    xs = _xs(slug, "deck")
    fx, fy = _dk_px(slug)
    b = _buf("#0d0c12")
    # --- the printed nebula.  Right half, magenta into violet into black.
    # Big soft masses only: at 30 output rows anything finer averages away.
    for (cx, cy, rx, ry, col, al) in (
            (214.0, 120.0, 62.0, 118.0, "#4e1442", 0.90),
            (226.0, 100.0, 40.0, 76.0, "#7a2260", 0.75),
            (238.0, 138.0, 26.0, 50.0, "#a8367a", 0.50),
            (168.0, 168.0, 40.0, 58.0, "#2a0e30", 0.70),
            (52.0, 70.0, 44.0, 62.0, "#1b1530", 0.65)):
        _disc(b, cx, cy, rx, ry, _c(col), al)
    # star specks -- sparse, and tall enough to survive the box filter
    for k in range(18):
        sx = 8.0 + _h2(k, 3, 77) * 240.0
        sy = 10.0 + _h2(k, 9, 91) * 200.0
        r = 1.3 + _h2(k, 5, 12) * 1.1
        _disc(b, sx, sy, r, r * 3.0, _c("#f2f0fa"), 0.95)
    # --- a soft black printed field under each cluster, so no modelled button
    # ever sits straight on the nebula
    for u in (-0.66, 0.66):
        cx, cy = _uv(slug, u, 0.46)
        _disc(b, cx, cy, 0.58 * fx, 0.30 * fy, _c("#08070c"), 0.82)
    # --- printed collars, read straight out of DECKS so the modelled buttons
    # land in them: pink / white / black three-ring targets on the sticks,
    # gold rings behind the buttons -- exactly as v4 3 resolves them
    _collars_for(b, slug,
                 rings_btn=[(1.00, "#b8963f", 0.95), (0.74, "#100d13", 1.0)],
                 rings_stick=[(1.00, "#c9578f", 0.95), (0.80, "#efe6ee", 0.95),
                              (0.60, "#241a24", 1.00), (0.40, "#0c0a10", 1.00)],
                 k_btn=2.0, k_stick=2.7)
    # --- the trackball bezel, dead centre, OD 0.45 ft = 14 texels
    tb = DECKS[slug]["trackball"]
    tcx, tcy = _uv(slug, tb["u"], tb["v"])
    _collar(b, tcx, tcy, 1.55 * tb["r_ft"] * fx, 1.55 * tb["r_ft"] * fy,
            [(1.00, "#8b9099", 0.95), (0.80, "#20222c", 1.0),
             (0.58, "#0a0a0e", 1.0)])
    # --- the printed strip behind the admin buttons
    _rrect(b, 96.0, 26.0, 160.0, 62.0, 7.0, _c("#15141b"), 0.92)
    # --- the CHARTREUSE wordmark along the front edge, left of centre.
    # cap 34 buffer px = 4.3 output rows; round 5 set 15 px, which is under two
    # rows, and is why it never appeared in any render.
    _text(b, "LEGENDS ULTIMATE", 10, 216, 34.0, _c("#b9d43a"), weight=0.19,
          xs=xs, wide=1.06, track=0.19, ital=0.20, align="l", a=0.95)
    # --- the lit white front lip.  Resolved in BOTH v3 4 and v4 8 and the one
    # control-panel feature either of those frames gives up; kept from round 5.
    _rect(b, 0, 224, 256, 232, _c("#141319"), 1.0)
    _rect(b, 0, 232, 256, 248, _c("#f7f9fc"), 1.0)
    _rect(b, 0, 248, 256, 256, _c("#8f98a6"), 1.0)
    _commit(px, ox, oy, b, tile)
'''


CE = r'''def ce_deck(px, ox, oy, tile=TILE):
    """PALE MULTICADE COLLAGE PANEL -- the value is this round's correction.

    ROUND 5 PAINTED THIS DECK DARK NAVY.  THE PHOTOGRAPHS SAY IT IS PALE.
    `r7/v44_ce_deck.png` (v4 4 px (96,162)-(142,188) at 30x) and
    `r7/v45_ce_lu.png` (v4 5 px (238,165)-(300,195) at 22x) both show a LIGHT
    grey-white control panel printed edge to edge with a dense mosaic of small
    saturated cells -- pinks, crimsons, cobalts, creams -- which is the classic
    multicade licence collage, not a Capcom player-art panel.  The only two
    features that survive at low magnification are the two the roster named:
    the bright silver/steel band along the LEADING edge, and the olive-yellow
    instruction strip across the very BACK under the monitor.

    So this deck is the room's one BRIGHT control panel, and against T2's black
    steel and Time Crisis's red tray that is the biggest value break on the
    wall.  Nothing else on the south run is pale.

    The controls do NOT resolve in any frame.  `DECKS` gives the class layout
    (two ball-tops, six buttons a player in a FLAT 2 x 3 grid, both clusters
    the same hand -- stick left, buttons right, which is how a dedicated SFII
    panel is built) and flags it as such.  The ball colour and the white/
    crimson split ARE photo-supported: v3 4 at 12x (`r7/ce_deck.png`) shows a
    pale-blue ball with pale and red caps round it.

    Material is ART_DK (#4c4c4c): a deck authored here renders about THREE
    times its authored value (measured -- round 6's ground authored ~(30,39,64)
    metered (112,133,181) in `shots/r6_full_south.png`).  So this panel is
    authored in the 8..96 band on purpose: it is a PALE deck expressed dark.
    """
    slug = "street-fighter-2-champion-edition"
    _dk.slug = slug
    xs = _xs(slug, "deck")
    fx, fy = _dk_px(slug)
    b = _buf_dk("#d8d6d0")                    # renders ~ #d8d6d0, warm pale grey
    # --- the olive-yellow instruction strip across the very back
    _rect(b, 0, 0, 256, 26, _dk("#9c9840"), 1.0)
    _rect(b, 0, 26, 256, 34, _dk("#312f28"), 1.0)
    # --- the printed licence collage.  Cells are 0.19 x 0.16 ft = 7 x 6
    # output texels, which is the smallest thing on this deck that survives.
    _cells(b, 4, 38, 252, 196,
           ("#9a6068", "#6d8aa6", "#b6b2a6", "#a0789a", "#6f9a92",
            "#a89a6c", "#8a76a2", "#c0bcb2", "#a06a66", "#7688a6"),
           9, 5, seed=41, gut=4.0, a=0.97, cf=_dk)
    # a few brighter hero cells so the field is not uniform noise
    for (i, j, col) in ((1, 0, "#e2ded0"), (3, 2, "#c4525e"),
                        (5, 1, "#4e8fd0"), (7, 3, "#c8ae44"),
                        (2, 4, "#b06aa8"), (8, 0, "#9fb0a8"),
                        (6, 4, "#d8d4c6"), (0, 2, "#7a90a8")):
        _rect(b, 4 + i * 27.6 + 2.0, 38 + j * 31.6 + 2.0,
              4 + (i + 1) * 27.6 - 2.0, 38 + (j + 1) * 31.6 - 2.0,
              _dk(col), 1.0)
    # --- NO printed island.  v4 4 at 30x shows the collage running UNDER the
    # controls edge to edge, which is what makes this deck the room's busiest
    # printed surface; the controls get ring collars and nothing else.  Two
    # thin printed player keylines mark the split, red for 1P and blue for 2P,
    # which is a Capcom convention and is declared as such in DECK_EVIDENCE.
    for (u, key) in ((-0.60, "#b03840"), (0.42, "#3462b4")):
        cx, _t = _uv(slug, u, 0.5)
        _keyline(b, [(cx - 0.47 * fx, 66.0), (cx + 0.47 * fx, 66.0),
                     (cx + 0.47 * fx, 180.0), (cx - 0.47 * fx, 180.0)],
                 8.0, key, 0.95, cf=_dk)
    _collars_for(b, slug,
                 rings_btn=[(1.00, "#26262e", 0.98), (0.64, "#eceadf", 1.0)],
                 rings_stick=[(1.00, "#2a2a34", 0.95), (0.72, "#e8eaf0", 0.95),
                              (0.46, "#1c1c24", 1.0)],
                 k_btn=2.1, k_stick=2.8, cf=_dk)
    # --- the player numerals.  Cap 40 buffer px = 5 output rows; anything
    # under 32 is unreadable at this packing.
    _text(b, "1P", 14, 184, 40.0, _dk("#34343f"), weight=0.22, xs=xs,
          track=0.18, align="l", a=0.9)
    _text(b, "2P", 242, 184, 40.0, _dk("#34343f"), weight=0.22, xs=xs,
          track=0.18, align="r", a=0.9)
    # --- the bright steel bezel band along the leading edge.  Roster-named,
    # and a hard metallic line in v3 4, v4 4 and v4 8.
    _rect(b, 0, 198, 256, 206, _dk("#14141a"), 1.0)
    _rect(b, 0, 206, 256, 240,
          _dkv(206, 240, [(0.0, "#eef1f6"), (0.30, "#a8aeb8"),
                            (0.62, "#6a6e78"), (1.0, "#c4c9d2")]), 1.0)
    _rect(b, 0, 240, 256, 256, _dk("#16161c"), 1.0)
    _commit(px, ox, oy, b, tile)
'''


TC = r'''def tc_deck(px, ox, oy, tile=TILE):
    """RED TRAY, TAN CHAMFERED KEYLINE, TWO PRINTED CARDS, TWO GUNS.

    `docs/photos-jpg/Arcade Room v4 4.jpg` at 14x (`r7/v44_tc.png`, px
    (30,160)-(130,250)) is the best photograph of any control deck in this room
    and it settles this one completely:

      * the deck is a saturated RED-ORANGE tray -- the only warm control panel
        on the south wall;
      * a TAN / GOLD PRINTED KEYLINE traces the whole deck about 0.10 ft in
        from the edge and CHAMFERS both front corners.  Round 5 drew a plain
        gold band across the lip and missed the border entirely; the chamfer is
        the most distinctive printed line on this wall and it is unmistakable
        in that crop;
      * TWO CREAM PRINTED CARDS lie across the BACK, each carrying a row of
        small saturated cells and dark type;
      * a RED gun sits left of centre and a BLUE gun right of it, each in its
        own dark printed well.  Corroborated in v4 5 (`r7/v45_south.png`) and
        v4 8 (`r7/v48_t2tc.png`).

    No joystick and no button field: this machine is played with two guns and a
    floor pedal.  Material is ART_D (#c9c9c9), roughly 0.9x out, so the hexes
    below are close to true albedo.

    Tile TOP = deck BACK, tile BOTTOM = the player's edge.
    """
    slug = "time-crisis"
    xs = _xs(slug, "deck")
    fx, fy = _dk_px(slug)
    b = _buf("#a83d31")
    # Two flat value bands rather than a full-field gradient: the back of the
    # tray sits in the monitor's shadow in every frame, and flat blocks are
    # both what survives 32 output rows and what zlib likes.
    _rect(b, 0, 0, 256, 30, _c("#6d2620"), 1.0)
    _rect(b, 0, 30, 256, 96, _c("#9c3a2e"), 1.0)
    _rect(b, 0, 96, 256, 200, _c("#b8473a"), 1.0)
    # --- the tan printed keyline with chamfered FRONT corners
    _keyline(b, _chamfer(11.0, 26.0, 245.0, 198.0, 26.0), 8.0, "#d6b877", 0.95)
    _keyline(b, _chamfer(20.0, 35.0, 236.0, 189.0, 21.0), 3.0, "#8a6a30", 0.55)
    # --- the two cream printed instruction cards along the back
    for (sx, seed) in ((60.0, 5), (196.0, 9)):
        _rrect(b, sx - 0.46 * fx, 34.0, sx + 0.46 * fx, 86.0, 5.0,
               _c("#dcd8cb"), 0.97)
        _rect(b, sx - 0.46 * fx, 34.0, sx + 0.46 * fx, 45.0,
              _c("#2b4f8e"), 0.95)
        _cells(b, sx - 0.42 * fx, 49.0, sx + 0.42 * fx, 82.0,
               ("#b23a2c", "#2f5fa8", "#c8a23a", "#3f7a63", "#6d3a7a",
                "#8f9199"), 6, 2, seed=seed, gut=2.5, a=0.9)
    # --- the two gun wells, taken from DECKS so the print registers with the
    # modelled cradles.  RED gun left of centre, BLUE gun right.
    gs = DECKS[slug]["guns"]
    _well(b, slug, gs[0], "#4a1712", "#631f17")
    _well(b, slug, gs[1], "#1b2748", "#26356a")
    # --- the two small start buttons get a printed cream collar each
    _collars_for(b, slug,
                 rings_btn=[(1.00, "#e2d6ae", 0.85), (0.60, "#3a1512", 1.0)],
                 rings_stick=[], k_btn=2.9)
    # --- the gold front lip, then the dark maroon under-lip
    _rect(b, 0, 200, 256, 216, _c("#c9a94e"), 1.0)
    _rect(b, 0, 216, 256, 224, _c("#8a6a30"), 1.0)
    _rect(b, 0, 224, 256, 256, _c("#511b16"), 1.0)
    _text(b, "TIME CRISIS", 128, 250, 30.0, _c("#e8d4a2"), weight=0.20,
          xs=xs, wide=1.02, track=0.20, ital=0.22, align="c", a=0.92)
    _commit(px, ox, oy, b, tile)
'''


T2 = r'''def t2_deck(px, ox, oy, tile=TILE):
    """BLACK STEEL GUN DECK -- and the photograph really does say it is bare.

    THIS IS THE ONE PLACE I ARGUE WITH THE ASSIGNMENT.  Every frame that sees
    this deck -- v4 5 at 38x (`r7/v45_t2deck.png`, px (190,166)-(222,186)),
    v4 8 at 16x (`r7/v48_t2tc.png`) and v3 4 at 12x (`r7/t2_deck.png`) -- shows
    a NEAR-BLACK panel carrying a BLUE gun on the left, a RED gun on the right,
    a maroon T-molding along the player edge and two small bright specks at the
    front.  There is no printed field on it.  Inventing a busy graphic here is
    exactly the failure ROOM-BRIEF names, so what this deck gets instead is
    CONTRAST and STRUCTURE, all of it either photographed on this deck or
    photographed on another surface of THIS machine:

      * two big printed holster wells with bright chrome keylines.  The wells
        are physically there (both guns sit down in them) and the keyline is
        what makes a black panel read as built rather than blank;
      * a solid BLUE bar under the left well and a solid RED bar under the
        right one.  Blue-left / red-right is the loudest thing the photographs
        say about this deck, and printing it puts that colour on ten times the
        area instead of leaving it all on two small gun bodies;
      * the chrome SHARD device dead centre.  Photo-read on this machine's
        MARQUEE (roster: "a bright chrome/steel shard-and-blade device") and
        its front panel carries the same chrome T2 mark.  It is this machine's
        own device moved onto a third surface, not a new invention, and it is
        declared as such in EVIDENCE;
      * the maroon T-molding band along the player edge, photo-read.

    Round 5 painted two thin chrome _ring()s here at 6 buffer px -- under one
    output texel -- which is precisely the "faint round ghost decal" a critic
    measured in `shots/r6_full_south.png`.  Everything here is >= 16 px tall.

    Material is ART_DK (#4c4c4c): the ground authored ~(26,24,33) in round 5
    metered (80,78,79) in the round-6 render, so this panel renders about 3x
    what it is authored at.  Round 5's deck was therefore a MID GREY slab on
    the machine the roster calls the blackest object in the room.  This one is
    authored at ~(11,10,15) so it lands near 35 -- black, as photographed.
    """
    slug = "terminator-2"
    _dk.slug = slug
    xs = _xs(slug, "deck")
    fx, fy = _dk_px(slug)
    b = _buf_dk("#22202c")
    _rect(b, 0, 0, 256, 34, _dk("#141220"), 1.0)          # monitor shadow
    _rect(b, 0, 34, 256, 208, _dk("#2a2836"), 1.0)
    # a machined brush across the working area -- four bands, 12 px each, so
    # each lands as 1.5 output rows and the panel is not algebraically flat
    for k in range(4):
        y = 46.0 + k * 38.0
        _rect(b, 0, y, 256, y + 12.0, _dk("#3a374c"), 0.55)
    # --- the two holster wells, chrome-keylined, with the printed player bar
    for (g, col, bar) in zip(DECKS[slug]["guns"],
                             ("#4a7ae0", "#d83a3a"), ("#2a4a9e", "#9a2020")):
        cx, cy = _uv(slug, g["u"], g["v"])
        hw, hh = 0.40 * fx, 0.170 * fy
        _rrect(b, cx - hw, cy - hh, cx + hw, cy + hh, 16.0, _dk("#111116"), 1.0)
        _keyline(b, [(cx - hw, cy - hh), (cx + hw, cy - hh),
                     (cx + hw, cy + hh), (cx - hw, cy + hh)],
                 9.0, "#c2c8d2", 0.92, cf=_dk)
        _rrect(b, cx - hw + 10, cy - hh + 10, cx + hw - 10, cy + hh - 10,
               12.0, _dk("#151220"), 1.0)
        _rect(b, cx - hw, cy + hh + 6, cx + hw, cy + hh + 42, _dk(col), 1.0)
        _rect(b, cx - hw, cy + hh + 42, cx + hw, cy + hh + 52, _dk(bar), 1.0)
    # --- the chrome shard, dead centre
    _shard = [(112, 58), (146, 72), (140, 114), (158, 106), (150, 152),
              (118, 138), (124, 98), (106, 106)]
    _poly(b, _shard,
          _dkv(58, 152, [(0.0, "#f0f3f8"), (0.50, "#b8bec9"),
                           (1.0, "#6a707c")]), 1.0)
    _keyline(b, _shard, 3.0, "#141018", 0.8, cf=_dk)
    # --- printed collars under the two white start buttons
    _collars_for(b, slug,
                 rings_btn=[(1.00, "#9aa0aa", 0.75), (0.62, "#101018", 1.0)],
                 rings_stick=[], k_btn=2.8, cf=_dk)
    # --- the maroon T-molding band along the player edge, then the black kick
    _rect(b, 0, 208, 256, 214, _dk("#141220"), 1.0)
    _rect(b, 0, 214, 256, 238, _dk("#7c2030"), 1.0)
    _rect(b, 0, 238, 256, 246, _dk("#a83a44"), 0.8)
    _rect(b, 0, 246, 256, 256, _dk("#100e16"), 1.0)
    _commit(px, ox, oy, b, tile)
'''
