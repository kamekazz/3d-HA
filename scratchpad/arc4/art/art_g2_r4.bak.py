"""Round-4 cabinet artwork, agent G2 -- four slots of the Arcade Room roster.

    EAST_RUN[2]   marvel-vs-capcom      Marvel vs Capcom
    EAST_RUN[6]   east-7-no-machine     (no machine stands here -- see below)
    SOUTH_RUN[3]  terminator-2          Terminator 2: Judgment Day
    NORTH_RUN[2]  nfl-blitz             NFL Blitz

Every panel is drawn from the owner's photographs (see `EVIDENCE` at the foot
of this file for the crop each graphic was read off).  Nothing here is a
recoloured copy of anything else here: the four machines carry four unrelated
compositions, and each machine's four panels carry four different ones again.

HOW THE INTEGRATOR USES THIS
----------------------------
`PANELS` maps "<slug>.<panel>" to `paint(px, ox, oy, tile)`, painting one
`tile` x `tile` square into a shared atlas.  `tile` should be `TILE` (256);
smaller works but the letterforms will lose their edges.

Panel names follow ar2.upright's consumers:

  .marquee  the lit title band            (uvq -> MQ_MATS, emissive)
  .side     the swept flank, BOTH sides   (a2kit.sweep -> ART)
  .front    the lower front panel         (uvq -> ART)
  .deck     the control-panel top         (uvq -> ART_DK, flip=True)
  .riser    marvel-vs-capcom only: the royal-blue kick base under the front
            panel.  If the build has no separate riser quad, ignore it --
            the same wordmark is already baked into the bottom band of
            "marvel-vs-capcom.front", which is where the photograph puts it.

THREE THINGS THE INTEGRATOR MUST KNOW, because they are geometry, not art:

1. ASPECT.  The tile is square and every panel it lands on is not, so every
   letterform and every circle in here is PRE-SQUEEZED horizontally by
   1/ASPECT[panel] (values fitted to ar2's own geometry: a marquee quad is
   about 2.2 x 0.62 ft, a flank bbox 2.95 x 6.0, a front panel 2.2 x 1.7, a
   deck 2.2 x 0.92).  If the cabinets are re-proportioned by more than ~15%,
   change ASPECT here and re-run -- do not stretch the atlas.
2. ORIENTATION.  On the flank tile, `sweep`'s uvof puts the cabinet FRONT at
   the tile's RIGHT edge and the cabinet TOP at the tile's TOP.  On the deck
   tile, ar2 passes flip=True, so the tile TOP is the deck's BACK (screen end)
   and the tile is mirrored left-right -- every deck here is drawn
   left-right symmetric so the mirror cannot show.
3. MATERIALS.  `.side` and `.front` are authored as true albedo for ART
   (#ffffff).  `.deck` tiles are authored bright for ART_DK (#4c4c4c), which
   is the existing 0.30 factor for an up-facing surface.  ONE exception:
   "marvel-vs-capcom.deck" is a genuinely pale silver panel in the photograph
   -- the clearest deck in the east run -- and needs a lighter deck material
   (about #9a9a9a) or it lands as dark as its neighbours.

east-7-no-machine: the east wall carries FIVE uprights, not seven.  The
honest fix is to delete that slot and re-space the run.  The panels here are
only a fallback if the build must keep seven: an unbranded black upright with
a blank backlit marquee and a plain steel coin door.  No invented title.

Pure stdlib.  The 4x4 ordered dither and round-to-8 quantisation are copied
from a2kit._paint and are what keeps the PNG small.
"""

import math

TILE = 256

# --- copied verbatim from a2kit so the two atlases quantise identically
_BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]

# panel width / panel height in FEET, measured off ar2._profile + ar2.upright
ASPECT = {
    "marquee": 3.40,    # (bw - 0.12) / mqh
    "side": 0.49,       # (bd/2 + hd + 0.40) / top
    "front": 1.25,      # (bw - 0.16) / (dy - 0.78)
    "deck": 2.35,       # (bw - 0.12) / 0.92
    "riser": 6.20,      # (bw - 0.16) / 0.36
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


# ------------------------------------------------------------------ export
PANELS = {
    "marvel-vs-capcom.marquee": mvc_marquee,
    "marvel-vs-capcom.side": mvc_side,
    "marvel-vs-capcom.front": mvc_front,
    "marvel-vs-capcom.riser": mvc_riser,
    "marvel-vs-capcom.deck": mvc_deck,

    "terminator-2.marquee": t2_marquee,
    "terminator-2.side": t2_side,
    "terminator-2.front": t2_front,
    "terminator-2.deck": t2_deck,

    "nfl-blitz.marquee": blitz_marquee,
    "nfl-blitz.side": blitz_side,
    "nfl-blitz.front": blitz_front,
    "nfl-blitz.deck": blitz_deck,

    "east-7-no-machine.marquee": blank_marquee,
    "east-7-no-machine.side": blank_side,
    "east-7-no-machine.front": blank_front,
    "east-7-no-machine.deck": blank_deck,
}

# which photograph each graphic was read off, for the record
EVIDENCE = {
    "marvel-vs-capcom": (
        "docs/photos-jpg/Arcade Room v3 4.jpg px (140,520)-(300,850) at 6x "
        "(scratchpad/arc4/art/ref/mvc_v34.png): marquee illustration, silver "
        "control deck with two ball-tops and six-button arrays, plain black "
        "lower front with a centre coin box, royal-blue riser.  Riser "
        "wordmark at 16x: scratchpad/arc4/roster/rec/mvc_riser.png.  Run "
        "order confirmed in rec/e_run3x.png, v4 8 and v4 9."),
    "terminator-2": (
        "docs/photos-jpg/Arcade Room v4 8.jpg px (348,110)-(410,230) at 10x "
        "(scratchpad/arc4/art/ref/t2_v48.png): the white T2 on the lower "
        "front and the marquee's two silver lines with the chrome device "
        "right.  Guns and marquee at 14-16x in rec/v34_south.png."),
    "nfl-blitz": (
        "docs/photos-jpg/Arcade Room v4 7.jpg px (0,100)-(200,330) at 6x "
        "(scratchpad/arc4/art/ref/blitz_v47.png): 'NFL BLITZ' italic chrome "
        "in the marquee, the winged chrome badge on the lower front, the two "
        "recessed upper panels with their white dots, and the blue-violet "
        "nebula deck.  Marquee corroborated at 24x in rec/v31_m3.png."),
    "east-7-no-machine": (
        "No machine.  Five uprights counted on the east wall in v3 4, v4 3, "
        "v4 8 and v4 9.  These panels are a fallback only."),
}
