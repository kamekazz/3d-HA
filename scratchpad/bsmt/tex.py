"""Tiled-texture + vertex-colour helpers for room 1.

Fine-scale surface gradient comes from a small seamless PNG tile (a few KB)
multiplied into the material colour, NOT from rasterised geometry cells --
see ROOM-BRIEF "sd is SCALE-BLIND" and the payload budget.
"""
import math, sys
sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
from roomkit.glb import png_gray, png_rgb, Part


class R:
    def __init__(self, s): self.s = s & 0x7fffffff
    def f(self, a=0.0, b=1.0):
        self.s = (self.s * 1103515245 + 12345) % (1 << 31)
        return a + (b - a) * (((self.s >> 9) % 100000) / 100000.0)


def _value_noise(n, cells, rnd):
    """Bilinear value noise on an n x n grid, wrapping. Returns -1..1 floats."""
    g = [[rnd.f(-1, 1) for _ in range(cells)] for _ in range(cells)]
    out = [[0.0] * n for _ in range(n)]
    for y in range(n):
        fy = y * cells / n; y0 = int(fy) % cells; y1 = (y0 + 1) % cells; ty = fy - int(fy)
        ty = ty * ty * (3 - 2 * ty)
        for x in range(n):
            fx = x * cells / n; x0 = int(fx) % cells; x1 = (x0 + 1) % cells; tx = fx - int(fx)
            tx = tx * tx * (3 - 2 * tx)
            a = g[y0][x0] * (1 - tx) + g[y0][x1] * tx
            b = g[y1][x0] * (1 - tx) + g[y1][x1] * tx
            out[y][x] = a * (1 - ty) + b * ty
    return out


def grain_tile(n=48, mean=246, grain=7.0, blotch=0.0, cells=4, seed=7):
    """Near-white seamless grey tile: fine per-texel grain + optional soft
    low-frequency blotch. Mean near white so it only modulates `color`."""
    rnd = R(seed)
    lo = _value_noise(n, cells, R(seed * 3 + 1)) if blotch else None
    rows = []
    for y in range(n):
        row = []
        for x in range(n):
            v = mean + rnd.f(-grain, grain)
            if lo:
                v += lo[y][x] * blotch
            row.append(max(0, min(255, int(round(v)))))
        rows.append(row)
    return png_gray(rows)


def weave_tile(n=48, mean=244, grain=10.0, seed=11, warp=6):
    """Fabric: fine grain modulated by a warp/weft ribbing."""
    rnd = R(seed)
    rows = []
    for y in range(n):
        row = []
        for x in range(n):
            rib = (math.sin(2 * math.pi * x * warp / n) * 0.5
                   + math.sin(2 * math.pi * y * warp / n) * 0.5) * grain * 0.45
            v = mean + rib + rnd.f(-grain, grain)
            row.append(max(0, min(255, int(round(v)))))
        rows.append(row)
    return png_gray(rows)


def plank_tile(n=96, boards=3, seed=5):
    """Grey wide-plank: `boards` planks per tile with anisotropic grain running
    along u.  No sine term -- a periodic one reads as chevron stripes once the
    tile repeats across a room."""
    rnd = R(seed)
    coarse = _value_noise(n, 5, R(seed + 1))
    fine = _value_noise(n, 26, R(seed + 2))
    bh = n // boards
    rows = []
    for y in range(n):
        row = []
        b = y // bh
        edge = (y % bh) < 2
        tint = (-14, 6, 20)[b % 3]
        for x in range(n):
            # stretch the noise along u so the grain runs lengthwise.  Contrast
            # raised in round 2b: the photographed plank meters sd 26-36 and
            # |dh| 3.2-5.0, the render was at sd 9.1 / |dh| 2.1.
            v = 238 + tint * 1.6 + coarse[(y * 4) % n][x] * 26 + fine[(y * 9) % n][x] * 19
            v += rnd.f(-11, 11)
            if edge:
                v -= 52
            row.append(max(0, min(255, int(round(v)))))
        rows.append(row)
    return png_gray(rows)


