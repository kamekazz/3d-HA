# =========================================================================
#  ROUND 5 -- THE SOUTH RUN.  Four machines, four unrelated wraps.
#
#  Round 4's defect, named identically by three independent critics: "all
#  three cabinets are one asset recoloured -- the same flat-black front panel
#  with the SAME centred grey coin-door rectangle, the same two-joystick deck
#  (one red top, one blue top) over the same row of flat square buttons, only
#  the trim colour and a small floated logo differ."  Verified against
#  scratchpad/arc4/shots/r4_mq_south.png: correct.
#
#  Everything below the marquee is redrawn.  No two of these four machines
#  share a ground colour, a composition, a coin-door treatment or a control
#  layout, and every panel covers its quad edge to edge.
# =========================================================================

# panel width / panel height in FEET for MY four machines, computed from
# ar2._profile + ar2.upright with each machine's own row of SOUTH_RUN.
# Round 4 used one ASPECT table for every machine; the widths here differ by
# 30% (Legends Ultimate 2.95 ft against T2's 2.28) so one table pre-squeezed
# three of the four wrong.
#   marquee = (bw - 0.12) / mqh
#   side    = (bd/2 + DECK_OUT + 0.30) / (top + plinth)      [profile bbox]
#   front   = (bw - 0.16) / (dy - 0.62 - plinth - 0.16)
#   deck    = (bw - 0.12) / 0.92
#   screen  = (bw - 0.34) / (mq_lo - 0.26 - dy - 0.46)
A = {
    "legends-ultimate": {
        "marquee": 3.54, "side": 0.464, "front": 1.52, "deck": 3.08,
        "screen": 1.28},
    "street-fighter-2-champion-edition": {
        "marquee": 3.97, "side": 0.490, "front": 1.35, "deck": 2.50,
        "screen": 1.00},
    "time-crisis": {
        "marquee": 3.53, "side": 0.464, "front": 1.42, "deck": 2.61,
        "screen": 1.04},
    "terminator-2": {
        "marquee": 3.60, "side": 0.498, "front": 1.29, "deck": 2.35,
        "screen": 0.97},
}


def _xs(slug, panel):
    return 1.0 / A[slug][panel]


def _hgrad(x0, x1, stops):
    """Colour callable: HORIZONTAL ramp through (t, colour) stops."""
    st = [(t, _c(cc)) for (t, cc) in stops]

    def f(x, y):
        t = (x - x0) / max(1e-6, x1 - x0)
        t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
        for i in range(len(st) - 1):
            if t <= st[i + 1][0]:
                lo, hi = st[i], st[i + 1]
                u = (t - lo[0]) / max(1e-6, hi[0] - lo[0])
                return _mix(lo[1], hi[1], u)
        return st[-1][1]
    return f


def _typerun(b, x0, x1, ybase, cap, col, n, seed, weight=0.20, kx=1.0, a=1.0):
    """A run of `n` pseudo-glyphs across x0..x1 -- letterform-SCALE marks.

    Used for the wordmarks on Legends Ultimate's licence grid that the
    photograph resolves as a coloured shape but NOT as a readable title.
    Drawing invented titles there would be worse than drawing the ink: this
    puts real stems, bowls and crossbars at the right size and colour without
    claiming a game the owner does not own.
    """
    w = max(1.0, cap * weight)
    step = (x1 - x0) / float(n)
    for i in range(n):
        gx = x0 + i * step
        gw = step * 0.72
        h = _h2(i, seed, 7)
        if h < 0.30:                                   # stem + arm
            _seg(b, gx, ybase, gx, ybase - cap, w, col, a, kx)
            _seg(b, gx, ybase - cap * 0.52, gx + gw * 0.8,
                 ybase - cap * 0.52, w, col, a, kx)
        elif h < 0.55:                                 # bowl
            _ring(b, gx + gw * 0.45, ybase - cap * 0.5, gw * 0.46,
                  cap * 0.5, w, col, a, n=16)
        elif h < 0.75:                                 # stem + bowl
            _seg(b, gx, ybase, gx, ybase - cap, w, col, a, kx)
            _seg(b, gx, ybase - cap, gx + gw * 0.75, ybase - cap * 0.72,
                 w, col, a, kx)
            _seg(b, gx + gw * 0.75, ybase - cap * 0.72, gx, ybase - cap * 0.44,
                 w, col, a, kx)
        elif h < 0.90:                                 # diagonal pair
            _seg(b, gx, ybase, gx + gw * 0.45, ybase - cap, w, col, a, kx)
            _seg(b, gx + gw * 0.45, ybase - cap, gx + gw * 0.9, ybase,
                 w, col, a, kx)
        else:                                          # squared C
            _seg(b, gx + gw * 0.85, ybase - cap * 0.88, gx, ybase - cap * 0.88,
                 w, col, a, kx)
            _seg(b, gx, ybase - cap * 0.88, gx, ybase - cap * 0.12, w, col,
                 a, kx)
            _seg(b, gx, ybase - cap * 0.12, gx + gw * 0.85, ybase - cap * 0.12,
                 w, col, a, kx)


def _script(b, x0, x1, ybase, cap, col, seed, w=2.2):
    """A cursive/script wordmark: one continuous stroked path with a swash."""
    pts = []
    n = 26
    for i in range(n + 1):
        t = i / float(n)
        x = x0 + (x1 - x0) * t
        y = ybase - cap * (0.34 + 0.30 * math.sin(t * 9.0 + seed)
                           + 0.22 * math.sin(t * 21.0 + seed * 2.0))
        pts.append((x, y))
    _pline(b, pts, w, col, 1.0, kx=1.0)
    _seg(b, x0 - 3.0, ybase - cap * 0.10, x0 + (x1 - x0) * 0.34,
         ybase - cap * 0.10, w * 0.8, col, 0.85, kx=1.0)
    _seg(b, x1 - (x1 - x0) * 0.10, ybase - cap * 0.9, x1 + 4.0,
         ybase - cap * 1.25, w * 0.8, col, 0.9, kx=1.0)


def _sheen(b, cx, w, lo, hi, col, a=0.5):
    """A soft vertical satin band -- what a curved vinyl flank does to light."""
    for x in range(max(0, int(cx - w)), min(TILE, int(cx + w) + 1)):
        t = 1.0 - abs(x - cx) / float(w)
        if t <= 0.0:
            continue
        _rect(b, x, lo, x + 1, hi, col, a * t * t)


def _plate(b, x0, y0, x1, y1, face, edge, depth=3.0, lip=True):
    """A recessed metal plate: dark reveal, then the face, then a top light."""
    _rect(b, x0 - depth, y0 - depth, x1 + depth, y1 + depth,
          _c("#07070a"), 0.85)
    _rect(b, x0, y0, x1, y1, face, 1.0)
    if lip:
        _rect(b, x0, y0, x1, y0 + 2.0, edge, 0.9)
        _rect(b, x0, y1 - 2.0, x1, y1, _c("#0b0b0e"), 0.7)


# =========================================================================
#  LEGENDS ULTIMATE (AtGames)     SOUTH_RUN[0]  -- x 2.05, bw 2.95 (widest)
#
#  The only machine of its brand in the room and the widest cabinet in it.
#  Photograph: matte black EVERYWHERE -- carcase, molding, marquee band and
#  bezel -- with silver angular italic caps on the marquee and, on the lower
#  front, a GRID OF SIXTEEN LICENCE LOGOS in two columns of eight.  It is a
#  home multicade: it has no coin door at all, which is the cleanest
#  per-machine coin variation on this wall.
#  Evidence: v3 4 px (985,690)-(1130,850) at 7x -> art/g2r5/lu_grid.png;
#  marquee v3 4 (1025,570)-(1175,615) at 12x; corroborated v4 8 and v4 5.
# =========================================================================
_LU_BLACK = "#191d25"


