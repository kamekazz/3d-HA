"""Dining Windows -- five units on real cut holes.

Round 1's single biggest stated limitation was that "the room geometry can't
hold the bay, so the three windows are laid flat".  The re-traced footprint has
the real three-facet bay, so the bay's windows now sit on the CANTED facets
(edges 2/3/4) and the two front-facade windows on the south wall (edge 0).

Every unit: jamb lining through the wall, a stool sitting on the chair-rail cap
(the photos show no apron -- the rail does that job), flat casing on the sides
and head, a sash with a meeting rail, and white 2 in faux-wood blinds LOWERED
with the slats tilted open, which is what all four photos show.  A daylight pane
sits just outside each hole: without one the hole shows the app's single-floor
studio backdrop and the window reads as a black rectangle.
"""
import math

from dcommon import (Model, Material, box, cylinder, quad, EDGES, on_edge,
                     TRIM, TRIM_LO, TRIM_SH, BLIND, BLIND_E, GLASSY,
                     E_SOUTH, E_BAY_S, E_BAY_F, E_BAY_N, WIN_S, WIN_Y0, WIN_Y1,
                     CR1, emit)

# opening (edge, u0, u1) -- must match p_openings.py exactly
UNITS = [
    (E_SOUTH, 1.88, 1.88 + 2.60, 2),      # front facade, east window (2 sashes)
    (E_SOUTH, 7.88, 7.88 + 2.60, 2),      # front facade, west window
    (E_BAY_S, 0.55, 0.55 + 1.46, 1),      # bay, south facet
    (E_BAY_F, 0.45, 0.45 + 3.70, 2),      # bay, front
    (E_BAY_N, 0.55, 0.55 + 1.46, 1),      # bay, north facet
]

# What photo A actually shows through the glass, top to bottom: blown-out sky,
# a dark treeline, the neighbour's white porch rail, and lawn.  Four bands, not
# a flat white card -- a flat card is what makes a window read as a light box.
SKY_HI = Material("skyhi", "#eef4f7", roughness=0.9, emissive="#dee8ee",
                  emissive_strength=2.15)
SKY_MID = Material("skymid", "#dfe9ec", roughness=0.9, emissive="#ccdbe2",
                   emissive_strength=1.95)
TREES = Material("wtrees", "#aab4a6", roughness=0.9, emissive="#94a08f",
                 emissive_strength=1.55)
RAIL = Material("wrail", "#eff2f0", roughness=0.9, emissive="#d5dad7",
                emissive_strength=1.90)
LAWN = Material("wlawn", "#bcc8ab", roughness=0.9, emissive="#9daa8c",
                emissive_strength=1.62)


def wput(m, part, mat, i, u, y, n, rot_x=0.0):
    """Place `part` in wall-edge i's frame: `u` along the wall, `n` into the room."""
    x, z = on_edge(i, u, n)
    m.add(part, mat, at=(x, y, z), rot_x=rot_x, rot_y=EDGES[i]["rot"])


def wbox(m, mat, i, u0, u1, y0, y1, n0, n1):
    """Axis-aligned box in wall-edge i's frame, given u / y / n extents."""
    if abs(u1 - u0) < 1e-6 or abs(y1 - y0) < 1e-6 or abs(n1 - n0) < 1e-6:
        return
    wput(m, box(abs(u1 - u0), abs(y1 - y0), abs(n1 - n0)), mat, i,
         (u0 + u1) / 2.0, min(y0, y1), (n0 + n1) / 2.0)


