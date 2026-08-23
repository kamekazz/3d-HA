"""Room 17 (2F Hallway) -- ROUND 2 doors.  Owns exactly two pieces:

    Hall2F Doors          five closed 6-panel moulded-skin colonial leaves
                          and their hardware.
    Hall2F Door Casings   jamb linings, the graded reveal seam, the flat
                          casings + head cap + mitre lines, and a baked floor
                          contact shadow at each threshold.

Re-runnable: `roomkit.place` is keyed by name.  Touches no room polygon, no
opening's edge/offset/width, no other room.  Room 17's five openings are
already `passage` (the engine's own flat panel is off) so nothing is PATCHed.

WHAT ROUND 1's NINE CRITICS SAID, AND WHAT IS DONE ABOUT IT HERE
----------------------------------------------------------------
Measured off `two_closed_white_doors_1/2.jpg` (450x600), sRGB luma:

  leaf field         205-218   sd 5.9   |d1|h 1.65  |d1|v 0.90
  casing face        192-202
  wall               174-182
  shadow line at the casing's outer arris   162-167   (2 px, -16 vs wall)

  vertical scan crossing a panel's TOP edge, left door of doors_2 (x=140):
      220 220 | 179 173 178 | 217 242 239 239 239 240 | 219 220 ...
      rail    | DARK 3 px   | BRIGHT 5 px            | field == rail

  the same scan on a panel's SIDE edge (y=180) is a single 1 px dip of -15
  to -30 and NO bright band, and the panel field is the SAME value as the
  stile either side of it.

So a photographed colonial panel carries exactly three signals: a ~0.8 in
dark quirk and a ~1.3 in bright up-facing sweep along its TOP edge, a
hairline down its sides, and nothing worth reading at its bottom.  Round 1
drew a 25-30 level chisel bevel on all four sides of every panel with a
13-level darker field, which is what read as vacuum-formed plastic.

`sweep_panel` below therefore:
  * runs a stepped ovolo (quirk wall -> quirk floor -> cove -> ovolo shoulder
    -> step) round a ROUNDED-RECTANGLE loop, so no corner mitres to a point;
  * shades every vertex from the loop point's own outward normal, so the
    bright band lives only where the surface faces UP and dies away round the
    corners exactly as it does in the photograph;
  * paints the field in the leaf's own white, not a darker one.

Everything else the critics named:
  * HINGES are a 0.55 in black barrel in the leaf/jamb gap, 3.5 in of it
    showing, no plate on the face of anything.  Round 1's flat quads are gone.
  * The REVEAL is a graded seam board (`seam_board`), dark only at the head
    and down the hinge stile, all but gone on the strike side at mid height.
  * The HANDLE is a chunky square rose with a real standoff, a lever that
    returns back toward the leaf, an occlusion smudge baked under it, and it
    is centred on the lock stile.
  * TEXTURE: every leaf face, every panel field and the casings carry a
    vertex-colour tone field -- a top-to-bottom light falloff plus vertical
    roller streaks plus fine noise.  See `tone()`.
  * EVERY WHITE IS A DIFFERENT WHITE: leaf / band / quirk / field / edge /
    jamb / seam / casing / casing-bead / casing-return are ten values.

LEAF VALUE SPLIT
----------------
Set `EM=<n>` to give every leaf an emissive fill of strength n and `RGH=<r>`
to override the leaf roughness; that is how the numbers in `EMIS` were
measured.  Two-point probes, `p_doors2`, the Rios leaf (north facing).

WHERE THE WALL FACE ACTUALLY IS  (unchanged from round 1, re-verified)
---------------------------------------------------------------------
`house.js` extrudes each wall OUTWARD from its own room's footprint line
(WALL_THICKNESS 0.35), so on all five doorways the nearest visible face is
the NEIGHBOUR's outer wall face, standing 0.10-0.39 ft inside room 17.  TR is
computed per door from the DB; the casing is nailed to that plane.
"""

import json
import math
import os
import sys
import urllib.request

sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")

from roomkit.glb import Model, Material, Part, box, cylinder, quad    # noqa: E402
from roomkit.place import place                                       # noqa: E402

