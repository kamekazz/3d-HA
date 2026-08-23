"""Room 17 -- the four STAIR pieces, rebuilt for the RE-TRACED footprint.

    Hall2F Stair Flight            plank treads, white risers, raking skirts
    Hall2F Stair Runner            one continuous band of cloth down the flight
    Hall2F Stair Rail              black rail, cast brackets, newel, balusters
    Hall2F Stairwell Floor Lining  the shaft, the 1F hall, and its daylight

Every coordinate here is ROOM-17-LOCAL feet.  Room 17's anchor is world
(6.70, 18.00, 6.55), so local = world - anchor, and local y = 0 is the second
floor slab.

The flight itself is app data (`stairs` row 7, floor_id 2) and MAY NOT be moved.
Re-derived from house.js buildStairs:

    row 7 : x 14.6..18.4  z 13.5..23.3  direction 'n'  on floor 2 (rise 10.0)
    steps = round(10.0 / 0.6) = 17
    going = 9.8 / 17 = 0.57647 ft (6.92 in)   rise = 10 / 17 = 0.58824 ft (7.06 in)

    local:  x 7.90..11.70,  z 6.95..16.75,  y -10.0..0.0
    step i (0 = bottom): top face y = -10 + RS*(i+1)
                         z from ZH(i) = 16.75-(i+1)*TR  to  ZL(i) = 16.75-i*TR

That is a 45.6-degree pitch.  See the report -- it is 8 degrees steeper than the
photograph and there is nothing this piece can do about it.

Tone is carried in Part(colors=...) -- glTF COLOR_0, which three multiplies into
the base colour.  One material per surface class, all the grain / falloff /
contact darkening in the vertex colours.  It is about 4 bytes a vertex against
the ~24 that splitting the same field into per-cell material buckets costs, and
it interpolates, so it gives gradients a cell field cannot.
"""

import math
import os
import sys

sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\shellpass")

from kit import (Model, Material, box, rounded_box, cylinder, quad, Part,   # noqa
                 bx, rect_up, rect_down, Rnd, mix, R)
from roomkit.place import place

HERE = os.path.dirname(os.path.abspath(__file__))
GLB = os.path.join(HERE, "s2glb")
ROOM = 17

# ------------------------------------------------------------- the app flight
SX0, SX1 = 7.90, 11.70          # the app's own step boxes, local x
SZB = 16.75                     # local z of the bottom (south) face of step 0
NST = 17
TR = 9.8 / 17.0
RS = 10.0 / 17.0
FY = -10.0                      # local y of the first-floor slab


def ytop(i):
    return FY + RS * (i + 1)


def ZH(i):
    return SZB - (i + 1) * TR   # north / high edge of step i


def ZL(i):
    return SZB - i * TR         # south / low edge of step i = its riser plane


# ---------------------------------------------------------------- the shaft
WELL_X0, WELL_X1 = 7.61, 11.92  # room 17 edge 1 (knee wall) .. room 28 east
WELL_Z0, WELL_Z1 = 6.81, 16.89  # room 17 edge 0 (open cut) .. room 28 south
# the first-floor hallway below (room 12, world x 10.7..18.3 z 4.6..32.2)
H_X0, H_X1 = 4.00, 11.58        # its inner wall faces, local, inset 0.02
H_Z0, H_Z1 = 5.20, 25.63        # ... and the front-door wall at the south end
DOOR_X0, DOOR_X1 = 6.40, 9.30   # room 12 opening 117, re-derived to local
SL_W = (5.35, 6.15)             # room 12 opening 119 -- sidelight, west of it
SL_E = (9.55, 10.35)            # room 12 opening 118 -- sidelight, east of it

# ------------------------------------------------------------------- x lanes
WSTR0, WSTR1 = 7.70, 7.92       # west string board (the open, balustrade side)
ESK0, ESK1 = 11.40, 11.58       # east skirt board (against the shaft wall)
TX0, TX1 = 7.92, 11.40          # the treads, 3.48 ft of them
RUNW = 2.62                     # runner, leaving 0.43 ft (5.2 in) of tread each side
RUN0 = (TX0 + TX1 - RUNW) / 2.0
RUN1 = RUN0 + RUNW
BALX = 7.81                     # centre line of the balusters and the rail
SPLIT = 8                       # steps 8..16 run against a wall; 0..7 open

# ------------------------------------------------------------------ sections
TT = 0.090                      # tread board thickness
NOSE = 0.105                    # nosing overhang past the riser face
RIS = 0.020                     # riser face, proud of the app's own step box
NR = 0.030                      # radius rolled on the tread's front top arris
RT = 0.048                      # runner thickness
RNR = 0.075                     # the radius the runner turns at a nosing


# ============================================================ colour plumbing
def _l(u):
    return u / 12.92 if u <= 0.04045 else ((u + 0.055) / 1.055) ** 2.4


def _s(u):
    u = max(0.0, min(1.0, u))
    return 12.92 * u if u <= 0.0031308 else 1.055 * u ** (1 / 2.4) - 0.055


def gm(target, base):
    """Vertex colour that renders sRGB value `base` (0-255) as `target`."""
    f = _l(target / 255.0) / max(_l(base / 255.0), 1e-9)
    g = _s(f ** (1 / 2.4) if False else f)   # keep it linear-correct
    return (g, g, g)


def _mk_gm(base):
    tbl = [gm(v, base) for v in range(256)]

    def f(target):
        return tbl[max(0, min(255, int(round(target))))]
    return f


class Noise:
    """Value noise on a lattice -- smooth, tileable enough, deterministic."""

    def __init__(self, seed, scale):
        self.s, self.k = seed, 1.0 / scale

    def _h(self, i, j):
        n = (i * 374761393 + j * 668265263 + self.s * 1442695040888963407) & 0xFFFFFFFF
        n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
        return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0 - 0.5

    def __call__(self, a, b):
        a, b = a * self.k, b * self.k
        i, j = math.floor(a), math.floor(b)
        u, v = a - i, b - j
        u = u * u * (3 - 2 * u)
        v = v * v * (3 - 2 * v)
        h = self._h
        return ((h(i, j) * (1 - u) + h(i + 1, j) * u) * (1 - v)
                + (h(i, j + 1) * (1 - u) + h(i + 1, j + 1) * u) * v)


