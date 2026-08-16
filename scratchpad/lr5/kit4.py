"""Round-4 helpers for the Living Room (room 5).

Round 4 is surfaces and soft goods only; the inventory, scale and layout were
adjudicated correct.  Three new primitives carry it:

* `puff`  -- a rounded CUBE (smooth-shaded), optionally nubbed.  Every
  upholstered part in rounds 1-3 was a `rounded_box`: rounded on the four
  vertical edges only, so from above and from the reference pose every cushion
  read as a planar chamfered slab.  A puff is rounded on all three axes, which
  is what makes a seat cushion read as plump.  `nub` displaces each vertex
  along its own radius by a small random amount; with smooth normals that is a
  soft shading mottle at ~0.2 ft pitch -- boucle, for 6 KB a cushion.

* `mottle` -- a flat field of 4-vertex SMOOTH quads in N materials.  Round 3
  wrote the rug as 4453 flat-shaded `box()`es and the file came out at 4.5 MB,
  three times the whole ROOM budget.  A smooth quad is 4 verts against a flat
  box's 36, so the same field costs ~2% of that.

* `coursed_seeds` -- Voronoi seeds laid out in COURSES rather than on a near
  square grid, with widths varying ~3:1, so the fieldstone has a horizontal
  grain instead of reading as near-equant crazy paving.
"""
import math
import random

from kit3 import *                     # noqa: F401,F403
from kit3 import Part, Material, Model, _shrink


# ======================================================================= puff
def puff(w, h, d, r=None, seg=14, rings=7, nub=0.0, rnd=None, anchor="base"):
    """Box with EVERY edge rounded (a rounded cube), smooth-shaded.

    `nub` gives each vertex a random radial offset; at rings=7/seg=14 the
    facets are ~0.2 ft across, so a 0.02 ft offset tilts each one by a few
    degrees -- a soft woven mottle rather than a mirror-smooth pillow.
    """
    if r is None:
        r = min(w, h, d) * 0.42
    r = max(0.02, min(r, w / 2 - 1e-3, h / 2 - 1e-3, d / 2 - 1e-3))
    ex, ey, ez = w / 2 - r, h / 2 - r, d / 2 - r
    y0 = h / 2 if anchor == "base" else 0.0
    v = []
    for i in range(rings + 1):
        phi = math.pi * i / rings
        ny, sr = math.cos(phi), math.sin(phi)
        for j in range(seg):
            th = 2 * math.pi * j / seg
            nx, nz = sr * math.cos(th), sr * math.sin(th)
            rr = r + (rnd.uniform(-nub, nub) if (nub and rnd) else 0.0)
            v.append((nx * rr + (ex if nx >= 0 else -ex),
                      ny * rr + (ey if ny >= 0 else -ey) + y0,
                      nz * rr + (ez if nz >= 0 else -ez)))
    t = []
    for i in range(rings):
        for j in range(seg):
            a = i * seg + j
            b = i * seg + (j + 1) % seg
            c = a + seg
            e = b + seg
            t += [(a, c, b), (b, c, e)]
    return Part(v, t, smooth=True)


def bolster(length, r, seg=14, rings=6, nub=0.0, rnd=None):
    """A capsule lying along X -- body pillows, rolled throws, bolsters."""
    return puff(length, 2 * r, 2 * r, r=r, seg=seg, rings=rings, nub=nub,
                rnd=rnd, anchor="center")


# ===================================================================== mottle
def mottle(m, w, d, cell, mats, at=(0, 0, 0), rot_y=0.0, rnd=None, wobble_xz=0.0):
    """A flat field of per-cell coloured quads (4 SMOOTH verts each).

    Used for the rug pile and for the visible top decks of upholstery.  All
    normals point +Y, so rendered luminance tracks the material albedo almost
    exactly -- which is how the spread can be aimed at a metered target.
    """
    rnd = rnd or random.Random(1)
    nx = max(1, int(round(w / cell)))
    nz = max(1, int(round(d / cell)))
    cw, cd = w / nx, d / nz
    for iz in range(nz):
        z0 = -d / 2 + cd * iz
        for ix in range(nx):
            x0 = -w / 2 + cw * ix
            jx = rnd.uniform(-wobble_xz, wobble_xz) if wobble_xz else 0.0
            jz = rnd.uniform(-wobble_xz, wobble_xz) if wobble_xz else 0.0
            q = [(x0 + jx, 0.0, z0 + jz), (x0 + cw + jx, 0.0, z0 + jz),
                 (x0 + cw + jx, 0.0, z0 + cd + jz), (x0 + jx, 0.0, z0 + cd + jz)]
            m.add(Part(q, [(0, 2, 1), (0, 3, 2)], smooth=True),
                  mats[rnd.randrange(len(mats))], at=at, rot_y=rot_y)


def ramp(base, n, spread, warm=0.0):
    """N hex colours evenly spanning base +/- spread (0-255 units)."""
    r, g, b = (int(base[i:i + 2], 16) for i in (1, 3, 5))
    out = []
    for k in range(n):
        f = (k / (n - 1.0) - 0.5) * 2.0 if n > 1 else 0.0
        dv = f * spread
        out.append("#%02x%02x%02x" % (
            max(0, min(255, int(r + dv + warm * f))),
            max(0, min(255, int(g + dv))),
            max(0, min(255, int(b + dv - warm * f)))))
    return out


