"""Cut the two real window openings in room 15's SOUTH wall and set the room
surface colours.  Idempotent: it clears room 15's openings first.

Edge indices for a rect room come from house.js's `pts` order
[[0,0],[W,0],[W,D],[0,D]]:
    0 = north (offset measured east from x=0)
    1 = east  (offset measured south from z=0)
    2 = south (offset measured WEST from x=W)
    3 = west  (offset measured north from z=D)

Type is `passage`, not `window`: a `window` opening gets the app's own 0.3 ft
deep pale-blue glass box centred on the wall, which would sit 1.8 in proud of
the blinds and lay a blue film over the whole unit -- exactly the cast the
critic flagged on round 1's fake glass.  `passage` renders the hole and nothing
else, and the window unit GLB supplies its own pane, blinds, stool and casing.
"""

import json
import urllib.request

from common import ROOM, W, WIN_E, WIN_W, SILL, HEAD

BASE = "http://127.0.0.1:5000"


def req(method, path, data=None):
    body = json.dumps(data).encode() if data is not None else None
    r = urllib.request.Request(BASE + path, data=body, method=method)
    if body:
        r.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(r, timeout=30) as x:
        t = x.read().decode()
        return json.loads(t) if t.strip() else {}


def main():
    house = req("GET", "/api/house")
    room = None
    for f in house["floors"]:
        for r in f["rooms"]:
            if r["id"] == ROOM:
                room = r
    for op in room.get("openings", []):
        req("DELETE", "/api/house/opening/%d" % op["id"])
        print("deleted opening", op["id"])

    for name, (x0, x1) in (("east", WIN_E), ("west", WIN_W)):
        payload = {"type": "passage", "edge_index": 2,
                   "offset": round(W - x1, 3), "width": round(x1 - x0, 3),
                   "elevation": SILL, "height": round(HEAD - SILL, 3)}
        print(name, payload, req("POST", "/api/house/room/%d/opening" % ROOM, payload))

    print(req("PATCH", "/api/house/room/%d" % ROOM,
              {"wall_color": "#f0eeea", "floor_color": "#8f8c88",
               "floor_texture": "wood"}))


if __name__ == "__main__":
    main()
