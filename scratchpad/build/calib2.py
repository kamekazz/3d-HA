"""Decisive calibration for GLB model surfaces.

P0 pure white, unlit-emissive-free  -> isolates I (illumination per unit albedo)
P1 mid grey, no emissive            -> checks linearity of I
P2 black albedo + mid grey emissive -> isolates k (the emissive scale)
"""
from dk import *  # noqa

COMBOS = [("#ffffff", None), ("#808080", None), ("#000000", "#808080")]
mats = [Material("q%d" % i, a, roughness=0.9, emissive=e, double_sided=False)
        for i, (a, e) in enumerate(COMBOS)]

m = Model()
for i, mt in enumerate(mats):
    x0 = 1.0 + i * 4.0
    m.add(panel(x0, x0 + 3.6, 3.4, 6.4, D - 0.10, -1), mt)      # south wall
    z0 = 1.0 + i * 4.0
    m.add(panel_zy(z0, z0 + 3.6, 3.4, 6.4, 0.10, +1), mt)       # west wall
    m.add(plane_xz(x0, x0 + 3.6, 12.0, 15.0, 8.15, -1), mt)     # facing down
place_local("Dining Calib2", m)