def lu_marquee(px, ox, oy, tile=TILE):
    """Plain black band, 'LEGENDS ULTIMATE' in silver angular italic caps,
    centred, sitting in the UPPER half with clear black beneath it."""
    xs = _xs("legends-ultimate", "marquee")
    b = _buf(_LU_BLACK)
    _field(b, lambda x, y, c: _mix(_c("#242934"), _c("#101319"),
                                   ((y - 40) / 216.0) ** 0.8
                                   if y > 40 else 0.0))
    # a very faint blue backlight bleed at the top edge -- the band IS lit
    _rect(b, 0, 0, 256, 30, _c("#2a3550"), 0.35)
    _rect(b, 0, 0, 256, 10, _c("#3d4a6b"), 0.30)
    _text(b, "LEGENDS ULTIMATE", 128, 132, 62.0, _c("#0a0b0f"), weight=0.30,
          xs=xs, wide=0.90, track=0.13, ital=0.20, align="c")
    _text(b, "LEGENDS ULTIMATE", 128, 130, 62.0,
          _vgrad(70, 130, [(0.0, "#ffffff"), (0.45, "#d6dae2"),
                           (0.55, "#8b919c"), (1.0, "#e8ebf0")]),
          weight=0.185, xs=xs, wide=0.90, track=0.13, ital=0.20, align="c")
    # the clear black lower half the photograph shows, with the T-molding line
    _rect(b, 0, 178, 256, 182, _c("#2b2f38"), 0.55)
    _rect(b, 0, 249, 256, 256, _c("#05050a"), 1.0)
    _commit(px, ox, oy, b, tile)


def lu_side(px, ox, oy, tile=TILE):
    """The plainest flank in the room, and the photograph says so: black,
    no graphic.  It is NOT a slab -- a wide-body cabinet's flank carries a
    satin sheen down its length, a horizontal panel seam at deck height and
    a brushed silver kick rail, and all three read in v4 8.
    Tile left = cabinet BACK, tile right = cabinet FRONT, tile top = top."""
    b = _buf(_LU_BLACK)
    _field(b, lambda x, y, c: _mix(_c("#20232b"), _c("#0c0d12"),
                                   min(1.0, abs(y - 96) / 190.0)))
    _sheen(b, 150.0, 74.0, 4.0, 252.0, _c("#464c58"), 0.65)
    _sheen(b, 66.0, 40.0, 4.0, 252.0, _c("#2a2e37"), 0.40)
    # horizontal panel seam at deck height (v4 8: the flank breaks here)
    _rect(b, 0, 146, 256, 150, _c("#050508"), 0.95)
    _rect(b, 0, 150, 256, 156, _c("#4a4f5a"), 0.75)
    _rect(b, 0, 62, 256, 65, _c("#050508"), 0.55)
    _rect(b, 0, 65, 256, 68, _c("#3b4049"), 0.45)
    # brushed silver kick rail along the floor, and the front-edge molding
    _rect(b, 0, 240, 256, 250, _c("#878d97"), 0.90)
    _rect(b, 0, 250, 256, 256, _c("#2a2d34"), 0.9)
    _rect(b, 247, 0, 256, 256, _c("#3a3e47"), 1.0)
    _rect(b, 244, 0, 247, 256, _c("#0a0a0e"), 0.9)
    _commit(px, ox, oy, b, tile)


# The licence grid, read left-to-right off art/g2r5/lu_grid.png.  Four of the
# sixteen are legible at 7x and are drawn as themselves; the other twelve
# resolve as a coloured wordmark SHAPE and are drawn as ink at letterform
# scale (see `_typerun`) rather than as invented titles.
#   (column, row, kind, colour, secondary)
_LU_GRID = [
    (0, 0, "script", "#e9ecf2", None),
    (0, 1, "pill", "#d9dce2", "#1a1c22"),
    (0, 2, "arch", "#c8145a", None),
    (0, 3, "type", "#e4699a", None),
    (0, 4, "type", "#a9c7a2", None),
    (0, 5, "swoosh", "#8a4fd0", None),
    (0, 6, "type", "#9aa4a0", None),
    (0, 7, "invaders", "#f2f4f8", "#2f6bd8"),
    (1, 0, "outline", "#4c86e8", "#f2f5fa"),
    (1, 1, "script", "#dfe3ea", None),
    (1, 2, "millipede", "#eef0f4", None),
    (1, 3, "bar", "#c8a68e", None),
    (1, 4, "starwars", "#e6e9f0", "#c03a3a"),
    (1, 5, "pill", "#a9a6c4", "#3d3f52"),
    (1, 6, "chip", "#3d6ee0", None),
    (1, 7, "tron", "#3c62d6", None),
]


def _lu_logo(b, kind, cx, cy, hw, hh, col, sec, xs, seed):
    c = _c(col)
    if kind == "script":
        _script(b, cx - hw, cx + hw * 0.9, cy + hh * 0.6, hh * 1.5, c, seed,
                w=2.0)
    elif kind == "pill":
        _rrect(b, cx - hw, cy - hh, cx + hw, cy + hh, hh * 0.95, c, 1.0)
        _typerun(b, cx - hw * 0.78, cx + hw * 0.78, cy + hh * 0.48,
                 hh * 1.05, _c(sec), 7, seed, weight=0.24, kx=xs)
    elif kind == "arch":
        pts = []
        for i in range(13):
            t = i / 12.0
            pts.append((cx - hw + 2 * hw * t, cy + hh * 0.7
                        - hh * 1.25 * math.sin(t * math.pi) * 0.55))
        _pline(b, pts, hh * 1.5, c, 1.0, kx=1.0)
        _pline(b, [(p[0], p[1] - hh * 0.55) for p in pts], hh * 0.35,
               _c("#f7d8e4"), 0.55, kx=1.0)
    elif kind == "swoosh":
        _seg(b, cx - hw - 4, cy - hh * 0.9, cx - hw * 0.2, cy + hh * 0.4,
             hh * 0.6, c, 0.9, kx=1.0)
        _typerun(b, cx - hw * 0.35, cx + hw, cy + hh * 0.75, hh * 1.6, c,
                 8, seed, weight=0.26, kx=xs)
        _seg(b, cx - hw, cy + hh * 1.05, cx + hw, cy + hh * 1.05, 2.0, c,
             0.8, kx=1.0)
    elif kind == "bar":
        _rect(b, cx - hw, cy - hh * 0.35, cx + hw, cy + hh * 0.35, c, 0.9)
        _typerun(b, cx - hw * 0.85, cx + hw * 0.85, cy + hh * 0.9,
                 hh * 1.3, c, 8, seed, weight=0.26, kx=xs)
    elif kind == "chip":
        _rrect(b, cx - hw, cy - hh * 0.8, cx + hw, cy + hh * 0.2, 3.0,
               _c("#b7b3cd"), 1.0)
        _rect(b, cx - hw * 0.30, cy + hh * 0.2, cx + hw * 0.30,
              cy + hh * 1.25, c, 1.0)
    elif kind == "invaders":
        _rect(b, cx - hw, cy - hh * 1.15, cx + hw, cy + hh * 1.15, c, 1.0)
        inv = ["00100", "01110", "11111", "10101", "10001"]
        p = max(1.0, hh * 0.34)
        for k in range(3):
            gx = cx - hw + hw * 0.30 + k * hw * 0.64
            for r, row in enumerate(inv):
                for q, ch in enumerate(row):
                    if ch == "1":
                        _rect(b, gx + q * p - p * 2.5,
                              cy - hh * 0.75 + r * p,
                              gx + q * p - p * 1.5,
                              cy - hh * 0.75 + (r + 1) * p, _c(sec), 1.0)
    elif kind == "millipede":
        _text(b, "MILLIPEDE", cx, cy + hh, hh * 2.1, c, weight=0.22,
              xs=xs, wide=1.45, track=0.08, align="c")
    elif kind == "starwars":
        _text(b, "STAR", cx, cy + hh * 0.15, hh * 1.55, c, weight=0.30,
              xs=xs, wide=2.55, track=0.05, align="c")
        _text(b, "WARS", cx, cy + hh * 1.55, hh * 1.55, c, weight=0.30,
              xs=xs, wide=2.70, track=0.05, align="c")
        _seg(b, cx - hw, cy + hh * 1.7, cx + hw, cy + hh * 1.7, 2.0,
             _c(sec), 0.85, kx=1.0)
    elif kind == "tron":
        _text(b, "TRON", cx, cy + hh, hh * 2.1, _c("#0a0f2a"), weight=0.36,
              xs=xs, wide=2.70, track=0.04, align="c")
        _text(b, "TRON", cx, cy + hh, hh * 2.1, c, weight=0.22, xs=xs,
              wide=2.70, track=0.04, align="c")
    elif kind == "outline":
        _text(b, "3D", cx - hw * 0.58, cy + hh, hh * 2.0, _c(sec),
              weight=0.34, xs=xs, wide=2.10, track=0.06, align="c")
        _typerun(b, cx - hw * 0.15, cx + hw, cy + hh, hh * 2.0, c, 5, seed,
                 weight=0.30, kx=xs)
    else:                                                   # "type"
        _typerun(b, cx - hw, cx + hw, cy + hh * 0.8, hh * 1.7, c, 8, seed,
                 weight=0.26, kx=xs)


