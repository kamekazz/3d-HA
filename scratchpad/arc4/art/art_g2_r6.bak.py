"""Round-5 cabinet artwork, agent G2 -- the ARCADE ROOM'S SOUTH RUN.

    SOUTH_RUN[0]  legends-ultimate                     Legends Ultimate
    SOUTH_RUN[1]  street-fighter-2-champion-edition    SFII: Champion Edition
    SOUTH_RUN[2]  time-crisis                          Time Crisis
    SOUTH_RUN[3]  terminator-2                         Terminator 2

WHAT CHANGED FROM ROUND 4, AND WHY
----------------------------------
Three independent critics rejected round 4 in the same words: "all three
cabinets are one asset recoloured -- the same flat-black front panel with the
SAME centred grey coin-door rectangle at the same size and position, and the
same two-joystick deck (one red top, one blue top) over the same row of flat
square buttons; only the trim colour and a small floated logo differ."  That
is verifiable in scratchpad/arc4/shots/r4_mq_south.png and it is correct.

Round 5 rebuilds everything below the marquee:

  * FULL-BLEED panels.  Every side / front / deck tile carries its own ground
    colour edge to edge -- Time Crisis is red with gold trim, Champion
    Edition royal blue, Legends Ultimate a black licence grid, T2 machined
    gunmetal.  No panel is a dark field with a logo floated on it.
  * THE COIN DOOR IS ARTWORK, and no two are alike: Time Crisis has a big
    steel plate dead centre with two slots, a chrome bar and a return cup;
    T2 a small nearly-black plate offset RIGHT; Champion Edition a narrow
    dark service plate low LEFT on the blue base; Legends Ultimate has NONE,
    because it is a home cabinet and no frame shows one.
  * CONTROL DECKS have their own printed graphic AND their own control
    layout.  The controls are geometry, so they are exported as `DECKS`
    for ar2.upright to consume -- see the contract above that table.  Counts
    and kinds: 2 ball-tops + 12 convex buttons + trackball + spinner /
    2 bat-tops + 14 buttons / 2 light guns + 3 buttons / 2 light guns +
    2 buttons.  Not one flat square button survives.
  * THE CRT IS NOT BLACK -- but neither is it an attract loop.  All four of
    these machines photograph DARK, so `.screen` paints dark glass with the
    room reflected in it, plus the one bright thing any frame shows: the pale
    yellow instruction card burning along the bottom of Champion Edition's
    monitor, and Time Crisis's dim olive game image.  Declared, and dark on
    purpose.

Terminator 2's MARQUEE is round 4's, untouched -- it reads cleanly in the
judged frame and the brief says keep it.  The other three marquees are new
here because those machines moved onto this agent's run this round; they are
drawn to the same roster descriptions round 4 worked from.

HOW THE INTEGRATOR USES THIS
----------------------------
`PANELS` maps "<slug>.<panel>" to `paint(px, ox, oy, tile)`, painting one
`tile` x `tile` square into a shared atlas.  `tile` should be `TILE` (256);
smaller works but the letterforms lose their edges, which is exactly why
atlas4 supersamples.

`DECKS`, `FRONT_RECT` and `COIN` (inside DECKS) are the geometry contract.
`LEGACY_PANELS` holds round 4's marvel-vs-capcom / nfl-blitz /
east-7-no-machine so that merging this module can never collide with whoever
owns those machines now.

THREE THINGS THAT ARE GEOMETRY, NOT ART:

1. ASPECT.  The tile is square and no panel it lands on is.  Round 4 used ONE
   aspect table for every machine; the south run's widths differ by 30%
   (Legends Ultimate 2.95 ft against T2's 2.28), so three of the four were
   pre-squeezed wrong.  `A` below is PER MACHINE, computed from each row of
   ar2.SOUTH_RUN.  If a cabinet is re-proportioned by more than ~15%, change
   `A` and re-run -- do not stretch the atlas.
2. ORIENTATION.  On the flank tile, sweep's uvof puts the cabinet FRONT at
   the tile's RIGHT edge and the cabinet TOP at the tile's TOP.  On the deck,
   front and marquee tiles, tile LEFT is local -x, which for a south-wall
   machine (rot 180) is the VIEWER'S LEFT; on the deck tile the tile TOP is
   the deck's BACK (screen end).  `flip` is off and must stay off.
3. MATERIALS.  `.side`, `.front` and `.marquee` are true albedo for ART
   (#ffffff).  `.deck` tiles are authored bright for ART_DK (#4c4c4c) -- an
   up-facing surface collects roughly twice what a vertical one does -- EXCEPT
   `time-crisis.deck`, whose red-orange ground needs the lighter ART_D
   (#c9c9c9) or it lands as brown mud.  a2kit.DECK_MAT already lists
   time-crisis as "D"; keep it.  `.screen` needs a DARK factor material,
   darker than ART_DK; #3a3a3a is about right.

THIS FILE IS GENERATED.  art_g2.py = _g2_splice.py applied to
art_g2_r4.bak.py (round 4, kept verbatim for its helper library and its three
legacy machines) + _g2_frag.py (round 5 machines) + _g2_export.py (PANELS,
DECKS, FRONT_RECT, EVIDENCE).  Edit the fragments and re-run
    $PY scratchpad/arc4/art/_g2_splice.py
then preview_g2r5.py / compare_g2r5.py / bytes_g2r5.py.  Editing art_g2.py by
hand is fine for the integrator -- just be aware a re-splice would drop it.

Pure stdlib.  The 4x4 ordered dither and round-to-8 quantisation are copied
from a2kit._paint and are what keeps the PNG small; atlas4 re-quantises to 16
levels after its box-average.  Full-tile fbm noise grounds were REMOVED this
round -- they cost bytes and are invisible under the dither at panel scale.
"""

import math

TILE = 256

# --- copied verbatim from a2kit so the two atlases quantise identically
_BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]

# ROUND 4's single aspect table.  Kept because the three legacy machines at
# the foot of this file were authored against it.  MY four machines use `A`.
ASPECT = {
    "marquee": 3.40,
    "side": 0.49,
    "front": 1.25,
    "deck": 2.35,
    "riser": 6.20,
}

# --------------------------------------------------------------- primitives
def _c(v):
    """hex string or triple -> float triple."""
    if isinstance(v, str):
        v = v.lstrip("#")
        return (float(int(v[0:2], 16)), float(int(v[2:4], 16)),
                float(int(v[4:6], 16)))
    return (float(v[0]), float(v[1]), float(v[2]))


def _mix(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t,
            a[2] + (b[2] - a[2]) * t)


def _buf(col="#000000"):
    r, g, b = _c(col)
    return [[[r, g, b] for _ in range(TILE)] for _ in range(TILE)]


def _q(v):
    v = int(round(v / 8.0)) * 8
    return 0 if v < 0 else (255 if v > 255 else v)


def _commit(px, ox, oy, buf, tile):
    """Bayer-dither, quantise to 8 levels, blit.  Rescales if tile != TILE."""
    for y in range(tile):
        sy = y if tile == TILE else min(TILE - 1, int(y * TILE / tile))
        row = buf[sy]
        brow = _BAYER[y & 3]
        out = px[oy + y]
        for x in range(tile):
            sx = x if tile == TILE else min(TILE - 1, int(x * TILE / tile))
            n = (brow[x & 3] - 7.5) * 0.90
            p = row[sx]
            out[ox + x] = (_q(p[0] + n), _q(p[1] + n), _q(p[2] + n))


def _blend(buf, x, y, col, a):
    if a <= 0.0 or x < 0 or y < 0 or x >= TILE or y >= TILE:
        return
    if a > 1.0:
        a = 1.0
    p = buf[y][x]
    p[0] += (col[0] - p[0]) * a
    p[1] += (col[1] - p[1]) * a
    p[2] += (col[2] - p[2]) * a


def _colat(col, x, y):
    return col(x, y) if callable(col) else col


def _field(buf, fn):
    """fn(x, y, cur) -> colour triple, over the whole tile."""
    for y in range(TILE):
        row = buf[y]
        for x in range(TILE):
            row[x] = list(fn(x, y, row[x]))


def _rect(buf, x0, y0, x1, y1, col, a=1.0):
    ix0, ix1 = int(math.floor(x0)), int(math.ceil(x1))
    iy0, iy1 = int(math.floor(y0)), int(math.ceil(y1))
    for y in range(max(0, iy0), min(TILE, iy1)):
        cy = min(y + 1.0, y1) - max(float(y), y0)
        if cy <= 0:
            continue
        for x in range(max(0, ix0), min(TILE, ix1)):
            cx = min(x + 1.0, x1) - max(float(x), x0)
            if cx > 0:
                _blend(buf, x, y, _colat(col, x, y), cx * cy * a)


def _poly(buf, pts, col, a=1.0, ss=3):
    """Scanline fill of a simple polygon, ss sub-rows of vertical AA."""
    ys = [p[1] for p in pts]
    y0 = max(0, int(math.floor(min(ys))))
    y1 = min(TILE - 1, int(math.ceil(max(ys))))
    n = len(pts)
    for yy in range(y0, y1 + 1):
        acc = {}
        for k in range(ss):
            sy = yy + (k + 0.5) / ss
            xs = []
            for i in range(n):
                ax, ay = pts[i]
                bx, by = pts[(i + 1) % n]
                if (ay <= sy < by) or (by <= sy < ay):
                    xs.append(ax + (bx - ax) * (sy - ay) / (by - ay))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                xa, xb = xs[i], xs[i + 1]
                if xb <= 0.0 or xa >= float(TILE):
                    continue
                xa = max(xa, 0.0)
                xb = min(xb, float(TILE))
                for xx in range(int(xa), min(int(math.ceil(xb)), TILE)):
                    c = min(xx + 1.0, xb) - max(float(xx), xa)
                    if c > 0:
                        acc[xx] = acc.get(xx, 0.0) + c / ss
        for xx, cv in acc.items():
            _blend(buf, xx, yy, _colat(col, xx, yy), cv * a)


