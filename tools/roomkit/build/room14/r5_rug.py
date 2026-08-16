"""Area rug — round 5.  A tone field instead of a height field.

Round 4 built the pile as a 56 x 420 smooth height field (24.6k verts, 1.13 MB)
with 0.013 ft loops, and it metered sigma 3.6 against the photo's ~18 local /
~33 over the whole rug.  That is not a tuning miss, it is the wrong mechanism:
this scene has one directional sun and a large isotropic hemisphere + IBL term,
so a 20-degree normal tilt changes almost nothing about what a surface collects.
The photo's ribs are visible because of self-shadowing the renderer does not do.

So the ribs, bands and the bed's contact shadow are ALBEDO now, quantised into a
small palette and merged into runs along x (r5_raster).  The rug drops from
1.13 MB to well under 100 KB and gains four to five times the spread.

SIZE re-solved for the king: the photo has the rug running ~1 ft past the bed's
west rail, stopping about level with the nightstand on the east, and reaching
~4.7 ft past the foot.  With the king at x 6.85..13.95, z 0.10..7.65 that is
x 5.30..14.20, z 2.55..12.35.
"""
import math
import os
import sys

sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from roomkit.glb import Model, Material, Part            # noqa: E402
from r5_raster import Field, raster, ramp, fbm, hash01   # noqa: E402

OUT = sys.argv[1] if len(sys.argv) > 1 else "rug.glb"

X0, X1 = 5.30, 14.20
Z0, Z1 = 2.55, 12.35
BED = (6.85, 13.95, 0.10, 7.65)      # king footprint, for the baked contact AO

PILE = 0.052
CX, CZ = (X0 + X1) / 2, (Z0 + Z1) / 2

# The ramp has to be WIDE.  Near white, the exposure+ACES curve compresses hard:
# #d3d5d6 and #f4f6f6 both land within a few bytes of each other, which is how
# round 5's first coverlet still metered sigma 3.  These are picked so the
# darkest tone renders ~210 and the lightest ~252 on a 225 wall.
TONES = ramp("#9b9d9e", "#ffffff", 7, "rug", roughness=0.99)
BACK = Material("rug_back", "#8f9092", roughness=1.0)
EDGE = Material("rug_edge", "#c6c7c7", roughness=0.99)

NT = len(TONES)


def band_profile(z):
    """The photo's rug is BANDED: flat pile, looped rows, chevron, repeating.

    Band WIDTH is jittered per band.  A fixed 0.62 ft repeat renders as a
    venetian blind -- round 2's "corrugated board" finding in a new form.
    """
    v = z - Z0
    band = int(v / 0.62)
    kind = band % 3
    j = hash01(band, 3, 55) * 0.35 + 0.85          # per-band pitch jitter
    if kind == 0:                                   # flat cut pile
        return 0.845 + 0.022 * math.sin(v * 9.1 * j)
    if kind == 1:                                   # fine looped ribs
        return 0.825 + 0.044 * math.cos(2 * math.pi * v / (0.115 * j))
    return 0.835 + 0.032 * math.cos(2 * math.pi * v / (0.152 * j))  # chevron


def ao(x, z):
    """Fake contact shadow: the app renders none, so the bed is baked in."""
    dx = max(BED[0] - x, x - BED[1], 0.0)
    dz = max(BED[2] - z, z - BED[3], 0.0)
    d = math.hypot(dx, dz)
    if d <= 0.02:
        return 0.30
    if d < 0.62:
        return 0.30 * math.exp(-(d / 0.30) ** 1.5)
    return 0.0


def tone(x, z):
    v = z - Z0
    band = int(v / 0.62)
    t = band_profile(z)
    if band % 3 == 2:                       # chevron: shift the rib along x
        s = abs(((x - X0 + band * 0.33) % 0.92) - 0.46)
        t += 0.038 * math.cos(2 * math.pi * (v + 0.55 * s) / 0.152)
    t += (fbm(x * 0.80, z * 0.80, 517, 3) - 0.5) * 0.26      # broad soiling
    t += (fbm(x * 1.45, z * 1.45, 733, 2) - 0.5) * 0.09       # weave mottle
    t -= ao(x, z)
    return t


def fn(x, z):
    return max(0, min(NT - 1, int(tone(x, z) * NT)))


def pt(u, w):
    # a whisper of relief so the silhouette is pile and not a card; the tone
    # field does the visual work
    y = PILE + 0.010 * math.cos(2 * math.pi * (w - Z0) / 0.115)
    ex = min(u - X0, X1 - u, w - Z0, Z1 - w)
    if ex < 0.09:
        y *= max(0.0, ex / 0.09) ** 0.6
    return (u - CX, y, w - CZ)


def nrm(_u, _w):
    return (0.0, 1.0, 0.0)


m = Model()
fld = Field(TONES)
NU = int((X1 - X0) / 0.235)
NW = int((Z1 - Z0) / 0.055)
raster(fld, pt, nrm, X0, X1, Z0, Z1, NU, NW, fn)
verts = fld.emit(m)

# thin backing + a soft edge band so the perimeter reads as a bound rug
W, D = X1 - X0, Z1 - Z0
m.add(Part([(-W / 2 + 0.02, 0.0, -D / 2 + 0.02), (W / 2 - 0.02, 0.0, -D / 2 + 0.02),
            (W / 2 - 0.02, 0.0, D / 2 - 0.02), (-W / 2 + 0.02, 0.0, D / 2 - 0.02)],
           [(0, 2, 1), (0, 3, 2)]), BACK)
for sx, sz, a, b in ((0, -1, (-W / 2, -D / 2), (W / 2, -D / 2)),
                     (0, 1, (-W / 2, D / 2), (W / 2, D / 2)),
                     (-1, 0, (-W / 2, -D / 2), (-W / 2, D / 2)),
                     (1, 0, (W / 2, -D / 2), (W / 2, D / 2))):
    m.add(Part([(a[0], 0.0, a[1]), (b[0], 0.0, b[1]),
                (b[0], PILE * 0.55, b[1]), (a[0], PILE * 0.55, a[1])],
               [(0, 1, 2), (0, 2, 3)]), EDGE)

m.save(OUT)
lo, hi = m.bounds()
print("bounds", tuple(round(v, 3) for v in lo), tuple(round(v, 3) for v in hi))
print("pile %.2f x %.2f ft  cells %dx%d  field verts %d  %.1f KB"
      % (W, D, NU, NW, verts, os.path.getsize(OUT) / 1024))