def lu_front(px, ox, oy, tile=TILE):
    """THE HERO SURFACE of this machine: a full-bleed black field carrying
    the two-column licence grid, edge to edge and running to the floor.  No
    coin door -- Legends Ultimate is a home cabinet and has none, in any
    frame."""
    slug = "legends-ultimate"
    xs = _xs(slug, "front")
    b = _buf(_LU_BLACK)
    _field(b, lambda x, y, c: _mix(_c("#262b37"), _c("#101319"),
                                   min(1.0, ((y / 255.0) ** 0.55
                                             * 0.8 + abs(x - 108) / 320.0))))
    _sheen(b, 74.0, 92.0, 0.0, 256.0, _c("#2b3040"), 0.40)
    for (colm, row, kind, col, sec) in _LU_GRID:
        cx = 66.0 + colm * 122.0
        cy = 26.0 + row * 29.5
        _lu_logo(b, kind, cx, cy, 48.0, 7.0, col, sec, xs, row * 3 + colm)
    # the printed panel's own border: a hairline silver reveal all round,
    # which is what separates it from the carcase in v4 8
    for (x0, y0, x1, y1) in ((0, 0, 256, 3), (0, 253, 256, 256),
                             (0, 0, 3, 256), (253, 0, 256, 256)):
        _rect(b, x0, y0, x1, y1, _c("#4a4f5a"), 0.75)
    _commit(px, ox, oy, b, tile)


def lu_deck(px, ox, oy, tile=TILE):
    """Wide black deck.  The photographs do NOT resolve individual controls
    on this machine (roster: 'do not invent joysticks') -- what they DO
    resolve is a bright white lit strip along the full length of the deck's
    front lip.  So the print is monochrome: a charcoal field, two screened
    control-cluster outlines, player numerals at the back, and the lit lip.
    Tile TOP = deck BACK (screen end), tile BOTTOM = the player's edge."""
    slug = "legends-ultimate"
    xs = _xs(slug, "deck")
    b = _buf("#20242d")
    _field(b, lambda x, y, c: _mix(_c("#31363f"), _c("#171a21"),
                                   (y / 255.0) ** 0.9))
    # ONE printed control plate with a silver keyline -- the real controls
    # (DECKS['legends-ultimate']) stand on it.  An earlier pass screened two
    # big target rings here and they read as a face at panel scale.
    _rrect(b, 10, 46, 246, 208, 8.0, _c("#2a2f39"), 1.0)
    _rrect(b, 14, 50, 242, 204, 6.0, _c("#1c2028"), 1.0)
    _rect(b, 14, 50, 242, 54, _c("#8b919b"), 0.55)
    _rect(b, 14, 200, 242, 204, _c("#0b0d11"), 0.7)
    _rect(b, 126, 54, 130, 200, _c("#3d434d"), 0.55)
    _text(b, "1", 66, 78, 24.0, _c("#7d838d"), weight=0.22, xs=xs, align="c")
    _text(b, "2", 190, 78, 24.0, _c("#7d838d"), weight=0.22, xs=xs, align="c")
    _text(b, "LEGENDS ULTIMATE", 128, 34, 15.0, _c("#959ba5"), weight=0.20,
          xs=xs, wide=1.35, track=0.22, ital=0.18, align="c", a=0.85)
    # the lit white lip strip along the player edge -- resolved in v3 4 AND
    # v4 8, and the one control-panel feature either photograph gives up
    _rect(b, 0, 226, 256, 232, _c("#1b1e25"), 1.0)
    _rect(b, 0, 232, 256, 246, _c("#f6f8fb"), 1.0)
    _rect(b, 0, 246, 256, 251, _c("#b9c2cc"), 0.9)
    _rect(b, 0, 251, 256, 256, _c("#191c22"), 1.0)
    _commit(px, ox, oy, b, tile)


def lu_screen(px, ox, oy, tile=TILE):
    """DARK.  Every frame that sees this machine shows a dark screen with a
    faint cool sheen and the room's hex panels reflected in the glass -- no
    attract loop.  Painted dark, deliberately."""
    b = _buf("#0a0d14")
    _field(b, lambda x, y, c: _mix(_c("#11161f"), _c("#05070c"),
                                   min(1.0, (y / 255.0) * 0.9
                                       + abs(x - 90) / 500.0)))
    # faint reflected room light down the left third, and one hex reflection
    _sheen(b, 58.0, 52.0, 0.0, 256.0, _c("#233046"), 0.45)
    _poly(b, [(150, 60), (176, 46), (202, 60), (202, 90), (176, 104),
              (150, 90)], _c("#1b2532"), 0.55)
    for y in range(0, 256, 4):
        _rect(b, 0, y, 256, y + 1, _c("#000000"), 0.16)
    _rect(b, 0, 0, 256, 6, _c("#000000"), 0.8)
    _rect(b, 0, 250, 256, 256, _c("#000000"), 0.8)
    _commit(px, ox, oy, b, tile)


