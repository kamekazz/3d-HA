"""Room 17 (2F Hallway) -- V3 ROUND 2 WAVE A: **Hall2F Ceiling** + its fittings.

Owns exactly one piece.  Everything here is measured off
`docs/v2 Hallway-jpg/hallway_looking_towards_stairs.jpg` and
`hallway_with_white_runner_rug.jpg` (450x600 originals) and off calibration
renders of this very room (`ccal3.py`, uniform-plane sweep).

----------------------------------------------------------------- calibration
`ccal3.py` paints the whole ceiling one flat (emissive, COLOR_0) pair and meters
three clean boxes in `p_stairs`.  The three boxes always agree to <0.1 of a
level, which is the important result: **a down-facing plane in this scene gets
no positional light variation at all**.  Every gradient the eye is supposed to
read has to be authored.

    emissive   tone 1.0     tone 0.6 / 0.5
    none          97.0        26.7 (t=.5)
    #404040      125.7
    #808080      178.0       158.0 (t=.5)
    #c0c0c0      214.7
    #ffffff      233.0       231.0 (t=.5)
    #ffffff x2   245.0

So one emissive level reaches at most ~V+0 .. V-swing(E), and swing collapses
from 78 levels at E=0 to 2 at E=255.  The field is therefore authored in RENDER
VALUE and split across an emissive ladder, with COLOR_0 interpolating inside
each rung (`emit`).

------------------------------------------------------------- what the photos say
* Ceiling field: 135..162.  Walls 157..193.  So the ceiling is NOT the brightest
  surface -- it meters 20-35 levels BELOW the walls it meets, in both hallway
  photographs.  Round 1's critic said the opposite; the numbers say otherwise
  and this build keeps the photo's ratio (~0.85).
* Every fixture core clips at 250-255.  The "dimmer far cans" are not dimmer,
  they are smaller: blob w14 h9 near vs w9 h4 far, i.e. exactly the 0.62 the
  perspective demands.
* Halo off the near surface-mount, converted to ceiling feet:
  +72 @0.26 ft, +40 @0.36, +21 @0.46, +11 @0.56, +4 @0.66, +1 @0.81 -- a fast
  e-fold of ~0.19 ft, plus a broad ~+9 lobe out to 1.5 ft.
* Ceiling/wall junction (x=420 vertical cut): 134 in the field, drifting to 122
  over ~14 px, then a hard dip to **94** in 5 px, then the wall climbs from 95
  to 148.  Ratio at the line 0.70.
* No soffit.  The "ceiling step" round 1's critic saw is that junction: the
  darkest line in the frame with a brightly washed wall immediately under it.
  Vertical cuts through the ceiling either side of it are flat to +-2 levels.
* Fixture layout, un-projected through the ROUND-V3 poses onto y=26.0:
      p_stairs  (225.5,130.2)->(5.88,7.17)   (345.4,132.6)->(8.32,7.17)
                (227.7,167.3)->(6.12,4.20)   (302.2,169.4)->(8.22,4.08)
      p_runner  (240.1, 50.6)->(5.69,7.19)   (125.0, 50.8)->(7.16,7.20)
  Two rows of two, at z 7.18 and z 4.14, both pairs pushed WEST of the block's
  centreline (7.89) -- asymmetric, as round 1's critic asked for.  The east can
  of the front row is the one place the two photographs disagree (8.32 vs 7.16);
  p_stairs is believed because its two rows agree with each other.

    python ceil3.py           # build + place
    python ceil3.py --dry     # build only
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
YC = H - 0.010

AL_X, AL_Z0, AL_Z1 = 3.86, 10.77, 16.15
EX, DZ = 11.92, 16.89
M = 0.14                       # bury this much inside the walls
WELL_X0, WELL_Z0 = 7.61, 6.81

# ---------------------------------------------------------------- the ladder
# V(E) with COLOR_0 = 1, from ccal3.  Interpolated in LINEAR emissive space,
# because that is what the exporter writes and what the tone-mapper sees.
CAL_E = [0, 64, 88, 112, 128, 136, 168, 192, 208, 255]
CAL_V = [97.0, 125.7, 145.3, 165.3, 178.0, 184.0, 203.3, 214.7, 220.7, 233.0]
CAL_SW = [78.0, 52.0, 38.5, 27.1, 22.3, 18.5, 9.8, 6.5, 4.6, 2.2]
STR_V = {1.0: 233.0, 1.2: 236.6, 1.5: 240.7, 2.0: 245.0, 2.5: 247.2, 3.0: 249.0}
TONE_GAMMA = 3.3               # albedo falls as tone**this
T_LO = 0.22


def _s2l(u):
    return u / 12.92 if u <= 0.04045 else ((u + 0.055) / 1.055) ** 2.4


def _interp(xs, ys, x):
    if x <= xs[0]:
        return ys[0]
    for i in range(len(xs) - 1):
        if x <= xs[i + 1]:
            t = (x - xs[i]) / (xs[i + 1] - xs[i])
            return ys[i] + t * (ys[i + 1] - ys[i])
    return ys[-1]


_CAL_EL = [_s2l(e / 255.0) for e in CAL_E]


def rung_vmax(e, strength=1.0):
    if strength != 1.0:
        return _interp(sorted(STR_V), [STR_V[k] for k in sorted(STR_V)], strength)
    return _interp(_CAL_EL, CAL_V, _s2l(e / 255.0))


def rung_swing(e, strength=1.0):
    if strength != 1.0:
        return 2.0
    return _interp(_CAL_EL, CAL_SW, _s2l(e / 255.0))


# E byte, emissive strength.  Chosen so consecutive reachable ranges overlap
# from V=104 all the way to V=250 (printed by --dry).
LADDER = [(72, 1.0), (88, 1.0), (104, 1.0), (120, 1.0), (136, 1.0),
          (152, 1.0), (164, 1.0), (176, 1.0), (188, 1.0), (200, 1.0),
          (216, 1.0), (232, 1.0), (248, 1.0), (255, 1.2), (255, 1.5), (255, 2.0), (255, 2.5)]

RUNGS = [(rung_vmax(e, s), rung_swing(e, s)) for (e, s) in LADDER]
RANGES = [(v - sw * (1.0 - T_LO ** TONE_GAMMA), v) for (v, sw) in RUNGS]

MATS = [Material("h17c%d" % i, "#ffffff", roughness=0.95,
                 emissive="#%02x%02x%02x" % (e, e, e),
                 emissive_strength=s, double_sided=False)
        for i, (e, s) in enumerate(LADDER)]


def _tone_for(i, v):
    vmax, sw = RUNGS[i]
    if sw <= 0.01:
        return 1.0
    f = 1.0 - (vmax - v) / sw            # = tone**gamma
    f = max(T_LO ** TONE_GAMMA, min(1.0, f))
    return f ** (1.0 / TONE_GAMMA)


def _pick_rung(vs):
    lo, hi = min(vs), max(vs)
    best, bestc = None, None
    for i, (a, b) in enumerate(RANGES):
        if a - 0.4 <= lo and hi <= b + 0.4:
            c = abs(((a + b) * 0.5) - (lo + hi) * 0.5)
            if bestc is None or c < bestc:
                best, bestc = i, c
    if best is not None:
        return best
    mid = (lo + hi) * 0.5
    return min(range(len(RANGES)),
               key=lambda i: abs((RANGES[i][0] + RANGES[i][1]) * 0.5 - mid))


def emit(m, verts, tris, vals):
    """Triangle soup whose per-vertex TARGET RENDER VALUES are `vals`."""
    buckets = {}
    for tri in tris:
        buckets.setdefault(_pick_rung([vals[k] for k in tri]), []).append(tri)
    for i, tl in buckets.items():
        remap, vv, cc, out = {}, [], [], []
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


# ----------------------------------------------------------------- fixtures
# (x, z, kind, amp) -- kind 0 surface-mount puck, 1 flush wafer.
CANS = [
    (5.88, 7.17, 0, 1.00),    # front row west -- the proud puck (both photos)
    (8.28, 7.17, 1, 0.96),    # front row east
    (6.12, 4.20, 1, 0.92),    # back row west
    (8.22, 4.08, 1, 0.92),    # back row east
    (9.90, 12.60, 1, 0.72),   # over the shaft (staircase_looking_up)
    (1.93, 13.46, 1, 0.80),   # west alcove -- GUESSED, no photo sees it
]

R_SM_BODY = 0.225             # puck body radius   (~5.4 in dia)
R_SM_LENS = 0.208
D_SM = 0.070                  # how far it hangs below the drywall
R_WF_TRIM = 0.196             # wafer outer
R_WF_LENS = 0.170
D_RECESS = 0.006              # nearly flush: at 11 deg the lens must stay visible

LENS_HOT = Material("h17clens", "#ffffff", roughness=0.30, emissive="#fff6e8",
                    emissive_strength=3.0, double_sided=False)
LENS_MID = Material("h17clens2", "#ffffff", roughness=0.30, emissive="#fff6e8",
                    emissive_strength=2.0, double_sided=False)
TRIMW = Material("h17ctrim", "#ffffff", roughness=0.55, emissive="#dcdcdc",
                 double_sided=False)
# the puck's cylindrical side reads 85-136 in the photograph: it is the one
# genuinely DARK thing on the ceiling, and it is what proves the fitting has
# depth.  Non-emissive white on a vertical face lands near there.
SMSIDE = Material("h17csm", "#8a8a8a", roughness=0.60, double_sided=False)


# --------------------------------------------------------------- tone field
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


def _sm(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def zone(x, z):
    """Base level in render-value units, before the fixtures."""
    v = 151.0
    fx = _sm((x - WELL_X0) / 1.7)
    fz = _sm((z - WELL_Z0) / 1.7)
    v -= 13.0 * fx * fz                      # light escapes down the shaft
    v -= 4.0 * fx * _sm((z - 10.65) / 2.4)
    v -= 6.0 * _sm((z - 9.0) / 5.5) * (1.0 - fx)   # far end of the walking strip
    v -= 2.0 * _sm((AL_X - x) / 1.4)               # alcove, no can this side
    return v


def pools(x, z):
    """Fitted to the photograph: a tight e-fold of 0.19 ft carrying +72 at the
    lens rim, plus a broad +9 lobe.  Amplitude falls with the fixture's own
    output, not with distance from the camera (the camera does that for us)."""
    s = 0.0
    for i, (fx, fz, kind, k) in enumerate(CANS):
        dx, dz = x - fx, z - fz
        r = math.hypot(dx, dz)
        if r > 4.4:
            continue
        rim = R_SM_BODY if kind == 0 else R_WF_TRIM
        th = math.atan2(dz, dx)
        wob = 1.0 + 0.055 * math.cos(3 * th + 1.9 * i)
        s += k * 96.0 * math.exp(-max(0.0, r - rim) / 0.200)
        s += k * 10.0 * math.exp(-((r / (1.50 * wob)) ** 1.7))
    return s


def contact(x, z):
    """The puck parks its own shadow on the drywall it is screwed to."""
    f = 1.0
    for (fx, fz, kind, k) in CANS:
        if kind != 0:
            continue
        r = math.hypot(x - fx, z - fz)
        if r < R_SM_BODY + 0.13:
            f *= 0.74 + 0.26 * _sm((r - R_SM_BODY) / 0.13)
    return f


def junction(e):
    """Photo: flat field, a slow -9% over ~1.3 ft, then a hard dip to 0.70 in
    the last 0.09 ft.  Round 1 ramped the whole thing smoothly over 1.6 ft, so
    the line itself never got dark enough to read."""
    if e <= 0.115:
        return 0.67
    if e <= 0.40:
        return 0.67 + 0.22 * _sm((e - 0.115) / 0.285)
    return 0.89 + 0.11 * _sm((e - 0.40) / 1.75)


def target(x, z, e=None):
    v = zone(x, z) + pools(x, z)
    if e is None:
        e = _edge_dist(x, z)
    v *= junction(e)
    v *= contact(x, z)
    v *= 1.0 + 0.018 * math.sin(x / 3.1 + 0.6) * math.sin(z / 4.7 + 2.2)
    v += (6.4 * (_vnoise(x, z, 0.63) - 0.5)
          + 5.0 * (_vnoise(x + 31.4, z + 17.7, 1.70) - 0.5)
          + 3.2 * (_vnoise(x + 8.1, z - 5.3, 3.60) - 0.5))
    return max(100.0, min(246.0, v))


# ------------------------------------------------------------------ meshing
def _axis(lo, hi, step, walls):
    """Sample list from lo..hi at `step`, densified near each wall coordinate in
    `walls` so the junction hairline gets its own rows without a fine lattice
    everywhere."""
    n = max(1, int(round((hi - lo) / step)))
    xs = [lo + (hi - lo) * i / n for i in range(n + 1)]
    for w in walls:
        for d in (0.0, 0.045, 0.10, 0.185, 0.30, 0.50, 0.80, 1.25):
            for s in (-1, 1):
                v = w + s * d
                if lo - 1e-6 <= v <= hi + 1e-6:
                    xs.append(v)
    xs = sorted(set(round(v, 4) for v in xs))
    out = [xs[0]]
    for v in xs[1:]:
        if v - out[-1] > 0.012:
            out.append(v)
    return out


def _grid(m, xs, zs, y):
    verts, vals = [], []
    for z in zs:
        for x in xs:
            verts.append((x, y, z))
            vals.append(target(x, z))
    nx = len(xs)
    tris = []
    for j in range(len(zs) - 1):
        for i in range(nx - 1):
            p = j * nx + i
            q, r_, s_ = p + 1, p + nx, p + nx + 1
            tris += [(p, q, s_), (p, s_, r_)]          # wound to face DOWN
    emit(m, verts, tris, vals)


def _fan(m, cx, cz, y, r0, r1, rings, seg=26, gamma=2.2):
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


def _ring(m, mat, cx, cz, y, r0, r1, seg=26):
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


def _disc(m, mat, cx, cz, y, r, seg=26):
    v = [(cx, y, cz)] + [(cx + r * math.cos(2 * math.pi * i / seg), y,
                          cz + r * math.sin(2 * math.pi * i / seg))
                         for i in range(seg)]
    t = [(0, 1 + i, 1 + (i + 1) % seg) for i in range(seg)]
    m.add(Part(v, t, smooth=True), mat)


def _shell(m, mat, cx, cz, y0, r0, y1, r1, seg=26, flip=False):
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


def _wafer(m, cx, cz, amp):
    """Flush LED wafer.  The recess is only 0.006 ft: at the 11-degree grazing
    angle these are seen from, round 1's 0.024 ft recess hid the whole lens
    behind the cone wall, which is why three of four fittings rendered as empty
    white rings with no light in them."""
    yt = YC - 0.004
    yl = YC - 0.013                       # the lens is the LOWEST element, so a
                                          # 11-degree grazing view can never lose
                                          # it behind the trim -- round 1 recessed
                                          # it 0.024 ft UP and three of four cans
                                          # rendered as empty rings.
    _fan(m, cx, cz, YC - 0.006, R_WF_TRIM, 1.60, rings=10, seg=22, gamma=2.4)
    _ring(m, TRIMW, cx, cz, yt, R_WF_LENS - 0.006, R_WF_TRIM)
    _shell(m, TRIMW, cx, cz, yt, R_WF_LENS - 0.006, yl, R_WF_LENS)
    _disc(m, LENS_HOT if amp > 0.9 else LENS_MID, cx, cz, yl, R_WF_LENS)


def _puck(m, cx, cz, amp):
    """Surface-mount disc: a shallow cylinder standing proud, blown lens, and a
    dark side wall -- the 85-136 line the photograph shows across the top of the
    near fitting."""
    yb = YC - D_SM
    _fan(m, cx, cz, YC - 0.006, R_SM_BODY, 1.75, rings=11, seg=26, gamma=2.4)
    _shell(m, SMSIDE, cx, cz, YC, R_SM_BODY, yb + 0.016, R_SM_BODY, seg=30)
    _shell(m, TRIMW, cx, cz, yb + 0.016, R_SM_BODY, yb, R_SM_LENS, seg=30)
    _disc(m, LENS_HOT, cx, cz, yb, R_SM_LENS, seg=30)


STEP = 0.30                    # the open field
ALSTEP = 0.54                  # the alcove: seen small, and only in p_doors*
# rows measured OUT from the wall face; -0.14 is buried inside the wall
BAND_E = [-M, -0.02, 0.0, 0.055, 0.13, 0.28, 0.55, 0.95, 1.45]
BAND_ALONG = 0.72


def _uniform(lo, hi, step):
    n = max(1, int(round((hi - lo) / step)))
    return [lo + (hi - lo) * i / n for i in range(n + 1)]


def _band(m, y):
    """A strip hugging every boundary segment, drawn 0.006 ft below the field so
    it wins the overlap.  The open-field lattice cannot carry a 0.055 ft
    feature, and that hairline is the whole junction."""
    n = len(UNION)
    for s in range(n):
        ax, az = UNION[s]
        bx, bz = UNION[(s + 1) % n]
        dx, dz = bx - ax, bz - az
        L = math.hypot(dx, dz)
        ux, uz = dx / L, dz / L
        nx_, nz_ = -uz, ux
        # UNION is wound so that the inward normal is (+uz, -ux); check by
        # stepping in and seeing which side stays inside the bounding rect.
        if not _inside(ax + nx_ * 0.2 + ux * L * 0.5,
                       az + nz_ * 0.2 + uz * L * 0.5):
            nx_, nz_ = -nx_, -nz_
        cols = max(2, int(round(L / BAND_ALONG)) + 1)
        verts, vals, tris = [], [], []
        for c in range(cols):
            t = c / (cols - 1.0)
            px, pz = ax + dx * t, az + dz * t
            for e in BAND_E:
                x, z = px + nx_ * e, pz + nz_ * e
                verts.append((x, y, z))
                vals.append(target(x, z,
                                   e=max(0.0, _edge_dist(x, z)) if e > 0 else 0.0))
        R = len(BAND_E)
        for c in range(cols - 1):
            for k in range(R - 1):
                p = c * R + k
                q, r_, s_ = p + 1, p + R, p + R + 1
                tris += [(p, s_, q), (p, r_, s_)]      # face DOWN
        emit(m, verts, tris, vals)


def _inside(x, z):
    if AL_X <= x <= EX and 0.0 <= z <= DZ:
        return True
    return 0.0 <= x <= AL_X and AL_Z0 <= z <= AL_Z1


def piece_ceiling():
    m = Model()
    _grid(m, _uniform(AL_X - M, EX + M, STEP), _uniform(-M, DZ + M, STEP), YC)
    _grid(m, _uniform(-M, AL_X + 0.10, ALSTEP),
          _uniform(AL_Z0 - M, AL_Z1 + M, ALSTEP), YC - 0.003)
    _band(m, YC - 0.006)
    for (cx, cz, kind, k) in CANS:
        (_puck if kind == 0 else _wafer)(m, cx, cz, k)
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
    print("  rungs:", ", ".join("%d/%.1f:[%.0f,%.0f]" % (e, s, a, b)
                                for (e, s), (a, b) in zip(LADDER, RANGES)))
    if dry:
        return
    pos = ((lo[0] + hi[0]) / 2.0, lo[1], (lo[2] + hi[2]) / 2.0)
    from roomkit.place import place
    res = place("Hall2F Ceiling", path, ROOM, pos=pos, rot_y_deg=0.0, scale=1.0)
    print("  placed at %s  %s" % (tuple(round(v, 3) for v in pos), res["action"]))


if __name__ == "__main__":
    main(dry="--dry" in sys.argv)
