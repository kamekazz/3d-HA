"""Dining room shell: wall skin + trim (wainscot/chair rail/baseboard/crown) and
the tray ceiling.  Both are ONE-SIDED and face into the room, so from outside
(the dollhouse view) they are back-facing and cull away -- the app's own wall
culling still lets the camera see in, and `--pose plan` still shows the floor.
"""
import math
import sys

from dk import *          # noqa
import tone

# ------------------------------------------------------------------ heights
BASE_H, BASE_D = 0.52, 0.085           # baseboard
FIELD_Y0, FIELD_Y1 = 0.52, 2.60        # wainscot field
RAIL_Y0, RAIL_Y1, RAIL_D = 2.60, 2.86, 0.115
FRM_Y0, FRM_Y1 = 0.86, 2.28            # picture-frame moulding band
FRM_W, FRM_D = 0.185, 0.065
CROWN_Y0, CROWN_Y1, CROWN_D = 7.42, 8.15, 0.60
SOFFIT_Y = 8.15
TRAY_IN = 2.05                          # tray inset from each wall
RISER_Y1 = 8.95
SKIN_TOP = 8.17

# window opening zones (used to break the wainscot + skin)
WIN_W, WIN_H = 3.02, 4.40
WIN_Y0 = 2.98                           # top of the stool = bottom of the casing
WIN_Y1 = WIN_Y0 + WIN_H                 # 7.38
SOUTH_WIN = [6.0, 13.0]                 # local x centres
WEST_WIN = [4.4, 8.6, 12.8]             # local z centres

# Cased openings: north -> the kitchen (Dining C), east -> the front-door
# hallway (Dining f).  We do not cut real holes in the room (the app fills an
# opening with a hardcoded teal slab); this is a cased reveal with a lit panel
# in it, which is what reads correctly from inside.
DOOR_TOP = WIN_Y1
DOORS = {"north": [(0.95, 7.65)], "east": [(1.10, 7.00)]}

WALL_RUN = {"north": (0.0, W), "south": (0.0, W),
            "west": (0.0, D), "east": (0.0, D)}

# ---------------------------------------------------------------- palette
GREY = "#c3c9ce"        # wall paint straight off the photo
WHITE = "#ffffff"       # trim

FIELD_TARGET = {"north": 202, "west": 196, "east": 186, "south": 183}
TRIM_TARGET = {"north": 229, "west": 222, "east": 214, "south": 208}


def mat(name, albedo, surface, target, rough=0.92, ds=True):
    em, st = tone.emissive_for(target, albedo, surface)
    return Material(name, albedo, roughness=rough, emissive=em,
                    emissive_strength=st, double_sided=ds)


FIELD = {w: mat("field_" + w, GREY, w, FIELD_TARGET[w], ds=False) for w in WALL_RUN}
TRIM = {w: mat("trim_" + w, WHITE, w, TRIM_TARGET[w]) for w in WALL_RUN}


# ------------------------------------------------------------------ helpers

def skin_quad(wall, t0, t1, y0, y1, d=0.035):
    """One-sided wall quad `d` feet in front of the wall face, facing the room."""
    if wall == "north":
        return panel(t0, t1, y0, y1, d, +1)
    if wall == "south":
        return panel(t0, t1, y0, y1, D - d, -1)
    if wall == "west":
        return panel_zy(t0, t1, y0, y1, d, +1)
    return panel_zy(t0, t1, y0, y1, W - d, -1)


def band(wall, t0, t1, y0, y1, d0, d1):
    """Solid trim band along a wall: d0..d1 = depth range from the wall face."""
    if wall == "north":
        return slab(t0, t1, y0, y1, d0, d1)
    if wall == "south":
        return slab(t0, t1, y0, y1, D - d1, D - d0)
    if wall == "west":
        return slab(d0, d1, y0, y1, t0, t1)
    return slab(W - d1, W - d0, y0, y1, t0, t1)


def add_band(m, material, wall, t0, t1, y0, y1, d0, d1):
    p, at = band(wall, t0, t1, y0, y1, d0, d1)
    m.add(p, material, at=at)


