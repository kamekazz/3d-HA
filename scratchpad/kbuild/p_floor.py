"""Kitchen Floor -- planks, grain and every contact shadow, in ONE image.

ROUND 4.  Round 3's floor was 1.26 MB: one box per plank plus ~64 000 raster
quads of contact shadow, quantised onto 15 translucent alpha steps.  It carried
two of the critic's remaining defects.

  * "The floor has no grain."  Plank interiors metered sd 3.7-8.6 against the
    photo's 7.4-11.2 in EVERY lighting zone -- all our variance was plank-to-
    plank tone steps, so it read as flat grey rectangles.  (The photo's floor sd
    is a constant ~11 in every zone; the 23.5 an earlier round chased came from
    a crop that mixed three lighting zones, and is not a material property.)
  * "Contact shadows too weak" -- a smooth 15% darkening (101.6 -> 120.0) that is
    invisible at dollhouse and plan distance.

Both are now baked into a single 952 x 1071 px greyscale image at 64 px/ft --
0.19 in per texel -- laid on TWO quads (the main rectangle and the bay
trapezoid).  Planks, butt joints, fibre and shadow are all in the one OPAQUE
layer, which is what makes the shadow reliable: a translucent decal over varying
planks has to win a depth sort against them, and an earlier round-4 pass proved
an alpha overlay can silently lose it and render nothing at all (verified by
painting it pure red and finding no red pixel anywhere in the room).  One image
also means the shadow can be as deep as the photo without costing a byte.

Named "Kitchen Floor" on purpose: objects.js SURFACE_RE makes anything with
"floor" in its name unpickable, so this room-sized plane cannot swallow the
room's clicks (verify with roomkit.check_pick).
"""
import numpy as np

from kcommon import *   # noqa
from kcommon import _rng
from ktex import TexModel, TexMaterial, png_gray, tex_plane, tex_quad
import kfield

PPF = 64                     # texels per foot
LEVELS = 64                  # tone quantisation; the grain dithers the steps

# Plank tone palette, sRGB albedo.  GAIN trims the whole set at once.
GAIN = 0.560
PLANKS = ["#5c6165", "#666b6f", "#70757a", "#7a7f84", "#83888d", "#8d9297"]
BASE_DARK = "#3c4044"        # the plank gaps: grout / butt joint

PITCH = 0.62                 # 7.4 in planks
GAP = 0.022

# ROUND 4b: 10.5 gave plank interiors sd 4.2-8.3 against the photo's 7.0-12.0
# (3 clean plank interiors in photo F, one per lighting zone: 12.0 / 9.1 / 7.0 --
# the sd really is ~constant with zone, so it is a material property and the
# "23.5" an earlier round chased was a crop that mixed zones).
GRAIN_AMP = 19.0             # render bytes, peak fibre
GRAIN_FINE = 4.2

# ROUND 4b: 0.32 measured 24.8% darkening at the island's visible contact edge
# against the brief's 34% target.  Also see `rects` below -- the island's rect
# was its CARCASE, and the counter overhangs it by 1.10 ft on the seating side,
# so the whole first band of the falloff was hidden under the counter.  That is
# the brief's "the ramp must extend outside the piece's footprint" defect in its
# other form: here the footprint that matters is the one you can SEE from above.
AO_MAX = 0.40                # deepest contact shadow, as a fraction of value

# Render response of a floor-facing surface, measured in round 3: albedo 65.5
# (the mid plank at GAIN 0.560) landed on 113.6 on open floor.  Used to apply
# the contact shadow in RENDER space and convert back, so "30% darker" means
# 30% darker on screen rather than 30% less albedo.
SLOPE, BIAS = 0.89, 55.3

Y_TOP = 0.026                # the plank surface


def _dim(hex_c, k):
    c = hex_c.lstrip("#")
    return [min(255, max(0, int(int(c[i:i + 2], 16) * k))) for i in (0, 2, 4)]


def _lum(rgb):
    return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]


def _zrange(x):
    """The bay narrows along both angled walls at x < 2.28."""
    if x >= XW_WEST:
        return ZW_NORTH, ZW_SOUTH
    t = (XW_WEST - x) * (1.16 / 2.28)
    return 3.35 + t, 11.16 - t


BAY_QUAD = [(XW_WEST, 3.37), (0.05, 4.53), (0.05, 9.98), (XW_WEST, 11.14)]


