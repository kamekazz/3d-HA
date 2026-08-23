"""Meter the contact-shadow darkening of every ring, from the plan render.

The round-1 report claimed "about 25-30%" and the critic re-measured 48 / 15 /
9 / 0 / 0.  The difference was that the round-1 boxes were placed by eye.  Here
the sample boxes are COMPUTED from the same footprint list the shadow piece is
built from, so a box cannot land on the object instead of the floor:

  * `edge`  -- the 6 px of floor immediately OUTSIDE the footprint, on the side
               of the ring that faces open floor;
  * `open`  -- the same strip pushed 1.6 ft further out, past the ramp.

Run after `g8_surface.py` and a plan shot.
"""
import sys

sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\g8")

import m as METER                                                  # noqa: E402
import g8_surface as S                                             # noqa: E402
import g8_furn as F                                                # noqa: E402
import g8_arch as A                                                # noqa: E402

SHOT = (r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\shots"
        r"\v3_garage\r2_plan.png")

# plan pose: pos (29.1, 44.125, 23.85) looking straight down, fov 45, 900 px.
PXFT = 900.0 / (2 * (44.125 - 8.0) * 0.41421)      # tan(22.5 deg)
CX, CZ = 10.2, 10.85                               # room-local centre


def img(x, z):
    return (450 + (x - CX) * PXFT, 450 + (z - CZ) * PXFT)


def main():
    models = [fn() for _n, fn in F.PIECES] + [A.steps()]
    rects = S._foot_rects(models)
    feet = [((a + c) / 2, (b + d) / 2, (c - a) / 2, (d - b) / 2, 0.0)
            for (a, b, c, d) in rects]
    def clear(px, pz, skip):
        """How far (cheaply) this point is from every OTHER footprint -- the
        sample side is chosen by this, so a box cannot land on a neighbouring
        object or inside a neighbour's ramp."""
        best = 99.0
        for j, (x0, z0, x1, z1) in enumerate(rects):
            if j == skip:
                continue
            dx = max(0.0, x0 - px, px - x1)
            dz = max(0.0, z0 - pz, pz - z1)
            best = min(best, (dx * dx + dz * dz) ** 0.5)
        best = min(best, px - 0.2, S.W - 0.2 - px, pz - 0.2, S.D - 0.2 - pz)
        return best

    names = []
    boxes = {}
    for i, (cx, cz, rx, rz, s) in enumerate(feet):
        best, side = -1.0, (1, 0)
        for (sx, sz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            px = cx + sx * (rx + 1.2)
            pz = cz + sz * (rz + 1.2)
            c = clear(px, pz, i)
            if c > best:
                best, side = c, (sx, sz)
        sx, sz = side
        for tag, d0, d1 in (("edge", 0.02, 0.22), ("open", 1.05, 1.35)):
            if sx:
                ex = cx + sx * rx
                a = img(ex + sx * d0, cz - rz * 0.55)
                b = img(ex + sx * d1, cz + rz * 0.55)
            else:
                ez = cz + sz * rz
                a = img(cx - rx * 0.55, ez + sz * d0)
                b = img(cx + rx * 0.55, ez + sz * d1)
            x0, y0 = min(a[0], b[0]), min(a[1], b[1])
            x1, y1 = max(a[0], b[0]), max(a[1], b[1])
            boxes["%02d_%s" % (i, tag)] = (int(x0), int(y0),
                                           max(int(x1), int(x0) + 3),
                                           max(int(y1), int(y0) + 3))
        names.append((i, cx, cz, rx, rz, best))
    res = METER.run(SHOT, boxes, overlay="shadow_boxes.png")
    print("%-4s %-22s %8s %8s %8s" % ("#", "footprint", "edge", "open", "dark%"))
    for (i, cx, cz, rx, rz, s) in names:
        e = res["%02d_edge" % i]["mean"]
        o = res["%02d_open" % i]["mean"]
        print("%-4d c=(%5.2f,%5.2f) r=(%4.2f,%4.2f) %8.1f %8.1f %7.1f%%  clear=%.2f"
              % (i, cx, cz, rx, rz, e, o, 100.0 * (o - e) / max(o, 1e-6), s))


if __name__ == "__main__":
    main()