def excluded(wall):
    """Run intervals covered by windows (no wainscot / no skin behind them)."""
    if wall == "south":
        return [(c - WIN_W / 2, c + WIN_W / 2) for c in SOUTH_WIN]
    if wall == "west":
        return [(c - WIN_W / 2, c + WIN_W / 2) for c in WEST_WIN]
    return []


def doors(wall):
    return DOORS.get(wall, [])


def free_spans(t0, t1, blocked, pad=0.0):
    spans, cur = [], t0
    for a, b in sorted(blocked):
        a, b = a - pad, b + pad
        if a > cur:
            spans.append((cur, min(a, t1)))
        cur = max(cur, b)
    if cur < t1:
        spans.append((cur, t1))
    return [(a, b) for a, b in spans if b - a > 0.02]


def frame_layout(t0, t1, target=2.95, gap=0.50, edge=0.42):
    """Even run of picture-frame boxes inside t0..t1."""
    span = (t1 - t0) - 2 * edge
    if span < 1.5:
        return []
    n = max(1, round((span + gap) / (target + gap)))
    wdt = (span - gap * (n - 1)) / n
    if wdt < 1.2 and n > 1:
        n -= 1
        wdt = (span - gap * (n - 1)) / n
    return [(t0 + edge + i * (wdt + gap), t0 + edge + i * (wdt + gap) + wdt)
            for i in range(n)]


# ------------------------------------------------------------------ the walls

def build_walls():
    m = Model()
    for wall, (t0, t1) in WALL_RUN.items():
        fmat, tmat = FIELD[wall], TRIM[wall]
        blocked = excluded(wall)

        dz = doors(wall)

        # --- painted skin, broken around the window glass and the openings ---
        for a, b in free_spans(t0, t1, dz):
            m.add(skin_quad(wall, a, b, 0.0, WIN_Y0), fmat)         # below sills
        for a, b in free_spans(t0, t1, blocked + dz):
            m.add(skin_quad(wall, a, b, WIN_Y0, WIN_Y1), fmat)
        m.add(skin_quad(wall, t0, t1, WIN_Y1, SKIN_TOP), fmat)      # above heads

        for a, b in free_spans(t0, t1, dz):
            # --- baseboard --------------------------------------------------
            add_band(m, tmat, wall, a, b, 0.0, BASE_H - 0.055, 0.0, BASE_D)
            add_band(m, tmat, wall, a, b, BASE_H - 0.055, BASE_H, 0.0, BASE_D * 0.72)
            # --- chair rail -------------------------------------------------
            add_band(m, tmat, wall, a, b, RAIL_Y0, RAIL_Y1 - 0.07, 0.0, RAIL_D * 0.6)
            add_band(m, tmat, wall, a, b, RAIL_Y1 - 0.07, RAIL_Y1, 0.0, RAIL_D)

        # --- wainscot picture frames ---------------------------------------
        for a, b in free_spans(t0, t1, blocked + dz, pad=0.30):
            for f0, f1 in frame_layout(a, b):
                for (u0, u1, v0, v1) in (
                        (f0, f1, FRM_Y0, FRM_Y0 + FRM_W),          # bottom rail
                        (f0, f1, FRM_Y1 - FRM_W, FRM_Y1),          # top rail
                        (f0, f0 + FRM_W, FRM_Y0, FRM_Y1),          # left stile
                        (f1 - FRM_W, f1, FRM_Y0, FRM_Y1)):         # right stile
                    add_band(m, tmat, wall, u0, u1, v0, v1, 0.0, FRM_D)

        # --- crown: a two-step sloped moulding at the ceiling ---------------
        prof = [(0.0, CROWN_Y0), (0.10, CROWN_Y0 + 0.02), (0.14, CROWN_Y0 + 0.15),
                (0.115, CROWN_Y0 + 0.20), (0.36, CROWN_Y0 + 0.40),
                (0.335, CROWN_Y0 + 0.46), (CROWN_D, CROWN_Y1 - 0.075),
                (CROWN_D, CROWN_Y1), (0.0, CROWN_Y1)]
        m.add(sweep(wall, t0, t1, prof), CROWN_MAT)
    return m


