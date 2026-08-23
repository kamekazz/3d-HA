"""Room 17 -- `Hall2F Knee Wall`, round-2 rebuild (wave A).

Owns exactly ONE piece, idempotent by name.  Writes glb/hall2f_knee_wall.glb
and places THAT file, so disk and app can never disagree.  Nothing else in
room 17 is touched, and no other room is touched at all.

WHY
---
Round-1's two blind critics both failed this piece and disagreed about why, in
a way that turned out to be informative: from `p_stairs` the cap reads as a
thin board with a step, from `p_runner` its returned end reads as ONE chunky
slab with a fat square lip.  Both are true of the same object -- the old cap
was cap-board (0.125) + sub-band (0.085) + two soffits stacked into a single
0.21 ft (2.5 in) white mass, and from the end you see the whole stack at once
with nothing dark between the layers, so it merges.

MEASURED OFF THE PHOTOGRAPHS  (450x600 JPGs, so ~2 px per inch at the near end)
------------------------------------------------------------------------------
`hallway_looking_towards_stairs.jpg`, vertical cut at x=320 (mid-run), top to
bottom -- this is the section drawing the whole rebuild is fitted to:

    y 322..359   cap top plane                 230
    y 360..364   eased outer arris             238..241   <- specular streak
    y 365..373   cap nose, vertical            215 -> 173 <- a RAMP, not a fill
    y 374..375   the reveal under the nose      140       <- the dark line
    y 376..400   painted wall face             143..159

and the same cut at x=380 (nearer): 214 / 218 / 207->148 / 116 / 117..129.
Cut at x=300 through the base: face 154 at the top falling to 140 at the
skirting, skirting cove-top 199-200, skirting body 188 falling to 145 at the
toe, then the floor contact 86..94 against open floor at 123.

Normalised on each photo's own east wall so the two exposures can be compared:

    surface                 photo/east-wall        our round-1 render
    cap top plane           1.84 / 1.77 / 1.62     1.25 flat
    painted face  N -> S    1.25 / 1.04 / 0.97     0.99 / 1.06 / 1.04
    skirting                1.59                   1.02   (DARKER than the face)

So the photograph's cap is 1.6-1.8x its own wall and the face is about 1.0x --
the cap and the face are two clearly different whites.  Ours were 1.25 and
1.03: one white, which is round 2's theme 5 exactly.  The face target here is
absolute (the photo's own numbers), which assumes this wave's `Hall2F Wall
Wash Skins` brings the room walls down from our 175 to the photo's ~125; see
the report.

WHAT CHANGED
------------
* Cap section rebuilt: 1.18 in of visible edge (0.070 nose + 0.028 eased
  arris) over a 0.055 ft DARK soffit over a small cove, instead of a 2.5 in
  stack of white boxes.  The sub-band is gone.
* The reveal is now three things at once, which is what makes it read: a dark
  down-facing soffit, a cove that turns away from the light, and the top
  0.055 ft of the face baked to 0.78x.  Any one alone metered as nothing.
* Every white is a different white: arris > cap top > skirting cove > nose >
  skirting body > face > reveal > soffit.  Eight values, fitted above.
* The face carries a real along-the-run ramp (north 0.90 -> south 0.72) and a
  vertical one (top 1.02 -> skirting 0.92), both taken off the photo.
* THE RETURN LEG (new).  Room 17's edge 0 -- z = 6.81, x 7.61..11.92 -- is a
  full-span opening with no wall, so from `p_runner` you look straight past
  the knee wall's north end into the stairwell and see lit treads and the
  shaft wall five feet below the floor.  The owner asked not to see that.  The
  photograph shows plain floor and wall there, which means our footprint's
  well starts further north than the real one; the footprint is signed off, so
  the fix inside this piece is the guard turning the corner and running east
  along edge 0.  Verified by raycast: every ray that reached the well crossed
  z = 6.81 between x 7.9 and 8.8 at y 0.95..2.2, all of it inside this leg and
  under the cap line.  Behind the `p_down` camera (local z 7.35), so the
  flight still reads in full from the head.
"""

import math
import os
import random
import sys

sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")

from roomkit.glb import Model, Material, Part, box          # noqa: E402
from roomkit.place import place                             # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOM = 17
NAME = "Hall2F Knee Wall"

