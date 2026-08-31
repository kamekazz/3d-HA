
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

    def __init__(self, tile, A, hpx=None):
        # `tile` is the WIDTH in pixels and `hpx` the height; when hpx is None
        # the surface is the square atlas tile round 4 used.  A non-square
        # surface with hpx = tile / A is ISOTROPIC -- one frame unit is the
        # same number of pixels across and down -- which is how a 3.5:1
        # marquee stops spending 120 rows on a band that only needs 34.
        self.n = tile
        self.m = tile if hpx is None else int(hpx)
        self.A = float(A)
        self.b = [[[0.0, 0.0, 0.0] for _ in range(self.n)]
                  for _ in range(self.m)]
        self.aa = 0.6 / self.m        # half a pixel, in v units

    # ---- coordinate helpers
    def px(self, u):
        return u / self.A * self.n

    def py(self, v):
        return v * self.m

    def _bbox(self, u0, v0, u1, v1, pad=0.0):
        x0 = int(math.floor(self.px(min(u0, u1) - pad)))
        x1 = int(math.ceil(self.px(max(u0, u1) + pad)))
        y0 = int(math.floor(self.py(min(v0, v1) - pad)))
        y1 = int(math.ceil(self.py(max(v0, v1) + pad)))
        return (max(0, x0), max(0, y0), min(self.n, x1 + 1),
                min(self.m, y1 + 1))

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
        y1 = min(self.m, int(math.ceil(max(ys))) + 1)
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
            dv = (y + 0.5) / self.m - v
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
            pv = (y + 0.5) / self.m
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
    def blit(self, px, ox, oy, tile=None):
        for y in range(self.m):
            row = self.b[y]
            orow = px[oy + y]
            by = _BAYER[y & 3]
            for x in range(self.n):
                n = (by[x & 3] - 7.5) * 0.90
                p = row[x]
                orow[ox + x] = (
                    _clamp8(round((p[0] + n) / 8.0) * 8),
                    _clamp8(round((p[1] + n) / 8.0) * 8),
                    _clamp8(round((p[2] + n) / 8.0) * 8))

