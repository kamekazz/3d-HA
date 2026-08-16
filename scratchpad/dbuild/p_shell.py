"""Dining Baseboards (base + chair rail + picture-frame wainscot),
Dining Crown, and Dining Ceiling (the tray).

Names matter: objects.js SURFACE_RE marks anything containing floor / ceiling /
wall wash / baseboard(s) / crown as unpickable, which is what stops a room-scale
surface swallowing every click in the room.

NO EMISSIVE on the crown, baseboard or wainscot.  A critic rejected emissive
trim runs for glowing as bright fins against the darker walls, and the app-level
daylight fix removed the reason round 1 added it.  The ceiling is the single
exception: it faces DOWN, collects ~0.05 of scene radiance, and with no emissive
renders as a black lid.
"""
import math

from dcommon import (Model, Material, box, cylinder, torus, quad, raster,
                     TRIM, TRIM_LO, TRIM_SH, CEIL, CEIL_LO, CEIL_TRIM,
                     POLY, EDGES, E_SOUTH, E_NORTH, E_EAST, HGT,
                     BASE_H, CR0, CR1, WP0, WP1, CROWN0, CROWN1,
                     SOFFIT_Y, RECESS_Y, KIT_OP, FOY_OP, XW_WEST, XW_EAST,
                     ZW_NORTH, ZW_SOUTH, TABLE_C, PASS_H,
                     bx, edge_run, edge_gaps, on_edge, inside, emit)

# The two cased openings are the only trim breaks: every window sill sits ON the
# chair rail (2.92) and every window head (7.25) is below the crown (7.40).
HOLES = {
    E_NORTH: [(KIT_OP[0] - XW_WEST - 0.36, KIT_OP[1] - XW_WEST + 0.36)],
    E_EAST: [(FOY_OP[0] - 0.36, FOY_OP[1] + 0.36)],
}


# --------------------------------------------------------------------------
def frames(m, i, u0, u1, target=2.55, gap=0.52):
    """Fill a wall run with picture-frame wainscot boxes (photos A, B, f).

    0.155 ft stock, mitred as four runs; the field between them is the wall
    itself, which is what the real moulding does.
    """
    span = u1 - u0 - gap
    if span < 1.1:
        return
    n = max(1, int(round(span / (target + gap))))
    w = span / n - gap
    if w < 0.95:
        n = max(1, n - 1)
        w = span / n - gap
    st, ins = 0.155, 0.052
    for k in range(n):
        a = u0 + gap + k * (w + gap)
        b = a + w
        edge_run(m, TRIM, i, WP0, WP0 + st, ins, a, b)              # bottom
        edge_run(m, TRIM, i, WP1 - st, WP1, ins, a, b)              # top
        edge_run(m, TRIM, i, WP0, WP1, ins, a, a + st)              # left
        edge_run(m, TRIM, i, WP0, WP1, ins, b - st, b)              # right


def build_trim():
    m = Model()
    for i in range(len(POLY)):
        for (u0, u1) in edge_gaps(i, HOLES.get(i, [])):
            # baseboard: a plinth with a small cap, the way the photos read
            edge_run(m, TRIM, i, 0.0, BASE_H - 0.075, 0.085, u0, u1)
            edge_run(m, TRIM, i, BASE_H - 0.075, BASE_H, 0.115, u0, u1)
            edge_run(m, TRIM_SH, i, BASE_H, BASE_H + 0.018, 0.030, u0, u1)
            # chair rail: rail, then a proud cap the window stools land on
            edge_run(m, TRIM, i, CR0, CR1 - 0.055, 0.075, u0, u1)
            edge_run(m, TRIM, i, CR1 - 0.055, CR1, 0.135, u0, u1)
            edge_run(m, TRIM_SH, i, CR0 - 0.016, CR0, 0.028, u0, u1)
            frames(m, i, u0, u1)
    return m


# --------------------------------------------------------------------------
# Three members, not five: at five the crown read as horizontal siding from
# below, because every step edge catches the sun as its own line.
CROWN_STEPS = ((0.000, 0.150, 0.085),
               (0.150, 0.520, 0.335),
               (0.520, 0.760, 0.545))


def build_crown():
    """A built-up crown that springs from the wall at 7.40 and dies into the
    tray soffit at 8.16.  Unbroken: both cased openings stop at 7.20."""
    m = Model()
    for i in range(len(POLY)):
        ln = EDGES[i]["len"]
        # mitres are faked by letting each edge run its full length; the corner
        # overlap is inside the solid and never shows.
        edge_run(m, TRIM_SH, i, CROWN0 - 0.022, CROWN0, 0.036, 0, ln)
        for (a, b, proj) in CROWN_STEPS:
            edge_run(m, TRIM, i, CROWN0 + a, CROWN0 + b, proj, 0, ln)
    return m


