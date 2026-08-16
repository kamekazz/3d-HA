"""Shared materials + helpers for the room-6 (Kitchen) build -- ROUND 2.

The footprint was re-traced under round 1: the room is now 14.87 x 16.74 ft and
a POLYGON (three-facet bay on the west wall), anchored 5.31/7.24 ft away from
where round 1 built.  Everything here is authored in ROOM-LOCAL FEET:

    x 2.28 .. 14.87   west wall -> east wall   (bay reaches out to x = 0)
    z 0.00 .. 16.74   north wall -> south wall
    y 0.00 ..  9.00   slab -> ceiling

`emit()` reads the model bbox back and hands place() the centre/floor it
implies, so every piece is placed at rot 0.

ROUND-2 CHANGES TO THE SHARED LAYER
  * daylight.js was fixed app-wide (hemisphere ground + daytime IBL raised), so
    every emissive term round 1 metered is now too bright.  Re-metered against
    the photos: white doors want ~210 (were 220), quartz tops ~209 (were 237),
    ceiling ~205 (was 220).  Emissives below are pulled down to match.
  * HARDWARE: the photos show small round BLACK KNOBS on doors and black bar
    pulls on DRAWERS ONLY.  Round 1 put long vertical bar pulls on ~30 doors.
    `pull=("k", frac)` is the knob; ("h", frac) stays the drawer bar.
  * VEINING: round 1's veins were 0.29 in wide and 15 tone steps off the field,
    so they vanished past 6 ft.  `veins()` now draws a soft halo plus a dark
    core at ~0.5 ft spacing, which is what the Calacatta-look tops really do.
"""
import math
import os
import sys

sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
from roomkit.glb import Model, Material, box, rounded_box, cylinder, prism, quad, sag_plane, torus  # noqa
from roomkit.place import place  # noqa

OUT = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- the room
# footprint polygon, room-local feet, in the order the DB stores it (edge i
# runs POLY[i] -> POLY[i+1]; house.js indexes openings by that same i).
POLY = [(14.87, 16.74), (2.28, 16.74), (2.28, 11.16), (0.0, 10.0),
        (0.0, 4.51), (2.28, 3.35), (2.28, 0.0), (14.87, 0.0)]
E_SOUTH, E_WSOUTH, E_BAY_S, E_BAY_F, E_BAY_N, E_WNORTH, E_NORTH, E_EAST = range(8)

XW_WEST, XW_EAST = 2.28, 14.87      # main-rect wall planes
ZW_NORTH, ZW_SOUTH = 0.0, 16.74
HGT = 9.0                           # wall height (ground truth)
CEIL_Y = HGT - 0.03

# p_floor.py lays real plank geometry over the app's slab, so everything that
# stands on the floor is emitted at this height instead of 0 -- otherwise the
# planks and the baked contact shadows cut through the bottom half-inch of
# every toe kick.
FLOOR_TOP = 0.046

CT, CB = 3.00, 2.88                 # counter top / underside
TOE = 0.32
UP0, UP1 = 4.50, 8.10               # wall-cabinet band
CR1 = 8.55                          # top of the stepped crown

# ---------------------------------------------------------------- materials
# Vertical interior faces still collect well under half the scene radiance, so
# the whites carry an emissive stand-in for the bounce the renderer skips --
# but ~15% less of one than round 1 used, see the header.
EM_W = "#757575"
WHITE     = Material("white",   "#eeece8", roughness=0.52, emissive=EM_W)
WHITE_LO  = Material("whitelo", "#dbd8d3", roughness=0.55, emissive="#565656")
TRIM      = Material("trim",    "#f6f5f2", roughness=0.55, emissive="#6d6d6d")
QUARTZ    = Material("quartz",  "#cdcdca", roughness=0.46, emissive="#242424")
VEINH     = Material("veinh",   "#c0c3c5", roughness=0.47, emissive="#202020")
VEIN      = Material("vein",    "#a4a9ad", roughness=0.48, emissive="#1c1c1c")
VEINC     = Material("veinc",   "#979ea3", roughness=0.48, emissive="#1a1a1a")
MARBLE    = Material("marble",  "#cfcfcd", roughness=0.52, emissive="#1e1e1e")
BLACK     = Material("black",   "#191a1c", roughness=0.40, metallic=0.25)
GLASSBLK  = Material("blkglass", "#0c0d0f", roughness=0.14, metallic=0.35)
PULL      = Material("pull",    "#202226", roughness=0.32, metallic=0.55)
STEEL     = Material("steel",   "#c0c3c7", roughness=0.28, metallic=0.70,
                     emissive="#414141")
