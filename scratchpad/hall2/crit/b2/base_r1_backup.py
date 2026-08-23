"""Room 17 (2F Hallway) -- "Hall2F Baseboards", round V3 rebuild.

    python base.py            # build + place
    python base.py --dry      # build only, print runs / bounds / KB

WHY THIS FILE EXISTS
--------------------
`doors.py piece_baseboards` built the skirting as four straight runs keyed to
the wall NAMES of an 8.10 x 16.70 rectangle.  Room 17 is now a 10-vertex L
(11.92 x 16.89), so that piece:

  * missed the whole WEST ALCOVE (local x 0..3.86, z 10.77..16.15) -- three
    doors' worth of dead end with bare wall meeting bare floor, which is what
    `p_doors2` was showing;
  * ran a phantom board down local x = 11.9 for the full 16.7 ft, where the east
    wall only exists over z 0..6.81 -- a white line hanging in the stairwell;
  * ran another along z = 16.75, where the south edge only exists x 3.86..7.61.

So the run is re-derived from the POLYGON.  Nothing here touches the footprint,
an opening, or any other builder's piece.

HOW THE RUN IS DERIVED
----------------------
`POLY` is room 17's `footprint.points` verbatim.  Winding is CCW, so for edge
i (Vi -> Vi+1) with unit direction u the INWARD normal is n = (-u.z, u.x) --
checked on all ten edges (edge 8 runs +x with n = +z and the room lies at
z > 0; edge 5 runs -z with n = +x and the room lies at x > 0; and so on).

Edges 0 and 1 carry full-span floor-to-ceiling passages (openings 124 and 143),
which makes `house.js buildRoom` skip the wall outright -- the stairwell cut and
the knee-wall line.  They get NO skirting; the knee wall carries its own and is
another builder's piece.  Every other edge gets skirting, broken around its door
and stopped on the casing.

Segments that meet end-to-end across a corner are chained into one POLYLINE and
swept, so every corner is a true mitre rather than two boxes butted into a
notch.  Room 17 has two 270-degree OUTSIDE corners -- V4 (3.86, 16.15) and V7
(3.86, 10.77), the piers either side of the alcove mouth -- and the sweep wraps
the profile round both, which is exactly what `two_closed_white_doors_2.jpg`
shows at the near pier.

THE THING THAT COST THIS ROUND ITS FIRST THREE CYCLES: THE WALL YOU SEE IN
ROOM 17 IS USUALLY NOT ROOM 17'S WALL
--------------------------------------------------------------------------
A skirting authored 0.052 ft (5/8 in) proud of the footprint line rendered as
NOTHING -- not dark, not z-fighting, simply absent from every pose.  Raycasting
the live scene found why: `buildRoom` puts each wall's mass OUTSIDE its own
footprint, and several of room 17's neighbours are traced 0.00-0.29 ft inside
room 17's line, so their 0.35 ft wall mass projects into this room and the
surface you actually see is theirs, up to 0.39 ft in from the polygon.

Measured in the running app (`_seg_probe.py`, rays cast along each edge's
inward normal at y = 0.25, keeping the first hit on a material with NO name --
house.js names none of its own materials, every builder's GLB names all of
them).  `BACK` below is that measurement, and each figure has a neighbour that
explains it exactly:

  | edge | back | the surface you actually see                                |
  |------|------|------------------------------------------------------------|
  | 2    | 0.39 | room 26 (bath), north wall mass world z 23.05..23.40        |
  | 3    | 0.35 | room 15 (Rios), east wall mass world x 10.50..10.85         |
  | 4    | 0.35 | room 15, north wall mass world z 22.35..22.70               |
  | 5    | 0.36 | room 25, east wall mass world x 6.70..7.05                  |
  | 6    | 0.35 | room 13 (Guest), south wall mass world z 17.30..17.65       |
  | 7    | 0.29 | room 13, east wall mass world x 10.50..10.85                |
  | 8    | 0.10 | room 14 (Master Bed), south wall mass world z 6.30..6.65    |
  | 9    | 0.37 | room 16 (Master Bath), west wall mass world x 18.25..18.60  |

The doors builder independently landed on the same numbers: their casings meter
0.078 ft proud of each of these figures on all four edges that carry a door.
So this is the room's real inner face, not a fudge.  The board's back plane is
set to `BACK[edge]` and each corner point is the INTERSECTION of the two pushed
lines, so a corner where the two neighbours' walls step (V3, where room 15's
wall is 0.35 further in than room 26's) mitres on the surface you can see.

None of this touches room 13/14/15/16/25/26 -- it is measurement, not repair.
The overlaps are a house-model condition and belong in the round report.

THE PROFILE, off `two_closed_white_doors_1/2.jpg`
-------------------------------------------------
Both close shots read the section at 5x: a TALL flat-faced board, a hairline
groove near the top, a small proud cap above it, an eased (rounded) top edge,
and a dark line where it meets the plank.  Height 0.45 ft = 5.4 in (the brief's
"roughly 5-5.5 in"); body 0.62 in proud, cap 0.72 in -- both inside the 0.078 ft
the door casings stand proud, so the skirting dies INTO a casing the way it does
in the photos instead of crossing in front of it.

VALUES -- the round-2 critic's theme 5, "every white is the same white"
----------------------------------------------------------------------
Measured off `hallway_looking_towards_stairs.jpg` with a five-pixel column scan
down the NEAR left wall at x = 150, which is the one place in the six photos
where the section is read face-on rather than at a grazing angle:

    skirting cap / eased top  L 239   the brightest white in the photograph
    skirting body             L 219
    door leaf (same photo)    L 201
    casing                    L 205
    wall right above it       L 181
    dark line at the foot     L 180
    plank just past it        L 123-130

So the skirting is 9% brighter than the door leaf and its cap 19% brighter --
that is the brief's "the SKIRTING READS BRIGHTER than the door above it",
confirmed rather than taken on trust.  Staged here across five materials, and
fitted by RENDERING, not by matching hex to hex: a two-point albedo probe at
fixed roughness 0.72 (#a29c92 -> L 197.6, #dfd9cf -> L 227.7) gives an exponent
of 0.43, i.e. this surface sits deep in the ACES shoulder where 34 points of
albedo buy 8 points of render.

Shipped, metered in `shots/base_p_stairs.png` on the north wall (x = 430):

    cap / eased top  246      body 234      groove 183
    door leaf        232      wall  134     floor 119

    cap / leaf 1.06   body / leaf 1.01   body / floor 1.97
    photo:     1.19                1.09                1.74

The ordering the critic asked for holds -- cap, then body, then the leaf, then
the casing, then the wall -- but the MARGIN is squeezed: `Hall2F Doors` already
renders its leaf at 232/255, so the photo's 1.09x body would clip.  Against the
floor this skirting is if anything slightly hot (1.97 vs 1.74), never flat.  The
leaf figure drifts while the doors builder iterates; re-meter before re-tuning.

The eased top is swept in three SMOOTHED steps so its tone ramps continuously
instead of reading as one flat chamfer fill, and the groove under the cap is a
real recessed face (0.018 ft tall, 0.008 ft deep) rather than a painted line.

A non-emissive vertex-colour ramp (COLOR_0) darkens the run 7% into the dead end
and 4.5% at the very foot, with +-2% grain.  It buys less than it should for the
same shoulder reason (the body meters sd 0.2), which is honest to the photo --
the photograph's own clean skirting field is sd 1.6.  No emissive: two rounds of
glowing trim fins were rejected.

THE CONTACT LINE IS OPAQUE, AND HAS TO BE
-----------------------------------------
ROOM-BRIEF asks for an alpha decal.  It cannot be one here: `cutaway.js
WALL_ARCH_RE` matches /baseboards?/, so this piece is classed as wall
architecture, its triangles are bucketed onto the wall nearest each one, and
both `update()` and `restoreAll()` call `objects.js fadeSubtree`, which writes
`m.opacity` on every material in the subtree.  `v3.py` shoots `--no-cutaway`,
which runs `restoreAll()` -> opacity 1.0 on all of it, so an authored 0.26 is
erased and the decal renders as a black chip (round 3 measured L 38 against a
floor at L 136).  So the contact band is three OPAQUE steps graded off the
floor's own RENDERED tone, and it is narrow: the photo shows a dark LINE at the
joint, not a wide AO pool -- past the joint its plank meters 123-130 against
123-128 further out, so a 25 ft-wide AO pool would be an invention.

Shipped, metered on the north wall in `shots/base_p_stairs.png`: 93 / 110 / 115
against a floor at 115-119, i.e. 0.80 / 0.95 / 0.99, over 0.15 ft total.  The
board's own toe band carries the rest of the darkening, which is where the
photograph puts it (L 180 on the board, not on the plank).
"""