# =========================================================================
#  STREET FIGHTER II: CHAMPION EDITION (Capcom)   SOUTH_RUN[1] -- x 4.95
#
#  The only machine in the room standing on its own coloured base, and the
#  only ROYAL BLUE object on this wall.  Photograph: near-black carcase over
#  a big blue base printed with a ghosted pale fighter and 'CAPCOM' low;
#  marquee is a navy band with a gold-ringed oval badge and silver wings.
#  Base blue is the most trustworthy hex on the wall because v4 8 lights it
#  with white cans, not cove: #2b5baf .. #4e7bba.
#  Evidence: v3 4 (900,545)-(1010,830) at 5x -> art/g2r5/ce_whole.png;
#  v4 8 (340,100)-(520,260) at 7x -> art/g2r5/v48_south.png.
# =========================================================================
_CE_BLUE = "#2f62b6"


def ce_marquee(px, ox, oy, tile=TILE):
    """Navy ground; a wide gold-ringed OVAL badge fills the centre with
    'CHAMPION' arched over the top and 'EDITION' straight across the bottom;
    a green/gold brush wordmark in the black middle; silver wing forms spill
    out of the oval left and right onto the blue.

    NOTE THE PRE-SQUEEZE.  This band is 2.30 x 0.58 ft, so the tile is
    compressed 3.97:1 horizontally and a HORIZONTAL oval on the panel must be
    drawn TALL in the tile (rx 70, ry 100 -> 1.26 x 0.45 ft).  Drawing it
    wide in the tile, as the first pass did, lands a circle on the cabinet.
    """
    slug = "street-fighter-2-champion-edition"
    xs = _xs(slug, "marquee")
    b = _buf("#1d2a56")
    _field(b, lambda x, y, c: _mix(_c("#31468a"), _c("#131c46"),
                                   min(1.0, abs(y - 118) / 165.0
                                       + abs(x - 128) / 500.0)))
    _sheen(b, 128.0, 110.0, 0.0, 256.0, _c("#4560ad"), 0.35)
    # silver wing forms spilling out of the oval left and right
    for d in (-1, 1):
        base = 128 + d * 62
        tip = 128 + d * 126
        for k in range(6):
            t = k / 5.0
            y0 = 128 - 66 + k * 26
            _poly(b, [(base, y0), (tip, y0 + (t - 0.5) * 52),
                      (tip, y0 + 12 + (t - 0.5) * 52), (base, y0 + 16)],
                  _c("#d6dde9"), 0.78 - 0.07 * k)
        _seg(b, base, 128, tip, 128, 5.0, _c("#f0f3f8"), 0.85, kx=1.0)
    # the oval badge -- TALL in the tile, horizontal on the panel
    _disc(b, 128, 128, 74, 106, _c("#7a5f1c"), 1.0)
    _disc(b, 128, 128, 70, 101, _c("#eccf6a"), 1.0)
    _disc(b, 128, 128, 65, 95, _c("#8a6c22"), 1.0)
    _disc(b, 128, 128, 61, 90, _c("#0b0d16"), 1.0)
    _disc(b, 128, 124, 55, 80, _c("#151a28"), 1.0)
    # CHAMPION arched over the top of the oval
    for i, ch in enumerate("CHAMPION"):
        t = (i - 3.5) / 3.5
        _text(b, ch, 128 + t * 28.0, 74 + 16.0 * t * t, 34.0,
              _c("#f6f8fc"), weight=0.24, xs=xs, wide=1.15, align="c")
    # EDITION straight across the bottom
    _text(b, "EDITION", 128, 206, 30.0, _c("#eff2f8"), weight=0.24, xs=xs,
          wide=1.15, track=0.22, align="c")
    # the green-and-gold brush wordmark in the black middle of the oval
    _text(b, "STREET", 118, 122, 30.0, _c("#0a2610"), weight=0.38, xs=xs,
          wide=1.30, track=0.05, ital=0.24, align="c")
    _text(b, "STREET", 118, 121, 30.0, _c("#6cc94f"), weight=0.22, xs=xs,
          wide=1.30, track=0.05, ital=0.24, align="c")
    _text(b, "FIGHTER", 116, 158, 30.0, _c("#0a2610"), weight=0.38, xs=xs,
          wide=1.28, track=0.05, ital=0.24, align="c")
    _text(b, "FIGHTER", 116, 157, 30.0, _c("#9adc60"), weight=0.22, xs=xs,
          wide=1.28, track=0.05, ital=0.24, align="c")
    _text(b, "II", 162, 160, 44.0, _c("#f0c94e"), weight=0.30, xs=xs,
          wide=1.30, ital=0.26, align="c")
    _rect(b, 0, 0, 256, 6, _c("#0e1430"), 1.0)
    _rect(b, 0, 250, 256, 256, _c("#0e1430"), 1.0)
    _commit(px, ox, oy, b, tile)


def ce_side(px, ox, oy, tile=TILE):
    """Capcom big-blue: a near-black upper carcase over a royal-blue lower
    body, split on the diagonal the cabinet's own break makes, a white
    pinstripe down the front edge and a blue kick at the floor.  No
    figurative art -- the machine is close to head-on in every frame that
    sees it, so none resolves and none is drawn."""
    b = _buf("#1e2433")
    _field(b, lambda x, y, c: _mix(_c("#2f3850"), _c("#141926"),
                                   min(1.0, abs(x - 190) / 260.0
                                       + (y / 255.0) * 0.25)))
    # the blue lower body, cut on the cabinet's own break
    _poly(b, [(0, 152), (256, 138), (256, 256), (0, 256)],
          _c("#3d74c8"), 1.0)
    _poly(b, [(0, 152), (256, 138), (256, 152), (0, 168)], _c("#7ea3dc"), 0.7)
    _field(b, lambda x, y, c: c if y < 150 else _mix(
        tuple(c), _c("#1b3a70"), min(0.45, (y - 150) / 240.0)))
    _sheen(b, 176.0, 66.0, 150.0, 256.0, _c("#84aae4"), 0.42)
    # white pinstripe down the front edge, and the front molding
    _rect(b, 240, 0, 244, 256, _c("#e7ebf2"), 0.85)
    _rect(b, 244, 0, 256, 256, _c("#1a2030"), 1.0)
    _rect(b, 0, 246, 256, 256, _c("#0d1524"), 0.85)
    _commit(px, ox, oy, b, tile)


