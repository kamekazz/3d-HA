"""Kitchen Stool -- light-grey barrel-back counter stool on a black steel
cantilever sled (photos A / C / F).

Authored facing EAST (+x) in room coordinates, pulled up to the island's west
overhang (island counter edge x 5.25).  Emitted twice at different z.
"""
from kcommon import *   # noqa

SEAT = 2.16          # seat top
XC = 4.51            # seat centre
TUBE = Material("tube", "#191a1e", roughness=0.30, metallic=0.68)
FAB = Material("stoolfab", "#c2c1bd", roughness=0.94, emissive="#535353")
FAB_IN = Material("stoolfabin", "#a5a49f", roughness=0.95, emissive="#3d3d3d")
T = 0.055            # flat-bar thickness


def _ring(cx, cz, r_in, r_out, a0, a1, seg, flat=1.0):
    pts = []
    for i in range(seg + 1):
        a = a0 + (a1 - a0) * i / seg
        pts.append((cx + r_out * math.cos(a) * flat, cz + r_out * math.sin(a)))
    for i in range(seg, -1, -1):
        a = a0 + (a1 - a0) * i / seg
        pts.append((cx + r_in * math.cos(a) * flat, cz + r_in * math.sin(a)))
    return pts


def build(zc):
    m = Model()
    xc = XC

    # ---- cantilever sled: an open "C" each side, no rear leg
    for dz in (-0.58, 0.58):
        z = zc + dz
        bx(m, TUBE, xc - 0.70, xc + 0.56, 0.0, 0.09, z - T, z + T)      # runner
        bx(m, TUBE, xc + 0.47, xc + 0.56, 0.05, SEAT - 0.22, z - T, z + T)
        bx(m, TUBE, xc - 0.34, xc + 0.56, SEAT - 0.31, SEAT - 0.22, z - T, z + T)
    bx(m, TUBE, xc - 0.70, xc - 0.61, 0.0, 0.09, zc - 0.58, zc + 0.58)
    bx(m, TUBE, xc + 0.47, xc + 0.56, SEAT - 0.31, SEAT - 0.22, zc - 0.58, zc + 0.58)
    bx(m, TUBE, xc - 0.34, xc - 0.25, SEAT - 0.31, SEAT - 0.22, zc - 0.58, zc + 0.58)

    # ---- upholstered seat
    m.add(rounded_box(1.28, 0.34, 1.36, r=0.26, seg=5), FAB,
          at=(xc, SEAT - 0.34, zc))

    # ---- barrel back: one swept shell wrapping most of the way round, with a
    # slightly darker liner so the inside of the barrel reads as a hollow.  The
    # app renders no shadow, so without the value step the whole stool came back
    # as one white blob at dollhouse distance.
    a0, a1 = -1.62, 1.62
    m.add(prism(_ring(xc - 0.06, zc, 0.60, 0.72, a0, a1, 14, flat=0.80), 0.92,
                smooth=False), FAB, at=(0, SEAT, 0))
    m.add(prism(_ring(xc - 0.06, zc, 0.545, 0.60, a0, a1, 14, flat=0.80), 0.88,
                smooth=False), FAB_IN, at=(0, SEAT, 0))
    m.add(prism(_ring(xc - 0.06, zc, 0.575, 0.745, a0 - 0.03, a1 + 0.03, 14,
                      flat=0.80), 0.15, smooth=False), FAB, at=(0, SEAT + 0.86, 0))
    m.add(prism(_ring(xc - 0.06, zc, 0.0, 0.61, a0, a1, 14, flat=0.80), 0.06,
                smooth=False), FAB, at=(0, SEAT - 0.06, 0))
    return m


if __name__ == "__main__":
    for name, z in (("Kitchen Stool North", 6.78), ("Kitchen Stool South", 9.30)):
        emit(build(z), name, y=FLOOR_TOP)
