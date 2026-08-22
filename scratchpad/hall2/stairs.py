"""Room 17 -- the STAIRWELL and the STAIRCASE inside it (hall2 v2 round).

Scope (BRIEF.md): `Hall2F Floor Planks` recut to the L so the void is real,
`Hall2F Knee Wall`, and a new stair-dressing piece.  Nothing else in room 17
and nothing at all in any other room.

Geometry, all ROOM-17-LOCAL feet (room origin world 10.5, 18.0, 6.6):

  footprint L : [[0,0],[8.1,0],[8.1,7.7],[3.95,7.7],[3.95,16.7],[0,16.7]]
  the void    : x 3.95..8.10, z 7.70..16.70   (edges 2 and 3, cut away)
  the flight  : app `stairs` row id 7 -- floor_id 2 (level 1, floor_height 10),
                world x 14.6..18.4 z 14.3..24.5, direction 'n' (ascends NORTH).
                house.js buildStairs => steps = round(10/0.6) = 17 solid boxes,
                tread run 0.6 ft, riser 10/17 = 0.5882 ft, the mesh spanning
                local x 4.10..7.90, z 7.70..17.90.  Step i's TOP face sits at
                local y = 0.5882*(i+1) - 10, so step 16 is flush with the 2F
                slab and step 0 tops out 9.41 ft below it.

Everything here is laid 0.01-0.05 ft PROUD of those faces (never coplanar --
coplanar dressing z-fights into a moire right down the flight).
"""

import math
import os
import sys

sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\circ")
sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")

from ckit import *                                            # noqa: F401,F403
from ckit import raked                                        # noqa: F401
from roomkit.place import place

HERE = os.path.dirname(os.path.abspath(__file__))
ROOM, W, D, H = 17, 8.1, 16.7, 8.0

# ------------------------------------------------------------------ the flight
SX0, SX1 = 4.10, 7.90          # the app mesh's own x span
SZB = 17.90                    # z of the bottom (south) edge of step 0
NST = 17
TR = 0.6                       # going, ft
RS = 10.0 / 17.0               # rise, ft
SLOPE = RS / TR                # 0.9804 -- steep, but it is the app's flight
FY = -10.0                     # local y of the floor the flight starts from


def ytop(i):
    """Local y of step i's top face."""
    return RS * (i + 1) + FY


def zspan(i):
    """(north/high edge, south/low edge) of step i."""
    return SZB - (i + 1) * TR, SZB - i * TR


def yn(z):
    """The nosing line: y of the tread whose SOUTH edge is at z."""
    return SLOPE * (SZB - z) + FY + RS


# ------------------------------------------------------- swept-section tools
# Everything on this flight is a section swept ACROSS the stair (along x): the
# treads, the runner, the runner's contact shadow.  Sweeping is what lets the
# runner be ONE continuous solid from the head of the flight to the bottom
# riser instead of 17 disconnected quads -- and a swept strip welds its verts,
# so it is also about six times cheaper per surface than the boxes it replaces.

def _sweep(m, mat, poly, x0, x1, smooth=True, closed=False):
    """Sweep a (z, y) polyline from x0 to x1.

    Wound so that a polyline traversed in the direction of INCREASING z has its
    normals pointing up/south -- i.e. out of the stair.

    The quad diagonal ALTERNATES with the segment index, and that is load
    bearing.  glb._weld's smooth normal is an area-weighted sum of the faces
    touching a vertex, so with one fixed diagonal the x0 column collects the
    quad ahead twice and the quad behind once while the x1 column collects the
    reverse -- the two edges of every rib end up with different normals and the
    runner shades as a row of soft pleats, one per pile lane.  Flipping the
    diagonal each segment gives both columns 2:2 / 1:1 of the same two faces,
    so their normals are parallel and the lanes go flat.
    """
    n = len(poly)
    v = [(x0, y, z) for (z, y) in poly] + [(x1, y, z) for (z, y) in poly]
    t = []
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        j = (i + 1) % n
        if i % 2:
            t += [(i, j, n + i), (j, n + j, n + i)]
        else:
            t += [(i, j, n + j), (i, n + j, n + i)]
    m.add(Part(v, t, smooth=smooth), mat)


def _sweep_wall(m, mat, outer, inner, x, sign, smooth=False):
    """The cut edge of a swept band: the wall between two parallel polylines."""
    n = len(outer)
    v = [(x, y, z) for (z, y) in outer] + [(x, y, z) for (z, y) in inner]
    t = []
    for i in range(n - 1):
        a, b, c, d = i, i + 1, n + i, n + i + 1
        t += [(a, b, c), (b, d, c)] if sign > 0 else [(a, c, b), (b, c, d)]
    m.add(Part(v, t, smooth=smooth), mat)


def _offset(poly, d):
    """Offset a (z, y) polyline by `d` along its outward normal (mitred)."""
    n = len(poly)
    sn = []
    for i in range(n - 1):
        dz, dy = poly[i + 1][0] - poly[i][0], poly[i + 1][1] - poly[i][1]
        L = math.hypot(dz, dy) or 1e-9
        sn.append((-dy / L, dz / L))
    out = []
    for i in range(n):
        if i == 0:
            nz, ny = sn[0]
        elif i == n - 1:
            nz, ny = sn[-1]
        else:
            a, b = sn[i - 1], sn[i]
            mz, my = a[0] + b[0], a[1] + b[1]
            L = math.hypot(mz, my)
            if L < 1e-6:
                nz, ny = b
            else:
                mz, my = mz / L, my / L
                k = max(0.40, mz * b[0] + my * b[1])   # mitre, clamped
                nz, ny = mz / k, my / k
        out.append((poly[i][0] + nz * d, poly[i][1] + ny * d))
    return out


def _arc(cz, cy, r, a0, a1, seg):
    return [(cz + r * math.cos(a0 + (a1 - a0) * k / seg),
             cy + r * math.sin(a0 + (a1 - a0) * k / seg))
            for k in range(1, seg + 1)]