import math
import os
import sys

sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\circ")

from ckit import Material, Model, Part, save_and_place, mix, Rnd   # noqa: F401

ROOM = 17

# ------------------------------------------------------------------ footprint
# room 17 footprint.points, verbatim.  DO NOT EDIT -- signed off by the owner.
POLY = [(11.92, 6.81), (7.61, 6.81), (7.61, 16.89), (3.86, 16.89),
        (3.86, 16.15), (0.00, 16.15), (0.00, 10.77), (3.86, 10.77),
        (3.86, 0.00), (11.92, 0.00)]
N = len(POLY)

# edges whose wall `buildRoom` skips outright: the stairwell cut (opening 124)
# and the knee-wall line (opening 143), both full-span floor-to-ceiling.
NO_WALL = {0, 1}

# openings, as (offset, width) in the edge's own u frame -- straight off
# GET /api/house.  Not edited, only read.
DOORS = {
    2: [(0.150, 2.790)],     # 133 -> bathroom, room 26
    4: [(0.747, 2.537)],     # 127 -> Rios Room, room 15
    5: [(1.088, 2.899)],     # 125 -> room 25
    6: [(0.362, 2.754)],     # 136 -> Guest Room, room 13
    8: [(3.968, 2.863)],     # 137 -> Master Bed, room 14
}

