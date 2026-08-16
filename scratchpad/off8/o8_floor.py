"""Room 8 Office -- the grey LVP plank floor as a tone field.

The room's `floor_texture: wood` slab renders flat (metered sd 3.3) and 31
bytes brighter than the photo (141 vs Office A's 109.8 / sd 13.9 over a
230x220 clean patch).  Rather than push more geometry at it, this is a single
plane of plank quads -- 7 shared materials, butt joints staggered like the
real floor -- which fixes value, spread and plank direction (the photo's seams
run north-south) in ~15 KB.

Named "Office Floor" so objects.js SURFACE_RE keeps it unpickable.
"""
import sys
from o8kit import (Model, Material, Part, W, D, Rnd, save_and_place)

# base greys sampled off Office A.jpg's clean floor patch, spread to sd ~14
TONES = ["#383836", "#3d3d3b", "#414140", "#454543", "#494947", "#4e4e4b",
         "#535350"]
SEAM = Material("plankseam", "#2e2e2d", roughness=0.95)
PW = 0.58          # 7in planks
Y = 0.045


def build(scale=1.0):
    m = Model()
    mats = [Material(f"plank{i}", _scaled(c, scale), roughness=0.88)
            for i, c in enumerate(TONES)]
    r = Rnd(80808)
    # one seam plane under everything so the butt joints read as dark lines
    m.add(_quad(0, W, 0, D, Y - 0.002), SEAM)
    x = 0.0
    col = 0
    while x < W - 0.001:
        x1 = min(W, x + PW)
        z = -((col * 1.7) % 4.0)          # stagger the butt joints
        while z < D - 0.001:
            z1 = min(D, z + 3.2 + r.f(0.0, 2.6))
            if z1 > 0:
                t = int(r.f(0, len(mats) - 0.001))
                m.add(_quad(x + 0.012, x1 - 0.012, max(0.0, z) + 0.018,
                            z1 - 0.018, Y), mats[t])
            z = z1
        x = x1
        col += 1
    return m


def _quad(x0, x1, z0, z1, y):
    return Part([(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)],
                [(0, 2, 1), (0, 3, 2)])


def _scaled(hexc, s):
    c = hexc.lstrip("#")
    return "#%02x%02x%02x" % tuple(
        max(0, min(255, int(round(int(c[i:i + 2], 16) * s)))) for i in (0, 2, 4))


if __name__ == "__main__":
    s = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
    save_and_place("Office Floor", build(s))
