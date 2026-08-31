"""Arcade Room round 4 -- printed artwork for four machines (group 0).

Round 3 shipped ONE motif sixteen times: a coloured vertical gradient, a header
strip and one off-centre blob, plus four "marquees" whose lettering was a comb
of rectangles.  This module replaces that for the four machines assigned to
group 0 with per-machine drawn graphics.

    EAST_RUN[0]   star-wars-atari                     yellow carcase, black
                                                      stepped starfield panel
    EAST_RUN[4]   nba-jam                             cream marquee, court deck
    SOUTH_RUN[1]  street-fighter-2-champion-edition   CHAMPION EDITION oval,
                                                      royal-blue CAPCOM base
    NORTH_RUN[0]  north-1-graffiti-multicade          pale line-art wrap,
                                                      NO legible title

Everything is DRAWN -- no photo-derived raster anywhere in here.  Where a
surface is genuinely not visible in any photograph (Star Wars' marquee, front
and deck) the panel is built plain and generic on purpose; that is recorded in
NOTES and in the report, and no title is invented for it.

Interface, per the round-4 brief:

    TILE = 256
    PANELS = {"<slug>.<zone>": paint_fn}
    paint_fn(px, ox, oy, tile)      px[y][x] = (r, g, b)

Pure stdlib inside every paint function (math + a tiny LCG).  The 4x4 ordered
dither and the round-to-8 quantisation are copied verbatim from a2kit so the
PNG stays cheap; a paint function writes into `px` only at flush time.

-------------------------------------------------------------------------
ASPECT -- the thing that would have sunk this round quietly.

The atlas tile is SQUARE but none of the quads it lands on are.  With a2kit's
geometry a marquee band is about 2.2 ft x 0.66 ft, so a square tile is
stretched 3.3x horizontally across it; a flank is 2.95 ft x 6.2 ft, so a square
tile is stretched 2.1x VERTICALLY.  Draw "NBA JAM" square and the cabinet shows
letters 3.3x too wide with stems 3.3x fatter than their crossbars.

So each panel declares its quad aspect in ASPECT (width/height in feet, taken
off ar2.py's own row for that machine).  It is drawn into an intermediate
buffer with SQUARE pixels at that aspect and resampled into the square tile on
the way out, which pre-distorts it exactly enough to come back correct on the
cabinet.  Inside a paint function:

    positions (u, v) are fractions of the panel's WIDTH / HEIGHT
    LENGTHS   (stroke widths, radii, text heights) are fractions of its HEIGHT
    cv.kx     converts a length into u-units when a helper offsets in u

If the integrator changes a machine's width, marquee height or deck projection,
update ASPECT with it -- the numbers are declared so they can be checked.
-------------------------------------------------------------------------

TONE NOTE.  a2kit multiplies the deck tile by ART_DK (#4c4c4c) because an
up-facing surface over-collects in this scene.  The four `.deck` tiles are
authored for that: the black decks sit at mean ~70-95 rather than the photo's
~25, or they crush to zero after the multiply.  `.side` / `.front` are authored
at true albedo for a near-white material (ART, #ffffff): black cabinets are
authored BLACK.  Authoring every tile at a2kit's ~236 mean is part of why round
3's run read as sixteen coloured boxes.

BEZELS: no `.bezel` tiles are exported.  A screen surround differing only in
trim hue between machines is exactly the defect this round exists to remove.
Use a plain dark untextured material (~#15151a) for bezels.
"""

import math

TILE = 256

# Fine random grain on top of the ordered dither.  OFF: it costs 37% of the
# atlas PNG and the dither alone already meters |d1| 7-14 at texel scale.
GRAIN = False

_BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]

# quad width / height in FEET, from ar2.py's own row for each machine:
#   side    = (bd + DECK_OUT) / top        = 2.95 / top
#   marquee = (bw - 0.12) / mqh
#   front   = (bw - 0.16) / (dy - 0.62 - 0.16)
#   deck    = (bw - 0.12) / 0.92
ASPECT = {
    # EAST_RUN[0]  bw 2.34  top 6.28  dy 2.56  mqh 0.70
    "star-wars-atari.side": 2.95 / 6.28,
    "star-wars-atari.marquee": 2.22 / 0.70,
    "star-wars-atari.front": 2.18 / 1.78,
    "star-wars-atari.deck": 2.22 / 0.92,
    # EAST_RUN[4]  bw 2.30  top 6.22  dy 2.54  mqh 0.66
    "nba-jam.side": 2.95 / 6.22,
    "nba-jam.marquee": 2.18 / 0.66,
    "nba-jam.front": 2.14 / 1.76,
    "nba-jam.deck": 2.18 / 0.92,
    # SOUTH_RUN[1]  bw 2.42  top 6.02  dy 2.46  mqh 0.58
    "street-fighter-2-champion-edition.side": 2.95 / 6.02,
    "street-fighter-2-champion-edition.marquee": 2.30 / 0.58,
    "street-fighter-2-champion-edition.front": 2.26 / 1.68,
    "street-fighter-2-champion-edition.deck": 2.30 / 0.92,
    # NORTH_RUN[0]  bw 2.44  top 6.20  dy 2.56  mqh 0.72
    "north-1-graffiti-multicade.side": 2.95 / 6.20,
    "north-1-graffiti-multicade.marquee": 2.32 / 0.72,
    "north-1-graffiti-multicade.front": 2.28 / 1.78,
    "north-1-graffiti-multicade.deck": 2.32 / 0.92,

    # ---- ROUND 5.  Three machines moved into this module for the wrap round
    # (see WRAP_R5 at the foot of the file).  Only .side / .front / .deck are
    # claimed -- and .bezel for Golden Tee, which has a real lit feature there.
    # Their MARQUEES stay where round 4 drew them (art_g1 / art_g3): round 4's
    # marquees work and this round is everything BELOW the marquee.
    # NORTH_RUN[1]  bw 2.28  top 6.34  dy 2.50  mqh 0.64  plinth 0.10
    "pac-man.side": 2.95 / 6.34,
    "pac-man.front": 2.12 / 1.72,
    "pac-man.deck": 2.16 / 0.92,
    # EAST_RUN[5]   bw 2.04  top 5.78  dy 2.40  mqh 0.52  plinth 0.08
    "tmnt-turtles-in-time.side": 2.95 / 5.78,
    "tmnt-turtles-in-time.front": 1.88 / 1.62,
    "tmnt-turtles-in-time.deck": 1.92 / 0.92,
    # NORTH_RUN[3]  bw 2.32  top 6.26  dy 2.54  mqh 0.68  plinth 0.06
    "golden-tee-3d-golf.side": 2.95 / 6.26,
    "golden-tee-3d-golf.front": 2.16 / 1.76,
    "golden-tee-3d-golf.deck": 2.20 / 0.92,
    # bezel quad: (bw - 0.10) / (mq_lo - 0.10 - (dy + 0.30)) = 2.22 / 2.46
    "golden-tee-3d-golf.bezel": 2.22 / 2.46,
}


# ------------------------------------------------------------------ colours
def _c(v):
    if isinstance(v, str):
        s = v.lstrip("#")
        return (float(int(s[0:2], 16)), float(int(s[2:4], 16)),
                float(int(s[4:6], 16)))
    return (float(v[0]), float(v[1]), float(v[2]))


def _mix(a, b, t):
    a, b = _c(a), _c(b)
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t,
            a[2] + (b[2] - a[2]) * t)


def _q8(v):
    v = int(round(v / 8.0)) * 8
    return 0 if v < 0 else (255 if v > 255 else v)


class _Rnd(object):
    """Deterministic LCG -- the artwork must be byte-identical every run."""

    def __init__(self, seed):
        self.s = (seed * 1103515245 + 12345) & 0x7FFFFFFF

    def u(self):
        self.s = (self.s * 1103515245 + 12345) & 0x7FFFFFFF
        return self.s / 2147483648.0

    def f(self, a, b):
        return a + (b - a) * self.u()

    def i(self, a, b):
        return int(self.f(a, b + 0.999999))


# ------------------------------------------------------------------- canvas
class _Cv(object):
    """A panel with SQUARE pixels, drawn in unit coordinates.

    u right, v DOWN.  Positions are fractions of the panel's own width and
    height; LENGTHS are fractions of its HEIGHT, so a stroke keeps the same
    physical weight whichever way it runs.  `kx` turns a length into u-units.
    """

    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.s = float(h)               # isotropic length scale, in pixels
        self.kx = self.s / float(w)     # length -> u-units
        self.b = [[[0.0, 0.0, 0.0] for _ in range(w)] for _ in range(h)]

    def X(self, u):
        return u * self.w

    def Y(self, v):
        return v * self.h

    def L(self, d):
        return d * self.s

    # ---- primitives -----------------------------------------------------
    def _bl(self, px, col, a):
        if a <= 0.0:
            return
        if a > 1.0:
            a = 1.0
        px[0] += (col[0] - px[0]) * a
        px[1] += (col[1] - px[1]) * a
        px[2] += (col[2] - px[2]) * a

    def fill(self, col):
        col = _c(col)
        for row in self.b:
            for p in row:
                p[0], p[1], p[2] = col

    def rect(self, u0, v0, u1, v1, col, a=1.0):
        self.poly([(u0, v0), (u1, v0), (u1, v1), (u0, v1)], col, a)

    def vgrad(self, u0, v0, u1, v1, ctop, cbot, a=1.0):
        ctop, cbot = _c(ctop), _c(cbot)
        yt, yb = self.Y(v0), self.Y(v1)
        y0 = max(0, int(yt))
        y1 = min(self.h - 1, int(math.ceil(yb)) - 1)
        x0 = max(0, int(self.X(u0)))
        x1 = min(self.w - 1, int(math.ceil(self.X(u1))) - 1)
        span = max(1e-6, yb - yt)
        for y in range(y0, y1 + 1):
            t = min(1.0, max(0.0, (y + 0.5 - yt) / span))
            col = (ctop[0] + (cbot[0] - ctop[0]) * t,
                   ctop[1] + (cbot[1] - ctop[1]) * t,
                   ctop[2] + (cbot[2] - ctop[2]) * t)
            row = self.b[y]
            for x in range(x0, x1 + 1):
                self._bl(row[x], col, a)

    def hgrad(self, u0, v0, u1, v1, cl, cr, a=1.0):
        cl, cr = _c(cl), _c(cr)
        y0 = max(0, int(self.Y(v0)))
        y1 = min(self.h - 1, int(math.ceil(self.Y(v1))) - 1)
        xl, xr = self.X(u0), self.X(u1)
        x0 = max(0, int(xl))
        x1 = min(self.w - 1, int(math.ceil(xr)) - 1)
        span = max(1e-6, xr - xl)
        for x in range(x0, x1 + 1):
            t = min(1.0, max(0.0, (x + 0.5 - xl) / span))
            col = (cl[0] + (cr[0] - cl[0]) * t, cl[1] + (cr[1] - cl[1]) * t,
                   cl[2] + (cr[2] - cl[2]) * t)
            for y in range(y0, y1 + 1):
                self._bl(self.b[y][x], col, a)

    def poly(self, pts, col, a=1.0):
        """Even-odd scanline fill, two sub-scanlines, exact x coverage."""
        col = _c(col)
        P = [(self.X(p[0]), self.Y(p[1])) for p in pts]
        m = len(P)
        if m < 3:
            return
        W = self.w
        ys = [p[1] for p in P]
        y0 = max(0, int(math.floor(min(ys))))
        y1 = min(self.h - 1, int(math.ceil(max(ys))))
        for py in range(y0, y1 + 1):
            cov = None
            for sub in (0.25, 0.75):
                sy = py + sub
                xs = []
                for i in range(m):
                    ax, ay = P[i]
                    bx, by = P[(i + 1) % m]
                    if (ay <= sy < by) or (by <= sy < ay):
                        xs.append(ax + (bx - ax) * (sy - ay) / (by - ay))
                if not xs:
                    continue
                xs.sort()
                if cov is None:
                    cov = [0.0] * W
                for k in range(0, len(xs) - 1, 2):
                    xa, xb = xs[k], xs[k + 1]
                    if xb <= 0.0 or xa >= W:
                        continue
                    xa = max(xa, 0.0)
                    xb = min(xb, float(W))
                    ia = int(xa)
                    ib = min(W - 1, int(math.ceil(xb)) - 1)
                    if ia >= ib:
                        cov[ia] += (xb - xa) * 0.5
                    else:
                        cov[ia] += (ia + 1 - xa) * 0.5
                        for xi in range(ia + 1, ib):
                            cov[xi] += 0.5
                        cov[ib] += (xb - ib) * 0.5
            if cov is None:
                continue
            row = self.b[py]
            for xi in range(W):
                cvv = cov[xi]
                if cvv > 0.002:
                    self._bl(row[xi], col, min(1.0, cvv) * a)

    def seg(self, p0, p1, col, w, a=1.0):
        """A stroke with SQUARE caps -- block caps want butt ends, not discs."""
        col = _c(col)
        x0, y0 = self.X(p0[0]), self.Y(p0[1])
        x1, y1 = self.X(p1[0]), self.Y(p1[1])
        hw = max(0.35, self.L(w) * 0.5)
        dx, dy = x1 - x0, y1 - y0
        ln = math.hypot(dx, dy)
        lo_x = max(0, int(min(x0, x1) - hw - 1.5))
        hi_x = min(self.w - 1, int(max(x0, x1) + hw + 1.5))
        lo_y = max(0, int(min(y0, y1) - hw - 1.5))
        hi_y = min(self.h - 1, int(max(y0, y1) + hw + 1.5))
        if ln < 1e-6:
            for py in range(lo_y, hi_y + 1):
                row = self.b[py]
                for px_ in range(lo_x, hi_x + 1):
                    d = max(abs(px_ + 0.5 - x0), abs(py + 0.5 - y0))
                    self._bl(row[px_], col,
                             min(1.0, max(0.0, 0.5 + hw - d)) * a)
            return
        ux, uy = dx / ln, dy / ln
        for py in range(lo_y, hi_y + 1):
            fy = py + 0.5
            row = self.b[py]
            for px_ in range(lo_x, hi_x + 1):
                fx = px_ + 0.5
                t = (fx - x0) * ux + (fy - y0) * uy
                perp = abs((fx - x0) * (-uy) + (fy - y0) * ux)
                over = t - ln if t > ln else (-t if t < 0.0 else 0.0)
                d = perp if perp > over else over
                cvv = 0.5 + hw - d
                if cvv > 0.0:
                    self._bl(row[px_], col, min(1.0, cvv) * a)

    def stroke(self, pts, col, w, closed=False, a=1.0):
        m = len(pts)
        rng = range(m) if closed else range(m - 1)
        for i in rng:
            self.seg(pts[i], pts[(i + 1) % m], col, w, a)

    def taper(self, p0, p1, w0, w1, col, a=1.0):
        """A stroke that narrows; widths are LENGTHS, so it stays isotropic."""
        x0, y0 = self.X(p0[0]), self.Y(p0[1])
        x1, y1 = self.X(p1[0]), self.Y(p1[1])
        dx, dy = x1 - x0, y1 - y0
        ln = math.hypot(dx, dy)
        if ln < 1e-9:
            return
        nx, ny = -dy / ln, dx / ln
        h0 = self.L(w0) * 0.5
        h1 = self.L(w1) * 0.5
        pts = [(x0 + nx * h0, y0 + ny * h0), (x1 + nx * h1, y1 + ny * h1),
               (x1 - nx * h1, y1 - ny * h1), (x0 - nx * h0, y0 - ny * h0)]
        self.poly([(p[0] / self.w, p[1] / self.h) for p in pts], col, a)

    # ---- conics (radii are LENGTHS) -------------------------------------
    def _ellpts(self, cu, cv, ru, rv, a0=0.0, a1=math.tau, steps=None):
        span = a1 - a0
        if steps is None:
            steps = max(10, int(abs(span) / math.tau * 72) + 4)
        k = self.kx
        return [(cu + ru * k * math.cos(a0 + span * i / float(steps)),
                 cv + rv * math.sin(a0 + span * i / float(steps)))
                for i in range(steps + 1)]

    def ell(self, cu, cv, ru, rv, col, a=1.0):
        self.poly(self._ellpts(cu, cv, ru, rv)[:-1], col, a)

    def ring(self, cu, cv, ru, rv, w, col, a=1.0):
        self.stroke(self._ellpts(cu, cv, ru, rv), col, w, a=a)

    def arc(self, cu, cv, ru, rv, a0, a1, w, col, a=1.0):
        self.stroke(self._ellpts(cu, cv, ru, rv, a0, a1), col, w, a=a)

    def annulus(self, cu, cv, ru, rv, tk, a0, a1, col, a=1.0):
        out = self._ellpts(cu, cv, ru, rv, a0, a1)
        inn = self._ellpts(cu, cv, ru - tk, rv - tk, a1, a0)
        self.poly(out + inn, col, a)

    # ---- text -----------------------------------------------------------
    def glyph(self, ch, xf, w, col, a=1.0):
        for run in _FONT.get(ch.upper(), ()):
            self.stroke([xf(p[0], p[1]) for p in run], col, w, a=a)

    def text(self, s, cu, cv, h, col, w, track=0.14, slant=0.0,
             aspect=0.64, a=1.0, outline=None, ow=0.0, align="c"):
        """`h` is the cap height as a fraction of panel height; `aspect` is the
        glyph's real width/height, so letterforms keep their proportions."""
        k = self.kx
        gw = h * aspect
        adv = gw * (1.0 + track)
        total = (adv * len(s) - (adv - gw)) * k
        if align == "c":
            x = cu - total * 0.5
        elif align == "l":
            x = cu
        else:
            x = cu - total
        top = cv - h * 0.5
        for ch in s:
            if ch != " ":
                def xf(gx, gy, _l=x, _t=top):
                    return (_l + (gx * gw + slant * (1.0 - gy) * h) * k,
                            _t + gy * h)
                if outline is not None:
                    self.glyph(ch, xf, w + ow, outline, a)
                self.glyph(ch, xf, w, col, a)
            x += adv * k
        return total

    def arctext(self, s, cu, cv, ru, rv, a0, a1, h, col, w, a=1.0,
                outline=None, ow=0.0, aspect=0.64):
        """Set `s` around an ellipse; 0 rad = +u and v is DOWN, so angles
        run clockwise on screen."""
        k = self.kx
        m = len(s)
        gw = h * aspect
        for i, ch in enumerate(s):
            if ch == " ":
                continue
            t = (i + 0.5) / float(m)
            ang = a0 + (a1 - a0) * t
            cxl = ru * math.cos(ang)          # centre offset, in LENGTHS
            cyl = rv * math.sin(ang)
            tx, ty = -ru * math.sin(ang), rv * math.cos(ang)
            tl = math.hypot(tx, ty)
            tx, ty = tx / tl, ty / tl
            nx, ny = -ty, tx

            def xf(gx, gy, _cx=cxl, _cy=cyl, _t=(tx, ty), _n=(nx, ny)):
                lx = (gx - 0.5) * gw
                ly = (gy - 0.5) * h
                return (cu + (_cx + _t[0] * lx + _n[0] * ly) * k,
                        cv + (_cy + _t[1] * lx + _n[1] * ly))
            if outline is not None:
                self.glyph(ch, xf, w + ow, outline, a)
            self.glyph(ch, xf, w, col, a)


