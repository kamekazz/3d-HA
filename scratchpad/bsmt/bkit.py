"""Basement furnishing kit -- room 1 Movie Room, room 2 Arcade Room.

Builds on scratchpad/shellpass/kit.py (ceiling / baseboards / door / window /
contact_shadow) and adds the upholstery primitives from scratchpad/lr5/kit4.py
(`puff`, `bolster`) plus the few helpers these two rooms need.

Every piece is idempotent by name through roomkit.place, so re-running a build
file rebuilds and re-places without stacking duplicates.
"""

import math
import os
import sys

sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\shellpass")

from kit import (  # noqa: F401,E402
    Model, Material, box, rounded_box, cylinder, prism, quad, sag_plane, torus,
    Part, R, mix, Rnd, bx, rect_down, rect_up, disc_down, ring_down, spans,
    wall_band, ceiling, baseboards, panel_door, door_unit, cased_opening,
    window_unit, contact_shadow, save_and_place as _sp, surfaces,
    TRIM, TRIM_D, CEIL, CEIL_FLAT, CAN_CONE, LENS, VENT, WHITEWD, DOORSHADE,
    BLACKMET, CHROME, GLASS, BB_H, BB_T, CROWN_H, CASE_W, DOOR_TOP, _blit,
)
from roomkit.place import place  # noqa: E402

blit = _blit          # `from bkit import *` skips underscore names

OUT =os.path.join(os.path.dirname(os.path.abspath(__file__)), "glb")


def save_and_place(name, m, room, fname=None):
    """Same seat as kit.save_and_place but writes into scratchpad/bsmt/glb."""
    path = os.path.join(OUT, (fname or name.replace(" ", "_")) + ".glb")
    os.makedirs(OUT, exist_ok=True)
    m.save(path)
    lo, hi = m.bounds()
    pos = ((lo[0] + hi[0]) / 2.0, lo[1], (lo[2] + hi[2]) / 2.0)
    res = place(name, path, room, pos=pos, rot_y_deg=0.0, scale=1.0)
    size = tuple(round(hi[i] - lo[i], 3) for i in range(3))
    kb = os.path.getsize(path) / 1024.0
    print(f"  {name:26s} size={size} pos=({pos[0]:.2f},{pos[1]:.2f},{pos[2]:.2f})"
          f"  {kb:6.1f} KB  {res['action']}")
    return {"name": name, "size_ft": list(size),
            "pos": [round(p, 3) for p in pos], "kb": round(kb, 1)}


# ------------------------------------------------------------ upholstery
def puff(w, h, d, r=None, seg=14, rings=7, nub=0.0, rnd=None, anchor="base"):
    """Box with every edge rounded, smooth-shaded -- cushions, pillows, seats."""
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
            c = a + seg
            e = b + seg
            t += [(a, c, b), (b, c, e)]
    return Part(v, t, smooth=True)


def cush(m, mat, x0, x1, y0, y1, z0, z1, r=0.14, nub=0.0, rnd=None):
    """A puff filling the given box."""
    m.add(puff(x1 - x0, y1 - y0, z1 - z0, r=r, nub=nub, rnd=rnd, anchor="base"),
          mat, at=((x0 + x1) / 2, y0, (z0 + z1) / 2))


def slab(m, mat, x0, x1, y0, y1, z0, z1, r=0.05, smooth=False):
    """A softly-rounded box -- upholstered bases, arms, ottoman bodies.

    Flat-shaded by default: rounded_box is smooth=True, and averaging normals
    across a big flat top puts a visible diagonal crease down every seat
    cushion (the round-C render).  The chamfer still reads at 3 segments."""
    part = rounded_box(x1 - x0, y1 - y0, z1 - z0, r=r, seg=3)
    part.smooth = smooth
    m.add(part, mat, at=((x0 + x1) / 2, y0, (z0 + z1) / 2))


def barrel(m, mat, cx, cz, r, thick, a0, a1, y0, h0, h1, steps=22, roll=0.14):
    """A swept upholstered band on an arc -- the wrap-around back of a barrel
    chair.  Height eases from h1 at the arc's midpoint to h0 at both ends, and a
    rolled top edge runs the whole way, so it reads as one shell rather than the
    string of separate lumps a ring of puffs gives."""
    for i in range(steps):
        t = (i + 0.5) / steps
        a = a0 + (a1 - a0) * t
        h = h0 + (h1 - h0) * math.sin(math.pi * t) ** 0.7
        w = abs(a1 - a0) * r / steps * 1.35            # overlap the neighbours
        x, z = cx + r * math.cos(a), cz + r * math.sin(a)
        ry = -(a + math.pi / 2)          # local +x tangent, local +z radial-in
        m.add(box(w, h - roll, thick), mat, at=(x, y0, z), rot_y=ry)
        if roll > 0.001:
            # a slimmer capping box, not a cylinder: consecutive cylinders on an
            # arc cross at an angle and read as a chain of beads
            m.add(box(w, roll, thick * 0.72), mat,
                  at=(x, y0 + h - roll, z), rot_y=ry)


def nailheads(m, mat, p0, p1, y, n, r=0.028):
    """A row of small domed studs from p0=(x,z) to p1=(x,z) at height y."""
    for i in range(n):
        t = (i + 0.5) / n
        x = p0[0] + (p1[0] - p0[0]) * t
        z = p0[1] + (p1[1] - p0[1]) * t
        m.add(cylinder(r, r * 0.9, 8), mat, at=(x, y, z), rot_x=R(90))


def leg(m, mat, cx, cz, h, w=0.15, taper=0.6):
    m.add(cylinder(w / 2, h, 8, r_top=w * taper / 2), mat, at=(cx, 0.0, cz))


# ------------------------------------------------------------ wall art
def framed(m, back, frame, wall, W, D, a0, a1, y0, y1, depth=0.06):
    """A flat panel with a thin frame, on `wall`, in that wall's own axis."""
    sub = Model()
    bx(sub, frame, a0, a1, y0, y1, 0.0, depth)
    bx(sub, back, a0 + 0.035, a1 - 0.035, y0 + 0.035, y1 - 0.035,
       depth, depth + 0.012)
    _blit(m, sub, wall, W, D, 0.0)