def ce_front(px, ox, oy, tile=TILE):
    """THE BLUE BASE.  Full-bleed royal blue; a ghosted pale-blue lunging
    fighter fills the upper two thirds (airbrushed, low contrast -- that is
    exactly how it reads in v3 4 and v4 8); a darker blue band across the
    bottom carries 'CAPCOM' in white caps with a warm red edge.  The coin
    treatment is a narrow dark service plate low LEFT, not a centred grey
    rectangle -- no coin door reads on the blue base in any frame.

    INTEGRATOR: ar2 builds this base as a solid `a2capc` box whose front face
    sits ~0.015 ft PROUD of the cabinet's printed front quad, so this panel
    is currently hidden.  See `FRONT_RECT` -- pull the box front back to
    D - 0.10 - SD and this becomes the visible face, with the box reading as
    the blue surround the photograph shows round it."""
    slug = "street-fighter-2-champion-edition"
    xs = _xs(slug, "front")
    b = _buf(_CE_BLUE)
    _field(b, lambda x, y, c: _mix(_c("#3f74c8"), _c("#1d4894"),
                                   min(1.0, abs(x - 96) / 300.0
                                       + (y / 255.0) * 0.55)))
    # the ghosted fighter: a lunging figure, pale on blue, very low contrast
    PALE = _c("#a8c8ef")
    _poly(b, [(96, 52), (126, 44), (140, 62), (132, 86), (104, 92), (88, 74)],
          PALE, 0.20)                                       # head / hair mass
    _poly(b, [(70, 88), (150, 78), (172, 116), (150, 158), (96, 166),
              (62, 132)], PALE, 0.16)                       # torso
    _poly(b, [(150, 96), (222, 74), (236, 96), (168, 126)], PALE, 0.19)
    _poly(b, [(214, 66), (244, 62), (250, 96), (222, 100)], PALE, 0.22)
    _poly(b, [(96, 158), (150, 152), (168, 196), (120, 206), (86, 186)],
          PALE, 0.15)                                       # forward thigh
    _poly(b, [(56, 128), (96, 150), (78, 196), (40, 176)], PALE, 0.13)
    for (dx, dy, al) in ((-7, -5, 0.11), (8, 6, 0.10), (0, 10, 0.08)):
        _poly(b, [(70 + dx, 88 + dy), (150 + dx, 78 + dy),
                  (172 + dx, 116 + dy), (150 + dx, 158 + dy),
                  (96 + dx, 166 + dy), (62 + dx, 132 + dy)], PALE, al)
        _poly(b, [(150 + dx, 96 + dy), (222 + dx, 74 + dy),
                  (236 + dx, 96 + dy), (168 + dx, 126 + dy)], PALE, al)
    for (x0, y0, x1, y1, al) in ((104, 58, 130, 64, 0.24),
                                 (76, 100, 140, 108, 0.16),
                                 (162, 84, 224, 92, 0.19),
                                 (108, 166, 152, 174, 0.14)):
        _rect(b, x0, y0, x1, y1, _c("#d8e6fa"), al)
    for (cx, cy, rx, ry, al) in ((104, 92, 34, 26, 0.13),
                                 (128, 124, 62, 44, 0.10),
                                 (188, 96, 40, 24, 0.12),
                                 (232, 82, 22, 18, 0.14),
                                 (124, 178, 46, 30, 0.10),
                                 (66, 156, 32, 30, 0.09),
                                 (150, 116, 74, 52, 0.07)):
        _disc(b, cx, cy, rx, ry, PALE, al)
    _sheen(b, 128.0, 120.0, 20.0, 210.0, _c("#b9d2f2"), 0.18)
    # the darker lower band with CAPCOM
    _rect(b, 0, 206, 256, 256, _c("#204c9c"), 1.0)
    _rect(b, 0, 204, 256, 208, _c("#12336e"), 0.85)
    _text(b, "CAPCOM", 128, 240, 26.0, _c("#7a1c14"), weight=0.34, xs=xs,
          wide=0.98, track=0.14, align="c")
    _text(b, "CAPCOM", 128, 238, 26.0, _c("#f6f8fc"), weight=0.20, xs=xs,
          wide=0.98, track=0.14, align="c")
    # the service plate, low LEFT -- narrow, dark, two slots, no cup
    _plate(b, 16, 164, 54, 200, _c("#1a2438"), _c("#5d6a80"), depth=2.0)
    _rect(b, 22, 172, 48, 176, _c("#0a0d14"), 1.0)
    _rect(b, 22, 184, 48, 188, _c("#0a0d14"), 1.0)
    _commit(px, ox, oy, b, tile)


def ce_deck(px, ox, oy, tile=TILE):
    """Black deck with a bright SILVER/STEEL bezel band along its leading
    edge -- a hard metallic line in both v3 4 and v4 8 and the single most
    identifying thing about this control panel.  A navy printed field, two
    white instruction blocks at the back corners, and a red centre keyline.
    Tile TOP = deck BACK, tile BOTTOM = the player's edge."""
    slug = "street-fighter-2-champion-edition"
    xs = _xs(slug, "deck")
    b = _buf("#1e2740")
    _field(b, lambda x, y, c: _mix(_c("#2b3757"), _c("#131a2c"),
                                   (y / 255.0) ** 0.7))
    _rect(b, 0, 0, 256, 18, _c("#080a12"), 1.0)
    # per-player instruction blocks, back corners
    for sx in (48.0, 208.0):
        _rrect(b, sx - 40, 30, sx + 40, 74, 4.0, _c("#dfe4ee"), 0.95)
        for k in range(4):
            _rect(b, sx - 33, 38 + k * 9, sx + 33 - k * 9, 42 + k * 9,
                  _c("#3d5590"), 0.85)
    # a red keyline down the centre split
    _rect(b, 126, 20, 130, 214, _c("#8f1c22"), 0.75)
    # the steel bezel band along the leading edge
    _rect(b, 0, 206, 256, 214, _c("#0a0c14"), 1.0)
    _rect(b, 0, 214, 256, 242,
          _vgrad(214, 242, [(0.0, "#eef1f6"), (0.35, "#b8bfcb"),
                            (0.6, "#7d8492"), (1.0, "#d5dae2")]), 1.0)
    _rect(b, 0, 242, 256, 256, _c("#12161f"), 1.0)
    _commit(px, ox, oy, b, tile)


def ce_screen(px, ox, oy, tile=TILE):
    """Nearly dark.  v4 5 and v4 8 show a dim stage with a pale instruction
    card burning along the BOTTOM edge -- the yellow strip is the only bright
    thing on this glass and it is not an attract loop."""
    b = _buf("#0b0d13")
    _field(b, lambda x, y, c: _mix(_c("#141924"), _c("#05070b"),
                                   min(1.0, (y / 200.0) ** 0.8)))
    # a dim stage silhouette: a horizon band and two figure masses
    _rect(b, 0, 128, 256, 132, _c("#2a3140"), 0.6)
    _poly(b, [(58, 96), (86, 88), (98, 130), (62, 134)], _c("#1e2836"), 0.9)
    _poly(b, [(160, 92), (190, 100), (188, 134), (154, 130)],
          _c("#22202c"), 0.9)
    _rect(b, 0, 40, 256, 46, _c("#1b2130"), 0.5)
    # the pale yellow instruction card along the bottom edge
    _rect(b, 6, 224, 250, 244, _c("#c9b055"), 0.85)
    _rect(b, 6, 224, 250, 229, _c("#e6d69a"), 0.7)
    for k in range(9):
        _rect(b, 16 + k * 26, 232, 32 + k * 26, 238, _c("#3a3416"), 0.6)
    for y in range(0, 256, 4):
        _rect(b, 0, y, 256, y + 1, _c("#000000"), 0.15)
    _commit(px, ox, oy, b, tile)


# =========================================================================
#  TIME CRISIS (Namco)     SOUTH_RUN[2] -- x 7.55, the tallest and narrowest
#
#  The only RED machine of the four and the only one with a printed coin door
#  worth the name.  Photograph: cream/gold head shroud (marquee band, then a
#  deep maroon band, then a tan speaker panel with TWO round black holes),
#  a red body with gold/tan trim down the front edge, a red-orange control
#  deck carrying a light gun and two pale instruction panels, and a lower
#  front of black flanked by two RED pillars with a big recessed coin door
#  between them.
#  Evidence: v3 4 (820,540)-(930,900) at 5x -> art/g2r5/tc_whole.png;
#  v4 5 (150,120)-(320,300) at 7x -> art/g2r5/v45_t2ce.png (coin door and
#  return cup); v4 8 -> art/g2r5/v48_south.png.
# =========================================================================
_TC_RED = "#9a3a30"
_TC_GOLD = "#c9a94e"