# A compact uppercase stroke alphabet.  Unit glyph box, y DOWN from the cap
# line.  Round 3's marquees were rectangles standing in for letters; these are
# letters.
_O = [[(0.30, 0.0), (0.70, 0.0), (0.94, 0.24), (0.94, 0.76), (0.70, 1.0),
       (0.30, 1.0), (0.06, 0.76), (0.06, 0.24), (0.30, 0.0)]]
_PP = [[(0.10, 1.0), (0.10, 0.0), (0.70, 0.0), (0.92, 0.18), (0.92, 0.38),
        (0.70, 0.56), (0.10, 0.56)]]
_FONT = {
    "A": [[(0.03, 1.0), (0.50, 0.0), (0.97, 1.0)], [(0.21, 0.62), (0.79, 0.62)]],
    "B": [[(0.10, 0.0), (0.10, 1.0)],
          [(0.10, 0.0), (0.68, 0.0), (0.90, 0.16), (0.90, 0.32), (0.70, 0.48),
           (0.10, 0.48)],
          [(0.10, 0.48), (0.74, 0.48), (0.94, 0.66), (0.94, 0.84), (0.72, 1.0),
           (0.10, 1.0)]],
    "C": [[(0.95, 0.17), (0.76, 0.0), (0.28, 0.0), (0.06, 0.22), (0.06, 0.78),
           (0.28, 1.0), (0.76, 1.0), (0.95, 0.83)]],
    "D": [[(0.10, 0.0), (0.10, 1.0)],
          [(0.10, 0.0), (0.62, 0.0), (0.92, 0.28), (0.92, 0.72), (0.62, 1.0),
           (0.10, 1.0)]],
    "E": [[(0.92, 0.0), (0.10, 0.0), (0.10, 1.0), (0.92, 1.0)],
          [(0.10, 0.50), (0.78, 0.50)]],
    "F": [[(0.92, 0.0), (0.10, 0.0), (0.10, 1.0)], [(0.10, 0.50), (0.76, 0.50)]],
    "G": [[(0.95, 0.17), (0.76, 0.0), (0.28, 0.0), (0.06, 0.22), (0.06, 0.78),
           (0.28, 1.0), (0.80, 1.0), (0.95, 0.82), (0.95, 0.56), (0.58, 0.56)]],
    "H": [[(0.10, 0.0), (0.10, 1.0)], [(0.90, 0.0), (0.90, 1.0)],
          [(0.10, 0.52), (0.90, 0.52)]],
    "I": [[(0.50, 0.0), (0.50, 1.0)]],
    "J": [[(0.90, 0.0), (0.90, 0.76), (0.70, 1.0), (0.32, 1.0), (0.10, 0.78)]],
    "K": [[(0.10, 0.0), (0.10, 1.0)], [(0.92, 0.0), (0.14, 0.56)],
          [(0.34, 0.42), (0.94, 1.0)]],
    "L": [[(0.12, 0.0), (0.12, 1.0), (0.92, 1.0)]],
    "M": [[(0.06, 1.0), (0.06, 0.0), (0.50, 0.62), (0.94, 0.0), (0.94, 1.0)]],
    "N": [[(0.10, 1.0), (0.10, 0.0), (0.90, 1.0), (0.90, 0.0)]],
    "O": _O,
    "P": _PP,
    "Q": _O + [[(0.60, 0.72), (1.00, 1.06)]],
    "R": _PP + [[(0.44, 0.56), (0.94, 1.0)]],
    "S": [[(0.94, 0.17), (0.74, 0.0), (0.28, 0.0), (0.08, 0.18), (0.08, 0.36),
           (0.28, 0.50), (0.74, 0.50), (0.94, 0.64), (0.94, 0.82), (0.74, 1.0),
           (0.26, 1.0), (0.06, 0.84)]],
    "T": [[(0.04, 0.0), (0.96, 0.0)], [(0.50, 0.0), (0.50, 1.0)]],
    "U": [[(0.08, 0.0), (0.08, 0.76), (0.30, 1.0), (0.70, 1.0), (0.92, 0.76),
           (0.92, 0.0)]],
    "V": [[(0.04, 0.0), (0.50, 1.0), (0.96, 0.0)]],
    "W": [[(0.02, 0.0), (0.24, 1.0), (0.50, 0.40), (0.76, 1.0), (0.98, 0.0)]],
    "X": [[(0.06, 0.0), (0.94, 1.0)], [(0.94, 0.0), (0.06, 1.0)]],
    "Y": [[(0.06, 0.0), (0.50, 0.52), (0.94, 0.0)], [(0.50, 0.52), (0.50, 1.0)]],
    "Z": [[(0.06, 0.0), (0.94, 0.0), (0.06, 1.0), (0.94, 1.0)]],
    "1": [[(0.28, 0.20), (0.52, 0.0), (0.52, 1.0)], [(0.22, 1.0), (0.82, 1.0)]],
    "2": [[(0.08, 0.20), (0.28, 0.0), (0.72, 0.0), (0.92, 0.20), (0.92, 0.36),
           (0.10, 1.0), (0.94, 1.0)]],
    "3": [[(0.08, 0.16), (0.30, 0.0), (0.72, 0.0), (0.92, 0.18), (0.72, 0.46),
           (0.36, 0.46)], [(0.72, 0.46), (0.94, 0.66), (0.94, 0.82),
                           (0.72, 1.0), (0.28, 1.0), (0.06, 0.84)]],
    "-": [[(0.14, 0.52), (0.86, 0.52)]],
    ".": [[(0.44, 0.94), (0.58, 0.94)]],
    "'": [[(0.50, 0.0), (0.50, 0.26)]],
    " ": [],
}


# ------------------------------------------------------- flush + decorator
def _flush(px, ox, oy, tile, cv):
    """Resample the aspect-correct buffer into the square tile, dither, quantise."""
    W, H = cv.w, cv.h
    b = cv.b
    xs = []
    for x in range(tile):
        fx = (x + 0.5) * W / float(tile) - 0.5
        i0 = int(math.floor(fx))
        t = fx - i0
        if i0 < 0:
            i0, t = 0, 0.0
        elif i0 > W - 2:
            i0, t = max(0, W - 2), 1.0 if W > 1 else 0.0
        xs.append((i0, min(i0 + 1, W - 1), t))
    for y in range(tile):
        fy = (y + 0.5) * H / float(tile) - 0.5
        j0 = int(math.floor(fy))
        s = fy - j0
        if j0 < 0:
            j0, s = 0, 0.0
        elif j0 > H - 2:
            j0, s = max(0, H - 2), 1.0 if H > 1 else 0.0
        r0 = b[j0]
        r1 = b[min(j0 + 1, H - 1)]
        out = px[oy + y]
        by = _BAYER[y & 3]
        for x in range(tile):
            i0, i1, t = xs[x]
            # ROUND 5: 0.90 -> 0.55.  atlas4 supersamples 2x, box-averages
            # and re-quantises to 16 levels, so most of this dither is
            # destroyed before it ships and only its cost survives.
            # MEASURED over art_g0's 17 panels: 0.90 = 48.0 KB,
            # 0.70 = 48.0, 0.55 = 47.4, 0.30 = 46.5, 0.00 = 45.1, and no
            # banding appears in the preview sheet down to 0.55.
            n = (by[x & 3] - 7.5) * 0.55
            a0 = r0[i0]
            a1 = r0[i1]
            c0 = r1[i0]
            c1 = r1[i1]
            top0 = a0[0] + (a1[0] - a0[0]) * t
            top1 = a0[1] + (a1[1] - a0[1]) * t
            top2 = a0[2] + (a1[2] - a0[2]) * t
            bot0 = c0[0] + (c1[0] - c0[0]) * t
            bot1 = c0[1] + (c1[1] - c0[1]) * t
            bot2 = c0[2] + (c1[2] - c0[2]) * t
            out[ox + x] = (_q8(top0 + (bot0 - top0) * s + n),
                           _q8(top1 + (bot1 - top1) * s + n),
                           _q8(top2 + (bot2 - top2) * s + n))


_REG = {}


def _panel(key):
    """Bind a paint function to its quad aspect from ASPECT."""
    def deco(fn):
        def paint(px, ox, oy, tile):
            a = ASPECT[key]
            root = math.sqrt(a)
            w = max(48, int(round(tile * root)))
            h = max(48, int(round(tile / root)))
            cv = _Cv(w, h)
            fn(cv)
            _flush(px, ox, oy, tile, cv)
        paint.__name__ = fn.__name__
        paint.key = key
        _REG[key] = paint
        return paint
    return deco


# ---------------------------------------------------------------- textures
def _sheen(cv, u0, v0, u1, v1, amp, seed, n=5):
    """Broad soft vinyl sheen -- large-scale, so it never reads as noise."""
    r = _Rnd(seed)
    for _ in range(n):
        cu = r.f(u0, u1)
        w = r.f(0.10, 0.34)
        col = (255.0, 255.0, 255.0) if r.u() > 0.35 else (0.0, 0.0, 0.0)
        for k in range(7):
            t = (k + 0.5) / 7.0
            aa = (amp / 255.0) * (1.0 - abs(t - 0.5) * 2.0) ** 1.4
            cv.rect(cu - w * 0.5 + w * t, v0,
                    cu - w * 0.5 + w * (t + 1.0 / 7.0), v1, col, aa)


def _grain(cv, amp, seed, cell=0.020):
    """Fine printed-vinyl grain.  OFF by default -- see GRAIN above."""
    if not GRAIN:
        return
    r = _Rnd(seed)
    step = cell * cv.kx
    v = 0.0
    while v < 1.0:
        u = 0.0
        while u < 1.0:
            k = r.f(-amp, amp)
            col = (255.0, 255.0, 255.0) if k > 0 else (0.0, 0.0, 0.0)
            cv.rect(u, v, min(u + step, 1.0), min(v + cell, 1.0), col,
                    abs(k) / 255.0)
            u += step
        v += cell


# ------------------------------------------------ round-5 wrap primitives
# Shared by the four machines wrapped in ROUND 5.  Every one of them is a
# LARGE-SCALE printed form -- a plate, a course of bricks, a run of boards --
# because the defect being fixed is "flat panel with a small logo floated on
# it", and because fine noise is what the payload cannot afford.


def _rr(cv, u0, v0, u1, v1, r, col, a=1.0):
    """Rounded rectangle.  `r` is a LENGTH (fraction of panel height)."""
    k = cv.kx
    rx = r * k
    pts = []
    for (cu, cvv, a0) in ((u1 - rx, v0 + r, -math.pi * 0.5),
                          (u1 - rx, v1 - r, 0.0),
                          (u0 + rx, v1 - r, math.pi * 0.5),
                          (u0 + rx, v0 + r, math.pi)):
        for i in range(6):
            aa = a0 + math.pi * 0.5 * i / 5.0
            pts.append((cu + rx * math.cos(aa), cvv + r * math.sin(aa)))
    cv.poly(pts, col, a)


def _plate(cv, u0, v0, u1, v1, r, face, lip_hi, lip_lo, t=0.012):
    """A coin-door style plate: a bevelled bezel with a recessed face."""
    _rr(cv, u0, v0, u1, v1, r, lip_lo)
    _rr(cv, u0, v0, u1 - t * cv.kx, v1 - t, r, lip_hi)
    _rr(cv, u0 + t * cv.kx, v0 + t, u1 - t * cv.kx, v1 - t, max(0.001, r - t),
        face)


def _pebble(cv, u0, v0, u1, v1, step, hi, lo, seed, a=0.55):
    """Basketball-leather / diamond-plate grain: an offset grid of bumps."""
    k = cv.kx
    r = _Rnd(seed)
    v = v0 + step * 0.5
    row = 0
    while v < v1:
        u = u0 + (step * k * 0.5 if row % 2 else step * k * 0.1)
        while u < u1:
            rr = step * 0.34 + r.f(-step * 0.06, step * 0.06)
            cv.ell(u, v, rr, rr, hi, a)
            cv.ell(u + step * 0.10 * k, v + step * 0.11, rr * 0.70, rr * 0.70,
                   lo, a * 0.72)
            u += step * k
        v += step * 0.86
        row += 1


def _bricks(cv, u0, v0, u1, v1, rows, face, edge, mortar, seed, a=1.0,
            jitter=10.0):
    """Running-bond brick, drawn as courses so it costs almost nothing."""
    k = cv.kx
    cv.rect(u0, v0, u1, v1, mortar, a)
    r = _Rnd(seed)
    hgt = (v1 - v0) / float(rows)
    bw = hgt * 2.35 * k
    for j in range(rows):
        vy = v0 + j * hgt
        u = u0 - (bw * 0.5 if j % 2 else 0.0)
        while u < u1:
            f = _mix(face, edge, max(0.0, min(1.0, 0.5 + r.f(-1.0, 1.0) *
                                              jitter / 255.0)))
            cv.rect(max(u0, u + bw * 0.045), vy + hgt * 0.10,
                    min(u1, u + bw * 0.955), vy + hgt * 0.86, f, a)
            u += bw


def _boards(cv, u0, v0, u1, v1, n, warm, cool, line, seed):
    """Hardwood planks running ACROSS the panel."""
    r = _Rnd(seed)
    hgt = (v1 - v0) / float(n)
    for j in range(n):
        vy = v0 + j * hgt
        t = 0.5 + r.f(-0.5, 0.5)
        cv.rect(u0, vy, u1, min(v1, vy + hgt), _mix(warm, cool, t))
        cv.seg((u0, vy), (u1, vy), line, hgt * 0.16, 0.55)


def _wear(cv, u0, v0, u1, v1, amp, seed, n=4, vert=True):
    """A few broad soft bands -- printed vinyl reads as sheen, not as noise."""
    r = _Rnd(seed)
    for _ in range(n):
        c = r.f(u0, u1) if vert else r.f(v0, v1)
        w = r.f(0.10, 0.30) * ((u1 - u0) if vert else (v1 - v0))
        col = (255.0, 255.0, 255.0) if r.u() > 0.42 else (0.0, 0.0, 0.0)
        for j in range(5):
            t = (j + 0.5) / 5.0
            aa = (amp / 255.0) * (1.0 - abs(t - 0.5) * 2.0) ** 1.3
            if vert:
                cv.rect(c - w * 0.5 + w * t, v0,
                        c - w * 0.5 + w * (t + 0.2), v1, col, aa)
            else:
                cv.rect(u0, c - w * 0.5 + w * t,
                        u1, c - w * 0.5 + w * (t + 0.2), col, aa)


def _burst(cv, cu, cvv, ru, spikes, col, w0=0.05, phase=0.16, ratio=0.62,
           a=1.0):
    """A spiked starburst -- NBA Jam's front and riser both carry one."""
    k = cv.kx
    for j in range(spikes):
        aa = math.tau * j / float(spikes) + phase
        rr = ru if j % 2 == 0 else ru * ratio
        cv.taper((cu, cvv), (cu + rr * k * math.cos(aa),
                             cvv + rr * math.sin(aa)), w0, 0.006, col, a)


def _window_rows(cv, u0, v0, u1, v1, cols, rows, lit, dark, seed, p=0.42):
    """A grid of building windows, some lit -- the TMNT city artwork."""
    r = _Rnd(seed)
    cw = (u1 - u0) / float(cols)
    ch = (v1 - v0) / float(rows)
    for j in range(rows):
        for i in range(cols):
            u = u0 + i * cw
            v = v0 + j * ch
            cv.rect(u + cw * 0.22, v + ch * 0.20, u + cw * 0.78, v + ch * 0.74,
                    lit if r.u() < p else dark)


def _inpoly(pts, u, v):
    inside = False
    m = len(pts)
    for i in range(m):
        ax, ay = pts[i]
        bx, by = pts[(i + 1) % m]
        if (ay > v) != (by > v):
            xx = ax + (bx - ax) * (v - ay) / (by - ay)
            if xx > u:
                inside = not inside
    return inside


def _stars(cv, poly_pts, seed, count, col="#f4f6ff"):
    r = _Rnd(seed)
    us = [p[0] for p in poly_pts]
    vs = [p[1] for p in poly_pts]
    for _ in range(count):
        u = r.f(min(us), max(us))
        v = r.f(min(vs), max(vs))
        if not _inpoly(poly_pts, u, v):
            continue
        rr = r.f(0.0016, 0.0052)
        cv.ell(u, v, rr, rr, col, r.f(0.45, 1.0))


# =========================================================================
#  1.  STAR WARS  (Atari, 1983 upright)  --  EAST_RUN[0]
# =========================================================================
# Evidence: v4 9 px (150,220)-(300,480) and v4 8 px (0,90)-(140,340).  The
# flank is the identifying surface and is unmistakable: a golden-yellow carcase
# with a BLACK stepped / chevron art panel inset into it, a wide band of bare
# yellow all round, white-line TIE fighters and stars over the top half, a
# blue-grey X-wing low and forward, the Death Star's surface curve along the
# bottom third and a small rectangular inset panel at the lower rear.
#
# The sweep's flank UV runs u = 0 at the BACK of the profile to u = 1 at the
# control-deck front, v = 0 at the top.  Above the deck the carcase front only
# reaches u ~ 0.65 and below it u ~ 0.76, so nothing is authored past 0.74 --
# anything further forward would fall outside the flank polygon and never draw.

_SW_YEL = "#d8c92e"          # hue ~55 deg; the photo's #969129 is a SHADED read
_SW_YEL_D = "#a89c24"
_SW_BLK = "#14111c"

_SW_PANEL = [
    (0.070, 0.940), (0.070, 0.265), (0.098, 0.185), (0.170, 0.126),
    (0.300, 0.096), (0.470, 0.080), (0.545, 0.088), (0.596, 0.122),
    (0.614, 0.180), (0.612, 0.318),                       # rounded top-front
    (0.470, 0.392), (0.372, 0.446),                       # the chevron step in
    (0.470, 0.492), (0.596, 0.548), (0.618, 0.606),       # and back out
    (0.706, 0.652),                                       # flare below the deck
    (0.724, 0.940),
]


def _tie(cv, cu, cvv, s, col, w):
    """A TIE fighter in white line: ball cockpit, struts, hexagonal panels."""
    k = cv.kx
    cv.ring(cu, cvv, s * 0.20, s * 0.20, w, col)
    cv.seg((cu - s * 0.20 * k, cvv), (cu - s * 0.52 * k, cvv), col, w)
    cv.seg((cu + s * 0.20 * k, cvv), (cu + s * 0.52 * k, cvv), col, w)
    for sgn in (-1.0, 1.0):
        hx = cu + sgn * s * 0.78 * k
        d = s * 0.26 * k
        e = s * 0.30 * k
        hexa = [(hx - d, cvv - s * 0.52), (hx + d, cvv - s * 0.62),
                (hx + e, cvv), (hx + d, cvv + s * 0.62),
                (hx - d, cvv + s * 0.52), (hx - e, cvv)]
        cv.stroke(hexa, col, w, closed=True)
        cv.seg((hx, cvv - s * 0.55), (hx, cvv + s * 0.55), col, w * 0.7)