# ------------------------------------------------------------------ ceiling
CROWN_MAT = mat("crown", WHITE, "ceiling", 223, rough=0.9)
SOFFIT_MAT = mat("soffit", "#fbfbfb", "ceiling", 203, rough=0.95, ds=False)
PANEL_MAT = mat("tray", "#ffffff", "ceiling", 221, rough=0.95, ds=False)
RISER_MAT = {w: mat("riser_" + w, WHITE, w, min(228, TRIM_TARGET[w] + 12), ds=False)
             for w in WALL_RUN}
MEDAL_MAT = mat("medallion", WHITE, "ceiling", 226, rough=0.9)


def build_ceiling():
    m = Model()
    a, b = TRAY_IN, W - TRAY_IN          # tray x range
    c, d = TRAY_IN, D - TRAY_IN          # tray z range

    # perimeter soffit at 8.30, facing down
    m.add(plane_xz(0, W, 0, c, SOFFIT_Y, -1), SOFFIT_MAT)
    m.add(plane_xz(0, W, d, D, SOFFIT_Y, -1), SOFFIT_MAT)
    m.add(plane_xz(0, a, c, d, SOFFIT_Y, -1), SOFFIT_MAT)
    m.add(plane_xz(b, W, c, d, SOFFIT_Y, -1), SOFFIT_MAT)

    # tray risers -- each face points in toward the recess centre
    m.add(panel(a, b, SOFFIT_Y, RISER_Y1, c, +1), RISER_MAT["north"])
    m.add(panel(a, b, SOFFIT_Y, RISER_Y1, d, -1), RISER_MAT["south"])
    m.add(panel_zy(c, d, SOFFIT_Y, RISER_Y1, a, +1), RISER_MAT["west"])
    m.add(panel_zy(c, d, SOFFIT_Y, RISER_Y1, b, -1), RISER_MAT["east"])

    # recessed panel
    m.add(plane_xz(a, b, c, d, RISER_Y1, -1), PANEL_MAT)

    # small trim at the foot of each riser (reads as the tray's applied moulding)
    for (x0, x1, z0, z1) in ((a - 0.15, b + 0.15, c - 0.15, c + 0.0),
                             (a - 0.15, b + 0.15, d - 0.0, d + 0.15),
                             (a - 0.15, a + 0.0, c, d),
                             (b - 0.0, b + 0.15, c, d)):
        add_slab(m, MEDAL_MAT, x0, x1, SOFFIT_Y - 0.13, SOFFIT_Y, z0, z1)

    # ceiling medallion under the chandelier
    cx, cz = 9.0, 9.9
    m.add(cylinder(0.86, 0.055, 40, anchor="base"), MEDAL_MAT,
          at=(cx, RISER_Y1 - 0.055, cz))
    m.add(cylinder(0.62, 0.075, 36, anchor="base", r_top=0.50), MEDAL_MAT,
          at=(cx, RISER_Y1 - 0.13, cz))
    m.add(cylinder(0.30, 0.05, 28, anchor="base"), MEDAL_MAT,
          at=(cx, RISER_Y1 - 0.18, cz))

    # round supply diffuser in the tray
    m.add(cylinder(0.55, 0.045, 32, anchor="base"), MEDAL_MAT, at=(5.2, RISER_Y1 - 0.045, 5.0))
    m.add(cylinder(0.40, 0.05, 28, anchor="base", r_top=0.34), MEDAL_MAT,
          at=(5.2, RISER_Y1 - 0.095, 5.0))
    return m


OPEN_CASE = {w: mat("ocase_" + w, WHITE, w, TRIM_TARGET[w]) for w in WALL_RUN}
REVEAL = {w: mat("oreveal_" + w, "#dfe2e5", w, max(140, FIELD_TARGET[w] - 44))
          for w in WALL_RUN}