# ------------------------------------------------------------------ geometry
# The east (well) face MUST stay at x = 7.75: `Hall2F Stair Rail` hangs its two
# black brackets off it (stairs.py `_bracket`, wall pad reaching x 7.59 in room
# coordinates).  Moving this face west would leave them in mid air.
XE = 7.75          # well face
XW = 7.37          # hall face  -> body 0.38 ft = 4.6 in (was 5.0; the critic
                   # read the old body as "a solid 8-inch block")
Z1 = 16.92         # dies 0.03 ft into the south wall's mass
ZN = 6.43          # north face of the return leg
ZL = 6.81          # south face of the return leg = the well's own edge
XL = 9.95          # east end of the return leg

TOP = 3.16         # top of the cap.  The photograph solves to 33.8 in (bath
                   # door leaf 138 px = 80 in; cap top 58.3 px above the same
                   # floor line) and this is 37.9 in.  It is held 4 in high by
                   # `Hall2F Stair Rail`, whose level return at the head of the
                   # flight tops out at y = 3.06 and projects 0.4 ft EAST of
                   # the cap -- at a 34 in cap that black bar breaks through
                   # the cap board.  Reported to wave B; drop this to 2.90 the
                   # day the rail return comes down to <= 2.55.

ARR = 0.028        # the eased arris on the cap's long top edges
CAP_T = 0.098      # cap board: 0.070 of square nose + ARR of eased nosing
CAP_O = 0.085      # cap overhang past each wall face  (1.0 in)
COVE_H = 0.055     # the small cove tucked under the cap
COVE_P = 0.030     # how far it projects from the wall face
CAP_Y = TOP - CAP_T          # 3.062 -- the cap's soffit
COVE_Y = CAP_Y - COVE_H      # 3.007
BODY_H = COVE_Y              # the painted face stops here

BB_H = 0.52        # skirting height, matching the room's own run
BB_T = 0.055       # how proud of the wall face it stands
BB_CH = 0.038      # its top cove/bevel

# ----------------------------------------------------------------- materials
# One material per ROLE, not per value: every value difference is carried by
# vertex colour, so the whole assembly is a handful of primitives.  Roughness
# is the second lever and it is doing real work here -- the arris is the only
# 0.24 surface on the piece and that is why it reads as a specular streak.
FACE = Material("kw4face", "#ffffff", roughness=0.74)   # both painted faces
CAPM = Material("kw4cap", "#ffffff", roughness=0.44)    # cap top + nose
ARRM = Material("kw4arr", "#ffffff", roughness=0.24)    # the eased arris
COVEM = Material("kw4cove", "#ffffff", roughness=0.50)  # cove under the cap
SOF = Material("kw4sof", "#6d6a64", roughness=0.88)     # soffit of the overhang
BBM = Material("kw4bb", "#ffffff", roughness=0.60)      # skirting body
BBC = Material("kw4bbc", "#ffffff", roughness=0.34)     # skirting cove cap
CORE = Material("kw4core", "#dcdad6", roughness=0.70)   # never seen

TAU = math.pi * 2.0


def bx(m, mat, x0, x1, y0, y1, z0, z1):
    if x1 - x0 <= 0 or y1 - y0 <= 0 or z1 - z0 <= 0:
        return
    m.add(box(x1 - x0, y1 - y0, z1 - z0), mat,
          at=((x0 + x1) / 2.0, y0, (z0 + z1) / 2.0))


def quad(m, mat, p, cols=None):
    m.add(Part(list(p), [(0, 1, 2), (0, 2, 3)], colors=cols), mat)


def _noise(seed):
    rnd = random.Random(seed)
    tbl = [rnd.random() for _ in range(4096)]

    def n(u, v):
        """Three octaves of value noise.  The third octave is the point: sd is
        scale-blind, and it was fine-scale gradient (mean |d1|) the critics
        actually read as 'plastic'."""
        out = 0.0
        for oct_, amp in ((6.0, 0.50), (17.0, 0.32), (47.0, 0.18)):
            fu, fv = u * oct_, v * oct_ * 0.45
            iu, iv = int(fu), int(fv)
            tu, tv = fu - iu, fv - iv
            tu = tu * tu * (3 - 2 * tu)
            tv = tv * tv * (3 - 2 * tv)

            def g(a, b):
                return tbl[(a * 131 + b * 977 + 17) % 4096]
            v00, v10 = g(iu, iv), g(iu + 1, iv)
            v01, v11 = g(iu, iv + 1), g(iu + 1, iv + 1)
            out += amp * ((v00 * (1 - tu) + v10 * tu) * (1 - tv)
                          + (v01 * (1 - tu) + v11 * tu) * tv)
        return out - 0.5
    return n