# ---------------------------------------------------------------- materials
# Five separate whites.  Every critic in round 1 said our whites were one white;
# in the photographs the riser, the skirt, the baluster, the door and the
# baseboard all meter differently, and the riser is the brightest of them.
M_PLANK = Material("s2plk", "#b9b6b2", roughness=0.86)          # tread + floors
M_GROOVE = Material("s2grv", "#4d4c49", roughness=0.95)         # plank joints
M_RISER = Material("s2ris", "#fdfcfa", roughness=0.54)          # riser, brightest
M_SKIRT = Material("s2skt", "#f5f3ef", roughness=0.60)          # raking skirt
M_BAL = Material("s2bal", "#f0eee9", roughness=0.58)            # balusters
M_CARPET = Material("s2car", "#cdc8c1", roughness=0.99)         # the runner
M_BLACK = Material("s2blk", "#34343a", roughness=0.40, metallic=0.22)
M_BLACK2 = Material("s2blk2", "#232327", roughness=0.55, metallic=0.10)
M_WALL = Material("s2wal", "#d8dadb", roughness=0.95)           # shaft paint
M_DOOR = Material("s2dor", "#fbfaf7", roughness=0.50)
M_GLASS = Material("s2gls", "#eef4fb", roughness=0.25,
                   emissive="#fdfbf3", emissive_strength=3.4, double_sided=False)
M_GLASS2 = Material("s2gls2", "#dfe9f2", roughness=0.30,
                    emissive="#e6f0e2", emissive_strength=1.5, double_sided=False)

PLK = _mk_gm(0xB9)
RIS_ = _mk_gm(0xFD)
SKT = _mk_gm(0xF5)
BAL = _mk_gm(0xF0)
CAR = _mk_gm(0xCD)
WAL = _mk_gm(0xD8)
GRV = _mk_gm(0x4D)
BLK = _mk_gm(0x34)
DOR = _mk_gm(0xFB)


# ------------------------------------------------------------------ geometry
def band(m, mat, poly, xs, cfun, smooth=True, flip=False):
    """Sweep a (z, y) polyline across a list of x stations.

    Wound so that a polyline running in +z with x increasing faces UP/OUT.
    `cfun(x, y, z)` returns the vertex colour.
    """
    nz = len(poly)
    v, c, t = [], [], []
    for x in xs:
        for (z, y) in poly:
            v.append((x, y, z))
            c.append(cfun(x, y, z))
    for i in range(len(xs) - 1):
        for j in range(nz - 1):
            a, b = i * nz + j, i * nz + j + 1
            cc, d = (i + 1) * nz + j, (i + 1) * nz + j + 1
            t += [(a, d, b), (a, cc, d)] if flip else [(a, b, d), (a, d, cc)]
    m.add(Part(v, t, smooth=smooth, colors=c), mat)


def slab(m, mat, x0, x1, z0, z1, y, cfun, nx=2, nz=2, down=False):
    """A horizontal vertex-toned rectangle, nx x nz cells."""
    xs = [x0 + (x1 - x0) * i / nx for i in range(nx + 1)]
    zs = [z0 + (z1 - z0) * j / nz for j in range(nz + 1)]
    v, c, t = [], [], []
    for x in xs:
        for z in zs:
            v.append((x, y, z))
            c.append(cfun(x, z))
    n = len(zs)
    for i in range(nx):
        for j in range(nz):
            a, b = i * n + j, i * n + j + 1
            cc, d = (i + 1) * n + j, (i + 1) * n + j + 1
            t += [(a, b, d), (a, d, cc)] if down else [(a, d, b), (a, cc, d)]
    m.add(Part(v, t, smooth=True, colors=c), mat)


def wall_x(m, mat, x, z0, z1, y0, y1, cfun, nz=8, ny=8, out=+1):
    zs = [z0 + (z1 - z0) * j / nz for j in range(nz + 1)]
    ys = [y0 + (y1 - y0) * j / ny for j in range(ny + 1)]
    v, c, t = [], [], []
    for z in zs:
        for y in ys:
            v.append((x, y, z))
            c.append(cfun(y, z))
    n = len(ys)
    for i in range(nz):
        for j in range(ny):
            a, b = i * n + j, i * n + j + 1
            cc, d = (i + 1) * n + j, (i + 1) * n + j + 1
            t += [(a, b, d), (a, d, cc)] if out > 0 else [(a, d, b), (a, cc, d)]
    m.add(Part(v, t, smooth=True, colors=c), mat)


def wall_z(m, mat, z, x0, x1, y0, y1, cfun, nx=8, ny=8, out=+1):
    xs = [x0 + (x1 - x0) * j / nx for j in range(nx + 1)]
    ys = [y0 + (y1 - y0) * j / ny for j in range(ny + 1)]
    v, c, t = [], [], []
    for x in xs:
        for y in ys:
            v.append((x, y, z))
            c.append(cfun(y, x))
    n = len(ys)
    for i in range(nx):
        for j in range(ny):
            a, b = i * n + j, i * n + j + 1
            cc, d = (i + 1) * n + j, (i + 1) * n + j + 1
            t += [(a, d, b), (a, cc, d)] if out > 0 else [(a, b, d), (a, d, cc)]
    m.add(Part(v, t, smooth=True, colors=c), mat)


def _arc(cz, cy, r, a0, a1, seg):
    return [(cz + r * math.cos(a0 + (a1 - a0) * k / seg),
             cy + r * math.sin(a0 + (a1 - a0) * k / seg))
            for k in range(seg + 1)]


# =============================================================== 1  the flight
GRAIN = Noise(9137, 0.55)       # long grain along a plank
FIG = Noise(4021, 0.16)         # fine figure
BLOT = Noise(715, 2.6)          # slow blotch, walls


