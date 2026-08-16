"""Round 4 — the re-traced master bedroom, and every number derived from it.

THE ROOM CHANGED UNDER ROUND 3.  It was 15 x 23.5 ft with the long axis running
north-south; it is now 20.51 x 18.68 with the long axis EAST-WEST and a new
entry vestibule.  Every wall assignment in layout.json had to be re-derived.

HOW THE WALLS WERE RE-DERIVED (not guessed):

  1. `plan_retrace.py` records the plan-px -> model-ft transform for the second
     floor.  Inverting it puts the Apple-Home scan's own furniture icons and its
     blue window marks into room-local feet.  Read straight off
     `docs/floor plan/Second Floor Plan App.png`:

        bed icon          x  6.85..13.95   z 0.20..7.77   (pillows against z=0)
        nightstand W      x  4.82.. 6.74   z 0.20..1.83
        nightstand E      x 14.10..16.09   z 0.20..1.61
        DRESSER           x  0.21.. 1.66   z 3.32..8.50   <- the WEST wall
        armchair          x  1.05.. 4.93   z 0.24..4.08
        desk              x 17.65..20.33   z 0.49..4.73   <- the EAST wall
        dark chest        x 18.81..20.29   z 8.46..11.65  <- the EAST wall
        window  N-west    x  1.77.. 4.64   z 0
        window  N-east    x 15.83..18.55   z 0
        window  east      x 20.51          z 1.40..4.40
        window  west      x 0              z 9.19..12.09

  2. The photo agrees.  Camera stands in the vestibule (~local 10.5, 16) looking
     north; +x is to the RIGHT of frame.  Left to right the photo reads:
     west window (very oblique, cut by the frame) -> dresser + mirror -> the
     room's NW corner -> narrow window with the pale armchair in front of it ->
     bed + canvas -> nightstand -> the NE corner -> the big window over the desk
     on the east wall -> the dark chest.  Projecting the plan positions through
     a pinhole at (10.5, 16) yawed 12 deg west of north puts the NW corner at
     photo x 424 where the photo has the corner at 424-435, the dresser at
     186..364 where the photo has 200..415, and the north window at 465..536
     where the photo has 490..575.  The ORDER and the corner both land.

  3. `Master Bed 2.jpg` closes it: shot from the room's east side looking west,
     it shows a wall carrying door | TV | door, then a corner, then a narrow
     window IMMEDIATELY past that corner, then the dresser + mirror with the
     potted plant on it.  That is edge 4 (the south-west wall) -> the corner at
     (0, 13.26) -> Window West at z 9.19..12.09 -> the Dresser at z 3.32..8.50.

  SO: the DRESSER IS NOT ON THE HEADBOARD WALL ANY MORE.  Round 2/3 had dresser,
  window, bed and nightstand all fighting for one 15 ft wall; the re-trace moves
  the dresser to its own 13.26 ft west wall and the collision simply stops
  existing.
"""

# ---- footprint (ground truth, never edited here) --------------------------
W_ROOM = 20.51          # local x 0..20.51
D_ROOM = 18.68          # local z 0..18.68 (main room + entry vestibule)
MAIN_Z = 13.26          # south wall of the main area
LEG_X0, LEG_X1 = 7.86, 15.58     # entry vestibule, z 13.26..18.68
WALL_H = 8.0

# rooms.points, in the order the DB stores them -- opening.edge_index counts
# edges in this order, edge i running POLY[i] -> POLY[i+1].
POLY = [(20.51, 13.26), (15.58, 13.26), (15.58, 18.68), (7.86, 18.68),
        (7.86, 13.26), (0.0, 13.26), (0.0, 0.0), (20.51, 0.0)]
E_SOUTH_EAST, E_LEG_EAST, E_LEG_SOUTH, E_LEG_WEST = 0, 1, 2, 3
E_SOUTH_WEST, E_WEST, E_NORTH, E_EAST = 4, 5, 6, 7