NF = _noise(1717)
NC = _noise(90210)


def _grid(m, mat, nu, nv, pt, tone, flip=False):
    """A one-sided quad grid.  `pt(u, v) -> (x, y, z)`, `tone(u, v) -> 0..1`.

    smooth=True is a SIZE decision, not a shading one: the grid is planar, so
    averaged normals equal flat ones, but flat shading makes the exporter split
    every triangle into its own three vertices.
    """
    verts, cols = [], []
    for iv in range(nv + 1):
        for iu in range(nu + 1):
            u, v = iu / nu, iv / nv
            verts.append(pt(u, v))
            c = tone(u, v)
            cols.append(c if isinstance(c, tuple) else (c, c, c))
    tris = []
    for iv in range(nv):
        for iu in range(nu):
            a = iv * (nu + 1) + iu
            b, c, d = a + 1, a + nu + 2, a + nu + 1
            tris += [(a, c, b), (a, d, c)] if flip else [(a, b, c), (a, c, d)]
    m.add(Part(verts, tris, smooth=True, colors=cols), mat)


# --------------------------------------------------------------- tone fields
FACE_Y0, FACE_Y1 = BB_H, BODY_H
FACE_H = FACE_Y1 - FACE_Y0
REVEAL = 0.055 / FACE_H          # the baked shade under the cap's overhang
FOOT = 0.075 / FACE_H            # the line the skirting's own top edge throws


def face_tone(a_n, a_s, v_lo, v_hi, noise, amp=0.030, reveal=0.78):
    """One painted face.  u runs NORTH -> SOUTH, v runs skirting -> cap.

    The along-the-run ramp is the biggest single number in this file and it is
    measured, not styled: the same face meters 1.25x the room's east wall at
    its north end and 0.97x at its south end in
    `hallway_looking_towards_stairs.jpg`.  Round 1 shipped it flat and all four
    round-2 critics wrote down 'no light falloff'.
    """
    def t(u, v):
        c = a_n + (a_s - a_n) * u
        c *= v_lo + (v_hi - v_lo) * v
        if v > 1.0 - REVEAL:
            k = (v - (1.0 - REVEAL)) / REVEAL
            c *= 1.0 - (1.0 - reveal) * (k ** 0.65)
        if v < FOOT:
            c *= 1.0 - 0.075 * (1.0 - v / FOOT) ** 1.5
        c *= 1.0 + amp * noise(u, v)
        return max(0.02, min(1.0, c))
    return t