def tread_cols():
    """x stations across a tread: fine where the tread is EXPOSED, coarse under
    the runner where nothing can be seen."""
    xs = []
    x = TX0
    while x < RUN0 - 1e-6:
        xs.append(x)
        x += 0.070
    xs.append(RUN0)
    for k in range(1, 4):
        xs.append(RUN0 + (RUN1 - RUN0) * k / 4.0)
    xs.append(RUN1)
    x = RUN1 + 0.070
    while x < TX1 - 1e-6:
        xs.append(x)
        x += 0.070
    xs.append(TX1)
    return xs


TCOLS = tread_cols()


def tread_tone(i):
    """Base value of step i's tread board.  The flight darkens into the middle
    of the well and lifts again at the bottom where the front door throws light
    in -- the photograph's flight is NOT one value end to end."""
    f = i / (NST - 1.0)                      # 0 bottom, 1 top
    v = 150.0 - 26.0 * math.exp(-((f - 0.30) ** 2) / 0.10)
    v += 12.0 * math.exp(-(f ** 2) / 0.035)  # bounce off the 1F floor
    return v


def flight_treads(m):
    for i in range(NST):
        y = ytop(i)
        zr = ZL(i) + RIS               # riser plane, proud of the app box
        zf = zr + NOSE                 # front of the nosing
        zb = ZH(i) - 0.02              # back, tucked under the riser above
        base = tread_tone(i)
        # closed section: top -> rolled arris -> front face -> underside -> back
        poly = ([(zb, y)]
                + [(zf - NR, y)]
                + _arc(zf - NR, y - NR, NR, math.pi / 2, 0.0, 3)
                + [(zf, y - TT + 0.02), (zf - 0.02, y - TT), (zb, y - TT)])

        def cf(x, yy, z, base=base, y=y, zb=zb, zf=zf):
            t = base
            # lengthwise plank grain: streaks running ACROSS the stair
            t += 11.0 * GRAIN(x * 0.35, z * 3.1) + 5.0 * FIG(x, z * 2.2)
            # the shade the nosing above throws on the back of the tread run
            d = (z - zb) / 0.26
            if d < 1.0:
                t -= 30.0 * (1.0 - d) ** 1.3
            # under the nosing roll and on the front face: contact darkening
            if yy < y - 0.012:
                t -= 34.0 * min(1.0, (y - yy) / TT)
            # the runner's own contact shade, spilling onto the bare tread
            e = min(abs(x - RUN0), abs(x - RUN1))
            if RUN0 - 0.16 < x < RUN1 + 0.16:
                t -= 26.0 * max(0.0, 1.0 - e / 0.16) ** 1.2
            # the skirt boards darken the tread where they land on it
            t -= 22.0 * max(0.0, 1.0 - (x - TX0) / 0.13)
            t -= 22.0 * max(0.0, 1.0 - (TX1 - x) / 0.13)
            return PLK(t)

        band(m, M_PLANK, poly, TCOLS, cf, smooth=False)

        # the riser BELOW this tread -- white, and the brightest white in shot
        ylo = (ytop(i - 1) - 0.004) if i else FY - 0.02
        yhi = y - TT + 0.006
        rb = 196.0 + 10.0 * math.exp(-((i / (NST - 1.0)) ** 2) / 0.05)

        def rf(yy, x, ylo=ylo, yhi=yhi, rb=rb):
            t = rb
            # the nosing's shadow across the top of the riser -- the single
            # strongest cue that a tread overhangs at all
            d = (yhi - yy) / 0.115
            if d < 1.0:
                t -= 58.0 * (1.0 - d) ** 0.85
            # and the tread below occludes its foot
            d = (yy - ylo) / 0.075
            if d < 1.0:
                t -= 26.0 * (1.0 - d) ** 1.2
            t -= 30.0 * max(0.0, 1.0 - (x - TX0) / 0.10)
            t -= 30.0 * max(0.0, 1.0 - (TX1 - x) / 0.10)
            t += 5.0 * BLOT(x, yy * 3)
            return RIS_(t)

        wall_z(m, M_RISER, zr, TX0, TX1, ylo, yhi, rf, nx=14, ny=8, out=+1)


def skirt_poly(top_off):
    """(z, y) polyline of a raking skirt board: the stepped bottom edge that
    follows the treads, closed by a straight rake `top_off` above the nosings."""
    lo = []
    for i in range(NST - 1, -1, -1):
        zr, zh = ZL(i) + RIS, ZH(i)
        lo.append((zh - 0.02, ytop(i) - TT))
        lo.append((zr, ytop(i) - TT))
        lo.append((zr, (ytop(i - 1) - TT) if i else FY - 0.02))
    lo.append((SZB + RIS, FY - 0.02))
    # straight rake over the top, from the bottom back to the head
    zt, zbm = ZH(NST - 1) - 0.02, SZB + RIS
    yt = ytop(NST - 1) + top_off
    ybm = ytop(0) - TT + top_off - RS * 0.0
    ybm = FY + top_off + 0.10
    hi = [(zbm, ybm), (zt, yt)]
    return hi + lo[::-1] if False else lo + [(zbm, ybm), (zt, yt)]


def flight_skirts(m):
    """A white painted skirt board raking down each side of the flight.

    The east one is the 'crisp white painted skirt board raking down the wall'
    the round-1 critic asked for; the west one is the string the balusters and
    the newel stand on.
    """
    for (a0, a1, side) in ((WSTR0, WSTR1, "w"), (ESK0, ESK1, "e")):
        pts = skirt_poly(0.60)

        def cf(x, y, z, side=side):
            t = 214.0
            # falls off down the well like every other surface in the photo
            f = (y - FY) / 10.0
            t -= 26.0 * (1.0 - f) ** 1.1
            t += 14.0 * math.exp(-(((y - FY) / 1.8) ** 2))   # front-door bounce
            t += 4.5 * BLOT(z * 0.7, y * 0.7)
            # a caulk/contact line where the board meets the treads
            return SKT(t)

        band(m, M_SKIRT, pts, [a0, a1], cf, smooth=False, flip=(side == "e"))
        # the exposed vertical face of the board
        x = a0 if side == "w" else a1
        prof = [(z, y) for (z, y) in pts]
        v, c, t = [], [], []
        for (z, y) in prof:
            v.append((x, y, z))
            c.append(cf(x, y, z))
        n = len(prof)
        for k in range(1, n - 1):
            t.append((0, k, k + 1) if side == "w" else (0, k + 1, k))
        m.add(Part(v, t, colors=c), M_SKIRT)


