"""Room 17 (2F Hallway) -- `Hall2F Floor Planks`, ROUND 2.

    python floor2.py                       # build + place + repaint the slab
    F2_TEX=carpet F2_OP=0.55 python floor2.py

WHY THIS IS A REWRITE, NOT A TUNE
---------------------------------
Round 1's floor was judged by two critics whose subject WAS the floor and by
three more whose subject was something else; all five named it.  Measured
against the photographs at native resolution, the failure is not opinion:

    clean floor patch          L      sd     |d1|   |d1|/sd
    photo  doors_1 near      131.7    9.85   6.99    0.709
    photo  doors_2 near      126.6    9.90   4.54    0.459
    photo  runner  near      121.8   10.64   3.84    0.361
    photo  stairs  near      126.9   11.16   4.65    0.417
    R1     doors_2 near      130.6   19.74   1.51    0.076
    R1     runner  far       122.9    4.84   0.70    0.145
    R1     stairs  far       116.8    4.28   0.58    0.136

The VALUE was close (R1 floor/wall 0.665-0.715 against the photographs'
0.73-0.80 -- the round-1 critics' "roughly half the photo's luminance" is not
what the pixels say, and I say so in the report).  What was missing is
STRUCTURE: |d1| 3x-10x too low and |d1|/sd 3x-9x too low, i.e. all of R1's
variation was big smooth blobs and none of it was at the scale an eye lands
on.  You could not see a single board edge or butt joint in the frame.

THE FOUR THINGS THAT CHANGED
----------------------------
1.  THE SLAB TEXTURE IS NOW `carpet`, NOT `wood`.  Sounds wrong; it is the
    single biggest win.  `wood.png` is a 2.2 ft repeat with FOUR hard board
    seams baked in at 0.55 ft, so (a) it forces a 0.55 ft plank pitch that the
    photographs do not have, (b) its seams beat against any other pitch, and
    (c) its fine grain is weak: mean|d1|/mean = 0.019.  `carpet.png` is the
    same generator's ISOTROPIC fine noise, 0.036 relative -- which is exactly
    the photographs' floor (4.5/126.6 = 0.036 to 7.0/131.7 = 0.053) -- with no
    stripes at all, at 0.0234 ft per texel (2.1 render px at the near field).
    So the slab now carries the sub-inch grain and this piece owns every plank
    cue, at whatever pitch the photographs actually show.

2.  PLANK PITCH 0.583 ft (7 in), free of the tile.  Round 1 shipped 0.55
    because the tile hard-coded it and said in its own header that the photos
    "read wider".  7 in is also what the round-1 floor critic independently
    read off the photograph ("one about every 7 in").

3.  THE X-SAMPLES ARE SPENT ON EDGES AND STREAKS, THE Z-SAMPLES ON JOINTS.
    Wood grain is anisotropic: it varies fast ACROSS a board and slowly ALONG
    it.  So the grid is 13 x-samples per 0.583 ft board (0.045 ft = 0.54 in
    apart, with tight 0.022 ft triples at the two mineral streaks) and only
    one z-row per 1.15 ft, plus a 4-row cluster at every butt joint.  That
    buys board edges, streaks and joints inside the 300 KB cap; a uniform grid
    fine enough in both axes is ~11 k verts = 540 KB.

4.  EVERY CUE THE PHOTOGRAPHS SHOW IS NOW PRESENT AND SEPARATELY TUNABLE:
      * micro-bevelled long edge -- a real 0.004 ft V groove at every board
        edge with a dark line in it, so boards converge to the vanishing point
      * staggered butt joints -- 3.3-5.1 ft apart, phase-shifted per column,
        each a TONE STEP (the piece past it is a different value) plus a
        0.016 ft dark hairline, which is how they read in the photographs
      * per-board value +-8 % and per-butt-piece +-3 %
      * three-octave cathedral grain that migrates across the board as it runs
      * two hairline mineral streaks per board, fading in and out along it
      * a baked light field: a pool under each of the six ceiling cans (the
        ceiling piece's own solved positions), a longitudinal ramp, and an AO
        ramp into every wall line with a tight contact hairline at the wall --
        theme 4 ("no light falloff") and theme 2 ("nothing touches the ground")
      * satin sheen from roughness, broken lengthwise by a per-board crown

VALUE is solved as a floor/wall RATIO because the render's walls are another
agent's skins this round and an absolute target would chase them:

    photo                           wall    floor   ratio
    two_closed_white_doors_1       172.0    131.7   0.766
    two_closed_white_doors_2       166.2    126.6   0.762
    hallway_with_white_runner_rug  167.4    121.8   0.728   (left wall 151.3 -> 0.805)
    hallway_looking_towards_stairs 159.5    126.9   0.795

HUE.  The photographs meter R+2.6 G-2.3 B-0.3 about their own mean at the near
field (135.2/130.6/132.6 and 129.2/125.8/127.4) -- a NEUTRAL grey with a slight
green deficit, NOT the "warm greige washed oak" one round-1 critic asked for
and NOT the blue-violet an earlier build produced.  I followed the pixels.
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "circ"))
sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")

from ckit import *                                            # noqa: F401,F403,E402
from ckit import _req                                         # noqa: E402
from roomkit.glb import Part                                  # noqa: E402
from roomkit.place import place                               # noqa: E402

ROOM = 17

# ---------------------------------------------------------------- footprint
POLY = [(11.92, 6.81), (7.61, 6.81), (7.61, 16.89), (3.86, 16.89),
        (3.86, 16.15), (0.0, 16.15), (0.0, 10.77), (3.86, 10.77),
        (3.86, 0.0), (11.92, 0.0)]

# Three axis-aligned bands whose union is exactly that L (areas sum to
# 113.455 sq ft against the polygon's own 113.455).  Split on x so a board
# column is never cut along its length.
REGIONS = [
    (0.00, 3.86, 10.77, 16.15),     # west alcove   (three-door dead end)
    (3.86, 7.61, 0.00, 16.89),      # walking strip + west half of north block
    (7.61, 11.92, 0.00, 6.81),      # east half of the north block
]
# polygon edge 0 -- z = 6.81, x 7.61..11.92 -- is the OPEN stairwell cut.  No
# AO there (light comes up through the well) and it gets a nosing board.
OPEN_EDGE = ((11.92, 6.81), (7.61, 6.81))

# ------------------------------------------------------------------- tuning
PITCH = float(os.environ.get("F2_PITCH", 0.583))      # 7 in boards
TEXTURE = os.environ.get("F2_TEX", "carpet")
OPACITY = float(os.environ.get("F2_OP", 0.62))
ROUGH = float(os.environ.get("F2_ROUGH", 0.46))
WEAR_COLOR = os.environ.get("F2_COL", "#8a8688")
FLOOR_COLOR = os.environ.get("F2_SLAB", "#63615f")

Y0 = float(os.environ.get("F2_Y", 0.034))   # over the slab (0.010), under the runner body (0.020)
CROWN = float(os.environ.get("F2_CROWN", 0.0008))   # per-board crown -> a specular band down each board
GROOVE = 0.0042         # how deep the micro-bevel at a board edge cuts

ROW = 1.15              # z-row pitch down a board
JOINT_MIN, JOINT_MAX = 3.30, 5.10      # butt spacing, ft (48 in nominal)

# THE VERTEX-COLOUR CEILING.  glb.py writes COLOR_0 as `_srgb_to_linear(c)`
# scaled into a normalized ubyte, so ANY channel authored above 1.0 pegs at
# 255 and the whole upward half of the grain is silently thrown away (round 3's
# floor metered mean|d1| 0.08 -- algebraically flat -- for exactly this
# reason).  The field is centred on NOM with the material albedo carrying the
# rest, so s may swing +-30 % without touching the ceiling.
NOM = 0.74

# The ceiling piece's own solved can positions (room-local ft, 8 ft up).  A
# pool under each is what the photographs show and what theme 4 asks for.
CANS = [(5.80, 7.18), (7.75, 7.18), (6.10, 4.18), (8.22, 4.10),
        (10.03, 12.74), (1.93, 13.46)]
CAN_AMP = 0.052         # peak lift directly under a can
CAN_SIG = 3.30          # ft; a 8 ft drop spreads the pool this wide

WEAR = Material("h17wear4", WEAR_COLOR, roughness=ROUGH, metallic=0.0,
                opacity=OPACITY, double_sided=False)
NOSE = Material("h17nose4", "#55524f", roughness=0.50, metallic=0.0)


# ------------------------------------------------------------------ helpers
def h(*a):
    """Deterministic hash -> [0,1). Keyed on the GLOBAL board index, so a board
    clipped by a region boundary gets the same tone on both sides."""
    v = 0x9E3779B9
    for x in a:
        v = (v ^ (int(x) * 0x85EBCA6B + 0xC2B2AE35)) & 0xFFFFFFFF
        v = ((v << 13) | (v >> 19)) & 0xFFFFFFFF
        v = (v * 0x27D4EB2F + 0x165667B1) & 0xFFFFFFFF
    return ((v >> 8) & 0xFFFFFF) / 16777216.0


def sym(*a):
    return h(*a) * 2.0 - 1.0


def _seg_dist(px, pz, a, b):
    ax, az = a
    bx_, bz = b
    dx, dz = bx_ - ax, bz - az
    L2 = dx * dx + dz * dz
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (pz - az) * dz) / L2))
    return math.hypot(px - (ax + t * dx), pz - (az + t * dz))


EDGES = [(POLY[i], POLY[(i + 1) % len(POLY)]) for i in range(len(POLY))]
AO_EDGES = [e for e in EDGES if e != OPEN_EDGE]


def wall_dist(px, pz):
    return min(_seg_dist(px, pz, a, b) for (a, b) in AO_EDGES)


def light(px, pz):
    """Baked light field, multiplicative, mean ~1.0.

    Three terms, all read off the photographs:
      * a pool under each ceiling can (theme 4: "the photos brighten under
        each can and fall off into every corner");
      * a longitudinal ramp -- the photographs run ~122 in the near foreground
        to ~135 at mid hall;
      * an AO ramp into every wall line with a tight contact hairline at the
        wall itself, which is what gives the skirting something to sit in
        (theme 2).  The open stairwell cut is excluded: light comes UP there.
    """
    v = 1.0
    for (cx, cz) in CANS:
        d2 = (px - cx) ** 2 + (pz - cz) ** 2
        v += CAN_AMP * math.exp(-d2 / (2.0 * CAN_SIG * CAN_SIG))
    v *= 1.0 + 0.016 * math.exp(-((pz - 9.6) / 7.4) ** 2)
    d = wall_dist(px, pz)
    v *= 0.905 + 0.095 * min(1.0, (d / 0.42) ** 0.85)      # AO ramp
    if d < 0.075:                                          # contact hairline
        v *= 0.900 + 0.100 * (d / 0.075) ** 0.6
    return v


def joints_for(gk, z0, z1):
    """Butt joints down one board column, staggered by column."""
    out = []
    z = z0 + JOINT_MIN * (0.20 + 0.80 * h(gk, 11))
    i = 0
    while z < z1 - 0.50:
        if z > z0 + 0.50:
            out.append(z)
        z += JOINT_MIN + (JOINT_MAX - JOINT_MIN) * h(gk, i, 23)
        i += 1
    return out


def board_rows(z0, z1, jz):
    n = max(2, int(round((z1 - z0) / ROW)))
    rows = [z0 + (z1 - z0) * k / n for k in range(n + 1)]
    for j in jz:
        rows += [j - 0.048, j - 0.010, j + 0.010, j + 0.048]
    rows = sorted(v for v in set(round(v, 4) for v in rows)
                  if z0 - 1e-6 <= v <= z1 + 1e-6)
    return rows


# --------------------------------------------------------------- the sheet
def piece_floor():
    m = Model()
    nv = 0

    for (rx0, rx1, rz0, rz1) in REGIONS:
        k0 = int(math.floor(rx0 / PITCH + 1e-6))
        k1 = int(math.ceil(rx1 / PITCH - 1e-6))
        for gk in range(k0, k1):
            bx0 = max(rx0, gk * PITCH)
            bx1 = min(rx1, (gk + 1) * PITCH)
            if bx1 - bx0 < 0.014:
                continue

            jz = joints_for(gk, rz0, rz1)
            rows = board_rows(rz0, rz1, jz)

            # ---- per-column constants -------------------------------------
            # Per-board base value.  The round-1 critic asked for +-12 %; the
            # photographs' board patches at one depth run 133 -> 93, but most
            # of that is the hall's own lateral light falloff (which `light()`
            # now carries), so the random part is smaller.  +-8 % uniform.
            board = 1.0 + 0.080 * sym(gk, 3)
            # three cathedral octaves; each has its own phase, its own
            # frequency and its own slow fade ALONG the board, so a figure
            # wanders in and out instead of running the whole length
            oct_ = [(0.052, 1.35 + 0.45 * h(gk, 40), h(gk, 50) * 6.2832,
                     2.4 + 3.6 * h(gk, 60), h(gk, 70) * 6.2832),
                    (0.040, 2.60 + 0.70 * h(gk, 41), h(gk, 51) * 6.2832,
                     1.7 + 2.3 * h(gk, 61), h(gk, 71) * 6.2832),
                    (0.026, 4.10 + 0.90 * h(gk, 42), h(gk, 52) * 6.2832,
                     1.1 + 1.7 * h(gk, 62), h(gk, 72) * 6.2832)]
            ph2 = h(gk, 6) * 6.2832
            ph3 = h(gk, 7) * 6.2832
            wob = 0.55 + 0.9 * h(gk, 9)

            # ---- x-samples ------------------------------------------------
            # 13 per board.  Two tight triples sit on the mineral streaks so
            # they resolve as 0.022 ft hairlines rather than soft swells; the
            # two pairs at the ends resolve the micro-bevel at the board edge.
            st = [0.17 + 0.30 * i + 0.13 * sym(gk, 80 + i) for i in range(2)]
            st = sorted(min(0.86, max(0.14, v)) for v in st)
            ts = [0.0, 0.030]
            for s in st:
                ts += [s - 0.038, s, s + 0.038]
            ts += [0.50, 0.75] if st[0] < 0.45 else [0.30, 0.62]
            ts += [0.970, 1.0]
            ts = sorted(set(round(min(1.0, max(0.0, v)), 4) for v in ts))

            xs = []
            for t in ts:
                x = gk * PITCH + t * PITCH
                if bx0 - 1e-6 <= x <= bx1 + 1e-6:
                    xs.append(round(x, 5))
            for x in (bx0, bx1):
                if all(abs(x - v) > 1e-4 for v in xs):
                    xs.append(round(x, 5))
            xs = sorted(set(xs))
            nx = len(xs)
            if nx < 2:
                continue

            st_amp = [0.075 + 0.060 * h(gk, 90 + i) for i in range(2)]
            st_zl = [1.4 + 2.8 * h(gk, 95 + i) for i in range(2)]
            st_zp = [h(gk, 98 + i) * 6.2832 for i in range(2)]

            verts, cols, tris = [], [], []
            for z in rows:
                piece = sum(1 for j in jz if z >= j)
                dj = min((abs(z - j) for j in jz), default=9.0)
                # A butt joint in the photographs is a TONE STEP first and a
                # line second: the piece past it is a different value, and the
                # joint itself is only a fine dark hairline.
                jf = 1.0
                if dj < 0.016:
                    jf = 0.885
                elif dj < 0.052:
                    jf = 0.885 + 0.115 * ((dj - 0.016) / 0.036) ** 0.7
                pt = 1.0 + 0.030 * sym(gk, piece, 17)
                grain_z = (0.014 * math.sin(z / (1.9 * wob) + ph3)
                           + 0.012 * math.sin(z / (0.44 * wob) + ph2))

                for x in xs:
                    t = (x / PITCH) - gk           # 0..1 across this board
                    lane = 0.0
                    for (amp, fr, phs, zl, zp) in oct_:
                        fade = 0.50 + 0.50 * math.sin(z / zl + zp)
                        lane += amp * fade * math.sin(6.2832 * fr * t + phs)
                    for i, p in enumerate(st):
                        d = abs(t - p) * PITCH
                        if d < 0.048:
                            f = 0.40 + 0.60 * math.sin(z / st_zl[i] + st_zp[i])
                            lane -= (st_amp[i] * max(0.0, f)
                                     * math.exp(-(d / 0.019) ** 2))
                    # the micro-bevelled long edge: a real groove with a dark
                    # line in it, so a board edge is readable to the far door
                    ds = min(abs(x - gk * PITCH), abs(x - (gk + 1) * PITCH))
                    edge = -0.115 * math.exp(-(ds / 0.021) ** 2)

                    s = board * pt * jf * light(x, z) * (1.0 + lane + grain_z + edge)
                    s *= NOM

                    y = Y0 + CROWN * math.sin(math.pi * t)
                    if ds < 0.026:
                        y -= GROOVE * math.exp(-(ds / 0.017) ** 2)
                    if dj < 0.020:
                        y -= 0.0016
                    verts.append((x, y, z))
                    cols.append((min(1.0, s * 1.014), min(1.0, s * 0.988),
                                 min(1.0, s * 0.999)))

            for j in range(len(rows) - 1):
                for i in range(nx - 1):
                    a = j * nx + i
                    tris += [(a, a + nx, a + 1), (a + 1, a + nx, a + nx + 1)]
            nv += len(verts)
            m.add(Part(verts, tris, smooth=True, colors=cols), WEAR)

    # Nosing on the open stairwell cut (polygon edge 0).  Without it the slab
    # ends in a raw sawn line right where `p_runner` and `p_down` look at it.
    bx(m, NOSE, 7.61, 11.92, -0.085, 0.0186, 6.745, 6.812)
    print(f"  verts={nv}")
    return m


# ------------------------------------------------------------------- drive
def save_and_place_local(name, m, room=ROOM, fname=None):
    path = os.path.join(HERE, "..", "glb",
                        (fname or name.replace(" ", "_").lower()) + ".glb")
    path = os.path.abspath(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    m.save(path)
    lo, hi = m.bounds()
    pos = ((lo[0] + hi[0]) / 2.0, lo[1], (lo[2] + hi[2]) / 2.0)
    res = place(name, path, room, pos=pos, rot_y_deg=0.0, scale=1.0)
    kb = os.path.getsize(path) / 1024.0
    print(f"  {name:24s} size={tuple(round(hi[i]-lo[i],2) for i in range(3))}"
          f"  {kb:7.1f} KB  {res['action']}")
    return kb


if __name__ == "__main__":
    print(f"  pitch={PITCH} tex={TEXTURE} op={OPACITY} rough={ROUGH} "
          f"col={WEAR_COLOR} slab={FLOOR_COLOR}")
    save_and_place_local("Hall2F Floor Planks", piece_floor())
    if "--nopatch" not in sys.argv:
        _req("PATCH", f"/api/house/room/{ROOM}",
             {"floor_color": FLOOR_COLOR, "floor_texture": TEXTURE})
        print(f"  room {ROOM} floor_color -> {FLOOR_COLOR}, "
              f"floor_texture -> {TEXTURE}")
