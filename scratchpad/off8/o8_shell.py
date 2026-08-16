"""Room 8 Office -- shell: ceiling, trim + wainscot, window units, doors.

Replaces the shell pass's "Office Ceiling" / "Office Baseboards" (same names,
so roomkit.place swaps them in place).  What changed:

  * the shell pass had ONE flush window on the east wall and a phantom plain
    door on the west wall.  The floor plan draws TWO windows on the east
    (exterior) wall and exactly one door, the 15-lite french door, at the west
    wall's south end -- which is also the only opening the DB already had.
  * every opening is now a real cut (o8_openings.py), so the casings, stools,
    aprons and blinds are fitted to real holes instead of drawn flush.
  * the wainscot is gapped at the window casings, because the sills sit at
    1.85 ft -- below the 3.30 ft chair rail -- exactly as photo f shows.
"""
from o8kit import *                                                # noqa: F403
from o8kit import (Model, Material, W, D, H, RAIL, WAINSCOT, DOOR_W, WIN_N,
                   WIN_S, WIN_SILL, WIN_HEAD, PASS_S, PASS_TOP, save_and_place,
                   skins, bx, wall_band, spans, _blit, R, cylinder, box,
                   TRIM, TRIM_D, WHITEWD, BLACKMET, CEIL, CEIL_FLAT, CAN_CONE,
                   LENS, VENT, ceiling, BB_H, BB_T, CASE_W, surfaces, ROOM,
                   disc_down, ring_down, rect_down)

# The photo's charcoal meters 82.9 (Office A, 190x55 clean patch on the north
# wall).  The shell pass used the swatch straight off the photo (#3e4145) and it
# rendered 107 -- a GLB collects ~1.6x what the same albedo does in the photo's
# own light, so the paint has to be authored darker than it looks.
WAIN = Material("wains", "#303337", roughness=0.86)
# same reason for the lid: kit.CEIL renders 208 against the photo's 181
CEIL_O = Material("ceilo", "#f0efec", roughness=0.95, emissive="#8d8d8d",
                  double_sided=False)
SLAT = Material("slat", "#f2f1ee", roughness=0.72)
PANE = Material("pane", "#ffffff", roughness=0.2, emissive="#ffffff",
                emissive_strength=2.2)
OUTLET = Material("outlet", "#f2f0ec", roughness=0.55)
SMOKE = Material("smoke", "#f0efec", roughness=0.6)


# ------------------------------------------------------------------ ceiling
def build_ceiling():
    m = ceiling(W, D, H, ceil_mat=CEIL_O,
                cans=[(2.35, 2.35), (7.55, 2.35), (2.35, 8.10), (7.55, 8.10),
                      (5.00, 5.20)],
                vents=[(5.30, 1.10, 0.95, 0.52)])
    # smoke detector -- photo B has one just off the middle of the ceiling
    ring_down(m, SMOKE, 6.55, 5.90, H - 0.055, 0.0, 0.30, 20)
    ring_down(m, CEIL_FLAT, 6.55, 5.90, H - 0.020, 0.30, 0.34, 20)
    return m


