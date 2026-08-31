"""Round-4 printed cabinet artwork, group 1 (four machines).

Marvel Super Heroes (east 1) / TMNT: Turtles in Time (east 5) /
Time Crisis (south 2) / Pac-Man (north 1).

Round 3's atlas was one motif -- a gradient, a header strip and an off-centre
blob -- repeated twelve times in different hues, plus four "marquees" whose
lettering was a row of rectangles.  Everything here is drawn as the machine's
own graphic: real glyph outlines from the stroke font below, and shapes that
are that game's shapes (Pac-Man's ghost and maze elbows, the Turtles' brick
street, Time Crisis's raked italic lockup, Marvel's comic-panel collage).

TWO THINGS THE INTEGRATOR MUST KNOW
-----------------------------------
1.  ``ASPECT[key]`` is the width/height of the real-world quad each panel is
    mapped onto.  a2kit maps a SQUARE atlas tile onto a marquee band of about
    2.6 ft x 0.72 ft, so a square-authored marquee renders stretched ~3.5x
    horizontally -- which is a large part of why round 3's marquees read as a
    pattern rather than a title.  Every panel here is therefore authored
    PRE-COMPENSATED: drawing happens in a normalised frame that is ``A`` wide
    and 1 tall, and is squeezed into the square tile on the way out.  If you
    map a panel onto a quad of a different aspect, change ``ASPECT`` and
    re-render -- do not rescale the tile.
2.  ``MATERIAL_HINT[key]`` says which of a2kit's materials the panel expects.
    These are true printed albedos: a black cabinet front is authored black.
    Putting the TMNT control deck (a bright brick scene) through ``ART_DK``
    (#4c4c4c) will crush it -- decks here want ``ART_D`` at most.

Pure stdlib.  ``paint(px, ox, oy, tile)`` writes ``px[y][x] = (r, g, b)`` into
the square (ox, oy)-(ox+tile, oy+tile), with a2kit's 4x4 ordered dither and
round-to-8 quantisation so the shared PNG stays small.
"""

import math

TILE = 256

_BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


# --------------------------------------------------------------- colour utils
def _hx(c):
    c = c.lstrip("#")
    return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16))


def _mix(a, b, t):
    return (a[0] + (b[0] - a[0]) * t,
            a[1] + (b[1] - a[1]) * t,
            a[2] + (b[2] - a[2]) * t)


def _clamp8(v):
    return 0 if v < 0 else (255 if v > 255 else int(v))


def _hash(x, y, s):
    n = (x * 374761393 + y * 668265263 + s * 2654435761) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0


