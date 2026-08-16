"""Room 13 (Guest Room) furnishing kit.

Builds on scratchpad/shellpass/kit.py (ceiling / baseboards / door + window
units / wall_band / bx / Rnd / materials) and adds the pieces the living-room
round-4 build proved out:

  * `puff`   -- rounded cube, smooth shaded, optional per-vertex nub.  Every
                cushion, pillow and duvet mound in this room is one.
  * `shadow` -- contact shadow as DISJOINT annuli, each painted with its own
                absolute alpha off a smooth curve, all at ONE y.  Stacked
                translucent layers do not composite at room scale (the depth
                buffer rejects them) and nested hard rings read as a bullseye.
  * `mottle` -- flat per-cell coloured quads for tonal fields at near-flat cost.

ROOM 13 ORIENTATION (derived in the report; the shell pass had z reversed):
    NORTH (z=0)     headboard wall, wreath over the bed
    WEST  (x=0)     exterior -- window at z 1.75..4.55, framed collage south
                    of it, small table + lamp in the NW corner
    EAST  (x=12.4)  dresser z 1.90..6.80 with the round mirror over it, then
                    the entry door z 8.05..10.80 onto the 2F hallway
    SOUTH (z=10.8)  TV at the east end, closet bypass doors, two small frames
"""

import math
import os
import sys

sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\shellpass")
sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")

from kit import *                                    # noqa: F401,F403
from kit import (Model, Material, Part, box, rounded_box, cylinder, prism,
                 quad, sag_plane, torus, bx, rect_down, rect_up, disc_down,
                 ring_down, wall_band, spans, mix, Rnd, R, place,
                 ceiling, baseboards, window_unit, door_unit, cased_opening,
                 panel_door, _blit, BB_H, BB_T, CASE_W, CEIL, CEIL_FLAT,
                 TRIM, TRIM_D, WHITEWD, DOORSHADE, BLACKMET, CHROME, GLASS)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "glb")
os.makedirs(OUT, exist_ok=True)

blit = _blit          # `from gkit import *` skips underscore names

ROOM, W, D, H = 13, 12.4, 10.8, 8.0

# ------------------------------------------------------------ architecture
RAIL = 3.32                     # chair-rail top, straight off the photos
WIN = (1.75, 4.55)              # west wall, local z
WIN_SILL, WIN_HEAD = 2.55, 6.45
DOOR = (8.05, 10.78)            # east wall, local z (entry, onto the hallway)
CLOSET = (3.55, 8.35)           # south wall, local x (bypass doors)
DOOR_H = 6.78

BED = (2.55, 8.15, 0.16, 7.32)  # x0, x1, z_head, z_foot
DRESSER = (10.82, 12.36, 1.90, 6.80)   # x0, x1, z0, z1  (east wall)


# --------------------------------------------------------------- placement
def save_and_place(name, m, fname=None, pos=None, rot=0.0):
    """Author in ROOM-LOCAL feet, place at rot 0 on the bbox seat."""
    path = os.path.join(OUT, (fname or name.replace(" ", "_").lower()) + ".glb")
    m.save(path)
    lo, hi = m.bounds()
    p = pos or ((lo[0] + hi[0]) / 2.0, lo[1], (lo[2] + hi[2]) / 2.0)
    res = place(name, path, ROOM, pos=p, rot_y_deg=rot, scale=1.0)
    kb = os.path.getsize(path) / 1024.0
    size = tuple(round(hi[i] - lo[i], 2) for i in range(3))
    print("  %-26s %-22s %6.0f KB  %s" % (name, size, kb, res["action"]))
    return {"name": name, "size_ft": list(size), "kb": round(kb),
            "pos": [round(v, 3) for v in p], "rot": rot}


# --------------------------------------------------------------------- puff
def puff(w, h, d, r=None, seg=14, rings=7, nub=0.0, rnd=None, anchor="base"):
    """Box with every edge rounded, smooth-shaded; `nub` mottles the surface."""
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
            rr = r + (rnd.f(-nub, nub) if (nub and rnd) else 0.0)
            v.append((nx * rr + (ex if nx >= 0 else -ex),
                      ny * rr + (ey if ny >= 0 else -ey) + y0,
                      nz * rr + (ez if nz >= 0 else -ez)))
    t = []
    for i in range(rings):
        for j in range(seg):
            a = i * seg + j
            b = i * seg + (j + 1) % seg
            t += [(a, a + seg, b), (b, a + seg, b + seg)]
    return Part(v, t, smooth=True)


def bolster(length, r, seg=14, rings=6, nub=0.0, rnd=None):
    return puff(length, 2 * r, 2 * r, r=r, seg=seg, rings=rings, nub=nub,
                rnd=rnd, anchor="center")