def tc_marquee(px, ox, oy, tile=TILE):
    """Pale gold / cream ground.  'TIME' small on the upper line with a
    swash, 'CRISIS' large across the full width beneath it, both raked right,
    blue italic block caps with a heavy white outline and a drop shadow."""
    slug = "time-crisis"
    xs = _xs(slug, "marquee")
    b = _buf("#d8bc63")
    _field(b, lambda x, y, c: _mix(_c("#eddb9a"), _c("#b7963c"),
                                   min(1.0, (y / 255.0) * 0.75
                                       + abs(x - 108) / 420.0)))
    _sheen(b, 100.0, 96.0, 0.0, 256.0, _c("#fbf1cb"), 0.45)
    # TIME, upper line, small, with its swash
    _text(b, "TIME", 82, 96, 56.0, _c("#20305e"), weight=0.34, xs=xs,
          wide=1.45, track=0.06, ital=0.30, align="c")
    _text(b, "TIME", 82, 94, 56.0, _c("#f4f7fc"), weight=0.20, xs=xs,
          wide=1.45, track=0.06, ital=0.30, align="c")
    _text(b, "TIME", 82, 94, 56.0, _c("#3f6ac4"), weight=0.10, xs=xs,
          wide=1.45, track=0.06, ital=0.30, align="c")
    _seg(b, 132, 58, 186, 46, 4.0, _c("#f4f7fc"), 0.9, kx=1.0)
    _seg(b, 136, 64, 182, 54, 3.0, _c("#3f6ac4"), 0.9, kx=1.0)
    # CRISIS, large, full width
    _text(b, "CRISIS", 128, 216, 104.0, _c("#1a2750"), weight=0.30, xs=xs,
          wide=1.52, track=0.05, ital=0.26, align="c")
    _text(b, "CRISIS", 128, 212, 104.0, _c("#f6f9ff"), weight=0.20, xs=xs,
          wide=1.52, track=0.05, ital=0.26, align="c")
    _text(b, "CRISIS", 128, 212, 104.0, _c("#3560bd"), weight=0.105, xs=xs,
          wide=1.52, track=0.05, ital=0.26, align="c")
    # the maroon band the head carries directly under the lit panel
    _rect(b, 0, 246, 256, 256, _c("#5d2a2c"), 1.0)
    _rect(b, 0, 0, 256, 5, _c("#8e7433"), 0.8)
    _commit(px, ox, oy, b, tile)


def tc_side(px, ox, oy, tile=TILE):
    """RED flank, full bleed, with the TAN/GOLD trim band running the whole
    FRONT edge (tile right) and along the top -- the trim is what makes this
    machine read from across the room.  A darker maroon kick at the floor
    and a soft airbrushed highlight down the belly.  No figurative art
    resolves at any magnification, so none is drawn."""
    b = _buf(_TC_RED)
    _field(b, lambda x, y, c: _mix(_c("#b04a3a"), _c("#61231f"),
                                   min(1.0, abs(x - 168) / 250.0
                                       + (y / 255.0) * 0.5)))
    _sheen(b, 168.0, 78.0, 0.0, 256.0, _c("#cf6a52"), 0.45)
    # the cream head shroud wraps onto the top of the flank
    _poly(b, [(112, 0), (256, 0), (256, 44), (150, 40), (112, 22)],
          _c("#c6a54e"), 1.0)
    _poly(b, [(112, 22), (150, 40), (256, 44), (256, 62), (140, 58)],
          _c("#6a2b2d"), 1.0)
    # tan/gold trim: the whole front edge plus a top run
    _rect(b, 238, 0, 250, 256, _c(_TC_GOLD), 1.0)
    _rect(b, 250, 0, 256, 256, _c("#8c7233"), 1.0)
    _rect(b, 234, 0, 238, 256, _c("#4a1a18"), 0.8)
    # the deck break and the maroon kick
    _rect(b, 120, 150, 238, 155, _c("#4a1a18"), 0.7)
    _rect(b, 0, 240, 238, 256, _c("#571d1c"), 0.9)
    _commit(px, ox, oy, b, tile)


def tc_front(px, ox, oy, tile=TILE):
    """Black centre field between TWO FULL-HEIGHT RED PILLARS, the small
    white-and-blue 'TIME CRISIS' logo at about 65% height, and beneath it the
    biggest coin door on this wall: a steel plate recessed in black, two coin
    slots, a chrome bar and a RETURN CUP at the bottom -- all clearly
    resolved in v4 5.  Nothing about this panel is shared with T2 beside
    it."""
    slug = "time-crisis"
    xs = _xs(slug, "front")
    b = _buf("#141116")
    _field(b, lambda x, y, c: _mix(_c("#1d1920"), _c("#0a080c"),
                                   (y / 255.0) ** 0.6))
    # the two red pillars, full height, edge to edge
    for (x0, x1) in ((0, 46), (210, 256)):
        _rect(b, x0, 0, x1, 256, _c(_TC_RED), 1.0)
        _rect(b, x0, 0, x1, 256, _hgrad(x0, x1, [(0.0, "#b8503c"),
                                                 (0.55, "#8d3128"),
                                                 (1.0, "#5f221e")]), 1.0)
    _rect(b, 46, 0, 50, 256, _c("#3d1512"), 0.9)
    _rect(b, 206, 0, 210, 256, _c("#3d1512"), 0.9)
    # gold hairline where the pillars meet the black
    _rect(b, 44, 0, 46, 256, _c(_TC_GOLD), 0.55)
    _rect(b, 210, 0, 212, 256, _c(_TC_GOLD), 0.55)
    # the small logo, upper-centre of the black field
    _text(b, "TIME", 128, 64, 30.0, _c("#101a34"), weight=0.34, xs=xs,
          wide=1.0, track=0.06, ital=0.28, align="c")
    _text(b, "TIME", 128, 63, 30.0, _c("#eef3fb"), weight=0.20, xs=xs,
          wide=1.0, track=0.06, ital=0.28, align="c")
    _text(b, "CRISIS", 128, 96, 34.0, _c("#101a34"), weight=0.34, xs=xs,
          wide=1.0, track=0.05, ital=0.26, align="c")
    _text(b, "CRISIS", 128, 94, 34.0, _c("#eef3fb"), weight=0.20, xs=xs,
          wide=1.0, track=0.05, ital=0.26, align="c")
    _text(b, "CRISIS", 128, 94, 34.0, _c("#3f6ac4"), weight=0.10, xs=xs,
          wide=1.0, track=0.05, ital=0.26, align="c")
    _seg(b, 150, 46, 178, 40, 3.0, _c("#e8c24e"), 0.9, kx=1.0)
    # THE COIN DOOR -- big, centred, low, steel in a black recess
    _plate(b, 76, 134, 180, 216,
           _vgrad(134, 216, [(0.0, "#c9ced6"), (0.4, "#9aa1ac"),
                             (0.72, "#6f7681"), (1.0, "#aeb5c0")]),
           _c("#e6eaf0"), depth=5.0)
    _rect(b, 84, 144, 128, 152, _c("#0a0a0e"), 1.0)     # left coin slot
    _rect(b, 130, 144, 174, 152, _c("#0a0a0e"), 1.0)    # right coin slot
    _rect(b, 84, 154, 128, 158, _c("#dfe4ea"), 0.7)
    _rect(b, 130, 154, 174, 158, _c("#dfe4ea"), 0.7)
    _rect(b, 88, 168, 170, 176, _c("#2a2e36"), 0.9)     # the chrome bar seat
    _rect(b, 88, 166, 170, 170, _c("#eef1f6"), 0.95)
    _rrect(b, 104, 188, 154, 210, 5.0, _c("#07070a"), 1.0)   # return cup
    _rect(b, 104, 188, 154, 193, _c("#8f96a2"), 0.8)
    # the pale coin plate the roster records at bottom centre
    _rect(b, 96, 226, 162, 240, _c("#c8ccd4"), 0.9)
    _rect(b, 96, 226, 162, 229, _c("#f0f3f8"), 0.8)
    _commit(px, ox, oy, b, tile)