def landing_nose(m):
    """The second-floor landing edge at the head of the flight.

    Room 17's slab stops at z 6.81 and the app's top step starts at 6.95, so
    there is a 0.14 ft slot straight through to the sky.  This fills it and
    gives the head of the flight the dark plank nosing board the photograph
    shows running across in front of the top riser.
    """
    def cf(x, z):
        t = 128.0 + 13.0 * GRAIN(x * 0.4, z * 3.0) + 5.0 * FIG(x, z * 2.0)
        t -= 16.0 * max(0.0, 1.0 - (z - 6.79) / 0.05)
        return PLK(t)

    slab(m, M_PLANK, WELL_X0, WELL_X1, 6.79, 6.99, 0.012, cf, nx=16, nz=3)
    bx(m, M_GROOVE, WELL_X0, WELL_X1, -0.30, 0.012, 6.79, 6.99)
    # the top step's own top face is the landing: plank, matching the 2F floor
    def cf2(x, z):
        t = 150.0 + 13.0 * GRAIN(x * 0.4, z * 3.0) + 6.0 * FIG(x, z * 2.1)
        t -= 20.0 * max(0.0, 1.0 - (x - TX0) / 0.14)
        t -= 20.0 * max(0.0, 1.0 - (TX1 - x) / 0.14)
        return PLK(t)

    slab(m, M_PLANK, TX0, TX1, 6.97, ZL(NST - 1) + RIS + NOSE - 0.001, 0.010,
         cf2, nx=18, nz=4)


def piece_flight():
    m = Model()
    landing_nose(m)
    flight_treads(m)
    flight_skirts(m)
    return m


# =============================================================== 2  the runner
def runner_path():
    """One (z, y) polyline from the head of the flight to the bottom riser:
    tread run -> rolled nosing -> down the riser -> next tread, 17 times."""
    pts = [(6.99, ytop(NST - 1) + 0.012)]
    for i in range(NST - 1, -1, -1):
        y = ytop(i) + 0.012
        zr = ZL(i) + RIS
        zf = zr + NOSE
        pts.append((zf - RNR, y))
        pts += _arc(zf - RNR, y - RNR, RNR, math.pi / 2, -0.20, 4)
        ylo = (ytop(i - 1) + 0.012) if i else FY + 0.030
        pts.append((zf - RNR + RNR * math.cos(-0.20) + 0.004, ylo + 0.10))
        pts.append((zr + 0.012, ylo))
    return pts


PILE = Noise(2287, 0.085)
PILE2 = Noise(6613, 0.26)


def piece_runner():
    """A real strip of cloth, not a lighter quad painted on the tread tops.

    2.62 ft wide -- 5.2 in of bare tread each side -- 0.048 ft thick, wrapping
    every nosing on a 0.9 in radius and running down every riser without a
    break, its cut edges walled, and a woven binding down both edges.
    """
    m = Model()
    path = runner_path()
    xs = [RUN0 + (RUN1 - RUN0) * k / 26.0 for k in range(27)]

    def cf(x, y, z):
        s = math.hypot(z, y)
        t = 176.0
        # the pile itself: high-frequency, isotropic, continuous top to bottom
        t += 15.0 * PILE(x, s) + 7.0 * PILE2(x * 1.7, s * 1.7)
        # falloff down the well, then the bounce at the bottom
        f = (y - FY) / 10.0
        t -= 30.0 * (1.0 - f) ** 1.15
        t += 16.0 * math.exp(-(((y - FY) / 2.2) ** 2))
        # a riser is turned away from every light in the scene
        # (detected by the local slope of the path)
        t -= 4.0 * BLOT(x * 2, s * 2)
        # the woven binding down each edge is a shade darker and tighter
        e = min(x - RUN0, RUN1 - x)
        if e < 0.09:
            t -= 16.0 * (1.0 - e / 0.09)
        return CAR(t)

    # riser panels need to read darker than tread runs; do it by sampling the
    # path slope per row instead of guessing from y alone
    rows = []
    for k in range(len(path)):
        a = path[max(0, k - 1)]
        b = path[min(len(path) - 1, k + 1)]
        dz, dy = b[0] - a[0], b[1] - a[1]
        rows.append(abs(dy) / (abs(dy) + abs(dz) + 1e-6))    # 0 flat, 1 vertical

    nz = len(path)
    v, c, t = [], [], []
    for x in xs:
        for k, (z, y) in enumerate(path):
            v.append((x, y + 0.0, z))
            col = cf(x, y, z)
            drop = 1.0 - 0.20 * rows[k]           # risers 20% down
            c.append((col[0] * drop, col[1] * drop, col[2] * drop))
    for i in range(len(xs) - 1):
        for j in range(nz - 1):
            a, b = i * nz + j, i * nz + j + 1
            cc, d = (i + 1) * nz + j, (i + 1) * nz + j + 1
            t += [(a, b, d), (a, d, cc)]
    m.add(Part(v, t, smooth=True, colors=c), M_CARPET)

    # the band's THICKNESS -- two walls down its cut edges.  Without these it
    # is a decal again no matter how well it wraps.
    for (x, sgn) in ((RUN0, -1), (RUN1, +1)):
        v2, c2, t2 = [], [], []
        for (z, y) in path:
            v2.append((x, y, z))
            v2.append((x, y - RT, z))
        for k in range(len(path) - 1):
            a, b = 2 * k, 2 * k + 1
            cc, d = 2 * k + 2, 2 * k + 3
            t2 += [(a, b, d), (a, d, cc)] if sgn > 0 else [(a, d, b), (a, cc, d)]
        for (px, py, pz) in v2:
            c2.append(CAR(150.0 + 9.0 * PILE(pz * 3, py * 3)))
        m.add(Part(v2, t2, colors=c2), M_CARPET)

    # the contact line where the cloth meets the tread, following the same
    # wrap so it runs down every riser as well as across every tread
    for (a0, a1) in ((RUN0 - 0.085, RUN0 - 0.002), (RUN1 + 0.002, RUN1 + 0.085)):
        v3, c3, t3 = [], [], []
        for (z, y) in path:
            for x in (a0, a1):
                v3.append((x, y - RT - 0.004, z))
                inner = abs(x - RUN0) < 0.05 or abs(x - RUN1) < 0.05
                c3.append(CAR(104.0 if inner else 138.0))
        for k in range(len(path) - 1):
            a, b = 2 * k, 2 * k + 1
            cc, d = 2 * k + 2, 2 * k + 3
            t3 += [(a, d, b), (a, cc, d)]
        m.add(Part(v3, t3, smooth=True, colors=c3), M_CARPET)
    return m


