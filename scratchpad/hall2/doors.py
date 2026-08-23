"""Room 17 (2F Hallway) -- DOORS + TRIM.   v2 rebuild, round 3.

Owns two pieces:

    Hall2F Doors       five CLOSED white 6-panel leaves, cased, with matte
                       black lever-on-a-rose and three black barrel hinges.
    Hall2F Baseboards  the skirting run, cut to the room's L footprint, with
                       a baked floor contact shadow.

It does NOT own the openings any more -- `openings()` is kept for reference but
`main()` never calls it (room 17's seven openings are frozen: 124 125 126 127
135 plus the two cut-away edges 133/134).

WHY THE OPENINGS SIT WHERE THEY DO
----------------------------------
`docs/floor plan/Second Floor Plan App.png` is a phone screenshot of the HA
app, not a drawing.  What it DOES support, and what the owner states, is the
order down the WEST side of the hall reading from the south (dead) end
northwards:  Rios Room, closet, Guest Room.  Master Bedroom is the single door
at the NORTH end; the bathroom is at the south end on the SOUTH wall.

SWING / HARDWARE -- re-derived in round 3, see the report
--------------------------------------------------------
`two_closed_white_doors_2.jpg` is the SW corner: its LEFT door and its RIGHT
door sit on two walls meeting in a corner.  The same corner rendered from
`v2_doors` puts the BATH (south wall, and the darker of the two because the
south face is the one the sun never reaches) on the LEFT and RIOS (west wall,
bright) on the RIGHT -- the photo shows exactly that value split, left door
L 163-204, right door L 222.  So:

* bath   (south wall): lever on the EAST stile, THREE black hinges on the
  WEST stile, plainly visible in `two_closed_white_doors_2.jpg` at the left
  door's right-hand edge.  Round 2 had `hinges=False` here; that was wrong.
* west three: lever on the SOUTH stile (photo 2's right door, lever at its
  frame-left = south), hinges on the NORTH stile.
* master (north wall): lever on the WEST stile
  (`hallway_looking_towards_stairs.jpg`), hinges east.

Every leaf now carries hinges: `docs/v2 Hallway-jpg` describes these doors as
"matte black lever handles and black hinges", and a closed door with no
knuckles anywhere was the round-2 critic's complaint.

WHAT ROUND 3 CHANGED
--------------------
1. The raised panels are COVED, not chamfered.  `cove_panel` sweeps the bevel
   through a smoothstep profile in `seg` steps with SMOOTHED normals, so each
   bevel's tone ramps continuously from the sticking to the shoulder instead
   of rendering as one constant fill per sloped face.  The top sweep, the two
   side sweeps and the bottom sweep carry three different materials so the top
   picks up a specular smear (roughness 0.30) and the bottom drops into shadow.
2. AO is baked where the engine cannot cast it: a dark rebate groove round
   every panel, a dark reveal slot between every leaf and its frame, and a
   three-band alpha contact shadow on the floor at the foot of the skirting.
3. Every white is now a different white -- see `_mset`.
"""

import math
import os
import sys

sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\circ")

from ckit import *                                          # noqa: F401,F403
from ckit import save_and_place, blit, room_row, _req

ROOM, W, D, H = 17, 8.1, 16.7, 8.0

# ------------------------------------------------------------------ spans
# wall-axis (== room-local) feet.  'n'/'s' use local x, 'w'/'e' use local z.
MBED   = ("n", 4.05,  6.95, 6.85)      # world x 14.55..17.45
BATHD  = ("s", 0.90,  3.70, 6.78)      # world x 11.40..14.20
GUEST  = ("w", 7.95, 10.68, 6.78)      # world z 14.55..17.28  (pairs room 13/111)
CLOSET = ("w", 11.25, 13.40, 6.78)     # world z 17.85..20.00
RIOS   = ("w", 13.98, 16.38, 6.78)     # world z 20.58..22.98

DOORS = [MBED, BATHD, GUEST, CLOSET, RIOS]

