"""Printed artwork for four Arcade Room machines -- round 4, agent g3.

Machines: Mortal Kombat (EAST_RUN 3), Legends Ultimate (SOUTH_RUN 0),
Ridge Racer (CORNER 0) and Golden Tee 3D Golf (NORTH_RUN 3).

Round 3's atlas painted one motif sixteen times with the hue swapped and stood
blocky rectangles in for marquee lettering.  Everything here is drawn as the
machine's own graphic, and every title is set in a real stroke font
(`_FONT` below) so "LEGENDS ULTIMATE" reads as those words.

TWO THINGS THE INTEGRATOR MUST KNOW
-----------------------------------
1. ASPECT.  A square atlas tile is stretched onto a rectangular quad, so a
   circle drawn as a circle in the tile comes out as an ellipse in the room.
   Every panel below declares the world aspect (W/H) of the quad it is meant
   for in `PANEL_AR`, and every round / stroked / typeset element is drawn
   through an `ar`-aware helper so it lands correctly proportioned AFTER the
   stretch.  The values are computed from `ar2.py`'s own geometry for these
   four table rows.  If a machine's `bw` / `top` / `dy` / `mqh` changes, update
   `PANEL_AR` or the lettering will squash.
2. ar2.py currently feeds the SAME tile (`art_f`) to the lower front panel,
   the control deck and the screen bezel, and mirrors u on the deck.  Those are
   three different printed surfaces on a real cabinet and they are three
   different panels here (`.front`, `.deck`, `.bezel`).  Wire them separately.

Conventions: tile (0,0) is the TOP-LEFT of the panel, matching `uvr`/`uvq` in
a2kit (v0 is the tile's top row and `sweep`/`uvq` both put the panel's top edge
there).  Colours are authored bright where the surrounding material darkens
them -- ar2 multiplies the deck by #4c4c4c and the bezel by #3c3c3c -- and flat
where the machine really is black.  The 4x4 ordered dither and round-to-8
quantisation are copied from a2kit so the PNG stays small.
"""

import math

TILE = 256                       # tile edge in px, matches a2kit

# world aspect (quad width / quad height) of every panel, from ar2.py geometry
PANEL_AR = {
    "mortal-kombat.marquee": 3.52,
    "mortal-kombat.side": 0.42,
    "mortal-kombat.front": 1.28,
    "mortal-kombat.deck": 2.22,
    "mortal-kombat.bezel": 0.88,
    "legends-ultimate.marquee": 3.54,
    "legends-ultimate.side": 0.40,
    "legends-ultimate.front": 1.52,
    "legends-ultimate.deck": 3.08,
    "legends-ultimate.bezel": 1.21,
    "ridge-racer.marquee": 3.48,
    "ridge-racer.side": 0.42,
    "ridge-racer.front": 1.26,
    "ridge-racer.deck": 2.50,
    "ridge-racer.bezel": 1.04,
    "golden-tee-3d-golf.marquee": 3.24,
    "golden-tee-3d-golf.side": 0.40,
    "golden-tee-3d-golf.front": 1.27,
    "golden-tee-3d-golf.deck": 2.39,
    "golden-tee-3d-golf.bezel": 0.90,
}


# --------------------------------------------------------------- raster base
_BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def _c8(v):
    return 0 if v < 0 else (255 if v > 255 else int(v))


def _hx(c):
    c = c.lstrip("#")
    return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16))


def _new(t, col):
    r, g, b = col
    return [[[float(r), float(g), float(b)] for _ in range(t)]
            for _ in range(t)]


def _flush(px, ox, oy, buf, t):
    """Blit `buf` into the atlas with a2kit's 4x4 ordered dither."""
    for y in range(t):
        row = buf[y]
        brow = _BAYER[y & 3]
        orow = px[oy + y]
        for x in range(t):
            n = (brow[x & 3] - 7.5) * 0.90
            c = row[x]
            orow[ox + x] = (_c8(round((c[0] + n) / 8.0) * 8),
                            _c8(round((c[1] + n) / 8.0) * 8),
                            _c8(round((c[2] + n) / 8.0) * 8))


def _mix(a, b, k):
    return (a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k,
            a[2] + (b[2] - a[2]) * k)


def _put(buf, x, y, col, a):
    if a <= 0.0:
        return
    if a > 1.0:
        a = 1.0
    p = buf[y][x]
    p[0] += (col[0] - p[0]) * a
    p[1] += (col[1] - p[1]) * a
    p[2] += (col[2] - p[2]) * a


def _rect(buf, t, x0, y0, x1, y1, col, a=1.0):
    """Axis-aligned rect in normalised tile coords, fractional edge coverage."""
    if x1 < x0:
        x0, x1 = x1, x0
    if y1 < y0:
        y0, y1 = y1, y0
    px0, px1 = x0 * t, x1 * t
    py0, py1 = y0 * t, y1 * t
    ix0, ix1 = max(0, int(math.floor(px0))), min(t - 1, int(math.ceil(px1)) - 1)
    iy0, iy1 = max(0, int(math.floor(py0))), min(t - 1, int(math.ceil(py1)) - 1)
    for y in range(iy0, iy1 + 1):
        cy = min(y + 1.0, py1) - max(float(y), py0)
        if cy <= 0.0:
            continue
        for x in range(ix0, ix1 + 1):
            cx = min(x + 1.0, px1) - max(float(x), px0)
            if cx > 0.0:
                _put(buf, x, y, col, a * cx * cy)


def _vgrad(buf, t, y0, y1, c0, c1, x0=0.0, x1=1.0, a=1.0):
    iy0 = max(0, int(y0 * t))
    iy1 = min(t, int(math.ceil(y1 * t)))
    ix0, ix1 = max(0, int(x0 * t)), min(t, int(math.ceil(x1 * t)))
    span = max(1e-6, (y1 - y0) * t)
    for y in range(iy0, iy1):
        k = min(1.0, max(0.0, (y + 0.5 - y0 * t) / span))
        c = _mix(c0, c1, k)
        for x in range(ix0, ix1):
            _put(buf, x, y, c, a)


def _hgrad(buf, t, x0, x1, c0, c1, y0=0.0, y1=1.0, a=1.0):
    ix0 = max(0, int(x0 * t))
    ix1 = min(t, int(math.ceil(x1 * t)))
    iy0, iy1 = max(0, int(y0 * t)), min(t, int(math.ceil(y1 * t)))
    span = max(1e-6, (x1 - x0) * t)
    for x in range(ix0, ix1):
        k = min(1.0, max(0.0, (x + 0.5 - x0 * t) / span))
        c = _mix(c0, c1, k)
        for y in range(iy0, iy1):
            _put(buf, x, y, c, a)


def _seg(buf, t, p0, p1, w, col, ar=1.0, a=1.0):
    """A stroked segment.  `w` is the stroke width measured in tile-Y units;
    x distances are scaled by `ar` so the stroke stays uniform after the
    tile is stretched onto its quad."""
    x0, y0 = p0
    x1, y1 = p1
    hw = w * 0.5
    mx = hw / ar + 1.5 / t
    my = hw + 1.5 / t
    ix0 = max(0, int((min(x0, x1) - mx) * t))
    ix1 = min(t - 1, int(math.ceil((max(x0, x1) + mx) * t)))
    iy0 = max(0, int((min(y0, y1) - my) * t))
    iy1 = min(t - 1, int(math.ceil((max(y0, y1) + my) * t)))
    ax0, ay0 = x0 * ar, y0
    dx, dy = (x1 - x0) * ar, y1 - y0
    dd = dx * dx + dy * dy
    soft = 1.0 / t
    for y in range(iy0, iy1 + 1):
        py = (y + 0.5) / t
        for x in range(ix0, ix1 + 1):
            pxx = (x + 0.5) / t * ar
            if dd < 1e-12:
                d = math.hypot(pxx - ax0, py - ay0)
            else:
                u = ((pxx - ax0) * dx + (py - ay0) * dy) / dd
                u = 0.0 if u < 0.0 else (1.0 if u > 1.0 else u)
                d = math.hypot(pxx - ax0 - dx * u, py - ay0 - dy * u)
            cov = (hw + soft - d) / soft
            if cov > 0.0:
                _put(buf, x, y, col, a * (1.0 if cov > 1.0 else cov))