# ------------------------------------------------------------- window units
def window(m, a0, a1, sill=WIN_SILL, head=WIN_HEAD):
    """Casing + stool + apron + white 2in venetian blinds over a real cut in
    the EAST wall.  Authored in the wall frame (a = z, depth = into the room)
    and blitted, so the winding stays right."""
    sub = Model()
    # daylight behind the slats: the single-floor backdrop is a dark studio
    # gradient, so an unlit pane would read as a black hole where the photo's
    # brightest surface is.  Sized exactly to the opening -- not a room box.
    bx(sub, PANE, a0, a1, sill, head, 0.035, 0.050)
    # stool + apron
    bx(sub, TRIM, a0 - 0.20, a1 + 0.20, sill - 0.115, sill, 0.0, 0.255)
    bx(sub, TRIM, a0 + 0.10, a1 - 0.10, sill - 0.46, sill - 0.115, 0.0, 0.085)
    # side + head casing
    bx(sub, TRIM, a0 - CASE_W, a0, sill - 0.115, head, 0.0, 0.095)
    bx(sub, TRIM, a1, a1 + CASE_W, sill - 0.115, head, 0.0, 0.095)
    bx(sub, TRIM, a0 - CASE_W, a1 + CASE_W, head, head + CASE_W, 0.0, 0.095)
    # jamb returns so the cut does not show raw wall thickness
    bx(sub, TRIM_D, a0, a0 + 0.035, sill, head, 0.0, 0.075)
    bx(sub, TRIM_D, a1 - 0.035, a1, sill, head, 0.0, 0.075)
    bx(sub, TRIM_D, a0, a1, head - 0.035, head, 0.0, 0.075)
    # headrail + slats, tilted the way every photo of this room shows them
    bx(sub, SLAT, a0 + 0.03, a1 - 0.03, head - 0.235, head - 0.030,
       0.055, 0.170)
    n = int((head - 0.33 - sill) / 0.185)
    for i in range(n):
        y = head - 0.34 - i * 0.185
        sub.add(box(a1 - a0 - 0.06, 0.015, 0.145), SLAT,
                at=((a0 + a1) / 2, y, 0.112), rot_x=R(26))
    # the two lift cords
    for cx in (a0 + 0.55, a1 - 0.55):
        bx(sub, TRIM_D, cx - 0.012, cx + 0.012, sill + 0.05, head - 0.25,
           0.145, 0.165)
    _blit(m, sub, "e", W, D, 0.0)


# ------------------------------------------------------------- french door
def french_door(m):
    """15 lites, 3 wide x 5 tall (photo B), white, black lever.  Sits over the
    app's painted door panel in the real cut, so the leaf reads closed."""
    sub = Model()
    a0, a1 = D - DOOR_W[1], D - DOOR_W[0]          # _blit('w') frame
    top = 6.98
    st = 0.36                                       # stile / rail width
    dz0, dz1 = 0.045, 0.155
    bx(sub, WHITEWD, a0 + 0.02, a0 + st, 0.0, top, dz0, dz1)
    bx(sub, WHITEWD, a1 - st, a1 - 0.02, 0.0, top, dz0, dz1)
    bx(sub, WHITEWD, a0 + 0.02, a1 - 0.02, 0.0, 0.95, dz0, dz1)        # bottom rail
    bx(sub, WHITEWD, a0 + 0.02, a1 - 0.02, top - 0.30, top, dz0, dz1)  # top rail
    gx0, gx1 = a0 + st, a1 - st
    gy0, gy1 = 0.95, top - 0.30
    for c in range(1, 3):
        x = gx0 + c * (gx1 - gx0) / 3
        bx(sub, WHITEWD, x - 0.028, x + 0.028, gy0, gy1, dz0, dz1)
    for r in range(1, 5):
        y = gy0 + r * (gy1 - gy0) / 5
        bx(sub, WHITEWD, gx0, gx1, y - 0.028, y + 0.028, dz0, dz1)
    # casing
    for a, b in ((a0 - CASE_W, a0 + 0.02), (a1 - 0.02, a1 + CASE_W)):
        bx(sub, TRIM, a, b, 0.0, top + CASE_W, 0.0, 0.20)
    bx(sub, TRIM, a0 - CASE_W, a1 + CASE_W, top, top + CASE_W, 0.0, 0.20)
    # black lever on the south stile
    sub.add(cylinder(0.075, 0.06, 12), BLACKMET, at=(a0 + 0.30, 3.05, 0.20),
            rot_x=R(90))
    bx(sub, BLACKMET, a0 + 0.14, a0 + 0.32, 2.99, 3.10, 0.20, 0.26)
    _blit(m, sub, "w", W, D, 0.0)


