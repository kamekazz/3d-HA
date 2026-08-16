"""Light-grey skins on the east and west walls.

The app lights the room with one directional sun (roomkit's --day puts it at
azimuth 155) plus a hemisphere light, and renders no bounce at all, so the two
side walls fall to a blue-grey ~#a4acb4 while the sun-facing north wall sits
near #f0f0ee.  The reference photo has all three walls within a few levels of
each other -- that difference is indirect light the renderer does not do.

These are 0.012 ft skins hung on the inside face of the east and west walls,
one-sided so they are invisible from outside the room and from above, carrying
the missing bounce as emissive.  Nothing else in the room changes.
"""

from common import *   # noqa

SKIN = Material("wallskin", "#e4e2de", roughness=0.95, emissive="#6f6f6f",
                double_sided=False)


def wash():
    m = Model()
    # west wall: inside face must look +x
    x = 0.010
    m.add(quad((x, 0, D), (x, 0, 0), (x, H, 0), (x, H, D)), SKIN)
    # east wall: inside face must look -x
    x = W - 0.010
    m.add(quad((x, 0, 0), (x, 0, D), (x, H, D), (x, H, 0)), SKIN)
    # south wall: inside face must look -z
    z = D - 0.010
    m.add(quad((W, 0, z), (0, 0, z), (0, H, z), (W, H, z)), SKIN)
    return m


if __name__ == "__main__":
    m = wash()
    path = os.path.join(OUT, "rios_wallwash.glb")
    m.save(path)
    lo, hi = m.bounds()
    pos = ((lo[0] + hi[0]) / 2, lo[1], (lo[2] + hi[2]) / 2)
    place("Rios Wall Wash", path, ROOM, pos=pos, rot_y_deg=0.0)
    print("Rios Wall Wash", tuple(round(hi[i] - lo[i], 3) for i in range(3)), pos)
