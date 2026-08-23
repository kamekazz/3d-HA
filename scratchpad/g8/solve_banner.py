"""Independent geometric solve for the KIES banner in Garage v3 1.jpg.

Round 2 shipped it at 0.73 W/H from a four-point guess.  This re-derives the
banner's four corners from intensity steps, checks them against the wall's own
vanishing point, and converts to feet by TWO independent scale references.
Everything it prints goes into rooms/7.json.
"""
import math
import numpy as np
from PIL import Image

SRC = r"C:\Users\Manuel\Desktop\Pro\3d HA\docs\photos-jpg\Garage v3 1.jpg"
im = Image.open(SRC).convert("RGB")
A = np.asarray(im).astype(np.float64)
L = 0.2126 * A[:, :, 0] + 0.7152 * A[:, :, 1] + 0.0722 * A[:, :, 2]
H, W = L.shape


def subpix_step(vals, lo, hi, rising):
    """Index of the strongest gradient in vals[lo:hi], parabola-refined."""
    g = np.diff(vals[lo:hi])
    if not rising:
        g = -g
    k = int(np.argmax(g))
    if 0 < k < len(g) - 1:
        a, b, c = g[k - 1], g[k], g[k + 1]
        den = (a - 2 * b + c)
        d = 0.5 * (a - c) / den if den != 0 else 0.0
    else:
        d = 0.0
    return lo + k + 0.5 + d, float(g[k])


def fit(pts):
    x = np.array([p[0] for p in pts], float)
    y = np.array([p[1] for p in pts], float)
    m, b = np.polyfit(x, y, 1)
    r = y - (m * x + b)
    return m, b, float(np.sqrt((r ** 2).mean()))


def robust_fit(pts, keep=0.75):
    m, b, _ = fit(pts)
    r = [abs(p[1] - (m * p[0] + b)) for p in pts]
    idx = np.argsort(r)[:max(4, int(len(pts) * keep))]
    return fit([pts[i] for i in idx])


print("=" * 74)
print("1. BANNER EDGES from intensity steps")
print("=" * 74)

# ---- top edge: the wall above is slightly darker/greyer than the vinyl ------
top = []
for x in range(410, 615, 4):
    v = L[500:560, x]
    y, g = subpix_step(v, 0, 60, rising=True)
    if g > 1.2:
        top.append((x, 500 + y))
mt, bt, rt = robust_fit(top)
print("  top    n=%3d  slope %+.4f  rms %.2f  y(400)=%.1f y(620)=%.1f"
      % (len(top), mt, rt, mt * 400 + bt, mt * 620 + bt))

# ---- bottom edge: vinyl hem against the wall -------------------------------
bot = []
for x in range(410, 615, 4):
    v = L[760:830, x]
    y, g = subpix_step(v, 0, 70, rising=False)
    if g > 1.2:
        bot.append((x, 760 + y))
mb, bb, rb = robust_fit(bot)
print("  bottom n=%3d  slope %+.4f  rms %.2f  y(400)=%.1f y(620)=%.1f"
      % (len(bot), mb, rb, mb * 400 + bb, mb * 620 + bb))

# ---- left / right edges ----------------------------------------------------
lef = []
for y in range(545, 780, 4):
    v = L[y, 380:420]
    x, g = subpix_step(v, 0, 40, rising=True)
    if g > 1.0:
        lef.append((y, 380 + x))
ml, bl, rl = robust_fit(lef)
rig = []
for y in range(570, 770, 4):
    v = L[y, 600:645]
    x, g = subpix_step(v, 0, 45, rising=False)
    if g > 1.0:
        rig.append((y, 600 + x))
mr, br, rr = robust_fit(rig)
print("  left   n=%3d  dx/dy %+.5f rms %.2f x(530)=%.1f x(800)=%.1f"
      % (len(lef), ml, rl, ml * 530 + bl, ml * 800 + bl))
print("  right  n=%3d  dx/dy %+.5f rms %.2f x(560)=%.1f x(790)=%.1f"
      % (len(rig), mr, rr, mr * 560 + br, mr * 790 + br))


def isect(m1, b1, m2, b2):
    x = (b2 - b1) / (m1 - m2)
    return x, m1 * x + b1


def isect_vh(mh, bh, mv, bv):
    """horizontal line y=mh x+bh  vs  vertical line x=mv y+bv."""
    y = (mh * bv + bh) / (1 - mh * mv)
    return mv * y + bv, y


TL = isect_vh(mt, bt, ml, bl)
TR = isect_vh(mt, bt, mr, br)
BL = isect_vh(mb, bb, ml, bl)
BR = isect_vh(mb, bb, mr, br)
print("\n  CORNERS  TL(%.1f,%.1f)  TR(%.1f,%.1f)  BR(%.1f,%.1f)  BL(%.1f,%.1f)"
      % (TL + TR + BR + BL))
uv, yv = isect(mt, bt, mb, bb)
print("  banner's own horizontal VP: (%.0f, %.0f)" % (uv, yv))

print()
print("=" * 74)
print("2. INDEPENDENT VANISHING POINTS on the same north wall")
print("=" * 74)
# the KIES wordmark baseline and cap line are horizontal lines ON the vinyl
ink = L[520:620, 440:680] < 120
pts_base, pts_cap = [], []
for i in range(ink.shape[1]):
    col = np.nonzero(ink[:, i])[0]
    if len(col) > 6:
        pts_base.append((440 + i, 520 + col.max()))
        pts_cap.append((440 + i, 520 + col.min()))
mk, bk, rk = robust_fit(pts_base, 0.6)
mc, bc, rc = robust_fit(pts_cap, 0.6)
print("  KIES baseline slope %+.4f rms %.2f  -> y at x=1689: %.0f"
      % (mk, rk, mk * 1689 + bk))
print("  KIES cap line slope %+.4f rms %.2f  -> y at x=1689: %.0f"
      % (mc, rc, mc * 1689 + bc))

# the wall/ceiling line of the north wall, west of the banner
wc = []
for x in range(150, 380, 4):
    v = L[420:500, x]
    y, g = subpix_step(v, 0, 80, rising=False)
    if g > 1.0:
        wc.append((x, 420 + y))
mw, bw, rw = robust_fit(wc)
print("  north wall/ceiling slope %+.4f rms %.2f -> y at x=1689: %.0f"
      % (mw, rw, mw * 1689 + bw))