def _poly_line(buf, t, pts, w, col, ar=1.0, a=1.0, close=False):
    n = len(pts)
    for i in range(n - 1):
        _seg(buf, t, pts[i], pts[i + 1], w, col, ar, a)
    if close and n > 2:
        _seg(buf, t, pts[-1], pts[0], w, col, ar, a)


def _ellipse(buf, t, cx, cy, r, col, ar=1.0, a=1.0, r_in=0.0):
    """Disc (or annulus) of world-radius `r` measured in tile-Y units."""
    mx = r / ar + 1.5 / t
    ix0 = max(0, int((cx - mx) * t))
    ix1 = min(t - 1, int(math.ceil((cx + mx) * t)))
    iy0 = max(0, int((cy - r - 1.5 / t) * t))
    iy1 = min(t - 1, int(math.ceil((cy + r + 1.5 / t) * t)))
    soft = 1.0 / t
    acx = cx * ar
    for y in range(iy0, iy1 + 1):
        py = (y + 0.5) / t - cy
        for x in range(ix0, ix1 + 1):
            d = math.hypot((x + 0.5) / t * ar - acx, py)
            cov = (r - d) / soft + 0.5
            if r_in > 0.0:
                cov = min(cov, (d - r_in) / soft + 0.5)
            if cov > 0.0:
                _put(buf, x, y, col, a * (1.0 if cov > 1.0 else cov))


def _fill_poly(buf, t, pts, col, a=1.0):
    """Scanline fill of a normalised polygon, 3x vertical supersample."""
    n = len(pts)
    ys = [p[1] for p in pts]
    iy0 = max(0, int(min(ys) * t))
    iy1 = min(t - 1, int(math.ceil(max(ys) * t)))
    for y in range(iy0, iy1 + 1):
        acc = [0.0] * t
        for s in range(3):
            sy = (y + (s + 0.5) / 3.0) / t
            xs = []
            for i in range(n):
                ax, ay = pts[i]
                bx, by = pts[(i + 1) % n]
                if (ay <= sy < by) or (by <= sy < ay):
                    xs.append(ax + (bx - ax) * (sy - ay) / (by - ay))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                px0, px1 = xs[k] * t, xs[k + 1] * t
                i0 = max(0, int(math.floor(px0)))
                i1 = min(t - 1, int(math.ceil(px1)) - 1)
                for x in range(i0, i1 + 1):
                    cov = min(x + 1.0, px1) - max(float(x), px0)
                    if cov > 0.0:
                        acc[x] += cov / 3.0
        for x in range(t):
            if acc[x] > 0.0:
                _put(buf, x, y, col, a * min(1.0, acc[x]))


def _band(buf, t, amp, period=13.0, seed=0):
    """Print banding: a low sinusoid that varies down the panel only.  A 2-D
    grain field is what a printed surface really has, but it costs 250 KB
    across these twenty tiles through a2kit's filter-0 PNG writer and the
    payload cap is the binding constraint here -- so the fine-scale variation
    comes from the ordered dither and the large-scale from this."""
    for y in range(t):
        v = amp * (math.sin(y / period + seed)
                   + 0.55 * math.sin(y / (period * 2.7) + seed * 1.7))
        row = buf[y]
        for x in range(t):
            p = row[x]
            p[0] += v
            p[1] += v
            p[2] += v