def runner_skin():
    """The surface the runner lies on, as ONE (z, y) polyline from the head of
    the flight to the 1F floor: tread run -> rolled nosing -> the drape down
    the riser -> the next tread run, 17 times.  86 points, 85 segments."""
    pts = [(zspan(NST - 1)[0], ytop(NST - 1) + TBT)]
    for i in range(NST - 1, -1, -1):
        y = ytop(i) + TBT
        za, zb = zspan(i)
        zc = zb + NOSE - TCR
        pts.append((zc, y))                                   # along the tread
        pts += _arc(zc, y - TCR, TCR, math.pi / 2, 0.0, 3)     # over the nosing
        y2 = (ytop(i - 1) + TBT) if i else (FLOOR1 + 0.035)
        pts.append((zb + RISF, y2))                           # down the riser
    return pts


# dressing x lanes.  Both strings are CLOSED (the photos show a white skirt
# board on the east/wall side and a white string carrying the balustrade on the
# west/open side), so the tread boards BUTT INTO them rather than overhanging:
# their ends are buried under the raked cap boards and never need an end cap.
WSK0, WSK1 = 3.90, 4.22        # west string body (covers the mesh face at 4.10)
ESK0, ESK1 = 7.80, 8.04        # east string body (covers the mesh face at 7.90)
WCAP0, WCAP1 = 3.888, 4.232    # the raked cap board over each string
ECAP0, ECAP1 = 7.788, 8.052
TX0, TX1 = 4.19, 7.85          # tread boards, tucked under both cap boards
# The visible tread is WCAP1..ECAP0 = 3.556 ft.  The photos put the runner
# about 4.5-5 in inside each string, so it is 2.78 ft wide, not the 2.30 the
# round-2 build used (that left 10 in of bare tread each side and read as a
# painted stripe rather than a strip of cloth).
RUNC = (WCAP1 + ECAP0) / 2.0
RUNW = 2.78
RUN0, RUN1 = RUNC - RUNW / 2.0, RUNC + RUNW / 2.0
RAILX = 4.12                   # centre line of the black handrail
BALX = 4.12                    # centre line of the square balusters

# tread / riser / runner section
TBT = 0.030                    # half thickness of a tread board
NOSE = 0.12                    # how far the nosing overhangs the riser line
RISF = 0.034                   # riser face, proud of the app's own step box
TCR = 0.055                    # radius rolled onto the tread's front top edge
RT = 0.046                     # the runner's own thickness

# the shaft this all hangs in
SH_E0, SH_E1 = 8.04, 8.24      # east lining wall
SH_S0, SH_S1 = 20.40, 20.60    # south lining wall (closes the view past the
                               # bottom of the flight)
SH_N0, SH_N1 = 7.50, 7.70      # north lining wall, under the 2F landing
SH_W0, SH_W1 = 0.06, 0.24      # the 1F hallway's own west wall
FLOOR1 = -10.04                # the 1F floor, 0.04 under room 12's slab

# ----------------------------------------------------------------- materials
# Authored ~14/255 lighter than the CIRCULATION palette: the render metered
# L 115 on the hall floor against 123-138 across the two v2 photos.
PLK = [Material("s17pl%d" % i, c, roughness=0.90) for i, c in enumerate(
    ("#46453f", "#4f4e4a", "#585752", "#605e59", "#4a4944", "#545350",
     "#5c5a55", "#504f4b"))]
WHT = Material("s17wht", "#f4f3f0", roughness=0.62)
WHT2 = Material("s17wht2", "#e2e0dc", roughness=0.64)
# Treads meter 142-145 in the photo and the runner 143 -- they are the SAME
# value there, so the tread palette is tight and sits on the runner, not
# above it.  The separation in the photo is texture, not tone.
TRD = [Material("s17trd%d" % i, c, roughness=0.90) for i, c in enumerate(
    ("#494942", "#4d4b43", "#504e4a", "#4b4943", "#484740"))]
SHDW = Material("s17shdw", "#3a3932", roughness=0.95)   # nosing shadow line
SHDW2 = Material("s17shdw2", "#414038", roughness=0.93)  # its soft outer step
BLK = Material("s17blk", "#1c1c1f", roughness=0.42, metallic=0.30)
BLK2 = Material("s17blk2", "#26262a", roughness=0.50, metallic=0.22)
WALG = Material("s17wal", "#b4b6b7", roughness=0.95)    # shaft lining paint
FLR1 = [Material("s17flr%d" % i, c, roughness=0.92) for i, c in enumerate(
    ("#4c4a45", "#514f4a", "#585651", "#5e5c56", "#54524c",
     "#67655f", "#706e67", "#7a7870"))]                 # the 1F floor below

# ---- the runner.  ONE strip of cloth draped down the flight.  There is NO
# per-step tone alternation any more: that is exactly what read as "hard
# rectangular blocks marching down the lower treads".  Tone now varies ACROSS
# the width, in irregular pile lanes that run continuously top to bottom.
RUNT = [Material("s17rn%d" % i, c, roughness=0.99) for i, c in enumerate(
    ("#4c4944", "#4f4d47", "#494841", "#514f4a", "#4d4b43", "#4b4942"))]
RUNED = Material("s17rned", "#454440", roughness=0.99)  # woven binding, both edges
RUNSH1 = Material("s17rsh1", "#3e3d36", roughness=0.97)  # contact line on the tread
RUNSH2 = Material("s17rsh2", "#45443d", roughness=0.96)
RUNSH3 = Material("s17rsh3", "#44433c", roughness=0.99)  # under-nosing shade, inner
RUNSH4 = Material("s17rsh4", "#494841", roughness=0.99)


# ======================================================== 1  floor planks (L)
def piece_floor_planks():
    """The 2F plank floor, recut to the L so the stairwell is a REAL hole.

    Two strips, split exactly on the void's west edge (x 3.95): west strip runs
    the full depth, east strip stops at z 7.7.  The split lands on a plank seam,
    so the L edge reads as a board joint rather than a torn plank.
    """
    m = Model()
    rn = Rnd(4407)
    for (ax0, ax1, ncol, zmax) in ((0.00, 3.95, 7, 16.70),
                                   (3.95, 8.10, 7, 7.70)):
        pw = (ax1 - ax0) / ncol
        for c in range(ncol):
            x0 = ax0 + c * pw
            z = -1.0
            while z < zmax:
                L = rn.f(3.2, 7.2)
                z1 = min(zmax, z + L)
                if z1 > 0.0:
                    rect_up(m, PLK[int(rn.f(0, 7.99))], x0 + 0.010,
                            x0 + pw - 0.010, 0.014,
                            max(0.0, z) + 0.012, z1 - 0.012)
                z = z1
    # a bullnose along the two cut edges so the slab does not end in a raw
    # sawn line where it meets the void
    bx(m, PLK[3], 3.95, 8.10, -0.075, 0.020, 7.62, 7.72)
    bx(m, PLK[3], 3.87, 3.97, -0.075, 0.020, 7.62, 16.70)
    return m


