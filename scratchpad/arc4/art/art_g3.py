"""Printed artwork for the Arcade Room's three ODDITIES -- round 5, agent g3.

    EAST_RUN[0]   star-wars-atari              free-standing angled cabinet,
                                               NE corner, yellow carcase
    CORNER        ridge-racer                  Namco driving cabinet, SW corner
    NORTH_RUN[0]  north-1-graffiti-multicade   full-size upright, pale line-art
                                               wrap, NO legible title

WHY THIS FILE WAS REWRITTEN.  Round 4 gave every machine a marquee that works
and then stopped.  Three independent critics rejected the round separately and
named the same defect in the same words: below the marquee all sixteen machines
were ONE asset recoloured -- the same flat-black front panel with the same
centred grey coin-door rectangle at the same size and position, the same
two-joystick deck (one red top, one blue top) over the same row of flat square
buttons, and a blurry white word floated on an otherwise empty field standing in
for a graphic.  They were right; `shots/r4_mq_east.png` beside
`docs/photos-jpg/Arcade Room v4 8.jpg` settles it in one glance.

Round 5 replaces every surface below the marquee for these three.  Each machine
now has its OWN ground colour, its OWN composition running edge to edge to the
floor, its OWN coin-door treatment at its own size and place, and its OWN
control-deck layout.  The three round-4 marquees are kept, redrawn here
unchanged in intent (that was the half that worked).

--------------------------------------------------------------------------
1.  WHAT THE INTEGRATOR MUST WIRE -- `DECKS` and `COINDOOR`, both at the foot
    of this file.

    Buttons, joysticks, wheels and coin-door boxes are GEOMETRY that
    `ar2.upright()` places, so an art module cannot vary them by painting.
    Round 4's critics counted the same two sticks and six flat squares on all
    sixteen machines, and the same grey slab low on every front.  So the layout
    is exported as DATA instead.  Both dicts are keyed by slug and use the
    panel's OWN normalised tile coordinates, which is what makes the geometry
    land ON the printed graphic rather than beside it.

    DECK TILE  ->  cabinet-local feet, exactly as `upright()` already UVs it:

        x = (-bw/2 + 0.06) + u * (bw - 0.12)          u = 0 at the tile's left
        z = (ft + 0.04)    + v * ((fd - 0.06) - (ft + 0.04))
        y = dy + 0.014                                (the deck art plane)

        so v = 0 is the BACK of the deck (under the screen) and v = 1 is the
        FRONT edge nearest the player.  ft = bd/2 - 0.62, fd = bd/2 + 0.40.

    FRONT TILE ->  cabinet-local feet, same derivation from `upright()`:

        x = (-bw/2 + 0.08) + u * (bw - 0.16)
        y = (dy - 0.62)    - v * ((dy - 0.62) - (plinth + 0.16))
        z = fb + 0.008                                (the printed front plane)

        so v = 0 is the TOP of the printed front panel and v = 1 its bottom.

2.  ASPECT.  A square atlas tile is stretched onto a rectangular quad, so a
    circle drawn as a circle in the tile comes out an ellipse on the cabinet.
    Every panel declares its quad's world aspect (W/H) in `PANEL_AR` and every
    round, stroked or typeset element goes through an `ar`-aware helper, so it
    lands correctly proportioned AFTER the stretch.  The values are computed
    from `ar2.py`'s own rows:

        side    = 2.95 / top                     (the profile bbox)
        marquee = (bw - 0.12) / mqh
        front   = (bw - 0.16) / (dy - 0.78)
        deck    = (bw - 0.12) / 0.92

    Change a machine's bw / top / dy / mqh and PANEL_AR must change with it or
    the lettering squashes.

3.  EXPOSURE.  `a2kit` samples `.side` / `.front` / `.marquee` through ART
    (#ffffff) so those tiles are true albedo -- a yellow cabinet is authored
    yellow, a near-black one near-black.  It samples `.deck` through ART_DK
    (#4c4c4c) because an up-facing surface over-collects roughly 2x in this
    scene, so the `.deck` tiles here are authored about twice their real value
    and will look washed out in the flat preview sheet.  That is correct.

    The brief asked for panel means of 200-240.  Two of these three machines
    are photographically NEAR BLACK (the multicade's wrap, Ridge Racer's
    recessed front panel) and lifting them to 220 would print a grey cabinet.
    What is lifted instead is the INK: the multicade's pale line work is
    authored at 190-235 against a ground lifted to ~55, so the wrap reads as
    line art rather than as a dark slab.  Measured means are in `MEANS` at the
    foot of the file, per panel, with the reason for each.

4.  NO PHOTO-DERIVED RASTER.  Every mark here is drawn from primitives.  The
    photographs are 600x450 night frames of lit 3-D cabinets at an angle;
    rectifying one would bake the room's RGB wash into a surface the renderer
    then lights again.

5.  WHAT IS *NOT* INVENTED.  Star Wars' marquee, front and control deck appear
    in NO photograph, and the multicade has no legible title in any frame at
    any magnification.  Those surfaces are built from what IS evidenced (the
    yellow carcase, the black art panel, the pale line wrap) plus honest
    cabinet hardware -- coin doors, returns, vents, service plates.  No title
    is printed on the multicade's marquee and no Atari logo is printed
    anywhere.  Each claim is recorded in `NOTES`, panel by panel, with the
    photograph and pixel box it was read off.

CONVENTIONS.  Tile (0, 0) is the TOP-LEFT of the panel, matching `uvq`/`sweep`
in a2kit.  On a `.side` tile u = 0 is the cabinet's BACK and u = 1 its FRONT
(that is `sweep`'s profile-bbox mapping), and v = 0 is the top of the cabinet.
Colours are quantised to multiples of 8 and dithered with a fixed 4x4 Bayer
matrix on the way out, copied from a2kit, so the packed PNG stays cheap.
"""

import math

TILE = 256                       # tile edge in px, matches a2kit