def _seg(buf, ax, ay, bx, by, w, col, a=1.0, kx=1.0):
    """Capsule of half-width w/2, measured with x divided by kx.

    kx < 1 makes the stroke narrower in x than in y, which is exactly the
    pre-squeeze a wide panel needs: on the panel the stroke comes out round.
    """
    hw = w * 0.5
    ex, ey = hw * kx + 1.0, hw + 1.0
    x0 = max(0, int(min(ax, bx) - ex))
    x1 = min(TILE - 1, int(max(ax, bx) + ex) + 1)
    y0 = max(0, int(min(ay, by) - ey))
    y1 = min(TILE - 1, int(max(ay, by) + ey) + 1)
    nax, nbx = ax / kx, bx / kx
    dx, dy = nbx - nax, by - ay
    dd = dx * dx + dy * dy
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            px_, py_ = (x + 0.5) / kx, y + 0.5
            if dd <= 1e-9:
                t = 0.0
            else:
                t = ((px_ - nax) * dx + (py_ - ay) * dy) / dd
                t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
            qx, qy = nax + dx * t, ay + dy * t
            d = math.hypot(px_ - qx, py_ - qy)
            cov = hw - d + 0.5
            if cov > 0.0:
                _blend(buf, x, y, _colat(col, x, y), min(1.0, cov) * a)


def _pline(buf, pts, w, col, a=1.0, kx=1.0, closed=False):
    n = len(pts)
    m = n if closed else n - 1
    for i in range(m):
        ax, ay = pts[i]
        bx, by = pts[(i + 1) % n]
        _seg(buf, ax, ay, bx, by, w, col, a, kx)


def _disc(buf, cx, cy, rx, ry, col, a=1.0):
    x0 = max(0, int(cx - rx - 1))
    x1 = min(TILE - 1, int(cx + rx + 1))
    y0 = max(0, int(cy - ry - 1))
    y1 = min(TILE - 1, int(cy + ry + 1))
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            d = math.hypot((x + 0.5 - cx) / max(1e-6, rx),
                           (y + 0.5 - cy) / max(1e-6, ry))
            cov = (1.0 - d) * min(rx, ry) + 0.5
            if cov > 0.0:
                _blend(buf, x, y, _colat(col, x, y), min(1.0, cov) * a)


def _ring(buf, cx, cy, rx, ry, w, col, a=1.0, n=44):
    pts = [(cx + rx * math.cos(i * 2.0 * math.pi / n),
            cy + ry * math.sin(i * 2.0 * math.pi / n)) for i in range(n)]
    _pline(buf, pts, w, col, a, kx=max(0.08, rx / max(1e-6, ry)), closed=True)


def _rrect(buf, x0, y0, x1, y1, r, col, a=1.0):
    """Rounded rectangle, filled."""
    _rect(buf, x0 + r, y0, x1 - r, y1, col, a)
    _rect(buf, x0, y0 + r, x0 + r, y1 - r, col, a)
    _rect(buf, x1 - r, y0 + r, x1, y1 - r, col, a)
    for (cx, cy) in ((x0 + r, y0 + r), (x1 - r, y0 + r),
                     (x0 + r, y1 - r), (x1 - r, y1 - r)):
        _disc(buf, cx, cy, r, r, col, a)


# ------------------------------------------------------------------- noise
def _h2(x, y, s):
    n = (x * 1836311903) ^ (y * 2971215073) ^ (s * 374761393)
    n = (n ^ (n >> 13)) & 0x7FFFFFFF
    n = (n * 1274126177) & 0x7FFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0


def _vnoise(x, y, s):
    xi, yi = int(math.floor(x)), int(math.floor(y))
    fx, fy = x - xi, y - yi
    fx = fx * fx * (3.0 - 2.0 * fx)
    fy = fy * fy * (3.0 - 2.0 * fy)
    a = _h2(xi, yi, s)
    b = _h2(xi + 1, yi, s)
    c = _h2(xi, yi + 1, s)
    d = _h2(xi + 1, yi + 1, s)
    return (a + (b - a) * fx) * (1.0 - fy) + (c + (d - c) * fx) * fy


def _fbm(x, y, s, oct_=3):
    v, amp, f = 0.0, 0.5, 1.0
    for i in range(oct_):
        v += amp * _vnoise(x * f, y * f, s + i * 37)
        amp *= 0.5
        f *= 2.0
    return v


def _grain(buf, amp, seed, step=1):
    """Fine print grain.  MEASURED AND REMOVED: calling this on all 17 panels
    cost 387 KB of PNG on top of 184 KB without it (2.1x the whole atlas) and
    it is invisible under the Bayer dither, which already modulates every
    pixel by +/-6.75 at a 4 px period.  Kept only so the finding is on the
    record -- do not re-enable it without re-weighing the atlas."""
    for y in range(0, TILE, step):
        for x in range(0, TILE, step):
            n = (_h2(x, y, seed) - 0.5) * 2.0 * amp
            p = buf[y][x]
            p[0] += n
            p[1] += n
            p[2] += n


# ------------------------------------------------------- a stroke alphabet
# Unit box: x right in [0, advance], y UP in [0, 1] (1 = cap line).  Each
# glyph is a list of polylines.  Filled rectangles and diagonals only -- at
# 256 px that is enough for "NFL BLITZ" to read as NFL BLITZ.
_O = [[(0.33, 1.0), (0.56, 0.88), (0.64, 0.5), (0.56, 0.12), (0.33, 0.0),
       (0.10, 0.12), (0.02, 0.5), (0.10, 0.88), (0.33, 1.0)]]
_P = [[(0.03, 0.0), (0.03, 1.0)],
      [(0.03, 1.0), (0.40, 1.0), (0.58, 0.86), (0.58, 0.64), (0.40, 0.50),
       (0.03, 0.50)]]

_GLYPH = {
    " ": (0.34, []),
    "A": (0.66, [[(0.0, 0.0), (0.33, 1.0), (0.66, 0.0)],
                 [(0.13, 0.34), (0.53, 0.34)]]),
    "B": (0.62, [[(0.03, 0.0), (0.03, 1.0)],
                 [(0.03, 1.0), (0.40, 1.0), (0.56, 0.87), (0.56, 0.68),
                  (0.42, 0.55), (0.03, 0.55)],
                 [(0.03, 0.55), (0.45, 0.55), (0.62, 0.41), (0.62, 0.14),
                  (0.45, 0.0), (0.03, 0.0)]]),
    "C": (0.62, [[(0.60, 0.84), (0.45, 0.98), (0.22, 1.0), (0.07, 0.84),
                  (0.02, 0.5), (0.07, 0.16), (0.22, 0.0), (0.45, 0.02),
                  (0.60, 0.16)]]),
    "D": (0.64, [[(0.03, 0.0), (0.03, 1.0), (0.36, 1.0), (0.57, 0.84),
                  (0.63, 0.5), (0.57, 0.16), (0.36, 0.0), (0.03, 0.0)]]),
    "E": (0.58, [[(0.03, 0.0), (0.03, 1.0)], [(0.03, 1.0), (0.55, 1.0)],
                 [(0.03, 0.52), (0.45, 0.52)], [(0.03, 0.0), (0.57, 0.0)]]),
    "F": (0.56, [[(0.03, 0.0), (0.03, 1.0)], [(0.03, 1.0), (0.55, 1.0)],
                 [(0.03, 0.52), (0.44, 0.52)]]),
    "G": (0.66, [[(0.61, 0.84), (0.46, 0.98), (0.22, 1.0), (0.07, 0.84),
                  (0.02, 0.5), (0.07, 0.16), (0.24, 0.0), (0.48, 0.02),
                  (0.63, 0.16), (0.63, 0.42), (0.38, 0.42)]]),
    "H": (0.64, [[(0.03, 0.0), (0.03, 1.0)], [(0.61, 0.0), (0.61, 1.0)],
                 [(0.03, 0.52), (0.61, 0.52)]]),
    "I": (0.20, [[(0.10, 0.0), (0.10, 1.0)]]),
    "J": (0.56, [[(0.52, 1.0), (0.52, 0.22), (0.40, 0.03), (0.21, 0.0),
                  (0.05, 0.11), (0.01, 0.29)]]),
    "K": (0.62, [[(0.03, 0.0), (0.03, 1.0)], [(0.58, 1.0), (0.07, 0.46)],
                 [(0.24, 0.61), (0.62, 0.0)]]),
    "L": (0.54, [[(0.03, 1.0), (0.03, 0.0), (0.54, 0.0)]]),
    "M": (0.80, [[(0.03, 0.0), (0.03, 1.0), (0.40, 0.30), (0.77, 1.0),
                  (0.77, 0.0)]]),
    "N": (0.66, [[(0.03, 0.0), (0.03, 1.0), (0.63, 0.02), (0.63, 1.0)]]),
    "O": (0.66, _O),
    "P": (0.60, _P),
    "Q": (0.66, _O + [[(0.40, 0.20), (0.66, -0.08)]]),
    "R": (0.64, _P + [[(0.33, 0.50), (0.63, 0.0)]]),
    "S": (0.60, [[(0.57, 0.86), (0.42, 0.99), (0.18, 1.0), (0.04, 0.86),
                  (0.05, 0.66), (0.24, 0.58), (0.40, 0.52), (0.56, 0.42),
                  (0.57, 0.16), (0.42, 0.01), (0.16, 0.0), (0.02, 0.14)]]),
    "T": (0.60, [[(0.0, 1.0), (0.60, 1.0)], [(0.30, 1.0), (0.30, 0.0)]]),
    "U": (0.64, [[(0.03, 1.0), (0.03, 0.22), (0.16, 0.03), (0.33, 0.0),
                  (0.50, 0.03), (0.61, 0.22), (0.61, 1.0)]]),
    "V": (0.64, [[(0.0, 1.0), (0.32, 0.0), (0.64, 1.0)]]),
    "W": (0.92, [[(0.0, 1.0), (0.20, 0.0), (0.46, 0.62), (0.72, 0.0),
                  (0.92, 1.0)]]),
    "X": (0.62, [[(0.0, 1.0), (0.62, 0.0)], [(0.0, 0.0), (0.62, 1.0)]]),
    "Y": (0.62, [[(0.0, 1.0), (0.31, 0.52), (0.62, 1.0)],
                 [(0.31, 0.52), (0.31, 0.0)]]),
    "Z": (0.60, [[(0.02, 1.0), (0.58, 1.0), (0.02, 0.0), (0.58, 0.0)]]),
    # a squared "techno" 2: flat top bar, straight diagonal, flat foot --
    # this is the shape the T2 wordmark uses, read off v4 8
    "2": (0.62, [[(0.04, 0.76), (0.04, 1.0), (0.60, 1.0), (0.60, 0.62),
                  (0.05, 0.02), (0.62, 0.02)]]),
    "0": (0.62, _O),
    "1": (0.40, [[(0.02, 0.80), (0.20, 1.0), (0.20, 0.0)],
                 [(0.04, 0.0), (0.36, 0.0)]]),
    "3": (0.60, [[(0.04, 0.90), (0.24, 1.0), (0.48, 0.98), (0.58, 0.80),
                  (0.44, 0.56), (0.20, 0.54)],
                 [(0.44, 0.56), (0.60, 0.36), (0.52, 0.08), (0.26, 0.0),
                  (0.04, 0.10)]]),
    "4": (0.62, [[(0.44, 0.0), (0.44, 1.0), (0.02, 0.28), (0.62, 0.28)]]),
    "5": (0.60, [[(0.56, 1.0), (0.08, 1.0), (0.05, 0.58), (0.32, 0.62),
                  (0.55, 0.48), (0.56, 0.20), (0.34, 0.0), (0.08, 0.04)]]),
    "6": (0.62, [[(0.54, 0.92), (0.30, 1.0), (0.09, 0.80), (0.04, 0.40),
                  (0.14, 0.08), (0.38, 0.0), (0.58, 0.14), (0.60, 0.36),
                  (0.42, 0.50), (0.14, 0.46), (0.04, 0.36)]]),
    "7": (0.58, [[(0.02, 1.0), (0.58, 1.0), (0.24, 0.0)]]),
    "8": (0.62, [[(0.32, 0.54), (0.10, 0.66), (0.10, 0.88), (0.32, 1.0),
                  (0.54, 0.88), (0.54, 0.66), (0.32, 0.54), (0.06, 0.38),
                  (0.06, 0.12), (0.32, 0.0), (0.58, 0.12), (0.58, 0.38),
                  (0.32, 0.54)]]),
    "9": (0.62, [[(0.10, 0.08), (0.34, 0.0), (0.55, 0.20), (0.60, 0.60),
                  (0.50, 0.92), (0.26, 1.0), (0.06, 0.86), (0.04, 0.64),
                  (0.22, 0.50), (0.50, 0.54), (0.60, 0.64)]]),
    ".": (0.24, [[(0.10, 0.0), (0.11, 0.0)]]),
    "-": (0.46, [[(0.05, 0.48), (0.41, 0.48)]]),
    ":": (0.24, [[(0.10, 0.0), (0.11, 0.0)], [(0.10, 0.52), (0.11, 0.52)]]),
    "'": (0.20, [[(0.10, 1.0), (0.10, 0.78)]]),
    "/": (0.48, [[(0.02, 0.0), (0.46, 1.0)]]),
}


