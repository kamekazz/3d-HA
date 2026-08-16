"""Kitchen Floor -- the plank floor AND every contact shadow in the room.

Two critic defects live here.

  * "The floor is not a material -- measured tonal spread sigma 9.5 against the
    photo's 27.3."  The app's slab is one flat colour under a faint wood
    texture; the photo is 7-8 in planks in five distinct greys with visible butt
    joints.  So the slab gets covered with real plank geometry: a dark base
    layer showing through 0.036 ft gaps as grout/butt lines, and one box per
    plank with a tone drawn from a five-step grey palette plus jitter.

  * "Nothing has a contact shadow -- island, stools, fridge, trash can all
    float."  The app renders NO shadows for generated geometry, so every piece
    that meets the floor gets a soft dark decal baked in here, the same trick
    the master bedroom's Rug uses for the bed.  Three nested tones make the
    falloff read as soft rather than as a printed rectangle.

Named "Kitchen Floor" on purpose: objects.js SURFACE_RE makes anything with
"floor" in its name unpickable, so this room-sized plane cannot swallow the
room's clicks (verify with roomkit.check_pick).
"""
from kcommon import *   # noqa
from kcommon import _rng

# Plank tone palette, sRGB.  GAIN trims the whole set at once after metering
# the render against the photo.
#
# ROUND 3 -- REGRESSION FIX.  Round 1 metered sigma 9.5 and read plastic; round 2
# over-corrected to 127.7 / sd 23.7 against the photo's 114.1 / sd 16.2, and the
# critic's words were "near-white planks now abut charcoal in a patchwork the
# real uniform grey oak never does".  Two changes: the palette is much NARROWER
# (a 1.42 spread instead of 1.94), and neighbouring columns are drawn by a
# RANDOM WALK over the palette rather than independently, so no plank can sit
# five steps away from the one beside it.  Aiming at the photo's numbers, not
# past them.
GAIN = 0.560
PLANKS = ["#5c6165", "#666b6f", "#70757a", "#7a7f84", "#83888d", "#8d9297"]

BASE_DARK = "#3c4044"        # shows through the plank gaps: grout / butt joint

# Contact shadows are no longer nested rectangles -- see Shadows in kraster.py.
# This is the ramp the smooth field is quantised onto: 12 steps of a gentle
# multiplier on the mid plank tone.  The app's tone curve is steep down here, so
# a shadow that looks right in hex reads as a black pond on screen.
AO_N = 15
AO_MAX_ALPHA = 0.44          # how dark the deepest contact shadow gets

PITCH = 0.62                 # 7.4 in planks
GAP = 0.020
Y0, Y1 = 0.0, 0.026          # base slab / plank top


def _dim(hex_c, k):
    c = hex_c.lstrip("#")
    return "#" + "".join(f"{min(255, max(0, int(int(c[i:i+2], 16) * k))):02x}"
                         for i in (0, 2, 4))


def _mat(hex_c, name):
    # no emissive: the floor faces up and collects the sky/hemisphere directly,
    # which is exactly why round 1's floor came out 40 points too bright.
    return Material(name, _dim(hex_c, GAIN), roughness=0.72)


# bay facets: at x < 2.28 the room narrows along both angled walls
def _zrange(x):
    if x >= XW_WEST:
        return ZW_NORTH, ZW_SOUTH
    t = (XW_WEST - x) * (1.16 / 2.28)
    return 3.35 + t, 11.16 - t


def _clip(x0, x1, z0, z1):
    """Keep an AO decal inside the room so it never pokes through a wall."""
    x0, x1 = max(x0, 0.02), min(x1, XW_EAST - 0.02)
    if x1 > XW_WEST:
        x0 = max(x0, XW_WEST + 0.02) if x1 - XW_WEST > 0.2 else x0
    return x0, x1, max(z0, 0.02), min(z1, ZW_SOUTH - 0.02)


