"""Room 17 (2F Hallway) -- `Hall2F Floor Planks`, round V3.

    python floor.py                     # build + place + repaint the slab
    python floor.py --nopatch           # geometry only
    H17_PITCH=0.73 H17_TEX=carpet python floor.py    # the pitch/texture test

WHAT WAS WRONG
--------------
1.  OLD FOOTPRINT.  The piece was authored against an 8.1 x 16.7 L with the
    notch at 3.95/7.7.  The room is now a 10-vertex L with a WEST ALCOVE at
    local x 0..3.86, z 10.77..16.15, and the old deck did not reach it -- in
    `p_doors1` the alcove was bare app slab, metering 107.9 against a 210.7
    wall (ratio 0.51) because `floor_color` was #504f4b, a near-black brown.
    This version tiles the polygon EXACTLY: three axis-aligned bands whose
    areas sum to 113.455 sq ft against the polygon's own 113.455.

2.  HARD ALTERNATING STRIPES, which all four blind critics named first.  Two
    separate causes, both found by measurement, neither of them "the tone
    field needs tuning":

    (a) THE VERTEX COLOURS WERE BEING CLIPPED AWAY.  `glb.py` writes COLOR_0
        as `_srgb_to_linear(c)` scaled into a normalized ubyte, so any channel
        authored above 1.0 pegs at 255.  Round 3's floor -- and this piece's
        own first two builds -- centred their tone field on 1.0, so every
        UPWARD excursion clipped and only the dark half of the grain survived.
        Exported buffer: min 179, max 255, a large fraction at 255.  Rendered
        with the slab texture removed, that floor metered mean|d1| 0.08:
        algebraically flat.  The field is centred on NOM = 0.76 now, with the
        material albedo divided back out so the mean is unchanged, and it may
        swing +-30% without touching the ceiling.
    (b) THE SEAM LIFT WAS 5x TOO STRONG.  The shared `wood` tile stamps a
        15%-dark board seam every 0.55 ft.  Cancelling it is arithmetic, not
        taste: at opacity 0.62 the tile is 38% of the composite, so its seam
        costs 0.38 x 15% = 5.7% of linear radiance, and a lift E in this
        sRGB-ish tone domain returns 0.62 x ((1+E)^2.2 - 1).  E = 0.040
        cancels exactly.  The first build used 0.22 and put a +12% BRIGHT
        line on every seam -- measured on a scanline through the alcove:
        field 128, peak 143.  E = 0.025 ships, leaving the -2% whisper of a
        board edge the photographs actually show.

VALUE.  Solved as a floor/wall RATIO, because the render's walls are not the
photographs' walls and an absolute target would chase another builder's skin:

    photo                            wall   floor  ratio
    hallway_with_white_runner_rug   158.9   122.4  0.770
    hallway_looking_towards_stairs  156.1   126.6  0.811
    two_closed_white_doors_1        172.6   128.3  0.743
    two_closed_white_doors_2        172.6   130.2  0.754

Shipped: 0.755 / 0.782 / 0.789 on the three clean render patches.  Hue is
near-neutral with a slight green deficit -- the photographs meter R+1.5 G-2.5
B+1.0 about their own mean, NOT the blue-violet the first build produced.

WHERE THE GRAIN COMES FROM
--------------------------
Not from mesh cells.  The photographs' clean floor meters mean|d1| 4.3-5.8 at
450x600, i.e. grain at roughly a 0.1 in scale; reaching that with geometry
needs ~0.05 ft lanes over 113 sq ft, about 5600 verts of lanes alone, ~290 KB,
and still lands 5-9x too coarse.  So the fine end comes from the app's own
tiled field (`floor_texture: 'wood'`, 4 boards per 2.2 ft, |d1|x 5.77 on a
mean of 220 = 2.6% relative at 0.0086 ft per texel) and this piece is a thin
WEAR LAYER over it carrying what a tile cannot:

  * PORE LINES, not tone ramps.  A photographed oak-look plank is a light
    field cut by a few narrow dark pore/figure lines running its length.
    Eleven evenly spread samples across 0.55 ft can only make broad soft
    swells -- which is exactly what the first pass rendered.  The x-samples
    are spent WHERE THE LINES ARE instead: three pores per board, each with
    its own triple of samples 0.013 ft apart, its own depth, and its own slow
    fade along the board, so no two boards line up and a streak wanders in
    and out the way real figure does.  Three broad octaves underneath carry
    the field tone.
  * BUTT JOINTS.  wood.png has infinitely long boards and no joints at all.
    Real LVP butts every ~4 ft, staggered per column.  In the photographs a
    joint is a TONE STEP, not a line, so each board piece between two joints
    gets its own value (+-2.6%) and the joint itself is only a 0.075 ft
    whisper at 0.962.
  * SHEEN.  Roughness 0.34 against scene.js's PMREM environment, plus a
    per-board crown (0.0013 ft over 0.55) and a slow lengthwise undulation,
    so the specular breaks into soft bands running DOWN the boards instead of
    lying on the floor as one sheet -- the cue a critic called "most of what
    makes the hall read as long".  A broad +1.8% baked pool around z 9.4
    matches the photograph's 122-near / 135-mid longitudinal ramp.
  * A baked edge AO ramp, 0.40 ft to 0.94 at the wall line, on every polygon
    edge except the open stairwell cut (light comes UP through that one),
    plus a nosing board along that cut so the slab does not end in a sawn
    line where `p_runner` and `p_down` look straight at it.

HEIGHT.  0.0168..0.0196 ft.  Verified empirically rather than assumed: a test
piece with bands at y = 0.012 / 0.016 / 0.020 / 0.026 / 0.032 / 0.040 / 0.050
rendered at EVERY height, opaque and at opacity 0.34, so the slab's
polygonOffsetFactor -1 does not in fact win at 0.012 the way STYLE-BAR's decal
note implies.  0.0168 is chosen to stay under the runner, whose body beds at
y 0.020 and whose contact-shadow decal is at 0.050.

PLANK DIRECTION is along Z, down the hall.  Read off the photographs: in
`hallway_with_white_runner_rug` and `hallway_looking_towards_stairs` the boards
converge to the vanishing point down the hall, and in both alcove photographs
the run continues unbroken through the doorway -- one continuous install, no
change of direction at the alcove.  That agrees with what the app texture
already does (house.js maps a polygon slab's UVs straight off shape coords,
so u = local_x / 2.2 and the tile's seams land at local x = 0.55k exactly),
so sheet and slab register instead of beating.

PLANK WIDTH is the one thing here I could not settle -- see the report.
0.55 ft (6.6 in) ships because the shared tile hard-codes it and any other
pitch double-lines the floor; the photographs read wider, maybe 8-9 in, but
with no in-frame scale reference I trust better than +-25%.
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "circ"))
sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")

from ckit import *                                            # noqa: F401,F403,E402
from ckit import _req                                         # noqa: E402
from roomkit.glb import Part                                  # noqa: E402
from roomkit.place import place                               # noqa: E402

ROOM = 17

# ---------------------------------------------------------------- footprint
# The 10-vertex L, room-local feet (anchor world 6.70, 18.00, 6.55).
POLY = [(11.92, 6.81), (7.61, 6.81), (7.61, 16.89), (3.86, 16.89),
        (3.86, 16.15), (0.0, 16.15), (0.0, 10.77), (3.86, 10.77),
        (3.86, 0.0), (11.92, 0.0)]

# Three axis-aligned bands whose union is exactly that L.  Split on x so a
# board column is never split along its length.
REGIONS = [
    (0.00, 3.86, 10.77, 16.15),     # west alcove   (three-door dead end)
    (3.86, 7.61, 0.00, 16.89),      # walking strip + west half of north block
    (7.61, 11.92, 0.00, 6.81),      # east half of the north block
]
# edge 0 of the polygon -- z = 6.81, x 7.61..11.92 -- is the open stairwell
# cut.  No AO there (the well is lit from below) and it gets a nosing board.
OPEN_EDGE = ((11.92, 6.81), (7.61, 6.81))

# ------------------------------------------------------------------- tuning
# Two board pitches were built and shot side by side against
# `two_closed_white_doors_2.jpg` (see PITCH TEST in the report): 0.55, which is
# what the shared `wood` tile hard-codes, and 0.73.
PITCH = float(os.environ.get("H17_PITCH", 0.55))     # board width, ft
# The slab texture under the sheet.  'wood' pins the boards to 0.55 ft AND
# stamps a 15%-dark seam every 0.55 -- exactly the "butt-lines read as UV
# seams" complaint.  'carpet' is the same generator's ISOTROPIC fine noise
# (|d1| 8.29 on a mean of 230.9, one repeat per 6 ft = 0.28 in per texel), so
# it supplies fine grain with no plank stripes at all and leaves the board
# pitch to this piece.  Both are `use: 'floor'` keys, so the planner's picker
# still has an option for whichever is set.
TEXTURE = os.environ.get("H17_TEX", "wood")
SEAMW = 0.034           # the wood tile's seam is 4 px of 256 over 2.2 ft

Y0 = 0.0168             # sheet floor: over the slab (0.010), under the rug
CROWN = 0.0013          # per-board crown -> the specular band down each board
WAVE = 0.0008           # slow lengthwise undulation

# t-samples across one board.  Uneven on purpose: the tight pair at each end
# is what lets the sheet resolve the board edge without spending samples in
# the middle of the field.
TS = (0.0, 0.026, 0.070, 0.145, 0.255, 0.375, 0.500, 0.625, 0.755, 0.900, 0.972)

ROW = 0.80              # ladder pitch down a board
JOINT_MIN, JOINT_MAX = 3.30, 5.10      # butt spacing, ft (48 in nominal)

# THE VERTEX-COLOUR CEILING.  glb.py writes COLOR_0 as `_srgb_to_linear(c)`
# scaled to a normalized ubyte, so ANY channel authored above 1.0 clamps to
# 255.  Round 3's floor and this piece's first two builds both centred their
# tone field on 1.0, which quietly threw away every upward excursion: the
# exported buffer came back min 179 / max 255 with a large fraction pegged at
# 255, so only the DARK half of the grain survived and the floor metered
# mean|d1| 0.08 with the slab texture removed -- algebraically flat.  The tone
# field is centred on NOM instead, with the material's albedo divided back out
# so the mean value is unchanged; s may now swing +-30% without clipping.
NOM = 0.76

WEAR = Material("h17wear3", "#757273", roughness=0.34, metallic=0.0,
                opacity=float(os.environ.get("H17_OP", 0.62)),
                double_sided=False)
NOSE = Material("h17nose3", "#514e50", roughness=0.45, metallic=0.0)

FLOOR_COLOR = "#595758"                # room 17 slab albedo (was #504f4b)


# ------------------------------------------------------------------ helpers
def h(*a):
    """Deterministic hash -> [0,1). Keyed on the GLOBAL board index, so a
    board clipped by a region boundary gets the same tone on both sides."""
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
    bx, bz = b
    dx, dz = bx - ax, bz - az
    L2 = dx * dx + dz * dz
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (pz - az) * dz) / L2))
    return math.hypot(px - (ax + t * dx), pz - (az + t * dz))


EDGES = [(POLY[i], POLY[(i + 1) % len(POLY)]) for i in range(len(POLY))]
AO_EDGES = [e for e in EDGES if e != OPEN_EDGE]


def wall_dist(px, pz):
    return min(_seg_dist(px, pz, a, b) for (a, b) in AO_EDGES)


def joints_for(gk, z0, z1):
    """Butt joints down one board column, staggered by column."""
    out = []
    z = z0 + JOINT_MIN * (0.25 + 0.75 * h(gk, 11))
    i = 0
    while z < z1 - 0.55:
        if z > z0 + 0.55:
            out.append(z)
        z += JOINT_MIN + (JOINT_MAX - JOINT_MIN) * h(gk, i, 23)
        i += 1
    return out


# --------------------------------------------------------------- the sheet
def board_rows(z0, z1, jz):
    rows = [z0 + (z1 - z0) * k / max(2, int(round((z1 - z0) / ROW)))
            for k in range(max(2, int(round((z1 - z0) / ROW))) + 1)]
    for j in jz:
        rows += [j - 0.090, j - 0.045, j, j + 0.045, j + 0.090]
    rows = sorted(v for v in set(round(v, 4) for v in rows) if z0 - 1e-6 <= v <= z1 + 1e-6)
    return rows


def piece_floor():
    m = Model()

    for (rx0, rx1, rz0, rz1) in REGIONS:
        k0 = int(math.floor(rx0 / PITCH + 1e-6))
        k1 = int(math.ceil(rx1 / PITCH - 1e-6))
        for gk in range(k0, k1):
            bx0 = max(rx0, gk * PITCH)
            bx1 = min(rx1, (gk + 1) * PITCH)
            if bx1 - bx0 < 0.012:
                continue

            jz = joints_for(gk, rz0, rz1)
            rows = board_rows(rz0, rz1, jz)

            # per-column constants.  THREE cross-board grain octaves, each with
            # its own phase, its own frequency jitter and its own slow fade
            # along the board -- so a streak wanders in and out the way oak
            # figure does instead of running the whole length at one strength.
            board = 1.0 + 0.022 * sym(gk, 3)          # board-to-board value
            oct_ = [(0.040, 1.95 + 0.5 * h(gk, 40), h(gk, 50) * 6.2832,
                     2.2 + 3.4 * h(gk, 60), h(gk, 70) * 6.2832)]
            oct_ += [(0.044, 3.20 + 0.7 * h(gk, 41), h(gk, 51) * 6.2832,
                      1.6 + 2.2 * h(gk, 61), h(gk, 71) * 6.2832)]
            oct_ += [(0.036, 4.45 + 0.6 * h(gk, 42), h(gk, 52) * 6.2832,
                      1.1 + 1.6 * h(gk, 62), h(gk, 72) * 6.2832)]
            ph1 = h(gk, 5) * 6.2832
            ph2 = h(gk, 6) * 6.2832
            ph3 = h(gk, 7) * 6.2832                   # lengthwise grain phase
            wob = 0.55 + 0.9 * h(gk, 9)               # grain wavelength scale

            # PORE LINES.  A photographed oak-look plank is not a smooth tone
            # ramp across its width -- it is a light field cut by a handful of
            # narrow dark pore/figure lines running the length of the board.
            # Smooth-interpolating 11 evenly spread samples across 0.55 ft can
            # only make broad soft bands (which is exactly what the first pass
            # rendered).  So the x-samples are spent WHERE THE LINES ARE: three
            # per board, each given its own triple of samples 0.013 ft apart,
            # so the dip is a genuine hairline instead of a swell.  Positions
            # and depths are per board, so no two boards line up.
            pores = sorted(0.20 + 0.28 * i + 0.16 * sym(gk, 80 + i)
                           for i in range(3))
            ts = [0.0]
            for i, p in enumerate(pores):
                ts += [p - 0.024, p, p + 0.024]
            ts.append(1.0)
            ts = sorted(min(0.999, max(0.001, v)) for v in ts[1:-1])
            ts = [0.0] + ts + [1.0]

            xs = []
            for t in ts:
                x = gk * PITCH + t * PITCH
                if bx0 - 1e-6 <= x <= bx1 + 1e-6:
                    xs.append(x)
            for x in (bx0, bx1):
                if all(abs(x - v) > 1e-4 for v in xs):
                    xs.append(x)
            xs = sorted(xs)
            nx = len(xs)
            if nx < 2:
                continue
            pore_amp = [0.085 + 0.055 * h(gk, 90 + i) for i in range(3)]
            pore_zl = [1.3 + 2.6 * h(gk, 95 + i) for i in range(3)]
            pore_zp = [h(gk, 98 + i) * 6.2832 for i in range(3)]

            verts, cols, tris = [], [], []
            for z in rows:
                # which board piece are we on, and how close to a butt joint
                piece = sum(1 for j in jz if z >= j)
                dj = min((abs(z - j) for j in jz), default=9.0)
                # A butt joint in the photographs is a TONE STEP, not a line:
                # the piece past it is a different value and the joint itself
                # is a hairline you only see where the two values differ.  So
                # `pt` does the work and `jf` is only a whisper.
                jf = 1.0
                if dj < 0.075:
                    jf = 0.962 + 0.038 * (dj / 0.075) ** 0.7
                pt = 1.0 + 0.026 * sym(gk, piece, 17)

                # broad sheen: the hall's ceiling cans pool around z 8-10, and
                # the photo runs 122 in the foreground to 135 at mid distance
                sheen = 0.018 * math.exp(-((z - 9.4) / 6.6) ** 2)
                grain_z = (0.011 * math.sin(z / (1.7 * wob) + ph3)
                           + 0.013 * math.sin(z / (0.41 * wob) + ph2))

                for x in xs:
                    t = (x / PITCH) - gk           # 0..1 across this board
                    lane = 0.0
                    for (amp, fr, phs, zl, zp) in oct_:
                        fade = 0.55 + 0.45 * math.sin(z / zl + zp)
                        lane += amp * fade * math.sin(6.2832 * fr * t + phs)
                    # the hairline pores, each fading in and out down the board
                    for i, p in enumerate(pores):
                        d = abs(t - p) * PITCH
                        if d < 0.030:
                            f = 0.45 + 0.55 * math.sin(z / pore_zl[i] + pore_zp[i])
                            lane -= (pore_amp[i] * max(0.0, f)
                                     * math.exp(-(d / 0.011) ** 2))
                    ds = min(abs(x - gk * PITCH), abs(x - (gk + 1) * PITCH))
                    if TEXTURE == "wood":
                        # Paint the wood tile's own 15%-dark board seam nearly
                        # out.  SOLVED, not guessed: the tile is 38% of the
                        # composite at this opacity, so its seam costs the
                        # render 0.38 x 15% = 5.7% of linear radiance; the
                        # sheet is the other 62%, so a lift E in this sRGB-ish
                        # tone domain returns 0.62 x ((1+E)^2.2 - 1).  E = 0.040
                        # cancels it exactly; E = 0.025 leaves the -2% whisper
                        # of a board edge the photographs actually show.  The
                        # first build used 0.22 and put a +12% BRIGHT line on
                        # every seam -- measured off a scanline, field 128,
                        # peak 143.
                        edge = 0.025 * math.exp(-(ds / (0.62 * SEAMW)) ** 2)
                    else:
                        # no seam under us: put our own hairline board edge in,
                        # soft, the way the photographs show it
                        edge = -0.035 * math.exp(-(ds / 0.020) ** 2)
                    ao = 0.94 + 0.06 * min(1.0, wall_dist(x, z) / 0.40)

                    s = board * pt * jf * ao * (1.0 + lane + grain_z + sheen + edge)
                    s *= NOM

                    y = (Y0
                         + CROWN * math.sin(math.pi * t)
                         + WAVE * (0.5 + 0.5 * math.sin(z / 1.35 + ph1)))
                    if dj < 0.05:
                        y -= 0.0006          # the butt gap catches its own line
                    verts.append((x, y, z))
                    cols.append((min(1.0, s * 1.000), min(1.0, s * 0.997),
                                 min(1.0, s * 1.008)))

            for j in range(len(rows) - 1):
                for i in range(nx - 1):
                    a = j * nx + i
                    tris += [(a, a + nx, a + 1), (a + 1, a + nx, a + nx + 1)]
            m.add(Part(verts, tris, smooth=True, colors=cols), WEAR)

    # Nosing on the open stairwell cut (polygon edge 0).  Without it the slab
    # ends in a raw sawn line right where `p_runner` and `p_down` look at it.
    bx(m, NOSE, 7.61, 11.92, -0.085, 0.0186, 6.745, 6.812)
    return m


# ------------------------------------------------------------------- drive
def save_and_place(name, m, room=ROOM, fname=None):
    path = os.path.join(HERE, "glb",
                        (fname or name.replace(" ", "_").lower()) + ".glb")
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
    print(f"  pitch={PITCH} texture={TEXTURE}")
    save_and_place("Hall2F Floor Planks", piece_floor())
    if "--nopatch" not in sys.argv:
        _req("PATCH", f"/api/house/room/{ROOM}",
             {"floor_color": FLOOR_COLOR, "floor_texture": TEXTURE})
        print(f"  room {ROOM} floor_color -> {FLOOR_COLOR}, "
              f"floor_texture -> {TEXTURE}")
