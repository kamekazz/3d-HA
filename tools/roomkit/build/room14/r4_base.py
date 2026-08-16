"""Baseboards for the re-traced room — round 4, and RE-METERED.

Round 2's board was authored albedo #ffffff + emissive #757575 to land 24 bytes
over a 188 wall, which is the step the photo shows LOCALLY (photo: board 174 in
shade, wall 174-197).  After the daylight.js fix the north wall renders at ~224,
so the same emissive would drive the board past 250 and clip it into a white
bar.  The step is re-solved as a RATIO instead: photo board/wall = 1.00..1.05,
so the board is aimed at 1.045 of the render's own wall and the cap a touch
brighter.  Emissive = radiance_for_byte(target) - LIT, with LIT measured the
same way as the ceiling's (probe with zero emissive, read the byte back).

The run follows the room's real L: all eight edges, boards on the interior face,
with gaps at the two south-west doors and at the vestibule->hallway passage.
"""
import math
import os
import sys

sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from roomkit.glb import Model, Material, box
from tone import radiance_for_byte, lin_to_srgb, srgb_to_lin, aces
from r4_room import POLY, edge, DOORS, PASSAGE

OUT = sys.argv[1] if len(sys.argv) > 1 else "base.glb"
LIT = 2.77                # measured: radiance an ALBEDO-1.0 vertical face of a
                          # MODEL collects on this wall.  A room wall of the
                          # same albedo/orientation only collects 1.63 -- object
                          # materials run ~1.7x hotter here -- so solving the
                          # board on the wall's number overshot it by 12 bytes.
WALL = 224.0
for i, a in enumerate(sys.argv):
    if a == "--lit":
        LIT = float(sys.argv[i + 1])
    if a == "--wall":
        WALL = float(sys.argv[i + 1])
PROBE = "--probe" in sys.argv

FACE_H = 0.400            # 4.8 in of flat face
CAP_H = 0.058             # 0.7 in cap
T = 0.070                 # board thickness off the wall
CAP_T = 0.048


# MEASURED response of an object's vertical face on this wall.  tone.py's
# analytic exposure-1.15 -> ACES inverse does NOT predict it (it says a 0.68
# linear albedo and a 0.38 one should differ by 22 bytes; the render says 22,
# but it puts them at 245 and 223, not where the inverse says).  So the curve is
# fitted from two real renders instead:
#     linear albedo 0.6795 -> byte 245     (#d6d6d6)
#     linear albedo 0.3813 -> byte 223     (#a9a9a9)
# log-linear between/around them.
FIT = ((0.3813, 223.0), (0.6795, 245.0))


def albedo(ratio):
    """sRGB hex whose render lands on `ratio` x the wall byte."""
    tgt = WALL * ratio
    (l0, b0), (l1, b1) = FIT
    slope = (b1 - b0) / (math.log(l1) - math.log(l0))
    lin = min(1.0, math.exp(math.log(l0) + (tgt - b0) / slope))
    b = max(0, min(255, round(255 * lin_to_srgb(lin))))
    return "#%02x%02x%02x" % (b, b, b)


def byte_of(hexc):
    lin = srgb_to_lin(int(hexc[1:3], 16) / 255.0)
    (l0, b0), (l1, b1) = FIT
    slope = (b1 - b0) / (math.log(l1) - math.log(l0))
    return round(b0 + slope * (math.log(max(lin, 1e-4)) - math.log(l0)))


FACE_C, CAP_C = albedo(1.031), albedo(1.067)
FACE = Material("base_face", FACE_C, roughness=0.60)
CAP = Material("base_cap", CAP_C, roughness=0.45)

# gaps per edge index: list of (offset0, offset1) along that edge
GAPS = {}
for e, off, w in DOORS:
    GAPS.setdefault(e, []).append((off, off + w))
GAPS.setdefault(PASSAGE[0], []).append((PASSAGE[1], PASSAGE[1] + PASSAGE[2]))
# the vestibule opens into the main room across edges 0..? — no, the L's inner
# corner at (7.86,13.26)/(15.58,13.26) is a real corner, not an opening, so
# every other edge runs full length.

m = Model()
runs = 0
for i in range(len(POLY)):
    (ax, az), _b, u, n, L = edge(i)
    ang = math.atan2(-u[1], u[0])
    cuts = [0.0, L]
    for g0, g1 in GAPS.get(i, []):
        cuts += [max(0.0, g0), min(L, g1)]
    cuts = sorted(set(round(c, 4) for c in cuts))
    for k in range(len(cuts) - 1):
        s0, s1 = cuts[k], cuts[k + 1]
        mid = 0.5 * (s0 + s1)
        if any(g0 - 1e-6 <= mid <= g1 + 1e-6 for g0, g1 in GAPS.get(i, [])):
            continue
        # run 0.08 past an outside corner so the board wraps the jamb
        e0 = s0 - (0.08 if s0 == 0.0 else 0.0)
        e1 = s1 + (0.08 if s1 == L else 0.0)
        ln = e1 - e0
        if ln <= 0.02:
            continue
        cx = ax + u[0] * (e0 + ln / 2) + n[0] * T / 2
        cz = az + u[1] * (e0 + ln / 2) + n[1] * T / 2
        m.add(box(ln, FACE_H, T), FACE, at=(cx, 0.0, cz), rot_y=ang)
        ccx = ax + u[0] * (e0 + ln / 2) + n[0] * CAP_T / 2
        ccz = az + u[1] * (e0 + ln / 2) + n[1] * CAP_T / 2
        m.add(box(ln, CAP_H, CAP_T), CAP, at=(ccx, FACE_H, ccz), rot_y=ang)
        runs += 1

m.save(OUT)
lo, hi = m.bounds()
print("bounds", tuple(round(v, 2) for v in lo), tuple(round(v, 2) for v in hi))
print("%d runs; lit=%.2f wall=%.0f -> face %s (byte %d) cap %s (byte %d)"
      % (runs, LIT, WALL, FACE_C, byte_of(FACE_C), CAP_C, byte_of(CAP_C)))