BASE = "http://127.0.0.1:5000"
HERE = os.path.dirname(os.path.abspath(__file__))
GLB = os.path.join(HERE, "glb")
ROOM = 17
WALL_T = 0.35


def _req(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE + path, data=data, method=method)
    r.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(r, timeout=30) as resp:
        txt = resp.read()
        return json.loads(txt) if txt.strip() else {}


def house():
    return _req("GET", "/api/house")


def rooms_by_id(h):
    out = {}
    for f in h["floors"]:
        for r in f["rooms"]:
            out[r["id"]] = r
    return out


def poly(r):
    fp = r["footprint"]
    if fp.get("points"):
        return [tuple(p) for p in fp["points"]]
    return [(0, 0), (fp["width"], 0), (fp["width"], fp["depth"]), (0, fp["depth"])]


def edge_frame(r, i):
    p = poly(r)
    fp = r["footprint"]
    ax, az = p[i]
    bx_, bz = p[(i + 1) % len(p)]
    L = math.hypot(bx_ - ax, bz - az)
    u = ((bx_ - ax) / L, (bz - az) / L)
    n = (-u[1], u[0])
    return (fp["x"] + ax, fp["z"] + az), u, n, L


def op_world(r, op):
    A, u, n, L = edge_frame(r, op["edge_index"])
    s = (A[0] + u[0] * op["offset"], A[1] + u[1] * op["offset"])
    e = (s[0] + u[0] * op["width"], s[1] + u[1] * op["width"])
    return s, e, u, n


# ------------------------------------------------------------------ the five
# (opening, neighbour room, neighbour opening, label, hinge end, LOD)
#   hinge end 1 = hinges at the a=A1 stile, lever at A0.
DOORS = [
    (133, 26, 128, "bath",   1, 1),
    (127, 15, 140, "rios",   1, 1),
    (125, 25, 142, "closet", 1, 1),
    (136, 13, 112, "guest",  1, 1),
    (137, 14, 132, "master", 1, 0),
]

# Emissive fill per leaf, fitted from the two-point probe described above.
# A leaf whose face never sees the sun renders ~50 counts below one that does
# at an identical albedo, and the albedo lever is exhausted (#ffffff already).
EMIS = {"bath": 0.085, "rios": 0.085, "closet": 0.0,
        "guest": 0.0, "master": 0.0}
EM_OVER = os.environ.get("EM")
RGH_OVER = os.environ.get("RGH")


# ------------------------------------------------------------------ tone field
def _h(x, y):
    """Deterministic hash noise in -1..1."""
    s = math.sin(x * 127.1 + y * 311.7) * 43758.5453
    return 2.0 * (s - math.floor(s)) - 1.0


def tone(a, y, y0, y1, amp=1.0):
    """The leaf's baked surface tone: light falloff + roller streaks + noise.

    The photographs' leaves darken ~10% from head to threshold (measured: the
    right leaf of doors_2 runs 218 at its head to 194 at the lock rail) and
    carry |d1|h 1.4-1.9 of paint/sensor noise with a clear VERTICAL streak
    structure -- more variation across the leaf than down it.  Both are
    reproduced here, the streaks sampled fine in `a` and coarse in `y`.
    """
    f = (y - y0) / max(1e-6, y1 - y0)
    fall = 0.905 + 0.095 * (f ** 0.75)
    streak = (0.016 * math.sin(a * 34.7 + 1.13)
              + 0.011 * math.sin(a * 81.3 + 4.02)
              + 0.007 * math.sin(a * 173.0 + 2.6))
    grain = 0.009 * _h(a * 11.0, y * 3.0) + 0.006 * _h(a * 47.0, y * 19.0)
    return fall * (1.0 + amp * (streak + grain))