WALL_T = 0.35            # house.js WALL_THICKNESS -- the reveal depth
CASE = 0.190             # flat casing width (photos read ~2 1/4 in)
JT = 0.052               # jamb board face width
STOPW = 0.022            # the proud stop bead on the jamb rebate
GAPW = 0.024             # the dark reveal slot between bead and leaf
REV = 0.155              # jamb reveal in front of the leaf face
LEAF_T = 0.118           # leaf thickness


# ------------------------------------------------------------- materials
#
# The albedo ladder, measured off the two door photos (sRGB luma of a clean
# sample; see the report for box coords).  Everything is quoted relative to
# the LEAF FACE, because the absolute render level is set by which wall the
# door is on, not by the paint:
#
#   panel cove, top sweep      1.06   photo 215-239 vs leaf 191-220
#   skirting top cap           1.05   photo 213 vs a wall at 160
#   stop bead                  1.01   photo 192 vs leaf 191
#   skirting body              1.01   photo 191 (photo 1, lit run)
#   LEAF FACE                  1.00   photo 191-220
#   panel field (top band)     0.98   photo 198-212
#   panel field (bottom band)  0.94   photo 187-190
#   casing                     0.92   photo 173-202
#   jamb reveal return         0.83   photo 161 -- the "warm mid-grey"
#   panel rebate groove        0.79   photo 166-182 at the sticking
#   leaf-to-frame reveal slot  0.63   photo 124
#
# `k` lifts a whole set toward white for the SOUTH wall, whose inner face the
# sun never reaches: round 2 probed albedo 245 -> 255 there and moved the
# render only 161 -> 168, so the set is pushed to the ceiling and the residue
# is the renderer (ROOM-BRIEF: "the one wall the sun never reaches").
def _mset(tag, k):
    def C(hexc, rough=0.62, met=0.0):
        return Material(tag + hexc.lstrip("#") + ("%.2f" % rough),
                        mix(hexc, "#ffffff", k), roughness=rough, metallic=met)
    return dict(
        leaf   = C("#f1eee9", 0.64),      # leaf body / face / edges
        pf     = C("#eae7e0", 0.58),      # panel field -- a step below the leaf
        cov_t  = C("#fdfcf9", 0.30),      # top sweep -- the specular smear
        cov_s  = C("#f4f1ec", 0.34),      # left / right sweeps
        cov_b  = C("#cec8bf", 0.46),      # bottom sweep -- soft shadow
        ao     = C("#bcb6ac", 0.86),      # the rebate groove at the sticking
        case   = C("#e5e1db", 0.66),      # flat casing
        stop   = C("#f9f8f5", 0.46),      # the proud stop bead
        jamb   = C("#dcd6cd", 0.74),      # the reveal return into the opening
        gap    = Material(tag + "gap", mix("#4c4945", "#ffffff", k * 0.4),
                          roughness=0.95),
    )


MSET = _mset("h17", 0.0)          # west + north doors
MSET_S = _mset("h17s", 0.50)      # the bathroom door on the dark south face

BLK = Material("h17blk", "#212124", roughness=0.42, metallic=0.30)

# skirting -- the critic's point 3: the skirting must read BRIGHTER than the
# door above it and its top edge must catch a highlight.
SK_BODY = Material("h17sk", "#f6f4f0", roughness=0.58)
SK_CAP = Material("h17skc", "#fdfcfa", roughness=0.40)
SK_TAPER = Material("h17skt", "#e8e4de", roughness=0.66)
SK_FOOT = Material("h17skf", "#cbc6be", roughness=0.80)   # the shadowed toe
# Baked floor contact shadow.  ROOM-BRIEF asks for ALPHA here, "never an
# opaque colour mix" -- but alpha is impossible inside this piece:
# `cutaway.js WALL_ARCH_RE` matches /baseboards?/ and /doors?/, so both of this
# builder's pieces are classed as wall architecture and every frame runs
# `objects.js fadeSubtree(mesh, wallOpacity)`, which writes `m.opacity` on
# EVERY material in the subtree.  An authored 0.26 is overwritten with 1.0 the
# moment the piece is visible; measured, the alpha decal rendered L 38 against
# a floor at L 136, i.e. a black chip.  So these are opaque and graded off the
# floor's OWN albedo (`Hall2F Floor Planks` is #8e8b85 at roughness 0.20, two
# materials, so there is almost no grain to erase over a 0.23 ft band), with
# the same roughness so the sheen does not change across the joint.
SH1 = Material("h17sh1", "#6b6864", roughness=0.22)
SH2 = Material("h17sh2", "#7c7974", roughness=0.21)
SH3 = Material("h17sh3", "#87847f", roughness=0.20)