# ================================================================= 3  the rail
def rail_y(z):
    """Rail centre height over the nosing line at z."""
    return FY + (SZB + RIS + NOSE - z) * (RS / TR) + 2.92


def _bracket(m, z):
    """A shaped cast bracket: base plate on the wall, a tapered arm, a saddle
    under the rail.  The photograph's brackets have all three."""
    y = rail_y(z) - 0.13
    x = WSTR0 - 0.005
    # base plate
    m.add(box(0.035, 0.42, 0.30), M_BLACK2, at=(x + 0.017, y - 0.42, z))
    m.add(box(0.05, 0.30, 0.20), M_BLACK, at=(x + 0.05, y - 0.36, z))
    # tapered arm
    for k in range(5):
        f = k / 4.0
        m.add(box(0.075 + 0.10 * f, 0.085, 0.13 - 0.045 * f), M_BLACK,
              at=(x + 0.055 + 0.115 * f, y - 0.30 + 0.30 * f, z))
    # saddle
    m.add(box(0.20, 0.055, 0.24), M_BLACK, at=(x + 0.155, y, z))


def piece_rail():
    """Slim rectangular black rail 2 in off the wall on two shaped brackets for
    the upper flight, black newel over white balusters below.  Dead parallel to
    the stair pitch -- round 1's was pitched shallower than the flight it
    followed, which is what made it read as furniture."""
    m = Model()
    slope = RS / TR
    zt, zb = ZH(NST - 1) - 0.10, SZB + 0.55
    # ---- the rail itself: 2.0 in wide x 2.6 in deep, tiny chamfers
    rw, rh = 0.165, 0.215
    prof = [(-rw / 2, -rh / 2 + 0.03), (-rw / 2 + 0.03, -rh / 2),
            (rw / 2 - 0.03, -rh / 2), (rw / 2, -rh / 2 + 0.03),
            (rw / 2, rh / 2 - 0.035), (rw / 2 - 0.035, rh / 2),
            (-rw / 2 + 0.035, rh / 2), (-rw / 2, rh / 2 - 0.035)]
    cx = WSTR0 + 0.155           # ~2 in clear of the wall face
    v, c, t = [], [], []
    n = len(prof)
    for z in (zt, zb):
        y0 = rail_y(z)
        for (dx, dy) in prof:
            v.append((cx + dx, y0 + dy, z))
            top = dy > 0.03
            c.append(BLK(88.0 if top else (46.0 if dx > 0 else 34.0)))
    for k in range(n):
        a, b = k, (k + 1) % n
        t += [(a, b, n + b), (a, n + b, n + a)]
    m.add(Part(v, t, smooth=False, colors=c), M_BLACK)
    # capped ends -- round 1's terminated in air
    for (z, o) in ((zt, +1), (zb, -1)):
        y0 = rail_y(z)
        cap = [(cx + dx, y0 + dy, z + o * 0.10) for (dx, dy) in prof]
        base = [(cx + dx, y0 + dy, z) for (dx, dy) in prof]
        vv = base + cap
        tt = []
        for k in range(n):
            a, b = k, (k + 1) % n
            tt += [(a, b, n + b), (a, n + b, n + a)]
        tt += [(n, n + k, n + k + 1) for k in range(1, n - 1)]
        m.add(Part(vv, tt, colors=[BLK(70.0)] * (2 * n)), M_BLACK)

    # ---- brackets, on the walled upper half only
    for z in (ZH(NST - 3), ZH(SPLIT + 2)):
        _bracket(m, z)

    # ---- the balustrade over the open lower half
    ytop_str = lambda z: FY + (SZB + RIS - z) * slope + 0.60 + 0.10   # noqa: E731
    for i in range(0, SPLIT):
        for f in (0.28, 0.72):
            z = ZL(i) - TR * f
            yb = FY + (SZB + RIS - z) * slope + 0.66
            yt = rail_y(z) - 0.115
            h = yt - yb
            if h < 0.4:
                continue
            # square top block / turned vase / square base -- the photograph's
            # balusters are pin-top colonial, not plain sticks
            m.add(box(0.115, h * 0.34, 0.115), M_BAL, at=(BALX, yb + h * 0.66, z))
            m.add(box(0.135, h * 0.16, 0.135), M_BAL, at=(BALX, yb, z))
            m.add(cylinder(0.072, h * 0.52, 8, r_top=0.050), M_BAL,
                  at=(BALX, yb + h * 0.15, z))
            m.add(cylinder(0.090, 0.11, 8, r_top=0.062), M_BAL,
                  at=(BALX, yb + h * 0.15, z))
    # the newel: square black post with a turned cap, standing on the floor
    nz_ = SZB + 0.42
    m.add(box(0.38, 3.30, 0.38), M_BLACK, at=(BALX, FY, nz_))
    m.add(box(0.44, 0.30, 0.44), M_BLACK, at=(BALX, FY, nz_))
    m.add(box(0.42, 0.34, 0.42), M_BLACK, at=(BALX, FY + 3.00, nz_))
    m.add(cylinder(0.135, 0.16, 10, r_top=0.115), M_BLACK,
          at=(BALX, FY + 3.34, nz_))
    m.add(cylinder(0.115, 0.10, 10, r_top=0.055), M_BLACK,
          at=(BALX, FY + 3.50, nz_))
    # the white box the newel sits in at the foot of the string
    bx(m, M_BAL, WSTR0 - 0.04, WSTR1 + 0.04, FY, FY + 0.72, nz_ - 0.30, SZB + 0.80)
    return m