def _vader(cv, cu, cvv, s):
    """Vader's helmet: dome, flared cheeks, angular lenses, mouth grille.
    `s` is the helmet height as a LENGTH; it is printed dark-on-dark in the
    photograph, so it is drawn at low contrast on purpose."""

    def P(dx, dy):
        return (cu + dx * s * cv.kx, cvv + dy * s)
    D = "#2c3550"
    DD = "#1b2138"
    RIM = "#5a6b8e"
    LENS = "#0c0f1a"
    # flared shoulder / cape line first, behind the helmet
    cv.poly([P(-0.86, 0.44), P(-0.40, 0.26), P(0.40, 0.26), P(0.86, 0.44),
             P(0.94, 0.62), P(-0.94, 0.62)], DD)
    # the helmet dome and the flared side panels
    cv.poly([P(0.0, -0.52), P(0.27, -0.46), P(0.42, -0.24), P(0.46, 0.02),
             P(0.56, 0.20), P(0.44, 0.34), P(0.24, 0.46), P(0.0, 0.50),
             P(-0.24, 0.46), P(-0.44, 0.34), P(-0.56, 0.20), P(-0.46, 0.02),
             P(-0.42, -0.24), P(-0.27, -0.46)], D)
    cv.stroke([P(0.0, -0.52), P(0.27, -0.46), P(0.42, -0.24), P(0.46, 0.02),
               P(0.56, 0.20), P(0.44, 0.34), P(0.24, 0.46), P(0.0, 0.50),
               P(-0.24, 0.46), P(-0.44, 0.34), P(-0.56, 0.20), P(-0.46, 0.02),
               P(-0.42, -0.24), P(-0.27, -0.46)], RIM, s * 0.030, closed=True,
              a=0.75)
    # brow ridge
    cv.poly([P(-0.44, -0.10), P(-0.30, -0.22), P(0.30, -0.22), P(0.44, -0.10),
             P(0.36, -0.03), P(-0.36, -0.03)], DD)
    cv.stroke([P(-0.44, -0.10), P(-0.30, -0.22), P(0.30, -0.22), P(0.44, -0.10)],
              RIM, s * 0.026, a=0.7)
    # the two angular eye lenses
    for sg in (-1.0, 1.0):
        cv.poly([P(sg * 0.10, -0.02), P(sg * 0.38, -0.05), P(sg * 0.40, 0.10),
                 P(sg * 0.12, 0.12)], LENS)
        cv.stroke([P(sg * 0.10, -0.02), P(sg * 0.38, -0.05), P(sg * 0.40, 0.10),
                   P(sg * 0.12, 0.12)], RIM, s * 0.024, closed=True, a=0.65)
    # nose triangle and the mouth grille
    cv.poly([P(0.0, 0.02), P(0.09, 0.22), P(-0.09, 0.22)], DD)
    cv.poly([P(-0.22, 0.24), P(0.22, 0.24), P(0.17, 0.42), P(-0.17, 0.42)], DD)
    for j in range(4):
        yy = 0.27 + j * 0.045
        cv.seg(P(-0.20 + j * 0.008, yy), P(0.20 - j * 0.008, yy), RIM,
               s * 0.020, 0.6)
    # the round breather discs on the cheeks
    for sg in (-1.0, 1.0):
        cv.ell(P(sg * 0.40, 0.0)[0], cvv + 0.26 * s, s * 0.085, s * 0.085,
               DD)
        cv.ring(P(sg * 0.40, 0.0)[0], cvv + 0.26 * s, s * 0.085, s * 0.085,
                s * 0.022, RIM, 0.6)


def _xwing(cv, cu, cvv, s, body, edge, hi):
    """Three-quarter X-wing.  The four s-foils have to open into a visible X --
    an earlier pass swept them all the same way and the ship read as a paper
    dart."""

    def P(dx, dy):
        return (cu + dx * s * cv.kx, cvv + dy * s)
    # s-foils: four distinct angles off the mid-body, cannons out at the tips
    for (wx, wy) in ((-1.05, -0.86), (-0.66, -0.34), (-0.66, 0.34),
                     (-1.05, 0.86)):
        root = P(0.10, wy * 0.16)
        tip = P(wx, wy)
        cv.taper(root, tip, s * 0.20, s * 0.13, body)
        cv.taper(root, tip, s * 0.06, s * 0.035, hi, 0.5)
        # engine nacelle sitting on the wing, and the cannon barrel past it
        nac0 = P(wx * 0.52 + 0.10, wy * 0.60)
        nac1 = P(wx * 0.92, wy * 0.96)
        cv.taper(nac0, nac1, s * 0.19, s * 0.17, edge)
        cv.taper(nac0, nac1, s * 0.07, s * 0.05, hi, 0.45)
        cv.ell(nac1[0], nac1[1], s * 0.085, s * 0.085, "#20242e")
        cv.taper(tip, P(wx + 0.86, wy * 1.02), s * 0.055, s * 0.030, edge)
    # fuselage, nose forward, then the canopy
    cv.poly([P(1.28, 0.0), P(0.72, -0.15), P(-0.30, -0.21), P(-0.62, -0.08),
             P(-0.62, 0.10), P(-0.30, 0.23), P(0.72, 0.17)], body)
    cv.poly([P(1.28, 0.0), P(0.66, -0.11), P(0.66, 0.03)], hi)
    cv.seg(P(0.66, -0.13), P(-0.34, -0.17), edge, s * 0.050)
    cv.poly([P(0.34, -0.15), P(-0.06, -0.20), P(-0.18, -0.06), P(0.26, -0.03)],
            "#cfe0f2")                                      # canopy
    cv.taper(P(-0.62, 0.0), P(-0.86, 0.0), s * 0.30, s * 0.22, edge)  # thruster


@_panel("star-wars-atari.side")
def _sw_side(cv):
    k = cv.kx
    # --- carcase: golden yellow, cooler and darker toward the foot
    cv.fill(_SW_YEL)
    cv.vgrad(0.0, 0.0, 1.0, 1.0, "#ded23a", _SW_YEL_D)
    _sheen(cv, 0.0, 0.0, 1.0, 1.0, 12.0, 41, 4)
    cv.rect(0.0, 0.0, 0.030, 1.0, "#6d6417", 0.85)        # T-molding returns
    cv.rect(0.0, 0.984, 1.0, 1.0, "#6d6417", 0.7)

    # --- the black art panel, cut to the machine's own stepped silhouette
    cv.poly([(p[0] + 0.010, p[1] + 0.005) for p in _SW_PANEL], "#5e5714", 0.55)
    cv.poly(_SW_PANEL, _SW_BLK)
    cv.stroke(_SW_PANEL, "#8e93a8", 0.0035, closed=True, a=0.75)
    cv.vgrad(0.05, 0.06, 0.75, 0.96, "#1a1726", "#0b0a12", 0.55)

    # --- starfield over the upper half
    _stars(cv, _SW_PANEL, 91, 300)

    # --- two TIE fighters in white line, and a distant third
    _tie(cv, 0.212, 0.186, 0.076, "#e8ecf6", 0.0040)
    _tie(cv, 0.436, 0.146, 0.056, "#d6dcea", 0.0032)
    _tie(cv, 0.328, 0.268, 0.027, "#9aa2b4", 0.0022)

    # --- Vader's helmet, the thing that makes this panel unmistakable.  It is
    # in v4 8 (the flank at px 0,90-140,340) and again in v4 9, printed dark
    # blue on black and deliberately low contrast, so it is drawn that way and
    # NOT lifted to read like a poster.
    _vader(cv, 0.238, 0.408, 0.205)

    # --- Death Star: the planet limb curving across the bottom third
    DSU, DSV, DSR = 0.360, 1.190, 0.400
    limb = cv._ellpts(DSU, DSV, DSR, DSR, math.pi * 1.02, math.pi * 1.98)
    cv.poly(limb + [(limb[-1][0], 1.05), (limb[0][0], 1.05)], "#26364c", 0.92)
    for j in range(4):                                    # surface banding
        t = j / 3.0
        cv.arc(DSU, DSV, DSR - 0.035 - t * 0.075, DSR - 0.035 - t * 0.075,
               math.pi * (1.06 + t * 0.05), math.pi * (1.94 - t * 0.05),
               0.0055, _mix("#40566f", "#7d92ad", 1.0 - t), 0.75)
    cv.arc(DSU, DSV, DSR, DSR, math.pi * 1.02, math.pi * 1.98, 0.0045,
           "#a6bacd", 0.95)                               # the lit limb
    for j in range(13):                                   # radial panel lines
        aa = math.pi * (1.05 + 0.0742 * j)
        cv.seg((DSU + DSR * k * math.cos(aa), DSV + DSR * math.sin(aa)),
               (DSU + (DSR - 0.115) * k * math.cos(aa),
                DSV + (DSR - 0.115) * math.sin(aa)), "#647a92", 0.0032, 0.65)
    cv.arc(0.205, 1.048, 0.115, 0.115, math.pi * 1.10, math.pi * 1.90, 0.0040,
           "#8ea4bb", 0.85)                               # the trench notch

    # --- the X-wing, low and forward, and a smaller ship behind it
    _xwing(cv, 0.448, 0.632, 0.104, "#9db2c8", "#5d6f86", "#e2ecf6")
    _xwing(cv, 0.236, 0.752, 0.052, "#6e8196", "#465468", "#b7c6d6")

    # --- the small rectangular inset panel at the lower rear
    cv.rect(0.100, 0.792, 0.268, 0.884, "#7f8798", 0.9)
    cv.rect(0.110, 0.799, 0.258, 0.877, "#161a24")
    cv.arc(0.184, 0.886, 0.080, 0.080, math.pi * 1.14, math.pi * 1.86, 0.0035,
           "#6d7f95", 0.9)
    cv.ell(0.152, 0.828, 0.020, 0.014, "#c8d6e6", 0.75)
    cv.seg((0.122, 0.860), (0.246, 0.855), "#54617a", 0.0030, 0.8)
    _grain(cv, 9.0, 5)


@_panel("star-wars-atari.marquee")
def _sw_marquee(cv):
    # NOT VISIBLE in any photograph: in both frames that show this machine the
    # head is cropped or turned away, and it does not read as lit.  So it is
    # built dark and generic ON PURPOSE -- no Atari marquee is invented here.
    cv.fill("#181722")
    cv.vgrad(0.0, 0.0, 1.0, 1.0, "#22212e", "#0e0d14")
    cv.rect(0.0, 0.0, 1.0, 0.070, "#2e2c1a")             # retainer rails
    cv.rect(0.0, 0.930, 1.0, 1.0, "#141320")
    cv.rect(0.0, 0.0, 0.030, 1.0, _SW_YEL_D, 0.85)       # carcase returns
    cv.rect(0.970, 0.0, 1.0, 1.0, _SW_YEL_D, 0.85)
    cv.rect(0.030, 0.070, 0.048, 0.930, "#0b0a10", 0.6)
    cv.rect(0.952, 0.070, 0.970, 0.930, "#0b0a10", 0.6)
    _sheen(cv, 0.06, 0.08, 0.94, 0.92, 8.0, 12, 3)
    _grain(cv, 7.0, 6)


@_panel("star-wars-atari.front")
def _sw_front(cv):
    # NOT VISIBLE either -- the front faces away in both frames.  A plain dark
    # front with the carcase's yellow edge returns is the honest build.
    cv.fill("#1b1920")
    cv.vgrad(0.0, 0.0, 1.0, 1.0, "#232029", "#121017")
    cv.vgrad(0.0, 0.0, 0.052, 1.0, "#c4b62c", "#77700f")
    cv.vgrad(0.948, 0.0, 1.0, 1.0, "#c4b62c", "#77700f")
    cv.rect(0.052, 0.0, 0.070, 1.0, "#0d0c11", 0.7)
    cv.rect(0.930, 0.0, 0.948, 1.0, "#0d0c11", 0.7)
    cv.seg((0.070, 0.415), (0.930, 0.415), "#0a0910", 0.012, 0.8)
    cv.seg((0.070, 0.398), (0.930, 0.398), "#3c3844", 0.004, 0.6)
    _sheen(cv, 0.08, 0.0, 0.92, 1.0, 10.0, 23, 4)
    _grain(cv, 8.0, 7)


@_panel("star-wars-atari.deck")
def _sw_deck(cv):
    # NOT VISIBLE.  Plain black deck, yellow front-edge return along the
    # leading (bottom) edge, two pale wear patches where hands rest.
    cv.fill("#4b4952")
    cv.vgrad(0.0, 0.0, 1.0, 1.0, "#3a3841", "#56545f")
    cv.vgrad(0.0, 0.885, 1.0, 1.0, "#cbbd38", "#8a7f18")
    cv.rect(0.0, 0.850, 1.0, 0.885, "#232028")
    cv.rect(0.0, 0.0, 1.0, 0.070, "#2a2830")
    cv.seg((0.500, 0.075), (0.500, 0.845), "#2b2932", 0.030)   # 1P / 2P split
    cv.seg((0.500, 0.075), (0.500, 0.845), "#63616b", 0.008, 0.55)
    for (a0, b0, a1, b1) in ((0.06, 0.20, 0.94, 0.34),
                             (0.10, 0.62, 0.90, 0.74)):
        cv.taper((a0, b0), (a1, b1), 0.020, 0.008, "#7a7882", 0.16)
    _sheen(cv, 0.0, 0.07, 1.0, 0.84, 14.0, 77, 5)
    _grain(cv, 9.0, 8)


# =========================================================================
#  2.  NBA JAM  --  EAST_RUN[4]
# =========================================================================
# Evidence: v4 7 px (320,150)-(420,205) reads "NBA", the roundel and "JAM"
# directly at 12x; v3 4 px (330,585)-(400,615) agrees.  Cream / tan band, thin
# warm gold rails top and bottom, crimson block caps with a pale gold outline,
# the NBA roundel between the two words, black bezel with small type below.
# The flank carries NO legible graphic at any resolution -- black vinyl with
# deep red T-molding, and it is authored as exactly that.

_NBA_RED = "#b0202f"


def _nba_roundel(cv, cu, cvv, h):
    """The NBA device: blue/red rounded tablet, white dribbling silhouette."""
    k = cv.kx
    w = h * 0.56

    def P(dx, dy):
        return (cu + dx * k, cvv + dy)
    r = w * 0.32
    body = [P(-w * 0.5 + r, -h * 0.5), P(w * 0.5 - r, -h * 0.5),
            P(w * 0.5, -h * 0.5 + r), P(w * 0.5, h * 0.5 - r),
            P(w * 0.5 - r, h * 0.5), P(-w * 0.5 + r, h * 0.5),
            P(-w * 0.5, h * 0.5 - r), P(-w * 0.5, -h * 0.5 + r)]
    cv.poly(body, "#e8e4dc")
    inn = [(p[0] + (cu - p[0]) * 0.12, p[1] + (cvv - p[1]) * 0.07)
           for p in body]
    cv.poly(inn, "#1b3f92")
    cv.poly([p for p in inn if p[0] >= cu] + [P(0.0, h * 0.44),
                                              P(0.0, -h * 0.44)], "#b81f31")
    cv.rect(cu - w * 0.018 * k, cvv - h * 0.46, cu + w * 0.018 * k,
            cvv + h * 0.46, "#e8e4dc", 0.5)
    S = "#f2f0ea"
    cv.ell(P(w * 0.04, 0.0)[0], cvv - h * 0.30, h * 0.062, h * 0.062, S)
    cv.taper(P(w * 0.06, -h * 0.22), P(-w * 0.10, h * 0.06), h * 0.115,
             h * 0.085, S)
    cv.taper(P(w * 0.04, -h * 0.16), P(w * 0.56, -h * 0.02), h * 0.052,
             h * 0.034, S)
    cv.taper(P(-w * 0.08, h * 0.02), P(-w * 0.50, h * 0.22), h * 0.056,
             h * 0.038, S)
    cv.taper(P(-w * 0.06, h * 0.04), P(w * 0.30, h * 0.34), h * 0.060,
             h * 0.038, S)
    cv.taper(P(w * 0.30, h * 0.30), P(w * 0.58, h * 0.40), h * 0.040,
             h * 0.032, S)


@_panel("nba-jam.marquee")
def _nba_marquee(cv):
    cv.fill("#241c18")
    cv.vgrad(0.0, 0.0, 1.0, 1.0, "#2c221c", "#171210")
    cv.vgrad(0.0, 0.060, 1.0, 0.800, "#f0e6ca", "#d3c39f")     # lit band
    cv.vgrad(0.0, 0.060, 1.0, 0.118, "#e6c672", "#9c7c2c")     # gold rails
    cv.vgrad(0.0, 0.742, 1.0, 0.800, "#e6c672", "#9c7c2c")
    cv.seg((0.0, 0.122), (1.0, 0.122), "#8a6c28", 0.010, 0.7)
    cv.seg((0.0, 0.738), (1.0, 0.738), "#8a6c28", 0.010, 0.7)
    cv.rect(0.0, 0.0, 0.022, 1.0, "#5e1119")                   # molding wrap
    cv.rect(0.978, 0.0, 1.0, 1.0, "#5e1119")

    cv.text("NBA", 0.232, 0.428, 0.470, _NBA_RED, 0.052, track=0.09,
            aspect=0.72, outline="#f4e6b4", ow=0.034)
    cv.text("JAM", 0.768, 0.428, 0.470, _NBA_RED, 0.052, track=0.09,
            aspect=0.72, outline="#f4e6b4", ow=0.034)
    _nba_roundel(cv, 0.500, 0.424, 0.560)
    cv.text("MIDWAY", 0.500, 0.880, 0.090, "#a4855a", 0.016, track=0.42,
            aspect=0.62)
    cv.rect(0.0, 0.955, 1.0, 1.0, "#0e0b0a")
    _grain(cv, 8.0, 31)


@_panel("nba-jam.side")
def _nba_side(cv):
    """ROUND 5.  Round 4 authored this flank as flat black vinyl because the
    roster reads "no legible graphic at any resolution" -- true, and it shipped
    a black slab.  What v4 7 (405,160)-(470,700) DOES show is that the whole
    silhouette is wrapped in a deep-red PEBBLE / DIAMOND-PLATE grain that
    catches the cove light, and that the orange-brown basketball-leather riser
    band carries round the bottom of the machine.  Both are drawn, so the flank
    is a textured red-black wrap with a warm kick, not a hole.
    """
    cv.fill("#1f181d")
    cv.vgrad(0.0, 0.0, 1.0, 1.0, "#382930", "#161116")
    cv.poly([(0.0, 1.00), (1.0, 0.30), (1.0, 0.62), (0.0, 1.00)],
            "#5e1c26", 0.62)
    cv.poly([(0.0, 0.14), (1.0, 0.0), (1.0, 0.10), (0.0, 0.26)],
            "#4a151d", 0.45)
    _pebble(cv, 0.0, 0.0, 1.0, 0.905, 0.0150, "#7c2c36", "#0c090c", 41, 0.50)
    cv.arc(1.10, 0.46, 0.560, 0.560, math.pi * 0.55, math.pi * 1.45, 0.016,
           "#b0868c", 0.16)
    cv.arc(1.10, 0.46, 0.330, 0.330, math.pi * 0.52, math.pi * 1.48, 0.012,
           "#b0868c", 0.11)
    cv.hgrad(0.86, 0.0, 1.0, 1.0, "#191419", "#68202a", 0.80)
    cv.rect(0.0, 0.0, 1.0, 0.022, "#5a1922")
    cv.vgrad(0.0, 0.905, 1.0, 1.0, "#9c6039", "#69381f")
    _pebble(cv, 0.0, 0.910, 1.0, 1.0, 0.0165, "#b87a4a", "#5a3018", 42, 0.60)
    cv.rect(0.0, 0.896, 1.0, 0.912, "#231710")
    _wear(cv, 0.0, 0.0, 1.0, 0.90, 10.0, 55, 2)
    _grain(cv, 7.0, 9)