# Where the visible wall face really is, per edge -- see the module docstring.
BACK = {2: 0.39, 3: 0.35, 4: 0.35, 5: 0.36, 6: 0.35, 7: 0.29, 8: 0.10, 9: 0.37}

# How far the door CASING stands out past its opening on each side.  The
# skirting stops on the casing's outer edge: it dies into the casing, it does
# not run behind it and it does not leave a strip of bare wall.  0.19 ft is
# `doors.py CASE`, the casing that is actually placed; if the doors builder
# widens it this round the skirting end simply disappears BEHIND the wider
# casing, which is the safe direction to be wrong in.
CASE = 0.190

MIN_RUN = 0.02          # drop slivers narrower than this


# ------------------------------------------------------------------- profile
T = 0.052               # body proud of the wall face   (0.62 in)
CAPD = 0.060            # cap proud                     (0.72 in)
BH = 0.450              # total height                  (5.40 in)

SK_BODY = Material("h17b_body", "#f7f3ec", roughness=0.70)
SK_CAP = Material("h17b_cap",  "#ffffff", roughness=0.36)
SK_TOP = Material("h17b_top",  "#ffffff", roughness=0.30)   # the eased edge
SK_GRV = Material("h17b_grv",  "#bdb6ab", roughness=0.86)   # under the cap
SK_TOE = Material("h17b_toe",  "#8f8a81", roughness=0.82)   # shadowed foot
SK_BK = Material("h17b_bk",   "#dcd6cc", roughness=0.72)    # sliver at the wall

# The contact line.  Opaque (see the docstring), graded off the floor's RENDERED
# tone -- metered at L 112-135 next to the skirting in the photos and L ~118 in
# our own render -- because `Hall2F Floor Planks` is a translucent wear layer
# over the app's own tiled wood slab, so its authored albedo is not what you see.
FLOORTONE = "#6f6d69"
CS = [(0.000, 0.024, 0.46), (0.024, 0.075, 0.36), (0.075, 0.150, 0.28)]
CS_MATS = [Material("h17b_cs%d" % i, mix(FLOORTONE, "#000000", k), roughness=0.30)
           for i, (_, _, k) in enumerate(CS)]
CS_Y = 0.040            # clear of `Hall2F Floor Planks`, whose top is y 0.02


def _profile():
    """(d, y) stations, floor-back -> floor-front -> up -> over -> wall-top.

    Traversed in this order every swept quad winds OUTWARD, so nothing needs
    flipping -- a flipped face here is the round-2 critic's "pure black slab".
    Returns [(d, y)] and one (material, smooth) per gap between stations.
    """
    st = [(0.000, 0.000),        # back, on the floor
          (T,     0.000),        # front bottom corner
          (T,     0.032),        # toe
          (T,     0.342),        # the flat field
          (CAPD,  0.360),        # step out -- its underside is the groove
          (CAPD,  0.410)]        # the proud cap face
    bands = [(SK_TOE, False),    # bottom face (never seen)
             (SK_TOE, False),    # the toe
             (SK_BODY, False),   # the field
             (SK_GRV, False),    # the groove under the cap
             (SK_CAP, False)]    # the cap face
    d0, y0, d1, y1 = CAPD, 0.410, 0.010, BH
    for i in range(1, 4):        # eased top, 3 SMOOTHED steps
        a = (i / 3.0) * (math.pi / 2.0)
        st.append((d1 + (d0 - d1) * math.cos(a), y0 + (y1 - y0) * math.sin(a)))
        bands.append((SK_TOP, True))
    st.append((0.000, BH))       # back to the wall
    bands.append((SK_BK, False))
    return st, bands