GREYFAB   = Material("greyfab", "#d3d2cf", roughness=0.92, emissive="#5e5e5e")
DARKFAB   = Material("darkfab", "#5e6062", roughness=0.95, emissive="#2e2e2e")
CEIL      = Material("ceil",    "#fbfbfa", roughness=0.90, emissive="#b2b2b2",
                     double_sided=False)
CEIL_TRIM = Material("ceiltrim", "#f7f7f5", roughness=0.70, emissive="#8b8b8b")
GLOW      = Material("glow",    "#ffffff", roughness=0.9, emissive="#ffffff",
                     emissive_strength=1.55, double_sided=False)
GLASS     = Material("glass",   "#dfe7ea", roughness=0.10, emissive="#98a1a6")
GREEN     = Material("green",   "#5d7f4e", roughness=0.85, emissive="#28331f")
WOODBLK   = Material("woodblk", "#8d6a4b", roughness=0.75, emissive="#372a1d")
# the app paints its own walls; this matches them for the bits of wall we build
# ourselves (the peninsula half-wall's back, opening jambs).
WALLPT    = Material("wallpt",  "#eeeae2", roughness=0.94, emissive="#4e4e4e")

FT = 1.0


# ---------------------------------------------------------------- helpers
def bx(m, mat, x0, x1, y0, y1, z0, z1):
    """Axis-aligned box given absolute room-local extents."""
    if abs(x1 - x0) < 1e-6 or abs(y1 - y0) < 1e-6 or abs(z1 - z0) < 1e-6:
        return
    m.add(box(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)), mat,
          at=((x0 + x1) / 2.0, min(y0, y1), (z0 + z1) / 2.0))


_AX = {"+x": (0, 1), "-x": (0, -1), "+z": (2, 1), "-z": (2, -1)}


def knob(m, mat, face, at, u, y, r=0.058):
    """A small round cabinet knob standing off the door face.

    This is the hardware the photos actually show on every DOOR; bar pulls are
    on drawers only.  `at` is the outer surface of the door's proud rails.
    """
    axis, d = _AX[face]

    def cyl(rad, h, off, r_top=None):
        p = cylinder(rad, h, seg=12, r_top=r_top)
        if axis == 0:
            m.add(p, mat, at=(at + d * off, y, u),
                  rot_z=(math.pi / 2 if d < 0 else -math.pi / 2))
        else:
            m.add(p, mat, at=(u, y, at + d * off),
                  rot_x=(math.pi / 2 if d > 0 else -math.pi / 2))

    cyl(0.022, 0.060, 0.0)                       # stem
    cyl(r, 0.052, 0.058, r_top=r * 0.86)         # head


def door(m, mat, face, at, u0, u1, y0, y1, depth=0.055, rail=0.135,
         proud=0.028, pull=None, pull_mat=None, panel=None, pull_y=0.5):
    """A shaker door/drawer front on a vertical plane.

    face: which way the front looks ('-x' means the front faces west).
    at:   the coordinate of the outer surface on the face axis.
    u0/u1: the in-plane horizontal extent (z for x-faces, x for z-faces).
    pull: None | ('k', frac) knob | ('h', frac) drawer bar | ('v', frac) bar.
    """
    axis, d = _AX[face]
    panel = panel or mat
    a0, a1 = at, at + d * depth                    # recessed panel
    p0, p1 = a1, at + d * (depth + proud)          # stiles/rails

    def put(mt, lo, hi, uu0, uu1, yy0, yy1):
        if axis == 0:
            bx(m, mt, min(lo, hi), max(lo, hi), yy0, yy1, uu0, uu1)
        else:
            bx(m, mt, uu0, uu1, yy0, yy1, min(lo, hi), max(lo, hi))

    put(panel, a0, a1, u0, u1, y0, y1)
    r = min(rail, (u1 - u0) / 2.5, (y1 - y0) / 2.5)
    put(mat, p0, p1, u0, u1, y0, y0 + r)          # bottom rail
    put(mat, p0, p1, u0, u1, y1 - r, y1)          # top rail
    put(mat, p0, p1, u0, u0 + r, y0, y1)          # left stile
    put(mat, p0, p1, u1 - r, u1, y0, y1)          # right stile

    if pull:
        kind, frac = pull
        pm = pull_mat or PULL
        h0, h1 = p1, at + d * (depth + proud + 0.055)
        uc = u0 + (u1 - u0) * frac
        if kind == "k":
            yc = y0 + (y1 - y0) * pull_y
            yc = min(max(yc, y0 + 0.16), y1 - 0.16)
            knob(m, pm, face, p1, uc, yc)
        elif kind == "v":
            L = min(0.46, (y1 - y0) * 0.42)
            yc = y0 + (y1 - y0) * pull_y
            yc = min(max(yc, y0 + L / 2 + 0.1), y1 - L / 2 - 0.1)
            put(pm, h0, h1, uc - 0.028, uc + 0.028, yc - L / 2, yc + L / 2)
        else:
            yc = y0 + (y1 - y0) * frac
            L = min(0.95, (u1 - u0) * 0.58)
            uc = (u0 + u1) / 2.0
            put(pm, h0, h1, uc - L / 2, uc + L / 2, yc - 0.030, yc + 0.030)
            for s in (-1, 1):                      # posts back to the drawer
                put(pm, p1, p1 + d * 0.026, uc + s * (L / 2 - 0.035),
                    uc + s * (L / 2 - 0.005), yc - 0.030, yc + 0.030)