def _text_w(s, cap, xs, wide, track):
    kx = cap * xs * wide
    w = 0.0
    for ch in s.upper():
        gw = _GLYPH.get(ch, _GLYPH[" "])[0]
        w += gw * kx + track * cap * xs
    return w - track * cap * xs


def _text(buf, s, x, ybase, cap, col, weight=0.14, xs=1.0, wide=1.0,
          track=0.16, ital=0.0, align="l", a=1.0):
    """Draw uppercase `s` with its baseline at `ybase`.

    `xs` is the panel's horizontal pre-squeeze (1/ASPECT), `wide` the
    typeface's own width factor, `weight` the stroke width as a fraction of
    the cap height.  Strokes are measured with x divided by (xs*wide) so a
    squeezed glyph still has even-weight strokes on the panel.
    """
    kx = cap * xs * wide
    tot = _text_w(s, cap, xs, wide, track)
    if align == "c":
        x -= tot * 0.5
    elif align == "r":
        x -= tot
    w = max(1.0, weight * cap)
    pen = x
    for ch in s.upper():
        gw, strokes = _GLYPH.get(ch, _GLYPH[" "])
        for pl in strokes:
            pts = [(pen + gx * kx + gy * ital * cap * xs, ybase - gy * cap)
                   for (gx, gy) in pl]
            _pline(buf, pts, w, col, a, kx=max(0.10, xs * wide))
        pen += gw * kx + track * cap * xs
    return tot


def _vgrad(y0, y1, stops):
    """Colour callable: vertical ramp through (t, colour) stops."""
    st = [(t, _c(cc)) for (t, cc) in stops]

    def f(x, y):
        t = (y - y0) / max(1e-6, y1 - y0)
        t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
        for i in range(len(st) - 1):
            if t <= st[i + 1][0]:
                lo, hi = st[i], st[i + 1]
                u = (t - lo[0]) / max(1e-6, hi[0] - lo[0])
                return _mix(lo[1], hi[1], u)
        return st[-1][1]
    return f


# =======================================================================
#  ROUND 4 LEGACY -- machines that moved to other agents' runs in
#  round 5.  Exported as LEGACY_PANELS, not PANELS.  Unchanged.
# =======================================================================

# =========================================================================
#  MARVEL VS CAPCOM   -- EAST_RUN[2]
#  east run, second from the north end; the tallest cabinet, stepped head.
# =========================================================================
_MVC_XS = 1.0 / ASPECT["marquee"]


def mvc_marquee(px, ox, oy, tile=TILE):
    """A wide full-bleed character-battle illustration: warm reds and oranges
    driving in from the left, blues from the right, a white flash where they
    meet.  No type -- at 16x in v3 4 none separates from the art."""
    b = _buf("#120a2a")
    _field(b, lambda x, y, c: _mix(
        _c("#1a0e38"), _c("#0a1a52"), min(1.0, max(0.0, x / 255.0))))
    cx, cy = 132.0, 128.0
    # radiating wedge rays: warm on the left of the flash, cool on the right
    for i in range(26):
        a0 = i * (2.0 * math.pi / 26.0) + 0.09
        a1 = a0 + (2.0 * math.pi / 26.0) * 0.52
        warm = math.cos(a0) < 0.0
        col = ("#e0741c" if i % 2 else "#b81f28") if warm else \
              ("#1b46c0" if i % 2 else "#2b93d8")
        p = [(cx, cy)]
        for aa in (a0, a1):
            p.append((cx + 260.0 * math.cos(aa) * 0.34,
                      cy + 260.0 * math.sin(aa)))
        _poly(b, p, _c(col), 0.55)
    # Two half-length figures charging the centre.  Everything below is
    # authored in PANEL pixels and squeezed by S on the way in, so a head
    # drawn round here comes out round on the cabinet and not as the wide
    # ovals a naive circle in tile space would give.
    S = 1.0 / ASPECT["marquee"]

    def X(c, d):
        return c + d * S

    def F(c, pts):
        return [(c + dx * S, y) for (dx, y) in pts]

    # --- supporting figures, behind
    for (c, fc, fh, dirn) in ((80, "#2f6fd0", 166, 1), (104, "#e8a02a", 184, 1),
                              (158, "#c8283c", 180, -1),
                              (180, "#3fa8d8", 164, -1)):
        _poly(b, F(c, [(-26, 244), (-30, fh + 20), (-24, fh),
                       (24, fh), (30, fh + 20), (26, 244)]), _c(fc), 0.82)
        _poly(b, F(c, [(28 * dirn, fh + 4), (74 * dirn, fh + 30),
                       (80 * dirn, fh + 48), (24 * dirn, fh + 26)]),
              _c(fc), 0.82)                                       # arm
        _disc(b, X(c, 84 * dirn), fh + 42.0, 12.0 * S, 12.0,
              _c("#e8c49a"), 0.82)                                # hand
        _disc(b, c, fh - 15.0, 15.0 * S, 15.0, _c("#e8c49a"), 0.82)
    # --- left hero: cape, red suit, fist driving right
    _poly(b, F(46, [(-64, 244), (-50, 152), (-20, 94), (18, 116),
                    (6, 190), (32, 244)]), _c("#16225e"), 0.95)     # cape
    _poly(b, F(46, [(-30, 244), (-34, 176), (-37, 126), (37, 124),
                    (34, 178), (28, 244)]), _c("#a3141e"), 1.0)     # torso
    _poly(b, F(46, [(-20, 238), (-24, 178), (-26, 132), (16, 131),
                    (14, 180), (10, 238)]), _c("#e0342c"), 1.0)     # lit
    _rect(b, X(46, -37), 186, X(46, 37), 202, _c("#f2c22a"), 0.95)  # belt
    _poly(b, F(46, [(28, 128), (118, 148), (126, 172), (24, 154)]),
          _c("#a3141e"), 1.0)                                       # arm
    _disc(b, X(46, 130), 160, 17.0 * S, 17.0, _c("#f0c48a"), 1.0)   # fist
    _rect(b, X(46, -11), 108, X(46, 11), 128, _c("#f0c48a"), 1.0)   # neck
    _disc(b, 46, 96, 20.0 * S, 20.0, _c("#f0c48a"), 1.0)            # head
    _poly(b, F(46, [(-21, 94), (-19, 76), (21, 74), (23, 96),
                    (8, 88), (-6, 88)]), _c("#16225e"), 1.0)        # mask
    # --- right hero: white gi, red headband, fist driving left
    _poly(b, F(212, [(-36, 244), (-33, 178), (-36, 126), (37, 128),
                     (34, 180), (30, 244)]), _c("#b9b3a2"), 1.0)    # gi
    _poly(b, F(212, [(-24, 238), (-22, 180), (-24, 134), (16, 135),
                     (14, 182), (11, 238)]), _c("#f2eee0"), 1.0)    # lit
    _rect(b, X(212, -36), 182, X(212, 37), 198, _c("#1a1a20"), 0.95)
    _poly(b, F(212, [(-30, 134), (-122, 152), (-130, 176), (-26, 158)]),
          _c("#e6ddc8"), 1.0)                                       # arm
    _disc(b, X(212, -134), 164, 17.0 * S, 17.0, _c("#eab887"), 1.0)  # fist
    _rect(b, X(212, -11), 110, X(212, 11), 130, _c("#eab887"), 1.0)
    _disc(b, 212, 98, 20.0 * S, 20.0, _c("#eab887"), 1.0)           # head
    _poly(b, F(212, [(-22, 88), (22, 86), (23, 98), (-21, 100)]),
          _c("#cf2020"), 1.0)                                       # headband
    _poly(b, F(212, [(22, 88), (58, 62), (62, 78), (23, 98)]),
          _c("#cf2020"), 1.0)                                       # tail
    # --- the impact flash, over the fists where they meet
    fy = 162.0
    _disc(b, cx, fy, 92.0 * S, 92.0, _c("#f7e9b0"), 0.34)
    _disc(b, cx, fy, 40.0 * S, 40.0, _c("#fffbe8"), 0.85)
    for k in range(12):
        aa = k * math.pi / 6.0 + 0.16
        _seg(b, cx, fy, cx + 116.0 * math.cos(aa) * S,
             fy + 116.0 * math.sin(aa), 3.4, _c("#fff8d8"), 0.5, kx=S)
    # frame: the marquee sits in a black extrusion
    _rect(b, 0, 0, 256, 9, _c("#0a0810"), 1.0)
    _rect(b, 0, 247, 256, 256, _c("#0a0810"), 1.0)
    _commit(px, ox, oy, b, tile)