# --------------------------------------------------------------------------
# The tray.  Photo B looks straight at its far edge and photo f at the near
# corner: the recess is NOT a plain rectangle -- it steps OUT toward the bay in
# the middle of the west side and steps back at both ends.  Round 1 shipped a
# plain rectangle and listed that as an open item.
REC_X0, REC_X1 = 4.30, 12.64
REC_Z0, REC_Z1 = 2.05, 11.07
BUMP_X0, BUMP_Z0, BUMP_Z1 = 2.10, 4.30, 8.00

# riser segments of the recess outline: (x0, x1, z0, z1) of a thin vertical box
RISERS = [
    (REC_X0, REC_X1, REC_Z0, REC_Z0),          # north
    (REC_X1, REC_X1, REC_Z0, REC_Z1),          # east
    (REC_X0, REC_X1, REC_Z1, REC_Z1),          # south
    (REC_X0, REC_X0, REC_Z0, BUMP_Z0),         # west, north of the bump
    (REC_X0, REC_X0, BUMP_Z1, REC_Z1),         # west, south of the bump
    (BUMP_X0, REC_X0, BUMP_Z0, BUMP_Z0),       # bump, north return
    (BUMP_X0, BUMP_X0, BUMP_Z0, BUMP_Z1),      # bump, face
    (BUMP_X0, REC_X0, BUMP_Z1, BUMP_Z1),       # bump, south return
]


def in_recess(x, z):
    return ((REC_X0 <= x <= REC_X1 and REC_Z0 <= z <= REC_Z1) or
            (BUMP_X0 <= x <= REC_X0 and BUMP_Z0 <= z <= BUMP_Z1))


def down_quad(m, mat, y, x0, x1, z0, z1):
    """A horizontal quad whose normal points DOWN, so it is solid at eye level
    and invisible from the plan pose (STYLE-BAR item 7).

    Winding matters: the first pass wound this the other way, the recess panel
    faced UP, and the whole middle of the ceiling rendered as the studio
    backdrop -- exactly the "a black slab means an inverted normal" failure the
    round-2 notes warn about."""
    m.add(quad((x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)), mat)


def build_ceiling():
    m = Model()
    # -- perimeter soffit: the room polygon minus the recess, one flat tone
    raster(m, [CEIL], "-y", SOFFIT_Y, 0.0, 14.64, 0.0, 13.12, 0.24,
           lambda x, z: None if (not inside(x, z) or in_recess(x, z)) else 0,
           lift=0.0)

    # -- the recess panel, a touch lighter than the soffit (a real tray reads
    #    that way and it is the only thing that draws the step from below)
    down_quad(m, CEIL_LO, RECESS_Y, REC_X0, REC_X1, REC_Z0, REC_Z1)
    down_quad(m, CEIL_LO, RECESS_Y, BUMP_X0, REC_X0, BUMP_Z0, BUMP_Z1)

    # -- risers + the applied moulding at their foot
    t = 0.075
    for (x0, x1, z0, z1) in RISERS:
        ax0, ax1 = (x0 - t / 2, x1 + t / 2) if abs(x1 - x0) > 1e-6 else (x0 - t / 2, x0 + t / 2)
        az0, az1 = (z0 - t / 2, z1 + t / 2) if abs(z1 - z0) > 1e-6 else (z0 - t / 2, z0 + t / 2)
        bx(m, CEIL_TRIM, ax0, ax1, SOFFIT_Y, RECESS_Y, az0, az1)
        # moulding: a wider, deeper step at the foot of the riser
        bx(m, CEIL_TRIM, ax0 - 0.10, ax1 + 0.10, SOFFIT_Y - 0.115, SOFFIT_Y + 0.02,
           az0 - 0.10, az1 + 0.10)

    # -- ceiling medallion under the chandelier (photos A, B, f)
    cx, cz = TABLE_C
    for (r, y0, y1) in ((1.02, RECESS_Y - 0.075, RECESS_Y),
                        (0.86, RECESS_Y - 0.135, RECESS_Y - 0.055),
                        (0.60, RECESS_Y - 0.105, RECESS_Y - 0.045),
                        (0.34, RECESS_Y - 0.150, RECESS_Y - 0.040)):
        m.add(cylinder(r, y1 - y0, seg=26), CEIL_TRIM, at=(cx, y0, cz))

    # -- round supply diffuser (photo A, top left of the tray)
    dx, dz = 4.55, 3.30
    m.add(cylinder(0.44, 0.055, seg=20), CEIL_TRIM, at=(dx, RECESS_Y - 0.055, dz))
    m.add(cylinder(0.31, 0.075, seg=20), Material("diff", "#cfcecb", roughness=0.7,
                                                  emissive="#5a5a5a"),
          at=(dx, RECESS_Y - 0.130, dz))
    return m


if __name__ == "__main__":
    emit(build_trim(), "Dining Baseboards", y=0.0)
    emit(build_crown(), "Dining Crown", y=CROWN0 - 0.022)
    emit(build_ceiling(), "Dining Ceiling")   # y=None: seat at the model's own min-Y