# ---------------------------------------------------------------- helpers
def cut(lo, hi, gaps):
    """[lo,hi] minus every (a,b) in gaps."""
    segs = [(lo, hi)]
    for g0, g1 in gaps:
        out = []
        for s0, s1 in segs:
            if g1 <= s0 or g0 >= s1:
                out.append((s0, s1))
                continue
            if s0 < g0:
                out.append((s0, g0))
            if s1 > g1:
                out.append((g1, s1))
        segs = out
    return [(a, b) for a, b in segs if b - a > 0.03]


def _strip(m, mat, rings, pick, flip):
    """One swept side of a cove, as a smooth-shaded triangle strip.

    `rings` are the profile stations outermost-first; `pick` selects the two
    corners of a ring that belong to this side, in the order that makes the
    face wind outward.  Smoothed normals are the whole point: they are what
    turns a bevel from one constant fill into a continuous tonal ramp.
    """
    v, tris = [], []
    for r in rings:
        p, q = pick(*r)
        v += [p, q]
    for i in range(len(rings) - 1):
        a, b, c, d = 2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2
        tris += [(a, b, c), (a, c, d)]
    if flip:
        tris = [(a, c, b) for (a, b, c) in tris]
    m.add(Part(v, tris, smooth=True), mat)


def cove_panel(m, M, x0, x1, y0, y1, zf, sign, seg=3, bands=True):
    """A raised panel whose bevel is a COVE, not a flat chamfer.

    x0..x1 / y0..y1 is the panel opening in the stiles and rails, `zf` the
    leaf face plane and `sign` +1 for the face that looks into the hall.

    Profile, outermost station first:
      d = -0.028  the rebate groove floor -- baked AO, the darkest tone here
      d = -0.012  the cove springs
      ...         smoothstep sweep, `seg` segments, smoothed
      d = +0.042  the raised field
    """
    def Z(d):
        return zf + sign * d

    w, h = x1 - x0, y1 - y0
    bw = min(0.155 * w, 0.30 * h)
    bh = bw
    g = 0.032                                  # groove width round the panel

    # ---- the rebate groove: a recess whose floor is the darkest tone on the
    # leaf.  This is the AO the engine will not cast for us -- the round-2
    # critic's "the corner where the bevel meets the panel field is exactly as
    # bright as the open door face, which is physically impossible".
    a, b = Z(-0.028), Z(0.002)
    bx(m, M["ao"], x0, x1, y0, y1, min(a, b), max(a, b))

    # ---- the cove sweep
    X0, X1, Y0, Y1 = x0 + g, x1 - g, y0 + g, y1 - g
    rings = []
    for i in range(seg + 1):
        t = i / float(seg)
        s = t * t * (3.0 - 2.0 * t)            # smoothstep: flat at both ends
        rings.append((X0 + bw * t, X1 - bw * t, Y0 + bh * t, Y1 - bh * t,
                      Z(-0.012 + 0.054 * s)))
    flip = sign < 0
    _strip(m, M["cov_b"], rings,
           lambda a0, a1, b0, b1, z: ((a0, b0, z), (a1, b0, z)), flip)
    _strip(m, M["cov_t"], rings,
           lambda a0, a1, b0, b1, z: ((a1, b1, z), (a0, b1, z)), flip)
    _strip(m, M["cov_s"], rings,
           lambda a0, a1, b0, b1, z: ((a1, b0, z), (a1, b1, z)), flip)
    _strip(m, M["cov_s"], rings,
           lambda a0, a1, b0, b1, z: ((a0, b1, z), (a0, b0, z)), flip)

    # ---- the raised field.  One tone, deliberately: round 3's first attempt
    # split it into graded bands and the steps rendered as hard horizontal
    # seams across the leaf -- exactly the "repeat artefact" the round-2
    # critic penalised elsewhere.  The tonal ramp comes from the cove.
    fx0, fx1, fy0, fy1, fz = rings[-1]
    p = quad((fx0, fy0, fz), (fx1, fy0, fz), (fx1, fy1, fz), (fx0, fy1, fz))
    if flip:
        p = Part(p.verts, [(a, c, b) for (a, b, c) in p.tris])
    m.add(p, M["pf"])