def mvc_side(px, ox, oy, tile=TILE):
    """Dark flank.  No graphic resolves in any frame, so none is invented:
    a black print with a large very-low-contrast tonal shape in it and a
    black T-molding down the front (right) edge."""
    b = _buf("#1e1c23")

    def f(x, y, c):
        t = _fbm(x / 96.0, y / 150.0, 401, 2)
        v = 26.0 + 20.0 * t - 7.0 * (y / 255.0)
        return (v * 1.02, v * 0.99, v * 1.14)
    _field(b, f)
    # a faint sheen band, the one thing the photograph does show on this flank
    for i in range(3):
        _seg(b, 30 + i * 8, 250, 150 + i * 8, 20, 26.0,
             _c("#33313c"), 0.16, kx=1.0)
    _rect(b, 244, 0, 256, 256, _c("#141319"), 1.0)
    _rect(b, 241, 0, 244, 256, _c("#2b2933"), 0.8)
    _commit(px, ox, oy, b, tile)


def mvc_front(px, ox, oy, tile=TILE):
    """The emptiest lower front in the run: plain black, a small recessed
    coin/service box dead centre, and the ROYAL BLUE riser under it carrying
    the wordmark.  The riser is included here because ar2 gives this machine
    no separate plinth quad -- see "marvel-vs-capcom.riser" if it gains one."""
    b = _buf("#201d26")
    xs = 1.0 / ASPECT["front"]

    def f(x, y, c):
        v = 33.0 - 5.0 * (y / 190.0) + 7.0 * _fbm(x / 60.0, y / 60.0, 55, 2)
        return (v * 0.98, v * 0.96, v * 1.10)
    _field(b, f)
    # recessed coin / service box
    _rrect(b, 92, 62, 164, 150, 4.0, _c("#17151c"), 1.0)
    _seg(b, 92, 62, 164, 62, 2.0, _c("#3a3742"), 0.8, kx=1.0)
    _seg(b, 92, 150, 164, 150, 2.0, _c("#0d0c11"), 0.9, kx=1.0)
    _rect(b, 110, 78, 146, 84, _c("#0a090d"), 1.0)     # coin slot
    _rect(b, 110, 96, 146, 101, _c("#0a090d"), 1.0)
    _disc(b, 128, 124, 5.0, 5.0, _c("#8c8a94"), 0.9)   # release button
    # ------ the royal-blue riser, bottom 26%
    _rect(b, 0, 190, 256, 256, _vgrad(190, 256, [
        (0.0, "#2049c4"), (0.45, "#1a3ea8"), (1.0, "#122c78")]), 1.0)
    _seg(b, 0, 191, 256, 191, 3.0, _c("#4f77e0"), 0.7, kx=1.0)
    cap = 21.0
    wm = _text_w("MARVEL", cap, xs, 1.0, 0.14)
    wc = _text_w("CAPCOM", cap, xs, 1.0, 0.14)
    gap = 26.0
    tot = wm + gap + wc
    x0 = 128.0 - tot * 0.5
    _text(b, "MARVEL", x0, 226, cap, _c("#f4f4f8"), weight=0.19, xs=xs,
          track=0.14)
    _text(b, "CAPCOM", x0 + wm + gap, 226, cap, _c("#e02a2a"), weight=0.19,
          xs=xs, track=0.14)
    # the small light "VS" device between the two words
    vx = x0 + wm + gap * 0.5
    _disc(b, vx, 218, 13.0, 15.0, _c("#8fa8e8"), 0.55)
    _text(b, "VS", vx, 224, 15.0, _c("#ffffff"), weight=0.22, xs=xs,
          track=0.10, align="c")
    # the second, smaller line under it
    _text(b, "CLASH OF SUPER HEROES", 128, 243, 8.0, _c("#b9c8ee"),
          weight=0.24, xs=xs, track=0.20, align="c", a=0.85)
    _commit(px, ox, oy, b, tile)


def mvc_riser(px, ox, oy, tile=TILE):
    """The riser on its own, for a build that gives this machine a plinth
    quad.  Same wordmark, sized for a 6.2:1 band."""
    b = _buf("#1a3ea8")
    xs = 1.0 / ASPECT["riser"]
    _field(b, lambda x, y, c: _mix(_c("#2049c4"), _c("#122c78"),
                                   (y / 255.0) ** 0.8))
    cap = 78.0
    wm = _text_w("MARVEL", cap, xs, 1.0, 0.14)
    wc = _text_w("CAPCOM", cap, xs, 1.0, 0.14)
    gap = 30.0
    x0 = 128.0 - (wm + gap + wc) * 0.5
    _text(b, "MARVEL", x0, 150, cap, _c("#f4f4f8"), weight=0.19, xs=xs,
          track=0.14)
    _text(b, "CAPCOM", x0 + wm + gap, 150, cap, _c("#e02a2a"), weight=0.19,
          xs=xs, track=0.14)
    vx = x0 + wm + gap * 0.5
    _disc(b, vx, 128, 13.0, 48.0, _c("#8fa8e8"), 0.5)
    _text(b, "VS", vx, 142, 52.0, _c("#ffffff"), weight=0.22, xs=xs,
          track=0.10, align="c")
    _text(b, "CLASH OF SUPER HEROES", 128, 210, 30.0, _c("#b9c8ee"),
          weight=0.22, xs=xs, track=0.20, align="c", a=0.9)
    _commit(px, ox, oy, b, tile)


def mvc_deck(px, ox, oy, tile=TILE):
    """The clearest deck in the run: a pale grey/silver panel, two ball-top
    joystick collars and two six-button arrays in green, red, white and blue.
    The controls themselves are geometry -- this is the print under them."""
    b = _buf("#cdd0d8")
    _field(b, lambda x, y, c: _mix(_c("#d9dce3"), _c("#b9bdc7"),
                                   abs(y - 118.0) / 150.0))
    # brushed grain, along the panel's long axis
    for y in range(0, TILE, 2):
        v = (_h2(0, y, 7) - 0.5) * 9.0
        _rect(b, 0, y, 256, y + 1, (200 + v, 203 + v, 210 + v), 0.35)
    _rect(b, 0, 0, 256, 12, _c("#2c2f36"), 1.0)         # dark back lip
    _rect(b, 0, 244, 256, 256, _c("#2c2f36"), 1.0)      # dark front lip
    _seg(b, 0, 14, 256, 14, 2.0, _c("#8d919b"), 0.7, kx=1.0)
    for side in (0, 1):
        sx = 64.0 + side * 128.0
        # joystick collar
        _ring(b, sx - 34.0, 150.0, 15.0, 15.0, 4.0, _c("#5b5f68"), 0.85)
        _disc(b, sx - 34.0, 150.0, 8.0, 8.0, _c("#3a3d44"), 0.9)
        # six buttons, 2 rows of 3 -- the fighting-game layout
        cols = ("#3aa03c", "#c8302c", "#e8e8ec", "#2f5fc0",
                "#3aa03c", "#c8302c")
        for k in range(6):
            r, cc = k // 3, k % 3
            bx_ = sx + 2.0 + cc * 21.0
            by_ = 128.0 + r * 34.0 + (cc % 2) * 7.0
            _ring(b, bx_, by_, 9.5, 9.5, 3.0, _c(cols[k]), 0.9)
            _disc(b, bx_, by_, 6.5, 6.5, _c("#9aa0aa"), 0.35)
        _text(b, "1P" if side == 0 else "2P", sx - 34.0, 196, 13.0,
              _c("#4a4e57"), weight=0.20, xs=1.0 / ASPECT["deck"],
              align="c", a=0.8)
    _seg(b, 128, 16, 128, 242, 3.0, _c("#8d919b"), 0.55, kx=1.0)
    _commit(px, ox, oy, b, tile)


# =========================================================================
#  TERMINATOR 2: JUDGMENT DAY   -- SOUTH_RUN[3]
#  the easternmost of the four south uprights.  Matte black, chrome type,
#  a blue gun and a red gun on the deck.
# =========================================================================
def _chrome(y0, y1):
    return _vgrad(y0, y1, [(0.0, "#f2f4f8"), (0.30, "#c6ccd6"),
                           (0.52, "#6b7280"), (0.56, "#9aa2ae"),
                           (0.80, "#e2e6ec"), (1.0, "#8d949f")])


def t2_marquee(px, ox, oy, tile=TILE):
    """Black ground.  Two lines of silver caps set LEFT of centre and
    left-aligned, 'TERMINATOR 2' over 'JUDGMENT DAY', the second slightly
    wider; the right third carries the chrome shard device."""
    b = _buf("#161423")
    xs = 1.0 / ASPECT["marquee"]
    _field(b, lambda x, y, c: _mix(_c("#1b1826"), _c("#0d0c15"),
                                   (y / 255.0) ** 0.7))
    # the chrome shard-and-blade device, right third
    _poly(b, [(206, 40), (242, 72), (232, 130), (250, 178), (216, 214),
              (198, 150), (210, 102)], _chrome(40, 214), 1.0)
    _poly(b, [(212, 58), (232, 80), (224, 128), (216, 104)],
          _c("#f4f6fa"), 0.75)
    _poly(b, [(206, 140), (226, 168), (214, 202), (204, 168)],
          _c("#5c626e"), 0.8)
    _seg(b, 188, 44, 188, 210, 3.0, _c("#6e7480"), 0.5, kx=1.0)
    # the type -- left-aligned, left of centre, second line slightly wider
    cap = 56.0
    _text(b, "TERMINATOR 2", 16, 108, cap, _chrome(52, 108), weight=0.155,
          xs=xs, wide=1.00, track=0.13)
    _text(b, "JUDGMENT DAY", 16, 196, cap, _chrome(140, 196), weight=0.155,
          xs=xs, wide=1.08, track=0.16)
    # maroon T-molding reads at the band edges in every frame
    _rect(b, 0, 0, 256, 7, _c("#4e1119"), 1.0)
    _rect(b, 0, 249, 256, 256, _c("#4e1119"), 1.0)
    _commit(px, ox, oy, b, tile)


