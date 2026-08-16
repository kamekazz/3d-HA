"""Dining room (room 4) build kit -- shared helpers.

Room-local feet: x 0(west)..19(east), z 0(north)..17(south), y 0(slab)..9(wall top).
Author every architectural piece in ROOM-LOCAL coordinates and hand it to
`place_local()`, which works out the pos that lands the bbox exactly there.
"""
import math
import os
import sys

sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")

from roomkit.glb import (Model, Material, Part, box, rounded_box, cylinder,  # noqa
                         prism, quad, sag_plane, torus)
from roomkit.place import place

ROOM = 4
W, D, H = 19.0, 17.0, 9.0          # west-east, north-south, floor-to-ceiling
OUT = os.path.dirname(os.path.abspath(__file__))


def glb(name):
    return os.path.join(OUT, name + ".glb")


def place_local(name, model, scale=1.0):
    """Save `model` (authored in room-local ft) and place it so it lands there."""
    path = glb(name.replace(" ", "_").lower())
    model.save(path)
    lo, hi = model.bounds()
    pos = ((lo[0] + hi[0]) / 2.0, lo[1], (lo[2] + hi[2]) / 2.0)
    r = place(name, path, ROOM, pos=pos, rot_y_deg=0.0, scale=scale)
    print("%-26s %s  bbox x%.2f..%.2f y%.2f..%.2f z%.2f..%.2f"
          % (name, r["action"], lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))
    return r


# ---------------------------------------------------------------- primitives

def face(p0, p1, p2, p3):
    """One-sided quad; CCW as seen from the front."""
    return Part([p0, p1, p2, p3], [(0, 1, 2), (0, 2, 3)])


def panel(x0, x1, y0, y1, z, facing):
    """Vertical quad in the XY plane at `z`. facing +1 => normal +Z, -1 => -Z."""
    if facing > 0:
        return face((x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z))
    return face((x1, y0, z), (x0, y0, z), (x0, y1, z), (x1, y1, z))


def panel_zy(z0, z1, y0, y1, x, facing):
    """Vertical quad in the ZY plane at `x`. facing +1 => normal +X."""
    if facing > 0:
        return face((x, y0, z1), (x, y0, z0), (x, y1, z0), (x, y1, z1))
    return face((x, y0, z0), (x, y0, z1), (x, y1, z1), (x, y1, z0))


def plane_xz(x0, x1, z0, z1, y, facing):
    """Horizontal quad. facing +1 => normal +Y (up), -1 => down."""
    if facing > 0:
        return face((x0, y, z1), (x1, y, z1), (x1, y, z0), (x0, y, z0))
    return face((x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1))


def slab(x0, x1, y0, y1, z0, z1):
    """Axis-aligned solid box given by its extents (double sided use)."""
    return box(x1 - x0, y1 - y0, z1 - z0), ((x0 + x1) / 2, y0, (z0 + z1) / 2)


def add_slab(m, mat, x0, x1, y0, y1, z0, z1):
    p, at = slab(x0, x1, y0, y1, z0, z1)
    m.add(p, mat, at=at)
    return m


# --------------------------------------------------------------- wall sweeps
# `profile` is a closed CCW list of (d, y): d = distance from the wall face into
# the room, y = height above the slab. The run goes from p0 to p1 in (x, z).

WALLS = {           # name -> (inward normal in XZ, wall plane coordinate)
    "north": ((0.0, 1.0), 0.0),      # z = 0, inward = +z
    "south": ((0.0, -1.0), D),       # z = D, inward = -z
    "west":  ((1.0, 0.0), 0.0),      # x = 0, inward = +x
    "east":  ((-1.0, 0.0), W),       # x = W, inward = -x
}


def wall_point(wall, t, d):
    """(x, z) at run parameter t along `wall`, d feet in from the wall face."""
    n, c = WALLS[wall]
    if wall in ("north", "south"):
        return (t, c + n[1] * d)
    return (c + n[0] * d, t)


def sweep(wall, t0, t1, profile, cap=True):
    """Extrude a (d, y) profile along a wall run.  Returns a solid Part."""
    n = len(profile)
    verts, tris = [], []
    for t in (t0, t1):
        for (d, y) in profile:
            x, z = wall_point(wall, t, d)
            verts.append((x, y, z))
    # side quads; orientation depends on run direction, but the pieces are thin
    # trim, so they are drawn double-sided and winding does not matter.
    for i in range(n):
        j = (i + 1) % n
        a, b, c, dd = i, j, n + j, n + i
        tris += [(a, b, c), (a, c, dd)]
    if cap:
        for i in range(1, n - 1):
            tris.append((0, i, i + 1))
            tris.append((n, n + i + 1, n + i))
    return Part(verts, tris)


def run_len(wall, t0, t1):
    return abs(t1 - t0)


# ------------------------------------------------------------------- shading

def lerp_hex(a, b, t):
    a = a.lstrip("#"); b = b.lstrip("#")
    out = ""
    for i in range(3):
        va = int(a[2 * i:2 * i + 2], 16)
        vb = int(b[2 * i:2 * i + 2], 16)
        out += "%02x" % round(va + (vb - va) * t)
    return "#" + out
