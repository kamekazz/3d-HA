"""Tone calibration strip: patches of known albedo/emissive on the two walls the
primary view (corner_nw) shows, plus a downward-facing ceiling row and an
upward-facing floor row.  Render it, measure the bytes, then throw it away.
"""
from dk import *  # noqa

COMBOS = [
    ("ffffff", None),
    ("c9ced3", None),
    ("c9ced3", "303030"),
    ("c9ced3", "5a5a5a"),
    ("c9ced3", "8a8a8a"),
    ("ffffff", "5a5a5a"),
]

m = Model()
mats = []
for i, (alb, em) in enumerate(COMBOS):
    mats.append(Material("p%d" % i, "#" + alb, roughness=0.9,
                         emissive=("#" + em) if em else None,
                         double_sided=False))

PW, GAP = 2.2, 0.2
for i, mat in enumerate(mats):
    x0 = 2.0 + i * (PW + GAP)
    # south wall (far wall in corner_nw), facing north
    m.add(panel(x0, x0 + PW, 3.4, 5.6, D - 0.12, -1), mat)
    # ceiling row, facing down
    m.add(plane_xz(x0, x0 + PW, 7.0, 9.2, 8.55, -1), mat)
    # floor row, facing up
    m.add(plane_xz(x0, x0 + PW, 12.0, 14.2, 0.06, +1), mat)
    # east wall, facing west
    z0 = 1.4 + i * (PW + GAP)
    m.add(panel_zy(z0, z0 + PW, 3.4, 5.6, W - 0.12, -1), mat)

place_local("Dining Calib", m)