def two_door(m, mat, face, at, u0, u1, y0, y1, pull_y=0.88, **kw):
    """A pair of shaker doors, knobs on the meeting stiles."""
    mid = (u0 + u1) / 2.0
    g = 0.014
    door(m, mat, face, at, u0, mid - g, y0, y1, pull=("k", 0.86),
         pull_y=pull_y, **kw)
    door(m, mat, face, at, mid + g, u1, y0, y1, pull=("k", 0.14),
         pull_y=pull_y, **kw)


def veins(m, mat, face, at, u0, u1, w0, w1, seeds, thin=0.045, count=None,
          step=0.34, core=None, spacing=0.95, angle=None):
    """Calacatta veining on a flat surface: near-parallel drifting veins.

    Round 1 drew 0.29 in hairlines only 15 tone steps off the field, and a
    critic metered the tops as "plain white paint" past 6 ft.  The first round-2
    attempt over-corrected into a scribble -- veins that wandered freely and
    crossed each other read as pencil scratches, not stone.

    Real Calacatta-look quartz runs a family of roughly PARALLEL veins with a
    soft grey halo, a thinner darker core along part of it, and short feathers
    peeling off at a shallow angle.  That is what this draws: one base direction
    per slab, low meander, `spacing` ft apart.  face '+y' = a horizontal top.
    """
    rnd = _rng(seeds)
    span_u, span_w = u1 - u0, w1 - w0
    if span_u <= 0.05 or span_w <= 0.05:
        return
    core = core or VEINC
    if count is None:
        count = max(2, int(math.hypot(span_u, span_w) / spacing))
    base = angle if angle is not None else (0.55 + rnd() * 0.55)

    # Each vein is three coplanar-ish layers -- a broad soft halo, the vein
    # proper, then a thin dark core -- so `layer` lifts them off each other by
    # 2.5 thou of a foot.  Without that they z-fight and the whole thing renders
    # as one flat hairline, which is what the first two round-2 builds did.
    def lay(mt, mu, mw, ang, ln, t, layer=1):
        off = 0.0022 * layer
        if face == "+y":
            m.add(box(ln, 0.003, t), mt, at=(mu, at + off, mw), rot_y=-ang)
        elif face in ("-x", "+x"):
            d = (0.003 + off) if face == "+x" else -(0.003 + off)
            m.add(box(0.003, t, ln), mt, at=(at + d, mw, mu), rot_x=-ang)
        else:
            d = (0.003 + off) if face == "+z" else -(0.003 + off)
            m.add(box(ln, t, 0.003), mt, at=(mu, mw, at + d), rot_z=ang)

    def walk(u, w, ang, wide, steps, with_core):
        for _s in range(steps):
            ang += (rnd() - 0.5) * 0.20
            nu, nw = u + math.cos(ang) * step, w + math.sin(ang) * step
            if not (u0 <= nu <= u1 and w0 <= nw <= w1):
                break
            mu, mw = (u + nu) / 2.0, (w + nw) / 2.0
            t = wide * (0.75 + rnd() * 0.5)
            if with_core:
                lay(VEINH, mu, mw, ang, step * 1.35, t * (2.4 + rnd() * 1.4), 0)
            lay(mat, mu, mw, ang, step * 1.22, t, 1)
            if with_core and rnd() < 0.88:
                lay(core, mu, mw, ang, step * 1.34, t * 0.52, 2)
            u, w = nu, nw
        return u, w, ang

    for i in range(count):
        ang = base + (rnd() - 0.5) * 0.55
        # spread the starts along the edge the veins run away from
        t0 = (i + 0.35 + (rnd() - 0.5) * 0.5) / max(count, 1)
        if rnd() < 0.5:
            u, w = u0 + span_u * t0, w0
        else:
            u, w = u0, w0 + span_w * t0
        wide = thin * (0.75 + rnd() * 0.6)
        eu, ew, ea = walk(u, w, ang, wide, 60, True)
        # one short feather peeling off the vein at a shallow angle
        if rnd() < 0.7:
            walk((u + eu) / 2, (w + ew) / 2, ea + (0.35 + rnd() * 0.35) *
                 (1 if rnd() < 0.5 else -1), wide * 0.42,
                 3 + int(rnd() * 4), False)


