"""Room 17 -- `Hall2F Knee Wall`, rebuilt from the photographs (round V3).

Owns exactly ONE piece.  Idempotent by name, so re-running replaces it in
place.  Nothing else in room 17 is touched.

WHY A REBUILD
-------------
The full-height partition that used to stand on room 17's edge 1 is gone
(openings 143 / 144 are full-span, so `buildRoom` skips the wall outright).
This GLB is now the only thing standing on that line -- local x = 7.61,
z 6.81 .. 16.89 -- so it has to carry the whole boundary between the walking
strip and the stairwell.  The old piece was authored for a shorter footprint,
stopped 0.14 ft short of the south wall, carried a very thick cap and ended in
a stepped newel notch that the photographs do not have.

WHAT THE PHOTOGRAPHS ACTUALLY SHOW  (docs/v2 Hallway-jpg/)
----------------------------------------------------------
`hallway_with_white_runner_rug.jpg` at 6x on the near end is the clearest
section drawing of the whole set.  Top to bottom the assembly is:

    flat cap board, square nosed, overhanging BOTH faces by about an inch
    a narrower sub-band under it, overhanging about half an inch
    a shadow reveal where the overhang shades the wall face
    plain painted wall face
    the room's own tall baseboard, wrapping the open end as well

and the open (north, head-of-the-flight) end is simply SQUARE: the wall stops,
the cap and sub-band return over it with their full overhang, the baseboard
wraps the corner.  There is no pilaster, no step up, no notch.

HEIGHT -- this is a deliberate departure from the round brief, which said
3.2-3.6 ft.  Measured off the photograph instead:

  * `hallway_with_white_runner_rug.jpg`, at the FAR end of the run the knee
    wall and the bathroom door are at the same depth (both on z = 16.89), so
    one image scale serves both and camera tilt cancels.
  * bath door leaf: top y = 117, floor at that wall y = 255  ->  138 px = 80 in
  * knee wall cap top at the far end y = 196.7, same floor line y = 255
    ->  58.3 px  ->  58.3 / 138 * 80 = 33.8 in
  * cross-check on the south wall's own baseboard at x = 270: 8 px = 4.6 in,
    which is the same scale.

So the real wall is 34-36 in to the top of the cap -- a code-minimum 36 in
guard, not a 40 in one.  Built here at 3.16 ft = 37.9 in, which is a compromise
with the existing stair rail; see the TOP comment below.  Reported.

TONE was solved by rendering the piece with each part keyed pure R/G/B
(`kwprobe.py mask`) and metering the real render through those masks, against
the same measurement taken off the photographs (`phmeter.py`).  Every number in
the report comes from those two scripts, not from a hand-drawn sample box.

ENGINE NOTES
------------
`roomkit.glb` has no image-texture API and the app renders no shadow maps for
generated geometry, so: the two big faces and the cap top are vertex-coloured
grids (COLOR_0 multiplies baseColor, 4 bytes a vertex) carrying the vertical
light falloff, the along-the-run gradient, the reveal shade under the cap nose
and a fine mottle -- NOT per-cell material buckets, which is what blows the KB
budget.  The floor contact is a baked alpha ramp of nested strips at y = 0.05
(the slab draws with polygonOffsetFactor -1, so anything at 0.005-0.018
z-fights and loses).
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
# black brackets off it (stairs.py `_bracket`, wall pad at authored x 3.952,
# placed with a +3.80 shift).  Moving this face would leave them in mid air.
XW = 7.33          # hall face
XE = 7.75          # well face  (0.42 ft = 5.0 in wall, framed + board both sides)
Z0 = 6.81          # open end, at the head of the flight
Z1 = 16.92         # dies 0.03 into the south wall's mass (it starts at 16.89)

BB_H = 0.52        # the room's own baseboard height, so the two register
BB_T = 0.055       # how proud of the wall face it stands

CAP_T = 0.125      # cap board thickness      (1.5 in)
BAND_T = 0.085     # sub-band thickness       (1.0 in)
CAP_O = 0.083      # cap overhang each face   (1.0 in)
BAND_O = 0.042     # sub-band overhang        (0.5 in)
TOP = 3.16         # top of the cap           (37.9 in -- see the docstring)
# The photograph solves to 34-36 in.  Built 2 in taller for one hard reason:
# `Hall2F Stair Rail`'s level return at the head of the flight occupies
# y 2.97..3.15 (stairs.py, `bx(m, BLK, 3.90, RAILX + 0.10, y_hi +/- 0.090,
# 8.02, 8.28)`).  At a 36 in cap that black block breaks THROUGH the cap board
# and sits on it as a blob -- shot and confirmed.  3.16 buries it while staying
# at the bottom of the round brief's 3.2-3.6 ft band.  If the rail is ever
# lowered, drop this to 3.02 and the wall matches the photograph outright.

BODY_H = TOP - CAP_T - BAND_T        # 2.840
BAND_Y = BODY_H                      # 2.840 .. 2.925
CAP_Y = BODY_H + BAND_T              # 2.925 .. 3.050

CH = 0.018         # eased arris on the cap's two long top edges -- this is the
                   # crisp line running the length of the cap in
                   # `staircase_looking_down.jpg`, and it is the only reason
                   # that photo's cap does not read as a plain slab.

# ----------------------------------------------------------------- materials
# One white per roughness family; every value difference below is carried by
# vertex colour, so the whole wall is a handful of primitives.
WM = Material("kw3m", "#ffffff", roughness=0.62)     # matte, vertex-coloured
WG = Material("kw3g", "#ffffff", roughness=0.52)     # cap, vertex-coloured
CORE = Material("kw3core", "#e6e4df", roughness=0.62)
CAPF = Material("kw3capf", "#e9e6e1", roughness=0.52)   # cap nose, hall side
BBCAP = Material("kw3bbc", "#eeece8", roughness=0.62)   # skirting top bevel
CAPW = Material("kw3capw", "#cfccc7", roughness=0.52)   # cap nose, well side
BANDF = Material("kw3bnf", "#efece7", roughness=0.56)   # sub-band, hall side
BANDW = Material("kw3bnw", "#dad7d1", roughness=0.56)   # sub-band, well side
BBM = Material("kw3bb", "#fbfaf7", roughness=0.54)      # skirting reads BRIGHTER
BBT = Material("kw3bbt", "#c9c5be", roughness=0.74)     # its shadowed toe
ENDM = Material("kw3end", "#ffffff", roughness=0.40)    # the square end face
UND = Material("kw3und", "#b6b2ab", roughness=0.74)     # soffit of the overhangs


def bx(m, mat, x0, x1, y0, y1, z0, z1):
    if x1 - x0 <= 0 or y1 - y0 <= 0 or z1 - z0 <= 0:
        return
    m.add(box(x1 - x0, y1 - y0, z1 - z0), mat,
          at=((x0 + x1) / 2.0, y0, (z0 + z1) / 2.0))


def soffit(m, mat, x0, x1, y, z0, z1):
    """A single quad facing DOWN -- the shaded underside of an overhang."""
    if x1 - x0 <= 0 or z1 - z0 <= 0:
        return
    m.add(Part([(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)],
               [(0, 1, 2), (0, 2, 3)]), mat)


# --------------------------------------------------------- vertex-tone grids
def _grid(m, mat, nu, nv, pt, tone, flip=False):
    """A one-sided quad grid.  `pt(iu, iv) -> (x, y, z)`, `tone(u, v) -> 0..1`.

    Wound so the face points the way `pt`'s (u, v) frame implies; `flip`
    reverses it.  A black surface in a render means this got it backwards.
    """
    verts, cols = [], []
    for iv in range(nv + 1):
        for iu in range(nu + 1):
            verts.append(pt(iu / nu, iv / nv))
            c = tone(iu / nu, iv / nv)
            cols.append((c, c, c) if not isinstance(c, tuple) else c)
    tris = []
    for iv in range(nv):
        for iu in range(nu):
            a = iv * (nu + 1) + iu
            b, c, d = a + 1, a + nu + 2, a + nu + 1
            if flip:
                tris += [(a, c, b), (a, d, c)]
            else:
                tris += [(a, b, c), (a, c, d)]
    # smooth=True is a SIZE decision, not a shading one: the grid is planar, so
    # averaged normals are identical to flat ones, but flat shading makes the
    # exporter split every triangle into its own three vertices -- 3036 verts a
    # face instead of 564, which is 85 KB a face instead of 16.
    m.add(Part(verts, tris, smooth=True, colors=cols), mat)


def _noise(seed):
    rnd = random.Random(seed)
    tbl = [rnd.random() for _ in range(2048)]

    def n(u, v):
        """Two octaves of value noise, bilinear -- a soft drywall mottle."""
        out = 0.0
        for oct_, amp in ((7.0, 0.62), (19.0, 0.38)):
            fu, fv = u * oct_, v * oct_ * 0.55
            iu, iv = int(fu), int(fv)
            tu, tv = fu - iu, fv - iv
            tu = tu * tu * (3 - 2 * tu)
            tv = tv * tv * (3 - 2 * tv)

            def g(a, b):
                return tbl[(a * 131 + b * 977 + 17) % 2048]
            v00, v10 = g(iu, iv), g(iu + 1, iv)
            v01, v11 = g(iu, iv + 1), g(iu + 1, iv + 1)
            out += amp * ((v00 * (1 - tu) + v10 * tu) * (1 - tv)
                          + (v01 * (1 - tu) + v11 * tu) * tv)
        return out - 0.5
    return n


NH = _noise(1717)     # hall face
NW = _noise(4242)     # well face
NC = _noise(90210)    # cap top

RUN = Z1 - Z0
FACE_Y0, FACE_Y1 = BB_H, BODY_H          # the painted field, above the skirting
FACE_H = FACE_Y1 - FACE_Y0


def _face_tone(base, n, top_shade, foot_shade, along, vert):
    """One painted face's tone field.  v = 0 at the skirting, 1 under the cap."""
    def t(u, v):
        c = base
        c *= vert[0] + (vert[1] - vert[0]) * v            # light falls off down
        c *= along[0] + (along[1] - along[0]) * u         # and along the run
        # the reveal: the cap's nose overhangs by an inch and shades the wall
        rev = 0.09 / FACE_H
        if v > 1.0 - rev:
            k = (v - (1.0 - rev)) / rev
            c *= 1.0 - top_shade * k * k
        # and the skirting's own top edge throws a thin line onto the wall
        fut = 0.09 / FACE_H
        if v < fut:
            c *= 1.0 - foot_shade * (1.0 - v / fut) ** 1.6
        c *= 1.0 + 0.020 * n(u, v)
        return max(0.02, min(1.0, c))
    return t