@_panel("nba-jam.front")
def _nba_front(cv):
    """ROUND 5.  Same evidence as round 4 (v3 4 px 320,690-420,830 and v4 3
    px 230,180-300,260) but composed to FILL: the badge column is ~2x the
    round-4 size, the pebble riser is three real panels split by grout rather
    than one wash, and the coin door is a small near-black plate LOW AND LEFT,
    which is where the photographs show no bright plate at all.  Round 4 put
    the shared grey coin-door box straight through the middle of the badge.
    """
    k = cv.kx
    cv.fill("#131218")
    cv.vgrad(0.0, 0.0, 1.0, 0.700, "#221d23", "#0c0b10")
    cv.arc(0.500, 0.360, 0.560, 0.560, math.pi * 1.16, math.pi * 1.84, 0.016,
           "#6a4a3a", 0.22)
    cv.arc(0.500, 0.360, 0.560, 0.560, math.pi * 0.16, math.pi * 0.84, 0.016,
           "#6a4a3a", 0.22)
    _wear(cv, 0.0, 0.0, 1.0, 0.70, 9.0, 66, 2)

    _burst(cv, 0.500, 0.118, 0.150, 16, "#efe9de", 0.052, 0.16, 0.58, 0.95)
    cv.ell(0.500, 0.118, 0.062, 0.062, "#1a1218")
    cv.text("NBA", 0.500, 0.118, 0.066, "#e8dcc4", 0.011, track=0.18,
            aspect=0.68)

    bu, bv = 0.500, 0.360
    for (fx, fy, tx, ty, w0, cc) in (
            (-0.040, -0.086, -0.166, -0.286, 0.068, "#e8752a"),
            (0.020, -0.098, -0.066, -0.330, 0.060, "#f0a238"),
            (0.078, -0.078, 0.082, -0.244, 0.050, "#d8551c")):
        cv.taper((bu + fx * k, bv + fy), (bu + tx * k, bv + ty), w0, 0.010, cc)
    cv.ring(bu, bv, 0.148, 0.148, 0.020, "#cfd3da", 0.9)
    cv.ell(bu, bv, 0.122, 0.122, "#e6e8ee")
    cv.ell(bu, bv, 0.104, 0.104, "#c9631e")
    cv.ell(bu - 0.030 * k, bv - 0.032, 0.044, 0.044, "#e69340", 0.55)
    cv.seg((bu, bv - 0.104), (bu, bv + 0.104), "#1a1208", 0.013, 0.9)
    cv.seg((bu - 0.104 * k, bv), (bu + 0.104 * k, bv), "#1a1208", 0.012, 0.9)
    cv.arc(bu - 0.084 * k, bv, 0.104, 0.096, -math.pi * 0.46, math.pi * 0.46,
           0.012, "#1a1208", 0.9)
    cv.arc(bu + 0.084 * k, bv, 0.104, 0.096, math.pi * 0.54, math.pi * 1.46,
           0.012, "#1a1208", 0.9)

    cv.text("NBA JAM", 0.500, 0.556, 0.082, _NBA_RED, 0.017, track=0.10,
            aspect=0.70, slant=0.08, outline="#f0e6cc", ow=0.015)
    cv.text("TOURNAMENT EDITION", 0.500, 0.626, 0.030, "#9aa0a8", 0.007,
            track=0.30, aspect=0.60)

    _plate(cv, 0.040, 0.398, 0.290, 0.662, 0.020, "#151318", "#2e2126",
           "#08070a", 0.010)
    cv.rect(0.078, 0.426, 0.106, 0.474, "#6e5a4c")
    cv.rect(0.130, 0.426, 0.158, 0.474, "#6e5a4c")
    cv.seg((0.072, 0.544), (0.258, 0.544), "#3a2c30", 0.014, 0.9)
    cv.ell(0.238, 0.606, 0.024, 0.024, "#b8bcc2", 0.9)
    cv.seg((0.070, 0.606), (0.180, 0.606), "#241a1e", 0.026, 0.9)

    cv.vgrad(0.0, 0.705, 1.0, 1.0, "#a9683d", "#6f4026")
    _pebble(cv, 0.0, 0.712, 1.0, 1.0, 0.0175, "#c07a48", "#5a3118", 404, 0.62)
    cv.rect(0.0, 0.690, 1.0, 0.714, "#241a12")
    for uu in (0.300, 0.700):
        cv.seg((uu, 0.714), (uu, 1.0), "#2a1c12", 0.016, 0.85)
    cv.rect(0.312, 0.720, 0.688, 1.0, "#54301c", 0.42)
    cv.seg((0.0, 0.720), (1.0, 0.720), "#d8a070", 0.006, 0.35)
    _burst(cv, 0.500, 0.838, 0.150, 10, "#efe9de", 0.062, 0.16, 0.60, 0.95)
    cv.ell(0.500, 0.838, 0.036, 0.036, "#8d5533")
    cv.text("NBA JAM", 0.500, 0.955, 0.048, "#d8323e", 0.010, track=0.20,
            aspect=0.70, slant=0.08)
    _grain(cv, 8.0, 10)


@_panel("nba-jam.deck")
def _nba_deck(cv):
    """ROUND 5.  The hardwood court survives from round 4 -- it was the one
    deck no critic named -- but is rebuilt with real boards, BOTH keys, a
    centre stripe, printed button collars under the layout DECKS declares, and
    the maroon front lip the machine actually has.  Tile TOP = the deck's back
    edge (at the screen); tile BOTTOM = the player's edge.
    """
    _boards(cv, 0.0, 0.0, 1.0, 1.0, 15, "#b87c44", "#8d5528", "#5e3614", 707)
    _wear(cv, 0.0, 0.0, 1.0, 1.0, 12.0, 88, 3, vert=False)

    W = "#f4eee2"
    lw = 0.030
    cv.stroke([(0.040, 0.055), (0.960, 0.055), (0.960, 0.945), (0.040, 0.945)],
              W, lw, closed=True)
    cv.seg((0.500, 0.055), (0.500, 0.945), W, lw)
    cv.ring(0.500, 0.500, 0.240, 0.240, lw, W)
    for (bu, sgn) in ((0.040, 1.0), (0.960, -1.0)):
        cv.stroke([(bu, 0.300), (bu + sgn * 0.215, 0.300),
                   (bu + sgn * 0.215, 0.700), (bu, 0.700)], W, lw)
        cv.arc(bu, 0.500, 0.900, 0.900,
               -math.pi * 0.44 if sgn > 0 else math.pi * 0.56,
               math.pi * 0.44 if sgn > 0 else math.pi * 1.44, lw, W)
        cv.seg((bu, 0.418), (bu, 0.582), "#d84a2a", 0.040)
    cv.text("NBA JAM", 0.500, 0.500, 0.260, "#c0202e", 0.052, track=0.10,
            aspect=0.72, slant=0.10, outline="#f0e8d2", ow=0.034)

    for (cu, ccv, rr) in ((0.272, 0.560, 0.085), (0.728, 0.560, 0.085)):
        cv.ring(cu, ccv, rr, rr, 0.020, "#2b1d12", 0.55)
    for (cu, ccv) in ((0.372, 0.340), (0.436, 0.470), (0.372, 0.600),
                      (0.628, 0.340), (0.564, 0.470), (0.628, 0.600)):
        cv.ring(cu, ccv, 0.060, 0.060, 0.016, "#2b1d12", 0.50)
    cv.vgrad(0.0, 0.900, 1.0, 1.0, "#7c2028", "#4a1218")
    cv.seg((0.0, 0.900), (1.0, 0.900), "#0e0a0c", 0.014, 0.8)
    _grain(cv, 9.0, 11)


# =========================================================================
#  3.  STREET FIGHTER II: CHAMPION EDITION  --  SOUTH_RUN[1]
# =========================================================================
# Evidence: v3 4 px (930,565)-(1010,600) at 16x -- "CHAMPION" arched over the
# oval, "EDITION" straight across its foot, a green / gold slanted brush
# wordmark in the black middle, silver wing forms spilling left and right.
# v3 4 px (920,730)-(1030,810) -- the ROYAL BLUE riser with a ghosted pale
# fighter and "CAPCOM" on a dark plate low and left of centre.
#
# DECLARED: the centre wordmark does not resolve letter by letter in any frame
# (it reads as a green/gold brush mass).  It is drawn here as STREET FIGHTER /
# II because "CHAMPION EDITION" fixes the title beyond doubt; that is a
# reconstruction from the badge, not a reading of the pixels.

_CE_BLUE = "#2e5fbe"


@_panel("street-fighter-2-champion-edition.marquee")
def _ce_marquee(cv):
    k = cv.kx
    cv.fill("#161f3a")
    cv.vgrad(0.0, 0.0, 1.0, 1.0, "#1d2a4c", "#101728")
    _sheen(cv, 0.0, 0.0, 1.0, 1.0, 10.0, 21, 4)
    cv.vgrad(0.0, 0.0, 1.0, 0.070, "#e0e4ea", "#8d939e")   # pale cabinet edge
    cv.rect(0.0, 0.930, 1.0, 1.0, "#0b1020")

    cu, cvv = 0.500, 0.480
    ru, rv = 1.010, 0.420                                  # LENGTHS

    for sgn in (-1.0, 1.0):                                # silver wings
        base = cu + sgn * ru * 0.86 * k
        for j in range(5):
            t = j / 4.0
            cv.taper((base, cvv + (t - 0.5) * 0.055),
                     (cu + sgn * (ru + 0.62 + t * 0.06) * k,
                      cvv + (t - 0.5) * 0.62),
                     0.16 - t * 0.024, 0.040, _mix("#dfe3ea", "#7f8794", t),
                     0.92)
        cv.taper((base, cvv), (cu + sgn * (ru + 0.66) * k, cvv), 0.060, 0.024,
                 "#f0f2f6", 0.85)

    cv.ell(cu, cvv, ru + 0.035, rv + 0.035, "#c3c8d2")
    cv.ell(cu, cvv, ru, rv, "#0a0a10")
    cv.annulus(cu, cvv, ru, rv, 0.150, math.pi * 1.02, math.pi * 1.98, "#701f2c")
    cv.annulus(cu, cvv, ru, rv, 0.150, math.pi * 0.02, math.pi * 0.98, "#1c3fa4")
    cv.ring(cu, cvv, ru, rv, 0.022, "#d6dae2", 0.9)
    cv.ring(cu, cvv, ru - 0.150, rv - 0.150, 0.018, "#9aa0ac", 0.85)
    cv.arctext("CHAMPION", cu, cvv, ru - 0.078, rv - 0.078,
               math.pi * 1.235, math.pi * 1.765, 0.128, "#f0ece2", 0.024,
               outline="#3a0d14", ow=0.016, aspect=0.64)
    cv.text("EDITION", cu, cvv + rv - 0.076, 0.120, "#f2f4f8", 0.023,
            track=0.28, aspect=0.62, outline="#0a1740", ow=0.016)

    cv.text("STREET", cu - 0.055 * k, cvv - 0.108, 0.170, "#9fd63c", 0.030,
            track=0.06, aspect=0.62, slant=0.22, outline="#cfa422", ow=0.020)
    cv.text("FIGHTER", cu - 0.100 * k, cvv + 0.090, 0.180, "#9fd63c", 0.030,
            track=0.04, aspect=0.60, slant=0.22, outline="#cfa422", ow=0.020)
    cv.text("II", cu + 0.560 * k, cvv + 0.080, 0.260, "#e8c53a", 0.040,
            track=0.26, aspect=0.44, slant=0.22, outline="#6c4c08", ow=0.018)
    _grain(cv, 8.0, 12)


@_panel("street-fighter-2-champion-edition.side")
def _ce_side(cv):
    # The machine is close to head-on in every frame that shows it, so no side
    # graphic is resolvable.  What the photographs DO establish is that the
    # flanks are pale -- they read light grey / white laminate against the
    # black neighbours -- so it is authored as laminate, not as invented art.
    cv.fill("#c9ccd1")
    cv.vgrad(0.0, 0.0, 1.0, 1.0, "#d6d9de", "#a8abb2")
    r = _Rnd(313)
    u = 0.0
    while u < 1.0:                                        # vertical brush grain
        j = r.f(-12.0, 12.0)
        col = (255.0, 255.0, 255.0) if j > 0 else (0.0, 0.0, 0.0)
        cv.rect(u, 0.0, u + 0.010, 1.0, col, abs(j) / 255.0)
        u += 0.010
    _sheen(cv, 0.0, 0.0, 1.0, 1.0, 9.0, 44, 4)
    cv.hgrad(0.0, 0.0, 0.070, 1.0, "#5a5d64", "#c9ccd1", 0.9)   # back edge
    cv.hgrad(0.70, 0.0, 1.0, 1.0, "#c9ccd1", "#3a3d44", 0.55)   # molding bleed
    cv.rect(0.0, 0.978, 1.0, 1.0, "#6b6e75", 0.8)
    for (a0, b0, a1, b1) in ((0.24, 0.24, 0.32, 0.60), (0.56, 0.12, 0.48, 0.40)):
        cv.taper((a0, b0), (a1, b1), 0.004, 0.002, "#8e9198", 0.25)
    _grain(cv, 7.0, 13)


@_panel("street-fighter-2-champion-edition.front")
def _ce_front(cv):
    # The identifying front surface: the ROYAL BLUE riser.  A ghosted pale
    # fighter across the upper half, CAPCOM white on a dark plate low left.
    k = cv.kx
    cv.fill(_CE_BLUE)
    cv.vgrad(0.0, 0.0, 1.0, 1.0, "#3a70d4", "#20428c")
    _sheen(cv, 0.0, 0.0, 1.0, 1.0, 14.0, 91, 5)
    cv.rect(0.0, 0.0, 0.028, 1.0, "#c8ccd2", 0.9)         # white cabinet returns
    cv.rect(0.972, 0.0, 1.0, 1.0, "#c8ccd2", 0.9)

    # the ghost is LOW contrast in the photograph -- a pale wash on blue, not a
    # graphic silhouette, so it is drawn only ~26 lighter than its ground
    G = "#6f9adc"
    gu, gv, s = 0.480, 0.390, 0.300

    def P(dx, dy):
        return (gu + dx * s * k, gv + dy * s)
    for (grow, ga) in ((0.40, 0.10), (0.26, 0.16), (0.14, 0.22)):
        cv.ell(gu, gv, s * (1.25 + grow), s * (1.25 + grow), "#5f8ddc", ga)
    # torso leaning into the punch, then the limbs over it
    cv.taper(P(-0.30, -0.34), P(-0.02, 0.30), s * 0.44, s * 0.34, G, 0.80)
    cv.taper(P(-0.02, 0.26), P(0.16, 0.44), s * 0.36, s * 0.30, G, 0.80)
    cv.ell(P(-0.30, 0.0)[0], gv - 0.60 * s, s * 0.20, s * 0.20, G, 0.85)
    cv.taper(P(-0.28, -0.46), P(-0.30, -0.34), s * 0.16, s * 0.24, G, 0.85)
    cv.taper(P(-0.06, -0.30), P(0.74, -0.14), s * 0.26, s * 0.20, G, 0.82)
    cv.taper(P(0.74, -0.14), P(1.14, -0.08), s * 0.20, s * 0.17, G, 0.82)
    cv.ell(P(1.20, 0.0)[0], gv - 0.07 * s, s * 0.20, s * 0.20, G, 0.88)
    cv.taper(P(-0.36, -0.24), P(-0.82, 0.06), s * 0.22, s * 0.16, G, 0.72)
    cv.taper(P(-0.82, 0.06), P(-0.72, 0.34), s * 0.16, s * 0.14, G, 0.72)
    cv.taper(P(0.06, 0.36), P(0.62, 0.72), s * 0.30, s * 0.22, G, 0.78)
    cv.taper(P(0.62, 0.72), P(0.86, 0.98), s * 0.22, s * 0.17, G, 0.78)
    cv.taper(P(-0.14, 0.34), P(-0.72, 0.72), s * 0.28, s * 0.20, G, 0.72)
    cv.taper(P(-0.72, 0.72), P(-1.02, 0.98), s * 0.20, s * 0.16, G, 0.72)
    for j in range(6):
        yy = -0.36 + j * 0.09
        cv.taper(P(0.92, yy), P(1.78 - j * 0.07, yy), s * 0.036, s * 0.010,
                 "#a8c8f2", 0.28)

    cv.rect(0.140, 0.795, 0.575, 0.915, "#71121c")
    cv.rect(0.140, 0.795, 0.575, 0.815, "#a8323c", 0.7)
    cv.text("CAPCOM", 0.357, 0.855, 0.078, "#f2f2ef", 0.014, track=0.22,
            aspect=0.64)
    cv.rect(0.0, 0.975, 1.0, 1.0, "#16274e")
    _grain(cv, 9.0, 14)


@_panel("street-fighter-2-champion-edition.deck")
def _ce_deck(cv):
    # Black deck with a bright silver / steel bezel band along its LEADING edge
    # (a hard metallic line in both v3 4 and v4 8) and the checker strip along
    # its back.  Individual controls do not resolve, so none are printed.
    cv.fill("#4f4d55")
    cv.vgrad(0.0, 0.0, 1.0, 1.0, "#3d3b43", "#5a5860")
    _sheen(cv, 0.0, 0.0, 1.0, 1.0, 13.0, 61, 5)
    n = 26
    for j in range(n):
        u0 = j / float(n)
        cv.rect(u0, 0.075, u0 + 1.0 / n, 0.185,
                "#8e8c94" if j % 2 == 0 else "#26242b")
    cv.seg((0.0, 0.072), (1.0, 0.072), "#1c1a20", 0.012)
    cv.seg((0.0, 0.188), (1.0, 0.188), "#1c1a20", 0.012)
    for cu in (0.280, 0.720):
        cv.rect(cu - 0.185, 0.300, cu + 0.185, 0.720, "#3a3840", 0.75)
        cv.stroke([(cu - 0.185, 0.300), (cu + 0.185, 0.300),
                   (cu + 0.185, 0.720), (cu - 0.185, 0.720)], "#6c6a74",
                  0.010, closed=True, a=0.6)
    cv.vgrad(0.0, 0.848, 1.0, 1.0, "#dcdfe6", "#7f838c")
    cv.seg((0.0, 0.858), (1.0, 0.858), "#f0f2f6", 0.010, 0.9)
    cv.seg((0.0, 0.840), (1.0, 0.840), "#1b1920", 0.016)
    _grain(cv, 9.0, 15)


# =========================================================================
#  4.  THE GRAFFITI MULTICADE  --  NORTH_RUN[0]   (no legible title)
# =========================================================================
# Evidence: v3 1 px (520,570)-(620,830) at 7x and v4 6 px (225,115)-(290,285)
# at 10x.  A full-bleed vinyl wrap on a near-black ground in dense pale grey /
# white line work: long sweeping curves, a large almond / lens ellipse low on
# the flank, a diagonal slash near the top, a scatter of small glyphs.  NO
# title resolves at any magnification in any frame, so NO game name is printed
# here.  It reads blue in v3 1 only because that whole wall is under a blue RGB
# wash; v4 6 (neutral -- its floor meters #a4a39f) shows grey-on-black.

# Ink values are deliberately LOW contrast: v4 6 (the neutral exposure) puts
# the ground at #24263b-#414248 and the line work at #656871-#93959f, so a
# bright white collage would be wrong even though it reads better in a preview.
_N1_GND = "#22242c"
_N1_INK = "#6b6f79"
_N1_HI = "#9a9ea8"