# ==================================================== 2  the flight + its shaft
def shaft(m):
    """Line the well.  Floor 2 is HIDDEN when the app is showing level 2, so
    without this you look down the hole at the sky.  Three painted walls, the
    1F floor, and a door at the far end -- which is what the bottom of
    `staircase_looking_down.jpg` actually shows."""
    y0, y1 = FLOOR1, 0.02
    bx(m, WALG, SH_E0, SH_E1, y0, y1, SH_N0, SH_S1)             # east
    bx(m, WALG, SH_W0, SH_W1, y0, -0.04, 6.10, SH_S1)           # 1F west wall
    bx(m, WALG, SH_W0, SH_E1, y0, y1, SH_S0, SH_S1)             # south
    bx(m, WALG, 3.95, SH_E1, y0, y1, SH_N0, SH_N1)              # north, in well
    bx(m, WALG, SH_W0, 3.95, y0, -0.04, 6.10, 6.28)             # 1F north wall
    # the 1F floor, laid as planks so the bottom of the well is not a flat slab.
    # Board tone is chosen by DISTANCE FROM THE FRONT DOOR, so the floor carries
    # the same falloff the lining walls do instead of being one flat value.
    rn = Rnd(1207)
    pw = (SH_E0 - SH_W1) / 13.0
    for c in range(13):
        x0 = SH_W1 + c * pw
        z = 6.28
        while z < SH_S0:
            z1 = min(SH_S0, z + rn.f(3.0, 6.5))
            d = math.hypot((SH_S0 - (z + z1) / 2.0) * 0.42,
                           (x0 + pw / 2.0 - 5.95) * 0.34)
            k = 7.4 - d * 1.05 + rn.f(-0.9, 0.9)
            rect_up(m, FLR1[max(0, min(len(FLR1) - 1, int(round(k))))],
                    x0 + 0.012, x0 + pw - 0.012,
                    FLOOR1, z + 0.012, z1 - 0.012)
            z = z1
    rect_up(m, FLR1[0], SH_W1, SH_E0, FLOOR1 - 0.02, 6.28, SH_S0)
    # the pool of daylight the front door throws across the entry -- the one
    # thing round 2's shaft had none of ("NO LIGHT GRADIENT down the stairwell")
    decal(m, 5.95, 19.20, 3.10, 2.50, FLOOR1 + 0.030, "#fffdf4", 0.46,
          steps=8, seg=18)
    decal(m, 5.95, 19.90, 1.55, 1.05, FLOOR1 + 0.050, "#fffef8", 0.26,
          steps=4, seg=14)
    # A ceiling over the 1F space, everywhere EXCEPT the void.  The room slabs
    # are wound to face up, so from underneath they render as nothing at all --
    # from the dollhouse pose you looked into the well and straight out through
    # the floor above at the night sky.
    # y = -0.04, not -0.10: any slot between this and the slab above is a slit
    # the dollhouse camera looks along and straight out at the night sky.
    for (a0, a1, b0, b1) in ((SH_W1, 4.00, 6.28, SH_S0),
                             (3.95, SH_E1, 6.28, 7.70),
                             (3.95, SH_E1, 16.70, SH_S0)):
        rect_down(m, WALG, a0, a1, -0.04, b0, b1)

    # ---- the well's rim.  Every room round the void hangs a 0.5 ft accent
    # PLINTH under its slab (house.js PLINTH_DEPTH) -- room 27 teal at x 8.1,
    # room 26 purple at z 16.8, room 17's own blue at x 3.95 -- and from inside
    # the well those read as saturated stripes ringing the hole.  A painted
    # reveal round the opening covers them and gives the void a real edge.
    # Each plinth extrudes OUTWARD from its own footprint line by
    # WALL_THICKNESS 0.35 and drops PLINTH_DEPTH 0.5, so the reveal has to be
    # 0.35 wide on the far side of every edge and 0.58 deep:
    #   room 17 edge 3  x 3.95..4.30   room 17 edge 2  z 7.70..8.05
    #   room 27 west    x 7.75..8.10   room 26 north   z 16.45..16.80
    ry0, ry1 = -0.58, 0.02
    bx(m, WALG, 3.86, 8.62, ry0, ry1, 7.50, 8.12)               # north rim
    # west rim runs a touch proud (to y +0.12, and past the knee wall's own
    # ends) -- the dollhouse camera looks straight down the seam where the
    # knee wall's base meets the slab edge and any sliver there shows sky
    bx(m, WALG, 3.80, 4.34, ry0, 0.12, 6.90, 17.00)             # west rim
    bx(m, WALG, 7.70, 8.62, ry0, ry1, 7.50, 17.10)              # east rim
    bx(m, WALG, 3.86, 8.62, ry0, ry1, 16.30, 17.10)             # south rim
    # 1F baseboard so the shaft bottom does not read as a bare box
    for (a0, a1, b0, b1) in ((SH_W1, SH_W1 + 0.05, 6.28, SH_S0),
                             (SH_E0 - 0.05, SH_E0, SH_N1, SH_S0)):
        bx(m, WHT, a0, a1, FLOOR1, FLOOR1 + 0.52, b0, b1)
    bx(m, WHT, SH_W1, SH_E0, FLOOR1, FLOOR1 + 0.52, SH_S0 - 0.05, SH_S0)
    # a plain white door on the end wall, on the flight's own axis so it is
    # what you actually see at the bottom of the well (the 1F entry in the photo)
    dz = SH_S0 - 0.02
    bx(m, DOORW, 4.55, 7.35, FLOOR1, FLOOR1 + 7.10, dz - 0.16, dz)     # casing
    bx(m, DOORL, 4.71, 7.19, FLOOR1, FLOOR1 + 6.86, dz - 0.22, dz - 0.16)
    for (a, b, c, d) in ((4.87, 5.87, 0.55, 3.10), (6.03, 7.03, 0.55, 3.10),
                         (4.87, 5.87, 3.40, 6.50), (6.03, 7.03, 3.40, 6.50)):
        bx(m, DOORW, a, b, FLOOR1 + c, FLOOR1 + d, dz - 0.26, dz - 0.22)
    m.add(cylinder(0.055, 0.30, 8), BLK,
          at=(6.97, FLOOR1 + 2.95, dz - 0.36), rot_x=R(90))
    shaft_falloff(m)
    shaft_clutter(m)