PROF, BANDS = _profile()


# ------------------------------------------------------------ polygon walking
def _edge(i):
    ax, az = POLY[i]
    bx, bz = POLY[(i + 1) % N]
    dx, dz = bx - ax, bz - az
    L = math.hypot(dx, dz)
    return (ax, az), (dx / L, dz / L), L


def _normal(i):
    """Inward unit normal of edge i (CCW polygon -> interior on the left)."""
    _, (ux, uz), _ = _edge(i)
    return (-uz, ux)


def _point(i, u):
    (ax, az), (ux, uz), _ = _edge(i)
    return (ax + ux * u, az + uz * u)


def _segments():
    """[(edge, u0, u1)] -- where skirting exists, in edge order."""
    out = []
    for i in range(N):
        if i in NO_WALL:
            continue
        _, _, L = _edge(i)
        gaps = [(o - CASE, o + w + CASE) for (o, w) in DOORS.get(i, [])]
        spans = [(0.0, L)]
        for g0, g1 in gaps:
            nxt = []
            for s0, s1 in spans:
                if g1 <= s0 or g0 >= s1:
                    nxt.append((s0, s1))
                    continue
                if s0 < g0:
                    nxt.append((s0, g0))
                if s1 > g1:
                    nxt.append((g1, s1))
            spans = nxt
        for a, b in spans:
            if b - a > MIN_RUN:
                out.append((i, a, b))
    return out


def _chain():
    """Group segments into runs of segments that meet end-to-end at a corner."""
    segs = _segments()
    runs, cur = [], []
    for (i, a, b) in segs:
        _, _, L = _edge(i)
        joins = False
        if cur:
            pi, pa, pb = cur[-1]
            _, _, pL = _edge(pi)
            joins = pb >= pL - 1e-6 and a <= 1e-6 and (pi + 1) % N == i
        if joins:
            cur.append((i, a, b))
        else:
            if cur:
                runs.append(cur)
            cur = [(i, a, b)]
        if b < L - 1e-6:                 # ends on a casing -> the run ends here
            runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    return runs


def _runs(step=0.9):
    """Mitred, wall-offset polylines: [[(x, z, mx, mz)]].

    (x, z) is on the VISIBLE wall face (the footprint line pushed in by
    `BACK[edge]`), and (mx, mz) is the mitre vector, so the profile station at
    depth d lands at (x, z) + d*(mx, mz).  All ten corners are right angles, so
    the pushed-line intersection is p + n1*b1 + n2*b2 and the depth mitre is
    (n1 + n2) / (1 + n1.n2), which for a 270-degree outside corner wraps the
    profile round it instead of butting two ends together.
    """
    out = []
    for run in _chain():
        # (point on the footprint line, normal/back before, normal/back after)
        pts = []
        for j, (i, a, b) in enumerate(run):
            n, bk = _normal(i), BACK[i]
            if j == 0:
                pts.append((_point(i, a), n, bk, n, bk))
            else:
                pi = run[j - 1][0]
                pts.append((_point(i, a), _normal(pi), BACK[pi], n, bk))
            # interior stations along this segment, for the baked falloff ramp
            (ax, az), (ux, uz), _ = _edge(i)
            L = b - a
            for k in range(1, max(1, int(round(L / step)))):
                u = a + L * k / float(max(1, int(round(L / step))))
                pts.append(((ax + ux * u, az + uz * u), n, bk, n, bk))
            pts.append((_point(i, b), n, bk, n, bk))
        # the shared corner vertex appears twice (end of j, start of j+1)
        merged = []
        for p, n1, b1, n2, b2 in pts:
            if merged and abs(merged[-1][0][0] - p[0]) < 1e-9 \
                    and abs(merged[-1][0][1] - p[1]) < 1e-9:
                q = merged[-1]
                merged[-1] = (p, q[1], q[2], n2, b2)
                continue
            merged.append((p, n1, b1, n2, b2))
        poly = []
        for (px, pz), n1, b1, n2, b2 in merged:
            dot = n1[0] * n2[0] + n1[1] * n2[1]
            if dot > 0.999:                       # straight run
                ox, oz = n1[0] * b1, n1[1] * b1
            else:                                 # right-angle corner
                ox, oz = n1[0] * b1 + n2[0] * b2, n1[1] * b1 + n2[1] * b2
            mx = (n1[0] + n2[0]) / (1.0 + dot)
            mz = (n1[1] + n2[1]) / (1.0 + dot)
            poly.append((px + ox, pz + oz, mx, mz))
        out.append(poly)
    return out


# --------------------------------------------------------------------- sweep
RN = Rnd(20250822)