# vertical layout of a 6-panel leaf, as fractions of the leaf height, bottom
# up.  Standard colonial 6-panel: thick bottom rail, tall bottom pair, tall
# middle pair, short top pair -- matched against `two_closed_white_doors_2`'s
# left door, allowing for the heavy foreshortening at the door's foot.
ROWS = [("rail", 0.073), ("panel", 0.335), ("rail", 0.040),
        ("panel", 0.295), ("rail", 0.055), ("panel", 0.140), ("rail", 0.062)]


def leaf_face(m, M, la0, la1, ly0, ly1, z, sign, seg=3, bands=True):
    """Six coved panels on one face of a leaf."""
    lw, lh = la1 - la0, ly1 - ly0
    stile = 0.105 * lw
    mull = 0.075 * lw
    cols = [(la0 + stile, la0 + lw / 2 - mull), (la0 + lw / 2 + mull, la1 - stile)]

    y = ly0
    for kind, frac in ROWS:
        hgt = frac * lh
        if kind == "panel":
            for (cx0, cx1) in cols:
                cove_panel(m, M, cx0, cx1, y, y + hgt, z, sign,
                           seg=seg, bands=bands)
        y += hgt


def hardware(s, M, a1, top, LZ1, hinge_a):
    """Matte black lever on a RECTANGULAR ROSE, plus three barrel hinges.

    The round-2 critic: "the handle is a floating black stub with no rose /
    escutcheon".  `two_closed_white_doors_1.jpg` shows a squarish black
    backplate roughly 3 x 3.5 in with the lever bar coming off its centre.
    """
    hx = a1 - JT - GAPW - STOPW - 0.240
    hy = 3.05
    # rose: a flat plate, then a slightly smaller proud step, then the boss
    bx(s, BLK, hx - 0.120, hx + 0.120, hy - 0.150, hy + 0.150,
       LZ1 - 0.002, LZ1 + 0.030)
    bx(s, BLK, hx - 0.098, hx + 0.098, hy - 0.126, hy + 0.126,
       LZ1 + 0.030, LZ1 + 0.052)
    s.add(cylinder(0.058, 0.055, 10), BLK, at=(hx, hy, LZ1 + 0.052), rot_x=R(90))
    # the lever bar and its down-turned tip
    bx(s, BLK, hx - 0.330, hx + 0.052, hy - 0.036, hy + 0.038,
       LZ1 + 0.070, LZ1 + 0.124)
    bx(s, BLK, hx - 0.350, hx - 0.276, hy - 0.124, hy - 0.030,
       LZ1 + 0.074, LZ1 + 0.120)
    # three barrel hinges on the hinge stile
    for y in (0.90, top * 0.50, top - 0.66):
        s.add(cylinder(0.052, 0.30, 8), BLK, at=(hinge_a, y - 0.15, LZ1 - 0.012))