# ------------------------------------------------------------------ materials
def mset(tag, em, extra_rough=0.0):
    """One door's ten whites.

    The ladder, as fractions of the leaf, is taken straight off the photo:
    casing 0.90 of the leaf, wall 0.82, the shadow at the casing arris 0.76.
    Round 1 authored the casing at 0.81 of the leaf and it read as a grey band.
    """
    rgh = float(RGH_OVER) if RGH_OVER else None
    e = float(EM_OVER) if EM_OVER is not None else em

    def C(hexc, rough, r_override=True):
        r = rgh if (rgh is not None and r_override) else rough
        r = min(1.0, r + extra_rough)
        kw = {}
        if e > 0:
            kw = dict(emissive="#fffdf8", emissive_strength=e)
        # NAMED BY VALUE, NOT BY DOOR: two leaves with the same white, the same
        # roughness and the same fill share one primitive, which takes the file
        # from 55 material groups to ~22 and ~20 KB of JSON with it.
        return Material(f"d17_{hexc.lstrip('#')}_{r:.2f}_{e:.3f}", hexc,
                        roughness=r, metallic=0.0, **kw)

    return dict(
        leaf=C("#ffffff", 0.58),      # stiles, rails and the panel FIELD: one white
        band=C("#ffffff", 0.26),      # the up-facing ovolo sweep -- semi-gloss kick
        quirk=C("#fbf9f6", 0.92),     # the quirk wall + floor: dulled, then shaded
        edge=C("#f0ede8", 0.72),      # the leaf's own 1 3/4 in edge
        jamb=C("#f4f1ec", 0.80),      # jamb lining
        seam=C("#cdc8c1", 0.95),      # the reveal seam board, graded per vertex
        blank=C("#5d5a56", 0.95, False),
        case=C("#f6f3ee", 0.60),      # flat casing face
        case_hi=C("#fdfcf9", 0.46),   # head cap + the bright top arris
        case_ret=C("#c6c1ba", 0.88),  # the casing's outer return -> the shadow line
        mitre=C("#b9b4ad", 0.94, False),
    )


BLK = Material("d17blk", "#181819", roughness=0.44, metallic=0.25)
BLK_D = Material("d17blkd", "#0e0e10", roughness=0.60, metallic=0.10)
# Floor contact shadow.  Opaque, graded by vertex colour off the floor piece's
# own albedo, because cutaway.js classes /doors?|casings?/ as wall architecture
# and rewrites authored opacity every frame -- an alpha decal renders black.
SHAD = Material("d17shad", "#5b5755", roughness=0.34)

# ------------------------------------------------------------------ dimensions
JT = 0.055          # jamb board thickness
GAPW = 0.010        # leaf-to-jamb reveal
LEAF_T = 0.145      # leaf thickness (1 3/4 in)
SETBACK = 0.046
CASE_W = 0.292      # 3 1/2 in
CASE_P = 0.050
BEAD_P = 0.068
REVEAL = 0.021

ROWS = [("rail", 0.075), ("panel", 0.264), ("rail", 0.103),
        ("panel", 0.310), ("rail", 0.058), ("panel", 0.138), ("rail", 0.052)]
STILE = 0.125
MULL = 0.120

# Panel sticking profile: (inset from the opening arris, dz below the leaf
# face).  Total 0.160 ft = 1.9 in, against ~2.1 in read off the photo.
PROF = [(0.000,  0.000),
        (0.014, -0.021),      # quirk wall  -- 0.8 in of dark at the panel head
        (0.050, -0.025),      # quirk floor
        (0.092, -0.016),      # cove springs  \
        (0.132, -0.007),      # ovolo shoulder / 1.0 in of bright up-facing sweep
        (0.160, -0.010)]      # the step back down to the field
# per-ring (top, side, bottom) vertex shade; blended by the loop normal's ny.
PSHADE = [(0.985, 0.985, 0.985),
          (0.845, 0.940, 0.960),
          (0.865, 0.945, 0.935),
          (1.000, 0.965, 0.905),
          (1.000, 0.975, 0.915),
          (0.985, 0.975, 0.955)]


# ------------------------------------------------------------------- helpers
def bx(m, mat, a0, a1, y0, y1, t0, t1):
    m.add(box(abs(a1 - a0), abs(y1 - y0), abs(t1 - t0), anchor="center"), mat,
          at=((a0 + a1) / 2, (y0 + y1) / 2, (t0 + t1) / 2))


