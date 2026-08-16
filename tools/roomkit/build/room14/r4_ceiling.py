"""Vaulted ceiling for the re-traced room — round 4.

See r4_room.py for how the ridge was re-derived (apex over the bed at local
x 10.50, peak 14.6, west 32.2 deg / east 33.4 deg).  Coverage follows the real
L polygon: the slopes run the full depth over the vestibule's x band and stop at
the main room's south wall elsewhere, and six vertical infills close the gap
between the 8 ft wall tops and the slopes.

TONE IS RE-METERED, NOT INHERITED.  daylight.js raised the hemisphere ground and
the daytime IBL after round 3, so every emissive number in layout.json now
overshoots.  This script takes the lit term as a measured argument:

    emissive_strength = radiance_for_byte(target_byte) - LIT

LIT is what a downward-facing #f3f3f4 plane collects in this scene with no
emissive at all; measure it with --probe (builds the same ceiling with zero
emissive) and pass it back in with --lit.

Target bytes come from the photo, scaled to the render's own wall.  Sampled off
`Master bedroom.jpg`: north wall 174.5, ceiling west slope 182..188, near the
ridge 168, east slope 176, east eave 161 -- i.e. the ceiling runs 0.92..1.08 of
the wall and is BRIGHTEST at the eaves, darkest at the ridge, on both sides.
"""
import math
import sys
import os

sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from roomkit.glb import Model, Material, Part, cylinder
from tone import radiance_for_byte, lin_to_srgb, srgb_to_lin, aces
from r4_room import (W_ROOM, D_ROOM, MAIN_Z, LEG_X0, LEG_X1,
                     RIDGE_X, PEAK, EAVE, RISE, h)

OUT = sys.argv[1] if len(sys.argv) > 1 else "ceiling.glb"
LIT = 0.095                       # MEASURED, not assumed: the round-4 render
                                  # put band 5 (built for byte 215) at 219 and
                                  # band 2 (232) at 233, which solves the
                                  # downward-plane light term at 0.095 -- a
                                  # downward face collects almost nothing here.
LIT_VERT = 2.77                   # what an albedo-1.0 VERTICAL face of an
                                  # OBJECT collects here.  Note it is NOT the
                                  # 1.63 a room WALL of the same albedo and
                                  # orientation collects -- model materials pick
                                  # up ~1.7x the wall's light in this scene, so
                                  # a gable solved on the wall's number came out
                                  # 238 against a 225 wall and left a visible
                                  # seam across the room.  Measured, not derived.
WALL = 224.0                      # the render's own north wall, re-metered
for i, a in enumerate(sys.argv):
    if a == "--lit":
        LIT = float(sys.argv[i + 1])
    if a == "--wall":
        WALL = float(sys.argv[i + 1])
PROBE = "--probe" in sys.argv

CEIL_BASE = "#f3f3f4"
EMIS = "#fffefc"

# photo ratio (ceiling / north wall) eave -> ridge, per side
W_RATIO = [1.075, 1.055, 1.035, 1.010, 0.985, 0.962]     # west: eave -> ridge
E_RATIO = [0.962, 0.985, 1.005, 1.020, 1.010]            # east: ridge -> eave


def strength(ratio):
    if PROBE:
        return 0.0
    return max(0.0, radiance_for_byte(min(254.0, WALL * ratio)) - LIT)


def byte_of(s):
    r = s + LIT
    return round(255 * lin_to_srgb(aces((r, r, r))[0]))


MW = [Material("ceil_w%d" % i, CEIL_BASE, roughness=0.96, emissive=EMIS,
               emissive_strength=max(1e-4, strength(r)), double_sided=False)
      for i, r in enumerate(W_RATIO)]
ME = [Material("ceil_e%d" % i, CEIL_BASE, roughness=0.96, emissive=EMIS,
               emissive_strength=max(1e-4, strength(r)), double_sided=False)
      for i, r in enumerate(E_RATIO)]
# The gable infills are VERTICAL continuations of the wall below them, so they
# must render at exactly the wall's byte and they collect the wall's own light:
# pure albedo, no emissive.  (#ececeb + 0.05 emissive metered 238 against a 239
# wall in the first round-4 render, which is how LIT_VERT was solved.)
# Fitted from two real renders of this very gable (tone.py's analytic inverse
# does not predict the object path): linear albedo 0.5089 -> byte 238 and
# 0.3006 -> byte 205, log-linear between.
_L0, _B0, _L1, _B1 = 0.3006, 205.0, 0.5089, 238.0
_slope = (_B1 - _B0) / (math.log(_L1) - math.log(_L0))
_g = min(1.0, math.exp(math.log(_L0) + (WALL + 5.0 - _B0) / _slope))
_gb = max(0, min(255, round(255 * lin_to_srgb(_g))))
GABLE = Material("gable", "#%02x%02x%02x" % (_gb, _gb, _gb), roughness=0.95,
                 double_sided=False)

m = Model()


def z_span(x):
    """how deep the ceiling runs at local x — the room is an L."""
    return D_ROOM if LEG_X0 - 1e-6 <= x <= LEG_X1 + 1e-6 else MAIN_Z


def quad4(a, b, c, d):
    return Part([a, b, c, d], [(0, 1, 2), (0, 2, 3)])


def slope(x0, x1, z0, z1, mat):
    if x1 - x0 < 1e-6 or z1 - z0 < 1e-6:
        return
    a = (x0, h(x0), z0)
    b = (x1, h(x1), z0)
    c = (x1, h(x1), z1)
    d = (x0, h(x0), z1)
    m.add(quad4(a, b, c, d), mat)      # wound so the normal points DOWN


