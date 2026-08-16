"""Living Room ceiling: flat white plane at 9 ft + crown moulding + recessed cans."""
import math
from kit import *

# ---- tone ---------------------------------------------------------------
# A downward-facing plane collects almost no direct light in this scene, so the
# ceiling is emissive-driven (same lesson as the master bedroom vault).
CEIL = Material("ceil", "#ffffff", roughness=0.96, emissive="#c9c9c9", double_sided=False)
CROWN = Material("crown", "#fbfbfa", roughness=0.7, emissive="#9c9c9c")
TRIM = Material("cantrim", "#ffffff", roughness=0.6, emissive="#9a9a9a", double_sided=False)
APER = Material("canaper", "#ffffff", roughness=0.4, emissive="#8e8c86", double_sided=False)
LENS = Material("lens", "#ffffff", roughness=0.35, emissive="#b9b7b0")

def disc_down(r, seg=18, y=0.0):
    """A flat disc whose single face looks DOWN -- a cylinder would leave its
    top cap visible from the plan/dollhouse view, where the ceiling must not be."""
    from roomkit.glb import Part
    v = [(0.0, y, 0.0)]
    for i in range(seg):
        a = 2 * math.pi * i / seg
        v.append((r * math.cos(a), y, r * math.sin(a)))
    t = [(0, 1 + i, 1 + (i + 1) % seg) for i in range(seg)]
    return Part(v, t)


m = Model()
HW, HD = RW / 2, RD / 2

# flat ceiling, single-sided facing DOWN so the plan view still shows the floor
m.add(quad((-HW, 0, -HD), (HW, 0, -HD), (HW, 0, HD), (-HW, 0, HD)), CEIL)

# ---- crown moulding -----------------------------------------------------
# profile = (vertical from the ceiling, depth out from the wall face)
CR = [(0.0, 0.0), (-0.52, 0.0), (-0.50, 0.055), (-0.42, 0.085),
      (-0.30, 0.12), (-0.07, 0.31), (0.0, 0.33)]
sweep(CR, RW, CROWN, m, "n", (HW, 0.0, -HD))
sweep(CR, RW, CROWN, m, "s", (-HW, 0.0, HD))
sweep(CR, RD, CROWN, m, "e", (HW, 0.0, HD))
sweep(CR, RD, CROWN, m, "w", (-HW, 0.0, -HD))

# ---- recessed cans ------------------------------------------------------
CANS = [(5.0, 3.4), (11.6, 3.4), (19.2, 3.6), (26.0, 3.4),
        (4.6, 12.4), (10.8, 12.6), (19.8, 12.8), (26.4, 12.4),
        (26.6, 8.0)]
for (cx, cz) in CANS:
    at = (lx(cx), -0.035, lz(cz))
    m.add(disc_down(0.345), TRIM, at=at)
    m.add(disc_down(0.275), APER, at=(at[0], -0.012, at[2]))

# ---- round flush-mount over the seating group ---------------------------
# The photo's fixture is a flat white disc with a raised concentric ring, not a
# dome -- a dome reads as a bathroom globe from every angle.
fx, fz = lx(13.6), lz(8.6)
m.add(disc_down(0.80, seg=36), CROWN, at=(fx, -0.004, fz))
m.add(cylinder(0.78, 0.055, seg=36, anchor="base"), LENS, at=(fx, -0.055, fz))
m.add(cylinder(0.72, 0.075, seg=36, anchor="base", r_top=0.70), LENS, at=(fx, -0.13, fz))
m.add(torus(0.46, 0.035, seg=36, ring=6), CROWN, at=(fx, -0.15, fz))
m.add(torus(0.30, 0.025, seg=28, ring=6), CROWN, at=(fx, -0.15, fz))

p = save(m, "ceiling")
lo, hi = m.bounds()
# ceiling plane sits at local y = RH; the model's y=0 IS that plane
put("Living Ceiling", p, (RW / 2, RH + lo[1], RD / 2))
