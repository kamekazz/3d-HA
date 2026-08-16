"""ROUND 4 -- the tone fields, as IMAGES.

Round 3's rasteriser could only draw marks as coarse as its cell (0.034 ft on
the island, 0.4 in), and to carry the photo's variance on a grid that coarse it
had to draw a handful of FAT veins.  The critic's measurement of that failure
was spatial, not tonal: high-pass energy above 9 px, photo 0.33-0.48, ours 0.25.

Everything here renders a field into a numpy image at 90-130 px/ft -- ten times
finer than the cell grid -- so the same variance is carried by a dense net of
hairlines instead, which is what photo F actually shows.

Authoring is in RENDER-VALUE space, not albedo.  This renderer's measured
response on our own surfaces is close to linear over the range that matters
(albedo 74 lands on 110, albedo 192 on 215), so `to_albedo()` inverts it and
the field parameters can be read straight off a photo crop.
"""
import numpy as np

# render = SLOPE * albedo + BIAS, fitted on this room's own probes in round 3
SLOPE, BIAS = 0.89, 44.1


def to_albedo(v):
    return np.clip((np.asarray(v, dtype=np.float64) - BIAS) / SLOPE, 0, 255)


# --------------------------------------------------------------- value noise
def _h(ix, iy, seed):
    ix = ix.astype(np.uint64)
    iy = iy.astype(np.uint64)
    h = (ix * np.uint64(374761393) + iy * np.uint64(668265263)
         + np.uint64(seed * 2246822519)) & np.uint64(0xFFFFFFFF)
    h = ((h ^ (h >> np.uint64(13))) * np.uint64(1274126177)) & np.uint64(0xFFFFFFFF)
    return ((h ^ (h >> np.uint64(16))) & np.uint64(0xFFFFFF)).astype(np.float64) / 0xFFFFFF


def _sm(t):
    return t * t * (3.0 - 2.0 * t)


def vnoise(U, W, seed):
    iu, iw = np.floor(U), np.floor(W)
    su, sw = _sm(U - iu), _sm(W - iw)
    iu = iu.astype(np.int64) + 4096
    iw = iw.astype(np.int64) + 4096
    a = _h(iu, iw, seed)
    b = _h(iu + 1, iw, seed)
    c = _h(iu, iw + 1, seed)
    d = _h(iu + 1, iw + 1, seed)
    return (a + (b - a) * su) * (1 - sw) + (c + (d - c) * su) * sw


def fbm(U, W, seed, octaves=4, gain=0.52, lac=2.13):
    s = np.zeros_like(U)
    tot, amp, f = 0.0, 1.0, 1.0
    for i in range(octaves):
        s += amp * vnoise(U * f, W * f, seed + i * 7919)
        tot += amp
        amp *= gain
        f *= lac
    return s / tot


def grid(w_ft, d_ft, ppf):
    """Pixel-centre coordinate arrays in FEET for a w x d ft surface."""
    nx = max(4, int(round(w_ft * ppf)))
    ny = max(4, int(round(d_ft * ppf)))
    x = (np.arange(nx) + 0.5) / ppf
    y = (np.arange(ny) + 0.5) / ppf
    return np.meshgrid(x, y)            # (Y-major, X-minor) -> image rows = y