def open_box(m, mat, a0, a1, y0, y1, t0, t1):
    """A box with its +t face omitted -- the leaf core.

    Its side/top/bottom faces ARE the leaf's visible edges, and leaving the
    front off means the panel sweeps can recess into it without the core's own
    face standing in front of them.
    """
    v = [(a0, y0, t0), (a1, y0, t0), (a1, y1, t0), (a0, y1, t0),
         (a0, y0, t1), (a1, y0, t1), (a1, y1, t1), (a0, y1, t1)]
    f = [(0, 3, 2), (0, 2, 1),          # back
         (0, 1, 5), (0, 5, 4),          # bottom
         (2, 3, 7), (2, 7, 6),          # top
         (0, 4, 7), (0, 7, 3),          # a0 side
         (1, 2, 6), (1, 6, 5)]          # a1 side
    m.add(Part(v, f, smooth=False), mat)


def grid(m, mat, a0, a1, y0, y1, t, nx, ny, shade):
    """Subdivided flat quad in the (a, y) plane, one vertex colour per node."""
    verts, cols, tris = [], [], []
    for j in range(ny + 1):
        y = y0 + (y1 - y0) * j / ny
        for i in range(nx + 1):
            a = a0 + (a1 - a0) * i / nx
            verts.append((a, y, t))
            s = shade(a, y)
            cols.append((s, s, s))
    for j in range(ny):
        for i in range(nx):
            p = j * (nx + 1) + i
            q = p + nx + 1
            tris += [(p, q, q + 1), (p, q + 1, p + 1)]
    m.add(Part(verts, tris, smooth=True, colors=cols), mat)


def rrect(a0, a1, y0, y1, r, cseg):
    """Closed CCW loop of (a, y, nx, ny) for a rounded rectangle.

    `nx, ny` is the in-plane OUTWARD normal at that point; the panel sticking
    is shaded from it, which is what rounds the bright band off at the corners
    instead of mitring it to a point.
    """
    r = min(r, 0.45 * min(a1 - a0, y1 - y0))
    cen = [(a1 - r, y0 + r, -math.pi / 2), (a1 - r, y1 - r, 0.0),
           (a0 + r, y1 - r, math.pi / 2), (a0 + r, y0 + r, math.pi)]
    pts = []
    for (cx, cy, a_start) in cen:
        for k in range(cseg + 1):
            th = a_start + (math.pi / 2) * k / cseg
            nx_, ny_ = math.cos(th), math.sin(th)
            pts.append((cx + r * nx_, cy + r * ny_, nx_, ny_))
    return pts, r


def sweep_panel(m, M, a0, a1, y0, y1, tf, base, cseg=3, ring_mid=True):
    """The stepped-ovolo sticking swept round a rounded-rect panel opening."""
    loop, r = rrect(a0, a1, y0, y1, 0.088, cseg)
    N = len(loop)

    def ring(k):
        ins, dz = PROF[k]
        top, side, bot = PSHADE[k]
        v, c = [], []
        for (a, y, nx_, ny_) in loop:
            if k == 0:
                # Ring 0 is the SHARP rectangle: a rounded loop offset outward
                # never recovers the square corner of the opening, so leaving
                # ring 0 rounded punched a notch of bare core at each of the
                # 120 panel corners.  The L-infinity projection of the same
                # loop point lands exactly on the rectangle, corner included.
                sc = 1.0 / max(abs(nx_), abs(ny_))
                cx = a - nx_ * r
                cy = y - ny_ * r
                v.append((cx + r * nx_ * sc, cy + r * ny_ * sc, tf + dz))
            else:
                v.append((a - nx_ * ins, y - ny_ * ins, tf + dz))
            s = side + (top - side) * max(ny_, 0.0) + (bot - side) * max(-ny_, 0.0)
            s *= base(a, y)
            c.append((s, s, s))
        return v, c

    def strip(mat, ks):
        V, C, T = [], [], []
        for k in ks:
            v, c = ring(k)
            V += v
            C += c
        for j in range(len(ks) - 1):
            for i in range(N):
                p = j * N + i
                q = j * N + (i + 1) % N
                T += [(p, q, q + N), (p, q + N, p + N)]
        m.add(Part(V, T, smooth=True, colors=C), mat)

    strip(M["quirk"], (0, 1, 2))
    strip(M["band"], (2, 3, 4, 5))

    # the field: rim + one mid ring + centre, so it carries tone of its own
    ins, dz = PROF[-1]
    rim = [(a - nx_ * ins, y - ny_ * ins) for (a, y, nx_, ny_) in loop]
    ca, cy = (a0 + a1) / 2, (y0 + y1) / 2
    V, C, T = [], [], []
    rings = [1.0, 0.52] if ring_mid else [1.0]
    for f in rings:
        for (a, y) in rim:
            pa, py = ca + (a - ca) * f, cy + (y - cy) * f
            V.append((pa, py, tf + dz))
            s = base(pa, py) * 0.995
            C.append((s, s, s))
    V.append((ca, cy, tf + dz))
    s = base(ca, cy) * 0.995
    C.append((s, s, s))
    for j in range(len(rings) - 1):
        for i in range(N):
            p = j * N + i
            q = j * N + (i + 1) % N
            T += [(p, q, q + N), (p, q + N, p + N)]
    b = (len(rings) - 1) * N
    ctr = len(V) - 1
    for i in range(N):
        T.append((b + i, b + (i + 1) % N, ctr))
    m.add(Part(V, T, smooth=True, colors=C), M["leaf"])