def cased_nook(m):
    """Cased opening south into the printer nook -- trim only, real hole."""
    sub = Model()
    a0, a1 = W - PASS_S[1], W - PASS_S[0]           # _blit('s') frame
    for a, b in ((a0 - CASE_W, a0 + 0.02), (a1 - 0.02, a1 + CASE_W)):
        bx(sub, TRIM, a, b, 0.0, PASS_TOP + CASE_W, 0.0, 0.20)
    bx(sub, TRIM, a0 - CASE_W, a1 + CASE_W, PASS_TOP, PASS_TOP + CASE_W,
       0.0, 0.20)
    bx(sub, TRIM_D, a0 + 0.02, a1 - 0.02, PASS_TOP - 0.05, PASS_TOP, 0.0, 0.10)
    _blit(m, sub, "s", W, D, 0.0)


# ------------------------------------------------------ trim + wainscot run
def build_trim():
    m = Model()
    C = CASE_W + 0.02
    # gaps in each wall's ASCENDING local axis
    door_gap = (DOOR_W[0] - C, DOOR_W[1] + C)
    pass_gap = (PASS_S[0] - C, PASS_S[1] + C)
    win_gaps = [(WIN_N[0] - C, WIN_N[1] + C), (WIN_S[0] - C, WIN_S[1] + C)]

    floor_gaps = {"n": [], "e": [], "s": [pass_gap], "w": [door_gap]}
    wains_gaps = {"n": [], "e": win_gaps, "s": [pass_gap], "w": [door_gap]}

    for w in "nesw":
        wall_band(m, TRIM, w, W, D, 0.0, BB_H - 0.07, BB_T, floor_gaps[w])
        wall_band(m, TRIM, w, W, D, BB_H - 0.07, BB_H, BB_T * 0.70, floor_gaps[w])
    # charcoal wainscot panel, then the two-step chair rail
    for w in "nesw":
        wall_band(m, WAIN, w, W, D, BB_H, RAIL - 0.145, 0.044, wains_gaps[w])
        wall_band(m, TRIM, w, W, D, RAIL - 0.145, RAIL - 0.040, 0.090, wains_gaps[w])
        wall_band(m, TRIM, w, W, D, RAIL - 0.040, RAIL, 0.055, wains_gaps[w])

    window(m, *WIN_N)
    window(m, *WIN_S)
    french_door(m)
    cased_nook(m)

    # white devices against the charcoal -- outlets on the wainscot, a triple
    # switch by the door and the wall tablet photo B shows south of the clock
    for (wall, a, y) in (("n", 6.30, 1.30), ("n", 1.80, 1.30), ("e", 5.70, 1.30),
                         ("s", 4.05, 1.30), ("w", 4.60, 1.30)):
        sub = Model()
        bx(sub, OUTLET, a - 0.15, a + 0.15, y - 0.24, y + 0.24, 0.0, 0.030)
        _blit(m, sub, wall, W, D, 0.052)
    sub = Model()
    bx(sub, OUTLET, 0.95, 1.60, 4.05, 4.55, 0.0, 0.030)     # switch plate
    _blit(m, sub, "w", W, D, 0.032)
    return m


if __name__ == "__main__":
    surfaces(ROOM, wall_color="#dedbd4", floor_color="#6b6967",
             floor_texture="wood")
    save_and_place("Office Ceiling", build_ceiling())
    save_and_place("Office Baseboards", build_trim())
    # Per-wall albedo skins, solved from two-point log-linear fits measured off
    # real renders (probe p1/p2 in shots/).  One sun, no bounce, so at the room
    # wall's single #dedbd4 the four walls rendered N 234 / W 210 / E 171 /
    # S 149; the photo's own walls sit 167-205.  Non-emissive, corner to corner,
    # roughness 0.95 to match the room wall -- see ROOM-BRIEF "give each wall
    # its own albedo".
    save_and_place("Office Wall Wash",
                   skins({"n": "#86807a", "e": "#f4f2ed",
                          "s": "#fbfaf6", "w": "#bfbdb6"}))