def door_unit(m, wall, a0, a1, top, both_faces=True, backing=False, rev=REV,
              M=None):
    """One closed 6-panel door: jamb lining, a proud stop bead, a DARK REVEAL
    SLOT, the leaf, flat casing with a stepped head cap, lever-on-rose and
    three hinges.

    `rev` is how far the leaf FACE sits back from the wall face; 0.155 ft
    (~2 in) is the real figure off the photos and every door gets it.

    Lever always on a1, hinges always on a0 -- callers that need the mirror
    pass their spans through `_door_unit_mirrored`.
    """
    s = Model()
    M = M or MSET
    LZ1 = -rev
    LZ0 = LZ1 - LEAF_T

    # ---- jamb lining, the full depth of the wall.  Its inner face is the
    # 2 in reveal the camera actually reads, and it is a whole value step
    # below the leaf -- photo L 161 against a leaf at 191-220.
    bx(s, M["jamb"], a0, a0 + JT, 0.0, top, -WALL_T, 0.012)
    bx(s, M["jamb"], a1 - JT, a1, 0.0, top, -WALL_T, 0.012)
    bx(s, M["jamb"], a0, a1, top - JT, top, -WALL_T, 0.012)

    # ---- proud stop bead on the jamb rebate
    for (b0, b1) in ((a0 + JT, a0 + JT + STOPW), (a1 - JT - STOPW, a1 - JT)):
        bx(s, M["stop"], b0, b1, 0.0, top - JT, LZ1 - 0.030, LZ1 + 0.008)
    bx(s, M["stop"], a0 + JT, a1 - JT, top - JT - STOPW, top - JT,
       LZ1 - 0.030, LZ1 + 0.008)

    # ---- the leaf
    la0, la1 = a0 + JT + STOPW + GAPW, a1 - JT - STOPW - GAPW
    ly0, ly1 = 0.030, top - JT - STOPW - GAPW
    bx(s, M["leaf"], la0, la1, ly0, ly1, LZ0, LZ1)
    leaf_face(s, M, la0, la1, ly0, ly1, LZ1, +1, seg=3, bands=True)
    if both_faces:
        leaf_face(s, M, la0, la1, ly0, ly1, LZ0, -1, seg=2, bands=False)

    # ---- the reveal slot: the dark line between leaf and frame.  Round 2 had
    # the stop bead lapping 0.020 ft OVER the leaf edge, so there was no gap to
    # be dark -- "no leaf-to-frame reveal shadow at all".  Drawn as recessed
    # quads rather than boxes: it is only ever read face-on and boxes here cost
    # 12 tris apiece against 2.
    def slot(x0, x1, y0, y1):
        m2 = quad((x0, y0, LZ1 - 0.014), (x1, y0, LZ1 - 0.014),
                  (x1, y1, LZ1 - 0.014), (x0, y1, LZ1 - 0.014))
        s.add(m2, M["gap"])
    slot(a0 + JT + STOPW, la0 + 0.002, 0.0, ly1)
    slot(la1 - 0.002, a1 - JT - STOPW, 0.0, ly1)
    slot(la0, la1, ly1 - 0.002, top - JT - STOPW)
    # and the shadow under the leaf
    bx(s, M["gap"], la0, la1, 0.0, ly0 - 0.002, LZ0 - 0.004, LZ1 + 0.004)

    if backing:
        # this opening faces unmodelled space -- seal the back of the reveal
        bx(s, M["jamb"], a0, a1, 0.0, top, -WALL_T, -WALL_T + 0.045)

    # ---- flat casing on the room face, laid over the wall/jamb joint
    bx(s, M["case"], a0 - CASE, a0 + 0.022, 0.0, top + 0.022, 0.0, 0.048)
    bx(s, M["case"], a1 - 0.022, a1 + CASE, 0.0, top + 0.022, 0.0, 0.048)
    bx(s, M["case"], a0 - CASE, a1 + CASE, top - 0.022, top + CASE, 0.0, 0.048)
    # the small stepped cap over the head casing (visible on every door photo)
    bx(s, M["stop"], a0 - CASE - 0.035, a1 + CASE + 0.035, top + CASE,
       top + CASE + 0.055, 0.0, 0.082)

    hardware(s, M, a1, top, LZ1, a0 + JT + STOPW + 0.010)

    blit(m, s, wall, W, D, 0.0)


def _door_unit_mirrored(m, wall, a0, a1, top, **kw):
    """Same unit with the lever on a0 and the hinge side on a1."""
    s = Model()
    door_unit(s, "n", 0.0, a1 - a0, top, **kw)      # build in a flat frame...
    t = Model()
    for part, mat in s._parts:
        t._parts.append((Part([(a0 + (a1 - a0) - x, y, z) for (x, y, z) in part.verts],
                              [(p, r, q) for (p, q, r) in part.tris], part.smooth),
                         mat))
    # `door_unit` already blitted onto 'n', where wall-axis == x and depth == z.
    blit(m, t, wall, W, D, 0.0)