# ==================================================== 4  the shaft and the 1F
def piece_lining():
    """Room 17's stand-in for everything below its own slab.

    house.js hides floor 2 when the app is showing level 2, so without this the
    well is a hole to the sky.  It carries the shaft walls (with the top-to-
    bottom falloff every photograph of this stairwell has and round 1 had none
    of), the first-floor plank hall, the front door and its two sidelights, and
    the hard daylight wash they throw across the planks -- which is most of what
    makes `staircase_looking_down.jpg` read as a lit room rather than a backdrop.
    """
    m = Model()
    DOORZ = H_Z1

    # ---------------------------------------------------------- the daylight
    def day(x, z):
        """0..1 wash from the front door + sidelights."""
        d = math.hypot((z - DOORZ) * 0.72, (x - 7.9) * 0.55)
        g = math.exp(-(d / 5.4) ** 1.6)
        # the hard-edged patch the doorway itself throws
        sl = math.exp(-(((z - DOORZ) / 5.0) ** 2))
        if DOOR_X0 - 0.6 < x < DOOR_X1 + 0.6:
            g += 0.55 * sl
        for (a, b) in (SL_W, SL_E):
            if a - 0.5 < x < b + 0.5:
                g += 0.40 * sl
        return min(1.35, g)

    # ------------------------------------------------------- the 1F plank hall
    grv_y = FY - 0.008
    slab(m, M_GROOVE, H_X0, H_X1, H_Z0, H_Z1, grv_y, lambda x, z: GRV(70), 2, 2)
    rn = Rnd(5501)
    pw = 0.62
    z = H_Z0
    row = 0
    while z < H_Z1 - 0.02:
        z1 = min(H_Z1, z + pw)
        # staggered butt joints
        cuts = [H_X0]
        cx = H_X0 + rn.f(1.4, 4.2)
        while cx < H_X1 - 1.0:
            cuts.append(cx)
            cx += rn.f(2.6, 5.4)
        cuts.append(H_X1)
        tint = rn.f(-9.0, 9.0)
        for k in range(len(cuts) - 1):
            a, b = cuts[k] + 0.018, cuts[k + 1] - 0.018
            if b - a < 0.2:
                continue

            def cf(x, zz, tint=tint, row=row):
                t = 128.0 + tint
                t += 12.0 * GRAIN(zz * 0.5, x * 0.30) + 5.5 * FIG(zz * 1.4, x * 0.9)
                t += 62.0 * day(x, zz)
                # occlusion into the wall lines
                t -= 26.0 * max(0.0, 1.0 - (x - H_X0) / 0.55) ** 1.2
                t -= 26.0 * max(0.0, 1.0 - (H_X1 - x) / 0.55) ** 1.2
                t -= 30.0 * max(0.0, 1.0 - (H_Z1 - zz) / 0.55) ** 1.2
                return PLK(t)

            nx = max(2, int((b - a) / 0.55))
            slab(m, M_PLANK, a, b, z + 0.016, z1 - 0.016, FY, cf, nx=nx, nz=2)
        z = z1
        row += 1

    # ------------------------------------------------------- the shaft walls
    def wallc(y, u, warm=0.0, lit=1.0):
        """Vertical falloff, mild blotch, and the door wash near the floor."""
        f = (y - FY) / 18.0                     # 0 at the 1F floor, 1 at 2F ceiling
        t = 152.0 + 46.0 * f ** 0.85
        t += 4.2 * BLOT(u * 0.8, y * 0.55)
        t -= 20.0 * max(0.0, 1.0 - (y - FY) / 0.55) ** 1.3      # base occlusion
        t += 34.0 * lit * math.exp(-(((y - FY) / 3.4) ** 2))     # bounce off the floor
        return WAL(t)

    # east wall of the well and of the 1F hall (one plane, y -10 .. +8)
    wall_x(m, M_WALL, H_X1, H_Z0, H_Z1, FY, 8.0,
           lambda y, z: wallc(y, z, lit=math.exp(-(((z - H_Z1) / 7.0) ** 2))),
           nz=24, ny=26, out=-1)
    # west wall of the 1F hall, well behind the balustrade
    wall_x(m, M_WALL, H_X0, H_Z0, H_Z1, FY, -0.06,
           lambda y, z: wallc(y, z, lit=math.exp(-(((z - H_Z1) / 7.0) ** 2))),
           nz=16, ny=10, out=+1)
    # south (front-door) wall
    wall_z(m, M_WALL, H_Z1, H_X0, H_X1, FY, -0.06,
           lambda y, x: wallc(y, x, lit=1.25), nx=14, ny=10, out=-1)
    # north end of the 1F hall, so the run does not open to nothing
    wall_z(m, M_WALL, H_Z0, H_X0, H_X1, FY, -0.06,
           lambda y, x: wallc(y, x, lit=0.15), nx=8, ny=8, out=+1)
    # the stairwell's west wall -- the bright wedge that shapes the whole upper
    # half of `staircase_looking_down.jpg`.  It runs from the 2F slab down to
    # the string, and stops where the balustrade takes over.
    zsplit = ZL(SPLIT)
    v, c, t = [], [], []
    slope = RS / TR
    ny = 16
    zs = [WELL_Z0 + (zsplit - WELL_Z0) * k / 18.0 for k in range(19)]
    for z in zs:
        ylo = FY + (SZB + RIS - z) * slope + 0.60
        for j in range(ny + 1):
            y = ylo + (0.0 - ylo) * j / ny
            v.append((WSTR0, y, z))
            c.append(wallc(y, z, lit=0.0))
    n = ny + 1
    for i in range(len(zs) - 1):
        for j in range(ny):
            a, b = i * n + j, i * n + j + 1
            cc, d = (i + 1) * n + j, (i + 1) * n + j + 1
            t += [(a, d, b), (a, cc, d)]
    m.add(Part(v, t, smooth=True, colors=c), M_WALL)
    # ... and the raking white skirt where that wall lands on the string
    # (the photograph's white board raking down the shaft wall)
    for (za, zb_) in ((WELL_Z0, zsplit),):
        pass
    # the ceiling over the 1F hall, everywhere except the well
    for (a0, a1, b0, b1) in ((H_X0, WELL_X0, H_Z0, H_Z1),
                             (WELL_X0, H_X1, H_Z0, WELL_Z0),
                             (WELL_X0, H_X1, WELL_Z1, H_Z1)):
        if a1 - a0 > 0.02 and b1 - b0 > 0.02:
            slab(m, M_WALL, a0, a1, b0, b1, -0.06,
                 lambda x, z: WAL(150 + 30 * day(x, z)), nx=4, nz=6, down=True)
    # the reveal round the well: every room ringing the hole hangs a 0.5 ft
    # accent plinth under its slab, and from inside the well those read as
    # saturated stripes.  Paint them out.
    ry0, ry1 = -0.62, 0.015
    bx(m, M_WALL, WELL_X0 - 0.42, WELL_X1 + 0.05, ry0, ry1, WELL_Z0 - 0.40, WELL_Z0 + 0.06)
    bx(m, M_WALL, WELL_X0 - 0.42, WELL_X1 + 0.05, ry0, ry1, WELL_Z1 - 0.06, WELL_Z1 + 0.40)
    bx(m, M_WALL, WELL_X0 - 0.42, WELL_X0 + 0.02, ry0, 0.10, WELL_Z0 - 0.40, WELL_Z1 + 0.40)
    bx(m, M_WALL, WELL_X1 - 0.02, WELL_X1 + 0.42, ry0, ry1, WELL_Z0 - 0.40, WELL_Z1 + 0.40)

    # ------------------------------------------------------ the front door
    dz = H_Z1 - 0.10
    # casing
    bx(m, M_DOOR, DOOR_X0 - 0.30, DOOR_X1 + 0.30, FY, FY + 7.25, dz - 0.06, dz)
    # leaf
    bx(m, M_DOOR, DOOR_X0, DOOR_X1, FY, FY + 6.92, dz - 0.22, dz - 0.06)
    for (a, b, y0, y1) in ((0.16, 1.31, 0.62, 3.02), (1.59, 2.74, 0.62, 3.02),
                           (0.16, 1.31, 3.36, 5.10), (1.59, 2.74, 3.36, 5.10),
                           (0.16, 1.31, 5.44, 6.42), (1.59, 2.74, 5.44, 6.42)):
        bx(m, M_DOOR, DOOR_X0 + a, DOOR_X0 + b, FY + y0, FY + y1,
           dz - 0.255, dz - 0.22)
    m.add(cylinder(0.055, 0.28, 8), M_BLACK2,
          at=(DOOR_X1 - 0.22, FY + 3.05, dz - 0.36), rot_x=R(90))
    m.add(box(0.10, 0.16, 0.09), M_BLACK2, at=(DOOR_X1 - 0.24, FY + 3.52, dz - 0.31))
    # sidelights -- the light source at the bottom of the well
    for (a, b) in (SL_W, SL_E):
        bx(m, M_DOOR, a - 0.22, b + 0.22, FY, FY + 7.25, dz - 0.05, dz + 0.02)
        m.add(quad((a, FY + 0.62, dz - 0.06), (b, FY + 0.62, dz - 0.06),
                   (b, FY + 6.55, dz - 0.06), (a, FY + 6.55, dz - 0.06)),
              M_GLASS)
        m.add(quad((a + 0.02, FY + 0.70, dz - 0.09), (b - 0.02, FY + 0.70, dz - 0.09),
                   (b - 0.02, FY + 3.20, dz - 0.09), (a + 0.02, FY + 3.20, dz - 0.09)),
              M_GLASS2)
        for yy in (2.2, 4.2):
            bx(m, M_DOOR, a, b, FY + yy, FY + yy + 0.07, dz - 0.075, dz - 0.055)
    # 1F baseboard, so the bottom of the well is not a bare box
    for (a0, a1, b0, b1) in ((H_X0, H_X0 + 0.055, H_Z0, H_Z1),
                             (H_X1 - 0.055, H_X1, H_Z0, H_Z1)):
        bx(m, M_SKIRT, a0, a1, FY, FY + 0.52, b0, b1)
    bx(m, M_SKIRT, H_X0, DOOR_X0 - 0.30, FY, FY + 0.52, H_Z1 - 0.055, H_Z1)
    bx(m, M_SKIRT, DOOR_X1 + 0.30, H_X1, FY, FY + 0.52, H_Z1 - 0.055, H_Z1)

    clutter(m)
    return m