# ------------------------------------------------------------- flat fields
def mottle(m, mat_list, x0, x1, z0, z1, cell, y, rnd):
    """Flat per-cell quads facing +Y -- a tonal field at near-flat-plane cost."""
    nx = max(1, int(round((x1 - x0) / cell)))
    nz = max(1, int(round((z1 - z0) / cell)))
    cw, cd = (x1 - x0) / nx, (z1 - z0) / nz
    for iz in range(nz):
        for ix in range(nx):
            a, b = x0 + cw * ix, z0 + cd * iz
            q = [(a, y, b), (a + cw, y, b), (a + cw, y, b + cd), (a, y, b + cd)]
            m.add(Part(q, [(0, 2, 1), (0, 3, 2)], smooth=True),
                  mat_list[int(rnd.f(0, len(mat_list) - 1e-6))])


def ramp(base, n, spread):
    """n hex colours evenly spanning base +/- spread (0-255 units)."""
    r, g, b = (int(base.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
    out = []
    for k in range(n):
        f = (k / (n - 1.0) - 0.5) * 2.0 if n > 1 else 0.0
        out.append("#%02x%02x%02x" % tuple(
            max(0, min(255, int(round(c + f * spread)))) for c in (r, g, b)))
    return out


# ---------------------------------------------------------- contact shadow
SH_Y = 0.016
SH_N = 8
SH_GAMMA = 1.5


def shadow_mats(a0=0.50, tag="g"):
    return [Material("gsh%s%d" % (tag, k), "#0a0a0b", roughness=1.0,
                     opacity=round(a0 * (1.0 - (j + 0.5) / SH_N) ** SH_GAMMA, 4),
                     double_sided=True)
            for k, j in enumerate(range(SH_N))]


def _clip(poly, inset=0.045):
    """Sutherland-Hodgman clip to the room rect -- a penumbra that pokes
    through a wall is visible from outside the room."""
    lo_x, hi_x, lo_z, hi_z = inset, W - inset, inset, D - inset
    for (ax, az, keep) in ((1, 0, lambda p: p[0] >= lo_x),
                           (-1, 0, lambda p: p[0] <= hi_x),
                           (0, 1, lambda p: p[1] >= lo_z),
                           (0, -1, lambda p: p[1] <= hi_z)):
        if not poly:
            return []
        out = []
        for i in range(len(poly)):
            a, b = poly[i], poly[(i + 1) % len(poly)]
            ka, kb = keep(a), keep(b)
            if ka:
                out.append(a)
            if ka != kb:
                if ax:
                    xc = lo_x if ax > 0 else hi_x
                    t = (xc - a[0]) / (b[0] - a[0])
                    out.append((xc, a[1] + t * (b[1] - a[1])))
                else:
                    zc = lo_z if az > 0 else hi_z
                    t = (zc - a[1]) / (b[1] - a[1])
                    out.append((a[0] + t * (b[0] - a[0]), zc))
        poly = out
    return poly


def _fan(m, poly, y, mat):
    if len(poly) < 3:
        return
    m.add(Part([(p[0], y, p[1]) for p in poly],
               [(0, 1 + i, i) for i in range(1, len(poly) - 1)]), mat)


def _grow(foot, d):
    cx = sum(p[0] for p in foot) / len(foot)
    cz = sum(p[1] for p in foot) / len(foot)
    out = []
    for (x, z) in foot:
        dx, dz = x - cx, z - cz
        L = math.hypot(dx, dz) or 1.0
        out.append((x + dx / L * d, z + dz / L * d))
    return out


def shadow(m, foot, pad=0.85, y=SH_Y, a0=0.50, core=True, tag="g"):
    """Soft contact shadow under `foot` (a CCW list of (x,z) room-local ft)."""
    mats = shadow_mats(a0, tag)
    n = len(mats)
    rings = [_grow(foot, pad * k / float(n)) for k in range(n + 1)]
    if core:
        _fan(m, _clip(rings[0]), y, mats[0])
    q = len(foot)
    for k in range(n):
        inner, outer = rings[k], rings[k + 1]
        for i in range(q):
            j = (i + 1) % q
            for tri in ((inner[i], outer[i], outer[j]),
                        (inner[i], outer[j], inner[j])):
                _fan(m, _clip(list(tri)), y, mats[k])


def rect_foot(x0, x1, z0, z1):
    return [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]


def disc_foot(cx, cz, r, seg=14):
    return [(cx + r * math.cos(2 * math.pi * i / seg),
             cz + r * math.sin(2 * math.pi * i / seg)) for i in range(seg)]