def build():
    m = Model()

    # ---------------------------------------------------------------- bodies
    # Inset 0.006 so the vertex-toned skins own every face you can see; the
    # core only stops you looking through the wall.
    bx(m, CORE, XW + 0.006, XE - 0.006, 0.0, BODY_H, ZN + 0.006, Z1)
    bx(m, CORE, XE - 0.006, XL - 0.006, 0.0, BODY_H, ZN + 0.006, ZL - 0.006)

    # ----------------------------------------------------- the painted faces
    # hall face (-x), the long run.  north -> south = z ZN -> Z1
    hall = face_tone(0.900, 0.720, 0.920, 1.020, NF)
    _grid(m, FACE, 68, 14,
          lambda u, v: (XW, FACE_Y0 + v * FACE_H, ZN + u * (Z1 - ZN)), hall)

    # well face (+x).  Seen only from `p_down`, where it is the largest single
    # surface in the frame; it takes a gentler ramp and a stronger vertical one
    # because the light in the shaft comes from the 2F ceiling above it.
    well = face_tone(0.700, 0.620, 0.880, 1.010, NF, amp=0.034)
    _grid(m, FACE, 68, 14,
          lambda u, v: (XE, FACE_Y0 + v * FACE_H, ZL + u * (Z1 - ZL)), well,
          flip=True)

    # return leg: north face (-z) and its east end (+x), both seen from the
    # hall; south face (+z) faces the well and is never in frame.
    legn = face_tone(0.880, 0.840, 0.920, 1.020, NF)
    _grid(m, FACE, 20, 12,
          lambda u, v: (XW + u * (XL - XW), FACE_Y0 + v * FACE_H, ZN), legn,
          flip=True)
    lege = face_tone(0.760, 0.740, 0.910, 1.010, NF)
    _grid(m, FACE, 4, 12,
          lambda u, v: (XL, FACE_Y0 + v * FACE_H, ZN + u * (ZL - ZN)), lege)
    bx(m, CORE, XE, XL, 0.0, BODY_H, ZL - 0.006, ZL)

    # ------------------------------------------------------------- the cove
    # A two-facet cove tucked under the cap: the upper facet turns up toward
    # the ceiling and stays bright, the lower one turns down and goes dark, so
    # the pair reads as a moulding rather than as another white box.  This is
    # the "small step" visible at the near end in
    # `hallway_with_white_runner_rug.jpg` at 8x.
    def cove(pa, pb, nx, nz):
        (xa, za), (xb, zb) = pa, pb
        ox, oz = nx * COVE_P, nz * COVE_P
        ym = COVE_Y + COVE_H * 0.55
        for (y0, y1, o0, o1, tone) in (
                (COVE_Y, ym, 0.0, 0.78, (0.60, 0.72)),
                (ym, CAP_Y, 0.78, 1.0, (0.88, 1.02))):
            v = [(xa + ox * o0, y0, za + oz * o0),
                 (xb + ox * o0, y0, zb + oz * o0),
                 (xb + ox * o1, y1, zb + oz * o1),
                 (xa + ox * o1, y1, za + oz * o1)]
            c0, c1 = tone
            cols = [(c0, c0, c0), (c0, c0, c0), (c1, c1, c1), (c1, c1, c1)]
            quad(m, COVEM, v, cols)

    cove((XW, Z1), (XW, ZN), -1, 0)                 # hall side
    cove((XW, ZN), (XL, ZN), 0, -1)                 # leg north
    cove((XL, ZN), (XL, ZL), 1, 0)                  # leg east end
    cove((XE, ZL), (XE, Z1), 1, 0)                  # well side

    # --------------------------------------------------------------- the cap
    c0, c1 = XW - CAP_O, XE + CAP_O          # hall / well nose lines
    n0, n1 = ZN - CAP_O, ZL + CAP_O          # leg north / south nose lines
    e1 = XL + CAP_O                          # leg east nose line

    # solid.  Two boxes whose union is the L.  Their top is held 0.006 BELOW
    # the finished top and their underside 0.004 above the finished soffit:
    # every toned skin below sits on the real plane, and a skin coplanar with a
    # box face z-fights into a dotted line (that stipple is visible along the
    # underside of the round-1 cap in shots/noskin_p_runner.png).
    bx(m, CAPM, c0, c1, CAP_Y + 0.004, TOP - 0.006, n0, Z1)
    bx(m, CAPM, c1, e1, CAP_Y + 0.004, TOP - 0.006, n0, n1)

    # soffit of the overhang -- one dark down-facing quad per side, running
    # from the nose line back to where the cove takes over.
    def soffit(x0, x1, z0, z1):
        quad(m, SOF, [(x0, CAP_Y, z0), (x1, CAP_Y, z0),
                      (x1, CAP_Y, z1), (x0, CAP_Y, z1)])

    soffit(c0, XW - COVE_P, n0, Z1)                  # hall
    soffit(c0, e1, n0, ZN - COVE_P)                  # leg north
    soffit(XL + COVE_P, e1, ZN - COVE_P, n1)         # leg east
    soffit(c1, e1, ZL + COVE_P, n1)                  # leg south
    soffit(XE + COVE_P, c1, n1, Z1)                  # well

    # cap TOP plane, inset by the arris on every free edge, vertex-toned.
    captone = lambda a, b: (lambda u, v: max(0.02, min(1.0,
        (a + (b - a) * u) * (0.995 + 0.010 * v) * (1.0 + 0.030 * NC(u, v)))))
    _grid(m, CAPM, 68, 3,
          lambda u, v: (c0 + ARR + v * (c1 - c0 - 2 * ARR), TOP,
                        n0 + ARR + u * (Z1 - n0 - ARR)),
          captone(0.735, 0.660))
    _grid(m, CAPM, 14, 3,
          lambda u, v: (c1 + u * (e1 - ARR - c1), TOP,
                        n0 + ARR + v * (n1 - n0 - 2 * ARR)),
          captone(0.730, 0.720))

    # the eased arris: TWO narrow facets, not one chamfer -- a single flat
    # chamfer renders as a constant fill and reads as a bevel, two facets give
    # the graded specular streak the photograph has at 238-241 directly above
    # the reveal.
    def arris(pa, pb, nx, nz):
        (xa, za), (xb, zb) = pa, pb
        for k0, k1, t0, t1 in ((0.0, 0.5, 1.00, 0.97), (0.5, 1.0, 0.97, 0.86)):
            oy0, oy1 = k0 * ARR, k1 * ARR
            ox0, oz0 = nx * (ARR - oy0), nz * (ARR - oy0)
            ox1, oz1 = nx * (ARR - oy1), nz * (ARR - oy1)
            v = [(xa - ox0, TOP - oy0, za - oz0), (xb - ox0, TOP - oy0, zb - oz0),
                 (xb - ox1, TOP - oy1, zb - oz1), (xa - ox1, TOP - oy1, za - oz1)]
            cols = [(t0, t0, t0), (t0, t0, t0), (t1, t1, t1), (t1, t1, t1)]
            quad(m, ARRM, v, cols)

    arris((c0, Z1), (c0, n0), -1, 0)
    arris((c0, n0), (e1, n0), 0, -1)
    arris((e1, n0), (e1, n1), 1, 0)
    arris((e1, n1), (c1, n1), 0, 1)
    arris((c1, n1), (c1, Z1), 1, 0)

    # the nose: a vertical RAMP, bright at the arris and falling into the
    # reveal.  Round 1 had this as one flat fill 1 level off the wall face,
    # which is exactly why one critic said the cap had no profile at all.
    NOSE_Y0, NOSE_Y1 = CAP_Y, TOP - ARR
    nose = lambda a: (lambda u, v: max(0.02, min(1.0,
        a * (0.760 + 0.300 * v) * (1.0 + 0.022 * NC(u * 3.1, v)))))

    def nosegrid(pa, pb, nu, tone, nx, nz, flip=False):
        (xa, za), (xb, zb) = pa, pb
        ex, ez = nx * 0.002, nz * 0.002       # stand off the solid, no z-fight
        _grid(m, CAPM, nu, 3,
              lambda u, v: (xa + (xb - xa) * u + ex,
                            NOSE_Y0 + v * (NOSE_Y1 - NOSE_Y0),
                            za + (zb - za) * u + ez), tone, flip=flip)

    nosegrid((c0, n0), (c0, Z1), 60, nose(0.985), -1, 0)              # hall
    nosegrid((c0, n0), (e1, n0), 16, nose(0.940), 0, -1, flip=True)   # leg N
    nosegrid((e1, n0), (e1, n1), 4, nose(0.860), 1, 0)                # leg E
    nosegrid((c1, n1), (c1, Z1), 56, nose(0.700), 1, 0, flip=True)    # well

    # ---------------------------------------------------------- the skirting
    # In the photograph the skirting is the BRIGHTEST white below the cap
    # (cove top 199-200 against a 145 face) and it has a shadowed toe.  Round 1
    # rendered it 5 levels DARKER than the face.
    def skirt(x0, x1, z0, z1, nx, nz):
        """One run of skirting.  (x0,x1,z0,z1) is the SOLID it occupies -- it
        already stands `BB_T` proud of the wall face; (nx,nz) says which way it
        faces so the toned outer skin and the cove cap go on the right side."""
        bx(m, CORE, x0, x1, 0.0, BB_H - BB_CH, z0, z1)
        # outer face, 0.002 proud: bright at the top (photo 188-196 just under
        # the cove) and falling to a shadowed toe (145) at the plank.
        if nx:
            fx = (x0 if nx < 0 else x1) + nx * 0.002
            pa, pb = (fx, z0), (fx, z1)
        else:
            fz = (z0 if nz < 0 else z1) + nz * 0.002
            pa, pb = (x0, fz), (x1, fz)
        (ax, az), (bx_, bz) = pa, pb

        def btone(u, v):
            # 0.72 at the toe -> 1.00 just under the cove, and a hard dark band
            # in the bottom 0.05 ft: the photo's skirting runs 196 down to 145
            # with the last two pixels at 103-119 before the floor contact.
            c = 0.720 + 0.280 * v
            if v < 0.10:
                c *= 0.62 + 0.38 * (v / 0.10)
            return c * (1.0 + 0.020 * NF(u * 2.0, v))

        _grid(m, BBM, 2, 9,
              lambda u, v: (ax + (bx_ - ax) * u, v * (BB_H - BB_CH),
                            az + (bz - az) * u), btone,
              flip=(nx > 0 or nz > 0))
        # a real cove cap: a facet turned UP toward the ceiling, so it catches
        # light the vertical body cannot.  This is the bright ribbon the base_a
        # critic asked for, and the reason the skirting out-reads the face.
        if nx < 0:
            p = [(x0, BB_H - BB_CH, z0), (x0, BB_H - BB_CH, z1),
                 (x1, BB_H, z1), (x1, BB_H, z0)]
        elif nx > 0:
            p = [(x1, BB_H - BB_CH, z1), (x1, BB_H - BB_CH, z0),
                 (x0, BB_H, z0), (x0, BB_H, z1)]
        elif nz < 0:
            p = [(x1, BB_H - BB_CH, z0), (x0, BB_H - BB_CH, z0),
                 (x0, BB_H, z1), (x1, BB_H, z1)]
        else:
            p = [(x0, BB_H - BB_CH, z1), (x1, BB_H - BB_CH, z1),
                 (x1, BB_H, z0), (x0, BB_H, z0)]
        quad(m, BBC, p, [(1.0, 1.0, 1.0)] * 4)

    skirt(XW - BB_T, XW, ZN - BB_T, Z1, -1, 0)          # hall run
    skirt(XW - BB_T, XL + BB_T, ZN - BB_T, ZN, 0, -1)   # leg north, mitred round
    skirt(XL, XL + BB_T, ZN - BB_T, ZL, 1, 0)           # leg east end

    # ------------------------------------------------ baked floor contact
    # The app renders no shadow maps for generated geometry.  ROOM-BRIEF's four
    # rules: y = 0.05 clears the slab's polygonOffset, alpha not an opaque mix,
    # one coplanar layer of non-overlapping strips, and the ramp must run
    # OUTSIDE the footprint.  Photo: floor 86-94 at the contact against 123 in
    # the open, i.e. ~28% at the edge easing out over ~25 px.
    STEPS, W, S = 11, 0.85, 0.30
    a = round(1.0 - (1.0 - S) ** (1.0 / STEPS), 4)
    shd = Material("kw4shd", "#221f1a", roughness=0.98, opacity=a)
    for i in range(STEPS):
        w = W * (1.0 - (i / STEPS) ** (1.0 / 1.15))
        if w <= 0.006:
            continue
        y = 0.050 + i * 0.0011
        xa, za = XW - BB_T, ZN - BB_T
        # along the hall face
        quad(m, shd, [(xa, y, za), (xa, y, Z1),
                      (xa - w, y, Z1), (xa - w, y, za)])
        # along the leg's north face, out to its east end
        xb = XL + BB_T
        quad(m, shd, [(xa - w, y, za), (xb + w, y, za),
                      (xb + w, y, za - w), (xa - w, y, za - w)])
        # off the east end of the leg
        quad(m, shd, [(xb, y, za), (xb + w, y, za),
                      (xb + w, y, ZL), (xb, y, ZL)])
    return m


if __name__ == "__main__":
    m = build()
    path = os.path.join(HERE, "glb", "hall2f_knee_wall.glb")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    m.save(path)
    lo, hi = m.bounds()
    pos = ((lo[0] + hi[0]) / 2.0, lo[1], (lo[2] + hi[2]) / 2.0)
    res = place(NAME, path, ROOM, pos=pos, rot_y_deg=0.0, scale=1.0)
    kb = os.path.getsize(path) / 1024.0
    print(f"  {NAME:22s} local x {lo[0]:.3f}..{hi[0]:.3f}  y {lo[1]:.3f}..{hi[1]:.3f}"
          f"  z {lo[2]:.3f}..{hi[2]:.3f}")
    print(f"  pos=({pos[0]:.3f},{pos[1]:.3f},{pos[2]:.3f})  {kb:.1f} KB  {res['action']}")