def tc_deck(px, ox, oy, tile=TILE):
    """RED-ORANGE deck -- nothing else on this wall is warm.  A dark maroon
    gun island left of centre, a blue holster socket right of centre, and
    TWO pale blue-and-white printed instruction panels either side, exactly
    as v3 4 resolves them.  No joystick and no button field: this machine is
    played with a gun and a foot pedal.
    Tile TOP = deck BACK, tile BOTTOM = the player's edge."""
    slug = "time-crisis"
    xs = _xs(slug, "deck")
    b = _buf("#a8442f")
    _field(b, lambda x, y, c: _mix(_c("#c9583a"), _c("#75291f"),
                                   min(1.0, (y / 255.0) * 0.85
                                       + abs(x - 128) / 520.0)))
    _rect(b, 0, 0, 256, 16, _c("#57201a"), 1.0)
    # two pale instruction panels, back left and back right
    for (sx, tint) in ((44.0, "#dfe8f4"), (212.0, "#dfe8f4")):
        _rrect(b, sx - 40, 26, sx + 40, 92, 4.0, _c(tint), 0.96)
        _rect(b, sx - 40, 26, sx + 40, 34, _c("#3a63b4"), 0.9)
        for k in range(5):
            _rect(b, sx - 33, 42 + k * 10, sx + 26 - k * 7, 47 + k * 10,
                  _c("#41597f"), 0.75)
        _disc(b, sx + 26, 78, 9, 9, _c("#c33a2c"), 0.85)
    # the dark maroon gun island, left of centre
    _rrect(b, 62, 110, 168, 190, 12.0, _c("#4d1b16"), 1.0)
    _rrect(b, 70, 116, 160, 182, 10.0, _c("#65241c"), 1.0)
    _seg(b, 78, 150, 152, 138, 9.0, _c("#37110e"), 0.8, kx=1.0)
    # the blue holster socket, right of centre
    _rrect(b, 178, 122, 236, 186, 10.0, _c("#1d2a52"), 1.0)
    _ring(b, 207, 154, 21, 21, 5.0, _c("#3f6ac4"), 0.9)
    _disc(b, 207, 154, 11, 11, _c("#0b0d16"), 1.0)
    # gold edge trim wrapping onto the deck, and the player lip
    _rect(b, 0, 200, 256, 208, _c(_TC_GOLD), 0.9)
    _rect(b, 0, 208, 256, 232, _c("#8c3226"), 1.0)
    _text(b, "TIME CRISIS", 128, 228, 16.0, _c("#efd9a0"), weight=0.20,
          xs=xs, wide=1.0, track=0.20, ital=0.22, align="c", a=0.9)
    _rect(b, 0, 232, 256, 256, _c("#4d1b16"), 1.0)
    _commit(px, ox, oy, b, tile)


def tc_screen(px, ox, oy, tile=TILE):
    """v3 4 is the only frame that resolves this glass and it shows a DIM
    OLIVE-GREEN scene -- a dark game image, not a bright attract loop.  Kept
    dim: mean sits near 40, which is what the crop meters."""
    b = _buf("#141a10")
    _field(b, lambda x, y, c: _mix(_c("#2b3a1e"), _c("#080b06"),
                                   min(1.0, math.hypot((x - 118) / 150.0,
                                                       (y - 120) / 140.0))))
    # a soft olive mass, the shape the crop shows centred on the glass
    _disc(b, 118, 118, 78, 66, _c("#41562a"), 0.55)
    _disc(b, 104, 108, 44, 38, _c("#546b34"), 0.45)
    _poly(b, [(60, 168), (196, 156), (206, 208), (52, 214)],
          _c("#22301a"), 0.7)
    _rect(b, 0, 16, 256, 22, _c("#5a6b3a"), 0.30)
    for y in range(0, 256, 4):
        _rect(b, 0, y, 256, y + 1, _c("#000000"), 0.17)
    _rect(b, 0, 0, 256, 8, _c("#000000"), 0.85)
    _commit(px, ox, oy, b, tile)


# =========================================================================
#  TERMINATOR 2: JUDGMENT DAY     SOUTH_RUN[3] -- x 10.05, the easternmost
#
#  The MARQUEE IS ROUND 4'S, UNCHANGED -- it reads cleanly in
#  shots/r4_mq_south.png and the brief says keep it.  Everything below it is
#  redrawn: round 4 gave this machine a black field with a floated wordmark,
#  a full-tile fbm noise ground (expensive and invisible) and the same
#  centred grey coin rectangle as its neighbours.
#  Evidence: v4 8 (348,110)-(410,230) at 10x, v4 5 (150,120)-(320,300) at 7x
#  -> art/g2r5/v45_t2ce.png: the white T2, the maroon T-molding down both
#  front edges, the strip of small coloured plates along the bottom of the
#  front panel, and the BLUE gun left / RED gun right on the deck.
# =========================================================================


def t2_side(px, ox, oy, tile=TILE):
    """Gunmetal flank -- black at value but STRUCTURED, which is what the
    photograph's 'white/silver line work' actually is: three long chrome
    slashes raking back from the front edge, a machined horizontal banding,
    the chrome 'T2' low and forward, and the dark red-maroon T-molding down
    the whole front edge.  Full bleed, floor to top.  Round 4 painted this
    as an fbm noise field with two hairlines and it read as a black slab."""
    b = _buf("#191722")
    _field(b, lambda x, y, c: _mix(_c("#262433"), _c("#0c0b13"),
                                   min(1.0, abs(x - 200) / 260.0
                                       + abs(y - 110) / 300.0)))
    # machined horizontal banding -- cheap, and it kills the slab
    for k in range(11):
        y = 8.0 + k * 23.0
        _rect(b, 0, y, 250, y + 1.6, _c("#33313f"), 0.30)
        _rect(b, 0, y + 1.6, 250, y + 2.6, _c("#0a0910"), 0.30)
    # three long chrome slashes raking back off the front edge
    CH = _vgrad(0, 256, [(0.0, "#e8ebf1"), (0.35, "#9aa0ac"),
                         (0.6, "#4d525c"), (1.0, "#c3c8d1")])
    _poly(b, [(238, 26), (86, 74), (78, 92), (238, 46)], CH, 0.85)
    _poly(b, [(238, 120), (44, 172), (40, 188), (238, 142)], CH, 0.70)
    _poly(b, [(238, 196), (110, 228), (108, 240), (238, 214)], CH, 0.55)
    _seg(b, 236, 62, 100, 108, 1.6, _c("#7c828e"), 0.45, kx=1.0)
    _seg(b, 236, 162, 66, 208, 1.6, _c("#7c828e"), 0.35, kx=1.0)
    # the chrome T2, low and forward (tile right = cabinet front)
    _text(b, "T2", 196, 226, 34.0, _c("#07060b"), weight=0.34,
          xs=_xs("terminator-2", "side"), wide=0.72, track=0.10, align="c")
    _text(b, "T2", 196, 224, 34.0, CH, weight=0.20,
          xs=_xs("terminator-2", "side"), wide=0.72, track=0.10, align="c")
    # maroon T-molding on the front edge
    _rect(b, 242, 0, 256, 256, _c("#5f1720"), 1.0)
    _rect(b, 250, 0, 256, 256, _c("#3a0e15"), 0.9)
    _rect(b, 239, 0, 242, 256, _c("#0a0910"), 0.9)
    _commit(px, ox, oy, b, tile)