# ---- the NORTH WALL BUDGET (20.51 ft, z = 0) ------------------------------
# Everything on the headboard wall, solved together.  The wall grew 15 -> 20.51
# ft and the dresser left it, so for the first time nothing on it collides.
#
#   0.00 .. 1.77   blank (NW corner return)
#   1.77 .. 4.64   Window North          (plan opening, 2.87 ft)
#   4.64 .. 7.73   blank  3.09 ft        (the photo's pale armchair stands here)
#   7.73 .. 13.08  Bed, queen 5.35       centre 10.40 = the plan's bed centre
#   8.18 .. 12.62  Wall Art 4.44         centred on the bed, above the headboard
#  13.08 .. 13.10  0.02 ft
#  13.10 .. 15.30  Nightstand 2.20
#  15.30 .. 15.83  0.53 ft
#  15.83 .. 18.55  Window North East     (plan opening, 2.72 ft)
#  18.55 .. 20.51  blank 1.96 (NE corner return)
BED_CX = 10.40
BED_W = 5.35
BED_POS_Z = 3.75        # headboard back face lands at local z 0.075, just clear of the skirting
ART_W = 4.44

WIN = {                 # name -> (edge, offset along that edge, width)
    "Window North":      (E_NORTH, 1.77, 2.87),
    "Window North East": (E_NORTH, 15.83, 2.72),
    "Window East":       (E_EAST, 1.40, 3.00),
    "Window West":       (E_WEST, 1.17, 2.90),
}
WIN_SILL = {"Window North": 2.20, "Window North East": 2.20,
            "Window East": 2.50, "Window West": 2.30}
WIN_H = {"Window North": 4.60, "Window North East": 4.60,
         "Window East": 4.40, "Window West": 4.50}

# doors, from Master Bed 2 + the plan's door leaf drawn on the south-west wall
DOORS = [(E_SOUTH_WEST, 0.00, 2.93),    # x 4.93..7.86, beside the vestibule
         (E_SOUTH_WEST, 5.31, 2.55)]    # x 0.00..2.55, beside the west corner
PASSAGE = (E_LEG_SOUTH, 0.15, 3.00)     # vestibule -> 2F hallway

# ---- the VAULT ------------------------------------------------------------
# Round 3 measured, off the photo, that the gable's apex sits OVER THE BED and
# that the apex stands ~358 px above the eave line at ~53 px/ft on the north
# wall = 6.6-6.75 ft of rise over an 8 ft wall.  Both hold; what does not hold
# is round 3's 35.8/47.3 deg split, which was forced by squeezing an apex over a
# bed at x 9.75 into a 15 ft wall.  Re-derived on the real 20.51 ft wall:
#
#   * the north gable's apex is at photo x ~712.  The NW corner projects to
#     photo x ~427 and the NE corner to ~980, so the apex sits at
#     (712-427)/553 = 51.5% of the wall  ->  local x 10.56.
#   * the plan's bed centre is 10.40 and the room centre is 10.255.  All three
#     agree inside 0.3 ft, so the ridge is placed at 10.50.
#   * peak stays at the measured 14.6 ft (8.0 eave + 6.6 rise).
#
# The pitch RELATIONSHIP survives -- the ridge is still east of the room centre
# so the west plane is still the shallower one -- but the asymmetry collapses
# from 35.8/47.3 to 32.2/33.4 because it was an artifact of the wrong footprint,
# not a fact about the roof.  32-33 deg is a 7.6:12 roof, which is what a house
# like this is framed at.
RIDGE_X = 10.50
PEAK = 14.60
EAVE = 8.00
RISE = PEAK - EAVE


def h(x):
    """ceiling height above the slab at local x."""
    if x <= RIDGE_X:
        return EAVE + RISE * x / RIDGE_X
    return EAVE + RISE * (W_ROOM - x) / (W_ROOM - RIDGE_X)


def edge(i):
    """(ax, az), (bx, bz), unit direction, inward normal, length."""
    import math
    ax, az = POLY[i]
    bx, bz = POLY[(i + 1) % len(POLY)]
    L = math.hypot(bx - ax, bz - az)
    u = ((bx - ax) / L, (bz - az) / L)
    n = (-u[1], u[0])          # verified against all eight edges of this L
    return (ax, az), (bx, bz), u, n, L


def on_edge(i, offset):
    (ax, az), _b, u, _n, _L = edge(i)
    return (ax + u[0] * offset, az + u[1] * offset)
