"""Generate `frontend/textures/plank_grey.png` -- the grey wood-look LVP tile
used by room 17's floor slab.

WHY A NEW APP TEXTURE AND NOT MORE GEOMETRY
-------------------------------------------
The photographs' clean floor meters mean|d1| 3.2-7.4 (horizontal) at their own
450x600, on a patch whose near field runs about 0.013 ft per pixel.  Reaching
that with vertex colour needs sample spacing near 0.02 ft; over room 17's
113 sq ft that is a quarter of a million vertices.  It cannot be done inside a
300 KB GLB, and `roomkit.glb` has no image-texture API.

But the ROOM SLAB does take an image texture -- `rooms.floor_texture`, keyed
into `frontend/js/textures.js`.  That is the documented lever for floor
surfaces ("Wall and floor *surfaces* are yours ... texture keys in
frontend/js/textures.js") and it is where the fine scale has to come from.
The shipped `wood` tile cannot serve: it is 256 px over 2.2 ft (0.0086 ft per
texel), it has NO lengthwise variation at all (every column is constant down
y bar +-4 of noise), no butt joints, no knots, and a 15%-dark 2 px seam every
plank that reads as hard stripes.  So this adds a NEW key rather than editing
a tile six other rooms use.

WHAT IT CARRIES              (the GLB wear layer carries the rest -- floor3.py)
  * 12 planks of 8 in over an 8 ft repeat, 96 px/ft.
  * A micro-bevelled long edge: 4 px of groove with a 1 px catch-light either
    side, ~12% deep, not the shipped tile's flat 15% two-pixel bar.
  * Staggered butt joints, two per plank column per repeat, spacings 3.3-4.7 ft
    (LVP is 48 in stock), each a tone STEP between segments plus a hairline.
  * Per-segment base value, sd ~5%, so a near-white board can sit beside a
    brown-grey one.
  * Three grain octaves, all periodic (FFT gaussian, so the tile wraps):
    wire-brush streaks (sx 0.6 px, sy 34), broken short figure (2.2, 10),
    and cathedral swirl (7, 150).  Per-plank figure strength, so some boards
    are nearly plain.
  * Mineral streaks and knots.
"""
import os
import numpy as np
from PIL import Image

OUT = r"C:\Users\Manuel\Desktop\Pro\3d HA\frontend\textures\plank_grey.png"

PX = 768
FEET = 8.0                 # one repeat = 8 ft  -> TEXTURE_PRESETS size
PPF = PX / FEET            # 96 px per foot
PLANKS = 12
PW = PX // PLANKS          # 64 px = 0.6667 ft = 8 in boards

# The GLB wear layer over this tile is 44% opaque, so only ~62% of the tile's
# contrast survives into the render (measured: tile 9.3% relative sd -> render
# 6.7%).  BOOST is the pre-compensation, and BASE drops with it so the +25%
# excursions do not clip at 255.
BASE = 188.0               # near-white; rooms.floor_color tints it
BOOST = float(os.environ.get("H17_BOOST", 1.50))

rng = np.random.default_rng(20260822)


def pblur(a, sx, sy):
    """Periodic gaussian blur (circular convolution via FFT) -> tiles exactly."""
    fx = np.fft.fftfreq(a.shape[1])
    fy = np.fft.fftfreq(a.shape[0])
    k = np.exp(-2.0 * np.pi ** 2 * ((fx[None, :] * sx) ** 2 + (fy[:, None] * sy) ** 2))
    return np.real(np.fft.ifft2(np.fft.fft2(a) * k))


def unit(a):
    return (a - a.mean()) / max(a.std(), 1e-9)