def unit(m, i, u0, u1, sashes):
    w = u1 - u0
    y0, y1 = WIN_Y0, WIN_Y1

    # --- daylight beyond the glass -------------------------------------------
    # three bands, brightest at the head: the photos' windows are blown-out sky
    # at the top grading to lawn/foliage at the sill.
    for (a, b, mat) in ((0.00, 0.40, SKY_HI), (0.40, 0.58, SKY_MID),
                        (0.58, 0.70, TREES), (0.70, 0.765, RAIL),
                        (0.765, 1.00, LAWN)):
        wbox(m, mat, i, u0 - 0.05, u1 + 0.05,
             y1 - (y1 - y0) * b, y1 - (y1 - y0) * a, -0.30, -0.26)

    # --- jamb lining, running OUT of the room the way a real jamb does --------
    t = 0.075
    wbox(m, TRIM_LO, i, u0 - t, u0, y0, y1 + t, -0.28, 0.02)
    wbox(m, TRIM_LO, i, u1, u1 + t, y0, y1 + t, -0.28, 0.02)
    wbox(m, TRIM_LO, i, u0 - t, u1 + t, y1, y1 + t, -0.28, 0.02)

    # NO glass sheet of our own: house.js already fills a `window` hole with a
    # translucent pane, and an opaque sheet here hid the view bands behind it --
    # which is exactly what made the raised half of every blind read as a flat
    # pale slab instead of daylight.

    # --- sash frame + meeting rail -------------------------------------------
    s = 0.085
    for (a, b) in ((u0, u0 + s), (u1 - s, u1)):
        wbox(m, TRIM, i, a, b, y0, y1, -0.135, -0.055)
    wbox(m, TRIM, i, u0, u1, y1 - s, y1, -0.135, -0.055)
    wbox(m, TRIM, i, u0, u1, y0, y0 + s, -0.135, -0.055)
    wbox(m, TRIM, i, u0, u1, (y0 + y1) / 2 - 0.055, (y0 + y1) / 2 + 0.055,
         -0.135, -0.055)                                   # meeting rail
    if sashes > 1:                                          # centre mullion
        um = (u0 + u1) / 2.0
        wbox(m, TRIM, i, um - 0.075, um + 0.075, y0, y1, -0.140, -0.050)

    # --- blinds: 2 in slats, lowered, tilted open ----------------------------
    hb = 0.24
    wbox(m, TRIM, i, u0 + 0.04, u1 - 0.04, y1 - hb, y1 - 0.01, -0.055, 0.075)
    pitch, tilt = 0.148, math.radians(30.0)
    ytop = y1 - hb - 0.05
    # photo A has every blind RAISED to roughly half-mast, with bright glass
    # below -- that light is most of what the photograph is.
    n = int((ytop - (y0 + (y1 - y0) * 0.50)) / pitch)
    for k in range(n + 1):
        yy = ytop - k * pitch
        wput(m, box(u1 - u0 - 0.115, 0.026, 0.152, anchor="center"),
             BLIND if k % 2 == 0 else BLIND_E, i,
             (u0 + u1) / 2.0, yy, 0.010, rot_x=tilt)
    # the two lift cords, dead centre of each sash
    # the bottom rail of the raised stack, then the lift cords down to the sill
    wbox(m, BLIND, i, u0 + 0.05, u1 - 0.05, ytop - n * pitch - 0.085,
         ytop - n * pitch, -0.045, 0.070)
    for f in ((0.5,) if sashes == 1 else (0.27, 0.73)):
        wbox(m, BLIND_E, i, u0 + (u1 - u0) * f - 0.010,
             u0 + (u1 - u0) * f + 0.010, y0, ytop - n * pitch,
             0.020, 0.034)

    # --- stool on the chair-rail cap, then flat casing -----------------------
    wbox(m, TRIM, i, u0 - 0.26, u1 + 0.26, y0 - 0.115, y0, -0.10, 0.235)
    wbox(m, TRIM_SH, i, u0 - 0.26, u1 + 0.26, y0 - 0.155, y0 - 0.115, -0.10, 0.19)
    cw, cp = 0.335, 0.085
    wbox(m, TRIM, i, u0 - cw, u0, y0 - 0.02, y1 + cw, 0.0, cp)
    wbox(m, TRIM, i, u1, u1 + cw, y0 - 0.02, y1 + cw, 0.0, cp)
    wbox(m, TRIM, i, u0 - cw, u1 + cw, y1, y1 + cw, 0.0, cp)
    wbox(m, TRIM, i, u0 - cw - 0.045, u1 + cw + 0.045, y1 + cw, y1 + cw + 0.075,
         0.0, cp + 0.045)                                   # head cap


if __name__ == "__main__":
    m = Model()
    for (i, a, b, s) in UNITS:
        unit(m, i, a, b, s)
    emit(m, "Dining Windows", y=WIN_Y0 - 0.155)