def _tagstroke(cv, pts, col, w, a=1.0):
    """A graffiti tag stroke: tapered polyline, thick through the middle."""
    m = len(pts) - 1
    for i in range(m):
        f0 = 0.35 + 0.65 * math.sin(math.pi * (i / float(m)))
        f1 = 0.35 + 0.65 * math.sin(math.pi * ((i + 1) / float(m)))
        cv.taper(pts[i], pts[i + 1], w * f0, w * f1, col, a)


def _glyphscatter(cv, u0, v0, u1, v1, seed, count, col, hi, avoid=None):
    """Small illegible marks -- letters, tags, arrows, boxes, loops."""
    k = cv.kx
    r = _Rnd(seed)
    for _ in range(count):
        u = r.f(u0, u1)
        v = r.f(v0, v1)
        if avoid and _inpoly(avoid, u, v):
            continue
        s = r.f(0.012, 0.088) ** 1.15 * 1.35     # wide scale spread, not a comb
        j = r.i(0, 6)
        cc = hi if r.u() > 0.78 else col
        w = 0.0044 + s * 0.030
        if j == 0:
            _tagstroke(cv, [(u, v + s * 0.5), (u + s * 0.22 * k, v - s * 0.4),
                            (u + s * 0.48 * k, v + s * 0.45),
                            (u + s * 0.74 * k, v - s * 0.3)], cc, w * 1.6, 0.85)
        elif j == 1:
            cv.ring(u, v, s * 0.5, s * 0.5, w, cc, 0.8)
            cv.seg((u - s * 0.28 * k, v), (u + s * 0.28 * k, v), cc, w, 0.8)
        elif j == 2:
            cv.seg((u - s * 0.45 * k, v - s * 0.45),
                   (u + s * 0.45 * k, v + s * 0.45), cc, w, 0.8)
            cv.seg((u + s * 0.45 * k, v - s * 0.45),
                   (u - s * 0.45 * k, v + s * 0.45), cc, w, 0.8)
        elif j == 3:
            for b in range(r.i(2, 4)):
                yy = v + b * s * 0.30
                cv.seg((u, yy), (u + s * r.f(0.4, 1.0) * k, yy), cc, w * 1.3,
                       0.75)
        elif j == 4:
            cv.seg((u, v), (u + s * k, v - s * 0.45), cc, w, 0.85)
            cv.seg((u + s * k, v - s * 0.45), (u + s * 0.62 * k, v - s * 0.62),
                   cc, w, 0.85)
            cv.seg((u + s * k, v - s * 0.45), (u + s * 0.66 * k, v - s * 0.10),
                   cc, w, 0.85)
        elif j == 5:
            cv.stroke([(u, v), (u + s * 0.7 * k, v),
                       (u + s * 0.7 * k, v + s * 0.8), (u, v + s * 0.8)],
                      cc, w, closed=True, a=0.7)
            cv.seg((u, v + s * 0.4), (u + s * 0.7 * k, v + s * 0.4), cc, w, 0.6)
        else:
            cv.arc(u, v, s * 0.5, s * 0.5, r.f(0.0, 2.0), r.f(3.0, 6.0),
                   w, cc, 0.8)


@_panel("north-1-graffiti-multicade.marquee")
def _n1_marquee(cv):
    # Dark, near-black.  Pale abstract lettering across the centre, a small
    # maroon patch below and left of it, and a light angular X / wing mark at
    # the right end.  NO title -- none resolves in any frame.
    cv.fill("#191b22")
    cv.vgrad(0.0, 0.0, 1.0, 1.0, "#22242d", "#101219")
    _sheen(cv, 0.0, 0.0, 1.0, 1.0, 9.0, 71, 4)
    cv.rect(0.0, 0.0, 1.0, 0.075, "#0c0d12")
    cv.rect(0.0, 0.925, 1.0, 1.0, "#0c0d12")
    cv.seg((0.0, 0.085), (1.0, 0.085), "#43464f", 0.010, 0.6)

    # ONE continuous pale tag that never resolves into letters.  An earlier
    # pass drew four separate letter-like glyphs and the marquee accidentally
    # read "RUNLS" -- inventing a title is exactly what the evidence forbids,
    # so the strokes now cross and share tails instead of standing apart.
    _tagstroke(cv, [(0.146, 0.548), (0.170, 0.318), (0.212, 0.512),
                    (0.244, 0.372), (0.258, 0.596), (0.316, 0.336),
                    (0.286, 0.478), (0.372, 0.436), (0.412, 0.310),
                    (0.408, 0.572), (0.466, 0.394), (0.500, 0.556),
                    (0.548, 0.330), (0.578, 0.520), (0.634, 0.386)],
               "#9fa3ad", 0.100, 0.92)
    _tagstroke(cv, [(0.128, 0.452), (0.226, 0.604), (0.352, 0.352),
                    (0.454, 0.630), (0.556, 0.392), (0.656, 0.500)],
               "#83878f", 0.050, 0.78)
    # a loop, so the run cannot be parsed as a row of separate letters
    cv.ring(0.318, 0.470, 0.115, 0.115, 0.046, "#8f939d", 0.72)
    cv.ring(0.520, 0.436, 0.086, 0.086, 0.038, "#878b95", 0.62)
    cv.taper((0.140, 0.640), (0.660, 0.596), 0.036, 0.016, "#7f838d", 0.70)
    cv.taper((0.176, 0.286), (0.612, 0.268), 0.028, 0.013, "#9ba0aa", 0.50)

    cv.poly([(0.300, 0.672), (0.452, 0.658), (0.462, 0.766), (0.306, 0.782)],
            "#7d2029")
    cv.stroke([(0.300, 0.672), (0.452, 0.658), (0.462, 0.766), (0.306, 0.782)],
              "#b6555c", 0.016, closed=True, a=0.6)

    # the light angular mark at the right end -- a swept wing, not a neat X
    cv.taper((0.712, 0.300), (0.944, 0.512), 0.185, 0.030, "#bcc0ca", 0.92)
    cv.taper((0.744, 0.646), (0.952, 0.408), 0.120, 0.026, "#9ba0aa", 0.88)
    cv.taper((0.736, 0.352), (0.878, 0.470), 0.042, 0.018, "#d4d8e0", 0.72)
    _glyphscatter(cv, 0.06, 0.16, 0.96, 0.86, 202, 12, "#4c505a", "#6a6e78")
    _grain(cv, 8.0, 16)


@_panel("north-1-graffiti-multicade.side")
def _n1_side(cv):
    # The identifying surface: a full-bleed collage wrap.
    cv.fill(_N1_GND)
    cv.vgrad(0.0, 0.0, 1.0, 1.0, "#2b2e37", "#15171d")
    _sheen(cv, 0.0, 0.0, 1.0, 1.0, 11.0, 33, 5)

    cv.arc(0.22, -0.30, 1.30, 1.30, math.pi * 0.10, math.pi * 0.88, 0.016,
           _N1_INK, 0.85)
    cv.arc(0.18, -0.26, 1.46, 1.46, math.pi * 0.12, math.pi * 0.84, 0.008,
           _N1_HI, 0.6)
    cv.arc(0.90, 0.34, 1.34, 1.34, math.pi * 0.60, math.pi * 1.44, 0.014,
           _N1_INK, 0.8)
    cv.arc(0.50, 1.36, 1.16, 1.16, math.pi * 1.06, math.pi * 1.94, 0.013,
           _N1_INK, 0.75)

    cv.taper((0.115, 0.085), (0.560, 0.262), 0.088, 0.020, _N1_HI, 0.9)
    cv.taper((0.135, 0.126), (0.522, 0.282), 0.026, 0.010, "#e2e6ee", 0.55)

    lu, lv, lw_, lh = 0.420, 0.680, 0.290, 0.145
    lens = []
    for j in range(25):
        t = -1.0 + 2.0 * j / 24.0
        lens.append((lu + t * lw_, lv - (1.0 - t * t) * lh))
    for j in range(25):
        t = 1.0 - 2.0 * j / 24.0
        lens.append((lu + t * lw_, lv + (1.0 - t * t) * lh))
    cv.stroke(lens, _N1_HI, 0.018, closed=True, a=0.95)
    cv.stroke([(p[0] + (lu - p[0]) * 0.22, p[1] + (lv - p[1]) * 0.22)
               for p in lens], _N1_INK, 0.010, closed=True, a=0.7)
    cv.seg((lu - lw_ * 0.72, lv), (lu + lw_ * 0.72, lv), _N1_INK, 0.008, 0.7)
    cv.arc(lu + lw_ * 0.10, lv - 0.030, 0.110, 0.110, math.pi * 0.15,
           math.pi * 1.05, 0.010, _N1_HI, 0.6)
    cv.taper((lu - lw_ * 0.55, lv + 0.070), (lu + lw_ * 0.62, lv - 0.062),
             0.026, 0.010, _N1_HI, 0.55)

    _tagstroke(cv, [(0.075, 0.470), (0.180, 0.392), (0.250, 0.470),
                    (0.350, 0.386), (0.430, 0.462)], _N1_HI, 0.042, 0.85)
    _tagstroke(cv, [(0.560, 0.852), (0.640, 0.774), (0.700, 0.868),
                    (0.760, 0.782)], _N1_INK, 0.034, 0.8)
    _glyphscatter(cv, 0.03, 0.03, 0.97, 0.97, 5150, 96, _N1_INK, _N1_HI,
                  avoid=lens)
    _grain(cv, 8.0, 17)


@_panel("north-1-graffiti-multicade.front")
def _n1_front(cv):
    # The same wrap continues down the front, but the FRONT's own structure is
    # what is drawn here: two panels split by a seam at about mid height, a
    # single small white dot (coin plunger / lock) in the upper one, and a
    # printed QR square low on the lower one.
    k = cv.kx
    cv.fill("#1e2028")
    cv.vgrad(0.0, 0.0, 1.0, 1.0, "#272a33", "#131519")
    _sheen(cv, 0.0, 0.0, 1.0, 1.0, 10.0, 34, 4)

    r = _Rnd(808)
    for j in range(7):
        uu = 0.075 + j * 0.132 + r.f(-0.018, 0.018)
        cv.taper((uu, r.f(0.04, 0.16)),
                 (uu + r.f(-0.05, 0.05), r.f(0.84, 0.97)),
                 r.f(0.012, 0.036), r.f(0.008, 0.024),
                 _N1_INK if j % 2 else _N1_HI, r.f(0.35, 0.70))
    for j in range(5):
        vv = 0.14 + j * 0.175
        cv.taper((0.05, vv), (0.95, vv + r.f(-0.03, 0.03)), 0.010, 0.005,
                 _N1_INK, 0.45)

    cv.rect(0.0, 0.485, 1.0, 0.506, "#0a0b0f")
    cv.seg((0.0, 0.510), (1.0, 0.510), "#5a5e68", 0.005, 0.55)
    cv.stroke([(0.030, 0.028), (0.970, 0.028), (0.970, 0.470), (0.030, 0.470)],
              "#4e525c", 0.006, closed=True, a=0.55)
    cv.stroke([(0.030, 0.524), (0.970, 0.524), (0.970, 0.970), (0.030, 0.970)],
              "#4e525c", 0.006, closed=True, a=0.55)

    _glyphscatter(cv, 0.05, 0.05, 0.95, 0.45, 616, 44, _N1_INK, _N1_HI)
    _glyphscatter(cv, 0.05, 0.55, 0.95, 0.94, 617, 38, _N1_INK, _N1_HI)

    cv.ell(0.618, 0.300, 0.026, 0.026, "#e8eaf0")
    cv.ell(0.618, 0.300, 0.014, 0.014, "#8a8e98")

    # the printed QR square -- 17 modules, real finder patterns
    qs = 0.230                                            # a LENGTH
    qu, qv = 0.520, 0.690
    cv.rect(qu, qv, qu + qs * k, qv + qs, "#0c0d11")
    m0 = qs * 0.06
    mod = qs * 0.88 / 17.0
    q = _Rnd(9090)
    cv.rect(qu + m0 * k, qv + m0, qu + (qs - m0) * k, qv + qs - m0, "#d8dbe2")
    for gy in range(17):
        for gx in range(17):
            if (gx < 7 and gy < 7) or (gx > 9 and gy < 7) or (gx < 7 and gy > 9):
                continue
            if q.u() < 0.46:
                cv.rect(qu + (m0 + gx * mod) * k, qv + m0 + gy * mod,
                        qu + (m0 + (gx + 1) * mod) * k,
                        qv + m0 + (gy + 1) * mod, "#0e0f14")
    for (fx, fy) in ((0, 0), (10, 0), (0, 10)):
        bx0 = m0 + fx * mod
        by0 = m0 + fy * mod
        for (o0, o1, cc) in ((0, 7, "#0e0f14"), (1, 6, "#d8dbe2"),
                             (2, 5, "#0e0f14")):
            cv.rect(qu + (bx0 + o0 * mod) * k, qv + by0 + o0 * mod,
                    qu + (bx0 + o1 * mod) * k, qv + by0 + o1 * mod, cc)
    _grain(cv, 8.0, 18)


@_panel("north-1-graffiti-multicade.deck")
def _n1_deck(cv):
    # Black, wide, the deepest deck on the north wall; two joystick / button
    # clusters; the surface reads plain dark with NO printed legend, so none is
    # drawn.  Authored light for a2kit's #4c4c4c deck material.
    cv.fill("#494750")
    cv.vgrad(0.0, 0.0, 1.0, 1.0, "#3b3942", "#54525c")
    _sheen(cv, 0.0, 0.0, 1.0, 1.0, 15.0, 99, 6)
    r = _Rnd(1212)
    v = 0.0
    while v < 1.0:                                       # brushed along u
        j = r.f(-9.0, 9.0)
        col = (255.0, 255.0, 255.0) if j > 0 else (0.0, 0.0, 0.0)
        cv.rect(0.0, v, 1.0, v + 0.010, col, abs(j) / 255.0)
        v += 0.010
    for cu in (0.265, 0.735):
        cv.ell(cu, 0.500, 0.470, 0.310, "#3a3841", 0.55)
        cv.ell(cu, 0.500, 0.330, 0.215, "#333139", 0.45)
    cv.vgrad(0.0, 0.895, 1.0, 1.0, "#6e6c76", "#4a4852")
    cv.seg((0.0, 0.890), (1.0, 0.890), "#232128", 0.014)
    cv.rect(0.0, 0.0, 1.0, 0.055, "#2c2a32")
    for (a0, b0, a1, b1) in ((0.10, 0.22, 0.42, 0.30), (0.58, 0.72, 0.88, 0.66)):
        cv.taper((a0, b0), (a1, b1), 0.006, 0.004, "#7c7a84", 0.30)
    _grain(cv, 9.0, 19)


# =========================================================================
#  ROUND 5.  THE WRAP ROUND -- pac-man, tmnt-turtles-in-time,
#  golden-tee-3d-golf move into this module (nba-jam was already here).
# =========================================================================
# Three critics rejected round 4 in the same words: "all three cabinets are one
# asset recoloured -- the same flat-black front panel with the SAME centred
# grey coin-door rectangle at the same size and position, and the same
# two-joystick deck over the same row of flat square buttons".  They were
# right.  Below the marquee, each of these four machines now gets:
#
#   * a FULL-BLEED side / front, edge to edge, with its own ground and its own
#     composition -- Pac-Man is yellow from the moulding to the floor with the
#     ghost, the Pac and the maze elbows on it; TMNT is a brick street; NBA Jam
#     is a red pebble wrap over a leather riser; Golden Tee is the black it
#     photographs as, carried by a big embossed coin door rather than a label.
#   * its OWN coin door -- position, size, plate colour, whether there is a
#     printed graphic round it, whether there is a return cup.  See DOORS.
#   * its OWN deck graphic AND its own control layout.  The controls are
#     GEOMETRY that ar2.upright() places, so DECKS below declares them and the
#     integrator consumes it; the printed collars on each deck tile are drawn
#     to match what DECKS asks for.
#
# MARQUEES ARE NOT TOUCHED.  Round 4's marquees for these three machines live
# in art_g1 (pac-man, tmnt) and art_g3 (golden-tee) and they work; this module
# deliberately does NOT claim `<slug>.marquee`.  See WRAP_R5 for the merge.


# -------------------------------------------------------------- 5. PAC-MAN
# Evidence: v4 6 px (262,110)-(335,285) at 8x and v3 1 px (585,545)-(700,810)
# at 5x (crops in art/crops_r5/pac_v46.png, pac_v31.png, pac_deck31.png).
# Both show: a saturated yellow body top to bottom; a TALL BLACK ROUNDED coin
# plate, narrow, centred, in the UPPER HALF of the lower front, with one
# horizontal return-door line and a WHITE round return button at its right; a
# blue ghost with white eyes below the plate; a yellow Pac below and right of
# the ghost; and dark-blue MAZE ELBOW brackets across the very bottom edge.
# The screen is DARK in both frames -- no attract art is invented for it.

_PM_YEL = "#f2c81c"
_PM_YEL_D = "#c39a10"
_PM_MAR = "#7c1c1e"
_PM_BLUE = "#2436b8"
_PM_GHOST = "#4ab0ea"


def _pm_ghost(cv, cu, cvv, h):
    """The classic ghost: domed head, scalloped skirt, big white eyes."""
    k = cv.kx
    w = h * 0.86
    pts = []
    for i in range(13):                                  # the dome
        a = math.pi + math.pi * i / 12.0
        pts.append((cu + w * 0.5 * k * math.cos(a), cvv - h * 0.16 +
                    h * 0.44 * math.sin(a)))
    n = 4
    for i in range(n * 2 + 1):                           # the skirt
        t = 1.0 - i / float(n * 2)
        dv = h * 0.50 if i % 2 else h * 0.36
        pts.append((cu + (t - 0.5) * w * k, cvv + dv))
    cv.poly(pts, _PM_GHOST)
    for sgn in (-1.0, 1.0):
        cv.ell(cu + sgn * w * 0.20 * k, cvv - h * 0.10, h * 0.155, h * 0.195,
               "#f4f6fa")
        cv.ell(cu + sgn * w * 0.20 * k + w * 0.07 * k, cvv - h * 0.08,
               h * 0.085, h * 0.100, "#1c2a90")


def _pm_pac(cv, cu, cvv, r, ang=0.62):
    """A Pac with an open wedge mouth, facing right."""
    k = cv.kx
    pts = [(cu, cvv)]
    a0, a1 = ang * 0.5, math.tau - ang * 0.5
    for i in range(25):
        a = a0 + (a1 - a0) * i / 24.0
        pts.append((cu + r * k * math.cos(a), cvv + r * math.sin(a)))
    cv.poly(pts, "#ffd91e")
    cv.stroke(pts + [pts[0]], "#241a04", 0.012, a=0.85)


def _pm_elbow(cv, u0, v0, u1, v1, w, col, flip):
    """A maze corner bracket -- two legs meeting at a square corner."""
    if flip:
        cv.rect(u0, v0, u1, v0 + w, col)
        cv.rect(u1 - w * cv.kx, v0, u1, v1, col)
    else:
        cv.rect(u0, v0, u1, v0 + w, col)
        cv.rect(u0, v0, u0 + w * cv.kx, v1, col)


