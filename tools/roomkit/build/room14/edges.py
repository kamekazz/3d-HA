"""Sub-pixel edge finding on a scanline, pure python (no numpy in this venv)."""
from PIL import Image


def load_gray(path):
    im = Image.open(path).convert("L")
    return im, im.load(), im.size


def row_lum(px, y, x0, x1, blur=2):
    """average |blur| rows around y, over [x0,x1)"""
    out = []
    for x in range(x0, x1):
        s = 0.0
        n = 0
        for dy in range(-blur, blur + 1):
            s += px[x, y + dy]
            n += 1
        out.append(s / n)
    return out


def col_lum(px, x, y0, y1, blur=2):
    out = []
    for y in range(y0, y1):
        s = 0.0
        n = 0
        for dx in range(-blur, blur + 1):
            s += px[x + dx, y]
            n += 1
        out.append(s / n)
    return out


def best_edge(vals, base, sign):
    """sign=+1 -> rising (dark->bright as index grows); returns subpixel coord."""
    k = [-1, -2, 0, 2, 1]
    best, bi, bg = None, None, -1e9
    g = [0.0] * len(vals)
    for i in range(2, len(vals) - 2):
        gg = sum(k[j + 2] * vals[i + j] for j in range(-2, 3)) / 6.0 * sign
        g[i] = gg
        if gg > bg:
            bg, bi = gg, i
    if bi is None or bi < 3 or bi > len(vals) - 4:
        return None, 0.0
    a, b, c = g[bi - 1], g[bi], g[bi + 1]
    den = (a - 2 * b + c)
    d = 0.5 * (a - c) / den if den != 0 else 0.0
    return base + bi + d, bg


def fit_line(pts):
    """least squares y = m*x + b over (x,y); returns m,b,resid"""
    n = len(pts)
    sx = sum(p[0] for p in pts)
    sy = sum(p[1] for p in pts)
    sxx = sum(p[0] * p[0] for p in pts)
    sxy = sum(p[0] * p[1] for p in pts)
    den = n * sxx - sx * sx
    m = (n * sxy - sx * sy) / den
    b = (sy - m * sx) / n
    r = (sum((p[1] - m * p[0] - b) ** 2 for p in pts) / n) ** 0.5
    return m, b, r