def build():
    Y, X = np.mgrid[0:PX, 0:PX]
    v = np.zeros((PX, PX))

    # ---- three grain octaves, periodic --------------------------------
    n = rng.standard_normal((PX, PX))
    g_brush = unit(pblur(n, 0.45, 30.0))      # wire-brushed fine streaks
    g_med = unit(pblur(rng.standard_normal((PX, PX)), 1.3, 62.0))
    g_short = unit(pblur(rng.standard_normal((PX, PX)), 2.4, 11.0))
    g_cath = unit(pblur(rng.standard_normal((PX, PX)), 8.0, 70.0))

    # per-plank figure strength: some boards are nearly plain
    fig = np.ones((PX, PX))
    seg_val = np.zeros((PX, PX))
    joint = np.zeros((PX, PX))

    for p in range(PLANKS):
        x0, x1 = p * PW, (p + 1) * PW
        fig[:, x0:x1] = 0.45 + 1.25 * rng.random()

        # two butt joints per column per repeat, spacings d and PX-d
        j0 = int(rng.integers(0, PX))
        d = int(rng.integers(int(3.30 * PPF), int(4.70 * PPF)))
        js = sorted([j0 % PX, (j0 + d) % PX])

        # segment id down the column, and a value per segment
        sid = np.zeros(PX, dtype=int)
        sid[js[0]:js[1]] = 1
        sv = np.zeros(PX)
        vals = [np.clip(rng.normal(0.0, 0.036), -0.082, 0.082) for _ in range(2)]
        # never let the two halves of one column land on the same value
        if abs(vals[0] - vals[1]) < 0.022:
            vals[1] += 0.032 * (1 if vals[1] >= vals[0] else -1)
        for s in range(2):
            sv[sid == s] = vals[s]
        seg_val[:, x0:x1] = sv[:, None]

        # the joint itself: a hairline, plus a 1 px feather
        for j in js:
            for dy, amt in ((-1, -0.035), (0, -0.105), (1, -0.075), (2, -0.025)):
                joint[(j + dy) % PX, x0:x1] += amt

    v += seg_val
    v += fig * (0.056 * g_brush + 0.028 * g_med + 0.022 * g_short) + 0.036 * g_cath
    v += joint

    # ---- mineral streaks: narrow, long, dark, wandering ---------------
    for _ in range(46):
        px_ = int(rng.integers(0, PX))
        y0 = int(rng.integers(0, PX))
        ln = int(rng.integers(int(1.2 * PPF), int(5.0 * PPF)))
        amp = -rng.uniform(0.045, 0.115)
        w = rng.uniform(0.8, 2.1)
        for i in range(ln):
            yy = (y0 + i) % PX
            xx = px_ + 2.0 * np.sin(i / 46.0 + px_)
            fade = min(1.0, min(i, ln - i) / (0.25 * ln + 1))
            for dx in range(-3, 4):
                c = int(round(xx)) + dx
                v[yy, c % PX] += amp * fade * np.exp(-((c - xx) / w) ** 2)

    # ---- knots --------------------------------------------------------
    for _ in range(9):
        cx = float(rng.integers(0, PX))
        cy = float(rng.integers(0, PX))
        r = rng.uniform(2.5, 6.5)
        dx = ((X - cx + PX / 2) % PX) - PX / 2
        dy = ((Y - cy + PX / 2) % PX) - PX / 2
        d = np.hypot(dx, dy / 1.9)
        v += -0.22 * np.exp(-(d / r) ** 2)
        v += 0.018 * np.exp(-((d - 2.1 * r) / (1.5 * r)) ** 2)

    # ---- the micro-bevelled long edge ---------------------------------
    xm = X % PW
    edge = np.zeros((PX, PX))
    prof = {0: -0.125, 1: -0.115, 2: -0.055, PW - 1: -0.125, PW - 2: -0.070,
            3: 0.030, PW - 3: 0.022}
    for k, a in prof.items():
        edge[xm == k] += a
    v += edge

    # ---- fine sensor-scale speckle ------------------------------------
    v += rng.standard_normal((PX, PX)) * 0.030

    img = BASE * (1.0 + BOOST * v)
    out = np.clip(np.rint(img), 0, 255).astype(np.uint8)
    return out


if __name__ == "__main__":
    a = build()
    Image.fromarray(a, mode="L").save(OUT, optimize=True)
    l = a.astype(float)
    print(f"wrote {OUT}  {os.path.getsize(OUT)/1024:.0f} KB  {PX}x{PX} over {FEET} ft")
    print(f"  mean {l.mean():6.1f}  sd {l.std():5.2f} ({100*l.std()/l.mean():.1f}%)"
          f"  |d1|h {np.abs(np.diff(l,axis=1)).mean():5.2f}"
          f"  |d1|v {np.abs(np.diff(l,axis=0)).mean():5.2f}")
    # what a 450x600-photo-scale view of the near field would meter
    q = np.asarray(Image.fromarray(a).resize((PX // 2, PX // 2), Image.BOX), float)
    print(f"  at half res: sd {q.std():5.2f}  |d1|h {np.abs(np.diff(q,axis=1)).mean():5.2f}"
          f"  |d1|v {np.abs(np.diff(q,axis=0)).mean():5.2f}")