# --------------------------------------------------------------- the wisp net
def wisp_net(X, Y, ppf, seed, scale=2.4, warp=0.30, warp_scale=0.9,
             layers=((1.0, 0.030, 1.00),
                     (2.05, 0.019, 0.78),
                     (4.20, 0.012, 0.60),
                     (8.60, 0.008, 0.42))):
    """A dense fine net of thin low-contrast filaments, in 0..1.

    Built as the LEVEL SET of a domain-warped noise field: |n - 0.5| small
    traces a set of closed, branching, curving contours -- which is what stone
    veining physically is (a crack network), and unlike round 3's random walk it
    is connected everywhere and never runs as a straight diagonal.

    The distance to the contour is normalised by the field's own GRADIENT, so
    `width` is a real width in FEET and a low-frequency layer draws a line just
    as thin as a high-frequency one.  Without that the coarse layers come out as
    fat soft blurs -- which is precisely round 3's defect reappearing.

    `layers` is (frequency, width_ft, amplitude): four octaves give the photo's
    hierarchy of a few broader wisps with a much finer net between them.
    """
    wu = (fbm(X * warp_scale, Y * warp_scale, seed + 555, 3) - 0.5) * warp
    wv = (fbm(X * warp_scale, Y * warp_scale, seed + 777, 3) - 0.5) * warp
    out = np.zeros_like(X)
    sp = 1.0 / ppf
    for k, (f, width, amp) in enumerate(layers):
        n = fbm((X + wu) * scale * f, (Y + wv) * scale * f, seed + 31 * k, 3)
        gy, gx = np.gradient(n, sp)
        d = np.abs(n - 0.5) / (np.hypot(gx, gy) + 1e-9)      # feet to the vein
        t = d / width
        out = np.maximum(out, amp * np.exp(-t * t))
    # A uniformly dense net reads as a contour map.  Photo F has open white
    # ground between the busy passages, and individual wisps fade in and out
    # along their length, so the net is modulated by two slow fields.
    dens = np.clip((fbm(X * 0.75, Y * 0.75, seed + 313, 3) - 0.30) * 2.6, 0, 1)
    along = 0.55 + 0.75 * fbm(X * 2.6, Y * 2.6, seed + 404, 3)
    return out * (0.20 + 0.80 * dens) * np.clip(along, 0, 1.3)


# --------------------------------------------------------------- stone
def quartz(w_ft, d_ft, ppf, seed, ground=216.0, cloud=5.0, vein=44.0,
           grain=3.2, scale=2.4, layers=None):
    """Photo F's island top: a near-white ground under a dense hairline net.

    Returns a RENDER-VALUE image.  `vein` is how far the darkest wisp core sits
    below the ground -- the photo's deepest wisps are only ~45 bytes down and
    most of the net is far shallower, which is why round 3's six fat branches
    read as cracks and stains rather than as stone.
    """
    X, Y = grid(w_ft, d_ft, ppf)
    kw = {} if layers is None else {"layers": layers}
    v = np.full(X.shape, ground)
    v += (fbm(X * 0.55, Y * 0.55, seed + 11, 4) - 0.5) * 2.0 * cloud
    v -= wisp_net(X, Y, ppf, seed, scale=scale, **kw) * vein
    v += (fbm(X * 9.0, Y * 9.0, seed + 91, 2) - 0.5) * 2.0 * grain
    return v


# --------------------------------------------------------------- floor grain
def plank_grain(w_ft, d_ft, ppf, seed, amp=9.0, fine=3.0):
    """Wood grain as a MODULATION in render bytes, mean 0.

    The photo's plank interiors meter sd 7.4-11.2 in every lighting zone; ours
    metered 3.7-8.6 because all our variance was plank-to-plank tone steps.
    Grain is strongly anisotropic -- long fibres up the board -- so the noise is
    stretched ~14:1 along the plank (which runs north-south, i.e. +Y here).
    """
    X, Y = grid(w_ft, d_ft, ppf)
    g = (fbm(X * 26.0, Y * 1.9, seed, 4) - 0.5) * 2.0
    g += (fbm(X * 58.0, Y * 4.4, seed + 13, 3) - 0.5) * 1.2
    g /= 1.6
    # a few darker cathedral streaks, the visible figure of the board
    fig = fbm(X * 7.0, Y * 0.9, seed + 202, 3)
    g -= np.clip((fig - 0.62) * 3.0, 0, 1) * 0.55
    g = g * amp
    g += (fbm(X * 70.0, Y * 30.0, seed + 41, 2) - 0.5) * 2.0 * fine
    return g


