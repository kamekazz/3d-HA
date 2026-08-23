"""Room 17 (2F Hallway) -- ROUND 2 of the V3 gauntlet: the CEILING + its cans.

Owns exactly one piece: **Hall2F Ceiling**.

Round 1's ceiling failed on four counts (crit ceiling_a).  What follows is what
was measured, what was built, and where a finding was checked against the
photograph and found wrong.

-------------------------------------------------------------- the real bug
The round-1 plane was ONE material, `emissive #6f6f6f`, with a per-vertex tone
field on top.  COLOR_0 multiplies baseColor only -- it cannot touch emissive --
and on a DOWN-facing surface in this scene the lit albedo term is worth almost
nothing.  Calibrated (`ccal.py`, striped test plane, three shots):

    emissive   V at tone 1.0     slope dV/dtone
    #5a5a5a        145                 68
    #6f6f6f        163                 50
    #828282        179                 42

So a single emissive level can only swing ~35-45 levels, and round 1's field
used a fraction of that: the plane metered 145..156 (11 levels) where the
photograph's ceiling runs 99..255.  The pools were arithmetically present and
optically invisible.

The fix is a **7-level emissive ladder**: the target field is authored in
RENDER VALUE (0-255), and every triangle is assigned the ladder rung whose
reachable range contains it, with COLOR_0 interpolating inside that rung.
Consecutive rungs overlap by 6-32 levels, so the assignment is always possible
and the seams are continuous, not banded.  Total reach: V 86..206.

------------------------------------------------------------- what the photos say
Metered off `docs/v2 Hallway-jpg/` (450x600 originals, clean ceiling only):

  hallway_looking_towards_stairs   ceiling field 129..170, cores 255
  hallway_with_white_runner_rug    ceiling field 141..168, cores 254
  ceiling/wall junction            dips to **99-122** in a 1-2 px line, then
                                   the wall jumps to 174-188
  halo, radial, off the near can    +20 @0.17ft  +12 @0.36  +8 @0.45
                                    +5 @0.64   +3 @0.83   +1.5 @1.2

Three of round 1's findings did NOT survive that metering, and are reported
rather than built:

1. "The ceiling is the brightest surface in the frame, near-white, warmer than
   the walls."  It is not.  In `hallway_looking_towards_stairs` the ceiling
   meters 145.8 at (150,20) and 132.4 at (420,60) while the LEFT WALL meters
   174.7 and the far wall 166.1 -- the ceiling is 20-40 levels DARKER than the
   walls it meets, in the photograph.  Hue: ceiling B-R = +6, wall B-R = +7, so
   they are the same slightly-cool white, not warm-over-grey.  Round 1's render
   metered ceiling 145-156 against walls 165-183 -- a ceiling/wall ratio of
   0.84 against the photo's 0.83.  The VALUE was already right.  What made it
   read as an unlit slab was the absence of the other three things below, and
   raising it toward white would have made it worse, not better.
2. "OURS lost a ceiling step / soffit above the stair rail."  There is no
   soffit.  Vertical cuts through the ceiling at x = 260/280/300/320 in that
   photo are flat to +-2 levels for 40 px; the only edge on that side of the
   frame runs (347,161) -> (450,102), which is exactly where the ceiling meets
   the RIGHT WALL.  It reads as a step because the photo's junction is a dark
   line with a brightly washed wall under it.  So the break is real but it is
   the wall junction, and the fix is the junction line -- built below -- not a
   bulkhead.  (High-pass of both hallway shots: `crit/hp_st.png`, `hp_ru.png`.)
3. "The layout is too tidy, ours is a 2x2 grid, the photo pushes them to the far
   end."  Round 1's cans were solved by un-projecting the saturated blobs
   through the pose, and they land within 5 px of the photograph at three of
   four fixtures.  The photograph's four blobs really are two rows of two at
   local z 7.18 and z 4.15 -- both rows in the north block, nothing at all over
   the ten-foot walking strip.  The layout was already the photograph's.  The
   one real residual is the east can of the front row (render 317 px vs photo
   346 px), and that is the hand-authored pose, not the model: the same can
   fitted from `hallway_with_white_runner_rug` wants x=7.16 and from
   `hallway_looking_towards_stairs` x=8.32.  Kept at the least-squares 7.75.

------------------------------------------------------------------ what changed
* **Value field.**  Target authored in render-value units: a zone base (150 in
  the north block, falling to 136 over the open stair well where light escapes
  down the shaft, 141 in the alcove), plus per-can pools, times the junction
  falloff, plus grain.  Rendered swing 100..200 against round 1's 145..156.
* **The junction line.**  A perimeter band mesh hugging all eight boundary
  segments with rows at e = -0.14, 0, .035, .08, .16, .28, .45, .75, 1.2, 1.8 ft
  carries a 0.67x hairline at the wall face recovering to 1.0 over 1.6 ft.  The
  0.34 ft slab lattice cannot resolve that, which is why it is its own mesh.
* **Two fixture types.**  The near fitting in both hallway photos (local
  5.80,7.18) is a SURFACE-MOUNT disc: `crit/fx_f1.png` shows a cylindrical body
  standing proud with a dark contact line on the ceiling behind it.  The other
  five are recessed wafers with a real 0.024 ft reflector recess, so the
  shadowed cone wall shows as a dark crescent on the far side at oblique angles
  -- which is exactly what `crit/fx_f2.png` and `hp_ru.png` show and what round
  1 deleted.
* **Falloff with distance.**  Pool amplitude is per-fixture: 1.15x for the
  surface-mount, 1.0 for the north-block pair, 0.72 for the shaft and alcove
  wafers, and their lens emissive_strength steps 8 / 6.5 / 4.5.

    python ceiling2.py            # build + place
    python ceiling2.py --dry      # build only, print size/bounds
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "circ"))

from ckit import *                                            # noqa: F401,F403
from roomkit.glb import Part                                  # noqa: E402

ROOM = 17
H = 8.0
YC = H - 0.010                # the drywall plane

AL_X, AL_Z0, AL_Z1 = 3.86, 10.77, 16.15
EX = 11.92
DZ = 16.89
M = 0.14                      # bury this much in the walls

# stair well: room 28's footprint inside the union, local coords
WELL_X0, WELL_Z0 = 7.61, 6.81

# --------------------------------------------------------------- the ladder
# Fitted from ccal.py: Vmax(E) = 145 + 0.85*(E-90);  slope(E) = 110 - 0.52*E,
# where E is the 0-255 grey of the emissive factor and V is the rendered 0-255
# value of a DOWN-facing face at mid-hall depth with COLOR_0 = tone.
#     V(tone) = Vmax - slope*(1 - tone)
# CAL_DV is a measured correction applied after cycle 1 (see the report).
LADDER_E = [78, 92, 106, 120, 134, 148, 162]
CAL_DV = 0.0
T_LO = 0.30                   # lowest tone we will author (below this the
                              # sRGB->linear curve makes the step per unit tone
                              # coarse enough to band)


def _rung(i):
    e = LADDER_E[i]
    vmax = 145.0 + 0.85 * (e - 90.0) + CAL_DV
    slope = 110.0 - 0.52 * e
    return vmax, slope


RUNGS = [_rung(i) for i in range(len(LADDER_E))]
RANGES = [(v - s * (1 - T_LO), v) for (v, s) in RUNGS]

MATS = [Material("h17c%d" % i, "#ffffff", roughness=0.95,
                 emissive="#%02x%02x%02x" % (e, e, e), double_sided=False)
        for i, e in enumerate(LADDER_E)]


def _tone_for(i, v):
    vmax, slope = RUNGS[i]
    return max(T_LO, min(1.0, 1.0 - (vmax - v) / slope))


def _pick_rung(vs):
    """Lowest-cost rung whose reachable range contains every target in `vs`."""
    lo, hi = min(vs), max(vs)
    best, bestc = None, None
    for i, (a, b) in enumerate(RANGES):
        if a - 0.5 <= lo and hi <= b + 0.5:
            c = abs(((a + b) * 0.5) - (lo + hi) * 0.5)
            if bestc is None or c < bestc:
                best, bestc = i, c
    if best is not None:
        return best
    # target range wider than any rung -- take the rung closest to the mean and
    # let the ends clamp.  Only happens inside 0.1 ft of a lens.
    mid = (lo + hi) * 0.5
    return min(range(len(RANGES)),
               key=lambda i: abs((RANGES[i][0] + RANGES[i][1]) * 0.5 - mid))


def emit(m, verts, tris, vals):
    """Add a triangle soup whose per-vertex TARGET RENDER VALUES are `vals`,
    split across the emissive ladder."""
    buckets = {}
    for tri in tris:
        i = _pick_rung([vals[k] for k in tri])
        buckets.setdefault(i, []).append(tri)
    for i, tl in buckets.items():
        remap, vv, cc = {}, [], []
        out = []
        for tri in tl:
            t2 = []
            for k in tri:
                if k not in remap:
                    remap[k] = len(vv)
                    vv.append(verts[k])
                    s = _tone_for(i, vals[k])
                    cc.append((s, s, s))
                t2.append(remap[k])
            out.append(tuple(t2))
        m.add(Part(vv, out, smooth=True, colors=cc), MATS[i])


# ------------------------------------------------------------------ fixtures
# (x, z, kind, strength) -- kind 0 = surface-mount disc, 1 = recessed wafer.
# Positions solved in round 1 by un-projecting the saturated blobs through the
# ROUND-V3 poses; see the header.
CANS = [
    (5.80,  7.18, 0, 1.15),   # front row west  -- the surface-mount disc
    (7.75,  7.18, 1, 1.00),   # front row east  -- lsq compromise
    (6.10,  4.18, 1, 1.00),   # back row west
    (8.22,  4.10, 1, 1.00),   # back row east
    (10.03, 12.74, 1, 0.72),  # over the stair shaft (staircase_looking_up)
    (1.93, 13.46, 1, 0.72),   # west alcove -- GUESSED, no photo sees it
]

R_TRIM_O = 0.172              # wafer trim ring outer
R_TRIM_I = 0.145              # wafer trim ring inner  == cone mouth
R_CONE_T = 0.130              # cone throat, 0.024 ft up inside the ceiling
D_RECESS = 0.024
D_TRIM = 0.008                # how far the wafer trim stands proud

R_SM_BODY = 0.215             # surface-mount body radius
R_SM_LENS = 0.198
D_SM = 0.072                  # how far the body hangs below the drywall

TRIMW = Material("h17ctrim", "#ffffff", roughness=0.50, emissive="#d0d0d0",
                 double_sided=False)
SMSIDE = Material("h17csm", "#ffffff", roughness=0.42, emissive="#bdbdbd",
                  double_sided=False)
CONEM = Material("h17ccone", "#c8c8c8", roughness=0.85, emissive="#3a3a3a",
                 double_sided=True)
LENS = [Material("h17clens%d" % i, "#fffaf0", roughness=0.30,
                 emissive="#fff2da", emissive_strength=s, double_sided=False)
        for i, s in enumerate((8.0, 6.5, 4.5))]


def _lens_for(strength):
    return LENS[0] if strength > 1.1 else (LENS[1] if strength > 0.85 else LENS[2])


# ------------------------------------------------------------- the tone field
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
    fx, fz = x / cell, z / cell
    i, j = math.floor(fx), math.floor(fz)
    u, v = fx - i, fz - j
    u = u * u * (3 - 2 * u)
    v = v * v * (3 - 2 * v)
    a = _hash2(i, j) * (1 - u) + _hash2(i + 1, j) * u
    b = _hash2(i, j + 1) * (1 - u) + _hash2(i + 1, j + 1) * u
    return a * (1 - v) + b * v


def _smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def zone(x, z):
    """The base level of the plane, in render-value units, before the fixtures.

    Measured off `hallway_looking_towards_stairs`: the ceiling over the OPEN
    STAIR WELL (local x>7.61, z>6.81) meters 129-138 where the north-block
    ceiling meters 145-152 -- light escapes down the shaft and there is no floor
    under it to bounce off.  `hallway_with_white_runner_rug` agrees from the
    other end (141 on that side against 155-168 mid-hall).
    """
    v = 150.0
    # the open well: feather in over 1.6 ft from its two open boundaries
    fx = _smooth((x - WELL_X0) / 1.6)
    fz = _smooth((z - WELL_Z0) / 1.6)
    v -= 14.0 * fx * fz
    # deeper still once past the head of the flight
    v -= 4.0 * fx * _smooth((z - 10.65) / 2.2)
    # the far end of the walking strip and the alcove sit away from every can
    v -= 6.0 * _smooth((z - 9.2) / 5.0) * (1.0 - fx)
    v -= 5.0 * _smooth((AL_X - x) / 1.4)
    return v


def pools(x, z):
    """Lift from the fixtures.  Radial profile fitted to the photograph:
    +20 @0.17 ft, +12 @0.36, +8 @0.45, +5 @0.64, +3 @0.83, +1.5 @1.2, plus a
    broad lobe that is what actually makes the north end read as the lit end.
    """
    s = 0.0
    for i, (fx, fz, kind, k) in enumerate(CANS):
        dx, dz = x - fx, z - fz
        r = math.hypot(dx, dz * 0.88)          # slightly elongated down the hall
        if r > 5.2:
            continue
        th = math.atan2(dz, dx)
        wob = 1.0 + 0.13 * math.cos(3 * th + 1.7 * i) + 0.07 * math.cos(5 * th - i)
        s += k * 21.0 * math.exp(-((r / (0.55 * wob)) ** 1.3))
        s += k * 7.5 * math.exp(-((r / (2.30 * wob)) ** 1.7))
    return s


def contact(x, z):
    """The surface-mount disc parks a shadow ring on the drywall behind it --
    the 97-level arc visible in crit/fx_f1.png."""
    f = 1.0
    for (fx, fz, kind, k) in CANS:
        if kind != 0:
            continue
        r = math.hypot(x - fx, z - fz)
        if r < R_SM_BODY + 0.16:
            f *= 0.80 + 0.20 * _smooth((r - R_SM_BODY) / 0.16)
    return f


def target(x, z, e=None):
    """Desired RENDER VALUE at (x, z)."""
    v = zone(x, z) + pools(x, z)
    if e is None:
        e = _edge_dist(x, z)
    # the ceiling/wall junction: a hairline at 0.67 recovering over 1.6 ft
    v *= 0.67 + 0.33 * (max(0.0, min(1.0, e / 1.6)) ** 0.42)
    v *= contact(x, z)
    # very low-frequency drift, then two octaves of grain
    v *= 1.0 + 0.020 * math.sin(x / 3.1 + 0.6) * math.sin(z / 4.7 + 2.2)
    v += (5.2 * (_vnoise(x, z, 0.62) - 0.5)
          + 3.4 * (_vnoise(x + 31.4, z + 17.7, 0.26) - 0.5))
    return max(86.0, min(205.0, v))


# ------------------------------------------------------------------ meshing
def _slab(m, x0, x1, z0, z1, y, step=0.34):
    nx = max(1, int(round((x1 - x0) / step)))
    nz = max(1, int(round((z1 - z0) / step)))
    verts, vals, tris = [], [], []
    for j in range(nz + 1):
        z = z0 + (z1 - z0) * j / nz
        for i in range(nx + 1):
            x = x0 + (x1 - x0) * i / nx
            verts.append((x, y, z))
            vals.append(target(x, z))
    for j in range(nz):
        for i in range(nx):
            p = j * (nx + 1) + i
            q, r_, s_ = p + 1, p + nx + 1, p + nx + 2
            tris += [(p, q, s_), (p, s_, r_)]      # wound to face DOWN
    emit(m, verts, tris, vals)


# rows measured OUT from the wall face; -0.14 is buried in the wall
BAND_E = [-M, -0.02, 0.0, 0.035, 0.08, 0.16, 0.28, 0.45, 0.75, 1.2, 1.8]


def _band(m, y, along=0.55):
    """A strip hugging every boundary segment so the junction hairline gets
    resolved.  The 0.34 ft slab lattice cannot carry a 0.035 ft feature."""
    n = len(UNION)
    for s in range(n):
        ax, az = UNION[s]
        bx, bz = UNION[(s + 1) % n]
        dx, dz = bx - ax, bz - az
        L = math.hypot(dx, dz)
        ux, uz = dx / L, dz / L
        nx_, nz_ = -uz, ux                       # inward for a CCW ring
        cols = max(2, int(round(L / along)) + 1)
        verts, vals, tris = [], [], []
        for c in range(cols):
            t = c / (cols - 1.0)
            px, pz = ax + dx * t, az + dz * t
            for e in BAND_E:
                x, z = px + nx_ * e, pz + nz_ * e
                verts.append((x, y, z))
                # true distance to the WHOLE ring, so corners darken properly
                vals.append(target(x, z, e=max(0.0, _edge_dist(x, z))
                                   if e > 0 else 0.0))
        R = len(BAND_E)
        for c in range(cols - 1):
            for k in range(R - 1):
                p = c * R + k
                q, r_, s_ = p + 1, p + R, p + R + 1
                tris += [(p, s_, q), (p, r_, s_)]   # face DOWN
        emit(m, verts, tris, vals)


def _fan(m, cx, cz, y, r0, r1, rings, seg=24, gamma=2.0):
    """Fine radial patch of the same field round a fixture, so the tight halo
    (which lives inside 0.6 ft) is resolved without a fine lattice everywhere."""
    verts, vals, tris = [], [], []
    for k in range(rings + 1):
        f = k / float(rings)
        r = r0 + (r1 - r0) * (f ** gamma)
        for i in range(seg):
            a = 2 * math.pi * i / seg
            x, z = cx + r * math.cos(a), cz + r * math.sin(a)
            verts.append((x, y, z))
            vals.append(target(x, z))
    for k in range(rings):
        for i in range(seg):
            p = k * seg + i
            q = k * seg + (i + 1) % seg
            tris += [(p, q + seg, q), (p, p + seg, q + seg)]   # face DOWN
    emit(m, verts, tris, vals)


def _ring(m, mat, cx, cz, y, r0, r1, seg=24):
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


def _disc(m, mat, cx, cz, y, r, seg=24):
    v = [(cx, y, cz)] + [(cx + r * math.cos(2 * math.pi * i / seg), y,
                          cz + r * math.sin(2 * math.pi * i / seg))
                         for i in range(seg)]
    t = [(0, 1 + i, 1 + (i + 1) % seg) for i in range(seg)]
    m.add(Part(v, t, smooth=True), mat)


def _shell(m, mat, cx, cz, y0, r0, y1, r1, seg=24, flip=False):
    v, t = [], []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        v.append((cx + r0 * math.cos(a), y0, cz + r0 * math.sin(a)))
        v.append((cx + r1 * math.cos(a), y1, cz + r1 * math.sin(a)))
    for i in range(seg):
        a0, b0 = 2 * i, 2 * i + 1
        a1, b1 = (2 * i + 2) % (2 * seg), (2 * i + 3) % (2 * seg)
        if flip:
            t += [(a0, b1, b0), (a0, a1, b1)]
        else:
            t += [(a0, b0, b1), (a0, b1, a1)]
    m.add(Part(v, t, smooth=True), mat)


def _wafer(m, cx, cz, strength):
    """A flush LED wafer with a REAL 0.024 ft reflector recess, so the shadowed
    cone wall reads as a dark crescent on the far side at grazing angles."""
    yt = YC - D_TRIM
    _fan(m, cx, cz, YC - 0.003, R_TRIM_O, 1.30, rings=11, seg=24, gamma=2.1)
    _ring(m, TRIMW, cx, cz, yt, R_TRIM_I, R_TRIM_O)
    _shell(m, TRIMW, cx, cz, YC - 0.002, R_TRIM_O, yt, R_TRIM_O)
    _shell(m, CONEM, cx, cz, yt, R_TRIM_I, YC + D_RECESS, R_CONE_T)
    _disc(m, _lens_for(strength), cx, cz, YC + D_RECESS - 0.002, R_CONE_T)


def _surface_mount(m, cx, cz, strength):
    """The near fitting in both hallway photographs: a shallow cylinder standing
    proud of the drywall, blown-out lens, dark contact line on the ceiling
    behind it (that line is baked into the tone field by `contact`)."""
    yb = YC - D_SM
    _fan(m, cx, cz, YC - 0.003, R_SM_BODY, 1.45, rings=11, seg=28, gamma=2.1)
    _shell(m, SMSIDE, cx, cz, YC, R_SM_BODY, yb + 0.012, R_SM_BODY, seg=28)
    _shell(m, SMSIDE, cx, cz, yb + 0.012, R_SM_BODY, yb, R_SM_LENS, seg=28)
    _disc(m, _lens_for(strength), cx, cz, yb, R_SM_LENS, seg=28)


def piece_ceiling():
    m = Model()
    _slab(m, AL_X - M, EX + M, -M, DZ + M, YC)
    _slab(m, -M, AL_X - M + 0.10, AL_Z0 - M, AL_Z1 + M, YC - 0.004)
    _band(m, YC - 0.006)
    for (cx, cz, kind, k) in CANS:
        if kind == 0:
            _surface_mount(m, cx, cz, k)
        else:
            _wafer(m, cx, cz, k)
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
    print("  rungs:", ["%d:[%.0f,%.0f]" % (e, a, b)
                       for e, (a, b) in zip(LADDER_E, RANGES)])
    if dry:
        return
    pos = ((lo[0] + hi[0]) / 2.0, lo[1], (lo[2] + hi[2]) / 2.0)
    from roomkit.place import place
    res = place("Hall2F Ceiling", path, ROOM, pos=pos, rot_y_deg=0.0, scale=1.0)
    print("  placed at %s  %s" % (tuple(round(v, 3) for v in pos), res["action"]))


if __name__ == "__main__":
    main(dry="--dry" in sys.argv)