def t2_side(px, ox, oy, tile=TILE):
    """Essentially black over the whole flank with white/silver line work, a
    white 'T2' near the lower FRONT corner (tile right = cabinet front) and
    the dark red-maroon T-molding down the front edge.  No figurative art
    resolves in any frame, so none is drawn."""
    b = _buf("#1c161e")
    _field(b, lambda x, y, c: (
        27.0 + 6.0 * _fbm(x / 40.0, y / 90.0, 88, 2) - 4.0 * (y / 255.0),
        23.0 + 6.0 * _fbm(x / 40.0, y / 90.0, 88, 2) - 4.0 * (y / 255.0),
        30.0 + 6.0 * _fbm(x / 40.0, y / 90.0, 88, 2) - 4.0 * (y / 255.0)))
    # silver line work: long shallow diagonals, a couple of hairline seams
    for (ax, ay, bx, by, w, al) in (
            (10, 60, 236, 24, 2.0, 0.45), (10, 74, 236, 38, 1.4, 0.30),
            (16, 150, 240, 104, 2.0, 0.38), (0, 196, 244, 168, 1.4, 0.26),
            (28, 246, 244, 210, 2.4, 0.34)):
        _seg(b, ax, ay, bx, by, w, _c("#b9bec8"), al, kx=1.0)
    for (ax, ay, bx, by) in ((60, 8, 106, 250), (150, 10, 186, 250)):
        _seg(b, ax, ay, bx, by, 1.2, _c("#7d838f"), 0.20, kx=1.0)
    # the white T2 mark, low and forward
    _text(b, "T2", 196, 226, 30.0, _c("#e8eaee"), weight=0.20,
          xs=1.0 / ASPECT["side"], wide=0.72, track=0.10, align="c")
    # maroon T-molding on the front edge
    _rect(b, 246, 0, 256, 256, _c("#5a1620"), 1.0)
    _rect(b, 243, 0, 246, 256, _c("#31101a"), 0.9)
    _commit(px, ox, oy, b, tile)


def t2_front(px, ox, oy, tile=TILE):
    """Matte black with ONE large white 'T2' wordmark left of centre, about
    the middle 45% of the panel width at 40-60% of its height, in a heavy
    squared techno sans; a narrow row of small pale legal graphics along the
    bottom.  Nothing else."""
    b = _buf("#1c161e")
    xs = 1.0 / ASPECT["front"]
    _field(b, lambda x, y, c: (
        29.0 + 5.0 * _fbm(x / 70.0, y / 70.0, 141, 2) - 6.0 * (y / 255.0),
        24.0 + 5.0 * _fbm(x / 70.0, y / 70.0, 141, 2) - 6.0 * (y / 255.0),
        31.0 + 5.0 * _fbm(x / 70.0, y / 70.0, 141, 2) - 6.0 * (y / 255.0)))
    # the wordmark: heavy, squared, wide.  Drawn twice -- a dark spread
    # first, so the letters have an edge against the black carcase.
    _text(b, "T2", 104, 164, 64.0, _c("#0d0a11"), weight=0.30, xs=xs,
          wide=1.85, track=0.06, align="c")
    _text(b, "T2", 104, 164, 64.0, _c("#c4c6cc"), weight=0.235, xs=xs,
          wide=1.85, track=0.06, align="c")
    _text(b, "T2", 104, 162, 64.0, _c("#eceef2"), weight=0.16, xs=xs,
          wide=1.85, track=0.06, align="c")
    # the row of small pale graphics / legal text across the bottom
    y = 232.0
    x = 26.0
    for k in range(17):
        w = 5.0 + (_h2(k, 3, 9) * 16.0)
        h = 2.0 + 2.0 * (k % 2)
        _rect(b, x, y, x + w, y + h, _c("#8a8792"), 0.55)
        x += w + 5.0
        if x > 232.0:
            break
    _rect(b, 26, 244, 96, 247, _c("#8a8792"), 0.35)
    _commit(px, ox, oy, b, tile)


def t2_deck(px, ox, oy, tile=TILE):
    """Black, angled, projecting.  It carries TWO LIGHT GUNS -- no joystick
    and no button field -- so the print is a black deck with the two holster
    cradles, a maroon pinstripe along the player edge and the two player
    marks.  Blue gun left, red gun right: the guns are geometry, the coloured
    cradle collars are what the print contributes."""
    b = _buf("#191420")
    xs = 1.0 / ASPECT["deck"]
    _field(b, lambda x, y, c: (
        34.0 + 8.0 * _fbm(x / 26.0, y / 26.0, 611, 2),
        28.0 + 8.0 * _fbm(x / 26.0, y / 26.0, 611, 2),
        38.0 + 8.0 * _fbm(x / 26.0, y / 26.0, 611, 2)))
    _rect(b, 0, 0, 256, 14, _c("#0f0c14"), 1.0)
    for (sx, col) in ((66.0, "#2f5fd0"), (190.0, "#cf2424")):
        _rrect(b, sx - 44, 96, sx + 44, 186, 10.0, _c("#100d15"), 1.0)
        _ring(b, sx, 141, 33.0, 33.0, 4.0, _c(col), 0.85)
        _ring(b, sx, 141, 21.0, 21.0, 2.5, _c(col), 0.45)
        _disc(b, sx, 141, 13.0, 13.0, _c("#0b090e"), 1.0)
    _rect(b, 0, 224, 256, 231, _c("#5a1620"), 1.0)
    _text(b, "PLAYER 1", 66, 216, 13.0, _c("#8f96a4"), weight=0.20, xs=xs,
          track=0.20, align="c", a=0.8)
    _text(b, "PLAYER 2", 190, 216, 13.0, _c("#8f96a4"), weight=0.20, xs=xs,
          track=0.20, align="c", a=0.8)
    _rect(b, 0, 246, 256, 256, _c("#0f0c14"), 1.0)
    _commit(px, ox, oy, b, tile)


# =========================================================================
#  NFL BLITZ   -- NORTH_RUN[2]
#  third from the west on the north wall, between Pac-Man and Golden Tee.
# =========================================================================
def _wing(b, cx, cy, dirn, span, col, a=1.0):
    """One half of a swept chrome wing, `dirn` = -1 left / +1 right."""
    p = [(cx, cy - 3.0)]
    for k in range(5):
        t = (k + 1) / 5.0
        p.append((cx + dirn * span * t, cy - 3.0 - 13.0 * t ** 0.7))
    for k in range(5, 0, -1):
        t = k / 5.0
        p.append((cx + dirn * span * t, cy + 2.0 + 5.0 * t ** 1.4))
    p.append((cx, cy + 3.0))
    _poly(b, p, col, a)
    for k in range(3):
        t = 0.35 + k * 0.2
        _seg(b, cx + dirn * span * t, cy - 5.0 - 10.0 * t,
             cx + dirn * span * (t + 0.16), cy + 2.0 + 4.0 * t,
             1.6, _c("#3c414c"), 0.5, kx=1.0)


def blitz_marquee(px, ox, oy, tile=TILE):
    """Near-black / dark navy ground, a RED-and-WHITE flare across the top
    left, and 'NFL BLITZ' in chunky ITALIC chrome block capitals spanning
    nearly the full width.  Reads directly in v4 7 at 8x."""
    b = _buf("#0b0e1c")
    xs = 1.0 / ASPECT["marquee"]
    _field(b, lambda x, y, c: _mix(_c("#101534"), _c("#05060e"),
                                   (y / 255.0) ** 0.6))
    # the flare: a white core streak with a red halo, upper left
    _poly(b, [(6, 84), (60, 56), (128, 42), (172, 40), (170, 52),
              (126, 56), (62, 72), (10, 96)], _c("#8c1420"), 0.6)
    _poly(b, [(10, 78), (62, 54), (126, 44), (166, 43), (165, 50),
              (124, 52), (62, 66), (12, 88)], _c("#d8262c"), 0.8)
    _poly(b, [(16, 74), (64, 54), (124, 46), (152, 45), (152, 49),
              (123, 50), (64, 60), (17, 80)], _c("#f4e8e0"), 0.92)
    for k in range(9):
        t = k / 8.0
        x = 20.0 + t * 128.0
        y = 70.0 - t * 16.0
        _seg(b, x, y - 20.0 - 14.0 * math.sin(t * 3.0), x, y + 14.0,
             1.6, _c("#e8b0a4"), 0.35, kx=1.0)
    _disc(b, 96, 60, 24.0, 16.0, _c("#ffffff"), 0.28)
    # NFL BLITZ, italic chrome, near full width
    cap = 96.0
    _text(b, "NFL BLITZ", 128, 214, cap, _c("#05060c"), weight=0.30, xs=xs,
          wide=1.70, track=0.10, ital=0.22, align="c")
    _text(b, "NFL BLITZ", 128, 214, cap, _chrome(118, 214), weight=0.215,
          xs=xs, wide=1.70, track=0.10, ital=0.22, align="c")
    _text(b, "NFL BLITZ", 128, 211, cap, _c("#f4f7fb"), weight=0.075, xs=xs,
          wide=1.70, track=0.10, ital=0.22, align="c", a=0.85)
    _rect(b, 0, 0, 256, 6, _c("#05060c"), 1.0)
    _rect(b, 0, 250, 256, 256, _c("#05060c"), 1.0)
    _commit(px, ox, oy, b, tile)