# --------------------------------------------------- baked light down the well
def vface_z(m, mat, x0, x1, y0, y1, z, out):
    if out > 0:
        m.add(quad((x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)), mat)
    else:
        m.add(quad((x1, y0, z), (x0, y0, z), (x0, y1, z), (x1, y1, z)), mat)


def vface_x(m, mat, z0, z1, y0, y1, x, out):
    if out > 0:
        m.add(quad((x, y0, z1), (x, y0, z0), (x, y1, z0), (x, y1, z1)), mat)
    else:
        m.add(quad((x, y0, z0), (x, y0, z1), (x, y1, z1), (x, y1, z0)), mat)


def decal(m, cx, cz, rx, rz, y, tone, strength, steps=6, seg=16, n=2.6):
    """kit.contact_shadow's smooth radial falloff, but at a tenth of the cost.

    kit's version is 12 rings of 30 segments -- 25 KB of geometry per blob, and
    the well needs four of them plus a light pool.  Same construction, fewer
    rings and segments (this all sits 10 ft below the camera).  `tone` lighter
    than the floor makes it a light POOL instead of a shadow.
    """
    a = round(1.0 - (1.0 - strength) ** (1.0 / steps), 4)
    mat = Material("s17dc%s%d" % (tone.lstrip("#"), int(strength * 100)), tone,
                   roughness=0.98, opacity=a)
    for i in range(steps):
        s = 1.0 - 0.90 * (i / steps)
        v = [(cx, y + i * 0.0016, cz)]
        for k in range(seg):
            t = 2 * math.pi * k / seg
            ct, st = math.cos(t), math.sin(t)
            v.append((cx + rx * s * math.copysign(abs(ct) ** (2.0 / n), ct),
                      y + i * 0.0016,
                      cz + rz * s * math.copysign(abs(st) ** (2.0 / n), st)))
        m.add(Part(v, [(0, 1 + (k + 1) % seg, 1 + k) for k in range(seg)]), mat)


_TONE = {}


def shaft_tone(y, z, x):
    """Baked falloff for one patch of shaft lining.

    `staircase_looking_down.jpg` has an obvious bright pool at the bottom of the
    well thrown by the front door, dying away up the walls; round 2's shaft was
    one flat #b4b6b7 top to bottom, which is what the critic called "no light
    gradient at all".  There are no bounce lights in this renderer, so it is
    baked here: a vertical ramp times an inverse-square-ish term in the distance
    from the door opening.
    """
    ky = min(1.0, max(0.0, (y - FLOOR1) / (0.0 - FLOOR1)))
    d = math.hypot(max(0.0, SH_S0 - z) * 0.50, (x - 5.95) * 0.32)
    g = (1.0 - ky) ** 1.30 / (1.0 + (d / 5.4) ** 1.8)
    key = int(round(max(0.0, min(1.0, g)) * 48))
    if key not in _TONE:
        _TONE[key] = Material("s17wg%02d" % key,
                              mix("#c2c4c5", "#fbfcfc", key / 48.0),
                              roughness=0.95)
    return _TONE[key]


def _grid(m, y0, y1, a0, a1, ny, na, emit):
    for r in range(ny):
        ya, yb = y0 + (y1 - y0) * r / ny, y0 + (y1 - y0) * (r + 1) / ny
        for c in range(na):
            aa = a0 + (a1 - a0) * c / na
            ab = a0 + (a1 - a0) * (c + 1) / na
            emit(ya, yb, aa, ab)


def shaft_falloff(m):
    y0, y1 = FLOOR1, 0.0
    # east lining wall, the big one you look straight at coming down
    _grid(m, y0, y1, SH_N1, SH_S0, 16, 4, lambda ya, yb, aa, ab: vface_x(
        m, shaft_tone((ya + yb) / 2, (aa + ab) / 2, SH_E0), aa, ab, ya, yb,
        SH_E0 - 0.006, -1))
    # north lining, under the 2F landing
    _grid(m, y0, y1, 3.95, SH_E0, 14, 2, lambda ya, yb, aa, ab: vface_z(
        m, shaft_tone((ya + yb) / 2, SH_N1, (aa + ab) / 2), aa, ab, ya, yb,
        SH_N1 + 0.006, +1))
    # the end wall the front door is in: the door itself masks 4.55..7.35
    for (a0, a1) in ((SH_W1, 4.55), (7.35, SH_E0)):
        _grid(m, y0, y1, a0, a1, 14, 2, lambda ya, yb, aa, ab: vface_z(
            m, shaft_tone((ya + yb) / 2, SH_S0, (aa + ab) / 2), aa, ab, ya, yb,
            SH_S0 - 0.006, -1))
    _grid(m, FLOOR1 + 7.10, y1, SH_W1, SH_E0, 4, 3, lambda ya, yb, aa, ab:
          vface_z(m, shaft_tone((ya + yb) / 2, SH_S0, (aa + ab) / 2),
                  aa, ab, ya, yb, SH_S0 - 0.006, -1))
    # the far 1F west wall, coarser -- it is small on screen
    _grid(m, y0, -0.06, 6.28, SH_S0, 8, 2, lambda ya, yb, aa, ab: vface_x(
        m, shaft_tone((ya + yb) / 2, (aa + ab) / 2, SH_W1), aa, ab, ya, yb,
        SH_W1 + 0.006, +1))


# ------------------------------------------- what is actually at the bottom
MAT1 = Material("s17mat1", "#3d3d3f", roughness=0.99)
BAG = Material("s17bag", "#4a4a4d", roughness=0.85)
DOORW = Material("s17dorw", "#f7f6f3", roughness=0.55)
DOORL = Material("s17dorl", "#fcfbf9", roughness=0.50)
MAT2 = Material("s17mat2", "#4b4b4d", roughness=0.99)
CONS = Material("s17cons", "#f0efec", roughness=0.55)
CONS2 = Material("s17cons2", "#dedbd5", roughness=0.60)
LEAF = Material("s17leaf", "#5e7a52", roughness=0.85)
LEAF2 = Material("s17leaf2", "#6f8c5e", roughness=0.85)
BLOOM = Material("s17bloom", "#c58fa4", roughness=0.90)