# --------------------------------------------------------------------- leaf
def hardware(m, M, base, la0, la1, ly0, ly1, tf, hinge_at_a1, lw):
    """Matte black lever on a square rose, and three barrel hinges.

    THE ROSE, measured off `two_closed_white_doors_1.jpg` at 8x: a squarish
    plate about 3 x 3.3 in with a visible standoff, the lever leaving its
    LOWER half, projecting ~3.5 in and turning back down and toward the leaf.
    It is centred on the lock stile.  Round 1 put a flat slab 0.215 ft inboard
    of the stile arris, which landed it on the panel field.

    THE HINGES: in the photo only a 0.5 in wide, 3.5 in tall black slug shows,
    tucked in the leaf/jamb gap with the knuckle joints just readable.  Round 1
    drew 1 in x 2.8 in opaque plates on the FACE of the jamb.  Those are gone;
    what is left is the barrel alone, at the door's real pivot, which is
    outboard of the leaf face.
    """
    sa = la1 if hinge_at_a1 else la0        # hinge stile arris
    ka = la0 if hinge_at_a1 else la1        # lock stile arris
    sgn = 1.0 if hinge_at_a1 else -1.0      # +1: lock stile is at the a0 end

    stile_w = STILE * lw
    hx = ka + sgn * (stile_w * 0.50)        # rose centre: ON the lock stile
    hy = ly0 + 2.78                         # 33 1/3 in above the threshold

    rw, rh = 0.125, 0.138                   # rose half-extents
    # A baked occlusion smudge on the leaf under and around the rose -- drawn
    # in the LEAF's own material (so it can only darken it, never show as a
    # patch of a different white) 1/50 in proud of the leaf face.
    grid(m, M["leaf"], hx - rw * 2.5, hx + rw * 2.5, hy - rh * 2.3, hy + rh * 1.9,
         tf + 0.0016, 6, 6,
         lambda a, y: base(a, y) * max(0.78, min(1.0,
             0.78 + 0.22 * min(1.0, (((a - hx) / (rw * 2.4)) ** 2
                                     + ((y - (hy - rh * 0.35)) / (rh * 2.0)) ** 2)))))
    bx(m, BLK, hx - rw, hx + rw, hy - rh, hy + rh, tf + 0.002, tf + 0.030)
    bx(m, BLK, hx - rw * 0.90, hx + rw * 0.90, hy - rh * 0.90, hy + rh * 0.90,
       tf + 0.030, tf + 0.044)
    # lever: leaves the rose low, runs inboard, then returns back to the leaf
    l0 = hx + sgn * (rw * 0.20)
    l1 = hx + sgn * 0.300
    bx(m, BLK, min(l0, l1), max(l0, l1), hy - rh * 0.60, hy - rh * 0.10,
       tf + 0.044, tf + 0.082)
    # the return: the tip bends down and back toward the door
    r0 = hx + sgn * 0.238
    r1 = hx + sgn * 0.300
    bx(m, BLK, min(r0, r1), max(r0, r1), hy - rh * 1.15, hy - rh * 0.45,
       tf + 0.040, tf + 0.070)
    # latch / turn on the leaf edge, just visible past the stile arris
    bx(m, BLK_D, ka - sgn * 0.004, ka + sgn * 0.012, hy - 0.075, hy + 0.075,
       tf - 0.030, tf + 0.008)

    # three barrel hinges, at the pivot: outboard of the stile, proud of the face
    for hy2 in (ly0 + 0.62, ly0 + (ly1 - ly0) * 0.505, ly1 - 0.62):
        ax = sa + (0.014 if hinge_at_a1 else -0.014)
        # 0.049 ft = 0.59 in diameter, 0.292 ft = 3.5 in tall.  Photo: the
        # visible slug is ~2 px x 13 px on a 310 px leaf, i.e. 0.5 x 3.4 in.
        m.add(cylinder(0.0245, 0.292, 6), BLK_D, at=(ax, hy2 - 0.146, tf + 0.026))