# ------------------------------------------------------------- a stroke font
# Monoline uppercase in a unit box, y UP (0 = baseline, 1 = cap height).
# Octagonal bowls rather than curves: that is what an arcade display face
# looks like anyway, and it keeps every glyph to <= 9 segments.
def _P(*pts):
    return [(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]


_FONT = {
    " ": [],
    "A": _P((0.04, 0.0), (0.50, 1.0), (0.96, 0.0)) + _P((0.21, 0.34), (0.79, 0.34)),
    "B": _P((0.10, 0.0), (0.10, 1.0), (0.68, 1.0), (0.90, 0.80), (0.68, 0.56),
            (0.10, 0.56)) + _P((0.68, 0.56), (0.93, 0.32), (0.70, 0.0), (0.10, 0.0)),
    "C": _P((0.95, 0.84), (0.74, 1.0), (0.28, 1.0), (0.05, 0.76), (0.05, 0.24),
            (0.28, 0.0), (0.74, 0.0), (0.95, 0.16)),
    "D": _P((0.10, 0.0), (0.10, 1.0), (0.64, 1.0), (0.93, 0.72), (0.93, 0.28),
            (0.64, 0.0), (0.10, 0.0)),
    "E": _P((0.92, 1.0), (0.10, 1.0), (0.10, 0.0), (0.92, 0.0))
         + _P((0.10, 0.50), (0.74, 0.50)),
    "F": _P((0.92, 1.0), (0.10, 1.0), (0.10, 0.0)) + _P((0.10, 0.52), (0.74, 0.52)),
    "G": _P((0.95, 0.84), (0.74, 1.0), (0.28, 1.0), (0.05, 0.76), (0.05, 0.24),
            (0.28, 0.0), (0.74, 0.0), (0.95, 0.18), (0.95, 0.46), (0.56, 0.46)),
    "H": _P((0.10, 0.0), (0.10, 1.0)) + _P((0.90, 0.0), (0.90, 1.0))
         + _P((0.10, 0.50), (0.90, 0.50)),
    "I": _P((0.50, 0.0), (0.50, 1.0)),
    "J": _P((0.86, 1.0), (0.86, 0.24), (0.62, 0.0), (0.30, 0.0), (0.07, 0.22)),
    "K": _P((0.10, 0.0), (0.10, 1.0)) + _P((0.92, 1.0), (0.14, 0.44))
         + _P((0.36, 0.58), (0.94, 0.0)),
    "L": _P((0.12, 1.0), (0.12, 0.0), (0.92, 0.0)),
    "M": _P((0.04, 0.0), (0.04, 1.0), (0.50, 0.30), (0.96, 1.0), (0.96, 0.0)),
    "N": _P((0.10, 0.0), (0.10, 1.0), (0.90, 0.0), (0.90, 1.0)),
    "O": _P((0.28, 1.0), (0.72, 1.0), (0.95, 0.76), (0.95, 0.24), (0.72, 0.0),
            (0.28, 0.0), (0.05, 0.24), (0.05, 0.76), (0.28, 1.0)),
    "P": _P((0.10, 0.0), (0.10, 1.0), (0.70, 1.0), (0.93, 0.80), (0.70, 0.54),
            (0.10, 0.54)),
    "Q": _P((0.28, 1.0), (0.72, 1.0), (0.95, 0.76), (0.95, 0.24), (0.72, 0.0),
            (0.28, 0.0), (0.05, 0.24), (0.05, 0.76), (0.28, 1.0))
         + _P((0.62, 0.26), (0.99, -0.10)),
    "R": _P((0.10, 0.0), (0.10, 1.0), (0.70, 1.0), (0.93, 0.80), (0.70, 0.54),
            (0.10, 0.54)) + _P((0.52, 0.54), (0.95, 0.0)),
    "S": _P((0.93, 0.86), (0.70, 1.0), (0.28, 1.0), (0.06, 0.80), (0.30, 0.57),
            (0.70, 0.52), (0.94, 0.30), (0.72, 0.0), (0.28, 0.0), (0.06, 0.16)),
    "T": _P((0.04, 1.0), (0.96, 1.0)) + _P((0.50, 1.0), (0.50, 0.0)),
    "U": _P((0.08, 1.0), (0.08, 0.24), (0.32, 0.0), (0.68, 0.0), (0.92, 0.24),
            (0.92, 1.0)),
    "V": _P((0.04, 1.0), (0.50, 0.0), (0.96, 1.0)),
    "W": _P((0.02, 1.0), (0.24, 0.0), (0.50, 0.62), (0.76, 0.0), (0.98, 1.0)),
    "X": _P((0.06, 1.0), (0.94, 0.0)) + _P((0.94, 1.0), (0.06, 0.0)),
    "Y": _P((0.06, 1.0), (0.50, 0.50), (0.94, 1.0)) + _P((0.50, 0.50), (0.50, 0.0)),
    "Z": _P((0.06, 1.0), (0.94, 1.0), (0.06, 0.0), (0.94, 0.0)),
    "0": _P((0.28, 1.0), (0.72, 1.0), (0.94, 0.76), (0.94, 0.24), (0.72, 0.0),
            (0.28, 0.0), (0.06, 0.24), (0.06, 0.76), (0.28, 1.0))
         + _P((0.26, 0.20), (0.74, 0.80)),
    "1": _P((0.22, 0.78), (0.52, 1.0), (0.52, 0.0)) + _P((0.20, 0.0), (0.84, 0.0)),
    "2": _P((0.06, 0.80), (0.30, 1.0), (0.70, 1.0), (0.94, 0.78), (0.06, 0.0),
            (0.94, 0.0)),
    "3": _P((0.06, 0.86), (0.30, 1.0), (0.72, 1.0), (0.90, 0.76), (0.52, 0.55))
         + _P((0.52, 0.55), (0.92, 0.32), (0.70, 0.0), (0.28, 0.0), (0.06, 0.16)),
    "4": _P((0.72, 0.0), (0.72, 1.0), (0.06, 0.30), (0.96, 0.30)),
    "5": _P((0.90, 1.0), (0.16, 1.0), (0.12, 0.58), (0.66, 0.60), (0.92, 0.36),
            (0.70, 0.0), (0.26, 0.0), (0.06, 0.16)),
    "6": _P((0.88, 0.90), (0.62, 1.0), (0.26, 1.0), (0.06, 0.72), (0.06, 0.22),
            (0.30, 0.0), (0.68, 0.0), (0.92, 0.22), (0.70, 0.48), (0.10, 0.44)),
    "7": _P((0.06, 1.0), (0.94, 1.0), (0.38, 0.0)),
    "8": _P((0.30, 0.54), (0.08, 0.76), (0.30, 1.0), (0.70, 1.0), (0.92, 0.76),
            (0.70, 0.54), (0.30, 0.54), (0.06, 0.28), (0.30, 0.0), (0.70, 0.0),
            (0.94, 0.28), (0.70, 0.54)),
    "9": _P((0.12, 0.10), (0.38, 0.0), (0.74, 0.0), (0.94, 0.28), (0.94, 0.78),
            (0.70, 1.0), (0.32, 1.0), (0.08, 0.78), (0.30, 0.52), (0.90, 0.56)),
    "!": _P((0.50, 1.0), (0.50, 0.30)) + _P((0.50, 0.11), (0.50, 0.02)),
    ".": _P((0.50, 0.09), (0.50, 0.02)),
    "-": _P((0.14, 0.50), (0.86, 0.50)),
    "'": _P((0.50, 1.0), (0.42, 0.74)),
    "&": _P((0.92, 0.0), (0.28, 0.66), (0.44, 1.0), (0.66, 0.84), (0.10, 0.30),
            (0.30, 0.0), (0.66, 0.10), (0.94, 0.44)),
}


def _text_w(s, h, ar, aspect, track):
    if not s:
        return 0.0
    return (len(s) * (aspect + track) - track) * h / ar


def text(buf, t, s, x, ybase, h, col, ar=1.0, aspect=0.60, track=0.16,
         weight=0.15, slant=0.0, align="c", box=None, outline=None, ow=0.07,
         alpha=1.0):
    """Set `s` in caps.  `h` is cap height in tile-Y units, `ybase` the
    baseline.  `box=(x0, x1)` fits the line to that span (condensing or
    expanding the face, which is what arcade title art does)."""
    s = s.upper()
    if box is not None:
        want = box[1] - box[0]
        nat = _text_w(s, h, ar, aspect, track)
        if nat > 1e-9:
            f = want / nat
            aspect *= f
            track *= f
        x = box[0]
        align = "l"
    tw = _text_w(s, h, ar, aspect, track)
    if align == "c":
        pen = x - tw * 0.5
    elif align == "r":
        pen = x - tw
    else:
        pen = x
    gw = aspect * h / ar
    adv = (aspect + track) * h / ar
    for ch in s:
        segs = _FONT.get(ch)
        if segs:
            mapped = []
            for (a, b) in segs:
                p0 = (pen + a[0] * gw + slant * a[1] * h / ar, ybase - a[1] * h)
                p1 = (pen + b[0] * gw + slant * b[1] * h / ar, ybase - b[1] * h)
                mapped.append((p0, p1))
            if outline is not None:
                for (p0, p1) in mapped:
                    _seg(buf, t, p0, p1, weight * h + 2.0 * ow * h, outline,
                         ar, alpha)
            for (p0, p1) in mapped:
                _seg(buf, t, p0, p1, weight * h, col, ar, alpha)
        pen += adv


# --------------------------------------------------------- shared small marks
def _fineprint(buf, t, x0, x1, y, h, n, col, ar, seed=3, a=0.75):
    """Rules standing in for body copy too small to be type at 256 px.  These
    are deliberately NOT letterforms: at 0.05 ft a real glyph is 3 texels and
    would be a lie either way, so they are drawn as what fine print looks like
    from across a room."""
    hsh = seed * 7919
    for i in range(n):
        hsh = (hsh * 1103515245 + 12345) & 0x7FFFFFFF
        f = 0.45 + 0.55 * (hsh / 0x7FFFFFFF)
        yy = y + i * h
        _rect(buf, t, x0, yy, x0 + (x1 - x0) * f, yy + h * 0.34, col, a)


# =============================================================== MORTAL KOMBAT
# EAST_RUN[3].  Black carcase, dark maroon T-molding, dark red-brown riser.
MK_BLACK = _hx("#161519")
MK_MAROON = _hx("#6b1e22")
MK_BONE = _hx("#e6e0d2")
MK_GOLD = _hx("#c8a24a")
MK_RED = _hx("#a8202a")
MK_BLUE = _hx("#59c8e8")


def mk_marquee(px, ox, oy, t):
    """Dark navy-to-black band, the pale MK dragon roundel dead centre,
    MORTAL / KOMBAT flanking it in condensed bone caps."""
    ar = PANEL_AR["mortal-kombat.marquee"]
    b = _new(t, _hx("#0b0d18"))
    _vgrad(b, t, 0.0, 1.0, _hx("#141a30"), _hx("#05060c"))
    _hgrad(b, t, 0.30, 0.70, _hx("#101528"), _hx("#1a2440"), 0.0, 1.0, 0.6)
    # backlight bloom behind the roundel
    for k in range(7):
        _ellipse(b, t, 0.50, 0.50, 0.46 - k * 0.05, _hx("#2c3c68"), ar, 0.10)
    # the roundel: bright ring, dark field, a dragon curled inside it
    _ellipse(b, t, 0.50, 0.50, 0.40, MK_BONE, ar, 1.0, r_in=0.30)
    _ellipse(b, t, 0.50, 0.50, 0.30, _hx("#0d1020"), ar)
    _ellipse(b, t, 0.50, 0.50, 0.30, MK_GOLD, ar, 1.0, r_in=0.265)
    body = [(0.500, 0.72), (0.474, 0.62), (0.487, 0.50), (0.516, 0.44),
            (0.527, 0.35), (0.505, 0.28)]
    _poly_line(b, t, body, 0.115, MK_BONE, ar)
    _poly_line(b, t, [(0.505, 0.30), (0.478, 0.25), (0.452, 0.29)],
               0.085, MK_BONE, ar)                       # head + snout
    _poly_line(b, t, [(0.487, 0.50), (0.452, 0.42), (0.446, 0.31)],
               0.070, MK_BONE, ar)                       # near wing
    _poly_line(b, t, [(0.500, 0.55), (0.545, 0.47), (0.556, 0.36)],
               0.070, MK_BONE, ar)                       # far wing
    _ellipse(b, t, 0.4705, 0.283, 0.022, _hx("#0d1020"), ar)   # eye
    # title, split either side of the roundel
    text(b, t, "MORTAL", 0.0, 0.685, 0.40, MK_BONE, ar,
         box=(0.030, 0.372), weight=0.17, outline=_hx("#3a2020"), ow=0.05)
    text(b, t, "KOMBAT", 0.0, 0.685, 0.40, MK_BONE, ar,
         box=(0.628, 0.970), weight=0.17, outline=_hx("#3a2020"), ow=0.05)
    # maroon T-molding closing the band top and bottom
    _rect(b, t, 0.0, 0.0, 1.0, 0.055, MK_MAROON)
    _rect(b, t, 0.0, 0.945, 1.0, 1.0, _hx("#4a1418"))
    _flush(px, ox, oy, b, t)


def mk_side(px, ox, oy, t):
    """Black flank.  No figurative graphic resolves in any frame; what does
    resolve is the dark maroon T-molding following the whole silhouette, so
    that is all this panel carries."""
    ar = PANEL_AR["mortal-kombat.side"]
    b = _new(t, MK_BLACK)
    _vgrad(b, t, 0.0, 1.0, _hx("#1e1d22"), _hx("#0c0b0e"))
    # a broad satin sheen down the front third (u1 is the cabinet FRONT)
    _hgrad(b, t, 0.55, 1.00, _hx("#000000"), _hx("#38343c"), 0.0, 1.0, 0.30)
    # T-molding: front edge, top edge, and the kick at the foot
    _rect(b, t, 0.945, 0.0, 1.0, 1.0, MK_MAROON)
    _rect(b, t, 0.0, 0.0, 1.0, 0.030, MK_MAROON)
    _rect(b, t, 0.0, 0.962, 1.0, 1.0, _hx("#4a1418"))
    _rect(b, t, 0.0, 0.905, 1.0, 0.962, _hx("#3a2420"))   # red-brown riser
    _band(b, t, 2.6, 15.0, 0.4)
    _flush(px, ox, oy, b, t)


def mk_front(px, ox, oy, t):
    """The identifying face: a large display-face MK with a dragon curling
    round the K, an ornate scroll below it, fine print, and a pale logo band."""
    ar = PANEL_AR["mortal-kombat.front"]
    b = _new(t, _hx("#141317"))
    _vgrad(b, t, 0.0, 1.0, _hx("#1b1a20"), _hx("#0a090c"))
    # MK, bone with a red outline, across the upper third
    text(b, t, "M", 0.30, 0.300, 0.255, MK_BONE, ar, aspect=0.70,
         weight=0.20, outline=MK_RED, ow=0.075)
    text(b, t, "K", 0.53, 0.300, 0.255, MK_BONE, ar, aspect=0.70,
         weight=0.20, outline=MK_RED, ow=0.075)
    # the dragon curling round the right of the K: a serpentine body that
    # tapers from a coiled tail up to a small head over the K's shoulder
    coil = [(0.648, 0.330), (0.724, 0.336), (0.786, 0.300), (0.800, 0.240),
            (0.762, 0.196), (0.706, 0.204)]
    for i in range(len(coil) - 1):
        _seg(b, t, coil[i], coil[i + 1], 0.062 - i * 0.008, MK_BONE, ar, 0.95)
    neck = [(0.706, 0.204), (0.678, 0.166), (0.700, 0.126), (0.748, 0.116)]
    for i in range(len(neck) - 1):
        _seg(b, t, neck[i], neck[i + 1], 0.040 - i * 0.004, MK_BONE, ar, 0.95)
    _fill_poly(b, t, [(0.748, 0.104), (0.812, 0.116), (0.826, 0.134),
                      (0.766, 0.140), (0.744, 0.130)], MK_BONE, 0.95)  # jaw
    _poly_line(b, t, [(0.742, 0.108), (0.726, 0.078), (0.756, 0.086)],
               0.018, MK_BONE, ar, 0.9)                                # horn
    _ellipse(b, t, 0.7660, 0.1215, 0.011, _hx("#141317"), ar)          # eye
    _fill_poly(b, t, [(0.700, 0.232), (0.646, 0.196), (0.612, 0.140),
                      (0.664, 0.176), (0.706, 0.208)], MK_BONE, 0.85)  # wing
    # the ornate pale scroll / banner under the wordmark
    _fill_poly(b, t, [(0.115, 0.352), (0.192, 0.386), (0.115, 0.420),
                      (0.150, 0.386)], _hx("#a49c8c"), 0.9)      # left tail
    _fill_poly(b, t, [(0.885, 0.352), (0.808, 0.386), (0.885, 0.420),
                      (0.850, 0.386)], _hx("#a49c8c"), 0.9)      # right tail
    _fill_poly(b, t, [(0.500, 0.348), (0.760, 0.360), (0.828, 0.386),
                      (0.760, 0.412), (0.500, 0.424), (0.240, 0.412),
                      (0.172, 0.386), (0.240, 0.360)], _hx("#d4ccb8"), 0.94)
    for k in range(3):
        _rect(b, t, 0.300 + k * 0.010, 0.372 + k * 0.014,
              0.700 - k * 0.010, 0.379 + k * 0.014, _hx("#4a4238"), 0.75)
    # three short lines of small light print
    _fineprint(b, t, 0.240, 0.760, 0.455, 0.034, 3, _hx("#a49eae"), ar, 5)
    # the wide pale logo band, low on the panel
    _rect(b, t, 0.090, 0.628, 0.910, 0.706, _hx("#b9b2a2"), 0.92)
    _rect(b, t, 0.090, 0.628, 0.910, 0.642, _hx("#8e887a"), 0.9)
    _ellipse(b, t, 0.500, 0.667, 0.052, _hx("#1a1820"), ar)
    _ellipse(b, t, 0.500, 0.667, 0.034, _hx("#b9b2a2"), ar)
    _rect(b, t, 0.560, 0.658, 0.860, 0.676, _hx("#1a1820"), 0.9)
    _rect(b, t, 0.140, 0.658, 0.440, 0.676, _hx("#1a1820"), 0.9)
    _fineprint(b, t, 0.060, 0.300, 0.760, 0.032, 3, _hx("#7e7888"), ar, 9)
    _fineprint(b, t, 0.700, 0.940, 0.760, 0.032, 3, _hx("#7e7888"), ar, 13)
    _rect(b, t, 0.0, 0.960, 1.0, 1.0, _hx("#43231e"))     # red-brown riser
    _flush(px, ox, oy, b, t)


def mk_deck(px, ox, oy, t):
    """The only strongly BLUE control deck in the east run.  Authored bright:
    ar2 multiplies the deck art by #4c4c4c."""
    ar = PANEL_AR["mortal-kombat.deck"]
    b = _new(t, _hx("#2f7fc0"))
    _vgrad(b, t, 0.0, 1.0, _hx("#17406e"), _hx("#57b6e2"))
    # a pale cyan sweep across the middle of the panel
    _fill_poly(b, t, [(0.00, 0.62), (0.30, 0.40), (0.58, 0.52), (1.00, 0.30),
                      (1.00, 0.44), (0.58, 0.66), (0.30, 0.54), (0.00, 0.76)],
               _hx("#a7e2f4"), 0.55)
    _fill_poly(b, t, [(0.00, 0.86), (0.36, 0.66), (0.68, 0.78), (1.00, 0.60),
                      (1.00, 0.70), (0.68, 0.88), (0.36, 0.76), (0.00, 0.96)],
               _hx("#0e2c50"), 0.45)
    # a dark navy legend strip along the deck BACK (tile top)
    _rect(b, t, 0.0, 0.0, 1.0, 0.135, _hx("#0c1a30"))
    text(b, t, "MORTAL KOMBAT", 0.50, 0.105, 0.075, _hx("#cfd8e4"), ar,
         box=(0.28, 0.72), weight=0.20)
    # printed button bezels where the geometry puts its buttons
    py1, py2 = 0.44, 0.62
    for sgn in (-1.0, 1.0):
        jx = 0.50 + sgn * 0.135
        _ellipse(b, t, jx, 0.53, 0.115, _hx("#0d2038"), ar, 0.65)
        for k in range(3):
            bxx = jx + sgn * (0.098 + k * 0.071)
            yy = py1 if (k % 2 == 0) else py2
            _ellipse(b, t, bxx, yy, 0.075, _hx("#f2f0e8"), ar, 0.85)
            _ellipse(b, t, bxx, yy, 0.058,
                     (MK_RED, _hx("#1f52b8"), _hx("#e8c832"))[k], ar, 0.95)
        for k in range(3):
            bxx = jx + sgn * (0.098 + k * 0.071)
            yy = py2 if (k % 2 == 0) else py1
            _ellipse(b, t, bxx, yy + 0.19, 0.075, _hx("#f2f0e8"), ar, 0.85)
            _ellipse(b, t, bxx, yy + 0.19, 0.058,
                     (_hx("#3aa64c"), _hx("#f2f0e8"), MK_RED)[k], ar, 0.95)
    _rect(b, t, 0.0, 0.955, 1.0, 1.0, _hx("#5a1418"))      # front lip
    _flush(px, ox, oy, b, t)


def mk_bezel(px, ox, oy, t):
    """Black screen surround, maroon inner line, the title small at the top --
    a faint pale line of type sits there in `v3 4`."""
    ar = PANEL_AR["mortal-kombat.bezel"]
    b = _new(t, _hx("#17161b"))
    _vgrad(b, t, 0.0, 1.0, _hx("#201f26"), _hx("#0d0c10"))
    _rect(b, t, 0.03, 0.02, 0.97, 0.135, _hx("#0d0c12"))
    text(b, t, "MORTAL KOMBAT", 0.50, 0.105, 0.058, _hx("#8e8898"), ar,
         box=(0.30, 0.70), weight=0.20)
    for (a0, a1) in ((0.030, 0.052), (0.948, 0.970)):
        _rect(b, t, a0, 0.14, a1, 0.96, MK_MAROON, 0.85)
    _rect(b, t, 0.03, 0.940, 0.97, 0.962, MK_MAROON, 0.85)
    _flush(px, ox, oy, b, t)


# ============================================================ LEGENDS ULTIMATE
# SOUTH_RUN[0].  Matte black everywhere; the front-panel logo grid is the
# identifying surface and the marquee wordmark is fully legible in v3 4 / v4 8.
LU_BLACK = _hx("#141821")
LU_SILVER = _hx("#e2e9f2")


def lu_marquee(px, ox, oy, t):
    ar = PANEL_AR["legends-ultimate.marquee"]
    b = _new(t, LU_BLACK)
    _vgrad(b, t, 0.0, 1.0, _hx("#1a1f2c"), _hx("#080a11"))
    # one line, upper half, ~72% of the band, wide condensed techno italic
    text(b, t, "LEGENDS ULTIMATE", 0.0, 0.520, 0.335, LU_SILVER, ar,
         box=(0.140, 0.905), weight=0.155, slant=0.20, track=0.10,
         outline=_hx("#5c6a80"), ow=0.030)
    # the clear black below the line that the photo shows
    _rect(b, t, 0.0, 0.0, 1.0, 0.030, _hx("#05060a"))
    _rect(b, t, 0.0, 0.970, 1.0, 1.0, _hx("#05060a"))
    _flush(px, ox, oy, b, t)


def lu_side(px, ox, oy, t):
    """The plainest flank in the room: matte black, no graphic in any frame.
    Only a broad satin drift and a slightly darker foot."""
    ar = PANEL_AR["legends-ultimate.side"]
    b = _new(t, _hx("#191a1f"))
    _vgrad(b, t, 0.0, 1.0, _hx("#212228"), _hx("#0e0f13"))
    _hgrad(b, t, 0.0, 1.0, _hx("#2a2b32"), _hx("#101115"), 0.0, 1.0, 0.35)
    _rect(b, t, 0.0, 0.972, 1.0, 1.0, _hx("#0a0b0e"))
    _band(b, t, 2.4, 17.0, 1.1)
    _flush(px, ox, oy, b, t)


_LU_L = [                    # left column, top to bottom, off `rec/lu_front.png`
    ("script", _hx("#e8ecf2")),
    ("pill", _hx("#dfe3ea")),
    ("arc", _hx("#b0243c")),
    ("bar", _hx("#e08ab4")),
    ("bar", _hx("#e6e9ee")),
    ("swoosh", _hx("#8f6ad0")),
    ("bar2", _hx("#63cfc4")),
    ("invaders", _hx("#f0f2f6")),
]
_LU_R = [
    ("word:JOUST", _hx("#8fc4ee")),
    ("script", _hx("#dde2ea")),
    ("word:MILLIPEDE", _hx("#eef1f5")),
    ("stack", _hx("#c8ccd6")),
    ("starwars", _hx("#e26aa8")),
    ("tee", _hx("#5fa8e8")),
    ("word:TRON", _hx("#6ea8e6")),
    ("bar", _hx("#c2b06a")),
]


def _lu_logo(b, t, kind, col, cx, cy, w, h, ar):
    """One licensed-game logo in the front-panel grid."""
    x0, x1 = cx - w * 0.5, cx + w * 0.5
    if kind.startswith("word:"):
        text(b, t, kind[5:], 0.0, cy + h * 0.42, h * 0.86, col, ar,
             box=(x0, x1), weight=0.20, track=0.14)
    elif kind == "script":
        n = 9
        pts = []
        for i in range(n):
            u = i / (n - 1.0)
            pts.append((x0 + w * u,
                        cy + h * 0.30 * math.sin(u * 7.4 + 0.6) - h * 0.10))
        _poly_line(b, t, pts, h * 0.16, col, ar, 0.95)
        _seg(b, t, (x0 + w * 0.06, cy - h * 0.46), (x0 + w * 0.20, cy + h * 0.2),
             h * 0.16, col, ar, 0.95)
    elif kind == "pill":
        _rect(b, t, x0, cy - h * 0.36, x1, cy + h * 0.36, col)
        for k in range(9):
            xx = x0 + w * (0.06 + k * 0.098)
            _rect(b, t, xx, cy - h * 0.20, xx + w * 0.052, cy + h * 0.20,
                  _hx("#181a20"))
    elif kind == "arc":
        pts = [(x0 + w * i / 8.0,
                cy + h * 0.34 * math.cos(math.pi * (i / 8.0 - 0.5) * 1.6))
               for i in range(9)]
        _poly_line(b, t, pts, h * 0.52, col, ar)
    elif kind == "bar":
        _rect(b, t, x0, cy - h * 0.30, x1, cy + h * 0.28, col)
        _rect(b, t, x0 + w * 0.03, cy - h * 0.10, x1 - w * 0.03, cy + h * 0.04,
              _hx("#1a1c22"), 0.45)
    elif kind == "bar2":
        _rect(b, t, x0, cy - h * 0.34, x1, cy + h * 0.10, col)
        _rect(b, t, x0 + w * 0.10, cy + h * 0.22, x1 - w * 0.10, cy + h * 0.36,
              col, 0.8)
    elif kind == "swoosh":
        _rect(b, t, x0 + w * 0.22, cy - h * 0.26, x1, cy + h * 0.26, col)
        _poly_line(b, t, [(x0 + w * 0.30, cy - h * 0.46),
                          (x0 + w * 0.06, cy - h * 0.10),
                          (x0 + w * 0.26, cy + h * 0.30)],
                   h * 0.18, col, ar)
    elif kind == "stack":
        _rect(b, t, x0 + w * 0.08, cy - h * 0.44, x1 - w * 0.08, cy - h * 0.06,
              col, 0.9)
        _rect(b, t, x0, cy + h * 0.02, x1, cy + h * 0.40, col, 0.9)
    elif kind == "starwars":
        text(b, t, "STAR", 0.0, cy - h * 0.14, h * 0.44, col, ar,
             box=(x0 + w * 0.18, x1 - w * 0.18), weight=0.24)
        text(b, t, "WARS", 0.0, cy + h * 0.46, h * 0.44, col, ar,
             box=(x0, x1), weight=0.24)
    elif kind == "tee":
        _rect(b, t, x0, cy - h * 0.40, x1, cy - h * 0.02, col)
        _rect(b, t, cx - w * 0.20, cy - h * 0.02, cx + w * 0.20, cy + h * 0.46,
              col)
    elif kind == "invaders":
        _rect(b, t, x0, cy - h * 0.46, x1, cy + h * 0.46, col)
        blue = _hx("#2a54c8")
        for k in range(4):
            ix = x0 + w * (0.070 + k * 0.230)
            iw = w * 0.155
            ih = h * 0.72
            iy = cy - ih * 0.5
            _rect(b, t, ix + iw * 0.18, iy + ih * 0.30,
                  ix + iw * 0.82, iy + ih * 0.72, blue)          # body
            _rect(b, t, ix, iy + ih * 0.46, ix + iw * 0.20,
                  iy + ih * 0.64, blue)                          # arms
            _rect(b, t, ix + iw * 0.80, iy + ih * 0.46, ix + iw,
                  iy + ih * 0.64, blue)
            _rect(b, t, ix + iw * 0.14, iy, ix + iw * 0.30,
                  iy + ih * 0.30, blue)                          # antennae
            _rect(b, t, ix + iw * 0.70, iy, ix + iw * 0.86,
                  iy + ih * 0.30, blue)
            _rect(b, t, ix + iw * 0.10, iy + ih * 0.76, ix + iw * 0.34,
                  iy + ih, blue)                                 # legs
            _rect(b, t, ix + iw * 0.66, iy + ih * 0.76, ix + iw * 0.90,
                  iy + ih, blue)


def lu_front(px, ox, oy, t):
    """A grid of about sixteen small licensed game logos in two columns --
    the surface that identifies this cabinet.  MILLIPEDE, STAR WARS, TRON and
    the Space Invaders block are the four legible in v3 4; the rest are drawn
    as coloured wordmark-shaped marks, not as titles I cannot read."""
    ar = PANEL_AR["legends-ultimate.front"]
    b = _new(t, _hx("#101219"))
    _vgrad(b, t, 0.0, 1.0, _hx("#161923"), _hx("#0a0b11"))
    rows = 8
    y0, y1 = 0.085, 0.945
    pitch = (y1 - y0) / rows
    for col_i, (cx, w) in enumerate(((0.275, 0.335), (0.700, 0.335))):
        table = _LU_L if col_i == 0 else _LU_R
        for r, (kind, col) in enumerate(table):
            _lu_logo(b, t, kind, col, cx, y0 + pitch * (r + 0.5), w,
                     pitch * 0.66, ar)
    _flush(px, ox, oy, b, t)


def lu_deck(px, ox, oy, t):
    """Wide black deck.  Individual controls do NOT resolve at 20x in any
    frame, so none are drawn -- the one thing that does resolve is the bright
    white lit strip along the front lip (tile bottom)."""
    ar = PANEL_AR["legends-ultimate.deck"]
    b = _new(t, _hx("#15161b"))
    _vgrad(b, t, 0.0, 1.0, _hx("#0e0f13"), _hx("#23242b"))
    _rect(b, t, 0.0, 0.0, 1.0, 0.10, _hx("#090a0d"))
    _hgrad(b, t, 0.10, 0.90, _hx("#15161b"), _hx("#2b2d35"), 0.20, 0.80, 0.45)
    _rect(b, t, 0.0, 0.885, 1.0, 0.925, _hx("#3a3d46"))
    _rect(b, t, 0.0, 0.925, 1.0, 1.0, _hx("#f4f6fa"))     # the lit lip
    _rect(b, t, 0.0, 0.925, 1.0, 0.945, _hx("#c8d2e0"))
    _flush(px, ox, oy, b, t)


def lu_bezel(px, ox, oy, t):
    ar = PANEL_AR["legends-ultimate.bezel"]
    b = _new(t, _hx("#212630"))
    _vgrad(b, t, 0.0, 1.0, _hx("#2a2f3a"), _hx("#131720"))
    _rect(b, t, 0.045, 0.045, 0.955, 0.955, _hx("#101319"))
    for (a0, a1) in ((0.045, 0.062), (0.938, 0.955)):
        _rect(b, t, a0, 0.045, a1, 0.955, _hx("#39404d"), 0.8)
    _rect(b, t, 0.045, 0.045, 0.955, 0.062, _hx("#39404d"), 0.8)
    _flush(px, ox, oy, b, t)


# ================================================================ RIDGE RACER
# The SW-corner driving cabinet.  Red body, yellow marquee band with dark type,
# black wheel deck, white italic wordmark on the red lower front.
RR_RED = _hx("#8e1a24")
RR_YEL = _hx("#e8d24e")
RR_INK = _hx("#241a10")


def rr_marquee(px, ox, oy, t):
    """Yellow band, two lines of dark type.  The band COLOUR is read straight
    off v4 5 / v4 8; the LETTERING is reconstructed from the wordmark on the
    lower front (`rec/rr_base.png`, 'RIDGE RAC' at 16x) because the marquee
    itself blows out in every frame."""
    ar = PANEL_AR["ridge-racer.marquee"]
    b = _new(t, RR_YEL)
    _vgrad(b, t, 0.0, 1.0, _hx("#f4e78c"), _hx("#cdb032"))
    _hgrad(b, t, 0.0, 0.35, _hx("#fdf6c0"), RR_YEL, 0.10, 0.90, 0.5)
    _rect(b, t, 0.0, 0.0, 1.0, 0.075, _hx("#8e1a24"))
    _rect(b, t, 0.0, 0.925, 1.0, 1.0, _hx("#6e1218"))
    text(b, t, "NAMCO", 0.0, 0.360, 0.155, RR_INK, ar,
         box=(0.400, 0.600), weight=0.20, slant=0.10)
    text(b, t, "RIDGE RACER", 0.0, 0.845, 0.400, RR_INK, ar,
         box=(0.085, 0.915), weight=0.20, slant=0.22, track=0.13)
    # a thin red keyline under the title, as the photo's band carries
    _rect(b, t, 0.09, 0.878, 0.91, 0.898, _hx("#a8202a"), 0.75)
    _flush(px, ox, oy, b, t)


def rr_side(px, ox, oy, t):
    """Not visible in any frame -- so this is the cabinet's body colour and
    nothing else: red/maroon over a black base, with a black T-molding at the
    front edge.  No graphic is invented."""
    ar = PANEL_AR["ridge-racer.side"]
    b = _new(t, RR_RED)
    _vgrad(b, t, 0.0, 1.0, _hx("#a8232e"), _hx("#5c1017"))
    _hgrad(b, t, 0.50, 1.00, _hx("#000000"), _hx("#c8404a"), 0.0, 1.0, 0.25)
    _rect(b, t, 0.0, 0.760, 1.0, 1.0, _hx("#17171b"))     # black lower mass
    _rect(b, t, 0.0, 0.745, 1.0, 0.762, _hx("#e6e2d8"), 0.55)
    _rect(b, t, 0.952, 0.0, 1.0, 1.0, _hx("#101014"))     # front T-molding
    _rect(b, t, 0.0, 0.0, 1.0, 0.028, _hx("#101014"))
    _band(b, t, 2.8, 14.0, 2.2)
    _flush(px, ox, oy, b, t)


def rr_front(px, ox, oy, t):
    """Black upper panel over the deep maroon lower front, which carries
    'RIDGE RACER' in white italic caps, with the recessed coin/service area
    below it."""
    ar = PANEL_AR["ridge-racer.front"]
    b = _new(t, _hx("#15151a"))
    _vgrad(b, t, 0.0, 0.560, _hx("#1e1e24"), _hx("#0d0d11"))
    _vgrad(b, t, 0.560, 1.0, _hx("#a02330"), _hx("#66131b"))
    _rect(b, t, 0.0, 0.552, 1.0, 0.572, _hx("#d8d4cc"), 0.55)
    # a pale speed-flash sweeping in from the left, as v4 8's base carries
    _fill_poly(b, t, [(0.020, 0.640), (0.300, 0.616), (0.330, 0.652),
                      (0.050, 0.678)], _hx("#e8e4dc"), 0.55)
    text(b, t, "RIDGE RACER", 0.0, 0.790, 0.115, _hx("#f4f2ec"), ar,
         box=(0.060, 0.620), weight=0.19, slant=0.26, track=0.12)
    _rect(b, t, 0.100, 0.880, 0.900, 0.985, _hx("#0d0d11"))
    _rect(b, t, 0.120, 0.898, 0.880, 0.968, _hx("#1c1c22"))
    for k in range(3):                                    # coin slots
        xx = 0.400 + k * 0.075
        _rect(b, t, xx, 0.910, xx + 0.028, 0.956, _hx("#08080a"))
    _flush(px, ox, oy, b, t)


def rr_deck(px, ox, oy, t):
    """The driving deck: a big round black wheel with a pale olive centre boss,
    a small dark cluster to its left and two round white illuminated buttons to
    its right.  ar2's `upright()` also builds two joysticks and six buttons on
    every deck -- SUPPRESS THEM FOR THIS MACHINE, it is a wheel cabinet."""
    ar = PANEL_AR["ridge-racer.deck"]
    b = _new(t, _hx("#191a1f"))
    _vgrad(b, t, 0.0, 1.0, _hx("#101116"), _hx("#26272e"))
    _rect(b, t, 0.0, 0.0, 1.0, 0.085, _hx("#0a0a0d"))
    # wheel
    _ellipse(b, t, 0.500, 0.500, 0.400, _hx("#0e0e12"), ar, 0.55)
    _ellipse(b, t, 0.500, 0.500, 0.375, _hx("#33343c"), ar, 1.0, r_in=0.290)
    _ellipse(b, t, 0.500, 0.500, 0.352, _hx("#5a5c66"), ar, 0.55, r_in=0.318)
    for a_deg in (90.0, 210.0, 330.0):
        a_r = math.radians(a_deg)
        _seg(b, t, (0.500, 0.500),
             (0.500 + math.cos(a_r) * 0.300 / ar, 0.500 + math.sin(a_r) * 0.300),
             0.085, _hx("#2b2c34"), ar)
    _ellipse(b, t, 0.500, 0.500, 0.145, _hx("#1b1c21"), ar)
    _ellipse(b, t, 0.500, 0.500, 0.120, _hx("#b6b884"), ar)   # olive boss
    _ellipse(b, t, 0.500, 0.500, 0.075, _hx("#8d9060"), ar)
    # left cluster: small dark buttons
    for k in range(2):
        for j in range(2):
            _ellipse(b, t, 0.115 + j * 0.062, 0.400 + k * 0.230, 0.070,
                     _hx("#0c0c10"), ar, 0.9)
            _ellipse(b, t, 0.115 + j * 0.062, 0.400 + k * 0.230, 0.052,
                     _hx("#3c3e46"), ar)
    # right: two round white illuminated buttons + a service pad
    for k in range(2):
        _ellipse(b, t, 0.845, 0.360 + k * 0.250, 0.098, _hx("#0c0c10"), ar, 0.9)
        _ellipse(b, t, 0.845, 0.360 + k * 0.250, 0.078, _hx("#f2f4f6"), ar)
    _rect(b, t, 0.735, 0.700, 0.915, 0.790, _hx("#2a2b32"))
    _rect(b, t, 0.0, 0.945, 1.0, 1.0, _hx("#7a1620"))     # red front lip
    _flush(px, ox, oy, b, t)


def rr_bezel(px, ox, oy, t):
    ar = PANEL_AR["ridge-racer.bezel"]
    b = _new(t, _hx("#16161b"))
    _vgrad(b, t, 0.0, 1.0, _hx("#1e1e25"), _hx("#0c0c10"))
    for (a0, a1) in ((0.030, 0.058), (0.942, 0.970)):
        _rect(b, t, a0, 0.03, a1, 0.97, _hx("#7a1620"), 0.9)
    _rect(b, t, 0.030, 0.030, 0.970, 0.058, _hx("#7a1620"), 0.9)
    _rect(b, t, 0.030, 0.942, 0.970, 0.970, _hx("#7a1620"), 0.9)
    text(b, t, "RIDGE RACER", 0.50, 0.150, 0.058, _hx("#8e8a84"), ar,
         box=(0.32, 0.68), weight=0.20, slant=0.22)
    _flush(px, ox, oy, b, t)


# ========================================================= GOLDEN TEE 3D GOLF
# NORTH_RUN[3].  Flat black carcase; all the green lives on the marquee, the
# lit instruction strip and the deck.  Greens are the v4 6 / v4 7 readings,
# lifted for the daylight render (the v3 1 greens are blue-shifted).
GT_GOLD = _hx("#e8d18a")
GT_INK = _hx("#20240f")


def gt_marquee(px, ox, oy, t):
    """A photographic golf-course scene -- pale sky and trees upper left,
    fairway right -- carrying GOLDEN TEE 3D over GOLF! in gold display caps
    with a dark outline, and a small square logo at the far right."""
    ar = PANEL_AR["golden-tee-3d-golf.marquee"]
    b = _new(t, _hx("#4e6a44"))
    _vgrad(b, t, 0.0, 1.0, _hx("#b8d0a8"), _hx("#33502f"))
    # sky wedge over the upper left, fairway sweeping down to the right
    _fill_poly(b, t, [(0.00, 0.00), (0.62, 0.00), (0.44, 0.36), (0.00, 0.44)],
               _hx("#cfe0c4"), 0.9)
    _fill_poly(b, t, [(0.00, 0.40), (0.46, 0.33), (1.00, 0.20), (1.00, 1.00),
                      (0.00, 1.00)], _hx("#5c8248"), 0.85)
    _fill_poly(b, t, [(0.00, 0.62), (0.40, 0.52), (1.00, 0.44), (1.00, 1.00),
                      (0.00, 1.00)], _hx("#3f6636"), 0.75)
    # tree line along the horizon
    for k in range(9):
        tx = 0.045 + k * 0.075
        th = 0.20 + 0.09 * math.sin(k * 2.3)
        _ellipse(b, t, tx, 0.31 - th * 0.35, th * 0.55, _hx("#22401f"), ar, 0.95)
        _rect(b, t, tx - 0.006, 0.30 - th * 0.10, tx + 0.006, 0.36,
              _hx("#2a2418"), 0.8)
    # a bright green and a pale bunker to the right
    _ellipse(b, t, 0.845, 0.560, 0.130, _hx("#89ad63"), ar, 0.9)
    _ellipse(b, t, 0.760, 0.700, 0.095, _hx("#e2dcbc"), ar, 0.85)
    _ellipse(b, t, 0.848, 0.545, 0.020, _hx("#f4f4ee"), ar)      # the ball
    # a small square logo block at the far right end
    _rect(b, t, 0.930, 0.300, 0.988, 0.700, _hx("#16281a"), 0.9)
    _rect(b, t, 0.941, 0.360, 0.977, 0.470, GT_GOLD, 0.9)
    _rect(b, t, 0.941, 0.520, 0.977, 0.630, GT_GOLD, 0.6)
    # title
    text(b, t, "GOLDEN TEE 3D", 0.0, 0.560, 0.255, GT_GOLD, ar,
         box=(0.120, 0.700), weight=0.19, outline=_hx("#1c2a14"), ow=0.055)
    text(b, t, "GOLF!", 0.0, 0.900, 0.290, _hx("#f2e6b4"), ar,
         box=(0.230, 0.560), weight=0.20, outline=_hx("#1c2a14"), ow=0.055)
    # the little ball-on-a-tee at the lower left the photo shows
    _fill_poly(b, t, [(0.0585, 0.808), (0.0855, 0.808), (0.0745, 0.940),
                      (0.0695, 0.940)], _hx("#d8caa0"), 0.95)
    _ellipse(b, t, 0.0720, 0.770, 0.048, _hx("#f6f6f0"), ar, 0.95)
    _ellipse(b, t, 0.0670, 0.756, 0.020, _hx("#ffffff"), ar, 0.6)
    _rect(b, t, 0.0, 0.0, 1.0, 0.030, _hx("#0f1a10"))
    _rect(b, t, 0.0, 0.965, 1.0, 1.0, _hx("#0f1a10"))
    _flush(px, ox, oy, b, t)


def gt_side(px, ox, oy, t):
    """Plain black flanks in every frame -- ~#2e2f33 in v4 6.  No side art."""
    ar = PANEL_AR["golden-tee-3d-golf.side"]
    b = _new(t, _hx("#2c2d31"))
    _vgrad(b, t, 0.0, 1.0, _hx("#35363b"), _hx("#1a1b1e"))
    _hgrad(b, t, 0.62, 1.00, _hx("#000000"), _hx("#43444a"), 0.0, 1.0, 0.22)
    _rect(b, t, 0.0, 0.968, 1.0, 1.0, _hx("#131418"))
    _rect(b, t, 0.966, 0.0, 1.0, 1.0, _hx("#1e1f23"))
    _band(b, t, 2.5, 19.0, 3.0)
    _flush(px, ox, oy, b, t)


def gt_front(px, ox, oy, t):
    """Plain black, a small silver Golden Tee wordmark high on it, and a coin
    door with three vertical slots and a white coin-return button below."""
    ar = PANEL_AR["golden-tee-3d-golf.front"]
    b = _new(t, _hx("#212227"))
    _vgrad(b, t, 0.0, 1.0, _hx("#292a30"), _hx("#141518"))
    text(b, t, "GOLDEN TEE", 0.0, 0.135, 0.072, _hx("#c6c8cc"), ar,
         box=(0.290, 0.710), weight=0.18, slant=0.16, track=0.13)
    _seg(b, t, (0.290, 0.163), (0.710, 0.152), 0.012, _hx("#9fa2a8"), ar, 0.8)
    # coin door
    _rect(b, t, 0.330, 0.560, 0.670, 0.850, _hx("#17181c"))
    _rect(b, t, 0.345, 0.575, 0.655, 0.835, _hx("#2a2b31"))
    for k in range(3):
        xx = 0.395 + k * 0.075
        _rect(b, t, xx, 0.600, xx + 0.030, 0.700, _hx("#0c0d10"))
        _rect(b, t, xx + 0.004, 0.606, xx + 0.026, 0.694, _hx("#3c3e46"), 0.6)
    _ellipse(b, t, 0.500, 0.782, 0.055, _hx("#0c0d10"), ar)
    _ellipse(b, t, 0.500, 0.782, 0.040, _hx("#eceef2"), ar)
    _flush(px, ox, oy, b, t)


def gt_deck(px, ox, oy, t):
    """Two printed bands: three yellow block-capital words on very dark green
    across the back, and a bright grass-green golf-course image filling the
    rest, with the white trackball centred.  ar2's joysticks must be suppressed
    here too -- this machine has a trackball."""
    ar = PANEL_AR["golden-tee-3d-golf.deck"]
    b = _new(t, _hx("#6f9459"))
    _vgrad(b, t, 0.180, 1.0, _hx("#7ba05f"), _hx("#4c7440"))
    # the dark-green legend band with GOLDEN / TEE / GOLF in yellow caps
    _rect(b, t, 0.0, 0.0, 1.0, 0.180, _hx("#1b200c"))
    _rect(b, t, 0.330, 0.0, 0.340, 0.180, _hx("#3a4018"))
    _rect(b, t, 0.660, 0.0, 0.670, 0.180, _hx("#3a4018"))
    text(b, t, "GOLDEN", 0.0, 0.140, 0.098, _hx("#d9df94"), ar,
         box=(0.045, 0.290), weight=0.21)
    text(b, t, "TEE", 0.0, 0.140, 0.098, _hx("#c6cd82"), ar,
         box=(0.420, 0.582), weight=0.21)
    text(b, t, "GOLF", 0.0, 0.140, 0.098, _hx("#d9df94"), ar,
         box=(0.720, 0.945), weight=0.21)
    # course: fairway bands, a putting green, a bunker, a ball
    _fill_poly(b, t, [(0.00, 0.34), (0.42, 0.26), (1.00, 0.36), (1.00, 0.52),
                      (0.40, 0.44), (0.00, 0.50)], _hx("#8fb26a"), 0.75)
    _fill_poly(b, t, [(0.00, 0.72), (0.34, 0.62), (1.00, 0.70), (1.00, 1.00),
                      (0.00, 1.00)], _hx("#3f6636"), 0.65)
    _ellipse(b, t, 0.190, 0.480, 0.150, _hx("#a4c085"), ar, 0.85)
    _ellipse(b, t, 0.810, 0.470, 0.135, _hx("#a4c085"), ar, 0.85)
    _ellipse(b, t, 0.735, 0.720, 0.110, _hx("#e0dcbe"), ar, 0.80)  # bunker
    _ellipse(b, t, 0.255, 0.740, 0.085, _hx("#e0dcbe"), ar, 0.75)
    _ellipse(b, t, 0.186, 0.470, 0.030, _hx("#f6f6f0"), ar)        # ball
    _seg(b, t, (0.812, 0.470), (0.812, 0.310), 0.016, _hx("#f0f0ea"), ar, 0.9)
    _fill_poly(b, t, [(0.812, 0.310), (0.876, 0.336), (0.812, 0.362)],
               _hx("#d43a34"), 0.95)                               # pin flag
    # the white trackball, dead centre, with a small button either side
    _ellipse(b, t, 0.500, 0.590, 0.215, _hx("#15170f"), ar, 0.85)
    _ellipse(b, t, 0.500, 0.590, 0.180, _hx("#f4f5f0"), ar)
    _ellipse(b, t, 0.470, 0.545, 0.070, _hx("#ffffff"), ar, 0.55)
    for sgn in (-1.0, 1.0):
        _ellipse(b, t, 0.500 + sgn * 0.185, 0.640, 0.090, _hx("#15170f"), ar, 0.8)
        _ellipse(b, t, 0.500 + sgn * 0.185, 0.640, 0.068, _hx("#d8d0a0"), ar)
    _rect(b, t, 0.0, 0.960, 1.0, 1.0, _hx("#1b2410"))
    _flush(px, ox, oy, b, t)


def gt_bezel(px, ox, oy, t):
    """Black surround with the LIT YELLOW three-panel instruction strip across
    the bottom -- one of the few genuinely emissive surfaces on the north wall,
    so give this panel an emissive material, not a plain one."""
    ar = PANEL_AR["golden-tee-3d-golf.bezel"]
    b = _new(t, _hx("#1a1b1f"))
    _vgrad(b, t, 0.0, 1.0, _hx("#232429"), _hx("#101114"))
    text(b, t, "GOLDEN TEE 3D GOLF", 0.50, 0.085, 0.045, _hx("#8d9096"), ar,
         box=(0.26, 0.74), weight=0.20)
    y0, y1 = 0.790, 0.960
    _rect(b, t, 0.030, y0 - 0.016, 0.970, y1 + 0.014, _hx("#0a0b0d"))
    for k in range(3):
        x0 = 0.045 + k * 0.3080
        _rect(b, t, x0, y0, x0 + 0.2860, y1, _hx("#e8dc5a"))
        _rect(b, t, x0, y0, x0 + 0.2860, y0 + 0.022, _hx("#f6ee9a"))
        _fineprint(b, t, x0 + 0.030, x0 + 0.256, y0 + 0.046, 0.036, 3,
                   _hx("#26240c"), ar, 200 + k, 0.9)
    _flush(px, ox, oy, b, t)


# ==================================================================== exports
PANELS = {
    "mortal-kombat.marquee": mk_marquee,
    "mortal-kombat.side": mk_side,
    "mortal-kombat.front": mk_front,
    "mortal-kombat.deck": mk_deck,
    "mortal-kombat.bezel": mk_bezel,

    "legends-ultimate.marquee": lu_marquee,
    "legends-ultimate.side": lu_side,
    "legends-ultimate.front": lu_front,
    "legends-ultimate.deck": lu_deck,
    "legends-ultimate.bezel": lu_bezel,

    "ridge-racer.marquee": rr_marquee,
    "ridge-racer.side": rr_side,
    "ridge-racer.front": rr_front,
    "ridge-racer.deck": rr_deck,
    "ridge-racer.bezel": rr_bezel,

    "golden-tee-3d-golf.marquee": gt_marquee,
    "golden-tee-3d-golf.side": gt_side,
    "golden-tee-3d-golf.front": gt_front,
    "golden-tee-3d-golf.deck": gt_deck,
    "golden-tee-3d-golf.bezel": gt_bezel,
}