def shaft_clutter(m):
    """The bottom of the flight is a ROOM in the photo, not a backdrop: a mat
    inside the front door, a shelf against the left-hand wall carrying flowers,
    a bag on the floor.  It is invented -- there is no real first floor modelled
    here -- so it stays sparse and low-contrast on purpose.
    """
    fy = FLOOR1
    # entry mat, with a contact shadow so it does not float
    decal(m, 5.62, 19.30, 1.05, 0.66, fy + 0.055, "#26262a", 0.26,
          steps=4, seg=14)
    bx(m, MAT2, 4.78, 6.46, fy + 0.062, fy + 0.098, 18.90, 19.86)
    bx(m, MAT1, 4.85, 6.39, fy + 0.098, fy + 0.110, 18.97, 19.79)
    # a narrow shelf/console against the east wall, left of the door coming down
    cx0, cx1, cz0, cz1 = 6.95, 7.90, 16.90, 18.55
    decal(m, (cx0 + cx1) / 2, (cz0 + cz1) / 2, 0.80, 1.30, fy + 0.055,
          "#26262a", 0.34, steps=4, seg=14)
    bx(m, CONS, cx0, cx1, fy + 2.42, fy + 2.55, cz0, cz1)          # top
    bx(m, CONS2, cx0 + 0.06, cx1 - 0.02, fy + 1.20, fy + 1.30,
       cz0 + 0.08, cz1 - 0.08)                                     # shelf
    for (a, b) in ((cz0 + 0.06, cz0 + 0.18), (cz1 - 0.18, cz1 - 0.06)):
        bx(m, CONS2, cx0 + 0.06, cx0 + 0.18, fy, fy + 2.42, a, b)
        bx(m, CONS2, cx1 - 0.18, cx1 - 0.06, fy, fy + 2.42, a, b)
    # flowers on it
    for (px, pz, r, h) in ((7.28, 17.35, 0.22, 0.42), (7.52, 18.10, 0.17, 0.34)):
        m.add(cylinder(r, h, 12, r_top=r * 0.82), CONS, at=(px, fy + 2.55, pz))
        leafy(m, px, fy + 2.55 + h - 0.04, pz, 0.34, 0.72, LEAF, n=7, seed=31)
        leafy(m, px, fy + 2.55 + h - 0.04, pz, 0.24, 0.55, LEAF2, n=5, seed=12)
        m.add(cylinder(0.055, 0.055, 8), BLOOM,
              at=(px + 0.10, fy + 2.55 + h + 0.62, pz - 0.06))
    # a bag left by the door
    m.add(rounded_box(0.50, 0.52, 0.36, 0.13, 3), BAG, at=(6.90, fy + 0.02, 18.95))
    decal(m, 6.90, 18.95, 0.44, 0.34, fy + 0.052, "#26262a", 0.26,
          steps=3, seg=12)


def string_section():
    """The closed string's own (z, y) section: the app's exact step profile down
    to the 1F floor.  Swept, this is 6 KB a side against the 17 KB of per-step
    boxes it replaces, and room 17 is sharing a 1.5 MB budget with three other
    builders this round."""
    pts = [(zspan(NST - 1)[0], ytop(NST - 1) + 0.10)]
    for i in range(NST - 1, -1, -1):
        _, zb = zspan(i)
        pts.append((zb, ytop(i) + (0.10 if i == NST - 1 else TR)))
        if i:
            pts.append((zb, ytop(i - 1) + TR))
    pts.append((SZB, FLOOR1))
    pts.append((zspan(NST - 1)[0], FLOOR1))
    return pts


def stringers(m):
    """The two closed strings.  Per-step white fill from the 1F floor up to the
    next tread, then ONE smooth raked board laid over the stepped edge -- the
    fill kills the app's blue-grey side faces at x 4.10 / 7.90, the board gives
    the clean rake the photos show."""
    sec = string_section()
    _sweep(m, WHT2, sec, WSK0, WSK1, smooth=False, closed=True)
    _sweep(m, WHT2, sec, ESK0, ESK1, smooth=False, closed=True)
    z0, z1 = SZB + 0.40, 8.42
    for (a0, a1) in ((WCAP0, WCAP1), (ECAP0, ECAP1)):
        raked(m, WHT, a0, a1, z0, z1, yn(z0) + 0.28, yn(z1) + 0.28, 0.55,
              extend=0.16)


def tread_section(y, za, zb):
    """A tread board's closed (z, y) section: flat top, a rolled front edge and
    a chamfered underside.  Swept in x this is one welded solid, which is both
    cheaper than the three boxes it replaces and gives the nosing a real roll
    instead of a bolted-on cylinder."""
    zf = zb + NOSE
    return ([(za - 0.05, y + TBT), (zf - TCR, y + TBT)]
            + _arc(zf - TCR, y + TBT - TCR, TCR, math.pi / 2, 0.0, 3)
            + [(zf, y - TBT + 0.040), (zf - 0.040, y - TBT),
               (za - 0.05, y - TBT)])


def treads(m):
    """Grey plank treads and WHITE risers.  The RUNNER is a separate piece
    (`Hall2F Stair Runner`) -- wrapping it properly costs ~140 KB and this
    piece is already near the 300 KB per-piece cap."""
    for i in range(NST):
        za, zb = zspan(i)
        y = ytop(i)
        _sweep(m, TRD[i % len(TRD)], tread_section(y, za, zb), TX0, TX1,
               smooth=False, closed=True)
        # Looking DOWN a flight you never see a riser -- they face away -- so
        # the flight reads as one flat ramp unless each tread carries the shade
        # the nosing above throws on it.  That line, not the risers, is what
        # gives `staircase_looking_down.jpg` its rhythm.  Only the two EXPOSED
        # lanes need it; the runner piece carries its own.
        for (a, b) in ((TX0, RUN0), (RUN1, TX1)):
            rect_up(m, SHDW, a, b, y + TBT + 0.004, za + 0.030, za + 0.108)
            rect_up(m, SHDW2, a, b, y + TBT + 0.003, za + 0.108, za + 0.196)
        # the riser BELOW this tread: white, proud of the app's own step face
        ylo = (ytop(i - 1) + TBT) if i else FLOOR1
        bx(m, WHT, TX0, TX1, ylo - 0.004, y - TBT + 0.004,
           zb - 0.004, zb + RISF)
        # a hairline of shade where the riser dies into the tread below it
        if i:
            vface_z(m, WHT2, TX0, TX1, ylo - 0.004, ylo + 0.055,
                    zb + RISF + 0.005, +1)