# --------------------------------------------------------------- rug
def loop_weave(w_ft, d_ft, ppf, seed, ground=182.0, loop=132.0, density=0.46,
               pitch_in=0.40):
    """A neutral loop-pile mat: a pale ground carrying dense small dark loops.

    Round 3 built ~1200 rotated loop quads and the critic measured the result
    warm (R-B +6.9) and too coarse (sd 56.7 against photo F's honest 39.0) --
    "warm confetti".  Round 2's finer NEUTRAL speckle read closer to a woven mat.
    So: strictly neutral, a mark about a third of round 3's, and the loops laid
    on a jittered offset lattice in visible ROWS, which is what a 2.5x crop of
    photo F actually shows -- not an even pepper and not confetti.
    """
    X, Y = grid(w_ft, d_ft, ppf)
    p = pitch_in / 12.0
    ru, rv = X / p, Y / (p * 0.92)
    j = np.floor(rv)
    ru = ru + (j % 2) * 0.5
    i = np.floor(ru)
    ii = (i + 4096).astype(np.int64)
    jj = (j + 4096).astype(np.int64)
    jx = (_h(ii, jj, seed) - 0.5) * 0.55
    jy = (_h(ii, jj, seed + 17) - 0.5) * 0.55
    du = (ru - i - 0.5 - jx) / 0.60
    dv = (rv - j - 0.5 - jy) / 0.46
    mark = np.clip(1.0 - np.hypot(du, dv), 0, 1) ** 0.55

    # only some cells carry a dark loop, and the density drifts across the mat
    dens = density + (fbm(X * 1.7, Y * 1.7, seed + 5, 3) - 0.5) * 0.34
    on = (_h(ii, jj, seed + 31) < dens).astype(np.float64)
    depth = 0.55 + 0.45 * _h(ii, jj, seed + 47)

    v = np.full(X.shape, ground)
    v -= mark * on * depth * loop
    v -= (1.0 - mark) * 10.0                       # shadow between the loops
    v += (fbm(X * 3.1, Y * 0.6, seed + 71, 3) - 0.5) * 26.0   # weave rows
    v += (fbm(X * 0.9, Y * 0.9, seed + 91, 3) - 0.5) * 14.0   # soft soiling
    return v


# --------------------------------------------------------------- soft shadows
def shadow_alpha(rects, discs, x0, x1, z0, z1, ppf, max_alpha=0.62, mask=None):
    """One contact-shadow field for a whole room, as an ALPHA image.

    Round 3's was a smooth 15% darkening (101.6 -> 120.0 over ~110 px), which
    the critic could not see at dollhouse or plan distance.  Same smooth
    exponential falloff -- that part was confirmed good -- but roughly twice the
    depth, and free now that it costs one quad instead of 64 000 raster cells.
    """
    nx = max(4, int(round((x1 - x0) * ppf)))
    ny = max(4, int(round((z1 - z0) * ppf)))
    xs = x0 + (np.arange(nx) + 0.5) / ppf
    zs = z0 + (np.arange(ny) + 0.5) / ppf
    X, Z = np.meshgrid(xs, zs)
    v = np.zeros_like(X)
    for (ax0, ax1, az0, az1, reach, s) in rects:
        dx = np.maximum(np.maximum(ax0 - X, 0.0), X - ax1)
        dz = np.maximum(np.maximum(az0 - Z, 0.0), Z - az1)
        d = np.hypot(dx, dz)
        v = np.maximum(v, s * np.exp(-(d / reach) ** 1.55))
    for (cx, cz, r, reach, s) in discs:
        d = np.maximum(0.0, np.hypot(X - cx, Z - cz) - r)
        v = np.maximum(v, s * np.exp(-(d / reach) ** 1.55))
    if mask is not None:
        v = v * mask(X, Z)
    return np.clip(v, 0, 1) * max_alpha * 255.0
