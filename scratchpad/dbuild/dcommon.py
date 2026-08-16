"""Shared layout + materials for the room-4 (Dining) build -- ROUND 2.

The footprint was RE-TRACED under round 1: the room went from a 19 x 17 rect to
a 14.64 x 13.12 POLYGON with a three-facet bay on the WEST wall, and its anchor
moved (+5.31, -3.80).  Everything is re-derived.  Authored in ROOM-LOCAL FEET:

    x  0.00 .. 14.64   (west .. east; the bay reaches out to x = 0,
                        the main rect's west wall plane is x = 2.28)
    z  0.00 .. 13.12   (north .. south)
    y  0.00 ..  9.00   (slab .. ceiling)

ORIENTATION (derived from the world rects + the Main Floor Plan, then checked
against all four photos -- see rooms/4.json _orientation):
    NORTH (z=0)      kitchen (room 6) -- cased opening at its west end, then the
                     black buffet with the wall TV over it
    SOUTH (z=13.12)  the FRONT facade: window / round clock / window
    WEST  (x=0/2.28) side facade, the three-facet BAY (3 windows)
    EAST  (x=14.64)  first-floor hallway (room 12): cased opening onto the stairs
"""
import math
import os
import sys

sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\tools")
sys.path.insert(0, r"C:\Users\Manuel\Desktop\Pro\3d HA\scratchpad\kbuild")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from roomkit.glb import (Model, Material, box, rounded_box, cylinder, prism,  # noqa
                         quad, sag_plane, torus)
from roomkit.place import place  # noqa
# kraster.py is the round-3 kitchen's tone-field rasteriser: it is what turns a
# smooth scalar field into flat quads, and it is what makes a contact shadow a
# real gradient instead of the nested rings two critics rejected.
from kraster import (ramp, raster, fbm, vnoise, khash, rng as krng,  # noqa
                     Shadows, shadow_ramp, stone_field, Veins)

OUT = os.path.dirname(os.path.abspath(__file__))
ROOM = 4

# ------------------------------------------------------------------ the room
# Edge i runs POLY[i] -> POLY[i+1]; house.js indexes openings by that same i
# and measures `offset` along the edge from POLY[i].
POLY = [(14.64, 13.12), (2.28, 13.12), (2.28, 9.60), (0.00, 8.44),
        (0.00, 3.84), (2.28, 2.68), (2.28, 0.00), (14.64, 0.00)]
E_SOUTH, E_WSOUTH, E_BAY_S, E_BAY_F, E_BAY_N, E_WNORTH, E_NORTH, E_EAST = range(8)

XW_WEST, XW_EAST = 2.28, 14.64      # main-rect wall planes
ZW_NORTH, ZW_SOUTH = 0.00, 13.12
HGT = 9.00                          # wall height -- ground truth, never edited

# ------------------------------------------------------------------ trim heights
FLOOR_TOP = 0.030                   # carpet field sits here (app slab is y=0.01)
RUG_TOP = 0.052
SHADOW_Y = 0.064                    # translucent contact shadows, over both

BASE_H = 0.60                       # baseboard
CR0, CR1 = 2.70, 2.92               # chair rail band (the window stools sit on it)
WP0, WP1 = 0.78, 2.56               # picture-frame wainscot zone
CROWN0, CROWN1 = 7.40, 8.16         # crown run at the wall top
SOFFIT_Y = 8.16                     # tray perimeter soffit
RECESS_Y = 8.96                     # tray recess panel

WIN_Y0, WIN_H = 3.00, 4.25          # window hole: 3.00 .. 7.25
WIN_Y1 = WIN_Y0 + WIN_H
PASS_H = 7.20                       # cased-opening height

# ------------------------------------------------------------------ layout
# Derived from photo B (the camera looks straight down the table's long axis at
# the bay, 3 chairs a side + 1 each end) and photo f (the gap to the south wall
# is generous, the buffet side is tight).
TABLE_C = (7.10, 6.90)
TABLE_W, TABLE_D, TABLE_H = 7.80, 3.80, 2.50
CHAIR_SEAT, CHAIR_BACK = 1.45, 3.42
CHAIR_W, CHAIR_D = 1.62, 1.60

# (x, z, yaw_deg) -- yaw 0 = back to the NORTH wall
CHAIRS = (
    [(TABLE_C[0] + dx, TABLE_C[1] - TABLE_D / 2 - 0.64, 0.0) for dx in (-2.50, 0.0, 2.50)] +
    [(TABLE_C[0] + dx, TABLE_C[1] + TABLE_D / 2 + 0.64, 180.0) for dx in (-2.50, 0.0, 2.50)] +
    [(TABLE_C[0] - TABLE_W / 2 - 0.64, TABLE_C[1], 90.0),
     (TABLE_C[0] + TABLE_W / 2 + 0.64, TABLE_C[1], 270.0)]
)

