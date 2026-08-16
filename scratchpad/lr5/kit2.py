"""Round-2 shared helpers for the Living Room (room 5).

The room was re-traced under round 1: it is now 20.49 x 16.96 ft with the
NORTH-WEST corner chamfered off at 45 degrees, and the fireplace lives on that
chamfer (the floor plan draws a thickened wall there, and photo f/Kitchen F both
show the stone breast on a wall angled to the TV wall).

Room-local polygon, CCW as the store normalised it:

    idx 0  S   (20.49,16.96) -> (0,16.96)     20.49 ft
    idx 1  W   (0,16.96)     -> (0,4.96)      12.00 ft
    idx 2  CH  (0,4.96)      -> (4.87,0)       6.95 ft   <- fireplace
    idx 3  N   (4.87,0)      -> (20.49,0)     15.62 ft   <- TV + slider
    idx 4  E   (20.49,0)     -> (20.49,16.96) 16.96 ft
"""
import math
import os
import sys

sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
from roomkit.glb import (Model, Material, Part, box, rounded_box, cylinder,
                         prism, quad, sag_plane, torus)
from roomkit.place import place as _place, _req

req = _req          # `from kit2 import *` skips underscore names

OUT = r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\lr5"
ROOM = 5
RW, RD, RH = 20.49, 16.96, 9.0

POLY = [(20.49, 16.96), (0.0, 16.96), (0.0, 4.96), (4.87, 0.0), (20.49, 0.0)]
EDGES = [(POLY[i], POLY[(i + 1) % len(POLY)]) for i in range(len(POLY))]
S, W, CH, N, E = 0, 1, 2, 3, 4


# ------------------------------------------------------------------ plumbing
def save(m, name):
    p = os.path.join(OUT, name + ".glb")
    m.save(p)
    lo, hi = m.bounds()
    print("  %-16s lo=(%.2f,%.2f,%.2f) size=(%.2f,%.2f,%.2f)" %
          (name, lo[0], lo[1], lo[2], hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]))
    return p


def put(name, glb, pos, rot=0.0, scale=1.0):
    r = _place(name, glb, ROOM, pos=pos, rot_y_deg=rot, scale=scale)
    print("  place %-24s %s at (%.2f,%.2f,%.2f) rot %.1f" %
          (name, r["action"], pos[0], pos[1], pos[2], rot))
    return r


def put_anchor(name, m, glb, model_pt, room_pt, rot_deg=0.0):
    """Place a rotated piece by an ANCHOR rather than by its bbox centre.

    objects.js seats a model on its bbox centre, so anything whose bbox is
    asymmetric (a throw hanging over the back, a chaise return) ends up off the
    wall by however far the drape reaches.  `model_pt` (mx, mz) is the point in
    model space -- e.g. the middle of the sofa's back rail -- that must land on
    room-local `room_pt`.
    """
    lo, hi = m.bounds()
    cx, cz = (lo[0] + hi[0]) / 2, (lo[2] + hi[2]) / 2
    th = math.radians(rot_deg)
    dx, dz = model_pt[0] - cx, model_pt[1] - cz
    wx = dx * math.cos(th) + dz * math.sin(th)
    wz = -dx * math.sin(th) + dz * math.cos(th)
    put(name, glb, (room_pt[0] - wx, lo[1], room_pt[1] - wz), rot_deg)


def put_in_place(name, m, glb):
    """For pieces AUTHORED DIRECTLY IN ROOM-LOCAL FEET (ceiling, baseboards,
    shadow decals).  objects.js centres a model on its own bbox in XZ and seats
    min-Y at pos.y, so feeding back the authored bbox reproduces the authoring
    coordinates exactly."""
    lo, hi = m.bounds()
    put(name, glb, ((lo[0] + hi[0]) / 2, lo[1], (lo[2] + hi[2]) / 2), 0.0)


# ------------------------------------------------------------------ edges
def edge_normal(a, b):
    """Inward unit normal of a polygon edge, plus its length."""
    dx, dz = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dz)
    return (-dz / L, dx / L), L


def edge_angle(i):
    n, _ = edge_normal(*EDGES[i])
    return math.degrees(math.atan2(n[0], n[1]))


def on_edge(i, t, out=0.0, ):
    """Room-local (x, z) `t` feet along edge i from its first vertex, pushed
    `out` feet into the room along the inward normal."""
    (a, b) = EDGES[i]
    n, L = edge_normal(a, b)
    d = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
    return (a[0] + d[0] * t + n[0] * out, a[1] + d[1] * t + n[1] * out)


def sweep_edge(m, mat, profile, i, y=0.0, t0=0.0, t1=None, inset=0.0):
    """Sweep a (vertical, out-from-wall) profile along part of edge i."""
    a, b = EDGES[i]
    n, L = edge_normal(a, b)
    if t1 is None:
        t1 = L
    seg = t1 - t0
    if seg <= 0.02:
        return
    th = math.atan2(n[0], n[1])
    run = (-math.cos(th), math.sin(th))
    d = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
    p0 = (a[0] + d[0] * t0 + n[0] * inset, a[1] + d[1] * t0 + n[1] * inset)
    p1 = (a[0] + d[0] * t1 + n[0] * inset, a[1] + d[1] * t1 + n[1] * inset)
    anchor = p0 if (run[0] * d[0] + run[1] * d[1]) > 0 else p1
    m.add(prism(profile, seg), mat, at=(anchor[0], y, anchor[1]),
          rot_z=math.pi / 2, rot_y=th)