def leaf(m, M, A0, A1, H, TR, hinge_at_a1, lod):
    tf = TR - SETBACK
    tb = tf - LEAF_T

    la0, la1 = A0 + JT + GAPW, A1 - JT - GAPW
    ly0, ly1 = 0.048, H - JT - GAPW
    lw, lh = la1 - la0, ly1 - ly0

    def base(a, y):
        return tone(a, y, ly0, ly1)

    # core: no front face, so the sticking recesses into it cleanly
    open_box(m, M["edge"], la0, la1, ly0, ly1, tb, tf - 0.0015)

    cols = [(la0 + STILE * lw, la0 + (0.5 - MULL / 2) * lw),
            (la0 + (0.5 + MULL / 2) * lw, la1 - STILE * lw)]
    verts = [(la0, cols[0][0]), (cols[0][1], cols[1][0]), (cols[1][1], la1)]

    NXV, NYV = (5, 5) if lod else (3, 3)         # stile / mullion grid
    NXR, NYR = (6, 2) if lod else (4, 2)         # rail grid
    for (v0, v1) in verts:
        grid(m, M["leaf"], v0, v1, ly0, ly1, tf, NXV, NYV, base)
    y = ly0
    for kind, frac in ROWS:
        hgt = frac * lh
        if kind == "rail":
            for (c0, c1) in ((verts[0][1], verts[1][0]), (verts[1][1], verts[2][0])):
                grid(m, M["leaf"], c0, c1, y, y + hgt, tf, NXR, NYR, base)
        else:
            for (c0, c1) in ((verts[0][1], verts[1][0]), (verts[1][1], verts[2][0])):
                sweep_panel(m, M, c0, c1, y, y + hgt, tf, base,
                            cseg=3 if lod else 2, ring_mid=bool(lod))
        y += hgt

    hardware(m, M, base, la0, la1, ly0, ly1, tf, hinge_at_a1, lw)


# --------------------------------------------------------------------- frame
def seam_board(m, M, A0, A1, H, TR, hinge_at_a1):
    """The reveal.

    The photograph's leaf-to-frame seam is a soft uneven grey that all but
    vanishes on the strike side at mid height, thickens toward the head and
    down the hinge stile, and only goes properly dark in the corner where the
    leaf meets the stop.  Round 1 ran one constant near-black line the whole
    way round, which a critic called the strongest 'modelled' cue after the
    panels.  This is a graded board standing behind the leaf; only the ~1/8 in
    of it either side of the leaf is ever seen.
    """
    tf = TR - SETBACK
    la0, la1 = A0 + JT + GAPW, A1 - JT - GAPW
    ly1 = H - JT - GAPW
    sa = la1 if hinge_at_a1 else la0

    def sh(a, y):
        s = 0.98
        head = (ly1 - y) / 0.85
        if head < 1.0:
            s = min(s, 0.60 + 0.38 * max(0.0, head) ** 0.7)
        dh = abs(a - sa)
        if dh < 0.22:
            s = min(s, 0.66 + 0.32 * (dh / 0.22) ** 0.8)
        st = abs(a - (la0 if hinge_at_a1 else la1))
        if st < 0.22:
            # the strike side: mid height is nearly clean, the ends are not
            f = abs(y - ly1 * 0.46) / (ly1 * 0.52)
            s = min(s, 0.84 + 0.14 * (st / 0.22) + 0.06 * (1.0 - min(1.0, f)))
        if y < 0.30:
            s = min(s, 0.70 + 0.26 * (y / 0.30))
        s *= 1.0 + 0.035 * math.sin(y * 6.7 + a * 3.1) + 0.02 * _h(a * 9.0, y * 5.0)
        return max(0.0, min(1.0, s))

    grid(m, M["seam"], A0 - 0.02, A1 + 0.02, -0.05, ly1 + 0.10,
         tf - 0.034, 7, 16, sh)