RUG = (2.45, 12.85, 2.45, 11.25)    # x0, x1, z0, z1

BUF_C, BUF_W, BUF_D, BUF_H = 10.50, 5.20, 1.72, 2.92
TV_W, TV_H, TV_Y = 4.60, 2.64, 4.36

# south wall (edge 0) window centres, and the clock between them
WIN_S = (5.46, 11.46)
CLOCK_X, CLOCK_Y, CLOCK_R = 8.46, 5.55, 1.15

FIG = (3.55, 11.00)
SNAKE = (13.75, 7.70)
SIDE_T = (12.55, 3.55)              # the little black table beside the buffet (photo B)

# openings, room-local, so p_doors can line exactly what p_openings cut
KIT_OP = (2.58, 5.58)               # north wall, matches room 6's own hole (world x -1.61..1.39)
FOY_OP = (1.00, 6.60)               # east wall, faces the staircase (world z 22.7..28.3)

# ------------------------------------------------------------------ materials
# NO ROOM-SCALE EMISSIVE.  daylight.js was fixed app-wide; the walls, crown,
# baseboard, wainscot and casings here are plain painted surfaces and take the
# spread the single-sun renderer gives them.  The only emissive in this room is
# (a) the ceiling, which faces DOWN and collects ~0.05 of scene radiance so with
# none it renders black, and (b) a small floor under the near-black lacquer of
# the buffet/table so a face turned from the sun is not literally 0.
TRIM = Material("trim", "#f4f2ee", roughness=0.62)
TRIM_LO = Material("trimlo", "#e2dfd9", roughness=0.66)     # jamb returns / reveals
TRIM_SH = Material("trimsh", "#c8c4bd", roughness=0.72)     # shadow lines under trim
WALLPT = Material("wallpt", "#c6c9ca", roughness=0.94)      # matches room.wall_color

CEIL = Material("ceil", "#fbfbfa", roughness=0.90, emissive="#a8a8a8",
                double_sided=False)
CEIL_LO = Material("ceillo", "#f9f9f8", roughness=0.90, emissive="#a3a3a3",
                   double_sided=False)
CEIL_TRIM = Material("ceiltrim", "#f8f7f4", roughness=0.72, emissive="#7c7c7c")

ESPRESSO = Material("espresso", "#332e2b", roughness=0.86, emissive="#0d0c0b")
ESPRESSO_D = Material("espressod", "#252120", roughness=0.88, emissive="#090808")
BLACKLAQ = Material("blacklaq", "#33363a", roughness=0.44, metallic=0.18,
                    emissive="#171819")
BLACKLAQ_D = Material("blacklaqd", "#191b1d", roughness=0.46, metallic=0.20,
                      emissive="#0e0f10")
IRON = Material("iron", "#1f2124", roughness=0.36, metallic=0.42, emissive="#101112")
CHROME = Material("chrome", "#c4c7cb", roughness=0.24, metallic=0.75)

LINEN = Material("linen", "#7c7974", roughness=0.94)
LINEN_D = Material("linend", "#69665f", roughness=0.94)
SHADE = Material("shade", "#f2f0ec", roughness=0.86, emissive="#cfcdc8",
                 emissive_strength=1.25)

BLIND = Material("blind", "#f0eeea", roughness=0.78)
BLIND_E = Material("blinde", "#e3e0da", roughness=0.80)      # slat edge / reveal
GLASSY = Material("glassy", "#dfe6ea", roughness=0.12, metallic=0.05,
                  emissive="#8d969b")

LEAF = Material("leaf", "#4f6f45", roughness=0.86, double_sided=True)
LEAF_L = Material("leafl", "#6d8a58", roughness=0.86, double_sided=True)
STEM = Material("stem", "#5b5a4a", roughness=0.88)
SOIL = Material("soil", "#3a332c", roughness=0.96)
POT = Material("pot", "#efeeea", roughness=0.80)

ROSE = Material("rose", "#9b2531", roughness=0.90)
ROSE_D = Material("rosed", "#6f1721", roughness=0.92)
GREENTHROW = Material("greenthrow", "#7d8a5e", roughness=0.95)
KRAFT = Material("kraft", "#b39a76", roughness=0.94)
PAPER = Material("paper", "#f2efe8", roughness=0.92)
WOODLID = Material("woodlid", "#a98a63", roughness=0.85)
CLOCKFACE = Material("clockface", "#cbb798", roughness=0.88)
GREY_MET = Material("greymet", "#8c9095", roughness=0.42, metallic=0.5)