# ============================================== 2b  the runner, as real cloth
def piece_runner():
    """ONE strip of cloth draped down the whole flight.

    Round 2 painted a lighter quad on each tread top: it stopped dead at every
    nosing, had no thickness, no riser, and its per-step tone alternation read
    as tiled rectangular blocks.  This is a real solid instead -- a swept band
    that runs tread -> rolled nosing -> down the riser -> next tread, 17 times
    without a break, 2.78 ft wide so ~4.7 in of tread shows either side, 0.046
    ft thick with its cut edges walled, and a two-step contact-shadow line
    tracking that same wrap so it sits ON the tread instead of hovering.
    """
    m = Model()
    skin = runner_skin()
    outer = _offset(skin, RT)
    # pile lanes: irregular widths so the band never reads as a regular comb,
    # tone varying only ACROSS the strip so nothing repeats down its length
    rn = Rnd(9311)
    w = [rn.f(0.75, 1.30) for _ in range(12)]
    s = sum(w)
    xs, x = [RUN0], RUN0
    for k in w:
        x += (RUN1 - RUN0) * k / s
        xs.append(x)
    xs[-1] = RUN1
    for k in range(12):
        edge = min(k, 11 - k) == 0            # the woven binding down each edge
        _sweep(m, RUNED if edge else RUNT[(k * 5 + 1) % len(RUNT)],
               outer, xs[k], xs[k + 1])
    # the band's own THICKNESS.  Without these two walls it is still a decal.
    _sweep_wall(m, RUNED, outer, skin, RUN0, -1, smooth=True)
    _sweep_wall(m, RUNED, outer, skin, RUN1, +1, smooth=True)
    # contact shadow where the cloth meets the tread -- two bands, following
    # the SAME wrap, so it runs down every riser as well as across every tread
    lift = _offset(skin, 0.008)
    for (a0, a1, mt) in ((RUN0 - 0.045, RUN0 - 0.004, RUNSH1),
                         (RUN0 - 0.102, RUN0 - 0.045, RUNSH2),
                         (RUN1 + 0.004, RUN1 + 0.045, RUNSH1),
                         (RUN1 + 0.045, RUN1 + 0.102, RUNSH2)):
        _sweep(m, mt, lift, a0, a1)
    # the shade the nosing above throws across the back of each tread run
    for i in range(NST):
        za, zb = zspan(i)
        y = ytop(i) + TBT + RT
        rect_up(m, RUNSH3, RUN0, RUN1, y + 0.004, za + 0.048, za + 0.140)
        rect_up(m, RUNSH4, RUN0, RUN1, y + 0.003, za + 0.140, za + 0.262)
    return m


def piece_well():
    m = Model()
    shaft(m)
    return m


def piece_flight():
    m = Model()
    stringers(m)
    treads(m)
    return m


# ================================================== 3  balustrade + handrail
def _area(pts):
    return 0.5 * sum(pts[i][0] * pts[(i + 1) % len(pts)][1]
                     - pts[(i + 1) % len(pts)][0] * pts[i][1]
                     for i in range(len(pts)))


def _round_prof(w, h, r, seg=4):
    """A rounded-rectangle section in (x, y), CCW."""
    pts = []
    for (cx, cy, a0) in ((w / 2 - r, h / 2 - r, 0.0),
                         (-(w / 2 - r), h / 2 - r, math.pi / 2),
                         (-(w / 2 - r), -(h / 2 - r), math.pi),
                         (w / 2 - r, -(h / 2 - r), 1.5 * math.pi)):
        for s in range(seg + 1):
            a = a0 + (math.pi / 2) * s / seg
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def raked_prof(m, mat, prof, cx, z_bot, z_top, y_bot, y_top, extend=0.0,
               smooth=True):
    """`raked`, but sweeping an arbitrary section instead of a box.

    `raked` builds the handrail as a single box, which is why the round-2 rail
    read as "a chunky faceted low-poly bar" -- four flat faces and four hard
    90-degree arrises.  This sweeps a 20-point rounded section with averaged
    normals, so the rail has a shoulder that catches light along its length.
    """
    dz, dy = z_bot - z_top, y_top - y_bot
    L = math.hypot(dz, dy) + 2.0 * extend
    ang = math.atan2(dy, dz)
    pts = [(px, -py) for (px, py) in prof]     # prism extrudes along +Y
    if _area(pts) < 0:
        pts.reverse()
    m.add(prism(pts, L, anchor="center", smooth=smooth), mat,
          at=(cx, (y_bot + y_top) / 2.0, (z_bot + z_top) / 2.0),
          rot_x=R(90) + ang)


RH = 2.86                                      # rail height above the nosing
RAIL_W, RAIL_H = 0.245, 0.175                  # the handrail's own section


def _bracket(m, zb):
    """One of the two BLACK brackets `staircase_looking_down.jpg` shows: a pad
    on the knee wall, a plate, a sloping arm and a saddle under the rail.  The
    round-2 rail hung on nothing at all over this stretch."""
    yr = yn(zb) + RH
    m.add(cylinder(0.135, 0.050, 14), BLK, at=(3.952, yr - 0.44, zb),
          rot_z=R(-90))                                        # wall pad
    bx(m, BLK, 3.955, 4.020, yr - 0.58, yr - 0.30, zb - 0.070, zb + 0.070)
    ax0, ax1 = 4.000, RAILX
    ay0, ay1 = yr - 0.52, yr - 0.16
    L = math.hypot(ax1 - ax0, ay1 - ay0)
    m.add(box(L + 0.06, 0.090, 0.105, anchor="center"), BLK,
          at=((ax0 + ax1) / 2.0, (ay0 + ay1) / 2.0, zb),
          rot_z=math.atan2(ay1 - ay0, ax1 - ax0))              # sloping arm
    bx(m, BLK, RAILX - 0.115, RAILX + 0.115, yr - 0.125, yr - 0.055,
       zb - 0.085, zb + 0.085)                                 # saddle


