"""Room 13 shell -- REBUILT for the correct orientation.

The shell pass had the room 180 degrees out on z: it put the headboard and the
entry door on the SOUTH/EAST-north ends and the closet on the NORTH wall.  The
floor plan's bed icon draws its pillows at world z 6.8-7.8 (the NORTH end) with
the nightstand beside them, and photo 1's camera solve puts the photographer in
the south-east doorway; so the headboard is on the NORTH wall and the closet on
the SOUTH.  See the report.

Pieces:
    Guest Ceiling     one-sided downward plane + three-step crown + 4 cans
    Guest Baseboards  skirting + chair rail + wainscot, gapped at the two
                      doorways, plus the window unit, the entry door leaf and
                      the closet bypass doors

Real openings are cut as `passage` (a true hole, no app panel) and every unit
supplies its own glass / leaf, which is what round 1's critic asked for and
what build15r2 proved.
"""

import json
import urllib.request

from gkit import *

BASE = "http://127.0.0.1:5000"


def req(method, path, data=None):
    body = json.dumps(data).encode() if data is not None else None
    r = urllib.request.Request(BASE + path, data=body, method=method)
    if body:
        r.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(r, timeout=30) as x:
        t = x.read().decode()
        return json.loads(t) if t.strip() else {}


# ------------------------------------------------------------ real openings
def openings():
    """edge order for a rect room comes from house.js `pts`
    [[0,0],[W,0],[W,D],[0,D]]:
        0 north (offset = local x)      1 east  (offset = local z)
        2 south (offset = W - local x)  3 west  (offset = D - local z)
    """
    house = req("GET", "/api/house")
    room = next(r for f in house["floors"] for r in f["rooms"] if r["id"] == ROOM)
    for op in room.get("openings", []):
        req("DELETE", "/api/house/opening/%d" % op["id"])
    out = []
    out.append(("window west", req("POST", "/api/house/room/%d/opening" % ROOM, {
        "type": "passage", "edge_index": 3, "offset": round(D - WIN[1], 3),
        "width": round(WIN[1] - WIN[0], 3), "elevation": WIN_SILL,
        "height": round(WIN_HEAD - WIN_SILL, 3)})))
    out.append(("entry door east", req("POST", "/api/house/room/%d/opening" % ROOM, {
        "type": "passage", "edge_index": 1, "offset": DOOR[0],
        "width": round(DOOR[1] - DOOR[0], 3), "elevation": 0.0,
        "height": DOOR_H})))
    out.append(("closet south", req("POST", "/api/house/room/%d/opening" % ROOM, {
        "type": "passage", "edge_index": 2, "offset": round(W - CLOSET[1], 3),
        "width": round(CLOSET[1] - CLOSET[0], 3), "elevation": 0.0,
        "height": DOOR_H})))
    for n, r in out:
        print("  opening %-16s %s" % (n, r))


# ----------------------------------------------------------------- surfaces
def surfaces(wall="#c3c1bd", floor="#525150"):
    print("  surfaces", req("PATCH", "/api/house/room/%d" % ROOM,
                            {"wall_color": wall, "floor_color": floor,
                             "floor_texture": "wood", "wall_texture": None}))


# ------------------------------------------------------------------- pieces
WAINS = "#b9b7b3"


def ceiling_piece():
    # photo 1 shows four cans in a rectangle plus a smoke alarm (photo 3)
    m = ceiling(W, D, H,
                cans=[(3.2, 2.6), (8.9, 2.6), (3.2, 7.9), (8.9, 7.9)],
                vents=[(11.2, 0.75, 0.55, 0.95)])
    # smoke alarm, photo 3 ceiling
    m.add(cylinder(0.28, 0.075, 16), Material("smoke", "#f2f1ee", roughness=0.6),
          at=(6.0, H - 0.09, 5.6))
    return m


def trim_piece():
    # kit.wall_band measures its axis in ROOM x (n/s) or ROOM z (w/e); kit._blit
    # mirrors it for the s and w walls.  So the run gaps and the unit offsets
    # are NOT the same numbers on those two walls -- this bit them once.
    m = baseboards(W, D, rail=RAIL, wainscot=WAINS,
                   doors=[("e", DOOR[0], DOOR[1]),
                          ("s", CLOSET[0], CLOSET[1]),
                          ("w", WIN[0], WIN[1])])
    # the west gap above is only so the rail and wainscot die into the window
    # casing; the skirting itself runs unbroken under a window.
    wall_band(m, TRIM, "w", W, D, 0.0, BB_H - 0.06, BB_T,
              [(0, WIN[0]), (WIN[1], D)])
    wall_band(m, TRIM, "w", W, D, BB_H - 0.06, BB_H, BB_T * 0.72,
              [(0, WIN[0]), (WIN[1], D)])

    window_unit(m, "w", W, D, D - WIN[1], D - WIN[0],
                sill=WIN_SILL, head=WIN_HEAD)
    door_unit(m, "e", W, D, DOOR[0], DOOR[1], top=DOOR_H)
    closet_doors(m)
    return m


def closet_doors(m):
    """Two bypass leaves in a cased opening on the SOUTH wall (photo 3): six
    panel faces each, the west leaf hung 0.055 ft proud of the east one so the
    pair reads as a bypass and not one flat slab."""
    sub = Model()
    a0, a1 = W - CLOSET[1], W - CLOSET[0]        # wall-frame coords (see _blit)
    mid = (a0 + a1) / 2
    panel_door(sub, WHITEWD, a0 + 0.02, mid + 0.03, 0.0, DOOR_H, 0.045, 0.135)
    panel_door(sub, WHITEWD, mid - 0.03, a1 - 0.02, 0.0, DOOR_H, 0.135, 0.225)
    # reveal behind the leaves so the passage hole never shows daylight
    bx(sub, Material("closetdark", "#3b3a38", roughness=0.95),
       a0, a1, 0.0, DOOR_H, 0.0, 0.03)
    for a, b in ((a0 - CASE_W, a0 + 0.02), (a1 - 0.02, a1 + CASE_W)):
        bx(sub, TRIM, a, b, 0.0, DOOR_H + CASE_W, 0.0, 0.30)
    bx(sub, TRIM, a0 - CASE_W, a1 + CASE_W, DOOR_H, DOOR_H + CASE_W, 0.0, 0.30)
    # edge pulls
    for hx in (mid - 0.26, mid + 0.26):
        bx(sub, BLACKMET, hx - 0.045, hx + 0.045, 2.95, 3.35, 0.225, 0.255)
    blit(m, sub, "s", W, D, 0.0)


if __name__ == "__main__":
    print("room 13 shell")
    openings()
    surfaces()
    save_and_place("Guest Ceiling", ceiling_piece())
    save_and_place("Guest Baseboards", trim_piece())
