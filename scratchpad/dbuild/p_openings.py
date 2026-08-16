"""Real cut openings for room 4 (Dining).

Round 1 faked both doorways as painted reveals on a solid wall and flattened the
bay's three windows onto a straight west wall.  The footprint re-trace gave us
the real canted bay, and `house.js buildRoom` cuts a genuine hole per opening
row (`shape.holes.push`) -- a `passage` gets NO panel at all, a `window` gets
glass.  So all seven are real now.

Edge indices (edge i runs POLY[i] -> POLY[i+1], `offset` measured from POLY[i]):

    0 SOUTH   (14.64,13.12)->(2.28,13.12)   offset runs EAST -> WEST
    1 west wall, south segment (3.52 ft)
    2 bay SOUTH facet   3 bay FRONT (x=0)   4 bay NORTH facet
    5 west wall, north segment (2.68 ft)
    6 NORTH   (2.28,0)->(14.64,0)           offset runs WEST -> EAST
    7 EAST    (14.64,0)->(14.64,13.12)      offset runs NORTH -> SOUTH

The kitchen hole is set to the SAME world span room 6 already cut on its own
side (its edge 0, offset 9.29, width 3.00 -> world x -1.61..1.39); both rooms
are anchored at world x = -4.19 so the local numbers match one for one.  A
mismatched pair would show the neighbour's jamb lining floating inside our hole.

Idempotent: every opening on room 4 is deleted and re-created on each run.
"""
import json
import urllib.request

BASE = "http://127.0.0.1:5000"
ROOM = 4

WY0, WH = 3.00, 4.25            # every window: sill on the chair rail, head 7.25

OPENINGS = [
    # --- north wall: cased opening to the kitchen (photo B and C) ----------
    dict(type="passage", edge_index=6, offset=0.30, width=3.00,
         elevation=0.0, height=7.20),

    # --- east wall: cased opening to the hallway + staircase (photo C) -----
    dict(type="passage", edge_index=7, offset=1.00, width=5.60,
         elevation=0.0, height=7.20),

    # --- south wall (front facade): two windows with the clock between -----
    # offsets run east->west; centres at local x 11.46 and 5.46
    dict(type="window", edge_index=0, offset=1.88, width=2.60,
         elevation=WY0, height=WH),
    dict(type="window", edge_index=0, offset=7.88, width=2.60,
         elevation=WY0, height=WH),

    # --- the BAY: one window per facet ------------------------------------
    dict(type="window", edge_index=2, offset=0.55, width=1.46,
         elevation=WY0, height=WH),
    dict(type="window", edge_index=3, offset=0.45, width=3.70,
         elevation=WY0, height=WH),
    dict(type="window", edge_index=4, offset=0.55, width=1.46,
         elevation=WY0, height=WH),
]


def req(method, path, data=None):
    body = json.dumps(data).encode() if data is not None else None
    r = urllib.request.Request(f"{BASE}{path}", data=body, method=method)
    if body:
        r.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(r, timeout=30) as resp:
        txt = resp.read().decode()
        return json.loads(txt) if txt.strip() else {}


def main():
    house = req("GET", "/api/house")
    room = next(r for f in house["floors"] for r in f["rooms"] if r["id"] == ROOM)
    old = room.get("openings", [])
    for op in old:
        req("DELETE", f"/api/house/opening/{op['id']}")
    print(f"removed {len(old)} old openings")
    for op in OPENINGS:
        res = req("POST", f"/api/house/room/{ROOM}/opening", op)
        print(f"  edge {op['edge_index']} off {op['offset']:5.2f} w {op['width']:4.2f} "
              f"y {op['elevation']:4.2f}+{op['height']:4.2f} {op['type']:8s} "
              f"-> id {res.get('id')}")


if __name__ == "__main__":
    main()