# ================================================================ fieldstone
def pillow_s(poly, z0, h, rim=0.028, dome=0.008):
    """kit3's bevelled stone pillow, SMOOTH-shaded.

    Two reasons.  (a) Payload: flat shading duplicates a vertex per face, and
    at 65 stones the flat version alone was 260 KB of a 300 KB piece budget;
    smooth is ~1.5 KB a stone.  (b) Look: photo f's clean lit stone meters
    sd 8, i.e. the stones are soft painted-over blobs whose edges are rolled,
    not faceted plates.  Flat shading plus a bright joint gave a hard white
    plate with a black outline -- exactly what metered sd 34.
    """
    p = pillow(poly, z0, h, rim=rim, dome=dome)
    p.smooth = True
    return p


def coursed_seeds(x0, x1, y0, y1, rnd, course=0.85, pitch=0.90,
                  wlo=0.60, whi=1.75, hlo=0.80, hhi=1.26, cut=None):
    """Voronoi seeds in COURSES: horizontal grain, ~3:1 area variation.

    Round 3 seeded a near-square grid, so the cells came out near-equant and
    the face read as crazy paving.  Real painted fieldstone on this breast runs
    in broken courses about 0.85 ft tall.
    """
    seeds = []
    y = y0
    while y < y1 - 1e-6:
        h = course * rnd.uniform(hlo, hhi)
        if y1 - (y + h) < course * 0.5:
            h = y1 - y
        cy = y + h / 2
        x = x0
        while x < x1 - 1e-6:
            w = pitch * rnd.uniform(wlo, whi)
            if x1 - (x + w) < pitch * 0.45:
                w = x1 - x
            sx = x + w / 2 + rnd.uniform(-0.05, 0.05)
            sy = cy + rnd.uniform(-0.16, 0.16) * h
            if not (cut and cut[0] < sx < cut[2] and cut[1] < sy < cut[3]):
                seeds.append((sx, sy))
            x += w
        y += h
    return seeds


# ==================================================================== shadows
def smooth_shadow4(m, foot, pad=1.00, y_base=None, mats=None, a0=None, core=True):
    """kit3's `smooth_shadow` with the solid core made optional.

    The core is `rings[0]` painted at the full a0, i.e. a HARD-EDGED filled
    polygon.  Under a sofa that is invisible (the sofa covers it), but round 3
    also put one under the coffee table's open X-frame at a0 0.22, and from the
    plan pose its boundary drew a hard rectangle across the rug -- one of the
    two "seams splitting the rug into differently-toned panels".  Wide ambient
    halos over open furniture now start faded.
    """
    from kit3 import SH_Y, shadow_mats, SH_MATS, _offset, _fan
    y_base = SH_Y if y_base is None else y_base
    mats = mats or (shadow_mats(a0) if a0 else SH_MATS)
    n = len(mats)
    rings = [_offset(foot, pad * k / float(n)) for k in range(n + 1)]
    if core:
        _fan(m, clip_room(rings[0]), y_base, mats[0])
    q = len(foot)
    for k in range(n):
        inner, outer = rings[k], rings[k + 1]
        for i in range(q):
            j = (i + 1) % q
            for tri in ((inner[i], outer[i], outer[j]),
                        (inner[i], outer[j], inner[j])):
                _fan(m, clip_room(list(tri)), y_base, mats[k])


def plate(poly, z0, h, rim=0.032, tilt=(0.0, 0.0), skirt=True):
    """A fieldstone as photo f actually shows one: a FLAT angular plate with a
    narrow chamfered edge, flat-shaded.

    Round 3 used a three-ring domed `pillow`, and round 4's first pass kept it
    smooth-shaded; both spread a soft value gradient across every stone, which
    is where the render's sd 19-34 came from against the photo's 8.9.  In
    photo_stonecrop.png the stones are flat painted plates separated by thin
    seams -- essentially no within-stone gradient, and what variance there is
    is stone-TO-stone, from each plate sitting at a slightly different angle.
    `tilt` reproduces exactly that and nothing else.

    Cost: 3n triangles instead of 5n, and only one ring instead of three.
    """
    n = len(poly)
    cx = sum(p[0] for p in poly) / n
    cy = sum(p[1] for p in poly) / n
    inn = _shrink(poly, rim)
    def zc(x, y):
        return z0 + h + tilt[0] * (x - cx) + tilt[1] * (y - cy)
    v = [(x, y, z0) for (x, y) in poly] + [(x, y, zc(x, y)) for (x, y) in inn]
    v.append((cx, cy, zc(cx, cy)))
    c = 2 * n
    t = []
    for i in range(n):
        j = (i + 1) % n
        if skirt:
            t += [(i, j, i + n), (j, j + n, i + n)]  # chamfer
        t.append((i + n, j + n, c))                  # flat cap
    return Part(v, t)
