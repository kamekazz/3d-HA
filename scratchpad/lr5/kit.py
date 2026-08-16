"""Shared helpers for the Living Room (room 5) build."""
import sys, math, os
sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
from roomkit.glb import Model, Material, box, rounded_box, cylinder, prism, quad, sag_plane, torus
from roomkit.place import place as _place

OUT = r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\lr5"
ROOM = 5
RW, RD, RH = 30.5, 17.0, 9.0          # room width (x), depth (z), wall height


def save(m, name):
    p = os.path.join(OUT, name + ".glb")
    m.save(p)
    lo, hi = m.bounds()
    print(name, "bounds lo=(%.2f,%.2f,%.2f) hi=(%.2f,%.2f,%.2f)" % (lo + hi),
          "size=(%.2f,%.2f,%.2f)" % (hi[0]-lo[0], hi[1]-lo[1], hi[2]-lo[2]))
    return p


def put(name, glb, pos, rot=0.0, scale=1.0):
    r = _place(name, glb, ROOM, pos=pos, rot_y_deg=rot, scale=scale)
    print("  place", name, r["action"], "at", pos, "rot", rot)
    return r


# ---------------------------------------------------------------- sweeps
def sweep(profile, length, mat, m, wall, at, flip=False):
    """Sweep a (vertical, depth) profile along a wall.

    profile: [(v, u)] with v vertical (feet, sign as authored) and u the
    distance out from the wall face.  wall is 'n'|'s'|'e'|'w'; `at` is the
    (x, y, z) start corner in model space of the run's origin.
    """
    part = prism(profile, length)
    rz = math.pi / 2
    ry = {"n": 0.0, "s": math.pi, "e": -math.pi / 2, "w": math.pi / 2}[wall]
    m.add(part, mat, at=at, rot_z=rz, rot_y=ry)
    return m


def run_with_gaps(m, mat, profile, wall, y, span, gaps, fixed, pad=0.0):
    """Emit sweep segments along `span`=(a,b) minus `gaps`=[(a,b)] on one wall.

    `fixed` is the wall's constant coordinate.  For n/s walls the run is along
    x and `fixed` is z; for e/w it is along z and `fixed` is x.
    """
    a, b = span
    cuts = []
    lo = a
    for (g0, g1) in sorted(gaps):
        if g0 > lo:
            cuts.append((lo, min(g0, b)))
        lo = max(lo, g1)
    if lo < b:
        cuts.append((lo, b))
    for (c0, c1) in cuts:
        L = c1 - c0
        if L <= 0.02:
            continue
        if wall == "n":      # run goes -x from `at`
            m.add(prism(profile, L), mat, at=(c1, y, fixed), rot_z=math.pi/2, rot_y=0.0)
        elif wall == "s":    # run goes +x from `at`
            m.add(prism(profile, L), mat, at=(c0, y, fixed), rot_z=math.pi/2, rot_y=math.pi)
        elif wall == "e":    # run goes -z from `at`
            m.add(prism(profile, L), mat, at=(fixed, y, c1), rot_z=math.pi/2, rot_y=-math.pi/2)
        elif wall == "w":    # run goes +z from `at`
            m.add(prism(profile, L), mat, at=(fixed, y, c0), rot_z=math.pi/2, rot_y=math.pi/2)
    return m


def lx(x):
    """room-local x -> model x (piece authored about the room centre)"""
    return x - RW / 2


def lz(z):
    return z - RD / 2
