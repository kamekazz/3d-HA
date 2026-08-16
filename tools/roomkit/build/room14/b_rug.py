"""Area rug — round 3. Smaller, a shade off white, and BANDED instead of ribbed.

Round 2 was 10.05 x 7.05 ft of perfectly regular half-round ribs at one pitch,
edge to edge: the critic read it as corrugated board. Three changes:

  * SIZE. Off the photo the rug's east edge stops just short of the nightstand
    (rug at photo x~895, nightstand feet at 920) i.e. at the bed's east rail, and
    it runs ~1.4 ft west of the bed's west rail. With the queen bed at local
    x 7.03..12.48 that is x 5.55..12.55 -- 7.0 ft, not 10.05.
  * TEXTURE. The photo's rug is not one rib field: it is broad horizontal BANDS,
    some flat, some looped, some chevroned, at ~0.6 ft. Built as one smooth
    height field (soft normals, no facets) with a per-band profile, a finer
    0.145 ft loop pitch, half the round-2 amplitude, and a per-row jitter, so no
    two rows are identical and the eye stops reading a wave.
  * VALUE. Round 2 base #c3c4c6 metered 207 flat. The photo has the rug at
    164/177 = 0.927 of its wall; ours renders against a 224 wall, and 0.88 of
    that is 197, so the base drops to #b9babc. The rug still has to out-read a
    floor that renders much lighter than the photo's, so the separation is
    carried by the fake contact shadow instead of by brightness.

Fake AO: the app renders no shadows at all, so the bed's footprint and a 0.55 ft
penumbra around it are baked into the pile as two darker materials. Keyed to the
bed at local x 7.025..12.475, z 0.15..7.45 -- re-run this if the bed moves.
"""
import math
import random
import sys
sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
from roomkit.glb import Model, Material, Part, box

OUT = sys.argv[1] if len(sys.argv) > 1 else "../glb/rug.glb"

X0, X1 = 5.55, 12.55        # room-local footprint of the PILE
Z0, Z1 = 2.30, 11.00
BED = (7.025, 12.475, 0.15, 7.45)     # x0,x1,z0,z1 of the bed on the floor

W = X1 - X0
D = Z1 - Z0
PILE = 0.055                # pile height above the backing
SKIRT = -0.028              # backing bottom (buried in the room slab)

NX, NZ = 56, 420

PALE = Material("rug", "#c1c1c0", roughness=0.99)
AO1 = Material("rug_ao1", "#aaaaa9", roughness=0.99)
AO2 = Material("rug_ao2", "#919191", roughness=0.99)
BACK = Material("rug_back", "#9d9ea0", roughness=1.0)

rnd = random.Random(414)
ROW_J = {}


def rowj(k):
    if k not in ROW_J:
        ROW_J[k] = rnd.uniform(-0.0045, 0.0045)
    return ROW_J[k]


def height(x, z):
    """pile height at a point, feet above the backing."""
    u = (x - X0)
    v = (z - Z0)
    band = int(v / 0.60)
    kind = band % 3
    h = PILE
    if kind == 0:                       # flat cut pile, faint grain
        h += 0.007 * math.sin(v * 41.0) + 0.003 * math.sin(u * 7.3 + band)
    elif kind == 1:                     # looped rows
        h += 0.021 * (0.5 + 0.5 * math.cos(2 * math.pi * v / 0.145))
        h += 0.0035 * math.sin(u * 11.0 + band * 2.1)
    else:                               # chevron
        s = abs(((u + band * 0.31) % 0.86) - 0.43)
        h += 0.017 * (0.5 + 0.5 * math.cos(2 * math.pi * (v + 0.40 * s) / 0.165))
    h += rowj(int(v / 0.021))
    # taper + serrate the perimeter so the edge reads as pile, not as a slab
    ex = min(x - X0, X1 - x)
    ez = min(z - Z0, Z1 - z)
    e = min(ex, ez)
    if e < 0.10:
        h *= max(0.0, e / 0.10) ** 0.6
        h += 0.006 * ((int(round((u + v) / 0.06)) % 2) * 2 - 1) * (1 - e / 0.10)
    return max(0.0, h)


def ao(x, z):
    dx = max(BED[0] - x, x - BED[1], 0.0)
    dz = max(BED[2] - z, z - BED[3], 0.0)
    d = math.hypot(dx, dz)
    if d <= 0.02:
        return 2
    if d < 0.55:
        return 1
    return 0


m = Model()

# --- backing slab, slightly inset, its edge buried in the room slab --------
m.add(box(W - 0.02, -SKIRT, D - 0.02), BACK,
      at=((X0 + X1) / 2 - (X0 + X1) / 2, SKIRT, 0))   # centred on origin below

# --- pile height field, split into three AO buckets ------------------------
cols = [[], [], []]     # verts per bucket
tris = [[], [], []]
index = {}


def vid(bucket, ix, iz):
    key = (bucket, ix, iz)
    if key not in index:
        x = X0 + W * ix / NX
        z = Z0 + D * iz / NZ
        index[key] = len(cols[bucket])
        cols[bucket].append((x - (X0 + X1) / 2, PILE * 0 + height(x, z),
                             z - (Z0 + Z1) / 2))
    return index[key]


for iz in range(NZ):
    for ix in range(NX):
        x = X0 + W * (ix + 0.5) / NX
        z = Z0 + D * (iz + 0.5) / NZ
        b = ao(x, z)
        a = vid(b, ix, iz)
        bb = vid(b, ix + 1, iz)
        c = vid(b, ix + 1, iz + 1)
        d = vid(b, ix, iz + 1)
        tris[b] += [(a, c, bb), (a, d, c)]

for b, mat in ((0, PALE), (1, AO1), (2, AO2)):
    if tris[b]:
        m.add(Part(cols[b], tris[b], smooth=True), mat)

m.save(OUT)
lo, hi = m.bounds()
print("bounds", tuple(round(v, 3) for v in lo), tuple(round(v, 3) for v in hi))
print("pile %.2f x %.2f ft, %d verts" % (W, D, sum(len(c) for c in cols)))
