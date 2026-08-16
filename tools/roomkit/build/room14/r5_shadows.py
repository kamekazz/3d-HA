"""Contact shadows — round 5 footprints (round 4's trick, re-keyed).

Re-keyed to the king bed, the new dresser, the armchair and the leaning
panels that replace the invented Tall Chest, and the new floor props.  The
bed's own contact shadow is baked into the Rug where the rug covers it and
kept here only for the head of the bed, which stands on bare floor.

Round 4 notes follow.

The app renders no shadows for generated geometry, so every piece in this house
floated except the bed, whose contact shadow the Rug bakes into its pile.  This
is that trick applied to everything else in room 14: soft dark decals lying on
the slab under each piece's footprint, built as NESTED translucent frames (core
+ three penumbra rings) rather than stacked quads, so nothing is coplanar with
anything and there is no z-fighting.

Named "Master Floor Shadows" on purpose — objects.js's SURFACE_RE makes any
object whose name contains "floor" unpickable, which a room-wide decal has to be
or it swallows every click in the room.
"""
import os
import sys

sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from roomkit.glb import Model, Material, Part

OUT = sys.argv[1] if len(sys.argv) > 1 else "shadows.glb"

# pad (ft) -> alpha.  Six rings, not four: at four the falloff still read as a
# grey mat with a visible step.  Core stays under the piece where nothing sees
# it; everything outside 0.1 ft is penumbra.
RINGS = [(0.00, 0.42), (0.10, 0.30), (0.22, 0.20), (0.36, 0.12),
         (0.52, 0.065), (0.72, 0.03)]

m = Model()
MATS = [Material("ao%d" % i, "#000000", roughness=1.0, opacity=a,
                 double_sided=True)
        for i, (_p, a) in enumerate(RINGS)]


def quad(x0, x1, z0, z1, mat, y=0.0):
    if x1 - x0 < 1e-4 or z1 - z0 < 1e-4:
        return
    v = [(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)]
    m.add(Part(v, [(0, 2, 1), (0, 3, 2)]), mat)     # normal +y


def blob(x0, x1, z0, z1):
    """core rect plus concentric frames — never overlapping, so no z-fight."""
    for i, (pad, _a) in enumerate(RINGS):
        mat = MATS[i]
        a0, a1, b0, b1 = x0 - pad, x1 + pad, z0 - pad, z1 + pad
        if i == 0:
            quad(a0, a1, b0, b1, mat)
            continue
        p_prev = RINGS[i - 1][0]
        i0, i1, j0, j1 = x0 - p_prev, x1 + p_prev, z0 - p_prev, z1 + p_prev
        quad(a0, a1, b0, j0, mat)          # north strip
        quad(a0, a1, j1, b1, mat)          # south strip
        quad(a0, i0, j0, j1, mat)          # west strip
        quad(i1, a1, j0, j1, mat)          # east strip


# footprints in room-local feet — keep in step with r4_place.PLACE
FEET = [
    ("Dresser",          0.075, 1.670, 3.41, 8.41),
    ("Armchair",         1.950, 4.650, 0.50, 3.20),
    ("Lean Panels",      0.070, 1.170, 0.69, 2.71),
    ("Nightstand",      13.950, 16.150, 0.70, 2.30),
    ("Desk",            18.295, 20.305, 0.21, 5.01),
    ("Foreground Chest", 18.620, 20.420, 8.36, 11.76),
    ("Chair",           16.700, 18.300, 3.40, 5.00),
    ("Bin",              0.140, 1.160, 8.60, 9.62),
    ("Laundry",          0.400, 1.800, 11.95, 13.07),
    ("Bed head",         6.850, 13.950, 0.10, 2.50),
]
for name, x0, x1, z0, z1 in FEET:
    blob(x0, x1, z0, z1)

m.save(OUT)
lo, hi = m.bounds()
print("bounds", tuple(round(v, 2) for v in lo), tuple(round(v, 2) for v in hi))
print("%d blobs" % len(FEET))