def _rng(seed):
    s = [seed & 0xFFFFFFFF]

    def nxt():
        s[0] = (1103515245 * s[0] + 12345) & 0x7FFFFFFF
        return s[0] / 0x7FFFFFFF
    return nxt


def arc_tube(m, mat, r, cx, cy, cz, a0, a1, segs, tube, plane="zy"):
    """Sweep a small cylinder along a circular arc (for the gooseneck faucet)."""
    prev = None
    for i in range(segs + 1):
        a = a0 + (a1 - a0) * i / segs
        if plane == "zy":
            p = (cx, cy + r * math.sin(a), cz + r * math.cos(a))
        else:
            p = (cx + r * math.cos(a), cy + r * math.sin(a), cz)
        if prev is not None:
            dx, dy, dz = p[0] - prev[0], p[1] - prev[1], p[2] - prev[2]
            L = math.sqrt(dx * dx + dy * dy + dz * dz)
            mid = ((p[0] + prev[0]) / 2, (p[1] + prev[1]) / 2, (p[2] + prev[2]) / 2)
            rx = math.atan2(dz, dy) if abs(dy) + abs(dz) > 1e-9 else 0.0
            m.add(cylinder(tube, L * 1.25, seg=10, anchor="center"), mat,
                  at=mid, rot_x=-rx)
        prev = p


# ---------------------------------------------------------------- polygon walls
_CENTROID = (sum(p[0] for p in POLY) / len(POLY),
             sum(p[1] for p in POLY) / len(POLY))


def edge_info(i):
    ax, az = POLY[i]
    bx_, bz = POLY[(i + 1) % len(POLY)]
    dx, dz = bx_ - ax, bz - az
    ln = math.hypot(dx, dz)
    ux, uz = dx / ln, dz / ln
    nx, nz = -uz, ux                       # one of the two normals
    mx, mz = (ax + bx_) / 2, (az + bz) / 2
    if (_CENTROID[0] - mx) * nx + (_CENTROID[1] - mz) * nz < 0:
        nx, nz = -nx, -nz                  # point it INTO the room
    return {"a": (ax, az), "b": (bx_, bz), "u": (ux, uz), "n": (nx, nz),
            "len": ln, "rot": math.atan2(-dz, dx)}


def edge_box(m, mat, i, y0, y1, thick, u0=None, u1=None, out=0.0):
    """A box lying along wall edge `i`, `thick` deep into the room.

    u0/u1 are distances along the edge from POLY[i]; `out` pushes the box
    further into the room (for the projecting steps of a crown).
    """
    e = edge_info(i)
    u0 = 0.0 if u0 is None else u0
    u1 = e["len"] if u1 is None else u1
    if u1 - u0 < 1e-4:
        return
    ux, uz = e["u"]
    nx, nz = e["n"]
    cu = (u0 + u1) / 2.0
    cx = e["a"][0] + ux * cu + nx * (thick / 2.0 + out)
    cz = e["a"][1] + uz * cu + nz * (thick / 2.0 + out)
    m.add(box(u1 - u0, y1 - y0, thick), mat, at=(cx, y0, cz), rot_y=e["rot"])


def emit(m, name, room=6, y=None, scale=1.0):
    lo, hi = m.bounds()
    path = os.path.join(OUT, name.replace(" ", "_") + ".glb")
    m.save(path)
    pos = ((lo[0] + hi[0]) / 2.0, lo[1] if y is None else y, (lo[2] + hi[2]) / 2.0)
    res = place(name, path, room, pos=pos, rot_y_deg=0.0, scale=scale)
    print(f"{name:26s} x{lo[0]:6.2f}..{hi[0]:6.2f} y{lo[1]:5.2f}..{hi[1]:5.2f} "
          f"z{lo[2]:6.2f}..{hi[2]:6.2f} -> {res['action']}")
    return res