# ------------------------------------------------------------- a stroke font
# y = 0 is the cap line, y = 1 the baseline; x runs 0..(glyph width), both in
# cap-height units.  Filled by drawing each polyline as a thick round-capped
# stroke, so one skeleton serves light type, fat bubble caps and outlined
# display type alike -- which is what lets "PAC-MAN" read as PAC-MAN.
def _ell(cx, cy, rx, ry, n=16, a0=0.0, a1=2 * math.pi):
    return [(cx + rx * math.cos(a0 + (a1 - a0) * i / n),
             cy + ry * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


_O = _ell(0.46, 0.5, 0.46, 0.49)

FONT = {
    " ": [],
    "A": [[(0.0, 1.0), (0.45, 0.0), (0.9, 1.0)], [(0.16, 0.63), (0.74, 0.63)]],
    "B": [[(0.0, 0.0), (0.0, 1.0)],
          [(0.0, 0.0), (0.6, 0.0), (0.8, 0.14), (0.8, 0.34), (0.6, 0.49),
           (0.0, 0.49)],
          [(0.0, 0.49), (0.66, 0.49), (0.86, 0.65), (0.86, 0.85),
           (0.64, 1.0), (0.0, 1.0)]],
    "C": [[(0.9, 0.2), (0.7, 0.02), (0.32, 0.02), (0.04, 0.24), (0.04, 0.76),
           (0.32, 0.98), (0.7, 0.98), (0.9, 0.8)]],
    "D": [[(0.0, 0.0), (0.0, 1.0)],
          [(0.0, 0.0), (0.52, 0.0), (0.86, 0.28), (0.86, 0.72), (0.52, 1.0),
           (0.0, 1.0)]],
    "E": [[(0.84, 0.02), (0.0, 0.02), (0.0, 0.98), (0.84, 0.98)],
          [(0.0, 0.5), (0.66, 0.5)]],
    "F": [[(0.84, 0.02), (0.0, 0.02), (0.0, 1.0)], [(0.0, 0.5), (0.64, 0.5)]],
    "G": [[(0.9, 0.2), (0.7, 0.02), (0.32, 0.02), (0.04, 0.24), (0.04, 0.76),
           (0.32, 0.98), (0.7, 0.98), (0.9, 0.78), (0.9, 0.55), (0.52, 0.55)]],
    "H": [[(0.0, 0.0), (0.0, 1.0)], [(0.84, 0.0), (0.84, 1.0)],
          [(0.0, 0.5), (0.84, 0.5)]],
    "I": [[(0.14, 0.0), (0.14, 1.0)]],   # _ADV widened below, see _ADV[]
    "J": [[(0.74, 0.0), (0.74, 0.76), (0.52, 0.98), (0.24, 0.98),
           (0.02, 0.76)]],
    "K": [[(0.0, 0.0), (0.0, 1.0)], [(0.8, 0.0), (0.08, 0.54)],
          [(0.3, 0.38), (0.86, 1.0)]],
    "L": [[(0.0, 0.0), (0.0, 0.98), (0.78, 0.98)]],
    "M": [[(0.0, 1.0), (0.0, 0.0), (0.5, 0.62), (1.0, 0.0), (1.0, 1.0)]],
    "N": [[(0.0, 1.0), (0.0, 0.0), (0.84, 1.0), (0.84, 0.0)]],
    "O": [_O],
    "P": [[(0.0, 1.0), (0.0, 0.0), (0.62, 0.0), (0.84, 0.18), (0.84, 0.38),
           (0.62, 0.56), (0.0, 0.56)]],
    "Q": [_O, [(0.56, 0.68), (0.96, 1.06)]],
    "R": [[(0.0, 1.0), (0.0, 0.0), (0.6, 0.0), (0.82, 0.18), (0.82, 0.37),
           (0.6, 0.55), (0.0, 0.55)], [(0.42, 0.55), (0.88, 1.0)]],
    "S": [[(0.86, 0.16), (0.66, 0.02), (0.26, 0.02), (0.05, 0.18),
           (0.05, 0.36), (0.28, 0.48), (0.64, 0.48), (0.87, 0.62),
           (0.87, 0.82), (0.64, 0.98), (0.22, 0.98), (0.02, 0.82)]],
    "T": [[(0.0, 0.02), (0.88, 0.02)], [(0.44, 0.02), (0.44, 1.0)]],
    "U": [[(0.0, 0.0), (0.0, 0.72), (0.22, 0.98), (0.62, 0.98), (0.84, 0.72),
           (0.84, 0.0)]],
    "V": [[(0.0, 0.0), (0.44, 1.0), (0.88, 0.0)]],
    "W": [[(0.0, 0.0), (0.2, 1.0), (0.5, 0.34), (0.8, 1.0), (1.0, 0.0)]],
    "X": [[(0.0, 0.0), (0.84, 1.0)], [(0.84, 0.0), (0.0, 1.0)]],
    "Y": [[(0.0, 0.0), (0.42, 0.5), (0.84, 0.0)], [(0.42, 0.5), (0.42, 1.0)]],
    "Z": [[(0.02, 0.02), (0.86, 0.02), (0.02, 0.98), (0.88, 0.98)]],
    "0": [_ell(0.42, 0.5, 0.42, 0.49)],
    "1": [[(0.06, 0.2), (0.3, 0.02), (0.3, 1.0)]],
    "2": [[(0.04, 0.2), (0.24, 0.02), (0.62, 0.02), (0.84, 0.22),
           (0.78, 0.44), (0.03, 0.98), (0.86, 0.98)]],
    "3": [[(0.04, 0.14), (0.26, 0.02), (0.64, 0.02), (0.84, 0.19),
           (0.62, 0.46), (0.3, 0.48)],
          [(0.62, 0.46), (0.86, 0.66), (0.86, 0.82), (0.62, 0.98),
           (0.22, 0.98), (0.02, 0.82)]],
    "4": [[(0.64, 1.0), (0.64, 0.02), (0.03, 0.7), (0.86, 0.7)]],
    "5": [[(0.84, 0.02), (0.12, 0.02), (0.06, 0.44), (0.5, 0.4),
           (0.84, 0.58), (0.84, 0.82), (0.56, 0.98), (0.18, 0.98),
           (0.02, 0.84)]],
    "6": [[(0.8, 0.06), (0.4, 0.02), (0.08, 0.3), (0.06, 0.78),
           (0.3, 0.98), (0.6, 0.98), (0.82, 0.78), (0.8, 0.6),
           (0.56, 0.46), (0.24, 0.5), (0.06, 0.7)]],
    "7": [[(0.02, 0.02), (0.86, 0.02), (0.34, 1.0)]],
    "8": [_ell(0.44, 0.26, 0.36, 0.25), _ell(0.44, 0.74, 0.42, 0.25)],
    "9": [[(0.06, 0.94), (0.46, 0.98), (0.78, 0.7), (0.8, 0.22),
           (0.56, 0.02), (0.26, 0.02), (0.04, 0.22), (0.06, 0.4),
           (0.3, 0.54), (0.62, 0.5), (0.8, 0.3)]],
    "-": [[(0.06, 0.52), (0.6, 0.52)]],
    ".": [[(0.1, 0.96), (0.16, 0.96)]],
    ":": [[(0.1, 0.3), (0.16, 0.3)], [(0.1, 0.86), (0.16, 0.86)]],
    "!": [[(0.12, 0.0), (0.12, 0.66)], [(0.12, 0.94), (0.16, 0.94)]],
    "'": [[(0.1, 0.0), (0.06, 0.24)]],
    "2ND": [],
}

_ADV = {}
for _ch, _st in FONT.items():
    if not _st:
        _ADV[_ch] = 0.42
    else:
        _ADV[_ch] = max(p[0] for pl in _st for p in pl)
_ADV["I"] = 0.28
_ADV["1"] = 0.40
_ADV[" "] = 0.42
_ADV["."] = 0.2
_ADV[":"] = 0.2
_ADV["'"] = 0.18
_ADV["!"] = 0.22


# ------------------------------------------------------------------- canvas
class Cv(object):
    """A drawing surface in a normalised frame ``A`` wide by 1 tall.

    Everything is authored in that frame, so proportions are the printed
    artwork's real proportions whatever the tile resolution and whatever the
    quad's aspect.  ``blit`` squeezes it into the square atlas tile.
    """

    def __init__(self, tile, A):
        self.n = tile
        self.A = float(A)
        self.b = [[[0.0, 0.0, 0.0] for _ in range(tile)] for _ in range(tile)]
        self.aa = 0.6 / tile          # half a pixel, in v units

    # ---- coordinate helpers
    def px(self, u):
        return u / self.A * self.n

    def py(self, v):
        return v * self.n

    def _bbox(self, u0, v0, u1, v1, pad=0.0):
        x0 = int(math.floor(self.px(min(u0, u1) - pad)))
        x1 = int(math.ceil(self.px(max(u0, u1) + pad)))
        y0 = int(math.floor(self.py(min(v0, v1) - pad)))
        y1 = int(math.ceil(self.py(max(v0, v1) + pad)))
        return (max(0, x0), max(0, y0), min(self.n, x1 + 1),
                min(self.n, y1 + 1))

    # ---- primitives
    def fill(self, c):
        for row in self.b:
            for p in row:
                p[0], p[1], p[2] = c[0], c[1], c[2]

    def _put(self, x, y, c, a):
        if a <= 0.0:
            return
        p = self.b[y][x]
        if a >= 1.0:
            p[0], p[1], p[2] = c[0], c[1], c[2]
        else:
            p[0] += (c[0] - p[0]) * a
            p[1] += (c[1] - p[1]) * a
            p[2] += (c[2] - p[2]) * a

    def rect(self, u0, v0, u1, v1, c, a=1.0):
        x0, y0, x1, y1 = self._bbox(u0, v0, u1, v1)
        fx0, fx1 = self.px(min(u0, u1)), self.px(max(u0, u1))
        fy0, fy1 = self.py(min(v0, v1)), self.py(max(v0, v1))
        for y in range(y0, y1):
            cy = min(y + 1.0, fy1) - max(float(y), fy0)
            if cy <= 0:
                continue
            for x in range(x0, x1):
                cx = min(x + 1.0, fx1) - max(float(x), fx0)
                if cx <= 0:
                    continue
                self._put(x, y, c, a * min(1.0, cx) * min(1.0, cy))

    def grad(self, u0, v0, u1, v1, c0, c1, horiz=False, a=1.0):
        x0, y0, x1, y1 = self._bbox(u0, v0, u1, v1)
        for y in range(y0, y1):
            for x in range(x0, x1):
                t = ((self.px(u1) - x) / max(1e-6, self.px(u1) - self.px(u0))
                     if horiz else
                     (y - self.py(v0)) / max(1e-6, self.py(v1) - self.py(v0)))
                t = 0.0 if t < 0 else (1.0 if t > 1 else t)
                if horiz:
                    t = 1.0 - t
                self._put(x, y, _mix(c0, c1, t), a)

    def poly(self, pts, c, a=1.0):
        if len(pts) < 3:
            return
        P = [(self.px(u), self.py(v)) for (u, v) in pts]
        ys = [p[1] for p in P]
        xs = [p[0] for p in P]
        y0 = max(0, int(math.floor(min(ys))))
        y1 = min(self.n, int(math.ceil(max(ys))) + 1)
        x0 = max(0, int(math.floor(min(xs))))
        x1 = min(self.n, int(math.ceil(max(xs))) + 1)
        if y1 <= y0 or x1 <= x0:
            return
        w = x1 - x0
        SUB = 3
        for y in range(y0, y1):
            cov = [0.0] * w
            for s in range(SUB):
                sy = y + (s + 0.5) / SUB
                xsx = []
                for i in range(len(P)):
                    ax, ay = P[i]
                    bx, by = P[(i + 1) % len(P)]
                    if (ay <= sy < by) or (by <= sy < ay):
                        xsx.append(ax + (bx - ax) * (sy - ay) / (by - ay))
                if not xsx:
                    continue
                xsx.sort()
                for k in range(0, len(xsx) - 1, 2):
                    sa, sb = xsx[k], xsx[k + 1]
                    if sb <= x0 or sa >= x1:
                        continue
                    ia = max(x0, int(math.floor(sa)))
                    ib = min(x1 - 1, int(math.ceil(sb)) - 1)
                    for x in range(ia, ib + 1):
                        o = min(x + 1.0, sb) - max(float(x), sa)
                        if o > 0:
                            cov[x - x0] += min(1.0, o) / SUB
        # (span accumulation happens per sub-row above; write once per row)
            for x in range(x0, x1):
                cvg = cov[x - x0]
                if cvg > 0.002:
                    self._put(x, y, c, a * min(1.0, cvg))

    def disc(self, u, v, r, c, a=1.0, ry=None, a0=None, a1=None):
        rv = r if ry is None else ry
        x0, y0, x1, y1 = self._bbox(u - r, v - rv, u + r, v + rv, self.aa * 2)
        aa = self.aa
        for y in range(y0, y1):
            dv = (y + 0.5) / self.n - v
            for x in range(x0, x1):
                du = (x + 0.5) / self.n * self.A - u
                d = math.hypot(du * rv / max(1e-6, r), dv)
                if a0 is not None:
                    ang = math.atan2(dv, du)
                    if ang < 0:
                        ang += 2 * math.pi
                    lo, hi = a0 % (2 * math.pi), a1 % (2 * math.pi)
                    ok = (lo <= ang <= hi) if lo <= hi else (
                        ang >= lo or ang <= hi)
                    if not ok:
                        continue
                cvg = (rv + aa - d) / (2 * aa)
                if cvg > 0:
                    self._put(x, y, c, a * min(1.0, cvg))

    def seg(self, u0, v0, u1, v1, w, c, a=1.0):
        h = w * 0.5
        x0, y0, x1, y1 = self._bbox(u0, v0, u1, v1, h + self.aa * 2)
        du, dv = u1 - u0, v1 - v0
        L2 = du * du + dv * dv
        aa = self.aa
        for y in range(y0, y1):
            pv = (y + 0.5) / self.n
            for x in range(x0, x1):
                pu = (x + 0.5) / self.n * self.A
                if L2 < 1e-12:
                    d = math.hypot(pu - u0, pv - v0)
                else:
                    t = ((pu - u0) * du + (pv - v0) * dv) / L2
                    t = 0.0 if t < 0 else (1.0 if t > 1 else t)
                    d = math.hypot(pu - u0 - du * t, pv - v0 - dv * t)
                cvg = (h + aa - d) / (2 * aa)
                if cvg > 0:
                    self._put(x, y, c, a * min(1.0, cvg))

    def path(self, pl, w, c, a=1.0):
        for i in range(len(pl) - 1):
            self.seg(pl[i][0], pl[i][1], pl[i + 1][0], pl[i + 1][1], w, c, a)

    def noise(self, amp, seed, mode="add", u0=0.0, v0=0.0, u1=None, v1=None):
        """Printed-vinyl grain as a 16x16 TILED cell, not white noise -- see
        the note in the module header about what white noise costs a PNG."""
        u1 = self.A if u1 is None else u1
        v1 = 1.0 if v1 is None else v1
        x0, y0, x1, y1 = self._bbox(u0, v0, u1, v1)
        for y in range(y0, y1):
            for x in range(x0, x1):
                d = (_hash(x & 15, y & 15, seed) - 0.5) * 2.0 * amp
                p = self.b[y][x]
                if mode == "mul":
                    f = 1.0 + d
                    p[0] *= f
                    p[1] *= f
                    p[2] *= f
                else:
                    p[0] += d
                    p[1] += d
                    p[2] += d

    # ---- type
    def layout(self, s, u, v, h, track=0.14, ital=0.0, arch=0.0, cond=1.0,
               align="l"):
        """Return the string's polylines, already placed, plus its width."""
        adv = []
        tot = 0.0
        for ch in s:
            a = _ADV.get(ch, 0.7) * h * cond
            adv.append(a)
            tot += a + track * h
        tot -= track * h if s else 0.0
        if align == "c":
            ux = u - tot * 0.5
        elif align == "r":
            ux = u - tot
        else:
            ux = u
        out = []
        n = max(1, len(s) - 1)
        for i, ch in enumerate(s):
            t = (2.0 * i / n - 1.0) if len(s) > 1 else 0.0
            dy = arch * (t * t)
            for pl in FONT.get(ch, []):
                q = []
                for (gx, gy) in pl:
                    px = ux + gx * h * cond + (1.0 - gy) * ital * h
                    py = v + gy * h + dy
                    q.append((px, py))
                out.append(q)
            ux += adv[i] + track * h
        return out, tot

    def text(self, s, u, v, h, c, w, track=0.14, ital=0.0, arch=0.0,
             cond=1.0, align="l", outline=None, ow=0.0, shadow=None,
             sh=(0.0, 0.0), a=1.0):
        pls, tot = self.layout(s, u, v, h, track, ital, arch, cond, align)
        if shadow is not None:
            for pl in pls:
                self.path([(x + sh[0], y + sh[1]) for (x, y) in pl],
                          w + ow * 2, shadow, a)
        if outline is not None and ow > 0:
            for pl in pls:
                self.path(pl, w + ow * 2, outline, a)
        for pl in pls:
            self.path(pl, w, c, a)
        return tot

    def width(self, s, h, track=0.14, cond=1.0):
        return self.layout(s, 0, 0, h, track, 0, 0, cond)[1]

    # ---- out
    def blit(self, px, ox, oy, tile):
        for y in range(tile):
            row = self.b[y]
            orow = px[oy + y]
            by = _BAYER[y & 3]
            for x in range(tile):
                n = (by[x & 3] - 7.5) * 0.90
                p = row[x]
                orow[ox + x] = (
                    _clamp8(round((p[0] + n) / 8.0) * 8),
                    _clamp8(round((p[1] + n) / 8.0) * 8),
                    _clamp8(round((p[2] + n) / 8.0) * 8))


# ----------------------------------------------------------- shared elements
def _bricks(cv, u0, v0, u1, v1, base, mortar, ch, cw, seed, jitter=14):
    """Running-bond masonry.  Used only by the Turtles machine."""
    cv.rect(u0, v0, u1, v1, mortar)
    r = 0
    v = v0
    while v < v1:
        off = 0.0 if (r % 2 == 0) else cw * 0.5
        u = u0 - off
        cbi = 0
        while u < u1:
            a, b = max(u0, u + 0.008), min(u1, u + cw - 0.008)
            if b > a:
                k = (_hash(int(u * 900), r * 7, seed) - 0.5) * jitter
                cv.rect(a, max(v0, v + 0.006), b,
                        min(v1, v + ch - 0.006),
                        (base[0] + k, base[1] + k * 0.8, base[2] + k * 0.6))
            u += cw
            cbi += 1
        v += ch
        r += 1


def _turtle_logo(cv, u, v, h, cond=0.80):
    """The 'TEENAGE MUTANT NINJA / TURTLES' lockup, arched, as printed.

    ``h`` is the cap height of TURTLES; the whole lockup is about 5.6*h*cond
    wide and 1.5*h tall, which is the real marquee's proportion.
    """
    red = _hx("#c9202a")
    grn = _hx("#5fbf2b")
    ylw = _hx("#f5c119")
    blk = (10, 12, 10)
    top = h * 0.26
    bw = cv.width("TEENAGE MUTANT NINJA", top, 0.08, cond * 0.95) * 0.5
    cv.poly([(u - bw - top * 0.5, v + top * 1.30), (u + bw, v - top * 0.05),
             (u + bw + top * 0.5, v + top * 0.72),
             (u - bw, v + top * 2.05)], red)
    cv.text("TEENAGE MUTANT NINJA", u, v + top * 0.42, top, (250, 246, 240),
            top * 0.16, track=0.08, cond=cond * 0.95, arch=top * 0.10,
            align="c")
    cv.text("TURTLES", u, v + top * 2.10, h, grn, h * 0.19, track=0.02,
            cond=cond, arch=h * 0.13, align="c", outline=ylw, ow=h * 0.070,
            shadow=blk, sh=(h * 0.085, h * 0.080))


def _turtle_figure(cv, u, v, s, band, flip=False):
    """One turtle: shell, head, bandana, arms.  Crude but it is a turtle."""
    sk = _hx("#5ea832")
    dk = _hx("#2f6b1c")
    shell = _hx("#8a5a1e")
    d = -1.0 if flip else 1.0
    cv.disc(u, v + s * 0.62, s * 0.34, shell, ry=s * 0.40)
    cv.disc(u, v + s * 0.62, s * 0.20, _hx("#6d4415"), ry=s * 0.24)
    cv.seg(u - s * 0.30 * d, v + s * 0.52, u - s * 0.62 * d, v + s * 0.30,
           s * 0.16, sk)
    cv.seg(u + s * 0.30 * d, v + s * 0.60, u + s * 0.60 * d, v + s * 0.80,
           s * 0.16, sk)
    cv.seg(u - s * 0.15, v + s * 0.98, u - s * 0.22, v + s * 1.28, s * 0.17, sk)
    cv.seg(u + s * 0.15, v + s * 0.98, u + s * 0.24, v + s * 1.28, s * 0.17, sk)
    cv.disc(u, v + s * 0.20, s * 0.27, sk, ry=s * 0.25)
    cv.rect(u - s * 0.29, v + s * 0.12, u + s * 0.29, v + s * 0.24, band)
    cv.seg(u + s * 0.26 * d, v + s * 0.20, u + s * 0.52 * d, v + s * 0.30,
           s * 0.07, band)
    cv.disc(u - s * 0.10, v + s * 0.18, s * 0.05, (250, 250, 245), ry=s * 0.045)
    cv.disc(u + s * 0.10, v + s * 0.18, s * 0.05, (250, 250, 245), ry=s * 0.045)
    cv.disc(u, v + s * 0.32, s * 0.09, dk, ry=s * 0.05)


def _ghost(cv, u, v, w, h, body, eye=(250, 250, 252), pup=_hx("#1a2a9e")):
    """Pac-Man's ghost: dome, straight flanks, three-scallop skirt."""
    pts = _ell(u, v + w * 0.52, w * 0.5, w * 0.52, 18, math.pi, 2 * math.pi)
    pts += [(u + w * 0.5, v + h - w * 0.16)]
    k = w / 6.0
    for j in range(3):
        cx = u + w * 0.5 - k * (2 * j + 1)
        pts += _ell(cx, v + h - w * 0.16, k, w * 0.20, 6, 0.0, math.pi)
    pts += [(u - w * 0.5, v + h - w * 0.16)]
    cv.poly(pts, body)
    for sx in (-1, 1):
        cv.disc(u + sx * w * 0.21, v + w * 0.44, w * 0.17, eye, ry=w * 0.21)
        cv.disc(u + sx * w * 0.21 + w * 0.05, v + w * 0.47, w * 0.085, pup,
                ry=w * 0.10)


def _pac(cv, u, v, r, c, ang=0.0, mouth=0.62):
    cv.disc(u, v, r, c, a0=ang + mouth * 0.5, a1=ang - mouth * 0.5)


def _panel_grid(cv, u0, v0, u1, v1, seed):
    """Marvel's comic-collage flank: irregular panels, black gutters, teal."""
    teal = [_hx("#0e3742"), _hx("#14606b"), _hx("#1d8a92"), _hx("#2fb3ad"),
            _hx("#0b2630"), _hx("#186d7e")]
    rows = [0.00, 0.185, 0.375, 0.545, 0.735, 1.0]
    cols = [[0.0, 0.46, 1.0], [0.0, 1.0], [0.0, 0.33, 0.66, 1.0],
            [0.0, 0.58, 1.0], [0.0, 0.42, 1.0]]
    g = 0.010
    k = 0
    for ri in range(5):
        ra = v0 + (v1 - v0) * rows[ri]
        rb = v0 + (v1 - v0) * rows[ri + 1]
        cc = cols[ri]
        for ci in range(len(cc) - 1):
            ca = u0 + (u1 - u0) * cc[ci]
            cb = u0 + (u1 - u0) * cc[ci + 1]
            a, b = ca + g, cb - g
            c, d = ra + g * 2, rb - g * 2
            base = teal[k % len(teal)]
            cv.rect(a, c, b, d, base)
            cv.grad(a, c, b, d, _mix(base, (255, 255, 255), 0.22),
                    _mix(base, (0, 0, 0), 0.45))
            mu, mv = (a + b) * 0.5, (c + d) * 0.5
            wd, ht = b - a, d - c
            kind = k % 6
            lite = _mix(base, (235, 255, 250), 0.72)
            dark = _mix(base, (0, 8, 12), 0.75)
            if kind == 0:                                    # action burst
                for j in range(11):
                    ang = j * 2 * math.pi / 11 + 0.2
                    cv.seg(mu, mv, mu + math.cos(ang) * wd * 0.52,
                           mv + math.sin(ang) * ht * 0.52, ht * 0.035, lite)
                cv.disc(mu, mv, wd * 0.17, dark, ry=ht * 0.17)
            elif kind == 1:                                  # halftone field
                nx, ny = 9, max(3, int(9 * ht / max(wd, 1e-6) * 0.5))
                for iy in range(ny):
                    for ix in range(nx):
                        t = ix / (nx - 1.0)
                        rr = wd * 0.040 * (0.35 + t)
                        cv.disc(a + wd * (ix + 0.5) / nx,
                                c + ht * (iy + 0.5) / ny, rr, lite,
                                ry=rr * wd / max(ht, 1e-6) * 0.0 + rr)
            elif kind == 2:                                  # hero silhouette
                cv.disc(mu, c + ht * 0.30, wd * 0.16, dark, ry=ht * 0.16)
                cv.poly([(mu - wd * 0.30, d), (mu - wd * 0.12, c + ht * 0.42),
                         (mu + wd * 0.12, c + ht * 0.42), (mu + wd * 0.30, d)],
                        dark)
                cv.seg(mu - wd * 0.12, c + ht * 0.46, mu - wd * 0.40,
                       c + ht * 0.72, ht * 0.05, dark)
                cv.seg(mu + wd * 0.12, c + ht * 0.46, mu + wd * 0.40,
                       c + ht * 0.66, ht * 0.05, dark)
            elif kind == 3:                                  # speech balloon
                cv.disc(mu, mv - ht * 0.06, wd * 0.34, lite, ry=ht * 0.26)
                cv.poly([(mu - wd * 0.10, mv + ht * 0.14),
                         (mu + wd * 0.02, mv + ht * 0.14),
                         (mu - wd * 0.14, mv + ht * 0.36)], lite)
                for j in range(3):
                    cv.rect(mu - wd * 0.22, mv - ht * 0.14 + j * ht * 0.09,
                            mu + wd * 0.20, mv - ht * 0.11 + j * ht * 0.09,
                            dark)
            elif kind == 4:                                  # bold diagonals
                for j in range(6):
                    o = j * wd * 0.30 - wd * 0.5
                    cv.poly([(a + o, d), (a + o + wd * 0.14, d),
                             (a + o + wd * 0.44, c), (a + o + wd * 0.30, c)],
                            lite if j % 2 else dark)
            else:                                            # city skyline
                x = a
                j = 0
                while x < b:
                    bw = wd * (0.10 + 0.05 * ((j * 7) % 3))
                    bh = ht * (0.30 + 0.14 * ((j * 5) % 4))
                    cv.rect(x, d - bh, min(b, x + bw), d, dark)
                    x += bw + wd * 0.02
                    j += 1
                cv.disc(mu + wd * 0.24, c + ht * 0.26, wd * 0.11, lite,
                        ry=ht * 0.11)
            k += 1


# =============================================================== the machines
# ------------------------------------------------- Marvel Super Heroes (east 1)
def _msh_marquee(cv):
    """Full-bleed painted character art on a dark ground; 'MARVEL' white
    toward the left end, the rest of the title lost in the illustration."""
    cv.grad(0, 0, cv.A, 1, _hx("#0b0e1c"), _hx("#05060d"))
    # painted nebula wash
    for (u, v, r, c, al) in ((0.55, 0.42, 0.62, _hx("#1d3f86"), 0.55),
                             (1.35, 0.66, 0.72, _hx("#25185e"), 0.45),
                             (2.35, 0.40, 0.66, _hx("#5b1f8e"), 0.55),
                             (3.05, 0.58, 0.55, _hx("#7a2bb0"), 0.45),
                             (1.95, 0.20, 0.40, _hx("#0f3a63"), 0.40)):
        for j in range(4):
            cv.disc(u, v, r * (1.0 - j * 0.20), c, a=al * 0.34,
                    ry=r * 0.75 * (1.0 - j * 0.20))
    # figures, painted-cover style: rim-lit silhouettes, no faces
    def hero(u, s, body, rim, cape=None):
        cv.poly([(u - 0.20 * s, 1.02), (u - 0.11 * s, 0.30 * s + 0.12),
                 (u + 0.11 * s, 0.30 * s + 0.12), (u + 0.22 * s, 1.02)], body)
        cv.disc(u, 0.16 + 0.06 * s, 0.10 * s, body, ry=0.11 * s)
        cv.seg(u - 0.10 * s, 0.34, u - 0.34 * s, 0.62, 0.075 * s, body)
        cv.seg(u + 0.10 * s, 0.34, u + 0.36 * s, 0.20, 0.075 * s, body)
        cv.seg(u - 0.13 * s, 0.30, u - 0.16 * s, 0.92, 0.022 * s, rim)
        cv.seg(u + 0.13 * s, 0.30, u + 0.19 * s, 0.92, 0.022 * s, rim)
        cv.seg(u - 0.08 * s, 0.11, u + 0.08 * s, 0.11, 0.020 * s, rim)
        if cape:
            cv.poly([(u - 0.14 * s, 0.26), (u - 0.62 * s, 0.72),
                     (u - 0.44 * s, 1.02), (u - 0.10 * s, 0.86)], cape)
    hero(0.34, 1.0, _hx("#7e1b24"), _hx("#e8687a"))
    hero(0.75, 0.86, _hx("#123a7a"), _hx("#5fa8ff"), _hx("#0d2450"))
    hero(2.62, 0.94, _hx("#3d1560"), _hx("#c07dff"))
    hero(3.02, 0.80, _hx("#12403a"), _hx("#57e0b0"))
    hero(2.20, 0.72, _hx("#6a3a08"), _hx("#f0a83c"))
    # the title, sitting toward the left end and half-swallowed by the art
    for j in range(7):                    # painted scrim over the figures
        cv.rect(0, 0, cv.A, 1, (6, 8, 18), a=0.055)
        cv.disc(cv.A * 0.5, 0.5, 1.9 - j * 0.12, _hx("#1b2a52"), a=0.05,
                ry=0.62 - j * 0.04)
    for j in range(9):                    # vignette
        cv.rect(0, 0, 0.10 + j * 0.05, 1, (3, 4, 10), a=0.055)
        cv.rect(cv.A - 0.10 - j * 0.05, 0, cv.A, 1, (3, 4, 10), a=0.055)
    cv.text("MARVEL", 1.42, 0.30, 0.34, (243, 244, 248), 0.055, track=0.10,
            align="c", shadow=(4, 4, 10), sh=(0.02, 0.025))
    cv.text("SUPER HEROES", 1.42, 0.70, 0.115, (196, 205, 224), 0.026,
            track=0.16, align="c")
    cv.rect(0, 0, cv.A, 0.028, _hx("#191a22"))
    cv.rect(0, 0.972, cv.A, 1, _hx("#141520"))
    cv.noise(4.5, 11)


def _msh_side(cv):
    """Comic-collage wrap, near-black ground, teal / blue-green, with the
    gold T-molding that is this machine's most distinctive edge."""
    cv.fill(_hx("#080a0e"))
    _panel_grid(cv, 0.030, 0.024, cv.A - 0.030, 0.976, 5)
    gold0, gold1 = _hx("#8e6f2c"), _hx("#f0d488")
    t = 0.020
    cv.grad(0, 0, cv.A, t, gold1, gold0)
    cv.grad(0, 1 - t, cv.A, 1, gold0, gold1)
    cv.grad(0, 0, t * 1.1, 1, gold1, gold0, horiz=True)
    cv.grad(cv.A - t * 1.1, 0, cv.A, 1, gold0, gold1, horiz=True)
    cv.noise(3.5, 23)


def _msh_front(cv):
    """The most typographic panel in the room: CAPCOM / MARVEL / SUPER
    HEROES / two blue title lines / legal type / a row of character heads."""
    cv.fill(_hx("#0b0c11"))
    cv.grad(0, 0, 1, 1, _hx("#14161d"), _hx("#07080c"))
    gold0, gold1 = _hx("#8e6f2c"), _hx("#f0d488")
    cv.grad(0, 0, 0.030, 1, gold1, gold0, horiz=True)
    cv.grad(0.970, 0, 1, 1, gold0, gold1, horiz=True)
    wht = (238, 240, 246)
    # publisher lockup: the little white block, then CAPCOM
    cv.rect(0.300, 0.112, 0.398, 0.152, wht)
    cv.text("CAPCOM", 0.435, 0.106, 0.052, wht, 0.0125, track=0.13)
    # the title
    cv.text("MARVEL", 0.545, 0.200, 0.118, wht, 0.0225, track=0.075,
            align="c")
    cv.text("SUPER HEROES", 0.545, 0.336, 0.046, wht, 0.0105, track=0.155,
            align="c")
    # two lines of blue title lettering (illegible in every photo -- drawn as
    # the blue lockup the panel shows, not as invented words)
    blu, blu2 = _hx("#3f6fd8"), _hx("#8fb4ff")
    cv.text("MARVEL", 0.560, 0.420, 0.058, blu2, 0.0135, track=0.06,
            align="c", ital=0.16, outline=_hx("#16255e"), ow=0.006)
    cv.text("SUPER HEROES", 0.548, 0.492, 0.044, blu, 0.0105, track=0.10,
            align="c", ital=0.16)
    # a line of fine legal type
    for j in range(2):
        u = 0.335
        while u < 0.760:
            w = 0.010 + 0.028 * _hash(int(u * 400), j, 3)
            cv.rect(u, 0.582 + j * 0.026, u + w, 0.590 + j * 0.026,
                    (118, 122, 134))
            u += w + 0.011
    # the row of small warm-toned character heads
    heads = ("#9d3324", "#c26a3a", "#d99a55", "#8a2f3e", "#b7532c",
             "#e0b070", "#a34a2a")
    for i, hc in enumerate(heads):
        u = 0.300 + i * 0.0645
        base = _hx(hc)
        cv.poly([(u - 0.031, 0.878), (u - 0.026, 0.806),
                 (u - 0.014, 0.792), (u + 0.014, 0.792),
                 (u + 0.026, 0.806), (u + 0.031, 0.878)],
                _mix(base, (0, 0, 0), 0.34))
        cv.disc(u, 0.772, 0.0285, base, ry=0.0300)
        cv.poly([(u - 0.030, 0.762), (u - 0.024, 0.735), (u + 0.024, 0.735),
                 (u + 0.030, 0.762)], _mix(base, (18, 12, 10), 0.55))
        cv.disc(u - 0.011, 0.770, 0.0060, (20, 16, 14), ry=0.0055)
        cv.disc(u + 0.011, 0.770, 0.0060, (20, 16, 14), ry=0.0055)
        cv.seg(u - 0.010, 0.790, u + 0.010, 0.790, 0.0050,
               _mix(base, (0, 0, 0), 0.5))
    cv.rect(0.286, 0.884, 0.762, 0.892, _mix(_hx("#8e6f2c"), (0, 0, 0), 0.2))
    cv.noise(3.2, 31)


def _msh_deck(cv):
    """Two-player deck.  NOT INVENTED: no control layout resolves in any
    photograph at any magnification, so this is the printed ground only --
    black with a teal comic wash and the machine's gold hairline."""
    cv.grad(0, 0, cv.A, 1, _hx("#20242e"), _hx("#0d1014"))
    for j in range(11):
        u = 0.10 + j * 0.235
        cv.disc(u, 0.24 + 0.42 * ((j * 5) % 3) / 2.0, 0.40,
                _hx("#1a5c69"), a=0.34, ry=0.34)
        cv.disc(u, 0.24 + 0.42 * ((j * 5) % 3) / 2.0, 0.19,
                _hx("#2b96a0"), a=0.24, ry=0.16)
    for j in range(30):
        u = 0.02 + j * 0.09
        cv.seg(u, 0.0, u - 0.11, 1.0, 0.011, _hx("#2f7f8e"), a=0.28)
    for u in (cv.A * 0.27, cv.A * 0.73):
        cv.poly([(u - 0.44, 0.16), (u + 0.44, 0.16), (u + 0.50, 0.86),
                 (u - 0.50, 0.86)], (8, 12, 16), a=0.55)
    gold = _hx("#b8923c")
    cv.rect(0, 0, cv.A, 0.022, gold)
    cv.rect(0, 0.978, cv.A, 1, gold)
    cv.noise(4.6, 47)


def _msh_riser(cv):
    """The separate printed riser strip under the front panel: 'MARVEL SUPER
    HEROES' in white over a blue/green character scene."""
    cv.grad(0, 0, cv.A, 1, _hx("#0d3a52"), _hx("#08202f"))
    for j in range(14):
        u = 0.10 + j * 0.225
        v = 0.16 + 0.52 * ((j * 3) % 4) / 3.0
        r = 0.16 + 0.10 * ((j * 7) % 3) / 2.0
        cv.disc(u, v, r, _hx("#1a7f8c"), a=0.42, ry=r * 0.8)
        cv.disc(u, v, r * 0.5, _hx("#2fc0bc"), a=0.34, ry=r * 0.4)
    for j in range(6):
        u = 0.35 + j * 0.52
        cv.poly([(u - 0.10, 1.0), (u - 0.05, 0.34), (u + 0.05, 0.34),
                 (u + 0.11, 1.0)], _hx("#0a2c3e"))
        cv.disc(u, 0.28, 0.055, _hx("#0a2c3e"), ry=0.062)
    cv.rect(0, 0.30, cv.A, 0.80, (4, 12, 20), a=0.34)
    cv.text("MARVEL", cv.A * 0.5, 0.30, 0.30, (240, 242, 248), 0.050,
            track=0.075, align="c", shadow=(3, 8, 14), sh=(0.018, 0.022))
    cv.text("SUPER HEROES", cv.A * 0.5, 0.66, 0.115, (206, 224, 236), 0.026,
            track=0.15, align="c")
    cv.rect(0, 0.94, cv.A, 1, _hx("#123f5c"))
    cv.noise(4.0, 59)


# ---------------------------------- TMNT: Turtles in Time (east 5, southmost)
def _tmnt_marquee(cv):
    """April in the yellow jumpsuit at the left against a brick alley, the
    arched logo, then the four turtles across a New York street."""
    cv.grad(0, 0, cv.A, 0.62, _hx("#8f6fb4"), _hx("#c99ec4"))
    cv.grad(0, 0.58, cv.A, 1, _hx("#6d5a52"), _hx("#3a2e28"))
    # --- left: brick alley + April
    _bricks(cv, 0.0, 0.0, 1.14, 1.0, _hx("#7c3f34"), _hx("#4a2620"),
            0.115, 0.20, 71)
    cv.rect(0.0, 0.0, 1.14, 1.0, _hx("#2a1830"), a=0.30)
    cv.rect(0.30, 0.10, 0.62, 0.72, _hx("#241a2c"))          # alley doorway
    cv.poly([(0.14, 1.0), (0.20, 0.46), (0.34, 0.46), (0.36, 1.0)],
            _hx("#e8c832"))                                   # jumpsuit
    cv.seg(0.20, 0.50, 0.09, 0.66, 0.045, _hx("#e8c832"))
    cv.seg(0.33, 0.50, 0.44, 0.62, 0.045, _hx("#e8c832"))
    cv.disc(0.262, 0.395, 0.062, _hx("#e8b48e"), ry=0.070)    # face
    cv.poly([(0.19, 0.40), (0.20, 0.28), (0.33, 0.28), (0.34, 0.42),
             (0.31, 0.30), (0.22, 0.30)], _hx("#8a3a1c"))     # hair
    cv.rect(0.16, 1.0 - 0.10, 0.38, 1.0, _hx("#2a1a14"))
    # --- right: the street, shopfronts, manhole, four turtles
    cv.rect(1.12, 0.0, cv.A, 1.0, _hx("#3b2f2a"))
    _bricks(cv, 2.86, 0.0, cv.A, 1.0, _hx("#c08a48"), _hx("#7a5228"),
            0.105, 0.19, 91)
    for j in range(5):
        u = 1.20 + j * 0.30
        cv.rect(u, 0.09, u + 0.20, 0.50, _hx("#3f3a48"))
        cv.rect(u + 0.02, 0.11, u + 0.18, 0.46, _hx("#8a7f6a"))
        cv.rect(u + 0.02, 0.11, u + 0.18, 0.27, _hx("#c2b394"))
        cv.rect(u + 0.095, 0.11, u + 0.105, 0.46, _hx("#3f3a48"))
    cv.rect(1.12, 0.52, 2.86, 0.62, _hx("#7d6a4e"))           # awning line
    for j in range(4):                                        # fire escape
        cv.rect(2.80, 0.10 + j * 0.20, 2.90, 0.125 + j * 0.20, _hx("#2a2622"))
    cv.rect(2.845, 0.05, 2.865, 0.95, _hx("#2a2622"))
    cv.rect(0.86, 0.80, cv.A, 1.0, _hx("#55504c"))            # pavement
    cv.disc(2.08, 0.925, 0.085, _hx("#3a3735"), ry=0.042)     # manhole
    cv.disc(2.08, 0.925, 0.062, _hx("#4b4744"), ry=0.030)
    _turtle_figure(cv, 1.90, 0.26, 0.40, _hx("#2f5fd0"))
    _turtle_figure(cv, 2.34, 0.20, 0.44, _hx("#8f2fd0"), flip=True)
    _turtle_figure(cv, 2.80, 0.28, 0.39, _hx("#d02f2f"))
    _turtle_figure(cv, 3.18, 0.22, 0.42, _hx("#e07a1c"), flip=True)
    # a Foot soldier silhouette between the turtles
    cv.poly([(2.585, 0.98), (2.625, 0.46), (2.715, 0.46), (2.755, 0.98)],
            _hx("#1d1b28"))
    cv.disc(2.67, 0.410, 0.048, _hx("#1d1b28"), ry=0.054)
    cv.rect(2.628, 0.392, 2.712, 0.418, _hx("#5a1420"))
    cv.seg(2.63, 0.50, 2.52, 0.60, 0.030, _hx("#1d1b28"))
    cv.seg(2.71, 0.50, 2.82, 0.58, 0.030, _hx("#1d1b28"))
    cv.seg(2.50, 0.34, 2.86, 0.66, 0.018, _hx("#6d6455"))
    # --- the logo, occupying the left third as the real marquee does
    _turtle_logo(cv, 1.02, 0.10, 0.235, cond=0.78)
    cv.rect(0, 0.972, cv.A, 1, _hx("#101418"))
    cv.noise(4.5, 101)


def _tmnt_side(cv):
    """Black flank, dim turtle/city artwork, and the bright grass-green
    T-molding that makes this machine read from across the room."""
    cv.fill(_hx("#07080a"))
    cv.grad(0.03, 0.03, cv.A - 0.03, 0.97, _hx("#0b1410"), _hx("#050807"))
    # city silhouette, low contrast
    u = 0.03
    j = 0
    while u < cv.A - 0.03:
        bw = 0.030 + 0.022 * ((j * 5) % 3)
        bh = 0.16 + 0.09 * ((j * 7) % 4)
        cv.rect(u, 0.97 - bh, min(cv.A - 0.03, u + bw), 0.97, _hx("#131d2a"))
        for k in range(int(bh / 0.035)):
            cv.rect(u + bw * 0.25, 0.99 - bh + k * 0.035,
                    u + bw * 0.55, 1.005 - bh + k * 0.035, _hx("#1d2c3e"))
        u += bw + 0.014
        j += 1
    # a big dim turtle head, the flank's one figurative element
    cu, cvv, s = cv.A * 0.5, 0.34, 0.30
    cv.disc(cu, cvv, s, _hx("#173d20"), ry=s * 1.10)
    cv.disc(cu, cvv + s * 0.12, s * 0.80, _hx("#1f5028"), ry=s * 0.88)
    cv.rect(cu - s * 1.02, cvv - s * 0.22, cu + s * 1.02, cvv + s * 0.06,
            _hx("#3a1414"))
    cv.poly([(cu + s * 0.96, cvv - s * 0.18), (cu + s * 1.9, cvv + s * 0.18),
             (cu + s * 1.75, cvv + s * 0.42), (cu + s * 0.96, cvv + s * 0.02)],
            _hx("#3a1414"))
    for sx in (-1, 1):
        cv.disc(cu + sx * s * 0.34, cvv - s * 0.06, s * 0.19, (208, 214, 200),
                ry=s * 0.17)
        cv.disc(cu + sx * s * 0.34, cvv - s * 0.06, s * 0.075, (14, 16, 12),
                ry=s * 0.07)
    cv.disc(cu, cvv + s * 0.68, s * 0.26, _hx("#0d2c15"), ry=s * 0.10)
    # T-molding
    g0, g1 = _hx("#1e7a26"), _hx("#4fd45c")
    t = 0.026
    cv.grad(0, 0, cv.A, t, g1, g0)
    cv.grad(0, 1 - t, cv.A, 1, g0, g1)
    cv.grad(0, 0, t * 1.15, 1, g1, g0, horiz=True)
    cv.grad(cv.A - t * 1.15, 0, cv.A, 1, g0, g1, horiz=True)
    cv.noise(3.6, 113)


def _tmnt_front(cv):
    """Black, the arched TURTLES logo, 'TURTLES IN TIME' in a pale slab, a
    short red line, and green T-molding down both vertical edges."""
    cv.fill(_hx("#08090b"))
    cv.grad(0, 0, 1, 1, _hx("#101317"), _hx("#050607"))
    for j in range(9):                       # ghost of the sewer-tunnel print
        cv.disc(0.5, 0.62, 0.40 - j * 0.035, _hx("#132a1c"), a=0.10, ry=0.30)
    _turtle_logo(cv, 0.50, 0.068, 0.132, cond=0.74)
    cv.text("TURTLES IN TIME", 0.50, 0.425, 0.088, _hx("#8fb8ee"), 0.0180,
            track=0.075, cond=0.82, arch=0.045, align="c",
            outline=_hx("#1a2f78"), ow=0.0075,
            shadow=(6, 8, 14), sh=(0.008, 0.009))
    cv.text("KONAMI", 0.50, 0.612, 0.044, _hx("#c22a2a"), 0.0105, track=0.20,
            align="c")
    g0, g1 = _hx("#1e7a26"), _hx("#4fd45c")
    cv.grad(0, 0, 0.036, 1, g1, g0, horiz=True)
    cv.grad(0.964, 0, 1, 1, g0, g1, horiz=True)
    cv.noise(3.2, 127)


def _tmnt_deck(cv):
    """Four-player deck: a brown/red brick New York street with the TURTLES
    wordmark repeated across it and character-portrait decals."""
    _bricks(cv, 0, 0, cv.A, 1, _hx("#8a4a34"), _hx("#4e2820"), 0.135, 0.145,
            151)
    cv.grad(0, 0, cv.A, 1, _hx("#40201a"), _hx("#0e0a0a"), a=0.30)
    # fire escapes / grates
    for u in (0.30, 1.26, 2.30):
        cv.rect(u - 0.115, 0.055, u - 0.098, 0.70, _hx("#241c18"))
        cv.rect(u + 0.098, 0.055, u + 0.115, 0.70, _hx("#241c18"))
        for j in range(7):
            cv.rect(u - 0.115, 0.075 + j * 0.092, u + 0.115,
                    0.090 + j * 0.092, _hx("#2c231d"))
    cv.disc(1.80, 0.575, 0.145, _hx("#22201e"), ry=0.190)    # manhole
    cv.disc(1.80, 0.575, 0.125, _hx("#5a5450"), ry=0.163)
    cv.disc(1.80, 0.575, 0.108, _hx("#403b38"), ry=0.141)
    for j in range(5):
        cv.disc(1.80, 0.575, 0.096 - j * 0.020, _hx("#5a5450"), a=0.45,
                ry=0.125 - j * 0.026)
    # the wordmark, three times, at three sizes and colours
    for (u, v, h, c, o) in ((0.60, 0.13, 0.145, _hx("#5fbf2b"), _hx("#f5c119")),
                            (1.46, 0.09, 0.095, _hx("#3f8fe0"), _hx("#dbe8f6")),
                            (2.08, 0.30, 0.170, _hx("#f0c81e"), _hx("#8a4a12"))):
        cv.text("TURTLES", u, v, h, c, h * 0.19, track=0.02, cond=0.80,
                arch=h * 0.13, align="c", outline=o, ow=h * 0.070,
                shadow=(10, 10, 8), sh=(h * 0.085, h * 0.085))
    # character-portrait decals
    for i, bc in enumerate(("#2f5fd0", "#d02f2f", "#8f2fd0", "#e07a1c")):
        u = 0.42 + i * 0.62
        cv.rect(u - 0.075, 0.735, u + 0.075, 0.945, _hx("#efe6d2"))
        cv.rect(u - 0.062, 0.752, u + 0.062, 0.928, _hx("#2b4a20"))
        cv.disc(u, 0.845, 0.050, _hx("#5ea832"), ry=0.062)
        cv.rect(u - 0.052, 0.818, u + 0.052, 0.845, _hx(bc))
        cv.disc(u - 0.019, 0.832, 0.011, (245, 245, 238), ry=0.013)
        cv.disc(u + 0.019, 0.832, 0.011, (245, 245, 238), ry=0.013)
    g0, g1 = _hx("#1e7a26"), _hx("#4fd45c")
    t = 0.030
    cv.grad(0, 0, cv.A, t, g1, g0)
    cv.grad(0, 1 - t, cv.A, 1, g0, g1)
    cv.grad(0, 0, t * 0.42, 1, g1, g0, horiz=True)
    cv.grad(cv.A - t * 0.42, 0, cv.A, 1, g0, g1, horiz=True)
    cv.noise(5.0, 163)


def _tmnt_riser(cv):
    """The riser under the front panel: one turtle illustration in green and
    grey, brick behind it -- figure-led, unlike the brick-led deck."""
    _bricks(cv, 0, 0, cv.A, 1, _hx("#6b3a2c"), _hx("#3c2018"), 0.16, 0.17, 181)
    cv.rect(0, 0, cv.A, 1, _hx("#120c0c"), a=0.42)
    cv.grad(0, 0, cv.A, 1, _hx("#3a4a44"), _hx("#12181a"), a=0.30)
    cu = cv.A * 0.40
    # a turtle bust: shell rim, shoulders, plastron, head, bandana, nunchuck
    cv.disc(cu, 0.86, 0.62, _hx("#6b4a18"), ry=0.44)
    cv.disc(cu, 0.88, 0.52, _hx("#8a6222"), ry=0.36)
    cv.poly([(cu - 0.52, 1.0), (cu - 0.34, 0.58), (cu + 0.34, 0.58),
             (cu + 0.52, 1.0)], _hx("#3f8a2a"))
    cv.poly([(cu - 0.28, 1.0), (cu - 0.19, 0.63), (cu + 0.19, 0.63),
             (cu + 0.28, 1.0)], _hx("#c3ad6a"))
    for j in range(3):
        cv.rect(cu - 0.24 + j * 0.005, 0.72 + j * 0.09,
                cu + 0.24 - j * 0.005, 0.735 + j * 0.09, _hx("#8d7a44"))
    cv.seg(cu - 0.36, 0.66, cu - 0.86, 0.86, 0.085, _hx("#4f9a2c"))
    cv.seg(cu + 0.36, 0.66, cu + 0.80, 0.50, 0.085, _hx("#4f9a2c"))
    cv.disc(cu, 0.40, 0.185, _hx("#5ea832"), ry=0.205)
    cv.rect(cu - 0.20, 0.345, cu + 0.20, 0.435, _hx("#c22a2a"))
    cv.poly([(cu + 0.18, 0.355), (cu + 0.62, 0.285), (cu + 0.66, 0.375),
             (cu + 0.19, 0.435)], _hx("#c22a2a"))
    for sx in (-1, 1):
        cv.disc(cu + sx * 0.072, 0.390, 0.040, (244, 244, 236), ry=0.040)
        cv.disc(cu + sx * 0.072, 0.390, 0.016, (14, 16, 12), ry=0.016)
    cv.disc(cu, 0.505, 0.062, _hx("#2f6b1c"), ry=0.030)
    cv.seg(cu - 0.92, 0.42, cu - 0.86, 0.84, 0.045, _hx("#3a2a16"))
    cv.seg(cu - 0.92, 0.42, cu - 1.14, 0.66, 0.045, _hx("#3a2a16"))
    cv.text("TURTLES", cv.A - 0.62, 0.32, 0.165, _hx("#5fbf2b"), 0.031,
            track=0.02, cond=0.80, arch=0.021, align="c",
            outline=_hx("#f5c119"), ow=0.012, shadow=(10, 10, 8),
            sh=(0.014, 0.013))
    cv.noise(4.2, 191)


# ------------------------------------------------------- Time Crisis (south 2)
def _tc_marquee(cv):
    """Pale gold ground; 'TIME' small on the upper line with a swash,
    'CRISIS' large across the full width, both raked right in blue block
    italic with a heavy white outline and a drop shadow."""
    cv.grad(0, 0, cv.A, 1, _hx("#e0d09a"), _hx("#a8914c"))
    for j in range(9):                       # a soft painted glow behind
        cv.disc(cv.A * 0.5, 0.55, 1.55 - j * 0.14, _hx("#efe4bc"), a=0.10,
                ry=0.52 - j * 0.05)
    cv.rect(0, 0, cv.A, 0.035, _hx("#8a7436"))
    cv.rect(0, 0.965, cv.A, 1, _hx("#6d5a26"))
    blu, wht, shd = _hx("#28368f"), (247, 248, 250), (58, 44, 26)
    cv.text("TIME", 1.02, 0.075, 0.34, blu, 0.062, track=0.04, ital=0.30,
            align="c", outline=wht, ow=0.030, shadow=shd, sh=(0.045, 0.050))
    # the swash off the end of TIME, clear of the word
    for (w, c) in ((0.050, shd), (0.038, wht), (0.022, blu)):
        cv.seg(1.50, 0.215, 1.72, 0.130, w, c)
        cv.seg(1.72, 0.130, 1.81, 0.168, w * 0.60, c)
    cv.text("CRISIS", cv.A * 0.5, 0.455, 0.46, blu, 0.082, track=0.045,
            ital=0.30, align="c", outline=wht, ow=0.038,
            shadow=shd, sh=(0.055, 0.060))
    cv.noise(4.0, 211)


def _tc_speaker(cv):
    """The head below the marquee: a deep maroon band over a tan-gold panel
    pierced by two round black speaker holes set wide apart."""
    cv.grad(0, 0, cv.A, 0.34, _hx("#6a2530"), _hx("#42161f"))
    for j in range(20):                       # a horizontal sheen
        v = 0.02 + j * 0.015
        cv.rect(0, v, cv.A, v + 0.006, _hx("#93404a"), a=0.16)
    cv.rect(0, 0.335, cv.A, 0.355, _hx("#2a1014"))
    cv.grad(0, 0.355, cv.A, 1, _hx("#b09a52"), _hx("#7d6a34"))
    for (u) in (cv.A * 0.22, cv.A * 0.78):
        cv.disc(u, 0.70, 0.155, _hx("#4a3f1e"), ry=0.20)
        cv.disc(u, 0.695, 0.135, _hx("#0a0a0c"), ry=0.175)
        cv.disc(u, 0.660, 0.115, _hx("#17171a"), ry=0.135)
    cv.rect(0, 0.982, cv.A, 1, _hx("#5c4c22"))
    cv.noise(3.8, 223)


def _tc_side(cv):
    """Red/maroon flank with tan-gold trim along the front edge and the pale
    head shroud across the top.  DECLARED: no figurative art resolves on this
    machine's flanks at any magnification I could get, so none is invented."""
    cv.grad(0, 0, cv.A, 1, _hx("#8e3a36"), _hx("#5a2422"))
    cv.grad(0, 0, cv.A, 0.185, _hx("#cbb478"), _hx("#a58d4a"))   # head shroud
    cv.rect(0, 0.185, cv.A, 0.200, _hx("#4c1d1e"))
    cv.grad(0, 0.200, cv.A, 0.285, _hx("#6a2530"), _hx("#8e3a36"))
    for j in range(30):                       # vinyl sheen, back to front
        u = j * (cv.A / 30.0)
        cv.rect(u, 0.20, u + cv.A / 60.0, 1.0, _hx("#a04a44"), a=0.10)
    cv.grad(0, 0.28, 0.040, 1, _hx("#e3cc8e"), _hx("#8f7a38"), horiz=True)
    cv.rect(cv.A - 0.030, 0.20, cv.A, 1, _hx("#3f1718"))
    cv.rect(0, 0.985, cv.A, 1, _hx("#241012"))
    cv.noise(4.4, 233)


def _tc_front(cv):
    """Black lower panel: two red pillars, a black coin-door recess between
    them, the small white-and-blue italic lockup at about 60% height, and a
    pale coin plate at bottom centre."""
    cv.fill(_hx("#0c0c0e"))
    cv.grad(0, 0, 1, 1, _hx("#141417"), _hx("#08080a"))
    cv.grad(0, 0, 0.165, 1, _hx("#9a3b34"), _hx("#5e2320"), horiz=True)
    cv.grad(0.835, 0, 1, 1, _hx("#5e2320"), _hx("#9a3b34"), horiz=True)
    cv.rect(0.165, 0, 0.180, 1, _hx("#c9a860"))
    cv.rect(0.820, 0, 0.835, 1, _hx("#c9a860"))
    # coin-door recess
    cv.rect(0.300, 0.615, 0.700, 0.925, _hx("#050506"))
    cv.rect(0.300, 0.615, 0.700, 0.632, _hx("#33343a"))
    cv.rect(0.318, 0.638, 0.682, 0.905, _hx("#16171b"))
    for u in (0.400, 0.600):
        cv.rect(u - 0.020, 0.660, u + 0.020, 0.742, _hx("#3d4048"))
        cv.rect(u - 0.007, 0.668, u + 0.007, 0.734, _hx("#0a0a0c"))
    cv.rect(0.430, 0.790, 0.570, 0.858, _hx("#2b2d33"))
    # the small lockup
    blu, wht = _hx("#3a52c8"), (238, 240, 246)
    cv.text("TIME", 0.330, 0.352, 0.098, blu, 0.020, track=0.04, ital=0.30,
            align="c", outline=wht, ow=0.0095)
    cv.text("CRISIS", 0.405, 0.452, 0.126, blu, 0.024, track=0.045, ital=0.30,
            align="c", outline=wht, ow=0.011)
    cv.text("NAMCO", 0.500, 0.560, 0.036, (150, 154, 166), 0.0085, track=0.22,
            align="c")
    # pale coin plate
    cv.rect(0.428, 0.930, 0.572, 0.982, _hx("#b9bcc2"))
    cv.rect(0.440, 0.940, 0.560, 0.972, _hx("#8d9096"))
    cv.noise(3.4, 241)


def _tc_deck(cv):
    """Red/orange deck: two pale blue-and-white printed instruction placards
    either side of the darker gun cradle, gold trim at the front edge."""
    cv.grad(0, 0, cv.A, 1, _hx("#c9552e"), _hx("#8e3418"))
    for j in range(24):
        u = j * (cv.A / 24.0)
        cv.rect(u, 0, u + cv.A / 48.0, 1, _hx("#dd6b3a"), a=0.13)
    # the gun cradle, left of centre
    cv.poly([(0.98, 0.30), (1.62, 0.26), (1.68, 0.80), (1.02, 0.84)],
            _hx("#7b2c18"))
    cv.poly([(1.04, 0.35), (1.56, 0.315), (1.60, 0.75), (1.08, 0.78)],
            _hx("#5d1f11"))
    # instruction placards
    for u0 in (0.16, 1.78):
        cv.rect(u0, 0.235, u0 + 0.70, 0.765, _hx("#f0f4f8"))
        cv.rect(u0 + 0.018, 0.258, u0 + 0.682, 0.742, _hx("#cfe0f0"))
        cv.rect(u0 + 0.018, 0.258, u0 + 0.682, 0.320, _hx("#2a4f9e"))
        for j in range(5):
            w = 0.30 + 0.30 * _hash(j, int(u0 * 10), 7)
            cv.rect(u0 + 0.050, 0.365 + j * 0.072,
                    u0 + 0.050 + w, 0.398 + j * 0.072, _hx("#28468c"))
        cv.rect(u0 + 0.520, 0.560, u0 + 0.650, 0.700, _hx("#3f6fd0"))
        cv.rect(u0 + 0.548, 0.588, u0 + 0.622, 0.672, _hx("#e6eef8"))
    cv.grad(0, 0, cv.A, 0.030, _hx("#e3cc8e"), _hx("#9c8440"))
    cv.grad(0, 0.970, cv.A, 1, _hx("#9c8440"), _hx("#e3cc8e"))
    cv.noise(4.6, 251)


# ----------------------------------------------------------- Pac-Man (north 1)
def _pac_marquee(cv):
    """White ground in a thin dark frame inside a maroon band; PAC | MAN in
    fat rounded yellow bubble caps, arched, with the chase art between."""
    mar, cream = _hx("#7a2028"), _hx("#f5f1e4")
    cv.fill(mar)
    cv.grad(0, 0, cv.A, 0.5, _hx("#8d2a32"), _hx("#651a22"))
    cv.grad(0, 0.5, cv.A, 1, _hx("#651a22"), _hx("#4d1219"))
    cv.rect(0.155, 0.115, cv.A - 0.155, 0.885, _hx("#20161a"))
    cv.rect(0.185, 0.145, cv.A - 0.185, 0.855, cream)
    cv.grad(0.185, 0.145, cv.A - 0.185, 0.855, (255, 253, 246),
            (226, 220, 202))
    ylw, blk = _hx("#f8d21a"), (12, 10, 8)
    cv.text("PAC", 0.94, 0.250, 0.375, ylw, 0.128, track=0.10, arch=0.048,
            align="c", outline=blk, ow=0.034)
    cv.text("MAN", 2.46, 0.250, 0.375, ylw, 0.128, track=0.10, arch=0.048,
            align="c", outline=blk, ow=0.034)
    cv.seg(1.585, 0.335, 1.795, 0.335, 0.098, blk)
    cv.seg(1.60, 0.335, 1.78, 0.335, 0.064, ylw)
    # chase art: a blue ghost, then Pac-Man and a dot trail
    _ghost(cv, 1.58, 0.470, 0.250, 0.315, _hx("#2438cf"))
    _pac(cv, 2.02, 0.690, 0.125, ylw, ang=0.0, mouth=0.85)
    for j in range(4):
        cv.disc(2.24 + j * 0.120, 0.690, 0.023, _hx("#c9922a"))
    cv.noise(3.4, 263)


def _pac_side(cv):
    """Plain yellow flank with maroon T-molding on every exposed edge.
    DECLARED: no large graphic appears on the sides in any view -- the real
    upright's flanks are painted yellow, so nothing is invented here."""
    cv.grad(0, 0, cv.A, 1, _hx("#f4cb12"), _hx("#d3ab08"))
    for j in range(26):                       # faint vinyl sheen
        u = j * (cv.A / 26.0)
        cv.rect(u, 0, u + cv.A / 52.0, 1, _hx("#ffe04a"), a=0.11)
    cv.grad(0, 0.68, cv.A, 1, _hx("#c99f06"), _hx("#a88104"), a=0.45)
    m0, m1 = _hx("#5a161c"), _hx("#9c2f38")
    t = 0.024
    cv.grad(0, 0, cv.A, t, m1, m0)
    cv.grad(0, 1 - t, cv.A, 1, m0, m1)
    cv.grad(0, 0, t * 1.15, 1, m1, m0, horiz=True)
    cv.grad(cv.A - t * 1.15, 0, cv.A, 1, m0, m1, horiz=True)
    cv.noise(3.0, 271)


def _pac_front(cv):
    """Yellow full height: the black coin-door plate, the ghost, Pac-Man and
    the blue maze elbows across the bottom."""
    cv.grad(0, 0, 1, 1, _hx("#f6ce16"), _hx("#dcb20a"))
    cv.grad(0, 0, 0.030, 1, _hx("#9c2f38"), _hx("#5a161c"), horiz=True)
    cv.grad(0.970, 0, 1, 1, _hx("#5a161c"), _hx("#9c2f38"), horiz=True)
    # the tall black coin-door plate
    cv.rect(0.302, 0.140, 0.618, 0.556, _hx("#0e0e0b"))
    cv.rect(0.318, 0.156, 0.602, 0.540, _hx("#1a1a15"))
    for v in (0.198, 0.330):
        cv.rect(0.350, v, 0.402, v + 0.070, _hx("#40403a"))
        cv.rect(0.362, v + 0.010, 0.390, v + 0.060, _hx("#080806"))
        cv.rect(0.518, v, 0.570, v + 0.070, _hx("#40403a"))
        cv.rect(0.530, v + 0.010, 0.558, v + 0.060, _hx("#080806"))
    cv.rect(0.386, 0.452, 0.534, 0.520, _hx("#9aa0a4"))       # coin return
    cv.rect(0.398, 0.464, 0.522, 0.508, _hx("#61666a"))
    cv.text("PAC-MAN", 0.460, 0.086, 0.040, _hx("#3a2c06"), 0.0095,
            track=0.16, align="c")
    # the ghost and Pac-Man
    _ghost(cv, 0.400, 0.585, 0.185, 0.230, _hx("#2438cf"),
           pup=_hx("#c22a5e"))
    cv.seg(0.330, 0.775, 0.470, 0.775, 0.020, _hx("#e0698c"))  # mouth line
    _pac(cv, 0.560, 0.845, 0.088, _hx("#f8d21a"), ang=3.55, mouth=0.9)
    # the maze elbows across the very bottom
    blu = _hx("#2438cf")
    for (u0, u1) in ((0.075, 0.300), (0.660, 0.905)):
        cv.rect(u0, 0.905, u1, 0.960, blu)
        cv.rect(u0, 0.905, u0 + 0.055, 1.0, blu)
        cv.rect(u1 - 0.055, 0.905, u1, 1.0, blu)
        cv.rect(u0 + 0.020, 0.925, u1 - 0.020, 0.940, _hx("#0b1240"))
    cv.rect(0.400, 0.955, 0.600, 0.985, blu)
    cv.rect(0.430, 0.966, 0.570, 0.976, _hx("#0b1240"))
    cv.noise(3.4, 283)


def _pac_deck(cv):
    """Black deck with a maroon lip along its front edge.  DECLARED: the
    joystick and buttons are geometry, and the printed deck itself is plain
    black in every frame -- so this is the ground and the lip, nothing more."""
    cv.grad(0, 0, cv.A, 1, _hx("#1a1a18"), _hx("#0b0b0a"))
    for j in range(40):
        u = j * (cv.A / 40.0)
        cv.rect(u, 0, u + cv.A / 80.0, 1, _hx("#26261f"), a=0.16)
    cv.rect(0, 0, cv.A, 0.030, _hx("#3a3a32"))
    cv.grad(0, 0.855, cv.A, 0.885, _hx("#f0c81e"), _hx("#a88a10"))
    cv.grad(0, 0.885, cv.A, 1, _hx("#8d2a32"), _hx("#4d1219"))
    cv.noise(3.2, 293)


# ================================================================== the table
ASPECT = {
    "marvel-super-heroes.marquee": 3.40,
    "marvel-super-heroes.side": 0.43,
    "marvel-super-heroes.front": 1.00,
    "marvel-super-heroes.deck": 2.60,
    "marvel-super-heroes.riser": 3.20,
    "tmnt-turtles-in-time.marquee": 3.40,
    "tmnt-turtles-in-time.side": 0.43,
    "tmnt-turtles-in-time.front": 1.00,
    "tmnt-turtles-in-time.deck": 2.60,
    "tmnt-turtles-in-time.riser": 3.20,
    "time-crisis.marquee": 3.40,
    "time-crisis.speaker": 2.20,
    "time-crisis.side": 0.43,
    "time-crisis.front": 1.00,
    "time-crisis.deck": 2.60,
    "pac-man.marquee": 3.40,
    "pac-man.side": 0.43,
    "pac-man.front": 1.00,
    "pac-man.deck": 2.60,
}

# Which a2kit material each panel expects.  These are true printed albedos.
MATERIAL_HINT = {
    "marvel-super-heroes.marquee": "MQ (emissive, dim -- this marquee reads "
                                   "unlit in every photo)",
    "marvel-super-heroes.side": "ART",
    "marvel-super-heroes.front": "ART",
    "marvel-super-heroes.deck": "ART_D",
    "marvel-super-heroes.riser": "ART",
    "tmnt-turtles-in-time.marquee": "MQ (emissive)",
    "tmnt-turtles-in-time.side": "ART",
    "tmnt-turtles-in-time.front": "ART",
    "tmnt-turtles-in-time.deck": "ART_D  -- NOT ART_DK, it crushes the brick",
    "tmnt-turtles-in-time.riser": "ART",
    "time-crisis.marquee": "MQ (emissive)",
    "time-crisis.speaker": "ART",
    "time-crisis.side": "ART",
    "time-crisis.front": "ART",
    "time-crisis.deck": "ART_D",
    "pac-man.marquee": "MQ (emissive -- one of only two lit marquees on the "
                       "north wall)",
    "pac-man.side": "ART",
    "pac-man.front": "ART",
    "pac-man.deck": "ART_DK (this deck really is black)",
}

_FN = {
    "marvel-super-heroes.marquee": _msh_marquee,
    "marvel-super-heroes.side": _msh_side,
    "marvel-super-heroes.front": _msh_front,
    "marvel-super-heroes.deck": _msh_deck,
    "marvel-super-heroes.riser": _msh_riser,
    "tmnt-turtles-in-time.marquee": _tmnt_marquee,
    "tmnt-turtles-in-time.side": _tmnt_side,
    "tmnt-turtles-in-time.front": _tmnt_front,
    "tmnt-turtles-in-time.deck": _tmnt_deck,
    "tmnt-turtles-in-time.riser": _tmnt_riser,
    "time-crisis.marquee": _tc_marquee,
    "time-crisis.speaker": _tc_speaker,
    "time-crisis.side": _tc_side,
    "time-crisis.front": _tc_front,
    "time-crisis.deck": _tc_deck,
    "pac-man.marquee": _pac_marquee,
    "pac-man.side": _pac_side,
    "pac-man.front": _pac_front,
    "pac-man.deck": _pac_deck,
}


def _mk(key):
    fn = _FN[key]
    A = ASPECT[key]

    def paint(px, ox, oy, tile):
        cv = Cv(tile, A)
        fn(cv)
        cv.blit(px, ox, oy, tile)

    paint.__name__ = "paint_" + key.replace("-", "_").replace(".", "_")
    paint.aspect = A
    return paint


PANELS = dict((k, _mk(k)) for k in _FN)