# The daylight in this hall comes up the open stairwell.  Baking a small falloff
# toward the dead end is the round-2 critic's theme 4 ("no light falloff")
# applied to the trim -- as albedo, never emissive.
LIGHT = (9.20, 12.30)          # local xz, middle of the stairwell cut
FAR = 13.5
DROP = 0.070                   # 7% into the dead end
FOOT = 0.045                   # 4.5% at the very foot
GRAIN = 0.020


def _tone(x, z, y):
    d = math.hypot(x - LIGHT[0], z - LIGHT[1])
    t = min(1.0, max(0.0, (d - 3.0) / (FAR - 3.0)))
    t = t * t * (3.0 - 2.0 * t)
    v = 1.0 - DROP * t
    v *= 1.0 - FOOT * (1.0 - min(1.0, y / BH))
    v *= 1.0 + RN.f(-GRAIN, GRAIN)
    return (v, v, v)


def _sweep(m, poly, stations, bands, tone=True, reverse=False):
    """Sweep a (d, y) profile along a mitred polyline; one Part per band.

    Quad (k,s) (k+1,s) (k+1,s+1) (k,s+1), triangulated on the (k,s)-(k+1,s+1)
    diagonal.  With the profile ordered bottom-up this winds OUTWARD on every
    wall orientation -- verified against edge 8 (u = +x, n = +z), where the
    field quad's normal comes out +z, the bottom face -y and the top sliver +y.
    """
    def P(k, s):
        x, z, mx, mz = poly[k]
        d, y = stations[s]
        return (x + mx * d, y, z + mz * d)

    for s in range(len(stations) - 1):
        mat, smooth = bands[s]
        v, c, tris = [], [], []
        for k in range(len(poly)):
            for ss in (s, s + 1):
                p = P(k, ss)
                v.append(p)
                if tone:
                    c.append(_tone(p[0], p[2], p[1]))
        for k in range(len(poly) - 1):
            a, b = 2 * k, 2 * k + 1          # (k, s), (k, s+1)
            cc, dd = 2 * k + 2, 2 * k + 3    # (k+1, s), (k+1, s+1)
            if reverse:
                tris += [(a, dd, cc), (a, b, dd)]
            else:
                tris += [(a, cc, dd), (a, dd, b)]
        m.add(Part(v, tris, smooth=smooth, colors=c if tone else None), mat)


def _cap(m, poly, stations, k, at_start):
    """Close a run end with the profile's own silhouette.

    The free end at V0 (11.92, 6.81) is the one that is actually seen: the
    skirting dies at the stairwell cut there, exactly as in
    `staircase_looking_down.jpg`, and an open end would read as a hole.
    """
    x, z, mx, mz = poly[k]
    v = [(x + mx * d, y, z + mz * d) for (d, y) in stations]
    tris = [(0, s, s + 1) for s in range(1, len(v) - 1)]
    if not at_start:
        tris = [(a, c, b) for (a, b, c) in tris]
    m.add(Part(v, tris, colors=[_tone(p[0], p[2], p[1]) for p in v]), SK_BODY)


# ---------------------------------------------------------------- the piece
def piece():
    m = Model()
    runs = _runs()
    for poly in runs:
        _sweep(m, poly, PROF, BANDS)
        _cap(m, poly, PROF, 0, True)
        _cap(m, poly, PROF, len(poly) - 1, False)
        # the contact line: three opaque steps on the floor, station order
        # reversed so the band faces UP.  Started at the body face so the cap's
        # 0.008 ft overhang covers the joint at a grazing angle.
        for (a, b, _), mat in zip(CS, CS_MATS):
            _sweep(m, poly, [(T + b, CS_Y), (T + a, CS_Y)],
                   [(mat, False)], tone=False)
    return m, runs


def main():
    m, runs = piece()
    lo, hi = m.bounds()
    print("  runs %d, %d stations" % (len(runs), sum(len(r) for r in runs)))
    for r in runs:
        print("    (%5.2f,%5.2f) -> (%5.2f,%5.2f)  %2d pts"
              % (r[0][0], r[0][1], r[-1][0], r[-1][1], len(r)))
    print("  bounds %s -> %s" % (tuple(round(q, 2) for q in lo),
                                 tuple(round(q, 2) for q in hi)))
    if "--dry" in sys.argv:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "glb", "hall2f_baseboards.glb")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        m.save(path)
        print("  %.1f KB (dry, not placed)" % (os.path.getsize(path) / 1024.0))
        return
    save_and_place("Hall2F Baseboards", m, ROOM)


if __name__ == "__main__":
    main()
