"""Dining Floor -- the area rug plus EVERY contact shadow in the room.

Two critic findings drive this file:

  * "nothing had a contact shadow, so everything floated" -- so the table, all
    eight chairs, the buffet, the side table and both plants get one;
  * "contact shadows baked as five nested hard-edged outlines read as bullseye
    decals" -- so they are ONE smooth distance field with an exponential
    falloff, quantised through kraster.raster into flat quads and drawn in
    TRANSLUCENT tones, which darken the carpet underneath instead of painting
    over it.  There is no ring anywhere in it.

The wall-to-wall carpet is a coarse loop-pile tone field over the app slab: the
slab alone renders essentially flat, and photo A's carpet measures sd 16.2.  The
rug sits 0.02 ft above it, lighter and finer, the way the photos have it.
"""
import math

from dcommon import (Model, Material, ramp, raster, fbm, khash, Shadows,
                     shadow_ramp, inside, emit, quad,
                     RUG, RUG_TOP, SHADOW_Y, FLOOR_TOP, TABLE_C, TABLE_W, TABLE_D,
                     CHAIRS, CHAIR_W, CHAIR_D, BUF_C, BUF_W, BUF_D,
                     FIG, SNAKE, SIDE_T)

RX0, RX1, RZ0, RZ1 = RUG
BORDER = 0.42

# The photo's rug is a cream basket-weave loop pile: blocks of parallel ribs
# that alternate direction block to block.  Rendered as a tone lattice rather
# than real ribs -- at dollhouse distance the tone is what reads, and round 1's
# real rib geometry cost 40k triangles for the same look.
RUG_N = 12
RUG_TONES = ramp("#6a645a", "#8d8578", RUG_N, "rug", roughness=0.93)
BIND = Material("rugbind", "#7b7469", roughness=0.92)

CELL = 0.115
BLOCK = 0.345          # 3 cells


def rug_tone(u, w):
    """Woven loop pile: a soft cloud, a block lattice, and a rib inside each
    block running the way that block's weave goes."""
    bu, bw = int(math.floor(u / BLOCK)), int(math.floor(w / BLOCK))
    flip = (bu + bw) & 1
    t = 0.63
    t += (fbm(u * 0.42, w * 0.42, 5501, 4) - 0.5) * 0.30     # slow tone drift
    t += (khash(bu, bw, 77) - 0.5) * 0.10                    # block to block
    rib = ((u if flip else w) % BLOCK) / BLOCK
    t += (math.sin(rib * math.pi * 3.0) * 0.5 + 0.5 - 0.5) * 0.26
    t += (fbm(u * 6.5, w * 6.5, 991, 2) - 0.5) * 0.11        # fibre grain
    return max(0, min(RUG_N - 1, int(t * RUG_N)))


# The wall-to-wall carpet.  The app slab alone renders flat (sd ~4) against
# photo A's 16.2, and "matched the value but not the spread" is a documented
# critic failure -- so a coarse loop-pile tone field goes over it.  Aim is the
# PHOTO's spread, not the biggest spread available: overshooting to a light/dark
# patchwork failed a sibling room just as hard as being flat did.
CARP_N = 10
CARP_TONES = ramp("#5b554d", "#6c6559", CARP_N, "carp", roughness=0.95)
CCELL = 0.15
CBLOCK = 0.45


def carpet_tone(u, w):
    bu, bw = int(math.floor(u / CBLOCK)), int(math.floor(w / CBLOCK))
    t = 0.52
    t += (fbm(u * 0.30, w * 0.30, 3307, 4) - 0.5) * 0.14      # slow drift
    t += (khash(bu, bw, 41) - 0.5) * 0.11                     # tuft to tuft
    t += (fbm(u * 5.2, w * 5.2, 613, 2) - 0.5) * 0.12         # fibre grain
    return max(0, min(CARP_N - 1, int(t * CARP_N)))


def build_carpet(m):
    raster(m, CARP_TONES, "+y", FLOOR_TOP, 0.0, 14.64, 0.0, 13.12, CCELL,
           lambda x, z: None if not inside(x, z) else carpet_tone(x, z),
           lift=0.0)


def build_rug(m):
    ix0, ix1 = RX0 + BORDER, RX1 - BORDER
    iz0, iz1 = RZ0 + BORDER, RZ1 - BORDER
    # binding: a slightly proud band all round, which is what casts the rug's
    # own thin edge shadow in the photos
    for (x0, x1, z0, z1) in ((RX0, RX1, RZ0, iz0), (RX0, RX1, iz1, RZ1),
                             (RX0, ix0, iz0, iz1), (ix1, RX1, iz0, iz1)):
        m.add(quad((x0, RUG_TOP, z1), (x1, RUG_TOP, z1),
                   (x1, RUG_TOP, z0), (x0, RUG_TOP, z0)), BIND)
    raster(m, RUG_TONES, "+y", RUG_TOP - 0.004, ix0, ix1, iz0, iz1, CELL,
           rug_tone, lift=0.0)


# --------------------------------------------------------------------- shadows
AO_N = 9
AO = shadow_ramp(AO_N, color="#22252a", max_alpha=0.56, name="dao")


def build_shadows(m):
    s = Shadows()
    # table: a broad soft pool under the whole top, plus a tight one under each
    # pedestal where the weight actually lands
    cx, cz = TABLE_C
    s.rect(cx - TABLE_W / 2 + 0.35, cx + TABLE_W / 2 - 0.35,
           cz - TABLE_D / 2 + 0.30, cz + TABLE_D / 2 - 0.30,
           reach=0.95, strength=0.46)
    for sx in (-1, 1):
        s.rect(cx + sx * 1.85 - 0.80, cx + sx * 1.85 + 0.80,
               cz - 0.72, cz + 0.72, reach=0.30, strength=1.0)
    # chairs
    for (x, z, _yaw) in CHAIRS:
        s.rect(x - CHAIR_W / 2 + 0.10, x + CHAIR_W / 2 - 0.10,
               z - CHAIR_D / 2 + 0.10, z + CHAIR_D / 2 - 0.10,
               reach=0.30, strength=0.86)
    # buffet, side table, plants
    s.rect(BUF_C - BUF_W / 2, BUF_C + BUF_W / 2, 0.05, BUF_D,
           reach=0.40, strength=1.0)
    s.rect(SIDE_T[0] - 0.62, SIDE_T[0] + 0.62, SIDE_T[1] - 0.62, SIDE_T[1] + 0.62,
           reach=0.26, strength=0.84)
    s.disc(FIG[0], FIG[1], 0.62, reach=0.34, strength=0.92)
    s.disc(SNAKE[0], SNAKE[1], 0.46, reach=0.28, strength=0.86)

    s.bake(m, AO, SHADOW_Y, 0.0, 14.64, 0.0, 13.12, cell=0.115,
           mask=lambda x, z: inside(x, z))


if __name__ == "__main__":
    m = Model()
    build_carpet(m)
    build_rug(m)
    build_shadows(m)
    emit(m, "Dining Floor", y=FLOOR_TOP)