def blitz_side(px, ox, oy, tile=TILE):
    """The flank is occluded by Pac-Man on one side and Golden Tee on the
    other; the one sliver v4 6 shows (x322-330, y155-200) gives BLUE and a
    RED/ORANGE form against dark.  So: a blue energy swash crossed by a
    red-orange one on a black ground, and NO invented figures -- I can see
    that there is a coloured graphic, not what it depicts."""
    b = _buf("#101018")
    _field(b, lambda x, y, c: (
        16.0 + 5.0 * _fbm(x / 50.0, y / 110.0, 700, 2),
        16.0 + 5.0 * _fbm(x / 50.0, y / 110.0, 700, 2),
        24.0 + 6.0 * _fbm(x / 50.0, y / 110.0, 700, 2)))
    # blue swash, lower-back to upper-front
    _poly(b, [(0, 236), (96, 150), (256, 40), (256, 96), (110, 190), (0, 254)],
          _vgrad(40, 254, [(0.0, "#3f8fe0"), (0.5, "#1f47b0"),
                           (1.0, "#132a70")]), 0.92)
    _poly(b, [(0, 226), (96, 142), (256, 34), (256, 52), (104, 158), (0, 240)],
          _c("#7fc0f4"), 0.45)
    # red / orange form crossing it
    _poly(b, [(6, 70), (120, 128), (256, 154), (256, 200), (110, 168),
              (0, 104)],
          _vgrad(70, 200, [(0.0, "#f0902a"), (0.55, "#d4451e"),
                           (1.0, "#8c1c14")]), 0.9)
    _poly(b, [(10, 74), (118, 132), (256, 158), (256, 168), (112, 146),
              (6, 92)], _c("#ffcf7a"), 0.4)
    # silver speed lines
    for k in range(6):
        y = 30.0 + k * 40.0
        _seg(b, 20, y, 236, y - 26.0, 1.4, _c("#c8ccd4"), 0.16, kx=1.0)
    _rect(b, 248, 0, 256, 256, _c("#0b0b11"), 1.0)
    _commit(px, ox, oy, b, tile)


def blitz_front(px, ox, oy, tile=TILE):
    """Black.  Two large dark recessed panels side by side across the upper
    half, each with a single small white dot, and across the lower part the
    large chrome winged badge -- 'NFL' small over 'BLITZ' larger, wings
    spreading left and right.  Legible in v4 7 at 8x."""
    b = _buf("#1a1a20")
    xs = 1.0 / ASPECT["front"]
    _field(b, lambda x, y, c: (
        27.0 + 5.0 * _fbm(x / 64.0, y / 64.0, 909, 2) - 5.0 * (y / 255.0),
        27.0 + 5.0 * _fbm(x / 64.0, y / 64.0, 909, 2) - 5.0 * (y / 255.0),
        33.0 + 5.0 * _fbm(x / 64.0, y / 64.0, 909, 2) - 5.0 * (y / 255.0)))
    for sx in (26.0, 134.0):
        _rrect(b, sx, 22, sx + 96, 132, 5.0, _c("#131318"), 1.0)
        _seg(b, sx, 22, sx + 96, 22, 2.0, _c("#33333c"), 0.65, kx=1.0)
        _seg(b, sx, 132, sx + 96, 132, 2.0, _c("#0b0b0f"), 0.9, kx=1.0)
        _rect(b, sx + 14, 40, sx + 82, 46, _c("#0c0c10"), 0.9)
        _disc(b, sx + 60, 108, 4.5, 4.5, _c("#f0f2f6"), 0.95)
    # the winged badge
    cy = 196.0
    _wing(b, 118, cy, -1, 96, _chrome(cy - 22, cy + 12), 0.95)
    _wing(b, 138, cy, 1, 96, _chrome(cy - 22, cy + 12), 0.95)
    _text(b, "NFL", 128, cy - 8, 22.0, _c("#05060c"), weight=0.42, xs=xs,
          wide=1.30, track=0.14, align="c")
    _text(b, "NFL", 128, cy - 8, 22.0, _chrome(cy - 30, cy - 8), weight=0.26,
          xs=xs, wide=1.30, track=0.14, align="c")
    _text(b, "BLITZ", 128, cy + 30, 34.0, _c("#05060c"), weight=0.36, xs=xs,
          wide=1.55, track=0.10, ital=0.20, align="c")
    _text(b, "BLITZ", 128, cy + 30, 34.0, _chrome(cy - 4, cy + 30),
          weight=0.22, xs=xs, wide=1.55, track=0.10, ital=0.20, align="c")
    _commit(px, ox, oy, b, tile)


def blitz_deck(px, ox, oy, tile=TILE):
    """A printed BLUE-VIOLET MOTTLED / NEBULA graphic across the whole deck --
    the most distinctive control surface on the north wall and the only
    strongly coloured thing on the machine.  Authored bright for ART_DK.
    The joysticks and buttons on top of it are geometry."""
    b = _buf("#6b5f96")

    def f(x, y, c):
        n = _fbm(x / 52.0, y / 38.0, 1201, 3)
        w = _vnoise(x / 21.0 + 3.0, y / 17.0, 1301)
        t = min(1.0, max(0.0, n * 1.30 + w * 0.24 - 0.22))
        if t < 0.5:
            return _mix(_c("#41386a"), _c("#7d72b4"), t * 2.0)
        return _mix(_c("#7d72b4"), _c("#cfc6f0"), (t - 0.5) * 2.0)
    _field(b, f)
    # star specks
    for k in range(46):
        x = _h2(k, 1, 21) * 255.0
        y = _h2(k, 2, 21) * 255.0
        r = 0.6 + _h2(k, 3, 21) * 1.5
        _disc(b, x, y, r, r, _c("#f4f0ff"), 0.75)
    _rect(b, 0, 0, 256, 13, _c("#241f36"), 1.0)
    _rect(b, 0, 243, 256, 256, _c("#241f36"), 1.0)
    # printed button collars, under where the geometry's buttons sit
    for side in (0, 1):
        sx = 62.0 + side * 132.0
        _ring(b, sx - 32.0, 148.0, 14.0, 14.0, 3.0, _c("#241f36"), 0.6)
        for k in range(6):
            r, cc = k // 3, k % 3
            _ring(b, sx + 2.0 + cc * 20.0, 130.0 + r * 32.0, 9.0, 9.0, 2.5,
                  _c("#241f36"), 0.55)
    _commit(px, ox, oy, b, tile)


# =========================================================================
#  EAST_RUN[6]  -- THERE IS NO MACHINE HERE
#  The east wall carries five uprights plus the angled Star Wars, counted
#  independently in v3 4, v4 3, v4 8 and v4 9.  Delete the slot and re-space
#  the run.  If the build must keep seven, these four panels are an honest
#  unbranded black upright: no title, no licensed art, nothing invented.
# =========================================================================
def blank_marquee(px, ox, oy, tile=TILE):
    """A blank backlit marquee: a diffuser panel in a black frame, no type."""
    b = _buf("#1b1b20")
    _field(b, lambda x, y, c: _mix(_c("#22222a"), _c("#131318"),
                                   (y / 255.0) ** 0.8))
    _rect(b, 14, 34, 242, 222, _vgrad(34, 222, [
        (0.0, "#8e9099"), (0.35, "#b6b8c0"), (1.0, "#75777f")]), 1.0)
    _seg(b, 14, 34, 242, 34, 3.0, _c("#c8cad2"), 0.7, kx=1.0)
    _seg(b, 14, 222, 242, 222, 3.0, _c("#4b4d55"), 0.9, kx=1.0)
    for k in range(4):
        _seg(b, 20 + k * 58, 40, 20 + k * 58, 216, 2.0, _c("#6e7078"),
             0.30, kx=1.0)
    _commit(px, ox, oy, b, tile)


def blank_side(px, ox, oy, tile=TILE):
    """Plain matte black vinyl: a horizontal seam, a small vent grille low
    and back, and nothing else."""
    b = _buf("#1d1d21")
    _field(b, lambda x, y, c: (
        30.0 + 4.0 * _fbm(x / 120.0, y / 200.0, 1500, 2),
        30.0 + 4.0 * _fbm(x / 120.0, y / 200.0, 1500, 2),
        33.0 + 4.0 * _fbm(x / 120.0, y / 200.0, 1500, 2)))
    _seg(b, 0, 88, 256, 88, 1.6, _c("#0f0f13"), 0.7, kx=1.0)
    _seg(b, 0, 90, 256, 90, 1.2, _c("#3a3a42"), 0.35, kx=1.0)
    for k in range(9):
        _rect(b, 18, 176 + k * 7, 74, 180 + k * 7, _c("#0d0d11"), 0.85)
    _rect(b, 248, 0, 256, 256, _c("#141418"), 1.0)
    _commit(px, ox, oy, b, tile)


def blank_front(px, ox, oy, tile=TILE):
    """Black, with a plain steel coin door and no printed graphic at all."""
    b = _buf("#1e1e22")
    _field(b, lambda x, y, c: (
        31.0 + 4.0 * _fbm(x / 80.0, y / 80.0, 1700, 2) - 6.0 * (y / 255.0),
        31.0 + 4.0 * _fbm(x / 80.0, y / 80.0, 1700, 2) - 6.0 * (y / 255.0),
        34.0 + 4.0 * _fbm(x / 80.0, y / 80.0, 1700, 2) - 6.0 * (y / 255.0)))
    _rect(b, 88, 74, 168, 176, _vgrad(74, 176, [
        (0.0, "#6e7078"), (0.5, "#4e5057"), (1.0, "#33353b")]), 1.0)
    _seg(b, 88, 74, 168, 74, 2.5, _c("#9a9ca4"), 0.8, kx=1.0)
    _rect(b, 100, 92, 156, 98, _c("#141418"), 1.0)
    _rect(b, 100, 112, 156, 118, _c("#141418"), 1.0)
    _disc(b, 128, 150, 6.0, 6.0, _c("#20222a"), 1.0)
    _commit(px, ox, oy, b, tile)


def blank_deck(px, ox, oy, tile=TILE):
    """Dark grey deck, two plain player zones, black collars, no colour."""
    b = _buf("#4c4c55")
    _field(b, lambda x, y, c: _mix(_c("#585862"), _c("#3c3c45"),
                                   abs(y - 122.0) / 150.0))
    _rect(b, 0, 0, 256, 13, _c("#232329"), 1.0)
    _rect(b, 0, 243, 256, 256, _c("#232329"), 1.0)
    for side in (0, 1):
        sx = 64.0 + side * 128.0
        _ring(b, sx - 32.0, 150.0, 15.0, 15.0, 4.0, _c("#26262c"), 0.8)
        for k in range(6):
            r, cc = k // 3, k % 3
            _ring(b, sx + 2.0 + cc * 21.0, 130.0 + r * 33.0, 9.5, 9.5, 3.0,
                  _c("#26262c"), 0.75)
    _seg(b, 128, 16, 128, 240, 2.0, _c("#33333b"), 0.6, kx=1.0)
    _commit(px, ox, oy, b, tile)


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