def art_tile(w=180, h=90, seed=99):
    """A wide, low-key battle-scene print: pale sky, dark massed silhouettes."""
    rnd = R(seed)
    lo = _value_noise(max(w, h), 6, R(seed + 3))
    px = [[(0, 0, 0)] * w for _ in range(h)]
    for y in range(h):
        t = y / (h - 1.0)
        # sky: pale grey-green above, murk below
        base = 208 - 96 * (t ** 1.15)
        for x in range(w):
            v = base + lo[y % len(lo)][x % len(lo[0])] * 26
            r = v * 0.99; g = v * 1.00; b = v * 0.96
            px[y][x] = (r, g, b)
    # massed dark silhouettes along the lower half
    for _ in range(58):
        cx = rnd.f(0, w); cy = rnd.f(h * 0.30, h * 1.02)
        rx = rnd.f(3.0, 13.0); ry = rnd.f(5.0, 26.0)
        tone = rnd.f(0.34, 0.66)
        for y in range(max(0, int(cy - ry)), min(h, int(cy + ry) + 1)):
            for x in range(max(0, int(cx - rx)), min(w, int(cx + rx) + 1)):
                d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
                if d <= 1.0:
                    k = tone + (1 - tone) * (d ** 2) * 0.35
                    r, g, b = px[y][x]
                    px[y][x] = (r * k, g * k, b * k)
    # a few pale highlights so it is not a black mass
    for _ in range(26):
        cx = rnd.f(0, w); cy = rnd.f(h * 0.25, h * 0.85)
        rx = rnd.f(1.5, 5.0); ry = rnd.f(1.5, 6.0); add = rnd.f(30, 95)
        for y in range(max(0, int(cy - ry)), min(h, int(cy + ry) + 1)):
            for x in range(max(0, int(cx - rx)), min(w, int(cx + rx) + 1)):
                d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
                if d <= 1.0:
                    r, g, b = px[y][x]
                    a = add * (1 - d)
                    px[y][x] = (r + a, g + a * 1.02, b + a * 0.9)
    rows = []
    for y in range(h):
        row = []
        for x in range(w):
            r, g, b = px[y][x]
            m = (r + g + b) / 3.0
            k = 0.70                      # compress toward the panel mean
            r = 121 + (r - 113) * k; g = 124 + (g - 116) * k; b = 116 + (b - 108) * k
            n = rnd.f(-9, 9)
            row.append((max(0, min(255, int(r + n))), max(0, min(255, int(g + n))),
                        max(0, min(255, int(b + n)))))
        rows.append(row)
    return png_rgb(rows)


def geo_tile(n=32, seed=21):
    """Black/white blocky geometric weave for the throw pillows."""
    rnd = R(seed)
    rows = [[235] * n for _ in range(n)]
    for by in range(0, n, 8):
        for bx in range(0, n, 8):
            if rnd.f() < 0.55:
                for y in range(by, min(n, by + 6)):
                    for x in range(bx, min(n, bx + 6)):
                        rows[y][x] = 38
    for y in range(n):
        for x in range(n):
            rows[y][x] = max(0, min(255, rows[y][x] + int(rnd.f(-10, 10))))
    return png_gray(rows)


def grid_panel(pt, a0, a1, y0, y1, tile, rnd, amp=0.030, cell=1.7, flip=False,
               tone=None):
    """A subdivided plane in a wall's own (a, y) frame.

    `pt(a, y) -> (x, y, z)`.  Carries UVs for a repeating tile AND a smooth
    per-vertex colour jitter, so the surface has both fine grain (tile) and
    soft large-scale variation (vertex colour) at ~4 bytes/vertex.

    `tone(y) -> 0..1` is an optional multiplier in the SAME space Part.colors
    is authored in (glb.py runs COLOR_0 through srgb->linear on export).  It is
    how the top-to-bottom brightness RAMP a real wall has under ceiling
    downlights gets baked in: round 2 shipped a plane-fit slope of -0.5..0.0
    lum/100 px on all four walls where the photographs meter +14 to +35.
    """
    nx = max(1, int(round(abs(a1 - a0) / cell)))
    ny = max(1, int(round(abs(y1 - y0) / cell)))
    verts, uv, cols = [], [], []
    for j in range(ny + 1):
        for i in range(nx + 1):
            a = a0 + (a1 - a0) * i / nx
            y = y0 + (y1 - y0) * j / ny
            verts.append(pt(a, y))
            uv.append((a / tile, y / tile))
            c = 1.0 + rnd.f(-amp, amp)
            if tone is not None:
                c *= tone(y)
            c = max(0.0, min(1.0, c))
            cols.append((c, c, c))
    tris = []
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            b, c, d = a + 1, a + nx + 1, a + nx + 2
            tris += ([(a, b, c), (b, d, c)] if flip else [(a, c, b), (b, c, d)])
    return Part(verts, tris, smooth=True, colors=cols, uv=uv)