def _inside(x, z):
    """The room polygon, for clipping the shadow raster at the bay."""
    if x >= XW_WEST:
        return ZW_NORTH + 0.01 <= z <= ZW_SOUTH - 0.01
    if x < 0.02:
        return False
    zlo, zhi = _zrange(x)
    return zlo + 0.02 <= z <= zhi - 0.02


def build():
    m = Model()
    base = Material("plankbase", _dim(BASE_DARK, GAIN), roughness=0.85)
    mats = [_mat(c, f"pl{i}") for i, c in enumerate(PLANKS)]
    # translucent, NOT opaque: see Shadows.bake
    aomats = shadow_ramp(AO_N, "#21252a", AO_MAX_ALPHA)

    # ---- base layer (what the gaps show) -- built to the polygon so nothing
    # pokes out past the bay's angled walls into the next room
    bx(m, base, XW_WEST, XW_EAST, Y0, Y1 - 0.004, ZW_NORTH, ZW_SOUTH)
    bay = [(XW_WEST, 3.35), (0.0, 4.51), (0.0, 10.0), (XW_WEST, 11.16)]
    m.add(prism(bay, Y1 - 0.004), base, at=(0, Y0, 0))

    # ---- planks, running north-south like the photo's.  Tone is a RANDOM WALK
    # across the palette so adjacent boards stay within a step or two of each
    # other -- round 2 drew them independently and the critic read the result as
    # a light/dark patchwork.
    rnd = _rng(20260816)
    idx = len(PLANKS) // 2

    x = XW_EAST
    col = 0
    while x > 0.001:
        x0 = max(0.0, x - PITCH)
        x1 = x
        zlo, zhi = _zrange(x0 + 0.001)
        # stagger the butt joints column to column so no two line up
        z = zlo - (0.4 + rnd() * 3.4) if col else zlo
        while z < zhi:
            ln = 3.1 + rnd() * 3.4
            a, b = max(z, zlo), min(z + ln, zhi)
            r = rnd()
            step = -1 if r < 0.36 else (1 if r > 0.64 else 0)
            idx = max(0, min(len(PLANKS) - 1, idx + step))
            if b - a > 0.25:
                bx(m, mats[idx], x0 + GAP / 2, x1 - GAP / 2, Y1 - 0.010, Y1,
                   a + GAP / 2, b - GAP / 2)
            z += ln
        x -= PITCH
        col += 1

    # ---- contact shadows: ONE smooth field over the whole floor -------------
    # Round 2 baked five nested hard-edged rectangles per object and the critic
    # called them "bullseye decals painted on the planks, worse than no shadow".
    # Shadows.bake rasterises an exponential distance falloff through the same
    # quantiser the stone uses: round corners, irregular contours, no rings.
    sh = (Shadows()
          .rect(6.35, 8.95, 5.48, 10.52, reach=0.52)            # island box
          .disc(4.51, 6.78, 0.58, reach=0.30)                   # stool north
          .disc(4.51, 9.30, 0.58, reach=0.30)                   # stool south
          .rect(9.93, 12.92, 13.72, ZW_SOUTH, reach=0.44)       # fridge
          .disc(1.15, 5.30, 0.58, reach=0.28)                   # step bin
          .rect(5.75, XW_EAST, ZW_NORTH, 2.20, reach=0.38)      # peninsula
          .rect(12.87, XW_EAST, 2.20, 10.60, reach=0.38)        # east run
          .rect(5.90, 12.95, 14.74, ZW_SOUTH, reach=0.38)       # south run
          .rect(12.80, XW_EAST, 4.30, 6.80, reach=0.30))        # range
    sh.bake(m, aomats, Y1, 0.0, XW_EAST, ZW_NORTH, ZW_SOUTH, cell=0.062,
            mask=_inside, lift=0.003)
    return m


if __name__ == "__main__":
    emit(build(), "Kitchen Floor", y=0.012)