# ------------------------------------------------------------- the 1F landing
M_CONS = Material("s2cons", "#f2f0ec", roughness=0.55)
M_CONS2 = Material("s2cons2", "#dcd8d2", roughness=0.62)
M_LEAF = Material("s2leaf", "#6d8a5c", roughness=0.86)
M_LEAF2 = Material("s2leaf2", "#88a06f", roughness=0.86)
M_DRY = Material("s2dry", "#b9a493", roughness=0.92)
M_TERRA = Material("s2ter", "#b08268", roughness=0.85)
M_PINK = Material("s2pnk", "#c86e92", roughness=0.55)
M_SHOE = Material("s2shoe", "#eeece7", roughness=0.70)


def _fan(m, cx, cy, cz, spread, h, mat, n=11, seed=5, w=0.075):
    rn = Rnd(seed)
    for k in range(n):
        a = 2 * math.pi * k / n + rn.f(-0.2, 0.2)
        tilt = rn.f(0.10, 0.42)
        hh = h * rn.f(0.62, 1.0)
        m.add(box(w, hh, 0.022), mat,
              at=(cx + math.cos(a) * spread * tilt * 0.5, cy,
                  cz + math.sin(a) * spread * tilt * 0.5),
              rot_z=math.cos(a) * tilt, rot_x=-math.sin(a) * tilt,
              rot_y=a)


