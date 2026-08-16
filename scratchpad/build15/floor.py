"""Grey LVP plank floor laid over the room slab.

The app's 'wood' floor texture tiles at 2.2 ft and reads as fine corduroy from
eye level; the photo's floor is 6-in grey planks with clear butt joints running
north-south.  This is a 0.014 ft skin of real plank geometry sitting just above
the slab (slab top is y=0.01, so the planks live at 0.016..0.030 and nothing
z-fights).
"""

import math
from common import *   # noqa
from furniture import Rnd, bx

PW = 0.52          # plank width
PL = 4.30          # plank length
GAP = 0.022

TONES = ["#706d6a", "#6b6966", "#77736f", "#666461", "#726f6b", "#6d6b68",
         "#7a7671", "#625f5d"]
MATS = [Material(f"plank{i}", c, roughness=0.62) for i, c in enumerate(TONES)]
SEAM = Material("seam", "#403e3a", roughness=0.95)


def floor():
    m = Model()
    y0, y1 = 0.0, 0.014
    # dark ground so the joints read as shadow lines
    bx(m, SEAM, 0.0, W, -0.006, y0 + 0.002, 0.0, D)

    rn = Rnd(20250815)
    ncol = int(math.ceil(W / PW))
    for c in range(ncol):
        x0 = c * PW
        x1 = min(W, x0 + PW - GAP)
        if x1 - x0 < 0.05:
            continue
        off = rn.f(0.0, PL)          # stagger the butt joints per column
        z = -off
        while z < D:
            za = max(0.0, z)
            zb = min(D, z + PL - GAP)
            if zb - za > 0.06:
                mat = MATS[int(rn.f(0, len(MATS) - 0.001))]
                bx(m, mat, x0, x1, y0, y1, za, zb)
            z += PL
    return m


if __name__ == "__main__":
    m = floor()
    path = os.path.join(OUT, "rios_floor.glb")
    m.save(path)
    lo, hi = m.bounds()
    place("Rios Floor", path, ROOM, pos=(W / 2, 0.012, D / 2), rot_y_deg=0.0)
    print("Rios Floor", tuple(round(hi[i] - lo[i], 3) for i in range(3)),
          "pos", (W / 2, 0.012, D / 2))
