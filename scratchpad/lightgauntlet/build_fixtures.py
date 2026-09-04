"""Four generic light fixtures for the model library.

Authored in FEET (roomkit.glb converts to metres on save; models.js scales the
loaded instance back by 3.28084, so feet in -> feet on screen).

Material naming contract: every emissive part carries "shade" / "lens" /
"glass" in its material name so light_cfg.glow_part can target it; every metal
part deliberately does NOT, and is a distinctly darker grey so the glow reads
as coming from the lens.
"""

import math
import os
import sys

sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")

from roomkit.glb import Model, Material, Part, box, cylinder  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "glb")
os.makedirs(OUT, exist_ok=True)

# --- materials -------------------------------------------------------------
# Lens: warm off-white, near-white so a raised emissive reads as a lit lens
# rather than a tinted one. Opaque on purpose -- a BLEND material sorts badly
# against the room shell and against itself.
LENS = dict(roughness=0.55, metallic=0.0)
# Metal: distinctly darker/greyer. Low metallic -- there is no env map in this
# scene, so a metallic=1 part just goes black.
MET = dict(roughness=0.40, metallic=0.30)

LENS_HEX = "#f6f2e7"
METAL_HEX = "#54585c"
STEEL_HEX = "#63686c"


def dome(radius, h, seg=28, rings=7):
    """Half-ellipsoid cap, apex DOWN at y=0, rim of `radius` at y=h.

    Wound so faces point outward/downward (same convention cylinder() uses:
    (lower_j, upper_j, lower_j+1), (upper_j, upper_j+1, lower_j+1)).
    """
    v, t = [], []
    apex = 0
    v.append((0.0, 0.0, 0.0))
    ring_base = []
    for i in range(1, rings + 1):
        a = (math.pi / 2) * i / rings
        r = radius * math.sin(a)
        y = h * (1.0 - math.cos(a))
        ring_base.append(len(v))
        for j in range(seg):
            th = 2 * math.pi * j / seg
            v.append((r * math.cos(th), y, r * math.sin(th)))
    # apex fan
    b0 = ring_base[0]
    for j in range(seg):
        t.append((b0 + j, b0 + (j + 1) % seg, apex))
    # bands
    for i in range(rings - 1):
        lo, up = ring_base[i], ring_base[i + 1]
        for j in range(seg):
            k = (j + 1) % seg
            t.append((lo + j, up + j, lo + k))
            t.append((up + j, up + k, lo + k))
    # flat rim cap facing +Y (never seen -- it is against the ceiling)
    top = len(v)
    v.append((0.0, h, 0.0))
    lo = ring_base[-1]
    for j in range(seg):
        k = (j + 1) % seg
        t.append((top, lo + j, lo + k))
    return Part(v, t, smooth=True)


def save(m, fname):
    p = os.path.join(OUT, fname)
    m.save(p)
    lo, hi = m.bounds()
    print(f"{fname:26s} w={hi[0]-lo[0]:.3f} h={hi[1]-lo[1]:.3f} "
          f"d={hi[2]-lo[2]:.3f} ft   y=[{lo[1]:.3f},{hi[1]:.3f}]  "
          f"{os.path.getsize(p)/1024:.1f} KB")


# --------------------------------------------------------------------------
# 1. Flush Dome Ceiling -- ~1.1 ft dia, ~0.45 ft tall
# --------------------------------------------------------------------------
def flush_dome():
    glass = Material("dome_shade_glass", LENS_HEX, **LENS)
    metal = Material("dome_ring_metal", METAL_HEX, **MET)
    m = Model()
    m.add(dome(0.52, 0.36), glass, at=(0, 0.0, 0))          # y 0.00 .. 0.36
    m.add(cylinder(0.55, 0.07, seg=28), metal, at=(0, 0.34, 0))   # trim ring
    m.add(cylinder(0.42, 0.04, seg=24), metal, at=(0, 0.41, 0))   # canopy
    save(m, "flush_dome_ceiling.glb")


# --------------------------------------------------------------------------
# 2. Pendant Shade -- shade 1.2 ft dia, 2.2 ft total drop
# --------------------------------------------------------------------------
def pendant():
    shade = Material("pendant_shade_opal", LENS_HEX, **LENS)
    lens = Material("pendant_lens_glass", "#faf7ef", roughness=0.45, metallic=0.0)
    metal = Material("pendant_metal", METAL_HEX, **MET)
    m = Model()
    m.add(cylinder(0.50, 0.05, seg=28), lens, at=(0, 0.0, 0))       # diffuser disc
    # downward-facing cone shade: wide (0.60) at the bottom, narrow at the top
    m.add(cylinder(0.60, 0.85, seg=28, r_top=0.24), shade, at=(0, 0.05, 0))
    m.add(cylinder(0.045, 1.20, seg=12), metal, at=(0, 0.90, 0))    # drop rod
    m.add(cylinder(0.26, 0.10, seg=24, r_top=0.16), metal, at=(0, 2.10, 0))  # canopy
    save(m, "pendant_shade.glb")


# --------------------------------------------------------------------------
# 3. Vanity Bar -- 2.4 ft wide, ~0.7 ft tall, 3 upward shades
# --------------------------------------------------------------------------
def vanity():
    shade = Material("vanity_shade_glass", LENS_HEX, **LENS)
    metal = Material("vanity_bar_metal", METAL_HEX, **MET)
    m = Model()
    # wall backplate
    m.add(box(2.40, 0.34, 0.08), metal, at=(0, 0.16, -0.13))
    # horizontal bar: a cylinder laid along X (rot_z turns its Y axis into X)
    m.add(cylinder(0.11, 2.40, seg=20, anchor="center"), metal,
          at=(0, 0.11, 0.0), rot_z=math.pi / 2)
    # three upward-facing glass shades
    for x in (-0.78, 0.0, 0.78):
        m.add(cylinder(0.14, 0.46, seg=22, r_top=0.24), shade, at=(x, 0.22, 0))
    save(m, "vanity_bar.glb")


# --------------------------------------------------------------------------
# 4. Shop Strip Light -- 4 ft long, ~0.35 ft tall, 0.5 ft deep
# --------------------------------------------------------------------------
def strip():
    lens = Material("strip_lens_glass", LENS_HEX, **LENS)
    metal = Material("strip_housing_metal", STEEL_HEX, **MET)
    m = Model()
    m.add(box(4.00, 0.20, 0.50), metal, at=(0, 0.15, 0))            # channel
    for z in (-0.14, 0.14):                                          # two tubes
        m.add(cylinder(0.075, 3.70, seg=16, anchor="center"), lens,
              at=(0, 0.075, z), rot_z=math.pi / 2)
    for x in (-1.96, 1.96):                                          # end plates
        m.add(box(0.08, 0.15, 0.50), metal, at=(x, 0.0, 0))
    save(m, "shop_strip_light.glb")


if __name__ == "__main__":
    flush_dome()
    pendant()
    vanity()
    strip()