@_panel("pac-man.side")
def _pm_side(cv):
    """Full-bleed school-bus yellow, floor to head, with the maroon head trim
    and kick the photographs show.  The roster is explicit that this machine
    carries NO large graphic on its flanks -- the graphics live on the front
    and the marquee -- so none is invented; what makes it read is that it is
    the only SATURATED body in the room, edge to edge."""
    cv.fill(_PM_YEL)
    cv.hgrad(0.0, 0.0, 1.0, 1.0, "#d9ae14", "#fbd634")       # back -> front
    cv.vgrad(0.0, 0.0, 1.0, 0.10, "#e0b418", _PM_YEL)
    _wear(cv, 0.0, 0.0, 1.0, 1.0, 11.0, 21, 3)
    cv.rect(0.0, 0.0, 1.0, 0.020, _PM_MAR)                   # head trim
    cv.hgrad(0.955, 0.0, 1.0, 1.0, _PM_YEL, "#8e2224", 0.85)  # front molding
    cv.vgrad(0.0, 0.965, 1.0, 1.0, "#8e2224", "#4c1012")     # kick
    cv.seg((0.0, 0.962), (1.0, 0.962), "#a8850e", 0.005, 0.6)
    # the coin box / service door the flank actually carries, low and back
    cv.rect(0.055, 0.760, 0.300, 0.930, "#d3aa16")
    cv.stroke([(0.055, 0.760), (0.300, 0.760), (0.300, 0.930), (0.055, 0.930)],
              "#9a7a0c", 0.006, closed=True, a=0.8)
    _grain(cv, 7.0, 71)


@_panel("pac-man.front")
def _pm_front(cv):
    """Yellow edge to edge.  Round 4 shipped a yellow field with a floated
    wordmark and the shared grey coin box across it; this is the panel v3 1
    actually shows -- black plate high and narrow, ghost, Pac, maze elbows."""
    k = cv.kx
    cv.fill(_PM_YEL)
    cv.vgrad(0.0, 0.0, 1.0, 1.0, "#f8d128", "#d8a814")
    _wear(cv, 0.0, 0.0, 1.0, 1.0, 10.0, 22, 3)
    cv.hgrad(0.0, 0.0, 0.030, 1.0, "#7e1e20", _PM_YEL)       # molding returns
    cv.hgrad(0.970, 0.0, 1.0, 1.0, _PM_YEL, "#7e1e20")

    # the small dark service plaque the photos show high and centred
    cv.rect(0.398, 0.032, 0.602, 0.082, "#2a2118")
    cv.text("PAC-MAN", 0.500, 0.057, 0.030, "#c9b98a", 0.006, track=0.24,
            aspect=0.62)

    # ---- the coin door: TALL, NARROW, black, upper half, centred
    _plate(cv, 0.392, 0.118, 0.612, 0.560, 0.042, "#15161c", "#3a3c46",
           "#0a0a0e", 0.011)
    for uu in (0.452, 0.552):                                # two coin slots
        cv.rect(uu - 0.013, 0.156, uu + 0.013, 0.212, "#8e939c")
        cv.rect(uu - 0.008, 0.162, uu + 0.008, 0.206, "#20222a")
    cv.seg((0.418, 0.316), (0.552, 0.316), "#a9aeb6", 0.019, 0.95)
    cv.ell(0.578, 0.316, 0.030, 0.030, "#eef0f4")            # return button
    cv.ell(0.578, 0.316, 0.018, 0.018, "#b9bec6")
    for vv in (0.400, 0.436, 0.472):
        cv.seg((0.424, vv), (0.580, vv), "#262932", 0.014, 0.85)

    # ---- the chase group
    _pm_ghost(cv, 0.452, 0.662, 0.215)
    cv.taper((0.382, 0.760), (0.346, 0.818), 0.052, 0.032, "#e0384c", 0.9)
    cv.taper((0.452, 0.772), (0.452, 0.834), 0.048, 0.030, "#e0384c", 0.9)
    _pm_pac(cv, 0.628, 0.800, 0.118)
    for (du, dv) in ((0.740, 0.800), (0.806, 0.800), (0.872, 0.800)):
        cv.ell(du, dv, 0.026, 0.026, "#f6e6a2")

    # ---- the maze elbows across the bottom edge
    _pm_elbow(cv, 0.055, 0.868, 0.290, 0.988, 0.036, _PM_BLUE, False)
    _pm_elbow(cv, 0.710, 0.868, 0.945, 0.988, 0.036, _PM_BLUE, True)
    cv.rect(0.055, 0.868, 0.290, 0.904, "#3a4ce0", 0.35)
    cv.rect(0.710, 0.868, 0.945, 0.904, "#3a4ce0", 0.35)
    cv.rect(0.0, 0.988, 1.0, 1.0, "#5d1214")
    _grain(cv, 8.0, 23)


@_panel("pac-man.deck")
def _pm_deck(cv):
    """Black deck with the maroon front lip, a yellow legend at the left and
    the printed collars for the single ball-top stick and the button row DECKS
    declares.  Authored LIFTED: a2kit multiplies this tile by ART_DK (#4c4c4c)
    because an up-facing surface over-collects in this scene."""
    cv.vgrad(0.0, 0.0, 1.0, 1.0, "#7e7e88", "#54545e")
    _wear(cv, 0.0, 0.0, 1.0, 1.0, 11.0, 24, 2, vert=False)
    cv.vgrad(0.0, 0.0, 1.0, 0.080, "#b4b4be", "#666670")      # back return
    cv.seg((0.0, 0.092), (1.0, 0.092), "#ffe45c", 0.018, 0.95)
    cv.text("PAC-MAN", 0.170, 0.235, 0.215, "#ffe45c", 0.040, track=0.14,
            aspect=0.68)
    cv.seg((0.028, 0.372), (0.318, 0.372), "#ffe45c", 0.012, 0.8)
    # printed collars: one stick left of centre, a row of small buttons right
    cv.ring(0.196, 0.640, 0.175, 0.175, 0.022, "#26262e", 0.55)
    for (cu, ccv) in ((0.400, 0.400), (0.472, 0.640), (0.544, 0.400),
                      (0.616, 0.640), (0.688, 0.400), (0.760, 0.640),
                      (0.832, 0.400)):
        cv.ring(cu, ccv, 0.096, 0.096, 0.018, "#26262e", 0.45)
    cv.vgrad(0.0, 0.875, 1.0, 1.0, "#e0505c", "#8e2630")      # maroon lip
    cv.seg((0.0, 0.875), (1.0, 0.875), "#141014", 0.016, 0.9)
    _grain(cv, 9.0, 25)


# ------------------------------------------- 6. TEENAGE MUTANT NINJA TURTLES
# Evidence: v3 4 px (400,690)-(500,830) at 5x (crops_r5/e_run_v34.png) shows
# the front dead-on -- black panel, "TURTLES" in green with a yellow-orange
# outline, "TURTLES IN TIME" in a pale slab under it, a short red line, and a
# RISER printed with a turtle illustration over brown brick with a green
# TURTLES plaque at its right end.  v4 7 px (400,150)-(600,460)
# (crops_r5/tmnt_v47.png) shows the deck: a brown/red brick New York street,
# repeated TURTLES wordmarks in green / blue / red, ball-top sticks, one large
# yellow and one large red button per station, small square character portraits
# along the front edge, and the bright grass-green T-molding round everything.
# NO coin door reads on this machine in any frame -- see DOORS.

_TM_GRN = "#4cbe3c"
_TM_GRN_D = "#1d5f22"
_TM_YEL = "#f6c22a"
_TM_BRICK = "#8a4a34"
_TM_SIL = "#c6cad2"


def _tm_logo(cv, cu, cvv, h, keyline=True):
    """TURTLES in the green-with-yellow-outline logo letters."""
    if keyline:
        cv.text("TURTLES", cu, cvv, h, "#12140f", h * 0.30, track=0.10,
                aspect=0.74, slant=0.06)
    cv.text("TURTLES", cu, cvv, h, _TM_GRN, h * 0.155, track=0.10,
            aspect=0.74, slant=0.06, outline=_TM_YEL, ow=h * 0.085)


def _tm_turtle(cv, cu, cvv, h):
    """A turtle: green shell with plates, head, bandana, arms."""
    k = cv.kx
    cv.ell(cu, cvv, h * 0.52, h * 0.46, "#2f7a2c")
    cv.ell(cu, cvv + h * 0.02, h * 0.40, h * 0.34, "#c9a24a")
    for (dx, dy) in ((-0.20, -0.10), (0.20, -0.10), (0.0, 0.0),
                     (-0.20, 0.12), (0.20, 0.12)):
        cv.ell(cu + dx * h * k, cvv + dy * h, h * 0.115, h * 0.095, "#a8813a")
    cv.ell(cu, cvv - h * 0.56, h * 0.28, h * 0.26, "#49a83c")       # head
    cv.rect(cu - h * 0.30 * k, cvv - h * 0.64, cu + h * 0.30 * k,
            cvv - h * 0.52, "#d8322c")                              # bandana
    for sgn in (-1.0, 1.0):
        cv.ell(cu + sgn * h * 0.11 * k, cvv - h * 0.585, h * 0.055, h * 0.045,
               "#f2f2ee")
        cv.taper((cu + sgn * h * 0.30 * k, cvv - h * 0.60),
                 (cu + sgn * h * 0.62 * k, cvv - h * 0.50), h * 0.055,
                 h * 0.030, "#d8322c")
        cv.taper((cu + sgn * h * 0.44 * k, cvv - h * 0.18),
                 (cu + sgn * h * 0.72 * k, cvv + h * 0.16), h * 0.13,
                 h * 0.09, "#49a83c")


@_panel("tmnt-turtles-in-time.side")
def _tm_side(cv):
    """The roster reads this flank as "black, carrying dark turtle/city
    artwork, edged all round by bright green T-molding".  Drawn as that: a
    night skyline of brick blocks with lit windows over a dark street, a
    manhole, and a big low-contrast turtle silhouette -- a scene, not a slab.
    Image LEFT is the cabinet's back, RIGHT is the deck front."""
    cv.vgrad(0.0, 0.0, 1.0, 0.46, "#241a3a", "#3a2450")          # night sky
    cv.vgrad(0.0, 0.46, 1.0, 1.0, "#241c22", "#12100f")
    for (u0, u1, v0) in ((0.0, 0.26, 0.30), (0.22, 0.52, 0.19),
                         (0.48, 0.72, 0.34), (0.68, 1.0, 0.24)):
        cv.rect(u0, v0, u1, 0.760, "#4a2c22")
        _bricks(cv, u0, v0, u1, 0.760, 8, "#6f3f2c", "#8c5238", "#2c1a14",
                int(u0 * 100) + 3, 1.0, 10.0)
        _window_rows(cv, u0 + 0.03, v0 + 0.05, u1 - 0.03, 0.700, 2, 4,
                     "#e8c24a", "#1a1420", int(u1 * 100) + 7, 0.34)
        cv.rect(u0, v0, u1, v0 + 0.016, "#2c1a14")
    cv.rect(0.0, 0.760, 1.0, 1.0, "#1a1a1e")                     # the street
    cv.vgrad(0.0, 0.760, 1.0, 0.800, "#3c3a40", "#1a1a1e")
    cv.ell(0.300, 0.905, 0.070, 0.070, "#2e2e34")                # manhole
    cv.ring(0.300, 0.905, 0.070, 0.070, 0.010, "#4a4a52", 0.7)
    for uu in (0.520, 0.640, 0.760):                             # road dashes
        cv.rect(uu, 0.930, uu + 0.055, 0.946, "#6a6a62", 0.55)
    _tm_turtle(cv, 0.660, 0.500, 0.230)
    cv.rect(0.0, 0.0, 1.0, 0.020, _TM_GRN)                       # molding
    cv.vgrad(0.0, 0.978, 1.0, 1.0, "#2c7a28", "#17451a")
    cv.hgrad(0.965, 0.0, 1.0, 1.0, "#1e1e22", _TM_GRN, 0.9)
    _wear(cv, 0.0, 0.0, 1.0, 1.0, 9.0, 33, 2)
    _grain(cv, 7.0, 34)


@_panel("tmnt-turtles-in-time.front")
def _tm_front(cv):
    """v3 4 dead-on: the logo block over a brick riser carrying the turtle and
    the green TURTLES plaque.  NO coin door -- none reads in any frame, and
    DOORS asks the integrator to omit the plate on this machine entirely."""
    cv.fill("#121317")
    cv.vgrad(0.0, 0.0, 1.0, 0.720, "#1d1e24", "#0d0e12")
    _wear(cv, 0.0, 0.0, 1.0, 0.70, 8.0, 35, 2)
    cv.hgrad(0.0, 0.0, 0.026, 1.0, _TM_GRN, "#121317")           # molding
    cv.hgrad(0.974, 0.0, 1.0, 1.0, "#121317", _TM_GRN)

    cv.seg((0.150, 0.072), (0.850, 0.072), "#b8bcc4", 0.010, 0.75)
    cv.text("TEENAGE MUTANT NINJA", 0.500, 0.132, 0.046, "#d8322c", 0.009,
            track=0.20, aspect=0.60)
    _tm_logo(cv, 0.500, 0.250, 0.170)
    cv.rect(0.180, 0.372, 0.820, 0.470, "#20222a")
    cv.text("TURTLES IN TIME", 0.500, 0.421, 0.062, _TM_SIL, 0.012,
            track=0.18, aspect=0.62)
    cv.text("KONAMI", 0.500, 0.532, 0.040, "#d4382c", 0.009, track=0.34,
            aspect=0.60)
    cv.seg((0.240, 0.582), (0.760, 0.582), "#8a2a24", 0.009, 0.85)
    cv.text("4 PLAYERS", 0.500, 0.618, 0.034, "#8e929a", 0.008, track=0.30,
            aspect=0.60)

    # ---- the riser: brick street, turtle, green plaque
    _bricks(cv, 0.0, 0.672, 1.0, 1.0, 6, "#7f4632", _TM_BRICK, "#33201a", 36,
            1.0, 7.0)
    cv.vgrad(0.0, 0.672, 1.0, 0.746, "#1a1418", _TM_BRICK, 0.55)
    cv.rect(0.0, 0.658, 1.0, 0.678, "#181a16")
    _tm_turtle(cv, 0.215, 0.840, 0.178)
    cv.rect(0.520, 0.740, 0.968, 0.948, "#1d5f22")
    cv.rect(0.534, 0.754, 0.954, 0.934, "#2c8f2c")
    _tm_logo(cv, 0.736, 0.844, 0.086, keyline=False)
    cv.rect(0.0, 0.985, 1.0, 1.0, "#17451a")
    _grain(cv, 8.0, 37)


@_panel("tmnt-turtles-in-time.deck")
def _tm_deck(cv):
    """The brick New York street the deck is printed with, seen the way the
    deck quad is UV'd: tile TOP = the back edge at the screen, tile BOTTOM =
    the player's edge, where the four square character portraits sit."""
    cv.vgrad(0.0, 0.0, 1.0, 0.20, "#d8b072", "#a87848")          # sky band
    _bricks(cv, 0.0, 0.135, 1.0, 0.865, 8, "#8c4e36", "#a86040", "#3c2318",
            38, 1.0, 9.0)
    for u0 in (0.075, 0.330, 0.585, 0.840):                      # facades
        cv.rect(u0, 0.150, u0 + 0.115, 0.860, "#6b3a2a", 0.55)
        _window_rows(cv, u0 + 0.012, 0.185, u0 + 0.103, 0.820, 2, 5,
                     "#e6c86a", "#241a20", int(u0 * 200), 0.32)
    for u0 in (0.205, 0.460, 0.715):                             # fire escapes
        for vv in (0.300, 0.470, 0.640):
            cv.seg((u0, vv), (u0 + 0.090, vv), "#2a2228", 0.020, 0.85)
            cv.seg((u0 + 0.045, vv), (u0 + 0.045, vv + 0.170), "#2a2228",
                   0.014, 0.7)
    cv.rect(0.0, 0.865, 1.0, 1.0, "#2b2b30")                     # the street
    cv.ell(0.500, 0.930, 0.052, 0.052, "#3c3c44")                # manhole
    cv.ring(0.500, 0.930, 0.052, 0.052, 0.012, "#585862", 0.8)

    _tm_logo(cv, 0.262, 0.400, 0.170)
    cv.text("TURTLES", 0.690, 0.300, 0.130, "#4aa8f0", 0.026, track=0.10,
            aspect=0.74, slant=0.06, outline="#12203a", ow=0.024)
    cv.text("TURTLES", 0.640, 0.700, 0.115, "#e0384c", 0.024, track=0.10,
            aspect=0.74, slant=0.06, outline="#2a0c12", ow=0.022)

    # the square character portraits along the player's edge
    for (i, bd) in enumerate(("#d8322c", "#4a6ee0", "#e08a1c", "#8a3ad0")):
        u0 = 0.055 + i * 0.238
        cv.rect(u0, 0.878, u0 + 0.128, 0.988, "#efe8d8")
        cv.rect(u0 + 0.010, 0.890, u0 + 0.118, 0.976, "#1c2a18")
        cv.ell(u0 + 0.064, 0.940, 0.052, 0.052, "#49a83c")
        cv.rect(u0 + 0.026, 0.918, u0 + 0.102, 0.934, bd)
    # printed collars for the layout DECKS declares
    for cu in (0.270, 0.730):
        cv.ring(cu, 0.450, 0.150, 0.150, 0.026, "#1a1210", 0.55)
    for (cu, ccv, rr) in ((0.408, 0.330, 0.110), (0.408, 0.580, 0.110),
                          (0.868, 0.330, 0.110), (0.868, 0.580, 0.110)):
        cv.ring(cu, ccv, rr, rr, 0.024, "#1a1210", 0.5)
    cv.vgrad(0.0, 0.988, 1.0, 1.0, "#3fae38", "#1d5f22")         # green lip
    _grain(cv, 8.0, 39)


# ------------------------------------------------- 7. GOLDEN TEE 3D GOLF
# Evidence: v4 7 px (90,105)-(185,300) at 7x and v4 6 px (366,135)-(440,295)
# at 8x (crops_r5/gt_v47.png, gt_v46.png, gt_deck.png).  The lower front of
# this machine IS PLAIN BLACK in both frames -- the roster says so and so do
# the pixels.  It is NOT given an invented graphic.  What it is given is the
# thing the photographs DO show carrying it: a LARGE embossed coin door with
# three vertical slots and a white return button, filling ~40% of the panel,
# plus the silver wordmark high under the deck.  Its identity lives on the
# marquee (art_g3, untouched), on the LIT yellow three-panel instruction strip
# in the bezel, and on the bright fairway deck.  The screen is DARK in both
# frames and no attract art is invented for it.

_GT_BLK = "#1c1d21"
_GT_SIL = "#b4b8be"
_GT_FAIR = "#5f9440"
_GT_YEL = "#ffe23a"
_GT_DARK = "#1d2a12"


def _gt_wordmark(cv, cu, cvv, h, col):
    """GOLDEN TEE with the little tee-and-ball device in front of it."""
    k = cv.kx
    cv.text("GOLDEN TEE", cu + h * 0.22 * k, cvv, h, col, h * 0.115,
            track=0.16, aspect=0.62, slant=0.05)
    cv.taper((cu - h * 1.90 * k, cvv + h * 0.62), (cu - h * 1.90 * k,
                                                   cvv - h * 0.20),
             h * 0.14, h * 0.20, col)
    cv.ell(cu - h * 1.90 * k, cvv - h * 0.34, h * 0.24, h * 0.24, col)