def frame(m, M, A0, A1, H, TR, hinge_at_a1):
    """Jamb lining, blanking board and the graded reveal seam."""
    for (j0, j1) in ((A0, A0 + JT), (A1 - JT, A1)):
        bx(m, M["jamb"], j0, j1, 0.0, H, TR + 0.018, TR - 0.36)
    bx(m, M["jamb"], A0, A1, H - JT, H, TR + 0.018, TR - 0.36)
    bx(m, M["blank"], A0 - 0.03, A1 + 0.03, -0.06, H + 0.03,
       TR - 0.225, TR - 0.200)
    seam_board(m, M, A0, A1, H, TR, hinge_at_a1)


def casing(m, M, A0, A1, H, TR):
    """Flat 3 1/2 in casing, a darker outer return, a head cap and the mitres.

    The photo reads casing 0.90 of the leaf and a 2 px line at 0.76 of it
    where the casing's outer arris stands proud of the wall.  That line is
    built here as the casing's own outer RETURN face in a darker white --
    honest geometry rather than a decal painted on someone else's wall.
    """
    i0, i1 = A0 + JT - REVEAL, A1 - JT + REVEAL
    o0, o1 = i0 - CASE_W, i1 + CASE_W
    hy0 = H - JT + REVEAL
    hy1 = hy0 + CASE_W

    def face(c0, c1, y0, y1, vertical):
        nx_, ny_ = (2, 9) if vertical else (9, 2)
        grid(m, M["case"], c0, c1, y0, y1, TR + CASE_P, nx_, ny_,
             lambda a, y: tone(a, y, 0.0, hy1, amp=0.7) * 0.995)

    face(o0, i0, 0.0, hy0 + 0.004, True)
    face(i1, o1, 0.0, hy0 + 0.004, True)
    face(o0, o1, hy0, hy1, False)
    # the body behind the face (so the casing has thickness at the reveal)
    for (c0, c1, y0, y1) in ((o0, i0, 0.0, hy0 + 0.004), (i1, o1, 0.0, hy0 + 0.004),
                             (o0, o1, hy0, hy1)):
        bx(m, M["case"], c0, c1, y0, y1, TR - 0.030, TR + CASE_P - 0.002)
    # outer return: the dark line where the casing stands proud of the wall
    rt = 0.030
    for (c0, c1, y0, y1) in ((o0, o0 + rt, 0.0, hy1), (o1 - rt, o1, 0.0, hy1),
                             (o0, o1, hy1 - rt, hy1)):
        bx(m, M["case_ret"], c0, c1, y0, y1, TR - 0.012, TR + CASE_P + 0.001)
    # head cap: a thin board overhanging the head casing on three sides
    bx(m, M["case_hi"], o0 - 0.036, o1 + 0.036, hy1 - 0.012, hy1 + 0.038,
       TR - 0.018, TR + BEAD_P + 0.014)
    # the 45 degree mitre at each head corner
    for (px, s) in ((i0, -1.0), (i1, 1.0)):
        cx0 = px + s * CASE_W
        v = [(px, hy0, TR + CASE_P + 0.0012),
             (cx0, hy0 + CASE_W, TR + CASE_P + 0.0012),
             (cx0 - s * 0.012, hy0 + CASE_W, TR + CASE_P + 0.0012),
             (px - s * 0.012, hy0, TR + CASE_P + 0.0012)]
        m.add(Part(v, [(0, 1, 2), (0, 2, 3)], smooth=False), M["mitre"])