def t2_front(px, ox, oy, tile=TILE):
    """Matte black, full bleed, with the huge chrome 'T2' left of centre --
    the identity of this machine and the one thing legible on it at 10x --
    maroon T-molding stripes down BOTH edges, a faint blast-scorch behind the
    wordmark, the row of small coloured licence plates along the bottom that
    v4 5 resolves, and a SMALL DARK coin plate low right.  Time Crisis
    beside it has a big steel door dead centre with a return cup; this one is
    deliberately the opposite -- small, offset, and nearly black."""
    slug = "terminator-2"
    xs = _xs(slug, "front")
    b = _buf("#17141c")
    _field(b, lambda x, y, c: _mix(_c("#221e29"), _c("#0a080d"),
                                   min(1.0, math.hypot((x - 104) / 210.0,
                                                       (y - 130) / 220.0))))
    # a faint scorch/blast halo behind the wordmark -- structure, not noise
    for k in range(7):
        _ring(b, 104, 132, 54 + k * 13, 40 + k * 10, 2.0, _c("#332c3c"),
              0.20 - 0.02 * k, n=30)
    CH = _vgrad(84, 176, [(0.0, "#ffffff"), (0.28, "#d3d7de"),
                          (0.52, "#787f8b"), (0.62, "#aeb4bf"),
                          (1.0, "#e9ecf1")])
    _text(b, "T2", 104, 176, 92.0, _c("#07060a"), weight=0.32, xs=xs,
          wide=1.85, track=0.06, align="c")
    _text(b, "T2", 104, 174, 92.0, CH, weight=0.215, xs=xs, wide=1.85,
          track=0.06, align="c")
    # maroon T-molding down BOTH edges of the printed panel
    for (x0, x1) in ((0, 11), (245, 256)):
        _rect(b, x0, 0, x1, 256, _c("#5f1720"), 1.0)
    _rect(b, 11, 0, 14, 256, _c("#0a0910"), 0.8)
    _rect(b, 242, 0, 245, 256, _c("#0a0910"), 0.8)
    # the strip of small coloured licence plates along the bottom (v4 5)
    cols = ["#b8452f", "#d8d2c4", "#3c5f9c", "#c9a94e", "#8f9aa8",
            "#7a2f52", "#cfd4dc", "#2f6b58"]
    x = 22.0
    for k in range(8):
        w = 18.0 + 7.0 * _h2(k, 5, 11)
        _rect(b, x, 218, x + w, 234, _c(cols[k]), 0.9)
        _rect(b, x, 218, x + w, 221, _c("#f0f2f6"), 0.35)
        _rect(b, x + 2, 224, x + w - 2, 227, _c("#141118"), 0.45)
        x += w + 5.0
    # the small dark coin plate, LOW RIGHT and nearly black
    _plate(b, 168, 186, 232, 212, _c("#22222a"), _c("#767c88"), depth=2.5)
    _rect(b, 176, 192, 224, 196, _c("#08080b"), 1.0)
    _rect(b, 176, 200, 200, 206, _c("#4b505a"), 0.8)
    _commit(px, ox, oy, b, tile)


def t2_deck(px, ox, oy, tile=TILE):
    """Black, angled, projecting.  TWO LIGHT GUNS -- no joystick and no
    button field.  BLUE gun on the left half, RED gun on the right, both in
    chrome-collared cradles, exactly as v3 4 at 16x and v4 8 at 14x resolve
    them.  A maroon pinstripe along the player edge and two start buttons
    at the back.  Kept from round 4 in composition; the cradles, the chrome
    collars and the machined ground are new."""
    slug = "terminator-2"
    xs = _xs(slug, "deck")
    b = _buf("#201d2b")
    _field(b, lambda x, y, c: _mix(_c("#302c3f"), _c("#131019"),
                                   (y / 255.0) ** 0.75))
    for k in range(9):
        y = 20.0 + k * 24.0
        _rect(b, 0, y, 256, y + 1.4, _c("#312e3d"), 0.28)
    _rect(b, 0, 0, 256, 16, _c("#0a0810"), 1.0)
    for (sx, col, lab) in ((64.0, "#2f5fd0", "1"), (192.0, "#cf2424", "2")):
        _rrect(b, sx - 46, 88, sx + 46, 188, 12.0, _c("#0c0a12"), 1.0)
        _rrect(b, sx - 40, 94, sx + 40, 182, 10.0, _c("#181521"), 1.0)
        _ring(b, sx, 138, 34.0, 34.0, 6.0,
              _vgrad(104, 172, [(0.0, "#dfe3ea"), (0.5, "#6a7080"),
                                (1.0, "#c2c7d0")]), 0.95)
        _ring(b, sx, 138, 27.0, 27.0, 5.0, _c(col), 0.9)
        _ring(b, sx, 138, 17.0, 17.0, 3.0, _c(col), 0.45)
        _disc(b, sx, 138, 11.0, 11.0, _c("#08070c"), 1.0)
        _text(b, lab, sx, 44, 20.0, _c(col), weight=0.24, xs=xs, align="c")
    _rect(b, 0, 206, 256, 214, _c("#5f1720"), 1.0)
    _rect(b, 0, 214, 256, 218, _c("#8d2a33"), 0.6)
    _text(b, "JUDGMENT DAY", 128, 236, 17.0, _c("#7e838f"), weight=0.20,
          xs=xs, wide=1.0, track=0.22, align="c", a=0.85)
    _rect(b, 0, 246, 256, 256, _c("#0a0810"), 1.0)
    _commit(px, ox, oy, b, tile)


def t2_screen(px, ox, oy, tile=TILE):
    """DARK, and it stays dark: v4 5, v4 8 and v3 4 all show this glass
    black with only the room reflected in it.  Painted as reflection, not as
    an attract loop."""
    b = _buf("#14161f")
    _field(b, lambda x, y, c: _mix(_c("#1e2231"), _c("#0a0b11"),
                                   min(1.0, (y / 220.0) ** 0.7
                                       + abs(x - 70) / 420.0)))
    _sheen(b, 44.0, 44.0, 0.0, 256.0, _c("#39435c"), 0.6)
    _poly(b, [(150, 22), (250, 8), (250, 34), (150, 50)], _c("#2b3346"), 0.7)
    _poly(b, [(24, 176), (96, 168), (104, 214), (28, 222)], _c("#242b3c"),
          0.55)
    for y in range(0, 256, 4):
        _rect(b, 0, y, 256, y + 1, _c("#000000"), 0.18)
    _rect(b, 0, 0, 256, 8, _c("#000000"), 0.85)
    _rect(b, 0, 248, 256, 256, _c("#000000"), 0.85)
    _commit(px, ox, oy, b, tile)