def run_edge_gaps(m, mat, profile, i, y=0.0, gaps=(), inset=0.0):
    """Sweep along the whole of edge i minus the (t0,t1) spans in `gaps`."""
    _, L = edge_normal(*EDGES[i])
    lo = 0.0
    for (g0, g1) in sorted(gaps):
        if g0 > lo:
            sweep_edge(m, mat, profile, i, y, lo, min(g0, L), inset)
        lo = max(lo, g1)
    if lo < L:
        sweep_edge(m, mat, profile, i, y, lo, L, inset)


# ------------------------------------------------------------------ surfaces
def disc_down(r, seg=18, y=0.0):
    """Flat disc whose single face looks DOWN (a cylinder would show its top cap
    in the plan/dollhouse view, where the ceiling must be invisible)."""
    v = [(0.0, y, 0.0)]
    for k in range(seg):
        a = 2 * math.pi * k / seg
        v.append((r * math.cos(a), y, r * math.sin(a)))
    return Part(v, [(0, 1 + k, 1 + (k + 1) % seg) for k in range(seg)])


def face_slab(poly, z0, z1, dome=0.0):
    """Extrude a CCW polygon [(x, y)] in the wall-face plane from z0 to z1.

    `dome` pushes a centre vertex further out so the front face is faceted
    rather than flat -- what makes painted fieldstone read as stone.
    """
    n = len(poly)
    v = [(x, y, z0) for (x, y) in poly] + [(x, y, z1) for (x, y) in poly]
    t = []
    for i in range(n):
        j = (i + 1) % n
        t += [(i, j, i + n), (j, j + n, i + n)]
    if dome:
        cx = sum(p[0] for p in poly) / n
        cy = sum(p[1] for p in poly) / n
        c = len(v)
        v.append((cx, cy, z1 + dome))
        for i in range(n):
            t.append((n + i, n + (i + 1) % n, c))
    else:
        for i in range(1, n - 1):
            t.append((n, n + i, n + i + 1))
    return Part(v, t)


# ------------------------------------------------------------------ contact shadows
# The app renders no shadows for generated geometry, so every piece floats.
# A soft dark decal is baked under each footprint: three nested outlines in ONE
# translucent black material, so the overlap gives a penumbra without textures.
# They sit just above the rug pile (0.079) so one piece serves rug and bare
# floor alike -- an inch of float that no camera in this app can resolve.
SHADOW_Y = 0.086
SHADOW = Material("lrshadow", "#050506", roughness=1.0, opacity=0.165,
                  double_sided=True)
PADS = (0.90, 0.42, 0.07)


def foot_rect(cx, cz, w, d, rot_deg=0.0, seg=1):
    """Footprint polygon of a (rotated) rectangle, CCW in (x, z)."""
    r = math.radians(rot_deg)
    c, s = math.cos(r), math.sin(r)
    out = []
    for (dx, dz) in ((-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2)):
        out.append((cx + dx * c + dz * s, cz - dx * s + dz * c))
    return out


def foot_disc(cx, cz, r, seg=14):
    return [(cx + r * math.cos(2 * math.pi * k / seg),
             cz + r * math.sin(2 * math.pi * k / seg)) for k in range(seg)]


def clip_room(poly, inset=0.03):
    """Sutherland-Hodgman against the room polygon so a penumbra never smears
    through a wall and out onto the lawn."""
    for (a, b) in EDGES:
        n, _ = edge_normal(a, b)
        c = n[0] * a[0] + n[1] * a[1] + inset
        out, k = [], len(poly)
        if k == 0:
            return []
        for i in range(k):
            p, q = poly[i], poly[(i + 1) % k]
            dp = n[0] * p[0] + n[1] * p[1] - c
            dq = n[0] * q[0] + n[1] * q[1] - c
            if dp >= 0:
                out.append(p)
            if (dp < 0) != (dq < 0) and abs(dq - dp) > 1e-12:
                t = dp / (dp - dq)
                out.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
        poly = out
    return poly


def soft_shadow(m, foot, pads=PADS, y_base=SHADOW_Y):
    """Three nested, room-clipped outlines of `foot` in one translucent black
    material: the overlap is the penumbra.  This is the whole contact-shadow
    story -- the app draws no real shadows, so without it every piece floats."""
    for k, pad in enumerate(pads):
        cx = sum(p[0] for p in foot) / len(foot)
        cz = sum(p[1] for p in foot) / len(foot)
        ring = []
        for (x, z) in foot:
            dx, dz = x - cx, z - cz
            L = math.hypot(dx, dz) or 1.0
            ring.append((x + dx / L * pad, z + dz / L * pad))
        ring = clip_room(ring)
        if len(ring) < 3:
            continue
        rx = sum(p[0] for p in ring) / len(ring)
        rz = sum(p[1] for p in ring) / len(ring)
        y = y_base - 0.004 + 0.002 * k
        n = len(ring)
        v = [(rx, y, rz)] + [(p[0], y, p[1]) for p in ring]
        m.add(Part(v, [(0, 1 + (i + 1) % n, 1 + i) for i in range(n)]), SHADOW)