# =========================================================================
#  EXPORTS
# =========================================================================
# ROUND 5 OWNS THE SOUTH RUN.  `PANELS` is exactly the four machines this
# agent was assigned; the three machines art_g2 painted in round 4 that are
# now on other agents' runs have moved to `LEGACY_PANELS` so that merging
# this module can never collide with theirs.
#
# INTEGRATOR: if no other module claims marvel-vs-capcom / nfl-blitz /
# east-7-no-machine this round, `atlas4.Atlas` will raise
# "no art module paints 'nfl-blitz.side'".  The fix is one line, after the
# merge loop in atlas4.py:
#
#     for k, fn in art_g2.LEGACY_PANELS.items():
#         PANELS.setdefault(k, fn)
#
# That prefers whoever owns them now and falls back to round 4's drawings.
PANELS = {
    "legends-ultimate.marquee": lu_marquee,
    "legends-ultimate.side": lu_side,
    "legends-ultimate.front": lu_front,
    "legends-ultimate.deck": lu_deck,
    "legends-ultimate.screen": lu_screen,

    "street-fighter-2-champion-edition.marquee": ce_marquee,
    "street-fighter-2-champion-edition.side": ce_side,
    "street-fighter-2-champion-edition.front": ce_front,
    "street-fighter-2-champion-edition.deck": ce_deck,
    "street-fighter-2-champion-edition.screen": ce_screen,

    "time-crisis.marquee": tc_marquee,
    "time-crisis.side": tc_side,
    "time-crisis.front": tc_front,
    "time-crisis.deck": tc_deck,
    "time-crisis.screen": tc_screen,

    "terminator-2.marquee": t2_marquee,     # ROUND 4'S, UNCHANGED
    "terminator-2.side": t2_side,
    "terminator-2.front": t2_front,
    "terminator-2.deck": t2_deck,
    "terminator-2.screen": t2_screen,
}

# Round 4's three, kept only as a fallback -- see the note above.
LEGACY_PANELS = {
    "marvel-vs-capcom.marquee": mvc_marquee,
    "marvel-vs-capcom.side": mvc_side,
    "marvel-vs-capcom.front": mvc_front,
    "marvel-vs-capcom.riser": mvc_riser,
    "marvel-vs-capcom.deck": mvc_deck,
    "nfl-blitz.marquee": blitz_marquee,
    "nfl-blitz.side": blitz_side,
    "nfl-blitz.front": blitz_front,
    "nfl-blitz.deck": blitz_deck,
    "east-7-no-machine.marquee": blank_marquee,
    "east-7-no-machine.side": blank_side,
    "east-7-no-machine.front": blank_front,
    "east-7-no-machine.deck": blank_deck,
}

# `.screen` is NEW and OPTIONAL.  ar2.upright currently draws the monitor as
# an untextured `SCRN` quad, which is why three critics saw four black
# rectangles in a row.  To use these:
#   1. atlas4.EXTRA_KEYS += tuple("%s.screen" % s for s in MY_SLUGS)
#      and atlas4.SIZE["screen"] = 48
#   2. in ar2.upright, replace
#          sub.add(quad(...), SCRN)
#      with
#          if art.has(slug + ".screen"):
#              uvq(sub, art.BEZEL_ART_or_ART, [...], art.uv(slug + ".screen"))
#          else:
#              sub.add(quad(...), SCRN)
#      sampling through a DARK factor material (the glass is glossy and
#      nearly black -- ART at #ffffff would wash these to grey).  Measured
#      cost of all four at 48 px is reported in the round-5 notes.
# If the integrator does not want the ar2 change, drop these four keys and
# nothing else in this module changes.
SCREEN_KEYS = tuple("%s.screen" % s for s in
                    ("legends-ultimate",
                     "street-fighter-2-champion-edition",
                     "time-crisis", "terminator-2"))


# -------------------------------------------------------------- geometry spec
# THE BUTTONS AND JOYSTICKS ARE GEOMETRY.  ar2.upright places them and this
# module cannot, so this is the contract the integrator consumes.  Round 4's
# upright() gave every machine in the room the identical loop
#
#     for k in range(2):  two 0.09 ft chrome shafts, two cube tops (red,
#     blue), then three FLAT SQUARE buttons each, at fixed offsets
#
# which is the defect all three critics named in the same words.  Replace
# that loop with a read of `DECKS[slug]`.
#
# COORDINATES, both normalised so they survive any re-proportioning:
#   u  -1.0 .. +1.0 across the cabinet width.  u = -1 is local x = -bw/2.
#      For a south-wall machine (rot 180) local -x is the VIEWER'S LEFT, and
#      these tables are written as the viewer sees them.
#      -> x = u * (bw/2 - 0.10)
#   v   0.0 at the deck's BACK edge (the screen end, z = ft + 0.04)
#       1.0 at the deck's FRONT lip  (z = fd - 0.06)
#      -> z = (ft + 0.04) + v * ((fd - 0.06) - (ft + 0.04))
#   every *_ft is feet, and every y is measured UP from the deck's top face
#   (y = dy + 0.014), except COINS, whose y is measured up from the cabinet
#   base (plinth included), matching upright()'s own coin-door block.
#
# ELEMENT SHAPES
#   stick   {u, v, top, top_color, top_r_ft, shaft_color, shaft_h_ft,
#            dust_color, dust_r_ft}
#           top: "ball"  a sphere (an 8-segment low-poly sphere is plenty)
#                "bat"   a taller capsule, flat-topped
#                "none"  shaft only
#   button  {u, v, r_ft, h_ft, color, shape}
#           shape: "round_convex"  a short cylinder with a domed cap -- THE
#                                  DEFAULT.  Round 4 used flat squares on
#                                  every machine in the room and a critic
#                                  named it.
#                  "round_flat"    a plain cylinder, no dome
#                  "square"        the round-4 box, kept only where a photo
#                                  shows a square membrane pad
#   gun     {u, v, yaw_deg, body, grip, len_ft, cradle, cradle_color}
#           yaw_deg 0 = muzzle pointing at the player (down-tile, +v).
#           `cradle` True means a shallow recessed cup is modelled under it.
#   trackball {u, v, r_ft, color, bezel_color}
#   spinner   {u, v, r_ft, color}
#   lip     {color, emissive, emissive_strength, h_ft}  a strip across the
#           whole deck front lip.  Only Legends Ultimate has one, and both
#           v3 4 and v4 8 resolve it, so it is a fixture the photograph
#           shows -- emissive is legitimate there under ROOM-BRIEF's rule.
#
# NOTHING HERE IS SHARED BETWEEN THE FOUR MACHINES: the counts are 2 sticks
# + 12 buttons + trackball + spinner / 2 sticks + 14 buttons / 2 guns + 3
# buttons / 2 guns + 2 buttons, and no two use the same top, colour set,
# radius or arrangement.
DECKS = {
    "legends-ultimate": {
        "note": ("The photographs do NOT resolve this deck's controls "
                 "(roster: 'do not invent joysticks').  What they DO resolve "
                 "is the lit white strip along the front lip, which is "
                 "modelled.  The control layout below is the manufacturer's "
                 "standard for this cabinet -- two ball-tops, 6+6 buttons, a "
                 "centre trackball and a spinner -- and is declared as "
                 "INFERENCE, not as a photo reading.  It is here because a "
                 "bare deck reads as unbuilt; if the integrator would rather "
                 "ship only the lip, drop `sticks`/`buttons`/`trackball`/"
                 "`spinner` and keep `lip`."),
        "inferred": True,
        "sticks": [
            {"u": -0.62, "v": 0.42, "top": "ball", "top_color": "#f2f4f8",
             "top_r_ft": 0.062, "shaft_color": "#9aa0aa", "shaft_h_ft": 0.15,
             "dust_color": "#1a1c22", "dust_r_ft": 0.085},
            {"u": 0.62, "v": 0.42, "top": "ball", "top_color": "#f2f4f8",
             "top_r_ft": 0.062, "shaft_color": "#9aa0aa", "shaft_h_ft": 0.15,
             "dust_color": "#1a1c22", "dust_r_ft": 0.085},
        ],
        "buttons": (
            [{"u": -0.44 + 0.11 * i, "v": 0.32 + 0.05 * (i % 2),
              "r_ft": 0.052, "h_ft": 0.030, "shape": "round_convex",
              "color": c}
             for i, c in enumerate(("#e03a2e", "#e8a51e", "#f2f4f8"))]
            + [{"u": -0.44 + 0.11 * i, "v": 0.52 + 0.05 * (i % 2),
                "r_ft": 0.052, "h_ft": 0.030, "shape": "round_convex",
                "color": c}
               for i, c in enumerate(("#2f6bd8", "#39a552", "#d0d4dc"))]
            + [{"u": 0.80 - 0.11 * i, "v": 0.32 + 0.05 * (i % 2),
                "r_ft": 0.052, "h_ft": 0.030, "shape": "round_convex",
                "color": c}
               for i, c in enumerate(("#e03a2e", "#e8a51e", "#f2f4f8"))]
            + [{"u": 0.80 - 0.11 * i, "v": 0.52 + 0.05 * (i % 2),
                "r_ft": 0.052, "h_ft": 0.030, "shape": "round_convex",
                "color": c}
               for i, c in enumerate(("#2f6bd8", "#39a552", "#d0d4dc"))]
        ),
        "trackball": {"u": 0.0, "v": 0.46, "r_ft": 0.115, "color": "#15161c",
                      "bezel_color": "#3a3e46"},
        "spinner": {"u": 0.26, "v": 0.20, "r_ft": 0.075, "color": "#b8bec8"},
        "guns": [],
        "lip": {"color": "#f6f8fb", "emissive": "#c9d2e0",
                "emissive_strength": 0.9, "h_ft": 0.05},
        "coin_geometry": None,
    },

    "street-fighter-2-champion-edition": {
        "note": ("Six buttons per player in two rows of three, BAT-top "
                 "sticks, and two small black start buttons on the back "
                 "edge.  The identifying feature is not the controls but the "
                 "bright steel bezel band along the leading edge -- that is "
                 "painted into `.deck` and should NOT also be modelled."),
        "inferred": False,
        "sticks": [
            {"u": -0.66, "v": 0.46, "top": "bat", "top_color": "#15161b",
             "top_r_ft": 0.048, "shaft_color": "#8f95a0", "shaft_h_ft": 0.20,
             "dust_color": "#c8ccd4", "dust_r_ft": 0.075},
            {"u": 0.66, "v": 0.46, "top": "bat", "top_color": "#15161b",
             "top_r_ft": 0.048, "shaft_color": "#8f95a0", "shaft_h_ft": 0.20,
             "dust_color": "#c8ccd4", "dust_r_ft": 0.075},
        ],
        "buttons": (
            [{"u": -0.44 + 0.115 * i, "v": 0.34 + 0.045 * (2 - i),
              "r_ft": 0.058, "h_ft": 0.026, "shape": "round_convex",
              "color": "#e8eaee"} for i in range(3)]
            + [{"u": -0.44 + 0.115 * i, "v": 0.56 + 0.045 * (2 - i),
                "r_ft": 0.058, "h_ft": 0.026, "shape": "round_convex",
                "color": "#2f5fd0"} for i in range(3)]
            + [{"u": 0.14 + 0.115 * i, "v": 0.34 + 0.045 * i,
                "r_ft": 0.058, "h_ft": 0.026, "shape": "round_convex",
                "color": "#e8eaee"} for i in range(3)]
            + [{"u": 0.14 + 0.115 * i, "v": 0.56 + 0.045 * i,
                "r_ft": 0.058, "h_ft": 0.026, "shape": "round_convex",
                "color": "#cf2424"} for i in range(3)]
            + [{"u": -0.20, "v": 0.10, "r_ft": 0.034, "h_ft": 0.018,
                "shape": "round_flat", "color": "#22242a"},
               {"u": 0.20, "v": 0.10, "r_ft": 0.034, "h_ft": 0.018,
                "shape": "round_flat", "color": "#22242a"}]
        ),
        "trackball": None,
        "spinner": None,
        "guns": [],
        "lip": None,
        "coin_geometry": None,
    },

    "time-crisis": {
        "note": ("NO joystick and NO button field.  One RED gun lying flat "
                 "and angled across the maroon island left of centre (the "
                 "roster records only this one as certain) and one BLUE gun "
                 "standing in the socket right of centre, which is the blue "
                 "object v3 4 resolves there.  Also a RED FOOT-PEDAL unit on "
                 "the floor in front of the cabinet -- listed in `extras`; "
                 "ar2 has no geometry for it and it is a distinctive "
                 "silhouette worth building."),
        "inferred": False,
        "sticks": [],
        "buttons": [
            {"u": -0.72, "v": 0.16, "r_ft": 0.040, "h_ft": 0.020,
             "shape": "round_flat", "color": "#e03a2e"},
            {"u": 0.72, "v": 0.16, "r_ft": 0.040, "h_ft": 0.020,
             "shape": "round_flat", "color": "#2f5fd0"},
            {"u": 0.0, "v": 0.86, "r_ft": 0.034, "h_ft": 0.016,
             "shape": "round_flat", "color": "#e8c24e"},
        ],
        "guns": [
            {"u": -0.30, "v": 0.55, "yaw_deg": 24.0, "body": "#c0392b",
             "grip": "#3a1512", "len_ft": 0.62, "cradle": True,
             "cradle_color": "#4d1b16"},
            {"u": 0.44, "v": 0.58, "yaw_deg": -8.0, "body": "#2f5fd0",
             "grip": "#141a2e", "len_ft": 0.58, "cradle": True,
             "cradle_color": "#1d2a52"},
        ],
        "trackball": None,
        "spinner": None,
        "lip": None,
        "coin_geometry": {
            "u": 0.0, "y0_ft": 0.62, "y1_ft": 1.36, "w_ft": 0.94,
            "depth_ft": 0.075, "plate": "#9aa1ac", "recess": "#0a0a0e",
            "cup": True, "cup_color": "#07070a",
            "note": ("The BIG door of the wall: steel, centred, and it "
                     "projects.  Painted into `.front` as well, so the "
                     "geometry only needs the plate, the two slots and the "
                     "return cup registered to the print."),
        },
        "extras": [
            {"kind": "foot_pedal", "note": "red pedal unit on the floor, "
             "roughly 1.0 x 0.8 x 0.35 ft, centred on the cabinet and about "
             "0.9 ft in front of the deck lip.  Visible in v3 4 and v4 5."},
        ],
    },

    "terminator-2": {
        "note": ("TWO LIGHT GUNS in chrome-collared cradles, blue LEFT and "
                 "red RIGHT -- resolved at 16x in v3 4 and 14x in v4 8.  No "
                 "joystick, no button field, two start buttons.  Round 4 "
                 "gave this machine two joysticks and six squares, which is "
                 "flatly contradicted by both photographs."),
        "inferred": False,
        "sticks": [],
        "buttons": [
            {"u": -0.50, "v": 0.17, "r_ft": 0.038, "h_ft": 0.018,
             "shape": "round_flat", "color": "#2f5fd0"},
            {"u": 0.50, "v": 0.17, "r_ft": 0.038, "h_ft": 0.018,
             "shape": "round_flat", "color": "#cf2424"},
        ],
        "guns": [
            {"u": -0.50, "v": 0.52, "yaw_deg": 0.0, "body": "#2f5fd0",
             "grip": "#12162a", "len_ft": 0.58, "cradle": True,
             "cradle_color": "#181521"},
            {"u": 0.50, "v": 0.52, "yaw_deg": 0.0, "body": "#cf2424",
             "grip": "#2a1013", "len_ft": 0.58, "cradle": True,
             "cradle_color": "#181521"},
        ],
        "trackball": None,
        "spinner": None,
        "lip": None,
        "coin_geometry": {
            "u": 0.32, "y0_ft": 0.34, "y1_ft": 0.72, "w_ft": 0.52,
            "depth_ft": 0.035, "plate": "#22222a", "recess": "#08080b",
            "cup": False, "cup_color": None,
            "note": ("Small, OFFSET RIGHT and nearly black -- the deliberate "
                     "opposite of Time Crisis's.  Round 4 put a 0.68 ft grey "
                     "plate dead centre on every machine in the room."),
        },
        "extras": [],
    },
}

