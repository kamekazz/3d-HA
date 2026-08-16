"""Kitchen Range -- black freestanding gas range + the black over-range
microwave, in one model so they stay aligned in the east-wall cabinet slot
(x front 12.70, z 4.32 .. 6.78).
"""
from kcommon import *   # noqa

XW = XW_EAST
XF = 12.70            # range front face (stands proud of the door fronts)
Z0, Z1 = 4.32, 6.78
CTOP = 2.99           # cooktop glass
BG0, BG1 = 2.99, 3.72  # backguard / control panel
MW0, MW1 = 4.50, 5.96  # microwave band
XMW = 13.52           # microwave front


def build():
    m = Model()
    zc = (Z0 + Z1) / 2.0

    # ---- oven body
    bx(m, BLACK, XF, XW, 0.0, CTOP, Z0, Z1)
    bx(m, GLASSBLK, XF - 0.035, XF, 0.30, 2.18, Z0 + 0.11, Z1 - 0.11)
    bx(m, BLACK, XF - 0.055, XF - 0.03, 0.30, 0.45, Z0 + 0.09, Z1 - 0.09)
    bx(m, BLACK, XF - 0.055, XF - 0.03, 2.05, 2.20, Z0 + 0.09, Z1 - 0.09)
    bx(m, BLACK, XF - 0.03, XF, 0.02, 0.28, Z0 + 0.05, Z1 - 0.05)
    bx(m, BLACK, XF - 0.26, XF - 0.19, 2.30, 2.42, Z0 + 0.05, Z1 - 0.05)
    bx(m, BLACK, XF - 0.19, XF - 0.05, 2.33, 2.39, Z0 + 0.08, Z0 + 0.14)
    bx(m, BLACK, XF - 0.19, XF - 0.05, 2.33, 2.39, Z1 - 0.14, Z1 - 0.08)

    # ---- cooktop: black glass + five cast-iron grates
    bx(m, GLASSBLK, XF, XW - 0.02, CTOP - 0.02, CTOP + 0.03, Z0, Z1)
    grate = Material("grate", "#131417", roughness=0.62)
    for (gx, gz, r) in ((13.30, 4.94, 0.44), (13.30, 6.20, 0.44),
                        (14.14, 4.94, 0.40), (14.14, 6.20, 0.40),
                        (13.74, 5.57, 0.40)):
        for a in range(3):
            m.add(box(r * 2.0, 0.055, 0.075), grate, at=(gx, CTOP + 0.03, gz),
                  rot_y=a * math.pi / 3.0)
        m.add(cylinder(0.135, 0.05, seg=12), grate, at=(gx, CTOP + 0.01, gz))

    # ---- back control panel with a display, knobs on the front rail
    bx(m, BLACK, XW - 0.62, XW, BG0, BG1, Z0, Z1)
    bx(m, GLASSBLK, XW - 0.64, XW - 0.60, BG0 + 0.12, BG1 - 0.10, Z0 + 0.12, Z1 - 0.12)
    disp = Material("disp", "#c6ccd0", roughness=0.25, emissive="#6c7379")
    bx(m, disp, XW - 0.655, XW - 0.635, BG0 + 0.26, BG0 + 0.46, zc - 0.42, zc + 0.10)
    for i in range(5):
        z = Z0 + 0.30 + i * (Z1 - Z0 - 0.60) / 4.0
        m.add(cylinder(0.075, 0.12, seg=12), BLACK, at=(XF - 0.06, 2.58, z),
              rot_z=math.pi / 2)

    # ---- two grey towels over the handle (photo F)
    TOWEL = Material("towel", "#9b9e9f", roughness=0.95, emissive="#414243")
    for z in (zc - 0.50, zc + 0.14):
        bx(m, TOWEL, XF - 0.295, XF - 0.255, 1.62, 2.38, z, z + 0.36)
        bx(m, TOWEL, XF - 0.295, XF - 0.255, 1.55, 1.63, z + 0.01, z + 0.35)

    # ---- over-range microwave
    bx(m, BLACK, XMW, XW, MW0, MW1, Z0 - 0.02, Z1 + 0.02)
    bx(m, GLASSBLK, XMW - 0.035, XMW, MW0 + 0.10, MW1 - 0.22, Z0 + 0.02, Z1 - 0.62)
    bx(m, BLACK, XMW - 0.045, XMW - 0.02, MW1 - 0.24, MW1 - 0.19, Z0 + 0.02, Z1 - 0.62)
    for i in range(7):
        bx(m, GLASSBLK, XMW - 0.04, XMW - 0.02, MW1 - 0.17, MW1 - 0.06,
           Z0 + 0.10 + i * 0.28, Z0 + 0.10 + i * 0.28 + 0.17)
    pad = Material("pad", "#26282b", roughness=0.35)
    bx(m, pad, XMW - 0.035, XMW - 0.01, MW0 + 0.12, MW1 - 0.20, Z1 - 0.58, Z1 - 0.06)
    bx(m, PULL, XMW - 0.10, XMW - 0.05, MW0 + 0.16, MW0 + 0.26, Z0 + 0.06, Z1 - 0.60)
    return m


if __name__ == "__main__":
    emit(build(), "Kitchen Range", y=FLOOR_TOP)