def plank_image():
    """Albedo image of the whole floor: planks, joints, grain, contact shadow."""
    nx = int(round(XW_EAST * PPF))
    nz = int(round(ZW_SOUTH * PPF))
    dark = _lum(_dim(BASE_DARK, GAIN))
    tone = np.full((nz, nx), dark)

    xs = (np.arange(nx) + 0.5) / PPF
    zs = (np.arange(nz) + 0.5) / PPF

    # ---- planks.  Same layout rule as round 3 (which the critic accepted):
    # 7.4 in boards running NORTH-SOUTH, butt joints staggered column to column,
    # and the tone drawn by a RANDOM WALK across a narrow six-step palette so no
    # board sits five steps from its neighbour.
    rnd = _rng(20260816)
    pal = [_lum(_dim(c, GAIN)) for c in PLANKS]
    idx = len(pal) // 2
    x = XW_EAST
    col = 0
    while x > 0.001:
        x0, x1 = max(0.0, x - PITCH), x
        zlo, zhi = _zrange(x0 + 0.001)
        z = zlo - (0.4 + rnd() * 3.4) if col else zlo
        ia = np.searchsorted(xs, x0 + GAP / 2)
        ib = np.searchsorted(xs, x1 - GAP / 2)
        while z < zhi:
            ln = 3.1 + rnd() * 3.4
            a, b = max(z, zlo), min(z + ln, zhi)
            r = rnd()
            step = -1 if r < 0.36 else (1 if r > 0.64 else 0)
            idx = max(0, min(len(pal) - 1, idx + step))
            if b - a > 0.25:
                ja = np.searchsorted(zs, a + GAP / 2)
                jb = np.searchsorted(zs, b - GAP / 2)
                tone[ja:jb, ia:ib] = pal[idx]
            z += ln
        x -= PITCH
        col += 1

    # ---- grain: dark fibre stretched ~14:1 up the board, plus the cathedral
    # figure.  This is the whole point of the rebuild -- round 3's plank
    # interiors were flat, so all the floor's variance sat at board scale.
    g = kfield.plank_grain(XW_EAST, ZW_SOUTH, PPF, 4242, amp=GRAIN_AMP,
                           fine=GRAIN_FINE)
    tone = tone + g * (tone > dark + 1)          # never in the joints

    # ---- contact shadows: the same exponential distance field as round 3 (its
    # smoothness was confirmed good), applied in render space and ~2x deeper.
    rects = [(5.25, 9.15, 5.30, 10.70, 0.70, 1.00),      # island COUNTER, not box
             (9.93, 12.92, 13.72, ZW_SOUTH, 0.50, 0.95),  # fridge
             (5.75, XW_EAST, ZW_NORTH, 2.20, 0.44, 0.92),  # peninsula
             (12.87, XW_EAST, 2.20, 10.60, 0.44, 0.92),   # east run
             (5.90, 12.95, 14.74, ZW_SOUTH, 0.44, 0.92),  # south run
             (12.80, XW_EAST, 4.30, 6.80, 0.34, 0.88)]    # range
    discs = [(4.51, 6.78, 0.58, 0.34, 0.92),             # stool north
             (4.51, 9.30, 0.58, 0.34, 0.92),             # stool south
             (1.15, 5.30, 0.58, 0.32, 0.92)]             # step bin
    ao = kfield.shadow_alpha(rects, discs, 0.0, XW_EAST, ZW_NORTH, ZW_SOUTH,
                             PPF, max_alpha=1.0) / 255.0

    r = SLOPE * tone + BIAS
    r = r * (1.0 - AO_MAX * ao)
    return np.clip((r - BIAS) / SLOPE, 0, 255)


def build():
    m = TexModel()
    mat = TexMaterial("plank", png_gray(plank_image(), levels=LEVELS),
                      roughness=0.72, mip=False)

    def uv(x, z):
        return (x / XW_EAST, z / ZW_SOUTH)

    tex_plane(m, mat, "+y", Y_TOP, XW_WEST, XW_EAST, ZW_NORTH, ZW_SOUTH,
              uvrect=(*uv(XW_WEST, ZW_NORTH), *uv(XW_EAST, ZW_SOUTH)))
    pts = [(x, Y_TOP, z) for (x, z) in BAY_QUAD]
    a, b, c = pts[0], pts[1], pts[2]
    if ((b[2] - a[2]) * (c[0] - a[0]) - (b[0] - a[0]) * (c[2] - a[2])) < 0:
        pts = pts[::-1]
    tex_quad(m, mat, pts, [uv(p[0], p[2]) for p in pts])

    # a thin dark skirt under the plank plane, so no sliver of the app's own slab
    # shows at a wall line or along the bay's two angled facets
    base = Material("plankbase", "#22262a", roughness=0.85)
    bx(m, base, XW_WEST, XW_EAST, 0.0, Y_TOP - 0.004, ZW_NORTH, ZW_SOUTH)
    m.add(prism([(XW_WEST, 3.35), (0.0, 4.51), (0.0, 10.0), (XW_WEST, 11.16)],
                Y_TOP - 0.004), base, at=(0, 0.0, 0))
    return m


if __name__ == "__main__":
    emit(build(), "Kitchen Floor", y=0.012)
