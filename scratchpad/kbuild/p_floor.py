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
# the render against the photo (photo A floor 115, photo F floor 86, sigma
# 24-32; the first round-2 build metered 160/30 at GAIN 0.90).
GAIN = 0.67
PLANKS = ["#4e5256", "#5d6166", "#6b6f74", "#7a7e83", "#8b8f94", "#9ba1a6"]
WEIGHTS = [0.18, 0.22, 0.22, 0.18, 0.13, 0.07]

BASE_DARK = "#303337"        # shows through the plank gaps: grout / butt joint

# Contact shadow ramp, as a multiplier on the mid plank tone.  The app's tone
# curve is steep down here -- an albedo at 0.74 of the floor's rendered 0.48 of
# it -- so a shadow that looks right in hex reads as a black pond on screen.
# The first round-2 build did exactly that; these are five gentle steps.
AO_STEPS = (0.960, 0.925, 0.890, 0.855, 0.815)
AO_MID = "#6b6f74"

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


def _ramp(reach):
    """Ring offsets from the outermost inward, one per AO_STEPS entry."""
    n = len(AO_STEPS)
    return [reach * (n - 1 - i) / (n - 1) for i in range(n)]


def ao_rect(m, mats, x0, x1, z0, z1, reach=0.55, clip=True):
    """Soft contact shadow under a rectangular footprint."""
    for i, g in enumerate(_ramp(reach)):
        a, b, c, d = (x0 - g, x1 + g, z0 - g, z1 + g)
        if clip:
            a, b, c, d = _clip(a, b, c, d)
        if b - a < 0.02 or d - c < 0.02:
            continue
        bx(m, mats[i], a, b, Y1 + 0.002 + i * 0.0012,
           Y1 + 0.0032 + i * 0.0012, c, d)


def ao_disc(m, mats, cx, cz, r, reach=0.42):
    for i, g in enumerate(_ramp(reach)):
        m.add(cylinder(r + g, 0.0012, seg=20), mats[i],
              at=(cx, Y1 + 0.002 + i * 0.0012, cz))


def build():
    m = Model()
    base = Material("plankbase", _dim(BASE_DARK, GAIN), roughness=0.85)
    mats = [_mat(c, f"pl{i}") for i, c in enumerate(PLANKS)]
    aomats = [Material(f"ao{i}", _dim(AO_MID, GAIN * k), roughness=0.76)
              for i, k in enumerate(AO_STEPS)]

    # ---- base layer (what the gaps show) -- built to the polygon so nothing
    # pokes out past the bay's angled walls into the next room
    bx(m, base, XW_WEST, XW_EAST, Y0, Y1 - 0.004, ZW_NORTH, ZW_SOUTH)
    bay = [(XW_WEST, 3.35), (0.0, 4.51), (0.0, 10.0), (XW_WEST, 11.16)]
    m.add(prism(bay, Y1 - 0.004), base, at=(0, Y0, 0))

    # ---- planks, running north-south like the photo's
    rnd = _rng(20260815)
    cum = []
    s = 0.0
    for w in WEIGHTS:
        s += w
        cum.append(s)

    def pick():
        r = rnd() * cum[-1]
        for i, c in enumerate(cum):
            if r <= c:
                return i
        return len(cum) - 1

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
            if b - a > 0.25:
                mat = mats[pick()]
                bx(m, mat, x0 + GAP / 2, x1 - GAP / 2, Y1 - 0.010, Y1,
                   a + GAP / 2, b - GAP / 2)
            z += ln
        x -= PITCH
        col += 1

    # ---- contact shadows: every piece that meets this floor ---------------
    ao_rect(m, aomats, 6.35, 8.95, 5.48, 10.52, reach=0.60)     # island box
    ao_disc(m, aomats, 4.51, 6.78, 0.62, reach=0.34)            # stool north
    ao_disc(m, aomats, 4.51, 9.30, 0.62, reach=0.34)            # stool south
    ao_rect(m, aomats, 9.93, 12.92, 13.72, ZW_SOUTH, reach=0.50)  # fridge
    ao_disc(m, aomats, 1.15, 5.30, 0.60, reach=0.30)            # step bin
    ao_rect(m, aomats, 5.75, XW_EAST, ZW_NORTH, 2.20, reach=0.42)
    ao_rect(m, aomats, 12.87, XW_EAST, 2.20, 10.60, reach=0.42)
    ao_rect(m, aomats, 5.90, 12.95, 14.74, ZW_SOUTH, reach=0.42)
    ao_rect(m, aomats, 12.80, XW_EAST, 4.30, 6.80, reach=0.34)  # range
    return m


if __name__ == "__main__":
    emit(build(), "Kitchen Floor", y=0.012)