# The printed front panel's own rect, in feet, where it should differ from
# upright()'s hard-coded `plinth + 0.16 .. dy - 0.62` inset by 0.08 either
# side.  ROOM-BRIEF's standard for this round is a panel that runs TO THE
# FLOOR; three of these four do in the photographs.
FRONT_RECT = {
    # runs to the floor, full width: the licence grid is edge to edge and
    # there is no black kick under it in v3 4 or v4 8.
    "legends-ultimate": {"y0_ft": 0.02, "y1_ft": 2.00, "inset_ft": 0.03},
    # the blue base.  ar2 builds `a2capc` as a solid box whose front face is
    # ~0.015 ft PROUD of this quad, so the panel is invisible today.  Pull
    # the box front from `D - 0.06 - SD` to `D - 0.10 - SD` and raise this
    # quad to cover the base's height; the box then reads as the blue
    # surround the photograph shows round the printed area.
    "street-fighter-2-champion-edition": {
        "y0_ft": 0.06, "y1_ft": 2.30, "inset_ft": 0.10,
        "requires": "a2capc box front -> D - 0.10 - SD"},
    # red pillars are part of the print, so the panel must reach the
    # cabinet's full width and down to the plinth.
    "time-crisis": {"y0_ft": 0.02, "y1_ft": 1.86, "inset_ft": 0.02},
    "terminator-2": {"y0_ft": 0.02, "y1_ft": 1.80, "inset_ft": 0.02},
}

# Suggested atlas sizes for the four new screen panels.  48 px each; the
# glass is dark and low-contrast so they quantise to very few levels.
SCREEN_SIZE_PX = 48

# which photograph each graphic was read off, for the record
EVIDENCE = {
    "legends-ultimate": (
        "docs/photos-jpg/Arcade Room v3 4.jpg px (985,690)-(1130,850) at 7x "
        "-> scratchpad/arc4/art/g2r5/lu_grid.png: the two-column licence "
        "grid, sixteen logos, of which MILLIPEDE, STAR WARS, TRON and the "
        "white Space-Invaders block are legible and are drawn as themselves; "
        "the other twelve resolve as a coloured wordmark SHAPE only and are "
        "drawn as ink at letterform scale, not as invented titles.  Marquee "
        "px (1025,570)-(1175,615) at 12x.  Whole machine "
        "art/g2r5/lu_whole.png.  Corroborated v4 8 -> art/g2r5/v48_south.png "
        "(no coin door anywhere on the front) and v4 5."),
    "street-fighter-2-champion-edition": (
        "docs/photos-jpg/Arcade Room v3 4.jpg px (900,545)-(1010,830) at 5x "
        "-> scratchpad/arc4/art/g2r5/ce_whole.png: the gold-ringed oval "
        "marquee badge with CHAMPION arched and EDITION straight, the "
        "ghosted pale fighter on the royal-blue base and CAPCOM low.  Base "
        "blue #2b5baf..#4e7bba off v4 8 (white cans, not cove) -> "
        "art/g2r5/v48_south.png; the steel band on the deck's leading edge "
        "reads in both."),
    "time-crisis": (
        "docs/photos-jpg/Arcade Room v3 4.jpg px (820,540)-(930,900) at 5x "
        "-> scratchpad/arc4/art/g2r5/tc_whole.png: cream head, maroon band, "
        "tan speaker panel with two round holes, red body with gold front "
        "trim, red-orange deck with a red gun and two pale instruction "
        "panels, black lower front between two red pillars.  The coin door "
        "and its return cup are read off v4 5 px (150,120)-(320,300) at 7x "
        "-> art/g2r5/v45_t2ce.png.  Screen shows a DIM OLIVE image in v3 4 "
        "and is painted dim, not as an attract loop."),
    "terminator-2": (
        "docs/photos-jpg/Arcade Room v4 5.jpg px (150,120)-(320,300) at 7x "
        "-> scratchpad/arc4/art/g2r5/v45_t2ce.png: the white T2 low on the "
        "black front, the maroon T-molding down both front edges, the strip "
        "of small coloured plates along the bottom of the panel, and the "
        "BLUE gun left / RED gun right on the deck.  Marquee and guns also "
        "at 14-16x in roster/rec/v34_south.png and v4 8.  Screen is black in "
        "all three frames and is painted as reflection only."),
}