# =============================================================== the pieces
def piece_doors():
    m = Model()
    # west wall: lever SOUTH (a1), hinges NORTH (a0).
    door_unit(m, "w", *GUEST[1:])
    door_unit(m, "w", *CLOSET[1:], backing=True, both_faces=False)
    door_unit(m, "w", *RIOS[1:], backing=True, both_faces=False)
    # north wall: lever WEST == a0, so mirror.
    _door_unit_mirrored(m, "n", *MBED[1:])
    # south wall: lever EAST == a1, hinges WEST == a0 -- three of them, they
    # are the ones plainly visible in `two_closed_white_doors_2.jpg`.
    door_unit(m, "s", *BATHD[1:], M=MSET_S)
    return m


def piece_baseboards():
    """Skirting cut to the L footprint, with a baked floor contact shadow.

    The room is a polygon: the EAST wall exists only over local z 0..7.7 and
    the SOUTH wall only over local x 0..3.95.  Edges 2 and 3 (the head of the
    stairwell and the knee-wall line) are cut away and carry no skirting.
    """
    m = Model()
    # profile, bottom up: a shadowed toe, the body, a proud cap, a taper.
    # The cap is the brightest white in the room -- photo 2 meters the
    # skirting's top edge at L 213 against a wall at 160 right beside it.
    prof = ((0.000, 0.026, 0.070, SK_FOOT),
            (0.026, 0.452, 0.072, SK_BODY),
            (0.452, 0.492, 0.086, SK_CAP),
            (0.492, BB_H, 0.050, SK_TAPER))
    # the contact shadow: alpha bands on the floor, darkest at the skirting,
    # running OUT past its own footprint (ROOM-BRIEF's failure mode #4).
    shadow = ((0.000, 0.050, SH1), (0.050, 0.120, SH2), (0.120, 0.220, SH3))

    runs = {
        "n": (0.0, 8.10, [MBED]),
        "e": (0.0, 7.70, []),
        "s": (0.0, 3.95, [BATHD]),
        "w": (0.0, 16.70, [GUEST, CLOSET, RIOS]),
    }
    for wall, (lo, hi, doors) in runs.items():
        gaps = [(d[1] - CASE - 0.02, d[2] + CASE + 0.02) for d in doors]
        s = Model()
        for (a, b) in cut(lo, hi, gaps):
            for (y0, y1, dep, mat) in prof:
                bx(s, mat, a, b, y0, y1, 0.0, dep)
            # The three west doors sit 0.15 ft apart, so `cut` leaves skirting
            # slivers narrower than the shadow band is deep -- on those the
            # decal reads as a solid black chip on the floor rather than a
            # contact shadow, so they get skirting but no shadow.
            if b - a > 0.45:
                for (d0, d1, mat) in shadow:
                    # y 0.040: clear of `Hall2F Floor Planks`, whose top face
                    # is at y 0.0235, without standing so proud that the band
                    # shows an edge at a grazing angle.
                    rect_up(s, mat, a, b, 0.040, 0.086 + d0, 0.086 + d1)
        blit(m, s, wall, W, D, 0.0)

    # NOTE: the grille / switch plates / night light live in `Hall2F Wall
    # Fittings`, owned by another builder.  This piece is the skirting only.
    return m


# =================================================================== main
def openings():
    """FROZEN.  Room 17's seven openings (124 125 126 127 135 + the cut-away
    edges 133/134) are a hard spec and round 3 does not touch them.  Left here
    only as the record of what they are."""
    raise SystemExit("openings are frozen -- see the module docstring")


# NOTE (round V3): "Hall2F Baseboards" moved OUT of this file and into
# `base.py`.  `piece_baseboards` below is kept only as the record of what round
# 3 built; it is wired to the OLD 8.10 x 16.70 rectangle, so re-running it would
# put a phantom board through the stairwell void and leave the west alcove bare
# again.  `roomkit.place` is idempotent by NAME, so leaving it in PIECES meant
# any `python doors.py` would silently overwrite the new run.  Build the
# skirting with `python base.py`.
PIECES = {
    "doors": ("Hall2F Doors", piece_doors),
}


def main(only=None):
    print("room 17 Hallway -- doors + trim (round 3)")
    for k, (name, fn) in PIECES.items():
        if only in (None, k):
            save_and_place(name, fn(), ROOM)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