def build_openings():
    """White cased reveals with the next room painted into the back of them:
    the kitchen through the north wall, the front-door hallway through the east.
    """
    m = Model()
    CS, DEPTH = 0.34, 0.66

    def put(wall, a, b, y0, y1, d0, d1, mt):
        add_band(m, mt, wall, a, b, y0, y1, d0, d1)

    # --- kitchen, seen through the north wall -----------------------------
    K = DEPTH
    kwall = mat("k_wall", "#eceae6", "north", 200, ds=False)
    kupper = mat("k_upper", "#f8f7f5", "north", 216, ds=False)
    kline = mat("k_line", "#8f8b85", "north", 140, ds=False)
    kcount = mat("k_count", "#5f5b57", "north", 112, ds=False)
    kfloor = mat("k_floor", "#7a736d", "north", 124, ds=False)
    a, b = DOORS["north"][0]
    put("north", a, b, 0.0, DOOR_TOP, K, K + 0.03, kwall)
    put("north", a, b, 0.0, 0.55, K + 0.03, K + 0.06, kfloor)           # floor
    put("north", a + 0.5, b - 0.5, 0.55, 3.05, K + 0.03, K + 0.06, kupper)   # bases
    put("north", a + 0.5, b - 0.5, 4.55, 6.85, K + 0.03, K + 0.06, kupper)   # wall cabs
    for i in range(1, 5):                                               # door lines
        t = a + 0.5 + i * (b - a - 1.0) / 5
        put("north", t - 0.035, t + 0.035, 0.55, 3.05, K + 0.06, K + 0.08, kline)
        put("north", t - 0.035, t + 0.035, 4.55, 6.85, K + 0.06, K + 0.08, kline)
    put("north", a + 0.42, b - 0.42, 3.05, 3.26, K + 0.06, K + 0.11, kcount)  # counter

    # --- foyer, seen through the east wall --------------------------------
    hwall = mat("h_wall", "#d9dcdf", "east", 176, ds=False)
    hfloor = mat("h_floor", "#6a6058", "east", 96, ds=False)
    hdoor = mat("h_door", "#f4f4f2", "east", 196, ds=False)
    hline = mat("h_line", "#9b968f", "east", 132, ds=False)
    a, b = DOORS["east"][0]
    put("east", a, b, 0.0, DOOR_TOP, K, K + 0.03, hwall)
    put("east", a, b, 0.0, 0.80, K + 0.03, K + 0.06, hfloor)
    put("east", a + 0.55, a + 3.45, 0.30, 7.05, K + 0.03, K + 0.06, hdoor)
    for (u0, u1, v0, v1) in ((a + 0.85, a + 1.85, 0.75, 3.15),
                             (a + 2.15, a + 3.15, 0.75, 3.15),
                             (a + 0.85, a + 1.85, 3.60, 6.55),
                             (a + 2.15, a + 3.15, 3.60, 6.55)):
        for (p0, p1, q0, q1) in ((u0, u1, v0, v0 + 0.05), (u0, u1, v1 - 0.05, v1),
                                 (u0, u0 + 0.05, v0, v1), (u1 - 0.05, u1, v0, v1)):
            put("east", p0, p1, q0, q1, K + 0.06, K + 0.08, hline)

    # --- the reveals and casing, shared -----------------------------------
    for wall, spans in DOORS.items():
        case, rev = OPEN_CASE[wall], REVEAL[wall]
        for (a, b) in spans:
            put(wall, a, a + 0.10, 0.0, DOOR_TOP, 0.0, DEPTH, rev)
            put(wall, b - 0.10, b, 0.0, DOOR_TOP, 0.0, DEPTH, rev)
            put(wall, a, b, DOOR_TOP - 0.10, DOOR_TOP, 0.0, DEPTH, rev)
            put(wall, a - CS, a, 0.0, DOOR_TOP + CS, 0.0, 0.105, case)
            put(wall, b, b + CS, 0.0, DOOR_TOP + CS, 0.0, 0.105, case)
            put(wall, a - CS, b + CS, DOOR_TOP, DOOR_TOP + CS, 0.0, 0.105, case)
            put(wall, a - CS - 0.05, b + CS + 0.05, DOOR_TOP + CS,
                DOOR_TOP + CS + 0.09, 0.0, 0.155, case)
    return m


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which in ("all", "walls"):
        place_local("Dining Walls", build_walls())
    if which in ("all", "ceiling"):
        place_local("Dining Ceiling", build_ceiling())
    if which in ("all", "openings"):
        place_local("Dining Openings", build_openings())