def clutter(m):
    """The bottom of the flight is a ROOM in the photograph: a white console
    loaded with plants and bottles, a black round bin, shoes on the floor."""
    fy = FY
    # ---- console against the east wall, between the stair and the door
    cx0, cx1 = 10.28, 11.52
    cz0, cz1 = 20.35, 23.75
    bx(m, M_CONS, cx0, cx1, fy + 2.44, fy + 2.60, cz0, cz1)          # top
    bx(m, M_CONS2, cx0 + 0.05, cx1, fy + 0.30, fy + 2.44, cz0 + 0.05, cz1 - 0.05)
    for k in range(3):
        za = cz0 + 0.16 + k * ((cz1 - cz0 - 0.32) / 3.0)
        zb = za + (cz1 - cz0 - 0.32) / 3.0 - 0.10
        bx(m, M_CONS, cx0 - 0.015, cx0 + 0.02, fy + 0.42, fy + 2.36, za, zb)
        m.add(cylinder(0.035, 0.10, 8), M_BLACK2,
              at=(cx0 - 0.05, fy + 1.40, (za + zb) / 2.0), rot_x=R(90))
    # contact shade under it
    slab(m, M_GROOVE, cx0 - 0.35, cx1, cz0 - 0.30, cz1 + 0.30, fy + 0.055,
         lambda x, z: GRV(int(52 + 30 * max(abs(x - (cx0 + cx1) / 2) / 0.9,
                                            abs(z - (cz0 + cz1) / 2) / 2.0))), 6, 8)
    # ---- what is on it
    for (px, pz, r, h, mat) in ((10.90, 20.85, 0.20, 0.44, M_TERRA),
                                (10.85, 21.70, 0.17, 0.36, M_CONS),
                                (10.95, 22.55, 0.22, 0.30, M_CONS2)):
        m.add(cylinder(r, h, 12, r_top=r * 0.84), mat, at=(px, fy + 2.60, pz))
    _fan(m, 10.90, fy + 3.02, 20.85, 0.9, 1.35, M_LEAF, n=11, seed=17)
    _fan(m, 10.85, fy + 2.94, 21.70, 0.7, 0.95, M_LEAF2, n=9, seed=41)
    _fan(m, 10.95, fy + 2.88, 22.55, 1.0, 0.62, M_DRY, n=13, seed=8, w=0.055)
    # bottles
    for (px, pz, h, mat) in ((11.28, 23.10, 0.62, M_PINK),
                             (11.30, 23.38, 0.48, M_CONS),
                             (11.12, 23.24, 0.40, M_CONS2)):
        m.add(cylinder(0.075, h, 10, r_top=0.045), mat, at=(px, fy + 2.60, pz))
    # ---- black round waste bin
    m.add(cylinder(0.52, 1.32, 16, r_top=0.62), M_BLACK2, at=(8.85, fy, 22.60))
    m.add(cylinder(0.60, 0.09, 16), M_BLACK, at=(8.85, fy + 1.30, 22.60))
    slab(m, M_GROOVE, 8.15, 9.55, 21.90, 23.30, fy + 0.05,
         lambda x, z: GRV(int(58 + 34 * min(1.0, math.hypot(x - 8.85, z - 22.60) / 0.70))),
         6, 6)
    # ---- shoes
    for (px, pz, rot) in ((9.85, 24.35, 0.15), (10.20, 24.20, -0.25)):
        m.add(rounded_box(0.34, 0.30, 0.92, 0.11, 3), M_SHOE,
              at=(px, fy + 0.02, pz), rot_y=rot)
    slab(m, M_GROOVE, 9.45, 10.60, 23.70, 24.95, fy + 0.05,
         lambda x, z: GRV(int(64 + 30 * min(1.0, math.hypot(x - 10.0, z - 24.3) / 0.65))),
         5, 5)
    # ---- a black wire basket tucked under the console
    m.add(box(1.05, 0.52, 0.62), M_BLACK2, at=(10.85, fy + 0.04, 23.35))


# ---------------------------------------------------------------- the driver
def save_and_place(name, m, fname):
    os.makedirs(GLB, exist_ok=True)
    path = os.path.join(GLB, fname + ".glb")
    m.save(path)
    lo, hi = m.bounds()
    pos = ((lo[0] + hi[0]) / 2.0, lo[1], (lo[2] + hi[2]) / 2.0)
    res = place(name, path, ROOM, pos=pos, rot_y_deg=0.0, scale=1.0)
    kb = os.path.getsize(path) / 1024.0
    print(f"  {name:32s} size=({hi[0]-lo[0]:.2f},{hi[1]-lo[1]:.2f},{hi[2]-lo[2]:.2f})"
          f"  pos=({pos[0]:.2f},{pos[1]:.2f},{pos[2]:.2f})  {kb:7.1f} KB  {res['action']}")
    return kb


PIECES = {
    "flight": ("Hall2F Stair Flight", piece_flight, "hall2f_stair_flight"),
    "runner": ("Hall2F Stair Runner", piece_runner, "hall2f_stair_runner"),
    "rail": ("Hall2F Stair Rail", piece_rail, "hall2f_stair_rail"),
    "lining": ("Hall2F Stairwell Floor Lining", piece_lining,
               "hall2f_stairwell_floor_lining"),
}

if __name__ == "__main__":
    want = sys.argv[1:] or list(PIECES)
    tot = 0.0
    for k in want:
        name, fn, fname = PIECES[k]
        tot += save_and_place(name, fn(), fname)
    print(f"  total {tot:.1f} KB")