def band(x0, x1, mat):
    """one x band of slope, split at the vestibule's x edges so the L is exact."""
    cuts = sorted({x0, x1} | {c for c in (LEG_X0, LEG_X1) if x0 < c < x1})
    for i in range(len(cuts) - 1):
        a, b = cuts[i], cuts[i + 1]
        slope(a, b, 0.0, z_span((a + b) / 2), mat)


for i, mat in enumerate(MW):
    band(RIDGE_X * i / len(MW), RIDGE_X * (i + 1) / len(MW), mat)
for i, mat in enumerate(ME):
    span = W_ROOM - RIDGE_X
    band(RIDGE_X + span * i / len(ME), RIDGE_X + span * (i + 1) / len(ME), mat)

# ---- vertical infills between the 8 ft wall tops and the slopes ------------
SK = EAVE - 0.12          # skirt down behind the wall top so there is no seam


def _fan(v, axis, face):
    """Fan a convex polygon and FLIP it if the normal points the wrong way.
    Round 3 shipped a north gable wound backwards once and you saw sky through
    it, so the winding is checked rather than assumed."""
    n = len(v)
    tris = [(0, i, i + 1) for i in range(1, n - 1)]
    a, b, c = v[0], v[1], v[2]
    u = [b[i] - a[i] for i in range(3)]
    w = [c[i] - a[i] for i in range(3)]
    nz = (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2],
          u[0] * w[1] - u[1] * w[0])
    if nz[axis] * face < 0:
        tris = [(t[0], t[2], t[1]) for t in tris]
    return Part(v, tris)


def zgable(pts, z, face):
    """pts [(x, y)] in the z-plane; face=+1 -> normal points +z."""
    m.add(_fan([(p[0], p[1], z) for p in pts], 2, face), GABLE)


def xgable(pts, x, face):
    """pts [(z, y)] in the x-plane; face=+1 -> normal points +x."""
    m.add(_fan([(x, p[1], p[0]) for p in pts], 0, face), GABLE)


# north wall — the full gable, apex over the bed
zgable([(0, SK), (0, EAVE), (RIDGE_X, PEAK), (W_ROOM, EAVE), (W_ROOM, SK)],
       0.0, +1)
# main south wall, west of the vestibule (x 0..7.86)
zgable([(0, SK), (0, EAVE), (LEG_X0, h(LEG_X0)), (LEG_X0, SK)], MAIN_Z, -1)
# main south wall, east of the vestibule (x 15.58..20.51)
zgable([(LEG_X1, SK), (LEG_X1, h(LEG_X1)), (W_ROOM, EAVE), (W_ROOM, SK)],
       MAIN_Z, -1)
# vestibule south wall (x 7.86..15.58) — crosses the ridge
zgable([(LEG_X0, SK), (LEG_X0, h(LEG_X0)), (RIDGE_X, PEAK),
        (LEG_X1, h(LEG_X1)), (LEG_X1, SK)], D_ROOM, -1)
# vestibule side walls — constant height, so plain rectangles
xgable([(MAIN_Z, SK), (D_ROOM, SK), (D_ROOM, h(LEG_X0)), (MAIN_Z, h(LEG_X0))],
       LEG_X0, +1)
xgable([(MAIN_Z, SK), (D_ROOM, SK), (D_ROOM, h(LEG_X1)), (MAIN_Z, h(LEG_X1))],
       LEG_X1, -1)

# ---- recessed cans, lying in the slope plane ------------------------------
A_W = math.atan2(RISE, RIDGE_X)
A_E = math.atan2(RISE, W_ROOM - RIDGE_X)
CANS = [(3.4, 2.6), (3.0, 9.8), (14.2, 2.6), (14.8, 9.8), (17.9, 6.2),
        (11.6, 16.4)]
made = {}
for (cx, cz) in CANS:
    if cx <= RIDGE_X:
        i = min(len(MW) - 1, int(cx / (RIDGE_X / len(MW))))
        s, rot = MW[i].emissive_strength, A_W
    else:
        i = min(len(ME) - 1,
                int((cx - RIDGE_X) / ((W_ROOM - RIDGE_X) / len(ME))))
        s, rot = ME[i].emissive_strength, -A_E
    b = byte_of(s)
    if b not in made:
        rim = Material("trim%d" % b, "#d8d6d2", roughness=0.96, emissive=EMIS,
                       emissive_strength=s, double_sided=False)
        ap = Material("can%d" % b, "#fbfbfa", roughness=0.96, emissive=EMIS,
                      emissive_strength=max(1e-4,
                                            radiance_for_byte(min(254, b + 12)) - LIT),
                      double_sided=False)
        made[b] = (rim, ap)
    rim, ap = made[b]
    y = h(cx)
    m.add(cylinder(0.27, 0.02, seg=20, anchor="center"), rim,
          at=(cx, y - 0.012, cz), rot_z=rot)
    m.add(cylinder(0.21, 0.02, seg=20, anchor="center"), ap,
          at=(cx, y - 0.030, cz), rot_z=rot)

m.save(OUT)
lo, hi = m.bounds()
print("bounds", tuple(round(v, 2) for v in lo), tuple(round(v, 2) for v in hi))
print("h(0)=%.2f h(7.86)=%.2f h(10.5)=%.2f h(15.58)=%.2f h(20.51)=%.2f"
      % (h(0), h(LEG_X0), h(RIDGE_X), h(LEG_X1), h(W_ROOM)))
print("west %.1f deg (%.2f:12), east %.1f deg (%.2f:12)"
      % (math.degrees(A_W), 12 * RISE / RIDGE_X,
         math.degrees(A_E), 12 * RISE / (W_ROOM - RIDGE_X)))
print("lit=%.4f wall=%.0f  west bytes %s  east bytes %s"
      % (LIT, WALL, [byte_of(mm.emissive_strength) for mm in MW],
         [byte_of(mm.emissive_strength) for mm in ME]))