@_panel("golden-tee-3d-golf.side")
def _gt_side(cv):
    """Plain black flanks -- the roster is explicit ("the green lives entirely
    on the marquee, the instruction strip and the deck") and v4 6 agrees.  So
    this is black, but it is PRINTED black: a vertical brushed vinyl with a
    seam down the panel line, a matt kick, and the small silver wordmark that
    sits high on the flank.  Declared as a deliberately plain surface."""
    cv.fill("#26262a")
    cv.hgrad(0.0, 0.0, 1.0, 1.0, "#1b1b1e", "#34343a")
    _wear(cv, 0.0, 0.0, 1.0, 1.0, 12.0, 51, 3)
    for uu in (0.235, 0.470, 0.705):
        cv.seg((uu, 0.030), (uu, 0.965), "#4a4d55", 0.010, 0.55)
        cv.seg((uu + 0.012, 0.030), (uu + 0.012, 0.965), "#141519", 0.008,
               0.45)
    cv.vgrad(0.0, 0.0, 1.0, 0.030, "#565961", _GT_BLK)
    cv.vgrad(0.0, 0.950, 1.0, 1.0, "#15161a", "#0c0d10")        # kick
    cv.seg((0.0, 0.948), (1.0, 0.948), "#565961", 0.006, 0.6)
    _gt_wordmark(cv, 0.640, 0.235, 0.034, "#8e939c")
    cv.rect(0.070, 0.700, 0.330, 0.900, "#33353c")              # service door
    cv.stroke([(0.070, 0.700), (0.330, 0.700), (0.330, 0.900), (0.070, 0.900)],
              "#4e5158", 0.007, closed=True, a=0.85)
    _grain(cv, 7.0, 52)


@_panel("golden-tee-3d-golf.front")
def _gt_front(cv):
    """Black, as photographed -- and carried by the coin door, which on this
    machine is the biggest and brightest of the four in this module: a raised
    plate filling 42% of the panel width with THREE vertical slots, a recessed
    return door and a WHITE return button (v4 6 px 374,230-432,285)."""
    cv.fill("#28282d")
    cv.vgrad(0.0, 0.0, 1.0, 1.0, "#36363c", "#17171a")
    _wear(cv, 0.0, 0.0, 1.0, 1.0, 10.0, 53, 2)
    for uu in (0.180, 0.500, 0.820):
        cv.seg((uu, 0.040), (uu, 0.960), "#4a4d55", 0.009, 0.50)
    _gt_wordmark(cv, 0.520, 0.108, 0.068, "#d2d6dc")

    _plate(cv, 0.278, 0.330, 0.722, 0.870, 0.030, "#1a1b20", "#5a5d66",
           "#0b0c0f", 0.018)
    cv.vgrad(0.292, 0.346, 0.708, 0.470, "#2e3037", "#1a1b20")
    for uu in (0.380, 0.500, 0.620):                            # three slots
        cv.rect(uu - 0.017, 0.376, uu + 0.017, 0.452, "#8e939c")
        cv.rect(uu - 0.011, 0.382, uu + 0.011, 0.446, "#141519")
    cv.rect(0.318, 0.512, 0.682, 0.700, "#191a1f")              # return door
    cv.stroke([(0.318, 0.512), (0.682, 0.512), (0.682, 0.700), (0.318, 0.700)],
              "#3c3e46", 0.008, closed=True, a=0.9)
    cv.text("PUSH", 0.430, 0.600, 0.048, "#6e727a", 0.010, track=0.24,
            aspect=0.62)
    cv.ell(0.606, 0.600, 0.052, 0.052, "#eef0f4")               # return button
    cv.ell(0.606, 0.600, 0.032, 0.032, "#c2c6cc")
    cv.rect(0.336, 0.740, 0.664, 0.812, "#141519")              # coin cup
    cv.vgrad(0.336, 0.740, 0.664, 0.770, "#3a3c44", "#141519")
    for uu in (0.316, 0.684):                                   # hinge screws
        for vv in (0.372, 0.828):
            cv.ell(uu, vv, 0.014, 0.014, "#5c6068", 0.8)
    cv.vgrad(0.0, 0.940, 1.0, 1.0, "#0d0e11", "#08090b")        # kick
    _grain(cv, 8.0, 54)


@_panel("golden-tee-3d-golf.bezel")
def _gt_bezel(cv):
    """The screen surround.  The screen quad covers all but the outer ~6% of
    this tile, so the only things drawn are the two things that show: the pale
    wordmark line in the head margin, and the LIT YELLOW THREE-PANEL
    instruction strip along the bottom -- one of the few genuinely emissive
    surfaces on that wall, and directly legible in v4 7 and v4 6."""
    cv.fill("#101116")
    cv.vgrad(0.0, 0.0, 1.0, 1.0, "#181a20", "#0b0c0f")
    cv.rect(0.0, 0.0, 1.0, 0.028, "#26282e")
    cv.text("GOLDEN TEE", 0.500, 0.030, 0.020, "#7e828a", 0.005, track=0.30,
            aspect=0.62)
    cv.rect(0.0, 0.885, 1.0, 0.906, "#2a2c32")
    for (u0, u1) in ((0.045, 0.335), (0.355, 0.645), (0.665, 0.955)):
        cv.rect(u0, 0.912, u1, 0.988, "#c8a410")
        cv.rect(u0 + 0.006, 0.918, u1 - 0.006, 0.982, _GT_YEL)
        cv.rect(u0 + 0.030, 0.934, u1 - 0.030, 0.950, "#3c3208")
        cv.rect(u0 + 0.050, 0.958, u1 - 0.050, 0.970, "#3c3208")
    cv.rect(0.0, 0.988, 1.0, 1.0, "#0b0c0f")
    _grain(cv, 6.0, 55)


@_panel("golden-tee-3d-golf.deck")
def _gt_deck(cv):
    """The bright grass-green course the deck is printed with, plus the dark
    band of three yellow legend words along its back edge that the roster
    reads.  A WHITE TRACKBALL is centred with small buttons either side -- see
    DECKS; this machine gets NO joystick, which is the photograph."""
    cv.vgrad(0.0, 0.0, 1.0, 1.0, "#6ba148", "#4a7c33")
    for j in range(7):                                           # mown stripes
        v0 = j / 7.0
        if j % 2 == 0:
            cv.rect(0.0, v0, 1.0, v0 + 1.0 / 7.0, "#e6f0c0", 0.11)
    cv.poly([(0.0, 0.30), (0.34, 0.22), (0.72, 0.34), (1.0, 0.28),
             (1.0, 0.10), (0.0, 0.14)], "#3c6a2c")               # rough
    cv.poly([(0.0, 0.965), (1.0, 0.930), (1.0, 1.0), (0.0, 1.0)], "#335e26")
    cv.ell(0.700, 0.560, 0.230, 0.230, "#8ec063")                # putting green
    cv.ell(0.700, 0.560, 0.190, 0.190, "#a2d072")
    cv.ell(0.185, 0.640, 0.170, 0.150, "#dfd3a2")                # bunker
    cv.ell(0.185, 0.640, 0.140, 0.120, "#efe6c0")
    cv.poly([(0.30, 0.98), (0.46, 0.36), (0.56, 0.36), (0.44, 0.98)],
            "#c8cfa8", 0.35)                                     # cart path
    cv.seg((0.700, 0.560), (0.700, 0.400), "#f2f2ee", 0.014)     # flagstick
    cv.poly([(0.700, 0.400), (0.760, 0.424), (0.700, 0.448)], "#e03a2c")
    cv.ell(0.560, 0.700, 0.036, 0.036, "#fbfbf6")                # the ball
    _wear(cv, 0.0, 0.15, 1.0, 1.0, 8.0, 56, 2)

    cv.rect(0.0, 0.0, 1.0, 0.150, _GT_DARK)                      # legend band
    for (i, w) in enumerate(("GOLDEN", "TEE", "GOLF")):
        cv.rect(0.026 + i * 0.324, 0.016, 0.322 + i * 0.324, 0.132, "#0e1408")
        cv.text(w, 0.174 + i * 0.324, 0.074, 0.104, "#ffef7a", 0.024,
                track=0.10, aspect=0.60)
    cv.ring(0.500, 0.540, 0.205, 0.205, 0.032, "#1a2a12", 0.65)  # trackball
    for cu in (0.180, 0.820):
        cv.ring(cu, 0.330, 0.095, 0.095, 0.024, "#1a2a12", 0.6)
    cv.text("GOLDEN TEE", 0.150, 0.930, 0.062, "#20301a", 0.012, track=0.18,
            aspect=0.62, a=0.7)
    _grain(cv, 8.0, 57)


# =========================================================================
#  EXPORTS
# =========================================================================
# ROUND 5 REASSIGNED THE MACHINES.  This module drew star-wars-atari,
# street-fighter-2-champion-edition and north-1-graffiti-multicade in round 4;
# in round 5 art_g2 owns Street Fighter and art_g3 owns Star Wars and the
# graffiti multicade, and this module owns pac-man, nba-jam,
# tmnt-turtles-in-time and golden-tee-3d-golf.  The round-4 paint functions for
# the three handed-over machines are still in this file -- they cost nothing
# and they are the fallback if another module ends up not shipping one -- but
# they are NOT in PANELS, because atlas4 refuses a key two modules both claim.
# They are reachable as LEGACY_R4.
WRAPPED = ("pac-man", "nba-jam", "tmnt-turtles-in-time", "golden-tee-3d-golf")
HANDED_OVER = ("star-wars-atari", "street-fighter-2-champion-edition",
               "north-1-graffiti-multicade")

LEGACY_R4 = dict((k, v) for (k, v) in _REG.items()
                 if k.split(".")[0] in HANDED_OVER)
PANELS = dict((k, v) for (k, v) in _REG.items()
              if k.split(".")[0] in WRAPPED)


# ------------------------------------------------------------ the marquees
# "Round 4 gave each of your machines a marquee that works.  KEEP IT."  Taken
# literally: pac-man's and tmnt's marquees were drawn by round-4 art_g1 and
# golden-tee's by round-4 art_g3, and this module re-exports those functions
# BYTE-IDENTICALLY rather than redrawing them.  The two round-4 modules are
# vendored beside this one as `r4mq/g1.py` and `r4mq/g3.py` (verbatim copies of
# `_r5/art_g1_r4.bak.py` and `art_g3_r4.bak.py`) so the re-export cannot be
# broken by round-5 edits to the live art_g1 / art_g3.  nba-jam's marquee was
# already this module's and is unchanged above.
def _r4_marquee(mod, key):
    import importlib
    import os
    import sys
    d = os.path.dirname(os.path.abspath(__file__))
    if d not in sys.path:
        sys.path.insert(0, d)
    return importlib.import_module("r4mq." + mod).PANELS[key]


for _mod, _key in (("g1", "pac-man.marquee"),
                   ("g1", "tmnt-turtles-in-time.marquee"),
                   ("g3", "golden-tee-3d-golf.marquee")):
    PANELS[_key] = _r4_marquee(_mod, _key)
del _mod, _key


# =========================================================================
#  DECKS -- the control layout, for ar2.upright() to place as GEOMETRY
# =========================================================================
# The critics' second finding: "the same two-joystick deck (one red top, one
# blue top) over the same row of flat square buttons" on all sixteen machines.
# ar2.upright() hard-codes that:
#
#     for k in range(2):
#         jx = (-0.28 + 0.56 * k) * (bw / 2.20)
#         ... two 0.09 ft square shafts, two 0.13 ft square tops,
#         ... three 0.11 ft FLAT SQUARE buttons each, at two z rows
#
# A paint function cannot fix that, so the layout is declared here and the
# integrator consumes it in upright().  Where a machine is absent from DECKS,
# upright()'s existing loop is the right fallback.
#
# ---- COORDINATE FRAME.  Deliberately the SAME frame as the `.deck` art tile,
#      so a printed collar and the control that sits in it cannot drift apart.
#
#   u   across the machine, -0.5 .. +0.5.   local x = u * (bw - 0.12)
#       u = -0.5 is the x0 edge, which is the LEFT edge of the .deck tile.
#   v   along the deck, 0 at the BACK edge (z = ft + 0.04, up against the
#       screen) and 1 at the player's edge (z = fd - 0.06).
#           local z = (ft + 0.04) + v * ((fd - 0.06) - (ft + 0.04))
#       and with ar2's DECK_OUT that bracket is exactly 0.92 ft.
#       v is also the .deck tile's own v, top of tile = back of deck.
#   y   every control sits ON the deck surface, y = dy (dy already includes
#       the plinth by the time upright() reaches its control loop).
#
#   EVERY LENGTH IN THIS TABLE IS IN FEET.
#
# ---- SHAPES.
#   stick   {"u","v","shaft_r","shaft_h","shaft_color",
#            "top": "ball" | "bat" | "none", "top_d", "top_color"}
#           `top_d` is the ball's DIAMETER, or a bat-top's length.  A ball top
#           wants a sphere or an 8-segment cylinder+cap, NOT the 0.13 ft box
#           round 4 used -- every stick in the photographs is a round ball top.
#   button  {"u","v","r","h","shape": "round"|"square",
#            "profile": "convex"|"flat", "color"}
#           `r` is the RADIUS (or half-width for a square), `h` how proud of
#           the deck it stands.  "convex" wants a short cylinder with a domed
#           or tapered cap (r_top ~0.75 r) -- ar2's cylinder(r_top=) already
#           does this; "flat" is round 4's rect_up.
#   trackball {"u","v","r","color"}
#           a sphere half-sunk in the deck: draw a hemisphere of radius r
#           centred at y = dy, plus a dark ring bezel of radius r * 1.25.
#
# The emissive on ar2.BUTTONS is fine to keep on the coloured buttons; a white
# button should NOT be emissive or it blooms.
DECKS = {
    # --------------------------------------------------------------- PAC-MAN
    # v4 6 (268,190)-(330,240) and v3 1 (600,690)-(700,760): ONE red ball-top
    # stick at centre-left and a scattered row of SMALL round buttons in red,
    # white and blue across the width -- not two sticks, and not squares.
    "pac-man": {
        "why": "v4 6 / v3 1: single red ball-top stick left of centre, seven "
               "small round buttons in red / white / blue in two staggered "
               "rows to its right.",
        "sticks": [
            {"u": -0.304, "v": 0.640, "shaft_r": 0.040, "shaft_h": 0.185,
             "shaft_color": "#17171b", "top": "ball", "top_d": 0.115,
             "top_color": "#d8323a"},
        ],
        "buttons": [
            {"u": -0.100, "v": 0.400, "r": 0.052, "h": 0.030,
             "shape": "round", "profile": "convex", "color": "#d8323a"},
            {"u": -0.028, "v": 0.640, "r": 0.052, "h": 0.030,
             "shape": "round", "profile": "convex", "color": "#e8e8ea"},
            {"u": 0.044, "v": 0.400, "r": 0.052, "h": 0.030,
             "shape": "round", "profile": "convex", "color": "#2f6ad8"},
            {"u": 0.116, "v": 0.640, "r": 0.052, "h": 0.030,
             "shape": "round", "profile": "convex", "color": "#d8323a"},
            {"u": 0.188, "v": 0.400, "r": 0.052, "h": 0.030,
             "shape": "round", "profile": "convex", "color": "#e8e8ea"},
            {"u": 0.260, "v": 0.640, "r": 0.052, "h": 0.030,
             "shape": "round", "profile": "convex", "color": "#2f6ad8"},
            {"u": 0.332, "v": 0.400, "r": 0.052, "h": 0.030,
             "shape": "round", "profile": "convex", "color": "#d8323a"},
        ],
    },
    # --------------------------------------------------------------- NBA JAM
    # v4 7 (320,300)-(420,460): a BALL-TOP stick with a red ball at the near
    # station and round buttons in orange, white, red and blue in a shallow
    # arc.  The brief said NBA Jam has a trackball; I re-checked and it does
    # NOT -- see the report.  The white disc in that crop sits in the button
    # row at button size, and Golden Tee's trackball two machines away is
    # visibly a different object (bigger, proud, and with no collar).
    "nba-jam": {
        "why": "v4 7: two stations, black shafts with RED and BLUE ball tops, "
               "three round convex buttons each in a shallow arc. NO "
               "trackball on this machine.",
        "sticks": [
            {"u": -0.228, "v": 0.560, "shaft_r": 0.042, "shaft_h": 0.190,
             "shaft_color": "#141416", "top": "ball", "top_d": 0.135,
             "top_color": "#d8323a"},
            {"u": 0.228, "v": 0.560, "shaft_r": 0.042, "shaft_h": 0.190,
             "shaft_color": "#141416", "top": "ball", "top_d": 0.135,
             "top_color": "#2f6ad8"},
        ],
        "buttons": [
            {"u": -0.128, "v": 0.340, "r": 0.058, "h": 0.032,
             "shape": "round", "profile": "convex", "color": "#e05a1c"},
            {"u": -0.064, "v": 0.470, "r": 0.058, "h": 0.032,
             "shape": "round", "profile": "convex", "color": "#e8e8ea"},
            {"u": -0.128, "v": 0.600, "r": 0.058, "h": 0.032,
             "shape": "round", "profile": "convex", "color": "#2f6ad8"},
            {"u": 0.128, "v": 0.340, "r": 0.058, "h": 0.032,
             "shape": "round", "profile": "convex", "color": "#d8323a"},
            {"u": 0.064, "v": 0.470, "r": 0.058, "h": 0.032,
             "shape": "round", "profile": "convex", "color": "#e8e8ea"},
            {"u": 0.128, "v": 0.600, "r": 0.058, "h": 0.032,
             "shape": "round", "profile": "convex", "color": "#2f6ad8"},
        ],
    },
    # -------------------------------------------------------- TURTLES IN TIME
    # v4 7 (400,150)-(600,460): ball tops (one yellow, one cyan in the two
    # stations that are visible) and ONE LARGE yellow and ONE LARGE red button
    # per station -- much bigger buttons than any other machine in the room,
    # which is most of what makes this deck read.
    "tmnt-turtles-in-time": {
        "why": "v4 7: ball tops in yellow and cyan; one LARGE yellow (or "
               "cyan) and one LARGE red button per station. The real cabinet "
               "is four-player; this carcase is 2.04 ft wide and takes two.",
        "sticks": [
            {"u": -0.230, "v": 0.450, "shaft_r": 0.042, "shaft_h": 0.195,
             "shaft_color": "#141416", "top": "ball", "top_d": 0.145,
             "top_color": "#f2c22a"},
            {"u": 0.230, "v": 0.450, "shaft_r": 0.042, "shaft_h": 0.195,
             "shaft_color": "#141416", "top": "ball", "top_d": 0.145,
             "top_color": "#3ab8e8"},
        ],
        "buttons": [
            {"u": -0.092, "v": 0.330, "r": 0.072, "h": 0.036,
             "shape": "round", "profile": "convex", "color": "#f2c22a"},
            {"u": -0.092, "v": 0.580, "r": 0.072, "h": 0.036,
             "shape": "round", "profile": "convex", "color": "#d8322c"},
            {"u": 0.368, "v": 0.330, "r": 0.072, "h": 0.036,
             "shape": "round", "profile": "convex", "color": "#3ab8e8"},
            {"u": 0.368, "v": 0.580, "r": 0.072, "h": 0.036,
             "shape": "round", "profile": "convex", "color": "#d8322c"},
        ],
    },
    # --------------------------------------------------- GOLDEN TEE 3D GOLF
    # v4 7 (95,175)-(185,215): a WHITE TRACKBALL centred in the deck with two
    # small buttons either side.  NO joystick -- do not give this machine one.
    "golden-tee-3d-golf": {
        "why": "v4 7: white trackball centred, two small red buttons either "
               "side, NO joystick. The trackball is the machine's whole "
               "control interface and it is the only one in the room.",
        "sticks": [],
        "trackball": {"u": 0.0, "v": 0.540, "r": 0.125, "color": "#f4f4f0",
                      "bezel_color": "#1a1c18"},
        "buttons": [
            {"u": -0.320, "v": 0.330, "r": 0.055, "h": 0.030,
             "shape": "round", "profile": "convex", "color": "#d8323a"},
            {"u": 0.320, "v": 0.330, "r": 0.055, "h": 0.030,
             "shape": "round", "profile": "convex", "color": "#d8323a"},
        ],
    },
}