def piece_rail():
    """Open (WEST) side.  Low down it is a white square-baluster balustrade on a
    chunky BLACK newel; higher up the same BLACK rake of handrail runs along the
    inner face of the white knee wall on BLACK brackets.  One continuous rail
    line: it crosses the 2F floor level at z = 11.26, which is exactly where the
    knee wall takes over from the balusters."""
    m = Model()
    z_lo, z_hi = 18.14, 8.30                   # the rail's own run
    y_lo, y_hi = yn(z_lo) + RH, yn(z_hi) + RH
    zcross = SZB + (RH + FY + RS) / SLOPE      # where the rail meets y = 0

    # ---- the white BOTTOM RAIL.  Round 2's balusters ended in mid air above
    # the string cap ("the balusters just terminate in air").  In
    # `staircase_looking_up.jpg` they stand on a shoe rail that runs the rake
    # on top of the closed string, and each one has a small square shoe.
    zb_lo, zb_hi = 18.30, zcross + 0.10
    raked_prof(m, WHT, _round_prof(0.295, 0.150, 0.035, 3), BALX,
               zb_lo, zb_hi, yn(zb_lo) + 0.625, yn(zb_hi) + 0.625, extend=0.10)

    # ---- balusters, only where the rail is out in the open well
    z = 18.02
    while z > zcross + 0.30:
        y0b = yn(z) + 0.690
        top = yn(z) + RH - RAIL_H / 2 + 0.02
        m.add(box(0.100, top - y0b, 0.100), WHT, at=(BALX, y0b, z))
        bx(m, WHT2, BALX - 0.072, BALX + 0.072, y0b - 0.010, y0b + 0.075,
           z - 0.072, z + 0.072)                             # shoe at the foot
        z -= 0.295

    # ---- the black handrail, one continuous raked bar with a rounded section
    raked_prof(m, BLK, _round_prof(RAIL_W, RAIL_H, 0.058, 4), RAILX,
               z_lo, z_hi, y_lo, y_hi, extend=0.20)
    # a short level return at the head that dies INTO the knee wall's east face
    # rather than stopping in mid air (from the hallway you look over the wall,
    # and a black stub floating above it reads as debris)
    raked_prof(m, BLK, _round_prof(RAIL_W, RAIL_H, 0.058, 4), RAILX,
               z_hi + 0.14, 8.00, y_hi, y_hi, extend=0.04)
    bx(m, BLK, 3.90, RAILX + 0.10, y_hi - 0.090, y_hi + 0.090, 8.02, 8.28)

    # ---- black brackets on the knee wall's inner face (x 3.95)
    for zb in (8.72, 10.18):
        _bracket(m, zb)
    return _newel(m, y_lo)


# ======================================================== 3b  the knee wall
KW_X, KW_Z0, KW_Z1, KW_H = 3.95, 6.80, 16.70, 3.05
KW_T = 0.42
# Ported here from scratchpad/circ/r17.py (which must not be re-run: it would
# re-place the deleted fake well panel).  Geometry is unchanged so the piece
# does not move; what is new is that the whites are no longer ONE white -- cap,
# body, well face and the shade under the cap nose are four values -- and the
# wall now has a contact line where it meets the floor on both sides.
KWCAP = Material("s17kwcap", "#fbfaf7", roughness=0.58)   # cap, catches the sun
KWBODY = Material("s17kwbod", "#f2f1ed", roughness=0.62)  # hall face
KWWELL = Material("s17kwwel", "#e6e4df", roughness=0.64)  # face into the well
KWNECK = Material("s17kwnek", "#d9d7d1", roughness=0.66)  # under the cap nose
KWFOOT = Material("s17kwfut", "#c8c6c0", roughness=0.72)  # contact line


def piece_kneewall():
    """The white capped half wall round the stairwell -- solid, no spindles,
    which is what every shot of this floor shows."""
    m = Model()
    x, z0, z1, t = KW_X, KW_Z0, KW_Z1, KW_T
    bx(m, KWBODY, x - t, x, 0.0, KW_H, z0, z1)                 # body
    bx(m, KWWELL, x - 0.010, x, 0.0, KW_H, z0, z1)             # well face
    bx(m, KWBODY, x - t - 0.055, x - t, 0.0, BB_H, z0, z1)     # skirting return
    bx(m, KWBODY, x, x + 0.055, 0.0, BB_H, z0, z1)
    bx(m, KWFOOT, x - t - 0.061, x - t - 0.055, 0.0, 0.045, z0, z1)
    bx(m, KWFOOT, x + 0.055, x + 0.061, 0.0, 0.045, z0, z1)
    # a wide flat cap with a small nose either side (the photo's rail cap)
    bx(m, KWCAP, x - t - 0.10, x + 0.10, KW_H, KW_H + 0.13, z0 - 0.10, z1)
    bx(m, KWNECK, x - t - 0.07, x + 0.07, KW_H - 0.05, KW_H, z0 - 0.07, z1)
    # newel block where the run starts, at the head of the flight
    bx(m, KWBODY, x - t - 0.09, x + 0.09, 0.0, KW_H + 0.26, z0 - 0.42, z0 + 0.05)
    bx(m, KWCAP, x - t - 0.16, x + 0.16, KW_H + 0.26, KW_H + 0.40,
       z0 - 0.49, z0 + 0.12)
    return m

    # ---- the newel: chunky, black, standing on the 1F floor, with a real base
    # and a real cap.  It also has to READ as carrying the rail, so the rail's
    # bottom end runs into its neck.
    nx, nz = BALX, 18.34
    ntop = y_lo + 0.34
    bx(m, BLK, nx - 0.300, nx + 0.300, FLOOR1, FLOOR1 + 0.30,
       nz - 0.300, nz + 0.300)                                    # plinth
    bx(m, BLK, nx - 0.325, nx + 0.325, FLOOR1 + 0.28, FLOOR1 + 0.38,
       nz - 0.325, nz + 0.325)                                    # base cap
    bx(m, BLK, nx - 0.235, nx + 0.235, FLOOR1 + 0.36, ntop - 0.34,
       nz - 0.235, nz + 0.235)                                    # shaft
    bx(m, BLK, nx - 0.285, nx + 0.285, ntop - 0.34, ntop - 0.22,
       nz - 0.285, nz + 0.285)                                    # collar
    bx(m, BLK, nx - 0.250, nx + 0.250, ntop - 0.22, ntop - 0.06,
       nz - 0.250, nz + 0.250)                                    # neck
    bx(m, BLK, nx - 0.290, nx + 0.290, ntop - 0.06, ntop + 0.045,
       nz - 0.290, nz + 0.290)                                    # cap plate
    m.add(cylinder(0.135, 0.15, 14, r_top=0.050), BLK,
          at=(nx, ntop + 0.045, nz))                               # dome
    m.add(cylinder(0.050, 0.050, 10), BLK, at=(nx, ntop + 0.195, nz))
    return m