# world aspect (quad width / quad height) of every panel, from ar2.py geometry.
# ROUND 5 machines first; the three round-4 carry-overs after them.
PANEL_AR = {
    # star-wars-atari  EAST_RUN[0]  bw 2.34  top 6.28  dy 2.56  mqh 0.70
    "star-wars-atari.marquee": 3.1714,
    "star-wars-atari.side": 0.4697,
    "star-wars-atari.front": 1.2247,
    "star-wars-atari.deck": 2.4130,
    # ridge-racer      CORNER       bw 2.42  top 6.06  dy 2.58  mqh 0.66
    "ridge-racer.marquee": 3.4848,
    "ridge-racer.side": 0.4868,
    "ridge-racer.front": 1.2556,
    "ridge-racer.deck": 2.5000,
    "ridge-racer.bezel": 1.04,
    # north-1-...      NORTH_RUN[0] bw 2.44  top 6.20  dy 2.56  mqh 0.72
    "north-1-graffiti-multicade.marquee": 3.2222,
    "north-1-graffiti-multicade.side": 0.4758,
    "north-1-graffiti-multicade.front": 1.2809,
    "north-1-graffiti-multicade.deck": 2.5217,
    # ---- round-4 carry-overs, see LEGACY_PANELS at the foot of the file
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


# ------------------------------------------------- round-5 drawing additions
class _R(object):
    """A tiny LCG.  Every scatter in this file is seeded, so the artwork is
    byte-identical between runs and the atlas PNG does not churn."""

    def __init__(self, s):
        self.s = (s * 7919 + 12345) & 0x7FFFFFFF or 1

    def u(self):
        self.s = (self.s * 1103515245 + 12345) & 0x7FFFFFFF
        return self.s / float(0x7FFFFFFF)

    def f(self, a, b):
        return a + (b - a) * self.u()

    def i(self, a, b):
        return int(self.f(a, b + 0.999))


def _ellp(cx, cy, rx, ry, ar=1.0, n=44, a0=0.0, a1=None):
    """Points on an ellipse.  `rx`/`ry` are both LENGTHS in tile-Y units; rx is
    divided by `ar` so the shape survives the stretch onto the quad."""
    a1 = a0 + 2.0 * math.pi if a1 is None else a1
    return [(cx + math.cos(a0 + (a1 - a0) * i / float(n)) * rx / ar,
             cy + math.sin(a0 + (a1 - a0) * i / float(n)) * ry)
            for i in range(n + (0 if a1 - a0 >= 6.28 else 1))]


def _arc(buf, t, cx, cy, r, a0, a1, w, col, ar=1.0, a=1.0, rx=None):
    rx = r if rx is None else rx
    n = max(8, int(abs(a1 - a0) * max(r, rx) * t * 0.55))
    _poly_line(buf, t, _ellp(cx, cy, rx, r, ar, n, a0, a1), w, col, ar, a)


def _taper(buf, t, p0, p1, w0, w1, col, ar=1.0, a=1.0, n=12):
    """A stroke whose width runs from w0 to w1 -- the graffiti wrap's whole
    vocabulary, and what makes a brush mark read as a brush mark."""
    for i in range(n):
        k0, k1 = i / float(n), (i + 1) / float(n)
        q0 = (p0[0] + (p1[0] - p0[0]) * k0, p0[1] + (p1[1] - p0[1]) * k0)
        q1 = (p0[0] + (p1[0] - p0[0]) * k1, p0[1] + (p1[1] - p0[1]) * k1)
        _seg(buf, t, q0, q1, w0 + (w1 - w0) * (k0 + k1) * 0.5, col, ar, a)


def _inpoly(pts, x, y):
    n = len(pts)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if (yi > y) != (yj > y):
            if x < xi + (xj - xi) * (y - yi) / (yj - yi):
                inside = not inside
        j = i
    return inside


def _stars(buf, t, poly, n, seed, ar, big=6):
    """A starfield clipped to a polygon.  Sizes vary and the few big ones get a
    four-point flare, because a printed starfield is not a uniform stipple."""
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    r = _R(seed)
    got = 0
    tries = 0
    while got < n and tries < n * 12:
        tries += 1
        x = r.f(min(xs), max(xs))
        y = r.f(min(ys), max(ys))
        if not _inpoly(poly, x, y):
            continue
        got += 1
        s = r.f(0.0016, 0.0042)
        c = 190.0 + r.f(0.0, 62.0)
        _ellipse(buf, t, x, y, s, (c, c, c * 1.02), ar, r.f(0.55, 1.0))
        if got % max(1, n // big) == 0:
            f = s * 3.4
            _seg(buf, t, (x - f / ar, y), (x + f / ar, y), s * 0.9,
                 (c, c, c), ar, 0.55)
            _seg(buf, t, (x, y - f), (x, y + f), s * 0.9, (c, c, c), ar, 0.55)


def _glyphs(buf, t, x0, y0, x1, y1, n, seed, c_lo, c_hi, ar, avoid=None,
            scale=1.0, a=0.85):
    """The multicade wrap's small marks: ticks, bars, tiny rings, chevrons and
    short zigzags.  Deliberately NOT letterforms -- the roster failed to read a
    title off this machine at any magnification and so did every other reading,
    so nothing here may resolve into words."""
    r = _R(seed)
    for _ in range(n):
        x = r.f(x0, x1)
        y = r.f(y0, y1)
        if avoid is not None and _inpoly(avoid, x, y):
            continue
        col = c_lo if r.u() < 0.55 else c_hi
        s = r.f(0.011, 0.030) * scale
        w = r.f(0.0035, 0.0075) * scale
        k = r.i(0, 5)
        aa = a * r.f(0.45, 1.0)
        if k == 0:                                    # tick
            th = r.f(0.0, 3.14)
            _seg(buf, t, (x - math.cos(th) * s / ar, y - math.sin(th) * s),
                 (x + math.cos(th) * s / ar, y + math.sin(th) * s), w, col,
                 ar, aa)
        elif k == 1:                                  # small filled bar
            _rect(buf, t, x, y, x + s * 1.5 / ar, y + w * 2.2, col, aa)
        elif k == 2:                                  # tiny ring
            _ellipse(buf, t, x, y, s, col, ar, aa, r_in=max(0.0, s - w))
        elif k == 3:                                  # chevron
            _poly_line(buf, t, [(x - s / ar, y - s * 0.7), (x, y),
                                (x - s / ar, y + s * 0.7)], w, col, ar, aa)
        elif k == 4:                                  # zigzag
            _poly_line(buf, t, [(x, y), (x + s * 0.8 / ar, y - s * 0.8),
                                (x + s * 1.6 / ar, y),
                                (x + s * 2.4 / ar, y - s * 0.7)], w, col,
                       ar, aa)
        else:                                         # short double rule
            _seg(buf, t, (x, y), (x + s * 2.0 / ar, y), w, col, ar, aa)
            _seg(buf, t, (x, y + w * 3.0), (x + s * 1.3 / ar, y + w * 3.0),
                 w * 0.7, col, ar, aa * 0.7)


def _brush(buf, t, y0, y1, seed, amp=10.0, step=0.010):
    """Brushed metal along the panel's X axis -- decks and steel plates."""
    r = _R(seed)
    y = y0
    while y < y1:
        j = r.f(-amp, amp)
        col = (255.0, 255.0, 255.0) if j > 0 else (0.0, 0.0, 0.0)
        _rect(buf, t, 0.0, y, 1.0, min(y1, y + step), col, abs(j) / 255.0)
        y += step


def _sheen(buf, t, x0, y0, x1, y1, period, seed, amp=5.0):
    """A slow diagonal value drift, so a large flat field is not dead flat."""
    r = _R(seed)
    ph = r.f(0.0, 6.28)
    ix0, ix1 = max(0, int(x0 * t)), min(t, int(math.ceil(x1 * t)))
    iy0, iy1 = max(0, int(y0 * t)), min(t, int(math.ceil(y1 * t)))
    for y in range(iy0, iy1):
        for x in range(ix0, ix1):
            v = amp * math.sin((x * 0.7 + y) / period + ph)
            p = buf[y][x]
            p[0] += v
            p[1] += v
            p[2] += v


def _bevel(buf, t, x0, y0, x1, y1, w, hi, lo, ar=1.0, a=0.8):
    """A recessed panel's lit/shadowed lip.  `w` is a length in tile-Y units."""
    wx = w / ar
    _rect(buf, t, x0, y0, x1, y0 + w, lo, a)
    _rect(buf, t, x0, y0, x0 + wx, y1, lo, a)
    _rect(buf, t, x0, y1 - w, x1, y1, hi, a * 0.8)
    _rect(buf, t, x1 - wx, y0, x1, y1, hi, a * 0.8)


def _screws(buf, t, pts, r, ar, col=(150.0, 154.0, 162.0), a=0.8):
    for (x, y) in pts:
        _ellipse(buf, t, x, y, r, (28.0, 28.0, 34.0), ar, a)
        _ellipse(buf, t, x, y, r * 0.68, col, ar, a)
        _seg(buf, t, (x - r * 0.5 / ar, y - r * 0.3),
             (x + r * 0.5 / ar, y + r * 0.3), r * 0.30, (40.0, 40.0, 48.0),
             ar, a)


# ================================================================= STAR WARS
# EAST_RUN[0], the free-standing angled cabinet at the NE corner.
#
# EVIDENCE.  docs/photos-jpg/Arcade Room v4 9.jpg px (150,220)-(300,480) and
# v4 8 px (0,90)-(140,340) -- crops at 6x in art/ref_g3/sw_v49.png and
# sw_v48.png.  Both show the WEST FLANK almost square-on and nothing else: a
# bright yellow carcase, a large black art panel inset into it cut to a stepped
# silhouette (rounded top-front shoulder, a hard step at the control-panel
# notch, running to the floor), and inside that panel a white-line starfield,
# two TIE fighters upper, a dark blue Vader helmet centre-left, the pale
# blue-grey limb of the Death Star curving across the lower third, an X-wing in
# three-quarter view low and forward with a smaller ship behind it, and a small
# rectangular inset panel at the lower rear.  The blue strip along the lower
# front edge is an LED the owner stuck on -- a fixture, not printed art, and it
# is NOT drawn here.
#
# The MARQUEE, FRONT and DECK appear in no photograph: in both frames the head
# is cropped or turned away and the front faces the corner.  Nothing is
# invented for them.  What they carry is the carcase colour that IS
# photographed, the black art-panel language that IS photographed, and honest
# cabinet hardware.  See NOTES.
SW_YEL = _hx("#e4d038")
SW_YEL_H = _hx("#f8e86a")
SW_YEL_D = _hx("#97881a")
SW_BLK = _hx("#0d0b14")
SW_KEY = _hx("#8d95a8")
SW_STL = _hx("#9db2c8")
SW_STL_D = _hx("#4a5c74")
SW_WHT = _hx("#eef2fa")
SW_VDR = _hx("#212f47")

# the stepped art panel, in side-tile coords (u = 0 back, u = 1 front, v = 0 top)
SW_PANEL = [(0.052, 0.132), (0.150, 0.108), (0.300, 0.093), (0.440, 0.098),
            (0.520, 0.126), (0.560, 0.186), (0.578, 0.268), (0.596, 0.352),
            (0.614, 0.428), (0.640, 0.462), (0.640, 0.580), (0.712, 0.610),
            (0.734, 0.660), (0.734, 0.962), (0.052, 0.972)]


def _sw_tie(b, t, cx, cy, s, col, w, ar, a=1.0):
    """A TIE fighter: ball cockpit, two tall hexagonal wing panels, struts."""
    for sgn in (-1.0, 1.0):
        wx = cx + sgn * s * 1.02 / ar
        hexp = [(wx - s * 0.46 / ar, cy - s * 0.44),
                (wx, cy - s * 0.90),
                (wx + s * 0.46 / ar, cy - s * 0.44),
                (wx + s * 0.46 / ar, cy + s * 0.44),
                (wx, cy + s * 0.90),
                (wx - s * 0.46 / ar, cy + s * 0.44)]
        _fill_poly(b, t, hexp, _mix(col, (0.0, 0.0, 0.0), 0.72), a * 0.85)
        _poly_line(b, t, hexp, w, col, ar, a, close=True)
        _seg(b, t, (wx, cy - s * 0.78), (wx, cy + s * 0.78), w * 0.7, col,
             ar, a * 0.7)
        _seg(b, t, (cx + sgn * s * 0.30 / ar, cy),
             (wx - sgn * s * 0.42 / ar, cy), w * 1.5, col, ar, a)
    _ellipse(b, t, cx, cy, s * 0.34, _mix(col, (0.0, 0.0, 0.0), 0.55), ar, a)
    _ellipse(b, t, cx, cy, s * 0.34, col, ar, a, r_in=s * 0.34 - w * 1.3)
    _ellipse(b, t, cx, cy, s * 0.16, col, ar, a * 0.8, r_in=s * 0.16 - w)


def _sw_xwing(b, t, cx, cy, s, ar, a=1.0):
    """An X-wing in three-quarter view: four splayed wings, cannons, canopy."""
    body = [(cx + s * 1.15 / ar, cy + s * 0.02),
            (cx + s * 0.55 / ar, cy - s * 0.22),
            (cx - s * 0.95 / ar, cy - s * 0.26),
            (cx - s * 1.10 / ar, cy + s * 0.08),
            (cx - s * 0.90 / ar, cy + s * 0.30),
            (cx + s * 0.50 / ar, cy + s * 0.26)]
    for (dx, dyw, ln) in ((-0.15, -0.98, 1.15), (-0.15, 0.96, 1.15),
                          (-0.55, -0.66, 0.95), (-0.55, 0.64, 0.95)):
        tipx = cx + (dx - ln * 0.86) * s / ar
        tipy = cy + dyw * s
        wing = [(cx + dx * s / ar, cy + dyw * s * 0.10),
                (cx + (dx - 0.10) * s / ar, cy + dyw * s * 0.14),
                (tipx, tipy), (tipx + s * 0.20 / ar, tipy)]
        _fill_poly(b, t, wing, SW_STL_D, a * 0.95)
        _poly_line(b, t, wing, 0.0034, SW_STL, ar, a, close=True)
        _seg(b, t, (tipx + s * 0.05 / ar, tipy),
             (tipx - s * 0.34 / ar, tipy + dyw * s * 0.10), 0.0042,
             _mix(SW_STL, SW_WHT, 0.4), ar, a)           # laser cannon
    _fill_poly(b, t, body, SW_STL, a)
    _poly_line(b, t, body, 0.0036, SW_WHT, ar, a * 0.9, close=True)
    _fill_poly(b, t, [(cx + s * 0.34 / ar, cy - s * 0.20),
                      (cx - s * 0.10 / ar, cy - s * 0.22),
                      (cx - s * 0.16 / ar, cy - s * 0.02),
                      (cx + s * 0.36 / ar, cy - s * 0.02)], SW_WHT, a * 0.9)
    _seg(b, t, (cx - s * 0.98 / ar, cy - s * 0.08),
         (cx - s * 1.28 / ar, cy - s * 0.02), s * 0.22, _hx("#c8d8ea"), ar,
         a * 0.75)                                        # engine glow


def _sw_vader(b, t, cx, cy, s, ar, a=1.0):
    """Vader's helmet.  Printed dark blue on black in v4 8 -- deliberately low
    contrast in the photograph, so it is drawn low contrast here and NOT lifted
    to read like a poster."""
    hel = [(cx - 0.06 * s / ar, cy - 1.00 * s),
           (cx + 0.36 * s / ar, cy - 0.88 * s),
           (cx + 0.60 * s / ar, cy - 0.52 * s),
           (cx + 0.66 * s / ar, cy - 0.06 * s),
           (cx + 0.82 * s / ar, cy + 0.34 * s),
           (cx + 0.74 * s / ar, cy + 0.74 * s),
           (cx + 0.44 * s / ar, cy + 1.02 * s),
           (cx - 0.34 * s / ar, cy + 1.04 * s),
           (cx - 0.64 * s / ar, cy + 0.70 * s),
           (cx - 0.76 * s / ar, cy + 0.22 * s),
           (cx - 0.66 * s / ar, cy - 0.34 * s),
           (cx - 0.42 * s / ar, cy - 0.80 * s)]
    _fill_poly(b, t, hel, SW_VDR, a)
    _poly_line(b, t, hel, 0.0044, _hx("#4a6084"), ar, a * 0.72, close=True)
    face = [(cx - 0.30 * s / ar, cy - 0.34 * s),
            (cx + 0.30 * s / ar, cy - 0.34 * s),
            (cx + 0.36 * s / ar, cy + 0.30 * s),
            (cx + 0.10 * s / ar, cy + 0.70 * s),
            (cx - 0.16 * s / ar, cy + 0.70 * s),
            (cx - 0.38 * s / ar, cy + 0.28 * s)]
    _fill_poly(b, t, face, _hx("#16203a"), a)
    for sgn in (-1.0, 1.0):                               # the eye lenses
        _fill_poly(b, t, [(cx + sgn * 0.06 * s / ar, cy - 0.18 * s),
                          (cx + sgn * 0.30 * s / ar, cy - 0.24 * s),
                          (cx + sgn * 0.32 * s / ar, cy + 0.02 * s),
                          (cx + sgn * 0.08 * s / ar, cy + 0.02 * s)],
                   _hx("#334a70"), a * 0.9)
    for k in range(4):                                    # mouth grille
        yy = cy + 0.26 * s + k * 0.10 * s
        _seg(b, t, (cx - 0.20 * s / ar, yy), (cx + 0.20 * s / ar, yy),
             0.0040, _hx("#3c5478"), ar, a * 0.65)
    _seg(b, t, (cx - 0.30 * s / ar, cy - 0.72 * s),
         (cx + 0.22 * s / ar, cy - 0.90 * s), 0.010, _hx("#54709c"), ar,
         a * 0.45)                                        # dome highlight


def sw_marquee(px, ox, oy, t):
    """NOT VISIBLE in any photograph: in both frames the head is cropped or
    turned away, and it does not read as lit.  Built dark and generic ON
    PURPOSE with the carcase's yellow retainer returns -- no Atari marquee is
    invented.  KEPT from round 4: the marquees were the half that worked."""
    b = _new(t, _hx("#181722"))
    _vgrad(b, t, 0.0, 1.0, _hx("#23222f"), _hx("#0e0d14"))
    # no _sheen: MEASURED 0.86 KB of PNG on a panel that is deliberately
    # blank, which is the single most expensive byte-per-pixel thing in
    # this module.  The ordered dither alone carries it.
    _rect(b, t, 0.0, 0.0, 1.0, 0.072, _hx("#30301c"))
    _rect(b, t, 0.0, 0.930, 1.0, 1.0, _hx("#141320"))
    _rect(b, t, 0.0, 0.0, 0.030, 1.0, SW_YEL_D, 0.9)
    _rect(b, t, 0.970, 0.0, 1.0, 1.0, SW_YEL_D, 0.9)
    _rect(b, t, 0.030, 0.072, 0.048, 0.930, _hx("#0b0a10"), 0.7)
    _rect(b, t, 0.952, 0.072, 0.970, 0.930, _hx("#0b0a10"), 0.7)
    _band(b, t, 2.4, 9.0, 1.1)
    _flush(px, ox, oy, b, t)


def sw_side(px, ox, oy, t):
    """THE identifying surface, and the one the photographs give in full."""
    ar = PANEL_AR["star-wars-atari.side"]
    b = _new(t, SW_YEL)
    _vgrad(b, t, 0.0, 1.0, SW_YEL_H, _hx("#b8a422"))
    _hgrad(b, t, 0.62, 1.00, SW_YEL, SW_YEL_H, 0.0, 1.0, 0.45)
    _sheen(b, t, 0.0, 0.0, 1.0, 1.0, 17.0, 41, 5)
    _rect(b, t, 0.0, 0.0, 0.024, 1.0, SW_YEL_D, 0.85)     # T-molding returns
    _rect(b, t, 0.0, 0.0, 1.0, 0.011, SW_YEL_D, 0.8)
    _rect(b, t, 0.0, 0.986, 1.0, 1.0, _hx("#5e5410"), 0.9)

    # the black art panel, cut to the machine's own stepped silhouette
    _fill_poly(b, t, [(p[0] + 0.007, p[1] + 0.004) for p in SW_PANEL],
               _hx("#63590f"), 0.6)                       # printed drop shadow
    _fill_poly(b, t, SW_PANEL, SW_BLK)
    _poly_line(b, t, SW_PANEL, 0.0034, SW_KEY, ar, 0.8, close=True)
    _vgrad(b, t, 0.10, 0.62, _hx("#1b1830"), _hx("#08070e"), 0.06, 0.72, 0.55)

    _stars(b, t, SW_PANEL, 104, 91, ar)

    # two TIE fighters across the upper half, and a distant third
    _sw_tie(b, t, 0.222, 0.204, 0.062, SW_WHT, 0.0044, ar)
    _sw_tie(b, t, 0.452, 0.158, 0.046, _hx("#d2d8e6"), 0.0036, ar, 0.92)
    _sw_tie(b, t, 0.336, 0.286, 0.023, _hx("#9aa2b4"), 0.0026, ar, 0.75)

    _sw_vader(b, t, 0.248, 0.432, 0.128, ar)

    # the Death Star limb curving across the lower third
    dsu, dsv, dsr = 0.372, 1.176, 0.392
    limb = _ellp(dsu, dsv, dsr, dsr, ar, 40, math.pi * 1.02, math.pi * 1.98)
    _fill_poly(b, t, limb + [(limb[-1][0], 1.06), (limb[0][0], 1.06)],
               _hx("#243448"), 0.94)
    for j in range(4):
        k = j / 3.0
        rr = dsr - 0.036 - k * 0.078
        _arc(b, t, dsu, dsv, rr, math.pi * (1.06 + k * 0.05),
             math.pi * (1.94 - k * 0.05), 0.0052,
             _mix(_hx("#3e546e"), _hx("#7e94ae"), 1.0 - k), ar, 0.75)
    _arc(b, t, dsu, dsv, dsr, math.pi * 1.02, math.pi * 1.98, 0.0046,
         _hx("#a8bccf"), ar, 0.95)
    for j in range(13):
        aa = math.pi * (1.05 + 0.0742 * j)
        _seg(b, t, (dsu + dsr * math.cos(aa) / ar, dsv + dsr * math.sin(aa)),
             (dsu + (dsr - 0.112) * math.cos(aa) / ar,
              dsv + (dsr - 0.112) * math.sin(aa)), 0.0032, _hx("#647a92"),
             ar, 0.6)
    _arc(b, t, 0.212, 1.044, 0.114, math.pi * 1.10, math.pi * 1.90, 0.0040,
         _hx("#90a6bd"), ar, 0.85)                        # the trench notch

    _sw_xwing(b, t, 0.452, 0.640, 0.104, ar)
    _sw_xwing(b, t, 0.236, 0.756, 0.050, ar, 0.85)

    # the small rectangular inset panel at the lower rear
    _rect(b, t, 0.098, 0.790, 0.272, 0.888, _hx("#7f8798"), 0.9)
    _rect(b, t, 0.108, 0.798, 0.262, 0.880, _hx("#141824"))
    _arc(b, t, 0.186, 0.888, 0.080, math.pi * 1.14, math.pi * 1.86, 0.0036,
         _hx("#6d7f95"), ar, 0.9)
    _ellipse(b, t, 0.152, 0.828, 0.016, _hx("#c8d6e6"), ar, 0.8)
    _seg(b, t, (0.122, 0.860), (0.248, 0.856), 0.0030, _hx("#54617a"), ar, 0.8)
    _band(b, t, 2.6, 15.0, 0.7)
    _flush(px, ox, oy, b, t)


def sw_front(px, ox, oy, t):
    """NOT VISIBLE in any photograph -- the front faces the corner in both
    frames that show this machine.  So nothing is invented: the panel carries
    the carcase colour the photographs DO give (bright yellow, full bleed, edge
    to edge, deck to floor), a black inset panel in the same printed language as
    the flank's art panel (starfield, Death Star limb, one TIE, one small
    X-wing -- every one of those is photographed ON THIS MACHINE'S FLANK; no
    character portrait, no wordmark, no Atari logo), and honest
    hardware: a two-slot steel coin door set LEFT of centre with its coin-return
    cup below it, and a service plate to its right.  Round 4's version of this
    panel was a flat black field with a grey box in the middle of it, which is
    the thing three critics rejected the round for."""
    ar = PANEL_AR["star-wars-atari.front"]
    b = _new(t, SW_YEL)
    _vgrad(b, t, 0.0, 1.0, SW_YEL_H, _hx("#b09c1e"))
    _sheen(b, t, 0.0, 0.0, 1.0, 1.0, 15.0, 23, 4)
    _rect(b, t, 0.0, 0.0, 0.042, 1.0, SW_YEL_D, 0.9)      # yellow edge returns
    _rect(b, t, 0.958, 0.0, 1.0, 1.0, SW_YEL_D, 0.9)
    _rect(b, t, 0.0, 0.972, 1.0, 1.0, _hx("#4e4610"))     # kick line

    # the black inset panel
    pan = [(0.088, 0.048), (0.912, 0.040), (0.926, 0.276), (0.912, 0.504),
           (0.088, 0.512), (0.074, 0.276)]
    _fill_poly(b, t, [(p[0] + 0.006, p[1] + 0.008) for p in pan],
               _hx("#5e5410"), 0.65)
    _fill_poly(b, t, pan, SW_BLK)
    _poly_line(b, t, pan, 0.0060, SW_KEY, ar, 0.75, close=True)
    _vgrad(b, t, 0.05, 0.28, _hx("#1b1830"), _hx("#08070e"), 0.09, 0.91, 0.6)
    _stars(b, t, pan, 44, 313, ar, big=4)
    # the limb is clipped to the inset: its chord sits ON the panel's bottom
    # edge so no part of it spills onto the yellow carcase
    dsu, dsv, dsr = 0.430, 0.494, 0.238
    limb = _ellp(dsu, dsv, dsr, dsr, ar, 36, math.pi * 1.03, math.pi * 1.97)
    _fill_poly(b, t, limb + [(limb[-1][0], 0.506), (limb[0][0], 0.506)],
               _hx("#1c2839"), 0.95)
    _arc(b, t, dsu, dsv, dsr, math.pi * 1.06, math.pi * 1.94, 0.0055,
         _hx("#93a7bc"), ar, 0.85)
    for j in range(2):
        _arc(b, t, dsu, dsv, dsr - 0.060 - j * 0.078,
             math.pi * (1.12 + j * 0.06), math.pi * (1.88 - j * 0.06), 0.0045,
             _mix(_hx("#34485e"), _hx("#6f849c"), 1.0 - j), ar, 0.7)
    for j in range(5):
        aa = math.pi * (1.14 + 0.180 * j)
        _seg(b, t, (dsu + dsr * math.cos(aa) / ar, dsv + dsr * math.sin(aa)),
             (dsu + (dsr - 0.110) * math.cos(aa) / ar,
              dsv + (dsr - 0.110) * math.sin(aa)), 0.0038, _hx("#4c6076"),
             ar, 0.55)
    _sw_tie(b, t, 0.790, 0.156, 0.050, _hx("#d0d8e6"), 0.0060, ar, 0.9)
    _sw_xwing(b, t, 0.246, 0.352, 0.052, ar, 0.9)

    # the coin door -- a black steel door LEFT of centre, chrome bezel, two
    # coin mechs, its lock and its return cup
    _rect(b, t, 0.140, 0.578, 0.560, 0.884, _hx("#c2c6cc"))     # chrome bezel
    _rect(b, t, 0.156, 0.594, 0.544, 0.868, _hx("#141519"))     # the door
    _vgrad(b, t, 0.596, 0.866, _hx("#1e1f25"), _hx("#0c0d11"), 0.158, 0.542)
    for k in range(2):                                    # two coin mechs
        xx = 0.196 + k * 0.156
        _rect(b, t, xx, 0.616, xx + 0.104, 0.788, _hx("#d2d6dc"))
        _rect(b, t, xx + 0.012, 0.630, xx + 0.092, 0.774, _hx("#7e838c"))
        _rect(b, t, xx + 0.038, 0.644, xx + 0.066, 0.742, _hx("#050506"))
        _seg(b, t, (xx + 0.014, 0.762), (xx + 0.090, 0.762), 0.010,
             _hx("#e6eaee"), ar, 0.8)
    _ellipse(b, t, 0.496, 0.730, 0.034, _hx("#d2d6dc"), ar)     # lock
    _ellipse(b, t, 0.496, 0.730, 0.015, _hx("#101014"), ar)
    _rect(b, t, 0.196, 0.898, 0.430, 0.978, _hx("#c2c6cc"))     # return cup
    _rect(b, t, 0.210, 0.914, 0.416, 0.968, _hx("#08080a"))
    _rect(b, t, 0.210, 0.914, 0.416, 0.928, _hx("#6c7078"), 0.85)

    # service plate to the right of the door
    _rect(b, t, 0.650, 0.612, 0.918, 0.820, _hx("#1a1a20"))
    _bevel(b, t, 0.650, 0.612, 0.918, 0.820, 0.012, _hx("#6c6e76"),
           _hx("#26262c"), ar, 0.85)
    _fineprint(b, t, 0.676, 0.896, 0.640, 0.034, 4, _hx("#9a9ca4"), ar, 5, 0.8)
    _screws(b, t, [(0.674, 0.638), (0.894, 0.638), (0.674, 0.794),
                   (0.894, 0.794)], 0.012, ar)
    _band(b, t, 2.2, 12.0, 1.9)
    _flush(px, ox, oy, b, t)


def sw_deck(px, ox, oy, t):
    """NOT VISIBLE in any photograph.  Built as the hardware the machine must
    have and nothing more: a charcoal deck with the carcase's yellow leading
    return along the player edge, the chrome escutcheon plate a yoke column
    comes out of (the yoke ITSELF is geometry -- see DECKS), the shadow that
    yoke casts on the plate, and two pale instruction decals.  No legend is
    printed, because none is legible anywhere.  Authored ~2x for a2kit's
    ART_DK deck material."""
    ar = PANEL_AR["star-wars-atari.deck"]
    b = _new(t, _hx("#4a4852"))
    _vgrad(b, t, 0.0, 1.0, _hx("#3a3841"), _hx("#57555f"))
    _brush(b, t, 0.06, 0.94, 33, 11.0, 0.012)
    _rect(b, t, 0.0, 0.0, 1.0, 0.062, _hx("#2a2830"))
    # the yoke plate
    _rect(b, t, 0.292, 0.150, 0.708, 0.868, _hx("#26252c"))
    _bevel(b, t, 0.292, 0.150, 0.708, 0.868, 0.016, _hx("#6e6c76"),
           _hx("#1a191f"), ar, 0.85)
    _ellipse(b, t, 0.500, 0.512, 0.330, _hx("#141319"), ar, 0.35)  # yoke shadow
    _ellipse(b, t, 0.500, 0.512, 0.196, _hx("#b8bcc4"), ar)        # escutcheon
    _ellipse(b, t, 0.500, 0.512, 0.152, _hx("#7c8088"), ar)
    _ellipse(b, t, 0.500, 0.512, 0.108, _hx("#1c1b21"), ar)
    _screws(b, t, [(0.500, 0.238), (0.500, 0.786), (0.336, 0.512),
                   (0.664, 0.512)], 0.020, ar)
    for xx in (0.040, 0.772):                             # instruction decals
        _rect(b, t, xx, 0.256, xx + 0.188, 0.700, _hx("#b0aca0"))
        _rect(b, t, xx + 0.010, 0.276, xx + 0.178, 0.680, _hx("#d6d2c6"))
        _fineprint(b, t, xx + 0.024, xx + 0.164, 0.300, 0.062, 5,
                   _hx("#3c3a34"), ar, 7, 0.8)
    _rect(b, t, 0.0, 0.858, 1.0, 0.886, _hx("#201f26"))
    _vgrad(b, t, 0.886, 1.0, _hx("#d0c23c"), _hx("#8a7f18"))   # yellow return
    _flush(px, ox, oy, b, t)


# ================================================================ RIDGE RACER
# The SW-corner Namco DRIVING cabinet -- the only wheel machine in the room.
#
# EVIDENCE.  docs/photos-jpg/Arcade Room v4 8.jpg px (490,105)-(610,250) at 8x
# (art/ref_g3/rr_v48.png) is the frame that settles this machine, and it shows
# TWO of them side by side.  Reading down one cabinet: a YELLOW marquee band
# with two lines of dark type (the type does not resolve -- the band blows out);
# a black bezel; a DARK, OFF screen -- grey-blue with a hard specular of a
# ceiling can on the right-hand cabinet, no attract loop, nothing lit; a black
# control deck with a large round steering wheel mounted centrally, dark rim
# and a pale olive centre boss with three spokes, a small pale button cluster
# to its LEFT and two round white illuminated buttons to its RIGHT; below the
# deck one large BLACK RECESSED PANEL filling most of the front; and under that
# the deep maroon base carrying 'RIDGE RAC[ER]' in white italic caps (read
# directly at 16x in v3 4 px (1130,795)-(1200,850), art/ref_g3/rr_v34.png) with
# a black recessed coin/service area low and left.
#
# The FLANK is not visible in any frame, so no graphic is invented on it: it is
# the body colour edge to edge plus the hardware a driving cabinet has -- a
# louvred vent, a service door, the deck's black return, the base seam.
RR_RED = _hx("#a8232e")
RR_RED_H = _hx("#c8404a")
RR_RED_D = _hx("#68131b")
RR_YEL = _hx("#e8d24e")
RR_INK = _hx("#241a10")
RR_BLK = _hx("#0e0e12")
RR_SIL = _hx("#e2e6ea")


def rr_marquee(px, ox, oy, t):
    """Yellow band, two lines of dark type.  The band COLOUR is read straight
    off v4 5 / v4 8; the LETTERING is reconstructed from the wordmark on the
    lower front (rr_v34.png, 'RIDGE RAC' at 16x) because the marquee itself
    blows out in every frame that shows it.  KEPT from round 4."""
    ar = PANEL_AR["ridge-racer.marquee"]
    b = _new(t, RR_YEL)
    _vgrad(b, t, 0.0, 1.0, _hx("#f4e78c"), _hx("#cdb032"))
    _hgrad(b, t, 0.0, 0.35, _hx("#fdf6c0"), RR_YEL, 0.10, 0.90, 0.5)
    _rect(b, t, 0.0, 0.0, 1.0, 0.075, RR_RED)
    _rect(b, t, 0.0, 0.925, 1.0, 1.0, _hx("#6e1218"))
    text(b, t, "NAMCO", 0.0, 0.360, 0.155, RR_INK, ar,
         box=(0.400, 0.600), weight=0.20, slant=0.10)
    text(b, t, "RIDGE RACER", 0.0, 0.845, 0.400, RR_INK, ar,
         box=(0.085, 0.915), weight=0.20, slant=0.22, track=0.13)
    _rect(b, t, 0.09, 0.878, 0.91, 0.898, RR_RED, 0.75)
    _flush(px, ox, oy, b, t)


def rr_side(px, ox, oy, t):
    """Two-tone, and the split is structural rather than invented.  v4 5 px
    (270,120)-(360,240) at 10x (art/ref_g3/rr_v45b.png) is the only frame that
    gets round the front of this machine, and it shows the flank as a BRIGHT
    RED body from the floor up to the control deck, a BLACK monitor housing
    above it carrying the screen and the marquee, a red T-molding edge running
    up the back of that housing, and a pale red band along the base at the
    floor.  Round 4 shipped this panel as a flat red field with a black slab
    across the bottom -- the two-tone is the other way up, and the difference
    is the whole silhouette of the machine.  No graphic is printed on it,
    because none is visible in any frame; the detail is hardware -- the deck
    return, the base seam, a louvred vent, a bolted service door, the plinth.
    Packed at only 64 px (atlas4 SIZE['side']), so everything here is drawn at
    a scale that survives it."""
    ar = PANEL_AR["ridge-racer.side"]
    b = _new(t, RR_RED)
    _vgrad(b, t, 0.0, 1.0, RR_RED_H, _hx("#8c1c26"))
    # (no _sheen here: measured 0.4 KB for drift invisible under the
    # two-tone split -- see the payload note in the report)

    # ---- the BLACK monitor housing, everything above the control deck
    _rect(b, t, 0.0, 0.0, 0.700, 0.586, _hx("#141418"))
    _vgrad(b, t, 0.0, 0.586, _hx("#1e1e24"), _hx("#0c0c10"), 0.0, 0.700)
    _rect(b, t, 0.0, 0.0, 0.088, 0.600, RR_RED_H, 0.95)   # red molding up the
    _rect(b, t, 0.0, 0.0, 0.700, 0.028, RR_RED_H, 0.92)   # back and over the top
    _rect(b, t, 0.084, 0.026, 0.104, 0.590, _hx("#5c0f16"), 0.7)
    _seg(b, t, (0.104, 0.150), (0.620, 0.176), 0.008, _hx("#4a4a54"), ar, 0.55)
    # the same red molding returns down the FRONT edge of the housing, which is
    # the red curve v4 5 shows running up past the screen face
    _rect(b, t, 0.624, 0.026, 0.700, 0.586, RR_RED_H, 0.95)
    _rect(b, t, 0.604, 0.026, 0.624, 0.586, _hx("#5c0f16"), 0.7)

    # ---- the black control-deck return, standing proud of the carcase
    _rect(b, t, 0.0, 0.586, 1.0, 0.680, _hx("#101014"))
    _rect(b, t, 0.0, 0.586, 1.0, 0.600, _hx("#54545e"), 0.7)

    # ---- the red body below the deck, carried to the floor
    _vgrad(b, t, 0.680, 1.0, _hx("#b82832"), _hx("#7c1620"), 0.0, 0.955)
    _hgrad(b, t, 0.50, 0.955, RR_RED, _hx("#d2505a"), 0.690, 0.950, 0.45)
    _rect(b, t, 0.0, 0.680, 0.955, 0.694, _hx("#5c1017"))
    _rect(b, t, 0.0, 0.694, 0.955, 0.702, _hx("#e0aaae"), 0.40)
    _rect(b, t, 0.955, 0.680, 1.0, 1.0, _hx("#17171c"), 0.9)   # front molding
    # louvred cooling vent, low at the back
    _rect(b, t, 0.058, 0.756, 0.318, 0.908, _hx("#141419"))
    _bevel(b, t, 0.058, 0.756, 0.318, 0.908, 0.010, _hx("#e0a4aa"),
           _hx("#3c0d12"), ar, 0.7)
    for k in range(6):
        yy = 0.772 + k * 0.022
        _seg(b, t, (0.074, yy), (0.302, yy), 0.0075, _hx("#74747e"), ar, 0.6)
    # bolted service door
    _rect(b, t, 0.372, 0.744, 0.688, 0.932, _hx("#8e1c26"), 0.55)
    _poly_line(b, t, [(0.372, 0.744), (0.688, 0.744), (0.688, 0.932),
                      (0.372, 0.932)], 0.0070, _hx("#e2b0b4"), ar, 0.50,
               close=True)
    _ellipse(b, t, 0.650, 0.838, 0.022, _hx("#1a1a20"), ar, 0.9)
    _ellipse(b, t, 0.650, 0.838, 0.013, _hx("#c2c6cc"), ar, 0.9)
    _screws(b, t, [(0.394, 0.760), (0.666, 0.760), (0.394, 0.916),
                   (0.666, 0.916)], 0.012, ar, a=0.65)
    # the pale band along the base and the black plinth under it
    _rect(b, t, 0.0, 0.940, 0.955, 0.958, _hx("#e8949c"), 0.65)
    _rect(b, t, 0.0, 0.958, 1.0, 1.0, _hx("#121216"))
    _flush(px, ox, oy, b, t)


def rr_front(px, ox, oy, t):
    """The lower front, read straight off rr_v48 / rr_v34: a big black RECESSED
    panel filling the upper two thirds, framed all round by the red body, then
    the maroon base with a silver speed flash sweeping in from the left,
    'RIDGE RACER' in white italic caps, and the black recessed coin / service
    area LOW AND LEFT -- not a grey plate in the middle."""
    ar = PANEL_AR["ridge-racer.front"]
    b = _new(t, RR_RED)
    _vgrad(b, t, 0.0, 1.0, _hx("#b02a34"), _hx("#78161f"))
    _sheen(b, t, 0.0, 0.0, 1.0, 1.0, 13.0, 34, 4)
    _rect(b, t, 0.0, 0.0, 0.030, 1.0, _hx("#5c1017"), 0.8)
    _rect(b, t, 0.970, 0.0, 1.0, 1.0, _hx("#5c1017"), 0.8)

    # the black recessed panel
    _rect(b, t, 0.058, 0.040, 0.942, 0.616, RR_BLK)
    _bevel(b, t, 0.058, 0.040, 0.942, 0.616, 0.020, _hx("#d8949a"),
           _hx("#3a0c11"), ar, 0.85)
    _vgrad(b, t, 0.056, 0.612, _hx("#191920"), _hx("#08080b"), 0.076, 0.926)
    _fill_poly(b, t, [(0.100, 0.590), (0.360, 0.075), (0.470, 0.075),
                      (0.210, 0.590)], _hx("#4a4c58"), 0.16)   # glass reflection
    _fill_poly(b, t, [(0.520, 0.590), (0.700, 0.075), (0.744, 0.075),
                      (0.564, 0.590)], _hx("#4a4c58"), 0.10)
    _screws(b, t, [(0.092, 0.070), (0.908, 0.070), (0.092, 0.586),
                   (0.908, 0.586)], 0.013, ar, a=0.7)
    _rect(b, t, 0.058, 0.622, 0.942, 0.636, _hx("#e0b0b4"), 0.45)

    # the silver speed flash, and the wordmark
    _fill_poly(b, t, [(0.000, 0.760), (0.246, 0.694), (0.300, 0.716),
                      (0.052, 0.786)], RR_SIL, 0.92)
    _fill_poly(b, t, [(0.000, 0.822), (0.196, 0.766), (0.232, 0.782),
                      (0.036, 0.840)], _hx("#f0d24e"), 0.75)
    _fill_poly(b, t, [(0.000, 0.712), (0.166, 0.664), (0.190, 0.674),
                      (0.024, 0.722)], _hx("#f6f8fa"), 0.55)
    text(b, t, "RIDGE RACER", 0.0, 0.812, 0.128, _hx("#f6f6f2"), ar,
         box=(0.318, 0.944), weight=0.185, slant=0.28, track=0.11)

    # the recessed coin / service area, LOW AND LEFT
    _rect(b, t, 0.052, 0.856, 0.472, 0.986, _hx("#08080b"))
    _bevel(b, t, 0.052, 0.856, 0.472, 0.986, 0.014, _hx("#c8888e"),
           _hx("#340a0f"), ar, 0.8)
    _rect(b, t, 0.072, 0.874, 0.286, 0.968, _hx("#aeb2ba"))     # chrome plate
    _rect(b, t, 0.082, 0.884, 0.276, 0.958, _hx("#7a7e86"))
    for k in range(2):
        xx = 0.108 + k * 0.086
        _rect(b, t, xx, 0.896, xx + 0.030, 0.946, _hx("#08080a"))
    _rect(b, t, 0.312, 0.884, 0.452, 0.966, _hx("#0a0a0c"))     # return cup
    _rect(b, t, 0.312, 0.884, 0.452, 0.898, _hx("#5e626a"), 0.8)
    # a small black service square at the far right of the base
    _rect(b, t, 0.812, 0.874, 0.944, 0.968, _hx("#141419"))
    _bevel(b, t, 0.812, 0.874, 0.944, 0.968, 0.010, _hx("#c8888e"),
           _hx("#340a0f"), ar, 0.7)
    _ellipse(b, t, 0.878, 0.920, 0.020, _hx("#b8bcc4"), ar, 0.9)
    _band(b, t, 2.6, 12.0, 3.1)
    _flush(px, ox, oy, b, t)


def rr_deck(px, ox, oy, t):
    """The driving deck.  The WHEEL, its buttons and the two illuminated round
    buttons are GEOMETRY -- see DECKS['ridge-racer'] -- so what is printed here
    is the surface they sit on: brushed black steel, the chrome escutcheon the
    wheel column comes out of, the soft shadow the rim casts on it, a pale
    instruction decal on the left, a black button plate with its legends on the
    right, and Namco's red leading return along the player edge.  There are NO
    joysticks on this machine; suppress upright()'s default pair.
    Authored ~2x for a2kit's ART_DK deck material."""
    ar = PANEL_AR["ridge-racer.deck"]
    b = _new(t, _hx("#3c3d46"))
    _vgrad(b, t, 0.0, 1.0, _hx("#2e2f37"), _hx("#46474f"))
    _brush(b, t, 0.05, 0.92, 55, 12.0, 0.011)
    _rect(b, t, 0.0, 0.0, 1.0, 0.070, _hx("#232430"))
    # the wheel escutcheon and the shadow the rim casts
    _ellipse(b, t, 0.468, 0.500, 0.430, _hx("#15161b"), ar, 0.30)
    _ellipse(b, t, 0.468, 0.500, 0.336, _hx("#15161b"), ar, 0.22)
    _ellipse(b, t, 0.468, 0.500, 0.212, _hx("#0f1014"), ar, 0.85)
    _ellipse(b, t, 0.468, 0.500, 0.186, _hx("#c6cad0"), ar)
    _ellipse(b, t, 0.468, 0.500, 0.150, _hx("#82868e"), ar)
    _ellipse(b, t, 0.468, 0.500, 0.104, _hx("#1e1f26"), ar)
    _screws(b, t, [(0.468, 0.322), (0.468, 0.678), (0.398, 0.500),
                   (0.538, 0.500)], 0.017, ar)
    # left: the pale instruction decal
    _rect(b, t, 0.028, 0.230, 0.210, 0.780, _hx("#9a9c9e"))
    _rect(b, t, 0.038, 0.252, 0.200, 0.758, _hx("#d2d4d6"))
    _rect(b, t, 0.038, 0.252, 0.200, 0.318, RR_RED_H)
    _fineprint(b, t, 0.052, 0.186, 0.348, 0.066, 5, _hx("#3a3a40"), ar, 11, 0.8)
    # right: the black button plate the two illuminated buttons stand on
    _rect(b, t, 0.762, 0.176, 0.972, 0.824, _hx("#1a1b21"))
    _bevel(b, t, 0.762, 0.176, 0.972, 0.824, 0.014, _hx("#7c7e86"),
           _hx("#101116"), ar, 0.8)
    for k in range(2):                                  # legend under each
        yy = 0.324 + k * 0.290
        _rect(b, t, 0.792, yy + 0.106, 0.912, yy + 0.126, _hx("#c6c8cc"), 0.85)
        _rect(b, t, 0.792, yy + 0.136, 0.866, yy + 0.150, _hx("#8e9096"), 0.7)
    _rect(b, t, 0.0, 0.900, 1.0, 0.918, _hx("#1a1b21"))
    _vgrad(b, t, 0.918, 1.0, _hx("#c02c38"), _hx("#7a1620"))   # red front lip
    _flush(px, ox, oy, b, t)


def rr_bezel(px, ox, oy, t):
    """A dark screen surround with the body's red return.  The SCREEN itself is
    ar2 geometry and stays DARK on purpose: in rr_v48 both Ridge Racer cabinets
    show an off monitor -- flat grey-blue with a ceiling-can specular on the
    right-hand one.  No attract loop is invented."""
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


# ====================================================== GRAFFITI MULTICADE
# NORTH_RUN[0], the westernmost machine on the north wall and the odd one out
# in that run: a real full-size upright with a stepped head and a much deeper
# body than the three slim Arcade1Up-proportioned machines beside it.
#
# EVIDENCE.  docs/photos-jpg/Arcade Room v3 1.jpg px (515,555)-(625,840) at 6x
# (art/ref_g3/n1_v31.png) is the frame that shows the whole machine, and v4 6
# px (222,110)-(295,290) at 10x (n1_v46.png) is the neutral exposure -- its
# floor meters #a4a39f, so its colours are the ones to trust; v3 1 reads BLUE
# only because the whole north wall is under a blue RGB wash there.
#
# What those two frames give: a full-bleed all-over vinyl wrap on a near-black
# ground in dense PALE GREY line work -- long sweeping curves, a large
# almond/lens-shaped ellipse low on the flank, a diagonal slash near the top,
# and a dense scatter of smaller light glyphs and marks over the whole panel.
# The same wrap continues down the FRONT to the floor, split by a horizontal
# seam at about mid height, with a large near-black recessed coin panel
# carrying ONE small white dot (the coin plunger) and a printed QR-code square
# low on the panel.  The deck is black, wide, and projects further than any of
# its neighbours, with two joystick/button clusters and no printed legend.
#
# NO TITLE RESOLVES ANYWHERE, at any magnification, in any frame -- three
# independent photo readings failed on it and so did mine.  Nothing here spells
# a game name, and the marquee is deliberately abstract.
N1_GND = _hx("#2c2f3a")
N1_GND_H = _hx("#3c404e")
N1_GND_D = _hx("#14161c")
N1_INK = _hx("#8e929c")
N1_HI = _hx("#d2d6de")
N1_HI2 = _hx("#eef0f4")
N1_MAR = _hx("#7d2029")


def _n1_lens(cu, cv, lw, lh, n=26):
    """The almond / lens outline that sits low on the flank -- the one large
    shape in the wrap, and the thing that makes this machine identifiable."""
    pts = []
    for j in range(n + 1):
        s = -1.0 + 2.0 * j / n
        pts.append((cu + s * lw, cv - (1.0 - s * s) * lh))
    for j in range(n + 1):
        s = 1.0 - 2.0 * j / n
        pts.append((cu + s * lw, cv + (1.0 - s * s) * lh))
    return pts


def _n1_tag(b, t, pts, w, col, ar, a=0.9):
    """One continuous tag stroke that never separates into letters."""
    for i in range(len(pts) - 1):
        k = i / float(max(1, len(pts) - 2))
        _seg(b, t, pts[i], pts[i + 1], w * (1.25 - 0.55 * k), col, ar, a)


def _n1_ground(b, t, seed, hi=N1_GND_H, lo=N1_GND_D):
    _vgrad(b, t, 0.0, 1.0, hi, lo)
    _sheen(b, t, 0.0, 0.0, 1.0, 1.0, 13.0, seed, 3)


def n1_marquee(px, ox, oy, t):
    """Dark, near-black ground.  In v3 1 it carries light silver-grey lettering
    across the centre, a small maroon patch below and left of centre, and a
    light angular mark at the right end that reads like a stylised wing.  In
    v4 6 the same marquee is swamped by a specular of a ceiling can and looks
    blank.  It does NOT read as lit.  So: pale abstract strokes that cross and
    share tails rather than standing apart as glyphs -- an earlier pass drew
    four separate letter-like marks and the marquee accidentally read 'RUNLS',
    and inventing a title is exactly what the evidence forbids.  KEPT from
    round 4."""
    ar = PANEL_AR["north-1-graffiti-multicade.marquee"]
    b = _new(t, _hx("#191b22"))
    _vgrad(b, t, 0.0, 1.0, _hx("#24262f"), _hx("#0f1118"))
    # no _sheen: MEASURED 0.81 KB for drift invisible under the tag
    # strokes.  See the payload note in the report.
    _rect(b, t, 0.0, 0.0, 1.0, 0.075, _hx("#0c0d12"))
    _rect(b, t, 0.0, 0.925, 1.0, 1.0, _hx("#0c0d12"))
    _seg(b, t, (0.0, 0.086), (1.0, 0.086), 0.010, _hx("#43464f"), ar, 0.6)
    _n1_tag(b, t, [(0.146, 0.548), (0.170, 0.318), (0.212, 0.512),
                   (0.244, 0.372), (0.258, 0.596), (0.316, 0.336),
                   (0.286, 0.478), (0.372, 0.436), (0.412, 0.310),
                   (0.408, 0.572), (0.466, 0.394), (0.500, 0.556),
                   (0.548, 0.330), (0.578, 0.520), (0.634, 0.386)],
            0.100, _hx("#a3a7b1"), ar, 0.92)
    _n1_tag(b, t, [(0.128, 0.452), (0.226, 0.604), (0.352, 0.352),
                   (0.454, 0.630), (0.556, 0.392), (0.656, 0.500)],
            0.050, _hx("#83878f"), ar, 0.78)
    _ellipse(b, t, 0.318, 0.470, 0.118, _hx("#93979f"), ar, 0.72, r_in=0.072)
    _ellipse(b, t, 0.520, 0.436, 0.088, _hx("#878b95"), ar, 0.62, r_in=0.050)
    _taper(b, t, (0.140, 0.640), (0.660, 0.596), 0.036, 0.016, _hx("#7f838d"),
           ar, 0.70)
    _taper(b, t, (0.176, 0.286), (0.612, 0.268), 0.028, 0.013, _hx("#9ba0aa"),
           ar, 0.50)
    _fill_poly(b, t, [(0.300, 0.672), (0.452, 0.658), (0.462, 0.766),
                      (0.306, 0.782)], N1_MAR)
    _poly_line(b, t, [(0.300, 0.672), (0.452, 0.658), (0.462, 0.766),
                      (0.306, 0.782)], 0.016, _hx("#b6555c"), ar, 0.6,
               close=True)
    _taper(b, t, (0.712, 0.300), (0.944, 0.512), 0.185, 0.030, _hx("#bcc0ca"),
           ar, 0.92)
    _taper(b, t, (0.744, 0.646), (0.952, 0.408), 0.120, 0.026, _hx("#9ba0aa"),
           ar, 0.88)
    _taper(b, t, (0.736, 0.352), (0.878, 0.470), 0.042, 0.018, _hx("#d4d8e0"),
           ar, 0.72)
    _glyphs(b, t, 0.06, 0.16, 0.96, 0.86, 20, 202, _hx("#4c505a"),
            _hx("#6a6e78"), ar, scale=0.8, a=0.7)
    _flush(px, ox, oy, b, t)


def n1_side(px, ox, oy, t):
    """THE identifying surface: the full-bleed line-art wrap, edge to edge and
    top to floor.  The ground is lifted from the photograph's #1a1c24-#3c3f48
    (a night frame under a blue RGB wash) to a neutral #2c2f3a, and the ink is
    authored at 190-235 so the WRAP reads as line work in the render rather
    than as a dark slab -- the ink is what identifies this machine."""
    ar = PANEL_AR["north-1-graffiti-multicade.side"]
    b = _new(t, N1_GND)
    _n1_ground(b, t, 33)
    _hgrad(b, t, 0.55, 1.00, N1_GND, _hx("#454956"), 0.0, 1.0, 0.40)

    # the long sweeping curves that organise the whole wrap
    _arc(b, t, 0.22, -0.30, 1.30, math.pi * 0.10, math.pi * 0.88, 0.017,
         N1_INK, ar, 0.85)
    _arc(b, t, 0.18, -0.26, 1.46, math.pi * 0.12, math.pi * 0.84, 0.009,
         N1_HI, ar, 0.60)
    _arc(b, t, 0.90, 0.34, 1.34, math.pi * 0.60, math.pi * 1.44, 0.015,
         N1_INK, ar, 0.80)
    _arc(b, t, 0.50, 1.36, 1.16, math.pi * 1.06, math.pi * 1.94, 0.014,
         N1_INK, ar, 0.75)
    _arc(b, t, -0.10, 0.62, 0.86, math.pi * 1.76, math.pi * 2.34, 0.011,
         N1_HI, ar, 0.45)

    # the diagonal slash near the top.  A first pass drew it 0.09 wide and it
    # read as a solid white OBJECT -- a rocket -- rather than as a brush mark;
    # the photograph's slash is a stroke among strokes, so it is narrower now
    # and travels with two thinner companions.
    _taper(b, t, (0.104, 0.078), (0.578, 0.268), 0.056, 0.014, N1_HI, ar, 0.90)
    _taper(b, t, (0.128, 0.126), (0.548, 0.296), 0.020, 0.008, N1_HI2, ar, 0.60)
    _taper(b, t, (0.082, 0.152), (0.492, 0.322), 0.016, 0.007, N1_INK, ar, 0.60)
    _taper(b, t, (0.150, 0.044), (0.560, 0.212), 0.013, 0.006, N1_INK, ar, 0.50)

    # the almond lens, low on the flank
    lens = _n1_lens(0.418, 0.678, 0.292, 0.146)
    _poly_line(b, t, lens, 0.013, N1_HI, ar, 0.95, close=True)
    _poly_line(b, t, _n1_lens(0.418, 0.678, 0.228, 0.114), 0.011, N1_INK,
               ar, 0.72, close=True)
    _seg(b, t, (0.208, 0.678), (0.628, 0.678), 0.006, N1_INK, ar, 0.65)
    _arc(b, t, 0.448, 0.646, 0.110, math.pi * 0.15, math.pi * 1.05, 0.010,
         N1_HI, ar, 0.60)
    _taper(b, t, (0.258, 0.748), (0.600, 0.616), 0.026, 0.010, N1_HI, ar, 0.55)

    # tag strokes.  These MUST cross themselves and share tails.  A first pass
    # drew them as plain five-point zigzags and the flank came out carrying a
    # large white M and a large white N -- and the one thing three independent
    # photo readings all agree on about this machine is that NO title resolves
    # on it, so a letterform here would be an invented one.
    _n1_tag(b, t, [(0.072, 0.478), (0.168, 0.384), (0.132, 0.452),
                   (0.256, 0.408), (0.196, 0.492), (0.344, 0.396),
                   (0.288, 0.470), (0.436, 0.428)],
            0.038, N1_HI, ar, 0.85)
    _poly_line(b, t, _ellp(0.226, 0.446, 0.052, 0.052, ar, 18), 0.016,
               N1_HI, ar, 0.60, close=True)
    _n1_tag(b, t, [(0.548, 0.862), (0.636, 0.770), (0.596, 0.842),
                   (0.712, 0.788), (0.664, 0.874), (0.776, 0.804)],
            0.030, N1_INK, ar, 0.80)
    _n1_tag(b, t, [(0.084, 0.892), (0.176, 0.818), (0.140, 0.882),
                   (0.262, 0.828), (0.216, 0.898), (0.336, 0.842)],
            0.022, N1_HI, ar, 0.60)

    # a hatch cluster -- the wrap has one dense passage of near-parallel
    # strokes.  Drawn as arcs rather than rules: fifteen straight lines read as
    # ruled paper, which nothing in the photograph does.
    for k in range(13):
        _arc(b, t, 0.760 - k * 0.014, 0.404 + k * 0.006, 0.300 + k * 0.004,
             math.pi * 0.62, math.pi * 1.02, 0.0050,
             N1_HI if k % 3 else N1_INK, ar, 0.50)

    _glyphs(b, t, 0.03, 0.03, 0.96, 0.965, 108, 5177, N1_INK, N1_HI, ar,
            avoid=lens)
    # the vinyl folds over the front edge; a hairline where it meets the molding
    _rect(b, t, 0.944, 0.0, 0.960, 1.0, _hx("#5c606a"), 0.45)
    _rect(b, t, 0.960, 0.0, 1.0, 1.0, _hx("#16181e"), 0.85)
    _rect(b, t, 0.0, 0.976, 1.0, 1.0, _hx("#111319"))       # black plinth
    _flush(px, ox, oy, b, t)


def n1_front(px, ox, oy, t):
    """The wrap continues to the floor.  The front's OWN structure is what is
    drawn on top of it: two panels split by a horizontal seam at about mid
    height, a large NEAR-BLACK RECESSED coin panel in the upper one carrying a
    single small white dot -- the coin plunger, and the whole of this machine's
    coin-door treatment; there is no chrome plate and there are no visible
    slots -- and the printed QR-code square low on the lower panel."""
    ar = PANEL_AR["north-1-graffiti-multicade.front"]
    b = _new(t, N1_GND)
    _n1_ground(b, t, 34)

    # the wrap, running the full height of the front
    r = _R(808)
    for j in range(8):
        uu = 0.058 + j * 0.122 + r.f(-0.016, 0.016)
        _taper(b, t, (uu, r.f(0.02, 0.14)),
               (uu + r.f(-0.05, 0.05), r.f(0.86, 0.99)),
               r.f(0.012, 0.038), r.f(0.008, 0.024),
               N1_INK if j % 2 else N1_HI, ar, r.f(0.35, 0.72))
    _arc(b, t, 0.30, -0.55, 1.00, math.pi * 0.14, math.pi * 0.86, 0.016,
         N1_HI, ar, 0.55)
    _arc(b, t, 0.74, 1.52, 0.92, math.pi * 1.10, math.pi * 1.90, 0.014,
         N1_INK, ar, 0.60)
    # three long near-horizontal sweeps, not five ruled lines: the first pass
    # crossed the eight vertical strokes into a technical-drawing grid, which
    # is not what v4 6 shows.
    for j in range(3):
        _arc(b, t, 0.44 + j * 0.10, 0.10 + j * 0.34, 1.05 + j * 0.12,
             math.pi * (0.06 + j * 0.02), math.pi * (0.94 - j * 0.02),
             0.0085, N1_INK, ar, 0.42)
    _glyphs(b, t, 0.04, 0.03, 0.96, 0.50, 44, 623, N1_INK, N1_HI, ar)
    _glyphs(b, t, 0.04, 0.58, 0.96, 0.97, 40, 631, N1_INK, N1_HI, ar)

    # the horizontal seam between the two front panels
    _rect(b, t, 0.0, 0.532, 1.0, 0.552, _hx("#0a0b0f"))
    _seg(b, t, (0.0, 0.556), (1.0, 0.556), 0.005, _hx("#6a6e78"), ar, 0.6)
    _poly_line(b, t, [(0.026, 0.022), (0.974, 0.022), (0.974, 0.518),
                      (0.026, 0.518)], 0.006, _hx("#4e525c"), ar, 0.55,
               close=True)
    _poly_line(b, t, [(0.026, 0.566), (0.974, 0.566), (0.974, 0.976),
                      (0.026, 0.976)], 0.006, _hx("#4e525c"), ar, 0.55,
               close=True)

    # THE COIN DOOR: a large plain near-black recess with one white plunger
    _rect(b, t, 0.186, 0.116, 0.814, 0.486, _hx("#0b0c10"))
    _bevel(b, t, 0.186, 0.116, 0.814, 0.486, 0.014, _hx("#7a7e88"),
           _hx("#05060a"), ar, 0.75)
    _vgrad(b, t, 0.120, 0.482, _hx("#15161c"), _hx("#08090c"), 0.192, 0.808)
    _rect(b, t, 0.186, 0.116, 0.814, 0.132, _hx("#3c404a"), 0.5)
    _ellipse(b, t, 0.664, 0.300, 0.030, _hx("#f0f2f6"), ar)     # coin plunger
    _ellipse(b, t, 0.664, 0.300, 0.016, _hx("#8a8e98"), ar)
    _ellipse(b, t, 0.310, 0.408, 0.017, _hx("#4a4e58"), ar, 0.8)   # lock
    _screws(b, t, [(0.212, 0.146), (0.788, 0.146)], 0.010, ar, a=0.5)

    # the printed QR square, low on the lower panel
    qs = 0.230                                       # a LENGTH (tile-Y units)
    qw = qs / ar
    qu, qv = 0.452, 0.660
    _rect(b, t, qu, qv, qu + qw, qv + qs, _hx("#0c0d11"))
    m0 = qs * 0.06
    mod = qs * 0.88 / 15.0
    q = _R(9090)
    _rect(b, t, qu + m0 / ar, qv + m0, qu + (qs - m0) / ar, qv + qs - m0,
          _hx("#d8dbe2"))
    for gy in range(15):
        for gx in range(15):
            if (gx < 6 and gy < 6) or (gx > 8 and gy < 6) or \
               (gx < 6 and gy > 8):
                continue
            if q.u() < 0.46:
                _rect(b, t, qu + (m0 + gx * mod) / ar, qv + m0 + gy * mod,
                      qu + (m0 + (gx + 1) * mod) / ar,
                      qv + m0 + (gy + 1) * mod, _hx("#0e0f14"))
    for (fx, fy) in ((0, 0), (9, 0), (0, 9)):
        bx0 = m0 + fx * mod
        by0 = m0 + fy * mod
        for (o0, o1, cc) in ((0, 6, _hx("#0e0f14")), (1, 5, _hx("#d8dbe2")),
                             (2, 4, _hx("#0e0f14"))):
            _rect(b, t, qu + (bx0 + o0 * mod) / ar, qv + by0 + o0 * mod,
                  qu + (bx0 + o1 * mod) / ar, qv + by0 + o1 * mod, cc)
    _rect(b, t, 0.0, 0.980, 1.0, 1.0, _hx("#111319"))
    _flush(px, ox, oy, b, t)


def n1_deck(px, ox, oy, t):
    """Black, wide, and projecting further past the carcase than any of its
    three neighbours -- the deepest deck on the north wall.  Two joystick /
    button clusters, and the surface reads PLAIN DARK with no printed legend in
    either frame, so none is drawn: what is printed is worn steel, the two
    elliptical wear halos the clusters have rubbed into it, the bolted edge and
    the fold of the wrap over the back lip.  The clusters themselves are
    GEOMETRY -- see DECKS.  Authored ~2x for a2kit's ART_DK deck material."""
    ar = PANEL_AR["north-1-graffiti-multicade.deck"]
    b = _new(t, _hx("#46454e"))
    _vgrad(b, t, 0.0, 1.0, _hx("#3a3942"), _hx("#52515b"))
    _brush(b, t, 0.05, 0.93, 99, 13.0, 0.010)
    # the vinyl wrap folds over the back lip of the deck
    _rect(b, t, 0.0, 0.0, 1.0, 0.050, _hx("#2a2932"))
    _glyphs(b, t, 0.04, 0.006, 0.96, 0.044, 14, 771, _hx("#6e727c"),
            _hx("#a2a6ae"), ar, scale=0.55, a=0.55)
    # the black control-panel overlay, bolted down inside a steel surround --
    # the structure a real full-size upright has and the three Arcade1Up
    # machines beside it do not
    _rect(b, t, 0.032, 0.108, 0.968, 0.858, _hx("#26252d"))
    _bevel(b, t, 0.032, 0.108, 0.968, 0.858, 0.020, _hx("#7c7b85"),
           _hx("#16151b"), ar, 0.85)
    _vgrad(b, t, 0.112, 0.854, _hx("#2b2a33"), _hx("#1a1922"), 0.036, 0.964)
    # the wear halos the two clusters have rubbed into the overlay
    for cu in (0.262, 0.738):
        _fill_poly(b, t, _ellp(cu, 0.492, 0.430, 0.300, ar, 30),
                   _hx("#494852"), 0.45)
        _fill_poly(b, t, _ellp(cu, 0.492, 0.300, 0.200, ar, 30),
                   _hx("#54535e"), 0.35)
        _poly_line(b, t, _ellp(cu, 0.492, 0.430, 0.300, ar, 30), 0.007,
                   _hx("#7a7982"), ar, 0.28, close=True)
    _seg(b, t, (0.500, 0.130), (0.500, 0.836), 0.012, _hx("#151419"), ar, 0.8)
    _seg(b, t, (0.500, 0.130), (0.500, 0.836), 0.004, _hx("#6c6b75"), ar, 0.35)
    _screws(b, t, [(0.062, 0.148), (0.938, 0.148), (0.062, 0.818),
                   (0.938, 0.818)], 0.022, ar, a=0.8)
    for (a0, b0, a1, b1) in ((0.10, 0.22, 0.44, 0.30),
                             (0.56, 0.74, 0.90, 0.66)):
        _taper(b, t, (a0, b0), (a1, b1), 0.007, 0.004, _hx("#8c8b95"), ar, 0.28)
    _seg(b, t, (0.0, 0.884), (1.0, 0.884), 0.014, _hx("#1e1d24"), ar)
    _vgrad(b, t, 0.892, 1.0, _hx("#76757f"), _hx("#4c4b53"))
    _flush(px, ox, oy, b, t)

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
# The three machines this module OWNS in round 5.
PANELS = {
    "star-wars-atari.marquee": sw_marquee,
    "star-wars-atari.side": sw_side,
    "star-wars-atari.front": sw_front,
    "star-wars-atari.deck": sw_deck,

    "ridge-racer.marquee": rr_marquee,
    "ridge-racer.side": rr_side,
    "ridge-racer.front": rr_front,
    "ridge-racer.deck": rr_deck,
    "ridge-racer.bezel": rr_bezel,

    "north-1-graffiti-multicade.marquee": n1_marquee,
    "north-1-graffiti-multicade.side": n1_side,
    "north-1-graffiti-multicade.front": n1_front,
    "north-1-graffiti-multicade.deck": n1_deck,
}

# ROUND-4 CARRY-OVERS.  Round 5 re-dealt the machines between the four art
# agents; Mortal Kombat, Legends Ultimate and Golden Tee were this module's in
# round 4 and belong to somebody else now.  Their round-4 paint functions are
# still here, unchanged, but they are NOT in PANELS -- `atlas4.py` raises on a
# duplicate key and a hard import failure would take the whole build down.
#
#   INTEGRATOR: if no round-5 module claims one of these three, merge it back
#   with  PANELS.update({k: v for k, v in art_g3.LEGACY_PANELS.items()
#                        if k not in PANELS})
#   after the other modules are merged.  If somebody did claim it, theirs wins
#   and nothing here needs touching.
LEGACY_PANELS = {
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

    "golden-tee-3d-golf.marquee": gt_marquee,
    "golden-tee-3d-golf.side": gt_side,
    "golden-tee-3d-golf.front": gt_front,
    "golden-tee-3d-golf.deck": gt_deck,
    "golden-tee-3d-golf.bezel": gt_bezel,
}


# ------------------------------------------------------------------- DECKS
# Control-deck HARDWARE, exported as data because it is geometry `upright()`
# places and an art module cannot vary it by painting.  Round 4 gave all
# sixteen machines the same two joysticks (one red top, one blue top) over the
# same row of six flat squares; three critics counted it independently.
#
# COORDINATES.  (u, v) are the DECK TILE's own normalised coordinates, so the
# hardware lands exactly on the graphic printed under it:
#
#     x = (-bw/2 + 0.06) + u * (bw - 0.12)
#     z = (ft + 0.04)    + v * ((fd - 0.06) - (ft + 0.04))
#     y = dy + 0.014                       (the deck art plane; parts sit ON it)
#
#     v = 0 is the BACK of the deck, under the screen;  v = 1 is the FRONT edge
#     nearest the player.  ft = bd/2 - 0.62 and fd = bd/2 + 0.40, as in
#     `_profile()`.  All linear sizes below ("r", "d", "h", "cy", ...) are FEET.
#
# `suppress_default: True` means: do NOT run upright()'s built-in
# `for k in range(2): ... BUTTONS[...]` loop for this machine.  Build only what
# is listed here.  Every machine in this module suppresses it -- none of the
# three has the generic two-stick six-square deck, and two of them have no
# joystick at all.
DECKS = {
    # ---------------------------------------------------------- Star Wars
    # NOT PHOTOGRAPHED.  The deck faces the corner in both frames.  What is
    # specified is the control the 1983 Atari Star Wars upright is built round
    # -- a two-handed FLIGHT YOKE, no joystick, no button row -- and nothing
    # else.  If the yoke is too much to build, use `fallback`, which is four
    # red fire buttons and still shares no layout with any other machine.
    "star-wars-atari": {
        "note": "flight yoke, no joysticks; deck not visible in any photo",
        "suppress_default": True,
        "sticks": [],
        "buttons": [
            # 1P / 2P start, flanking the yoke plate on the player edge
            {"u": 0.150, "v": 0.800, "d": 0.085, "h": 0.040,
             "shape": "round", "col": "#c8342c", "emissive": False},
            {"u": 0.850, "v": 0.800, "d": 0.085, "h": 0.040,
             "shape": "round", "col": "#d8a028", "emissive": False},
        ],
        "specials": [{
            "kind": "yoke",
            "u": 0.500, "v": 0.512,        # centre, on the painted escutcheon
            "column_r": 0.052, "column_h": 0.24, "column_col": "#3a3a42",
            "cy": 0.26,                    # bar height above the deck plane
            "half_span": 0.34, "bar_r": 0.034, "bar_col": "#17171c",
            "grip_r": 0.058, "grip_h": 0.30, "grip_col": "#101014",
            "rake_deg": 74,                # bar plane tilted back from vertical
            # two red fire buttons, one on the top of each grip
            "grip_buttons": {"d": 0.070, "h": 0.030, "col": "#c8342c"},
        }],
        "fallback": {
            "sticks": [],
            "buttons": [{"u": u, "v": 0.480, "d": 0.115, "h": 0.045,
                         "shape": "round", "col": "#c8342c"}
                        for u in (0.340, 0.446, 0.552, 0.658)],
        },
    },

    # -------------------------------------------------------- Ridge Racer
    # PHOTOGRAPHED, v4 8 px (490,105)-(610,250) at 8x: a large round steering
    # wheel mounted centrally, dark rim with a pale olive centre boss and three
    # spokes, a small dark button cluster to its LEFT and two round WHITE
    # illuminated buttons to its RIGHT.  No joystick anywhere on this machine.
    "ridge-racer": {
        "note": "steering wheel + 3 small left buttons + 2 big white right",
        "suppress_default": True,
        "sticks": [],
        "buttons": [
            {"u": 0.252, "v": 0.300, "d": 0.085, "h": 0.032,
             "shape": "round", "col": "#3c3e46"},
            {"u": 0.252, "v": 0.470, "d": 0.085, "h": 0.032,
             "shape": "round", "col": "#3c3e46"},
            {"u": 0.252, "v": 0.640, "d": 0.085, "h": 0.032,
             "shape": "round", "col": "#3c3e46"},
            {"u": 0.866, "v": 0.324, "d": 0.150, "h": 0.048,
             "shape": "round", "col": "#f2f4f6", "emissive": True},
            {"u": 0.866, "v": 0.614, "d": 0.150, "h": 0.048,
             "shape": "round", "col": "#f2f4f6", "emissive": True},
        ],
        "specials": [{
            "kind": "wheel",
            "u": 0.468, "v": 0.500,        # centre, on the painted escutcheon
            "cy": 0.40,                    # hub height above the deck plane
            "rake_deg": 58,                # wheel FACE tilted up from horizontal
            "r": 0.34,                     # rim centreline radius
            "rim_r": 0.042,                # rim tube radius
            "rim_col": "#1b1c22",
            "spokes": 3, "spoke_r": 0.030, "spoke_col": "#2b2c34",
            "hub_r": 0.115, "hub_col": "#b6b884",   # the pale olive boss
            "column_r": 0.055, "column_col": "#26272e",
        }],
    },

    # ---------------------------------------------------- graffiti multicade
    # PHOTOGRAPHED, v4 6 px (222,110)-(295,290) at 10x and v3 1: black, wide,
    # the DEEPEST deck on the north wall, with TWO joystick/button clusters --
    # a real full-size two-player upright, not an Arcade1Up.  Colours do not
    # resolve; the deck reads plain dark, so the sticks are black bat-tops with
    # a chrome dust washer and the buttons are a monochrome set, NOT the
    # red/blue pair and rainbow squares round 4 put on all sixteen machines.
    "north-1-graffiti-multicade": {
        "note": "two 8-way BAT-TOP sticks + 6 round buttons each, 2 start",
        "suppress_default": True,
        "sticks": [
            {"u": 0.112, "v": 0.585, "type": "bat", "shaft_r": 0.030,
             "shaft_h": 0.175, "shaft_col": "#b6bac2",
             "top_w": 0.075, "top_h": 0.115, "top_col": "#141418",
             "washer_r": 0.085, "washer_col": "#9aa0a8"},
            {"u": 0.588, "v": 0.585, "type": "bat", "shaft_r": 0.030,
             "shaft_h": 0.175, "shaft_col": "#b6bac2",
             "top_w": 0.075, "top_h": 0.115, "top_col": "#141418",
             "washer_r": 0.085, "washer_col": "#9aa0a8"},
        ],
        # six per player in the standard two-row arc: the top row sits 0.075 ft
        # further from the player than the bottom row and is stepped up in u.
        "buttons": [
            {"u": 0.112 + 0.100 + i * 0.078 + p * 0.476,
             "v": 0.470 + (0.0 if row else 0.150) + i * (-0.028 if row else -0.022),
             "d": 0.115, "h": 0.042, "shape": "round",
             "col": "#dcdce0" if row else "#2a2a30"}
            for p in (0, 1) for row in (1, 0) for i in (0, 1, 2)
        ] + [
            {"u": 0.420, "v": 0.170, "d": 0.075, "h": 0.030,
             "shape": "round", "col": "#c8c8cc"},
            {"u": 0.580, "v": 0.170, "d": 0.075, "h": 0.030,
             "shape": "round", "col": "#c8c8cc"},
        ],
        "specials": [],
    },
}


# ---------------------------------------------------------------- COINDOOR
# The other half of the same defect: round 4 built ONE grey box, `CPANEL`
# -0.34..0.34 x plinth+0.30..0.92, dead centre and low, on all sixteen fronts,
# and it is the loudest thing on the north-wall close-up.  These three machines
# do not share a coin-door position, size, plate colour or treatment, and two
# of them have no proud plate at all -- theirs are RECESSES, printed into the
# front artwork.
#
# COORDINATES are the FRONT TILE's own normalised (u, v), so the box lands on
# the painted door:
#
#     x = (-bw/2 + 0.08) + u * (bw - 0.16)
#     y = (dy - 0.62)    - v * ((dy - 0.62) - (plinth + 0.16))
#     z = fb + 0.008                          (the printed front plane)
#
#     v = 0 is the TOP of the printed front panel, v = 1 its bottom.
#     `proud` is the thickness in FEET the box stands off z; proud = 0.0 means
#     BUILD NOTHING -- the artwork carries the whole door.
COINDOOR = {
    "star-wars-atari": {
        "note": "two-slot steel door LEFT of centre, coin-return cup below it; "
                "not photographed, so it is honest hardware and no more",
        "suppress_default": True,
        "u0": 0.140, "v0": 0.578, "u1": 0.560, "v1": 0.884,
        "proud": 0.045, "plate": "#141519",
        "cup": {"u0": 0.196, "v0": 0.898, "u1": 0.430, "v1": 0.978,
                "proud": 0.058, "plate": "#c2c6cc"},
    },
    "ridge-racer": {
        "note": "a RECESS low and LEFT in the maroon base, with a chrome coin "
                "plate and a separate return opening -- v4 8, v3 4.  Nothing "
                "stands proud; build no box.",
        "suppress_default": True,
        "u0": 0.052, "v0": 0.856, "u1": 0.472, "v1": 0.986,
        "proud": 0.0, "plate": None, "cup": None,
    },
    "north-1-graffiti-multicade": {
        "note": "a LARGE plain near-black recess across the middle of the "
                "upper front panel with ONE white plunger and no visible "
                "slots -- v3 1 at 7x.  Nothing stands proud except the "
                "plunger itself.",
        "suppress_default": True,
        "u0": 0.186, "v0": 0.116, "u1": 0.814, "v1": 0.486,
        "proud": 0.0, "plate": None, "cup": None,
        "boss": {"u": 0.664, "v": 0.300, "r": 0.030, "proud": 0.022,
                 "col": "#f0f2f6"},
    },
}


# ------------------------------------------------------------------- SCREENS
# Rule 4 of the round-5 brief: the CRT is not black -- unless the photograph
# says it is.  For all three of these machines it does.
SCREENS = {
    "star-wars-atari":
        "NOT VISIBLE.  The screen faces the corner in v4 8 and v4 9.  Leave "
        "ar2's default dark SCRN material; do not invent an attract loop.",
    "ridge-racer":
        "VISIBLE AND OFF.  v4 8 px (490,105)-(610,250) at 8x shows both Ridge "
        "Racer cabinets with a flat dark grey-blue monitor; the right-hand one "
        "carries a hard white specular of a ceiling can and nothing else.  No "
        "attract image exists to paint.  Keep it dark.",
    "north-1-graffiti-multicade":
        "VISIBLE AND OFF.  v3 1 px (515,555)-(625,840) at 6x shows a flat "
        "black screen under the marquee; v4 6 agrees.  The roster records that "
        "even the marquee does not read as lit.  Keep it dark.",
}


# --------------------------------------------------------------------- NOTES
# What each panel claims, so a critic can check the claim and not only the look.
NOTES = {
    "star-wars-atari.side":
        "v4 9 px (150,220)-(300,480) and v4 8 px (0,90)-(140,340), 6x crops in "
        "art/ref_g3/sw_v49.png and sw_v48.png.  Yellow carcase; black stepped "
        "art panel; starfield; two TIE fighters plus a distant third; Vader's "
        "helmet in dark blue at low contrast, as printed; the Death Star limb "
        "with panel banding and the trench notch; a large X-wing low-forward "
        "and a small one behind; the inset rectangular panel at the lower "
        "rear.  The blue LED strip along the lower front edge is a fixture the "
        "owner added and is deliberately NOT printed.",
    "star-wars-atari.marquee":
        "NOT VISIBLE in any photograph -- dark and generic on purpose, no "
        "title invented.  Unchanged in intent from round 4.",
    "star-wars-atari.front":
        "NOT VISIBLE.  Full-bleed in the carcase yellow that IS photographed, "
        "with a black inset panel in the same printed language as the flank "
        "(starfield, Death Star limb, one TIE, one small X-wing -- every one "
        "of those is photographed on this machine's flank).  No character "
        "portrait, no wordmark, no Atari logo.  The "
        "coin door is honest hardware set left of centre with its return cup.",
    "star-wars-atari.deck":
        "NOT VISIBLE.  Charcoal deck, yellow leading return, the chrome "
        "escutcheon a yoke column comes out of and two instruction decals.  No "
        "legend, because none is legible anywhere.",
    "ridge-racer.marquee":
        "Band colour off v4 5 / v4 8; the LETTERING is reconstructed from the "
        "lower-front wordmark (rr_v34.png, 'RIDGE RAC' at 16x) because the "
        "marquee itself blows out in every frame.  Unchanged from round 4.",
    "ridge-racer.side":
        "Not visible in any frame, so NO graphic is invented: body colour edge "
        "to edge plus hardware -- the moulded highlight, the black deck "
        "return, the base seam, a louvred vent, a bolted service door, the "
        "plinth.",
    "ridge-racer.front":
        "v4 8 px (490,105)-(610,250) at 8x (rr_v48.png) for the big black "
        "recessed panel and the coin recess low-left; v3 4 px "
        "(1130,795)-(1200,850) at 16x (rr_v34.png) for 'RIDGE RAC[ER]' in "
        "white italic caps and the pale flash to its left.",
    "ridge-racer.deck":
        "v4 8 at 8x: wheel centred, small dark cluster left, two round white "
        "illuminated buttons right.  All of that is GEOMETRY (DECKS); what is "
        "printed is the steel, the escutcheon, the rim's shadow, the "
        "instruction decal and the button plate.",
    "ridge-racer.bezel":
        "Dark surround with the body's red return.  The screen itself is off "
        "in the photograph -- see SCREENS.",
    "north-1-graffiti-multicade.marquee":
        "v3 1 at 7x: pale strokes, a small maroon patch below-left, a light "
        "angular mark at the right end.  NO title resolves in any frame at any "
        "magnification, so none is printed.  Unchanged from round 4.",
    "north-1-graffiti-multicade.side":
        "v3 1 px (515,555)-(625,840) at 6x (n1_v31.png) and v4 6 px "
        "(222,110)-(295,290) at 10x (n1_v46.png, the neutral exposure).  Full "
        "bleed: sweeping curves, the diagonal slash near the top, the large "
        "almond lens low, a dense scatter of small marks.  Ground lifted from "
        "the photograph's blue-washed #1a1c24 to a neutral #2c2f3a and the ink "
        "authored at 190-235, because the LINE WORK is the identity.",
    "north-1-graffiti-multicade.front":
        "Same two frames.  The wrap continues to the floor; horizontal seam at "
        "mid height; the large near-black coin recess with ONE white plunger "
        "and no visible slots; the printed QR square low on the lower panel.",
    "north-1-graffiti-multicade.deck":
        "v4 6 at 10x: black, wide, the deepest deck on the wall, two clusters, "
        "NO printed legend -- so none is drawn.  Worn steel, two wear halos, "
        "the bolted edge, the wrap folding over the back lip.",
}


# Measured panel means (R+G+B)/3 over the rendered tile, filled in by
# `art/preview_g3.py`.  Two of these three machines are photographically near
# black and lifting them to the brief's 200-240 would print a grey cabinet;
# what is lifted instead is the INK.  See point 3 of the module docstring.
MEANS = {
    "north-1-graffiti-multicade.deck": 58.5,
    "north-1-graffiti-multicade.front": 53.7,
    "north-1-graffiti-multicade.marquee": 52.3,
    "north-1-graffiti-multicade.side": 91.7,
    "ridge-racer.bezel": 30.2,
    "ridge-racer.deck": 70.3,
    "ridge-racer.front": 58.6,
    "ridge-racer.marquee": 126.3,
    "ridge-racer.side": 64.3,
    "star-wars-atari.deck": 90.4,
    "star-wars-atari.front": 85.8,
    "star-wars-atari.marquee": 32.8,
    "star-wars-atari.side": 109.4,
}
