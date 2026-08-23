"""Room 17 (2F Hallway) -- ROUND V3: the CEILING and its recessed cans.

Owns exactly one piece: **Hall2F Ceiling**.  Nothing else in the room is
touched.

    python ceiling.py            # build + place
    python ceiling.py --dry      # build only, print size/bounds

----------------------------------------------------------------- the two bugs
1.  The round-3 ceiling (`r3.py piece_ceiling`) was authored against the OLD
    footprint -- an 8.1 x 16.7 rect anchored where local x=3.80 now is.  The
    re-traced room is a 10-vertex L whose WEST ALCOVE (local x 0..3.86,
    z 10.77..16.15) was simply not under it, so `p_doors2` looks up into open
    sky.  This build covers the union of

        the L                          (room 17's own polygon)
        the stair opening + shaft      (local x 7.61..11.92, z 6.81..16.89)

    because the lid over the stairwell is 8 ft above THIS slab in every photo
    -- room 28 is `is_void=1`, so nothing else draws it.  Expressed as two
    abutting rects, R1 (everything east of x=3.86) and R2 (the alcove), which
    is enough: for x >= 3.86 the union is the full z span.

2.  The fixtures were wrong.  Round 3 shipped three protruding saucers plus a
    0.92 ft surface-mount DRUM.  Every photograph shows small FLUSH wafers: a
    slim white trim ring set INTO the plane round a bright diffuser, with
    nothing hanging below.  Measured off the FAR pair in
    `hallway_looking_towards_stairs.jpg` -- the only pair that is not
    bloom-limited -- the aperture subtends 1.17 deg at 11.5 ft, i.e. ~0.235 ft
    including bloom.  Shipped: a 0.280 ft lit aperture inside a 0.336 ft trim
    that stands 0.011 ft (1/8 in) proud.  No drum anywhere, and no crown.

--------------------------------------------------------------- where they are
Solved, not guessed.  Every can in the photographs was found as a saturated
blob (`cceil/find.py`), then un-projected through the ROUND-V3 pose that photo
belongs to onto the ceiling plane at world y=26 (`cceil/unproj.py`).  A ceiling
point is uniquely determined by one pixel in one known camera, so each blob
gives one (x, z).

    photo                          blob px        -> local (x, z)
    hallway_looking_towards_stairs (225.5,130.2)      5.88, 7.17
      "                            (345.5,132.5)      8.32, 7.18
      "                            (227.7,167.1)      6.12, 4.22
      "                            (302.3,169.2)      8.21, 4.10
    hallway_with_white_runner_rug  (240.2, 50.7)      5.69, 7.19
      "                            (124.7, 50.7)      7.16, 7.20
    staircase_looking_up           (239.7, 18.8)     10.03,12.74

The two hallway photos are independent and they AGREE, to 0.02 ft, that there
is a row of cans at z = 7.18 -- the head of the stairs.  A joint least-squares
fit of the west can of that row over BOTH poses lands at (5.74, 7.19) with an
rms of 5.8 px: that is the centreline of the walking strip, (3.86+7.61)/2 =
5.735, to a hundredth of a foot.  That agreement is the check that the whole
un-projection is sound.

The EAST can of that row will NOT fit both poses (rms 29 px; p_stairs wants
x=8.32, p_runner wants x=7.16).  That is pose error, not measurement error --
the two hand-authored v3 poses are not exactly the two phone cameras, and this
round forbids editing them.  Shipped x = 7.75, near the least-squares optimum
(7.49).  What that buys, measured on the RENDER against the photo:

    pose      photo can px    render px   near-pair separation
    p_stairs  225.5 / 345.5   220.9/317.3   96 px vs the photo's 120
    p_runner  240.2 / 124.7   230.9/ 77.3  154 px vs the photo's 116

The other three cans land within 5 px of the photograph in p_stairs, which is
the check that the geometry is right and this one residual is the camera.

---------------------------------------------------------------- how bright
Metered off the photographs (`cceil/sample.py`), clean ceiling field only:

    hallway_with_white_runner_rug  near 156.9 sd 2.66  |d1| 0.46
                                   right 166.1 (inside a pool)
    hallway_looking_towards_stairs       148.5 sd 1.88  |d1| 0.34

and the pools are SUBTLE: a horizontal cut through the near-right can reads
148 baseline -> 254 core -> 192 -> 148 within ~2 px of the trim, and the wash
beyond it only lifts the field by 8-18 levels.  So this is a smooth matte
white plane with soft lobed pools, NOT the big radial gradients the round-3
piece drew.  The round-3 ceiling metered 140.5 with sd 0.91 and |d1| 0.03 --
too dark and algebraically flat.  Shipped, at 450x600: 150.4-156.9 mean,
sd 1.6-2.2, |d1| 0.08-0.27.  The |d1|/sd RATIO is 0.04-0.13 against the
photo's 0.18-0.23, and that gap is not closable here: the photo's is sensor
noise at pixel scale, and vertex tone on a 0.42 ft lattice cannot carry it.
Buying it with a 0.10 ft lattice would cost this piece ~600 KB for a matte
white plane, which the budget says is the wrong trade.  Reported, not chased.

The plane is one material with a per-vertex tone field (COLOR_0 multiplies
baseColor, so albedo is the one thing it can swing) over a fixed emissive
floor -- a downward face collects too little in this renderer to reach 150 on
albedo alone.  No crown moulding: every photograph shows a clean drywall
corner, so the plane runs straight into the wall.
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "circ"))

from ckit import *                                            # noqa: F401,F403
from roomkit.glb import Part                                  # noqa: E402

ROOM = 17
H = 8.0                       # wall height; the lid sits just under it
YC = H - 0.010                # the drywall plane

# footprint, room-local feet
AL_X, AL_Z0, AL_Z1 = 3.86, 10.77, 16.15      # the west alcove's east edge / z span
EX = 11.92                                    # east extent (room 17 == room 28)
DZ = 16.89                                    # south extent
M = 0.14                                      # bury this much in the walls

# ------------------------------------------------------------------ fixtures
# (x, z) room-local.  See the header for how each was solved.
CANS = [
    (5.80,  7.18),    # row S west  -- strip centreline, both photos agree
    (7.75,  7.18),    # row S east  -- lsq compromise, see the header
    (6.10,  4.18),    # row N west  -- hallway_looking_towards_stairs
    (8.22,  4.10),    # row N east  -- hallway_looking_towards_stairs
    (10.03, 12.74),   # over the stair shaft -- staircase_looking_up
    (1.93, 13.46),    # west alcove -- GUESSED: no photograph sees this ceiling
]

# Size, solved off the FAR pair in hallway_looking_towards_stairs (the near pair
# and both cans in the runner shot are bloom-limited, so their pixel width is
# not a size measurement -- canA at 8.6 ft and canE at 6.0 ft both meter 14-15
# px wide, which can only be bloom).  The far pair is 9 px at 11.5 ft = 1.17
# deg = 0.235 ft including some bloom, so the aperture is ~0.21 ft.  These are
# slim LED wafers, not 6 in cans: a 0.32 ft trim round a 0.24 ft aperture.
R_TRIM_O = 0.168      # trim ring outer  (4.0 in) -- a SLIM 0.4 in ring
R_TRIM_I = 0.136      # trim ring inner
R_LENS = 0.140        # lit aperture     (3.4 in)
D_TRIM = 0.010        # how far the trim stands proud -- 1/8 in, i.e. flush
D_LENS = 0.011        # the diffuser sits 0.001 ft BELOW the trim's face.
# It has to be the lowest thing on the fixture, not the highest: at 0.004
# recessed the trim's inner edge occludes the lit disc at grazing angles and
# the can renders as an empty white ring round a grey hole (seen in
# shots/ceiling_c_alcove.png).  A wafer's diffuser is flush with its trim.

# ----------------------------------------------------------------- materials
# Solved by two-point probe against the render (see the header): emissive is
# the value FLOOR the vertex field swings albedo on top of.  Round 3 shipped a
# CONE between trim and lens; at this aperture it renders as a DARK ANNULUS
# round the light -- the one thing no photograph shows -- so a wafer's flush
# diffuser replaces it.
CEILM = Material("h17ceilv3", "#ffffff", roughness=0.95, emissive="#6f6f6f",
                 double_sided=False)
TRIMW = Material("h17ctrim", "#ffffff", roughness=0.55, emissive="#d4d4d4",
                 double_sided=False)
LENSM = Material("h17clens", "#fffaf0", roughness=0.30, emissive="#fff2da",
                 emissive_strength=7.0, double_sided=False)
# TRIED AND REJECTED: the photo's aperture carries a bloom halo the renderer
# has no way to make, and COLOR_0 multiplies baseColor only, so it cannot lift
# a surface above the ceiling's own emissive floor.  Building that halo as a
# stack of five coplanar annuli stepping the emissive down came back as a
# textbook BULLSEYE at both hero poses -- exactly the artefact round 2 was
# failed for on its contact shadows.  Deleted.  The glow now comes from the
# ceiling's own vertex field, which is continuous; the only thing needed for
# that was somewhere to put it, hence _fan() below.

# ------------------------------------------------------------------ the field
TONE_LO = 0.613       # dimmest corner
TONE_HI = 1.000       # under a fixture
POOL_R = 2.90         # nominal pool radius, ft
PH = [0.0, 1.9, 3.4, 0.7, 2.6, 4.4]     # per-can lobe phase, so no two match

# the union polygon, for the edge falloff
UNION = [(AL_X, 0.0), (EX, 0.0), (EX, DZ), (AL_X, DZ),
         (AL_X, AL_Z1), (0.0, AL_Z1), (0.0, AL_Z0), (AL_X, AL_Z0)]


def _seg_dist(px, pz, a, b):
    ax, az = a
    bx, bz = b
    dx, dz = bx - ax, bz - az
    L2 = dx * dx + dz * dz
    t = 0.0 if L2 <= 0 else max(0.0, min(1.0, ((px - ax) * dx + (pz - az) * dz) / L2))
    return math.hypot(px - (ax + t * dx), pz - (az + t * dz))


def _edge_dist(x, z):
    return min(_seg_dist(x, z, UNION[i], UNION[(i + 1) % len(UNION)])
               for i in range(len(UNION)))


def _hash2(i, j):
    n = (i * 73856093) ^ (j * 19349663)
    n = (n ^ (n >> 13)) * 1274126177
    return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0


def _vnoise(x, z, cell):
    """Smooth value noise on a `cell`-ft lattice, 0..1."""
    fx, fz = x / cell, z / cell
    i, j = math.floor(fx), math.floor(fz)
    u, v = fx - i, fz - j
    u = u * u * (3 - 2 * u)
    v = v * v * (3 - 2 * v)
    a = _hash2(i, j) * (1 - u) + _hash2(i + 1, j) * u
    b = _hash2(i, j + 1) * (1 - u) + _hash2(i + 1, j + 1) * u
    return a * (1 - v) + b * v


def _pool(x, z):
    """Screen-blended, LOBED falloff -- deliberately not a clean radial ramp.

    A circular exp() pool on a matte plane was called out by round 2's critics
    ("perfect circular gradients").  Real downlight on drywall is elliptical
    (the fixture is not a point and the plane is not infinitely far), its
    shoulder is squarer than a Gaussian, and its rim wobbles.  So: an
    anisotropic radius stretched along the hall, a lobe modulation on theta at
    two frequencies, a shoulder exponent of 1.75, and a tight hot core just
    outside the trim ring.
    """
    keep = 1.0
    for i, (fx, fz) in enumerate(CANS):
        dx, dz = x - fx, (z - fz) * 0.86          # elongated along z (the hall)
        r = math.hypot(dx, dz)
        if r > POOL_R * 2.4:
            continue
        th = math.atan2(dz, dx)
        R = POOL_R * (1.0 + 0.155 * math.cos(3 * th + PH[i])
                          + 0.085 * math.cos(5 * th - 1.3 * PH[i]))
        # two terms that SUM to 1.0 at the fixture and never clip: a broad
        # wash, plus the tight bright ring the photo shows hard against the
        # trim.  Clipping the sum was what made the old field a flat white
        # blob a foot across instead of a gradient.
        p = (0.35 * math.exp(-1.35 * (r / R) ** 1.75)
             + 0.65 * math.exp(-(r / 0.50) ** 1.30))
        keep *= (1.0 - min(1.0, p))
    return 1.0 - keep


def _tone(x, z):
    lit = _pool(x, z)
    # the plane darkens slightly into every wall junction
    e = _edge_dist(x, z)
    lit *= 0.70 + 0.30 * min(1.0, e / 1.30)
    # very low frequency drift so the flat field is never algebraically flat
    lit += 0.045 * math.sin(x / 3.1 + 0.6) * math.sin(z / 4.7 + 2.2)
    s = TONE_LO + (TONE_HI - TONE_LO) * max(0.0, min(1.0, lit))
    # fine grain -- this is what carries |d1|; the photo's ceiling meters
    # sd 1.9-2.9 with |d1| 0.34-0.67 and a |d1|/sd ratio of 0.18-0.23, which is
    # sensor noise at pixel scale.  Vertex tone on a 0.26 ft lattice cannot
    # reach that ratio, and buying it with a 0.1 ft lattice would cost ~600 KB
    # on a matte white plane.  Two octaves at the lattice limit get sd and part
    # of |d1|; the rest is a renderer difference, reported not chased.
    s += (0.030 * (_vnoise(x, z, 0.78) - 0.5)
          + 0.024 * (_vnoise(x + 31.4, z + 17.7, 0.30) - 0.5))
    return max(0.50, min(1.0, s))


def _slab(m, x0, x1, z0, z1, y, step=0.42):
    nx = max(1, int(round((x1 - x0) / step)))
    nz = max(1, int(round((z1 - z0) / step)))
    verts, cols, tris = [], [], []
    for j in range(nz + 1):
        z = z0 + (z1 - z0) * j / nz
        for i in range(nx + 1):
            x = x0 + (x1 - x0) * i / nx
            verts.append((x, y, z))
            s = _tone(x, z)
            cols.append((s, s, s))
    for j in range(nz):
        for i in range(nx):
            p = j * (nx + 1) + i
            q, r_, s_ = p + 1, p + nx + 1, p + nx + 2
            tris += [(p, q, s_), (p, s_, r_)]      # wound to face DOWN
    m.add(Part(verts, tris, smooth=True, colors=cols), CEILM)


def _fan(m, cx, cz, r0=0.150, r1=1.70, rings=10, seg=20, y=None):
    """A fine radial patch of the SAME ceiling material, carrying the SAME tone
    function, laid 0.002 ft under the plane round each fixture.

    The plane's 0.26 ft lattice cannot resolve the tight bright ring the photo
    shows hard against every trim (148 -> 192 within two pixels of the rim), so
    that detail simply vanished into the cell.  This patch resolves it at
    0.04 ft near the fixture without paying for a fine lattice over 160 sq ft.
    Because both surfaces sample one continuous function, and the plane's cells
    are small where the patch ends, there is no step at the patch rim.
    """
    y = YC - 0.002 if y is None else y
    verts, cols, tris = [], [], []
    for k in range(rings + 1):
        # geometric spacing: dense at the rim of the trim, coarse far out
        f = k / float(rings)
        r = r0 + (r1 - r0) * (f ** 2.1)
        for i in range(seg):
            a = 2 * math.pi * i / seg
            x, z = cx + r * math.cos(a), cz + r * math.sin(a)
            verts.append((x, y, z))
            s = _tone(x, z)
            cols.append((s, s, s))
    for k in range(rings):
        for i in range(seg):
            p = k * seg + i
            q = k * seg + (i + 1) % seg
            r_ = p + seg
            s_ = q + seg
            tris += [(p, s_, q), (p, r_, s_)]      # wound to face DOWN
    m.add(Part(verts, tris, smooth=True, colors=cols), CEILM)


def _ring(m, mat, cx, cz, y, r0, r1, seg=20):
    """Flat annulus facing DOWN, smooth-shaded so the ring's 2*seg vertices are
    shared instead of duplicated per triangle -- a planar ring's normals are all
    (0,-1,0) anyway, and it is 4x smaller in the payload."""
    v, t = [], []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        v.append((cx + r0 * math.cos(a), y, cz + r0 * math.sin(a)))
        v.append((cx + r1 * math.cos(a), y, cz + r1 * math.sin(a)))
    for i in range(seg):
        a0, b0 = 2 * i, 2 * i + 1
        a1, b1 = (2 * i + 2) % (2 * seg), (2 * i + 3) % (2 * seg)
        t += [(a0, b0, b1), (a0, b1, a1)]
    m.add(Part(v, t, smooth=True), mat)


def _disc(m, mat, cx, cz, y, r, seg=20):
    v = [(cx, y, cz)] + [(cx + r * math.cos(2 * math.pi * i / seg), y,
                          cz + r * math.sin(2 * math.pi * i / seg))
                         for i in range(seg)]
    t = [(0, 1 + i, 1 + (i + 1) % seg) for i in range(seg)]
    m.add(Part(v, t, smooth=True), mat)


def _band(m, mat, cx, cz, y0, r0, y1, r1, seg=20):
    """A truncated cone shell between two rings, facing inward/down."""
    v, t = [], []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        v.append((cx + r0 * math.cos(a), y0, cz + r0 * math.sin(a)))
        v.append((cx + r1 * math.cos(a), y1, cz + r1 * math.sin(a)))
    for i in range(seg):
        a0, b0 = 2 * i, 2 * i + 1
        a1, b1 = (2 * i + 2) % (2 * seg), (2 * i + 3) % (2 * seg)
        t += [(a0, b0, b1), (a0, b1, a1)]
    m.add(Part(v, t), mat)


def _can(m, cx, cz):
    """A slim flush LED downlight.  Nothing hangs below the drywall plane but
    the 0.010 ft lip of the trim ring -- 1/8 in, which is what a wafer trim
    actually stands proud by."""
    yt = YC - D_TRIM
    # the fine tone patch that carries the bright ring against the trim
    _fan(m, cx, cz)
    # trim ring: flat white annulus, its face 1/8 in proud of the drywall
    _ring(m, TRIMW, cx, cz, yt, R_TRIM_I, R_TRIM_O, seg=20)
    # the lip's outer edge, so the ring is a board and not a decal
    _band(m, TRIMW, cx, cz, YC - 0.003, R_TRIM_O, yt, R_TRIM_O, seg=20)
    # the lit aperture, all but flush inside the ring
    _disc(m, LENSM, cx, cz, YC - D_LENS, R_LENS, seg=20)


def piece_ceiling():
    m = Model()
    # R1 -- everything east of the alcove: for x >= 3.86 the union of room 17
    # and the stair shaft is the full z span, so one rect does it.
    _slab(m, AL_X - M, EX + M, -M, DZ + M, YC)
    # R2 -- the west alcove, abutting R1 at x = 3.86 - M, dropped 0.005 ft so
    # the seam can never z-fight.
    _slab(m, -M, AL_X - M, AL_Z0 - M, AL_Z1 + M, YC - 0.005)
    for (cx, cz) in CANS:
        _can(m, cx, cz)
    return m


def main(dry=False):
    m = piece_ceiling()
    lo, hi = m.bounds()
    path = os.path.join(HERE, "glb", "hall2f_ceiling.glb")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    m.save(path)
    kb = os.path.getsize(path) / 1024.0
    print("  Hall2F Ceiling  bounds=%s..%s  %.1f KB"
          % (tuple(round(v, 2) for v in lo), tuple(round(v, 2) for v in hi), kb))
    if dry:
        return
    pos = ((lo[0] + hi[0]) / 2.0, lo[1], (lo[2] + hi[2]) / 2.0)
    from roomkit.place import place
    res = place("Hall2F Ceiling", path, ROOM, pos=pos, rot_y_deg=0.0, scale=1.0)
    print("  placed at %s  %s" % (tuple(round(v, 3) for v in pos), res["action"]))


if __name__ == "__main__":
    main(dry="--dry" in sys.argv)