# ------------------------------------------------------------------- driver
def save_and_place(name, m, fname=None):
    path = os.path.join(HERE, "glb",
                        (fname or name.replace(" ", "_").lower()) + ".glb")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    m.save(path)
    lo, hi = m.bounds()
    pos = ((lo[0] + hi[0]) / 2.0, lo[1], (lo[2] + hi[2]) / 2.0)
    res = place(name, path, ROOM, pos=pos, rot_y_deg=0.0, scale=1.0)
    kb = os.path.getsize(path) / 1024.0
    print(f"  {name:26s} size={tuple(round(hi[i]-lo[i],2) for i in range(3))}"
          f"  pos=({pos[0]:.2f},{pos[1]:.2f},{pos[2]:.2f})  {kb:7.1f} KB"
          f"  {res['action']}")


# ============================================== 4  the corner-stub cladding
# `house.js buildRoom` draws every wall run from u = -WALL_THICKNESS to
# u = len + WALL_THICKNESS so corners overlap, but clamps every opening to
# 0 <= off and off+width <= len+ (it only ever widens to the shape edge).  So a
# fully cut-away edge ALWAYS keeps a 0.35 ft full-height block at each end.
# For room 17's notch that leaves two of them at the corner (3.95, 7.7):
#
#   edge 2, far end   u 4.15..4.50 -> x 3.60..3.95, z 7.70..8.05
#                     -- removable: widen opening 133 to 4.48 (its shape ends
#                        at len+t = 4.50), leaving 0.02 ft, and what is left is
#                        inside the knee wall's own body up to y 3.05 anyway.
#   edge 3, near end  u -0.35..0   -> x 3.95..4.30, z 7.35..7.70
#                     -- NOT removable at any width: `off` is clamped to >= 0,
#                        so no opening can ever reach u < 0.
#
# The photo has nothing there, so the second one gets clad instead: four faces
# painted to the value the room's own walls render at, plus the room's white
# baseboard, so it reads as a slim painted pier rather than a white post.
# Solved from a TWO-POINT probe on the real render (ROOM-BRIEF: fit, do not
# guess).  west face: albedo 156 -> 215.7, 121 -> 197.3, so L = 133.6 + 0.526a.
# south face: 168 -> 203.9, 138 -> 193.2, so L = 143.9 + 0.357a.  Target is the
# 158-170 the room's own walls render at from this pose.  The big constant is
# ambient/IBL, which is why a "wall coloured" pier still glowed white.
# Solved by probing the real render, one face at a time -- and the four faces
# of this little box need FOUR different albedos, because the scene has one sun
# and no bounce: at a single albedo 111 the pier's south face rendered 178 and
# its north face 58, against room surfaces that sit at 157-170 from both poses.
#   south  albedo 111 -> 178   (keep, it is already in range)
#   north  albedo 111 ->  58   -> white is the most it can be given
#   west   albedo 140 -> 100   -> 223
PIER = Material("s17pier", "#6f7273", roughness=0.95)      # south face
PIERN = Material("s17piern", "#fbfbfa", roughness=0.95)    # north face, no sun
PIERW = Material("s17pierw", "#dfe0e0", roughness=0.95)    # west face
PIERE = Material("s17piere", "#9aa0a2", roughness=0.95)    # east, into the well


def piece_pier():
    """One clad pier that absorbs BOTH leftovers at the notch corner.

    Its west face sits 0.05 ft east of the knee wall's, so from either hallway
    pose the knee wall and its cap pass in front of the pier and only the part
    above the cap (y > 3.18) is ever seen -- a slim painted chase where the hall
    widens, instead of two bare wall end-caps.
    """
    m = Model()
    x0, x1, z0, z1 = 3.58, 4.33, 7.30, 8.10
    t, top = 0.012, 7.90
    bx(m, PIERW, x0 - t, x0, 0.0, top, z0 - t, z1 + t)          # west
    bx(m, PIERE, x1, x1 + t, 0.0, top, z0 - t, z1 + t)          # east
    bx(m, PIERN, x0 - t, x1 + t, 0.0, top, z0 - t, z0)          # north
    bx(m, PIER, x0 - t, x1 + t, 0.0, top, z1, z1 + t)           # south
    bx(m, PIERN, x0, x1, top - t, top, z0, z1)                  # soffit cap
    bb = 0.055                                                  # room baseboard
    bx(m, WHT, x0 - t - bb, x1 + t + bb, 0.0, BB_H,
       z0 - t - bb, z1 + t + bb)
    return m


if __name__ == "__main__":
    # "pier" is NO LONGER in the default set. It clad the floor-to-ceiling
    # wall stubs that buildRoom used to leave at the notch corner; house.js
    # now skips a wall outright when an opening spans it entirely, so the
    # stubs are gone and the pier is a white box standing in an empty hall.
    # The object was deleted 22 Aug 2026. Pass "pier" explicitly to rebuild
    # it, but check a doll_se render first -- it should not be needed again.
    # `Hall2F Floor Planks` is NOT in the default set either: it is another
    # builder's piece this round, so pass "planks" explicitly to touch it.
    which = sys.argv[1:] or ["well", "flight", "runner", "rail"]
    if "planks" in which:
        save_and_place("Hall2F Floor Planks", piece_floor_planks())
    if "runner" in which:
        save_and_place("Hall2F Stair Runner", piece_runner())
    if "well" in which:
        # name carries 'floor' on purpose: objects.js SURFACE_RE then marks this
        # room-scale lining unpickable, like the ceiling and baseboard runs
        save_and_place("Hall2F Stairwell Floor Lining", piece_well())
    if "flight" in which:
        save_and_place("Hall2F Stair Flight", piece_flight())
    if "rail" in which:
        save_and_place("Hall2F Stair Rail", piece_rail())
    if "pier" in which:
        save_and_place("Hall2F Stair Pier", piece_pier())