# =========================================================================
#  DOORS -- the coin door, which round 4 made identical on all sixteen
# =========================================================================
# ar2.upright() hard-codes
#
#     bx(sub, CPANEL, -0.34, 0.34, plinth + 0.30, plinth + 0.92, zf, zf+0.055)
#     bx(sub, CHR,    -0.26, 0.26, plinth + 0.52, plinth + 0.60, ...)
#
# -- a 0.68 x 0.62 ft grey plate dead centre and low, on every machine.  That
# is the "SAME centred grey coin-door rectangle at the same size and position"
# all three critics named, and on NBA Jam it lands straight through the middle
# of the printed badge.
#
# Each entry below is the plate for one machine, in the cabinet's own local
# frame: x is local x in FEET (0 = machine centre), y is height above the FLOOR
# in feet WITH the plinth already added, `proud` is how far the plate stands
# out of the front face (add to zf).  The `.front` artwork already draws the
# door -- slots, return, cup, keyline -- at exactly these coordinates, so the
# geometry only has to agree with it.
#
#   None  means THIS MACHINE HAS NO COIN DOOR: omit the two boxes entirely.
DOORS = {
    # tall, narrow, black, high on the yellow -- v3 1 (600,690)-(700,760)
    "pac-man": {
        "x": (-0.229, 0.237), "y": (1.017, 1.777), "proud": 0.045,
        "plate": "#15161c", "bezel": "#3a3c46",
        "return_cup": {"x": (-0.096, 0.046), "y": 1.437, "color": "#a9aeb6"},
        "coin_slots": 2,
        "why": "black rounded plate, TALLER than wide, centred, in the upper "
               "half of the lower front; one chrome return line and a white "
               "round return button at its right.",
    },
    # low, left, small and near-black: no bright plate reads anywhere on this
    # machine in v3 4 or v4 8, so it is drawn and built as black-on-black
    "nba-jam": {
        "x": (-0.984, -0.449), "y": (0.755, 1.220), "proud": 0.030,
        "plate": "#151318", "bezel": "#2e2126",
        "return_cup": {"x": (-0.834, -0.599), "y": 0.855, "color": "#241a1e"},
        "coin_slots": 2,
        "why": "no coin door reads on NBA Jam in any frame; it is built small, "
               "low, LEFT of the badge column and near-black rather than "
               "invented as a bright plate.",
    },
    # NO DOOR.  v3 4 shows this front uninterrupted from the logo block to the
    # brick riser, and v4 8 agrees.  Omit the plate.
    "tmnt-turtles-in-time": None,
    # the biggest and brightest door of the four -- v4 6 (374,230)-(432,285)
    "golden-tee-3d-golf": {
        "x": (-0.480, 0.480), "y": (0.449, 1.399), "proud": 0.070,
        "plate": "#22232a", "bezel": "#5a5d66",
        "return_cup": {"x": (-0.354, 0.354), "y": 0.610, "color": "#141519"},
        "coin_slots": 3,
        "why": "a large raised plate filling ~44% of the panel width with "
               "THREE vertical slots, a recessed PUSH return door with a white "
               "round button, and a coin cup below it.",
    },
}


# =========================================================================
#  DECK_MAT_REQUEST -- one line of a2kit.DECK_MAT, and it matters
# =========================================================================
# a2kit.ArtSet.deck() multiplies a deck tile by ART_DK (#4c4c4c, x0.30) unless
# DECK_MAT names something else, because an up-facing surface over-collects in
# this scene.  Three of these four decks are BRIGHT PRINTED ART -- a hardwood
# court, a brick street, a fairway -- and x0.30 turns all three to mud, which
# is why round 4 already granted TMNT "D".  NBA Jam's and Golden Tee's decks
# are authored here at near-true albedo for ART_D (#c9c9c9, x0.79); Pac-Man's
# is a BLACK deck and is authored LIFTED for ART_DK, so it must NOT change.
DECK_MAT_REQUEST = {
    "nba-jam": "D",                 # hardwood court -- currently ART_DK
    "tmnt-turtles-in-time": "D",    # already "D" in a2kit; no change
    "golden-tee-3d-golf": "D",      # grass fairway -- currently ART_DK
    "pac-man": None,                # leave on ART_DK: this deck IS black
}


# =========================================================================
#  PAYLOAD -- measured, not estimated
# =========================================================================
# Room 2 stood at 1535.4 KB against a 1536 KB cap BEFORE round 5, i.e. 0.6 KB
# over, and four agents were then asked to add artwork to it.  Numbers below
# are from scratchpad/arc4/art/bytes_g0_r5.py, which builds two atlases: an
# ISOLATED one (art_g0 round 5, every other machine round 4, from the vendored
# backups) so art_g0's own bill can be read off, and a LIVE one.
#
#   round 4, all three wall-run atlases                        163.1 KB
#   isolated: art_g0's four machines wrapped                   165.2 KB
#     -- east 76.3 (+2.5), north 41.5 (+0.0), south 47.4 (-0.4).  The south
#        atlas holds no art_g0 machine; that -0.4 is the dither change landing
#        on LEGACY_R4's Street Fighter panels, which art_g2 ships in round 5,
#        so art_g0's HONEST bill is east + north = +2.5 KB.
#   the same with SIZE_KEY_REQUEST applied                     +1.6 KB
#
# art_g0's own savings inside that: pac-man.side -628 B (a flat saturated
# yellow flank is cheaper than round 4's), golden-tee bezel -120 B, and the
# _flush dither dropped 0.90 -> 0.55 (-0.6 KB across the module, no visible
# banding -- see the note in _flush).  Its own spends: golden-tee.front +912 B
# for the big embossed coin door, tmnt.front +571 B for the brick riser,
# pac-man.deck +592 B for a deck that is no longer a flat black slab.
#
# THE ROOM CANNOT BE BROUGHT BACK UNDER FROM INSIDE ONE ART MODULE.  With all
# four round-5 modules as they stood when this was measured the three atlases
# come to 197.4 KB, +34.3 KB on round 4 -- so ~35 KB has to come off globally,
# and the only dials for that are in atlas4, which is the integrator's file.
# Measured on the LIVE merged set, each lever alone and then combined:
PAYLOAD_LEVERS = {
    "_measured_on": "all four round-5 art modules merged, east-7-no-machine "
                    "filled from art_g2_r4.bak.py; three wall-run atlases.",
    "live round-5, round-4 atlas4 settings": 197.0,
    "+ art_g0 SIZE_KEY_REQUEST": 196.6,
    "+ QUANT 16 -> 20": 178.9,
    "+ QUANT 16 -> 24": 160.3,
    "+ SIZE['marquee'] 120 -> 112": 189.7,
    "+ SIZE['marquee'] 120 -> 104": 178.8,
    "+ SIZE['front'] 96 -> 88": 191.5,
    "+ SIZE['side'] 64 -> 56": 194.2,
    "COMBO marquee 112 + front 88 + QUANT 20 + SIZE_KEY_REQUEST": 163.5,
    "_recommendation":
        "Take the COMBO: 163.5 KB is +0.4 KB on round 4 with FOUR modules' "
        "worth of new artwork in it, which leaves the room where it was.  "
        "QUANT 24 alone also clears the cap (160.3, -2.8) and is the smaller "
        "edit, but round 4 measured 24 as the point where banding starts to "
        "show on the marquees, and the marquees are the hero surface.  Do NOT "
        "reach for SIZE['side'] 56: it saves 3.2 KB and costs the two flanks "
        "that are actually visible (Star Wars', the multicade's).",
}

# Two flanks that no camera in this room can see.  atlas4.SIZE_KEY already
# exists for exactly this judgement in the other direction -- it RAISES Star
# Wars' and the multicade's flanks to 96 px because they stand at the end of
# their runs.  NBA Jam sits between Mortal Kombat (z 9.63) and TMNT (z 14.15)
# on 2.26 ft centres with a 2.16 ft carcase, and Pac-Man between the multicade
# (x 6.55) and NFL Blitz (x 11.30) with a 2.28 ft carcase: the gaps are 0.1-0.2
# ft and neither flank is visible in any of the eight round-4 frames.  Both
# tiles are still drawn in full; they just do not need 64 px.
SIZE_KEY_REQUEST = {
    "nba-jam.side": 48,
    "pac-man.side": 48,
}


# =========================================================================
#  WRAP_R5 -- what the integrator has to do
# =========================================================================
WRAP_R5 = {
    "claims": sorted(PANELS),
    "merge": [
        "art_g0 no longer exports star-wars-atari.*, "
        "street-fighter-2-champion-edition.* or north-1-graffiti-multicade.* "
        "-- art_g3 and art_g2 own those in round 5.  Nothing to delete "
        "anywhere; the duplicate-key check in atlas4 should now pass.",
        "If art_g2 or art_g3 ends up NOT shipping one of those three, "
        "art_g0.LEGACY_R4 still holds round 4's version of every panel for "
        "all three machines -- merge it in rather than losing a machine.",
        "east-7-no-machine is claimed by NO round-5 module as of this write. "
        "atlas4.EAST_SLUGS still lists it, so either art_g2's round-4 backup "
        "(art/art_g2_r4.bak.py) supplies it or the slot is finally deleted "
        "from EAST_RUN, which round 4 already recommended.",
        "art_g0 re-exports pac-man.marquee, tmnt-turtles-in-time.marquee and "
        "golden-tee-3d-golf.marquee from vendored copies of the ROUND-4 "
        "art_g1 / art_g3 (art/r4mq/g1.py, art/r4mq/g3.py).  They are "
        "byte-identical to what shipped in round 4.  Do not redraw them, and "
        "do not delete art/r4mq/.",
    ],
    "ar2_changes_required": [
        "upright(): consume art_g0.DECKS[slug] instead of the hard-coded "
        "two-stick / six-square-button loop.  Frame and shapes are documented "
        "on DECKS above.  Machines absent from DECKS keep the old loop.",
        "upright(): consume art_g0.DOORS[slug] for the coin-door plate; a "
        "value of None means omit the plate entirely (TMNT).",
    ],
    "atlas4_changes_recommended": [
        "SIZE_KEY.update(art_g0.SIZE_KEY_REQUEST) -- two fully occluded flanks "
        "from 64 to 48 px, -0.9 KB, nothing visible lost.",
        "The room is over its cap with four modules' new artwork in it and no "
        "single module can fix that.  PAYLOAD_LEVERS above is a measured menu; "
        "the COMBO row lands the three atlases at 163.5 KB, +0.4 on round 4.",
    ],
    "a2kit_changes_required": [
        "DECK_MAT: add 'nba-jam': 'D' and 'golden-tee-3d-golf': 'D'.  Without "
        "them the court and the fairway render at 0.30 albedo and go to mud.",
        "CARCASE is UNCHANGED for all four machines -- pac-man #d8b81e, "
        "nba-jam #5e1a20, tmnt #3f9b4a, golden-tee #2a2b2f are all right and "
        "the artwork is drawn to sit against them.",
        "MARQUEE is UNCHANGED for all four.",
    ],
    "screens": "Pac-Man's, NBA Jam's, TMNT's and Golden Tee's screens are ALL "
               "DARK in every frame that shows them (v4 6, v4 7, v3 1, v3 4). "
               "No attract art is invented for any of them and ar2.SCRN is "
               "left alone.  The one genuinely lit surface among the four is "
               "Golden Tee's yellow three-panel instruction strip, which is "
               "drawn into golden-tee-3d-golf.bezel.",
}


# What each panel claims, so a critic can check the claim and not just the look.
NOTES_R5 = {
    "pac-man.side":
        "v4 6 (262,110)-(335,285): saturated yellow flank, floor to head, "
        "maroon head trim and kick. The roster says this machine carries NO "
        "large graphic on its flanks and none is invented; what makes it read "
        "is that it is the only saturated body in the room, edge to edge.",
    "pac-man.front":
        "v3 1 (585,545)-(700,810) at 5x, crop art/crops_r5/pac_v31.png. "
        "Yellow edge to edge; TALL NARROW black coin plate high and centred "
        "with a chrome return line and a white return button; blue ghost with "
        "white eyes and red trailing feet; yellow Pac and a dot trail; navy "
        "MAZE ELBOW brackets across the bottom edge. Every element is read "
        "off that crop.",
    "pac-man.deck":
        "v4 6 (268,190)-(330,240): black deck, maroon lip along the front "
        "edge, yellow legend, small round buttons. Authored LIFTED because "
        "a2kit multiplies it by ART_DK.",
    "nba-jam.side":
        "v4 7 (405,160)-(470,700): the red pebble / diamond-plate wrap and "
        "the orange-brown leather riser carrying round the base. Round 4 "
        "authored this flank flat black on the roster's 'no legible graphic' "
        "and shipped a slab; the grain and the kick band are both visible.",
    "nba-jam.front":
        "v3 4 (320,690)-(420,830) at 5x (art/crops_r5/e_run_v34.png): white "
        "starburst crown, silver-ringed flaming basketball, red NBA JAM, and "
        "the three-panel pebble riser with its own white starburst. The coin "
        "door is drawn black-on-black LOW AND LEFT because no bright plate "
        "reads on this machine in any frame.",
    "nba-jam.deck":
        "v4 7 (150,120)-(470,450): hardwood court, both keys, the centre "
        "circle, the logo lying on the boards, a maroon front lip, and "
        "printed collars under the layout DECKS declares.",
    "tmnt-turtles-in-time.side":
        "Roster: 'black flank carrying dark turtle/city artwork, edged all "
        "round by bright green T-molding'. Drawn as a night skyline of brick "
        "blocks with lit windows over a dark street with a manhole, and one "
        "turtle. The buildings and the turtle are a reconstruction of a scene "
        "the photographs establish only as 'dark city artwork'.",
    "tmnt-turtles-in-time.front":
        "v3 4 (400,690)-(500,830) dead-on: TEENAGE MUTANT NINJA in small red "
        "caps, TURTLES in green with a yellow-orange outline, TURTLES IN TIME "
        "in a pale slab, a short red line, and a brick riser carrying a "
        "turtle illustration and a green TURTLES plaque at its right end. NO "
        "coin door -- none reads in any frame, and DOORS asks for none.",
    "tmnt-turtles-in-time.deck":
        "v4 7 (400,150)-(600,460): brown/red brick New York street with "
        "facades, windows and fire escapes, TURTLES wordmarks repeated in "
        "green / blue / red, a manhole, and the four small square "
        "character-portrait decals along the player's edge.",
    "golden-tee-3d-golf.side":
        "Roster and v4 6 agree the flanks are PLAIN BLACK ('the green lives "
        "entirely on the marquee, the instruction strip and the deck'). Built "
        "as a printed black -- brushed vinyl, panel seams, a matt kick, a "
        "small silver wordmark -- and DECLARED as deliberately plain.",
    "golden-tee-3d-golf.front":
        "v4 6 (374,143)-(432,295) and v4 7 (98,116)-(175,300): the lower "
        "front is BLACK, and this panel stays black. What carries it is what "
        "the photographs show carrying it -- a large raised coin door with "
        "three vertical slots, a recessed PUSH return with a white button and "
        "a coin cup, plus the silver GOLDEN TEE wordmark high under the deck.",
    "golden-tee-3d-golf.bezel":
        "v4 7 (95,175)-(185,215): the LIT YELLOW three-panel instruction "
        "strip below the screen, which is one of the few genuinely emissive "
        "surfaces on the north wall, plus the pale wordmark line in the head "
        "margin. Everything between them is covered by the screen quad.",
    "golden-tee-3d-golf.deck":
        "v4 7 (95,175)-(185,215): the bright grass-green course -- mown "
        "stripes, rough, a putting green with a flag, a sand bunker, a ball, "
        "a cart path -- under the dark band of three yellow legend words the "
        "roster reads along its back edge. The trackball is GEOMETRY; see "
        "DECKS.",
    "_screens": "All four screens are DARK in every frame. No attract loop is "
                "invented for any of them.",
    "_photo_derived": "NONE. Every pixel in this module is drawn.",
}

# Round 4's notes, for the three machines handed to art_g2 / art_g3 in round 5
# and still present here as LEGACY_R4.
NOTES = {
    "star-wars-atari.marquee": "NOT VISIBLE in any photograph -- dark and "
                               "generic on purpose, no title invented.",
    "star-wars-atari.side":
        "v4 9 (150,220)-(300,480) and v4 8 (0,90)-(140,340): yellow carcase, "
        "black stepped art panel, TIEs, X-wing, Death Star curve, inset panel. "
        "The blue LED strip is a fixture the owner added and is deliberately "
        "NOT printed here.",
    "star-wars-atari.front": "NOT VISIBLE -- plain dark with yellow returns.",
    "star-wars-atari.deck": "NOT VISIBLE -- plain black with a yellow front "
                            "return.",
    "nba-jam.marquee": "v4 7 (320,150)-(420,205) at 12x. Letterforms, roundel "
                       "and rails all read directly from that crop.",
    "nba-jam.side": "No legible graphic at any magnification -- black vinyl "
                    "with maroon molding bleed, as photographed.",
    "nba-jam.front": "v4 3 (230,180)-(300,260): flaming-ball badge over the "
                     "pebble-leather riser with its white starburst.",
    "nba-jam.deck": "v4 7 (150,120)-(470,450): hardwood court, key, arcs, "
                    "centre circle and the logo lying on the boards.",
    "street-fighter-2-champion-edition.marquee":
        "v3 4 (930,565)-(1010,600) at 16x. CHAMPION / EDITION / silver wings "
        "are read. The green-gold centre wordmark does NOT resolve letter by "
        "letter in any frame; it is reconstructed as STREET FIGHTER II from "
        "the badge, and that is a reconstruction, not a reading.",
    "street-fighter-2-champion-edition.side":
        "Not resolvable -- the machine is near head-on in every frame. Built "
        "as the pale laminate the photographs do establish, no invented art.",
    "street-fighter-2-champion-edition.front":
        "v3 4 (920,730)-(1030,810): royal-blue riser, ghosted lunging fighter, "
        "CAPCOM on a dark plate low and left.",
    "street-fighter-2-champion-edition.deck":
        "v3 4 / v4 8: black deck, silver leading edge, checker strip. "
        "Individual controls do not resolve so none are printed.",
    "north-1-graffiti-multicade.marquee":
        "v3 1 (515,555)-(625,620) at 11x: pale illegible lettering, a small "
        "maroon patch, a light angular mark at the right end. NO title "
        "resolves in any frame at any magnification, so none is printed.",
    "north-1-graffiti-multicade.side":
        "v3 1 (520,570)-(620,830) at 7x and v4 6 (225,115)-(290,285) at 10x: "
        "pale line-work wrap, the almond ellipse, the diagonal slash, the "
        "glyph scatter. Grey-on-black per the neutral v4 6 exposure.",
    "north-1-graffiti-multicade.front":
        "Same wrap, drawn to the FRONT's own structure: two panels split at "
        "mid height, the coin-plunger dot, the printed QR square.",
    "north-1-graffiti-multicade.deck":
        "v4 6: the deepest deck on the north wall, two clusters, no printed "
        "legend.",
}