def threshold_shadow(m, A0, A1, TR):
    """One coplanar graded quad on the floor at the door foot."""
    t0 = TR + BEAD_P
    depth, over = 0.36, 0.22
    ny, na = 5, 4
    verts, cols, tris = [], [], []
    for i in range(ny + 1):
        f = i / float(ny)
        t = t0 + depth * f
        s = 0.50 + 0.50 * (f ** 1.15)
        for k in range(na + 1):
            g = k / float(na)
            a = (A0 - over) + ((A1 + over) - (A0 - over)) * g
            edge = min(1.0, 3.2 * min(g, 1 - g))
            sh = 1.0 - (1.0 - s) * edge
            verts.append((a, 0.048, t))
            cols.append((sh, sh, sh))
    for i in range(ny):
        for k in range(na):
            p = i * (na + 1) + k
            q = p + na + 1
            tris += [(p, q, q + 1), (p, q + 1, p + 1)]
    m.add(Part(verts, tris, smooth=True, colors=cols), SHAD)


# --------------------------------------------------------------------- build
def main():
    h = house()
    R = rooms_by_id(h)
    r17 = R[ROOM]
    ops = {o["id"]: o for o in r17["openings"]}
    fp = r17["footprint"]

    doors, casings = Model(), Model()
    report = []

    for (oid, nb_id, nb_oid, label, hinge_a1, lod) in DOORS:
        op = ops[oid]
        i = op["edge_index"]
        A, u, n, L = edge_frame(r17, i)
        s, e, _, _ = op_world(r17, op)

        nb = R[nb_id]
        nbop = next(o for o in nb["openings"] if o["id"] == nb_oid)
        nA, nu, nn, nL = edge_frame(nb, nbop["edge_index"])
        ns, ne, _, _ = op_world(nb, nbop)

        nb_off = (nA[0] - A[0]) * (-n[0]) + (nA[1] - A[1]) * (-n[1])
        TR = WALL_T - nb_off

        def a_of(p):
            return (p[0] - s[0]) * u[0] + (p[1] - s[1]) * u[1]
        A0 = min(0.0, a_of(ns), a_of(ne))
        A1 = max(op["width"], a_of(ns), a_of(ne))
        H = max(op["height"], nbop["height"])

        rot = math.atan2(-u[1], u[0])
        at = (s[0] - fp["x"], 0.0, s[1] - fp["z"])

        M = mset("d17" + label, EMIS.get(label, 0.0))

        sub = Model()
        leaf(sub, M, A0, A1, H, TR, bool(hinge_a1), lod)
        for part, mat in sub._parts:
            doors.add(part, mat, at=at, rot_y=rot)

        sub = Model()
        frame(sub, M, A0, A1, H, TR, bool(hinge_a1))
        casing(sub, M, A0, A1, H, TR)
        threshold_shadow(sub, A0, A1, TR)
        for part, mat in sub._parts:
            casings.add(part, mat, at=at, rot_y=rot)

        report.append(f"  {oid} {label:<7} edge {i}  TR={TR:.3f}  "
                      f"a=[{A0:.3f},{A1:.3f}] H={H:.2f} em={M['leaf'].emissive_strength if M['leaf'].emissive != (0,0,0) else 0:.3f}")
        if op["type"] != "passage":
            raise SystemExit(f"opening {oid} is {op['type']}, expected passage")

    print("\n".join(report))

    os.makedirs(GLB, exist_ok=True)
    for name, m in (("Hall2F Doors", doors), ("Hall2F Door Casings", casings)):
        path = os.path.join(GLB, name.replace(" ", "_").lower() + "2.glb")
        m.save(path)
        lo, hi = m.bounds()
        pos = ((lo[0] + hi[0]) / 2, lo[1], (lo[2] + hi[2]) / 2)
        res = place(name, path, ROOM, pos=pos, rot_y_deg=0.0, scale=1.0)
        kb = os.path.getsize(path) / 1024.0
        print(f"  {name:<22} {kb:7.1f} KB  bbox="
              f"{tuple(round(hi[k] - lo[k], 2) for k in range(3))}"
              f"  pos=({pos[0]:.2f},{pos[1]:.2f},{pos[2]:.2f})  {res['action']}")


if __name__ == "__main__":
    main()