def build():
    m = Model()

    # ---- the mass.  Inset 0.006 so the vertex-toned skins below own the two
    # faces you actually see; the core only stops you looking through the wall.
    bx(m, CORE, XW + 0.006, XE - 0.006, 0.0, BODY_H, Z0, Z1)

    # ---- hall face and well face, as vertex-toned skins
    # The along-the-run ramp is REAL and it is big: metered off the two hall
    # photographs the same face reads 0.888x the room's grey wall at z 9-11 and
    # 1.201x at z 13-16.  A flat albedo cannot be right in both, and round 2's
    # critics named "no light falloff, walls near-uniform" in all four reports.
    hall = _face_tone(0.990, NH, top_shade=0.15, foot_shade=0.07,
                      along=(0.880, 1.040), vert=(0.935, 1.015))
    well = _face_tone(0.648, NW, top_shade=0.24, foot_shade=0.05,
                      along=(1.010, 0.968), vert=(0.955, 1.010))
    nu, nv = 58, 14
    _grid(m, WM, nu, nv,
          lambda u, v: (XW, FACE_Y0 + v * FACE_H, Z0 + u * RUN), hall)
    _grid(m, WM, nu, nv,
          lambda u, v: (XE, FACE_Y0 + v * FACE_H, Z0 + u * RUN), well, flip=True)

    # ---- the square END at the head of the flight (faces -z, into the north
    # block).  Photograph: a plain flat face, no pilaster, no step.
    bx(m, ENDM, XW, XE, 0.0, BODY_H, Z0 - 0.006, Z0)

    # ---- sub-band: narrower than the cap, so the section steps twice
    b0, b1 = XW - BAND_O, XE + BAND_O
    bz0 = Z0 - BAND_O
    bx(m, BANDF, b0, b0 + 0.012, BAND_Y, BAND_Y + BAND_T, bz0, Z1)
    bx(m, BANDW, b1 - 0.012, b1, BAND_Y, BAND_Y + BAND_T, bz0, Z1)
    bx(m, CORE, b0 + 0.012, b1 - 0.012, BAND_Y, BAND_Y + BAND_T, bz0, Z1)
    bx(m, BANDF, b0, b1, BAND_Y, BAND_Y + BAND_T, bz0, bz0 + 0.012)  # return
    soffit(m, UND, b0, XW, BAND_Y, bz0, Z1)          # its half-inch overhangs
    soffit(m, UND, XE, b1, BAND_Y, bz0, Z1)
    soffit(m, UND, b0, b1, BAND_Y, bz0, Z0)

    # ---- cap board.  Flat, square nosed, eased arris on both long top edges.
    c0, c1 = XW - CAP_O, XE + CAP_O
    cz0 = Z0 - CAP_O
    ctop = CAP_Y + CAP_T
    bx(m, CAPF, c0, c0 + 0.014, CAP_Y, ctop - CH, cz0, Z1)          # hall nose
    bx(m, CAPW, c1 - 0.014, c1, CAP_Y, ctop - CH, cz0, Z1)          # well nose
    bx(m, CORE, c0 + 0.014, c1 - 0.014, CAP_Y, ctop - CH, cz0, Z1)
    bx(m, CAPF, c0, c1, CAP_Y, ctop, cz0, cz0 + 0.014)              # end return
    soffit(m, UND, c0, b0, CAP_Y, cz0, Z1)      # the inch of overhang, in shade
    soffit(m, UND, b1, c1, CAP_Y, cz0, Z1)
    soffit(m, UND, c0, c1, CAP_Y, cz0, bz0)

    # the two chamfers, as narrow ramps, then the top plane between them
    for xa, xb, mat in ((c0, c0 + CH, CAPF), (c1 - CH, c1, CAPW)):
        rising = (mat is CAPF)
        y_a, y_b = (ctop - CH, ctop) if rising else (ctop, ctop - CH)
        v = [(xa, y_a, cz0), (xb, y_b, cz0), (xb, y_b, Z1), (xa, y_a, Z1)]
        m.add(Part(v, [(0, 2, 1), (0, 3, 2)], smooth=False), mat)

    cap = _face_tone(0.700, NC, top_shade=0.0, foot_shade=0.0,
                     along=(0.965, 1.012), vert=(0.992, 1.000))
    _grid(m, WG, 58, 3,
          lambda u, v: (c0 + CH + v * (c1 - c0 - 2 * CH), ctop, cz0 + u * (Z1 - cz0)),
          cap)

    # ---- baseboard, both faces plus the end return.  In the photograph the
    # skirting reads BRIGHTER than the wall above it (round 2: "every white is
    # the same white") and it has a shadowed toe where it meets the floor.
    bx(m, BBM, XW - BB_T, XW, 0.0, BB_H, Z0 - BB_T, Z1)
    bx(m, BBM, XE, XE + BB_T, 0.0, BB_H, Z0 - BB_T, Z1)
    bx(m, BBM, XW - BB_T, XE + BB_T, 0.0, BB_H, Z0 - BB_T, Z0)      # end return
    bx(m, BBT, XW - BB_T - 0.004, XW - BB_T, 0.0, 0.055, Z0 - BB_T, Z1)
    bx(m, BBT, XE + BB_T, XE + BB_T + 0.004, 0.0, 0.055, Z0 - BB_T, Z1)
    bx(m, BBT, XW - BB_T, XE + BB_T, 0.0, 0.055, Z0 - BB_T - 0.004, Z0 - BB_T)
    # the small cap bevel along the top of the skirting
    bx(m, BBCAP, XW - BB_T, XW - BB_T + 0.010, BB_H - 0.030, BB_H, Z0 - BB_T, Z1)
    bx(m, BBCAP, XE + BB_T - 0.010, XE + BB_T, BB_H - 0.030, BB_H, Z0 - BB_T, Z1)

    # ---- baked floor contact.  The app renders no shadow maps for generated
    # geometry, so this is a decal: nested alpha strips whose overlap count is
    # the falloff.  ROOM-BRIEF: y = 0.05 clears the slab's polygonOffset, the
    # ramp must run OUTSIDE the footprint, exponent ~1.15, ~34% at the contact.
    STEPS, W, S = 10, 0.80, 0.27
    a = round(1.0 - (1.0 - S) ** (1.0 / STEPS), 4)
    shd = Material("kw3shd", "#26251f", roughness=0.98, opacity=a)
    xa = XW - BB_T                       # the skirting's own face
    for i in range(STEPS):
        w = W * (1.0 - (i / STEPS) ** (1.0 / 1.15))
        if w <= 0.006:
            continue
        y = 0.050 + i * 0.0012
        za, zb = Z0 - BB_T - w * 0.6, Z1
        v = [(xa, y, za), (xa, y, zb), (xa - w, y, zb), (xa - w, y, za)]
        m.add(Part(v, [(0, 2, 1), (0, 3, 2)]), shd)
        # and the little wedge off the open end, so the end reads seated too
        v2 = [(xa - w, y, za), (XE + BB_T, y, za),
              (XE + BB_T, y, za - w * 0.55), (xa - w, y, za - w * 0.55)]
        m.add(Part(v2, [(0, 1, 2), (0, 2, 3)]), shd)
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
