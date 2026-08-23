"""Camera + banner solve for Garage v3 1.jpg, round 3.

Measures the north-south lines on the east wall (TV edges, pegboard edges,
wall/floor line) to get the N-S vanishing point, combines it with the east-west
vanishing point already solved off the banner's own top and bottom edges, and
returns the focal length from the orthogonality of the two.
"""
import math
import numpy as np
from PIL import Image

A = np.asarray(Image.open(
    r"C:\Users\Manuel\Desktop\Pro\3d HA\docs\photos-jpg\Garage v3 1.jpg"
).convert("RGB")).astype(np.float64)
L = A.mean(axis=2)


def edge_y(x, y0, y1, rising, w=3):
    """Sub-pixel y of the strongest step in column x over [y0,y1)."""
    v = L[y0:y1, x]
    g = np.array([v[i + w:i + 2 * w].mean() - v[i:i + w].mean()
                  for i in range(len(v) - 2 * w)])
    if not rising:
        g = -g
    k = int(np.argmax(g))
    return y0 + k + w, float(g[k])


def fitline(pts):
    x = np.array([p[0] for p in pts], float)
    y = np.array([p[1] for p in pts], float)
    m, b = np.polyfit(x, y, 1)
    rms = float(np.sqrt(((y - (m * x + b)) ** 2).mean()))
    return m, b, rms


def report(name, pts):
    m, b, r = fitline(pts)
    print("  %-22s n=%2d slope %+.4f rms %.2f" % (name, len(pts), m, r))
    return m, b


# ---------------------------------------------------------------- N-S lines
lines = []

# 1. TV top edge (black panel on the east wall)
p = []
for x in range(790, 941, 10):
    y, g = edge_y(x, 500, 560, rising=False, w=3)
    if g > 25:
        p.append((x, y))
lines.append(("TV top", report("TV top", p)))

# 2. TV bottom edge
p = []
for x in range(790, 941, 10):
    y, g = edge_y(x, 650, 720, rising=True, w=3)
    if g > 25:
        p.append((x, y))
lines.append(("TV bottom", report("TV bottom", p)))

# 3. pegboard top edge
p = []
for x in range(1010, 1196, 10):
    y, g = edge_y(x, 620, 670, rising=False, w=3)
    if g > 12:
        p.append((x, y))
lines.append(("pegboard top", report("pegboard top", p)))

# 4. east wall / floor line
p = []
for x in list(range(730, 861, 10)) + list(range(960, 1061, 10)):
    y, g = edge_y(x, 790, 930, rising=False, w=4)
    if g > 40:
        p.append((x, y))
lines.append(("east wall/floor", report("east wall/floor", p)))


def vp_ls(lines):
    """Least-squares vanishing point of a set of image lines y = m x + b."""
    Amat, bvec = [], []
    for _n, (m, b) in lines:
        # m x - y = -b
        Amat.append([m, -1.0])
        bvec.append(-b)
    sol, *_ = np.linalg.lstsq(np.array(Amat), np.array(bvec), rcond=None)
    return sol


VP_NS = vp_ls(lines)
print("  VP_NS = (%.0f, %.0f)" % tuple(VP_NS))

VP_EW = np.array([1636.5, 714.0])
CX, CY = 600.0, 800.0
d = -((VP_EW[0] - CX) * (VP_NS[0] - CX) + (VP_EW[1] - CY) * (VP_NS[1] - CY))
print("  f from orthogonal VPs = %.0f  (hfov %.1f deg on the 1200 side)"
      % (math.sqrt(d), 2 * math.degrees(math.atan(600 / math.sqrt(d)))))