# ------------------------------------------------------------------ helpers
def bx(m, mat, x0, x1, y0, y1, z0, z1):
    """Axis-aligned box given absolute room-local extents."""
    if abs(x1 - x0) < 1e-6 or abs(y1 - y0) < 1e-6 or abs(z1 - z0) < 1e-6:
        return
    m.add(box(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)), mat,
          at=((x0 + x1) / 2.0, min(y0, y1), (z0 + z1) / 2.0))


_CENTROID = (sum(p[0] for p in POLY) / len(POLY),
             sum(p[1] for p in POLY) / len(POLY))


def edge_info(i):
    ax, az = POLY[i]
    bxx, bz = POLY[(i + 1) % len(POLY)]
    dx, dz = bxx - ax, bz - az
    ln = math.hypot(dx, dz)
    ux, uz = dx / ln, dz / ln
    nx, nz = -uz, ux
    mx, mz = (ax + bxx) / 2.0, (az + bz) / 2.0
    if (_CENTROID[0] - mx) * nx + (_CENTROID[1] - mz) * nz < 0:
        nx, nz = -nx, -nz                    # point it INTO the room
    return {"a": (ax, az), "b": (bxx, bz), "u": (ux, uz), "n": (nx, nz),
            "len": ln, "rot": math.atan2(-dz, dx)}


EDGES = [edge_info(i) for i in range(len(POLY))]


def on_edge(i, u, out=0.0):
    """World point at distance `u` along edge i, `out` ft into the room."""
    e = EDGES[i]
    return (e["a"][0] + e["u"][0] * u + e["n"][0] * out,
            e["a"][1] + e["u"][1] * u + e["n"][1] * out)


def edge_run(m, mat, i, y0, y1, thick, u0=None, u1=None, out=0.0):
    """A box lying along wall edge i, `thick` deep into the room."""
    e = EDGES[i]
    u0 = 0.0 if u0 is None else u0
    u1 = e["len"] if u1 is None else u1
    if u1 - u0 < 1e-4 or y1 - y0 < 1e-6:
        return
    cx, cz = on_edge(i, (u0 + u1) / 2.0, thick / 2.0 + out)
    m.add(box(u1 - u0, y1 - y0, thick), mat, at=(cx, y0, cz), rot_y=e["rot"])


def edge_gaps(i, holes):
    """Split edge i's 0..len into the runs BETWEEN `holes` [(u0,u1), ...]."""
    ln = EDGES[i]["len"]
    cuts = sorted(holes)
    out, at = [], 0.0
    for h0, h1 in cuts:
        if h0 > at:
            out.append((at, min(h0, ln)))
        at = max(at, h1)
    if at < ln:
        out.append((at, ln))
    return [(a, b) for a, b in out if b - a > 0.02]


def inside(x, z, shrink=0.0):
    """Point-in-polygon for the room footprint (optionally eroded by `shrink`)."""
    n = len(POLY)
    c = False
    j = n - 1
    for i in range(n):
        xi, zi = POLY[i]
        xj, zj = POLY[j]
        if (zi > z) != (zj > z) and x < (xj - xi) * (z - zi) / (zj - zi) + xi:
            c = not c
        j = i
    if not c or shrink <= 0:
        return c
    for i in range(n):
        ax, az = POLY[i]
        bxx, bz = POLY[(i + 1) % n]
        dx, dz = bxx - ax, bz - az
        L2 = dx * dx + dz * dz
        t = max(0.0, min(1.0, ((x - ax) * dx + (z - az) * dz) / L2))
        if math.hypot(ax + dx * t - x, az + dz * t - z) < shrink:
            return False
    return True


def emit(m, name, y=None, scale=1.0, room=ROOM):
    lo, hi = m.bounds()
    path = os.path.join(OUT, name.replace(" ", "_") + ".glb")
    m.save(path)
    pos = ((lo[0] + hi[0]) / 2.0, lo[1] if y is None else y, (lo[2] + hi[2]) / 2.0)
    res = place(name, path, room, pos=pos, rot_y_deg=0.0, scale=scale)
    print(f"{name:24s} x{lo[0]:6.2f}..{hi[0]:6.2f} y{lo[1]:5.2f}..{hi[1]:5.2f} "
          f"z{lo[2]:6.2f}..{hi[2]:6.2f} -> {res['action']}")
    return res
