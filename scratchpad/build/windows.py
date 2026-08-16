"""Double-hung windows with white 2in faux-wood blinds, flush on the inside wall
face (we deliberately do not cut real openings -- the app draws a hardcoded teal
slab for those, and every judged viewpoint is from inside).

Blinds are lowered to ~55% and the clear strip below shows lawn, a white porch
rail and foliage: that is what `Dining A.jpg`, the primary reference, shows, and
it is what stops two sunless walls from reading as a grey box.

South wall: two, with the clock between them.  West wall: three, bay-tight.
"""
import math
import sys

from dk import *  # noqa
import tone
from shell import WIN_W, WIN_H, WIN_Y0, WIN_Y1, SOUTH_WIN, WEST_WIN

CASE = 0.30          # casing stock width
CASE_D = 0.105       # how far the casing stands off the wall
STOOL_D = 0.30
GLASS_W = WIN_W - 2 * CASE          # 2.42
GLASS_Y0, GLASS_Y1 = WIN_Y0, WIN_Y1 - CASE
GH = GLASS_Y1 - GLASS_Y0
BLIND_BOT = GLASS_Y0 + 0.44 * GH
SLAT = 0.175


def mats(surface):
    def M(name, alb, target, **kw):
        e, s = tone.emissive_for(target, alb, surface)
        return Material(name + "_" + surface, alb, emissive=e,
                        emissive_strength=s, **kw)
    return {
        "trim": M("wtrim", "#ffffff", 208, roughness=0.85),
        "blind": M("blind", "#ffffff", 203, roughness=0.9),
        "line": M("bline", "#ffffff", 138, roughness=0.9),
        "sky": M("wsky", "#eaf0f4", 243, roughness=0.5, double_sided=False),
        "lawn": M("wlawn", "#94ad7c", 239, roughness=0.5, double_sided=False),
        "fence": M("wfence", "#f0f2ee", 250, roughness=0.5, double_sided=False),
        "tree": M("wtree", "#7d9a6d", 232, roughness=0.5, double_sided=False),
    }


def band(wall, t0, t1, y0, y1, d0, d1):
    if wall == "north":
        return slab(t0, t1, y0, y1, d0, d1)
    if wall == "south":
        return slab(t0, t1, y0, y1, D - d1, D - d0)
    if wall == "west":
        return slab(d0, d1, y0, y1, t0, t1)
    return slab(W - d1, W - d0, y0, y1, t0, t1)


def one_window(m, wall, centre, mt):
    def put(t0, t1, y0, y1, d0, d1, mat):
        p, at = band(wall, t0, t1, y0, y1, d0, d1)
        m.add(p, mat, at=at)

    a, b = centre - WIN_W / 2, centre + WIN_W / 2
    ga, gb = a + CASE, b - CASE

    # what is outside, painted in bands on the pane plane
    put(ga, gb, GLASS_Y0, GLASS_Y1, 0.040, 0.050, mt["sky"])
    put(ga, gb, GLASS_Y0, GLASS_Y0 + 0.72, 0.050, 0.056, mt["lawn"])
    put(ga, gb, GLASS_Y0 + 0.72, GLASS_Y0 + 1.02, 0.050, 0.056, mt["fence"])
    put(ga, gb, GLASS_Y0 + 1.02, GLASS_Y1, 0.050, 0.056, mt["tree"])
    # the sash: one meeting rail and thin stiles
    put(ga, gb, GLASS_Y0 + GH * 0.52, GLASS_Y0 + GH * 0.52 + 0.085,
        0.056, 0.068, mt["trim"])

    # blinds, lowered to BLIND_BOT
    put(ga, gb, GLASS_Y1 - 0.28, GLASS_Y1, 0.052, 0.150, mt["blind"])   # headrail
    n = int((GLASS_Y1 - 0.30 - BLIND_BOT) / SLAT)
    for i in range(n):
        y = BLIND_BOT + i * SLAT
        put(ga + 0.02, gb - 0.02, y, y + SLAT - 0.035, 0.062, 0.140, mt["blind"])
        put(ga + 0.02, gb - 0.02, y + SLAT - 0.035, y + SLAT, 0.058, 0.100,
            mt["line"])
    # bottom rail sits a touch heavier than a slat
    put(ga + 0.01, gb - 0.01, BLIND_BOT - 0.10, BLIND_BOT, 0.060, 0.145, mt["blind"])
    # ladder tapes
    for f in (0.27, 0.73):
        t = ga + GLASS_W * f
        put(t - 0.035, t + 0.035, BLIND_BOT, GLASS_Y1 - 0.28, 0.140, 0.152,
            mt["blind"])

    # casing: two legs, head, cap and the stool.  The chair rail runs in under
    # the stool and does the apron's job, exactly as the photo shows.
    put(a, a + CASE, WIN_Y0 - 0.02, WIN_Y1, 0.0, CASE_D, mt["trim"])
    put(b - CASE, b, WIN_Y0 - 0.02, WIN_Y1, 0.0, CASE_D, mt["trim"])
    put(a, b, WIN_Y1 - CASE, WIN_Y1, 0.0, CASE_D, mt["trim"])
    put(a - 0.055, b + 0.055, WIN_Y1, WIN_Y1 + 0.10, 0.0, CASE_D + 0.05, mt["trim"])
    put(a - 0.14, b + 0.14, WIN_Y0 - 0.115, WIN_Y0, 0.0, STOOL_D, mt["trim"])


def build(wall, centres):
    mt = mats(wall)
    m = Model()
    for c in centres:
        one_window(m, wall, c, mt)
    return m


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which in ("all", "south"):
        place_local("Dining Windows South", build("south", SOUTH_WIN))
    if which in ("all", "west"):
        place_local("Dining Windows West", build("west", WEST_WIN))
